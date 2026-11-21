"""0K4b P5 (D-0K4.21): `assumed_site` appends exactly the six assumed rows, and never overwrites a declared one.

The expected rows are this test's own literal (W2), not read back from `ASSUMED_PROPERTIES`.
"""

from __future__ import annotations

import copy

import pytest

from kobo import KOBO_TEMPLATE, KOBO_SITE_ID, component
from kobo_assumed import ASSUMPTION_NOTE, assumed_site
from fixtures import site_from_template
from assetops_backend.sites.site_parsing import parse_site_document, render_site_document

EXPECTED = {
    "generator": [
        {"property_key": "generator-no-load-fuel-rate", "value": 3.3, "unit": "L/h"},
        {"property_key": "generator-no-load-fuel-rate-basis", "value": "GENERIC_DEFAULT", "unit": "state"},
        {"property_key": "generator-minimum-load", "value": 30, "unit": "%"},
        {"property_key": "generator-minimum-load-basis", "value": "GENERIC_DEFAULT", "unit": "state"},
    ],
    "battery": [
        {"property_key": "battery-charge-taper-start", "value": 95, "unit": "%"},
        {"property_key": "battery-charge-taper-start-basis", "value": "GENERIC_DEFAULT", "unit": "state"},
    ],
}


def _document():
    site = site_from_template(KOBO_TEMPLATE, site_id=KOBO_SITE_ID, timezone="Africa/Addis_Ababa")
    return copy.deepcopy(render_site_document(site))


def test_p5_assumed_site_appends_exactly_the_six_rows():
    before = _document()
    after = copy.deepcopy(before)
    assumed_site(after)
    for component_id, rows in EXPECTED.items():
        old = component(before, component_id).get("properties") or []
        new = component(after, component_id)["properties"]
        assert new[: len(old)] == old
        assert new[len(old):] == [{**row, "source": "SITE", "source_version": 1} for row in rows]
    untouched = [c["component_id"] for c in before["foundation"]["components"] if c["component_id"] not in EXPECTED]
    assert all(component(before, c) == component(after, c) for c in untouched)
    parsed = parse_site_document(after, source="the assumed Kobo site")
    assert parsed.site_id == KOBO_SITE_ID
    for word in ("3.3 L/h", "30 %", "95 %", "assumed"):
        assert word in ASSUMPTION_NOTE


def test_p5_a_key_already_present_is_never_overwritten():
    document = _document()
    component(document, "battery").setdefault("properties", []).append(
        {"property_key": "battery-charge-taper-start", "value": 90, "unit": "%", "source": "SITE",
         "source_version": 1}
    )
    with pytest.raises(KeyError):
        assumed_site(document)
