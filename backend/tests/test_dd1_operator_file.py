"""DD1.1 (spec `specs/DD-demo-data/spec.md` §7 DD1.1; D-DD.6, D-DD.29): onboarding every vertical, format `/2`.

One parse per vertical, one refusal per new key misuse (ONBOARD_SITE_INVALID), and every `/1` file's digests unchanged
byte for byte (pinned from `main`'s code before DD1.1).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml

from assetops_backend.onboard_operator import SENTENCES
from assetops_backend.onboarding.operator_file import (OnboardRefused, parse_operator_file, roles_digest,
                                                      site_document, site_source)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
V1 = FIXTURES / "on1" / "lakeside-power.v1.onboarding.json"
#: Computed with `main`'s operator_file.py (57cecf954) from the `/1` file; DD1.1 must not move them.
V1_ROLES = "cfdfc54bf41514ef011e36de3da1734fbd5ae11a00a7bf76df0c23cbb6ab22a3"
V1_SITES = {"KISIWA-001": "3b31b0930c00846270cb254d357f17a15e612f5c280878a611c3258d5352bf01",
            "KOBO-001": "26e26e48154315af89463eca2f8edf5e98efd8995317c7fd63d16765dd7fe193",
            "MTO-001": "079a1c8f99a3bec96ac8b73280828a309b23ad256d7f6973963b61d2ccda2446"}
PEOPLE = [{"email": "e@x.example", "name": "Esther", "roles": [{"role": "OPERATOR_EXECUTIVE"}]},
          {"email": "k@x.example", "name": "Kevin", "roles": [{"role": "FINANCE_AND_COMMERCIAL_LEAD"}]},
          {"email": "n@x.example", "name": "Njeri", "roles": [{"role": "ANALYST"}]}]


def _site_from_lab(name: str, code: str) -> dict:
    """A `/2` file Site carrying a w2 lab fixture's foundation (components, properties, devices, topology)."""
    lab = yaml.safe_load((FIXTURES / "w2" / name).read_text(encoding="utf-8"))
    f = lab["foundation"]
    site = {"code": code, "name": code.title(), "timezone": lab["timezone"], "country": "Kenya", "locality": "X",
            "lifecycle": "ACTIVE", "valid_from": "2026-06-30T21:00:00Z",
            "components": [{k2: c[k1] for k1, k2 in (("component_id", "id"), ("component_type", "type"),
                                                      ("display_name", "name"), ("rating", "rating"),
                                                      ("properties", "properties")) if k1 in c}
                           for c in f["components"]]}
    for key in ("devices", "topology", "connector_enable_schedules"):
        if key in f:
            site[key] = f[key]
    return site


def _file(vertical: str, site: dict) -> dict:
    return {"format": "assetops.operator-onboarding/2", "data": "emulated",
            "operator": {"slug": "x-op", "name": "X", "vertical": vertical}, "sites": [site], "people": PEOPLE}


def _bytes(doc: dict) -> bytes:
    return json.dumps(doc).encode("utf-8")


@pytest.mark.parametrize("vertical, lab, site_type", [
    ("COLD_CHAIN", "cold-lab-001.yaml", "COLDCHAIN"),
    ("EV_DEPOT", "ev-lab-001.yaml", "EV_CHARGING"),
])
def test_each_new_vertical_onboards_with_its_foundation(vertical, lab, site_type) -> None:
    f = parse_operator_file(_bytes(_file(vertical, _site_from_lab(lab, "S-1"))))
    doc = site_document(f.sites[0], real=False, site_type=site_type)
    record = site_source(f, f.sites[0]).record
    assert doc["site_type"] == site_type and record.site_type == site_type
    assert doc["foundation"]["devices"] and doc["foundation"]["topology"]["nodes"]
    assert any(c.get("properties") for c in doc["foundation"]["components"])


def test_mini_grid_onboards_on_2_with_devices() -> None:
    v1 = json.loads(V1.read_bytes())
    doc = copy.deepcopy(v1)
    site = doc["sites"][1]
    site["components"].append({"id": "fuel-tank", "type": "FUEL_TANK", "name": "Tank"})
    site["devices"] = [{"device_id": "fuel-level-sensor", "device_type": "SENSOR", "display_name": "Fuel level",
                        "component_id": "fuel-tank",
                        "signals": [{"signal_id": "fuel-level", "display_name": "Fuel level", "unit": "L"}]}]
    doc["format"] = "assetops.operator-onboarding/2"
    f = parse_operator_file(_bytes(doc))
    assert f.format == "assetops.operator-onboarding/2"
    assert site_source(f, f.sites[1]).record.site_type == "MINIGRID"


def test_any_other_vertical_refuses_with_the_new_sentence() -> None:
    for vertical in ("HYDRO", "mini_grid", ""):
        with pytest.raises(OnboardRefused) as caught:
            parse_operator_file(_bytes(_file(vertical, _site_from_lab("cold-lab-001.yaml", "S-1"))))
        assert (caught.value.code, caught.value.where) == ("ONBOARD_VERTICAL", "operator.vertical")
    assert SENTENCES["ONBOARD_VERTICAL"] == "This operator's business type is not onboarded yet."


def _misuse(mutate) -> OnboardRefused:
    site = _site_from_lab("cold-lab-001.yaml", "S-1")
    mutate(site)
    with pytest.raises(OnboardRefused) as caught:
        parse_operator_file(_bytes(_file("COLD_CHAIN", site)))
    return caught.value


MISUSES = {
    "a device naming an unknown component": lambda s: s["devices"][0].update(component_id="nowhere"),
    "a device with an unknown key": lambda s: s["devices"][0].update(colour="red"),
    "a topology node naming an unknown component": lambda s: s["topology"]["nodes"][0].update(component_id="nowhere"),
    "topology not an object": lambda s: s.update(topology=[]),
    "a property with an unknown key": lambda s: s["components"][0]["properties"][0].update(key="x"),
    "a property value of the wrong type": lambda s: s["components"][0]["properties"][0].update(value="warm"),
    "properties not a list": lambda s: s["components"][0].update(properties={}),
    "an EV schedule on a cold Site": lambda s: s.update(connector_enable_schedules=[
        {"connector_asset_id": "room-1", "time_zone": s["timezone"], "weekly": []}]),
}


@pytest.mark.parametrize("name", sorted(MISUSES))
def test_each_new_key_misuse_refuses_site_invalid(name) -> None:
    refusal = _misuse(MISUSES[name])
    assert (refusal.code, refusal.where) == ("ONBOARD_SITE_INVALID", "sites[0]"), name


def test_new_keys_stay_refused_in_a_1_file() -> None:
    v1 = json.loads(V1.read_bytes())
    for where, mutate in (("sites[0]", lambda d: d["sites"][0].update(devices=[])),
                          ("sites[0].components[0]", lambda d: d["sites"][0]["components"][0].update(properties=[]))):
        doc = copy.deepcopy(v1)
        mutate(doc)
        with pytest.raises(OnboardRefused) as caught:
            parse_operator_file(_bytes(doc))
        assert (caught.value.code, caught.value.where) == ("ONBOARD_STRUCTURE", where)


def test_every_1_file_digests_byte_for_byte_as_before() -> None:
    f = parse_operator_file(V1.read_bytes())
    assert roles_digest(f) == V1_ROLES
    assert {s.code: site_source(f, s).sha256 for s in f.sites} == V1_SITES
