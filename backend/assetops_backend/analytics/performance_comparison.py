"""File-backed dispatch-claim comparison and the Postgres Performance read cutover gate (S3-01 phase 3).

Representative public-record dispatch claims from the read-only file-backed
baseline (`dispatch-2` lineages) are compared with the selected `dispatch-3`
interval revisions before an imported Site's Performance read switches to
Postgres. Each legacy claim is one of:

- MATCH: its cited records are accepted centrally and the selected dispatch-3
  interval over the same running span has the same claim level;
- INTENTIONAL_DELTA: same sources, and dispatch-3 is Indeterminate with named
  window limitations (it fails closed where public roles/controls are missing:
  `dispatch_3_decision_table.md` rows 5a/5b/6);
- MISSING_SOURCE: a cited record is not accepted centrally (a migration
  exception; never fabricated);
- UNPROVEN: anything else, including no selected dispatch-3 interval.

Outcome FAILED on any UNPROVEN claim or lineage break, EXCEPTIONS on any
MISSING_SOURCE, else PASSED. The gate opens only on PASSED, a current legacy
claim digest, the same tenant/Site/environment, and zero live lineage breaks
(fail-closed default; `.agent/S3-01-questions-3.md`).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import uuid4

SCHEMA = "s3-performance-comparison-v1"


def claims_digest(claims: list[dict]) -> str:
    return hashlib.sha256(json.dumps(claims, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _span(interval: dict) -> tuple[str, str] | None:
    lo, hi = interval.get("first_running_observed"), interval.get("last_running_observed")
    return None if not lo or not hi else (lo, hi)


def _pg_span(revision: dict) -> tuple[str, str] | None:
    interval = (revision.get("result") or {}).get("interval") or {}
    lo = interval.get("first_on") or interval.get("first_running_observed")
    hi = interval.get("last_on") or interval.get("last_running_observed")
    return None if not lo or not hi else (str(lo), str(hi))


def _iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def classify(claim: dict, accepted_message_ids: set[str], intervals: list[dict]) -> dict:
    latest = claim["revisions"][-1]
    assessment = latest["assessment"]
    cited = sorted(set((assessment.get("evidence_basis") or {}).get("message_ids") or []))
    out = {"legacy_assessment_id": claim["assessment_id"], "legacy_revision": latest.get("revision"),
           "legacy_model_version": latest.get("model_version"), "legacy_claim": assessment.get("claim_level"),
           "legacy_span": _span(assessment.get("interval") or {}), "cited_message_ids": len(cited)}
    missing = [m for m in cited if m not in accepted_message_ids]
    if missing or not cited:
        return {**out, "class": "MISSING_SOURCE", "missing_message_ids": missing,
                "reason": "cited source records are not accepted centrally" if cited else "the claim cites no record"}
    span = out["legacy_span"]
    hits = [] if span is None else [r for r in intervals if (s := _pg_span(r)) is not None
                                    and _iso(s[0]) <= _iso(span[1]) and _iso(span[0]) <= _iso(s[1])]
    if len(hits) != 1:
        return {**out, "class": "UNPROVEN", "postgres_revision_ids": [str(r["id"]) for r in hits],
                "reason": f"{len(hits)} selected dispatch-3 intervals overlap the legacy running span"}
    hit = hits[0]
    out.update({"postgres_revision_id": str(hit["id"]), "postgres_claim": hit["claim_level"]})
    if hit["claim_level"] == out["legacy_claim"]:
        return {**out, "class": "MATCH"}
    if hit["claim_level"] == "INDETERMINATE" and hit.get("window_limitations"):
        return {**out, "class": "INTENTIONAL_DELTA", "reason": "dispatch-3 fails closed with named limitations: "
                + "; ".join(hit["window_limitations"][:3])}
    return {**out, "class": "UNPROVEN", "reason": "claim levels differ without a documented dispatch-3 delta"}


def compare(*, site_code: str, tenant_id: str, site_id: str, environment: str, legacy_claims: list[dict],
            accepted_message_ids: set[str], intervals: list[dict], lineage: dict[str, int],
            compared_at: str) -> dict[str, Any]:
    rows = [classify(c, accepted_message_ids, intervals) for c in legacy_claims]
    count = {k: sum(1 for r in rows if r["class"] == k)
             for k in ("MATCH", "INTENTIONAL_DELTA", "MISSING_SOURCE", "UNPROVEN")}
    breaks = {k: v for k, v in lineage.items() if k != "selected_runs" and v}
    outcome = "FAILED" if count["UNPROVEN"] or breaks else ("EXCEPTIONS" if count["MISSING_SOURCE"] else "PASSED")
    empty = not legacy_claims
    statement = (f"Empty-set comparison: the file-backed baseline holds no dispatch claim for {site_code}, so no "
                 "claim is said to match." if empty else
                 f"{len(rows)} file-backed dispatch claims: " + ", ".join(f"{v} {k}" for k, v in count.items()))
    return {"schema": SCHEMA, "report_id": str(uuid4()), "site_id": site_code, "site_uuid": site_id,
            "tenant_id": tenant_id, "environment": environment, "compared_at": compared_at, "outcome": outcome,
            "empty_set": empty, "statement": statement, "legacy_claims_sha256": claims_digest(legacy_claims),
            "counts": count, "claims": rows, "lineage": lineage, "lineage_breaks": breaks,
            "selected_postgres_intervals": len(intervals)}


def permits_performance_cutover(report: dict | None, site_code: str, site_id: str, *, tenant_id: str,
                                environment: str | None, legacy_claims: list[dict],
                                live_lineage: dict[str, int] | None) -> tuple[bool, str]:
    if report is None:
        return False, "No Performance comparison report exists for this Site; the file-backed comparison must run."
    if report.get("schema") != SCHEMA or report.get("site_uuid") != site_id or report.get("site_id") != site_code:
        return False, "The newest Performance comparison report names another schema or Site."
    if report.get("tenant_id") != tenant_id or environment is None or report.get("environment") != environment:
        return False, "The newest Performance comparison report was made for another tenant or environment."
    if report.get("outcome") != "PASSED":
        return False, f"The newest Performance comparison report is {report.get('outcome')}: {report.get('statement')}"
    if report.get("legacy_claims_sha256") != claims_digest(legacy_claims):
        return False, "The file-backed dispatch claims changed after the comparison; rerun it."
    if live_lineage is None:
        return False, "The assessment lineage could not be read."
    breaks = {k: v for k, v in live_lineage.items() if k != "selected_runs" and v}
    if breaks:
        return False, f"Assessment lineage is broken: {breaks}"
    return True, report["statement"]
