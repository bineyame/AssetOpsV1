"""The forward replay adapter: a frozen mini-grid run's world, replayed under a caller's series (0K1).

Implements `ForwardReplayPort` (`backend/assetops_backend/runs/replay_port.py`). It lives in the composition leaf
because it needs both the product's frozen `SimulationRun` and the kernel; nothing imports it, and the product
receives it by injection.

## What a replay is (D-0K1.2)

The base run's own frozen world (`frozen_world_inputs(run)`) with four things replaced: the irradiance forcing
(rebuilt from the request's PV-available series), each load's demand forcing, the stop-threshold and reserve
override forcings (built only from the request's settings), and the three run-start values. Every cause, bound, site
control, bus attachment, unmodelled input and other forcing is kept as frozen. The kernel then executes it.

A setting is applied through the kernel's own override mechanism: one whole-interval window at the stop-threshold
or reserve address (`mini_grid._stop_threshold_at`, `minigrid._reserve_at`), never by arithmetic here. The only
arithmetic on a physical value is the PV inversion `G = 1000 x kW / rated` (D-0K1.4), the tank identity for fuel
burned and the sums for the totals. With `kW <= inverter limit`, the kernel's `min(potential, limit)` gives back
exactly `kW`, so a step at the limit (clipped) replays with the same dispatch and is only listed.

## Refusal and failure (D-0K1.6)

`replay_inputs` judges the run and the request in the order of spec §2.4 and raises `ForwardReplayRefused` at the
first failure, before anything executes. A kernel failure is not a refusal: it is a projection with status
`FAILED`.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable

from assetops_backend.runs.models import SimulationRun
from assetops_contracts.forward_replay import (
    REPLAY_GENERATOR_STATES,
    ForwardReplayProjection,
    ForwardReplayRefused,
    ForwardReplayRequest,
    ReplayStep,
)
from assetops_contracts.trajectory import PrivateTrajectory
from assetops_contracts.world_inputs import ForcingInput, FrozenWorldInputs
from assetops_simulator.kernel.execute import execute
from assetops_simulator.kernel.model import ModelSpec
from assetops_simulator.packs.minigrid import IRRADIANCE_ADDRESS, STANDARD_IRRADIANCE

from execution_adapter import (
    FrozenRunNotReconstructible,
    RunNotExecutable,
    frozen_world_inputs,
    model_for,
)

#: The models a replay runs on (D-0K1.3); v5-v7 are proven by T1 (D-0K1.12). A later version joins by one line here.
#: v8 is proven by 0K4a's N11 (`host/tests/test_0k4a_dispatch_v8.py`, D-0K4.22 I4), not by T1, whose hand anchors are
#: v7's linear fuel law.
REPLAY_MODELS = frozenset({("mini-grid", 5), ("mini-grid", 6), ("mini-grid", 7), ("mini-grid", 8)})


def STEP_HOURS(minutes: int) -> Fraction:
    return Fraction(minutes, 60)


@dataclass(frozen=True)
class OverrideFields:
    state_key: str
    canonical_unit: str
    dimension: str
    shape: str
    requirement: str


#: The shipped stop-60 run's own stop-override row (pinned by T10).
STOP_OVERRIDE_FIELDS = OverrideFields("generator-stop-soc-threshold", "%", "FRACTION", "WINDOW", "REQUIRED")
#: The overcast run's reserve-override row (T10's drift guard only; T4 proves the mini-grid models accept it).
RESERVE_OVERRIDE_FIELDS = OverrideFields("battery-reserve-state-of-charge", "%", "FRACTION", "WINDOW", "REQUIRED")

_SOC = "battery-state-of-charge@"
_GEN = "generator-state@"
_TANK = "fuel-tank-volume@"
_LOAD = "load-demand@"


@dataclass(frozen=True)
class ReplayPlant:
    """Every value read from the base run's frozen inputs; nothing assumed."""

    battery: str
    generator: str
    tank: str
    loads: tuple[str, ...]
    pv_rated_kw: Fraction
    inverter_ac_limit_kw: Fraction
    tank_capacity_l: Fraction
    start_threshold_pct: Fraction
    stop_baseline_pct: Fraction
    reserve_baseline_pct: Fraction


@dataclass(frozen=True)
class ReplayPlan:
    inputs: FrozenWorldInputs
    model: ModelSpec
    plant: ReplayPlant
    stop: tuple[Fraction, str]
    reserve: tuple[Fraction, str]
    clipped_offsets: tuple[int, ...]


def _refuse(code: str, subject: str, detail: str) -> ForwardReplayRefused:
    return ForwardReplayRefused(code, subject, detail)


def _one(rows: list, subject: str, run_id: str):
    if len(rows) != 1:
        raise _refuse("REPLAY_RUN_NOT_EXECUTABLE", subject,
                      f"run {run_id} freezes {len(rows)} rows for {subject}; a replay needs exactly one")
    return rows[0]


def _plant(run: SimulationRun, inputs: FrozenWorldInputs) -> ReplayPlant:
    run_id = run.run_id
    battery = _one([v for v in inputs.initial_values if v.address.startswith(_SOC)], "battery-state-of-charge", run_id)
    generator = _one([v for v in inputs.discrete_initial_values if v.address.startswith(_GEN)], "generator-state",
                     run_id)
    tank = _one([v for v in inputs.initial_values if v.address.startswith(_TANK)], "fuel-tank-volume", run_id)
    loads = tuple(sorted({f.address[len(_LOAD):] for f in inputs.forcings if f.address.startswith(_LOAD)}))
    if not loads:
        raise _refuse("REPLAY_RUN_NOT_EXECUTABLE", "load-demand", f"run {run_id} freezes no load-demand forcing")

    def number(state_key: str) -> Fraction:
        return _one([v for v in inputs.initial_values if v.state_key == state_key], state_key, run_id).value

    return ReplayPlant(
        battery=battery.address[len(_SOC):],
        generator=generator.address[len(_GEN):],
        tank=tank.address[len(_TANK):],
        loads=loads,
        pv_rated_kw=number("pv-rated-power"),
        inverter_ac_limit_kw=number("inverter-ac-limit"),
        tank_capacity_l=number("fuel-tank-capacity"),
        start_threshold_pct=number("generator-start-soc-threshold"),
        stop_baseline_pct=number("generator-stop-soc-threshold"),
        reserve_baseline_pct=number("battery-reserve-state-of-charge"),
    )


def _windows(values: tuple[Fraction, ...], dt: int) -> list[tuple[int, int, Fraction]]:
    """One (offset, duration, value) per run of equal consecutive values."""
    runs: list[tuple[int, int, Fraction]] = []
    for index, value in enumerate(values):
        if runs and runs[-1][2] == value:
            offset, duration, _ = runs[-1]
            runs[-1] = (offset, duration + dt, value)
        else:
            runs.append((index * dt, dt, value))
    return runs


def _series_forcings(template: ForcingInput, values: tuple[Fraction, ...], dt: int, event_prefix: str,
                     parameter_id: str) -> list[ForcingInput]:
    return [
        dataclasses.replace(template, event_id=f"{event_prefix}:{offset}", parameter_id=parameter_id, value=value,
                            shape="WINDOW", offset_minutes=offset, duration_minutes=duration)
        for offset, duration, value in _windows(values, dt)
    ]


def _override(fields: OverrideFields, address: str, event_id: str, parameter_id: str, value: Fraction,
              duration: int) -> ForcingInput:
    return ForcingInput(event_id=event_id, address=address, state_key=fields.state_key, parameter_id=parameter_id,
                        value=value, canonical_unit=fields.canonical_unit, dimension=fields.dimension,
                        shape=fields.shape, offset_minutes=0, duration_minutes=duration,
                        requirement=fields.requirement)


def replay_inputs(run: SimulationRun, request: ForwardReplayRequest) -> ReplayPlan:
    """Judge the run and the request (spec §2.4, first failure refuses) and build the replay's kernel inputs."""
    # 1. The run must be executable.
    try:
        model = model_for(run)
        inputs = frozen_world_inputs(run)
    except (RunNotExecutable, FrozenRunNotReconstructible) as refused:
        raise _refuse("REPLAY_RUN_NOT_EXECUTABLE", run.run_id, str(refused)) from refused
    # 2. On a replay model.
    identity = (model.model_profile_id, model.model_profile_version)
    if identity not in REPLAY_MODELS:
        raise _refuse("REPLAY_MODEL_UNSUPPORTED", f"{identity[0]}/{identity[1]}",
                      f"a replay runs on {sorted(REPLAY_MODELS)} only")
    # 3. The plant, read from the frozen inputs.
    plant = _plant(run, inputs)
    steps = inputs.interval.step_starts
    dt = inputs.interval.timestep_minutes
    n = len(steps)
    # 4. Every series one value per step.
    if len(request.pv_available_kw) != n:
        raise _refuse("REPLAY_SERIES_MISALIGNED", "pv", f"{len(request.pv_available_kw)} PV values for {n} steps")
    for load in sorted(request.loads, key=lambda item: item.load_id):
        if len(load.kw) != n:
            raise _refuse("REPLAY_SERIES_MISALIGNED", f"load:{load.load_id}", f"{len(load.kw)} values for {n} steps")
    # 5. Exactly the plant's loads, each once.
    requested = [load.load_id for load in request.loads]
    missing = sorted(set(plant.loads) - set(requested))
    extra = sorted(set(requested) - set(plant.loads))
    repeated = sorted({load_id for load_id in requested if requested.count(load_id) > 1})
    for subject, what in ((missing, "has no series"), (extra, "is not a load of the run"), (repeated, "repeats")):
        if subject:
            raise _refuse("REPLAY_ADDRESS_UNKNOWN", subject[0], f"{subject[0]} {what}")
    by_load = {load.load_id: load.kw for load in request.loads}

    def scan(test: Callable[[Fraction | None, bool], bool]) -> str | None:
        for index, offset in enumerate(steps):
            if test(request.pv_available_kw[index], True):
                return f"pv@{offset}"
            for load_id in plant.loads:
                if test(by_load[load_id][index], False):
                    return f"load:{load_id}@{offset}"
        return None

    # 6. No gap (D-0K1.5).
    gap = scan(lambda value, _: value is None)
    if gap is not None:
        raise _refuse("INPUT_GAP", gap, "a series has no value at this step; a gap is never filled")
    # 7. No negative value, no PV above the inverter limit.
    invalid = scan(lambda value, is_pv: value < 0 or (is_pv and value > plant.inverter_ac_limit_kw))
    if invalid is not None:
        raise _refuse("REPLAY_SERIES_INVALID", invalid,
                      f"a value is negative or PV exceeds the inverter limit {plant.inverter_ac_limit_kw} kW")
    # 8. Settings inside the kernel's own bands.
    settings = request.settings
    if settings.stop_soc_pct is not None and not plant.start_threshold_pct < settings.stop_soc_pct <= 100:
        raise _refuse("POLICY_BAND_INVALID", "stop", f"a stop threshold lies in ({plant.start_threshold_pct}, 100]")
    if settings.reserve_soc_pct is not None and not 0 <= settings.reserve_soc_pct <= 100:
        raise _refuse("POLICY_BAND_INVALID", "reserve", "a reserve lies in [0, 100]")
    # 9. A start state the run could declare.
    start = request.start
    if not 0 <= start.soc_pct <= 100:
        raise _refuse("REPLAY_START_STATE_INVALID", "soc", "a state of charge lies in [0, 100]")
    if not 0 <= start.fuel_l <= plant.tank_capacity_l:
        raise _refuse("REPLAY_START_STATE_INVALID", "fuel", f"fuel lies in [0, {plant.tank_capacity_l}]")
    if start.generator_state not in REPLAY_GENERATOR_STATES:
        raise _refuse("REPLAY_START_STATE_INVALID", "generator",
                      f"a run starts with the generator {sorted(REPLAY_GENERATOR_STATES)}")
    # 10. Build.
    soc_address = f"{_SOC}{plant.battery}"
    tank_address = f"{_TANK}{plant.tank}"
    generator_address = f"{_GEN}{plant.generator}"
    stop_address = f"generator-stop-soc-threshold@{plant.generator}"
    reserve_address = f"battery-reserve-state-of-charge@{plant.battery}"
    load_addresses = {f"{_LOAD}{load}": load for load in plant.loads}
    replaced = {IRRADIANCE_ADDRESS, stop_address, reserve_address} | set(load_addresses)

    def template(address: str) -> ForcingInput:
        for forcing in inputs.forcings:
            if forcing.address == address:
                return forcing
        raise _refuse("REPLAY_RUN_NOT_EXECUTABLE", address, f"run {run.run_id} freezes no forcing at {address}")

    built: list[ForcingInput] = []
    irradiance = tuple(STANDARD_IRRADIANCE * kw / plant.pv_rated_kw for kw in request.pv_available_kw)
    built += _series_forcings(template(IRRADIANCE_ADDRESS), irradiance, dt, "replay:pv", "replay:pv")
    for address, load in sorted(load_addresses.items(), key=lambda item: item[1]):
        built += _series_forcings(template(address), by_load[load], dt, f"replay:load:{load}", "replay:load")
    duration = inputs.interval.duration_minutes
    if settings.stop_soc_pct is not None:
        built.append(_override(STOP_OVERRIDE_FIELDS, stop_address, "replay:stop", "replay:stop",
                               settings.stop_soc_pct, duration))
    if settings.reserve_soc_pct is not None:
        built.append(_override(RESERVE_OVERRIDE_FIELDS, reserve_address, "replay:reserve", "replay:reserve",
                               settings.reserve_soc_pct, duration))
    forcings = tuple(f for f in inputs.forcings if f.address not in replaced) + tuple(built)

    def start_value(row):
        if row.address == soc_address:
            return dataclasses.replace(row, value=start.soc_pct)
        if row.address == tank_address:
            return dataclasses.replace(row, value=start.fuel_l)
        return row

    replay = dataclasses.replace(
        inputs,
        run_id=f"{run.run_id}:replay:{request.case_id}",
        forcings=forcings,
        initial_values=tuple(start_value(row) for row in inputs.initial_values),
        discrete_initial_values=tuple(
            dataclasses.replace(row, value=start.generator_state) if row.address == generator_address else row
            for row in inputs.discrete_initial_values
        ),
    )
    stop = (settings.stop_soc_pct, "SETTING") if settings.stop_soc_pct is not None else (
        plant.stop_baseline_pct, "BASELINE")
    reserve = (settings.reserve_soc_pct, "SETTING") if settings.reserve_soc_pct is not None else (
        plant.reserve_baseline_pct, "BASELINE")
    clipped = tuple(offset for offset, kw in zip(steps, request.pv_available_kw) if kw == plant.inverter_ac_limit_kw)
    return ReplayPlan(inputs=replay, model=model, plant=plant, stop=stop, reserve=reserve, clipped_offsets=clipped)


def _measured(boundary, key: str) -> Fraction:
    value = boundary.interval_measurement(key)
    if value is None:
        raise RuntimeError(f"the kernel recorded no {key} at offset {boundary.offset_minutes}; a defect, not a refusal")
    return value


def project(plan: ReplayPlan, trajectory: PrivateTrajectory, run: SimulationRun,
            request: ForwardReplayRequest) -> ForwardReplayProjection:
    """The neutral projection of one replay's trajectory (spec §2.5).

    `fuel_burned_l` is the tank identity: start - end + declared increases - declared decreases. It is exact only
    while the tank never meets its capacity or empty bound; a run whose tank causes could clip is outside 0K1's proof
    (0K2) (D-0K1.14).
    """
    plant = plan.plant
    soc = f"{_SOC}{plant.battery}"
    tank = f"{_TANK}{plant.tank}"
    generator = f"{_GEN}{plant.generator}"
    output = f"generator-output-power@{plant.generator}"
    boundaries = trajectory.boundaries
    n = len(plan.inputs.interval.step_starts)
    clipped = set(plan.clipped_offsets)
    steps = []
    for i in range(min(len(boundaries) - 1, n)):
        here, after = boundaries[i], boundaries[i + 1]
        unserved = sum(
            (_measured(after, f"load-requested-power@{load}") - _measured(after, f"load-served-power@{load}")
             for load in plant.loads),
            Fraction(0),
        )
        steps.append(ReplayStep(
            offset_minutes=here.offset_minutes,
            generator_state=here.discrete_state_for_step(generator),
            generator_kwh=_measured(after, output),
            unserved_kwh=unserved,
            soc_start_pct=here.stock(soc),
            fuel_start_l=here.stock(tank),
            pv_clipped=here.offset_minutes in clipped,
        ))
    completed = trajectory.outcome == "COMPLETED"
    soc_end = boundaries[n].stock(soc) if completed else None
    fuel_end = boundaries[n].stock(tank) if completed else None
    fuel_burned = None
    if completed:
        declared = sum(
            (cause.quantity if cause.direction == "INCREASE" else -cause.quantity
             for cause in plan.inputs.causes if cause.address == tank),
            Fraction(0),
        )
        fuel_burned = boundaries[0].stock(tank) - fuel_end + declared
    failure = trajectory.failure
    return ForwardReplayProjection(
        base_run_id=run.run_id,
        case_id=request.case_id,
        status=trajectory.outcome,
        model_profile_id=plan.model.model_profile_id,
        model_profile_version=plan.model.model_profile_version,
        interval_start=plan.inputs.interval.start_time,
        timestep_minutes=plan.inputs.interval.timestep_minutes,
        stop_soc_pct=plan.stop[0],
        stop_source=plan.stop[1],
        reserve_soc_pct=plan.reserve[0],
        reserve_source=plan.reserve[1],
        steps=tuple(steps),
        soc_end_pct=soc_end,
        fuel_end_l=fuel_end,
        min_soc_pct=min(b.stock(soc) for b in boundaries),
        generator_kwh=sum((s.generator_kwh for s in steps), Fraction(0)),
        unserved_kwh=sum((s.unserved_kwh for s in steps), Fraction(0)),
        starts=sum(1 for t in trajectory.discrete_transitions
                   if t.address == generator and t.previous == "STOPPED" and t.next == "STARTING"),
        running_steps=sum(1 for s in steps if s.generator_state == "RUNNING"),
        fuel_burned_l=fuel_burned,
        clipped_offsets=plan.clipped_offsets,
        replay_identity=trajectory.inputs_identity,
        failure_kind=failure.kind if failure is not None else None,
        failure_subject=failure.subject if failure is not None else None,
    )


class HostForwardReplay:
    """The host's `ForwardReplayPort`."""

    def __init__(self, *, execute_fn: Callable[[FrozenWorldInputs, ModelSpec], PrivateTrajectory] = execute) -> None:
        self._execute = execute_fn

    def forward_replay(self, run: SimulationRun, request: ForwardReplayRequest) -> ForwardReplayProjection:
        plan = replay_inputs(run, request)
        trajectory = self._execute(plan.inputs, plan.model)
        return project(plan, trajectory, run, request)


__all__ = [
    "REPLAY_MODELS",
    "RESERVE_OVERRIDE_FIELDS",
    "STEP_HOURS",
    "STOP_OVERRIDE_FIELDS",
    "HostForwardReplay",
    "OverrideFields",
    "ReplayPlan",
    "ReplayPlant",
    "project",
    "replay_inputs",
]
