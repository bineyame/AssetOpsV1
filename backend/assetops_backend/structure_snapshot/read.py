"""3B7a unit 2 (spec §3.3; D-3B7A.3, D-3B7A.11, D-3B7A.12): the served read.

It reads stored rows, `CommercialMonths.stale` and the held record kinds only: no structure read, no target read, no
evaluation and no month read. Out-of-date values are served with their reasons, never as current; a row of another
structure version or format is never decoded (`REBUILD_NEEDED`).
"""
from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from assetops_backend.chain.ports import SiteRef
from assetops_backend.commercial.months import PORTFOLIO_ZONE, month_bounds
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.read import KEY_NOT_READ, NOT_DECLARED, SITE_TYPE_TO_STRUCTURE, SiteInputs
from assetops_backend.structure.registry import REGISTRIES
from assetops_backend.structure_snapshot import codec
from assetops_backend.structure_snapshot.kinds import HeldKinds
from assetops_backend.structure_snapshot.model import REASONS, SNAPSHOT_FORMAT, Freshness, Served, SiteMonthSnapshot, \
    SnapshotRow
from assetops_backend.structure_snapshot.store import StructureSnapshotStore
from assetops_backend.structure_snapshot.untracked import untracked

if TYPE_CHECKING:
    from assetops_backend.commercial.months import CommercialMonths

_MONTH = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", re.ASCII)


def _check_month(month: str) -> str:
    if not isinstance(month, str) or _MONTH.fullmatch(month) is None:
        raise ValueError(f"month {month!r} is not YYYY-MM")
    return month


def _ordered(reasons: set[str]) -> tuple[str, ...]:
    return tuple(r for r in REASONS if r in reasons)


def _site_untracked(inputs: SiteInputs) -> tuple[str, ...]:
    return untracked(inputs)


class SnapshotRead:
    def __init__(self, store: StructureSnapshotStore, months: "CommercialMonths", kinds: HeldKinds, rules: str,
                 clock: Callable[[], datetime]) -> None:
        self._store = store
        self._months = months
        self._kinds = kinds
        self._rules = rules
        self._clock = clock

    def site(self, tenant_id: UUID, site: SiteRef, month: str) -> Served:
        key = SITE_TYPE_TO_STRUCTURE.get(site.site_type)
        if key is None:
            raise StructureError(NOT_DECLARED[0], str(site.site_type), site.site_code)
        if key != SITE_TYPE_TO_STRUCTURE["MINIGRID"]:  # 3B6 (D-3B6.6): snapshots are built for MINI_GRID only
            raise StructureError(KEY_NOT_READ, key, site.site_code)
        _check_month(month)
        row = self._store.latest_site(tenant_id, site.site_id, month)
        if row is None:
            return Served("NO_SNAPSHOT", None, None, None)
        rebuild = self._rebuild_needed(row, [row])
        if rebuild is not None:
            return rebuild
        snapshot = codec.decode_site(row, site)
        freshness = self._freshness(tenant_id, row, [(row, snapshot)], _site_untracked(snapshot.inputs))
        return Served("SERVED", snapshot, row.as_of, freshness)

    def portfolio(self, tenant_id: UUID, month: str) -> Served:
        _check_month(month)
        row = self._store.latest_portfolio(tenant_id, month)
        if row is None:
            return Served("NO_SNAPSHOT", None, None, None)
        site_rows = self._store.get(tenant_id, row.site_snapshot_ids or ())
        rebuild = self._rebuild_needed(row, [row, *site_rows])
        if rebuild is not None:
            return rebuild
        decoded = [(r, codec.decode_site(r, codec.site_ref(r))) for r in site_rows]
        snapshot = codec.decode_portfolio(row, {s.site.site_code: s for _, s in decoded})
        sites = [(r, snapshot.sites[code]) for code in snapshot.asked for r, s in decoded if s.site.site_code == code]
        missing = tuple(f"{s.site.site_code}:{leaf}" for _, s in sites for leaf in _site_untracked(s.inputs))
        freshness = self._freshness(tenant_id, row, sites, missing, portfolio=True)
        return Served("SERVED", snapshot, row.as_of, freshness)

    def _rebuild_needed(self, served: SnapshotRow, rows: Sequence[SnapshotRow]) -> Served | None:
        """Step 1: a stored form the code no longer reads; only these two reasons, the payload not decoded."""
        reasons = set()
        for r in rows:
            if r.format != SNAPSHOT_FORMAT:
                reasons.add("FORMAT")
            reg = REGISTRIES.get(r.structure_key)
            if reg is None or r.structure_version != reg.version:
                reasons.add("STRUCTURE_VERSION")
        if not reasons:
            return None
        return Served("REBUILD_NEEDED", None, served.as_of, Freshness(False, _ordered(reasons), (), (), ()))

    def _freshness(self, tenant_id: UUID, row: SnapshotRow, sites: Sequence[tuple[SnapshotRow, SiteMonthSnapshot]],
                   missing: tuple[str, ...], portfolio: bool = False) -> Freshness:
        """Steps 2 to 4: RECORDS (stamps and held kinds), MONTH_CLOSED, RULES."""
        now = self._clock()
        rows = ([row] if portfolio else []) + [r for r, _ in sites]
        stale = tuple(self._months.stale(tenant_id, [stamp for r in rows for stamp in r.stamps]))
        changed = []
        for r, s in sites:
            held_now = set(self._kinds.of(tenant_id, r.site_id))
            changed.extend(f"{s.site.site_code}:{kind}" for kind in sorted(held_now ^ set(r.held_kinds)))
        reasons = set()
        if stale or changed:
            reasons.add("RECORDS")
        zones = ([(row, PORTFOLIO_ZONE)] if portfolio else []) + [(r, s.site.timezone) for r, s in sites]
        if any(not r.closed_at_build and now >= month_bounds(r.period, zone)[1] for r, zone in zones):
            reasons.add("MONTH_CLOSED")
        if any(r.rules_digest != self._rules for r in rows):
            reasons.add("RULES")
        ordered = _ordered(reasons)
        return Freshness(ordered == (), ordered, stale, tuple(changed), missing)


__all__ = ["SnapshotRead"]
