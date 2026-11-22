"""6c (`specs/6c-option-evaluator/spec.md` §2, §6 tests 1 and 9 in part; D-P6.3, D-P6.4): the difference through the
structure. Every figure below is a hand-computed literal from the fixtures (§5)."""
from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from assetops_backend.structure import difference as diff_module
from assetops_backend.structure.difference import OUTCOME_FACTOR, LeafChange, difference
from assetops_backend.structure.evaluate import LeafValue, evaluate
from assetops_backend.structure.registry import REGISTRIES, parsed_text
from option_fixtures import (C1_CHANGES, CC, E1_CHANGES, EV, MG, c1_base, change, e1_base, f1_base, f1_changes,
                             leaves_for, recorded, stated)

D = Decimal
PKG = Path(__file__).resolve().parents[1] / "assetops_backend"


def _changes_of(result) -> dict:
    return {fid: d.change for fid, d in result.items()}


# --- parity ------------------------------------------------------------------------------------------------------

def _all_valued(registry):
    """Every leaf with a value, distinct and non-zero so a slip in an operator shows."""
    given = {}
    for i, row in enumerate(r for r in registry.rows if r.is_leaf):
        money = "USD" if row.unit.has_money_dimension else None
        given[row.factor_id] = stated(D(i + 2) + D("0.25"), currency=money)
    return leaves_for(registry, given)


@pytest.mark.parametrize("key", list(REGISTRIES))
def test_1_parity_fold_equals_evaluate_on_every_node(key) -> None:
    registry = REGISTRIES[key]
    leaves = _all_valued(registry)
    v0 = evaluate(registry, leaves)
    values = {fid: fv.value for fid, fv in v0.items()}
    nodes = [row for row in registry.rows if not row.is_leaf]
    assert nodes
    for row in nodes:
        assert diff_module._fold(parsed_text(row.expression), values) == v0[row.factor_id].value, row.factor_id


# --- F1b, C1, E1 effects as literals -----------------------------------------------------------------------------

def test_1_f1b_effects_of_stop_70_reserve_30() -> None:
    got = difference(MG, f1_base(), f1_changes(200, 50))
    assert list(got) == ["candidate_l", "battery_throughput_kwh", "diesel_l", "fuel_cost", "battery_wear",
                         "cost_to_serve", "contribution"]
    assert _changes_of(got) == {"candidate_l": D(-200), "battery_throughput_kwh": D(50), "diesel_l": D(-200),
                                "fuel_cost": D("-250.00"), "battery_wear": D("2.50"), "cost_to_serve": D("-247.50"),
                                "contribution": D("247.50")}
    out = got[OUTCOME_FACTOR]
    assert out.missing_leaves == () and out.currency == "USD" and str(out.unit) == str(MG.row("contribution").unit)
    assert out.used == ("candidate_l", "diesel_price", "battery_throughput_kwh", "wear_rate")
    assert out.evidence == "MODELLED"
    assert out.origins == ("demo-simulated", "unknown")
    assert got["diesel_l"].currency is None and got["battery_throughput_kwh"].currency is None
    assert got["fuel_cost"].currency == "USD"
    assert got["candidate_l"].used == ("candidate_l",) and got["candidate_l"].evidence == "MODELLED"


def test_1_c1_effects_of_repair_chiller() -> None:
    got = difference(CC, c1_base(), C1_CHANGES)
    assert _changes_of(got) == {"model_factor": D("-0.1"), "kwh_model": D(-500), "kwh": D(-500),
                                "energy": D("-100.00"), "cost_to_serve": D("-100.00"), "contribution": D("100.00")}
    out = got[OUTCOME_FACTOR]
    assert out.evidence == "MODELLED" and out.currency == "USD"
    assert out.origins == ("observed-financial", "field-integrated", "unknown")
    assert out.used == ("crate_days", "contract_crate_days", "base_kwh", "k_kwh_per_crate_day", "model_factor",
                        "elec_price")


def test_1_e1_effects_of_night_schedule() -> None:
    got = difference(EV, e1_base(), E1_CHANGES)
    assert _changes_of(got) == {
        "peak_kwh": D(-1000), "kwh_0000_0500": D(1000), "scheduled_kwh_night": D(0), "supplied_kwh_night": D(0),
        "buses_short_per_night": D(0), "departures_missed": D(0), "peak_cost": D("-300.00"),
        "night_cost": D("100.00"), "energy_cost": D("-200.00"), "penalties": D(0), "cost_to_serve": D("-200.00"),
        "contribution": D("200.00")}
    assert "cost_per_departure_met" not in got and "departures_met" not in got
    assert got["penalties"].used == ("peak_kwh", "kwh_0000_0500") and got["penalties"].evidence == "MODELLED"
    assert got[OUTCOME_FACTOR].origins == ("observed-financial", "field-integrated")


# --- a missing operand named; an unchanged factor exactly 0 ------------------------------------------------------

def test_1_f1a_missing_wear_is_named_and_fuel_still_set() -> None:
    got = difference(MG, f1_base(wear=False), f1_changes(200, 50))
    assert got["fuel_cost"].change == D("-250.00")
    for fid in ("battery_wear", "cost_to_serve", "contribution"):
        assert got[fid].change is None and got[fid].missing_leaves == ("wear_rate",), fid
    assert got[OUTCOME_FACTOR].evidence == "MODELLED"  # a missing value is not a used value
    assert "wear_rate" not in got[OUTCOME_FACTOR].used


def test_1_zero_throughput_needs_no_wear_value() -> None:
    got = difference(MG, f1_base(wear=False), f1_changes(5, 0))
    assert got["battery_wear"].change == 0 and got["battery_wear"].missing_leaves == ()
    assert got[OUTCOME_FACTOR].change == D("6.25")


def test_1_a_change_with_no_delta_names_itself_and_val1_still_reads_the_price() -> None:
    none = LeafChange(None, "MODELLED", ("replay-study",), ("demo-simulated",), ("SITE_MONTH_SIMULATION", "SIMULATION"))
    got = difference(MG, f1_base(), {"candidate_l": none, "battery_throughput_kwh": none})
    out = got[OUTCOME_FACTOR]
    assert out.change is None and out.missing_leaves == ("candidate_l", "battery_throughput_kwh")
    assert "diesel_price" in out.used and "wear_rate" in out.used and out.evidence == "MODELLED"


def test_1_the_base_candidate_litres_are_never_needed() -> None:
    base = f1_base()
    assert base["candidate_l"].value is None
    assert difference(MG, base, f1_changes(200, 50))[OUTCOME_FACTOR].change == D("247.50")


def test_1_unchanged_revenue_is_left_out_and_c1b_names_base_kwh() -> None:
    got = difference(CC, c1_base(base_kwh=False), C1_CHANGES)
    assert "revenue" not in got
    assert got[OUTCOME_FACTOR].change is None and got[OUTCOME_FACTOR].missing_leaves == ("base_kwh",)


def test_1_stated_records_are_never_read() -> None:
    # Plant (D-P6.4): passing SiteInputs.stated would make the fuel effect 0; the signature takes no stated map.
    import inspect
    params = inspect.signature(difference).parameters
    assert list(params) == ["registry", "base", "changes", "also"]  # 6h (D-P6.57): `also`, still no stated map
    assert params["also"].kind is inspect.Parameter.KEYWORD_ONLY and params["also"].default == ()


def test_1_a_product_of_two_changing_operands_uses_val1() -> None:
    # d(a x b) = d(a) * val1(b) + val0(a) * d(b): litres -200 at a price 1.25 -> 1.50 on base litres 1000.
    base = leaves_for(MG, {"necessary_l": stated(1000, "RECORDED", origins=("field-integrated",)),
                           "unexplained_l": stated(0, "RECORDED", origins=("field-integrated",)),
                           "diesel_price": stated("1.25", currency="USD"), "wear_rate": stated("0.05", currency="USD"),
                           "candidate_l": stated(0, "RECORDED", origins=("field-integrated",))})
    got = difference(MG, base, {"candidate_l": change(-200), "diesel_price": change("0.25")})
    # -200 * 1.50 + 1000 * 0.25 = -300 + 250 = -50
    assert got["fuel_cost"].change == D("-50.00")


def test_1_currency_plant() -> None:
    base = f1_base()
    base = dict(base, wear_rate=stated("0.05", currency="EUR"))
    got = difference(MG, base, f1_changes(200, 50))
    assert got[OUTCOME_FACTOR].change is None and got[OUTCOME_FACTOR].missing_leaves == ("currency",)


# --- test 9 in part ----------------------------------------------------------------------------------------------

def test_9_difference_imports_only_structure_and_the_standard_library() -> None:
    import sys
    tree = ast.parse((PKG / "structure" / "difference.py").read_text())
    typing_only = {id(n) for top in tree.body if isinstance(top, ast.If) and getattr(top.test, "id", "") ==
                   "TYPE_CHECKING" for n in ast.walk(top)}
    for node in ast.walk(tree):
        if id(node) in typing_only:
            continue
        if isinstance(node, ast.ImportFrom):
            name = node.module or ""
        elif isinstance(node, ast.Import):
            name = node.names[0].name
        else:
            continue
        top = name.split(".")[0]
        assert name.startswith("assetops_backend.structure") or top in sys.stdlib_module_names \
            or top == "__future__", name


# --- M1 and D-P6.40: the rules no fixture reaches, on planted registries with literal numbers ----------------------

def _plant_base(registry, **given):
    return leaves_for(registry, {k: v for k, v in given.items()})


def test_1_a_changed_leaf_through_division_ceil_floor_min_max() -> None:
    """a 250 -> 350, b 100, c 300: a/b 2.5 -> 3.5 (+1); ceil 3 -> 4 (+1); floor 2 -> 3 (+1); min 250 -> 300 (+50);
    max 300 -> 350 (+50)."""
    from option_fixtures import OPS
    base = _plant_base(OPS, a=stated(250), b=stated(100), c=stated(300))
    got = difference(OPS, base, {"a": change(100)})
    assert list(got) == ["a", "ratio", "cap", "fl", "lo", "hi", "contribution"]
    assert _changes_of(got) == {"a": D(100), "ratio": D(1), "cap": D(1), "fl": D(1), "lo": D(50), "hi": D(50),
                                "contribution": D(103)}
    assert all(d.missing_leaves == () for d in got.values())


def test_1_a_changed_leaf_with_a_missing_base_is_missing_never_zero() -> None:
    """a x b with both changed and b's base NOT_AVAILABLE: the change is missing and names b, not 100 x 5 + 250 x 5."""
    from option_fixtures import PRODUCT
    base = _plant_base(PRODUCT, a=stated(250))
    got = difference(PRODUCT, base, {"a": change(100), "b": change(5)})
    assert got["prod"].change is None and got["prod"].missing_leaves == ("b",)
    assert got[OUTCOME_FACTOR].change is None and got[OUTCOME_FACTOR].missing_leaves == ("b",)
    assert got["b"].change == D(5)  # the leaf's own delta is known; its base is what is missing


def test_1_the_option_only_neutral_zero_short_cut_matches_evaluate() -> None:
    """q = a x n x x with n neutral at 0: no-action q is 0 although a has no value, so x's change moves q by 0."""
    from option_fixtures import NEUTRAL
    base = _plant_base(NEUTRAL, x=stated(10))
    assert evaluate(NEUTRAL, base)["q"].value == 0
    got = difference(NEUTRAL, base, {"x": change(5)})
    assert _changes_of(got) == {"x": D(5), "q": D(0), "contribution": D(0)}
    assert all(d.missing_leaves == () for d in got.values())


def test_1_a_zero_denominator_is_tagged_on_the_node_that_met_it() -> None:
    from option_fixtures import DIVISION
    base = _plant_base(DIVISION, a=stated(250), z=stated(5))
    got = difference(DIVISION, base, {"z": change(-5)})  # the option side divides by 0
    assert got["r"].change is None and got["r"].missing_leaves == ("r",) and got["r"].zero_denominators == ("r",)
    assert got[OUTCOME_FACTOR].zero_denominators == ("r",) and got["z"].zero_denominators == ()
    fine = difference(DIVISION, base, {"z": change(5)})
    assert fine["r"].change == D(-25) and fine["r"].zero_denominators == ()  # 250/10 - 250/5
