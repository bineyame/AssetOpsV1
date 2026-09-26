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


@dataclass(frozen=True)
class ResolvedAddress:
    """Which component one declared reference means, or why none was found.

    ## Why this exists at all, and why it is not part of the Foundation answer

    T020A1 first put address resolution inside `_resolve_foundation_value`,
    which meant a reference was only ever resolved when the Site's Foundation
    was the thing answering for it. An independent review found what that
    leaves open, and it is not a corner: a `SCENARIO_INPUT` or `RUN_OVERRIDE`
    initial value, and every forcing input and reported observation, carried
    its authored reference straight into the frozen run. So
    `example-stored-level` with no selector, and even
    `example-stored-level@ghost-tank` naming a component the Foundation does
    not declare, were both frozen and called READY - a number, persisted,
    with no asset behind it.

    The rows were there, so this was not the old disappearance defect. What
    was missing is the ADDRESS OBLIGATION: a component-scoped reference has to
    identify one component of this Site before the run is ready, whoever
    supplies its number and whether or not it has one. Making that a separate
    step, run over every reference the document declares, is what stops the
    obligation from being attached to one owner again.

    ## What it does not do

    It resolves by DECLARED rules and nothing else. An explicit selector is
    looked up by identity; an omitted one is resolved through the component
    type the selected profile's `FoundationBinding` names for that state, and
    blocks when the profile declares no binding to name one. Nothing infers a
    component type from the spelling of a state key, and nothing narrows
    candidates by which of them happens to carry a useful property - the two
    rules the resolver has refused since T020A.
    """

    authored: StateRef
    resolved: StateRef | None
    component: SiteComponent | None
    reason: BlockingReason | None
    #: Whose declaration a reader should look at when it failed. The profile
    #: when it declares no way to choose, the Foundation when the Site does
    #: not declare what was named.
    answered_by: str
    detail: str
    #: That this reference was handed to `_support_for` rather than answered
    #: here, and that `_support_for` really is asked about it - the resolver
    #: sets this only for an address that appears in an executable
    #: declaration. A deferred reference is NOT resolved, and saying so is
    #: the whole reason the field exists: the version before it recorded
    #: these as settled, and a reference that reached neither check came back
    #: looking answered.
    deferred_to_support: bool = False

    @property
    def is_resolved(self) -> bool:
        """That this reference names one thing, established HERE.

        Defined as "no reason" alone until a second review pointed out what
        that made it say: a deferred reference has no reason either, so the
        predicate reported as resolved exactly the cases this function had
        not checked. It now means what its name means, and a caller that
        wants "nothing to report yet" has to ask for the deferral by name.
        """
        return self.reason is None and not self.deferred_to_support


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

        Addresses are resolved ONCE here, over the whole document, before any
        value is looked up. Resolving them inside the Foundation lookup is
        what left every scenario-owned and run-owned reference unresolved, so
        the pass runs first and the value lookup consumes its answer.
        """
        addresses = resolve_state_addresses(scenario, site, model)

        initialization, unresolved = self._freeze_initialization(
            scenario=scenario,
            site=site,
            model=model,
            supplied=supplied,
            addresses=addresses,
        )

        # Every reference the document declares, not only the ones that
        # initialize something. A forcing input carries no initial value and
        # still has to say which machine it forces.
        unresolved = unresolved + tuple(
            address.reason
            for address in addresses.values()
            if address.reason is not None
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
        addresses: dict[str, ResolvedAddress],
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
            # The address this row is frozen at, for EVERY owner.
            #
            # This used to stay the authored reference for every owner but
            # the Foundation, on the reasoning that only a Foundation answer
            # involves choosing a component. That reasoning was wrong and an
            # independent review proved it: a scenario-owned or run-owned
            # initial value is a claim about one asset too, and leaving its
            # reference alone let `example-stored-level` with no selector -
            # and `@ghost-tank`, naming a component the Foundation does not
            # declare - freeze and report READY. Who supplies the NUMBER and
            # which asset the number is ABOUT are two different questions.
            address = addresses[initial.addressed_key]
            frozen_ref = address.resolved or address.authored

            if address.reason is not None:
                # The address did not resolve, so there is no world state
                # for this to be the initial value OF, whoever states the
                # number. The row is frozen absent with the address
                # failure's attribution beside it, and the address pass has
                # already produced the reason that names it.
                #
                # This branch runs BEFORE the owner is looked at, which is
                # the point of it. An earlier draft kept a scenario-owned
                # number on an unresolvable row on the grounds that the
                # scenario really did state it - and that put `100 L` on the
                # detail screen beside `example-stored-volume@site-generator`
                # on a site whose generator cannot carry that state. It also
                # made the record behave one way for two owners and another
                # way for the third, which is the ownership-dependent
                # treatment this whole round exists to remove.
                value = None
                answered_by = address.answered_by
                detail = address.detail
            elif owner == "SCENARIO_INPUT":
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
                    address=address,
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
                #
                # **Against the address the ROW carries**, which is the
                # resolved one when the reference resolved. It named the
                # authored key for one round, and on a one-tank site that
                # meant a bare model-owned reference froze at
                # `@north-tank` with a reason about the bare key: the record
                # invariant caught the mismatch and raised, so a Draft that
                # should have been BLOCKED and inspectable was no Draft at
                # all. The rule this now follows, everywhere: a missing
                # value, the reference frozen beside it and the explanation
                # for it are kept at ONE grain.
                value = None
                detail = (
                    f"model profile {model.model_profile_id} version "
                    f"{model.model_profile_version}, which declares no rule "
                    "for it"
                )
                reason = BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=frozen_ref.addressed_key,
                    statement=(
                        f"The initial value of {frozen_ref.addressed_key} is "
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
        address: ResolvedAddress,
        unit: str,
        site: SiteRecord,
        model: ModelProfile,
    ) -> FoundationAnswer:
        """The Foundation's number for one resolved address, or a reason.

        It no longer chooses the component. `resolve_state_addresses` did
        that, over every reference the document declares and before anything
        was frozen, and this consumes the answer - which is the whole of the
        correction an independent review asked for. While selection lived
        here, a reference was only ever resolved when the Foundation happened
        to be the thing answering for its number, so every scenario-owned and
        run-owned reference went into the frozen run exactly as authored.

        Which declared fact answers is still a binding the model profile
        carries, never a match by spelling: `fuel-tank-capacity` and a
        component called `fuel-tank` look related and nothing about their
        names says one is the other, which is the same reason T018's review
        made a bound a declaration rather than a shared prefix.

        ## Every failure here blocks, and none refuses

        The T019 user review settled the discriminator: **would a different
        model profile fix this?** The Foundation's answer is only locatable
        THROUGH the profile's binding, so a failure to locate it is a joint
        fact about the pair - and the profile is the half a person can change
        on the setup form. The address is a third half a person can change,
        and it blocks for the same reason: it is a declaration.

        **Five cases, which is five `return blocked(...)` calls below** - the
        count and the list drifted apart once and a backup review counted
        them, so they are stated together. All blocking, all
        `INITIAL_VALUE_NOT_RESOLVED`, and each about a VALUE rather than an
        asset:

        1. the scenario claims the state at one scope and the profile models
           it at the other. A site-wide fact and a fact about one machine are
           two different claims and no Foundation reconciles them;
        2. the profile declares no binding, so nothing was even asked of the
           Foundation;
        3. **the binding's own declared unit is not the unit the scenario
           declares.** Decided before the Site's answer is read, because it
           needs no Site: the profile says what quantity it will answer with
           and the scenario says what it asked for. `binding.unit` was read
           by nothing at all until an independent review found it, and a
           declared unit nothing checks reads as a guarantee it is not;
        4. the resolved component declares no such property. The case
           `D-2026-09-22-foundation-property-absent-blocks` settled: the
           property name is as much the profile's aim as the component type
           is, so a different profile naming a different property may find
           something this Foundation does declare;
        5. the found property's unit is not the binding's. The three units
           must agree, and this closes the triangle: a profile naming a unit
           the property it chose is not declared in.

        The cases that were here and are now the address pass's report
        `STATE_ADDRESS_NOT_RESOLVED` instead, because they are the same fact
        for a forcing input that has no initial value to be unresolved: no
        component with that identity, a component of the wrong type, no
        candidate of the bound type, and more than one candidate. The
        wrong-type case was still listed here after it moved, which is how
        the list came to have six entries under a heading that said five.

        **There is no refusal.** `INITIAL_VALUE_ANSWERS_DISAGREE` used to
        live at the end of this function, comparing the Foundation's number
        against a number the scenario stated the Foundation declares. After
        `D-2026-09-22-foundation-value-declaration` no document can state that
        number, so nothing can produce the kind, and it was retired with its
        only producer under `D-2026-09-22-expiry-follows-the-condition`.
        """
        foundation_detail = (
            f"site {site.site_id} foundation version "
            f"{site.foundation.version}"
        )
        profile_detail = (
            f"model profile {model.model_profile_id} version "
            f"{model.model_profile_version}"
        )
        # The address the row will carry: the resolved one when the
        # reference resolved, the authored one when it did not. Every reason
        # below names THIS, so the missing value, the reference frozen beside
        # it and the explanation stay at one grain. A round where they did
        # not made the record invariant raise instead of producing a BLOCKED
        # Draft, which is worse than the defect it replaced.
        frozen_ref = address.resolved or state_ref
        addressed = frozen_ref.addressed_key

        def blocked(
            statement: str, answered_by: str, detail: str
        ) -> FoundationAnswer:
            return FoundationAnswer(
                value=None,
                reason=BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=addressed,
                    statement=statement,
                ),
                answered_by=answered_by,
                detail=detail,
                state_ref=frozen_ref,
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
                f"The initial value of {addressed} is declared as owned by "
                "the site's foundation, and "
                f"{profile_detail} declares no binding saying which declared "
                "fact answers for it. Nothing here matches a state to a "
                "component by the look of its name, so a profile that "
                "declares the binding is what this run needs.",
                "MODEL_PROFILE",
                f"{profile_detail}, which declares no binding for it",
            )

        # The binding's OWN unit, checked before the Site's answer is read.
        #
        # It was checked against nothing at all until an independent review
        # pointed at it: only the found property's unit was compared to the
        # scenario's, and `binding.unit` was a field production code never
        # read. Changing it from `L` to `%` still produced `READY` with
        # 500 L. **A declared unit that nothing checks is worse than no unit,
        # because it reads as a guarantee.**
        if binding.unit != unit:
            return blocked(
                f"The scenario declares {addressed} in {unit} and "
                f"{profile_detail} binds it to the {binding.property_key} "
                f"property declared in {binding.unit}. The profile and the "
                "scenario disagree about what kind of quantity this is, so no "
                "foundation could answer for both; a profile bound to the "
                "unit the scenario uses would resolve it.",
                "MODEL_PROFILE",
                f"{profile_detail}, whose binding names another unit",
            )

        # The address pass already said this reference names no asset, and
        # said it in a reason of its own. Repeating it here as a second
        # reason would report one fact twice, so the row is frozen absent and
        # carries the address pass's attribution.
        component = address.component
        if component is None:
            return FoundationAnswer(
                value=None,
                reason=None,
                answered_by=address.answered_by,
                detail=address.detail,
                state_ref=address.authored,
            )

        # The binding's component type is NOT checked here any more. It moved
        # into `resolve_state_addresses`, because a check that lives in the
        # Foundation's number lookup is a check that applies only when the
        # Foundation supplies the number - and naming a generator for a tank
        # state blocked under `SITE_FOUNDATION` while freezing 100 L under
        # `SCENARIO_INPUT`. Same obligation, same disease as R1, one position
        # further in. By the time this runs, `address.component` is a
        # component of the bound type or there is no component at all.

        declared_property = None
        for item in component.properties or ():
            if item.property_key == binding.property_key:
                declared_property = item
                break

        if declared_property is None:
            return blocked(
                f"{profile_detail} looks for the initial value of {addressed} "
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
                f"{profile_detail} binds {addressed} to the "
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
            state_ref=address.resolved or state_ref,
        )


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


def declared_state_refs(
    scenario: ScenarioDefinition,
) -> tuple[tuple[StateRef, str], ...]:
    """Every state reference the document declares, and where it was written.

    Four positions, because a reference can be written in four places and a
    rule applied at three of them is a rule with the fourth left over - the
    shape of the hole T018's review found in the cadence prohibition and of
    the one T020A1's review found in address resolution. A timeline entry
    names a state; a parameter on that entry names one; a public parameter
    names one; and a bound names the OTHER state it limits, which is a
    reference to a world state like any other and can be just as wrong.

    Deduplicated on the canonical address, because the same address written
    four times is one thing to resolve. `where` keeps the first position it
    was seen at, for the message.
    """
    found: dict[str, tuple[StateRef, str]] = {}

    def record(ref: StateRef | None, where: str) -> None:
        if ref is None:
            return
        found.setdefault(ref.addressed_key, (ref, where))

    for entry in scenario.timeline:
        record(entry.state_ref, f"entry {entry.event_id!r}")
        for parameter in entry.parameters:
            record(
                parameter.state_ref, f"parameter {parameter.parameter_id!r}"
            )
            if parameter.bounds is not None:
                record(
                    parameter.bounds.state_ref,
                    f"the bound declared by {parameter.parameter_id!r}",
                )
    for parameter in scenario.public_parameters:
        record(parameter.state_ref, f"parameter {parameter.parameter_id!r}")
        if parameter.bounds is not None:
            record(
                parameter.bounds.state_ref,
                f"the bound declared by {parameter.parameter_id!r}",
            )

    return tuple(found.values())


def resolve_state_addresses(
    scenario: ScenarioDefinition, site: SiteRecord, model: ModelProfile
) -> dict[str, ResolvedAddress]:
    """Which component each declared reference means, by address.

    One pass over the whole document, before anything is frozen, because the
    obligation is about the REFERENCE and not about who answers for its
    number. Run it per owner and it comes back attached to an owner, which is
    exactly the defect this replaces.

    ## Visiting a reference is not the same as resolving it

    The second review's sentence, and it is worth keeping because the first
    version of this function read as though it were. Every reference was
    VISITED - the enumeration below is genuinely exhaustive - but two of the
    branches recorded a reference as settled while checking nothing, on the
    assumption that `_support_for` would report the problem. `_support_for`
    is asked about executable declarations, so a reference occurring only as
    a BOUND TARGET reached neither check, and
    `unmodelled-volume@ghost-tank` came back READY with no reasons at all.

    So a reference now leaves this function in one of three states, and the
    third is a promise this function is not allowed to make on its own:

    - RESOLVED: it names one component of this Site, checked here;
    - REFUSED: it carries a reason, and the run blocks;
    - DEFERRED: `_support_for` will report it, and `deferred_to_support`
      says so rather than the record merely looking resolved. It is set only
      when the same address really does appear in an executable declaration,
      which is read from `_declared_requirements` - the same source
      `_support_for` is driven from - rather than assumed.

    ## What it checks, and in which order

    **Existence first, before the profile is consulted at all.** Whether this
    Foundation declares a component with that identity needs no profile and
    no state vocabulary, so asking it first means an explicitly addressed
    reference is checked even when the state it names is one this profile
    does not model. That is what closes the bound-only route without
    inventing a bounds mechanism.

    **Then compatibility, when the profile declares a binding.** The binding
    names the component type that carries this state, so a reference naming a
    component of another type does not identify an asset that could carry it.
    That check used to live in `_resolve_foundation_value`, which meant it
    applied only when the Foundation answered for the number: naming a
    generator for a tank state blocked under `SITE_FOUNDATION` and froze
    100 L under `SCENARIO_INPUT`. Same obligation, same disease as R1, one
    position further in.

    Nothing infers a component type from the spelling of a state key, and
    nothing narrows candidates by which of them happens to carry a useful
    property - the two rules the resolver has refused since T020A.
    """
    by_id = {
        component.component_id: component
        for component in site.foundation.components
    }
    # The addresses `_support_for` will be asked about, read from the same
    # function that drives it. A deferral is only legitimate when the address
    # is in here; anything else is a reference nobody checks.
    executable = {
        address for address, _ in _declared_requirements(scenario)
    }
    foundation_detail = (
        f"site {site.site_id} foundation version {site.foundation.version}"
    )
    profile_detail = (
        f"model profile {model.model_profile_id} version "
        f"{model.model_profile_version}"
    )

    def refused(
        ref: StateRef,
        statement: str,
        answered_by: str,
        detail: str,
        kind: str = "STATE_ADDRESS_NOT_RESOLVED",
    ) -> ResolvedAddress:
        return ResolvedAddress(
            authored=ref,
            resolved=None,
            component=None,
            reason=BlockingReason(
                kind=kind, subject=ref.addressed_key, statement=statement
            ),
            answered_by=answered_by,
            detail=detail,
        )

    def settled(
        ref: StateRef,
        resolved: StateRef,
        component: SiteComponent | None,
        detail: str,
        *,
        deferred: bool = False,
    ) -> ResolvedAddress:
        return ResolvedAddress(
            authored=ref,
            resolved=resolved,
            component=component,
            reason=None,
            answered_by="SITE_FOUNDATION",
            detail=detail,
            deferred_to_support=deferred,
        )

    def unmodelled(
        ref: StateRef, where: str, supported: SupportedState | None
    ) -> str:
        if supported is None:
            return (
                f"{where.capitalize()} concerns {ref.state_key}, and "
                f"{profile_detail} does not model that state at all. A "
                "reference this build cannot execute is not something a run "
                "may carry as though it were resolved."
            )
        claimed = (
            "as a fact about the whole installation"
            if ref.scope == "SITE"
            else "as a fact about one component"
        )
        modelled = (
            "a fact about the whole installation"
            if supported.scope == "SITE"
            else "a fact about one component"
        )
        return (
            f"{where.capitalize()} claims {ref.state_key} {claimed} and "
            f"{profile_detail} models it as {modelled}. Those are two "
            "different quantities; address the state the way the profile "
            "models it, or select a profile that models it the way the "
            "scenario claims it."
        )

    resolutions: dict[str, ResolvedAddress] = {}

    for authored, where in declared_state_refs(scenario):
        ref = authored
        supported = model.supported(ref.state_key)
        # The binding applies only when the profile models this state AT THE
        # SCOPE the reference claims it at. A binding read off a state the
        # profile models the other way round would be a component type
        # borrowed from a different claim.
        binding = (
            supported.foundation_binding
            if supported is not None and supported.scope == ref.scope
            else None
        )
        component: SiteComponent | None = None

        # --- Obligation one: the address ---------------------------------
        #
        # A component-scoped reference has to identify one component of this
        # Site. This is NEVER deferred, and that is the correction a backup
        # review produced: the branch below used to hand an unmodelled or
        # differently scoped reference to `_support_for` entire, and
        # `_support_for` does not answer address questions at any requirement
        # level - it blocks on REQUIRED and records on OPTIONAL, both about
        # SUPPORT. So `unmodelled-level` with no selector came back READY
        # with 200 L frozen against no asset whenever it was marked OPTIONAL.
        #
        # A SITE reference makes no component claim, so it has no address
        # obligation to meet - the record refuses it a selector outright.
        if ref.scope == "COMPONENT":
            if ref.component_id is not None:
                component = by_id.get(ref.component_id)
                if component is None:
                    resolutions[authored.addressed_key] = refused(
                        authored,
                        f"{where.capitalize()} concerns {ref.state_key} on "
                        f"component {ref.component_id}, and the foundation "
                        f"of site {site.site_id} declares no component with "
                        "that identity. A named asset is the one this run "
                        "would act on, so nothing falls back to a different "
                        "component.",
                        "SITE_FOUNDATION",
                        (
                            f"{foundation_detail}, which declares no "
                            f"component {ref.component_id}"
                        ),
                    )
                    continue
                if (
                    binding is not None
                    and component.component_type != binding.component_type
                ):
                    resolutions[authored.addressed_key] = refused(
                        authored,
                        f"{where.capitalize()} concerns {ref.state_key} on "
                        f"component {component.component_id}, which the "
                        f"foundation of site {site.site_id} declares as a "
                        f"{component.component_type}, and {profile_detail} "
                        f"carries that state on a {binding.component_type}. "
                        "The named component is the one this run would act "
                        f"on, so nothing looks for a "
                        f"{binding.component_type} elsewhere on the site.",
                        "SITE_FOUNDATION",
                        (
                            f"{foundation_detail}, whose component "
                            f"{component.component_id} is a "
                            f"{component.component_type}"
                        ),
                    )
                    continue
            elif binding is None:
                # Nothing can choose. The profile declares no binding for
                # this state at this scope - because it models it another
                # way, or does not model it at all - so there is no component
                # type to select candidates from, and reading one out of the
                # spelling of a state key is the thing this module refuses.
                resolutions[authored.addressed_key] = refused(
                    authored,
                    f"{where.capitalize()} concerns {ref.state_key} on a "
                    "component and names none, and "
                    f"{profile_detail} declares no binding saying which kind "
                    f"of component carries {ref.state_key} as "
                    "a fact about one component. Nothing reads a component "
                    "type out of the state's name, so this needs either an "
                    "address in the scenario or a profile that declares the "
                    "binding.",
                    "MODEL_PROFILE",
                    f"{profile_detail}, which declares no binding for it",
                )
                continue
            else:
                matches = [
                    candidate
                    for candidate in site.foundation.components
                    if candidate.component_type == binding.component_type
                ]

                if not matches:
                    resolutions[authored.addressed_key] = refused(
                        authored,
                        f"{where.capitalize()} concerns {ref.state_key} on a "
                        f"{binding.component_type} component and names none, "
                        f"and the foundation of site {site.site_id} declares "
                        "no such component. A scenario addressing something "
                        "this site declares would resolve it.",
                        "SITE_FOUNDATION",
                        (
                            f"{foundation_detail}, which declares nothing of "
                            "that type"
                        ),
                    )
                    continue

                if len(matches) > 1:
                    named_ids = sorted(item.component_id for item in matches)
                    resolutions[authored.addressed_key] = refused(
                        authored,
                        f"{where.capitalize()} concerns {ref.state_key} "
                        "without saying which component it is about, "
                        f"{profile_detail} carries that state on a "
                        f"{binding.component_type}, and the foundation of "
                        f"site {site.site_id} declares more than one: "
                        f"{', '.join(named_ids)}. Two assets for one "
                        "reference is not something a run may choose between, "
                        "so the scenario has to name the one it means - for "
                        f"example {ref.state_key}@{named_ids[0]}.",
                        "SITE_FOUNDATION",
                        (
                            f"{foundation_detail}, which declares more than "
                            "one match"
                        ),
                    )
                    continue

                component = matches[0]
                # The resolved reference. The dict stays keyed on the
                # AUTHORED address, because that is what every caller looks
                # a row up by; the resolved one is what the row freezes.
                ref = authored.resolved_to(component.component_id)

        # --- Obligation two: can this build model the state at all? -------
        #
        # Every scope, which is the other half of the same review's finding.
        # The SITE branch used to return before this lookup, so the check
        # added to close bound-only references never ran for a `site:`
        # spelling: `site:unmodelled-volume` as a bound target came back
        # READY with nothing recorded about it.
        #
        # This one IS deferred, and legitimately - `_support_for` says it
        # better, with the requirement level taken into account - but only
        # when `_support_for` is actually asked, which `executable` decides.
        # A bound target it never sees is reported here, in the same
        # vocabulary, so a reader meets one kind of statement wherever the
        # reference was written.
        if supported is None or supported.scope != authored.scope:
            if authored.addressed_key in executable:
                resolutions[authored.addressed_key] = settled(
                    authored, ref, component, profile_detail, deferred=True
                )
            else:
                resolutions[authored.addressed_key] = refused(
                    authored,
                    unmodelled(authored, where, supported),
                    "MODEL_PROFILE",
                    f"{profile_detail}, which does not model it that way",
                    kind="STATE_NOT_SUPPORTED",
                )
            continue

        resolutions[authored.addressed_key] = settled(
            authored,
            ref,
            component,
            (
                foundation_detail
                if component is None
                else f"{foundation_detail}, component {component.component_id}"
            ),
        )

    return resolutions


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
    site: SiteRecord,
    model: ModelProfile,
) -> tuple[RequirementConflict, ...]:
    """Every RESOLVED address and role one document states two requirements for.

    Detection at the grain acceptance criterion 8 names. What the product
    finally DOES about a conflict - refuse the document, block the run, or
    keep taking the stricter answer - is T020B's, and this reports rather
    than decides so that decision has something to act on.
    `_executable_inputs` keeps taking `REQUIRED` meanwhile, which can only
    block a run that would otherwise have run and never the reverse.

    ## Why it takes a Site and a profile

    It took only the scenario and grouped by the AUTHORED address, and an
    independent review showed what that misses. On a site with one tank,
    `example-stored-volume` REQUIRED and `example-stored-volume@north-tank`
    OPTIONAL are two different authored spellings of one asset: setup
    resolves the first to the second, and the two requirements land on the
    same address. Grouped by spelling, the function returned nothing and
    claimed detection at the resolved grain while missing exactly the alias
    that makes resolution necessary. The parser's qualified/unqualified
    refusal does not cover it either - that rule inspects initializing
    parameters, and one of these two does not initialize.

    So it resolves first, through the same pass run setup uses, and groups by
    the address the run would actually act on. A reference that does not
    resolve is grouped by what the author wrote, because there is nothing
    else to group it by and the run is blocked for that reason anyway.

    Two components of one type declared at different requirements are NOT a
    conflict. They are two independent requirements, which is the whole of the
    slice, and reporting them as a disagreement would be the collapse this
    module has just stopped doing.
    """
    addresses = resolve_state_addresses(scenario, site, model)
    stated: dict[tuple[str, str], tuple[StateRef, list[str]]] = {}

    def record(
        state_ref: StateRef | None, role: str, requirement: str | None
    ) -> None:
        if state_ref is None or role not in EXECUTABLE_ROLES:
            return
        if requirement is None:
            return
        address = addresses.get(state_ref.addressed_key)
        resolved = (
            state_ref
            if address is None or address.resolved is None
            else address.resolved
        )
        entry = stated.setdefault(
            (resolved.addressed_key, role), (resolved, [])
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
            # The statement does not name the role, and the reason is
            # deduplicated on `(kind, subject)` below. A state the profile
            # does not model is ONE fact however many roles the scenario
            # uses it in; saying it twice, differing only in which role the
            # prose mentioned, is the repetition `subject` exists to prevent.
            #
            # **The subject is the ADDRESS, not the key.** It was the key
            # until an independent review showed what that costs: two
            # required declarations about two different tanks deduplicated
            # into one row, because their addresses had already been thrown
            # away before `_deduplicated` compared them. One fact per role is
            # the rule; one fact for two assets is a lost declaration. The
            # profile is still ASKED about the semantic key - it models a
            # kind of state and knows nothing about how many a site has -
            # and that is the line: semantic lookup, addressed report.
            return (
                BlockingReason(
                    kind="STATE_NOT_SUPPORTED",
                    subject=executable.addressed_key,
                    statement=statement,
                ),
                None,
            )
        return (
            None,
            UnsupportedOptionalInput(
                state_ref=executable.state_ref,
                execution_role=executable.execution_role,
                statement=statement,
            ),
        )

    if supported.scope != executable.state_ref.scope:
        # A scope disagreement is per DECLARATION, so its subject is the
        # address rather than the state key: a scenario may legitimately
        # address one state correctly and another wrongly, and collapsing
        # both onto the key would report one and hide the other.
        #
        # This is checked here as well as in the Foundation resolver because
        # the two reach different declarations. The resolver sees only the
        # initial values a Foundation owns; a forcing input the scenario owns
        # never goes near it, and without this an entry forcing demand at one
        # feeder against a profile that models one site-wide demand would be
        # reported as supported with the address quietly ignored.
        claimed = (
            "as a fact about the whole installation"
            if executable.state_ref.scope == "SITE"
            else "as a fact about one component"
        )
        modelled = (
            "a fact about the whole installation"
            if supported.scope == "SITE"
            else "a fact about one component"
        )
        statement = (
            f"The scenario declares {executable.state_key} {claimed} and "
            f"model profile {model.model_profile_id} version "
            f"{model.model_profile_version} models it as {modelled}."
        )
        if executable.execution_requirement == "REQUIRED":
            return (
                BlockingReason(
                    kind="STATE_NOT_SUPPORTED",
                    subject=executable.addressed_key,
                    statement=statement,
                ),
                None,
            )
        return (
            None,
            UnsupportedOptionalInput(
                state_ref=executable.state_ref,
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
            # report, and those are two things to fix. It carries the address
            # as well, for the reason the case above does: two assets at one
            # unsupported role are two declarations, not one.
            return (
                BlockingReason(
                    kind="ROLE_NOT_SUPPORTED",
                    subject=(
                        f"{executable.addressed_key} as "
                        f"{executable.execution_role}"
                    ),
                    statement=statement,
                ),
                None,
            )
        return (
            None,
            UnsupportedOptionalInput(
                state_ref=executable.state_ref,
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
