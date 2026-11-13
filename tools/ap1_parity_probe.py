"""AP-1 parity probe (D-SR.75 "Parity against the file-backed version"). Run ONLY on a scratch clone DB.

Reads Kobo's file-backed declaration straight from the file stores (bypassing LegacySiteGate inside this probe
only) and the stored declaration from the clone, then prints a JSON comparison:
- per requirement `available` (by role, device, signal): must match;
- readiness level, ceiling and coverage-gap roles: may differ (dispatch-2 vs 3.2); each difference is listed for
  classification (model change, cohort rule, record only in one store) in the parity report;
- the stored read's unwarmed wall time (D-WARM.2: <= 2 s stays unstored).

    DATABASE_URL=<scratch clone url> python tools/ap1_parity_probe.py KOBO-001 > .agent/AP-1-parity-kobo.json
"""

from __future__ import annotations

import json
import sys
import time

from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
from assetops_backend.analytics.composition import build_assessment_store
from assetops_backend.analytics.declaration import applicable, site_declaration
from assetops_backend.analytics.service import AssessmentService
from assetops_backend.analytics.stored_declaration import stored_site_declaration
from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.evidence.composition import build_evidence_store
from assetops_backend.evidence.service import system_clock
from assetops_backend.sites.composition import build_foundation_store, build_site_repository
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_service import FoundationService, utc_now


def main(code: str) -> None:
    url = database_url()
    legacy = build_site_repository()  # the ungated legacy repository: file side read directly (probe only)
    evidence = build_evidence_store()
    service = AssessmentService(evidence, build_assessment_store(persistent=True), legacy.get_site, system_clock)
    site = legacy.get_site(code)
    active = service.dispatch(code) if applicable(site.site_type) else None
    pairs = {} if active is None else {
        active["analytic_id"]: [(a["assessment_id"], a["assessment"]) for a in active["assessments"]]}
    file_side = site_declaration(site, evidence.load_site(code), pairs)

    scope = ImportedSiteRegistry(FoundationService(build_foundation_store(url), DEVELOPMENT_TENANT_SLUG,
                                                   utc_now)).ledger_scope(code)
    if scope is None:
        raise SystemExit(f"{code} is not a stored Site in this database")
    store = PostgresAssessmentStore(url)
    started = time.perf_counter()
    stored_side = stored_site_declaration(store, scope[1], scope[2], scope[0])
    seconds = time.perf_counter() - started

    def avail(body):
        return {f"{r['role']}|{r['device_id']}|{r['signal_id']}": r["available"]
                for a in body["analytics"] for r in (*a["required_evidence"], *a["optional_evidence"])}

    def score(body):
        return [{"level": a["readiness"]["level"], "ceiling": a["readiness"]["claim_ceiling"]["claim_level"],
                 "gaps": sorted(f"{g['kind']}:{g['role']}" for g in a["readiness"]["missing_evidence"]),
                 "assessed_intervals": a["readiness"]["assessed_intervals"]} for a in body["analytics"]]

    fa, sa = avail(file_side), avail(stored_side)
    print(json.dumps({
        "site": code, "stored_read_seconds_unwarmed": round(seconds, 3),
        "available_mismatch": {k: [fa.get(k), sa.get(k)] for k in sorted(set(fa) | set(sa)) if fa.get(k) != sa.get(k)},
        "file_score": score(file_side), "stored_score": score(stored_side),
    }, indent=2, default=str))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "KOBO-001")
