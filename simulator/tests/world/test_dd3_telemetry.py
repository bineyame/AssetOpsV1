"""DD3.1 (spec `specs/DD-demo-data/spec.md` §4.1, §4.2; D-DD.19, D-DD.69, D-DD.71, D-DD.72): the telemetry writer on Kobo.

Every expected figure is written by hand from the pinned inputs in the first lines of each test: Kobo's July books
(`history.json`: delivered 8592 kWh, unexplained 12 L), the fuel note of 1 July 10:00 (400 L), the /2 file's tank of
2500 L (D-DD.76; so 1250 L at the start) and the binding file's twelve rows.
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


#: `demand` family day weights by day class (`history.families.demand.day` of the manifest); this test's own
#: (D-DD.129 moved it out of the writer).
DAY_WEIGHTS = {"classes": {"WD": [1, 2, 3, 4, 5], "SA": [6], "SU": [7]}, "WD": "1.00", "SA": "0.97", "SU": "0.90"}


def _books(first_note_l: int = 100, delivered_kwh: int = 8592, unexplained_l: int = 12) -> dict:
    return {"KOBO-001": {
        "months": {"2026-07": {"delivered_kwh": delivered_kwh, "unexplained_l": unexplained_l}},
        "fuel_notes": [{"at": "2026-07-01T10:00:00+03:00", "litres": first_note_l}],
        "day_weights": DAY_WEIGHTS, "sun_weights": tel.DEFAULT_SUN_WEIGHTS}}


def test_site_inputs_joins_the_foundation_with_its_bindings(sites_file: dict) -> None:
    assert sites_file["schema"] == "assetops.world-site-inputs/1"
    kobo = _kobo(sites_file)
    assert (kobo["tenant"], kobo["timezone"], kobo["role_set"]) == ("lakeside-power", "Africa/Nairobi", "minigrid-roles-5")  # D-DD.114
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
    assert by_address["generator-rated-power@generator"].value == 36
    assert by_address["generator-specific-fuel-consumption@generator"].value == Fraction(2917, 10000)
    assert by_address["fuel-tank-capacity@fuel-tank"].value == 2500  # D-DD.76
    assert by_address["fuel-tank-volume@fuel-tank"].value == 1250  # 50 % of the capacity (D-DD.19)
    assert [d.value for d in frozen.discrete_initial_values] == ["STOPPED"]
    assert frozen.interval.duration_minutes == 2 * 1440 and frozen.interval.timestep_minutes == 5
    assert frozen.interval.start_time == "2026-06-30T21:00:00Z"  # 1 July 00:00 at +03:00
    assert [b.kind for b in frozen.bounds] == ["UPPER"] and frozen.bounds[0].value == 2500


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
    # The tank holds 2500 L and starts at 1250 L: a 2000 L note on the first morning cannot fit.
    run = tel.SiteRun(_kobo(sites_file), _books(first_note_l=2000)["KOBO-001"], "2026-07-01", "2026-07-02")
    with pytest.raises(tel.TelemetryRefused) as refusal:
        run.next_day_readings()
    assert str(refusal.value).startswith("TEL_PACK KOBO-001 2026-07-01 fuel-tank-capacity")


def test_an_empty_tank_is_refused_as_tel_pack_with_the_packs_code(sites_file: dict) -> None:
    books = _books()["KOBO-001"]
    books["months"]["2026-07"]["unexplained_l"] = 31 * 200  # 200 L a night from a tank of 1250 L
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


def _sun(inputs, day_index: int) -> list[Fraction]:
    return [f.value for f in inputs.forcings if f.state_key == "plane-of-array-irradiance"
            and day_index * 1440 <= f.offset_minutes < (day_index + 1) * 1440]


def test_kobo_sun_outside_season_v2_is_the_clear_shape_times_the_solar_surplus_weight(sites_file: dict) -> None:
    """D-DD.77: July and August are `cool_dry` (solar_surplus 0.80, every day class 1.00); 1 Sep to 31 Oct keep
    season v2's calendar (2 Sep, index 1, clear; 3 Sep, index 2, overcast)."""
    clear = [0, 0, 0, 0, 0, 0, 150, 150, 550, 550, 900, 900, 950, 950, 600, 600, 150, 150, 0, 0, 0, 0, 0, 0]
    overcast = [0, 0, 0, 0, 0, 0, 50, 50, 190, 190, 310, 310, 330, 330, 210, 210, 50, 50, 0, 0, 0, 0, 0, 0]
    july = tel.frozen_inputs(_kobo(sites_file), _books()["KOBO-001"], "2026-07-04", "2026-07-05")  # Sat, Sun
    assert _sun(july, 0) == _sun(july, 1) == [Fraction(v) * Fraction(4, 5) for v in clear]
    books = {**_books()["KOBO-001"], "months": {"2026-09": {"delivered_kwh": 8592, "unexplained_l": 12}}}
    september = tel.frozen_inputs(_kobo(sites_file), books, "2026-09-02", "2026-09-03")
    assert _sun(september, 0) == [Fraction(v) for v in clear]
    assert _sun(september, 1) == [Fraction(v) for v in overcast]


def test_the_manifest_records_the_sun_rule(sites_file: dict) -> None:
    books = _books()["KOBO-001"]
    run = tel.SiteRun(_kobo(sites_file), books, "2026-07-01", "2026-07-01")
    conditions = tel.site_manifest(run.site, run, books, {})["conditions"]
    assert conditions["sun_outside_calendar"]["rule"] == (
        "clear shape x solar_surplus day weight (season x day class, no jitter) (D-DD.77)")
    assert conditions["sun_outside_calendar"]["weights"]["season"]["cool_dry"] == "0.80"


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


def test_books_carry_the_views_solar_surplus_weights() -> None:
    """D-DD.77: the sun weights come from the view's `history` block, not the default."""
    view = {"accounting_period": "2026-10", "history": {
        "seasons": {"2026-07": "cool_dry"}, "day_classes": {"WD": [1, 2, 3, 4, 5], "SA": [6], "SU": [7]},
        "families": {"demand": {"day": {"WD": "1.00", "SA": "0.97", "SU": "0.90"}},
                     "solar_surplus": {"season": {"cool_dry": "0.70"}, "day": {"WD": "1.00", "SA": "1.00", "SU": "0.50"}}}},
        "tenants": [{"tenant": "t", "vertical": "MINI_GRID",
                     "sites": [{"site": "s", "code": "X-001", "period": {"actual": {"delivered_kwh": 1}}}]}]}
    sun = tel.books_for(view, {"tenants": {"t": {"s": {}}}}, {"t": ""})["X-001"]["sun_weights"]
    assert sun == {"seasons": {"2026-07": "cool_dry"}, "classes": {"WD": [1, 2, 3, 4, 5], "SA": [6], "SU": [7]},
                   "season": {"cool_dry": "0.70"}, "day": {"WD": "1.00", "SA": "1.00", "SU": "0.50"}}


#: D-DD.76's storage sizes, in order; the rule rounds two months of the largest month up to the next one.
STANDARD_TANKS_L = (500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 10000)


def test_each_lakeside_tank_is_the_sites_own_two_months_of_its_largest_month() -> None:
    """D-DD.76: necessary + candidate + unexplained litres of `history.json` July-September and October's
    `period.actual.diesel_l`; twice the largest, rounded up to a standard size; source SITE, version 1."""
    import yaml

    layer4 = REPOSITORY_ROOT / "Docs/demo-sprint/product-direction-layer4"
    history = json.loads((layer4 / "history.json").read_text(encoding="utf-8"))["tenants"]["lakeside-power"]
    manifest = yaml.safe_load((layer4 / "demo-site-scenario-manifest.yaml").read_text(encoding="utf-8"))
    tenant = next(t for t in manifest["tenants"] if t["tenant"] == "lakeside-power")
    onboarding = json.loads(ONBOARDING.read_text(encoding="utf-8"))
    declared = {}
    for site in onboarding["sites"]:
        tank = next(c for c in site["components"] if c["type"] == "FUEL_TANK")
        declared[site["code"]] = [(p["value"], p["source"], p["source_version"]) for p in tank["properties"]
                                  if p["property_key"] == "tank-capacity"]
    expected = {}
    for site in tenant["sites"]:
        months = [sum(b["actual"].get(k, 0) for k in ("necessary_l", "candidate_l", "unexplained_l"))
                  for b in history[site["site"]].values()] + [site["period"]["actual"]["diesel_l"]]
        expected[site["code"]] = [(next(s for s in STANDARD_TANKS_L if s >= 2 * max(months)), "SITE", 1)]
    assert expected == {"KISIWA-001": [(5000, "SITE", 1)], "KOBO-001": [(2500, "SITE", 1)], "MTO-001": [(1000, "SITE", 1)]}
    assert declared == expected


def test_kobos_readings_do_not_depend_on_the_role_set_label() -> None:
    """DD3c review L1: `foundation_digest` is taken over `role_set`, and the frozen run's seed is the digest's head, so
    D-DD.114's move to roles-5 changed Kobo's seed. No draw consumes the seed today: two days of Kobo's readings are
    byte-identical under both labels while the seeds differ. If a pack ever draws on the seed (D-DD.102/115's
    class), this fails and the seed must be taken off the label."""
    onboarding = json.loads(ONBOARDING.read_text(encoding="utf-8"))
    roles4 = {**_bindings(), "role_set": "minigrid-roles-4"}
    runs = []
    for binding in (_bindings(), roles4):
        site = next(s for s in tel.site_inputs(onboarding, {"KOBO-001": binding})["sites"] if s["code"] == "KOBO-001")
        components = {c["id"]: c for c in site["foundation"]["components"]}
        components["generator"]["properties"] += [
            {"property_key": "generator-no-load-fuel-rate", "value": "0.62", "unit": "L/h"},
            {"property_key": "generator-minimum-load", "value": "30", "unit": "%"}]
        components["battery"]["properties"].append(
            {"property_key": "battery-charge-taper-start", "value": "95", "unit": "%"})
        run = tel.SiteRun(site, _books()["KOBO-001"], "2026-07-01", "2026-07-02")
        runs.append((tel.frozen_inputs(site, _books()["KOBO-001"], "2026-07-01", "2026-07-02").seed,
                     tel.readings_bytes(run.next_day_readings() + run.next_day_readings())))
    (seed5, bytes5), (seed4, bytes4) = runs
    assert seed5 != seed4  # the label does move the seed (the coupling is real)
    assert len(bytes5) > 0 and bytes5 == bytes4
