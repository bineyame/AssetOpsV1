"""One schedule stage, run in its own killable child process (S4-02d phase 1).

    python -m assetops_backend.scheduling.stages <stage> '<json arguments>'

<stage>: discover|s3|cold_assess|ev_assess|mini|opportunity|s4|chain_threads|consequence|cold_consequence|ev_consequence

The tick (`scheduling/tick.py`) starts each stage as a child with `PGOPTIONS` carrying `statement_timeout` and
`lock_timeout` (S4-02d N2: the existing stores build their own engines and are not edited; libpq applies the
options to every connection the child opens), and kills it when the stage's wall-time bound passes. The child
reaches the database only through the existing writer and store modules, by their compositions. Its last stdout
line is `STAGE_RESULT {json}` with a typed `code`:

- `OK` (discover, s3, cold_assess, ev_assess, mini, opportunity, consequence, cold_consequence, ev_consequence),
  `MATCHED` or `SKIPPED_UNCHANGED_FENCE` (s4): the stage did its work.
- `FENCE_MOVED`: the matcher fence moved under every planned attempt; retryable.
- `MATCH_EVIDENCE_NOT_ACCEPTED`: the matcher cited an evidence ID that is not accepted in this Site; the same
  `FindingFenceMoved` type, but deterministic (S4-02d N3), so it is reported apart from a moved fence.
- `TIMEOUT`: a server-side `statement_timeout` or `lock_timeout` fired (SQLSTATE 57014 / 55P03).
- `UNAVAILABLE`: a store reported itself unavailable for another reason.
- `FAILED`: any other error, with its type and message.
- `CONSEQUENCE_CLAIMED` (cold_consequence, ev_consequence): another runner holds that domain's Site claim.

FIX-COLD-DRAIN: `cold_assess`/`ev_assess` lease this Site's `cold_chain`/`ev_charging` assessment jobs at DB time,
and `cold_consequence`/`ev_consequence` drain this Site's cold/EV consequence work at the DB time the tick passes,
each through its existing worker (job lease, retries and back-off, per-item locks and replay stay the workers').

The S4 stage runs the matcher only when the Site has no completed pass for the current `MATCHER_VERSION` in the
schedule head, or its current matcher fence differs from the fence recorded at that pass (packet item 1, N1);
otherwise it appends nothing.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, replace
from datetime import datetime
from typing import Any, Callable
from uuid import UUID

_TIMEOUT_SQLSTATES = {"57014", "55P03"}


def _chain(error: BaseException):
    seen: set[int] = set()
    stack: list[BaseException | None] = [error]
    while stack:
        e = stack.pop()
        if e is None or id(e) in seen:
            continue
        seen.add(id(e))
        yield e
        stack += [e.__cause__, e.__context__, getattr(e, "orig", None)]


def classify(error: BaseException) -> str:
    for e in _chain(error):
        state = getattr(e, "sqlstate", None) or getattr(e, "pgcode", None)
        if state in _TIMEOUT_SQLSTATES or type(e).__name__ in {"QueryCanceled", "LockNotAvailable"}:
            return "TIMEOUT"
    if any(type(e).__name__.endswith("Unavailable") for e in _chain(error)):
        return "UNAVAILABLE"
    return "FAILED"


def db_clock(url: str | None) -> Callable[[], datetime]:
    """A clock that reads the database's `clock_timestamp()` on every call (S4-02d phase 2, I3), through the
    schedule store's read; the stores' application-clock defaults are not used by scheduled stages."""
    from assetops_backend.scheduling.composition import build_schedule_store

    def clock() -> datetime:
        store = build_schedule_store(url)
        try:
            return store.db_now()
        finally:
            store.dispose()

    return clock


def _uuid(value: Any) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def discover(url: str, args: dict[str, Any]) -> dict[str, Any]:
    """Global `reconcile_all()` (measured, never omitted), then the persisted Site inventory, live S3 jobs, live
    four-domain mini jobs (W4-02 q7 ruling 2) and pending consequence work of every tenant. Selection is applied by
    the tick."""
    from assetops_backend.analytics import dispatch_v3
    from assetops_backend.analytics.assessment_worker import DOMAIN
    from assetops_backend.analytics.composition import (
        build_dispatch_assessment_worker,
        build_postgres_assessment_store,
    )
    from assetops_backend.financials.composition import build_consequence_store
    from assetops_backend.scheduling.composition import build_schedule_store

    started = time.perf_counter()
    reconciled = build_dispatch_assessment_worker(url, clock=db_clock(url)).reconcile_all()  # I3: DB time
    reconcile_ms = int((time.perf_counter() - started) * 1000)
    inventory = build_schedule_store(url).site_inventory()
    assessments = build_postgres_assessment_store(url)
    live = assessments.live_jobs(dispatch_v3.ANALYTIC_ID, DOMAIN)
    live_mini = assessments.live_mini_jobs()
    live_opportunity = assessments.live_opportunity_jobs()  # W4-03: opportunity work keeps a Site scheduled
    pending = build_consequence_store(url).pending_work_sites()
    return {"code": "OK", "reconcile_ms": reconcile_ms, "reconciled_windows": len(reconciled),
            "inventory": inventory, "live_jobs": live, "live_mini_jobs": live_mini,
            "live_opportunity_jobs": live_opportunity, "pending_work_sites": pending}


def s3(url: str, args: dict[str, Any]) -> dict[str, Any]:
    """This Site's bounded S3 stage: reconcile it, then process at most `limit` of its due jobs."""
    from assetops_backend.analytics import dispatch_v3
    from assetops_backend.analytics.assessment_worker import DOMAIN
    from assetops_backend.analytics.composition import (
        build_dispatch_assessment_worker,
        build_postgres_assessment_store,
    )

    tenant_id, site_id = _uuid(args["tenant_id"]), _uuid(args["site_id"])
    # S4-02d phase 2 (I3): the S3 lease expiry, knowledge cutoff and job timestamps take DB time, not this host's.
    outcomes = build_dispatch_assessment_worker(url, clock=db_clock(url)).run_site(
        tenant_id, site_id, int(args["limit"]))
    live = build_postgres_assessment_store(url).live_jobs(dispatch_v3.ANALYTIC_ID, DOMAIN, tenant_id, site_id)
    return {"code": "OK", "processed": len(outcomes),
            "outcomes": [{"job_id": o.job_id, "status": o.status, "runs": len(o.runs), "error": o.error}
                         for o in outcomes],
            "deferred": sum(1 for j in live if j["status"] in ("PENDING", "LEASED")),
            "live_jobs": [{k: j[k] for k in ("id", "status", "window_start", "window_end", "attempts",
                                              "lease_until", "last_error")} for j in live]}


MINI_JOB_LEASE_SECONDS = 300  # MiniDepthWorker's five-minute lease; the MINI stage bound must stay below it.


def mini(url: str, args: dict[str, Any]) -> dict[str, Any]:
    """This Site's bounded mini-depth stage (W4-02 closure 4 S7, q7 rulings 1-3): at most `limit` due jobs of the
    four `mini_*` domains of this Site only, leased at DB time by `MiniDepthWorker`. `processed` counts the jobs
    this stage leased, `failed` those it left FAILED, `deferred` this Site's mini jobs still PENDING or LEASED."""
    from datetime import timedelta

    from assetops_backend.analytics.composition import build_postgres_assessment_store
    from assetops_backend.mini_depth.worker import build_worker

    tenant_id, site_id = _uuid(args["tenant_id"]), _uuid(args["site_id"])
    worker = build_worker(url, lease=timedelta(seconds=MINI_JOB_LEASE_SECONDS))
    try:
        outcomes = worker.run_pending(int(args["limit"]), tenant_id, site_id)
    finally:
        worker.store.dispose()
    live = build_postgres_assessment_store(url).live_mini_jobs(tenant_id, site_id)
    return {"code": "OK", "processed": len(outcomes),
            "failed": sum(1 for o in outcomes if o.status == "FAILED"),
            "deferred": sum(1 for j in live if j["status"] in ("PENDING", "LEASED")),
            "outcomes": [o.as_json() for o in outcomes],
            "live_jobs": [{k: j[k] for k in ("id", "domain", "status", "window_start", "window_end", "attempts",
                                              "lease_until", "last_error")} for j in live]}


def s4(url: str, args: dict[str, Any]) -> dict[str, Any]:
    from assetops_backend.analytics import dispatch_v3
    from assetops_backend.analytics.composition import (
        build_finding_matcher,
        build_finding_store,
        finding_fence_moved_type,
    )
    from assetops_backend.analytics.finding_episode import MATCHER_VERSION

    tenant_id, site_id = _uuid(args["tenant_id"]), _uuid(args["site_id"])
    current = asdict(build_finding_store(url).fence(tenant_id, site_id, dispatch_v3.ANALYTIC_ID))
    if args.get("matched_version") == MATCHER_VERSION and args.get("matched_fence") == current:
        return {"code": "SKIPPED_UNCHANGED_FENCE", "fence": current, "version": MATCHER_VERSION}
    fence_moved = finding_fence_moved_type()
    matcher = build_finding_matcher(url)
    matcher.now = db_clock(url)  # I3: the matcher's `now` (revision instants) is DB time
    try:
        out = matcher.match(tenant_id, site_id)
    except fence_moved as moved:
        deterministic = "not accepted" in str(moved)
        return {"code": "MATCH_EVIDENCE_NOT_ACCEPTED" if deterministic else "FENCE_MOVED",
                "error": f"{type(moved).__name__}: {moved}", "fence_before": current}
    # The pass applied under `out.fence`; its own appended revisions are the only change it made to the fence,
    # so the completed fence is that fence plus them. Re-reading instead could absorb a concurrent change the
    # pass never saw and skip the match it needs.
    completed = asdict(replace(out.fence, finding_revisions=out.fence.finding_revisions + len(out.revision_ids)))
    return {"code": "MATCHED", "fence": completed, "version": MATCHER_VERSION, "planned": out.planned,
            "finding_ids": list(out.finding_ids), "revision_ids": list(out.revision_ids),
            "window_statuses": out.window_statuses,
            "deferred_windows": [d.isoformat() for d in out.deferred_windows]}


def chain_threads(url: str, args: dict[str, Any]) -> dict[str, Any]:
    """CH-2 (build sheet §4, live path until CH-1b's outbox): this Site's backfill steps (b) and (c), placing its new
    Finding and opportunity revisions on their threads and linking its unlinked Actions, then CH-3's step (d), the
    lifecycle run (the fallback until CH-1b's `consume('lifecycle')`; it also runs the time-based causes).
    Idempotent."""
    from assetops_backend.chain.backfill import run_threads
    from assetops_backend.chain.composition import build_thread_sources, build_thread_store

    reader, store = build_thread_sources(url), build_thread_store(url)
    try:
        steps = run_threads(reader, store, _uuid(args["tenant_id"]), _uuid(args["site_id"]), ("b", "c", "d"),
                            created_by="tick")
    finally:
        _dispose(reader, store)
    return {"code": "OK", "processed": sum(int(s["written"]) for s in steps), "steps": steps}


def consequence(url: str, args: dict[str, Any]) -> dict[str, Any]:
    """This Site's bounded consequence drain, by IDs (never the one-off CLI), at the DB time the tick passes."""
    from assetops_backend.financials.composition import build_recompute_worker

    tenant_id, site_id = _uuid(args["tenant_id"]), _uuid(args["site_id"])
    report = build_recompute_worker(url).run(tenant_id, site_id, int(args["limit"]),
                                              now=datetime.fromisoformat(args["now"]))
    counts = report.counts()
    return {"code": "OK" if report.claimed else "CONSEQUENCE_CLAIMED", "claimed": report.claimed,
            "now": report.now, **counts,
            "outcomes": [{"work_id": o.work_id, "cause": o.cause, "succeeded": o.succeeded,
                          "attempt_no": o.attempt_no, "no_op_reason": o.no_op_reason, "error_code": o.error_code}
                         for o in report.outcomes]}


# The cold and EV assessment workers' five-minute lease; their stage bound stays below it.
DOMAIN_JOB_LEASE_SECONDS = 300


def _dispose(*holders: Any) -> None:
    for holder in holders:
        closer = getattr(holder, "dispose", None) or getattr(getattr(holder, "_engine", None), "dispose", None)
        if closer is not None:
            closer()


def _domain_assess(url: str, args: dict[str, Any], domain: str) -> dict[str, Any]:
    """This Site's bounded cold or EV assessment stage: at most `limit` due jobs of the domain, leased at DB time
    by the domain's worker. `processed` counts the jobs leased, `failed` those left FAILED, `deferred` this Site's
    jobs of the domain still PENDING or LEASED."""
    from datetime import timedelta

    from assetops_backend.analytics import cold, ev
    from assetops_backend.analytics.assessment_worker import COLD_DOMAIN, EV_DOMAIN
    from assetops_backend.analytics.composition import (
        build_cold_assessment_worker,
        build_ev_assessment_worker,
        build_postgres_assessment_store,
    )

    build, analytic, job_domain = {"cold": (build_cold_assessment_worker, cold.EXCURSION_ANALYTIC, COLD_DOMAIN),
                                   "ev": (build_ev_assessment_worker, ev.SESSION_ANALYTIC, EV_DOMAIN)}[domain]
    tenant_id, site_id = _uuid(args["tenant_id"]), _uuid(args["site_id"])
    worker = build(url, clock=db_clock(url), lease=timedelta(seconds=DOMAIN_JOB_LEASE_SECONDS))
    try:
        outcomes = worker.run_pending(int(args["limit"]), tenant_id, site_id)
    finally:
        _dispose(worker.store, worker.findings)
    store = build_postgres_assessment_store(url)
    try:
        live = store.live_jobs(analytic, job_domain, tenant_id, site_id)
    finally:
        _dispose(store)
    return {"code": "OK", "processed": len(outcomes),
            "failed": sum(1 for o in outcomes if o.status == "FAILED"),
            "deferred": sum(1 for j in live if j["status"] in ("PENDING", "LEASED")),
            "outcomes": [{"job_id": o.job_id, "status": o.status, "runs": len(o.runs), "error": o.error}
                         for o in outcomes],
            "live_jobs": [{k: j[k] for k in ("id", "status", "window_start", "window_end", "attempts",
                                              "lease_until", "last_error")} for j in live]}


def cold_assess(url: str, args: dict[str, Any]) -> dict[str, Any]:
    return _domain_assess(url, args, "cold")


def ev_assess(url: str, args: dict[str, Any]) -> dict[str, Any]:
    return _domain_assess(url, args, "ev")


def _domain_consequence(url: str, args: dict[str, Any], domain: str) -> dict[str, Any]:
    """This Site's bounded cold or EV consequence drain, by IDs, at the DB time the tick passes, in the
    `consequence` stage's shape (the counts are computed here; the workers are unchanged)."""
    from assetops_backend.financials.composition import build_cold_consequence_worker, build_ev_consequence_worker

    build = {"cold": build_cold_consequence_worker, "ev": build_ev_consequence_worker}[domain]
    tenant_id, site_id = _uuid(args["tenant_id"]), _uuid(args["site_id"])
    worker = build(url)
    try:
        report = worker.run(tenant_id, site_id, int(args["limit"]), now=datetime.fromisoformat(args["now"]))
    finally:
        _dispose(worker._store)
    o = report.outcomes
    if domain == "cold":
        appended = sum(len(x.appended) for x in o)
        replayed = sum(len(x.replayed) for x in o)
    else:
        appended = sum(1 for x in o if x.succeeded and x.consequence_revision_id is not None and not x.replayed)
        replayed = sum(1 for x in o if x.succeeded and x.replayed)
    return {"code": "OK" if report.claimed else "CONSEQUENCE_CLAIMED", "claimed": report.claimed,
            "now": report.now, "selected": len(o), "appended": appended, "replayed": replayed,
            "failed": sum(1 for x in o if not x.succeeded), "deferred": report.deferred, "backlog": report.backlog,
            "outcomes": [{"work_id": x.work_id, "succeeded": x.succeeded, "attempt_no": x.attempt_no,
                          "error_code": x.error_code} for x in o]}


def cold_consequence(url: str, args: dict[str, Any]) -> dict[str, Any]:
    return _domain_consequence(url, args, "cold")


def ev_consequence(url: str, args: dict[str, Any]) -> dict[str, Any]:
    return _domain_consequence(url, args, "ev")


OPPORTUNITY_JOB_LEASE_SECONDS = 300  # MiniOpportunityWorker's five-minute lease; the stage bound stays below it.


def opportunity(url: str, args: dict[str, Any]) -> dict[str, Any]:
    """This Site's bounded W4-03 OPPORTUNITY stage (closure 4 S1, u3 unit-4 dry-read): the worker's scan of this
    Site's committed renewable heads, then at most `limit` due `mini_opportunity` jobs of this Site, leased at DB
    time. `processed` counts the jobs leased, `failed` those left FAILED, `deferred` this Site's opportunity jobs
    still PENDING or LEASED after the loop."""
    from datetime import timedelta

    from assetops_backend.analytics.composition import build_postgres_assessment_store
    from assetops_backend.mini_decisions.worker import build_worker

    tenant_id, site_id = _uuid(args["tenant_id"]), _uuid(args["site_id"])
    worker = build_worker(url, lease=timedelta(seconds=OPPORTUNITY_JOB_LEASE_SECONDS))
    try:
        outcomes = worker.run_pending(int(args["limit"]), tenant_id, site_id)
    finally:
        worker.store.dispose()
    live = build_postgres_assessment_store(url).live_opportunity_jobs(tenant_id, site_id)
    return {"code": "OK", "processed": len(outcomes),
            "failed": sum(1 for o in outcomes if o.status == "FAILED"),
            "deferred": len(live),
            "outcomes": [o.as_json() for o in outcomes],
            "live_jobs": [{k: j[k] for k in ("id", "status", "window_start", "window_end", "attempts",
                                              "lease_until", "last_error")} for j in live]}


STAGES: dict[str, Callable[[str, dict[str, Any]], dict[str, Any]]] = {
    "discover": discover, "s3": s3, "cold_assess": cold_assess, "ev_assess": ev_assess, "mini": mini,
    "opportunity": opportunity, "s4": s4, "chain_threads": chain_threads, "consequence": consequence,
    "cold_consequence": cold_consequence, "ev_consequence": ev_consequence}


def _peak_rss_kb() -> int | None:
    """CH-0 U3: this stage child's peak resident memory in kB (POSIX `ru_maxrss`; Windows `PeakWorkingSetSize`).
    Any failure gives None; it never raises and never changes a stage result's other keys."""
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            class _Counters(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

            counters = _Counters()
            counters.cb = ctypes.sizeof(_Counters)
            kernel32 = ctypes.WinDLL("kernel32")
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            query = kernel32.K32GetProcessMemoryInfo
            query.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Counters), wintypes.DWORD]
            query.restype = wintypes.BOOL
            if not query(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
                return None
            return int(counters.PeakWorkingSetSize // 1024)
        import resource

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(peak // 1024) if sys.platform == "darwin" else int(peak)  # macOS reports bytes, Linux kB
    except Exception:  # noqa: BLE001 - memory reporting never fails a stage
        return None


def main(argv: list[str] | None = None) -> int:
    import os

    argv = sys.argv[1:] if argv is None else argv
    stage, args = argv[0], json.loads(argv[1] if len(argv) > 1 else "{}")
    url = os.environ.get("DATABASE_URL")
    try:
        result = STAGES[stage](url, args)
    except Exception as error:  # noqa: BLE001 - every stage failure is typed and reported to the tick
        result = {"code": classify(error), "error": f"{type(error).__name__}: {error}"[:2000]}
    if isinstance(result, dict):
        result["peak_rss_kb"] = _peak_rss_kb()
    print("STAGE_RESULT " + json.dumps(result, default=str, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
