"""5b (spec `specs/5b-attribution/spec.md` rev 2; rulings D-5B.1 to D-5B.15): attribution, the gap explained by its drivers.

Unit 1 (spec §2, §5.1): the split rules, tests 1 to 4. Units 2 and 3 (spec §3, §4, §5.2): carrying, the Site and
portfolio bridges and the read, tests 5 to 11. No database. Every expected value is spec §5's hand-computed literal
(W2), typed here; none is derived from the code under test. Unit 1's leaves are hand-built and evaluated with 3B3's
`evaluate`; the toy registry is 5a's `_toy`. Units 2 and 3 read §5.2's world through 4b's test reader and 5a's
`TargetRead` (the world helpers of 3A4, 4b and 5a imported, never edited).
"""
from __future__ import annotations

import ast
import dataclasses
import functools
import json
import subprocess
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from pathlib import Path

import pytest

import test_5a_targets as t5a
from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure.attribution import rules
from assetops_backend.structure.attribution.bridge import BridgeRow, bridge, by_home, lowest
from assetops_backend.structure.attribution.carry import CARRIED_TEXT, NO_TARGET_LINE, carry_at_target
from assetops_backend.structure.attribution.portfolio import PortfolioBridge, portfolio_bridge
from assetops_backend.structure.attribution.read import BridgeRead
from assetops_backend.structure.attribution.rules import SOLVE_TOLERANCE, agree
from assetops_backend.structure.attribution.site import SiteBridge, site_bridge
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import LeafValue, Missing, SiteStructure, evaluate, weakest_origin
from assetops_backend.structure.money import CommercialLeafSource
from assetops_backend.structure.read import SiteInputs, StructureRead
from assetops_backend.structure.registry import REGISTRIES, FactorRow, FilledBy, Registry
from assetops_backend.structure.targets.lines import BudgetLineReader
from assetops_backend.structure.targets.read import SiteTargets, TargetCheck, TargetRead
from assetops_backend.structure.targets.rules import solve_main
from assetops_contracts.canonical.units import KWH, MONEY
from test_3a4_commercial_months import READ_AT, new_world
from test_4b_money_leaves import MTO_MISSING, fallback
from test_4b_money_leaves import fixture_steps as money_steps
from test_4b_money_leaves import ingest as money_ingest
from test_5a_targets import _toy

D = Decimal
MG = REGISTRIES["MINI_GRID"]
E = "source-emulated"
USD, KES = "USD", "KES"
#: The named money leaves of spec §5.1 (money and prices carry a currency).
MONEY_LEAVES = ("tariff", "productive_tariff", "in_transit", "outstanding", "diesel_price", "om", "staff")
OPTION_ONLY = ("extra_l", "battery_throughput_kwh", "collection_cost")

# Spec §5.1's table: actual RECORDED, target DECLARED, origins ("source-emulated",).
ACTUAL = {"delivered_kwh": "9100", "technical_loss_kwh": "410", "unexplained_loss_kwh": "0", "adjustments_kwh": "45",
          "unmapped_kwh": "0", "tariff": "0.40", "productive_kwh": "0", "productive_tariff": "0.30",
          "necessary_l": "730", "candidate_l": "330", "unexplained_l": "120", "diesel_price": "1.25",
          "om": "600.00", "staff": "500.00", "in_transit": "0", "outstanding": "278.00"}
TARGET = {"delivered_kwh": "8550", "technical_loss_kwh": "0", "unexplained_loss_kwh": "0", "adjustments_kwh": "0",
          "unmapped_kwh": "0", "tariff": "0.40", "productive_kwh": "0", "productive_tariff": "0.30",
          "necessary_l": "700", "candidate_l": "0", "unexplained_l": "0", "diesel_price": "1.25",
          "om": "600.00", "staff": "500.00", "in_transit": "0", "outstanding": "0"}


# --- the leaves (spec §5.1) ----------------------------------------------------------------------------------------

def _absent(leaf: str, cause: str = "NOT_CONNECTED") -> LeafValue:
    fb = MG.row(leaf).filled_by
    return LeafValue(None, "NOT_AVAILABLE", (), None, Missing(fb.kind, fb.family, cause, None, (), fb.words, None),
                     None)


def leaves(side: str, values: dict[str, str], currency: str = USD) -> dict[str, LeafValue]:
    evidence = "RECORDED" if side == "actual" else "DECLARED"
    out: dict[str, LeafValue] = {}
    for row in MG.rows:
        f = row.factor_id
        if not row.is_leaf:
            continue
        if f in values:
            out[f] = LeafValue(D(values[f]), evidence, (f"test:{side}",), None, None,
                               currency if f in MONEY_LEAVES else None, (E,))
        elif f in OPTION_ONLY:
            out[f] = LeafValue(D("0"), "NEUTRAL", (), None, None, None)
        elif f == "period_days":
            out[f] = LeafValue(D("31"), "DERIVED", ("calendar",), None, None, None)  # CALENDAR: no origins
        else:
            out[f] = _absent(f)
    return out


def side(which: str, values: dict[str, str] | None = None, *, stated: dict[str, LeafValue] | None = None,
         currency: str = USD, **replace: LeafValue):
    base = values if values is not None else (ACTUAL if which == "actual" else TARGET)
    lv = {**leaves(which, base, currency), **replace}
    return evaluate(MG, lv, stated or {})


def stated(value: str, evidence: str = "RECORDED") -> LeafValue:
    return LeafValue(D(value), evidence, ("test:stated",), None, None, USD, (E,))


def kobo(root: str = "contribution", **actual_values: str) -> BridgeRow:
    a = side("actual", {**ACTUAL, **actual_values})
    return bridge(MG, a, side("target"), root)


# --- the comparison helpers ----------------------------------------------------------------------------------------

def find(row: BridgeRow, factor_id: str) -> BridgeRow:
    if row.factor_id == factor_id:
        return row
    for child in row.rows:
        try:
            return find(child, factor_id)
        except LookupError:
            pass
    raise LookupError(factor_id)


def every(row: BridgeRow):
    yield row
    for child in row.rows:
        yield from every(child)


def check_shape(row: BridgeRow, expected: tuple) -> None:
    """`expected` = (factor, kind, rule, scale, gap, effect, split, reason, children); `effect` a money literal compared
    as `Decimal` and as `format(v, "f")`; scale and gap compared as `Decimal`."""
    factor, kind, rule, scale, gap, effect, split, reason, children = expected
    where = f"{row.parent}>{row.factor_id}"
    assert (row.factor_id, row.kind, row.rule, row.split, row.reason) == (factor, kind, rule, split, reason), where
    assert row.scale == D(scale), (where, row.scale)
    assert row.gap == D(gap), (where, row.gap)
    assert row.effect == D(effect) and format(row.effect, "f") == effect, (where, row.effect)
    assert [c.factor_id for c in row.rows] == [c[0] for c in children], where
    for child, exp in zip(row.rows, children):
        assert child.parent == factor, where
        check_shape(child, exp)


def leaf(factor, kind, scale, gap, effect):
    rule = "AR2" if kind in ("VOLUME", "PRICE") else "AR1"
    return (factor, kind, rule, scale, gap, effect, "LEAF", None, ())


REVENUE = ("revenue", "TERM", "AR1", "1", "38.00", "38.00", "SPLIT", None, (
    ("billed_kwh", "VOLUME", "AR2", "0.40", "95", "38.00", "SPLIT", None, (
        ("metered_kwh", "TERM", "AR1", "0.40", "140", "56.00", "SPLIT", None, (
            leaf("delivered_kwh", "TERM", "0.40", "550", "220.00"),
            leaf("technical_loss_kwh", "TERM", "-0.40", "410", "-164.00"),
            leaf("unexplained_loss_kwh", "TERM", "-0.40", "0", "0.00"))),
        leaf("adjustments_kwh", "TERM", "-0.40", "45", "-18.00"),
        leaf("unmapped_kwh", "TERM", "-0.40", "0", "0.00"))),
    leaf("tariff", "PRICE", "8645", "0", "0.00"),
    leaf("productive_kwh", "VOLUME", "0.30", "0", "0.00"),
    leaf("productive_tariff", "PRICE", "0", "0", "0.00")))

CONTRIBUTION = ("contribution", "ROOT", None, "1", "-562.00", "-562.00", "SPLIT", None, (
    REVENUE,
    ("cost_to_serve", "TERM", "AR1", "-1", "600.00", "-600.00", "SPLIT", None, (
        ("fuel_cost", "TERM", "AR1", "-1", "600.00", "-600.00", "SPLIT", None, (
            ("diesel_l", "VOLUME", "AR2", "-1.25", "480", "-600.00", "SPLIT", None, (
                leaf("necessary_l", "TERM", "-1.25", "30", "-37.50"),
                leaf("candidate_l", "TERM", "-1.25", "330", "-412.50"),
                leaf("unexplained_l", "TERM", "-1.25", "120", "-150.00"))),
            leaf("diesel_price", "PRICE", "-1180", "0", "0.00"))),
        leaf("om", "TERM", "-1", "0", "0.00"),
        leaf("staff", "TERM", "-1", "0", "0.00")))))


# --- test 1: §5.1's trees (AT-1, AT-2) -----------------------------------------------------------------------------

def test_1_kobo_contribution_splits_to_the_observed_leaves_exactly() -> None:  # plants V2, V12, V13, V14
    root = kobo()
    check_shape(root, CONTRIBUTION)
    assert (root.actual, root.target) == (D("883.00"), D("1445.00"))
    assert (root.parent, root.rule, root.home, root.currency) == (None, None, "ABOVE", USD)
    assert root.evidence == "DECLARED" and root.origins == (E,)
    assert all(r.kind != "RESIDUAL" for r in every(root))
    assert all(r.currency == USD and r.carried is False for r in every(root))
    assert all(r.unobserved_actual == () and r.unobserved_target == () for r in every(root))
    assert find(root, "delivered_kwh").home == "GROW_REVENUE"
    assert find(root, "technical_loss_kwh").home == "OPTIMIZE_COST"
    assert find(root, "diesel_l").evidence == "DECLARED"
    # no row for an option-only term (D-5B.5)
    assert [c.factor_id for c in find(root, "cost_to_serve").rows] == ["fuel_cost", "om", "staff"]
    for neutral in ("collection_cost", "battery_wear", "extra_l", "battery_throughput_kwh", "wear_rate"):
        with pytest.raises(LookupError):
            find(root, neutral)


def test_1_by_home_reads_each_lowest_rows_own_home() -> None:  # plant V12
    homes = by_home(kobo())
    assert dict(homes) == {"GROW_REVENUE": D("220.00"), "OPTIMIZE_COST": D("-782.00")}
    assert list(homes) == ["GROW_REVENUE", "OPTIMIZE_COST"]
    assert [r.factor_id for r in lowest(kobo())] == [
        "delivered_kwh", "technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh", "tariff",
        "productive_kwh", "productive_tariff", "necessary_l", "candidate_l", "unexplained_l", "diesel_price", "om",
        "staff"]


def test_1_kobo_collected_tree() -> None:
    root = kobo("collected")
    check_shape(root, ("collected", "ROOT", None, "1", "-240.00", "-240.00", "SPLIT", None, (
        REVENUE,
        leaf("in_transit", "TERM", "-1", "0", "0"),
        leaf("outstanding", "TERM", "-1", "278.00", "-278.00"))))
    assert (root.actual, root.target) == (D("3180.00"), D("3420.00"))
    assert dict(by_home(root)) == {"GROW_REVENUE": D("220.00"), "OPTIMIZE_COST": D("-460.00")}


# --- test 2: AT-3, volume at target price first -------------------------------------------------------------------

def test_2_at3_volume_at_target_price_then_price_at_actual_volume() -> None:  # plants V1, V2
    root = kobo(diesel_price="1.30")
    fuel = find(root, "fuel_cost")
    assert fuel.actual == D("1534.00") and format(fuel.effect, "f") == "-659.00"
    volume, price = fuel.rows
    assert (volume.factor_id, volume.kind, volume.scale, volume.effect) == ("diesel_l", "VOLUME", D("-1.25"),
                                                                            D("-600.00"))
    assert (price.factor_id, price.kind, price.scale, price.gap) == ("diesel_price", "PRICE", D("-1180"), D("0.05"))
    assert format(price.effect, "f") == "-59.00" and format(volume.effect, "f") == "-600.00"
    assert {volume.effect, price.effect}.isdisjoint({D("-35.00"), D("-624.00"), D("35.00"), D("624.00")})
    assert price.evidence == "DECLARED" and price.origins == (E,)
    assert format(root.effect, "f") == "-621.00"


# --- test 3: the stops ---------------------------------------------------------------------------------------------

def test_3a_a_residual_sits_beside_the_unobserved_leaf() -> None:
    gone = {"delivered_kwh": _absent("delivered_kwh", "NOT_RECEIVED")}
    a = side("actual", stated={"revenue": stated("3458.00")}, **gone)
    t = side("target", stated={"revenue": stated("3420.00", "DECLARED")}, **gone)
    root = bridge(MG, a, t, "revenue")
    assert (root.split, root.reason, format(root.effect, "f")) == ("SPLIT", None, "38.00")
    assert [(r.factor_id, r.kind) for r in root.rows] == [("productive_kwh", "VOLUME"), ("productive_tariff", "PRICE"),
                                                          (None, "RESIDUAL")]
    assert [r.effect for r in root.rows[:2]] == [D("0"), D("0")]
    res = root.rows[-1]
    assert (res.parent, res.rule, res.home) == ("revenue", "AR1", "GROW_REVENUE")
    assert (res.actual, res.target, res.gap, res.scale) == (None, None, None, None)
    assert format(res.effect, "f") == "38.00" and res.rows == ()
    assert (res.unobserved_actual, res.unobserved_target) == (("delivered_kwh",), ("delivered_kwh",))
    assert res.evidence == "DECLARED" and res.currency == USD
    assert (res.split, res.reason) == ("NOT_SPLIT", "DETAIL_NOT_AVAILABLE")  # D-5B.15 (mid-build Q1)
    assert dict(by_home(root)) == {"GROW_REVENUE": D("38.00")}


def test_3b_no_computable_term_is_not_split_and_names_the_leaves() -> None:  # plant V13
    gone = {f: _absent(f, "NOT_RECEIVED") for f in ("delivered_kwh", "productive_tariff")}
    a = side("actual", stated={"revenue": stated("3458.00")}, **gone)
    t = side("target", stated={"revenue": stated("3420.00", "DECLARED")}, **gone)
    root = bridge(MG, a, t, "revenue")
    assert (root.split, root.reason, root.rows) == ("NOT_SPLIT", "DETAIL_NOT_AVAILABLE", ())
    assert format(root.effect, "f") == "38.00"
    assert root.unobserved_actual == ("delivered_kwh", "productive_tariff")
    assert root.unobserved_target == ("delivered_kwh", "productive_tariff")


def test_3c_a_record_its_factors_do_not_explain_is_not_split() -> None:  # plant V16
    root = bridge(MG, side("actual", stated={"revenue": stated("3500.00")}), side("target"), "revenue")
    assert (root.split, root.reason, root.rows) == ("NOT_SPLIT", "RECORD_AND_FACTORS_DIFFER", ())
    assert format(root.effect, "f") == "80.00"


def _toy_side(reg: Registry, x: str, p: str, currency: str | None = USD) -> dict:
    lv = {"x": LeafValue(D(x), "RECORDED", ("x",), None, None, None, (E,)),
          "p": LeafValue(D(p), "DECLARED", ("p",), None, None, currency, (E,))}
    return evaluate(reg, lv)


def test_3d_the_price_is_chosen_by_its_unit_never_by_position() -> None:  # plant V3
    reg = _toy("p * x")
    root = bridge(reg, _toy_side(reg, "100", "0.50"), _toy_side(reg, "80", "0.40"), "y")
    assert (root.split, format(root.effect, "f")) == ("SPLIT", "18.00")
    volume, price = root.rows
    assert (volume.factor_id, volume.kind, volume.scale, volume.effect) == ("x", "VOLUME", D("0.40"), D("8.00"))
    assert (price.factor_id, price.kind, price.scale, price.effect) == ("p", "PRICE", D("100"), D("10.00"))
    assert (volume.home, price.home) == (None, None)
    assert dict(by_home(root)) == {"UNPLACED": D("18.00")}


def _planted(expression: str) -> Registry:
    rows = (FactorRow("x", None, KWH, None, FilledBy("READING", "x", None), "MISSING", None, composes="SUM"),
            FactorRow("z", None, KWH, None, FilledBy("READING", "z", None), "MISSING", None, composes="SUM"),
            FactorRow("y", expression, MONEY, None, None, None, None, composes="SUM"))
    return Registry("TOY", 1, rows)


def _planted_side(reg: Registry, x: str, z: str) -> dict:
    return evaluate(reg, {"x": LeafValue(D(x), "RECORDED", ("x",), None, None, None, (E,)),
                          "z": LeafValue(D(z), "RECORDED", ("z",), None, None, None, (E,))})


@pytest.mark.parametrize(("expression", "reason"), [("x * z", "PRICE_NOT_DECLARED"), ("x / z", "RULE_NOT_DECLARED")])
def test_3ef_an_undeclared_shape_is_not_split(expression: str, reason: str) -> None:
    reg = _planted(expression)
    root = bridge(reg, _planted_side(reg, "10", "4"), _planted_side(reg, "8", "4"), "y")
    assert (root.split, root.reason, root.rows) == ("NOT_SPLIT", reason, ())
    assert root.effect == root.gap and root.effect is not None


def test_3g_a_missing_actual_has_no_gap_never_zero() -> None:  # plant V10
    a = side("actual", om=_absent("om", "NOT_RECEIVED"))
    root = bridge(MG, a, side("target"), "contribution")
    assert (root.split, root.reason, root.rows) == ("NOT_SPLIT", "GAP_NOT_AVAILABLE", ())
    assert (root.actual, root.gap, root.effect, root.evidence) == (None, None, None, "NOT_AVAILABLE")
    assert root.target == D("1445.00")
    assert (root.unobserved_actual, root.unobserved_target) == (("om",), ())
    assert dict(by_home(root)) == {}


def test_3h_two_currencies_are_never_subtracted() -> None:
    root = bridge(MG, side("actual"), side("target", currency=KES), "contribution")
    assert (root.split, root.reason, root.gap, root.effect) == ("NOT_SPLIT", "CURRENCY_MISMATCH:KES,USD", None, None)
    assert root.evidence == "NOT_AVAILABLE" and root.rows == ()


def _solved_target():
    t_leaves = leaves("target", {**TARGET, "diesel_price": "1.27"})
    solved, note = solve_main(MG, t_leaves, "fuel_cost", "necessary_l", D("875.00"), currency=USD)
    assert note is None and solved is not None
    t_leaves["necessary_l"] = dataclasses.replace(t_leaves["necessary_l"], value=solved)
    return evaluate(MG, t_leaves, {"fuel_cost": LeafValue(D("875.00"), "DECLARED", ("budget:test",), None, None,
                                                          USD, (E,))})


def test_3i_a_solved_target_agrees_with_its_record_within_the_tolerance() -> None:  # plant V18a
    root = bridge(MG, side("actual"), _solved_target(), "fuel_cost")
    assert (root.split, root.reason, root.gap, root.effect) == ("SPLIT", None, D("600.00"), D("600.00"))
    volume, price = root.rows
    assert (price.factor_id, price.kind, price.scale, price.gap, price.effect) == (
        "diesel_price", "PRICE", D("1180"), D("-0.02"), D("-23.60"))
    assert format(price.effect, "f") == "-23.60"
    assert (volume.factor_id, volume.kind, volume.scale) == ("diesel_l", "VOLUME", D("1.27"))
    assert volume.effect.quantize(D("0.01")) == D("623.60")
    total = _sum([volume.effect, price.effect])
    assert total != D("600.00") and agree(total, D("600.00"))  # the case exercises the tolerance


def test_3j_a_cent_is_never_within_the_tolerance() -> None:  # plant V18b
    root = bridge(MG, side("actual", stated={"revenue": stated("3458.01")}), side("target"), "revenue")
    assert (root.split, root.reason, root.rows) == ("NOT_SPLIT", "RECORD_AND_FACTORS_DIFFER", ())


def test_3_tolerance_literal() -> None:
    assert SOLVE_TOLERANCE == D("1E-12") and str(SOLVE_TOLERANCE) == "1E-12"
    assert agree(D("1"), D("1") + D("1E-12")) and not agree(D("1"), D("1") + D("2E-12"))
    assert rules.BRIDGE_ROOTS["MINI_GRID"] == ("contribution", "collected")


# --- test 4: invariants over every tree ----------------------------------------------------------------------------

def _trees() -> list[tuple[str, BridgeRow, bool]]:
    gone = {"delivered_kwh": _absent("delivered_kwh", "NOT_RECEIVED")}
    gone2 = {f: _absent(f, "NOT_RECEIVED") for f in ("delivered_kwh", "productive_tariff")}
    toy = _toy("p * x")
    out = [("1", kobo(), True), ("1-collected", kobo("collected"), True), ("2", kobo(diesel_price="1.30"), True),
           ("3a", bridge(MG, side("actual", stated={"revenue": stated("3458.00")}, **gone),
                         side("target", stated={"revenue": stated("3420.00", "DECLARED")}, **gone), "revenue"), True),
           ("3b", bridge(MG, side("actual", stated={"revenue": stated("3458.00")}, **gone2),
                         side("target", stated={"revenue": stated("3420.00", "DECLARED")}, **gone2), "revenue"), True),
           ("3c", bridge(MG, side("actual", stated={"revenue": stated("3500.00")}), side("target"), "revenue"), True),
           ("3d", bridge(toy, _toy_side(toy, "100", "0.50"), _toy_side(toy, "80", "0.40"), "y"), True),
           ("3g", bridge(MG, side("actual", om=_absent("om", "NOT_RECEIVED")), side("target"), "contribution"), True),
           ("3h", bridge(MG, side("actual"), side("target", currency=KES), "contribution"), True),
           ("3i", bridge(MG, side("actual"), _solved_target(), "fuel_cost"), False),
           ("3j", bridge(MG, side("actual", stated={"revenue": stated("3458.01")}), side("target"), "revenue"), True)]
    for expression in ("x * z", "x / z"):
        reg = _planted(expression)
        out.append((expression, bridge(reg, _planted_side(reg, "10", "4"), _planted_side(reg, "8", "4"), "y"), True))
    return out


def _sum(values) -> Decimal:
    """Spec §2.2's context (34 digits, half-even): the default 28 digits would round 3(i)'s difference away."""
    with localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN)):
        total = D("0")
        for v in values:
            total += v
        return total


@pytest.mark.parametrize("name", [n for n, _, _ in _trees()])
def test_4_invariants(name: str) -> None:  # plants V13, V14
    _, root, exact = next(t for t in _trees() if t[0] == name)
    check_invariants(name, root, exact)


def check_invariants(name: str, root: BridgeRow, exact: bool) -> None:
    for row in every(root):
        for v in (row.gap, row.effect, row.scale):
            assert v is None or not (v == 0 and v.is_signed()), (name, row.factor_id, v)  # never -0
        if row.split == "SPLIT":
            total = _sum(c.effect for c in row.rows)
            assert total == row.effect if exact else agree(total, row.effect), (name, row.factor_id)
            assert row.rows, (name, row.factor_id)
        else:
            assert row.rows == (), (name, row.factor_id)
        assert row.kind in rules.KINDS and row.split in rules.SPLITS
        assert (row.reason is None) == (row.split != "NOT_SPLIT"), (name, row.factor_id)
        if row.effect is None:
            assert row.evidence == "NOT_AVAILABLE"
        if row.kind == "RESIDUAL":
            assert row.factor_id is None and row.parent is not None
            assert (row.split, row.reason) == ("NOT_SPLIT", "DETAIL_NOT_AVAILABLE"), name  # D-5B.15
        assert row.factor_id not in ("collection_cost", "battery_wear", "extra_l"), (name, row.factor_id)
        assert all(c.kind != "RESIDUAL" for c in row.rows[:-1]), (name, row.factor_id)  # RESIDUAL last
    homes = by_home(root)
    if root.effect is None:
        assert dict(homes) == {}
    else:
        total = _sum(homes.values())
        assert total == root.effect if exact else agree(total, root.effect), name


# =====================================================================================================================
# Units 2 and 3 (spec §3, §4, §5.2): Lakeside's October, read through 4b's test reader and 5a's `TargetRead`.
# =====================================================================================================================

TREE = Path(__file__).resolve().parents[2]
FIXTURE_5B = TREE / "backend" / "tests" / "fixtures" / "attribution_lakeside_mto.json"
PACK = TREE / "Docs" / "demo-sprint" / "product-direction-layer4" / "derived-values.json"
OCT = "2026-10"
OF = "observed-financial"
CR = "COMMERCIAL_RECORD"
KOBO, KISIWA, MTO = "KOBO-001", "KISIWA-001", "MTO-001"
CODES = (KOBO, KISIWA, MTO)
PACK_NAMES = {"Kobo": KOBO, "Kisiwa": KISIWA, "Mto": MTO}
PACK_NODES = ("revenue", "collected", "in_transit", "outstanding", "fuel_cost", "om", "staff", "cost_to_serve",
              "contribution")
#: Spec §5.2 (handshake R9): the leaves that would split revenue and fuel cost, the same on every Site.
REVENUE_UNOBSERVED = (("adjustments_kwh", "delivered_kwh", "productive_tariff", "tariff", "technical_loss_kwh",
                       "unexplained_loss_kwh", "unmapped_kwh"), ("delivered_kwh", "productive_tariff", "tariff"))
FUEL_UNOBSERVED = (("candidate_l", "necessary_l", "unexplained_l"), ())
CHECK_KISIWA = TargetCheck("contribution", D("-60.00"), D("-65.00"), USD, False)


def mto_steps() -> list[dict]:
    return json.loads(FIXTURE_5B.read_text(encoding="utf-8"))["steps"]


def load_lakeside(w: dict, with_mto: bool = True) -> dict:
    """Spec §5.2's world: 4b's money fixture, 5a's steps 1 and 2 (their `at` and `entered_by`), then this file's step."""
    for step in money_steps():
        money_ingest(w, step["at"], step["batch"], step["entered_by"])
    t5a.load(w, 2)
    if with_mto:
        for step in mto_steps():
            money_ingest(w, step["at"], step["batch"], step["entered_by"])
    return w


@functools.lru_cache(maxsize=None)
def _world(with_mto: bool = True) -> dict:
    return load_lakeside(new_world(), with_mto)


def reads(w: dict) -> tuple[StructureRead, TargetRead]:
    """4b's test reader and 5a's `TargetRead` over it (spec §5.2)."""
    src = CommercialLeafSource(w["months"], w["store"], fallback())
    actual = StructureRead(src, stated=src)
    return actual, TargetRead(BudgetLineReader(w["months"], w["store"]), actual)


def ref(w: dict, code: str) -> SiteRef:
    return t5a.refs(w)[code]


def unit2_site(w: dict, code: str) -> SiteBridge:
    """Unit 2's call (spec §5.2): `site_bridge(read.site_inputs(s, OCT, READ_AT), targets.site(s, OCT, READ_AT))`."""
    actual, targets = reads(w)
    s = ref(w, code)
    return site_bridge(actual.site_inputs(s, OCT, READ_AT), targets.site(s, OCT, READ_AT))


def bridge_read(w: dict) -> BridgeRead:
    actual, targets = reads(w)
    return BridgeRead(actual, targets, clock=lambda: READ_AT)


def lakeside_portfolio(w: dict) -> PortfolioBridge:
    r = t5a.refs(w)
    return bridge_read(w).portfolio(w["tid"], [r[c] for c in CODES], OCT)


def money(v: Decimal | None, literal: str) -> None:
    assert v == D(literal) and format(v, "f") == literal, (v, literal)


# --- test 5: carrying (pure; Kisiwa's real inputs and targets, then one field replaced) -------------------------------

def _kisiwa() -> tuple[SiteInputs, SiteTargets]:
    w = _world()
    actual, targets = reads(w)
    s = ref(w, KISIWA)
    return actual.site_inputs(s, OCT, READ_AT), targets.site(s, OCT, READ_AT)


def _with_leaf(inputs: SiteInputs, factor: str, value: LeafValue, *, stated: bool = False) -> SiteInputs:
    if stated:
        return dataclasses.replace(inputs, stated={**inputs.stated, factor: value})
    return dataclasses.replace(inputs, leaves={**inputs.leaves, factor: value})


def _om_missing(**change) -> LeafValue:
    m = Missing("EXPENSE (OM)", CR, "NOT_RECEIVED", None, (), "Service contractor invoice", None, None)
    return LeafValue(None, "NOT_AVAILABLE", (), None, dataclasses.replace(m, **change), None)


def test_5a_kisiwa_om_is_carried_at_its_budget_line() -> None:  # plant V7 (the leaf)
    inputs, targets = _kisiwa()
    c = carry_at_target(inputs, targets.structure.values)
    assert c.carried == ("om",) and dict(c.not_carried) == {}
    rid = t5a.revision_of(_world(), "gen:KISIWA-001:2026-10:plan:om").id
    expected = LeafValue(D("700.00"), "ESTIMATED", (f"target:budget:{rid}",), None,
                         Missing("EXPENSE (OM)", CR, "NOT_RECEIVED", "TARGET", (), "Service contractor invoice",
                                 CARRIED_TEXT, None), USD, (E,))
    assert c.inputs.leaves["om"] == expected
    assert CARRIED_TEXT == "Not received: taken at its budget line for the month (estimate)"
    assert all(c.inputs.leaves[f] is inputs.leaves[f] for f in inputs.leaves if f != "om")
    assert c.inputs.stated is inputs.stated or dict(c.inputs.stated) == dict(inputs.stated)
    assert list(c.inputs.leaves) == list(inputs.leaves)  # registry order kept


def test_5b_an_open_month_is_never_carried() -> None:  # plant V5
    inputs, targets = _kisiwa()
    opened = _with_leaf(inputs, "om", _om_missing(note="MONTH_OPEN"))
    c = carry_at_target(opened, targets.structure.values)
    assert c.carried == () and dict(c.not_carried) == {"om": "MONTH_OPEN"}
    root = site_bridge(opened, targets).roots["contribution"]
    assert (root.split, root.reason, root.effect, root.evidence) == ("NOT_SPLIT", "GAP_NOT_AVAILABLE", None,
                                                                     "NOT_AVAILABLE")


def test_5c_a_source_not_connected_is_never_carried() -> None:
    inputs, targets = _kisiwa()
    c = carry_at_target(_with_leaf(inputs, "om", _om_missing(cause="NOT_CONNECTED")), targets.structure.values)
    assert c.carried == () and dict(c.not_carried) == {"om": "NOT_CONNECTED"}


def test_5d_an_assumed_target_is_never_carried() -> None:  # plant V6
    inputs, targets = _kisiwa()
    t = dict(targets.structure.values)
    t["om"] = dataclasses.replace(t["om"], evidence="ESTIMATED", sources=("assumption:at-actual",))
    c = carry_at_target(inputs, t)
    assert c.carried == () and dict(c.not_carried) == {"om": NO_TARGET_LINE}
    assert NO_TARGET_LINE == "NO_TARGET_LINE"


def test_5e_a_stated_heading_is_never_carried() -> None:  # plant V4
    inputs, targets = _kisiwa()
    gone = LeafValue(None, "NOT_AVAILABLE", (), None,
                     Missing("EXPENSE (FUEL)", CR, "NOT_RECEIVED", None, (), "Fuel invoices for the month", None),
                     None)
    given = _with_leaf(inputs, "fuel_cost", gone, stated=True)
    assert targets.structure.values["fuel_cost"].evidence == "DECLARED"
    c = carry_at_target(given, targets.structure.values)
    assert c.inputs.stated["fuel_cost"] == gone and c.inputs.stated["fuel_cost"].value is None
    assert "fuel_cost" not in c.carried and "fuel_cost" not in c.not_carried
    assert c.carried == ("om",)


def test_5f_a_leaf_outside_the_list_is_untouched() -> None:
    inputs, targets = _kisiwa()
    gone = dataclasses.replace(_om_missing(), missing=Missing("EXPENSE (FUEL)", CR, "NOT_RECEIVED", None, (), None,
                                                              None))
    c = carry_at_target(_with_leaf(inputs, "diesel_price", gone), targets.structure.values)
    assert c.inputs.leaves["diesel_price"] == gone
    assert "diesel_price" not in c.carried and "diesel_price" not in c.not_carried


# --- test 6: the three Site bridges (spec §5.2) -----------------------------------------------------------------------

#: Spec §5.2's table: root (actual, target, gap), evidence, revenue TERM effect, cost to serve TERM (fuel, om, staff).
SITE_TABLE = {
    KOBO: (("883.00", "1445.00", "-562.00"), "DECLARED", "38.00", "-600.00", ("-600.00", "0.00", "0.00")),
    KISIWA: (("-250.00", "-65.00", "-185.00"), "ESTIMATED", "-55.00", "-130.00", ("-130.00", "0.00", "0.00")),
    MTO: (("810.00", "915.00", "-105.00"), "DECLARED", "-80.00", "-25.00", ("-25.00", "0.00", "0.00")),
}
SITE_HOMES = {KOBO: ("38.00", "-600.00"), KISIWA: ("-55.00", "-130.00"), MTO: ("-80.00", "-25.00")}
#: Cash roots (actual, target, gap; in_transit effect, outstanding effect).
SITE_CASH = {KOBO: ("3180.00", "3420.00", "-240.00", "0", "-278.00"),
             KISIWA: ("3800.00", "4125.00", "-325.00", "0", "-270.00"),
             MTO: ("1890.00", "2240.00", "-350.00", "-150.00", "-120.00")}


def check_site(sb: SiteBridge, code: str, w: dict) -> None:
    (actual, target, gap), evidence, revenue, cts, (fuel, om, staff) = SITE_TABLE[code]
    assert (sb.site_code, sb.month, sb.structure_key, sb.structure_version) == (code, OCT, "MINI_GRID", MG.version)
    assert list(sb.roots) == ["contribution", "collected"]
    root = sb.roots["contribution"]
    assert (root.factor_id, root.kind, root.split, root.reason) == ("contribution", "ROOT", "SPLIT", None)
    money(root.actual, actual), money(root.target, target), money(root.gap, gap), money(root.effect, gap)
    assert root.evidence == evidence, (code, root.evidence)
    assert [(r.factor_id, r.kind) for r in root.rows] == [("revenue", "TERM"), ("cost_to_serve", "TERM")]
    rev, cost = root.rows
    money(rev.effect, revenue)
    assert (rev.split, rev.reason, rev.rows) == ("NOT_SPLIT", "DETAIL_NOT_AVAILABLE", ()), code
    assert (rev.unobserved_actual, rev.unobserved_target) == REVENUE_UNOBSERVED, code
    money(cost.effect, cts)
    assert cost.split == "SPLIT" and [r.factor_id for r in cost.rows] == ["fuel_cost", "om", "staff"], code
    f, o, s = cost.rows
    money(f.effect, fuel), money(o.effect, om), money(s.effect, staff)
    assert (f.split, f.reason, f.rows) == ("NOT_SPLIT", "DETAIL_NOT_AVAILABLE", ()), code
    assert (f.unobserved_actual, f.unobserved_target) == FUEL_UNOBSERVED, code
    assert (o.split, s.split) == ("LEAF", "LEAF")
    assert o.carried is (code == KISIWA) and s.carried is False
    if code == KISIWA:
        assert o.evidence == "ESTIMATED"
    grow, cut = SITE_HOMES[code]
    assert dict(sb.by_home) == {"GROW_REVENUE": D(grow), "OPTIMIZE_COST": D(cut)}
    assert [format(v, "f") for v in sb.by_home.values()] == [grow, cut]
    # the cash root
    ca, ct, cg, transit, outstanding = SITE_CASH[code]
    cash = sb.roots["collected"]
    money(cash.actual, ca), money(cash.target, ct), money(cash.gap, cg), money(cash.effect, cg)
    assert cash.evidence == "ESTIMATED" and weakest_origin(cash.origins) == "unknown", (code, cash.origins)
    cash_rows = {r.factor_id: r for r in cash.rows}
    assert cash_rows["in_transit"].effect == D(transit) and cash_rows["outstanding"].effect == D(outstanding)
    money(cash_rows["outstanding"].effect, outstanding)
    # carried leaves and the target's own checks
    if code == KISIWA:
        assert sb.carried == ("om",) and dict(sb.not_carried) == {}
        rid = t5a.revision_of(w, "gen:KISIWA-001:2026-10:plan:om").id
        om_v = sb.actual.values["om"]
        assert (om_v.value, om_v.evidence, om_v.sources, om_v.origins, om_v.currency) == (
            D("700.00"), "ESTIMATED", (f"target:budget:{rid}",), (E,), USD)
        assert om_v.missing == Missing("EXPENSE (OM)", CR, "NOT_RECEIVED", "TARGET", ("cost_to_serve", "contribution"),
                                       "Service contractor invoice", CARRIED_TEXT, None)
        assert sb.targets.checks == (CHECK_KISIWA,)
    else:
        assert sb.carried == () and dict(sb.not_carried) == {}
    # the pack (handshake R13): actual against `actual.nodes`, target against `plan.nodes`
    name = next(n for n, c in PACK_NAMES.items() if c == code)
    pack = json.loads(PACK.read_text(encoding="utf-8"))["sites"][f"lakeside-power/{name}"]
    rows = {r.factor_id: r for root_ in sb.roots.values() for r in every(root_) if r.factor_id is not None}
    for node in PACK_NODES:
        assert D(str(pack["actual"]["nodes"][node])) == rows[node].actual, (code, node)
        assert D(str(pack["plan"]["nodes"][node])) == rows[node].target, (code, node)


@pytest.mark.parametrize("code", CODES)
def test_6_the_three_site_bridges(code: str) -> None:  # plants V7, V8, V11
    w = _world()
    check_site(unit2_site(w, code), code, w)


def test_6_kobo_root_origins() -> None:
    root = unit2_site(_world(), KOBO).roots["contribution"]
    assert root.origins == (OF, E)


def test_6_inputs_and_targets_must_share_key_version_and_month() -> None:
    w = _world()
    actual, targets = reads(w)
    s = ref(w, KOBO)
    inputs, t = actual.site_inputs(s, OCT, READ_AT), targets.site(s, OCT, READ_AT)
    for bad in (dataclasses.replace(inputs, month="2026-09"), dataclasses.replace(inputs, structure_version=0)):
        with pytest.raises(StructureError) as e:
            site_bridge(bad, t)
        assert (e.value.code, e.value.factor_id) == ("STRUCTURE_COMPOSE", KOBO)


@pytest.mark.parametrize("code", CODES)
@pytest.mark.parametrize("root", ["contribution", "collected"])
def test_4_invariants_on_the_site_bridges(code: str, root: str) -> None:  # test 4 over test 6's trees
    check_invariants(f"6-{code}-{root}", unit2_site(_world(), code).roots[root], True)


# --- test 7: the portfolio (spec §5.2) --------------------------------------------------------------------------------

#: key: (actual, target, gap, effect, evidence, carried)
PORTFOLIO_TABLE = {
    "contribution": ("1443.00", "2295.00", "-852.00", "-852.00", "ESTIMATED", (KISIWA,)),
    "revenue": ("9688.00", "9785.00", "-97.00", "-97.00", "DECLARED", ()),
    "cost_to_serve": ("8245.00", "7490.00", "755.00", "-755.00", "ESTIMATED", (KISIWA,)),
    "fuel_cost": ("4995.00", "4240.00", "755.00", "-755.00", "DECLARED", ()),
    "om": ("1800.00", "1800.00", "0.00", "0.00", "ESTIMATED", (KISIWA,)),
    "staff": ("1450.00", "1450.00", "0.00", "0.00", "DECLARED", ()),
}


def check_portfolio(pb: PortfolioBridge, w: dict) -> None:
    assert (pb.month, pb.structure_key, pb.structure_version, pb.asked) == (OCT, "MINI_GRID", MG.version, CODES)
    assert tuple(pb.sites) == CODES and list(pb.rows) == ["contribution", "collected"]
    rows = pb.rows["contribution"]
    for key, (actual, target, gap, effect, evidence, carried) in PORTFOLIO_TABLE.items():
        row = rows[key]
        money(row.actual, actual), money(row.target, target), money(row.gap, gap), money(row.effect, effect)
        assert (row.evidence, row.carried, row.k, row.n, row.out) == (evidence, carried, 3, 3, ()), key
        assert (row.currency, row.note) == (USD, None), key
    assert dict(pb.by_home) == {"GROW_REVENUE": D("-97.00"), "OPTIMIZE_COST": D("-755.00")}
    assert pb.disagreements == ((KISIWA, CHECK_KISIWA),)
    assert [(line.factor_id, line.value) for line in pb.portfolio_lines.lines] == [("staff", D("1200.00"))]
    cash = pb.rows["collected"]
    money(cash["collected"].actual, "8870.00"), money(cash["collected"].target, "9785.00")
    money(cash["collected"].gap, "-915.00"), money(cash["collected"].effect, "-915.00")
    money(cash["in_transit"].effect, "-150.00"), money(cash["outstanding"].effect, "-668.00")
    # the pack (SUM keys only, handshake R13; D-5B.11)
    sums = json.loads(PACK.read_text(encoding="utf-8"))["portfolio"]["lakeside-power"]
    every_row = {k: r for tree in pb.rows.values() for k, r in tree.items()}
    for node in PACK_NODES:
        assert MG.row(node).composes == "SUM", node
        assert D(str(sums["actual"]["sums"][node])) == every_row[node].actual, node
        assert D(str(sums["plan"]["sums"][node])) == every_row[node].target, node
    for key, row in every_row.items():
        if row.kind != "RESIDUAL" and MG.row(key).composes != "SUM":
            assert (row.actual, row.target, row.gap) == (None, None, None), key


def test_7_the_portfolio_is_1443_against_2295_3_of_3() -> None:  # plants V8, V9, V15, V20
    w = _world()
    check_portfolio(lakeside_portfolio(w), w)


# --- test 8: never one set minus another, never a summed price --------------------------------------------------------

def test_8a_without_mto_billing_the_gap_is_747_over_2_of_3() -> None:  # plants V9, V10
    w = _world(False)
    mto = unit2_site(w, MTO).roots["contribution"]
    assert (mto.split, mto.reason, mto.effect, mto.evidence) == ("NOT_SPLIT", "GAP_NOT_AVAILABLE", None,
                                                                 "NOT_AVAILABLE")
    assert (mto.unobserved_actual, mto.unobserved_target) == (MTO_MISSING, ())
    row = lakeside_portfolio(w).rows["contribution"]["contribution"]
    money(row.actual, "633.00"), money(row.target, "1380.00"), money(row.gap, "-747.00"), money(row.effect, "-747.00")
    assert (row.k, row.n) == (2, 3)
    assert row.out == ((MTO, tuple(f"actual:{leaf}" for leaf in MTO_MISSING)),)


def _hand_site(code: str, currency: str = USD, **actual_values: str) -> SiteBridge:
    """A Site bridge from §5.1's hand-built leaves (no records)."""
    inputs = SiteInputs(code, OCT, "MINI_GRID", MG.version, leaves("actual", {**ACTUAL, **actual_values}, currency), {})
    target = SiteStructure(code, OCT, "MINI_GRID", MG.version, side("target", currency=currency))
    return site_bridge(inputs, SiteTargets(target, None, (), currency))


def _hand_portfolio(*sites: SiteBridge) -> PortfolioBridge:
    return portfolio_bridge({s.site_code: s for s in sites}, [s.site_code for s in sites], {}, None, OCT, "MINI_GRID",
                            MG.version)


def test_8b_two_currencies_are_never_added() -> None:
    pb = _hand_portfolio(_hand_site("A-001"), _hand_site("B-001", KES))
    row = pb.rows["contribution"]["contribution"]
    assert (row.actual, row.target, row.gap, row.effect) == (None, None, None, None)
    assert row.note == "CURRENCY_MISMATCH:KES,USD"
    assert dict(pb.by_home) == {}


def test_8c_a_price_never_adds_across_sites() -> None:  # plant V17 (D-5B.11)
    pb = _hand_portfolio(_hand_site("A-001"), _hand_site("B-001", diesel_price="1.30"))
    rows = pb.rows["contribution"]
    price = rows["diesel_price"]
    assert (price.actual, price.target, price.gap) == (None, None, None)
    money(price.effect, "-59.00")
    assert (price.k, price.n, price.kind) == (2, 2, "PRICE")
    tariff = rows["tariff"]
    assert (tariff.actual, tariff.target, tariff.gap) == (None, None, None)
    money(tariff.effect, "0.00")
    litres = rows["diesel_l"]
    assert (litres.actual, litres.target, litres.gap) == (D("2360"), D("1400"), D("960"))
    money(litres.effect, "-1200.00")



def test_8d_an_open_month_shows_no_figure_never_zero() -> None:  # reviewer plant R3 (k = 0 written as 0.00)
    w = _world()
    r = t5a.refs(w)
    pb = bridge_read(w).portfolio(w["tid"], [r[c] for c in CODES], "2026-11")
    rows = [row for tree in pb.rows.values() for row in tree.values()]
    assert rows
    for row in rows:
        assert row.k == 0 and row.n == 3, row.key
        assert row.effect is None and row.evidence == "NOT_AVAILABLE", row.key
    row = pb.rows["contribution"]["contribution"]
    assert (row.actual, row.target, row.gap, row.effect) == (None, None, None, None)
    assert {c for c, _ in row.out} == set(CODES)
    assert dict(pb.by_home) == {}


def test_8e_the_builders_refuse_mismatched_parts() -> None:
    a = _hand_site("A-001")
    for bad in (dataclasses.replace(a, month="2026-09"), dataclasses.replace(a, structure_key="OTHER"),
                dataclasses.replace(a, structure_version=a.structure_version + 1)):
        with pytest.raises(StructureError):
            portfolio_bridge({"A-001": bad}, ["A-001"], {}, None, OCT, "MINI_GRID", MG.version)


def test_8f_a_site_bridge_refuses_another_sites_targets() -> None:
    inputs = SiteInputs("A-001", OCT, "MINI_GRID", MG.version, leaves("actual", ACTUAL, USD), {})
    other = SiteStructure("B-001", OCT, "MINI_GRID", MG.version, side("target"))
    with pytest.raises(StructureError):
        site_bridge(inputs, SiteTargets(other, None, (), USD))


# --- test 9: the read --------------------------------------------------------------------------------------------------

def test_9a_the_portfolio_read_refuses_as_the_target_read_does() -> None:
    w = _world()
    r = t5a.refs(w)
    for tenant, asked in ((w["tid"], [r[KOBO], r[KOBO]]), (w["tenants"]["harvest-cold"], [r[KOBO]])):
        with pytest.raises(StructureError) as e:
            bridge_read(w).portfolio(tenant, asked, OCT)
        assert (e.value.code, e.value.factor_id) == ("STRUCTURE_COMPOSE", KOBO)
    cold = SiteRef(w["tid"], w["sites"][KISIWA], KISIWA, "COLDCHAIN", t5a.TZ)
    pb = bridge_read(w).portfolio(w["tid"], [r[KOBO], cold], OCT)
    assert tuple(pb.sites) == (KOBO,) and pb.asked == (KOBO, KISIWA)
    seen = 0
    for tree in pb.rows.values():
        for key, row in tree.items():
            assert row.n == 2 and (KISIWA, ("STRUCTURE_OTHER_KEY",)) in row.out, key
            seen += 1
    assert seen > 0


class _Recorder:
    """Records the `known_at` of every call it passes on (test 9(b))."""

    def __init__(self, inner, seen: list) -> None:
        self._inner, self._seen = inner, seen

    def __getattr__(self, name):
        method = getattr(self._inner, name)

        def call(*args, **kwargs):
            at = kwargs.get("known_at", next((a for a in args if isinstance(a, datetime)), None))
            self._seen.append((name, at))
            return method(*args, **kwargs)
        return call


def test_9b_one_instant_per_read() -> None:  # plant V19 (D-5B.13)
    w = _world()
    seen: list = []
    src = CommercialLeafSource(w["months"], w["store"], fallback())
    actual = _Recorder(StructureRead(src, stated=src), seen)
    targets = _Recorder(TargetRead(BudgetLineReader(w["months"], w["store"]), actual), seen)
    calls: list[datetime] = []

    def clock() -> datetime:  # a clock that moves on every call
        calls.append(READ_AT + timedelta(seconds=len(calls)))
        return calls[-1]

    read = BridgeRead(actual, targets, clock=clock)
    r = t5a.refs(w)
    read.site(r[KISIWA], OCT)
    assert len(calls) == 1
    assert {k for n, k in seen} == {calls[0]}, seen
    seen.clear()
    read.portfolio(w["tid"], [r[c] for c in CODES], OCT)
    assert len(calls) == 2  # once per call, not once per Site
    names = {name for name, _ in seen}
    assert {"site_inputs", "site", "portfolio"} <= names, names
    assert {k for _, k in seen} == {calls[1]}, seen


def test_9c_a_naive_time_is_refused() -> None:
    w = _world()
    with pytest.raises(ValueError):
        bridge_read(w).site(t5a.refs(w)[KISIWA], OCT, known_at=datetime(2026, 11, 1, 12, 0))


# --- test 10: the boundaries -------------------------------------------------------------------------------------------

ATTRIBUTION = TREE / "backend" / "assetops_backend" / "structure" / "attribution"


def _imports(path: Path) -> list[str]:
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.append(node.module)
    return out


def test_10_no_float_and_no_commercial_or_snapshot_import() -> None:  # plant: a commercial import in bridge.py
    modules = sorted(ATTRIBUTION.glob("*.py"))
    assert {m.name for m in modules} >= {"rules.py", "bridge.py", "carry.py", "site.py", "portfolio.py", "read.py",
                                         "composition.py"}
    for m in modules:
        assert "float(" not in m.read_text(encoding="utf-8"), m.name
        names = _imports(m)
        assert not any("snapshot" in n for n in names), (m.name, names)
        if m.name != "composition.py":
            assert not any(n.split(".")[:2] == ["assetops_backend", "commercial"] for n in names), (m.name, names)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=TREE, capture_output=True, text=True, check=True).stdout


def _on_5b_branch() -> bool:
    try:
        return _git("rev-parse", "--abbrev-ref", "HEAD").strip().startswith("task/5b-")
    except (OSError, subprocess.CalledProcessError):
        return False


@pytest.mark.skipif(not _on_5b_branch(), reason="5b's branch check only (another lane may own structure/read.py)")
def test_10_no_diff_in_the_seam_and_the_packet_lists_every_5b_file() -> None:  # plant V22
    assert _git("diff", "main...HEAD", "--", "backend/assetops_backend/structure/read.py") == ""
    changed = [p for p in _git("diff", "--name-only", "main...HEAD").split()
               if p.startswith(("backend/assetops_backend/structure/attribution/", "backend/tests/test_5b_",
                                "backend/tests/fixtures/attribution_", "specs/5b-attribution/"))]
    packet = (TREE / "specs" / "5b-attribution" / "packet-u23.md").read_text(encoding="utf-8")
    assert changed and [p for p in changed if p not in packet] == []


# --- test 11: a repeated key ---------------------------------------------------------------------------------------------

def test_11_a_factor_twice_in_one_tree_is_refused() -> None:  # plant V21
    sb = _hand_site("A-001")
    root = sb.roots["contribution"]
    om = find(root, "om")
    twice = dataclasses.replace(root, rows=(*root.rows, om))
    bad = dataclasses.replace(sb, roots={**sb.roots, "contribution": twice})
    with pytest.raises(ValueError) as e:
        _hand_portfolio(bad, _hand_site("B-001"))
    assert str(e.value) == "REPEATED_FACTOR:om"
