"""Operator CLI for the S3-01 dispatch recompute worker (DATABASE_URL names the database).

    python -m assetops_backend.analytics.assess_dispatch process-jobs
    python -m assetops_backend.analytics.assess_dispatch reconcile --tenant-id T --site-id S
    python -m assetops_backend.analytics.assess_dispatch assess --tenant-id T --site-id S \
        --start 2026-10-05T00:00:00Z --end 2026-10-06T00:00:00Z --cohort GATEWAY:SOURCE:EPOCH ...
    python -m assetops_backend.analytics.assess_dispatch match-findings --tenant-id T --site-id S
    python -m assetops_backend.analytics.assess_dispatch finding-rows --tenant-id T --site-id S
    python -m assetops_backend.analytics.assess_dispatch requeue --tenant-id T --site-id S --job-id J

Prints one JSON document. `assess` is an explicit cohort choice (persisted under
a cohort-suffixed key); default selection only happens through jobs.
`match-findings` runs the S4-01 `finding-episode-1` matcher over the selected
read; `finding-rows` reloads every stored Finding row of the Site (read-only).
`requeue` is the operator recovery for a terminal FAILED job (S4-02d item 2, N5): after the cause is fixed, it
re-enqueues exactly that job's window of that tenant/Site through `AssessmentStore.enqueue`. The next DEFAULT
selection over the window (by the schedule's S3 stage or `process-jobs`) supersedes the failure; `assess` makes
an EXPLICIT run and is not recovery. It refuses a job that is not a live FAILED dispatch job of that Site (exit 2).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from uuid import UUID

from assetops_backend.analytics.assessment_inputs import CohortMember, Window
from assetops_backend.analytics.composition import (build_dispatch_assessment_worker, build_finding_matcher,
                                                     build_finding_read_service, build_finding_store)


def _instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _run(run) -> dict:
    return {"run_id": str(run.run_id), "created": run.created, "revision_ids": [str(x) for x in run.revision_ids],
            "new_revision_ids": [str(x) for x in run.new_revision_ids]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="assess_dispatch")
    parser.add_argument("command", choices=("process-jobs", "reconcile", "assess", "match-findings", "finding-rows", "requeue",
                                                "finding-reads"))
    parser.add_argument("--tenant-id")
    parser.add_argument("--site-id")
    parser.add_argument("--job-id", help="requeue: the FAILED job whose window is re-enqueued")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--cohort", nargs="*", default=())
    parser.add_argument("--manifest", default=None, help="finding-reads: case manifest for exact-ID annotations")
    args = parser.parse_args(argv)
    if args.command == "requeue" and not (args.tenant_id and args.site_id and args.job_id):
        parser.error("requeue needs --tenant-id, --site-id and --job-id (the FAILED job to re-enqueue)")
    url = os.environ.get("DATABASE_URL")
    if args.command == "match-findings":
        outcome = build_finding_matcher(url).match(UUID(args.tenant_id), UUID(args.site_id))
        json.dump({"planned": outcome.planned, "finding_ids": list(outcome.finding_ids),
                   "revision_ids": list(outcome.revision_ids), "window_statuses": outcome.window_statuses},
                  sys.stdout)
        sys.stdout.write("\n")
        return 0
    if args.command == "finding-rows":
        json.dump(build_finding_store(url).rows(UUID(args.tenant_id), UUID(args.site_id)), sys.stdout, default=str)
        sys.stdout.write("\n")
        return 0
    if args.command == "finding-reads":
        tenant, site = UUID(args.tenant_id), UUID(args.site_id)
        reads = build_finding_read_service(url, args.manifest)
        out = []
        for f in build_finding_store(url).rows(tenant, site)["findings"]:
            body = reads.finding(tenant, site, f["id"])
            out.append({"finding_id": str(f["id"]), "latest_revision_id": str(body["selection"]["latest_revision_id"]),
                        "revision_count": body["revision_page"]["total"], "lifecycle": body["state"]["lifecycle"],
                        "projection": body["state"]["projection"],
                        "recurrence": body["relations"]["recurrence"]["status"],
                        "cited_evidence_count": len(body["revision"]["cited_evidence"]),
                        "annotation_kinds": sorted({a["kind"] for a in body["provenance"]["case_annotations"]})})
        json.dump(out, sys.stdout)
        sys.stdout.write("\n")
        return 0
    worker = build_dispatch_assessment_worker(url)
    if args.command == "requeue":
        return _requeue(worker, UUID(args.tenant_id), UUID(args.site_id), UUID(args.job_id))
    if args.command == "process-jobs":
        out = [{"job_id": str(o.job_id), "status": o.status, "error": o.error, "runs": [_run(r) for r in o.runs]}
               for o in worker.run_pending()]
    elif args.command == "reconcile":
        out = [w.payload() for w in worker.reconcile(UUID(args.tenant_id), UUID(args.site_id))]
    else:
        cohort = tuple(CohortMember(UUID(g), UUID(s), e) for g, s, e in (c.split(":", 2) for c in args.cohort))
        out = _run(worker.assess_explicit(UUID(args.tenant_id), UUID(args.site_id),
                                          Window(_instant(args.start), _instant(args.end)), cohort))
    json.dump(out, sys.stdout)
    sys.stdout.write("\n")
    return 0


def _requeue(worker, tenant_id: UUID, site_id: UUID, job_id: UUID) -> int:
    from assetops_backend.analytics.assessment_worker import DOMAIN

    analytic = worker.model.ANALYTIC_ID
    job = worker.store.job(tenant_id, site_id, job_id, analytic)
    if job is None or job["domain"] != DOMAIN:
        print(f"No dispatch job {job_id} in tenant {tenant_id} Site {site_id}; nothing was requeued.", file=sys.stderr)
        return 2
    if job["status"] != "FAILED" or not job["live"]:
        state = job["status"] if job["status"] != "FAILED" else "FAILED and already superseded"
        print(f"Job {job_id} is {state}, not a live failure; nothing was requeued.", file=sys.stderr)
        return 2
    window = Window(job["window_start"], job["window_end"])
    worker.store.enqueue(tenant_id, site_id, DOMAIN, window, worker.clock())
    pending = [j for j in worker.store.live_jobs(analytic, DOMAIN, tenant_id, site_id)
               if j["status"] == "PENDING" and j["window_start"] < window.end and j["window_end"] > window.start]
    json.dump({"requeued_failed_job_id": str(job_id), "last_error": job["last_error"],
               "window": [window.start.isoformat(), window.end.isoformat()],
               "pending_job_ids": [str(j["id"]) for j in pending]}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
