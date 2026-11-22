"""DD3.2 (spec `specs/DD-demo-data/spec.md` §6; D-DD.17, D-DD.30): the data-sheet tool, pure.

The mapping of `config/datasheets/kobo-equipment.json` onto Kobo's generator and battery in Lakeside's `/2` file, the
fit of the no-load rate, the residuals printed beside the sheet, and each refusal on a planted slot.
"""
from __future__ import annotations

import copy
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import datasheet_template as dt  # noqa: E402

SLOT = ROOT / "config/datasheets/kobo-equipment.json"
LAKESIDE = ROOT / "backend/tests/fixtures/on1/lakeside-power.onboarding.json"


@pytest.fixture
def slot() -> dict:
    return json.loads(SLOT.read_text(encoding="utf-8"))


def _props(component: dict) -> dict[str, object]:
    return {p["property_key"]: p["value"] for p in component.get("properties", [])}


def test_fit_is_the_least_squares_intercept() -> None:
    points = [(Fraction(18), Fraction("5.6")), (Fraction(27), Fraction("7.8")), (Fraction(36), Fraction("10.5"))]
    intercept = dt.fit_intercept(points)
    assert intercept == Fraction(37, 60)  # mean 239/30 minus slope 49/180 at 27 kW
    assert dt.half_even(intercept, "0.01") == "0.62"


def test_mapping_gives_the_spec_table(slot) -> None:
    mapping = dt.map_slot(slot)
    assert mapping.generator == {
        "generator-rated-power": ("36", "MANUFACTURER_DATASHEET"),
        "specific-fuel-consumption": ("0.2917", "MANUFACTURER_DATASHEET"),
        "generator-no-load-fuel-rate": ("0.62", "DATASHEET_FIT"),
        "generator-minimum-load": ("30", "GENERIC_DEFAULT"),
    }
    assert mapping.battery == {
        "battery-energy-capacity": ("191.5", "MANUFACTURER_DATASHEET"),
        "battery-charge-taper-start": ("95", "GENERIC_DEFAULT"),
    }
    assert mapping.generator_rating == "36" and mapping.battery_rating == "191.5"
    # sheet beside line, per stated point (spec §6: 10.50 / 10.50; 7.80 / 8.03; 5.60 / 5.56)
    assert mapping.residuals == [("100", "10.50", "10.50"), ("75", "7.80", "8.03"), ("50", "5.60", "5.56")]


def test_a_stated_no_load_rate_wins_and_is_declared(slot) -> None:
    slot["generator"]["no_load_l_per_h"] = "0.9"
    assert dt.map_slot(slot).generator["generator-no-load-fuel-rate"] == ("0.9", "MANUFACTURER_DATASHEET")


def test_the_owner_generic_value_is_taken_when_chosen(slot) -> None:
    slot["assumed"][0] = {"item": "generator.no_load_l_per_h", "value": "3.3", "basis_code": "GENERIC_DEFAULT",
                          "basis": "the owner's value of 2026-11-07 for an unsheeted set; the sheet states no no-load rate"}
    assert dt.map_slot(slot).generator["generator-no-load-fuel-rate"] == ("3.3", "GENERIC_DEFAULT")


def test_a_fit_entry_that_disagrees_with_the_fit_refuses(slot) -> None:
    slot["assumed"][0]["value"] = "0.70"
    with pytest.raises(dt.DatasheetRefused, match="DATASHEET_FIT_MISMATCH"):
        dt.map_slot(slot)


@pytest.mark.parametrize("points", [
    {"25": None, "50": None, "75": None, "100": "10.5"},  # one stated point
    {"25": None, "50": "1.0", "75": "5.5", "100": "10.5"},  # the line meets zero load below 0 L/h
])
def test_too_few_points_or_a_non_positive_intercept_refuses(slot, points) -> None:
    slot["generator"]["fuel_l_per_h"] = points
    with pytest.raises(dt.DatasheetRefused, match="DATASHEET_CURVE_INVALID"):
        dt.map_slot(slot)


def test_a_curve_v8_refuses_is_refused_with_v8s_code(slot) -> None:
    # SFC 0.10 L/kWh is below the diesel energy floor v8 enforces
    slot["generator"]["fuel_l_per_h"] = {"25": None, "50": "1.0", "75": "2.0", "100": "3.6"}
    slot["assumed"][0]["value"] = dt.half_even(dt.fit_intercept([
        (Fraction(18), Fraction(1)), (Fraction(27), Fraction(2)), (Fraction(36), Fraction("3.6"))]), "0.01")
    with pytest.raises(dt.DatasheetRefused, match="SFC_BELOW_DIESEL_ENERGY|DATASHEET_CURVE_INVALID"):
        dt.map_slot(slot)


def test_apply_writes_only_kobos_generator_and_battery(slot) -> None:
    before = json.loads(LAKESIDE.read_text(encoding="utf-8"))
    after = dt.apply(copy.deepcopy(before), "KOBO-001", dt.map_slot(slot))
    kobo_b = next(s for s in before["sites"] if s["code"] == "KOBO-001")
    kobo_a = next(s for s in after["sites"] if s["code"] == "KOBO-001")
    gen = next(c for c in kobo_a["components"] if c["type"] == "GENERATOR")
    bat = next(c for c in kobo_a["components"] if c["type"] == "BATTERY")
    assert gen["rating"]["value"] == 36 and bat["rating"]["value"] == 191.5
    p = _props(gen)
    assert p["generator-rated-power"] == 36 and p["specific-fuel-consumption"] == 0.2917
    assert p["generator-rated-power-basis"] == "MANUFACTURER_DATASHEET"
    assert p["generator-no-load-fuel-rate"] == 0.62 and p["generator-no-load-fuel-rate-basis"] == "DATASHEET_FIT"
    assert p["generator-minimum-load"] == 30 and p["generator-minimum-load-basis"] == "GENERIC_DEFAULT"
    # the policy stays as Lakeside's /1 values
    assert p["start-soc-threshold"] == 35 and p["stop-soc-threshold"] == 90 and p["minimum-runtime"] == 30
    b = _props(bat)
    assert b["battery-energy-capacity"] == 191.5 and b["battery-energy-capacity-basis"] == "MANUFACTURER_DATASHEET"
    assert b["battery-charge-taper-start"] == 95 and b["battery-charge-taper-start-basis"] == "GENERIC_DEFAULT"
    assert b["reserve-state-of-charge"] == 30
    # everything else is untouched: other Sites, other components, devices, people
    for key in ("format", "data", "operator", "people"):
        assert after[key] == before[key]
    assert [s for s in after["sites"] if s["code"] != "KOBO-001"] == [
        s for s in before["sites"] if s["code"] != "KOBO-001"]
    untouched = lambda site: [c for c in site["components"] if c["type"] not in ("GENERATOR", "BATTERY")]  # noqa: E731
    assert untouched(kobo_a) == untouched(kobo_b) and kobo_a["devices"] == kobo_b["devices"]


def test_apply_is_idempotent(slot) -> None:
    doc = json.loads(LAKESIDE.read_text(encoding="utf-8"))
    once = dt.apply(copy.deepcopy(doc), "KOBO-001", dt.map_slot(slot))
    assert dt.apply(copy.deepcopy(once), "KOBO-001", dt.map_slot(slot)) == once


def test_the_written_file_parses_as_a_foundation(slot) -> None:
    from assetops_backend.onboarding.operator_file import parse_operator_file, site_document
    from assetops_backend.sites.site_parsing import parse_site_document

    doc = dt.apply(json.loads(LAKESIDE.read_text(encoding="utf-8")), "KOBO-001", dt.map_slot(slot))
    parsed = parse_operator_file(json.dumps(doc).encode("utf-8"))
    kobo = next(s for s in parsed.sites if s.entry["code"] == "KOBO-001")
    record = parse_site_document(site_document(kobo, real=False), source="test")
    assert record is not None


def test_cli_check_reports_the_diff_then_write_makes_it_clean(tmp_path, capsys) -> None:
    target = tmp_path / "lakeside.json"
    target.write_text(LAKESIDE.read_text(encoding="utf-8"), encoding="utf-8")
    code = dt.main(["--slot", str(SLOT), "--onboarding", str(target), "--site", "KOBO-001", "--check"])
    out = capsys.readouterr().out
    assert code == 1 and "generator-no-load-fuel-rate" in out and "10.50 / 10.50" in out
    dt.main(["--slot", str(SLOT), "--onboarding", str(target), "--site", "KOBO-001", "--write"])
    assert dt.main(["--slot", str(SLOT), "--onboarding", str(target), "--site", "KOBO-001", "--check"]) == 0


def test_the_basis_vocabulary_carries_the_datasheet_siblings() -> None:  # D-DD.17
    from assetops_backend.sites.models import COMPONENT_PROPERTY_DEFINITIONS as PROPERTIES, MINIGRID_PROPERTY_CARRIERS, STATE_PROPERTY_VALUES

    three = frozenset({"GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_TEST"})
    for key, carrier in (("generator-rated-power-basis", "GENERATOR"), ("specific-fuel-consumption-basis", "GENERATOR"),
                         ("battery-energy-capacity-basis", "BATTERY")):
        assert STATE_PROPERTY_VALUES[key] == three and key in PROPERTIES
        assert MINIGRID_PROPERTY_CARRIERS[key] == carrier
    assert STATE_PROPERTY_VALUES["generator-no-load-fuel-rate-basis"] == three | {"DATASHEET_FIT"}
    assert STATE_PROPERTY_VALUES["generator-minimum-load-basis"] == three  # DATASHEET_FIT on the no-load rate only


def test_every_basis_sentence_renders_the_rulings_english() -> None:  # D-DD.17
    from statement_cases import component_property as cases

    from assetops_backend.i18n import message, render

    assert {c.variant for c in cases.CASES} == {"declared", "fit", "generic"}
    for case in cases.CASES:
        assert render(message(case.key, **case.facts)) == case.english
