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
from fractions import Fraction
from typing import Callable, Iterable, Sequence

from assetops_backend.runs.identity import allocate_run_id
from assetops_backend.runs.models import (
    ANSWERER_BY_INITIALIZATION_OWNER,
    BlockingReason,
    DeterministicIdentity,
    FrozenCause,
    FrozenDeclaredBound,
    FrozenForcing,
    FrozenInitializationInput,
    FrozenReportingPathCondition,
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
    REPORTING_PATH_STATES,
    FoundationBinding,
    ModelProfile,
    PublicationProfile,
    StateAuthority,
    find_model_profile,
    find_publication_profile,
    resolve_observation_binding,
    resolve_publication_identity,
    state_authority,
)
from assetops_backend.runs.refusals import refuse
from assetops_backend.runs.timezones import (
    TimeZoneDatabaseUnavailable,
    TimeZoneNotFound,
    validate_iana_timezone,
)
from assetops_backend.scenarios.execution import (
    CANONICAL_UNITS,
    EXECUTION_CONTRACT_VERSION,
    RATE_INTEGRALS,
    canonical_quantity,
    frozen_canonical_value,
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
        self._refuse_requirement_conflicts(scenario, site, model, publication)

        parameters = _parameters_by_id(scenario)
        supplied = self._resolve_run_inputs(request, parameters)

        identity, frozen_reasons, addresses = self._freeze(
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
            publication=publication,
            identity=identity,
            addresses=addresses,
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

    def _refuse_requirement_conflicts(
        self,
        scenario: ScenarioDefinition,
        site: SiteRecord,
        model: ModelProfile,
        publication: PublicationProfile,
    ) -> None:
        """Two requirement levels for one resolved address and role refuse.

        On the refusal side of the line, and it is the line's own wording that
        puts it there: a refusal means the request names something that
        "contradicts something else it names". Two answers to whether an input
        must be modelled is exactly that, and it is the shape this project
        already refused as `INITIAL_VALUE_ANSWERS_DISAGREE` before that kind
        lost its producer.

        **The alternative was taking the stricter one, and that is what this
        replaces.** `REQUIRED` won, which sounds conservative and is not: it
        makes an author's mistake into the product's behaviour, and it made the
        lowering this slice exists to do invisible, because a state declared at
        three positions kept whichever position was still `REQUIRED`
        (`D-2026-09-22-forcing-state-requirements`, rider one).

        The same-authored-address case is refused by the scenario parser when
        the document is read, so what reaches here is the alias: two spellings
        that resolve to one address on this Site. That one needs the Site, which
        is why it is decided here and not there.
        """
        conflicts = requirement_conflicts(scenario, site, model, publication)
        if not conflicts:
            return

        # EVERY conflict, not the first. It reported `conflicts[0]`, so an author
        # with two alias conflicts fixed one, resubmitted and met the next. A
        # refusal that knows about three problems and names one charges a round
        # trip per problem, and knowing them all costs nothing here.
        described = "; ".join(
            f"{conflict.addressed_key} as a {conflict.execution_role} at "
            f"{' and '.join(conflict.requirements)}"
            for conflict in conflicts
        )
        counted = (
            "one address and role"
            if len(conflicts) == 1
            else f"{len(conflicts)} addresses and roles"
        )
        raise refuse(
            "EXECUTION_REQUIREMENT_CONFLICT",
            f"Scenario {scenario.scenario_id} states two requirement levels for "
            f"{counted}, against the foundation of site {site.site_id}: "
            f"{described}. Each of those is one address the declarations resolve "
            "to, so the document gives two answers to whether that input must be "
            "modelled. Nothing here picks one: the stricter reading would make "
            "the other declaration have no effect, and the author is the only "
            "one who knows which was meant.",
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
    ) -> tuple[
        DeterministicIdentity,
        tuple[BlockingReason, ...],
        dict[str, ResolvedAddress],
    ]:
        """Freeze everything, and say which values had no answer.

        The reasons come back rather than being raised, because a value the
        selected profile cannot supply blocks the run instead of refusing it,
        and a blocked run is frozen in full.

        Addresses are resolved ONCE here, over the whole document, before any
        value is looked up. Resolving them inside the Foundation lookup is
        what left every scenario-owned and run-owned reference unresolved, so
        the pass runs first and the value lookup consumes its answer.

        The resolutions come back out as well as the identity, because
        `_decide` needs them: an address this pass refused is not asked the
        support question a second time.
        """
        addresses = resolve_state_addresses(scenario, site, model, publication)

        initialization, unresolved = self._freeze_initialization(
            scenario=scenario,
            site=site,
            model=model,
            publication=publication,
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

        causes, forcings, declared, reporting = _freeze_causal_projection(
            scenario=scenario,
            parameters=parameters,
            supplied=supplied,
            addresses=addresses,
            initialization=initialization,
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
            causes=causes,
            forcings=forcings,
            declared_bounds=declared,
            reporting_path_conditions=reporting,
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
        ), unresolved, addresses

    def _freeze_initialization(
        self,
        *,
        scenario: ScenarioDefinition,
        site: SiteRecord,
        model: ModelProfile,
        publication: PublicationProfile,
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
                    publication=publication,
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

            # Through the same checked boundary as the causal projection. The
            # reported defect was a rate normalized twice; the same conversion
            # was here unchecked, so an initial value in a unit with a non-unit
            # factor could freeze a number the frozen float cannot carry. Fixing
            # the reported instance and not the class is how the class comes
            # back somewhere else.
            canonical_value = (
                None
                if value is None
                else frozen_canonical_value(value, initial.unit)[0]
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
        publication: PublicationProfile,
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
        # The same authority the address pass and `_support_for` ask. This
        # function's docstring stated the scope-before-binding order first and
        # was the only one of the three that followed it; asking through one
        # record is what stops that being a fact about which function a reader
        # happened to open.
        authority = state_authority(state_ref.state_key, model, publication)
        profile_detail = authority.detail
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

        supported = authority.supported

        # Scope before binding, because a scope disagreement explains a
        # missing binding rather than the other way round: a site-wide state
        # has no binding BY CONSTRUCTION, so reporting "no binding declared"
        # for it would name the symptom and hide the cause.
        if supported is not None and supported.scope != state_ref.scope:
            return blocked(
                scope_disagreement_statement(
                    state_ref, authority, subject="The scenario"
                ),
                authority.answerer,
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
                "declares the binding is what this run needs."
                + (
                    " A publication profile never declares one: it cannot see "
                    "a foundation, so a reporting-path state has no "
                    "foundation-owned initial value at all."
                    if authority.is_reporting_path
                    else ""
                ),
                authority.answerer,
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
        publication: PublicationProfile,
        identity: DeterministicIdentity,
        addresses: dict[str, ResolvedAddress],
        frozen_reasons: tuple[BlockingReason, ...] = (),
    ) -> tuple[tuple[BlockingReason, ...], tuple[UnsupportedOptionalInput, ...]]:
        reasons: list[BlockingReason] = []
        optional: list[UnsupportedOptionalInput] = []

        for executable in _executable_inputs(scenario):
            # An address the resolution pass already refused is not asked the
            # support question, and this is the second half of F5. The two
            # obligations are genuinely independent and a declaration can fail
            # both - but a reference that names no asset has nothing for a
            # profile to be asked ABOUT, and a reader met two blocking rows
            # with the same subject where the second added no repair the first
            # did not already state. The address reason is the one that has to
            # be fixed first: nothing about resolving it depends on the
            # requirement level, while the support answer does.
            #
            # Nothing is lost by the run's outcome either way. The address
            # obligation is not requirement-sensitive, so such a run is
            # BLOCKED on the address reason whether or not a support reason
            # sits beside it.
            address = addresses.get(executable.addressed_key)
            if address is not None and address.reason is not None:
                continue

            reason, unsupported = _support_for(executable, model, publication)
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


def _freeze_causal_projection(
    *,
    scenario: ScenarioDefinition,
    parameters: dict[str, ScenarioParameter],
    supplied: dict[str, float],
    addresses: dict[str, ResolvedAddress],
    initialization: tuple[FrozenInitializationInput, ...],
) -> tuple[
    tuple[FrozenCause, ...],
    tuple[FrozenForcing, ...],
    tuple[FrozenDeclaredBound, ...],
    tuple[FrozenReportingPathCondition, ...],
]:
    """Freeze what the document says happens, when, and to which asset.

    Run setup is the component entitled to hold a document and a resolved Site
    together, so it is the component that can freeze a causal projection. Before
    T021's independent review this projection was built by the host adapter from
    whatever definition a caller handed it, and the reviewer reproduced what that
    allows: the same persisted run, the same scenario version, one offset moved on
    the live document, and a different trajectory.

    Three things this deliberately does NOT do.

    It does not apportion. A window's quantity is frozen whole and how much of it
    has moved part way through is the execution contract's ramp - a partial answer
    frozen here would put a transition rule in a record.

    It does not decide what is executable. A reference that did not resolve is
    frozen at its authored address, exactly as `_freeze_initialization` freezes an
    absent value, because the blocking reason beside it is what says the run may
    not run. Freezing nothing would make a blocked Draft unable to show what it
    was going to do.

    It does not read a profile. Which states a build can model is the support
    question and it is asked elsewhere; this records the document's declarations
    against the Site's components, and the kernel cross-references the run's own
    unsupported-optional rows.
    """
    initial_by_parameter = {item.parameter_id: item for item in initialization}

    def frozen_ref(reference: StateRef) -> StateRef:
        resolution = addresses.get(reference.addressed_key)
        if resolution is None:
            return reference
        return resolution.resolved or resolution.authored

    def authored_number(parameter: ScenarioParameter) -> float | None:
        """The number this run froze for a parameter, from either carrier.

        A parameter that initializes a state is frozen as an initialization
        input; every other one is frozen as a resolved parameter. Reading only
        one of the two is R4: a timeline entry whose effect names a parameter
        that also initializes lost its cause entirely, and the removal simply
        stopped happening.
        """
        frozen_initial = initial_by_parameter.get(parameter.parameter_id)
        if frozen_initial is not None:
            return frozen_initial.value
        if parameter.parameter_id in supplied:
            return supplied[parameter.parameter_id]
        return parameter.value if isinstance(parameter.value, float) else None

    causes: list[FrozenCause] = []
    forcings: list[FrozenForcing] = []
    declared: list[FrozenDeclaredBound] = []
    reporting: list[FrozenReportingPathCondition] = []

    for entry in scenario.timeline:
        if entry.state_ref is None:
            continue

        if entry.state_ref.state_key in REPORTING_PATH_STATES:
            reporting.append(
                FrozenReportingPathCondition(
                    event_id=entry.event_id,
                    state_ref=frozen_ref(entry.state_ref),
                    timing_shape=entry.timing.shape,
                    offset_minutes=entry.offset_minutes,
                    duration_minutes=entry.timing.duration_minutes,
                )
            )
            continue

        effect = entry.state_effect
        if effect is not None:
            source_id = (
                effect.quantity_parameter_id or effect.rate_parameter_id
            )
            parameter = (
                parameters.get(source_id) if source_id is not None else None
            )
            if parameter is None or parameter.unit is None:
                raise UnresolvedCausalProjection(
                    f"timeline entry {entry.event_id!r} declares a state "
                    f"effect naming {source_id!r}, which is not a parameter "
                    "this document declares with a unit. A declared effect "
                    "whose magnitude cannot be found is refused rather than "
                    "frozen as silence."
                )
            number = authored_number(parameter)
            # Absent, not raised. The reachable case is a `MODEL_RULE` magnitude
            # the selected profile declares no rule for, and the product has
            # always BLOCKED such a run - a different profile may answer. Raising
            # here turned that into an HTTP 500 with nothing written.
            if number is None:
                canonical_value = None
                _, canonical_unit, dimension = canonical_quantity(
                    0.0, parameter.unit
                )
                if effect.rate_parameter_id is not None:
                    dimension = RATE_INTEGRALS[dimension]
                    canonical_unit = CANONICAL_UNITS[
                        _canonical_unit_for(dimension)
                    ].canonical_unit
            else:
                # One conversion and one normalization, in exact arithmetic, with
                # the rate's integration done INSIDE it. Doing the multiplication
                # after a float round trip normalized twice and turned a
                # millionth of a litre an hour into zero.
                across = (
                    Fraction(entry.timing.duration_minutes or 0)
                    if effect.rate_parameter_id is not None
                    else Fraction(1)
                )
                canonical_value, canonical_unit, dimension = (
                    frozen_canonical_value(number, parameter.unit, times=across)
                )
                if effect.rate_parameter_id is not None:
                    dimension = RATE_INTEGRALS[dimension]
                    canonical_unit = CANONICAL_UNITS[
                        _canonical_unit_for(dimension)
                    ].canonical_unit
            causes.append(
                FrozenCause(
                    event_id=entry.event_id,
                    state_ref=frozen_ref(entry.state_ref),
                    direction=effect.direction,
                    parameter_id=parameter.parameter_id,
                    canonical_value=canonical_value,
                    canonical_unit=canonical_unit,
                    dimension=dimension,
                    timing_shape=entry.timing.shape,
                    offset_minutes=entry.offset_minutes,
                    duration_minutes=entry.timing.duration_minutes,
                )
            )

        if entry.execution_role != "FORCING_INPUT":
            continue
        for parameter in entry.parameters:
            if parameter.execution_role != "FORCING_INPUT":
                continue
            if parameter.state_ref is None or parameter.unit is None:
                continue
            number = authored_number(parameter)
            if number is None:
                canonical_value = None
                _, canonical_unit, dimension = canonical_quantity(
                    0.0, parameter.unit
                )
            else:
                canonical_value, canonical_unit, dimension = (
                    frozen_canonical_value(number, parameter.unit)
                )
            forcings.append(
                FrozenForcing(
                    event_id=entry.event_id,
                    state_ref=frozen_ref(parameter.state_ref),
                    parameter_id=parameter.parameter_id,
                    canonical_value=canonical_value,
                    canonical_unit=canonical_unit,
                    dimension=dimension,
                    timing_shape=entry.timing.shape,
                    offset_minutes=entry.offset_minutes,
                    duration_minutes=entry.timing.duration_minutes,
                    execution_requirement=parameter.execution_requirement,
                )
            )

    for parameter in parameters.values():
        bound = parameter.bounds
        if bound is None or parameter.state_ref is None:
            continue
        declared.append(
            FrozenDeclaredBound(
                state_ref=frozen_ref(bound.state_ref),
                bound_kind=bound.bound_kind,
                source_state_ref=frozen_ref(parameter.state_ref),
                source_parameter_id=parameter.parameter_id,
            )
        )

    return tuple(causes), tuple(forcings), tuple(declared), tuple(reporting)


def _canonical_unit_for(dimension: str) -> str:
    """The authored unit whose canonical form represents a dimension."""
    for unit, canonical in CANONICAL_UNITS.items():
        if canonical.dimension == dimension and canonical.numerator == 1:
            return unit
    raise KeyError(dimension)


class UnresolvedCausalProjection(Exception):
    """A state effect names something that is not a parameter with a unit.

    Defensive, and unreachable through the scenario parser:
    `_validate_entry_state_effect` already refuses an effect naming no declared
    parameter, one whose role is not `CAUSAL_INPUT`, one addressing another state,
    and one with no unit. It is kept because this projection is the first thing to
    consume that guarantee, and a projection that assumed it silently would be a
    projection with nothing to say when the assumption stopped holding.

    A magnitude nobody ANSWERED is not this: that is frozen absent with the
    blocking reason beside it, which is what the product has always done with an
    unanswered value and what `SimulationRun` enforces.
    """


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

    **Nothing here resolves a disagreement about the requirement.** `REQUIRED`
    used to win, and that rule is retired: it made lowering a requirement
    unobservable wherever a state was declared in more than one position, which
    is every state this slice had to lower
    (`D-2026-09-22-forcing-state-requirements`). A document that disagrees with
    itself is refused before this runs, and `_declared_requirements` raises
    rather than choosing if one ever reaches it.
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


def _claim_words(scope: str) -> str:
    return (
        "a fact about the whole installation"
        if scope == "SITE"
        else "a fact about one component"
    )


def scope_repair(ref: StateRef, authority: StateAuthority) -> str:
    """The one thing an author types to settle a scope disagreement.

    Two possible strings, decided by the two scopes, and it exists because
    every message this project had for a scope disagreement offered "address
    the state the way the profile models it" - a restatement of the diagnosis
    rather than a repair. F5 is that gap: the author who met it was told to add
    a binding or an address, and the fix was four characters of prefix.
    """
    assert authority.scope is not None
    if authority.scope == "SITE":
        return f"write site:{ref.state_key} to claim it site-wide"
    return (
        f"write {ref.state_key}@<component-id> to claim it on the component "
        "that carries it"
    )


def scope_disagreement_statement(
    ref: StateRef, authority: StateAuthority, *, subject: str
) -> str:
    """One statement for a scope disagreement, and the repair it needs.

    Written once, for two reasons, and F5 is both of them.

    **The wording was duplicated three times** - in the address pass, in
    `_support_for` and in `_resolve_foundation_value` - and each copy had its
    own hedges. A reader who met two of them met two accounts of one fact.

    **None of the three said what to do about it.** They said the scenario
    claims the state one way and the profile models it the other, which is the
    diagnosis, and then offered "address the state the way the profile models
    it" - true, and not a repair anybody can type. The repair is one of exactly
    two strings, and which one is decided by the two scopes, so it is computed
    here rather than left to the author to infer.

    `subject` is how the declaration is introduced, so the same statement works
    for "Entry 'overcast-day'" and for "The scenario".
    """
    repair = scope_repair(ref, authority)
    return (
        f"{subject} claims {ref.state_key} as {_claim_words(ref.scope)} and "
        f"{authority.detail} models it as {_claim_words(authority.scope)}. "
        f"Those are two different quantities, so nothing answers for both: "
        f"{repair}, or select a profile that models it the way the scenario "
        "claims it."
    )


def state_not_modelled_statement(
    ref: StateRef,
    authority: StateAuthority,
    *,
    subject: str,
    requirement: str | None = None,
) -> str:
    """One statement for a state the answering profile does not model at all.

    It names the profile whose job it was, which is the whole value of deciding
    the authority by the state rather than by who answers first. A scenario
    forcing the reporting path against a publication profile that does not
    declare that capability used to be told the MODEL profile did not model it,
    and a reader following that was widening the wrong profile.

    ## Why the consequence is a separate clause

    T020B's independent review found the closing clause false on the screen this
    slice exists to make honest. One sentence served both of `_support_for`'s
    answers, and it ended "which this scenario needs it to" - true of a REQUIRED
    input, and false of an OPTIONAL one. So a READY run's "Optional inputs this
    profile does not support" panel said the scenario needed something it had
    just declared it could do without, which contradicts the argument the
    lowering rests on.

    The fact and its consequence are two things, so they are two clauses. The
    fact is the same however the input is declared: this profile does not model
    this state. What follows from it is exactly what the requirement level
    decides, which is why the level is an argument here rather than something
    the caller pastes on afterwards.

    `requirement` is `None` for the address pass, which is deliberately
    requirement-INSENSITIVE - a reference that names no asset blocks whatever
    its level - and which appends its own closing sentence.
    """
    if authority.is_reporting_path:
        fact = (
            f"{subject} forces {ref.state_key}, which is a condition on the "
            f"reporting path rather than on the world, and {authority.detail} "
            "does not declare that it can model the reporting path being in "
            "that condition. A model profile cannot answer for this: whether a "
            "signal is carrying readings is a property of the path, so the "
            "publication profile is the one to change or to reselect."
        )
    else:
        fact = (
            f"{subject} concerns {ref.state_key}, and {authority.detail} does "
            "not model that state at all."
        )

    if requirement == "REQUIRED":
        return f"{fact} This scenario requires it, so the run is blocked."
    if requirement == "OPTIONAL":
        return (
            f"{fact} This scenario declares it optional, so the run proceeds "
            "without it and the gap is recorded here rather than blocking. "
            "Nothing about this run models it."
        )
    return fact


def resolve_state_addresses(
    scenario: ScenarioDefinition,
    site: SiteRecord,
    model: ModelProfile,
    publication: PublicationProfile,
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

    **And scope before "no binding", which is F5.** An unqualified reference to
    a state the answering profile models SITE-WIDE used to reach the no-binding
    refusal, because a binding is only read when the scopes agree and a
    site-wide state has no binding by construction. The statement told the
    author to add an address or select a profile that declares the binding, and
    the actual repair is to write `site:` in front of the key, which it never
    said. `_resolve_foundation_value` already ordered these two correctly and
    said so in its docstring, so the two functions contradicted each other.
    The scope check now runs first here too, and the statement both share names
    the repair.

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
        ref: StateRef, where: str, authority: StateAuthority
    ) -> str:
        if not authority.models_it:
            return (
                state_not_modelled_statement(
                    ref, authority, subject=where.capitalize()
                )
                + " A reference this build cannot execute is not something a "
                "run may carry as though it were resolved."
            )
        return scope_disagreement_statement(
            ref, authority, subject=where.capitalize()
        )

    resolutions: dict[str, ResolvedAddress] = {}

    for authored, where in declared_state_refs(scenario):
        ref = authored
        # Asked of whichever profile answers for this state, which the state
        # decides. `_support_for` asks the same function, so the two cannot
        # consult different profiles or order the same two facts differently.
        authority = state_authority(ref.state_key, model, publication)
        profile_detail = authority.detail
        supported = authority.supported
        # The binding applies only when the profile models this state AT THE
        # SCOPE the reference claims it at. A binding read off a state the
        # profile models the other way round would be a component type
        # borrowed from a different claim.
        binding = (
            authority.foundation_binding
            if authority.scope == ref.scope
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
            elif authority.models_it and authority.scope != ref.scope:
                # F5. The scopes disagree, so `binding` is None for a reason
                # that has nothing to do with the profile being incomplete:
                # the profile models this state site-wide and a site-wide
                # state has no binding BY CONSTRUCTION. Reporting "no binding
                # declared" here names the symptom and hides the cause, and
                # the repair it offered - add an address, or find a profile
                # that declares the binding - is not the repair. The repair is
                # to write `site:` in front of the key, and the shared
                # statement says so.
                #
                # Ordered this way in `_resolve_foundation_value` since T020A1
                # and stated in its docstring; this is the function that
                # contradicted it.
                resolutions[authored.addressed_key] = refused(
                    authored,
                    f"{where.capitalize()} concerns {ref.state_key} on a "
                    f"component and names none, and {profile_detail} models "
                    f"{ref.state_key} as {_claim_words(authority.scope)}. "
                    "There is no kind of component for a selector to be "
                    "resolved against, so this reference names no asset: "
                    f"{scope_repair(ref, authority)}, or select a profile that "
                    "models it the way the scenario claims it and name the "
                    "component you mean.",
                    authority.answerer,
                    f"{profile_detail}, which models this state at another "
                    "scope",
                )
                continue
            elif binding is None:
                # Nothing can choose, and now this branch means one thing: the
                # answering profile does not model this state at all, so there
                # is no component type to select candidates from. Reading one
                # out of the spelling of a state key is what this module
                # refuses.
                #
                # A reporting-path state reaches here too, and legitimately: a
                # publication profile can never declare a binding, because it
                # cannot see a Foundation. So the repair for one of those is
                # always to name the component in the scenario.
                repair = (
                    "so the scenario has to name the component it means"
                    if authority.is_reporting_path
                    else (
                        "so this needs either an address in the scenario or a "
                        "profile that declares the binding"
                    )
                )
                resolutions[authored.addressed_key] = refused(
                    authored,
                    f"{where.capitalize()} concerns {ref.state_key} on a "
                    "component and names none, and "
                    f"{profile_detail} declares no binding saying which kind "
                    f"of component carries {ref.state_key} as "
                    f"a fact about one component. Nothing reads a component "
                    f"type out of the state's name, {repair}.",
                    authority.answerer,
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
                    unmodelled(authored, where, authority),
                    authority.answerer,
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


class UnresolvedRequirementConflict(Exception):
    """Two requirement levels for one authored `(address, role)` reached setup.

    Not a refusal and not a blocking reason, because it is neither: it is the
    scenario parser's rule having failed to hold. A document with two
    requirement levels for one authored address and role is refused when it is
    read (`_validate_execution_requirements`), so by the time run setup gathers
    executable inputs the disagreement cannot exist.

    It is an exception rather than a comment saying so. The rule this replaces
    was `REQUIRED` wins - invented by T019, retired by
    `D-2026-09-22-forcing-state-requirements` - and the reason it had to be
    retired rather than left as a harmless fallback is that it was the thing
    making the lowering unobservable: `site-load-demand` is declared at three
    positions, and under the collapse lowering one of them changed nothing.
    A silent resolution here would restore exactly that, so there is nothing
    silent here to restore it.
    """


def _declared_requirements(
    scenario: ScenarioDefinition,
) -> dict[tuple[str, str], tuple[StateRef, str]]:
    """Every `(address, role)` the scenario declares, and its requirement.

    One requirement per pair, never a resolution of two. See
    `UnresolvedRequirementConflict` for why the collapse that used to be here
    is gone rather than kept as a fallback.
    """
    found: dict[tuple[str, str], tuple[StateRef, str]] = {}

    def record(
        state_ref: StateRef | None, role: str, requirement: str | None
    ) -> None:
        if state_ref is None or role not in EXECUTABLE_ROLES:
            return
        key = (state_ref.addressed_key, role)
        # An executable declaration always carries a requirement: the scenario
        # parser requires one for every executable role and refuses one on a
        # non-executable condition. `or "REQUIRED"` used to stand here and was
        # a default for a case that cannot arise, which is the shape that hides
        # the next one.
        if requirement is None:
            raise UnresolvedRequirementConflict(
                f"{state_ref.addressed_key} is declared as a {role} with no "
                "execution requirement. An executable declaration carries one "
                "or the scenario parser refuses the document, so nothing here "
                "supplies a level on its behalf."
            )
        current = found.get(key)
        if current is not None and current[1] != requirement:
            raise UnresolvedRequirementConflict(
                f"{state_ref.addressed_key} is declared as a {role} at both "
                f"{current[1]} and {requirement}. The scenario parser refuses "
                "a document that does this, so reaching run setup means that "
                "rule did not run. Nothing here picks the stricter level: "
                "picking one is how an author's mistake becomes the product's "
                "behaviour."
            )
        found[key] = (state_ref, requirement)

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
    publication: PublicationProfile,
) -> tuple[RequirementConflict, ...]:
    """Every RESOLVED address and role one document states two requirements for.

    ## What happens to what it finds, since T020B

    It is refused. `create_draft_run` calls this before it freezes anything and
    raises `EXECUTION_REQUIREMENT_CONFLICT` if it returns a row, so no `run_id`
    is allocated and nothing is written
    (`D-2026-09-22-forcing-state-requirements`, rider one). T020A1 left this
    function reporting rather than deciding and said T020B owned the decision;
    this is the decision.

    **Two layers, because there are two grains and only one of them needs a
    Site.** Two requirement levels on ONE AUTHORED address are a property of
    the document alone, so the scenario parser refuses that when it reads it,
    and such a document never reaches a run. What is left for this function is
    the ALIAS: two different authored spellings that resolve to one address,
    which cannot be seen without the Site that resolves them. Both refuse; they
    refuse at the earliest moment each becomes decidable.

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
    addresses = resolve_state_addresses(scenario, site, model, publication)
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
    executable: ExecutableInput,
    model: ModelProfile,
    publication: PublicationProfile,
) -> tuple[BlockingReason | None, UnsupportedOptionalInput | None]:
    """Ask the answering profile about one executable input.

    Required and unsupported blocks; optional and unsupported is recorded.
    There is no third answer, because `EXECUTION_REQUIREMENTS` has no third
    value and "supported if convenient" is how an input gets ignored.

    **Which profile is asked is decided by the state**, through
    `state_authority`, and the two profiles' state sets cannot overlap. So a
    reporting-path condition is answered by the publication profile whether or
    not that profile declares it, and the reason a reader is sent to names the
    profile whose job it was. Before T020B the model profile answered for
    everything, and a scenario forcing the reporting path was told the model
    profile did not model it - sending a reader to widen a kernel over
    something no kernel does.
    """
    authority = state_authority(executable.state_key, model, publication)
    supported = authority.supported

    if supported is None:
        # The requirement level is passed, not pasted on by the caller. This
        # function answers for BOTH of the two outcomes below, so a statement
        # that did not know the level could only be right about one of them -
        # and it was wrong about the optional one, on the screen that argues
        # the lowering is honest.
        statement = state_not_modelled_statement(
            executable.state_ref,
            authority,
            subject="The scenario",
            requirement=executable.execution_requirement,
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
        statement = scope_disagreement_statement(
            executable.state_ref, authority, subject="The scenario"
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
            f"{authority.detail.capitalize()} models "
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
