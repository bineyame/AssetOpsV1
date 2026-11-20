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
    assert ORIGIN_ORDER == ("observed-financial", "field-integrated", "bench-tested", "source-emulated",
                            "demo-simulated")
    assert ORIGIN_ORDER == PROVENANCE_ORDER and set(ORIGIN_ORDER) == set(PROVENANCES)
    assert weakest_origin(()) is None


@pytest.mark.parametrize("om, staff, union, weakest", [
    ("source-emulated", "observed-financial", ("observed-financial", "source-emulated"), "source-emulated"),
    ("demo-simulated", "source-emulated", ("source-emulated", "demo-simulated"), "demo-simulated"),
    ("field-integrated", "observed-financial", ("observed-financial", "field-integrated"), "field-integrated"),
])
def test_s6_origins_union_in_origin_order(om, staff, union, weakest):
    leaves = pack_leaves("Kobo")
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
    assert MG.version == 3
    stated = {r.factor_id: r.stated_by for r in MG.rows if r.stated_by is not None}
    assert stated == {
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
# The D-4B.17 rate plant (a copy of `revenue` with `tariff`'s unit MONEY / KWH) is stopped: mid-build question Q1.


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
        return LeafValue(Decimal("1475.00"), "RECORDED", ("commercial:kobo-fuel",), None, None, "USD",
                         ("source-emulated",))


def test_s9_the_read_asks_each_stated_node_once():
    leaves = pack_leaves("Kobo")
    fake = _Stated()
    result = StructureRead(_Leaves(leaves), stated=fake).site(KOBO, "2026-10")
    assert tuple(fake.asked) == ("revenue", "fuel_cost")
    assert result.values["revenue"].value == Decimal("3458.00") and result.values["revenue"].stated is True
    assert result.values["fuel_cost"].value == Decimal("1475.00") and result.values["fuel_cost"].stated is True


def test_s9_without_a_stated_source_the_read_is_3b3s():
    leaves = pack_leaves("Kobo")
    fake = _Stated()
    result = StructureRead(_Leaves(leaves)).site(KOBO, "2026-10")
    assert fake.asked == []
    assert result == SiteStructure("KOBO-001", "2026-10", "MINI_GRID", 3, evaluate(MG, leaves))
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
