"""Analytics read models: declaration, dispatch assessments, Findings, revisions (T028).

Served with the Simulator Lab gate open or closed, beside the evidence routes:
every payload is computed from accepted evidence and the Site's Foundation.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from assetops_backend.analytics.declaration import applicable, site_declaration
from assetops_backend.analytics.ports import AssessmentStoreUnavailable
from assetops_backend.analytics.service import AssessmentService
from assetops_backend.evidence.ports import EvidenceStore, EvidenceStoreUnavailable
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import (
    SiteAwaitingMigration,
    SiteNotFound,
    SiteRepository,
    SiteStoreUnavailable,
)

SITE_ANALYTICS_ROUTE = "/api/sites/{site_id}/analytics"
SITE_DISPATCH_ROUTE = "/api/sites/{site_id}/dispatch"
SITE_FINDINGS_ROUTE = "/api/sites/{site_id}/findings"
SITE_ASSESSMENT_ROUTE = "/api/sites/{site_id}/assessments/{assessment_id}"
SITE_ASSESSMENT_REVISIONS_ROUTE = "/api/sites/{site_id}/assessments/{assessment_id}/revisions"
#: The Findings rail root's global index (T028 AC21): every configured Site's
#: active Findings, each row naming its Site. It is the per-Site read repeated,
#: never a second assessment: rows are the same lineage summaries.
FINDINGS_ROUTE = "/api/findings"


def build_analytics_router(
    service: AssessmentService, evidence: EvidenceStore, sites: SiteRepository
) -> APIRouter:
    router = APIRouter()

    def site_or_404(site_id: str) -> SiteRecord:
        try:
            return sites.get_site(site_id)
        except SiteAwaitingMigration as error:
            raise HTTPException(
                status_code=409,
                detail={"code": SiteAwaitingMigration.code, "message": str(error)},
            ) from error
        except SiteStoreUnavailable as error:
            raise HTTPException(
                status_code=503,
                detail={"code": "SITE_STORE_UNAVAILABLE", "message": str(error)},
            ) from error
        except SiteNotFound as error:
            raise HTTPException(
                status_code=404,
                detail={"code": "SITE_NOT_FOUND", "message": f"No Site {site_id} is configured."},
            ) from error

    def guarded(read):
        try:
            return read()
        except (EvidenceStoreUnavailable, AssessmentStoreUnavailable) as error:
            raise HTTPException(
                status_code=503,
                detail={"code": "ASSESSMENT_UNAVAILABLE", "message": str(error)},
            ) from error

    def found(payload: dict[str, Any] | None, assessment_id: str) -> dict[str, Any]:
        if payload is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "ASSESSMENT_NOT_FOUND",
                        "message": f"No assessment {assessment_id} for this Site."},
            )
        return payload

    @router.get(FINDINGS_ROUTE)
    def get_all_findings() -> dict[str, Any]:
        def read() -> dict[str, Any]:
            rows: list[dict[str, Any]] = []
            for site in sites.list_sites():
                for finding in service.findings(site.site_id)["findings"]:
                    rows.append({
                        **finding,
                        "site_id": site.site_id,
                        "site_display_name": site.display_name,
                        "site_type": site.site_type,
                    })
            rows.sort(key=lambda row: (row["interval"]["first_running_observed"], row["site_id"]))
            return {
                "findings": rows,
                "statement": (
                    "Active Findings across every configured site: periods where the "
                    "generator possibly operated longer than needed, or where that cannot "
                    "be determined. Periods where it was needed have no Finding and are "
                    "listed on each site's Performance > Dispatch."
                ),
            }

        return guarded(read)

    @router.get(SITE_ANALYTICS_ROUTE)
    def get_declaration(site_id: str) -> dict[str, Any]:
        site = site_or_404(site_id)

        def read() -> dict[str, Any]:
            # Readiness (T028 AC20) is scored against the active assessments'
            # coverage: the same lineages Performance > Dispatch lists.
            active = service.dispatch(site_id) if applicable(site.site_type) else None
            assessments = {} if active is None else {
                active["analytic_id"]: [
                    (a["assessment_id"], a["assessment"]) for a in active["assessments"]
                ]
            }
            return site_declaration(site, evidence.load_site(site_id), assessments)

        return guarded(read)

    @router.get(SITE_DISPATCH_ROUTE)
    def get_dispatch(site_id: str) -> dict[str, Any]:
        site_or_404(site_id)
        return guarded(lambda: service.dispatch(site_id))

    @router.get(SITE_FINDINGS_ROUTE)
    def get_findings(site_id: str) -> dict[str, Any]:
        site_or_404(site_id)
        return guarded(lambda: service.findings(site_id))

    @router.get(SITE_ASSESSMENT_ROUTE)
    def get_assessment(site_id: str, assessment_id: str) -> dict[str, Any]:
        site_or_404(site_id)
        return found(guarded(lambda: service.assessment(site_id, assessment_id)), assessment_id)

    @router.get(SITE_ASSESSMENT_REVISIONS_ROUTE)
    def get_revisions(site_id: str, assessment_id: str) -> dict[str, Any]:
        site_or_404(site_id)
        return found(guarded(lambda: service.revisions(site_id, assessment_id)), assessment_id)

    return router
