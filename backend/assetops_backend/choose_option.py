"""6a (`specs/6a-decision-records/spec.md` §4; D-P6.9, D-P6.12): the executive chooses an option (or none) of a
valued decision, once, optionally under an agreed Action.

    python -m assetops_backend.choose_option --tenant SLUG --as EMAIL --decision UUID (--option KEY | --none)
        [--action UUID]

The choice is tied to the decision's latest run. A re-run of the same choice says so (`already_chosen` true).
Success: one JSON line on stdout, exit 0; a refusal: `<CODE> <sentence>` on stderr, exit 2 (3 when the store cannot
be reached).
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import Any, Callable, Sequence

from assetops_backend.decisions import cli
from assetops_backend.decisions.records import DecisionRefused


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.choose_option",
                                     description="Choose an option of a decision, or none.")
    parser.add_argument("--tenant", required=True, help="the operator's slug")
    parser.add_argument("--as", dest="as_email", required=True, help="email of the executive who chooses")
    parser.add_argument("--decision", required=True, help="the decision's id (a UUID)")
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--option", default=None, help="the option's key")
    which.add_argument("--none", action="store_true", help="keep things as they are")
    parser.add_argument("--action", default=None, help="the agreed Action the choice proceeds under (a UUID)")
    return parser


def main(argv: Sequence[str] | None = None, *, services: Any = None,
         clock: Callable[[], datetime] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        decision_id = cli.as_uuid(args.decision)
        action = None if args.action is None else cli.as_uuid(args.action)
    except DecisionRefused as refused:
        return cli.refuse(refused.code, refused.exit)

    def act(service) -> dict:
        got = service.choose(tenant_slug=args.tenant, as_email=args.as_email, decision_id=decision_id,
                             option_key=args.option, agreed_action_id=action)
        c = got.choice
        view = next(v for v in service.for_tenant(c.tenant_id) if v.decision_id == str(decision_id))
        return {"decision_id": str(decision_id), "option_key": view.choice.option_key, "run_id": str(c.run_id),
                "agreed_action_id": None if c.agreed_action_id is None else str(c.agreed_action_id),
                "chosen_by": view.choice.chosen_by_name, "chosen_at": cli.iso_seconds(c.chosen_at),
                "already_chosen": got.already_chosen}

    return cli.run(args, services, clock, act)


if __name__ == "__main__":
    sys.exit(main())
