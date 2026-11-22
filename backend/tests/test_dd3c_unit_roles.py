"""DD3c part 1 (spec DD3.4; D-DD.41, D-DD.43): the Site-from-units rule and the lead-unit policy read, pure.

The parity class: a one-unit Site (Kobo) reads as today, byte for byte, through every function.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from assetops_backend.sites import unit_roles as ur

ON1 = Path(__file__).resolve().parent / "fixtures" / "on1" / "lakeside-power.onboarding.json"


def _components(code: str) -> list[dict]:
    """The Site's Foundation components as the Foundation content holds them (`component_id`, `component_type`)."""
    site = next(s for s in json.loads(ON1.read_bytes())["sites"] if s["code"] == code)
    return [{"component_id": c["id"], "component_type": c["type"], "properties": c.get("properties", [])}
            for c in site["components"]]


# --- power: summed, absent if any unit is absent, named by unit -------------------------------------------------

def test_power_is_the_sum_of_the_units() -> None:
    got = ur.site_power({"gen-ks-01": Decimal("12.5"), "gen-ks-02": Decimal("30.25")})
    assert got == ur.SiteValue(Decimal("42.75"), ())


def test_power_is_absent_when_a_unit_is_absent_and_names_it() -> None:
    got = ur.site_power({"gen-ks-01": Decimal("12.5"), "gen-ks-02": None})
    assert got == ur.SiteValue(None, ("gen-ks-02",))
    assert ur.site_power({"a": None, "b": None}).missing == ("a", "b")


def test_power_series_is_aggregated_per_step_over_the_union_of_steps() -> None:
    got = ur.site_power_series({"inv-mt-01": {1: Decimal("3"), 2: Decimal("4")}, "inv-mt-02": {1: Decimal("5")}})
    assert got == {1: ur.SiteValue(Decimal("8"), ()), 2: ur.SiteValue(None, ("inv-mt-02",))}


def test_no_units_is_absent_not_zero() -> None:
    assert ur.site_power({}) == ur.SiteValue(None, ())


# --- generator state: RUNNING > STARTING > STOPPED > FAILED --------------------------------------------------------

@pytest.mark.parametrize(("states", "site"), [
    (("RUNNING", "FAILED"), "RUNNING"),
    (("STOPPED", "RUNNING"), "RUNNING"),
    (("STARTING", "STOPPED"), "STARTING"),
    (("FAILED", "STARTING"), "STARTING"),
    (("STOPPED", "FAILED"), "STOPPED"),
    (("FAILED", "STOPPED"), "STOPPED"),
    (("FAILED", "FAILED"), "FAILED"),
])
def test_generator_state_order(states, site) -> None:
    assert ur.site_generator_state(dict(zip(("u1", "u2"), states))) == ur.SiteValue(site, ())


def test_generator_state_absent_when_a_unit_is_absent() -> None:  # pre-flight Q4 default
    assert ur.site_generator_state({"u1": "RUNNING", "u2": None}) == ur.SiteValue(None, ("u2",))


# --- events: the union in time order, each keeping its unit --------------------------------------------------------

def test_events_union_in_time_order_keeping_the_unit() -> None:
    got = ur.site_events({"g1": [(3, "REQUEST"), (9, "RESULT")], "g2": [(1, "REQUEST"), (3, "RESULT")]},
                         at=lambda e: e[0])
    assert got == (("g2", (1, "REQUEST")), ("g1", (3, "REQUEST")), ("g2", (3, "RESULT")), ("g1", (9, "RESULT")))


# --- unit properties: rating, burn, lead-unit policy ---------------------------------------------------------------

def test_units_are_in_declared_order_and_the_lead_is_the_first_generator() -> None:
    comps = _components("KISIWA-001")
    assert [u["component_id"] for u in ur.units(comps, "GENERATOR")] == ["gen-ks-01", "gen-ks-02"]
    assert ur.lead_unit(comps)["component_id"] == "gen-ks-01"


def test_rating_is_the_sum_of_non_failed_units() -> None:
    comps = _components("KISIWA-001")
    assert ur.site_rating(comps) == ur.SiteValue(Decimal("120"), ())
    assert ur.site_rating(comps, {"gen-ks-01": "FAILED", "gen-ks-02": "RUNNING"}) == ur.SiteValue(Decimal("60"), ())
    assert ur.site_rating(comps, {"gen-ks-01": "RUNNING", "gen-ks-02": None}) == ur.SiteValue(None, ("gen-ks-02",))


def test_litres_are_the_sum_of_each_units_own_burn() -> None:
    assert ur.site_litres({"g1": Decimal("1.2"), "g2": Decimal("0.8")}) == ur.SiteValue(Decimal("2.0"), ())
    assert ur.site_litres({"g1": Decimal("1.2"), "g2": None}) == ur.SiteValue(None, ("g2",))


def test_policy_is_read_from_the_lead_unit() -> None:
    policy = ur.lead_policy(_components("KISIWA-001"))
    assert sorted(policy) == sorted(ur.POLICY_KEYS)
    assert policy["start-soc-threshold"]["value"] == 35


def test_a_non_lead_unit_carrying_policy_is_refused() -> None:
    comps = _components("KISIWA-001")
    second = next(c for c in comps if c["component_id"] == "gen-ks-02")
    second["properties"] = [*second["properties"], {"property_key": "start-delay", "value": 5, "unit": "min"}]
    with pytest.raises(ur.UnitRolesRefused) as refused:
        ur.lead_policy(comps)
    assert refused.value.code == "TEL_FOUNDATION" and refused.value.unit == "gen-ks-02"


# --- parity: a one-unit Site (Kobo) gives the unit's own value, byte for byte --------------------------------------

KOBO_VALUES = [Decimal("17.30"), Decimal("-0.0"), Decimal("0E-3"), Decimal("40"), 12.5, -0.0, 7, "8.10", None]


@pytest.mark.parametrize("value", KOBO_VALUES, ids=repr)
def test_one_unit_power_and_litres_are_the_units_own_value(value) -> None:
    for fn in (ur.site_power, ur.site_litres):
        got = fn({"generator": value})
        assert got.value is value if value is not None else got == ur.SiteValue(None, ("generator",))
        if value is not None:
            assert type(got.value) is type(value) and repr(got.value) == repr(value)


@pytest.mark.parametrize("state", ["RUNNING", "STARTING", "STOPPED", "FAILED", "UNMAPPED-TEXT"])
def test_one_unit_state_is_the_units_own_state(state) -> None:
    assert ur.site_generator_state({"generator": state}) == ur.SiteValue(state, ())


def test_kobo_one_unit_reads_as_today() -> None:
    comps = _components("KOBO-001")
    gen = next(c for c in comps if c["component_type"] == "GENERATOR")
    rated = next(p["value"] for p in gen["properties"] if p["property_key"] == ur.RATING_KEY)
    got = ur.site_rating(comps)
    assert got.value is rated and got.missing == ()
    policy = ur.lead_policy(comps)
    assert {k: v for k, v in policy.items()} == {
        p["property_key"]: p for p in gen["properties"] if p["property_key"] in ur.POLICY_KEYS}
    assert all(policy[k] is next(p for p in gen["properties"] if p["property_key"] == k) for k in policy)
    series = {"generator": {"t1": Decimal("17.30"), "t2": Decimal("0E-3")}}
    assert {k: v.value for k, v in ur.site_power_series(series).items()} == series["generator"]
    events = [("t2", "RESULT"), ("t1", "REQUEST")]
    assert ur.site_events({"generator": events}, at=lambda e: e[0]) == (
        ("generator", ("t1", "REQUEST")), ("generator", ("t2", "RESULT")))
