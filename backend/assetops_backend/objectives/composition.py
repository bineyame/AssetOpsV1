"""OUT-D U3: the composition root of the declared-objective store; the only importer of its adapter."""
from __future__ import annotations

from assetops_backend.objectives.adapters.postgres_objective_store import (
    ObjectiveStoreUnavailable,
    PostgresObjectiveStore,
)

__all__ = ["ObjectiveStoreUnavailable", "PostgresObjectiveStore", "build_objective_store"]


def build_objective_store(database_url: str | None) -> PostgresObjectiveStore | None:
    """The store, or None when no database is configured (the board then reads no objectives)."""
    return PostgresObjectiveStore(database_url) if database_url else None
