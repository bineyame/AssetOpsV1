"""DD2.5 (spec `specs/DD-demo-data/spec.md` §8.1; D-DD.55): C-DD2 to C-DD4 on rows, no database.

The checker's own evaluator is tested against hand figures (Kobo's July: 8163 kWh, 3265.20, 3002.73). The judges run on
rows built from the simulator's emulated mini-grid books (the test may import the simulator; the checker may not), and
on hand-written cold rows. Each plant must flip its check.
"""
from __future__ import annotations

import copy
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "simulator"))
import dd_check  # noqa: E402

LAKESIDE = {"lakeside-power"}


@pytest.fixture(scope="module")
def inputs() -> dd_check.Inputs:
    return dd_check.read_inputs("postgresql+psycopg://u:p@dd.invalid:1/x_test")


@pytest.fixture(scope="module")
def mini_rows(inputs) -> list[dict]:
    """The emulator's Lakeside books, as the stored-record dicts the SQL read returns (latest revisions)."""
    from assetops_simulator.world.exports import build_exports
    from assetops_simulator.world.history import generate_history
    from assetops_simulator.world.view import ManifestView

    view = ManifestView.from_document(inputs.manifest)
    result = build_exports(view, generate_history(view))
    rows = []
    for f in result.files:
        for r in f.records:
            rows.append({"tenant": f.tenant, "site": r["site_code"], "kind": r["kind"],
                         "month": r["clocks"]["recognition_period"] if "recognition_period" in r["clocks"] else "",
                         "provenance": "source-emulated",
                         "amount": Decimal(r["amount"]["value"]) if "amount" in r else None,
                         "quantity": Decimal(r["quantity"]["value"]) if "quantity" in r else None,
                         "status": r.get("status"), "body": r.get("body", {})})
    return rows


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
    assert f.node("billed_kwh") == Decimal(8163)      # 8592 - 387 - 0 - 42 - 0
    assert f.node("revenue") == Decimal("3265.2")      # 8163 x 0.40
    assert f.node("collected") == Decimal("3002.73")   # 3265.20 - 0 - 262.47
    assert f.node("diesel_l") == Decimal(983)          # 711 + 260 + 12
    assert f.node("fuel_cost") == Decimal("1228.75")   # 983 x 1.25


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


# --- C-DD2 to C-DD4 ------------------------------------------------------------------------------------------------------

def test_the_mini_grid_books_pass_all_three(inputs, mini_rows) -> None:
    for judge in (dd_check.judge_kinds, dd_check.judge_identities, dd_check.judge_leaves_and_nodes):
        result = judge(inputs, mini_rows, LAKESIDE)
        assert result.passed, result.detail


def test_c_dd2_fails_on_a_missing_kind_and_a_wrong_source_word(inputs, mini_rows) -> None:
    short = [r for r in mini_rows if not (r["site"] == "KOBO-001" and r["month"] == "2026-08" and r["kind"] == "RECEIPT")]
    result = dd_check.judge_kinds(inputs, short, LAKESIDE)
    assert not result.passed and "lakeside-power/KOBO-001 2026-08: no RECEIPT record" in result.detail
    wrong = copy.deepcopy(mini_rows)
    wrong[0]["provenance"] = "field-integrated"
    assert not dd_check.judge_kinds(inputs, wrong, LAKESIDE).passed


def test_c_dd2_fails_without_the_other_tenants_books(inputs, mini_rows) -> None:
    result = dd_check.judge_kinds(inputs, mini_rows)  # all three tenants: cold and EV are DD2b's rows
    assert not result.passed and any(line.startswith("harvest-cold/") for line in result.detail)


def test_c_dd3_fails_when_billed_does_not_make_revenue(inputs, mini_rows) -> None:
    bent = copy.deepcopy(mini_rows)
    next(r for r in bent if r["site"] == "MTO-001" and r["month"] == "2026-09" and r["kind"] == "CHARGE")["amount"] += 1
    result = dd_check.judge_identities(inputs, bent, LAKESIDE)
    assert not result.passed and any("MTO-001 2026-09: revenue" in line for line in result.detail)


def test_c_dd3_fails_when_collections_do_not_close(inputs, mini_rows) -> None:
    bent = [r for r in mini_rows if not (r["site"] == "KOBO-001" and r["month"] == "2026-07" and r["kind"] == "RECEIPT"
                                         and r["body"].get("payer_ref", "").endswith("0001"))]
    result = dd_check.judge_identities(inputs, bent, LAKESIDE)
    assert not result.passed and any("KOBO-001 2026-07: collected" in line for line in result.detail)


def test_c_dd4_fails_when_a_history_node_is_not_the_manifests_evaluation(inputs, mini_rows) -> None:
    """The plant that matters: billed kWh is derived, so only an independent evaluation can see it move."""
    bent = copy.deepcopy(mini_rows)
    charges = [r for r in bent if r["site"] == "KOBO-001" and r["month"] == "2026-07" and r["kind"] == "CHARGE"]
    charges[0]["quantity"] += 1
    charges[0]["amount"] += Decimal("0.40")  # keeps C-DD3's identity: revenue = billed x tariff
    next(r for r in bent if r["site"] == "KOBO-001" and r["month"] == "2026-07" and r["kind"] == "RECEIPT")[
        "amount"] += Decimal("0.40")  # ... and collected + outstanding = revenue
    assert dd_check.judge_identities(inputs, bent, LAKESIDE).passed
    result = dd_check.judge_leaves_and_nodes(inputs, bent, LAKESIDE)
    assert not result.passed
    assert any("KOBO-001 2026-07: billed_kwh stored 8164 != evaluated 8163" in line for line in result.detail)


def test_c_dd4_fails_on_a_leaf_and_on_octobers_recorded_node(inputs, mini_rows) -> None:
    bent = copy.deepcopy(mini_rows)
    next(r for r in bent if r["site"] == "KOBO-001" and r["month"] == "2026-08" and r["kind"] == "EXPENSE"
         and r["body"].get("category") == "STAFF")["amount"] += Decimal("0.01")
    assert any("KOBO-001 2026-08: STAFF" in line
               for line in dd_check.judge_leaves_and_nodes(inputs, bent, LAKESIDE).detail)
    october = copy.deepcopy(mini_rows)
    next(r for r in october if r["site"] == "KOBO-001" and r["month"] == "2026-10" and r["kind"] == "EXPENSE"
         and r["body"].get("category") == "FUEL")["amount"] += Decimal("0.01")
    assert any("KOBO-001 2026-10: fuel_cost" in line
               for line in dd_check.judge_leaves_and_nodes(inputs, october, LAKESIDE).detail)


def test_the_three_checks_are_live_and_fail_on_an_empty_store(inputs) -> None:
    assert {"C-DD2", "C-DD3", "C-DD4"} <= set(dd_check.LIVE)
    assert not dd_check.judge_kinds(inputs, []).passed


def test_the_checker_still_imports_nothing_from_the_simulator() -> None:
    import ast
    tree = ast.parse((ROOT / "tools" / "dd_check.py").read_text(encoding="utf-8"))
    names = {n.module if isinstance(n, ast.ImportFrom) else a.name
             for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
             for a in (n.names if isinstance(n, ast.Import) else [n])}
    assert not [x for x in names if x and ("simulator" in x or "world" in x)]
