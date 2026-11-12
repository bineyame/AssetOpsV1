"""W4-02 unit 5: the mini-depth Performance reads (`D-2026-10-20-w4-02-buildspec` base "Wire, order and refusals";
closure 1 Q10-Q12, Q31, Q33; closure 4 S1, S6, S9, N7).

`GET /api/sites/{site_code}/performance/mini/{domain}?from=&to=&known_at=` for `renewable|service|fuel|backup`, and
`GET /api/sites/{site_code}/performance/mini/capabilities`. Order is authentication -> Site grant -> Site lookup
(scope outage 503) -> Site type -> parameter validation -> mini store read. The Dispatch Performance gate is not
consulted (S1): an authorized non-MINIGRID Site gets a 200 UNKNOWN `SITE_ROLE_UNSUPPORTED` envelope; a MINIGRID Site
gets the mini result or the mini store's 503. Refusals use `{detail:{code,message}}` and never echo foreign Site
details. `site_code` is the public Site code resolved inside the tenant (S9).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder

from assetops_backend import perf
from assetops_backend.chain.read import window_days
from assetops_backend.chain.response_store import ResponseStore, StoredRoute, finish
from assetops_backend.estate.scope import EstateRefusal, estate_request

from assetops_backend.finding_api import Access, development_access
from assetops_backend.mini_depth.read import (
    MESSAGES,
    MINIGRID,
    NULL_CARDS,
    SCHEMA_VERSION,
    MiniDepthRead,
    MiniReadRefused,
    MiniReadUnavailable,
    iso,
    site_path,
)
from assetops_backend.mini_depth.store import DOMAINS
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites import renewable_range
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.ports import SiteStoreUnavailable

ROUTE = "/api/sites/{site_code}/performance/mini"
#: SR-8 (rev 10 §10.4): Renewable over the whole date range, from the stored chain day snapshots.
RENEWABLE_RANGE_ROUTE = "/api/sites/{site_code}/renewable-range"
#: S6: the served mini tabs in this order; the frontend merges Dispatch to `service,dispatch,fuel,renewable,backup`.
CAPABILITIES = (("service", "Service"), ("fuel", "Fuel"), ("renewable", "Renewable"), ("backup", "Backup"))
REFUSALS = {
    "UNAUTHENTICATED": (401, "Authentication is required."),
    "SITE_SCOPE_FORBIDDEN": (403, "You do not have access to this site."),
    "SITE_NOT_FOUND": (404, "This site was not found."),
    "INVALID_WINDOW": (422, MESSAGES["INVALID_WINDOW"]),
    "INVALID_KNOWN_AT": (422, MESSAGES["INVALID_KNOWN_AT"]),
    "MINI_DEPTH_STORE_UNAVAILABLE": (503, MESSAGES["MINI_DEPTH_STORE_UNAVAILABLE"]),
}


def _refuse(code: str) -> HTTPException:
    status, message = REFUSALS[code]
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return HTTPException(status_code=status, headers=headers, detail={"code": code, "message": message})


def _instant(request: Request, key: str, code: str) -> datetime | None:
    """Q33: a UTC instant; offset input is accepted and normalized to UTC; a naive or malformed value refuses."""
    values = request.query_params.getlist(key)
    if not values:
        return None
    if len(values) > 1:
        raise _refuse(code)
    try:
        at = datetime.fromisoformat(values[0].replace("Z", "+00:00"))
    except ValueError as error:
        raise _refuse(code) from error
    if at.tzinfo is None:
        raise _refuse(code)
    return at.astimezone(timezone.utc)


def _lenient(request: Request, key: str) -> datetime | None:
    try:
        return _instant(request, key, "INVALID_WINDOW")
    except HTTPException:
        return None


def unsupported_envelope(domain: str, site_code: str, timezone_name: str | None, lo: datetime | None,
                         hi: datetime | None, known_at: datetime | None) -> dict[str, Any]:
    """Q10/S1: an authorized non-MINIGRID Site's direct mini read; no mini store is consulted."""
    return {
        "schema_version": SCHEMA_VERSION, "domain": domain,
        "site": {"code": site_code, "timezone": timezone_name},
        "window": {"from": iso(lo), "to": iso(hi), "known_at": iso(known_at), "bounds": "[from,to)"},
        "currentness": {"state": "UNKNOWN", "job_state": "NONE", "windows": []},
        "source_provenance": {"classification": "UNKNOWN", "state": "UNKNOWN", "source_ids": [], "evidence_ids": [],
                              "basis_sha256": None,
                              "reasons": [{"code": "EMPTY_CITATION_SET", "accepted_evidence_ids": []}]},
        "selected_source_provenance": None, "pending_source_provenance": None,
        "status": "UNKNOWN", "coverage": None, "cards": dict(NULL_CARDS[domain]), "rows": [],
        "limitations": [{"code": "SITE_ROLE_UNSUPPORTED", "evidence_ids": []}], "basis": None,
        "links": {"dispatch": None, "evidence": f"{site_path(site_code)}/evidence", "financials": None,
                  "actions": None},
        **({"critical_delivered_coverage": None} if domain == "service" else {}),
    }


def build_mini_depth_router(reader: MiniDepthRead | None, registry: ImportedSiteRegistry,
                            access: Access = development_access) -> APIRouter:
    router = APIRouter()

    def site_of(request: Request, site_code: str) -> Any:
        refusal = access(request, site_code)
        if refusal == 401:
            raise _refuse("UNAUTHENTICATED")
        if refusal == 403:
            raise _refuse("SITE_SCOPE_FORBIDDEN")
        try:  # N7: a Site scope outage is 503 before the missing-Site 404 branch
            tenant = registry.tenant()
            site = registry.imported(site_code) if tenant is not None else None
        except (SiteStoreUnavailable, FoundationStoreError) as error:
            raise _refuse("MINI_DEPTH_STORE_UNAVAILABLE") from error
        if tenant is None or site is None:
            raise _refuse("SITE_NOT_FOUND")
        return tenant, site

    @router.get(f"{ROUTE}/capabilities")
    def capabilities(request: Request, site_code: str) -> list[dict[str, str]]:
        _, site = site_of(request, site_code)
        if site.site_type != MINIGRID or reader is None:
            return []
        return [{"id": i, "display_name": name} for i, name in CAPABILITIES]

    @router.get(f"{ROUTE}/{{domain}}")
    def read(request: Request, site_code: str, domain: str) -> dict[str, Any]:
        tenant, site = site_of(request, site_code)
        if domain not in DOMAINS:
            raise HTTPException(status_code=404,
                                detail={"code": "MINI_DOMAIN_NOT_FOUND", "message": "This page was not found."})
        if site.site_type != MINIGRID:
            # The unsupported gap is answered before parameter validation (S1 order); q9 ruling 9: each parseable
            # parameter echoes as UTC and each bad one is null, independently.
            lo, hi, known = (_lenient(request, key) for key in ("from", "to", "known_at"))
            return unsupported_envelope(domain, site.site_code, getattr(site, "timezone", None), lo, hi, known)
        lo, hi = _instant(request, "from", "INVALID_WINDOW"), _instant(request, "to", "INVALID_WINDOW")
        if lo is None or hi is None:
            raise _refuse("INVALID_WINDOW")
        known = _instant(request, "known_at", "INVALID_KNOWN_AT")
        if reader is None:
            raise _refuse("MINI_DEPTH_STORE_UNAVAILABLE")
        try:
            return reader.read(tenant_id=tenant.id, site_id=site.id, site_code=site.site_code, domain=domain,
                               lo=lo, hi=hi, known_at=known)
        except MiniReadRefused as refused:
            raise _refuse(refused.code) from refused
        except MiniReadUnavailable as error:
            raise _refuse("MINI_DEPTH_STORE_UNAVAILABLE") from error

    return router


RANGE_REFUSALS = {
    "UNAUTHENTICATED": REFUSALS["UNAUTHENTICATED"],
    "SITE_SCOPE_FORBIDDEN": REFUSALS["SITE_SCOPE_FORBIDDEN"],
    "SITE_NOT_FOUND": REFUSALS["SITE_NOT_FOUND"],
    "RENEWABLE_RANGE_NOT_APPLICABLE": (404, "Renewable headroom over a range is read for mini-grid sites only."),
    "INVALID_WINDOW": (422, "'from' and 'to' must be UTC midnights, 'from' before 'to', at most 31 days apart."),
    "INVALID_KNOWN_AT": (422, MESSAGES["INVALID_KNOWN_AT"]),
    "SITE_RENEWABLE_RANGE_UNAVAILABLE": (503, "The renewable range read is unavailable right now."),
}


def _range_refuse(code: str) -> HTTPException:
    status, message = RANGE_REFUSALS[code]
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return HTTPException(status_code=status, headers=headers, detail={"code": code, "message": message})


def build_renewable_range_router(chain_reader: Callable[[], Any], registry: ImportedSiteRegistry, *,
                                 access: Access = development_access,
                                 unavailable: tuple[type[BaseException], ...] = (),
                                 responses: ResponseStore | None = None) -> APIRouter:
    """SR-8 (rev 10 §10.4, D-SR.23/27): included in `main.py` after the response store and the outcome board.
    `chain_reader()` returns the board service's `ChainReader` (None: 503). Order: authentication -> Site grant ->
    Site lookup (outage 503) -> Site type (404) -> window (422, the estate rule: UTC midnights, at most 31 days) ->
    `known_at` (422) -> chain read (503). One `ChainRequest.day` read over `window_days(from, to, tz)`."""
    router = APIRouter()

    def site_of(request: Request, site_code: str) -> Any:
        refusal = access(request, site_code)
        if refusal == 401:
            raise _range_refuse("UNAUTHENTICATED")
        if refusal == 403:
            raise _range_refuse("SITE_SCOPE_FORBIDDEN")
        try:
            tenant = registry.tenant()
            site = registry.imported(site_code) if tenant is not None else None
        except (SiteStoreUnavailable, FoundationStoreError) as error:
            raise _range_refuse("SITE_RENEWABLE_RANGE_UNAVAILABLE") from error
        if tenant is None or site is None:
            raise _range_refuse("SITE_NOT_FOUND")
        return site

    @router.get(RENEWABLE_RANGE_ROUTE)
    def renewable_range_route(request: Request, response: Response, site_code: str) -> Any:
        with perf.route(RENEWABLE_RANGE_ROUTE, response):
            out = _renewable_range(request, site_code)
        return finish(out, response) if isinstance(out, Response) else out

    def _renewable_range(request: Request, site_code: str) -> Any:
        site = site_of(request, site_code)
        if site.site_type != MINIGRID:
            raise _range_refuse("RENEWABLE_RANGE_NOT_APPLICABLE")
        lo, hi = _instant(request, "from", "INVALID_WINDOW"), _instant(request, "to", "INVALID_WINDOW")
        if lo is None or hi is None:
            raise _range_refuse("INVALID_WINDOW")
        known = _instant(request, "known_at", "INVALID_KNOWN_AT")
        try:
            window = estate_request("portfolio", lo, hi, known)
        except EstateRefusal as refused:
            raise _range_refuse("INVALID_WINDOW") from refused
        reader = chain_reader()
        if reader is None:
            raise _range_refuse("SITE_RENEWABLE_RANGE_UNAVAILABLE")
        tz = getattr(site, "timezone", None)
        days = window_days(window.from_, window.to, tz)

        def compose() -> dict[str, Any]:
            try:
                facts = reader.request(site.tenant_id, known).day(site.id, MINIGRID, days)
            except (SiteStoreUnavailable, *unavailable) as error:
                raise _range_refuse("SITE_RENEWABLE_RANGE_UNAVAILABLE") from error
            body = renewable_range.compose(
                {"site_code": site.site_code, "site_name": getattr(site, "name", None), "timezone": tz},
                {"from": iso(window.from_), "to": iso(window.to), "known_at": iso(known)}, days, facts)
            return {RENEWABLE_RANGE_ROUTE: jsonable_encoder(body)}

        if responses is None:
            return compose()[RENEWABLE_RANGE_ROUTE]
        sid = UUID(str(site.id))
        key = {"site": str(site.id), "from": iso(window.from_), "to": iso(window.to), "known_at": iso(known)}
        return responses.serve(StoredRoute(RENEWABLE_RANGE_ROUTE, site.tenant_id, key, sites=(sid,),
                                           watermark_sites=(sid,)), compose, request.headers.get("if-none-match"))

    return router


__all__ = ["CAPABILITIES", "REFUSALS", "RANGE_REFUSALS", "RENEWABLE_RANGE_ROUTE", "build_mini_depth_router",
           "build_renewable_range_router", "unsupported_envelope"]
