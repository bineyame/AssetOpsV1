"""Writable YAML adapter over the run store.

This is the second module in the product with a write path, and the only one
that writes a run. `tools/check-architecture.ps1` enforces that by registering
the run domain beside the two configuration domains: a write-capable call
anywhere else in the backend fails the build. A run is not configuration, but
the persistence seam it needs is the same one, and a second write path would
be a second set of atomicity guarantees nobody wrote.

`RUN_STORE_ROOT` is declared here and nowhere else. One owned location for the
writable root is what keeps "outside the shipped configuration roots"
checkable, and the guard fails if a second module declares it.

The write is create-only and never an update, and it is built so that a failed
create leaves the store byte-identical. It follows the recipe the user Site
store established, for the same reasons and in the same order:

1.  The record is rendered and serialized first, before anything is touched,
    so a serialization failure never reaches the store.
2.  The absence of the identity is checked under a lock, so two concurrent
    creates cannot both pass the check. The store is file-backed and
    single-host, so a process-level lock is the honest scope for this.
3.  The bytes go to a uniquely named temporary file created exclusively, then
    flushed and fsynced.
4.  That temporary file is read back and parsed. The record it yields must
    equal the record that was validated, so what lands in the store is
    provably what the service produced rather than whatever the writer
    emitted. For a run that matters more than for a Site: a frozen identity
    that did not survive its own round trip is not frozen.
5.  Only then is it moved into place atomically. Any failure at any step
    removes the temporary file, so no partial or stray document is left
    behind and no existing run is disturbed.

The stored file name is the case-folded `run_id`, but identity is never read
back out of a file name: documents are parsed and keyed on the `run_id` they
declare.
"""

from __future__ import annotations

import os
import threading
import uuid
from pathlib import Path

from assetops_backend.runs.adapters.yaml_run_documents import (
    DOCUMENT_SUFFIX,
    read_run_record,
    read_run_records,
    serialize_run_document,
)
from assetops_backend.runs.identity import run_id_key
from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.parsing import render_run_document
from assetops_backend.runs.ports import (
    RunConfigurationInvalid,
    RunIdentityConflict,
    RunNotFound,
    RunStoreUnavailable,
)

REPO_ROOT = Path(__file__).resolve().parents[4]

#: Where Draft runs are persisted. It lives outside every shipped
#: configuration root and outside version control: `.gitignore` covers `var/`,
#: and `tools/check-architecture.ps1` checks that it does. A run is a record
#: this installation produced, so it is no more shippable than a user's site.
RUN_STORE_ROOT = REPO_ROOT / "var" / "runs"


class YamlRunStore:
    """The file-backed run store.

    One store, not two. Unlike Sites and scenarios there is no shipped half:
    nothing ships a run, because a run is something this installation did.
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = RUN_STORE_ROOT if root is None else root
        self._write_lock = threading.Lock()

    def list_runs(self) -> tuple[SimulationRun, ...]:
        return read_run_records(self._root)

    def get_run(self, run_id: str) -> SimulationRun:
        key = run_id_key(run_id)
        for record in self.list_runs():
            if run_id_key(record.run_id) == key:
                return record
        raise RunNotFound(f"No run with run ID {run_id!r} is persisted.")

    def create_run(self, record: SimulationRun) -> SimulationRun:
        """Write a new Draft, or write nothing at all."""
        payload = serialize_run_document(render_run_document(record))

        with self._write_lock:
            self._ensure_root()

            self._refuse_existing_identity(record.run_id)

            destination = (
                self._root / f"{run_id_key(record.run_id)}{DOCUMENT_SUFFIX}"
            )
            staged = self._root / f".{uuid.uuid4().hex}.staging"
            moved = False

            try:
                self._write_exclusively(staged, payload)

                stored = read_run_record(staged)
                if stored != record:
                    raise RunConfigurationInvalid(
                        f"The stored document for run {record.run_id!r} did "
                        "not match the frozen run, so nothing was written. A "
                        "frozen identity that does not survive its own round "
                        "trip is not frozen."
                    )

                # Re-checked immediately before the move: the absence check
                # above ran before any I/O, and this is the last moment at
                # which an existing run could still be overwritten.
                self._refuse_existing_identity(record.run_id)
                if destination.exists():
                    raise RunIdentityConflict(
                        f"Run ID {record.run_id!r} is already in use."
                    )

                try:
                    os.replace(staged, destination)
                except OSError as error:
                    raise RunStoreUnavailable(
                        f"The run {record.run_id!r} could not be written to "
                        "the run store."
                    ) from error
                moved = True
            finally:
                if not moved:
                    try:
                        staged.unlink(missing_ok=True)
                    except OSError:
                        # Removing the staging file is best effort. It carries
                        # no document suffix, so it is never read as a run.
                        pass

        return record

    def _ensure_root(self) -> None:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise RunStoreUnavailable(
                f"The run store could not be opened: {self._root}"
            ) from error

    def _refuse_existing_identity(self, run_id: str) -> None:
        key = run_id_key(run_id)
        for existing in self.list_runs():
            if run_id_key(existing.run_id) == key:
                raise RunIdentityConflict(
                    f"Run ID {run_id!r} is already in use. Run identities are "
                    "allocated, so meeting this means something is allocating "
                    "them somewhere it should not be."
                )

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
            raise RunStoreUnavailable(
                f"The run store could not be written: {self._root}"
            ) from error
