"""The executable meaning of a scenario: units, timing, bounds, reconciliation.

`scenarios/models.py` holds the vocabularies an author writes and the parser
enforces. This module holds the semantics those vocabularies commit the product
to - the parts that are the same for every scenario and are therefore versioned
simulator rules rather than authored content:

- what each unit is in canonical terms, so a consumer converts a quantity
  without parsing the text a screen shows;
- how a point entry and a window entry are dispatched against the run's
  half-open time model, and what "exactly once" means at a boundary;
- what a kernel must do when a bound is reached, stated as a policy with no
  silent option in it;
- whether each reported observation is accounted for by the causal inputs the
  same scenario declares.

## This is not a runtime kernel

`reconcile_reported_observations` is contract arithmetic and nothing more. It
has no clock, no timestep, no seed, no state record, no event cursor, and no
output for any instant the scenario did not author an observation at. It never
produces a state trajectory, it is not called by anything that executes, and
removing it would change no behaviour except what the scenario detail screen
can tell a reader.

What it answers is one question the T018 task makes an acceptance criterion:
does the sum of the causal quantities a scenario declares reach the value the
same scenario says a device reported? A contract that cannot answer that lets a
reported number silently prescribe private tank state, which is the thing
`D-2026-09-21-causal-runtime-before-golden-traces` says an authored artifact
must not be able to do. The answer is reported; it is never used to adjust
anything.

The real kernel is T021's. When it exists it owns initialization and the
transition from one private world state to the next, and this module keeps
answering only the contract question.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from assetops_backend.scenarios.models import (
    ScenarioDefinition,
    ScenarioParameter,
    TimelineEntry,
)

#: The contract this module implements, named so a later run, trace, or payload
#: can say which version of these semantics it was built against. It is not the
#: scenario version and not the simulator version: it is the version of the
#: rules below.
EXECUTION_CONTRACT_VERSION = 1


@dataclass(frozen=True)
class CanonicalUnit:
    """One authored unit, in canonical terms.

    `factor` is carried as an exact ratio rather than a float so that a rate
    integrated over a window lands on the number an author would write down.
    Fourteen litres an hour over four hours is fifty-six litres; computed
    through a binary float it is fifty-six point zero zero zero zero zero zero
    zero zero zero zero one, and a screen that showed that would be stating a
    precision the scenario does not have.
    """

    dimension: str
    canonical_unit: str
    numerator: int
    denominator: int


#: Every unit a scenario parameter may carry, in canonical terms. A test
#: asserts this covers `PARAMETER_UNITS` exactly, so a unit added to the
#: authoring vocabulary without a conversion fails the build rather than
#: arriving at a consumer as text to parse.
CANONICAL_UNITS: dict[str, CanonicalUnit] = {
    "L": CanonicalUnit("VOLUME", "L", 1, 1),
    "L/h": CanonicalUnit("VOLUME_RATE", "L/min", 1, 60),
    "kW": CanonicalUnit("POWER", "kW", 1, 1),
    "kWh": CanonicalUnit("ENERGY", "kWh", 1, 1),
    "V": CanonicalUnit("VOLTAGE", "V", 1, 1),
    "Hz": CanonicalUnit("FREQUENCY", "Hz", 1, 1),
    "degC": CanonicalUnit("TEMPERATURE", "degC", 1, 1),
    "W/m2": CanonicalUnit("IRRADIANCE", "W/m2", 1, 1),
    "%": CanonicalUnit("FRACTION", "%", 1, 1),
    "min": CanonicalUnit("TIME", "min", 1, 1),
    "h": CanonicalUnit("TIME", "min", 60, 1),
}

#: Which dimension a rate becomes when it is applied across a window of
#: canonical time. Only the rates this product can integrate are here; a rate
#: outside it cannot be used as a state effect, because the contract would not
#: know what quantity it accumulated to.
RATE_INTEGRALS: dict[str, str] = {"VOLUME_RATE": "VOLUME"}

#: Dimensions whose values cannot be negative. A negative volume, rate, power,
#: energy, irradiance or duration is not a small authoring slip with a
#: defensible reading: it is an invalid input, and the invalid-rate bound case
#: below says it is refused at parse rather than clamped later. Temperature and
#: percentage are deliberately absent, because a negative degC is ordinary.
NON_NEGATIVE_DIMENSIONS = frozenset(
    {"VOLUME", "VOLUME_RATE", "POWER", "ENERGY", "IRRADIANCE", "TIME"}
)


def canonical_quantity(value: float, unit: str) -> tuple[float, str, str]:
    """Convert an authored quantity into canonical terms.

    Returns the canonical value, the canonical unit, and the dimension.

    Raises:
        KeyError: the unit has no canonical conversion. The parser refuses an
            unsupported unit long before this, so reaching it means the
            authoring vocabulary and this table have drifted apart.
    """
    canonical = CANONICAL_UNITS[unit]
    converted = _exact(value) * Fraction(canonical.numerator, canonical.denominator)
    return float(converted), canonical.canonical_unit, canonical.dimension


def _exact(value: float) -> Fraction:
    """A float as the decimal an author wrote, not as its binary expansion."""
    return Fraction(value).limit_denominator(1_000_000)


# --- Dispatch semantics -----------------------------------------------------
#
# Stated as data rather than prose so the screen, the payload and a later
# kernel read one answer. A run interval is half-open, `[start_time, end_time)`,
# and so is each step, `[t, t + timestep)`. Every rule below follows from
# choosing that consistently, which is the point: a boundary event applied
# twice, or dropped, is what happens when two places choose differently.


@dataclass(frozen=True)
class DispatchRule:
    rule_id: str
    display_name: str
    statement: str


DISPATCH_RULES: tuple[DispatchRule, ...] = (
    DispatchRule(
        rule_id="half-open-interval",
        display_name="The run interval and every step are half-open",
        statement=(
            "A run covers its start instant up to but not including its end "
            "instant, and each step covers its own start up to but not "
            "including the next. An instant therefore belongs to exactly one "
            "step, which is what makes applying something once a property of "
            "the time model rather than of the code that happens to read it."
        ),
    ),
    DispatchRule(
        rule_id="point-applied-once",
        display_name="A point entry is applied exactly once",
        statement=(
            "A point entry is due in the one step whose half-open span "
            "contains its offset, and is applied at the start of that step. An "
            "offset that falls exactly on a step boundary belongs to the step "
            "that begins there and never to the step that ends there, so it "
            "cannot be applied by both and cannot be skipped by both."
        ),
    ),
    DispatchRule(
        rule_id="window-active-span",
        display_name="A window entry is active across a half-open span",
        statement=(
            "A window entry is active for every step whose start lies at or "
            "after its offset and before its offset plus its length. The step "
            "beginning exactly at the end of the window is outside it, so two "
            "windows that meet end to start never overlap by one step."
        ),
    ),
    DispatchRule(
        rule_id="quantity-across-a-window",
        display_name="A quantity declared over a window totals to that quantity",
        statement=(
            "A window entry that declares a quantity rather than a rate moves "
            "exactly that quantity, and the state at the end of the window is "
            "the same whether a kernel applies it in one step or spreads it "
            "across the window. A rate, by contrast, may only be declared over "
            "a window, because a rate at an instant moves nothing."
        ),
    ),
    DispatchRule(
        rule_id="interval-wide-span",
        display_name="An interval-wide entry holds for the whole run",
        statement=(
            "An interval-wide entry starts at offset zero and holds until the "
            "run interval ends. It declares no length, because the length is "
            "the run's and choosing that is run setup."
        ),
    ),
    DispatchRule(
        rule_id="outside-the-interval",
        display_name="An entry outside the chosen interval is not silently dropped",
        statement=(
            "An entry whose offset, or whose window, falls outside the "
            "interval a run chooses is a mismatch between the scenario and the "
            "run. Later run setup refuses it and says which entry; it never "
            "quietly leaves the entry out and executes the rest."
        ),
    ),
)


# --- Bound semantics --------------------------------------------------------


@dataclass(frozen=True)
class BoundCase:
    case_id: str
    display_name: str
    policy: str
    statement: str


#: What a kernel is permitted to do when a declared bound is reached.
#:
#: Three policies, and the absent fourth is the one that matters: there is no
#: value meaning "clamp quietly" or "drop the remainder". A bound that is
#: reached is either refused before a run exists, fails the run, or produces a
#: bounded transition that is recorded with the quantity it refused. A kernel
#: that silently clamped would produce a trajectory nothing in the evidence
#: path could account for, and a later analysis would be right to be confused
#: by it.
BOUND_POLICIES = frozenset({"REFUSED_AT_PARSE", "FAIL_RUN", "BOUNDED_AND_RECORDED"})

BOUND_CASES: tuple[BoundCase, ...] = (
    BoundCase(
        case_id="fuel-tank-capacity",
        display_name="The tank cannot hold more than its capacity",
        policy="BOUNDED_AND_RECORDED",
        statement=(
            "The declared capacity bounds the stored volume at every step. A "
            "transition that would take the volume above it fills to capacity "
            "and records the volume it could not accept as a bounded "
            "transition of its own, carrying the quantity refused."
        ),
    ),
    BoundCase(
        case_id="delivery-overflow",
        display_name="A delivery larger than the space left is bounded and recorded",
        policy="BOUNDED_AND_RECORDED",
        statement=(
            "A delivery is applied up to the space the tank has and the "
            "remainder is recorded as refused, with its quantity. It is never "
            "discarded silently: a delivery that partly did not fit is a fact "
            "a later analysis has to be able to see, because the alternative "
            "is fuel that arrives in the record and never in the tank."
        ),
    ),
    BoundCase(
        case_id="insufficient-fuel",
        display_name="A draw larger than the fuel present fails the run",
        policy="FAIL_RUN",
        statement=(
            "A consumption or removal that would take the stored volume below "
            "zero means the authored causes and the world they produced "
            "disagree. The run fails and names the entry. It does not empty "
            "the tank quietly, because that would invent the missing quantity "
            "out of the model instead of reporting the contradiction."
        ),
    ),
    BoundCase(
        case_id="invalid-rate",
        display_name="A negative or unusable rate never reaches a run",
        policy="REFUSED_AT_PARSE",
        statement=(
            "A rate or quantity that is negative, infinite, or not a number is "
            "refused when the definition is read, so no run setup and no "
            "kernel ever sees one. This is the only bound case the product "
            "already enforces end to end, because it is the only one that can "
            "be decided without executing anything."
        ),
    ),
)


# --- Initialization and the private-state transition surface ----------------


@dataclass(frozen=True)
class InitializationInput:
    """One initial world value, with the owner that answers for it."""

    parameter_id: str
    display_name: str
    state_key: str
    owner: str
    value: float
    unit: str
    canonical_value: float
    canonical_unit: str
    dimension: str


@dataclass(frozen=True)
class StateTransitionInput:
    """One declared change to private world state, and where it came from."""

    event_id: str
    state_key: str
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

    Only a parameter whose ownership says it initializes appears here. A
    reported observation cannot: it carries no ownership record at all, which
    is the structural form of "a recording may not hide initialization".
    """
    inputs: list[InitializationInput] = []

    for parameter in _all_parameters(scenario).values():
        ownership = parameter.ownership
        if ownership is None or not ownership.initializes:
            continue
        if parameter.state_key is None or parameter.unit is None:
            continue
        if not isinstance(parameter.value, float):
            continue

        canonical_value, canonical_unit, dimension = canonical_quantity(
            parameter.value, parameter.unit
        )
        inputs.append(
            InitializationInput(
                parameter_id=parameter.parameter_id,
                display_name=parameter.display_name,
                state_key=parameter.state_key,
                owner=ownership.owner,
                value=parameter.value,
                unit=parameter.unit,
                canonical_value=canonical_value,
                canonical_unit=canonical_unit,
                dimension=dimension,
            )
        )

    return tuple(sorted(inputs, key=lambda entry: entry.state_key))


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
        if effect is None or entry.state_key is None:
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
                state_key=entry.state_key,
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
#: `NOT_RECONCILABLE` means the contract cannot answer: no declared initial
#: value for the state, or a causal window that is still running when the
#: reading is taken.
#:
#: There is no value meaning "close enough". A reported value that differs from
#: the declared causes differs for a reason, and the reason is either another
#: cause nobody modelled or a reporting behaviour nobody declared. Both are
#: things to decide, not things to round away.
RECONCILIATION_STATES = frozenset(
    {"ACCOUNTED_FOR", "NOT_ACCOUNTED_FOR", "NOT_RECONCILABLE"}
)


@dataclass(frozen=True)
class ObservationReconciliation:
    """One reported observation, against the causes declared before it."""

    event_id: str
    source_id: str
    parameter_id: str
    state_key: str
    offset_minutes: int
    reported_value: float
    declared_value: float | None
    difference: float | None
    unit: str
    state: str
    accounted_by: tuple[str, ...]


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
    initial_by_state = {
        entry.state_key: entry for entry in initialization_inputs(scenario)
    }
    transitions = state_transition_inputs(scenario)

    results: list[ObservationReconciliation] = []

    for entry in scenario.timeline:
        binding = entry.observation
        if binding is None:
            continue
        parameter = parameters.get(binding.reported_parameter_id)
        if (
            parameter is None
            or parameter.state_key is None
            or parameter.unit is None
            or not isinstance(parameter.value, float)
        ):
            continue

        state_key = parameter.state_key
        reported_value, reported_unit, _ = canonical_quantity(
            parameter.value, parameter.unit
        )

        initial = initial_by_state.get(state_key)
        relevant = [
            transition
            for transition in transitions
            if transition.state_key == state_key
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

        if initial is None or straddling:
            results.append(
                ObservationReconciliation(
                    event_id=entry.event_id,
                    source_id=binding.source_id,
                    parameter_id=parameter.parameter_id,
                    state_key=state_key,
                    offset_minutes=entry.offset_minutes,
                    reported_value=reported_value,
                    declared_value=None,
                    difference=None,
                    unit=reported_unit,
                    state="NOT_RECONCILABLE",
                    accounted_by=(),
                )
            )
            continue

        applied = [
            transition
            for transition in relevant
            if transition.complete_at_offset is not None
            and transition.complete_at_offset <= entry.offset_minutes
        ]

        declared = _exact(initial.canonical_value)
        for transition in applied:
            magnitude = _exact(transition.applied_value)
            declared += magnitude if transition.direction == "INCREASE" else -magnitude

        difference = _exact(reported_value) - declared

        results.append(
            ObservationReconciliation(
                event_id=entry.event_id,
                source_id=binding.source_id,
                parameter_id=parameter.parameter_id,
                state_key=state_key,
                offset_minutes=entry.offset_minutes,
                reported_value=reported_value,
                declared_value=float(declared),
                difference=float(difference),
                unit=reported_unit,
                state="ACCOUNTED_FOR" if difference == 0 else "NOT_ACCOUNTED_FOR",
                accounted_by=tuple(
                    transition.event_id for transition in applied
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
