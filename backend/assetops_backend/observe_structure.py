"""3B4 unit 3 (spec §5.2; D-3B4.10, D-3B4.13): observe a closed month's structure snapshot on command.

    python -m assetops_backend.observe_structure run --tenant SLUG --month YYYY-MM

`DATABASE_URL` from the environment. One JSON line on stdout: `{"month", "snapshot_id", "as_of", "sites": {code:
{"states": {factor: state}, "written": [{"factor_id", "transition", "finding_id", "revision_id"}]}}, "excluded":
{code: [reasons]}}`. Exit 0 done; 2 refused before any work (`NO_DATABASE`, `BAD_MONTH`, `UNKNOWN_TENANT`); 3 the
observer refused (`NO_SNAPSHOT`, `REBUILD_NEEDED`, `SNAPSHOT_NOT_CURRENT`, `MONTH_OPEN`), nothing written. stderr
carries the code alone (no served text, D-3B4.13).

Runbook (the analyst): after `build_structure_snapshot build` for a closed month, run `observe_structure run` for that
month.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Sequence

from assetops_backend.structure.observe.service import ObserveRefused

_MONTH = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", re.ASCII)


class _Stop(Exception):
    def __init__(self, exit_code: int, code: str) -> None:
        super().__init__(code)
        self.exit_code = exit_code
        self.code = code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.observe_structure")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="observe every Site of the tenant for one closed month")
    run.add_argument("--tenant", required=True)
    run.add_argument("--month", required=True)
    return parser


def result_line(result: Any) -> dict[str, Any]:
    return {"month": result.month, "snapshot_id": str(result.snapshot_id), "as_of": result.as_of.isoformat(),
            "sites": {code: {"states": dict(s.states),
                             "written": [{"factor_id": w.factor_id, "transition": w.transition,
                                          "finding_id": str(w.finding_id), "revision_id": str(w.revision_id)}
                                         for w in s.written]}
                      for code, s in result.sites.items()},
            "excluded": {code: list(reasons) for code, reasons in result.excluded.items()}}


def _run(args: argparse.Namespace, wiring: Any) -> int:
    url = os.environ.get("DATABASE_URL")
    if wiring is None and not url:
        raise _Stop(2, "NO_DATABASE")
    if _MONTH.fullmatch(args.month) is None:
        raise _Stop(2, "BAD_MONTH")
    owned = wiring is None
    if owned:
        from assetops_backend.structure.observe.composition import build_structure_observer

        wiring = build_structure_observer(url)
    try:
        found = wiring.store.tenant_sites(args.tenant)
        if found is None:
            raise _Stop(2, "UNKNOWN_TENANT")
        try:
            result = wiring.observer.run(found[0], args.month)
        except ObserveRefused as refused:
            raise _Stop(3, refused.code) from None
        sys.stdout.write(json.dumps(result_line(result), sort_keys=False) + "\n")
        return 0
    finally:
        if owned:
            wiring.dispose()


def main(argv: Sequence[str] | None = None, *, observer: Any = None, accounts: Any = None) -> int:
    """An injected `observer` (a `Wiring`: `observer`, `store`, `dispose`; tests) skips the composition and the
    DATABASE_URL check. `accounts` is accepted for the spec's signature (D-3B4.22) and not read: the run names no
    person."""
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        return _run(args, observer)
    except _Stop as stop:
        sys.stderr.write(f"{stop.code}\n")
        return stop.exit_code


if __name__ == "__main__":
    sys.exit(main())
