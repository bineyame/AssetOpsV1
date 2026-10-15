"""S5-01 one-Finding money state for the selected-window Site Overview (`tasks/S5-01-site-overview.md`).

A pure precedence function: it reads nothing and decides whether the selected Finding's exact-head consequence may
show a current amount, else which typed no-amount state limits it. Precedence (packet "S5 no-amount states"):

1. `SOURCE_CLOSED` - the Performance source gate is closed.
2. Upstream: `UPSTREAM_FAILED`, `UPSTREAM_STALE`, `UPSTREAM_PENDING`, `UPSTREAM_UNASSESSED` from the S5 upstream
   currentness (S3, S4 and schedule blockers, `S3_UNASSESSED` included), or a basis that moved during the read.
   Blockers that are only consequence work are judged per Finding in step 6, and still block a current amount.
3. `ABSENT` only after complete, current discovery found no intersecting canonical Finding.
4. LR-01 shared gate (`financials/money_eligibility.py`), raw and never rewritten here (Architect LR-01 deviations
   item 2): `PENDING_REASSESSMENT`, then `WITHHELD_GENERATOR_SERIES`. Any state other than `ELIGIBLE` is pending.
5. `SUPERSEDED` - the selected FindingRevision is not the Finding's latest, or the Finding was merged.
6. `CONSEQUENCE_PENDING`, `CONSEQUENCE_STALE` - the exact read's currentness, a head that moved from the seam's
   `head_consequence_revision_id`, or any outstanding consequence blocker of the window.
7. `QUANTITY_UNAVAILABLE`, `UNPRICED`, `MINOR_UNIT_UNKNOWN` from the exact-head consequence row.
8. `MIXED_OR_UNKNOWN_SOURCE` - the provenance input could not resolve the Finding's source (today: the unverified
   demonstration label; S4-05 replaces that input with a stored provenance resolver).
9. `PRICED` only when every gate above passed and the exact read itself presents the head as the current amount.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PRICED = "PRICED"
ABSENT = "ABSENT"
PENDING_REASSESSMENT = "PENDING_REASSESSMENT"
WITHHELD_GENERATOR_SERIES = "WITHHELD_GENERATOR_SERIES"
SOURCE_CLOSED = "SOURCE_CLOSED"
UPSTREAM_UNASSESSED = "UPSTREAM_UNASSESSED"
UPSTREAM_PENDING = "UPSTREAM_PENDING"
UPSTREAM_STALE = "UPSTREAM_STALE"
UPSTREAM_FAILED = "UPSTREAM_FAILED"
SUPERSEDED = "SUPERSEDED"
CONSEQUENCE_PENDING = "CONSEQUENCE_PENDING"
CONSEQUENCE_STALE = "CONSEQUENCE_STALE"
QUANTITY_UNAVAILABLE = "QUANTITY_UNAVAILABLE"
UNPRICED = "UNPRICED"
MINOR_UNIT_UNKNOWN = "MINOR_UNIT_UNKNOWN"
MIXED_OR_UNKNOWN_SOURCE = "MIXED_OR_UNKNOWN_SOURCE"

NO_AMOUNT_STATES = (ABSENT, PENDING_REASSESSMENT, WITHHELD_GENERATOR_SERIES, SOURCE_CLOSED, UPSTREAM_UNASSESSED,
                    UPSTREAM_PENDING, UPSTREAM_STALE, UPSTREAM_FAILED, SUPERSEDED, CONSEQUENCE_PENDING,
                    CONSEQUENCE_STALE, QUANTITY_UNAVAILABLE, UNPRICED, MINOR_UNIT_UNKNOWN, MIXED_OR_UNKNOWN_SOURCE)

UPSTREAM_STATE = {"FAILED": UPSTREAM_FAILED, "STALE_PROJECTION": UPSTREAM_STALE, "PENDING": UPSTREAM_PENDING,
                  "UNASSESSED": UPSTREAM_UNASSESSED}

#: Upstream reason codes the seam raises for consequence work (judged per Finding, step 6); every other code,
#: known or not, is an S3/S4/schedule blocker (fail closed).
CONSEQUENCE_CODES = frozenset({"STALE_NO_WORK", "WORK_OUTSTANDING"})


def is_consequence_code(code: str) -> bool:
    return code in CONSEQUENCE_CODES or code.startswith("CONSEQUENCE_")


@dataclass(frozen=True)
class MoneyInputs:
    source_open: bool
    upstream_status: str  # CURRENT | PENDING | STALE_PROJECTION | FAILED | UNASSESSED
    upstream_reasons: tuple[str, ...] = ()
    basis_moved: bool = False  # an accepted-source, selection or head fence moved during this read
    discovery_complete: bool = False
    finding_selected: bool = False
    eligibility: str | None = None  # the raw shared LR-01 gate state
    revision_is_latest: bool = False
    merged: bool = False
    consequence_state: str | None = None  # the exact read: CURRENT | STALE | PENDING | HISTORICAL | AUDIT_ONLY
    head_matches_seam: bool = False
    consequence_row_state: str | None = None  # PRICED | UNPRICED | QUANTITY_UNAVAILABLE
    quantity_state: str | None = None  # AVAILABLE | QUANTITY_UNAVAILABLE
    price_state: str | None = None  # PRICED | UNPRICED | NOT_EVALUATED
    display_state: str | None = None  # ROUNDED_OUTWARD | MINOR_UNIT_UNKNOWN | None
    provenance_resolved: bool = True
    presented_as_current: bool = False


def money_state(i: MoneyInputs) -> str:
    if not i.source_open:
        return SOURCE_CLOSED
    upstream_blockers = [c for c in i.upstream_reasons if not is_consequence_code(c)]
    if i.upstream_status != "CURRENT" and (upstream_blockers or not i.upstream_reasons):
        return UPSTREAM_STATE.get(i.upstream_status, UPSTREAM_PENDING)
    if i.basis_moved:
        return UPSTREAM_PENDING
    if not i.finding_selected:
        return ABSENT if i.discovery_complete and i.upstream_status == "CURRENT" else UPSTREAM_PENDING
    if i.eligibility == WITHHELD_GENERATOR_SERIES:
        return WITHHELD_GENERATOR_SERIES
    if i.eligibility != "ELIGIBLE":
        return PENDING_REASSESSMENT
    if not i.revision_is_latest or i.merged or i.consequence_state == "HISTORICAL":
        return SUPERSEDED
    if i.consequence_state == "AUDIT_ONLY":
        return SOURCE_CLOSED
    if i.consequence_state == "PENDING" or i.consequence_row_state is None:
        return CONSEQUENCE_PENDING
    if i.consequence_state != "CURRENT" or not i.head_matches_seam or i.upstream_status != "CURRENT":
        return CONSEQUENCE_STALE
    if i.quantity_state != "AVAILABLE" or i.consequence_row_state == QUANTITY_UNAVAILABLE:
        return QUANTITY_UNAVAILABLE
    if i.price_state != "PRICED" or i.consequence_row_state != "PRICED":
        return UNPRICED
    if i.display_state != "ROUNDED_OUTWARD":
        return MINOR_UNIT_UNKNOWN
    if not i.provenance_resolved:
        return MIXED_OR_UNKNOWN_SOURCE
    return PRICED if i.presented_as_current else CONSEQUENCE_STALE
