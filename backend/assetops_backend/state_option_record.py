"""6h4 (`specs/6h-named-option-levers/spec.md` §6.2; D-P6.58): state a document's level of one figure under an option.

    python -m assetops_backend.state_option_record --tenant SLUG --as EMAIL --decision UUID --option KEY
        --factor ID --value N --unit UNIT [--currency USD] --document TEXT --basis TEXT [--emulated]

A site manager on the decision's Site, or a finance lead. The figure is the level a month under the option, as the
document gives it, never a difference. A later record for the same option and figure replaces the earlier one in the
read (both are kept). Success: one JSON line on stdout, exit 0; a refusal: `<CODE> <sentence>` on stderr, exit 2
(3 when the store cannot be reached).
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import Any, Callable, Sequence

from assetops_backend.decisions import cli
from assetops_backend.decisions.records import DecisionRefused


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.state_option_record",
                                     description="State a document's level of a figure under a decision's option.")
    parser.add_argument("--tenant", required=True, help="the operator's slug")
    parser.add_argument("--as", dest="as_email", required=True, help="email of the person who states it")
    parser.add_argument("--decision", required=True, help="the decision's id (a UUID)")
    parser.add_argument("--option", required=True, help="the option's key")
    parser.add_argument("--factor", required=True, help="the figure's id, a leaf the option changes")
    parser.add_argument("--value", required=True, help="the level under the option, at most 6 decimals")
    parser.add_argument("--unit", required=True, help="the figure's unit, as the registry writes it")
    parser.add_argument("--currency", default=None, help="three capital letters; only for a money figure")
    parser.add_argument("--document", required=True, help="the document that states it, 1 to 200 characters")
    parser.add_argument("--basis", required=True, help="how the document gives it, 1 to 200 characters")
    parser.add_argument("--emulated", action="store_true", help="the document is a source emulation")
    return parser


def main(argv: Sequence[str] | None = None, *, services: Any = None,
         clock: Callable[[], datetime] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        decision_id = cli.as_uuid(args.decision)
        value = cli.as_decimal(args.value, "BAD_VALUE")
    except DecisionRefused as refused:
        return cli.refuse(refused.code, refused.exit)

    def act(service) -> dict:
        row = service.state_option_record(
            tenant_slug=args.tenant, as_email=args.as_email, decision_id=decision_id, option_key=args.option,
            factor_id=args.factor, value=value, unit=args.unit, currency=args.currency, document=args.document,
            basis=args.basis, emulated=args.emulated)
        return {"decision_id": str(decision_id), "option_key": args.option, "factor_id": row.factor_id,
                "value": str(row.value), "unit": row.unit, "currency": row.currency, "origin": row.origin,
                "document": row.document, "basis": row.basis, "declared_role": row.declared_role,
                "declared_at": cli.iso_seconds(row.declared_at)}

    return cli.run(args, services, clock, act)


if __name__ == "__main__":
    sys.exit(main())
