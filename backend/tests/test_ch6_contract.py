"""CH-6a3 L1 (CH6a3-R Q1, Q3, Q6): the node keys on the named goldens, and the price bases. Pure."""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from assetops_backend.chain.outcomes import earnings_money, energy_basis, fuel_basis

G = Path(__file__).parent / "fixtures"
NAMED = ("ch5a1_board_contract/kobo_2026-10-31", "ch5a1_board_contract/cold_2026-10-31",
         "ch5a1_board_contract/ev_2026-10-27", "ch5a1_board_contract/kobo_2026-11-01")


@pytest.mark.parametrize("name", NAMED)
def test_every_row_carries_the_node_keys(name):
    body = json.loads((G / f"{name}.json").read_text(encoding="utf-8"))
    assert body["rows"]
    for row in body["rows"]:
        assert {"nodes", "days_line", "target_note"} <= set(row)
        assert set(row["nodes"]) == {"kpi", "earnings", "potential"}


def test_kobo_grow_has_a_potential_and_a_kpi_claim():
    body = json.loads((G / NAMED[0]).with_suffix(".json").read_text(encoding="utf-8"))
    grow = next(r for r in body["rows"] if r["category"] == "GROW_REVENUE")
    assert grow["nodes"]["potential"]["key"].startswith("potential.")
    assert grow["nodes"]["kpi"]["key"].startswith("verdict.")


def _row(kwh, rev, grade="COMPLETE", day=1, rate="0.5"):
    return SimpleNamespace(local_day=date(2026, 10, day), grade=grade, measure="m", subject_ref="SITE",
                           value={"kwh": kwh}, money={"amount": str(Decimal(kwh) * Decimal(rate)),
                                                      "assumption_revision_id": rev},
                           evidence_class="MEASURED")


def test_energy_basis_one_price_names_it():
    rows = (_row("2", "r1"), _row("3", "r1", day=2))
    out = energy_basis(rows, {"amount": "0.5", "currency": "USD", "revision_id": "R1"})
    assert out == {"kwh": "5", "price": {"amount": "0.5", "currency": "USD"}}
    # CH6a3-R2 M5: the line reproduces the summed stored money
    assert Decimal(out["kwh"]) * Decimal(out["price"]["amount"]) == sum(Decimal(r.money["amount"]) for r in rows)


def test_energy_basis_names_no_price_of_another_or_no_revision():
    """CH6a3-R2 M5: a price whose revision is not the rows' one revision, or rows with no revision: no line."""
    assert energy_basis((_row("2", "r1"),), {"amount": "0.6", "currency": "USD", "revision_id": "r9"}) == {"kwh": "2"}
    assert energy_basis((_row("2", None),), {"amount": "0.5", "currency": "USD", "revision_id": "r1"}) == {"kwh": "2"}


def test_fuel_basis_rounds_litres_as_the_dispatch_read():
    head = SimpleNamespace(body={"consequence": {"quantity": {"low": "10.04", "high": "12.25"},
                                                 "price": {"value": "1.5", "currency": "USD"}}})
    assert (fuel_basis(head)["litres_low"], fuel_basis(head)["litres_high"]) == ("10", "12.3")


def test_energy_basis_several_prices_counts_them():
    out = energy_basis((_row("2", "r1"), _row("3", "r2", day=2)), {"amount": "0.5", "currency": "USD"})
    assert out == {"kwh": "5", "price_count": 2}


def test_fuel_basis_requires_a_price():
    head = SimpleNamespace(body={"consequence": {"quantity": {"low": "10", "high": "12"},
                                                 "price": {"value": "1.5", "currency": "USD"}}})
    assert fuel_basis(head)["price"] == {"amount": "1.5", "currency": "USD"}
    assert fuel_basis(SimpleNamespace(body={"consequence": {"quantity": {"low": "1", "high": "2"}}})) is None


def test_earnings_money_none_when_not_known():
    assert earnings_money(None) is None and earnings_money({"value": None}) is None
    assert earnings_money({"value": {"amount": "3", "currency": "USD"}}) == {
        "amount_low": "3", "amount_high": "3", "currency": "USD"}


def test_why_price_lines_and_union():
    from assetops_backend.chain.why import outcome_measures, price_lines
    e, f = price_lines({"value": {"kwh": "5.0", "price": {"amount": "0.50", "currency": "USD"}}})
    assert e == "5 kWh × 0.5 USD/kWh" and f is None
    e, _ = price_lines({"value": {"kwh": "5", "price_count": 2}})
    assert e == "5 kWh at 2 declared prices over these days"
    _, f = price_lines({"value": {"litres_low": "10", "litres_high": "12", "price": {"amount": "1.5", "currency": "USD"}}})
    assert f == "10–12 L × 1.5 USD/L"
    assert price_lines({"value": None}) == (None, None)
    found, earn = outcome_measures("mini_grid", "GROW_REVENUE")
    assert "productive_kwh" in found and earn == "productive_kwh"
