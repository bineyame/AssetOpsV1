"""Server-side recompute of `fuel-cost-1` consequences (S4-02b phase 2a; S4-02c phase 2 scheduled runner).

    python -m assetops_backend.recompute_consequences run --tenant demo --site KOBO-001 [--limit 100]
    python -m assetops_backend.recompute_consequences pending --tenant demo --site KOBO-001

`run` is a one-shot, bounded drain of ONE explicitly named tenant and Site (packet
`tasks/S4-02c-evidence-consequence-work.md` item 4). It takes the Site runner claim
(`pg_try_advisory_lock('financial_consequence_runner:' || site)`) on a dedicated connection; if another runner
holds it, it reports the Site skipped and exits 0. Otherwise it processes at most `--limit` due work items (never
attempted, or past the retry time derived from the last FAILED attempt: 1, 2, 4, 8, 16 minutes, then 16) and
prints one JSON line per item, then one summary line with the Site scope and the selected, appended, replayed,
no-op, failed, deferred and backlog counts. Exit code 0 when every processed item succeeded (or the Site was
skipped), 1 when any failed, 2 for a tenant other than the configured development tenant or an unknown Site,
3 when the store is unavailable. `pending` lists the work still pending with its attempt count and last error.

This CLI is not an active-Site iterator and does not cover every Site of a production tenant: it serves only the
configured development tenant, one Site per invocation. Scheduling (owner: whoever operates the deployment's
backend host; cadence: every minute; recovery: none needed beyond the next tick, because failed work stays
pending and a killed run's claim is released with its connection) is an external timer, for example:

    Windows Task Scheduler (one task per Site; "Run whether user is logged on or not"; repeat every 1 minute;
    "Do not start a new instance" if the previous run is still going):
        schtasks /Create /TN "AssetOps consequence runner KOBO-001" /SC MINUTE /MO 1 /TR
          "C:\\AssetOps\\.venv\\Scripts\\python.exe -m assetops_backend.recompute_consequences run
           --tenant demo --site KOBO-001 --limit 100"

    systemd (assetops-consequence-runner@KOBO-001.service with Type=oneshot, EnvironmentFile holding
    DATABASE_URL, ExecStart=/opt/assetops/.venv/bin/python -m assetops_backend.recompute_consequences run
    --tenant demo --site %i --limit 100; and a .timer with OnCalendar=*-*-* *:*:00, AccuracySec=5s,
    Persistent=false).

An overlapping tick is harmless: the second run finds the Site claimed and reports it skipped.
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

DEFAULT_LIMIT = 100


def _limit(value: str) -> int:
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("--limit must be at least 1")
    return n


def main(argv: Sequence[str] | None = None, *, worker=None, store=None, prices=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.recompute_consequences")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--limit", type=_limit, default=DEFAULT_LIMIT)
    pending = sub.add_parser("pending")
    for p in (run, pending):
        p.add_argument("--tenant", required=True)
        p.add_argument("--site", required=True)
    args = parser.parse_args(argv)
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant; this runner serves only that "
              "tenant, one named Site per run, and does not cover other tenants' Sites.", file=sys.stderr)
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
        report = worker.run(tenant_id, site_id, args.limit)
        for out in report.outcomes:
            print(json.dumps({"site_code": code, "work_id": str(out.work_id), "cause": out.cause,
                              "succeeded": out.succeeded, "attempt_no": out.attempt_no,
                              "appended": [str(x) for x in out.appended],
                              "replayed": [str(x) for x in out.replayed], "no_op_reason": out.no_op_reason,
                              "error_code": out.error_code, "error_detail": out.error_detail}))
        counts = report.counts()
        print(json.dumps({"site_code": code, "tenant": args.tenant, "site_id": str(site_id),
                          "claimed": report.claimed, "skipped": not report.claimed,
                          "now": report.now.isoformat(), "limit": args.limit, **counts}))
        return 1 if counts["failed"] else 0
    except CONSEQUENCE_UNAVAILABLE as error:
        print(f"The consequence store is unavailable: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
