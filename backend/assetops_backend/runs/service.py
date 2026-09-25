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

**`runs/refusals.py` states it. This is what it looks like here.** The rule
is not restated: a second copy is a second thing to keep true, and the last
round proved it by letting this module's copy get ahead of the canonical one
while that one went stale.

What the rule costs this module is one shape. `_resolve_foundation_value`
returns a reason instead of raising when the selected profile cannot supply
or locate a value, and `_freeze` carries those out, so it is no longer true
that the whole of `_freeze` raises. What is still true, and what the split
rests on, is that a refusal means nothing could be frozen at all, while a
blocked run is frozen in full - including a value marked as having no
answer, which the record can now represent.

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
    FoundationBinding,
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
from assetops_backend.sites.models import SiteComponent, SiteRecord
from assetops_backend.sites.ports import SiteNotFound, SiteRepository
from assetops_backend.state_refs import StateRef


@dataclass(frozen=True)
class ExecutableInput:
    """One state a scenario needs executed, in one role, at one requirement.

    Gathered from both places an executable role can be declared - a timeline
    entry and a parameter - because a rule applied at one of the two is a rule
    with the other left over, which is the shape of the hole T018's review
    found in the cadence prohibition.

    Gathered at the ADDRESS since T020A1, and asked of the profile at the
    state key. Those are two different grains on purpose: two generators are
    two requirements a scenario can state differently, and they are one
    question to a profile, which models a kind of state and knows nothing
    about how many of them a site has.
    """

    state_ref: StateRef
    execution_role: str
    execution_requirement: str

    @property
    def state_key(self) -> str:
        """The semantic state a model profile answers about."""
        return self.state_ref.state_key

    @property
    def addressed_key(self) -> str:
        """The address the scenario declared."""
        return self.state_ref.addressed_key


@dataclass(frozen=True)
class RequirementConflict:
    """One address and role a scenario declares at two requirements.

    Detection, not refusal. `_executable_inputs` resolves the disagreement by
    taking `REQUIRED` - a state required anywhere is required - and that is
    the safe resolution, because it can only make a run block rather than let
    one through. But the disagreement is still an authoring mistake, and
    T020B owns what the product finally does about it
    (`D-2026-09-22-forcing-state-requirements`). Reporting it at the address
    and role grain is what this slice owes that decision: on a site with two
    tanks, "the scenario disagrees with itself about fuel-tank-volume" names
    two possible mistakes, and "about fuel-tank-volume@north-tank as a
    CAUSAL_INPUT" names one.
    """

    state_ref: StateRef
    execution_role: str
    requirements: tuple[str, ...]

    @property
    def addressed_key(self) -> str:
        return self.state_ref.addressed_key


@dataclass(frozen=True)
class FoundationAnswer:
    """What a Foundation said about one addressed initial value.

    Five things travelled out of the resolver as a bare tuple before
    addressing, and the fifth is the reason this is a record: the address that
    was actually used. A resolved answer carries the component that supplied
    it; a blocked one carries the address as the scenario wrote it. Returning
    both a value and the address it came from, together, is what stops the two
    being assembled separately by the caller and disagreeing.
    """

    value: float | None
    reason: BlockingReason | None
    answered_by: str
    detail: str
    state_ref: StateRef


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RunInventoryService:
    """Read-only access to the Drafts run setup has written.

    Two methods and no more. There is no create here - `RunSetupService` owns
    that and the port has one write - and no update, delete, rerun, start or
    commit, because nothing in this build can do any of them and a method for
    one would be a contract with nothing behind it.

    Ordering is fixed here rather than left to whichever adapter is composed,
    the way the scenario catalog fixes its own. Newest first, because a run
    store grows by appending and the run somebody wants is almost always the
    one they just made; ties break on identity so the order is total and two
    runs created in the same second do not swap places between reads.
    """

    def __init__(self, runs: SimulationRunRepository) -> None:
        self._runs = runs

    def list_runs(self) -> tuple[SimulationRun, ...]:
        """Every persisted Draft, newest first."""
        return tuple(
            sorted(
                self._runs.list_runs(),
                key=lambda record: (record.created_at, record.run_id),
                reverse=True,
            )
        )

    def get_run(self, run_id: str) -> SimulationRun:
        """One Draft by identity.

        Raises:
            RunNotFound: no such `run_id`. Never another run: a lookup that
                fell back to something would put one run's frozen identity
                under another run's name.
        """
        return self._runs.get_run(run_id)


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

        # A Foundation-owned parameter states no value
        # (`D-2026-09-22-foundation-value-declaration`), so there is nothing
        # for this record to resolve. It is left out rather than frozen as a
        # `SCENARIO` answer of `None`: `answered_by` here has two cases and
        # neither is true of it, and its real answer - the Site's property,
        # with the Foundation named - is frozen as a
        # `FrozenInitializationInput`, which is the record that has a shape
        # for an absent value and a reason beside it.
        # Excluded BY WHAT REPRESENTS THEM, not by a proxy for it.
        #
        # This filtered on `value is not None` until an independent review
        # showed the two facts are not the same one. It assumed every
        # valueless parameter was represented as a
        # `FrozenInitializationInput`, and a Foundation-owned parameter that
        # did not initialize was represented by neither: the row vanished, no
        # reason was raised, and the run reported `READY`.
        #
        # The scenario parser now refuses that combination, so the two sets
        # agree again. Filtering on the frozen collection rather than on the
        # absence of a number is what keeps them agreeing: if a later slice
        # adds a Foundation-owned parameter that is not an initial value, it
        # arrives here as a `FrozenParameter` carrying no number rather than
        # as a row nobody kept.
        #
        # **Be precise about what catches it then, because this comment said
        # the wrong thing and a second review caught that.** It said the run
        # record refuses such a parameter loudly. It does not:
        # `FrozenParameter` is annotated and not validated, and
        # `SimulationRun.__post_init__` checks initialization rows rather than
        # resolved parameters - so a record built that way is returned as
        # `READY` with no reasons. The boundary that actually holds is one
        # layer out, in `YamlRunStore.create_run`, which re-reads the staged
        # document before committing it and refuses a value the run document
        # parser will not take, leaving the store directory empty.
        # `test_run_store.py` keeps that demonstrated rather than asserted
        # here.
        #
        # So the guarantee is: such a row is KEPT rather than dropped, and it
        # cannot be persisted. It is not that the dataclass rejects it. A
        # future author must not build on a guard that is not there.
        frozen_states = {item.parameter_id for item in initialization}
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
            if parameter_id not in frozen_states
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
            # The address this row is frozen at. It stays the authored one for
            # every owner but the Foundation, because only a Foundation answer
            # involves choosing a component: a scenario-owned initial value is
            # already as addressed as it is going to be, and a run input names
            # a parameter rather than an asset.
            frozen_ref = initial.state_ref

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
                # No `declared` argument any more. A Foundation-owned
                # parameter states no number
                # (`D-2026-09-22-foundation-value-declaration`), so there is
                # nothing for the Foundation's own answer to be checked
                # against and no way for a run to meet two answers.
                answer = self._resolve_foundation_value(
                    state_ref=initial.state_ref,
                    unit=initial.unit,
                    site=site,
                    model=model,
                )
                value = answer.value
                reason = answer.reason
                answered_by = answer.answered_by
                detail = answer.detail
                # Resolved when something answered, authored when nothing did.
                # The blocked case keeps the authored address so the reason
                # beside it names the same subject.
                frozen_ref = answer.state_ref
            else:
                # A versioned model rule owns it, and no profile in this build
                # carries one: `SupportedState` has no field a model-supplied
                # initial value could live in. T020A did not add it either.
                # That is option C of `D-2026-09-22-foundation-value-declaration`
                # - the model profile declaring the need rather than the
                # scenario - and it is a follower with a trigger rather than a
                # slice: the first model rule that needs a Foundation value
                # without a scenario asking for it, which T024 is the candidate
                # for. Until then this is the profile failing to answer - the
                # same fact as a missing binding, so the same reason.
                value = None
                detail = (
                    f"model profile {model.model_profile_id} version "
                    f"{model.model_profile_version}, which declares no rule "
                    "for it"
                )
                reason = BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=initial.addressed_key,
                    statement=(
                        f"The initial value of {initial.addressed_key} is "
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
                    state_ref=frozen_ref,
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
        state_ref: StateRef,
        unit: str,
        site: SiteRecord,
        model: ModelProfile,
    ) -> FoundationAnswer:
        """The Foundation's answer for one addressed initial value, or a reason.

        Which declared fact answers is a binding the model profile carries,
        never a match by spelling: `fuel-tank-capacity` and a component called
        `fuel-tank` look related and nothing about their names says one is the
        other, which is the same reason T018's review made a bound a
        declaration rather than a shared prefix.

        WHICH component answers is the scenario's address, also never a match
        by spelling. An explicit selector picks that component and nothing
        else; an omitted one is a question the Foundation must answer with
        exactly one candidate or not at all.

        ## Every failure here blocks, and none refuses

        The T019 user review settled the discriminator: **would a different
        model profile fix this?** The Foundation's answer is only locatable
        THROUGH the profile's binding, so a failure to locate it is a joint
        fact about the pair - and the profile is the half a person can change
        on the setup form. T020A1 adds a third half a person can change, the
        address the scenario declares, and it blocks for the same reason: it
        is a declaration, and a declaration can be corrected.

        Eight cases, all blocking, all `INITIAL_VALUE_NOT_RESOLVED`:

        - the scenario claims the state at one scope and the profile models it
          at the other. A site-wide fact and a fact about one machine are two
          different claims and no Foundation reconciles them;
        - the profile declares no binding, so nothing was even asked of the
          Foundation;
        - **the binding's own declared unit is not the unit the scenario
          declares.** Decided before the Site is consulted, because it needs
          no Site: the profile says what quantity it will answer with and the
          scenario says what it asked for. `binding.unit` was read by nothing
          at all until an independent review found it, and a declared unit
          nothing checks reads as a guarantee it is not;
        - the address names a component this Foundation does not declare;
        - the address names a component this Foundation declares and it is not
          of the type the binding needs. **Nothing falls back to a component
          that is**, which is acceptance criterion 4: an author who named the
          wrong asset gets a refusal naming the asset they named, not the
          value off a different one;
        - the binding's component type matches nothing this Foundation
          declares, for an unqualified address;
        - it matches more than one and the address chose none of them, which
          is two answers to one value. This is the case T020A left open and
          this slice closes: the way to resolve it is to say which, and the
          reason names both candidates so the author can;
        - the one selected component declares no such property. This is the
          case `D-2026-09-22-foundation-property-absent-blocks` settled: the
          property name is as much the profile's aim as the component type is,
          so a different profile naming a different property may find
          something this Foundation does declare;
        - the found property's unit is not the binding's. The three units must
          agree, and this is the third side of that triangle: a profile naming
          a unit the property it chose is not declared in.

        **There is no refusal.** `INITIAL_VALUE_ANSWERS_DISAGREE` used to live
        at the end of this function, comparing the Foundation's number against
        a number the scenario stated the Foundation declares. After
        `D-2026-09-22-foundation-value-declaration` no document can state that
        number, so nothing can produce the kind, and it was retired with its
        only producer under `D-2026-09-22-expiry-follows-the-condition`.

        **And nothing searches for a convenient value.** The candidate set is
        the components of the declared type - not the components that happen
        to declare the property - so a second tank cannot answer for the one
        the address could not reach. Narrowing by property would turn both the
        ambiguity and the wrong-selector case into a silent choice, which is
        the one outcome addressing exists to prevent.

        **Every returned reason names the address, not the state key.** Two
        tanks are two rows on a blocked run, and a reason keyed on
        `fuel-tank-volume` would be deduplicated down to one - leaving the
        second absent value with nothing explaining it.
        """
        foundation_detail = (
            f"site {site.site_id} foundation version "
            f"{site.foundation.version}"
        )
        profile_detail = (
            f"model profile {model.model_profile_id} version "
            f"{model.model_profile_version}"
        )
        address = state_ref.addressed_key

        def blocked(
            statement: str, answered_by: str, detail: str
        ) -> FoundationAnswer:
            return FoundationAnswer(
                value=None,
                reason=BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=address,
                    statement=statement,
                ),
                answered_by=answered_by,
                detail=detail,
                # The address as AUTHORED. Nothing resolved, so there is no
                # resolved address to record, and writing one here would name
                # an asset beside a value it did not supply.
                state_ref=state_ref,
            )

        supported = model.supported(state_ref.state_key)

        # Scope before binding, because a scope disagreement explains a
        # missing binding rather than the other way round: a site-wide state
        # has no binding BY CONSTRUCTION, so reporting "no binding declared"
        # for it would name the symptom and hide the cause.
        if supported is not None and supported.scope != state_ref.scope:
            claimed = (
                "as a fact about the whole installation"
                if state_ref.scope == "SITE"
                else "as a fact about one component"
            )
            modelled = (
                "a fact about the whole installation"
                if supported.scope == "SITE"
                else "a fact about one component"
            )
            return blocked(
                f"The scenario claims {state_ref.state_key} {claimed} and "
                f"{profile_detail} models it as {modelled}. Those are two "
                "different quantities, so no foundation answers for both; "
                "address the state the way the profile models it, or select a "
                "profile that models it the way the scenario claims it.",
                "MODEL_PROFILE",
                f"{profile_detail}, which models this state at another scope",
            )

        binding = None if supported is None else supported.foundation_binding

        if binding is None:
            return blocked(
                f"The initial value of {address} is declared as owned by the "
                f"site's foundation, and {profile_detail} declares no binding "
                "saying which declared fact answers for it. Nothing here "
                "matches a state to a component by the look of its name, so a "
                "profile that declares the binding is what this run needs.",
                "MODEL_PROFILE",
                f"{profile_detail}, which declares no binding for it",
            )

        # The binding's OWN unit, checked before the Site is consulted.
        #
        # It was checked against nothing at all until an independent review
        # pointed at it: only the found property's unit was compared to the
        # scenario's, and `binding.unit` was a field production code never
        # read. Changing it from `L` to `%` still produced `READY` with
        # 500 L. **A declared unit that nothing checks is worse than no unit,
        # because it reads as a guarantee.**
        if binding.unit != unit:
            return blocked(
                f"The scenario declares {address} in {unit} and "
                f"{profile_detail} binds it to the {binding.property_key} "
                f"property declared in {binding.unit}. The profile and the "
                "scenario disagree about what kind of quantity this is, so no "
                "foundation could answer for both; a profile bound to the "
                "unit the scenario uses would resolve it.",
                "MODEL_PROFILE",
                f"{profile_detail}, whose binding names another unit",
            )

        # A site-wide reference cannot reach here: the scope check above
        # refuses the disagreement, and a SITE-scoped supported state may not
        # carry a binding at all (`SupportedState.__post_init__`). So by this
        # point the claim is component-scoped and the only question left is
        # which component.
        component, reason = self._select_component(
            state_ref=state_ref,
            binding=binding,
            site=site,
            address=address,
            foundation_detail=foundation_detail,
            profile_detail=profile_detail,
        )
        if reason is not None:
            return FoundationAnswer(
                value=None,
                reason=reason[0],
                answered_by=reason[1],
                detail=reason[2],
                state_ref=state_ref,
            )
        assert component is not None

        declared_property = None
        for item in component.properties or ():
            if item.property_key == binding.property_key:
                declared_property = item
                break

        if declared_property is None:
            return blocked(
                f"{profile_detail} looks for the initial value of {address} "
                f"in the {binding.property_key} property of component "
                f"{component.component_id}, and the foundation of site "
                f"{site.site_id} declares no such property on it. Nothing "
                "looks for that value on another component, so this needs "
                "either a foundation that declares the property or a profile "
                "that names one it does declare.",
                "SITE_FOUNDATION",
                (
                    f"{foundation_detail}, whose component "
                    f"{component.component_id} declares no "
                    f"{binding.property_key}"
                ),
            )

        # And the found property against the binding. The three units must
        # agree, and the check above has already established that the binding
        # agrees with the scenario, so this closes the triangle: a binding
        # naming a unit the property it names is not declared in.
        #
        # Reachable because a property key carries its unit from the closed
        # vocabulary while a binding states one separately - so a profile can
        # name `tank-capacity` and claim it is a percentage. The vocabulary
        # settles which of the two is right; this says the profile is wrong
        # about the property it chose rather than about the scenario.
        if declared_property.unit != binding.unit:
            return blocked(
                f"{profile_detail} binds {address} to the "
                f"{binding.property_key} property declared in {binding.unit}, "
                f"and component {component.component_id} declares that "
                f"property in {declared_property.unit}. A run freezes the "
                "foundation's value, so the binding and the property must "
                "name one quantity; a profile bound to the unit the property "
                "carries would resolve it.",
                "MODEL_PROFILE",
                f"{profile_detail}, whose binding names another unit",
            )

        return FoundationAnswer(
            value=declared_property.value,
            reason=None,
            answered_by="SITE_FOUNDATION",
            detail=(
                f"{foundation_detail}, component {component.component_id} "
                f"property {declared_property.property_key}"
            ),
            # The RESOLVED address, which is the point of the slice. An
            # author who named no component gets the one that answered
            # recorded here, so a reader of the frozen run - and T021's kernel
            # - knows whose number this is without re-running the resolution
            # against a Foundation that may have been reordered since.
            state_ref=state_ref.resolved_to(component.component_id),
        )

    def _select_component(
        self,
        *,
        state_ref: StateRef,
        binding: FoundationBinding,
        site: SiteRecord,
        address: str,
        foundation_detail: str,
        profile_detail: str,
    ) -> tuple[SiteComponent | None, tuple[BlockingReason, str, str] | None]:
        """Which component this address means, or why none was chosen.

        Two questions, and which one is asked depends on whether the author
        named a component.

        **Named.** That component and no other. It must exist and it must be
        of the type the binding needs; a second component that WOULD fit is
        not consulted, because then naming the wrong asset would silently
        become naming the right one and the selector would be advisory.

        **Not named.** Exactly one candidate of the bound type, or nothing.
        Zero and two are different facts with different fixes - declare the
        component, or say which one - so they are two reasons rather than one.

        The candidate set is the components OF THE DECLARED TYPE, not the
        components that declare the property. Narrowing it by property would
        let a second tank answer for the one the address could not reach,
        which is the fallback the whole module refuses.
        """
        components = site.foundation.components

        if state_ref.component_id is not None:
            named = [
                component
                for component in components
                if component.component_id == state_ref.component_id
            ]
            if not named:
                return None, (
                    BlockingReason(
                        kind="INITIAL_VALUE_NOT_RESOLVED",
                        subject=address,
                        statement=(
                            f"The scenario resolves the initial value of "
                            f"{state_ref.state_key} on component "
                            f"{state_ref.component_id}, and the foundation of "
                            f"site {site.site_id} declares no component with "
                            "that identity. Nothing answers from a different "
                            "component: a named asset is the one the run "
                            "freezes from, or the run does not freeze."
                        ),
                    ),
                    "SITE_FOUNDATION",
                    (
                        f"{foundation_detail}, which declares no component "
                        f"{state_ref.component_id}"
                    ),
                )

            component = named[0]
            if component.component_type != binding.component_type:
                return None, (
                    BlockingReason(
                        kind="INITIAL_VALUE_NOT_RESOLVED",
                        subject=address,
                        statement=(
                            f"The scenario resolves the initial value of "
                            f"{state_ref.state_key} on component "
                            f"{component.component_id}, which the foundation "
                            f"of site {site.site_id} declares as a "
                            f"{component.component_type}, and "
                            f"{profile_detail} answers for this state from a "
                            f"{binding.component_type}. The named component "
                            "is the one this run would freeze from, so "
                            "nothing looks for a "
                            f"{binding.component_type} elsewhere on the site."
                        ),
                    ),
                    "SITE_FOUNDATION",
                    (
                        f"{foundation_detail}, whose component "
                        f"{component.component_id} is a "
                        f"{component.component_type}"
                    ),
                )
            return component, None

        matches = [
            component
            for component in components
            if component.component_type == binding.component_type
        ]

        if not matches:
            return None, (
                BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=address,
                    statement=(
                        f"{profile_detail} looks for the initial value of "
                        f"{address} in the {binding.property_key} property of "
                        f"a {binding.component_type} component, and the "
                        f"foundation of site {site.site_id} declares no such "
                        "component. A profile whose binding names something "
                        "this site declares would resolve it."
                    ),
                ),
                "SITE_FOUNDATION",
                f"{foundation_detail}, which declares nothing the binding fits",
            )

        if len(matches) > 1:
            named_ids = ", ".join(sorted(item.component_id for item in matches))
            return None, (
                BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=address,
                    statement=(
                        f"The scenario asks for the initial value of "
                        f"{state_ref.state_key} without saying which "
                        f"component it is about, {profile_detail} answers for "
                        f"it from a {binding.component_type}, and the "
                        f"foundation of site {site.site_id} declares more "
                        f"than one: {named_ids}. Two answers to one initial "
                        "value is not something a run may choose between, so "
                        "the scenario has to name the component it means - "
                        f"for example {state_ref.state_key}@"
                        f"{sorted(item.component_id for item in matches)[0]}."
                    ),
                ),
                "SITE_FOUNDATION",
                f"{foundation_detail}, which declares more than one match",
            )

        return matches[0], None


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

        return _deduplicated(reasons), tuple(optional)


def _deduplicated(
    reasons: list[BlockingReason],
) -> tuple[BlockingReason, ...]:
    """One row per fact, in the order the facts were found.

    `BlockingReason.subject` exists so that two reasons of the same kind are
    two facts rather than one repeated, and a run can reach the same fact
    twice: a state the profile does not model, needed in two roles, was two
    identical-subject rows differing only in the role their prose mentioned.
    A reader counting rows would have counted the same problem twice.

    Deduplicating on `(kind, subject)` rather than on the whole reason is
    deliberate: if two rows agree on both, they are the same fact, and a
    difference in their wording is a reason to fix the wording rather than to
    print both.
    """
    seen: set[tuple[str, str]] = set()
    unique: list[BlockingReason] = []
    for reason in reasons:
        key = (reason.kind, reason.subject)
        if key in seen:
            continue
        seen.add(key)
        unique.append(reason)
    return tuple(unique)


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
    both are gathered. Duplicates are collapsed on `(address, role)`, so a
    state declared in one role by four rows is one question asked once - but a
    state declared in two roles is two questions, because a profile may model
    a state it cannot report.

    **On the address, not the key, since T020A1.** Two tanks declared in one
    role were one entry here, so a scenario could declare the north tank
    required and the south tank optional and the second declaration vanished
    into the first. They are two requirements, and `requirement_conflicts`
    below reports it when one document states both about one of them.

    Where the two positions disagree about the requirement, `REQUIRED` wins. A
    state that is required anywhere is required.
    """
    return tuple(
        ExecutableInput(
            state_ref=ref,
            execution_role=role,
            execution_requirement=requirement,
        )
        for (_, role), (ref, requirement) in sorted(
            _declared_requirements(scenario).items()
        )
    )


def _declared_requirements(
    scenario: ScenarioDefinition,
) -> dict[tuple[str, str], tuple[StateRef, str]]:
    """Every `(address, role)` the scenario declares, and its requirement."""
    found: dict[tuple[str, str], tuple[StateRef, str]] = {}

    def record(
        state_ref: StateRef | None, role: str, requirement: str | None
    ) -> None:
        if state_ref is None or role not in EXECUTABLE_ROLES:
            return
        key = (state_ref.addressed_key, role)
        current = found.get(key)
        resolved = requirement or "REQUIRED"
        if current is not None and (
            current[1] == "REQUIRED" or resolved == "REQUIRED"
        ):
            found[key] = (state_ref, "REQUIRED")
        else:
            found[key] = (state_ref, resolved)

    for entry in scenario.timeline:
        record(entry.state_ref, entry.execution_role, entry.execution_requirement)
        for parameter in entry.parameters:
            record(
                parameter.state_ref,
                parameter.execution_role,
                parameter.execution_requirement,
            )
    for parameter in scenario.public_parameters:
        record(
            parameter.state_ref,
            parameter.execution_role,
            parameter.execution_requirement,
        )

    return found


def requirement_conflicts(
    scenario: ScenarioDefinition,
) -> tuple[RequirementConflict, ...]:
    """Every address and role one document states two requirements for.

    Detectable at the resolved address and role grain, which is acceptance
    criterion 8. What the product finally DOES about a conflict - refuse the
    document, block the run, or keep taking the stricter answer - is T020B's,
    and this reports rather than decides so that decision has something to act
    on. `_executable_inputs` keeps taking `REQUIRED` meanwhile, which can only
    block a run that would otherwise have run and never the reverse.

    Two components of one type declared at different requirements are NOT a
    conflict. They are two independent requirements, which is the whole of the
    slice, and reporting them as a disagreement would be the collapse this
    module has just stopped doing.
    """
    stated: dict[tuple[str, str], tuple[StateRef, list[str]]] = {}

    def record(
        state_ref: StateRef | None, role: str, requirement: str | None
    ) -> None:
        if state_ref is None or role not in EXECUTABLE_ROLES:
            return
        if requirement is None:
            return
        entry = stated.setdefault(
            (state_ref.addressed_key, role), (state_ref, [])
        )
        if requirement not in entry[1]:
            entry[1].append(requirement)

    for entry_row in scenario.timeline:
        record(
            entry_row.state_ref,
            entry_row.execution_role,
            entry_row.execution_requirement,
        )
        for parameter in entry_row.parameters:
            record(
                parameter.state_ref,
                parameter.execution_role,
                parameter.execution_requirement,
            )
    for parameter in scenario.public_parameters:
        record(
            parameter.state_ref,
            parameter.execution_role,
            parameter.execution_requirement,
        )

    return tuple(
        RequirementConflict(
            state_ref=ref,
            execution_role=role,
            requirements=tuple(sorted(requirements)),
        )
        for (_, role), (ref, requirements) in sorted(stated.items())
        if len(requirements) > 1
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
            f"{executable.state_key} at all, which this scenario needs it "
            "to."
        )
        if executable.execution_requirement == "REQUIRED":
            # The statement no longer names the role, and the reason is
            # deduplicated on `(kind, subject)` below. A state the profile
            # does not model is ONE fact however many roles the scenario
            # uses it in; saying it twice, differing only in which role the
            # prose mentioned, is the repetition `subject` exists to prevent.
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
            # The subject carries the role here, because this IS one fact per
            # role: a profile can model a state it can cause and cannot
            # report, and those are two things to fix.
            return (
                BlockingReason(
                    kind="ROLE_NOT_SUPPORTED",
                    subject=(
                        f"{executable.state_key} as "
                        f"{executable.execution_role}"
                    ),
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
        # A device signal with no cadence is the one unresolved case; an
        # operator record has no rate to resolve.
        if (
            binding.cadence_minutes is not None
            or binding.source_kind != "DEVICE_SIGNAL"
        ):
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
