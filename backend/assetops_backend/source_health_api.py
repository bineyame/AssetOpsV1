"""S7-01a Site source-health route (`I-source-health-read`, `D-2026-10-16-a-s7-health`).

`GET /api/sites/{site_code}/source-health` - the versioned two-clock DTO of
`evidence/source_health.py`. The S2 `gateway-health` route and contract are unchanged.

Order of checks, so no refusal leaks a gateway, count or current claim:

1. Request identity with the Finding route seam (`finding_api.Access`): 401 / 403; then the tenant
   Site scope: 404 (a foreign or unknown Site is never an empty healthy list).
2. 503 `SOURCE_HEALTH_UNAVAILABLE` without a store or when the central store cannot be read.
3. 409 `SOURCE_HEALTH_SELECTION_INCONSISTENT` when registration and diagnostic selection disagree.
4. 200 with the DTO; an enabled-gateway-free Site is `NO_REGISTERED_SOURCE`, a registered gateway
   never received is `UNKNOWN` contact.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from assetops_backend.evidence.ledger import LedgerUnavailable
from assetops_backend.evidence.source_health import (
    SelectionInconsistent,
    SourceHealthStore,
    source_health_document,
)
from assetops_backend.finding_api import ACCESS_BASIS, Access, Scope, development_access

ROUTE = "/api/sites/{site_code}/source-health"


def build_source_health_router(store: SourceHealthStore | None, scope: Scope, clock: Callable[[], datetime],
                               access: Access = development_access, access_basis: str = ACCESS_BASIS
                               ) -> APIRouter:
    router = APIRouter()

    @router.get(ROUTE)
    def source_health(request: Request, site_code: str) -> dict[str, Any]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read Site health."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        try:
            found = scope(site_code)
        except Exception as error:  # noqa: BLE001 - the Site store could not be asked: no claim
            raise HTTPException(status_code=503, detail={"code": "SOURCE_HEALTH_UNAVAILABLE",
                                                         "message": str(error), "gateways": None}) from error
        if found is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if store is None:
            raise HTTPException(status_code=503, detail={"code": "SOURCE_HEALTH_UNAVAILABLE",
                                                         "message": "No central gateway store is configured.",
                                                         "gateways": None})
        code, tenant_id, site_id = found
        try:
            snapshot = store.source_health_snapshot(UUID(str(tenant_id)), UUID(str(site_id)))
            return source_health_document(snapshot, code, clock(), access_basis)
        except LedgerUnavailable as error:
            raise HTTPException(status_code=503, detail={"code": "SOURCE_HEALTH_UNAVAILABLE",
                                                         "message": str(error), "gateways": None}) from error
        except SelectionInconsistent as error:
            raise HTTPException(status_code=409, detail={
                "code": "SOURCE_HEALTH_SELECTION_INCONSISTENT", "message": error.reason, "gateways": None,
                "note": "Registration and diagnostic selection disagree; no current contact or fact claim is made."
            }) from error

    return router
