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
owner-only file the gateway reads as protected configuration. Order (Q8): the
secret is first written to a new versioned path `<credential-out>.<selector>`,
restricted to the current user and verified (Windows DACL or POSIX mode); only
then are the verifier, revocation and enablement committed in one transaction;
finally the file is renamed onto `--credential-out`. A file/ACL or database
failure before that commit leaves the earlier credential usable and no identity
more enabled. The secret is
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
from assetops_backend.evidence.composition import (
    CredentialFileRefused,
    activate_gateway_credential_file,
    build_gateway_access,
    discard_gateway_credential_file,
    prepare_gateway_credential_file,
)
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
            # Q8 order: the secret goes to a NEW versioned path, restricted and
            # verified owner-only (Windows DACL or POSIX mode) BEFORE anything is
            # committed; the configured file (the old usable secret) is not touched.
            try:
                prepared = prepare_gateway_credential_file(args.credential_out, issued.selector, issued.token)
            except CredentialFileRefused as error:
                print(f"Refused; nothing was committed and the earlier credential remains usable. {error}",
                      file=sys.stderr)
                return 2
            # One transaction: verifier, revocation of earlier credentials, gateway and
            # named-source enablement. A refusal rolls all of it back.
            try:
                revoked = access.issue_credential(*ref, issued, actor=args.actor, at=at,
                                                  enable_sources=args.enable_source,
                                                  cadence_seconds=args.cadence_seconds)
            except BaseException:
                discard_gateway_credential_file(prepared)
                raise
            try:
                active = activate_gateway_credential_file(prepared, args.credential_out)
            except CredentialFileRefused as error:
                print(f"Issued {redact(issued.token)} and revoked {len(revoked)} earlier credential(s), but the "
                      f"configured file could not be replaced ({error}). The new credential is in {prepared}; "
                      f"point the gateway's upload_credential_file at it.", file=sys.stderr)
                return 3
            print(f"Issued {redact(issued.token)} for gateway {args.gateway!r}; revoked {len(revoked)} earlier "
                  f"credential(s); enabled the gateway and {len(args.enable_source)} named source(s). "
                  f"The secret was written only to {active}, verified readable by the current user only.")
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
