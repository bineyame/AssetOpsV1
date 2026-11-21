"""3A7 (spec §5, §6.1; D-3A7.5, D-3A7.12, D-3A7.15): record a closed month's management accounts, show a Site-month's
money standing, or set the tenant's tolerance from an owner file.

    python -m assetops_backend.reconcile_month record --tenant SLUG --as EMAIL --period YYYY-MM [--site CODE] \\
        --currency CCC --revenue R --fuel-cost F --source-ref TEXT
    python -m assetops_backend.reconcile_month show --tenant SLUG --period YYYY-MM [--site CODE] [--known-at ISO]
    python -m assetops_backend.reconcile_month set-tolerance --tenant SLUG --tolerance T --owner-ref owner/owner-x.md

`DATABASE_URL` from the environment, checked (with the real-data switch) before any connection. Exit 0: one JSON
line (§6.1's shapes; Decimals as plain strings; the sentences as the statements render them). Exit 3: a refused
statement, `{"state": "REFUSED", "code", "params", "text"}`. Exit 2: a refusal before the service, its code alone on
stderr. The finance lead is named with `--as`; the row records `recorded_by_script` true (queue Q1).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Sequence

from assetops_backend.accounts.permissions import roles_of
from assetops_backend.commercial.composition import commercial_upload_settings
from assetops_backend.commercial.model import PERIOD_FORM
from assetops_backend.commercial.uploads import Actor
from assetops_backend.config import ConfigurationError
from assetops_backend.i18n import render
from assetops_backend.structure.reconciliation import (COMMAND, HeadingCheck, MoneyStanding, ReconRefused,
                                                        StatementCheck, refusal_words)

#: §2.4: the repository root, which holds `owner/`.
OWNER_ROOT = Path(__file__).resolve().parents[2]


class _Stop(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.reconcile_month",
                                     description="Reconcile a closed month with the management accounts.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("record", "show", "set-tolerance"):
        sub = commands.add_parser(name)
        sub.add_argument("--tenant", required=True, help="the tenant's slug")
        if name == "set-tolerance":
            sub.add_argument("--tolerance", required=True, help="a fraction, like 0.02")
            sub.add_argument("--owner-ref", required=True, help="the owner file that sets it")
            continue
        sub.add_argument("--period", required=True, help="the month, YYYY-MM")
        sub.add_argument("--site", default=None, help="a Site code; omitted, the organisation")
        if name == "show":
            sub.add_argument("--known-at", default=None, help="an ISO instant with its offset")
            continue
        sub.add_argument("--as", dest="as_email", required=True, help="the finance lead's email")
        sub.add_argument("--currency", required=True)
        sub.add_argument("--revenue", required=True)
        sub.add_argument("--fuel-cost", required=True)
        sub.add_argument("--source-ref", required=True, help="where the figures come from")
    return parser


def owner_reader(root: Path) -> Callable[[str], bytes | None]:
    """D-3A7.15: the `owner_file` port over an owner root. The service admits only `owner/owner-<topic>.md` refs."""
    def read(ref: str) -> bytes | None:
        path = root / ref
        if path.is_symlink() or not path.is_file():
            return None
        try:
            return path.read_bytes()
        except OSError:
            return None
    return read


def _plain(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def heading_json(h: HeadingCheck) -> dict[str, Any]:
    return {"heading": h.heading, "state": h.state, "reason": h.reason, "accounts": _plain(h.accounts),
            "recorded": _plain(h.recorded), "difference": _plain(h.difference), "allowed": _plain(h.allowed),
            "record_currencies": list(h.record_currencies), "sources": list(h.sources), "origins": list(h.origins),
            "text": h.text}


def statement_json(c: StatementCheck | None) -> dict[str, Any] | None:
    if c is None:
        return None
    return {"statement_id": str(c.statement_id), "site_code": c.site_code, "period": c.period, "currency": c.currency,
            "tolerance": _plain(c.tolerance), "state": c.state, "opens": c.opens,
            "headings": [heading_json(h) for h in c.headings], "recorded_by": str(c.recorded_by),
            "recorded_at": c.recorded_at.isoformat(), "recorded_by_script": c.recorded_by_script,
            "source_ref": c.source_ref, "text": c.text}


def standing_json(s: MoneyStanding, site_code: str | None) -> dict[str, Any]:
    return {"site_code": site_code, "period": s.period,
            "known_at": None if s.known_at is None else s.known_at.isoformat(), "reconciled": s.reconciled,
            "reason": s.reason, "tolerance": _plain(s.tolerance), "this_month": statement_json(s.this_month),
            "cited": statement_json(s.cited), "text": s.text, "details": list(s.details)}


def _line(obj: Any) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=False) + "\n")


def _person(accounts: Any, email: str, slug: str) -> Actor:
    """3A3 §2.6 step 5: the person and the first role of the command they hold."""
    person = accounts.onboard_person(email)
    if person is None or person.tenant_slug != slug or not person.active:
        raise _Stop("PERSON_NOT_FOUND")
    held = {role for role, _ in person.roles}
    role = next((r for r in roles_of(COMMAND) if r in held), None)
    if role is None:
        raise _Stop("PERSON_ROLE_REQUIRED")
    return Actor(person.person_id, role)


def _known_at(text: str | None) -> datetime | None:
    if text is None:
        return None
    try:
        at = datetime.fromisoformat(text)
    except ValueError:
        raise _Stop("KNOWN_AT_INVALID") from None
    if at.tzinfo is None or at.utcoffset() is None or "T" not in text:
        raise _Stop("KNOWN_AT_INVALID")
    return at


def _record(recon: Any, accounts: Any, tenant_id: Any, args: argparse.Namespace) -> int:
    actor = _person(accounts, args.as_email, args.tenant)
    try:
        check = recon.record(tenant_id, actor, site_code=args.site, period=args.period, currency=args.currency,
                             revenue=args.revenue, fuel_cost=args.fuel_cost, source_ref=args.source_ref,
                             by_script=True)
    except ReconRefused as refused:
        _line({"state": "REFUSED", "code": refused.code, "params": refused.params,
               "text": render(refusal_words(refused))})
        return 3
    _line(statement_json(check))
    return 0


def _show(recon: Any, tenant_id: Any, args: argparse.Namespace) -> int:
    if PERIOD_FORM.fullmatch(args.period) is None:
        raise _Stop("RECON_PERIOD")
    known_at = _known_at(args.known_at)
    site = None
    if args.site is not None:
        site = recon.site(tenant_id, args.site)
        if site is None:
            raise _Stop("RECON_SITE_UNKNOWN")
    standing = recon.standing(tenant_id, None if site is None else site.site_id, args.period, known_at=known_at)
    _line(standing_json(standing, None if site is None else site.site_code))
    return 0


def _set_tolerance(recon: Any, tenant_id: Any, args: argparse.Namespace) -> int:
    try:
        row = recon.set_tolerance(tenant_id, args.tolerance, args.owner_ref)
    except ReconRefused as refused:
        raise _Stop(refused.code) from None
    _line({"state": "SET", "tolerance": row.tolerance, "owner_ref_sha256": row.owner_ref_sha256})
    return 0


def _run(args: argparse.Namespace, recon: Any, accounts: Any, owner_root: Path | None) -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise _Stop("DATABASE_URL_REQUIRED")
    try:
        commercial_upload_settings(url)  # before any connection; the real-data switch follows the database
    except ConfigurationError:
        raise _Stop("CONFIGURATION") from None
    dispose = None
    if recon is None:
        from assetops_backend.structure.reconciliation_composition import build_commercial_reconciliation

        reader = owner_reader(owner_root if owner_root is not None else OWNER_ROOT)
        recon, dispose = build_commercial_reconciliation(url, owner_file=reader)
    if accounts is None:
        from assetops_backend.accounts.composition import build_account_service

        accounts = build_account_service(url)
    try:
        tenant_id = accounts.tenant_by_slug(args.tenant)
        if tenant_id is None:
            raise _Stop("TENANT_NOT_FOUND")
        if args.command == "record":
            return _record(recon, accounts, tenant_id, args)
        if args.command == "show":
            return _show(recon, tenant_id, args)
        return _set_tolerance(recon, tenant_id, args)
    finally:
        if dispose is not None:
            dispose()


def main(argv: Sequence[str] | None = None, *, reconciliation: Any = None, accounts: Any = None,
         owner_root: Path | None = None) -> int:
    """Injected services (tests) skip the composition; the URL and settings checks always run. An injected
    `reconciliation` carries its own owner-file reader; `owner_root` is the folder that reader reads."""
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        return _run(args, reconciliation, accounts, owner_root)
    except _Stop as stop:
        sys.stderr.write(f"{stop.code}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
