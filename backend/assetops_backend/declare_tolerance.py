"""3B4 unit 3 (spec §5.3; D-3B4.11, D-3B4.19, D-3B4.22): declare, clear or show a Site's tolerance on an observed leaf.

    python -m assetops_backend.declare_tolerance set   --tenant SLUG --site CODE --factor F --of OF --pct P \\
                                                         --from YYYY-MM --as EMAIL
    python -m assetops_backend.declare_tolerance clear --tenant SLUG --site CODE --factor F --from YYYY-MM --as EMAIL
    python -m assetops_backend.declare_tolerance show  --tenant SLUG --site CODE --month YYYY-MM

`DATABASE_URL` from the environment. The finance lead declares a leaf with a money dimension, the Site's own manager
(a grant bound to that Site) every other observed leaf; the row records the person, the admitting role and the
store's time, and is never changed (append-only). Exit 0 one JSON line; exit 2 a refusal, nothing written, its code
alone on stderr (no served text, D-3B4.13).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Sequence
from uuid import uuid4

from assetops_backend.accounts.permissions import SITE_MANAGER, roles_of
from assetops_backend.structure.observe import observe as _observe
from assetops_backend.structure.observe import rules
from assetops_backend.structure.observe.service import tolerance_in_force
from assetops_backend.structure.read import SITE_TYPE_TO_STRUCTURE
from assetops_backend.structure.registry import REGISTRIES

_MONTH = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", re.ASCII)
_PCT = re.compile(r"[0-9]{1,3}(\.[0-9]{1,2})?", re.ASCII)
MONEY_COMMAND = "structure.tolerance.money"
OPERATIONAL_COMMAND = "structure.tolerance.operational"


class _Stop(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.declare_tolerance")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("set", "clear", "show"):
        sub = commands.add_parser(name)
        sub.add_argument("--tenant", required=True)
        sub.add_argument("--site", required=True)
        if name == "show":
            sub.add_argument("--month", required=True)
            continue
        sub.add_argument("--factor", required=True)
        if name == "set":
            sub.add_argument("--of", required=True)
            sub.add_argument("--pct", required=True)
        sub.add_argument("--from", dest="valid_from", required=True)
        sub.add_argument("--as", dest="person", required=True)
    return parser


def pct_valid(pct: str) -> bool:
    """`^[0-9]{1,3}(\\.[0-9]{1,2})?$` and `0 <= pct <= 100`; 0 is accepted (D-3B4.19)."""
    return _PCT.fullmatch(pct) is not None and Decimal(pct) <= 100


def admitting_role(person: Any, command: str, site_id: Any) -> str | None:
    """The first role of `roles_of(command)` the person holds; a SITE_MANAGER pair counts only on this Site."""
    for role in roles_of(command):
        for held, bound in person.roles:
            if held == role and (role != SITE_MANAGER or bound == site_id):
                return role
    return None


def _line(obj: Any) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=False) + "\n")


def _site(wiring: Any, args: argparse.Namespace):
    found = wiring.store.tenant_sites(args.tenant)
    if found is None:
        raise _Stop("UNKNOWN_TENANT")
    tenant_id, sites = found
    site = next((s for s in sites if s.site_code == args.site), None)
    key = None if site is None else SITE_TYPE_TO_STRUCTURE.get(site.site_type)
    if key is None or key not in REGISTRIES:
        raise _Stop("SITE_UNKNOWN")
    return tenant_id, site, key


def _show(wiring: Any, args: argparse.Namespace) -> int:
    tenant_id, site, key = _site(wiring, args)
    if _MONTH.fullmatch(args.month) is None:
        raise _Stop("BAD_MONTH")
    registry = REGISTRIES[key]
    declared = tolerance_in_force(wiring.findings.tolerances(tenant_id, site.site_id), key, args.month,
                                  datetime.now(timezone.utc))
    out = []
    for factor in rules.OBSERVED.get(key, {}):
        t = _observe.in_force(registry, factor, declared.get(factor))
        out.append({"factor_id": factor, "source": t.source, "of_factor": t.of_factor,
                    "pct": None if t.pct is None else format(t.pct, "f"),
                    "declaration_id": None if t.declaration_id is None else str(t.declaration_id)})
    _line(out)
    return 0


def _declare(wiring: Any, accounts: Any, args: argparse.Namespace) -> int:
    tenant_id, site, key = _site(wiring, args)
    if args.factor not in rules.OBSERVED.get(key, {}):
        raise _Stop("FACTOR_NOT_OBSERVED")
    registry = REGISTRIES[key]
    leaf = registry.row(args.factor)
    setting = args.command == "set"
    if setting:
        by_id = {r.factor_id: r for r in registry.rows}
        if args.of not in by_id or by_id[args.of].unit != leaf.unit:
            raise _Stop("OF_FACTOR_UNIT")
        if not pct_valid(args.pct):
            raise _Stop("PCT_INVALID")
    if _MONTH.fullmatch(args.valid_from) is None:
        raise _Stop("BAD_MONTH")
    if accounts is None:
        from assetops_backend.accounts.composition import build_account_service

        accounts = build_account_service(os.environ["DATABASE_URL"])
    person = accounts.onboard_person(args.person)
    if person is None or not person.active or person.tenant_id != tenant_id:
        raise _Stop("PERSON_NOT_FOUND")
    command = MONEY_COMMAND if rules.money_dimension(leaf.unit) else OPERATIONAL_COMMAND
    role = admitting_role(person, command, site.site_id)
    if role is None:
        raise _Stop("PERSON_ROLE_REQUIRED")
    row = rules.ToleranceRow(uuid4(), tenant_id, site.site_id, key, args.factor, "SET" if setting else "CLEARED",
                             args.of if setting else None, args.pct if setting else None, args.valid_from, None,
                             person.person_id, role, True)
    declaration_id = wiring.findings.tolerance_append(row)
    _line({"state": row.state, "declaration_id": str(declaration_id), "factor_id": row.factor_id,
           "of_factor": row.of_factor, "pct": row.pct, "valid_from": row.valid_from,
           "recorded_by": str(row.recorded_by), "recorded_role": role, "recorded_by_script": True})
    return 0


def _run(args: argparse.Namespace, wiring: Any, accounts: Any) -> int:
    url = os.environ.get("DATABASE_URL")
    if wiring is None and not url:
        raise _Stop("NO_DATABASE")
    owned = wiring is None
    if owned:
        from assetops_backend.structure.observe.composition import build_structure_observer

        wiring = build_structure_observer(url)
    try:
        return _show(wiring, args) if args.command == "show" else _declare(wiring, accounts, args)
    finally:
        if owned:
            wiring.dispose()


def main(argv: Sequence[str] | None = None, *, observer: Any = None, accounts: Any = None) -> int:
    """An injected `observer` (a `Wiring`: `store`, `findings`, `dispose`) and `accounts` (tests) skip the
    composition; with `observer` injected the DATABASE_URL check is skipped too."""
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        return _run(args, observer, accounts)
    except _Stop as stop:
        sys.stderr.write(f"{stop.code}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
