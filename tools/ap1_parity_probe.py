"""AP-1 parity probe (D-SR.75 "Parity against the file-backed version"). Run ONLY on a scratch clone DB.

Reads Kobo's file-backed declaration straight from the file stores (bypassing LegacySiteGate inside this probe
only) and the stored declaration from the clone, then prints a JSON comparison:
- per requirement `available`, keyed by role (and by feeder for Load): must match (pass rule: role-keyed
  `available_mismatch` empty, D-SR.79 L3). Device/signal id differences, including D-SR.78 null ids for unbound
  roles, are listed apart under `id_differences` and are not a mismatch;
- readiness level, ceiling and coverage-gap roles: may differ (dispatch-2 vs 3.2); each difference is listed for
  classification (model change, cohort rule, record only in one store) in the parity report;
- the stored read's unwarmed wall time (D-WARM.2: <= 2 s stays unstored);
- a selected revision of an unmapped model is recorded as `{"refused": "UNSUPPORTED_RULE_VERSION", ...}`
  (D-SR.78 Q3) instead of aborting.
The probe writes nothing: the file-side assessments are recomputed in memory (`persistent=False`).

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
from assetops_backend.analytics.stored_declaration import UnsupportedModel, stored_site_declaration
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
    service = AssessmentService(evidence, build_assessment_store(persistent=False), legacy.get_site, system_clock)
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
    try:
        stored_side = stored_site_declaration(store, scope[1], scope[2], scope[0])
    except UnsupportedModel as error:
        print(json.dumps({"site": code, "stored_read_seconds_unwarmed": round(time.perf_counter() - started, 3),
                          "refused": "UNSUPPORTED_RULE_VERSION", "revision": error.revision,
                          "model": error.model, "message": str(error)}, indent=2, default=str))
        return
    seconds = time.perf_counter() - started

    def rows(body):
        return [r for a in body["analytics"] for r in (*a["required_evidence"], *a["optional_evidence"])]

    def ids(body):
        out: dict[str, list[str]] = {}
        for r in rows(body):
            out.setdefault(r["role"], []).append(f"{r['device_id']}|{r['signal_id']}")
        return {role: sorted(v) for role, v in out.items()}

    file_ids, stored_ids = ids(file_side), ids(stored_side)

    def avail(body):
        """Role -> available (any row); Load per feeder: by feeder id when both sides bind the same feeders,
        else by feeder position (the ids then appear under `id_differences`)."""
        out: dict[str, bool] = {}
        same_feeders = file_ids.get("Load") == stored_ids.get("Load")
        loads = sorted((r for r in rows(body) if r["role"] == "Load"), key=lambda r: str(r["device_id"]))
        for i, r in enumerate(loads):
            out[f"Load|{r['device_id'] if same_feeders else f'feeder {i + 1}'}"] = r["available"]
        for r in rows(body):
            if r["role"] != "Load":
                out[r["role"]] = out.get(r["role"], False) or r["available"]
        return out

    def score(body):
        return [{"level": a["readiness"]["level"], "ceiling": a["readiness"]["claim_ceiling"]["claim_level"],
                 "gaps": sorted(f"{g['kind']}:{g['role']}" for g in a["readiness"]["missing_evidence"]),
                 "assessed_intervals": a["readiness"]["assessed_intervals"]} for a in body["analytics"]]

    fa, sa = avail(file_side), avail(stored_side)
    print(json.dumps({
        "site": code, "stored_read_seconds_unwarmed": round(seconds, 3),
        "available_mismatch": {k: [fa.get(k), sa.get(k)] for k in sorted(set(fa) | set(sa)) if fa.get(k) != sa.get(k)},
        "id_differences": {role: {"file": file_ids.get(role), "stored": stored_ids.get(role)}
                           for role in sorted(set(file_ids) | set(stored_ids)) if file_ids.get(role) != stored_ids.get(role)},
        "file_score": score(file_side), "stored_score": score(stored_side),
    }, indent=2, default=str))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "KOBO-001")
