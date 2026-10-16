"""S3-02a selected-assessment capability and claim-limit route (`I-capability-read`, `I-claim-limit-read`).

`GET /api/sites/{site_code}/performance/dispatch/windows/{day}/claim-limit?revision=<assessment_revision_id>&rule=`

Order of checks, so no refusal leaks a ceiling or an empty claim:

1. Request identity with the Finding route seam (`finding_api.Access`): 401 / 403; then the tenant Site scope: 404;
   503 without a product database.
2. Request validation: a malformed `revision` is 422 `INVALID_REVISION_ID`; an unsupported `rule` is 422
   `UNSUPPORTED_RULE_VERSION`.
3. The S3 Performance cutover gate (`performance_api.py` `open_scope`): closed is 409 `PERFORMANCE_CUTOVER_CLOSED`,
   never `UNASSESSED` or an empty success.
4. The read (`ClaimLimitReadService`): 404 foreign/unknown revision, 422 `REVISION_OUTSIDE_WINDOW` /
   `UNSUPPORTED_RULE_VERSION`, 409 `ACCEPTED_LINEAGE_ABSENT`; otherwise 200 with a typed currentness.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.analytics.assessment_ports import AssessmentStoreUnavailable
from assetops_backend.analytics.claim_limit_read import RULE_ID, ClaimLimitReadService, ClaimLimitRefusal
from assetops_backend.analytics.ports import AssessmentStoreUnavailable as FileAssessmentStoreUnavailable
from assetops_backend.evidence.ports import EvidenceStoreUnavailable
from assetops_backend.finding_api import ACCESS_BASIS, Access, Gate, Scope, development_access, no_gate

ROUTE = "/api/sites/{site_code}/performance/dispatch/windows/{day}/claim-limit"


def build_claim_limit_router(reads: ClaimLimitReadService | None, scope: Scope, access: Access = development_access,
                             access_basis: str = ACCESS_BASIS, gate: Gate = no_gate) -> APIRouter:
    router = APIRouter()
    down = (AssessmentStoreUnavailable, FileAssessmentStoreUnavailable, EvidenceStoreUnavailable)

    def unavailable(error: Exception) -> HTTPException:
        return HTTPException(status_code=503, detail={"code": "ASSESSMENT_STORE_UNAVAILABLE", "message": str(error)})

    @router.get(ROUTE)
    def claim_limit(request: Request, site_code: str, day: date, revision: str | None = None,
                    rule: str | None = None) -> dict[str, Any]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read claim limits."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        found = scope(site_code)
        if found is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if reads is None:
            raise HTTPException(status_code=503, detail={"code": "ASSESSMENT_STORE_UNAVAILABLE",
                                                         "message": "No product database is configured."})
        code, tenant_id, site_id = found
        try:
            revision_id = None if revision is None else UUID(revision)
        except ValueError as error:
            raise HTTPException(status_code=422, detail={"code": "INVALID_REVISION_ID",
                                                         "message": f"{revision!r} is not an assessment revision ID."}
                                ) from error
        if rule is not None and rule != RULE_ID:
            raise HTTPException(status_code=422, detail={"code": "UNSUPPORTED_RULE_VERSION",
                                                         "message": f"Rule {rule!r} is not supported; this read "
                                                                    f"serves {RULE_ID} only."})
        try:
            permitted, reason = gate(code, tenant_id, site_id)
        except down as error:
            raise unavailable(error) from error
        if not permitted:
            raise HTTPException(status_code=409, detail={
                "code": "PERFORMANCE_CUTOVER_CLOSED", "read": "CLOSED", "message": reason,
                "capability": None, "claim_limit": None})
        try:
            body = reads.read(UUID(str(tenant_id)), UUID(str(site_id)), day, revision_id, rule)
        except ClaimLimitRefusal as error:
            raise HTTPException(status_code=error.status, detail=error.detail) from error
        except down as error:
            raise unavailable(error) from error
        return jsonable_encoder({"site_code": code, **body, "access_basis": access_basis,
                                 "source_gate": {"permitted": True, "reason": reason}})

    return router
