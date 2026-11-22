"""0K3: the replay series read from stored readings (spec `specs/0K3-replay-series-reader/spec.md` §2).

A producer for 0K2's seam. `SeriesReader.read` turns a Site's accepted readings over whole local days into the
`ObservedSeries` that `replay_study` takes, or refuses with a code and a subject. It reads only what is stored and
accepted, places each reading on the 5-minute grid by its own interval or instant, and fills nothing:

- a kW role needs interval means inside one step; means that tile a step exactly give its exact time-weighted value;
  a coarser mean (15 minutes) or one crossing a step or the window edge is refused, never split (D-0K3.2);
- charge, fuel and generator state are read only at a step start; an instant off the grid is counted, not read, and
  no state or level is carried forward (D-0K3.3);
- the PV series is `pv_available_power` only: inverter output (`pv_power`) is never read as availability (D-0K3.4);
- loads are delivered feeder power (`feeder_demand`) by asset code (D-0K3.5);
- the input class comes from the readings' own source mode (D-0K3.6).

Configuration is checked before readings (D-0K3.7). No clock read, no adapter import; nothing is served (D-0K3.9).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from fractions import Fraction
import re
from types import MappingProxyType
from typing import Mapping, Protocol, Sequence
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from assetops_backend.analytics.dispatch_v3 import OFF_STATES, ON_STATES
from assetops_backend.analytics.assessment_inputs import (
    AcceptedReading,
    CohortMember,
    EvidenceQuery,
    EvidenceQueryResult,
    RoleBinding,
    Window,
    build_input_set,
    iso,
)
from assetops_backend.analytics.assessment_worker import ROLES_BY_SET
from assetops_backend.analytics.cohort import select_cohort
from assetops_backend.runs.replay_study import ObservedSeries
from assetops_backend.sites import unit_roles
from assetops_contracts.forward_replay import LoadSeries

STEP = timedelta(minutes=5)
PV, LOAD, GEN_POWER = "pv_available_power", "feeder_demand", "generator_power"
SOC, FUEL, GEN_STATE = "battery_soc", "fuel_level", "generator_state"
REPLAY_ROLES = (PV, LOAD, GEN_POWER, GEN_STATE, SOC, FUEL)  # the query's roles, and the refusal order
MEAN_ROLES = frozenset({PV, LOAD, GEN_POWER})  # an interval mean, kW
INSTANT_ROLES = frozenset({SOC, FUEL, GEN_STATE})  # a reading at a step's start
ONE_ASSET_ROLES = (PV, GEN_POWER, GEN_STATE, SOC, FUEL)  # exactly one bound asset each; LOAD: one or more
#: D-DD.110 Q10: these may bind several units when every binding is PER_ASSET in its set (roles-5); the Site series
#: is then built through `unit_roles`. Under a ONE set a second asset is still a binding change.
UNIT_ROLES = (PV, GEN_POWER, GEN_STATE)
UNITS = MappingProxyType({PV: "kW", LOAD: "kW", GEN_POWER: "kW", SOC: "%", FUEL: "L", GEN_STATE: "state"})
STATES = ON_STATES | OFF_STATES  # RUNNING, STOPPED, STARTING, FAILED
INPUT_CLASS_BY_MODE = MappingProxyType({"LIVE": "RECORDED", "SIMULATED": "SIMULATED"})
DECIMAL = re.compile(r"-?[0-9]{1,15}(\.[0-9]{1,9})?")
MAX_DAYS = 92  # D-0K3.14
INSTANT = "%Y-%m-%dT%H:%M:%SZ"  # the study's instant form (D-0K3.10)
SERIES_ANALYTIC_ID, SERIES_VERSION = "replay-series", "replay-series-1"  # the input set's identity
QUERY_DOMAIN = "replay-series"  # a label: query_evidence does not filter on it
READER_REFUSALS = frozenset({
    "READER_WINDOW_INVALID", "READER_SITE_UNKNOWN", "READER_ROLE_UNBOUND", "READER_BINDING_CHANGED",
    "READER_ASSET_UNKNOWN", "READER_COHORT", "READER_RESOLUTION", "READER_READINGS_CONFLICT", "READER_UNIT",
    "READER_VALUE", "READER_STATE_UNKNOWN", "READER_INPUT_CLASS", "READER_START_FUEL_UNKNOWN"})
# One read holds about MAX_DAYS x 288 x (5 + loads) readings plus the bracket (D-0K3.14); no separate count cap.
_TICK = timedelta(microseconds=1)  # the exact unit of a tiling weight


class SeriesRefused(Exception):
    """Nothing was returned: the request, the Site's configuration or a reading was judged and refused.
    `detail` is a developer diagnostic, never served (D-0K3.9)."""

    def __init__(self, code: str, subject: str, detail: str) -> None:
        if code not in READER_REFUSALS:
            raise ValueError(f"{code!r} is not a reader refusal")
        super().__init__(f"{code} ({subject}): {detail}")
        self.code = code
        self.subject = subject
        self.detail = detail


@dataclass(frozen=True)
class SeriesRequest:
    tenant_id: UUID
    site_id: UUID
    first_local_date: date  # the first local day, in the Site's zone
    days: int  # whole local days, 1 to MAX_DAYS
    knowledge_at: datetime  # aware; readings accepted at or before it (6c: its lease instant)
    cohort: tuple[CohortMember, ...] | None = None  # None: the default selection


@dataclass(frozen=True)
class PlacedSeries:
    series: ObservedSeries
    readings_used: int  # readings placed on a step the series reads (GOOD or not)
    off_grid: tuple[tuple[str, int], ...]  # (role, count) of instants not on a step start: not read (D-0K3.3)


@dataclass(frozen=True)
class SeriesRead:
    series: ObservedSeries
    timezone: str  # the Site's zone; the caller's StudyFrame uses it
    window: Window  # UTC [local midnight of the first day, local midnight after the last)
    input_sha256: str  # build_input_set's identity of the readings and configuration read
    cohort: tuple[CohortMember, ...]  # the selected members
    readings_used: int
    off_grid: tuple[tuple[str, int], ...]
    load_role: str = LOAD  # what the load series is (D-0K3.5)


class EvidenceSource(Protocol):
    def query_evidence(self, query: EvidenceQuery) -> EvidenceQueryResult: ...


class SiteRecords(Protocol):
    def find_site_by_id(self, tenant_id: UUID, site_id: UUID): ...  # .timezone

    def registrations(self, tenant_id: UUID, site_id: UUID): ...  # .assets: .id, .asset_code


# --- the window --------------------------------------------------------------------------------------------------


def local_window(first_local_date: date, days: int, zone: str) -> Window:
    """UTC `[local midnight of the first day, local midnight after the last)`; every local day must last 24 hours
    (D-0K3.18: the study's 288-step day), else `READER_WINDOW_INVALID` `day:<date>`."""
    try:
        tz = ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError, TypeError, OSError) as unknown:
        raise SeriesRefused("READER_WINDOW_INVALID", "timezone", f"{zone!r} is not an IANA zone") from unknown

    def midnight(day: date) -> datetime:
        return datetime.combine(day, time(0), tz).astimezone(ZoneInfo("UTC"))

    for d in range(days):
        day = first_local_date + timedelta(days=d)
        if midnight(day + timedelta(days=1)) - midnight(day) != timedelta(hours=24):
            raise SeriesRefused("READER_WINDOW_INVALID", f"day:{day.isoformat()}",
                                "a local day that is not 24 hours (a clock change) is not 288 steps")
    return Window(midnight(first_local_date), midnight(first_local_date + timedelta(days=days)))


# --- the configuration -------------------------------------------------------------------------------------------


def bound_assets(bindings: Sequence[RoleBinding], asset_codes: Mapping[UUID, str],
                 window: Window) -> Mapping[str, tuple[UUID, ...]]:
    """§2.2 step 4: per replay role, the assets bound over any part of the window. Loads by ascending code."""
    out: dict[str, tuple[UUID, ...]] = {}
    for role in REPLAY_ROLES:
        assets = {b.asset_id for b in bindings if b.role == role and b.valid_from < window.end
                  and (b.valid_to is None or b.valid_to > window.start)}
        if not assets:
            raise SeriesRefused("READER_ROLE_UNBOUND", role, f"no binding of {role} over the window")
        units = len(assets) > 1 and role in UNIT_ROLES and all(
            unit_roles.per_asset(b.role_set, role) for b in bindings if b.role == role and b.valid_from < window.end
            and (b.valid_to is None or b.valid_to > window.start))
        if units:
            out[role] = tuple(sorted(assets, key=str))
            continue
        if role in ONE_ASSET_ROLES:
            if len(assets) > 1:
                raise SeriesRefused("READER_BINDING_CHANGED", role,
                                    f"{len(assets)} assets bound to {role} over the window; one is read")
            out[role] = tuple(assets)
            continue
        for asset in sorted(assets, key=str):
            if asset is None or asset not in asset_codes:
                raise SeriesRefused("READER_ASSET_UNKNOWN", f"{LOAD}:{asset}",
                                    "a load asset with no registered asset code")
        out[role] = tuple(sorted(assets, key=lambda a: asset_codes[a]))
    return MappingProxyType(out)


# --- placing readings on the grid (§2.3) -------------------------------------------------------------------------


def _subject(role: str, code: str, reading: AcceptedReading) -> str:
    at = iso(reading.interval_start or reading.source_time)
    return f"{LOAD}:{code}@{at}" if role == LOAD else f"{role}@{at}"


def _value(role: str, reading: AcceptedReading, subject: str):
    if reading.unit != UNITS[role]:
        raise SeriesRefused("READER_UNIT", subject, f"unit {reading.unit!r}, not {UNITS[role]!r}")
    if role == GEN_STATE:
        if reading.value not in STATES:
            raise SeriesRefused("READER_STATE_UNKNOWN", subject, f"state {reading.value!r} is not one of "
                                f"{sorted(STATES)}")
        return reading.value
    if reading.value is None or not DECIMAL.fullmatch(reading.value):
        raise SeriesRefused("READER_VALUE", subject, f"value {reading.value!r} is not an exact decimal")
    return Fraction(reading.value)


def series_from_readings(readings: Sequence[AcceptedReading], bound: Mapping[str, tuple[UUID, ...]],
                         asset_codes: Mapping[UUID, str], window: Window) -> PlacedSeries:
    """§2.3: each reading placed by its own interval or instant; the first refusal raises; nothing is filled."""
    span = window.end - window.start
    if span % STEP:
        raise SeriesRefused("READER_WINDOW_INVALID", "steps", f"the window is not a whole number of {STEP} steps")
    n = span // STEP
    start, end = window.start, window.end

    def key(r: AcceptedReading):
        return (REPLAY_ROLES.index(r.role), asset_codes.get(r.asset_id, ""), r.placed_at, str(r.evidence_id))

    chosen = sorted((r for r in readings if r.role in REPLAY_ROLES and r.asset_id in bound.get(r.role, ())), key=key)
    means: dict[tuple[str, UUID | None], dict[int, list[tuple[datetime, datetime, object]]]] = {}
    instants: dict[tuple[str, UUID | None], dict[int, object]] = {}
    used: list[tuple[AcceptedReading, bool]] = []  # (reading, sets a value: GOOD)
    off_grid: dict[str, int] = {}
    for r in chosen:
        role, code = r.role, asset_codes.get(r.asset_id, "")
        subject = _subject(role, code, r)
        lo = r.interval_start if r.interval_start is not None else r.source_time
        hi = r.interval_end if r.interval_end is not None else r.source_time
        # 1. the window edge: the bracket is skipped; a mean across an edge is refused
        if r.interval_start is None or r.interval_end is None:
            if r.source_time < start or r.source_time >= end:
                continue
        else:
            if hi <= start or lo >= end:
                continue
            if lo < start < hi or lo < end < hi:
                raise SeriesRefused("READER_RESOLUTION", subject, "crosses the window edge")
        # 2. the shape
        has_interval = r.interval_start is not None or r.interval_end is not None
        if role in MEAN_ROLES and not has_interval:
            raise SeriesRefused("READER_RESOLUTION", subject, "an instant where an interval mean is needed")
        if role in INSTANT_ROLES and has_interval:
            raise SeriesRefused("READER_RESOLUTION", subject, "an interval where an instant is needed")
        # 3. unit and value, GOOD only
        good = r.quality == "GOOD"
        value = _value(role, r, subject) if good else None
        channel = (role, r.asset_id)
        if role in MEAN_ROLES:
            # 4. a mean inside one step
            k = (lo - start) // STEP
            step_end = start + (k + 1) * STEP
            if not hi > lo:
                raise SeriesRefused("READER_RESOLUTION", subject, "an empty or reversed interval")
            if hi > step_end:
                raise SeriesRefused("READER_RESOLUTION", subject, "coarser than the 5-minute step")
            parts = means.setdefault(channel, {}).setdefault(k, [])
            if any(p_lo < hi and lo < p_hi for p_lo, p_hi, _ in parts):
                raise SeriesRefused("READER_READINGS_CONFLICT", subject, "overlapping means in one step")
            parts.append((lo, hi, value))
            used.append((r, good))
            continue
        # 5. an instant on a step start, else off the grid
        offset = r.source_time - start
        if offset % STEP:
            off_grid[role] = off_grid.get(role, 0) + 1
            continue
        k = offset // STEP
        slots = instants.setdefault(channel, {})
        if k in slots:
            raise SeriesRefused("READER_READINGS_CONFLICT", subject, "two readings at one step start")
        slots[k] = value
        if role == FUEL and k != 0:
            continue  # the fuel at any other step is not read
        used.append((r, good))

    def mean_series(role: str, asset: UUID | None) -> tuple[Fraction | None, ...]:
        steps = means.get((role, asset), {})
        out: list[Fraction | None] = []
        for k in range(n):
            parts = sorted(steps.get(k, ()), key=lambda p: p[0])
            t_k, t_next = start + k * STEP, start + (k + 1) * STEP
            tiled = (bool(parts) and parts[0][0] == t_k and parts[-1][1] == t_next
                     and all(a[1] == b[0] for a, b in zip(parts, parts[1:]))
                     and all(v is not None for _, _, v in parts))
            out.append(sum((v * Fraction((b - a) // _TICK, STEP // _TICK) for a, b, v in parts), Fraction(0))
                       if tiled else None)
        return tuple(out)

    def instant_series(role: str, asset: UUID | None) -> tuple:
        slots = instants.get((role, asset), {})
        return tuple(slots.get(k) for k in range(n))

    # 6. the series
    def site_mean(role: str) -> tuple:
        """The Site series of a unit role: one asset is its own series; several, `unit_roles.site_power` a step."""
        if len(bound[role]) == 1:
            return mean_series(role, bound[role][0])
        by_unit = {str(a): mean_series(role, a) for a in bound[role]}
        return tuple(unit_roles.site_power({u: s[k] for u, s in by_unit.items()}).value for k in range(n))

    def site_state() -> tuple:
        if len(bound[GEN_STATE]) == 1:
            return instant_series(GEN_STATE, bound[GEN_STATE][0])
        by_unit = {str(a): instant_series(GEN_STATE, a) for a in bound[GEN_STATE]}
        return tuple(unit_roles.site_generator_state({u: s[k] for u, s in by_unit.items()}).value for k in range(n))

    [soc_asset], [fuel_asset] = bound[SOC], bound[FUEL]
    gen_kw = site_mean(GEN_POWER)
    start_fuel = instants.get((FUEL, fuel_asset), {}).get(0)
    if start_fuel is None:
        raise SeriesRefused("READER_START_FUEL_UNKNOWN", FUEL, "no GOOD fuel reading at the window start")
    # 7. the input class, from the readings that set a value
    modes = sorted({r.source_mode for r, good in used if good})
    unknown = [m for m in modes if m not in INPUT_CLASS_BY_MODE]
    if unknown:
        raise SeriesRefused("READER_INPUT_CLASS", unknown[0], f"source mode {unknown[0]!r} has no input class")
    classes = {INPUT_CLASS_BY_MODE[m] for m in modes}
    if len(classes) != 1:
        raise SeriesRefused("READER_INPUT_CLASS", "mixed", f"readings of more than one class: {sorted(classes)}")
    series = ObservedSeries(
        interval_start=start.strftime(INSTANT),
        timestep_minutes=5,
        pv_available_kw=site_mean(PV),
        loads=tuple(LoadSeries(asset_codes[a], mean_series(LOAD, a)) for a in bound[LOAD]),
        generator_kwh=tuple(None if kw is None else kw * Fraction(5, 60) for kw in gen_kw),
        generator_state=site_state(),
        soc_pct=instant_series(SOC, soc_asset),
        start_fuel_l=start_fuel,
        input_class=classes.pop(),
    )
    return PlacedSeries(series, len(used),
                        tuple((role, off_grid[role]) for role in REPLAY_ROLES if role in off_grid))


# --- the reader (§2.2) -------------------------------------------------------------------------------------------


class SeriesReader:
    def __init__(self, evidence: EvidenceSource, sites: SiteRecords) -> None:
        self._evidence = evidence
        self._sites = sites

    def read(self, request: SeriesRequest) -> SeriesRead:
        """§2.2, in order; the first failure raises, and nothing is queried before the Site and its window."""
        # 1. the request
        if type(request.days) is not int or not 1 <= request.days <= MAX_DAYS:
            raise SeriesRefused("READER_WINDOW_INVALID", "days", f"days must be an int from 1 to {MAX_DAYS}")
        if not isinstance(request.first_local_date, date) or isinstance(request.first_local_date, datetime):
            raise SeriesRefused("READER_WINDOW_INVALID", "first_local_date", "a local date, not a datetime")
        known = request.knowledge_at
        if not isinstance(known, datetime) or known.tzinfo is None or known.utcoffset() is None:
            raise SeriesRefused("READER_WINDOW_INVALID", "knowledge_at", "the knowledge cutoff must be aware")
        # 2. the Site and its window
        site = self._sites.find_site_by_id(request.tenant_id, request.site_id)
        if site is None:
            raise SeriesRefused("READER_SITE_UNKNOWN", str(request.site_id), "no such Site for the tenant")
        zone = site.timezone
        window = local_window(request.first_local_date, request.days, zone)
        asset_codes = {a.id: a.asset_code for a in self._sites.registrations(request.tenant_id, request.site_id).assets}
        # 3. the one query
        result = self._evidence.query_evidence(EvidenceQuery(
            request.tenant_id, request.site_id, QUERY_DOMAIN, window, known, cohort=request.cohort,
            roles=REPLAY_ROLES))
        # 4. bindings before the cohort
        bound = bound_assets(result.bindings, asset_codes, window)
        # 5. the cohort
        selection = select_cohort(result.readings, window, request.cohort, result.attestations)
        if not selection.usable:
            raise SeriesRefused("READER_COHORT", selection.status, selection.reason or "the cohort is not usable")
        inputs = build_input_set(result, selection, analytic_id=SERIES_ANALYTIC_ID, model_version=SERIES_VERSION,
                                 roles_by_set=ROLES_BY_SET)
        # 6. the series
        placed = series_from_readings(inputs.readings, bound, asset_codes, window)
        return SeriesRead(placed.series, zone, window, inputs.input_sha256, selection.members, placed.readings_used,
                          placed.off_grid)


__all__ = [
    "INPUT_CLASS_BY_MODE", "INSTANT", "INSTANT_ROLES", "MAX_DAYS", "MEAN_ROLES", "ONE_ASSET_ROLES", "READER_REFUSALS",
    "REPLAY_ROLES", "STATES", "STEP", "UNITS", "UNIT_ROLES", "PlacedSeries", "SeriesRead", "SeriesReader",
    "SeriesRefused", "SeriesRequest", "bound_assets", "local_window", "series_from_readings",
]
