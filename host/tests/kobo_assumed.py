"""0K4b (D-0K4.7): the values Kobo has not sent yet, assumed for `mini-grid` v8 runs and labelled as such.

A test fixture only: the shipped template (`config/site-templates/kobo-mini-grid-60kw.yaml`) is unchanged. Every
assumed value travels with its basis row, `GENERIC_DEFAULT`, so a run made with it says where the number came from.
`specific-fuel-consumption` stays the template's 0.3 L/kWh, read by the curve as the full-load consumption (D-0K4.5).
"""

from __future__ import annotations

from typing import Any

from kobo import component

ASSUMED_BASIS = "GENERIC_DEFAULT"
ASSUMED_PROPERTIES: dict[str, tuple[tuple[str, Any, str], ...]] = {
    "generator": (
        ("generator-no-load-fuel-rate", 3.3, "L/h"),
        ("generator-no-load-fuel-rate-basis", ASSUMED_BASIS, "state"),
        ("generator-minimum-load", 30, "%"),
        ("generator-minimum-load-basis", ASSUMED_BASIS, "state"),
    ),
    "battery": (
        ("battery-charge-taper-start", 95, "%"),
        ("battery-charge-taper-start-basis", ASSUMED_BASIS, "state"),
    ),
}
ASSUMPTION_NOTE = (
    "assumed until Kobo's sheets arrive: generic no-load fuel rate 3.3 L/h for a 40 kW set (owner value "
    "2026-11-07), minimum load 30 % of rating, lithium iron phosphate battery tapering above 95 %"
)


def assumed_site(document: dict[str, Any]) -> None:
    """Append the assumed rows to a rendered Kobo site document; a key already present is `KeyError`."""
    for component_id, rows in ASSUMED_PROPERTIES.items():
        item = component(document, component_id)
        properties = item.get("properties") or []
        present = {entry["property_key"] for entry in properties}
        for key, value, unit in rows:
            if key in present:
                raise KeyError(f"{key} is already declared on {component_id}; an assumed value never overwrites it")
            properties.append(
                {"property_key": key, "value": value, "unit": unit, "source": "SITE", "source_version": 1}
            )
        item["properties"] = properties
