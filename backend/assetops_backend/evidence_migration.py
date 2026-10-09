"""The explicit legacy evidence comparison CLI (S2-02 phase 3a, item 5).

    python -m assetops_backend.evidence_migration run --tenant demo --site KOBO-001
    python -m assetops_backend.evidence_migration show --site KOBO-001

`run` reads the Site's legacy file-backed evidence, dry-runs every stored
envelope through the legacy V1 parser, compares with the central ledger's
accepted envelopes by message ID, copies file-saved `dispatch` claims and the
ledger's recompute jobs as S3 fixtures, and writes one new immutable report.
It writes nothing to Postgres and changes no legacy store. Exit 0 when the
report is PASSED, 1 for EXCEPTIONS/FAILED, 2 when the Site cannot be compared.

A top-level composition module (like `serve_tls.py`) because it reads both the
evidence and the analytics stores; the evidence package may not import analytics.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Sequence

from assetops_backend.analytics.composition import build_assessment_store
from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.evidence.composition import (
    build_comparison_reports,
    build_evidence_ledger,
    build_evidence_store,
)
from assetops_backend.evidence.ledger import LedgerUnavailable
from assetops_backend.evidence.legacy_comparison import (
    compare,
    environment_identity,
    legacy_inventory,
    permits_cutover,
)
from assetops_backend.evidence.models import SiteEvidence
from assetops_backend.evidence.ports import EvidenceStoreUnavailable
from assetops_backend.runs.commit_ports import CommitStoreError
from assetops_backend.runs.composition import build_commit_store
from assetops_backend.sites.identity import site_id_key


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _jsonable(value):
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _legacy_evidence(store, site_code: str) -> SiteEvidence:
    for stored in store.list_sites():
        if site_id_key(stored) == site_id_key(site_code):
            return store.load_site(stored)
    return SiteEvidence(site_id=site_code)


def committed_artifacts(commit_store, site_code: str) -> list[tuple[str, str]]:
    """The Site's committed artifacts for the inventory; unreadable -> EvidenceStoreUnavailable."""
    try:
        return commit_store.site_artifacts(site_id_key(site_code))
    except CommitStoreError as error:
        raise EvidenceStoreUnavailable(f"the committed artifacts could not be read: {error}") from error


def current_legacy_inventory(evidence_store, commit_store, site_code: str) -> dict:
    """`legacy_inventory` of the Site's CURRENT legacy input (Q14). Raises
    `EvidenceStoreUnavailable` when any of it cannot be read, so the gate closes."""
    legacy = _legacy_evidence(evidence_store, site_code)
    return legacy_inventory(legacy, committed_artifacts(commit_store, site_code))


def _dispatch_claims(assessments, site_code: str) -> list[dict]:
    history = assessments.load_history(site_code)
    return [_jsonable(asdict(lineage)) for lineage in history.lineages if lineage.analytic_id == "dispatch"]


def main(argv: Sequence[str] | None = None, *, evidence_store=None, ledger=None, reports=None,
         assessments=None, now=None, commit_store=None, environment=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.evidence_migration")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="compare and write a new immutable report")
    run.add_argument("--tenant", required=True)
    run.add_argument("--site", required=True)
    show = commands.add_parser("show", help="print the newest report's outcome")
    show.add_argument("--site", required=True)
    args = parser.parse_args(argv)
    reports = build_comparison_reports() if reports is None else reports

    if args.command == "show":
        report = reports.latest(args.site)
        if report is None:
            print(f"No comparison report exists for {args.site}.")
            return 2
        print(json.dumps({k: report.get(k) for k in ("report_id", "outcome", "empty_set", "statement",
                                                     "compared_at")}, indent=2))
        return 0 if report.get("outcome") == "PASSED" else 1

    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    environment = environment_identity(database_url()) if environment is None else environment
    if environment is None:
        print("DATABASE_URL names no database; a comparison is scoped to the active environment.",
              file=sys.stderr)
        return 2
    ledger = build_evidence_ledger(database_url()) if ledger is None else ledger
    store = build_evidence_store() if evidence_store is None else evidence_store
    commits = build_commit_store() if commit_store is None else commit_store
    assessments = build_assessment_store() if assessments is None else assessments
    try:
        scope = ledger.site_scope(args.tenant, args.site)
        if scope is None:
            print(f"Site {args.site!r} is not registered in tenant {args.tenant!r}.", file=sys.stderr)
            return 2
        tenant_id, site_id = scope
        legacy = _legacy_evidence(store, args.site)
        report = compare(
            site_code=args.site, tenant_id=tenant_id, site_id=site_id, legacy=legacy,
            ledger_digests=ledger.message_digests(tenant_id, site_id, [r.message_id for r in legacy.records]),
            bound_channels=ledger.bound_channels(tenant_id, site_id),
            legacy_dispatch_claims=_dispatch_claims(assessments, args.site),
            recompute_jobs=_jsonable(ledger.dispatch_jobs(tenant_id, site_id)),
            compared_at=(now or _now)(),
            committed_artifacts=committed_artifacts(commits, args.site),
            environment=environment,
        )
    except (LedgerUnavailable, EvidenceStoreUnavailable) as error:
        print(f"The comparison could not read its stores: {error}", file=sys.stderr)
        return 2
    path = reports.write(report)
    allowed, reason = permits_cutover(report, args.site, site_id, tenant_id=tenant_id, environment=environment,
                                      inventory=report["legacy_inventory"])
    print(f"{report['outcome']}: {report['statement']}")
    print(f"Report: {path}")
    print("Evidence cutover: " + ("permitted" if allowed else f"closed. {reason}"))
    return 0 if report["outcome"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
