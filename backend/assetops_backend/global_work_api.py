"""W6-01a/b: the read-only global work list roots (`global-work-index-1`); A1 mounts `GET /api/work/incidents`,
B1 `GET /api/work/maintenance` and `GET /api/work/preventive`, E1 `GET /api/work/operational-records?kind=` (same
checks, same order).

`GET /api/work/incidents?from=&to=&known_at=&limit=&cursor=`. Order of checks (the W3 estate roots' order):

1. `authenticate(request)`: 401 `UNAUTHENTICATED` with `WWW-Authenticate: Bearer`, before any tenant lookup, Site
   enumeration, parameter parsing or cursor decoding.
2. The strict parser: typed 422 with `rows:null,total_count:null`.
3. One read-only snapshot: the tenant comes only from the server's registry; each imported candidate Site is admitted
   by the per-Site `access(request, site_code)` before any value enters a response or digest, so global lists never
   answer 403/404. 409 `WORK_BASIS_CHANGED`; 503 `WORK_STORE_UNAVAILABLE` without a database, a readable store or a
   valid cursor key, never an empty list.

W6-01c C1 mounts `GET /api/work/requests/{case_id}?site_id={site_code}&known_at=` (`global-work-detail-1`, a
MAINTENANCE_REQUEST only; pre-flight ruling "C1 outer wire and selection"). Order: `authenticate` 401 `Sign in to
read work.`; exactly one nonempty `site_id`, else 404 `WORK_CASE_NOT_FOUND` with no store read; the W4 `read_scope`
order (`access` 401/403 `SITE_SCOPE_FORBIDDEN`, `scope` 503/404 `SITE_NOT_FOUND`); then the case UUID (404) and
`known_at` (W4 422) and the one snapshot. Refusals are detail-only `{"detail":{"code","message"}}`; unknown query
keys are ignored.
"""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.estate_api import Authenticate, development_authenticate
from assetops_backend.finding_api import Access, Scope, development_access
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.ports import SiteStoreUnavailable
from assetops_backend.work.global_detail import GlobalWorkDetailService
from assetops_backend.work.global_index import (MESSAGES, GlobalWorkIndexService, GlobalWorkRefusal,
                                                parse_global_request)
from assetops_backend.work.model import MESSAGES as WORK_MESSAGES
from assetops_backend.work.model import WorkRefused, WorkStoreUnavailable
from assetops_backend.work_api import WorkGate


def build_global_work_router(service: GlobalWorkIndexService | None, tenant: Callable[[], UUID | None], *,
                             authenticate: Authenticate = development_authenticate,
                             access: Access = development_access,
                             unavailable: tuple[type[BaseException], ...] = (),
                             details: GlobalWorkDetailService | None = None, scope: Scope | None = None) -> APIRouter:
    router = APIRouter()
    down = (WorkStoreUnavailable, *unavailable)

    def no_store(site_code: str) -> None:
        """Without a detail service or Site scope the detail is the existing 503, after access (R373 ruling Q2)."""
        raise WorkStoreUnavailable("no global work detail store is composed")

    # R373 (B19-15) ruling Q2: detail admission IS the W4 Site Work `read_scope` (access 401/403, then scope 503/404),
    # with the same callable as the lists, so a denied Site answers W4's 403 before any Site or case lookup.
    gate = WorkGate(scope if details is not None and scope is not None else no_store, tuple(unavailable), access)

    def store_down() -> HTTPException:
        return HTTPException(status_code=503, detail={"code": "WORK_STORE_UNAVAILABLE",
                                                      "message": MESSAGES["WORK_STORE_UNAVAILABLE"],
                                                      "rows": None, "total_count": None})

    def serve(kind: str, request: Request) -> dict[str, Any]:
        if authenticate(request) == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": MESSAGES["UNAUTHENTICATED"],
                                        "rows": None, "total_count": None})
        try:
            parsed = parse_global_request(kind, request.query_params.multi_items())
            if service is None:
                raise store_down()
            body = service.read(tenant(), kind, parsed, lambda code: access(request, code) is None)
        except GlobalWorkRefusal as error:
            headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else None
            raise HTTPException(status_code=error.status, detail=error.detail, headers=headers) from error
        except down as error:
            raise store_down() from error
        return jsonable_encoder(body)

    @router.get("/api/work/incidents")
    def global_incidents(request: Request) -> dict[str, Any]:
        return serve("incidents", request)

    @router.get("/api/work/maintenance")
    def global_maintenance(request: Request) -> dict[str, Any]:
        return serve("maintenance", request)

    @router.get("/api/work/preventive")
    def global_preventive(request: Request) -> dict[str, Any]:
        return serve("preventive", request)

    @router.get("/api/work/operational-records")
    def global_operational_records(request: Request) -> dict[str, Any]:
        return serve("operational-records", request)  # W6-01e E1; `kind` is parsed by the shared parser

    def refuse(status: int, code: str, message: str | None = None) -> HTTPException:
        """C1 detail-only refusal body: `{code, message}`, never the list `rows`/`total_count`."""
        headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
        return HTTPException(status_code=status, headers=headers,
                             detail={"code": code, "message": WORK_MESSAGES[code] if message is None else message})

    @router.get("/api/work/requests/{case_id}")
    def global_request_detail(request: Request, case_id: str) -> dict[str, Any]:
        if authenticate(request) == 401:
            raise refuse(401, "UNAUTHENTICATED", "Sign in to read work.")
        codes = request.query_params.getlist("site_id")
        if len(codes) != 1 or not codes[0]:
            raise refuse(404, "WORK_CASE_NOT_FOUND")
        tenant_id, site_id, site_code = gate.read_scope(request, codes[0])
        if details is None:  # unreachable: `no_store` already refused 503; kept for type narrowing
            raise refuse(503, "WORK_STORE_UNAVAILABLE")
        try:
            body = details.detail(tenant_id, site_id, site_code, case_id, request.query_params.getlist("known_at"))
        except WorkRefused as refused:
            raise refuse(refused.status, refused.code, refused.message) from refused
        except (SiteStoreUnavailable, FoundationStoreError, *down) as error:
            raise refuse(503, "WORK_STORE_UNAVAILABLE") from error
        return jsonable_encoder(body)

    return router
