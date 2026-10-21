"""W4-02 units 2-3: pure renewable, service, fuel and backup rules for one Site-local clock hour.

`D-2026-10-20-w4-02-buildspec` (base "New model and computation"; closure 1 Q4, Q8, Q9, Q17; closure 2
"Derivations, status and copy"). Nothing here reads a database, a clock or a Foundation store: the caller (unit 4's
`inputs.py`) supplies the cutoff-filtered accepted readings of one hour and the pinned Foundation values, and these
functions return the typed hour result that `projection.py` turns into the wire.

Shared reading rules (base "New model and computation"):

- Only a GOOD interval mean in kW with a numeric value covers time. An instant report (no interval) covers zero
  seconds; nothing is interpolated. Non-GOOD, instant and unusable rows are still cited, because citations are the
  full selected set, including limiting rows. An in-window unusable row of a required bound input is also
  `REQUIRED_INPUT_UNUSABLE` and withholds the positive claim even when GOOD rows cover the hour (q2 ruling 5).
- Two usable rows of one role and asset that overlap in time are a conflict (a duplicate included); the rule never
  picks the favourable row.
- A role with no usable row is MISSING; a role whose usable rows leave part of the hour uncovered is PARTIAL.
- Amounts are `None` when not established, never a zero substitute.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable, Sequence
from uuid import UUID

from assetops_backend.sites.binding_roles import MINI_BUS_STATES, MINI_SUPPLY_STATES

GOOD = "GOOD"
KW = "kW"
_ZERO = Decimal(0)
_HOUR_SECONDS = Decimal(3600)

# Series states.
COMPLETE, PARTIAL, MISSING, CONFLICTING = "COMPLETE", "PARTIAL", "MISSING", "CONFLICT"

#: Renewable constraint codes in their stable display order (closure 1 Q8 + closure 2), with their exact copy.
RENEWABLE_CONSTRAINTS: tuple[tuple[str, str], ...] = (
    ("CAPABILITY_MISSING", "Available solar power unknown"),
    ("PV_USE_MISSING", "Observed use unknown"),
    ("MARGIN_MISSING", "Retained margin unknown"),
    ("CHARGE_OBLIGATION_MISSING", "Storage obligation unknown"),
    ("CRITICAL_SERVICE_MISSING", "Critical service not established"),
    ("COVERAGE_GAP", "Incomplete hour"),
    ("REQUIRED_INPUT_UNUSABLE", "Required reading could not be used"),
    ("CONFLICT", "Conflicting evidence"),
    ("HEADROOM_NON_POSITIVE", "No positive headroom after retained margin"),
    ("CHARGE_OBLIGATION_ACTIVE", "Storage charging uses the available headroom"),
    ("CRITICAL_SERVICE_DEFICIT", "Critical service has an unresolved deficit"),
)
_CONSTRAINT_ORDER = {code: i for i, (code, _) in enumerate(RENEWABLE_CONSTRAINTS)}
_LIMITING = frozenset({
    "CAPABILITY_MISSING", "PV_USE_MISSING", "MARGIN_MISSING", "CHARGE_OBLIGATION_MISSING",
    "CRITICAL_SERVICE_MISSING", "COVERAGE_GAP", "REQUIRED_INPUT_UNUSABLE",
})
_CONTRAINDICATING = frozenset({"HEADROOM_NON_POSITIVE", "CHARGE_OBLIGATION_ACTIVE", "CRITICAL_SERVICE_DEFICIT"})

#: Limitation codes in their stable order (closure 1 Q8): the constraint codes, then the domain codes.
LIMITATION_ORDER: tuple[str, ...] = tuple(code for code, _ in RENEWABLE_CONSTRAINTS) + (
    "REQUEST_BASELINE_MISSING", "SITE_ROLE_UNSUPPORTED", "DELIVERY_COMPLETENESS_MISSING", "CLOSING_READING_MISSING",
    "RECOVERY_TARGET_MISSING", "BACKUP_CHAIN_INCOMPLETE", "SOURCE_CLASS_UNKNOWN", "SOURCE_CLASS_MIXED",
    "SOURCE_STALE", "RECOMPUTE_PENDING",
)

# Roles (sites/binding_roles.py MINIGRID_ROLES_4).
PV_AVAILABLE, PV_POWER, FEEDER_DEMAND = "pv_available_power", "pv_power", "feeder_demand"
CHARGE_REQUEST = "storage_charge_requested_power"
CRITICAL_REQUESTED, CRITICAL_DELIVERED = "critical_load_requested_power", "critical_load_delivered_power"
FEEDER_REQUESTED = "feeder_requested_power"


@dataclass(frozen=True)
class Reading:
    """One cutoff-visible accepted reading as the rules see it. `value` is `None` when not numeric."""

    evidence_id: UUID
    source_id: UUID
    role: str
    asset_id: UUID | None
    source_time: datetime
    interval_start: datetime | None
    interval_end: datetime | None
    quality: str
    value: Decimal | None
    unit: str | None


@dataclass(frozen=True)
class Window:
    """A UTC half-open `[start, end)` assessment window."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if not self.start < self.end:
            raise ValueError("window start must precede its end")

    @property
    def seconds(self) -> Decimal:
        return Decimal(str((self.end - self.start).total_seconds()))


@dataclass(frozen=True)
class Bound:
    low: Decimal
    high: Decimal


@dataclass(frozen=True)
class Gap:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class Coverage:
    required_seconds: int
    observed_seconds: int
    source_count: int
    gaps: tuple[Gap, ...]


@dataclass(frozen=True)
class Segment:
    start: datetime
    end: datetime
    value: Decimal

    @property
    def seconds(self) -> Decimal:
        return Decimal(str((self.end - self.start).total_seconds()))


@dataclass(frozen=True)
class Series:
    """One role (and asset) over one window."""

    role: str
    asset_id: UUID | None
    state: str
    segments: tuple[Segment, ...]
    coverage: Coverage
    cited: tuple[UUID, ...]
    covered: tuple[tuple[datetime, datetime], ...]
    #: In-window rows of this required input that are unusable (`_unusable`; q2 ruling 5, q4 ruling 1). A GOOD
    #: well-formed instant is cited and covers nothing, but is not unusable.
    unusable: tuple[UUID, ...] = ()
    #: Sources behind the usable (covering) rows.
    source_ids: tuple[UUID, ...] = ()

    @property
    def complete(self) -> bool:
        return self.state == COMPLETE

    def mean_kw(self) -> Decimal | None:
        """Time-weighted mean over the observed seconds; `None` with no usable row or a conflict."""
        if self.state in (MISSING, CONFLICTING):
            return None
        seconds = sum((s.seconds for s in self.segments), _ZERO)
        return sum((s.value * s.seconds for s in self.segments), _ZERO) / seconds


def _usable(r: Reading) -> bool:
    return (r.quality == GOOD and r.value is not None and r.unit == KW
            and r.interval_start is not None and r.interval_end is not None and r.interval_start < r.interval_end)


def _malformed_bounds(r: Reading) -> bool:
    """Purports to be an interval but is not one: only one bound, or `start >= end` (q4 ruling 1)."""
    if (r.interval_start is None) != (r.interval_end is None):
        return True
    return r.interval_start is not None and r.interval_end is not None and not r.interval_start < r.interval_end


def _unusable(r: Reading, unit: str = KW) -> bool:
    """q4 ruling 1, separate from `_usable`: non-GOOD, nonnumeric, wrong unit or malformed interval bounds. A GOOD
    numeric instant (`interval_start = interval_end = None`) in the right unit is valid, though it covers 0 s."""
    return r.quality != GOOD or r.value is None or r.unit != unit or _malformed_bounds(r)


def _in_window(r: Reading, w: Window) -> bool:
    """A well-formed interval by its bounds; an instant or a malformed interval by its source time."""
    if r.interval_start is not None and r.interval_end is not None and r.interval_start < r.interval_end:
        return r.interval_start < w.end and w.start < r.interval_end
    return w.start <= r.source_time < w.end


def _union(spans: Iterable[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    merged: list[tuple[datetime, datetime]] = []
    for lo, hi in sorted(spans):
        if merged and lo <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return merged


def _intersect(a: Sequence[tuple[datetime, datetime]],
               b: Sequence[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    out = []
    for alo, ahi in a:
        for blo, bhi in b:
            lo, hi = max(alo, blo), min(ahi, bhi)
            if lo < hi:
                out.append((lo, hi))
    return _union(out)


def _coverage(w: Window, covered: Sequence[tuple[datetime, datetime]], sources: set[UUID]) -> Coverage:
    gaps, cursor = [], w.start
    for lo, hi in covered:
        if cursor < lo:
            gaps.append(Gap(cursor, lo))
        cursor = max(cursor, hi)
    if cursor < w.end:
        gaps.append(Gap(cursor, w.end))
    observed = sum(((hi - lo) for lo, hi in covered), timedelta())
    return Coverage(int(w.seconds), int(observed.total_seconds()), len(sources), tuple(gaps))


def series(readings: Iterable[Reading], role: str, asset_id: UUID | None, w: Window,
           *, any_asset: bool = False) -> Series:
    """Clip one role's (and asset's) readings to `w` and classify it; `any_asset` ignores the asset (ONE roles)."""
    mine = [r for r in readings if r.role == role and (any_asset or r.asset_id == asset_id) and _in_window(r, w)]
    cited = tuple(sorted({r.evidence_id for r in mine}, key=str))
    segs = sorted(
        ((Segment(max(r.interval_start, w.start), min(r.interval_end, w.end), r.value), r.source_id)  # type: ignore[arg-type]
         for r in mine if _usable(r)),
        key=lambda p: (p[0].start, p[0].end, str(p[1])),
    )
    segments = tuple(s for s, _ in segs)
    covered = tuple(_union((s.start, s.end) for s in segments))
    coverage = _coverage(w, covered, {src for _, src in segs})
    overlap = any(b.start < a.end for a, b in zip(segments, segments[1:]))
    if not segments:
        state = MISSING
    elif overlap:
        state = CONFLICTING
    elif coverage.gaps:
        state = PARTIAL
    else:
        state = COMPLETE
    unusable = tuple(sorted({r.evidence_id for r in mine if _unusable(r)}, key=str))
    sources = tuple(sorted({src for _, src in segs}, key=str))
    return Series(role, asset_id, state, segments, coverage, cited, covered, unusable, sources)


def _aligned(a: Series, b: Series) -> bool:
    """Both complete over the same interval boundaries, so their means are comparable interval by interval."""
    return (a.complete and b.complete
            and [(s.start, s.end) for s in a.segments] == [(s.start, s.end) for s in b.segments])


def _combined(w: Window, parts: Sequence[Series], source_count: int) -> Coverage:
    """Seconds covered by every part at once; `source_count` counts the sources behind the usable rows."""
    covered: list[tuple[datetime, datetime]] = [(w.start, w.end)]
    for p in parts:
        covered = _intersect(covered, p.covered)
    whole = _coverage(w, covered, set())
    return Coverage(whole.required_seconds, whole.observed_seconds, source_count, whole.gaps)


def _cited(parts: Iterable[Series], extra: Iterable[Reading] = ()) -> tuple[UUID, ...]:
    ids = {i for p in parts for i in p.cited} | {r.evidence_id for r in extra}
    return tuple(sorted(ids, key=str))


def _sources(parts: Sequence[Series]) -> int:
    """Distinct sources of the usable rows that fed `parts`."""
    return len({src for p in parts for src in p.source_ids})


def _pinned(readings: Sequence[Reading], role: str, asset_id: UUID | None, w: Window) -> Series:
    """The pinned asset's series only (q4 ruling 2); with no unique pinned asset it is MISSING, never another
    asset's rows."""
    return series(readings if asset_id is not None else (), role, asset_id, w)


# --- Renewable -------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RenewableInputs:
    """Pinned Foundation values for one noon hour (closure 1 Q9). `None` means not authored or not in force."""

    pv_uncertainty_kw: Decimal | None
    retained_margin_kw: Decimal | None
    feeder_asset_ids: tuple[UUID, ...]
    #: The single LOAD asset named by the selected in-force `critical-load-priority` property and its binding;
    #: `None` when none or several (q4 ruling 2).
    critical_asset_id: UUID | None


@dataclass(frozen=True)
class RenewableHour:
    """One selected local day's designated noon hour: a renewable table row plus the terms behind its cards."""

    day: date
    window: Window
    capability_kw: Bound | None
    used_kw: Decimal | None
    headroom_kw: Bound | None
    opportunity_kwh: Bound | None
    constraints: tuple[str, ...]
    decision: str
    coverage: Coverage
    evidence_ids: tuple[UUID, ...]


def _decision(codes: set[str]) -> str:
    if "CONFLICT" in codes:
        return "CONFLICT"
    if codes & _LIMITING:
        return "LIMITED"
    if codes & _CONTRAINDICATING:
        return "EXCLUDED"
    return "ELIGIBLE"


def assess_renewable_hour(day: date, w: Window, readings: Sequence[Reading], inputs: RenewableInputs) -> RenewableHour:
    """Closure 1 Q4/Q9 and closure 2: physical headroom of one noon hour and its eligibility."""
    cap = series(readings, PV_AVAILABLE, None, w, any_asset=True)
    pv = series(readings, PV_POWER, None, w, any_asset=True)
    feeders = [series(readings, FEEDER_DEMAND, a, w) for a in sorted(set(inputs.feeder_asset_ids), key=str)]
    charge = series(readings, CHARGE_REQUEST, None, w, any_asset=True)
    crit_req = _pinned(readings, CRITICAL_REQUESTED, inputs.critical_asset_id, w)
    crit_del = _pinned(readings, CRITICAL_DELIVERED, inputs.critical_asset_id, w)
    required = [cap, pv, *feeders, charge, crit_req, crit_del]

    codes: set[str] = set()
    u_valid = inputs.pv_uncertainty_kw is not None and inputs.pv_uncertainty_kw >= _ZERO  # q2 ruling 2
    if cap.state == MISSING or not u_valid:
        codes.add("CAPABILITY_MISSING")
    if pv.state == MISSING or not feeders or any(f.state == MISSING for f in feeders):
        codes.add("PV_USE_MISSING")
    if inputs.retained_margin_kw is None:
        codes.add("MARGIN_MISSING")
    if charge.state == MISSING:
        codes.add("CHARGE_OBLIGATION_MISSING")
    if MISSING in (crit_req.state, crit_del.state):
        codes.add("CRITICAL_SERVICE_MISSING")
    if any(s.state == PARTIAL for s in required):
        codes.add("COVERAGE_GAP")
    if any(s.unusable for s in required):
        codes.add("REQUIRED_INPUT_UNUSABLE")
    if any(s.state == CONFLICTING for s in required):
        codes.add("CONFLICT")

    if charge.complete and any(s.value > _ZERO for s in charge.segments):
        codes.add("CHARGE_OBLIGATION_ACTIVE")
    if crit_req.complete and crit_del.complete:
        if not _aligned(crit_req, crit_del):
            codes.add("CRITICAL_SERVICE_MISSING")
        elif any(r.value > d.value for r, d in zip(crit_req.segments, crit_del.segments)):
            codes.add("CRITICAL_SERVICE_DEFICIT")

    capability = used = headroom = None
    if cap.complete and u_valid:
        reported, u = cap.mean_kw(), inputs.pv_uncertainty_kw
        assert reported is not None and u is not None
        capability = Bound(max(_ZERO, reported - u), reported + u)
    if feeders and pv.complete and all(f.complete for f in feeders):
        # used_kwh = sum(load_kw_i * hours_i); used_kw = used_kwh / 1 hour (closure 2).
        used = sum((s.value * s.seconds for f in feeders for s in f.segments), _ZERO) / w.seconds
    if capability is not None and used is not None and inputs.retained_margin_kw is not None:
        margin = inputs.retained_margin_kw
        headroom = Bound(max(_ZERO, capability.low - used - margin), max(_ZERO, capability.high - used - margin))
        # q2 ruling 8: "positive headroom" is the upper bound (raw_high <= 0); 0-1 kW stays eligible, low 0.
        if headroom.high <= _ZERO:
            codes.add("HEADROOM_NON_POSITIVE")

    decision = _decision(codes)
    coverage = _combined(w, required, _sources(required))
    in_hour = [r for r in readings if _in_window(r, w)]
    return RenewableHour(
        day=day, window=w, capability_kw=capability, used_kw=used, headroom_kw=headroom,
        opportunity_kwh=headroom if decision == "ELIGIBLE" else None,
        constraints=tuple(sorted(codes, key=_CONSTRAINT_ORDER.__getitem__)),
        decision=decision, coverage=coverage, evidence_ids=_cited(required, in_hour),
    )


@dataclass(frozen=True)
class RenewableCards:
    capability_kw: Bound | None
    used_kw: Bound | None
    headroom_kw: Bound | None
    eligible_days: int | None
    assessed_days: int | None
    recurrence_established: bool


def summarize_renewable(hours: Sequence[RenewableHour], *, requested_days: int) -> RenewableCards:
    """Closure 1 Q4/Q19, closure 2: cards over complete eligible days; the denominator is complete days only."""
    eligible = [h for h in hours if h.decision == "ELIGIBLE"]
    assessed = [h for h in hours if h.decision in ("ELIGIBLE", "EXCLUDED")]

    def span(values: list[Bound]) -> Bound | None:
        return Bound(min(v.low for v in values), max(v.high for v in values)) if values else None

    used = [h.used_kw for h in eligible if h.used_kw is not None]
    return RenewableCards(
        capability_kw=span([h.capability_kw for h in eligible if h.capability_kw is not None]),
        used_kw=Bound(min(used), max(used)) if used else None,
        headroom_kw=span([h.headroom_kw for h in eligible if h.headroom_kw is not None]),
        eligible_days=len(eligible) if assessed else None,
        assessed_days=len(assessed) if assessed else None,
        recurrence_established=requested_days == 5 and len(hours) == 5 and len(assessed) == 5,
    )


def renewable_rows(hours: Iterable[RenewableHour]) -> list[RenewableHour]:
    """Daily rows in wire order `(local_day ASC, window_start ASC)` (base "Wire, order and refusals")."""
    return sorted(hours, key=lambda h: (h.day, h.window.start))


# --- Service ---------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class LoadAsset:
    """One bound `feeder_demand` LOAD asset. `critical` only when pinned `critical-load-priority` names it.

    `feeder_request_bound` is whether the pinned binding set binds `feeder_requested_power` to this asset; the
    critical request may qualify the critical asset only when that binding is absent (q2 ruling 12).
    """

    asset_id: UUID
    asset_code: str
    load_label: str
    critical: bool
    feeder_request_bound: bool


@dataclass(frozen=True)
class ServiceRow:
    asset_id: UUID
    asset_code: str
    load_label: str
    role: str
    delivered_kw: Decimal | None
    requested_evidence_state: str
    assessment: str
    coverage: Coverage
    evidence_ids: tuple[UUID, ...]
    interruptions: int | None
    unserved_kwh: Decimal | None


@dataclass(frozen=True)
class Limitation:
    code: str
    evidence_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class ServiceHour:
    window: Window
    status: str
    delivered_load_kw: Decimal | None
    interruptions_seen: int | None
    critical_delivered_kw: Decimal | None
    unserved_kwh: Decimal | None
    rows: tuple[ServiceRow, ...]
    limitations: tuple[Limitation, ...]
    coverage: Coverage
    evidence_ids: tuple[UUID, ...]
    #: Final review ruling 2 (M2): the pinned `critical_load_delivered_power` series' own coverage, from the same
    #: selected series as `critical_delivered_kw`; None when no single critical asset is pinned. Never feeder coverage.
    critical_delivered_coverage: Coverage | None = None


def _interruptions(req: Series, dlv: Series) -> int:
    """Maximal contiguous aligned intervals with requested > 0 and delivered = 0 (closure 1 Q17)."""
    runs, previous_end = 0, None
    for r, d in zip(req.segments, dlv.segments):
        if r.value > _ZERO and d.value == _ZERO:
            if previous_end != r.start:
                runs += 1
            previous_end = r.end
        else:
            previous_end = None
    return runs


@dataclass(frozen=True)
class _Built:
    row: ServiceRow
    delivered: Series
    request: Series
    partial_request: bool
    absent_request: bool


def _service_row(load: LoadAsset, readings: Sequence[Reading], w: Window) -> _Built:
    dlv = series(readings, FEEDER_DEMAND, load.asset_id, w)
    if load.feeder_request_bound or not load.critical:
        req = series(readings, FEEDER_REQUESTED, load.asset_id, w)
    else:
        # q2 ruling 12: the single critical request qualifies only the pinned critical asset, and only when no
        # feeder-request binding exists for it; a bound but empty feeder request is never bypassed.
        req = series(readings, CRITICAL_REQUESTED, load.asset_id, w)
    request_state = "CONFLICT" if req.state == CONFLICTING else "ACCEPTED" if req.complete else "MISSING"
    unusable = bool(dlv.unusable or req.unusable)
    # q2 ruling 13: conflict, partial delivery or request, an unusable required row, or complete but unaligned
    # series limit the row; absent delivery or request is UNKNOWN; complete aligned GOOD series are SUPPORTED.
    if CONFLICTING in (dlv.state, req.state) or PARTIAL in (dlv.state, req.state) or unusable:
        assessment = "LIMITED"
    elif dlv.state == MISSING or req.state == MISSING:
        assessment = "UNKNOWN"  # complete measured delivery with no request remains UNKNOWN
    elif _aligned(req, dlv):
        assessment = "SUPPORTED"
    else:
        assessment = "LIMITED"
    supported = assessment == "SUPPORTED"
    row = ServiceRow(
        asset_id=load.asset_id, asset_code=load.asset_code, load_label=load.load_label,
        role="CRITICAL" if load.critical else "UNCLASSIFIED",
        delivered_kw=dlv.mean_kw(), requested_evidence_state=request_state, assessment=assessment,
        coverage=dlv.coverage, evidence_ids=_cited((dlv, req)),
        interruptions=_interruptions(req, dlv) if supported else None,
        unserved_kwh=(sum((max(_ZERO, r.value - d.value) * r.seconds for r, d in zip(req.segments, dlv.segments)),
                          _ZERO) / _HOUR_SECONDS) if supported else None,
    )
    return _Built(row, dlv, req, req.state == PARTIAL, req.state == MISSING)


def assess_service_hour(w: Window, readings: Sequence[Reading], loads: Sequence[LoadAsset]) -> ServiceHour:
    """Closure 1 Q17 and q2 rulings 12-14: delivered power per addressed feeder; request evidence decides service."""
    built = [_service_row(load, readings, w) for load in loads]
    rows = tuple(sorted((b.row for b in built), key=lambda r: (r.role != "CRITICAL", r.asset_code, str(r.asset_id))))
    delivered = [b.delivered for b in built]
    requests = [b.request for b in built]
    critical = sorted((load.asset_id for load in loads if load.critical), key=str)
    # q2 ruling 14: critical delivery is the pinned critical LOAD asset's series only.
    crit_del = series(readings, CRITICAL_DELIVERED, critical[0], w) if len(critical) == 1 else None
    crit_parts = (crit_del,) if crit_del is not None else ()

    all_supported = bool(rows) and all(r.assessment == "SUPPORTED" for r in rows)
    complete_delivery = (bool(delivered) and all(d.complete and not d.unusable for d in delivered))

    limitations: list[Limitation] = []
    partial = [d for d in delivered if d.state == PARTIAL] + [b.request for b in built if b.partial_request]
    unusable = [s for s in (*delivered, *requests, *crit_parts) if s.unusable]
    conflicting = [s for s in (*delivered, *requests) if s.state == CONFLICTING]
    if partial:
        limitations.append(Limitation("COVERAGE_GAP", _cited(partial)))
    if unusable:
        bad_ids = tuple(sorted({i for u in unusable for i in u.unusable}, key=str))
        limitations.append(Limitation("REQUIRED_INPUT_UNUSABLE", bad_ids))
    if conflicting:
        limitations.append(Limitation("CONFLICT", _cited(conflicting)))
    if not rows or any(b.absent_request for b in built):
        limitations.append(Limitation("REQUEST_BASELINE_MISSING", ()))

    if conflicting or partial or unusable or any(r.assessment == "LIMITED" for r in rows):
        status = "LIMITED"
    elif all_supported:
        status = "SUPPORTED"
    else:
        status = "UNKNOWN"

    coverage = _combined(w, delivered, _sources(delivered)) if delivered else _coverage(w, (), set())
    in_hour = [r for r in readings if _in_window(r, w)]
    return ServiceHour(
        window=w, status=status,
        delivered_load_kw=sum((r.delivered_kw for r in rows if r.delivered_kw is not None), _ZERO)
        if complete_delivery else None,
        interruptions_seen=sum(r.interruptions or 0 for r in rows) if all_supported else None,
        critical_delivered_kw=crit_del.mean_kw()
        if crit_del is not None and crit_del.complete and not crit_del.unusable else None,
        unserved_kwh=sum((r.unserved_kwh or _ZERO for r in rows), _ZERO) if all_supported else None,
        rows=rows, limitations=tuple(sorted(limitations, key=lambda l: LIMITATION_ORDER.index(l.code))),
        coverage=coverage, evidence_ids=_cited((*delivered, *requests, *crit_parts), in_hour),
        critical_delivered_coverage=crit_del.coverage if crit_del is not None else None,
    )


# --- Fuel ------------------------------------------------------------------------------------------------------

GENERATOR_POWER, FUEL_LEVEL = "generator_power", "fuel_level"
LITRES = "L"  # `fuel_level` unit (sites/binding_roles.py)
#: Closure 1 Q16 / closure 2 fuel paragraph: the fixed bridge term order.
FUEL_TERMS: tuple[str, ...] = ("OPENING", "DELIVERIES", "USE", "CLOSING", "RESIDUAL")


@dataclass(frozen=True)
class SfcValue:
    """One pinned generator `specific-fuel-consumption` revision in L/kWh over its in-force `[valid_from, valid_to)`
    (`valid_to=None` is open). The caller selects it as `financials/fuel_cost.py` does."""

    property_revision_id: UUID
    value_l_per_kwh: Decimal
    valid_from: datetime
    valid_to: datetime | None


@dataclass(frozen=True)
class FuelInputs:
    sfc: tuple[SfcValue, ...]
    #: `fuel-cost-1/sfc-upper-multiplier/v1` (1.10), supplied by the caller from `financials/fuel_cost.py`.
    upper_multiplier: Decimal


@dataclass(frozen=True)
class FuelRow:
    term: str
    basis: str  # ACCEPTED_READING | FOUNDATION_MODEL | AUTHORED_EVIDENCE_UNAVAILABLE | MISSING
    treatment: str  # OBSERVED | MODELLED | COMPLETENESS_UNCONFIRMED | MISSING | CONFLICT
    value: Bound | None
    evidence_ids: tuple[UUID, ...]
    #: q6 ruling 2: the term's coverage over the selected hour (instants and absent terms cover zero seconds).
    coverage: Coverage | None = None


@dataclass(frozen=True)
class FuelHour:
    window: Window
    status: str
    opening_l: Bound | None
    deliveries_l: Bound | None
    expected_use_l: Bound | None
    closing_l: Bound | None
    residual_l: Bound | None
    nominal_l: Decimal | None
    sfc_property_revision_ids: tuple[UUID, ...]
    generator_power_evidence_ids: tuple[UUID, ...]
    rows: tuple[FuelRow, ...]
    limitations: tuple[Limitation, ...]
    coverage: Coverage
    evidence_ids: tuple[UUID, ...]


def _sfc_for(seg: Segment, sfc: Sequence[SfcValue]) -> SfcValue | None:
    """The one positive SFC in force over the whole segment, or `None` (none, several, or not positive)."""
    found = [s for s in sfc if s.valid_from <= seg.start and (s.valid_to is None or seg.end <= s.valid_to)]
    if len(found) != 1 or not found[0].value_l_per_kwh > _ZERO:
        return None
    return found[0]


def _tank_term(term: str, level: Sequence[Reading]) -> tuple[FuelRow, bool]:
    """Opening/closing from an accepted scalar `fuel_level` reading. No merged tank measurement-uncertainty property
    exists, so a scalar reading never yields a bound (closure 2): the value is null either way. Returns the row and
    whether an accepted valid reading was found.

    q4 ruling 3: a candidate failing the tank-level predicate (`_unusable` in litres) is unusable. It makes the term
    it competes for unavailable: OPENING when at or before the earliest valid instant, CLOSING when at or after the
    latest, both when no valid candidate exists."""
    good = [r for r in level if not _unusable(r, LITRES)]
    bad = [r for r in level if _unusable(r, LITRES)]
    if not good:
        return FuelRow(term, "MISSING", "MISSING", None, tuple(sorted({r.evidence_id for r in level}, key=str))), False
    edge = min(r.source_time for r in good) if term == "OPENING" else max(r.source_time for r in good)
    at = [r for r in good if r.source_time == edge]
    rivals = [r for r in bad if (r.source_time <= edge if term == "OPENING" else r.source_time >= edge)]
    if rivals:
        return FuelRow(term, "MISSING", "MISSING", None, _ids(r.evidence_id for r in (*at, *rivals))), False
    treatment = "CONFLICT" if len({r.value for r in at}) > 1 else "MISSING"
    return FuelRow(term, "ACCEPTED_READING", treatment, None, tuple(sorted({r.evidence_id for r in at}, key=str))), True


def _instant_coverage(w: Window, sources: Iterable[UUID]) -> Coverage:
    """q6 rulings 2-3: instants cover zero seconds; the whole window is the gap; distinct usable sources count."""
    return Coverage(int(w.seconds), 0, len(set(sources)), (Gap(w.start, w.end),))


def assess_fuel_hour(w: Window, readings: Sequence[Reading], inputs: FuelInputs) -> FuelHour:
    """Closure 1 Q16 as amended by closure 2: modelled expected use from accepted `generator_power` interval means
    times the in-force SFC, `{low: 0, high: multiplier x nominal}`; inventory terms stay null in W4-02."""
    gen = series(readings, GENERATOR_POWER, None, w, any_asset=True)
    level = [r for r in readings if r.role == FUEL_LEVEL and _in_window(r, w)]

    nominal: Decimal | None = None
    sfc_ids: set[UUID] = set()
    # q4 ruling 3: an in-window unusable bound generator row withholds the modelled use even when GOOD rows cover.
    if gen.complete and not gen.unusable:
        total = _ZERO
        for seg in gen.segments:
            chosen = _sfc_for(seg, inputs.sfc)
            if chosen is None:
                total = None  # type: ignore[assignment]
                break
            sfc_ids.add(chosen.property_revision_id)
            total += seg.value * seg.seconds / _HOUR_SECONDS * chosen.value_l_per_kwh
        nominal = total
    expected = Bound(_ZERO, inputs.upper_multiplier * nominal) if nominal is not None else None

    if expected is not None:
        use = FuelRow("USE", "FOUNDATION_MODEL", "MODELLED", expected, gen.cited)
    elif gen.state == CONFLICTING:
        use = FuelRow("USE", "FOUNDATION_MODEL", "CONFLICT", None, gen.cited)
    else:
        use = FuelRow("USE", "MISSING", "MISSING", None, gen.cited)
    opening, _ = _tank_term("OPENING", level)
    closing, _ = _tank_term("CLOSING", level)

    def tank_cov(row: FuelRow) -> FuelRow:
        cited = set(row.evidence_ids)
        return replace(row, coverage=_instant_coverage(
            w, (r.source_id for r in level if r.evidence_id in cited and not _unusable(r, LITRES))))

    opening, closing = tank_cov(opening), tank_cov(closing)
    rows = (
        opening,
        FuelRow("DELIVERIES", "AUTHORED_EVIDENCE_UNAVAILABLE", "COMPLETENESS_UNCONFIRMED", None, (),
                _instant_coverage(w, ())),
        replace(use, coverage=gen.coverage),
        closing,
        FuelRow("RESIDUAL", "MISSING", "MISSING", None, (), _instant_coverage(w, ())),
    )

    limitations = [Limitation("DELIVERY_COMPLETENESS_MISSING", ()),
                   Limitation("CLOSING_READING_MISSING", closing.evidence_ids)]
    if gen.state == PARTIAL:
        limitations.append(Limitation("COVERAGE_GAP", gen.cited))
    bad_tank = [r.evidence_id for r in level if _unusable(r, LITRES)]
    unusable = _ids([*gen.unusable, *bad_tank])
    if unusable:
        limitations.append(Limitation("REQUIRED_INPUT_UNUSABLE", unusable))
    conflict = gen.state == CONFLICTING or "CONFLICT" in (opening.treatment, closing.treatment)
    if conflict:
        tank = set(opening.evidence_ids) | set(closing.evidence_ids)
        limitations.append(Limitation("CONFLICT", _cited((gen,), [r for r in level if r.evidence_id in tank])))
    # Residual needs all five terms and delivery completeness, which W4-02 never has, so no fuel hour is SUPPORTED.
    status = "LIMITED" if conflict or gen.state == PARTIAL or unusable else "UNKNOWN"
    return FuelHour(
        window=w, status=status, opening_l=None, deliveries_l=None, expected_use_l=expected, closing_l=None,
        residual_l=None, nominal_l=nominal, sfc_property_revision_ids=tuple(sorted(sfc_ids, key=str)),
        generator_power_evidence_ids=gen.cited, rows=rows,
        limitations=tuple(sorted(limitations, key=lambda l: LIMITATION_ORDER.index(l.code))),
        coverage=gen.coverage, evidence_ids=_cited((gen,), level),
    )


# --- Backup ----------------------------------------------------------------------------------------------------

SITE_SUPPLY, START_EVENT, BACKUP_BUS = "site_supply_state", "mini_backup_start_event", "mini_backup_bus_state"
#: Closure 1 Q8: chain step codes in their fixed order.
BACKUP_STEPS: tuple[str, ...] = ("LOSS", "REQUEST", "START", "POWER", "LOAD", "SERVICE")
#: Valid `mini_backup_start_event` kind/outcome pairs (closure 4 B2).
_START_PAIRS = frozenset({("START_REQUEST", "REQUESTED"), ("START_RESULT", "SUCCEEDED"), ("START_RESULT", "FAILED")})


@dataclass(frozen=True)
class Observation:
    """One cutoff-visible accepted STATE or EVENT row (closure 4 B2). `state` is the normalized state value text;
    `record_kind`/`outcome`/`correlation_id` are the v4 event fields."""

    evidence_id: UUID
    source_id: UUID  # q6 ruling 3: counts real sources for instant roles; `evidence_id` stays the citation
    role: str
    source_time: datetime
    quality: str
    state: str | None = None
    record_kind: str | None = None
    outcome: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class Step:
    code: str
    state: str  # OBSERVED | MISSING | CONFLICT
    at: datetime | None
    evidence_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class Recovery:
    seconds: Decimal
    target_seconds: Decimal


@dataclass(frozen=True)
class BackupChain:
    chain_id: str
    outage_start: datetime
    steps: tuple[Step, ...]
    service_outcome: str  # RECOVERED | MISSED_TARGET | UNKNOWN
    result: str  # PASS | FAIL | INCOMPLETE
    critical_recovery: Recovery | None
    start_succeeded: bool
    evidence_ids: tuple[UUID, ...]
    #: q4 ruling 3: unusable rows among this chain's required bound inputs (and the hour's supply rows).
    unusable: tuple[UUID, ...] = ()
    #: q6 ruling 2: measured critical-service span over the bounded outage `[LOSS, restoration or hour end)`.
    coverage: Coverage | None = None
    #: q6 ruling 6: outcome of the one witnessed, correlated, noncontradictory start request/result pair, if any.
    start_pair: str | None = None


@dataclass(frozen=True)
class BackupHour:
    window: Window
    status: str
    outage_count: int
    #: q6 ruling 6: successful witnessed request/result pairs; `None` when no witnessed pair exists.
    start_success_count: int | None
    last_witnessed_test_at: None  # no accepted witnessed test record exists in W4-02 (closure 1 Q2)
    critical_recovery: Recovery | None
    chains: tuple[BackupChain, ...]
    limitations: tuple[Limitation, ...]
    coverage: Coverage
    evidence_ids: tuple[UUID, ...]


def _ids(items: Iterable[UUID]) -> tuple[UUID, ...]:
    return tuple(sorted(set(items), key=str))


def _good(obs: Iterable[Observation], role: str) -> list[Observation]:
    return sorted((o for o in obs if o.role == role and o.quality == GOOD),
                  key=lambda o: (o.source_time, str(o.evidence_id)))


def _first_state(rows: Sequence[Observation], code: str, value: str, after: datetime,
                 before: datetime) -> Step | None:
    """The earliest `value` state strictly after `after` and before `before`; two different states at that
    instant are a conflict."""
    hits = [o for o in rows if after < o.source_time < before and o.state == value]
    if not hits:
        return None
    at = hits[0].source_time
    same = [o for o in rows if o.source_time == at]
    state = "CONFLICT" if len({o.state for o in same}) > 1 else "OBSERVED"
    return Step(code, state, at, _ids(o.evidence_id for o in same))


def _bad_observation(o: Observation) -> bool:
    """q4 ruling 3: a non-GOOD or wrong-value STATE/EVENT row. A GOOD instant with a declared value is valid."""
    if o.quality != GOOD:
        return True
    if o.role == SITE_SUPPLY:
        return o.state not in MINI_SUPPLY_STATES
    if o.role == BACKUP_BUS:
        return o.state not in MINI_BUS_STATES
    if o.role == START_EVENT:
        return (o.record_kind, o.outcome) not in _START_PAIRS or not o.correlation_id
    return False


def _chain_unusable(t0: datetime, end: datetime, correlation: str | None, obs: Sequence[Observation],
                    readings: Sequence[Reading]) -> set[UUID]:
    """Unusable rows among one outage's required bound inputs: the correlated start events (every in-outage start
    row while no request is selected), the bus state, and the generator and critical interval rows in the outage."""
    bad = {o.evidence_id for o in obs if t0 <= o.source_time < end and _bad_observation(o) and (
        o.role == BACKUP_BUS or (o.role == START_EVENT and (correlation is None or o.correlation_id == correlation)))}
    if t0 < end:
        span = Window(t0, end)
        bad |= {r.evidence_id for r in readings
                if r.role in (GENERATOR_POWER, CRITICAL_REQUESTED, CRITICAL_DELIVERED)
                and _in_window(r, span) and _unusable(r)}
    return bad


def _missing(code: str) -> Step:
    return Step(code, "MISSING", None, ())


def _witnessed_miss(t0: datetime, end: datetime, target: Decimal, readings: Sequence[Reading]) -> bool:
    """A missed target is witnessed only when complete aligned critical requested/delivered intervals cover
    `[t0, t0 + target)` inside the outage and none of them shows delivered >= requested."""
    deadline = t0 + timedelta(seconds=float(target))
    if deadline > end:
        return False
    span = Window(t0, deadline)
    req = series(readings, CRITICAL_REQUESTED, None, span, any_asset=True)  # rows already pinned (q5 ruling 4)
    dlv = series(readings, CRITICAL_DELIVERED, None, span, any_asset=True)
    return _aligned(req, dlv) and all(d.value < r.value for r, d in zip(req.segments, dlv.segments))


def _start_steps(t0: datetime, end: datetime, obs: Sequence[Observation]) -> tuple[str | None, Step, Step, bool]:
    events = [o for o in _good(obs, START_EVENT) if t0 <= o.source_time < end]
    request = next((o for o in events if o.record_kind == "START_REQUEST" and o.outcome == "REQUESTED"), None)
    if request is None:
        return None, _missing("REQUEST"), _missing("START"), False
    req_step = Step("REQUEST", "OBSERVED", request.source_time, (request.evidence_id,))
    results = [o for o in events if o.record_kind == "START_RESULT" and o.correlation_id == request.correlation_id
               and o.source_time > request.source_time]
    if not results:
        return request.correlation_id, req_step, _missing("START"), False
    outcomes = {o.outcome for o in results}
    start = Step("START", "CONFLICT" if len(outcomes) > 1 else "OBSERVED", results[0].source_time,
                 _ids(o.evidence_id for o in results))
    return request.correlation_id, req_step, start, outcomes == {"SUCCEEDED"}


def _power_step(start: Step, end: datetime, obs: Sequence[Observation], readings: Sequence[Reading]) -> Step | None:
    """POWER reads `mini_backup_bus_state` ENERGIZED plus bound generator output > 0 after it (closure 4 B2)."""
    assert start.at is not None
    bus = _first_state(_good(obs, BACKUP_BUS), "POWER", "ENERGIZED", start.at, end)
    if bus is None or bus.at is None:
        return None
    output = [r for r in readings if r.role == GENERATOR_POWER and _usable(r) and r.value is not None
              and r.value > _ZERO and r.interval_end is not None and r.interval_start is not None
              and r.interval_end > bus.at and r.interval_start < end]
    if not output:
        return None
    return Step("POWER", bus.state, bus.at, _ids([*bus.evidence_ids, *(r.evidence_id for r in output)]))


def _interval_rows(readings: Sequence[Reading], role: str, after: datetime, end: datetime) -> list[Reading]:
    return sorted((r for r in readings if r.role == role and _usable(r)
                   and after <= r.interval_start < end),  # type: ignore[operator]
                  key=lambda r: (r.interval_start, str(r.evidence_id)))


def _load_and_service(power: Step, end: datetime, readings: Sequence[Reading]) -> tuple[Step | None, Step | None]:
    """LOAD: the first accepted critical delivered interval > 0 starting at or after POWER. SERVICE: the end of the
    first aligned critical interval from LOAD on whose delivered power meets the requested power."""
    assert power.at is not None
    delivered = _interval_rows(readings, CRITICAL_DELIVERED, power.at, end)
    first = next((r for r in delivered if r.value is not None and r.value > _ZERO), None)
    if first is None or first.interval_start is None:
        return None, None
    load = Step("LOAD", "OBSERVED", first.interval_start, (first.evidence_id,))
    requested = {(r.interval_start, r.interval_end): r
                 for r in _interval_rows(readings, CRITICAL_REQUESTED, first.interval_start, end)}
    for d in (r for r in delivered if r.interval_start >= first.interval_start):  # type: ignore[operator]
        q = requested.get((d.interval_start, d.interval_end))
        if q is not None and d.value is not None and q.value is not None and d.value >= q.value:
            return load, Step("SERVICE", "OBSERVED", d.interval_end, _ids((d.evidence_id, q.evidence_id)))
    return load, None


def _chain(loss: Step, loss_id: UUID, end: datetime, obs: Sequence[Observation], readings: Sequence[Reading],
           target_min: Decimal | None, hour_unusable: set[UUID], pinned: bool) -> BackupChain:
    t0 = loss.at
    assert t0 is not None
    correlation, request, start, succeeded = _start_steps(t0, end, obs)
    unusable = _ids(hour_unusable | _chain_unusable(t0, end, correlation, obs, readings))
    power = _power_step(start, end, obs, readings) if succeeded else None
    load, service = (_load_and_service(power, end, readings) if power is not None and power.state == "OBSERVED"
                     else (None, None))
    steps = (loss, request, start, power or _missing("POWER"), load or _missing("LOAD"), service or _missing("SERVICE"))

    timed = [s.at for s in steps if s.at is not None]
    ordered = all(a < b for a, b in zip(timed, timed[1:]))
    complete = ordered and all(s.state == "OBSERVED" for s in steps)
    target = None if target_min is None else target_min * 60
    recovery = None
    # q4 ruling 3: an unusable required row blocks PASS/FAIL (and the recovery it would be judged on).
    if (complete and service is not None and service.at is not None and target is not None and not unusable
            and pinned):
        recovery = Recovery(Decimal(str((service.at - t0).total_seconds())), target)
    if recovery is not None:
        result = "PASS" if recovery.seconds <= recovery.target_seconds else "FAIL"
    elif (target is not None and service is None and not unusable and pinned
          and all(s.state != "CONFLICT" for s in steps)
          and _witnessed_miss(t0, end, target, readings)):
        result = "FAIL"
    else:
        result = "INCOMPLETE"
    if result == "PASS":
        outcome = "RECOVERED"
    elif result == "FAIL":
        outcome = "MISSED_TARGET"
    else:
        outcome = "RECOVERED" if complete and service is not None and not unusable and pinned else "UNKNOWN"
    if t0 < end:
        span = Window(t0, end)
        measured = [series(readings, role, None, span, any_asset=True)  # rows already pinned (q5 ruling 4)
                    for role in (CRITICAL_REQUESTED, CRITICAL_DELIVERED)]
        coverage = _combined(span, measured, _sources(measured))
    else:
        coverage = Coverage(0, 0, 0, ())
    pair = None
    if start.state == "OBSERVED":
        outcomes = {o.outcome for o in obs if o.evidence_id in start.evidence_ids}
        pair = next(iter(outcomes)) if len(outcomes) == 1 and outcomes <= {"SUCCEEDED", "FAILED"} else None
    return BackupChain(correlation or str(loss_id), t0, steps, outcome, result, recovery, succeeded,
                       _ids(i for s in steps for i in s.evidence_ids), unusable, coverage, pair)


def assess_backup_hour(w: Window, observations: Sequence[Observation], readings: Sequence[Reading],
                       recovery_target_min: Decimal | None, *, critical_asset_id: UUID | None) -> BackupHour:
    """Closure 1 Q22 / closure 4 B2: each observed `site_supply_state` ENERGIZED->LOST transition inside the hour
    starts one bounded outage (ending at the next ENERGIZED, or the hour end). Nothing is inferred: a missing step
    keeps the chain INCOMPLETE; generator operation alone never passes. `observations` may include the last
    supply state before the hour, which only witnesses the transition."""
    supply = _good(observations, SITE_SUPPLY)
    bad_supply = [o for o in observations if o.role == SITE_SUPPLY and _bad_observation(o)]
    # q5 ruling 2: any bad in-hour supply row limits the hour; a bad row vetoes only the chain whose span (from its
    # usable ENERGIZED witness through the restoration instant) contains it.
    supply_bad = {o.evidence_id for o in bad_supply if w.start <= o.source_time < w.end}
    # q5 ruling 4: critical rows of the one pinned critical LOAD asset only; with no unique pin, none.
    pinned = critical_asset_id is not None
    crit_rows = [r for r in readings if r.role not in (CRITICAL_REQUESTED, CRITICAL_DELIVERED)
                 or (pinned and r.asset_id == critical_asset_id)]
    chains: list[BackupChain] = []
    previous: Observation | None = None
    for i, o in enumerate(supply):
        if (o.state == "LOST" and previous is not None and previous.state == "ENERGIZED"
                and w.start <= o.source_time < w.end):
            same = [x for x in supply if x.source_time == o.source_time]
            loss = Step("LOSS", "CONFLICT" if len({x.state for x in same}) > 1 else "OBSERVED", o.source_time,
                        _ids(x.evidence_id for x in same))
            restored = next((x.source_time for x in supply[i + 1:] if x.state == "ENERGIZED"), None)
            end = min(restored, w.end) if restored is not None else w.end
            chain_bad = {x.evidence_id for x in bad_supply if previous.source_time <= x.source_time
                         and (x.source_time <= end if restored is not None and restored <= w.end
                              else x.source_time < w.end)}
            supply_bad |= chain_bad
            chains.append(_chain(loss, o.evidence_id, end, observations, crit_rows, recovery_target_min,
                                 chain_bad, pinned))
        if o.state in ("ENERGIZED", "LOST"):
            previous = o
    chains.sort(key=lambda c: (c.outage_start, c.chain_id))

    limitations: list[Limitation] = []
    conflict = [c for c in chains if any(s.state == "CONFLICT" for s in c.steps)]
    incomplete = [c for c in chains if c.result == "INCOMPLETE"]
    if conflict:
        limitations.append(Limitation("CONFLICT", _ids(i for c in conflict for i in c.evidence_ids)))
    unusable = _ids([*supply_bad, *(i for c in chains for i in c.unusable)])
    if unusable:
        limitations.append(Limitation("REQUIRED_INPUT_UNUSABLE", unusable))
    if chains and not pinned:
        limitations.append(Limitation("CRITICAL_SERVICE_MISSING", ()))
    if recovery_target_min is None:
        limitations.append(Limitation("RECOVERY_TARGET_MISSING", ()))
    if not chains or incomplete:
        limitations.append(Limitation("BACKUP_CHAIN_INCOMPLETE", _ids(i for c in incomplete for i in c.evidence_ids)))
    if conflict or unusable or (chains and not pinned):
        status = "LIMITED"
    elif chains and not incomplete:
        status = "SUPPORTED"
    else:
        status = "UNKNOWN"

    crit = [_pinned(readings, role, critical_asset_id, w) for role in (CRITICAL_REQUESTED, CRITICAL_DELIVERED)]
    in_hour = [r for r in readings if _in_window(r, w)]
    latest = next((c.critical_recovery for c in reversed(chains) if c.critical_recovery is not None), None)
    return BackupHour(
        window=w, status=status, outage_count=len(chains),
        start_success_count=(sum(1 for c in chains if c.start_pair == "SUCCEEDED")
                             if any(c.start_pair is not None for c in chains) else None),
        last_witnessed_test_at=None,
        critical_recovery=latest, chains=tuple(chains),
        limitations=tuple(sorted(limitations, key=lambda l: LIMITATION_ORDER.index(l.code))),
        coverage=_combined(w, crit, _sources(crit)),
        evidence_ids=_ids([*_cited(crit, in_hour),
                           *(o.evidence_id for o in observations
                             if w.start <= o.source_time < w.end or o.role == SITE_SUPPLY)]),
    )
