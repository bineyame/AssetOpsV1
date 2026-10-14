"""Operator entry point for the S4-02d schedule (phase 1: no timer is installed by this slice).

    python -m assetops_backend.scheduling.run tick [--environment default] [--max-sites 20] [--s3-jobs 10]
        [--consequence-items 50]
    python -m assetops_backend.scheduling.run enrol --tenant-id UUID --site-id UUID [--off] --by NAME
    python -m assetops_backend.scheduling.run heads [--environment default]

`tick` runs one bounded environment tick (`scheduling/tick.py`) against `DATABASE_URL` and prints its report as
one JSON line. Exit 0 for COMPLETED, SKIPPED_CLAIMED or RETRY_DUE; 1 when the tick failed or lost its claim, or
when any visited Site stage failed (the failure is in the report and the Site head). Tenants are named by UUID;
there is no development-tenant restriction (S4-02d N5).
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Sequence
from uuid import UUID

from assetops_backend.scheduling.composition import build_schedule_store
from assetops_backend.scheduling.tick import ScheduleTick, StageRunner, TickLimits


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.scheduling.run")
    sub = parser.add_subparsers(dest="command", required=True)
    tick = sub.add_parser("tick")
    tick.add_argument("--max-sites", type=int, default=TickLimits.max_sites)
    tick.add_argument("--s3-jobs", type=int, default=TickLimits.s3_jobs_per_site)
    tick.add_argument("--consequence-items", type=int, default=TickLimits.consequence_items_per_site)
    enrol = sub.add_parser("enrol")
    enrol.add_argument("--tenant-id", type=UUID, required=True)
    enrol.add_argument("--site-id", type=UUID, required=True)
    enrol.add_argument("--off", action="store_true")
    enrol.add_argument("--by", required=True)
    heads = sub.add_parser("heads")
    for p in (tick, heads):
        p.add_argument("--environment", default="default")
    args = parser.parse_args(argv)
    url = os.environ.get("DATABASE_URL")
    if args.command == "enrol":
        print(json.dumps(build_schedule_store(url).enrol(args.tenant_id, args.site_id, not args.off, args.by),
                         default=str))
        return 0
    if args.command == "heads":
        store = build_schedule_store(url)
        print(json.dumps({"tick": store.tick_head(args.environment), "sites": store.site_heads()}, default=str))
        return 0
    limits = TickLimits(max_sites=args.max_sites, s3_jobs_per_site=args.s3_jobs,
                        consequence_items_per_site=args.consequence_items)
    store = build_schedule_store(url, statement_timeout_ms=limits.statement_timeout_ms,
                                 lock_timeout_ms=limits.lock_timeout_ms)
    report = ScheduleTick(store, StageRunner(url, limits), limits, environment=args.environment).tick()
    print(json.dumps(report.as_json()))
    if report.outcome in ("COMPLETED", "SKIPPED_CLAIMED", "RETRY_DUE"):
        return 1 if any(s.result == "FAILED" for s in report.selected) else 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
