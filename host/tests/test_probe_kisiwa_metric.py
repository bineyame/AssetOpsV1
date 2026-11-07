"""DIESEL-1 D0 (§2.5, §2.10 item 3): the night metric on a hand-built 4-step series. L0, no DB, no run."""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from probe_kisiwa_nights import COLD_STORE, FUEL, GEN, SOC, measure_night  # noqa: E402

SFC = Fraction(355, 1000)


def _step(state: str, kw: Fraction, soc: int, demand: int, cold_unserved=Fraction(0), res_unserved=Fraction(0)):
    energy = kw * Fraction(5, 60)
    view = NS(entries=(NS(name="state-of-charge", value=Fraction(soc)), NS(name="reserve-in-effect", value=Fraction(30)),
                       NS(name="pv-available", value=Fraction(0)), NS(name="load-demand", value=Fraction(demand))))
    accepted = NS(flows=(NS(flow_id="generator_output", energy=energy),),
                  loads=(NS(address=COLD_STORE, unserved_energy=cold_unserved),
                         NS(address="load-demand@load-res", unserved_energy=res_unserved)))
    return state, energy, NS(view=view, accepted=accepted), soc


def _series(steps, end_soc: int):
    boundaries, fuel = [], Fraction(1000)
    for state, energy, control, soc in steps:
        boundaries.append(NS(stocks=((SOC, Fraction(soc)), (FUEL, fuel)), discrete_for_step=((GEN, state),),
                             control_step=control))
        fuel -= energy * SFC
    boundaries.append(NS(stocks=((SOC, Fraction(end_soc)), (FUEL, fuel)), discrete_for_step=(), control_step=None))
    return NS(boundaries=boundaries)


def _measure(end_soc: int = 45, cold=Fraction(0)):
    steps = [_step("RUNNING", Fraction(30), 50, 30),  # loaded 30 kW
             _step("RUNNING", Fraction(0), 50, 5),  # idle RUNNING at 0
             _step("STARTING", Fraction(0), 48, 5, cold_unserved=cold),
             _step("STOPPED", Fraction(0), 46, 5, res_unserved=Fraction(1))]
    return measure_night(_series(steps, end_soc), lo=0, hi=4, info_hi=4)


def test_litres_follow_the_four_step_rule():
    m = _measure()
    expected = Fraction(30 * 5, 60) * Fraction(355, 1000) + Fraction(5, 60) * Fraction(49, 10)
    assert m["night_litres"] == expected
    assert m["loaded_litres"] == Fraction(30 * 5, 60) * Fraction(355, 1000)
    assert m["idle_litres"] == Fraction(5, 60) * Fraction(49, 10)
    assert m["tank_drop_litres"] == m["loaded_litres"]  # the linear law has no idle fuel
    assert (m["running_minutes"], m["loaded_minutes"], m["idle_minutes"], m["starts"]) == (10, 5, 5, 1)
    assert m["generator_kwh"] == Fraction(5, 2)
    assert m["indicative_avoidable_minutes"] == 5  # only the idle step: 0 + 20 kW >= 1.1 x 5 kW at 50 %


def test_cold_store_unserved_sum_and_all_loads():
    m = _measure(cold=Fraction(1, 4))
    assert m["cold_store_unserved_kwh"] == Fraction(1, 4)
    assert m["all_loads_unserved_kwh"] == Fraction(5, 4)
    assert _measure()["cold_store_unserved_kwh"] == 0


def test_below_reserve_flag():
    assert _measure(end_soc=45)["below_reserve"] is False
    low = _measure(end_soc=29)
    assert low["below_reserve"] is True and low["battery_min_pct"] == 29
