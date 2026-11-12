"""OUT-B4 (§B.1, §B.3): the Site outcome board and the estate outcome summary.

    GET /api/sites/{site_code}/outcome-board     mini: `date`, or a `from`/`to` of one UTC day or one Site-local
                                                 day (R6; `selected_day` and its 422 codes), optional
                                                 `finding_id`/`finding_revision_id` pin;
                                                 cold and EV: `from`/`to` (at most 31 days); every domain: `known_at`
    GET /api/estate/outcome-summary              `from`/`to`/`known_at`, parsed as the estate scope root

Admission (addendum 4, #2 and #7): a Site is admitted only when both the Site read seam of the domain overview
routes (`access`, `development_access`) and the Work read seam (`work_access`, bound in `main.py` to the
`site_read_access` the Work pages use) admit it; the first refusal of the two is 401/403 before any lookup. Then
the imported Site from the registry (404 SITE_NOT_FOUND for an unknown code or a Site type with no board), and for
a cold or EV Site the cold/EV disclosure check, answered with that gate's own 403 code.
The estate summary uses the estate authenticate/admit seam of `estate_portfolio_api.py` and the estate scope
service's authorized Site set, in its `(site_code_key, site_id)` order; a Site that either seam or its domain's
disclosure refuses is omitted, with no foreign count. The services are called directly, never
over HTTP; a refused producer read inside a board is that board's PARTIAL, never the route's error.
"""
from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder

from assetops_backend import perf
from assetops_backend.chain.read import board_day, window_day
from assetops_backend.chain.response_store import ResponseStore, StoredRoute, finish, parsed_key
from assetops_backend.cold_assessment_api import Disclosure, allow_disclosure
from assetops_backend.estate.scope import (
    EstateRefusal, EstateStoreUnavailable, estate_request, parse_request as parse_estate)
from assetops_backend.estate.site_range import RangeOverviewNotApplicable, site_range_body
from assetops_backend.estate_api import Authenticate, development_authenticate
from assetops_backend.estate_portfolio_api import refusal as estate_refusal
from assetops_backend.finding_api import Access, development_access
from assetops_backend.outcomes.catalogue import COLD, EV, MINI
from assetops_backend.site_outcomes.read import SiteOutcomeBoardService, SiteRef
from assetops_backend.site_overview.route import selected_day
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.ports import SiteStoreUnavailable

BOARD_ROUTE = "/api/sites/{site_code}/outcome-board"
SUMMARY_ROUTE = "/api/estate/outcome-summary"
RANGE_ROUTE = "/api/sites/{site_code}/range-overview"
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


def _mini_day_params(params: Any, tz: str | None) -> Any:
    """R6, CH5a2-R R7: the day of a `from`/`to` pair is `chain.read.window_day`, the one rule the summary card also
    reads. A pair that is exactly one Site-local day selects that local date, as `date=` does. A UTC-midnight pair
    goes to `selected_day` unchanged (it selects its UTC calendar date, `window_day` rule 2, and keeps every 422
    code); the board accepts no other window (`NOT_ONE_UTC_DAY`)."""
    start, end = params.get("from"), params.get("to")
    if start is None or end is None or not (_INSTANT.fullmatch(start) and _INSTANT.fullmatch(end)):
        return params
    lo = datetime.fromisoformat(start.replace("Z", "+00:00"))
    hi = datetime.fromisoformat(end.replace("Z", "+00:00"))
    if (lo.hour, lo.minute, lo.second) == (0, 0, 0):
        return params  # a UTC day (or a refusal): `selected_day` reads it
    local = window_day(lo, hi, tz)
    if local is None or (lo, hi) != board_day(local, tz):
        return params  # not a Site-local day: `selected_day` refuses it
    text = params.get("date")
    if text is not None and text != local.isoformat():
        raise _refuse(422, "CONFLICTING_WINDOW", "date conflicts with from/to")
    return {"date": local.isoformat()}


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


def board_site(admitted: Callable[[Request, str], int | None] | None, registry: ImportedSiteRegistry,
               site_code: str, what: str, request: Request | None = None) -> SiteRef:
    """The board route's admission and Site lookup (module doc), shared by the `/chain` routes (CH-5a2a §B1)."""
    refusal = None if admitted is None else admitted(request, site_code)
    if refusal == 401:
        raise _refuse(401, "UNAUTHENTICATED", f"Sign in to read the {what}.", {"WWW-Authenticate": "Bearer"})
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
    return ref


def board_window(ref: SiteRef, params: Any) -> tuple[Any, datetime | None, datetime | None, Any]:
    """The board route's window parsing and refusals: mini -> (`selected_day`, None, None, pin); cold and EV ->
    (None, from, to, None), at most 31 days (`MAX_WINDOW`)."""
    if ref.domain == MINI:
        return selected_day(_mini_day_params(params, ref.timezone)), None, None, _pin(params)  # its own 422s (B-Q5)
    lo, hi = _instant(params, "from"), _instant(params, "to")
    if (lo is None) != (hi is None):
        raise _refuse(422, "PARTIAL_WINDOW", "Give both 'from' and 'to', or neither.")
    if lo is not None and not (lo < hi and hi - lo <= MAX_WINDOW):
        raise _refuse(422, "INVALID_WINDOW", "'from' must be before 'to', at most 31 days apart.")
    return None, lo, hi, None


def estate_sites(request: Request, *, authenticate: Authenticate, estate: Any, tenant: Callable[[], UUID | None],
                 admitted: Callable[[Request, str], int | None], registry: ImportedSiteRegistry,
                 disclosed: Callable[[SiteRef], bool],
                 unavailable: tuple[type[BaseException], ...],
                 items: list[tuple[str, str]] | None = None) -> tuple[list[SiteRef], Any]:
    """The estate summary's authentication, scope parsing and Site set (module doc), shared by `/estate/chain`.
    `estate` None (no product database) is the scope's 503. `items` replaces the query items (CH-5b2: the estate
    "Why?" parses its scope without its own `category`)."""
    if authenticate(request) == 401:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                            detail=estate_refusal("UNAUTHENTICATED"))
    try:
        parsed = parse_estate("scope", request.query_params.multi_items() if items is None else items)
        if estate is None:
            raise EstateStoreUnavailable("No product database is configured.")
        with perf.timed("summary.scope"):
            scope = estate.site_list(tenant(), parsed, lambda code: admitted(request, code) is None)  # R2
        sites = []
        for item in scope["sites"]:
            site = registry.imported(item["site_code"])
            if site is not None and disclosed(site_ref(site)):
                sites.append(site_ref(site))
    except EstateRefusal as error:
        headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else None
        raise HTTPException(status_code=error.status, detail=estate_refusal(error.code),
                            headers=headers) from error
    except (EstateStoreUnavailable, SiteStoreUnavailable, FoundationStoreError, *unavailable) as error:
        raise HTTPException(status_code=503, detail=estate_refusal("ESTATE_STORE_UNAVAILABLE")) from error
    return sites, parsed


# The cold and EV gates' own disclosure refusals (cold_site_api.build_cold_gate, ev_assessment_api.ev_gate).
DISCLOSURE_REFUSAL = {COLD: "COLD_SOURCE_DISCLOSURE_FORBIDDEN", EV: "EV_SOURCE_DISCLOSURE_FORBIDDEN"}


def build_outcome_router(service: SiteOutcomeBoardService | None, registry: ImportedSiteRegistry, *,
                         estate: Any = None, tenant: Callable[[], UUID | None] = lambda: None,
                         access: Access = development_access,
                         work_access: Access = development_access,
                         cold_disclosure: Disclosure = allow_disclosure,
                         ev_disclosure: Disclosure = allow_disclosure,
                         authenticate: Authenticate = development_authenticate,
                         unavailable: tuple[type[BaseException], ...] = (),
                         responses: ResponseStore | None = None) -> APIRouter:
    router = APIRouter()
    disclosures = {COLD: cold_disclosure, EV: ev_disclosure}

    def admitted(request: Request, code: str) -> int | None:
        return access(request, code) or work_access(request, code)

    def disclosed(ref: SiteRef) -> bool:
        check = disclosures.get(ref.domain)
        return check is None or bool(check(ref.site_code, ref.tenant_id, ref.site_id))

    @router.get(BOARD_ROUTE)
    def outcome_board(site_code: str, request: Request, response: Response) -> dict[str, Any]:
        with perf.route(BOARD_ROUTE, response):  # QW-1: one `assetops.perf` line per request
            out = _outcome_board(site_code, request)
        return finish(out, response) if isinstance(out, Response) else out

    def _outcome_board(site_code: str, request: Request) -> Any:
        ref = board_site(admitted, registry, site_code, "Site outcome board", request)
        params = request.query_params
        known_at = _instant(params, "known_at")
        day, lo, hi, pin = board_window(ref, params)
        if service is None:
            raise _refuse(503, "SITE_OUTCOME_BOARD_UNAVAILABLE", "No product database is configured.")
        if not disclosed(ref):
            raise _refuse(403, DISCLOSURE_REFUSAL[ref.domain],
                          f"The source provenance of Site {site_code!r} may not be disclosed to this caller.")
        def compose() -> dict[str, Any]:
            try:
                body = service.board(ref, day=day, lo=lo, hi=hi, known_at=known_at, pin=pin)
            except (SiteStoreUnavailable, *unavailable) as error:
                raise _refuse(503, "SITE_OUTCOME_BOARD_UNAVAILABLE", str(error)) from error
            return {BOARD_ROUTE: _public(body)}

        if responses is None:
            return compose()[BOARD_ROUTE]
        # CH-5c: the board's key is its Site and its parsed window (a mini `date` and its Site-local `from`/`to`
        # pair parse to one day), its watermark its own Site's.
        key = {"site": ref.site_id, "domain": ref.domain, "day": day, "from": lo, "to": hi, "known_at": known_at,
               "pin": None if pin is None else [str(x) if x is not None else None for x in pin]}
        site = UUID(str(ref.site_id))
        return responses.serve(StoredRoute(BOARD_ROUTE, ref.tenant_id, key, sites=(site,),
                                           watermark_sites=(site,)), compose)

    @router.get(RANGE_ROUTE)
    def range_overview(site_code: str, request: Request, response: Response) -> dict[str, Any]:
        with perf.route(RANGE_ROUTE, response):  # QW-1: one `assetops.perf` line per request
            out = _range_overview(site_code, request)
        return finish(out, response) if isinstance(out, Response) else out

    def _range_overview(site_code: str, request: Request) -> Any:
        """SR-5a (rev 9 §9.4): one mini-grid Site over a range, on the Portfolio's selectors. Admission as the
        board; the window is the estate's (midnight UTC, at most 31 days, 422 INVALID_WINDOW)."""
        ref = board_site(admitted, registry, site_code, "Site range overview", request)
        if ref.domain != MINI:
            raise _refuse(404, "RANGE_OVERVIEW_NOT_APPLICABLE",
                          f"Site {site_code!r} reads its date range on its own Overview.")
        if not disclosed(ref):
            raise _refuse(403, DISCLOSURE_REFUSAL[ref.domain],
                          f"The source provenance of Site {site_code!r} may not be disclosed to this caller.")
        params = request.query_params
        lo, hi, known_at = _instant(params, "from"), _instant(params, "to"), _instant(params, "known_at")
        if lo is None or hi is None:
            raise _refuse(422, "INVALID_WINDOW", "Give both 'from' and 'to' (UTC midnights, at most 31 days).")
        try:
            req = replace(estate_request("portfolio", lo, hi, known_at), lens="all")
        except EstateRefusal as error:
            raise _refuse(error.status, error.code, error.detail["message"]) from error
        if estate is None:
            raise _refuse(503, "SITE_RANGE_OVERVIEW_UNAVAILABLE", "No product database is configured.")

        def compose() -> dict[str, Any]:
            try:
                body = site_range_body(estate, ref.tenant_id, ref.site_code, req)
            except RangeOverviewNotApplicable as error:
                raise _refuse(404, "RANGE_OVERVIEW_NOT_APPLICABLE",
                              f"Site {site_code!r} reads its date range on its own Overview.") from error
            except (EstateStoreUnavailable, SiteStoreUnavailable, *unavailable) as error:
                raise _refuse(503, "SITE_RANGE_OVERVIEW_UNAVAILABLE", str(error)) from error
            except EstateRefusal as error:
                if error.status == 503:
                    raise _refuse(503, "SITE_RANGE_OVERVIEW_UNAVAILABLE", error.detail["message"]) from error
                raise _refuse(error.status, error.code, error.detail["message"]) from error
            if body is None:
                raise _refuse(404, "SITE_NOT_FOUND", f"No imported Site {site_code!r} with a range overview.")
            return {RANGE_ROUTE: _public(body)}

        if responses is None:
            return compose()[RANGE_ROUTE]
        site = UUID(str(ref.site_id))
        key = {"site": ref.site_id, "from": lo, "to": hi, "known_at": known_at}
        return responses.serve(StoredRoute(RANGE_ROUTE, ref.tenant_id, key, sites=(site,),
                                           watermark_sites=(site,)), compose)

    @router.get(SUMMARY_ROUTE)
    def outcome_summary(request: Request, response: Response) -> dict[str, Any]:
        with perf.route(SUMMARY_ROUTE, response):  # QW-1: one `assetops.perf` line per request
            out = _outcome_summary(request)
        return finish(out, response) if isinstance(out, Response) else out

    def _outcome_summary(request: Request) -> Any:
        def compose() -> dict[str, Any]:
            sites, parsed = estate_sites(request, authenticate=authenticate, estate=estate if service is not None
                                         else None, tenant=tenant, admitted=admitted, registry=registry,
                                         disclosed=disclosed, unavailable=unavailable)
            lo = parsed.from_.astimezone(timezone.utc)
            hi = parsed.to.astimezone(timezone.utc)
            return {SUMMARY_ROUTE: jsonable_encoder(service.summary(sites, lo, hi, parsed.known_at))}

        tenant_id = tenant() if responses is not None and service is not None and estate is not None else None
        if tenant_id is None or authenticate(request) == 401:
            return compose()[SUMMARY_ROUTE]  # every refusal comes from `estate_sites`, unchanged
        try:
            parsed = parse_estate("scope", request.query_params.multi_items())
        except EstateRefusal:
            return compose()[SUMMARY_ROUTE]

        def admit(code: str) -> bool:  # `estate_sites`' admission and disclosure, per Site code
            if admitted(request, code) is not None:
                return False
            site = registry.imported(code)
            return site is not None and disclosed(site_ref(site))

        return responses.serve(StoredRoute(SUMMARY_ROUTE, tenant_id, parsed_key(parsed), admit=admit), compose)

    return router
