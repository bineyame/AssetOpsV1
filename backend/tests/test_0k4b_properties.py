"""0K4b P1-P4, P6 (spec section 3; D-0K4.19, D-0K4.21): the Foundation's three new properties and their words.

No database. The six rows are this test's own literal (W2), independent of `host/tests/kobo_assumed.py` (P5 checks
the fixture writes the same). Every expected sentence is a hand literal from spec section 2.6.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from assetops_backend.i18n import message, render
from assetops_backend.runs.profiles import GENERATOR_CURVE_NEEDS, MODEL_PROFILES
from assetops_backend.served_text import served_text
from assetops_backend.sites.models import COMPONENT_PROPERTY_DEFINITIONS
from assetops_backend.sites.parsing import parse_site_template
from assetops_backend.sites.ports import SiteConfigurationInvalid
from assetops_backend.sites.service import SiteCreationService
from assetops_backend.sites.site_parsing import CreateSiteRequest, parse_site_document, render_site_document
from statement_cases import foundation as foundation_cases
from statement_cases import model_profile as model_profile_cases

ROOT = Path(__file__).resolve().parents[2]
NEW_KEYS = ("generator-minimum-load", "generator-minimum-load-basis", "battery-charge-taper-start",
            "battery-charge-taper-start-basis")
ROWS = {
    "generator": [
        ("generator-no-load-fuel-rate", 3.3, "L/h"),
        ("generator-no-load-fuel-rate-basis", "GENERIC_DEFAULT", "state"),
        ("generator-minimum-load", 30, "%"),
        ("generator-minimum-load-basis", "GENERIC_DEFAULT", "state"),
    ],
    "battery": [
        ("battery-charge-taper-start", 95, "%"),
        ("battery-charge-taper-start-basis", "GENERIC_DEFAULT", "state"),
    ],
}


def _kobo_document() -> dict:
    """The shipped Kobo template, created as a Site and rendered into a site document (as `kobo.kobo_site` does)."""
    template = parse_site_template(
        yaml.safe_load((ROOT / "config" / "site-templates" / "kobo-mini-grid-60kw.yaml").read_text(encoding="utf-8")),
        source="the Kobo template",
    )
    created: list = []

    class Recording:
        def create_site(self, record):
            created.append(record)
            return record

    class Catalog:
        def list_templates(self) -> tuple:
            return (template,)

        def get_template(self, template_id: str):
            return template

    SiteCreationService(Recording(), Catalog()).create_site_from_template(CreateSiteRequest(
        template_id="kobo-mini-grid-60kw", site_id="KOBO-001", display_name="Kobo mini-grid", country="Ethiopia",
        locality="Kobo", timezone="Africa/Addis_Ababa"))
    return copy.deepcopy(render_site_document(created[0]))


def _component(document: dict, component_id: str) -> dict:
    return next(c for c in document["foundation"]["components"] if c["component_id"] == component_id)


def _with_rows(rows: dict) -> dict:
    document = _kobo_document()
    for component_id, items in rows.items():
        item = _component(document, component_id)
        item["properties"] = [*(item.get("properties") or []), *(
            {"property_key": k, "value": v, "unit": u, "source": "SITE", "source_version": 1} for k, v, u in items)]
    return document


def _parse(document: dict):
    return parse_site_document(document, source="the 0K4b Kobo site")


def test_p1_the_six_rows_parse_on_their_components():
    site = _parse(_with_rows(ROWS))
    by_id = {c.component_id: c for c in site.foundation.components}
    for component_id, items in ROWS.items():
        declared = {p.property_key: p for p in by_id[component_id].properties}
        for key, value, unit in items:
            assert declared[key].unit == unit and declared[key].value == value, key
            assert declared[key].source == "SITE"


@pytest.mark.parametrize("key, component_id", [("generator-minimum-load-basis", "generator"),
                                               ("battery-charge-taper-start-basis", "battery")])
def test_p2_a_basis_outside_the_set_is_refused_naming_the_key(key, component_id):
    rows = copy.deepcopy(ROWS)
    rows[component_id] = [(k, "ASSUMED" if k == key else v, u) for k, v, u in rows[component_id]]
    with pytest.raises(SiteConfigurationInvalid, match=key):
        _parse(_with_rows(rows))


def test_p3_minimum_load_on_the_battery_is_refused_by_the_carrier_rule():
    rows = {"generator": ROWS["generator"][:2], "battery": [*ROWS["battery"], ("generator-minimum-load", 30, "%")]}
    with pytest.raises(SiteConfigurationInvalid, match="generator-minimum-load belongs on a GENERATOR component"):
        _parse(_with_rows(rows))


NEED_SENTENCES = {
    "generator-no-load-fuel-rate": "Litres an hour the generator burns while starting or running at no output.",
    "generator-minimum-load": "Site policy: the least share of its rating a running generator is held at.",
    "battery-charge-taper-start": "The state of charge above which the battery accepts less than its charge limit.",
}


def test_p4_the_curve_needs_are_declared_and_and_v8_alone_declares_them():
    assert [(n.state_key, n.foundation_binding.property_key, n.foundation_binding.unit,
             n.foundation_binding.component_type) for n in GENERATOR_CURVE_NEEDS] == [
        ("generator-no-load-fuel-rate", "generator-no-load-fuel-rate", "L/h", "GENERATOR"),
        ("generator-minimum-load", "generator-minimum-load", "%", "GENERATOR"),
        ("battery-charge-taper-start", "battery-charge-taper-start", "%", "BATTERY"),
    ]
    # 0K4a puts the needs on `mini-grid` v8 (its own test, `test_0k4a_profile_words.py`); every other profile has none.
    for profile in (p for p in MODEL_PROFILES if (p.model_profile_id, p.model_profile_version) != ("mini-grid", 8)):
        assert not any(need in profile.supported_states for need in GENERATOR_CURVE_NEEDS), profile.model_profile_id
        assert not {"generator-minimum-load", "battery-charge-taper-start"} & set(profile.foundation_needs)
    assert {n.state_key: served_text(n.statement) for n in GENERATOR_CURVE_NEEDS} == NEED_SENTENCES
    assert sorted(NEED_SENTENCES.values()) == sorted(
        c.english for c in model_profile_cases.CASES if c.key == "model_profile.need")


NAMES = {
    "generator-minimum-load": "Generator minimum load",
    "generator-minimum-load-basis": "Generator minimum load basis",
    "battery-charge-taper-start": "Battery charge taper start",
    "battery-charge-taper-start-basis": "Battery charge taper start basis",
}


def test_p6_new_names_are_messages_and_legacy_names_stay_strings():
    for key, label in NAMES.items():
        definition = COMPONENT_PROPERTY_DEFINITIONS[key]
        assert not isinstance(definition.display_name, str), key
        assert served_text(definition.display_name) == label
    assert {(COMPONENT_PROPERTY_DEFINITIONS[k].unit, COMPONENT_PROPERTY_DEFINITIONS[k].kind) for k in NAMES} == {
        ("%", "CONTROL"), ("state", "CONTROL"), ("%", "PHYSICAL"), ("state", "PHYSICAL")}
    for key, definition in COMPONENT_PROPERTY_DEFINITIONS.items():
        if key not in NAMES:
            assert isinstance(definition.display_name, str), key
    assert sorted(NAMES.values()) == sorted(c.english for c in foundation_cases.CASES)
    assert served_text("Generator no-load fuel rate") == "Generator no-load fuel rate"


@pytest.mark.parametrize("case", [*foundation_cases.CASES, *model_profile_cases.CASES],
                         ids=lambda c: f"{c.key}-{c.variant}-{c.english[:20]}")
def test_every_0k4b_case_renders_its_english(case):
    assert render(message(case.key, **case.facts)) == case.english
