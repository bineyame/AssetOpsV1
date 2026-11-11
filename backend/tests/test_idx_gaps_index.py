"""IDX-GAPS U1: the Site Finding index `finding-index/2` (fake store and fake dispatch, no database).

T1 pins v1 CURRENT bodies (rows, count, order, page walk) as literals recorded from a v1 run on `ca6d7d61b`.
T2-T8 pin the v2 rule: PARTIAL lists only the Findings whose touched days avoid every gap day, and names the gaps.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import pytest

from assetops_backend.analytics import dispatch as dispatch_contract
from assetops_backend.analytics.finding_index import (
    PARTIAL,
    POLICY_VERSION,
    SCHEMA_VERSION,
    FindingIndexService,
    IndexConflict,
    gap_days,
    parse_request,
    touched,
)

UTC = timezone.utc
T = UUID("00000000-0000-0000-0000-0000000000a1")
S = UUID("00000000-0000-0000-0000-0000000000b1")
D6, D7, D8 = date(2026, 10, 6), date(2026, 10, 7), date(2026, 10, 8)


def at(day: date, hh: int, mm: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hh, mm, tzinfo=UTC)


def fid(n: int) -> UUID:
    return UUID(f"00000000-0000-0000-0000-{n:012d}")


def head(n: int, start: datetime, end: datetime, merged_into: UUID | None = None) -> dict[str, Any]:
    return {"finding_id": fid(n), "finding_revision_id": fid(1000 + n), "revision_no": 1, "title": f"F{n}",
            "domain": "mini_grid", "analytic_id": "dispatch", "episode_start": start, "episode_end": end,
            "lifecycle": "OPEN", "transition": "OPENED", "claim_level": "OBSERVED",
            "assessment_revision_id": fid(2000 + n), "analytic_run_id": fid(3000 + n), "model_version": "m1",
            "matcher_version": "x", "cohort_sha256": "c", "limitations": [], "recurs_after_finding_id": None,
            "split_from_finding_id": None, "merged_into_finding_id": merged_into}


class Store:
    def __init__(self, heads, days, *, matched_through=10, deferred=(), merges=(), seqs=None) -> None:
        self.heads, self.merges = list(heads), list(merges)
        self.seqs = seqs if seqs is not None else {
            datetime(d.year, d.month, d.day, tzinfo=UTC): 1 for d in days}
        self.match = {"matched_through_selection_seq": matched_through}
        self.deferred = list(deferred)
        self.fence_value, self.fence_after = "f1", "f1"

    def index_snapshot(self, t, s, domain, analytic):
        return {"heads": self.heads, "match_pass": self.match, "selection_seqs": self.seqs,
                "deferred_windows": self.deferred, "fence": self.fence_value, "merges": self.merges}

    def index_lineage(self, t, s, ids):
        return {"runs": [], "assessments": [], "evidence": []}

    def fence(self, t, s, analytic):
        return self.fence_after


class Dispatch:
    """Per day: status (default CURRENT) and optional Candidate segments (start, end)."""

    def __init__(self, status: dict[date, str] | None = None,
                 segments: dict[date, list[tuple[datetime, datetime]]] | None = None,
                 indeterminate: dict[date, tuple[str, str]] | None = None) -> None:
        """`indeterminate` (PB-4): day -> (selected run cohort status, window limitation) of an INDETERMINATE window."""
        self.status, self.segments, self.indeterminate = status or {}, segments or {}, indeterminate or {}

    def window(self, t, s, day):
        status = self.status.get(day, "CURRENT")
        segs = [{"classification": dispatch_contract.CANDIDATE, "start": a.isoformat(), "end": b.isoformat()}
                for a, b in self.segments.get(day, [])]
        cohort, limit = self.indeterminate.get(day, ("SELECTED_UNIQUE", None))
        limits = [] if limit is None else [limit]
        window_rev = {} if limit is None else {"claim_level": "INDETERMINATE",
                                               "result": {"claim_level": "INDETERMINATE", "limitations": limits}}
        return {"status": status, "status_reasons": [] if status == "CURRENT" else [f"{status}: fake"],
                "selection": {"run_id": "r", "knowledge_cutoff": None, "cohort_status": cohort},
                "window_assessment": window_rev,
                "watermarks": None, "coverage": None, "limitations": limits, "current_basis": {},
                "intervals": [{"result": {"segments": segs}}] if segs else []}


def read(store, dispatch, lo: date, hi: date, limit: int = 50, cursor: str | None = None) -> dict[str, Any]:
    req = parse_request("mini-grid-dispatch", at(lo, 0).isoformat(), at(hi, 0).isoformat(), str(limit), cursor)
    return FindingIndexService(store, dispatch).read(T, S, "MG-1", req, access_basis="test")


def walk(store, dispatch, lo, hi, limit) -> list[tuple[list[str], int | None, bool]]:
    """Every page: (row titles, total_count, next_cursor present)."""
    pages, cursor = [], None
    while True:
        body = read(store, dispatch, lo, hi, limit, cursor)
        pages.append(([r["title"] for r in body["rows"]], body["total_count"], body["next_cursor"] is not None))
        cursor = body["next_cursor"]
        if not cursor:
            return pages


# ------------------------------------------------------------------ T1: v1 CURRENT bodies unchanged

def _t1_cases():
    three = [head(1, at(D6, 8), at(D6, 9)), head(2, at(D6, 10), at(D6, 11)), head(3, at(D7, 3), at(D7, 4))]
    return {
        "empty": (Store([], [D6, D7]), Dispatch(), D6, D8, 50),
        "one_row": (Store([head(1, at(D6, 8), at(D6, 9))], [D6]), Dispatch(), D6, D7, 50),
        "three_paged_by_2": (Store(three, [D6, D7]), Dispatch(), D6, D8, 2),
        "cross_midnight": (Store([head(4, at(D6, 23, 30), at(D7, 0, 40))], [D6, D7]), Dispatch(), D6, D8, 50),
        "merged_head": (Store([head(5, at(D6, 8), at(D6, 9)), head(6, at(D6, 8, 30), at(D6, 9), merged_into=fid(5))],
                              [D6], merges=[{"canonical_finding_id": fid(5), "superseded_finding_id": fid(6)}]),
                        Dispatch(), D6, D7, 50),
        "deferred_then_current": (Store([head(7, at(D6, 12), at(D6, 13))], [D6], deferred=[at(date(2026, 9, 1), 0)]),
                                  Dispatch(), D6, D7, 50),
    }


#: Recorded from a v1 run on ca6d7d61b (the packet lists the command): (row titles, total_count, next) per page.
T1_EXPECTED = {
    "empty": [([], 0, False)],
    "one_row": [(["F1"], 1, False)],
    "three_paged_by_2": [(["F3", "F2"], 3, True), (["F1"], 3, False)],
    "cross_midnight": [(["F4"], 1, False)],
    "merged_head": [(["F5"], 1, False)],
    "deferred_then_current": [(["F7"], 1, False)],
}


@pytest.mark.parametrize("name", sorted(T1_EXPECTED))
def test_t1_v1_current_bodies_unchanged(name: str) -> None:
    store, dispatch, lo, hi, limit = _t1_cases()[name]
    body = read(store, dispatch, lo, hi, limit)
    assert body["status"] == "CURRENT" and body["is_current"] is True
    assert body["gaps"] == [] and body["withheld"] is False and body["rows_statement"] is None
    assert walk(store, dispatch, lo, hi, limit) == T1_EXPECTED[name]


def test_v2_identity() -> None:
    body = read(Store([], [D6]), Dispatch(), D6, D7)
    assert body["schema_version"] == SCHEMA_VERSION == "site-finding-index-2"
    assert body["policy_version"] == POLICY_VERSION == "finding-index/2"
    assert body["selection_token"].startswith("sfi2-")


# ------------------------------------------------------------------ pure helpers

def test_touched_widens_by_the_continuity_tolerance() -> None:
    days = [D6, D7, D8]
    assert touched({"episode_start": at(D6, 8), "episode_end": at(D6, 9)}, days) == {D6}
    assert touched({"episode_start": at(D6, 23, 45), "episode_end": at(D6, 23, 58)}, days) == {D6, D7}
    assert touched({"episode_start": at(D7, 0, 21), "episode_end": at(D7, 23, 39)}, days) == {D7}
    assert touched({"episode_start": at(D7, 0, 10), "episode_end": at(D7, 1)}, days) == {D6, D7}
    # U1 review M1: both bounds are inclusive, as `reaches` and the matcher's margin (edge - 20 min, edge + 20 min)
    assert touched({"episode_start": at(D6, 23), "episode_end": at(D6, 23, 40)}, days) == {D6, D7}
    assert touched({"episode_start": at(D7, 0, 20), "episode_end": at(D7, 1)}, days) == {D6, D7}
    assert touched({"episode_start": at(D6, 23), "episode_end": at(D6, 23, 39)}, days) == {D6}
    assert touched({"episode_start": at(D7, 0, 21), "episode_end": at(D7, 1)}, days) == {D7}


def test_gap_days_names_non_current_and_edge_days() -> None:
    inspected = [{"day": d.isoformat(), "status": s} for d, s in ((D6, "CURRENT"), (D7, "PENDING"), (D8, "CURRENT"))]
    quiet = lambda day: (False, False)  # noqa: E731
    assert gap_days(inspected, quiet) == {D7: ("PENDING", "NOT_CURRENT")}
    reach = lambda day: (False, True) if day == D6 else (True, False) if day == D8 else (False, False)  # noqa: E731
    assert gap_days(inspected, reach) == {D6: ("CURRENT", "EDGE_NEXT_TO_GAP"), D7: ("PENDING", "NOT_CURRENT"),
                                          D8: ("CURRENT", "EDGE_NEXT_TO_GAP")}
    # an edge into a CURRENT neighbour is no gap; an edge out of the inspected range is
    assert gap_days(inspected[:1], lambda day: (False, True)) == {D6: ("CURRENT", "EDGE_NEXT_TO_GAP")}
    assert gap_days([inspected[0], inspected[2]], lambda day: (False, False)) == {}


# ------------------------------------------------------------------ T2-T8

def test_t2_one_unassessed_day_mid_window_is_partial_with_true_rows() -> None:
    store = Store([head(1, at(D6, 8), at(D6, 9))], [D6, D8])
    body = read(store, Dispatch({D7: "UNASSESSED"}), D6, date(2026, 10, 9))
    assert body["status"] == PARTIAL and body["is_current"] is False
    assert [r["title"] for r in body["rows"]] == ["F1"] and body["total_count"] == 1
    assert body["gaps"] == [{"day": "2026-10-07", "state": "UNASSESSED", "reason": "NOT_CURRENT"}]
    assert body["withheld"] is False
    assert body["rows_statement"].startswith("Rows from assessed days only")
    assert any(r.startswith("2026-10-07: ") for r in body["status_reasons"])


def test_t3_finding_next_to_an_unassessed_day_is_withheld() -> None:
    late, early = head(1, at(D6, 23, 45), at(D6, 23, 58)), head(2, at(D6, 8), at(D6, 9))
    store = Store([late, early], [D6])
    body = read(store, Dispatch({D7: "UNASSESSED"}), D6, D8)  # discover adds nothing: D7 requested
    assert body["status"] == PARTIAL
    assert [r["title"] for r in body["rows"]] == ["F2"] and body["total_count"] == 1
    assert body["gaps"] == [{"day": "2026-10-06", "state": "CURRENT", "reason": "WITHHELD_FINDING"},
                            {"day": "2026-10-07", "state": "UNASSESSED", "reason": "NOT_CURRENT"}]
    assert body["withheld"] is True


def test_t3b_episode_ending_exactly_the_tolerance_before_midnight_is_withheld() -> None:
    """U1 review M1: an episode ending at 23:40 is continuous with an UNASSESSED next day, so it is withheld."""
    store = Store([head(1, at(D6, 23), at(D6, 23, 40)), head(2, at(D6, 8), at(D6, 9))], [D6])
    body = read(store, Dispatch({D7: "UNASSESSED"}), D6, D8)
    assert body["status"] == PARTIAL and [r["title"] for r in body["rows"]] == ["F2"]
    assert body["withheld"] is True and body["total_count"] == 1
    assert {"day": "2026-10-06", "state": "CURRENT", "reason": "WITHHELD_FINDING"} in body["gaps"]


def test_t4_candidate_edge_next_to_a_pending_day() -> None:
    store = Store([head(1, at(D6, 8), at(D6, 9))], [D5 := date(2026, 10, 5), D6, D7])
    dispatch = Dispatch({D7: "PENDING"}, segments={D6: [(at(D6, 23, 50), at(D7, 0))]})
    body = read(store, dispatch, D5, D7)  # D6 reaches its end edge: D7 is inspected
    assert body["discovery"]["days"] == ["2026-10-05", "2026-10-06", "2026-10-07"]
    assert body["status"] == PARTIAL and body["rows"] == [] and body["total_count"] == 0
    assert body["gaps"] == [{"day": "2026-10-06", "state": "CURRENT", "reason": "EDGE_NEXT_TO_GAP"},
                            {"day": "2026-10-07", "state": "PENDING", "reason": "NOT_CURRENT"}]
    assert body["withheld"] is True
    one = read(store, dispatch, D6, D7)  # scenario A: the one-day window stays PENDING with no rows
    assert one["status"] == "PENDING" and one["rows"] == [] and one["total_count"] is None
    assert one["rows_statement"].startswith("No rows and no count")


def test_t5_every_requested_day_a_gap_keeps_the_v1_status() -> None:
    store = Store([head(1, at(D6, 8), at(D6, 9))], [])
    body = read(store, Dispatch({D6: "UNASSESSED", D7: "FAILED"}), D6, D8)
    assert body["status"] == "FAILED" and body["rows"] == [] and body["total_count"] is None
    assert body["next_cursor"] is None and body["withheld"] is False
    assert body["gaps"] == [{"day": "2026-10-06", "state": "UNASSESSED", "reason": "NOT_CURRENT"},
                            {"day": "2026-10-07", "state": "FAILED", "reason": "NOT_CURRENT"}]


def test_t6_fence_moved_gives_no_rows() -> None:
    store = Store([head(1, at(D6, 8), at(D6, 9))], [D6, D8])
    store.fence_after = "f2"
    body = read(store, Dispatch({D7: "UNASSESSED"}), D6, date(2026, 10, 9))
    assert body["status"] == "UNASSESSED" and body["rows"] == [] and body["total_count"] is None
    assert body["gaps"] == [{"day": "2026-10-07", "state": "UNASSESSED", "reason": "NOT_CURRENT"}]
    assert any("SELECTION_MOVED_DURING_READ" in r for r in body["status_reasons"])
    clean = Store([head(1, at(D6, 8), at(D6, 9))], [D6])
    clean.fence_after = "f2"
    body = read(clean, Dispatch(), D6, D7)
    assert body["status"] == "STALE_PROJECTION" and body["rows"] == [] and body["gaps"] == []


V1_CURSOR = (
    "eyJhZnRlciI6WyIyMDI2LTEwLTA2VDEwOjAwOjAwWiIsIjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMiJdLCJkb21haW4iOiJtaW5p"
    "LWdyaWQtZGlzcGF0Y2giLCJmcm9tIjoiMjAyNi0xMC0wNlQwMDowMDowMFoiLCJzZWxlY3Rpb25fdG9rZW4iOiJzZmkxLTk5MzMyM2U4NDMyODQ1"
    "MzUyYTc0OGU3NWQyZDBkZjMyYjdjMDEyMzAwOGQwYzhiYjRlYWY2MDFhZjBmNzE1NWIiLCJzaXRlX2lkIjoiMDAwMDAwMDAtMDAwMC0wMDAwLTAw"
    "MDAtMDAwMDAwMDAwMGIxIiwidGVuYW50X2lkIjoiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMGExIiwidG8iOiIyMDI2LTEwLTA5"
    "VDAwOjAwOjAwWiIsInYiOjF9")


def test_t7_partial_cursor_validates_on_its_basis_only() -> None:
    heads = [head(1, at(D6, 8), at(D6, 9)), head(2, at(D6, 10), at(D6, 11)), head(3, at(D8, 1), at(D8, 2))]
    store, gap = Store(heads, [D6, D8]), Dispatch({D7: "UNASSESSED"})
    hi = date(2026, 10, 9)
    first = read(store, gap, D6, hi, limit=2)
    assert first["status"] == PARTIAL and first["total_count"] == 3 and first["next_cursor"]
    assert [r["title"] for r in first["rows"]] == ["F3", "F2"]
    second = read(store, gap, D6, hi, limit=2, cursor=first["next_cursor"])
    assert [r["title"] for r in second["rows"]] == ["F1"] and second["next_cursor"] is None
    with pytest.raises(IndexConflict) as err:  # the gap day turns CURRENT: a new basis
        read(Store(heads, [D6, D7, D8]), Dispatch(), D6, hi, limit=2, cursor=first["next_cursor"])
    assert err.value.detail["reason"] == "SELECTION_CHANGED"
    # U1 review L1: a real v1 cursor, issued by the ca6d7d61b index on the same heads with every day CURRENT
    # (page one, limit 2). The v2 basis carries the policy, so it never validates, on CURRENT or PARTIAL data.
    for basis_store, dispatch in ((Store(heads, [D6, D7, D8]), Dispatch()), (store, gap)):
        with pytest.raises(IndexConflict) as err:
            read(basis_store, dispatch, D6, hi, limit=2, cursor=V1_CURSOR)
        assert err.value.detail["reason"] == "SELECTION_CHANGED"


def test_t8_pending_day_is_named_pending() -> None:
    seqs = {at(d, 0): (1 if d != D7 else 50) for d in (D6, D7, D8)}  # D7's selection is past the match pass
    store = Store([head(1, at(D6, 8), at(D6, 9))], [], seqs=seqs)
    body = read(store, Dispatch(), D6, date(2026, 10, 9))
    assert body["status"] == PARTIAL and [r["title"] for r in body["rows"]] == ["F1"]
    assert body["gaps"] == [{"day": "2026-10-07", "state": "PENDING", "reason": "NOT_CURRENT"}]


# ------------------------------------------------------------------ PB-4: a day that cannot be analysed is a gap

CONFLICT = ("AMBIGUOUS", "AMBIGUOUS_COHORT: two report series overlap for one channel")
TOO_FEW = ("EMPTY", "NO_COHORT: no accepted reading in the window")


def test_pb4_ambiguous_day_mid_window_is_partial_and_named_conflicting() -> None:
    """A selected run whose cohort is AMBIGUOUS is CURRENT in S3, yet the day was never analysed: the list is
    PARTIAL (never CURRENT) and the day carries the D-E5.46 reason READINGS_CONFLICT."""
    store = Store([head(1, at(D6, 8), at(D6, 9))], [D6, D7, D8])
    body = read(store, Dispatch(indeterminate={D7: CONFLICT}), D6, date(2026, 10, 9))
    assert body["status"] == PARTIAL and body["is_current"] is False
    assert [r["title"] for r in body["rows"]] == ["F1"] and body["total_count"] == 1
    assert body["gaps"] == [{"day": "2026-10-07", "state": "CURRENT", "reason": "READINGS_CONFLICT"}]
    assert body["withheld"] is False  # a data gap holds no analysis to wait for: nothing is withheld for it


def test_pb4_one_day_window_on_an_ambiguous_day_is_never_current() -> None:
    body = read(Store([], [D6]), Dispatch(indeterminate={D6: CONFLICT}), D6, D7)
    assert body["status"] == PARTIAL and body["is_current"] is False
    assert body["rows"] == [] and body["total_count"] == 0
    assert body["gaps"] == [{"day": "2026-10-06", "state": "CURRENT", "reason": "READINGS_CONFLICT"}]


def test_pb4_no_cohort_day_is_not_enough_readings() -> None:
    body = read(Store([], [D6, D7]), Dispatch(indeterminate={D7: TOO_FEW}), D6, D8)
    assert body["status"] == PARTIAL
    assert body["gaps"] == [{"day": "2026-10-07", "state": "CURRENT", "reason": "NOT_ENOUGH_READINGS"}]


def test_pb4_system_work_takes_precedence_over_the_data_reason() -> None:
    """A day still waiting on the system keeps NOT_CURRENT ("not analysed yet" is only for system work)."""
    body = read(Store([], [D6, D7]), Dispatch({D7: "PENDING"}, indeterminate={D7: CONFLICT}), D6, D8)
    assert body["gaps"] == [{"day": "2026-10-07", "state": "PENDING", "reason": "NOT_CURRENT"}]


def test_pb4_limited_window_is_not_a_gap() -> None:
    """A LIMITED (not INDETERMINATE) window with an ordinary limitation stays an analysed day."""
    class Limited(Dispatch):
        def window(self, t, s, day):
            out = super().window(t, s, day)
            out["limitations"] = ["MISSING_ROLE: pv_available is not bound"]
            out["window_assessment"] = {"claim_level": "LIMITED", "result": {"claim_level": "LIMITED"}}
            return out
    body = read(Store([], [D6]), Limited(), D6, D7)
    assert body["status"] == "CURRENT" and body["gaps"] == []
