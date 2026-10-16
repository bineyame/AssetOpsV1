"""S6-02a reserve-trial verification rules: pure, exact, no database.

Version-1 conventions (`D-2026-10-16-s602-questions`, S6-02a Q1/Q2):

* Each window is exactly twelve half-open UTC slots ``[t, t+5 min)`` aligned to
  UTC five-minute boundaries.
* Power energy comes only from interval-valued (``INTERVAL_MEAN``) readings that
  cover a slot whole or exactly partition it; ``kWh = kW * seconds / 3600``.
  Point readings alone establish no energy. Gaps, conflicting overlaps, readings
  crossing a slot boundary and invalid values make the slot UNKNOWN.
* SOC needs an accepted sample at every slot start and at the window end; no
  sample is carried across a boundary. The reserve guardrail is a five-minute
  sampled count (300 s per slot whose start SOC is below its start reserve),
  never continuous physical SOC proof.
* Comparability bands are frozen: feeder-demand and PV-available energy within
  10 % inclusive (zero baseline requires zero later), initial SOC within two
  points inclusive. All comparisons use exact rationals.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any, Iterable

PLAN_VERSION = "reserve-trial-verification-1"
SLOT = timedelta(minutes=5)
WINDOW = timedelta(minutes=60)
SLOTS_PER_WINDOW = 12
GUARDRAIL_BASIS = "FIVE_MINUTE_SAMPLED"
POWER_SEMANTICS = "INTERVAL_MEAN"

BANDS_V1: dict[str, Any] = {
    "feeder_demand_energy_relative": Fraction(1, 10),
    "pv_available_energy_relative": Fraction(1, 10),
    "initial_soc_points": Fraction(2),
    "target_ratio": (3, 4),
}

INTERVAL_MEAN = "INTERVAL_MEAN"
STATE_AT_INSTANT = "STATE_AT_INSTANT"
#: Only GOOD is acceptable (contracts READING_QUALITIES / V3_QUALITIES also
#: carry STALE, SUSPECT and UNAVAILABLE, none of which is accepted evidence).
ACCEPTED_QUALITY = "GOOD"
POWER_UNIT = "kW"
SOC_UNIT = "%"

NECESSARY = "NECESSARY"
CANDIDATE = "CANDIDATE_AVOIDABLE"
INDETERMINATE = "INDETERMINATE"

_US = timedelta(microseconds=1)
_US_PER_HOUR = 3_600_000_000


# --------------------------------------------------------------------------- exact numbers


def fmt(value: Fraction | int | None) -> str | None:
    """Exact text: a decimal string when terminating, otherwise ``p/q``."""
    if value is None:
        return None
    value = Fraction(value)
    den = value.denominator
    twos = fives = 0
    while den % 2 == 0:
        den //= 2
        twos += 1
    while den % 5 == 0:
        den //= 5
        fives += 1
    if den != 1:
        return f"{value.numerator}/{value.denominator}"
    places = max(twos, fives)
    if places == 0:
        return str(value.numerator)
    scaled = value * 10 ** places
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled.numerator)).rjust(places + 1, "0")
    text = f"{sign}{digits[:-places]}.{digits[-places:]}".rstrip("0").rstrip(".")
    return text


def parse_exact(value: Any) -> Fraction | None:
    """Parse an exact decimal string, ``p/q`` string, int or Fraction; None if not exact/finite."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, Decimal):
        return Fraction(value) if value.is_finite() else None
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if "/" in text:
        try:
            num, den = text.split("/")
            return Fraction(int(num), int(den))
        except (ValueError, ZeroDivisionError):
            return None
    try:
        dec = Decimal(text)
    except InvalidOperation:
        return None
    return Fraction(dec) if dec.is_finite() else None


def bands_payload() -> dict[str, Any]:
    """The frozen version-1 bands as JSON-able exact text."""
    num, den = BANDS_V1["target_ratio"]
    return {
        "plan_version": PLAN_VERSION,
        "feeder_demand_energy_relative": fmt(BANDS_V1["feeder_demand_energy_relative"]),
        "pv_available_energy_relative": fmt(BANDS_V1["pv_available_energy_relative"]),
        "initial_soc_points": fmt(BANDS_V1["initial_soc_points"]),
        "target_ratio": {"later": num, "baseline": den,
                         "rule": f"{den} * later_seconds <= {num} * baseline_seconds"},
        "inclusive": True,
        "zero_baseline_rule": "a zero baseline energy total requires a zero later total",
        "slot_seconds": int(SLOT.total_seconds()),
        "slots_per_window": SLOTS_PER_WINDOW,
        "power_semantics": POWER_SEMANTICS,
        "guardrail_basis": GUARDRAIL_BASIS,
    }


def _iso(instant: datetime | None) -> str | None:
    if instant is None:
        return None
    # D-2026-10-16-s602a-cutoff (F7): ISO 8601 UTC with `+00:00`; value and precision retained.
    return instant.astimezone(timezone.utc).isoformat()


def _parse_time(text: Any) -> datetime | None:
    if isinstance(text, datetime):
        return text
    if not isinstance(text, str):
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _aware(instant: Any) -> bool:
    return isinstance(instant, datetime) and instant.tzinfo is not None and instant.utcoffset() is not None


# --------------------------------------------------------------------------- windows


def window_problem(start: datetime, end: datetime) -> str | None:
    """Why ``[start, end)`` is not a valid version-1 window, or None."""
    if not _aware(start) or not _aware(end):
        return "the window bounds must be timezone-aware UTC instants"
    if start.utcoffset() != timedelta(0) or end.utcoffset() != timedelta(0):
        return "the window bounds must be expressed in UTC"
    if end - start != WINDOW:
        return "the window must be exactly 60 minutes"
    if start.second or start.microsecond or start.minute % 5:
        return "the window must start on a UTC five-minute boundary"
    return None


def slot_starts(start: datetime) -> list[datetime]:
    return [start + SLOT * i for i in range(SLOTS_PER_WINDOW)]


@dataclass(frozen=True)
class Reading:
    id: str
    role: str
    asset_id: str
    measurement: str
    source_time: datetime | None
    interval_start: datetime | None
    interval_end: datetime | None
    value_text: str | None
    unit: str | None
    quality: str


@dataclass(frozen=True)
class ReserveValue:
    value: Fraction
    valid_from: datetime
    valid_to: datetime | None
    foundation_revision_id: str


def _problem(code: str, detail: str, **where: Any) -> dict[str, Any]:
    out = {"code": code, "detail": detail}
    out.update({k: v for k, v in where.items()})
    return out


def _value(reading: Reading, *, unit: str, lo: Fraction | None = Fraction(0),
           hi: Fraction | None = None) -> tuple[Fraction | None, dict | None]:
    if reading.unit != unit:
        return None, _problem("INVALID_UNIT", f"reading {reading.id} is in {reading.unit!r}, not {unit!r}",
                              reading_id=reading.id)
    value = parse_exact(reading.value_text) if isinstance(reading.value_text, str) else None
    if value is None or "/" in (reading.value_text or ""):
        return None, _problem("INVALID_VALUE", f"reading {reading.id} has no finite decimal value",
                              reading_id=reading.id)
    if (lo is not None and value < lo) or (hi is not None and value > hi):
        return None, _problem("INVALID_VALUE", f"reading {reading.id} value {reading.value_text} is out of range",
                              reading_id=reading.id)
    return value, None


# --------------------------------------------------------------------------- power coverage


def _power_slot(slot_start: datetime, readings: Iterable[Reading]) -> tuple[dict[str, Any], Fraction | None]:
    slot_end = slot_start + SLOT
    problems: list[dict] = []
    ids: set[str] = set()
    pieces: dict[tuple[datetime, datetime, str], list[str]] = {}
    saw_point = False
    for r in readings:
        if r.measurement != INTERVAL_MEAN:
            if r.measurement == STATE_AT_INSTANT and _aware(r.source_time) and slot_start <= r.source_time < slot_end:
                saw_point = True
            continue
        if not (_aware(r.interval_start) and _aware(r.interval_end)) or r.interval_end <= r.interval_start:
            anchor = r.interval_start if _aware(r.interval_start) else r.source_time
            if _aware(anchor) and slot_start <= anchor < slot_end:
                ids.add(r.id)
                problems.append(_problem("INVALID_SPAN", f"reading {r.id} has no valid interval", reading_id=r.id))
            continue
        if not (r.interval_start < slot_end and slot_start < r.interval_end):
            continue  # outside this slot
        ids.add(r.id)
        if r.interval_start < slot_start or r.interval_end > slot_end:
            problems.append(_problem("SPANS_SLOT_BOUNDARY",
                                     f"reading {r.id} crosses a slot boundary; values are not clipped",
                                     reading_id=r.id))
            continue
        if r.quality != ACCEPTED_QUALITY:
            problems.append(_problem("NOT_ACCEPTED", f"reading {r.id} has quality {r.quality}", reading_id=r.id))
            continue
        value, bad = _value(r, unit=POWER_UNIT)
        if bad:
            problems.append(bad)
            continue
        pieces.setdefault((r.interval_start, r.interval_end, r.value_text), []).append(r.id)

    kwh: Fraction | None = None
    if not problems:
        ordered = sorted(pieces)
        if not ordered:
            if saw_point:
                problems.append(_problem("POINT_ONLY", "point readings alone establish no slot energy"))
            else:
                problems.append(_problem("GAP", "no interval reading covers the slot"))
        else:
            cursor = slot_start
            total = Fraction(0)
            for span_start, span_end, text in ordered:
                if span_start < cursor:
                    problems.append(_problem("CONFLICT", "interval readings overlap within the slot",
                                             reading_ids=sorted(pieces[(span_start, span_end, text)])))
                    break
                if span_start > cursor:
                    problems.append(_problem("GAP", f"no reading covers {_iso(cursor)} to {_iso(span_start)}"))
                    break
                total += parse_exact(text) * Fraction((span_end - span_start) // _US, _US_PER_HOUR)
                cursor = span_end
            if not problems and cursor != slot_end:
                problems.append(_problem("GAP", f"no reading covers {_iso(cursor)} to {_iso(slot_end)}"))
            if not problems:
                kwh = total
    payload = {"slot_start": _iso(slot_start), "slot_end": _iso(slot_end),
               "state": "COVERED" if kwh is not None else "UNKNOWN", "kwh": fmt(kwh),
               "evidence_ids": sorted(ids), "problems": problems}
    return payload, kwh


def power_slot(slot_start: datetime, readings: Iterable[Reading]) -> dict[str, Any]:
    """Coverage and exact kWh of one power role/asset over ``[slot_start, slot_start+5 min)``."""
    return _power_slot(slot_start, readings)[0]


# --------------------------------------------------------------------------- instant samples


def _instant(at: datetime, readings: Iterable[Reading], *, numeric: bool,
             unit: str | None = None) -> tuple[dict[str, Any], Any]:
    problems: list[dict] = []
    ids: set[str] = set()
    values: dict[Any, list[str]] = {}
    for r in readings:
        if r.measurement != STATE_AT_INSTANT or not _aware(r.source_time) or r.source_time != at:
            continue
        ids.add(r.id)
        if r.quality != ACCEPTED_QUALITY:
            problems.append(_problem("NOT_ACCEPTED", f"reading {r.id} has quality {r.quality}", reading_id=r.id))
            continue
        if numeric:
            value, bad = _value(r, unit=unit or SOC_UNIT, lo=Fraction(0), hi=Fraction(100))
            if bad:
                problems.append(bad)
                continue
        else:
            if not isinstance(r.value_text, str) or not r.value_text:
                problems.append(_problem("INVALID_VALUE", f"reading {r.id} has no state", reading_id=r.id))
                continue
            value = r.value_text
        values.setdefault(value, []).append(r.id)
    result = None
    if not problems:
        if not values:
            problems.append(_problem("MISSING_SAMPLE", f"no accepted sample at {_iso(at)}"))
        elif len(values) > 1:
            problems.append(_problem("CONFLICT", f"different values at {_iso(at)}"))
        else:
            result = next(iter(values))
    text = fmt(result) if numeric else result
    payload = {"at": _iso(at), "state": "KNOWN" if result is not None else "UNKNOWN", "value": text,
               "evidence_ids": sorted(ids), "problems": problems}
    return payload, result


def soc_samples(starts: list[datetime], window_end: datetime,
                readings: Iterable[Reading]) -> list[dict[str, Any]]:
    """Accepted battery SOC exactly at each slot start and at the window end (last item)."""
    readings = list(readings)
    return [_instant(at, readings, numeric=True)[0] for at in [*starts, window_end]]


# --------------------------------------------------------------------------- reserve


def _reserve_at(t: datetime, reserves: Iterable[ReserveValue]) -> tuple[dict[str, Any], Fraction | None]:
    end = t + SLOT
    reserves = list(reserves)
    problems: list[dict] = []
    changed = [r for r in reserves
               if t < r.valid_from < end or (r.valid_to is not None and t < r.valid_to < end)]
    effective = [r for r in reserves if r.valid_from <= t and (r.valid_to is None or t < r.valid_to)]
    state, value, rev = "UNKNOWN", None, None
    if changed:
        state = "UNASSESSABLE"
        problems.append(_problem("RESERVE_CHANGED_IN_SLOT", "a reserve value changes inside the slot",
                                 foundation_revision_ids=sorted({str(r.foundation_revision_id) for r in changed})))
    elif not effective:
        problems.append(_problem("NO_EFFECTIVE_RESERVE", f"no reserve is effective at {_iso(t)}"))
    elif len({r.value for r in effective}) > 1:
        problems.append(_problem("CONFLICT", f"different reserves are effective at {_iso(t)}"))
    else:
        state, value, rev = "KNOWN", effective[0].value, str(effective[0].foundation_revision_id)
    return ({"slot_start": _iso(t), "state": state, "value": fmt(value), "foundation_revision_id": rev,
             "problems": problems}, value)


def reserve_at_slots(starts: list[datetime], reserves: Iterable[ReserveValue]) -> list[dict[str, Any]]:
    reserves = list(reserves)
    return [_reserve_at(t, reserves)[0] for t in starts]


# --------------------------------------------------------------------------- window evidence

_SINGLE_POWER_ROLES = ("generator_power", "pcs_discharge_capability", "pv_available_power")


def _by_role_asset(readings: list[Reading], role: str, asset_id: str | None) -> list[Reading]:
    return [r for r in readings if r.role == role and (asset_id is None or r.asset_id == asset_id)]


def window_evidence(start: datetime, readings: Iterable[Reading], *, load_asset_ids: list[str],
                    critical_load_asset_id: str | None, reserves: Iterable[ReserveValue],
                    battery_asset_id: str | None = None,
                    role_assets: dict[str, list[str]] | None = None) -> dict[str, Any]:
    """Per-slot coverage and exact window totals for one 60-minute verification window.

    F6: `battery_asset_id` keeps only the plan's battery for SOC, and `role_assets` (role -> bound asset IDs) keeps
    only bound assets for the single-asset roles; a reading of any other asset is ignored, never mixed in."""
    end = start + WINDOW
    bad_window = window_problem(start, end)
    if bad_window:
        raise ValueError(bad_window)
    allowed: dict[str, set[str]] = {role: {str(a) for a in ids} for role, ids in (role_assets or {}).items()
                                    if role in (*_SINGLE_POWER_ROLES, "generator_state")}
    if battery_asset_id is not None:
        allowed["battery_soc"] = {str(battery_asset_id)}
    readings = [r for r in readings if r.role not in allowed or r.asset_id in allowed[r.role]]
    reserves = list(reserves)
    starts = slot_starts(start)
    problems: list[dict] = []
    evidence: set[str] = set()

    def note(role: str, asset: str | None, slot: datetime | None, items: list[dict]) -> None:
        for p in items:
            problems.append({"role": role, "asset_id": asset, "slot_start": _iso(slot), **p})

    single_assets: dict[str, str | None] = {}
    for role in (*_SINGLE_POWER_ROLES, "generator_state", "battery_soc"):
        assets = sorted({r.asset_id for r in readings if r.role == role})
        if len(assets) > 1:
            single_assets[role] = None
            note(role, None, None, [_problem("AMBIGUOUS_BINDING", f"{role} is reported by {len(assets)} assets")])
        else:
            single_assets[role] = assets[0] if assets else ""

    def power(role: str, asset: str | None, t: datetime) -> tuple[dict, Fraction | None]:
        if asset is None:
            payload = {"slot_start": _iso(t), "slot_end": _iso(t + SLOT), "state": "UNKNOWN", "kwh": None,
                       "evidence_ids": [], "problems": [_problem("MISSING_BINDING", f"{role} has no bound asset")]}
            note(role, None, t, payload["problems"])
            return payload, None
        payload, kwh = _power_slot(t, _by_role_asset(readings, role, asset or None))
        evidence.update(payload["evidence_ids"])
        note(role, asset or None, t, payload["problems"])
        return payload, kwh

    loads = list(load_asset_ids)
    if not loads:
        note("feeder_demand", None, None, [_problem("MISSING_BINDING", "no load asset is bound")])
    soc_readings = _by_role_asset(readings, "battery_soc", None)
    state_readings = _by_role_asset(readings, "generator_state", None)

    slots: list[dict] = []
    feeder_total: Fraction | None = Fraction(0) if loads else None
    pv_total: Fraction | None = Fraction(0)
    unserved_total: Fraction | None = Fraction(0)
    below_total: int | None = 0
    slot_complete = True
    for t in starts:
        row: dict[str, Any] = {"slot_start": _iso(t), "slot_end": _iso(t + SLOT)}
        known = True
        for role in _SINGLE_POWER_ROLES:
            asset = single_assets[role]
            row[role], kwh = power(role, asset, t)
            known &= kwh is not None
            if role == "pv_available_power":
                pv_total = None if kwh is None or pv_total is None else pv_total + kwh
        feeder: dict[str, dict] = {}
        slot_feeder: Fraction | None = Fraction(0) if loads else None
        for asset in loads:
            feeder[asset], kwh = power("feeder_demand", asset, t)
            slot_feeder = None if kwh is None or slot_feeder is None else slot_feeder + kwh
        row["feeder_demand"] = feeder
        row["feeder_demand_kwh"] = fmt(slot_feeder)
        known &= slot_feeder is not None
        feeder_total = None if slot_feeder is None or feeder_total is None else feeder_total + slot_feeder

        crit = critical_load_asset_id
        row["critical_load_requested_power"], req = power("critical_load_requested_power", crit, t)
        row["critical_load_delivered_power"], dlv = power("critical_load_delivered_power", crit, t)
        unserved: Fraction | None = None
        if req is not None and dlv is not None:
            if dlv > req:
                note("critical_load_delivered_power", crit, t,
                     [_problem("DELIVERED_EXCEEDS_REQUESTED", "delivered critical energy exceeds requested")])
            else:
                unserved = req - dlv
        row["unserved_critical_kwh"] = fmt(unserved)
        known &= unserved is not None
        unserved_total = None if unserved is None or unserved_total is None else unserved_total + unserved

        if single_assets["generator_state"] is None:
            gen = {"at": _iso(t), "state": "UNKNOWN", "value": None, "evidence_ids": [], "problems": []}
            gen_value = None
        else:
            gen, gen_value = _instant(t, state_readings, numeric=False)
            note("generator_state", single_assets["generator_state"] or None, t, gen["problems"])
        evidence.update(gen["evidence_ids"])
        row["generator_state"] = gen
        known &= gen_value is not None

        if single_assets["battery_soc"] is None:
            soc, soc_value = {"at": _iso(t), "state": "UNKNOWN", "value": None, "evidence_ids": [],
                              "problems": []}, None
        else:
            soc, soc_value = _instant(t, soc_readings, numeric=True)
            note("battery_soc", single_assets["battery_soc"] or None, t, soc["problems"])
        evidence.update(soc["evidence_ids"])
        row["soc_start"] = soc

        reserve, reserve_value = _reserve_at(t, reserves)
        note("battery_reserve", None, t, reserve["problems"])
        row["reserve"] = reserve
        below: int | None = None
        if soc_value is not None and reserve_value is not None:
            below = int(SLOT.total_seconds()) if soc_value < reserve_value else 0
        row["below_reserve_seconds"] = below
        known &= below is not None
        below_total = None if below is None or below_total is None else below_total + below
        row["complete"] = known
        slot_complete &= known
        slots.append(row)

    if single_assets["battery_soc"] is None:
        terminal, terminal_value = {"at": _iso(end), "state": "UNKNOWN", "value": None, "evidence_ids": [],
                                    "problems": []}, None
    else:
        terminal, terminal_value = _instant(end, soc_readings, numeric=True)
        note("battery_soc", single_assets["battery_soc"] or None, end, terminal["problems"])
    evidence.update(terminal["evidence_ids"])
    initial = slots[0]["soc_start"]["value"]
    complete = (slot_complete and terminal_value is not None and feeder_total is not None
                and pv_total is not None and unserved_total is not None and below_total is not None)
    return {
        "plan_version": PLAN_VERSION,
        "window_start": _iso(start),
        "window_end": _iso(end),
        "slot_seconds": int(SLOT.total_seconds()),
        "power_semantics": POWER_SEMANTICS,
        "guardrail_basis": GUARDRAIL_BASIS,
        "guardrail_label": "five-minute sampled guardrail, not continuous physical SOC proof",
        "load_asset_ids": loads,
        "critical_load_asset_id": critical_load_asset_id,
        "slots": slots,
        "terminal_soc_sample": terminal,
        "feeder_demand_kwh": fmt(feeder_total),
        "pv_available_kwh": fmt(pv_total),
        "unserved_critical_kwh": fmt(unserved_total),
        "below_reserve_seconds": below_total,
        "initial_soc": initial,
        "terminal_soc": fmt(terminal_value),
        "complete": complete,
        "problems": problems,
        "evidence_ids": sorted(evidence),
    }


# --------------------------------------------------------------------------- comparability


def _relative_band(name: str, base: Fraction | None, later: Fraction | None, rel: Fraction) -> dict[str, Any]:
    out: dict[str, Any] = {"metric": name, "unit": "kWh", "baseline": fmt(base), "later": fmt(later),
                           "relative_band": fmt(rel), "inclusive": True}
    if base is None or later is None or base < 0 or later < 0:
        out.update(state="UNKNOWN", threshold=None, difference=None,
                   reason="missing, negative or non-exact input")
        return out
    threshold = base * rel
    diff = abs(later - base)
    if base == 0:
        state = "PASS" if later == 0 else "FAIL"
        reason = "zero baseline requires zero later total"
    else:
        state = "PASS" if diff <= threshold else "FAIL"
        reason = "|later - baseline| <= baseline * band"
    out.update(state=state, threshold=fmt(threshold), difference=fmt(diff), reason=reason)
    return out


def comparability(baseline: dict[str, Any], later: dict[str, Any]) -> dict[str, Any]:
    """Frozen version-1 comparability of two window evidence payloads (exact)."""
    def get(d: dict, key: str) -> Fraction | None:
        return parse_exact(d.get(key))

    checks = [
        _relative_band("feeder_demand_energy", get(baseline, "feeder_demand_kwh"), get(later, "feeder_demand_kwh"),
                       BANDS_V1["feeder_demand_energy_relative"]),
        _relative_band("pv_available_energy", get(baseline, "pv_available_kwh"), get(later, "pv_available_kwh"),
                       BANDS_V1["pv_available_energy_relative"]),
    ]
    b_soc, l_soc = get(baseline, "initial_soc"), get(later, "initial_soc")
    points = BANDS_V1["initial_soc_points"]
    soc: dict[str, Any] = {"metric": "initial_soc", "unit": "%", "baseline": fmt(b_soc), "later": fmt(l_soc),
                           "threshold": fmt(points), "inclusive": True}
    if b_soc is None or l_soc is None:
        soc.update(state="UNKNOWN", difference=None, reason="missing initial SOC")
    else:
        diff = abs(l_soc - b_soc)
        soc.update(state="PASS" if diff <= points else "FAIL", difference=fmt(diff),
                   reason="|later - baseline| <= points")
    checks.append(soc)
    states = {c["state"] for c in checks}
    overall = "UNKNOWN" if "UNKNOWN" in states else ("FAIL" if "FAIL" in states else "PASS")
    return {"state": overall, "checks": checks, "bands": bands_payload()}


# --------------------------------------------------------------------------- target


def target_days(start: datetime) -> list[date]:
    """UTC days whose selected dispatch-3 revisions can hold time in the window."""
    start = start.astimezone(timezone.utc)
    last = (start + WINDOW - _US).astimezone(timezone.utc)
    days = {start.date() - timedelta(days=1), start.date(), last.date()}
    return sorted(days)


def _seconds(td: timedelta) -> int:
    return td // timedelta(seconds=1)


def target_window(start: datetime, interval_results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Candidate-avoidable generator seconds inside ``[start, start+60 min)`` from S3 interval results."""
    end = start + WINDOW
    reasons: list[str] = []
    contributing: set[str] = set()
    seen: dict[tuple[Any, Any], Any] = {}
    candidate = 0
    inconclusive = False
    for item in interval_results:
        result = item.get("result") or {}
        rev = str(item.get("assessment_revision_id"))
        key = (result.get("generator_asset_id"), (result.get("interval") or {}).get("first_on"))
        segs = result.get("segments") or []
        if key in seen:
            if seen[key] != segs:
                inconclusive = True
                reasons.append(f"CONFLICTING_INTERVAL: {key[0]} at {key[1]} differs between revisions")
            continue
        seen[key] = segs
        open_bound = any(isinstance(x, str) and x.startswith("OPEN_BOUND") for x in result.get("limitations") or [])
        for seg in segs:
            s, e = _parse_time(seg.get("start")), _parse_time(seg.get("end"))
            if s is None or e is None:
                inconclusive = True
                reasons.append(f"INVALID_SEGMENT: revision {rev} has an unreadable segment")
                continue
            lo, hi = max(s, start), min(e, end)
            if hi <= lo:
                continue
            contributing.add(rev)
            cls = seg.get("classification")
            if open_bound:
                inconclusive = True
                reasons.append(f"OPEN_BOUND: interval {key[1]} of {key[0]} has an open bound and time in the window")
            if cls == INDETERMINATE:
                inconclusive = True
                reasons.append(f"INDETERMINATE: segment {_iso(lo)} to {_iso(hi)} intersects the window")
            elif cls == CANDIDATE:
                candidate += _seconds(hi - lo)
            elif cls != NECESSARY:
                inconclusive = True
                reasons.append(f"UNKNOWN_CLASSIFICATION: {cls!r}")
    return {"window_start": _iso(start), "window_end": _iso(end),
            "state": "INCONCLUSIVE" if inconclusive else "KNOWN",
            "candidate_seconds": None if inconclusive else candidate,
            "reasons": sorted(set(reasons)), "assessment_revision_ids": sorted(contributing)}


def target_met(baseline_seconds: int | None, later_seconds: int | None) -> bool | None:
    """Version-1 target: ``4 * later <= 3 * baseline``; None when either is unknown."""
    if baseline_seconds is None or later_seconds is None:
        return None
    num, den = BANDS_V1["target_ratio"]
    return den * later_seconds <= num * baseline_seconds


# --------------------------------------------------------------------------- verdict (phase 2)

VERIFIED, INEFFECTIVE, INCONCLUSIVE = "VERIFIED", "INEFFECTIVE", "INCONCLUSIVE"
GUARDRAIL_FAIL = "GUARDRAIL_FAIL"
TARGET_MISS = "TARGET_MISS"
POSITIVE_SOURCE_CLASSES = ("REGISTERED_SIMULATION", "AUTHORED_DEMONSTRATION")


def _metric(key: str, window: str, state: str, *, value: Any = None, threshold: str | None = None,
            unit: str | None = None, reason: str | None = None, evidence_ids: Iterable[str] = ()) -> dict[str, Any]:
    if isinstance(value, (Fraction, int)) and not isinstance(value, bool):
        value = fmt(value)
    return {"metric_key": key, "window_name": window, "state": state,
            "value_text": None if value is None else str(value), "threshold_text": threshold, "unit": unit,
            "reason": reason, "evidence_ids": sorted(set(evidence_ids))}


def _fixtures(res: dict[str, Any]) -> list[tuple[str, Any]]:
    return sorted((f["fixture_id"], f["fixture_version"]) for f in res.get("fixtures") or [])


def _run_digests(res: dict[str, Any]) -> set[str]:
    return {r["run_identity_sha256"] for r in res.get("runs") or []}


def source_pair(baseline: dict[str, Any] | None, later: dict[str, Any] | None) -> dict[str, Any]:
    """Per-window S4-05 source resolutions (never their union) judged as a pair for a labelled demo verdict.

    PASS needs each window to resolve to one coherent REGISTERED_SIMULATION or AUTHORED_DEMONSTRATION set, the same
    class in both, the same authored fixture lineage (authored) or two distinct run identity digests (registered).
    Anything else - MIXED, UNKNOWN, a crossed class, a shared run, a missing resolution - is UNKNOWN."""
    problems: list[str] = []
    for name, res in (("baseline", baseline), ("later", later)):
        if res is None:
            problems.append(f"{name}: no source resolution")
        elif res.get("state") not in POSITIVE_SOURCE_CLASSES:
            problems.append(f"{name}: source resolves {res.get('state')} {sorted(res.get('reasons') or [])}")
    if not problems:
        assert baseline is not None and later is not None
        if baseline["state"] != later["state"]:
            problems.append(f"crossed source classes: {baseline['state']} then {later['state']}")
        elif baseline["state"] == "AUTHORED_DEMONSTRATION":
            if not _fixtures(baseline) or _fixtures(baseline) != _fixtures(later):
                problems.append("authored fixture lineage differs between windows")
        else:
            b_runs, l_runs = _run_digests(baseline), _run_digests(later)
            if len(b_runs) != 1 or len(l_runs) != 1:
                problems.append("each window needs exactly one registered run")
            elif b_runs == l_runs:
                problems.append("both windows come from one registered run; two distinct runs are required")
    return {"state": "UNKNOWN" if problems else "PASS", "problems": problems,
            "source_class": None if problems else baseline["state"],  # type: ignore[index]
            "statement": ("Simulated or authored policy trial evidence; no real-source verdict before a separate "
                          "real attestation.")}


def decide(*, baseline: dict[str, Any], later: dict[str, Any], comparable: dict[str, Any],
           baseline_seconds: int | None, later_target: dict[str, Any] | None, source: dict[str, Any],
           blockers: Iterable[str] = ()) -> dict[str, Any]:
    """The version-1 verdict over two window evidence payloads (exact): outcome, reasons and metrics.

    VERIFIED: target and every guardrail pass on a complete, comparable, source-coherent pair. INEFFECTIVE: on a
    fully assessable pair, a target miss and/or a measured guardrail failure (`GUARDRAIL_FAIL` only for the latter).
    INCONCLUSIVE: any unknown required fact (coverage, comparability, target, guardrail, source, `blockers`), even
    with a known failure, which stays in the reasons as `KNOWN_FAILURE:<metric>`."""
    metrics: list[dict[str, Any]] = []
    unknown: list[str] = [f"BLOCKED:{b}" for b in blockers]
    for name, w in (("BASELINE", baseline), ("LATER", later)):
        complete = bool(w.get("complete"))
        covered = sum(1 for s in w.get("slots", []) if s.get("complete"))
        metrics.append(_metric("window_coverage", name, "PASS" if complete else "UNKNOWN",
                               value=f"{covered}/{SLOTS_PER_WINDOW}",
                               reason="every slot and role covered" if complete else
                               f"{len(w.get('problems') or [])} coverage problem(s)",
                               evidence_ids=w.get("evidence_ids") or []))
        if not complete:
            unknown.append(f"INCOMPLETE_{name}_WINDOW")
    for check in comparable.get("checks", []):
        metrics.append(_metric(f"{check['metric']}_band", "COMPARISON", check["state"],
                               value=check.get("difference"), threshold=check.get("threshold"),
                               unit=check.get("unit"), reason=check.get("reason")))
    if comparable.get("state") == "UNKNOWN" or not comparable.get("checks"):
        unknown.append("COMPARABILITY_UNKNOWN")
    elif comparable.get("state") == "FAIL":
        unknown.append("NOT_COMPARABLE")
    metrics.append(_metric("source_provenance", "COMPARISON", source["state"], value=source.get("source_class"),
                           reason="; ".join(source.get("problems") or []) or "coherent per-window source pair"))
    if source["state"] != "PASS":
        unknown.append("SOURCE_NOT_COHERENT")

    known = later_target is not None and later_target.get("state") == "KNOWN"
    later_seconds = later_target.get("candidate_seconds") if known else None  # type: ignore[union-attr]
    met = target_met(baseline_seconds, later_seconds) if baseline_seconds else None
    metrics.append(_metric("candidate_avoidable_seconds", "BASELINE", "PASS" if baseline_seconds else "UNKNOWN",
                           value=baseline_seconds, unit="s"))
    metrics.append(_metric("candidate_avoidable_seconds", "LATER", "UNKNOWN" if later_seconds is None else "PASS",
                           value=later_seconds, unit="s",
                           reason=None if later_target is None else
                           ("; ".join(later_target.get("reasons") or []) or later_target.get("state"))))
    metrics.append(_metric("target_reduction", "COMPARISON", {True: "PASS", False: "FAIL", None: "UNKNOWN"}[met],
                           threshold="4 * later_seconds <= 3 * baseline_seconds", unit="s"))
    if met is None:
        unknown.append("TARGET_UNKNOWN")

    b_un, l_un = parse_exact(baseline.get("unserved_critical_kwh")), parse_exact(later.get("unserved_critical_kwh"))
    unserved = "UNKNOWN" if b_un is None or l_un is None else ("PASS" if l_un <= b_un else "FAIL")
    metrics.append(_metric("unserved_critical_energy", "COMPARISON", unserved, value=l_un, threshold=fmt(b_un),
                           unit="kWh", reason="later_kwh <= baseline_kwh"))
    b_br, l_br = baseline.get("below_reserve_seconds"), later.get("below_reserve_seconds")
    below = "UNKNOWN" if b_br is None or l_br is None else ("PASS" if l_br == 0 and l_br <= b_br else "FAIL")
    metrics.append(_metric("below_reserve_seconds", "COMPARISON", below, value=l_br, threshold="0 and <= baseline",
                           unit="s", reason=f"{GUARDRAIL_BASIS}: five-minute sampled guardrail, not continuous "
                                            "physical SOC proof"))
    b_t, l_t = parse_exact(baseline.get("terminal_soc")), parse_exact(later.get("terminal_soc"))
    terminal = "UNKNOWN" if b_t is None or l_t is None else ("PASS" if l_t >= b_t else "FAIL")
    metrics.append(_metric("terminal_soc", "COMPARISON", terminal, value=l_t, threshold=fmt(b_t), unit="%",
                           reason="later_terminal_soc >= baseline_terminal_soc"))
    guardrails = {"unserved_critical_energy": unserved, "below_reserve_seconds": below, "terminal_soc": terminal}
    unknown += [f"GUARDRAIL_UNKNOWN:{k}" for k, v in guardrails.items() if v == "UNKNOWN"]
    failed = [k for k, v in guardrails.items() if v == "FAIL"]

    known_failures = [f"KNOWN_FAILURE:{k}" for k in failed] + (["KNOWN_FAILURE:target_reduction"] if met is False else [])
    if unknown:
        outcome, reasons = INCONCLUSIVE, sorted(set(unknown)) + known_failures
    elif failed:
        outcome = INEFFECTIVE
        reasons = [GUARDRAIL_FAIL] + [f"GUARDRAIL:{k}" for k in failed] + ([TARGET_MISS] if met is False else [])
    elif met is False:
        outcome, reasons = INEFFECTIVE, [TARGET_MISS]
    else:
        outcome, reasons = VERIFIED, ["TARGET_AND_GUARDRAILS_PASS"]
    return {"outcome": outcome, "reasons": reasons, "metrics": metrics, "guardrail_failed": failed,
            "target_met": met}
