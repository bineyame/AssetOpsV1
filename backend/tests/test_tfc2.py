"""FUEL-1 A2: `trial-fuel-comparison/2` (`financials/trial_fuel_comparison.py`) and the window idle seconds
(`actions/verification_rules.window_evidence`), no database.

`.agent/build-sheet-FUEL-1.md` §4.2: v1 byte-equal without a rate in force over both windows; idle only (the demo
figures, computed here from the inputs); loaded only; mixed; both new reasons; the priced total and its credit.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from uuid import UUID

import pytest

import test_s6_verification_rules as s6
from assetops_backend.actions import verification_rules as vr
from assetops_backend.financials import trial_fuel_comparison as tfc
from assetops_backend.financials.fuel_cost import MULTIPLIER, PriceSelection
from assetops_backend.mini_depth.rules import SfcValue
from assetops_backend.outcomes import credit

UTC = timezone.utc
B0 = datetime(2026, 10, 6, 8, 0, tzinfo=UTC)
L0 = datetime(2026, 11, 2, 8, 0, tzinfo=UTC)
H = timedelta(hours=1)
REV = UUID(int=7)
SFC_VALUE, R, PRICE, DEMAND = Decimal("0.3"), Decimal("3.3"), Decimal("1.25"), Fraction(15)
SFC = (SfcValue(REV, SFC_VALUE, datetime(2026, 1, 1, tzinfo=UTC), None),)
RATE = (tfc.NoLoadValue(REV, R, datetime(2026, 1, 1, tzinfo=UTC), None),)
V1 = PriceSelection("PRICED", None, "price-v1", PRICE, "USD")
COST = tfc.InterventionCost(Fraction(0), None, "Generator stop setting changed; no direct cost declared")
OUT = tfc.OutcomeFacts("outcome-1", "plan-1", "rev-1", "VERIFIED", {"baseline": ("b1",), "later": ("l1",)},
                       "PASS", "PASS")


def window(start, gen, idle, ids, feeder=DEMAND) -> tfc.WindowFacts:
    return tfc.WindowFacts(tuple(ids), True, Fraction(gen), feeder, start, start + H, idle)


#: the demo trial hour: baseline 12 slots RUNNING at 0 kWh (3600 s idle), later 0 idle slots, 15 kWh demand each
IDLE_BASE, IDLE_LATER = window(B0, 0, 3600, ("b1",)), window(L0, 0, 0, ("l1",))


def run(baseline=IDLE_BASE, later=IDLE_LATER, no_load=RATE, sfc=SFC, prices=(V1, V1), outcome=OUT):
    return tfc.compare(baseline, later, outcome, sfc, prices, COST, no_load)


def fuel(gen, idle) -> Fraction:
    return Fraction(SFC_VALUE) * Fraction(gen) + Fraction(R) * Fraction(idle, 3600)


# ------------------------------------------------------------------ v1 byte-equal


def test_v1_byte_equal_without_a_rate_in_force_over_both_windows():
    base, later = window(B0, 40, 3600, ("b1",)), window(L0, 28, 0, ("l1",))
    plain = tfc.compare(replace(base, idle_seconds=None), replace(later, idle_seconds=None), OUT, SFC, (V1, V1), COST)
    for no_load in ((), (tfc.NoLoadValue(REV, R, B0, B0 + H),), (tfc.NoLoadValue(REV, R, L0, None),),
                    (tfc.NoLoadValue(REV, Decimal("0"), B0, None),), RATE + RATE):
        out = tfc.compare(base, later, OUT, SFC, (V1, V1), COST, no_load)
        assert out == plain, no_load  # idle seconds are ignored and the digest is the v1 digest
    assert plain["formula"] == "trial-fuel-comparison/1" and "priced_total" not in plain and "no_load" not in plain
    assert set(plain["windows"]["baseline"]) == {"generator_kwh", "feeder_demand_kwh", "fuel_l", "cost",
                                                 "cost_per_demand_kwh"}


# ------------------------------------------------------------------ v2


def test_idle_only_demo_figures_from_the_inputs():
    out = run()
    assert (out["formula"], out["state"], out["reason"]) == ("trial-fuel-comparison/2", "MODELLED_IMPROVEMENT", None)
    change_l = fuel(0, 3600) - fuel(0, 0)
    amount = change_l * Fraction(PRICE)
    assert change_l == Fraction(33, 10) and amount == Fraction(4125, 1000)
    assert out["priced_total"] == {"amount": vr.fmt(amount), "currency": "USD", "basis": "TRIAL_HOUR_MODELLED_FUEL",
                                   "window": [L0.isoformat(), (L0 + H).isoformat()], "fuel_change_l": vr.fmt(change_l)}
    assert out["change_per_demand_kwh"]["nominal"] == vr.fmt(amount / DEMAND) == "0.275"
    assert out["windows"]["baseline"]["fuel_l"] == {"nominal": vr.fmt(fuel(0, 3600)),
                                                    "upper": vr.fmt(fuel(0, 3600) * Fraction(MULTIPLIER))}
    assert (out["windows"]["baseline"]["idle_seconds"], out["windows"]["later"]["idle_seconds"]) == (3600, 0)
    assert out["no_load"] == {"value_l_per_h": "3.3"}
    assert credit.credited({**out, "outcome_id": "outcome-1"}, "VERIFIED") == ((33, 8), "USD")
    assert credit.recovered_value([(out, "VERIFIED")])["items"] == [
        {"key": "outcome-1", "currency": "USD", "amount": "4.125", "basis": "TRIAL_HOUR_MODELLED_FUEL"}]


def test_loaded_only_with_a_rate_declared_equals_v1_fuel():
    base, later = window(B0, 40, 0, ("b1",), Fraction(120)), window(L0, 28, 0, ("l1",), Fraction(126))
    v2 = run(base, later)
    v1 = run(base, later, no_load=())
    assert v2["formula"] == "trial-fuel-comparison/2" and v1["formula"] == "trial-fuel-comparison/1"
    for name in tfc.WINDOWS:
        assert {k: v2["windows"][name][k] for k in v1["windows"][name]} == v1["windows"][name]
    assert v2["change_per_demand_kwh"] == v1["change_per_demand_kwh"]
    assert v2["basis_sha256"] != v1["basis_sha256"]
    assert v2["priced_total"]["amount"] == vr.fmt((fuel(40, 0) - fuel(28, 0)) * Fraction(PRICE)) == "4.5"


def test_mixed_loaded_and_idle():
    base, later = window(B0, 10, 1800, ("b1",)), window(L0, 10, 300, ("l1",))
    out = run(base, later)
    nominal = fuel(10, 1800)
    assert out["windows"]["baseline"]["fuel_l"]["nominal"] == vr.fmt(nominal) == "4.65"
    assert out["priced_total"]["fuel_change_l"] == vr.fmt(fuel(10, 1800) - fuel(10, 300)) == "1.375"
    assert out["priced_total"]["amount"] == vr.fmt((fuel(10, 1800) - fuel(10, 300)) * Fraction(PRICE))


def test_idle_seconds_unknown_and_no_load_rate_differs():
    unknown = run(later=replace(IDLE_LATER, idle_seconds=None))
    assert (unknown["state"], unknown["reason"]) == ("UNAVAILABLE", "IDLE_SECONDS_UNKNOWN")
    assert unknown["windows"]["later"]["fuel_l"] is None and "priced_total" not in unknown
    two = (tfc.NoLoadValue(REV, R, B0, B0 + H), tfc.NoLoadValue(UUID(int=8), Decimal("3.4"), L0, None))
    differs = run(no_load=two)
    assert (differs["formula"], differs["reason"]) == ("trial-fuel-comparison/2", "NO_LOAD_RATE_DIFFERS")
    assert differs["no_load"] is None and differs["change_per_demand_kwh"] is None
    # SFC reasons still come first
    assert run(no_load=two, sfc=())["reason"] == "SFC_MISSING"


def test_no_improvement_has_no_priced_total():
    out = run(window(B0, 0, 0, ("b1",)), window(L0, 0, 600, ("l1",)))
    assert out["state"] == "MODELLED_NO_IMPROVEMENT" and "priced_total" not in out
    assert credit.credited(out, "VERIFIED") is None


def test_digest_covers_the_idle_inputs():
    base = run()
    assert run(baseline=replace(IDLE_BASE, idle_seconds=3300))["basis_sha256"] != base["basis_sha256"]
    other = (tfc.NoLoadValue(REV, Decimal("3.0"), datetime(2026, 1, 1, tzinfo=UTC), None),)
    assert run(no_load=other)["basis_sha256"] != base["basis_sha256"]
    assert run()["basis_sha256"] == base["basis_sha256"]


# ------------------------------------------------------------------ window idle seconds


def _states(readings, state_by_slot):
    out = []
    for r in readings:
        if r.role == "generator_state":
            i = int((r.source_time - s6.T0) / vr.SLOT)
            value = state_by_slot.get(i, r.value_text)
            if value is None:
                continue
            r = replace(r, value_text=value)
        out.append(r)
    return out


def test_window_idle_seconds_count_running_slots_at_zero_kwh():
    running = {i: "RUNNING" for i in range(12)}
    assert s6.evidence(_states(s6.full_window(gen_kw="0"), running))["generator_idle_seconds"] == 3600
    # running but loaded, or at 0 kWh but not running: not idle
    assert s6.evidence(_states(s6.full_window(gen_kw="20"), running))["generator_idle_seconds"] == 0
    assert s6.evidence(s6.full_window(gen_kw="0"))["generator_idle_seconds"] == 0  # state "ON"
    three = {i: "RUNNING" for i in range(3)}
    assert s6.evidence(_states(s6.full_window(gen_kw="0"), three))["generator_idle_seconds"] == 900


def test_window_idle_seconds_unknown_when_a_slot_is_unknown():
    missing_state = _states(s6.full_window(gen_kw="0"), {4: None})
    assert s6.evidence(missing_state)["generator_idle_seconds"] is None
    gap = [r for r in s6.full_window(gen_kw="0")
           if not (r.role == "generator_power" and r.interval_start == s6.T0 + vr.SLOT * 3)]
    assert s6.evidence(gap)["generator_idle_seconds"] is None
