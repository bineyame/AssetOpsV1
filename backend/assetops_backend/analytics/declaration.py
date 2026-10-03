"""Analytic capability declarations, served as a site-scoped read model (T028 AC16).

`D-2026-10-02-presentation-profile-and-capability-declaration`: the backend owns
which analytics exist, the Finding type each may emit, the evidence each
requires and its claim levels. The frontend presentation profile may only
label, order, group and emphasise these ids. Verification rules are not
declared yet (T034).

Every analytic module registers here; `tools/checks/analytic-declaration.ps1`
fails when an analytic module (one that sets `ANALYTIC_ID`) has no declaration
or a declaration lacks a field.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from assetops_backend.analytics import dispatch
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
)

#: Every analytic AssetOps runs. One entry per analytic module.
DECLARATIONS: tuple[AnalyticDeclaration, ...] = (DISPATCH,)

DECLARATION_STATEMENT = (
    "What each analytic declares: the Finding type it may emit, the evidence it "
    "requires and the claim levels it may reach. Availability is whether accepted "
    "evidence holds a usable record of that signal for this Site; it is not a "
    "readiness score. Verification rules are not declared yet."
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


def site_declaration(site: SiteRecord, evidence: SiteEvidence) -> dict[str, Any]:
    """The declarations that apply to this Site's type, evaluated against its evidence."""
    return {
        "site_id": site.site_id,
        "site_type": site.site_type,
        "statement": DECLARATION_STATEMENT,
        "analytics": [
            {
                "analytic_id": d.analytic_id,
                "display_name": d.display_name,
                "site_types": list(d.site_types),
                "finding_type": {"id": d.finding_type, "display_name": d.finding_type_display_name},
                "model_version": d.model_version,
                "claim_levels": [
                    {"claim_level": c.claim_level, "label": c.label, "ceiling": c.ceiling}
                    for c in d.claim_levels
                ],
                "required_evidence": [_requirement(r, evidence) for r in d.required_evidence],
                "optional_evidence": [_requirement(r, evidence) for r in d.optional_evidence],
                "thresholds": [dict(t) for t in d.thresholds],
            }
            for d in applicable(site.site_type)
        ],
    }
