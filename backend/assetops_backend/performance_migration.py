"""The explicit S3-01 Performance comparison: file-backed dispatch claims vs selected dispatch-3 revisions.

    python -m assetops_backend.performance_migration run --tenant demo --site KOBO-001
    python -m assetops_backend.performance_migration show --site KOBO-001

Writes one immutable report per run; the newest decides the imported Site's
Postgres Performance read cutover (`analytics/performance_comparison.py`).
The file-backed baseline is read only.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Sequence

from assetops_backend.analytics.composition import build_assessment_store, build_lineage_reader
from assetops_backend.analytics.performance_comparison import compare, permits_performance_cutover
from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.evidence.composition import build_evidence_ledger, build_performance_comparison_reports
from assetops_backend.evidence.legacy_comparison import environment_identity

ANALYTIC_ID = "dispatch"


def legacy_dispatch_claims(assessments, site_code: str) -> list[dict]:
    history = assessments.load_history(site_code)
    return [json.loads(json.dumps(asdict(x), default=str)) for x in history.lineages if x.analytic_id == ANALYTIC_ID]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.performance_migration")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="compare and write a new immutable report")
    run.add_argument("--tenant", required=True)
    run.add_argument("--site", required=True)
    show = commands.add_parser("show", help="print the newest report's outcome")
    show.add_argument("--site", required=True)
    args = parser.parse_args(argv)
    reports = build_performance_comparison_reports()
    if args.command == "show":
        report = reports.latest(args.site)
        if report is None:
            print(f"No Performance comparison report exists for {args.site}.")
            return 2
        print(json.dumps({k: report.get(k) for k in ("report_id", "outcome", "empty_set", "statement", "counts",
                                                     "lineage_breaks", "compared_at")}, indent=2))
        return 0 if report.get("outcome") == "PASSED" else 1
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    environment = environment_identity(database_url())
    if environment is None:
        print("DATABASE_URL names no database; a comparison is scoped to the active environment.", file=sys.stderr)
        return 2
    scope = build_evidence_ledger(database_url()).site_scope(args.tenant, args.site)
    if scope is None:
        print(f"Site {args.site!r} is not registered in tenant {args.tenant!r}.", file=sys.stderr)
        return 2
    tenant_id, site_id = scope
    claims = legacy_dispatch_claims(build_assessment_store(), args.site)
    store = build_lineage_reader(database_url())
    cited = sorted({m for c in claims for m in (c["revisions"][-1]["assessment"].get("evidence_basis") or {})
                    .get("message_ids", [])})
    report = compare(site_code=args.site, tenant_id=str(tenant_id), site_id=str(site_id), environment=environment,
                     legacy_claims=claims, accepted_message_ids=store.accepted_message_ids(tenant_id, site_id, cited),
                     intervals=store.selected_intervals(tenant_id, site_id, ANALYTIC_ID),
                     lineage=store.lineage_breaks(tenant_id, site_id, ANALYTIC_ID),
                     compared_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    path = reports.write(json.loads(json.dumps(report, default=str)))
    allowed, reason = permits_performance_cutover(
        report, args.site, str(site_id), tenant_id=str(tenant_id), environment=environment, legacy_claims=claims,
        live_lineage=store.lineage_breaks(tenant_id, site_id, ANALYTIC_ID))
    print(f"{report['outcome']}: {report['statement']}")
    print(f"Lineage: {report['lineage']}")
    print(f"Report: {path}")
    print("Performance cutover: " + ("permitted" if allowed else f"closed. {reason}"))
    return 0 if report["outcome"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
