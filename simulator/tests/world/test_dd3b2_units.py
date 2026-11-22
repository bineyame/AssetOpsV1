"""DD3b2 (spec DD §4.2, §4.3; D-DD.128, D-DD.129, D-DD.126, D-DD.145, D-DD.146): the writer runs units.

This part's first tests: Kisiwa's and Mto's kit in Lakeside's `/2` file (D-DD.128)."""

from __future__ import annotations

import json

from .conftest import REPOSITORY_ROOT

ONBOARDING = REPOSITORY_ROOT / "backend" / "tests" / "fixtures" / "on1" / "lakeside-power.onboarding.json"


def _sites() -> dict[str, dict]:
    return {s["code"]: s for s in json.loads(ONBOARDING.read_text(encoding="utf-8"))["sites"]}


def _props(component: dict) -> dict[str, tuple]:
    return {p["property_key"]: (p["value"], p["unit"], p["source"], p["source_version"]) for p in component["properties"]}


def test_kisiwa_and_mto_units_carry_the_generic_kit_with_its_basis() -> None:
    """Per generator: no-load 0.08 L/h per kW of rating, minimum load 30 %; per Site taper 95 %; each GENERIC_DEFAULT,
    source SITE, version 1 (D-DD.128, spec §4.2, owner 7 Nov)."""
    for code, no_load in (("KISIWA-001", {"gen-ks-01": 4.8, "gen-ks-02": 4.8}), ("MTO-001", {"generator": 2.4})):
        components = _sites()[code]["components"]
        for unit, rate in no_load.items():
            props = _props(next(c for c in components if c["id"] == unit))
            assert props["generator-no-load-fuel-rate"] == (rate, "L/h", "SITE", 1)
            assert props["generator-minimum-load"] == (30, "%", "SITE", 1)
            for key in ("generator-no-load-fuel-rate-basis", "generator-minimum-load-basis"):
                assert props[key] == ("GENERIC_DEFAULT", "state", "SITE", 1)
        battery = _props(next(c for c in components if c["type"] == "BATTERY"))
        assert battery["battery-charge-taper-start"] == (95, "%", "SITE", 1)
        assert battery["battery-charge-taper-start-basis"] == ("GENERIC_DEFAULT", "state", "SITE", 1)


def test_each_inverter_declares_its_share_of_the_array_by_rating() -> None:
    """`pv-array-share` = the inverter's AC limit / the Site's summed limits: Mto 50 % each, Kisiwa's one 100 %."""
    for code, shares in (("KISIWA-001", {"pv-inverter": 100}), ("MTO-001", {"inv-mt-01": 50, "inv-mt-02": 50})):
        for unit, share in shares.items():
            props = _props(next(c for c in _sites()[code]["components"] if c["id"] == unit))
            assert props["pv-array-share"] == (share, "%", "SITE", 1)
            assert props["pv-array-share-basis"] == ("GENERIC_DEFAULT", "state", "SITE", 1)


def test_every_tank_rating_is_its_declared_capacity() -> None:
    """The 400 L template placeholder is gone: each FUEL_TANK's rating equals its `tank-capacity` (D-DD.128)."""
    expected = {"KOBO-001": 2500, "KISIWA-001": 5000, "MTO-001": 1000}
    for code, site in _sites().items():
        tank = next(c for c in site["components"] if c["type"] == "FUEL_TANK")
        assert tank["rating"] == {"value": expected[code], "unit": "L"}
        assert _props(tank)["tank-capacity"][0] == expected[code]
