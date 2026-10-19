"""W2-04 commit 2: pure cold consequence derivation (`cold-exposure/1`). No SQL and no driver.

`.agent/W2-04-build-spec.md` "Money schema `0023` and rules", "Implementer dry-read: exact backend behavior" and
rulings Q3-Q6. Input is one exact basis the consequence store read in the worker's repeatable-read snapshot: a
cold FindingRevision, the episode revision its claim names, that revision's assessment (window, knowledge cutoff,
chamber room) and the exact accepted evidence both cite, with their S4-05 publication link rows.

- Only a warranted (`SUPPORTED`) `EXCURSION` FindingRevision gets a `PRODUCT_EXPOSURE` revision. `START_RESPONSE`
  is chronology/context and gets none here; a non-warranted revision gets none (the worker closes its work with
  an empty-ID success attempt).
- The `degC_min` bounds are copied from the episode revision's `degree_minutes_low/high` as canonical decimal
  strings; nothing is integrated or inferred. An open episode keeps its proved lower bound with a null upper, as
  `UNPRICED` with the named limit `OPEN_EPISODE_UPPER_UNKNOWN` (Q4).
- A source class other than `REGISTERED_SIMULATION`/`AUTHORED_DEMONSTRATION` (MIXED, UNKNOWN), contradictory or
  unproved claim levels, coverage under the 0.8 excursion-bounds floor, or an unknown lower bound gives
  `WITHHELD`. Every amount and currency is null: no cold stock value, currency or exposure rule is approved.
- The consequence basis SHA-256 hashes canonical JSON of the sorted exact evidence uses/reasons, the Finding,
  episode and assessment IDs with their basis hashes, the selected window and cutoff, the model, the quantity
  bounds, the aggregate source class and gate digest and the explicit missing assumption markers.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Iterable, Mapping

from assetops_contracts.source_envelope import canonical_json

from assetops_backend.evidence.source_provenance import (
    AUTHORED_DEMONSTRATION,
    MIXED,
    REGISTERED_SIMULATION,
    LinkRow,
    classify,
    link_of,
)

MODEL_EXPOSURE = "cold-exposure/1"
KIND_EXPOSURE = "PRODUCT_EXPOSURE"
UNIT_DEG_C_MIN = "degC_min"
STATE_UNPRICED = "UNPRICED"
STATE_WITHHELD = "WITHHELD"

# Reserved future scenario keys, reported missing; never published through the diesel-only publisher.
MISSING_ASSUMPTIONS = ("cold_exposure_rule", "cold_stock_quantity", "cold_stock_unit_value")

# Reason codes stored in `cold_consequence_revision.reason`.
REASON_UNPRICED = "COLD_VALUATION_NOT_APPROVED"
REASON_SOURCE_WITHHELD = "SOURCE_GATE_WITHHELD"
REASON_TECHNICAL_WITHHELD = "TECHNICAL_CLAIM_LIMITED"

# Named technical limits stored in `cold_consequence_revision.limitation` (Q4: a named limit, never a note).
LIMIT_OPEN_UPPER = "OPEN_EPISODE_UPPER_UNKNOWN"
LIMIT_CONTRADICTORY = "CONTRADICTORY_EVIDENCE"
LIMIT_COVERAGE = "COVERAGE_INCOMPLETE"
LIMIT_LOWER_UNKNOWN = "EXPOSURE_LOWER_BOUND_UNKNOWN"
LIMIT_CLAIM_POSSIBLE = "CLAIM_LEVEL_POSSIBLE"
LIMIT_CLAIM_UNKNOWN = "CLAIM_LEVEL_UNKNOWN"
LIMIT_SOURCE_MIXED = "SOURCE_CLASS_MIXED"
LIMIT_SOURCE_UNKNOWN = "SOURCE_CLASS_UNKNOWN"

# Spec "Selection, projection and capability": EXCURSION_BOUNDS needs >= 0.8 coverage.
COVERAGE_FLOOR = Decimal("0.8")

#: Commit-2 Architect rulings ("stored codes and screen copy"): the exact plain wording a screen shows for each
#: stored machine code; a raw code never reaches a screen.
SCREEN_WORDING: dict[str, str] = {
    "COLD_VALUATION_NOT_APPROVED": "Thermal exposure is recorded, but no approved product valuation is available.",
    "SOURCE_GATE_WITHHELD": "The source record cannot support a money claim for this selection.",
    "TECHNICAL_CLAIM_LIMITED": "The available temperature evidence cannot establish an exposure amount.",
    "OPEN_EPISODE_UPPER_UNKNOWN": "The excursion has no recorded end, so its total exposure has no upper bound.",
    "CONTRADICTORY_EVIDENCE": "Accepted records disagree; this conclusion cannot be established.",
    "CLAIM_LEVEL_POSSIBLE": "The evidence suggests an excursion but does not confirm it.",
    "CLAIM_LEVEL_UNKNOWN": "The evidence cannot establish whether an excursion occurred.",
    "COVERAGE_INCOMPLETE": "Too few qualifying temperature readings were recorded for an exposure conclusion.",
    "EXPOSURE_LOWER_BOUND_UNKNOWN": "The recorded readings do not establish a minimum thermal exposure.",
    "SOURCE_CLASS_MIXED": "This selection mixes source types, so its money claim is withheld.",
    "SOURCE_CLASS_UNKNOWN": "The source type is unknown, so its money claim is withheld.",
    "COLD_RECOMPUTE_FAILED": "The exposure calculation failed and is waiting to retry.",
    "STORE_UNAVAILABLE": "The exposure record is temporarily unavailable.",
    "WORK_SCOPE_MISMATCH": "This exposure work item does not belong to the selected site.",
}


def screen_sentences(limitation: str | None) -> list[str]:
    """Each distinct stored code of a semicolon-joined limitation as its plain sentence, in stored order."""
    out: list[str] = []
    for code in (limitation or "").split("; "):
        sentence = SCREEN_WORDING.get(code.strip())
        if sentence and sentence not in out:
            out.append(sentence)
    return out
PERMITTED_CLASSES = (REGISTERED_SIMULATION, AUTHORED_DEMONSTRATION)
PROVED_LEVELS = ("OBSERVED", "BOUNDED")

ERROR_BASIS_MISMATCH = "COLD_BASIS_MISMATCH"

USES = ("SUPPORT", "CONTEXT", "EXCLUDED")


class ColdBasisMismatch(LookupError):
    """The exact Finding/episode/assessment basis is missing, foreign or does not pair (`COLD_BASIS_MISMATCH`)."""

    code = ERROR_BASIS_MISMATCH


def selected_instant(moment: datetime) -> str:
    """Q3: a selected-window instant as UTC `Z`, whole seconds, or six fractional digits when microseconds are
    nonzero (never truncated). Matches SQL `cold_consequence_instant`."""
    utc = moment.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ" if utc.microsecond else "%Y-%m-%dT%H:%M:%SZ")


def sha256_canonical(document: object) -> str:
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()


def overlap_group(tenant_id: Any, site_id: Any, window_start: datetime, window_end: datetime,
                  room_asset_id: Any) -> str:
    """`'cold:' + sha256(canonical JSON [tenant, site, window_start, window_end, room])`: a money grouping label,
    not a V4 event/correlation ID."""
    return "cold:" + sha256_canonical([str(tenant_id).lower(), str(site_id).lower(), selected_instant(window_start),
                                       selected_instant(window_end), str(room_asset_id).lower()])


def decimal_text(value: Decimal | int | str | None) -> str | None:
    """Canonical decimal string: no exponent, no trailing zeros (`45.0000` -> `45`)."""
    if value is None:
        return None
    d = Decimal(str(value)).normalize()
    text = format(d, "f")
    return "0" if text in ("-0", "0") else text


@dataclass(frozen=True)
class EvidenceUse:
    evidence_id: str
    use: str
    reason: str | None = None


@dataclass(frozen=True)
class ColdBasis:
    """One exact basis as read in the worker snapshot. `episode_*` fields are None when the claim's episode
    revision is not in this tenant/Site; `assessment_*` likewise."""

    tenant_id: str
    site_id: str
    finding_revision_id: str
    finding_id: str
    finding_lifecycle: str
    finding_basis_sha256: str
    finding_assessment_revision_id: str
    claim: Mapping[str, Any]
    episode_revision_id: str | None
    episode_id: str | None
    episode_kind: str | None
    episode_assessment_revision_id: str | None
    episode_basis_sha256: str | None
    claim_level: str | None
    degree_minutes_low: Decimal | None
    degree_minutes_high: Decimal | None
    coverage: Decimal | None
    assessment_revision_id: str | None
    assessment_basis_sha256: str | None
    window_start: datetime | None
    window_end: datetime | None
    known_at: datetime | None
    room_asset_id: str | None
    evidence: tuple[EvidenceUse, ...] = ()
    link_rows: tuple[LinkRow, ...] = ()
    #: Q4 (corrected): the selected episode has no recorded end (both end bounds null).
    episode_open: bool = False


@dataclass(frozen=True)
class ColdConsequence:
    """One `cold_consequence_revision` to append (server times omitted, Q6) and its evidence links."""

    tenant_id: str
    site_id: str
    finding_revision_id: str
    finding_id: str
    episode_revision_id: str
    assessment_revision_id: str
    kind: str
    state: str
    reason: str
    window_start: datetime
    window_end: datetime
    room_asset_id: str
    overlap_group: str
    quantity_unit: str
    quantity_low: str | None
    quantity_high: str | None
    finding_basis_sha256: str
    consequence_basis_sha256: str
    model_id: str
    source_classification: str
    source_gate_sha256: str
    limitation: str | None
    evidence: tuple[EvidenceUse, ...]
    assumption_revision_ids: tuple[str, ...] = field(default_factory=tuple)


def merged_evidence(episode_links: Iterable[EvidenceUse], finding_cited: Iterable[str]) -> tuple[EvidenceUse, ...]:
    """Every exact accepted ID the pinned Finding and episode cite: the episode's links with their use/reason, plus
    each Finding-cited ID as SUPPORT unless the episode already links it as SUPPORT. One row per (ID, use)."""
    by: dict[tuple[str, str], EvidenceUse] = {}
    for link in episode_links:
        key = (str(link.evidence_id).lower(), link.use)
        by.setdefault(key, EvidenceUse(key[0], link.use, link.reason))
    for evidence_id in finding_cited:
        key = (str(evidence_id).lower(), "SUPPORT")
        by.setdefault(key, EvidenceUse(key[0], "SUPPORT", None))
    return tuple(sorted(by.values(), key=lambda e: (e.evidence_id, USES.index(e.use))))


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if value is None or isinstance(value, (bool, int, str)):
        return value
    return str(value)


def source_gate(basis: ColdBasis) -> tuple[str, str]:
    """(aggregate S4-05 class, gate SHA-256) of exactly the cited accepted IDs."""
    ids = sorted({e.evidence_id for e in basis.evidence})
    result = classify(ids, {r.requested_id: link_of(r) for r in basis.link_rows})
    return result["state"], sha256_canonical(_plain(result))


def check_basis(basis: ColdBasis, work: Mapping[str, Any]) -> None:
    """Refuse a missing, foreign or unpaired exact basis (`COLD_BASIS_MISMATCH`); never fall back to a latest row."""
    def refuse(detail: str) -> None:
        raise ColdBasisMismatch(f"FindingRevision {basis.finding_revision_id}: {detail}")

    if basis.episode_revision_id is None:
        refuse(f"claim episode revision {basis.claim.get('episode_revision_id')!r} is not in this Site")
    if str(basis.claim.get("episode_revision_id", "")).lower() != basis.episode_revision_id:
        refuse("claim episode revision does not match the read episode revision")
    if str(basis.claim.get("episode_id", "")).lower() != basis.episode_id:
        refuse(f"claim episode {basis.claim.get('episode_id')!r} is not episode {basis.episode_id}")
    if basis.claim.get("kind") != basis.episode_kind:
        refuse(f"claim kind {basis.claim.get('kind')!r} is not episode kind {basis.episode_kind!r}")
    if basis.assessment_revision_id is None or basis.finding_assessment_revision_id != basis.assessment_revision_id:
        refuse("its assessment revision is not in this Site")
    if basis.episode_assessment_revision_id != basis.finding_assessment_revision_id:
        refuse(f"episode revision assessment {basis.episode_assessment_revision_id} is not the Finding's "
               f"assessment {basis.finding_assessment_revision_id}")
    if (basis.window_start, basis.window_end) != (work["window_start"], work["window_end"]):
        refuse("the assessment window is not the work window")
    if basis.room_asset_id != str(work["room_asset_id"]).lower():
        refuse("the assessment chamber room is not the work room")
    cause = work["cause"]
    if cause == "FINDING_REVISION_APPENDED" and str(work["finding_revision_id"]).lower() != basis.finding_revision_id:
        refuse("it is not the work's FindingRevision")
    if cause == "EPISODE_REVISION_APPENDED" and str(work["episode_revision_id"]).lower() != basis.episode_revision_id:
        refuse("its claim does not name the work's episode revision")


def warranted(basis: ColdBasis) -> bool:
    """Only a selected, warranted EXCURSION FindingRevision gets an exposure revision."""
    return (basis.finding_lifecycle == "SUPPORTED" and basis.claim.get("kind") == "EXCURSION"
            and basis.episode_kind == "EXCURSION")


def basis_document(basis: ColdBasis, *, quantity_low: str | None, quantity_high: str | None,
                   source_classification: str, source_gate_sha256: str) -> dict[str, Any]:
    assert basis.window_start is not None and basis.window_end is not None and basis.known_at is not None
    return {
        "model_id": MODEL_EXPOSURE,
        "kind": KIND_EXPOSURE,
        "finding_revision_id": basis.finding_revision_id,
        "finding_basis_sha256": basis.finding_basis_sha256,
        "episode_revision_id": basis.episode_revision_id,
        "episode_basis_sha256": basis.episode_basis_sha256,
        "assessment_revision_id": basis.assessment_revision_id,
        "assessment_basis_sha256": basis.assessment_basis_sha256,
        "window": [selected_instant(basis.window_start), selected_instant(basis.window_end)],
        "known_at": selected_instant(basis.known_at),
        "evidence": [[e.evidence_id, e.use, e.reason] for e in basis.evidence],
        "quantity": {"unit": UNIT_DEG_C_MIN, "low": quantity_low, "high": quantity_high},
        "source_classification": source_classification,
        "source_gate_sha256": source_gate_sha256,
        "assumption_revision_ids": [],
        "missing_assumptions": list(MISSING_ASSUMPTIONS),
    }


def basis_sha256(document: Mapping[str, Any]) -> str:
    return sha256_canonical(_plain(document))


def derive(basis: ColdBasis) -> ColdConsequence | None:
    """The `PRODUCT_EXPOSURE` revision of one checked basis, or None when the FindingRevision warrants none."""
    if not warranted(basis):
        return None
    assert basis.episode_revision_id and basis.assessment_revision_id and basis.room_asset_id
    assert basis.window_start is not None and basis.window_end is not None
    classification, gate_sha = source_gate(basis)
    low, high = decimal_text(basis.degree_minutes_low), decimal_text(basis.degree_minutes_high)
    technical: list[str] = []
    if basis.claim_level == "CONTRADICTORY":
        technical.append(LIMIT_CONTRADICTORY)
    elif basis.claim_level == "POSSIBLE":
        technical.append(LIMIT_CLAIM_POSSIBLE)
    elif basis.claim_level not in PROVED_LEVELS:
        technical.append(LIMIT_CLAIM_UNKNOWN)
    if basis.coverage is None or Decimal(basis.coverage) < COVERAGE_FLOOR:
        technical.append(LIMIT_COVERAGE)
    if low is None:
        technical.append(LIMIT_LOWER_UNKNOWN)
    source_withheld = classification not in PERMITTED_CLASSES
    source_limit = {MIXED: LIMIT_SOURCE_MIXED}.get(classification, LIMIT_SOURCE_UNKNOWN)
    limits = ([source_limit] if source_withheld else []) + technical
    if technical:
        low = high = None  # missing-probe/contradictory: the technical quantity is not proved
    elif basis.episode_open or high is None:
        # Q4 corrected: an open episode keeps its proved low; W2-03's finite observed-segment high is not a high for
        # total episode exposure.
        high = None
        limits.append(LIMIT_OPEN_UPPER)
    if source_withheld or technical:
        state, reason = STATE_WITHHELD, (REASON_SOURCE_WITHHELD if source_withheld else REASON_TECHNICAL_WITHHELD)
    else:
        state, reason = STATE_UNPRICED, REASON_UNPRICED
    document = basis_document(basis, quantity_low=low, quantity_high=high,
                              source_classification=classification, source_gate_sha256=gate_sha)
    return ColdConsequence(
        tenant_id=basis.tenant_id, site_id=basis.site_id, finding_revision_id=basis.finding_revision_id,
        finding_id=basis.finding_id, episode_revision_id=basis.episode_revision_id,
        assessment_revision_id=basis.assessment_revision_id, kind=KIND_EXPOSURE, state=state, reason=reason,
        window_start=basis.window_start, window_end=basis.window_end, room_asset_id=basis.room_asset_id,
        overlap_group=overlap_group(basis.tenant_id, basis.site_id, basis.window_start, basis.window_end,
                                    basis.room_asset_id),
        quantity_unit=UNIT_DEG_C_MIN, quantity_low=low, quantity_high=high,
        finding_basis_sha256=basis.finding_basis_sha256, consequence_basis_sha256=basis_sha256(document),
        model_id=MODEL_EXPOSURE, source_classification=classification, source_gate_sha256=gate_sha,
        limitation="; ".join(limits) if limits else None, evidence=basis.evidence)
