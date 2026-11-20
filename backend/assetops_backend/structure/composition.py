"""3B3: composition for the structure read (spec §3, P2). No route is added here (D-3B3.5).

`build_structure_read(database_url)` wires `ProductLeafSource` to the snapshot store and to the declared prices.
The adapters are reached only through their domains' compositions (the configuration-persistence guard: only
`chain/composition.py` and `financials/composition.py` may import their adapters), so the prices come from
`financials.composition.build_window_price_selection`: one assumption store, disposed with the service.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

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
    from assetops_backend.financials.composition import build_window_price_selection
    from assetops_backend.structure.sources import ProductLeafSource

    snapshots = build_snapshot_store(database_url)
    if snapshots is None:
        raise RuntimeError("DATABASE_URL is not set, so the structure read cannot reach its sources.")
    try:
        prices = build_window_price_selection(database_url)
    except BaseException:
        snapshots.dispose()  # L1: never leak the store when the second builder raises
        raise

    def dispose() -> None:
        snapshots.dispose()
        prices.dispose()

    source = ProductLeafSource(SnapshotReader(snapshots), prices.select, _utc_now)
    return StructureReadService(StructureRead(source), dispose)


__all__ = ["StructureReadService", "build_structure_read"]
