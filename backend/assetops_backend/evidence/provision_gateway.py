"""Operator provisioning of a registered gateway's upload credential (S2-02 phase 2).

    python -m assetops_backend.evidence.provision_gateway issue --tenant demo \
        --site KOBO-001 --gateway edge-kobo-01 --enable-source <source external id> ... \
        --credential-out var/gateway/upload-credential

Run with `DATABASE_URL` set and the database migrated to 0006.

`issue` generates a fresh high-entropy bearer credential, stores only its
selector and one-way verifier, revokes every earlier credential of the gateway
(rotation: the old one stops working on the next request; sealed bytes are not
touched), enables the gateway and exactly the sources named with
`--enable-source`, and writes the secret once to a NEW unique versioned file
`<credential-out>.<selector>`, an owner-only file the gateway reads as
protected configuration. Order (Q8, Q16): the secret is written to that path,
restricted to the current user, made durable and verified (Windows DACL or POSIX
mode); only then are the verifier, revocation and enablement committed in one
transaction. That versioned file is the final credential path: nothing is
renamed or overwritten afterwards, and the file at `--credential-out` (or any
earlier versioned file) is left untouched. The output names the new path; the
operator switches the gateway's `upload_credential_file` to it before the next
upload (the earlier credential is revoked at once). A file/ACL failure before
the transaction, or a refusal inside it, removes only the new unissued file,
leaving the earlier credential usable and no identity more enabled. A database
error whose COMMIT outcome is unknown keeps the new file and reconciles by a
fresh database read (Architect Q28): committed -> issued; no row with the new
selector -> proven non-commit, the unissued file is removed; unreadable or
inconsistent -> `ISSUE_OUTCOME_UNKNOWN` (exit 3), the file is kept and rotation
halts for operator reconciliation. Nothing is ever blindly reissued. The secret is
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
            # Q8/Q16 order: the secret goes to a NEW unique versioned path, restricted,
            # durable and verified owner-only (Windows DACL or POSIX mode) BEFORE
            # anything is committed. That path is the final issued credential; the
            # configured file (the old usable secret) is never touched.
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
            except ProvisioningRefused:
                # Raised inside the transaction before COMMIT: a proven rollback.
                discard_gateway_credential_file(prepared)  # only the new, unissued file
                raise
            except Exception as error:  # noqa: BLE001 - the COMMIT outcome is unknown (Q28)
                outcome = _reconcile_issue(access, ref, issued, args.enable_source)
                if outcome == "NOT_ISSUED":
                    discard_gateway_credential_file(prepared)  # proven non-commit: only the new file
                    print(f"Provisioning failed: {error}. A fresh database read shows the new credential was "
                          "not committed; its unissued file was removed. Nothing about the earlier credential "
                          "is asserted here: check it before relying on it.", file=sys.stderr)
                    return 1
                if outcome != "ISSUED":
                    print(f"ISSUE_OUTCOME_UNKNOWN: {error}. Whether the new credential was committed cannot be "
                          f"established. Its protected file was KEPT at {prepared} (it may hold the only usable "
                          "secret). Halt rotation: do not issue again and do not delete that file until an "
                          "operator has reconciled the gateway's active credential in the database.",
                          file=sys.stderr)
                    return 3
                revoked = None  # committed; the response was lost, so the revoked count is unknown
                print(f"The issue response was lost ({error}); a fresh database read shows it was committed.")
            revoked_text = "every earlier" if revoked is None else f"{len(revoked)} earlier"
            print(f"Issued {redact(issued.token)} for gateway {args.gateway!r}; revoked {revoked_text} "
                  f"credential(s); enabled the gateway and {len(args.enable_source)} named source(s). "
                  f"The secret was written only to {prepared}, verified readable by the current user only. "
                  "Set the gateway's upload_credential_file to that path before its next upload; the earlier "
                  "credential file was left untouched and its credential no longer authenticates.")
            print(f"Credential file: {prepared}")
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


def _reconcile_issue(access, ref, issued, enable_sources) -> str:
    """`ISSUED`, `NOT_ISSUED`, or `UNKNOWN` (also when the database still cannot be read)."""
    try:
        return access.issue_outcome(*ref, issued, enable_sources)
    except Exception:  # noqa: BLE001 - unreadable means unknown, never a guessed rollback
        return "UNKNOWN"


if __name__ == "__main__":
    raise SystemExit(main())
