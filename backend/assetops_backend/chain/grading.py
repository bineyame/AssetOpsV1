"""Pure day grading for snapshots (design §5.2 A1, AG-4).

Every snapshot grade comes from :func:`classify_day`; there is no second
day-count rule anywhere in the chain package.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo

from .policy import (
    MIDDAY_WINDOW_LOCAL,
    PERIOD_MIDDAY,
    PERIOD_OPERATING_HOURS,
    Bands,
    CalendarEntry,
)

COMPLETE = "COMPLETE"
PARTIAL = "PARTIAL"
LOW = "LOW"
NO_DATA = "NO_DATA"
NOT_EXPECTED = "NOT_EXPECTED"
PENDING = "PENDING"
GRADES = (COMPLETE, PARTIAL, LOW, NO_DATA, NOT_EXPECTED, PENDING)


def _local_minute_to_utc(local_day: date, minute: int, tz: ZoneInfo) -> datetime:
    # Anchor through the wall clock so a DST zone resolves the local time itself.
    wall = datetime.combine(local_day + timedelta(days=minute // 1440), time(0)) + timedelta(
        minutes=minute % 1440
    )
    local = wall.replace(tzinfo=tz)
    return local.astimezone(timezone.utc)


def period_bounds(
    cal: CalendarEntry, tz: str | ZoneInfo, local_day: date, period: str
) -> tuple[datetime, datetime] | None:
    """UTC bounds of the measure period on ``local_day``; None means NOT_EXPECTED."""
    zone = tz if isinstance(tz, ZoneInfo) else ZoneInfo(tz)
    if not cal.operates_on(local_day.weekday()):
        return None
    if period == PERIOD_OPERATING_HOURS:
        lo_min, hi_min = cal.hours[0][0], cal.hours[-1][1]
    elif period == PERIOD_MIDDAY:
        lo_min, hi_min = MIDDAY_WINDOW_LOCAL
    else:
        raise ValueError(f"unknown period {period!r}")
    return _local_minute_to_utc(local_day, lo_min, zone), _local_minute_to_utc(local_day, hi_min, zone)


def covered_seconds(
    intervals: Iterable[tuple[datetime, datetime]], lo: datetime, hi: datetime
) -> int:
    """Seconds of the union of ``intervals`` inside ``[lo, hi)``, no double counting."""
    clipped = sorted(
        (max(a, lo), min(b, hi)) for a, b in intervals if min(b, hi) > max(a, lo)
    )
    total = 0.0
    cur_lo: datetime | None = None
    cur_hi: datetime | None = None
    for a, b in clipped:
        if cur_hi is None or a > cur_hi:
            if cur_hi is not None:
                total += (cur_hi - cur_lo).total_seconds()
            cur_lo, cur_hi = a, b
        elif b > cur_hi:
            cur_hi = b
    if cur_hi is not None:
        total += (cur_hi - cur_lo).total_seconds()
    return int(total)


def classify_day(
    expected: bool,
    required: int,
    covered: int,
    pending: bool,
    bands: Bands,
    threshold: float | None,
) -> str:
    if not expected:
        return NOT_EXPECTED
    if pending:
        return PENDING
    if required <= 0 or covered <= 0:
        return NO_DATA
    pct = Fraction(covered, required)
    complete = Fraction(str(threshold if threshold is not None else bands.complete))
    if pct >= complete:
        return COMPLETE
    if pct >= Fraction(str(bands.partial)):
        return PARTIAL
    return LOW


def coverage_pct(required: int, covered: int) -> str:
    """round(100 x covered/required, 2), capped at 100, as a decimal string."""
    if required <= 0:
        return "0.00"
    pct = (Decimal(100 * covered) / Decimal(required)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return str(min(pct, Decimal("100.00")))


def input_fp(
    ids: Sequence[str],
    pending: bool,
    policy_version: str,
    calendar_version: str,
    catalogue_version: int,
    adapter_key: str,
) -> str:
    payload = json.dumps(
        {
            "ids": sorted(str(i) for i in ids),
            "pending": bool(pending),
            "policy_version": policy_version,
            "calendar_version": calendar_version,
            "catalogue_version": catalogue_version,
            "adapter_key": adapter_key,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
