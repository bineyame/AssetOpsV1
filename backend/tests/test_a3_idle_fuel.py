"""FUEL-1 A3 (`.agent/build-sheet-FUEL-1.md` A3-R §5.1-§5.2): idle fuel on Kobo's screens, L0 (fakes, no DB).

Every expected line is built from the module constants, never retyped from a run."""
from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest

from assetops_backend.actions.verification import VerificationService
from assetops_backend.chain import vocabulary as voc
from assetops_backend.chain.outcomes import fuel_basis, idle_fuel
from assetops_backend.chain.read import MoneyHead
from assetops_backend.chain.vocabulary import (
    FUEL_VALUE_PAGE, NO_LOAD_BASIS_WORDS, WHY_TEXT, money_text, price_text, trial_litres)
from assetops_backend.chain.why import price_lines
from assetops_backend.finding_api import bridge_consequence
from assetops_backend.site_outcomes import board, mini
from assetops_backend.site_overview.read import money_label
from test_out_b2_mini import ASSURE, COST, Fake, contributor, run

T, S, A, O = (UUID(int=i) for i in (1, 2, 3, 4))
EXAMPLE = {"state": "REGISTERED_SIMULATION"}


def cons(model_id: str = "fuel-cost-2", idle: int | None = 12000, rate: str = "3.3", basis: str | None = "GENERIC_DEFAULT",
         mult: str | None = "1.10", high_exact: str | None = "121/10", high: str = "12.1", price: str = "1.25") -> dict:
    """A consequence read body (`financials/consequence_read.dto`'s `model`, `quantity` and `price` blocks)."""
    model = {"model_id": model_id, "sfc_upper_multiplier": mult}
    if model_id == "fuel-cost-2":
        model.update({"no_load_fuel_rate_l_per_h": rate, "no_load_fuel_rate_basis": basis, "idle_seconds": idle})
    return {"consequence": {"model": model, "quantity": {"low": "0", "high": high, "high_exact": high_exact},
                            "price": {"value": price, "currency": "USD"}}}


def head(body: dict, source: dict | None = EXAMPLE, low: str = "0.00", high: str = "15.13") -> MoneyHead:
    return MoneyHead(True, low, high, "USD", source, body)


# ---- 1. idle_fuel -----------------------------------------------------------------------------------------------

def test_idle_fuel_selects_only_fuel_cost_2_with_idle_time_and_is_exact() -> None:
    assert idle_fuel(head(cons(model_id="fuel-cost-1"))) is None
    assert idle_fuel(head(cons(idle=0))) is None and idle_fuel(head(cons(idle=None))) is None
    assert idle_fuel(head(cons(mult=None))) is None and idle_fuel(head(cons(high_exact=None))) is None
    assert idle_fuel(head(cons())) == {"idle_seconds": 12000, "rate": "3.3", "basis": "GENERIC_DEFAULT",
                                       "litres_high": "12.1", "idle_only": True}
    # mixed: the stored upper is above the idle part (litres burned under power are counted too)
    assert idle_fuel(head(cons(high_exact="131/10", high="13.1")))["idle_only"] is False


# ---- 2. the mini headline ---------------------------------------------------------------------------------------

def _cost(money: MoneyHead) -> dict:
    return run(Fake(money_head=money))[1][COST]


def test_idle_only_priced_day_reads_cost_idle_and_keeps_headline_money() -> None:
    row = _cost(head(cons()))
    want = mini.COST_IDLE.format(h="200 minutes", l="12.1", basis=NO_LOAD_BASIS_WORDS["GENERIC_DEFAULT"], r="3.3")
    assert row["headline"] == want
    assert row["headline_money"] == {"amount_low": "0.00", "amount_high": "15.13", "currency": "USD"}
    print("RENDERED COST_IDLE:", money_text("0.00", "15.13", "USD"), row["headline"])


def test_mixed_and_fuel_cost_1_days_keep_the_existing_headlines() -> None:
    assert _cost(head(cons(high_exact="131/10", high="13.1")))["headline"] == mini.COST_MONEY
    assert _cost(head(cons(model_id="fuel-cost-1")))["headline"] == mini.COST_MONEY
    zero = _cost(head(cons(model_id="fuel-cost-1"), low="0.00", high="0.00"))
    assert zero["headline"] == mini.COST_ZERO and zero["headline_money"] is None


@pytest.mark.parametrize("basis", ["GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_TEST"])
def test_each_basis_word(basis: str) -> None:
    assert NO_LOAD_BASIS_WORDS[basis] in _cost(head(cons(basis=basis)))["headline"]


def test_sixty_idle_seconds_read_one_minute() -> None:
    row = _cost(head(cons(idle=60, high_exact="121/2000", high="0.0605")))
    assert row["headline"] == mini.COST_IDLE.format(h="1 minute", l="0.1", basis=NO_LOAD_BASIS_WORDS["GENERIC_DEFAULT"],
                                                    r="3.3")


# ---- 3. fuel_basis ----------------------------------------------------------------------------------------------

def test_fuel_basis_adds_the_idle_keys_only_for_fuel_cost_2_with_idle_time() -> None:
    plain = {"litres_low": "0", "litres_high": "12.1", "price": {"amount": "1.25", "currency": "USD"}}
    assert fuel_basis(head(cons(model_id="fuel-cost-1"))) == plain
    assert fuel_basis(head(cons(idle=0))) == plain
    assert fuel_basis(head(cons())) == {**plain, "idle_seconds": 12000, "no_load_basis": "GENERIC_DEFAULT",
                                        "source_class": "REGISTERED_SIMULATION"}
    assert fuel_basis(head(cons(), source={"state": "UNKNOWN"}))["source_class"] is None


# ---- 4. price_lines ---------------------------------------------------------------------------------------------

def _earn(**extra) -> dict:
    return {"value": {"kwh": "10", "price": {"amount": "1.25", "currency": "USD"}, "litres_low": "0",
                      "litres_high": "12.1", **extra}}


def test_why_idle_line_only_on_example_data_with_idle_time() -> None:
    energy0, fuel0 = price_lines(_earn())
    energy, fuel = price_lines(_earn(idle_seconds=12000, source_class="REGISTERED_SIMULATION"))
    assert fuel == fuel0 + " · " + WHY_TEXT["why.from.fuel_idle_example"] and energy == energy0
    assert price_lines(_earn(idle_seconds=12000, source_class=None)) == (energy0, fuel0)
    assert price_lines(_earn(idle_seconds=0, source_class="REGISTERED_SIMULATION")) == (energy0, fuel0)
    print("RENDERED WHY:", fuel)


# ---- 5. cost_line and _assure -----------------------------------------------------------------------------------

PT = {"amount": "4.125", "currency": "USD", "basis": "TRIAL_HOUR_MODELLED_FUEL", "window": ["a", "b"],
      "fuel_change_l": "3.3"}
CC = {"state": "MODELLED_IMPROVEMENT", "reason": None, "nominal": "0.275", "upper": "0.3025", "currency": "USD",
      "recorded_at": "2026-10-20T00:00:00Z", "priced_total": PT, "price_per_litre": "1.25"}


def _fact(state: str, cc: dict) -> board.ActionFact:
    return board.ActionFact("a48", "ACT-048", "", "f", "r", True, False, state, None, cost_check=cc)


def test_cost_line_priced_total_branches() -> None:
    want = board.COST_PRICED.format(l="3.3", amount="4.12 USD", p="1.25", cur="USD")
    assert board.cost_line(_fact("VERIFIED", CC)) == want and "4.12 USD" in want
    assert board.cost_line(_fact("PENDING", CC)) == board.COST_NOT_CREDITED
    per_kwh = board.COST_CHANGE.format(amount=board.per_kwh_amount(CC), currency="USD")
    assert board.cost_line(_fact("VERIFIED", {**CC, "priced_total": None})) == per_kwh
    no_price = {k: v for k, v in CC.items() if k != "price_per_litre"}
    assert board.cost_line(_fact("VERIFIED", no_price)) == per_kwh
    print("RENDERED COST_PRICED:", want)


def _assure_text(cc: dict, state: str = "VERIFIED") -> str:
    rows = run(Fake(verification={"state": state, "cost_check": cc}))[1]
    return contributor(rows[ASSURE], "verified_results")["text"]


def test_assure_verified_with_fuel_and_fallbacks() -> None:
    want = mini.VERIFIED_WITH_FUEL.format(code="ACT-048", suffix=" on example data", l="3.3", amount="4.12 USD",
                                          p="1.25", cur="USD")
    assert _assure_text(CC) == want
    per_kwh = mini.VERIFIED_WITH_COST.format(code="ACT-048", suffix=" on example data",
                                             amount=board.per_kwh_amount(CC), currency="USD")
    assert _assure_text({**CC, "priced_total": None}) == per_kwh
    assert _assure_text({k: v for k, v in CC.items() if k != "price_per_litre"}) == per_kwh
    print("RENDERED VERIFIED_WITH_FUEL:", want)


# ---- 6. helpers -------------------------------------------------------------------------------------------------

def test_helpers() -> None:
    assert [trial_litres(x) for x in ("3.3", "0.25", "33/10")] == ["3.3", "0.2", "3.3"]
    assert money_text("4.125", None, "USD") == "4.12 USD" and money_text("0.135", None, "USD") == "0.14 USD"
    assert mini.price_text is voc.price_text and price_text("1.25") == "1.25" and price_text(None) is None


# ---- 8. A1 review L2: the bridge and overview label name the stored model ---------------------------------------

def test_bridge_and_overview_label_name_fuel_cost_2() -> None:
    row = {"id": "c1", "state": "PRICED", "model": {"model_id": "fuel-cost-2"},
           "display": {"state": "ROUNDED_OUTWARD", "amount_low": "0.00", "amount_high": "15.13"},
           "quantity": {"low": "0", "high": "12.1", "unit": "L", "reason": None},
           "price": {"reason": None, "revision_id": "p1"}, "amount": {"currency": "USD"}}
    result = {"consequence": row, "money_eligibility": {"state": "ELIGIBLE"},
              "currentness": {"state": "CURRENT", "reasons": [], "pending_work": False,
                              "source_gate": {"permits_current_money": True}}}
    got = bridge_consequence(result)
    assert got["quantity_source"] == "fuel-cost-2" and "fuel-cost-2" in got["reason"]
    assert money_label("fuel-cost-2").startswith("fuel-cost-2 ")


# ---- 5.2 verification: price_per_litre and fuel_value -----------------------------------------------------------

def _trial_row(state: str = "MODELLED_IMPROVEMENT", priced: bool = True, basis: str | None = "GENERIC_DEFAULT") -> dict:
    result = {"state": state, "change_per_demand_kwh": {"nominal": "0.275", "upper": "0.3025"},
              "price": {"revision_id": "p1", "value": "1.25", "currency": "USD"},
              "no_load": {"value_l_per_h": "3.3", "basis": basis}}
    if priced:
        result["priced_total"] = dict(PT)
    return {"state": state, "reason": None, "recorded_at": None, "result": result}


def _service(row: dict | None, outcomes: list[dict] | None = None) -> VerificationService:
    store = SimpleNamespace(latest=lambda t, s, o: row)
    action_store = SimpleNamespace(outcomes=lambda t, s, a: outcomes or [], action=lambda t, s, a: {"id": a},
                                   plans=lambda t, s, a: [])
    actions = SimpleNamespace(store=action_store, clock=None,
                              verification_ports=SimpleNamespace(trial_comparison=SimpleNamespace(store=store)))
    return VerificationService(actions)


def test_cost_check_read_price_per_litre_iff_priced_total() -> None:
    got = _service(_trial_row())._cost_check_read(T, S, A, str(O))["cost_check"]
    assert got["price_per_litre"] == "1.25" and got["priced_total"] == PT
    plain = _service(_trial_row(priced=False))._cost_check_read(T, S, A, str(O))["cost_check"]
    assert "price_per_litre" not in plain and plain["priced_total"] is None
    assert set(plain) == {"state", "reason", "nominal", "upper", "currency", "recorded_at", "priced_total"}


def _outcome_body(outcome: str, row: dict | None) -> dict:
    chosen = {"id": O, "action_id": A, "plan_id": UUID(int=9), "supersedes_outcome_id": None, "outcome": outcome,
              "recorded_at": None, "metrics": []}
    svc = _service(row, [chosen])
    svc.current_state = lambda *a, **k: {"state": outcome}  # type: ignore[method-assign]
    return svc.outcome(T, S, "KOBO-001", A)


def test_outcome_fuel_value_only_for_verified_with_priced_total() -> None:
    want = FUEL_VALUE_PAGE.format(l="3.3", amount="4.12 USD", p="1.25", cur="USD",
                                  basis=NO_LOAD_BASIS_WORDS["GENERIC_DEFAULT"])
    assert _outcome_body("VERIFIED", _trial_row())["fuel_value"] == want
    assert _outcome_body("VERIFIED", _trial_row(basis=None))["fuel_value"].endswith(
        "modelled from a declared idle fuel rate, not measured by a fuel meter")
    assert "fuel_value" not in _outcome_body("VERIFIED", _trial_row(priced=False))
    # must-fail (A3-R §5.2): an INEFFECTIVE outcome with a stored priced total has no fuel line
    assert "fuel_value" not in _outcome_body("INEFFECTIVE", _trial_row())
    print("RENDERED FUEL_VALUE_PAGE:", want)


def test_each_new_literal_formats_with_every_basis_word() -> None:
    lines = [FUEL_VALUE_PAGE.format(l="3.3", amount="4.12 USD", p="1.25", cur="USD", basis=w)
             for w in NO_LOAD_BASIS_WORDS.values()]
    assert len(set(lines)) == 4 and not any(" load" in x or "-load" in x for x in lines)
