"""CH-5c Q8: the pre-built route list (`config/chain/prebuilt-routes-v1.json`), page 1 only (Q11).

The file is read by `chain/adapters/file_chain_config.load_prebuilt_routes` (CH5c-R6: no file read above the port);
`chain.composition.prebuilt_requests()` is the one entry point.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

CONFIG_NAME = "prebuilt-routes-v1.json"
SCHEMA = "chain-prebuilt-routes-1"


@dataclass(frozen=True)
class PrebuiltRequest:
    id: str
    path: str
    query: str


def parse(doc: Mapping[str, Any]) -> tuple[PrebuiltRequest, ...]:
    if doc.get("schema") != SCHEMA:
        raise ValueError(f"{CONFIG_NAME}: schema {doc.get('schema')!r} is not {SCHEMA!r}")
    return tuple(PrebuiltRequest(r["id"], r["path"], r["query"]) for r in doc["requests"])
