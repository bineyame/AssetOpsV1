"""W3-02 estate Evidence root (`I-estate-evidence-root`): read-only, no Site parameter.

`GET /api/estate/evidence?from=&to=&known_at=&limit=&cursor=`. Same order of checks as W3-01 `estate_api.py`:
authentication (401 with `WWW-Authenticate: Bearer`) before any tenant lookup or parsing, then the strict shared
parser, then one read-only snapshot with per-Site admission through the existing `access` seam. Every refusal is
W3-01's `{code,message,rows:null,total_count:null}` body inside `detail`, plus the endpoint's null extras
(`gaps:null` for Evidence), including 401 and 503 (closure 4 B1). W3-01 refusal bodies are unchanged.
Lane A mounts this router in `main.py`.
"""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.estate.scope import EstateRefusal, EstateStoreUnavailable, MESSAGES, parse_request
from assetops_backend.estate_api import Authenticate, development_authenticate
from assetops_backend.finding_api import Access, development_access

#: The endpoint-specific null fields inside every refusal `detail` (closure 1 "Estate wire").
EXTRAS = {"evidence": {"gaps": None}}


def build_estate_evidence_money_router(service: Any | None, tenant: Callable[[], UUID | None], *,
                                       authenticate: Authenticate = development_authenticate,
                                       access: Access = development_access,
                                       unavailable: tuple[type[BaseException], ...] = ()) -> APIRouter:
    router = APIRouter()
    down = (EstateStoreUnavailable, *unavailable)

    def refusal(code: str, kind: str) -> dict[str, Any]:
        return {"code": code, "message": MESSAGES[code], "rows": None, "total_count": None, **EXTRAS[kind]}

    def serve(kind: str, request: Request) -> dict[str, Any]:
        if authenticate(request) == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail=refusal("UNAUTHENTICATED", kind))
        try:
            parsed = parse_request(kind, request.query_params.multi_items())
            if service is None:
                raise EstateStoreUnavailable("No product database is configured.")
            body = getattr(service, kind)(tenant(), parsed, lambda code: access(request, code) is None)
        except EstateRefusal as error:
            headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else None
            raise HTTPException(status_code=error.status, detail=refusal(error.code, kind),
                                headers=headers) from error
        except down as error:
            raise HTTPException(status_code=503, detail=refusal("ESTATE_STORE_UNAVAILABLE", kind)) from error
        return jsonable_encoder(body)

    @router.get("/api/estate/evidence")
    def estate_evidence(request: Request) -> dict[str, Any]:
        return serve("evidence", request)

    return router
