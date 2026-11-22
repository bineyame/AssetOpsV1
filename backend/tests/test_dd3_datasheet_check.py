"""DD3.2 (spec `specs/DD-demo-data/spec.md` §6 and §8.1): C-DD16 on the slot and Lakeside's `/2` file, no database.

C-DD16 asks whether the world's Kobo Site (its `/2` onboarding foundation, which the writer runs on) carries the slot's
values with their `-basis` properties, as the tool maps them. The checker maps the slot by its own arithmetic.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import dd_check  # noqa: E402

SLOT = ROOT / "config/datasheets/kobo-equipment.json"
ONBOARDING = ROOT / "backend/tests/fixtures/on1/lakeside-power.onboarding.json"


def _slot() -> dict:
    return json.loads(SLOT.read_text(encoding="utf-8"))


def _doc() -> dict:
    return json.loads(ONBOARDING.read_text(encoding="utf-8"))


def _component(doc: dict, kind: str) -> dict:
    site = next(s for s in doc["sites"] if s["code"] == "KOBO-001")
    return next(c for c in site["components"] if c["type"] == kind)


def _prop(doc: dict, kind: str, key: str) -> dict:
    return next(p for p in _component(doc, kind)["properties"] if p["property_key"] == key)


def test_c_dd16_is_live() -> None:
    assert "C-DD16" in dd_check.LIVE and "C-DD16" not in dd_check.STUBS


def test_the_checkers_own_mapping_gives_the_spec_table() -> None:
    want = dd_check.datasheet_expectation(_slot())
    assert want["GENERATOR"]["generator-rated-power"] == ("36", "MANUFACTURER_DATASHEET")
    assert want["GENERATOR"]["specific-fuel-consumption"] == ("0.2917", "MANUFACTURER_DATASHEET")
    assert want["GENERATOR"]["generator-no-load-fuel-rate"] == ("0.62", "DATASHEET_FIT")
    assert want["GENERATOR"]["generator-minimum-load"] == ("30", "GENERIC_DEFAULT")
    assert want["BATTERY"]["battery-energy-capacity"] == ("191.5", "MANUFACTURER_DATASHEET")
    assert want["BATTERY"]["battery-charge-taper-start"] == ("95", "GENERIC_DEFAULT")


def test_c_dd16_passes_on_the_committed_slot_and_file() -> None:
    result = dd_check.judge_datasheet(_slot(), _doc())
    assert result.passed, result.detail


def test_a_moved_value_a_changed_basis_and_a_dropped_sibling_each_fail() -> None:
    doc = _doc()
    _prop(doc, "GENERATOR", "specific-fuel-consumption")["value"] = 0.3
    _prop(doc, "BATTERY", "battery-charge-taper-start-basis")["value"] = "MANUFACTURER_DATASHEET"
    gen = _component(doc, "GENERATOR")
    gen["properties"] = [p for p in gen["properties"] if p["property_key"] != "generator-rated-power-basis"]
    result = dd_check.judge_datasheet(_slot(), doc)
    assert not result.passed
    text = "\n".join(result.detail)
    assert "specific-fuel-consumption" in text and "battery-charge-taper-start-basis" in text
    assert "generator-rated-power-basis" in text


def test_a_rating_off_the_slot_or_a_template_source_fails() -> None:
    doc = _doc()
    _component(doc, "BATTERY")["rating"]["value"] = 200
    _prop(doc, "GENERATOR", "generator-minimum-load")["source"] = "TEMPLATE"
    result = dd_check.judge_datasheet(_slot(), doc)
    assert not result.passed
    text = "\n".join(result.detail)
    assert "BATTERY rating" in text and "generator-minimum-load" in text


def test_a_slot_whose_fit_disagrees_with_its_assumed_no_load_fails() -> None:
    slot = copy.deepcopy(_slot())
    next(a for a in slot["assumed"] if a["item"] == "generator.no_load_l_per_h")["value"] = "0.70"
    result = dd_check.judge_datasheet(slot, _doc())
    assert not result.passed and any("fit" in line for line in result.detail)
