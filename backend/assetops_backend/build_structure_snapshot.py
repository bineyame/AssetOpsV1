"""3B7a unit 3 (spec §4.4; D-3B7A.6): build or verify the frozen monthly structure snapshot on command.

    python -m assetops_backend.build_structure_snapshot build  --tenant SLUG --month YYYY-MM --by BUILT_BY
    python -m assetops_backend.build_structure_snapshot verify --tenant SLUG --snapshot UUID

`DATABASE_URL` from the environment. `build` covers every Site of the tenant (every lifecycle; the types with no
structure are listed as excluded). One JSON line on stdout: build `{"as_of", "portfolio_snapshot_id", "sites",
"excluded", "rules_digest"}`; verify `{"snapshot_id", "matches", "differences", "rules_changed"}`. Exit 0 done
(verify: matches); 2 refused before any work; 3 `SNAPSHOT_EXISTS`; 4 verify differs. Refusals print `<CODE> <one
sentence>` on stderr.

Runbook (the analyst, after each accepted import, and after a deploy):
`build --tenant <slug> --month <YYYY-MM> --by person:<their account id>`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Sequence
from uuid import UUID

from assetops_backend.structure_snapshot.model import BUILT_BY
from assetops_backend.structure_snapshot.store import SnapshotExists

_MONTH = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", re.ASCII)
_SENTENCES = {
    "NO_DATABASE": "Set DATABASE_URL to the database to build in.",
    "BAD_MONTH": "The month must be YYYY-MM.",
    "BAD_BUILT_BY": "The builder must be person:<account id> or service:<name>.",
    "UNKNOWN_TENANT": "No organisation has that slug.",
    "UNKNOWN_SNAPSHOT": "No portfolio snapshot of this organisation has that id.",
    "SNAPSHOT_EXISTS": "A snapshot of this month was already built at this instant; nothing was written.",
}


class _Stop(Exception):
    def __init__(self, exit_code: int, code: str) -> None:
        super().__init__(code)
        self.exit_code = exit_code
        self.code = code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.build_structure_snapshot")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="build the month's snapshot for every Site of the tenant")
    build.add_argument("--tenant", required=True)
    build.add_argument("--month", required=True)
    build.add_argument("--by", required=True)
    verify = commands.add_parser("verify", help="rebuild a portfolio snapshot at its as-of and compare")
    verify.add_argument("--tenant", required=True)
    verify.add_argument("--snapshot", required=True, type=UUID)
    return parser


def _line(obj: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=False) + "\n")


def _run(args: argparse.Namespace, service: Any) -> int:
    url = os.environ.get("DATABASE_URL")
    if service is None and not url:
        raise _Stop(2, "NO_DATABASE")
    if args.command == "build":
        if _MONTH.fullmatch(args.month) is None:
            raise _Stop(2, "BAD_MONTH")
        if BUILT_BY.fullmatch(args.by) is None:
            raise _Stop(2, "BAD_BUILT_BY")
    owned = service is None
    if owned:
        from assetops_backend.structure_snapshot.composition import build_structure_snapshot

        service = build_structure_snapshot(url)
    try:
        found = service.store.tenant_sites(args.tenant)
        if found is None:
            raise _Stop(2, "UNKNOWN_TENANT")
        tenant_id, sites = found
        if args.command == "build":
            try:
                result = service.builder.build(tenant_id, sites, args.month, built_by=args.by)
            except SnapshotExists:
                raise _Stop(3, "SNAPSHOT_EXISTS") from None
            _line({"as_of": result.as_of.isoformat(), "portfolio_snapshot_id": str(result.portfolio_snapshot_id),
                   "sites": {code: str(i) for code, i in result.sites.items()}, "excluded": list(result.excluded),
                   "rules_digest": result.rules_digest})
            return 0
        try:
            v = service.builder.verify(tenant_id, args.snapshot)
        except (LookupError, ValueError):
            raise _Stop(2, "UNKNOWN_SNAPSHOT") from None
        _line({"snapshot_id": str(v.snapshot_id), "matches": v.matches, "differences": list(v.differences),
               "rules_changed": v.rules_changed})
        return 0 if v.matches else 4
    finally:
        if owned:
            service.dispose()


def main(argv: Sequence[str] | None = None, *, service: Any = None) -> int:
    """An injected service (tests) skips the composition and the DATABASE_URL check."""
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        return _run(args, service)
    except _Stop as stop:
        sys.stderr.write(f"{stop.code} {_SENTENCES[stop.code]}\n")
        return stop.exit_code


if __name__ == "__main__":
    sys.exit(main())
