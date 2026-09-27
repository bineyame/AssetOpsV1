"""Projecting a scenario document, against the contract the kernel executes.

This module used to hold two different things: the versioned rules a conforming
implementation obeys, and the projections of a document that report what it
declares. T021 separated them, because the first conforming kernel lives in
`assetops_simulator` and `simulator/` may not import `assetops_backend` at all
(v4 section 3.2, and `.ai/ARCHITECTURE.md` Execution Composition And Truth
Barrier).

The rules moved, unchanged, to `assetops_contracts.execution_contract` -
canonical units, half-open dispatch, the boundary cycle, what a reading
timestamped `T` describes, and what each bound policy commits a kernel to - and
are re-exported below so a product caller still reads one module and the
scenario detail screen still renders those objects rather than copies of them.
Two new functions arrived with them: `step_concerns_window` and
`window_share_of_step`, the `window-overlap` predicate and the `window-ramp`
share as executable arithmetic beside the sentences that publish them.

What stayed is what needs a `ScenarioDefinition`:

- `initialization_inputs` and `state_transition_inputs`, which report the
  initial world values and the declared changes a document carries;
- `declared_bounds`, which reports the `(lower, upper)` a document declares and
  deliberately reports no number for a bound whose value is the site's
  (`D-2026-09-22-capacity-bound-source`);
- `reconcile_reported_observations`, the specification reference implementation.

## `reconcile_reported_observations` has lost its authority

`D-2026-09-21-specification-reference-implementation` said it stops being an
authority the moment a kernel exists to be compared against, and T021 is that
moment. The comparison is in `host/tests/test_shipped_trajectory.py`: against
the shipped document the reconciler reports the declared level as 310 L at both
readings and the kernel computes 254.02 L, and the 55.98 L between them is
exactly the fuel the model law burns and the document no longer declares. Where
the two disagree, the kernel is right, and the reconciler is right about the
narrower question it asks.

It is still honest about that narrower question, so it stays: it answers whether
the causes a DOCUMENT declares reach a reading the same document declares, which
is a real property of a document that still contains two authored readings. Its
removal follows its last product-path caller, the scenario detail screen's
reconciliation panel, which is T022's under
`D-2026-09-22-reconciliation-panel-retirement`. `declared_bounds` and
`IMPLICIT_LOWER_BOUND_DIMENSIONS` leave with it.

## This is still not a runtime kernel

`reconcile_reported_observations` has no clock, no timestep, no seed, no state
record and no event cursor, and it produces nothing for any instant the scenario
did not author an observation at. It never produces a state trajectory, nothing
that executes calls it, and removing it would change no behaviour except what
the scenario detail screen can tell a reader. The kernel owns initialization and
the transition from one private world state to the next; this module keeps
answering only the contract question.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from assetops_contracts.execution_contract import (
    BOUNDARY_CYCLE,
    BOUND_CASES,
    BOUND_POLICIES,
    BOUND_POLICY_STATEMENTS,
    CANONICAL_UNITS,
    DISPATCH_RULES,
    DURATION_UNIT_SPELLINGS,
    EXECUTION_CONTRACT_VERSION,
    NON_NEGATIVE_DIMENSIONS,
    NUMERIC_POLICY,
    NUMERIC_POLICY_VERSION,
    OBSERVATION_RULES,
    RATE_INTEGRALS,
    READING_CLASSES,
    BoundaryPhase,
    BoundCase,
    CanonicalUnit,
    DispatchRule,
    ExecutionContractIncompatible,
    ObservationRule,
    _exact,
    canonical_fraction,
    canonical_quantity,
    normalize_authored_float,
    overlap_minutes,
    point_due_at,
    refuse_incompatible_execution,
    step_concerns_window,
    steps_concerning_window,
    window_share_of_step,
    window_span,
)
from assetops_backend.scenarios.models import (
    STATE_CHANGING_ROLES,
    ScenarioDefinition,
    ScenarioParameter,
    TimelineEntry,
)
from assetops_backend.state_refs import StateRef

#: Re-exported so a product caller reads one module. The names are the contract
#: module's objects and not copies of them: `is` holds, which is what keeps the
#: screen, the payload and the kernel reading one answer.
__all__ = [
    "BOUNDARY_CYCLE",
    "BOUND_CASES",
    "BOUND_POLICIES",
    "BOUND_POLICY_STATEMENTS",
    "CANONICAL_UNITS",
    "DISPATCH_RULES",
    "DURATION_UNIT_SPELLINGS",
    "EXECUTION_CONTRACT_VERSION",
    "NON_NEGATIVE_DIMENSIONS",
    "NUMERIC_POLICY",
    "NUMERIC_POLICY_VERSION",
    "OBSERVATION_RULES",
    "RATE_INTEGRALS",
    "READING_CLASSES",
    "BoundaryPhase",
    "BoundCase",
    "CanonicalUnit",
    "DispatchRule",
    "ExecutionContractIncompatible",
    "ObservationRule",
    "canonical_fraction",
    "canonical_quantity",
    "normalize_authored_float",
    "overlap_minutes",
    "point_due_at",
    "refuse_incompatible_execution",
    "step_concerns_window",
    "steps_concerning_window",
    "window_share_of_step",
    "window_span",
    "ACCOUNTED_FOR_REASON",
    "BOUND_REACHED_LOWER",
    "BOUND_REACHED_UPPER",
    "IMPLICIT_LOWER_BOUND_DIMENSIONS",
    "InitializationInput",
    "NOT_ACCOUNTED_FOR_REASON",
    "NO_DECLARED_INITIAL_VALUE",
    "OPEN_CAUSAL_WINDOW",
    "ORDER_DEPENDENT_GROUP",
    "ObservationReconciliation",
    "RECONCILIATION_STATES",
    "StateTransitionInput",
    "declared_bounds",
    "initialization_inputs",
    "reconcile_reported_observations",
    "state_transition_inputs",
    "unaccounted_observations",
]


# --- Initialization and the private-state transition surface ----------------


@dataclass(frozen=True)
class InitializationInput:
    """One initial world value, with the owner that answers for it.

    `value` and `canonical_value` are `None` exactly when the declared owner
    is `SITE_FOUNDATION`, because such a parameter states no number
    (`D-2026-09-22-foundation-value-declaration`). This record is a projection
    of the document and the document genuinely does not know the number: the
    Site does, and run setup is the component entitled to hold a document and
    a resolved Site together.

    `unit` and `dimension` are present either way. What kind of quantity the
    state is remains the scenario's to declare, and it is what run setup
    checks the Foundation's own property against.
    """

    parameter_id: str
    display_name: str
    state_ref: StateRef
    owner: str
    value: float | None
    unit: str
    canonical_value: float | None
    canonical_unit: str
    dimension: str

    @property
    def state_key(self) -> str:
        """The semantic state, without its selector."""
        return self.state_ref.state_key

    @property
    def addressed_key(self) -> str:
        """The canonical spelling of the address this concerns."""
        return self.state_ref.addressed_key


@dataclass(frozen=True)
class StateTransitionInput:
    """One declared change to private world state, and where it came from."""

    event_id: str
    state_ref: StateRef
    direction: str
    parameter_id: str
    canonical_value: float
    canonical_unit: str
    dimension: str
    #: The volume, energy or other accumulated quantity this transition
    #: amounts to once a rate has been applied across its window. Equal to
    #: `canonical_value` for a quantity effect.
    applied_value: float
    applied_unit: str
    applied_dimension: str
    #: Where the transition begins, as an offset from the interval start.
    starts_at_offset: int
    #: The offset at which the transition is complete: its own offset for a
    #: point, the end of its window otherwise. `None` for an interval-wide
    #: entry, which never completes inside the scenario.
    complete_at_offset: int | None

    @property
    def state_key(self) -> str:
        """The semantic state, without its selector."""
        return self.state_ref.state_key

    @property
    def addressed_key(self) -> str:
        """The canonical spelling of the address this concerns."""
        return self.state_ref.addressed_key


def _all_parameters(scenario: ScenarioDefinition) -> dict[str, ScenarioParameter]:
    """Every public parameter in the document, by identity.

    Parameter identities are unique across the whole document, enforced by the
    parser, so a state effect that names one names exactly one thing.
    """
    found: dict[str, ScenarioParameter] = {
        parameter.parameter_id: parameter
        for parameter in scenario.public_parameters
    }
    for entry in scenario.timeline:
        for parameter in entry.parameters:
            found[parameter.parameter_id] = parameter
    return found


def initialization_inputs(
    scenario: ScenarioDefinition,
) -> tuple[InitializationInput, ...]:
    """Every initial world value the scenario declares, with its owner.

    Two conditions, and the second is deliberately not a restatement of a
    parser rule. A parameter appears here only if its ownership says it
    initializes AND its role is one of `STATE_CHANGING_ROLES`. The parser
    refuses the combination that would make the second condition matter, so
    this is the layer that keeps holding if that refusal is ever loosened -
    which is exactly what the T018 review found had happened by accident for a
    forcing input.

    A reported observation cannot reach here at all: it carries no ownership
    record, which is the structural form of "a recording may not hide
    initialization".
    """
    inputs: list[InitializationInput] = []

    for parameter in _all_parameters(scenario).values():
        ownership = parameter.ownership
        if ownership is None or not ownership.initializes:
            continue
        if parameter.execution_role not in STATE_CHANGING_ROLES:
            continue
        if parameter.state_ref is None or parameter.unit is None:
            continue
        # A Foundation-owned parameter states no number, by construction
        # (`D-2026-09-22-foundation-value-declaration`), and it still declares
        # an initial world value: the need is what it declares, and run setup
        # resolves the answer from the Site through the profile's binding.
        # Skipping it here on the old float filter would have made the
        # decision's own parameters vanish from initialization, which is the
        # opposite of what it settles.
        if parameter.value is None:
            if ownership.owner != "SITE_FOUNDATION":
                continue
            canonical_value = None
            _, canonical_unit, dimension = canonical_quantity(
                0.0, parameter.unit
            )
            value: float | None = None
        elif isinstance(parameter.value, float):
            value = parameter.value
            canonical_value, canonical_unit, dimension = canonical_quantity(
                parameter.value, parameter.unit
            )
        else:
            continue

        inputs.append(
            InitializationInput(
                parameter_id=parameter.parameter_id,
                display_name=parameter.display_name,
                state_ref=parameter.state_ref,
                owner=ownership.owner,
                value=value,
                unit=parameter.unit,
                canonical_value=canonical_value,
                canonical_unit=canonical_unit,
                dimension=dimension,
            )
        )

    # Sorted by ADDRESS, so two components of one type hold a stable and
    # distinguishable order rather than colliding on one semantic key.
    return tuple(sorted(inputs, key=lambda entry: entry.addressed_key))


def state_transition_inputs(
    scenario: ScenarioDefinition,
) -> tuple[StateTransitionInput, ...]:
    """Every declared change to private world state, in authored order.

    Built only from `CAUSAL_INPUT` entries carrying a state effect. Nothing
    else in the document can reach this list, because no other entry kind has a
    field a state effect could be written in.
    """
    parameters = _all_parameters(scenario)
    transitions: list[StateTransitionInput] = []

    for entry in scenario.timeline:
        effect = entry.state_effect
        if effect is None or entry.state_ref is None:
            continue

        source_id = effect.quantity_parameter_id or effect.rate_parameter_id
        if source_id is None:
            continue
        parameter = parameters.get(source_id)
        if (
            parameter is None
            or parameter.unit is None
            or not isinstance(parameter.value, float)
        ):
            continue

        canonical_value, canonical_unit, dimension = canonical_quantity(
            parameter.value, parameter.unit
        )

        if effect.rate_parameter_id is not None:
            duration = entry.timing.duration_minutes or 0
            applied_value = float(
                _exact(canonical_value) * Fraction(duration)
            )
            applied_dimension = RATE_INTEGRALS[dimension]
            applied_unit = CANONICAL_UNITS[
                _canonical_unit_name(applied_dimension)
            ].canonical_unit
        else:
            applied_value = canonical_value
            applied_unit = canonical_unit
            applied_dimension = dimension

        transitions.append(
            StateTransitionInput(
                event_id=entry.event_id,
                state_ref=entry.state_ref,
                direction=effect.direction,
                parameter_id=parameter.parameter_id,
                canonical_value=canonical_value,
                canonical_unit=canonical_unit,
                dimension=dimension,
                applied_value=applied_value,
                applied_unit=applied_unit,
                applied_dimension=applied_dimension,
                starts_at_offset=entry.offset_minutes,
                complete_at_offset=_complete_at(entry),
            )
        )

    return tuple(transitions)


def _canonical_unit_name(dimension: str) -> str:
    """The authored unit whose canonical form represents a dimension."""
    for unit, canonical in CANONICAL_UNITS.items():
        if canonical.dimension == dimension and canonical.numerator == 1:
            return unit
    raise KeyError(dimension)


def _complete_at(entry: TimelineEntry) -> int | None:
    if entry.timing.shape == "POINT":
        return entry.offset_minutes
    if entry.timing.shape == "WINDOW":
        return entry.offset_minutes + (entry.timing.duration_minutes or 0)
    return None


# --- Reconciling reported observations against the declared causes ----------

#: What a reported observation turned out to be, against the causes the same
#: scenario declares.
#:
#: `ACCOUNTED_FOR` means the declared causal inputs reach the reported value
#: exactly. `NOT_ACCOUNTED_FOR` means they do not, and the difference is
#: reported with its sign so a reader can see which way and by how much.
#: `NOT_RECONCILABLE` means the contract cannot answer, for one of four
#: reasons it names: no declared initial value for the state, a causal window
#: still running when the reading is taken, a declared bound reached before
#: it, or a group of simultaneous causes whose outcome depends on an order the
#: scenario does not declare.
#:
#: The third was the T018 review's finding. Summing every completed transition
#: without consulting a bound reported a declared volume above the capacity
#: the same document declares, under a column headed "declared causes reach" -
#: a number the contract refuses elsewhere. Applying the bound is the kernel's
#: job and out of scope here, so the contract declines to answer instead.
#:
#: The fourth is the same lesson once more, and T019's review found it. An
#: earlier draft of `intra-instant-order` serialised simultaneous causes in
#: authored order and evaluated bounds between them, so a delivery and a draw
#: at one instant could reach a level the tank is never in - an artifact of
#: serialising two things the author declared to happen together. The contract
#: now evaluates the group's net and abstains only when an ordering could
#: genuinely have changed the answer.
#:
#: There is no value meaning "close enough". A reported value that differs from
#: the declared causes differs for a reason, and the reason is either another
#: cause nobody modelled or a reporting behaviour nobody declared. Both are
#: things to decide, not things to round away.
RECONCILIATION_STATES = frozenset(
    {"ACCOUNTED_FOR", "NOT_ACCOUNTED_FOR", "NOT_RECONCILABLE"}
)

#: The reasons, as product copy. Digit-free on purpose: the quantities belong
#: in the record's own columns, and prose that restated them would be a second
#: place for a number to drift.
ACCOUNTED_FOR_REASON = (
    "the causes declared before this reading reach the value it reports"
)
NOT_ACCOUNTED_FOR_REASON = (
    "the causes declared before this reading do not reach the value it "
    "reports, and no declared cause accounts for the difference"
)
NO_DECLARED_INITIAL_VALUE = (
    "no initial value is declared for this state, so there is nothing for the "
    "declared causes to start from"
)
#: Reworded in T020B's correction round, because it had become false.
#:
#: It read "apportioning part of a window would be a transition rule rather
#: than a contract", and `window-ramp` is now exactly a contract statement of
#: how a window apportions - so this string denied what the same module
#: declares two hundred lines up. The reconciler still abstains, and still
#: should: it has no clock and no state, so it cannot evaluate a ramp even
#: though the contract now defines one. What changed is that its reason has to
#: be its own inability rather than a gap in the contract.
OPEN_CAUSAL_WINDOW = (
    "a declared cause is still running when this reading is taken. The contract "
    "states how a window apportions - see the window ramp rule - but this "
    "comparison has no clock and no state to evaluate it with, so it reports "
    "that it cannot answer rather than guessing at the fraction"
)
BOUND_REACHED_UPPER = (
    "a declared cause would take this state above a bound the same definition "
    "declares before the reading. What a run does then is the bounded "
    "transition the bound case names, and computing it belongs to the runtime"
)
BOUND_REACHED_LOWER = (
    "a declared cause would take this state below a bound the same definition "
    "declares before the reading. What a run does then is what the bound case "
    "names, and deciding it belongs to the runtime"
)
ORDER_DEPENDENT_GROUP = (
    "two or more declared causes complete on this state at the same offset, "
    "and whether a bound is reached between them depends on the order they "
    "are applied in. The scenario declares them as simultaneous, so no order "
    "is the true one and the contract will not pick between them. A scenario "
    "that needs one to happen first says so in time, by separating the "
    "offsets"
)

#: The floor every stored quantity has, whether or not a document declares
#: one. The `insufficient-fuel` bound case states it in words - a draw that
#: would take the stored volume below zero - so the contract may rely on it
#: without inventing anything.
IMPLICIT_LOWER_BOUND_DIMENSIONS: dict[str, float] = {"VOLUME": 0.0}


def declared_bounds(
    scenario: ScenarioDefinition,
) -> dict[str, tuple[float | None, float | None]]:
    """The `(lower, upper)` a document declares for each addressed state.

    Keyed on the ADDRESS since T020A1, and on a site with two tanks that is
    the substance of it: the capacity bounding the north tank's volume is the
    north tank's, and a map keyed on `fuel-tank-volume` would have let
    whichever capacity was read last cap both of them.

    Upper bounds come from a `bounds` declaration on an initial world value;
    nothing is inferred from two state keys that happen to share a prefix. The
    lower bound for a stored quantity is the floor the `insufficient-fuel`
    bound case already states in words.

    Everything here is in canonical units, because a bound and the value it
    limits have to be compared in the same terms and an authored unit is not
    guaranteed to be the canonical one.
    """
    lower: dict[str, float] = {}
    upper: dict[str, float] = {}

    for parameter in _all_parameters(scenario).values():
        if parameter.unit is None or not isinstance(parameter.value, float):
            continue

        canonical_value, _, dimension = canonical_quantity(
            parameter.value, parameter.unit
        )

        address = parameter.addressed_key
        if address is not None and dimension in IMPLICIT_LOWER_BOUND_DIMENSIONS:
            lower.setdefault(
                address, IMPLICIT_LOWER_BOUND_DIMENSIONS[dimension]
            )

        bound = parameter.bounds
        if bound is None:
            continue
        if bound.bound_kind == "UPPER":
            upper[bound.state_ref.addressed_key] = canonical_value
        else:
            lower[bound.state_ref.addressed_key] = canonical_value

    return {
        address: (lower.get(address), upper.get(address))
        for address in set(lower) | set(upper)
    }


@dataclass(frozen=True)
class ObservationReconciliation:
    """One reported observation, against the causes declared before it."""

    event_id: str
    source_id: str
    parameter_id: str
    state_ref: StateRef
    offset_minutes: int
    reported_value: float
    declared_value: float | None
    difference: float | None
    unit: str
    state: str
    #: Why the contract answered the way it did. Always present, because a
    #: `NOT_RECONCILABLE` with no reason is four different facts wearing one
    #: name: no declared initial value, an open causal window, a declared
    #: bound reached, and a group of simultaneous causes whose outcome depends
    #: on an order nobody declared are four problems with four different
    #: fixes. The fourth arrived with T019's revised intra-instant rule and
    #: this count did not follow it until the review said so.
    reason: str
    accounted_by: tuple[str, ...]

    @property
    def state_key(self) -> str:
        """The semantic state, without its selector."""
        return self.state_ref.state_key

    @property
    def addressed_key(self) -> str:
        """The canonical spelling of the address this concerns."""
        return self.state_ref.addressed_key


def reconcile_reported_observations(
    scenario: ScenarioDefinition,
) -> tuple[ObservationReconciliation, ...]:
    """Compare each reported observation with the causes declared before it.

    Contract arithmetic over declared quantities, evaluated only at the offsets
    the scenario authored an observation at. It computes no trajectory, holds
    no state, and produces nothing for any other instant. See the module
    docstring: this is not a kernel and must not grow into one.

    A causal effect counts when it is complete at or before the reading. An
    effect whose window is still open when the reading is taken makes the
    reading `NOT_RECONCILABLE`, because apportioning part of a window would be
    a transition rule, and transition rules belong to the kernel.
    """
    parameters = _all_parameters(scenario)
    # Every lookup below is by ADDRESS. Two tanks share one semantic state
    # key, so a map keyed on the key would reconcile the north tank's reading
    # against the south tank's initial value and its causes, and report a
    # discrepancy about a tank nobody touched.
    initial_by_state = {
        entry.addressed_key: entry
        for entry in initialization_inputs(scenario)
    }
    transitions = state_transition_inputs(scenario)
    bounds_by_state = declared_bounds(scenario)

    results: list[ObservationReconciliation] = []

    for entry in scenario.timeline:
        binding = entry.observation
        if binding is None:
            continue
        parameter = parameters.get(binding.reported_parameter_id)
        if (
            parameter is None
            or parameter.state_ref is None
            or parameter.unit is None
            or not isinstance(parameter.value, float)
        ):
            continue

        state_ref = parameter.state_ref
        address = state_ref.addressed_key
        reported_value, reported_unit, _ = canonical_quantity(
            parameter.value, parameter.unit
        )

        initial = initial_by_state.get(address)
        bounds = bounds_by_state.get(address, (None, None))
        relevant = [
            transition
            for transition in transitions
            if transition.addressed_key == address
        ]
        straddling = [
            transition
            for transition in relevant
            if transition.starts_at_offset <= entry.offset_minutes
            and (
                transition.complete_at_offset is None
                or transition.complete_at_offset > entry.offset_minutes
            )
        ]

        def unanswerable(reason: str) -> ObservationReconciliation:
            return ObservationReconciliation(
                event_id=entry.event_id,
                source_id=binding.source_id,
                parameter_id=parameter.parameter_id,
                state_ref=state_ref,
                offset_minutes=entry.offset_minutes,
                reported_value=reported_value,
                declared_value=None,
                difference=None,
                unit=reported_unit,
                state="NOT_RECONCILABLE",
                reason=reason,
                accounted_by=(),
            )

        if initial is None:
            results.append(unanswerable(NO_DECLARED_INITIAL_VALUE))
            continue
        if straddling:
            results.append(unanswerable(OPEN_CAUSAL_WINDOW))
            continue

        applied = [
            transition
            for transition in relevant
            if transition.complete_at_offset is not None
            and transition.complete_at_offset <= entry.offset_minutes
        ]

        lower, upper = bounds

        # Walked instant by instant rather than summed, because a bound is
        # reached at a moment: a delivery that overfills and a draw that
        # empties both land inside the sequence, and a total that happens to
        # come back inside the bounds would hide them.
        #
        # Everything completing at one offset is ONE step, not several. That
        # is the `intra-instant-order` dispatch rule and it is the whole of
        # what this loop assumes about order: nothing here reads the order
        # rows were written in, because that order is authoring rather than
        # physics. Whether it could have mattered is decided exactly, by the
        # two extremes below, and the result of this function does not depend
        # on document order at all.
        declared = _exact(initial.canonical_value)
        reached: str | None = None

        for offset in sorted({item.complete_at_offset for item in applied}):
            group = [
                item for item in applied if item.complete_at_offset == offset
            ]
            increases = sum(
                (
                    _exact(item.applied_value)
                    for item in group
                    if item.direction == "INCREASE"
                ),
                Fraction(0),
            )
            decreases = sum(
                (
                    _exact(item.applied_value)
                    for item in group
                    if item.direction != "INCREASE"
                ),
                Fraction(0),
            )
            after = declared + increases - decreases

            # The net endpoint first. Every ordering reaches it, so a bound
            # broken there is broken however the group is applied, and that is
            # the ordinary bound case rather than an ambiguity.
            if upper is not None and after > _exact(upper):
                reached = BOUND_REACHED_UPPER
                break
            if lower is not None and after < _exact(lower):
                reached = BOUND_REACHED_LOWER
                break

            # Then the two extremes, which bracket every ordering: no ordering
            # peaks above "every increase first" and none troughs below "every
            # decrease first". If neither extreme reaches a bound, no ordering
            # does and the net stands. If either does - one of them or both -
            # the group is ambiguous and the contract will not pick an order.
            #
            # Both is a real case and the statement above names it, because a
            # case a versioned statement leaves unspecified is a case where
            # two conforming kernels may legitimately disagree: a group that
            # overfills applied one way and empties applied the other reaches
            # a bound under every ordering, but not the same bound, so what a
            # kernel does still differs.
            peak = declared + increases
            trough = declared - decreases
            if (upper is not None and peak > _exact(upper)) or (
                lower is not None and trough < _exact(lower)
            ):
                reached = ORDER_DEPENDENT_GROUP
                break

            declared = after

        if reached is not None:
            results.append(unanswerable(reached))
            continue

        difference = _exact(reported_value) - declared

        results.append(
            ObservationReconciliation(
                event_id=entry.event_id,
                source_id=binding.source_id,
                parameter_id=parameter.parameter_id,
                state_ref=state_ref,
                offset_minutes=entry.offset_minutes,
                reported_value=reported_value,
                declared_value=float(declared),
                difference=float(difference),
                unit=reported_unit,
                state="ACCOUNTED_FOR" if difference == 0 else "NOT_ACCOUNTED_FOR",
                reason=(
                    ACCOUNTED_FOR_REASON
                    if difference == 0
                    else NOT_ACCOUNTED_FOR_REASON
                ),
                # Sorted within each instant, because within an instant
                # there is no order to preserve. Across instants the
                # completion offset is the order. Together that makes this
                # tuple - and so the whole record - independent of the order
                # the document happens to list simultaneous entries in, which
                # is what the dispatch rule says and a test measures.
                accounted_by=tuple(
                    transition.event_id
                    for transition in sorted(
                        applied,
                        key=lambda item: (
                            item.complete_at_offset or 0,
                            item.event_id,
                        ),
                    )
                ),
            )
        )

    return tuple(results)


def unaccounted_observations(
    reconciliations: Iterable[ObservationReconciliation],
) -> tuple[ObservationReconciliation, ...]:
    """The reported observations the declared causes do not reach."""
    return tuple(
        result
        for result in reconciliations
        if result.state != "ACCOUNTED_FOR"
    )
