"""0K2: the replay study on the kernel, over the declared simulated Kobo season (spec §4 T1-T13). No database.

The site is the season run continuously on the kernel (`kobo_season.py`); the study replays its published series
through `HostForwardReplay`. Every expected value comes from this file's own reader of the site trajectory and of the
projections, which shares no code with `runs/replay_study.py` (W2): dawn by the fixed offset `d x 1440 + 300` from the
window start, months by offset, starts and throughput by their own loops. Each kernel run is built once
(`functools.cache`, D-0K2.28); replays go through one caching port, so a request is executed once however many
studies ask for it, and a recording wrapper in front of it counts the calls each study makes.
"""

from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from functools import cache
from pathlib import Path

import pytest

from assetops_backend.runs.replay_study import (
    CALIBRATION_KWH,
    CALIBRATION_SOC_MAE,
    CALIBRATION_STARTS,
    MIN_DAWN_DAYS,
    MIN_LITRE_DAYS,
    RESERVE_GRID,
    STOP_GRID,
    StudyFrame,
    StudyRefused,
    replay_study,
)
from assetops_contracts.forward_replay import ForwardReplayRefused, ReplaySettings
from assetops_simulator.kernel.execute import execute

from execution_adapter import frozen_world_inputs, model_for
from forward_replay import HostForwardReplay
from kobo_season import (
    LATE_WINDOWS,
    SEASON_START,
    TIMEZONE,
    base_run,
    observed_series,
    overcast_v1,
    season_inputs,
)

REPO = Path(__file__).resolve().parents[2]
SOC = "battery-state-of-charge@battery"
TANK = "fuel-tank-volume@fuel-tank"
GEN = "generator-state@generator"
PV = "pv-available-power@pv-inverter"
GEN_OUT = "generator-output-power@generator"
LOADS = ("load-res", "load-mill", "load-clinic")  # the publication's order: reverse sorted
HOURS = F(5, 60)
DAY = 288
N8 = 8 * DAY
CAPACITY = F(200)
LIMIT = F(35)
DAWN_INDEX = 60  # offset d x 1440 + 300 from a local midnight: 05:00 local
OCT_START = "2026-09-26T21:00:00Z"  # 27 Sep 00:00 local


def S(stop, reserve):
    return ReplaySettings(F(stop), F(reserve))


GRID = (S(90, 30), S(70, 30), S(90, 25))


def frame(**overrides) -> StudyFrame:
    return StudyFrame(timezone=TIMEZONE, battery_capacity_kwh=CAPACITY, **overrides)


# --- kernel runs, each once -------------------------------------------------------------------------------------


@cache
def site(label: str):
    """(run, trajectory) of a site season."""
    days, start, kwargs = {
        "8": (8, SEASON_START, {}),
        "14-stop-70": (14, SEASON_START, {"site_stop_pct": F(70)}),
        "8-tank-50": (8, SEASON_START, {"start_fuel_l": F(50)}),
        "oct": (8, OCT_START, {}),
    }[label]
    run = base_run(days, start=start)
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    trajectory = execute(season_inputs(run, days, **kwargs), model_for(run))
    assert trajectory.outcome == "COMPLETED", trajectory.failure
    return run, trajectory


@cache
def published(label: str):
    run, trajectory = site(label)
    start = OCT_START if label == "oct" else SEASON_START
    return observed_series(trajectory, len(trajectory.boundaries) - 1, start=start)


class CachingPort:
    def __init__(self) -> None:
        self.inner = HostForwardReplay()
        self.done: dict = {}

    def forward_replay(self, run, request):
        key = (id(run), request)
        if key not in self.done:
            self.done[key] = self.inner.forward_replay(run, request)
        return self.done[key]


PORT = CachingPort()


class Recorder:
    def __init__(self, port=PORT) -> None:
        self.port = port
        self.requests = []

    def forward_replay(self, run, request):
        self.requests.append(request)
        return self.port.forward_replay(run, request)


@cache
def study8(min_dawn_days: int = 8):
    recorder = Recorder()
    result = replay_study(recorder, site("8")[0], published("8"), frame(min_litre_days=8, min_dawn_days=min_dawn_days),
                          grid=GRID)
    return result, recorder


# --- this file's own reader ----------------------------------------------------------------------------------------


def q(value: F, quantum: F) -> F:
    return round(value / quantum) * quantum


def site_track(trajectory):
    """S: exact SOC at each step start, generator kWh in each step, generator state for each step."""
    B = trajectory.boundaries
    n = len(B) - 1
    return ([B[i].stock(SOC) for i in range(n)],
            [B[i + 1].interval_measurement(GEN_OUT) for i in range(n)],
            [B[i].discrete_state_for_step(GEN) for i in range(n)])


def my_starts(states, before):
    count, previous = 0, before
    for state in states:
        if previous == "STOPPED" and state in ("STARTING", "RUNNING"):
            count += 1
        previous = state
    return count


def my_start_marks(states, before):
    marks, previous = [], before
    for state in states:
        marks.append(int(previous == "STOPPED" and state in ("STARTING", "RUNNING")))
        previous = state
    return marks


def my_burns(p):
    fuel = [s.fuel_start_l for s in p.steps] + [p.fuel_end_l]
    return [fuel[i] - fuel[i + 1] for i in range(len(p.steps))]


def my_discharge(p):
    soc = [s.soc_start_pct for s in p.steps] + [p.soc_end_pct]
    out = []
    for i in range(len(p.steps)):
        drop = soc[i] - soc[i + 1]
        out.append(drop * CAPACITY / 100 if drop > 0 else F(0))
    return out


def my_dawn(p, days):
    return [(p.steps[d * DAY + DAWN_INDEX].soc_start_pct, p.steps[d * DAY + DAWN_INDEX].generator_state)
            for d in range(days)]


def dates(start_day: int, month: str, days: int):
    return [f"{month}-{start_day + d:02d}" for d in range(days)]


SEP_DATES = dates(1, "2026-09", 8)


def transitions(states):
    return {i for i in range(1, len(states)) if states[i] != states[i - 1]}


def position(soc_a, kwh_a, st_a, soc_b, kwh_b, st_b):
    """(SOC MAE, kWh |difference| share of b's total, transition differences share of b's): a against b."""
    m = min(len(soc_a), len(soc_b))
    mae = sum((abs(soc_a[i] - soc_b[i]) for i in range(m)), F(0)) / m
    kwh = sum((abs(kwh_a[i] - kwh_b[i]) for i in range(m)), F(0)) / sum(kwh_b[:m], F(0))
    tb = transitions(st_b[:m])
    moved = len(transitions(st_a[:m]) ^ tb)
    return mae, kwh, F(moved, len(tb))


def within(measures) -> tuple[bool, bool, bool]:
    mae, kwh, moved = measures
    return mae <= F(1, 10), kwh <= F(1, 100), moved <= F(1, 10)


# --- T1 calibrated -------------------------------------------------------------------------------------------------


def test_t1_the_baseline_calibrates_against_the_reader() -> None:
    result, recorder = study8()
    observed = published("8")
    _, trajectory = site("8")
    assert result.status == "CALIBRATED"
    soc, kwh, states = site_track(trajectory)
    # quantization is live: the published series is not the kernel's exact values
    assert any(observed.soc_pct[i] != soc[i] for i in range(N8)) or any(
        observed.generator_kwh[i] != kwh[i] for i in range(N8))
    base = result.projections[0]
    cal = result.calibration
    pub_kwh = [q(kwh[i], F(1, 1000)) for i in range(N8)]
    pub_soc = [q(soc[i], F(1, 10)) for i in range(N8)]
    assert cal.admissible_days == tuple(SEP_DATES)  # every day admissible, clipped days kept
    assert cal.generator_kwh_site == sum(pub_kwh, F(0))
    assert cal.generator_kwh_replayed == sum((s.generator_kwh for s in base.steps), F(0))
    assert cal.starts_site == my_starts(states, states[0])
    assert cal.starts_replayed == my_starts([s.generator_state for s in base.steps], states[0])
    assert cal.soc_mae_points == sum((abs(base.steps[i].soc_start_pct - pub_soc[i]) for i in range(N8)), F(0)) / N8
    assert cal.failed == ()
    assert result.clipped_days, "precondition: some step is clipped"
    B0 = trajectory.boundaries[0]
    start = recorder.requests[0].start
    assert (start.soc_pct, start.generator_state, start.fuel_l) == (
        q(B0.stock(SOC), F(1, 10)), B0.discrete_state_for_step(GEN), q(B0.stock(TANK), F(1, 10)))


# --- T2 anchor ------------------------------------------------------------------------------------------------------


def test_t2_the_90_30_setting_is_the_baseline() -> None:
    result, _ = study8()
    base, anchor = result.projections[0], result.projections[1]
    assert anchor.case_id == "stop-90-reserve-30" and base.case_id == "baseline"
    assert anchor.steps == base.steps
    case = result.cases[0]
    assert case.case_id == "stop-90-reserve-30" and case.avoided_l == 0
    assert (case.stop_source, case.reserve_source) == ("SETTING", "SETTING")
    assert (result.baseline.stop_source, result.baseline.reserve_source) == ("BASELINE", "BASELINE")


# --- T3 outcomes ------------------------------------------------------------------------------------------------------


def test_t3_every_outcome_equals_the_reader() -> None:
    result, _ = study8()
    b = result.projections[0]
    first = published("8").generator_state[0]
    assert first == "STOPPED" and b.steps[0].generator_state == "STOPPED"
    b_below = {SEP_DATES[d] for d, (soc, _) in enumerate(my_dawn(b, 8)) if soc < LIMIT}
    b_marks, b_dis = my_start_marks([s.generator_state for s in b.steps], first), my_discharge(b)
    seen_below = seen_above = False
    for outcome, p in zip((result.baseline, *result.cases), result.projections, strict=True):
        assert outcome.case_id == p.case_id
        states = [s.generator_state for s in p.steps]
        fuel = p.steps[0].fuel_start_l - p.fuel_end_l
        assert outcome.fuel_l == fuel
        assert outcome.avoided_l == (b.steps[0].fuel_start_l - b.fuel_end_l) - fuel
        assert [(m.month, m.days, m.value) for m in outcome.avoided_l_by_month] == [
            ("2026-09", 8, sum((x - y for x, y in zip(my_burns(b), my_burns(p))), F(0)))]
        assert sum((m.value for m in outcome.avoided_l_by_month), F(0)) == outcome.avoided_l
        marks = my_start_marks(states, first)
        assert outcome.starts == my_starts(states, first) == p.starts
        assert outcome.added_starts == sum(marks) - sum(b_marks)
        assert [(m.month, m.value) for m in outcome.added_starts_by_month] == [("2026-09", outcome.added_starts)]
        assert outcome.running_steps == sum(1 for s in states if s == "RUNNING")
        assert outcome.added_running_steps == outcome.running_steps - sum(
            1 for s in b.steps if s.generator_state == "RUNNING")
        assert outcome.generator_kwh == sum((s.generator_kwh for s in p.steps), F(0))
        assert outcome.unserved_kwh == sum((s.unserved_kwh for s in p.steps), F(0))
        dis = my_discharge(p)
        assert outcome.throughput_kwh == sum(dis, F(0))
        assert outcome.added_throughput_kwh == sum(dis, F(0)) - sum(b_dis, F(0))
        assert [(m.month, m.value) for m in outcome.added_throughput_kwh_by_month] == [
            ("2026-09", outcome.added_throughput_kwh)]
        assert outcome.min_soc_pct == min([s.soc_start_pct for s in p.steps] + [p.soc_end_pct])
        dawn = my_dawn(p, 8)
        assert [(r.local_date, r.soc_pct, r.generator_state) for r in outcome.dawn] == [
            (SEP_DATES[d], soc, state) for d, (soc, state) in enumerate(dawn)]
        below = {SEP_DATES[d] for d, (soc, _) in enumerate(dawn) if soc < LIMIT}
        assert outcome.dawn_days_below == len(below)
        assert outcome.worst_dawn_soc_pct == min(soc for soc, _ in dawn)
        assert outcome.dawn_verdict == ("FAIL" if below else "PASS")
        assert outcome.new_dawn_days_below == tuple(sorted(below - b_below))
        assert outcome.cleared_dawn_days_below == tuple(sorted(b_below - below))
        assert outcome.clipped_steps == len(p.clipped_offsets)
        assert (outcome.input_class, outcome.evidence_class) == ("SIMULATED", "MODELLED")
        seen_below |= bool(below)
        seen_above |= any(soc >= LIMIT for soc, _ in dawn)
    assert seen_below and seen_above, "precondition: the bound both holds and fails"
    assert next(c for c in result.cases if c.case_id == "stop-70-reserve-30").avoided_l != 0


# --- T4 not calibrated (14 days) ------------------------------------------------------------------------------------


def test_t4_a_site_stopping_at_70_fails_on_generator_energy() -> None:
    recorder = Recorder()
    run, _ = site("14-stop-70")
    result = replay_study(recorder, run, published("14-stop-70"), frame(min_litre_days=14))
    assert result.status == "NOT_CALIBRATED"
    assert result.calibration.failed == ("generator_kwh",)
    assert (result.cases, result.baseline, len(result.projections), len(recorder.requests)) == ((), None, 1, 1)


# --- T5 short sample --------------------------------------------------------------------------------------------------


def test_t5_a_short_sample_is_never_replayed() -> None:
    recorder = Recorder()
    result = replay_study(recorder, site("8")[0], published("8"), frame(min_litre_days=14))
    assert result.status == "SAMPLE_TOO_SHORT" and recorder.requests == []


# --- T6 verdict --------------------------------------------------------------------------------------------------------


def test_t6_a_verdict_needs_61_days() -> None:
    unclaimed, _ = study8(MIN_DAWN_DAYS)
    assert {o.dawn_verdict for o in (unclaimed.baseline, *unclaimed.cases)} == {"NOT_CLAIMED"}
    claimed, _ = study8()
    for o in (claimed.baseline, *claimed.cases):
        assert o.dawn_verdict == ("FAIL" if o.dawn_days_below > 0 else "PASS")
    assert len(claimed.baseline.dawn) == 8


# --- T7 whole window ---------------------------------------------------------------------------------------------------


def test_t7_every_replay_is_one_whole_window_call() -> None:
    _, recorder = study8()
    assert len(recorder.requests) == 1 + len(GRID)
    assert all(len(r.pv_available_kw) == N8 for r in recorder.requests)


# --- T8 pins -------------------------------------------------------------------------------------------------------------


def test_t8_pins() -> None:
    assert STOP_GRID == tuple(F(s) for s in (90, 85, 80, 75, 70, 65, 60))
    assert RESERVE_GRID == (F(30), F(25))
    assert (CALIBRATION_KWH, CALIBRATION_STARTS, CALIBRATION_SOC_MAE) == (F(5, 100), F(10, 100), F(5))
    assert (MIN_LITRE_DAYS, MIN_DAWN_DAYS) == (14, 61)
    path = REPO / "tools" / "derive_steady_scenarios.py"
    spec = importlib.util.spec_from_file_location("derive_steady_scenarios_pin", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    late = module.NIGHT_WINDOWS["late"]

    def minute(text: str) -> int:
        hours, minutes = text.split(":")
        return int(hours) * 60 + int(minutes)

    mapped = tuple((minute(row[0]), row[3], {"load-res": row[4], "load-clinic": row[6]}) for row in late)
    assert len(mapped) == len(LATE_WINDOWS)
    for got, want in zip(LATE_WINDOWS, mapped, strict=True):
        assert got == want
    assert [row[0] for row in LATE_WINDOWS] == [1200, 1320]
    assert sum(1 for d in range(61) if overcast_v1(d)) == 15
    capacity = [v.value for v in frozen_world_inputs(site("8")[0]).initial_values
                if v.state_key == "battery-energy-capacity"]
    assert capacity == [CAPACITY]


# --- T9 tank ----------------------------------------------------------------------------------------------------------


def test_t9_a_tank_that_empties_is_refused() -> None:
    run, _ = site("8-tank-50")
    observed = published("8-tank-50")
    assert observed.start_fuel_l == F(50)
    with pytest.raises(StudyRefused) as caught:
        replay_study(Recorder(), run, observed, frame(min_litre_days=8), grid=GRID)
    assert caught.value.code == "TANK_BOUND_MET"


# --- T10 gap ------------------------------------------------------------------------------------------------------------


def test_t10_an_input_gap_is_the_port_refusal() -> None:
    import dataclasses

    observed = published("8")
    pv = list(observed.pv_available_kw)
    pv[600 // 5] = None
    with pytest.raises(ForwardReplayRefused) as caught:
        replay_study(Recorder(), site("8")[0], dataclasses.replace(observed, pv_available_kw=tuple(pv)),
                     frame(min_litre_days=8), grid=GRID)
    assert (caught.value.code, caught.value.subject) == ("INPUT_GAP", "pv@600")


# --- T11 position against the site --------------------------------------------------------------------------------------


def test_t11_the_baseline_follows_the_site_step_by_step() -> None:
    result, _ = study8()
    p = result.projections[0]
    soc, kwh, states = site_track(site("8")[1])
    # precondition: the bounds see a one-step shift, each way
    for shift in (1, -1):
        if shift == 1:
            shifted = (soc[1:], kwh[1:], states[1:], soc[:-1], kwh[:-1], states[:-1])
        else:
            shifted = (soc[:-1], kwh[:-1], states[:-1], soc[1:], kwh[1:], states[1:])
        assert within(position(*shifted)) == (False, False, False), (shift, position(*shifted))
    replayed = ([s.soc_start_pct for s in p.steps], [s.generator_kwh for s in p.steps],
                [s.generator_state for s in p.steps])
    measured = position(*replayed, soc, kwh, states)
    assert within(measured) == (True, True, True), measured
    site_below = {SEP_DATES[d] for d in range(8) if soc[d * DAY + DAWN_INDEX] < LIMIT}
    replay_below = {SEP_DATES[d] for d in range(8) if replayed[0][d * DAY + DAWN_INDEX] < LIMIT}
    assert site_below == replay_below


# --- T12 publication pins -----------------------------------------------------------------------------------------------


def test_t12_every_published_value_is_read_at_its_index() -> None:
    observed = published("8")
    B = site("8")[1].boundaries
    kw, kwh, pct = F(1, 100), F(1, 1000), F(1, 10)
    assert observed.interval_start == SEASON_START and observed.input_class == "SIMULATED"
    assert [load.load_id for load in observed.loads] == list(LOADS)
    for i in range(N8):
        assert observed.pv_available_kw[i] == q(B[i + 1].interval_measurement(PV) / HOURS, kw), i
        for load in observed.loads:
            assert load.kw[i] == q(B[i + 1].interval_measurement(f"load-requested-power@{load.load_id}") / HOURS,
                                   kw), (i, load.load_id)
        assert observed.generator_kwh[i] == q(B[i + 1].interval_measurement(GEN_OUT), kwh), i
        assert observed.generator_state[i] == B[i].discrete_state_for_step(GEN), i
        assert observed.soc_pct[i] == q(B[i].stock(SOC), pct), i
    assert observed.start_fuel_l == q(B[0].stock(TANK), F(1, 10))


# --- T13 month boundary ----------------------------------------------------------------------------------------------------


def test_t13_a_window_across_1_october() -> None:
    run, _ = site("oct")
    result = replay_study(Recorder(), run, published("oct"), frame(min_litre_days=8), grid=(S(70, 30),))
    assert result.status == "CALIBRATED"
    b, p = result.projections
    case = result.cases[0]
    split = 4 * DAY
    first = published("oct").generator_state[0]
    diffs = [x - y for x, y in zip(my_burns(b), my_burns(p))]
    marks = [x - y for x, y in zip(my_start_marks([s.generator_state for s in p.steps], first),
                                   my_start_marks([s.generator_state for s in b.steps], first))]
    through = [x - y for x, y in zip(my_discharge(p), my_discharge(b))]

    def halves(values):
        return [("2026-09", 4, sum(values[:split], F(0))), ("2026-10", 4, sum(values[split:], F(0)))]

    assert [(m.month, m.days, m.value) for m in case.avoided_l_by_month] == halves(diffs)
    assert [(m.month, m.days, m.value) for m in case.added_starts_by_month] == halves(marks)
    assert [(m.month, m.days, m.value) for m in case.added_throughput_kwh_by_month] == halves(through)
    assert all(m.value != 0 for m in case.avoided_l_by_month), "precondition: both months avoid litres"
