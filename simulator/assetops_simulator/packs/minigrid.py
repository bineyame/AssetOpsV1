"""The daytime mini-grid world: PV, a battery, and addressed loads (T024).

The first electrical world, and the smallest one that makes dispatch mean
anything. It is the simulator half of `DAYTIME_MINI_GRID_MODEL` on the product
side; the conformance test in `host/tests` is what makes the two one claim.

## What it models

- **PV potential** is the array's rated power times plane-of-array irradiance
  over 1000 W/m2 - DC, linear, no temperature derate. The inverter passes at
  most its AC limit; what it cannot pass is `inverter_clipping`.
- **Load demand** is forced per load address. Two loads of one type are two
  addresses with two demands, and nothing sums them before service is decided.
- **The battery** holds a state of charge in %. Its energy is that share of the
  capacity. Charging stores `efficiency` of the AC energy taken in; discharging
  delivers `efficiency` of the stored energy taken out. The PCS limits the AC
  power each way.
- **The controller** reads a local view at T and requests a battery power: to
  discharge the deficit it sees, if the state of charge is above the reserve in
  effect; to charge the surplus it sees, if the battery is not full. It knows no
  PCS limit - which is exactly how a request of 30 kW meets a 22 kW PCS.
- **The resolver** is a declared cascade (execution contract 9,
  `resolver-is-a-declared-cascade`): sources serve loads in the Site's source
  priority, loads are served in its critical-load priority, the battery
  discharges within the request, the PCS limit and the energy above the reserve
  in effect, it charges from PV surplus within the request, the PCS limit and
  the headroom, and PV nobody can use is curtailed.

A step whose inputs change inside it - a forcing window starting or ending off
the step grid - is evaluated in segments split at those instants, with the
state of charge carried between them (`a-step-splits-where-its-inputs-change`).

## What it does not model

The generator. This is a generator-stopped daytime baseline; the source
priority names the generator because it is a fact about the Site, and this
model skips it and says so. T025 adds the generator lifecycle.

Every number is an exact `Fraction`. There is no tolerance anywhere, because
the kernel checks the balances exactly.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from assetops_contracts.control import (
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
    ModelSpec,
    StateHandler,
    StepContext,
)
from assetops_simulator.packs.fuel import PhysicallyUnacceptable

IRRADIANCE = "plane-of-array-irradiance"
LOAD_DEMAND = "load-demand"
STATE_OF_CHARGE = "battery-state-of-charge"
RESERVE = "battery-reserve-state-of-charge"
PV_RATED_POWER = "pv-rated-power"
INVERTER_LIMIT = "inverter-ac-limit"
CAPACITY = "battery-energy-capacity"
CHARGE_LIMIT = "pcs-charge-limit"
DISCHARGE_LIMIT = "pcs-discharge-limit"
EFFICIENCY = "pcs-conversion-efficiency"

#: The interval measurements this model publishes, by state key.
PV_AC_POWER = "pv-ac-power"
BATTERY_AC_POWER = "battery-ac-power"
LOAD_SERVED_POWER = "load-served-power"

SOURCE_PRIORITY = "source-priority"
CRITICAL_LOAD_PRIORITY = "critical-load-priority"

IRRADIANCE_ADDRESS = f"site:{IRRADIANCE}"
STANDARD_IRRADIANCE = Fraction(1000)
HUNDRED = Fraction(100)


# --- Handlers ----------------------------------------------------------------


def _non_negative(what: str, unit: str):
    def accept(value: Fraction, *_: object) -> Fraction:
        if value < 0:
            raise PhysicallyUnacceptable(
                f"{what} of {value} {unit} is not a value the world can have"
            )
        return value

    return accept


def _percentage(what: str):
    def accept(value: Fraction, *_: object) -> Fraction:
        if not 0 <= value <= 100:
            raise PhysicallyUnacceptable(
                f"{what} of {value} % is not a share of a battery"
            )
        return value

    return accept


def _efficiency(value: Fraction) -> Fraction:
    if not 0 < value <= 100:
        raise PhysicallyUnacceptable(
            f"a conversion efficiency of {value} % is not one a PCS can have: "
            "above nothing and at most all of it"
        )
    return value


def _capacity(value: Fraction) -> Fraction:
    if value <= 0:
        raise PhysicallyUnacceptable(
            f"a battery energy capacity of {value} kWh stores nothing"
        )
    return value


def _forced_level(what: str, unit: str):
    """A forcing handler: a level over the part of a step it covers.

    The kernel calls it with the declared level and the exposed minutes and
    records the exposure. What it returns is that level times the exposure in
    hours, which nothing in this model reads - the resolver reads the
    exposures themselves, segment by segment.
    """

    check = _non_negative(what, unit)

    def consume(value: Fraction, exposed_minutes: int) -> Fraction:
        return check(value) * Fraction(exposed_minutes, 60)

    return consume


def _apply_to_stock(current: Fraction, delta: Fraction) -> Fraction:
    return current + delta


def _sample(value: Fraction, phase_id: str) -> Fraction:
    if phase_id != "sample-and-publish":
        raise PhysicallyUnacceptable(
            f"a state-of-charge reading was asked for during {phase_id!r}; a "
            "reading timestamped T is taken in the sampling phase only"
        )
    return value


def _coefficient(state_key: str, handler_id: str, dimension: str, accept, statement: str) -> StateHandler:
    return StateHandler(
        handler_id=handler_id,
        state_key=state_key,
        scope="COMPONENT",
        role="CAUSAL_INPUT",
        kind="COEFFICIENT",
        dimension=dimension,
        statement=statement,
        consume=accept,
    )


HANDLERS: tuple[StateHandler, ...] = (
    StateHandler(
        handler_id="irradiance-forcing",
        state_key=IRRADIANCE,
        scope="SITE",
        role="FORCING_INPUT",
        kind="FORCING",
        dimension="IRRADIANCE",
        statement="Plane-of-array irradiance, forced across declared windows.",
        consume=_forced_level("an irradiance", "W/m2"),
    ),
    StateHandler(
        handler_id="load-demand-forcing",
        state_key=LOAD_DEMAND,
        scope="COMPONENT",
        role="FORCING_INPUT",
        kind="FORCING",
        dimension="POWER",
        statement="One load's demand, forced at that load's own address.",
        consume=_forced_level("a load demand", "kW"),
    ),
    StateHandler(
        handler_id="battery-state-of-charge-stock",
        state_key=STATE_OF_CHARGE,
        scope="COMPONENT",
        role="CAUSAL_INPUT",
        kind="STOCK",
        dimension="FRACTION",
        floor=Fraction(0),
        floor_bound_case_id="battery-state-of-charge-limits",
        ceiling=Fraction(100),
        ceiling_bound_case_id="battery-state-of-charge-limits",
        statement=(
            "The battery's state of charge persists across steps, is "
            "initialized explicitly by the scenario, and moves only under "
            "accepted charge and discharge."
        ),
        consume=_apply_to_stock,
        initialize=_percentage("a starting state of charge"),
    ),
    StateHandler(
        handler_id="battery-state-of-charge-state-signal",
        state_key=STATE_OF_CHARGE,
        scope="COMPONENT",
        role="REPORTED_OBSERVATION",
        kind="STATE_SAMPLE",
        dimension="FRACTION",
        statement="The state of charge sampled at T, after T's events.",
        consume=_sample,
    ),
    _coefficient(
        RESERVE,
        "battery-reserve-baseline",
        "FRACTION",
        _percentage("a reserve"),
        "The frozen baseline reserve, answered by the Foundation.",
    ),
    StateHandler(
        handler_id="battery-reserve-override-forcing",
        state_key=RESERVE,
        scope="COMPONENT",
        role="FORCING_INPUT",
        kind="FORCING",
        dimension="FRACTION",
        statement=(
            "A scenario override of the reserve, replacing the baseline "
            "inside its window only."
        ),
        consume=_forced_level("a reserve override", "%"),
    ),
    _coefficient(
        PV_RATED_POWER,
        "pv-rated-power-coefficient",
        "POWER",
        _non_negative("a PV rated power", "kW"),
        "The array's DC output at 1000 W/m2.",
    ),
    _coefficient(
        INVERTER_LIMIT,
        "inverter-ac-limit-coefficient",
        "POWER",
        _non_negative("an inverter limit", "kW"),
        "The most AC power the inverter passes.",
    ),
    _coefficient(
        CAPACITY,
        "battery-energy-capacity-coefficient",
        "ENERGY",
        _capacity,
        "The battery's energy at 100 % state of charge.",
    ),
    _coefficient(
        CHARGE_LIMIT,
        "pcs-charge-limit-coefficient",
        "POWER",
        _non_negative("a PCS charge limit", "kW"),
        "The most AC power the PCS takes in while charging.",
    ),
    _coefficient(
        DISCHARGE_LIMIT,
        "pcs-discharge-limit-coefficient",
        "POWER",
        _non_negative("a PCS discharge limit", "kW"),
        "The most AC power the PCS delivers while discharging.",
    ),
    _coefficient(
        EFFICIENCY,
        "pcs-conversion-efficiency-coefficient",
        "FRACTION",
        _efficiency,
        "The PCS's one-way efficiency, applied in each direction.",
    ),
)

RELATIONS: tuple[ComponentRelation, ...] = (
    ComponentRelation(
        relation_id="pv-array",
        display_name="PV array",
        state_keys=frozenset({PV_RATED_POWER}),
        statement="The array's rated power is a fact about one array.",
    ),
    ComponentRelation(
        relation_id="pv-inverter",
        display_name="PV inverter",
        state_keys=frozenset({INVERTER_LIMIT}),
        statement="The inverter's AC limit is a fact about one inverter.",
    ),
    ComponentRelation(
        relation_id="battery",
        display_name="battery",
        state_keys=frozenset({STATE_OF_CHARGE, RESERVE, CAPACITY}),
        statement=(
            "A state of charge, the reserve below which it is not discharged "
            "and the capacity it is a share of are three facts about one "
            "battery."
        ),
    ),
    ComponentRelation(
        relation_id="battery-pcs",
        display_name="battery PCS",
        state_keys=frozenset({CHARGE_LIMIT, DISCHARGE_LIMIT, EFFICIENCY}),
        statement="The PCS's limits and efficiency are facts about one PCS.",
    ),
    ComponentRelation(
        relation_id="load",
        display_name="load",
        state_keys=frozenset({LOAD_DEMAND}),
        statement=(
            "Each load's demand is a fact about that load. There are many "
            "loads, which is the point: two of one type stay two."
        ),
        many=True,
    ),
)


# --- The plant, as this run carries it ----------------------------------------


def _component(address: str) -> str:
    return address.split("@", 1)[1] if "@" in address else address


@dataclass(frozen=True)
class _Plant:
    pv: str
    inverter: str
    battery: str
    pcs: str
    rated: Fraction
    inverter_limit: Fraction
    capacity: Fraction
    charge_limit: Fraction
    discharge_limit: Fraction
    efficiency: Fraction
    reserve_baseline: Fraction
    loads: tuple[str, ...]
    source_order: tuple[str, ...]
    skipped_sources: tuple[str, ...]

    @property
    def soc_address(self) -> str:
        return f"{STATE_OF_CHARGE}@{self.battery}"

    @property
    def reserve_address(self) -> str:
        return f"{RESERVE}@{self.battery}"

    def load_address(self, load: str) -> str:
        return f"{LOAD_DEMAND}@{load}"


def _one(context: StepContext, state_key: str, what: str) -> tuple[str, Fraction]:
    found = [
        (address, value)
        for address, value in context.coefficients
        if address.split("@", 1)[0] == state_key
    ]
    if len(found) != 1:
        raise CouplingRefused(
            "TOPOLOGY_INCONSISTENT" if found else "INITIAL_STATE_UNANSWERED",
            state_key,
            f"this model relates exactly one {what} and the frozen run carries "
            f"{len(found)} answers for {state_key}",
        )
    return found[0]


def _plant(context: StepContext) -> _Plant:
    pv, rated = _one(context, PV_RATED_POWER, "PV array")
    inverter, limit = _one(context, INVERTER_LIMIT, "PV inverter")
    battery, capacity = _one(context, CAPACITY, "battery")
    pcs, charge = _one(context, CHARGE_LIMIT, "battery PCS")
    _, discharge = _one(context, DISCHARGE_LIMIT, "battery PCS")
    _, efficiency = _one(context, EFFICIENCY, "battery PCS")
    reserve_address, reserve = _one(context, RESERVE, "battery")

    battery_id = _component(battery)
    if _component(reserve_address) != battery_id:
        raise CouplingRefused(
            "TOPOLOGY_INCONSISTENT",
            reserve_address,
            "the reserve and the capacity name two different batteries",
        )
    soc_address = f"{STATE_OF_CHARGE}@{battery_id}"
    if context.stock(soc_address) is None:
        raise CouplingRefused(
            "INITIAL_STATE_UNANSWERED",
            soc_address,
            "the battery's state of charge at run start is not initialized; it "
            "is never inferred from the reserve or the capacity",
        )

    loads_control = context.site_control(CRITICAL_LOAD_PRIORITY)
    sources_control = context.site_control(SOURCE_PRIORITY)
    for key, control in (
        (CRITICAL_LOAD_PRIORITY, loads_control),
        (SOURCE_PRIORITY, sources_control),
    ):
        if control is None:
            raise CouplingRefused(
                "INITIAL_STATE_UNANSWERED",
                f"site-control:{key}",
                "the controller needs this Site Control and the run froze none",
            )

    modelled = {_component(pv): "pv", battery_id: "battery"}
    order = tuple(
        modelled[member]
        for member in sources_control.members
        if member in modelled
    )
    skipped = tuple(
        member for member in sources_control.members if member not in modelled
    )
    if sorted(order) != ["battery", "pv"]:
        raise CouplingRefused(
            "TOPOLOGY_INCONSISTENT",
            f"site-control:{SOURCE_PRIORITY}",
            "the source priority must name this run's PV array and battery",
            f"it names {list(sources_control.members)}",
        )

    return _Plant(
        pv=_component(pv),
        inverter=_component(inverter),
        battery=battery_id,
        pcs=_component(pcs),
        rated=rated,
        inverter_limit=limit,
        capacity=capacity,
        charge_limit=charge,
        discharge_limit=discharge,
        efficiency=efficiency / HUNDRED,
        reserve_baseline=reserve,
        loads=tuple(loads_control.members),
        source_order=order,
        skipped_sources=skipped,
    )


def _level_at(context: StepContext, address: str, instant: int) -> tuple[Fraction, str] | None:
    """The level a forcing holds across the instant, or nothing."""
    for exposure in context.exposures_of(address):
        if exposure.from_offset <= instant < exposure.to_offset:
            return exposure.value, exposure.event_id
    return None


def _required_level(context: StepContext, address: str, instant: int) -> Fraction:
    found = _level_at(context, address, instant)
    if found is None:
        raise CouplingRefused(
            "FORCING_NOT_AVAILABLE",
            address,
            f"no declared window provides {address} at offset {instant}; a "
            "forcing outside its window is unavailable, never zero",
        )
    return found[0]


def _reserve_at(
    context: StepContext, plant: _Plant, instant: int
) -> tuple[Fraction, str, str]:
    """The reserve in effect at an instant: an override inside its window,
    the frozen baseline everywhere else (`a-control-override-replaces-its-
    baseline`)."""
    found = _level_at(context, plant.reserve_address, instant)
    if found is None:
        return (
            plant.reserve_baseline,
            "BASELINE",
            "frozen Foundation answer (reserve-state-of-charge)",
        )
    value, event_id = found
    if not 0 <= value <= 100:
        raise PhysicallyUnacceptable(
            f"a reserve override of {value} % is not a share of a battery"
        )
    return value, "OVERRIDE", f"scenario override {event_id}"


def _pv_available(plant: _Plant, irradiance: Fraction) -> tuple[Fraction, Fraction]:
    potential = plant.rated * irradiance / STANDARD_IRRADIANCE
    return potential, min(potential, plant.inverter_limit)


# --- The three callables -----------------------------------------------------


def prepare(context: StepContext) -> None:
    """Refuse, before the first boundary, a run this model cannot execute."""
    plant = _plant(context)
    for load in plant.loads:
        if not context.exposures_of(plant.load_address(load)):
            raise CouplingRefused(
                "FORCING_NOT_AVAILABLE",
                plant.load_address(load),
                f"load {load} is in the critical-load priority and the run "
                "declares no demand for it anywhere",
            )
    if not context.exposures_of(IRRADIANCE_ADDRESS):
        raise CouplingRefused(
            "FORCING_NOT_AVAILABLE",
            IRRADIANCE_ADDRESS,
            "the run declares no irradiance anywhere, so PV has no potential",
        )
    forced_loads = {
        _component(item.address)
        for item in context.exposures
        if item.address.split("@", 1)[0] == LOAD_DEMAND
    }
    unknown = sorted(forced_loads - set(plant.loads))
    if unknown:
        raise CouplingRefused(
            "TOPOLOGY_INCONSISTENT",
            ", ".join(unknown),
            "demand is forced on loads the critical-load priority does not "
            "name, so nothing says where they are served",
        )


def view(context: StepContext) -> ControllerView:
    """The controller's local view at T - never a published reading."""
    plant = _plant(context)
    at = context.from_offset
    irradiance = _required_level(context, IRRADIANCE_ADDRESS, at)
    _, available = _pv_available(plant, irradiance)
    reserve, _, _ = _reserve_at(context, plant, at)
    entries = [
        ViewEntry("state-of-charge", plant.soc_address, context.stock(plant.soc_address), "%"),
        ViewEntry("reserve-in-effect", plant.reserve_address, reserve, "%"),
        ViewEntry("irradiance", IRRADIANCE_ADDRESS, irradiance, "W/m2"),
        ViewEntry("pv-available", f"{PV_AC_POWER}@{plant.inverter}", available, "kW"),
    ]
    for load in plant.loads:
        address = plant.load_address(load)
        entries.append(
            ViewEntry("load-demand", address, _required_level(context, address, at), "kW")
        )
    # The source priority, as ranks the controller can read: which of the
    # sources this model runs serves load first.
    for rank, source in enumerate(plant.source_order, start=1):
        component_id = plant.pv if source == "pv" else plant.battery
        entries.append(
            ViewEntry("source-priority-rank", component_id, Fraction(rank), "rank")
        )
    return ControllerView(
        at_offset_minutes=at,
        for_until_offset=context.to_offset,
        entries=tuple(entries),
    )


def decide(view: ControllerView) -> ControlIntent:
    """Request the battery power the view calls for. Knows no PCS limit."""
    soc_entry = next(item for item in view.entries if item.name == "state-of-charge")
    soc = soc_entry.value
    reserve = view.value("reserve-in-effect")
    available = view.value("pv-available")
    demand = sum(
        (item.value for item in view.entries if item.name == "load-demand"),
        Fraction(0),
    )
    net = demand - available
    ranks = {
        item.address: item.value
        for item in view.entries
        if item.name == "source-priority-rank"
    }
    battery_id = soc_entry.address.split("@", 1)[1]
    battery_first = ranks.get(battery_id, Fraction(2)) == 1
    if battery_first and demand > 0 and soc > reserve:
        # The Site's source priority puts the battery ahead of PV, so the
        # controller asks the battery for the whole demand and PV serves what
        # the battery cannot.
        return ControlIntent(
            from_offset=view.at_offset_minutes,
            to_offset=view.for_until_offset,
            requests=(
                ControlRequest(
                    address=soc_entry.address,
                    quantity="battery-power",
                    requested=demand,
                    unit="kW",
                    reason=(
                        f"discharge {demand} kW, the whole demand: the source "
                        "priority puts the battery ahead of PV and the state of "
                        f"charge {soc} % is above the reserve {reserve} %"
                    ),
                ),
            ),
        )
    if net > 0:
        if soc > reserve:
            requested, reason = net, (
                f"discharge the {net} kW deficit: demand {demand} kW exceeds "
                f"available PV {available} kW and the state of charge {soc} % "
                f"is above the reserve {reserve} %"
            )
        else:
            requested, reason = Fraction(0), (
                f"no discharge: the state of charge {soc} % is not above the "
                f"reserve {reserve} % in effect"
            )
    elif net < 0:
        if soc < HUNDRED:
            requested, reason = net, (
                f"charge from the {-net} kW surplus: available PV {available} "
                f"kW exceeds demand {demand} kW"
            )
        else:
            requested, reason = Fraction(0), "no charge: the battery is full"
    else:
        requested, reason = Fraction(0), "demand equals available PV"
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
        ),
    )


def _segments(context: StepContext) -> tuple[tuple[int, int], ...]:
    cuts = {context.from_offset, context.to_offset}
    for exposure in context.exposures:
        for instant in (exposure.from_offset, exposure.to_offset):
            if context.from_offset < instant < context.to_offset:
                cuts.add(instant)
    ordered = sorted(cuts)
    return tuple(zip(ordered, ordered[1:]))


def resolve(context: StepContext, intent: ControlIntent) -> AcceptedFlowSet:
    """What the world accepts over the step, segment by segment."""
    plant = _plant(context)
    request = intent.requests[0]
    requested = request.requested
    eta = plant.efficiency
    capacity = plant.capacity
    soc = context.stock(plant.soc_address)
    stored = soc * capacity / HUNDRED
    stored_at_start = stored

    totals: dict[str, Fraction] = {}
    per_load = {load: [Fraction(0), Fraction(0)] for load in plant.loads}
    limited: list[str] = []
    effective: list[EffectiveControl] = []
    segments = _segments(context)

    def add(flow_id: str, energy: Fraction) -> None:
        totals[flow_id] = totals.get(flow_id, Fraction(0)) + energy

    def note(reason: str) -> None:
        if reason not in limited:
            limited.append(reason)

    for start, end in segments:
        hours = Fraction(end - start, 60)
        irradiance = _required_level(context, IRRADIANCE_ADDRESS, start)
        potential, available = _pv_available(plant, irradiance)
        reserve, origin, provenance = _reserve_at(context, plant, start)
        effective.append(
            EffectiveControl(
                address=plant.reserve_address,
                from_offset=start,
                to_offset=end,
                value=reserve,
                unit="%",
                origin=origin,
                provenance=provenance,
            )
        )
        demands = {
            load: _required_level(context, plant.load_address(load), start)
            for load in plant.loads
        }
        demand = sum(demands.values(), Fraction(0))

        # Battery discharge capability over this segment, as AC power.
        discharge_cap = Fraction(0)
        if requested > 0:
            above_reserve = stored - reserve * capacity / HUNDRED
            by_energy = max(above_reserve, Fraction(0)) * eta / hours
            discharge_cap = min(requested, plant.discharge_limit, by_energy)
            if discharge_cap == plant.discharge_limit and requested > plant.discharge_limit:
                note(f"pcs-discharge-limit {plant.discharge_limit} kW")
            if by_energy < min(requested, plant.discharge_limit):
                note(f"energy above the reserve in effect ({reserve} %)")
        # Battery charge capability, as AC power taken in.
        charge_cap = Fraction(0)
        if requested < 0:
            headroom = capacity - stored
            by_energy = headroom / (eta * hours)
            charge_cap = min(-requested, plant.charge_limit, by_energy)
            if charge_cap == plant.charge_limit and -requested > plant.charge_limit:
                note(f"pcs-charge-limit {plant.charge_limit} kW")
            if by_energy < min(-requested, plant.charge_limit):
                note("headroom below full")

        supply = {"pv": available, "battery": discharge_cap}
        served_total = min(demand, available + discharge_cap)
        remaining = served_total
        from_source = {"pv": Fraction(0), "battery": Fraction(0)}
        for source in plant.source_order:
            take = min(supply[source], remaining)
            from_source[source] = take
            remaining -= take

        left = served_total
        for load in plant.loads:
            served = min(demands[load], left)
            left -= served
            per_load[load][0] += demands[load] * hours
            per_load[load][1] += served * hours

        pv_to_load = from_source["pv"]
        battery_to_load = from_source["battery"]
        surplus = available - pv_to_load
        pv_to_battery = (
            min(surplus, charge_cap) if battery_to_load == 0 else Fraction(0)
        )
        curtailed = surplus - pv_to_battery

        charged_ac = pv_to_battery * hours
        stored_in = charged_ac * eta
        delivered = battery_to_load * hours
        taken_out = delivered / eta
        stored = stored + stored_in - taken_out

        add("pv_potential", potential * hours)
        add("inverter_clipping", (potential - available) * hours)
        add("pv_to_load", pv_to_load * hours)
        add("pv_to_battery", charged_ac)
        add("curtailed_pv", curtailed * hours)
        add("battery_charge_stored", stored_in)
        add("charge_loss", charged_ac - stored_in)
        add("battery_discharge_taken", taken_out)
        add("battery_to_load", delivered)
        add("discharge_loss", taken_out - delivered)
        add("load_demand", demand * hours)
        add("unserved_load", (demand - served_total) * hours)

    step_hours = Fraction(context.to_offset - context.from_offset, 60)
    pv = plant.pv
    inv = plant.inverter
    bat = plant.battery
    pcs = plant.pcs

    def flow(flow_id: str, source: str, sink: str) -> AcceptedFlow:
        energy = totals[flow_id]
        return AcceptedFlow(flow_id, source, sink, energy, energy / step_hours)

    flows = [
        flow("pv_potential", pv, inv),
        flow("inverter_clipping", inv, "clipped"),
        flow("pv_to_load", inv, "loads"),
        flow("pv_to_battery", inv, pcs),
        flow("curtailed_pv", inv, "curtailed"),
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
    balances = [
        BalanceIdentity(
            "pv-potential",
            ("pv_potential",),
            ("pv_to_load", "pv_to_battery", "curtailed_pv", "inverter_clipping"),
        ),
        BalanceIdentity(
            "battery-charge", ("pv_to_battery",), ("battery_charge_stored", "charge_loss")
        ),
        BalanceIdentity(
            "battery-discharge",
            ("battery_discharge_taken",),
            ("battery_to_load", "discharge_loss"),
        ),
        BalanceIdentity(
            "load-service",
            ("load_demand",),
            ("pv_to_load", "battery_to_load", "unserved_load"),
        ),
        BalanceIdentity("served-by-load", ("pv_to_load", "battery_to_load"), served_ids),
        BalanceIdentity(
            "site-sources-and-sinks",
            ("pv_potential", "battery_discharge_taken"),
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

    delta_soc = (stored - stored_at_start) * HUNDRED / capacity
    battery_net_ac = totals["battery_to_load"] - totals["pv_to_battery"]
    accepted_power = battery_net_ac / step_hours
    if accepted_power != requested and not limited:
        limited.append(
            "the demand or PV surplus across the step differed from the view "
            "at T"
        )

    notes = tuple(
        f"source priority names {member}, which this model does not run; it is "
        "skipped (T025 adds the generator)"
        for member in plant.skipped_sources
    )
    return AcceptedFlowSet(
        from_offset=context.from_offset,
        to_offset=context.to_offset,
        segments=segments,
        flows=tuple(flows),
        controls=(
            AcceptedControl(
                address=request.address,
                quantity=request.quantity,
                requested=requested,
                accepted=accepted_power,
                unit="kW",
                limited_by=tuple(limited),
            ),
        ),
        loads=tuple(loads),
        effective_controls=tuple(effective),
        balances=tuple(balances),
        stock_accounts=(
            StockAccount(
                address=plant.soc_address,
                delta=delta_soc,
                energy_per_unit=capacity / HUNDRED,
                inflows=("battery_charge_stored",),
                outflows=("battery_discharge_taken",),
            ),
        ),
        interval_energies=tuple(
            sorted(
                [
                    (
                        f"{PV_AC_POWER}@{inv}",
                        totals["pv_to_load"] + totals["pv_to_battery"],
                    ),
                    (f"{BATTERY_AC_POWER}@{pcs}", battery_net_ac),
                ]
                + [
                    (f"{LOAD_SERVED_POWER}@{load}", per_load[load][1])
                    for load in plant.loads
                ]
            )
        ),
        notes=notes,
    )


DAYTIME_COUPLING = Coupling(
    statement=(
        "A controller that requests battery power from a local view, and a "
        "declared-cascade resolver that accepts what PV, the PCS, the battery's "
        "energy and reserve allow, serving loads in critical-load priority."
    ),
    prepare=prepare,
    view=view,
    decide=decide,
    resolve=resolve,
)

#: The model the daytime mini-grid profile declares, and its falsifier.
DAYTIME_MINI_GRID_MODEL = ModelSpec(
    model_profile_id="daytime-mini-grid",
    model_profile_version=1,
    statement=(
        "Models one PV array behind one inverter, one battery behind one PCS "
        "and any number of addressed loads, with a controller and a declared "
        "cascade resolver. The generator is not modelled."
    ),
    handlers=HANDLERS,
    laws=(),
    component_relations=RELATIONS,
    coupling=DAYTIME_COUPLING,
    measured_interval_states=frozenset(
        {PV_AC_POWER, BATTERY_AC_POWER, LOAD_SERVED_POWER}
    ),
)
