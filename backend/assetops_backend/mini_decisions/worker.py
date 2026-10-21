"""W4-03 unit 4: the five-day opportunity worker (`.agent/W4-03-build-spec.md` closure 2 Q4, closure 4 S1/S2/S5/S6,
u3 "Unit 4 dry-read").

    python -m assetops_backend.mini_decisions.worker run-pending [--limit N]
    python -m assetops_backend.mini_decisions.worker reconcile --site <code> --from <UTC> --to <UTC>

`run-pending` first scans committed W4-02 renewable noon heads (`enqueue_from_selections`): every selected noon whose
UTC instant is `>= :at - interval '5 days'` (`:at` one DB `clock_timestamp()`, or the assessment store's test-only
`test_clock_override`) ends one five-day study. A study is queued only when it has no projected revision yet or its
physical identity (S5 `input_sha256`) differs from the latest projected one, so a same-revision reselection queues
nothing. `reconcile` enumerates the complete five-day studies wholly inside `[from, to)` beyond that bound with the
same rule. Queueing, leasing, settling and failing go through `PostgresAssessmentStore`'s opportunity methods: this
module issues no `recompute_job` SQL.

The lease loop (u4) projects one leased study in one write transaction under the study-key advisory lock: it checks
the job's tenant/Site/domain and exact Site-local midnight window and the five selected noon heads before any insert,
builds the frozen `mini-opportunity/1` result, reuses an existing revision with the same `input_sha256`, appends a
selection only when the head revision changes, links the union of the selected accepted IDs, and marks the job DONE
on that same transaction. Any refusal or integrity error fails the job (retry or FAILED) and writes no history.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID, uuid4

from assetops_backend.analytics.assessment_ports import JobLease, LeaseLost
from assetops_backend.mini_decisions import projection
from assetops_backend.mini_decisions.store import (
    OPPORTUNITY_JOB_DOMAIN,
    OPPORTUNITY_MODEL_VERSION,
    MiniDecisionWriteRefused,
)
from assetops_backend.mini_depth.inputs import zone

RUN_PENDING_COMMAND = "run-pending"
#: Closure 1 Q2: the producer of every opportunity SERVICE projection.
PRODUCER_ID = OPPORTUNITY_MODEL_VERSION

#: Closure 4 S6: the routine scan's rolling bound on the selected noon UTC instant (the 0029 bound).
SCAN_BOUND = timedelta(days=5)

@dataclass(frozen=True)
class Study:
    tenant_id: UUID
    site_id: UUID
    tz_name: str | None
    first_day: date
    last_day: date


@dataclass(frozen=True)
class Queued:
    """One study the scan or reconcile found changed: `action` is INSERTED or COALESCED."""
    study: Study
    action: str
    job_id: UUID
    input_sha256: str


@dataclass(frozen=True)
class Projected:
    """What one settled job wrote: the root, the revision (`reused` when its digest already existed) and the new
    selection seq (None when the head was already that revision)."""
    opportunity_id: UUID
    revision_id: UUID
    reused: bool
    selection_seq: int | None
    input_sha256: str
    status: str


@dataclass(frozen=True)
class OpportunityOutcome:
    job_id: UUID
    status: str  # DONE | RETRY | FAILED | LEASE_LOST
    first_day: date | None = None
    last_day: date | None = None
    projected: Projected | None = None
    error: str | None = None

    def as_json(self) -> dict[str, Any]:
        p = self.projected
        return {"job_id": self.job_id, "status": self.status, "first_day": self.first_day,
                "last_day": self.last_day, "opportunity_id": p.opportunity_id if p else None,
                "revision_id": p.revision_id if p else None, "reused": p.reused if p else None,
                "seq": p.selection_seq if p else None, "result_status": p.status if p else None,
                "error": self.error}


class MiniOpportunityWorker:
    """`jobs` is the assessment store (opportunity enqueue/lease/settle/fail); `store` is the mini-decision store
    (snapshot reads and the opportunity inserts); `reader` is W4-02's `MiniDepthRead`, whose `provenance_blocks`
    classifies the selected five-day accepted set. `test_lease_clock` replaces the lease's DB clock in tests only."""

    def __init__(self, jobs: Any, store: Any, reader: Any = None, *, lease: timedelta = timedelta(minutes=5),
                 max_attempts: int = 3, backoff: timedelta = timedelta(seconds=30),
                 test_lease_clock: Callable[[], datetime] | None = None) -> None:
        self.jobs, self.store, self.reader = jobs, store, reader
        self.lease, self.max_attempts, self.backoff = lease, max_attempts, backoff
        self._test_clock = test_lease_clock

    def _now(self) -> datetime | None:
        return None if self._test_clock is None else self._test_clock()

    # --- scan and reconcile ---------------------------------------------------------------------------------------

    def _scan_at(self, c: Any) -> datetime:
        override = getattr(self.jobs, "test_clock_override", None)
        return override() if override is not None else self.store.db_now(c)

    def _changed(self, c: Any, study: Study) -> str | None:
        """The study's current S5 hash when it differs from its latest projected revision (or none exists)."""
        heads = projection.day_heads(self.store, c, study.tenant_id, study.site_id, study.tz_name,
                                     projection.study_days(study.last_day))
        sha = projection.input_sha256(study.tenant_id, study.site_id, study.first_day, study.last_day, heads)
        latest = self.store.latest_opportunity_sha(c, study.tenant_id, study.site_id, study.first_day,
                                                   study.last_day)
        return None if latest == sha else sha

    def _queue(self, c: Any, studies: list[Study]) -> list[Queued]:
        changed = [(s, sha) for s in studies if (sha := self._changed(c, s)) is not None]
        out = []
        for study, sha in changed:
            window = projection.study_window(study.first_day, study.last_day, study.tz_name)
            action, job_id = self.jobs.enqueue_opportunity_job(study.tenant_id, study.site_id, study.first_day,
                                                               study.last_day, window)
            out.append(Queued(study, action, job_id, sha))
        return out

    def enqueue_from_selections(self, tenant_id: UUID | None = None, site_id: UUID | None = None) -> list[Queued]:
        """Closure 2 Q4 / closure 4 S6: queue every changed study ending on a retained selected noon day, of every
        Site or of one Site. Each queue is its own advisory-locked transaction in the assessment store."""
        if (tenant_id is None) != (site_id is None):
            raise ValueError("A Site-scoped scan names both the tenant and the Site.")
        with self.store.snapshot() as c:
            at = self._scan_at(c)
            rows = self.store.renewable_scan_heads(c, at - SCAN_BOUND, tenant_id, site_id)
            studies = []
            for r in rows:
                last = r.window_start.astimezone(zone(r.timezone)).date()
                studies.append(Study(r.tenant_id, r.site_id, r.timezone, last - timedelta(days=4), last))
            studies = sorted(set(studies), key=lambda s: (str(s.tenant_id), str(s.site_id), s.last_day))
            return self._queue(c, studies)

    def reconcile(self, site_code: str, start: datetime, end: datetime) -> list[Queued]:
        """Explicit historical backfill: every complete five-day study whose job window lies inside `[start, end)`,
        queued by the same changed-identity and lock/coalesce rule. It never changes the routine bound."""
        if start.tzinfo is None or end.tzinfo is None or not start < end:
            raise ValueError("--from and --to are UTC instants with from < to")
        with self.store.snapshot() as c:
            rows = self.store.sites_by_code(c, site_code)
            if len(rows) != 1:
                raise MiniDecisionWriteRefused(f"Site code {site_code!r} names {len(rows)} Sites, not exactly one")
            tenant_id, site_id, tz_name = rows[0]
            tz = zone(tz_name)
            studies = []
            last = start.astimezone(tz).date() + timedelta(days=4)
            while last <= end.astimezone(tz).date():
                first = last - timedelta(days=4)
                window = projection.study_window(first, last, tz_name)
                if start <= window.start and window.end <= end:
                    studies.append(Study(tenant_id, site_id, tz_name, first, last))
                last += timedelta(days=1)
            return self._queue(c, studies)

    # --- lease loop and projection (u4) -----------------------------------------------------------------------------

    def _classification(self, c: Any, lease: JobLease, heads: list[projection.DayHead]) -> str | None:
        present = [h for h in heads if h.mini_revision_id is not None]
        if not present:
            return None
        if self.reader is None:
            raise projection.ProjectionIntegrityError("No provenance reader is configured for the projection")
        blocks = self.reader.provenance_blocks(
            c, tenant_id=lease.tenant_id, site_id=lease.site_id,
            selected_revision_ids=[h.mini_revision_id for h in present],
            selected_evidence_ids=[i for h in present for i in h.evidence_ids], pending_evidence_ids=None)
        selected = blocks.get("selected_source_provenance") or {}
        return selected.get("classification")

    def _project(self, c: Any, lease: JobLease) -> tuple[date, date, Projected]:
        site = self.store.site_timezone(c, lease.tenant_id, lease.site_id)
        if site is None:
            raise MiniDecisionWriteRefused(f"Recompute job {lease.job_id} names no known Site")
        tz_name = site[0]
        first = lease.window.start.astimezone(zone(tz_name)).date()
        last = first + timedelta(days=projection.STUDY_DAYS - 1)
        window = projection.study_window(first, last, tz_name)
        if lease.domain != OPPORTUNITY_JOB_DOMAIN or (lease.window.start, lease.window.end) != (window.start,
                                                                                              window.end):
            raise MiniDecisionWriteRefused(
                f"Recompute job {lease.job_id} is not one exact five-day {OPPORTUNITY_JOB_DOMAIN} study window")
        bounds = (window.start, window.end)
        self.store.lock_study(c, lease.tenant_id, lease.site_id, first, last)
        heads = projection.day_heads(self.store, c, lease.tenant_id, lease.site_id, tz_name,
                                     projection.study_days(last))
        result = projection.frozen_result(heads, self._classification(c, lease, heads))
        sha = projection.input_sha256(lease.tenant_id, lease.site_id, first, last, heads)
        opportunity_id = self.store.opportunity_root(c, lease.tenant_id, lease.site_id, first, last)
        if opportunity_id is None:
            opportunity_id = uuid4()
            self.store.insert_opportunity(c, {"id": opportunity_id, "tenant_id": lease.tenant_id,
                                              "site_id": lease.site_id, "first_day": first, "last_day": last,
                                              "model_version": OPPORTUNITY_MODEL_VERSION})
        same, head, top = self.store.opportunity_state(c, lease.tenant_id, lease.site_id, opportunity_id, sha)
        revision_id, reused = same, same is not None
        if revision_id is None:
            revision_id = uuid4()
            self.store.insert_opportunity_revision(c, {
                "id": revision_id, "tenant_id": lease.tenant_id, "site_id": lease.site_id,
                "opportunity_id": opportunity_id, "revision_no": top + 1,
                "selected_hours": projection.selected_hours(heads), "result": result, "input_sha256": sha,
                "producer_id": PRODUCER_ID, "source_job_id": lease.job_id,
                "model_version": OPPORTUNITY_MODEL_VERSION}, study_window=bounds)
            for evidence_id in sorted({i for h in heads for i in h.evidence_ids}):
                self.store.insert_opportunity_evidence(c, {"tenant_id": lease.tenant_id, "site_id": lease.site_id,
                                                           "opportunity_revision_id": revision_id,
                                                           "evidence_id": evidence_id})
        seq = None
        if head != revision_id:
            seq = self.store.insert_opportunity_selection(c, {
                "tenant_id": lease.tenant_id, "site_id": lease.site_id, "opportunity_id": opportunity_id,
                "revision_id": revision_id, "job_id": lease.job_id}, study_window=bounds)
        return first, last, Projected(opportunity_id, revision_id, reused, seq, sha, result["status"])

    def run_once(self, tenant_id: UUID | None = None, site_id: UUID | None = None) -> OpportunityOutcome | None:
        """Lease and project one due opportunity job: the oldest of any Site, or of the named Site."""
        lease: JobLease | None = self.jobs.lease_opportunity_job(self.lease, max_attempts=self.max_attempts,
                                                                 tenant_id=tenant_id, site_id=site_id,
                                                                 now=self._now())
        if lease is None:
            return None
        try:
            with self.store.transaction() as c:
                first, last, projected = self._project(c, lease)
                self.jobs.settle_opportunity_job(c, lease)
            return OpportunityOutcome(lease.job_id, "DONE", first, last, projected)
        except LeaseLost as lost:
            return OpportunityOutcome(lease.job_id, "LEASE_LOST", error=str(lost))
        except Exception as error:  # noqa: BLE001 - every failure is recorded on the job and retried or FAILED
            reason = f"{type(error).__name__}: {error}"[:500]
            status = self.jobs.fail_opportunity_job(lease, reason, max_attempts=self.max_attempts,
                                                    backoff=self.backoff, now=self._now())
            return OpportunityOutcome(lease.job_id, status, error=reason)

    def run_pending(self, limit: int = 100, tenant_id: UUID | None = None,
                    site_id: UUID | None = None, *, scan: bool = True) -> list[OpportunityOutcome]:
        """Closure 2 Q4: scan committed renewable heads first (globally or for one Site), then lease at most
        `limit` due opportunity jobs (the tick's bounded OPPORTUNITY stage)."""
        if limit < 1:
            raise ValueError("An opportunity pass processes at least one job.")
        if scan:
            self.enqueue_from_selections(tenant_id, site_id)
        outcomes: list[OpportunityOutcome] = []
        for _ in range(limit):
            outcome = self.run_once(tenant_id, site_id)
            if outcome is None:
                break
            outcomes.append(outcome)
        return outcomes


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError(f"{value!r} must carry a UTC offset")
    return parsed.astimezone(timezone.utc)


def build_worker(database_url: str, **options: Any) -> MiniOpportunityWorker:
    from assetops_backend.analytics.composition import build_postgres_assessment_store
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
    from assetops_backend.mini_depth.read import MiniDepthRead

    return MiniOpportunityWorker(build_postgres_assessment_store(database_url),
                                 PostgresMiniDecisionStore.from_url(database_url),
                                 MiniDepthRead.from_url(database_url, build_link_rows_reader()), **options)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.mini_decisions.worker")
    sub = parser.add_subparsers(dest="command", required=True)
    pending = sub.add_parser(RUN_PENDING_COMMAND, help="scan selected renewable heads, then project due studies")
    pending.add_argument("--limit", type=int, default=100)
    backfill = sub.add_parser("reconcile", help="queue one Site's complete five-day studies in [from, to)")
    backfill.add_argument("--site", required=True)
    backfill.add_argument("--from", dest="start", required=True, type=_utc)
    backfill.add_argument("--to", dest="end", required=True, type=_utc)
    args = parser.parse_args(argv)
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2
    worker = build_worker(url)
    try:
        if args.command == RUN_PENDING_COMMAND:
            outcomes = worker.run_pending(args.limit)
            print(json.dumps([o.as_json() for o in outcomes], default=str))
            return 1 if any(o.status == "FAILED" for o in outcomes) else 0
        queued = worker.reconcile(args.site, args.start, args.end)
        print(json.dumps([{"first_day": q.study.first_day, "last_day": q.study.last_day, "action": q.action,
                           "job_id": q.job_id, "input_sha256": q.input_sha256} for q in queued], default=str))
        return 0
    finally:
        worker.store.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
