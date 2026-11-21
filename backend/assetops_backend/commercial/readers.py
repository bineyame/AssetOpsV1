"""3A2 (spec §4; D-3A2.7): source readers turn an export's bytes into a canonical batch object.

A reader returns the batch object, an optional row map (the file row of each record index; None means row = index
+ 1) and extra personal paths (path, class) from `pseudonym.ALLOWED_EXTRA`. `READERS` holds `canonical-json-v1` only;
`3A6` registers source profiles here without changing intake, refusals, pseudonymisation or acceptance.

3A3 (spec §2.4; D-3A3.3, D-3A3.5, D-3A3.10): a reader is told the upload's context (`ReadContext`: the tenant, the
receipt time, whether the database holds real data) and may refuse rows itself (`ReadResult.refused`, index -> native
code and path), which wins over 2a's verdict for that row. `LayoutReader` reads one native layout of
`assetops_contracts.native`; its provenance follows the database. A reader is registered in `READERS` only with a
passing contract case (`backend/tests/source_contracts.py`, test S2).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Mapping, Protocol

from assetops_contracts.canonical import loads_canonical
from assetops_contracts.native import LAYOUTS, Layout, read_layout


@dataclass(frozen=True)
class ReadContext:
    tenant_code: str
    received_at: datetime
    real_data: bool


@dataclass(frozen=True)
class ReadResult:
    obj: object
    rows: tuple[int, ...] | None = None
    personal_paths: frozenset[tuple[str, str]] = field(default_factory=frozenset)
    refused: Mapping[int, tuple[str, str]] = MappingProxyType({})


class SourceReader(Protocol):
    id: str
    media_types: frozenset[str]

    def read(self, data: bytes, *, context: ReadContext) -> ReadResult:
        """The batch object; a `CanonicalRefused` for a file that cannot be read."""

    def field_label(self, path: str) -> str:
        """The person's name for a (cut) refusal path."""


class CanonicalJsonReader:
    id = "canonical-json-v1"
    media_types = frozenset({"application/json"})

    def read(self, data: bytes, *, context: ReadContext) -> ReadResult:
        return ReadResult(loads_canonical(data), None, frozenset())

    def field_label(self, path: str) -> str:
        if path in ("json", "batch") or path.startswith("json."):
            return "the file"
        if path.startswith("batch."):
            return path[len("batch."):]
        if path == "record":
            return "the record"
        if path.startswith("record."):
            return path[len("record."):]
        return path


#: 3A6 (spec §3): the media types a layout reader takes, by its file format.
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MEDIA_TYPES = MappingProxyType({"csv": frozenset({"text/csv"}), "xlsx": frozenset({XLSX_MEDIA_TYPE})})


class LayoutReader:
    """One native layout (spec §2.4): an illustrative CSV layout or a compiled source profile (3A6). Provenance
    follows the database (D-3A3.10); the media types follow the layout's file format."""

    def __init__(self, layout: Layout) -> None:
        self.layout = layout
        self.id = layout.id
        self.media_types = MEDIA_TYPES[layout.file.format]

    def read(self, data: bytes, *, context: ReadContext) -> ReadResult:
        produced_at = context.received_at.astimezone(timezone.utc).replace(microsecond=0).isoformat()
        provenance = "observed-financial" if context.real_data else "source-emulated"
        native = read_layout(self.layout, data, tenant_code=context.tenant_code, produced_at=produced_at,
                             provenance=provenance)
        return ReadResult(native.obj, native.rows, self.layout.personal, native.refused)

    def field_label(self, path: str) -> str:
        if path in ("json", "batch") or path.startswith("json."):
            return "the file"
        if path.startswith("row."):
            return f"row {path[len('row.'):]}"
        if path.startswith("record."):
            inner = path[len("record."):]
            for column in self.layout.columns:
                if any(p == inner or p.startswith(inner + ".") for p in column.paths):
                    return column.header
            return "the record"
        return _CANONICAL.field_label(path)


DEFAULT_READER = "canonical-json-v1"
_CANONICAL = CanonicalJsonReader()
READERS: Mapping[str, SourceReader] = MappingProxyType(
    {DEFAULT_READER: _CANONICAL, **{layout.id: LayoutReader(layout) for layout in LAYOUTS.values()}})
