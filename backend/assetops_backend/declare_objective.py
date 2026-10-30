"""Server-side SYSTEM declarer for site-level outcome objectives (OUT-D U3).

An administrative demonstration trigger, not a UI action. The actor is always the stable service principal
`SYSTEM_DECLARER`; there is no `--actor` flag. Unit, measure kind, comparison and window rule come from the measure,
never from the command line.

    python -m assetops_backend.declare_objective fixture --file backend/conversions/demo-objectives.json [--site CODE ...]
    python -m assetops_backend.declare_objective declare --site KOBO-001 --outcome MG-2 \
        --measure avoidable_generator_minutes --target 5 --source-note "..." --expected-prior <uuid> \
        --idempotency-key out-d-kobo-001-mg-2-v2

Output is one JSON line per objective. A fixture entry whose Site is not imported is skipped with a `skipped` line,
so one file serves every demonstration database. A refusal prints its typed code and exits 3; nothing is written
for that objective.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID

from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.objectives.composition import ObjectiveStoreUnavailable, build_objective_store
from assetops_backend.objectives.model import SYSTEM_DECLARER, Declaration, ObjectiveRefused, target_string


def _target(raw: Any) -> Decimal:
    try:
        return Decimal(str(raw))
    except InvalidOperation as error:
        raise ObjectiveRefused(422, "OBJECTIVE_INVALID", f"Target {raw!r} is not a decimal number.") from error


def _prior(raw: str | None) -> UUID | None:
    if raw is None or raw == "none":
        return None
    try:
        return UUID(raw)
    except ValueError as error:
        raise ObjectiveRefused(422, "OBJECTIVE_INVALID",
                               "--expected-prior is a revision UUID or the word 'none'.") from error


def _emit(row: dict[str, Any], site_code: str, inserted: bool) -> None:
    print(json.dumps({"site_code": site_code, "outcome_key": row["outcome_key"], "revision_id": str(row["id"]),
                      "revision_no": row["revision_no"], "measure_key": row["measure_key"],
                      "target": target_string(row["target"]), "inserted": inserted,
                      "recorded_at": row["recorded_at"].isoformat(), "actor_id": row["actor_id"]}))


def _refused(site_code: str, outcome: str | None, error: ObjectiveRefused) -> int:
    print(json.dumps({"site_code": site_code, "outcome_key": outcome, "refused": error.code, "status": error.status,
                      "message": error.message}), file=sys.stderr)
    return 3


def main(argv: Sequence[str] | None = None, *, store=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.declare_objective")
    sub = parser.add_subparsers(dest="command", required=True)
    fix = sub.add_parser("fixture")
    fix.add_argument("--file", required=True)
    fix.add_argument("--site", action="append", default=[])
    one = sub.add_parser("declare")
    one.add_argument("--site", required=True)
    one.add_argument("--outcome", required=True)
    one.add_argument("--measure", required=True)
    one.add_argument("--target", required=True)
    one.add_argument("--currency")
    one.add_argument("--source", default="DECLARED", choices=["DECLARED", "RECORDED"])
    one.add_argument("--source-note", required=True)
    one.add_argument("--expected-prior", required=True)
    one.add_argument("--idempotency-key", required=True)
    for p in (fix, one):
        p.add_argument("--tenant", default=DEVELOPMENT_TENANT_SLUG)
    args = parser.parse_args(argv)
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    store = build_objective_store(database_url()) if store is None else store
    if store is None:
        print("DATABASE_URL is not set; nothing was written.", file=sys.stderr)
        return 1
    try:
        tenant_id = store.tenant_id(args.tenant)
        if tenant_id is None:
            print(f"No tenant {args.tenant!r}; nothing was written.", file=sys.stderr)
            return 2
        if args.command == "declare":
            try:
                decl = Declaration(args.site, args.outcome, args.measure, _target(args.target), args.currency,
                                   args.source, args.source_note, _prior(args.expected_prior), args.idempotency_key)
                row, inserted = store.declare(tenant_id, decl, SYSTEM_DECLARER, "SYSTEM_CLI")
            except ObjectiveRefused as error:
                return _refused(args.site, args.outcome, error)
            _emit(row, args.site, inserted)
            return 0
        doc = json.loads(Path(args.file).read_bytes())
        wanted = {s.lower() for s in args.site}
        for entry in doc["objectives"]:
            code = entry["site_code"]
            if wanted and code.lower() not in wanted:
                continue
            site_id = store.site_id(tenant_id, code)
            if site_id is None:
                print(json.dumps({"site_code": code, "outcome_key": entry["outcome_key"], "skipped": "SITE_NOT_IMPORTED"}))
                continue
            try:
                prior_key = entry.get("expected_prior_key")
                prior = None if prior_key is None else store.revision_id(tenant_id, site_id, prior_key)
                if prior_key is not None and prior is None:
                    raise ObjectiveRefused(409, "OBJECTIVE_PRIOR_MISMATCH",
                                           f"Entry {entry['idempotency_key']} expects {prior_key}, which is not declared.")
                decl = Declaration(code, entry["outcome_key"], entry["measure_key"], _target(entry["target"]),
                                   entry.get("currency"), entry["source"], entry["source_note"], prior,
                                   entry["idempotency_key"])
                row, inserted = store.declare(tenant_id, decl, SYSTEM_DECLARER, "SYSTEM_FIXTURE")
            except ObjectiveRefused as error:
                return _refused(code, entry["outcome_key"], error)
            _emit(row, code, inserted)
        return 0
    except ObjectiveStoreUnavailable as error:
        print(f"Objective store unavailable; nothing was written. {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
