"""DD3.1 (spec `specs/DD-demo-data/spec.md` §4.1, §4.2; D-DD.19, D-DD.69, D-DD.71, D-DD.72): the telemetry writer on Kobo.

Every expected figure is written by hand from the pinned inputs in the first lines of each test: Kobo's July books
(`history.json`: delivered 8592 kWh, unexplained 12 L), the fuel note of 1 July 10:00 (400 L), the /2 file's tank of
400 L (so 200 L at the start) and the binding file's twelve rows.
"""

from __future__ import annotations

import copy
import json
from fractions import Fraction

import pytest

from assetops_simulator.world import telemetry as tel

from .conftest import REPOSITORY_ROOT

ONBOARDING = REPOSITORY_ROOT / "backend/tests/fixtures/on1/lakeside-power.onboarding.json"
BINDINGS = REPOSITORY_ROOT / "backend/conversions/world"
STEPS_PER_DAY = 288


def _bindings(code: str = "KOBO-001") -> dict:
    return json.loads((BINDINGS / f"{code}-bindings.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sites_file() -> dict:
    onboarding = json.loads(ONBOARDING.read_text(encoding="utf-8"))
    return tel.site_inputs(onboarding, {code: _bindings(code) for code in ("KISIWA-001", "KOBO-001", "MTO-001")})


def _kobo(sites_file: dict) -> dict:
    """Kobo with the three curve properties the data-sheet tool writes in commit 2 (DD3.2), by hand: no-load 0.62 L/h,
    minimum load 30 %, taper start 95 %."""
    kobo = copy.deepcopy(next(s for s in sites_file["sites"] if s["code"] == "KOBO-001"))
    components = {c["id"]: c for c in kobo["foundation"]["components"]}
    components["generator"]["properties"] += [
        {"property_key": "generator-no-load-fuel-rate", "value": "0.62", "unit": "L/h"},
        {"property_key": "generator-minimum-load", "value": "30", "unit": "%"}]
    components["battery"]["properties"].append(
        {"property_key": "battery-charge-taper-start", "value": "95", "unit": "%"})
    return kobo


def _books(first_note_l: int = 100, delivered_kwh: int = 8592, unexplained_l: int = 12) -> dict:
    return {"KOBO-001": {
        "months": {"2026-07": {"delivered_kwh": delivered_kwh, "unexplained_l": unexplained_l}},
        "fuel_notes": [{"at": "2026-07-01T10:00:00+03:00", "litres": first_note_l}],
        "day_weights": tel.DEFAULT_DAY_WEIGHTS}}


def test_site_inputs_joins_the_foundation_with_its_bindings(sites_file: dict) -> None:
    assert sites_file["schema"] == "assetops.world-site-inputs/1"
    kobo = _kobo(sites_file)
    assert (kobo["tenant"], kobo["timezone"], kobo["role_set"]) == ("lakeside-power", "Africa/Nairobi", "minigrid-roles-4")
    assert len(kobo["bindings"]) == 12 and len(kobo["foundation"]["components"]) == 10
    assert len(kobo["foundation_digest"]) == 64
    alone = tel.site_inputs(json.loads(ONBOARDING.read_text()), {"KOBO-001": _bindings()})
    assert [s["code"] for s in alone["sites"]] == ["KOBO-001"]
    assert alone["sites"][0]["foundation_digest"] == next(
        s for s in sites_file["sites"] if s["code"] == "KOBO-001")["foundation_digest"]
    assert [s["code"] for s in sites_file["sites"]] == ["KISIWA-001", "KOBO-001", "MTO-001"]


def test_frozen_inputs_come_from_the_foundation_by_address(sites_file: dict) -> None:
    frozen = tel.frozen_inputs(_kobo(sites_file), _books()["KOBO-001"], "2026-07-01", "2026-07-02")
    by_address = {row.address: row for row in frozen.initial_values}
    assert by_address["generator-rated-power@generator"].value == 40
    assert by_address["generator-specific-fuel-consumption@generator"].value == Fraction(3, 10)
    assert by_address["fuel-tank-capacity@fuel-tank"].value == 400
    assert by_address["fuel-tank-volume@fuel-tank"].value == 200  # 50 % of the capacity (D-DD.19)
    assert [d.value for d in frozen.discrete_initial_values] == ["STOPPED"]
    assert frozen.interval.duration_minutes == 2 * 1440 and frozen.interval.timestep_minutes == 5
    assert frozen.interval.start_time == "2026-06-30T21:00:00Z"  # 1 July 00:00 at +03:00
    assert [b.kind for b in frozen.bounds] == ["UPPER"] and frozen.bounds[0].value == 400


def test_a_foundation_without_a_needed_property_refuses(sites_file: dict) -> None:
    kobo = _kobo(sites_file)
    generator = next(c for c in kobo["foundation"]["components"] if c["type"] == "GENERATOR")
    generator["properties"] = [p for p in generator["properties"] if p["property_key"] != "start-delay"]
    with pytest.raises(tel.TelemetryRefused) as refusal:
        tel.frozen_inputs(kobo, _books()["KOBO-001"], "2026-07-01", "2026-07-02")
    assert str(refusal.value).startswith("TEL_FOUNDATION KOBO-001 start-delay")


def test_monthly_load_totals_equal_the_books_exactly(sites_file: dict) -> None:
    books = _books()["KOBO-001"]
    frozen = tel.frozen_inputs(_kobo(sites_file), books, "2026-07-01", "2026-07-31")
    kwh = sum(f.value * Fraction(f.duration_minutes, 60) for f in frozen.forcings if f.address.startswith("load-demand@"))
    assert kwh == 8592
    deliveries = sum(c.quantity for c in frozen.causes if c.direction == "INCREASE")
    draws = sum(c.quantity for c in frozen.causes if c.direction == "DECREASE")
    assert (deliveries, draws) == (100, 12)
    assert len([c for c in frozen.causes if c.direction == "DECREASE"]) == 31
    assert {c.offset_minutes % 1440 for c in frozen.causes if c.direction == "DECREASE"} == {120}  # 02:00 local


def test_input_total_refuses_when_the_books_cannot_be_met(sites_file: dict) -> None:
    books = _books(delivered_kwh=0)["KOBO-001"]
    with pytest.raises(tel.TelemetryRefused) as refusal:
        tel.frozen_inputs(_kobo(sites_file), books, "2026-07-01", "2026-07-02")
    assert str(refusal.value).startswith("TEL_INPUT_TOTAL KOBO-001 2026-07")


def test_one_continuous_execution_two_days_equals_one_pass_of_576(sites_file: dict) -> None:
    kobo, books = _kobo(sites_file), _books()["KOBO-001"]
    twice = tel.SiteRun(kobo, books, "2026-07-01", "2026-07-02")
    once = tel.SiteRun(kobo, books, "2026-07-01", "2026-07-02")
    first = twice.next_day_readings() + twice.next_day_readings()
    assert twice.steps_advanced == 2 * STEPS_PER_DAY
    all_at_once = once.readings_for_steps(1, 2 * STEPS_PER_DAY)
    assert once.steps_advanced == 2 * STEPS_PER_DAY
    assert tel.readings_bytes(first) == tel.readings_bytes(all_at_once)
    assert len(tel.readings_bytes(first)) > 0 and len(first) == 2 * STEPS_PER_DAY * len(twice.pairs)


def test_every_pair_written_resolves_to_exactly_one_binding_row(sites_file: dict) -> None:
    kobo = _kobo(sites_file)
    run = tel.SiteRun(kobo, _books()["KOBO-001"], "2026-07-01", "2026-07-01")
    rows = _bindings()["bindings"]
    written = {(r["source_id"], r["signal_id"]) for r in run.next_day_readings()}
    assert written == {(b["device_id"], b["signal_id"]) for b in rows}
    for pair in written:
        assert len([b for b in rows if (b["device_id"], b["signal_id"]) == pair]) == 1
    assert {m["role"] for m in run.mappings} == {b["role"] for b in rows}


@pytest.mark.parametrize("edit,detail", [
    ("drop", "TEL_BINDING KOBO-001 fuel_level"),
    ("duplicate", "TEL_BINDING KOBO-001 fuel_level"),
])
def test_a_public_record_with_no_binding_row_or_two_refuses(sites_file: dict, edit: str, detail: str) -> None:
    kobo = _kobo(sites_file)
    row = next(b for b in kobo["bindings"] if b["role"] == "fuel_level")
    if edit == "drop":
        kobo["bindings"].remove(row)
    else:
        kobo["bindings"].append({**row, "device_id": "second-fuel-sensor"})
    with pytest.raises(tel.TelemetryRefused) as refusal:
        tel.SiteRun(kobo, _books()["KOBO-001"], "2026-07-01", "2026-07-01")
    assert str(refusal.value) == detail


def test_a_delivery_that_overfills_the_tank_is_refused_as_tel_pack_naming_the_day(sites_file: dict) -> None:
    # The tank holds 400 L and starts at 200 L: a 400 L note on the first morning cannot fit.
    run = tel.SiteRun(_kobo(sites_file), _books(first_note_l=400)["KOBO-001"], "2026-07-01", "2026-07-02")
    with pytest.raises(tel.TelemetryRefused) as refusal:
        run.next_day_readings()
    assert str(refusal.value).startswith("TEL_PACK KOBO-001 2026-07-01 fuel-tank-capacity")


def test_an_empty_tank_is_refused_as_tel_pack_with_the_packs_code(sites_file: dict) -> None:
    books = _books()["KOBO-001"]
    books["months"]["2026-07"]["unexplained_l"] = 31 * 40  # 40 L a night from a tank of 200 L
    run = tel.SiteRun(_kobo(sites_file), books, "2026-07-01", "2026-07-31")
    with pytest.raises(tel.TelemetryRefused) as refusal:
        for _ in range(31):
            run.next_day_readings()
    assert str(refusal.value).startswith("TEL_PACK KOBO-001 2026-07-")


def test_readings_are_exact_decimal_strings_with_the_interval_stated(sites_file: dict) -> None:
    run = tel.SiteRun(_kobo(sites_file), _books()["KOBO-001"], "2026-07-01", "2026-07-01")
    readings = run.next_day_readings()
    first = readings[0]
    assert set(first) == {"source_id", "signal_id", "start", "end", "value", "unit"}
    assert first["start"] == "2026-07-01T00:00:00+03:00" and first["end"] == "2026-07-01T00:05:00+03:00"
    assert all(isinstance(r["value"], str) for r in readings)
    soc = [r for r in readings if r["signal_id"] == "state-of-charge"]
    assert len(soc) == STEPS_PER_DAY and Fraction(soc[0]["value"]) > 0
    assert readings == sorted(readings, key=lambda r: (r["start"], r["source_id"], r["signal_id"]))


def test_the_writer_never_reads_the_oracle() -> None:
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(tel))
    allowed = {"refuse_oracle", "TEL_ORACLE_READ", "ORACLE_KEY"}
    docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                  if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body
                  and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)}
    named = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            text = node.id
        elif isinstance(node, ast.Attribute):
            text = node.attr
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            text = node.name
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            text = " ".join([getattr(node, "module", None) or "", *[a.name for a in node.names]])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            text = node.value
        else:
            continue
        if "oracle" in text.lower() and not any(text.startswith(a) or a in text for a in allowed):
            named.append(text)
    assert named == []
    with pytest.raises(tel.TelemetryRefused) as refusal:
        tel.refuse_oracle({"tenants": [{"sites": [{"code": "X", "oracle": {"a": 1}}]}]})
    assert str(refusal.value).startswith("TEL_ORACLE_READ")
