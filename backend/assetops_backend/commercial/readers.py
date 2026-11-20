"""3A2 (spec §4; D-3A2.7): source readers turn an export's bytes into a canonical batch object.

A reader returns the batch object, an optional row map (the file row of each record index; None means row = index
+ 1) and extra personal paths (path, class) from `pseudonym.ALLOWED_EXTRA`. `READERS` holds `canonical-json-v1` only;
`3A6` registers source profiles here without changing intake, refusals, pseudonymisation or acceptance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Protocol

from assetops_contracts.canonical import loads_canonical


@dataclass(frozen=True)
class ReadResult:
    obj: object
    rows: tuple[int, ...] | None = None
    personal_paths: frozenset[tuple[str, str]] = field(default_factory=frozenset)


class SourceReader(Protocol):
    id: str
    media_types: frozenset[str]

    def read(self, data: bytes) -> ReadResult:
        """The batch object; a `CanonicalRefused` for a file that cannot be read."""

    def field_label(self, path: str) -> str:
        """The person's name for a (cut) refusal path."""


class CanonicalJsonReader:
    id = "canonical-json-v1"
    media_types = frozenset({"application/json"})

    def read(self, data: bytes) -> ReadResult:
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


DEFAULT_READER = "canonical-json-v1"
READERS: Mapping[str, SourceReader] = MappingProxyType({DEFAULT_READER: CanonicalJsonReader()})
