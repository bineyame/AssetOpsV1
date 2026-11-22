"""DD2.5 (spec `specs/DD-demo-data/spec.md` §8.1; D-DD.55): C-DD2 to C-DD4 on rows, no database.

The checker's own evaluator is tested against hand figures (Kobo's July: 8163 kWh, 3265.20, 3002.73). The judges' tests on the
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
