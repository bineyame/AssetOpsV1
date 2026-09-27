"""A second installation, with a different tank and a different generator.

Criterion 11 asks for a capacity bound taken from the actual frozen Foundation
value "including a second Site with a different capacity", and the point of the
second is that the first could have passed by accident. The shipped hybrid
template declares a 500 litre tank and a 0.311 L/kWh generator, and 500 appears
in the document's own comments, in the test fixtures and in the layout tool. A
kernel that had 500 anywhere in it would look right against that Site.

So this document is addressed to the twin-tank archetype's SOUTH run: an 800
litre tank and a 0.285 L/kWh generator, both declared by the template and neither
appearing anywhere in the kernel. Nothing here states either number - the document
declares only that the Foundation answers - so the trajectory below is evidence
that the bound came from the site rather than from a default.

Its numbers are chosen to reach the capacity from a different direction:

    dispatch    60 kW over [600, 720), eight steps of 15 minutes
    per step    60 kW x 1/4 h = 15 kWh, and 285/1000 x 15 = 171/40 L
    over eight  171/5 = 34.2 L, so the tank is at 3329/5 = 665.8 L at 720
    removal     100 L over [900, 960), four steps of 25 L
    after 960   2829/5 = 565.8 L
    delivery    300 L at 1200 would reach 4329/5 = 865.8 L
    capacity    800 L, so the tank fills and refuses 329/5 = 65.8 L

It is authored here rather than added to `config/scenarios/` because it is a test
fixture. The shipped store is product content, and a document that exists to
prove a kernel property would appear on the scenario catalog screen.
"""

from __future__ import annotations

from typing import Any

SOUTH_TANK = "fuel-tank-volume@south-tank"
SOUTH_CAPACITY = "fuel-tank-capacity@south-tank"
SOUTH_GENERATOR = "generator-output-power@south-generator"
SOUTH_COEFFICIENT = "generator-specific-fuel-consumption@south-generator"

SECOND_SITE_ID = "MG-T21"


def second_site_document() -> dict[str, Any]:
    """A fuel loss on the south run of a twin-tank installation."""
    return {
        "scenario_id": "south-run-fuel-loss",
        "display_name": "South run fuel loss",
        "purpose": (
            "Exercise the same fuel path against a second installation whose "
            "tank and generator are different sizes, so a capacity bound and a "
            "consumption coefficient are shown to come from the configured "
            "asset rather than from anything the kernel carries."
        ),
        "version": {
            "scenario_version": 1,
            "version_valid_from": "2026-09-27T00:00:00Z",
            "supersedes": None,
        },
        "target_site": {
            "policy": "DECLARED_SITE",
            "site_id": SECOND_SITE_ID,
            "template_id": None,
            "requirement": (
                "A mini-grid whose foundation declares two fuel runs, so a "
                "reference has to say which tank and which generator it means."
            ),
        },
        "observation_sources": [
            {
                "source_id": "south-tank-level",
                "source_kind": "DEVICE_SIGNAL",
                "device_id": "south-fuel-sensor",
                "signal_id": "fuel-level",
                "cadence_ownership": "NOT_DECLARED",
                "description": (
                    "The south tank's own level sensor. The north tank has its "
                    "own, and a single sensor reporting the fuel level on this "
                    "site would be a reading nobody could attribute."
                ),
            }
        ],
        "public_parameters": [
            {
                "parameter_id": "south-tank-capacity",
                "display_name": "South tank capacity",
                "unit": "L",
                "execution_role": "CAUSAL_INPUT",
                "state_key": SOUTH_CAPACITY,
                "execution_requirement": "REQUIRED",
                "ownership": {
                    "owner": "SITE_FOUNDATION",
                    "initializes": True,
                },
                "bounds": {
                    "state_key": SOUTH_TANK,
                    "bound_kind": "UPPER",
                },
            },
            {
                "parameter_id": "south-starting-level",
                "display_name": "South tank level at the start",
                "value": 700,
                "unit": "L",
                "execution_role": "CAUSAL_INPUT",
                "state_key": SOUTH_TANK,
                "execution_requirement": "REQUIRED",
                "ownership": {"owner": "SCENARIO_INPUT", "initializes": True},
            },
            {
                "parameter_id": "south-specific-consumption",
                "display_name": "South generator specific fuel consumption",
                "unit": "L/kWh",
                "execution_role": "CAUSAL_INPUT",
                "state_key": SOUTH_COEFFICIENT,
                "execution_requirement": "REQUIRED",
                "ownership": {
                    "owner": "SITE_FOUNDATION",
                    "initializes": True,
                },
            },
        ],
        "timeline": [
            {
                "event_id": "south-dispatch-window",
                "sequence": 1,
                "offset_minutes": 600,
                "entry_kind": "EVENT",
                "category": "EQUIPMENT",
                "description": (
                    "The south generator is dispatched for two hours at the "
                    "declared output."
                ),
                "execution_role": "FORCING_INPUT",
                "state_key": SOUTH_GENERATOR,
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "WINDOW", "duration_minutes": 120},
                "parameters": [
                    {
                        "parameter_id": "south-dispatched-output",
                        "display_name": "South generator output",
                        "value": 60,
                        "unit": "kW",
                        "execution_role": "FORCING_INPUT",
                        "state_key": SOUTH_GENERATOR,
                        "execution_requirement": "REQUIRED",
                        "ownership": {
                            "owner": "SCENARIO_INPUT",
                            "initializes": False,
                        },
                    }
                ],
            },
            {
                "event_id": "south-fuel-removal",
                "sequence": 2,
                "offset_minutes": 900,
                "entry_kind": "EVENT",
                "category": "LOSS_OR_FRAUD",
                "description": (
                    "Fuel leaves the south tank outside any dispatch or "
                    "refuelling window."
                ),
                "execution_role": "CAUSAL_INPUT",
                "state_key": SOUTH_TANK,
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "WINDOW", "duration_minutes": 60},
                "state_effect": {
                    "direction": "DECREASE",
                    "quantity_parameter_id": "south-volume-removed",
                },
                "parameters": [
                    {
                        "parameter_id": "south-volume-removed",
                        "display_name": "Volume removed",
                        "value": 100,
                        "unit": "L",
                        "execution_role": "CAUSAL_INPUT",
                        "state_key": SOUTH_TANK,
                        "execution_requirement": "REQUIRED",
                        "ownership": {
                            "owner": "SCENARIO_INPUT",
                            "initializes": False,
                        },
                    }
                ],
            },
            {
                "event_id": "south-level-reading",
                "sequence": 3,
                "offset_minutes": 1020,
                "entry_kind": "EVIDENCE_CONDITION",
                "category": "LOSS_OR_FRAUD",
                "description": (
                    "The south tank sensor reports a level after the removal."
                ),
                "execution_role": "REPORTED_OBSERVATION",
                "state_key": SOUTH_TANK,
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "POINT"},
                "observation": {
                    "source_id": "south-tank-level",
                    "reported_parameter_id": "south-reported-level",
                },
                "parameters": [
                    {
                        "parameter_id": "south-reported-level",
                        "display_name": "Level the south sensor reports",
                        "value": 565.8,
                        "unit": "L",
                        "execution_role": "REPORTED_OBSERVATION",
                        "state_key": SOUTH_TANK,
                        "execution_requirement": "REQUIRED",
                    }
                ],
            },
            {
                "event_id": "south-scheduled-refuelling",
                "sequence": 4,
                "offset_minutes": 1200,
                "entry_kind": "EVENT",
                "category": "MAINTENANCE",
                "description": (
                    "The scheduled delivery tops the south tank up, and more "
                    "arrives than the tank has room for."
                ),
                "execution_role": "CAUSAL_INPUT",
                "state_key": SOUTH_TANK,
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "POINT"},
                "state_effect": {
                    "direction": "INCREASE",
                    "quantity_parameter_id": "south-volume-delivered",
                },
                "parameters": [
                    {
                        "parameter_id": "south-volume-delivered",
                        "display_name": "Volume delivered",
                        "value": 300,
                        "unit": "L",
                        "execution_role": "CAUSAL_INPUT",
                        "state_key": SOUTH_TANK,
                        "execution_requirement": "REQUIRED",
                        "ownership": {
                            "owner": "SCENARIO_INPUT",
                            "initializes": False,
                        },
                    }
                ],
            },
        ],
        "private_expectations": [
            {
                "expectation_id": "south-bound-follows-the-site",
                "display_name": "The bound follows this site's tank",
                "oracle_kind": "TRAJECTORY",
                "statement": (
                    "The south tank holds 700 L at offset 0, 665.8 L when the "
                    "dispatch window closes at 720, 565.8 L when the removal "
                    "completes at 960, and 800 L at 1200 with 65.8 L of the "
                    "300 L delivery recorded refused against this tank's own "
                    "800 L capacity."
                ),
            }
        ],
    }
