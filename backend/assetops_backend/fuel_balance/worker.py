"""DIESEL-K3 (`.agent/build-sheet-DIESEL-1.md` §9d.4): assess named nights, explicitly.

    python -m assetops_backend.fuel_balance.worker assess --site <code> --from <local date> --to <local date>

Nights `[from, to)`, using `DATABASE_URL`. One JSON line per night:
`{"site_code", "night_date", "status": "APPENDED"|"REUSED"|"OPEN", "revision", "state", "reason"}`. A night whose
window is not yet closed prints `OPEN` and the run continues; any other refusal prints a `REFUSED` line with its code
and exits 2. There is no tick stage, job domain or HTTP route in v1.

    python -m assetops_backend.fuel_balance.worker raise --site <code> --from <local date> --to <local date>

DIESEL-K4a (§9j.6): raise the unexplained-fuel Finding of each stored night `[from, to)`; one JSON line per night
`{"site_code", "night_date", "status", "finding_id", "revision_id"}`, status OPENED, REVISED, WITHDRAWN, UNCHANGED,
NO_FINDING or NO_WINDOW; a refusal prints its line and exits 2.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from typing import Any, Sequence

from assetops_backend.fuel_balance.model import WINDOW_OPEN, FuelBalanceRefused
from assetops_backend.fuel_balance.service import FuelBalanceService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="assetops_backend.fuel_balance.worker")
    sub = parser.add_subparsers(dest="command", required=True)
    assess = sub.add_parser("assess", help="assess the closed nights [from, to) of one Site")
    assess.add_argument("--site", required=True)
    assess.add_argument("--from", dest="lo", required=True, type=date.fromisoformat)
    assess.add_argument("--to", dest="hi", required=True, type=date.fromisoformat)
    raise_ = sub.add_parser("raise", help="raise the unexplained-fuel Finding of the stored nights [from, to)")
    raise_.add_argument("--site", required=True)
    raise_.add_argument("--from", dest="lo", required=True, type=date.fromisoformat)
    raise_.add_argument("--to", dest="hi", required=True, type=date.fromisoformat)
    return parser


def _raise(args: argparse.Namespace, service: Any) -> int:
    """DIESEL-K4a (§9j.6): one JSON line per night `{"site_code", "night_date", "status", "finding_id",
    "revision_id"}`; a refusal prints its line and exits 2."""
    if not args.lo < args.hi:
        _line({"site_code": args.site, "status": "REFUSED", "code": "FUEL_FINDING_NIGHTS_INVALID",
               "detail": "--from must be before --to"})
        return 2
    site = service.stores.fuel.site_by_code(args.site)
    if site is None:
        _line({"site_code": args.site, "status": "REFUSED", "code": "FUEL_FINDING_SITE_UNKNOWN",
               "detail": f"no single Site has the code {args.site!r}"})
        return 2
    night = args.lo
    while night < args.hi:
        result = service.raise_night(site[0], site[1], night)
        _line({"site_code": args.site, "night_date": night.isoformat(), "status": result.status,
               "finding_id": None if result.finding_id is None else str(result.finding_id),
               "revision_id": None if result.revision_id is None else str(result.revision_id)})
        night += timedelta(days=1)
    return 0


def _line(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, sort_keys=False), flush=True)


def main(argv: Sequence[str] | None = None, *, store: Any = None, finding_service: Any = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "raise":
        owned_service = finding_service is None
        if owned_service:
            from assetops_backend.fuel_balance.composition import build_fuel_finding_service

            finding_service = build_fuel_finding_service(os.environ.get("DATABASE_URL"))
        try:
            return _raise(args, finding_service)
        finally:
            if owned_service:
                finding_service.dispose()
    owned = store is None
    if owned:
        from assetops_backend.fuel_balance.composition import build_fuel_balance_store

        store = build_fuel_balance_store(os.environ.get("DATABASE_URL"))
    try:
        if not args.lo < args.hi:
            _line({"site_code": args.site, "status": "REFUSED", "code": "FUEL_BALANCE_NIGHTS_INVALID",
                   "detail": "--from must be before --to"})
            return 2
        site = store.site_by_code(args.site)
        if site is None:
            _line({"site_code": args.site, "status": "REFUSED", "code": "FUEL_BALANCE_SITE_UNKNOWN",
                   "detail": f"no single Site has the code {args.site!r}"})
            return 2
        service = FuelBalanceService(store)
        night = args.lo
        while night < args.hi:
            base = {"site_code": args.site, "night_date": night.isoformat()}
            try:
                result = service.assess_night(site[0], site[1], night)
            except FuelBalanceRefused as refused:
                if refused.code == WINDOW_OPEN:
                    _line({**base, "status": "OPEN", "revision": None, "state": None, "reason": None})
                    night += timedelta(days=1)
                    continue
                _line({**base, "status": "REFUSED", "code": refused.code, "detail": refused.detail})
                return 2
            w = result.window
            _line({**base, "status": "APPENDED" if result.appended else "REUSED", "revision": w.revision,
                   "state": w.state, "reason": w.reason})
            night += timedelta(days=1)
        return 0
    finally:
        if owned:
            store.dispose()


if __name__ == "__main__":
    sys.exit(main())
