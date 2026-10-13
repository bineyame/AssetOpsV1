"""Composition for the financials domain: the only module that imports its adapters."""

from __future__ import annotations

from assetops_backend.financials.adapters.postgres_assumption_store import (
    AssumptionStoreUnavailable,
    PostgresAssumptionStore,
    Published,
)

__all__ = ["AssumptionStoreUnavailable", "PostgresAssumptionStore", "Published", "build_assumption_store"]


def build_assumption_store(database_url: str | None) -> PostgresAssumptionStore:
    return PostgresAssumptionStore(database_url)
