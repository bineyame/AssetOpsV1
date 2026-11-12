"""PR-1 (BL-68): the server-built `price_action` on every unpriced item. No database.

Covers: the PRICES Ref; every early-warning kind; an UNPRICED estate money line and the Portfolio card built from it;
a mini Finding's UNPRICED fuel cost; and a mill verification value without a price. No write path is added: the
price route still refuses every request (`HUMAN_PRINCIPAL_REQUIRED`, unchanged and tested elsewhere)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from assetops_backend.actions import verification_families as vf
from assetops_backend.chain import refs as R
from assetops_backend.estate import financials as fin
from assetops_backend.estate import portfolio
from assetops_backend.finding_api import with_price_action
from assetops_backend.outcomes import price_action as pa
from assetops_backend.outcomes.warnings import KINDS
from test_out_c1_never_money import every_rule, money_hits

PRICES = "/financials/prices"


def _shape_ok(action: dict, site: str) -> None:
    assert action["href"] == R.href_for(action["link_ref"])
    assert action["link_ref"]["kind"] == "PRICES" and action["link_ref"]["site"] == site
    assert action["href"].startswith(f"/sites/{site}{PRICES}")
    assert action["label"].endswith(" →")
    if action["kind"] == pa.SET_PRICE and action["key"] not in pa.STORED_KEYS:
        assert action["label"] == "What pricing this needs →"
    if action["kind"] == pa.SET_PRICE:
        assert set(action) == {"kind", "key", "label", "href", "link_ref"}
        assert action["key"] in pa.PRICE_NOUN and action["href"].endswith(f"?key={action['key']}")
    else:
        assert action["kind"] == pa.NEEDS_MODEL
        assert set(action) == {"kind", "need_key", "text", "label", "href", "link_ref"}
        assert action["text"] == pa.NEED_TEXT[action["need_key"]] and action["label"] == pa.NEEDS_LABEL
        assert action["href"].endswith(f"?need={action['need_key']}")
    assert money_hits(action) == [], money_hits(action)


# --- the Ref ------------------------------------------------------------------------------------------------------

def test_prices_ref_paths() -> None:
    assert R.href_for(R.prices_ref("KOBO-001")) == "/sites/KOBO-001/financials/prices"
    assert R.href_for(R.prices_ref("KOBO-001", key="repair_visit_cost")) == (
        "/sites/KOBO-001/financials/prices?key=repair_visit_cost")
    assert R.href_for(R.prices_ref("GH 01/a", need="bus_roster")) == "/sites/GH%2001%2Fa/financials/prices?need=bus_roster"
    with pytest.raises(ValueError):
        R.prices_ref("KOBO-001", key="repair_visit_cost", need="bus_roster")


# --- early warnings -----------------------------------------------------------------------------------------------

def test_every_warning_kind_has_a_spec() -> None:
    assert set(pa.WARNING_SPEC) == set(KINDS)


def test_every_warning_wires_a_price_action_without_money() -> None:
    ws = every_rule()
    assert {w.kind for w in ws} == set(KINDS)  # non-vacuous: every rule fired
    for w in ws:
        action = w.wire("GH-01", "GreenHarvest")["price_action"]
        _shape_ok(action, "GH-01")
        spec = pa.WARNING_SPEC[w.kind]
        assert action["kind"] == spec.kind


def test_warning_words_follow_the_spec() -> None:
    by_kind = {w.kind: w.wire("GH-01", "GreenHarvest")["price_action"] for w in every_rule()}
    assert by_kind["REPEATED_MAINTENANCE_NO_RESULT"]["label"] == "What pricing this needs →"
    assert by_kind["REPEATED_MAINTENANCE_NO_RESULT"]["key"] == "repair_visit_cost"
    assert by_kind["CHARGER_FAULT_OVERDUE_INSPECTION"]["label"] == "What pricing this needs →"
    assert by_kind["PLAN_OVERDUE"]["key"] == by_kind["PLAN_DUE_SOON"]["key"] == "planned_service_cost"
    assert by_kind["BATTERY_NEAR_RESERVE"]["label"] == "What is needed to price this →"
    assert by_kind["BATTERY_NEAR_RESERVE"]["text"].startswith("Battery wear is measured, not priced.")
    assert by_kind["CONNECTOR_OUT_OF_SERVICE"]["need_key"] == "bus_roster"
    assert by_kind["PEAK_NEAR_IMPORT_LIMIT"]["need_key"] == "demand_forecast"


# --- estate money lines and the Portfolio card --------------------------------------------------------------------

SITE = {"site_id": "00000000-0000-0000-0000-000000000001", "site_code": "KOBO-001", "site_name": "Kobo",
        "site_code_key": "kobo-001"}


def _line(category: str, decision: tuple) -> dict:
    return fin._line(SITE, fin.MINI_GRID, category, "rev-1", finding_id="f-1", finding_revision_id="fr-1",
                     window_start=None, window_end=None, quantity={"low": None, "high": None, "unit": None},
                     amount=None, period_kind=fin.OBSERVED, assumptions=[], fingerprint=None, cited=[], technical=[],
                     overlap_group=None, limit=None, provenance={}, links={}, decision=decision)


def test_unpriced_money_line_links_its_price_and_others_do_not() -> None:
    line = _line(fin.OPERATING, (fin.UNPRICED, ["UNPRICED"]))
    _shape_ok(line["price_action"], "KOBO-001")
    assert line["price_action"]["key"] == "diesel_price_per_litre"
    assert line["price_action"]["label"] == "Set a diesel price for Kobo →"
    assert _line(fin.OPERATING, (fin.ELIGIBLE, []))["price_action"] is None
    assert _line(fin.OPERATING, (fin.WITHHELD, ["WITHHELD"]))["price_action"] is None


def test_every_money_category_spec_is_a_real_category() -> None:
    assert set(pa.MONEY_CATEGORY_SPEC) <= set(fin.BENEFICIARY_OF_CATEGORY)
    assert _line(fin.PRODUCT, (fin.UNPRICED, ["UNPRICED"]))["price_action"]["need_key"] == "stock_record"
    assert _line(fin.TARIFF, (fin.UNPRICED, ["UNPRICED"]))["price_action"]["key"] == "ev_gross_tariff_per_kwh"


def test_portfolio_unpriced_card_carries_the_line_action() -> None:
    line = _line(fin.OPERATING, (fin.UNPRICED, ["UNPRICED"]))
    card = portfolio.operating_cost_card([line], {fin.OPERATING: True}, [])
    assert card["state"] == "UNPRICED" and card["price_action"] == line["price_action"]
    assert portfolio.operating_cost_card([], {fin.OPERATING: True}, [])["price_action"] is None


# --- a mini Finding's fuel cost -----------------------------------------------------------------------------------

def test_finding_fuel_cost_unpriced_links_the_diesel_price() -> None:
    got = with_price_action({"state": "UNPRICED", "amount": None}, "KOBO-001")
    _shape_ok(got["price_action"], "KOBO-001")
    assert got["price_action"]["label"] == "Set a diesel price for this site →"
    assert with_price_action({"state": "CURRENT", "amount": None}, "KOBO-001")["price_action"] is None


# --- a mill verification value ------------------------------------------------------------------------------------

def _details() -> dict:
    return {"baseline": {"days": ["2026-10-01", "2026-10-02", "2026-10-03"], "mean_kwh_per_day": "42.00"},
            "later": {"days": ["2026-10-11", "2026-10-12", "2026-10-13"], "mean_kwh_per_day": "110.00"}}


def test_mill_value_unpriced_links_the_productive_price() -> None:
    from assetops_backend.financials.fuel_cost import PriceSelection

    v = vf.mill_value(_details(), vf.VERIFIED, PriceSelection("UNPRICED", "NO_PRICE"), "KOBO-001")
    assert v["state"] == "UNPRICED"
    _shape_ok(v["price_action"], "KOBO-001")
    assert v["price_action"]["key"] == "productive_use_price_per_kwh"
    assert vf.mill_value(_details(), vf.VERIFIED, None)["price_action"] is None  # no Site code: no link
    priced = vf.mill_value(_details(), vf.VERIFIED, PriceSelection("PRICED", None, "rev-1", Decimal("0.25"), "USD"),
                           "KOBO-001")
    assert "price_action" not in priced


def test_shape_check_is_not_vacuous() -> None:
    good = pa.wire(pa.WARNING_SPEC["REPEATED_MAINTENANCE_NO_RESULT"], "S1", "Y", R)
    with pytest.raises(AssertionError):
        _shape_ok({**good, "href": "/sites/S1/financials"}, "S1")
    with pytest.raises(AssertionError):
        _shape_ok({**good, "label": "Set a cost per visit at 5 USD →"}, "S1")
