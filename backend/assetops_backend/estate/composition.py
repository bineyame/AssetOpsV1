"""W3-01 estate composition: the read-only estate adapter wired to the reviewed connection-taking W1/W2 reads.

Lane A mounts `build_estate_router` in `main.py`; this module only builds the service and its tenant seam.
"""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from assetops_backend.estate.index import EstateIndexService


def build_estate_read(database_url: str | None) -> Any:
    from assetops_backend.actions.composition import build_action_store
    from assetops_backend.analytics.adapters.postgres_assessment_store import SelectionPinRefused
    from assetops_backend.analytics.cold_reads import ColdPinnedLineageUnavailable, ColdReadUnavailable
    from assetops_backend.analytics.composition import (
        build_cold_read_service, build_dispatch_read_service, build_ev_read_service, build_finding_store,
        build_postgres_assessment_store)
    from assetops_backend.analytics.ev_reads import EvPinnedLineageUnavailable, EvReadUnavailable
    from assetops_backend.estate.adapters.postgres_estate_read import PostgresEstateRead
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.evidence.public_provenance import LinkRowsReads
    from assetops_backend.financials.composition import build_consequence_read_service
    from assetops_backend.financials.money_eligibility import MoneyEligibility

    findings = build_finding_store(database_url)
    link_rows = build_link_rows_reader()

    def provenance_reads(c: Any) -> Any:  # set resolution on the estate connection only
        return LinkRowsReads(lambda t, s, ids: list(link_rows(c, t, s, ids)))

    return PostgresEstateRead(
        database_url, findings=findings, assessments=build_postgres_assessment_store(database_url),
        actions=build_action_store(database_url), consequences=build_consequence_read_service(database_url),
        eligibility=MoneyEligibility(build_dispatch_read_service(database_url), findings),
        cold=build_cold_read_service(database_url), ev=build_ev_read_service(database_url),
        provenance_reads=provenance_reads, inconsistent=(ColdPinnedLineageUnavailable, EvPinnedLineageUnavailable, SelectionPinRefused),
        unavailable=(ColdReadUnavailable, EvReadUnavailable))


def build_estate_index_service(database_url: str | None) -> EstateIndexService | None:
    """None without a product database: the router answers 503, never an empty estate."""
    return None if not database_url else EstateIndexService(build_estate_read(database_url))


def registry_tenant(registry: Any) -> Callable[[], UUID | None]:
    """The server's configured tenant from `ImportedSiteRegistry.tenant()`; never a client-supplied ID."""
    def tenant() -> UUID | None:
        found = registry.tenant()
        return None if found is None else found.id
    return tenant
