"""3B3: composition for the structure read (spec §3, P2). No route is added here (D-3B3.5).

`build_structure_read(database_url)` wires `ProductLeafSource` to the snapshot store and to the declared prices.
The adapters are reached only through their domains' compositions (the configuration-persistence guard: only
`chain/composition.py` and `financials/composition.py` may import their adapters), so the prices come from the
two existing window-price builders, each `PostgresAssumptionStore.snapshot` + `fuel_cost.select_window_price`
with its key and stored unit: `build_trial_comparison_ports(...).price_selection` (diesel, `currency/L`) and
`build_productive_price_selection` (productive use, `unit_for(PRODUCTIVE_PRICE_KEY)`).
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
    from assetops_backend.chain.composition import build_snapshot_store
    from assetops_backend.chain.reader import SnapshotReader
    from assetops_backend.financials.composition import (
        build_productive_price_selection,
        build_trial_comparison_ports,
    )
    from assetops_backend.structure.sources import PRICE_KEYS, ProductLeafSource

    snapshots = build_snapshot_store(database_url)
    if snapshots is None:
        raise RuntimeError("DATABASE_URL is not set, so the structure read cannot reach its sources.")
    diesel = build_trial_comparison_ports(database_url)
    by_key = {PRICE_KEYS["diesel_price"]: diesel.price_selection,
              PRICE_KEYS["productive_tariff"]: build_productive_price_selection(database_url)}

    def window_price(tenant_id: UUID, site_id: UUID, key: str, start: datetime, end: datetime,
                     known_at: datetime | None):
        return by_key[key](tenant_id, site_id, start, end, known_at)

    def dispose() -> None:
        snapshots.dispose()
        getattr(diesel.store, "dispose", lambda: None)()

    source = ProductLeafSource(SnapshotReader(snapshots), window_price, _utc_now)
    return StructureReadService(StructureRead(source), dispose)


__all__ = ["StructureReadService", "build_structure_read"]
