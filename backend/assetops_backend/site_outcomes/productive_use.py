"""WALK1-3 §4.3: measured energy used by declared productive users, read at request time (no stored number).

Pure: the caller passes accepted `feeder_demand` interval readings of the LOAD components the Site configuration
declares `supply-use = PRODUCTIVE`. Each reading is a mapping with `start` and `end` (aware datetimes), `value_kw`
(a decimal-able average power over the interval) and `quality`. Only GOOD readings count; any other quality is a
gap, never a zero. Energy is the exact sum of `value_kw x clipped seconds / 3600` inside `[lo, hi)`;
`measured_seconds` is the union of GOOD coverage inside `[lo, hi)`, so the copy can name the measured hours and never
scale them to a whole day.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

GOOD = "GOOD"
SECONDS_PER_HOUR = Decimal(3600)


def _clip(r: Mapping[str, Any], lo: datetime, hi: datetime) -> tuple[datetime, datetime] | None:
    start, end = r.get("start"), r.get("end")
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        return None
    s, e = max(start, lo), min(end, hi)
    return (s, e) if s < e else None


def _value(r: Mapping[str, Any]) -> Decimal | None:
    try:
        v = Decimal(str(r.get("value_kw")))
    except (InvalidOperation, ValueError):
        return None
    return v if v.is_finite() else None


def productive_energy(readings: Iterable[Mapping[str, Any]], lo: datetime, hi: datetime) -> dict[str, Any]:
    """`{"kwh": Decimal | None, "measured_seconds": int, "evidence_count": int}`; `kwh` is None when no GOOD
    reading overlaps the window."""
    kw_seconds = Decimal(0)
    spans: list[tuple[datetime, datetime]] = []
    count = 0
    for r in readings:
        if r.get("quality") != GOOD:
            continue
        clipped = _clip(r, lo, hi)
        value = _value(r)
        if clipped is None or value is None:
            continue
        s, e = clipped
        seconds = Decimal((e - s).total_seconds())
        kw_seconds += value * seconds
        spans.append(clipped)
        count += 1
    if not count:
        return {"kwh": None, "measured_seconds": 0, "evidence_count": 0}
    covered = 0
    cur_s, cur_e = None, None
    for s, e in sorted(spans):
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                covered += int((cur_e - cur_s).total_seconds())
            cur_s, cur_e = s, e
        elif e > cur_e:
            cur_e = e
    covered += int((cur_e - cur_s).total_seconds())
    return {"kwh": kw_seconds / SECONDS_PER_HOUR, "measured_seconds": covered, "evidence_count": count}
