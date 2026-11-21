"""3C2 (`specs/3C2-agreed-change-action/spec.md` §2.5; D-3C2.3, D-3C2.12, D-3C2.14): record the change agreed at the end
of the deep-dive as an Action, in the agreeing person's name.

    python -m assetops_backend.record_action --tenant SLUG --as EMAIL --title TEXT --owner EMAIL --due YYYY-MM-DD
        [--site CODE] [--factor ID]

The analyst's trusted act, not a sign-in: it reads no password, session or token. `--as` names the person the record
is attributed to, and `created_by_script` true says a script typed it (residual risk R-AUTH). A re-run records
nothing new and says so (`already_recorded` true).

Success: one JSON line of twelve keys on stdout, exit 0; names, never emails; no value or amount. A refusal: `<CODE>
<sentence>` on stderr, nothing on stdout, exit 2 (3 when the store cannot be reached). The sentence and the success
line's `state` word are SC-1 statements rendered by `actions/agreed.py` (D-3C2.14).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from typing import Any, Callable, Sequence

from assetops_backend.actions.agreed import AgreedActionRefused, Recorded, refusal_sentence

_DUE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.record_action",
                                     description="Record the change agreed at the end of the deep-dive as an Action.",
                                     epilog="Overdue counts from the day after the due date, by the UTC calendar.")
    parser.add_argument("--tenant", required=True, help="the operator's slug")
    parser.add_argument("--as", dest="as_email", required=True, help="email of the executive who agreed the change")
    parser.add_argument("--title", required=True, help="the change, 1 to 200 characters")
    parser.add_argument("--owner", required=True, help="email of the person who owns the change")
    parser.add_argument("--due", required=True, help="the due date, YYYY-MM-DD")
    parser.add_argument("--site", default=None, help="the Site's code, when the change applies to one Site")
    parser.add_argument("--factor", default=None, help="the factor the change moves (needs --site)")
    return parser


def _refuse(code: str, status: int = 2) -> int:
    sys.stderr.write(f"{code} {refusal_sentence(code)}\n")
    return status


def _iso_seconds(at: datetime) -> str:
    return at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _line(recorded: Recorded) -> dict[str, Any]:
    row, view = recorded.row, recorded.view
    return {"action_id": str(row.id), "title": row.title, "site_code": view.site_code, "factor_id": row.factor_id,
            "owner": view.owner_name, "created_by": view.created_by_name, "created_role": row.created_role,
            "created_by_script": row.created_by_script, "created_at": _iso_seconds(row.created_at),
            "due_on": row.due_on.isoformat(), "state": view.state_words, "already_recorded": recorded.already_recorded}


def _due(text: str) -> date | None:
    if not _DUE.fullmatch(text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def main(argv: Sequence[str] | None = None, *, services: Any = None,
         clock: Callable[[], datetime] | None = None) -> int:
    args = build_parser().parse_args(argv)
    due_on = _due(args.due)
    if due_on is None:
        return _refuse("BAD_DUE")
    composed = None
    if services is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            return _refuse("NO_DATABASE")
        from assetops_backend.actions.agreed_composition import build_agreed_actions

        try:
            composed = services = (build_agreed_actions(url) if clock is None
                                   else build_agreed_actions(url, clock=clock))
        except Exception:  # noqa: BLE001 - any composition error is the store being unreachable (§2.5)
            return _refuse("ACTIONS_UNAVAILABLE", 3)
    from assetops_backend.accounts.composition import ACCOUNTS_UNAVAILABLE

    try:
        recorded = services.service.record(tenant_slug=args.tenant, as_email=args.as_email, title=args.title,
                                           owner_email=args.owner, due_on=due_on, site_code=args.site,
                                           factor_id=args.factor)
    except AgreedActionRefused as refused:
        return _refuse(refused.code, refused.exit)
    except ACCOUNTS_UNAVAILABLE:
        return _refuse("ACTIONS_UNAVAILABLE", 3)
    finally:
        if composed is not None:
            composed.dispose()
    sys.stdout.write(json.dumps(_line(recorded)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
