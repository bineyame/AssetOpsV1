"""Site-scoped exact Finding read (S4-01 phase 2) at the `A-claim-work-routes` API routes.

`D-2026-10-09-pre-s3-claim-routes-and-actor`: the Site code resolves inside the configured tenant; an
unauthenticated caller is 401 and an authenticated caller without the known Site scope is 403 (the `access`
seam decides both); a foreign or unknown Site, Finding or revision is 404; an unavailable store is a typed
503, never an empty claim. No human sign-in exists yet: the default composition admits the development
tenant's operator context exactly as the S3 Performance read does, and says so in every body.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.analytics.assessment_ports import AssessmentStoreUnavailable
from assetops_backend.analytics.finding_read import FindingReadService

Scope = Callable[[str], "tuple[str, UUID, UUID] | None"]
# (request, site_code) -> None to admit, else 401 or 403.
Access = Callable[[Request, str], "int | None"]
ACCESS_BASIS = ("DEVELOPMENT_TENANT_OPERATOR_CONTEXT: no authenticated human principal exists yet; the read is "
                "admitted for the configured development tenant, as the S3 Performance read is")


def development_access(request: Request, site_code: str) -> int | None:
    return None


def build_finding_router(reads: FindingReadService | None, scope: Scope, unavailable: tuple[type, ...] = (),
                         access: Access = development_access, access_basis: str = ACCESS_BASIS) -> APIRouter:
    router = APIRouter()
    down = (AssessmentStoreUnavailable, *unavailable)

    def open_scope(request: Request, site_code: str) -> tuple[str, UUID, UUID]:
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
        if reads is None:
            raise HTTPException(status_code=503, detail={"code": "FINDING_STORE_UNAVAILABLE",
                                                         "message": "No product database is configured."})
        return found

    def served(work: Callable[[], Any], missing: str) -> Any:
        try:
            body = work()
        except down as error:
            raise HTTPException(status_code=503, detail={"code": "FINDING_STORE_UNAVAILABLE",
                                                         "message": str(error)}) from error
        if body is None:
            raise HTTPException(status_code=404, detail=missing)
        return jsonable_encoder(body)

    @router.get("/api/sites/{site_code}/finding-windows/{day}")
    def window_state(request: Request, site_code: str, day: date) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        return {"site_code": code, "access_basis": access_basis,
                **served(lambda: reads.window_state(tenant_id, site_id, day), "No such window.")}

    @router.get("/api/sites/{site_code}/findings/{finding_id}")
    def finding(request: Request, site_code: str, finding_id: UUID, revision_id: UUID | None = None,
                after_revision_no: int = Query(0, ge=0), limit: int = Query(200, ge=1, le=500)) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        body = served(lambda: reads.finding(tenant_id, site_id, finding_id, revision_id,
                                            after_revision_no=after_revision_no, limit=limit),
                      "No such Finding or revision for this Site.")
        selected = body["selection"]["revision_id"]
        base = f"/sites/{code}/findings/{finding_id}"
        return {"site_code": code, "access_basis": access_basis, **body, "links": {
            "canonical": base, "selected_revision": f"{base}?revision_id={selected}",
            "api_selected_revision": f"/api{base}?revision_id={selected}",
            "canonical_finding": f"/sites/{code}/findings/{body['relations']['canonical_finding_id']}",
            "assessment_revisions": {str(a["assessment_revision_id"]):
                                     f"/api/sites/{code}/performance/dispatch/revisions/{a['assessment_revision_id']}"
                                     for a in body["revision"]["assessments"]},
            "windows": {w["day"]: f"/api/sites/{code}/performance/dispatch/windows/{w['day']}"
                        for w in body["revision"]["currentness"]["windows"]}}}

    return router
