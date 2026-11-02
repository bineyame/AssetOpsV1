"""IDX-GAPS U2: the board's Finding index settledness and gap line (pure, no database)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from assetops_backend.site_outcomes.mini import (
    GAPS_NO_READINGS,
    GAPS_NOT_ASSESSED,
    GAPS_WITHHELD,
    UNSETTLED_INDEX_STATUS,
    finding_gap_line,
    index_settled,
)

DAY = date(2026, 10, 20)
REQUESTED = [(DAY - timedelta(days=30 - n)).isoformat() for n in range(31)]


def body(gaps, *, status="PARTIAL", withheld=False):
    return {"status": status, "withheld": withheld, "discovery": {"requested_days": REQUESTED},
            "gaps": [{"day": d, "state": s, "reason": r} for d, s, r in gaps]}


def test_gap_line_counts_requested_non_current_days_only() -> None:
    assert finding_gap_line(None, 31) is None
    assert finding_gap_line(body([]), 31) is None
    # CURRENT-state entries (edge, withheld host) and days outside the requested window never count
    edge_only = body([(REQUESTED[4], "CURRENT", "EDGE_NEXT_TO_GAP"), ("2026-09-18", "PENDING", "NOT_CURRENT")])
    assert finding_gap_line(edge_only, 31) is None
    one = finding_gap_line(body([(REQUESTED[2], "UNASSESSED", "NOT_CURRENT")]), 31)
    assert one == {"text": "1 of the last 31 days has no checked readings yet", "days": [REQUESTED[2]],
                   "withheld": False}
    many = finding_gap_line(body([(d, "UNASSESSED", "NOT_CURRENT") for d in REQUESTED[:23]]), 31)
    assert many["text"] == "23 of the last 31 days have no checked readings yet"
    assert many["days"] == REQUESTED[:23]
    mixed = body([(REQUESTED[9], "PENDING", "NOT_CURRENT"), (REQUESTED[1], "UNASSESSED", "NOT_CURRENT")])
    assert finding_gap_line(mixed, 31) == {"text": "Not available yet · 2 of 31 days are not assessed yet",
                                           "days": [REQUESTED[1], REQUESTED[9]],
                                           "withheld": False}
    single = finding_gap_line(body([(REQUESTED[9], "FAILED", "NOT_CURRENT")]), 31)
    assert single["text"] == "Not available yet · 1 of 31 days is not assessed yet"
    held = body([(REQUESTED[5], "UNASSESSED", "NOT_CURRENT"), (REQUESTED[4], "CURRENT", "WITHHELD_FINDING")],
                withheld=True)
    assert finding_gap_line(held, 31)["text"] == (
        "1 of the last 31 days has no checked readings yet; Findings next to those days are not shown yet")
    assert finding_gap_line(held, 31)["withheld"] is True  # WALK1-1 M1: the client words "None shown yet" from it


@pytest.mark.parametrize(("status", "gaps", "settled"), [
    ("CURRENT", [], True),
    ("PARTIAL", [(REQUESTED[0], "UNASSESSED", "NOT_CURRENT")], True),
    ("PARTIAL", [(DAY.isoformat(), "PENDING", "NOT_CURRENT")], False),
    ("PARTIAL", [(DAY.isoformat(), "CURRENT", "EDGE_NEXT_TO_GAP")], False),
    ("PARTIAL", [(DAY.isoformat(), "CURRENT", "WITHHELD_FINDING")], False),
    ("UNASSESSED", [], False), ("PENDING", [], False), ("FAILED", [], False), ("STALE_PROJECTION", [], False),
    (None, [], False),
])
def test_index_settled_uses_the_board_day(status, gaps, settled) -> None:
    b = body(gaps, status=status)
    if status is None:
        b.pop("status")
    assert index_settled(b, DAY) is settled


def test_unsettled_statuses_include_the_dispatch_stale_code() -> None:
    assert {"STALE_PROJECTION", "UNASSESSED", "PENDING", "FAILED"} <= set(UNSETTLED_INDEX_STATUS)


def test_gap_line_copy_passes_the_vocabulary_scan() -> None:
    from test_out_b2_vocabulary import _patterns

    texts = [GAPS_NO_READINGS.format(g=23, n=31, verb="have"), GAPS_NOT_ASSESSED.format(g=1, n=31, verb="is"),
             GAPS_WITHHELD.strip("; ")]
    hits = [(t, name) for t in texts for name, p in _patterns() if p.search(t)]
    assert hits == []
    assert any(p.search("23 of 31 STALE_PROJECTION days") for _, p in _patterns())  # the scan can fail


def test_board_finding_titles_are_the_frontend_plain_titles() -> None:
    """Addendum 3: each board Finding title is a literal of `frontend/src/sites/findingWords.ts`, keyed by lifecycle."""
    from pathlib import Path

    from assetops_backend.site_outcomes.mini import COPY, FINDING_TITLE, FINDING_TITLE_FALLBACK

    words = (Path(__file__).resolve().parents[2] / "frontend" / "src" / "sites" / "findingWords.ts").read_text(
        encoding="utf-8")
    for lifecycle, title in FINDING_TITLE.items():
        assert f"{lifecycle}: {{" in words and f'title: "{title}"' in words, (lifecycle, title)
    assert f'"{FINDING_TITLE_FALLBACK}"' in Path(__file__).resolve().parents[2].joinpath(
        "frontend", "src", "sites", "OverviewFindingList.tsx").read_text(encoding="utf-8")
    assert set(FINDING_TITLE.values()) | {FINDING_TITLE_FALLBACK} <= set(COPY)  # in the vocabulary scan


def test_board_names_a_finding_by_lifecycle_not_stored_title() -> None:
    import test_out_b2_mini as b2

    raw = dict(b2.F104, title="A stored title the board does not show")
    comp, _ = b2.run(b2.Fake(finding_index={"status": "CURRENT", "gaps": [], "rows": [raw], "next_cursor": None}))
    assert [f.title for f in comp.facts.findings] == ["Generator may have been on longer than needed"]
    retired = dict(b2.F090, lifecycle="RETIRED")
    comp, _ = b2.run(b2.Fake(finding_index={"status": "CURRENT", "gaps": [], "rows": [retired], "next_cursor": None}))
    assert [f.title for f in comp.facts.findings] == ["Generator support review"]
