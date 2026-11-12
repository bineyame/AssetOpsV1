"""SR-8 (rev 10 §10.4, rev 10a §10a.3, D-SR.15, D-SR.27): mini-grid Renewable over the whole date range.

`GET /api/sites/{site_code}/renewable-range?from&to[&known_at]`, schema `site-renewable-range-1`. One chain day read
(`ChainRequest.day`, memoised `chain.day`) per request; each Site-local day of the window reads its stored
`daylight_headroom_kw` snapshot row (`chain/measure_impls.py RenewableHeadroom`). No hour is recomputed on read.

Per day (D-SR.27): the stored low-high kW band, the decision, `window_hours` (the ELIGIBLE hour count) and the
row's covered / required seconds over the declared **operating** hours, as hours. Day state:

- a grade gap first: no row, NO_DATA, PENDING or NOT_EXPECTED (a missing row reads NO_DATA, as `chain.read.day_gaps`);
- else the stored value: ELIGIBLE -> COUNTED, EXCLUDED -> EXCLUDED (bounds shown), `result_state` CONFLICT,
  LIMITED or MISSING_HOUR ("Partial: an hour is missing"); a graded row with no value -> NO_VALUE.

Totals: `days_counted` = COUNTED days with both bounds; the average daylight headroom is the mean of `low_kw` and the
mean of `high_kw`, separately, over those days only; `partial` when `days_counted < days_requested`.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Mapping, Sequence
from urllib.parse import quote

from assetops_backend.chain.grading import NO_DATA, NOT_EXPECTED, PENDING
from assetops_backend.chain.read import board_day

SCHEMA_VERSION = "site-renewable-range-1"
MEASURE = "daylight_headroom_kw"
SUBJECT = "SITE"
COUNTED = "COUNTED"
EXCLUDED = "EXCLUDED"
NO_VALUE = "NO_VALUE"
VALUE_STATES = ("CONFLICT", "LIMITED", "MISSING_HOUR")
GAP_GRADES = (NO_DATA, PENDING, NOT_EXPECTED)
STATES = (COUNTED, EXCLUDED, *VALUE_STATES, NO_VALUE, *GAP_GRADES)
AVERAGE_LABEL = "average daylight headroom"
#: The averages are decimal text rounded to this step (kW).
AVERAGE_STEP = Decimal("0.01")


def _iso(at: datetime) -> str:
    return at.strftime("%Y-%m-%dT%H:%M:%SZ")


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return d if d.is_finite() else None


def _hours(seconds: Any) -> float | None:
    return None if seconds is None else round(int(seconds) / 3600, 2)


def day_link(site_code: str, day: date, tz: str | None) -> str:
    """The existing one-day Renewable depth page: `[local midnight, +1 day)` as UTC instants."""
    lo, hi = board_day(day, tz)
    return (f"/sites/{quote(site_code, safe='')}/performance/renewable"
            f"?from={quote(_iso(lo), safe='')}&to={quote(_iso(hi), safe='')}")


def day_state(grade: str | None, value: Mapping[str, Any] | None) -> str:
    """The D-SR.27 day state of one stored `daylight_headroom_kw` row (`grade` None: no row)."""
    if grade is None:
        return NO_DATA
    if grade in GAP_GRADES:
        return grade
    if not value:
        return NO_VALUE
    result_state = value.get("result_state")
    if result_state in VALUE_STATES:
        return result_state
    decision = value.get("decision")
    if decision == "ELIGIBLE":
        return COUNTED
    if decision == "EXCLUDED":
        return EXCLUDED
    return NO_VALUE


def _rows_by_day(rows: Sequence[Any]) -> dict[date, Any]:
    return {r.local_day: r for r in rows if r.measure == MEASURE and r.subject_ref == SUBJECT}


def range_days(site_code: str, tz: str | None, days: Sequence[date], facts: Any) -> list[dict[str, Any]]:
    """One entry per requested Site-local day, from the chain day read's stored rows (`DayFacts`)."""
    rows = _rows_by_day(getattr(facts, "rows", ()) or ())
    out = []
    for d in days:
        grade = ((facts.grades.get(d) or {}).get(MEASURE) or {}).get(SUBJECT)
        value = ((facts.values.get(d) or {}).get(MEASURE) or {}).get(SUBJECT)
        row = rows.get(d)
        state = day_state(grade, value)
        shown = state in (COUNTED, EXCLUDED)
        v = value or {}
        out.append({
            "local_day": d.isoformat(), "grade": grade if grade is not None else NO_DATA,
            "low_kw": v.get("low_kw") if shown else None, "high_kw": v.get("high_kw") if shown else None,
            "decision": v.get("decision"), "window_hours": v.get("window_hours"),
            "covered_hours": None if row is None else _hours(row.covered_seconds),
            "operating_hours": None if row is None else _hours(row.required_seconds),
            "state": state, "link": day_link(site_code, d, tz)})
    return out


def _mean(values: Sequence[Decimal]) -> str | None:
    if not values:
        return None
    return f"{(sum(values, Decimal(0)) / len(values)).quantize(AVERAGE_STEP, rounding=ROUND_HALF_UP):f}"


def totals(days: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counted = [(_dec(d["low_kw"]), _dec(d["high_kw"])) for d in days if d["state"] == COUNTED]
    counted = [(lo, hi) for lo, hi in counted if lo is not None and hi is not None]
    return {"days_requested": len(days), "days_counted": len(counted),
            "average_low_kw": _mean([lo for lo, _ in counted]), "average_high_kw": _mean([hi for _, hi in counted]),
            "average_label": AVERAGE_LABEL, "partial": len(counted) < len(days)}


def compose(site: Mapping[str, Any], window: Mapping[str, Any], days: Sequence[date], facts: Any) -> dict[str, Any]:
    """The `site-renewable-range-1` body. `site` = {site_code, site_name, timezone}; `window` = {from, to, known_at}
    as UTC text; `facts` the `ChainRequest.day` read over `days`."""
    rows = range_days(site["site_code"], site.get("timezone"), days, facts)
    return {"schema_version": SCHEMA_VERSION, "site": dict(site), "window": dict(window), "days": rows,
            "totals": totals(rows)}
