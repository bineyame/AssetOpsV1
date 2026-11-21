"""5c (spec section 4.1; D-3A7.9, D-5C.4): the deep-dive month read.

One served portfolio snapshot (3B7a); when it is served, one organisation standing read at the snapshot's `as_of` (no
Site standing is read); the agreed Actions through the port; then the pure `month_view`. No text is built here.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from assetops_backend.deep_dive import tables as T
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

