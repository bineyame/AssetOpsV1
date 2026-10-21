"""W4-02 units 2-3: pure renewable, service, fuel and backup rules (`mini_depth/rules.py`). No database."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from assetops_backend.mini_depth import rules
from assetops_backend.mini_depth.rules import (
    Bound, LoadAsset, Reading, RenewableInputs, Window, assess_renewable_hour, assess_service_hour, series,
    summarize_renewable,
)

NOON = datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc)  # 12:00 Africa/Nairobi
HOUR = Window(NOON, NOON + timedelta(hours=1))
SRC = uuid4()
INV, BAT, LOAD_A, LOAD_B, CRIT = (uuid4() for _ in range(5))


def reading(role: str, value: str | None, start_min: float, end_min: float | None, *, asset: UUID | None = None,
            quality: str = "GOOD", unit: str = "kW", source: UUID = SRC, base: datetime = NOON) -> Reading:
    start = base + timedelta(minutes=start_min)
    end = None if end_min is None else base + timedelta(minutes=end_min)
    return Reading(uuid4(), source, role, asset, start, start if end else None, end, quality,
                   None if value is None else Decimal(value), unit)


def minutes(role: str, value: str, asset: UUID | None = None, *, base: datetime = NOON,
            spans: tuple[tuple[int, int], ...] = ((0, 60),), step: int = 1) -> list[Reading]:
    """Accepted one-minute interval means over each `(from_min, to_min)` span."""
    return [reading(role, value, m, m + step, asset=asset, base=base)
            for lo, hi in spans for m in range(lo, hi, step)]


def positive_hour(base: datetime = NOON, *, load: str = "20", charge: str = "0") -> list[Reading]:
    return [
        *minutes("pv_available_power", "42", INV, base=base),
        *minutes("pv_power", "20", INV, base=base),
        *minutes("feeder_demand", load, LOAD_A, base=base),
        *minutes("storage_charge_requested_power", charge, BAT, base=base),
        *minutes("critical_load_requested_power", "4", CRIT, base=base),
        *minutes("critical_load_delivered_power", "4", CRIT, base=base),
    ]


INPUTS = RenewableInputs(pv_uncertainty_kw=Decimal("1"), retained_margin_kw=Decimal("3"), feeder_asset_ids=(LOAD_A,),
                         critical_asset_id=CRIT)


def test_interval_coverage_and_nullable_denominators() -> None:
    # A 40-minute hole between interval means stays a gap; nothing is interpolated.
    partial = series(minutes("feeder_demand", "5", LOAD_A, spans=((0, 20),)), "feeder_demand", LOAD_A, HOUR)
    assert partial.state == rules.PARTIAL
    assert (partial.coverage.required_seconds, partial.coverage.observed_seconds) == (3600, 1200)
    assert [(g.start, g.end) for g in partial.coverage.gaps] == [(NOON + timedelta(minutes=20), HOUR.end)]
    assert partial.coverage.source_count == 1

    # Instant reports, non-GOOD rows and non-kW rows cover nothing but are still cited.
    instant = reading("feeder_demand", "5", 10, None, asset=LOAD_A)
    suspect = reading("feeder_demand", "5", 0, 60, asset=LOAD_A, quality="SUSPECT")
    wrong_unit = reading("feeder_demand", "5", 0, 60, asset=LOAD_A, unit="W")
    s = series([instant, suspect, wrong_unit], "feeder_demand", LOAD_A, HOUR)
    assert s.state == rules.MISSING and s.coverage.observed_seconds == 0 and s.mean_kw() is None
    assert set(s.cited) == {instant.evidence_id, suspect.evidence_id, wrong_unit.evidence_id}
    # q4 ruling 1: a GOOD well-formed instant is cited with zero coverage but is not unusable.
    assert set(s.unusable) == {suspect.evidence_id, wrong_unit.evidence_id}
    lone = series([instant], "feeder_demand", LOAD_A, HOUR)
    assert lone.cited == (instant.evidence_id,) and lone.unusable == () and lone.coverage.observed_seconds == 0
    # A purported interval with one bound, or start >= end, is malformed and unusable.
    one_bound = Reading(uuid4(), SRC, "feeder_demand", LOAD_A, NOON, NOON, None, "GOOD", Decimal("5"), "kW")
    backwards = Reading(uuid4(), SRC, "feeder_demand", LOAD_A, NOON, NOON + timedelta(minutes=5), NOON, "GOOD",
                        Decimal("5"), "kW")
    bad_bounds = series([one_bound, backwards], "feeder_demand", LOAD_A, HOUR)
    assert set(bad_bounds.unusable) == {one_bound.evidence_id, backwards.evidence_id}
    assert bad_bounds.coverage.observed_seconds == 0

    # q2 ruling 5: a GOOD complete series plus an overlapping SUSPECT row stays COMPLETE but carries the unusable row.
    gp = series(minutes("feeder_demand", "5", LOAD_A) + [suspect], "feeder_demand", LOAD_A, HOUR)
    assert gp.state == rules.COMPLETE and gp.unusable == (suspect.evidence_id,)
    assert suspect.evidence_id in gp.cited

    # q2 ruling 11: hour coverage is the intersection of required roles across sources; sources are counted.
    other_src = uuid4()
    cross = [r for r in positive_hour() if r.role != "pv_power"] + [
        reading("pv_power", "20", m, m + 1, asset=INV, source=other_src) for m in range(30, 60)]
    crossed = assess_renewable_hour(date(2026, 10, 6), HOUR, cross, INPUTS)
    assert crossed.coverage.observed_seconds == 1800 and crossed.coverage.source_count == 2
    assert [(g.start, g.end) for g in crossed.coverage.gaps] == [(NOON, NOON + timedelta(minutes=30))]

    # A duplicate or overlapping usable row is a conflict; no favourable row is chosen.
    dup = minutes("feeder_demand", "5", LOAD_A) + [reading("feeder_demand", "9", 10, 11, asset=LOAD_A)]
    conflict = series(dup, "feeder_demand", LOAD_A, HOUR)
    assert conflict.state == rules.CONFLICTING and conflict.mean_kw() is None

    # Rows reaching outside the hour are clipped to it.
    clipped = series([reading("feeder_demand", "6", -30, 90, asset=LOAD_A)], "feeder_demand", LOAD_A, HOUR)
    assert clipped.state == rules.COMPLETE and clipped.coverage.observed_seconds == 3600
    assert clipped.mean_kw() == Decimal("6")

    # Service: complete delivery without request evidence is UNKNOWN, with null request-dependent amounts.
    loads = (LoadAsset(LOAD_A, "FDR-A", "Feeder A", False, True),)
    hour = assess_service_hour(HOUR, minutes("feeder_demand", "5", LOAD_A), loads)
    assert hour.status == "UNKNOWN"
    assert hour.delivered_load_kw == Decimal("5")
    assert (hour.unserved_kwh, hour.interruptions_seen) == (None, None)
    [row] = hour.rows
    assert (row.requested_evidence_state, row.assessment, row.role) == ("MISSING", "UNKNOWN", "UNCLASSIFIED")
    assert [l.code for l in hour.limitations] == ["REQUEST_BASELINE_MISSING"]

    # A partial feeder shows its observed mean and measured seconds, but no top aggregate.
    loads2 = loads + (LoadAsset(LOAD_B, "FDR-B", "Feeder B", False, True),)
    gap = assess_service_hour(
        HOUR, minutes("feeder_demand", "5", LOAD_A) + minutes("feeder_demand", "8", LOAD_B, spans=((0, 20),)), loads2)
    assert gap.status == "LIMITED" and gap.delivered_load_kw is None
    row_b = next(r for r in gap.rows if r.asset_id == LOAD_B)
    assert row_b.delivered_kw == Decimal("8") and row_b.coverage.observed_seconds == 1200
    assert row_b.assessment == "LIMITED"
    assert [l.code for l in gap.limitations] == ["COVERAGE_GAP", "REQUEST_BASELINE_MISSING"]

    # No addressed load at all: every amount is null, never zero.
    empty = assess_service_hour(HOUR, [], ())
    assert empty.status == "UNKNOWN" and empty.rows == ()
    assert (empty.delivered_load_kw, empty.interruptions_seen, empty.critical_delivered_kw, empty.unserved_kwh) \
        == (None, None, None, None)
    assert empty.coverage.observed_seconds == 0

    # Renewable denominators are null, not zero, when no day is completely assessed.
    limited = assess_renewable_hour(date(2026, 10, 6), HOUR, [], INPUTS)
    cards = summarize_renewable([limited], requested_days=1)
    assert (cards.eligible_days, cards.assessed_days) == (None, None)
    assert (cards.capability_kw, cards.used_kw, cards.headroom_kw) == (None, None, None)


def test_service_request_supported_interruptions_and_critical_row() -> None:
    loads = (LoadAsset(LOAD_B, "FDR-B", "Feeder B", False, True), LoadAsset(CRIT, "FDR-C", "Clinic", True, False))
    delivered_b = minutes("feeder_demand", "6", LOAD_B, spans=((0, 10), (20, 60))) + minutes(
        "feeder_demand", "0", LOAD_B, spans=((10, 20),))
    requested_b = minutes("feeder_requested_power", "6", LOAD_B)
    delivered_c = minutes("feeder_demand", "4", CRIT)
    # The critical pair qualifies only its bound critical asset.
    requested_c = minutes("critical_load_requested_power", "4", CRIT)
    critical_delivered = minutes("critical_load_delivered_power", "4", CRIT)
    hour = assess_service_hour(HOUR, delivered_b + requested_b + delivered_c + requested_c + critical_delivered, loads)

    assert hour.status == "SUPPORTED" and hour.limitations == ()
    assert [r.asset_code for r in hour.rows] == ["FDR-C", "FDR-B"]  # critical first
    clinic, feeder_b = hour.rows
    assert clinic.role == "CRITICAL" and clinic.requested_evidence_state == "ACCEPTED"
    assert feeder_b.interruptions == 1  # ten contiguous zero-delivery minutes are one interruption
    assert feeder_b.unserved_kwh == Decimal("6") * Decimal(600) / Decimal(3600)
    assert hour.interruptions_seen == 1 and hour.unserved_kwh == feeder_b.unserved_kwh
    assert hour.critical_delivered_kw == Decimal("4")
    assert hour.delivered_load_kw == clinic.delivered_kw + feeder_b.delivered_kw
    cited = {r.evidence_id for r in delivered_b + requested_b + delivered_c + requested_c + critical_delivered}
    assert set(hour.evidence_ids) == cited

    # The critical pair does not qualify a feeder it is not bound to.
    other = assess_service_hour(HOUR, minutes("feeder_demand", "6", LOAD_B) + requested_c,
                                (LoadAsset(LOAD_B, "FDR-B", "Feeder B", False, True),))
    assert other.rows[0].requested_evidence_state == "MISSING" and other.status == "UNKNOWN"

    # A conflicting request is CONFLICT and limits the hour.
    clash = requested_b + [reading("feeder_requested_power", "1", 5, 6, asset=LOAD_B)]
    limited = assess_service_hour(HOUR, delivered_b + clash, (LoadAsset(LOAD_B, "FDR-B", "Feeder B", False, True),))
    assert limited.rows[0].requested_evidence_state == "CONFLICT"
    assert limited.status == "LIMITED" and [l.code for l in limited.limitations] == ["CONFLICT"]

    # Complete but misaligned request and delivery are not compared.
    halves = minutes("feeder_requested_power", "6", LOAD_B, step=30)
    misaligned = assess_service_hour(HOUR, minutes("feeder_demand", "6", LOAD_B) + halves,
                                     (LoadAsset(LOAD_B, "FDR-B", "Feeder B", False, True),))
    assert misaligned.rows[0].assessment == "LIMITED" and misaligned.unserved_kwh is None
    assert misaligned.status == "LIMITED"  # q2 ruling 13

    # q2 ruling 12: a bound but empty feeder request is not bypassed by a complete critical request.
    bound_clinic = (LoadAsset(CRIT, "FDR-C", "Clinic", True, True),)
    bypass = assess_service_hour(HOUR, delivered_c + requested_c + critical_delivered, bound_clinic)
    assert bypass.rows[0].requested_evidence_state == "MISSING" and bypass.rows[0].assessment == "UNKNOWN"
    assert bypass.status != "SUPPORTED"
    # q2 rulings 12/13: a partial feeder request is a coverage gap; row and hour LIMITED, never SUPPORTED.
    part_req = minutes("feeder_requested_power", "6", LOAD_B, spans=((0, 40),))
    partial = assess_service_hour(HOUR, minutes("feeder_demand", "6", LOAD_B) + part_req,
                                  (LoadAsset(LOAD_B, "FDR-B", "Feeder B", False, True),))
    assert (partial.rows[0].requested_evidence_state, partial.rows[0].assessment, partial.status) \
        == ("MISSING", "LIMITED", "LIMITED")
    [gap_lim] = partial.limitations
    assert gap_lim.code == "COVERAGE_GAP" and set(gap_lim.evidence_ids) == {r.evidence_id for r in part_req}

    # q2 ruling 14: critical delivery of another asset does not stand in for the pinned critical asset.
    wrong = minutes("critical_load_delivered_power", "4", LOAD_B)
    wrong_asset = assess_service_hour(HOUR, delivered_b + requested_b + delivered_c + requested_c + wrong, loads)
    assert wrong_asset.critical_delivered_kw is None

    # q2 ruling 5: a SUSPECT delivery row beside complete GOOD delivery withholds SUPPORTED.
    suspect_b = reading("feeder_demand", "6", 0, 60, asset=LOAD_B, quality="SUSPECT")
    unusable = assess_service_hour(HOUR, delivered_b + requested_b + [suspect_b],
                                   (LoadAsset(LOAD_B, "FDR-B", "Feeder B", False, True),))
    assert unusable.rows[0].assessment == "LIMITED" and unusable.status == "LIMITED"
    assert [(l.code, l.evidence_ids) for l in unusable.limitations] \
        == [("REQUIRED_INPUT_UNUSABLE", (suspect_b.evidence_id,))]
    assert unusable.interruptions_seen is None and unusable.delivered_load_kw is None
    # q4 ruling 1: a GOOD instant beside complete GOOD delivery adds no unusable limitation.
    instant_b = reading("feeder_demand", "6", 30, None, asset=LOAD_B)
    with_instant = assess_service_hour(HOUR, delivered_b + requested_b + [instant_b],
                                       (LoadAsset(LOAD_B, "FDR-B", "Feeder B", False, True),))
    assert with_instant.status == "SUPPORTED" and with_instant.limitations == ()
    assert instant_b.evidence_id in with_instant.evidence_ids


def test_renewable_hour_headroom_constraints_and_precedence() -> None:
    day = date(2026, 10, 6)
    ok = assess_renewable_hour(day, HOUR, positive_hour(), INPUTS)
    assert ok.decision == "ELIGIBLE" and ok.constraints == ()
    assert ok.capability_kw == Bound(Decimal("41"), Decimal("43"))
    assert ok.used_kw == Decimal("20")
    assert ok.headroom_kw == Bound(Decimal("18"), Decimal("20")) == ok.opportunity_kwh
    assert ok.coverage.observed_seconds == 3600 and ok.coverage.gaps == ()

    # Missing authored uncertainty or margin makes headroom null, never zero.
    no_margin = assess_renewable_hour(day, HOUR, positive_hour(), RenewableInputs(Decimal("1"), None, (LOAD_A,), CRIT))
    assert no_margin.decision == "LIMITED" and no_margin.headroom_kw is None and no_margin.opportunity_kwh is None
    assert no_margin.constraints == ("MARGIN_MISSING",)
    no_u = assess_renewable_hour(day, HOUR, positive_hour(), RenewableInputs(None, Decimal("3"), (LOAD_A,), CRIT))
    assert no_u.capability_kw is None and no_u.constraints == ("CAPABILITY_MISSING",)
    # q2 ruling 2: a negative (invalid) uncertainty is not a default; capability stays null.
    bad_u = assess_renewable_hour(day, HOUR, positive_hour(), RenewableInputs(Decimal("-1"), Decimal("3"), (LOAD_A,), CRIT))
    assert bad_u.capability_kw is None and bad_u.constraints == ("CAPABILITY_MISSING",)

    # Missing obligation/critical roles and gaps are LIMITED, in the declared code order.
    sparse = [r for r in positive_hour() if r.role not in ("storage_charge_requested_power",
                                                           "critical_load_delivered_power")]
    sparse = [r for r in sparse if not (r.role == "pv_power" and r.interval_start >= NOON + timedelta(minutes=50))]
    limited = assess_renewable_hour(day, HOUR, sparse, INPUTS)
    assert limited.constraints == ("CHARGE_OBLIGATION_MISSING", "CRITICAL_SERVICE_MISSING", "COVERAGE_GAP")
    assert limited.decision == "LIMITED" and limited.coverage.observed_seconds == 0

    # q2 rulings 3/5: a present but unusable required row is cited and limits, even with GOOD coverage.
    bad_pv = reading("pv_power", "20", 0, 60, asset=INV, quality="BAD")
    unusable = assess_renewable_hour(day, HOUR, positive_hour() + [bad_pv], INPUTS)
    assert (unusable.decision, unusable.constraints) == ("LIMITED", ("REQUIRED_INPUT_UNUSABLE",))
    assert unusable.opportunity_kwh is None and bad_pv.evidence_id in unusable.evidence_ids
    # q4 ruling 1: a GOOD instant beside a complete GOOD hour adds nothing; the SUSPECT overlap above still does.
    instant_pv = reading("pv_power", "20", 30, None, asset=INV)
    with_instant = assess_renewable_hour(day, HOUR, positive_hour() + [instant_pv], INPUTS)
    assert (with_instant.decision, with_instant.constraints) == ("ELIGIBLE", ())
    assert instant_pv.evidence_id in with_instant.evidence_ids
    only_bad = [r for r in positive_hour() if r.role != "pv_power"] + [bad_pv]
    assert assess_renewable_hour(day, HOUR, only_bad, INPUTS).constraints \
        == ("PV_USE_MISSING", "REQUIRED_INPUT_UNUSABLE")

    # q2 ruling 6: a partial obligation is a limitation, not evidence of zero charge.
    part_charge = [r for r in positive_hour(charge="5") if not (
        r.role == "storage_charge_requested_power" and r.interval_start >= NOON + timedelta(minutes=30))]
    pc = assess_renewable_hour(day, HOUR, part_charge, INPUTS)
    assert (pc.decision, pc.constraints) == ("LIMITED", ("COVERAGE_GAP",))

    # q2 ruling 7: complete but unaligned critical requested/delivered is CRITICAL_SERVICE_MISSING.
    unaligned = [r for r in positive_hour() if r.role != "critical_load_requested_power"]
    unaligned += minutes("critical_load_requested_power", "4", CRIT, step=30)
    ua = assess_renewable_hour(day, HOUR, unaligned, INPUTS)
    assert (ua.decision, ua.constraints) == ("LIMITED", ("CRITICAL_SERVICE_MISSING",))

    # q4 ruling 2: critical service is the pinned critical LOAD's pair only. A complete pair on another asset does
    # not stand in for it; nor does a mixed-asset pair; no unique pinned asset is CRITICAL_SERVICE_MISSING.
    crit_roles = ("critical_load_requested_power", "critical_load_delivered_power")
    elsewhere = [r for r in positive_hour() if r.role not in crit_roles] + [
        *minutes("critical_load_requested_power", "4", LOAD_B), *minutes("critical_load_delivered_power", "4", LOAD_B)]
    other_asset = assess_renewable_hour(day, HOUR, elsewhere, INPUTS)
    assert (other_asset.decision, other_asset.constraints) == ("LIMITED", ("CRITICAL_SERVICE_MISSING",))
    assert other_asset.opportunity_kwh is None
    assert {r.evidence_id for r in elsewhere} == set(other_asset.evidence_ids)
    mixed = [r for r in positive_hour() if r.role != "critical_load_delivered_power"] + minutes(
        "critical_load_delivered_power", "4", LOAD_B)
    assert assess_renewable_hour(day, HOUR, mixed, INPUTS).constraints == ("CRITICAL_SERVICE_MISSING",)
    two_critical = RenewableInputs(Decimal("1"), Decimal("3"), (LOAD_A,), None)  # unit 4: none or several -> None
    unpinned = assess_renewable_hour(day, HOUR, positive_hour(), two_critical)
    assert (unpinned.decision, unpinned.constraints) == ("LIMITED", ("CRITICAL_SERVICE_MISSING",))
    assert unpinned.opportunity_kwh is None
    assert assess_renewable_hour(day, HOUR, positive_hour(), INPUTS).decision == "ELIGIBLE"  # pinned pair

    # Complete contraindicating facts are EXCLUDED with their codes.
    charging = assess_renewable_hour(day, HOUR, positive_hour(charge="5"), INPUTS)
    assert (charging.decision, charging.constraints) == ("EXCLUDED", ("CHARGE_OBLIGATION_ACTIVE",))
    assert charging.opportunity_kwh is None and charging.headroom_kw is not None
    deficit = [r for r in positive_hour() if r.role != "critical_load_delivered_power"]
    deficit += minutes("critical_load_delivered_power", "3", CRIT)
    assert assess_renewable_hour(day, HOUR, deficit, INPUTS).constraints == ("CRITICAL_SERVICE_DEFICIT",)
    heavy = assess_renewable_hour(day, HOUR, positive_hour(load="39"), INPUTS)
    assert heavy.headroom_kw == Bound(Decimal("0"), Decimal("1"))
    # q2 ruling 8: positive headroom is the upper bound; 0-1 kW is ELIGIBLE with a zero lower opportunity.
    assert (heavy.decision, heavy.constraints) == ("ELIGIBLE", ())
    assert heavy.opportunity_kwh == Bound(Decimal("0"), Decimal("1"))
    flat = assess_renewable_hour(day, HOUR, positive_hour(load="40"), INPUTS)
    assert flat.headroom_kw == Bound(Decimal("0"), Decimal("0"))
    assert (flat.decision, flat.constraints, flat.opportunity_kwh) == ("EXCLUDED", ("HEADROOM_NON_POSITIVE",), None)

    # A contradiction takes precedence over an exclusion.
    clash = positive_hour(charge="5") + [reading("pv_available_power", "10", 3, 4, asset=INV)]
    both = assess_renewable_hour(day, HOUR, clash, INPUTS)
    assert both.decision == "CONFLICT"
    assert both.constraints == ("CONFLICT", "CHARGE_OBLIGATION_ACTIVE")
    assert {r.evidence_id for r in clash} == set(both.evidence_ids)


def test_renewable_daily_denominator() -> None:
    days = [date(2026, 10, d) for d in range(6, 11)]
    bases = [NOON + timedelta(days=i) for i in range(5)]
    windows = [Window(b, b + timedelta(hours=1)) for b in bases]
    hours = [
        assess_renewable_hour(days[0], windows[0], positive_hour(bases[0]), INPUTS),                  # 18-20
        assess_renewable_hour(days[1], windows[1], positive_hour(bases[1], load="15"), INPUTS),       # 23-25
        assess_renewable_hour(days[2], windows[2], positive_hour(bases[2], charge="2"), INPUTS),      # EXCLUDED
        assess_renewable_hour(days[3], windows[3],
                              [r for r in positive_hour(bases[3]) if r.role != "pv_power"], INPUTS),  # LIMITED
        assess_renewable_hour(days[4], windows[4], positive_hour(bases[4], load="30"), INPUTS),       # 8-10
    ]
    assert [h.decision for h in hours] == ["ELIGIBLE", "ELIGIBLE", "EXCLUDED", "LIMITED", "ELIGIBLE"]
    cards = summarize_renewable(list(reversed(hours)), requested_days=5)
    # The incomplete day stays visible but outside the denominator.
    assert (cards.eligible_days, cards.assessed_days) == (3, 4)
    assert cards.used_kw == Bound(Decimal("15"), Decimal("30"))
    assert cards.headroom_kw == Bound(Decimal("8"), Decimal("25"))
    assert cards.capability_kw == Bound(Decimal("41"), Decimal("43"))
    assert cards.recurrence_established is False
    assert [h.day for h in rules.renewable_rows(reversed(hours))] == days

    complete = [assess_renewable_hour(d, w, positive_hour(b), INPUTS) for d, w, b in zip(days, windows, bases)]
    assert summarize_renewable(complete, requested_days=5).recurrence_established is True
    # One eligible day establishes no recurrence.
    single = summarize_renewable(complete[:1], requested_days=1)
    assert (single.eligible_days, single.assessed_days, single.recurrence_established) == (1, 1, False)
    # Only excluded days: zero eligible over a real denominator; the cards stay null.
    excluded = summarize_renewable([hours[2]], requested_days=1)
    assert (excluded.eligible_days, excluded.assessed_days) == (0, 1)
    assert (excluded.capability_kw, excluded.used_kw, excluded.headroom_kw) == (None, None, None)
    # q2 ruling 10: five complete EXCLUDED days are a reportable 0/5 denominator, not a recurring opportunity.
    all_excluded = [assess_renewable_hour(d, w, positive_hour(b, charge="2"), INPUTS)
                    for d, w, b in zip(days, windows, bases)]
    five = summarize_renewable(all_excluded, requested_days=5)
    assert (five.eligible_days, five.assessed_days, five.recurrence_established) == (0, 5, True)


# --- Unit 3: fuel and backup ----------------------------------------------------------------------------------

GEN, TANK = uuid4(), uuid4()
SFC = rules.SfcValue(uuid4(), Decimal("0.3"), NOON - timedelta(days=30), None)
FUEL = rules.FuelInputs(sfc=(SFC,), upper_multiplier=Decimal("1.10"))


def test_fuel_interval_and_completeness() -> None:
    # 30 min at 20 kW + 30 min at 0 kW = 10 kWh; x 0.3 L/kWh = 3 L nominal; upper allowance 1.10x, lower 0.
    gen = [*minutes("generator_power", "20", GEN, spans=((0, 30),)), *minutes("generator_power", "0", GEN,
                                                                               spans=((30, 60),))]
    tank = [reading("fuel_level", "180", 0, None, asset=TANK, unit="L"),
            reading("fuel_level", "176", 59, None, asset=TANK, unit="L")]
    hour = rules.assess_fuel_hour(HOUR, [*gen, *tank], FUEL)
    assert hour.nominal_l == Decimal("3.0")
    assert hour.expected_use_l == Bound(Decimal(0), Decimal("3.300"))
    assert hour.sfc_property_revision_ids == (SFC.property_revision_id,)
    assert set(hour.generator_power_evidence_ids) == {r.evidence_id for r in gen}
    # A scalar tank reading has no measurement uncertainty: opening/closing stay null; deliveries and residual
    # are never established in W4-02, and the bridge keeps the fixed term order.
    assert (hour.opening_l, hour.deliveries_l, hour.closing_l, hour.residual_l) == (None, None, None, None)
    assert [r.term for r in hour.rows] == list(rules.FUEL_TERMS)
    by = {r.term: r for r in hour.rows}
    assert (by["OPENING"].basis, by["OPENING"].treatment, by["OPENING"].evidence_ids) == (
        "ACCEPTED_READING", "MISSING", (tank[0].evidence_id,))
    assert by["CLOSING"].evidence_ids == (tank[1].evidence_id,)
    assert (by["DELIVERIES"].basis, by["DELIVERIES"].treatment) == ("AUTHORED_EVIDENCE_UNAVAILABLE",
                                                                    "COMPLETENESS_UNCONFIRMED")
    assert (by["USE"].basis, by["USE"].treatment, by["USE"].value) == ("FOUNDATION_MODEL", "MODELLED",
                                                                       hour.expected_use_l)
    assert (by["RESIDUAL"].value, by["RESIDUAL"].treatment) == (None, "MISSING")
    assert [l.code for l in hour.limitations] == ["DELIVERY_COMPLETENESS_MISSING", "CLOSING_READING_MISSING"]
    assert hour.status == "UNKNOWN"  # no residual => never SUPPORTED in W4-02
    assert set(hour.evidence_ids) == {r.evidence_id for r in (*gen, *tank)}

    # A 40-minute hole: no expected use (no zero substitute), coverage gap, LIMITED.
    gap = rules.assess_fuel_hour(HOUR, minutes("generator_power", "20", GEN, spans=((0, 20),)), FUEL)
    assert gap.expected_use_l is None and gap.nominal_l is None and gap.status == "LIMITED"
    assert {r.term: r.treatment for r in gap.rows}["USE"] == "MISSING"
    assert gap.coverage.observed_seconds == 1200 and "COVERAGE_GAP" in [l.code for l in gap.limitations]
    # A duplicate interval conflicts: no favourable row chosen.
    dup = rules.assess_fuel_hour(HOUR, [*gen, reading("generator_power", "5", 0, 1, asset=GEN)], FUEL)
    assert dup.expected_use_l is None and dup.status == "LIMITED"
    assert {r.term: r.treatment for r in dup.rows}["USE"] == "CONFLICT"
    # No in-force SFC, or a non-positive one, or two overlapping ones: no model value.
    later = rules.SfcValue(uuid4(), Decimal("0.3"), NOON + timedelta(minutes=30), None)
    assert rules.assess_fuel_hour(HOUR, gen, rules.FuelInputs((later,), Decimal("1.10"))).expected_use_l is None
    zero = rules.SfcValue(uuid4(), Decimal("0"), NOON - timedelta(days=1), None)
    assert rules.assess_fuel_hour(HOUR, gen, rules.FuelInputs((zero,), Decimal("1.10"))).expected_use_l is None
    assert rules.assess_fuel_hour(HOUR, gen, rules.FuelInputs((SFC, later), Decimal("1.10"))).expected_use_l is None
    # No generator evidence at all: USE is MISSING, nothing is zero.
    none = rules.assess_fuel_hour(HOUR, [], FUEL)
    assert none.expected_use_l is None and {r.term: r.basis for r in none.rows}["OPENING"] == "MISSING"

    # q3 2: differing tank values at the chosen instant are a CONFLICT row, never a favourable choice.
    clash = [*tank, reading("fuel_level", "179", 0, None, asset=TANK, unit="L")]
    tank_conflict = rules.assess_fuel_hour(HOUR, [*gen, *clash], FUEL)
    by_t = {r.term: r for r in tank_conflict.rows}
    assert (by_t["OPENING"].basis, by_t["OPENING"].treatment, by_t["OPENING"].value) == (
        "ACCEPTED_READING", "CONFLICT", None)
    assert set(by_t["OPENING"].evidence_ids) == {tank[0].evidence_id, clash[2].evidence_id}
    assert by_t["CLOSING"].treatment == "MISSING"
    assert tank_conflict.status == "LIMITED" and "CONFLICT" in [l.code for l in tank_conflict.limitations]
    assert tank_conflict.expected_use_l == hour.expected_use_l  # an independently valid model stays visible
    # q3 2: no SFC in force -> USE is MISSING/MISSING with no model amount and no SFC revision cited.
    no_sfc = rules.assess_fuel_hour(HOUR, gen, rules.FuelInputs((), Decimal("1.10")))
    assert (no_sfc.nominal_l, no_sfc.expected_use_l, no_sfc.sfc_property_revision_ids) == (None, None, ())
    by_n = {r.term: r for r in no_sfc.rows}
    assert (by_n["USE"].basis, by_n["USE"].treatment, by_n["USE"].value) == ("MISSING", "MISSING", None)
    assert no_sfc.status == "UNKNOWN"
    # q3 3: the exact status table; deliveries and residual are null in every row, and nothing is SUPPORTED.
    table = {"conflict": (tank_conflict, "LIMITED"), "duplicate": (dup, "LIMITED"), "partial": (gap, "LIMITED"),
             "modelled": (hour, "UNKNOWN"), "no-sfc": (no_sfc, "UNKNOWN"), "no-evidence": (none, "UNKNOWN")}
    for name, (h, expected_status) in table.items():
        assert h.status == expected_status, name
        assert (h.deliveries_l, h.residual_l) == (None, None), name
        codes = [l.code for l in h.limitations]
        assert {"DELIVERY_COMPLETENESS_MISSING", "CLOSING_READING_MISSING"} <= set(codes), name
        by_h = {r.term: r for r in h.rows}
        assert (by_h["RESIDUAL"].value, by_h["DELIVERIES"].treatment) == (None, "COMPLETENESS_UNCONFIRMED"), name

    # q4 ruling 3: a SUSPECT bound generator interval beside complete GOOD coverage withholds the model.
    suspect_gen = reading("generator_power", "20", 0, 60, asset=GEN, quality="SUSPECT")
    sus = rules.assess_fuel_hour(HOUR, [*gen, *tank, suspect_gen], FUEL)
    assert (sus.expected_use_l, sus.nominal_l, sus.status) == (None, None, "LIMITED")
    assert ("REQUIRED_INPUT_UNUSABLE", (suspect_gen.evidence_id,)) in [(l.code, l.evidence_ids)
                                                                         for l in sus.limitations]
    assert suspect_gen.evidence_id in sus.evidence_ids
    # A GOOD tank instant is not unusable (the modelled hour above has no such code).
    assert "REQUIRED_INPUT_UNUSABLE" not in [l.code for l in hour.limitations]
    # A bad tank candidate limits and makes its term unavailable; the valid modelled use stays visible.
    bad_tank = reading("fuel_level", "150", 0, None, asset=TANK, unit="L", quality="BAD")
    tb = rules.assess_fuel_hour(HOUR, [*gen, *tank, bad_tank], FUEL)
    assert tb.status == "LIMITED" and tb.expected_use_l == hour.expected_use_l
    assert ("REQUIRED_INPUT_UNUSABLE", (bad_tank.evidence_id,)) in [(l.code, l.evidence_ids) for l in tb.limitations]
    by_b = {r.term: r for r in tb.rows}
    assert (by_b["OPENING"].basis, by_b["OPENING"].treatment) == ("MISSING", "MISSING")
    assert bad_tank.evidence_id in by_b["OPENING"].evidence_ids
    assert by_b["CLOSING"].basis == "ACCEPTED_READING"
    # A wrong-unit tank candidate is unusable too.
    pct = reading("fuel_level", "90", 59, None, asset=TANK, unit="%")
    assert {r.term: r.basis for r in rules.assess_fuel_hour(HOUR, [*gen, *tank, pct], FUEL).rows}["CLOSING"]         == "MISSING"
    # q5 ruling 1: explicit tank edges around two valid instants (10 and 50 min).
    v10 = reading("fuel_level", "180", 10, None, asset=TANK, unit="L")
    v50 = reading("fuel_level", "176", 50, None, asset=TANK, unit="L")

    def edges(*bad: Reading) -> tuple[dict[str, rules.FuelRow], rules.FuelHour]:
        h = rules.assess_fuel_hour(HOUR, [*gen, v10, v50, *bad], FUEL)
        assert h.status == "LIMITED" and h.expected_use_l == hour.expected_use_l and h.residual_l is None
        assert ("REQUIRED_INPUT_UNUSABLE", tuple(sorted((b.evidence_id for b in bad), key=str))) in [
            (l.code, l.evidence_ids) for l in h.limitations]
        return {r.term: r for r in h.rows}, h

    def ids(*rows: Reading) -> tuple[UUID, ...]:
        return tuple(sorted((r.evidence_id for r in rows), key=str))

    ok = ("ACCEPTED_READING", "MISSING")
    gone = ("MISSING", "MISSING")
    for minute, opening, closing in ((5, gone, ok), (10, gone, ok), (30, ok, ok), (50, ok, gone), (55, ok, gone)):
        bad = reading("fuel_level", "150", minute, None, asset=TANK, unit="L", quality="SUSPECT")
        rows, _ = edges(bad)
        assert (rows["OPENING"].basis, rows["OPENING"].treatment) == opening, minute
        assert (rows["CLOSING"].basis, rows["CLOSING"].treatment) == closing, minute
        assert rows["OPENING"].value is None and rows["CLOSING"].value is None
        # An invalidated edge cites its good edge row plus the competing bad row; it never moves to the next edge.
        assert rows["OPENING"].evidence_ids == (ids(v10, bad) if opening == gone else ids(v10)), minute
        assert rows["CLOSING"].evidence_ids == (ids(v50, bad) if closing == gone else ids(v50)), minute
    # Single valid instant: a bad row at that instant invalidates both edges.
    v30 = reading("fuel_level", "178", 30, None, asset=TANK, unit="L")
    tie = reading("fuel_level", "150", 30, None, asset=TANK, unit="L", quality="BAD")
    th = rules.assess_fuel_hour(HOUR, [*gen, v30, tie], FUEL)
    by_tie = {r.term: r for r in th.rows}
    for term in ("OPENING", "CLOSING"):
        assert (by_tie[term].basis, by_tie[term].treatment, by_tie[term].value) == ("MISSING", "MISSING", None)
        assert by_tie[term].evidence_ids == ids(v30, tie)
    assert th.status == "LIMITED" and th.residual_l is None and th.expected_use_l == hour.expected_use_l
    assert ("REQUIRED_INPUT_UNUSABLE", (tie.evidence_id,)) in [(l.code, l.evidence_ids) for l in th.limitations]
    # No valid instant: both edges are unavailable and cite every bad candidate.
    b1 = reading("fuel_level", "150", 5, None, asset=TANK, unit="L", quality="BAD")
    b2 = reading("fuel_level", "149", 55, None, asset=TANK, unit="%")
    nh = rules.assess_fuel_hour(HOUR, [*gen, b1, b2], FUEL)
    by_none = {r.term: r for r in nh.rows}
    for term in ("OPENING", "CLOSING"):
        assert (by_none[term].basis, by_none[term].treatment, by_none[term].value) == ("MISSING", "MISSING", None)
        assert by_none[term].evidence_ids == ids(b1, b2)
    assert nh.status == "LIMITED" and nh.residual_l is None and nh.expected_use_l == hour.expected_use_l
    assert ("REQUIRED_INPUT_UNUSABLE", ids(b1, b2)) in [(l.code, l.evidence_ids) for l in nh.limitations]


def obs(role: str, minute: float, *, state: str | None = None, kind: str | None = None, outcome: str | None = None,
        corr: str | None = None, quality: str = "GOOD") -> rules.Observation:
    return rules.Observation(uuid4(), SRC, role, NOON + timedelta(minutes=minute), quality, state, kind, outcome, corr)


def chain_obs(*, result: str = "SUCCEEDED") -> list[rules.Observation]:
    return [
        obs("site_supply_state", -5, state="ENERGIZED"),
        obs("site_supply_state", 10, state="LOST"),
        obs("mini_backup_start_event", 10.5, kind="START_REQUEST", outcome="REQUESTED", corr="c-1"),
        obs("mini_backup_start_event", 11, kind="START_RESULT", outcome=result, corr="c-1"),
        obs("mini_backup_bus_state", 11.5, state="ENERGIZED"),
        obs("site_supply_state", 40, state="ENERGIZED"),
    ]


def chain_readings(delivered_from: int = 12) -> list[Reading]:
    return [
        *minutes("generator_power", "15", GEN, spans=((11, 40),)),
        *minutes("critical_load_requested_power", "4", CRIT),
        *minutes("critical_load_delivered_power", "4", CRIT, spans=((0, 10), (delivered_from, 60))),
        *minutes("critical_load_delivered_power", "0", CRIT, spans=((10, delivered_from),)),
    ]


def backup(w, o, r, target, *, pin=CRIT):
    """q5 ruling 4: every direct rule call passes the explicit pinned critical asset."""
    return rules.assess_backup_hour(w, o, r, target, critical_asset_id=pin)


def test_backup_chain_order_and_no_event() -> None:
    target = Decimal("5")  # minutes
    hour = backup(HOUR, chain_obs(), chain_readings(), target)
    assert (hour.outage_count, hour.start_success_count, hour.status) == (1, 1, "SUPPORTED")
    (chain,) = hour.chains
    assert [s.code for s in chain.steps] == list(rules.BACKUP_STEPS)
    assert all(s.state == "OBSERVED" for s in chain.steps)
    ats = [s.at for s in chain.steps]
    assert ats == sorted(ats) and len(set(ats)) == 6  # strictly time ordered
    assert chain.chain_id == "c-1" and chain.outage_start == NOON + timedelta(minutes=10)
    # SERVICE is the end of the first aligned interval meeting the request: 12:13 - 12:10 = 180 s <= 300 s.
    assert chain.critical_recovery == rules.Recovery(Decimal("180"), Decimal("300"))
    assert (chain.result, chain.service_outcome) == ("PASS", "RECOVERED")
    assert hour.critical_recovery == chain.critical_recovery and hour.last_witnessed_test_at is None
    assert hour.limitations == ()

    # Recovery slower than the declared target is a witnessed FAIL.
    slow = backup(HOUR, chain_obs(), chain_readings(delivered_from=20), target)
    assert (slow.chains[0].result, slow.chains[0].service_outcome) == ("FAIL", "MISSED_TARGET")
    # No declared target: the observed sequence and elapsed time stand, but there is no PASS/FAIL claim.
    untargeted = backup(HOUR, chain_obs(), chain_readings(), None)
    assert untargeted.chains[0].result == "INCOMPLETE" and untargeted.chains[0].critical_recovery is None
    assert [l.code for l in untargeted.limitations] == ["RECOVERY_TARGET_MISSING", "BACKUP_CHAIN_INCOMPLETE"]
    # A failed start or a missing step is never inferred into a pass.
    failed = backup(HOUR, chain_obs(result="FAILED"), chain_readings(), target).chains[0]
    assert failed.result == "INCOMPLETE" and failed.start_succeeded is False
    assert [s.state for s in failed.steps][3:] == ["MISSING", "MISSING", "MISSING"]
    no_bus = [o for o in chain_obs() if o.role != "mini_backup_bus_state"]
    assert backup(HOUR, no_bus, chain_readings(), target).chains[0].result == "INCOMPLETE"
    # Generator operation alone (no supply loss) is not an outage, so not a start success.
    alone = backup(HOUR, [o for o in chain_obs() if o.role != "site_supply_state"],
                                     chain_readings(), target)
    assert (alone.outage_count, alone.start_success_count, alone.chains, alone.status) == (0, None, (), "UNKNOWN")
    assert [l.code for l in alone.limitations] == ["BACKUP_CHAIN_INCOMPLETE"]
    # A LOST report with no preceding ENERGIZED witnesses no transition.
    assert backup(HOUR, chain_obs()[1:], chain_readings(), target).outage_count == 0
    # Contradictory start results under one correlation are a conflict, never a choice.
    contra = [*chain_obs(), obs("mini_backup_start_event", 11.2, kind="START_RESULT", outcome="FAILED", corr="c-1")]
    conflicted = backup(HOUR, contra, chain_readings(), target)
    assert conflicted.status == "LIMITED" and conflicted.chains[0].steps[2].state == "CONFLICT"
    assert "CONFLICT" in [l.code for l in conflicted.limitations]
    # A start result under another correlation does not pair.
    other = [o if o.record_kind != "START_RESULT" else rules.Observation(o.evidence_id, o.source_id, o.role, o.source_time,
                                                                        o.quality, None, o.record_kind, o.outcome,
                                                                        "c-2") for o in chain_obs()]
    assert backup(HOUR, other, chain_readings(), target).chains[0].steps[2].state == "MISSING"

    # q3 6: a bus ENERGIZED report without positive generator output after it is no POWER step.
    idle = [*minutes("generator_power", "0", GEN, spans=((11, 40),)), *chain_readings()[29:]]
    no_output = backup(HOUR, chain_obs(), idle, target).chains[0]
    assert [s.state for s in no_output.steps][3:] == ["MISSING", "MISSING", "MISSING"]
    assert no_output.result == "INCOMPLETE"
    # q3 6: critical requested and delivered series on different intervals never align, so no SERVICE step.
    unaligned = [*minutes("generator_power", "15", GEN, spans=((11, 40),)),
                 *minutes("critical_load_requested_power", "4", CRIT, step=2),
                 *minutes("critical_load_delivered_power", "4", CRIT, spans=((12, 60),))]
    u = backup(HOUR, chain_obs(), unaligned, target)
    assert u.chains[0].steps[4].state == "OBSERVED" and u.chains[0].steps[5].state == "MISSING"
    assert (u.chains[0].result, u.status) == ("INCOMPLETE", "UNKNOWN")
    # q3 7: a witnessed miss -- complete aligned critical intervals over [LOSS, LOSS + target) inside the outage,
    # delivered < requested throughout -- is FAIL without a SERVICE step.
    starved = [*minutes("critical_load_requested_power", "4", CRIT),
               *minutes("critical_load_delivered_power", "0", CRIT, spans=((10, 60),)),
               *minutes("critical_load_delivered_power", "4", CRIT, spans=((0, 10),))]
    missed = backup(HOUR, no_bus, starved, target).chains[0]
    assert (missed.result, missed.service_outcome, missed.critical_recovery) == ("FAIL", "MISSED_TARGET", None)
    # Countercase: one missing delivered minute inside [LOSS, LOSS + target) witnesses nothing.
    holed = [r for r in starved if not (r.role == "critical_load_delivered_power"
                                        and r.interval_start == NOON + timedelta(minutes=12))]
    assert backup(HOUR, no_bus, holed, target).chains[0].result == "INCOMPLETE"
    # q3 8: an instant supply-state report covers zero seconds; the hour's coverage is only the critical series.
    bare = backup(HOUR, chain_obs(), [], target)
    assert (bare.coverage.observed_seconds, bare.coverage.required_seconds) == (0, 3600)

    # q4 ruling 3: an unusable row among the chain's required bound inputs blocks PASS/FAIL and limits the hour,
    # even when a GOOD row supplies the same step; its exact ID is cited.
    sus_result = obs("mini_backup_start_event", 11, kind="START_RESULT", outcome="SUCCEEDED", corr="c-1",
                     quality="SUSPECT")
    sus_bus = obs("mini_backup_bus_state", 11.5, state="ENERGIZED", quality="SUSPECT")
    sus_crit = reading("critical_load_delivered_power", "4", 15, 16, asset=CRIT, quality="SUSPECT")
    cases = {"start": ([*chain_obs(), sus_result], chain_readings(), sus_result.evidence_id),
             "bus": ([*chain_obs(), sus_bus], chain_readings(), sus_bus.evidence_id),
             "critical": (chain_obs(), [*chain_readings(), sus_crit], sus_crit.evidence_id)}
    for name, (o, r, bad_id) in cases.items():
        h = backup(HOUR, o, r, target)
        assert (h.status, h.chains[0].result, h.chains[0].critical_recovery) == ("LIMITED", "INCOMPLETE", None), name
        assert ("REQUIRED_INPUT_UNUSABLE", (bad_id,)) in [(l.code, l.evidence_ids) for l in h.limitations], name
        assert bad_id in h.evidence_ids, name
    # A bad supply row inside the outage limits the hour and blocks its chain (q5 ruling 2).
    sus_supply = obs("site_supply_state", 30, state="LOST", quality="SUSPECT")
    hs = backup(HOUR, [*chain_obs(), sus_supply], chain_readings(), target)
    assert (hs.status, hs.chains[0].result) == ("LIMITED", "INCOMPLETE")
    # A wrong-value state is unusable; an unrelated uncorrelated start event is not a required input.
    odd_bus = obs("mini_backup_bus_state", 20, state="POWERED")
    assert backup(HOUR, [*chain_obs(), odd_bus], chain_readings(), target).status == "LIMITED"
    stray = obs("mini_backup_start_event", 20, kind="START_RESULT", outcome="FAILED", corr="c-9", quality="SUSPECT")
    assert backup(HOUR, [*chain_obs(), stray], chain_readings(), target).status == "SUPPORTED"
    # GOOD instant supply/bus/start observations alone add no unusable limitation.
    extra = [obs("site_supply_state", 50, state="ENERGIZED"), obs("mini_backup_bus_state", 12, state="ENERGIZED"),
             obs("mini_backup_start_event", 12, kind="START_RESULT", outcome="SUCCEEDED", corr="c-1")]
    good = backup(HOUR, [*chain_obs(), *extra], chain_readings(), target)
    assert (good.status, good.chains[0].result, good.limitations) == ("SUPPORTED", "PASS", ())

    # q5 ruling 2: a bad supply row vetoes only the chain whose span contains it.
    two = [obs("site_supply_state", -5, state="ENERGIZED"), obs("site_supply_state", 2, state="LOST"),
           obs("mini_backup_start_event", 2.5, kind="START_REQUEST", outcome="REQUESTED", corr="c-1"),
           obs("mini_backup_start_event", 3, kind="START_RESULT", outcome="SUCCEEDED", corr="c-1"),
           obs("mini_backup_bus_state", 3.5, state="ENERGIZED"), obs("site_supply_state", 20, state="ENERGIZED"),
           obs("site_supply_state", 30, state="LOST"),
           obs("mini_backup_start_event", 30.5, kind="START_REQUEST", outcome="REQUESTED", corr="c-2"),
           obs("mini_backup_start_event", 31, kind="START_RESULT", outcome="SUCCEEDED", corr="c-2"),
           obs("mini_backup_bus_state", 31.5, state="ENERGIZED"), obs("site_supply_state", 50, state="ENERGIZED")]
    two_r = [*minutes("generator_power", "15", GEN, spans=((3, 20), (31, 50))),
             *minutes("critical_load_requested_power", "4", CRIT),
             *minutes("critical_load_delivered_power", "4", CRIT, spans=((0, 2), (4, 30), (32, 60))),
             *minutes("critical_load_delivered_power", "0", CRIT, spans=((2, 4), (30, 32)))]
    clean = backup(HOUR, two, two_r, target)
    assert [c.result for c in clean.chains] == ["PASS", "PASS"]
    inside = obs("site_supply_state", 40, state="LOST", quality="SUSPECT")
    h2 = backup(HOUR, [*two, inside], two_r, target)
    assert [c.result for c in h2.chains] == ["PASS", "INCOMPLETE"]
    assert h2.chains[0].critical_recovery is not None and h2.chains[1].critical_recovery is None
    assert h2.critical_recovery == h2.chains[0].critical_recovery
    assert (h2.status, ("REQUIRED_INPUT_UNUSABLE", (inside.evidence_id,))) == (
        "LIMITED", next((l.code, l.evidence_ids) for l in h2.limitations if l.code == "REQUIRED_INPUT_UNUSABLE"))
    # A bad row at the first chain's restoration instant belongs to the first chain (and the second's witness).
    edge = obs("site_supply_state", 20, state="LOST", quality="SUSPECT")
    assert [c.result for c in backup(HOUR, [*two, edge], two_r, target).chains] == ["INCOMPLETE", "INCOMPLETE"]
    # A bad row outside both chains limits the hour but erases neither result; an earlier unrelated prior row is
    # cited and vetoes nothing.
    outside = obs("site_supply_state", 55, state="ENERGIZED", quality="SUSPECT")
    early = obs("site_supply_state", -30, state="LOST", quality="SUSPECT")
    h3 = backup(HOUR, [early, *two, outside], two_r, target)
    assert ([c.result for c in h3.chains], h3.status) == (["PASS", "PASS"], "LIMITED")
    assert early.evidence_id in h3.evidence_ids
    assert ("REQUIRED_INPUT_UNUSABLE", (outside.evidence_id,)) in [(l.code, l.evidence_ids) for l in h3.limitations]

    # q5 ruling 3: complete GOOD steps plus a SUSPECT duplicate critical row in the second chain. Its observed step
    # times and IDs stay visible; the chain is INCOMPLETE/UNKNOWN with null recovery; the first keeps its own.
    dup = reading("critical_load_delivered_power", "4", 35, 36, asset=CRIT, quality="SUSPECT")
    h4 = backup(HOUR, two, [*two_r, dup], target)
    first, second = h4.chains
    assert (first.result, first.service_outcome, first.critical_recovery) == (
        "PASS", "RECOVERED", clean.chains[0].critical_recovery)
    assert (second.result, second.service_outcome, second.critical_recovery) == ("INCOMPLETE", "UNKNOWN", None)
    assert [(s.code, s.state, s.at, s.evidence_ids) for s in second.steps] == [
        (s.code, s.state, s.at, s.evidence_ids) for s in clean.chains[1].steps]
    assert all(s.state == "OBSERVED" and s.at is not None for s in second.steps)
    assert dup.evidence_id in second.unusable and dup.evidence_id in h4.evidence_ids
    assert h4.critical_recovery == first.critical_recovery and h4.status == "LIMITED"

    # q5 ruling 4: only the pinned critical asset's rows judge a chain; no unique pin -> no PASS/FAIL.
    other = uuid4()
    wrong = [r if not r.role.startswith("critical_load") else replace(r, asset_id=other) for r in chain_readings()]
    hw = backup(HOUR, chain_obs(), wrong, target)
    assert (hw.chains[0].result, hw.status, hw.coverage.observed_seconds) == ("INCOMPLETE", "UNKNOWN", 0)
    assert {r.evidence_id for r in wrong if r.role.startswith("critical_load")} <= set(hw.evidence_ids)
    mixed = [r if r.role != "critical_load_requested_power" else replace(r, asset_id=other) for r in chain_readings()]
    assert backup(HOUR, chain_obs(), mixed, target).chains[0].result == "INCOMPLETE"
    nopin = backup(HOUR, chain_obs(), chain_readings(), target, pin=None)
    assert (nopin.chains[0].result, nopin.chains[0].critical_recovery, nopin.status) == ("INCOMPLETE", None, "LIMITED")
    assert "CRITICAL_SERVICE_MISSING" in [l.code for l in nopin.limitations]
    assert backup(HOUR, no_bus, starved, target, pin=None).chains[0].result == "INCOMPLETE"
    unrelated = reading("critical_load_delivered_power", "4", 15, 16, asset=other, quality="SUSPECT")
    hu = backup(HOUR, chain_obs(), [*chain_readings(), unrelated], target)
    assert (hu.status, hu.chains[0].result) == ("SUPPORTED", "PASS") and unrelated.evidence_id in hu.evidence_ids
