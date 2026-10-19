"""W2-05b EV replay route (`.agent/W2-05b-build-spec.md` commit 5 and q4 "Final commit 4-5" item 3).

`GET /api/sites/{site_code}/ev/replay?run_id=<id>` - mounted only under the Simulator Lab gate, beside the cold
replay route it mirrors. `main.create_app` passes its injected `ev_access`/`ev_owner` (N1), the same callables the
EV choice list uses; production defaults are `development_access`/`no_owner_principal`, so every production read
answers 403. Refusals use the shared envelope `{error:{code,message}}`, checked in this order: 401
`UNAUTHENTICATED`, 403 `SITE_SCOPE_FORBIDDEN`, 422 `EV_REPLAY_PARAMETER_INVALID`, 404 `SITE_NOT_FOUND`, 503
`EV_REPLAY_UNAVAILABLE`, 404 `RUN_NOT_FOUND`. No SQL here; the service holds none either.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from assetops_backend.ev_replay import EvReplayService, EvReplayUnavailable, EvRunNotFound
from assetops_backend.finding_api import Access, Scope
from assetops_backend.runs.identity import RUN_ID_PATTERN
from assetops_backend.sites.ports import SiteStoreUnavailable

EV_REPLAY_ROUTE = "/api/sites/{site_code}/ev/replay"
# (request, site_code) -> True only for an authenticated Lab owner of the Site.
OwnerRole = Callable[[Request, str], bool]


def _refusal(status: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}}, headers=headers)


def build_ev_replay_router(service: EvReplayService | None, scope: Scope, *, access: Access,
                           owner: OwnerRole) -> APIRouter:
    router = APIRouter()

    @router.get(EV_REPLAY_ROUTE)
    def ev_replay(request: Request, site_code: str) -> Any:
        refusal = access(request, site_code)
        if refusal == 401:
            return _refusal(401, "UNAUTHENTICATED", "Sign in to read an EV Lab replay.",
                            {"WWW-Authenticate": "Bearer"})
        if refusal == 403 or not owner(request, site_code):
            return _refusal(403, "SITE_SCOPE_FORBIDDEN", f"No Lab owner access to Site {site_code!r}.")
        params = request.query_params.multi_items()
        if len(params) != 1 or params[0][0] != "run_id" or not RUN_ID_PATTERN.match(params[0][1]):
            return _refusal(422, "EV_REPLAY_PARAMETER_INVALID", "Exactly one valid 'run_id' is required.")
        run_id = params[0][1]
        try:
            scoped = scope(site_code)
        except SiteStoreUnavailable as error:
            return _refusal(503, "EV_REPLAY_UNAVAILABLE", str(error))
        if scoped is None:
            return _refusal(404, "SITE_NOT_FOUND", f"No registered Site {site_code!r} in this tenant.")
        if service is None:
            return _refusal(503, "EV_REPLAY_UNAVAILABLE", "No evidence ledger is configured.")
        code, tenant_id, site_id = scoped
        try:
            return service.replay(tenant_id, site_id, code, run_id)
        except EvRunNotFound:
            return _refusal(404, "RUN_NOT_FOUND", f"No EV run {run_id!r} at Site {site_code!r}.")
        except EvReplayUnavailable as error:
            return _refusal(503, "EV_REPLAY_UNAVAILABLE", str(error))

    return router
