"""CC-R2 (D5): Portfolio placement with reasons, policy `estate-placement/1`.

Pure: `place` reads only the internal Portfolio row's facts, its exact Action (`portfolio._action_for`), the row's
Site coverage (text only, R5.6) and the money group state of the row's line from the same call's `compare()`
result. No query, no score: groups say where to look first, never a value ranking. The rules, reason texts and
confidence texts are fixed by `.agent/build-spec-commercial-2026-10-27.md` "CC-R2" (with the CC-R1-Q1 ruling for
`VERIFIED_WATCH_RETURN`) and Appendix C D5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

POLICY_VERSION = "estate-placement/1"
GROUPS = ("NEEDS_INVESTIGATION", "ACT_NOW", "COMPARE_VALUE", "UNPRICED_RISK", "MONITOR")  # group_rank = index + 1
GROUP_LABEL = {"NEEDS_INVESTIGATION": "Needs investigation first", "ACT_NOW": "Act now",
               "COMPARE_VALUE": "Compare value", "UNPRICED_RISK": "Unpriced risk", "MONITOR": "Monitor"}
CONFIDENCE_STATES = ("SUPPORTED_SOURCE_COHERENT", "LIMITED", "UNKNOWN")

REASON_TEXT = {
    "EVIDENCE_SOURCE_MIXED": "Evidence comes from mixed sources; check the source before acting",
    "EVIDENCE_SOURCE_UNKNOWN": "Evidence source is not resolved; check the source before acting",
    "LIFECYCLE_UNCONFIRMED": "The latest assessment no longer confirms this Finding; check its basis",
    "CONSEQUENCE_WITHHELD": "Cost is withheld because its basis is not current",
    "EPISODE_OPEN": "No end is recorded for this episode",
    "RECURRED": "Returned after an earlier episode ({other})",
    "REOPENED": "Reopened after it had closed",
    "NO_ACTION_RECORDED": "No accepted Action; open the recommendation",
    "ACTION_PENDING": "Action accepted, not yet applied",
    "OUTCOME_PENDING": "Change applied; verification result pending",
    "RESOLUTION_WITHDRAWN": "Earlier resolution withdrawn after new evidence",
    "PRICED_COMPARABLE": "Priced cost exposure; compares with like lines in Financials",
    "PRICED_SINGLE": "Priced cost exposure; no like line to compare with",
    "UNPRICED_PRODUCT_EXPOSURE": "Product temperature risk; no price basis",
    "UNPRICED_START_FAILURE": "Backup start failure; no price basis",
    "UNPRICED_SERVICE_INTERRUPTION": "Charging service interruption; no price basis",
    "UNPRICED_OTHER": "No price basis for this Finding",
    # CC-R1-Q1 ruling: "simulated" stays guarded, so the verified-change text says "test data".
    "VERIFIED_WATCH_RETURN": "Change verified on test data; watch for a return",
    "APPLIED_AWAITING_PLAN": "Change applied; no verified result yet",
    "NO_OPEN_SIGNAL": "No open signal",
}

#: Rule 2: the action reason for each `portfolio.workflow_label` that leaves the work open.
_ACTION_REASON = {"Recommendation not accepted": "NO_ACTION_RECORDED", "No action yet": "ACTION_PENDING",
                  "Pending": "ACTION_PENDING", "Outcome pending": "OUTCOME_PENDING",
                  "Resolution withdrawn": "RESOLUTION_WITHDRAWN"}
#: Rule 3: checked after rule 2 and before COMPARE_VALUE (Q-C6).
_MONITOR_REASON = {"Verified": "VERIFIED_WATCH_RETURN", "Applied": "APPLIED_AWAITING_PLAN"}
#: Rule 5: the unpriced reason per stored mechanism; anything else (mini `GENERATOR_SUPPORT_CANDIDATE`, null) is OTHER.
_UNPRICED_REASON = {"COLD_EXCURSION": "UNPRICED_PRODUCT_EXPOSURE", "COLD_START_FAILURE": "UNPRICED_START_FAILURE",
                    "EV_INTERRUPTION": "UNPRICED_SERVICE_INTERRUPTION"}
_SOURCE_TEXT = {"REGISTERED_SIMULATION": "Generated test data source",
                "AUTHORED_DEMONSTRATION": "Prepared example data source", "MIXED": "Mixed sources"}
_SITE_COVERED = ("CURRENT", "HISTORICAL")
# CC-R2-Q1 ruling: customer words; `claim` and `simulation` stay guarded.
_LIFECYCLE_TEXT = {"UNCONFIRMED": "Unconfirmed Finding", None: "Supported Finding"}
_SOURCE_UNRESOLVED_TEXT = "Source not resolved"
_WITHHELD_TEXT = "Cost basis withheld"
_COVERAGE_TEXT = "Site coverage incomplete; other Findings may be missing"


@dataclass(frozen=True)
class Reason:
    code: str
    text: str


@dataclass(frozen=True)
class Placement:
    group: str
    group_rank: int
    reasons: tuple[Reason, ...]
    confidence: str  # SUPPORTED_SOURCE_COHERENT | LIMITED | UNKNOWN
    confidence_reasons: tuple[str, ...]

    def wire(self) -> dict[str, Any]:
        """The row's public `placement` object (Appendix C D5 wire shape)."""
        return {"policy_version": POLICY_VERSION, "group": self.group, "group_rank": self.group_rank,
                "reasons": [{"code": r.code, "text": r.text} for r in self.reasons]}


def _reason(code: str, row: Mapping[str, Any]) -> Reason:
    if code == "RECURRED":
        return Reason(code, REASON_TEXT[code].format(other="Finding " + str(row["_recurs_after"])[:8]))
    return Reason(code, REASON_TEXT[code])


def _group(name: str, codes: list[str], row: Mapping[str, Any]) -> tuple[str, int, tuple[Reason, ...]]:
    return name, GROUPS.index(name) + 1, tuple(_reason(c, row) for c in codes)


def _rule(row: Mapping[str, Any], label: str, src: str | None, cons: str | None,
          line_group: str | None) -> tuple[str, int, tuple[Reason, ...]]:
    # 1. NEEDS_INVESTIGATION: all that apply, in order.
    first = ((["EVIDENCE_SOURCE_MIXED"] if src == "MIXED" else [])
             + (["EVIDENCE_SOURCE_UNKNOWN"] if src in (None, "UNKNOWN") else [])
             + (["LIFECYCLE_UNCONFIRMED"] if row.get("lifecycle") == "UNCONFIRMED" else [])
             + (["CONSEQUENCE_WITHHELD"] if cons == "WITHHELD" else []))
    if first:
        return _group("NEEDS_INVESTIGATION", first, row)
    # 2. ACT_NOW: a signal (all that apply, in order) and open action work.
    signals = ((["RECURRED"] if row.get("_recurs_after") is not None else [])
               + (["REOPENED"] if row.get("_transition") == "REOPENED" else [])
               + (["EPISODE_OPEN"] if row.get("_episode_end") is None else []))
    if signals and label in _ACTION_REASON:
        return _group("ACT_NOW", [*signals, _ACTION_REASON[label]], row)
    # 3. MONITOR for a verified or applied change (before COMPARE_VALUE, Q-C6).
    if label in _MONITOR_REASON:
        return _group("MONITOR", [_MONITOR_REASON[label]], row)
    # 4. COMPARE_VALUE for a priced exposure.
    if cons == "PRICED":
        return _group("COMPARE_VALUE", ["PRICED_COMPARABLE" if line_group == "COMPARABLE" else "PRICED_SINGLE"], row)
    # 5. UNPRICED_RISK for any other consequence.
    if cons is not None:
        return _group("UNPRICED_RISK", [_UNPRICED_REASON.get(row.get("_mechanism"), "UNPRICED_OTHER")], row)
    # 6. No consequence.
    return _group("MONITOR", ["NO_OPEN_SIGNAL"], row)


def _confidence(row: Mapping[str, Any], src: str | None, cons: str | None,
                site_cov: Mapping[str, Any]) -> tuple[str, tuple[str, ...]]:
    lifecycle = row.get("lifecycle")
    if src in (None, "MIXED", "UNKNOWN"):
        state = "UNKNOWN"
    elif lifecycle == "UNCONFIRMED" or cons == "WITHHELD":
        state = "LIMITED"
    else:
        state = "SUPPORTED_SOURCE_COHERENT"
    reasons = [_LIFECYCLE_TEXT["UNCONFIRMED" if lifecycle == "UNCONFIRMED" else None],
               _SOURCE_TEXT.get(src or "UNKNOWN", _SOURCE_UNRESOLVED_TEXT)]
    if cons == "WITHHELD":
        reasons.append(_WITHHELD_TEXT)
    if (site_cov or {}).get("state") not in _SITE_COVERED:  # R5.6: text only, never a move
        reasons.append(_COVERAGE_TEXT)
    return state, tuple(reasons)


def place(row: Mapping[str, Any], action: Mapping[str, Any] | None, site_cov: Mapping[str, Any],
          line_group: str | None) -> Placement:
    """First match wins over the row's own facts. `action` is the row's exact Action (or None), `site_cov` its
    Site's coverage, `line_group` the money group `state` holding the row's line (None without a line)."""
    from assetops_backend.estate.portfolio import workflow_label  # the one label precedence (closure 5 S7)

    label = workflow_label(action)  # type: ignore[arg-type]
    src = (row.get("source_provenance") or {}).get("state", "UNKNOWN")
    cons = (row.get("consequence") or {}).get("state")
    group, rank, reasons = _rule(row, label, src, cons, line_group)
    confidence, confidence_reasons = _confidence(row, src, cons, site_cov)
    return Placement(group, rank, reasons, confidence, confidence_reasons)
