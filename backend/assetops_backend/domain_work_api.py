"""W5-02a K1a: the domain Action command routes under `/api/sites/{site_code}/domain-work`.

`.agent/W5-02-build-spec.md` "Command/read wire" and Architect pre-flight ruling A2:

- `POST /actions` - a cold domain Action root from one exact selected Finding (`domain-action-1`).
- `POST /actions/{action_id}/intents` - a declared intent version (`domain-action-intent-1`).
- `POST /actions/{action_id}/case-links` - an explicit link to one W4 case revision/event
  (`domain-action-case-link-1`).

Each returns 201 for a first submission and 200 with the original body for an identical retry. Refusal order:
the shared W4 `WorkGate` (401 `UNAUTHENTICATED`, 403 `SITE_SCOPE_FORBIDDEN`, 404 `SITE_NOT_FOUND`, write grant
401/403, 503 `WORK_STORE_UNAVAILABLE`), then the service (absent SERVICE principal 403, 422, 404 `ACTION_NOT_FOUND`,
409). Refusals are `{"detail":{"code","message"}}`. The SERVICE principal is injected server-side only.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from assetops_backend.work.domain_action import DomainIntentRefused
from assetops_backend.work.domain_intent import DomainIntentService
from assetops_backend.work.model import MESSAGES, WorkRefused, WorkStoreUnavailable
from assetops_backend.work_api import WorkGate

_NOT_JSON = object()  # a body that is not JSON reaches the service as a non-object (422 after the write gate)


def _refuse(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def build_domain_work_router(service: DomainIntentService | None, gate: WorkGate,
                             unavailable: tuple[type, ...] = ()) -> APIRouter:
    router = APIRouter()
    down = (WorkStoreUnavailable, *unavailable)

    async def body_of(request: Request) -> Any:
        try:
            return await request.json()
        except ValueError:
            return _NOT_JSON

    def run(work: Callable[[], tuple[int, dict[str, Any]]]) -> JSONResponse:
        try:
            status, body = work()
        except DomainIntentRefused as refused:
            raise _refuse(refused.status, refused.code, refused.message) from refused
        except WorkRefused as refused:
            raise _refuse(refused.status, refused.code, refused.message) from refused
        except down as error:
            raise _refuse(503, "WORK_STORE_UNAVAILABLE", MESSAGES["WORK_STORE_UNAVAILABLE"]) from error
        return JSONResponse(status_code=status, content=body)

    @router.post("/api/sites/{site_code}/domain-work/actions")
    async def create_action(request: Request, site_code: str) -> JSONResponse:
        tenant_id, site_id, code, who = gate.open_scope(request, site_code, service is not None)
        body = await body_of(request)
        return run(lambda: service.create_action(tenant_id, site_id, code, body, who))

    @router.post("/api/sites/{site_code}/domain-work/actions/{action_id}/intents")
    async def post_intent(request: Request, site_code: str, action_id: str) -> JSONResponse:
        tenant_id, site_id, code, who = gate.open_scope(request, site_code, service is not None)
        body = await body_of(request)
        return run(lambda: service.post_intent(tenant_id, site_id, code, action_id, body, who))

    @router.post("/api/sites/{site_code}/domain-work/actions/{action_id}/case-links")
    async def post_case_link(request: Request, site_code: str, action_id: str) -> JSONResponse:
        tenant_id, site_id, code, who = gate.open_scope(request, site_code, service is not None)
        body = await body_of(request)
        return run(lambda: service.post_case_link(tenant_id, site_id, code, action_id, body, who))

    return router
