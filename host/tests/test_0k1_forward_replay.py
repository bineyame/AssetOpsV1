"""0K1: the forward replay port's host adapter, proven by exact equality with the kernel's own trajectory.

No database. Every expected value is read from a kernel trajectory by this file's own reader (`recorded_request`,
`kernel_steps`, `kernel_totals`), which shares no code with `host/forward_replay.py` (W2). The kernel runs for the
expected values use `execute(frozen_world_inputs(run), model_for(run))` directly.

Cases (spec §3): K-BASE (prolonged, v5, v6, v7), K-START (start SOC 55), K-STOP (the shipped stop-60 run), K-RES
(reserve-trial at a 25 % reserve, and the no-setting baseline-30 anchor), K-CLIP (the 240-minute irradiance window
at 900 W/m2, 54 kW potential on a 50 kW inverter). The reader emits loads in REVERSE sorted order, so an adapter
that matched loads by position would fail (D-0K1.10).
"""

from __future__ import annotations

import dataclasses
from fractions import Fraction
from functools import cache

import pytest

from assetops_backend.runs.replay_port import ForwardReplayPort
from assetops_contracts.failures import EXECUTION_FAILURE_KINDS, ExecutionFailure
from assetops_contracts.forward_replay import (
    FORWARD_REPLAY_REFUSALS,
    ForwardReplayProjection,
    ForwardReplayRefused,
    ForwardReplayRequest,
    LoadSeries,
    ReplaySettings,
    ReplayStartState,
    ReplayStep,
)
from assetops_contracts.lab_projection import LAB_CONTROL_REFUSALS
from assetops_simulator.kernel.execute import execute

from execution_adapter import frozen_world_inputs, model_for
from forward_replay import (
    RESERVE_OVERRIDE_FIELDS,
    STOP_OVERRIDE_FIELDS,
    HostForwardReplay,
    replay_inputs,
)
from kobo import kobo_draft

START = "2026-09-22T03:00:00Z"
END = "2026-09-22T11:00:00Z"
PROLONGED = "kobo-mini-grid-prolonged"
STOP_60 = "kobo-mini-grid-stop-60"
TRIAL = "kobo-mini-grid-reserve-trial"
GEN = "generator-state@generator"
SOC = "battery-state-of-charge@battery"
TANK = "fuel-tank-volume@fuel-tank"
PV = "pv-available-power@pv-inverter"
GEN_OUT = "generator-output-power@generator"
LOADS = ("load-clinic", "load-mill", "load-res")
STOP_ADDRESS = "generator-stop-soc-threshold@generator"
RESERVE_ADDRESS = "battery-reserve-state-of-charge@battery"
IRRADIANCE = "site:plane-of-array-irradiance"
HOURS = Fraction(5, 60)


# --- runs ------------------------------------------------------------------------------------------------------


def _set_parameter(parameter_id: str, value):
    def edit(document):
        for item in document["public_parameters"]:
            if item["parameter_id"] == parameter_id:
                item["value"] = value
                return
        raise KeyError(parameter_id)

    return edit


def _drop_parameter(parameter_id: str):
    def edit(document):
        document["public_parameters"] = [
            item for item in document["public_parameters"] if item["parameter_id"] != parameter_id
        ]

    return edit


def _irradiance_4_at_900(document):
    for entry in document["timeline"]:
        if entry["event_id"] == "irradiance-4":
            assert entry["offset_minutes"] == 240 and entry["parameters"][0]["value"] == 550
            entry["parameters"][0]["value"] = 900
            return
    raise KeyError("irradiance-4")


def _reserve(value):
    def edit(document):
        for item in document["foundation"]["components"]:
            for prop in item.get("properties") or []:
                if prop["property_key"] == "reserve-state-of-charge":
                    prop["value"], prop["source"] = value, "SITE"
                    return
        raise KeyError("reserve-state-of-charge")

    return edit


def _mini(name: str, version: int = 7, **edits):
    return kobo_draft(name, timestep_minutes=5, model_profile="mini-grid", model_profile_version=version,
                      start_time=START, end_time=END, **edits)


@cache
def run_for(label: str):
    run = {
        "base-5": lambda: _mini(PROLONGED, 5),
        "base-6": lambda: _mini(PROLONGED, 6),
        "base-7": lambda: _mini(PROLONGED, 7),
        "start": lambda: _mini(PROLONGED, document_edit=_set_parameter("starting-state-of-charge", 55)),
        "stop": lambda: _mini(STOP_60),
        "res-25": lambda: _mini(TRIAL, site_edit=_reserve(25)),
        "res-30": lambda: _mini(TRIAL),
        "res-32": lambda: _mini(TRIAL, site_edit=_reserve(32)),
        "clip": lambda: _mini(PROLONGED, document_edit=_irradiance_4_at_900),
        "v4": lambda: _mini(PROLONGED, 4),
        "daytime": lambda: kobo_draft("kobo-daytime"),
        "blocked": lambda: _mini(PROLONGED, document_edit=_drop_parameter("starting-state-of-charge")),
        "overcast": lambda: kobo_draft("kobo-daytime-overcast"),
    }[label]()
    if label != "blocked":
        assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    return run


@cache
def kernel(label: str):
    """The expected trajectory: the kernel's own run of the case."""
    run = run_for(label)
    trajectory = execute(frozen_world_inputs(run), model_for(run))
    assert trajectory.outcome == "COMPLETED", trajectory.failure
    return trajectory


# --- this file's own reader (shares no code with the adapter) ---------------------------------------------------


def recorded_request(trajectory, case_id: str, settings: ReplaySettings = ReplaySettings()) -> ForwardReplayRequest:
    B = trajectory.boundaries
    n = len(B) - 1

    def measured(i: int, key: str) -> Fraction:
        return dict(B[i + 1].interval_measurements)[key]  # a missing key is a KeyError

    pv = tuple(measured(i, PV) / HOURS for i in range(n))
    loads = tuple(
        LoadSeries(load, tuple(measured(i, f"load-requested-power@{load}") / HOURS for i in range(n)))
        for load in sorted(LOADS, reverse=True)
    )
    stocks = dict(B[0].stocks)
    start = ReplayStartState(stocks[SOC], stocks[TANK], B[0].discrete_state(GEN))
    return ForwardReplayRequest(case_id, pv, loads, start, settings)


def kernel_steps(trajectory) -> list[tuple]:
    B = trajectory.boundaries
    rows = []
    for i in range(len(B) - 1):
        m = dict(B[i + 1].interval_measurements)
        stocks = dict(B[i].stocks)
        unserved = sum(
            (m[f"load-requested-power@{load}"] - m[f"load-served-power@{load}"] for load in LOADS), Fraction(0)
        )
        rows.append((B[i].offset_minutes, dict(B[i].discrete_for_step)[GEN], m[GEN_OUT], unserved,
                     stocks[SOC], stocks[TANK]))
    return rows


def kernel_totals(trajectory) -> dict:
    steps = kernel_steps(trajectory)
    final = dict(trajectory.boundaries[-1].stocks)
    return {
        "starts": sum(1 for t in trajectory.discrete_transitions
                      if t.address == GEN and t.previous == "STOPPED" and t.next == "STARTING"),
        "running_steps": sum(1 for row in steps if row[1] == "RUNNING"),
        "soc_end_pct": final[SOC],
        "fuel_end_l": final[TANK],
        "min_soc_pct": min(dict(b.stocks)[SOC] for b in trajectory.boundaries),
    }


def projected_steps(projection: ForwardReplayProjection) -> list[tuple]:
    return [(s.offset_minutes, s.generator_state, s.generator_kwh, s.unserved_kwh, s.soc_start_pct, s.fuel_start_l)
            for s in projection.steps]


def assert_parity(projection: ForwardReplayProjection, trajectory, *, min_soc: bool = True) -> None:
    expected = kernel_steps(trajectory)
    assert projection.status == "COMPLETED"
    assert len(projection.steps) == len(expected) == 96
    for got, want in zip(projected_steps(projection), expected):
        assert got == want
    totals = kernel_totals(trajectory)
    assert projection.starts == totals["starts"]
    assert projection.running_steps == totals["running_steps"]
    assert projection.soc_end_pct == totals["soc_end_pct"]
    assert projection.fuel_end_l == totals["fuel_end_l"]
    if min_soc:
        assert projection.min_soc_pct == totals["min_soc_pct"]
    assert projection.generator_kwh == sum((row[2] for row in expected), Fraction(0))
    assert projection.unserved_kwh == sum((row[3] for row in expected), Fraction(0))


@cache
def base_request(version: int = 7) -> ForwardReplayRequest:
    return recorded_request(kernel(f"base-{version}"), "baseline")


REPLAYED: dict = {}  # label -> the trajectory the adapter's own kernel call produced (D-0K1.21)


@cache
def replay(label: str) -> ForwardReplayProjection:
    """Each replay executed once and shared between the tests that read it (spec §4 run count)."""
    base = base_request()
    cases = {
        "base-5": (lambda: run_for("base-5"), lambda: base_request(5)),
        "base-6": (lambda: run_for("base-6"), lambda: base_request(6)),
        "base-7": (lambda: run_for("base-7"), lambda: base),
        "start": (lambda: run_for("base-7"), lambda: dataclasses.replace(
            base, case_id="k-start", start=dataclasses.replace(base.start, soc_pct=Fraction(55)))),
        "stop": (lambda: run_for("base-7"), lambda: dataclasses.replace(
            base, case_id="stop-60", settings=ReplaySettings(stop_soc_pct=Fraction(60)))),
        "res-25": (lambda: run_for("res-30"), lambda: recorded_request(
            kernel("res-30"), "reserve-25", ReplaySettings(reserve_soc_pct=Fraction(25)))),
        "res-30": (lambda: run_for("res-30"), lambda: recorded_request(kernel("res-30"), "reserve-baseline")),
        "res-32": (lambda: run_for("res-30"), lambda: recorded_request(
            kernel("res-30"), "reserve-32", ReplaySettings(reserve_soc_pct=Fraction(32)))),
        "clip": (lambda: run_for("clip"), lambda: recorded_request(kernel("clip"), "k-clip")),
    }
    run, request = cases[label]

    def recording(inputs, model):
        trajectory = execute(inputs, model)
        REPLAYED[label] = trajectory
        return trajectory

    return HostForwardReplay(execute_fn=recording).forward_replay(run(), request())


# --- T1 to T5: parity -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("version", [5, 6, 7])
def test_t1_k_base_replays_to_the_kernels_own_trajectory(version: int) -> None:
    trajectory = kernel(f"base-{version}")
    request = base_request(version)
    # Preconditions of the positional-match plant (D-0K1.10): the reader's order is not the sorted order, and the
    # three series differ pairwise, so a mix-up changes the result.
    assert [load.load_id for load in request.loads] == sorted(LOADS, reverse=True)
    series = [load.kw for load in request.loads]
    assert len(set(series)) == 3
    projection = replay(f"base-{version}")
    assert_parity(projection, trajectory)
    if version == 7:  # D-0K1.21: the output-level per-load check, on the kernel trajectory (not the projection)
        got, want = REPLAYED["base-7"].boundaries, trajectory.boundaries
        assert len(got) == len(want) == 97
        for load in LOADS:
            key = f"load-served-power@{load}"
            assert [dict(b.interval_measurements)[key] for b in got[1:]] == \
                [dict(b.interval_measurements)[key] for b in want[1:]]
    # Hand anchors (spec §3), independent of the kernel and the adapter.
    assert projection.fuel_burned_l == Fraction(3, 10) * projection.generator_kwh
    assert projection.starts == 1
    assert projection.running_steps == 66
    assert projection.unserved_kwh > 0
    assert projection.clipped_offsets == ()
    assert not any(step.pv_clipped for step in projection.steps)
    assert (projection.stop_source, projection.stop_soc_pct) == ("BASELINE", Fraction(90))
    assert (projection.reserve_source, projection.reserve_soc_pct) == ("BASELINE", Fraction(30))
    assert (projection.model_profile_id, projection.model_profile_version) == ("mini-grid", version)
    assert (projection.base_run_id, projection.case_id) == (run_for(f"base-{version}").run_id, "baseline")
    assert (projection.interval_start, projection.timestep_minutes) == (START, 5)
    assert projection.evidence_class == "MODELLED"
    assert projection.failure_kind is None and projection.failure_subject is None


def test_t2_k_start_uses_the_requests_start_state() -> None:
    projection = replay("start")
    assert_parity(projection, kernel("start"))
    assert projection.steps[0].soc_start_pct == Fraction(55)
    assert kernel_steps(kernel("start")) != kernel_steps(kernel("base-7"))  # the start state matters


def test_t3_k_stop_equals_the_kernels_stop_60_run() -> None:
    projection = replay("stop")
    assert_parity(projection, kernel("stop"))
    assert (projection.stop_source, projection.stop_soc_pct) == ("SETTING", Fraction(60))
    base = replay("base-7")
    assert projection.generator_kwh < base.generator_kwh
    assert projection.running_steps < base.running_steps


def test_t4_k_res_equals_the_kernels_run_on_a_25_reserve() -> None:
    projection = replay("res-25")
    trajectory = kernel("res-25")
    assert projected_steps(projection) == kernel_steps(trajectory)
    totals = kernel_totals(trajectory)
    assert (projection.starts, projection.running_steps) == (totals["starts"], totals["running_steps"])
    assert (projection.soc_end_pct, projection.fuel_end_l) == (totals["soc_end_pct"], totals["fuel_end_l"])
    assert projection.min_soc_pct == totals["min_soc_pct"]
    # From the request, not the kernel run (whose reserve is a baseline; D-0K1.11).
    assert (projection.reserve_source, projection.reserve_soc_pct) == ("SETTING", Fraction(25))
    assert projection.running_steps == 0
    # D-0K1.20: at 32 the right and wrong reserve paths differ (at 25 they match).
    p32 = replay("res-32")
    t32 = kernel("res-32")
    assert projected_steps(p32) == kernel_steps(t32)
    assert (p32.reserve_source, p32.reserve_soc_pct) == ("SETTING", Fraction(32))
    assert p32.running_steps == kernel_totals(t32)["running_steps"] == 46
    anchor = replay("res-30")  # the same series with NO setting: the baseline-30 path
    assert_parity(anchor, kernel("res-30"))
    assert (anchor.reserve_source, anchor.reserve_soc_pct) == ("BASELINE", Fraction(30))
    assert anchor.running_steps > 0


def test_t5_k_clip_replays_a_clipped_step_and_lists_it() -> None:
    projection = replay("clip")
    assert_parity(projection, kernel("clip"))
    assert projection.clipped_offsets == tuple(range(240, 480, 5))
    assert [s.offset_minutes for s in projection.steps if s.pv_clipped] == list(range(240, 480, 5))
    request = recorded_request(kernel("clip"), "k-clip")
    assert max(request.pv_available_kw) == Fraction(50)  # the inverter limit: the steps are clipped


# --- T6: refusals ---------------------------------------------------------------------------------------------


class _Stub:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, inputs, model):
        self.calls += 1
        raise AssertionError("a refused replay executed")


def _set_at(values, index, value):
    values = list(values)
    values[index] = value
    return tuple(values)


def _with_load(request, load_id, kw):
    return dataclasses.replace(request, loads=tuple(
        LoadSeries(l.load_id, kw if l.load_id == load_id else l.kw) for l in request.loads))


def _refusals():
    base = base_request()
    mill = next(l for l in base.loads if l.load_id == "load-mill")
    res = next(l for l in base.loads if l.load_id == "load-res")
    r = dataclasses.replace
    start = base.start
    return [
        ("pv-95", "base-7", r(base, pv_available_kw=base.pv_available_kw[:95]), "REPLAY_SERIES_MISALIGNED", "pv"),
        ("mill-missing", "base-7", r(base, loads=tuple(l for l in base.loads if l.load_id != "load-mill")),
         "REPLAY_ADDRESS_UNKNOWN", "load-mill"),
        ("pump-extra", "base-7", r(base, loads=base.loads + (LoadSeries("load-pump", mill.kw),)),
         "REPLAY_ADDRESS_UNKNOWN", "load-pump"),
        ("res-twice", "base-7", r(base, loads=base.loads + (res,)), "REPLAY_ADDRESS_UNKNOWN", "load-res"),
        ("pv-gap", "base-7", r(base, pv_available_kw=_set_at(base.pv_available_kw, 10, None)), "INPUT_GAP", "pv@50"),
        ("mill-gap-first", "base-7", r(_with_load(base, "load-mill", _set_at(mill.kw, 10, None)),
                                       pv_available_kw=_set_at(base.pv_available_kw, 11, None)),
         "INPUT_GAP", "load:load-mill@50"),
        ("pv-negative", "base-7", r(base, pv_available_kw=_set_at(base.pv_available_kw, 0, Fraction(-1))),
         "REPLAY_SERIES_INVALID", "pv@0"),
        ("pv-above-limit", "base-7", r(base, pv_available_kw=_set_at(base.pv_available_kw, 0, Fraction(51))),
         "REPLAY_SERIES_INVALID", "pv@0"),
        ("stop-35", "base-7", r(base, settings=ReplaySettings(stop_soc_pct=Fraction(35))), "POLICY_BAND_INVALID",
         "stop"),
        ("stop-101", "base-7", r(base, settings=ReplaySettings(stop_soc_pct=Fraction(101))), "POLICY_BAND_INVALID",
         "stop"),
        ("reserve-neg", "base-7", r(base, settings=ReplaySettings(reserve_soc_pct=Fraction(-1))),
         "POLICY_BAND_INVALID", "reserve"),
        ("reserve-101", "base-7", r(base, settings=ReplaySettings(reserve_soc_pct=Fraction(101))),
         "POLICY_BAND_INVALID", "reserve"),
        ("soc-101", "base-7", r(base, start=r(start, soc_pct=Fraction(101))), "REPLAY_START_STATE_INVALID", "soc"),
        ("fuel-401", "base-7", r(base, start=r(start, fuel_l=Fraction(401))), "REPLAY_START_STATE_INVALID", "fuel"),
        ("generator-running", "base-7",
         r(base, start=ReplayStartState(start.soc_pct, start.fuel_l, "RUNNING")),
         "REPLAY_START_STATE_INVALID", "generator"),
        ("daytime-model", "daytime", base, "REPLAY_MODEL_UNSUPPORTED", "daytime-mini-grid/1"),
        ("v4-model", "v4", base, "REPLAY_MODEL_UNSUPPORTED", "mini-grid/4"),
        ("blocked", "blocked", base, "REPLAY_RUN_NOT_EXECUTABLE", None),
        ("misaligned-before-band", "base-7",
         r(base, pv_available_kw=base.pv_available_kw[:95], settings=ReplaySettings(stop_soc_pct=Fraction(35))),
         "REPLAY_SERIES_MISALIGNED", "pv"),
    ]


REFUSAL_NAMES = (
    "pv-95", "mill-missing", "pump-extra", "res-twice", "pv-gap", "mill-gap-first", "pv-negative", "pv-above-limit",
    "stop-35", "stop-101", "reserve-neg", "reserve-101", "soc-101", "fuel-401", "generator-running", "daytime-model",
    "v4-model", "blocked", "misaligned-before-band")


@pytest.mark.parametrize("name", REFUSAL_NAMES)
def test_t6_each_refusal_has_its_code_and_subject_and_executes_nothing(name: str) -> None:
    _, label, request, code, subject = next(case for case in _refusals() if case[0] == name)
    run = run_for(label)
    if label == "blocked":
        assert run.execution_status == "BLOCKED"
        subject = run.run_id
    stub = _Stub()
    with pytest.raises(ForwardReplayRefused) as refused:
        HostForwardReplay(execute_fn=stub).forward_replay(run, request)
    assert (refused.value.code, refused.value.subject) == (code, subject), name
    assert stub.calls == 0
    with pytest.raises(ForwardReplayRefused):
        replay_inputs(run, request)


def test_t6_the_case_list_is_whole() -> None:
    assert tuple(case[0] for case in _refusals()) == REFUSAL_NAMES


def test_t6_stop_36_is_accepted() -> None:
    plan = replay_inputs(run_for("base-7"), dataclasses.replace(
        base_request(), settings=ReplaySettings(stop_soc_pct=Fraction(36))))
    assert plan.stop == (Fraction(36), "SETTING")


# --- T7: a kernel failure is a FAILED projection --------------------------------------------------------------


def test_t7_a_kernel_failure_is_a_failed_projection_not_a_refusal() -> None:
    def failing(inputs, model):
        t = execute(inputs, model)
        return dataclasses.replace(t, outcome="FAILED",
                                   failure=ExecutionFailure("PHYSICAL_RESOLUTION_FAILURE", "x", "y"),
                                   boundaries=t.boundaries[:41])

    projection = HostForwardReplay(execute_fn=failing).forward_replay(run_for("base-7"), base_request())
    assert projection.status == "FAILED"
    assert (projection.failure_kind, projection.failure_subject) == ("PHYSICAL_RESOLUTION_FAILURE", "x")
    assert len(projection.steps) == 40
    assert projection.soc_end_pct is None and projection.fuel_end_l is None and projection.fuel_burned_l is None


# --- T8: determinism ------------------------------------------------------------------------------------------


def test_t8_the_same_request_gives_the_same_projection_and_identity() -> None:
    run, request = run_for("base-7"), base_request()
    first = HostForwardReplay().forward_replay(run, request)
    second = HostForwardReplay().forward_replay(run, request)
    assert first == second
    renamed = HostForwardReplay().forward_replay(run, dataclasses.replace(request, case_id="another-name"))
    assert renamed.replay_identity == first.replay_identity
    assert renamed.case_id == "another-name"
    assert replay("stop").replay_identity != first.replay_identity


# --- T9: the seam ---------------------------------------------------------------------------------------------


def _values(value):
    if isinstance(value, (ForwardReplayProjection, ReplayStep)):
        for item in dataclasses.fields(value):
            yield from _values(getattr(value, item.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from _values(item)
    else:
        yield value


def test_t9_the_adapter_satisfies_the_port_and_nothing_simulator_shaped_crosses() -> None:
    assert isinstance(HostForwardReplay(), ForwardReplayPort)
    assert FORWARD_REPLAY_REFUSALS.isdisjoint(LAB_CONTROL_REFUSALS)
    assert FORWARD_REPLAY_REFUSALS.isdisjoint(EXECUTION_FAILURE_KINDS)
    projection = replay("base-7")
    assert {f.name for f in dataclasses.fields(projection)} == {
        "base_run_id", "case_id", "status", "model_profile_id", "model_profile_version", "interval_start",
        "timestep_minutes", "stop_soc_pct", "stop_source", "reserve_soc_pct", "reserve_source", "steps",
        "soc_end_pct", "fuel_end_l", "min_soc_pct", "generator_kwh", "unserved_kwh", "starts", "running_steps",
        "fuel_burned_l", "clipped_offsets", "replay_identity", "evidence_class", "failure_kind", "failure_subject"}
    values = list(_values(projection))
    assert len(values) > 96
    for value in values:
        assert type(value) in (Fraction, int, str, bool, type(None)), type(value)
        assert not type(value).__module__.startswith("assetops_simulator")


# --- T10: pins and plans --------------------------------------------------------------------------------------


def _fields(row) -> tuple:
    return (row.state_key, row.canonical_unit, row.dimension, row.shape, row.requirement)


def _at(inputs, address):
    return [f for f in inputs.forcings if f.address == address]


def test_t10_the_override_constants_equal_the_shipped_rows() -> None:
    (stop_row,) = _at(frozen_world_inputs(run_for("stop")), STOP_ADDRESS)
    assert dataclasses.astuple(STOP_OVERRIDE_FIELDS) == _fields(stop_row)
    assert (stop_row.offset_minutes, stop_row.duration_minutes) == (0, 480)
    (reserve_row,) = _at(frozen_world_inputs(run_for("overcast")), RESERVE_ADDRESS)
    assert dataclasses.astuple(RESERVE_OVERRIDE_FIELDS) == _fields(reserve_row)


def test_t10_a_setting_is_one_whole_interval_override_and_none_without() -> None:
    base = base_request()
    stop_plan = replay_inputs(run_for("base-7"), dataclasses.replace(
        base, settings=ReplaySettings(stop_soc_pct=Fraction(60))))
    (row,) = _at(stop_plan.inputs, STOP_ADDRESS)
    assert (row.offset_minutes, row.duration_minutes, row.value, row.shape) == (0, 480, Fraction(60), "WINDOW")
    assert _fields(row) == dataclasses.astuple(STOP_OVERRIDE_FIELDS)
    assert _at(stop_plan.inputs, RESERVE_ADDRESS) == []

    on_stop_60 = replay_inputs(run_for("stop"), dataclasses.replace(
        base, settings=ReplaySettings(stop_soc_pct=Fraction(70))))
    (row,) = _at(on_stop_60.inputs, STOP_ADDRESS)
    assert row.value == Fraction(70)
    assert _at(replay_inputs(run_for("stop"), base).inputs, STOP_ADDRESS) == []

    reserve_plan = replay_inputs(run_for("res-30"), recorded_request(
        kernel("res-30"), "reserve-25", ReplaySettings(reserve_soc_pct=Fraction(25))))
    (row,) = _at(reserve_plan.inputs, RESERVE_ADDRESS)
    assert (row.offset_minutes, row.duration_minutes, row.value) == (0, 480, Fraction(25))
    assert _fields(row) == dataclasses.astuple(RESERVE_OVERRIDE_FIELDS)
    # The reserve setting is a forcing only: the start threshold and every other plant value are untouched.
    frozen = frozen_world_inputs(run_for("res-30"))
    assert [v for v in reserve_plan.inputs.initial_values if v.address not in (SOC, TANK)] == [
        v for v in frozen.initial_values if v.address not in (SOC, TANK)]

    plain = replay_inputs(run_for("base-7"), base)
    assert _at(plain.inputs, STOP_ADDRESS) == [] and _at(plain.inputs, RESERVE_ADDRESS) == []


def test_t10_everything_not_replaced_is_kept_unchanged() -> None:
    run = run_for("base-7")
    request = dataclasses.replace(base_request(), start=ReplayStartState(Fraction(45), Fraction(250), "FAILED"))
    frozen = frozen_world_inputs(run)
    plan = replay_inputs(run, request).inputs
    replaced = {IRRADIANCE, STOP_ADDRESS, RESERVE_ADDRESS} | {f"load-demand@{load}" for load in LOADS}
    kept = [f for f in frozen.forcings if f.address not in replaced]
    assert [f for f in plan.forcings if f.address not in replaced] == kept
    assert plan.causes == frozen.causes
    assert (plan.bounds, plan.site_controls, plan.bus_attachments, plan.unmodelled_inputs) == (
        frozen.bounds, frozen.site_controls, frozen.bus_attachments, frozen.unmodelled_inputs)
    assert plan.interval == frozen.interval
    assert plan.run_id == f"{run.run_id}:replay:baseline"
    by_address = {v.address: v for v in plan.initial_values}
    for row in frozen.initial_values:
        if row.address == SOC:
            assert by_address[SOC] == dataclasses.replace(row, value=Fraction(45))
        elif row.address == TANK:
            assert by_address[TANK] == dataclasses.replace(row, value=Fraction(250))
        else:
            assert by_address[row.address] == row
    assert len(plan.initial_values) == len(frozen.initial_values)
    (generator,) = plan.discrete_initial_values
    assert generator == dataclasses.replace(frozen.discrete_initial_values[0], value="FAILED")
    irradiance = _at(plan, IRRADIANCE)
    assert 0 < len(irradiance) < len(frozen.interval.step_starts)  # run-length merged
    assert all(f.parameter_id == "replay:pv" and f.event_id.startswith("replay:pv:") for f in irradiance)
    loads = [f for f in plan.forcings if f.address.startswith("load-demand@")]
    assert {f.address for f in loads} == {f"load-demand@{load}" for load in LOADS}
    assert all(f.parameter_id == "replay:load" for f in loads)
    # Each load's forcings carry that load's own series, matched by id (P2: the projection's fields are sums over
    # loads, so a positional swap is invisible to T1 and is caught here; mid-build question Q1).
    for series in request.loads:
        per_step = {}
        for f in _at(plan, f"load-demand@{series.load_id}"):
            for offset in range(f.offset_minutes, f.offset_minutes + f.duration_minutes, 5):
                per_step[offset] = f.value
        assert tuple(per_step[o] for o in frozen.interval.step_starts) == series.kw, series.load_id
    # The windows tile the interval at each forcing address.
    for address in {f.address for f in irradiance + loads}:
        windows = sorted((f.offset_minutes, f.duration_minutes) for f in _at(plan, address))
        cursor = 0
        for offset, duration in windows:
            assert offset == cursor
            cursor += duration
        assert cursor == 480
