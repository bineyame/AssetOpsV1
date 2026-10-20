"""W4-01 commit 3: the Site-scoped work command routes (`.agent/W4-01-build-spec.md` "API wire and refusals").

Under `/api/sites/{site_code}/work` (Lane A mount in `main.py`):

- `POST /cases` - create an Incident or a MaintenanceWorkRequest (`work-case-1`).
- `POST /cases/{case_id}/events` - ASSIGN/COMPLETE/COMMENT/CLOSE/REOPEN/CANCEL (`work-event-1`).
- `POST /cases/{case_id}/revisions` - append a correction revision.
- `POST /cases/{case_id}/records` - performed activity on a request (`maintenance-record-1`, outcome UNVERIFIED).
- `POST /plans` - an immutable DRAFT plan or its correction successor (`maintenance-plan-1`).
- `POST /operational-records` - an authored SUBMITTED record or its correction (`operational-record-1`).
- `GET /cases/{case_id}?known_at=` - the B3 `work-case-detail-1` read at one cutoff (Run 3 ruling 8).

Each POST returns 201 for a first submission and 200 with the stored exact body for an identical retry.
Refusal order (Run 2 ruling reading 2): Site read access 401/403 (`finding_api.Access`), unknown Site 404, the
write grant (`command_access`, the `action_api.py` pattern) 401/403, store 503 when no database is configured,
then the service: absent server SERVICE principal 403 `WORK_WRITE_FORBIDDEN`, closed shape 422, development USER
403, attestation 422, and only then hash/idempotency and first-write checks. A refusal writes nothing.

The SERVICE principal is server-side identity injected through `principal`; a client-supplied actor ID never
authenticates it (closure 3 Q28, Run 1 ruling 1). The development composition injects none, so a write there is
403. `authorization_basis` is derived by the service from that principal, never read from the request.
"""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from assetops_backend.finding_api import Access, Scope, development_access
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.ports import SiteStoreUnavailable
from assetops_backend.work.detail import WorkDetailService
from assetops_backend.work.model import MESSAGES, WorkRefused, WorkStoreUnavailable
from assetops_backend.work.service import WorkService

# Closure 3 Q28: the W4 contract constant for the development fixture SERVICE principal. Only a server-side
# principal injection returns it; it is never read from a request body.
W401_FIXTURE_SERVICE_PRINCIPAL_ID = "service:w401-fixture"

# (request, site_code) -> the authenticated server SERVICE principal ID, or None when there is none.
Principal = Callable[[Request, str], "str | None"]

_NOT_JSON = object()  # a body that is not JSON reaches the service as a non-object (422 after the write gate)


def no_service_principal(request: Request, site_code: str) -> str | None:
    """Development has no authenticated SERVICE principal: every work write is refused 403."""
    return None


def _refuse(status: int, code: str, message: str) -> HTTPException:
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return HTTPException(status_code=status, headers=headers, detail={"code": code, "message": message})


def build_work_router(service: WorkService | None, scope: Scope, unavailable: tuple[type, ...] = (),
                      access: Access = development_access, command_access: Access = development_access,
                      principal: Principal = no_service_principal,
                      details: WorkDetailService | None = None) -> APIRouter:
    router = APIRouter()
    down = (WorkStoreUnavailable, *unavailable)

    def read_scope(request: Request, site_code: str) -> tuple[UUID, UUID, str]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise _refuse(401, "UNAUTHENTICATED", "Sign in to read work.")
        if refusal == 403:
            raise _refuse(403, "SITE_SCOPE_FORBIDDEN", f"No access to Site '{site_code}'.")
        try:  # q3 reading 5: a Site scope/storage outage is this API's 503, never a raw 500 or a 404
            found = scope(site_code)
        except (SiteStoreUnavailable, FoundationStoreError, *down) as error:
            raise _refuse(503, "WORK_STORE_UNAVAILABLE", MESSAGES["WORK_STORE_UNAVAILABLE"]) from error
        if found is None:
            raise _refuse(404, "SITE_NOT_FOUND", f"No imported Site '{site_code}' in this tenant.")
        code, tenant_id, site_id = found
        return tenant_id, site_id, code

    def open_scope(request: Request, site_code: str) -> tuple[UUID, UUID, str | None]:
        tenant_id, site_id, _ = read_scope(request, site_code)
        grant = command_access(request, site_code)
        if grant == 401:
            raise _refuse(401, "UNAUTHENTICATED", "Sign in to read work.")
        if grant == 403:
            raise _refuse(403, "WORK_WRITE_FORBIDDEN", MESSAGES["WORK_WRITE_FORBIDDEN"])
        if service is None:
            raise _refuse(503, "WORK_STORE_UNAVAILABLE", MESSAGES["WORK_STORE_UNAVAILABLE"])
        return tenant_id, site_id, principal(request, site_code)

    async def body_of(request: Request) -> Any:
        try:
            return await request.json()
        except ValueError:
            return _NOT_JSON

    def run(work: Callable[[], tuple[int, dict[str, Any]]]) -> JSONResponse:
        try:
            status, body = work()
        except WorkRefused as refused:
            raise _refuse(refused.status, refused.code, refused.message) from refused
        except down as error:
            raise _refuse(503, "WORK_STORE_UNAVAILABLE", MESSAGES["WORK_STORE_UNAVAILABLE"]) from error
        return JSONResponse(status_code=status, content=body)

    @router.post("/api/sites/{site_code}/work/cases")
    async def create_case(request: Request, site_code: str) -> JSONResponse:
        tenant_id, site_id, who = open_scope(request, site_code)
        body = await body_of(request)
        return run(lambda: service.create_case(tenant_id, site_id, body, who))

    @router.post("/api/sites/{site_code}/work/cases/{case_id}/events")
    async def post_event(request: Request, site_code: str, case_id: str) -> JSONResponse:
        tenant_id, site_id, who = open_scope(request, site_code)
        body = await body_of(request)
        return run(lambda: service.post_event(tenant_id, site_id, case_id, body, who))

    @router.post("/api/sites/{site_code}/work/cases/{case_id}/revisions")
    async def post_revision(request: Request, site_code: str, case_id: str) -> JSONResponse:
        tenant_id, site_id, who = open_scope(request, site_code)
        body = await body_of(request)
        return run(lambda: service.post_revision(tenant_id, site_id, case_id, body, who))

    @router.post("/api/sites/{site_code}/work/cases/{case_id}/records")
    async def post_record(request: Request, site_code: str, case_id: str) -> JSONResponse:
        tenant_id, site_id, who = open_scope(request, site_code)
        body = await body_of(request)
        return run(lambda: service.post_record(tenant_id, site_id, case_id, body, who))

    @router.post("/api/sites/{site_code}/work/plans")
    async def post_plan(request: Request, site_code: str) -> JSONResponse:
        tenant_id, site_id, who = open_scope(request, site_code)
        body = await body_of(request)
        return run(lambda: service.post_plan(tenant_id, site_id, body, who))

    @router.post("/api/sites/{site_code}/work/operational-records")
    async def post_operational_record(request: Request, site_code: str) -> JSONResponse:
        tenant_id, site_id, who = open_scope(request, site_code)
        body = await body_of(request)
        return run(lambda: service.post_operational_record(tenant_id, site_id, body, who))

    @router.get("/api/sites/{site_code}/work/cases/{case_id}")
    async def case_detail(request: Request, site_code: str, case_id: str) -> JSONResponse:
        """B3 `work-case-detail-1` at the optional `known_at` (Run 3 ruling 8): read access, Site scope, then
        `known_at`, then the one snapshot. Refusals are `{"detail":{"code","message"}}` (no list fields)."""
        tenant_id, site_id, code = read_scope(request, site_code)
        if details is None:
            raise _refuse(503, "WORK_STORE_UNAVAILABLE", MESSAGES["WORK_STORE_UNAVAILABLE"])
        known = request.query_params.getlist("known_at")
        return run(lambda: (200, details.detail(tenant_id, site_id, code, case_id, known)))

    return router
