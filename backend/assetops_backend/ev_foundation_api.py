"""W2-05a selected EV Foundation read (`.agent/W2-05a-build-spec.md` "Role set, binding and selected read").

`GET /api/sites/{site_code}/ev/foundation?at=<UTC>` - the effective Foundation revision and binding set at `at`
(default: the existing current-selection rule) of an EV_CHARGING Site: feed and limit, chargers and connectors
with their ratings and enable schedule, topology, bindings with their Foundation-derived cadence, readiness,
gateway contact and commissioning (always `UNCONFIRMED` until a commissioning record exists). Configuration
only: no charging, energy or charger-health claim, and contact is source contact, not charger health.

Refusals use the shared envelope `{error:{code,message}}` through the cold selected-read Access/source gate:
401 `UNAUTHENTICATED`, 403 `SITE_SCOPE_FORBIDDEN`, 404 `SITE_NOT_FOUND` (unknown, foreign or non-EV Site, checked
after access), 422 `EV_SELECTION_INVALID` (malformed `at` or any other query field), 503
`EV_FOUNDATION_UNAVAILABLE` (Foundation or gateway store unreadable). No revision at `at` passes the Foundation
service's own refusal through, as the cold read does.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from assetops_backend.evidence.gateway_access import freshness
from assetops_backend.evidence.ledger import LedgerUnavailable
from assetops_backend.finding_api import Access, development_access
from assetops_backend.sites.cold_foundation import (
    CONTACT_HEALTH_ABSENT,
    CONTACT_NO_DIAGNOSTIC,
    CONTACT_NO_GATEWAY_REGISTERED,
    CONTACT_NO_GATEWAY_SELECTED,
    ContactFacts,
    _iso,
    assets_by_code,
    contact_document,
)
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.ev_foundation import EV_SITE_TYPE, ev_foundation_document
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.foundation_service import FoundationRefused
from assetops_backend.sites.ports import SiteStoreUnavailable

EV_FOUNDATION_ROUTE = "/api/sites/{site_code}/ev/foundation"
QUERY_KEYS = frozenset({"at"})
UNAVAILABLE = "EV_FOUNDATION_UNAVAILABLE"


def _refusal(status: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}}, headers=headers)


def ev_contact(facts: ContactFacts | None, absent: str, gateway_id: Any, checked_at: datetime) -> dict[str, Any]:
    """Spec contact mapping: S7 CURRENT -> RECENT, STALE -> STALE, absent diagnostic -> NEVER with a reason and
    null `as_of`; the selected gateway comes from registration. Per-source contact is unavailable in 05a.
    QL: `checked_at` is the server's request-time UTC check, independent of the selected configuration `at`."""
    document = contact_document(facts, absent)
    reason = document["limitations"][0] if document["limitations"] else None
    if document["state"] == "NEVER" and reason is None:
        reason = CONTACT_NO_DIAGNOSTIC
    return {"state": document["state"], "as_of": document["as_of"], "checked_at": _iso(checked_at),
            "gateway_id": None if gateway_id is None else str(gateway_id), "reason": reason}


def build_ev_foundation_router(registry: ImportedSiteRegistry, health_store: Any | None,
                               clock: Callable[[], datetime], access: Access = development_access) -> APIRouter:
    router = APIRouter()

    @router.get(EV_FOUNDATION_ROUTE)
    def ev_foundation(request: Request, site_code: str) -> Any:
        refusal = access(request, site_code)
        if refusal == 401:
            return _refusal(401, "UNAUTHENTICATED", "Sign in to read Site configuration.",
                            {"WWW-Authenticate": "Bearer"})
        if refusal == 403:
            return _refusal(403, "SITE_SCOPE_FORBIDDEN", f"No access to Site {site_code!r}.")
        unknown = sorted(set(request.query_params) - QUERY_KEYS)
        if unknown or len(request.query_params.getlist("at")) > 1:
            return _refusal(422, "EV_SELECTION_INVALID", f"Unknown or repeated parameters {unknown or ['at']}; "
                            "only one 'at' is accepted.")
        at: datetime | None = None
        raw_at = request.query_params.get("at")
        if raw_at is not None:
            try:
                at = datetime.fromisoformat(raw_at.replace("Z", "+00:00"))
            except ValueError:
                at = None
            if at is None or at.tzinfo is None or at.utcoffset() != timezone.utc.utcoffset(None):
                return _refusal(422, "EV_SELECTION_INVALID",
                                "'at' must be a UTC instant such as 2026-10-06T12:00:00Z.")
        service = registry.service
        try:
            site = registry.imported(site_code)
            if site is not None and service is None:
                return _refusal(503, UNAVAILABLE, "No product Foundation store is configured.")
            tenant = registry.tenant() if site is not None else None
            if site is None or tenant is None or site.site_type != EV_SITE_TYPE:
                return _refusal(404, "SITE_NOT_FOUND", f"No EV charging Site {site_code!r} in this tenant.")
            view = service.read(site, tenant, at, None)
        except (SiteStoreUnavailable, FoundationStoreError) as error:
            return _refusal(503, UNAVAILABLE, str(error))
        except FoundationRefused as error:
            return _refusal(error.status, error.code, str(error))
        gateways = view.registrations.gateways
        wanted = view.binding_set.gateway_id if view.binding_set is not None else (
            gateways[0].id if len(gateways) == 1 else None)
        checked_at = clock()
        facts: ContactFacts | None = None
        absent = CONTACT_HEALTH_ABSENT
        if health_store is not None:
            try:
                health = health_store.gateway_health(tenant.id, site.id)
            except LedgerUnavailable as error:
                return _refusal(503, UNAVAILABLE, str(error))
            if wanted is None:
                absent = CONTACT_NO_GATEWAY_SELECTED if gateways else CONTACT_NO_GATEWAY_REGISTERED
            else:
                absent = CONTACT_NO_DIAGNOSTIC
                selected = next((f for f in health if f.gateway_id == wanted), None)
                if selected is not None:
                    received = None if selected.latest is None else selected.latest.received_at
                    facts = ContactFacts(received, freshness(received, selected.cadence_seconds, checked_at))
        return ev_foundation_document(
            site=site,
            selected_at=view.at,
            revision=view.revision,
            binding_set=view.binding_set,
            assets_by_code=assets_by_code(view.registrations.assets),
            contact=ev_contact(facts, absent, wanted, checked_at),
        )

    return router
