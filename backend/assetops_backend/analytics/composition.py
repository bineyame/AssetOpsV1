"""The single composition module for the assessment store.

The one place allowed to import `assetops_backend.analytics.adapters.*`.
"""

from __future__ import annotations

from assetops_backend.analytics.adapters.json_assessment_store import JsonAssessmentStore
from assetops_backend.analytics.adapters.memory_assessment_store import MemoryAssessmentStore
from assetops_backend.analytics.ports import AssessmentStore


def selection_pin_refused() -> type[LookupError]:
    """The exact-pin refusal the estate adapter treats as an inconsistent selection (c2 r1 L1); composition-only
    access to the adapter's class."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import SelectionPinRefused

    return SelectionPinRefused


def build_assessment_store(persistent: bool = True) -> AssessmentStore:
    """Choose the adapter that persists assessment history.

    `persistent=False` is for a composition that injected its own evidence
    store: its assessments must not land in the shared `var/assessments`.
    """
    return JsonAssessmentStore() if persistent else MemoryAssessmentStore()


def build_dispatch_assessment_worker(database_url: str | None, **options):
    """The S3-01 dispatch recompute worker over the PostgreSQL assessment store."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker

    return DispatchAssessmentWorker(PostgresAssessmentStore(database_url), **options)


def build_dispatch_read_service(database_url: str | None, demo_manifest_path: str | None = None):
    """The S3-01 phase-3 selected-window/interval read over the PostgreSQL assessment store.
    `demo_manifest_path` (env `ASSETOPS_DEMO_FIXTURE_MANIFEST`) only annotates exact matching IDs."""
    from assetops_backend.analytics.adapters.demo_manifest_file import DemoManifestAnnotations
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.dispatch_read import DispatchReadService

    return DispatchReadService(PostgresAssessmentStore(database_url),
                               annotations=DemoManifestAnnotations(demo_manifest_path))


def build_claim_limit_read_service(database_url: str | None):
    """S3-02a: selected-assessment capability and claim-limit read over the PostgreSQL assessment store."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.claim_limit_read import ClaimLimitReadService

    return ClaimLimitReadService(PostgresAssessmentStore(database_url))


def build_lineage_reader(database_url: str | None):
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore

    return PostgresAssessmentStore(database_url)


def build_finding_store(database_url: str | None):
    """The S4-01 Finding store (append-only; the only Finding writer)."""
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore

    return PostgresFindingStore(database_url)


def build_finding_matcher(database_url: str | None):
    """The S4-01 `finding-episode-1` matcher over the selected dispatch read and the Finding store."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.adapters.postgres_finding_store import FindingFenceMoved
    from assetops_backend.analytics.finding_service import FindingMatcher

    return FindingMatcher(PostgresAssessmentStore(database_url), build_finding_store(database_url),
                          fence_moved=FindingFenceMoved)


def build_finding_read_service(database_url: str | None, demo_manifest_path: str | None = None):
    """The S4-01 phase-2 exact Finding root/revision read over the Finding store and the S3 dispatch read.
    `demo_manifest_path` only annotates exact matching evidence IDs (fixture or gateway case labels)."""
    from assetops_backend.analytics.finding_read import FindingReadService

    from assetops_backend.evidence.composition import build_public_provenance

    return FindingReadService(build_finding_store(database_url),
                              build_dispatch_read_service(database_url, demo_manifest_path),
                              build_public_provenance(database_url))


def build_finding_index_service(database_url: str | None, demo_manifest_path: str | None = None):
    """The S4-04 Site Finding index read over the Finding store and the S3 dispatch read (read-only)."""
    from assetops_backend.analytics.finding_index import FindingIndexService

    return FindingIndexService(build_finding_store(database_url),
                               build_dispatch_read_service(database_url, demo_manifest_path))


def finding_store_unavailable() -> tuple[type, ...]:
    from assetops_backend.analytics.adapters.postgres_finding_store import FindingStoreUnavailable

    return (FindingStoreUnavailable,)


def build_postgres_assessment_store(database_url: str | None):
    """The S3 assessment writer itself (job leasing, live-job and job reads) for the S4-02d schedule stages."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.evidence.composition import build_link_rows_reader
    return PostgresAssessmentStore(database_url, link_rows=build_link_rows_reader())


def build_cold_assessment_worker(database_url: str | None):
    """W2-03: the cold worker over the assessment and Finding stores (one shared transaction per job)."""
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
    from assetops_backend.analytics.assessment_worker import ColdAssessmentWorker
    return ColdAssessmentWorker(build_postgres_assessment_store(database_url), PostgresFindingStore(database_url))



def build_ev_assessment_worker(database_url: str | None):
    """W2-06 Q13: the EV worker over the assessment and Finding stores (one shared transaction per job)."""
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
    from assetops_backend.analytics.assessment_worker import EvAssessmentWorker
    return EvAssessmentWorker(build_postgres_assessment_store(database_url), PostgresFindingStore(database_url))

def finding_fence_moved_type() -> type:
    """`FindingFenceMoved`, for a caller that classifies a failed match without importing the adapter."""
    from assetops_backend.analytics.adapters.postgres_finding_store import FindingFenceMoved
    return FindingFenceMoved


def build_cold_read_service(database_url: str):
    """W2-03: the selected cold temperature, backup-chain and cold Finding read (read-only Postgres adapter)."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import ColdReadService

    from assetops_backend.evidence.composition import build_link_rows_reader

    return ColdReadService(database_url, link_rows=build_link_rows_reader())


def build_ev_selected_snapshot(link_rows):
    """W2-07: W2-06's exact selected EV snapshot on a caller's connection at the committed cutoff, for the EV money
    worker (`EvReadService._snapshot` with no requested `known_at`)."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import EvReadService

    reads = EvReadService(link_rows=link_rows)
    return lambda c, tenant_id, site_id, lo, hi: reads._snapshot(c, tenant_id, site_id, "", lo, hi, None)


def build_ev_read_service(database_url: str):
    """W2-06 commit 4: the selected EV session and Finding read (read-only Postgres adapter)."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import EvReadService
    from assetops_backend.evidence.composition import build_link_rows_reader

    return EvReadService(database_url, link_rows=build_link_rows_reader())


def build_cold_ev_selection_pins():
    """W4-01 Run 3 ruling 6: the shared W3 exact-window selection helper (`selected_windows_on`, caller's
    connection) and its pin refusal type, for a pinned cold/EV `_snapshot` caller outside analytics."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import SelectionPinRefused, selected_windows_on

    return selected_windows_on, SelectionPinRefused
