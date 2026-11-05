"""CH-5c Q5 (CH5c-R4; moved below the port by CH5c-R6): the file reads behind `code_version`.

`code_version` hashes the alembic head, every backend source file, every `config/` file, `host/**/*.py` and `contracts/**` (CH5c-R7), each by relative path
and content (the file list is hashed, so an edited, added or deleted file changes it), and every composer setting
named by `chain.watermark.COMPOSER_ENV` (the value's sha, and for a manifest path the file's content too). The
domain rule and the setting list live in `chain/watermark.py`; this adapter only reads the files.
"""
from __future__ import annotations

import hashlib
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from assetops_backend.chain.watermark import COMPOSER_ENV, MANIFEST_ENV

_ROOT = Path(__file__).resolve().parents[4]


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
        if name in MANIFEST_ENV and value and Path(value).is_file():
            digest.update(hashlib.sha256(Path(value).read_bytes()).digest())
        digest.update(b"\x00")


def _files() -> list[Path]:
    backend = _ROOT / "backend"
    out = [p for p in (backend / "assetops_backend").rglob("*.py")]
    out += [p for p in (backend / "migrations" / "versions").glob("*.py")]
    out += [p for p in (_ROOT / "config").rglob("*") if p.is_file()]
    # CH5c-R7 residual: the host and contract packages a composer imports
    out += [p for p in (_ROOT / "host").rglob("*.py") if "__pycache__" not in p.parts]
    out += [p for p in (_ROOT / "contracts").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
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
