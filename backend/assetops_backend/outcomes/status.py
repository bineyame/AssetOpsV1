"""OUT-B1: outcome status, policy `outcome-status/1` (build spec outcome sprint 2026-10-29 §1.4, rulings B-Q16/Q17).

Pure. The state of one site-level outcome is the first matching rule; a category row rolls its outcomes up by a
fixed precedence and names the first outcome (catalogue order) holding the winning state. Rows are never combined
into a score. Reason codes stay on the wire for tests and are never rendered."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from assetops_backend.outcomes.catalogue import SiteOutcome
from assetops_backend.outcomes.outcome_map import DOMAIN_ALIAS

STATUS_POLICY = "outcome-status/1"

NOT_APPLICABLE, NOT_MEASURED, UNKNOWN = "NOT_APPLICABLE", "NOT_MEASURED", "UNKNOWN"
NEEDS_ATTENTION, WATCH, OPPORTUNITY = "NEEDS_ATTENTION", "WATCH", "OPPORTUNITY"
ON_TRACK, NO_OBJECTIVE = "ON_TRACK", "NO_OBJECTIVE"

#: Signal kinds. EVIDENCE_GAP is issue-only: it never sets a status (ruling B-Q16).
FINDING, WARNING, SIGNAL_OPPORTUNITY, READINESS, EVIDENCE_GAP = (
    "FINDING", "WARNING", "OPPORTUNITY", "READINESS", "EVIDENCE_GAP")

STATE_LABEL = {
    NOT_APPLICABLE: "N/A", NOT_MEASURED: "Not measured yet", UNKNOWN: "Unknown",
    NEEDS_ATTENTION: "Needs attention", WATCH: "Watch", OPPORTUNITY: "Opportunity",
    ON_TRACK: "On track", NO_OBJECTIVE: "No objective declared"}
STATE_TONE = {  # mock outcomes.js:8; NO_OBJECTIVE gray is D2 (R543)
    NEEDS_ATTENTION: "amber", WATCH: "blue", UNKNOWN: "gray", NO_OBJECTIVE: "gray",
    NOT_MEASURED: "none", NOT_APPLICABLE: "none", ON_TRACK: "green", OPPORTUNITY: "green"}
#: Roll-up precedence, highest first (doc §4.3).
PRECEDENCE = (NEEDS_ATTENTION, WATCH, UNKNOWN, OPPORTUNITY, NO_OBJECTIVE, ON_TRACK, NOT_MEASURED, NOT_APPLICABLE)
_RANK = {state: i for i, state in enumerate(PRECEDENCE)}

LIMITED_READINESS = ("LIMITED", "NONE")


@dataclass(frozen=True)
class Signal:
    kind: str                 # FINDING | WARNING | OPPORTUNITY | READINESS | EVIDENCE_GAP
    outcome: str              # outcome key the signal moves
    primary: bool             # first moved outcome of its map entry
    open: bool
    applied: bool = False     # FINDING: its exact-revision Action is APPLIED or later
    status_effect: str | None = None  # WARNING (C): NEEDS_ATTENTION | WATCH
    ref: str = ""


def _evidence_outcome(outcome: SiteOutcome) -> bool:
    return DOMAIN_ALIAS["@EVIDENCE"].get(outcome.domain) == outcome.key


def outcome_state(outcome: SiteOutcome, *, settled: bool, signals: Sequence[Signal],
                  readiness: str | None, applicable: bool = True) -> tuple[str, str]:
    """(state, reason_code) for one outcome; first match wins (§1.4 rules 1-8)."""
    if not applicable:
        return NOT_APPLICABLE, "CONFIGURATION_NOT_APPLICABLE"
    if not outcome.measured:
        return NOT_MEASURED, "NOT_MEASURED_IN_CATALOGUE"
    if not settled:
        return UNKNOWN, "PRODUCER_NOT_SETTLED"
    mine = [s for s in signals if s.outcome == outcome.key and s.open]
    for s in mine:
        if s.kind == FINDING and s.primary and not s.applied:
            return NEEDS_ATTENTION, "PRIMARY_FINDING_OPEN"
        if s.kind == WARNING and s.status_effect == NEEDS_ATTENTION:
            return NEEDS_ATTENTION, "WARNING_NEEDS_ATTENTION"
    for s in mine:
        if s.kind == FINDING:
            return WATCH, "PRIMARY_FINDING_APPLIED" if s.primary else "SECONDARY_FINDING_OPEN"
        if s.kind == WARNING and s.status_effect == WATCH:
            return WATCH, "WARNING_WATCH"
    if _evidence_outcome(outcome) and readiness in LIMITED_READINESS:
        return WATCH, "EVIDENCE_READINESS_" + readiness
    if any(s.kind == SIGNAL_OPPORTUNITY for s in mine):
        return OPPORTUNITY, "OPPORTUNITY_OPEN"
    return NO_OBJECTIVE, "NO_OBJECTIVE_DECLARED"


def roll_up(states: Sequence[tuple[str, str]]) -> tuple[str, str]:
    """(state, lead outcome key) for a row, from (outcome_key, state) pairs in catalogue order.

    The winner is the highest-precedence state; the lead is the first outcome holding it."""
    if not states:
        raise ValueError("a category row has at least one outcome")
    best = min(states, key=lambda pair: _RANK[pair[1]])[1]
    lead = next(key for key, state in states if state == best)
    return best, lead
