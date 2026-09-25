"""Fixtures for a site with two of things, and a scenario that addresses them.

The run setup fixtures next door describe a site with one fuel tank, which is
the shape every earlier slice needed and the shape that cannot exercise
addressing at all: with one candidate, an unqualified reference and an
addressed one resolve to the same component and a test cannot tell a working
selector from an ignored one.

So this module builds the smallest site that can tell them apart - two fuel
tanks with DIFFERENT capacities, two loads, and a generator - and a scenario
that names them. Different capacities rather than two 500 L tanks on purpose:
the value is what proves which component answered, and two equal values would
let a resolver pick either one and still pass.

`LOAD_RES` and `LOAD_MILL` are the repeated-load pair. They carry no Foundation
property and no binding, because what they are here to prove is addressability
at setup: two loads are two declarations a scenario states separately and a run
keeps apart. Serving them electricity is T024's.
"""

from __future__ import annotations

from typing import Any

from run_fixtures import component_property, site

from assetops_backend.runs.profiles import (
    FoundationBinding,
    ModelProfile,
    SupportedState,
)
from assetops_backend.sites.models import (
    FoundationTopology,
    Rating,
    SiteComponent,
    SiteRecord,
    TopologyNode,
)

NORTH_TANK = "north-tank"
SOUTH_TANK = "south-tank"
LOAD_RES = "load-res"
LOAD_MILL = "load-mill"

#: The two capacities, and they differ. Which number a run freezes is the only
#: evidence available that the right component answered.
NORTH_CAPACITY = 500.0
SOUTH_CAPACITY = 800.0


def twin_components(
    *,
    north: str = NORTH_TANK,
    south: str | None = SOUTH_TANK,
    south_type: str = "FUEL_TANK",
    south_properties: Any = "DEFAULT",
    order_reversed: bool = False,
) -> tuple[SiteComponent, ...]:
    """Two fuel tanks, two loads and a generator.

    `south` of `None` leaves the second tank out, which is how a test removes
    one candidate; `south_type` changes what the second component IS without
    changing its identity, which is how a test proves a selector validates the
    type it landed on. `order_reversed` lists the tanks the other way round,
    which must change nothing a run freezes.
    """
    tanks = [
        SiteComponent(
            component_id=north,
            component_type="FUEL_TANK",
            display_name="North fuel tank",
            rating=Rating(value=NORTH_CAPACITY, unit="L"),
            properties=(component_property(value=NORTH_CAPACITY),),
        )
    ]
    if south is not None:
        tanks.append(
            SiteComponent(
                component_id=south,
                component_type=south_type,
                display_name="South fuel tank",
                rating=Rating(value=SOUTH_CAPACITY, unit="L"),
                properties=(
                    (component_property(value=SOUTH_CAPACITY),)
                    if south_properties == "DEFAULT"
                    else south_properties
                ),
            )
        )

    if order_reversed:
        tanks.reverse()

    return tuple(tanks) + (
        SiteComponent(
            component_id="site-generator",
            component_type="GENERATOR",
            display_name="Diesel generator",
            rating=Rating(value=60.0, unit="kW"),
            properties=(
                component_property(
                    property_key="specific-fuel-consumption",
                    value=0.311,
                    unit="L/kWh",
                ),
            ),
        ),
        SiteComponent(
            component_id=LOAD_RES,
            component_type="LOAD",
            display_name="Residential feeder",
            rating=Rating(value=40.0, unit="kW"),
            properties=None,
        ),
        SiteComponent(
            component_id=LOAD_MILL,
            component_type="LOAD",
            display_name="Grain mill feeder",
            rating=Rating(value=25.0, unit="kW"),
            properties=None,
        ),
    )


def twin_site(**overrides: Any) -> SiteRecord:
    """The two-of-everything Site, at the identity the scenario targets."""
    components = overrides.pop("components", None)
    if components is None:
        components = twin_components()
    return site(
        components=components,
        topology=FoundationTopology(
            nodes=tuple(
                TopologyNode(
                    node_id=component.component_id,
                    component_id=component.component_id,
                    node_role=(
                        "FUEL_STORAGE"
                        if component.component_type == "FUEL_TANK"
                        else "GENERATION"
                        if component.component_type == "GENERATOR"
                        else "LOAD"
                    ),
                )
                for component in components
            ),
            connections=(),
        ),
        devices=(),
        signal_mappings=(),
        **overrides,
    )


def twin_profile(
    *,
    volume_scope: str = "COMPONENT",
    demand_scope: str = "SITE",
    binding: FoundationBinding | None = None,
) -> ModelProfile:
    """A profile that models three states and names no component.

    Three because the slice needs three different shapes: a component-scoped
    state the Foundation answers for, a component-scoped state the scenario
    answers for, and a site-wide state nothing on a component could answer.

    `volume_scope` and `demand_scope` are arguments so a test can make the
    profile and the scenario disagree about scope without changing anything
    else. Nothing here names `north-tank`: select this same profile for a
    different Site and it addresses that Site's components, which is what
    makes it a simulator build rather than a fixture.
    """
    return ModelProfile(
        model_profile_id="twin-asset-model",
        model_profile_version=1,
        display_name="Twin asset model",
        statement="Models a stored volume per tank and one site-wide demand.",
        supported_states=(
            SupportedState(
                state_key="example-stored-volume",
                scope=volume_scope,
                supported_roles=frozenset({"CAUSAL_INPUT"}),
                foundation_binding=(
                    binding
                    if binding is not None
                    else FoundationBinding(
                        component_type="FUEL_TANK",
                        property_key="tank-capacity",
                        unit="L",
                    )
                )
                if volume_scope == "COMPONENT"
                else None,
                statement="The capacity of one tank, from that tank.",
            ),
            SupportedState(
                state_key="example-stored-level",
                scope="COMPONENT",
                supported_roles=frozenset(
                    {"CAUSAL_INPUT", "REPORTED_OBSERVATION"}
                ),
                foundation_binding=None,
                statement=(
                    "How full one tank is at the start, which the scenario "
                    "owns: a foundation says how large a tank is and never "
                    "how full it is."
                ),
            ),
            SupportedState(
                state_key="example-demand",
                scope=demand_scope,
                supported_roles=frozenset({"FORCING_INPUT"}),
                foundation_binding=None,
                statement="Demand forced on the run.",
            ),
        ),
    )


def twin_document(
    *,
    north_volume: str = f"example-stored-volume@{NORTH_TANK}",
    south_volume: str | None = f"example-stored-volume@{SOUTH_TANK}",
    north_level: float = 200.0,
    south_level: float = 350.0,
    north_level_ref: str = f"example-stored-level@{NORTH_TANK}",
    south_level_ref: str | None = f"example-stored-level@{SOUTH_TANK}",
    demand: str = "site:example-demand",
) -> dict[str, Any]:
    """A scenario that addresses two tanks and two loads.

    Built here rather than by mutating the shared fixture, because the shared
    one is deliberately a single-asset document and half of these tests are
    about what happens when a document names two of something.

    Four initial values: each tank's capacity, answered by the Foundation, and
    each tank's starting level, answered by the scenario. The second pair is
    acceptance criterion 9 - a component's own initial level is addressed too,
    so one tank's 200 L cannot start the other tank at 200 L.

    The level addresses are arguments for a reason an independent review
    made plain. A test that puts this document on a site with different
    components has to move those references too: a scenario-owned initial
    value names an asset like any other reference, and leaving it pointing at
    `north-tank` on a site that declares `alpha-tank` is not a harmless
    detail in the fixture - it is the very defect that review found, written
    into the test that was supposed to establish the opposite.
    """
    parameters: list[dict[str, Any]] = [
        {
            "parameter_id": "north-capacity",
            "display_name": "North tank capacity",
            "unit": "L",
            "execution_role": "CAUSAL_INPUT",
            "state_key": north_volume,
            "execution_requirement": "REQUIRED",
            "ownership": {"owner": "SITE_FOUNDATION", "initializes": True},
        },
        {
            "parameter_id": "north-start",
            "display_name": "North tank level at the start",
            "value": north_level,
            "unit": "L",
            "execution_role": "CAUSAL_INPUT",
            "state_key": north_level_ref,
            "execution_requirement": "REQUIRED",
            "ownership": {"owner": "SCENARIO_INPUT", "initializes": True},
        },
    ]

    if south_level_ref is not None:
        parameters.append(
            {
                "parameter_id": "south-start",
                "display_name": "South tank level at the start",
                "value": south_level,
                "unit": "L",
                "execution_role": "CAUSAL_INPUT",
                "state_key": south_level_ref,
                "execution_requirement": "REQUIRED",
                "ownership": {
                    "owner": "SCENARIO_INPUT",
                    "initializes": True,
                },
            }
        )

    if south_volume is not None:
        parameters.insert(
            1,
            {
                "parameter_id": "south-capacity",
                "display_name": "South tank capacity",
                "unit": "L",
                "execution_role": "CAUSAL_INPUT",
                "state_key": south_volume,
                "execution_requirement": "REQUIRED",
                "ownership": {"owner": "SITE_FOUNDATION", "initializes": True},
            },
        )

    return {
        "scenario_id": "twin-asset-scenario",
        "display_name": "Twin asset scenario",
        "purpose": "Exercise two components of one type on one site.",
        "version": {
            "scenario_version": 1,
            "version_valid_from": "2026-01-01T00:00:00Z",
            "supersedes": None,
        },
        "target_site": {
            "policy": "DECLARED_SITE",
            "site_id": "MG-900",
            "template_id": None,
            "requirement": "A mini-grid with two fuel tanks and two feeders.",
        },
        "observation_sources": [
            {
                "source_id": "example-hand-record",
                "source_kind": "OPERATOR_RECORD",
                "cadence_ownership": "NOT_APPLICABLE",
                "description": "A technician reading one tank by hand.",
            }
        ],
        "public_parameters": parameters,
        "timeline": [
            {
                "event_id": "residential-feeder",
                "sequence": 1,
                "offset_minutes": 0,
                "entry_kind": "EVENT",
                "category": "LOAD",
                "description": "The residential feeder follows its shape.",
                "execution_role": "FORCING_INPUT",
                "state_key": demand,
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "INTERVAL_WIDE"},
                "parameters": [
                    {
                        "parameter_id": "residential-demand",
                        "display_name": "Residential demand",
                        "value": 40,
                        "unit": "kW",
                        "execution_role": "FORCING_INPUT",
                        "state_key": demand,
                        "execution_requirement": "REQUIRED",
                        "ownership": {
                            "owner": "SCENARIO_INPUT",
                            "initializes": False,
                        },
                    }
                ],
            },
            {
                "event_id": "north-tank-inspection",
                "sequence": 2,
                "offset_minutes": 120,
                "entry_kind": "INTERVENTION",
                "category": "MAINTENANCE",
                "description": "A technician records the north tank by hand.",
                "execution_role": "REPORTED_OBSERVATION",
                "state_key": north_level_ref,
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "POINT"},
                "observation": {
                    "source_id": "example-hand-record",
                    "reported_parameter_id": "north-reading",
                },
                "parameters": [
                    {
                        "parameter_id": "north-reading",
                        "display_name": "North tank level recorded",
                        "value": north_level,
                        "unit": "L",
                        "execution_role": "REPORTED_OBSERVATION",
                        "state_key": north_level_ref,
                        "execution_requirement": "REQUIRED",
                    }
                ],
            },
        ],
        "private_expectations": [
            {
                "expectation_id": "two-tanks-stay-two",
                "display_name": "The two tanks are never one",
                "oracle_kind": "DETECTION",
                "statement": (
                    "A later analysis must attribute a change to the tank it "
                    "happened in rather than to the site."
                ),
            }
        ],
    }


def repeated_load_document() -> dict[str, Any]:
    """The same scenario with demand declared per feeder instead of site-wide.

    The repeated-load binding the proof asks for. It addresses `load-res` and
    `load-mill` separately, which is the whole claim: two feeders are two
    forcing declarations a run keeps apart at setup. Nothing here serves
    either of them any power, and nothing in this build could.
    """
    document = twin_document(demand=f"example-demand@{LOAD_RES}")
    # Paired with `twin_profile(demand_scope="COMPONENT")`: demand declared
    # per feeder is a component-scoped claim, and a profile modelling one
    # site-wide demand blocks it rather than silently dropping the address.
    mill = {
        "event_id": "mill-feeder",
        "sequence": 3,
        "offset_minutes": 0,
        "entry_kind": "EVENT",
        "category": "LOAD",
        "description": "The grain mill feeder runs on its own shape.",
        "execution_role": "FORCING_INPUT",
        "state_key": f"example-demand@{LOAD_MILL}",
        "execution_requirement": "REQUIRED",
        "timing": {"shape": "INTERVAL_WIDE"},
        "parameters": [
            {
                "parameter_id": "mill-demand",
                "display_name": "Grain mill demand",
                "value": 25,
                "unit": "kW",
                "execution_role": "FORCING_INPUT",
                "state_key": f"example-demand@{LOAD_MILL}",
                "execution_requirement": "REQUIRED",
                "ownership": {
                    "owner": "SCENARIO_INPUT",
                    "initializes": False,
                },
            }
        ],
    }
    document["timeline"].append(mill)
    return document
