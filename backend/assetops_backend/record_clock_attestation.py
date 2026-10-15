"""Server-side SYSTEM attester for labelled simulated source clock attestations (LR-01 phase 1).

An administrative demonstration trigger, not a UI action and not a gateway path. The actor is always the
stable service principal `SYSTEM_ATTESTER`; there is no `--actor`, `--author` or credential flag, no HTTP
route, and no real-source proof class (`D-2026-10-15-lr01-source-time-cohort`). Each command appends one
event and, in the same transaction, requeues the dispatch windows whose clock basis could change.

    python -m assetops_backend.record_clock_attestation record --site KOBO-001 --source <uuid> \
        --epoch <sequence-epoch> --authority "..." --label "SIMULATED ..." --max-error-seconds 30 \
        --valid-from 2026-10-24T00:00:00Z --valid-to 2026-10-25T00:00:00Z --idempotency-key k1
    python -m assetops_backend.record_clock_attestation replace|expire|revoke --site KOBO-001 \
        --attestation <uuid> --expected-version N --source <uuid> --epoch <epoch> --idempotency-key k2 ...

Output is one JSON line; a refusal prints its typed code and exits 3 with nothing written.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence
from uuid import UUID

from assetops_backend.analytics.composition import build_postgres_assessment_store
from assetops_backend.analytics.assessment_ports import AssessmentStoreUnavailable
from assetops_backend.analytics.clock_attestation import SYSTEM_ATTESTER, AttestationChange, AttestationRefused
from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url

KINDS = {"record": "RECORDED", "replace": "REPLACED", "expire": "EXPIRED", "revoke": "REVOKED"}


def _instant(raw: str | None, name: str) -> datetime | None:
    if raw is None:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise AttestationRefused(422, "VALIDITY_NOT_INSTANT", f"{name} {raw!r} is not an ISO instant.") from error


def change_from(args: argparse.Namespace) -> AttestationChange:
    error = None if args.max_error_seconds is None else timedelta(seconds=float(args.max_error_seconds))
    return AttestationChange(
        event_kind=KINDS[args.command], source_id=UUID(args.source), sequence_epoch=args.epoch,
        idempotency_key=args.idempotency_key, channel="SYSTEM_CLI", authority=args.authority, label=args.label,
        max_utc_error=error, valid_from=_instant(args.valid_from, "valid_from"),
        valid_to=_instant(args.valid_to, "valid_to"),
        attestation_id=None if args.attestation is None else UUID(args.attestation),
        expected_version=args.expected_version, reason=args.reason)


def main(argv: Sequence[str] | None = None, store: Any = None,
         now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(prog="record_clock_attestation", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in KINDS:
        p = sub.add_parser(name)
        p.add_argument("--site", required=True)
        p.add_argument("--tenant", default=DEVELOPMENT_TENANT_SLUG)
        p.add_argument("--source", required=True)
        p.add_argument("--epoch", required=True)
        p.add_argument("--idempotency-key", required=True)
        p.add_argument("--authority")
        p.add_argument("--label")
        p.add_argument("--max-error-seconds")
        p.add_argument("--valid-from")
        p.add_argument("--valid-to")
        p.add_argument("--attestation")
        p.add_argument("--expected-version", type=int)
        p.add_argument("--reason")
    args = parser.parse_args(argv)
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    store = build_postgres_assessment_store(database_url()) if store is None else store
    try:
        scope = store.site_scope(args.tenant, args.site)
        if scope is None:
            print(f"No imported Site {args.site!r} in tenant {args.tenant!r}; nothing was written.", file=sys.stderr)
            return 2
        code, tenant_id, site_id = scope
        try:
            out = store.record_clock_attestation(tenant_id, site_id, change_from(args), SYSTEM_ATTESTER,
                                                 now or datetime.now(timezone.utc))
        except AttestationRefused as error:
            print(json.dumps({"site_code": code, "refused": error.code, "status": error.status,
                              "message": error.message}), file=sys.stderr)
            return 3
        event = out["event"]
        print(json.dumps({"site_code": code, "replayed": not out["created"], "actor_id": SYSTEM_ATTESTER.actor_id,
                          **event.payload(), "recorded_at": event.recorded_at.isoformat(),
                          "requeued": [w.payload() for w in out["requeued"]]}))
        return 0
    except AssessmentStoreUnavailable as error:
        print(f"Assessment store unavailable; nothing was written. {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
