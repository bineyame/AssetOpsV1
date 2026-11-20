"""5b (spec `specs/5b-attribution/spec.md` rev 2; rulings D-5B.1 to D-5B.14): attribution, the gap explained by its drivers.

Unit 1 (spec §2, §5.1): the split rules, tests 1 to 4. No database. Every expected value is spec §5.1's hand-computed
literal (W2), typed here; none is derived from the code under test. The leaves are hand-built and evaluated with 3B3's
`evaluate`; the toy registry is 5a's `_toy` (imported, never edited).
"""
from __future__ import annotations

import dataclasses
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext

import pytest

from assetops_backend.structure.attribution import rules
from assetops_backend.structure.attribution.bridge import BridgeRow, bridge, by_home, lowest
from assetops_backend.structure.attribution.rules import SOLVE_TOLERANCE, agree
from assetops_backend.structure.evaluate import LeafValue, Missing, evaluate
from assetops_backend.structure.registry import REGISTRIES, FactorRow, FilledBy, Registry
from assetops_backend.structure.targets.rules import solve_main
from assetops_contracts.canonical.units import KWH, MONEY
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
    # Mid-build Q1 (`mid-build-questions.md`): the RESIDUAL row's `split`/`reason` are not fixed by the spec; not
    # asserted here until the Architect rules.
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
        assert row.factor_id not in ("collection_cost", "battery_wear", "extra_l"), (name, row.factor_id)
        assert all(c.kind != "RESIDUAL" for c in row.rows[:-1]), (name, row.factor_id)  # RESIDUAL last
    homes = by_home(root)
    if root.effect is None:
        assert dict(homes) == {}
    else:
        total = _sum(homes.values())
        assert total == root.effect if exact else agree(total, root.effect), name
