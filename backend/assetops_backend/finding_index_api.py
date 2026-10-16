"""Site Finding index route (S4-04 phase 1, `I-finding-index`).

`GET /api/sites/{site_code}/finding-index?domain=mini-grid-dispatch&from=&to=&limit=&cursor=`
(`D-2026-10-15-s404-contract`). Order of checks, so that no refusal leaks a count or an empty claim:

1. Site access and scope with the Finding route rules: 401 / 403 / 404 (no foreign count), 503 without a store.
2. Explicit request validation: unsupported domain, non-UTC or reversed window, more than 31 days, bad limit or
   a malformed cursor are a typed 422 with no status, rows or count.
3. The S3 Performance cutover gate: closed is 409 `PERFORMANCE_CUTOVER_CLOSED` with its reason; exact pinned
   Finding detail stays the separate audit route.
4. The read: 409 `INDEX_CONTINUITY_LIMIT` past the discovery cap, 409 `INDEX_BASIS_CHANGED` for a well-formed
   cursor whose scope or fenced basis changed; otherwise 200 with a typed status, where only `CURRENT` carries
   rows and a `total_count`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.analytics.assessment_ports import AssessmentStoreUnavailable
from assetops_backend.analytics.finding_index import FindingIndexService, IndexRefusal, parse_request
from assetops_backend.analytics.ports import AssessmentStoreUnavailable as FileAssessmentStoreUnavailable
from assetops_backend.evidence.ports import EvidenceStoreUnavailable
from assetops_backend.finding_api import ACCESS_BASIS, Access, Gate, Scope, development_access, no_gate


def build_finding_index_router(index: FindingIndexService | None, scope: Scope, unavailable: tuple[type, ...] = (),
                               access: Access = development_access, access_basis: str = ACCESS_BASIS,
                               gate: Gate = no_gate) -> APIRouter:
    router = APIRouter()
    down = (AssessmentStoreUnavailable, FileAssessmentStoreUnavailable, EvidenceStoreUnavailable, *unavailable)

    def store_down(error: Exception) -> HTTPException:
        return HTTPException(status_code=503, detail={"code": "FINDING_STORE_UNAVAILABLE", "message": str(error)})

    @router.get("/api/sites/{site_code}/finding-index")
    def finding_index(request: Request, site_code: str, domain: str | None = None,
                      from_: str | None = Query(None, alias="from"), to: str | None = None,
                      limit: str | None = None, cursor: str | None = None) -> dict[str, Any]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read Findings."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        found = scope(site_code)
        if found is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if index is None:
            raise HTTPException(status_code=503, detail={"code": "FINDING_STORE_UNAVAILABLE",
                                                         "message": "No product database is configured."})
        code, tenant_id, site_id = found
        try:
            parsed = parse_request(domain, from_, to, limit, cursor)
        except IndexRefusal as error:
            raise HTTPException(status_code=error.status, detail=error.detail) from error
        try:
            permitted, reason = gate(code, tenant_id, site_id)
        except down as error:
            raise store_down(error) from error
        if not permitted:
            raise HTTPException(status_code=409, detail={
                "code": "PERFORMANCE_CUTOVER_CLOSED", "read": "CLOSED", "message": reason,
                "rows": None, "total_count": None,
                "note": "The Finding index's authority is the selected S3 assessment, which is closed for this Site; "
                        "no Finding rows, count or no-Findings verdict is shown. An exact revision_id Finding "
                        "link reads audit material."})
        try:
            body = index.read(UUID(str(tenant_id)), UUID(str(site_id)), code, parsed, access_basis=access_basis)
        except IndexRefusal as error:
            raise HTTPException(status_code=error.status, detail=error.detail) from error
        except down as error:
            raise store_down(error) from error
        return jsonable_encoder({**body, "source_gate": {"permitted": True, "reason": reason}})

    return router
