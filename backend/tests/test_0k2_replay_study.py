"""0K2: the replay study against a stub port (spec §2, §4 B1-B13). No kernel, no database.

Every projection is scripted here from per-case values; the stub records every request, so the number, order and
shape of the port calls are asserted directly. Windows are 2 or 15 local days at 5 minutes in Africa/Addis_Ababa.
"""

from __future__ import annotations

import ast
import dataclasses
from datetime import time
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace

import pytest

from assetops_backend.runs import replay_study as rs
from assetops_backend.runs.replay_study import (
    KOBO_GRID,
    Calibration,
    CaseOutcome,
    MonthFigure,
    ObservedSeries,
    StudyFrame,
    StudyRefused,
    admissible_days,
    avoided_l_on,
    calibrate,
    count_starts,
    replay_study,
    start_steps,
    study_days,
    throughput_steps,
)
from assetops_contracts.forward_replay import (
    ForwardReplayProjection,
    ForwardReplayRefused,
    LoadSeries,
    ReplaySettings,
    ReplayStep,
)

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
STUDY = BACKEND / "assetops_backend" / "runs" / "replay_study.py"
TOOL = REPO / "tools" / "kobo_replay_study.py"
START = "2026-08-31T21:00:00Z"  # 1 Sep 00:00 local
LATE_SEP = "2026-09-23T21:00:00Z"  # 24 Sep 00:00 local
DAY = 288
RUN = SimpleNamespace(run_id="run-k")
FRAME = StudyFrame(timezone="Africa/Addis_Ababa", battery_capacity_kwh=F(200), min_litre_days=1, min_dawn_days=2)


def S(stop, reserve):
    return ReplaySettings(F(stop), F(reserve))


def series(days: int = 2, *, n: int | None = None, start: str = START, timestep: int = 5, kwh=None, states=None,
           soc=None, pv=None, input_class: str = "SIMULATED", fuel=F(1000)) -> ObservedSeries:
    n = days * DAY if n is None else n
    return ObservedSeries(
        interval_start=start, timestep_minutes=timestep,
        pv_available_kw=tuple(pv) if pv is not None else (F(1),) * n,
        loads=(LoadSeries("load-res", (F(2),) * n), LoadSeries("load-clinic", (F(1),) * n)),
        generator_kwh=tuple(kwh) if kwh is not None else (F(0),) * n,
        generator_state=tuple(states) if states is not None else ("STOPPED",) * n,
        soc_pct=tuple(soc) if soc is not None else (F(50),) * n,
        start_fuel_l=fuel, input_class=input_class,
    )


def proj(case_id: str, n: int, *, states=None, kwh=None, soc=None, fuel=None, fuel_end=None, soc_end=F(50),
         status="COMPLETED", start=START, timestep=5, stop=(F(90), "BASELINE"), reserve=(F(30), "BASELINE"),
         starts=0, clipped=()) -> ForwardReplayProjection:
    states = tuple(states) if states is not None else ("STOPPED",) * n
    kwh = tuple(kwh) if kwh is not None else (F(0),) * n
    soc = tuple(soc) if soc is not None else (F(50),) * n
    fuel = tuple(fuel) if fuel is not None else (F(1000),) * n
    if fuel_end is None:
        fuel_end = fuel[-1] if n else F(1000)
    done = status == "COMPLETED"
    steps = tuple(ReplayStep(5 * i, states[i], kwh[i], F(0), soc[i], fuel[i], 5 * i in clipped) for i in range(n))
    return ForwardReplayProjection(
        base_run_id="run-k", case_id=case_id, status=status, model_profile_id="mini-grid", model_profile_version=7,
        interval_start=start, timestep_minutes=timestep, stop_soc_pct=stop[0], stop_source=stop[1],
        reserve_soc_pct=reserve[0], reserve_source=reserve[1], steps=steps,
        soc_end_pct=soc_end if done else None, fuel_end_l=fuel_end if done else None,
        min_soc_pct=min(soc) if soc else F(0), generator_kwh=sum(kwh, F(0)), unserved_kwh=F(0), starts=starts,
        running_steps=sum(1 for s in states if s == "RUNNING"),
        fuel_burned_l=(fuel[0] - fuel_end) if done and n else None, clipped_offsets=tuple(clipped),
        replay_identity="x", failure_kind=None if done else "MODEL_FAILURE", failure_subject=None if done else "x")


def echo(observed: ObservedSeries, **overrides):
    """A projection equal to the published series (a calibrated baseline), with per-field overrides."""
    n = len(observed.pv_available_kw)
    values = dict(states=observed.generator_state, kwh=observed.generator_kwh, soc=observed.soc_pct)
    values.update(overrides)
    return lambda request: proj(request.case_id, n, **values)


class Stub:
    def __init__(self, scripts: dict):
        self.scripts = scripts
        self.requests = []

    def forward_replay(self, run, request):
        self.requests.append(request)
        made = self.scripts.get(request.case_id, self.scripts.get("*"))
        if isinstance(made, Exception):
            raise made
        return made(request) if callable(made) else made


def refused(code: str, subject: str, call):
    with pytest.raises(StudyRefused) as caught:
        call()
    assert (caught.value.code, caught.value.subject) == (code, subject)


# --- B1 thresholds -------------------------------------------------------------------------------------------------


def _cal(observed, **replayed):
    days = study_days(observed, FRAME)
    return calibrate(observed, echo(observed, **replayed)(SimpleNamespace(case_id="baseline")),
                     admissible_days(observed, days))


def test_b1_generator_energy_is_relative_to_the_site_side() -> None:
    n = 2 * DAY
    observed = series(kwh=[F(100)] + [F(0)] * (n - 1))
    for rep, ok in ((F(105), True), (F(105) + F(1, 1000), False), (F(95), True), (F(95) - F(1, 1000), False)):
        cal = _cal(observed, kwh=[rep] + [F(0)] * (n - 1))
        assert ("generator_kwh" not in cal.failed) is ok, rep
        assert (cal.generator_kwh_site, cal.generator_kwh_replayed) == (F(100), rep)


def _starts_states(n: int, count: int):
    states = ["STOPPED"] * n
    for k in range(count):
        states[10 + 4 * k] = "RUNNING"
    return states


def test_b1_starts_tolerance_and_zero() -> None:
    n = 2 * DAY
    observed = series(states=_starts_states(n, 10))
    for rep, ok in ((11, True), (12, False), (9, True), (8, False)):
        cal = _cal(observed, states=_starts_states(n, rep))
        assert ("starts" not in cal.failed) is ok, rep
        assert (cal.starts_site, cal.starts_replayed) == (10, rep)
    zero = series()
    assert _cal(zero).failed == ()
    assert _cal(zero, states=_starts_states(n, 1)).failed == ("starts",)


def test_b1_soc_mean_absolute_error() -> None:
    n = 2 * DAY
    observed = series()
    assert _cal(observed, soc=[F(55)] * n).failed == ()
    assert _cal(observed, soc=[F(45)] * n).soc_mae_points == F(5)
    assert _cal(observed, soc=[F(55) + F(1, 1000)] * n).failed == ("soc",)


def test_b1_failed_order_and_not_calibrated_stops() -> None:
    n = 2 * DAY
    observed = series(kwh=[F(100)] + [F(0)] * (n - 1), states=_starts_states(n, 10))
    stub = Stub({"baseline": echo(observed, kwh=[F(200)] + [F(0)] * (n - 1), states=_starts_states(n, 20),
                                  soc=[F(60)] * n)})
    result = replay_study(stub, RUN, observed, FRAME)
    assert result.status == "NOT_CALIBRATED"
    assert result.calibration.failed == ("generator_kwh", "starts", "soc")
    assert (result.baseline, result.cases, len(result.projections)) == (None, (), 1)
    assert [r.case_id for r in stub.requests] == ["baseline"]


# --- B2 admissibility ------------------------------------------------------------------------------------------------


def test_b2_a_gap_in_the_site_outputs_excludes_the_whole_day() -> None:
    n = 2 * DAY
    soc = [F(50)] * n
    soc[DAY + 7] = None
    observed = series(soc=soc)
    replayed = [F(50)] * DAY + [F(0)] * DAY  # 50 points off on day 2 only
    days = study_days(observed, FRAME)
    assert [d.local_date for d in admissible_days(observed, days)] == ["2026-09-01"]
    stub = Stub({"*": echo(observed, soc=replayed)})
    result = replay_study(stub, RUN, observed, FRAME, grid=(S(90, 30),))
    assert result.status == "CALIBRATED"
    assert result.calibration.admissible_days == ("2026-09-01",)
    assert result.calibration.soc_mae_points == 0


# --- B3 dawn is local ----------------------------------------------------------------------------------------------


def test_b3_dawn_is_the_local_0500_step_with_its_own_state() -> None:
    n = 2 * DAY
    soc = [F(40) + F(i, 1000) for i in range(n)]
    states = ["STOPPED"] * n
    states[60], states[61] = "RUNNING", "STARTING"
    states[DAY + 60], states[DAY + 61] = "STARTING", "RUNNING"
    observed = series(soc=soc, states=states)
    base_soc, case_soc = list(soc), list(soc)
    base_soc[60] = F(30)  # baseline below on day 1 only
    case_soc[DAY + 60] = F(31)  # the case below on day 2 only
    base_soc[61] = case_soc[61] = F(1)  # the step after dawn: never read
    stub = Stub({"baseline": echo(observed, soc=base_soc), "*": echo(observed, soc=case_soc)})
    result = replay_study(stub, RUN, observed, FRAME, grid=(S(80, 30),))
    assert result.status == "CALIBRATED"
    base, case = result.baseline, result.cases[0]
    assert [(r.local_date, r.soc_pct, r.generator_state) for r in base.dawn] == [
        ("2026-09-01", F(30), "RUNNING"), ("2026-09-02", soc[DAY + 60], "STARTING")]
    assert [(r.soc_pct, r.generator_state) for r in case.dawn] == [(soc[60], "RUNNING"), (F(31), "STARTING")]
    assert (base.dawn_days_below, base.worst_dawn_soc_pct, base.dawn_verdict) == (1, F(30), "FAIL")
    assert (case.dawn_days_below, case.worst_dawn_soc_pct, case.dawn_verdict) == (1, F(31), "FAIL")
    assert (case.new_dawn_days_below, case.cleared_dawn_days_below) == (("2026-09-02",), ("2026-09-01",))
    assert (base.new_dawn_days_below, base.cleared_dawn_days_below) == ((), ())
    longer = dataclasses.replace(FRAME, min_dawn_days=3)
    again = replay_study(Stub({"baseline": echo(observed, soc=base_soc), "*": echo(observed, soc=case_soc)}),
                         RUN, observed, longer, grid=(S(80, 30),))
    assert {o.dawn_verdict for o in (again.baseline, *again.cases)} == {"NOT_CLAIMED"}
    clear = replay_study(Stub({"*": echo(observed)}), RUN, observed, FRAME, grid=(S(80, 30),))
    assert (clear.cases[0].dawn_verdict, clear.cases[0].dawn_days_below) == ("PASS", 0)


# --- B4 months are local ---------------------------------------------------------------------------------------------


def _fuel_path(burns):
    fuel, level = [], F(1000)
    for b in burns:
        fuel.append(level)
        level -= b
    return fuel, level


def test_b4_the_first_three_utc_hours_count_in_september() -> None:
    n = 2 * DAY
    base_burn = [F(1, 10)] * 36 + [F(0)] * (n - 36)  # 21:00Z-24:00Z on 31 Aug only
    fuel, end = _fuel_path(base_burn)
    observed = series()
    stub = Stub({"baseline": echo(observed, fuel=fuel, fuel_end=end), "*": echo(observed)})
    result = replay_study(stub, RUN, observed, FRAME, grid=(S(80, 30),))
    case = result.cases[0]
    assert case.avoided_l == F(36, 10)
    assert case.avoided_l_by_month == (MonthFigure("2026-09", 2, F(36, 10)),)


def test_b4_a_window_across_a_month_end() -> None:
    n = 15 * DAY
    case_burn = [F(1, 100)] * n
    base_burn = [F(3, 100)] * n
    base_fuel, base_end = _fuel_path(base_burn)
    case_fuel, case_end = _fuel_path(case_burn)
    observed = series(15, start=LATE_SEP)
    stub = Stub({"baseline": echo(observed, fuel=base_fuel, fuel_end=base_end),
                 "*": lambda r: proj(r.case_id, n, states=observed.generator_state, kwh=observed.generator_kwh,
                                     soc=observed.soc_pct, fuel=case_fuel, fuel_end=case_end, start=LATE_SEP)})
    stub.scripts["baseline"] = lambda r: proj(r.case_id, n, states=observed.generator_state,
                                              kwh=observed.generator_kwh, soc=observed.soc_pct, fuel=base_fuel,
                                              fuel_end=base_end, start=LATE_SEP)
    result = replay_study(stub, RUN, observed, FRAME, grid=(S(80, 30),))
    case = result.cases[0]
    months = case.avoided_l_by_month
    assert [(m.month, m.days) for m in months] == [("2026-09", 7), ("2026-10", 8)]
    assert months[0].value == F(2, 100) * 7 * DAY and months[1].value == F(2, 100) * 8 * DAY
    assert sum((m.value for m in months), F(0)) == case.avoided_l > 0


# --- B5 throughput ---------------------------------------------------------------------------------------------------


def test_b5_throughput_counts_discharge_only() -> None:
    p = proj("baseline", 3, soc=[F(50), F(40), F(45)], soc_end=F(30))
    assert sum(throughput_steps(p, FRAME), F(0)) == F(50)


def test_b5_month_splits_sum_to_their_totals() -> None:
    n = 15 * DAY
    site_states = ["STOPPED"] * n
    site_states[200] = "RUNNING"  # the baseline starts once, in September
    observed = series(15, start=LATE_SEP, states=site_states)
    case_soc = [F(50) if i % 2 == 0 else F(49) for i in range(n)]  # a 1-point drop every other step
    case_states = list(observed.generator_state)
    for i in (100, 3000):  # one added start in each month
        case_states[i] = "RUNNING"

    base_soc = [F(50) if i % 4 else F(49) for i in range(n)]  # the baseline discharges too, less often

    def base(r):
        return proj(r.case_id, n, start=LATE_SEP, soc=base_soc, states=site_states)

    def case(r):
        return proj(r.case_id, n, start=LATE_SEP, soc=case_soc, states=case_states)

    result = replay_study(Stub({"baseline": base, "*": case}), RUN, observed, FRAME, grid=(S(80, 30),))
    out = result.cases[0]
    assert all(m.value != 0 for m in out.added_throughput_kwh_by_month)
    assert sum((m.value for m in out.added_throughput_kwh_by_month), F(0)) == out.added_throughput_kwh
    assert all(m.value != 0 for m in out.added_starts_by_month)
    assert sum((m.value for m in out.added_starts_by_month), F(0)) == out.added_starts == 2
    assert result.baseline.starts == 1 and result.baseline.throughput_kwh > 0
    assert out.throughput_kwh - result.baseline.throughput_kwh == out.added_throughput_kwh


# --- B6 starts --------------------------------------------------------------------------------------------------------


def test_b6_one_start_rule() -> None:
    assert count_starts(("STOPPED", "STARTING", "RUNNING", "RUNNING", "STOPPED", "RUNNING"), "STOPPED") == 2
    assert count_starts(("FAILED", "RUNNING"), "STOPPED") == 0
    assert count_starts(("STARTING", "RUNNING"), "STOPPED") == 1
    assert count_starts((None, "RUNNING"), "STOPPED") == 0
    assert start_steps(("STARTING", "RUNNING", "STOPPED", "RUNNING"), "STOPPED") == (1, 0, 0, 1)
    assert count_starts(("STOPPED", "RUNNING", "STOPPED", "RUNNING"), "STOPPED", frozenset({3})) == 1


def test_b6_a_case_reads_the_study_count_not_the_projection_count() -> None:
    n = 2 * DAY
    observed = series()
    states = ["STARTING"] + ["STOPPED"] * (n - 1)
    stub = Stub({"baseline": echo(observed), "*": lambda r: proj(r.case_id, n, states=states, starts=7)})
    result = replay_study(stub, RUN, observed, FRAME, grid=(S(80, 30),))
    assert result.cases[0].starts == 1 and result.cases[0].added_starts == 1


# --- B7 refusals and order --------------------------------------------------------------------------------------------


def test_b7_window_refusals() -> None:
    stub = Stub({"*": echo(series())})
    refused("STUDY_WINDOW_INVALID", "timestep", lambda: replay_study(stub, RUN, series(timestep=15), FRAME))
    refused("STUDY_WINDOW_INVALID", "start",
            lambda: replay_study(stub, RUN, series(start="2026-08-31T22:00:00Z"), FRAME))
    refused("STUDY_WINDOW_INVALID", "start", lambda: replay_study(stub, RUN, series(start="2026-08-31 21:00"), FRAME))
    refused("STUDY_WINDOW_INVALID", "day:2026-09-02", lambda: replay_study(stub, RUN, series(n=2 * DAY - 1), FRAME))
    refused("STUDY_WINDOW_INVALID", "day:2026-09-01", lambda: replay_study(stub, RUN, series(n=0), FRAME))
    assert stub.requests == []


def test_b7_alignment_start_and_sample() -> None:
    n = 2 * DAY
    stub = Stub({"*": echo(series())})
    refused("STUDY_SERIES_MISALIGNED", "soc_pct",
            lambda: replay_study(stub, RUN, series(soc=[F(50)] * (n - 1)), FRAME))
    refused("STUDY_SERIES_MISALIGNED", "generator_kwh",
            lambda: replay_study(stub, RUN, series(kwh=[F(0)] * (n + 1), soc=[F(50)] * (n - 1)), FRAME))
    soc = [None] + [F(50)] * (n - 1)
    refused("STUDY_START_UNKNOWN", "soc", lambda: replay_study(stub, RUN, series(soc=soc), FRAME))
    long_frame = dataclasses.replace(FRAME, min_litre_days=3)
    short = replay_study(stub, RUN, series(), long_frame)
    assert (short.status, short.calibration, short.baseline, short.cases, short.projections) == (
        "SAMPLE_TOO_SHORT", None, None, (), ())
    assert short.input_class == "SIMULATED" and short.evidence_class == "MODELLED"
    # step 2 precedes step 3: a misaligned short sample refuses
    refused("STUDY_SERIES_MISALIGNED", "soc_pct",
            lambda: replay_study(stub, RUN, series(soc=[F(50)] * (n - 1)), long_frame))
    assert stub.requests == []


def test_b7_grid_refusals_precede_every_port_call() -> None:
    stub = Stub({"*": echo(series())})
    refused("STUDY_GRID_INVALID", "grid:1",
            lambda: replay_study(stub, RUN, series(), FRAME, grid=(S(90, 30), ReplaySettings(F(141, 2), F(30)))))
    refused("STUDY_GRID_INVALID", "grid:2",
            lambda: replay_study(stub, RUN, series(), FRAME, grid=(S(70, 30), S(80, 30), S(70, 30))))
    assert stub.requests == []
    replay_study(stub, RUN, series(), FRAME, grid=(ReplaySettings(stop_soc_pct=F(70)),))
    assert [r.case_id for r in stub.requests] == ["baseline", "stop-70-reserve-site"]
    assert stub.requests[1].settings == ReplaySettings(stop_soc_pct=F(70))


# --- B8 propagation ------------------------------------------------------------------------------------------------


def test_b8_a_port_refusal_reaches_the_caller_unchanged() -> None:
    gap = ForwardReplayRefused("INPUT_GAP", "pv@50", "x")
    with pytest.raises(ForwardReplayRefused) as caught:
        replay_study(Stub({"*": gap}), RUN, series(), FRAME)
    assert caught.value is gap


def test_b8_failed_and_short_projections() -> None:
    n = 2 * DAY
    observed = series()
    failed = lambda r: proj(r.case_id, n, status="FAILED")  # noqa: E731
    refused("REPLAY_FAILED", "baseline", lambda: replay_study(Stub({"*": failed}), RUN, observed, FRAME))
    refused("REPLAY_FAILED", "stop-80-reserve-30",
            lambda: replay_study(Stub({"baseline": echo(observed), "stop-80-reserve-30": failed, "*": echo(observed)}),
                                 RUN, observed, FRAME, grid=(S(90, 30), S(80, 30))))
    short = lambda r: proj(r.case_id, n - 1)  # noqa: E731
    refused("STUDY_WINDOW_INVALID", "run", lambda: replay_study(Stub({"*": short}), RUN, observed, FRAME))
    shifted = lambda r: proj(r.case_id, n, start=LATE_SEP)  # noqa: E731
    refused("STUDY_WINDOW_INVALID", "run",
            lambda: replay_study(Stub({"baseline": echo(observed), "*": shifted}), RUN, observed, FRAME,
                                 grid=(S(80, 30),)))


# --- B9 tank ---------------------------------------------------------------------------------------------------------


def test_b9_a_tank_that_empties_is_refused() -> None:
    n = 2 * DAY
    observed = series()
    empty_step = [F(10)] * (n - 1) + [F(0)]
    refused("TANK_BOUND_MET", "stop-80-reserve-30",
            lambda: replay_study(Stub({"baseline": echo(observed), "*": echo(observed, fuel=empty_step,
                                                                              fuel_end=F(5))}),
                                 RUN, observed, FRAME, grid=(S(80, 30),)))
    refused("TANK_BOUND_MET", "stop-70-reserve-30",
            lambda: replay_study(Stub({"baseline": echo(observed), "*": echo(observed, fuel=[F(10)] * n,
                                                                              fuel_end=F(0))}),
                                 RUN, observed, FRAME, grid=(S(70, 30),)))
    refused("TANK_BOUND_MET", "baseline",
            lambda: replay_study(Stub({"*": echo(observed, fuel=[F(10)] * n, fuel_end=F(0))}), RUN, observed,
                                 FRAME))


# --- B10 avoided litres on a subset -----------------------------------------------------------------------------------


def test_b10_avoided_litres_on_offsets() -> None:
    base_fuel, base_end = _fuel_path([F(2)] * 4)
    case_fuel, case_end = _fuel_path([F(1), F(2), F(0), F(2)])
    b = proj("baseline", 4, fuel=base_fuel, fuel_end=base_end)
    p = proj("stop-80-reserve-30", 4, fuel=case_fuel, fuel_end=case_end)
    assert avoided_l_on(b, p, frozenset({0, 10})) == F(3)
    assert avoided_l_on(b, p, frozenset()) == 0
    with pytest.raises(ValueError):
        avoided_l_on(b, proj("x", 3), frozenset({0}))
    with pytest.raises(ValueError):
        avoided_l_on(b, proj("x", 4, start=LATE_SEP), frozenset({0}))


# --- B11 construction and labels ------------------------------------------------------------------------------------


def test_b11_construction() -> None:
    n = 2 * DAY
    with pytest.raises(TypeError, match="soc_pct"):
        series(soc=[50.0] + [F(50)] * (n - 1))
    with pytest.raises(TypeError, match="start_fuel_l"):
        series(fuel=1000)
    with pytest.raises(ValueError):
        series(input_class="OBSERVED")
    with pytest.raises(ValueError):
        dataclasses.replace(FRAME, dawn_local=time(5, 2))
    with pytest.raises(ValueError):
        dataclasses.replace(FRAME, timezone="Mars/Olympus")
    with pytest.raises(TypeError):
        dataclasses.replace(FRAME, battery_capacity_kwh=200)
    with pytest.raises(ValueError):
        StudyRefused("NOPE", "", "")
    observed = series()
    result = replay_study(Stub({"*": echo(observed)}), RUN, observed, FRAME, grid=(S(90, 30), S(80, 25)))
    for record in (result, result.calibration, result.baseline, *result.cases):
        assert (record.input_class, record.evidence_class) == ("SIMULATED", "MODELLED")
    emulated = series(input_class="EMULATED")
    again = replay_study(Stub({"*": echo(emulated)}), RUN, emulated, FRAME, grid=(S(90, 30),))
    assert {r.input_class for r in (again, again.calibration, again.baseline, *again.cases)} == {"EMULATED"}
    for bad in ({"input_class": "X"}, {"evidence_class": "OBSERVED"}):
        with pytest.raises(ValueError):
            dataclasses.replace(result.baseline, **bad)
        with pytest.raises(ValueError):
            dataclasses.replace(result.calibration, **bad)
        with pytest.raises(ValueError):
            dataclasses.replace(result, **bad)
    with pytest.raises(ValueError):
        dataclasses.replace(result.baseline, dawn_verdict="MAYBE")
    with pytest.raises(ValueError):
        dataclasses.replace(result, status="DONE")
    assert isinstance(result.calibration, Calibration) and isinstance(result.baseline, CaseOutcome)


def test_b11_the_kobo_grid() -> None:
    assert len(KOBO_GRID) == 14
    assert [(s.stop_soc_pct, s.reserve_soc_pct) for s in KOBO_GRID[:3]] == [(90, 30), (90, 25), (85, 30)]
    assert KOBO_GRID[-1] == S(60, 25)


# --- B12 seam ----------------------------------------------------------------------------------------------------------


def test_b12_the_study_imports_exactly_its_modules() -> None:
    assert Path(rs.__file__).resolve() == STUDY.resolve()
    modules = set()
    for node in ast.walk(ast.parse(STUDY.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module)
    assert modules == {"__future__", "dataclasses", "datetime", "fractions", "zoneinfo",
                       "assetops_backend.runs.models", "assetops_backend.runs.replay_port",
                       "assetops_contracts.forward_replay"}


def test_b12_whole_window_calls() -> None:
    n = 2 * DAY
    observed = series(kwh=[F(100)] + [F(0)] * (n - 1))
    stub = Stub({"*": echo(observed, kwh=[F(200)] + [F(0)] * (n - 1))})
    assert replay_study(stub, RUN, observed, FRAME).status == "NOT_CALIBRATED"
    assert len(stub.requests) == 1
    stub = Stub({"*": echo(observed)})
    grid = (S(90, 30), S(80, 30), S(70, 25))
    result = replay_study(stub, RUN, observed, FRAME, grid=grid)
    assert len(stub.requests) == 1 + len(grid) == len(result.projections)
    assert all(len(r.pv_available_kw) == n and all(len(load.kw) == n for load in r.loads) for r in stub.requests)
    assert [r.settings for r in stub.requests] == [ReplaySettings(), *grid]
    assert [c.case_id for c in result.cases] == ["stop-90-reserve-30", "stop-80-reserve-30", "stop-70-reserve-25"]


# --- B13 no adopting word ----------------------------------------------------------------------------------------------

ADOPTING = ("reproduc", "confirm", "validat", "replace", "agree")


def _string_constants(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings]


@pytest.mark.parametrize("path", [STUDY, TOOL], ids=["replay_study", "kobo_replay_study"])
def test_b13_no_adopting_word(path: Path) -> None:
    strings = _string_constants(path)
    assert len(strings) > 10, "vacuous: almost no string constants"
    offenders = [s for s in strings if any(word in s.lower() for word in ADOPTING)]
    assert offenders == []
