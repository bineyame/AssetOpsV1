"""K7-F: KIS-10's estate summary window is UTC-midnight aligned and covers the story days (L0, no DB)."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import demo_combined_finish as finish  # noqa: E402
from assetops_backend.estate.scope import EstateRefusal, check_window  # noqa: E402

# Kisiwa (Africa/Dar_es_Salaam, UTC+3) local day start: 21:00Z the previous UTC day.
LO = datetime(2026, 11, 5, 21, 0, tzinfo=timezone.utc)


def test_the_old_local_start_window_is_refused_by_the_estate_rule() -> None:
    with pytest.raises(EstateRefusal):
        check_window(LO - timedelta(days=6), LO + timedelta(days=1))


def test_the_aligned_window_passes_the_estate_rule_and_covers_the_story_days() -> None:
    old_from, old_to = LO - timedelta(days=6), LO + timedelta(days=1)
    start, end = finish.utc_aligned_window(old_from, old_to)
    check_window(start, end)
    assert start <= old_from and end >= old_to
    assert old_from - start < timedelta(days=1) and end - old_to < timedelta(days=1)
    assert finish.iso(start) == "2026-10-30T00:00:00Z" and finish.iso(end) == "2026-11-07T00:00:00Z"


def test_an_already_aligned_window_is_unchanged() -> None:
    a = datetime(2026, 11, 1, tzinfo=timezone.utc)
    assert finish.utc_aligned_window(a, a + timedelta(days=7)) == (a, a + timedelta(days=7))
