"""`reserve-trial-1`: the server-computed, bounded battery-reserve policy-sensitivity trial (S6-01a).

`D-2026-10-15-s601-action-store-and-ui` Q1: eligible only for the latest, `SUPPORTED`, current
`GENERATOR_SUPPORT_CANDIDATE` FindingRevision whose cited Candidate segment's accepted analytic input holds a usable
numeric battery-SOC reading strictly above that segment's pinned effective reserve plus the dispatch model's
`SOC_HEADROOM_POINTS` (10), whose cited Foundation has one unambiguous percent reserve on the same battery asset,
and whose current Site Foundation reserve still equals the pinned reserve. For a reserve `r` in [15, 90] the
proposal is exactly `r - 5` percentage points. Anything else is a typed unavailable reason.

This module is pure: the adapter gathers the persisted inputs (`RuleInputs`), this decides. It never diagnoses
the Finding's cause and never predicts runtime, saving or safety.

Segment SOC (implementer rule, recorded in the handoff): a segment's readings are the `battery_soc` evidence its
interval assessment cites. Usable = quality GOOD, numeric, unit `%`. Two usable readings at the same instant with
different values are conflicting. The selected reading is the lowest usable value (the conservative choice), so
"strictly above r + 10" holds for every usable reading of an eligible segment.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from assetops_backend.analytics.dispatch_v3 import SOC_HEADROOM_POINTS

RULE_ID = "reserve-trial-1"
RULE_VERSION = 1
FIELD = "reserve-state-of-charge"
UNIT = "%"
SOC_ROLE = "battery_soc"
HEADROOM = Decimal(int(SOC_HEADROOM_POINTS))
TRIAL_STEP = Decimal(5)
RESERVE_MIN, RESERVE_MAX = Decimal(15), Decimal(90)
MECHANISM = "GENERATOR_SUPPORT_CANDIDATE"
CANDIDATE = "CANDIDATE_AVOIDABLE"

LIMITATION_CODE = "POLICY_SENSITIVITY_TRIAL_ONLY"
LIMITATION_TEXT = ("A five-percentage-point battery-reserve trial chosen by a fixed rule. It tests whether the "
                   "reserve setting matters; it does not say the reserve caused this finding and does not predict "
                   "less generator running time, any saving or any safety effect.")

# Typed unavailable reasons (code -> plain statement).
REASONS = {
    "FINDING_KIND_UNSUPPORTED": "The rule applies only to a generator-support Finding.",
    "FINDING_NOT_SUPPORTED": "The selected Finding revision is not a supported claim.",
    "FINDING_REVISION_NOT_LATEST": "A later revision of this Finding exists; only the latest revision can be used.",
    "FINDING_NOT_CURRENT": "The Finding's basis is not the current assessment, so no trial is proposed.",
    "CANDIDATE_ABSENT": "The revision cites no Candidate segment.",
    "SOC_MISSING": "The Candidate segment's accepted input has no battery state-of-charge reading.",
    "SOC_NOT_NUMERIC": "The Candidate segment's battery state-of-charge readings are not usable percent numbers.",
    "SOC_CONFLICTING": "The Candidate segment has conflicting battery state-of-charge readings at the same time.",
    "SOC_NOT_ABOVE_HEADROOM": "Battery state of charge was not above the reserve plus the 10-point headroom.",
    "RESERVE_MISSING": "The cited Foundation has no battery reserve for the segment.",
    "RESERVE_CONFLICTING": "The cited Foundation has more than one battery reserve for the segment.",
    "RESERVE_UNIT_INVALID": "The cited Foundation's battery reserve is not a percent number.",
    "ASSET_MISMATCH": "The state-of-charge reading is not from the battery the reserve belongs to.",
    "RESERVE_OUT_OF_BAND": "The pinned reserve is outside 15-90 %, so the trial is not proposed.",
    "CURRENT_FOUNDATION_MISSING": "The Site has no single current Foundation revision.",
    "FOUNDATION_BASIS_STALE": "The Site's current battery reserve no longer equals the reserve the Finding used.",
    "UNCHANGED_RESULT": "The trial would not change the current reserve.",
    "LIVE_RECOMPUTATION_FAILED": "The live recomputation could not read this revision's persisted inputs.",
}


@dataclass(frozen=True)
class SocReading:
    evidence_id: UUID
    asset_id: UUID | None
    value_text: str | None
    unit: str
    quality: str
    at: datetime
    envelope_sha256: str


@dataclass(frozen=True)
class ReserveEntry:
    asset_code: str
    asset_id: UUID | None
    value: Any
    unit: Any


@dataclass(frozen=True)
class FoundationBasis:
    revision_id: UUID
    reserves: tuple[ReserveEntry, ...]


@dataclass(frozen=True)
class Segment:
    assessment_revision_id: UUID
    start: datetime
    end: datetime
    soc: tuple[SocReading, ...]
    #: the cited FoundationRevisions whose valid interval covers the segment start
    foundations: tuple[FoundationBasis, ...]


@dataclass(frozen=True)
class RuleInputs:
    tenant_id: UUID
    site_id: UUID
    finding_id: UUID
    finding_revision_id: UUID
    mechanism: str
    lifecycle: str
    is_latest: bool
    claim_is_current: bool
    primary_assessment_revision_id: UUID
    segments: tuple[Segment, ...]
    #: None when the Site has no single covering Foundation revision now
    current_foundation: FoundationBasis | None


@dataclass(frozen=True)
class Evaluation:
    available: bool
    reason: str | None
    proposal: dict[str, Any] | None
    segments: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def unavailable(self) -> dict[str, Any] | None:
        return None if self.available else {"code": self.reason, "message": REASONS[self.reason or ""]}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def sha(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def number(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return out if out.is_finite() else None


def text_of(value: Decimal) -> str:
    """A stable decimal text: no exponent, no trailing zeros beyond the integer."""
    out = format(value.normalize(), "f")
    return out


def recommendation_key(tenant_id: UUID, site_id: UUID, finding_revision_id: UUID, foundation_revision_id: UUID,
                       asset_id: UUID) -> dict[str, str | int]:
    return {"tenant_id": str(tenant_id), "site_id": str(site_id), "finding_revision_id": str(finding_revision_id),
            "foundation_revision_id": str(foundation_revision_id), "rule_id": RULE_ID, "rule_version": RULE_VERSION,
            "asset_id": str(asset_id)}


def key_digest(key: dict[str, Any]) -> str:
    return sha(key)


def acceptance_key(key: dict[str, Any]) -> str:
    """The canonical digest of the recommendation tuple plus ACCEPT (unique within tenant/Site)."""
    return sha({"recommendation": key, "command": "ACCEPT"})


def _reserve(basis: FoundationBasis) -> tuple[str | None, ReserveEntry | None, Decimal | None]:
    if not basis.reserves:
        return "RESERVE_MISSING", None, None
    if len(basis.reserves) > 1:
        return "RESERVE_CONFLICTING", None, None
    entry = basis.reserves[0]
    value = number(entry.value)
    if entry.unit != UNIT or value is None or entry.asset_id is None:
        return ("RESERVE_UNIT_INVALID" if entry.asset_id is not None else "RESERVE_MISSING"), entry, None
    return None, entry, value


def _segment(seg: Segment) -> dict[str, Any]:
    """One Candidate segment's verdict, with its pinned reserve and selected SOC reading."""
    out: dict[str, Any] = {"assessment_revision_id": str(seg.assessment_revision_id), "start": seg.start.isoformat(),
                           "end": seg.end.isoformat(), "eligible": False, "reason": None}
    if not seg.foundations:
        out["reason"] = "RESERVE_MISSING"
        return out
    if len(seg.foundations) > 1:
        out["reason"] = "RESERVE_CONFLICTING"
        return out
    basis = seg.foundations[0]
    problem, entry, reserve = _reserve(basis)
    out["foundation_revision_id"] = str(basis.revision_id)
    if problem:
        out["reason"] = problem
        return out
    assert entry is not None and reserve is not None
    out.update(reserve=text_of(reserve), asset_id=str(entry.asset_id), asset_code=entry.asset_code)
    if not seg.soc:
        out["reason"] = "SOC_MISSING"
        return out
    if any(r.asset_id != entry.asset_id for r in seg.soc):
        out["reason"] = "ASSET_MISMATCH"
        return out
    usable = [(r, number(r.value_text)) for r in seg.soc
              if r.quality == "GOOD" and r.unit == UNIT and number(r.value_text) is not None]
    if not usable:
        out["reason"] = "SOC_NOT_NUMERIC"
        return out
    by_instant: dict[datetime, set[Decimal]] = {}
    for reading, value in usable:
        by_instant.setdefault(reading.at, set()).add(value)  # type: ignore[arg-type]
    if any(len(values) > 1 for values in by_instant.values()):
        out["reason"] = "SOC_CONFLICTING"
        return out
    selected, low = min(usable, key=lambda pair: (pair[1], pair[0].at, str(pair[0].evidence_id)))
    threshold = reserve + HEADROOM
    out.update(soc_threshold=text_of(threshold), selected_soc={
        "evidence_id": str(selected.evidence_id), "value": text_of(low), "unit": UNIT, "at": selected.at.isoformat(),
        "envelope_sha256": selected.envelope_sha256},
        soc_evidence=[{"evidence_id": str(r.evidence_id), "value": text_of(v), "at": r.at.isoformat(),
                       "envelope_sha256": r.envelope_sha256} for r, v in sorted(
                           usable, key=lambda p: (p[0].at, str(p[0].evidence_id)))])
    if not low > threshold:
        out["reason"] = "SOC_NOT_ABOVE_HEADROOM"
        return out
    out["eligible"] = True
    return out


def evaluate(inputs: RuleInputs) -> Evaluation:
    def no(reason: str, segments: tuple[dict[str, Any], ...] = ()) -> Evaluation:
        return Evaluation(False, reason, None, segments)

    if inputs.mechanism != MECHANISM:
        return no("FINDING_KIND_UNSUPPORTED")
    if inputs.lifecycle != "SUPPORTED":
        return no("FINDING_NOT_SUPPORTED")
    if not inputs.is_latest:
        return no("FINDING_REVISION_NOT_LATEST")
    if not inputs.claim_is_current:
        return no("FINDING_NOT_CURRENT")
    if not inputs.segments:
        return no("CANDIDATE_ABSENT")
    ordered = sorted(inputs.segments, key=lambda s: (s.start, str(s.assessment_revision_id)))
    verdicts = tuple(_segment(s) for s in ordered)
    eligible = [v for v in verdicts if v["eligible"]]
    if not eligible:
        return no(verdicts[-1]["reason"], verdicts)
    # The basis is the latest eligible segment's pinned Foundation; every eligible segment on it is cited.
    basis = eligible[-1]
    cited = [v for v in eligible if v["foundation_revision_id"] == basis["foundation_revision_id"]
             and v["asset_id"] == basis["asset_id"]]
    reserve = Decimal(basis["reserve"])
    if not RESERVE_MIN <= reserve <= RESERVE_MAX:
        return no("RESERVE_OUT_OF_BAND", verdicts)
    if inputs.current_foundation is None:
        return no("CURRENT_FOUNDATION_MISSING", verdicts)
    problem, entry, current = _reserve(inputs.current_foundation)
    if problem or entry is None or str(entry.asset_id) != basis["asset_id"] or current != reserve:
        return no("FOUNDATION_BASIS_STALE", verdicts)
    proposed = reserve - TRIAL_STEP
    if proposed == current:
        return no("UNCHANGED_RESULT", verdicts)
    key = recommendation_key(inputs.tenant_id, inputs.site_id, inputs.finding_revision_id,
                             UUID(basis["foundation_revision_id"]), UUID(basis["asset_id"]))
    inputs_pinned = {
        "finding_revision_id": str(inputs.finding_revision_id),
        "primary_assessment_revision_id": str(inputs.primary_assessment_revision_id),
        "foundation_revision_id": basis["foundation_revision_id"],
        "segments": [{k: v[k] for k in ("assessment_revision_id", "start", "end", "reserve", "soc_threshold",
                                        "selected_soc", "soc_evidence")} for v in cited]}
    proposal = {
        "recommendation_key": key_digest(key), "key": key, "acceptance_key": acceptance_key(key),
        "rule": {"id": RULE_ID, "version": RULE_VERSION, "headroom_points": text_of(HEADROOM),
                 "step_points": text_of(TRIAL_STEP), "band": [text_of(RESERVE_MIN), text_of(RESERVE_MAX)]},
        "finding_id": str(inputs.finding_id), "finding_revision_id": str(inputs.finding_revision_id),
        "primary_assessment_revision_id": str(inputs.primary_assessment_revision_id),
        "foundation_revision_id": basis["foundation_revision_id"],
        "current_foundation_revision_id": str(inputs.current_foundation.revision_id),
        "asset_id": basis["asset_id"], "asset_code": basis["asset_code"], "field": FIELD, "unit": UNIT,
        "old_value": text_of(reserve), "proposed_value": text_of(proposed),
        "limitation": {"code": LIMITATION_CODE, "text": LIMITATION_TEXT},
        "inputs": inputs_pinned, "input_sha256": sha(inputs_pinned),
    }
    return Evaluation(True, None, proposal, verdicts)
