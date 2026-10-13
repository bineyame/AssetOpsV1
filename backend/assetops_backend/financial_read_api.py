"""Site financial assumption reads (S4-02a phase 2, packet item 3).

`GET /api/sites/{site_code}/financial-assumptions?key=&valid_at=&recorded_at=&after_revision_no=&limit=`
returns the series at the current or a recorded cutoff: the effective price timeline, the selection at
`valid_at` (PRICED, NO_PRICE or CONFLICT, never a default), and a bounded page of revisions.
`GET /api/sites/{site_code}/financial-assumptions/{revision_id}` returns that exact revision; an unknown,
malformed or foreign ID is 404/422 and never falls back to the latest price.

Scope and refusal semantics are the Finding read's (`finding_api`): 401 / 403 from the access seam, 404 for
a Site the tenant does not know, 503 `ASSUMPTION_STORE_UNAVAILABLE` without a database or on a store failure.
Reads are admitted under the development tenant operator context, like every other Site read. The human
write route lives in `financial_api` with its own default `no_verified_principal`; nothing here writes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.finding_api import ACCESS_BASIS, Access, Scope, development_access
from assetops_backend.financials.assumption_read import PAGE_LIMIT, AssumptionReadService, known_key


def build_financial_read_router(reads: AssumptionReadService | None, scope: Scope,
                                unavailable: tuple[type, ...] = (), access: Access = development_access,
                                access_basis: str = ACCESS_BASIS) -> APIRouter:
    router = APIRouter()

    def store_down(message: str) -> HTTPException:
        return HTTPException(status_code=503, detail={"code": "ASSUMPTION_STORE_UNAVAILABLE", "message": message})

    def open_scope(request: Request, site_code: str) -> tuple[str, UUID, UUID]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read Site prices."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        found = scope(site_code)
        if found is None or refusal == 404:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if reads is None:
            raise store_down("No product database is configured.")
        return found

    def served(work: Callable[[], Any]) -> Any:
        try:
            return work()
        except unavailable as error:
            raise store_down(str(error)) from error

    def zoned(name: str, at: datetime | None) -> datetime | None:
        if at is not None and (at.tzinfo is None or at.utcoffset() is None):
            raise HTTPException(status_code=422, detail={"code": "INSTANT_NOT_ZONED",
                                                         "message": f"{name} must carry a timezone offset."})
        return at

    @router.get("/api/sites/{site_code}/financial-assumptions")
    def series(request: Request, site_code: str, key: str = "diesel_price_per_litre",
               valid_at: datetime | None = None, recorded_at: datetime | None = None,
               after_revision_no: int = Query(0, ge=0), limit: int = Query(PAGE_LIMIT, ge=1, le=PAGE_LIMIT)
               ) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        if not known_key(key):
            raise HTTPException(status_code=422, detail={"code": "UNKNOWN_ASSUMPTION_KEY",
                                                         "message": f"No assumption key {key!r}."})
        valid_at, recorded_at = zoned("valid_at", valid_at), zoned("recorded_at", recorded_at)
        body = served(lambda: reads.series(tenant_id, site_id, key, valid_at=valid_at, recorded_at=recorded_at,
                                           after_revision_no=after_revision_no, limit=limit))
        base = f"/api/sites/{code}/financial-assumptions"
        page = body["revision_page"]
        links: dict[str, Any] = {
            "assumptions": f"/sites/{code}/financials/assumptions",
            "revisions": {str(r["revision_id"]): f"{base}/{r['revision_id']}" for r in body["revisions"]}}
        if page["next_after_revision_no"] is not None:
            links["api_next_page"] = (f"{base}?key={key}&after_revision_no={page['next_after_revision_no']}"
                                      f"&limit={page['limit']}"
                                      + ("" if recorded_at is None else f"&recorded_at={recorded_at.isoformat()}"))
        return jsonable_encoder({"site_code": code, "access_basis": access_basis, **body, "links": links})

    @router.get("/api/sites/{site_code}/financial-assumptions/{revision_id}")
    def revision(request: Request, site_code: str, revision_id: UUID) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        body = served(lambda: reads.revision(tenant_id, site_id, revision_id))
        if body is None:
            raise HTTPException(status_code=404, detail={
                "code": "ASSUMPTION_REVISION_NOT_FOUND",
                "message": "No such price revision for this Site; the latest price is not substituted."})
        return jsonable_encoder({"site_code": code, "access_basis": access_basis, **body, "links": {
            "assumptions": f"/sites/{code}/financials/assumptions?revision_id={revision_id}",
            "api_series": f"/api/sites/{code}/financial-assumptions"}})

    return router
