"""W4-03 unit 4: the tick's OPPORTUNITY stage (`.agent/W4-03-build-spec.md` closure 4 S1, u3 "Unit 4 dry-read"):
order after MINI and before S4, limits and lease budget, counters only for an OK stage, a failed stage reported while
later stages still run, claim loss, and an opportunity-only Site kept scheduled. Pure (fake runner and store).
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from test_w402_mini_stage import FakeRunner, FakeStore, visit

from assetops_backend.mini_decisions.worker import MiniOpportunityWorker
from assetops_backend.scheduling.stages import OPPORTUNITY_JOB_LEASE_SECONDS, STAGES
from assetops_backend.scheduling.tick import TickLimits, select_sites

T, S = UUID(int=1), UUID(int=2)


def test_limits_and_lease_budget() -> None:
    limits = TickLimits()
    assert (limits.opportunity_jobs_per_site, limits.opportunity_seconds) == (10, 120)
    assert limits.site_lease_seconds == 120 + 120 + 120 + 120 + 60 + 60
    # u4b: the literal default, so a future stage change forces an explicit budget review.
    assert limits.site_lease_seconds == 600
    assert OPPORTUNITY_JOB_LEASE_SECONDS == 300 == MiniOpportunityWorker(None, None).lease.total_seconds()
    for bad in (0, -1, 300, 301):
        with pytest.raises(ValueError, match="OPPORTUNITY stage bound"):
            TickLimits(opportunity_seconds=bad)
    with pytest.raises(ValueError, match="at least 1"):
        TickLimits(opportunity_jobs_per_site=0)
    with pytest.raises(ValueError, match="statement timeout"):
        TickLimits(opportunity_seconds=20, statement_timeout_ms=25_000)
    assert "opportunity" in STAGES


def test_order_args_and_counts() -> None:
    runner = FakeRunner({"opportunity": {"code": "OK", "processed": 2, "deferred": 1, "failed": 1}})
    store = FakeStore()
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ["s3", "mini", "opportunity", "s4", "consequence"]
    assert [c[1] for c in store.calls if c[0] == "stage"] == ["S3", "MINI", "OPPORTUNITY", "S4", "CONSEQUENCE"]
    _, args, seconds = runner.calls[2]
    assert args == {"tenant_id": str(T), "site_id": str(S), "limit": 10} and seconds == 120
    assert ("record_opportunity", (2, 1, 1)) in store.calls
    assert site.result == "COMPLETED" and site.stages["opportunity"]["processed"] == 2


@pytest.mark.parametrize("code", ["TIMEOUT", "FAILED", "UNAVAILABLE"])
def test_failed_stage_is_reported_without_counts_and_later_stages_run(code) -> None:
    runner, store = FakeRunner({"opportunity": {"code": code, "error": "child died"}}), FakeStore()
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ["s3", "mini", "opportunity", "s4", "consequence"]
    assert not [c for c in store.calls if c[0] == "record_opportunity"]  # the prior durable counts are kept
    assert site.failure == ("OPPORTUNITY", code, "child died") and site.result == "FAILED"
    assert store.calls[-1] == ("release", ("OPPORTUNITY", code, "child died"))
    # An earlier MINI failure stays the first failure.
    runner = FakeRunner({"mini": {"code": "FAILED", "error": "m"}, "opportunity": {"code": code, "error": "o"}})
    assert visit(runner, FakeStore()).failure == ("MINI", "FAILED", "m")


def test_lost_claim_stops_before_the_opportunity_stage() -> None:
    runner, store = FakeRunner(), FakeStore(lose="OPPORTUNITY")
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ["s3", "mini"] and site.result == "CLAIM_LOST"
    assert site.failure[0] == "OPPORTUNITY" and not [c for c in store.calls if c[0] == "release"]


def test_opportunity_only_site_is_selected_and_failed_only_is_not() -> None:
    a, b, c = UUID(int=3), UUID(int=4), UUID(int=5)
    inventory = [{"tenant_id": T, "site_id": s, "site_code": code, "lifecycle": life, "has_evidence": False,
                  "enrolled": False} for s, code, life in ((a, "ONLY-OPP", "ACTIVE"), (b, "GONE", "DECOMMISSIONED"),
                                                           (c, "FAILED-ONLY", "ACTIVE"))]
    jobs = [{"id": uuid4(), "tenant_id": T, "site_id": s, "domain": "mini_opportunity", "status": st,
             "last_error": err} for s, st, err in ((a, "PENDING", None), (b, "LEASED", None), (c, "FAILED", "x"))]
    selected, excluded, not_selected = select_sites({"inventory": inventory, "live_jobs": [], "live_mini_jobs": [],
                                                     "live_opportunity_jobs": jobs, "pending_work_sites": []})
    assert [(s.site_code, s.reason) for s in selected] == [("ONLY-OPP", "EXCLUDED_WITH_WORK"),
                                                          ("GONE", "EXCLUDED_WITH_WORK")]
    assert not_selected == 1
    assert [(e["site_code"], [j["status"] for j in e["live_opportunity_jobs"]], e["live_mini_jobs"])
            for e in excluded] == [("ONLY-OPP", ["PENDING"], []), ("GONE", ["LEASED"], [])]


def test_run_pending_cli_parses_limit_and_calls_the_worker(monkeypatch) -> None:
    """u4b: `main(['run-pending', '--limit', '1'])` calls `run_pending(1)` on the built worker (stub, no database)."""
    from assetops_backend.mini_decisions import worker as worker_module

    calls: list[tuple] = []

    class StubStore:
        def dispose(self) -> None:
            calls.append(("dispose",))

    class StubWorker:
        store = StubStore()

        def run_pending(self, *args, **kwargs):
            calls.append(("run_pending", args, kwargs))
            return []

    monkeypatch.setenv("DATABASE_URL", "postgresql://stub")
    monkeypatch.setattr(worker_module, "build_worker", lambda url: StubWorker())
    assert worker_module.RUN_PENDING_COMMAND == "run-pending"
    assert worker_module.main(["run-pending", "--limit", "1"]) == 0
    assert calls == [("run_pending", (1,), {}), ("dispose",)]
