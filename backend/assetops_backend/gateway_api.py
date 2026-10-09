"""Central gateway diagnostics and Site gateway health (S2-02 phase 2, AC6).

`POST /api/gateways/{gateway_id}/diagnostics` authenticates the registered
gateway bearer credential (the same resolver as Batch V2 upload), then stores
the exact `GatewayDiagnosticsV1` bytes with the server's `received_at`.
`GET /api/sites/{site_id}/gateway-health` reports last server contact, the
registered declared cadence and `CURRENT|STALE|UNKNOWN` from server receive
time. Neither is AcceptedEvidence, asset health or proof of device contact.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from assetops_backend.evidence.gateway_access import (
    DiagnosticIngestionService,
    DiagnosticRefused,
    GatewayAccessStore,
    gateway_health_document,
)
from assetops_backend.evidence.ledger import (
    ClosedGatewayPrincipals,
    GatewayPrincipalResolver,
    LedgerUnavailable,
    PrincipalRefused,
)
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.ports import SiteRepositoryError
from assetops_contracts.gateway_diagnostics import MAX_DIAGNOSTIC_BYTES

GATEWAY_DIAGNOSTICS_ROUTE = "/api/gateways/{gateway_id}/diagnostics"
GATEWAY_HEALTH_ROUTE = "/api/sites/{site_id}/gateway-health"

#: Resolves a product Site code to `(tenant_id, site_id)`, or None when the Site
#: is not an imported Postgres Site. Raises HTTPException for store failures.
SiteScope = Callable[[str], "tuple[UUID, UUID] | None"]


def _unavailable(message: str) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": {"code": "GATEWAY_ACCESS_UNAVAILABLE", "message": message}})


def build_gateway_router(
    principals: GatewayPrincipalResolver | None,
    diagnostics: DiagnosticIngestionService | None,
    health_store: GatewayAccessStore | None,
    site_scope: SiteScope,
    clock: Callable[[], datetime],
) -> APIRouter:
    router = APIRouter()
    resolver = ClosedGatewayPrincipals() if principals is None else principals

    @router.post(GATEWAY_DIAGNOSTICS_ROUTE)
    async def post_diagnostic(gateway_id: str, request: Request):
        try:
            principal = await run_in_threadpool(resolver.resolve, request.headers.get("authorization"))
        except PrincipalRefused as refusal:
            return JSONResponse(
                status_code=refusal.status,
                content={"detail": {"code": refusal.code, "message": refusal.message}},
                headers={"WWW-Authenticate": "Bearer"} if refusal.status == 401 else None)
        except LedgerUnavailable as error:
            return _unavailable(str(error))
        if diagnostics is None:
            return _unavailable("No central gateway diagnostics store is configured.")
        declared = request.headers.get("content-length")
        if declared is not None and declared.isdigit() and int(declared) > MAX_DIAGNOSTIC_BYTES:
            return JSONResponse(status_code=413, content={"detail": {
                "code": "DIAGNOSTIC_REFUSED", "kind": "TOO_LARGE", "field": "diagnostic",
                "message": f"more than {MAX_DIAGNOSTIC_BYTES} bytes"}})
        raw = await request.body()
        try:
            receipt = await run_in_threadpool(diagnostics.submit, principal, gateway_id, raw)
        except DiagnosticRefused as refused:
            return JSONResponse(status_code=refused.status, content={"detail": {
                "code": refused.code, "kind": refused.kind, "field": refused.field, "message": refused.detail,
                "refusal_id": None if refused.refusal_id is None else str(refused.refusal_id)}})
        except LedgerUnavailable as error:
            return _unavailable(str(error))
        return JSONResponse(status_code=receipt.status, content={
            "diagnostic_id": str(receipt.diagnostic_id),
            "received_at": receipt.received_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "received_at_clock": "SERVER_REAL_UTC",
            "payload_sha256": receipt.payload_sha256,
        })

    @router.get(GATEWAY_HEALTH_ROUTE)
    def read_gateway_health(site_id: str) -> dict:
        scope = site_scope(site_id)
        if scope is None:
            raise HTTPException(status_code=404, detail={
                "code": "GATEWAY_HEALTH_UNAVAILABLE",
                "message": f"Site {site_id} has no registered gateway in the product store."})
        if health_store is None:
            raise HTTPException(status_code=503, detail={
                "code": "GATEWAY_ACCESS_UNAVAILABLE", "message": "No gateway access store is configured."})
        tenant_id, site_uuid = scope
        try:
            facts = health_store.gateway_health(tenant_id, site_uuid)
        except LedgerUnavailable as error:
            raise HTTPException(status_code=503, detail={
                "code": "GATEWAY_ACCESS_UNAVAILABLE", "message": str(error)}) from error
        return gateway_health_document(facts, site_uuid, clock())

    return router


def _is_gateway_network_route(request: Request) -> bool:
    path = request.url.path
    if request.method == "POST" and path.startswith("/api/gateways/") and path.endswith("/diagnostics"):
        return True
    # Batch V2 upload is the credentialed POST; legacy V1 without Authorization is unchanged.
    return (path.startswith("/api/ingestion/batches")
            and request.headers.get("authorization") is not None)


_PROXY_SCHEME_HEADERS = ("x-forwarded-proto", "forwarded")


def install_gateway_tls_boundary(app) -> None:
    """Refuse every credentialed gateway request that did not arrive over TLS
    (`D-2026-10-09-s2-pilot-gateway-upload-credential`), before authentication or
    parsing, so no plaintext request is ever authorized. 426, no ledger row."""

    @app.middleware("http")
    async def gateway_tls_required(request: Request, call_next):
        # A proxy header can rewrite the ASGI scheme before this middleware runs
        # (uvicorn trusts loopback `X-Forwarded-Proto` by default), and app code cannot
        # see the pre-rewrite scheme, so a gateway request carrying one is never trusted.
        if _is_gateway_network_route(request) and (
                request.url.scheme != "https" or any(h in request.headers for h in _PROXY_SCHEME_HEADERS)):
            return JSONResponse(status_code=426, headers={"Upgrade": "TLS/1.2"}, content={"detail": {
                "code": "GATEWAY_TLS_REQUIRED",
                "message": "Gateway upload and diagnostics are accepted only over HTTPS."}})
        return await call_next(request)


def registered_site_scope(registry) -> SiteScope:
    """`site_code -> (tenant_id, site_id)` through the imported-Site registry; None
    for a legacy YAML or unknown Site. Store failures are 503."""

    def scope(site_code: str):
        if registry.service is None:
            return None
        try:
            tenant = registry.tenant()
            site = None if tenant is None else registry.service.site(tenant, site_code)
        except (FoundationStoreError, SiteRepositoryError) as error:
            raise HTTPException(status_code=503, detail={
                "code": "FOUNDATION_STORE_UNAVAILABLE", "message": str(error)}) from error
        return None if site is None else (tenant.id, site.id)

    return scope
