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
- a **publication profile** says at what cadence a device signal reports, and
  which simulator source and which gateway a run would publish through.

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

    def __post_init__(self) -> None:
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
    """

    state_key: str
    scope: str
    supported_roles: frozenset[str]
    statement: str

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

    @property
    def foundation_binding(self) -> None:
        """Always absent, and absent by construction rather than by value.

        A binding names a component type and a property on it, which is a
        Foundation fact. This module cannot see a Foundation, so a publication
        profile has nothing to declare one from.
        """
        return None


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

    def __post_init__(self) -> None:
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
    """

    publication_profile_id: str
    publication_profile_version: int
    display_name: str
    statement: str
    device_signal_cadence_minutes: int | None
    simulator_source_id: str | None
    gateway_id: str | None
    supported_reporting_states: tuple[SupportedReportingState, ...] = ()

    def supported_reporting(
        self, state_key: str
    ) -> SupportedReportingState | None:
        for state in self.supported_reporting_states:
            if state.state_key == state_key:
                return state
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

    cadence = profile.device_signal_cadence_minutes

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
LAB_PUBLICATION_PROFILE = PublicationProfile(
    publication_profile_id="simulator-lab-publication",
    publication_profile_version=1,
    display_name="Simulator Lab publication profile",
    statement=(
        "Declares the reporting cadence for a configured device signal, the "
        "simulator source and gateway identities a run would publish through, "
        "and that a run may force the reporting path for a configured signal "
        "to be unavailable across a declared window. A site's foundation "
        "declares none of these and nothing derives them from a device or from "
        "how a site was created."
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
        ),
    ),
)

MODEL_PROFILES: tuple[ModelProfile, ...] = (MINIMAL_FUEL_TANK_MODEL,)

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
