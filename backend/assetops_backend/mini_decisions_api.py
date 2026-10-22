"""W4-03 unit 2b: the mini-decision routes (`.agent/W4-03-build-spec.md` "API, exact wire, ordering and errors";
closure 1 Q1-Q3/Q12-Q16; closure 2 Q1; closure 4 B2, S10, S15, N8).

- `GET /api/sites/{site_code}/financials/scenarios?from=&to=&known_at=&limit=&cursor=` (`mini-scenarios-1`).
- `POST /api/sites/{site_code}/financials/scenarios` and `POST .../financials/scenarios/{scenario_id}/revisions`.
- Unit 3: `GET /api/sites/{site_code}/findings/{finding_id}/alternatives?revision_id=&known_at=&limit=&cursor=`
  (`mini-alternatives-1`) and `POST .../findings/{finding_id}/alternatives`. Alternatives have no `from`/`to`.
- Unit 5: `GET /api/sites/{site_code}/opportunities?from=&to=&known_at=&limit=&cursor=` (`mini-opportunities-1`),
  `GET .../opportunities/{opportunity_id}?known_at=` (`mini-opportunity-detail-1`) and
  `POST .../opportunities/{opportunity_id}/scenario-links`. The physical opportunity GETs take the Performance gate
  after Site scope and role (S10, u5): a non-MINIGRID Site is the 200 UNKNOWN `SITE_ROLE_UNSUPPORTED` envelope before
  the gate; a closed gate is 409 `PERFORMANCE_CUTOVER_CLOSED`; a gate or store failure is 503.
- Unit 8: `POST /api/sites/{site_code}/work/decision-links` (`mini-decision-link-write-1`) and
  `GET /api/sites/{site_code}/work/decision-contexts?case_ids=&known_at=` (`mini-work-contexts-1`), outside the W4-01
  list cursor; an authored-association read, so no Performance gate.

Order: Site read access 401/403 -> registered Site lookup (scope outage 503, unknown 404) -> Site type -> for a
write, the injected command access 401/403, the store 503, and the injected server principal 403, all before the
body is parsed; for the list, the query is parsed after scope. Authored scenario reads do not take the Performance
gate (S10). The default composition injects a command access that refuses every write and no principal.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from assetops_backend.finding_api import ACCESS_BASIS, Access, development_access
from assetops_backend.mini_decisions.alternatives import AlternativeService
from assetops_backend.mini_decisions.model import MESSAGES, DecisionPrincipal, DecisionRefused
from assetops_backend.mini_decisions.opportunities import (
    SCHEMA_LIST as OPPORTUNITIES_SCHEMA,
    OpportunityService,
    parse_opportunity_list,
    unsupported_detail,
)
from assetops_backend.mini_decisions.scenarios import SCHEMA_LIST, ScenarioService, parse_list
from assetops_backend.mini_decisions.store import MiniDecisionStoreUnavailable
from assetops_backend.mini_decisions.work_links import WorkLinkService
from assetops_backend.mini_depth.read import MINIGRID
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.ports import SiteStoreUnavailable

ROUTE = "/api/sites/{site_code}/financials/scenarios"
ALTERNATIVES_ROUTE = "/api/sites/{site_code}/findings/{finding_id}/alternatives"
OPPORTUNITIES_ROUTE = "/api/sites/{site_code}/opportunities"
WORK_LINKS_ROUTE = "/api/sites/{site_code}/work/decision-links"
WORK_CONTEXTS_ROUTE = "/api/sites/{site_code}/work/decision-contexts"
#: (site_code, tenant_id, site_id) -> (permitted, reason): the S3 Performance cutover gate (S10).
PerformanceGate = Callable[[str, Any, Any], "tuple[bool, str]"]
#: (request, site_code) -> the server-authenticated W4-03 principal, or None (closure 2 Q1).
DecisionPrincipalResolver = Callable[[Request, str], "DecisionPrincipal | None"]


def deny_decision_writes(request: Request, site_code: str) -> int | None:
    """The default W4-03 command access: every write is 403 (closure 2 Q1)."""
    return 403


def no_decision_principal(request: Request, site_code: str) -> DecisionPrincipal | None:
    """Development has no authenticated W4-03 principal."""
    return None


def closed_gate(site_code: str, tenant_id: Any, site_id: Any) -> tuple[bool, str]:
    """The default when no Performance gate is composed: physical opportunity reads stay closed."""
    return False, "No Performance cutover gate is configured."


class _Refusal(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(code)
        self.status, self.code, self.message = status, code, message


def _of(refused: DecisionRefused) -> _Refusal:
    return _Refusal(refused.status, refused.code, refused.message)


def _response(refusal: _Refusal, *, listing: bool) -> HTTPException:
    detail: dict[str, Any] = {"code": refusal.code, "message": refusal.message}
    if listing:
        detail.update(rows=None, total_count=None)
    headers = {"WWW-Authenticate": "Bearer"} if refusal.status == 401 else None
    return HTTPException(status_code=refusal.status, headers=headers, detail=detail)


def build_mini_decisions_router(scenarios: ScenarioService | None, registry: ImportedSiteRegistry,
                                access: Access = development_access,
                                command_access: Access = deny_decision_writes,
                                principal: DecisionPrincipalResolver = no_decision_principal,
                                access_basis: str = ACCESS_BASIS,
                                alternatives: AlternativeService | None = None,
                                opportunities: OpportunityService | None = None,
                                gate: PerformanceGate = closed_gate,
                                gate_unavailable: tuple[type[BaseException], ...] = (),
                                work_links: WorkLinkService | None = None) -> APIRouter:
    router = APIRouter()

    def site_of(request: Request, site_code: str) -> Any:
        refusal = access(request, site_code)
        if refusal == 401:
            raise _Refusal(401, "UNAUTHENTICATED", MESSAGES["UNAUTHENTICATED"])
        if refusal == 403:
            raise _Refusal(403, "SITE_SCOPE_FORBIDDEN", f"No access to Site '{site_code}'.")
        try:
            tenant = registry.tenant()
            site = registry.imported(site_code) if tenant is not None else None
        except (SiteStoreUnavailable, FoundationStoreError) as error:
            raise _Refusal(503, "DECISION_STORE_UNAVAILABLE", MESSAGES["DECISION_STORE_UNAVAILABLE"]) from error
        if tenant is None or site is None:
            raise _Refusal(404, "SITE_NOT_FOUND", f"No imported Site '{site_code}' in this tenant.")
        return tenant, site

    def command(request: Request, site_code: str, service: Any) -> tuple[Any, Any, DecisionPrincipal | None]:
        tenant, site = site_of(request, site_code)
        grant = command_access(request, site_code)
        if grant == 401:
            raise _Refusal(401, "UNAUTHENTICATED", MESSAGES["UNAUTHENTICATED"])
        if grant == 403:
            raise _Refusal(403, "DECISION_WRITE_FORBIDDEN", MESSAGES["DECISION_WRITE_FORBIDDEN"])
        if service is None:
            raise _Refusal(503, "DECISION_STORE_UNAVAILABLE", MESSAGES["DECISION_STORE_UNAVAILABLE"])
        if site.site_type != MINIGRID:
            # PR-4 (provisional, pending ruling): no mini scenario is authored on a non-MINIGRID Site.
            raise _Refusal(422, "DECISION_LINK_SCOPE_INVALID", MESSAGES["DECISION_LINK_SCOPE_INVALID"])
        return tenant, site, principal(request, site_code)

    def physical(site_code: str, tenant: Any, site: Any) -> None:
        """S10: the Performance gate for a physical opportunity read, after Site scope and role."""
        try:
            permitted, reason = gate(site_code, tenant.id, site.id)
        except (SiteStoreUnavailable, FoundationStoreError, MiniDecisionStoreUnavailable,
                *gate_unavailable) as error:
            raise _Refusal(503, "DECISION_STORE_UNAVAILABLE", MESSAGES["DECISION_STORE_UNAVAILABLE"]) from error
        if not permitted:
            raise _Refusal(409, "PERFORMANCE_CUTOVER_CLOSED", reason)

    async def body_of(request: Request) -> Any:
        try:
            return await request.json()
        except ValueError:
            return None  # not JSON: refused 422 by the closed shape, after the write gate

    @router.get(ROUTE)
    def list_scenarios(request: Request, site_code: str) -> dict[str, Any]:
        try:
            tenant, site = site_of(request, site_code)
            if site.site_type != MINIGRID:
                return unsupported_envelope()
            if scenarios is None:
                raise _Refusal(503, "DECISION_STORE_UNAVAILABLE", MESSAGES["DECISION_STORE_UNAVAILABLE"])
            q = request.query_params
            try:
                parsed = parse_list(q.get("from"), q.get("to"), q.get("limit"), q.getlist("known_at"),
                                    q.get("cursor"))
                return scenarios.list(tenant.id, site.id, parsed, access_basis)
            except DecisionRefused as refused:
                raise _of(refused) from refused
        except _Refusal as refusal:
            raise _response(refusal, listing=True) from refusal

    @router.post(ROUTE)
    async def create_scenario(request: Request, site_code: str) -> JSONResponse:
        try:
            tenant, site, admitted = command(request, site_code, scenarios)
            body = await body_of(request)
            try:
                status, out = scenarios.create(tenant.id, site.id, admitted, body)  # type: ignore[union-attr]
            except DecisionRefused as refused:
                raise _of(refused) from refused
        except _Refusal as refusal:
            raise _response(refusal, listing=False) from refusal
        return JSONResponse(status_code=status, content=out)

    @router.post(ROUTE + "/{scenario_id}/revisions")
    async def correct_scenario(request: Request, site_code: str, scenario_id: str) -> JSONResponse:
        try:
            tenant, site, admitted = command(request, site_code, scenarios)
            body = await body_of(request)
            try:
                status, out = scenarios.correct(tenant.id, site.id, admitted, scenario_id,  # type: ignore[union-attr]
                                                body)
            except DecisionRefused as refused:
                raise _of(refused) from refused
        except _Refusal as refusal:
            raise _response(refusal, listing=False) from refusal
        return JSONResponse(status_code=status, content=out)

    @router.get(ALTERNATIVES_ROUTE)
    def list_alternatives(request: Request, site_code: str, finding_id: str) -> dict[str, Any]:
        """N1: a Finding that is not a W1 mini-grid dispatch Finding (any Finding of a non-MINIGRID Site included)
        is 404 `DECISION_NOT_FOUND` after scope, the store check and the query parse."""
        try:
            tenant, site = site_of(request, site_code)
            if alternatives is None:
                raise _Refusal(503, "DECISION_STORE_UNAVAILABLE", MESSAGES["DECISION_STORE_UNAVAILABLE"])
            q = request.query_params
            if site.site_type == MINIGRID and q.get("revision_id") is None:
                # S10, uF 8 (final review M2): a current read (no `revision_id`) takes the Performance gate, as the
                # underlying W1 Finding read does; a pinned exact revision keeps W1's reviewed audit exception.
                physical(site_code, tenant, site)
            try:
                parsed = parse_list(None, None, q.get("limit"), q.getlist("known_at"), q.get("cursor"))
                return alternatives.list(tenant.id, site.id, finding_id, q.get("revision_id"), parsed, access_basis)
            except DecisionRefused as refused:
                raise _of(refused) from refused
        except _Refusal as refusal:
            raise _response(refusal, listing=True) from refusal

    @router.post(ALTERNATIVES_ROUTE)
    async def create_alternative(request: Request, site_code: str, finding_id: str) -> JSONResponse:
        try:
            tenant, site, admitted = command(request, site_code, alternatives)
            body = await body_of(request)
            try:
                status, out = alternatives.create(tenant.id, site.id, admitted,  # type: ignore[union-attr]
                                                  finding_id, body)
            except DecisionRefused as refused:
                raise _of(refused) from refused
        except _Refusal as refusal:
            raise _response(refusal, listing=False) from refusal
        return JSONResponse(status_code=status, content=out)

    @router.get(OPPORTUNITIES_ROUTE)
    def list_opportunities(request: Request, site_code: str) -> dict[str, Any]:
        try:
            tenant, site = site_of(request, site_code)
            if site.site_type != MINIGRID:
                return unsupported_envelope(OPPORTUNITIES_SCHEMA)
            physical(site_code, tenant, site)
            q = request.query_params
            try:
                parsed = parse_opportunity_list(q.get("from"), q.get("to"), q.get("limit"), q.getlist("known_at"),
                                                q.get("cursor"))
                if opportunities is None:
                    raise DecisionRefused("DECISION_STORE_UNAVAILABLE")
                return opportunities.list(tenant.id, site.id, parsed, access_basis)
            except DecisionRefused as refused:
                raise _of(refused) from refused
        except _Refusal as refusal:
            raise _response(refusal, listing=True) from refusal

    @router.get(OPPORTUNITIES_ROUTE + "/{opportunity_id}")
    def opportunity_detail(request: Request, site_code: str, opportunity_id: str) -> dict[str, Any]:
        try:
            tenant, site = site_of(request, site_code)
            if site.site_type != MINIGRID:
                return unsupported_detail()
            physical(site_code, tenant, site)
            if opportunities is None:
                raise _Refusal(503, "DECISION_STORE_UNAVAILABLE", MESSAGES["DECISION_STORE_UNAVAILABLE"])
            try:
                return opportunities.detail(tenant.id, site.id, opportunity_id,
                                            request.query_params.getlist("known_at"))
            except DecisionRefused as refused:
                raise _of(refused) from refused
        except _Refusal as refusal:
            raise _response(refusal, listing=False) from refusal

    @router.post(OPPORTUNITIES_ROUTE + "/{opportunity_id}/scenario-links")
    async def link_opportunity_scenario(request: Request, site_code: str, opportunity_id: str) -> JSONResponse:
        try:
            tenant, site, admitted = command(request, site_code, opportunities)
            body = await body_of(request)
            try:
                status, out = opportunities.link_scenario(  # type: ignore[union-attr]
                    tenant.id, site.id, admitted, opportunity_id, body)
            except DecisionRefused as refused:
                raise _of(refused) from refused
        except _Refusal as refusal:
            raise _response(refusal, listing=False) from refusal
        return JSONResponse(status_code=status, content=out)

    @router.post(WORK_LINKS_ROUTE)
    async def link_work_case(request: Request, site_code: str) -> JSONResponse:
        try:
            tenant, site, admitted = command(request, site_code, work_links)
            body = await body_of(request)
            try:
                status, out = work_links.link(tenant.id, site.id, admitted, body)  # type: ignore[union-attr]
            except DecisionRefused as refused:
                raise _of(refused) from refused
        except _Refusal as refusal:
            raise _response(refusal, listing=False) from refusal
        return JSONResponse(status_code=status, content=out)

    @router.get(WORK_CONTEXTS_ROUTE)
    def work_contexts(request: Request, site_code: str) -> dict[str, Any]:
        try:
            tenant, site = site_of(request, site_code)
            if work_links is None:
                raise _Refusal(503, "DECISION_STORE_UNAVAILABLE", MESSAGES["DECISION_STORE_UNAVAILABLE"])
            q = request.query_params
            try:
                return work_links.contexts(tenant.id, site.id, site.site_code, q.getlist("case_ids"),
                                           q.getlist("known_at"))
            except DecisionRefused as refused:
                raise _of(refused) from refused
        except _Refusal as refusal:
            raise _response(refusal, listing=False) from refusal

    return router


def unsupported_envelope(schema_version: str = SCHEMA_LIST) -> dict[str, Any]:
    """S10 (provisional shape, PR-4): an authorized non-MINIGRID Site's list; no store is consulted."""
    return {"schema_version": schema_version, "window": {"from": None, "to": None, "known_at": None},
            "status": "UNKNOWN", "currentness": {"state": "UNKNOWN", "job_state": "NONE"},
            "source_provenance": {"classification": "UNKNOWN", "state": "UNKNOWN", "source_ids": [],
                                  "evidence_ids": [], "basis_sha256": None,
                                  "reasons": [{"code": "EMPTY_CITATION_SET", "accepted_evidence_ids": []}]},
            "selected_source_provenance": None, "pending_source_provenance": None, "total_count": 0, "rows": [],
            "next_cursor": None, "selection_token": None,
            "limitations": [{"code": "SITE_ROLE_UNSUPPORTED", "evidence_ids": []}]}


__all__ = ["DecisionPrincipalResolver", "PerformanceGate", "build_mini_decisions_router", "closed_gate", "deny_decision_writes",
           "no_decision_principal", "unsupported_envelope"]
