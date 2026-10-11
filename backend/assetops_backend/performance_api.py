"""Imported-Site Performance > Dispatch read over the durable dispatch-3.1 assessment (S3-01 phase 3).

Routes follow `D-2026-10-09-pre-s3-claim-routes-and-actor`: the Site code is
resolved inside the configured tenant (never taken from the client), a foreign
or unknown Site, run or revision is 404, and an unbuilt or lagging read returns
a typed state, never a fabricated empty one. The window/run/revision reads stay
closed (409 PERFORMANCE_CUTOVER_CLOSED) until the file-backed comparison and
lineage gate passes; the gate itself is always readable.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from assetops_backend.analytics.assessment_ports import AssessmentStoreUnavailable
from assetops_backend.analytics.dispatch_read import DispatchReadService
from assetops_backend.analytics.ports import AssessmentStoreUnavailable as FileAssessmentStoreUnavailable
from assetops_backend.evidence.ports import EvidenceStoreUnavailable

Scope = Callable[[str], "tuple[str, UUID, UUID] | None"]
Gate = Callable[[str, UUID, UUID], "tuple[bool, str]"]
Report = Callable[[str], "dict[str, Any] | None"]

# Review R3: an unreadable comparison report or file-backed baseline is the same typed 503 as an
# unavailable assessment store, never a 500 and never an open gate.
_UNAVAILABLE = (AssessmentStoreUnavailable, FileAssessmentStoreUnavailable, EvidenceStoreUnavailable)


def _unavailable(error: Exception) -> dict[str, str]:
    code = ("ASSESSMENT_STORE_UNAVAILABLE" if isinstance(error, AssessmentStoreUnavailable)
            else "COMPARISON_STORE_UNAVAILABLE")
    return {"code": code, "message": str(error) or code}


def build_performance_router(reads: DispatchReadService | None, scope: Scope, gate: Gate,
                             report: Report | None = None) -> APIRouter:
    router = APIRouter()

    def resolve(site_code: str) -> tuple[str, UUID, UUID]:
        found = scope(site_code)
        if found is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        return found

    def open_scope(site_code: str) -> tuple[str, UUID, UUID]:
        code, tenant_id, site_id = resolve(site_code)
        if reads is None:
            raise HTTPException(status_code=503, detail={"code": "ASSESSMENT_STORE_UNAVAILABLE",
                                                         "message": "No product database is configured."})
        try:
            allowed, reason = gate(code, tenant_id, site_id)
        except _UNAVAILABLE as error:
            raise HTTPException(status_code=503, detail=_unavailable(error)) from error
        if not allowed:
            raise HTTPException(status_code=409, detail={"code": "PERFORMANCE_CUTOVER_CLOSED", "message": reason})
        return code, tenant_id, site_id

    def served(work: Callable[[], Any], missing: str) -> Any:
        try:
            body = work()
        except AssessmentStoreUnavailable as error:
            raise HTTPException(status_code=503, detail={"code": "ASSESSMENT_STORE_UNAVAILABLE",
                                                         "message": str(error)}) from error
        if body is None:
            raise HTTPException(status_code=404, detail=missing)
        return jsonable_encoder(body)

    @router.get("/api/sites/{site_code}/performance/dispatch/cutover", response_model=None)
    def cutover(site_code: str) -> dict[str, Any] | JSONResponse:
        code, tenant_id, site_id = resolve(site_code)
        try:
            allowed, reason = gate(code, tenant_id, site_id)
            comparison = None if report is None else report(code)
        except _UNAVAILABLE as error:
            detail = _unavailable(error)
            return JSONResponse(status_code=503, content={
                "site_code": code, "read": "CLOSED", "permitted": False, "comparison": None, "unavailable": detail,
                "reason": f"The Performance read is unavailable: {detail['message']}"})
        return {"site_code": code, "read": "POSTGRES_DISPATCH_3_1" if allowed else "CLOSED", "permitted": allowed,
                "reason": reason, "comparison": jsonable_encoder(comparison)}

    @router.get("/api/sites/{site_code}/performance/dispatch/windows/{day}")
    def window(site_code: str, day: date) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(site_code)
        return {"site_code": code, **served(lambda: reads.window(tenant_id, site_id, day), "No such window.")}

    @router.get("/api/sites/{site_code}/performance/dispatch/runs/{run_id}")
    def run(site_code: str, run_id: UUID) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(site_code)
        return {"site_code": code, **served(lambda: reads.run(tenant_id, site_id, run_id),
                                            "No such analytic run for this Site.")}

    @router.get("/api/sites/{site_code}/performance/dispatch/revisions/{revision_id}")
    def revision(site_code: str, revision_id: UUID) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(site_code)
        return {"site_code": code, **served(lambda: reads.revision(tenant_id, site_id, revision_id),
                                            "No such assessment revision for this Site.")}

    return router
