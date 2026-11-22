"""DD3c part 3 remainder (D-DD.118, D-DD.117's shape): the modelled cost check's fuel per unit, summed.

Each GENERATOR unit burns on its own SFC (and, under `/2`, idles on its own no-load rate) over its own kWh and idle
seconds; the window fuel is the sum. A two-unit roles-5 Site no longer reads UNAVAILABLE. One unit: unchanged
(`test_dd3c_kobo_one_unit_golden.py`)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from fractions import Fraction
from types import SimpleNamespace
from uuid import UUID

from test_s6_verification_rules import RESERVE, T0, full_window, point, power

from assetops_backend.actions import verification_rules as vr
from assetops_backend.actions.verification import VerificationService
from assetops_backend.financials import trial_fuel_comparison as tfc
from assetops_backend.financials.fuel_cost import PriceSelection
from assetops_backend.mini_depth.rules import SfcValue
from assetops_backend.sites.binding_roles import ROLE_SET_MINIGRID_4, ROLE_SET_MINIGRID_5

T1 = T0 + timedelta(days=1)
SINCE = T0 - timedelta(days=30)
UNITS = ("generator_power", "generator_state")
ROLE_ASSETS = {"generator_power": ["gen", "gen-2"], "generator_state": ["gen", "gen-2"]}
PRICE = PriceSelection("PRICED", None, "price-1", Decimal("1.25"), "USD")


def two_units(start, gen_kw: str = "20", gen2_kw: str = "6", gen2_state: str = "RUNNING", silent2=False) -> list:
    out = [replace(r, value_text="RUNNING") if r.role == "generator_state" else r
           for r in full_window(start, gen_kw=gen_kw)]
    if silent2:
        return out + [point("generator_state", "gen-2", start, "RUNNING", unit="state")]
    for i in range(12):
        t = start + vr.SLOT * i
        out.append(power("generator_power", "gen-2", t, t + vr.SLOT, gen2_kw))
        out.append(point("generator_state", "gen-2", t, gen2_state, unit="state"))
    return out


def window(start, readings):
    return vr.window_evidence(start, readings, load_asset_ids=["load-a", "load-b"], critical_load_asset_id="crit",
                              reserves=RESERVE, battery_asset_id="bat", role_assets=ROLE_ASSETS, unit_roles=UNITS)


def sfc(value: str, rid: int = 1, valid_to=None) -> list[SfcValue]:
    return [SfcValue(UUID(int=rid), Decimal(value), SINCE, valid_to)]


def rate(value: str, rid: int = 2) -> list[tfc.NoLoadValue]:
    return [tfc.NoLoadValue(UUID(int=rid), Decimal(value), SINCE, None, "GENERIC_DEFAULT")]


# ------------------------------------------------------------------------------ window evidence: per-unit use


def test_c1_window_states_each_units_kwh_and_idle_seconds() -> None:
    w = window(T0, two_units(T0, gen2_kw="0"))
    assert w["generator_kwh"] == "20"
    assert w["generator_units"] == {"gen": {"generator_kwh": "20", "idle_seconds": 0},
                                    "gen-2": {"generator_kwh": "0", "idle_seconds": 3600}}


def test_c1b_one_unit_window_has_no_units_key() -> None:
    w = vr.window_evidence(T0, full_window(T0), load_asset_ids=["load-a", "load-b"], critical_load_asset_id="crit",
                           reserves=RESERVE, battery_asset_id="bat", unit_roles=UNITS)
    assert "generator_units" not in w


# ------------------------------------------------------------------------------ compare: per-unit fuel, summed


def facts(start, w) -> tfc.WindowFacts:
    return tfc.WindowFacts(tuple(w["evidence_ids"]), bool(w["complete"]), vr.parse_exact(w["generator_kwh"]),
                           vr.parse_exact(w["feeder_demand_kwh"]), start, start + vr.WINDOW,
                           w["generator_idle_seconds"],
                           {a: (vr.parse_exact(u["generator_kwh"]), u["idle_seconds"])
                            for a, u in w.get("generator_units", {}).items()})


def compare(base, later, units, no_load=False):
    out = tfc.OutcomeFacts("o", "p", "f", "VERIFIED", {"baseline": base[1]["evidence_ids"],
                                                       "later": later[1]["evidence_ids"]}, "PASS", "PASS")
    return tfc.compare(facts(T0, base[1]), facts(T1, later[1]), out, (), (PRICE, PRICE),
                       tfc.InterventionCost(Fraction(0), None, "x"), (), units=units)


def test_c2_two_units_burn_each_on_its_own_sfc() -> None:
    base = (T0, window(T0, two_units(T0, gen_kw="20", gen2_kw="6")))
    later = (T1, window(T1, two_units(T1, gen_kw="10", gen2_kw="6")))
    units = (tfc.TrialUnit("gen", sfc("0.3")), tfc.TrialUnit("gen-2", sfc("0.5", 3)))
    r = compare(base, later, units)
    assert r["state"] == "MODELLED_IMPROVEMENT" and r["reason"] is None
    assert r["windows"]["baseline"]["fuel_l"]["nominal"] == vr.fmt(Fraction(3, 10) * 20 + Fraction(1, 2) * 6)
    assert r["windows"]["later"]["fuel_l"]["nominal"] == vr.fmt(Fraction(3, 10) * 10 + Fraction(1, 2) * 6)
    assert [u["asset_id"] for u in r["windows"]["baseline"]["units"]] == ["gen", "gen-2"]
    assert r["sfc"] is None and r["formula"] == tfc.FORMULA


def test_c3_two_units_idle_each_on_its_own_no_load_rate() -> None:
    base = (T0, window(T0, two_units(T0, gen_kw="20", gen2_kw="0")))
    later = (T1, window(T1, two_units(T1, gen_kw="20", gen2_kw="6")))
    units = (tfc.TrialUnit("gen", sfc("0.3"), rate("4")), tfc.TrialUnit("gen-2", sfc("0.5", 3), rate("2", 4)))
    r = compare(base, later, units)
    assert r["formula"] == tfc.FORMULA_V2 and r["reason"] is None
    assert r["windows"]["baseline"]["fuel_l"]["nominal"] == vr.fmt(Fraction(3, 10) * 20 + 2 * 1)
    assert r["windows"]["later"]["fuel_l"]["nominal"] == vr.fmt(Fraction(3, 10) * 20 + Fraction(1, 2) * 6)


def test_c4_a_unit_without_sfc_gives_sfc_missing() -> None:
    base = (T0, window(T0, two_units(T0)))
    later = (T1, window(T1, two_units(T1)))
    r = compare(base, later, (tfc.TrialUnit("gen", sfc("0.3")), tfc.TrialUnit("gen-2", [])))
    assert (r["state"], r["reason"]) == ("UNAVAILABLE", "SFC_MISSING")


def test_c5_a_units_sfc_differing_between_windows_gives_sfc_differs() -> None:
    base = (T0, window(T0, two_units(T0)))
    later = (T1, window(T1, two_units(T1)))
    cut = T0 + timedelta(hours=12)
    gen2 = [*sfc("0.5", 3, valid_to=cut), SfcValue(UUID(int=5), Decimal("0.6"), cut, None)]
    r = compare(base, later, (tfc.TrialUnit("gen", sfc("0.3")), tfc.TrialUnit("gen-2", gen2)))
    assert (r["state"], r["reason"]) == ("UNAVAILABLE", "SFC_DIFFERS")


def test_c6_a_silent_unit_gives_generator_kwh_unknown() -> None:
    base = (T0, window(T0, two_units(T0)))
    later = (T1, window(T1, two_units(T1, silent2=True)))
    r = compare(base, later, (tfc.TrialUnit("gen", sfc("0.3")), tfc.TrialUnit("gen-2", sfc("0.5", 3))))
    assert r["state"] == "UNAVAILABLE"
    assert r["reason"] in ("WINDOW_INCOMPLETE", "GENERATOR_KWH_UNKNOWN")


# ------------------------------------------------------------------------------ the service: a two-unit Site


def service(windows, histories):
    appended = []
    trial = SimpleNamespace(store=SimpleNamespace(append=lambda row: (appended.append(row), (row, True))[1]),
                            price_selection=lambda *a: PRICE)
    store = SimpleNamespace(sfc_history=lambda t, s, g, lo, hi, now: histories[g][0],
                            no_load_history=lambda t, s, g, lo, hi, now: histories[g][1])
    svc = VerificationService(SimpleNamespace(store=store, clock=lambda: T1 + timedelta(days=2),
                                              verification_ports=SimpleNamespace(trial_comparison=trial,
                                                                                 provenance=None)))
    svc._window_replay = lambda *a: (windows, {"state": "PASS"}, {"state": "PASS"})
    return svc, appended


def run_cost_check(role_sets=(ROLE_SET_MINIGRID_5,)):
    windows = {"baseline": window(T0, two_units(T0, gen_kw="20")), "later": window(T1, two_units(T1, gen_kw="10"))}
    svc, appended = service(windows, {"gen": (sfc("0.3"), []), "gen-2": (sfc("0.5", 3), [])})
    plan = {"id": UUID(int=61), "baseline_start": T0, "baseline_end": T0 + vr.WINDOW, "later_start": T1,
            "later_end": T1 + vr.WINDOW, "basis": {"baseline_bindings": {"role_assets": ROLE_ASSETS,
                                                                          "role_sets": list(role_sets)}}}
    outcome = {"id": UUID(int=62), "action_id": UUID(int=63), "outcome": "VERIFIED",
               "basis": {"origin_finding_revision_id": UUID(int=64),
                         "evidence_ids": {n: windows[n]["evidence_ids"] for n in windows}}}
    request = dict.fromkeys(("actor_kind", "actor_id", "source_channel", "authorization_basis",
                             "triggering_service", "triggering_fixture"))
    svc._cost_check(UUID(int=65), UUID(int=66), plan, outcome, request)
    return appended[0]


def test_c7_two_unit_site_cost_check_is_no_longer_unavailable() -> None:
    row = run_cost_check()
    assert (row["state"], row["reason"]) == ("MODELLED_IMPROVEMENT", None)
    assert row["result"]["windows"]["baseline"]["fuel_l"]["nominal"] == vr.fmt(
        Fraction(3, 10) * 20 + Fraction(1, 2) * 6)


def test_c8_two_units_under_a_one_binding_set_stay_unavailable() -> None:
    row = run_cost_check(role_sets=(ROLE_SET_MINIGRID_4,))
    assert row["state"] == "UNAVAILABLE"
