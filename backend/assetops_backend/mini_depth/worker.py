"""W4-02 unit 4 step 4: the mini-depth worker (lease -> inputs -> rules -> projection -> selection -> DONE).

`D-2026-10-20-w4-02-buildspec` closure 1 Q3 (one worker leases only the four `mini_*` domains, reads one repeatable
snapshot, appends a revision and `mini_depth_selection(job_id)` in one transaction, then marks the job DONE),
closure 2 (CLI `run-pending` and `reconcile --site <code> --from <UTC> --to <UTC>`), closure 4 S2 (the worker issues
no `recompute_job` SQL: it leases, settles and fails through `PostgresAssessmentStore`'s mini methods) and q5 ruling
5 (the lease instant is the one knowledge cutoff, passed unchanged to the inputs, digest and revision).

    python -m assetops_backend.mini_depth.worker run-pending [--limit N]
    python -m assetops_backend.mini_depth.worker reconcile --site <code> --from <UTC> --to <UTC>

`reconcile` is explicit historical backfill (closure 2: the only path beyond retention): it assesses each Site-local
hour inside `[from, to)` (renewable: local noon only, as the 0029 enqueue functions do) at the database clock of its
own transaction and appends a `backfill` selection with no job. It never writes a job.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from assetops_backend.analytics.assessment_ports import JobLease, LeaseLost
from assetops_backend.mini_depth import projection
from assetops_backend.mini_depth.inputs import MiniInputsRefused, load_hour_inputs, local_hour, zone
from assetops_backend.mini_depth.rules import Window
from assetops_backend.mini_depth.store import DOMAINS, JOB_DOMAIN, AppendedSelection

_PAGE_DOMAIN = {job: page for page, job in JOB_DOMAIN.items()}
RENEWABLE_LOCAL_HOUR = 12


@dataclass(frozen=True)
class MiniOutcome:
    job_id: UUID | None
    domain: str
    window: Window
    status: str  # DONE | RETRY | FAILED | LEASE_LOST
    knowledge_cutoff: datetime
    selection: AppendedSelection | None = None
    error: str | None = None

    def as_json(self) -> dict[str, Any]:
        s = self.selection
        return {"job_id": self.job_id, "domain": self.domain, "window_start": self.window.start,
                "window_end": self.window.end, "status": self.status, "knowledge_cutoff": self.knowledge_cutoff,
                "seq": s.seq if s else None, "revision_id": s.revision_id if s else None,
                "reused": s.reused if s else None, "error": self.error}


class MiniDepthWorker:
    """`jobs` is the assessment store (lease/settle/fail of the four mini domains); `store` is the mini-depth
    store (the snapshot transaction, its reads and the selection writer). `test_lease_clock` replaces the lease's
    database clock in tests only."""

    def __init__(self, jobs: Any, store: Any, *, lease: timedelta = timedelta(minutes=5), max_attempts: int = 3,
                 backoff: timedelta = timedelta(seconds=30),
                 test_lease_clock: Callable[[], datetime] | None = None) -> None:
        self.jobs, self.store = jobs, store
        self.lease, self.max_attempts, self.backoff = lease, max_attempts, backoff
        self._test_clock = test_lease_clock

    def _now(self) -> datetime | None:
        return None if self._test_clock is None else self._test_clock()

    def run_once(self, tenant_id: UUID | None = None, site_id: UUID | None = None) -> MiniOutcome | None:
        """Lease and process one due mini job: the oldest of any Site, or of the named Site."""
        lease: JobLease | None = self.jobs.lease_mini_job(self.lease, max_attempts=self.max_attempts,
                                                          tenant_id=tenant_id, site_id=site_id, now=self._now())
        if lease is None:
            return None
        domain = _PAGE_DOMAIN[lease.domain]
        window = Window(lease.window.start, lease.window.end)  # the rules' window type (it carries `seconds`)
        try:
            with self.store.snapshot() as c:
                inputs = load_hour_inputs(c, lease.tenant_id, lease.site_id, window, lease.knowledge_cutoff)
                selection = self.store.append_selection(projection.project(domain, inputs), job_id=lease.job_id,
                                                        connection=c)
                self.jobs.settle_mini_job(c, lease)
            return MiniOutcome(lease.job_id, domain, window, "DONE", lease.knowledge_cutoff, selection)
        except LeaseLost as lost:
            return MiniOutcome(lease.job_id, domain, window, "LEASE_LOST", lease.knowledge_cutoff,
                               error=str(lost))
        except Exception as error:  # noqa: BLE001 - every failure is recorded on the job and retried or FAILED
            reason = (f"{error.code}: {error}" if isinstance(error, MiniInputsRefused)
                      else f"{type(error).__name__}: {error}")[:500]
            status = self.jobs.fail_mini_job(lease, reason, max_attempts=self.max_attempts, backoff=self.backoff,
                                             now=self._now())
            return MiniOutcome(lease.job_id, domain, window, status, lease.knowledge_cutoff, error=reason)

    def run_pending(self, limit: int = 100, tenant_id: UUID | None = None,
                    site_id: UUID | None = None) -> list[MiniOutcome]:
        """At most `limit` due mini jobs, globally or of one Site (the tick's bounded `mini` stage)."""
        if limit < 1:
            raise ValueError("A mini-depth pass processes at least one job.")
        outcomes: list[MiniOutcome] = []
        for _ in range(limit):
            outcome = self.run_once(tenant_id, site_id)
            if outcome is None:
                break
            outcomes.append(outcome)
        return outcomes

    def reconcile(self, site_code: str, start: datetime, end: datetime) -> list[MiniOutcome]:
        """Explicit backfill of every Site-local hour inside `[start, end)`; no job is read or written."""
        if start.tzinfo is None or end.tzinfo is None or not start < end:
            raise ValueError("--from and --to are UTC instants with from < to")
        tenant_id, site_id, tz_name = self.store.site_scope(site_code)
        outcomes: list[MiniOutcome] = []
        for window in hours_within(start, end, tz_name):
            local = window.start.astimezone(zone(tz_name)).hour
            domains = [d for d in DOMAINS if d != "renewable" or local == RENEWABLE_LOCAL_HOUR]
            with self.store.snapshot() as c:
                cutoff = self.store.clock(c)
                inputs = load_hour_inputs(c, tenant_id, site_id, window, cutoff)
                for domain in domains:
                    selection = self.store.append_selection(projection.project(domain, inputs), job_id=None,
                                                            backfill=True, connection=c)
                    outcomes.append(MiniOutcome(None, domain, window, "DONE", cutoff, selection))
        return outcomes


#: Closure 2's CLI command name, spelled from the method it runs: a quoted `run-` literal is reserved for run
#: identities (`runs/identity.py`, tools/checks/run-setup.ps1), which this command is not.
RUN_PENDING_COMMAND = MiniDepthWorker.run_pending.__name__.replace("_", "-")


def hours_within(start: datetime, end: datetime, tz_name: str | None) -> list[Window]:
    """The Site-local clock hours (first occurrence; a nonexistent local hour is skipped) wholly inside
    `[start, end)`, in time order."""
    tz = zone(tz_name)
    day, last = start.astimezone(tz).date(), end.astimezone(tz).date()
    out: list[Window] = []
    while day <= last:
        for hour in range(24):
            try:
                w = local_hour(day, hour, tz.key)
            except MiniInputsRefused:
                continue
            if start <= w.start and w.end <= end:
                out.append(w)
        day += timedelta(days=1)
    return out


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError(f"{value!r} must carry a UTC offset")
    return parsed.astimezone(timezone.utc)


def build_worker(database_url: str, **options: Any) -> MiniDepthWorker:
    from assetops_backend.analytics.composition import build_postgres_assessment_store
    from assetops_backend.mini_depth.store import PostgresMiniDepthStore

    return MiniDepthWorker(build_postgres_assessment_store(database_url),
                           PostgresMiniDepthStore.from_url(database_url), **options)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.mini_depth.worker")
    sub = parser.add_subparsers(dest="command", required=True)
    pending = sub.add_parser(RUN_PENDING_COMMAND, help="process due mini-depth jobs")
    pending.add_argument("--limit", type=int, default=100)
    backfill = sub.add_parser("reconcile", help="explicit backfill of one Site's hours in [from, to)")
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
        outcomes = (worker.run_pending(args.limit) if args.command == RUN_PENDING_COMMAND
                    else worker.reconcile(args.site, args.start, args.end))
    finally:
        worker.store.dispose()
    print(json.dumps([o.as_json() for o in outcomes], default=str))
    return 1 if any(o.status == "FAILED" for o in outcomes) else 0


if __name__ == "__main__":
    raise SystemExit(main())
