"""One schedule stage, run in its own killable child process (S4-02d phase 1).

    python -m assetops_backend.scheduling.stages discover|s3|mini|opportunity|s4|consequence '<json arguments>'

The tick (`scheduling/tick.py`) starts each stage as a child with `PGOPTIONS` carrying `statement_timeout` and
`lock_timeout` (S4-02d N2: the existing stores build their own engines and are not edited; libpq applies the
options to every connection the child opens), and kills it when the stage's wall-time bound passes. The child
reaches the database only through the existing writer and store modules, by their compositions. Its last stdout
line is `STAGE_RESULT {json}` with a typed `code`:

- `OK` (discover, s3, mini, opportunity, consequence), `MATCHED` or `SKIPPED_UNCHANGED_FENCE` (s4): the stage did its work.
- `FENCE_MOVED`: the matcher fence moved under every planned attempt; retryable.
- `MATCH_EVIDENCE_NOT_ACCEPTED`: the matcher cited an evidence ID that is not accepted in this Site; the same
  `FindingFenceMoved` type, but deterministic (S4-02d N3), so it is reported apart from a moved fence.
- `TIMEOUT`: a server-side `statement_timeout` or `lock_timeout` fired (SQLSTATE 57014 / 55P03).
- `UNAVAILABLE`: a store reported itself unavailable for another reason.
- `FAILED`: any other error, with its type and message.

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
    "discover": discover, "s3": s3, "mini": mini, "opportunity": opportunity, "s4": s4, "consequence": consequence}


def main(argv: list[str] | None = None) -> int:
    import os

    argv = sys.argv[1:] if argv is None else argv
    stage, args = argv[0], json.loads(argv[1] if len(argv) > 1 else "{}")
    url = os.environ.get("DATABASE_URL")
    try:
        result = STAGES[stage](url, args)
    except Exception as error:  # noqa: BLE001 - every stage failure is typed and reported to the tick
        result = {"code": classify(error), "error": f"{type(error).__name__}: {error}"[:2000]}
    print("STAGE_RESULT " + json.dumps(result, default=str, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
