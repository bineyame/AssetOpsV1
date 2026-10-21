"""S5-01: the imported-Site branch of the existing `GET /api/sites/{site_code}/overview` handler.

The evidence router keeps the single route at this path and delegates here first (no second router is
registered; the first included evidence router would shadow it). Order, per the packet "Gate and scope
composition":

1. `access(request, site_code)` before any tenant/Site discovery: 401 / 403 (the Finding read's convention).
2. `scope(site_code)` (`registry.ledger_scope`): None means a legacy Site, served by the legacy branch.
3. the S2-02 Evidence comparison (`imported_scope`, raising 409 `AWAITING_EVIDENCE_MIGRATION` when absent or
   failed) for the whole imported Overview; a closed Performance gate never bypasses it. W4-02 q12-6: only a
   persisted `NO_LEGACY_EVIDENCE` cutover basis for the Site's current import (`no_legacy_basis`) stands in for
   the comparison; it is never inferred from a missing comparison, and every other import keeps the 409.
4. one UTC day: `date=YYYY-MM-DD`, or `from`/`to` exactly one midnight-to-midnight day; anything else 422.
   No selection: the database clock's current UTC day.
5. the Performance gate (`performance_gate`) supplies `source_open`; the read applies it to every S3, Finding and
   money claim.

Optional `finding_id` / `finding_revision_id` (review N3) pin the previously selected Finding. They are scope
checked (a foreign or unknown ID is 404) and only retained while the basis is incomplete or the source is
closed; they never produce an amount.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.analytics.performance_comparison import basis_reason
from assetops_backend.site_overview.read import PinNotFound
from assetops_backend.sites.ports import SiteStoreUnavailable

Access = Callable[[Request, str], "int | None"]
Scope = Callable[[str], "tuple[str, UUID, UUID] | None"]
Gate = Callable[[str, UUID, UUID], "tuple[bool, str]"]

_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _invalid(message: str, code: str = "INVALID_WINDOW") -> HTTPException:
    return HTTPException(status_code=422, detail={"code": code, "message": message})


def selected_day(params: Any) -> date | None:
    """The one selected UTC day, None when nothing is selected; typed 422 for partial/conflicting/non-UTC."""
    text, start, end = params.get("date"), params.get("from"), params.get("to")
    day = None
    if text is not None:
        if not _DAY.fullmatch(text):
            raise _invalid("date is a UTC calendar day (YYYY-MM-DD)")
        try:
            day = date.fromisoformat(text)
        except ValueError as error:
            raise _invalid("date is a UTC calendar day (YYYY-MM-DD)") from error
    if start is None and end is None:
        return day
    if start is None or end is None:
        raise _invalid("from and to are given together, as exactly one UTC day", "PARTIAL_WINDOW")
    if not (_INSTANT.fullmatch(start) and _INSTANT.fullmatch(end)):
        raise _invalid("from and to are UTC instants (YYYY-MM-DDTHH:MM:SSZ)")
    lo = datetime.fromisoformat(start.replace("Z", "+00:00"))
    hi = datetime.fromisoformat(end.replace("Z", "+00:00"))
    if (lo.hour, lo.minute, lo.second) != (0, 0, 0) or hi - lo != timedelta(days=1):
        raise _invalid("from and to select exactly one UTC day [00:00Z, next 00:00Z)", "NOT_ONE_UTC_DAY")
    if day is not None and day != lo.date():
        raise _invalid("date conflicts with from/to", "CONFLICTING_WINDOW")
    return lo.date()


def legacy_window(params: Any) -> tuple[str | None, str | None] | None:
    """Legacy Sites: `date=` becomes the same midnight from/to pair; None keeps the legacy parameters."""
    text = params.get("date")
    if text is None:
        return None
    if params.get("from") is not None or params.get("to") is not None:
        raise _invalid("date conflicts with from/to", "CONFLICTING_WINDOW")
    day = selected_day({"date": text})
    lo = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return lo.strftime(fmt), (lo + timedelta(days=1)).strftime(fmt)


def _uuid(params: Any, name: str) -> UUID | None:
    value = params.get(name)
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError as error:
        raise _invalid(f"{name} is a UUID", "INVALID_FINDING_PIN") from error


def _closed_basis(tenant_id: UUID, site_id: UUID) -> bool:
    """No empty-legacy basis reader: the S2 comparison stays required."""
    return False


@dataclass
class SiteOverviewRoute:
    read: Any  # SiteOverviewRead, or None when no product database is configured
    scope: Scope
    gate: Gate
    access: Access
    access_basis: str
    unavailable: tuple[type, ...] = ()
    scope_unavailable: tuple[type, ...] = (SiteStoreUnavailable,)
    #: q12-6: True only for a persisted empty-legacy cutover basis; the default keeps the S2 comparison required.
    no_legacy_basis: Callable[[UUID, UUID], bool] = None  # type: ignore[assignment]  # set in __post_init__
    legacy_window = staticmethod(legacy_window)

    def __post_init__(self) -> None:
        if self.no_legacy_basis is None:
            self.no_legacy_basis = _closed_basis

    def serve(self, request: Request, site_code: str, s2_scope: Callable[[str], Any]) -> dict[str, Any] | None:
        refusal = self.access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read the Site Overview."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        try:
            found = self.scope(site_code)
        except self.scope_unavailable as error:  # review L1: the legacy handler's typed 503, kept
            raise HTTPException(status_code=503, detail={"code": "SITE_STORE_UNAVAILABLE",
                                                         "message": str(error)}) from error
        if found is None:
            return None
        code, tenant_id, site_id = found
        # 409 AWAITING_EVIDENCE_MIGRATION unless the S2 comparison passed; no comparison reader is also closed.
        # q12-6: a persisted NO_LEGACY_EVIDENCE basis for this import is the one alternative to the comparison.
        try:
            empty_legacy = bool(self.no_legacy_basis(tenant_id, site_id))
        except self.scope_unavailable as error:
            raise HTTPException(status_code=503, detail={"code": "SITE_STORE_UNAVAILABLE",
                                                         "message": str(error)}) from error
        if not empty_legacy and s2_scope(site_code) is None:
            raise HTTPException(status_code=409, detail={
                "code": "AWAITING_EVIDENCE_MIGRATION",
                "message": f"Site {code!r} has no passing Evidence comparison, so its Overview is not served."})
        params = request.query_params
        day = selected_day(params)
        fid, rid = _uuid(params, "finding_id"), _uuid(params, "finding_revision_id")
        if rid is not None and fid is None:
            raise _invalid("finding_revision_id needs finding_id", "INVALID_FINDING_PIN")
        if self.read is None:
            raise HTTPException(status_code=503, detail={"code": "SITE_OVERVIEW_UNAVAILABLE",
                                                         "message": "No product database is configured."})
        try:
            permitted, reason = self.gate(code, tenant_id, site_id)
            reason = basis_reason(bool(permitted), reason, empty_legacy)  # final review ruling 3 (M4)
            if day is None:
                day = self.read.db_today()
            body = self.read.read(code, tenant_id, site_id, day, access_basis=self.access_basis,
                                  source_open=bool(permitted), source_reason=reason,
                                  pinned=None if fid is None else (fid, rid))
        except PinNotFound as error:
            raise HTTPException(status_code=404, detail={"code": "FINDING_PIN_NOT_FOUND",
                                                         "message": str(error)}) from error
        except self.unavailable as error:
            raise HTTPException(status_code=503, detail={"code": "SITE_OVERVIEW_UNAVAILABLE",
                                                         "message": str(error)}) from error
        return jsonable_encoder(body)
