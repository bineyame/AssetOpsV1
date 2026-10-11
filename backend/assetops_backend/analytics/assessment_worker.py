"""Dispatch recompute worker (S3-01 phase 2).

Leases the S2 `dispatch` recompute jobs, expands each job's source-time window
by the continuity bracket to the UTC-day assessment windows it can affect
(the affected window and its continuity neighbours), assesses each window at
the lease's knowledge cutoff through the typed seam, and commits every run,
revision and the job completion together. A failure releases the job for a
retry with back-off; after `max_attempts` the job is FAILED with its reason.

An acceptance that arrives while a job is leased cannot widen that job (S2
coalesces only into PENDING jobs), so it creates a new PENDING job: the next
pass reassesses with the new evidence and nothing is lost.

`reconcile` schedules windows whose latest default run used another model
version or a configuration that the current selection no longer gives (a
backdated Foundation or binding publication).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import ModuleType
from typing import Any, Callable
from uuid import UUID

from assetops_backend.analytics import dispatch_v3
from assetops_backend.analytics.assessment_inputs import (
    BRACKET,
    CohortMember,
    EvidenceQuery,
    Window,
    build_input_set,
    sha256_json,
    watermarks,
)
from assetops_backend.analytics.assessment_ports import (
    AssessmentStore,
    Configuration,
    JobLease,
    LeaseLost,
    PersistedRun,
    RunOutput,
)
from assetops_backend.analytics.cohort import select_cohort
from assetops_backend.sites.binding_roles import ROLE_SET_MINIGRID_1, ROLE_SET_MINIGRID_2, roles_for

DOMAIN = "dispatch"
DAY = timedelta(days=1)
DISPATCH_ROLES = (dispatch_v3.GEN_STATE, dispatch_v3.GEN_POWER, dispatch_v3.LOAD, dispatch_v3.PV_AVAILABLE,
                  dispatch_v3.DISCHARGE, dispatch_v3.SOC)
ROLES_BY_SET = {s: tuple(roles_for(s)) for s in (ROLE_SET_MINIGRID_1, ROLE_SET_MINIGRID_2)}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def day_windows(start: datetime, end: datetime, bracket: timedelta = BRACKET) -> list[Window]:
    """UTC-day windows intersecting `[start - bracket, end + bracket)`."""
    lo = (start - bracket).astimezone(timezone.utc)
    day = lo.replace(hour=0, minute=0, second=0, microsecond=0)
    out = []
    while day < end + bracket:
        out.append(Window(day, day + DAY))
        day += DAY
    return out


def configuration_sha256(config: Configuration) -> str:
    return sha256_json({
        "controls": sorted((c.payload() for c in config.controls), key=lambda p: sha256_json(p)),
        "bindings": sorted([b.role, str(b.asset_id), str(b.valid_from), str(b.valid_to),
                            str(b.binding_revision_id), b.role_set] for b in config.bindings),
        "role_sets": sorted(config.role_sets), "limits": sorted(config.limits),
    })


@dataclass(frozen=True)
class JobOutcome:
    job_id: UUID
    status: str  # DONE | RETRY | FAILED | LEASE_LOST
    runs: tuple[PersistedRun, ...] = ()
    error: str | None = None


class DispatchAssessmentWorker:
    def __init__(self, store: AssessmentStore, *, model: ModuleType | Any = dispatch_v3,
                 clock: Callable[[], datetime] = utc_now, lease: timedelta = timedelta(minutes=5),
                 max_attempts: int = 3, backoff: timedelta = timedelta(seconds=30)) -> None:
        self.store, self.model, self.clock = store, model, clock
        self.lease, self.max_attempts, self.backoff = lease, max_attempts, backoff

    # -- one window -------------------------------------------------------------
    def compute(self, tenant_id: UUID, site_id: UUID, window: Window, knowledge_at: datetime,
                cohort: tuple[CohortMember, ...] | None = None) -> RunOutput:
        started = self.clock()
        query = EvidenceQuery(tenant_id, site_id, DOMAIN, window, knowledge_at, cohort=cohort, roles=DISPATCH_ROLES)
        result = self.store.query_evidence(query)
        selection = select_cohort(result.readings, window, query.cohort)
        inputs = build_input_set(result, selection, analytic_id=self.model.ANALYTIC_ID,
                                 model_version=self.model.MODEL_VERSION, roles_by_set=ROLES_BY_SET)
        assessment = self.model.assess(inputs)
        config = Configuration(result.bindings, result.controls, result.role_sets, result.configuration_limits)
        return RunOutput(inputs, assessment, configuration_sha256(config), watermarks(inputs.readings),
                         "DEFAULT" if cohort is None else "EXPLICIT", started)

    def assess_explicit(self, tenant_id: UUID, site_id: UUID, window: Window,
                        cohort: tuple[CohortMember, ...], knowledge_at: datetime | None = None) -> PersistedRun:
        """An operator's explicit cohort choice for one window (persisted under a cohort-suffixed key)."""
        out = self.compute(tenant_id, site_id, window, knowledge_at or self.clock(), cohort)
        return self.store.record_runs([out], self.clock())[0]

    # -- jobs -------------------------------------------------------------------
    def run_once(self) -> JobOutcome | None:
        lease = self.store.lease_job(DOMAIN, self.clock(), self.lease, max_attempts=self.max_attempts)
        if lease is None:
            return None
        try:
            computed = [self.compute(lease.tenant_id, lease.site_id, w, lease.knowledge_cutoff)
                        for w in day_windows(lease.window.start, lease.window.end)]
            # A neighbour with no accepted reading in it has nothing to assess (evidence is
            # append-only, so it never had a run either); it stays UNASSESSED.
            outputs = [o for o in computed if o.inputs.cohort.status != "EMPTY"]
            runs = self.store.complete_job(lease, outputs, self.clock())
            return JobOutcome(lease.job_id, "DONE", tuple(runs))
        except LeaseLost as lost:
            return JobOutcome(lease.job_id, "LEASE_LOST", error=str(lost))
        except Exception as error:  # noqa: BLE001 - every failure is recorded on the job and retried
            reason = f"{type(error).__name__}: {error}"[:500]
            status = self.store.fail_job(lease, reason, self.clock(), max_attempts=self.max_attempts,
                                         backoff=self.backoff)
            return JobOutcome(lease.job_id, status, error=reason)

    def run_pending(self, limit: int = 1000) -> list[JobOutcome]:
        outcomes = []
        for _ in range(limit):
            outcome = self.run_once()
            if outcome is None:
                break
            outcomes.append(outcome)
        return outcomes

    def reconcile(self, tenant_id: UUID, site_id: UUID) -> list[Window]:
        """Enqueue windows whose latest default run used another model version or a configuration
        the current selection no longer gives (backdated Foundation/binding publication)."""
        now = self.clock()
        scheduled = []
        for head in self.store.run_heads(tenant_id, site_id, self.model.ANALYTIC_ID):
            stale = head.model_version != self.model.MODEL_VERSION
            if not stale:
                config = self.store.configuration(tenant_id, site_id, head.window.widened(BRACKET), now)
                stale = configuration_sha256(config) != head.configuration_sha256
            if stale:
                self.store.enqueue(tenant_id, site_id, DOMAIN, head.window, now)
                scheduled.append(head.window)
        return scheduled
