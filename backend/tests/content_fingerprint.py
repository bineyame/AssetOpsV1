"""The content fingerprint shared by the shipped-content version guards.

SHA-256 over a PARSED document (``yaml.safe_load``), dumped as canonical JSON
with sorted keys. Comments, key order and whitespace are not content and do not
move it; every key and value does. Used by the shipped template guard (T025f)
and the shipped scenario guard (T025g), so "changed content at an unchanged
version" means the same thing for both.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def content_fingerprint(document: Any) -> str:
    """SHA-256 over the canonical JSON form of a parsed document."""
    canonical = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
