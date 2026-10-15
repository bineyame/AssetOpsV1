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
from assetops_backend.financials.consequence_read import ConsequenceReadService
from assetops_backend.financials.recompute import ConsequenceRecomputeWorker

__all__ = ["Appended", "AssumptionStoreUnavailable", "ConsequenceStoreUnavailable", "PostgresAssumptionStore",
           "PostgresConsequenceStore", "Published", "build_assumption_read_service", "build_assumption_store",
           "build_consequence_read_service", "build_consequence_store", "build_recompute_worker",
           "CONSEQUENCE_UNAVAILABLE"]

# Store failures the consequence read and the recompute worker report as typed unavailable.
CONSEQUENCE_UNAVAILABLE = (ConsequenceStoreUnavailable, AssumptionStoreUnavailable)


def build_assumption_store(database_url: str | None) -> PostgresAssumptionStore:
    return PostgresAssumptionStore(database_url)


def build_assumption_read_service(database_url: str | None) -> AssumptionReadService:
    return AssumptionReadService(PostgresAssumptionStore(database_url))


def build_consequence_store(database_url: str | None) -> PostgresConsequenceStore:
    return PostgresConsequenceStore(database_url)


def build_consequence_read_service(database_url: str | None) -> ConsequenceReadService:
    # LR-01: the shared money eligibility gate reads the S3 selected windows and S4 Finding rows (lazy import,
    # as the scheduling composition does, so the analytics composition stays the only owner of its adapters).
    from assetops_backend.analytics.composition import build_dispatch_read_service, build_finding_store
    from assetops_backend.financials.money_eligibility import MoneyEligibility

    return ConsequenceReadService(
        PostgresConsequenceStore(database_url), PostgresAssumptionStore(database_url),
        eligibility=MoneyEligibility(build_dispatch_read_service(database_url), build_finding_store(database_url)))


def build_recompute_worker(database_url: str | None) -> ConsequenceRecomputeWorker:
    return ConsequenceRecomputeWorker(PostgresConsequenceStore(database_url), PostgresAssumptionStore(database_url),
                                      CONSEQUENCE_UNAVAILABLE)
