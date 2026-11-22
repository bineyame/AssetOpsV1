"""6a (spec §4): the decisions composition, the only importer of its adapter. Callers receive the `DecisionService`
over the `DecisionStore` port and the `dispose` that closes both connection pools."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from assetops_backend.accounts.composition import build_account_service
from assetops_backend.decisions.adapters.postgres_decision_store import PostgresDecisionStore
from assetops_backend.decisions.records import DecisionService

__all__ = ["DecisionsService", "build_decisions"]


@dataclass
class DecisionsService:
    service: DecisionService
    dispose: Callable[[], None]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_decisions(database_url: str, *, clock: Callable[[], datetime] = _now) -> DecisionsService:
    store = PostgresDecisionStore(database_url)
    accounts = build_account_service(database_url)

    def dispose() -> None:  # both pools: the decision store's and the accounts store's
        store.dispose()
        accounts._store.dispose()

    return DecisionsService(DecisionService(store, accounts, clock=clock), dispose)
