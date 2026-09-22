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

## `reconcile_reported_observations` is a reference implementation

It is labelled as one, with its expiry stated as a condition, in
`backend/tests/test_scenario_execution_contract.py`, per
`D-2026-09-21-specification-reference-implementation`. The short form: it
exercises this contract against a real document because a specification with
no implementation is under-tested, it is not a product feature, and it stops
being an authority the moment a kernel exists to be compared against. Its one
remaining product-path caller is the scenario detail screen's reconciliation
panel, and it leaves the repository when that caller does - which is Open
Question 5 and undecided.

Run setup used to be a second caller. Amendment 1's proposal (e) removed that,
because deciding whether declared causes reach a reading needs a kernel, and
run setup has none.

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
    STATE_CHANGING_ROLES,
    ScenarioDefinition,
    ScenarioParameter,
    TimelineEntry,
)

#: The contract this module implements, named so a later run, trace, or payload
#: can say which version of these semantics it was built against. It is not the
#: scenario version and not the simulator version: it is the version of the
#: rules below.
#:
#: **When this moves.** A version moves when the space of behaviours a
#: conforming implementation may exhibit changes, including when it narrows.
#: Wording does not move it.
#:
#: That is a stricter test than "the rule set is what is versioned", which an
#: earlier draft of this comment used, and the difference has a cost
#: downstream. `D-2026-09-21-causal-runtime-before-golden-traces` makes a
#: provenance mismatch REFUSE playback rather than fall back, so a version
#: that moved on a prose edit would force regeneration of golden traces that
#: were never invalid.
#:
#: Two since T019, which declared what happens when two causes complete at one
#: instant. Version one left that unspecified: two conforming version-one
#: kernels could legitimately disagree at that instant, so declaring any rule
#: for it narrows the space, and that is what moved the number. T019's review
#: then replaced the rule's content - authored order gave way to a net effect
#: with an exact ambiguity test - and the version did not move again. Both
#: drafts narrow the same unspecified space, the number identifies the space
#: rather than the wording, and no implementation ever conformed to the first
#: draft: it existed only inside this slice.
EXECUTION_CONTRACT_VERSION = 2


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
#:
#: No duration unit appears here, and that is the cadence prohibition in its
#: structural form - see `DURATION_UNIT_SPELLINGS` below.
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
}

#: Spellings of a duration, refused as a parameter unit anywhere.
#:
#: T018 first enforced the cadence prohibition at one position - a duration
#: parameter on a reported observation - and the review found three more the
#: rule did not reach: a top-level duration, a duration on the entry that
#: forces the reporting path, and a reading timed as a window. Closing them
#: one at a time is how the next one gets missed, so the closure is at the
#: vocabulary instead: a duration has no unit to be written in, so there is no
#: position it can occupy as a parameter.
#:
#: This is a narrowing rather than a new field. `min` and `h` were authoring
#: units until this slice moved `run-window-length`, `removal-window-length`
#: and `gap-length` into `timing.duration_minutes`, which is where an entry's
#: length now lives and the only place it may. A duration that is NOT an
#: entry's length has no legitimate home in this product today; if a later
#: slice needs one, it reopens this vocabulary with a reason on the record
#: rather than by an author finding a gap.
#:
#: Listed generously, because the point is the refusal message. A spelling
#: outside this set is refused anyway by the closed unit vocabulary; a
#: spelling inside it is refused with an explanation of where a duration
#: belongs.
DURATION_UNIT_SPELLINGS = frozenset(
    {
        "min",
        "mins",
        "minute",
        "minutes",
        "h",
        "hr",
        "hrs",
        "hour",
        "hours",
        "s",
        "sec",
        "secs",
        "second",
        "seconds",
        "ms",
        "d",
        "day",
        "days",
    }
)

#: Which dimension a rate becomes when it is applied across a window of
#: canonical time. Only the rates this product can integrate are here; a rate
#: outside it cannot be used as a state effect, because the contract would not
#: know what quantity it accumulated to.
RATE_INTEGRALS: dict[str, str] = {"VOLUME_RATE": "VOLUME"}

#: Dimensions whose values cannot be negative. A negative volume, rate, power,
#: energy or irradiance is not a small authoring slip with a defensible
#: reading: it is an invalid input, and the invalid-rate bound case below says
#: it is refused at parse rather than clamped later. Temperature and
#: percentage are deliberately absent, because a negative degC is ordinary.
NON_NEGATIVE_DIMENSIONS = frozenset(
    {"VOLUME", "VOLUME_RATE", "POWER", "ENERGY", "IRRADIANCE"}
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
        display_name="Half-open interval and steps",
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
        display_name="A point applies once",
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
        display_name="A window's active span",
        statement=(
            "A window entry is active for every step whose start lies at or "
            "after its offset and before its offset plus its length. The step "
            "beginning exactly at the end of the window is outside it, so two "
            "windows that meet end to start never overlap by one step."
        ),
    ),
    DispatchRule(
        rule_id="quantity-across-a-window",
        display_name="A quantity across a window",
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
        display_name="An interval-wide entry",
        statement=(
            "An interval-wide entry starts at offset zero and holds until the "
            "run interval ends. It declares no length, because the length is "
            "the run's and choosing that is run setup."
        ),
    ),
    DispatchRule(
        rule_id="intra-instant-order",
        display_name="Two things at one instant",
        statement=(
            "Entries that take effect on one state at the same instant are a "
            "group with a net effect, and a bound is evaluated on that net "
            "rather than between the members. The order rows are written in "
            "is authoring and display; it is not a fact about the world, so "
            "it decides nothing here. Whether an ordering could have mattered "
            "is decided exactly rather than assumed: every increase first "
            "tests the upper bound, every decrease first tests the lower, and "
            "if neither extreme reaches a bound then no ordering does and the "
            "net stands. If one reaches a bound and the other does not, the "
            "group is genuinely ambiguous and the contract declines to answer "
            "rather than choosing an order. A scenario that needs one thing "
            "to happen before another says so in time, by separating the "
            "offsets."
        ),
    ),
    DispatchRule(
        rule_id="outside-the-interval",
        display_name="An entry outside the interval",
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
        display_name="Tank capacity",
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
        display_name="Delivery overflow",
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
        display_name="Insufficient fuel",
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
        display_name="Invalid rate or quantity",
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
OPEN_CAUSAL_WINDOW = (
    "a declared cause is still running when this reading is taken, and "
    "apportioning part of a window would be a transition rule rather than a "
    "contract"
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
    """The `(lower, upper)` a document declares for each world state.

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

        if (
            parameter.state_key is not None
            and dimension in IMPLICIT_LOWER_BOUND_DIMENSIONS
        ):
            lower.setdefault(
                parameter.state_key,
                IMPLICIT_LOWER_BOUND_DIMENSIONS[dimension],
            )

        bound = parameter.bounds
        if bound is None:
            continue
        if bound.bound_kind == "UPPER":
            upper[bound.state_key] = canonical_value
        else:
            lower[bound.state_key] = canonical_value

    return {
        state_key: (lower.get(state_key), upper.get(state_key))
        for state_key in set(lower) | set(upper)
    }


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
    #: Why the contract answered the way it did. Always present, because a
    #: `NOT_RECONCILABLE` with no reason is three different facts wearing one
    #: name: no declared initial value, an open causal window, and a declared
    #: bound reached are not the same problem and do not have the same fix.
    reason: str
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
    bounds_by_state = declared_bounds(scenario)

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
        bounds = bounds_by_state.get(state_key, (None, None))
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

        def unanswerable(reason: str) -> ObservationReconciliation:
            return ObservationReconciliation(
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
            # does and the net stands; if exactly one does, the group is
            # genuinely ambiguous and the contract will not pick an order.
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
                state_key=state_key,
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
