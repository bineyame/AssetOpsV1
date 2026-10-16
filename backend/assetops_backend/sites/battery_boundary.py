"""Configured-battery boundary read (S7-01a, `I-asset-boundary-read`, `D-2026-10-16-a-s7-health`).

Resolves the battery from the effective S1 Site basis (Foundation revision + binding set revision)
and discloses the selected IDs. W1 has no reviewed causal battery observation or rule, so physical
condition is always `UNKNOWN` with the named missing causal inputs; an absent battery is
`NOT_CONFIGURED`. Declared nameplate appears only as a declared Foundation fact; bound channels
(such as state of charge) appear only as binding IDs. Neither proves degradation or remaining life.
Degradation, remaining life, stress score, warranty/replacement exposure and diagnosis are withheld.

An asset ID that is not a battery component of the effective basis (foreign Site, unknown,
non-battery, or present only in a superseded revision) is `AssetNotInBasis`, which the route
answers 404: never a healthy or Unknown row for that ID.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from assetops_backend.sites.foundation_service import FoundationView

SCHEMA = {"id": "assetops.asset-boundary", "version": 1}
RULE_ID = "assetops.battery-condition-boundary.w1"
BATTERY_TYPE = "BATTERY"
WITHHELD = ["DEGRADATION", "REMAINING_LIFE", "STRESS_SCORE", "WARRANTY_EXPOSURE", "REPLACEMENT_EXPOSURE",
            "DIAGNOSIS"]
#: The causal inputs a battery physical-condition rule would need; none is accepted in W1.
MISSING_CAUSAL_INPUTS = (
    ("ACCEPTED_BATTERY_TEMPERATURE_HISTORY",
     "No battery temperature role is defined or bound, so no accepted temperature history exists."),
    ("ACCEPTED_MEASURED_CAPACITY",
     "No accepted capacity test or measured usable-capacity evidence exists; the declared rating is not a "
     "measurement."),
    ("ACCEPTED_CYCLE_STRESS_HISTORY",
     "No reviewed stress rule over accepted charge/discharge history exists."),
)


class AssetNotInBasis(Exception):
    """The asset ID is not a battery of the effective Site basis."""


def _z(instant: datetime) -> str:
    return instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def configured_batteries(view: FoundationView) -> list[dict[str, Any]]:
    """Battery components of the effective Foundation revision, with their registered asset rows."""
    components = {c["component_id"]: c for c in view.revision.content.get("components", ())
                  if c.get("component_type") == BATTERY_TYPE}
    batteries = []
    for asset in sorted(view.registrations.assets, key=lambda a: a.asset_code):
        if asset.asset_type == BATTERY_TYPE and asset.asset_code in components:
            batteries.append({"asset": asset, "component": components[asset.asset_code]})
    return batteries


def _basis(view: FoundationView) -> dict[str, Any]:
    bs = view.binding_set
    return {
        "foundation_revision_id": str(view.revision.id),
        "foundation_version": view.revision.version,
        "binding_set_revision_id": None if bs is None else str(bs.id),
        "binding_set_version": None if bs is None else bs.version,
        "binding_set_foundation_revision_id": None if bs is None else str(bs.foundation_revision_id),
        "effective_at": _z(view.at),
        "knowledge_at": _z(view.knowledge_at),
    }


def _envelope(view: FoundationView, read_at: datetime, access_basis: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "rule_id": RULE_ID, "site_code": view.site.site_code, "site_id": str(view.site.id),
        "read_at": _z(read_at), "read_at_clock": "SERVER_REAL_UTC", "access_basis": access_basis,
        "claim_scope": "CONFIGURED_ASSET_BOUNDARY", "basis": _basis(view), "withheld": WITHHELD,
    }


def _unknown(reason: str, missing: list[dict[str, str]]) -> dict[str, Any]:
    return {"status": "UNKNOWN", "reason": reason, "missing_causal_inputs": missing}


def battery_entry(view: FoundationView, read_at: datetime, access_basis: str) -> dict[str, Any]:
    """The Site battery entry: configured battery IDs, or typed `NOT_CONFIGURED` with no asset ID."""
    batteries = configured_batteries(view)
    body = _envelope(view, read_at, access_basis)
    if not batteries:
        return {**body, "configuration": "NOT_CONFIGURED",
                "reason": "NO_BATTERY_IN_EFFECTIVE_FOUNDATION", "batteries": [],
                "physical_condition": _unknown("NOT_CONFIGURED", [])}
    return {**body, "configuration": "CONFIGURED", "reason": None, "batteries": [
        {"asset_id": str(b["asset"].id), "asset_code": b["asset"].asset_code,
         "display_name": b["component"].get("display_name"),
         "detail_path": f"/api/sites/{view.site.site_code}/assets/{b['asset'].id}/battery"}
        for b in batteries]}


def battery_detail(view: FoundationView, asset_id: UUID, read_at: datetime, access_basis: str) -> dict[str, Any]:
    match = next((b for b in configured_batteries(view) if b["asset"].id == asset_id), None)
    if match is None:
        raise AssetNotInBasis(f"Asset {asset_id} is not a battery of the effective basis of {view.site.site_code}.")
    asset, component = match["asset"], match["component"]
    bs = view.binding_set
    bound = [] if bs is None else [b for b in bs.bindings if b.asset_id == asset.id]
    binding_status = "NO_BINDING_SET" if bs is None else "BOUND" if bound else "UNBOUND"
    rating = component.get("rating")
    missing = [{"input": key, "status": "MISSING", "reason": why} for key, why in MISSING_CAUSAL_INPUTS]
    return {
        **_envelope(view, read_at, access_basis),
        "configuration": "CONFIGURED",
        "asset": {"asset_id": str(asset.id), "asset_code": asset.asset_code, "asset_type": asset.asset_type,
                  "display_name": component.get("display_name")},
        "binding_status": binding_status,
        "bound_channels": [{
            "binding_revision_id": str(b.id), "role": b.role, "gateway_id": str(b.gateway_id),
            "source_id": str(b.source_id), "device_id": b.device_id, "signal_id": b.signal_id,
            "label": "BOUND_CHANNEL_NOT_A_CONDITION_INPUT"} for b in sorted(bound, key=lambda b: b.role)],
        "declared_nameplate": None if not rating else {
            "value": rating.get("value"), "unit": rating.get("unit"), "label": "DECLARED_FOUNDATION_RATING",
            "foundation_revision_id": str(view.revision.id), "component_id": asset.asset_code},
        "accepted_state_of_charge": {"included": False,
                                     "reason": "The W1 boundary read selects no accepted SOC value; SOC would "
                                               "not prove physical condition."},
        "physical_condition": _unknown(
            "NO_REVIEWED_CAUSAL_BATTERY_RULE" if binding_status == "BOUND" else binding_status, missing),
    }


__all__ = ["AssetNotInBasis", "RULE_ID", "SCHEMA", "WITHHELD", "battery_detail", "battery_entry",
           "configured_batteries"]
