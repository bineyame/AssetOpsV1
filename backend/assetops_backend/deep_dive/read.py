"""5c (spec section 4.1; D-3A7.9, D-5C.4): the deep-dive month read.

One served portfolio snapshot (3B7a); when it is served, one organisation standing read at the snapshot's `as_of` (no
Site standing is read); the agreed Actions through the port; then the pure `month_view`. No text is built here.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from assetops_backend.deep_dive import tables as T
from assetops_backend.deep_dive import period as P
from assetops_backend.deep_dive.actions import AgreedActionsPort
from assetops_backend.deep_dive.view import month_view

if TYPE_CHECKING:
    from assetops_backend.sites.foundation_records import TenantRef
    from assetops_backend.structure.reconciliation import CommercialReconciliation
    from assetops_backend.structure_snapshot.read import SnapshotRead

BAD_MONTH = "BAD_MONTH"
SERVED = "SERVED"


class BadMonth(ValueError):
    """`ValueError("BAD_MONTH")` (spec section 4.1), typed so the route answers it without reading its text."""


#: IA-P (`spec-period.md` P.2, P.6): `BAD_RANGE` or `RANGE_TOO_LONG`, typed so the route answers it by its code.
BadRange = P.RangeRefused


#: P.3: how far back the mode-`none` suggestion looks.
SUGGEST_READS = 12


def previous_month(now: datetime) -> str:
    """The calendar month before `now`'s UTC month."""
    utc = now.astimezone(timezone.utc)
    return T.month_code(utc.year, utc.month - 1)


class DeepDiveRead:
    def __init__(self, snapshots: SnapshotRead, reconciliation: CommercialReconciliation,
                 actions: AgreedActionsPort, clock: Callable[[], datetime]) -> None:
        self._snapshots = snapshots
        self._reconciliation = reconciliation
        self._actions = actions
        self._clock = clock

    def month(self, tenant: TenantRef, month: str | None, names: Mapping[str, str]) -> dict:
        now = self._clock()
        if month is None:
            month = previous_month(now)
        elif not isinstance(month, str) or T.MONTH_PATTERN.fullmatch(month) is None:
            raise BadMonth(BAD_MONTH)
        served = self._snapshots.portfolio(tenant.id, month)
        standing = None
        if served.state == SERVED:
            standing = self._reconciliation.standing(tenant.id, None, month, known_at=served.as_of)
        actions = self._actions.for_tenant(tenant.id)
        return month_view(operator=tenant.name, month=month, served=served, standing=standing, actions=actions,
                          names=names, now=now)

    # --- IA-P P3a (`spec-period.md` P.3) ---------------------------------------------------------------------------

    def _resolve(self, first: date, last: date) -> tuple[datetime, P.Period]:
        now = self._clock()
        return now, P.resolve(first, last, now)

    def _months(self, tenant: TenantRef, months) -> tuple[P.MonthServed, ...]:
        out = []
        for m in months:
            served = self._snapshots.portfolio(tenant.id, m)
            standing = (self._reconciliation.standing(tenant.id, None, m, known_at=served.as_of)
                        if served.state == SERVED else None)
            out.append(P.MonthServed(m, served, standing))
        return tuple(out)

    def _suggest(self, tenant: TenantRef, last: date, now: datetime) -> str | None:
        """The latest closed month whose first day is on or before `last`, stepping back to the first SERVED one,
        at most `SUGGEST_READS` reads."""
        month = min(T.month_code(last.year, last.month), previous_month(now))
        year, mon = (int(p) for p in month.split("-"))
        for back in range(SUGGEST_READS):
            code = T.month_code(year, mon - back)
            if self._snapshots.portfolio(tenant.id, code).state == SERVED:
                return code
        return None

    def _period_reads(self, tenant: TenantRef, first: date, last: date):
        now, p = self._resolve(first, last)
        read = self._months(tenant, p.months)
        suggest = self._suggest(tenant, last, now) if P.mode_of(read) == T.MODE_NONE else None
        return now, p, read, suggest

    def period(self, tenant: TenantRef, first: date, last: date, names: Mapping[str, str]) -> dict:
        now, p, read, suggest = self._period_reads(tenant, first, last)
        actions = self._actions.for_tenant(tenant.id) if P.mode_of(read) == T.MODE_PERIOD else None
        return P.period_view(period=p, read=read, suggest=suggest, names=names, actions=actions, now=now)
