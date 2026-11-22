"""D-DD.103 (DD4a, with D-DD.90): one declared readings span ending 6 Nov 06:00 local; a month with no books runs at
the last booked month's rate; the draw goes on by day of month; the last day file ends at 06:00.

Expected figures are computed here from the declared shape and weights with this file's own arithmetic (the rule's
formula), not read from the writer.
"""

from __future__ import annotations

import copy
import json
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest
import yaml

from assetops_simulator.world import telemetry as tel
from assetops_simulator.world.telemetry_cold import ColdSiteRun

from .conftest import REPOSITORY_ROOT, load_fixture

LAYER4 = REPOSITORY_ROOT / "Docs" / "demo-sprint" / "product-direction-layer4"
ON1 = REPOSITORY_ROOT / "backend/tests/fixtures/on1"
BINDINGS = REPOSITORY_ROOT / "backend/conversions/world"
NAIROBI = ZoneInfo("Africa/Nairobi")
END = "2026-11-06T06:00"
W1_ROWS = {"GENERATOR": [("generator-no-load-fuel-rate", "0.62", "L/h"), ("generator-minimum-load", "30", "%")]}


def _sites(operator: str, codes: tuple[str, ...]) -> dict:
    onboarding = json.loads((ON1 / f"{operator}.onboarding.json").read_text(encoding="utf-8"))
    bindings = {c: json.loads((BINDINGS / f"{c}-bindings.json").read_text(encoding="utf-8")) for c in codes}
    return tel.site_inputs(onboarding, bindings)


def _kobo() -> dict:
    kobo = copy.deepcopy(next(s for s in _sites("lakeside-power", ("KOBO-001",))["sites"]))
    for component in kobo["foundation"]["components"]:
        for key, value, unit in W1_ROWS.get(component["type"], ()):
            component["properties"] = [p for p in component["properties"] if p["property_key"] != key]
            component["properties"].append({"property_key": key, "value": value, "unit": unit})
    return kobo


@pytest.fixture(scope="module")
def books() -> dict:
    view = load_fixture()
    history = json.loads((LAYER4 / "history.json").read_text(encoding="utf-8"))
    return tel.books_for(view, history, {})["KOBO-001"]


def _weight(day: date) -> Fraction:
    weekday = day.isoweekday()
    return Fraction("1.00") if weekday <= 5 else Fraction("0.97") if weekday == 6 else Fraction("0.90")


def _shape(hours: range) -> Fraction:
    return Fraction(sum(tel.LOAD_SHAPE_KW[f][h] for f in tel.LOAD_SHAPE_KW for h in hours))


def _expected_november_kwh(october_kwh: int) -> int:
    october = [date(2026, 10, d) for d in range(1, 32)]
    k = Fraction(october_kwh) / sum((_weight(d) * _shape(range(24)) for d in october), Fraction(0))
    span = sum((_weight(date(2026, 11, d)) * _shape(range(24)) for d in range(1, 6)), Fraction(0))
    span += _weight(date(2026, 11, 6)) * _shape(range(6))
    exact = k * span
    return int((Decimal(exact.numerator) / Decimal(exact.denominator)).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def test_the_span_is_one_constant_ending_at_m_as_of_06_00() -> None:
    manifest = yaml.safe_load((LAYER4 / "demo-site-scenario-manifest.yaml").read_text(encoding="utf-8"))
    first_month = sorted(manifest["history"]["months"])[0]
    assert tel.READINGS_SPAN == ("2026-07-01T00:00", END)
    assert tel.READINGS_SPAN[1][:10] == str(manifest["as_of"])
    assert tel.READINGS_SPAN[0][:10] == f"{first_month}-01"


def test_november_has_no_books_and_runs_at_octobers_rate(books: dict) -> None:
    november = books["months"]["2026-11"]
    assert november == {"rate_of": "2026-10", "delivered_kwh": _expected_november_kwh(9100)}


def test_kobo_from_1_nov_writes_six_files_the_last_ending_at_06_00(books: dict) -> None:
    kobo = _kobo()
    result = tel.build_telemetry({}, {"sites": [kobo]}, {"KOBO-001": books}, start="2026-11-01", end=END)
    days = sorted(p for p, _ in result.files if p.endswith(".readings.json"))
    assert days == [f"lakeside-power/telemetry/KOBO-001.2026-11-0{d}.readings.json" for d in range(1, 7)]
    last = json.loads(dict(result.files)[days[-1]])
    assert last["schema"] == tel.READINGS_SCHEMA and last["day"] == "2026-11-06"
    ends = [datetime.fromisoformat(r["end"]) for r in last["readings"]]
    limit = datetime(2026, 11, 6, 6, 0, tzinfo=NAIROBI)
    assert max(ends) == limit and all(e <= limit for e in ends)
    slots: dict[tuple[str, str], int] = {}
    for r in last["readings"]:
        slots[(r["source_id"], r["signal_id"])] = slots.get((r["source_id"], r["signal_id"]), 0) + 1
    assert slots and set(slots.values()) == {72}
    manifest = dict(result.manifests)["lakeside-power/telemetry/KOBO-001.manifest.json"]
    assert manifest["span"] == {"first": "2026-11-01", "last": "2026-11-06", "to": "2026-11-06T06:00:00+03:00"}
    assert manifest["conditions"]["month_without_books"] == {
        "rule": "D-DD.103", "load": "the rate month's kWh per weighted shape unit",
        "draw": "the rate month's daily parts by day of month", "rate_of": "2026-10"}
    measured = json.loads(dict(result.files)["lakeside-power/telemetry/measured.json"])
    assert measured["sites"]["KOBO-001"]["2026-11"]["partial_to"] == "2026-11-06T06:00:00+03:00"


def test_novembers_load_energy_is_e_and_six_draws_repeat_octobers_first_six_parts(books: dict) -> None:
    inputs = tel.frozen_inputs(_kobo(), books, "2026-11-01", END)
    assert inputs.interval.duration_minutes == 5 * 1440 + 360
    loads = [f for f in inputs.forcings if f.parameter_id == "world-load"]
    assert sum((f.value for f in loads), Fraction(0)) == books["months"]["2026-11"]["delivered_kwh"]
    assert max(f.offset_minutes + f.duration_minutes for f in inputs.forcings) == 5 * 1440 + 360
    draws = [c for c in inputs.causes if c.parameter_id == "declared-draw"]
    assert [c.offset_minutes for c in draws] == [n * 1440 + 120 for n in range(6)]
    parts = [Fraction(c, 100) for c in ([388] * 3 + [387] * 28)]  # 120 L over 31 days, largest remainder to 0.01 L
    assert sum(parts) == 120
    assert [c.quantity for c in draws] == parts[:6]


def test_a_cold_room_ends_at_the_same_instant() -> None:
    mwea = next(s for s in _sites("harvest-cold", ("COLD-MWEA",))["sites"])
    view = load_fixture()
    history = view["history"]
    books = {"ledger": [], "cooling": history["families"]["cooling"], "seasons": history["seasons"],
             "day_classes": history["day_classes"]}
    run = ColdSiteRun(mwea, books, "2026-11-01", END)
    for _ in run.days:
        run.advance_day()
    assert run.days[-1] == date(2026, 11, 6)
    last = run.day_records(run.days[-1])
    limit = datetime(2026, 11, 6, 3, 0, tzinfo=ZoneInfo("UTC"))
    assert max(r[3] for r in last) == limit and all(r[3] <= limit for r in last)
    meter = [r for r in last if r[0] == "compressor-meter"]  # 5-minute interval means: 72 slots, the last ends 06:00
    assert len(meter) == 72 and meter[-1][3] == limit
    chamber = [r for r in last if r[0] == "chamber-probe"]  # instants 00:00 to 05:55; 06:00 is the horizon
    assert len(chamber) == 72 and chamber[-1][3] == limit - timedelta(minutes=5)
    assert run.end - run.start == timedelta(days=5, hours=6)


def test_the_cli_span_defaults_are_readings_span() -> None:
    import importlib.util

    from .conftest import CLI

    spec = importlib.util.spec_from_file_location("world_history_cli", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args = module.build_parser().parse_args(["telemetry", "--manifest", "m", "--sites", "s", "--books", "b", "--out", "o"])
    assert (args.start, args.end) == tel.READINGS_SPAN


def test_an_end_instant_off_the_hour_or_with_an_offset_is_refused() -> None:
    for end in ("2026-11-06T06:30", "2026-11-06T06:00+03:00"):
        with pytest.raises(tel.TelemetryRefused, match="TEL_EVENT_UNPLACED"):
            tel.span_days("2026-11-01", end)
    assert tel.span_days("2026-07-01T00:00", "2026-07-02T00:00") == ([date(2026, 7, 1)], 1440)
