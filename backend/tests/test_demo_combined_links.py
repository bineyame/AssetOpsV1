"""POLISH PA-3 (build sheet §4 P-01/P-02, Addendum 9 Q1/Q3): the walkthrough links `tools/demo_combined.py` prints, and
its database / work-folder guards. Pure: no database, no work folder is written."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import demo_combined as tool  # noqa: E402

STORY = {"S": "2026-10-29T00:00:00Z", "S_date": "2026-10-29", "sites": ["kobo", "cold", "ev"]}
DAYS = [
    {"site": "kobo", "day": "2026-10-29", "offset": 0, "kind": "trial-before",
     "start": "2026-10-29T03:00:00Z", "end": "2026-10-29T11:00:00Z"},
    {"site": "kobo", "day": "2026-10-28", "offset": -1, "kind": "missing", "start": None, "end": None},
    {"site": "cold", "day": "2026-10-29", "offset": 0, "kind": "failure",
     "start": "2026-10-29T16:00:00Z", "end": "2026-10-29T17:05:00Z"},
    {"site": "cold", "day": "2026-10-30", "offset": 1, "kind": "missing", "start": None, "end": None},
    {"site": "ev", "day": "2026-10-27", "offset": -2, "kind": "fault",
     "start": "2026-10-27T08:00:00Z", "end": "2026-10-27T09:00:00Z"},
]
KOBO = {"action": "a-1", "action_code": "ACT-000001", "finding": "f-1", "finding_revision": "r-1"}
BASE = "http://localhost:5490"


def _links(kobo=KOBO):
    return tool.story_links(STORY, DAYS, kobo, 5490)


def test_every_link_uses_a_route_form_and_no_retired_form() -> None:
    rows = _links()
    assert rows
    for label, url in rows:
        assert url.startswith(BASE), (label, url)
        path = url[len(BASE):]
        assert path.startswith(tool.LINK_FORMS), (label, path)
        assert "/outcomes" not in path and "/overview" not in path, (label, path)


def test_week_month_and_kobo_rows() -> None:
    urls = dict(_links())
    week = "from=2026-10-23T00:00:00Z&to=2026-10-30T00:00:00Z"
    month = "from=2026-10-01T00:00:00Z&to=2026-11-01T00:00:00Z"
    assert urls["Portfolio, week to story day S"] == f"{BASE}/portfolio?{week}"
    assert urls["Findings, week to story day S"] == f"{BASE}/findings?{week}"
    assert urls["Maintenance, Preventive, month to S+3d"] == f"{BASE}/maintenance/preventive?{month}"
    assert urls["Maintenance, month to S+3d"] == f"{BASE}/maintenance?{month}"
    assert urls["KOBO-001 Overview, day S"] == f"{BASE}/sites/KOBO-001?date=2026-10-29"
    assert urls["KOBO-001 board, missing day S-1d (2026-10-28)"] == f"{BASE}/sites/KOBO-001?date=2026-10-28"
    assert urls["Action ACT-000001 verification"] == f"{BASE}/sites/KOBO-001/actions/a-1/verification"
    assert urls["Finding"] == f"{BASE}/sites/KOBO-001/findings/f-1?revision_id=r-1"


def test_cold_and_ev_boards_read_the_event_window_or_the_whole_day() -> None:
    urls = dict(_links())
    assert urls["COLD-LAB-001 board, failure day S+0d (2026-10-29)"] == \
        f"{BASE}/sites/COLD-LAB-001?from=2026-10-29T16:00:00Z&to=2026-10-29T17:05:00Z"
    assert urls["EV-LAB-001 board, fault day S-2d (2026-10-27)"] == \
        f"{BASE}/sites/EV-LAB-001/ev?from=2026-10-27T08:00:00Z&to=2026-10-27T09:00:00Z"
    assert urls["COLD-LAB-001 board, missing day S+1d (2026-10-30), no event: whole day"] == \
        f"{BASE}/sites/COLD-LAB-001?from=2026-10-30T00:00:00Z&to=2026-10-31T00:00:00Z"


def test_every_story_day_has_one_row_and_no_kobo_doc_drops_only_the_action_rows() -> None:
    labels = [label for label, _ in _links(kobo=None)]
    assert sum(" board, " in label for label in labels) == len(DAYS)
    assert not any(label.startswith(("Action ", "KOBO-001 Overview")) or label == "Finding" for label in labels)
    assert "Findings, week to story day S" in labels


def test_guards_accept_polish_and_refuse_other_names() -> None:
    demo = tool.Demo("assetops_polish_full_test", "var/polish_full")
    assert demo.work.name == "polish_full" and demo.db == "assetops_polish_full_test"
    assert tool.Demo("assetops_demo3_full_test", "var/demo3_full").work.name == "demo3_full"
    with pytest.raises(SystemExit, match="--db"):
        tool.Demo("assetops_other_x_test", "var/polish_full")
    with pytest.raises(SystemExit, match="--work"):
        tool.Demo("assetops_polish_full_test", "var/other_x")
