"""JSON-file adapter over the committed-artifact store (T027, D4).

One file per run, `var/commits/{run_id}.json`, holding `artifact_text(...)`
exactly. A file is staged, verified by re-parsing, and moved into place only
if no artifact is filed for that run yet; once it exists it is never written
again. Reads go through `parse_artifact_text`, which re-derives the artifact id,
manifest and integrity digest, so a changed byte is an unreadable artifact.
"""

from __future__ import annotations

import hashlib
import os
import threading
import uuid
from pathlib import Path

from assetops_backend.runs.commit_ports import (
    CommitStoreUnavailable,
    CommittedArtifactUnreadable,
)
from assetops_backend.runs.identity import run_id_key
from assetops_contracts.committed_artifact import (
    ArtifactUnreadable,
    CommittedArtifact,
    artifact_text,
    parse_artifact_text,
)

REPO_ROOT = Path(__file__).resolve().parents[4]

#: Where sealed artifacts are filed. Outside every shipped configuration root
#: and outside version control (`.gitignore` covers `var/`).
COMMIT_STORE_ROOT = REPO_ROOT / "var" / "commits"

SUFFIX = ".json"


class JsonCommitStore:
    def __init__(self, root: Path | None = None) -> None:
        self._root = COMMIT_STORE_ROOT if root is None else root
        self._write_lock = threading.Lock()

    def _path(self, run_id: str) -> Path:
        return self._root / f"{run_id_key(run_id)}{SUFFIX}"

    def _read(self, path: Path, run_id: str) -> CommittedArtifact | None:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except OSError as error:
            raise CommitStoreUnavailable(
                f"The commit store could not be read: {self._root}"
            ) from error
        try:
            artifact = parse_artifact_text(text)
        except ArtifactUnreadable as error:
            raise CommittedArtifactUnreadable(
                f"The committed artifact for run {run_id!r} failed verification: {error}"
            ) from error
        if run_id_key(artifact.run_id) != run_id_key(run_id):
            raise CommittedArtifactUnreadable(
                f"The artifact filed for run {run_id!r} names run {artifact.run_id!r}."
            )
        return artifact

    def get(self, run_id: str) -> CommittedArtifact | None:
        return self._read(self._path(run_id), run_id)

    def site_artifacts(self, site_key: str) -> list[tuple[str, str]]:
        """`(run_id, sha256 of the stored bytes)` of every verified artifact filed
        for the Site whose `site_id_key` is `site_key` (S2-02 Q14 legacy inventory).

        Read-only. Any unreadable or unverifiable artifact raises, so a caller
        that fingerprints the legacy input fails closed rather than skip it."""
        from assetops_backend.sites.identity import site_id_key

        if not self._root.is_dir():
            return []
        found: list[tuple[str, str]] = []
        try:
            paths = sorted(self._root.glob(f"*{SUFFIX}"))
        except OSError as error:
            raise CommitStoreUnavailable(f"The commit store could not be read: {self._root}") from error
        for path in paths:
            try:
                raw = path.read_bytes()
            except OSError as error:
                raise CommitStoreUnavailable(f"The commit store could not be read: {path.name}") from error
            try:
                artifact = parse_artifact_text(raw.decode("utf-8"))
            except (ArtifactUnreadable, UnicodeDecodeError) as error:
                raise CommittedArtifactUnreadable(f"{path.name} failed verification: {error}") from error
            if site_id_key(artifact.site_id) == site_key:
                found.append((artifact.run_id, hashlib.sha256(raw).hexdigest()))
        return found

    def create(self, artifact: CommittedArtifact) -> CommittedArtifact:
        payload = artifact_text(artifact).encode("utf-8")
        destination = self._path(artifact.run_id)
        with self._write_lock:
            existing = self._read(destination, artifact.run_id)
            if existing is not None:
                return existing
            try:
                self._root.mkdir(parents=True, exist_ok=True)
            except OSError as error:
                raise CommitStoreUnavailable(
                    f"The commit store could not be opened: {self._root}"
                ) from error
            staged = self._root / f".{uuid.uuid4().hex}.staging"
            moved = False
            try:
                self._write_exclusively(staged, payload)
                if self._read(staged, artifact.run_id) != artifact:
                    raise CommittedArtifactUnreadable(
                        f"The artifact for run {artifact.run_id!r} did not survive "
                        "its own round trip, so nothing was filed."
                    )
                if destination.exists():
                    existing = self._read(destination, artifact.run_id)
                    if existing is not None:
                        return existing
                try:
                    os.replace(staged, destination)
                except OSError as error:
                    raise CommitStoreUnavailable(
                        f"The artifact for run {artifact.run_id!r} could not be filed."
                    ) from error
                moved = True
            finally:
                if not moved:
                    try:
                        staged.unlink(missing_ok=True)
                    except OSError:
                        pass
        return artifact

    def _write_exclusively(self, path: Path, payload: bytes) -> None:
        try:
            descriptor = os.open(
                path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0),
            )
            try:
                os.write(descriptor, payload)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError as error:
            raise CommitStoreUnavailable(
                f"The commit store could not be written: {self._root}"
            ) from error
