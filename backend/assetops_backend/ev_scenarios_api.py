"""W5-03b E5: the authored EV scenario routes (`.agent/W5-03-build-spec.md` E5 card, "E5 exact persisted schema and
wire contract" and its refusal table).

- `GET /api/sites/{site_code}/ev/financials/scenarios?from=&to=&known_at=&scenario_at=&limit=&cursor=`
  (`ev-scenarios-1`), for an ordinary viewer of the EV Site.
- `POST /api/sites/{site_code}/ev/financials/scenarios?from=&to=&known_at=` and
  `POST .../scenarios/{scenario_id}/revisions?from=&to=&known_at=` (`ev-scenario-write-1`), which also need the
  injected decision command access and server principal.

Order: W2-06's EV gate unchanged (`ev_assessment_api.ev_gate`: authentication, Site scope, repeated or unknown query
keys 422 `EV_PARAMETER_UNKNOWN`, the strict paired half-open UTC window at most 31 days, the imported EV Site, the
configured store, source disclosure); a GET then parses `scenario_at` and `limit` (1..100, the existing
`EV_LIMIT_INVALID`); a POST needs both `from,to`, the command access, the principal and actor, the body, the basis and
the write. Every refusal is `{error:{code,message}}`. Composition only; no SQL driver here.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from assetops_backend.ev_assessment_api import (
    EV_ROUTE,
    WINDOW_KEYS,
    Disclosure,
    _instant,
    _Refused,
    allow_disclosure,
    ev_gate,
)
from assetops_backend.ev_scenarios.rules import PAGE_MAX
from assetops_backend.finding_api import Access, development_access
from assetops_backend.mini_decisions.model import MESSAGES as DECISION_MESSAGES
from assetops_backend.mini_decisions.model import DecisionRefused
from assetops_backend.mini_decisions_api import (
    DecisionPrincipalResolver,
    deny_decision_writes,
    no_decision_principal,
)
from assetops_backend.sites.cutover import ImportedSiteRegistry

ROUTE = EV_ROUTE + "/financials/scenarios"
POST_KEYS = WINDOW_KEYS
GET_KEYS = WINDOW_KEYS | {"scenario_at", "limit", "cursor"}


def _decision(error: DecisionRefused) -> _Refused:
    return _Refused(error.status, error.code, error.message)


def build_ev_scenarios_router(registry: ImportedSiteRegistry, service: Any | None,
                              access: Access = development_access,
                              disclosure: Disclosure = allow_disclosure,
                              command_access: Access = deny_decision_writes,
                              principal: DecisionPrincipalResolver = no_decision_principal) -> APIRouter:
    router = APIRouter()
    gate = ev_gate(registry, service, access, disclosure)

    def command(request: Request, site_code: str) -> tuple[Any, Any, dict[str, Any], Any]:
        t, s, w = gate.opened(request, site_code, POST_KEYS)
        if w["lo"] is None:
            raise _Refused(422, "EV_WINDOW_INVALID", "An EV scenario write needs both 'from' and 'to'.")
        grant = command_access(request, site_code)
        if grant == 401:
            raise _Refused(401, "UNAUTHENTICATED", "Sign in to read EV assessments.", {"WWW-Authenticate": "Bearer"})
        if grant == 403:
            raise _Refused(403, "DECISION_WRITE_FORBIDDEN", DECISION_MESSAGES["DECISION_WRITE_FORBIDDEN"])
        return t, s, w, principal(request, site_code)

    async def body_of(request: Request) -> Any:
        try:
            return await request.json()
        except ValueError:
            return None  # not JSON: refused 422 by the closed shape, after the write gate

    def served(work: Callable[[], Any]) -> Any:
        def decided() -> Any:
            try:
                return work()
            except DecisionRefused as error:
                raise _decision(error) from error
        return gate.served(decided)

    @router.get(ROUTE)
    def list_scenarios(request: Request, site_code: str) -> Any:
        def work() -> Any:
            t, s, w = gate.opened(request, site_code, GET_KEYS)
            scenario_at = _instant(request, "scenario_at")
            raw = request.query_params.get("limit")
            limit = None
            if raw is not None:
                if not (raw.isascii() and raw.isdigit() and 1 <= int(raw) <= PAGE_MAX):
                    raise _Refused(422, "EV_LIMIT_INVALID", f"'limit' must be 1 to {PAGE_MAX}.")
                limit = int(raw)
            return service.list(t, s, site_code, w["lo"], w["hi"], w["known_at"], scenario_at, limit,
                                request.query_params.get("cursor"))
        return served(work)

    @router.post(ROUTE)
    async def create_scenario(request: Request, site_code: str) -> Any:
        admitted: list = []
        response = served(lambda: admitted.append(command(request, site_code)))
        if not admitted:
            return response
        t, s, w, who = admitted[0]
        body = await body_of(request)

        def work() -> Any:
            status, out = service.create(t, s, site_code, who, w["lo"], w["hi"], w["known_at"], body)
            return JSONResponse(status_code=status, content=out)
        return served(work)

    @router.post(ROUTE + "/{scenario_id}/revisions")
    async def correct_scenario(request: Request, site_code: str, scenario_id: str) -> Any:
        admitted: list = []
        response = served(lambda: admitted.append(command(request, site_code)))
        if not admitted:
            return response
        t, s, w, who = admitted[0]
        body = await body_of(request)

        def work() -> Any:
            status, out = service.correct(t, s, site_code, who, scenario_id, w["lo"], w["hi"], w["known_at"],
                                          body)
            return JSONResponse(status_code=status, content=out)
        return served(work)

    return router
