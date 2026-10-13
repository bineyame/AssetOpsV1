"""Site financial assumption routes (S4-02a).

Phase 1 builds only the human write route, and it has no success path
(packet item 2, plan review C7): no verified human principal exists yet, so a
human cannot publish a price. Refusal order, fixed and tested:

1. 401 `UNAUTHENTICATED` - the access seam's default (`no_verified_principal`)
   refuses every request: there is no sign-in.
2. 422 `CLIENT_ACTOR_FORBIDDEN` - any body field naming an actor or author. The
   server derives actor and author from a verified principal, never the body.
3. 403 / 404 - from the injected access seam (Site scope), or 404 for a Site the
   tenant scope does not know.
4. An admitted request still has no verified human principal: 401
   `HUMAN_PRINCIPAL_REQUIRED`. Nothing is ever written here.

This router deliberately does not use `finding_api.development_access`, which
admits every read: a write must never be admitted by the development context.
Publication happens only through the server-side SYSTEM publisher
(`assetops_backend/publish_assumption.py`). Phase 2 adds the Site-scoped reads.
"""

from __future__ import annotations

import json
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

Scope = Callable[[str], "tuple[str, UUID, UUID] | None"]
# (request, site_code) -> None to admit, else 401, 403 or 404.
Access = Callable[[Request, str], "int | None"]

_CLIENT_ACTOR_MARKERS = ("actor", "author", "principal")


def no_verified_principal(request: Request, site_code: str) -> int | None:
    """The default access for writes: nobody is signed in, so every request is unauthenticated."""
    return 401


def _client_actor_fields(body: Any, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(body, dict):
        for key, value in body.items():
            name = f"{path}{key}"
            if any(marker in str(key).lower() for marker in _CLIENT_ACTOR_MARKERS):
                found.append(name)
            found += _client_actor_fields(value, f"{name}.")
    elif isinstance(body, list):
        for i, value in enumerate(body):
            found += _client_actor_fields(value, f"{path}{i}.")
    return found


def build_financial_assumption_router(scope: Scope, access: Access = no_verified_principal) -> APIRouter:
    router = APIRouter()

    @router.post("/api/sites/{site_code}/financial-assumptions")
    async def publish_assumption(request: Request, site_code: str) -> dict[str, Any]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"}, detail={
                "code": "UNAUTHENTICATED",
                "message": "Sign in to edit Site prices. Interactive price editing awaits an authenticated operator."})
        raw = await request.body()
        try:
            body = json.loads(raw) if raw else {}
        except ValueError:
            raise HTTPException(status_code=422, detail={"code": "BODY_NOT_JSON",
                                                         "message": "The request body is not JSON."}) from None
        named = _client_actor_fields(body)
        if named:
            raise HTTPException(status_code=422, detail={
                "code": "CLIENT_ACTOR_FORBIDDEN", "fields": named,
                "message": "Actor and author are derived on the server from a verified principal; a request "
                           "cannot assert them."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        if refusal == 404 or scope(site_code) is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        # Admitted, but there is still no verified human principal to author the price: never a success.
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"}, detail={
            "code": "HUMAN_PRINCIPAL_REQUIRED",
            "message": "No verified human principal exists, so a human cannot publish a Site price yet. Prices "
                       "are published by the server-side SYSTEM publisher."})

    return router
