"""DD2.5 (spec `specs/DD-demo-data/spec.md` §8.1; D-DD.55): C-DD2 to C-DD4 on rows, no database.

The checker's own evaluator is tested against hand figures (Kobo's July: 8190 kWh, 3276.00, 3012.62). The judges' tests on the
emulator's rows are `simulator/tests/world/test_dd2_checker_on_emulated_rows.py` (a product test may not import the
simulator).
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import dd_check  # noqa: E402

LAKESIDE = {"lakeside-power"}


@pytest.fixture(scope="module")
def inputs() -> dd_check.Inputs:
    return dd_check.read_inputs("postgresql+psycopg://u:p@dd.invalid:1/x_test")


# --- the evaluator, against hand figures ---------------------------------------------------------------------------------

def formulas_for(inputs, tenant: str, site: str, month: str) -> dd_check.Formulas:
    money = set(inputs.history["meta"]["money_leaves"])
    record = dd_check.history_record(inputs.history["tenants"][tenant][site][month]["actual"], money)
    t = next(x for x in inputs.manifest["tenants"] if x["tenant"] == tenant)
    key = {"MINI_GRID": "MINI_GRID", "COLD_CHAIN": "COLD_CHAIN"}[t["vertical"]]
    return dd_check.Formulas(inputs.manifest["structures"][key], inputs.manifest["factor_map"][key], record,
                             t["prices"], site)


def test_the_evaluator_gives_kobos_july_by_hand(inputs) -> None:
    f = formulas_for(inputs, "lakeside-power", "Kobo", "2026-07")
    assert f.node("billed_kwh") == Decimal(8190)      # 8621 - 388 - 0 - 43 - 0
    assert f.node("revenue") == Decimal("3276")      # 8190 x 0.40
    assert f.node("collected") == Decimal("3012.62")   # 3276.00 - 0 - 263.38
    assert f.node("diesel_l") == Decimal(508)          # 476 + 20 + 12
    assert f.node("fuel_cost") == Decimal("635")      # 508 x 1.25


def test_the_evaluator_gives_cold_revenue_and_received_by_hand(inputs) -> None:
    record = inputs.history["tenants"]["harvest-cold"]["Room A · Mwea"]["2026-07"]["actual"]
    f = formulas_for(inputs, "harvest-cold", "Room A · Mwea", "2026-07")
    assert f.node("revenue") == Decimal(record["crate_days"]) * Decimal("0.2")
    assert f.node("received") == f.node("revenue") - Decimal(record["outstanding"]) / 100


def test_the_evaluator_reads_alternatives_and_refuses_what_it_cannot_read(inputs) -> None:
    structure = {"a": "x - y", "b": "record.q | record.r | 0", "c": "(1 + 2) * 3"}
    f = dd_check.Formulas(structure, {"x": "record.p | 5", "y": "record.z | 0"}, {"p": 10, "r": 4}, {}, "S")
    assert (f.node("a"), f.node("b"), f.node("c")) == (Decimal(10), Decimal(4), Decimal(9))
    with pytest.raises(dd_check.FormulaError):
        dd_check.Formulas({"a": "min(1, 2)"}, {}, {}, {}, "S").node("a")


def test_the_three_checks_are_live_and_fail_on_an_empty_store(inputs) -> None:
    assert {"C-DD2", "C-DD3", "C-DD4"} <= set(dd_check.LIVE)
    assert not dd_check.judge_kinds(inputs, []).passed


def test_the_checker_still_imports_nothing_from_the_simulator() -> None:
    import ast
    tree = ast.parse((ROOT / "tools" / "dd_check.py").read_text(encoding="utf-8"))
    inside = {id(n) for f in ast.walk(tree) if isinstance(f, ast.FunctionDef) and f.name == "check_property_table_parity"
              for n in ast.walk(f)}  # C-DD21's one function imports the writer's table (DD3.1)
    names = {n.module if isinstance(n, ast.ImportFrom) else a.name
             for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) and id(n) not in inside
             for a in (n.names if isinstance(n, ast.Import) else [n])}
    assert not [x for x in names if x and ("simulator" in x or "world" in x)]


# --- D-DD.58: C-DD3 and C-DD4 never crash; the EV clause judges quantity x band price ------------------------------------

def _ev_site(inputs):
    t = next(x for x in inputs.manifest["tenants"] if x["vertical"] == "EV_DEPOT")
    site = next(s for s in t["sites"] if s["site"] == "Embakasi")
    return t["tenant"], site["code"], site["tariff"]["prices"]


def _ev_line(tenant, code, band, line_type, quantity, amount, month="2026-10"):
    return {"tenant": tenant, "site": code, "kind": "CHARGE", "month": month, "provenance": "source-emulated",
            "amount": Decimal(amount), "quantity": Decimal(quantity), "status": None,
            "body": {"line_type": line_type, "band": band}}


def test_c_dd3_and_c_dd4_on_the_real_inputs_with_no_tenant_filter_raise_nothing(inputs) -> None:
    for judge in (dd_check.judge_identities, dd_check.judge_leaves_and_nodes):
        result = judge(inputs, [], None)
        assert result.check in ("C-DD3", "C-DD4")


def test_a_dropped_cold_crate_days_is_a_fail_line_not_an_exception(inputs) -> None:
    import copy
    planted = dd_check.Inputs(manifest=inputs.manifest, history=copy.deepcopy(inputs.history), database_url=inputs.database_url)
    cold = next(t for t in planted.manifest["tenants"] if t["vertical"] == "COLD_CHAIN")
    site = cold["sites"][0]
    del planted.history["tenants"][cold["tenant"]][site["site"]]["2026-07"]["actual"]["crate_days"]
    result = dd_check.judge_identities(planted, [], {cold["tenant"]})
    assert not result.passed
    assert f"{cold['tenant']}/{site['code']} 2026-07: crate_days not recorded" in result.detail


def test_the_ev_clause_is_pending_while_no_ev_charge_row_is_stored(inputs) -> None:
    result = dd_check.judge_identities(inputs, [], {"metro-bus"})
    assert result.pending == ["EV utility invoices are DD4.4's"]
    assert not any("energy" in line for line in result.detail)


def test_the_ev_clause_judges_each_line_as_quantity_times_band_price_half_even(inputs) -> None:
    tenant, code, prices = _ev_site(inputs)
    good = [_ev_line(tenant, code, "PEAK", "USAGE", "47740", "11457.60"),
            _ev_line(tenant, code, "OFFPEAK", "USAGE", "39060", "4687.20"),
            _ev_line(tenant, code, "DEMAND", "DEMAND", "500", "6000.00")]
    result = dd_check.judge_identities(inputs, good, {tenant})
    assert not result.pending and not [l for l in result.detail if "2026-10" in l and code in l and "!=" in l]
    bad = [dict(good[0], amount=Decimal("11457.61"))] + good[1:]
    result = dd_check.judge_identities(inputs, bad, {tenant})
    assert not result.passed and any(f"{tenant}/{code} 2026-10 PEAK" in l for l in result.detail)
    half = _ev_line(tenant, code, "PEAK", "USAGE", "0.0625", "0.02")  # 0.0625 x 0.24 = 0.015 -> half-even 0.02
    assert not [l for l in dd_check.judge_identities(inputs, [half], {tenant}).detail if "PEAK" in l]
    half = _ev_line(tenant, code, "PEAK", "USAGE", "0.0625", "0.01")
    assert [l for l in dd_check.judge_identities(inputs, [half], {tenant}).detail if "PEAK" in l]


def test_an_ev_line_without_a_price_in_m_is_a_fail_line(inputs) -> None:
    tenant, code, _ = _ev_site(inputs)
    result = dd_check.judge_identities(inputs, [_ev_line(tenant, code, "FLAT", "USAGE", "10", "1.50")], {tenant})
    assert not result.passed and any("usd_per_kwh not recorded" in l for l in result.detail)


def test_book_months_is_gone() -> None:
    assert not hasattr(dd_check, "BOOK_MONTHS")
