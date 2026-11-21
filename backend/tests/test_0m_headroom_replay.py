"""0M: the demand-on-headroom study against a stub port (spec §2, §4 M1-M8). No kernel, no database.

Every projection is scripted here from per-case values; the stub records every request, so the number, order and
shape of the port calls are asserted directly. Windows are whole local days at 5 minutes in Africa/Addis_Ababa
(UTC+3). Expected values are written out by hand from the window's calendar, never computed by a study helper.
"""

from __future__ import annotations

import ast
from datetime import time
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace

import pytest

from assetops_backend.runs import headroom_replay as hr
from assetops_backend.runs.headroom_replay import (
    MIN_DEMAND_DAYS,
    CapacityOutcome,
    CustomerLoad,
    DemandOutcome,
    HeadroomRefused,
    ReducedCapacity,
    headroom_study,
)
from assetops_backend.runs.replay_study import MonthFigure, ObservedSeries, StudyFrame
from assetops_contracts.forward_replay import ForwardReplayProjection, LoadSeries, ReplayStep

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
MODULE = BACKEND / "assetops_backend" / "runs" / "headroom_replay.py"
TOOL = REPO / "tools" / "mto_headroom_study.py"
START = "2026-08-31T21:00:00Z"  # Tue 1 Sep 2026 00:00 local
SEP30 = "2026-09-29T21:00:00Z"  # Wed 30 Sep 00:00 local
DAY = 288
H = F(5, 60)
ZONE = "Africa/Addis_Ababa"
FRAME = StudyFrame(timezone=ZONE, battery_capacity_kwh=F(150), min_dawn_days=1)
WEEK = frozenset(range(5))
EVERY_DAY = frozenset(range(7))
LOAD_ORDER = ("load-res", "load-mill", "load-clinic")  # reverse sorted: the host is not first by position


def need(key, value, unit="kW", component="pv-inverter"):
    return SimpleNamespace(state_ref=(component, key), property_key=key, value=value, unit=unit,
                           canonical_value=value, canonical_unit=unit)


def stand_in(run_id: str, limit: float | None, *, battery: float = 150.0, interval="2026-09-01/61d", extra=()):
    needs = [need("pv-rated-power", 50.0, component="pv-array"),
             need("battery-energy-capacity", battery, "kWh", "battery")]
    if limit is not None:
        needs.insert(1, need("inverter-ac-limit", limit))
    needs += list(extra)
    return SimpleNamespace(run_id=run_id, deterministic_identity=SimpleNamespace(model_needs=tuple(needs),
                                                                                  interval=interval))


RUN = stand_in("run-m", 50.0)
RUN25 = stand_in("run-m-25", 25.0)


def customer(cid="mto-huller", kw=F(15), start=time(10), end=time(15), weekdays=WEEK, host="load-mill",
             evidence="SIGNED") -> CustomerLoad:
    return CustomerLoad(cid, kw, start, end, weekdays, host, evidence)


def series(days: int, *, start: str = START, pv=None, loads=None, soc=None, input_class="SIMULATED") -> ObservedSeries:
    n = days * DAY
    if loads is None:
        loads = {"load-res": (F(2),) * n, "load-mill": (F(3),) * n, "load-clinic": (F(1),) * n}
    return ObservedSeries(
        interval_start=start, timestep_minutes=5,
        pv_available_kw=tuple(pv) if pv is not None else (F(30),) * n,
        loads=tuple(LoadSeries(load_id, tuple(loads[load_id])) for load_id in LOAD_ORDER),
        generator_kwh=(F(0),) * n, generator_state=("STOPPED",) * n,
        soc_pct=tuple(soc) if soc is not None else (F(50),) * n,
        start_fuel_l=F(1000), input_class=input_class,
    )


def proj(case_id, n, *, start=START, states=None, kwh=None, soc=None, fuel=None, unserved=F(0)):
    states = tuple(states) if states is not None else ("STOPPED",) * n
    kwh = tuple(kwh) if kwh is not None else (F(0),) * n
    soc = tuple(soc) if soc is not None else (F(50),) * n
    fuel = tuple(fuel) if fuel is not None else (F(1000),) * n
    fuel_end = fuel[-1]
    steps = tuple(ReplayStep(5 * i, states[i], kwh[i], F(0), soc[i], fuel[i], False) for i in range(n))
    return ForwardReplayProjection(
        base_run_id="run-m", case_id=case_id, status="COMPLETED", model_profile_id="mini-grid",
        model_profile_version=7, interval_start=start, timestep_minutes=5, stop_soc_pct=F(90),
        stop_source="BASELINE", reserve_soc_pct=F(30), reserve_source="BASELINE", steps=steps,
        soc_end_pct=soc[-1], fuel_end_l=fuel_end, min_soc_pct=min(soc), generator_kwh=sum(kwh, F(0)),
        unserved_kwh=unserved, starts=0, running_steps=sum(1 for s in states if s == "RUNNING"),
        fuel_burned_l=fuel[0] - fuel_end, clipped_offsets=(), replay_identity="x")


def echo(observed: ObservedSeries, **overrides):
    """A projection equal to the published series (a calibrated replay), with per-field overrides."""
    values = dict(states=observed.generator_state, kwh=observed.generator_kwh, soc=observed.soc_pct,
                  start=observed.interval_start)
    values.update(overrides)
    return lambda request: proj(request.case_id, len(observed.pv_available_kw), **values)


class Stub:
    def __init__(self, scripts: dict):
        self.scripts = scripts
        self.requests = []
        self.runs = []

    def forward_replay(self, run, request):
        self.requests.append(request)
        self.runs.append(run.run_id)
        made = self.scripts.get(request.case_id, self.scripts.get("*"))
        return made(request) if callable(made) else made


def calibrated(observed: ObservedSeries, **cases) -> Stub:
    return Stub({"*": echo(observed), **cases})


def refused(code: str, subject: str, call, stub: Stub) -> None:
    with pytest.raises(HeadroomRefused) as caught:
        call()
    assert (caught.value.code, caught.value.subject) == (code, subject)
    assert stub.requests == []


def by_id(request) -> dict:
    return {load.load_id: load.kw for load in request.loads}


def months(result) -> dict:
    return {m.month: m.value for m in result}


# --- M1 customer steps are local ----------------------------------------------------------------------------------


def test_m1_customer_steps_are_local_and_join_only_the_host_load() -> None:
    observed = series(5)  # Tue 1 Sep - Sat 5 Sep local
    stub = calibrated(observed)
    result = headroom_study(stub, RUN, observed, (customer(),), FRAME, min_days=1)
    assert result.status == "CALIBRATED"
    request = next(r for r in stub.requests if r.case_id == "mto-huller")
    assert [load.load_id for load in request.loads] == list(LOAD_ORDER)
    loads, base = by_id(request), {load.load_id: load.kw for load in observed.loads}
    # 07:00Z on 1 Sep is offset 10 h = step 120; 11:55Z is step 179; 06:55Z step 119 and 12:00Z step 180 carry none.
    added = [i for i in range(5 * DAY) if loads["load-mill"][i] != base["load-mill"][i]]
    expected = [d * DAY + i for d in range(4) for i in range(120, 180)]  # Tue-Fri; Saturday 5 Sep none
    assert added == expected
    assert 119 not in added and 180 not in added and 120 in added and 179 in added
    assert all(loads["load-mill"][i] == base["load-mill"][i] + 15 for i in expected)
    assert loads["load-res"] == base["load-res"] and loads["load-clinic"] == base["load-clinic"]
    huller = result.demand[0]
    assert huller.customer_days == ("2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04")
    assert huller.customer_kwh == 4 * 60 * 15 * H


# --- M2 headroom ----------------------------------------------------------------------------------------------------


def test_m2_headroom_per_step_clamped_and_by_month() -> None:
    n = 3 * DAY  # Wed 30 Sep, Thu 1 Oct, Fri 2 Oct local
    pv = [F(26)] * DAY + [F(16)] * DAY + [F(3)] * DAY  # PV minus the 6 kW load: 20, 10, -3 kW
    observed = series(3, start=SEP30, pv=pv)
    stub = calibrated(observed)
    result = headroom_study(stub, RUN, observed, (customer(weekdays=EVERY_DAY),), FRAME, min_days=1)
    huller = result.demand[0]
    assert huller.days_without_headroom == ("2026-10-01", "2026-10-02")
    assert huller.kwh_beyond_headroom == 60 * 5 * H + 60 * 15 * H == F(100)
    assert months(huller.days_without_headroom_by_month) == {"2026-09": 0, "2026-10": 2}
    assert months(huller.kwh_beyond_headroom_by_month) == {"2026-09": 0, "2026-10": 100}
    assert months(huller.customer_kwh_by_month) == {"2026-09": 75, "2026-10": 150}
    assert huller.customer_kwh == 225
    assert [m.days for m in huller.customer_kwh_by_month] == [1, 2]
    assert n == len(stub.requests[0].pv_available_kw)


# --- M3 extra figures ------------------------------------------------------------------------------------------------


def test_m3_extra_figures_against_the_no_customer_replay() -> None:
    n = 3 * DAY
    observed = series(3, start=SEP30)
    fuel = [F(1000)] * 11 + [F(999)] * 290 + [F(997)] * (n - 301)  # 1 L burned on 30 Sep, 2 L on 1 Oct
    states = ["STOPPED"] * n
    for i in list(range(10, 20)) + list(range(300, 310)):
        states[i] = "RUNNING"  # two starts, 20 running steps
    kwh = [F(0)] * n
    kwh[10], kwh[300] = F(4), F(6)
    stub = calibrated(observed, **{"mto-huller": echo(observed, fuel=fuel, states=states, kwh=kwh,
                                                       unserved=F(7, 2))})
    result = headroom_study(stub, RUN, observed, (customer(weekdays=EVERY_DAY),), FRAME, min_days=1)
    huller = result.demand[0]
    assert huller.extra_fuel_l == 3
    assert months(huller.extra_fuel_l_by_month) == {"2026-09": 1, "2026-10": 2}
    assert huller.extra_generator_kwh == 10
    assert huller.extra_unserved_kwh == F(7, 2)
    assert huller.extra_running_steps == 20
    assert huller.extra_starts == 2
    assert huller.litres_per_customer_kwh == F(3) / 225
    assert result.baseline_fuel_l == 0


def test_m3_a_customer_with_no_step_in_the_window_has_no_ratio() -> None:
    observed = series(4)  # Tue 1 Sep - Fri 4 Sep
    result = headroom_study(calibrated(observed), RUN, observed, (customer(weekdays=frozenset({5})),), FRAME,
                            min_days=1)
    saturday = result.demand[0]
    assert saturday.customer_kwh == 0 and saturday.customer_days == ()
    assert saturday.litres_per_customer_kwh is None


# --- M4 reduced capacity ---------------------------------------------------------------------------------------------


def _reduced_scripts(observed):
    n = len(observed.pv_available_kw)
    burned = lambda litres: [F(1000)] * 100 + [F(1000) - litres] * (n - 100)  # noqa: E731
    return {
        "reduced": echo(observed, fuel=burned(F(5)), soc=(F(50),) * n),  # clears the 1 Sep dawn
        "reduced-mto-huller": echo(observed, fuel=burned(F(8))),
        "mto-huller": echo(observed, fuel=burned(F(1))),
    }


def test_m4_reduced_runs_on_clipped_pv_against_the_reduced_baseline() -> None:
    n = 2 * DAY
    pv = [F(51)] * n
    for i in range(12):
        pv[i] = F(25, 2)
    soc = [F(50)] * n
    soc[60] = F(20)  # the 1 Sep dawn (05:00 local, step 60) is below 35 in the series and the baseline
    observed = series(2, pv=pv, soc=soc)
    stub = calibrated(observed, **_reduced_scripts(observed))
    huller = customer(kw=F(30), weekdays=EVERY_DAY)
    result = headroom_study(stub, RUN, observed, (huller,), FRAME, reduced=ReducedCapacity(RUN25, F(25)),
                            min_days=1)
    assert [r.case_id for r in stub.requests] == ["baseline", "mto-huller", "reduced", "reduced-mto-huller"]
    assert stub.runs == ["run-m", "run-m", "run-m-25", "run-m-25"]
    reduced_request = stub.requests[2]
    assert reduced_request.pv_available_kw == tuple(F(25, 2) if i < 12 else F(25) for i in range(n))
    assert stub.requests[3].pv_available_kw == reduced_request.pv_available_kw
    full, low = result.demand
    assert (full.capacity, low.capacity, low.case_id) == ("FULL", "REDUCED", "reduced-mto-huller")
    assert low.extra_fuel_l == 3  # 8 - 5 against the reduced baseline; 8 against the full one
    assert full.extra_fuel_l == 1
    # headroom: full 51 - 6 = 45 >= 30; reduced 25 - 6 = 19, 11 kW short at each of 2 x 60 customer steps
    assert full.kwh_beyond_headroom == 0 and full.days_without_headroom == ()
    assert low.kwh_beyond_headroom == 2 * 60 * 11 * H
    assert low.days_without_headroom == ("2026-09-01", "2026-09-02")
    # dawn: the reduced customer keeps the 1 Sep dawn below; the reduced baseline cleared it, the full one did not
    assert low.new_dawn_days_below == ("2026-09-01",) and low.cleared_dawn_days_below == ()
    assert full.new_dawn_days_below == () and full.cleared_dawn_days_below == ()
    capacity = result.capacity
    assert capacity.case_id == "reduced" and capacity.inverter_limit_kw == 25
    assert capacity.extra_fuel_l == 5 and capacity.extra_fuel_l_per_day == F(5) / 2
    assert capacity.cleared_dawn_days_below == ("2026-09-01",) and capacity.new_dawn_days_below == ()
    assert capacity.dawn_days_below == 0


@pytest.mark.parametrize("reduced_run, limit, full_run", [
    (stand_in("r", 50.0), F(25), RUN),  # the reduced run's frozen limit is 50, not the stated 25
    (stand_in("r", 25.0), F(25), stand_in("f", 25.0)),  # the full run is not above
    (stand_in("r", 25.0, battery=200.0), F(25), RUN),  # another need differs
    (stand_in("r", 25.0, extra=(need("inverter-ac-limit", 25.0),)), F(25), RUN),  # two limit rows
    (stand_in("r", None), F(25), RUN),  # no limit row
    (stand_in("r", 25.0, interval="other"), F(25), RUN),  # another interval
    (SimpleNamespace(run_id="r", deterministic_identity=SimpleNamespace(
        model_needs=(need("inverter-ac-limit", 25.0, unit="W"), need("pv-rated-power", 50.0, component="pv-array"),
                     need("battery-energy-capacity", 150.0, "kWh", "battery")), interval="2026-09-01/61d")),
     F(25), RUN),  # a unit other than kW
], ids=["limit-mismatch", "full-not-above", "battery-differs", "two-limit-rows", "no-limit-row", "interval",
        "unit-not-kw"])
def test_m4_reduced_run_checked_against_its_frozen_foundation(reduced_run, limit, full_run) -> None:
    observed = series(2)
    stub = calibrated(observed)
    refused("REDUCED_CAPACITY_INVALID", "reduced",
            lambda: headroom_study(stub, full_run, observed, (customer(),), FRAME,
                                   reduced=ReducedCapacity(reduced_run, limit), min_days=1), stub)


# --- M5 refusals, each with zero port calls ---------------------------------------------------------------------------


@pytest.mark.parametrize("customers, code, subject", [
    ((customer("baseline"),), "CUSTOMER_ID_INVALID", "baseline"),
    ((customer("reduced"),), "CUSTOMER_ID_INVALID", "reduced"),
    ((customer("reduced-x"),), "CUSTOMER_ID_INVALID", "reduced-x"),
    ((customer("a"), customer("a")), "CUSTOMER_ID_INVALID", "a"),
    ((customer("Bad Id"),), "CUSTOMER_ID_INVALID", "Bad Id"),
    ((customer("a" * 33),), "CUSTOMER_ID_INVALID", "a" * 33),
    ((customer(kw=F(0)),), "CUSTOMER_WINDOW_INVALID", "mto-huller"),
    ((customer(start=time(10, 2)),), "CUSTOMER_WINDOW_INVALID", "mto-huller"),
    ((customer(start=time(10, 0, 30)),), "CUSTOMER_WINDOW_INVALID", "mto-huller"),
    ((customer(end=time(10)),), "CUSTOMER_WINDOW_INVALID", "mto-huller"),
    ((customer(weekdays=frozenset()),), "CUSTOMER_WINDOW_INVALID", "mto-huller"),
    ((customer(weekdays=frozenset({7})),), "CUSTOMER_WINDOW_INVALID", "mto-huller"),
    ((customer(host="load-pump"),), "CUSTOMER_LOAD_UNKNOWN", "mto-huller"),
], ids=["baseline", "reduced", "reduced-prefix", "repeated", "bad-id", "33-chars", "kw-0", "minute-2", "second-30",
        "end-equals-start", "no-weekday", "weekday-7", "unknown-load"])
def test_m5_customer_refusals_before_any_call(customers, code, subject) -> None:
    observed = series(2)
    stub = calibrated(observed)
    refused(code, subject, lambda: headroom_study(stub, RUN, observed, customers, FRAME,
                                                  reduced=ReducedCapacity(RUN25, F(25)), min_days=1), stub)


def test_m5_a_32_character_id_proceeds_and_its_reduced_case_reaches_the_port() -> None:
    observed = series(2)
    stub = calibrated(observed)
    cid = "a" * 32
    headroom_study(stub, RUN, observed, (customer(cid),), FRAME, reduced=ReducedCapacity(RUN25, F(25)), min_days=1)
    assert [r.case_id for r in stub.requests] == ["baseline", cid, "reduced", f"reduced-{cid}"]


def test_m5_limit_zero_is_refused_before_any_call() -> None:
    observed = series(2)
    stub = calibrated(observed)
    refused("REDUCED_CAPACITY_INVALID", "reduced",
            lambda: headroom_study(stub, RUN, observed, (customer(),), FRAME,
                                   reduced=ReducedCapacity(RUN25, F(0)), min_days=1), stub)


def test_m5_sample_boundary_at_the_default_and_a_failed_calibration() -> None:
    assert MIN_DEMAND_DAYS == 28
    soc = [F(50)] * (28 * DAY)
    soc[4 * DAY + 100] = None  # one step of day 5 unknown: 27 admissible days
    short = series(28, soc=soc)
    stub = calibrated(short)
    result = headroom_study(stub, RUN, short, (customer(),), FRAME)
    assert result.status == "SAMPLE_TOO_SHORT" and result.calibration is None and result.projections == ()
    assert stub.requests == []
    whole = series(28)
    stub = calibrated(whole)
    assert headroom_study(stub, RUN, whole, (customer(),), FRAME).status == "CALIBRATED"
    assert len(stub.requests) == 2
    off = Stub({"*": echo(whole, soc=(F(60),) * (28 * DAY))})  # SOC 10 points off: not calibrated
    result = headroom_study(off, RUN, whole, (customer(),), FRAME, reduced=ReducedCapacity(RUN25, F(25)))
    assert result.status == "NOT_CALIBRATED" and result.calibration.failed == ("soc",)
    assert len(off.requests) == 1 and result.demand == () and result.capacity is None
    assert len(result.projections) == 1


# --- M6 calls ----------------------------------------------------------------------------------------------------------


def test_m6_one_whole_window_call_per_case() -> None:
    observed = series(3)
    n = 3 * DAY
    two = (customer(), customer("mto-welder", F(10), time(18), time(21), evidence="VERBAL"))
    stub = calibrated(observed)
    result = headroom_study(stub, RUN, observed, two, FRAME, min_days=1)
    assert len(stub.requests) == 1 + 2 and len(result.projections) == 3
    stub = calibrated(observed)
    result = headroom_study(stub, RUN, observed, two, FRAME, reduced=ReducedCapacity(RUN25, F(25)), min_days=1)
    assert len(stub.requests) == 2 + 2 * 2 and len(result.projections) == 6
    assert [r.case_id for r in stub.requests] == ["baseline", "mto-huller", "mto-welder", "reduced",
                                                  "reduced-mto-huller", "reduced-mto-welder"]
    assert all(len(r.pv_available_kw) == n and all(len(load.kw) == n for load in r.loads) for r in stub.requests)
    assert [d.case_id for d in result.demand] == ["mto-huller", "mto-welder", "reduced-mto-huller",
                                                  "reduced-mto-welder"]


# --- M7 construction and seam --------------------------------------------------------------------------------------------


def _demand_fields(**overrides):
    fields = dict(case_id="x", customer_id="x", evidence="SIGNED", capacity="FULL", customer_days=(),
                  customer_kwh=F(0), customer_kwh_by_month=(), days_without_headroom=(),
                  days_without_headroom_by_month=(), kwh_beyond_headroom=F(0), kwh_beyond_headroom_by_month=(),
                  extra_fuel_l=F(0), extra_fuel_l_by_month=(), extra_generator_kwh=F(0), extra_unserved_kwh=F(0),
                  extra_starts=0, extra_running_steps=0, litres_per_customer_kwh=None, dawn_days_below=0,
                  worst_dawn_soc_pct=F(50), dawn_verdict="PASS", new_dawn_days_below=(),
                  cleared_dawn_days_below=(), input_class="SIMULATED")
    fields.update(overrides)
    return fields


def _capacity_fields(**overrides):
    fields = dict(case_id="reduced", inverter_limit_kw=F(25), extra_fuel_l=F(0), extra_fuel_l_per_day=F(0),
                  extra_fuel_l_by_month=(), extra_generator_kwh=F(0), extra_unserved_kwh=F(0), dawn_days_below=0,
                  worst_dawn_soc_pct=F(50), dawn_verdict="PASS", new_dawn_days_below=(),
                  cleared_dawn_days_below=(), input_class="SIMULATED")
    fields.update(overrides)
    return fields


def test_m7_construction() -> None:
    with pytest.raises(TypeError):
        customer(kw=15.0)
    with pytest.raises(TypeError):
        ReducedCapacity(RUN25, 25.0)
    with pytest.raises(ValueError):
        customer(evidence="UNKNOWN")
    with pytest.raises(ValueError):
        HeadroomRefused("NOPE", "", "")
    DemandOutcome(**_demand_fields())
    CapacityOutcome(**_capacity_fields())
    for bad in ({"input_class": "X"}, {"evidence_class": "OBSERVED"}):
        with pytest.raises(ValueError):
            DemandOutcome(**_demand_fields(**bad))
        with pytest.raises(ValueError):
            CapacityOutcome(**_capacity_fields(**bad))


def test_m7_every_outcome_carries_the_series_class_and_modelled() -> None:
    observed = series(2, input_class="EMULATED")
    result = headroom_study(calibrated(observed), RUN, observed, (customer(),), FRAME,
                            reduced=ReducedCapacity(RUN25, F(25)), min_days=1)
    records = (result, result.calibration, result.capacity, *result.demand)
    assert len(result.demand) == 2
    assert {(r.input_class, r.evidence_class) for r in records} == {("EMULATED", "MODELLED")}


def test_m7_the_module_imports_exactly_its_set() -> None:
    modules = set()
    for node in ast.walk(ast.parse(MODULE.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module)
    assert Path(hr.__file__).resolve() == MODULE.resolve()
    assert modules == {"__future__", "dataclasses", "datetime", "fractions", "assetops_backend.runs.models",
                       "assetops_backend.runs.replay_port", "assetops_backend.runs.replay_study",
                       "assetops_contracts.forward_replay"}


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


@pytest.mark.parametrize("path", [MODULE, TOOL], ids=["headroom_replay", "mto_headroom_study"])
def test_m7_no_adopting_word(path: Path) -> None:
    strings = _string_constants(path)
    assert len(strings) > 10, "vacuous: almost no string constants"
    offenders = [s for s in strings if any(word in s.lower() for word in ADOPTING)]
    assert offenders == []


# --- M8 the month's customer ---------------------------------------------------------------------------------------------


def test_m8_the_huller_runs_22_weekdays_in_each_month() -> None:
    observed = series(61)
    result = headroom_study(calibrated(observed), RUN, observed, (customer(),), FRAME, min_days=1)
    huller = result.demand[0]
    assert len(huller.customer_days) == 44
    assert huller.customer_kwh == 44 * 75
    assert huller.customer_kwh_by_month == (MonthFigure("2026-09", 30, F(1650)), MonthFigure("2026-10", 31, F(1650)))
