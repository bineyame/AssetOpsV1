"""Versioned model and publication profiles, and what they resolve.

A profile is versioned simulator configuration. It is not authored scenario
content and it is not Site configuration: it says what a simulator build can
model and how a simulated site publishes, which is the same for every scenario
and every Site that build runs.

Two profiles, selected separately by run setup, because they answer two
different questions:

- a **model profile** says which private world states this simulator can
  model, and in which execution roles. `EXECUTION_REQUIREMENTS` gives an input
  two values and no third, so a required input this profile does not support
  blocks the run and an optional one is recorded as unsupported. There is no
  "supported if convenient", which is how an input gets ignored.
- a **publication profile** says at what cadence a device signal reports, which
  simulator source and which gateway a run would publish through, and - since
  T022 - which configured device signals report which world state, with what
  error and with what reliability. That last one is what the observation
  transform consumes, and it is here because the publication profile owns
  reporting behaviour: a Foundation says a signal CAN report and declares its
  unit, and declares no rate, no bias and no dropout.

## Why this module may not see a Site

`D-2026-09-21-scenario-execution-contract` settles that Foundation declares
that a signal CAN report and declares no rate, and that nothing derives a
cadence from a device's name, from displayed text, or from the spacing between
authored rows. T019 carries the same rule for the two publication identities:
they come from the selected profile or the run is `BLOCKED`.

The rule is structural here rather than remembered. This module imports
nothing from `assetops_backend.sites`, the three resolver functions below take
only a profile and the scenario's own declared source, and
`tools/checks/run-setup.ps1` fails the build if a `FrozenObservationBinding` or
a `FrozenPublicationIdentity` is constructed anywhere else in the product. A
Site fact cannot reach a cadence, because it cannot reach this module and
nothing outside it may build the record a cadence lives in.

## What the shipped profiles say, and what they deliberately do not

`MINIMAL_FUEL_TANK_MODEL` is the profile the first causal kernel will
implement. It models the fuel tank, the generator's own consumption
coefficient and the output the scenario forces on it, and nothing else - which
is the truth about this build. The shipped Fuel Loss Event also declares site
demand and plane-of-array irradiance, and this profile supports neither.

What changed in T020B is what that costs, and it is worth being exact because
the cost used to be a blocked run. Those two states are now declared
`OPTIONAL` in that document, because producing the fuel trajectory does not
need either - the dispatch is declared directly, so nothing computes it from
load and PV (`D-2026-09-22-forcing-state-requirements`). An `OPTIONAL` state
this profile does not model is RECORDED on the run as an unsupported optional
input, named on the run's own screen, and does not block it. Widening the
profile to model them is T024's work, and it widens by modelling a state
rather than by declaring that it does.

The third state that used to block that document was never this profile's to
answer. Whether the fuel level sensor is reporting is a fact about the
reporting path, so `REPORTING_PATH_STATES` names it and the publication
profile declares whether it can be modelled. A model profile that claimed it
is refused.
"""

from __future__ import annotations

from dataclasses import dataclass

from assetops_backend.runs.models import (
    FrozenObservationBinding,
    FrozenPublicationIdentity,
)
from assetops_backend.scenarios.models import ObservationSource
from assetops_backend.state_refs import STATE_SCOPES
from assetops_contracts.observation import REPORTABLE_READING_CLASSES


@dataclass(frozen=True)
class FoundationBinding:
    """How a Foundation-owned initial world value is found in a Foundation.

    The scenario says the Foundation owns a value; this says which declared
    fact answers for it. Declared rather than guessed: nothing matches a state
    key against a component identity by spelling, for the same reason T018's
    review made a bound a declaration rather than a shared prefix.

    Three fields since T020A, and the middle one is the slice. It used to name
    a component type and a RATING unit, which can address exactly one fact per
    component: a generator has one rating, so a profile needing both its
    specific fuel consumption and its minimum runtime had nothing to say which
    it meant. `property_key` names the typed property, so the binding aims at a
    named fact rather than at whatever the component happened to be rated in.

    That is also why a Foundation declaring no such property BLOCKS rather than
    refusing (`D-2026-09-22-foundation-property-absent-blocks`): the property
    name is as much this profile's aim as the component type is, and a
    different profile naming a different property may well find something the
    same Foundation does declare.

    This module names three strings and reads no Foundation. Resolving the
    binding against a Site is the run setup service's job, which is the same
    parser/service split the target-site declaration uses - and it is enforced,
    because `tools/checks/run-setup.ps1` forbids this module from importing the
    Site record family at all.

    ## Still three strings after T020A1, and deliberately no fourth

    Addressing did not add a component id here. A binding says WHAT KIND of
    declared fact answers - a `FUEL_TANK`'s `tank-capacity`, in litres - and
    the scenario says WHICH ONE, because the scenario is the thing that knows
    the installation it targets. A component id in a profile would make the
    profile a fixture: the same simulator build could not be selected for a
    second Site without being edited, which is what acceptance criterion 3
    asks not to happen. What addressing did add is one field on
    `SupportedState`, at the same grain: a kind of claim, never an instance.
    """

    component_type: str
    property_key: str
    unit: str


@dataclass(frozen=True)
class SupportedState:
    """One private world state a model profile can model, and how.

    `supported_roles` is the set of execution roles this profile can consume
    for this state. A state it can cause but not report is a real and common
    case - a kernel can move a tank level long before anything publishes a
    reading of it - so the two are separate rather than one flag.

    ## `scope` is a fourth field since T020A1, and it names no fixture

    It says whether this state is a fact about ONE COMPONENT or about the
    installation. Stored fuel volume is a component's; plane-of-array
    irradiance is the site's. That is a property of the state the simulator
    models, not of any installation, which is why it is declared here and why
    it can be declared without naming a single component id - the point of
    acceptance criterion 3. Select this same profile for a different Site and
    it addresses that Site's components.

    A scenario declares the scope too, on each reference, and run setup blocks
    when they disagree. Two declarations of one fact sounds like a place for
    them to drift, and the disagreement is the substance: the scenario says
    which instance it means and the profile says whether instances are a thing
    this state has. A scenario addressing site-wide irradiance at one PV array
    has asked for something the model does not carry, and saying so is more
    use than quietly answering the question it did not ask.

    A `SITE` state has no `foundation_binding`, refused below rather than
    remembered. A binding names a component type and a property on it, which
    is a component-scoped answer by construction; hanging one on a site-wide
    state would be a declaration that could never resolve.
    """

    state_key: str
    scope: str
    supported_roles: frozenset[str]
    foundation_binding: FoundationBinding | None
    statement: str
    #: T024. The kind of component a COMPONENT state with no Foundation
    #: binding is carried on - a load's demand is a fact about a LOAD. Without
    #: it an explicitly addressed reference could name any component at all,
    #: because the binding's component type was the only type check there was.
    #: A state with a binding reads its type from the binding instead.
    component_type: str | None = None

    def __post_init__(self) -> None:
        if self.component_type is not None and (
            self.scope != "COMPONENT" or self.foundation_binding is not None
        ):
            raise ValueError(
                f"Model profile state {self.state_key!r} declares a carrier "
                "component type and is either site-wide or already bound. A "
                "bound state's carrier is its binding's type, and a site-wide "
                "state has no carrier."
            )
        if self.scope not in STATE_SCOPES:
            raise ValueError(
                f"Model profile state {self.state_key!r} is claimed at "
                f"{self.scope!r}, and a world state is claimed at one of "
                f"{sorted(STATE_SCOPES)}."
            )
        if self.scope == "SITE" and self.foundation_binding is not None:
            raise ValueError(
                f"Model profile state {self.state_key!r} is site-wide and "
                "carries a foundation binding, which names a component type "
                "and a property on it. A site-wide state has no component for "
                "such a binding to find, so the declaration could never "
                "resolve."
            )


#: States that are facts about the REPORTING PATH rather than about the world.
#:
#: Whether the fuel level sensor is reporting is not a property of the fuel. It
#: changes nothing about how much is in the tank, it carries no state effect,
#: and no kernel that models a tank is any nearer to modelling it. What it is a
#: property of is the path a reading travels, and the publication profile is
#: the thing that declares that path
#: (`D-2026-09-22-forcing-state-requirements`).
#:
#: A closed vocabulary rather than a naming convention, for the reason every
#: other vocabulary in this product is closed: the alternative is deciding
#: which profile answers by looking for `reporting` in a state key, and a rule
#: that reads authority out of a spelling is a rule an author can move by
#: renaming something.
#:
#: One member today, which is the honest size of it. The build knows one
#: reporting-path state because the shipped scenario declares one.
REPORTING_PATH_STATES = frozenset({"fuel-level-reporting-availability"})


@dataclass(frozen=True)
class SupportedReportingState:
    """One reporting-path state a publication profile can model, and how.

    The same shape as `SupportedState` minus the one field it must not have. A
    publication profile cannot read a Foundation - this module may not import
    the Site record family at all - so there is no position here for a binding,
    and `foundation_binding` is a property returning `None` rather than a field
    somebody could set. Both records answer the same two questions, at the same
    scope grain and about the same roles, which is what lets one caller ask
    either of them without knowing which it holds.

    `state_key` must be in `REPORTING_PATH_STATES`. That is the half of the
    authority split this record enforces: a publication profile cannot claim to
    model a state of the world by declaring it here.

    ## `silences` is new in T022, and it is the declaration nothing else could make

    A scenario forces `fuel-level-reporting-availability@fuel-tank` and the
    observation transform has to know WHICH configured signals stop publishing.
    Nothing derivable answers that. The component is not enough - a second sensor
    on the same tank is a second path, and cutting one says nothing about the
    other - and the state key is not enough either, because two tanks have two
    paths. So the profile that declares both the reporting-path capability and the
    device signals declares the link between them, and
    `PublicationProfile.__post_init__` refuses a name that is not one of its own
    declared signals.

    Empty is a real answer and has a consequence worth stating: a reporting-path
    state this profile can model but that silences nothing would be a capability
    with no effect, so a run forcing it would complete with every reading intact.
    """

    state_key: str
    scope: str
    supported_roles: frozenset[str]
    statement: str
    silences: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.scope not in STATE_SCOPES:
            raise ValueError(
                f"Publication profile state {self.state_key!r} is claimed at "
                f"{self.scope!r}, and a state is claimed at one of "
                f"{sorted(STATE_SCOPES)}."
            )
        if self.state_key not in REPORTING_PATH_STATES:
            raise ValueError(
                f"Publication profile state {self.state_key!r} is not a "
                "reporting-path state. A publication profile declares what it "
                "can model about the path a reading travels; a state of the "
                f"world belongs to a model profile. The reporting-path states "
                f"are {sorted(REPORTING_PATH_STATES)}."
            )

    #: A reporting-path state is carried on whatever component the scenario
    #: names; no carrier type is declared for it.
    component_type = None

    @property
    def foundation_binding(self) -> None:
        """Always absent, and absent by construction rather than by value.

        A binding names a component type and a property on it, which is a
        Foundation fact. This module cannot see a Foundation, so a publication
        profile has nothing to declare one from.
        """
        return None


@dataclass(frozen=True)
class DiscreteStateDeclaration:
    """T025a. A discrete state a model profile carries, as run setup checks it.

    The product half of the simulator's `DiscreteStateSpec`: the closed set of
    members, which of them a run may start from, and why the others may not.
    A conformance test holds the two halves equal.
    """

    state_key: str
    allowed_values: tuple[str, ...]
    initial_values_supported: frozenset[str]
    unsupported_initial_reason: str


@dataclass(frozen=True)
class ModelProfile:
    """One versioned simulator model, and what it can model.

    It may not declare a reporting-path state, refused below rather than
    remembered. That is the other half of the authority split: exactly one
    profile answers "can this build model this state", and which one is decided
    by the state rather than by which profile was asked first. Two profiles
    both claiming a state would be two answers to one question, and the
    interesting case is not the disagreement - it is the silent agreement that
    hides which one a run actually consulted.
    """

    model_profile_id: str
    model_profile_version: int
    display_name: str
    statement: str
    supported_states: tuple[SupportedState, ...]
    #: T024, Option C (`D-2026-09-29-t024-option-c-and-reserve-override`).
    #: The Foundation values this model's laws need whether or not a scenario
    #: asks for them: each names a supported state whose binding says which
    #: property of which component type answers. Run setup resolves every
    #: component of that type and freezes each answer with its provenance in
    #: the run's deterministic identity; an absent answer BLOCKS. Empty for a
    #: profile whose laws need nothing the scenario does not declare, which is
    #: every profile before T024.
    foundation_needs: tuple[str, ...] = ()
    #: The typed Site Controls this model's controller needs, by control key.
    site_control_needs: tuple[str, ...] = ()
    #: Run-start dynamic states this model needs the SCENARIO (or the run) to
    #: initialize at every component of the state's carrier type - a battery's
    #: state of charge. v4 section 10.1 makes a run-start condition the
    #: scenario's to answer, so the model does not answer it; it says it needs
    #: one, and a Draft whose scenario states none is BLOCKED with the address
    #: named rather than executing until the kernel meets the hole.
    initialization_needs: tuple[str, ...] = ()
    #: T024 fix round. The single-bus electrical arrangement this model's
    #: laws assume, as `(role, need, via_need)` paths: every component the
    #: `need` names must connect to the Site's one bus THROUGH a component the
    #: `via_need` names (an array through its inverter, a battery through its
    #: PCS). `bus_loads_control` names the Site Control whose members are the
    #: loads the model serves, each of which must connect to the bus directly.
    #: Setup refuses to run a Site whose declared topology does not connect
    #: them, instead of serving a load nothing connects. Empty for a profile
    #: with no electrical bus.
    #: T025a: `via_need` may be `None` for a machine attached to the bus
    #: directly (a generator).
    bus_paths: tuple[tuple[str, str, str | None], ...] = ()
    bus_loads_control: str = ""
    #: T025a. The discrete states this model carries, and the Foundation needs
    #: in minutes that must be whole multiples of the run's step because the
    #: model moves lifecycle state at step boundaries only.
    discrete_states: tuple[DiscreteStateDeclaration, ...] = ()
    step_aligned_needs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for _, participant, via in self.bus_paths:
            if participant not in self.foundation_needs or (
                via is not None and via not in self.foundation_needs
            ):
                raise ValueError(
                    f"{self.model_profile_id} names the bus path "
                    f"{participant} via {via}, and a bus path is made only of "
                    "declared Foundation needs, which is what says which "
                    "component type carries each."
                )
        if self.bus_paths and self.bus_loads_control not in self.site_control_needs:
            raise ValueError(
                f"{self.model_profile_id} declares a bus and names no "
                "declared Site Control as the loads it serves."
            )
        for need in self.foundation_needs:
            state = self.supported(need)
            if (
                state is None
                or state.foundation_binding is None
                or state.scope != "COMPONENT"
                or "CAUSAL_INPUT" not in state.supported_roles
            ):
                raise ValueError(
                    f"Model profile {self.model_profile_id!r} needs {need!r} "
                    "from the Foundation and does not declare it as a "
                    "component-scoped CAUSAL_INPUT state with a Foundation "
                    "binding. A need names the binding that answers it."
                )
        for need in self.initialization_needs:
            state = self.supported(need)
            if (
                state is None
                or state.component_type is None
                or "CAUSAL_INPUT" not in state.supported_roles
            ):
                raise ValueError(
                    f"Model profile {self.model_profile_id!r} needs {need!r} "
                    "initialized and does not declare it as a CAUSAL_INPUT "
                    "state with a carrier component type."
                )
        for state in self.supported_states:
            if state.state_key in REPORTING_PATH_STATES:
                raise ValueError(
                    f"Model profile {self.model_profile_id!r} declares that it "
                    f"models {state.state_key!r}, which is a fact about the "
                    "reporting path and not about the world. Whether a signal "
                    "is reporting changes nothing physical, so the publication "
                    "profile declares it and a model profile may not."
                )

    def supported(self, state_key: str) -> SupportedState | None:
        for state in self.supported_states:
            if state.state_key == state_key:
                return state
        return None


@dataclass(frozen=True)
class DeviceSignalDeclaration:
    """One reporting path this profile declares: what publishes what, and how.

    The product half of `assetops_contracts.observation.DeviceSignalSpec`, and
    the reason the publication profile is the thing that declares it: "the
    publication profile owns reporting behavior" (`.ai/ARCHITECTURE.md`
    Addressing, Properties And Policy). A Foundation declares that a device
    signal CAN report and declares its unit; it declares no rate, no error and no
    reliability, and nothing infers one from a device name.

    `device_id` and `signal_id` must be a signal the target Site's Foundation
    configures, which run setup resolves - a profile cannot see a Foundation, so
    it declares the identity and run setup says whether this installation has it.
    The COMPONENT comes from the Foundation's own signal mapping, which is what
    turns a declaration about `fuel-tank-volume` into a reporting path about
    `fuel-tank-volume@fuel-tank`.

    `state_key` is a state of the WORLD, refused below if it is a reporting-path
    state. A path cannot report whether it is itself reporting.

    `bias` is additive, in the signal's canonical unit, and is the whole of the
    instrument error this build models. It is authored as a decimal and normalized
    once at the input boundary like every other authored number.

    `dropout_per_thousand` is how many of this signal's due samples do not
    publish. Which ones is drawn from the run's seed rather than chosen, under the
    contract's `a-publication-failure-is-drawn-not-chosen`.

    `cadence_minutes` is when a sample is due, counted from the interval's start.
    It is NOT the span an interval reading covers: the span is the run's timestep
    and the contract's `interval-signal-describes-the-preceding-interval` says so.
    A signal publishing hourly at a fifteen-minute timestep therefore publishes a
    measurement of the last fifteen minutes, once an hour, which is what real
    telemetry does.
    """

    device_id: str
    signal_id: str
    state_key: str
    reading_class: str
    canonical_unit: str
    cadence_minutes: int
    bias: float
    dropout_per_thousand: int
    statement: str

    def __post_init__(self) -> None:
        if self.reading_class not in REPORTABLE_READING_CLASSES:
            raise ValueError(
                f"Signal {self.signal_id!r} on {self.device_id!r} is declared as "
                f"a {self.reading_class!r}, and a published reading is one of "
                f"{sorted(REPORTABLE_READING_CLASSES)}. A controller's view is "
                "not published, so no device signal may be declared for it."
            )
        if self.state_key in REPORTING_PATH_STATES:
            raise ValueError(
                f"Signal {self.signal_id!r} on {self.device_id!r} is declared to "
                f"report {self.state_key!r}, which is a fact about the reporting "
                "path rather than about the world. A path does not report "
                "whether it is reporting."
            )
        if self.cadence_minutes <= 0:
            raise ValueError(
                f"Signal {self.signal_id!r} on {self.device_id!r} declares a "
                f"cadence of {self.cadence_minutes} minutes. How often a reading "
                "is published is a span of non-zero length."
            )
        if not 0 <= self.dropout_per_thousand <= 1000:
            raise ValueError(
                f"Signal {self.signal_id!r} on {self.device_id!r} declares a "
                f"dropout of {self.dropout_per_thousand} per thousand, which is "
                "not a share of the samples that were due."
            )

    @property
    def signal_key(self) -> tuple[str, str]:
        return (self.device_id, self.signal_id)


@dataclass(frozen=True)
class PublicationProfile:
    """One versioned observation and publication profile.

    Each of the three values it declares may be absent, and absent is a real
    answer: it means nobody has declared that input yet, and a run that needs
    it is `BLOCKED`. None of the three has a default, because a default here
    would be the product inventing a reporting rate or a source identity.

    ## `supported_reporting_states` is a fourth declaration since T020B

    A scenario can force a condition on the reporting path - the shipped Fuel
    Loss Event forces the fuel level sensor to report nothing across the
    removal - and something has to say whether this build can model that. It
    is not the model profile's to say, because it is not a fact about the
    world, so the authority moved here
    (`D-2026-09-22-forcing-state-requirements`).

    Declared as a tuple that may be EMPTY, and empty is a real answer with a
    consequence: a run whose scenario requires a reporting-path condition this
    profile does not declare is `BLOCKED`, with a reason naming this profile
    rather than the model profile. That is the whole reason the authority
    moved - the previous answer sent a reader to widen the wrong profile.

    ## `device_signals` is a fifth since T022, and it is what makes a reading

    Until T022 this profile said at what rate a declared scenario source
    publishes and nothing about what any device reports. Nothing generated a
    reading, so there was nothing more to say. The observation transform is the
    consumer, and it needs per-signal answers that a single blanket cadence
    cannot give: two signals about one tank at two rates, one biased and one not,
    one dropping samples and one not.

    **`device_signal_cadence_minutes` is not a second answer to the same
    question.** It is what a scenario's own declared observation source resolves
    to and is frozen on the run for provenance. `resolve_observation_binding`
    below now prefers a matching declaration's cadence and falls back to it, so
    there is one answer per signal rather than two that could drift.
    """

    publication_profile_id: str
    publication_profile_version: int
    display_name: str
    statement: str
    device_signal_cadence_minutes: int | None
    simulator_source_id: str | None
    gateway_id: str | None
    supported_reporting_states: tuple[SupportedReportingState, ...] = ()
    device_signals: tuple[DeviceSignalDeclaration, ...] = ()

    def __post_init__(self) -> None:
        seen: set[tuple[str, str]] = set()
        for declaration in self.device_signals:
            if declaration.signal_key in seen:
                raise ValueError(
                    f"Publication profile {self.publication_profile_id!r} "
                    f"declares {declaration.signal_key} twice. One device signal "
                    "has one reporting path, or nothing says which cadence, bias "
                    "and dropout apply to it."
                )
            seen.add(declaration.signal_key)
        for state in self.supported_reporting_states:
            for silenced in state.silences:
                if silenced not in seen:
                    raise ValueError(
                        f"Publication profile {self.publication_profile_id!r} "
                        f"says {state.state_key!r} silences {silenced}, which it "
                        "does not declare as a device signal. A path can only "
                        "silence a path this profile says exists, or the "
                        "capability would be a claim about a signal nobody "
                        "configured."
                    )

    def supported_reporting(
        self, state_key: str
    ) -> SupportedReportingState | None:
        for state in self.supported_reporting_states:
            if state.state_key == state_key:
                return state
        return None

    def device_signal(
        self, device_id: str, signal_id: str
    ) -> DeviceSignalDeclaration | None:
        for declaration in self.device_signals:
            if declaration.signal_key == (device_id, signal_id):
                return declaration
        return None


#: The two answerers of "can this build model this state", spelled once.
#:
#: These are the same strings `FROZEN_INPUT_ANSWERERS` uses, and they are
#: repeated here rather than imported because `runs/models.py` imports nothing
#: from this module and the dependency would be the wrong way round. A test
#: asserts the two agree.
STATE_AUTHORITIES = frozenset({"MODEL_PROFILE", "PUBLICATION_PROFILE"})


@dataclass(frozen=True)
class StateAuthority:
    """Which profile answers for one state, and what it said.

    ## Why one record, asked once

    Two functions in run setup used to ask the support question independently -
    the address pass and `_support_for` - and they asked it of the model
    profile with their own lookups and their own message wording. T020A1's
    review found them ordering the same two facts oppositely: one refused a
    scope disagreement first because a disagreement explains a missing binding,
    and the other refused the missing binding first and told the author to add
    a binding that could never exist. Both were reading the same profile and
    neither was reading the other.

    So the question is asked here, once, and both callers consume the answer.
    An ordering mistake is now a mistake in one place rather than a
    disagreement between two.

    `supported` is whichever record the answering profile holds, or `None` when
    that profile declares nothing for this state. Both records expose `scope`,
    `supported_roles`, `foundation_binding` and `statement`, so a caller reads
    the answer without knowing which kind it is.
    """

    answerer: str
    detail: str
    supported: SupportedState | SupportedReportingState | None

    def __post_init__(self) -> None:
        if self.answerer not in STATE_AUTHORITIES:
            raise ValueError(
                f"{self.answerer!r} is not a state authority. One of "
                f"{sorted(STATE_AUTHORITIES)} answers whether this build can "
                "model a state."
            )

    @property
    def models_it(self) -> bool:
        return self.supported is not None

    @property
    def scope(self) -> str | None:
        return None if self.supported is None else self.supported.scope

    @property
    def foundation_binding(self) -> FoundationBinding | None:
        return None if self.supported is None else self.supported.foundation_binding

    @property
    def is_reporting_path(self) -> bool:
        return self.answerer == "PUBLICATION_PROFILE"


def state_authority(
    state_key: str, model: ModelProfile, publication: PublicationProfile
) -> StateAuthority:
    """Which profile answers for this state, and its answer.

    Decided by the STATE, from a closed vocabulary, and never by asking both
    and taking whichever replied. That distinction is the point: "ask the model
    profile, and if it declares nothing ask the publication profile" would make
    a state the model profile simply has not got round to modelling look like a
    reporting-path state, and the reason a reader is sent to would be the wrong
    profile.

    So a reporting-path state is answered by the publication profile whether or
    not that profile declares it, and a world state by the model profile on the
    same terms. An unanswered question is reported against the profile whose
    job it was.
    """
    if state_key in REPORTING_PATH_STATES:
        return StateAuthority(
            answerer="PUBLICATION_PROFILE",
            detail=(
                f"publication profile {publication.publication_profile_id} "
                f"version {publication.publication_profile_version}"
            ),
            supported=publication.supported_reporting(state_key),
        )
    return StateAuthority(
        answerer="MODEL_PROFILE",
        detail=(
            f"model profile {model.model_profile_id} version "
            f"{model.model_profile_version}"
        ),
        supported=model.supported(state_key),
    )


def resolve_observation_binding(
    source: ObservationSource, profile: PublicationProfile
) -> FrozenObservationBinding:
    """Freeze one declared source with the cadence the profile resolves.

    Two arguments and neither is a Site. The scenario's own declared source
    carries an identity, a kind and who owns its cadence - and, since T018, no
    rate and no name it could be read off - and the profile carries the rate.
    Nothing else is consulted, so there is nothing else a cadence could come
    from.

    An operator record resolves to `NOT_APPLICABLE` deliberately rather than by
    omission: a person writing a level down reports at no rate, so there is no
    cadence for anything to own and no reason to block.

    **Since T022 the profile may declare a rate per signal.** Where it has, that
    is the rate, and the blanket `device_signal_cadence_minutes` is the answer for
    a signal it has not declared one for. One answer per signal rather than two:
    a declaration and a blanket rate disagreeing about one signal would put a
    provenance row and a generated reading series on two grids, and nothing would
    say which was the cadence.
    """
    if source.source_kind != "DEVICE_SIGNAL":
        return FrozenObservationBinding(
            source_id=source.source_id,
            source_kind=source.source_kind,
            device_id=source.device_id,
            signal_id=source.signal_id,
            cadence_ownership=source.cadence_ownership,
            # A person writing a level down reports at no rate, so there is
            # no cadence and nothing to own. What that means is read off the
            # source kind rather than stored beside it.
            cadence_minutes=None,
        )

    declared = (
        None
        if source.device_id is None or source.signal_id is None
        else profile.device_signal(source.device_id, source.signal_id)
    )
    cadence = (
        profile.device_signal_cadence_minutes
        if declared is None
        else declared.cadence_minutes
    )

    return FrozenObservationBinding(
        source_id=source.source_id,
        source_kind=source.source_kind,
        device_id=source.device_id,
        signal_id=source.signal_id,
        cadence_ownership=source.cadence_ownership,
        cadence_minutes=cadence,
    )


def resolve_publication_identity(
    profile: PublicationProfile,
) -> FrozenPublicationIdentity:
    """Freeze the simulator source and gateway the profile declares.

    One argument, and it is the profile. There is no Site here, no source
    mode, no device, and no fallback: what the profile does not declare stays
    `None` and blocks the run.
    """
    return FrozenPublicationIdentity(
        simulator_source_id=profile.simulator_source_id,
        gateway_id=profile.gateway_id,
    )


#: The model the first causal kernel will implement.
#:
#: Four states since T020A. Two are about the generator fuel tank, one is the
#: generator's own physical coefficient, and one is the exogenous output the
#: scenario forces on it.
#:
#: Two of the four are answered by the Site's Foundation and say so with a
#: binding naming the component type, the property and the unit. The stored
#: volume has no Foundation answer, because a Foundation says how large a tank
#: is and never how full it is; the forced output has none either, because it
#: is the story's, not the machine's.
MINIMAL_FUEL_TANK_MODEL = ModelProfile(
    model_profile_id="minimal-fuel-tank",
    model_profile_version=1,
    display_name="Minimal fuel tank model",
    statement=(
        "Models the stored volume in a generator fuel tank, the capacity that "
        "bounds it, the generator's specific fuel consumption and the output "
        "it is dispatched at, and nothing else. Site demand and plane-of-array "
        "irradiance are not modelled: a scenario that REQUIRES either cannot "
        "execute against this profile, and one that declares either as "
        "optional runs with that input recorded as unsupported. Whether a "
        "reporting path is carrying readings is not a state of the world and "
        "is not this profile's to declare at all."
    ),
    supported_states=(
        SupportedState(
            state_key="fuel-tank-volume",
            scope="COMPONENT",
            supported_roles=frozenset({"CAUSAL_INPUT", "REPORTED_OBSERVATION"}),
            foundation_binding=None,
            statement=(
                "The stored volume can be initialized, moved by a declared "
                "cause, and reported through a declared source."
            ),
        ),
        SupportedState(
            state_key="fuel-tank-capacity",
            scope="COMPONENT",
            supported_roles=frozenset({"CAUSAL_INPUT"}),
            foundation_binding=FoundationBinding(
                component_type="FUEL_TANK",
                property_key="tank-capacity",
                unit="L",
            ),
            statement=(
                "The capacity is a bound on the stored volume, and the site's "
                "foundation is the authority for it: the tank-capacity "
                "property of the fuel-storage component is the value a run "
                "freezes."
            ),
        ),
        SupportedState(
            state_key="generator-specific-fuel-consumption",
            scope="COMPONENT",
            supported_roles=frozenset({"CAUSAL_INPUT"}),
            foundation_binding=FoundationBinding(
                component_type="GENERATOR",
                property_key="specific-fuel-consumption",
                unit="L/kWh",
            ),
            statement=(
                "How much fuel this generator burns per kilowatt-hour "
                "delivered is a property of the machine, so the site's "
                "foundation answers for it. The model rule that consumes it - "
                "consumption is specific consumption times energy delivered - "
                "belongs to the kernel, not to this declaration."
            ),
        ),
        SupportedState(
            state_key="generator-output-power",
            scope="COMPONENT",
            supported_roles=frozenset({"FORCING_INPUT"}),
            foundation_binding=None,
            statement=(
                "The output the generator is dispatched at is forced by the "
                "scenario across a declared window; this profile carries the "
                "forced value and solves no power flow for it. It has no "
                "foundation answer, because what a generator is asked to "
                "deliver is the story's and not the machine's."
            ),
        ),
    ),
)


def _need(
    state_key: str,
    component_type: str,
    property_key: str,
    unit: str,
    statement: str,
) -> SupportedState:
    return SupportedState(
        state_key=state_key,
        scope="COMPONENT",
        supported_roles=frozenset({"CAUSAL_INPUT"}),
        foundation_binding=FoundationBinding(
            component_type=component_type,
            property_key=property_key,
            unit=unit,
        ),
        statement=statement,
    )


#: The daytime mini-grid model T024 adds (map A, first electrical world).
#:
#: A separate profile rather than a second version of `minimal-fuel-tank`,
#: which is unchanged: the fuel profile's recorded limitation - it does not
#: model demand or irradiance - stays true of it, and a Fuel Loss run keeps
#: meaning exactly what it meant (criterion 14).
#:
#: It is the first profile whose laws need Foundation values no scenario asks
#: for, which is Option C's trigger. `foundation_needs` names them; the
#: scenario declares only the story - irradiance, each load's demand, the
#: battery's state of charge at the start, and any temporary reserve override.
#:
#: The generator is deliberately not modelled: this is a generator-stopped
#: daytime baseline and T025 adds the generator lifecycle.
DAYTIME_MINI_GRID_MODEL = ModelProfile(
    model_profile_id="daytime-mini-grid",
    model_profile_version=1,
    display_name="Daytime mini-grid model",
    statement=(
        "Models a daytime mini-grid with one PV array behind one inverter, one "
        "battery behind one power conversion system, and any number of "
        "addressed loads. Plane-of-array irradiance and each load's demand are "
        "forced; the battery's state of charge is initialized by the scenario "
        "and evolves under accepted charge and discharge. A controller reads a "
        "local view and requests battery power; a resolver accepts what the "
        "PCS limits, the battery's energy, its reserve and its efficiency allow, "
        "serves loads in the Site's critical-load priority and curtails what "
        "cannot be used. The generator is not modelled."
    ),
    supported_states=(
        SupportedState(
            state_key="plane-of-array-irradiance",
            scope="SITE",
            supported_roles=frozenset({"FORCING_INPUT"}),
            foundation_binding=None,
            statement=(
                "Plane-of-array irradiance is forced by the scenario across "
                "declared windows. PV potential is the array's rated power "
                "scaled by irradiance over 1000 W/m2."
            ),
        ),
        SupportedState(
            state_key="load-demand",
            scope="COMPONENT",
            supported_roles=frozenset({"FORCING_INPUT"}),
            foundation_binding=None,
            component_type="LOAD",
            statement=(
                "Each load's demand is forced separately at its own address, "
                "so two loads of one type have two independent demands."
            ),
        ),
        SupportedState(
            state_key="battery-state-of-charge",
            scope="COMPONENT",
            supported_roles=frozenset({"CAUSAL_INPUT", "REPORTED_OBSERVATION"}),
            foundation_binding=None,
            component_type="BATTERY",
            statement=(
                "The battery's state of charge is initialized explicitly by the "
                "scenario at run start, never inferred from its reserve, and "
                "moves only under accepted charge and discharge."
            ),
        ),
        SupportedState(
            state_key="battery-reserve-state-of-charge",
            scope="COMPONENT",
            supported_roles=frozenset({"CAUSAL_INPUT", "FORCING_INPUT"}),
            foundation_binding=FoundationBinding(
                component_type="BATTERY",
                property_key="reserve-state-of-charge",
                unit="%",
            ),
            statement=(
                "The battery's reserve is a component control property the "
                "Foundation answers for as the baseline. A scenario may force "
                "it across a window, which replaces the baseline inside the "
                "window only; the baseline applies again at the window's end."
            ),
        ),
        _need(
            "pv-rated-power",
            "PV_ARRAY",
            "pv-rated-power",
            "kW",
            "The array's DC output at 1000 W/m2, from the Foundation.",
        ),
        _need(
            "inverter-ac-limit",
            "INVERTER",
            "inverter-ac-limit",
            "kW",
            "The most AC power the PV inverter passes, from the Foundation.",
        ),
        _need(
            "battery-energy-capacity",
            "BATTERY",
            "battery-energy-capacity",
            "kWh",
            "The battery's usable energy at 100 % state of charge.",
        ),
        _need(
            "pcs-charge-limit",
            "POWER_CONVERSION_SYSTEM",
            "pcs-charge-limit",
            "kW",
            "The most AC power the PCS takes in while charging.",
        ),
        _need(
            "pcs-discharge-limit",
            "POWER_CONVERSION_SYSTEM",
            "pcs-discharge-limit",
            "kW",
            "The most AC power the PCS delivers while discharging.",
        ),
        _need(
            "pcs-conversion-efficiency",
            "POWER_CONVERSION_SYSTEM",
            "pcs-conversion-efficiency",
            "%",
            "The PCS's one-way efficiency, applied in each direction.",
        ),
    ),
    foundation_needs=(
        "pv-rated-power",
        "inverter-ac-limit",
        "battery-energy-capacity",
        "pcs-charge-limit",
        "pcs-discharge-limit",
        "pcs-conversion-efficiency",
        "battery-reserve-state-of-charge",
    ),
    site_control_needs=("source-priority", "critical-load-priority"),
    initialization_needs=("battery-state-of-charge",),
    bus_paths=(
        ("PV_SOURCE", "pv-rated-power", "inverter-ac-limit"),
        ("STORAGE", "battery-energy-capacity", "pcs-charge-limit"),
    ),
    bus_loads_control="critical-load-priority",
)

#: The full-site mini-grid model T025a adds (map A, healthy full-site physics),
#: under execution contract 9 and additively
#: (`D-2026-09-29-t025-generator-policy-package`). `daytime-mini-grid` v1 is
#: unchanged beside it: a new profile identity is a new answer.
#:
#: The generator's control policy is the SITE's: start and stop thresholds and
#: minimum runtime are CONTROL properties of the generator on the Foundation,
#: frozen as model needs with their provenance; the model adds no trigger of
#: its own. The start delay and rating are PHYSICAL properties. Initial fuel,
#: state of charge and lifecycle state are the scenario's.
MINI_GRID_MODEL = ModelProfile(
    model_profile_id="mini-grid",
    model_profile_version=1,
    display_name="Mini-grid model",
    statement=(
        "Models a full mini-grid: one PV array behind one inverter, one battery "
        "behind one power conversion system, any number of addressed loads, "
        "and one generator with its fuel tank. The generator's lifecycle - "
        "STOPPED, STARTING, RUNNING, FAILED - is a typed discrete state that "
        "moves at step boundaries only; the Site's frozen policy starts it at "
        "or below its start threshold and stops it at or above its stop "
        "threshold once its minimum runtime has elapsed. Sources serve load in "
        "the Site's frozen source priority, fuel falls with accepted generator "
        "energy, and every electrical and fuel balance is exact."
    ),
    supported_states=DAYTIME_MINI_GRID_MODEL.supported_states
    + (
        SupportedState(
            state_key="generator-state",
            scope="COMPONENT",
            supported_roles=frozenset({"CAUSAL_INPUT"}),
            foundation_binding=None,
            component_type="GENERATOR",
            statement=(
                "The generator's physical lifecycle state, a typed member of "
                "STOPPED, STARTING, RUNNING and FAILED. The scenario states it "
                "at run start; this build starts from STOPPED or FAILED only."
            ),
        ),
        SupportedState(
            state_key="fuel-tank-volume",
            scope="COMPONENT",
            supported_roles=frozenset({"CAUSAL_INPUT"}),
            foundation_binding=None,
            component_type="FUEL_TANK",
            statement=(
                "The fuel in the tank, initialized by the scenario and moved "
                "only by accepted generator energy."
            ),
        ),
        _need(
            "generator-rated-power",
            "GENERATOR",
            "generator-rated-power",
            "kW",
            "The most AC power the generator delivers: a ceiling, not a command.",
        ),
        _need(
            "generator-specific-fuel-consumption",
            "GENERATOR",
            "specific-fuel-consumption",
            "L/kWh",
            "Litres burned per kWh of accepted generator energy.",
        ),
        _need(
            "generator-start-soc-threshold",
            "GENERATOR",
            "start-soc-threshold",
            "%",
            "Site policy: the generator is requested to start at or below it.",
        ),
        _need(
            "generator-stop-soc-threshold",
            "GENERATOR",
            "stop-soc-threshold",
            "%",
            "Site policy: the generator is requested to stop at or above it.",
        ),
        _need(
            "generator-minimum-runtime",
            "GENERATOR",
            "minimum-runtime",
            "min",
            "Site policy: no stop before the generator has run this long.",
        ),
        _need(
            "generator-start-delay",
            "GENERATOR",
            "start-delay",
            "min",
            "How long the generator is STARTING, delivering nothing.",
        ),
        _need(
            "fuel-tank-capacity",
            "FUEL_TANK",
            "tank-capacity",
            "L",
            "The most fuel the tank holds.",
        ),
    ),
    foundation_needs=DAYTIME_MINI_GRID_MODEL.foundation_needs
    + (
        "generator-rated-power",
        "generator-specific-fuel-consumption",
        "generator-start-soc-threshold",
        "generator-stop-soc-threshold",
        "generator-minimum-runtime",
        "generator-start-delay",
        "fuel-tank-capacity",
    ),
    site_control_needs=("source-priority", "critical-load-priority"),
    initialization_needs=(
        "battery-state-of-charge",
        "fuel-tank-volume",
        "generator-state",
    ),
    bus_paths=DAYTIME_MINI_GRID_MODEL.bus_paths
    + (
        ("GENERATION", "generator-rated-power", None),
        ("FUEL_SUPPLY", "fuel-tank-capacity", "generator-rated-power"),
    ),
    bus_loads_control="critical-load-priority",
    discrete_states=(
        DiscreteStateDeclaration(
            state_key="generator-state",
            allowed_values=("STOPPED", "STARTING", "RUNNING", "FAILED"),
            initial_values_supported=frozenset({"STOPPED", "FAILED"}),
            unsupported_initial_reason=(
                "RUNNING and STARTING need timer history - how long it has run, "
                "how much start delay remains - that no scenario can declare "
                "yet, and this build does not invent one."
            ),
        ),
    ),
    step_aligned_needs=("generator-minimum-runtime", "generator-start-delay"),
)

#: The publication profile the Lab publishes through.
#:
#: It declares the three things nothing else may supply: how often a device
#: signal reports, which simulator source a run publishes as, and which
#: gateway it publishes through. All three are this profile's to declare and
#: nobody else's, which is why a run that selects a profile declaring none of
#: them is blocked rather than defaulted.
#:
#: Since T020B it declares a fourth thing: that it can model the reporting path
#: being unavailable. That is the one the shipped Fuel Loss Event needs, and it
#: belongs here rather than in the model profile because a sensor reporting
#: nothing changes nothing about the fuel. This profile OWNS the path, so
#: suppressing what travels along it is a capability of the path.
#:
#: ## Version two since T022, and the version moves because the content does
#:
#: `device_signals` is new, and it is what turns a sampled world into a reading:
#: which configured signals report which state, when, with what error and with
#: what reliability. A run freezes which publication profile answered and at
#: which version precisely so that the readings it produced can be reproduced
#: without the profile catalog being frozen with it. Leaving this at version one
#: would mean two builds claiming one version and generating different series,
#: which is the whole thing the version exists to rule out.
#:
#: ## Version three since T024, and it moves for the same reason
#:
#: Six electrical reporting paths are added: the battery's state of charge,
#: the PCS's AC power, the PV inverter's AC power and one meter per load. A run
#: of an unchanged document against this profile generates a different series
#: than it would under two, so the version moves. A declared path whose state
#: the selected model does not produce is not a reporting path for that run -
#: a fuel run on a hybrid Site does not grow a column of empty battery readings.
#:
#: Two reporting paths, and both resolve against MG-001's own Foundation because
#: a profile declares a signal's identity and run setup says whether this
#: installation configures it. They are deliberately different in every field
#: that matters, because criterion 10's claim is about the key and a pair that
#: differed only in name would not test it:
#:
#: - `fuel-level-sensor`/`fuel-level` reports the tank's stored volume every
#:   fifteen minutes, half a litre low, losing one sample in twenty-five. It is
#:   the signal the shipped scenario's own declared observation source names, and
#:   the one the scenario's reporting gap silences across the removal.
#: - `generator-controller`/`ac-power` reports the average output over the span
#:   that just ended, hourly, with no error and losing nothing. The cadence and
#:   the span are different numbers on purpose: the cadence says when it publishes
#:   and the run's timestep says what span the measurement covers, which is what
#:   real telemetry does.
#:
#: **The dropout is on the fifteen-minute signal deliberately, and the reason is
#: about evidence rather than realism.** An hourly signal whose measurement exists
#: only while the generator runs has four valued samples in this interval, so a
#: dropout declared on it would draw four times and would quite likely select
#: none - and a stochastic mechanism that produced nothing would be a mechanism
#: whose test passes over an empty set. On the fifteen-minute signal it draws a
#: hundred and fifty-nine times and drops a visible handful, which is what makes
#: "adding an unrelated stream changes no existing stream" worth asserting.
LAB_PUBLICATION_PROFILE = PublicationProfile(
    publication_profile_id="simulator-lab-publication",
    publication_profile_version=3,
    display_name="Simulator Lab publication profile",
    statement=(
        "Declares which configured device signals report which world state, how "
        "often, with what bias and with what share of samples not arriving; the "
        "simulator source and gateway identities a run would publish through; "
        "and that a run may force the reporting path for a configured signal to "
        "be unavailable across a declared window. A site's foundation declares "
        "that a signal can report and declares its unit, and declares none of "
        "these; nothing derives them from a device or from how a site was "
        "created."
    ),
    device_signal_cadence_minutes=15,
    simulator_source_id="simulator-lab-source",
    gateway_id="simulator-lab-gateway",
    supported_reporting_states=(
        SupportedReportingState(
            state_key="fuel-level-reporting-availability",
            scope="COMPONENT",
            supported_roles=frozenset({"FORCING_INPUT"}),
            statement=(
                "Whether the fuel level reporting path for a component is "
                "carrying readings can be forced across a declared window. It "
                "is a condition on the path and not on the fuel: it changes no "
                "physical quantity, moves no stock, and carries no state "
                "effect. What it changes is which readings exist to be "
                "published, which is this profile's business."
            ),
            silences=(("fuel-level-sensor", "fuel-level"),),
        ),
    ),
    device_signals=(
        DeviceSignalDeclaration(
            device_id="fuel-level-sensor",
            signal_id="fuel-level",
            state_key="fuel-tank-volume",
            reading_class="STATE_SIGNAL",
            canonical_unit="L",
            cadence_minutes=15,
            bias=-0.5,
            dropout_per_thousand=40,
            statement=(
                "The fuel level sensor publishes the tank's stored volume every "
                "fifteen minutes, reading half a litre low, and one sample in "
                "twenty-five does not arrive. The bias is the instrument's and "
                "not the installation's: the tank holds what it holds, and this "
                "is what the sensor says about it. The dropout is the path's, and "
                "which samples it takes is drawn from the run's seed - so it is "
                "reproducible without being chosen."
            ),
        ),
        DeviceSignalDeclaration(
            device_id="generator-controller",
            signal_id="ac-power",
            state_key="generator-output-power",
            reading_class="INTERVAL_SIGNAL",
            canonical_unit="kW",
            cadence_minutes=60,
            bias=0.0,
            dropout_per_thousand=0,
            statement=(
                "The generator controller publishes its average output over the "
                "span that just ended, once an hour, with no measurement error "
                "and losing no sample. An hourly publication of a fifteen-minute "
                "span is what the two numbers mean: the cadence is when it speaks "
                "and the run's timestep is what it speaks about. It is clean on "
                "purpose, so that a reader comparing it against the fuel sensor "
                "beside it can see that a bias and a dropout are properties of one "
                "reporting path rather than of the run."
            ),
        ),
        # T024: the electrical signals T026 will publish. Generated as device
        # observations now; the gateway's allowlist does not publish them yet.
        DeviceSignalDeclaration(
            device_id="battery-pcs-controller",
            signal_id="state-of-charge",
            state_key="battery-state-of-charge",
            reading_class="STATE_SIGNAL",
            canonical_unit="%",
            cadence_minutes=15,
            bias=0.0,
            dropout_per_thousand=20,
            statement=(
                "The PCS controller publishes the battery's state of charge "
                "every fifteen minutes, sampled after that instant's events. "
                "One sample in fifty does not arrive."
            ),
        ),
        DeviceSignalDeclaration(
            device_id="battery-pcs-controller",
            signal_id="ac-power",
            state_key="battery-ac-power",
            reading_class="INTERVAL_SIGNAL",
            canonical_unit="kW",
            cadence_minutes=15,
            bias=0.0,
            dropout_per_thousand=0,
            statement=(
                "The PCS controller publishes the mean AC power over the span "
                "that just ended: positive while discharging to the bus, "
                "negative while charging from it."
            ),
        ),
        DeviceSignalDeclaration(
            device_id="pv-inverter-controller",
            signal_id="ac-power",
            state_key="pv-ac-power",
            reading_class="INTERVAL_SIGNAL",
            canonical_unit="kW",
            cadence_minutes=15,
            bias=0.0,
            dropout_per_thousand=0,
            statement=(
                "The PV inverter publishes the mean AC power it delivered over "
                "the span that just ended - what was used, not what the array "
                "could have offered."
            ),
        ),
        DeviceSignalDeclaration(
            device_id="residential-meter",
            signal_id="active-power",
            state_key="load-served-power",
            reading_class="INTERVAL_SIGNAL",
            canonical_unit="kW",
            cadence_minutes=15,
            bias=0.0,
            dropout_per_thousand=0,
            statement=(
                "The residential feeder meter publishes the mean power served "
                "to the feeder over the span that just ended."
            ),
        ),
        DeviceSignalDeclaration(
            device_id="clinic-meter",
            signal_id="active-power",
            state_key="load-served-power",
            reading_class="INTERVAL_SIGNAL",
            canonical_unit="kW",
            cadence_minutes=15,
            bias=0.0,
            dropout_per_thousand=0,
            statement=(
                "The clinic meter publishes the mean power served to the "
                "clinic over the span that just ended."
            ),
        ),
        DeviceSignalDeclaration(
            device_id="mill-meter",
            signal_id="active-power",
            state_key="load-served-power",
            reading_class="INTERVAL_SIGNAL",
            canonical_unit="kW",
            cadence_minutes=15,
            bias=0.0,
            dropout_per_thousand=0,
            statement=(
                "The mill meter publishes the mean power served to the mill "
                "over the span that just ended."
            ),
        ),
    ),
)

MODEL_PROFILES: tuple[ModelProfile, ...] = (
    MINIMAL_FUEL_TANK_MODEL,
    DAYTIME_MINI_GRID_MODEL,
    MINI_GRID_MODEL,
)

PUBLICATION_PROFILES: tuple[PublicationProfile, ...] = (LAB_PUBLICATION_PROFILE,)


def find_model_profile(
    profiles: tuple[ModelProfile, ...], profile_id: str, version: int
) -> ModelProfile | None:
    """The one profile with this identity and version, or nothing.

    Identity and version together, never identity alone. A run freezes the
    exact version it was set up against, so resolving "the latest" here would
    make two runs with the same frozen inputs mean different things.
    """
    for profile in profiles:
        if (
            profile.model_profile_id == profile_id
            and profile.model_profile_version == version
        ):
            return profile
    return None


def find_publication_profile(
    profiles: tuple[PublicationProfile, ...], profile_id: str, version: int
) -> PublicationProfile | None:
    """The one publication profile with this identity and version."""
    for profile in profiles:
        if (
            profile.publication_profile_id == profile_id
            and profile.publication_profile_version == version
        ):
            return profile
    return None
