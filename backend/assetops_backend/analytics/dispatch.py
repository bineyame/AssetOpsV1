"""The dispatch analytic: reconstruct generator intervals and classify them (T028).

Decision table: `backend/tests/dispatch_decision_table.md` (written before this
module, and the authority for every rule here). Inputs are accepted records
and one Foundation property (the generator's specific fuel consumption, the
stated basis of the indicative fuel quantity). Nothing here reads a run, a
scenario, a stage, a LabProjection, a world or a private trace (AC14), and
observed PV output never stands in for available PV capability (AC3).

`assess(records, fuel)` is pure: the same records and model version give the
same payload, which is what makes a rerun produce no new revision (AC13).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from typing import Any, Iterable, Sequence

from assetops_backend.evidence.models import AcceptedRecord

ANALYTIC_ID = "dispatch"
MODEL_VERSION = "dispatch-1"
FINDING_TYPE = "generator-dispatch-interval"

NECESSARY = "NECESSARY"
CANDIDATE = "CANDIDATE_AVOIDABLE"
INDETERMINATE = "INDETERMINATE"
CLAIM_LABELS = {
    NECESSARY: "Necessary",
    CANDIDATE: "Candidate avoidable",
    INDETERMINATE: "Indeterminate",
}
#: Claim levels a Finding is raised for (decision table "Interval classification").
FINDING_CLAIM_LEVELS = (CANDIDATE, INDETERMINATE)

# --- model dispatch-1 thresholds (decision table) ---------------------------
CONTINUITY_TOLERANCE_S = 20 * 60
INSTANT_TOLERANCE_S = 10 * 60
CAPABILITY_HEADROOM = Fraction(1, 10)
SOC_HEADROOM_POINTS = 10
STRONG_MARGIN = Fraction(1, 4)
TRANSITION_LIMIT_S = 15 * 60
SFC_UNCERTAINTY = Fraction(1, 10)

THRESHOLDS: tuple[dict[str, str], ...] = (
    {"id": "continuity-tolerance", "value": "20", "unit": "min",
     "meaning": "Longest spacing between generator-state observations treated as continuous."},
    {"id": "instant-tolerance", "value": "10", "unit": "min",
     "meaning": "How far before a segment's end an instant (SOC) may be and still describe it."},
    {"id": "capability-headroom", "value": "10", "unit": "% of load",
     "meaning": "PV available plus battery support must exceed load by this for a candidate."},
    {"id": "soc-headroom", "value": "10", "unit": "SOC points above reserve",
     "meaning": "Battery support counts only when SOC exceeds the effective reserve by this."},
    {"id": "strong-margin", "value": "25", "unit": "% of load",
     "meaning": "Smallest candidate margin below this lowers confidence one level."},
    {"id": "transition-limit", "value": "15", "unit": "min",
     "meaning": "Start/stop time uncertainty above this lowers confidence one level."},
    {"id": "fuel-consumption-uncertainty", "value": "10", "unit": "%",
     "meaning": "Band applied to the configured specific fuel consumption."},
)

# --- evidence keys -------------------------------------------------------------
Key = tuple[str, str]
GEN_STATUS: Key = ("generator-controller", "status")
GEN_POWER: Key = ("generator-controller", "ac-power")
FEEDERS: tuple[Key, ...] = (
    ("residential-meter", "active-power"),
    ("clinic-meter", "active-power"),
    ("mill-meter", "active-power"),
)
PV_AVAILABLE: Key = ("pv-inverter-controller", "available-power")
SOC: Key = ("battery-pcs-controller", "state-of-charge")
DISCHARGE: Key = ("battery-pcs-controller", "discharge-capability")
POLICY_RESERVE: Key = ("battery-pcs-controller", "policy-reserve-soc")
POLICY_MIN_RUNTIME: Key = ("generator-controller", "policy-minimum-runtime")
POLICY_STOP: Key = ("generator-controller", "policy-stop-soc-threshold")
GEN_OVERRIDE: Key = ("generator-controller", "override-command")
BATTERY_OVERRIDE: Key = ("battery-pcs-controller", "override-command")

INPUT_LABELS: dict[str, str] = {
    "load": "Load (three feeder meters)",
    "pv_available": "PV available power",
    "soc": "Battery state of charge",
    "reserve": "Battery reserve policy",
    "discharge_capability": "Battery discharge capability",
}
REQUIRED_INPUTS = ("load", "pv_available", "soc", "reserve", "discharge_capability")

_FMT = "%Y-%m-%dT%H:%M:%SZ"
ON, OFF, UNOBSERVED = "ON", "OFF", "UNOBSERVED"
RUNNING_STATES = {"RUNNING"}
NOT_RUNNING_STATES = {"STOPPED", "STARTING", "FAILED"}


def _t(text: str) -> int:
    return int(datetime.strptime(text, _FMT).replace(tzinfo=timezone.utc).timestamp())


def _iso(seconds: int) -> str:
    return datetime.fromtimestamp(seconds, tz=timezone.utc).strftime(_FMT)


def _dec(value: Fraction, places: int = 2) -> str:
    exact = Decimal(value.numerator) / Decimal(value.denominator)
    text = str(exact.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))
    return text.rstrip("0").rstrip(".") if "." in text else text


def _hours(seconds: int) -> str:
    return _dec(Fraction(seconds, 3600), 2)


def _detail(record: AcceptedRecord, name: str) -> str | None:
    for key, value in record.record_detail:
        if key == name:
            return value
    return None


def _link(record: AcceptedRecord) -> dict[str, str]:
    return {
        "message_id": record.message_id,
        "device_id": record.device_id,
        "signal_id": record.signal_id,
        "source_time": record.source_time,
    }


@dataclass
class Lookup:
    """One input at one time: a value, or why there is none (never a substitute)."""

    value: Fraction | None
    records: list[AcceptedRecord] = field(default_factory=list)
    problem: str | None = None  # MISSING | CONFLICTING | NOT_GOOD

    @property
    def usable(self) -> bool:
        return self.value is not None


def _good(record: AcceptedRecord) -> bool:
    return record.quality == "GOOD" and record.normalized_value is not None


class _Evidence:
    """Accepted records indexed by (device, signal); lookups by source time."""

    def __init__(self, records: Iterable[AcceptedRecord]) -> None:
        self.by_key: dict[Key, list[AcceptedRecord]] = {}
        for record in records:
            self.by_key.setdefault((record.device_id, record.signal_id), []).append(record)
        for items in self.by_key.values():
            items.sort(key=lambda r: (r.source_time, r.message_id))

    def of(self, key: Key) -> list[AcceptedRecord]:
        return self.by_key.get(key, [])

    def interval_mean(self, key: Key, end: int) -> Lookup:
        """The mean whose interval ends at `end`; distinct records there conflict."""
        at = [r for r in self.of(key) if r.interval_end is not None and _t(r.interval_end) == end]
        good = [r for r in at if _good(r)]
        if not good:
            stated = [r for r in self.of(key) if _t(r.source_time) == end]
            return Lookup(None, stated, "NOT_GOOD" if stated else "MISSING")
        if len(good) > 1:
            return Lookup(None, good, "CONFLICTING")
        return Lookup(Fraction(good[0].normalized_value or "0"), good)

    def instant(self, key: Key, at: int) -> Lookup:
        """The latest GOOD instant in (at - tolerance, at]."""
        near = [
            r for r in self.of(key)
            if at - INSTANT_TOLERANCE_S < _t(r.source_time) <= at and r.interval_start is None
        ]
        good = [r for r in near if _good(r)]
        if not good:
            return Lookup(None, near, "NOT_GOOD" if near else "MISSING")
        latest = max(_t(r.source_time) for r in good)
        chosen = [r for r in good if _t(r.source_time) == latest]
        if len({r.normalized_value for r in chosen}) > 1 or len(chosen) > 1:
            return Lookup(None, chosen, "CONFLICTING")
        try:
            return Lookup(Fraction(chosen[0].normalized_value or ""), chosen)
        except ValueError:
            return Lookup(None, chosen, "NOT_GOOD")

    def effective(self, key: Key, at: int, family: str) -> AcceptedRecord | None:
        """The record of `family` effective at `at` (latest effective start wins)."""
        best: AcceptedRecord | None = None
        best_rank: tuple[int, int] | None = None
        for record in self.of(key):
            if record.family != family or record.normalized_value is None:
                continue
            start = _detail(record, "effective_start") or record.source_time
            end = _detail(record, "effective_end")
            if _t(start) > at or (end is not None and _t(end) <= at):
                continue
            rank = (_t(start), int(_detail(record, "policy_version") or "0"))
            if best_rank is None or rank > best_rank:
                best, best_rank = record, rank
        return best


# --- interval reconstruction (decision table, AC1) ---------------------------


@dataclass
class _State:
    time: int
    state: str
    records: list[AcceptedRecord]


def _states(evidence: _Evidence) -> list[_State]:
    times = sorted(
        {_t(r.source_time) for r in evidence.of(GEN_STATUS)}
        | {_t(r.interval_end) for r in evidence.of(GEN_POWER) if r.interval_end}
    )
    states = []
    for time in times:
        status = [
            r for r in evidence.of(GEN_STATUS) if _t(r.source_time) == time and _good(r)
        ]
        values = {r.normalized_value for r in status}
        if len(values) == 1 and len(status) == 1:
            value = status[0].normalized_value
            if value in RUNNING_STATES:
                states.append(_State(time, ON, status))
                continue
            if value in NOT_RUNNING_STATES:
                states.append(_State(time, OFF, status))
                continue
        power = evidence.interval_mean(GEN_POWER, time)
        if power.usable and not status:
            states.append(_State(time, ON if (power.value or 0) > 0 else OFF, power.records))
        else:
            states.append(_State(time, UNOBSERVED, status or power.records))
    return states


def _off_before(evidence: _Evidence, first_on: int) -> int | None:
    """Latest time the generator is shown not running, at or before `first_on`."""
    candidates = [
        _t(r.source_time) for r in evidence.of(GEN_STATUS)
        if _good(r) and r.normalized_value in NOT_RUNNING_STATES and _t(r.source_time) < first_on
    ] + [
        _t(r.interval_end or "") for r in evidence.of(GEN_POWER)
        if _good(r) and r.interval_end and Fraction(r.normalized_value or "0") == 0
        and _t(r.interval_end) <= first_on
    ]
    return max(candidates) if candidates else None


def _off_after(evidence: _Evidence, last_on: int) -> int | None:
    candidates = [
        _t(r.source_time) for r in evidence.of(GEN_STATUS)
        if _good(r) and r.normalized_value in NOT_RUNNING_STATES and _t(r.source_time) > last_on
    ] + [
        _t(r.interval_start or "") for r in evidence.of(GEN_POWER)
        if _good(r) and r.interval_start and Fraction(r.normalized_value or "0") == 0
        and _t(r.interval_start) >= last_on
    ]
    return min(candidates) if candidates else None


@dataclass
class _Run:
    on_times: list[int]
    unobserved: list[int]
    records: list[AcceptedRecord]


def _runs(states: list[_State]) -> list[_Run]:
    runs: list[_Run] = []
    current: _Run | None = None
    pending_unobserved: list[_State] = []
    for state in states:
        if state.state == ON:
            if current is None:
                current = _Run([], [], [])
            else:
                current.unobserved.extend(s.time for s in pending_unobserved)
                for s in pending_unobserved:
                    current.records.extend(s.records)
            pending_unobserved = []
            current.on_times.append(state.time)
            current.records.extend(state.records)
        elif state.state == UNOBSERVED:
            if current is not None:
                pending_unobserved.append(state)
        else:
            if current is not None:
                runs.append(current)
            current, pending_unobserved = None, []
    if current is not None:
        runs.append(current)
    return runs


# --- segment evaluation (decision table, AC2/AC7) ----------------------------


@dataclass
class _Segment:
    start: int
    end: int
    observed: bool
    classification: str
    binding: str | None
    reasons: list[str]
    missing: list[str]
    inputs: dict[str, str | None]
    records: list[AcceptedRecord]
    margin: Fraction | None = None
    load: Fraction | None = None
    generator_kw: Fraction | None = None

    def payload(self) -> dict[str, Any]:
        return {
            "start": _iso(self.start),
            "end": _iso(self.end),
            "minutes": (self.end - self.start) // 60,
            "observed": self.observed,
            "classification": self.classification,
            "label": CLAIM_LABELS[self.classification],
            "binding_constraint": self.binding,
            "reasons": self.reasons,
            "missing": self.missing,
            "inputs": self.inputs,
            "evidence": [_link(r) for r in self.records],
        }


def _problem_text(name: str, lookup: Lookup) -> str:
    what = {"MISSING": "no record", "NOT_GOOD": "no GOOD record", "CONFLICTING": "conflicting records"}
    return f"{INPUT_LABELS[name]}: {what.get(lookup.problem or 'MISSING', 'no record')}"


def _evaluate(evidence: _Evidence, start: int, end: int, first_on: int) -> _Segment:
    records: list[AcceptedRecord] = []
    feeder_lookups = [evidence.interval_mean(key, end) for key in FEEDERS]
    for lookup in feeder_lookups:
        records.extend(lookup.records)
    load_problem = next((l for l in feeder_lookups if not l.usable), None)
    load = None if load_problem else sum((l.value or Fraction(0) for l in feeder_lookups), Fraction(0))
    pv = evidence.interval_mean(PV_AVAILABLE, end)
    soc = evidence.instant(SOC, end)
    discharge = evidence.interval_mean(DISCHARGE, end)
    generator = evidence.interval_mean(GEN_POWER, end)
    for lookup in (pv, soc, discharge, generator):
        records.extend(lookup.records)

    reserve_record = evidence.effective(BATTERY_OVERRIDE, end, "OPERATIONAL_RECORD")
    reserve_source = "operator override"
    if reserve_record is None or _detail(reserve_record, "control") != "battery-reserve-state-of-charge":
        reserve_record = evidence.effective(POLICY_RESERVE, end, "POLICY")
        reserve_source = "policy"
    reserve = Fraction(reserve_record.normalized_value or "0") if reserve_record else None
    min_runtime = evidence.effective(POLICY_MIN_RUNTIME, end, "POLICY")
    override = evidence.effective(GEN_OVERRIDE, end, "OPERATIONAL_RECORD")
    for record in (reserve_record, min_runtime, override):
        if record is not None:
            records.append(record)

    inputs: dict[str, str | None] = {
        "load_kw": None if load is None else _dec(load),
        "pv_available_kw": None if pv.value is None else _dec(pv.value),
        "soc_pct": None if soc.value is None else _dec(soc.value),
        "reserve_pct": None if reserve is None else _dec(reserve),
        "reserve_source": None if reserve_record is None else reserve_source,
        "discharge_capability_kw": None if discharge.value is None else _dec(discharge.value),
        "generator_kw": None if generator.value is None else _dec(generator.value),
    }

    def segment(classification: str, binding: str | None, reasons: list[str],
                missing: list[str] | None = None, margin: Fraction | None = None) -> _Segment:
        return _Segment(start, end, True, classification, binding, reasons, missing or [],
                        inputs, records, margin, load, generator.value)

    # 1. operator override holding the generator on.
    if override is not None and _detail(override, "control") == "generator-stop-soc-threshold":
        value = Fraction(override.normalized_value or "0")
        if soc.value is None or soc.value < value:
            return segment(NECESSARY, "OPERATOR_OVERRIDE", [
                f"An operator-commanded override sets the generator stop threshold to "
                f"{_dec(value)} % from {_detail(override, 'effective_start')}; the generator "
                "runs under that command."
            ])
    # 2. minimum runtime.
    if min_runtime is not None:
        minutes = Fraction(min_runtime.normalized_value or "0")
        if end - first_on <= minutes * 60:
            return segment(NECESSARY, "MINIMUM_RUNTIME", [
                f"Within the {_dec(minutes)} min minimum runtime policy after the start "
                f"observed at {_iso(first_on)}."
            ])
    # 3. battery at or near reserve and PV short of load.
    if load is not None and pv.usable and soc.usable and reserve is not None:
        if (soc.value or 0) <= reserve + SOC_HEADROOM_POINTS and load > (pv.value or 0):
            at = (soc.value or 0) <= reserve
            return segment(NECESSARY, "BATTERY_AT_RESERVE" if at else "BATTERY_NEAR_RESERVE", [
                f"Battery at {_dec(soc.value or Fraction(0))} % is "
                + ("at or below" if at else f"within {SOC_HEADROOM_POINTS} points of")
                + f" its {_dec(reserve)} % reserve ({reserve_source}), so it cannot be counted on "
                f"to carry load {_dec(load)} kW above PV available {_dec(pv.value or Fraction(0))} kW."
            ])
    # 4. capability shortfall.
    if load is not None and pv.usable and discharge.usable:
        supply = (pv.value or 0) + (discharge.value or 0)
        if load > supply:
            return segment(NECESSARY, "CAPABILITY_SHORTFALL", [
                f"Load {_dec(load)} kW exceeds PV available {_dec(pv.value or Fraction(0))} kW "
                f"plus battery discharge capability {_dec(discharge.value or Fraction(0))} kW."
            ])
    # 5. candidate. PV alone covering load needs no battery state; otherwise
    # battery support counts only above reserve plus the declared headroom.
    missing = []
    if load is None and load_problem is not None:
        missing.append(_problem_text("load", load_problem))
    for name, lookup in (("pv_available", pv), ("discharge_capability", discharge)):
        if not lookup.usable:
            missing.append(_problem_text(name, lookup))
    pv_alone = (
        not missing and load is not None
        and (pv.value or 0) >= load * (1 + CAPABILITY_HEADROOM)
    )
    if not pv_alone:
        if not soc.usable:
            missing.append(_problem_text("soc", soc))
        if reserve is None:
            missing.append(f"{INPUT_LABELS['reserve']}: no effective record")
    if not missing and load is not None:
        if pv_alone:
            margin = (pv.value or 0) - load
            return segment(CANDIDATE, None, [
                f"PV available {_dec(pv.value or Fraction(0))} kW alone exceeds load "
                f"{_dec(load)} kW by {_dec(margin)} kW, with battery discharge capability "
                f"{_dec(discharge.value or Fraction(0))} kW evidenced; no binding constraint "
                "was evidenced."
            ], margin=margin)
        support = discharge.value or Fraction(0)
        supply = (pv.value or 0) + support
        margin = supply - load
        if supply >= load * (1 + CAPABILITY_HEADROOM):
            return segment(CANDIDATE, None, [
                f"PV available {_dec(pv.value or Fraction(0))} kW plus battery support "
                f"{_dec(support)} kW (SOC {_dec(soc.value or Fraction(0))} %, more than "
                f"{SOC_HEADROOM_POINTS} points above its {_dec(reserve or Fraction(0))} % reserve) "
                f"exceeds load {_dec(load)} kW by {_dec(margin)} kW; no binding constraint "
                "was evidenced."
            ], margin=margin)
        return segment(INDETERMINATE, None, [
            f"Capability margin {_dec(margin)} kW is inside the declared "
            f"{_dec(CAPABILITY_HEADROOM * 100)} % headroom on load {_dec(load)} kW."
        ])
    return segment(INDETERMINATE, None, [
        "The evidence needed to decide is missing or conflicting: " + "; ".join(missing) + "."
    ], missing)


def _combine(start: _Segment, end: _Segment) -> _Segment:
    """A segment from its two end points (decision table "Segment evaluation").

    Candidate only when both ends are; Necessary when either end is (that end's
    binding constraint); otherwise Indeterminate. A transition inside a segment
    therefore never becomes candidate time.
    """
    records = list(dict.fromkeys(start.records + end.records))
    if start.classification == CANDIDATE and end.classification == CANDIDATE:
        decided, level = end, CANDIDATE
        margin = min(start.margin or Fraction(0), end.margin or Fraction(0))
        load = end.load if end.margin == margin else start.load
    elif NECESSARY in (start.classification, end.classification):
        decided = end if end.classification == NECESSARY else start
        level, margin, load = NECESSARY, None, decided.load
    else:
        decided = end if end.classification == INDETERMINATE else start
        level, margin, load = INDETERMINATE, None, decided.load
    reasons = list(decided.reasons)
    if start.classification != end.classification:
        reasons.append(
            f"The segment's ends differ ({CLAIM_LABELS[start.classification]} at "
            f"{_iso(start.end)}, {CLAIM_LABELS[end.classification]} at {_iso(end.end)}); "
            "the conservative classification is kept."
        )
    missing = sorted(set(start.missing) | set(end.missing)) if level == INDETERMINATE else []
    return _Segment(
        start.end, end.end, True, level, decided.binding, reasons, missing,
        {"at_start": start.inputs, "at_end": end.inputs}, records, margin, load,
        end.generator_kw,
    )


# --- interval assembly (AC4-AC11) ---------------------------------------------


@dataclass(frozen=True)
class FuelBasis:
    """The Foundation property the fuel quantity is modelled from."""

    specific_fuel_consumption: Fraction | None
    source: str


def _portions(segments: list[_Segment]) -> dict[str, int]:
    out = {NECESSARY: 0, CANDIDATE: 0, INDETERMINATE: 0}
    for seg in segments:
        out[seg.classification] += seg.end - seg.start
    return out


def _spans(segments: list[_Segment], predicate) -> list[dict[str, str]]:
    spans: list[list[int]] = []
    for seg in segments:
        if predicate(seg):
            if spans and spans[-1][1] == seg.start:
                spans[-1][1] = seg.end
            else:
                spans.append([seg.start, seg.end])
    return [{"start": _iso(a), "end": _iso(b), "minutes": str((b - a) // 60)} for a, b in spans]


def _has(segment: _Segment, name: str) -> bool:
    """Whether an input is usable at both ends of an observed segment."""
    ends = [segment.inputs.get("at_start"), segment.inputs.get("at_end")]
    return all(isinstance(e, dict) and e.get(name) is not None for e in ends)


def _coverage(segments: list[_Segment]) -> dict[str, Any]:
    observed = [s for s in segments if s.observed]
    names = {
        "load": "load_kw", "pv_available": "pv_available_kw", "soc": "soc_pct",
        "reserve": "reserve_pct", "discharge_capability": "discharge_capability_kw",
    }
    rows = []
    for name in REQUIRED_INPUTS:
        usable = [s for s in observed if _has(s, names[name])]
        rows.append({
            "input": name,
            "label": INPUT_LABELS[name],
            "usable_segments": len(usable),
            "evaluated_segments": len(observed),
            "gaps": _spans(observed, lambda s, n=names[name]: not _has(s, n)),
        })
    return {
        "inputs": rows,
        "unobserved_generator_state": _spans(segments, lambda s: not s.observed),
        "statement": (
            "Coverage counts evaluated segments with a usable record for each input. "
            "Interval inputs are 5-minute means reported every 15 minutes, so about a "
            "third of each segment is measured; the rest is not observed and is not "
            "filled in."
        ),
    }


def _confidence(level: str, segments: list[_Segment], uncertainty: int | None) -> dict[str, Any]:
    if level == INDETERMINATE:
        return {"level": "NOT_APPLICABLE", "basis": [
            "No classification could be reached, so there is no confidence to state."
        ]}
    steps = ["HIGH", "MEDIUM", "LOW"]
    drop = 0
    basis = []
    indeterminate = [s for s in segments if s.classification == INDETERMINATE]
    if indeterminate:
        drop += 1
        minutes = sum(s.end - s.start for s in indeterminate) // 60
        basis.append(f"{minutes} min of the interval is Indeterminate (lowers one level).")
    else:
        basis.append("Every evaluated segment reached a classification.")
    if level == CANDIDATE:
        margins = [s.margin / s.load for s in segments
                   if s.classification == CANDIDATE and s.margin is not None and s.load]
        smallest = min(margins) if margins else None
        if smallest is not None and smallest < STRONG_MARGIN:
            drop += 1
            basis.append(
                f"Smallest candidate margin is {_dec(smallest * 100, 0)} % of load, below the "
                f"{_dec(STRONG_MARGIN * 100, 0)} % strong margin (lowers one level)."
            )
        elif smallest is not None:
            basis.append(f"Smallest candidate margin is {_dec(smallest * 100, 0)} % of load.")
    if uncertainty is None:
        drop += 1
        basis.append("Start or stop time is not bracketed by evidence (lowers one level).")
    elif uncertainty > TRANSITION_LIMIT_S:
        drop += 1
        basis.append(f"Start/stop uncertainty is {uncertainty // 60} min (lowers one level).")
    else:
        basis.append(f"Start/stop uncertainty is {uncertainty // 60} min.")
    return {"level": steps[min(drop, 2)], "basis": basis}


def _fuel(level: str, segments: list[_Segment], lower: int, upper: int | None,
          fuel: FuelBasis) -> dict[str, Any]:
    base = {"basis": "modelled", "statement": (
        "Indicative fuel associated with the candidate runtime. It is not a "
        "reconciled tank loss and not a financial saving."
    )}
    if level != CANDIDATE:
        return {**base, "status": "NOT_APPLICABLE",
                "reason": "Only a candidate avoidable interval carries a fuel estimate."}
    powers = [s.generator_kw for s in segments
              if s.classification == CANDIDATE and s.generator_kw is not None]
    reason = None
    if not powers:
        reason = "No generator output mean is usable in a candidate segment."
    elif upper is None:
        reason = "The candidate duration's upper bound is open (no stop evidence)."
    elif fuel.specific_fuel_consumption is None:
        reason = "No generator specific fuel consumption is configured in the Foundation."
    if reason is not None:
        return {**base, "status": "UNAVAILABLE", "reason": reason}
    sfc = fuel.specific_fuel_consumption or Fraction(0)
    p_low, p_high = min(powers), max(powers)
    assert upper is not None
    low = Fraction(lower, 3600) * p_low * sfc * (1 - SFC_UNCERTAINTY)
    high = Fraction(upper, 3600) * p_high * sfc * (1 + SFC_UNCERTAINTY)
    return {
        **base,
        "status": "BOUNDED",
        "low_litres": _dec(low, 1),
        "high_litres": _dec(high, 1),
        "unit": "L",
        "inputs": {
            "duration_hours": {"low": _hours(lower), "high": _hours(upper), "basis": "measured",
                               "note": "Candidate segment duration, bounded by start/stop evidence."},
            "generator_kw": {"low": _dec(p_low), "high": _dec(p_high), "basis": "measured",
                             "note": "Range of 5-minute output means in candidate segments."},
            "specific_fuel_consumption": {
                "value": _dec(sfc, 3), "unit": "L/kWh", "basis": "configured",
                "uncertainty_pct": _dec(SFC_UNCERTAINTY * 100, 0), "source": fuel.source,
            },
        },
        "formula": "duration x output x specific fuel consumption x (1 -/+ uncertainty)",
    }


def _alternatives(evidence: _Evidence, run: _Run, segments: list[_Segment],
                  after_off: int | None) -> list[dict[str, Any]]:
    first, last = run.on_times[0], run.on_times[-1]
    overrides = [
        r for key in (GEN_OVERRIDE, BATTERY_OVERRIDE) for r in evidence.of(key)
        if r.family == "OPERATIONAL_RECORD"
        and _t(_detail(r, "effective_start") or r.source_time) <= (after_off or last)
        and (_detail(r, "effective_end") is None or _t(_detail(r, "effective_end") or "") > first)
    ]
    out = []
    if overrides:
        out.append({
            "id": "OPERATOR_OVERRIDE", "label": "Operator-commanded override",
            "status": "OBSERVED",
            "statement": "An operator-commanded override record is effective during this "
                         "interval and is included in the constraint assessment at its time.",
            "evidence": [_link(r) for r in overrides],
        })
    else:
        out.append({
            "id": "UNOBSERVED_OVERRIDE", "label": "Unobserved operator override",
            "status": "NOT_EXCLUDED",
            "statement": "No operator-commanded override record observed for this interval. "
                         "Absence of a record is not proof that no override existed.",
            "evidence": [],
        })
    stop = evidence.effective(POLICY_STOP, last, "POLICY")
    if stop is not None:
        threshold = Fraction(stop.normalized_value or "0")
        statement = (
            f"The published generator stop threshold is {_dec(threshold)} % "
            f"(policy v{_detail(stop, 'policy_version')}, {_detail(stop, 'policy_source')}, from "
            f"{_detail(stop, 'effective_start')}). A generator held on below it is consistent "
            "with that policy: a candidate concerns the policy setting, not a controller fault."
        )
        links = [_link(stop)]
        if after_off is not None and not overrides:
            soc = evidence.instant(SOC, after_off + INSTANT_TOLERANCE_S - 1)
            if soc.usable and (soc.value or 0) < threshold:
                statement += (
                    f" The observed stop near {_iso(after_off)} at SOC "
                    f"{_dec(soc.value or Fraction(0))} % is below that threshold: the published "
                    "policy does not explain this stop, so the effective policy may differ and "
                    "no record of a change was observed."
                )
                links.extend(_link(r) for r in soc.records)
        out.append({"id": "POLICY_CONSTRAINT", "label": "Policy constraint",
                    "status": "NOT_EXCLUDED", "statement": statement, "evidence": links})
    else:
        out.append({"id": "POLICY_CONSTRAINT", "label": "Policy constraint",
                    "status": "NOT_EXCLUDED",
                    "statement": "No generator stop policy record is accepted; the policy the "
                                 "controller ran under is not known.", "evidence": []})
    observed = [s for s in segments if s.observed]
    gaps = _spans(observed, lambda s: not _has(s, "discharge_capability_kw"))
    capability = [r for s in observed for r in s.records if (r.device_id, r.signal_id) == DISCHARGE]
    if gaps:
        minutes = sum(int(g["minutes"]) for g in gaps)
        out.append({
            "id": "PCS_CAPABILITY_UNAVAILABLE", "label": "Unavailable PCS capability",
            "status": "NOT_EXCLUDED",
            "statement": f"Battery discharge capability is not evidenced for {minutes} min "
                         "of the interval; battery support there is unknown and those "
                         "segments carry no candidate claim.",
            "evidence": [_link(r) for r in capability],
            "gaps": gaps,
        })
    else:
        out.append({
            "id": "PCS_CAPABILITY_UNAVAILABLE", "label": "Unavailable PCS capability",
            "status": "CONTRADICTED_BY_EVIDENCE",
            "statement": "Battery discharge capability is evidenced in every evaluated segment.",
            "evidence": [_link(r) for r in capability],
        })
    out.append({
        "id": "UNMEASURED_PV_VARIATION", "label": "PV capability between measurements",
        "status": "NOT_EXCLUDED",
        "statement": "PV available power is a 5-minute mean reported every 15 minutes; "
                     "capability between those means is not observed.",
        "evidence": [_link(r) for s in observed for r in s.records
                     if (r.device_id, r.signal_id) == PV_AVAILABLE],
    })
    return out


CLAIM_CEILINGS = {
    NECESSARY: "Generator operation was required by the binding constraint shown, on the "
               "accepted evidence. It does not say the constraint itself was well set.",
    CANDIDATE: "A bounded candidate under declared evidence and model assumptions "
               f"({MODEL_VERSION}): not proven waste and not optimal dispatch.",
    INDETERMINATE: "No classification: the named evidence is missing or conflicting. This "
                   "is not a statement that the runtime was necessary or avoidable.",
}


def _one_line(level: str, portions: dict[str, int], lower: int, upper: int | None,
              confidence: str, binding: list[str], missing: list[str]) -> str:
    up = "open" if upper is None else f"{_hours(upper)} h"
    if level == CANDIDATE:
        return (f"{_hours(portions[CANDIDATE])} h of generator runtime with PV and battery "
                f"capability above load and no binding constraint evidenced "
                f"(confidence {confidence.lower()}).")
    if level == NECESSARY:
        return (f"Generator runtime of {_hours(lower)}-{up} was required: "
                f"{', '.join(binding).lower().replace('_', ' ')}.")
    return ("Generator runtime could not be classified: "
            f"{'; '.join(missing) if missing else 'generator state not observed'}.")


def _digest(records: Iterable[AcceptedRecord]) -> tuple[list[str], str]:
    pairs = sorted({(r.message_id, r.content_digest) for r in records})
    text = json.dumps({"model": MODEL_VERSION, "records": pairs}, separators=(",", ":"))
    return [m for m, _ in pairs], hashlib.sha256(text.encode("utf-8")).hexdigest()


def _interval(evidence: _Evidence, run: _Run, fuel: FuelBasis) -> dict[str, Any]:
    first, last = run.on_times[0], run.on_times[-1]
    before, after = _off_before(evidence, first), _off_after(evidence, last)
    points = {t: _evaluate(evidence, t, t, first) for t in run.on_times}
    segments: list[_Segment] = []
    if len(run.on_times) == 1:
        segments.append(_combine(points[first], points[first]))
    for a, b in zip(run.on_times, run.on_times[1:]):
        through_gap = any(a < u < b for u in run.unobserved)
        if b - a > CONTINUITY_TOLERANCE_S or through_gap:
            segments.append(_Segment(
                a, b, False, INDETERMINATE, None,
                ["Generator state is not observed between these times."],
                ["Generator state (status or output)"], {}, [],
            ))
        else:
            segments.append(_combine(points[a], points[b]))
    observed = [s for s in segments if s.observed]
    lower = sum(s.end - s.start for s in observed)
    upper = None if before is None or after is None else after - before
    uncertainty = None if upper is None else (first - (before or first)) + ((after or last) - last)
    portions = _portions(segments)
    classes = {s.classification for s in segments}
    if classes == {NECESSARY}:
        level = NECESSARY
    elif CANDIDATE in classes:
        level = CANDIDATE
    else:
        level = INDETERMINATE
    # Candidate bounds: the candidate segments, plus an edge's uncertainty when
    # the segment beside that edge is itself a candidate.
    candidate_lower = portions[CANDIDATE]
    candidate_upper: int | None = candidate_lower
    if level == CANDIDATE and segments:
        for edge, seg in (("start", segments[0]), ("end", segments[-1])):
            if seg.classification != CANDIDATE:
                continue
            bound = before if edge == "start" else after
            if bound is None:
                candidate_upper = None
                break
            candidate_upper = (candidate_upper or 0) + (first - bound if edge == "start" else bound - last)
    binding = sorted({s.binding for s in segments if s.binding})
    missing = sorted({m for s in segments for m in s.missing})
    confidence = _confidence(level, segments, uncertainty)
    used = list(run.records) + [r for s in segments for r in s.records]
    message_ids, basis_digest = _digest(used)
    alternatives = _alternatives(evidence, run, segments, after)
    override_alt = alternatives[0]
    limits = [CLAIM_CEILINGS[level], override_alt["statement"]]
    if level == CANDIDATE and portions[INDETERMINATE]:
        limits.append(
            f"{_hours(portions[INDETERMINATE])} h of this interval is Indeterminate and is not "
            "part of the candidate."
        )
    if level == CANDIDATE and portions[NECESSARY]:
        limits.append(
            f"{_hours(portions[NECESSARY])} h of this interval is Necessary and is not part of "
            "the candidate."
        )
    return {
        "analytic_id": ANALYTIC_ID,
        "model_version": MODEL_VERSION,
        "finding_type": FINDING_TYPE,
        "claim_level": level,
        "label": CLAIM_LABELS[level],
        "summary": _one_line(level, portions, lower, upper, confidence["level"], binding, missing),
        "raises_finding": level in FINDING_CLAIM_LEVELS,
        "interval": {
            "first_running_observed": _iso(first),
            "last_running_observed": _iso(last),
            "last_stopped_before": None if before is None else _iso(before),
            "first_stopped_after": None if after is None else _iso(after),
            "duration_hours": {"low": _hours(lower), "high": None if upper is None else _hours(upper)},
            "open_start": before is None,
            "open_end": after is None,
            "statement": (
                "Duration is bounded by generator-state evidence: the low bound counts "
                "observed running spans; the high bound runs from the last stopped evidence "
                "before to the first stopped evidence after. Gaps count in the high bound only."
            ),
        },
        "assessed_window": {
            "start": _iso(before if before is not None else first),
            "end": _iso(after if after is not None else last),
        },
        "portions_hours": {
            CANDIDATE: {"low": _hours(candidate_lower),
                        "high": None if candidate_upper is None else _hours(candidate_upper)},
            NECESSARY: {"low": _hours(portions[NECESSARY])},
            INDETERMINATE: {"low": _hours(portions[INDETERMINATE])},
        },
        "binding_constraints": binding,
        "missing_evidence": missing,
        "segments": [s.payload() for s in segments],
        "coverage": _coverage(segments),
        "confidence": confidence,
        "alternatives": alternatives,
        "claim_limits": limits,
        "fuel": _fuel(level, segments, candidate_lower, candidate_upper, fuel),
        "evidence_basis": {"message_ids": message_ids, "digest": basis_digest},
    }


def assess(records: Sequence[AcceptedRecord], fuel: FuelBasis) -> list[dict[str, Any]]:
    """Every generator interval in the accepted records, assessed (model dispatch-1)."""
    evidence = _Evidence(records)
    return [_interval(evidence, run, fuel) for run in _runs(_states(evidence))]
