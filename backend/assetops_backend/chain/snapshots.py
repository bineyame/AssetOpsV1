"""CLI for the day snapshots (CH-1a §4.5), modelled on ``declare_objective``.

    python -m assetops_backend.chain.snapshots build --site KOBO-001 [--from 2026-10-01 --to 2026-11-02] \
        [--measure productive_kwh ...] [--tenant <slug>]
    python -m assetops_backend.chain.snapshots show --site KOBO-001 --from 2026-10-01 --to 2026-11-02 \
        [--measure ...] [--known-at <iso>]

``build`` prints one JSON line per row it considered (``written`` false when the fingerprint was unchanged) and a
closing summary line; ``show`` prints one JSON line per latest row and a closing ``grade_counts`` line. The tenant
defaults to the development tenant and any other tenant exits 2; without DATABASE_URL it exits 1.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timezone
from typing import Sequence
from zoneinfo import ZoneInfo

from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.chain.composition import build_chain_services
from assetops_backend.chain.measures import measures_for


def _day(text: str) -> date:
    return date.fromisoformat(text)


def _instant(text: str) -> datetime:
    at = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return at if at.tzinfo else at.replace(tzinfo=timezone.utc)


def main(argv: Sequence[str] | None = None, *, services=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.chain.snapshots")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    show = sub.add_parser("show")
    for p in (build, show):
        p.add_argument("--site", required=True)
        p.add_argument("--measure", action="append", default=None)
        p.add_argument("--tenant", default=DEVELOPMENT_TENANT_SLUG)
    build.add_argument("--from", dest="from_day", type=_day)
    build.add_argument("--to", dest="to_day", type=_day)
    show.add_argument("--from", dest="from_day", type=_day, required=True)
    show.add_argument("--to", dest="to_day", type=_day, required=True)
    show.add_argument("--known-at", dest="known_at", type=_instant)
    args = parser.parse_args(argv)
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    services = build_chain_services(database_url()) if services is None else services
    if services is None:
        print("DATABASE_URL is not set; nothing was written.", file=sys.stderr)
        return 1
    try:
        tenant_id = services.inputs.tenant_id(args.tenant)
        if tenant_id is None:
            print(f"No tenant {args.tenant!r}; nothing was written.", file=sys.stderr)
            return 2
        site = services.inputs.site(tenant_id, args.site)
        if site is None:
            print(f"No Site {args.site!r}; nothing was written.", file=sys.stderr)
            return 2
        keys = [m.key for m in measures_for(site.site_type)]
        if args.measure:
            unknown = sorted(set(args.measure) - set(keys))
            if unknown:
                print(f"Unknown measure(s) for {site.site_type}: {unknown}", file=sys.stderr)
                return 2
            keys = [k for k in keys if k in set(args.measure)]
        if args.command == "build":
            tz = ZoneInfo(site.timezone)
            from_day, to_day = args.from_day, args.to_day
            if from_day is None:
                first = services.inputs.first_evidence_time(tenant_id, site.site_id)
                if first is None:
                    print(json.dumps({"site_code": site.site_code, "written": 0, "considered": 0,
                                      "note": "no accepted evidence"}))
                    return 0
                from_day = first.astimezone(tz).date()
            if to_day is None:
                to_day = datetime.now(tz).date()
            started = time.perf_counter()
            out = services.builder.build_range(tenant_id, site, from_day, to_day, keys)
            elapsed = time.perf_counter() - started
            for w in out:
                print(json.dumps({**w.row.to_json(), "site_code": site.site_code, "written": w.written},
                                 sort_keys=True))
            days = (to_day - from_day).days + 1
            print(json.dumps({"site_code": site.site_code, "from": from_day.isoformat(), "to": to_day.isoformat(),
                              "considered": len(out), "written": sum(1 for w in out if w.written),
                              "seconds": round(elapsed, 3),
                              "ms_per_measure_day": round(1000 * elapsed / max(1, days * len(keys)), 1)}))
            return 0
        rows = services.reader.latest(tenant_id, site.site_id, args.from_day, args.to_day, keys, args.known_at)
        for r in rows:
            print(json.dumps({**r.to_json(), "site_code": site.site_code}, sort_keys=True))
        counts = services.reader.grade_counts(tenant_id, site.site_id, args.from_day, args.to_day, keys,
                                              args.known_at)
        print(json.dumps({"site_code": site.site_code, "grade_counts": counts.to_json()}))
        return 0
    finally:
        services.dispose()


if __name__ == "__main__":
    sys.exit(main())
