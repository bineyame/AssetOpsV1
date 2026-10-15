"""Read the server-side SYSTEM demonstration grants document (`ASSETOPS_ACTION_DEMO_GRANTS`) for S6-01a.

An absent, unreadable or malformed document grants nothing (the capability check then denies every command).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_grants(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return document if isinstance(document, dict) else None
