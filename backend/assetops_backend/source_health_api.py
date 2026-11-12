"""S7-01a Site source-health route (`I-source-health-read`, `D-2026-10-16-a-s7-health`).

`GET /api/sites/{site_code}/source-health` - the versioned two-clock DTO of
`evidence/source_health.py`. The S2 `gateway-health` route and contract are unchanged.

Order of checks, so no refusal leaks a gateway, count or current claim:

1. Request identity with the Finding route seam (`finding_api.Access`): 401 / 403; then the tenant
   Site scope: 404 (a foreign or unknown Site is never an empty healthy list).
2. 503 `SOURCE_HEALTH_UNAVAILABLE` without a store or when the central store cannot be read.
3. 409 `SOURCE_HEALTH_SELECTION_INCONSISTENT` when registration and diagnostic selection disagree.
4. 200 with the DTO; an enabled-gateway-free Site is `NO_REGISTERED_SOURCE`, a registered gateway
   never received is `UNKNOWN` contact.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response

from assetops_backend import perf
from assetops_backend.chain.response_store import ResponseStore, StoredRoute, finish
from assetops_backend.estate.scope import EstateRefusal, EstateStoreUnavailable, estate_request

from assetops_backend.evidence.ledger import LedgerUnavailable
from assetops_backend.evidence.source_health import (
    SelectionInconsistent,
    SourceHealthStore,
    source_health_document,
)
from assetops_backend.finding_api import ACCESS_BASIS, Access, Scope, development_access
from assetops_backend.outcome_api import _instant, _public, _refuse
from assetops_backend.sites import site_health_range
from assetops_backend.sites.battery_boundary import battery_entry
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.foundation_service import FoundationRefused
from assetops_backend.sites.ports import SiteStoreUnavailable

ROUTE = "/api/sites/{site_code}/source-health"
HEALTH_RANGE_ROUTE = "/api/sites/{site_code}/health-range"
_UNAVAILABLE = "SITE_HEALTH_RANGE_UNAVAILABLE"


def build_source_health_router(store: SourceHealthStore | None, scope: Scope, clock: Callable[[], datetime],
                               access: Access = development_access, access_basis: str = ACCESS_BASIS
                               ) -> APIRouter:
    router = APIRouter()

    @router.get(ROUTE)
    def source_health(request: Request, site_code: str) -> dict[str, Any]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read Site health."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        try:
            found = scope(site_code)
        except Exception as error:  # noqa: BLE001 - the Site store could not be asked: no claim
            raise HTTPException(status_code=503, detail={"code": "SOURCE_HEALTH_UNAVAILABLE",
                                                         "message": str(error), "gateways": None}) from error
        if found is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if store is None:
            raise HTTPException(status_code=503, detail={"code": "SOURCE_HEALTH_UNAVAILABLE",
                                                         "message": "No central gateway store is configured.",
                                                         "gateways": None})
        code, tenant_id, site_id = found
        try:
            snapshot = store.source_health_snapshot(UUID(str(tenant_id)), UUID(str(site_id)))
            return source_health_document(snapshot, code, clock(), access_basis)
        except LedgerUnavailable as error:
            raise HTTPException(status_code=503, detail={"code": "SOURCE_HEALTH_UNAVAILABLE",
                                                         "message": str(error), "gateways": None}) from error
        except SelectionInconsistent as error:
            raise HTTPException(status_code=409, detail={
                "code": "SOURCE_HEALTH_SELECTION_INCONSISTENT", "message": error.reason, "gateways": None,
                "note": "Registration and diagnostic selection disagree; no current contact or fact claim is made."
            }) from error

    return router


def build_health_range_router(estate: Any, registry: ImportedSiteRegistry, responses: ResponseStore | None = None,
                              registration: site_health_range.Registration | None = None,
                              counts: site_health_range.Counts | None = None,
                              access: Access = development_access, access_basis: str = ACCESS_BASIS,
                              unavailable: tuple[type[BaseException], ...] = ()) -> APIRouter:
    """SR-6a (rev 10 §10.2, D-SR.23): `GET /api/sites/{site_code}/health-range?from&to[&known_at]`,
    `site-health-range-1`, a stored route. Admission as `source-health` (401/403, then the tenant Site scope: 503 when
    it cannot be asked, 404); the window is the estate's (midnight UTC, at most 31 days, 422 INVALID_WINDOW); a Cold
    or EV Site is 404 HEALTH_RANGE_NOT_APPLICABLE (its Health reads the range already); a store failure is 503
    SITE_HEALTH_RANGE_UNAVAILABLE. Included late in `main.py`, after `responses` and the estate service exist."""
    router = APIRouter()

    def not_applicable(site_code: str) -> HTTPException:
        return _refuse(404, "HEALTH_RANGE_NOT_APPLICABLE", f"Site {site_code!r} reads its date range on its own Health.")

    def battery(site: Any, tenant: Any) -> dict[str, Any]:
        """The existing `/battery` entry body, unchanged (Foundation configuration, point-in-time, D-SR.14)."""
        if registry.service is None:
            raise _refuse(503, _UNAVAILABLE, "No product Foundation store is configured.")
        try:
            view = registry.service.read(site, tenant, None, None)
        except FoundationRefused as error:
            raise _refuse(409, "FOUNDATION_BASIS_UNAVAILABLE", str(error)) from error
        return battery_entry(view, view.now, access_basis)

    @router.get(HEALTH_RANGE_ROUTE)
    def health_range(site_code: str, request: Request, response: Response) -> Any:
        with perf.route(HEALTH_RANGE_ROUTE, response):  # QW-1: one `assetops.perf` line per request
            out = _health_range(site_code, request)
        return finish(out, response) if isinstance(out, Response) else out

    def _health_range(site_code: str, request: Request) -> Any:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read Site health."})
        if refusal == 403:
            raise _refuse(403, "SITE_SCOPE_FORBIDDEN", f"No access to Site {site_code!r}.")
        try:
            tenant = registry.tenant()
            site = registry.imported(site_code) if tenant is not None else None
        except Exception as error:  # noqa: BLE001 - the Site store could not be asked: no claim
            raise _refuse(503, _UNAVAILABLE, str(error)) from error
        if tenant is None or site is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if site.site_type != "MINIGRID":
            raise not_applicable(site_code)
        params = request.query_params
        lo, hi, known_at = _instant(params, "from"), _instant(params, "to"), _instant(params, "known_at")
        if lo is None or hi is None:
            raise _refuse(422, "INVALID_WINDOW", "Give both 'from' and 'to' (UTC midnights, at most 31 days).")
        try:
            req = replace(estate_request("portfolio", lo, hi, known_at), lens="all")
        except EstateRefusal as error:
            raise _refuse(error.status, error.code, error.detail["message"]) from error
        if estate is None or registration is None or counts is None:
            raise _refuse(503, _UNAVAILABLE, "No product database is configured.")

        def compose() -> dict[str, Any]:
            try:
                body = site_health_range.health_range_body(estate, tenant.id, site.site_code, req,
                                                           registration, counts)
                if body is not None:
                    body["battery"] = battery(site, tenant)
            except site_health_range.HealthRangeNotApplicable as error:
                raise not_applicable(site_code) from error
            except (EstateStoreUnavailable, SiteStoreUnavailable, FoundationStoreError, *unavailable) as error:
                raise _refuse(503, _UNAVAILABLE, str(error)) from error
            except EstateRefusal as error:
                if error.status == 503:
                    raise _refuse(503, _UNAVAILABLE, error.detail["message"]) from error
                raise _refuse(error.status, error.code, error.detail["message"]) from error
            if body is None:
                raise _refuse(404, "SITE_NOT_FOUND", f"No imported Site {site_code!r} with a health range.")
            return {HEALTH_RANGE_ROUTE: _public(body)}

        if responses is None:
            return compose()[HEALTH_RANGE_ROUTE]
        site_id = UUID(str(site.id))
        key = {"site": site.id, "from": lo, "to": hi, "known_at": known_at}
        return responses.serve(StoredRoute(HEALTH_RANGE_ROUTE, tenant.id, key, sites=(site_id,),
                                           watermark_sites=(site_id,)), compose)

    return router
