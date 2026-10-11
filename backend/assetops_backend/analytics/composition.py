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
