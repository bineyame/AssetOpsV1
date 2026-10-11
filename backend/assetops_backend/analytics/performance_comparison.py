"""File-backed dispatch-claim comparison and the Postgres Performance read cutover gate (S3-01 phase 3).

Representative public-record dispatch claims from the read-only file-backed
baseline (`dispatch-2` lineages) are compared with the selected current-model
(`dispatch-3.1`) interval revisions before an imported Site's Performance read
switches to Postgres (`D-2026-10-11-s3-phase-3a-version-and-cutover`). Each
legacy claim is one of:

- MATCH: its cited records are accepted centrally and are all in the evidence
  of the one selected current-model interval over the same running span, which
  has no outstanding or failed recompute job and the same claim level;
- INTENTIONAL_DELTA: only through a `DOCUMENTED_DELTAS` entry: the claim change
  is the one that entry names, the selected interval itself (not the window)
  carries the entry's limitation, and every record the legacy claim cites is
  accepted and part of that interval's evidence (a comparable public basis);
- MISSING_SOURCE: a cited record is not accepted centrally (a migration
  exception; never fabricated, never parity);
- UNPROVEN: anything else, including no selected interval, a selected interval
  of another model version (STALE_MODEL), or an outstanding/failed job over the
  window (STALE_PROJECTION).

Outcome FAILED on any UNPROVEN claim or lineage break (a window still selected
under another model version counts as one), EXCEPTIONS on any MISSING_SOURCE,
else PASSED. The gate opens only on PASSED for the current model version, a
current legacy claim digest, the same tenant/Site/environment, and zero live
lineage breaks.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import uuid4

SCHEMA = "s3-performance-comparison-v2"

#: Claim-specific `dispatch-2` -> `dispatch-3.1` rule differences that may explain a claim mismatch
#: (`backend/tests/dispatch_3_decision_table.md`, "Comparison"). An entry applies only to its own claim
#: change and only when the selected interval's own segments name one of its limitations. No catch-all
#: entry (Architect Q11).
DOCUMENTED_DELTAS: tuple[dict[str, Any], ...] = (
    {"rule": "CAPABILITY_CHANNELS_REQUIRED", "table_rows": "5a/5b",
     "legacy_claims": ("CANDIDATE_AVOIDABLE",), "postgres_claims": ("INDETERMINATE",),
     "interval_limitations": ("PV available power: ", "PCS discharge capability: "),
     "explanation": "dispatch-2 inferred available PV and battery discharge from observed pv_power/battery_power; "
                    "dispatch-3.1 gives Candidate only from accepted pv_available_power and "
                    "pcs_discharge_capability channels (minigrid-roles-2), so without them the interval is "
                    "Indeterminate"},
)

_STALE_JOB = ("PENDING", "LEASED", "FAILED")


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


def _delta(claim_change: tuple[str, str], hit: dict) -> tuple[dict, list[str]] | None:
    segments = (hit.get("result") or {}).get("segments") or []
    named = sorted({m for seg in segments for m in seg.get("missing") or []})
    for entry in DOCUMENTED_DELTAS:
        if claim_change[0] not in entry["legacy_claims"] or claim_change[1] not in entry["postgres_claims"]:
            continue
        found = [m for m in named if m.startswith(entry["interval_limitations"])]
        if found:
            return entry, found
    return None


def classify(claim: dict, accepted_evidence: dict[str, str], intervals: list[dict], model_version: str) -> dict:
    latest = claim["revisions"][-1]
    assessment = latest["assessment"]
    cited = sorted(set((assessment.get("evidence_basis") or {}).get("message_ids") or []))
    out = {"legacy_assessment_id": claim["assessment_id"], "legacy_revision": latest.get("revision"),
           "legacy_model_version": latest.get("model_version"), "legacy_claim": assessment.get("claim_level"),
           "legacy_span": _span(assessment.get("interval") or {}), "cited_message_ids": len(cited)}
    missing = [m for m in cited if m not in accepted_evidence]
    if missing or not cited:
        return {**out, "class": "MISSING_SOURCE", "missing_message_ids": missing,
                "reason": "cited source records are not accepted centrally" if cited else "the claim cites no record"}
    span = out["legacy_span"]
    hits = [] if span is None else [r for r in intervals if (s := _pg_span(r)) is not None
                                    and _iso(s[0]) <= _iso(span[1]) and _iso(span[0]) <= _iso(s[1])]
    if len(hits) != 1:
        return {**out, "class": "UNPROVEN", "postgres_revision_ids": [str(r["id"]) for r in hits],
                "reason": f"{len(hits)} selected intervals overlap the legacy running span"}
    hit = hits[0]
    out.update({"postgres_revision_id": str(hit["id"]), "postgres_claim": hit["claim_level"],
                "postgres_model_version": hit.get("model_version")})
    if hit.get("model_version") != model_version:
        return {**out, "class": "UNPROVEN", "reason": f"STALE_MODEL: the selected interval was assessed by "
                f"{hit.get('model_version')}, the current model is {model_version}; reassessment is outstanding"}
    jobs = [j for j in hit.get("window_jobs") or [] if j.get("status") in _STALE_JOB]
    if jobs:
        return {**out, "class": "UNPROVEN", "reason": "STALE_PROJECTION: RECOMPUTE_OUTSTANDING over the selected "
                "window: " + ", ".join(f"job {j['id']} {j['status']}" for j in jobs)}
    compared = sorted(accepted_evidence[m] for m in cited)
    comparable = set(compared) <= {str(e) for e in hit.get("evidence_ids") or []}
    if hit["claim_level"] == out["legacy_claim"]:
        if not comparable:
            return {**out, "class": "UNPROVEN", "reason": "claim levels agree, but the records the legacy claim "
                    "cites are not all in the selected interval's evidence (no comparable basis)"}
        return {**out, "class": "MATCH", "compared_evidence_ids": compared}
    found = _delta((out["legacy_claim"], hit["claim_level"]), hit)
    if found is None:
        return {**out, "class": "UNPROVEN", "reason": f"claim levels differ and no documented dispatch-2 to "
                f"{model_version} rule difference names a limitation of this interval"}
    entry, named = found
    if not comparable:
        return {**out, "class": "UNPROVEN", "reason": f"{entry['rule']} would explain the change, but the records "
                "the legacy claim cites are not all in the selected interval's evidence (no comparable basis)"}
    return {**out, "class": "INTENTIONAL_DELTA", "rule": entry["rule"],
            "rule_change": {"from": "dispatch-2", "to": model_version, "table_rows": entry["table_rows"],
                            "explanation": entry["explanation"]},
            "interval_limitations": named, "compared_evidence_ids": compared,
            "reason": f"{entry['rule']} (table rows {entry['table_rows']}): " + "; ".join(named[:3])}


def compare(*, site_code: str, tenant_id: str, site_id: str, environment: str, legacy_claims: list[dict],
            accepted_evidence: dict[str, str], intervals: list[dict], lineage: dict[str, int],
            compared_at: str, model_version: str) -> dict[str, Any]:
    rows = [classify(c, accepted_evidence, intervals, model_version) for c in legacy_claims]
    count = {k: sum(1 for r in rows if r["class"] == k)
             for k in ("MATCH", "INTENTIONAL_DELTA", "MISSING_SOURCE", "UNPROVEN")}
    breaks = {k: v for k, v in lineage.items() if k != "selected_runs" and v}
    outcome = "FAILED" if count["UNPROVEN"] or breaks else ("EXCEPTIONS" if count["MISSING_SOURCE"] else "PASSED")
    empty = not legacy_claims
    statement = (f"Empty-set comparison: the file-backed baseline holds no dispatch claim for {site_code}, so no "
                 "claim is said to match; a zero-inventory statement, not claim parity." if empty else
                 f"{len(rows)} file-backed dispatch claims: " + ", ".join(f"{v} {k}" for k, v in count.items()))
    if breaks:
        statement += f" Lineage breaks: {breaks}."
    return {"schema": SCHEMA, "report_id": str(uuid4()), "site_id": site_code, "site_uuid": site_id,
            "tenant_id": tenant_id, "environment": environment, "compared_at": compared_at,
            "model_version": model_version, "outcome": outcome,
            "empty_set": empty, "statement": statement, "legacy_claims_sha256": claims_digest(legacy_claims),
            "counts": count, "claims": rows, "lineage": lineage, "lineage_breaks": breaks,
            "selected_postgres_intervals": len(intervals)}


def permits_performance_cutover(report: dict | None, site_code: str, site_id: str, *, tenant_id: str,
                                environment: str | None, legacy_claims: list[dict],
                                live_lineage: dict[str, int] | None, model_version: str) -> tuple[bool, str]:
    if report is None:
        return False, "No Performance comparison report exists for this Site; the file-backed comparison must run."
    if report.get("schema") != SCHEMA or report.get("site_uuid") != site_id or report.get("site_id") != site_code:
        return False, "The newest Performance comparison report names another schema or Site."
    if report.get("tenant_id") != tenant_id or environment is None or report.get("environment") != environment:
        return False, "The newest Performance comparison report was made for another tenant or environment."
    if report.get("model_version") != model_version:
        return False, (f"The newest Performance comparison report was made under another model version "
                       f"({report.get('model_version')}); the current model is {model_version}, so rerun it.")
    if report.get("outcome") != "PASSED":
        return False, f"The newest Performance comparison report is {report.get('outcome')}: {report.get('statement')}"
    if report.get("legacy_claims_sha256") != claims_digest(legacy_claims):
        return False, "The file-backed dispatch claims changed after the comparison; rerun it."
    if live_lineage is None:
        return False, "The assessment lineage could not be read."
    if live_lineage.get("selected_heads_other_model"):
        return False, (f"{live_lineage['selected_heads_other_model']} windows are still selected under another "
                       f"model version than {model_version}; reassessment is outstanding.")
    breaks = {k: v for k, v in live_lineage.items() if k != "selected_runs" and v}
    if breaks:
        return False, f"Assessment lineage is broken: {breaks}"
    return True, report["statement"]
