"""CH-5c2 (CH5c-R7 H1 F2): the file-state term `F` of a stored route's watermark.

The declared roots are `config/chain/file-inputs-v1.json`. For a request's Site codes, `F` is sha256 over every
root resolved for those Sites (a root without a Site placeholder once): its canonical path, then for every regular
file under it (or the root itself when it is a file) the sorted (relative path, size, `mtime_ns`). A missing root
hashes as `absent`. The bases are resolved at read time from the adapters' root constants (CH5c2-R1 Q6), so a test
that patches a root is followed. This adapter is the only reader of the declared roots for the store; `allowed`
gives the F4 audit guard the same set.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

_ROOT = Path(__file__).resolve().parents[4]
CONFIG = _ROOT / "config" / "chain" / "file-inputs-v1.json"


@lru_cache(maxsize=1)
def _declared() -> dict[str, Any]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _base(spec: str) -> Path:
    module, name = spec.split(":")
    return Path(getattr(importlib.import_module(module), name))


def _bases() -> dict[str, Path]:
    return {name: _base(spec) for name, spec in _declared()["bases"].items()}


def roots(site_codes: Iterable[str]) -> list[Path]:
    """Every declared root resolved for `site_codes` (sorted, de-duplicated)."""
    bases = _bases()
    codes = sorted({str(c) for c in site_codes})
    out: set[Path] = set()
    for entry in _declared()["roots"]:
        pattern = entry["path"]
        for name, base in bases.items():
            pattern = pattern.replace("{" + name + "}", str(base))
        if "{site_" in pattern:
            for code in codes:
                out.add(Path(pattern.replace("{site_key}", code.strip().lower()).replace("{site_code}", code)))
        else:
            out.add(Path(pattern))
    return sorted(out, key=str)


def prefixes() -> list[str]:
    """F4: the directory prefix of every declared root (the path before its first Site placeholder), normalised."""
    bases = _bases()
    out = []
    for entry in _declared()["roots"]:
        pattern = entry["path"]
        for name, base in bases.items():
            pattern = pattern.replace("{" + name + "}", str(base))
        cut = pattern.split("{site_")[0]
        out.append(os.path.normcase(os.path.abspath(cut)))
    return out


def _entries(root: Path) -> list[tuple[str, int, int]]:
    if root.is_file():
        st = root.stat()
        return [("", st.st_size, st.st_mtime_ns)]
    out = []
    for folder, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(folder, name)
            try:
                st = os.stat(path)
            except FileNotFoundError:
                continue
            out.append((os.path.relpath(path, root).replace(os.sep, "/"), st.st_size, st.st_mtime_ns))
    return sorted(out)


def file_state(site_codes: Iterable[str]) -> str:
    """`F` for the Sites `site_codes` (32 hex)."""
    digest = hashlib.sha256()
    for root in roots(site_codes):
        digest.update(os.path.normcase(str(root.resolve(strict=False))).encode("utf-8") + b"\x00")
        if not root.exists():
            digest.update(b"absent\x00")
            continue
        for rel, size, mtime in _entries(root):
            digest.update(f"{rel}\x01{size}\x01{mtime}\x00".encode("utf-8"))
        digest.update(b"\x02")
    return digest.hexdigest()[:32]
