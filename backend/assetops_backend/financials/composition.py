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
from assetops_backend.financials.consequence_history import ConsequenceHistoryService
from assetops_backend.financials.consequence_read import ConsequenceReadService
from assetops_backend.financials.cold_recompute import ColdConsequenceWorker
from assetops_backend.financials.ev_recompute import EvConsequenceWorker
from assetops_backend.financials.recompute import ConsequenceRecomputeWorker

__all__ = ["Appended", "AssumptionStoreUnavailable", "ConsequenceStoreUnavailable", "PostgresAssumptionStore",
           "PostgresConsequenceStore", "Published", "build_assumption_read_service", "build_assumption_store",
           "build_consequence_history_service", "build_consequence_read_service", "build_consequence_store", "build_recompute_worker",
           "build_cold_consequence_store", "build_cold_consequence_worker", "build_ev_consequence_store",
           "build_ev_consequence_worker",
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
    from assetops_backend.evidence.composition import build_public_provenance
    from assetops_backend.financials.money_eligibility import MoneyEligibility

    return ConsequenceReadService(
        PostgresConsequenceStore(database_url), PostgresAssumptionStore(database_url),
        eligibility=MoneyEligibility(build_dispatch_read_service(database_url), build_finding_store(database_url)),
        provenance=build_public_provenance(database_url))


def build_consequence_history_service(database_url: str | None) -> ConsequenceHistoryService:
    """S4-08: the read-only Site consequence history with the S4-05b exact-revision source resolver."""
    from assetops_backend.evidence.composition import build_public_provenance

    return ConsequenceHistoryService(PostgresConsequenceStore(database_url),
                                     provenance=build_public_provenance(database_url))


def build_recompute_worker(database_url: str | None) -> ConsequenceRecomputeWorker:
    return ConsequenceRecomputeWorker(PostgresConsequenceStore(database_url), PostgresAssumptionStore(database_url),
                                      CONSEQUENCE_UNAVAILABLE)


def build_cold_consequence_store(database_url: str | None) -> PostgresConsequenceStore:
    """W2-04: the consequence store with the S4-05 link-row reader on its own connection (cold source gate)."""
    from assetops_backend.evidence.composition import build_link_rows_reader

    return PostgresConsequenceStore(database_url, link_rows=build_link_rows_reader())


def build_cold_consequence_worker(database_url: str | None) -> ColdConsequenceWorker:
    return ColdConsequenceWorker(build_cold_consequence_store(database_url), CONSEQUENCE_UNAVAILABLE)


def build_ev_consequence_store(database_url: str | None) -> PostgresConsequenceStore:
    """W2-07: the consequence store with the S4-05 link-row reader (EV source gate) and W2-06's exact EV selection
    snapshot, both on the worker's own connection."""
    from assetops_backend.analytics.composition import build_ev_selected_snapshot
    from assetops_backend.evidence.composition import build_link_rows_reader

    link_rows = build_link_rows_reader()
    return PostgresConsequenceStore(database_url, link_rows=link_rows,
                                    ev_snapshot=build_ev_selected_snapshot(link_rows))


def build_ev_consequence_worker(database_url: str | None) -> EvConsequenceWorker:
    return EvConsequenceWorker(build_ev_consequence_store(database_url), CONSEQUENCE_UNAVAILABLE)


def build_ev_site_read_service(database_url: str):
    """W2-07 commit 3: the five EV Site reads over W2-06's `EvReadService` and the SELECT-only EV money reads, both
    on the one read connection (q4's shared selector)."""
    from assetops_backend.analytics.composition import build_ev_read_service
    from assetops_backend.ev_site_reads import EvSiteReads
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.financials.adapters.postgres_consequence_store import EvMoneyReads

    return EvSiteReads(build_ev_read_service(database_url), EvMoneyReads(build_link_rows_reader()))
