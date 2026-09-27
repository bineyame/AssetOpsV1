"""The boundary cycle, run against frozen content.

One function matters: `execute`, which walks a run's interval and returns the
private trajectory. Everything else here is one phase of the cycle.

## The phase order is read from the contract, not from this file's layout

`_PHASES` maps each `phase_id` in `BOUNDARY_CYCLE` to the function that runs it,
and the loop visits them in the contract's declared `sequence`. So the order is
the published ordinal rather than the order somebody wrote the calls in, a
constructor check fails if a phase in the contract has no function here, and a
tenth phase added to the contract stops this kernel until it is implemented
rather than being silently skipped. `BoundaryPhase.sequence` says it is "the
contract, not the tuple order"; this is what consuming it that way looks like.

## Where a bound is applied, and where it is checked

Phase 1 applies what is due at T and phase 8 checks invariants after the
evolution, and that pair reads two ways until one of them is ruled out. If a
bound were only applied at phase 8, the state at T that phase 2 declares to
exist - and that phase 3 samples - would be a volume above the tank's capacity,
and `fuel-tank-capacity` says the capacity "bounds the stored volume at every
step". So the policy is applied where the transition happens, at phase 1 for a
due event and at phase 7 for the evolution, and phase 8 verifies that no stock
is outside its bounds and that each step's change in a stock equals the changes
the records account for. A check that could never fail would be decoration; this
one fails if a handler and the records disagree, which is
`BALANCE_IDENTITY_VIOLATION`.

## Exact rational, once at the boundary and never again

Every number here is a `Fraction`. Authored floats were normalized once, by the
host adapter, through the contract's own input-boundary conversion. Nothing in
this module limits a denominator, converts to float, or rounds, which is what
makes `EXACT_RATIONAL` a description rather than an aspiration: 311/1000 times
45/4 is 2799/800, sixteen times over, and 430 - 55.98 is exactly 18701/50.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from typing import Callable

from assetops_contracts.execution_contract import (
    BOUNDARY_CYCLE,
    BOUND_CASES,
    NUMERIC_POLICY,
    EXECUTION_CONTRACT_VERSION,
    overlap_minutes,
    point_due_at,
    refuse_incompatible_execution,
    window_share_of_step,
)
from assetops_contracts.failures import (
    ExecutionFailure,
    KernelExecutionFailed,
    failure,
)
from assetops_contracts.trajectory import (
    AppliedEvent,
    BoundaryState,
    BoundedTransition,
    PrivateTrajectory,
    frozen_inputs_identity,
)
from assetops_contracts.world_inputs import (
    DeclaredCause,
    ForcingInput,
    FrozenWorldInputs,
)
from assetops_simulator.kernel.model import (
    KERNEL_VERSION,
    ExecutionLedger,
    ModelSpec,
    StateHandler,
)
from assetops_simulator.packs.fuel import (
    FUEL_TANK_CAPACITY,
    FUEL_TANK_VOLUME,
    GENERATOR_OUTPUT_POWER,
    GENERATOR_SPECIFIC_CONSUMPTION,
    MINIMAL_FUEL_MODEL,
    PhysicallyUnacceptable,
)

#: What each declared bound case commits a kernel to, by identity. Read from the
#: contract so a policy change there changes behaviour here rather than needing
#: to be copied.
POLICY_BY_BOUND_CASE = {case.case_id: case.policy for case in BOUND_CASES}


class _Stop(Exception):
    """Internal: a phase decided the run cannot continue."""

    def __init__(self, record: ExecutionFailure) -> None:
        super().__init__(record.kind)
        self.record = record


@dataclass
class _Bound:
    value: Fraction
    kind: str
    bound_case_id: str
    policy: str
    source_address: str


@dataclass
class _Contribution:
    """One change one instant or one step asks of one stock."""

    event_id: str
    direction: str
    quantity: Fraction
    share: Fraction
    origin: str


@dataclass
class _World:
    """Mutable execution state. Nothing outside this module holds one."""

    inputs: FrozenWorldInputs
    model: ModelSpec
    ledger: ExecutionLedger
    stocks: dict[str, Fraction] = field(default_factory=dict)
    coefficients: dict[str, Fraction] = field(default_factory=dict)
    upper: dict[str, _Bound] = field(default_factory=dict)
    lower: dict[str, _Bound] = field(default_factory=dict)
    tank_address: str = ""
    generator_address: str = ""
    boundaries: list[BoundaryState] = field(default_factory=list)
    applied: list[AppliedEvent] = field(default_factory=list)
    bounded: list[BoundedTransition] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    # Per-boundary scratch, rebuilt at every instant.
    offset: int = 0
    step_index: int = 0
    step_length: int = 0
    begins_a_step: bool = False
    forcings_now: dict[str, Fraction] = field(default_factory=dict)
    delivered_energy_now: dict[str, Fraction] = field(default_factory=dict)
    previous_delivered_energy: dict[str, Fraction] = field(
        default_factory=dict
    )
    previous_step_length: int = 0
    samples_now: dict[str, Fraction] = field(default_factory=dict)
    stocks_before_step: dict[str, Fraction] = field(default_factory=dict)
    step_contributions: dict[str, list[_Contribution]] = field(
        default_factory=dict
    )
    step_refusals: dict[str, Fraction] = field(default_factory=dict)


# --- Setup ------------------------------------------------------------------


def _instant(start_time: str, offset_minutes: int) -> str:
    """The simulated instant an offset names, in UTC.

    The interval's own instants are UTC on the frozen run, and the Site's zone
    lives on the Site binding where the Site answers for it. An offset is
    minutes from the start, so this is arithmetic rather than a second answer
    about what time zone a run is in.
    """
    parsed = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    moved = parsed.astimezone(timezone.utc) + timedelta(
        minutes=offset_minutes
    )
    return moved.strftime("%Y-%m-%dT%H:%M:%SZ")


def _entry_span(
    entry: ForcingInput | DeclaredCause, interval_minutes: int
) -> tuple[int, int]:
    """The half-open span an entry occupies, in offsets.

    An interval-wide entry starts at zero and holds until the interval ends, and
    declares no length of its own, because the length is the run's.
    """
    if entry.shape == "INTERVAL_WIDE":
        return 0, interval_minutes
    if entry.shape == "POINT":
        return entry.offset_minutes, entry.offset_minutes
    length = entry.duration_minutes or 0
    return entry.offset_minutes, entry.offset_minutes + length


def _refuse_entries_outside_the_interval(world: _World) -> None:
    interval = world.inputs.interval.duration_minutes
    for entry in world.inputs.causes + world.inputs.forcings:
        start, end = _entry_span(entry, interval)
        if start < 0 or start >= interval or end > interval:
            raise _Stop(
                failure(
                    "ENTRY_OUTSIDE_INTERVAL",
                    entry.event_id,
                    at_offset_minutes=entry.offset_minutes,
                    detail=(
                        f"the entry covers [{start}, {end}) and the run covers "
                        f"[0, {interval})",
                    ),
                )
            )


def _resolve_topology(world: _World) -> None:
    """Pair the one generator with the one tank, or say why it cannot.

    The model relates one of each and has no declared topology for two, so more
    than one of either is named rather than guessed at.
    """
    inputs = world.inputs
    tanks = sorted(
        set(inputs.addresses_of_state(FUEL_TANK_VOLUME))
        | set(inputs.addresses_of_state(FUEL_TANK_CAPACITY))
    )
    tank_components = sorted({_component_of(address) for address in tanks})
    generators = sorted(
        set(inputs.addresses_of_state(GENERATOR_OUTPUT_POWER))
        | set(inputs.addresses_of_state(GENERATOR_SPECIFIC_CONSUMPTION))
    )
    generator_components = sorted(
        {_component_of(address) for address in generators}
    )

    if len(tank_components) != 1:
        raise _Stop(
            failure(
                "TOPOLOGY_INCONSISTENT",
                ", ".join(tank_components) or "no fuel tank",
                detail=(
                    "this model relates one generator to one fuel tank and has "
                    "no declared topology telling it which tank each generator "
                    "burns from",
                ),
            )
        )
    if len(generator_components) != 1:
        raise _Stop(
            failure(
                "TOPOLOGY_INCONSISTENT",
                ", ".join(generator_components) or "no generator",
                detail=(
                    "this model relates one generator to one fuel tank and has "
                    "no declared topology telling it which tank each generator "
                    "burns from",
                ),
            )
        )

    world.tank_address = f"{FUEL_TANK_VOLUME}@{tank_components[0]}"
    world.generator_address = (
        f"{GENERATOR_OUTPUT_POWER}@{generator_components[0]}"
    )


def _component_of(address: str) -> str:
    """The component an address selects, or the site marker for a site fact."""
    if address.startswith("site:"):
        return "site"
    _, _, selector = address.partition("@")
    return selector or "(unaddressed)"


def _handler_or_stop(
    world: _World, state_key: str, role: str, address: str
) -> StateHandler | None:
    """The handler for a state and role, or a failure naming the address.

    The cross-reference the backlog asks for. An address the run recorded as an
    unsupported optional input may legitimately have no handler, and returns
    `None`; anything else with no handler stops the run, because a kernel that
    quietly skipped a declared state would have executed part of a scenario and
    reported a complete result.
    """
    handler = world.model.handler(state_key, role)
    if handler is not None:
        return handler
    if address in world.inputs.unmodelled_addresses:
        note = (
            f"{address} is recorded on the run as an unsupported optional "
            f"input and this model has no {role} handler for it, so nothing "
            "about this run models it"
        )
        if note not in world.notes:
            world.notes.append(note)
        return None
    raise _Stop(
        failure(
            "UNSUPPORTED_MODEL_STATE",
            address,
            detail=(
                f"model {world.model.model_profile_id} version "
                f"{world.model.model_profile_version} declares no {role} "
                f"handler for {state_key}, and the run does not record this "
                "address as an unsupported optional input either",
            ),
        )
    )


def _initialize(world: _World) -> None:
    """Initialize from frozen content, cross-referencing what is not modelled."""
    for entry in world.inputs.initial_values:
        handler = _handler_or_stop(
            world, entry.state_key, "CAUSAL_INPUT", entry.address
        )
        if handler is None:
            continue
        accept = (
            handler.initialize if handler.kind == "STOCK" else handler.consume
        )
        try:
            value = accept(entry.value)
        except PhysicallyUnacceptable as unacceptable:
            raise _Stop(
                failure(
                    "PHYSICAL_RESOLUTION_FAILURE",
                    entry.address,
                    detail=(str(unacceptable),),
                )
            ) from unacceptable
        world.ledger.record_handler(handler)

        if handler.kind == "STOCK":
            world.stocks[entry.address] = value
            if handler.floor is not None:
                world.lower[entry.address] = _Bound(
                    value=handler.floor,
                    kind="LOWER",
                    bound_case_id=handler.floor_bound_case_id or "",
                    policy=POLICY_BY_BOUND_CASE[
                        handler.floor_bound_case_id or ""
                    ],
                    source_address=(
                        f"model {world.model.model_profile_id} version "
                        f"{world.model.model_profile_version}"
                    ),
                )
        elif handler.kind == "COEFFICIENT":
            world.coefficients[entry.address] = value
        elif handler.kind == "BOUND_SOURCE":
            # The number is consumed here so the handler is genuinely reached
            # on initialization; which state it bounds comes from the declared
            # bound below, because that relationship is the document's.
            pass

    _resolve_declared_bounds(world)
    _require_handlers_for_every_entry(world)
    _require_an_initial_value_for_every_stock_a_cause_moves(world)


def _resolve_declared_bounds(world: _World) -> None:
    """Turn each declared bound into a number, through the model's handler.

    The declaration is the document's and the number is the site's
    (`D-2026-09-22-capacity-bound-source`). The host adapter has already paired
    them; what happens here is the model accepting the number as a bound on that
    kind of state, which is what makes the capacity handler executable rather
    than a label.
    """
    for bound in world.inputs.bounds:
        source = world.inputs.initial_value(bound.source_address)
        source_state = (
            source.state_key
            if source is not None
            else bound.source_address.split("@")[0]
        )
        handler = _handler_or_stop(
            world, source_state, "CAUSAL_INPUT", bound.source_address
        )
        if handler is None:
            continue
        try:
            value = handler.consume(bound.value)
        except PhysicallyUnacceptable as unacceptable:
            raise _Stop(
                failure(
                    "PHYSICAL_RESOLUTION_FAILURE",
                    bound.address,
                    detail=(str(unacceptable),),
                )
            ) from unacceptable
        world.ledger.record_handler(handler)
        resolved = _Bound(
            value=value,
            kind=bound.kind,
            bound_case_id=bound.bound_case_id,
            policy=POLICY_BY_BOUND_CASE[bound.bound_case_id],
            source_address=bound.source_address,
        )
        if bound.kind == "UPPER":
            world.upper[bound.address] = resolved
        else:
            world.lower[bound.address] = resolved


def _require_handlers_for_every_entry(world: _World) -> None:
    for forcing in world.inputs.forcings:
        _handler_or_stop(
            world, forcing.state_key, "FORCING_INPUT", forcing.address
        )
    for cause in world.inputs.causes:
        _handler_or_stop(
            world, cause.state_key, "CAUSAL_INPUT", cause.address
        )

    # A forcing the law requires, declared nowhere. Not held at a previous
    # value and not taken as zero: both would be a number nobody supplied.
    for law in world.model.laws:
        for handler_id in law.reads:
            handler = world.model.handler_by_id(handler_id)
            if handler.kind != "FORCING":
                continue
            declared = [
                forcing
                for forcing in world.inputs.forcings
                if forcing.state_key == handler.state_key
            ]
            if declared:
                continue
            raise _Stop(
                failure(
                    "FORCING_NOT_AVAILABLE",
                    handler.state_key,
                    detail=(
                        f"law {law.law_id} reads {handler.state_key} and the "
                        "frozen run declares no window for it",
                    ),
                )
            )


def _require_an_initial_value_for_every_stock_a_cause_moves(
    world: _World,
) -> None:
    for cause in world.inputs.causes:
        if cause.address in world.inputs.unmodelled_addresses:
            continue
        if cause.address in world.stocks:
            continue
        raise _Stop(
            failure(
                "INITIAL_STATE_UNANSWERED",
                cause.address,
                at_offset_minutes=cause.offset_minutes,
                detail=(
                    f"cause {cause.event_id} moves {cause.address} and the "
                    "frozen run carries no initial value for it",
                ),
            )
        )
    for law in world.model.laws:
        for handler_id in law.writes:
            handler = world.model.handler_by_id(handler_id)
            if handler.kind != "STOCK":
                continue
            for address in world.inputs.addresses_of_state(handler.state_key):
                if address in world.stocks:
                    continue
                raise _Stop(
                    failure(
                        "INITIAL_STATE_UNANSWERED",
                        address,
                        detail=(
                            f"law {law.law_id} moves that stock and the frozen "
                            "run carries no initial value for it",
                        ),
                    )
                )


def _note_reporting_path_conditions(world: _World) -> None:
    """Say that a reporting-path condition was withheld rather than dropped.

    A scenario forcing the fuel level sensor to report nothing is a condition on
    the path a reading travels. It moves no stock, carries no state effect and
    is not a world state, so it never reaches this kernel as a forcing - the
    publication profile answers for it and the observation transform is what
    makes the declaration true or false. The note is here because "this kernel
    did not model that" and "nothing modelled that" are different facts, and a
    trajectory that said neither would let a reader assume the first.
    """
    for address in world.inputs.reporting_path_addresses:
        world.notes.append(
            f"the run forces the reporting path at {address}; that is the "
            "publication profile's to model and no state of the world, so this "
            "kernel neither consumes it nor changes anything because of it"
        )


# --- The bound policy, applied where the transition happens -----------------


def _apply_contributions(
    world: _World,
    address: str,
    contributions: list[_Contribution],
    phase_id: str,
) -> None:
    """Apply one instant's or one step's group to one stock.

    `intra-instant-order`: the group has a net effect, a bound is evaluated on
    that net rather than between the members, and whether an ordering could have
    mattered is decided exactly by the two extremes. If neither extreme reaches
    a bound then no ordering does. If either does while the net stays inside,
    the group is ambiguous and this declines to answer rather than choosing an
    order.
    """
    if not contributions:
        return

    handler = world.model.handler(
        _state_key_of(address), "CAUSAL_INPUT"
    )
    if handler is None:  # pragma: no cover - guarded during initialization
        raise _Stop(
            failure("UNSUPPORTED_MODEL_STATE", address)
        )

    current = world.stocks[address]
    increases = sum(
        (item.quantity for item in contributions if item.direction == "INCREASE"),
        Fraction(0),
    )
    decreases = sum(
        (item.quantity for item in contributions if item.direction == "DECREASE"),
        Fraction(0),
    )

    upper = world.upper.get(address)
    lower = world.lower.get(address)
    requested = increases - decreases
    net_after = handler.consume(current, requested)
    world.ledger.record_handler(handler)

    reached: _Bound | None = None
    if upper is not None and net_after > upper.value:
        reached = upper
    elif lower is not None and net_after < lower.value:
        reached = lower

    if reached is None:
        peak = current + increases
        trough = current - decreases
        if (upper is not None and peak > upper.value) or (
            lower is not None and trough < lower.value
        ):
            raise _Stop(
                failure(
                    "ORDER_DEPENDENT_GROUP",
                    address,
                    at_offset_minutes=world.offset,
                    detail=tuple(
                        f"{item.event_id} {item.direction} {item.quantity}"
                        for item in contributions
                    ),
                )
            )
        world.stocks[address] = net_after
        _record_contributions(world, address, contributions, phase_id)
        return

    if reached.policy == "FAIL_RUN":
        raise _Stop(
            failure(
                "INTEGRATION_BOUND_FAILURE",
                address,
                at_offset_minutes=world.offset,
                detail=(
                    f"bound case {reached.bound_case_id} is {reached.policy}",
                    f"the group would take the stock to {net_after} against a "
                    f"{reached.kind} bound of {reached.value}",
                )
                + tuple(
                    f"{item.event_id} {item.direction} {item.quantity}"
                    for item in contributions
                ),
            )
        )

    if reached.policy != "BOUNDED_AND_RECORDED":  # pragma: no cover
        raise _Stop(
            failure(
                "INTEGRATION_BOUND_FAILURE",
                address,
                at_offset_minutes=world.offset,
                detail=(
                    f"bound case {reached.bound_case_id} carries policy "
                    f"{reached.policy}, which no kernel phase can apply",
                ),
            )
        )

    accepted_value = reached.value
    refused = net_after - accepted_value
    world.stocks[address] = accepted_value
    world.bounded.append(
        BoundedTransition(
            address=address,
            at_offset_minutes=world.offset,
            bound_case_id=reached.bound_case_id,
            bound_kind=reached.kind,
            bound_value=reached.value,
            requested=net_after,
            accepted=accepted_value,
            refused=refused,
            event_ids=tuple(item.event_id for item in contributions),
        )
    )
    world.step_refusals[address] = (
        world.step_refusals.get(address, Fraction(0)) + refused
    )
    _record_contributions(world, address, contributions, phase_id)


def _record_contributions(
    world: _World,
    address: str,
    contributions: list[_Contribution],
    phase_id: str,
) -> None:
    for item in contributions:
        world.applied.append(
            AppliedEvent(
                event_id=item.event_id,
                address=address,
                direction=item.direction,
                at_offset_minutes=world.offset,
                share=item.share,
                declared=item.quantity,
                origin=item.origin,
                phase_id=phase_id,
            )
        )
        world.step_contributions.setdefault(address, []).append(item)


def _state_key_of(address: str) -> str:
    without_scope = address.split(":", 1)[-1]
    return without_scope.split("@", 1)[0]


# --- The nine phases --------------------------------------------------------


def _phase_apply_events(world: _World) -> None:
    """A. Everything due exactly at T, applied before anything reads the world."""
    world.stocks_before_step = dict(world.stocks)
    world.step_contributions = {}
    world.step_refusals = {}

    if world.offset >= world.inputs.interval.duration_minutes:
        # The end instant is outside a half-open interval, so nothing is due
        # there. Run setup refuses a document with an entry outside the
        # interval, and `_refuse_entries_outside_the_interval` refuses frozen
        # inputs carrying one, so there is nothing to apply and nothing to skip.
        return

    step_starts = world.inputs.interval.step_starts
    grouped: dict[str, list[_Contribution]] = {}
    for cause in world.inputs.causes:
        if cause.shape != "POINT":
            continue
        due = point_due_at(
            step_starts,
            world.inputs.interval.timestep_minutes,
            cause.offset_minutes,
        )
        if due != world.offset:
            continue
        if cause.address in world.inputs.unmodelled_addresses:
            continue
        grouped.setdefault(cause.address, []).append(
            _Contribution(
                event_id=cause.event_id,
                direction=cause.direction,
                quantity=cause.quantity,
                share=Fraction(1),
                origin="DECLARED_CAUSE",
            )
        )

    for address in sorted(grouped):
        _apply_contributions(world, address, grouped[address], "apply-events")


def _phase_state_at_t(world: _World) -> None:
    """B. The post-event state at T exists, and every later phase reads it."""
    return None


def _phase_sample_and_publish(world: _World) -> None:
    """C. Sample the state at T, and attach the interval that has just ended.

    The interval measurement is attached only when a span precedes T, which at
    the run's first boundary it does not. No profile in this build can declare
    an initial historical window to measure over instead - neither profile record
    carries such a field - so this phase has no branch for one.
    """
    world.samples_now = {}
    for handler in world.model.handlers_of_kind("STATE_SAMPLE"):
        for address, value in world.stocks.items():
            if _state_key_of(address) != handler.state_key:
                continue
            try:
                world.samples_now[address] = handler.consume(
                    value, "sample-and-publish"
                )
            except PhysicallyUnacceptable as unacceptable:
                raise _Stop(
                    failure(
                        "PHYSICAL_RESOLUTION_FAILURE",
                        address,
                        at_offset_minutes=world.offset,
                        detail=(str(unacceptable),),
                    )
                ) from unacceptable
            world.ledger.record_handler(handler)


def _phase_controller_view(world: _World) -> None:
    """D. Build the controller's view at T.

    This model declares no controller, so there is no view to build and nothing
    here reads or writes world state. The phase is visited rather than omitted,
    because the cycle's order is the contract's and a kernel that skipped a
    phase it has nothing to do in would have no place to put the first
    controller when one arrives.
    """
    note = (
        "this model declares no controller, so the controller view and intent "
        "phases build nothing and mutate nothing"
    )
    if note not in world.notes:
        world.notes.append(note)


def _phase_controller_intent(world: _World) -> None:
    """E. Emit intent for [T, T+dt). No controller, so no intent."""
    return None


def _phase_physical_acceptance(world: _World) -> None:
    """F. Resolve what the world accepts over the step about to be evolved.

    In this world the accepted flow is the dispatch the scenario forces, read
    only in the steps its window concerns. A forcing outside its window gets no
    entry at all, which is unavailable: not zero, and not held at the value
    inside the window.
    """
    world.forcings_now = {}
    world.delivered_energy_now = {}
    if not world.begins_a_step:
        return

    interval = world.inputs.interval.duration_minutes
    by_address: dict[str, list[ForcingInput]] = {}
    for forcing in world.inputs.forcings:
        if forcing.address in world.inputs.unmodelled_addresses:
            continue
        handler = world.model.handler(forcing.state_key, "FORCING_INPUT")
        if handler is None:
            continue
        start, end = _entry_span(forcing, interval)
        exposed = overlap_minutes(
            world.offset, world.step_length, start, end - start
        )
        if exposed == 0:
            continue
        by_address.setdefault(forcing.address, []).append(forcing)

    for address, declared in sorted(by_address.items()):
        if len(declared) > 1:
            raise _Stop(
                failure(
                    "FORCING_VALUE_AMBIGUOUS",
                    address,
                    at_offset_minutes=world.offset,
                    detail=tuple(
                        f"{forcing.event_id}/{forcing.parameter_id} = "
                        f"{forcing.value} {forcing.canonical_unit}"
                        for forcing in declared
                    ),
                )
            )
        forcing = declared[0]
        handler = world.model.handler(forcing.state_key, "FORCING_INPUT")
        start, end = _entry_span(forcing, interval)
        exposed = overlap_minutes(
            world.offset, world.step_length, start, end - start
        )
        try:
            world.delivered_energy_now[address] = handler.consume(
                forcing.value, exposed
            )
        except PhysicallyUnacceptable as unacceptable:
            raise _Stop(
                failure(
                    "PHYSICAL_RESOLUTION_FAILURE",
                    address,
                    at_offset_minutes=world.offset,
                    detail=(str(unacceptable),),
                )
            ) from unacceptable
        world.ledger.record_handler(handler)
        world.forcings_now[address] = forcing.value


def _phase_evolve(world: _World) -> None:
    """G. Integrate over [T, T+dt): declared window shares, then the laws."""
    if not world.begins_a_step:
        return

    interval = world.inputs.interval.duration_minutes
    grouped: dict[str, list[_Contribution]] = {}

    for cause in world.inputs.causes:
        if cause.shape == "POINT":
            continue
        if cause.address in world.inputs.unmodelled_addresses:
            continue
        start, end = _entry_span(cause, interval)
        share = window_share_of_step(
            world.offset, world.step_length, start, end - start
        )
        if share == 0:
            continue
        grouped.setdefault(cause.address, []).append(
            _Contribution(
                event_id=cause.event_id,
                direction=cause.direction,
                quantity=cause.quantity * share,
                share=share,
                origin="DECLARED_CAUSE",
            )
        )

    for law in world.model.laws:
        moved = _run_law(world, law)
        if moved is None:
            continue
        address, contribution = moved
        grouped.setdefault(address, []).append(contribution)

    for address in sorted(grouped):
        _apply_contributions(world, address, grouped[address], "evolve")


def _run_law(
    world: _World, law
) -> tuple[str, _Contribution] | None:
    """One law over the current step, or nothing when its inputs are absent."""
    energy = world.delivered_energy_now.get(world.generator_address)
    if energy is None:
        return None
    coefficient = None
    for address, value in world.coefficients.items():
        if _state_key_of(address) == GENERATOR_SPECIFIC_CONSUMPTION:
            coefficient = value
            break
    if coefficient is None:
        return None
    world.ledger.record_law(law)
    return (
        world.tank_address,
        _Contribution(
            event_id=law.law_id,
            direction=law.direction,
            quantity=law.compute(coefficient, energy),
            share=Fraction(1),
            origin="MODEL_LAW",
        ),
    )


def _phase_check_invariants(world: _World) -> None:
    """H. Conservation, bounds and model invariants, after the evolution.

    Two checks, and both compare numbers produced by different code. The stock
    was moved by the model's own handler; the expected change is recomputed here
    from the applied-event and bounded-transition records. A handler that moved a
    stock by something other than what the records account for is
    `BALANCE_IDENTITY_VIOLATION`, and a stock left outside its own bound is the
    same failure, because the policy that should have applied did not.
    """
    for address, before in world.stocks_before_step.items():
        after = world.stocks[address]
        contributions = world.step_contributions.get(address, [])
        declared = sum(
            (
                item.quantity
                if item.direction == "INCREASE"
                else -item.quantity
                for item in contributions
            ),
            Fraction(0),
        )
        refused = world.step_refusals.get(address, Fraction(0))
        if after - before != declared - refused:
            raise _Stop(
                failure(
                    "BALANCE_IDENTITY_VIOLATION",
                    address,
                    at_offset_minutes=world.offset,
                    detail=(
                        f"the stock moved by {after - before}",
                        f"the records account for {declared - refused}",
                    ),
                )
            )

        upper = world.upper.get(address)
        lower = world.lower.get(address)
        if upper is not None and after > upper.value:
            raise _Stop(
                failure(
                    "BALANCE_IDENTITY_VIOLATION",
                    address,
                    at_offset_minutes=world.offset,
                    detail=(
                        f"the stock is {after} against an UPPER bound of "
                        f"{upper.value}, so the bound policy did not apply",
                    ),
                )
            )
        if lower is not None and after < lower.value:
            raise _Stop(
                failure(
                    "BALANCE_IDENTITY_VIOLATION",
                    address,
                    at_offset_minutes=world.offset,
                    detail=(
                        f"the stock is {after} against a LOWER bound of "
                        f"{lower.value}, so the bound policy did not apply",
                    ),
                )
            )


def _phase_carry_forward(world: _World) -> None:
    """I. The result becomes the state the next boundary starts from.

    There is no second copy of the world: `world.stocks` IS the hand-off, so
    what this phase does is remember the span that just finished, which is what
    the next boundary's interval measurement describes.
    """
    world.previous_delivered_energy = dict(world.delivered_energy_now)
    world.previous_step_length = world.step_length


#: Phase identity to the function that runs it. The loop reads the contract's
#: declared ordinals, so this table says WHAT a phase does and the contract says
#: WHEN. A phase in the contract with no entry here is refused below.
_PHASES: dict[str, Callable[[_World], None]] = {
    "apply-events": _phase_apply_events,
    "state-at-t": _phase_state_at_t,
    "sample-and-publish": _phase_sample_and_publish,
    "controller-view": _phase_controller_view,
    "controller-intent": _phase_controller_intent,
    "physical-acceptance": _phase_physical_acceptance,
    "evolve": _phase_evolve,
    "check-invariants": _phase_check_invariants,
    "carry-forward": _phase_carry_forward,
}


def declared_phase_order() -> tuple[str, ...]:
    """The cycle this kernel runs, in the contract's declared sequence.

    Exposed so a test can assert the kernel visits the published order rather
    than inferring it from the order calls appear in this file.
    """
    missing = sorted(
        phase.phase_id
        for phase in BOUNDARY_CYCLE
        if phase.phase_id not in _PHASES
    )
    if missing:
        raise RuntimeError(
            f"The execution contract declares phases {missing} and this kernel "
            "implements none of them. A phase added to the cycle stops this "
            "kernel until it is implemented, rather than being skipped."
        )
    return tuple(
        phase.phase_id
        for phase in sorted(BOUNDARY_CYCLE, key=lambda item: item.sequence)
    )


# --- The run ----------------------------------------------------------------


def execute(
    inputs: FrozenWorldInputs,
    model: ModelSpec = MINIMAL_FUEL_MODEL,
    *,
    raise_on_failure: bool = False,
) -> PrivateTrajectory:
    """Execute one frozen Draft and return its private trajectory.

    The version guard runs first and nothing is initialized before it. A run
    frozen against a different contract is refused rather than reinterpreted,
    because the meanings behind its frozen inputs have changed.
    """
    refuse_incompatible_execution(inputs.execution_contract_version)

    world = _World(inputs=inputs, model=model, ledger=ExecutionLedger())
    order = declared_phase_order()
    interval = inputs.interval
    step_starts = interval.step_starts
    stop: ExecutionFailure | None = None

    try:
        _refuse_entries_outside_the_interval(world)
        _resolve_topology(world)
        _initialize(world)
        _note_reporting_path_conditions(world)

        for index, offset in enumerate(interval.boundaries):
            world.offset = offset
            world.step_index = index
            world.begins_a_step = offset in step_starts
            world.step_length = (
                min(offset + interval.timestep_minutes, interval.duration_minutes)
                - offset
                if world.begins_a_step
                else 0
            )

            for phase_id in order:
                # The boundary state is the state AT T, so it is recorded once
                # the instant's own numbers are all in hand - after the events,
                # the sample and the resolved acceptance - and before the
                # evolution, which produces the NEXT boundary's state.
                if phase_id == "evolve":
                    _record_boundary(world)
                _PHASES[phase_id](world)
    except _Stop as stopped:
        stop = stopped.record

    trajectory = PrivateTrajectory(
        run_id=inputs.run_id,
        outcome="FAILED" if stop is not None else "COMPLETED",
        inputs_identity=frozen_inputs_identity(
            inputs,
            kernel_version=KERNEL_VERSION,
            model_profile_id=model.model_profile_id,
            model_profile_version=model.model_profile_version,
            numeric_policy=NUMERIC_POLICY,
        ),
        kernel_version=KERNEL_VERSION,
        model_profile_id=model.model_profile_id,
        model_profile_version=model.model_profile_version,
        numeric_policy=NUMERIC_POLICY,
        execution_contract_version=EXECUTION_CONTRACT_VERSION,
        boundaries=tuple(world.boundaries),
        applied_events=tuple(world.applied),
        bounded_transitions=tuple(world.bounded),
        handlers_exercised=world.ledger.handlers,
        failure=stop,
        notes=tuple(world.notes),
    )

    if stop is not None and raise_on_failure:
        raise KernelExecutionFailed(stop)
    return trajectory


def _record_boundary(world: _World) -> None:
    """The boundary state, recorded after the evolution that produced it.

    Recorded just before the carry-forward phase, which is the last moment the
    instant's own numbers and the span that ended at it are both in hand.
    """
    interval_available = world.step_index > 0
    measurements: tuple[tuple[str, Fraction], ...] = ()
    if interval_available:
        measurements = tuple(
            sorted(world.previous_delivered_energy.items())
        )
    world.boundaries.append(
        BoundaryState(
            step_index=world.step_index,
            offset_minutes=world.offset,
            simulation_time=_instant(
                world.inputs.interval.start_time, world.offset
            ),
            stocks=tuple(sorted(world.stocks.items())),
            forcings_available=tuple(sorted(world.forcings_now.items())),
            state_samples=tuple(sorted(world.samples_now.items())),
            interval_measurements=measurements,
            has_preceding_interval=interval_available,
        )
    )
