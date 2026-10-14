"""The single composition module for the assessment store.

The one place allowed to import `assetops_backend.analytics.adapters.*`.
"""

from __future__ import annotations

from assetops_backend.analytics.adapters.json_assessment_store import JsonAssessmentStore
from assetops_backend.analytics.adapters.memory_assessment_store import MemoryAssessmentStore
from assetops_backend.analytics.ports import AssessmentStore


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

    return FindingReadService(build_finding_store(database_url),
                              build_dispatch_read_service(database_url, demo_manifest_path))


def finding_store_unavailable() -> tuple[type, ...]:
    from assetops_backend.analytics.adapters.postgres_finding_store import FindingStoreUnavailable

    return (FindingStoreUnavailable,)


def build_postgres_assessment_store(database_url: str | None):
    """The S3 assessment writer itself (job leasing, live-job and job reads) for the S4-02d schedule stages."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    return PostgresAssessmentStore(database_url)


def finding_fence_moved_type() -> type:
    """`FindingFenceMoved`, for a caller that classifies a failed match without importing the adapter."""
    from assetops_backend.analytics.adapters.postgres_finding_store import FindingFenceMoved
    return FindingFenceMoved
