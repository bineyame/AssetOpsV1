"""5c (spec section 4.1): the deep-dive read, wired. 3B7a's snapshot read, 3A7's reconciliation and the actions port.

Imports no adapter: each store comes through its own composition. A failure in any builder disposes those already
built; `dispose` disposes all three (the agreed-action service's pools included).
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from assetops_backend.actions.agreed_composition import build_agreed_actions
from assetops_backend.deep_dive.actions import StoreAgreedActions
from assetops_backend.deep_dive.read import DeepDiveRead
from assetops_backend.structure.reconciliation_composition import build_commercial_reconciliation
from assetops_backend.structure_snapshot.composition import build_structure_snapshot


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _dispose_all(disposers: list[Callable[[], None]]) -> None:
    error: BaseException | None = None
    for dispose in disposers:
        try:
            dispose()
        except BaseException as raised:  # every store is disposed; the first failure is raised after
            error = error or raised
    if error is not None:
        raise error


def build_deep_dive_read(database_url: str) -> tuple[DeepDiveRead, Callable[[], None]]:
    disposers: list[Callable[[], None]] = []
    try:
        snapshots = build_structure_snapshot(database_url)
        disposers.append(snapshots.dispose)
        reconciliation, reconciliation_dispose = build_commercial_reconciliation(database_url)
        disposers.append(reconciliation_dispose)
        agreed = build_agreed_actions(database_url)
        disposers.append(agreed.dispose)
        actions = StoreAgreedActions(agreed.service)
    except BaseException:
        _dispose_all(disposers)  # never leak a store already built when a later builder raises
        raise
    read = DeepDiveRead(snapshots.read, reconciliation, actions, _utc_now)
    return read, lambda: _dispose_all(disposers)


__all__ = ["build_deep_dive_read"]
