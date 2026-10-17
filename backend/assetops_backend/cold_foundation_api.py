"""W2-01 selected cold Foundation read (`.agent/W2-technical-design-cold.md` section 3 and the route row).

`GET /api/sites/{site_code}/cold/foundation?at=<UTC>` - the effective Foundation revision and binding set at
`at` (default now) of a COLDCHAIN Site: rooms with policy band, topology, bindings with the fixed
`cold-roles-1` cadence, configuration readiness, commissioning (always `UNCONFIRMED` until a commissioning
record exists) and gateway contact. Configuration only: no temperature, start or equipment-health claim.

Refusals use the shared envelope `{error:{code,message}}`: 401 / 403 through the Finding route access seam,
404 for an unknown, foreign or non-COLDCHAIN Site or no revision at `at`, 422 for a malformed `at` or an
unknown parameter, 503 when the Foundation or gateway store cannot be read.
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
    COLD_SITE_TYPE,
    ContactFacts,
    assets_by_code,
    cold_foundation_document,
)
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.foundation_service import FoundationRefused
from assetops_backend.sites.ports import SiteStoreUnavailable

COLD_FOUNDATION_ROUTE = "/api/sites/{site_code}/cold/foundation"
QUERY_KEYS = frozenset({"at"})


def _refusal(status: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}}, headers=headers)


def build_cold_foundation_router(registry: ImportedSiteRegistry, health_store: Any | None,
                                 clock: Callable[[], datetime], access: Access = development_access) -> APIRouter:
    router = APIRouter()

    @router.get(COLD_FOUNDATION_ROUTE)
    def cold_foundation(request: Request, site_code: str) -> Any:
        refusal = access(request, site_code)
        if refusal == 401:
            return _refusal(401, "UNAUTHENTICATED", "Sign in to read Site configuration.",
                            {"WWW-Authenticate": "Bearer"})
        if refusal == 403:
            return _refusal(403, "SITE_SCOPE_FORBIDDEN", f"No access to Site {site_code!r}.")
        unknown = sorted(set(request.query_params) - QUERY_KEYS)
        if unknown:
            return _refusal(422, "COLD_PARAMETER_UNKNOWN", f"Unknown parameters {unknown}; only 'at' is accepted.")
        at: datetime | None = None
        raw_at = request.query_params.get("at")
        if raw_at is not None:
            try:
                at = datetime.fromisoformat(raw_at.replace("Z", "+00:00"))
            except ValueError:
                at = None
            if at is None or at.tzinfo is None or at.utcoffset() != timezone.utc.utcoffset(None):
                return _refusal(422, "COLD_TIME_INVALID", "'at' must be a UTC instant such as 2026-10-17T19:00:00Z.")
        service = registry.service
        try:
            site = registry.imported(site_code)
            if site is not None and service is None:
                return _refusal(503, "COLD_FOUNDATION_UNAVAILABLE", "No product Foundation store is configured.")
            tenant = registry.tenant() if site is not None else None
            if site is None or tenant is None or site.site_type != COLD_SITE_TYPE:
                return _refusal(404, "SITE_NOT_FOUND", f"No cold-chain Site {site_code!r} in this tenant.")
            view = service.read(site, tenant, at, None)
        except (SiteStoreUnavailable, FoundationStoreError) as error:
            return _refusal(503, "COLD_FOUNDATION_UNAVAILABLE", str(error))
        except FoundationRefused as error:
            return _refusal(error.status, error.code, str(error))
        contact: ContactFacts | None = None
        if health_store is not None:
            try:
                facts = health_store.gateway_health(tenant.id, site.id)
            except LedgerUnavailable as error:
                return _refusal(503, "GATEWAY_ACCESS_UNAVAILABLE", str(error))
            wanted = view.binding_set.gateway_id if view.binding_set is not None else (
                view.registrations.gateways[0].id if len(view.registrations.gateways) == 1 else None)
            selected = next((f for f in facts if f.gateway_id == wanted), None)
            if selected is not None:
                received = None if selected.latest is None else selected.latest.received_at
                contact = ContactFacts(received, freshness(received, selected.cadence_seconds, clock()))
        return cold_foundation_document(
            revision=view.revision,
            binding_set=view.binding_set,
            assets_by_code=assets_by_code(view.registrations.assets),
            contact=contact,
        )

    return router
