"""The persisted Foundation API (S1-01).

Three routes under the existing `/api/sites/{site_id}` mount, for Sites
imported into the product Foundation store:

* `GET  /api/sites/{site_id}/foundation?at=&knowledge_at=` - the revision
  effective at `at` (valid time) as recorded at `knowledge_at` (recorded
  time). Both instants are resolved on the server, default to server now and
  are returned. No effective revision is an explicit 404; the current
  configuration is never substituted.
* `GET  /api/sites/{site_id}/foundation/versions` - every persisted revision
  with its effective and recorded periods, for period selection.
* `POST /api/sites/{site_id}/foundation/revisions` - publish one change to the
  battery `reserve-state-of-charge`, and nothing else, in this release.

The tenant is the configured development tenant, resolved here at the request
boundary. Nothing the client sends (header, query or body) names a tenant.
An unimported code answers `FOUNDATION_MIGRATION_REQUIRED`; there is no
fabricated Postgres version for a legacy Site.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, HTTPException

from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_content import (
    RESERVE_PROPERTY_KEY,
    RESERVE_UNIT,
    battery_reserve,
    configuration_gaps,
)
from assetops_backend.sites.foundation_records import (
    FoundationOverlap,
    FoundationStoreError,
    RevisionRow,
    StoredSite,
    TenantRef,
)
from assetops_backend.sites.foundation_service import (
    FoundationRefused,
    FoundationView,
    revision_at,
)
from assetops_backend.sites.identity import validate_site_id
from assetops_backend.sites.ports import (
    SiteConfigurationInvalid,
    SiteNotFound,
    SiteRepository,
    SiteRepositoryError,
)
from assetops_backend.sites_api import site_detail

FOUNDATION_ROUTE = "/api/sites/{site_id}/foundation"
FOUNDATION_VERSIONS_ROUTE = "/api/sites/{site_id}/foundation/versions"
FOUNDATION_REVISIONS_ROUTE = "/api/sites/{site_id}/foundation/revisions"

PUBLISH_KEYS = frozenset({"asset_code", "property_key", "value", "unit", "valid_from", "note"})
PUBLISH_REQUIRED = frozenset({"asset_code", "property_key", "value", "unit", "valid_from"})


def _refused(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat().replace("+00:00", "Z")


def parse_instant(value: str, *, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise _refused(
            422, "FOUNDATION_TIME_INVALID", f"{name} {value!r} is not an ISO 8601 instant."
        ) from error
    if parsed.tzinfo is None:
        raise _refused(
            422,
            "FOUNDATION_TIME_INVALID",
            f"{name} {value!r} has no UTC offset; name the instant, e.g. 2026-10-07T12:00:00Z.",
        )
    return parsed


def _period_state(row: RevisionRow, now: datetime) -> str:
    if row.valid_from > now:
        return "FUTURE"
    if row.valid_to is not None and row.valid_to <= now:
        return "PAST"
    return "CURRENT"


def revision_summary(row: RevisionRow, now: datetime) -> dict[str, Any]:
    reserve = battery_reserve(row.content)
    return {
        "revision_id": str(row.id),
        "version": row.version,
        "valid_from": _iso(row.valid_from),
        "valid_to": _iso(row.valid_to),
        "recorded_at": _iso(row.recorded_at),
        "superseded_at": _iso(row.superseded_at),
        "recorded_state": "CURRENT" if row.superseded_at is None else "SUPERSEDED",
        "period_state": _period_state(row, now),
        "origin": row.origin,
        "derived_from_revision_id": (
            None if row.derived_from_revision_id is None else str(row.derived_from_revision_id)
        ),
        "content_sha256": row.content_sha256,
        "schema_version": row.schema_version,
        "change_note": row.change_note,
        "battery_reserve": (
            None if reserve is None else {"value": reserve["value"], "unit": reserve["unit"]}
        ),
    }


def _site_identity(site: StoredSite, tenant: TenantRef) -> dict[str, Any]:
    return {
        "site_uuid": str(site.id),
        "site_code": site.site_code,
        "tenant": tenant.slug,
        "display_name": site.name,
        "site_type": site.site_type,
        "timezone": site.timezone,
        "lifecycle_status": site.lifecycle,
    }


def _property(content: dict[str, Any], component_type: str, key: str) -> dict[str, Any] | None:
    for component in content.get("components") or ():
        if component.get("component_type") != component_type:
            continue
        for item in component.get("properties") or ():
            if item.get("property_key") == key:
                return {"asset_code": component["component_id"], **item}
    return None


def _controls(view: FoundationView, asset_ids: dict[str, str]) -> dict[str, Any]:
    content = view.revision.content
    authority = f"Foundation v{view.revision.version}"
    reserve = battery_reserve(content)
    runtime = _property(content, "GENERATOR", "minimum-runtime")
    site_controls = {c["control_key"]: c for c in content.get("site_controls") or ()}

    def priority(key: str) -> dict[str, Any]:
        control = site_controls.get(key)
        if control is None:
            return {"state": "NOT_CONFIGURED", "editable": False}
        return {
            "state": "CONFIGURED",
            "members": list(control["members"]),
            "source": control.get("source"),
            "authority": authority,
            "editable": False,
        }

    return {
        "battery_reserve": (
            {"state": "NOT_CONFIGURED", "editable": True}
            if reserve is None
            else {
                "state": "CONFIGURED",
                "asset_code": reserve["asset_code"],
                "asset_id": asset_ids.get(reserve["asset_code"]),
                "property_key": RESERVE_PROPERTY_KEY,
                "value": reserve["value"],
                "unit": reserve["unit"],
                "source": reserve["source"],
                "source_version": reserve["source_version"],
                "authority": authority,
                "editable": True,
            }
        ),
        "generator_minimum_runtime": (
            {"state": "NOT_CONFIGURED", "editable": False}
            if runtime is None
            else {
                "state": "DECLARED",
                "asset_code": runtime["asset_code"],
                "value": runtime["value"],
                "unit": runtime["unit"],
                "authority": authority,
                "editable": False,
            }
        ),
        "generator_start_stop": {
            "state": "NOT_CONFIGURED",
            "editable": False,
            "message": "This Foundation declares no generator start or stop threshold.",
        },
        "source_priority": priority("source-priority"),
        "critical_load_priority": priority("critical-load-priority"),
    }


def foundation_payload(view: FoundationView) -> dict[str, Any]:
    site, revision, regs = view.site, view.revision, view.registrations
    asset_ids = {asset.asset_code: str(asset.id) for asset in regs.assets}
    asset_codes = {str(asset.id): asset.asset_code for asset in regs.assets}
    current = revision_at(view.revisions, view.now, view.now)
    original = next((row for row in view.revisions if row.origin == "IMPORT"), None)
    record = site.import_record
    devices = {d["device_id"]: d for d in revision.content.get("devices") or ()}
    gaps = configuration_gaps(site, revision, regs)
    return {
        "resolved": {"at": _iso(view.at), "knowledge_at": _iso(view.knowledge_at), "server_now": _iso(view.now)},
        "site": _site_identity(site, view.tenant),
        "revision": {
            **revision_summary(revision, view.now),
            "is_current": current is not None and current.id == revision.id,
            "current_revision_id": None if current is None else str(current.id),
        },
        "provenance": {
            "import_id": None if record is None else str(record.id),
            "source_path": None if record is None else record.source_path,
            "source_sha256": None if record is None else record.source_sha256,
            "source_format": None if record is None else record.source_format,
            "imported_at": None if record is None else _iso(record.imported_at),
            "imported_revision_id": None if original is None else str(original.id),
            "imported_version": None if original is None else original.version,
        },
        "detail": site_detail(view.record),
        "assets": [
            {
                "asset_id": str(asset.id),
                "asset_code": asset.asset_code,
                "asset_type": asset.asset_type,
                "display_name": asset.attributes.get("display_name"),
            }
            for asset in regs.assets
        ],
        "gateways": [
            {
                "gateway_id": str(gateway.id),
                "gateway_external_id": gateway.gateway_external_id,
                "mode": gateway.mode,
                "status": "PENDING",
                "credential": "PROVISIONED" if gateway.credential_ref else "NOT_PROVISIONED",
                "registered_at": _iso(gateway.registered_at),
                "disabled_at": _iso(gateway.disabled_at),
            }
            for gateway in regs.gateways
        ],
        "sources": [
            {
                "source_id": str(source.id),
                "gateway_id": str(source.gateway_id),
                "source_external_id": source.source_external_id,
                "device_kind": source.device_kind,
                "display_name": devices.get(source.source_external_id, {}).get("display_name"),
                "asset_id": str(source.asset_id),
                "asset_code": asset_codes.get(str(source.asset_id)),
                "status": "PENDING",
                "registered_at": _iso(source.registered_at),
            }
            for source in regs.sources
        ],
        "controls": _controls(view, asset_ids),
        "bindings": {
            "state": "INCOMPLETE",
            "legacy_signal_mapping_count": len(revision.content.get("signal_mappings") or ()),
            "statement": (
                "Signal roles, units and conversions are not bound yet. The imported "
                "signal mappings are kept for comparison only and authorize no reading."
            ),
        },
        "acquisition_snapshot": {
            "available": False,
            "reason": "No signal binding set is published, so no gateway snapshot can be downloaded.",
        },
        "evidence": {
            "state": "NONE",
            "statement": "No accepted evidence is linked to this Foundation and no live source is claimed.",
        },
        "configuration_gaps": [item.to_wire() for item in gaps],
    }


def build_foundation_router(registry: ImportedSiteRegistry, legacy: SiteRepository) -> APIRouter:
    router = APIRouter(tags=["foundation"])

    def resolve(site_id: str) -> tuple[TenantRef, StoredSite]:
        try:
            validate_site_id(site_id)
        except SiteConfigurationInvalid as error:
            raise _refused(404, "SITE_NOT_FOUND", str(error)) from error
        if registry.service is None:
            raise _refused(
                503,
                "FOUNDATION_STORE_UNCONFIGURED",
                "This build has no product Foundation store composed.",
            )
        try:
            tenant = registry.service.tenant()
            site = registry.service.site(tenant, site_id)
        except FoundationStoreError as error:
            raise _refused(503, "FOUNDATION_STORE_UNAVAILABLE", str(error)) from error
        if site is not None:
            return tenant, site
        try:
            legacy.get_site(site_id)
        except SiteNotFound as error:
            raise _refused(404, "SITE_NOT_FOUND", f"No Site {site_id} is configured.") from error
        except SiteRepositoryError as error:
            raise _refused(503, "SITE_STORE_UNAVAILABLE", str(error)) from error
        raise _refused(
            409,
            "FOUNDATION_MIGRATION_REQUIRED",
            f"Site {site_id} is still a legacy file-backed Site. It has no persisted "
            "Foundation version until it is explicitly imported.",
        )

    def guarded(work):
        try:
            return work()
        except FoundationRefused as error:
            raise _refused(error.status, error.code, error.message) from error
        except FoundationOverlap as error:
            raise _refused(409, "FOUNDATION_OVERLAP", str(error)) from error
        except FoundationStoreError as error:
            raise _refused(503, "FOUNDATION_STORE_UNAVAILABLE", str(error)) from error
        except SiteConfigurationInvalid as error:
            raise _refused(503, "FOUNDATION_CONTENT_INVALID", str(error)) from error

    @router.get(FOUNDATION_ROUTE)
    def read_foundation(site_id: str, at: str | None = None, knowledge_at: str | None = None) -> dict[str, Any]:
        resolved_at = None if at is None else parse_instant(at, name="at")
        resolved_knowledge = None if knowledge_at is None else parse_instant(knowledge_at, name="knowledge_at")
        tenant, site = resolve(site_id)
        return guarded(
            lambda: foundation_payload(registry.service.read(site, tenant, resolved_at, resolved_knowledge))
        )

    @router.get(FOUNDATION_VERSIONS_ROUTE)
    def list_versions(site_id: str) -> dict[str, Any]:
        tenant, site = resolve(site_id)

        def work() -> dict[str, Any]:
            now = registry.service.now()
            rows = sorted(
                registry.service.store.revisions(tenant.id, site.id),
                key=lambda row: (row.valid_from, row.version),
            )
            current = revision_at(rows, now, now)
            return {
                "site": _site_identity(site, tenant),
                "server_now": _iso(now),
                "current_revision_id": None if current is None else str(current.id),
                "revisions": [revision_summary(row, now) for row in rows],
            }

        return guarded(work)

    @router.post(FOUNDATION_REVISIONS_ROUTE, status_code=201)
    def publish_revision(site_id: str, body: Any = Body(...)) -> dict[str, Any]:
        if not isinstance(body, dict):
            raise _refused(422, "FOUNDATION_REQUEST_INVALID", "The request body must be a JSON object.")
        unknown = set(body) - PUBLISH_KEYS
        missing = PUBLISH_REQUIRED - set(body)
        if unknown or missing:
            raise _refused(
                422,
                "FOUNDATION_REQUEST_INVALID",
                f"Unknown fields {sorted(unknown)}; missing fields {sorted(missing)}.",
            )
        if body["property_key"] != RESERVE_PROPERTY_KEY:
            raise _refused(
                422,
                "FOUNDATION_CHANGE_UNSUPPORTED",
                "Only the battery reserve-state-of-charge can be published in this release; "
                "source and critical-load priority are read-only.",
            )
        value = body["value"]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise _refused(422, "FOUNDATION_VALUE_INVALID", "value must be a number.")
        if body["unit"] != RESERVE_UNIT:
            raise _refused(
                422, "FOUNDATION_VALUE_INVALID", f"The reserve state of charge is stated in {RESERVE_UNIT!r}."
            )
        note = body.get("note")
        if note is not None and (not isinstance(note, str) or len(note) > 500):
            raise _refused(422, "FOUNDATION_REQUEST_INVALID", "note must be text of at most 500 characters.")
        if not isinstance(body["valid_from"], str):
            raise _refused(422, "FOUNDATION_TIME_INVALID", "valid_from must be an ISO 8601 instant.")
        effective_from = parse_instant(body["valid_from"], name="valid_from")
        if effective_from.microsecond:
            raise _refused(422, "FOUNDATION_TIME_INVALID", "valid_from must be a whole second.")
        tenant, site = resolve(site_id)

        def work() -> dict[str, Any]:
            regs = registry.service.store.registrations(tenant.id, site.id)
            if body["asset_code"] not in {asset.asset_code for asset in regs.assets}:
                raise FoundationRefused(
                    "FOUNDATION_REFERENCE_OUTSIDE_SITE",
                    f"Asset {body['asset_code']!r} is not registered to Site {site.site_code}.",
                    status=422,
                )
            result = registry.service.publish_battery_reserve(
                tenant,
                site,
                asset_code=body["asset_code"],
                value=float(value),
                effective_from=effective_from,
                note=note,
            )
            now = registry.service.now()
            return {
                "site": _site_identity(site, tenant),
                "revision": revision_summary(result.changed, now),
                "inserted": [revision_summary(row, now) for row in result.plan.inserts],
                "superseded_revision_ids": [str(rid) for rid in result.plan.supersede_ids],
            }

        return guarded(work)

    return router
