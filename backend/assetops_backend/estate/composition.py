"""W3-01 estate composition: the read-only estate adapter wired to the reviewed connection-taking W1/W2 reads.

Lane A mounts `build_estate_router` in `main.py`; this module only builds the service and its tenant seam.
"""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from assetops_backend.estate.index import EstateIndexService


def build_estate_read(database_url: str | None) -> Any:
    from assetops_backend.actions.composition import build_action_store
    from assetops_backend.analytics.cold_reads import ColdPinnedLineageUnavailable, ColdReadUnavailable
    from assetops_backend.analytics.composition import (
        build_cold_read_service, build_dispatch_read_service, build_ev_read_service, build_finding_store,
        build_postgres_assessment_store, selection_pin_refused)
    from assetops_backend.analytics.ev_reads import EvPinnedLineageUnavailable, EvReadUnavailable
    from assetops_backend.estate.adapters.postgres_estate_read import PostgresEstateRead
    from assetops_backend.evidence.composition import build_link_rows_many_reader, build_link_rows_reader
    from assetops_backend.analytics.cold_site_reads import ColdSiteReadService
    from assetops_backend.ev_site_reads import EvSiteReads
    from assetops_backend.evidence.public_provenance import LinkRowsReads
    from assetops_backend.financials.composition import (
        build_cold_consequence_store, build_consequence_read_service, build_ev_money_reads)
    from assetops_backend.financials.money_eligibility import MoneyEligibility

    findings = build_finding_store(database_url)
    link_rows = build_link_rows_reader()
    # W3-02 0c: the pinned Site facades share the estate owner's cold/EV read services and run on its connection.
    cold, ev, ev_money = build_cold_read_service(database_url), build_ev_read_service(database_url), \
        build_ev_money_reads(link_rows)

    def provenance_reads(c: Any) -> Any:  # set resolution on the estate connection only
        return LinkRowsReads(lambda t, s, ids: list(link_rows(c, t, s, ids)))

    return PostgresEstateRead(
        database_url, findings=findings, assessments=build_postgres_assessment_store(database_url),
        actions=build_action_store(database_url), consequences=build_consequence_read_service(database_url),
        eligibility=MoneyEligibility(build_dispatch_read_service(database_url), findings),
        cold=cold, ev=ev, provenance_reads=provenance_reads, link_rows_many=build_link_rows_many_reader(),
        inconsistent=(ColdPinnedLineageUnavailable, EvPinnedLineageUnavailable, selection_pin_refused()),
        unavailable=(ColdReadUnavailable, EvReadUnavailable),
        cold_site=ColdSiteReadService(cold, build_cold_consequence_store(database_url)),
        ev_site=EvSiteReads(ev, ev_money), ev_money=ev_money)


def build_estate_index_service(database_url: str | None) -> EstateIndexService | None:
    """None without a product database: the router answers 503, never an empty estate."""
    return None if not database_url else EstateIndexService(build_estate_read(database_url))


def build_estate_evidence_service(database_url: str | None) -> Any:
    """W3-02: None without a product database (the router answers 503, never an empty estate)."""
    if not database_url:
        return None
    from assetops_backend.analytics.claim_limit_read import ClaimLimitReadService, ClaimLimitRefusal
    from assetops_backend.estate.adapters.postgres_evidence_money_read import PostgresEvidenceMoneyRead
    from assetops_backend.estate.evidence_money import EstateEvidenceService

    base = build_estate_read(database_url)
    keys = ("findings", "assessments", "actions", "consequences", "eligibility", "cold", "ev", "provenance_reads",
            "inconsistent", "unavailable", "cold_site", "ev_site", "ev_money", "link_rows_many")
    return EstateEvidenceService(PostgresEvidenceMoneyRead(
        database_url, claim_limits=ClaimLimitReadService(base.assessments), claim_limit_refused=(ClaimLimitRefusal,),
        **{k: getattr(base, k) for k in keys}))


def build_estate_portfolio_service(database_url: str | None) -> Any:
    """W3-03: the Portfolio service on the W3-02 one-transaction reader; None without a product database (503)."""
    evidence = build_estate_evidence_service(database_url)
    if evidence is None:
        return None
    from assetops_backend.estate.portfolio import EstatePortfolioService

    return EstatePortfolioService(evidence.store)


def registry_tenant(registry: Any) -> Callable[[], UUID | None]:
    """The server's configured tenant from `ImportedSiteRegistry.tenant()`; never a client-supplied ID."""
    def tenant() -> UUID | None:
        found = registry.tenant()
        return None if found is None else found.id
    return tenant
