"""OWN-G2 (build sheet OWN-GAPS §2.2, §2.7; R2-G2 Q8): the `fuel_night` stage in the tick, no DB, with the recording
`FakeStore`/`FakeRunner` of `test_w402_mini_stage.py` (as `test_fix_cold_drain_stage.py` uses them)."""

from __future__ import annotations

import pytest
from test_fix_cold_drain_stage import ORDER, NthLoss
from test_w402_mini_stage import FakeRunner, FakeStore, visit

from assetops_backend.scheduling.stages import STAGES
from assetops_backend.scheduling.tick import STAGE_LIMIT_FIELDS, TickLimits, TickReport


def test_exact_stage_order_marker_and_arguments() -> None:
    runner, store = FakeRunner(), FakeStore()
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ["s3", "cold_assess", "ev_assess", "mini", "fuel_night", "opportunity",
                                          "s4", "chain_threads", "consequence", "cold_consequence", "ev_consequence",
                                          "chain_snapshots"] == ORDER
    markers = [c[1] for c in store.calls if c[0] == "stage"]
    assert markers[3:5] == ["MINI", "MINI"]  # fuel_night re-checks the claim under the MINI head stage
    by = {c[0]: (c[1], c[2]) for c in runner.calls}
    args, seconds = by["fuel_night"]
    assert seconds == 90 and args["limit"] == 10 and args["deadline_at"] > 0
    assert set(args) == {"tenant_id", "site_id", "limit", "deadline_at"}
    assert site.result == "COMPLETED" and "fuel_night" in STAGES
    assert not [c for c in store.calls if c[0] not in ("stage", "claim", "release", "record_s3", "record_mini",
                                                       "record_opportunity", "record_s4", "record_consequence")]


@pytest.mark.parametrize("code", ["FAILED", "TIMEOUT", "UNAVAILABLE"])
def test_a_failing_fuel_night_fails_the_site_and_later_stages_still_run(code) -> None:
    runner, store = FakeRunner({"fuel_night": {"code": code, "error": "child"}}), FakeStore()
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ORDER
    assert site.result == "FAILED" and site.failure == ("FUEL_NIGHT", code, "child")
    assert store.calls[-1] == ("release", ("FUEL_NIGHT", code, "child"))
    # an earlier failure stays the first failure
    runner = FakeRunner({"mini": {"code": "FAILED", "error": "m"}, "fuel_night": {"code": code, "error": "child"}})
    assert visit(runner, FakeStore()).failure == ("MINI", "FAILED", "m")


def test_a_lost_claim_before_fuel_night_stops_the_site() -> None:
    runner, store = FakeRunner(), NthLoss(5)  # S3, S3, S3, MINI, then the fuel_night MINI re-check
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ORDER[:ORDER.index("fuel_night")]
    assert site.result == "CLAIM_LOST" and site.failure[:2] == ("MINI", "CLAIM_LOST")


def test_limits_bounds_lease_and_limit_field() -> None:
    limits = TickLimits()
    assert (limits.fuel_nights_per_site, limits.fuel_night_seconds) == (10, 90)
    with pytest.raises(ValueError, match="The fuel_night stage bound must be positive."):
        TickLimits(fuel_night_seconds=0)
    with pytest.raises(ValueError, match="at least 1"):
        TickLimits(fuel_nights_per_site=0)
    with pytest.raises(ValueError, match="statement timeout"):
        TickLimits(fuel_night_seconds=20, statement_timeout_ms=25_000)
    assert TickLimits(fuel_night_seconds=100).site_lease_seconds == limits.site_lease_seconds + 10
    assert TickLimits(fuel_night_seconds=31).site_lease_seconds == limits.site_lease_seconds - 59
    assert STAGE_LIMIT_FIELDS["fuel_night"] == "fuel_night_seconds"


def test_the_tick_report_carries_eligible() -> None:
    runner = FakeRunner({"fuel_night": {"code": "OK", "eligible": True, "processed": 2, "deferred": 0,
                                        "nights": [{"night_date": "2026-11-05"}]}})
    site = visit(runner, FakeStore())
    report = TickReport(outcome="COMPLETED", environment="test", token="x")
    report.selected = [site]
    entry = report.as_json()["sites"][0]["stages"]["fuel_night"]
    assert entry == {"code": "OK", "eligible": True, "processed": 2, "deferred": 0}
