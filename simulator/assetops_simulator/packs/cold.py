"""The standalone cold-chain pack, `cold-thermal/1` (W2-02, technical design section 4).

One chamber, one probe, one compressor, one grid supply, one backup generator behind one transfer switch and
one bus. The pack owns its generator and bus power port; it does not compose with mini-grid.

## The law (one exact rational step per UTC minute)

    heat_kWh = (heat_leak * (Ta - T) + door_open * door_heat_kWh_per_min * 60) * 1/60
    cool_kWh = compressor_running_and_bus_powered * cooling_kW * 1/60
    T_next   = T + (heat_kWh - cool_kWh) / thermal_capacity

The minute order is fixed: forcing -> due lifecycle -> controller observation/intention -> physical transition
-> energy integration -> invariant -> public boundary. Nothing is clamped: a temperature outside [-40, 60] degC,
a nonzero energy residual, a negative capacity/power or an impossible lifecycle transition raises
`PhysicallyUnacceptable`.

The public boundary emits exact public records stamped at the step's own instant (the state the world was in at
that minute, before its transition). `observation/transform.py` (`cold-observation/1`) turns them into what a
device reports; the pack never serializes a private cause.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from fractions import Fraction
from typing import Mapping

from assetops_simulator.packs.errors import PhysicallyUnacceptable

MODEL_PROFILE = ("cold-thermal", 1)
STEP = timedelta(minutes=1)
SLOT_MINUTES = 5

#: Versioned `cold-thermal/1` pack constants; never Foundation properties.
GENERATOR_START_DELAY_MIN = 2
TRANSFER_DELAY_MIN = 1

TEMPERATURE_FLOOR = Fraction(-40)
TEMPERATURE_CEILING = Fraction(60)

COMPRESSOR_STATES = frozenset({"OFF", "STARTING", "RUNNING", "FAILED"})
GENERATOR_STATES = frozenset({"STOPPED", "STARTING", "RUNNING", "FAILED"})
GRID_STATES = frozenset({"AVAILABLE", "LOST"})
BUS_STATES = frozenset({"POWERED", "UNPOWERED"})
TRANSFER_POSITIONS = frozenset({"GRID", "BACKUP", "OPEN"})
DOOR_STATES = frozenset({"OPEN", "CLOSED"})
PROBE_STATES = frozenset({"OK", "FAILED"})

#: The thirteen frozen Foundation properties: key -> (field, unit, integral minutes?).
PROPERTY_FIELDS: Mapping[str, tuple[str, str, bool]] = {
    "cold-thermal-capacity": ("thermal_capacity", "kWh/degC", False),
    "cold-heat-leak": ("heat_leak", "kW/degC", False),
    "cold-door-heat": ("door_heat", "kWh/min", False),
    "cold-control-low": ("control_low", "degC", False),
    "cold-control-high": ("control_high", "degC", False),
    "cold-policy-low": ("policy_low", "degC", False),
    "cold-policy-high": ("policy_high", "degC", False),
    "cold-min-excursion": ("min_excursion", "min", True),
    "cold-return-hysteresis": ("return_hysteresis", "degC", False),
    "cold-probe-error": ("probe_error", "degC", False),
    "cold-cooling-capacity": ("cooling_capacity", "kW", False),
    "cold-compressor-start-delay": ("compressor_start_delay", "min", True),
    "cold-start-timeout": ("start_timeout", "min", True),
}

#: Named defaults, used only when constructing a new scenario fixture - never to override Foundation.
DEFAULT_PROPERTY_VALUES: Mapping[str, str] = {
    "cold-thermal-capacity": "1.2", "cold-heat-leak": "0.08", "cold-door-heat": "0.02",
    "cold-control-low": "2", "cold-control-high": "4", "cold-policy-low": "2", "cold-policy-high": "4",
    "cold-min-excursion": "15", "cold-return-hysteresis": "0.2", "cold-probe-error": "0.1",
    "cold-cooling-capacity": "3", "cold-compressor-start-delay": "1", "cold-start-timeout": "5",
}


@dataclass(frozen=True)
class ColdParameters:
    """The thirteen exact Foundation values plus the pack's fixed delays."""

    thermal_capacity: Fraction
    heat_leak: Fraction
    door_heat: Fraction
    control_low: Fraction
    control_high: Fraction
    policy_low: Fraction
    policy_high: Fraction
    min_excursion: Fraction
    return_hysteresis: Fraction
    probe_error: Fraction
    cooling_capacity: Fraction
    compressor_start_delay: Fraction
    start_timeout: Fraction
    generator_start_delay: int = GENERATOR_START_DELAY_MIN
    transfer_delay: int = TRANSFER_DELAY_MIN

    def __post_init__(self) -> None:
        if self.thermal_capacity <= 0:
            raise PhysicallyUnacceptable(f"thermal capacity {self.thermal_capacity} kWh/degC is not positive")
        for name in ("heat_leak", "door_heat", "cooling_capacity", "probe_error", "return_hysteresis"):
            if getattr(self, name) < 0:
                raise PhysicallyUnacceptable(f"{name} {getattr(self, name)} is negative")
        for name in ("compressor_start_delay", "start_timeout", "min_excursion"):
            value = getattr(self, name)
            if value.denominator != 1 or value < 0:
                raise PhysicallyUnacceptable(f"{name} {value} min is not a whole nonnegative minute count")
        if self.control_low >= self.control_high:
            raise PhysicallyUnacceptable("control low is not below control high")
        if self.policy_low >= self.policy_high:
            raise PhysicallyUnacceptable("policy low is not below policy high")

    @classmethod
    def from_properties(cls, properties: Mapping[str, tuple[str, str]]) -> "ColdParameters":
        """Build from frozen Foundation `(value_text, unit)` by key; every one of the thirteen is required."""
        missing = sorted(set(PROPERTY_FIELDS) - set(properties))
        if missing:
            raise PhysicallyUnacceptable(f"cold-thermal/1 needs Foundation properties {missing}")
        values: dict[str, Fraction] = {}
        for key, (name, unit, _whole) in PROPERTY_FIELDS.items():
            text, stated_unit = properties[key]
            if stated_unit != unit:
                raise PhysicallyUnacceptable(f"{key} is in {stated_unit!r}, not {unit!r}")
            values[name] = Fraction(text)
        return cls(**values)


@dataclass(frozen=True)
class ColdForcingRow:
    """One private forcing at a UTC minute. `PROBE_FAILURE` exists for unit tests only (no scenario kind)."""

    at: datetime
    kind: str
    asset: str
    value: str


FORCING_EFFECTS: Mapping[str, tuple[str, str]] = {
    "GRID_LOSS": ("grid-1", "LOST"),
    "GRID_RESTORE": ("grid-1", "AVAILABLE"),
    "GENERATOR_FAILURE": ("generator-1", "FAILED"),
    "DOOR_OPEN": ("door-1", "OPEN"),
    "DOOR_CLOSE": ("door-1", "CLOSED"),
    "PROBE_FAILURE": ("probe-1", "FAILED"),
}


@dataclass(frozen=True)
class PublicRecord:
    """One exact public record at the pack boundary, before the observation transform.

    `measurement` is `STATE_AT_INSTANT`/`INTERVAL_MEAN` for a measurement, None for an event. `value` is an
    exact Fraction (degC, kW) or a state member. Events carry `record_kind`, `outcome`, `component_id`, `actor`,
    the per-channel `transition_ordinal` and a `correlation_key` (`(kind, ordinal)`); report construction turns
    those into the public event and correlation IDs.
    """

    device_id: str
    signal_id: str
    source_time: datetime
    measurement: str | None
    value: Fraction | str | None
    unit: str | None
    quality: str = "GOOD"
    unavailable_reason: str | None = None
    interval_start: datetime | None = None
    record_kind: str | None = None
    outcome: str | None = None
    component_id: str | None = None
    actor: str | None = None
    transition_ordinal: int | None = None
    correlation_key: tuple[str, int] | None = None


@dataclass(frozen=True)
class ColdState:
    minute: datetime
    temperature: Fraction
    ambient: Fraction
    door: str = "CLOSED"
    demand: bool = False
    compressor: str = "OFF"
    grid: str = "AVAILABLE"
    bus: str = "POWERED"
    generator: str = "STOPPED"
    transfer: str = "GRID"
    probe: str = "OK"
    # lifecycle bookkeeping (private)
    generator_fault: bool = False
    compressor_due: datetime | None = None
    generator_running_due: datetime | None = None
    generator_timeout_due: datetime | None = None
    transfer_due: datetime | None = None
    # energy ledger since the run start (kWh) and the run's initial temperature
    initial_temperature: Fraction = Fraction(0)
    heat_total: Fraction = Fraction(0)
    cool_total: Fraction = Fraction(0)
    compressor_energy_slot: Fraction = Fraction(0)
    # public transition ordinals per event channel and correlation counters
    ordinals: tuple[tuple[str, int], ...] = ()
    outage: int = 0
    door_cycle: int = 0
    probe_reported_failure: bool = False

    def __post_init__(self) -> None:
        for name, allowed in (("door", DOOR_STATES), ("compressor", COMPRESSOR_STATES), ("grid", GRID_STATES),
                              ("bus", BUS_STATES), ("generator", GENERATOR_STATES),
                              ("transfer", TRANSFER_POSITIONS), ("probe", PROBE_STATES)):
            if getattr(self, name) not in allowed:
                raise PhysicallyUnacceptable(f"{name} {getattr(self, name)!r} is not a cold-thermal/1 state")
        if not TEMPERATURE_FLOOR <= self.temperature <= TEMPERATURE_CEILING:
            raise PhysicallyUnacceptable(f"chamber temperature {self.temperature} degC is outside [-40, 60]")

    @classmethod
    def initial(cls, minute: datetime, temperature: Fraction, ambient: Fraction) -> "ColdState":
        return cls(minute=minute, temperature=temperature, ambient=ambient, initial_temperature=temperature)


@dataclass(frozen=True)
class ColdTransition:
    before: ColdState
    after: ColdState
    heat_kwh: Fraction
    cool_kwh: Fraction
    records: tuple[PublicRecord, ...]


#: Allowed lifecycle moves; anything else is an impossible transition.
_COMPRESSOR_MOVES = {("OFF", "STARTING"), ("STARTING", "RUNNING"), ("STARTING", "OFF"), ("RUNNING", "OFF")}
_GENERATOR_MOVES = {("STOPPED", "STARTING"), ("STARTING", "RUNNING"), ("STARTING", "FAILED"),
                    ("RUNNING", "STOPPED"), ("STARTING", "STOPPED")}
_TRANSFER_MOVES = {("GRID", "OPEN"), ("OPEN", "BACKUP"), ("OPEN", "GRID"), ("BACKUP", "GRID"),
                   ("BACKUP", "OPEN")}

_STATE_CHANNELS = (
    ("grid-meter", "grid"), ("generator-controller", "generator"),
    ("compressor-controller", "compressor"), ("backup-bus-meter", "bus"),
)


def check_move(kind: str, before: str, after: str) -> None:
    moves = {"compressor": _COMPRESSOR_MOVES, "generator": _GENERATOR_MOVES, "transfer": _TRANSFER_MOVES}[kind]
    if before != after and (before, after) not in moves:
        raise PhysicallyUnacceptable(f"{kind} cannot move from {before} to {after}")


def check_residual(params: ColdParameters, state: ColdState) -> None:
    """Stored thermal energy since the start must equal integrated heat minus cooling, exactly."""
    stored = params.thermal_capacity * (state.temperature - state.initial_temperature)
    residual = stored - (state.heat_total - state.cool_total)
    if residual != 0:
        raise PhysicallyUnacceptable(f"energy residual {residual} kWh is not zero")


class ColdPack:
    """`cold-thermal/1`: a deterministic one-minute step over `ColdState`."""

    profile = MODEL_PROFILE

    def __init__(self, parameters: ColdParameters, *, backup_enabled: bool = True) -> None:
        self.p = parameters
        self.backup_enabled = backup_enabled

    # -- the step ---------------------------------------------------------------------------------

    def step(self, state: ColdState, forcings: tuple[ColdForcingRow, ...] = (), *,
             transition: bool = True, start: datetime | None = None) -> ColdTransition:
        """Advance one minute. With `transition=False` (closing boundary) only publish the instant."""
        t = state.minute
        events: list[PublicRecord] = []
        ordinals = dict(state.ordinals)

        def event(device: str, signal: str, kind: str, outcome: str, component: str | None, actor: str,
                  correlation: tuple[str, int]) -> None:
            key = f"{device}/{signal}"
            ordinals[key] = ordinals.get(key, 0) + 1
            events.append(PublicRecord(device, signal, t, None, None, None, record_kind=kind, outcome=outcome,
                                       component_id=component, actor=actor, transition_ordinal=ordinals[key],
                                       correlation_key=correlation))

        s = state
        prev = {attr: getattr(state, attr) for _d, attr in _STATE_CHANNELS}

        # 1. forcing
        for f in sorted(forcings, key=lambda r: (r.at, r.kind, r.asset)):
            if f.at != t:
                raise PhysicallyUnacceptable(f"forcing at {f.at} applied at {t}")
            if FORCING_EFFECTS.get(f.kind) != (f.asset, f.value):
                raise PhysicallyUnacceptable(f"forcing {f.kind} {f.asset} {f.value} is not cold-thermal/1")
            if f.kind == "GRID_LOSS":
                if s.grid == "LOST":
                    raise PhysicallyUnacceptable("grid lost while already lost")
                s = replace(s, grid="LOST", outage=s.outage + 1)
                event("grid-meter", "event", "POWER_LOSS", "LOST", "grid-1", "SENSOR", ("outage", s.outage))
                if s.transfer == "GRID":
                    check_move("transfer", s.transfer, "OPEN")
                    s = replace(s, transfer="OPEN")
            elif f.kind == "GRID_RESTORE":
                if s.grid == "AVAILABLE":
                    raise PhysicallyUnacceptable("grid restored while available")
                s = replace(s, grid="AVAILABLE")
                event("grid-meter", "event", "POWER_RESTORED", "RESTORED", "grid-1", "SENSOR",
                      ("outage", s.outage))
                if s.transfer != "GRID":
                    check_move("transfer", s.transfer, "GRID")
                    s = replace(s, transfer="GRID", transfer_due=None)
                    event("transfer-controller", "event", "TRANSFER_RESULT", "SUCCEEDED", "transfer-1",
                          "CONTROLLER", ("outage", s.outage))
                if s.generator in ("RUNNING", "STARTING"):
                    # a start in progress is abandoned; a running generator stops (both are STOPPED)
                    check_move("generator", s.generator, "STOPPED")
                    s = replace(s, generator="STOPPED", generator_running_due=None, generator_timeout_due=None)
            elif f.kind == "GENERATOR_FAILURE":
                s = replace(s, generator_fault=True)
                if s.generator == "RUNNING":
                    raise PhysicallyUnacceptable("cold-thermal/1 models a start failure, not a running trip")
            elif f.kind == "DOOR_OPEN":
                if s.door == "OPEN":
                    raise PhysicallyUnacceptable("door opened while open")
                s = replace(s, door="OPEN", door_cycle=s.door_cycle + 1)
                event("door-sensor", "event", "DOOR_OPEN", "OPEN", "room-1", "SENSOR", ("door-cycle", s.door_cycle))
            elif f.kind == "DOOR_CLOSE":
                if s.door == "CLOSED":
                    raise PhysicallyUnacceptable("door closed while closed")
                s = replace(s, door="CLOSED")
                event("door-sensor", "event", "DOOR_CLOSE", "CLOSED", "room-1", "SENSOR",
                      ("door-cycle", s.door_cycle))
            elif f.kind == "PROBE_FAILURE":
                s = replace(s, probe="FAILED")

        # 2. due lifecycle
        if s.generator == "STARTING" and s.generator_running_due == t and not s.generator_fault:
            check_move("generator", s.generator, "RUNNING")
            s = replace(s, generator="RUNNING", generator_running_due=None, generator_timeout_due=None)
            event("generator-controller", "start-event", "START_RESULT", "SUCCEEDED", "generator-1",
                  "CONTROLLER", ("outage", s.outage))
            if s.transfer == "OPEN":
                s = replace(s, transfer_due=t + STEP * self.p.transfer_delay)
        if s.generator == "STARTING" and s.generator_timeout_due == t:
            check_move("generator", s.generator, "FAILED")
            s = replace(s, generator="FAILED", generator_running_due=None, generator_timeout_due=None)
            event("generator-controller", "start-event", "START_RESULT", "FAILED", "generator-1",
                  "CONTROLLER", ("outage", s.outage))
        if s.transfer == "OPEN" and s.transfer_due == t and s.generator == "RUNNING":
            check_move("transfer", s.transfer, "BACKUP")
            s = replace(s, transfer="BACKUP", transfer_due=None)
            event("transfer-controller", "event", "TRANSFER_RESULT", "SUCCEEDED", "transfer-1", "CONTROLLER",
                  ("outage", s.outage))
        powered = (s.transfer == "GRID" and s.grid == "AVAILABLE") or (
            s.transfer == "BACKUP" and s.generator == "RUNNING")
        s = replace(s, bus="POWERED" if powered else "UNPOWERED")
        if s.compressor == "STARTING" and s.compressor_due == t and powered:
            check_move("compressor", s.compressor, "RUNNING")
            s = replace(s, compressor="RUNNING", compressor_due=None)

        # 3. controller observation / intention
        if s.grid == "LOST" and self.backup_enabled and s.generator == "STOPPED":
            check_move("generator", s.generator, "STARTING")
            s = replace(s, generator="STARTING", generator_running_due=t + STEP * self.p.generator_start_delay,
                        generator_timeout_due=t + STEP * int(self.p.start_timeout))
            event("generator-controller", "start-event", "START_REQUEST", "REQUESTED", "generator-1",
                  "CONTROLLER", ("outage", s.outage))
        demand = s.demand
        if s.temperature >= self.p.control_high:
            demand = True
        elif s.temperature <= self.p.control_low:
            demand = False
        s = replace(s, demand=demand)
        if not powered or not demand:
            if s.compressor in ("STARTING", "RUNNING"):
                check_move("compressor", s.compressor, "OFF")
            s = replace(s, compressor="OFF" if s.compressor != "FAILED" else "FAILED", compressor_due=None)
        elif s.compressor == "OFF":
            delay = int(self.p.compressor_start_delay)
            if delay == 0:
                s = replace(s, compressor="RUNNING")
            else:
                s = replace(s, compressor="STARTING", compressor_due=t + STEP * delay)

        # public records at this instant (state at t)
        records = list(events)
        start = start or t
        on_slot = (t - start) % timedelta(minutes=SLOT_MINUTES) == timedelta(0)
        if s.probe == "OK":
            if on_slot:
                records.append(PublicRecord("chamber-probe", "temperature", t, "STATE_AT_INSTANT",
                                            s.temperature, "degC"))
        elif not s.probe_reported_failure:
            records.append(PublicRecord("chamber-probe", "temperature", t, "STATE_AT_INSTANT", None, "degC",
                                        quality="UNAVAILABLE", unavailable_reason="SENSOR_FAILURE"))
            s = replace(s, probe_reported_failure=True)
        if on_slot:
            records.append(PublicRecord("ambient-probe", "temperature", t, "STATE_AT_INSTANT", s.ambient, "degC"))
        for device, attr in _STATE_CHANNELS:
            if on_slot or getattr(s, attr) != prev[attr]:
                records.append(PublicRecord(device, "state", t, "STATE_AT_INSTANT", getattr(s, attr), "state"))
        if on_slot and t > start:
            records.append(PublicRecord("compressor-meter", "power", t, "INTERVAL_MEAN",
                                        s.compressor_energy_slot / SLOT_MINUTES, "kW",
                                        interval_start=t - timedelta(minutes=SLOT_MINUTES)))
            s = replace(s, compressor_energy_slot=Fraction(0))

        if not transition:
            return ColdTransition(state, replace(s, ordinals=tuple(sorted(ordinals.items()))), Fraction(0),
                                  Fraction(0), tuple(records))

        # 4. physical transition
        running = s.compressor == "RUNNING" and s.bus == "POWERED"
        door_open = 1 if s.door == "OPEN" else 0
        heat = (self.p.heat_leak * (s.ambient - s.temperature) + door_open * self.p.door_heat * 60) * Fraction(1, 60)
        cool = (self.p.cooling_capacity if running else Fraction(0)) * Fraction(1, 60)
        if cool < 0:
            raise PhysicallyUnacceptable("negative cooling power")
        t_next = s.temperature + (heat - cool) / self.p.thermal_capacity
        compressor_kw = self.p.cooling_capacity if running else Fraction(0)
        # 5. energy integration
        after = replace(s, minute=t + STEP, temperature=t_next, heat_total=s.heat_total + heat,
                        cool_total=s.cool_total + cool, compressor_energy_slot=s.compressor_energy_slot + compressor_kw,
                        ordinals=tuple(sorted(ordinals.items())))  # __post_init__ enforces [-40, 60]
        # 6. invariant
        check_residual(self.p, after)
        # 7. public boundary
        return ColdTransition(state, after, heat, cool, tuple(records))


@dataclass(frozen=True)
class ColdRun:
    """A whole window: per-minute transitions from `start` to `end` and the closing-boundary records."""

    transitions: tuple[ColdTransition, ...]
    records: tuple[PublicRecord, ...] = field(default=())

    def state_at(self, minute: datetime) -> ColdState:
        for tr in self.transitions:
            if tr.before.minute == minute:
                return tr.before
        last = self.transitions[-1].after
        if last.minute == minute:
            return last
        raise KeyError(minute)


def run_window(pack: ColdPack, *, start: datetime, end: datetime, initial_temperature: Fraction,
               ambient: Fraction, forcings: tuple[ColdForcingRow, ...]) -> ColdRun:
    """Step every minute in [start, end) and publish the closing boundary at `end`."""
    by_minute: dict[datetime, list[ColdForcingRow]] = {}
    for f in forcings:
        if not start <= f.at <= end:
            raise PhysicallyUnacceptable(f"forcing at {f.at} is outside the run window")
        by_minute.setdefault(f.at, []).append(f)
    state = ColdState.initial(start, initial_temperature, ambient)
    transitions: list[ColdTransition] = []
    records: list[PublicRecord] = []
    t = start
    while t < end:
        tr = pack.step(state, tuple(by_minute.get(t, ())), start=start)
        transitions.append(tr)
        records.extend(tr.records)
        state = tr.after
        t += STEP
    closing = pack.step(state, tuple(by_minute.get(end, ())), transition=False, start=start)
    transitions.append(closing)
    records.extend(closing.records)
    return ColdRun(tuple(transitions), tuple(records))


__all__ = [
    "BUS_STATES", "COMPRESSOR_STATES", "ColdForcingRow", "ColdPack", "ColdParameters", "ColdRun", "ColdState",
    "ColdTransition", "DEFAULT_PROPERTY_VALUES", "GENERATOR_STATES", "MODEL_PROFILE", "PROPERTY_FIELDS",
    "PhysicallyUnacceptable", "PublicRecord", "check_move", "check_residual", "run_window",
]
