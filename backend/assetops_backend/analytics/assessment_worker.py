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

`reconcile` schedules windows whose last selected default run used another
model version or a configuration that the current selection no longer gives (a
backdated Foundation or binding publication); every `run_pending` pass runs it
for each assessed Site first.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import ModuleType
from typing import Any, Callable
from uuid import UUID

from assetops_backend.analytics import cold, dispatch_v3
from assetops_backend.analytics.assessment_inputs import (
    BRACKET,
    AnalyticInputSet,
    CohortMember,
    EvidenceQuery,
    EvidenceQueryResult,
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
from assetops_backend.sites.binding_roles import (
    ROLE_SET_MINIGRID_1,
    ROLE_SET_MINIGRID_2,
    ROLE_SET_MINIGRID_3,
    roles_for,
)

DOMAIN = "dispatch"
DAY = timedelta(days=1)
DISPATCH_ROLES = (dispatch_v3.GEN_STATE, dispatch_v3.GEN_POWER, dispatch_v3.LOAD, dispatch_v3.PV_AVAILABLE,
                  dispatch_v3.DISCHARGE, dispatch_v3.SOC)
ROLES_BY_SET = {s: tuple(roles_for(s)) for s in (ROLE_SET_MINIGRID_1, ROLE_SET_MINIGRID_2,
                                                    ROLE_SET_MINIGRID_3)}


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


def input_basis(result: EvidenceQueryResult, model: ModuleType | Any = dispatch_v3) -> tuple[AnalyticInputSet, str]:
    """Cohort selection and the frozen input set of one query result, with its configuration digest.
    The worker assesses it; the phase-3 read compares its `input_sha256` with the selected run."""
    selection = select_cohort(result.readings, result.query.window, result.query.cohort, result.attestations)
    inputs = build_input_set(result, selection, analytic_id=model.ANALYTIC_ID, model_version=model.MODEL_VERSION,
                             roles_by_set=ROLES_BY_SET)
    config = Configuration(result.bindings, result.controls, result.role_sets, result.configuration_limits)
    return inputs, configuration_sha256(config)


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
        inputs, config_sha = input_basis(self.store.query_evidence(query), self.model)
        assessment = self.model.assess(inputs)
        return RunOutput(inputs, assessment, config_sha, watermarks(inputs.readings),
                         "DEFAULT" if cohort is None else "EXPLICIT", started)

    def assess_explicit(self, tenant_id: UUID, site_id: UUID, window: Window,
                        cohort: tuple[CohortMember, ...], knowledge_at: datetime | None = None) -> PersistedRun:
        """An operator's explicit cohort choice for one window (persisted under a cohort-suffixed key)."""
        out = self.compute(tenant_id, site_id, window, knowledge_at or self.clock(), cohort)
        return self.store.record_runs([out], self.clock())[0]

    # -- jobs -------------------------------------------------------------------
    def run_once(self, tenant_id: UUID | None = None, site_id: UUID | None = None) -> JobOutcome | None:
        """Lease and process one due job: the global oldest, or with `tenant_id`/`site_id` that Site's oldest."""
        scope = {} if site_id is None else {"tenant_id": tenant_id, "site_id": site_id}
        lease = self.store.lease_job(DOMAIN, self.clock(), self.lease, max_attempts=self.max_attempts, **scope)
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

    def run_pending(self, limit: int = 1000, *, reconcile: bool = True) -> list[JobOutcome]:
        """Each pass first reconciles every assessed Site, so a backdated Foundation/binding
        publication or a model-version change is enqueued without an operator (phase-2 F4)."""
        if reconcile:
            self.reconcile_all()
        outcomes = []
        for _ in range(limit):
            outcome = self.run_once()
            if outcome is None:
                break
            outcomes.append(outcome)
        return outcomes

    def run_site(self, tenant_id: UUID, site_id: UUID, limit: int) -> list[JobOutcome]:
        """One Site's bounded S3 stage (S4-02d): reconcile this Site (a never-assessed Site has no heads and
        enqueues nothing), then process at most `limit` of its due jobs, leased only from this Site."""
        if limit < 1:
            raise ValueError("A Site stage processes at least one job.")
        self.reconcile(tenant_id, site_id)
        outcomes = []
        for _ in range(limit):
            outcome = self.run_once(tenant_id, site_id)
            if outcome is None:
                break
            outcomes.append(outcome)
        return outcomes

    def reconcile_all(self) -> list[Window]:
        scheduled: list[Window] = []
        for tenant_id, site_id in self.store.assessed_sites(self.model.ANALYTIC_ID):
            scheduled += self.reconcile(tenant_id, site_id)
        return scheduled

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


# --- cold_chain (W2-03) --------------------------------------------------------------------------------------

COLD_DOMAIN = "cold_chain"


@dataclass(frozen=True)
class ColdProjection:
    """One window's projection: per analytic, the persisted run/revision and the episode/Finding revisions."""

    window: Window
    known_at: datetime
    runs: tuple[dict, ...]
    finding_revision_ids: tuple[UUID, ...]


class ColdAssessmentWorker:
    """`cold-excursion/1` and `cold-start-response/1` projection (`.agent/W2-03-build-spec.md` commit 3).

    One SQLAlchemy transaction per job (or explicit request) rechecks the lease, selects the effective
    configuration and S4-05 lineage, computes both analytics, persists their revisions, episodes and Findings and
    completes the job before commit. Any failure rolls all of it back and records a retryable job failure."""

    def __init__(self, store, findings, *, clock: Callable[[], datetime] = utc_now,
                 lease: timedelta = timedelta(minutes=5), max_attempts: int = 3,
                 backoff: timedelta = timedelta(seconds=30)) -> None:
        self.store, self.findings, self.clock = store, findings, clock
        self.lease, self.max_attempts, self.backoff = lease, max_attempts, backoff

    def _project(self, c, tenant_id: UUID, site_id: UUID, window: Window, known_at: datetime, *,
                 job_id: UUID | None, selection: str) -> ColdProjection:
        started = self.clock()
        inputs = self.store.cold_inputs(c, tenant_id, site_id, cold.ColdWindow(window.start, window.end, known_at))
        runs, revisions = [], []
        for assessment in cold.assess_all(inputs):
            now = self.clock()
            persisted = self.store.cold_persist(c, inputs, assessment, job_id=job_id, selection=selection, now=now,
                                                started=started)
            if persisted["created"]:
                episodes = self.store.cold_episodes(c, inputs, assessment, persisted, now)
                revisions += self.findings.cold_apply(c, tenant_id, site_id, assessment.analytic_id, persisted,
                                                      episodes, list(assessment.limitations), now)
            runs.append(persisted)
        return ColdProjection(window, known_at, tuple(runs), tuple(revisions))

    def assess_explicit(self, tenant_id: UUID, site_id: UUID, window: Window,
                        known_at: datetime | None = None) -> ColdProjection:
        """One explicit window at `known_at` (default: the Site's committed disposition watermark), not selected."""
        with self.store.transaction() as c:
            known = known_at or self.store.cold_watermark(c, tenant_id, site_id)
            if known is None:
                raise cold.ColdConfigurationRefused("the Site has no committed disposition to assess")
            return self._project(c, tenant_id, site_id, window, known, job_id=None, selection="EXPLICIT")

    def run_once(self, tenant_id: UUID | None = None, site_id: UUID | None = None) -> JobOutcome | None:
        scope = {} if site_id is None else {"tenant_id": tenant_id, "site_id": site_id}
        lease = self.store.lease_job(COLD_DOMAIN, self.clock(), self.lease, max_attempts=self.max_attempts, **scope)
        if lease is None:
            return None
        try:
            with self.store.transaction() as c:
                self.store.cold_still_mine(c, lease)
                known = self.store.cold_watermark(c, lease.tenant_id, lease.site_id)
                projections = [self._project(c, lease.tenant_id, lease.site_id, w, known, job_id=lease.job_id,
                                             selection="DEFAULT")
                               for w in self.store.cold_windows(c, lease)]
                self.store.cold_complete(c, lease)
            return JobOutcome(lease.job_id, "DONE", tuple(projections))  # type: ignore[arg-type]
        except LeaseLost as lost:
            return JobOutcome(lease.job_id, "LEASE_LOST", error=str(lost))
        except Exception as error:  # noqa: BLE001 - every failure rolls back and is recorded on the job
            reason = f"{type(error).__name__}: {error}"[:500]
            status = self.store.fail_job(lease, reason, self.clock(), max_attempts=self.max_attempts,
                                         backoff=self.backoff)
            return JobOutcome(lease.job_id, status, error=reason)

    def run_pending(self, limit: int = 100, tenant_id: UUID | None = None,
                    site_id: UUID | None = None) -> list[JobOutcome]:
        out: list[JobOutcome] = []
        while len(out) < limit:
            outcome = self.run_once(tenant_id, site_id)
            if outcome is None:
                break
            out.append(outcome)
        return out
