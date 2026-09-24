"""Domain records for ScenarioDefinitions.

A `ScenarioDefinition` is the saved, versioned scenario artifact
(`D-2026-09-20-scenario-definition-model`). It carries scenario identity,
version identity, display metadata, a target-site requirement, a public
timeline, public parameters, and private expectations - and the last two are
separate fields on this record rather than one field a screen filters, because
a presentation-only split is not a boundary.

T018 adds the second half of that: what each authored value MEANS to an
executor. Every public value carries an execution role, every timeline entry
carries a timing shape, every causal entry names the state it changes, and
every reported observation names the source it arrives through. The roles are
the machine-readable answer to a question T017 left open - whether a row
prescribes a cause or describes a later observation - and
`D-2026-09-21-causal-runtime-before-golden-traces` is why it has to be answered
before run setup rather than after.

Three things this module deliberately is not.

It is not a Site model. `scenario_id`, `scenario_version`, `display_name` and
`event_id` are scenario identity; none of them is ever a `site_id`. The only
Site this package names is the one a scenario declares it needs, and it names
it as a requirement to be resolved elsewhere, not as a Site it owns. A device
or signal identity on an observation source is a REFERENCE into the target
Site's Foundation, resolved by the service, never owned here.

It is not a run model. Nothing here records a start instant, a wall clock, a
timestep, a seed, an execution status, or a result. Those belong to
`SimulationRun`, which does not exist yet, and a field for one here would let a
scenario screen state something about an execution that has never happened.
Timeline entries are placed by an offset from the start of the simulated
interval, because the scenario knows the shape of what happens and not when it
was asked to happen.

It is not a state trajectory. An execution role says what an executor may do
with a value; it does not say what the world was. `REPORTED_OBSERVATION`
carries the strongest form of that: a reported value has no ownership record,
because a record with one could initialize private state, and a value that can
initialize private state is a prescribed trajectory wearing an observation's
name.

It is not a control model. `D-2026-09-20-breaker-vocabulary` puts breaker
position and control mode on the evidence side of the product, so `OPEN`,
`CLOSED`, `TRIPPED`, `AUTO`, `MANUAL` and `BREAKER` are not scenario schema
vocabulary either. An equipment or intervention entry may describe an authored
cause or action in words and in parameters; it may not turn a position or a
mode into an entry kind, a category, a parameter key, a state key, or a unit. A
scan in `backend/tests/test_scenario_vocabulary.py` holds this over every
closed vocabulary below, over the parser's key vocabularies, over the shipped
definition and over the parser fixtures.

The versioning fields, the entry kinds and the categories were accepted at the
T017 user-review checkpoint on 2026-09-21 and are recorded in
`D-2026-09-21-scenario-authoring-semantics`. They are settled values. The
execution vocabularies T018 adds are not yet: they carry this slice's review.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- The accepted scenario versioning fields --------------------------------
#
# Accepted at the T017 checkpoint (`D-2026-09-21-scenario-authoring-semantics`).
# The invariants they serve were settled earlier, by
# `D-2026-09-20-scenario-definition-model`: identity and version are distinct, a
# version a run referenced is immutable, timeline identities are stable within a
# version, and a run freezes the concrete version it used rather than following
# latest.
#
# Declared as data rather than as prose so the screen and the tests read the
# same list, and so a field added or dropped in code cannot disagree with the
# field list the user accepted.
SCENARIO_VERSION_FIELDS = (
    "scenario_id",
    "scenario_version",
    "version_valid_from",
    "supersedes",
)

# --- The accepted event taxonomy --------------------------------------------

# What sort of authored item a timeline row is. Three kinds, because
# `D-2026-09-20-scenario-definition-model` names three:  a `ScenarioEvent` is
# something the simulated world does, an authored `Intervention` is something a
# person does to it, and an `EvidenceCondition` is a condition the evidence
# path is expected to be under. All three are authored sub-artifacts inside a
# scenario version; none is a runtime injection, which is run-scoped and
# belongs to `SimulationRun` (`D-2026-09-20-run-scoped-event-injection`).
TIMELINE_ENTRY_KINDS = frozenset({"EVENT", "INTERVENTION", "EVIDENCE_CONDITION"})

# Which domain an authored cause or condition belongs to. Seven, accepted as
# proposed; an eighth invented here would be a taxonomy nobody reviewed.
#
# `LOSS_OR_FRAUD` rather than `LOSS/FRAUD` because a value is an identifier
# here, not a sentence, and `EQUIPMENT` covers an authored equipment cause such
# as a generator being unavailable without naming what state any element is in.
EVENT_CATEGORIES = frozenset(
    {
        "LOAD",
        "WEATHER",
        "EQUIPMENT",
        "DATA_QUALITY",
        "LOSS_OR_FRAUD",
        "INTERVENTION",
        "MAINTENANCE",
    }
)

# --- The execution contract: what an executor may do with a value -----------
#
# The kind axis above says what sort of authored item something is. This axis
# says how it executes, and the two are orthogonal on purpose: an evidence
# condition and a reported observation are the same row seen by an author and
# by an executor, and collapsing them would make the row's meaning depend on
# who is reading it.
#
# - `CAUSAL_INPUT` initializes or transitions private world state. It is the
#   only role that may do so.
# - `FORCING_INPUT` is an exogenous condition the run is subjected to -
#   environmental, demand-side, or on the reporting path. It may influence
#   private state and it names the state it forces, but it is not a transition
#   the scenario computes.
# - `REPORTED_OBSERVATION` is a value that arrives through a named source. It
#   may never initialize or mutate private state; a kernel that let one do so
#   would be reading an authored trajectory back in as truth.
# - `NON_EXECUTABLE_CONDITION` is authored description an executor does not
#   consume: a value stating what the interval is expected to look like rather
#   than what it is told to do.
EXECUTION_ROLES = frozenset(
    {
        "CAUSAL_INPUT",
        "FORCING_INPUT",
        "REPORTED_OBSERVATION",
        "NON_EXECUTABLE_CONDITION",
    }
)

#: The roles an executor consumes. A value outside this set is description; a
#: value inside it must be supported by the chosen model profile or later run
#: setup is blocked, because ignoring one silently would make a run claim to
#: have executed a scenario it partly skipped.
EXECUTABLE_ROLES = frozenset(
    {"CAUSAL_INPUT", "FORCING_INPUT", "REPORTED_OBSERVATION"}
)

#: The roles that may reach initialization or a private-state transition. One.
#:
#: This is enforced rather than described, in two places that do not depend on
#: each other: `_parse_ownership` refuses `initializes: true` outside this set,
#: and `initialization_inputs` skips any parameter whose role is outside it.
#:
#: The T018 review found the gap this closes. A forcing input could declare
#: `initializes: true` and came back as the initializer of a world state,
#: while the screen's role legend said in so many words that only a causal
#: input could reach private state. A `USER_REVIEW_REQUIRED` screen asserting
#: a guarantee the code did not hold would have locked the guarantee in.
#:
#: The rule is also the truer contract. An exogenous state's value at every
#: instant comes from the forcing profile itself, including the first, so a
#: separate initial-value declaration beside it would be two answers to what
#: that state is at the start of the interval.
STATE_CHANGING_ROLES = frozenset({"CAUSAL_INPUT"})

#: Which execution roles each timeline entry kind may carry.
#:
#: The load-bearing row is `EVIDENCE_CONDITION`. An evidence condition states
#: what the evidence path is expected to be in, so it may be delivered as a
#: reported observation or carried as description - and it may never be a cause.
#: An evidence condition that could be a `CAUSAL_INPUT` is exactly the ambiguity
#: T018 exists to remove: the same row would prescribe both a cause and its own
#: expected result.
#:
#: An `EVENT` may not be a reported observation for the mirror-image reason: an
#: event is something the simulated world does, and a reading is not.
ROLES_BY_ENTRY_KIND = {
    "EVENT": frozenset(
        {"CAUSAL_INPUT", "FORCING_INPUT", "NON_EXECUTABLE_CONDITION"}
    ),
    "INTERVENTION": frozenset(
        {"CAUSAL_INPUT", "REPORTED_OBSERVATION", "NON_EXECUTABLE_CONDITION"}
    ),
    "EVIDENCE_CONDITION": frozenset(
        {"REPORTED_OBSERVATION", "NON_EXECUTABLE_CONDITION"}
    ),
}

#: Whether a later run setup may proceed without support for this input.
#:
#: `REQUIRED` means the chosen model profile must support the input's state key
#: or the Draft is `BLOCKED`. `OPTIONAL` means a profile may leave it
#: unsupported and say so. There is no third value, because "supported if
#: convenient" is how an input gets ignored.
EXECUTION_REQUIREMENTS = frozenset({"REQUIRED", "OPTIONAL"})

#: Who owns an initial world value or a model coefficient.
#:
#: `SITE_FOUNDATION` means the target Site's Foundation is the authority and the
#: scenario's value is the requirement run setup must check against it, not the
#: value a run uses. `SCENARIO_INPUT` means the scenario is the authority.
#: `RUN_OVERRIDE` means a run must supply it and the scenario's value is only a
#: default. `MODEL_RULE` means a versioned simulator rule supplies it.
#:
#: Four owners and no fifth, because "wherever the recording got it" is the
#: thing `D-2026-09-21-causal-runtime-before-golden-traces` forbids: a trace may
#: not hide or invent an initial condition.
INITIALIZATION_OWNERS = frozenset(
    {"SITE_FOUNDATION", "SCENARIO_INPUT", "RUN_OVERRIDE", "MODEL_RULE"}
)

#: How an entry is placed in time.
#:
#: `POINT` happens at its offset and has no length. `WINDOW` runs over
#: `[offset, offset + duration)` and must declare the duration. `INTERVAL_WIDE`
#: holds for the whole simulated interval, so it starts at offset zero and has
#: no authored length - the scenario does not know how long the interval is,
#: because choosing that is run setup.
#:
#: The distinction is validated rather than conventional: a point with a length
#: and a window without one are both refused, and a rate may only be applied
#: over a window, because a rate at an instant moves nothing.
TIMING_SHAPES = frozenset({"POINT", "WINDOW", "INTERVAL_WIDE"})

#: Which way a causal entry moves the state it names.
STATE_EFFECT_DIRECTIONS = frozenset({"INCREASE", "DECREASE"})

#: Which end of another state a declared world value bounds.
#:
#: Capacity was a world state with nothing connecting it to the volume it
#: limits, so the contract could report a declared level above a capacity the
#: same document declares - which the T018 review reproduced. A bound is now
#: declared rather than inferred from two state keys that happen to share a
#: prefix.
BOUND_KINDS = frozenset({"UPPER", "LOWER"})

#: What a reported observation arrives through.
#:
#: `DEVICE_SIGNAL` names a device and a signal the target Site's Foundation
#: configures. `OPERATOR_RECORD` is a person writing a value down, which has an
#: identity but no device and no signal - the criterion T018 carries is that a
#: hand-recorded level must not borrow a device's identity to look reported.
OBSERVATION_SOURCE_KINDS = frozenset({"DEVICE_SIGNAL", "OPERATOR_RECORD"})

#: Who owns the cadence a source reports at.
#:
#: `NOT_DECLARED` is the truthful answer for every device signal in this build.
#: Foundation declares that a signal CAN report and declares its unit; it
#: declares no cadence, and nothing in this product may infer one from a device
#: name, from display text, or from the spacing between authored entries. A
#: cadence arrives when a versioned observation profile declares one.
#:
#: `NOT_APPLICABLE` is the truthful answer for an operator record: a person
#: writing a level down has no reporting rate to own.
#:
#: There is deliberately no value meaning "the scenario declares it". A
#: scenario that could declare a cadence would be authoring the observation
#: profile, and the profile is versioned simulator configuration rather than
#: scenario content.
CADENCE_OWNERSHIP = frozenset({"NOT_DECLARED", "NOT_APPLICABLE"})

# --- Parameter and expectation vocabularies ---------------------------------

# Units an authored scenario parameter may carry. Closed, and separate from
# both `RATING_UNITS` and `SIGNAL_UNITS` in the Site models: a nameplate
# rating, a reportable signal and an authored scenario parameter are three
# different kinds of fact, and one vocabulary for all of them would let a
# scenario parameter borrow the authority of a declared rating.
#
# Every unit here has a canonical dimension and conversion in
# `scenarios/execution.py`, asserted exhaustively by a test, so a consumer
# converts a quantity without parsing the display text a screen shows.
#
# No duration unit is in this set, and its absence is load-bearing. An entry's
# length is declared by `timing.duration_minutes` and nowhere else, so a
# duration written as a parameter is either a reporting cadence - which a
# scenario does not own - or a length in the wrong field. Leaving `min` and
# `h` here would have left a position at every parameter in the document for
# one to arrive in, which is the hole the T018 review found when the rule
# against it was written for one position only.
#
# `L/kWh` arrives with T020A. Specific fuel consumption is a property of the
# machine alone, where `L/h` is a property of the machine times its operating
# point (`D-2026-09-22-consumption-coefficient-unit`). `L/h` stays in the
# vocabulary: it is a legitimate authored rate for a cause that genuinely
# declares one, and nothing in the shipped document uses it any more.
PARAMETER_UNITS = frozenset(
    {"L", "L/h", "L/kWh", "kW", "kWh", "V", "Hz", "degC", "W/m2", "%"}
)

# What a private expectation asserts. Test-oracle vocabulary: each value names
# the kind of claim a future test would make about a run of this scenario, and
# none of them is a product claim, a Finding, a severity, or a confidence.
EXPECTATION_KINDS = frozenset(
    {"DETECTION", "MAGNITUDE", "TIMING", "NO_FALSE_POSITIVE"}
)

# How a scenario declares which Site it needs.
#
# `DECLARED_SITE` names a concrete `site_id` the scenario expects to exist.
# `TEMPLATE_DERIVED` names the archetype a Site would have to be built from,
# and carries no `site_id` at all, because no Site has been chosen yet. The
# parser checks the shape of the declaration; whether a declared `site_id`
# resolves to a configured Site is a detail-screen state, decided by the
# service against the Site repository, and never a parser failure.
TARGET_SITE_POLICIES = frozenset({"DECLARED_SITE", "TEMPLATE_DERIVED"})

# Where this scenario's definition DOCUMENT came from: did the product ship it
# read-only, or does it live in the writable user store? Provenance about the
# document, never about evidence and never about identity - a user scenario is
# not prefixed and nothing can tell the two apart by reading a `scenario_id`.
#
# It is supplied by the store rather than declared by the document, so a user
# document cannot claim to be shipped.
SCENARIO_ORIGINS = frozenset({"SHIPPED", "USER"})

# The states the scenario detail read model can report about the declared
# target Site. Four, and they are four different facts: the Site resolved, no
# such Site is configured, this scenario names no concrete Site to resolve, and
# the Site store could not be read so nothing is known.
TARGET_RESOLUTION_STATES = frozenset(
    {"RESOLVED", "NOT_CONFIGURED", "NOT_APPLICABLE", "UNAVAILABLE"}
)

# The states an observation source's declared device and signal can be in on
# this installation. The same four facts as a target Site, for the same reason:
# a scenario declares what it needs, and what this installation has is a read
# against the Site store that must not make a readable scenario unreadable.
OBSERVATION_SOURCE_RESOLUTION_STATES = frozenset(
    {"RESOLVED", "NOT_CONFIGURED", "NOT_APPLICABLE", "UNAVAILABLE"}
)


@dataclass(frozen=True)
class ParameterOwnership:
    """Who owns a value an executor would consume, and whether it initializes.

    `initializes` is the difference between "the tank starts at this level" and
    "the generator burns at this rate". Both are inputs a kernel needs and both
    must be attributable, but only the first is an initial world value, and
    `D-2026-09-21-causal-runtime-before-golden-traces` requires exactly one
    attributable answer for each of those.

    A reported observation never carries one of these. That is the structural
    guarantee, not a convention: there is no field on a reported value that
    could name it as the source of an initial state.
    """

    owner: str
    initializes: bool


@dataclass(frozen=True)
class ParameterBound:
    """That this world value limits another one, and at which end.

    Declared, never inferred. `fuel-tank-capacity` and `fuel-tank-volume` are
    two state keys, and nothing about their spellings says one limits the
    other; a contract that guessed from a shared prefix would be guessing.
    """

    state_key: str
    bound_kind: str


@dataclass(frozen=True)
class ScenarioParameter:
    """One authored parameter: public authoring data, with its execution role.

    Public means a reader of the scenario is meant to see it in order to
    understand what the scenario does. It is not evidence and not a
    measurement: that a parameter says 120 L is removed is a statement about
    what the simulated world will be told to do, not about any fuel that ever
    moved.

    `unit` is present exactly when `value` is a number OR when the Site's
    Foundation is the declared owner. A quantity without a unit is unreadable
    and a unit on a piece of text is meaningless, so the parser refuses both
    rather than letting a screen guess.

    **`value` is `None` exactly when `ownership.owner` is `SITE_FOUNDATION`**,
    and that is a structure rather than a rule to remember
    (`D-2026-09-22-foundation-value-declaration`). A Foundation-owned
    parameter declares the NEED - the state, the unit, and that the Foundation
    answers - and states no number, because a machine's physical property is
    not the story's to carry. There is no position in the document for the
    number, so an author cannot put one there and a run cannot be told to
    check the Foundation against it.

    `state_key`, `execution_requirement` and `ownership` are present exactly
    when the role calls for them, and the parser refuses every other
    combination:

    - an executable role names the state it concerns and says whether a later
      run setup may proceed without support for it;
    - a causal or forcing input declares ownership;
    - a reported observation declares none, so it cannot initialize anything;
    - a non-executable condition declares neither, so nothing consumes it.
    """

    parameter_id: str
    display_name: str
    value: float | str | None
    unit: str | None
    execution_role: str
    state_key: str | None
    execution_requirement: str | None
    ownership: ParameterOwnership | None
    bounds: ParameterBound | None


@dataclass(frozen=True)
class EntryTiming:
    """How one entry is placed in time, beside the offset that places it.

    Held apart from `offset_minutes` because a shape and a position answer
    different questions, and because the dispatch rule differs by shape: a
    point is applied exactly once in the step whose half-open span contains it,
    and a window is active for every step whose start lies inside
    `[offset, offset + duration)`.
    """

    shape: str
    duration_minutes: int | None


@dataclass(frozen=True)
class StateEffect:
    """What a causal entry changes, and by how much.

    Exactly one of `quantity_parameter_id` and `rate_parameter_id` is set, and
    both name a parameter this scenario declares rather than repeating its
    number. A quantity is applied once; a rate is applied across a window, so a
    rate effect on a point entry is refused - a rate at an instant moves
    nothing and an author who wrote one meant something else.

    The state it changes is the entry's `state_key`, not a second declaration
    here: two places to name the state would be two answers to what a
    transition touches.

    Only a `CAUSAL_INPUT` entry has one. That is the whole of the private-state
    transition surface a scenario can reach.
    """

    direction: str
    quantity_parameter_id: str | None
    rate_parameter_id: str | None


@dataclass(frozen=True)
class ObservationBinding:
    """Which source a reported entry arrives through, and which value it carries.

    `source_id` names one of the scenario's declared observation sources, so
    the device or the person behind a reading is explicit rather than implied
    by an entry's wording. `reported_parameter_id` names the parameter on this
    entry that carries the value, so a reading is one identified quantity and
    not whichever parameter a reader picks.
    """

    source_id: str
    reported_parameter_id: str


@dataclass(frozen=True)
class ObservationSource:
    """Where a reported observation comes from.

    A `DEVICE_SIGNAL` source names a `device_id` and a `signal_id` from the
    target Site's Foundation. Those are references into the Site identity
    space: the parser validates their shape and the service resolves them, in
    exactly the split the target-site declaration already uses.

    An `OPERATOR_RECORD` source names neither, and that absence is the point.
    A hand-recorded level is a real observation with a real identity, and
    giving it a device identity it does not have would put a person's note into
    the evidence path wearing a sensor's name.

    `cadence_ownership` is always a statement about who owns the reporting rate
    and never a rate. Foundation declares that a signal can report and declares
    no cadence, so a device source says `NOT_DECLARED` until a versioned
    observation profile exists to own one.
    """

    source_id: str
    source_kind: str
    device_id: str | None
    signal_id: str | None
    cadence_ownership: str
    description: str


@dataclass(frozen=True)
class TimelineEntry:
    """One authored item inside a scenario version, and how it executes.

    Addressed by `(scenario_id, scenario_version, event_id)`: a saved
    sub-artifact of the definition, not a top-level stored entity. `event_id`
    is unique within its version and stable for the life of that version, which
    is what lets a future run refer to one of these without the scenario being
    able to move it underneath.

    `sequence` is the authored order and `offset_minutes` is the placement
    relative to the start of the simulated interval. Both are carried because
    they answer different questions: two entries may share an offset and still
    have an authored order, and a screen must render the order the document
    declares rather than whatever order a store returned.

    `state_key` is the one place an executable entry names what it concerns,
    whether it causes it, forces it, or reports it.

    `state_effect` is present exactly when the role is `CAUSAL_INPUT`;
    `observation` exactly when it is `REPORTED_OBSERVATION`. They are mutually
    exclusive by construction, which is how a reported value is kept out of the
    private-state transition inputs: there is no field it could arrive in.
    """

    event_id: str
    sequence: int
    offset_minutes: int
    entry_kind: str
    category: str
    description: str
    parameters: tuple[ScenarioParameter, ...]
    execution_role: str
    state_key: str | None
    execution_requirement: str | None
    timing: EntryTiming
    state_effect: StateEffect | None
    observation: ObservationBinding | None


@dataclass(frozen=True)
class PrivateExpectation:
    """One test-oracle expectation: private metadata, and never product data.

    `D-2026-09-20-scenario-definition-model`: a `PrivateExpectation` is not
    pipeline input, not public authoring data, not product evidence, not
    operator UI, and not product provenance. It exists so that a future test
    can decide whether a run of this scenario did what the scenario was written
    to exercise.

    It is a separate record type, held in a separate field of
    `ScenarioDefinition`, and rendered by a separate payload builder. That is
    the separation: a public payload cannot leak one by omission, because it
    never reads the field these live in.
    """

    expectation_id: str
    display_name: str
    oracle_kind: str
    statement: str


@dataclass(frozen=True)
class ScenarioTargetSite:
    """Which Site this scenario needs, as a declaration rather than a link.

    Exactly one of `site_id` and `template_id` is set, decided by `policy`. The
    parser enforces that shape; it never looks a Site up, because whether a
    declared Site is configured on this installation is a fact about the Site
    store at read time and not a property of the scenario document. A shipped
    scenario that named a Site nobody had configured would otherwise be
    unreadable on a fresh checkout.

    `requirement` says in words what the scenario needs of that Site, so a
    reader can tell whether a different Site would do.
    """

    policy: str
    site_id: str | None
    template_id: str | None
    requirement: str


@dataclass(frozen=True)
class ScenarioVersion:
    """Version identity, distinct from scenario identity.

    `scenario_version` is what a future run freezes. `version_valid_from` is
    when this version became the authored version. `supersedes` is the version
    this one replaced, or `None` for the first, so drift between versions stays
    inspectable without a separate history store.

    The field list is `SCENARIO_VERSION_FIELDS`, accepted at the T017
    checkpoint.
    """

    scenario_version: int
    version_valid_from: str
    supersedes: int | None


@dataclass(frozen=True)
class ScenarioDefinition:
    """One saved, versioned scenario.

    `scenario_id` is the only scenario identity. The display name is not
    identity, the version is not identity, and none of them is ever a Site
    identity.

    `public_parameters` and `private_expectations` are two fields, not one
    field with a visibility flag. A flag would put the boundary in whoever
    renders the record; two fields put it in the parser, which is where
    `D-2026-09-20-scenario-definition-model` puts it.

    `observation_sources` is public authoring data too. A reader has to be able
    to see which device or which person each reported value arrives through,
    because that is the difference between an observation and a prescription.
    """

    scenario_id: str
    display_name: str
    purpose: str
    origin: str
    version: ScenarioVersion
    target_site: ScenarioTargetSite
    observation_sources: tuple[ObservationSource, ...]
    timeline: tuple[TimelineEntry, ...]
    public_parameters: tuple[ScenarioParameter, ...]
    private_expectations: tuple[PrivateExpectation, ...]


@dataclass(frozen=True)
class ScenarioTargetResolution:
    """What the detail read model found when it resolved the declared target.

    A detail-screen state, produced by the service against the `SiteRepository`
    port. An unresolvable target Site is one of these, never a parser failure
    and never an unreadable scenario.

    `site_id` carries the store's canonical spelling when the Site resolved, so
    a link is built from what is configured rather than from what the scenario
    document happened to capitalise. `reason` is the accessible text a disabled
    or absent control carries; it is always present, because a control that is
    unavailable without a visible reason is a dead end.
    """

    state: str
    site_id: str | None
    display_name: str | None
    reason: str


@dataclass(frozen=True)
class ObservationSourceResolution:
    """What a declared observation source resolved to on this installation.

    Beside the source rather than inside it, for the same reason a target-site
    resolution is beside the scenario: it is what this installation's Site
    store answered, not something the document says about itself.

    `device_display_name` and `signal_display_name` come from Foundation when
    the source resolved, so a screen names the configured device rather than
    echoing the identity the scenario typed. `cadence_statement` is always
    present and always says who owns the cadence; it never states one, because
    Foundation declares none and nothing here may invent one.
    """

    source_id: str
    state: str
    device_display_name: str | None
    signal_display_name: str | None
    reason: str
    cadence_statement: str
