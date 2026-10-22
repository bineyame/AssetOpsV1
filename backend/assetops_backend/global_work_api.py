"""W6-01a: the read-only global work list roots (`global-work-index-1`); A1 mounts `GET /api/work/incidents`.

`GET /api/work/incidents?from=&to=&known_at=&limit=&cursor=`. Order of checks (the W3 estate roots' order):

1. `authenticate(request)`: 401 `UNAUTHENTICATED` with `WWW-Authenticate: Bearer`, before any tenant lookup, Site
   enumeration, parameter parsing or cursor decoding.
2. The strict parser: typed 422 with `rows:null,total_count:null`.
3. One read-only snapshot: the tenant comes only from the server's registry; each imported candidate Site is admitted
   by the per-Site `access(request, site_code)` before any value enters a response or digest, so global lists never
   answer 403/404. 409 `WORK_BASIS_CHANGED`; 503 `WORK_STORE_UNAVAILABLE` without a database, a readable store or a
   valid cursor key, never an empty list.
"""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.estate_api import Authenticate, development_authenticate
from assetops_backend.finding_api import Access, development_access
from assetops_backend.work.global_index import (MESSAGES, GlobalWorkIndexService, GlobalWorkRefusal,
                                                parse_global_request)
from assetops_backend.work.model import WorkStoreUnavailable


def build_global_work_router(service: GlobalWorkIndexService | None, tenant: Callable[[], UUID | None], *,
                             authenticate: Authenticate = development_authenticate,
                             access: Access = development_access,
                             unavailable: tuple[type[BaseException], ...] = ()) -> APIRouter:
    router = APIRouter()
    down = (WorkStoreUnavailable, *unavailable)

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

    return router
