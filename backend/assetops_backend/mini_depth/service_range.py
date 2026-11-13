"""SR-7a (sequence doc rev 10 §10.3, rev 10a D-SR.26): mini-grid critical-load Service over a date range.

`service_range_body` composes `site-service-range-1` from ONE chain day read (`ChainRequest.day`, the memoised
`chain.day` snapshot rows) and nothing else: per Site-local day the stored `critical_served` snapshot value
(`chain/measure_impls.py` `mini.critical_served@1`: served/demand/unserved kWh as decimal text) and its row's
`covered_seconds` / `required_seconds` (D-SR.26: hours = seconds / 3600; D-SR.15 stored rows only). No hour is
recomputed, and no all-load or interruption figure is invented over the range (those exist per hour only).

Day state (D-SR.26; gap states are the SR-5a names, read from the chain grade):
- no snapshot row reads as NO_DATA (the chain's own missing-row rule, `chain.read.day_gaps`) -> NO_READINGS;
- NOT_EXPECTED -> NOT_EXPECTED; PENDING -> STILL_PROCESSING; LOW -> NOT_ENOUGH_READINGS ("not counted",
  `chain.vocabulary.READINGS_TERMS`);
- COMPLETE / PARTIAL with a value (D-SR.45: PARTIAL carries `partial: true`): SHORTFALL when `unserved_kwh` > 0, else SERVED_ALL (these are the counted days);
- COMPLETE / PARTIAL without a value: NO_VALUE ("No critical-load figure for this day").
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping
from urllib.parse import quote, urlencode
from zoneinfo import ZoneInfo

from assetops_backend.chain.grading import COMPLETE, LOW, NO_DATA, NOT_EXPECTED, PARTIAL, PENDING

SCHEMA = "site-service-range-1"
MEASURE = "critical_served"
SUBJECT = "SITE"

SERVED_ALL, SHORTFALL, NO_VALUE = "SERVED_ALL", "SHORTFALL", "NO_VALUE"
NO_READINGS, NOT_ENOUGH_READINGS, STILL_PROCESSING = "NO_READINGS", "NOT_ENOUGH_READINGS", "STILL_PROCESSING"
COUNTED = (SERVED_ALL, SHORTFALL)
_GAP_OF_GRADE = {NO_DATA: NO_READINGS, NOT_EXPECTED: NOT_EXPECTED, PENDING: STILL_PROCESSING,
                 LOW: NOT_ENOUGH_READINGS}
_ANALYSED = (COMPLETE, PARTIAL)
_HOUR = Decimal(3600)


def _dec(text: Any) -> Decimal | None:
    if text is None:
        return None
    try:
        return Decimal(str(text))
    except (InvalidOperation, ValueError):
        return None


def _hours(seconds: Any) -> float | None:
    return None if seconds is None else float((Decimal(int(seconds)) / _HOUR).quantize(Decimal("0.01")))


def _wire(at: datetime | None) -> str | None:
    return None if at is None else at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def hour_link(site_code: str, day: date, tz: str | None) -> str:
    """The drill-in: the existing one-hour Service page at the day's Site-local 12:00 (`DEFAULT_SERVICE_HOUR`)."""
    zone = ZoneInfo(tz) if tz else timezone.utc
    lo = datetime.combine(day, time(12), tzinfo=zone)
    q = urlencode({"from": _wire(lo), "to": _wire(lo + timedelta(hours=1))})
    return f"/sites/{quote(site_code, safe='')}/performance/service?{q}"


def day_state(grade: str | None, value: Mapping[str, Any] | None) -> str:
    grade = NO_DATA if grade is None else grade
    if grade not in _ANALYSED:
        return _GAP_OF_GRADE.get(grade, NO_READINGS)
    if value is None:
        return NO_VALUE
    unserved = _dec(value.get("unserved_kwh"))
    return SHORTFALL if unserved is not None and unserved > 0 else SERVED_ALL


def _row_of(rows: Iterable[Any], day: date) -> Any:
    for r in rows:
        if r.local_day == day and r.measure == MEASURE and r.subject_ref == SUBJECT:
            return r
    return None


def service_range_body(site: Mapping[str, Any], facts: Any, days: Iterable[date], *, lo: datetime, hi: datetime,
                       known_at: datetime | None) -> dict[str, Any]:
    """`site` = {site_code, site_name, timezone}; `facts` = the `DayFacts` of `days` (one `ChainRequest.day`)."""
    code, tz = site["site_code"], site.get("timezone")
    rows = tuple(getattr(facts, "rows", ()) or ())
    out: list[dict[str, Any]] = []
    sums = {"served_kwh": Decimal(0), "unserved_kwh": Decimal(0), "demand_kwh": Decimal(0)}
    counted = 0
    for d in sorted(days):
        grade = ((facts.grades.get(d) or {}).get(MEASURE) or {}).get(SUBJECT)
        value = ((facts.values.get(d) or {}).get(MEASURE) or {}).get(SUBJECT)
        state = day_state(grade, value)
        row = _row_of(rows, d)
        shown = value if state in COUNTED else None
        if state in COUNTED:
            counted += 1
            for key in sums:
                sums[key] += _dec(value.get(key)) or Decimal(0)
        out.append({
            "local_day": d.isoformat(), "grade": grade,
            **{key: None if shown is None else shown.get(key) for key in ("served_kwh", "unserved_kwh", "demand_kwh")},
            "covered_hours": None if row is None else _hours(row.covered_seconds),
            "operating_hours": None if row is None else _hours(row.required_seconds),
            "state": state, "partial": state in COUNTED and grade == PARTIAL, "hour_link": hour_link(code, d, tz)})
    return {
        "schema_version": SCHEMA,
        "site": {"site_code": code, "site_name": site.get("site_name"), "timezone": tz},
        "window": {"from": _wire(lo), "to": _wire(hi), "known_at": _wire(known_at),
                   "basis": "CURRENT" if known_at is None else "HISTORICAL"},
        "days": out,
        "totals": {**{key: str(v) if counted else None for key, v in sums.items()},
                   "days_counted": counted, "days_requested": len(out)},
    }


__all__ = ["COUNTED", "NO_VALUE", "SCHEMA", "SERVED_ALL", "SHORTFALL", "day_state", "hour_link",
           "service_range_body"]
