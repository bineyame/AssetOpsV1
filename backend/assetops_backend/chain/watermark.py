"""CH-5c (CH5c-R3 R7, amended by CH5c-R4 W1-W4): the watermark of a stored route response.

The watermark is one statement: the count of `chain_input_change` rows (migration 0047) for the tenant whose Site
is one of the request's Sites or NULL (a tenant-wide change). The log is DB append-only and every write to a
watermark input table commits at least one row in the writer's own transaction, so between two snapshots the
count is equal exactly when no input change committed between them, whatever the commit order (W1). The count is
not filtered by `known_at`: a late change to a historical row moves it too (W2, W4). A change with a NULL tenant
(a TRUNCATE, or a table without a tenant column) moves every tenant's count: over-invalidation, the safe
direction.

`code_version` (Q5, CH5c-R4) hashes the alembic head, every backend source file and every `config/` file, each by
relative path and content (the file list is hashed, so an edited, added or deleted file changes it), and every
environment setting a composer of a stored route reads (`COMPOSER_ENV`: the value's sha, and for a manifest path
the file's content too). Not hashed: `DATABASE_URL` (the store lives in that database) and `ASSETOPS_SERVER_TIMING`
(a response header, never body bytes).
"""
from __future__ import annotations

import hashlib
import os
import re
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


#: Q5 survey (`grep os.environ backend/assetops_backend`): the settings that can change a stored body's bytes.
COMPOSER_ENV = (
    "ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX",  # the Portfolio `next_cursor` MAC (estate/scope.py)
    "ASSETOPS_WORK_CURSOR_KEY_HEX",  # the work index cursor MAC (work/global_index.py)
    "ASSETOPS_ACTION_DEMO_GRANTS",  # Action admission (actions/composition.py)
    "ASSETOPS_DEMO_FIXTURE_MANIFEST",  # the dispatch and Finding read manifests (main.py)
    "ASSETOPS_FINDING_CASES_MANIFEST",
)
_MANIFEST_ENV = ("ASSETOPS_DEMO_FIXTURE_MANIFEST", "ASSETOPS_FINDING_CASES_MANIFEST")


def alembic_head() -> str:
    """The migration head: the revision no other migration names as its `down_revision`."""
    revs, downs = set(), set()
    for path in (_ROOT / "backend" / "migrations" / "versions").glob("*.py"):
        body = path.read_text(encoding="utf-8")
        rev = re.search(r'^revision\s*=\s*"([^"]+)"', body, re.M)
        if rev:
            revs.add(rev.group(1))
        down = re.search(r"^down_revision\s*=\s*(.+)$", body, re.M)
        if down:
            downs.update(re.findall(r'"([^"]+)"', down.group(1)))
    return ",".join(sorted(revs - downs))


def _env_digest(digest: Any) -> None:
    for name in COMPOSER_ENV:
        value = os.environ.get(name)
        digest.update(name.encode() + b"=")
        digest.update(b"\x01" if value is None else hashlib.sha256(value.encode()).digest())
        if name in _MANIFEST_ENV and value and Path(value).is_file():
            digest.update(hashlib.sha256(Path(value).read_bytes()).digest())
        digest.update(b"\x00")


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
    digest.update(b"head=" + alembic_head().encode() + b"\x00")
    _env_digest(digest)
    for path in _files():
        digest.update(path.relative_to(_ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).digest())
    return digest.hexdigest()[:32]
