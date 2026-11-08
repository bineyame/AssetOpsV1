"""DIESEL-K4a (`.agent/build-sheet-DIESEL-1.md` §9j.4, §9j.6, ruling DIESEL-1-R3j): raise the unexplained-fuel
Finding of one stored night, explicitly (no tick stage).

`raise_night` runs in one transaction, the cold worker's pattern (`analytics/assessment_worker.py:250`, the
assessment store's `transaction()` shared across the assessment, Finding and consequence stores):

1. `known_at` (the transaction's `clock_timestamp()`, or the composition's test-only override), the per-night lock
   `hashtext('fuel-finding:' || site_id || ':' || night_date)`, and the night's latest window revision as known then;
   none -> `NO_WINDOW`;
2. §9j.4's lifecycle table (`fuel_transition`); when a Finding must be written: `fuel_balance_persist`, then
   `fuel_apply`, which calls `fuel_residual_append` for a SUPPORTED revision with the one declared diesel price over
   the window as known at its end.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable
from uuid import UUID

OPENED, REVISED, WITHDRAWN, UNCHANGED, NO_FINDING, NO_WINDOW = (
    "OPENED", "REVISED", "WITHDRAWN", "UNCHANGED", "NO_FINDING", "NO_WINDOW")
_STATUS = {"OPENED": OPENED, "SUPPORT_CHANGED": REVISED, "NO_LONGER_SUPPORTED": WITHDRAWN}


def fuel_transition(held: bool, held_window_id: str | None, window_id: str, state: str) -> tuple[str, str] | None:
    """§9j.4's lifecycle table (first match wins): the `(transition, lifecycle)` to write, or None for no write.

    | held | latest window W | write |
    | none | UNEXPLAINED | OPENED / SUPPORTED |
    | none | anything else | nothing |
    | held, its latest revision cites W | any | nothing (idempotent) |
    | held | UNEXPLAINED | SUPPORT_CHANGED / SUPPORTED |
    | held | not UNEXPLAINED | NO_LONGER_SUPPORTED / NO_LONGER_SUPPORTED |
    """
    if not held:
        return ("OPENED", "SUPPORTED") if state == "UNEXPLAINED" else None
    if held_window_id is not None and str(held_window_id) == str(window_id):
        return None
    if state == "UNEXPLAINED":
        return "SUPPORT_CHANGED", "SUPPORTED"
    return "NO_LONGER_SUPPORTED", "NO_LONGER_SUPPORTED"


@dataclass(frozen=True)
class RaiseResult:
    status: str
    finding_id: UUID | None
    revision_id: UUID | None


@dataclass(frozen=True)
class FuelFindingStores:
    """Wired by `fuel_balance/composition.py`: the fuel-balance store (`night_window_on`), the assessment store
    (`transaction`, `fuel_balance_persist`), the Finding store (`fuel_held`, `fuel_apply`), the consequence store
    (`fuel_residual_append`) and `price_selection(tenant, site, start, end, known_at)`."""

    fuel: Any
    assessments: Any
    findings: Any
    consequences: Any
    price_selection: Callable[[UUID, UUID, datetime, datetime, datetime], Any]


class FuelFindingService:
    def __init__(self, stores: FuelFindingStores) -> None:
        self.stores = stores

    def dispose(self) -> None:
        for store in (self.stores.fuel, self.stores.assessments, self.stores.findings, self.stores.consequences):
            close = getattr(store, "dispose", None)
            if callable(close):
                close()

    def raise_night(self, tenant_id: UUID, site_id: UUID, night_date: date) -> RaiseResult:
        st = self.stores
        with st.assessments.transaction() as c:
            known_at, window = st.fuel.night_window_on(c, tenant_id, site_id, night_date)
            if window is None:
                return RaiseResult(NO_WINDOW, None, None)
            held = st.findings.fuel_held(c, tenant_id, site_id, window)
            decided = fuel_transition(held is not None, None if held is None else held[1], str(window.id),
                                      window.state)
            if decided is None:
                return RaiseResult(NO_FINDING if held is None else UNCHANGED,
                                   None if held is None else held[0], None)

            def consequence(conn: Any, finding_id: UUID, revision_id: UUID, w: Any, now: datetime) -> None:
                price = st.price_selection(tenant_id, site_id, w.window_start, w.window_end, w.window_end)
                st.consequences.fuel_residual_append(conn, tenant_id, site_id, finding_id, revision_id, w, price, now)

            persisted = st.assessments.fuel_balance_persist(c, window, known_at)
            written = st.findings.fuel_apply(c, tenant_id, site_id, window, persisted, consequence, known_at)
            if not written:
                return RaiseResult(UNCHANGED, None if held is None else held[0], None)
            after = st.findings.fuel_held(c, tenant_id, site_id, window)
            return RaiseResult(_STATUS[decided[0]], None if after is None else after[0], written[0])
