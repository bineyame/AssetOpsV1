"""6a (spec §4): the decisions composition, the only importer of its adapter. Callers receive the `DecisionService`
over the `DecisionStore` port and the `dispose` that closes both connection pools."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from assetops_backend.accounts.composition import build_account_service
from assetops_backend.decisions.adapters.postgres_decision_store import PostgresDecisionStore
from assetops_backend.decisions.adapters.study_file import read_study_bytes
from assetops_backend.decisions.records import DecisionService
from assetops_backend.decisions.run import EvaluationService

__all__ = ["DecisionsService", "EvaluationsService", "build_decisions", "build_evaluation"]


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


@dataclass
class EvaluationsService:
    service: EvaluationService
    dispose: Callable[[], None]


def build_evaluation(database_url: str, *, clock: Callable[[], datetime] = _now) -> EvaluationsService:
    """6c (spec §4): the evaluation service over the decision store, the accounts and the structure read."""
    from assetops_backend.structure.composition import build_structure_read

    store = PostgresDecisionStore(database_url)
    accounts = build_account_service(database_url)
    try:
        structure = build_structure_read(database_url)
    except BaseException:
        store.dispose()
        accounts._store.dispose()
        raise

    def dispose() -> None:  # the three pools: decisions, accounts and the structure read's sources
        store.dispose()
        accounts._store.dispose()
        structure.dispose()

    return EvaluationsService(EvaluationService(store, accounts, structure.read, clock=clock,
                                                read_bytes=read_study_bytes), dispose)
