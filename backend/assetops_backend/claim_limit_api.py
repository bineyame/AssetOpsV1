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

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder

from assetops_backend import perf
from assetops_backend.chain.response_store import ResponseStore, StoredRoute, finish
from assetops_backend.estate.claim_limit_range import ClaimLimitRangeNotApplicable, claim_limit_range_body
from assetops_backend.estate.scope import EstateRefusal, EstateStoreUnavailable, estate_request
from assetops_backend.outcome_api import _instant as _utc_instant, _refuse as _refused, board_site
from assetops_backend.outcomes.catalogue import MINI
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.ports import SiteStoreUnavailable

from assetops_backend.analytics.assessment_ports import AssessmentStoreUnavailable
from assetops_backend.analytics.claim_limit_read import RULE_ID, ClaimLimitReadService, ClaimLimitRefusal
from assetops_backend.analytics.ports import AssessmentStoreUnavailable as FileAssessmentStoreUnavailable
from assetops_backend.evidence.ports import EvidenceStoreUnavailable
from assetops_backend.finding_api import ACCESS_BASIS, Access, Gate, Scope, development_access, no_gate

ROUTE = "/api/sites/{site_code}/performance/dispatch/windows/{day}/claim-limit"
RANGE_ROUTE = "/api/sites/{site_code}/claim-limit-range"


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


def build_claim_limit_range_router(estate: Any, registry: ImportedSiteRegistry, access: Access = development_access,
                                   gate: Gate = no_gate, unavailable: tuple[type[BaseException], ...] = (),
                                   responses: ResponseStore | None = None) -> APIRouter:
    """SR-7b (rev 10 §10.3, D-SR.23/24/25): `GET /api/sites/{site_code}/claim-limit-range?from&to[&known_at]`, schema
    `site-claim-limit-range-1`. Admission and Site lookup as the board (`outcome_api.board_site`); a cold or EV Site
    is 404 `CLAIM_LIMIT_RANGE_NOT_APPLICABLE`; the window is the estate's (422 INVALID_WINDOW); the one-day route's
    Performance cutover gate (409 `PERFORMANCE_CUTOVER_CLOSED`, so no refusal leaks a ceiling); no estate service or a
    store outage is 503 `SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE`. `estate` is the `EstatePortfolioService` (its
    `read_snapshot` yields the `EvidenceMoneySnapshot`). Stored route keyed `{site, from, to, known_at}`."""
    router = APIRouter()
    down = (AssessmentStoreUnavailable, FileAssessmentStoreUnavailable, EvidenceStoreUnavailable,
            EstateStoreUnavailable, SiteStoreUnavailable, *unavailable)

    def not_applicable(site_code: str) -> HTTPException:
        return _refused(404, "CLAIM_LIMIT_RANGE_NOT_APPLICABLE",
                        f"Site {site_code!r} has no mini-grid dispatch claim limit.")

    @router.get(RANGE_ROUTE)
    def claim_limit_range(site_code: str, request: Request, response: Response) -> Any:
        with perf.route(RANGE_ROUTE, response):  # QW-1: one `assetops.perf` line per request
            out = _range(site_code, request)
        return finish(out, response) if isinstance(out, Response) else out

    def _range(site_code: str, request: Request) -> Any:
        ref = board_site(access, registry, site_code, "Site claim-limit range", request)
        if ref.domain != MINI:
            raise not_applicable(site_code)
        params = request.query_params
        lo, hi = _utc_instant(params, "from"), _utc_instant(params, "to")
        known_at = _utc_instant(params, "known_at")
        if lo is None or hi is None:
            raise _refused(422, "INVALID_WINDOW", "Give both 'from' and 'to' (UTC midnights, at most 31 days).")
        try:
            req = estate_request("evidence", lo, hi, known_at)
        except EstateRefusal as error:
            raise _refused(error.status, error.code, error.detail["message"]) from error
        if estate is None:
            raise _refused(503, "SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE", "No product database is configured.")
        try:
            permitted, reason = gate(ref.site_code, ref.tenant_id, ref.site_id)
        except down as error:
            raise _refused(503, "SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE", str(error)) from error
        if not permitted:
            raise HTTPException(status_code=409, detail={
                "code": "PERFORMANCE_CUTOVER_CLOSED", "read": "CLOSED", "message": reason,
                "capability": None, "claim_limit": None})

        def compose() -> dict[str, Any]:
            try:
                body = claim_limit_range_body(estate, ref.tenant_id, ref.site_code, req, ref.timezone)
            except ClaimLimitRangeNotApplicable as error:
                raise not_applicable(site_code) from error
            except down as error:
                raise _refused(503, "SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE", str(error)) from error
            except EstateRefusal as error:
                status = 503 if error.status == 503 else error.status
                code = "SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE" if status == 503 else error.code
                raise _refused(status, code, error.detail["message"]) from error
            if body is None:
                raise _refused(404, "SITE_NOT_FOUND", f"No imported Site {site_code!r} with a claim limit range.")
            return {RANGE_ROUTE: jsonable_encoder(body)}

        if responses is None:
            return compose()[RANGE_ROUTE]
        site = UUID(str(ref.site_id))
        key = {"site": ref.site_id, "from": lo, "to": hi, "known_at": known_at}
        return responses.serve(StoredRoute(RANGE_ROUTE, ref.tenant_id, key, sites=(site,),
                                           watermark_sites=(site,)), compose)

    return router
