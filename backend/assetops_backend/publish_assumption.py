"""Server-side SYSTEM publisher for Site financial assumptions (S4-02a phase 1).

An administrative demonstration trigger, not a UI action. The actor is always the stable service principal
`SYSTEM_PUBLISHER`; there is no `--actor` or `--author` flag. Every publication names its Site explicitly,
its source, its expected prior revision (`none` for the first) and an idempotency key.

    python -m assetops_backend.publish_assumption publish --site KOBO-001 \
        --change-kind INITIAL --currency USD --value 1.25 --basis AUTHORED_ESTIMATE \
        --source "..." --valid-from 2026-01-01T00:00:00Z --expected-prior none --idempotency-key k1
    python -m assetops_backend.publish_assumption fixture --site KOBO-001 \
        --file backend/conversions/demo-diesel-price-publications.json [--step v1 ...]

A fixture run is idempotent: an already-published step answers with its stored revision ID. Output is one
JSON line per publication; a refusal prints its typed code and exits 3, nothing written for that step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence
from uuid import UUID

from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.financials.composition import (
    AssumptionStoreUnavailable,
    PostgresAssumptionStore,
    build_assumption_store,
)
from assetops_backend.financials.assumptions import (
    SYSTEM_PUBLISHER,
    canonical_step_sha256,
    Publication,
    PublicationRefused,
    parse_value,
)

SERVICE = "assetops-assumption-publisher"


def _instant(raw: str | None, name: str) -> datetime | None:
    if raw is None:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise PublicationRefused(422, "VALIDITY_NOT_INSTANT", f"{name} {raw!r} is not an ISO instant.") from error


def _prior(raw: str) -> UUID | None:
    if raw == "none":
        return None
    try:
        return UUID(raw)
    except ValueError as error:
        raise PublicationRefused(422, "EXPECTED_PRIOR_INVALID",
                                 "--expected-prior is a revision UUID or the word 'none'.") from error


def _emit(site: str, step: str | None, published) -> None:
    print(json.dumps({"site_code": site, "step": step, "revision_id": str(published.revision_id),
                      "revision_no": published.revision_no, "change_kind": published.change_kind,
                      "recorded_at": published.recorded_at.isoformat(), "replayed": published.replayed,
                      "actor_id": SYSTEM_PUBLISHER.actor_id}))


def _refused(site: str, step: str | None, error: PublicationRefused) -> int:
    print(json.dumps({"site_code": site, "step": step, "refused": error.code, "status": error.status,
                      "message": error.message}), file=sys.stderr)
    return 3


def fixture_publications(path: Path, steps: Sequence[str], resolve_prior) -> list[tuple[str, Publication]]:
    """Fixture steps as publications. `resolve_prior(idempotency_key)` returns that step's stored revision ID."""
    raw = path.read_bytes()
    doc = json.loads(raw)
    by_step = {s["step"]: s for s in doc["steps"]}
    wanted = list(steps) or [s["step"] for s in doc["steps"]]
    out = []
    for name in wanted:
        s = by_step[name]
        prior_step = s.get("expected_prior_step")
        prior = None if prior_step is None else resolve_prior(by_step[prior_step]["idempotency_key"])
        if prior_step is not None and prior is None:
            raise PublicationRefused(409, "PRIOR_STEP_NOT_PUBLISHED",
                                     f"Step {name} expects step {prior_step}, which is not published for this Site.")
        out.append((name, Publication(
            assumption_key=doc["assumption_key"], currency=s["currency"], value=parse_value(s["value"]),
            basis=s["basis"], source_reference=s["source_reference"],
            valid_from=_instant(s["valid_from"], "valid_from"), valid_to=_instant(s.get("valid_to"), "valid_to"),
            change_kind=s["change_kind"], correction_reason=s.get("correction_reason"),
            expected_prior_revision_id=prior, idempotency_key=s["idempotency_key"], channel="SYSTEM_FIXTURE",
            provenance={"service": SERVICE, "job": "fixture", "fixture": doc["fixture"],
                        "fixture_version": doc["version"], "fixture_step": name,
                        "fixture_step_sha256": canonical_step_sha256(s),
                        "fixture_sha256": hashlib.sha256(raw).hexdigest()})))
    return out


def main(argv: Sequence[str] | None = None, *, store: PostgresAssumptionStore | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.publish_assumption")
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("publish")
    one.add_argument("--site", required=True)
    one.add_argument("--key", default="diesel_price_per_litre")
    one.add_argument("--change-kind", required=True, choices=["INITIAL", "SUCCESSION", "CORRECTION"])
    one.add_argument("--currency", required=True)
    one.add_argument("--value", required=True)
    one.add_argument("--basis", required=True)
    one.add_argument("--source", required=True)
    one.add_argument("--valid-from", required=True)
    one.add_argument("--valid-to")
    one.add_argument("--reason")
    one.add_argument("--expected-prior", required=True)
    one.add_argument("--idempotency-key", required=True)
    fix = sub.add_parser("fixture")
    fix.add_argument("--site", required=True)
    fix.add_argument("--file", required=True)
    fix.add_argument("--step", action="append", default=[])
    for p in (one, fix):
        p.add_argument("--tenant", default=DEVELOPMENT_TENANT_SLUG)
    args = parser.parse_args(argv)
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    store = build_assumption_store(database_url()) if store is None else store
    try:
        scope = store.site_scope(args.tenant, args.site)
        if scope is None:
            print(f"No imported Site {args.site!r} in tenant {args.tenant!r}; nothing was written.", file=sys.stderr)
            return 2
        code, tenant_id, site_id = scope
        if args.command == "publish":
            try:
                publication = Publication(
                    assumption_key=args.key, currency=args.currency, value=parse_value(args.value),
                    basis=args.basis, source_reference=args.source,
                    valid_from=_instant(args.valid_from, "valid_from"), valid_to=_instant(args.valid_to, "valid_to"),
                    change_kind=args.change_kind, correction_reason=args.reason,
                    expected_prior_revision_id=_prior(args.expected_prior), idempotency_key=args.idempotency_key,
                    channel="SYSTEM_CLI", provenance={"service": SERVICE, "job": "cli-publish"})
                _emit(code, None, store.publish(tenant_id, site_id, publication, SYSTEM_PUBLISHER))
            except PublicationRefused as error:
                return _refused(code, None, error)
            return 0
        path = Path(args.file)
        doc = json.loads(path.read_bytes())
        unknown = [s for s in args.step if s not in {d["step"] for d in doc["steps"]}]
        if unknown:
            print(f"Unknown fixture step(s) {unknown}; nothing was written.", file=sys.stderr)
            return 2

        def resolve(key: str) -> UUID | None:
            rows = store.revisions(tenant_id, site_id, doc["assumption_key"])
            return next((r["id"] for r in rows if r["idempotency_key"] == key), None)

        for name in args.step or [s["step"] for s in doc["steps"]]:
            try:
                ((step, publication),) = fixture_publications(path, [name], resolve)
                _emit(code, step, store.publish(tenant_id, site_id, publication, SYSTEM_PUBLISHER))
            except PublicationRefused as error:
                return _refused(code, name, error)
        return 0
    except AssumptionStoreUnavailable as error:
        print(f"Assumption store unavailable; nothing was written. {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
