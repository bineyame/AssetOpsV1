"""Declared coverage policy and operating calendar for day snapshots (CH-1a).

Both files live under ``config/chain/`` and are reviewed as code (DECLARED
evidence class). This module holds the records and the schema validation; the
file read lives in ``chain/adapters/file_chain_config.py`` (no storage
technology above the adapter layer) and is composed in ``chain/composition.py``,
which loads the shipped files once per process. An invalid file raises
:class:`ChainConfigError` at load.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DAY_NAMES = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
CALENDAR_KINDS = ("OPERATING",)  # CH-1a section 5c: no LAB_SESSION kind

# Period names a MeasureSpec may use. CH-9 (CH9-R2 Q2): the fixed midday window is gone; daylight is measured
# per day inside the declared operating hours (`mini_depth.store.daylight_hours`).
PERIOD_OPERATING_HOURS = "operating_hours"
PERIODS = (PERIOD_OPERATING_HOURS,)


#: PB-3: the coverage basis a measure may declare (`measures.<key>.covered` in the coverage policy).
#: `intervals` (the default for every measure not listed): covered time is the union of the adapter's intervals.
#: `connector_status_known`: a metered-when-charging measure; covered time is connector-status-known time
#: (`grading.status_known_spans`).
BASIS_INTERVALS = "intervals"
BASIS_CONNECTOR_STATUS_KNOWN = "connector_status_known"
BASES = (BASIS_INTERVALS, BASIS_CONNECTOR_STATUS_KNOWN)


class ChainConfigError(ValueError):
    """A declared chain config file does not match its schema."""


@dataclass(frozen=True)
class Bands:
    complete: float
    partial: float


@dataclass(frozen=True)
class CoveragePolicy:
    policy_version: str
    bands: Bands
    objective_min_complete_days: int
    share_of_expected_days: float | None
    #: PB-3: (measure key, basis) pairs declared under `measures`; a measure not listed is `intervals`.
    coverage_bases: tuple[tuple[str, str], ...] = ()

    def basis_for(self, measure: str) -> str:
        return dict(self.coverage_bases).get(measure, BASIS_INTERVALS)


@dataclass(frozen=True)
class CalendarEntry:
    kind: str
    label: str
    days: frozenset[str]  # subset of DAY_NAMES
    hours: tuple[tuple[int, int], ...]  # (from_minute, to_minute), to <= 1440
    reason: str
    source: str | None

    def operates_on(self, weekday: int) -> bool:
        return DAY_NAMES[weekday] in self.days


@dataclass(frozen=True)
class OperatingCalendar:
    calendar_version: str
    sites: dict[str, CalendarEntry]
    default: CalendarEntry

    def entry_for(self, site_code: str) -> CalendarEntry:
        return self.sites.get(site_code, self.default)


def _require(cond: bool, path: str, message: str) -> None:
    if not cond:
        raise ChainConfigError(f"{path}: {message}")


def _fraction(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1


def parse_coverage_policy(payload: dict[str, Any], path: str) -> CoveragePolicy:
    _require(payload.get("schema") == "coverage-policy", path, "schema must be 'coverage-policy'")
    _require(payload.get("version") == 1, path, "version must be 1")
    policy_version = payload.get("policy_version")
    _require(isinstance(policy_version, str) and bool(policy_version), path, "policy_version required")
    bands = payload.get("bands")
    _require(isinstance(bands, dict), path, "bands must be an object")
    complete, partial = bands.get("complete"), bands.get("partial")
    _require(_fraction(complete) and _fraction(partial), path, "bands must be fractions in [0, 1]")
    _require(0 < partial < complete, path, "bands must satisfy 0 < partial < complete")
    min_days = payload.get("objective_min_complete_days")
    _require(
        isinstance(min_days, int) and not isinstance(min_days, bool) and min_days >= 1,
        path,
        "objective_min_complete_days must be an integer >= 1",
    )
    share = payload.get("share_of_expected_days")
    _require(share is None or _fraction(share), path, "share_of_expected_days must be null or a fraction")
    measures = payload.get("measures", {})
    _require(isinstance(measures, dict), path, "measures must be an object")
    bases: list[tuple[str, str]] = []
    for key, entry in sorted(measures.items()):
        _require(isinstance(entry, dict) and entry.get("covered") in BASES, path,
                 f"measures.{key}.covered must be one of {BASES}")
        bases.append((key, entry["covered"]))
    return CoveragePolicy(
        policy_version=policy_version,
        bands=Bands(complete=float(complete), partial=float(partial)),
        objective_min_complete_days=min_days,
        share_of_expected_days=None if share is None else float(share),
        coverage_bases=tuple(bases),
    )


def _minutes(text: Any, path: str, *, allow_24: bool) -> int:
    _require(isinstance(text, str) and len(text) == 5 and text[2] == ":", path, f"bad time {text!r}")
    hh, mm = text[:2], text[3:]
    _require(hh.isdigit() and mm.isdigit(), path, f"bad time {text!r}")
    h, m = int(hh), int(mm)
    if allow_24 and h == 24 and m == 0:
        return 1440
    _require(0 <= h <= 23 and 0 <= m <= 59, path, f"bad time {text!r}")
    return h * 60 + m


def _parse_entry(raw: Any, path: str, where: str, *, require_reason: bool) -> CalendarEntry:
    _require(isinstance(raw, dict), path, f"{where}: entry must be an object")
    kind = raw.get("kind")
    _require(kind in CALENDAR_KINDS, path, f"{where}: kind must be one of {CALENDAR_KINDS}")
    label = raw.get("label")
    _require(isinstance(label, str) and bool(label), path, f"{where}: label required")
    reason = raw.get("reason")
    if require_reason:
        _require(isinstance(reason, str) and bool(reason), path, f"{where}: reason required")
    source = raw.get("source")
    # source is optional; when an entry cites one it must be a non-empty string.
    _require(source is None or (isinstance(source, str) and bool(source)), path, f"{where}: source must be text")
    days_raw = raw.get("days")
    if days_raw == "ALL":
        days = frozenset(DAY_NAMES)
    else:
        _require(isinstance(days_raw, list) and bool(days_raw), path, f"{where}: days must be 'ALL' or a list")
        for name in days_raw:
            _require(name in DAY_NAMES, path, f"{where}: unknown day name {name!r}")
        days = frozenset(days_raw)
    hours_raw = raw.get("hours")
    _require(isinstance(hours_raw, list) and bool(hours_raw), path, f"{where}: hours must be a non-empty list")
    hours: list[tuple[int, int]] = []
    for item in hours_raw:
        _require(isinstance(item, dict), path, f"{where}: hours item must be an object")
        lo = _minutes(item.get("from"), path, allow_24=False)
        hi = _minutes(item.get("to"), path, allow_24=True)
        _require(lo < hi, path, f"{where}: hours need from < to (or to == '24:00')")
        hours.append((lo, hi))
    hours.sort()
    for (a_lo, a_hi), (b_lo, _b_hi) in zip(hours, hours[1:]):
        # v1 calendar: one contiguous window per day (period_bounds returns one span).
        _require(a_hi == b_lo, path, f"{where}: hours must form one contiguous window")
    return CalendarEntry(
        kind=kind,
        label=label,
        days=days,
        hours=tuple(hours),
        reason=reason if isinstance(reason, str) else "",
        source=source if isinstance(source, str) else None,
    )


def parse_operating_calendar(payload: dict[str, Any], path: str) -> OperatingCalendar:
    _require(payload.get("schema") == "operating-calendar", path, "schema must be 'operating-calendar'")
    _require(payload.get("version") == 1, path, "version must be 1")
    calendar_version = payload.get("calendar_version")
    _require(isinstance(calendar_version, str) and bool(calendar_version), path, "calendar_version required")
    sites_raw = payload.get("sites")
    _require(isinstance(sites_raw, dict), path, "sites must be an object")
    sites = {
        code: _parse_entry(raw, path, f"sites.{code}", require_reason=True)
        for code, raw in sites_raw.items()
    }
    default = _parse_entry(payload.get("default"), path, "default", require_reason=False)
    return OperatingCalendar(calendar_version=calendar_version, sites=sites, default=default)
