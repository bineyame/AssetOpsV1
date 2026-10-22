"""W4-03 unit 2a: pure Scenario assumption, decimal, currency and calculation vectors (no database)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from assetops_backend.mini_decisions import scenario_rules as r
from assetops_backend.mini_decisions.model import DecisionRefused


def a(key, value, unit, source="Authored trial proposal"):
    return {"key": key, "value": value, "unit": unit, "source": source}


LOAD = [a("proposed_kw", "10", "kW"), a("duration_hours", "1", "h")]
TARIFF = a("tariff_per_kwh", "0.25", "USD/kWh", "Authored illustrative tariff")


def refused(kind, items):
    with pytest.raises(DecisionRefused) as caught:
        r.assumptions(kind, items)
    assert (caught.value.code, caught.value.status) == ("DECISION_INPUT_INVALID", 422)


def day(n, decision="ELIGIBLE", low=10, high=None):
    bound = {"low": low, "high": low + 2 if high is None else high} if decision == "ELIGIBLE" else None
    return r.DayRow(f"2026-10-0{n}", decision, bound)


# ---- currency / tariff unit (closure 2 N1) -------------------------------------------------------------------------

def test_usd_per_kwh_is_accepted_and_iso4217_literal_is_refused():
    assert r.tariff_currency("USD/kWh") == "USD"
    assert r.tariff_currency("KES/kWh") == "KES"
    for unit in ("ISO4217/kWh", "usd/kWh", "XYZ/kWh", "USD/kwh", "USD/MWh", "USD", "", None, 1):
        with pytest.raises(DecisionRefused):
            r.tariff_currency(unit)
    assert r.assumptions("TARIFF_ONLY", [TARIFF])[0]["unit"] == "USD/kWh"
    refused("TARIFF_ONLY", [a("tariff_per_kwh", "0.25", "ISO4217/kWh")])


# ---- closed assumption keys and values (closure 1 Q7-Q11) ----------------------------------------------------------

def test_closed_keys_per_kind():
    assert [x["key"] for x in r.assumptions("PRODUCTIVE_LOAD", [TARIFF, *LOAD])] == [
        "duration_hours", "proposed_kw", "tariff_per_kwh"]
    assert r.assumptions("STOP_SOC", [a("stop_soc", "35", "%")])[0]["value"] == "35"
    other = r.assumptions("OTHER", [a("declared_value", "-4.50", None), a("declared_unit", " L/day ", None)])
    assert other == [{"key": "declared_unit", "value": "L/day", "unit": None, "source": "Authored trial proposal"},
                     {"key": "declared_value", "value": "-4.5", "unit": None, "source": "Authored trial proposal"}]
    refused("PRODUCTIVE_LOAD", [LOAD[0]])                                    # missing required key
    refused("PRODUCTIVE_LOAD", [*LOAD, a("eligible_days", "3", "d")])        # derived, never authored
    refused("PRODUCTIVE_LOAD", [*LOAD, LOAD[0]])                             # duplicate key
    refused("TARIFF_ONLY", [TARIFF, LOAD[0]])                                # key of another kind
    refused("STOP_SOC", [])
    refused("NOT_A_KIND", LOAD)
    refused("PRODUCTIVE_LOAD", "not-a-list")
    refused("PRODUCTIVE_LOAD", [{**LOAD[0], "extra": 1}, LOAD[1]])
    refused("PRODUCTIVE_LOAD", [{k: v for k, v in LOAD[0].items() if k != "source"}, LOAD[1]])
    refused("OTHER", [a("declared_value", "1", None), a("declared_unit", "x" * 33, None)])


@pytest.mark.parametrize("item", [
    a("proposed_kw", "0", "kW"), a("proposed_kw", "-1", "kW"), a("proposed_kw", "10", "W"),
    a("proposed_kw", 10, "kW"), a("proposed_kw", 10.0, "kW"), a("proposed_kw", "1e1", "kW"),
    a("proposed_kw", "", "kW"), a("proposed_kw", "NaN", "kW"), a("proposed_kw", "10", "kW", "  "),
])
def test_proposed_kw_refusals(item):
    refused("PRODUCTIVE_LOAD", [item, LOAD[1]])


@pytest.mark.parametrize("value,ok", [("1", True), ("0.5", True), ("0", False), ("1.01", False), ("-0.5", False)])
def test_duration_is_inside_the_noon_hour(value, ok):
    items = [LOAD[0], a("duration_hours", value, "h")]
    if ok:
        r.assumptions("PRODUCTIVE_LOAD", items)
    else:
        refused("PRODUCTIVE_LOAD", items)


@pytest.mark.parametrize("value,ok", [("0", True), ("100", True), ("100.1", False), ("-1", False)])
def test_stop_soc_percent_range(value, ok):
    items = [a("stop_soc", value, "%")]
    if ok:
        r.assumptions("STOP_SOC", items)
    else:
        refused("STOP_SOC", items)


def test_tariff_must_be_positive():
    refused("TARIFF_ONLY", [a("tariff_per_kwh", "0", "USD/kWh")])


# ---- decimal representation (closure 4 S8) -------------------------------------------------------------------------

def test_physical_numbers_serialize_deterministically():
    assert r.physical_range({"low": 18, "high": 18.0}) == {"low": "18", "high": "18"}
    assert r.physical_range({"low": 17.35, "high": 18.125}) == {"low": "17.35", "high": "18.125"}
    assert r.decimal_text(r.physical_decimal(1e-7)) == "0.0000001"          # never exponent form
    assert r.decimal_text(Decimal("2.500")) == "2.5"
    assert r.physical_range(None) is None
    for bad in ({"low": float("nan"), "high": 1}, {"low": 1, "high": float("inf")}, {"low": -1, "high": 1},
                {"low": 3, "high": 2}, {"low": True, "high": 1}, {"low": 1}):
        with pytest.raises(DecisionRefused):
            r.physical_range(bad)


# ---- calculation (closure 1 Q7-Q11, closure 4 S16) ----------------------------------------------------------------

def test_pure_250_vector_five_eligible_days():
    items = r.assumptions("PRODUCTIVE_LOAD", [*LOAD, TARIFF])
    days = [day(n, low=10 + n) for n in range(6, 11)]
    assert r.calculate("PRODUCTIVE_LOAD", items, days) == {
        "state": "GROSS_SCENARIO", "energy_kwh": "10",
        "gross_sales": {"amount": "2.5", "currency": "USD", "basis": "SCENARIO"}, "reason": None}
    assert r.eligible_days(days) == 5


def test_excluded_day_is_pinned_but_not_counted():
    items = r.assumptions("PRODUCTIVE_LOAD", [*LOAD, TARIFF])
    days = [day(6, "EXCLUDED"), *[day(n, low=18.0) for n in range(7, 11)]]
    result = r.calculate("PRODUCTIVE_LOAD", items, days)
    assert (result["state"], result["energy_kwh"], result["gross_sales"]["amount"]) == ("GROSS_SCENARIO", "10", "2.5")
    assert r.eligible_days(days) == 4


def test_exact_decimal_arithmetic():
    items = r.assumptions("PRODUCTIVE_LOAD", [a("proposed_kw", "3.3", "kW"), a("duration_hours", "0.3", "h"),
                                              a("tariff_per_kwh", "0.1", "KES/kWh")])
    result = r.calculate("PRODUCTIVE_LOAD", items, [day(6, low=4)])
    assert result["energy_kwh"] == "0.99"
    assert result["gross_sales"] == {"amount": "0.099", "currency": "KES", "basis": "SCENARIO"}


def test_withheld_and_no_calculation_states():
    load = r.assumptions("PRODUCTIVE_LOAD", LOAD)
    assert r.calculate("PRODUCTIVE_LOAD", load, [day(n) for n in range(6, 11)]) == {
        "state": "ENERGY_ONLY", "energy_kwh": "10", "gross_sales": None, "reason": None}
    assert r.calculate("PRODUCTIVE_LOAD", load, [])["state"] == "NO_CALCULATION"
    assert r.calculate("PRODUCTIVE_LOAD", load, [day(6, "EXCLUDED")] * 5)["reason"] == "NO_ELIGIBLE_DAY"
    assert r.calculate("PRODUCTIVE_LOAD", load, [day(6), day(7, "LIMITED")])["reason"] == "INCOMPLETE_STUDY"
    assert r.calculate("PRODUCTIVE_LOAD", load, [day(6), day(7, "CONFLICT")])["state"] == "WITHHELD"
    below = r.calculate("PRODUCTIVE_LOAD", load, [day(6), day(7, low=9.99)])
    assert (below["state"], below["energy_kwh"], below["reason"]) == ("WITHHELD", None, "HEADROOM_BELOW_LOAD")
    tariff = r.assumptions("TARIFF_ONLY", [TARIFF])
    assert r.calculate("TARIFF_ONLY", tariff, [day(6)]) == {
        "state": "NO_CALCULATION", "energy_kwh": None, "gross_sales": None, "reason": "NOT_PRODUCTIVE_LOAD"}
    stop = r.assumptions("STOP_SOC", [a("stop_soc", "40", "%")])
    assert r.calculate("STOP_SOC", stop, [day(6)])["state"] == "NO_CALCULATION"


def test_final_review_l4_inexact_product_is_refused_not_rounded():
    """Final review L4: authored decimal strings are unbounded, so a product that would round in the 28-digit
    context is 422 `DECISION_INPUT_INVALID`, never a silently rounded amount; an exact product is unchanged."""
    items = r.assumptions("PRODUCTIVE_LOAD", [a("proposed_kw", "1.000000000000001", "kW"),
                                              a("duration_hours", "0.999999999999999", "h")])
    with pytest.raises(DecisionRefused) as caught:
        r.calculate("PRODUCTIVE_LOAD", items, [day(6, low=4)])
    assert (caught.value.code, caught.value.status) == ("DECISION_INPUT_INVALID", 422)
    gross = r.assumptions("PRODUCTIVE_LOAD", [a("proposed_kw", "3", "kW"), a("duration_hours", "1", "h"),
                                              a("tariff_per_kwh", "0.12345678901234567890123456789", "USD/kWh")])
    with pytest.raises(DecisionRefused):
        r.calculate("PRODUCTIVE_LOAD", gross, [day(6, low=4)])
