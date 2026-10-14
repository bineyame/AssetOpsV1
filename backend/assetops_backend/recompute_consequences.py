"""Server-side recompute of `fuel-cost-1` consequences (S4-02b phase 2a).

    python -m assetops_backend.recompute_consequences run --site KOBO-001 [--limit N]
    python -m assetops_backend.recompute_consequences pending --site KOBO-001

`run` drains the Site's durable dirty work (migration 0011 triggers) through
`financials.recompute.ConsequenceRecomputeWorker` and prints one JSON line per work item: appended and
replayed consequence revision IDs, or the typed error a FAILED attempt recorded. A failed item stays pending
and the next `run` retries it. Exit code 0 when every processed item succeeded, 1 when any failed, 2 for an
unknown Site. `pending` lists the work still pending with its attempt count and last error.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.financials.composition import (
    CONSEQUENCE_UNAVAILABLE,
    build_assumption_store,
    build_consequence_store,
    build_recompute_worker,
)


def main(argv: Sequence[str] | None = None, *, worker=None, store=None, prices=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.recompute_consequences")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--limit", type=int)
    pending = sub.add_parser("pending")
    for p in (run, pending):
        p.add_argument("--site", required=True)
        p.add_argument("--tenant", default=DEVELOPMENT_TENANT_SLUG)
    args = parser.parse_args(argv)
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    url = database_url()
    prices = build_assumption_store(url) if prices is None else prices
    try:
        scope = prices.site_scope(args.tenant, args.site)
        if scope is None:
            print(f"No imported Site {args.site!r} in tenant {args.tenant!r}; nothing was recomputed.",
                  file=sys.stderr)
            return 2
        code, tenant_id, site_id = scope
        if args.command == "pending":
            store = build_consequence_store(url) if store is None else store
            for w in store.pending_work(tenant_id, site_id):
                print(json.dumps({"site_code": code, "work_id": str(w["id"]), "cause": w["cause"],
                                  "attempts": w["attempts"]}))
            return 0
        worker = build_recompute_worker(url) if worker is None else worker
        failed = 0
        for out in worker.run_pending(tenant_id, site_id, args.limit):
            failed += 0 if out.succeeded else 1
            print(json.dumps({"site_code": code, "work_id": str(out.work_id), "cause": out.cause,
                              "succeeded": out.succeeded, "attempt_no": out.attempt_no,
                              "appended": [str(x) for x in out.appended],
                              "replayed": [str(x) for x in out.replayed],
                              "error_code": out.error_code, "error_detail": out.error_detail}))
        return 1 if failed else 0
    except CONSEQUENCE_UNAVAILABLE as error:
        print(f"The consequence store is unavailable: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
