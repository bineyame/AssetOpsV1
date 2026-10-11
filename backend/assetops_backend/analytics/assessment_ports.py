"""Port for durable dispatch assessment (S3-01 phase 2). Domain types only; no SQL here."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from assetops_backend.analytics.assessment_inputs import (
    AnalyticInputSet,
    ControlValue,
    EvidenceQuery,
    EvidenceQueryResult,
    RoleBinding,
    Window,
)


class AssessmentStoreUnavailable(Exception):
    """The assessment store cannot be read or written."""


class LeaseLost(Exception):
    """The job's lease expired and was taken by another worker; nothing was committed."""


@dataclass(frozen=True)
class JobLease:
    job_id: UUID
    tenant_id: UUID
    site_id: UUID
    domain: str
    window: Window
    attempts: int
    knowledge_cutoff: datetime


@dataclass(frozen=True)
class Configuration:
    """Public configuration selected for a read range at a knowledge cutoff."""

    bindings: tuple[RoleBinding, ...]
    controls: tuple[ControlValue, ...]
    role_sets: tuple[str, ...]
    limits: tuple[str, ...]


@dataclass(frozen=True)
class RunOutput:
    """One window's computation, ready to persist."""

    inputs: AnalyticInputSet
    assessment: Any  # the analytic's WindowAssessment
    configuration_sha256: str
    watermarks: dict[str, str | None]
    selection: str  # DEFAULT | EXPLICIT
    started_at: datetime


@dataclass(frozen=True)
class PersistedRun:
    run_id: UUID
    created: bool
    revision_ids: tuple[UUID, ...]
    new_revision_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class RunHead:
    """The latest default-selection run of a window (for configuration/model reconciliation)."""

    window: Window
    model_version: str
    configuration_sha256: str


class AssessmentStore(Protocol):
    def query_evidence(self, query: EvidenceQuery) -> EvidenceQueryResult: ...

    def configuration(self, tenant_id: UUID, site_id: UUID, read_range: Window,
                      knowledge_at: datetime) -> Configuration: ...

    def lease_job(self, domain: str, now: datetime, lease: timedelta) -> JobLease | None: ...

    def complete_job(self, lease: JobLease, outputs: list[RunOutput], now: datetime) -> list[PersistedRun]:
        """Persist every run and mark the job DONE in ONE commit, only while the lease is still ours."""
        ...

    def fail_job(self, lease: JobLease, error: str, now: datetime, *, max_attempts: int,
                 backoff: timedelta) -> str: ...

    def record_runs(self, outputs: list[RunOutput], now: datetime) -> list[PersistedRun]:
        """Persist explicitly requested runs (no job)."""
        ...

    def run_heads(self, tenant_id: UUID, site_id: UUID, analytic_id: str) -> list[RunHead]: ...

    def enqueue(self, tenant_id: UUID, site_id: UUID, domain: str, window: Window, now: datetime) -> None: ...
