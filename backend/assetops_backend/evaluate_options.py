"""6c (`specs/6c-option-evaluator/spec.md` §4; D-P6.6, D-P6.27): value every option of a decision against no action,
in the analyst's name, and write the run.

    python -m assetops_backend.evaluate_options --tenant SLUG --as EMAIL --decision UUID [--study PATH]

Every call writes a new run (a valuation is dated); the latest run is the one a choice binds. Success: one JSON line on
stdout, exit 0, with money rounded half-even to cents once from the stored figure; a refusal: `<CODE> <sentence>` on
stderr, exit 2 (3 when the store or the month's figures cannot be reached).
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Any, Callable, Sequence

from assetops_backend.decisions import cli
from assetops_backend.decisions.records import SOURCE_CLASSES, DecisionRefused, RunRow

CENT = Decimal("0.01")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.evaluate_options",
                                     description="Value every option of a decision against doing nothing.")
    parser.add_argument("--tenant", required=True, help="the operator's slug")
    parser.add_argument("--as", dest="as_email", required=True, help="email of the analyst who values the options")
    parser.add_argument("--decision", required=True, help="the decision's id (a UUID)")
    parser.add_argument("--study", default=None, help="the simulation file for a setting-grid change")
    return parser


def money(value: Decimal | None) -> str | None:
    if value is None:
        return None
    rounded = value.quantize(CENT, rounding=ROUND_HALF_EVEN)
    return str(rounded.copy_abs() if rounded == 0 else rounded)


def line(run: RunRow, keys: dict) -> dict[str, Any]:
    """§4's JSON line: top-level keys in order, one entry per option in position order."""
    identity = run.study_identity or {}
    options = []
    for e in run.evaluations:
        options.append({
            "option_key": keys[e.option_id], "disposition": e.disposition, "reason_code": e.reason_code,
            "rank": e.rank, "monthly_change": money(e.monthly_change), "horizon_change": money(e.horizon_change),
            "value": money(e.value), "currency": e.currency,
            "missing": [[m.record_kind, m.source_family, m.factor_id] for m in e.missing],
            "admitted": None if e.admission is None else e.admission["admitted"]})
    return {"run_id": str(run.id), "decision_id": str(run.decision_id), "outcome": run.outcome,
            "source_class": min((e.source_class for e in run.evaluations), key=SOURCE_CLASSES.index),
            "frame": identity.get("frame"), "months_averaged": identity.get("months_averaged", []),
            "options": options}


def main(argv: Sequence[str] | None = None, *, services: Any = None,
         clock: Callable[[], datetime] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        decision_id = cli.as_uuid(args.decision)
    except DecisionRefused as refused:
        return cli.refuse(refused.code, refused.exit)

    def act(service) -> dict:
        run = service.evaluate(tenant_slug=args.tenant, as_email=args.as_email, decision_id=decision_id,
                               study_path=None if args.study is None else Path(args.study))
        return line(run, service.option_keys(run))

    from assetops_backend.decisions.decisions_composition import build_evaluation

    return cli.run(args, services, clock, act, build=build_evaluation)


if __name__ == "__main__":
    sys.exit(main())
