"""Composition for the work domain: the only module that imports its adapter (W4-01 commit 2).

Callers receive the `WorkService` over `PostgresWorkStore`, whose provenance reads use the evidence ledger's
caller-connection link-row reader (the shared W3 `PublicProvenance` contract; no second DTO).
"""

from __future__ import annotations

from typing import Callable
from uuid import UUID, uuid4

from assetops_backend.evidence.composition import build_link_rows_reader
from assetops_backend.work.adapters.postgres_domain_action_index import PostgresDomainActionRead
from assetops_backend.work.adapters.postgres_domain_intent import PostgresDomainIntentStore
from assetops_backend.work.adapters.postgres_global_read import PostgresGlobalWorkRead
from assetops_backend.work.adapters.postgres_work_read import LinkReadPorts, PostgresWorkRead, _ReadTx
from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
from assetops_backend.work.detail import WorkDetailService
from assetops_backend.work.domain_action_index import DomainActionReadService
from assetops_backend.work.domain_intent import DomainIntentService
from assetops_backend.work.global_detail import GlobalWorkDetailService
from assetops_backend.work.global_index import GlobalWorkIndexService
from assetops_backend.work.site_index import WorkIndexService
from assetops_backend.work.model import WorkStoreUnavailable
from assetops_backend.work.service import WorkService

__all__ = ["WORK_UNAVAILABLE", "build_domain_action_read", "build_domain_action_read_service",
           "build_domain_intent_service", "build_domain_intent_store",
           "build_global_work_detail_service", "build_global_work_index_service", "build_global_work_read",
           "build_work_detail_service", "build_work_index_service", "build_work_read", "build_work_service",
           "build_work_store"]

WORK_UNAVAILABLE = WorkStoreUnavailable


def build_work_store(database_url: str | None) -> PostgresWorkStore:
    return PostgresWorkStore(database_url, link_rows=build_link_rows_reader())


def build_work_service(database_url: str | None, *, new_id: Callable[[], UUID] = uuid4) -> WorkService:
    return WorkService(build_work_store(database_url), new_id=new_id)


def _link_read_ports() -> LinkReadPorts:
    """Run 3 ruling 6: the one shared cold/EV `_snapshot` owner and the W3 q5 at-cutoff mini-grid reads, each bound
    to no connection of its own (every call takes the work read's connection)."""
    from assetops_backend.actions.composition import build_action_store
    from assetops_backend.analytics import cold, ev
    from assetops_backend.analytics.composition import (build_cold_ev_selection_pins, build_cold_read_service,
                                                        build_ev_read_service, build_finding_store,
                                                        build_postgres_assessment_store)

    selected_windows_on, pin_refused = build_cold_ev_selection_pins()
    cold_read = build_cold_read_service(None)
    ev_read = build_ev_read_service(None)

    return LinkReadPorts(
        cold_snapshot=cold_read._snapshot, cold_envelope=cold_read.envelope_on,
        ev_snapshot=ev_read._snapshot, ev_sessions=ev_read.sessions_on, ev_findings=ev_read.findings_on,
        ev_selected_provenance=ev_read.selected_provenance_on,
        selected_windows=selected_windows_on, pin_refused=(pin_refused,),
        dispatch_days=build_postgres_assessment_store(None).select_dispatch_days_on,
        finding_index=build_finding_store(None).index_snapshot_on,
        cold_analytics=(cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC), ev_analytics=(ev.SESSION_ANALYTIC,),
        action_window=build_action_store(None).site_window_on)


def build_work_read(database_url: str | None) -> PostgresWorkRead:
    return PostgresWorkRead(database_url, link_rows=build_link_rows_reader(), ports=_link_read_ports())


def build_work_detail_service(database_url: str | None) -> WorkDetailService:
    return WorkDetailService(build_work_read(database_url))


def build_work_index_service(database_url: str | None) -> WorkIndexService:
    """W4-01 commit 4: the Site Incident/Maintenance lists over the same work read adapter."""
    return WorkIndexService(build_work_read(database_url))


def build_global_work_read(database_url: str | None) -> PostgresGlobalWorkRead:
    """W6-01a: the cross-Site read over the W4 per-Site selection reads, on one snapshot connection."""
    return PostgresGlobalWorkRead(database_url, link_rows=build_link_rows_reader(), ports=_link_read_ports())


def build_global_work_index_service(database_url: str | None) -> GlobalWorkIndexService | None:
    """W6-01a: None without a product database; the router answers 503, never an empty list."""
    return None if not database_url else GlobalWorkIndexService(build_global_work_read(database_url))


def selected_finding_pin(ports: LinkReadPorts):
    """W5-02a K1a (ruling A3): the W4 linked-selection pin of one Finding revision at a cutoff, on the caller's
    connection - the exact selection W4 links use (`_ReadTx._pin`), not a second selection implementation."""

    def pin_of(c, tenant_id, site_id, site_code, revision, known_at):
        return _ReadTx(c, tenant_id, site_id, site_code, known_at, None, ports)._pin(revision, None, None, known_at)

    return pin_of


def selected_ev_basis(ports: LinkReadPorts):
    """W5-04a V1a (readiness rulings 5, 6, 9): the selected EV basis of one valid EV Finding pin on the caller's
    connection. The pin's exact run window, evidence cutoff and selection seqs re-select `EvReadService._snapshot`
    at `known_at`; then, on the same snapshot, the exact SUPPORTED Finding revision (`findings_on`; its
    `source_provenance.evidence_ids` is the citation set), the selected public sessions (`ev_session.id` root ->
    selected `ev_session_revision.id`) and the selected assessment head's evidence IDs. Returns None when the pin no
    longer selects; an EV read outage is the work store's 503, never an empty success. No validation here: the
    command/read service decides membership and refuses without intersecting."""
    from assetops_backend.analytics.ev_reads import EvReadUnavailable

    def basis_of(c, tenant_id, site_id, site_code, pin, known_at, finding_revision_id):
        if ports.ev_findings is None or ports.ev_sessions is None:
            raise WorkStoreUnavailable("The domain Action store has no selected EV basis reader.")
        try:
            snap = ports.ev_snapshot(c, tenant_id, site_id, site_code, pin["window_start"], pin["window_end"],
                                     pin["evidence_cutoff"], selection_cutoff=known_at,
                                     selection_seqs=dict(pin["selection_seqs"]))
            if snap["selected"] is None:
                return None
            finding = next((f for f in ports.ev_findings(c, snap)
                            if str(f["revision_id"]) == str(finding_revision_id)), None)
            sessions = {str(r["session_id"]): str(r["revision_id"]) for r in ports.ev_sessions(c, snap)}
        except ports.pin_refused:
            return None
        except EvReadUnavailable as error:
            raise WorkStoreUnavailable(f"The selected EV read is unavailable: {error}") from error
        return {"state": snap["state"], "window_start": snap["lo"], "window_end": snap["hi"],
                "assessment_revision_id": str(snap["selected"]["revision_id"]),
                "finding": None if finding is None else {
                    "finding_id": str(finding["finding_id"]), "revision_id": str(finding["revision_id"]),
                    "session_id": None if finding.get("session_id") is None else str(finding["session_id"]),
                    "lifecycle": finding["lifecycle"],
                    "evidence_ids": sorted(str(e).lower() for e in finding["source_provenance"]["evidence_ids"])},
                "sessions": sessions,
                "selected_evidence_ids": sorted(str(e).lower() for e in snap["selected"]["evidence_ids"])}

    return basis_of


def build_domain_intent_store(database_url: str | None) -> PostgresDomainIntentStore:
    return PostgresDomainIntentStore(database_url, pin_of=selected_finding_pin(_link_read_ports()))


def build_domain_intent_service(database_url: str | None, *,
                                new_id: Callable[[], UUID] = uuid4) -> DomainIntentService:
    """W5-02a K1a: the domain Action commands over their sole writer."""
    return DomainIntentService(build_domain_intent_store(database_url), new_id=new_id)


def selected_cold_envelope(ports: LinkReadPorts):
    """W5-02a ruling B1: the selected cold envelope of one valid Finding pin on the caller's connection - the
    pin's exact window, evidence cutoff and selection seqs through `ColdReadService._snapshot`, then `envelope_on`.
    A cold read outage is the work read's 503, never an empty success."""
    from assetops_backend.analytics.cold_reads import ColdReadUnavailable

    def envelope_of(c, tenant_id, site_id, site_code, pin, known_at):
        if ports.cold_envelope is None:
            raise WorkStoreUnavailable("The domain Action read has no selected cold envelope reader.")
        try:
            snap = ports.cold_snapshot(c, tenant_id, site_id, site_code, pin["window_start"], pin["window_end"],
                                       pin["evidence_cutoff"], selection_cutoff=known_at,
                                       selection_seqs=dict(pin["selection_seqs"]))
            return ports.cold_envelope(c, snap, ports.cold_analytics)
        except ColdReadUnavailable as error:
            raise WorkStoreUnavailable(f"The selected cold read is unavailable: {error}") from error

    return envelope_of


def build_domain_action_read(database_url: str | None) -> PostgresDomainActionRead:
    ports = _link_read_ports()
    return PostgresDomainActionRead(database_url, link_rows=build_link_rows_reader(),
                                    pin_of=selected_finding_pin(ports), envelope_of=selected_cold_envelope(ports),
                                    action_window=ports.action_window)


def build_domain_action_read_service(database_url: str | None) -> DomainActionReadService | None:
    """W5-02a K1b: the domain Action detail and Site Action union index; None without a product database (503)."""
    return None if not database_url else DomainActionReadService(build_domain_action_read(database_url))


def build_global_work_detail_service(database_url: str | None) -> GlobalWorkDetailService | None:
    """W6-01c: the exact request detail on the global read; None without a product database (503)."""
    return None if not database_url else GlobalWorkDetailService(build_global_work_read(database_url))
