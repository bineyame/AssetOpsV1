"""COV-PARTIAL U1 (`estate-coverage/2`): the partly checked mini-grid Site rule and its `days` block over fake
one-transaction snapshots (build sheet COV-PARTIAL §2, T1-T12). No database."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from assetops_backend.estate import coverage
from assetops_backend.estate.index import _coverage_site, _status

T, S = "00000000-0000-4000-8000-00000000c001", "00000000-0000-4000-8000-00000000c011"
D0 = datetime(2026, 10, 6, tzinfo=timezone.utc)
K = D0 + timedelta(days=3)
FID, FRID = "00000000-0000-4000-8000-00000000c101", "00000000-0000-4000-8000-00000000c102"
PRICED = {"consequence_revision_id": "c1", "consequence_state": "PRICED", "currentness": {"state": "CURRENT"},
          "amount_low": "10.00", "amount_high": "12.50", "currency": "USD",
          "cited": {"assumption_revision_ids": ["p1"], "power_evidence_ids": ["e2"]}}
NULL_AMOUNTS = {"amount": None, "amount_low": None, "amount_high": None, "currency": None}


class Snap:
    """A live estate snapshot double: the given dispatch days and Finding heads, one matched pass at seq 5."""

    def __init__(self, days, heads=(), consequence=None, historical=False) -> None:
        self.read_at, self.historical, self.continuation = K, historical, False
        self.basis_historical = historical
        self._days, self._heads, self._consequence = list(days), list(heads), consequence

    def evidence_cutoff(self, t, s, k):
        return D0

    def dispatch_days(self, t, s, from_, to, k):
        return self._days

    def finding_index(self, t, s, k):
        return {"heads": self._heads, "deferred_windows": [], "match_pass": {"matched_through_selection_seq": 5}}

    def finding_lineage(self, t, s, ids, k):
        return {"evidence": [{"finding_revision_id": h["finding_revision_id"], "evidence_id": "e1"}
                             for h in self._heads], "assessments": [{"assessment_revision_id": "a1"}]}

    def finding_provenance(self, *a):
        return {"state": "AUTHORED_DEMONSTRATION"}

    def consequence(self, *a):
        return self._consequence or {"consequence_revision_id": None}

    def consequence_provenance(self, *a):
        return {"classification": "AUTHORED_DEMONSTRATION", "state": "AUTHORED_DEMONSTRATION", "source_ids": [],
                "evidence_ids": [], "basis_sha256": "sha256:c", "reasons": []}

    def eligibility(self, *a):
        return {"state": "ELIGIBLE"}


def day(n: int, status="CURRENT", selected=True, available=True, jobs=(), base=D0) -> dict:
    start = base + timedelta(days=n)
    return {"day": start.date(), "available": available, "selection": {"seq": 5} if selected else None,
            "status": status, "jobs": list(jobs), "window_start": start,
            "assessment_revision_ids": [f"a{n}"], "window_assessment_revision_id": f"w{n}"}


def head(start: datetime, end: datetime | None, n: int = 0) -> dict:
    return {"finding_id": f"{FID[:-1]}{n}", "finding_revision_id": f"{FRID[:-1]}{n}", "merged_into_finding_id": None,
            "lifecycle": "SUPPORTED", "title": "t", "episode_start": start, "episode_end": end}


def cov(days, n_days=None, **kw) -> dict:
    n = len(days) if n_days is None else n_days
    return coverage.site_coverage(Snap(days, **kw), T, S, coverage.MINI_GRID, D0, D0 + timedelta(days=n), K)


def without_days(body: dict) -> dict:
    assert "days" in body
    return {k: v for k, v in body.items() if k != "days"}


# T1: every combination that is not PARTIAL keeps today's state and body; `days` is the only addition.
@pytest.mark.parametrize("days,state", [
    ([day(0)], "CURRENT"),
    ([day(0), day(1)], "CURRENT"),
    ([day(0, status="PENDING")], "PENDING_RECOMPUTE"),
    ([day(0, status="STALE_PROJECTION")], "STALE_SOURCE"),
    ([day(0, available=False)], "UNKNOWN"),
    ([day(0, selected=False)], "UNKNOWN"),
    ([day(0), day(1, status="OTHER")], "UNKNOWN"),
])
def test_t1_existing_states_unchanged_plus_days(days, state) -> None:
    body = cov(days, heads=[head(D0 + timedelta(hours=8), D0 + timedelta(hours=9))])
    assert body["state"] == state
    assert set(without_days(body)) == set(coverage._empty(state)) - {"days"}
    assert body["days"]["policy"] == "estate-coverage/2" and body["days"]["text"] is None
    if state == "CURRENT":
        assert len(body["rows"]) == 1 and body["source_freshness"] == "RECENT"
    else:
        assert body["rows"] == []


def test_t2_gap_with_clean_checked_day_is_partial() -> None:
    body = cov([day(0), day(1, selected=False)], heads=[head(D0 + timedelta(hours=8), D0 + timedelta(hours=9))])
    assert (body["state"], body["match_state"], body["job_state"], body["source_freshness"]) == (
        "PARTIAL", "COMPLETE", "SETTLED", "RECENT")
    assert body["selection_id"] == "w0"
    assert body["days"] == {"policy": "estate-coverage/2", "requested": 2, "checked": 1,
                            "gaps": [{"day": "2026-10-07", "state": "UNASSESSED", "reason": "NO_ASSESSED_SELECTION"}],
                            "withheld": False, "text": "1 of 2 days checked · 1 day not available yet"}
    assert [r["finding_id"] for r in body["rows"]] == [f"{FID[:-1]}0"]
    assert "PARTIAL" not in coverage.COVERED


@pytest.mark.parametrize("other", [day(0, status="PENDING"), day(0, jobs=[{"status": "LEASED"}]),
                                   day(0, status="FAILED")])
def test_t3_gap_beside_pending_is_unknown(other) -> None:
    body = cov([other, day(1, selected=False)])
    assert body["state"] == "UNKNOWN" and body["rows"] == [] and body["days"]["text"] is None


def test_t4_gap_beside_stale_is_unknown() -> None:
    body = cov([day(0, status="STALE_PROJECTION"), day(1, available=False)])
    assert body["state"] == "UNKNOWN" and body["source_freshness"] == "UNKNOWN" and body["days"]["text"] is None


def test_t5_all_gaps_is_unknown() -> None:
    body = cov([day(0, selected=False), day(1, available=False), day(2, selected=False)])
    assert body["state"] == "UNKNOWN" and body["rows"] == []
    assert body["days"]["checked"] == 0 and body["days"]["requested"] == 3 and body["days"]["text"] is None
    assert [g["day"] for g in body["days"]["gaps"]] == ["2026-10-06", "2026-10-07", "2026-10-08"]


def test_t6_historical_gap_is_unknown() -> None:
    body = cov([day(0), day(1, selected=False)], historical=True)
    assert body["state"] == "UNKNOWN" and body["source_freshness"] == "UNKNOWN" and body["days"]["text"] is None


def test_t7_head_next_to_a_gap_is_withheld() -> None:
    late = head(D0 + timedelta(hours=23, minutes=50), D0 + timedelta(hours=23, minutes=58), 1)
    morning = head(D0 + timedelta(hours=8), D0 + timedelta(hours=9), 2)
    body = cov([day(0), day(1, selected=False)], heads=[late, morning])
    assert body["state"] == "PARTIAL"
    assert [r["finding_id"] for r in body["rows"]] == [morning["finding_id"]]
    assert body["selected_finding_revision_ids"] == [morning["finding_revision_id"]]
    assert body["days"]["withheld"] is True
    assert body["days"]["text"] == ("1 of 2 days checked · 1 day not available yet"
                                    "; Findings next to those days are not shown yet")
    # an open episode reads through the cutoff, so it reaches the gap day and is withheld
    body = cov([day(0), day(1, selected=False)], heads=[head(D0 + timedelta(hours=8), None)])
    assert body["rows"] == [] and body["days"]["withheld"] is True


def test_t8_priced_head_on_partial_site_carries_no_amount() -> None:
    body = cov([day(0), day(1, selected=False)], heads=[head(D0 + timedelta(hours=8), D0 + timedelta(hours=9))],
               consequence=PRICED)
    (row,) = body["rows"]
    assert row["consequence"] == {"state": "UNKNOWN", **NULL_AMOUNTS, "source_revision_id": "c1"}
    assert body["selected_consequence_revision_ids"] == ["c1"]


def test_t9_day_count_mismatch_is_unknown_without_days() -> None:
    body = cov([day(0), day(1, selected=False)], n_days=3)
    assert body["state"] == "UNKNOWN" and body["days"] is None and body["source_freshness"] == "UNKNOWN"
    clean = cov([day(0), day(1)], n_days=3)  # no gap: today's rule unchanged, still no day count published
    assert clean["state"] == "CURRENT" and clean["days"] is None


def test_t10_one_day_is_never_partial() -> None:
    for d in (day(0), day(0, selected=False), day(0, available=False), day(0, status="PENDING")):
        assert cov([d])["state"] != "PARTIAL"


def test_t11_partial_never_reads_current_at_the_root() -> None:
    assert _status(False, ["CURRENT", "PARTIAL"]) == "UNKNOWN"
    assert _status(False, ["PARTIAL"]) == "UNKNOWN"
    assert _status(False, ["CURRENT", "PARTIAL", "PENDING_RECOMPUTE"]) == "PENDING_RECOMPUTE"
    assert _status(True, ["PARTIAL"]) == "HISTORICAL"
    assert _status(False, ["CURRENT"]) == "CURRENT"


def test_t12_windowed_and_actions_carry_null_days() -> None:
    assert coverage.not_applicable()["days"] is None
    assert coverage._empty("UNKNOWN")["days"] is None
    body = cov([day(0), day(1, selected=False)])
    wire = _coverage_site({"site_id": S}, body)
    assert wire["days"] == body["days"] and wire["state"] == "PARTIAL"
    assert _coverage_site({"site_id": S}, coverage.not_applicable())["days"] is None

    class Cold:
        read_at, historical, continuation, basis_historical = K, False, False, False

        def evidence_cutoff(self, *a):
            return D0 + timedelta(hours=10)

        def selected_windows(self, *a):
            return [{"selection_id": "sel-1", "seq": 1, "selected_at": D0, "state": coverage.CURRENT,
                     "window_start": D0 + timedelta(hours=8), "window_end": D0 + timedelta(hours=9),
                     "probe_fresh": True, "assessment_revision_ids": ["a-1"], "evidence_ids": ["e-1"],
                     "findings": []}]

        def open_jobs(self, *a):
            return []

    for domain in (coverage.COLD, coverage.EV):
        windowed = coverage.site_coverage(Cold(), T, S, domain, D0, D0 + timedelta(days=1), K)
        assert windowed["days"] is None and windowed["state"] != "PARTIAL"
