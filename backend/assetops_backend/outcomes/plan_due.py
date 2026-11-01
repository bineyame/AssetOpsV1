"""POLISH §1.4 (P-09, PA-2b): the one due-state rule of a preventive plan, shared by the board warnings and the global
preventive read.

Only a CALENDAR plan with a due instant is assessed. It is OVERDUE when due strictly before `to` (a plan due exactly
at `to` is not overdue), DUE_SOON when due before `to + 14 days`, and NOT_DUE otherwise. Any other plan (a RUN_HOURS plan,
or a CALENDAR plan with no due instant) is NOT_ASSESSED.
"""
from __future__ import annotations

from typing import Any

CALENDAR = "CALENDAR"
#: The due-soon horizon in days. `outcomes/` stays pure (`test_out_a1_outcome_map`: no `datetime` import), so the
#: horizon is built from the type of `to - to` (a `timedelta`) at call time.
SOON_DAYS = 14
OVERDUE, DUE_SOON, NOT_DUE, NOT_ASSESSED = "OVERDUE", "DUE_SOON", "NOT_DUE", "NOT_ASSESSED"
DUE_STATES = (OVERDUE, DUE_SOON, NOT_DUE, NOT_ASSESSED)


def soon_until(to: Any) -> Any:
    """`to + 14 days`."""
    return to + type(to - to)(days=SOON_DAYS)


def plan_due_state(trigger_kind: str | None, next_due_at: Any, to: Any) -> str:
    """The plan's due state at the read's `to` (both timezone-aware datetimes)."""
    if trigger_kind != CALENDAR or next_due_at is None:
        return NOT_ASSESSED
    if next_due_at < to:
        return OVERDUE
    if next_due_at < soon_until(to):
        return DUE_SOON
    return NOT_DUE
