"""Operator CLI for the S3-01 dispatch recompute worker (DATABASE_URL names the database).

    python -m assetops_backend.analytics.assess_dispatch run-pending
    python -m assetops_backend.analytics.assess_dispatch reconcile --tenant-id T --site-id S
    python -m assetops_backend.analytics.assess_dispatch assess --tenant-id T --site-id S \
        --start 2026-10-05T00:00:00Z --end 2026-10-06T00:00:00Z --cohort GATEWAY:SOURCE:EPOCH ...

Prints one JSON document. `assess` is an explicit cohort choice (persisted under
a cohort-suffixed key); default selection only happens through jobs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from uuid import UUID

from assetops_backend.analytics.assessment_inputs import CohortMember, Window
from assetops_backend.analytics.composition import build_dispatch_assessment_worker


def _instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _run(run) -> dict:
    return {"run_id": str(run.run_id), "created": run.created, "revision_ids": [str(x) for x in run.revision_ids],
            "new_revision_ids": [str(x) for x in run.new_revision_ids]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="assess_dispatch")
    parser.add_argument("command", choices=("run-pending", "reconcile", "assess"))
    parser.add_argument("--tenant-id")
    parser.add_argument("--site-id")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--cohort", nargs="*", default=())
    args = parser.parse_args(argv)
    worker = build_dispatch_assessment_worker(os.environ.get("DATABASE_URL"))
    if args.command == "run-pending":
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


if __name__ == "__main__":
    raise SystemExit(main())
