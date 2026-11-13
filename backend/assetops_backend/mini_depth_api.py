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
from assetops_backend.infra import is_transient
from assetops_backend.chain.ports import SiteRef
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
from assetops_backend.mini_depth.service_range import service_range_body
from assetops_backend.mini_depth.store import DOMAINS
from assetops_backend.outcome_api import _instant as _utc_instant, _refuse as _refused, board_site
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites import renewable_range
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.ports import SiteStoreUnavailable

ROUTE = "/api/sites/{site_code}/performance/mini"
SERVICE_RANGE_ROUTE = "/api/sites/{site_code}/service-range"
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


def _instant(request: Request, key: str, code: str,
             refuse: Callable[[str], HTTPException] | None = None) -> datetime | None:
    """Q33: a UTC instant; offset input is accepted and normalized to UTC; a naive or malformed value refuses
    (through `refuse`, the one-day `_refuse` by default; a range route passes its own refuser)."""
    refuse = refuse or _refuse
    values = request.query_params.getlist(key)
    if not values:
        return None
    if len(values) > 1:
        raise refuse(code)
    try:
        at = datetime.fromisoformat(values[0].replace("Z", "+00:00"))
    except ValueError as error:
        raise refuse(code) from error
    if at.tzinfo is None:
        raise refuse(code)
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


def build_service_range_router(chain_reader: Callable[[], Any], registry: ImportedSiteRegistry,
                               access: Access = development_access,
                               unavailable: tuple[type[BaseException], ...] = (),
                               responses: ResponseStore | None = None) -> APIRouter:
    """SR-7a (rev 10 §10.3, D-SR.23/26): `GET /api/sites/{site_code}/service-range?from&to[&known_at]`, schema
    `site-service-range-1`. Admission and Site lookup as the board (`outcome_api.board_site`: 401/403, 503 Site
    store, 404); a cold or EV Site is 404 `SERVICE_RANGE_NOT_APPLICABLE`; the window is the estate's
    (`estate_request`: UTC midnights, at most 31 days, else 422 INVALID_WINDOW); no chain reader or a chain read
    outage is 503 `SITE_SERVICE_RANGE_UNAVAILABLE`. `chain_reader()` returns the board service's `ChainReader` (the
    object `build_chain_router` reads, `chain_api.py` `reader()`). Stored route keyed `{site, from, to, known_at}`,
    one Site and its own watermark."""
    router = APIRouter()

    @router.get(SERVICE_RANGE_ROUTE)
    def service_range(site_code: str, request: Request, response: Response) -> Any:
        with perf.route(SERVICE_RANGE_ROUTE, response):  # QW-1: one `assetops.perf` line per request
            out = _service_range(site_code, request)
        return finish(out, response) if isinstance(out, Response) else out

    def _service_range(site_code: str, request: Request) -> Any:
        ref = board_site(access, registry, site_code, "Site service range", request)
        if ref.site_type != MINIGRID:
            raise _refused(404, "SERVICE_RANGE_NOT_APPLICABLE",
                           f"Site {site_code!r} has no mini-grid critical-load service.")
        params = request.query_params
        lo, hi = _utc_instant(params, "from"), _utc_instant(params, "to")
        known_at = _utc_instant(params, "known_at")
        if lo is None or hi is None:
            raise _refused(422, "INVALID_WINDOW", "Give both 'from' and 'to' (UTC midnights, at most 31 days).")
        try:
            estate_request("portfolio", lo, hi, known_at)
        except EstateRefusal as error:
            raise _refused(error.status, error.code, error.detail["message"]) from error
        reader = chain_reader()
        if reader is None:
            raise _refused(503, "SITE_SERVICE_RANGE_UNAVAILABLE", "No product database is configured.")

        def compose() -> dict[str, Any]:
            days = window_days(lo, hi, ref.timezone)
            try:
                facts = reader.request(ref.tenant_id, known_at).day(ref.site_id, MINIGRID, days)
            except (SiteStoreUnavailable, *unavailable) as error:
                raise _refused(503, "SITE_SERVICE_RANGE_UNAVAILABLE", str(error)) from error
            site = {"site_code": ref.site_code, "site_name": ref.site_name, "timezone": ref.timezone}
            return {SERVICE_RANGE_ROUTE: service_range_body(site, facts, days, lo=lo, hi=hi, known_at=known_at)}

        if responses is None:
            return compose()[SERVICE_RANGE_ROUTE]
        site = UUID(str(ref.site_id))
        key = {"site": ref.site_id, "from": lo, "to": hi, "known_at": known_at}
        return responses.serve(StoredRoute(SERVICE_RANGE_ROUTE, ref.tenant_id, key, sites=(site,),
                                           watermark_sites=(site,)), compose)

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
        # SR-8 review L2: the window rule first (as the estate parser), then `known_at`; both refuse in range words.
        lo = _instant(request, "from", "INVALID_WINDOW", _range_refuse)
        hi = _instant(request, "to", "INVALID_WINDOW", _range_refuse)
        if lo is None or hi is None:
            raise _range_refuse("INVALID_WINDOW")
        try:
            window = estate_request("portfolio", lo, hi)
        except EstateRefusal as refused:
            raise _range_refuse("INVALID_WINDOW") from refused
        known = _instant(request, "known_at", "INVALID_KNOWN_AT", _range_refuse)
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


#: SR-10b / SR-11 (rev 10b.2/10b.3, D-SR.31-33): Fuel and Backup over the range, from the stored day rows.
DAY_RANGE_ROUTES = {"fuel": "/api/sites/{site_code}/fuel-range", "backup": "/api/sites/{site_code}/backup-range"}
DAY_RANGE_REFUSALS = {
    "UNAUTHENTICATED": REFUSALS["UNAUTHENTICATED"],
    "SITE_SCOPE_FORBIDDEN": REFUSALS["SITE_SCOPE_FORBIDDEN"],
    "SITE_NOT_FOUND": REFUSALS["SITE_NOT_FOUND"],
    "FUEL_RANGE_NOT_APPLICABLE": (404, "Fuel use over a range is read for mini-grid sites only."),
    "BACKUP_RANGE_NOT_APPLICABLE": (404, "Backup starts over a range are read for mini-grid sites only."),
    "INVALID_WINDOW": (422, "'from' and 'to' must be UTC midnights, 'from' before 'to', at most 31 days apart."),
    "INVALID_KNOWN_AT": (422, MESSAGES["INVALID_KNOWN_AT"]),
    "SITE_FUEL_RANGE_UNAVAILABLE": (503, "The fuel range read is unavailable right now."),
    "SITE_BACKUP_RANGE_UNAVAILABLE": (503, "The backup range read is unavailable right now."),
}


def _day_range_refuse(code: str) -> HTTPException:
    status, message = DAY_RANGE_REFUSALS[code]
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return HTTPException(status_code=status, headers=headers, detail={"code": code, "message": message})


def build_day_range_router(domain: str, period_reader: Callable[[], Any], chain_reader: Callable[[], Any],
                           registry: ImportedSiteRegistry, *, access: Access = development_access,
                           unavailable: tuple[type[BaseException], ...] = (),
                           responses: ResponseStore | None = None,
                           now: Callable[[], datetime] | None = None) -> APIRouter:
    """SR-10b (`domain="fuel"`) / SR-11 (`"backup"`), included in `main.py` after the response store and the
    outcome board (D-SR.23). `period_reader()` is the AR-2 `PeriodReader` (`build_mini_period_rows`), and
    `chain_reader()` the board's `ChainReader` (either None: 503). Order: authentication -> Site grant -> Site lookup
    (outage 503) -> Site type (404) -> window (422; the estate rule: UTC midnights, at most 31 days) -> `known_at`
    (422) -> one period read of the day kind over `window_days(from, to, tz)` (D-SR.45) and one `ChainRequest.day`
    for the grades (503). An absent row reads STILL_PROCESSING; nothing is composed on read (D-SR.31)."""
    from assetops_backend.mini_depth import day_summary

    route = DAY_RANGE_ROUTES[domain]
    prefix = domain.upper()
    not_applicable, unavailable_code = f"{prefix}_RANGE_NOT_APPLICABLE", f"SITE_{prefix}_RANGE_UNAVAILABLE"
    clock = now or (lambda: datetime.now(timezone.utc))
    router = APIRouter()

    def site_of(request: Request, site_code: str) -> Any:
        refusal = access(request, site_code)
        if refusal == 401:
            raise _day_range_refuse("UNAUTHENTICATED")
        if refusal == 403:
            raise _day_range_refuse("SITE_SCOPE_FORBIDDEN")
        try:
            tenant = registry.tenant()
            site = registry.imported(site_code) if tenant is not None else None
        except (SiteStoreUnavailable, FoundationStoreError) as error:
            raise _day_range_refuse(unavailable_code) from error
        if tenant is None or site is None:
            raise _day_range_refuse("SITE_NOT_FOUND")
        return site

    def _day_range(request: Request, site_code: str) -> Any:
        site = site_of(request, site_code)
        if site.site_type != MINIGRID:
            raise _day_range_refuse(not_applicable)
        try:
            lo, hi = _instant(request, "from", "INVALID_WINDOW"), _instant(request, "to", "INVALID_WINDOW")
        except HTTPException as error:
            raise _day_range_refuse("INVALID_WINDOW") from error
        if lo is None or hi is None:
            raise _day_range_refuse("INVALID_WINDOW")
        try:
            known = _instant(request, "known_at", "INVALID_KNOWN_AT")
        except HTTPException as error:
            raise _day_range_refuse("INVALID_KNOWN_AT") from error
        try:
            window = estate_request("portfolio", lo, hi, known)
        except EstateRefusal as refused:
            raise _day_range_refuse("INVALID_WINDOW") from refused
        periods, chain = period_reader(), chain_reader()
        tz = getattr(site, "timezone", None)
        if periods is None or chain is None or not tz:
            raise _day_range_refuse(unavailable_code)
        days = list(window_days(window.from_, window.to, tz))
        sid = UUID(str(site.id))

        def compose() -> dict[str, Any]:
            kind = day_summary.DAY_KIND[domain]
            # D-SR.52: deliberately NOT gated on ASSETOPS_PERIOD_READ_KINDS. The day kinds have no compose to fall
            # back to (D-SR.31), so honouring the switch would only blank the range; the safety behaviour is the
            # STILL_PROCESSING row plus the live hour drill-in.
            try:
                result = periods.read(site.tenant_id, [SiteRef(site.tenant_id, sid, site.site_code, MINIGRID, tz)],
                                      [kind], days[0], days[-1], known)
                facts = chain.request(site.tenant_id, known).day(sid, MINIGRID, days)
                grades = day_summary.day_grades(facts)
                no_readings = day_summary.no_reading_days(facts)
            except Exception as error:  # a store failure or a connection error (no driver import: `infra`)
                if isinstance(error, (SiteStoreUnavailable, *unavailable)) or is_transient(error):
                    raise _day_range_refuse(unavailable_code) from error
                raise
            body = day_summary.compose(
                domain, {"id": sid, "site_code": site.site_code, "site_name": getattr(site, "name", None),
                         "timezone": tz},
                {"from": iso(window.from_), "to": iso(window.to), "known_at": iso(known)}, days, result, grades,
                historical=known is not None and known < clock(), no_readings=no_readings)
            return {route: jsonable_encoder(body)}

        if responses is None:
            return compose()[route]
        key = {"site": str(sid), "from": iso(window.from_), "to": iso(window.to), "known_at": iso(known)}
        return responses.serve(StoredRoute(route, site.tenant_id, key, sites=(sid,), watermark_sites=(sid,)),
                               compose, request.headers.get("if-none-match"))

    @router.get(route)
    def day_range_route(request: Request, response: Response, site_code: str) -> Any:
        with perf.route(route, response):
            out = _day_range(request, site_code)
        return finish(out, response) if isinstance(out, Response) else out

    return router


__all__ = ["CAPABILITIES", "DAY_RANGE_REFUSALS", "DAY_RANGE_ROUTES", "RANGE_REFUSALS", "REFUSALS",
           "RENEWABLE_RANGE_ROUTE", "SERVICE_RANGE_ROUTE", "build_day_range_router", "build_mini_depth_router",
           "build_renewable_range_router", "build_service_range_router", "unsupported_envelope"]
