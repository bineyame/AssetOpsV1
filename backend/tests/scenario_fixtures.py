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
        "public_parameters": [
            {
                "parameter_id": "quantity-parameter",
                "display_name": "A quantity the scenario assumes",
                "value": 42,
                "unit": "kW",
            },
            {
                "parameter_id": "text-parameter",
                "display_name": "A phrase the scenario carries",
                "value": "measured at the metering point",
                "unit": None,
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
                "parameters": [
                    {
                        "parameter_id": "peak-demand",
                        "display_name": "Peak demand",
                        "value": 64,
                        "unit": "kW",
                    }
                ],
            },
            {
                "event_id": "second-entry",
                "sequence": 2,
                "offset_minutes": 120,
                "entry_kind": "INTERVENTION",
                "category": "MAINTENANCE",
                "description": "A technician records a reading by hand.",
                "parameters": [],
            },
            {
                "event_id": "third-entry",
                "sequence": 3,
                "offset_minutes": 240,
                "entry_kind": "EVIDENCE_CONDITION",
                "category": "DATA_QUALITY",
                "description": "Reported values resume after a gap.",
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
