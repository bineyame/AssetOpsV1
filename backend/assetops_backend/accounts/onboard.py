"""3C0a (spec §7; D-3C0A.7, R7, P2, P4): the onboarding command.

    python -m assetops_backend.accounts.onboard create --tenant SLUG --email E --name N [--executive]
    python -m assetops_backend.accounts.onboard set-password --email E
    python -m assetops_backend.accounts.onboard disable --email E --reason R
    python -m assetops_backend.accounts.onboard enable --email E

Reads `DATABASE_URL`. `create` and `set-password` read the password from the first line of stdin (only the trailing
newline removed). Success prints the person ID and exits 0; a refusal prints `<CODE>` and one plain sentence to
stderr and exits 2. Only the tenant's first executive gets a role from here (`--executive`); every other role is
granted by the executive through the API (OD-14).
"""
from __future__ import annotations

import argparse
import sys
from typing import Sequence

from assetops_backend.accounts.composition import build_account_service
from assetops_backend.accounts.model import AccountRefused
from assetops_backend.config import database_url
from assetops_backend.i18n import message, render


def _refuse(code: str) -> int:
    print(f"{code} {render(message('accounts.' + code.lower()), 'en')}", file=sys.stderr)
    return 2


def _password() -> str:
    line = sys.stdin.readline()
    return line[:-1] if line.endswith("\n") else line


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.accounts.onboard")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--tenant", required=True)
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--executive", action="store_true")
    commands.add_parser("set-password").add_argument("--email", required=True)
    disable = commands.add_parser("disable")
    disable.add_argument("--email", required=True)
    disable.add_argument("--reason", required=True)
    commands.add_parser("enable").add_argument("--email", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    url = database_url()
    if url is None:
        return _refuse("DATABASE_URL_REQUIRED")
    accounts = build_account_service(url)
    try:
        if args.command == "create":
            person = accounts.onboard_create(args.tenant, args.email, args.name, _password(),
                                             executive=args.executive)
        elif args.command == "set-password":
            person = accounts.onboard_set_password(args.email, _password())
        elif args.command == "disable":
            person = accounts.onboard_set_status(args.email, "DISABLED", args.reason)
        else:
            person = accounts.onboard_set_status(args.email, "ACTIVE", None)
    except AccountRefused as refused:
        return _refuse(refused.code)
    print(person)
    return 0


if __name__ == "__main__":
    sys.exit(main())
