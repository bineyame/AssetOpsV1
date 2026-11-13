"""Analytics read models: declaration, dispatch assessments, Findings, revisions (T028).

Served with the Simulator Lab gate open or closed, beside the evidence routes:
every payload is computed from accepted evidence and the Site's Foundation.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.analytics.declaration import applicable, site_declaration
from assetops_backend.analytics.ports import AssessmentStoreUnavailable
from assetops_backend.analytics.service import AssessmentService
from assetops_backend.analytics.stored_declaration import StoredSiteNotFound, UnsupportedModel
from assetops_backend.evidence.ports import EvidenceStore, EvidenceStoreUnavailable
from assetops_backend.i18n import message, render
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

_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _window(request: Request) -> tuple[datetime, datetime] | None:
    """SR-12b: optional `from`/`to` (UTC instants, both or neither, `from` before `to`); else 422 INVALID_WINDOW,
    the evidence routes' code (`evidence_api._window_params`)."""
    raw = (request.query_params.get("from"), request.query_params.get("to"))
    if raw == (None, None):
        return None
    if None in raw or not all(_INSTANT.fullmatch(v) for v in raw):
        raise HTTPException(status_code=422, detail={
            "code": "INVALID_WINDOW", "message": "Give both 'from' and 'to' as UTC instants (YYYY-MM-DDTHH:MM:SSZ)."})
    lo, hi = (datetime.fromisoformat(v.replace("Z", "+00:00")) for v in raw)
    if lo >= hi:
        raise HTTPException(status_code=422, detail={
            "code": "INVALID_WINDOW", "message": "from must be before to (half-open [from, to))"})
    return lo, hi


#: AP-1: `(site_code, tenant_id, site_id)` of a stored Site, else None (`ImportedSiteRegistry.ledger_scope`).
Scope = Callable[[str], "tuple[str, UUID, UUID] | None"]
#: AP-1: the Performance cutover gate (`main.performance_gate`): `(permitted, reason)`.
Gate = Callable[[str, UUID, UUID], "tuple[bool, str]"]
#: AP-1: the stored readiness read `(tenant_id, site_id, site_code, window, gate) -> body`
#: (`stored_declaration.stored_site_declaration` over the assessment store).
StoredRead = Callable[..., dict[str, Any]]


class _GateClosed(Exception):
    pass


def build_analytics_router(
    service: AssessmentService, evidence: EvidenceStore, sites: SiteRepository, *,
    scope: Scope | None = None, stored: StoredRead | None = None, gate: Gate | None = None,
    unavailable: tuple[type[BaseException], ...] = (),
) -> APIRouter:
    """`scope`/`stored`/`gate` (AP-1, D-SR.75): `/analytics` for a stored Site reads the stored declaration behind
    the Performance cutover gate; legacy Sites and every sibling route keep the file-backed, `LegacySiteGate` path.
    `unavailable`: further store errors the stored branch answers 503."""
    router = APIRouter()
    down = (EvidenceStoreUnavailable, AssessmentStoreUnavailable, SiteStoreUnavailable, *unavailable)

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
                detail={"code": "SITE_NOT_FOUND",
                        "message": render(message("analytics.site_not_found", site_id=site_id))},
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

    def stored_declaration(found: tuple[str, UUID, UUID], window) -> dict[str, Any]:
        code, tenant_id, site_id = found
        if stored is None:
            raise HTTPException(status_code=503, detail={
                "code": "ASSESSMENT_UNAVAILABLE", "message": "No product database is configured."})

        def check_gate() -> None:
            permitted, reason = (True, "") if gate is None else gate(code, tenant_id, site_id)
            if not permitted:
                raise _GateClosed(reason)

        try:
            return jsonable_encoder(stored(tenant_id, site_id, code, window, gate=check_gate))
        except _GateClosed as closed:
            # The existing refusal (SR-12b shows it as "not available yet"); never a partial readiness row.
            raise HTTPException(status_code=409, detail={
                "code": SiteAwaitingMigration.code, "message": str(closed)}) from closed
        except UnsupportedModel as error:
            raise HTTPException(status_code=422, detail={
                "code": "UNSUPPORTED_RULE_VERSION", "message": str(error)}) from error
        except StoredSiteNotFound as error:
            raise HTTPException(status_code=404, detail={
                "code": "SITE_NOT_FOUND", "message": render(message("analytics.site_not_found", site_id=code))
            }) from error
        except down as error:
            raise HTTPException(status_code=503, detail={
                "code": "ASSESSMENT_UNAVAILABLE", "message": str(error)}) from error

    @router.get(SITE_ANALYTICS_ROUTE)
    def get_declaration(site_id: str, request: Request) -> dict[str, Any]:
        window = _window(request)
        if scope is not None:
            try:
                found = scope(site_id)
            except SiteStoreUnavailable as error:
                raise HTTPException(status_code=503, detail={
                    "code": "SITE_STORE_UNAVAILABLE", "message": str(error)}) from error
            if found is not None:
                return stored_declaration(found, window)
        site = site_or_404(site_id)

        def read() -> dict[str, Any]:
            # Readiness (T028 AC20) is scored against the active assessments'
            # coverage: the same lineages Performance > Dispatch lists. SR-12b:
            # with `from`/`to`, only those meeting `[from, to)`.
            active = service.dispatch(site_id) if applicable(site.site_type) else None
            assessments = {} if active is None else {
                active["analytic_id"]: [
                    (a["assessment_id"], a["assessment"]) for a in active["assessments"]
                ]
            }
            return site_declaration(site, evidence.load_site(site_id), assessments, window)

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
