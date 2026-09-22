"""Domain records for a Draft SimulationRun and the inputs it freezes.

A `SimulationRun` is an execution and provenance record. T019 creates one in
`DRAFT` and freezes what a later kernel would consume; it executes nothing, so
there is no clock here, no step cursor, no state trajectory, no staged
envelope, no commit eligibility, and no evidence. There is no field any of
those could arrive in.

Three things this module deliberately is not.

It is not a Site model and it is not a scenario model. `run_id` is the only run
identity, and it is never a `site_id` and never a `scenario_id`. What the run
carries of the other two is a REFERENCE - an identity and the exact version -
and never a copy of their content: no site name, no device name, no lifecycle
status, no configuration origin, no source mode. `tools/checks/run-setup.ps1`
holds that structurally, because the acceptance criterion this slice carries is
that nothing about a run may be inferred from a Site's provenance or from what
a screen calls a device.

It is not a model profile. What a profile supports, and what cadence, source
identity and gateway identity it resolves, lives in `runs/profiles.py`, because
those are versioned simulator rules rather than run inputs. The run freezes
WHICH profile answered and WHAT it answered, so the same run is reproducible
without the profile catalog having to be frozen with it.

It is not a run inventory. T019 returns the setup summary for the Draft it just
created. Listing runs, presenting one, and offering anything to do with one are
T020's, and this record is the thing those will read.

## The frozen deterministic identity

`DeterministicIdentity` is the whole of what makes a run reproducible, and each
of its parts names who answered for it. That is what
`D-2026-09-21-causal-runtime-before-golden-traces` requires: an initial
condition must be explicit and attributable, and a trace may not hide or invent
one. `frozen_inputs` in `runs/provenance.py` turns the identity into one row per
frozen value, each carrying its answerer, and a test asserts every field of
this record is represented there - so a field added here without an answerer
fails the build rather than arriving on a screen with no origin.

`run_id` is deliberately NOT part of the deterministic identity. Two Drafts set
up from identical inputs are two runs of the same experiment, which is what
makes overlapping Drafts useful; if the identity carried the run's own name,
every run would be trivially unique and the identity would answer nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Where a run is in its own life. One value today: T019 creates Drafts and
#: nothing in this build can commit one. `COMMITTED` arrives with the slice
#: that can release evidence, and adding it here first would put a lifecycle
#: on screen that nothing can reach.
RUN_LIFECYCLE_STATUSES = frozenset({"DRAFT"})

#: Whether the frozen inputs can be executed by the profile the run selected.
#:
#: `READY` means every executable input the scenario requires is supported and
#: every profile-resolved input resolved. `BLOCKED` means at least one is not,
#: and the run carries the reasons. There is deliberately no third value: a run
#: that is neither is a run whose status was decided by whoever read it.
#:
#: The statuses a run acquires by running - `RUNNING`, `PAUSED`, `COMPLETED`,
#: `FAILED` - are absent, because nothing in this build can produce one and a
#: status nothing can reach is a claim that execution exists.
RUN_EXECUTION_STATUSES = frozenset({"READY", "BLOCKED"})

#: Who answers for one frozen value.
#:
#: The four correspond exactly to the four initialization owners T018 settled
#: (`INITIALIZATION_OWNERS`), and `ANSWERER_BY_INITIALIZATION_OWNER` below is
#: that correspondence written down. They are a separate vocabulary because
#: they answer a wider question - who answers for the interval, the seed, the
#: cadence - and not only who owns an initial world value. A test asserts the
#: mapping below covers `INITIALIZATION_OWNERS` exactly and lands inside this
#: set, so a fifth owner on either side fails rather than quietly having no
#: answerer.
FROZEN_INPUT_ANSWERERS = frozenset(
    {"SITE_FOUNDATION", "SCENARIO", "RUN_INPUT", "MODEL_PROFILE"}
)

ANSWERER_BY_INITIALIZATION_OWNER = {
    "SITE_FOUNDATION": "SITE_FOUNDATION",
    "SCENARIO_INPUT": "SCENARIO",
    "RUN_OVERRIDE": "RUN_INPUT",
    "MODEL_RULE": "MODEL_PROFILE",
}

#: Why a fully frozen Draft may not execute.
#:
#: Every one of these is a fact about the frozen run, inspectable after the
#: Draft is persisted. None of them is a reason to refuse setup: a refusal
#: means the request could not be frozen at all, and those allocate no
#: `run_id`. The split is the acceptance criterion this slice carries and it is
#: stated once, here.
#:
#: - `STATE_NOT_SUPPORTED`: the selected model profile does not model the world
#:   state a required executable input concerns.
#: - `ROLE_NOT_SUPPORTED`: it models the state but not in the role this input
#:   uses it - it can be caused but not reported, or the reverse.
#: - `CADENCE_NOT_RESOLVED`: a source whose cadence nobody owns yet, and a
#:   publication profile that declares none. Nothing infers one, so the run
#:   blocks rather than reporting at a rate somebody guessed.
#: - `SOURCE_IDENTITY_NOT_RESOLVED` and `GATEWAY_IDENTITY_NOT_RESOLVED`: the
#:   same rule for the two publication identities.
#: - `INITIAL_VALUE_NOT_RESOLVED`: an initial world value the selected profile
#:   cannot supply or cannot locate. Named for the state it leaves the value
#:   in rather than for the cause, because the causes differ - a profile that
#:   declares no binding for a Foundation-owned value, one whose binding
#:   matches nothing or matches twice, and one that declares no rule for a
#:   value a scenario says a versioned model rule owns - and a reader needs
#:   the same name for all of them: this run has no answer for that value and
#:   a different profile may.
#:
#: Every one of the six is a statement about the SELECTED PROFILE: something
#: the scenario requires that the profile does not model, does not resolve, or
#: cannot locate. That is the whole of what run setup can decide, and a
#: seventh member was removed to make it so. `OBSERVATION_NOT_ACCOUNTED_FOR`
#: blocked a run when the causes a scenario declares did not reach a reading
#: the same scenario declares, and Amendment 1's proposal (e) took it out: run
#: setup has no kernel, so it cannot settle a comparison only an execution can
#: settle. A kind added here that is not about the profile's ability to
#: execute an input is the same mistake returning.
BLOCKING_REASON_KINDS = frozenset(
    {
        "STATE_NOT_SUPPORTED",
        "ROLE_NOT_SUPPORTED",
        "CADENCE_NOT_RESOLVED",
        "SOURCE_IDENTITY_NOT_RESOLVED",
        "GATEWAY_IDENTITY_NOT_RESOLVED",
        "INITIAL_VALUE_NOT_RESOLVED",
    }
)

#: What a cadence statement on a frozen source is about.
#:
#: `MODEL_PROFILE` means the selected publication profile declared one and the
#: run froze it. `NOT_APPLICABLE` means the source has no reporting rate to
#: own, which is the truthful answer for a hand-recorded value. `NOT_RESOLVED`
#: means nobody declared one, which is a blocking reason rather than a default.
#:
#: There is no value meaning "inferred". A cadence read off a device's name, a
#: screen's text, or the spacing between authored entries is the thing this
#: vocabulary exists to make unwritable.
CADENCE_RESOLUTIONS = frozenset(
    {"MODEL_PROFILE", "NOT_APPLICABLE", "NOT_RESOLVED"}
)


@dataclass(frozen=True)
class FrozenSiteBinding:
    """Which Site and which Foundation version this run is bound to.

    An identity and a version, and nothing a screen would call a name. A run
    that carried the site's name would carry a value that can change under it
    while the identity it froze stayed the same.
    """

    site_id: str
    foundation_version: int
    foundation_valid_from: str
    site_type: str
    timezone: str


@dataclass(frozen=True)
class FrozenParameter:
    """One resolved public parameter, as the run will supply it.

    `answered_by` is `SCENARIO` for a value the scenario owns and `RUN_INPUT`
    for one the run supplied because the scenario said the run owns it. There
    is no third case: a parameter the scenario owns cannot be overridden, and
    one the run owns must be supplied, so no value here was defaulted.
    """

    parameter_id: str
    value: float | str
    unit: str | None
    answered_by: str


@dataclass(frozen=True)
class FrozenScenarioBinding:
    """Which scenario version this run froze, and its resolved parameters."""

    scenario_id: str
    scenario_version: int
    resolved_parameters: tuple[FrozenParameter, ...]


@dataclass(frozen=True)
class FrozenInterval:
    """The simulated interval and the step it is walked in.

    Half-open, `[start_time, end_time)`, as `DISPATCH_RULES` requires: an
    instant belongs to exactly one step, which is what makes "applied exactly
    once" a property of the time model rather than of whoever reads it.

    The instants are UTC, because an interval is a pair of instants and an
    instant does not need a zone to be one. The zone this run is placed in
    local time by is the target Site's and lives on `FrozenSiteBinding`, where
    the Site answers for it; a second copy here would be a second answer to
    what time zone the run is in.
    """

    start_time: str
    end_time: str
    duration_minutes: int
    timestep_minutes: int


@dataclass(frozen=True)
class FrozenProfileBinding:
    """Which versioned profiles answered, and against which contract."""

    model_profile_id: str
    model_profile_version: int
    publication_profile_id: str
    publication_profile_version: int
    execution_contract_version: int


@dataclass(frozen=True)
class FrozenInitializationInput:
    """One initial world value, frozen with the owner that answered for it.

    No display text: a run freezes the state key, the parameter identity, the
    value and its unit. What to call them on a screen is presentation, and a
    name copied into a run record is a second copy of something that can change
    underneath it.

    **`value` has an absent case**, the way `cadence_minutes` does on the
    binding beside it, and for the same reason. When the selected profile
    cannot supply or locate the value, the Draft is `BLOCKED` rather than
    refused - a different profile may answer, so the person gets a persisted
    run to inspect - and the record has to be able to say "this value has no
    answer" rather than being unable to represent it. `canonical_value` is
    absent exactly when `value` is; the unit is not, because the scenario
    declares it whether or not anything answers.

    A `READY` run may not carry one. `SimulationRun` enforces that: an absent
    value always has a blocking reason beside it, because the thing that made
    it absent is the thing that blocked the run.
    """

    state_key: str
    parameter_id: str
    value: float | None
    unit: str
    canonical_value: float | None
    canonical_unit: str
    dimension: str
    answered_by: str
    answered_by_detail: str


@dataclass(frozen=True)
class FrozenObservationBinding:
    """One declared observation source, with the cadence the profile resolved.

    `cadence_minutes` is present only when a publication profile declared one.
    Foundation declares that a signal can report and declares no rate; nothing
    here derives one from a device identity, from what a screen shows, or from
    the spacing between the entries that report through this source.
    """

    source_id: str
    source_kind: str
    device_id: str | None
    signal_id: str | None
    cadence_ownership: str
    cadence_minutes: int | None
    cadence_resolution: str


@dataclass(frozen=True)
class FrozenPublicationIdentity:
    """The simulator source and gateway a run would publish through.

    Both come from the selected publication profile or from nowhere. Neither is
    derived from the Site's provenance, from a device identity, or from the
    Site's source mode - which is the criterion, and which is why this record
    holds two identities and no fallback.
    """

    simulator_source_id: str | None
    gateway_id: str | None


@dataclass(frozen=True)
class FrozenSignalMapping:
    """One device-to-signal mapping the Foundation declares, frozen by identity.

    The mappings are part of the deterministic identity because a later run
    binds simulated quantities to them; freezing which ones were in force is
    what lets a rerun be compared against this run rather than against a
    Foundation that has since been re-created.
    """

    mapping_id: str
    device_id: str
    signal_id: str
    component_id: str


@dataclass(frozen=True)
class UnsupportedOptionalInput:
    """An executable input the profile does not support, and need not.

    `EXECUTION_REQUIREMENTS` has two values and no third, so an input is either
    required - and blocks when unsupported - or optional, and is recorded here
    instead. Recorded rather than dropped: a run that quietly ignored part of a
    scenario would claim to have executed something it partly skipped.
    """

    state_key: str
    execution_role: str
    statement: str


@dataclass(frozen=True)
class DeterministicIdentity:
    """Everything a rerun would have to reproduce to be the same run.

    Every field is answered for by exactly one of the four answerers, and
    `frozen_inputs` states which. `intervention_history` is ordered and empty:
    nothing in this build can inject a runtime event, and the order is part of
    the identity even while the list has nothing in it.
    """

    site: FrozenSiteBinding
    scenario: FrozenScenarioBinding
    interval: FrozenInterval
    seed: int
    profiles: FrozenProfileBinding
    initialization_inputs: tuple[FrozenInitializationInput, ...]
    observation_bindings: tuple[FrozenObservationBinding, ...]
    publication: FrozenPublicationIdentity
    signal_mappings: tuple[FrozenSignalMapping, ...]
    intervention_history: tuple[str, ...]


@dataclass(frozen=True)
class BlockingReason:
    """Why a frozen Draft may not execute, and what it is about.

    `subject` names the state key, source, or event the reason concerns, so two
    reasons of the same kind are two facts rather than one repeated. A reason
    with no subject would be the `NOT_RECONCILABLE` mistake T018's review found
    one layer down: several different facts wearing one name.
    """

    kind: str
    subject: str
    statement: str


@dataclass(frozen=True)
class SimulationRun:
    """One Draft SimulationRun: frozen inputs, and whether they can execute.

    `run_id` is the only run identity. It is allocated by `runs/identity.py`,
    never supplied by a request, and never derived from the Site or the
    scenario the run is bound to.

    A run is `READY` exactly when it carries no blocking reason. The
    constructor asserts it rather than trusting a caller, because a `READY` run
    with a reason attached and a `BLOCKED` run with none are both a status
    somebody wrote instead of computed.
    """

    run_id: str
    lifecycle_status: str
    execution_status: str
    created_at: str
    deterministic_identity: DeterministicIdentity
    blocking_reasons: tuple[BlockingReason, ...]
    unsupported_optional_inputs: tuple[UnsupportedOptionalInput, ...]

    def __post_init__(self) -> None:
        expected = "BLOCKED" if self.blocking_reasons else "READY"
        if self.execution_status != expected:
            raise ValueError(
                f"A run with {len(self.blocking_reasons)} blocking reason(s) "
                f"is {expected}, not {self.execution_status!r}. The execution "
                "status is computed from the reasons; it is never set beside "
                "them."
            )

        # A frozen identity with a hole in it is not a runnable identity. The
        # only reason an initial value can be absent is that something
        # blocked the run, so a `READY` run carrying one would be a run whose
        # status and whose inputs disagree.
        unresolved = [
            item.state_key
            for item in self.deterministic_identity.initialization_inputs
            if item.value is None
        ]
        if unresolved and not self.blocking_reasons:
            raise ValueError(
                f"A run with no blocking reason has no answer for "
                f"{sorted(unresolved)}. An initial value is absent only "
                "because something blocked the run, so a READY run cannot "
                "carry one."
            )
