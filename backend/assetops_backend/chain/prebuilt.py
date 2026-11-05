"""CH-5c Q8: the pre-built route list (`config/chain/prebuilt-routes-v1.json`), page 1 only (Q11)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[3] / "config" / "chain" / "prebuilt-routes-v1.json"
SCHEMA = "chain-prebuilt-routes-1"


@dataclass(frozen=True)
class PrebuiltRequest:
    id: str
    path: str
    query: str


@lru_cache(maxsize=1)
def requests() -> tuple[PrebuiltRequest, ...]:
    doc = json.loads(CONFIG.read_text(encoding="utf-8"))
    if doc.get("schema") != SCHEMA:
        raise ValueError(f"{CONFIG.name}: schema {doc.get('schema')!r} is not {SCHEMA!r}")
    return tuple(PrebuiltRequest(r["id"], r["path"], r["query"]) for r in doc["requests"])
