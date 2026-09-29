"""The `mini-grid` v1 model: the daytime world plus a generator and its fuel.

T025a, under execution contract 9 and additively
(`D-2026-09-29-t025-generator-policy-package`). `daytime-mini-grid` v1 and
the fuel model are untouched; this pack reuses the daytime pack's PV,
battery, reserve and load machinery and adds:

- an addressed discrete state `generator-state` with the declared members
  STOPPED, STARTING, RUNNING and FAILED. This build starts from STOPPED or
  FAILED only - RUNNING and STARTING need timer history no scenario can yet
  declare - and moves only along STOPPED -> STARTING -> RUNNING -> STOPPED.
  FAILED is inert: no output, no transition in or out, and not an execution
  failure. Failure and recovery causes are T035's.
- **Site-owned control policy, and no trigger of the model's own.** The
  controller requests RUN only when the state of charge at T is at or below
  the Site's frozen `start-soc-threshold`, and STOP only when the generator
  is RUNNING, the Site's `minimum-runtime` has elapsed since it became
  RUNNING and the state of charge is at or above `stop-soc-threshold`.
- **The Site's frozen source priority, unsubstituted.** Sources serve load in
  that order (Kobo: PV, battery, generator), so a running generator serves
  what the sources ahead of it do not. It may also charge the battery, only
  when the battery is not discharging, within the PCS charge limit and the
  battery's headroom; the rating is a ceiling, never a command.
- **Fuel is checked before energy is accepted**, and falls by the Foundation's
  specific fuel consumption times accepted generator energy - to load and to
  the battery alike. The law is linear: no idle fuel and no start fuel, a
  simplification this pack discloses in every step's notes.

Lifecycle timing: transitions happen at step boundaries only. A start delay
that has elapsed is due in phase A, before the sample at T; a request emitted
at T moves the state in phase F, after the sample and the view. Start delay
and minimum runtime must be step-aligned: one ending inside a step is refused
rather than rounded.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from assetops_contracts.control import (
    DISCRETE_UNIT,
    AcceptedControl,
    AcceptedFlow,
    AcceptedFlowSet,
    BalanceIdentity,
    ControlIntent,
    ControlRequest,
    ControllerView,
    EffectiveControl,
    LoadService,
    StockAccount,
    ViewEntry,
)
from assetops_simulator.kernel.model import (
    ComponentRelation,
    Coupling,
    CouplingRefused,
    DiscreteStateSpec,
    ModelSpec,
    StateHandler,
    StepContext,
    TransitionRequest,
)
from assetops_simulator.packs import minigrid as daytime
from assetops_simulator.packs.fuel import (
    FUEL_TANK_CAPACITY,
    FUEL_TANK_VOLUME,
    GENERATOR_SPECIFIC_CONSUMPTION,
    PhysicallyUnacceptable,
)

GENERATOR_STATE = "generator-state"
GENERATOR_RATED_POWER = "generator-rated-power"
START_THRESHOLD = "generator-start-soc-threshold"
STOP_THRESHOLD = "generator-stop-soc-threshold"
MINIMUM_RUNTIME = "generator-minimum-runtime"
START_DELAY = "generator-start-delay"

STOPPED, STARTING, RUNNING, FAILED = "STOPPED", "STARTING", "RUNNING", "FAILED"
RUN, STOP = "RUN", "STOP"
HUNDRED = daytime.HUNDRED

LINEAR_FUEL_NOTE = (
    "fuel follows accepted generator energy at the Foundation's specific "
    "consumption; the linear law has no idle or start fuel (a disclosed "
    "simplification)"
)

GENERATOR_LIFECYCLE = DiscreteStateSpec(
    state_key=GENERATOR_STATE,
    scope="COMPONENT",
    allowed_values=(STOPPED, STARTING, RUNNING, FAILED),
    initialization_owner="SCENARIO",
    initial_values_supported=frozenset({STOPPED, FAILED}),
    transitions=frozenset(
        {(STOPPED, STARTING), (STARTING, RUNNING), (RUNNING, STOPPED)}
    ),
    observable_signals=("generator-status (reported status is T025b's)",),
    statement=(
        "The generator's physical lifecycle state. STOPPED starts on a Site "
        "policy request and is STARTING for the frozen start delay, "
        "delivering nothing; RUNNING delivers up to its rating; a Site "
        "policy stop returns it to STOPPED. FAILED is declared and inert: "
        "failure and recovery causes are refused until T035. RUNNING and "
        "STARTING are not supported at run start, because they need timer "
        "history no scenario can declare yet."
    ),
)


def _minutes(what: str):
    def accept(value: Fraction, *_: object) -> Fraction:
        if value < 0 or value.denominator != 1:
            raise PhysicallyUnacceptable(
                f"{what} of {value} min is not a whole, non-negative number of "
                "minutes"
            )
        return value

    return accept


def _positive(what: str, unit: str):
    def accept(value: Fraction, *_: object) -> Fraction:
        if value <= 0:
            raise PhysicallyUnacceptable(f"{what} of {value} {unit} is not positive")
        return value

    return accept


def _fuel_volume(value: Fraction, *_: object) -> Fraction:
    if value < 0:
        raise PhysicallyUnacceptable(
            f"a stored volume of {value} litres is not a volume a tank holds"
        )
    return value


GENERATOR_HANDLERS: tuple[StateHandler, ...] = (
    daytime._coefficient(
        GENERATOR_RATED_POWER,
        "generator-rated-power-coefficient",
        "POWER",
        _positive("a generator rated power", "kW"),
        "The most AC power the generator delivers: a ceiling, not a command.",
    ),
    daytime._coefficient(
        GENERATOR_SPECIFIC_CONSUMPTION,
        "generator-specific-fuel-consumption-coefficient",
        "VOLUME_PER_ENERGY",
        _positive("a specific fuel consumption", "L/kWh"),
        "Litres burned per kWh of accepted generator energy.",
    ),
    daytime._coefficient(
        START_THRESHOLD,
        "generator-start-soc-threshold-coefficient",
        "FRACTION",
        daytime._percentage("a start threshold"),
        "Site policy: request a start at or below this state of charge.",
    ),
    daytime._coefficient(
        STOP_THRESHOLD,
        "generator-stop-soc-threshold-coefficient",
        "FRACTION",
        daytime._percentage("a stop threshold"),
        "Site policy: request a stop at or above this state of charge.",
    ),
    daytime._coefficient(
        MINIMUM_RUNTIME,
        "generator-minimum-runtime-coefficient",
        "DURATION",
        _minutes("a minimum runtime"),
        "Site policy: no stop before this long RUNNING.",
    ),
    daytime._coefficient(
        START_DELAY,
        "generator-start-delay-coefficient",
        "DURATION",
        _minutes("a start delay"),
        "How long the generator is STARTING, delivering nothing.",
    ),
    daytime._coefficient(
        FUEL_TANK_CAPACITY,
        "fuel-tank-capacity-coefficient",
        "VOLUME",
        _fuel_volume,
        "The most fuel the tank holds.",
    ),
    StateHandler(
        handler_id="fuel-tank-volume-stock",
        state_key=FUEL_TANK_VOLUME,
        scope="COMPONENT",
        role="CAUSAL_INPUT",
        kind="STOCK",
        dimension="VOLUME",
        floor=Fraction(0),
        floor_bound_case_id="insufficient-fuel",
        statement=(
            "The fuel in the tank, initialized by the scenario and moved only "
            "by accepted generator energy."
        ),
        consume=daytime._apply_to_stock,
        initialize=_fuel_volume,
    ),
)

GENERATOR_RELATIONS: tuple[ComponentRelation, ...] = (
    ComponentRelation(
        relation_id="generator",
        display_name="generator",
        state_keys=frozenset(
            {
                GENERATOR_RATED_POWER,
                GENERATOR_SPECIFIC_CONSUMPTION,
                START_THRESHOLD,
                STOP_THRESHOLD,
                MINIMUM_RUNTIME,
                START_DELAY,
            }
        ),
        statement=(
            "The rating, the consumption and the Site's generator policy are "
            "facts about one generator."
        ),
    ),
    ComponentRelation(
        relation_id="fuel-tank",
        display_name="fuel tank",
        state_keys=frozenset({FUEL_TANK_VOLUME, FUEL_TANK_CAPACITY}),
        statement="The fuel held and the most it can hold are facts about one tank.",
    ),
)


# --- The plant --------------------------------------------------------------


@dataclass(frozen=True)
class _Generator:
    generator: str
    tank: str
    rated: Fraction
    sfc: Fraction
    start_threshold: Fraction
    stop_threshold: Fraction
    minimum_runtime: int
    start_delay: int
    tank_capacity: Fraction
    #: The Site's source priority over the three sources this model runs.
    order: tuple[str, ...]

    @property
    def state_address(self) -> str:
        return f"{GENERATOR_STATE}@{self.generator}"

    @property
    def fuel_address(self) -> str:
        return f"{FUEL_TANK_VOLUME}@{self.tank}"


def _generator(context: StepContext, plant: daytime._Plant) -> _Generator:
    answers = {
        key: daytime._one(context, key, what)
        for key, what in (
            (GENERATOR_RATED_POWER, "generator"),
            (GENERATOR_SPECIFIC_CONSUMPTION, "generator"),
            (START_THRESHOLD, "generator"),
            (STOP_THRESHOLD, "generator"),
            (MINIMUM_RUNTIME, "generator"),
            (START_DELAY, "generator"),
            (FUEL_TANK_CAPACITY, "fuel tank"),
        )
    }
    generator = daytime._component(answers[GENERATOR_RATED_POWER][0])
    for key in (
        GENERATOR_SPECIFIC_CONSUMPTION,
        START_THRESHOLD,
        STOP_THRESHOLD,
        MINIMUM_RUNTIME,
        START_DELAY,
    ):
        if daytime._component(answers[key][0]) != generator:
            raise CouplingRefused(
                "TOPOLOGY_INCONSISTENT",
                answers[key][0],
                f"{key} and the rating name two different generators",
            )
    tank = daytime._component(answers[FUEL_TANK_CAPACITY][0])
    value = {key: item[1] for key, item in answers.items()}

    sources = context.site_control(daytime.SOURCE_PRIORITY)
    modelled = {plant.pv: "pv", plant.battery: "battery", generator: "generator"}
    order = tuple(modelled[m] for m in sources.members if m in modelled)
    if sorted(order) != ["battery", "generator", "pv"]:
        raise CouplingRefused(
            "TOPOLOGY_INCONSISTENT",
            f"site-control:{daytime.SOURCE_PRIORITY}",
            "the source priority must name this run's PV array, battery and "
            "generator exactly once each; this model never substitutes an order",
            f"it names {list(sources.members)}",
        )
    daytime._require_bus(
        context,
        (
            ("GENERATION", generator, None),
            ("FUEL_SUPPLY", tank, generator),
        ),
    )
    return _Generator(
        generator=generator,
        tank=tank,
        rated=value[GENERATOR_RATED_POWER],
        sfc=value[GENERATOR_SPECIFIC_CONSUMPTION],
        start_threshold=value[START_THRESHOLD],
        stop_threshold=value[STOP_THRESHOLD],
        minimum_runtime=int(value[MINIMUM_RUNTIME]),
        start_delay=int(value[START_DELAY]),
        tank_capacity=value[FUEL_TANK_CAPACITY],
        order=order,
    )


def _both(context: StepContext) -> tuple[daytime._Plant, _Generator]:
    plant = daytime._plant(context)
    return plant, _generator(context, plant)


def _state(context: StepContext, gen: _Generator):
    found = context.discrete_value(gen.state_address)
    if found is None:
        raise CouplingRefused(
            "INITIAL_STATE_UNANSWERED",
            gen.state_address,
            "the generator's lifecycle state at run start is scenario-owned and "
            "the run does not state it; it is never assumed",
        )
    return found


def _refuse_a_deadline_inside_the_step(
    context: StepContext, address: str, deadline: int, what: str
) -> None:
    if context.from_offset < deadline < context.to_offset:
        raise CouplingRefused(
            "PHYSICAL_RESOLUTION_FAILURE",
            address,
            f"the {what} ends at offset {deadline}, inside the step "
            f"[{context.from_offset}, {context.to_offset}); lifecycle "
            "transitions happen at step boundaries only, so it must be a whole "
            "multiple of the step",
        )


# --- The callables ----------------------------------------------------------


def prepare(context: StepContext) -> None:
    daytime.prepare(context)
    plant, gen = _both(context)
    _state(context, gen)
    if gen.start_threshold >= gen.stop_threshold:
        raise CouplingRefused(
            "PHYSICAL_RESOLUTION_FAILURE",
            f"{STOP_THRESHOLD}@{gen.generator}",
            f"the start threshold {gen.start_threshold} % is not below the stop "
            f"threshold {gen.stop_threshold} %, so the Site policy has no band",
        )
    if gen.start_delay <= 0:
        raise CouplingRefused(
            "PHYSICAL_RESOLUTION_FAILURE",
            f"{START_DELAY}@{gen.generator}",
            "the start delay must be positive: STARTING lasts at least one step",
        )
    fuel = context.stock(gen.fuel_address)
    if fuel is None:
        raise CouplingRefused(
            "INITIAL_STATE_UNANSWERED",
            gen.fuel_address,
            "the fuel in the tank at run start is scenario-owned and not stated",
        )
    if fuel > gen.tank_capacity:
        raise CouplingRefused(
            "PHYSICAL_RESOLUTION_FAILURE",
            gen.fuel_address,
            f"{fuel} L at run start exceeds the tank capacity {gen.tank_capacity} L",
        )


def due(context: StepContext) -> tuple[TransitionRequest, ...]:
    """Phase A: a start delay that has elapsed makes STARTING -> RUNNING due."""
    plant, gen = _both(context)
    current = _state(context, gen)
    if current.value != STARTING or current.since_offset is None:
        return ()
    deadline = current.since_offset + gen.start_delay
    if deadline > context.from_offset:
        _refuse_a_deadline_inside_the_step(
            context, gen.state_address, deadline, "start delay"
        )
        return ()
    return (
        TransitionRequest(
            address=gen.state_address,
            next=RUNNING,
            cause=(
                f"start delay of {gen.start_delay} min elapsed since STARTING "
                f"at offset {current.since_offset}"
            ),
        ),
    )


def view(context: StepContext) -> ControllerView:
    base = daytime.view(context)
    plant, gen = _both(context)
    current = _state(context, gen)
    at = context.from_offset
    running_for = (
        Fraction(at - current.since_offset)
        if current.value == RUNNING and current.since_offset is not None
        else None
    )
    if running_for is not None:
        _refuse_a_deadline_inside_the_step(
            context,
            gen.state_address,
            current.since_offset + gen.minimum_runtime,
            "minimum runtime",
        )
    ranks = [entry for entry in base.entries if entry.name != "source-priority-rank"]
    ids = {"pv": plant.pv, "battery": plant.battery, "generator": gen.generator}
    entries = ranks + [
        ViewEntry("generator-state", gen.state_address, current.value, DISCRETE_UNIT),
        ViewEntry("generator-running-for", gen.state_address, running_for, "min"),
        ViewEntry("generator-rated-power", f"{GENERATOR_RATED_POWER}@{gen.generator}", gen.rated, "kW"),
        ViewEntry("start-soc-threshold", f"{START_THRESHOLD}@{gen.generator}", gen.start_threshold, "%"),
        ViewEntry("stop-soc-threshold", f"{STOP_THRESHOLD}@{gen.generator}", gen.stop_threshold, "%"),
        ViewEntry("minimum-runtime", f"{MINIMUM_RUNTIME}@{gen.generator}", Fraction(gen.minimum_runtime), "min"),
        ViewEntry("fuel-in-tank", gen.fuel_address, context.stock(gen.fuel_address), "L"),
    ]
    for rank, source in enumerate(gen.order, start=1):
        entries.append(ViewEntry("source-priority-rank", ids[source], Fraction(rank), "rank"))
    return ControllerView(
        at_offset_minutes=base.at_offset_minutes,
        for_until_offset=base.for_until_offset,
        entries=tuple(entries),
    )


def _entry(view: ControllerView, name: str) -> ViewEntry:
    return next(item for item in view.entries if item.name == name)


def decide(view: ControllerView) -> ControlIntent:
    """Site policy for the generator, then the battery request, from the view."""
    soc_entry = _entry(view, "state-of-charge")
    soc = soc_entry.value
    reserve = view.value("reserve-in-effect")
    state_entry = _entry(view, "generator-state")
    state = state_entry.value
    running_for = view.value("generator-running-for")
    start = view.value("start-soc-threshold")
    stop = view.value("stop-soc-threshold")
    minimum = view.value("minimum-runtime")

    if state == STOPPED or state == FAILED:
        if soc <= start:
            run, why = RUN, (
                f"Site policy start: state of charge {soc} % is at or below "
                f"the start threshold {start} %"
            )
        else:
            run, why = STOP, (
                f"stay stopped: state of charge {soc} % is above the start "
                f"threshold {start} %"
            )
    elif state == STARTING:
        run, why = RUN, "keep starting: the start request stands through the start delay"
    elif running_for is not None and running_for >= minimum and soc >= stop:
        run, why = STOP, (
            f"Site policy stop: RUNNING {running_for} min, at least the minimum "
            f"runtime {minimum} min, and state of charge {soc} % is at or above "
            f"the stop threshold {stop} %"
        )
    elif running_for is not None and running_for < minimum:
        run, why = RUN, (
            f"keep running: RUNNING {running_for} min, below the minimum runtime "
            f"{minimum} min"
        )
    else:
        run, why = RUN, (
            f"keep running: state of charge {soc} % is below the stop threshold "
            f"{stop} %"
        )

    available = {
        "pv": view.value("pv-available"),
        "battery": Fraction(0),
        "generator": (
            view.value("generator-rated-power")
            if state == RUNNING and run == RUN
            else Fraction(0)
        ),
    }
    demand = sum(
        (item.value for item in view.entries if item.name == "load-demand"),
        Fraction(0),
    )
    ranks = {
        item.address: item.value
        for item in view.entries
        if item.name == "source-priority-rank"
    }
    battery_id = soc_entry.address.split("@", 1)[1]
    generator_id = state_entry.address.split("@", 1)[1]
    by_rank = sorted(ranks, key=lambda address: ranks[address])
    names = {battery_id: "battery", generator_id: "generator"}
    order = [names.get(address, "pv") for address in by_rank]
    ahead = sum(
        (available[source] for source in order[: order.index("battery")]),
        Fraction(0),
    )
    deficit = demand - ahead
    everything = available["pv"] + available["generator"]
    if deficit > 0 and soc > reserve:
        requested, reason = deficit, (
            f"discharge {deficit} kW: demand {demand} kW exceeds the {ahead} kW "
            f"the sources ahead of the battery in the Site's priority offer, and "
            f"the state of charge {soc} % is above the reserve {reserve} %"
        )
    elif everything > demand and soc < HUNDRED:
        requested, reason = demand - everything, (
            f"charge from the {everything - demand} kW the running sources "
            f"offer beyond demand {demand} kW"
        )
    elif deficit > 0:
        requested, reason = Fraction(0), (
            f"no discharge: the state of charge {soc} % is not above the "
            f"reserve {reserve} % in effect"
        )
    else:
        requested, reason = Fraction(0), "no battery power is called for"
    return ControlIntent(
        from_offset=view.at_offset_minutes,
        to_offset=view.for_until_offset,
        requests=(
            ControlRequest(
                address=soc_entry.address,
                quantity="battery-power",
                requested=requested,
                unit="kW",
                reason=reason,
            ),
            ControlRequest(
                address=state_entry.address,
                quantity="generator-run",
                requested=run,
                unit=DISCRETE_UNIT,
                reason=why,
            ),
        ),
    )


def _generator_request(intent: ControlIntent) -> ControlRequest:
    return next(item for item in intent.requests if item.quantity == "generator-run")


def commit(context: StepContext, intent: ControlIntent) -> tuple[TransitionRequest, ...]:
    """Phase F, before resolution: what the request just emitted at T causes."""
    plant, gen = _both(context)
    current = _state(context, gen).value
    request = _generator_request(intent)
    ref = f"control-intent@{intent.from_offset}:generator-run"
    if current == STOPPED and request.requested == RUN:
        return (TransitionRequest(gen.state_address, STARTING, request.reason, ref),)
    if current == RUNNING and request.requested == STOP:
        return (TransitionRequest(gen.state_address, STOPPED, request.reason, ref),)
    return ()


def resolve(context: StepContext, intent: ControlIntent) -> AcceptedFlowSet:
    """What the world accepts over the step, segment by segment."""
    plant, gen = _both(context)
    battery_request = intent.requests[0]
    run_request = _generator_request(intent)
    requested = battery_request.requested
    state = _state(context, gen)
    eta = plant.efficiency
    capacity = plant.capacity
    stored = context.stock(plant.soc_address) * capacity / HUNDRED
    stored_at_start = stored
    fuel = context.stock(gen.fuel_address)
    fuel_at_start = fuel

    totals: dict[str, Fraction] = {}
    per_load = {load: [Fraction(0), Fraction(0)] for load in plant.loads}
    limited: list[str] = []
    generator_limited: list[str] = []
    effective: list[EffectiveControl] = []
    segments = daytime._segments(context)

    def add(flow_id: str, energy: Fraction) -> None:
        totals[flow_id] = totals.get(flow_id, Fraction(0)) + energy

    def note(into: list[str], reason: str) -> None:
        if reason not in into:
            into.append(reason)

    if state.value == STARTING:
        note(generator_limited, f"STARTING: no output during the {gen.start_delay} min start delay")
    elif state.value == FAILED:
        note(generator_limited, "FAILED: inert, no output (failure causes are T035's)")
    elif state.value == STOPPED:
        note(generator_limited, "STOPPED: no output")

    for start, end in segments:
        hours = Fraction(end - start, 60)
        irradiance = daytime._required_level(context, daytime.IRRADIANCE_ADDRESS, start)
        potential, available = daytime._pv_available(plant, irradiance)
        reserve, origin, provenance = daytime._reserve_at(context, plant, start)
        effective.append(
            EffectiveControl(plant.reserve_address, start, end, reserve, "%", origin, provenance)
        )
        demands = {
            load: daytime._required_level(context, plant.load_address(load), start)
            for load in plant.loads
        }
        demand = sum(demands.values(), Fraction(0))

        generator_cap = Fraction(0)
        if state.value == RUNNING:
            by_fuel = fuel / gen.sfc / hours
            generator_cap = min(gen.rated, by_fuel)
            if by_fuel < gen.rated:
                note(generator_limited, f"fuel in tank ({fuel} L at the segment start)")

        discharge_cap = Fraction(0)
        if requested > 0:
            above_reserve = stored - reserve * capacity / HUNDRED
            by_energy = max(above_reserve, Fraction(0)) * eta / hours
            discharge_cap = min(requested, plant.discharge_limit, by_energy)
            if discharge_cap == plant.discharge_limit and requested > plant.discharge_limit:
                note(limited, f"pcs-discharge-limit {plant.discharge_limit} kW")
            if by_energy < min(requested, plant.discharge_limit):
                note(limited, f"energy above the reserve in effect ({reserve} %)")
        charge_cap = Fraction(0)
        if requested < 0:
            by_energy = (capacity - stored) / (eta * hours)
            charge_cap = min(-requested, plant.charge_limit, by_energy)
            if charge_cap == plant.charge_limit and -requested > plant.charge_limit:
                note(limited, f"pcs-charge-limit {plant.charge_limit} kW")
            if by_energy < min(-requested, plant.charge_limit):
                note(limited, "headroom below full")

        supply = {"pv": available, "battery": discharge_cap, "generator": generator_cap}
        served_total = min(demand, sum(supply.values(), Fraction(0)))
        remaining = served_total
        to_load = {"pv": Fraction(0), "battery": Fraction(0), "generator": Fraction(0)}
        for source in gen.order:
            take = min(supply[source], remaining)
            to_load[source] = take
            remaining -= take

        left = served_total
        for load in plant.loads:
            served = min(demands[load], left)
            left -= served
            per_load[load][0] += demands[load] * hours
            per_load[load][1] += served * hours

        # Charging: only while the battery is not discharging, from what the
        # charging sources have beyond load, in the Site's source order.
        to_battery = {"pv": Fraction(0), "generator": Fraction(0)}
        if to_load["battery"] == 0:
            room = charge_cap
            for source in gen.order:
                if source == "battery":
                    continue
                take = min(supply[source] - to_load[source], room)
                to_battery[source] = take
                room -= take

        generator_energy = (to_load["generator"] + to_battery["generator"]) * hours
        burned = generator_energy * gen.sfc
        fuel -= burned
        charged_ac = (to_battery["pv"] + to_battery["generator"]) * hours
        stored_in = charged_ac * eta
        delivered = to_load["battery"] * hours
        taken_out = delivered / eta
        stored = stored + stored_in - taken_out
        curtailed = available - to_load["pv"] - to_battery["pv"]

        add("pv_potential", potential * hours)
        add("inverter_clipping", (potential - available) * hours)
        add("pv_to_load", to_load["pv"] * hours)
        add("pv_to_battery", to_battery["pv"] * hours)
        add("curtailed_pv", curtailed * hours)
        add("generator_output", generator_energy)
        add("generator_to_load", to_load["generator"] * hours)
        add("generator_to_battery", to_battery["generator"] * hours)
        add("battery_charge_stored", stored_in)
        add("charge_loss", charged_ac - stored_in)
        add("battery_discharge_taken", taken_out)
        add("battery_to_load", delivered)
        add("discharge_loss", taken_out - delivered)
        add("load_demand", demand * hours)
        add("unserved_load", (demand - served_total) * hours)

    step_hours = Fraction(context.to_offset - context.from_offset, 60)
    pv, inv, bat, pcs, g = plant.pv, plant.inverter, plant.battery, plant.pcs, gen.generator

    def flow(flow_id: str, source: str, sink: str) -> AcceptedFlow:
        energy = totals[flow_id]
        return AcceptedFlow(flow_id, source, sink, energy, energy / step_hours)

    flows = [
        flow("pv_potential", pv, inv),
        flow("inverter_clipping", inv, "clipped"),
        flow("pv_to_load", inv, "loads"),
        flow("pv_to_battery", inv, pcs),
        flow("curtailed_pv", inv, "curtailed"),
        flow("generator_output", g, "generator-output"),
        flow("generator_to_load", g, "loads"),
        flow("generator_to_battery", g, pcs),
        flow("battery_charge_stored", pcs, bat),
        flow("charge_loss", pcs, "losses"),
        flow("battery_discharge_taken", bat, pcs),
        flow("battery_to_load", pcs, "loads"),
        flow("discharge_loss", pcs, "losses"),
        flow("load_demand", "loads", "demand"),
        flow("unserved_load", "demand", "unserved"),
    ]
    loads: list[LoadService] = []
    for rank, load in enumerate(plant.loads, start=1):
        demand_energy, served_energy = per_load[load]
        unserved_energy = demand_energy - served_energy
        flows.append(AcceptedFlow(f"demand:{load}", load, "demand", demand_energy, demand_energy / step_hours))
        flows.append(AcceptedFlow(f"served:{load}", "loads", load, served_energy, served_energy / step_hours))
        flows.append(AcceptedFlow(f"unserved:{load}", load, "unserved", unserved_energy, unserved_energy / step_hours))
        loads.append(
            LoadService(
                address=plant.load_address(load),
                priority_rank=rank,
                demand_energy=demand_energy,
                served_energy=served_energy,
                unserved_energy=unserved_energy,
                demand_power=demand_energy / step_hours,
                served_power=served_energy / step_hours,
                unserved_power=unserved_energy / step_hours,
            )
        )

    served_ids = tuple(f"served:{load}" for load in plant.loads)
    to_load_ids = ("pv_to_load", "battery_to_load", "generator_to_load")
    balances = [
        BalanceIdentity(
            "pv-potential",
            ("pv_potential",),
            ("pv_to_load", "pv_to_battery", "curtailed_pv", "inverter_clipping"),
        ),
        BalanceIdentity(
            "generator-output", ("generator_output",), ("generator_to_load", "generator_to_battery")
        ),
        BalanceIdentity(
            "battery-charge",
            ("pv_to_battery", "generator_to_battery"),
            ("battery_charge_stored", "charge_loss"),
        ),
        BalanceIdentity(
            "battery-discharge",
            ("battery_discharge_taken",),
            ("battery_to_load", "discharge_loss"),
        ),
        BalanceIdentity("load-service", ("load_demand",), to_load_ids + ("unserved_load",)),
        BalanceIdentity("served-by-load", to_load_ids, served_ids),
        BalanceIdentity(
            "site-sources-and-sinks",
            ("pv_potential", "battery_discharge_taken", "generator_output"),
            served_ids
            + (
                "curtailed_pv",
                "inverter_clipping",
                "battery_charge_stored",
                "charge_loss",
                "discharge_loss",
            ),
        ),
    ]
    for load in plant.loads:
        balances.append(
            BalanceIdentity(
                f"load:{load}", (f"demand:{load}",), (f"served:{load}", f"unserved:{load}")
            )
        )

    battery_net_ac = (
        totals["battery_to_load"] - totals["pv_to_battery"] - totals["generator_to_battery"]
    )
    accepted_power = battery_net_ac / step_hours
    if accepted_power != requested and not limited:
        limited.append("the demand or the sources across the step differed from the view at T")
    if state.value == RUNNING and totals["generator_output"] == 0:
        note(generator_limited, "RUNNING with nothing to absorb its output")

    return AcceptedFlowSet(
        from_offset=context.from_offset,
        to_offset=context.to_offset,
        segments=segments,
        flows=tuple(flows),
        controls=(
            AcceptedControl(
                address=battery_request.address,
                quantity=battery_request.quantity,
                requested=requested,
                accepted=accepted_power,
                unit="kW",
                limited_by=tuple(limited),
            ),
            AcceptedControl(
                address=run_request.address,
                quantity=run_request.quantity,
                requested=run_request.requested,
                accepted=state.value,
                unit=DISCRETE_UNIT,
                limited_by=tuple(generator_limited),
            ),
        ),
        loads=tuple(loads),
        effective_controls=tuple(effective),
        balances=tuple(balances),
        stock_accounts=(
            StockAccount(
                address=plant.soc_address,
                delta=(stored - stored_at_start) * HUNDRED / capacity,
                energy_per_unit=capacity / HUNDRED,
                inflows=("battery_charge_stored",),
                outflows=("battery_discharge_taken",),
            ),
            StockAccount(
                address=gen.fuel_address,
                delta=fuel - fuel_at_start,
                energy_per_unit=1 / gen.sfc,
                inflows=(),
                outflows=("generator_output",),
            ),
        ),
        interval_energies=tuple(
            sorted(
                [
                    (f"{daytime.PV_AC_POWER}@{inv}", totals["pv_to_load"] + totals["pv_to_battery"]),
                    (f"{daytime.BATTERY_AC_POWER}@{pcs}", battery_net_ac),
                ]
                + [
                    (f"{daytime.LOAD_SERVED_POWER}@{load}", per_load[load][1])
                    for load in plant.loads
                ]
            )
        ),
        notes=(LINEAR_FUEL_NOTE,),
    )


MINI_GRID_COUPLING = Coupling(
    statement=(
        "The daytime controller and cascade, plus a generator the Site's "
        "frozen policy starts and stops, dispatched in the Site's frozen "
        "source priority, burning fuel for accepted energy."
    ),
    prepare=prepare,
    view=view,
    decide=decide,
    resolve=resolve,
    due=due,
    commit=commit,
)

MINI_GRID_MODEL = ModelSpec(
    model_profile_id="mini-grid",
    model_profile_version=1,
    statement=(
        "Models one PV array behind one inverter, one battery behind one PCS, "
        "any number of addressed loads, and one generator with its fuel tank "
        "and lifecycle, under the Site's frozen control policy."
    ),
    handlers=daytime.HANDLERS + GENERATOR_HANDLERS,
    laws=(),
    component_relations=daytime.RELATIONS + GENERATOR_RELATIONS,
    coupling=MINI_GRID_COUPLING,
    measured_interval_states=frozenset(
        {daytime.PV_AC_POWER, daytime.BATTERY_AC_POWER, daytime.LOAD_SERVED_POWER}
    ),
    discrete_states=(GENERATOR_LIFECYCLE,),
)
