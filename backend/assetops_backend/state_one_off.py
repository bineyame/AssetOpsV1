"""6a (`specs/6a-decision-records/spec.md` §4; D-P6.5, D-P6.24): state the one-off cost of an option, in a person's name.

    python -m assetops_backend.state_one_off --tenant SLUG --as EMAIL --decision UUID --option KEY --amount 90.00
        --currency USD --crew-visits N --basis TEXT

A site manager on the decision's Site, or a finance lead. A later statement for the same option replaces the earlier
one in the read (both are kept). Success: one JSON line on stdout, exit 0; a refusal: `<CODE> <sentence>` on stderr,
exit 2 (3 when the store cannot be reached).
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import Any, Callable, Sequence

from assetops_backend.decisions import cli
from assetops_backend.decisions.records import DecisionRefused


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.state_one_off",
                                     description="State the one-off cost of a decision's option.")
    parser.add_argument("--tenant", required=True, help="the operator's slug")
    parser.add_argument("--as", dest="as_email", required=True, help="email of the person who states it")
    parser.add_argument("--decision", required=True, help="the decision's id (a UUID)")
    parser.add_argument("--option", required=True, help="the option's key")
    parser.add_argument("--amount", required=True, help="the one-off amount, at most 2 decimals")
    parser.add_argument("--currency", required=True, help="three capital letters, like USD")
    parser.add_argument("--crew-visits", dest="crew_visits", required=True, help="crew visits it needs, 0 or more")
    parser.add_argument("--basis", required=True, help="where the figure comes from, 1 to 200 characters")
    return parser


def main(argv: Sequence[str] | None = None, *, services: Any = None,
         clock: Callable[[], datetime] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        decision_id = cli.as_uuid(args.decision)
        amount = cli.as_decimal(args.amount, "BAD_AMOUNT")
        crew_visits = cli.as_int(args.crew_visits, "BAD_CREW_VISITS")
    except DecisionRefused as refused:
        return cli.refuse(refused.code, refused.exit)

    def act(service) -> dict:
        row = service.state_one_off(tenant_slug=args.tenant, as_email=args.as_email, decision_id=decision_id,
                                    option_key=args.option, amount=amount, currency=args.currency,
                                    crew_visits=crew_visits, basis=args.basis)
        view = next(v for v in service.for_tenant(row.tenant_id) if v.decision_id == str(decision_id))
        by = next(o.one_off for o in view.options if o.option_key == args.option).declared_by_name
        return {"decision_id": str(decision_id), "option_key": args.option, "amount": str(row.amount),
                "currency": row.currency, "crew_visits": row.crew_visits, "basis": row.basis, "declared_by": by,
                "declared_at": cli.iso_seconds(row.declared_at)}

    return cli.run(args, services, clock, act)


if __name__ == "__main__":
    sys.exit(main())
