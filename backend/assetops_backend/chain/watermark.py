"""CH-5c (CH5c-R3 R7, amended by CH5c-R4 W1-W4): the watermark of a stored route response.

The watermark is one statement: the count of `chain_input_change` rows (migration 0047) for the tenant whose Site
is one of the request's Sites or NULL (a tenant-wide change). The log is DB append-only and every write to a
watermark input table commits at least one row in the writer's own transaction, so between two snapshots the
count is equal exactly when no input change committed between them, whatever the commit order (W1). The count is
not filtered by `known_at`: a late change to a historical row moves it too (W2, W4). A change with a NULL tenant
(a TRUNCATE, or a table without a tenant column) moves every tenant's count: over-invalidation, the safe
direction.

`code_version` (Q5) hashes the alembic head, every backend source file and every `config/` file, each by
relative path and content, so an edited, added or deleted file changes it.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable
from uuid import UUID

from sqlalchemy import text

_ROOT = Path(__file__).resolve().parents[3]
_WATERMARK = ("SELECT count(*) FROM chain_input_change WHERE (tenant_id = :t OR tenant_id IS NULL) "
              "AND (site_id = ANY(:s) OR site_id IS NULL)")


def read_watermark(c: Any, tenant_id: UUID, site_ids: Iterable[UUID]) -> str:
    """The watermark on connection `c`. W3: call it as the first statement of the read snapshot it labels."""
    sites = sorted({UUID(str(s)) for s in site_ids}, key=str)
    count = c.execute(text(_WATERMARK), {"t": tenant_id, "s": sites}).scalar_one()
    return f"cic:{count}"


def _files() -> list[Path]:
    backend = _ROOT / "backend"
    out = [p for p in (backend / "assetops_backend").rglob("*.py")]
    out += [p for p in (backend / "migrations" / "versions").glob("*.py")]
    out += [p for p in (_ROOT / "config").rglob("*") if p.is_file()]
    return sorted(out)


@lru_cache(maxsize=1)
def code_version() -> str:
    """The code and configuration version a stored body was composed with (computed once per process)."""
    digest = hashlib.sha256()
    for path in _files():
        digest.update(path.relative_to(_ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).digest())
    return digest.hexdigest()[:32]
