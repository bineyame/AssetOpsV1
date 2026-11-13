"""D-SR.22: the one per-day state rule of a mini-grid Site over a range (rev 9 §9.4 SR-5a, rev 10a).

`range_day_states(snap, tenant_id, site, req, scope, cov)` gives each UTC day of `[req.from_, req.to)` (the
`dispatch.day` grain) its state and dispatch row, on the caller's one snapshot:
- precedence in D-E5.46 table order: NOT_EXPECTED, NO_READINGS, STILL_PROCESSING (PENDING grade or open jobs),
  READINGS_CONFLICT / NOT_ENOUGH_READINGS, NOT_ANALYSED (no available selection), STILL_PROCESSING (selected but not
  yet matched, as the coverage reads it: PENDING, never a gap), else ANALYSED;
- coverage wins: the gap set, with reasons, equals `cov["days"]["gaps"]`; a disagreement takes the coverage's reason
  (or ANALYSED when the coverage names no gap) and is logged `site_range_day_mismatch`.
SR-5a maps ANALYSED to FINDINGS/CLEAR by its finding count; SR-6 shows ANALYSED. Imports only; no AR-4 file edited.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from assetops_backend.estate.coverage import _day_of, data_gap_days, dispatch_days, local_day_grades_kw

LOG = logging.getLogger("assetops.site_range")

ANALYSED, NO_READINGS, READINGS_CONFLICT, NOT_ENOUGH_READINGS, NOT_ANALYSED, STILL_PROCESSING, NOT_EXPECTED = (
    "ANALYSED", "NO_READINGS", "READINGS_CONFLICT", "NOT_ENOUGH_READINGS", "NOT_ANALYSED", "STILL_PROCESSING",
    "NOT_EXPECTED")
#: The four gap states and the coverage `days.gaps[].reason` each one equals (D-E5.46). A coverage read without day
#: grades names an unchecked day NO_ASSESSED_SELECTION; it is the same fact as NOT_ANALYSED.
GAP_STATES = (NO_READINGS, READINGS_CONFLICT, NOT_ENOUGH_READINGS, NOT_ANALYSED)
STATE_OF_REASON = {"NO_READINGS": NO_READINGS, "READINGS_CONFLICT": READINGS_CONFLICT,
                   "NOT_ENOUGH_READINGS": NOT_ENOUGH_READINGS, "NOT_ANALYSED": NOT_ANALYSED,
                   "NO_ASSESSED_SELECTION": NOT_ANALYSED}
_OPEN_JOBS = {"PENDING", "LEASED"}
_NO_DATA, _PENDING_GRADE, _NOT_EXPECTED = "NO_DATA", "PENDING", "NOT_EXPECTED"


def range_days(from_: datetime, to: datetime) -> list[date]:
    """The UTC calendar days of `[from_, to)` (the `dispatch.day` grain; `from_`/`to` are UTC midnights)."""
    first, out = from_.astimezone(timezone.utc).date(), []
    while datetime.combine(first, time(0), tzinfo=timezone.utc) < to:
        out.append(first)
        first += timedelta(days=1)
    return out


def day_state(row: dict[str, Any] | None, grade: str | None, reason: str | None) -> str:
    """The precedence above for one day; `reason` is the day's `data_gap_days` state, if any."""
    if grade == _NOT_EXPECTED:
        return NOT_EXPECTED
    if grade == _NO_DATA:
        return NO_READINGS
    jobs = {j.get("status") for j in (row or {}).get("jobs") or ()}
    if grade == _PENDING_GRADE or jobs & _OPEN_JOBS:
        return STILL_PROCESSING
    if reason is not None:
        return reason
    if row is None or not row.get("available") or row.get("selection") is None:
        return NOT_ANALYSED
    if row.get("_unmatched"):
        return STILL_PROCESSING
    return ANALYSED


def range_day_states(snap: Any, tenant_id: Any, site: dict[str, Any], req: Any, scope: dict[str, Any],
                     cov: dict[str, Any]) -> dict[date, dict[str, Any]]:
    """`{day: {"state", "row"}}` for every UTC day of the request window (module doc)."""
    k = scope["k"]
    rows = dispatch_days(snap, tenant_id, site["site_id"], req.from_, req.to, k)
    reasons = {d: STATE_OF_REASON[r] for d, r in data_gap_days(rows).items()}
    grades = local_day_grades_kw(site, req, scope, tenant_id).get("day_grades")
    index = snap.finding_index(tenant_id, site["site_id"], k) if hasattr(snap, "finding_index") else {}
    match = (index or {}).get("match_pass")
    deferred = set((index or {}).get("deferred_windows") or ())
    by_day: dict[date, dict[str, Any]] = {}
    for row in rows:  # `_mini_grid_basis`'s matched rule
        sel = row.get("selection")
        unmatched = sel is not None and row.get("available") and (
            match is None or match["matched_through_selection_seq"] < int(sel["seq"])
            or row.get("window_start") in deferred)
        by_day[_day_of(row)] = {**row, "_unmatched": bool(unmatched)}

    cov_days = cov.get("days") or None
    cov_gaps = None if cov_days is None else {
        date.fromisoformat(g["day"]): STATE_OF_REASON.get(g["reason"], NOT_ANALYSED) for g in cov_days["gaps"]}
    out: dict[date, dict[str, Any]] = {}
    for d in range_days(req.from_, req.to):
        row = by_day.get(d)
        state = day_state(row, None if grades is None else grades.get(d), reasons.get(d))
        if cov_gaps is not None:  # coverage wins
            want = cov_gaps.get(d)
            if want is not None and state != want:
                LOG.warning("site_range_day_mismatch site=%s day=%s state=%s coverage=%s",
                            site["site_code"], d.isoformat(), state, want)
                state = want
            elif want is None and state in GAP_STATES:
                LOG.warning("site_range_day_mismatch site=%s day=%s state=%s coverage=none",
                            site["site_code"], d.isoformat(), state)
                state = ANALYSED
        out[d] = {"state": state, "row": row}
    return out
