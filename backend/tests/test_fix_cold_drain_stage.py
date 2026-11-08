"""FIX-COLD-DRAIN U3 (pure): the tick's cold/EV assessment children after `s3` and cold/EV consequence drains after
`consequence` (build sheet section 2): exact order, limits and Site lease, first-failure retention with later children
still running, a lost claim stopping the Site before a new child, and the summed S3/consequence head counts.

The stage runner and schedule store are the recording fakes of `test_w402_mini_stage.py`;
`test_fix_cold_drain_tick_postgres.py` proves the real stage children against PostgreSQL.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from test_w402_mini_stage import FakeRunner, FakeStore, visit

from assetops_backend.analytics.assessment_worker import ColdAssessmentWorker, EvAssessmentWorker
from assetops_backend.scheduling.stages import DOMAIN_JOB_LEASE_SECONDS, STAGES
from assetops_backend.scheduling.tick import TickLimits

T, S = UUID(int=1), UUID(int=2)
ORDER = ["s3", "cold_assess", "ev_assess", "mini", "fuel_night", "opportunity", "s4", "chain_threads", "consequence",
         "cold_consequence", "ev_consequence", "chain_snapshots"]  # CH-2 chain_threads; CH-1b chain_snapshots
NEW = {"cold_assess": "COLD_ASSESS", "ev_assess": "EV_ASSESS", "cold_consequence": "COLD_CONSEQUENCE",
       "ev_consequence": "EV_CONSEQUENCE"}


class NthLoss(FakeStore):
    """Loses the Site claim at the `nth` (1-based) `set_stage` call, whatever its marker."""

    def __init__(self, nth: int) -> None:
        super().__init__()
        self.nth, self.seen = nth, 0

    def set_stage(self, t, s, token, stage):
        self.seen += 1
        self.calls.append(("stage", stage))
        return self.seen != self.nth


def test_t1_exact_order_markers_and_arguments() -> None:
    runner, store = FakeRunner(), FakeStore()
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ORDER
    assert [c[1] for c in store.calls if c[0] == "stage"] == ["S3", "S3", "S3", "MINI", "MINI", "OPPORTUNITY", "S4", "S4",
                                                               "CONSEQUENCE", "CONSEQUENCE", "CONSEQUENCE",
                                                               "CONSEQUENCE"]  # CH-2 S4 chain_threads; CH-1b
    by = {c[0]: (c[1], c[2]) for c in runner.calls}
    ids = {"tenant_id": str(T), "site_id": str(S)}
    assert by["cold_assess"] == ({**ids, "limit": 10}, 120) == by["ev_assess"]
    for name in ("cold_consequence", "ev_consequence"):
        args, seconds = by[name]
        assert seconds == 60 and args["limit"] == 50 and args["now"].startswith("2026-10-21")
    assert site.result == "COMPLETED" and site.failure is None
    assert set(NEW) <= set(STAGES) and set(NEW) <= set(site.stages)


def test_t2_limits_and_lease_sum() -> None:
    limits = TickLimits()
    assert (limits.domain_jobs_per_site, limits.domain_assess_seconds, limits.domain_consequence_seconds) == (
        10, 120, 60)
    assert limits.site_lease_seconds == (limits.s3_seconds + limits.mini_seconds + limits.opportunity_seconds
                                         + limits.s4_seconds + limits.consequence_seconds
                                         + 2 * 120 + 2 * 60 + 60
                                         + limits.chain_seconds + limits.chain_snapshot_seconds
                                         + limits.fuel_night_seconds) == 1170  # OWN-G2 fuel_night
    assert DOMAIN_JOB_LEASE_SECONDS == 300
    assert ColdAssessmentWorker(None, None).lease.total_seconds() == 300 == EvAssessmentWorker(
        None, None).lease.total_seconds()
    for bad in (0, -1, 300, 301):
        with pytest.raises(ValueError, match="cold/EV assessment stage bound"):
            TickLimits(domain_assess_seconds=bad)
    assert TickLimits(domain_assess_seconds=299).domain_assess_seconds == 299
    with pytest.raises(ValueError, match="at least 1"):
        TickLimits(domain_jobs_per_site=0)
    for field in ("domain_assess_seconds", "domain_consequence_seconds"):
        with pytest.raises(ValueError, match="statement timeout"):
            TickLimits(**{field: 20}, statement_timeout_ms=25_000)


@pytest.mark.parametrize("name", list(NEW))
@pytest.mark.parametrize("code", ["FAILED", "TIMEOUT", "CONSEQUENCE_CLAIMED"])
def test_t3_new_child_failure_is_first_failure_and_later_children_run(name, code) -> None:
    runner, store = FakeRunner({name: {"code": code, "error": "child"}}), FakeStore()
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ORDER  # later children still ran
    assert site.failure == (NEW[name], code, "child") and site.result == "FAILED"
    assert store.calls[-1] == ("release", (NEW[name], code, "child"))
    # An earlier failure stays the first failure.
    runner = FakeRunner({"s3": {"code": "FAILED", "error": "s3"}, name: {"code": code, "error": "child"}})
    assert visit(runner, FakeStore()).failure == ("S3", "FAILED", "s3")


@pytest.mark.parametrize("nth,name", [(2, "cold_assess"), (3, "ev_assess"), (10, "cold_consequence"),
                                      (11, "ev_consequence")])  # CH-2/CH-1b: the S4 chain_threads marker; OWN-G2 MINI
def test_t4_lost_claim_stops_before_a_new_child(nth, name) -> None:
    runner, store = FakeRunner(), NthLoss(nth)
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ORDER[:ORDER.index(name)]
    marker = "S3" if name.endswith("assess") else "CONSEQUENCE"
    assert site.result == "CLAIM_LOST" and site.failure[:2] == (marker, "CLAIM_LOST")
    assert not [c for c in store.calls if c[0] == "release"]


def test_t5_summed_s3_and_consequence_counts() -> None:
    runner = FakeRunner({"s3": {"code": "OK", "processed": 1, "deferred": 2},
                         "cold_assess": {"code": "OK", "processed": 3, "deferred": 4, "failed": 0},
                         "ev_assess": {"code": "OK", "processed": 5, "deferred": 6, "failed": 1},
                         "consequence": {"code": "OK", "selected": 7, "deferred": 8},
                         "cold_consequence": {"code": "OK", "selected": 9, "deferred": 10},
                         "ev_consequence": {"code": "OK", "selected": 11, "deferred": 12}})
    store = FakeStore()
    visit(runner, store)
    assert [c for c in store.calls if c[0] == "record_s3"] == [("record_s3", (9, 12))]
    assert [c for c in store.calls if c[0] == "record_consequence"] == [("record_consequence", (27, 30))]
    # A non-OK child adds 0; the others are still summed.
    runner = FakeRunner({"s3": {"code": "OK", "processed": 1, "deferred": 2},
                         "cold_assess": {"code": "TIMEOUT", "error": "x"},
                         "ev_assess": {"code": "OK", "processed": 5, "deferred": 6, "failed": 0},
                         "consequence": {"code": "FAILED", "error": "y"},
                         "cold_consequence": {"code": "OK", "selected": 9, "deferred": 10},
                         "ev_consequence": {"code": "CONSEQUENCE_CLAIMED", "error": None}})
    store = FakeStore()
    site = visit(runner, store)
    assert [c for c in store.calls if c[0] == "record_s3"] == [("record_s3", (6, 8))]
    assert [c for c in store.calls if c[0] == "record_consequence"] == [("record_consequence", (9, 10))]
    assert site.failure[:2] == ("COLD_ASSESS", "TIMEOUT")
    # A group whose every child failed writes no invented counts.
    runner = FakeRunner({x: {"code": "FAILED", "error": x} for x in ("s3", "cold_assess", "ev_assess")})
    store = FakeStore()
    visit(runner, store)
    assert not [c for c in store.calls if c[0] == "record_s3"]
