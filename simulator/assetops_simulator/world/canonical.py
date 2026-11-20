"""Canonical bytes, digests and the history file's bytes (spec §4.5)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _refuse_floats(obj: Any) -> None:
    stack = [obj]
    while stack:
        item = stack.pop()
        if isinstance(item, float):
            raise TypeError("CANONICAL_FLOAT")
        if isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, (list, tuple)):
            stack.extend(item)


def canonical_bytes(obj: Any) -> bytes:
    """Sorted keys, no spaces, UTF-8; any binary float anywhere is refused."""
    _refuse_floats(obj)
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_bytes(obj: Any) -> bytes:
    """The written file: sorted keys, one-space indent, a final newline."""
    _refuse_floats(obj)
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def write_canonical_file(obj: Any, path: str | Path) -> None:
    Path(path).write_bytes(file_bytes(obj))
