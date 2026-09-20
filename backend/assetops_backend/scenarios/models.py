"""Domain records for ScenarioDefinitions.

A `ScenarioDefinition` is the saved, versioned scenario artifact
(`D-2026-09-20-scenario-definition-model`). It carries scenario identity,
version identity, display metadata, a target-site requirement, a public
timeline, public parameters, and private expectations - and the last two are
separate fields on this record rather than one field a screen filters, because
a presentation-only split is not a boundary.

Three things this module deliberately is not.

It is not a Site model. `scenario_id`, `scenario_version`, `display_name` and
`event_id` are scenario identity; none of them is ever a `site_id`. The only
Site this package names is the one a scenario declares it needs, and it names
it as a requirement to be resolved elsewhere, not as a Site it owns.

It is not a run model. Nothing here records a start instant, a wall clock, a
timestep, a seed, an execution status, or a result. Those belong to
`SimulationRun`, which does not exist yet, and a field for one here would let a
scenario screen state something about an execution that has never happened.
Timeline entries are placed by an offset from the start of the simulated
interval, because the scenario knows the shape of what happens and not when it
was asked to happen.

It is not a control model. `D-2026-09-20-breaker-vocabulary` puts breaker
position and control mode on the evidence side of the product, so `OPEN`,
`CLOSED`, `TRIPPED`, `AUTO`, `MANUAL` and `BREAKER` are not scenario schema
vocabulary either. An equipment or intervention entry may describe an authored
cause or action in words and in parameters; it may not turn a position or a
mode into an entry kind, a category, a parameter key, or a unit. A scan in
`backend/tests/test_scenario_vocabulary.py` holds this over every closed
vocabulary below, over the parser's key vocabularies, over the shipped
definition and over the parser fixtures.

Two of the vocabularies below are provisional and the T017 user-review
checkpoint owns them: `EVENT_CATEGORIES` and `TIMELINE_ENTRY_KINDS` are this
project's proposal for the event taxonomy, and `SCENARIO_VERSION_FIELDS` names
the versioning field list being proposed. Provisional means the values may be
redirected by review; it does not mean the parser is lenient about them.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Provisional: the proposed scenario versioning fields -------------------
#
# The invariants are settled (`D-2026-09-20-scenario-definition-model`):
# identity and version are distinct, a version a run referenced is immutable,
# timeline identities are stable within a version, and a run freezes the
# concrete version it used rather than following latest. What is provisional is
# which fields carry that, and this is the proposal the detail screen puts in
# front of the user.
#
# Declared as data rather than as prose so the screen and the tests read the
# same list, and so a field added or dropped in code cannot disagree with the
# field list the user was asked to accept.
SCENARIO_VERSION_FIELDS = (
    "scenario_id",
    "scenario_version",
    "version_valid_from",
    "supersedes",
)

# --- Provisional: the proposed event taxonomy -------------------------------

# What sort of authored item a timeline row is. Three kinds, because
# `D-2026-09-20-scenario-definition-model` names three:  a `ScenarioEvent` is
# something the simulated world does, an authored `Intervention` is something a
# person does to it, and an `EvidenceCondition` is a condition the evidence
# path is expected to be under. All three are authored sub-artifacts inside a
# scenario version; none is a runtime injection, which is run-scoped and
# belongs to `SimulationRun` (`D-2026-09-20-run-scoped-event-injection`).
TIMELINE_ENTRY_KINDS = frozenset({"EVENT", "INTERVENTION", "EVIDENCE_CONDITION"})

# Which domain an authored cause or condition belongs to. The seven the T017
# task names, and no more: an eighth invented here would be a taxonomy the
# review was not asked about.
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

# --- Parameter and expectation vocabularies ---------------------------------

# Units an authored scenario parameter may carry. Closed, and separate from
# both `RATING_UNITS` and `SIGNAL_UNITS` in the Site models: a nameplate
# rating, a reportable signal and an authored scenario parameter are three
# different kinds of fact, and one vocabulary for all of them would let a
# scenario parameter borrow the authority of a declared rating.
PARAMETER_UNITS = frozenset(
    {"L", "L/h", "kW", "kWh", "V", "Hz", "degC", "W/m2", "%", "min", "h"}
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


@dataclass(frozen=True)
class ScenarioParameter:
    """One authored parameter: public authoring data.

    Public means a reader of the scenario is meant to see it in order to
    understand what the scenario does. It is not evidence and not a
    measurement: that a parameter says 120 L is removed is a statement about
    what the simulated world will be told to do, not about any fuel that ever
    moved.

    `unit` is present exactly when `value` is a number. A quantity without a
    unit is unreadable and a unit on a piece of text is meaningless, so the
    parser refuses both rather than letting a screen guess.
    """

    parameter_id: str
    display_name: str
    value: float | str
    unit: str | None


@dataclass(frozen=True)
class TimelineEntry:
    """One authored item inside a scenario version.

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
    """

    event_id: str
    sequence: int
    offset_minutes: int
    entry_kind: str
    category: str
    description: str
    parameters: tuple[ScenarioParameter, ...]


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

    The field list is the provisional proposal named in `SCENARIO_VERSION_FIELDS`
    above; the invariants it serves are settled.
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
    """

    scenario_id: str
    display_name: str
    purpose: str
    origin: str
    version: ScenarioVersion
    target_site: ScenarioTargetSite
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
