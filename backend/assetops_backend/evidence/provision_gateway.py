"""Operator provisioning of a registered gateway's upload credential (S2-02 phase 2).

    python -m assetops_backend.evidence.provision_gateway issue --tenant demo \
        --site KOBO-001 --gateway edge-kobo-01 --enable-source <source external id> ... \
        --credential-out var/gateway/upload-credential

Run with `DATABASE_URL` set and the database migrated to 0006.

`issue` generates a fresh high-entropy bearer credential, stores only its
selector and one-way verifier, revokes every earlier credential of the gateway
(rotation: the old one stops working on the next request; sealed bytes are not
touched), enables the gateway and exactly the sources named with
`--enable-source`, and writes the secret once to `--credential-out`, an
owner-only file the gateway reads as protected configuration. The secret is
never printed or logged; output names the selector only. Import leaves the
gateway and every source disabled; no upload ever enables one (questions-1 Q2).

Other steps: `revoke --selector`, `enable-gateway`, `disable-gateway`,
`enable-source --source`, `disable-source --source`. Each is recorded as a
`gateway_access_event`.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Sequence

from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.evidence.composition import build_gateway_access, write_gateway_credential_file
from assetops_backend.evidence.gateway_access import ProvisioningRefused, new_credential, redact
from assetops_backend.evidence.ledger import LedgerUnavailable


def main(argv: Sequence[str] | None = None, *, store=None, now=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.evidence.provision_gateway")
    parser.add_argument("step", choices=["issue", "revoke", "enable-gateway", "disable-gateway",
                                         "enable-source", "disable-source"])
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--site", required=True)
    parser.add_argument("--gateway", required=True)
    parser.add_argument("--enable-source", action="append", default=[])
    parser.add_argument("--source")
    parser.add_argument("--selector")
    parser.add_argument("--credential-out")
    parser.add_argument("--cadence-seconds", type=int)
    parser.add_argument("--actor", default=os.environ.get("USERNAME") or os.environ.get("USER") or "operator")
    args = parser.parse_args(argv)
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    access = build_gateway_access(database_url()) if store is None else store
    at = now or datetime.now(timezone.utc)
    ref = (args.tenant, args.site, args.gateway)
    try:
        if args.step == "issue":
            if not args.credential_out:
                print("issue needs --credential-out (the gateway's protected credential file).", file=sys.stderr)
                return 2
            issued = new_credential()
            revoked = access.issue_credential(*ref, issued, actor=args.actor, at=at)
            # The verifier is committed first; the secret then goes only to the
            # protected file, and enablement follows, so a gateway is never enabled
            # with a credential nobody holds. A failed file write leaves the gateway
            # without a usable credential; re-run issue (rotation is idempotent).
            write_gateway_credential_file(args.credential_out, issued.token)
            access.set_gateway_enabled(*ref, True, actor=args.actor, at=at, cadence_seconds=args.cadence_seconds)
            for source in args.enable_source:
                access.set_source_enabled(*ref, source, True, actor=args.actor, at=at)
            print(f"Issued {redact(issued.token)} for gateway {args.gateway!r}; revoked {len(revoked)} earlier "
                  f"credential(s); enabled the gateway and {len(args.enable_source)} named source(s). "
                  f"The secret was written only to {args.credential_out}.")
        elif args.step == "revoke":
            if not args.selector:
                print("revoke needs --selector.", file=sys.stderr)
                return 2
            done = access.revoke_credential(*ref, args.selector, actor=args.actor, at=at)
            print("Revoked." if done else "No active credential with that selector; nothing changed.")
        elif args.step in ("enable-gateway", "disable-gateway"):
            access.set_gateway_enabled(*ref, args.step == "enable-gateway", actor=args.actor, at=at,
                                       cadence_seconds=args.cadence_seconds)
            print(f"Gateway {args.gateway!r} {args.step.split('-')[0]}d.")
        else:
            if not args.source:
                print(f"{args.step} needs --source.", file=sys.stderr)
                return 2
            access.set_source_enabled(*ref, args.source, args.step == "enable-source", actor=args.actor, at=at)
            print(f"Source {args.source!r} {args.step.split('-')[0]}d.")
    except ProvisioningRefused as error:
        print(f"Refused; nothing was written for this step. {error}", file=sys.stderr)
        return 2
    except LedgerUnavailable as error:
        print(f"Provisioning failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
