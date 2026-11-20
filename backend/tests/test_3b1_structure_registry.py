"""3B1: the structure registry, mini-grid (spec §6, T1-T5).

T1 is the independent check (W2, R7): its expectations come from the pack
manifest and from this file's own literal home map; it never reads `HOMES` or
`rows_mini_grid.py` for an expected value. T2's unit table is written here.
No database: run with `DATABASE_URL` and `ASSETOPS_TEST_DATABASE_URL` unset (P1).
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from assetops_backend.config import ConfigurationError
from assetops_backend.outcomes.catalogue import CATEGORIES
from assetops_backend.structure import registry as registry_module
from assetops_backend.structure.check import StructureError, check, check_all
from assetops_backend.structure.expressions import (
    Bin,
    Call,
    ExpressionError,
    Neg,
    Num,
    Ref,
    UnitError,
    parse,
    unit_of,
)
from assetops_backend.structure.registry import (
    REGISTRIES,
    FactorRow,
    FilledBy,
    Home,
    Registry,
    Tolerance,
)
from assetops_contracts.canonical import DAY, HOUR, KWH, L, MONEY, leaves_of
from assetops_contracts.canonical.units import KW, ONE

MANIFEST_PATH = (
    Path(__file__).resolve().parents[2]
    / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml"
)
_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)  # P4
MANIFEST = yaml.load(MANIFEST_PATH.read_text(encoding="utf-8"), Loader=_LOADER)  # once per module

# The test's own home map (R7). The four category values are checked against CATEGORIES below.
OWN_HOME_MAP = {
    "grow": "GROW_REVENUE",
    "optimize": "OPTIMIZE_COST",
    "protect": "PROTECT_ASSET",
    "assure": "ASSURE_PERFORMANCE",
    "above": "ABOVE",
    "calendar": "CALENDAR",
}

MG = REGISTRIES["MINI_GRID"]


def _home(entry: list) -> tuple[str, str | None]:
    return OWN_HOME_MAP[entry[0]], (entry[1] if len(entry) > 1 else None)


def _replace(reg: Registry, target: str, **changes) -> Registry:
    rows = tuple(dataclasses.replace(r, **changes) if r.factor_id == target else r for r in reg.rows)
    assert rows != reg.rows, f"plant did not touch {target}"
    return dataclasses.replace(reg, rows=rows)


def _refused(reg: Registry) -> str:
    with pytest.raises(StructureError) as caught:
        check(reg)
    return str(caught.value)


# ---------------------------------------------------------------- T1 parity with the manifest


def test_t1_own_home_map_categories_are_the_catalogue_codes():
    assert [OWN_HOME_MAP[k] for k in ("grow", "optimize", "protect", "assure")] == list(CATEGORIES)


def test_t1_47_rows_31_leaves_16_nodes():
    assert MG.structure_key == "MINI_GRID" and MG.version == 3
    assert len(MG.rows) == 47
    assert sum(r.is_leaf for r in MG.rows) == 31
    assert sum(not r.is_leaf for r in MG.rows) == 16
    assert set(REGISTRIES) == {"MINI_GRID"}


def test_t1_nodes_and_expressions_equal_the_manifest_structure():
    nodes = {r.factor_id: r.expression for r in MG.rows if not r.is_leaf}
    assert nodes == MANIFEST["structures"]["MINI_GRID"]


def test_t1_leaf_set_equals_factor_map():
    leaves = {r.factor_id for r in MG.rows if r.is_leaf}
    assert leaves == set(MANIFEST["factor_map"]["MINI_GRID"])


def test_t1_leaf_sources_absence_and_words_equal_the_manifest():
    sources = MANIFEST["empty_states"]["leaf_sources"]["MINI_GRID"]
    leaves = [r for r in MG.rows if r.is_leaf]
    assert {r.factor_id for r in leaves} == set(sources)
    for row in leaves:
        declared = sources[row.factor_id]
        assert row.filled_by == FilledBy(declared["family"], declared["kind"], declared.get("words")), row.factor_id
        assert row.filled_by.words == declared.get("words"), row.factor_id  # R13
        assert row.absent == declared["absent"], row.factor_id
    # The words field is not vacuous: the manifest declares some.
    assert any(r.filled_by.words for r in leaves)


def test_t1_every_row_home_equals_home_categories():
    homes = MANIFEST["home_categories"]["nodes"]["MINI_GRID"]
    for row in MG.rows:
        category, objective = _home(homes[row.factor_id])
        assert (row.home.category, row.home.objective) == (category, objective), row.factor_id
    assert set(homes) - {r.factor_id for r in MG.rows} == {"cover_not_claimable", "unclaimable_cover"}


def test_t1_manifest_fuel_balance_tolerance_is_the_structure_default():
    sites = [s for t in MANIFEST["tenants"] if t["vertical"] == "MINI_GRID" for s in t["sites"]]
    # MTO-001 declares no fuel balance; every Site that declares one is pinned (two today).
    tolerances = [s["period"]["fuel_balance"]["tolerance_pct"] for s in sites if "fuel_balance" in s["period"]]
    assert len(tolerances) >= 2 and all(Decimal(str(t)) == Decimal("2.0") for t in tolerances)
    tolerated = {r.factor_id: r.tolerance for r in MG.rows if r.tolerance is not None}
    assert tolerated == {"unexplained_l": Tolerance(of_factor="diesel_l", pct=Decimal("2.0"))}


def test_rows_order_is_leaves_in_catalogue_order_then_nodes():
    ids = [r.factor_id for r in MG.rows]
    assert ids[:31] == list(leaves_of("MINI_GRID"))
    assert ids[31:] == list(MANIFEST["structures"]["MINI_GRID"])  # §2.2's order is the manifest's


def test_children_are_distinct_first_seen_names_without_functions():
    assert MG.row("shortfall_backed").children == ("standby_kw", "lost_unit_kw")
    assert MG.row("revenue").children == ("billed_kwh", "tariff", "productive_kwh", "productive_tariff")
    assert MG.row("tariff").children == ()
    row = dataclasses.replace(MG.row("contribution"), expression="revenue - revenue + max(revenue, 0)")
    assert row.children == ("revenue",)


def test_r14_records_do_no_validation():
    row = FactorRow("not an id!", "**", "no unit", None, FilledBy("X", "y"), "WHATEVER", Tolerance("q", Decimal(-1)))
    assert row.home is None
    assert Registry("NOPE", 0, (row, row)).structure_key == "NOPE"
    assert Home("ANY", "Z9").objective == "Z9"


# ---------------------------------------------------------------- T2 units

EXPECTED_NODE_UNITS = {
    "metered_kwh": KWH,
    "billed_kwh": KWH,
    "revenue": MONEY,
    "collected": MONEY,
    "diesel_l": L,
    "fuel_cost": MONEY,
    "battery_wear": MONEY,
    "cost_to_serve": MONEY,
    "contribution": MONEY,
    "obligation_hours_without_redundancy": HOUR,
    "shortfall_backed": ONE,
    "obligation_hours_without_backup": HOUR,
    "replayed_dawn_days_below_safeguard": DAY,
    "asset_days_out_of_service": DAY,
    "asset_days_total": DAY,
    "asset_days_available": DAY,
}


def test_t2_check_all_passes():
    check_all()


def test_t2_composed_node_units_equal_the_table():
    declared = {r.factor_id: r.unit for r in MG.rows}
    nodes = {r.factor_id: r for r in MG.rows if not r.is_leaf}
    assert set(nodes) == set(EXPECTED_NODE_UNITS)
    for factor_id, expected in EXPECTED_NODE_UNITS.items():
        assert unit_of(parse(nodes[factor_id].expression), declared) == expected, factor_id
        assert nodes[factor_id].unit == expected, factor_id


@pytest.mark.parametrize(
    ("text", "units", "expected"),
    [
        ("max(x, 0)", {"x": MONEY}, MONEY),
        ("0 - cost", {"cost": MONEY}, MONEY),
        ("min(1, y)", {"y": ONE}, ONE),
        ("max(lost_unit_kw, 1)", {"lost_unit_kw": KW}, KW),
        ("1 - shortfall_backed", {"shortfall_backed": ONE}, ONE),
        ("min(1, floor(a / max(b, 1)))", {"a": KW, "b": KW}, ONE),
        ("x * 2", {"x": KWH}, KWH),
        ("2 / x", {"x": DAY}, ONE / DAY),
        ("2", {}, ONE),
        ("-x", {"x": L}, L),
        ("ceil(x)", {"x": HOUR}, HOUR),
        # T2b literal edges (R16)
        ("x - (1 + 1)", {"x": KWH}, KWH),
        ("max(x, -1)", {"x": MONEY}, MONEY),
        ("x + 2 * 3", {"x": L}, L),
    ],
)
def test_t2_literal_rule(text, units, expected):
    assert unit_of(parse(text), units) == expected


@pytest.mark.parametrize("text", ["x + y", "max(x, y)", "x - y * 1"])
def test_t2_unequal_operands_cannot_compose(text):
    with pytest.raises(UnitError):
        unit_of(parse(text), {"x": KWH, "y": MONEY})


# ---------------------------------------------------------------- T3 refusals (one plant per code)


def test_t3_duplicate():
    reg = dataclasses.replace(MG, rows=MG.rows + (MG.row("tariff"),))
    assert _refused(reg) == "STRUCTURE_DUPLICATE MINI_GRID/tariff"


@pytest.mark.parametrize("bad", ["diesel_l ** diesel_price", "diesel_l *", "diesel_l.x", "foo(diesel_l)", "1e3 * diesel_l"])
def test_t3_expression(bad):
    assert _refused(_replace(MG, "fuel_cost", expression=bad)) == "STRUCTURE_EXPRESSION MINI_GRID/fuel_cost"


def test_t3_unknown_factor():
    reg = _replace(MG, "fuel_cost", expression="diesel_l * diesel_cost")
    assert _refused(reg) == "STRUCTURE_UNKNOWN_FACTOR MINI_GRID/fuel_cost"


def test_t3_cycle_names_the_first_row_on_the_cycle():
    reg = _replace(MG, "diesel_l", expression="necessary_l + fuel_cost")  # reviewer probe P1
    assert _refused(reg) == "STRUCTURE_CYCLE MINI_GRID/diesel_l"
    reg = _replace(MG, "metered_kwh", expression="delivered_kwh + contribution")
    assert _refused(reg) == "STRUCTURE_CYCLE MINI_GRID/metered_kwh"


def test_t3_catalogue_both_directions():
    assert _refused(_replace(MG, "liability", factor_id="liability_x")) == "STRUCTURE_CATALOGUE MINI_GRID/liability_x"
    assert _refused(_replace(MG, "liability", unit=KWH)) == "STRUCTURE_CATALOGUE MINI_GRID/liability"
    cold_leaf = dataclasses.replace(MG.row("liability"), factor_id="crate_days", unit=DAY)
    assert _refused(dataclasses.replace(MG, rows=MG.rows + (cold_leaf,))) == "STRUCTURE_CATALOGUE MINI_GRID/crate_days"
    without = tuple(r for r in MG.rows if r.factor_id != "liability")  # reviewer probe P2b
    assert _refused(dataclasses.replace(MG, rows=without)) == "STRUCTURE_CATALOGUE MINI_GRID/liability"
    node_as_leaf_id = dataclasses.replace(MG.row("asset_days_total"), factor_id="base_kwh")
    assert _refused(dataclasses.replace(MG, rows=MG.rows + (node_as_leaf_id,))) == "STRUCTURE_CATALOGUE MINI_GRID/base_kwh"
    assert _refused(dataclasses.replace(MG, structure_key="SOLAR_FARM")) == "STRUCTURE_CATALOGUE SOLAR_FARM/-"


def test_t3_leaf_source():
    assert _refused(_replace(MG, "om", filled_by=None)) == "STRUCTURE_LEAF_SOURCE MINI_GRID/om"
    bad_family = FilledBy("EMAIL", "invoice")
    assert _refused(_replace(MG, "om", filled_by=bad_family)) == "STRUCTURE_LEAF_SOURCE MINI_GRID/om"
    node_source = FilledBy("DECLARED", "x")
    assert _refused(_replace(MG, "fuel_cost", filled_by=node_source)) == "STRUCTURE_LEAF_SOURCE MINI_GRID/fuel_cost"


def test_t3_leaf_absent():
    assert _refused(_replace(MG, "om", absent=None)) == "STRUCTURE_LEAF_ABSENT MINI_GRID/om"
    assert _refused(_replace(MG, "om", absent="SOMETIMES")) == "STRUCTURE_LEAF_ABSENT MINI_GRID/om"
    assert _refused(_replace(MG, "om", absent="NEVER_EMPTY")) == "STRUCTURE_LEAF_ABSENT MINI_GRID/om"
    assert _refused(_replace(MG, "period_days", absent="MISSING")) == "STRUCTURE_LEAF_ABSENT MINI_GRID/period_days"
    assert _refused(_replace(MG, "fuel_cost", absent="MISSING")) == "STRUCTURE_LEAF_ABSENT MINI_GRID/fuel_cost"


def test_t3_tolerance():
    for bad in (
        Tolerance("diesel_litres", Decimal("2.0")),
        Tolerance("fuel_cost", Decimal("2.0")),
        Tolerance("diesel_l", Decimal("0")),
        Tolerance("diesel_l", Decimal("-1")),
    ):
        assert _refused(_replace(MG, "unexplained_l", tolerance=bad)) == "STRUCTURE_TOLERANCE MINI_GRID/unexplained_l", bad
    node_tolerance = _replace(MG, "fuel_cost", tolerance=Tolerance("cost_to_serve", Decimal("1")))
    check(node_tolerance)  # a node's tolerance is allowed


def test_t3_unit_mismatch_acceptance_case():
    # reviewer probe P1
    assert _refused(_replace(MG, "fuel_cost", expression="diesel_l + diesel_price")) == "STRUCTURE_UNIT MINI_GRID/fuel_cost"
    assert _refused(_replace(MG, "fuel_cost", unit=L)) == "STRUCTURE_UNIT MINI_GRID/fuel_cost"


def test_t3_category():
    # acceptance case: the home removed from unmapped_kwh
    assert _refused(_replace(MG, "unmapped_kwh", home=None)) == "STRUCTURE_CATEGORY MINI_GRID/unmapped_kwh"
    assert _refused(_replace(MG, "om", home=Home("OTHER", "O1"))) == "STRUCTURE_CATEGORY MINI_GRID/om"
    assert _refused(_replace(MG, "om", home=Home("CALENDAR", None))) == "STRUCTURE_CATEGORY MINI_GRID/om"
    calendar_node = _replace(MG, "asset_days_total", home=Home("CALENDAR", None))
    assert _refused(calendar_node) == "STRUCTURE_CATEGORY MINI_GRID/asset_days_total"
    assert _refused(_replace(MG, "period_days", home=Home("OPTIMIZE_COST", "O2"))) == "STRUCTURE_CATEGORY MINI_GRID/period_days"
    assert _refused(_replace(MG, "om", home=Home("ABOVE", None))) == "STRUCTURE_CATEGORY MINI_GRID/om"


def test_t3_objective():
    assert _refused(_replace(MG, "collected", home=Home("OPTIMIZE_COST", "G3"))) == "STRUCTURE_OBJECTIVE MINI_GRID/collected"
    assert _refused(_replace(MG, "collected", home=Home("OPTIMIZE_COST", None))) == "STRUCTURE_OBJECTIVE MINI_GRID/collected"
    assert _refused(_replace(MG, "collected", home=Home("OPTIMIZE_COST", "O0"))) == "STRUCTURE_OBJECTIVE MINI_GRID/collected"
    assert _refused(_replace(MG, "collected", home=Home("OPTIMIZE_COST", "O10"))) == "STRUCTURE_OBJECTIVE MINI_GRID/collected"
    assert _refused(_replace(MG, "contribution", home=Home("ABOVE", "A1"))) == "STRUCTURE_OBJECTIVE MINI_GRID/contribution"
    assert _refused(_replace(MG, "period_days", home=Home("CALENDAR", "O1"))) == "STRUCTURE_OBJECTIVE MINI_GRID/period_days"


def test_t3_money_home():
    # the spec's example and the design's acceptance case (liability under Protect)
    assert _refused(_replace(MG, "collected", home=Home("PROTECT_ASSET", "P1"))) == "STRUCTURE_MONEY_HOME MINI_GRID/collected"
    assert _refused(_replace(MG, "liability", home=Home("PROTECT_ASSET", "P1"))) == "STRUCTURE_MONEY_HOME MINI_GRID/liability"
    assert _refused(_replace(MG, "om", home=Home("ASSURE_PERFORMANCE", "A1"))) == "STRUCTURE_MONEY_HOME MINI_GRID/om"
    # a money row homed CALENDAR is refused too (by CATEGORY, which runs first)
    assert _refused(_replace(MG, "contribution", home=Home("CALENDAR", None))) == "STRUCTURE_CATEGORY MINI_GRID/contribution"


def test_t3_code_major_order():
    # MONEY_HOME on an early row and UNIT on a later row: UNIT's code runs first.
    reg = _replace(MG, "tariff", home=Home("PROTECT_ASSET", "P1"))
    reg = _replace(reg, "contribution", unit=KWH)
    assert _refused(reg) == "STRUCTURE_UNIT MINI_GRID/contribution"


def test_t3_node_units_composed_from_declared_child_units():
    # A wrong declared unit on fuel_cost blames fuel_cost only, not cost_to_serve (R9).
    reg = _replace(MG, "fuel_cost", unit=L)
    assert _refused(reg) == "STRUCTURE_UNIT MINI_GRID/fuel_cost"


def test_t3_error_fields():
    with pytest.raises(StructureError) as caught:
        check(_replace(MG, "collected", home=Home("PROTECT_ASSET", "P1")))
    error = caught.value
    assert (error.code, error.structure_key, error.factor_id) == ("STRUCTURE_MONEY_HOME", "MINI_GRID", "collected")
    assert not isinstance(ExpressionError("x"), StructureError)


# ---------------------------------------------------------------- T4 start-up


def test_t4_create_app_refuses_a_bad_registry(monkeypatch):
    from assetops_backend.main import create_app

    bad = _replace(MG, "collected", home=Home("PROTECT_ASSET", "P1"))
    monkeypatch.setattr(registry_module, "REGISTRIES", {"MINI_GRID": bad})
    with pytest.raises(ConfigurationError, match="STRUCTURE_MONEY_HOME MINI_GRID/collected") as caught:
        create_app()
    assert isinstance(caught.value.__cause__, StructureError)


def test_t4_create_app_starts_with_the_real_registry():
    from assetops_backend.main import create_app

    from route_inventory import served_paths

    from assetops_backend.main import app as module_app

    app = create_app()
    assert "/api/health" in served_paths(app)
    assert served_paths(app) == served_paths(module_app)  # existing routes unchanged


# ---------------------------------------------------------------- T5 expressions


@pytest.mark.parametrize(
    "text",
    [
        "a.b",
        "a[0]",
        "a ** 2",
        "min(a, b=1)",
        "foo(a)",
        "'x'",
        "b'x'",
        "1e3",
        "0x10",
        "1_000",
        "1.",
        "True",
        "None",
        "1j",
        "ceil(a, b)",
        "floor()",
        "min(a)",
        "max(*a)",
        "a < b",
        "a and b",
        "a if b else c",
        "+a",
        "a % b",
        "a // b",
        "(a, b)",
        "",
        "a +",
    ],
)
def test_t5_refused_forms(text):
    with pytest.raises(ExpressionError):
        parse(text)


def test_t5_numeric_literals_are_decimal_from_source_text():
    value = parse("1.5")
    assert value == Num(Decimal("1.5"))
    assert type(value.value) is Decimal and str(value.value) == "1.5"
    assert parse("0.1").value != 0.1  # the float 0.1 is not the decimal 0.1
    assert parse("-1") == Neg(Num(Decimal("1")))


def test_t5_expr_shapes():
    assert parse("min(1, floor(a / max(b, 1)))") == Call(
        "min",
        (Num(Decimal("1")), Call("floor", (Bin("/", Ref("a"), Call("max", (Ref("b"), Num(Decimal("1"))))),))),
    )
    assert parse("a - b * c") == Bin("-", Ref("a"), Bin("*", Ref("b"), Ref("c")))
