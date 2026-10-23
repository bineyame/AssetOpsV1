"""W5-01b C4: the authored cold scenario routes (`.agent/W5-01-build-spec.md` C4 card, refusal table and pre-flight
rulings P-C4-7..14, 21).

- `GET /api/sites/{site_code}/cold/financials/scenarios?from=&to=&known_at=&scenario_at=&limit=&cursor=`
  (`cold-scenarios-1`), for an ordinary viewer of the cold Site.
- `POST /api/sites/{site_code}/cold/financials/scenarios?from=&to=&known_at=` and
  `POST .../scenarios/{scenario_id}/revisions?from=&to=&known_at=` (`cold-scenario-write-1`), which also need the
  injected decision command access and server principal.

Order: authenticate, Site scope, unknown or repeated query keys, the strict paired half-open UTC window (at most 31
days), the imported cold Site, source disclosure; a POST then needs both `from,to`, the command access, the service,
the principal and actor, the body, the basis and the write. Every refusal is `{error:{code,message}}` through this
module's own mapper. Composition only; no SQL driver here.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from assetops_backend.cold_assessment_api import Disclosure, allow_disclosure
from assetops_backend.cold_scenarios.rules import MESSAGES as SCENARIO_MESSAGES
from assetops_backend.cold_scenarios.rules import PAGE_MAX
from assetops_backend.finding_api import Access, development_access
from assetops_backend.mini_decisions.model import MESSAGES as DECISION_MESSAGES
from assetops_backend.mini_decisions.model import DecisionRefused
from assetops_backend.mini_decisions_api import (
    DecisionPrincipalResolver,
    deny_decision_writes,
    no_decision_principal,
)
from assetops_backend.sites.cold_foundation import COLD_SITE_TYPE
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.ports import SiteStoreUnavailable

ROUTE = "/api/sites/{site_code}/cold/financials/scenarios"
POST_KEYS = frozenset({"from", "to", "known_at"})
GET_KEYS = POST_KEYS | {"scenario_at", "limit", "cursor"}
MAX_WINDOW = timedelta(days=31)
_FRACTION = re.compile(r"\.(\d+)")


class _Refusal(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(code)
        self.status, self.code, self.message = status, code, message


def _of(error: DecisionRefused) -> _Refusal:
    return _Refusal(error.status, error.code, error.message)


def _response(refusal: _Refusal) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if refusal.status == 401 else None
    return JSONResponse(status_code=refusal.status, headers=headers,
                        content={"error": {"code": refusal.code, "message": refusal.message}})


def _store_unavailable() -> _Refusal:
    return _Refusal(503, "DECISION_STORE_UNAVAILABLE", DECISION_MESSAGES["DECISION_STORE_UNAVAILABLE"])


def _instant(request: Request, key: str) -> datetime | None:
    raw = request.query_params.get(key)
    if raw is None:
        return None
    fraction = _FRACTION.search(raw)
    try:
        at = None if fraction is not None and len(fraction.group(1)) > 6 else \
            datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        at = None
    if at is None or at.tzinfo is None or at.utcoffset() != timezone.utc.utcoffset(None):
        raise _Refusal(422, "COLD_TIME_INVALID",
                       f"'{key}' must be a UTC instant such as 2026-10-06T19:00:00Z, at most microsecond precision.")
    return at


def build_cold_scenarios_router(registry: ImportedSiteRegistry, service: Any | None,
                                access: Access = development_access,
                                disclosure: Disclosure = allow_disclosure,
                                command_access: Access = deny_decision_writes,
                                principal: DecisionPrincipalResolver = no_decision_principal) -> APIRouter:
    router = APIRouter()

    def gate(request: Request, site_code: str, keys: frozenset) -> tuple[Any, Any, dict[str, Any]]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise _Refusal(401, "UNAUTHENTICATED", "Sign in to read cold-chain Site data.")
        if refusal == 403:
            raise _Refusal(403, "SITE_SCOPE_FORBIDDEN", f"No access to Site {site_code!r}.")
        names = [key for key, _ in request.query_params.multi_items()]
        unknown = sorted(set(names) - keys)
        if unknown:
            raise _Refusal(422, "COLD_PARAMETER_UNKNOWN", f"Unknown parameters {unknown}.")
        repeated = sorted({key for key in names if names.count(key) > 1})
        if repeated:
            raise _Refusal(422, "COLD_PARAMETER_UNKNOWN", f"Repeated parameters {repeated}.")
        lo, hi, known = _instant(request, "from"), _instant(request, "to"), _instant(request, "known_at")
        scenario_at = _instant(request, "scenario_at")
        if (lo is None) != (hi is None):
            raise _Refusal(422, "COLD_WINDOW_INVALID", "Give both 'from' and 'to', or neither.")
        if lo is not None and not lo < hi:
            raise _Refusal(422, "COLD_WINDOW_INVALID", "'from' must be before 'to'.")
        if lo is not None and hi - lo > MAX_WINDOW:
            raise _Refusal(422, "COLD_WINDOW_TOO_LONG", "A cold read window is at most 31 days.")
        try:
            site = registry.imported(site_code)
            tenant = registry.tenant() if site is not None else None
        except SiteStoreUnavailable as error:
            raise _Refusal(503, "COLD_READ_UNAVAILABLE", str(error)) from error
        if site is None or tenant is None or site.site_type != COLD_SITE_TYPE:
            raise _Refusal(404, "SITE_NOT_FOUND", f"No cold-chain Site {site_code!r} in this tenant.")
        if not disclosure(site_code, tenant.id, site.id):
            raise _Refusal(403, "COLD_SOURCE_DISCLOSURE_FORBIDDEN",
                           f"The source provenance of Site {site_code!r} may not be disclosed to this caller.")
        return tenant.id, site.id, {"lo": lo, "hi": hi, "known_at": known, "scenario_at": scenario_at}

    def command(request: Request, site_code: str) -> tuple[Any, Any, dict[str, Any], Any]:
        t, s, w = gate(request, site_code, POST_KEYS)
        if w["lo"] is None:
            raise _Refusal(422, "COLD_WINDOW_INVALID", "A cold scenario write needs both 'from' and 'to'.")
        grant = command_access(request, site_code)
        if grant == 401:
            raise _Refusal(401, "UNAUTHENTICATED", "Sign in to read cold-chain Site data.")
        if grant == 403:
            raise _Refusal(403, "DECISION_WRITE_FORBIDDEN", DECISION_MESSAGES["DECISION_WRITE_FORBIDDEN"])
        if service is None:
            raise _store_unavailable()
        return t, s, w, principal(request, site_code)

    async def body_of(request: Request) -> Any:
        try:
            return await request.json()
        except ValueError:
            return None  # not JSON: refused 422 by the closed shape, after the write gate

    def served(work: Callable[[], Any]) -> Any:
        try:
            try:
                return work()
            except DecisionRefused as error:
                raise _of(error) from error
        except _Refusal as refusal:
            return _response(refusal)

    @router.get(ROUTE)
    def list_scenarios(request: Request, site_code: str) -> Any:
        def work() -> Any:
            t, s, w = gate(request, site_code, GET_KEYS)
            if service is None:
                raise _store_unavailable()
            raw = request.query_params.get("limit")
            limit = None
            if raw is not None:
                if not raw.isdigit() or not 1 <= int(raw) <= PAGE_MAX:
                    raise _Refusal(422, "COLD_LIMIT_INVALID", SCENARIO_MESSAGES["COLD_LIMIT_INVALID"])
                limit = int(raw)
            return service.list(t, s, site_code, w["lo"], w["hi"], w["known_at"], w["scenario_at"], limit,
                                request.query_params.get("cursor"))
        return served(work)

    @router.post(ROUTE)
    async def create_scenario(request: Request, site_code: str) -> Any:
        try:
            t, s, w, admitted = command(request, site_code)
        except _Refusal as refusal:
            return _response(refusal)
        body = await body_of(request)

        def work() -> Any:
            status, out = service.create(t, s, site_code, admitted, w["lo"], w["hi"], w["known_at"], body)
            return JSONResponse(status_code=status, content=out)
        return served(work)

    @router.post(ROUTE + "/{scenario_id}/revisions")
    async def correct_scenario(request: Request, site_code: str, scenario_id: str) -> Any:
        try:
            t, s, w, admitted = command(request, site_code)
        except _Refusal as refusal:
            return _response(refusal)
        body = await body_of(request)

        def work() -> Any:
            status, out = service.correct(t, s, site_code, admitted, scenario_id, w["lo"], w["hi"], w["known_at"],
                                          body)
            return JSONResponse(status_code=status, content=out)
        return served(work)

    return router
