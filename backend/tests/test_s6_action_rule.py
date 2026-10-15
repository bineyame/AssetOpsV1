"""S6-01a phase 1: `reserve-trial-1` boundaries, the Action transition table, exact-history selectors and the
scoped SYSTEM demonstration capability (pure; no database)."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from assetops_backend.actions import reserve_trial as rt
from assetops_backend.actions.capability import from_grants, no_capability
from assetops_backend.actions.lifecycle import (
    ACCEPTED,
    APPLIED,
    FAILED,
    NONE_AT_CUTOFF,
    OBSERVED,
    PENDING,
    SelectorConflict,
    UnknownEvent,
    reduce,
    select,
    selector,
)

T0 = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)
BATTERY = uuid4()
OTHER = uuid4()
F_PIN, F_NOW = uuid4(), uuid4()


def reading(value: str | None, *, at: datetime = T0, asset: UUID | None = BATTERY, unit: str = "%",
            quality: str = "GOOD") -> rt.SocReading:
    return rt.SocReading(uuid4(), asset, value, unit, quality, at, "a" * 64)


def basis(value, *, rid: UUID = F_PIN, unit="%", asset: UUID | None = BATTERY, extra: int = 0) -> rt.FoundationBasis:
    entries = [rt.ReserveEntry("battery", asset, value, unit)]
    entries += [rt.ReserveEntry(f"battery-{i}", uuid4(), value, unit) for i in range(extra)]
    return rt.FoundationBasis(rid, tuple(entries))


def segment(*soc: rt.SocReading, reserve=20, start: datetime = T0, foundations=None) -> rt.Segment:
    return rt.Segment(uuid4(), start, start + timedelta(minutes=20), tuple(soc),
                      (basis(reserve),) if foundations is None else foundations)


def inputs(*segments: rt.Segment, current=None, **over) -> rt.RuleInputs:
    base = rt.RuleInputs(tenant_id=uuid4(), site_id=uuid4(), finding_id=uuid4(), finding_revision_id=uuid4(),
                         mechanism=rt.MECHANISM, lifecycle="SUPPORTED", is_latest=True, claim_is_current=True,
                         primary_assessment_revision_id=uuid4(), segments=segments,
                         current_foundation=basis(20, rid=F_NOW) if current is None else current)
    return replace(base, **over)


def reason(evaluation: rt.Evaluation) -> str | None:
    return evaluation.reason


class TestEligibleProposal:
    def test_reserve_twenty_proposes_fifteen_with_pins(self) -> None:
        soc = reading("80")
        got = rt.evaluate(inputs(segment(soc)))
        assert got.available and got.reason is None
        p = got.proposal
        assert (p["old_value"], p["proposed_value"], p["unit"], p["field"]) == ("20", "15", "%", rt.FIELD)
        assert p["foundation_revision_id"] == str(F_PIN) and p["current_foundation_revision_id"] == str(F_NOW)
        assert p["asset_id"] == str(BATTERY)
        assert p["rule"]["id"] == "reserve-trial-1" and p["rule"]["version"] == 1
        assert p["limitation"]["code"] == rt.LIMITATION_CODE
        [seg] = p["inputs"]["segments"]
        assert seg["selected_soc"]["evidence_id"] == str(soc.evidence_id) and seg["soc_threshold"] == "30"
        assert p["input_sha256"] == rt.sha(p["inputs"])
        key = p["key"]
        assert set(key) == {"tenant_id", "site_id", "finding_revision_id", "foundation_revision_id", "rule_id",
                            "rule_version", "asset_id"}
        assert p["recommendation_key"] == rt.key_digest(key) and p["acceptance_key"] == rt.acceptance_key(key)
        assert p["acceptance_key"] != p["recommendation_key"]

    def test_the_key_includes_the_pinned_foundation(self) -> None:
        a = rt.recommendation_key(BATTERY, BATTERY, BATTERY, F_PIN, BATTERY)
        b = rt.recommendation_key(BATTERY, BATTERY, BATTERY, F_NOW, BATTERY)
        assert rt.key_digest(a) != rt.key_digest(b) and rt.acceptance_key(a) != rt.acceptance_key(b)


class TestSocHeadroomBoundary:
    @pytest.mark.parametrize(("soc", "eligible"), [("30", False), ("30.0", False), ("30.0001", True),
                                                   ("29.9", False), ("31", True)])
    def test_soc_must_be_strictly_above_reserve_plus_ten(self, soc: str, eligible: bool) -> None:
        got = rt.evaluate(inputs(segment(reading(soc))))
        assert got.available is eligible
        if not eligible:
            assert got.reason == "SOC_NOT_ABOVE_HEADROOM"

    def test_the_lowest_usable_reading_decides(self) -> None:
        later = T0 + timedelta(minutes=20)
        got = rt.evaluate(inputs(segment(reading("80"), reading("30", at=later))))
        assert got.reason == "SOC_NOT_ABOVE_HEADROOM"


class TestReserveBand:
    @pytest.mark.parametrize(("reserve", "proposed"), [(15, "10"), (90, "85"), ("15.0", "10"), (47.5, "42.5")])
    def test_reserve_inside_the_band(self, reserve, proposed: str) -> None:
        # Reserve 90 needs SOC above 100 %, so it is in band but unreachable by a physical reading; the band
        # boundary itself is proven with a rule-level number.
        got = rt.evaluate(inputs(segment(reading("100.5"), reserve=reserve), current=basis(reserve, rid=F_NOW)))
        assert got.available and got.proposal["proposed_value"] == proposed

    @pytest.mark.parametrize("reserve", [14.99, 90.01, 10, 95])
    def test_reserve_just_outside_the_band(self, reserve) -> None:
        got = rt.evaluate(inputs(segment(reading("106"), reserve=reserve), current=basis(reserve, rid=F_NOW)))
        assert got.reason == "RESERVE_OUT_OF_BAND"


class TestUnavailableReasons:
    @pytest.mark.parametrize(("over", "code"), [
        ({"mechanism": "OTHER"}, "FINDING_KIND_UNSUPPORTED"),
        ({"lifecycle": "UNCONFIRMED"}, "FINDING_NOT_SUPPORTED"),
        ({"lifecycle": "NO_LONGER_SUPPORTED"}, "FINDING_NOT_SUPPORTED"),
        ({"is_latest": False}, "FINDING_REVISION_NOT_LATEST"),
        ({"claim_is_current": False}, "FINDING_NOT_CURRENT"),
    ])
    def test_revision_gates(self, over, code) -> None:
        assert reason(rt.evaluate(inputs(segment(reading("80")), **over))) == code

    def test_absent_candidate(self) -> None:
        assert reason(rt.evaluate(inputs())) == "CANDIDATE_ABSENT"

    def test_missing_soc(self) -> None:
        assert reason(rt.evaluate(inputs(segment()))) == "SOC_MISSING"

    @pytest.mark.parametrize("bad", [reading(None), reading("abc"), reading("80", unit="fraction"),
                                     reading("80", quality="SUSPECT"), reading("NaN"), reading("Infinity")])
    def test_non_numeric_soc(self, bad) -> None:
        assert reason(rt.evaluate(inputs(segment(bad)))) == "SOC_NOT_NUMERIC"

    def test_conflicting_soc_at_one_instant(self) -> None:
        assert reason(rt.evaluate(inputs(segment(reading("80"), reading("81"))))) == "SOC_CONFLICTING"

    def test_equal_duplicates_are_not_conflicting(self) -> None:
        assert rt.evaluate(inputs(segment(reading("80"), reading("80.0")))).available

    def test_soc_from_another_asset(self) -> None:
        assert reason(rt.evaluate(inputs(segment(reading("80", asset=OTHER))))) == "ASSET_MISMATCH"

    def test_missing_and_conflicting_reserve(self) -> None:
        none = rt.FoundationBasis(F_PIN, ())
        assert reason(rt.evaluate(inputs(segment(reading("80"), foundations=(none,))))) == "RESERVE_MISSING"
        assert reason(rt.evaluate(inputs(segment(reading("80"), foundations=())))) == "RESERVE_MISSING"
        two = basis(20, extra=1)
        assert reason(rt.evaluate(inputs(segment(reading("80"), foundations=(two,))))) == "RESERVE_CONFLICTING"
        both = (basis(20), basis(20, rid=uuid4()))
        assert reason(rt.evaluate(inputs(segment(reading("80"), foundations=both)))) == "RESERVE_CONFLICTING"

    @pytest.mark.parametrize(("value", "unit"), [(20, "fraction"), ("twenty", "%"), (None, "%"), (True, "%")])
    def test_reserve_unit_or_number_invalid(self, value, unit) -> None:
        bad = basis(value, unit=unit)
        assert reason(rt.evaluate(inputs(segment(reading("80"), foundations=(bad,))))) == "RESERVE_UNIT_INVALID"

    def test_stale_current_basis(self) -> None:
        assert reason(rt.evaluate(inputs(segment(reading("80")), current=basis(25, rid=F_NOW)))) == (
            "FOUNDATION_BASIS_STALE")

    def test_current_reserve_on_another_asset_is_stale(self) -> None:
        assert reason(rt.evaluate(inputs(segment(reading("80")), current=basis(20, rid=F_NOW, asset=OTHER)))) == (
            "FOUNDATION_BASIS_STALE")

    def test_no_single_current_foundation(self) -> None:
        got = rt.evaluate(replace(inputs(segment(reading("80"))), current_foundation=None))
        assert got.reason == "CURRENT_FOUNDATION_MISSING"

    def test_reasons_are_all_typed(self) -> None:
        got = rt.evaluate(inputs(segment()))
        assert got.unavailable() == {"code": "SOC_MISSING", "message": rt.REASONS["SOC_MISSING"]}

    def test_latest_ineligible_segment_names_the_reason(self) -> None:
        early, late = segment(reading("80", quality="BAD")), segment(start=T0 + timedelta(hours=1))
        assert reason(rt.evaluate(inputs(early, late))) == "SOC_MISSING"

    def test_any_eligible_segment_is_enough_and_is_cited(self) -> None:
        ok = segment(reading("80"))
        bad = segment(start=T0 + timedelta(hours=1))
        got = rt.evaluate(inputs(ok, bad))
        assert got.available
        assert [s["assessment_revision_id"] for s in got.proposal["inputs"]["segments"]] == [
            str(ok.assessment_revision_id)]


def event(kind: str, at: datetime, eid: str | None = None, failure: str | None = None) -> dict:
    return {"id": UUID(eid) if eid else uuid4(), "kind": kind, "recorded_at": at, "failure_code": failure}


class TestTransitionTable:
    def test_states(self) -> None:
        a = event(ACCEPTED, T0)
        assert reduce([])["application"] == NONE_AT_CUTOFF
        assert reduce([a])["application"] == PENDING
        assert reduce([a, event(OBSERVED, T0 + timedelta(1))])["application"] == PENDING
        failed = reduce([a, event(FAILED, T0 + timedelta(1), failure="ACTION_FOUNDATION_STALE")])
        assert failed["application"] == PENDING and failed["failed_attempts"] == 1
        assert failed["last_failure"]["failure_code"] == "ACTION_FOUNDATION_STALE"
        applied = reduce([a, event(FAILED, T0 + timedelta(1), failure="X_Y"), event(APPLIED, T0 + timedelta(2))])
        assert applied["application"] == APPLIED and applied["application_attempts"] == 2

    def test_a_late_failed_never_reverts_applied(self) -> None:
        got = reduce([event(ACCEPTED, T0), event(APPLIED, T0 + timedelta(1)),
                      event(FAILED, T0 + timedelta(2), failure="ACTION_FOUNDATION_STALE")])
        assert got["application"] == APPLIED

    def test_applied_without_accepted_is_not_applied(self) -> None:
        assert reduce([event(APPLIED, T0)])["application"] == NONE_AT_CUTOFF

    def test_outcome_is_never_inferred(self) -> None:
        got = reduce([event(ACCEPTED, T0), event(APPLIED, T0 + timedelta(1))])
        assert got["outcome"]["state"] == "PENDING"

    def test_order_is_recorded_at_then_id(self) -> None:
        # APPLIED recorded before ACCEPTED in server order cannot apply.
        got = reduce([event(APPLIED, T0), event(ACCEPTED, T0 + timedelta(seconds=1))])
        assert got["application"] == PENDING


class TestSelectors:
    def test_conflict_and_naive_instant(self) -> None:
        with pytest.raises(SelectorConflict):
            selector(uuid4(), T0)
        with pytest.raises(ValueError):
            selector(None, datetime(2026, 10, 6))

    def test_ties_exact_event_and_cutoff(self) -> None:
        ids = sorted(str(uuid4()) for _ in range(3))
        tie_a, tie_b = event(ACCEPTED, T0, ids[1]), event(OBSERVED, T0, ids[0])
        later = event(OBSERVED, T0 + timedelta(minutes=1), ids[2])
        rows = [later, tie_a, tie_b]
        assert [str(e["id"]) for e in select(rows, selector(None, None))] == [ids[0], ids[1], ids[2]]
        assert [str(e["id"]) for e in select(rows, selector(None, T0))] == [ids[0], ids[1]]
        assert [str(e["id"]) for e in select(rows, selector(UUID(ids[0]), None))] == [ids[0]]
        assert [str(e["id"]) for e in select(rows, selector(UUID(ids[1]), None))] == [ids[0], ids[1]]
        assert select(rows, selector(None, T0 - timedelta(seconds=1))) == []
        with pytest.raises(UnknownEvent):
            select(rows, selector(uuid4(), None))

    def test_selector_query_is_url_safe(self) -> None:
        assert selector(None, T0).query() == "?recorded_at=2026-10-06T08%3A00%3A00%2B00%3A00"


class TestCapability:
    GRANTS = {"schema": "assetops.action-demo-grants", "version": 1, "fixture_id": "D-action-records-v1",
              "grants": [{"site_code": "KOBO-001", "commands": ["ACCEPT", "OBSERVE"]}]}

    def test_scoped_grant(self) -> None:
        check = from_grants(self.GRANTS)
        t, s = uuid4(), uuid4()
        assert check(t, s, "KOBO-001", "ACCEPT").allowed
        assert check(t, s, "kobo-001", "OBSERVE").fixture_id == "D-action-records-v1"
        denied = check(t, s, "KOBO-001", "APPLY")
        assert not denied.allowed and "does not include APPLY" in denied.unavailable_reason
        assert not check(t, s, "OTHER-1", "ACCEPT").allowed

    def test_pinned_site_and_tenant(self) -> None:
        t, s = uuid4(), uuid4()
        doc = {**self.GRANTS, "grants": [{"site_code": "KOBO-001", "site_id": str(s), "tenant_id": str(t),
                                          "commands": ["ACCEPT"]}]}
        assert from_grants(doc)(t, s, "KOBO-001", "ACCEPT").allowed
        assert not from_grants(doc)(t, uuid4(), "KOBO-001", "ACCEPT").allowed
        assert not from_grants(doc)(uuid4(), s, "KOBO-001", "ACCEPT").allowed

    @pytest.mark.parametrize("doc", [None, {}, {"schema": "x"}, {**GRANTS, "version": 2},
                                     {**GRANTS, "grants": "all"}])
    def test_malformed_or_absent_grants_deny(self, doc) -> None:
        got = from_grants(doc)(uuid4(), uuid4(), "KOBO-001", "ACCEPT")
        assert not got.allowed and got.unavailable_reason

    def test_default_denies_with_reason(self) -> None:
        got = no_capability(uuid4(), uuid4(), "KOBO-001", "ACCEPT").wire()
        assert got["allowed"] is False and got["command"] == "ACCEPT" and got["fixture_id"] is None
        assert got["unavailable_reason"] and got["actor_kind"] == "SYSTEM"


def test_decimal_text_is_stable() -> None:
    assert [rt.text_of(Decimal(x)) for x in ("20", "20.000", "15.50", "100")] == ["20", "20", "15.5", "100"]
