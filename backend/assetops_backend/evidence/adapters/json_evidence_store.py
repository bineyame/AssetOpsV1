"""JSON file adapter for the evidence store, under `var/evidence/`.

`EVIDENCE_STORE_ROOT` is declared here and nowhere else.

Layout:
- `sites/{site_id}.json`: one canonical JSON document per Site holding its
  accepted records, rejections, conflicts and batch progress. Written whole:
  the new text goes to a `.partial` sibling and is moved over the document in
  one `os.replace` (the pattern of `host/source_stages.py`), so a process that
  dies mid-write leaves either the previous complete document or a `.partial`
  nobody reads. Ingestion writes records and progress together, so the
  persisted watermark always names exactly what was persisted.
- `registry/mappings/{id}--v{n}.json` and
  `registry/configuration/{site_id}--v{n}.json`: immutable registrations,
  written once and never rewritten.

`clear_derived()` removes the per-Site documents and keeps the registries; a
rebuild re-ingests committed artifacts into the empty derived store.

Single-host and process-local: one lock serialises writes. Not a distributed
store claim.
"""

from __future__ import annotations

import dataclasses
import json
import os
import threading
from pathlib import Path
from typing import Any, Sequence, TypeVar

from assetops_backend.evidence.models import (
    AcceptedRecord,
    BasisSignal,
    BatchProgress,
    ConfigurationBasis,
    Conflict,
    MappingRegistration,
    Rejection,
    SiteEvidence,
)
from assetops_backend.evidence.ports import EvidenceStoreUnavailable

REPO_ROOT = Path(__file__).resolve().parents[4]

#: The writable evidence store. Outside every shipped configuration root and
#: outside version control (`var/` is gitignored).
EVIDENCE_STORE_ROOT = REPO_ROOT / "var" / "evidence"

DOCUMENT_SCHEMA = {"id": "assetops.site-evidence", "version": 1}

T = TypeVar("T")


def _canonical(document: object) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _build(kind: type[T], row: object) -> T:
    names = {field.name for field in dataclasses.fields(kind)}  # type: ignore[arg-type]
    if not isinstance(row, dict) or set(row) != names:
        raise EvidenceStoreUnavailable(f"a stored {kind.__name__} does not have its exact fields")
    return kind(**row)


def _record(row: object) -> AcceptedRecord:
    if isinstance(row, dict) and isinstance(row.get("record_detail"), list):
        row = {**row, "record_detail": tuple(tuple(pair) for pair in row["record_detail"])}
    return _build(AcceptedRecord, row)


def _basis(row: object) -> ConfigurationBasis:
    if isinstance(row, dict) and isinstance(row.get("signals"), list):
        row = {**row, "signals": tuple(_build(BasisSignal, item) for item in row["signals"])}
    return _build(ConfigurationBasis, row)


class JsonEvidenceStore:
    def __init__(self, root: Path | None = None) -> None:
        self._root = EVIDENCE_STORE_ROOT if root is None else Path(root)
        self._lock = threading.Lock()

    # --- paths -------------------------------------------------------------
    def _sites(self) -> Path:
        return self._root / "sites"

    def _site_path(self, site_id: str) -> Path:
        return self._sites() / f"{site_id}.json"

    def _mapping_path(self, mapping_set_id: str, version: int) -> Path:
        return self._root / "registry" / "mappings" / f"{mapping_set_id}--v{version}.json"

    def _configuration_path(self, site_id: str, version: int) -> Path:
        return self._root / "registry" / "configuration" / f"{site_id}--v{version}.json"

    # --- io ----------------------------------------------------------------
    def _read(self, path: Path) -> Any | None:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except OSError as error:
            raise EvidenceStoreUnavailable(f"cannot read {path.name}: {error}") from error
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise EvidenceStoreUnavailable(f"{path.name} is not JSON") from error

    def _write(self, path: Path, document: object) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_name(path.name + ".partial")
            partial.write_bytes(_canonical(document).encode("utf-8"))
            os.replace(partial, path)
        except OSError as error:
            raise EvidenceStoreUnavailable(f"cannot write {path.name}: {error}") from error

    # --- per-Site evidence --------------------------------------------------
    def load_site(self, site_id: str) -> SiteEvidence:
        document = self._read(self._site_path(site_id))
        if document is None:
            return SiteEvidence(site_id=site_id)
        expected = {"schema", "site_id", "records", "rejections", "conflicts", "batches"}
        if not isinstance(document, dict) or set(document) != expected:
            raise EvidenceStoreUnavailable(f"the evidence document for {site_id} is unreadable")
        if document["schema"] != DOCUMENT_SCHEMA or document["site_id"] != site_id:
            raise EvidenceStoreUnavailable(f"the evidence document for {site_id} is another schema or Site")
        try:
            return SiteEvidence(
                site_id=site_id,
                records=tuple(_record(row) for row in document["records"]),
                rejections=tuple(_build(Rejection, row) for row in document["rejections"]),
                conflicts=tuple(_build(Conflict, row) for row in document["conflicts"]),
                batches=tuple(_build(BatchProgress, row) for row in document["batches"]),
            )
        except TypeError as error:
            raise EvidenceStoreUnavailable(f"the evidence document for {site_id} is unreadable") from error

    def save_site(self, evidence: SiteEvidence) -> None:
        document = {
            "schema": DOCUMENT_SCHEMA,
            "site_id": evidence.site_id,
            "records": [dataclasses.asdict(row) for row in evidence.records],
            "rejections": [dataclasses.asdict(row) for row in evidence.rejections],
            "conflicts": [dataclasses.asdict(row) for row in evidence.conflicts],
            "batches": [dataclasses.asdict(row) for row in evidence.batches],
        }
        with self._lock:
            self._write(self._site_path(evidence.site_id), document)

    def list_sites(self) -> Sequence[str]:
        root = self._sites()
        if not root.is_dir():
            return ()
        return tuple(sorted(path.stem for path in root.glob("*.json")))

    # --- immutable registries ---------------------------------------------
    def get_mapping(self, mapping_set_id: str, mapping_version: int) -> MappingRegistration | None:
        document = self._read(self._mapping_path(mapping_set_id, mapping_version))
        return None if document is None else _build(MappingRegistration, document)

    def register_mapping(self, registration: MappingRegistration) -> MappingRegistration:
        with self._lock:
            existing = self.get_mapping(registration.mapping_set_id, registration.mapping_version)
            if existing is not None:
                return existing
            self._write(
                self._mapping_path(registration.mapping_set_id, registration.mapping_version),
                dataclasses.asdict(registration),
            )
            return registration

    def get_configuration(self, site_id: str, foundation_version: int) -> ConfigurationBasis | None:
        document = self._read(self._configuration_path(site_id, foundation_version))
        return None if document is None else _basis(document)

    def register_configuration(self, basis: ConfigurationBasis) -> ConfigurationBasis:
        with self._lock:
            existing = self.get_configuration(basis.site_id, basis.foundation_version)
            if existing is not None:
                return existing
            self._write(
                self._configuration_path(basis.site_id, basis.foundation_version),
                dataclasses.asdict(basis),
            )
            return basis

    def list_configurations(self, site_id: str) -> Sequence[ConfigurationBasis]:
        root = self._root / "registry" / "configuration"
        if not root.is_dir():
            return ()
        found = [
            _basis(self._read(path))
            for path in sorted(root.glob(f"{site_id}--v*.json"))
        ]
        return tuple(
            sorted(
                (basis for basis in found if basis.site_id == site_id),
                key=lambda basis: basis.foundation_version,
            )
        )

    def clear_derived(self) -> None:
        with self._lock:
            root = self._sites()
            if not root.is_dir():
                return
            for path in root.iterdir():
                try:
                    os.remove(path)
                except OSError as error:
                    raise EvidenceStoreUnavailable(f"cannot clear {path.name}: {error}") from error
