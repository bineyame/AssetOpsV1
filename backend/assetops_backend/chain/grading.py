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
    BASIS_CONNECTOR_STATUS_KNOWN,
    BASIS_INTERVALS,
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


#: PB-3: the coverage bases (`policy.BASES`) a measure may declare in the coverage policy. ev-charger/1 connector states that carry no energy: a connector reported in one is known at zero energy.
#: CHARGING carries energy, so it is known only where a meter interval covers it; any other value is unknown.
ZERO_ENERGY_STATES = frozenset({"UNPLUGGED", "PLUGGED", "AUTHORIZING", "FAULTED"})


def _union(spans: Iterable[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    out: list[list[datetime]] = []
    for a, b in sorted(s for s in spans if s[1] > s[0]):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def _intersect(xs: list[tuple[datetime, datetime]], ys: list[tuple[datetime, datetime]]):
    out, i, j = [], 0, 0
    while i < len(xs) and j < len(ys):
        a, b = max(xs[i][0], ys[j][0]), min(xs[i][1], ys[j][1])
        if b > a:
            out.append((a, b))
        if xs[i][1] < ys[j][1]:
            i += 1
        else:
            j += 1
    return out


def status_known_spans(connectors) -> list[tuple[datetime, datetime]]:
    """PB-3: the Site's energy-known spans for a metered-when-charging measure. Per connector (`{asset: {"states":
    [(from, to, state)], "meter": [(from, to)]}}`): the spans of a zero-energy reported state, plus its meter
    intervals. The Site is known only where every connector is; no connector, no known time."""
    out: list[tuple[datetime, datetime]] | None = None
    for item in connectors.values():
        known = _union([(a, b) for a, b, state in item.get("states") or () if state in ZERO_ENERGY_STATES]
                       + [(a, b) for a, b in item.get("meter") or ()])
        out = known if out is None else _intersect(out, known)
    return out or []


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
    coverage_basis: str = BASIS_INTERVALS,
) -> str:
    body = {
        "ids": sorted(str(i) for i in ids),
        "pending": bool(pending),
        "policy_version": policy_version,
        "calendar_version": calendar_version,
        "catalogue_version": catalogue_version,
        "adapter_key": adapter_key,
    }
    if coverage_basis != BASIS_INTERVALS:  # PB-3: a declared basis moves the fingerprint; the default stays byte-equal
        body["coverage_basis"] = coverage_basis
    payload = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
