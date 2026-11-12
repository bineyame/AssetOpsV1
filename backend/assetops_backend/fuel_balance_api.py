"""DIESEL-K5 (`.agent/build-sheet-DIESEL-1.md` §9l.2, ruling DIESEL-1-R3l): the fuel-balance night and fuel Finding
reads.

- `GET /api/sites/{site_code}/fuel-balance/nights?from=&to=&known_at=` has two forms (D-SR.55), told apart by a `T`
  in either value: night dates `[from, to)`, at most 31 nights (K5, `FUEL_BALANCE_RANGE_INVALID`), or SR-10k the date
  range's UTC instants, listing the nights of its Site-local days (`INVALID_WINDOW`). Mixing the two is refused with
  422 `INVALID_WINDOW`.
- `GET /api/sites/{site_code}/fuel-balance/nights/{night_date}?known_at=`
- `GET /api/sites/{site_code}/fuel-findings?from=&to=&known_at=` (UTC instants)
- `GET /api/sites/{site_code}/fuel-findings/{finding_id}?revision_id=&known_at=`

Scope, Site resolution and refusals copy `finding_api.py`: the `access` seam answers 401/403, a Site outside the
configured tenant is 404, no database is a typed 503. Every visible string is server-composed.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from assetops_backend.finding_api import Access, Scope, development_access
from assetops_backend.mini_depth.read import MESSAGES
from assetops_backend.fuel_balance.night_read import (
    MAX_NIGHTS, FuelNightRead, FuelNightRefused, FuelNightUnavailable)

RANGE_INVALID = ("FUEL_BALANCE_RANGE_INVALID", "Choose up to 31 nights, with the first night before the last.")
NIGHT_NOT_FOUND = ("FUEL_BALANCE_NIGHT_NOT_FOUND", "No fuel check is stored for this night.")
FINDING_NOT_FOUND = ("FUEL_FINDING_NOT_FOUND", "No such fuel finding for this Site.")
#: Existing messages reused (no new wording): the mini-depth read's knowledge-time and unavailable sentences; the
#: fuel-findings window refusal reuses the nights range refusal.
KNOWN_AT_INVALID = ("INVALID_KNOWN_AT", MESSAGES["INVALID_KNOWN_AT"])
WINDOW_INVALID = RANGE_INVALID
#: SR-10k: the date-range form of the nights list (UTC instants) refuses with the range code `INVALID_WINDOW` and the
#: nights range sentence (no new wording).
RANGE_WINDOW_INVALID = ("INVALID_WINDOW", RANGE_INVALID[1])
UNAVAILABLE = ("FUEL_BALANCE_STORE_UNAVAILABLE", MESSAGES["MINI_DEPTH_STORE_UNAVAILABLE"])


def _refuse(status: int, pair: tuple[str, str]) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": pair[0], "message": pair[1]})


def _one(request: Request, key: str) -> str | None:
    values = request.query_params.getlist(key)
    if len(values) > 1:
        raise _refuse(422, KNOWN_AT_INVALID if key == "known_at" else RANGE_INVALID)
    return values[0] if values else None


def _instant(raw: str | None, refusal: tuple[str, str]) -> datetime | None:
    if raw is None:
        return None
    try:
        at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise _refuse(422, refusal) from error
    if at.tzinfo is None:
        raise _refuse(422, refusal)
    return at.astimezone(timezone.utc)


def _day(raw: str | None) -> date | None:
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError as error:
        raise _refuse(422, RANGE_INVALID) from error


def build_fuel_balance_router(reads: FuelNightRead | None, scope: Scope,
                              access: Access = development_access) -> APIRouter:
    router = APIRouter()

    def open_scope(request: Request, site_code: str) -> tuple[str, UUID, UUID]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read fuel checks."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        found = scope(site_code)
        if found is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if reads is None:
            raise _refuse(503, UNAVAILABLE)
        return found

    def served(work: Callable[[], Any], missing: tuple[str, str]) -> Any:
        try:
            body = work()
        except FuelNightRefused as refused:
            pair = RANGE_WINDOW_INVALID if refused.code == "INVALID_WINDOW" else KNOWN_AT_INVALID
            raise _refuse(422, pair) from refused
        except FuelNightUnavailable as error:
            raise _refuse(503, UNAVAILABLE) from error
        if body is None:
            raise _refuse(404, missing)
        return body

    @router.get("/api/sites/{site_code}/fuel-balance/nights")
    def nights(request: Request, site_code: str) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        raw_lo, raw_hi = _one(request, "from"), _one(request, "to")
        if any(raw is not None and "T" in raw for raw in (raw_lo, raw_hi)):
            # SR-10k: the date range's UTC instants (both or neither); the read names the Site-local days.
            start, end = _instant(raw_lo, RANGE_WINDOW_INVALID), _instant(raw_hi, RANGE_WINDOW_INVALID)
            if start is None or end is None or start >= end:
                raise _refuse(422, RANGE_WINDOW_INVALID)
            known = _instant(_one(request, "known_at"), KNOWN_AT_INVALID)
            return served(lambda: reads.nights(tenant_id=tenant_id, site_id=site_id, code=code, lo=None, hi=None,
                                               known_at=known, window=(start, end)), NIGHT_NOT_FOUND)
        lo, hi = _day(raw_lo), _day(raw_hi)
        known = _instant(_one(request, "known_at"), KNOWN_AT_INVALID)
        if (lo is None) != (hi is None):
            raise _refuse(422, RANGE_INVALID)
        if lo is not None and hi is not None and (lo >= hi or (hi - lo).days > MAX_NIGHTS):
            raise _refuse(422, RANGE_INVALID)
        return served(lambda: reads.nights(tenant_id=tenant_id, site_id=site_id, code=code, lo=lo, hi=hi,
                                           known_at=known), NIGHT_NOT_FOUND)

    @router.get("/api/sites/{site_code}/fuel-balance/nights/{night_date}")
    def night(request: Request, site_code: str, night_date: str) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        try:
            day = date.fromisoformat(night_date)
        except ValueError as error:
            raise _refuse(404, NIGHT_NOT_FOUND) from error
        known = _instant(_one(request, "known_at"), KNOWN_AT_INVALID)
        return served(lambda: reads.night(tenant_id=tenant_id, site_id=site_id, code=code, night_date=day,
                                          known_at=known), NIGHT_NOT_FOUND)

    @router.get("/api/sites/{site_code}/fuel-findings")
    def fuel_findings(request: Request, site_code: str) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        lo = _instant(_one(request, "from"), WINDOW_INVALID)
        hi = _instant(_one(request, "to"), WINDOW_INVALID)
        if lo is None or hi is None or lo >= hi:
            raise _refuse(422, WINDOW_INVALID)
        known = _instant(_one(request, "known_at"), KNOWN_AT_INVALID)
        return served(lambda: reads.fuel_findings(tenant_id=tenant_id, site_id=site_id, code=code, lo=lo, hi=hi,
                                                  known_at=known), FINDING_NOT_FOUND)

    @router.get("/api/sites/{site_code}/fuel-findings/{finding_id}")
    def fuel_finding(request: Request, site_code: str, finding_id: str) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        try:
            fid = UUID(finding_id)
            raw_revision = _one(request, "revision_id")
            revision = None if raw_revision is None else UUID(raw_revision)
        except ValueError as error:
            raise _refuse(404, FINDING_NOT_FOUND) from error
        known = _instant(_one(request, "known_at"), KNOWN_AT_INVALID)
        return served(lambda: reads.fuel_finding(tenant_id=tenant_id, site_id=site_id, code=code, finding_id=fid,
                                                 revision_id=revision, known_at=known), FINDING_NOT_FOUND)

    return router


__all__ = ["FINDING_NOT_FOUND", "NIGHT_NOT_FOUND", "RANGE_INVALID", "RANGE_WINDOW_INVALID", "build_fuel_balance_router"]
