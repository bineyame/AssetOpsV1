"""0K4a: `mini-grid` v8, the generator takes the load (spec §3, D-0K4.2 to D-0K4.4, D-0K4.20, D-0K4.22).

The kernel runs here; every expected value comes from this file's own reader of the trajectory (W2), never from the
pack's split or 0K4b's curve. Commit 1 held N9; commit 3 adds v8's tests (N1-N8, N10-N13).

The reader: step `i` is `[B[i], B[i+1])`; its SOC at the start is `B[i].stock`, its energies are
`B[i+1].interval_measurement` (kWh), its generator state `B[i].discrete_state_for_step`, and its notes are the
accepted flow set on `B[i].control_step`. All exact.
"""

from __future__ import annotations

import dataclasses
from fractions import Fraction as F
from functools import cache

from assetops_backend.runs.replay_study import BASELINE, start_state
from assetops_contracts.forward_replay import ForwardReplayRequest
from assetops_simulator.kernel.execute import execute
from assetops_simulator.packs.mini_grid import LINEAR_FUEL_NOTE

from execution_adapter import model_for
from forward_replay import HostForwardReplay
from kobo import set_property
from kobo_assumed import assumed_site
from kobo_season import base_run, observed_series, season_inputs, season_site
from trajectory_digest import trajectory_digest

#: The v7 8-day Kobo season digest, computed on `main` b96d5e978 with only `trajectory_digest.py` added (packet,
#: pre-flight). A change here is a change to v1-v7, which 0K4a must never make.
V7_SEASON_8_DIGEST = "8eb9c44c38f31a77a8faf6e7e9f90fd2c62112dbe0d01c6a3243b7dae783f280"


@cache
def _v7_season(days: int):
    run = base_run(days)
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    trajectory = execute(season_inputs(run, days), model_for(run))
    assert trajectory.outcome == "COMPLETED", trajectory.failure
    return trajectory


def test_n9_v7_is_untouched() -> None:
    """v1-v7 untouched (D-0K4.20): the v7 8-day season digest equals the pre-flight literal. A change here is a new
    model version, never an edit."""
    assert trajectory_digest(_v7_season(8)) == V7_SEASON_8_DIGEST


# --- v8 (commit 3) ----------------------------------------------------------------------------------------------

#: The v8 8-day Kobo season digest (`base_run(8, version=8, site_edit=site)`, `season_inputs(run, 8)`), printed in
#: the packet. A change here is a new model version, never an edit.
V8_SEASON_8_DIGEST = "d6add2a3a4ee4f802c2820a772717718c8ca381d0e02d1269d2ea68df5371f11"

#: The spec's sentence (§2.4 step 8), written by hand.
CURVE_FUEL_NOTE = (
    "fuel follows the generator's declared curve: the no-load rate over every starting or running minute plus the "
    "slope to the full-load consumption over accepted energy"
)
DIFFERED = "the demand or the sources across the step differed from the view at T"

SOC = "battery-state-of-charge@battery"
TANK = "fuel-tank-volume@fuel-tank"
GEN = "generator-state@generator"
GEN_OUT = "generator-output-power@generator"
BAT_AC = "battery-ac-power@battery-pcs"
PV_AC = "pv-ac-power@pv-inverter"
PV_AVAILABLE = "pv-available-power@pv-inverter"
LOADS = ("load-clinic", "load-mill", "load-res")
RES, CLINIC, MILL = "load-demand@load-res", "load-demand@load-clinic", "load-demand@load-mill"
STEP_H = F(5, 60)
RATED = F(40)  # the Kobo template's generator, kW
NO_LOAD_L_PER_MIN = F(33, 600)  # 3.3 L/h assumed (kobo_assumed), in L/min
SLOPE_L_PER_KWH = F(2175, 10000)  # 0.3 - 60 x (33/600) / 40, by hand
START_IN_EFFECT = F(35)  # min(start 35, reserve 30 + 5)
STOP = F(90)
DAY_1_0500 = 1440 + 300


def site(document) -> None:
    season_site(document)
    assumed_site(document)


def site_with(key: str, value, component: str):
    def edit(document) -> None:
        site(document)
        set_property(document, component, key, value)
    return edit


TAPER_100 = site_with("battery-charge-taper-start", 100, "battery")
SFC_009 = site_with("specific-fuel-consumption", 0.09, "generator")


def overcast_day_0(day: int) -> bool:
    return day == 0


@cache
def _run(days: int, version: int, site_edit):
    run = base_run(days, version=version, site_edit=site_edit)
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    return run


def _start_soc(inputs, soc):
    return dataclasses.replace(inputs, initial_values=tuple(
        dataclasses.replace(row, value=F(soc)) if row.address == SOC else row for row in inputs.initial_values))


def _windows(inputs, windows):
    """Force `(address, from, to, kW)` windows: each existing window at the address that overlaps is cut into its
    parts before and after, at its own value, and the new window added, so no two windows force one address."""
    templates, kept = {}, []
    for forcing in inputs.forcings:
        templates.setdefault(forcing.address, forcing)
        cuts = [(a, b) for address, a, b, _ in windows if address == forcing.address]
        pieces = [(forcing.offset_minutes, forcing.offset_minutes + forcing.duration_minutes)]
        for a, b in cuts:
            pieces = [p for lo, hi in pieces for p in ((lo, min(hi, a)), (max(lo, b), hi)) if p[1] > p[0]]
        if not cuts:
            kept.append(forcing)
            continue
        kept += [dataclasses.replace(forcing, event_id=f"{forcing.event_id}:cut:{lo}", offset_minutes=lo,
                                     duration_minutes=hi - lo) for lo, hi in pieces]
    kept += [dataclasses.replace(templates[address], event_id=f"test:{address}:{a}", parameter_id="test",
                                 value=F(kw), shape="WINDOW", offset_minutes=a, duration_minutes=b - a)
             for address, a, b, kw in windows]
    return dataclasses.replace(inputs, forcings=tuple(kept))


def _execute(run, inputs):
    trajectory = execute(inputs, model_for(run))
    assert trajectory.outcome == "COMPLETED", trajectory.failure
    B = trajectory.boundaries
    assert [b.offset_minutes for b in B] == [5 * i for i in range(len(B))]
    return trajectory


@cache
def n1_run(version: int = 8, stop=None):
    run = _run(2, version, site)
    return _execute(run, season_inputs(run, 2, overcast=overcast_day_0, site_stop_pct=stop))


@cache
def night_support(mill_from: int, res: int = 25, clinic: int = 10):
    """Start SOC 34; res 25 and clinic 10 kW over [60, 90), the mill 40 kW from `mill_from` to 90 (N4: 60; N13: 62).

    N13 reads "res 25 and clinic 10 kW all night" as the night's support window [60, 90), N4's SOC history (packet,
    mid-build question): forced over [0, 360) the battery charges at only 5 kW before 01:00 and reaches its reserve
    inside the window (01:20, battery AC 3019/1600 kWh), so N4's per-step figures cannot hold there."""
    run = _run(1, 8, site)
    windows = ((RES, 60, 90, res), (CLINIC, 60, 90, clinic), (MILL, mill_from, 90, 40))
    return _execute(run, _windows(_start_soc(season_inputs(run, 1), 34), windows))


@cache
def soc_80(version: int, site_edit):
    run = _run(1, version, site_edit)
    return _execute(run, _start_soc(season_inputs(run, 1), 80))


# The reader (W2).
def steps(trajectory):
    return range(len(trajectory.boundaries) - 1)


def soc(trajectory, i):
    return trajectory.boundaries[i].stock(SOC)


def energy(trajectory, i, address):
    return trajectory.boundaries[i + 1].interval_measurement(address)


def state(trajectory, i):
    return trajectory.boundaries[i].discrete_state_for_step(GEN)


def demand(trajectory, i):
    return sum((energy(trajectory, i, f"load-requested-power@{load}") for load in LOADS), F(0))


def served(trajectory, i):
    return sum((energy(trajectory, i, f"load-served-power@{load}") for load in LOADS), F(0))


def accepted(trajectory, i):
    return trajectory.boundaries[i].control_step.accepted


def limited(trajectory, i, address):
    return next(c.limited_by for c in accepted(trajectory, i).controls if c.address == address)


def night_1_start(trajectory) -> int:
    """The first STOPPED to STARTING step after noon of day 0."""
    return next(i for i in steps(trajectory) if trajectory.boundaries[i].offset_minutes >= 720 and i > 0
                and state(trajectory, i - 1) == "STOPPED" and state(trajectory, i) == "STARTING")


def night_1_stop(trajectory, start: int) -> int:
    return next(i for i in steps(trajectory) if i > start and state(trajectory, i) == "STOPPED")


def test_n1_started_at_35_the_charge_rises() -> None:
    t = n1_run()
    start = night_1_start(t)
    stop = night_1_stop(t, start)
    assert soc(t, start) <= 35
    assert state(t, start + 1) == "RUNNING"
    assert all(state(t, i) == "RUNNING" for i in range(start + 1, stop))
    for i in range(start + 1, stop):
        assert soc(t, i + 1) > soc(t, i) or soc(t, i + 1) == 100, (i, soc(t, i), soc(t, i + 1))


def test_n2_no_discharge_beside_the_generator() -> None:
    t = n1_run()
    checked = 0
    for i in steps(t):
        if state(t, i) == "RUNNING" and demand(t, i) <= energy(t, i, PV_AVAILABLE) + RATED * STEP_H:
            assert energy(t, i, BAT_AC) <= 0, (i, energy(t, i, BAT_AC))
            checked += 1
    assert checked > 0


def test_n3_the_dawn_after_an_overcast_day() -> None:
    v7, v8 = n1_run(7), n1_run(8)
    dawn = DAY_1_0500 // 5
    assert soc(v7, dawn) < 35  # (a) the fault, reproduced on v7
    start = night_1_start(v8)
    s0 = soc(v8, start + 1)
    assert all(soc(v8, k) >= s0 for k in range(start + 1, dawn + 1))  # (b)
    assert soc(v8, dawn) > soc(v7, dawn)  # (c)


def test_n4_generator_support_is_exact() -> None:
    t = night_support(60)
    for i in range(12, 18):
        assert state(t, i) == "RUNNING", i
        assert energy(t, i, GEN_OUT) == F(10, 3), i
        assert energy(t, i, BAT_AC) == F(5, 2), i
        assert demand(t, i) - served(t, i) == F(5, 12), i
    assert soc(t, 18) > 30


def _acceptance_kw(t, i):
    """The reader's own `C` (D-0K4.22 R4): the request, the tapered PCS limit and the headroom, in kW."""
    s = soc(t, i)
    D, A = demand(t, i) / STEP_H, energy(t, i, PV_AVAILABLE) / STEP_H
    taper = F(1) if s <= 95 else max(F(1, 20), (100 - s) / 5)
    stored = s * 200 / 100
    return min(A + RATED - D, 30 * taper, (200 - stored) / (F(95, 100) * STEP_H))


def n5_exact_steps(t):
    out = []
    for i in steps(t):
        if state(t, i) != "RUNNING":
            continue
        D, A, C = demand(t, i) / STEP_H, energy(t, i, PV_AVAILABLE) / STEP_H, _acceptance_kw(t, i)
        if D + C - A < 12 <= D + C:
            out.append(i)
    return out


def test_n5_the_minimum_load_is_held() -> None:
    t = n1_run(8, F(100))
    for i in steps(t):
        if state(t, i) == "RUNNING":
            noted = any("below minimum load" in n for n in limited(t, i, GEN))
            assert energy(t, i, GEN_OUT) >= 1 or noted, (i, energy(t, i, GEN_OUT))
    exact = n5_exact_steps(t)
    assert exact, "precondition: a step with D + C - A < 12 <= D + C"
    for i in exact:
        assert energy(t, i, GEN_OUT) == 1, (i, energy(t, i, GEN_OUT))
        assert energy(t, i, PV_AC) < energy(t, i, PV_AVAILABLE), i


def test_n6_a_stopped_day_is_v7s_without_taper() -> None:
    v7, v8 = soc_80(7, TAPER_100), soc_80(8, TAPER_100)
    assert len(v7.boundaries) == len(v8.boundaries)
    for i in steps(v8):
        for address in (PV_AC, BAT_AC) + tuple(f"load-served-power@{load}" for load in LOADS):
            assert energy(v8, i, address) == energy(v7, i, address), (i, address)
        assert soc(v8, i + 1) == soc(v7, i + 1), i
    for t in (v7, v8):
        assert t.boundaries[0].stock(TANK) == t.boundaries[-1].stock(TANK)
        assert all(state(t, i) == "STOPPED" for i in steps(t))


def test_n6b_the_taper_holds_on_solar_charging() -> None:
    t = soc_80(8, site)
    tapered = [i for i in steps(t) if soc(t, i) > 95 and energy(t, i, BAT_AC) < 0]
    assert tapered, "precondition: the SOC passes 95 while charging"
    at_cap = 0
    for i in tapered:
        cap = 30 * max(F(1, 20), (100 - soc(t, i)) / 5) * STEP_H
        assert -energy(t, i, BAT_AC) <= cap, (i, soc(t, i), energy(t, i, BAT_AC), cap)
        at_cap += -energy(t, i, BAT_AC) == cap
    assert at_cap >= 1


def _starts_and_stops(t, stop_in_effect):
    starts = stops = 0
    for i in steps(t):
        if i == 0:
            continue
        if state(t, i - 1) == "STOPPED" and state(t, i) == "STARTING":
            assert soc(t, i) <= START_IN_EFFECT, (i, soc(t, i))
            starts += 1
        if state(t, i - 1) == "RUNNING" and state(t, i) == "STOPPED":
            ran = 0
            while i - 1 - ran >= 0 and state(t, i - 1 - ran) == "RUNNING":
                ran += 1
            assert ran * 5 >= 30, (i, ran)
            assert soc(t, i) >= stop_in_effect, (i, soc(t, i))
            stops += 1
    return starts, stops


def test_n7_the_start_and_stop_rules_are_v5s() -> None:
    starts, stops = _starts_and_stops(n1_run(), STOP)
    assert starts >= 1 and stops >= 1
    starts, _ = _starts_and_stops(n1_run(8, F(100)), F(100))
    assert starts >= 1
    # A stop of 37 % is reached within two running steps of a start at 35, so here the minimum runtime is what holds
    # the generator on (in N1's and N5's runs the charge takes hours and the runtime never binds).
    starts, stops = _starts_and_stops(n1_run(8, F(37)), F(37))
    assert starts >= 1 and stops >= 1


def test_n8_the_tank_follows_the_curve() -> None:
    t = n1_run()
    on = sum(1 for i in steps(t) if state(t, i) in ("STARTING", "RUNNING"))
    kwh = sum((energy(t, i, GEN_OUT) for i in steps(t)), F(0))
    assert on > 0 and kwh > 0
    fall = t.boundaries[0].stock(TANK) - t.boundaries[-1].stock(TANK)
    assert fall == NO_LOAD_L_PER_MIN * 5 * on + SLOPE_L_PER_KWH * kwh
    for i in steps(t):
        notes = accepted(t, i).notes
        assert CURVE_FUEL_NOTE in notes and LINEAR_FUEL_NOTE not in notes, (i, notes)


def test_n10_a_missing_need_and_an_impossible_curve_are_refused() -> None:
    blocked = base_run(1, version=8)  # season_site only: no assumed rows
    assert blocked.execution_status == "BLOCKED"
    assert any("generator-no-load-fuel-rate" in f"{r.subject} {r.statement}" for r in blocked.blocking_reasons)
    run = _run(1, 8, SFC_009)
    trajectory = execute(season_inputs(run, 1), model_for(run))
    assert trajectory.outcome == "FAILED"
    assert trajectory.failure.kind == "PHYSICAL_RESOLUTION_FAILURE"
    assert trajectory.failure.subject == "generator-no-load-fuel-rate@generator"
    assert trajectory.failure.detail[0].startswith("SFC_BELOW_DIESEL_ENERGY"), trajectory.failure.detail


def test_n11_the_replay_port_takes_v8() -> None:
    t = n1_run()
    observed = observed_series(t, 576)
    projection = HostForwardReplay().forward_replay(
        _run(2, 8, site),
        ForwardReplayRequest(BASELINE, observed.pv_available_kw, observed.loads, start_state(observed)))
    assert len(projection.steps) == 576
    site_kwh = sum((energy(t, i, GEN_OUT) for i in range(576)), F(0))
    assert site_kwh > 0
    assert abs(projection.generator_kwh - site_kwh) <= site_kwh / 100, (projection.generator_kwh, site_kwh)


def test_n12_v8_is_pinned() -> None:
    """v8 pinned (D-0K4.20): a change here is a new model version, never an edit."""
    run = _run(8, 8, site)
    assert trajectory_digest(_execute(run, season_inputs(run, 8))) == V8_SEASON_8_DIGEST


def test_n13_the_reverse_mismatch_keeps_v7s_rule_with_its_note() -> None:
    t = night_support(62)
    i = 12  # [60, 65): the view at 60 saw 35 kW and asked for charge; 75 kW from 62
    assert state(t, i) == "RUNNING"
    assert demand(t, i) - served(t, i) == F(7, 4)
    assert energy(t, i, BAT_AC) <= 0
    assert DIFFERED in accepted(t, i).controls[0].limited_by  # the battery's control
    for i in range(13, 18):
        assert state(t, i) == "RUNNING", i
        assert energy(t, i, GEN_OUT) == F(10, 3), i
        assert energy(t, i, BAT_AC) == F(5, 2), i
        assert demand(t, i) - served(t, i) == F(5, 12), i


def test_n13b_the_reverse_mismatch_note_beside_another_limit() -> None:
    """N13 with the PCS charge limit also binding (res 5 kW from 60: the view asks 35 kW of charge, the PCS takes 30),
    so v7's end-of-step rule (which notes the mismatch only when nothing else limits) cannot supply the note: v8's own
    reverse-mismatch note must. From 62 the mill makes 45 kW > 40, and 5 kW over 3 minutes is unserved."""
    t = night_support(62, res=5, clinic=0)
    i = 12
    assert state(t, i) == "RUNNING"
    notes = accepted(t, i).controls[0].limited_by
    assert any(n.startswith("pcs-charge-limit") for n in notes), notes  # precondition: another limit binds
    assert DIFFERED in notes, notes
    assert demand(t, i) - served(t, i) == F(1, 4)
    assert energy(t, i, BAT_AC) == F(-1)  # 30 kW over [60, 62), none over [62, 65)
