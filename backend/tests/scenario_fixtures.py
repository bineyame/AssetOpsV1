"""The canonical scenario document the scenario tests mutate.

One valid document, built fresh on every call, which every strict-validation
test starts from and breaks in exactly one way. That is what makes a refusal
test about the rule it names: if each test built its own document, a test could
pass because the document was malformed in a second way the parser happened to
reach first.

This module is also a scanned artifact. The breaker/control vocabulary guard in
`test_scenario_vocabulary.py` reads the document below alongside the shipped
definition and the scenario domain model, because a fixture is where a banned
term would most plausibly arrive first: a test needs a value, and the shipped
document is the one place an author would think twice.

It deliberately is NOT a copy of `config/scenarios/fuel-loss-event.yaml`. A
fixture that mirrored the shipped document would make every parser test a test
of the shipped content, and the shipped content would then be unable to change
without the parser suite changing with it. This is a small, generic scenario
that exercises the same shapes.

T020A1's review round addressed it. Every state it names is either a fact
about the site's one declared component, `example-store`, or a fact about the
installation - because a component-scoped reference has to identify one
component before a run is READY, and a bare key against a profile that
declares no binding for it identifies nothing. It was written with bare keys
and passed only because that obligation was missing.

T018 gives it one more job. It exercises every execution role, every timing
shape, both observation source kinds, and both kinds of state effect, so a
parser test can break exactly one of those and nothing else. Its numbers are
deliberately CONSISTENT - the declared causes reach the level the reading
reports exactly - so that a reconciliation test can prove both answers: this
document reconciles, and a one-value mutation of it does not. The shipped Fuel
Loss Event does not reconcile, and a fixture that also did not would leave
`ACCOUNTED_FOR` untested.
"""

from __future__ import annotations

from typing import Any


def scenario_document() -> dict[str, Any]:
    """A valid scenario document, fresh each call."""
    return {
        "scenario_id": "example-scenario",
        "display_name": "Example scenario",
        "purpose": "Exercise the scenario document shapes the parser accepts.",
        "version": {
            "scenario_version": 2,
            "version_valid_from": "2026-01-01T00:00:00Z",
            "supersedes": 1,
        },
        "target_site": {
            "policy": "DECLARED_SITE",
            "site_id": "MG-900",
            "template_id": None,
            "requirement": "A mini-grid with a metered distribution load.",
        },
        "observation_sources": [
            {
                "source_id": "example-device-reading",
                "source_kind": "DEVICE_SIGNAL",
                "device_id": "example-sensor",
                "signal_id": "example-level",
                "cadence_ownership": "NOT_DECLARED",
                "description": "A configured sensor reporting a stored level.",
            },
            {
                "source_id": "example-hand-record",
                "source_kind": "OPERATOR_RECORD",
                "cadence_ownership": "NOT_APPLICABLE",
                "description": "A technician reading the same quantity by hand.",
            },
        ],
        "public_parameters": [
            {
                "parameter_id": "quantity-parameter",
                "display_name": "A quantity the scenario assumes",
                "value": 42,
                "unit": "kW",
                "execution_role": "NON_EXECUTABLE_CONDITION",
            },
            {
                "parameter_id": "text-parameter",
                "display_name": "A phrase the scenario carries",
                "value": "measured at the metering point",
                "unit": None,
                "execution_role": "NON_EXECUTABLE_CONDITION",
            },
            {
                "parameter_id": "starting-level",
                "display_name": "Stored level at the start of the interval",
                "value": 200,
                "unit": "L",
                "execution_role": "CAUSAL_INPUT",
                "state_key": "example-stored-volume@example-store",
                "execution_requirement": "REQUIRED",
                "ownership": {"owner": "SCENARIO_INPUT", "initializes": True},
            },
            {
                "parameter_id": "draw-rate",
                "display_name": "Draw while the equipment runs",
                "value": 6,
                "unit": "L/h",
                "execution_role": "CAUSAL_INPUT",
                "state_key": "example-stored-volume@example-store",
                "execution_requirement": "REQUIRED",
                "ownership": {"owner": "SCENARIO_INPUT", "initializes": False},
            },
        ],
        "timeline": [
            {
                "event_id": "first-entry",
                "sequence": 1,
                "offset_minutes": 0,
                "entry_kind": "EVENT",
                "category": "LOAD",
                "description": "Demand follows the site's ordinary shape.",
                "execution_role": "FORCING_INPUT",
                "state_key": "site:example-demand",
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "INTERVAL_WIDE"},
                "parameters": [
                    {
                        "parameter_id": "peak-demand",
                        "display_name": "Peak demand",
                        "value": 64,
                        "unit": "kW",
                        "execution_role": "FORCING_INPUT",
                        "state_key": "site:example-demand",
                        "execution_requirement": "REQUIRED",
                        "ownership": {
                            "owner": "SCENARIO_INPUT",
                            "initializes": False,
                        },
                    }
                ],
            },
            {
                "event_id": "draw-window",
                "sequence": 2,
                "offset_minutes": 60,
                "entry_kind": "EVENT",
                "category": "EQUIPMENT",
                "description": "The equipment runs and draws at the declared rate.",
                "execution_role": "CAUSAL_INPUT",
                "state_key": "example-stored-volume@example-store",
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "WINDOW", "duration_minutes": 60},
                "state_effect": {
                    "direction": "DECREASE",
                    "rate_parameter_id": "draw-rate",
                },
                "parameters": [],
            },
            {
                "event_id": "second-entry",
                "sequence": 3,
                "offset_minutes": 120,
                "entry_kind": "INTERVENTION",
                "category": "MAINTENANCE",
                "description": "A technician records a reading by hand.",
                "execution_role": "REPORTED_OBSERVATION",
                "state_key": "example-stored-volume@example-store",
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "POINT"},
                "observation": {
                    "source_id": "example-hand-record",
                    "reported_parameter_id": "recorded-level",
                },
                "parameters": [
                    {
                        "parameter_id": "recorded-level",
                        "display_name": "Level the technician records",
                        # 200 L minus six litres an hour for one hour. The
                        # document reconciles exactly, so a test can prove
                        # both answers rather than only the unhappy one.
                        "value": 194,
                        "unit": "L",
                        "execution_role": "REPORTED_OBSERVATION",
                        "state_key": "example-stored-volume@example-store",
                        "execution_requirement": "REQUIRED",
                    }
                ],
            },
            {
                "event_id": "third-entry",
                "sequence": 4,
                "offset_minutes": 240,
                "entry_kind": "EVIDENCE_CONDITION",
                "category": "DATA_QUALITY",
                "description": "Reported values resume after a gap.",
                "execution_role": "REPORTED_OBSERVATION",
                "state_key": "example-stored-volume@example-store",
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "POINT"},
                "observation": {
                    "source_id": "example-device-reading",
                    "reported_parameter_id": "resumed-level",
                },
                "parameters": [
                    {
                        "parameter_id": "resumed-level",
                        "display_name": "Level when reporting resumes",
                        "value": 194,
                        "unit": "L",
                        "execution_role": "REPORTED_OBSERVATION",
                        "state_key": "example-stored-volume@example-store",
                        "execution_requirement": "REQUIRED",
                    }
                ],
            },
        ],
        "private_expectations": [
            {
                "expectation_id": "an-expectation",
                "display_name": "Something a later test must conclude",
                "oracle_kind": "DETECTION",
                "statement": "A later analysis separates the cause from noise.",
            }
        ],
    }
