"""4d (spec `specs/4d-litre-split/spec.md` rev 2; rulings D-4D.1 to D-4D.15): the monthly litre split.

No database. Every expected value is spec §5's hand-computed literal (W2), typed here; none is derived from the code
under test. The fixture's `use` and `held` are this file's own fakes over KOBO-OCT's running slots (spec §5): a
running slot is 20 kW for 5 minutes (5/3 kWh), an idle slot 0 kWh and 300 idle seconds.
"""
from __future__ import annotations

import ast
import bisect
import dataclasses
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from assetops_backend.structure.evaluate import LeafValue, Missing
from assetops_backend.structure.litres import rules
from assetops_backend.structure.litres.rules import (
    DispatchDay, FuelCurve, LitreInputs, LitreMonth, RunSpan, SpanUse, TankRecord, UnitFuel, month_litres)
from assetops_backend.structure.registry import REGISTRIES

D = Decimal
UTC = timezone.utc
EAT = timezone(timedelta(hours=3))
MG = REGISTRIES["MINI_GRID"]
FB = {f: MG.row(f).filled_by for f in ("necessary_l", "candidate_l", "unexplained_l")}
LEAVES = ("necessary_l", "candidate_l", "unexplained_l")
SLOT = timedelta(minutes=5)
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
LO = datetime(2026, 9, 30, 21, 0, tzinfo=UTC)
HI = datetime(2026, 10, 31, 21, 0, tzinfo=UTC)
KNOWN_AT = datetime(2026, 11, 20, 8, 0, tzinfo=UTC)
SFC, NL = "foundation:sfc-1", "foundation:nl-1"
NEC, CAND, IND = "NECESSARY", "CANDIDATE_AVOIDABLE", "INDETERMINATE"
NR, NCY = "NOT_RECEIVED", "NOT_CALCULATED_YET"


def local(y: int, m: int, d: int, hh: int = 0, mm: int = 0) -> datetime:
    return datetime(y, m, d, hh, mm, tzinfo=EAT)


def span(y: int, m: int, d: int, h0: int, m0: int, h1: int, m1: int, claim: str) -> RunSpan:
    start = local(y, m, d, h0, m0).astimezone(UTC)
    end = (local(y, m, d, 0) + timedelta(hours=h1, minutes=m1)).astimezone(UTC)
    return RunSpan(start, end, claim)


# --- KOBO-OCT (spec §5) -----------------------------------------------------------------------------------------------

def kobo_spans() -> list[RunSpan]:
    out = [span(2026, 10, d, 18, 0, 24, 0, NEC) for d in range(1, 25)]
    out.append(span(2026, 10, 25, 18, 0, 20, 0, IND))
    out += [span(2026, 10, d, 7, 0, 13, 0, CAND) for d in range(1, 12)]
    return out


def slots_of(spans: list[RunSpan]) -> set[datetime]:
    """The slots whose start lies in a span (spec §5 "Running")."""
    out: set[datetime] = set()
    for s in spans:
        t = s.start + (-(s.start - EPOCH) % SLOT)  # the first slot start on the grid at or after it
        while t < s.end:
            out.add(t)
            t += SLOT
    return out


@dataclasses.dataclass
class World:
    spans: list[RunSpan]
    running: set[datetime]
    idle: set[datetime] = dataclasses.field(default_factory=set)
    states: dict[date, str] = dataclasses.field(default_factory=dict)
    known_at: datetime = KNOWN_AT
    assets: str = "ONE_EACH"
    curve: FuelCurve = FuelCurve(Fraction(1, 4), SFC, Fraction(2), NL,
                                 (datetime(2026, 1, 1, tzinfo=UTC), None))
    tank: list[TankRecord] = dataclasses.field(default_factory=list)
    held: object = None           # None: always True
    incomplete: tuple[datetime, datetime] | None = None  # `use` gives kwh None for any range meeting it

    def use(self, a: datetime, b: datetime) -> SpanUse:
        if self.incomplete is not None and a < self.incomplete[1] and self.incomplete[0] < b:
            return SpanUse(None, 0)
        run, idle = sorted(self.running), sorted(self.idle)
        n = bisect.bisect_left(run, b) - bisect.bisect_left(run, a)
        i = bisect.bisect_left(idle, b) - bisect.bisect_left(idle, a)
        return SpanUse(Fraction(5, 3) * n, 300 * i)

    def inputs(self) -> LitreInputs:
        days = []
        d = date(2026, 9, 29)
        while d <= date(2026, 11, 1):
            state = self.states.get(d, "ASSESSED")
            mid = datetime(d.year, d.month, d.day, tzinfo=UTC)
            spans = tuple(s for s in self.spans if mid <= s.start < mid + timedelta(days=1)) \
                if state == "ASSESSED" else ()
            days.append(DispatchDay(d, state, f"run-{d.month:02d}-{d.day:02d}" if state == "ASSESSED" else None,
                                    spans))
            d += timedelta(days=1)
        held = self.held if self.held is not None else (lambda a, b: True)
        return LitreInputs("2026-10", LO, HI, self.known_at, self.assets, tuple(days),
                           (UnitFuel("gen", self.use, self.curve),), held, tuple(self.tank))  # D-DD.113: one unit


def kobo_tank() -> list[TankRecord]:
    return [TankRecord("TANK_DIP", local(2026, 10, 1).astimezone(UTC), D("500"), "dip-open"),
            TankRecord("FUEL_DELIVERY", local(2026, 10, 1, 9).astimezone(UTC), D("400"), "del-1"),
            TankRecord("FUEL_DELIVERY", local(2026, 10, 11, 9).astimezone(UTC), D("400"), "del-2"),
            TankRecord("FUEL_DELIVERY", local(2026, 10, 21, 9).astimezone(UTC), D("380"), "del-3"),
            TankRecord("TANK_DIP", local(2026, 11, 1).astimezone(UTC), D("500"), "dip-close")]


def kobo(extra_spans: list[RunSpan] | None = None, running_extra: list[RunSpan] | None = None) -> World:
    spans = kobo_spans() + list(extra_spans or [])
    return World(spans, slots_of(spans) | slots_of(list(running_extra or [])), tank=kobo_tank())


def runs(*days: str) -> tuple[str, ...]:
    return tuple(f"dispatch-run:run-{d}" for d in days)


def oct_runs(last: int) -> tuple[str, ...]:
    return runs(*[f"10-{d:02d}" for d in range(1, last + 1)])


FUEL = tuple(f"fuel-record:{r}" for r in ("dip-open", "del-1", "del-2", "del-3", "dip-close"))
KOBO_SOURCES = {"necessary_l": oct_runs(25) + (SFC,), "candidate_l": oct_runs(11) + (SFC,),
                "unexplained_l": oct_runs(25) + (SFC,) + FUEL}


def run(w: World) -> LitreMonth:
    return month_litres(w.inputs(), FB)


def valued(lv: LeafValue, literal: str, sources: tuple[str, ...] | None = None) -> None:
    assert lv.value == D(literal) and format(lv.value, "f") == literal, (lv.value, literal)
    assert (lv.evidence, lv.coverage, lv.missing, lv.currency, lv.origins) == ("MODELLED", None, None, None,
                                                                               ("unknown",))
    if sources is not None:
        assert lv.sources == sources, lv.sources


def absent(lv: LeafValue, leaf: str, note: str, cause: str = NR) -> None:
    fb = FB[leaf]
    assert lv == LeafValue(None, "NOT_AVAILABLE", (), None,
                           Missing(fb.kind, fb.family, cause, None, (), fb.words, None, note), None), (leaf, lv)
    assert lv.origins == ()


def all_absent(m: LitreMonth, note: str, cause: str = NR) -> None:
    assert tuple(m.values) == LEAVES
    for leaf in LEAVES:
        absent(m.values[leaf], leaf, note, cause)
    assert (m.indeterminate_l, m.burned_l, m.modelled_window_l) == (None, None, None)


# --- test 1: KOBO-OCT ---------------------------------------------------------------------------------------------------

def test_1_kobo_oct_field_by_field() -> None:
    m = run(kobo())
    assert tuple(m.values) == LEAVES
    valued(m.values["necessary_l"], "730.000", KOBO_SOURCES["necessary_l"])
    valued(m.values["candidate_l"], "330.000", KOBO_SOURCES["candidate_l"])
    valued(m.values["unexplained_l"], "120.000", KOBO_SOURCES["unexplained_l"])
    assert format(m.indeterminate_l, "f") == "10.000"
    assert m.window == (LO, HI)
    assert format(m.burned_l, "f") == "1180.000" and format(m.modelled_window_l, "f") == "1060.000"


# --- test 2: the variants -----------------------------------------------------------------------------------------------

def v1() -> World:
    """A NECESSARY hour on 26 Oct whose slots run at 0 kW with 300 idle seconds each."""
    hour = span(2026, 10, 26, 18, 0, 19, 0, NEC)
    w = kobo([hour])
    w.idle = slots_of([hour])
    w.running -= w.idle
    return w


def test_v1_idle_slots_use_the_no_load_rate() -> None:
    w = v1()
    m = run(w)
    valued(m.values["necessary_l"], "732.000", oct_runs(26) + (SFC, NL))
    valued(m.values["candidate_l"], "330.000", KOBO_SOURCES["candidate_l"])
    valued(m.values["unexplained_l"], "118.000", oct_runs(26) + (SFC, NL) + FUEL)


def test_v2_idle_without_a_no_load_rate() -> None:
    w = v1()
    w.curve = dataclasses.replace(w.curve, no_load=None, no_load_ref=None)
    all_absent(run(w), "NO_LOAD_RATE_MISSING")


def test_v3_no_rate_needed_without_idle() -> None:
    w = kobo()
    w.curve = dataclasses.replace(w.curve, no_load=None, no_load_ref=None)
    m = run(w)
    for leaf, literal in zip(LEAVES, ("730.000", "330.000", "120.000")):
        valued(m.values[leaf], literal, KOBO_SOURCES[leaf])


def test_v4_incomplete_output_stops_the_month() -> None:
    w = kobo()
    w.incomplete = (local(2026, 10, 3, 7).astimezone(UTC), local(2026, 10, 3, 13).astimezone(UTC))
    all_absent(run(w), "GENERATOR_USE_INCOMPLETE")


def test_v5_no_dip() -> None:
    w = kobo()
    w.tank = [r for r in w.tank if r.kind != "TANK_DIP"]
    m = run(w)
    valued(m.values["necessary_l"], "730.000"), valued(m.values["candidate_l"], "330.000")
    absent(m.values["unexplained_l"], "unexplained_l", "TANK_DIPS_MISSING")
    assert format(m.indeterminate_l, "f") == "10.000" and m.burned_l is None and m.window is None


@pytest.mark.parametrize("closing, literal", [("560", "60.000"), ("440", "180.000"), ("620", "0.000"),
                                              ("700", "-80.000")])
def test_v6_closing_dip(closing: str, literal: str) -> None:
    w = kobo()
    w.tank = [dataclasses.replace(r, litres=D(closing)) if r.ref == "dip-close" else r for r in w.tank]
    valued(run(w).values["unexplained_l"], literal)


def v7() -> World:
    w = kobo([span(2026, 9, 30, 18, 0, 19, 0, NEC)])
    w.tank = [TankRecord("TANK_DIP", local(2026, 9, 30, 18).astimezone(UTC), D("520"), "dip-open")
              if r.ref == "dip-open" else r for r in w.tank]
    return w


def test_v7_opening_dip_before_the_month() -> None:
    m = run(v7())
    valued(m.values["necessary_l"], "730.000", KOBO_SOURCES["necessary_l"])
    valued(m.values["unexplained_l"], "135.000", runs("09-30") + oct_runs(25) + (SFC,) + FUEL)
    assert m.window == (datetime(2026, 9, 30, 15, 0, tzinfo=UTC), HI)
    assert format(m.burned_l, "f") == "1200.000" and format(m.modelled_window_l, "f") == "1065.000"


@pytest.mark.parametrize("state", ["NOT_ASSESSED", "UNAVAILABLE"])
def test_v8_a_day_not_analysed(state: str) -> None:
    w = kobo()
    w.states[date(2026, 10, 12)] = state
    all_absent(run(w), "DISPATCH_NOT_ASSESSED", NCY)


def test_v9_a_day_without_readings() -> None:
    w = kobo()
    w.states[date(2026, 10, 12)] = "NO_READINGS"
    all_absent(run(w), "RUNNING_RECORD_GAP")


def v10(w: World) -> World:
    d = date(2026, 9, 29)
    while d <= date(2026, 11, 1):
        w.states[d] = "NO_READINGS"
        d += timedelta(days=1)
    w.held = lambda a, b: False
    return w


def test_v10_no_running_record() -> None:
    all_absent(run(v10(kobo())), "NO_RUNNING_RECORD")


def test_v11_not_one_generator_and_one_tank() -> None:
    w = v10(kobo())
    w.assets = "NOT_ONE_EACH"
    all_absent(run(w), "GENERATOR_OR_TANK_NOT_DECLARED")


def test_v12_the_month_is_open() -> None:
    w = v10(kobo())
    w.assets = "NOT_ONE_EACH"
    w.known_at = datetime(2026, 10, 31, 20, 59, tzinfo=UTC)
    all_absent(run(w), "MONTH_OPEN")


def test_v13_no_fuel_curve() -> None:
    w = kobo()
    w.curve = dataclasses.replace(w.curve, sfc=None, sfc_ref=None, valid=None)
    all_absent(run(w), "FUEL_CURVE_MISSING")


def test_v14_two_dips_disagree() -> None:
    w = kobo()
    w.tank.append(TankRecord("TANK_DIP", local(2026, 10, 1).astimezone(UTC), D("510"), "dip-open-2"))
    m = run(w)
    valued(m.values["necessary_l"], "730.000"), valued(m.values["candidate_l"], "330.000")
    absent(m.values["unexplained_l"], "unexplained_l", "TANK_DIPS_CONFLICT")


def test_v15_overlapping_spans() -> None:
    all_absent(run(kobo([span(2026, 10, 2, 19, 0, 20, 0, CAND)])), "SPANS_OVERLAP", NCY)


def test_v16_a_delivery_after_the_closing_dip() -> None:
    w = kobo()
    w.tank.append(TankRecord("FUEL_DELIVERY", local(2026, 11, 1, 6).astimezone(UTC), D("100"), "del-4"))
    m = run(w)
    for leaf, literal in zip(LEAVES, ("730.000", "330.000", "120.000")):
        valued(m.values[leaf], literal, KOBO_SOURCES[leaf])


def test_v17_a_span_off_the_grid() -> None:
    m = run(kobo([span(2026, 10, 12, 7, 2, 7, 58, NEC)]))
    valued(m.values["necessary_l"], "734.583"), valued(m.values["candidate_l"], "330.000")
    valued(m.values["unexplained_l"], "115.417")


def test_v18_solar_and_battery_without_generator_columns() -> None:
    w = World([], set(), tank=kobo_tank())
    w.held = lambda a, b: False
    all_absent(run(w), "NO_RUNNING_RECORD")


def test_v19_a_day_with_no_generator_reading() -> None:
    w = kobo()
    d0, d1 = datetime(2026, 10, 28, tzinfo=UTC), datetime(2026, 10, 29, tzinfo=UTC)
    w.held = lambda a, b: not (d0 <= a and b <= d1)
    all_absent(run(w), "RUNNING_RECORD_GAP")


def test_v20_a_delivery_inside_the_window_before_the_month() -> None:
    w = v7()
    w.tank.append(TankRecord("FUEL_DELIVERY", local(2026, 9, 30, 20).astimezone(UTC), D("50"), "del-0"))
    m = run(w)
    valued(m.values["necessary_l"], "730.000")
    fuel = tuple(f"fuel-record:{r}" for r in ("dip-open", "del-0", "del-1", "del-2", "del-3", "dip-close"))
    valued(m.values["unexplained_l"], "185.000", runs("09-30") + oct_runs(25) + (SFC,) + fuel)
    assert format(m.burned_l, "f") == "1250.000" and format(m.modelled_window_l, "f") == "1065.000"


def test_v21_the_day_before_the_month_not_analysed() -> None:
    w = kobo()
    w.states[date(2026, 9, 29)] = "NOT_ASSESSED"
    all_absent(run(w), "DISPATCH_NOT_ASSESSED", NCY)


def test_v22_one_rounding_at_the_end() -> None:
    m = run(kobo([span(2026, 10, 13, 7, 0, 7, 5, NEC), span(2026, 10, 14, 7, 0, 7, 5, NEC)]))
    valued(m.values["necessary_l"], "730.833"), valued(m.values["candidate_l"], "330.000")
    valued(m.values["unexplained_l"], "119.167")


def test_v23_a_class_4d_does_not_know() -> None:
    all_absent(run(kobo([span(2026, 10, 27, 7, 0, 8, 0, "SOMETHING_NEW")])), "SPAN_CLASS_UNKNOWN", NCY)


def test_v24_running_no_span_covers() -> None:
    m = run(kobo(running_extra=[span(2026, 10, 27, 10, 0, 10, 5, NEC)]))
    valued(m.values["necessary_l"], "730.417"), valued(m.values["candidate_l"], "330.000")
    valued(m.values["unexplained_l"], "119.583")
    assert format(m.indeterminate_l, "f") == "10.417"


def test_v25_the_curve_not_in_force_over_the_window() -> None:
    w = v7()
    w.curve = dataclasses.replace(w.curve, valid=(datetime(2026, 9, 30, 18, 0, tzinfo=UTC), None))
    m = run(w)
    valued(m.values["necessary_l"], "730.000"), valued(m.values["candidate_l"], "330.000")
    absent(m.values["unexplained_l"], "unexplained_l", "FUEL_CURVE_MISSING")


def test_v26_the_closing_dip_at_exactly_a_day_after() -> None:
    w = kobo()
    w.tank = [dataclasses.replace(r, occurred_at=local(2026, 11, 2).astimezone(UTC)) if r.ref == "dip-close" else r
              for r in w.tank]
    m = run(w)
    valued(m.values["necessary_l"], "730.000"), valued(m.values["candidate_l"], "330.000")
    absent(m.values["unexplained_l"], "unexplained_l", "TANK_DIPS_MISSING")


# --- test 3: invariants over every valued case ------------------------------------------------------------------------

def _valued_worlds() -> dict[str, World]:
    out = {"KOBO-OCT": kobo(), "V1": v1(), "V7": v7(),
           "V17": kobo([span(2026, 10, 12, 7, 2, 7, 58, NEC)]),
           "V22": kobo([span(2026, 10, 13, 7, 0, 7, 5, NEC), span(2026, 10, 14, 7, 0, 7, 5, NEC)]),
           "V24": kobo(running_extra=[span(2026, 10, 27, 10, 0, 10, 5, NEC)])}
    for closing in ("560", "440", "620", "700"):
        w = kobo()
        w.tank = [dataclasses.replace(r, litres=D(closing)) if r.ref == "dip-close" else r for r in w.tank]
        out[f"V6-{closing}"] = w
    return out


def _q(x: Fraction) -> Decimal:
    return (D(x.numerator) / D(x.denominator)).quantize(D("0.001"))


@pytest.mark.parametrize("name", sorted(_valued_worlds()))
def test_3_invariants(name: str) -> None:
    w = _valued_worlds()[name]
    m = run(w)
    v = {leaf: m.values[leaf].value for leaf in LEAVES}
    total = Fraction(5, 12) * sum(1 for t in w.running if LO <= t < HI) \
        + Fraction(2) * Fraction(300, 3600) * sum(1 for t in w.idle if LO <= t < HI)  # the test's own T(lo, hi)
    assert v["necessary_l"] + v["candidate_l"] == _q(total), name
    assert v["unexplained_l"] + m.modelled_window_l == m.burned_l, name
    for x in (*v.values(), m.indeterminate_l, m.burned_l, m.modelled_window_l):
        assert not (x == 0 and x.is_signed()), (name, x)


# --- test 4: precedence -----------------------------------------------------------------------------------------------

def test_4_month_open_first() -> None:
    w = v10(kobo())
    w.assets, w.known_at = "NOT_ONE_EACH", datetime(2026, 10, 31, 20, 59, tzinfo=UTC)
    w.curve = dataclasses.replace(w.curve, sfc=None, sfc_ref=None, valid=None)
    all_absent(run(w), "MONTH_OPEN")


def test_4_assets_before_the_curve() -> None:
    w = kobo()
    w.assets = "NOT_ONE_EACH"
    w.curve = dataclasses.replace(w.curve, sfc=None, sfc_ref=None, valid=None)
    all_absent(run(w), "GENERATOR_OR_TANK_NOT_DECLARED")


def test_4_overlap_before_an_unknown_class() -> None:
    w = kobo([span(2026, 10, 2, 19, 0, 20, 0, CAND), span(2026, 10, 27, 7, 0, 8, 0, "SOMETHING_NEW")])
    all_absent(run(w), "SPANS_OVERLAP", NCY)


def test_4_notes_and_causes_literal() -> None:
    assert rules.NOTES == ("MONTH_OPEN", "GENERATOR_OR_TANK_NOT_DECLARED", "NO_RUNNING_RECORD", "RUNNING_RECORD_GAP",
                           "DISPATCH_NOT_ASSESSED", "SPANS_OVERLAP", "SPAN_CLASS_UNKNOWN", "FUEL_CURVE_MISSING",
                           "GENERATOR_USE_INCOMPLETE", "NO_LOAD_RATE_MISSING", "TANK_DIPS_MISSING",
                           "TANK_DIPS_CONFLICT")
    assert dict(rules.CAUSE_OF) == {"DISPATCH_NOT_ASSESSED": NCY, "SPANS_OVERLAP": NCY, "SPAN_CLASS_UNKNOWN": NCY}
    assert rules.LITRE_ORDER == LEAVES and rules.EDGE == timedelta(hours=24) and rules.QUANTUM == D("0.001")


# --- test 9: dispatch-3.2's class strings -----------------------------------------------------------------------------

def test_9_claims_are_dispatch_strings() -> None:
    from assetops_backend.analytics import dispatch

    assert rules.CLAIMS == (dispatch.NECESSARY, dispatch.CANDIDATE, dispatch.INDETERMINATE)


# --- test 8: grep -----------------------------------------------------------------------------------------------------

PACKAGE = Path(__file__).resolve().parents[1] / "assetops_backend" / "structure" / "litres"


def _imports(path: Path) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
        elif isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
    return out


def test_8_no_float_no_adapter_and_compositions_only_in_composition() -> None:
    files = sorted(PACKAGE.glob("*.py"))
    assert {p.name for p in files} >= {"__init__.py", "rules.py"}
    for p in files:
        assert "float(" not in p.read_text(encoding="utf-8"), p.name
        mods = _imports(p)
        assert not any(".adapters" in m or m.startswith("adapters") for m in mods), (p.name, mods)
        if p.name != "composition.py":
            assert not mods & {"assetops_backend.fuel_balance.composition",
                               "assetops_backend.analytics.composition"}, p.name


# =====================================================================================================================
# Unit 2 (spec §3): the provider and the wiring; tests 5 to 7
# =====================================================================================================================

from uuid import uuid4  # noqa: E402

from assetops_backend.chain.ports import SiteRef  # noqa: E402
from assetops_backend.structure.litres.source import LitreLeafSource  # noqa: E402
from assetops_backend.structure.sources import LITRE_LEAVES, SOURCE_STATE, ReadContext  # noqa: E402

TENANT = uuid4()
KOBO_REF = SiteRef(TENANT, uuid4(), "KOBO-001", "MINIGRID", "Africa/Nairobi")


class Counting:
    def __init__(self, world: World | None = None) -> None:
        self.calls: list[tuple[str, str, datetime]] = []
        self.world = world or kobo()

    def read(self, site: SiteRef, month: str, known_at: datetime) -> LitreInputs:
        self.calls.append((site.site_code, month, known_at))
        return self.world.inputs()


class Fallback:
    def __init__(self) -> None:
        self.asked: list[str] = []

    def leaf(self, ctx: ReadContext, factor_id: str) -> LeafValue:
        self.asked.append(factor_id)
        return LeafValue(D("1"), "DERIVED", ("fallback",), None, None, None)


def test_5_a_non_litre_factor_goes_to_the_fallback() -> None:
    inputs, fb = Counting(), Fallback()
    src = LitreLeafSource(inputs, fb, lambda: KNOWN_AT)
    got = src.leaf(ReadContext(KOBO_REF, "2026-10", KNOWN_AT), "diesel_price")
    assert got.sources == ("fallback",) and fb.asked == ["diesel_price"] and inputs.calls == []


def test_5_a_pinned_read_costs_one_input_read() -> None:
    inputs = Counting()
    src = LitreLeafSource(inputs, Fallback(), lambda: KNOWN_AT)
    ctx = ReadContext(KOBO_REF, "2026-10", KNOWN_AT)
    got = [src.leaf(ctx, leaf).value for leaf in LEAVES]
    assert [format(v, "f") for v in got] == ["730.000", "330.000", "120.000"]
    assert inputs.calls == [("KOBO-001", "2026-10", KNOWN_AT)]


def test_5_a_live_read_is_never_memoised() -> None:
    inputs = Counting()
    src = LitreLeafSource(inputs, Fallback(), lambda: KNOWN_AT)
    ctx = ReadContext(KOBO_REF, "2026-10", None)
    for leaf in LEAVES:
        src.leaf(ctx, leaf)
    assert inputs.calls == [("KOBO-001", "2026-10", KNOWN_AT)] * 3  # `now()` stands in for known_at


def test_5_the_memo_keeps_at_most_sixteen() -> None:
    inputs = Counting()
    src = LitreLeafSource(inputs, Fallback(), lambda: KNOWN_AT)
    pins = [KNOWN_AT + timedelta(minutes=i) for i in range(17)]
    for k in pins:
        src.leaf(ReadContext(KOBO_REF, "2026-10", k), "necessary_l")
    src.leaf(ReadContext(KOBO_REF, "2026-10", pins[-1]), "candidate_l")   # still held
    src.leaf(ReadContext(KOBO_REF, "2026-10", pins[0]), "candidate_l")    # dropped, read again
    assert len(inputs.calls) == 18


# --- test 7: read alone, and the state rows -------------------------------------------------------------------------

def test_7_product_source_alone_gives_not_connected() -> None:
    from test_4b_money_leaves import fallback

    assert LITRE_LEAVES == frozenset(LEAVES)
    for leaf in LEAVES:
        assert SOURCE_STATE["MINI_GRID"][leaf] == "PROVIDED"
        got = fallback().leaf(ReadContext(KOBO_REF, "2026-10", KNOWN_AT), leaf)
        fb = FB[leaf]
        assert got == LeafValue(None, "NOT_AVAILABLE", (), None,
                                Missing(fb.kind, fb.family, "NOT_CONNECTED", None, (), fb.words, None, None), None)


# --- test 6: the bridge (spec §5; 5b §5.2's world with its step) -----------------------------------------------------

class LakesideInputs:
    """KOBO-OCT for KOBO-001; V11 (no generator and tank declared, no readings) for every other Site."""

    def read(self, site: SiteRef, month: str, known_at: datetime) -> LitreInputs:
        if site.site_code == "KOBO-001":
            return kobo().inputs()
        w = v10(kobo())
        w.assets = "NOT_ONE_EACH"
        return w.inputs()


def _bridge_reads(w: dict):
    from test_3a4_commercial_months import READ_AT
    from test_4b_money_leaves import fallback

    from assetops_backend.structure.money import CommercialLeafSource
    from assetops_backend.structure.read import StructureRead
    from assetops_backend.structure.targets.lines import BudgetLineReader
    from assetops_backend.structure.targets.read import TargetRead

    src = CommercialLeafSource(w["months"], w["store"], LitreLeafSource(LakesideInputs(), fallback(),
                                                                        lambda: READ_AT))
    actual = StructureRead(src, stated=src)
    return actual, TargetRead(BudgetLineReader(w["months"], w["store"]), actual), READ_AT


def _site_bridge(code: str):
    import test_5b_attribution as t5b
    from assetops_backend.structure.attribution.site import site_bridge

    w = t5b._world()
    actual, targets, at = _bridge_reads(w)
    s = t5b.ref(w, code)
    return site_bridge(actual.site_inputs(s, t5b.OCT, at), targets.site(s, t5b.OCT, at))


def shape(row, expected: tuple) -> None:
    """5b's `check_shape`, with `effect` compared as a `Decimal` only: a litre leaf has three places (D-4D.6), so
    480.000 x -1.25 is -600.00000, equal to the literal -600.00 (mid-build question 1)."""
    factor, kind, rule, scale, gap, effect, split, reason, children = expected
    where = f"{row.parent}>{row.factor_id}"
    assert (row.factor_id, row.kind, row.rule, row.split, row.reason) == (factor, kind, rule, split, reason), where
    assert (row.scale, row.gap, row.effect) == (D(scale), D(gap), D(effect)), (where, row.scale, row.gap, row.effect)
    assert [c.factor_id for c in row.rows] == [c[0] for c in children], where
    for child, exp in zip(row.rows, children):
        shape(child, exp)


def test_6_kobo_fuel_cost_splits_into_the_three_litre_leaves() -> None:
    import test_5b_attribution as t5b

    sb = _site_bridge("KOBO-001")
    root = sb.roots["contribution"]
    t5b.money(root.gap, "-562.00"), t5b.money(root.effect, "-562.00")
    fuel = t5b.find(root, "fuel_cost")
    t5b.money(fuel.effect, "-600.00")
    shape(fuel, ("fuel_cost", "TERM", "AR1", "-1", "600.00", "-600.00", "SPLIT", None, (
        ("diesel_l", "VOLUME", "AR2", "-1.25", "480", "-600.00", "SPLIT", None, (
            t5b.leaf("necessary_l", "TERM", "-1.25", "30", "-37.50"),
            t5b.leaf("candidate_l", "TERM", "-1.25", "330", "-412.50"),
            t5b.leaf("unexplained_l", "TERM", "-1.25", "120", "-150.00"))),
        t5b.leaf("diesel_price", "PRICE", "-1180", "0", "0.00"))))
    diesel = t5b.find(root, "diesel_l")
    assert diesel.evidence == "MODELLED"
    assert [r.evidence for r in diesel.rows] == ["MODELLED"] * 3
    assert [format(sb.actual.values[f].value, "f") for f in LEAVES] == ["730.000", "330.000", "120.000"]


@pytest.mark.parametrize("code", ["KISIWA-001", "MTO-001"])
def test_6_other_sites_say_what_is_missing(code: str) -> None:
    import test_5b_attribution as t5b

    sb = _site_bridge(code)
    fuel = t5b.find(sb.roots["contribution"], "fuel_cost")
    assert (fuel.split, fuel.reason, fuel.rows) == ("NOT_SPLIT", "DETAIL_NOT_AVAILABLE", ())
    assert fuel.unobserved_actual == ("candidate_l", "necessary_l", "unexplained_l")
    for leaf in LEAVES:
        lv = sb.actual.values[leaf]
        assert lv.value is None and lv.missing.note == "GENERATOR_OR_TANK_NOT_DECLARED", (code, leaf)


def test_6_the_portfolio() -> None:
    import test_5b_attribution as t5b
    from assetops_backend.structure.attribution.read import BridgeRead

    w = t5b._world()
    actual, targets, at = _bridge_reads(w)
    r = t5b.t5a.refs(w)
    pb = BridgeRead(actual, targets, clock=lambda: at).portfolio(w["tid"], [r[c] for c in t5b.CODES], t5b.OCT)
    rows = pb.rows["contribution"]
    fuel, diesel = rows["fuel_cost"], rows["diesel_l"]
    t5b.money(fuel.effect, "-755.00")
    assert (fuel.k, fuel.n, fuel.out) == (3, 3, ())
    assert format(diesel.actual, "f") == "1180.000" and diesel.target == D("700")
    assert format(diesel.gap, "f") == "480.000"
    assert diesel.effect == D("-600.00")  # -600.00000: mid-build question 1
    assert (diesel.k, diesel.n) == (1, 3)
    assert diesel.out == (("KISIWA-001", ("NOT_SPLIT",)), ("MTO-001", ("NOT_SPLIT",)))


# =====================================================================================================================
# Unit 3 (spec §4.3): test 10, the day state (pure)
# =====================================================================================================================

@pytest.mark.parametrize("facts, state", [
    ((False, "CURRENT", True, 12), "UNAVAILABLE"), ((False, None, False, None), "UNAVAILABLE"),
    ((True, None, False, 0), "NO_READINGS"), ((True, None, False, None), "NO_READINGS"),
    ((True, "UNASSESSED", False, 12), "NOT_ASSESSED"), ((True, "CURRENT", True, 12), "ASSESSED"),
    ((True, "STALE_PROJECTION", True, 12), "NOT_ASSESSED"), ((True, "FAILED", True, 12), "NOT_ASSESSED"),
    ((True, "PENDING", True, 12), "NOT_ASSESSED"),
])
def test_10_day_state(facts: tuple, state: str) -> None:
    from assetops_backend.structure.litres.inputs import day_state

    assert day_state(*facts) == state
