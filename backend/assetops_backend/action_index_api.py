"""S6-03 Site Work Action index route (`I-site-action-index-read`, `D-2026-10-16-a-action-index`).

`GET /api/sites/{site_code}/action-index?from=&to=&limit=&cursor=`. Order of checks, so no refusal leaks a count or
an empty claim (`D-2026-10-09-pre-s3-claim-routes-and-actor`):

1. Site access and scope: 401 unauthenticated, 403 known forbidden, 404 foreign or unknown Site, 503 without a store.
2. Explicit request validation: a missing, non-UTC, reversed or longer-than-31-day window, a bad limit or a
   malformed cursor is a typed 422 with no rows or count.
3. The read: 503 `ACTION_STORE_UNAVAILABLE` when the store fails, 409 `ACTION_INDEX_INCONSISTENT` for an
   inconsistent snapshot, 409 `ACTION_INDEX_BASIS_CHANGED` for a cursor whose scope or fence changed; otherwise
   200 `CURRENT` with rows and a `total_count` (zero only from a successful scoped read).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.actions.ports import ActionStoreUnavailable
from assetops_backend.actions.site_index import ActionIndexRefusal, ActionIndexService, parse_request
from assetops_backend.finding_api import ACCESS_BASIS, Access, Scope, development_access


def build_action_index_router(index: ActionIndexService | None, scope: Scope, unavailable: tuple[type, ...] = (),
                              access: Access = development_access, access_basis: str = ACCESS_BASIS) -> APIRouter:
    router = APIRouter()
    down = (ActionStoreUnavailable, *unavailable)

    def store_down(message: str) -> HTTPException:
        return HTTPException(status_code=503, detail={"code": "ACTION_STORE_UNAVAILABLE", "message": message,
                                                      "rows": None, "total_count": None})

    @router.get("/api/sites/{site_code}/action-index")
    def action_index(request: Request, site_code: str, from_: str | None = Query(None, alias="from"),
                     to: str | None = None, limit: str | None = None, cursor: str | None = None) -> dict[str, Any]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read Actions."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        found = scope(site_code)
        if found is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if index is None:
            raise store_down("No product database is configured.")
        code, tenant_id, site_id = found
        try:
            parsed = parse_request(from_, to, limit, cursor)
            body = index.read(UUID(str(tenant_id)), UUID(str(site_id)), code, parsed, access_basis=access_basis)
        except ActionIndexRefusal as error:
            raise HTTPException(status_code=error.status, detail=error.detail) from error
        except down as error:
            raise store_down(str(error)) from error
        return jsonable_encoder(body)

    return router
