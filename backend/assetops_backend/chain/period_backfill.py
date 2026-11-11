"""ANY-1 AR-1: the stored read-period backfill CLI (architect answer 2026-11-10 §4), modelled on ``chain.snapshots``.

    python -m assetops_backend.chain.period_backfill build --site KOBO-001 [--from 2026-10-01 --to 2026-11-02] \
        [--kind mini_depth.renewable ...] [--stale-only] [--tenant <slug>]
    python -m assetops_backend.chain.period_backfill show --site KOBO-001 --from 2026-10-01 --to 2026-11-02 \
        [--kind ...] [--known-at <iso>]

``build`` rebuilds every (day, kind) of the range through the one ``PeriodReadBuilder`` (an unchanged fingerprint and
builder version writes nothing); ``--stale-only`` rebuilds only the days holding a row of an older builder version
(those read as PENDING until rebuilt). It prints one JSON line per period considered and a closing summary line.
``show`` prints the latest row per period with its PENDING reasons, and a closing ``pending`` line. The kinds are
the builder's kinds the event register declares for the Site's type (AR-1 declares none, so both commands report
zero kinds). The tenant defaults to the development tenant and any other tenant exits 2; without DATABASE_URL it
exits 1.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timezone
from typing import Any, Sequence
from zoneinfo import ZoneInfo

from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.chain.period_read import PeriodReader, stale_rows


def _day(text: str) -> date:
    return date.fromisoformat(text)


def _instant(text: str) -> datetime:
    at = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return at if at.tzinfo else at.replace(tzinfo=timezone.utc)


def _default_services() -> Any:
    from assetops_backend.chain.composition import build_chain_services

    return build_chain_services(database_url())


def _default_register() -> Any:
    from assetops_backend.chain.composition import load_event_register

    return load_event_register()


def main(argv: Sequence[str] | None = None, *, services: Any = None, register: Any = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.chain.period_backfill")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    show = sub.add_parser("show")
    for p in (build, show):
        p.add_argument("--site", required=True)
        p.add_argument("--kind", action="append", default=None)
        p.add_argument("--tenant", default=DEVELOPMENT_TENANT_SLUG)
    build.add_argument("--quiet", action="store_true", help="AR-2: print only the closing summary line")
    build.add_argument("--from", dest="from_day", type=_day)
    build.add_argument("--to", dest="to_day", type=_day)
    build.add_argument("--stale-only", action="store_true")
    show.add_argument("--from", dest="from_day", type=_day, required=True)
    show.add_argument("--to", dest="to_day", type=_day, required=True)
    show.add_argument("--known-at", dest="known_at", type=_instant)
    args = parser.parse_args(argv)
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    services = _default_services() if services is None else services
    if services is None:
        print("DATABASE_URL is not set; nothing was written.", file=sys.stderr)
        return 1
    register = _default_register() if register is None else register
    try:
        tenant_id = services.inputs.tenant_id(args.tenant)
        if tenant_id is None:
            print(f"No tenant {args.tenant!r}; nothing was written.", file=sys.stderr)
            return 2
        site = services.inputs.site(tenant_id, args.site)
        if site is None:
            print(f"No Site {args.site!r}; nothing was written.", file=sys.stderr)
            return 2
        builder = services.period_builder
        kinds = [k for k in register.kinds_for(site.site_type) if k in builder.kinds]
        if args.kind:
            unknown = sorted(set(args.kind) - set(kinds))
            if unknown:
                print(f"Unknown or undeclared kind(s) for {site.site_type}: {unknown}", file=sys.stderr)
                return 2
            kinds = [k for k in kinds if k in set(args.kind)]
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
            if args.stale_only:
                rows = services.periods.read_latest(tenant_id, [site.site_id], kinds, from_day, to_day, None)
                todo = sorted({(r.local_day, r.kind) for r in stale_rows(rows, builder.versions())})
                out = [w for day, kind in todo for w in builder.build(tenant_id, site, day, kind)]
            else:
                out = builder.build_range(tenant_id, site, from_day, to_day, kinds) if kinds else []
            elapsed = time.perf_counter() - started
            for w in () if args.quiet else out:
                print(json.dumps({**w.row.to_json(), "site_code": site.site_code, "written": w.written},
                                 sort_keys=True))
            print(json.dumps({"site_code": site.site_code, "from": from_day.isoformat(), "to": to_day.isoformat(),
                              "kinds": kinds, "stale_only": bool(args.stale_only), "considered": len(out),
                              "written": sum(1 for w in out if w.written), "seconds": round(elapsed, 3)}))
            return 0
        reader = PeriodReader(services.periods, register, builder.versions())
        result = reader.read(tenant_id, [site], kinds, args.from_day, args.to_day, args.known_at)
        for r in result.rows:
            print(json.dumps({**r.row.to_json(), "site_code": site.site_code, "pending": list(r.pending)},
                             sort_keys=True))
        print(json.dumps({"site_code": site.site_code, "kinds": kinds,
                          "pending": [{"local_day": d.isoformat(), "kind": k, "reasons": list(v)}
                                      for (_, d, k), v in result.pending.items()]}))
        return 0
    finally:
        services.dispose()


if __name__ == "__main__":
    sys.exit(main())
