"""3B3: composition for the structure read (spec §3, P2): the only structure module that names adapters.

`build_structure_read(database_url)` wires `ProductLeafSource` to the snapshot store and to the declared prices,
read as `financials/composition.py` reads them (`PostgresAssumptionStore.snapshot` and
`fuel_cost.select_window_price(..., key=key, unit=unit_for(key))`). No route is added here (D-3B3.5).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from assetops_backend.structure.read import StructureRead


@dataclass(frozen=True)
class StructureReadService:
    read: StructureRead
    dispose: Callable[[], None]


def _utc_now() -> datetime:
    """The default "has the month closed" instant when a read passes no `known_at`."""
    return datetime.now(timezone.utc)


def build_structure_read(database_url: str | None) -> StructureReadService:
    from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
    from assetops_backend.chain.reader import SnapshotReader
    from assetops_backend.financials import fuel_cost
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.assumptions import unit_for
    from assetops_backend.structure.sources import ProductLeafSource

    snapshots = PostgresSnapshotStore(database_url)
    prices = PostgresAssumptionStore(database_url)

    def window_price(tenant_id: UUID, site_id: UUID, key: str, start: datetime, end: datetime,
                     known_at: datetime | None):
        snap = prices.snapshot(tenant_id, site_id, key, known_at, 0, 1)
        return fuel_cost.select_window_price(snap["timeline"], snap["cited"], start, end, key=key,
                                             unit=unit_for(key))

    def dispose() -> None:
        snapshots.dispose()
        prices.dispose()

    source = ProductLeafSource(SnapshotReader(snapshots), window_price, _utc_now)
    return StructureReadService(StructureRead(source), dispose)


__all__ = ["StructureReadService", "build_structure_read"]
