"""W2-02 cold replay route (`.agent/W2-02-build-spec.md` "Commit (4) exact contract").

`GET /api/sites/{site_code}/cold/replay?run_id=<id>` - mounted only under the Simulator Lab gate. The caller
passes the existing Finding-route `Access` seam and a Lab owner-role check. Production composition has no owner
principal, so it composes `no_owner_principal` and every production read answers 403; `development_owner` is for
injected tests only. Refusals use the shared envelope `{error:{code,message}}`: 401 `UNAUTHENTICATED`, 403
`SITE_SCOPE_FORBIDDEN`, 422 `COLD_REPLAY_PARAMETER_INVALID`, 404 `SITE_NOT_FOUND` / `RUN_NOT_FOUND`, 503
`COLD_REPLAY_UNAVAILABLE`. No SQL here; the service holds none either.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from assetops_backend.cold_replay import ColdReplayService, ColdReplayUnavailable, ColdRunNotFound
from assetops_backend.finding_api import Access, Scope
from assetops_backend.sites.ports import SiteStoreUnavailable

COLD_REPLAY_ROUTE = "/api/sites/{site_code}/cold/replay"
# (request, site_code) -> True only for an authenticated Lab owner of the Site.
OwnerRole = Callable[[Request, str], bool]


def no_owner_principal(request: Request, site_code: str) -> bool:
    """Production: no owner principal exists yet, so no caller is a Lab owner (403, not an implicit grant)."""
    return False


def development_owner(request: Request, site_code: str) -> bool:
    """Injected tests only."""
    return True


def _refusal(status: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}}, headers=headers)


def build_cold_replay_router(service: ColdReplayService | None, scope: Scope, *, access: Access,
                             owner: OwnerRole) -> APIRouter:
    router = APIRouter()

    @router.get(COLD_REPLAY_ROUTE)
    def cold_replay(request: Request, site_code: str) -> Any:
        refusal = access(request, site_code)
        if refusal == 401:
            return _refusal(401, "UNAUTHENTICATED", "Sign in to read a cold Lab replay.",
                            {"WWW-Authenticate": "Bearer"})
        if refusal == 403 or not owner(request, site_code):
            return _refusal(403, "SITE_SCOPE_FORBIDDEN", f"No Lab owner access to Site {site_code!r}.")
        params = request.query_params.multi_items()
        if len(params) != 1 or params[0][0] != "run_id" or not params[0][1]:
            return _refusal(422, "COLD_REPLAY_PARAMETER_INVALID", "Exactly one nonempty 'run_id' is required.")
        run_id = params[0][1]
        try:
            scoped = scope(site_code)
        except SiteStoreUnavailable as error:
            return _refusal(503, "COLD_REPLAY_UNAVAILABLE", str(error))
        if scoped is None:
            return _refusal(404, "SITE_NOT_FOUND", f"No registered Site {site_code!r} in this tenant.")
        if service is None:
            return _refusal(503, "COLD_REPLAY_UNAVAILABLE", "No evidence ledger is configured.")
        code, tenant_id, site_id = scoped
        try:
            return service.replay(tenant_id, site_id, code, run_id)
        except ColdRunNotFound:
            return _refusal(404, "RUN_NOT_FOUND", f"No cold run {run_id!r} at Site {site_code!r}.")
        except ColdReplayUnavailable as error:
            return _refusal(503, "COLD_REPLAY_UNAVAILABLE", str(error))

    return router
