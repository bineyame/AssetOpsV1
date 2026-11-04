"""IDX-GAPS U2: the board's gap line (pure, no database). CH-5a1 E3 (R8 / CH5a1-R Q9): the line reads the
ChainReader `DayFacts` (day grades over the 31 work-window days, a missing row is NO_DATA) instead of the Finding
index gaps; `index_settled` is deleted (R8 `findings_settled` replaces it) and the PARTIAL-mode withholding is not
reproduced (CH5a1-R Q4), so `withheld` is always False."""

from __future__ import annotations

from datetime import date, timedelta

from assetops_backend.chain.read import DayFacts
from assetops_backend.site_outcomes import mini
from assetops_backend.site_outcomes.mini import GAPS_NO_READINGS, GAPS_NOT_ASSESSED, finding_gap_line

DAY = date(2026, 10, 20)
DAYS = tuple(DAY - timedelta(days=30 - n) for n in range(31))
REQUESTED = [d.isoformat() for d in DAYS]


def facts(gaps, pending=()):
    grades = {d: {"generator_runtime": {"gen": "PENDING"}} for d in pending}
    return DayFacts(DAYS, grades, True, "LIMITED", tuple(gaps))


def test_gap_line_counts_the_gap_days_by_day_grade() -> None:
    assert finding_gap_line(None, 31) is None
    assert finding_gap_line(facts([]), 31) is None
    one = finding_gap_line(facts([DAYS[2]]), 31)
    assert one == {"text": "1 of the last 31 days has no checked readings yet", "days": [REQUESTED[2]],
                   "withheld": False}
    many = finding_gap_line(facts(DAYS[:23]), 31)
    assert many["text"] == "23 of the last 31 days have no checked readings yet"
    assert many["days"] == REQUESTED[:23]
    mixed = facts([DAYS[9], DAYS[1]], pending=[DAYS[9]])
    assert finding_gap_line(mixed, 31) == {"text": "Not available yet · 2 of 31 days are not assessed yet",
                                           "days": [REQUESTED[1], REQUESTED[9]],
                                           "withheld": False}
    single = finding_gap_line(facts([DAYS[9]], pending=[DAYS[9]]), 31)
    assert single["text"] == "Not available yet · 1 of 31 days is not assessed yet"
    # a PENDING grade on a day that is not a gap day never makes the line "not assessed"
    assert finding_gap_line(facts([DAYS[5]], pending=[DAYS[4]]), 31)["text"] == (
        "1 of the last 31 days has no checked readings yet")


def test_index_settledness_is_gone() -> None:
    assert not hasattr(mini, "index_settled")  # R8: `ChainRequest.findings_settled`


def test_gap_line_copy_passes_the_vocabulary_scan() -> None:
    from test_out_b2_vocabulary import _patterns

    texts = [GAPS_NO_READINGS.format(g=23, n=31, verb="have"), GAPS_NOT_ASSESSED.format(g=1, n=31, verb="is")]
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

    # CH-5a1: the heads are `FindingHead` rows, which carry no stored title at all.
    comp, _ = b2.run(b2.Fake(chain_findings=(b2.F104,)))
    assert [f.title for f in comp.facts.findings] == ["Generator may have been on longer than needed"]
    retired = b2.F090
    comp, _ = b2.run(b2.Fake(chain_findings=(retired,)))
    assert [f.title for f in comp.facts.findings] == ["Generator support review"]
