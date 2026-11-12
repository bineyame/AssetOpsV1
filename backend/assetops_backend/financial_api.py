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

PR-3 (D-PRICE.1) adds `POST /api/sites/{site_code}/financial-assumptions/entries`: a price typed on the Site price
page, published by the dip form's server-configured entry service (`service:operator-entry`, channel
`SITE_ADMIN_ENTRY`, "Entered by site admin") behind the same `ASSETOPS_OPERATIONAL_ENTRY` switch. Its refusal order
is on the route; the human route above is unchanged.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from assetops_backend.finding_api import development_access
from assetops_backend.financials import price_entry as pe
from assetops_backend.financials.assumptions import (
    SITE_ADMIN_CHANNEL, SITE_ADMIN_PRICE_PUBLISHER, Publication, PublicationRefused, unit_for)
from assetops_backend.work_api import Principal, no_service_principal

Scope = Callable[[str], "tuple[str, UUID, UUID] | None"]
# (request, site_code) -> None to admit, else 401, 403 or 404.
Access = Callable[[Request, str], "int | None"]
# (tenant_id, site_id) -> the Site's time zone (PR-3: the lookup `entry_site_context` uses).
SiteZone = Callable[[UUID, UUID], ZoneInfo]
_NOT_JSON = object()

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


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _refuse(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def build_financial_assumption_router(scope: Scope, access: Access = no_verified_principal, *,
                                      entry_principal: Principal = no_service_principal,
                                      store: Any | None = None,
                                      site_zone: SiteZone | None = None,
                                      read_access: Access = development_access,
                                      unavailable: tuple[type, ...] = (),
                                      clock: Callable[[], datetime] = _now) -> APIRouter:
    """The human write route (always refused) and PR-3's site-admin entry route (D-PRICE.1).

    `entry_principal` is the injected `operational_entry_principal` (`ASSETOPS_OPERATIONAL_ENTRY=on`, the dip form's
    one switch); `store` the assumption store (`snapshot`, `publish`) or None; `site_zone` the Site's time zone;
    `read_access` the price read's access; `unavailable` the store failures served as 503."""
    router = APIRouter()

    def store_down(message: str) -> HTTPException:
        return _refuse(503, "ASSUMPTION_STORE_UNAVAILABLE", message)

    @router.post("/api/sites/{site_code}/financial-assumptions/entries")
    async def enter_price(request: Request, site_code: str) -> JSONResponse:
        """PR-3 refusal order (revision 5 §5.3, fixed and tested): 404 Site, 403 read access, 403 entry off, 422 body
        not JSON, 422 client actor, 422 shape, 422 future key, 503 store, then the derivation's 422s and the store's own
        refusals unchanged. Nothing is written on any refusal; a dry run never publishes."""
        found = scope(site_code)
        if found is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        code, tenant_id, site_id = found
        refusal = read_access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read Site prices."})
        if refusal == 403:
            raise _refuse(403, "SITE_SCOPE_FORBIDDEN", f"No access to Site {site_code!r}.")
        if refusal == 404:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if entry_principal(request, site_code) is None:
            raise _refuse(403, "PRICE_ENTRY_OFF", pe.MESSAGES["PRICE_ENTRY_OFF"])
        raw = await request.body()
        try:
            body = json.loads(raw) if raw else _NOT_JSON
        except ValueError:
            body = _NOT_JSON
        if body is _NOT_JSON:
            raise _refuse(422, "BODY_NOT_JSON", "The request body is not JSON.")
        named = _client_actor_fields(body)
        if named:
            raise HTTPException(status_code=422, detail={
                "code": "CLIENT_ACTOR_FORBIDDEN", "fields": named,
                "message": "Prices typed here are recorded by the server's entry service; a request cannot name "
                           "an actor or author."})
        try:
            entry = pe.validate_entry(body)
        except pe.EntryRefused as refused:
            raise HTTPException(status_code=422, detail=refused.detail()) from None
        if store is None or site_zone is None:
            raise store_down("No product database is configured.")
        now = clock()
        try:
            zone = site_zone(tenant_id, site_id)
            snapshot = store.snapshot(tenant_id, site_id, entry.key, None, 0, 1)
        except unavailable as error:
            raise store_down(str(error)) from error
        try:
            derived = pe.derive(entry, zone, now, snapshot, require_reason=not entry.dry_run)
            pe.plan(derived, now)
        except pe.EntryRefused as refused:
            raise HTTPException(status_code=422, detail=refused.detail()) from None
        except PublicationRefused as refused:
            raise _refuse(refused.status, refused.code, refused.message) from None
        unit = unit_for(entry.key)
        applies = entry.applies_from.isoformat()
        if entry.dry_run:
            return JSONResponse(status_code=200, content={
                "dry_run": True, "change_kind": derived.change_kind, "applies_from": applies,
                "reason_required": derived.reason_required,
                "summary": pe.dry_run_summary(entry, derived.change_kind, unit, code)})
        correction_reason, provenance = pe.correction_and_provenance(entry, derived.change_kind)
        publication = Publication(
            assumption_key=entry.key, currency=entry.currency, value=entry.value, basis=entry.basis,
            source_reference=entry.source, valid_from=derived.valid_from, valid_to=None,
            change_kind=derived.change_kind, correction_reason=correction_reason,
            expected_prior_revision_id=derived.expected_prior_revision_id, idempotency_key=entry.idempotency_key,
            channel=SITE_ADMIN_CHANNEL, provenance=provenance)
        try:
            published = store.publish(tenant_id, site_id, publication, SITE_ADMIN_PRICE_PUBLISHER)
        except PublicationRefused as refused:
            raise _refuse(refused.status, refused.code, refused.message) from None
        except unavailable as error:
            raise store_down(str(error)) from error
        return JSONResponse(status_code=200 if published.replayed else 201, content={
            "revision_id": str(published.revision_id), "revision_no": published.revision_no,
            "change_kind": published.change_kind, "applies_from": applies,
            "recorded_at": published.recorded_at.isoformat(), "replayed": published.replayed,
            "set_by": pe.SET_BY, "summary": pe.saved_summary(entry, unit, code)})

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
