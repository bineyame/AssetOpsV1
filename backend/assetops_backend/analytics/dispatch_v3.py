"""Mini-grid dispatch analytic, model `dispatch-3` (pure; S3-01 phase 2).

Input: one `AnalyticInputSet` (selected public cohort, selected Foundation
controls, selected role bindings). Output: a window assessment plus one
interval assessment per generator ON interval whose first ON report lies in
the window. Every threshold, carried or changed `dispatch-2` branch and limit
is stated in `backend/tests/dispatch_3_decision_table.md`; changing one is a
new model version.

No IO, no clock, no SQL row, no envelope JSON, no Lab state, no file-backed
assessment. Roles are canonical `minigrid-roles-1/2` role names, never device
or signal strings.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any

from assetops_backend.analytics.assessment_inputs import (
    CONTROL_BATTERY_RESERVE,
    CONTROL_MINIMUM_RUNTIME,
    AcceptedReading,
    AnalyticInputSet,
    CohortLimit,
    ControlValue,
    iso,
    sha256_json,
)
from assetops_backend.analytics.dispatch import ANALYTIC_ID, CANDIDATE, INDETERMINATE, NECESSARY

MODEL_VERSION = "dispatch-3"

CONTINUITY_TOLERANCE = timedelta(minutes=20)
INSTANT_TOLERANCE = timedelta(minutes=10)
CAPABILITY_HEADROOM = Fraction(1, 10)
SOC_HEADROOM_POINTS = Fraction(10)
STRONG_MARGIN = Fraction(1, 4)
TRANSITION_LIMIT = timedelta(minutes=15)

GEN_STATE = "generator_state"
GEN_POWER = "generator_power"
LOAD = "feeder_demand"
PV_AVAILABLE = "pv_available_power"
DISCHARGE = "pcs_discharge_capability"
SOC = "battery_soc"
#: Roles whose readings an evaluated point reads (cohort limits on them make a segment unusable).
POINT_ROLES = (LOAD, PV_AVAILABLE, DISCHARGE, SOC)

ON_STATES = frozenset({"RUNNING"})
OFF_STATES = frozenset({"STOPPED", "STARTING", "FAILED"})

LABELS = {
    LOAD: "Load (feeder demand)", PV_AVAILABLE: "PV available power", DISCHARGE: "PCS discharge capability",
    SOC: "Battery state of charge", CONTROL_BATTERY_RESERVE: "Battery reserve (Foundation control)",
}

# Window claim levels (the interval levels are NECESSARY / CANDIDATE / INDETERMINATE).
WINDOW_COMPLETE = "COMPLETE"
WINDOW_LIMITED = "LIMITED"
WINDOW_INDETERMINATE = "INDETERMINATE"


def _num(x: Fraction | None) -> str | None:
    if x is None:
        return None
    return format((Decimal(x.numerator) / Decimal(x.denominator)).normalize(), "f")


def _fraction(text: str | None) -> Fraction | None:
    if text is None:
        return None
    try:
        return Fraction(Decimal(text))
    except (InvalidOperation, ValueError):
        return None


@dataclass(frozen=True)
class Lookup:
    value: Any
    ids: tuple[str, ...]
    problem: str | None


@dataclass
class Point:
    classification: str
    binding: str | None
    reasons: list[str]
    missing: list[str]
    ids: set[str]
    margin: Fraction | None = None
    load: Fraction | None = None


@dataclass
class Segment:
    start: datetime
    end: datetime
    observed: bool
    classification: str
    binding: str | None
    reasons: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    ids: set[str] = field(default_factory=set)
    margin: Fraction | None = None
    load: Fraction | None = None

    @property
    def seconds(self) -> int:
        return int((self.end - self.start).total_seconds())

    def payload(self) -> dict[str, Any]:
        return {"start": iso(self.start), "end": iso(self.end), "minutes": _num(Fraction(self.seconds, 60)),
                "observed": self.observed, "classification": self.classification,
                "binding_constraint": self.binding, "reasons": sorted(set(self.reasons)),
                "missing": sorted(set(self.missing)), "margin_kw": _num(self.margin), "load_kw": _num(self.load),
                "evidence_ids": sorted(self.ids)}


@dataclass(frozen=True)
class IntervalAssessment:
    assessment_key: str
    window_start: datetime
    window_end: datetime
    claim_level: str
    result: dict[str, Any]
    evidence_ids: tuple[str, ...]
    basis_sha256: str


@dataclass(frozen=True)
class WindowAssessment:
    assessment_key: str
    claim_level: str
    result: dict[str, Any]
    basis_sha256: str
    intervals: tuple[IntervalAssessment, ...]


class _Index:
    def __init__(self, inputs: AnalyticInputSet) -> None:
        self.inputs = inputs
        self.by_channel: dict[tuple[str, str], list[AcceptedReading]] = defaultdict(list)
        for r in inputs.readings:
            self.by_channel[r.channel].append(r)
        self.limits: dict[tuple[str, str], list[CohortLimit]] = defaultdict(list)
        for limit in inputs.cohort.limits:
            self.limits[(limit.role, limit.asset_id)].append(limit)
        self.digest = {str(r.evidence_id): r.envelope_sha256 for r in inputs.readings}

    def assets(self, role: str, at: datetime) -> list[str]:
        return sorted({str(b.asset_id) for b in self.inputs.bindings if b.role == role and b.effective(at)})

    def limited(self, role: str, asset: str, lo: datetime, hi: datetime) -> list[CohortLimit]:
        return [x for x in self.limits[(role, asset)] if x.start <= hi and lo <= x.end]

    def lookup(self, role: str, at: datetime) -> Lookup:
        """A ONE-cardinality role at `at`: an interval mean ending at `at`, else the latest
        instant in (at - INSTANT_TOLERANCE, at]."""
        assets = self.assets(role, at)
        if not assets:
            return Lookup(None, (), "UNBOUND")
        if len(assets) > 1:
            return Lookup(None, (), "MULTIPLE_BINDINGS")
        return self.lookup_asset(role, assets[0], at)

    def lookup_asset(self, role: str, asset: str, at: datetime) -> Lookup:
        rows = self.by_channel.get((role, asset), [])
        found = [r for r in rows if r.interval_end is not None and r.interval_end == at]
        lo = at if found else at - INSTANT_TOLERANCE
        if not found:
            instants = [r for r in rows if r.interval_end is None and at - INSTANT_TOLERANCE < r.source_time <= at]
            if instants:
                latest = max(r.source_time for r in instants)
                found = [r for r in instants if r.source_time == latest]
        if self.limited(role, asset, lo, at):
            ids = tuple(sorted({e for x in self.limited(role, asset, lo, at) for e in x.evidence_ids}))
            return Lookup(None, ids, "AMBIGUOUS_SERIES")
        if not found:
            return Lookup(None, (), "MISSING")
        ids = tuple(sorted(str(r.evidence_id) for r in found))
        good = [r for r in found if r.quality == "GOOD" and r.value is not None]
        if not good:
            return Lookup(None, ids, "NOT_GOOD")
        values = {r.value if role == GEN_STATE else _fraction(r.value) for r in good}
        if len(values) > 1 or None in values:
            return Lookup(None, ids, "CONFLICTING")
        return Lookup(values.pop(), ids, None)

    def control(self, key: str, at: datetime) -> tuple[Fraction | None, ControlValue | None, str | None]:
        found = [c for c in self.inputs.controls if c.key == key and c.effective(at)]
        if not found:
            return None, None, "NOT_CONFIGURED"
        if len({c.value for c in found}) > 1:
            return None, None, "CONFLICTING"
        return _fraction(found[0].value), found[0], None


_PROBLEM_TEXT = {
    "UNBOUND": "not bound in the selected role set (missing role)",
    "MULTIPLE_BINDINGS": "bound to more than one asset",
    "MISSING": "no accepted reading",
    "NOT_GOOD": "reading not GOOD quality",
    "CONFLICTING": "contradictory readings at one time",
    "AMBIGUOUS_SERIES": "reports out of sequence order or overlapping (cohort limit)",
    "NOT_CONFIGURED": "not configured",
}


def _missing(role: str, problem: str) -> str:
    return f"{LABELS.get(role, role)}: {_PROBLEM_TEXT.get(problem, problem)}"


def _state(index: _Index, asset: str, at: datetime) -> tuple[str, datetime, set[str]]:
    """ON / OFF / UNOBSERVED at report time `at`, the OFF bound to use after an interval
    (a zero-output mean's start, else `at`) and the readings that placed it."""
    status = [r for r in index.by_channel.get((GEN_STATE, asset), []) if r.placed_at == at]
    power = [r for r in index.by_channel.get((GEN_POWER, asset), []) if r.interval_end == at]
    if index.limited(GEN_STATE, asset, at, at) or index.limited(GEN_POWER, asset, at, at):
        return "UNOBSERVED", at, {str(r.evidence_id) for r in status + power}
    good = {r.value for r in status if r.quality == "GOOD" and r.value is not None}
    if len(good) == 1:
        value = next(iter(good))
        ids = {str(r.evidence_id) for r in status}
        if value in ON_STATES:
            return "ON", at, ids
        if value in OFF_STATES:
            return "OFF", at, ids
        return "UNOBSERVED", at, ids
    if len(good) > 1:
        return "UNOBSERVED", at, {str(r.evidence_id) for r in status}
    means = {_fraction(r.value) for r in power if r.quality == "GOOD" and r.value is not None}
    if len(means) == 1 and None not in means:
        mean = next(iter(means))
        ids = {str(r.evidence_id) for r in power}
        starts = [r.interval_start for r in power if r.interval_start is not None]
        return ("ON", at, ids) if mean > 0 else ("OFF", min(starts) if starts else at, ids)
    return "UNOBSERVED", at, {str(r.evidence_id) for r in status + power}


def _evaluate(index: _Index, t_meas: datetime, t_ctrl: datetime, t_rt: datetime,
              first_on: datetime) -> Point:
    ids: set[str] = set()
    missing: list[str] = []

    def take(role: str) -> Fraction | None:
        found = index.lookup(role, t_meas)
        ids.update(found.ids)
        if found.problem:
            missing.append(_missing(role, found.problem))
        return found.value

    feeders = index.assets(LOAD, t_meas)
    load: Fraction | None = Fraction(0)
    if not feeders:
        missing.append(_missing(LOAD, "UNBOUND"))
        load = None
    for asset in feeders:
        found = index.lookup_asset(LOAD, asset, t_meas)
        ids.update(found.ids)
        if found.problem:
            missing.append(_missing(LOAD, found.problem) + f" (asset {asset})")
            load = None
        elif load is not None:
            load += found.value
    pv, dis, soc = take(PV_AVAILABLE), take(DISCHARGE), take(SOC)
    reserve, reserve_control, problem = index.control(CONTROL_BATTERY_RESERVE, t_ctrl)
    if problem:
        missing.append(_missing(CONTROL_BATTERY_RESERVE, problem))
    reasons: list[str] = []
    if reserve_control is not None:
        reasons.append(f"reserve {reserve_control.value} % (Foundation revision {reserve_control.foundation_revision_id})")

    def point(classification: str, binding: str | None, margin: Fraction | None = None) -> Point:
        return Point(classification, binding, reasons, list(missing), ids, margin, load)

    result: Point | None = None
    if None not in (load, pv, soc, reserve) and soc <= reserve + SOC_HEADROOM_POINTS and load > pv:
        result = point(NECESSARY, "BATTERY_AT_RESERVE" if soc <= reserve else "BATTERY_NEAR_RESERVE")
    elif None not in (load, pv, dis) and load > pv + dis:
        result = point(NECESSARY, "CAPABILITY_SHORTFALL")
    elif None not in (load, pv, dis) and pv >= load * (1 + CAPABILITY_HEADROOM):
        result = point(CANDIDATE, None, pv - load)
        reasons.append("PV available alone covers load with 10 % headroom; PCS availability evidenced")
    elif None not in (load, pv, dis, soc, reserve):
        if soc <= reserve + SOC_HEADROOM_POINTS:
            result = point(INDETERMINATE, None)
            result.missing.append("battery inside the 10-point SOC headroom over reserve; battery support not counted")
        elif pv + dis >= load * (1 + CAPABILITY_HEADROOM):
            result = point(CANDIDATE, None, pv + dis - load)
            reasons.append("PV available plus PCS discharge capability covers load with 10 % headroom")
        else:
            result = point(INDETERMINATE, None)
            result.missing.append("capability margin inside the declared 10 % headroom")
    if result is None:
        result = point(INDETERMINATE, None)
    if result.classification == CANDIDATE:
        runtime, runtime_control, _ = index.control(CONTROL_MINIMUM_RUNTIME, t_ctrl)
        if runtime is not None and (t_rt - first_on) < timedelta(minutes=float(runtime)):
            result = Point(INDETERMINATE, None, reasons, list(missing), ids, None, load)
            result.missing.append(
                f"possibly within the configured minimum runtime ({runtime_control.value} min from the first "
                f"ON report); Candidate withheld, no policy Necessary claimed")
    return result


def _combine(a: Point, b: Point, start: datetime, end: datetime) -> Segment:
    ids = a.ids | b.ids
    reasons, missing = a.reasons + b.reasons, a.missing + b.missing
    if a.classification == CANDIDATE and b.classification == CANDIDATE:
        return Segment(start, end, True, CANDIDATE, None, reasons, missing, ids, min(a.margin, b.margin),
                       a.load if a.load is not None else b.load)
    for p in (a, b):
        if p.classification == NECESSARY:
            return Segment(start, end, True, NECESSARY, p.binding, reasons, missing, ids, None, p.load)
    if a.classification == CANDIDATE or b.classification == CANDIDATE:
        missing = missing + ["transition inside the segment: Candidate only when both ends are Candidate"]
    return Segment(start, end, True, INDETERMINATE, None, reasons, missing, ids)


def _control_changes(inputs: AnalyticInputSet, lo: datetime, hi: datetime) -> list[datetime]:
    edges = set()
    for c in inputs.controls:
        if c.key in (CONTROL_BATTERY_RESERVE, CONTROL_MINIMUM_RUNTIME):
            for edge in (c.valid_from, c.valid_to):
                if edge is not None and lo < edge < hi:
                    edges.add(edge)
    return sorted(edges)


def _segments(index: _Index, a: datetime, b: datetime, first_on: datetime) -> list[Segment]:
    cuts = [a, *_control_changes(index.inputs, a, b), b]
    out = []
    for p0, p1 in zip(cuts, cuts[1:]):
        left = _evaluate(index, a, p0, p0, first_on)
        right = _evaluate(index, b, p0, p1, first_on)
        out.append(_combine(left, right, p0, p1))
    return out


def _segment_limits(index: _Index, a: datetime, b: datetime) -> list[CohortLimit]:
    found = []
    for role in POINT_ROLES:
        for asset in index.assets(role, a) + index.assets(role, b):
            found.extend(index.limited(role, asset, a, b))
    return found


def _confidence(claim: str, segments: list[Segment], upper: int | None, lower: int) -> dict[str, Any]:
    if claim == INDETERMINATE:
        return {"level": "NOT_APPLICABLE", "basis": ["Indeterminate interval"]}
    levels = ["HIGH", "MEDIUM", "LOW"]
    drops, basis = 0, []
    if any(s.classification == INDETERMINATE for s in segments):
        drops += 1
        basis.append("an Indeterminate portion inside the interval")
    if claim == CANDIDATE:
        margins = [(s.margin, s.load) for s in segments if s.classification == CANDIDATE and s.load]
        if margins and min(m / ld for m, ld in margins) < STRONG_MARGIN:
            drops += 1
            basis.append("smallest candidate margin below 25 % of load")
    if upper is None or upper - lower > TRANSITION_LIMIT.total_seconds():
        drops += 1
        basis.append("transition uncertainty above 15 minutes (or an open bound)")
    return {"level": levels[min(drops, 2)], "basis": basis or ["no reduction"]}


def _key_suffix(inputs: AnalyticInputSet) -> str:
    return "" if inputs.cohort.status != "SELECTED_EXPLICIT" else f":cohort:{inputs.cohort.identity()[:16]}"


def _intervals(index: _Index, asset: str) -> list[IntervalAssessment]:
    inputs = index.inputs
    times = sorted({r.placed_at for r in index.by_channel.get((GEN_STATE, asset), [])}
                   | {r.interval_end for r in index.by_channel.get((GEN_POWER, asset), []) if r.interval_end})
    states = [(t, *_state(index, asset, t)) for t in times]
    on_idx = [i for i, s in enumerate(states) if s[1] == "ON"]
    runs: list[list[int]] = []
    for i in on_idx:
        if runs and not any(states[k][1] == "OFF" for k in range(runs[-1][-1] + 1, i)):
            runs[-1].append(i)
        else:
            runs.append([i])
    out = []
    for run in runs:
        first_on, last_on = states[run[0]][0], states[run[-1]][0]
        if not inputs.window.contains(first_on):
            continue
        before = [s for s in states[:run[0]] if s[1] == "OFF"]
        after = [s for s in states[run[-1] + 1:] if s[1] == "OFF"]
        off_before = before[-1][0] if before else None
        off_after = after[0][2] if after else None
        ids: set[str] = set()
        for i in range(run[0], run[-1] + 1):
            ids |= states[i][3]
        if before:
            ids |= before[-1][3]
        if after:
            ids |= after[0][3]
        segments: list[Segment] = []
        if len(run) == 1:
            p = _evaluate(index, first_on, first_on, first_on, first_on)
            segments.append(_combine(p, p, first_on, first_on))
        for i, j in zip(run, run[1:]):
            a, b = states[i][0], states[j][0]
            gap = (b - a) > CONTINUITY_TOLERANCE or any(states[k][1] == "UNOBSERVED" for k in range(i + 1, j))
            if gap:
                segments.append(Segment(a, b, False, INDETERMINATE, None,
                                        missing=["generator state not observed (gap over 20 minutes or unobserved)"]))
                continue
            limits = _segment_limits(index, a, b)
            if limits:
                segments.append(Segment(a, b, True, INDETERMINATE, None, missing=sorted(
                    {f"{x.role}: {x.kind} between {iso(x.start)} and {iso(x.end)}" for x in limits}),
                    ids={e for x in limits for e in x.evidence_ids}))
                continue
            segments.extend(_segments(index, a, b, first_on))
        for s in segments:
            ids |= s.ids
        out.append(_interval(inputs, asset, first_on, last_on, off_before, off_after, segments, ids, index))
    return out


def _interval(inputs: AnalyticInputSet, asset: str, first_on: datetime, last_on: datetime,
              off_before: datetime | None, off_after: datetime | None, segments: list[Segment], ids: set[str],
              index: _Index) -> IntervalAssessment:
    classes = [s.classification for s in segments]
    if classes and all(c == NECESSARY for c in classes):
        claim = NECESSARY
    elif CANDIDATE in classes:
        claim = CANDIDATE
    else:
        claim = INDETERMINATE
    lower = sum(s.seconds for s in segments if s.observed)
    upper = None if off_before is None or off_after is None else int((off_after - off_before).total_seconds())

    def total(c: str) -> int:
        return sum(s.seconds for s in segments if s.classification == c)

    limits = []
    if off_before is None:
        limits.append("OPEN_BOUND: no OFF evidence before the interval in the read range")
    if off_after is None:
        limits.append("OPEN_BOUND: no OFF evidence after the interval in the read range")
    runtime, runtime_control, _ = index.control(CONTROL_MINIMUM_RUNTIME, first_on)
    controls_used = sorted({c.foundation_revision_id for c in inputs.controls
                            if c.effective(first_on) or (off_after and c.effective(off_after))}, key=str)
    result = {
        "analytic_id": ANALYTIC_ID, "model_version": MODEL_VERSION, "generator_asset_id": asset,
        "claim_level": claim,
        "interval": {"first_on": iso(first_on), "last_on": iso(last_on), "off_before": iso(off_before),
                     "off_after": iso(off_after), "lower_minutes": _num(Fraction(lower, 60)),
                     "upper_minutes": None if upper is None else _num(Fraction(upper, 60))},
        "portions_minutes": {"candidate": _num(Fraction(total(CANDIDATE), 60)),
                             "necessary": _num(Fraction(total(NECESSARY), 60)),
                             "indeterminate": _num(Fraction(total(INDETERMINATE), 60))},
        "candidate_bound": ("the candidate duration is the sum of Candidate segments only; never the whole "
                            "interval" if claim == CANDIDATE else None),
        "binding_constraints": sorted({s.binding for s in segments if s.binding}),
        "segments": [s.payload() for s in segments],
        "confidence": _confidence(claim, segments, upper, lower),
        "limitations": limits,
        "alternatives": {
            "operator_command": "UNAVAILABLE: the measurement-only S2 V3 path carries no command record; no "
                                "command record observed, which is not evidence that no command occurred",
            "minimum_runtime": (f"configured {runtime_control.value} min ({runtime_control.source}); Candidate "
                                "withheld where possibly within it; no policy Necessary claim"
                                if runtime is not None else "not configured; not assessed"),
            "fuel_and_money": "UNAVAILABLE in S3: no fuel quantity, saving or money claim",
        },
        "foundation_revision_ids": [str(x) for x in controls_used],
    }
    evidence = tuple(sorted(ids))
    key = f"{ANALYTIC_ID}:interval:{asset}:{iso(first_on)}{_key_suffix(inputs)}"
    basis = sha256_json({"model_version": MODEL_VERSION, "evidence": [[e, index.digest.get(e)] for e in evidence],
                         "controls": [c.payload() for c in inputs.controls], "result": result})
    return IntervalAssessment(key, inputs.window.start, inputs.window.end, claim, result, evidence, basis)


def _unbound_spans(inputs: AnalyticInputSet, role: str) -> list[tuple[datetime, datetime]]:
    """Parts of the window where no selected binding set binds `role` (a missing-role limit)."""
    spans, cursor = [], inputs.window.start
    bound = sorted((b.valid_from, b.valid_to or inputs.window.end) for b in inputs.bindings if b.role == role)
    for lo, hi in bound:
        if hi <= cursor:
            continue
        if lo > cursor:
            spans.append((cursor, min(lo, inputs.window.end)))
        cursor = max(cursor, hi)
        if cursor >= inputs.window.end:
            break
    if cursor < inputs.window.end:
        spans.append((cursor, inputs.window.end))
    return [(lo, hi) for lo, hi in spans if lo < hi]


# Indeterminate for a modelling reason, not for missing, poor-quality or conflicting evidence.
_NOT_EVIDENCE_GAPS = ("transition inside the segment", "possibly within the configured minimum runtime",
                      "battery inside the 10-point", "capability margin inside")


def assess(inputs: AnalyticInputSet) -> WindowAssessment:
    """The `dispatch-3` window and interval assessments for one input set."""
    if inputs.model_version != MODEL_VERSION:
        raise ValueError(f"input set is for {inputs.model_version}, not {MODEL_VERSION}")
    index = _Index(inputs)
    intervals: list[IntervalAssessment] = []
    limitations: list[str] = list(inputs.configuration_limits)
    if inputs.cohort.usable:
        for asset in sorted({str(r.asset_id) for r in inputs.readings if r.role in (GEN_STATE, GEN_POWER)}):
            intervals.extend(_intervals(index, asset))
    else:
        limitations.append(f"AMBIGUOUS_COHORT: {inputs.cohort.reason}" if inputs.cohort.status == "AMBIGUOUS"
                           else f"NO_COHORT: {inputs.cohort.reason}")
    for role in (PV_AVAILABLE, DISCHARGE):
        for lo, hi in _unbound_spans(inputs, role):
            limitations.append(f"MISSING_ROLE: {role} is not bound in the selected role set over "
                               f"{iso(lo)}..{iso(hi)}; Candidate is unavailable there")
    for limit in inputs.cohort.limits:
        limitations.append(f"{limit.kind}: {limit.role} {iso(limit.start)}..{iso(limit.end)} "
                           f"({', '.join(limit.evidence_ids)})")
    if inputs.cohort.usable and not any(r.role in (GEN_STATE, GEN_POWER) for r in inputs.readings):
        limitations.append("NO_GENERATOR_STATE: no accepted generator state or output in the cohort")
    for i in intervals:
        for seg in i.result["segments"]:
            gaps = [m for m in seg["missing"] if not m.startswith(_NOT_EVIDENCE_GAPS)]
            if seg["classification"] == INDETERMINATE and gaps:
                limitations.append(f"EVIDENCE_GAP: interval from {i.result['interval']['first_on']} is "
                                   f"Indeterminate over {seg['start']}..{seg['end']}: {'; '.join(gaps)}")
    generator_ambiguous = any(x.role in (GEN_STATE, GEN_POWER) and x.start < inputs.window.end
                              and inputs.window.start <= x.end for x in inputs.cohort.limits)
    if generator_ambiguous:
        limitations.append("GENERATOR_SERIES_AMBIGUOUS: generator state reports are out of sequence order or "
                           "overlapping; intervals cannot be reconstructed over those spans")
    if not inputs.cohort.usable or generator_ambiguous:
        claim = WINDOW_INDETERMINATE
    elif limitations or any(i.result["limitations"] for i in intervals):
        claim = WINDOW_LIMITED
    else:
        claim = WINDOW_COMPLETE
    result = {
        "analytic_id": ANALYTIC_ID, "model_version": MODEL_VERSION, "window": inputs.window.payload(),
        "read_range": inputs.read_range.payload(), "claim_level": claim, "cohort": inputs.cohort.payload(),
        "role_coverage": inputs.role_coverage, "role_sets": list(inputs.role_sets),
        "limitations": limitations,
        "intervals": [{"assessment_key": i.assessment_key, "claim_level": i.claim_level,
                       "first_on": i.result["interval"]["first_on"]} for i in intervals],
        "counts": {c: sum(1 for i in intervals if i.claim_level == c) for c in (NECESSARY, CANDIDATE, INDETERMINATE)},
    }
    key = f"{ANALYTIC_ID}:window:{iso(inputs.window.start)}{_key_suffix(inputs)}"
    basis = sha256_json({"model_version": MODEL_VERSION, "input_sha256": inputs.input_sha256, "result": result})
    return WindowAssessment(key, claim, result, basis, tuple(intervals))
