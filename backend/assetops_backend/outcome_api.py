"""OUT-B4 (§B.1, §B.3): the Site outcome board and the estate outcome summary.

    GET /api/sites/{site_code}/outcome-board     mini: `date` or a one-UTC-day `from`/`to` (`selected_day` and its
                                                 422 codes), optional `finding_id`/`finding_revision_id` pin;
                                                 cold and EV: `from`/`to` (at most 31 days); every domain: `known_at`
    GET /api/estate/outcome-summary              `from`/`to`/`known_at`, parsed as the estate scope root

Admission is the Site read seam of the domain overview routes: `access(request, code)` (401/403) before any lookup,
then the imported Site from the registry (404 SITE_NOT_FOUND for an unknown code or a Site type with no board).
The estate summary uses the estate authenticate/admit seam of `estate_portfolio_api.py` and the estate scope
service's authorized Site set, in its `(site_code_key, site_id)` order. The services are called directly, never
over HTTP; a refused producer read inside a board is that board's PARTIAL, never the route's error.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.estate.scope import EstateRefusal, EstateStoreUnavailable, parse_request as parse_estate
from assetops_backend.estate_api import Authenticate, development_authenticate
from assetops_backend.estate_portfolio_api import refusal as estate_refusal
from assetops_backend.finding_api import Access, development_access
from assetops_backend.outcomes.catalogue import MINI
from assetops_backend.site_outcomes.read import SiteOutcomeBoardService, SiteRef
from assetops_backend.site_overview.route import selected_day
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.ports import SiteStoreUnavailable

BOARD_ROUTE = "/api/sites/{site_code}/outcome-board"
SUMMARY_ROUTE = "/api/estate/outcome-summary"
MAX_WINDOW = timedelta(days=31)
_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z")


def _refuse(status: int, code: str, message: str, headers: dict[str, str] | None = None) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message}, headers=headers)


def _instant(params: Any, key: str) -> datetime | None:
    value = params.get(key)
    if value is None:
        return None
    if not _INSTANT.fullmatch(value):
        raise _refuse(422, "INVALID_WINDOW", f"'{key}' must be a UTC instant such as 2026-10-06T00:00:00Z.")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _pin(params: Any) -> tuple[UUID, UUID | None] | None:
    try:
        fid = None if params.get("finding_id") is None else UUID(params["finding_id"])
        rid = None if params.get("finding_revision_id") is None else UUID(params["finding_revision_id"])
    except ValueError as error:
        raise _refuse(422, "INVALID_FINDING_PIN", "finding_id and finding_revision_id are UUIDs") from error
    if rid is not None and fid is None:
        raise _refuse(422, "INVALID_FINDING_PIN", "finding_revision_id needs finding_id")
    return None if fid is None else (fid, rid)


def site_ref(site: Any) -> SiteRef:
    return SiteRef(site.tenant_id, site.id, site.site_code, site.name, site.site_type,
                   getattr(site, "timezone", None))


def _public(body: dict[str, Any]) -> dict[str, Any]:
    return jsonable_encoder({k: v for k, v in body.items() if not k.startswith("_")})


def build_outcome_router(service: SiteOutcomeBoardService | None, registry: ImportedSiteRegistry, *,
                         estate: Any = None, tenant: Callable[[], UUID | None] = lambda: None,
                         access: Access = development_access,
                         authenticate: Authenticate = development_authenticate,
                         unavailable: tuple[type[BaseException], ...] = ()) -> APIRouter:
    router = APIRouter()

    @router.get(BOARD_ROUTE)
    def outcome_board(site_code: str, request: Request) -> dict[str, Any]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise _refuse(401, "UNAUTHENTICATED", "Sign in to read the Site outcome board.",
                          {"WWW-Authenticate": "Bearer"})
        if refusal == 403:
            raise _refuse(403, "SITE_SCOPE_FORBIDDEN", f"No access to Site {site_code!r}.")
        try:
            tenant_ref = registry.tenant()
            site = registry.imported(site_code) if tenant_ref is not None else None
        except (SiteStoreUnavailable, FoundationStoreError) as error:
            raise _refuse(503, "SITE_STORE_UNAVAILABLE", str(error)) from error
        ref = None if site is None else site_ref(site)
        if ref is None or ref.domain is None:
            raise _refuse(404, "SITE_NOT_FOUND", f"No imported Site {site_code!r} with an outcome board.")
        params = request.query_params
        known_at = _instant(params, "known_at")
        day = lo = hi = pin = None
        if ref.domain == MINI:
            day = selected_day(params)  # its own 422 codes (B-Q5)
            pin = _pin(params)
        else:
            lo, hi = _instant(params, "from"), _instant(params, "to")
            if (lo is None) != (hi is None):
                raise _refuse(422, "PARTIAL_WINDOW", "Give both 'from' and 'to', or neither.")
            if lo is not None and not (lo < hi and hi - lo <= MAX_WINDOW):
                raise _refuse(422, "INVALID_WINDOW", "'from' must be before 'to', at most 31 days apart.")
        if service is None:
            raise _refuse(503, "SITE_OUTCOME_BOARD_UNAVAILABLE", "No product database is configured.")
        try:
            body = service.board(ref, day=day, lo=lo, hi=hi, known_at=known_at, pin=pin)
        except (SiteStoreUnavailable, *unavailable) as error:
            raise _refuse(503, "SITE_OUTCOME_BOARD_UNAVAILABLE", str(error)) from error
        return _public(body)

    @router.get(SUMMARY_ROUTE)
    def outcome_summary(request: Request) -> dict[str, Any]:
        if authenticate(request) == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail=estate_refusal("UNAUTHENTICATED"))
        try:
            parsed = parse_estate("scope", request.query_params.multi_items())
            if service is None or estate is None:
                raise EstateStoreUnavailable("No product database is configured.")
            scope = estate.scope(tenant(), parsed, lambda code: access(request, code) is None)
            sites = []
            for item in scope["sites"]:
                site = registry.imported(item["site_code"])
                if site is not None:
                    sites.append(site_ref(site))
        except EstateRefusal as error:
            headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else None
            raise HTTPException(status_code=error.status, detail=estate_refusal(error.code),
                                headers=headers) from error
        except (EstateStoreUnavailable, SiteStoreUnavailable, FoundationStoreError, *unavailable) as error:
            raise HTTPException(status_code=503, detail=estate_refusal("ESTATE_STORE_UNAVAILABLE")) from error
        lo = parsed.from_.astimezone(timezone.utc)
        hi = parsed.to.astimezone(timezone.utc)
        return jsonable_encoder(service.summary(sites, lo, hi, parsed.known_at))

    return router
