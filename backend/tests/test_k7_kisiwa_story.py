"""DIESEL-1 K7-D L0 (ruling DIESEL-1-R3l §9l.3): the Kisiwa story days in the demo prepare. No database.

Imports the tools as the K3 tests do. Every "must fail" names its mutation.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
for extra in (REPO / "tools", REPO / "backend" / "tests", REPO / "host" / "tests", REPO / "host"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import demo_combined as dc  # noqa: E402
from k7_story_pins import THREE_SITE_STORY_PINS  # noqa: E402


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


# ---- 1. the three-Site story stays byte-equal ---------------------------------------------------------------------

@pytest.mark.parametrize("db_now, sha, length, S", THREE_SITE_STORY_PINS)
def test_1_three_site_story_is_byte_equal(db_now: str, sha: str, length: int, S: str) -> None:
    """Must fail if any core loop iterates `SITES` (with Kisiwa in it) or Kisiwa leaks into a three-Site story."""
    story = dc.resolve_story(_at(db_now))
    text = json.dumps(story, indent=2)
    assert story["S"] == S
    assert (hashlib.sha256(text.encode("utf-8")).hexdigest(), len(text)) == (sha, length)
