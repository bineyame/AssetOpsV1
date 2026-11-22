"""DD1.2 (spec §7 DD1.2; D-DD.37 to D-DD.39): the three operators' `/2` files and the nine binding conversions.

No database. The files are the world's input; these tests read them, never edit them.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from assetops_backend.onboarding.operator_file import OnboardRefused, parse_operator_file, roles_digest

BACKEND = Path(__file__).resolve().parent.parent
ON1 = BACKEND / "tests" / "fixtures" / "on1"
WORLD = BACKEND / "conversions" / "world"
FILES = {"lakeside-power": ("MINI_GRID", 3), "harvest-cold": ("COLD_CHAIN", 3), "metro-bus": ("EV_DEPOT", 3)}
ROLE_SET = {"MINI_GRID": "minigrid-roles-4", "COLD_CHAIN": "cold-roles-1", "EV_DEPOT": "ev-roles-1"}
VALID_FROM = "2026-06-30T21:00:00Z"


def _raw(slug: str) -> dict:
    return json.loads((ON1 / f"{slug}.onboarding.json").read_bytes())


@pytest.mark.parametrize("slug", FILES)
def test_each_file_is_format_2_and_parses(slug) -> None:
    vertical, count = FILES[slug]
    f = parse_operator_file((ON1 / f"{slug}.onboarding.json").read_bytes())
    assert f.format == "assetops.operator-onboarding/2" and f.data == "emulated" and len(f.sites) == count
    assert f.operator.vertical == vertical
    for site in f.sites:
        assert site.entry["valid_from"] == VALID_FROM and site.entry["timezone"] == "Africa/Nairobi"


@pytest.mark.parametrize("slug", FILES)
def test_people_follow_the_manifest_workflow(slug) -> None:
    import yaml
    manifest = yaml.safe_load((BACKEND.parent / "Docs/demo-sprint/product-direction-layer4/"
                               "demo-site-scenario-manifest.yaml").read_text(encoding="utf-8"))
    tenant = next(t for t in manifest["demo_workflow"]["tenants"] if t["tenant"] == slug)
    codes = {s["site"]: s["code"] for t in manifest["tenants"] if t["tenant"] == slug for s in t["sites"]}
    want = {(p["name"], p["role"], codes[p["site"]] if "site" in p else "") for p in tenant["people"]}
    got = {(p["name"], r["role"], r.get("site", "")) for p in _raw(slug)["people"] for r in p["roles"]}
    assert got == want
    assert all(p["email"] == f"{p['name'].lower()}@{slug}.example" for p in _raw(slug)["people"])
    assert {r for _, r, _ in got} >= {"OPERATOR_EXECUTIVE", "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST"}


def test_lakeside_roles_digest_is_unchanged_from_format_1() -> None:
    old = parse_operator_file((ON1 / "lakeside-power.v1.onboarding.json").read_bytes())
    new = parse_operator_file((ON1 / "lakeside-power.onboarding.json").read_bytes())
    assert roles_digest(old) == roles_digest(new)


def test_cold_rooms_carry_the_lab_foundation_with_six_kw_cooling() -> None:
    for site in _raw("harvest-cold")["sites"]:
        props = {p["property_key"]: p["value"] for c in site["components"] for p in c.get("properties", [])}
        assert len(props) == 13 and props["cold-cooling-capacity"] == 6.0  # D-DD.37
        compressor = next(c for c in site["components"] if c["id"] == "compressor-1")
        assert compressor["rating"] == {"value": 6.0, "unit": "kW"}


@pytest.mark.parametrize("code, chargers, limit, kw", [("EV-EMB", 10, 500, 60), ("EV-KAS", 4, 250, 50), ("EV-RUI", 12, 400, 60)])
def test_depots_carry_the_manifest_limits_ids_and_all_day_schedules(code, chargers, limit, kw) -> None:
    site = next(s for s in _raw("metro-bus")["sites"] if s["code"] == code)
    by_type: dict[str, list] = {}
    for c in site["components"]:
        by_type.setdefault(c["type"], []).append(c)
    assert len(by_type["EV_CHARGER"]) == chargers and len(by_type["EV_CONNECTOR"]) == 2 * chargers
    prop = lambda c, k: next(p["value"] for p in c["properties"] if p["property_key"] == k)  # noqa: E731
    feed = next(c for c in site["components"] if c["id"] == "feed-1")
    assert prop(feed, "ev-site-import-limit") == limit
    assert {prop(c, "ev-charger-max-power") for c in by_type["EV_CHARGER"]} == {kw}
    assert {prop(c, "ev-connector-max-power") for c in by_type["EV_CONNECTOR"]} == {kw}
    prefix = code[-3] .lower()  # e, k, r
    assert by_type["EV_CHARGER"][0]["id"] == f"ch-{prefix}1" and by_type["EV_CONNECTOR"][1]["id"] == f"ch-{prefix}1-c2"
    assert len(site["connector_enable_schedules"]) == 2 * chargers
    for s in site["connector_enable_schedules"]:
        assert s["time_zone"] == "Africa/Nairobi" and len(s["weekly"]) == 7
        assert {(w["local_start"], w["local_end"], w["utc_offset_minutes"]) for w in s["weekly"]} == {("00:00", "24:00", 180)}


def test_ev_names_carry_the_manifest_codes() -> None:
    site = next(s for s in _raw("metro-bus")["sites"] if s["code"] == "EV-KAS")
    names = {c["id"]: c["name"] for c in site["components"]}
    assert names["ch-k2"] == "Charger CH-K2" and names["ch-k2-c2"] == "CH-K2 connector 2"
    assert any(d["device_id"] == "ch-k2-c2-connector-meter" and d["display_name"] == "CH-K2 connector 2 meter"
               for d in site["devices"])


def _mutate_schedule(end: str, start: str = "00:00") -> bytes:
    doc = copy.deepcopy(_raw("metro-bus"))
    for w in doc["sites"][0]["connector_enable_schedules"][0]["weekly"]:
        w["local_start"], w["local_end"] = start, end
    return json.dumps(doc).encode("utf-8")


def test_a_day_may_end_at_24_00_and_never_start_there() -> None:  # D-DD.39
    parse_operator_file(_mutate_schedule("24:00"))
    for bad in (("24:00", "24:00"), ("23:59", "24:01")):
        with pytest.raises(OnboardRefused) as refused:
            parse_operator_file(_mutate_schedule(bad[1] if bad[0] == "23:59" else "24:00", start=bad[0]))
        assert refused.value.code == "ONBOARD_SITE_INVALID"


@pytest.mark.parametrize("slug", FILES)
def test_every_site_has_a_conversion_listing_every_device_signal(slug) -> None:
    vertical, _ = FILES[slug]
    for site in _raw(slug)["sites"]:
        fixture = json.loads((WORLD / f"{site['code']}-bindings.json").read_text(encoding="utf-8"))
        assert fixture["site_code"] == site["code"] and fixture["role_set"] == ROLE_SET[vertical]
        assert fixture["effective_from"] == VALID_FROM and fixture["declare_signals"] == []
        bound = {(b["device_id"], b["signal_id"]) for b in fixture["bindings"]}
        declared = {(d["device_id"], s["signal_id"]) for d in site["devices"] for s in d["signals"]}
        assert bound == declared
        assert {b["asset_code"] for b in fixture["bindings"]} <= {c["id"] for c in site["components"]}


def test_kisiwa_and_mto_list_every_units_device() -> None:
    kisiwa = json.loads((WORLD / "KISIWA-001-bindings.json").read_text(encoding="utf-8"))
    assert {b["device_id"] for b in kisiwa["bindings"] if b["role"] == "generator_power"} == {
        "gen-ks-01-controller", "gen-ks-02-controller"}
    mto = json.loads((WORLD / "MTO-001-bindings.json").read_text(encoding="utf-8"))
    assert {b["device_id"] for b in mto["bindings"] if b["role"] == "pv_power"} == {
        "inv-mt-01-controller", "inv-mt-02-controller"}
