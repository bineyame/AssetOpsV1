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
is the truth about this build: the shipped Fuel Loss Event also declares site
demand, plane-of-array irradiance and reporting availability as required
forcing inputs, and this profile supports none of them. A run of that scenario
against this profile is therefore `BLOCKED`, with a reason naming each - which
is the honest answer and not a defect. Widening the profile is T021's work,
and it widens by modelling a state rather than by declaring that it does.
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


@dataclass(frozen=True)
class ModelProfile:
    """One versioned simulator model, and what it can model."""

    model_profile_id: str
    model_profile_version: int
    display_name: str
    statement: str
    supported_states: tuple[SupportedState, ...]

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
    """

    publication_profile_id: str
    publication_profile_version: int
    display_name: str
    statement: str
    device_signal_cadence_minutes: int | None
    simulator_source_id: str | None
    gateway_id: str | None


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
        "it is dispatched at, and nothing else. Demand, irradiance and the "
        "availability of the reporting path are not modelled, so a scenario "
        "that requires any of them cannot execute against this profile."
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
LAB_PUBLICATION_PROFILE = PublicationProfile(
    publication_profile_id="simulator-lab-publication",
    publication_profile_version=1,
    display_name="Simulator Lab publication profile",
    statement=(
        "Declares the reporting cadence for a configured device signal, and "
        "the simulator source and gateway identities a run would publish "
        "through. A site's foundation declares none of these and nothing "
        "derives them from a device or from how a site was created."
    ),
    device_signal_cadence_minutes=15,
    simulator_source_id="simulator-lab-source",
    gateway_id="simulator-lab-gateway",
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
