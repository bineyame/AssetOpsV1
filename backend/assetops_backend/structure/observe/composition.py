"""3B4 unit 3 (spec §5.1): the structure observer, wired.

The served snapshot read and its store come from `structure_snapshot.composition.build_structure_snapshot`; the
Finding store and the assessment store from `analytics.composition` (as `fuel_balance/composition.py` builds them);
the clock is UTC now. A failure in any builder disposes what was already built.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from assetops_backend.structure.observe.floor import StoreFloorRead
from assetops_backend.structure.observe.service import StructureObserver


@dataclass(frozen=True)
class Wiring:
    observer: StructureObserver
    store: Any                 # the snapshot store: `tenant_sites`, `get`
    findings: Any              # the Finding store: `tolerances`, `tolerance_append`
    dispose: Callable[[], None]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_structure_observer(database_url: str) -> Wiring:
    from assetops_backend.analytics.composition import build_finding_store, build_postgres_assessment_store
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store
    from assetops_backend.structure_snapshot.composition import build_structure_snapshot

    snapshot = build_structure_snapshot(database_url)
    try:
        findings = build_finding_store(database_url)
        assessments = build_postgres_assessment_store(database_url)
        try:
            fuel = build_fuel_balance_store(database_url)
        except BaseException:
            assessments.dispose()
            raise
    except BaseException:
        snapshot.dispose()
        raise

    def dispose() -> None:
        try:
            snapshot.dispose()
        finally:
            try:
                assessments.dispose()
            finally:
                fuel.dispose()

    try:
        observer = StructureObserver(snapshot.read, snapshot.store, findings, assessments, _utc_now,
                                     StoreFloorRead(fuel))
    except BaseException:
        dispose()
        raise
    return Wiring(observer, snapshot.store, findings, dispose)


__all__ = ["Wiring", "build_structure_observer"]
