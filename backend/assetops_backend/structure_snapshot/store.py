"""3B7a unit 2 (spec §3.1; D-3B7A.1): the snapshot store port and its in-memory implementation.

Rows are never updated or deleted. Scope uniqueness: `(tenant_id, site_id, period, as_of)` for Site rows and
`(tenant_id, period, as_of)` for portfolio rows; `put` writes all of its rows or none.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure_snapshot.model import SnapshotRow


class SnapshotExists(Exception):
    """A row for the same scope and as_of already exists; nothing was written."""


class StructureSnapshotStore(Protocol):
    def tenant_sites(self, slug: str) -> tuple[UUID, tuple[SiteRef, ...]] | None:
        """The tenant and every Site of it (every lifecycle), sorted by site_code; None for an unknown slug."""

    def put(self, rows: Sequence[SnapshotRow]) -> None:
        """One transaction: all rows or none; `SnapshotExists` on a scope already held."""

    def latest_site(self, tenant_id: UUID, site_id: UUID, period: str) -> SnapshotRow | None:
        """The Site row with the greatest as_of."""

    def latest_portfolio(self, tenant_id: UUID, period: str) -> SnapshotRow | None:
        """The portfolio row with the greatest as_of."""

    def get(self, tenant_id: UUID, ids: Sequence[UUID]) -> tuple[SnapshotRow, ...]:
        """The rows in the order given; a missing id raises LookupError."""


def _scope(row: SnapshotRow) -> tuple:
    return row.tenant_id, row.site_id, row.period, row.as_of


class MemoryStructureSnapshotStore:
    def __init__(self) -> None:
        self.rows: list[SnapshotRow] = []
        self.sites: dict[str, tuple[UUID, tuple[SiteRef, ...]]] = {}  # slug -> (tenant, Sites); set by the test

    def tenant_sites(self, slug: str) -> tuple[UUID, tuple[SiteRef, ...]] | None:
        found = self.sites.get(slug)
        if found is None:
            return None
        return found[0], tuple(sorted(found[1], key=lambda s: s.site_code))

    def put(self, rows: Sequence[SnapshotRow]) -> None:
        scopes = {_scope(r) for r in self.rows}
        ids = {r.id for r in self.rows}
        for row in rows:  # every row is checked before any is kept
            if _scope(row) in scopes or row.id in ids:
                raise SnapshotExists()
            scopes.add(_scope(row))
            ids.add(row.id)
        self.rows.extend(rows)

    def _latest(self, tenant_id: UUID, site_id: UUID | None, period: str) -> SnapshotRow | None:
        found = [r for r in self.rows if r.tenant_id == tenant_id and r.site_id == site_id and r.period == period]
        return max(found, key=lambda r: r.as_of) if found else None

    def latest_site(self, tenant_id: UUID, site_id: UUID, period: str) -> SnapshotRow | None:
        return self._latest(tenant_id, site_id, period)

    def latest_portfolio(self, tenant_id: UUID, period: str) -> SnapshotRow | None:
        return self._latest(tenant_id, None, period)

    def get(self, tenant_id: UUID, ids: Sequence[UUID]) -> tuple[SnapshotRow, ...]:
        by_id = {r.id: r for r in self.rows if r.tenant_id == tenant_id}
        out = []
        for i in ids:
            if i not in by_id:
                raise LookupError(f"no snapshot {i}")
            out.append(by_id[i])
        return tuple(out)


__all__ = ["MemoryStructureSnapshotStore", "SnapshotExists", "StructureSnapshotStore"]
