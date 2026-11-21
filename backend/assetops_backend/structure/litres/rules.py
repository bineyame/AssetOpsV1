"""4d unit 1 (spec §2; D-4D.2 to D-4D.15): the monthly litre split, pure.

A litre is the generator's measured output in a 5-minute slot at the declared fuel curve (A2's slot rule, through
`LitreInputs.use`). `necessary_l` is every litre of the month less the CANDIDATE spans' litres (D-4D.11), so running
dispatch-3.2 could not judge or did not classify is never candidate (D-4D.3). `unexplained_l` is the tank's fuel
between two dips (opening plus deliveries less closing) less the modelled litres of the dip window (D-4D.5, D-4D.7).
Exact in `Fraction` until one rounding to the millilitre at the end (D-4D.6). Anything missing gives no figure, named
by its note in `NOTES` order; unknown is never zero.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from fractions import Fraction
from types import MappingProxyType
from typing import Any

from assetops_backend.structure.evaluate import ORIGIN_UNKNOWN, LeafValue, Missing

LITRE_ORDER = ("necessary_l", "candidate_l", "unexplained_l")        # registry order (P4)
CLAIMS = ("NECESSARY", "CANDIDATE_AVOIDABLE", "INDETERMINATE")       # dispatch-3.2's strings (D-4D.13; test 9)
NECESSARY, CANDIDATE, INDETERMINATE = CLAIMS
EDGE = timedelta(hours=24)                 # how far outside the month a dip may lie (D-4D.5)
SLOT = timedelta(minutes=5)                # A2's slot (fuel_balance.rules)
QUANTUM = Decimal("0.001")                 # one millilitre; the only rounding, at the end (D-4D.6)
DAY_STATES = ("ASSESSED", "NOT_ASSESSED", "UNAVAILABLE", "NO_READINGS")
NOTES = ("MONTH_OPEN", "GENERATOR_OR_TANK_NOT_DECLARED", "NO_RUNNING_RECORD", "RUNNING_RECORD_GAP",
         "DISPATCH_NOT_ASSESSED", "SPANS_OVERLAP", "SPAN_CLASS_UNKNOWN", "FUEL_CURVE_MISSING",
         "GENERATOR_USE_INCOMPLETE", "NO_LOAD_RATE_MISSING", "TANK_DIPS_MISSING", "TANK_DIPS_CONFLICT")  # this precedence
CAUSE_OF: Mapping[str, str] = MappingProxyType({
    "DISPATCH_NOT_ASSESSED": "NOT_CALCULATED_YET", "SPANS_OVERLAP": "NOT_CALCULATED_YET",
    "SPAN_CLASS_UNKNOWN": "NOT_CALCULATED_YET"})                                       # else NOT_RECEIVED
ASSESSED, NOT_ASSESSED, UNAVAILABLE, NO_READINGS = DAY_STATES
ONE_EACH, NOT_ONE_EACH = "ONE_EACH", "NOT_ONE_EACH"
TANK_DIP, FUEL_DELIVERY = "TANK_DIP", "FUEL_DELIVERY"
MODELLED = "MODELLED"

(MONTH_OPEN, NOT_DECLARED, NO_RUNNING_RECORD, RUNNING_RECORD_GAP, DISPATCH_NOT_ASSESSED, SPANS_OVERLAP,
 SPAN_CLASS_UNKNOWN, FUEL_CURVE_MISSING, USE_INCOMPLETE, NO_LOAD_RATE_MISSING, TANK_DIPS_MISSING,
 TANK_DIPS_CONFLICT) = NOTES

_DAY = timedelta(days=1)
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class RunSpan:            # one dispatch-3.2 segment: [start, end), UTC
    start: datetime
    end: datetime
    claim: str            # one of CLAIMS, or anything else (D-4D.13)


@dataclass(frozen=True)
class DispatchDay:        # one UTC day as select_dispatch_days_on gives it at known_at
    day: date
    state: str
    run_id: str | None
    spans: tuple[RunSpan, ...]   # () unless ASSESSED


@dataclass(frozen=True)
class SpanUse:            # A2's slot rule over [a, b): fuel_balance.rules.use_from_readings
    kwh: Fraction | None
    idle_seconds: int | None


@dataclass(frozen=True)
class FuelCurve:
    sfc: Fraction | None
    sfc_ref: str | None           # litres per kWh, "foundation:<revision id>"
    no_load: Fraction | None
    no_load_ref: str | None       # litres per hour at zero output
    valid: tuple[datetime, datetime | None] | None   # where every chosen revision is in force (D-4D.14); None: no sfc


@dataclass(frozen=True)
class TankRecord:
    kind: str                     # FUEL_DELIVERY | TANK_DIP
    occurred_at: datetime
    litres: Decimal
    ref: str                      # the record's root id


@dataclass(frozen=True)
class LitreInputs:
    month: str
    lo: datetime                  # month_window's UTC instants
    hi: datetime
    known_at: datetime
    assets: str                   # ONE_EACH | NOT_ONE_EACH (active GENERATOR and FUEL_TANK)
    days: tuple[DispatchDay, ...]  # every UTC day meeting [lo - EDGE, hi + EDGE), in order
    use: Callable[[datetime, datetime], SpanUse]   # bound by the adapter to the Site's readings; a, b on the grid
    held: Callable[[datetime, datetime], bool]     # any generator power or state reading with instant in (a, b]
    curve: FuelCurve
    tank: tuple[TankRecord, ...]  # the one tank's records with lo - EDGE <= occurred_at < hi + EDGE


@dataclass(frozen=True)
class LitreMonth:
    values: Mapping[str, LeafValue]              # LITRE_ORDER order
    indeterminate_l: Decimal | None              # necessary_l less the NECESSARY spans' litres (D-4D.3, D-4D.11)
    window: tuple[datetime, datetime] | None     # the dip window [up(t_o), up(t_c)), when found
    burned_l: Decimal | None
    modelled_window_l: Decimal | None


# --- slots, pieces and spans (spec §2.2) -------------------------------------------------------------------------------

def up(t: datetime) -> datetime:
    """The first instant on the 5-minute UTC grid at or after `t`."""
    base = _EPOCH + ((t - _EPOCH) // SLOT) * SLOT
    return base if base == t else base + SLOT


def _midnight(d: date) -> datetime:
    return datetime.combine(d, time(), timezone.utc)


def _meets(d: date, a: datetime, b: datetime) -> bool:
    start = _midnight(d)
    return start < b and a < start + _DAY


def _pieces(a: datetime, b: datetime) -> list[tuple[datetime, datetime]]:
    """`[max(a, d), min(b, d + 1 day))` for each UTC day `d` meeting `[a, b)`, in order."""
    out = []
    d = a.astimezone(timezone.utc).date()
    while (start := _midnight(d)) < b:
        if start + _DAY > a:
            out.append((max(a, start), min(b, start + _DAY)))
        d += _DAY
    return out


@dataclass(frozen=True)
class _Span:
    start: datetime
    end: datetime
    claim: str
    run_id: str | None


@dataclass(frozen=True)
class _Litres:
    note: str | None              # USE_INCOMPLETE | NO_LOAD_RATE_MISSING | None
    litres: Fraction
    idle: bool                    # some piece had idle seconds


def _piece(inp: LitreInputs, a: datetime, b: datetime) -> _Litres:
    u = inp.use(a, b)
    if u.kwh is None or u.idle_seconds is None:
        return _Litres(USE_INCOMPLETE, Fraction(0), False)
    idle = u.idle_seconds > 0
    if idle and inp.curve.no_load is None:
        return _Litres(NO_LOAD_RATE_MISSING, Fraction(0), True)
    assert inp.curve.sfc is not None
    litres = inp.curve.sfc * Fraction(u.kwh) + (inp.curve.no_load or Fraction(0)) * Fraction(u.idle_seconds, 3600)
    return _Litres(None, litres, idle)


def _sum(inp: LitreInputs, ranges: Iterable[tuple[datetime, datetime]]) -> _Litres:
    """Σ litres over the ranges; an incomplete one first, then one needing the idle rate, gives no sum."""
    parts = [_piece(inp, a, b) for a, b in ranges]
    for note in (USE_INCOMPLETE, NO_LOAD_RATE_MISSING):
        if any(p.note == note for p in parts):
            return _Litres(note, Fraction(0), False)
    return _Litres(None, sum((p.litres for p in parts), Fraction(0)), any(p.idle for p in parts))


def _spans(inp: LitreInputs, a: datetime, b: datetime) -> list[_Span]:
    """Every ASSESSED day's spans clipped to `[max(up(s), a), min(up(e), b))`, non-empty, sorted (P5)."""
    out = []
    for day in inp.days:
        if day.state != ASSESSED:
            continue
        for s in day.spans:
            start, end = max(up(s.start), a), min(up(s.end), b)
            if start < end:
                out.append(_Span(start, end, s.claim, day.run_id))
    out.sort(key=lambda s: (s.start, s.end, s.claim))
    return out


def _overlap(spans: list[_Span]) -> bool:
    reach: datetime | None = None
    for s in spans:
        if reach is not None and s.start < reach:
            return True
        reach = s.end if reach is None else max(reach, s.end)
    return False


def _days(inp: LitreInputs, a: datetime, b: datetime) -> list[DispatchDay]:
    return [d for d in inp.days if _meets(d.day, a, b)]


def _gap(inp: LitreInputs, a: datetime, b: datetime) -> bool:
    """Rule 4 (D-4D.10): a day of `[a, b)` with no readings, or with no generator reading in its part of the range."""
    for d in _days(inp, a, b):
        start = _midnight(d.day)
        if d.state == NO_READINGS or not inp.held(max(a, start), min(b, start + _DAY)):
            return True
    return False


def _not_assessed(inp: LitreInputs, a: datetime, b: datetime) -> bool:
    return any(d.state in (NOT_ASSESSED, UNAVAILABLE) for d in _days(inp, a, b))


def _checks(inp: LitreInputs, parts: list[tuple[datetime, datetime]], dispatch: tuple[datetime, datetime]
            ) -> str | None:
    """Rules 4 to 10 over `parts` (rule 5 over `dispatch`); the first that applies."""
    if any(_gap(inp, a, b) for a, b in parts):
        return RUNNING_RECORD_GAP
    if _not_assessed(inp, *dispatch):
        return DISPATCH_NOT_ASSESSED
    spans = [_spans(inp, a, b) for a, b in parts]
    if any(_overlap(s) for s in spans):
        return SPANS_OVERLAP
    if any(s.claim not in CLAIMS for group in spans for s in group):
        return SPAN_CLASS_UNKNOWN
    if inp.curve.sfc is None:
        return FUEL_CURVE_MISSING
    return _sum(inp, [p for a, b in parts for p in _pieces(a, b)]).note


# --- values (D-4D.6, D-4D.8, D-4D.9) -----------------------------------------------------------------------------------

def q(x: Fraction) -> Decimal:
    with localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN)):
        value = (Decimal(x.numerator) / Decimal(x.denominator)).quantize(QUANTUM)
    return value.copy_abs() if value == 0 else value


def _unique(items: Iterable[str | None]) -> tuple[str, ...]:
    out: list[str] = []
    for item in items:
        if item is not None and item not in out:
            out.append(item)
    return tuple(out)


def _sources(spans: Iterable[_Span], curve: FuelCurve, idle: bool, records: Iterable[TankRecord] = ()
             ) -> tuple[str, ...]:
    run_ids = sorted({s.run_id for s in spans if s.run_id is not None})
    fuel = sorted(records, key=lambda r: (r.occurred_at, r.ref))
    return _unique([f"dispatch-run:{r}" for r in run_ids] + [curve.sfc_ref, curve.no_load_ref if idle else None]
                   + [f"fuel-record:{r.ref}" for r in fuel])


def _valued(value: Fraction, sources: tuple[str, ...]) -> LeafValue:
    return LeafValue(q(value), MODELLED, sources, None, None, None, (ORIGIN_UNKNOWN,))


def _absent(fb: Any, note: str) -> LeafValue:
    return LeafValue(None, "NOT_AVAILABLE", (), None,
                     Missing(fb.kind, fb.family, CAUSE_OF.get(note, "NOT_RECEIVED"), None, (), fb.words, None, note),
                     None)


def _all_absent(note: str, filled_by: Mapping[str, Any]) -> LitreMonth:
    return LitreMonth(MappingProxyType({leaf: _absent(filled_by[leaf], note) for leaf in LITRE_ORDER}),
                      None, None, None, None)


# --- the month (spec §2.3) -------------------------------------------------------------------------------------------

def _month_note(inp: LitreInputs) -> str | None:
    lo, hi = inp.lo, inp.hi
    if inp.known_at < hi:                                              # 1.
        return MONTH_OPEN
    if inp.assets != ONE_EACH:                                         # 2.
        return NOT_DECLARED
    if not inp.held(lo, hi):                                           # 3. (D-4D.10)
        return NO_RUNNING_RECORD
    return _checks(inp, [(lo, hi)], (lo - _DAY, hi))                   # 4. to 10.


def _at(dips: list[TankRecord], at: datetime) -> list[TankRecord]:
    return [r for r in dips if r.occurred_at == at]


def month_litres(inp: LitreInputs, filled_by: Mapping[str, Any]) -> LitreMonth:
    note = _month_note(inp)
    if note is not None:
        return _all_absent(note, filled_by)
    lo, hi, curve = inp.lo, inp.hi, inp.curve
    total = _sum(inp, _pieces(lo, hi))                                 # 11.
    spans = _spans(inp, lo, hi)
    candidate = [s for s in spans if s.claim == CANDIDATE]
    c = _sum(inp, [(s.start, s.end) for s in candidate])
    n_spans = _sum(inp, [(s.start, s.end) for s in spans if s.claim == NECESSARY])
    for part in (c, n_spans):                     # a span is a part of a complete piece; kept for a non-additive `use`
        if part.note is not None:
            return _all_absent(part.note, filled_by)
    necessary = total.litres - c.litres
    values = {"necessary_l": _valued(necessary, _sources(spans, curve, total.idle)),
              "candidate_l": _valued(c.litres, _sources(candidate, curve, c.idle))}
    indeterminate = q(necessary - n_spans.litres)
    fb = filled_by["unexplained_l"]

    def without(note_: str, window: tuple[datetime, datetime] | None = None) -> LitreMonth:
        return LitreMonth(MappingProxyType({**values, "unexplained_l": _absent(fb, note_)}), indeterminate, window,
                          None, None)

    dips = [r for r in inp.tank if r.kind == TANK_DIP]                 # 12. (D-4D.5; half-open close, R11)
    before = [r.occurred_at for r in dips if lo - EDGE <= r.occurred_at <= lo]
    after = [r.occurred_at for r in dips if hi <= r.occurred_at < hi + EDGE]
    if not before or not after:
        return without(TANK_DIPS_MISSING)
    t_o, t_c = max(before), min(after)
    opening, closing = _at(dips, t_o), _at(dips, t_c)
    if len({r.litres for r in opening}) > 1 or len({r.litres for r in closing}) > 1:
        return without(TANK_DIPS_CONFLICT)
    w = (up(t_o), up(t_c))                                             # 13.
    if curve.valid is None or w[0] < curve.valid[0] or (curve.valid[1] is not None and curve.valid[1] < w[1]):
        return without(FUEL_CURVE_MISSING, w)                          # D-4D.14
    outside = [p for p in ((w[0], min(lo, w[1])), (max(hi, w[0]), w[1])) if p[0] < p[1]]
    note = _checks(inp, outside, (w[0] - _DAY, w[1]))
    if note is not None:
        return without(note, w)
    deliveries = [r for r in inp.tank if r.kind == FUEL_DELIVERY and t_o <= r.occurred_at < t_c]   # 14.
    modelled = _sum(inp, _pieces(*w))
    if modelled.note is not None:
        return without(modelled.note, w)
    burned = Fraction(opening[0].litres) + sum((Fraction(r.litres) for r in deliveries), Fraction(0)) \
        - Fraction(closing[0].litres)
    unexplained = burned - modelled.litres                             # D-4D.7: a negative value is kept
    values["unexplained_l"] = _valued(unexplained, _sources(_spans(inp, *w), curve, modelled.idle,
                                                           [*opening, *deliveries, *closing]))
    return LitreMonth(MappingProxyType(values), indeterminate, w, q(burned), q(modelled.litres))


__all__ = [
    "CANDIDATE", "CAUSE_OF", "CLAIMS", "DAY_STATES", "EDGE", "INDETERMINATE", "LITRE_ORDER", "NECESSARY", "NOTES",
    "QUANTUM", "SLOT", "DispatchDay", "FuelCurve", "LitreInputs", "LitreMonth", "RunSpan", "SpanUse", "TankRecord",
    "month_litres", "q", "up",
]
