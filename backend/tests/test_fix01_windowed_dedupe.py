"""FIX-01: the windowed (cold/EV) coverage dedupe across a day's selected windows, on a synthetic snapshot double.

A Finding is a lineage revised per assessed window: across windows the highest revision_no wins; the same revision
seen twice is no conflict; a fork (equal revision_no, different ids) and two revisions in one window still raise."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from assetops_backend.estate import coverage
from assetops_backend.estate.index import _finding_links, _WindowRecorder
from assetops_backend.estate.scope import EstateSelectionInconsistent

T, S = "00000000-0000-4000-8000-00000000a301", "00000000-0000-4000-8000-00000000b301"
DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)
K = DAY + timedelta(hours=20)
WATERMARK = DAY + timedelta(hours=10)
F = "f0000000-0000-4000-8000-000000000001"
R1, R2, R3 = ("r0000000-0000-4000-8000-00000000000%d" % n for n in (1, 2, 3))


def row(rev: str, no: int | None, finding: str = F, evidence: str = "e-1") -> dict:
    out = {"finding_id": finding, "finding_revision_id": rev, "lifecycle": "SUPPORTED", "title": "t",
           "episode_start": DAY + timedelta(hours=8, minutes=1), "episode_end": DAY + timedelta(hours=8, minutes=16),
           "evidence_ids": [evidence], "source_provenance": {}, "consequence_revision_id": None}
    if no is not None:
        out["revision_no"] = no
    return out


def window(n: int, end_minute: int, *rows: dict, evidence: str = "e-w") -> dict:
    return {"selection_id": f"sel-{n}", "seq": n, "selected_at": WATERMARK + timedelta(seconds=n),
            "state": coverage.CURRENT, "window_start": DAY + timedelta(hours=8),
            "window_end": DAY + timedelta(hours=9, minutes=end_minute), "probe_fresh": None,
            "assessment_revision_ids": [f"a-{n}"], "evidence_ids": [evidence + str(n)], "findings": list(rows)}


class Snap:
    read_at, historical, continuation, basis_historical = K, False, False, False

    def __init__(self, domain: str, windows: list[dict]) -> None:
        self.domain, self.windows = domain, windows

    def evidence_cutoff(self, t, s, k):
        return WATERMARK

    def selected_windows(self, t, s, domain, from_, to, cutoff, k):
        assert domain == self.domain
        return self.windows

    def open_jobs(self, t, s, domain, from_, to, k):
        return []


def read(domain: str, *windows: dict) -> dict:
    return coverage.site_coverage(Snap(domain, list(windows)), T, S, domain, DAY, DAY + timedelta(days=1), K)


@pytest.mark.parametrize("domain", [coverage.EV, coverage.COLD])
@pytest.mark.parametrize("reverse", [False, True])
def test_highest_revision_no_wins_across_windows(domain: str, reverse: bool) -> None:
    older, newer = window(1, 5, row(R1, 1, evidence="e-old")), window(2, 0, row(R2, 2, evidence="e-new"))
    cov = read(domain, *((newer, older) if reverse else (older, newer)))
    assert [r["finding_revision_id"] for r in cov["rows"]] == [R2]
    assert cov["selected_finding_revision_ids"] == [R2]
    # the Site-level sets stay unions over both selected windows; the row-level evidence is the winner's only
    assert cov["selected_assessment_revision_ids"] == ["a-1", "a-2"]
    assert cov["cited_accepted_evidence_ids"] == ["e-new", "e-w1", "e-w2"]
    assert cov["selection_id"] == "sel-2"


def test_higher_revision_wins_even_from_the_earlier_selection() -> None:
    cov = read(coverage.EV, window(1, 5, row(R2, 2)), window(2, 0, row(R1, 1)))
    assert [r["finding_revision_id"] for r in cov["rows"]] == [R2]


def test_same_revision_in_two_windows_is_no_conflict() -> None:
    cov = read(coverage.EV, window(1, 5, row(R1, 1)), window(2, 0, row(R1, 1)))
    assert [r["finding_revision_id"] for r in cov["rows"]] == [R1]


def test_fork_equal_revision_no_still_raises() -> None:
    with pytest.raises(EstateSelectionInconsistent, match="two selected revisions"):
        read(coverage.EV, window(1, 5, row(R1, 1)), window(2, 0, row(R2, 1)))


def test_missing_revision_no_fails_closed() -> None:
    with pytest.raises(EstateSelectionInconsistent):
        read(coverage.COLD, window(1, 5, row(R1, None)), window(2, 0, row(R2, None)))


def test_two_revisions_in_one_window_still_raise() -> None:
    with pytest.raises(EstateSelectionInconsistent, match="one selected window"):
        read(coverage.EV, window(1, 5, row(R1, 1), row(R2, 2)))


def test_episode_filter_runs_before_the_dedupe() -> None:
    outside = row(R2, 2) | {"episode_start": DAY + timedelta(days=3), "episode_end": DAY + timedelta(days=3, hours=1)}
    cov = read(coverage.EV, window(1, 5, row(R1, 1)), window(2, 0, outside))
    assert [r["finding_revision_id"] for r in cov["rows"]] == [R1]


def test_finding_link_opens_the_window_holding_the_winning_revision() -> None:
    older, newer = window(1, 5, row(R1, 1)), window(2, 0, row(R2, 2))
    rec = _WindowRecorder(Snap(coverage.EV, [older, newer]))
    rec.cutoff = rec.evidence_cutoff(T, S, K)
    rec.selected_windows(T, S, coverage.EV, DAY, DAY + timedelta(days=1), rec.cutoff, K)
    link = _finding_links("EV-LAB-001", coverage.EV, F, R2, rec, K)["finding"]
    assert link is not None and "T09%3A00%3A00" in link.replace(":", "%3A") and "T09%3A05" not in link.replace(":", "%3A")
    stale = _finding_links("EV-LAB-001", coverage.EV, F, R1, rec, K)["finding"]
    assert stale is not None and "T09%3A05" in stale.replace(":", "%3A")
