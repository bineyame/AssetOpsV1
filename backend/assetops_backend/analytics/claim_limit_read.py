"""S3-02a: selected-assessment capability readiness and claim-limit read (`I-capability-read`, `I-claim-limit-read`).

`D-2026-10-16-s302-capability` / `D-2026-10-16-w1-remaining-questions` (answer 4). For one Site, one half-open UTC
day and one exact S3 dispatch `assessment_revision_id`:

- Capability readiness is derived only from that revision's stored rule result (its segments) and its exact pinned
  accepted Evidence. Each required role gets exact COVERED / MISSING / POOR_QUALITY / CONFLICTED / NOT_EVALUATED
  spans with durations and the accepted Evidence IDs inside each span. A missing or conflicted subspan is never
  merged into a covered one. Latest readings, another day or another revision are never consulted, and configured
  capability (a Foundation or binding value) is never treated as observed capability.
- The claim limit maps the revision's dispatch classification to what the evidence supports under one versioned rule
  (`RULE_ID`): Candidate / Necessary / Indeterminate. A *current* positive ceiling needs the window's current
  selection (`CURRENT`) to contain this exact revision, a usable cohort, accepted lineage for every pinned Evidence ID
  and complete role coverage of the segments that carry the claim. Otherwise the result is UNASSESSED, PENDING,
  FAILED, STALE_PROJECTION or HISTORICAL with no current positive claim; the revision's own ceiling is still shown
  as `historical_ceiling`.
- Refusals (`ClaimLimitRefusal`): unknown/foreign revision 404, revision of another window 422
  `REVISION_OUTSIDE_WINDOW`, unsupported rule or model 422 `UNSUPPORTED_RULE_VERSION`, absent accepted lineage 409
  `ACCEPTED_LINEAGE_ABSENT`.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Protocol
from uuid import UUID

from assetops_backend.analytics import dispatch_v3
from assetops_backend.analytics.assessment_inputs import EvidenceQuery, EvidenceQueryResult
from assetops_backend.analytics.assessment_ports import WindowSnapshot
from assetops_backend.analytics.assessment_worker import DISPATCH_ROLES, DOMAIN, input_basis
from assetops_backend.analytics.dispatch import CANDIDATE, INDETERMINATE, NECESSARY
from assetops_backend.analytics.dispatch_read import CURRENT, OPEN_CUTOFF, UNASSESSED, day_window, derive_status

SCHEMA = "assetops.s3-claim-limit-read"
SCHEMA_VERSION = 1
RULE_ID = "s3-claim-limit-1"
#: Model versions whose stored segment vocabulary this rule maps. Any other model is refused, never guessed.
SUPPORTED_MODELS = ("dispatch-3.2",)
HISTORICAL = "HISTORICAL"
COVERED, MISSING, POOR, CONFLICTED, NOT_EVALUATED = (
    "COVERED", "MISSING", "POOR_QUALITY", "CONFLICTED", "NOT_EVALUATED")
GEN = dispatch_v3.GEN_STATE
LOAD, PV, DIS, SOC = dispatch_v3.LOAD, dispatch_v3.PV_AVAILABLE, dispatch_v3.DISCHARGE, dispatch_v3.SOC
#: Required roles of the rule: generator state plus every role an evaluated point reads.
REQUIRED_ROLES = (GEN, LOAD, PV, DIS, SOC)
#: Problem text (dispatch-3.2 `_PROBLEM_TEXT`) -> coverage status. Unknown text is not COVERED (fail closed).
_PROBLEM_STATUS = (
    ("not bound in the selected role set", MISSING), ("bound to more than one asset", MISSING),
    ("no accepted reading", MISSING), ("not configured", MISSING), ("reading not GOOD quality", POOR),
    ("contradictory readings at one time", CONFLICTED), ("reports out of sequence order or overlapping", CONFLICTED),
    ("SEQUENCE_ORDER_INVERTED", CONFLICTED), ("REPORTS_OVERLAP", CONFLICTED),
)
_LABEL_ROLE = {label: role for role, label in dispatch_v3.LABELS.items() if role in REQUIRED_ROLES}
#: Roles each Candidate branch of dispatch-3.2 needs (`_evaluate`): PV alone, or PV plus PCS with SOC.
_CANDIDATE_ROLES = {"PV available alone": (LOAD, PV, DIS), "PV available plus PCS": (LOAD, PV, DIS, SOC)}
NOT_INFERRED = ("No physical capacity is inferred: configured capability (Foundation or binding values) is not "
                "observed capability, and only the selected revision's accepted public readings are used.")

Evidence = dict[str, dict[str, Any]]  # evidence ID -> {"role", "at"} for exact pinned accepted Evidence


class ClaimLimitRefusal(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.detail = status, {"code": code, "message": message}


class ClaimLimitStore(Protocol):
    def claim_limit_snapshot(self, query: EvidenceQuery, analytic_id: str,
                             basis: Callable[[EvidenceQueryResult], tuple[str | None, str]],
                             revision_id: UUID | None) -> tuple[WindowSnapshot, dict[str, Any] | None]: ...


def _t(value: str | datetime | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _minutes(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 60


def _role_of(text: str) -> str | None:
    head = text.split(":", 1)[0]
    if head in _LABEL_ROLE:
        return _LABEL_ROLE[head]
    return head if head in REQUIRED_ROLES else None


def _status_of(text: str) -> str:
    for needle, status in _PROBLEM_STATUS:
        if needle in text:
            return status
    return MISSING  # an unrecognised problem is never read as coverage


def segment_roles(segment: dict[str, Any], evidence: Evidence) -> dict[str, tuple[str, list[str], list[str]]]:
    """Per required role: (status, problem texts, evidence IDs) for one stored dispatch-3.2 segment. Generator state
    readings are interval-level in the stored result, so they are matched to the segment by their placed time."""
    out: dict[str, tuple[str, list[str], list[str]]] = {}
    lo, hi = _t(segment["start"]), _t(segment["end"])
    ids = {str(e) for e in segment.get("evidence_ids", [])}
    ids |= {k for k, e in evidence.items() if e["role"] == GEN and e["at"] is not None and lo <= e["at"] <= hi}
    problems: dict[str, list[str]] = {}
    for text in segment.get("missing", []):
        role = _role_of(text)
        if role is not None:
            problems.setdefault(role, []).append(text)
    for role in REQUIRED_ROLES:
        mine = sorted(e for e in ids if evidence.get(e, {}).get("role") == role)
        if role == GEN:
            status = COVERED if segment.get("observed") else MISSING
            texts = [] if segment.get("observed") else [t for t in segment.get("missing", [])
                                                        if t.startswith("generator state")]
        elif not segment.get("observed"):
            status, texts = NOT_EVALUATED, ["generator state not observed: the point was not evaluated"]
        elif role in problems:
            statuses = {_status_of(t) for t in problems[role]}
            status = next(s for s in (CONFLICTED, POOR, MISSING) if s in statuses)
            texts = sorted(problems[role])
        else:
            status, texts = COVERED, []
        out[role] = (status, texts, mine)
    return out


def role_coverage(segments: list[dict[str, Any]], evidence: Evidence, revision_id: str) -> dict[str, Any]:
    """Exact per-role spans; adjacent spans merge only when their status is the same."""
    roles: dict[str, list[dict[str, Any]]] = {r: [] for r in REQUIRED_ROLES}
    for seg in segments:
        start, end = _t(seg["start"]), _t(seg["end"])
        for role, (status, texts, ids) in segment_roles(seg, evidence).items():
            spans = roles[role]
            if spans and spans[-1]["status"] == status and spans[-1]["_end"] == start:
                last = spans[-1]
                last["_end"], last["end"] = end, seg["end"]
                last["evidence_ids"] = sorted(set(last["evidence_ids"]) | set(ids))
                last["problems"] = sorted(set(last["problems"]) | set(texts))
            else:
                spans.append({"status": status, "start": seg["start"], "end": seg["end"], "_start": start,
                              "_end": end, "evidence_ids": ids, "problems": texts,
                              "assessment_revision_id": revision_id})
    out: dict[str, Any] = {}
    for role, spans in roles.items():
        totals: dict[str, float] = {}
        for s in spans:
            s["minutes"] = _minutes(s.pop("_start"), s.pop("_end"))
            totals[s["status"]] = totals.get(s["status"], 0.0) + s["minutes"]
        out[role] = {"spans": spans, "minutes_by_status": totals, "covered_minutes": totals.get(COVERED, 0.0),
                     "evidence_ids": sorted({e for s in spans for e in s["evidence_ids"]}),
                     "status": "NO_SPANS" if not spans else (
                         COVERED if all(s["status"] == COVERED for s in spans) else "INCOMPLETE")}
    return out


def _reasons(result: dict[str, Any], coverage: dict[str, Any], window_limits: list[str]) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    for role, item in coverage.items():
        for s in item["spans"]:
            if s["status"] != COVERED:
                code = "GENERATOR_UNOBSERVED" if role == GEN or s["status"] == NOT_EVALUATED else {
                    MISSING: "MISSING_ROLE", POOR: "POOR_QUALITY", CONFLICTED: "CONFLICTING"}[s["status"]]
                reasons.append({"code": code, "role": role, "start": s["start"], "end": s["end"],
                                "minutes": s["minutes"], "text": "; ".join(s["problems"])})
    for limit in result.get("limitations", []):
        reasons.append({"code": "OPEN_BOUND" if limit.startswith("OPEN_BOUND") else "LIMITED", "text": limit})
    for seg in result.get("segments", []):
        for text in seg.get("missing", []):
            if text.startswith(dispatch_v3._NOT_EVIDENCE_GAPS):
                reasons.append({"code": "MODEL_LIMIT", "start": seg["start"], "end": seg["end"], "text": text})
    for limit in window_limits:
        head = limit.split(":", 1)[0]
        if head in ("INTERVAL_LIMITED", "EVIDENCE_GAP"):
            continue  # restated per interval above
        code = {"AMBIGUOUS_COHORT": "COHORT", "NO_COHORT": "COHORT", "MISSING_ROLE": "MISSING_ROLE",
                "SEQUENCE_ORDER_INVERTED": "CONFLICTING", "REPORTS_OVERLAP": "CONFLICTING",
                "GENERATOR_SERIES_AMBIGUOUS": "CONFLICTING", "NO_GENERATOR_STATE": "GENERATOR_UNOBSERVED"}.get(
            head, "CONFIGURATION")
        reasons.append({"code": code, "scope": "WINDOW", "text": limit})
    return reasons


def interval_ceiling(revision: dict[str, Any], coverage: dict[str, Any], evidence: Evidence,
                     cohort_status: str | None) -> dict[str, Any]:
    """The ceiling the revision's own rule result supports (before currentness)."""
    result = revision.get("result") or {}
    claim = revision["claim_level"]
    portions = result.get("portions_minutes") or {}
    withheld: list[str] = []
    if cohort_status not in ("SELECTED_UNIQUE", "SELECTED_EXPLICIT"):
        withheld.append(f"COHORT: cohort {cohort_status} is not a usable selected cohort")
    carrying = [s for s in result.get("segments", []) if s["classification"] == claim]
    for seg in carrying if claim in (CANDIDATE, NECESSARY) else []:
        roles = segment_roles(seg, evidence)
        need: tuple[str, ...] = (LOAD, PV, DIS)
        if claim == CANDIDATE:
            need = next((r for k, r in _CANDIDATE_ROLES.items() if any(x.startswith(k) for x in seg["reasons"])),
                        (LOAD, PV, DIS, SOC))
        for role in (GEN, *need):
            if roles[role][0] != COVERED:
                withheld.append(f"RULE_BASIS_INCOMPLETE: {role} is {roles[role][0]} over {seg['start']}.."
                                f"{seg['end']} inside a {claim} segment")
    if claim == INDETERMINATE or withheld:
        return {"ceiling": INDETERMINATE, "positive": False, "support": "NONE", "supported_minutes": None,
                "withheld": withheld,
                "statement": "No Candidate or Necessary claim is supported by this revision's accepted evidence."}
    limited = any(item["status"] != COVERED for item in coverage.values()) or bool(result.get("limitations"))
    minutes = portions.get("candidate" if claim == CANDIDATE else "necessary")
    return {"ceiling": claim, "positive": True, "support": "LIMITED" if limited else "COMPLETE",
            "supported_minutes": minutes, "withheld": [],
            "statement": (f"At most {claim} over {minutes} min (the sum of {claim} segments only, never the whole "
                          "interval)" + ("; other portions are limited, see reasons" if limited else ""))}


class ClaimLimitReadService:
    def __init__(self, store: ClaimLimitStore, *, model: Any = dispatch_v3) -> None:
        self.store, self.model = store, model

    def read(self, tenant_id: UUID, site_id: UUID, day: date, revision_id: UUID | None,
             rule: str | None = None) -> dict[str, Any]:
        if rule is not None and rule != RULE_ID:
            raise ClaimLimitRefusal(422, "UNSUPPORTED_RULE_VERSION",
                                    f"Rule {rule!r} is not supported; this read serves {RULE_ID} only.")
        window = day_window(day)
        query = EvidenceQuery(tenant_id, site_id, DOMAIN, window, OPEN_CUTOFF, roles=DISPATCH_ROLES)

        def basis(result: EvidenceQueryResult) -> tuple[str | None, str]:
            inputs, config_sha = input_basis(result, self.model)
            return (None if inputs.cohort.status == "EMPTY" else inputs.input_sha256), config_sha

        snap, revision = self.store.claim_limit_snapshot(query, self.model.ANALYTIC_ID, basis, revision_id)
        projection = derive_status(snap, self.model.MODEL_VERSION)
        selected = snap.run
        body: dict[str, Any] = {
            "schema": SCHEMA, "schema_version": SCHEMA_VERSION, "rule_id": RULE_ID,
            "tenant_id": str(tenant_id), "site_id": str(site_id), "domain": DOMAIN,
            "day": day.isoformat(), "window": {"start": window.start, "end": window.end},
            "read_at": snap.read_at,
            "window_status": projection.status, "window_status_reasons": list(projection.reasons),
            "current_selection": None if selected is None else {
                "run_id": str(selected["id"]), "model_version": selected["model_version"],
                "revision_ids": sorted(str(r["id"]) for r in selected["revisions"])},
            "not_inferred": NOT_INFERRED,
        }
        if revision_id is None:
            return {**body, "assessment_revision_id": None, "currentness": UNASSESSED, "capability": None,
                    "claim_limit": {"rule_id": RULE_ID, "ceiling": None, "current_positive_claim": False,
                                    "historical_ceiling": None,
                                    "reasons": [{"code": "NO_REVISION_SELECTED",
                                                 "text": "No assessment revision selected; no claim ceiling is "
                                                         "shown (absence is not a zero capability)."}]}}
        if revision is None or revision.get("analytic_id") != self.model.ANALYTIC_ID:
            raise ClaimLimitRefusal(404, "ASSESSMENT_REVISION_NOT_FOUND", "No such assessment revision for this Site.")
        if (_t(revision["window_start"]), _t(revision["window_end"])) != (window.start, window.end):
            raise ClaimLimitRefusal(422, "REVISION_OUTSIDE_WINDOW",
                                    f"Revision {revision_id} belongs to window {revision['window_start']}.., not "
                                    f"the selected UTC day {day.isoformat()}.")
        if revision["model_version"] not in SUPPORTED_MODELS:
            raise ClaimLimitRefusal(422, "UNSUPPORTED_RULE_VERSION",
                                    f"{RULE_ID} maps {', '.join(SUPPORTED_MODELS)} results only; this revision is "
                                    f"{revision['model_version']}.")
        run = revision.get("run")
        accepted = {str(e["evidence_id"]): e for e in revision.get("evidence", [])
                    if e.get("disposition") == "ACCEPTED"}
        absent = sorted({str(e) for e in revision["evidence_ids"]} - set(accepted))
        if run is None or absent:
            raise ClaimLimitRefusal(409, "ACCEPTED_LINEAGE_ABSENT",
                                    "The revision's pinned Evidence is not all centrally accepted public Evidence "
                                    f"({len(absent)} ID(s) absent); no capability or ceiling is derived.")
        scope = "WINDOW" if revision["assessment_key"].startswith(f"{self.model.ANALYTIC_ID}:window:") else "INTERVAL"
        pinned = dict(accepted)
        if scope == "WINDOW":  # the window revision's intervals are pinned by the run that created it
            pinned.update({str(e["evidence_id"]): e for e in run.get("evidence", [])
                           if e.get("disposition") == "ACCEPTED"})
        evidence: Evidence = {k: {"role": e["role"], "at": _t(e["interval_end"] or e["source_time"])}
                              for k, e in pinned.items()}
        in_selection = selected is not None and str(revision["id"]) in {str(r["id"]) for r in selected["revisions"]}
        currentness = projection.status if in_selection else HISTORICAL
        window_rev = next((r for r in run["revisions"] if r.get("scope") == "WINDOW"), None)
        window_limits = list(((window_rev or {}).get("result") or {}).get("limitations", []))
        echo = {
            "assessment_revision_id": str(revision["id"]), "scope": scope, "assessment_key": revision["assessment_key"],
            "revision_no": revision["revision_no"], "claim_level": revision["claim_level"],
            "currentness": currentness,
            "run": {"run_id": str(run["id"]), "model_version": run["model_version"],
                    "knowledge_cutoff": run["knowledge_cutoff"], "cohort_status": run["cohort_status"],
                    "cohort_sha256": run["cohort_sha256"], "input_sha256": run["input_sha256"],
                    "configuration_sha256": run["configuration_sha256"],
                    "foundation_revision_ids": [str(x) for x in run["foundation_revision_ids"]],
                    "binding_set_revision_ids": [str(x) for x in run["binding_set_revision_ids"]],
                    "built_at": run["completed_at"]},
            "selected_by_runs": revision.get("selected_by_runs", []),
            "accepted_evidence_ids": sorted(accepted),
            "watermarks": {"source": run["watermarks"], "analytic_built_at": run["completed_at"]},
            "built_at": revision["created_at"],
        }
        if scope == "WINDOW":
            items, coverage = [], {}
            for interval in [r for r in run["revisions"] if r.get("scope") == "INTERVAL"]:
                cov = role_coverage((interval["result"] or {}).get("segments", []), evidence, str(interval["id"]))
                for role, item in cov.items():
                    merged = coverage.setdefault(role, {"spans": [], "minutes_by_status": {}, "evidence_ids": []})
                    merged["spans"].extend(item["spans"])
                    for k, v in item["minutes_by_status"].items():
                        merged["minutes_by_status"][k] = merged["minutes_by_status"].get(k, 0.0) + v
                    merged["evidence_ids"] = sorted(set(merged["evidence_ids"]) | set(item["evidence_ids"]))
                ceiling = interval_ceiling(interval, cov, evidence, run["cohort_status"])
                items.append({"assessment_revision_id": str(interval["id"]), "claim_level": interval["claim_level"],
                              "ceiling": ceiling["ceiling"], "support": ceiling["support"]})
            own: dict[str, Any] = {
                "ceiling": None, "positive": False, "support": revision["claim_level"], "supported_minutes": None,
                "withheld": [], "interval_ceilings": items,
                "statement": "A window revision carries no single dispatch classification; see each interval."}
            reasons = _reasons({}, {}, window_limits)
        else:
            coverage = role_coverage((revision["result"] or {}).get("segments", []), evidence, str(revision["id"]))
            own = interval_ceiling(revision, coverage, evidence, run["cohort_status"])
            reasons = _reasons(revision["result"] or {}, coverage, window_limits)
        current = currentness == CURRENT
        if not current:
            reasons.insert(0, {"code": "NOT_CURRENT", "text": (
                "This exact revision is not in the window's current selection; shown as history only."
                if currentness == HISTORICAL else
                f"The window's selection is {currentness}; no current claim is made from it.")})
        for text in own["withheld"]:
            reasons.append({"code": text.split(":", 1)[0], "text": text})
        claim_limit: dict[str, Any] = {
            "rule_id": RULE_ID, "model_version": revision["model_version"],
            "ceiling": own["ceiling"] if current else None,
            "current_positive_claim": current and own["positive"],
            "support": own["support"] if current else None,
            "supported_minutes": own["supported_minutes"] if current else None,
            "statement": own["statement"] if current else None,
            "historical_ceiling": None if current else {k: own[k] for k in ("ceiling", "support",
                                                                             "supported_minutes", "statement")},
            "reasons": reasons,
        }
        if "interval_ceilings" in own:
            # Per-interval ceilings are claims too: top level only when CURRENT, else history under
            # `historical_ceiling` (the same rule as the single ceiling above).
            if current:
                claim_limit["interval_ceilings"] = own["interval_ceilings"]
            else:
                claim_limit["historical_ceiling"]["interval_ceilings"] = own["interval_ceilings"]
        return {**body, **echo,
                "capability": {"rule_id": RULE_ID, "required_roles": list(REQUIRED_ROLES), "roles": coverage,
                               "basis": "stored segments of this exact revision and its pinned accepted Evidence"},
                "claim_limit": claim_limit}
