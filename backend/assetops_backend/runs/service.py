"""Run setup: freeze the inputs, decide whether they can execute, persist.

One service, and it does three things in that order, because the order is the
acceptance criterion.

**Freeze, or refuse.** Everything a run needs is resolved from the selected
Site and Foundation version, the selected scenario version, the run's own
inputs, and the selected versioned profiles. Anything that cannot be resolved
refuses the setup and allocates no `run_id`: the run does not come into
existence, so there is nothing to inspect afterwards and nothing in the store.

**Decide, never default.** With a complete frozen identity in hand, the
selected model profile is asked whether it can execute each required
executable input, and the publication profile is asked for the cadence and the
two publication identities. Every answer of "no" becomes a blocking reason on
the run. Nothing is filled in on the profile's behalf, which is the whole of
"no fabricated defaults make it `READY`": there is no code path here that
supplies a value a profile did not.

**Persist, then return.** The Draft is written through the port before the
summary is returned, so a `BLOCKED` run is inspectable rather than a message
that scrolled past.

## The refusal line, in this module

`runs/refusals.py` states it, and the T019 user review sharpened it to a
question about WHO failed to answer:

- the scenario's **declared owner** has no answer, so nothing can be frozen
  and no profile would help - **refuse**;
- the **selected profile** cannot answer, so a different profile would -
  **persist a `BLOCKED` Draft** with the reason to inspect and the frozen
  inputs to reason about.

That moved a case. A Foundation-owned initial value the selected profile
cannot locate used to be a refusal, and the person's fix for it - choose a
different model profile - is the fix for every blocking reason there is, so
refusing handed them nothing to inspect and no way to tell which profile to
try. `_resolve_foundation_value` below now returns a reason instead of
raising for those, and `_freeze` carries them out.

It is no longer true that the whole of `_freeze` raises. What is true, and
what the split rests on, is that a refusal means nothing could be frozen at
all, while a blocked run is frozen in full - including a value marked as
having no answer, which the record can now represent.

## What is deliberately not here

No clock beyond the one that stamps when the Draft was created, no step, no
event cursor, no state, no trace, no staging, no commit, and no evidence. No
reconciliation either, and that absence is the point of the next section.

## Why run setup does not judge a scenario's own arithmetic

An earlier version of this slice blocked a run when the causes a scenario
declares did not reach a reading the same scenario declares. Amendment 1's
proposal (e) removed it, and the reasoning is worth keeping where a future
slice will look for it: **run setup has no kernel, so it cannot decide that
question.** Whether declared causes reach a reading is a statement about what
a run would produce, and nothing here produces anything. What looked like
caution was run setup adjudicating a comparison only an execution can settle.

The shipped Fuel Loss Event is still `BLOCKED`, on the three states the first
model profile does not model, so nothing a user sees changes - the outcome is
now reached for a strictly sounder reason. `D-2026-09-21-scenario-execution-contract`
still accepts the residual as stated rather than resolved; what changed is
that stating it is the scenario contract's job and not this service's.

`reconcile_reported_observations` still exists and still answers that question
for the scenario detail surface. It is labelled as a specification reference
implementation rather than a product feature - see
`D-2026-09-21-specification-reference-implementation` - and nothing in this
module calls it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable, Sequence

from assetops_backend.runs.identity import allocate_run_id
from assetops_backend.runs.models import (
    ANSWERER_BY_INITIALIZATION_OWNER,
    BlockingReason,
    DeterministicIdentity,
    FrozenInitializationInput,
    FrozenInterval,
    FrozenParameter,
    FrozenProfileBinding,
    FrozenScenarioBinding,
    FrozenSignalMapping,
    FrozenSiteBinding,
    SimulationRun,
    UnsupportedOptionalInput,
)
from assetops_backend.runs.parsing import (
    RunSetupRequest,
    parse_run_setup_request,
    reject_unusable_quantity,
)
from assetops_backend.runs.ports import SimulationRunRepository
from assetops_backend.runs.profiles import (
    ModelProfile,
    PublicationProfile,
    find_model_profile,
    find_publication_profile,
    resolve_observation_binding,
    resolve_publication_identity,
)
from assetops_backend.runs.refusals import refuse
from assetops_backend.runs.timezones import (
    TimeZoneDatabaseUnavailable,
    TimeZoneNotFound,
    validate_iana_timezone,
)
from assetops_backend.scenarios.execution import (
    EXECUTION_CONTRACT_VERSION,
    canonical_quantity,
    initialization_inputs,
)
from assetops_backend.scenarios.models import (
    EXECUTABLE_ROLES,
    ScenarioDefinition,
    ScenarioParameter,
)
from assetops_backend.scenarios.ports import (
    ScenarioDefinitionRepository,
    ScenarioNotFound,
)
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import SiteNotFound, SiteRepository


@dataclass(frozen=True)
class ExecutableInput:
    """One state a scenario needs executed, in one role, at one requirement.

    Gathered from both places an executable role can be declared - a timeline
    entry and a parameter - because a rule applied at one of the two is a rule
    with the other left over, which is the shape of the hole T018's review
    found in the cadence prohibition.
    """

    state_key: str
    execution_role: str
    execution_requirement: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RunSetupService:
    """Create one Draft SimulationRun from a setup request.

    Every dependency arrives by injection: the two stores it reads, the store
    it writes, the profile catalogs, and the clock that stamps creation. A
    test supplies fakes for all five, so nothing here depends on a
    configuration root, and the profile catalogs are arguments rather than
    imports so a test can prove what happens when a profile resolves nothing
    without shipping a profile that resolves nothing.
    """

    def __init__(
        self,
        runs: SimulationRunRepository,
        sites: SiteRepository,
        scenarios: ScenarioDefinitionRepository,
        *,
        model_profiles: tuple[ModelProfile, ...],
        publication_profiles: tuple[PublicationProfile, ...],
        now: Callable[[], str] = _utc_now,
    ) -> None:
        self._runs = runs
        self._sites = sites
        self._scenarios = scenarios
        self._model_profiles = model_profiles
        self._publication_profiles = publication_profiles
        self._now = now

    # --- The one entry point ------------------------------------------------

    def create_draft_run(self, body: object) -> SimulationRun:
        """Freeze, decide, persist, and return the Draft.

        Raises:
            RunSetupRefused: the request could not be frozen. No `run_id` was
                allocated and nothing was written.
            SiteStoreUnavailable, ScenarioStoreUnavailable, RunStoreUnavailable:
                a store could not be reached. Nothing was written.
        """
        request = parse_run_setup_request(body)

        site = self._resolve_site(request)
        scenario = self._resolve_scenario(request)
        model = self._resolve_model_profile(request)
        publication = self._resolve_publication_profile(request)

        self._refuse_unsupported_target(request, scenario, site)
        self._refuse_entries_outside_the_interval(request, scenario)
        self._refuse_unresolved_sources(scenario, site)

        parameters = _parameters_by_id(scenario)
        supplied = self._resolve_run_inputs(request, parameters)

        identity, frozen_reasons = self._freeze(
            request=request,
            site=site,
            scenario=scenario,
            model=model,
            publication=publication,
            parameters=parameters,
            supplied=supplied,
        )

        reasons, optional = self._decide(
            scenario=scenario,
            model=model,
            identity=identity,
            frozen_reasons=frozen_reasons,
        )

        record = SimulationRun(
            run_id=allocate_run_id(),
            lifecycle_status="DRAFT",
            execution_status="BLOCKED" if reasons else "READY",
            created_at=self._now(),
            deterministic_identity=identity,
            blocking_reasons=reasons,
            unsupported_optional_inputs=optional,
        )

        return self._runs.create_run(record)

    # --- Resolving what the request names -----------------------------------

    def _resolve_site(self, request: RunSetupRequest) -> SiteRecord:
        try:
            site = self._sites.get_site(request.site_id)
        except SiteNotFound as error:
            raise refuse(
                "VERSION_UNAVAILABLE",
                f"No site with site ID {request.site_id!r} is configured, so "
                "there is nothing for a run to be bound to. Site IDs are "
                "compared without regard to case.",
            ) from error

        if site.foundation.version != request.foundation_version:
            raise refuse(
                "VERSION_UNAVAILABLE",
                f"Site {site.site_id} is configured at foundation version "
                f"{site.foundation.version}, and this request names version "
                f"{request.foundation_version}. A run freezes the exact "
                "foundation version it was set up against, so it is named "
                "rather than resolved to whatever is current.",
            )

        try:
            validate_iana_timezone(
                site.timezone, where=f"The time zone of site {site.site_id}"
            )
        except TimeZoneNotFound as error:
            raise refuse("TIMEZONE_NOT_IANA", str(error)) from error
        except TimeZoneDatabaseUnavailable as error:
            raise refuse(
                "TIMEZONE_DATABASE_UNAVAILABLE",
                f"{error} No run was created, and this is a statement about "
                "the database rather than about the site.",
            ) from error

        return site

    def _resolve_scenario(self, request: RunSetupRequest) -> ScenarioDefinition:
        try:
            scenario = self._scenarios.get_scenario(request.scenario_id)
        except ScenarioNotFound as error:
            raise refuse(
                "VERSION_UNAVAILABLE",
                f"No scenario with scenario ID {request.scenario_id!r} is "
                "saved, so there is nothing for a run to execute.",
            ) from error

        if scenario.version.scenario_version != request.scenario_version:
            raise refuse(
                "VERSION_UNAVAILABLE",
                f"Scenario {scenario.scenario_id} is saved at version "
                f"{scenario.version.scenario_version}, and this request names "
                f"version {request.scenario_version}. A run freezes the "
                "concrete version it used rather than following the latest.",
            )

        return scenario

    def _resolve_model_profile(self, request: RunSetupRequest) -> ModelProfile:
        profile = find_model_profile(
            self._model_profiles,
            request.model_profile_id,
            request.model_profile_version,
        )
        if profile is None:
            raise refuse(
                "VERSION_UNAVAILABLE",
                f"No model profile {request.model_profile_id!r} at version "
                f"{request.model_profile_version} exists in this build.",
            )
        return profile

    def _resolve_publication_profile(
        self, request: RunSetupRequest
    ) -> PublicationProfile:
        profile = find_publication_profile(
            self._publication_profiles,
            request.publication_profile_id,
            request.publication_profile_version,
        )
        if profile is None:
            raise refuse(
                "VERSION_UNAVAILABLE",
                f"No publication profile "
                f"{request.publication_profile_id!r} at version "
                f"{request.publication_profile_version} exists in this build.",
            )
        return profile

    # --- Refusals: what cannot be frozen ------------------------------------

    def _refuse_unsupported_target(
        self,
        request: RunSetupRequest,
        scenario: ScenarioDefinition,
        site: SiteRecord,
    ) -> None:
        """The selected Site must be one this scenario can run against.

        A declared target must be the Site the run selects. A template-derived
        scenario names no Site at all, and run setup does not choose one for
        it: picking a site because it happens to have been built from the same
        archetype would be run setup deciding what a scenario targets.

        The Foundation must also declare a topology. A scenario's causes act
        on components in a topology, and a Foundation that declares none is a
        Foundation with nowhere for them to act.
        """
        target = scenario.target_site

        if target.policy != "DECLARED_SITE" or target.site_id is None:
            raise refuse(
                "TARGET_TOPOLOGY_UNSUPPORTED",
                f"Scenario {scenario.scenario_id} names the kind of site it "
                "needs rather than a configured site, so this build cannot "
                "set a run up for it. A run is bound to a concrete site, and "
                "choosing which one is not run setup's to decide.",
            )

        if target.site_id.casefold() != request.site_id.casefold():
            raise refuse(
                "TARGET_TOPOLOGY_UNSUPPORTED",
                f"Scenario {scenario.scenario_id} declares that it targets "
                f"site {target.site_id}, and this request selects "
                f"{request.site_id}. A run is not the place to retarget a "
                "scenario.",
            )

        topology = site.foundation.topology
        if topology is None or not topology.nodes:
            raise refuse(
                "TARGET_TOPOLOGY_UNSUPPORTED",
                f"The foundation of site {site.site_id} declares no topology, "
                "so there is nowhere for this scenario's causes to act. The "
                "topology is what places a component in the site.",
            )

    def _refuse_entries_outside_the_interval(
        self, request: RunSetupRequest, scenario: ScenarioDefinition
    ) -> None:
        """Every authored entry must fall inside the interval the run chose.

        `DISPATCH_RULES` already commits the product to this and to naming the
        entry: an entry outside the interval is a mismatch between the
        scenario and the run, and leaving it out quietly would execute a
        scenario the run only partly ran.

        The comparison is half-open, so an entry at the end instant is
        outside: that instant belongs to the next interval, not this one.
        """
        length = request.duration_minutes

        for entry in scenario.timeline:
            if entry.timing.shape == "INTERVAL_WIDE":
                continue

            if entry.offset_minutes >= length:
                raise refuse(
                    "INTERVAL_INVALID",
                    f"Entry {entry.event_id} is placed at "
                    f"{entry.offset_minutes} minutes and the interval covers "
                    f"{length}. The interval is half-open, so an entry at the "
                    "end instant is outside it. Choose an interval that "
                    "covers the whole scenario.",
                )

            if entry.timing.shape == "WINDOW":
                window_end = entry.offset_minutes + (
                    entry.timing.duration_minutes or 0
                )
                if window_end > length:
                    raise refuse(
                        "INTERVAL_INVALID",
                        f"Entry {entry.event_id} runs until {window_end} "
                        f"minutes and the interval covers {length}. Choose an "
                        "interval that covers the whole scenario.",
                    )

    def _refuse_unresolved_sources(
        self, scenario: ScenarioDefinition, site: SiteRecord
    ) -> None:
        """Every device-signal source must be configured on this Site.

        A scenario whose declared device is not configured is still a readable
        scenario - that is the detail screen's business and T017 settled it -
        but it is not a runnable one: a reading has to arrive through a signal
        that exists.

        An operator record names no device and resolves against nothing, which
        is why it is skipped here rather than special-cased later.
        """
        devices = site.foundation.devices or ()

        for source in scenario.observation_sources:
            if source.source_kind != "DEVICE_SIGNAL":
                continue

            for device in devices:
                if device.device_id != source.device_id:
                    continue
                if any(
                    signal.signal_id == source.signal_id
                    for signal in device.signals
                ):
                    break
            else:
                raise refuse(
                    "COMPONENT_OR_SIGNAL_UNRESOLVED",
                    f"Source {source.source_id} reports through device "
                    f"{source.device_id} signal {source.signal_id}, and the "
                    f"foundation of site {site.site_id} configures no such "
                    "device and signal. A run cannot be bound to a signal "
                    "this site does not have.",
                )

    def _resolve_run_inputs(
        self,
        request: RunSetupRequest,
        parameters: dict[str, ScenarioParameter],
    ) -> dict[str, float]:
        """The values the run supplies, checked against what the scenario owns.

        Two rules, and they are the same rule from each side. A run may supply
        only a value the scenario says the run owns, because supplying one the
        scenario owns would be a second answer to a settled question. And it
        must supply every value the scenario says the run owns, because
        `RUN_OVERRIDE` means the run must supply it - defaulting to the
        scenario's number would make the declared owner a suggestion.
        """
        supplied: dict[str, float] = {}

        for value in request.run_inputs:
            parameter = parameters.get(value.parameter_id)
            if parameter is None:
                raise refuse(
                    "REQUEST_INVALID",
                    f"Parameter {value.parameter_id!r} is not declared by "
                    "this scenario version, so there is nothing for this run "
                    "input to supply.",
                )

            ownership = parameter.ownership
            if ownership is None or ownership.owner != "RUN_OVERRIDE":
                owner = "nobody" if ownership is None else ownership.owner
                raise refuse(
                    "REQUEST_INVALID",
                    f"Parameter {value.parameter_id!r} is owned by {owner}, "
                    "not by the run, so a run may not supply a value for it. "
                    "Only a value the scenario declares the run owns may be "
                    "supplied here.",
                )

            if parameter.unit != value.unit:
                raise refuse(
                    "UNIT_INVALID",
                    f"Parameter {value.parameter_id!r} is declared in "
                    f"{parameter.unit!r} and this run input is in "
                    f"{value.unit!r}. A run supplies the value, never a "
                    "different unit for it.",
                )

            reject_unusable_quantity(
                value.value,
                value.unit,
                where=f"Run input {value.parameter_id!r}",
            )
            supplied[value.parameter_id] = value.value

        for parameter_id, parameter in parameters.items():
            ownership = parameter.ownership
            if ownership is None or ownership.owner != "RUN_OVERRIDE":
                continue
            if parameter_id not in supplied:
                raise refuse(
                    "INITIALIZATION_INPUT_MISSING",
                    f"Parameter {parameter_id!r} is declared as owned by the "
                    "run, and this request supplies no value for it. Nothing "
                    "defaults it: a value the run owns and did not supply "
                    "would be a number nobody answers for.",
                )

        return supplied

    # --- Freezing -----------------------------------------------------------

    def _freeze(
        self,
        *,
        request: RunSetupRequest,
        site: SiteRecord,
        scenario: ScenarioDefinition,
        model: ModelProfile,
        publication: PublicationProfile,
        parameters: dict[str, ScenarioParameter],
        supplied: dict[str, float],
    ) -> tuple[DeterministicIdentity, tuple[BlockingReason, ...]]:
        """Freeze everything, and say which values had no answer.

        The reasons come back rather than being raised, because a value the
        selected profile cannot supply blocks the run instead of refusing it,
        and a blocked run is frozen in full.
        """
        initialization, unresolved = self._freeze_initialization(
            scenario=scenario, site=site, model=model, supplied=supplied
        )

        resolved = tuple(
            FrozenParameter(
                parameter_id=parameter_id,
                value=supplied.get(parameter_id, parameter.value),
                unit=parameter.unit,
                answered_by=(
                    "RUN_INPUT" if parameter_id in supplied else "SCENARIO"
                ),
            )
            for parameter_id, parameter in parameters.items()
        )

        return DeterministicIdentity(
            site=FrozenSiteBinding(
                site_id=site.site_id,
                foundation_version=site.foundation.version,
                foundation_valid_from=site.foundation.valid_from,
                site_type=site.site_type,
                timezone=site.timezone,
            ),
            scenario=FrozenScenarioBinding(
                scenario_id=scenario.scenario_id,
                scenario_version=scenario.version.scenario_version,
                resolved_parameters=resolved,
            ),
            interval=FrozenInterval(
                start_time=request.start_time,
                end_time=request.end_time,
                duration_minutes=request.duration_minutes,
                timestep_minutes=request.timestep_minutes,
            ),
            seed=request.seed,
            profiles=FrozenProfileBinding(
                model_profile_id=model.model_profile_id,
                model_profile_version=model.model_profile_version,
                publication_profile_id=publication.publication_profile_id,
                publication_profile_version=(
                    publication.publication_profile_version
                ),
                execution_contract_version=EXECUTION_CONTRACT_VERSION,
            ),
            initialization_inputs=initialization,
            observation_bindings=tuple(
                resolve_observation_binding(source, publication)
                for source in scenario.observation_sources
            ),
            publication=resolve_publication_identity(publication),
            signal_mappings=tuple(
                FrozenSignalMapping(
                    mapping_id=mapping.mapping_id,
                    device_id=mapping.device_id,
                    signal_id=mapping.signal_id,
                    component_id=mapping.component_id,
                )
                for mapping in (site.foundation.signal_mappings or ())
            ),
            # Ordered and empty. Nothing in this build can inject a runtime
            # event, and `D-2026-09-20-run-scoped-event-injection` puts one
            # here rather than in the scenario when something can.
            intervention_history=(),
        ), unresolved

    def _freeze_initialization(
        self,
        *,
        scenario: ScenarioDefinition,
        site: SiteRecord,
        model: ModelProfile,
        supplied: dict[str, float],
    ) -> tuple[
        tuple[FrozenInitializationInput, ...], tuple[BlockingReason, ...]
    ]:
        """Every initial world value, resolved from the owner that owns it.

        The four owners are the four T018 settled, and each resolves from
        exactly one place. Two of them can fail, and they fail differently,
        which is the whole of the refusal line applied here:

        - the scenario says the RUN owns a value and the request did not
          supply one: the declared owner has no answer and no profile helps,
          so `_resolve_run_inputs` refuses before this runs;
        - the scenario says the FOUNDATION or a MODEL RULE owns a value and
          the selected profile cannot locate or supply it: a different
          profile may, so the value is frozen as absent and the run carries a
          reason.

        `D-2026-09-21-causal-runtime-before-golden-traces` requires an initial
        condition to be explicit and attributable. An absent value with a
        named reason is both; a value quietly taken from another owner would
        be neither.
        """
        frozen: list[FrozenInitializationInput] = []
        reasons: list[BlockingReason] = []

        for initial in initialization_inputs(scenario):
            # The scenario parser refuses an owner outside the vocabulary, so
            # this lookup is total: a fifth owner fails the mapping test in
            # `test_run_setup.py` before it could ever reach here.
            owner = initial.owner
            answered_by = ANSWERER_BY_INITIALIZATION_OWNER[owner]
            value: float | None
            reason: BlockingReason | None = None

            if owner == "SCENARIO_INPUT":
                value = initial.value
                detail = (
                    f"scenario {scenario.scenario_id} version "
                    f"{scenario.version.scenario_version}"
                )
            elif owner == "RUN_OVERRIDE":
                value = supplied[initial.parameter_id]
                detail = "supplied by this run setup request"
            elif owner == "SITE_FOUNDATION":
                value, reason, answered_by, detail = (
                    self._resolve_foundation_value(
                        initial_state_key=initial.state_key,
                        parameter_id=initial.parameter_id,
                        declared=initial.value,
                        unit=initial.unit,
                        site=site,
                        model=model,
                    )
                )
            else:
                # A versioned model rule owns it, and no profile in this build
                # carries one: `SupportedState` has no field a model-supplied
                # initial value could live in. That carrier is T020A's to add,
                # and until it exists this is the profile failing to answer -
                # the same fact as a missing binding, so the same reason.
                value = None
                detail = (
                    f"model profile {model.model_profile_id} version "
                    f"{model.model_profile_version}, which declares no rule "
                    "for it"
                )
                reason = BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=initial.state_key,
                    statement=(
                        f"The initial value of {initial.state_key} is "
                        "declared as owned by a versioned model rule, and "
                        f"model profile {model.model_profile_id} version "
                        f"{model.model_profile_version} declares no rule for "
                        "it. Nothing else may answer for it, so a profile "
                        "that does is what this run needs."
                    ),
                )

            if reason is not None:
                reasons.append(reason)

            canonical_value = (
                None
                if value is None
                else canonical_quantity(value, initial.unit)[0]
            )
            _, canonical_unit, dimension = canonical_quantity(0.0, initial.unit)

            frozen.append(
                FrozenInitializationInput(
                    state_key=initial.state_key,
                    parameter_id=initial.parameter_id,
                    value=value,
                    unit=initial.unit,
                    canonical_value=canonical_value,
                    canonical_unit=canonical_unit,
                    dimension=dimension,
                    answered_by=answered_by,
                    answered_by_detail=detail,
                )
            )

        return tuple(frozen), tuple(reasons)

    def _resolve_foundation_value(
        self,
        *,
        initial_state_key: str,
        parameter_id: str,
        declared: float,
        unit: str,
        site: SiteRecord,
        model: ModelProfile,
    ) -> tuple[float | None, BlockingReason | None, str, str]:
        """The Foundation's answer for one initial world value, or a reason.

        Which declared fact answers is a binding the model profile carries,
        never a match by spelling: `fuel-tank-capacity` and a component called
        `fuel-tank` look related and nothing about their names says one is the
        other, which is the same reason T018's review made a bound a
        declaration rather than a shared prefix.

        ## Four of the five failures here block, and one refuses

        The T019 user review settled the discriminator: **would a different
        model profile fix this?** The Foundation's answer is only locatable
        THROUGH the profile's binding, so a failure to locate it is a joint
        fact about the pair - and the profile is the half a person can change
        on the setup form.

        Blocks, because a different profile may answer:

        - the profile declares no binding, so nothing was even asked of the
          Foundation;
        - the binding matches nothing this Foundation declares. A binding on
          another component type or another rating unit might match something
          it does declare;
        - the binding matches more than one thing, which is two answers to one
          value. A more specific binding is a profile's to carry;
        - the binding's unit is not the unit the scenario declares. That is a
          disagreement between the profile and the scenario about what kind of
          quantity this is, and the profile is the changeable half. It was a
          `UNIT_INVALID` refusal until this round, and leaving it there while
          the two cases either side of it moved would have been the same rule
          applied at one position - the failure shape this project keeps
          paying for.

        Refuses, because no profile can fix it:

        - the Foundation's value disagrees with the value the scenario states
          the Foundation declares. Both declared owners answered and they
          contradict each other. A profile pointing at some other component
          that happened to match the scenario's number would be resolving a
          contradiction by shopping for a value, so nothing is frozen and the
          refusal names both numbers.
        """
        foundation_detail = (
            f"site {site.site_id} foundation version "
            f"{site.foundation.version}"
        )
        profile_detail = (
            f"model profile {model.model_profile_id} version "
            f"{model.model_profile_version}"
        )

        supported = model.supported(initial_state_key)
        binding = None if supported is None else supported.foundation_binding

        if binding is None:
            return (
                None,
                BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=initial_state_key,
                    statement=(
                        f"The initial value of {initial_state_key} is "
                        "declared as owned by the site's foundation, and "
                        f"{profile_detail} declares no binding saying which "
                        "declared fact answers for it. Nothing here matches a "
                        "state to a component by the look of its name, so a "
                        "profile that declares the binding is what this run "
                        "needs."
                    ),
                ),
                "MODEL_PROFILE",
                f"{profile_detail}, which declares no binding for it",
            )

        matches = [
            component
            for component in site.foundation.components
            if component.component_type == binding.component_type
            and component.rating is not None
            and component.rating.unit == binding.rating_unit
        ]

        if not matches:
            return (
                None,
                BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=initial_state_key,
                    statement=(
                        f"{profile_detail} looks for the initial value of "
                        f"{initial_state_key} in a {binding.component_type} "
                        f"component rated in {binding.rating_unit}, and the "
                        f"foundation of site {site.site_id} declares none. A "
                        "profile whose binding names something this site "
                        "declares would resolve it."
                    ),
                ),
                "SITE_FOUNDATION",
                f"{foundation_detail}, which declares nothing the binding fits",
            )

        if len(matches) > 1:
            named = ", ".join(sorted(item.component_id for item in matches))
            return (
                None,
                BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=initial_state_key,
                    statement=(
                        f"{profile_detail} looks for the initial value of "
                        f"{initial_state_key} in a {binding.component_type} "
                        f"component rated in {binding.rating_unit}, and the "
                        f"foundation of site {site.site_id} declares more "
                        f"than one: {named}. Two answers to one initial value "
                        "is not something a run may choose between, so this "
                        "needs a profile whose binding tells them apart."
                    ),
                ),
                "SITE_FOUNDATION",
                f"{foundation_detail}, which declares more than one match",
            )

        rating = matches[0].rating
        assert rating is not None  # filtered above

        if rating.unit != unit:
            return (
                None,
                BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=initial_state_key,
                    statement=(
                        f"The scenario declares {initial_state_key} in "
                        f"{unit} and {profile_detail} binds it to a rating in "
                        f"{rating.unit}. A run freezes the foundation's "
                        "value, so the two must be the same quantity; a "
                        "profile bound to the unit the scenario uses would "
                        "resolve it."
                    ),
                ),
                "MODEL_PROFILE",
                f"{profile_detail}, whose binding names another unit",
            )

        if rating.value != declared:
            raise refuse(
                "INITIALIZATION_INPUT_MISSING",
                f"Parameter {parameter_id} states that the site's foundation "
                f"declares {declared} {unit} for {initial_state_key}, and the "
                f"foundation of site {site.site_id} declares "
                f"{rating.value} {rating.unit}. The scenario names the "
                "foundation as the authority, so its own value is the "
                "requirement to check; a run that froze one and discarded the "
                "other would be choosing which is true. No model profile can "
                "settle that, which is why this is refused rather than "
                "blocked.",
            )

        return rating.value, None, "SITE_FOUNDATION", foundation_detail

    # --- Deciding -----------------------------------------------------------

    def _decide(
        self,
        *,
        scenario: ScenarioDefinition,
        model: ModelProfile,
        identity: DeterministicIdentity,
        frozen_reasons: tuple[BlockingReason, ...] = (),
    ) -> tuple[tuple[BlockingReason, ...], tuple[UnsupportedOptionalInput, ...]]:
        reasons: list[BlockingReason] = []
        optional: list[UnsupportedOptionalInput] = []

        for executable in _executable_inputs(scenario):
            reason, unsupported = _support_for(executable, model)
            if reason is not None:
                reasons.append(reason)
            if unsupported is not None:
                optional.append(unsupported)

        # Beside the state and role reasons, because they are the same fact
        # about the same profile: something the scenario needs that this
        # profile cannot do.
        reasons.extend(frozen_reasons)

        reasons.extend(_cadence_reasons(identity))
        reasons.extend(_publication_reasons(identity))

        return tuple(reasons), tuple(optional)


def _parameters_by_id(
    scenario: ScenarioDefinition,
) -> dict[str, ScenarioParameter]:
    """Every public parameter in the document, by identity, in authored order.

    Parameter identities are unique across the whole document, enforced by the
    scenario parser, so a run input that names one names exactly one thing.
    """
    found: dict[str, ScenarioParameter] = {
        parameter.parameter_id: parameter
        for parameter in scenario.public_parameters
    }
    for entry in scenario.timeline:
        for parameter in entry.parameters:
            found[parameter.parameter_id] = parameter
    return found


def _executable_inputs(
    scenario: ScenarioDefinition,
) -> tuple[ExecutableInput, ...]:
    """Every executable input the scenario declares, from both positions.

    A timeline entry and a parameter can each carry an executable role, and
    both are gathered. Duplicates are collapsed on `(state_key, role)`, so a
    state declared in one role by four rows is one question asked once - but a
    state declared in two roles is two questions, because a profile may model
    a state it cannot report.

    Where the two positions disagree about the requirement, `REQUIRED` wins. A
    state that is required anywhere is required.
    """
    found: dict[tuple[str, str], str] = {}

    def record(
        state_key: str | None, role: str, requirement: str | None
    ) -> None:
        if state_key is None or role not in EXECUTABLE_ROLES:
            return
        key = (state_key, role)
        current = found.get(key)
        resolved = requirement or "REQUIRED"
        if current == "REQUIRED" or resolved == "REQUIRED":
            found[key] = "REQUIRED"
        else:
            found[key] = current or resolved

    for entry in scenario.timeline:
        record(entry.state_key, entry.execution_role, entry.execution_requirement)
        for parameter in entry.parameters:
            record(
                parameter.state_key,
                parameter.execution_role,
                parameter.execution_requirement,
            )
    for parameter in scenario.public_parameters:
        record(
            parameter.state_key,
            parameter.execution_role,
            parameter.execution_requirement,
        )

    return tuple(
        ExecutableInput(
            state_key=state_key,
            execution_role=role,
            execution_requirement=requirement,
        )
        for (state_key, role), requirement in sorted(found.items())
    )


def _support_for(
    executable: ExecutableInput, model: ModelProfile
) -> tuple[BlockingReason | None, UnsupportedOptionalInput | None]:
    """Ask one profile about one executable input.

    Required and unsupported blocks; optional and unsupported is recorded.
    There is no third answer, because `EXECUTION_REQUIREMENTS` has no third
    value and "supported if convenient" is how an input gets ignored.
    """
    supported = model.supported(executable.state_key)

    if supported is None:
        statement = (
            f"Model profile {model.model_profile_id} version "
            f"{model.model_profile_version} does not model "
            f"{executable.state_key}, which this scenario needs as a "
            f"{executable.execution_role}."
        )
        if executable.execution_requirement == "REQUIRED":
            return (
                BlockingReason(
                    kind="STATE_NOT_SUPPORTED",
                    subject=executable.state_key,
                    statement=statement,
                ),
                None,
            )
        return (
            None,
            UnsupportedOptionalInput(
                state_key=executable.state_key,
                execution_role=executable.execution_role,
                statement=statement,
            ),
        )

    if executable.execution_role not in supported.supported_roles:
        statement = (
            f"Model profile {model.model_profile_id} version "
            f"{model.model_profile_version} models "
            f"{executable.state_key}, but not as a "
            f"{executable.execution_role}."
        )
        if executable.execution_requirement == "REQUIRED":
            return (
                BlockingReason(
                    kind="ROLE_NOT_SUPPORTED",
                    subject=executable.state_key,
                    statement=statement,
                ),
                None,
            )
        return (
            None,
            UnsupportedOptionalInput(
                state_key=executable.state_key,
                execution_role=executable.execution_role,
                statement=statement,
            ),
        )

    return None, None


def _cadence_reasons(
    identity: DeterministicIdentity,
) -> Iterable[BlockingReason]:
    for binding in identity.observation_bindings:
        if binding.cadence_resolution != "NOT_RESOLVED":
            continue
        yield BlockingReason(
            kind="CADENCE_NOT_RESOLVED",
            subject=binding.source_id,
            statement=(
                "The publication profile this run selected declares no "
                "cadence for a configured device signal, and nothing else "
                "may supply one. A foundation declares that a signal can "
                "report and declares no rate, and nothing infers one from a "
                "device, from what a screen shows, or from the spacing "
                "between the entries that report through this source."
            ),
        )


def _publication_reasons(
    identity: DeterministicIdentity,
) -> Iterable[BlockingReason]:
    if identity.publication.simulator_source_id is None:
        yield BlockingReason(
            kind="SOURCE_IDENTITY_NOT_RESOLVED",
            subject=identity.profiles.publication_profile_id,
            statement=(
                "The publication profile this run selected declares no "
                "simulator source identity. A run publishes as a named "
                "source or it does not publish; the identity is not derived "
                "from the site, from how the site was created, or from any "
                "device on it."
            ),
        )

    if identity.publication.gateway_id is None:
        yield BlockingReason(
            kind="GATEWAY_IDENTITY_NOT_RESOLVED",
            subject=identity.profiles.publication_profile_id,
            statement=(
                "The publication profile this run selected declares no "
                "gateway identity. A run publishes through a named gateway "
                "or it does not publish, and nothing derives one from the "
                "site or from its provenance."
            ),
        )


def executable_inputs(scenario: ScenarioDefinition) -> Sequence[ExecutableInput]:
    """The executable inputs of one scenario, exposed for tests and callers."""
    return _executable_inputs(scenario)
