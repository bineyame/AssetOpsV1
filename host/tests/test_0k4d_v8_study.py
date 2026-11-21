"""0K4d: the replay study on `mini-grid` v8 and season v2 (spec §3 V0-V6). No database.

The site is the v2 season run on v8 (`kobo_season.py`, `season_site_v2`); the study replays its published series
through `HostForwardReplay`. Every expected value comes from this file's own reader of the site trajectory and of the
projections, copied from 0K2's test (never imported) and sharing no code with `runs/replay_study.py` (W2): dawn by the
fixed offset `d x 1440 + 300` from the window start, local dates by `step // 288`, starts by their own loop. Each
kernel run is built once (`functools.cache`); replays go through one caching port.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction as F
from functools import cache
from pathlib import Path

import pytest

from assetops_backend.runs.replay_study import StudyFrame, replay_study
from assetops_contracts.forward_replay import ReplaySettings
from assetops_simulator.kernel.execute import execute

from execution_adapter import frozen_world_inputs, model_for
from forward_replay import HostForwardReplay
from kobo_season import (
    IRRADIANCE,
    TIMEZONE,
    base_run,
    observed_series,
    overcast_v1,
    season_inputs,
    season_site_v2,
)
from mto import MTO_ASSUMED_DERIVATION, mto_base_run, mto_site_v2

REPO = Path(__file__).resolve().parents[2]
SOC = "battery-state-of-charge@battery"
GEN = "generator-state@generator"
GEN_OUT = "generator-output-power@generator"
DAY = 288
DAYS = 8
N = DAYS * DAY
CAPACITY = F(200)
LIMIT = F(35)
DAWN_INDEX = 60  # 05:00 local from a local midnight
RATED = F(40)  # the Kobo template's generator, kW
SEP_DATES = [f"2026-09-{1 + d:02d}" for d in range(DAYS)]

#: D-0K4.27, literal: Kobo's four assumption strings, in order.
KOBO_ASSUMPTIONS = (
    "generator-no-load-fuel-rate 3.3 L/h (assumed, GENERIC_DEFAULT: the owner's value of 2026-11-07 for a 40 kW set; "
    "the generic rule of about 0.08 L/h per kW of rating gives 3.2)",
    "generator-minimum-load 30 % (assumed, GENERIC_DEFAULT: a typical diesel controller setting, until Kobo's "
    "controller settings)",
    "battery-charge-taper-start 95 % (assumed, GENERIC_DEFAULT: a lithium iron phosphate battery, until Kobo's "
    "battery sheet)",
    "specific-fuel-consumption 0.3 L/kWh (assumed, TEMPLATE: the Kobo template's value, read as consumption at rated "
    "output, until Kobo's fuel sheet)",
)
#: D-0K4.27, literal: Mto's four.
MTO_ASSUMPTIONS = (
    "generator-no-load-fuel-rate 2.4 L/h (assumed, GENERIC_DEFAULT: the generic rule of 0.08 L/h per kW of rating x "
    "30 kW; no owner value for Mto)",
    "generator-minimum-load 30 % (assumed, GENERIC_DEFAULT: a typical diesel controller setting, until Kobo's "
    "controller settings)",
    "battery-charge-taper-start 95 % (assumed, GENERIC_DEFAULT: a lithium iron phosphate battery, until Kobo's "
    "battery sheet)",
    "specific-fuel-consumption 0.33 L/kWh (declared, MANIFEST: Mto's physical line, read as consumption at rated "
    "output)",
)

#: The pre-flight (packet §0): `main`'s `tools/kobo_replay_study.py` at 0K4d's merge of `main` (ff87ecac9), before
#: either tool was edited, no model or season flag. `--days 8` is SAMPLE_TOO_SHORT (14 admissible days are needed for
#: any litre figure), so it has no case; `--days 14` gives each case's `avoided_l`, exact (Known Deviations).
#: Evidence: /opt/assetecon/evidence/0K4d/preflight/main-kobo-14d.txt and main-kobo-14d-study.json.
MAIN_AVOIDED_L_14 = {
    "stop-90-reserve-30": "0/1", "stop-90-reserve-25": "362043/16000", "stop-85-reserve-30": "237/40",
    "stop-85-reserve-25": "416043/16000", "stop-80-reserve-30": "747/40", "stop-80-reserve-25": "544443/16000",
    "stop-75-reserve-30": "1197/40", "stop-75-reserve-25": "720443/16000", "stop-70-reserve-30": "1637/40",
    "stop-70-reserve-25": "936443/16000", "stop-65-reserve-30": "2107/40", "stop-65-reserve-25": "1112443/16000",
    "stop-60-reserve-30": "2547/40", "stop-60-reserve-25": "1292443/16000",
}


def S(stop, reserve):
    return ReplaySettings(F(stop), F(reserve))


GRID = (S(90, 30), S(70, 30), S(90, 25))


def load_tool(name: str):
    path = REPO / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{name}_0k4d", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@cache
def kobo_tool():
    return load_tool("kobo_replay_study")


@cache
def mto_tool():
    return load_tool("mto_headroom_study")


# --- kernel runs, each once ----------------------------------------------------------------------------------------


@cache
def site():
    run = base_run(DAYS, version=8, site_edit=season_site_v2)
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    trajectory = execute(season_inputs(run, DAYS, season="v2"), model_for(run))
    assert trajectory.outcome == "COMPLETED", trajectory.failure
    return run, trajectory


@cache
def published():
    _, trajectory = site()
    return observed_series(trajectory, len(trajectory.boundaries) - 1)


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


@cache
def study():
    run = site()[0]
    frame = StudyFrame(timezone=TIMEZONE, battery_capacity_kwh=CAPACITY, min_litre_days=DAYS, min_dawn_days=DAYS,
                       assumptions=kobo_tool().assumption_lines(run))
    return replay_study(PORT, run, published(), frame, grid=GRID)


# --- this file's own reader (copied from 0K2's test, W2) -----------------------------------------------------------


def site_track(trajectory):
    B = trajectory.boundaries
    n = len(B) - 1
    return ([B[i].stock(SOC) for i in range(n)],
            [B[i + 1].interval_measurement(GEN_OUT) for i in range(n)],
            [B[i].discrete_state_for_step(GEN) for i in range(n)])


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


def my_dawn(p):
    return [(p.steps[d * DAY + DAWN_INDEX].soc_start_pct, p.steps[d * DAY + DAWN_INDEX].generator_state)
            for d in range(DAYS)]


def my_admission_measures(p, first):
    breaches = sum(1 for s in p.steps if s.soc_start_pct < p.reserve_soc_pct)
    marks = my_start_marks([s.generator_state for s in p.steps], first)
    per_day = [sum(marks[d * DAY:(d + 1) * DAY]) for d in range(DAYS)]
    full = [any(s.soc_start_pct >= 100 for s in p.steps[d * DAY:(d + 1) * DAY]) for d in range(DAYS)]
    full[-1] = full[-1] or p.soc_end_pct >= 100
    longest = gap = 0
    for flag in full:
        gap = 0 if flag else gap + 1
        longest = max(longest, gap)
    return breaches, max(per_day), tuple(SEP_DATES[d] for d in range(DAYS) if full[d]), longest


def transitions(states):
    return {i for i in range(1, len(states)) if states[i] != states[i - 1]}


def position(soc_a, kwh_a, st_a, soc_b, kwh_b, st_b):
    m = min(len(soc_a), len(soc_b))
    mae = sum((abs(soc_a[i] - soc_b[i]) for i in range(m)), F(0)) / m
    kwh = sum((abs(kwh_a[i] - kwh_b[i]) for i in range(m)), F(0)) / sum(kwh_b[:m], F(0))
    tb = transitions(st_b[:m])
    return mae, kwh, F(len(transitions(st_a[:m]) ^ tb), len(tb))


def within(measures) -> tuple[bool, bool, bool]:
    mae, kwh, moved = measures
    return mae <= F(1, 10), kwh <= F(1, 100), moved <= F(1, 10)


# --- V0 frozen needs and smoke (D-0K4.26: 0K4c built S7's document half only) ----------------------------------------


def test_v0_v8_freezes_the_assumed_needs_and_runs_the_v2_season() -> None:
    run = base_run(1, version=8, site_edit=season_site_v2)
    assert run.execution_status == "READY"
    values = {row.parameter_id: row.value for row in frozen_world_inputs(run).initial_values}
    assert values["model-need:generator-no-load-fuel-rate"] == F(11, 200)  # 3.3 L/h in L/min
    assert values["model-need:generator-minimum-load"] == 30
    assert values["model-need:battery-charge-taper-start"] == 95
    two = base_run(2, version=8, site_edit=season_site_v2)
    assert execute(season_inputs(two, 2, season="v2"), model_for(two)).outcome == "COMPLETED"


def test_v0_a_passed_overcast_overrides_the_season_calendar() -> None:
    run = base_run(4, version=8, site_edit=season_site_v2)

    def irradiance(inputs):
        return sorted((f.offset_minutes, f.duration_minutes, f.value) for f in inputs.forcings
                      if f.address == IRRADIANCE)

    own = irradiance(season_inputs(run, 4, season="v2"))  # v2's calendar: days 2 and 3 overcast
    passed = irradiance(season_inputs(run, 4, season="v2", overcast=overcast_v1))  # day 3 only
    v1 = irradiance(season_inputs(run, 4, season="v1"))
    assert passed != own, "precondition: the two calendars differ on day 2"
    assert passed == v1  # irradiance reads the passed calendar alone (the v2 load shape touches loads only)


# --- V1 calibrated -------------------------------------------------------------------------------------------------


def test_v1_the_v8_baseline_is_calibrated_and_follows_the_site() -> None:
    result = study()
    assert result.status == "CALIBRATED", result.calibration
    assert (result.input_class, result.evidence_class) == ("SIMULATED", "MODELLED")
    assert result.calibration.failed == ()
    p = result.projections[0]
    soc, kwh, states = site_track(site()[1])
    replayed = ([s.soc_start_pct for s in p.steps], [s.generator_kwh for s in p.steps],
                [s.generator_state for s in p.steps])
    measured = position(*replayed, soc, kwh, states)
    assert within(measured) == (True, True, True), measured
    shifted = position(soc[1:], kwh[1:], states[1:], soc[:-1], kwh[:-1], states[:-1])
    assert within(shifted) == (False, False, False), "precondition: the bounds see a one-step shift"


# --- V2 every measure equals the reader's ----------------------------------------------------------------------------


def test_v2_every_outcome_equals_the_reader() -> None:
    result = study()
    b = result.projections[0]
    first = published().generator_state[0]
    b_below = {SEP_DATES[d] for d, (soc, _) in enumerate(my_dawn(b)) if soc < LIMIT}
    b_marks, b_dis = my_start_marks([s.generator_state for s in b.steps], first), my_discharge(b)
    seen = {"starts": False, "full": False, "gap": False, "avoided": False}
    for outcome, p in zip((result.baseline, *result.cases), result.projections, strict=True):
        assert outcome.case_id == p.case_id
        states = [s.generator_state for s in p.steps]
        fuel = p.steps[0].fuel_start_l - p.fuel_end_l
        assert outcome.fuel_l == fuel
        assert outcome.avoided_l == (b.steps[0].fuel_start_l - b.fuel_end_l) - fuel
        assert [(m.month, m.days, m.value) for m in outcome.avoided_l_by_month] == [
            ("2026-09", DAYS, sum((x - y for x, y in zip(my_burns(b), my_burns(p))), F(0)))]
        marks = my_start_marks(states, first)
        assert outcome.starts == sum(marks) == p.starts
        assert outcome.added_starts == sum(marks) - sum(b_marks)
        assert outcome.running_steps == sum(1 for s in states if s == "RUNNING")
        assert outcome.generator_kwh == sum((s.generator_kwh for s in p.steps), F(0))
        assert outcome.unserved_kwh == sum((s.unserved_kwh for s in p.steps), F(0))
        dis = my_discharge(p)
        assert outcome.throughput_kwh == sum(dis, F(0))
        assert outcome.added_throughput_kwh == sum(dis, F(0)) - sum(b_dis, F(0))
        assert outcome.min_soc_pct == min([s.soc_start_pct for s in p.steps] + [p.soc_end_pct])
        dawn = my_dawn(p)
        assert [(r.local_date, r.soc_pct, r.generator_state) for r in outcome.dawn] == [
            (SEP_DATES[d], soc, state) for d, (soc, state) in enumerate(dawn)]
        below = {SEP_DATES[d] for d, (soc, _) in enumerate(dawn) if soc < LIMIT}
        assert outcome.dawn_days_below == len(below)
        assert outcome.worst_dawn_soc_pct == min(soc for soc, _ in dawn)
        assert outcome.new_dawn_days_below == tuple(sorted(below - b_below))
        assert outcome.cleared_dawn_days_below == tuple(sorted(b_below - below))
        assert outcome.clipped_steps == len(p.clipped_offsets)
        assert (outcome.input_class, outcome.evidence_class) == ("SIMULATED", "MODELLED")
        # the four admission measures (D-0K4.16 as corrected by D-0K4.28)
        mine = my_admission_measures(p, first)
        assert (outcome.reserve_breach_steps, outcome.max_starts_in_a_day, outcome.full_charge_dates,
                outcome.longest_days_without_full_charge) == mine, outcome.case_id
        seen["starts"] |= mine[1] > 0
        seen["full"] |= bool(mine[2])
        seen["gap"] |= mine[3] > 0
        seen["avoided"] |= outcome.avoided_l != 0
    assert all(seen.values()), seen  # each measure is read on a non-empty set


# --- V3 the battery-beside-generator fault is gone ---------------------------------------------------------------------


def test_v3_soc_never_falls_while_the_generator_covers_the_demand() -> None:
    result = study()
    p = result.projections[0]
    observed = published()
    soc = [s.soc_start_pct for s in p.steps] + [p.soc_end_pct]
    checked = 0
    for i, step in enumerate(p.steps):
        if step.generator_state != "RUNNING" or soc[i] >= 100:
            continue
        demand = sum((load.kw[i] for load in observed.loads), F(0))
        if demand <= (observed.pv_available_kw[i] or 0) + RATED:
            checked += 1
            assert soc[i + 1] >= soc[i], (i, soc[i], soc[i + 1])
    assert checked > 0, "precondition: some RUNNING step is checked"


# --- V4 assumptions --------------------------------------------------------------------------------------------------


def test_v4_every_result_names_its_assumptions(monkeypatch) -> None:
    assert study().assumptions == KOBO_ASSUMPTIONS
    mto_run = mto_base_run(1, version=8, site=mto_site_v2)
    assert mto_run.execution_status == "READY"
    assert mto_tool().assumption_lines(mto_run) == MTO_ASSUMPTIONS
    monkeypatch.delitem(MTO_ASSUMED_DERIVATION, "generator-no-load-fuel-rate")
    with pytest.raises(KeyError):
        mto_tool().assumption_lines(mto_run)
    import kobo_assumed

    monkeypatch.delitem(kobo_assumed.ASSUMED_DERIVATION, "battery-charge-taper-start")
    with pytest.raises(KeyError):
        kobo_tool().assumption_lines(site()[0])


# --- V5 the tools are reproducible -------------------------------------------------------------------------------------


def test_v5_the_kobo_tool_with_no_flag_is_main_s(tmp_path, capsys, monkeypatch) -> None:
    assert MAIN_AVOIDED_L_14, "precondition: the pre-flight literals are recorded"
    out8 = tmp_path / "8" / "study.json"
    assert kobo_tool().main(["--days", "8", "--out", str(out8)]) == 0
    doc8 = json.loads(out8.read_text(encoding="utf-8"))
    assert (doc8["status"], doc8["cases"], doc8["model"], doc8["season"]) == (
        "SAMPLE_TOO_SHORT", [], "mini-grid/7", "v1")
    # each case is its own replay of the same series, so three of the fourteen stand for the grid (the full grid at
    # 14 days is about 3 minutes; these three about 1); the grid is the tool's, narrowed, never another frame
    monkeypatch.setattr(kobo_tool(), "KOBO_GRID", GRID)
    out = tmp_path / "14" / "study.json"
    assert kobo_tool().main(["--days", "14", "--out", str(out)]) == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert (doc["status"], doc["model"], doc["season"]) == ("CALIBRATED", "mini-grid/7", "v1")
    got = {c["case_id"]: c["avoided_l"]["exact"] for c in doc["cases"]}
    assert len(got) == 3 and got == {key: MAIN_AVOIDED_L_14[key] for key in got}
    printed = [line for line in capsys.readouterr().out.splitlines() if line]
    assert printed and all(line.startswith(
        "input_class=SIMULATED evidence_class=MODELLED model=mini-grid/7 season=v1 ") for line in printed)


# --- V6 a mixed pair is refused --------------------------------------------------------------------------------------


@pytest.mark.parametrize("tool", ["kobo", "mto"])
@pytest.mark.parametrize("version,season", [("8", "v1"), ("7", "v2")])
def test_v6_a_mixed_model_and_season_pair_is_refused(tool, version, season, tmp_path, capsys) -> None:
    module = kobo_tool() if tool == "kobo" else mto_tool()
    out = tmp_path / "study.json"
    code = module.main(["--days", "2", "--model-version", version, "--season", season, "--out", str(out)])
    assert code == 2
    assert f"STUDY_FLAGS_INVALID model={version} season={season}" in capsys.readouterr().err
    assert not out.exists()
