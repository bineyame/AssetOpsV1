"""4b1: the stated-node seam (spec §2.7, S1-S10; D-4B.1, D-4B.2, D-4B.10, D-4B.11, D-4B.16, D-4B.17). No database.

Leaves are 3B3 T1's builder for the pack's actual side (`test_3b3_structure_evaluate.pack_leaves`, imported, never
edited), then changed as each test states. Expected values are the spec's literals (W2).
Run with `DATABASE_URL` and `ASSETOPS_TEST_DATABASE_URL` unset.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from assetops_backend.commercial import composition as commercial_composition
from assetops_backend.commercial.months import PROVENANCE_ORDER, CommercialMonths
from assetops_backend.structure.check import CODES, check
from assetops_backend.structure.evaluate import (
    ORIGIN_ORDER,
    ORIGIN_UNKNOWN,
    Coverage,
    LeafValue,
    Missing,
    SiteStructure,
    compose,
    evaluate,
    weakest_origin,
)
from assetops_backend.structure.read import StructureRead
from assetops_backend.structure.registry import FilledBy
from assetops_contracts.canonical.records_v1 import PROVENANCES
from assetops_backend.structure.registry import Registry
from test_3b3_structure_evaluate import KOBO, MG, _absent, _plant, _raises, pack_leaves, site_structure

CENT = Decimal("0.01")
CHARGE_WORDS = "Billing export: the month's charges"
FUEL_WORDS = "Fuel invoices for the month"


def _stated_revenue(value: str = "3458.00") -> LeafValue:
    return LeafValue(Decimal(value), "RECORDED", ("commercial:kobo-vending",), None, None, "USD", ("source-emulated",))


def _absent_stated(cause: str, note: str | None = None) -> LeafValue:
    return LeafValue(None, "NOT_AVAILABLE", (), None,
                     Missing("CHARGE", "COMMERCIAL_RECORD", cause, None, (), CHARGE_WORDS, None, note), None)


def _kobo_without_kwh() -> dict[str, LeafValue]:
    leaves = pack_leaves("Kobo")
    leaves["delivered_kwh"] = _absent("delivered_kwh", "NOT_CALCULATED_YET")  # 3B3 §3's HELD form
    return leaves


# ---------------------------------------------------------------- S1 to S4: the table of §2.3


def test_s1_stated_governs():
    values = evaluate(MG, _kobo_without_kwh(), stated={"revenue": _stated_revenue()})
    revenue, contribution = values["revenue"], values["contribution"]
    assert revenue.value == Decimal("3458.00") and revenue.evidence == "RECORDED"
    assert revenue.stated is True and revenue.computed is None
    assert revenue.missing_leaves == () and revenue.detail_missing == ("delivered_kwh",)
    assert revenue.origins == ("source-emulated",) and revenue.sources == ("commercial:kobo-vending",)
    assert contribution.value == Decimal("883.00")
    assert contribution.detail_missing == ("delivered_kwh",) and contribution.missing_leaves == ()
    assert contribution.origins == ("source-emulated",)


def test_s2_both_known():
    values = evaluate(MG, pack_leaves("Kobo"), stated={"revenue": _stated_revenue("3500.00")})
    assert values["revenue"].value == Decimal("3500.00") and values["revenue"].stated is True
    assert values["revenue"].computed.quantize(CENT) == Decimal("3458.00")
    assert values["revenue"].detail_missing == ()
    assert values["contribution"].value == Decimal("925.00")


def test_s3_stated_absent_computed_known():
    values = evaluate(MG, pack_leaves("Kobo"), stated={"revenue": _absent_stated("NOT_CONNECTED")})
    revenue = values["revenue"]
    assert revenue.value.quantize(CENT) == Decimal("3458.00")
    assert revenue.stated is False and revenue.missing is None and revenue.computed is None
    assert values["contribution"].value.quantize(CENT) == Decimal("883.00")


def test_s4_both_absent():
    values = evaluate(MG, _kobo_without_kwh(), stated={"revenue": _absent_stated("NOT_CONNECTED")})
    revenue = values["revenue"]
    assert revenue.value is None and revenue.evidence == "NOT_AVAILABLE"
    assert revenue.missing.record_kind == "CHARGE" and revenue.missing.record_words == CHARGE_WORDS
    assert revenue.missing.blocks == ("collected", "contribution")
    assert revenue.missing_leaves == ("delivered_kwh", "revenue")
    assert revenue.stated is False and revenue.computed is None and revenue.detail_missing == ("delivered_kwh",)
    assert {"delivered_kwh", "revenue"} <= set(values["contribution"].missing_leaves)
    assert values["contribution"].value is None
    # Row 4 takes sources, origins and coverage from the expression, not from the (absent) stated value (F2c).
    expression_only = evaluate(MG, _kobo_without_kwh())["revenue"]
    stated_with_provenance = dataclasses.replace(
        _absent_stated("NOT_CONNECTED"), sources=("commercial:x",), origins=("demo-simulated",),
        coverage=Coverage(1, 31))
    planted = evaluate(MG, _kobo_without_kwh(), stated={"revenue": stated_with_provenance})["revenue"]
    assert expression_only.sources and expression_only.origins == ("source-emulated",)
    assert (revenue.sources, revenue.origins, revenue.coverage) == (
        expression_only.sources, expression_only.origins, expression_only.coverage)
    assert (planted.sources, planted.origins, planted.coverage) == (
        expression_only.sources, expression_only.origins, expression_only.coverage)
    # Row 3: the computed value, with the expression's provenance (F2c).
    row3 = evaluate(MG, pack_leaves("Kobo"), stated={"revenue": stated_with_provenance})["revenue"]
    ref = evaluate(MG, pack_leaves("Kobo"))["revenue"]
    assert (row3.sources, row3.origins, row3.coverage) == (ref.sources, ref.origins, ref.coverage)


def test_s1_stated_carried_as_target_stays_assumed_and_keeps_its_missing():
    """F2a/F2b: a stated value carried as TARGET is estimated, assumed, and keeps its Missing with `blocks`."""
    target = LeafValue(Decimal("3000.00"), "ESTIMATED", ("budget:b1",), None,
                       Missing("CHARGE", "COMMERCIAL_RECORD", "NOT_CONNECTED", "TARGET", (), CHARGE_WORDS,
                               "Budget line", None), "USD", ("source-emulated",))
    revenue = evaluate(MG, pack_leaves("Kobo"), stated={"revenue": target})["revenue"]
    assert revenue.value == Decimal("3000.00") and revenue.evidence == "ESTIMATED" and revenue.stated is True
    assert revenue.assumed_leaves == ("revenue",)
    assert revenue.missing is not None and revenue.missing.carried_as == "TARGET"
    assert revenue.missing.blocks == ("collected", "contribution")


# ---------------------------------------------------------------- S5: refusals


@pytest.mark.parametrize("key", ["contribution", "om", "nope"])
def test_s5_stated_key_must_be_a_stated_row(key):
    _raises("STRUCTURE_STATED", evaluate, MG, pack_leaves("Kobo"), {key: _stated_revenue()})


@pytest.mark.parametrize("code, value", [
    ("STRUCTURE_MISSING", LeafValue(None, "NOT_AVAILABLE", (), None, None, None)),
    ("STRUCTURE_CURRENCY", LeafValue(Decimal("3458.00"), "RECORDED", ("c",), None, None, None)),
    ("STRUCTURE_EVIDENCE", LeafValue(Decimal("0"), "NEUTRAL", ("c",), None, None, None)),
    ("STRUCTURE_ORIGIN", dataclasses.replace(_stated_revenue(), origins=("emulated",))),
    ("STRUCTURE_ORIGIN", dataclasses.replace(_stated_revenue(), origins=("source-emulated", "observed-financial"))),
    ("STRUCTURE_ORIGIN", dataclasses.replace(_stated_revenue(), origins=("demo-simulated", "source-emulated"))),
    ("STRUCTURE_ORIGIN", dataclasses.replace(_stated_revenue(), origins=("source-emulated", "source-emulated"))),
])
def test_s5_stated_value_checks(code, value):
    error = _raises(code, evaluate, MG, pack_leaves("Kobo"), {"revenue": value})
    assert error.factor_id == "revenue"


def test_s5_a_leaf_origin_is_checked_too():
    leaves = pack_leaves("Kobo")
    leaves["om"] = dataclasses.replace(leaves["om"], origins=("emulated",))
    assert _raises("STRUCTURE_ORIGIN", evaluate, MG, leaves).factor_id == "om"


# ---------------------------------------------------------------- S6: origins


def test_s6_origin_order_is_the_provenance_order():
    assert ORIGIN_ORDER[-1] == ORIGIN_UNKNOWN == "unknown"
    assert ORIGIN_ORDER[:-1] == PROVENANCE_ORDER and set(ORIGIN_ORDER[:-1]) == set(PROVENANCES)
    assert "unknown" not in PROVENANCES
    assert weakest_origin(()) is None


@pytest.mark.parametrize("om, staff, base, union, weakest", [
    ("source-emulated", "observed-financial", "source-emulated", ("observed-financial", "source-emulated"),
     "source-emulated"),
    ("demo-simulated", "source-emulated", "source-emulated", ("source-emulated", "demo-simulated"),
     "demo-simulated"),
    ("field-integrated", "observed-financial", "observed-financial", ("observed-financial", "field-integrated"),
     "field-integrated"),
])
def test_s6_origins_union_in_origin_order(om, staff, base, union, weakest):
    leaves = pack_leaves("Kobo", origins=(base,))
    leaves["om"] = dataclasses.replace(leaves["om"], origins=(om,))
    leaves["staff"] = dataclasses.replace(leaves["staff"], origins=(staff,))
    cost_to_serve = evaluate(MG, leaves)["cost_to_serve"]
    assert cost_to_serve.origins == union
    assert weakest_origin(cost_to_serve.origins) == weakest


def test_s6_neutral_identity_drops_the_other_operand():
    leaves = pack_leaves("Kobo")
    assert leaves["battery_throughput_kwh"].evidence == "NEUTRAL"
    leaves["wear_rate"] = _absent("wear_rate")
    assert leaves["wear_rate"].origins == ()
    wear = evaluate(MG, leaves)["battery_wear"]
    assert wear.origins == () and wear.detail_missing == ()
    leaves["wear_rate"] = dataclasses.replace(pack_leaves("Kobo")["wear_rate"], origins=("demo-simulated",))
    wear = evaluate(MG, leaves)["battery_wear"]
    assert wear.origins == () and wear.detail_missing == ()


# ---------------------------------------------------------------- S11: a valued part names its origin (D-4B.18)


def _no_origin() -> LeafValue:
    return LeafValue(Decimal("600.00"), "MEASURED", ("x",), None, None, "USD")


@pytest.mark.parametrize("factor, leaf", [
    ("om", _no_origin()),
    ("outstanding", LeafValue(Decimal("600.00"), "DERIVED", ("x",), None, None, "USD")),
])
def test_s11a_a_valued_leaf_without_origins_is_refused(factor, leaf):
    leaves = pack_leaves("Kobo")
    leaves[factor] = leaf
    assert _raises("STRUCTURE_ORIGIN", evaluate, MG, leaves).factor_id == factor


def _valued_cases():
    """R2-1: every valued leaf row that is not CALENDAR, money and non-money, in every registry, plus every stated node;
    read from the registry so a new row is covered without a hand list."""
    from assetops_backend.structure.registry import REGISTRIES
    cases = []
    for key, reg in REGISTRIES.items():
        for row in reg.rows:
            if row.is_leaf and not (row.filled_by is not None and row.filled_by.family == "CALENDAR"):
                cases.append(pytest.param(key, row.factor_id, False, id=f"{key}-leaf-{row.factor_id}"))
            if not row.is_leaf and row.stated_by is not None:
                cases.append(pytest.param(key, row.factor_id, True, id=f"{key}-stated-{row.factor_id}"))
    return cases


@pytest.mark.parametrize("key, factor_id, stated", _valued_cases())
def test_s11a_every_valued_part_with_empty_origins_is_refused(key, factor_id, stated):
    from assetops_backend.structure.evaluate import _check_leaf, _check_stated
    from assetops_backend.structure.registry import REGISTRIES
    reg = REGISTRIES[key]
    row = reg.row(factor_id)
    currency = "USD" if row.unit.has_money_dimension else None
    leaf = LeafValue(Decimal("1.00"), "MEASURED", ("x",), None, None, currency, ())
    err = _raises("STRUCTURE_ORIGIN", _check_stated, reg, {factor_id: leaf}) if stated else _raises(
        "STRUCTURE_ORIGIN", _check_leaf, reg, factor_id, leaf)
    assert err.factor_id == factor_id


def test_s11a_the_registry_yields_money_and_non_money_leaves():
    from assetops_backend.structure.registry import REGISTRIES
    rows = [REGISTRIES[p.values[0]].row(p.values[1]) for p in _valued_cases() if not p.values[2]]
    assert any(r.unit.has_money_dimension for r in rows) and any(not r.unit.has_money_dimension for r in rows)
    assert any(p.values[2] for p in _valued_cases())


def test_s11a_a_valued_stated_value_without_origins_is_refused():
    value = LeafValue(Decimal("3458.00"), "RECORDED", ("commercial:kobo-vending",), None, None, "USD")
    assert _raises("STRUCTURE_ORIGIN", evaluate, MG, pack_leaves("Kobo"), {"revenue": value}).factor_id == "revenue"


def test_s11b_unknown_ranks_weakest():
    leaves = pack_leaves("Kobo")
    leaves["om"] = dataclasses.replace(leaves["om"], origins=("unknown",))
    leaves["staff"] = dataclasses.replace(leaves["staff"], origins=("observed-financial",))
    cts = evaluate(MG, leaves)["cost_to_serve"]
    assert cts.origins == ("observed-financial", "source-emulated", "unknown")
    assert weakest_origin(cts.origins) == "unknown"
    leaves["om"] = dataclasses.replace(leaves["om"], origins=("demo-simulated",))
    leaves["staff"] = dataclasses.replace(leaves["staff"], origins=("unknown",))
    assert weakest_origin(evaluate(MG, leaves)["cost_to_serve"].origins) == "unknown"


def test_s11c_calendar_and_neutral_leaves_carry_no_origin():
    leaves = pack_leaves("Kobo")
    leaves["period_days"] = LeafValue(Decimal(31), "DERIVED", ("calendar",), None, None, None)
    neutral = [k for k, v in leaves.items() if v.evidence == "NEUTRAL"]
    assert neutral and all(leaves[k].origins == () for k in neutral)
    values = evaluate(MG, leaves)
    assert values["asset_days_total"].origins == ("source-emulated",)


# ---------------------------------------------------------------- S7: compose


def test_s7_compose_carries_detail_missing_and_origins():
    kisiwa = pack_leaves("Kisiwa")
    kisiwa["om"] = dataclasses.replace(kisiwa["om"], origins=("observed-financial",))
    per_site = {
        "Kobo": SiteStructure("Kobo", "2026-10", MG.structure_key, MG.version,
                              evaluate(MG, _kobo_without_kwh(), stated={"revenue": _stated_revenue()})),
        "Kisiwa": site_structure("Kisiwa", kisiwa),
    }
    contribution = compose(MG, per_site).values["contribution"].value
    assert contribution.detail_missing == ("Kobo:delivered_kwh",)
    assert contribution.origins == ("observed-financial", "source-emulated")
    assert contribution.stated is False and contribution.computed is None


# ---------------------------------------------------------------- S8: registry


def test_s8_registry_version_and_stated_rows():
    assert MG.version == 4  # 4a (D-4A.1)
    stated = {r.factor_id: r.stated_by for r in MG.rows if r.stated_by is not None}
    assert stated == {
        "metered_kwh": FilledBy("COMMERCIAL_RECORD", "CUSTOMER_METER_READ", "Customer meter reads for the month"),
        "billed_kwh": FilledBy("COMMERCIAL_RECORD", "CHARGE (USAGE kWh)", "Billing export: the month's billed kWh"),
        "revenue": FilledBy("COMMERCIAL_RECORD", "CHARGE", "Billing export: the month's charges"),
        "fuel_cost": FilledBy("COMMERCIAL_RECORD", "EXPENSE (FUEL)", "Fuel invoices for the month"),
    }
    check(MG)
    assert CODES.index("STRUCTURE_STATED") == CODES.index("STRUCTURE_COMPOSES") + 1


@pytest.mark.parametrize("target, changes", [
    ("om", {"stated_by": FilledBy("COMMERCIAL_RECORD", "EXPENSE (OM)", None)}),  # a leaf
    ("diesel_l", {"stated_by": FilledBy("COMMERCIAL_RECORD", "EXPENSE (FUEL)", None)}),  # unit L, not money
    ("contribution", {"stated_by": FilledBy("DECLARED", "CHARGE", None)}),  # wrong family
    ("revenue", {"composes": "NONE"}),  # a stated node that is not summed
])
def test_s8_structure_stated(target, changes):
    error = _raises("STRUCTURE_STATED", check, _plant(MG, target, **changes))
    assert error.factor_id == target


def _with_stated_copy(factor_id: str, expression: str, unit, stated: bool) -> Registry:
    """Mid-build Q1: append a copy of `revenue` with a new ID, expression and unit; `stated_by` kept or dropped."""
    revenue = MG.row("revenue")
    row = dataclasses.replace(revenue, factor_id=factor_id, expression=expression, unit=unit,
                              stated_by=revenue.stated_by if stated else None)
    return dataclasses.replace(MG, rows=MG.rows + (row,))


_NOT_EXACTLY_MONEY = [
    ("s8_money_sq", "tariff * delivered_kwh * om", MG.row("om").unit * MG.row("om").unit),
    ("s8_money_kwh", "om * delivered_kwh", MG.row("om").unit * MG.row("delivered_kwh").unit),
]


@pytest.mark.parametrize("factor_id, expression, unit", _NOT_EXACTLY_MONEY)
def test_s8_a_stated_node_must_be_exactly_money(factor_id, expression, unit):
    assert not unit.is_money and any(d == "MONEY" and e != 0 for d, e in unit.exponents)
    error = _raises("STRUCTURE_STATED", check, _with_stated_copy(factor_id, expression, unit, stated=True))
    assert error.factor_id == factor_id


@pytest.mark.parametrize("factor_id, expression, unit", _NOT_EXACTLY_MONEY)
def test_s8_the_control_without_stated_by_is_not_refused_at_stated(factor_id, expression, unit):
    try:
        check(_with_stated_copy(factor_id, expression, unit, stated=False))
    except Exception as error:  # a later code is allowed; STRUCTURE_STATED or an earlier one is not
        code = getattr(error, "code", None)
        assert code in CODES and CODES.index(code) > CODES.index("STRUCTURE_STATED"), str(error)


# ---------------------------------------------------------------- S9: the read


class _Leaves:
    def __init__(self, leaves: dict[str, LeafValue]) -> None:
        self._leaves = leaves

    def leaf(self, ctx, factor_id: str) -> LeafValue:
        return self._leaves[factor_id]


class _Stated:
    def __init__(self) -> None:
        self.asked: list[str] = []

    def stated(self, ctx, factor_id: str) -> LeafValue:
        self.asked.append(factor_id)
        if factor_id == "revenue":
            return _stated_revenue()
        if factor_id in ("metered_kwh", "billed_kwh"):  # 4a: nothing to read, the expression stands
            return LeafValue(None, "NOT_AVAILABLE", (), None,
                             Missing("X", "COMMERCIAL_RECORD", "NOT_CONNECTED", None, (), None, None, None), None)
        return LeafValue(Decimal("1475.00"), "RECORDED", ("commercial:kobo-fuel",), None, None, "USD",
                         ("source-emulated",))


def test_s9_the_read_asks_each_stated_node_once():
    leaves = pack_leaves("Kobo")
    fake = _Stated()
    result = StructureRead(_Leaves(leaves), stated=fake).site(KOBO, "2026-10")
    assert tuple(fake.asked) == ("metered_kwh", "billed_kwh", "revenue", "fuel_cost")  # 4a: two stated kWh nodes
    assert result.values["revenue"].value == Decimal("3458.00") and result.values["revenue"].stated is True
    assert result.values["fuel_cost"].value == Decimal("1475.00") and result.values["fuel_cost"].stated is True


def test_s9_without_a_stated_source_the_read_is_3b3s():
    leaves = pack_leaves("Kobo")
    fake = _Stated()
    result = StructureRead(_Leaves(leaves)).site(KOBO, "2026-10")
    assert fake.asked == []
    assert result == SiteStructure("KOBO-001", "2026-10", "MINI_GRID", 4, evaluate(MG, leaves))  # 4a: v4
    assert not any(v.stated for v in result.values.values())


# ---------------------------------------------------------------- S10: a refused stated record blocks (D-4B.16)


def test_s10_a_refused_stated_record_blocks():
    refused = _absent_stated("NOT_CALCULATED_YET", "CURRENCY_MISMATCH:KES,USD")
    values = evaluate(MG, pack_leaves("Kobo"), stated={"revenue": refused})
    revenue = values["revenue"]
    assert revenue.value is None and revenue.computed is None and revenue.stated is False
    assert revenue.missing.cause == "NOT_CALCULATED_YET" and revenue.missing.note == "CURRENCY_MISMATCH:KES,USD"
    assert revenue.missing_leaves == ("revenue",)
    assert values["contribution"].value is None


# ---------------------------------------------------------------- build_commercial_reads (spec §2.6)


def test_build_commercial_reads_shares_one_store_and_disposes_it(monkeypatch):
    built = []

    class _Store:
        disposed = 0

        def __init__(self, url):
            built.append(self)

        def dispose(self):
            self.disposed += 1

    monkeypatch.setattr(commercial_composition, "PostgresCommercialStore", _Store)
    reads = commercial_composition.build_commercial_reads("postgresql://x/y_test")
    assert len(built) == 1 and reads.store is built[0]
    assert isinstance(reads.months, CommercialMonths) and reads.months._store is built[0]
    reads.dispose()
    assert built[0].disposed == 1
