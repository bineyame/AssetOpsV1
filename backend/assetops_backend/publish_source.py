"""S4-05a phase 1: server-side command that publishes one authored fixture batch before its upload.

    python -m assetops_backend.publish_source --site KOBO-001 --fixture-id assetops.s4-power-demo-cases \\
        --fixture-version 1 --batch-file <sealed Batch V2>

The authority is the server's own SYSTEM principal (`FIXTURE_PUBLISHER`); no flag names an actor, basis,
channel, digest or source class. The digest is recomputed from the file's canonical Batch V2 bytes. The batch
must name the requested Site and must not have been admitted yet. There is no HTTP route for this command.
Registered-simulation batches are published from the Lab release step (`runs/source_publication.py`).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence
from uuid import UUID

from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.evidence.composition import build_authored_fixture_specs, build_evidence_ledger
from assetops_backend.evidence.ledger import LedgerUnavailable
from assetops_backend.evidence.publication import FixtureSpecs, PublicationRefused, authored_record


def main(argv: Sequence[str] | None = None, *, ledger=None, specs: FixtureSpecs | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.publish_source")
    parser.add_argument("--tenant", default=DEVELOPMENT_TENANT_SLUG)
    parser.add_argument("--site", required=True)
    parser.add_argument("--fixture-id", required=True)
    parser.add_argument("--fixture-version", required=True)
    parser.add_argument("--batch-file", required=True)
    parser.add_argument("--publication-id")
    args = parser.parse_args(argv)
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    ledger = build_evidence_ledger(database_url()) if ledger is None else ledger
    specs = build_authored_fixture_specs() if specs is None else specs
    try:
        scope = ledger.site_scope(args.tenant, args.site)
        if scope is None:
            print(f"No imported Site {args.site!r} in tenant {args.tenant!r}; nothing was written.", file=sys.stderr)
            return 2
        tenant_id, site_id = scope
        try:
            record = authored_record(
                specs, tenant_id, Path(args.batch_file).read_text(encoding="utf-8"), fixture_id=args.fixture_id,
                fixture_version=args.fixture_version,
                publication_id=UUID(args.publication_id) if args.publication_id else None)
            if record.site_id != site_id:
                raise PublicationRefused("SITE_MISMATCH", f"the batch names another Site than {args.site}")
            outcome = ledger.register_publication(record)
        except PublicationRefused as error:
            print(f"Publication refused ({error.kind}): {error.detail}. Nothing was written.", file=sys.stderr)
            return 3
        state = "published" if outcome.created else "already published (identical)"
        print(f"{args.site} batch {record.external_batch_id} {state}: publication {outcome.publication_id}")
        return 0
    except LedgerUnavailable as error:
        print(f"Evidence ledger unavailable; nothing was written. {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
