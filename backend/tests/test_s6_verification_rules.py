"""S6-02a pure verification rules: slots, coverage, bands, target (no database)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from itertools import count

import pytest

from assetops_backend.actions import verification_rules as vr
from assetops_backend.actions.verification_rules import Reading, ReserveValue

UTC = timezone.utc
T0 = datetime(2026, 10, 1, 10, 0, tzinfo=UTC)
M = timedelta(minutes=1)
_ids = count(1)


def power(role, asset, start, end, value, *, unit="kW", quality="GOOD", rid=None):
    return Reading(rid or f"r{next(_ids)}", role, asset, "INTERVAL_MEAN", end, start, end, value, unit, quality)


def point(role, asset, at, value, *, unit="%", quality="GOOD", rid=None):
    return Reading(rid or f"p{next(_ids)}", role, asset, "STATE_AT_INSTANT", at, None, None, value, unit, quality)


def full_window(start=T0, *, loads=("load-a", "load-b"), load_kw="10", pv_kw="6", soc="50",
                skip=frozenset(), terminal=True):
    out = []
    for i in range(12):
        t = start + vr.SLOT * i
        e = t + vr.SLOT
        for role, asset, val in (("generator_power", "gen", "20"), ("pcs_discharge_capability", "pcs", "30"),
                                 ("pv_available_power", "inv", pv_kw),
                                 ("critical_load_requested_power", "crit", "4"),
                                 ("critical_load_delivered_power", "crit", "4")):
            out.append(power(role, asset, t, e, val))
        for load in loads:
            if (load, i) not in skip:
                out.append(power("feeder_demand", load, t, e, load_kw))
        out.append(point("generator_state", "gen", t, "ON", unit="state"))
        out.append(point("battery_soc", "bat", t, soc))
    if terminal:
        out.append(point("battery_soc", "bat", start + vr.WINDOW, soc))
    return out


RESERVE = [ReserveValue(Fraction(30), T0 - timedelta(days=1), None, "rev-1")]


def evidence(readings, *, loads=("load-a", "load-b"), crit="crit", reserves=RESERVE, start=T0):
    return vr.window_evidence(start, readings, load_asset_ids=list(loads), critical_load_asset_id=crit,
                              reserves=reserves)


# ------------------------------------------------------------------ windows / exact numbers


def test_window_alignment_and_slots():
    assert vr.window_problem(T0, T0 + vr.WINDOW) is None
    assert vr.window_problem(T0 + M, T0 + M + vr.WINDOW)
    assert vr.window_problem(T0 + timedelta(seconds=1), T0 + timedelta(seconds=1) + vr.WINDOW)
    assert vr.window_problem(T0, T0 + timedelta(minutes=55))
    assert vr.window_problem(T0.replace(tzinfo=None), T0.replace(tzinfo=None) + vr.WINDOW)
    other = timezone(timedelta(hours=3))
    assert vr.window_problem(T0.astimezone(other), T0.astimezone(other) + vr.WINDOW)
    slots = vr.slot_starts(T0)
    assert len(slots) == 12 and slots[0] == T0 and slots[-1] == T0 + 55 * M
    with pytest.raises(ValueError):
        evidence(full_window(), start=T0 + 2 * M)


def test_fmt_exact():
    assert vr.fmt(Fraction(1, 3)) == "1/3"
    assert vr.fmt(Fraction(1, 120)) == "1/120"
    assert vr.fmt(Fraction(1, 8)) == "0.125"
    assert vr.fmt(Fraction(-5, 2)) == "-2.5"
    assert vr.fmt(Fraction(3)) == "3"
    assert vr.parse_exact("1/3") == Fraction(1, 3)
    assert vr.parse_exact("NaN") is None and vr.parse_exact("inf") is None


def test_bands_payload_frozen():
    b = vr.bands_payload()
    assert b["feeder_demand_energy_relative"] == "0.1" and b["initial_soc_points"] == "2"
    assert b["guardrail_basis"] == "FIVE_MINUTE_SAMPLED" and b["plan_version"] == vr.PLAN_VERSION


# ------------------------------------------------------------------ power coverage


def test_whole_slot_exact_arithmetic():
    out = vr.power_slot(T0, [power("pv_available_power", "inv", T0, T0 + vr.SLOT, "0.1")])
    assert out["state"] == "COVERED"
    assert vr.parse_exact(out["kwh"]) == Fraction(1, 10) * Fraction(1, 12)
    assert out["kwh"] == "1/120"


def test_exact_partition_vs_gap():
    half = timedelta(seconds=150)
    ok = vr.power_slot(T0, [power("x", "a", T0, T0 + half, "2"), power("x", "a", T0 + half, T0 + vr.SLOT, "4")])
    assert ok["state"] == "COVERED" and vr.parse_exact(ok["kwh"]) == Fraction(2 * 150 + 4 * 150, 3600)
    gap = vr.power_slot(T0, [power("x", "a", T0, T0 + half, "2"), power("x", "a", T0 + 3 * M, T0 + vr.SLOT, "4")])
    assert gap["state"] == "UNKNOWN" and gap["kwh"] is None and gap["problems"][0]["code"] == "GAP"
    tail = vr.power_slot(T0, [power("x", "a", T0, T0 + half, "2")])
    assert tail["problems"][0]["code"] == "GAP"


def test_conflicting_overlap_and_identical_duplicate():
    a = power("x", "a", T0, T0 + vr.SLOT, "2")
    b = power("x", "a", T0, T0 + vr.SLOT, "3")
    assert vr.power_slot(T0, [a, b])["problems"][0]["code"] == "CONFLICT"
    c = power("x", "a", T0 + M, T0 + 2 * M, "2")
    assert vr.power_slot(T0, [a, c])["problems"][0]["code"] == "CONFLICT"
    dup = power("x", "a", T0, T0 + vr.SLOT, "2")
    out = vr.power_slot(T0, [a, dup])
    assert out["state"] == "COVERED" and len(out["evidence_ids"]) == 2
    textual = power("x", "a", T0, T0 + vr.SLOT, "2.0")
    assert vr.power_slot(T0, [a, textual])["problems"][0]["code"] == "CONFLICT"


def test_point_only_power_and_spanning_boundary():
    pt = Reading("pt", "x", "a", "STATE_AT_INSTANT", T0, None, None, "5", "kW", "GOOD")
    assert vr.power_slot(T0, [pt])["problems"][0]["code"] == "POINT_ONLY"
    span = power("x", "a", T0 - M, T0 + 4 * M, "5")
    out = vr.power_slot(T0, [span, power("x", "a", T0 + 4 * M, T0 + vr.SLOT, "5")])
    assert out["state"] == "UNKNOWN" and out["problems"][0]["code"] == "SPANS_SLOT_BOUNDARY"
    assert vr.power_slot(T0, [])["problems"][0]["code"] == "GAP"


@pytest.mark.parametrize("value,unit,quality,code", [
    ("-1", "kW", "GOOD", "INVALID_VALUE"), ("NaN", "kW", "GOOD", "INVALID_VALUE"),
    ("abc", "kW", "GOOD", "INVALID_VALUE"), (None, "kW", "GOOD", "INVALID_VALUE"),
    ("5", "W", "GOOD", "INVALID_UNIT"), ("5", "kW", "STALE", "NOT_ACCEPTED"),
    ("5", "kW", "SUSPECT", "NOT_ACCEPTED"),
])
def test_invalid_power_values(value, unit, quality, code):
    out = vr.power_slot(T0, [power("x", "a", T0, T0 + vr.SLOT, value, unit=unit, quality=quality)])
    assert out["state"] == "UNKNOWN" and out["problems"][0]["code"] == code


# ------------------------------------------------------------------ SOC / reserve


def test_soc_samples_missing_terminal_and_conflict():
    starts = vr.slot_starts(T0)
    reads = [point("battery_soc", "bat", t, "50") for t in starts]
    out = vr.soc_samples(starts, T0 + vr.WINDOW, reads)
    assert len(out) == 13 and all(s["state"] == "KNOWN" for s in out[:12])
    assert out[12]["state"] == "UNKNOWN" and out[12]["problems"][0]["code"] == "MISSING_SAMPLE"
    reads.append(point("battery_soc", "bat", T0, "51"))
    reads.append(point("battery_soc", "bat", T0 + vr.WINDOW - timedelta(seconds=1), "50"))
    out = vr.soc_samples(starts, T0 + vr.WINDOW, reads)
    assert out[0]["problems"][0]["code"] == "CONFLICT"
    assert out[12]["state"] == "UNKNOWN"  # never carried from a nearby instant


def test_reserve_change_mid_slot_and_none_effective():
    starts = vr.slot_starts(T0)
    reserves = [ReserveValue(Fraction(30), T0 - timedelta(days=1), T0 + 7 * M, "r1"),
                ReserveValue(Fraction(40), T0 + 7 * M, None, "r2")]
    out = vr.reserve_at_slots(starts, reserves)
    assert out[0]["state"] == "KNOWN" and out[0]["value"] == "30"
    assert out[1]["state"] == "UNASSESSABLE" and out[1]["problems"][0]["code"] == "RESERVE_CHANGED_IN_SLOT"
    assert out[2]["state"] == "KNOWN" and out[2]["value"] == "40"
    boundary = [ReserveValue(Fraction(30), T0 - M, T0 + 5 * M, "r1"), ReserveValue(Fraction(40), T0 + 5 * M, None, "r2")]
    assert [s["state"] for s in vr.reserve_at_slots(starts[:2], boundary)] == ["KNOWN", "KNOWN"]
    assert vr.reserve_at_slots(starts[:1], [])[0]["state"] == "UNKNOWN"


# ------------------------------------------------------------------ window evidence


def test_complete_window_totals():
    ev = evidence(full_window())
    assert ev["complete"] is True and ev["problems"] == []
    assert ev["guardrail_basis"] == "FIVE_MINUTE_SAMPLED" and ev["power_semantics"] == "INTERVAL_MEAN"
    assert ev["feeder_demand_kwh"] == "20"  # two loads x 10 kW x 1 h
    assert ev["pv_available_kwh"] == "6"
    assert ev["unserved_critical_kwh"] == "0"
    assert ev["below_reserve_seconds"] == 0
    assert ev["initial_soc"] == "50" and ev["terminal_soc"] == "50"
    assert len(ev["slots"]) == 12


def test_below_reserve_counts_300_per_slot():
    ev = evidence(full_window(soc="25"))
    assert ev["below_reserve_seconds"] == 12 * 300
    assert all(s["below_reserve_seconds"] == 300 for s in ev["slots"])
    equal = evidence(full_window(soc="30"))
    assert equal["below_reserve_seconds"] == 0


def test_missing_terminal_soc_incomplete():
    ev = evidence(full_window(terminal=False))
    assert ev["complete"] is False and ev["terminal_soc"] is None
    assert any(p["code"] == "MISSING_SAMPLE" and p["slot_start"] == vr._iso(T0 + vr.WINDOW) for p in ev["problems"])


def test_reserve_change_makes_window_incomplete():
    reserves = [ReserveValue(Fraction(30), T0 - timedelta(days=1), T0 + 12 * M, "r1"),
                ReserveValue(Fraction(30), T0 + 12 * M, None, "r2")]
    ev = evidence(full_window(), reserves=reserves)
    assert ev["slots"][2]["reserve"]["state"] == "UNASSESSABLE" and ev["slots"][2]["below_reserve_seconds"] is None
    assert ev["below_reserve_seconds"] is None and ev["complete"] is False


def test_missing_load_slot_never_shrinks_total():
    ev = evidence(full_window(skip={("load-b", 4)}))
    assert ev["feeder_demand_kwh"] is None and ev["complete"] is False
    assert any(p["role"] == "feeder_demand" and p["asset_id"] == "load-b" for p in ev["problems"])
    # an unreported bound load asset leaves the total unknown, not the other load's sum
    ev2 = evidence(full_window(loads=("load-a",)), loads=("load-a", "load-b"))
    assert ev2["feeder_demand_kwh"] is None
    ev3 = evidence(full_window(), loads=())
    assert ev3["feeder_demand_kwh"] is None
    assert any(p["code"] == "MISSING_BINDING" for p in ev3["problems"])


def test_missing_critical_binding_unknown():
    ev = evidence(full_window(), crit=None)
    assert ev["unserved_critical_kwh"] is None and ev["complete"] is False
    assert any(p["code"] == "MISSING_BINDING" and p["role"] == "critical_load_requested_power"
               for p in ev["problems"])


def test_unserved_critical_energy():
    reads = [r for r in full_window() if not (r.role == "critical_load_delivered_power" and r.interval_start == T0)]
    reads.append(power("critical_load_delivered_power", "crit", T0, T0 + vr.SLOT, "1"))
    ev = evidence(reads)
    assert ev["unserved_critical_kwh"] == "0.25"  # (4-1) kW * 5 min


# ------------------------------------------------------------------ comparability


def _cmp(base_feeder, later_feeder, base_pv="100", later_pv="100", base_soc="50", later_soc="50"):
    return vr.comparability(
        {"feeder_demand_kwh": base_feeder, "pv_available_kwh": base_pv, "initial_soc": base_soc},
        {"feeder_demand_kwh": later_feeder, "pv_available_kwh": later_pv, "initial_soc": later_soc})


@pytest.mark.parametrize("later,state", [("110", "PASS"), ("110.0001", "FAIL"), ("90", "PASS"),
                                         ("89.999", "FAIL"), ("100", "PASS")])
def test_feeder_energy_band_edges(later, state):
    assert _cmp("100", later)["state"] == state


@pytest.mark.parametrize("later,state", [("110", "PASS"), ("110.0001", "FAIL"), ("90", "PASS"), ("89.999", "FAIL")])
def test_pv_energy_band_edges(later, state):
    assert _cmp("100", "100", later_pv=later)["state"] == state


@pytest.mark.parametrize("later,state", [("52", "PASS"), ("48", "PASS"), ("52.0001", "FAIL"), ("47.999", "FAIL")])
def test_initial_soc_band_edges(later, state):
    assert _cmp("100", "100", later_soc=later)["state"] == state


def test_zero_baseline_and_unknown():
    assert _cmp("0", "0")["state"] == "PASS"
    assert _cmp("0", "0.0001")["state"] == "FAIL"
    assert _cmp("100", None)["state"] == "UNKNOWN"
    assert _cmp(None, "100")["state"] == "UNKNOWN"
    assert _cmp("100", "200", later_soc=None)["state"] == "UNKNOWN"  # unknown dominates a known failure


def test_comparability_exact_thresholds_and_float_free():
    out = _cmp("0.3", "0.33")  # 0.1 * 0.3 == 0.03 exactly; float would say 0.030000000000000027
    feeder = out["checks"][0]
    assert feeder["state"] == "PASS" and feeder["threshold"] == "0.03" and feeder["difference"] == "0.03"


def test_comparability_one_missing_load_in_later_window_unknown():
    base = evidence(full_window())
    later = evidence(full_window(skip={("load-a", 11)}))
    assert vr.comparability(base, later)["state"] == "UNKNOWN"
    assert vr.comparability(base, evidence(full_window()))["state"] == "PASS"


# ------------------------------------------------------------------ target


def seg(start, end, cls):
    return {"start": vr._iso(start), "end": vr._iso(end), "classification": cls}


def interval(rev, day, first_on, segments, *, open_bound=False, asset="gen"):
    limits = ["OPEN_BOUND: no OFF evidence after the interval in the read range"] if open_bound else []
    return {"assessment_revision_id": rev, "day": day,
            "result": {"generator_asset_id": asset, "claim_level": "CANDIDATE_AVOIDABLE",
                       "interval": {"first_on": vr._iso(first_on)}, "segments": segments, "limitations": limits}}


MID = datetime(2026, 10, 2, 0, 0, tzinfo=UTC)


def test_target_days():
    assert vr.target_days(MID) == [date(2026, 10, 1), date(2026, 10, 2)]
    assert vr.target_days(datetime(2026, 10, 1, 23, 30, tzinfo=UTC)) == [
        date(2026, 9, 30), date(2026, 10, 1), date(2026, 10, 2)]


def test_target_cross_midnight_keeps_seconds():
    prev = interval("rev-prev", "2026-10-01", MID - 40 * M,
                    [seg(MID - 40 * M, MID - 20 * M, "NECESSARY"), seg(MID - 20 * M, MID + 25 * M, "CANDIDATE_AVOIDABLE")])
    today = interval("rev-today", "2026-10-02", MID + 40 * M, [seg(MID + 40 * M, MID + 50 * M, "CANDIDATE_AVOIDABLE")])
    out = vr.target_window(MID, [prev, today])
    assert out["state"] == "KNOWN"
    assert out["candidate_seconds"] == 25 * 60 + 10 * 60
    assert out["assessment_revision_ids"] == ["rev-prev", "rev-today"]
    assert vr.target_window(MID, [today])["candidate_seconds"] == 600  # without the previous day: lost seconds


def test_target_segment_crossing_window_end_counts_overlap_only():
    item = interval("r", "d", T0 + 50 * M, [seg(T0 + 50 * M, T0 + 80 * M, "CANDIDATE_AVOIDABLE")])
    assert vr.target_window(T0, [item])["candidate_seconds"] == 600
    outside = interval("r2", "d", T0 + 70 * M, [seg(T0 + 70 * M, T0 + 80 * M, "INDETERMINATE")], open_bound=True)
    out = vr.target_window(T0, [item, outside])
    assert out["state"] == "KNOWN" and out["assessment_revision_ids"] == ["r"]


def test_target_open_bound_inconclusive():
    item = interval("r", "d", T0, [seg(T0, T0 + 10 * M, "NECESSARY")], open_bound=True)
    out = vr.target_window(T0, [item])
    assert out["state"] == "INCONCLUSIVE" and out["candidate_seconds"] is None
    assert any(r.startswith("OPEN_BOUND") for r in out["reasons"])


def test_target_indeterminate_inconclusive():
    item = interval("r", "d", T0, [seg(T0, T0 + 10 * M, "CANDIDATE_AVOIDABLE"),
                                   seg(T0 + 10 * M, T0 + 12 * M, "INDETERMINATE")])
    out = vr.target_window(T0, [item])
    assert out["state"] == "INCONCLUSIVE" and any(r.startswith("INDETERMINATE") for r in out["reasons"])


def test_target_met_edges():
    assert vr.target_met(400, 300) is True
    assert vr.target_met(400, 301) is False
    assert vr.target_met(0, 0) is True
    assert vr.target_met(None, 0) is None and vr.target_met(100, None) is None
