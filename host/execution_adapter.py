"""The composition leaf: where a frozen product Draft becomes kernel input.

`host/` is the only place that may import both sides (v4 section 3.2, rules 3
and 4). Nothing imports it, which is what lets it know about a `SimulationRun`
and about `assetops_simulator` at once without either learning about the other.

## It takes the run and nothing else, and that is the whole of R1's fix

This module used to take a `ScenarioDefinition` beside the run and project the
causes, the forcings and the bounds out of it. T021's independent review
reproduced what that allows: execute the ordinary shipped Draft, then execute the
SAME persisted run against the same document version with one offset moved from
1500 to 1515, and the tank at 1515 goes from 334.02 L to 374.02 L. Both complete.
Nothing in the run has changed.

Comparing parameter identities, which is what this did, cannot see that - and an
offset is a causally effective number exactly as a quantity is. So run setup now
freezes the whole causal projection on the run (`FrozenCause`, `FrozenForcing`,
`FrozenDeclaredBound`, `FrozenReportingPathCondition`), and `frozen_world_inputs`
takes one argument. There is no parameter through which a different experiment
can arrive, which is a stronger statement than any comparison this module could
have made.

What is left here is a mapping: frozen product records to neutral ones, with the
one-time authored-float normalization the numeric policy allows at the input
boundary and no other arithmetic. It computes no physics, applies no bound and
decides no trajectory.

**One parameter survives and it is checked rather than trusted.** A caller may
supply the `ModelSpec` to execute against, because a model is code rather than
frozen content and there is no catalog of them here. A model is part of the
experiment, so `run_to_end` refuses one whose identity is not the profile identity
the run froze: executing a run against a model it did not select would be the same
defect as executing it against a document it did not freeze, one noun along.

What the check cannot see, stated rather than implied: a model carrying the frozen
identity and different BEHAVIOUR is still injectable. That is deliberate and it is
what the conformance test and the guard probes rely on - both substitute a model at
the same identity on purpose. A product caller resolves the model from a catalog
keyed on the frozen identity, which is T022's, and this refusal is what makes that
resolution checkable rather than assumed.

## What it refuses, and why each refusal is not an execution failure

A `BLOCKED` Draft is not executed. There is no flag, no override and no partial
mode: `BLOCKED` is run setup's answer that these frozen inputs may not execute,
and a leaf that could talk a caller past it would make the status advisory. That
is a refusal here rather than an execution failure, because nothing executed.

A Draft frozen against a different execution contract is refused by
`refuse_incompatible_execution`, called before anything is built. The kernel
calls it again as its own first act, because a caller can hand a kernel inputs
this adapter never saw, and a guard that only one of two entrances has is a guard
with an entrance. It is also what makes the frozen projection safe to default to
empty on readback: a run without one is a run at an earlier version, and such a
run is never executed.

Two answers for one address are refused rather than resolved. A stored document
can carry two initialization rows for one state, and building a map from it made
the last row silently authoritative - which T021's review found and carried. A
frozen run that answers one address twice is not a run whose experiment is
determined, so it is refused here, where both rows are still visible.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.profiles import (
    PUBLICATION_DELAY_STATES,
    PUBLICATION_PROFILES,
    PublicationProfile,
    find_publication_profile,
)
from assetops_backend.state_refs import component_state
from assetops_contracts.execution_contract import (
    BOUND_CASES,
    normalize_authored_float,
    refuse_incompatible_execution,
)
from assetops_contracts.observation import (
    DeviceSignalSpec,
    FrozenReportingInputs,
    PublicationDelayWindow,
    ReportingPathWindow,
    device_resolution,
)
from assetops_contracts.operational_records import (
    FrozenRecordInputs,
    OverrideCommand,
    PolicyDeclaration,
    RecordGap,
)
from assetops_contracts.control import DISCRETE_UNIT
from assetops_contracts.trajectory import PrivateTrajectory
from assetops_contracts.world_inputs import (
    DeclaredBound,
    DeclaredCause,
    ForcingInput,
    FrozenInterval,
    FrozenWorldInputs,
    DiscreteInitialValue,
    InitialValue,
    BusAttachmentInput,
    SiteControlInput,
    UnmodelledInput,
)
from assetops_simulator.kernel.execute import ProfilePairMismatch, execute, execution_path_for
from assetops_simulator.kernel.model import ModelSpec
from assetops_simulator.packs.fuel import MINIMAL_FUEL_MODEL
from assetops_simulator.packs.mini_grid import (
    MINI_GRID_MODEL,
    MINI_GRID_V2_MODEL,
    MINI_GRID_V3_MODEL,
    MINI_GRID_V4_MODEL,
    MINI_GRID_V5_MODEL,
)
from assetops_simulator.packs.minigrid import DAYTIME_MINI_GRID_MODEL

#: Every model this build can execute, by the profile identity a run freezes.
#: Selected by identity, never by the shape of a run: the leaf is the one
#: place allowed to know both the product's profiles and the simulator's
#: models, so it is where a frozen profile identity becomes executable code.
EXECUTABLE_MODELS: tuple[ModelSpec, ...] = (
    MINIMAL_FUEL_MODEL,
    DAYTIME_MINI_GRID_MODEL,
    MINI_GRID_MODEL,
    MINI_GRID_V2_MODEL,
    MINI_GRID_V3_MODEL,
    MINI_GRID_V4_MODEL,
    MINI_GRID_V5_MODEL,
)


def execution_path(run: SimulationRun) -> str:
    """W2-02: `COLD` for the frozen `cold-thermal/1` + `cold-publication/1` pair, W2-05b: `EV` for
    `ev-charger/1` + `ev-publication/1`, `MODEL_SPEC` for every older pair. A half pair is refused, never
    resolved to any path."""
    frozen = run.deterministic_identity.profiles
    try:
        return execution_path_for(
            (frozen.model_profile_id, frozen.model_profile_version),
            (frozen.publication_profile_id, frozen.publication_profile_version),
        )
    except ProfilePairMismatch as mismatch:
        raise FrozenRunNotReconstructible(
            f"Run {run.run_id} froze model profile {frozen.model_profile_id} version "
            f"{frozen.model_profile_version} with publication profile {frozen.publication_profile_id} "
            f"version {frozen.publication_profile_version}; no execution path accepts that pair."
        ) from mismatch


def model_for(run: SimulationRun) -> ModelSpec:
    """The executable model with the identity this run froze, or a refusal.

    A cold run never resolves a ModelSpec: it executes through the cold pack (`ColdExecution`).
    """
    frozen = run.deterministic_identity.profiles
    path = execution_path(run)
    if path == "EV":
        raise FrozenRunNotReconstructible(
            f"Run {run.run_id} froze the EV pair {frozen.model_profile_id}/{frozen.model_profile_version}, which "
            "executes through the EV pack and has no model specification."
        )
    if path == "COLD":
        raise FrozenRunNotReconstructible(
            f"Run {run.run_id} froze the cold-chain pair {frozen.model_profile_id}/"
            f"{frozen.model_profile_version}, which executes through the cold pack and has no model "
            "specification."
        )
    for model in EXECUTABLE_MODELS:
        if (
            model.model_profile_id == frozen.model_profile_id
            and model.model_profile_version == frozen.model_profile_version
        ):
            return model
    raise FrozenRunNotReconstructible(
        f"Run {run.run_id} froze model profile {frozen.model_profile_id} "
        f"version {frozen.model_profile_version}, and this build has no model "
        "with that identity to execute it against."
    )


def publication_profile_for(run: SimulationRun) -> PublicationProfile:
    """The publication profile with the identity this run froze, or a refusal.

    T025b: the build carries two (versions three and four), so a run's readings
    are generated through the profile it froze rather than through whichever
    one the host was constructed with. The same rule as `model_for`.
    """
    frozen = run.deterministic_identity.profiles
    execution_path(run)  # W2-02: a half-cold pair refuses before any profile resolves.
    profile = find_publication_profile(
        PUBLICATION_PROFILES,
        frozen.publication_profile_id,
        frozen.publication_profile_version,
    )
    if profile is None:
        raise FrozenRunNotReconstructible(
            f"Run {run.run_id} froze publication profile "
            f"{frozen.publication_profile_id} version "
            f"{frozen.publication_profile_version}, and this build has no "
            "publication profile with that identity to generate its readings."
        )
    return profile

#: Which contract bound case a declared bound falls under, keyed on the state
#: whose value supplies the limit and the direction of the limit.
#:
#: Explicit rather than inferred. The two strings on this one row happen to
#: coincide, and that is a naming coincidence rather than the rule: nothing here
#: matches a bound to a case by spelling, for the same reason a bound is a
#: declaration rather than a shared prefix between two state keys. A declared
#: bound with no row is refused, so a second bound cannot arrive with a policy
#: nobody chose.
BOUND_CASE_BY_DECLARED_BOUND: dict[tuple[str, str], str] = {
    ("fuel-tank-capacity", "UPPER"): "fuel-tank-capacity",
}

_POLICY_BY_CASE = {case.case_id: case.policy for case in BOUND_CASES}


class RunNotExecutable(Exception):
    """This Draft may not be executed, and nothing was executed.

    Distinct from every execution failure: an execution failure means a run
    started and stopped, and this means it never started.
    """


class FrozenRunNotReconstructible(Exception):
    """The frozen run does not determine one experiment."""


@dataclass(frozen=True)
class HostExecution:
    """One execution, with the inputs it was built from beside its result.

    Both halves, because criterion 2 is a claim about the pair: the same frozen
    inputs must produce the same canonical trajectory, and a caller that only got
    the trajectory back could not re-execute the inputs to check.
    """

    inputs: FrozenWorldInputs
    trajectory: PrivateTrajectory


def _fraction(value: float | None, where: str) -> Fraction:
    if value is None:
        raise FrozenRunNotReconstructible(
            f"{where} has no frozen value. A READY run answers every initial "
            "value it declares, so a run reaching here without one is a run "
            "whose status and whose content disagree."
        )
    return normalize_authored_float(float(value))


def frozen_world_inputs(run: SimulationRun) -> FrozenWorldInputs:
    """Project one frozen Draft into kernel input, from the run alone."""
    if run.execution_status != "READY":
        raise RunNotExecutable(
            f"Run {run.run_id} is {run.execution_status} and carries "
            f"{len(run.blocking_reasons)} blocking reason(s): "
            + "; ".join(
                f"{reason.kind} about {reason.subject}"
                for reason in run.blocking_reasons
            )
            + ". A blocked Draft says these frozen inputs may not execute, and "
            "there is no mode in which they do."
        )

    identity = run.deterministic_identity
    refuse_incompatible_execution(identity.profiles.execution_contract_version)

    initial_values = _initial_values(run)
    # The ROLE travels with the address. `UnsupportedOptionalInput` has carried
    # both since T020A1, and dropping the role here made the exclusion suppress
    # roles the model does support.
    unmodelled = tuple(
        sorted(
            (
                UnmodelledInput(
                    address=item.addressed_key, role=item.execution_role
                )
                for item in run.unsupported_optional_inputs
            ),
            key=lambda item: (item.address, item.role),
        )
    )

    site_controls = tuple(
        SiteControlInput(control_key=item.control_key, members=item.members)
        for item in identity.site_controls
        if item.members is not None
    )

    bus_attachments = tuple(
        BusAttachmentInput(
            role=item.role,
            component_id=item.component_id,
            via_component_id=item.via_component_id,
            bus_component_id=item.bus_component_id,
        )
        for item in identity.bus_attachments
    )

    return FrozenWorldInputs(
        run_id=run.run_id,
        execution_contract_version=(
            identity.profiles.execution_contract_version
        ),
        site_id=identity.site.site_id,
        foundation_version=identity.site.foundation_version,
        scenario_id=identity.scenario.scenario_id,
        scenario_version=identity.scenario.scenario_version,
        model_profile_id=identity.profiles.model_profile_id,
        model_profile_version=identity.profiles.model_profile_version,
        publication_profile_id=identity.profiles.publication_profile_id,
        publication_profile_version=(
            identity.profiles.publication_profile_version
        ),
        interval=FrozenInterval(
            start_time=identity.interval.start_time,
            end_time=identity.interval.end_time,
            duration_minutes=identity.interval.duration_minutes,
            timestep_minutes=identity.interval.timestep_minutes,
        ),
        seed=identity.seed,
        initial_values=initial_values,
        bounds=_bounds(run, initial_values),
        forcings=_forcings(run),
        causes=_causes(run),
        unmodelled_inputs=unmodelled,
        reporting_path_addresses=tuple(
            sorted(
                {
                    condition.addressed_key
                    for condition in identity.reporting_path_conditions
                }
            )
        ),
        intervention_history=identity.intervention_history,
        site_controls=site_controls,
        bus_attachments=bus_attachments,
        discrete_initial_values=_discrete_initial_values(run),
    )


def _is_discrete(item) -> bool:
    """T025a. A typed discrete member, frozen in unit `state`."""
    return item.unit == DISCRETE_UNIT


def _discrete_initial_values(run: SimulationRun) -> tuple[DiscreteInitialValue, ...]:
    """T025a. The run-start discrete states a scenario owns, typed, never numbers.

    Empty for every run frozen before discrete state existed, which is what
    keeps those runs' identities exactly as they were.
    """
    return tuple(
        DiscreteInitialValue(
            address=item.addressed_key,
            state_key=item.state_key,
            scope=item.state_ref.scope,
            value=str(item.canonical_value),
            answered_by=item.answered_by,
        )
        for item in run.deterministic_identity.initialization_inputs
        if _is_discrete(item)
    )


def _refuse_two_answers(run: SimulationRun, kind: str, keys: list[str]) -> None:
    """Refuse a frozen run that answers one address twice.

    A map built from such a run makes the last row authoritative, silently. That
    is not a defect a kernel can notice, because by then there is one answer; it
    has to be caught where both rows are still visible. Ordinary setup cannot
    produce one - the scenario parser refuses duplicate initializers - so what
    this catches is a stored document somebody wrote or edited by hand, which is
    the same boundary every other check in `runs/parsing.py` exists for.
    """
    seen: set[str] = set()
    duplicated: set[str] = set()
    for key in keys:
        if key in seen:
            duplicated.add(key)
        seen.add(key)
    if duplicated:
        raise FrozenRunNotReconstructible(
            f"Run {run.run_id} carries more than one frozen {kind} for "
            f"{sorted(duplicated)}. One address has one answer, or the "
            "experiment being executed depends on which row was read last."
        )


def _initial_values(run: SimulationRun) -> tuple[InitialValue, ...]:
    """Every frozen number a kernel initializes from, scenario and model alike.

    T024: a model-owned Foundation need is, to a kernel, a frozen number at an
    address answered by the Foundation - so it travels as an initial value. Its
    `parameter_id` says it answers a model need, because no scenario parameter
    stands behind it and none is invented. One address still has one answer
    across both collections, refused here where both rows are visible.
    """
    frozen = run.deterministic_identity.initialization_inputs
    needs = run.deterministic_identity.model_needs
    _refuse_two_answers(
        run,
        "initial value",
        [item.addressed_key for item in frozen]
        + [item.addressed_key for item in needs],
    )
    from_needs = tuple(
        InitialValue(
            address=item.addressed_key,
            state_key=item.state_key,
            scope=item.state_ref.scope,
            parameter_id=f"model-need:{item.property_key}",
            value=_fraction(
                item.canonical_value,
                f"the model-owned need {item.addressed_key}",
            ),
            canonical_unit=item.canonical_unit,
            dimension=item.dimension,
            answered_by=item.answered_by,
        )
        for item in needs
    )
    return from_needs + tuple(
        InitialValue(
            address=item.addressed_key,
            state_key=item.state_key,
            scope=item.state_ref.scope,
            parameter_id=item.parameter_id,
            value=_fraction(
                item.canonical_value,
                f"the initial value of {item.addressed_key}",
            ),
            canonical_unit=item.canonical_unit,
            dimension=item.dimension,
            answered_by=item.answered_by,
        )
        for item in frozen
        if not _is_discrete(item)
    )


def _bounds(
    run: SimulationRun, initial_values: tuple[InitialValue, ...]
) -> tuple[DeclaredBound, ...]:
    """Each frozen bound relationship, with the number the run froze for it.

    `D-2026-09-22-capacity-bound-source`: the declaration is the document's and
    the value is the site's. Both halves are frozen now - the relationship as a
    `FrozenDeclaredBound` and the number as the initialization input it points at
    - so this pairs two frozen records rather than a frozen record and a live
    document.
    """
    by_address = {item.address: item for item in initial_values}
    bounds: list[DeclaredBound] = []
    for declaration in run.deterministic_identity.declared_bounds:
        key = (declaration.source_state_ref.state_key, declaration.bound_kind)
        case_id = BOUND_CASE_BY_DECLARED_BOUND.get(key)
        if case_id is None:
            raise FrozenRunNotReconstructible(
                f"Run {run.run_id} froze a {declaration.bound_kind} bound whose "
                f"value comes from {declaration.source_state_ref.state_key!r}, "
                "and no bound case says what a kernel does when it is reached. "
                "A bound with no policy is a silent clamp waiting to be "
                "written, so this is refused rather than defaulted."
            )
        source = by_address.get(declaration.source_addressed_key)
        if source is None:
            raise FrozenRunNotReconstructible(
                f"Run {run.run_id} froze a bound on "
                f"{declaration.addressed_key} sourced from "
                f"{declaration.source_addressed_key}, and froze no initial "
                "value for that address. A bound relationship with no number "
                "behind it is a limit nobody stated."
            )
        bounds.append(
            DeclaredBound(
                address=declaration.addressed_key,
                kind=declaration.bound_kind,
                value=source.value,
                canonical_unit=source.canonical_unit,
                source_address=declaration.source_addressed_key,
                bound_case_id=case_id,
                policy=_POLICY_BY_CASE[case_id],
            )
        )
    return tuple(bounds)


def _forcings(run: SimulationRun) -> tuple[ForcingInput, ...]:
    return tuple(
        ForcingInput(
            event_id=item.event_id,
            address=item.addressed_key,
            state_key=item.state_key,
            parameter_id=item.parameter_id,
            value=_fraction(
                item.canonical_value, f"the forcing {item.parameter_id}"
            ),
            canonical_unit=item.canonical_unit,
            dimension=item.dimension,
            shape=item.timing_shape,
            offset_minutes=item.offset_minutes,
            duration_minutes=item.duration_minutes,
            requirement=item.execution_requirement,
        )
        for item in run.deterministic_identity.forcings
    )


def _causes(run: SimulationRun) -> tuple[DeclaredCause, ...]:
    """Every frozen change to a stock, with the quantity the run froze.

    A rate declared over a window was integrated once, at the input boundary, by
    run setup. How much of the result has moved part way through is the
    contract's ramp and the kernel's to apply.
    """
    return tuple(
        DeclaredCause(
            event_id=item.event_id,
            address=item.addressed_key,
            state_key=item.state_key,
            direction=item.direction,
            parameter_id=item.parameter_id,
            quantity=_fraction(
                item.canonical_value, f"the cause {item.event_id}"
            ),
            canonical_unit=item.canonical_unit,
            dimension=item.dimension,
            shape=item.timing_shape,
            offset_minutes=item.offset_minutes,
            duration_minutes=item.duration_minutes,
        )
        for item in run.deterministic_identity.causes
    )


def refuse_a_model_the_run_did_not_select(
    run: SimulationRun, model: ModelSpec
) -> None:
    """Refuse a model whose identity is not the one the run froze.

    A run freezes WHICH model profile answered and at which version, precisely so
    that the same run is reproducible without the profile catalog being frozen with
    it. Executing it against a model of another identity would discard that, and it
    is the same defect as executing it against a document it did not freeze.

    It checks the identity and cannot check the behaviour. A model carrying the
    frozen identity and different code is still injectable, which the conformance
    test and the guard probes both do deliberately.
    """
    frozen = run.deterministic_identity.profiles
    if (
        model.model_profile_id == frozen.model_profile_id
        and model.model_profile_version == frozen.model_profile_version
    ):
        return
    raise FrozenRunNotReconstructible(
        f"Run {run.run_id} froze model profile {frozen.model_profile_id} version "
        f"{frozen.model_profile_version} and was handed "
        f"{model.model_profile_id} version {model.model_profile_version}. A run "
        "executes the model it selected; executing it against another is "
        "reinterpretation wearing the old run's identity."
    )


def frozen_resolutions(
    run: SimulationRun, profile: PublicationProfile
) -> dict[tuple[str, str], Fraction]:
    """S2-01b: each signal's simulated device resolution, as the run froze it.

    The run's frozen identity is the authority, not the catalog: a build whose
    profile of the same identity declared a different resolution, or a unit
    other than the one frozen, would publish another experiment's readings
    under this run's name, so either disagreement refuses.
    """
    frozen = {
        (item.device_id, item.signal_id): item
        for item in run.deterministic_identity.signal_resolutions
    }
    declared = {
        declaration.signal_key: declaration
        for declaration in profile.device_signals
        if declaration.resolution is not None
    }
    disagreeing = sorted(
        key
        for key in set(frozen) | set(declared)
        if key not in frozen
        or key not in declared
        or frozen[key].resolution != declared[key].resolution
        or frozen[key].unit != declared[key].canonical_unit
    )
    if disagreeing:
        raise FrozenRunNotReconstructible(
            f"Run {run.run_id} froze device resolutions that publication profile "
            f"{profile.publication_profile_id} version "
            f"{profile.publication_profile_version} in this build does not "
            f"declare identically, for {disagreeing}. A run publishes at the "
            "resolution it froze or not at all."
        )
    return {key: device_resolution(item.resolution) for key, item in frozen.items()}


def refuse_a_publication_profile_the_run_did_not_select(
    run: SimulationRun, profile: PublicationProfile
) -> None:
    """Refuse a publication profile whose identity is not the one the run froze.

    The same rule as `refuse_a_model_the_run_did_not_select`, one noun along, and
    it became load-bearing in the same slice the profile started deciding
    something. A run freezes which publication profile answered and at which
    version; generating its readings against another profile's cadences, biases
    and dropouts would produce a different experiment's series under this run's
    name, and the reading digest would then be an identity for nothing.
    """
    frozen = run.deterministic_identity.profiles
    if (
        profile.publication_profile_id == frozen.publication_profile_id
        and profile.publication_profile_version
        == frozen.publication_profile_version
    ):
        return
    raise FrozenRunNotReconstructible(
        f"Run {run.run_id} froze publication profile "
        f"{frozen.publication_profile_id} version "
        f"{frozen.publication_profile_version} and was handed "
        f"{profile.publication_profile_id} version "
        f"{profile.publication_profile_version}. A run publishes through the "
        "profile it selected; generating its readings through another is "
        "reinterpretation wearing the old run's identity."
    )


def _component_carrying(
    run: SimulationRun, device_id: str, signal_id: str
) -> str | None:
    """Which component the Foundation says one device signal describes.

    Read off the run's frozen signal mappings, which is where the Foundation's
    own declaration was frozen, and never inferred from a device's attachment or
    its name: the shipped template's own comment says a device may be attached to
    one component and describe another.

    Two mappings for one device signal are refused rather than resolved. A map
    built from such a run would make the last row authoritative silently, which
    is the defect `_refuse_two_answers` above exists for, one record along.
    """
    matches = sorted(
        {
            mapping.component_id
            for mapping in run.deterministic_identity.signal_mappings
            if mapping.device_id == device_id and mapping.signal_id == signal_id
        }
    )
    if not matches:
        return None
    if len(matches) > 1:
        raise FrozenRunNotReconstructible(
            f"Run {run.run_id} froze {len(matches)} signal mappings saying "
            f"{device_id}/{signal_id} describes {matches}. Which component a "
            "reading is about is not a question with two answers, so this is "
            "refused where both rows are still visible."
        )
    return matches[0]


def reporting_inputs(
    run: SimulationRun,
    profile: PublicationProfile | None = None,
    model: ModelSpec | None = None,
) -> FrozenReportingInputs:
    """Project one frozen Draft into the observation transform's input.

    The companion projection to `frozen_world_inputs`, and deliberately a second
    function producing a second record. The world record has no field a cadence
    could arrive in and this one has no field a stock could, so the two halves of
    criterion 8 - the reports change, the world does not - are properties of two
    signatures rather than of a caller's discipline.

    Three sources and no fourth. The publication profile declares which signals
    report which state, when, with what bias and with what dropout. The run's
    frozen signal mappings say which component each signal describes, which is
    what turns a declaration about `fuel-tank-volume` into a reporting path about
    `fuel-tank-volume@fuel-tank`. And the run's frozen reporting-path conditions
    supply the windows, which is exactly the consumer
    `FrozenReportingPathCondition` says its window was frozen for.

    **A declared signal this installation does not configure is not a reporting
    path.** It is left out rather than invented, and the left-out signals are
    returned to the caller as a note rather than dropped in silence: a profile
    naming a sensor the Site has not got is a fact a reader of the Lab should see.
    """
    # The contract version first, and the order is not cosmetic. A run frozen
    # under an earlier contract will ALSO name an earlier publication profile,
    # because the two moved together - so asking about the profile first reports
    # "this run does not determine one experiment" for a run whose real answer is
    # "these rules are not the rules it was frozen under". The coarser, prior fact
    # is the one a reader needs, and a browser run of this slice found the two the
    # wrong way round.
    identity = run.deterministic_identity
    refuse_incompatible_execution(identity.profiles.execution_contract_version)
    if profile is None:
        profile = publication_profile_for(run)
    refuse_a_publication_profile_the_run_did_not_select(run, profile)
    if model is None:
        model = model_for(run)

    interval = FrozenInterval(
        start_time=identity.interval.start_time,
        end_time=identity.interval.end_time,
        duration_minutes=identity.interval.duration_minutes,
        timestep_minutes=identity.interval.timestep_minutes,
    )

    resolutions = frozen_resolutions(run, profile)
    signals: list[DeviceSignalSpec] = []
    components: dict[tuple[str, str], str] = {}
    for declaration in profile.device_signals:
        # T024: a declared path about a state the selected model does not
        # produce is not a reporting path for this run. Without this a fuel
        # run on a hybrid Site would grow a column of empty battery readings.
        if not model.reports(
            declaration.state_key,
            declaration.reading_class,
            declaration.canonical_unit,
        ):
            continue
        component = _component_carrying(
            run, declaration.device_id, declaration.signal_id
        )
        if component is None:
            continue
        components[declaration.signal_key] = component
        signals.append(
            DeviceSignalSpec(
                device_id=declaration.device_id,
                signal_id=declaration.signal_id,
                address=component_state(
                    declaration.state_key, component
                ).addressed_key,
                state_key=declaration.state_key,
                reading_class=declaration.reading_class,
                canonical_unit=declaration.canonical_unit,
                cadence_minutes=declaration.cadence_minutes,
                bias=normalize_authored_float(declaration.bias),
                dropout_per_thousand=declaration.dropout_per_thousand,
                statement=declaration.statement,
                resolution=resolutions.get(declaration.signal_key),
            )
        )

    by_signal = {
        (signal.device_id, signal.signal_id): signal for signal in signals
    }
    gaps: list[ReportingPathWindow] = []
    delays: list[PublicationDelayWindow] = []
    for condition in identity.reporting_path_conditions:
        declared = profile.supported_reporting(condition.state_ref.state_key)
        if declared is None:
            continue
        # T026: a delay condition holds publications back; it suppresses none.
        for device_id, signal_id in declared.delays:
            signal = by_signal.get((device_id, signal_id))
            if signal is None:
                continue
            if (
                condition.state_ref.component_id is not None
                and condition.state_ref.component_id
                != components[(device_id, signal_id)]
            ):
                continue
            delays.append(
                _delay_window(condition, device_id, signal_id, signal.address, interval)
            )
        for device_id, signal_id in declared.silences:
            signal = by_signal.get((device_id, signal_id))
            if signal is None:
                continue
            # The condition names a path on a component. A condition on one tank
            # does not silence another tank's sensor, so the components have to
            # agree before the window applies.
            if (
                condition.state_ref.component_id is not None
                and condition.state_ref.component_id
                != components[(device_id, signal_id)]
            ):
                continue
            # `timing_shape` travels, and its absence was a defect rather than a
            # simplification. Without it every missing duration read as the
            # interval's end, so a POINT condition at offset 1500 silenced 1500,
            # 1515 and 2400 alike - a run-long outage where the document declared
            # an instant. `FrozenReportingPathCondition`'s own docstring says its
            # window was frozen for this consumer; dropping the shape on the way
            # here discarded part of what had been frozen.
            gaps.append(
                ReportingPathWindow(
                    event_id=condition.event_id,
                    condition_address=condition.addressed_key,
                    device_id=device_id,
                    signal_id=signal_id,
                    address=signal.address,
                    timing_shape=condition.timing_shape,
                    offset_minutes=condition.offset_minutes,
                    duration_minutes=condition.duration_minutes,
                    interval_minutes=interval.duration_minutes,
                    timestep_minutes=interval.timestep_minutes,
                )
            )

    return FrozenReportingInputs(
        run_id=run.run_id,
        publication_profile_id=profile.publication_profile_id,
        publication_profile_version=profile.publication_profile_version,
        seed=identity.seed,
        interval=interval,
        signals=tuple(signals),
        gaps=tuple(gaps),
        delays=tuple(delays),
    )


def unconfigured_signals(
    run: SimulationRun,
    profile: PublicationProfile | None = None,
    model: ModelSpec | None = None,
) -> tuple[str, ...]:
    """Which declared reporting paths this installation does not configure.

    Returned so the Lab can say so. A profile declaring a sensor the Site has not
    got is not an error - a profile is versioned simulator configuration and is
    the same for every Site - but it IS a reason a reading a reader expected is
    not there, and that reason has to be visible somewhere.
    """
    if model is None:
        model = model_for(run)
    if profile is None:
        profile = publication_profile_for(run)
    return tuple(
        f"{declaration.device_id}/{declaration.signal_id}"
        for declaration in profile.device_signals
        if (
            model.reports(
                declaration.state_key,
                declaration.reading_class,
                declaration.canonical_unit,
            )
        )
        and _component_carrying(
            run, declaration.device_id, declaration.signal_id
        )
        is None
    )


def run_to_end(
    run: SimulationRun, model: ModelSpec = MINIMAL_FUEL_MODEL
) -> HostExecution:
    """Execute a Draft to the end of its interval and return both halves."""
    refuse_a_model_the_run_did_not_select(run, model)
    inputs = frozen_world_inputs(run)
    return HostExecution(inputs=inputs, trajectory=execute(inputs, model))


# --- T026: delays and records ---------------------------------------------------


def _resolved_span(condition, address: str, device_id: str, signal_id: str,
                   interval: FrozenInterval) -> tuple[int, int]:
    """A frozen condition's half-open span, by `ReportingPathWindow`'s own rule."""
    window = ReportingPathWindow(
        event_id=condition.event_id,
        condition_address=condition.addressed_key,
        device_id=device_id,
        signal_id=signal_id,
        address=address,
        timing_shape=condition.timing_shape,
        offset_minutes=condition.offset_minutes,
        duration_minutes=condition.duration_minutes,
        interval_minutes=interval.duration_minutes,
        timestep_minutes=interval.timestep_minutes,
    )
    return window.start_offset_minutes, window.end_offset_minutes


def _delay_window(condition, device_id: str, signal_id: str, address: str,
                  interval: FrozenInterval) -> PublicationDelayWindow:
    start, end = _resolved_span(condition, address, device_id, signal_id, interval)
    return PublicationDelayWindow(
        event_id=condition.event_id,
        device_id=device_id,
        signal_id=signal_id,
        start_offset_minutes=start,
        end_offset_minutes=end,
    )


#: Which Foundation answer is published as which policy record: the frozen
#: model need's state key, to the device and channel the gateway mapping
#: declares for it.
POLICY_CHANNEL_OF_NEED = {
    "generator-start-soc-threshold": (
        "generator-controller",
        "policy-start-soc-threshold",
    ),
    "generator-stop-soc-threshold": (
        "generator-controller",
        "policy-stop-soc-threshold",
    ),
    "generator-minimum-runtime": ("generator-controller", "policy-minimum-runtime"),
    "battery-reserve-state-of-charge": ("battery-pcs-controller", "policy-reserve-soc"),
}

#: Which Site Control is published on which site-controller channel.
POLICY_CHANNEL_OF_SITE_CONTROL = {
    "source-priority": ("site-controller", "policy-source-priority"),
    "critical-load-priority": ("site-controller", "policy-critical-load-priority"),
}

#: The CONTROL states whose forcing may be an operator command, and the device
#: whose override channel records it. A forcing is published as one only when
#: its scenario entry declares `issued_by: OPERATOR`
#: (`D-2026-10-02-scenario-states-override-issuer`). The backend's
#: `OVERRIDE_COMMAND_STATES` names the same keys; a test asserts the two agree.
OVERRIDE_CHANNEL_OF_STATE = {
    "generator-stop-soc-threshold": ("generator-controller", "override-command"),
    "battery-reserve-state-of-charge": ("battery-pcs-controller", "override-command"),
}


def _instant(text: str) -> str:
    moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_inputs(
    run: SimulationRun, profile: PublicationProfile | None = None
) -> FrozenRecordInputs:
    """Project one frozen Draft into the record transform's input (T026).

    Only for a profile that declares record channels; any other answers with no
    records, so every Draft frozen before T026 publishes exactly what it did.
    Policy records carry the Foundation answers the run froze; override
    commands are the run's frozen CONTROL override windows. A channel the
    profile does not declare publishes nothing.
    """
    if profile is None:
        profile = publication_profile_for(run)
    identity = run.deterministic_identity
    interval = FrozenInterval(
        start_time=identity.interval.start_time,
        end_time=identity.interval.end_time,
        duration_minutes=identity.interval.duration_minutes,
        timestep_minutes=identity.interval.timestep_minutes,
    )
    channels = set(profile.record_channels)
    if not channels:
        return FrozenRecordInputs(run_id=run.run_id, interval=interval)

    policies: list[PolicyDeclaration] = []
    for need in identity.model_needs:
        channel = POLICY_CHANNEL_OF_NEED.get(need.state_ref.state_key)
        if channel is None or channel not in channels or need.canonical_value is None:
            continue
        policies.append(
            PolicyDeclaration(
                device_id=channel[0],
                signal_id=channel[1],
                control=need.state_ref.state_key,
                component_id=need.state_ref.component_id,
                value=normalize_authored_float(need.canonical_value),
                members=None,
                unit=need.canonical_unit,
                policy_version=need.foundation_version,
                policy_source="FOUNDATION",
                effective_start=_instant(need.foundation_valid_from),
            )
        )
    for control in identity.site_controls:
        channel = POLICY_CHANNEL_OF_SITE_CONTROL.get(control.control_key)
        if channel is None or channel not in channels or not control.members:
            continue
        policies.append(
            PolicyDeclaration(
                device_id=channel[0],
                signal_id=channel[1],
                control=control.control_key,
                component_id=None,
                value=None,
                members=tuple(control.members),
                unit="order",
                policy_version=control.foundation_version,
                policy_source="FOUNDATION",
                effective_start=_instant(control.foundation_valid_from),
            )
        )

    overrides: list[OverrideCommand] = []
    for forcing in identity.forcings:
        if forcing.issued_by != "OPERATOR":
            continue
        channel = OVERRIDE_CHANNEL_OF_STATE.get(forcing.state_ref.state_key)
        if channel is None or channel not in channels:
            continue
        start, end = _resolved_span(
            forcing, forcing.addressed_key, channel[0], channel[1], interval
        )
        overrides.append(
            OverrideCommand(
                event_id=forcing.event_id,
                device_id=channel[0],
                signal_id=channel[1],
                control=forcing.state_ref.state_key,
                component_id=forcing.state_ref.component_id,
                value=_fraction(
                    forcing.canonical_value, f"the override {forcing.parameter_id}"
                ),
                unit=forcing.canonical_unit,
                occurrence_offset_minutes=start,
                effective_start_offset_minutes=start,
                effective_end_offset_minutes=end,
            )
        )

    gaps: list[RecordGap] = []
    delays: list[PublicationDelayWindow] = []
    for condition in identity.reporting_path_conditions:
        declared = profile.supported_reporting(condition.state_ref.state_key)
        if declared is None:
            continue
        for device_id, signal_id in declared.silences + declared.delays:
            if (device_id, signal_id) not in channels:
                continue
            # A condition on one component's path does not reach another's:
            # the generator's override channel is not the battery's.
            component = condition.state_ref.component_id
            if component is not None and not any(
                (command.device_id, command.signal_id) == (device_id, signal_id)
                and command.component_id == component
                for command in overrides
            ):
                continue
            start, end = _resolved_span(
                condition, condition.addressed_key, device_id, signal_id, interval
            )
            if condition.state_ref.state_key in PUBLICATION_DELAY_STATES:
                delays.append(
                    PublicationDelayWindow(
                        event_id=condition.event_id,
                        device_id=device_id,
                        signal_id=signal_id,
                        start_offset_minutes=start,
                        end_offset_minutes=end,
                    )
                )
            else:
                gaps.append(
                    RecordGap(
                        event_id=condition.event_id,
                        device_id=device_id,
                        signal_id=signal_id,
                        start_offset_minutes=start,
                        end_offset_minutes=end,
                    )
                )
    return FrozenRecordInputs(
        run_id=run.run_id,
        interval=interval,
        policies=tuple(policies),
        overrides=tuple(overrides),
        gaps=tuple(gaps),
        delays=tuple(delays),
    )
