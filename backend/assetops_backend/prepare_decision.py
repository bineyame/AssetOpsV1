"""6a (`specs/6a-decision-records/spec.md` §4; D-P6.3, D-P6.14): prepare a decision on a Site's lever, in the analyst's name.

    python -m assetops_backend.prepare_decision --tenant SLUG --as EMAIL --site CODE --lever ID --period YYYY-MM
        --current NAME=VALUE[,NAME=VALUE...] [--finding UUID] [--horizon N]

The analyst's trusted act, not a sign-in. Writes the decision and its options (no action first, then the lever's grid
minus today's setting) once; a re-run says so (`already_prepared` true). Success: one JSON line on stdout, exit 0;
names, never emails. A refusal: `<CODE> <sentence>` on stderr, exit 2 (3 when the store cannot be reached).
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import Any, Callable, Sequence

from assetops_backend.decisions import cli
from assetops_backend.decisions.records import DecisionRefused


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.prepare_decision",
                                     description="Prepare a decision on a Site's lever.")
    parser.add_argument("--tenant", required=True, help="the operator's slug")
    parser.add_argument("--as", dest="as_email", required=True, help="email of the analyst who prepares it")
    parser.add_argument("--site", required=True, help="the Site's code")
    parser.add_argument("--lever", required=True, help="the lever's id")
    parser.add_argument("--period", required=True, help="the period, YYYY-MM")
    parser.add_argument("--current", required=True, help="today's setting: NAME=VALUE[,NAME=VALUE...]")
    parser.add_argument("--finding", default=None, help="the Finding the decision answers (a UUID)")
    parser.add_argument("--horizon", default=None, help="months the options are valued over (default 12)")
    return parser


def _current(raw: str):
    settings = {}
    for part in raw.split(","):
        name, found, value = part.partition("=")
        if not found or not name or name in settings:
            raise DecisionRefused("BAD_CURRENT")
        settings[name] = cli.as_decimal(value, "BAD_CURRENT")
    return settings


def main(argv: Sequence[str] | None = None, *, services: Any = None,
         clock: Callable[[], datetime] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        current = _current(args.current)
        finding = None if args.finding is None else cli.as_uuid(args.finding)
        extra = {} if args.horizon is None else {"horizon_months": cli.as_int(args.horizon, "BAD_HORIZON")}
    except DecisionRefused as refused:
        return cli.refuse(refused.code, refused.exit)

    def act(service) -> dict:
        got = service.prepare(tenant_slug=args.tenant, as_email=args.as_email, site_code=args.site,
                              lever_id=args.lever, period=args.period, current=current, finding_id=finding, **extra)
        d = got.decision
        view = next(v for v in service.for_tenant(d.tenant_id, period_from=d.period, period_to=d.period)
                    if v.decision_id == str(d.id))
        return {"decision_id": str(d.id), "site_code": view.site_code, "lever_id": d.lever_id, "period": d.period,
                "horizon_months": d.horizon_months, "home_category": view.home_category,
                "options": [{"option_key": o.option_key, "settings": {k: str(v) for k, v in o.settings.items()}}
                            for o in got.options],
                "prepared_by": view.prepared_by_name, "already_prepared": got.already_prepared}

    return cli.run(args, services, clock, act)


if __name__ == "__main__":
    sys.exit(main())
