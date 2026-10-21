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
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable
from uuid import UUID

from assetops_backend.mini_decisions import projection
from assetops_backend.mini_decisions.store import MiniDecisionWriteRefused
from assetops_backend.mini_depth.inputs import zone

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


class MiniOpportunityWorker:
    """`jobs` is the assessment store (opportunity enqueue/lease/settle/fail); `store` is the mini-decision store
    (snapshot reads and the opportunity inserts)."""

    def __init__(self, jobs: Any, store: Any, *, lease: timedelta = timedelta(minutes=5), max_attempts: int = 3,
                 backoff: timedelta = timedelta(seconds=30),
                 test_lease_clock: Callable[[], datetime] | None = None) -> None:
        self.jobs, self.store = jobs, store
        self.lease, self.max_attempts, self.backoff = lease, max_attempts, backoff
        self._test_clock = test_lease_clock

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
