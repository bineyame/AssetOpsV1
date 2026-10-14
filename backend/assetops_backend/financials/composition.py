"""Composition for the financials domain: the only module that imports its adapters."""

from __future__ import annotations

from assetops_backend.financials.adapters.postgres_assumption_store import (
    AssumptionStoreUnavailable,
    PostgresAssumptionStore,
    Published,
)
from assetops_backend.financials.adapters.postgres_consequence_store import (
    Appended,
    ConsequenceStoreUnavailable,
    PostgresConsequenceStore,
)
from assetops_backend.financials.assumption_read import AssumptionReadService

__all__ = ["Appended", "AssumptionStoreUnavailable", "ConsequenceStoreUnavailable", "PostgresAssumptionStore",
           "PostgresConsequenceStore", "Published", "build_assumption_read_service", "build_assumption_store",
           "build_consequence_store"]


def build_assumption_store(database_url: str | None) -> PostgresAssumptionStore:
    return PostgresAssumptionStore(database_url)


def build_assumption_read_service(database_url: str | None) -> AssumptionReadService:
    return AssumptionReadService(PostgresAssumptionStore(database_url))


def build_consequence_store(database_url: str | None) -> PostgresConsequenceStore:
    return PostgresConsequenceStore(database_url)
