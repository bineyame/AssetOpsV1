"""3B7a unit 3 (spec §4.3): the snapshot builder and served read, wired. No route (`5c` reads through this).

The actual side is `structure.composition.build_structure_read`; the budget lines and the months come from
`commercial.composition.build_commercial_reads`; the snapshot store is this domain's Postgres adapter (only this
module imports it). A failure in any builder disposes those already built; `dispose` disposes all three. The code
digest (D-3B7A.11) is computed once and handed to both the builder and the read. This module is the root of that
digest's import closure (`rules_digest.RULE_ROOTS`), so every module a build can reach is covered.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from assetops_backend.structure_snapshot.build import SnapshotBuilder
from assetops_backend.structure_snapshot.read import SnapshotRead
from assetops_backend.structure_snapshot.store import StructureSnapshotStore


@dataclass(frozen=True)
class StructureSnapshotService:
    builder: SnapshotBuilder
    read: SnapshotRead
    store: StructureSnapshotStore
    dispose: Callable[[], None]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_structure_snapshot(database_url: str) -> StructureSnapshotService:
    from assetops_backend.commercial.composition import build_commercial_reads
    from assetops_backend.structure.composition import build_structure_read
    from assetops_backend.structure.targets.lines import BudgetLineReader
    from assetops_backend.structure.targets.read import TargetRead
    from assetops_backend.structure_snapshot.adapters.postgres_structure_snapshot_store import \
        PostgresStructureSnapshotStore
    from assetops_backend.structure_snapshot.kinds import StoreHeldKinds
    from assetops_backend.structure_snapshot.rules_digest import rules_digest

    actual = build_structure_read(database_url)
    try:
        reads = build_commercial_reads(database_url)
    except BaseException:
        actual.dispose()  # never leak the first service when the second builder raises
        raise
    try:
        store = PostgresStructureSnapshotStore(database_url)
    except BaseException:
        actual.dispose()
        reads.dispose()
        raise

    def dispose() -> None:
        try:
            actual.dispose()
        finally:
            try:
                reads.dispose()
            finally:
                store.dispose()

    lines = BudgetLineReader(reads.months, reads.store)
    targets = TargetRead(lines, actual.read)
    kinds = StoreHeldKinds(reads.store)
    rules = rules_digest()
    builder = SnapshotBuilder(actual.read, targets, lines, store, kinds, rules, _utc_now)
    read = SnapshotRead(store, reads.months, kinds, rules, _utc_now)
    return StructureSnapshotService(builder, read, store, dispose)


__all__ = ["StructureSnapshotService", "build_structure_snapshot"]
