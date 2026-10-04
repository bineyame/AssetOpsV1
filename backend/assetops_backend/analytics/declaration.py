"""Analytic capability declarations, served as a site-scoped read model (T028 AC16).

`D-2026-10-02-presentation-profile-and-capability-declaration`: the backend owns
which analytics exist, the Finding type each may emit, the evidence each
requires and its claim levels. The frontend presentation profile may only
label, order, group and emphasise these ids. Verification rules are not
declared yet (T034).

Every analytic module registers here; `tools/checks/analytic-declaration.ps1`
fails when an analytic module (one that sets `ANALYTIC_ID`) has no declaration
or a declaration lacks a field.

Each declaration also states its readiness basis (T028 AC20): how its row in
Site > Evidence's capability table is scored Full, Limited or None from the
declaration against accepted coverage. The score, the claim ceiling and the
missing evidence are computed here, so every gap the screen shows is backend
state (AC18 rule 3); the presentation profile only labels and orders the row.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from assetops_backend.analytics import dispatch, plain
from assetops_backend.evidence.models import SiteEvidence
from assetops_backend.sites.models import SiteRecord


@dataclass(frozen=True)
class EvidenceRequirement:
    device_id: str
    signal_id: str
    family: str
    role: str


@dataclass(frozen=True)
class ClaimLevel:
    claim_level: str
    label: str
    ceiling: str


@dataclass(frozen=True)
class ReadinessBasis:
    """How a declaration is scored against accepted coverage (T028 AC20).

    None: no role in `reconstruct_from_any` has a usable accepted record, so no
    interval can be reconstructed and no claim level is reachable. The roles
    are alternatives (the analytic reconstructs from either), so one absent
    channel alone is Limited, never None.
    Limited: some `reconstruct_from_any` role is evidenced, but a required role
    has no usable record, or an active assessment has a coverage gap that
    limited a claim (a segment's `missing` list names that input, or the
    generator state is unobserved inside it: readiness-3). The
    ceiling is `fallback_claim_level` when a role in `top_claim_needs` has no
    usable record at all, else `top_claim_level` only for the portions whose
    required inputs are evidenced.
    Full: every required role evidenced and no claim limited by a coverage
    gap; the ceiling is `top_claim_level`. A gap no classification depended on
    is still listed, as not limiting, so coverage is never hidden.
    """

    version: str
    reconstruct_from_any: tuple[str, ...]
    top_claim_level: str
    top_claim_needs: tuple[str, ...]
    fallback_claim_level: str


@dataclass(frozen=True)
class AnalyticDeclaration:
    analytic_id: str
    display_name: str
    site_types: tuple[str, ...]
    finding_type: str
    finding_type_display_name: str
    required_evidence: tuple[EvidenceRequirement, ...]
    optional_evidence: tuple[EvidenceRequirement, ...]
    claim_levels: tuple[ClaimLevel, ...]
    model_version: str
    thresholds: tuple[dict[str, str], ...]
    readiness: ReadinessBasis


def _m(key: tuple[str, str], role: str) -> EvidenceRequirement:
    return EvidenceRequirement(key[0], key[1], "MEASUREMENT", role)


DISPATCH = AnalyticDeclaration(
    analytic_id=dispatch.ANALYTIC_ID,
    display_name="Dispatch",
    site_types=("MINIGRID",),
    finding_type=dispatch.FINDING_TYPE,
    finding_type_display_name="Generator dispatch interval",
    required_evidence=(
        _m(dispatch.GEN_STATUS, "Generator state"),
        _m(dispatch.GEN_POWER, "Generator state and output"),
        *(_m(key, "Load") for key in dispatch.FEEDERS),
        _m(dispatch.PV_AVAILABLE, "PV capability"),
        _m(dispatch.SOC, "Battery state"),
        _m(dispatch.DISCHARGE, "Battery capability"),
        EvidenceRequirement(*dispatch.POLICY_RESERVE, "POLICY", "Reserve policy"),
    ),
    optional_evidence=(
        EvidenceRequirement(*dispatch.POLICY_MIN_RUNTIME, "POLICY", "Minimum runtime policy"),
        EvidenceRequirement(*dispatch.POLICY_STOP, "POLICY", "Stop threshold policy (context)"),
        EvidenceRequirement(*dispatch.GEN_OVERRIDE, "OPERATIONAL_RECORD", "Operator override"),
        EvidenceRequirement(*dispatch.BATTERY_OVERRIDE, "OPERATIONAL_RECORD", "Operator override"),
    ),
    claim_levels=tuple(
        ClaimLevel(level, dispatch.CLAIM_LABELS[level], dispatch.CLAIM_CEILINGS[level])
        for level in (dispatch.NECESSARY, dispatch.CANDIDATE, dispatch.INDETERMINATE)
    ),
    model_version=dispatch.MODEL_VERSION,
    thresholds=dispatch.THRESHOLDS,
    readiness=ReadinessBasis(
        version="readiness-3",
        reconstruct_from_any=("Generator state", "Generator state and output"),
        top_claim_level=dispatch.CANDIDATE,
        top_claim_needs=("Load", "PV capability", "Battery capability"),
        fallback_claim_level=dispatch.NECESSARY,
    ),
)

#: Every analytic AssetOps runs. One entry per analytic module.
DECLARATIONS: tuple[AnalyticDeclaration, ...] = (DISPATCH,)

DECLARATION_STATEMENT = (
    "What each analytic declares: the Finding type it may emit, the evidence it "
    "requires and the claim levels it may reach. Availability is whether accepted "
    "evidence holds a usable record of that signal for this Site; readiness "
    "scores the declaration against that and against the coverage of the active "
    "assessments. Verification rules are not declared yet."
)


def applicable(site_type: str) -> tuple[AnalyticDeclaration, ...]:
    return tuple(d for d in DECLARATIONS if site_type in d.site_types)


def _requirement(req: EvidenceRequirement, evidence: SiteEvidence) -> dict[str, Any]:
    records = [
        r for r in evidence.records
        if (r.device_id, r.signal_id) == (req.device_id, req.signal_id)
        and r.normalized_value is not None
        and (r.quality == "GOOD" or r.family != "MEASUREMENT")
    ]
    return {
        "device_id": req.device_id,
        "signal_id": req.signal_id,
        "family": req.family,
        "role": req.role,
        "available": bool(records),
        "usable_records": len(records),
        "last_source_time": max((r.source_time for r in records), default=None),
    }


#: The labels of the three readiness levels (T028 AC20).
READINESS_LABELS = {"FULL": "Full", "LIMITED": "Limited", "NONE": "None"}

READINESS_STATEMENT = (
    "Readiness is evidence sufficiency: how well the accepted evidence can support "
    "this analytic's conclusions. It is not Site health, setup progress or source "
    "health. It is scored site-wide from the declaration against all accepted "
    "evidence for this Site and the coverage of its active assessments, not the "
    "selected window. Full: every required signal has some usable accepted record "
    "and no assessed portion was left Indeterminate by a coverage gap (interim "
    "rule: only gaps that limit a claim lower readiness; other gaps are listed as "
    "not limiting). Full does not mean the Site is healthy, or that coverage is "
    "uninterrupted, current or present in every selected window. Limited: claims "
    "are possible but capped or segmented by the missing evidence named. None: no "
    "claim can be made because no generator reconstruction evidence is accepted."
)

def _roles(rows: list[dict[str, Any]], roles: tuple[str, ...]) -> list[dict[str, Any]]:
    return [r for r in rows if r["role"] in roles]


def _not_accepted(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "NOT_ACCEPTED",
        "limits_claim": True,
        "role": row["role"],
        "device_id": row["device_id"],
        "signal_id": row["signal_id"],
        "statement": (
            f"{row['role']} ({row['device_id']} / {row['signal_id']}): no usable "
            "accepted record."
        ),
        "assessment_ids": [],
    }


def _coverage_gaps(assessments: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    """Required inputs some active assessment could not evaluate everywhere."""
    gaps: dict[str, dict[str, Any]] = {}
    for assessment_id, assessment in assessments:
        for row in assessment.get("coverage", {}).get("inputs", []):
            if row["usable_segments"] >= row["evaluated_segments"]:
                continue
            gap = gaps.setdefault(row["input"], {
                "kind": "COVERAGE_GAP",
                "role": row["label"],
                "device_id": None,
                "signal_id": None,
                "missing_segments": 0,
                "evaluated_segments": 0,
                "limiting_segments": 0,
                "assessment_ids": [],
            })
            gap["missing_segments"] += row["evaluated_segments"] - row["usable_segments"]
            gap["evaluated_segments"] += row["evaluated_segments"]
            gap["assessment_ids"].append(assessment_id)
            gap["limiting_segments"] += sum(
                1 for segment in assessment.get("segments", [])
                if any(m.startswith(row["label"]) for m in segment.get("missing", []))
            )
    out = _generator_gaps(assessments)
    for gap in gaps.values():
        n = len(gap["assessment_ids"])
        plural = "" if n == 1 else "s"
        gap["limits_claim"] = gap["limiting_segments"] > 0
        consequence = (
            f"{gap['limiting_segments']} segment(s) that needed it are Indeterminate."
            if gap["limits_claim"]
            else "no classification depended on it there."
        )
        gap["statement"] = (
            f"{gap['role']}: no usable record for {gap['missing_segments']} of "
            f"{gap['evaluated_segments']} evaluated segments in {n} assessed "
            f"interval{plural}; {consequence}"
        )
        out.append(gap)
    return out


def _generator_gaps(assessments: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    """Generator-state gaps inside active assessments (readiness-3, R5).

    An unobserved generator-state span is always Indeterminate, so such a gap
    always limits a claim.
    """
    spans = [(aid, span) for aid, a in assessments
             for span in a.get("coverage", {}).get("unobserved_generator_state", [])]
    if not spans:
        return []
    ids = list(dict.fromkeys(aid for aid, _ in spans))
    minutes = sum(int(span["minutes"]) for _, span in spans)
    plural = "" if len(ids) == 1 else "s"
    return [{
        "kind": "COVERAGE_GAP",
        "role": "Generator state",
        "device_id": None,
        "signal_id": None,
        "missing_segments": len(spans),
        "evaluated_segments": sum(len(a.get("segments", [])) for aid, a in assessments if aid in ids),
        "limiting_segments": len(spans),
        "assessment_ids": ids,
        "limits_claim": True,
        "statement": (
            f"Generator state: not observed for {minutes} min in {len(ids)} assessed "
            f"interval{plural} ({len(spans)} span(s)); that time is Indeterminate."
        ),
    }]


def score_readiness(
    declaration: AnalyticDeclaration,
    required: list[dict[str, Any]],
    optional: list[dict[str, Any]],
    assessments: list[tuple[str, dict[str, Any]]],
) -> dict[str, Any]:
    """The capability row's readiness, ceiling and missing evidence (T028 AC20)."""
    basis = declaration.readiness
    ceilings = {c.claim_level: c for c in declaration.claim_levels}
    missing = [_not_accepted(r) for r in required if not r["available"]]
    alternatives = _roles(required, basis.reconstruct_from_any)
    blocked = alternatives if not any(r["available"] for r in alternatives) else []
    capped: list[dict[str, Any]] = []
    if blocked:
        level = "NONE"
        ceiling = {
            "claim_level": None,
            "label": "No claim",
            "statement": (
                "No claim can be made: with no accepted record of "
                + " or ".join(sorted({r["role"] for r in blocked}))
                + " no interval can be reconstructed from accepted evidence."
            ),
        }
    else:
        missing += _coverage_gaps(assessments)
        capped = [r for r in _roles(required, basis.top_claim_needs) if not r["available"]]
        top = ceilings[basis.top_claim_level]
        if capped:
            fallback = ceilings[basis.fallback_claim_level]
            level = "LIMITED"
            ceiling = {
                "claim_level": fallback.claim_level,
                "label": fallback.label,
                "statement": (
                    f"{top.label} cannot be reached without "
                    + " and ".join(sorted({r["role"] for r in capped}))
                    + f". {fallback.label} only where an evidenced constraint binds; "
                    "other portions are Indeterminate."
                ),
            }
        elif any(m["kind"] == "NOT_ACCEPTED" or m["limits_claim"] for m in missing):
            level = "LIMITED"
            ceiling = {
                "claim_level": top.claim_level,
                "label": top.label,
                "statement": (
                    f"{top.label} only for portions whose required inputs are "
                    "evidenced; portions without them are Indeterminate. " + top.ceiling
                ),
            }
        else:
            level = "FULL"
            ceiling = {"claim_level": top.claim_level, "label": top.label,
                       "statement": top.ceiling}
    return {
        "basis_version": basis.version,
        "level": level,
        "label": READINESS_LABELS[level],
        "claim_ceiling": ceiling,
        "missing_evidence": missing,
        "optional_not_observed": [
            {"role": r["role"], "device_id": r["device_id"], "signal_id": r["signal_id"]}
            for r in optional if not r["available"]
        ],
        "assessed_intervals": len(assessments),
        "statement": READINESS_STATEMENT,
        # Plain reading, read time only (D-2026-10-04-plain-language-analysis-views).
        **plain.readiness(level, ceiling, missing, sorted({r["role"] for r in capped})),
    }


def site_declaration(
    site: SiteRecord,
    evidence: SiteEvidence,
    assessments: dict[str, list[tuple[str, dict[str, Any]]]] | None = None,
) -> dict[str, Any]:
    """The declarations that apply to this Site's type, evaluated against its evidence.

    `assessments` maps an analytic id to its active assessments as
    `(assessment_id, assessment)` pairs; each row's readiness is scored against
    their coverage. Absent, readiness is scored from accepted records alone.
    """
    analytics = []
    for d in applicable(site.site_type):
        required = [_requirement(r, evidence) for r in d.required_evidence]
        optional = [_requirement(r, evidence) for r in d.optional_evidence]
        for row in (*required, *optional):
            row["plain_role"] = plain.role(row["role"])
        analytics.append({
            "analytic_id": d.analytic_id,
            "display_name": d.display_name,
            "site_types": list(d.site_types),
            "finding_type": {"id": d.finding_type, "display_name": d.finding_type_display_name},
            "model_version": d.model_version,
            "claim_levels": [
                {"claim_level": c.claim_level, "label": c.label, "ceiling": c.ceiling}
                for c in d.claim_levels
            ],
            "required_evidence": required,
            "optional_evidence": optional,
            "thresholds": [dict(t) for t in d.thresholds],
            "readiness": score_readiness(
                d, required, optional, (assessments or {}).get(d.analytic_id, [])
            ),
        })
    return {
        "site_id": site.site_id,
        "site_type": site.site_type,
        "statement": DECLARATION_STATEMENT,
        "analytics": analytics,
    }
