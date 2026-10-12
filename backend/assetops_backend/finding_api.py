"""Site-scoped exact Finding read (S4-01 phase 2) at the `A-claim-work-routes` API routes.

`D-2026-10-09-pre-s3-claim-routes-and-actor`: the Site code resolves inside the configured tenant; an
unauthenticated caller is 401 and an authenticated caller without the known Site scope is 403 (the `access`
seam decides both); a foreign or unknown Site, Finding or revision is 404; an unavailable store is a typed
503, never an empty claim. No human sign-in exists yet: the default composition admits the development
tenant's operator context exactly as the S3 Performance read does, and says so in every body.

Q19 (`D-2026-10-12-s4-finding-phase-2-read-boundaries`): the S3 Performance cutover gate (comparison,
lineage breaks, other-model heads) guards both routes. While it is closed a default/current read is a typed
409 `PERFORMANCE_CUTOVER_CLOSED`, never a positive Finding or `NO_FINDING`; a pinned `revision_id` is served
as non-current audit material (`SOURCE_CLOSED`), and S3 drill-down links are withheld with the reason.
An unconfigured gate is closed.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.analytics.assessment_ports import AssessmentStoreUnavailable
from assetops_backend.analytics.finding_read import FindingReadService
from assetops_backend.analytics.ports import AssessmentStoreUnavailable as FileAssessmentStoreUnavailable
from assetops_backend.evidence.ports import EvidenceStoreUnavailable

Scope = Callable[[str], "tuple[str, UUID, UUID] | None"]
# (request, site_code) -> None to admit, else 401 or 403.
Access = Callable[[Request, str], "int | None"]
ACCESS_BASIS = ("DEVELOPMENT_TENANT_OPERATOR_CONTEXT: no authenticated human principal exists yet; the read is "
                "admitted for the configured development tenant, as the S3 Performance read is")


Gate = Callable[[str, UUID, UUID], "tuple[bool, str]"]
CLOSED_LINKS = "S3 Performance drill-down routes answer 409 PERFORMANCE_CUTOVER_CLOSED while the gate is closed"


def development_access(request: Request, site_code: str) -> int | None:
    return None


def no_gate(site_code: str, tenant_id: UUID, site_id: UUID) -> tuple[bool, str]:
    return False, "No Performance cutover gate is configured for the Finding read."


def build_finding_router(reads: FindingReadService | None, scope: Scope, unavailable: tuple[type, ...] = (),
                         access: Access = development_access, access_basis: str = ACCESS_BASIS,
                         gate: Gate = no_gate) -> APIRouter:
    router = APIRouter()
    down = (AssessmentStoreUnavailable, FileAssessmentStoreUnavailable, EvidenceStoreUnavailable, *unavailable)

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

    def source_gate(code: str, tenant_id: UUID, site_id: UUID) -> dict[str, Any]:
        try:
            permitted, reason = gate(code, tenant_id, site_id)
        except down as error:
            raise HTTPException(status_code=503, detail={"code": "FINDING_STORE_UNAVAILABLE",
                                                         "message": str(error)}) from error
        return {"permitted": permitted, "reason": reason}

    def closed(source: dict[str, Any]) -> HTTPException:
        return HTTPException(status_code=409, detail={
            "code": "PERFORMANCE_CUTOVER_CLOSED", "read": "CLOSED", "message": source["reason"],
            "note": "The Finding's authority is the selected S3 assessment, which is closed for this Site; no "
                    "current Finding or no-Finding verdict is shown. An exact revision_id reads audit material."})

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
        source = source_gate(code, tenant_id, site_id)
        if not source["permitted"]:
            raise closed(source)
        return {"site_code": code, "access_basis": access_basis, "source_gate": source,
                **served(lambda: reads.window_state(tenant_id, site_id, day), "No such window.")}

    @router.get("/api/sites/{site_code}/findings/{finding_id}")
    def finding(request: Request, site_code: str, finding_id: UUID, revision_id: UUID | None = None,
                after_revision_no: int = Query(0, ge=0), limit: int = Query(200, ge=1, le=500)) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        source = source_gate(code, tenant_id, site_id)
        if not source["permitted"] and revision_id is None:
            raise closed(source)
        body = served(lambda: reads.finding(tenant_id, site_id, finding_id, revision_id,
                                            after_revision_no=after_revision_no, limit=limit,
                                            source_open=source["permitted"]),
                      "No such Finding or revision for this Site.")
        performance = {"status": "OPEN" if source["permitted"] else "CLOSED", "reason": source["reason"]}
        if not source["permitted"]:
            performance["note"] = CLOSED_LINKS
        selected = body["selection"]["revision_id"]
        base = f"/sites/{code}/findings/{finding_id}"
        audit = None if source["permitted"] else {
            "non_current": True, "reason": source["reason"],
            "statement": "Audit material only: the selected S3 source is closed, so this recorded revision is not "
                         "a current claim and its currentness is not read."}
        return {"site_code": code, "access_basis": access_basis, "source_gate": source, "audit_only": audit,
                **body, "links": {
            "canonical": base, "selected_revision": f"{base}?revision_id={selected}",
            "api_selected_revision": f"/api{base}?revision_id={selected}",
            "canonical_finding": f"/sites/{code}/findings/{body['relations']['canonical_finding_id']}",
            "performance": performance,
            "assessment_revisions": {} if not source["permitted"] else {
                str(a["assessment_revision_id"]):
                f"/api/sites/{code}/performance/dispatch/revisions/{a['assessment_revision_id']}"
                for a in body["revision"]["assessments"]},
            "windows": {} if not source["permitted"] else {
                w["day"]: f"/api/sites/{code}/performance/dispatch/windows/{w['day']}"
                for w in body["revision"]["currentness"]["windows"]}}}

    return router
