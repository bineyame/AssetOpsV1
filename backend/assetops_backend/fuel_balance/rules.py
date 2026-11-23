"""DIESEL-K3 (`specs/DIESEL-1/` §9d.2, ruling DIESEL-1-R3d): the `fuel-balance-1` night check, pure and
exact (`Fraction`).

For one Site, one fuel tank and one Site-local night `[d 18:00, d+1 12:00)`, the tank's change from accepted
`fuel_level` readings is compared with the generator's expected burn from accepted generator readings and the recorded
deliveries. The band, the states and their order are F0's (`tools/probe_kisiwa_fuel.py` `balance`); the parameters are
F0's declaration, copied byte-for-byte, and any change is a new parameter version, never a retune.

Use comes only from accepted generator readings through A2's slot rule (`verification_rules._power_slot`, `_instant`
and `idle_slot`, the shared idle rule of ruling DIESEL-1-R3h; imported by name and never edited here). This module
never reads a run or the simulator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from fractions import Fraction
from typing import Any, Iterable, Sequence

from assetops_backend.actions.verification_rules import (
    ACCEPTED_QUALITY, Reading, _instant, _power_slot, fmt, idle_slot, parse_exact)
from assetops_backend.financials.fuel_cost import sha256_canonical
from assetops_backend.fuel_balance.model import (
    LIMITATIONS, PARAMETER_VERSION, REASONS, WINDOW_INVALID, FuelBalanceRefused)
from assetops_backend.mini_depth.inputs import MiniInputsRefused, zone
from assetops_backend.work.fuel_records import FuelRecord

# --- F0's declaration (`tools/probe_kisiwa_fuel.py:80-94`), verbatim, plus the parameter version ------------------
PARAMETERS = {
    "id": "fuel-balance-1",
    "window": "night k, 18:00 local to 12:00 local next day",
    "opening": "last accepted fuel_level reading in [start - 30 min, start]; missing -> NOT_ASSESSED MISSING_OPENING",
    "closing": "first accepted fuel_level reading in [end, end + 30 min]; missing -> NOT_ASSESSED MISSING_CLOSING",
    "accuracy_a_l": "10 (GENERIC_DEFAULT)", "tank_margin_l": "2a = 20",
    "deliveries": "sum of FUEL_DELIVERY ticket volumes with instant in [start, end); tolerance 1/100 x ticket",
    "use": "loaded = sum kWh x 0.355; idle_h = RUNNING 5-min slots at 0 kWh; use_low = 9/10 loaded; "
           "use_high = 11/10 (loaded + idle_h x 4.9)",
    "residual_low": "(O - C) + D - D_tol - use_high - 2a", "residual_high": "(O - C) + D + D_tol - use_low + 2a",
    "states": "UNEXPLAINED iff residual_low >= 40; WITHIN_MARGIN iff residual_low <= 0 <= residual_high; "
              "BELOW_MATERIALITY iff 0 < residual_low < 40; EXCESS iff residual_high < 0",
    "gap": "sum of spans longer than 60 min between consecutive accepted fuel_level readings inside the window, "
           "edges included",
    "parameter_version": PARAMETER_VERSION,
}

# --- F0's constants (`tools/probe_kisiwa_fuel.py:72-78`); a, SFC and r are the Site's declared values ---------------
TANK_MARGIN_FACTOR = 2  # margin = 2 x a
DELIVERY_TOLERANCE = Fraction(1, 100)
USE_LOW_FACTOR, USE_HIGH_FACTOR = Fraction(9, 10), Fraction(11, 10)
MATERIALITY_L = Fraction(40)
EDGE_SEARCH_MIN = 30
GAP_LONGER_THAN_MIN = 60
SLOT_MIN = 5
#: §9d.2 limitation 2: a dip conflicts with the nearest reading when they differ by more than a + 10 L
DIP_CONFLICT_EXTRA_L = Fraction(10)
NIGHT_START, NIGHT_END = time(18), time(12)
LITRES = "L"
#: K1's vocabulary literals (§9c.1) for `fuel-level-sensor-accuracy-basis`
ACCURACY_BASES = frozenset({"GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_CALIBRATION"})

FUEL_LEVEL, GENERATOR_POWER, GENERATOR_STATE = "fuel_level", "generator_power", "generator_state"
ROLES = (FUEL_LEVEL, GENERATOR_POWER, GENERATOR_STATE)
DELIVERY, DIP = "FUEL_DELIVERY", "TANK_DIP"

_EDGE = timedelta(minutes=EDGE_SEARCH_MIN)
_SLOT = timedelta(minutes=SLOT_MIN)


@dataclass(frozen=True)
class Declared:
    """One Site-declared value (a, SFC or r) on one Foundation revision, in force over `[valid_from, valid_to)`."""

    value: Fraction
    basis: str | None
    revision_id: str
    valid_from: datetime
    valid_to: datetime | None = None


@dataclass(frozen=True)
class WindowResult:
    state: str
    reason: str | None
    residual_low: Fraction | None
    residual_high: Fraction | None
    gap_minutes: int
    gap_spans: tuple[tuple[datetime, datetime], ...]
    limitations: tuple[str, ...]
    terms: dict[str, Any] = field(hash=False)


@dataclass(frozen=True)
class GeneratorUnit:
    """One GENERATOR unit of the Site with its declared SFC and no-load rate in force over the window (D-DD.117)."""

    asset_id: str
    sfc: Declared | None
    no_load: Declared | None


# --- window ------------------------------------------------------------------------------------------------------


def _local(day: date, at: time, tz_name: str, tz) -> datetime:
    naive = datetime.combine(day, at)
    first = naive.replace(tzinfo=tz, fold=0).astimezone(timezone.utc)
    second = naive.replace(tzinfo=tz, fold=1).astimezone(timezone.utc)
    if first.astimezone(tz).replace(tzinfo=None) != naive:
        raise FuelBalanceRefused(WINDOW_INVALID, f"{naive.isoformat()} does not exist in {tz_name}")
    if first != second:
        raise FuelBalanceRefused(WINDOW_INVALID, f"{naive.isoformat()} is ambiguous in {tz_name}")
    return first


def night_window(night_date: date, tz_name: str | None) -> tuple[datetime, datetime]:
    """Night `d` = `[local(d, 18:00), local(d + 1, 12:00))` in UTC (fold 0), on UTC five-minute boundaries."""
    try:
        tz = zone(tz_name)
    except MiniInputsRefused as error:
        raise FuelBalanceRefused(WINDOW_INVALID, error.detail) from error
    start = _local(night_date, NIGHT_START, str(tz_name), tz)
    end = _local(night_date + timedelta(days=1), NIGHT_END, str(tz_name), tz)
    for bound in (start, end):
        if bound.second or bound.microsecond or bound.minute % SLOT_MIN:
            raise FuelBalanceRefused(WINDOW_INVALID, f"{bound.isoformat()} is not on a UTC five-minute boundary")
    return start, end


# --- inputs ------------------------------------------------------------------------------------------------------


def relevant_readings(readings: Iterable[Reading], tank_asset_id: str,
                      generator_asset_id: str | Sequence[str]) -> tuple[Reading, ...]:
    """The tank's `fuel_level` and every generator unit's power and state readings (one id or every unit's,
    D-DD.117); any other asset's are ignored."""
    tank = str(tank_asset_id)
    gens = {str(generator_asset_id)} if isinstance(generator_asset_id, str) else {str(g) for g in generator_asset_id}
    return tuple(r for r in readings
                 if (r.role == FUEL_LEVEL and r.asset_id == tank)
                 or (r.role in (GENERATOR_POWER, GENERATOR_STATE) and r.asset_id in gens))


def accepted_levels(readings: Iterable[Reading], tank_asset_id: str) -> list[tuple[datetime, Fraction, str]]:
    """Accepted tank levels as `(source_time, litres, id)`, ordered: quality GOOD, unit L, a finite decimal value
    (no `p/q`) and a UTC-aware `source_time`. Others are ignored."""
    out = []
    for r in readings:
        if r.role != FUEL_LEVEL or r.asset_id != str(tank_asset_id) or r.quality != ACCEPTED_QUALITY:
            continue
        if r.unit != LITRES or not isinstance(r.value_text, str) or "/" in r.value_text:
            continue
        value = parse_exact(r.value_text)
        at = r.source_time
        if value is None or not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
            continue
        out.append((at.astimezone(timezone.utc), value, r.id))
    return sorted(out, key=lambda x: (x[0], x[2]))


def _pick(levels: list[tuple[datetime, Fraction, str]], at: datetime) -> tuple[datetime, Fraction, bool]:
    values = {v for t, v, _ in levels if t == at}
    return at, next(iter(values)), len(values) > 1


def opening_closing(levels: list[tuple[datetime, Fraction, str]], start: datetime, end: datetime
                    ) -> tuple[tuple[datetime, Fraction] | None, tuple[datetime, Fraction] | None, bool]:
    """F0's rule: O = the last accepted level in `[start - 30 min, start]`, C = the first in `[end, end + 30 min]`.
    Returns `(opening, closing, conflict)`; `conflict` is True when two accepted readings at a chosen instant differ."""
    before = [t for t, _, _ in levels if start - _EDGE <= t <= start]
    after = [t for t, _, _ in levels if end <= t <= end + _EDGE]
    opening = closing = None
    conflict = False
    if before:
        at, value, bad = _pick(levels, max(before))
        opening, conflict = (at, value), conflict or bad
    if after:
        at, value, bad = _pick(levels, min(after))
        closing, conflict = (at, value), conflict or bad
    return opening, closing, conflict


def use_from_readings(start: datetime, end: datetime, readings: Iterable[Reading],
                      generator_asset_id: str) -> dict[str, Any]:
    """A2's slot rule over every 5-minute slot of `[start, end)`: kWh from `_power_slot`, the state from `_instant`;
    a slot is idle per A2's slot rule (`verification_rules.idle_slot`). `generator_kwh`/`idle_seconds` are None
    when any slot is unknown."""
    gen = str(generator_asset_id)
    readings = list(readings)
    power = [r for r in readings if r.role == GENERATOR_POWER and r.asset_id == gen]
    state = [r for r in readings if r.role == GENERATOR_STATE and r.asset_id == gen]
    total: Fraction | None = Fraction(0)
    idle_slots = 0
    kwh_unknown = state_unknown = False
    unknown_slots = 0
    t = start
    while t < end:
        kwh = _power_slot(t, power)[1]
        value = _instant(t, state, numeric=False)[1]
        if kwh is None:
            kwh_unknown = True
            total = None
        elif total is not None:
            total += kwh
        if value is None:
            state_unknown = True
        if kwh is None or value is None:
            unknown_slots += 1
        elif idle_slot(t, value, kwh, state):
            idle_slots += 1
        t += _SLOT
    idle = None if (kwh_unknown or state_unknown) else int(_SLOT.total_seconds()) * idle_slots
    return {"generator_kwh": total, "idle_seconds": idle, "kwh_unknown": kwh_unknown,
            "state_unknown": state_unknown, "unknown_slots": unknown_slots}


def reporting_gap(times: Iterable[datetime], start: datetime, end: datetime
                  ) -> tuple[int, tuple[tuple[datetime, datetime], ...]]:
    """F0's `reporting_gap_minutes`: points = start, the accepted reading times strictly inside, end; the gap is the
    sum of consecutive differences longer than 60 min, with those spans in order."""
    points = [start] + sorted({t for t in times if start < t < end}) + [end]
    spans = tuple((a, b) for a, b in zip(points, points[1:]) if b - a > timedelta(minutes=GAP_LONGER_THAN_MIN))
    seconds = sum(int((b - a).total_seconds()) for a, b in spans)
    return seconds // 60, spans


def balance(*, opening: Fraction, closing: Fraction, deliveries: Iterable[Fraction], loaded_litres: Fraction,
            idle_hours: Fraction, accuracy_l: Fraction, no_load_l_per_h: Fraction) -> dict[str, Any]:
    """F0's band (`tools/probe_kisiwa_fuel.py:106-134`), exactly, with a and r the Site's declared values."""
    d = sum((Fraction(v) for v in deliveries), Fraction(0))
    d_tol = DELIVERY_TOLERANCE * d
    loaded, idle_h = Fraction(loaded_litres), Fraction(idle_hours)
    use_low = USE_LOW_FACTOR * loaded
    use_high = USE_HIGH_FACTOR * (loaded + idle_h * Fraction(no_load_l_per_h))
    margin = TANK_MARGIN_FACTOR * Fraction(accuracy_l)
    drop = Fraction(opening) - Fraction(closing)
    low = drop + d - d_tol - use_high - margin
    high = drop + d + d_tol - use_low + margin
    if low >= MATERIALITY_L:
        state = "UNEXPLAINED"
    elif high < 0:
        state = "EXCESS"
    elif low <= 0 <= high:
        state = "WITHIN_MARGIN"
    else:
        state = "BELOW_MATERIALITY"
    return {"state": state, "residual_low": low, "residual_high": high, "opening_minus_closing": drop,
            "deliveries": d, "delivery_tolerance": d_tol, "use_low": use_low, "use_high": use_high}


def _nearest(levels: list[tuple[datetime, Fraction, str]], at: datetime) -> Fraction | None:
    near = [(abs(t - at), t, rid, v) for t, v, rid in levels if abs(t - at) <= _EDGE]
    return min(near, key=lambda x: (x[0], x[1], x[2]))[3] if near else None


def limitations(*, gap_minutes: int, levels: list[tuple[datetime, Fraction, str]], records: Sequence[FuelRecord],
                accuracy_l: Fraction | None, end: datetime) -> tuple[str, ...]:
    """Information only; never changes the state. Fixed order, each at most once."""
    found: set[str] = set()
    if gap_minutes > 0:
        found.add("REPORTING_GAP")
    if accuracy_l is not None:
        for r in records:
            if r.kind != DIP:
                continue
            reading = _nearest(levels, r.occurred_at)
            if reading is not None and abs(Fraction(r.quantity_l) - reading) > accuracy_l + DIP_CONFLICT_EXTRA_L:
                found.add("DIP_SENSOR_CONFLICT")
    if any(r.kind == DELIVERY and r.root_recorded_at > end + _EDGE for r in records):
        found.add("DELIVERY_RECORDED_LATE")
    return tuple(code for code in LIMITATIONS if code in found)


# --- declared values -------------------------------------------------------------------------------------------


def declared_for(values: Iterable[Declared], start: datetime, end: datetime,
                 bases: frozenset[str] | None) -> Declared | None:
    """The one positive declared value in force over the whole window (`trial_fuel_comparison.sfc_for` semantics);
    with `bases`, its basis must be one of them. Otherwise None."""
    found = [v for v in values if v.valid_from <= start and (v.valid_to is None or end <= v.valid_to)]
    if len(found) != 1 or not found[0].value > 0:
        return None
    if bases is not None and found[0].basis not in bases:
        return None
    return found[0]


# --- the night -------------------------------------------------------------------------------------------------


def iso(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(timezone.utc).isoformat()


def _unit_use(start: datetime, end: datetime, readings: Sequence[Reading], unit: GeneratorUnit) -> dict[str, Any]:
    """One unit on its own curve (D-DD.117, D-DD.113's shape): its kWh and idle time from A2's slot rule, its loaded
    litres on its own SFC and its idle litres on its own no-load rate (None when any input is unknown)."""
    use = use_from_readings(start, end, readings, unit.asset_id)
    kwh, idle_s = use["generator_kwh"], use["idle_seconds"]
    loaded = None if kwh is None or unit.sfc is None else unit.sfc.value * kwh
    idle_l = None if idle_s is None or unit.no_load is None else Fraction(idle_s, 3600) * unit.no_load.value
    return {**use, "loaded": loaded, "idle_litres": idle_l}


def _sum(values: Iterable[Fraction | int | None]) -> Any:
    """The Site value: the sum of the units' values; any unit unknown makes it unknown (D-DD.41, no imputation)."""
    values = list(values)
    return None if any(v is None for v in values) else sum(values[1:], values[0])


def _declared_terms(sfc: Declared | None, no_load: Declared | None) -> dict[str, Any]:
    return {"sfc_l_per_kwh": fmt(sfc and sfc.value), "sfc_revision_id": sfc and sfc.revision_id,
            "no_load_l_per_h": fmt(no_load and no_load.value), "no_load_basis": no_load and no_load.basis,
            "no_load_revision_id": no_load and no_load.revision_id}


def assess(*, start: datetime, end: datetime, tank_asset_id: str, units: Sequence[GeneratorUnit],
           readings: Iterable[Reading], records: Sequence[FuelRecord], accuracy: Declared | None) -> WindowResult:
    """One night. `units` are the Site's GENERATOR units in declared Foundation order (the lead first, D-DD.117),
    each with the SFC and no-load rate in force over the window (None when missing); `records` are the tank's fuel
    records occurring in `[start, end)`; `accuracy` likewise. Reasons in `model.REASONS` precedence. Model-implied
    litres are the sum of each unit's burn on its own SFC and no-load rate; one unit reads exactly as v1."""
    readings = relevant_readings(readings, tank_asset_id, [u.asset_id for u in units])
    levels = accepted_levels(readings, tank_asset_id)
    opening, closing, conflict = opening_closing(levels, start, end)
    uses = [_unit_use(start, end, readings, u) for u in units]
    gap_minutes, spans = reporting_gap((t for t, _, _ in levels), start, end)
    deliveries = [Fraction(r.quantity_l) for r in records if r.kind == DELIVERY]
    d = sum(deliveries, Fraction(0))

    kwh, idle_s = _sum(u["generator_kwh"] for u in uses), _sum(u["idle_seconds"] for u in uses)
    loaded = _sum(u["loaded"] for u in uses)
    idle_l = _sum(u["idle_litres"] for u in uses)
    use_low = None if loaded is None else USE_LOW_FACTOR * loaded
    use_high = (None if loaded is None or idle_l is None
                else USE_HIGH_FACTOR * (loaded + idle_l))

    checks = {"NO_SENSOR_ACCURACY": accuracy is None, "SFC_MISSING": any(u.sfc is None for u in units),
              "NO_LOAD_RATE_MISSING": any(u.no_load is None for u in units), "MISSING_OPENING": opening is None,
              "MISSING_CLOSING": closing is None, "FUEL_LEVEL_CONFLICT": conflict,
              "GENERATOR_KWH_UNKNOWN": any(u["kwh_unknown"] for u in uses),
              "IDLE_SECONDS_UNKNOWN": any(u["state_unknown"] for u in uses)}
    reason = next((code for code in REASONS if checks[code]), None)
    state, low, high = "NOT_ASSESSED", None, None
    if reason is None:
        # One unit: F0's band with the unit's own idle hours and rate, exactly. Several: the idle litres are the
        # units' sum, carried as one hour at that rate (the same exact product).
        one = len(units) == 1
        band = balance(opening=opening[1], closing=closing[1], deliveries=deliveries, loaded_litres=loaded,
                       idle_hours=Fraction(idle_s, 3600) if one else Fraction(1),
                       accuracy_l=accuracy.value, no_load_l_per_h=units[0].no_load.value if one else idle_l)
        state, low, high = band["state"], band["residual_low"], band["residual_high"]
        use_low, use_high = band["use_low"], band["use_high"]

    lead = units[0]
    declared = (_declared_terms(lead.sfc, lead.no_load) if len(units) == 1
                else _declared_terms(None, None))  # several units: each unit's declared values are in `units`
    terms = {
        "opening_l": fmt(None if opening is None else opening[1]), "opening_at": iso(opening and opening[0]),
        "closing_l": fmt(None if closing is None else closing[1]), "closing_at": iso(closing and closing[0]),
        "deliveries_l": fmt(d), "delivery_tolerance_l": fmt(DELIVERY_TOLERANCE * d),
        "generator_kwh": fmt(kwh), "loaded_litres": fmt(loaded), "idle_seconds": idle_s,
        "use_low": fmt(use_low), "use_high": fmt(use_high),
        "accuracy_l": fmt(accuracy and accuracy.value), "accuracy_basis": accuracy and accuracy.basis,
        "accuracy_revision_id": accuracy and accuracy.revision_id,
        **declared,
        "unknown_slots": sum(u["unknown_slots"] for u in uses),
    }
    if len(units) > 1:
        terms["units"] = [{"asset_id": str(unit.asset_id), "generator_kwh": fmt(u["generator_kwh"]),
                           "idle_seconds": u["idle_seconds"], "loaded_litres": fmt(u["loaded"]),
                           "unknown_slots": u["unknown_slots"], **_declared_terms(unit.sfc, unit.no_load)}
                          for unit, u in zip(units, uses)]
    lims = limitations(gap_minutes=gap_minutes, levels=levels, records=records,
                       accuracy_l=None if accuracy is None else accuracy.value, end=end)
    return WindowResult(state=state, reason=reason, residual_low=low, residual_high=high, gap_minutes=gap_minutes,
                        gap_spans=spans, limitations=lims, terms=terms)


def _declared(value: Declared | None, with_basis: bool) -> list[Any] | None:
    if value is None:
        return None
    return [fmt(value.value), value.basis, value.revision_id] if with_basis else [fmt(value.value), value.revision_id]


def input_sha256(*, night_date: date, start: datetime, end: datetime, tank_asset_id: str,
                 units: Sequence[GeneratorUnit], accuracy: Declared | None, evidence_ids: Iterable[str],
                 records: Iterable[FuelRecord]) -> str:
    """§9d.4: the digest of everything the result is a function of; equal digests mean an equal result. The lead
    unit keys it as v1 did; above one unit, `generator_asset_ids` (declared order) and every unit's declared values
    are added (D-DD.117), so a one-unit digest is unchanged."""
    lead = units[0]
    body = {
        "parameter_version": PARAMETER_VERSION, "night_date": night_date.isoformat(),
        "window": [iso(start), iso(end)], "tank_asset_id": str(tank_asset_id),
        "generator_asset_id": str(lead.asset_id), "accuracy": _declared(accuracy, True),
        "sfc": _declared(lead.sfc, False), "no_load": _declared(lead.no_load, True),
        "evidence_ids": sorted(str(i) for i in evidence_ids),
        "records": sorted([r.root_id, r.head_id, iso(r.recorded_at)] for r in records)}
    if len(units) > 1:
        body["generator_asset_ids"] = [str(u.asset_id) for u in units]
        body["unit_declared"] = [[_declared(u.sfc, False), _declared(u.no_load, True)] for u in units]
    return sha256_canonical(body)
