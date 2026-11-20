"""3B3: the structure evaluator and the leaf sources (spec §6, T1-T7). No database.

T1-T3 are the independent check (W2): their expected values are the pack's `derived-values.json` and
`missing-records.json` (written by the pack's own evaluator), the leaf set and sources come from the pack manifest,
and T3's `SUM` list is this file's own literal. Nothing expected is read from the code under test.
Run with `DATABASE_URL` and `ASSETOPS_TEST_DATABASE_URL` unset.
"""

from __future__ import annotations

import dataclasses
import decimal
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
import yaml

from assetops_backend.chain.ports import SiteRef
from assetops_backend.financials.fuel_cost import PriceSelection
from assetops_backend.structure import expressions
from assetops_backend.structure import registry as registry_module
from assetops_backend.structure.check import StructureError, check
from assetops_backend.structure.evaluate import (
    LeafValue,
    Missing,
    blocks_of,
    compose,
    evaluate,
)
from assetops_backend.structure.read import StructureRead
from assetops_backend.structure.registry import REGISTRIES, Registry, Tolerance
from assetops_backend.structure.sources import SOURCE_STATE, ProductLeafSource, ReadContext

PACK = Path(__file__).resolve().parents[2] / "Docs/demo-sprint/product-direction-layer4"
DERIVED = json.loads((PACK / "derived-values.json").read_text(encoding="utf-8"))
MISSING = json.loads((PACK / "missing-records.json").read_text(encoding="utf-8"))
_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
MANIFEST = yaml.load((PACK / "demo-site-scenario-manifest.yaml").read_text(encoding="utf-8"), Loader=_LOADER)

MG = REGISTRIES["MINI_GRID"]
SITES = ("Kobo", "Kisiwa", "Mto")
CENT = Decimal("0.01")
USD = "USD"
LEAF_SOURCES = MANIFEST["empty_states"]["leaf_sources"]["MINI_GRID"]
LEAVES = tuple(MANIFEST["factor_map"]["MINI_GRID"])
OPTION_ONLY = tuple(f for f in LEAVES if LEAF_SOURCES[f]["absent"] == "OPTION_ONLY")
#: The test's own list of leaves whose unit carries money (W2).
MONEY_LEAVES = ("tariff", "productive_tariff", "in_transit", "outstanding", "diesel_price", "wear_rate", "om",
                "staff", "collection_cost", "liability")

#: T3's own copy of spec §2.4's lists (W2).
SUM = (
    "delivered_kwh", "technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh",
    "productive_kwh", "in_transit", "outstanding", "necessary_l", "candidate_l", "unexplained_l", "extra_l",
    "battery_throughput_kwh", "om", "staff", "collection_cost", "reduced_days", "major_assets",
    "unserved_critical_kwh", "customer_hours_interrupted", "field_visits", "liability", "dawn_days_below",
    "metered_kwh", "billed_kwh", "revenue", "collected", "diesel_l", "fuel_cost", "battery_wear", "cost_to_serve",
    "contribution", "obligation_hours_without_redundancy", "obligation_hours_without_backup",
    "replayed_dawn_days_below_safeguard", "asset_days_out_of_service", "asset_days_total", "asset_days_available",
)
NONE = ("tariff", "productive_tariff", "diesel_price", "wear_rate", "hours_per_day", "standby_kw", "lost_unit_kw",
        "shortfall_backed", "period_days")

#: T6's own copy of spec §3's table (W2).
STATE_TABLE = {
    "PROVIDED": {"period_days", "unserved_critical_kwh"},
    "ASSUMED": {"productive_tariff", "diesel_price"},
    "HELD_NOT_CALCULATED": {"delivered_kwh", "necessary_l", "candidate_l", "unexplained_l", "reduced_days",
                            "hours_per_day", "customer_hours_interrupted", "field_visits", "dawn_days_below"},
    "NOT_CONNECTED": {"productive_kwh", "technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh",
                      "unmapped_kwh", "tariff", "in_transit", "outstanding", "wear_rate", "om", "staff",
                      "major_assets", "liability", "standby_kw", "lost_unit_kw"},
    "OPTION_ONLY": {"extra_l", "battery_throughput_kwh", "collection_cost"},
}


def _cent(x) -> Decimal:
    return Decimal(str(x)).quantize(CENT)


def _pack_decimal(site: str, side: str, leaf: str) -> Decimal:
    raw = DERIVED["sites"][f"lakeside-power/{site}"][side]["nodes"][leaf]
    value = Decimal(str(raw))
    assert value == value.quantize(CENT), f"{site} {side} {leaf} is not a cent amount: {raw!r}"  # R12
    return value


def _entries(site: str, side: str) -> list[dict]:
    return [e for e in MISSING["sites"][f"lakeside-power/{site}"] if e["side"] == side]


def _missing_of(entry: dict, carried_as: str) -> Missing:
    return Missing(entry["record_kind"], entry["source_family"], entry["cause"], carried_as, (),
                   entry.get("record_words"), entry.get("assumption"), entry.get("note"))


def pack_leaves(site: str, side: str = "actual", currency: str = USD) -> dict[str, LeafValue]:
    """The pack's leaves of one side: actual MEASURED, plan DECLARED, option-only NEUTRAL; the pack's carried and
    assumed entries ESTIMATED."""
    base = "MEASURED" if side == "actual" else "DECLARED"
    out = {}
    for leaf in LEAVES:
        value = _pack_decimal(site, side, leaf)
        if leaf in OPTION_ONLY:
            out[leaf] = LeafValue(value, "NEUTRAL", ("pack",), None, None, None)
        else:
            out[leaf] = LeafValue(value, base, (f"pack:{side}",), None, None,
                                  currency if leaf in MONEY_LEAVES else None)
    for entry in _entries(site, side):
        if side == "actual" and "leaf" in entry:  # R11: `right` and `stage` entries are not leaves
            leaf = entry["leaf"]
            out[leaf] = dataclasses.replace(out[leaf], evidence="ESTIMATED",
                                            missing=_missing_of(entry, entry["carried_as"]))
        if side == "plan" and entry["carried_as"] == "ASSUMPTION":
            for leaf in entry["leaves"]:
                out[leaf] = dataclasses.replace(out[leaf], evidence="ESTIMATED",
                                                missing=_missing_of(entry, "ASSUMPTION"))
    return out


def _absent(leaf: str, cause: str = "NOT_RECEIVED") -> LeafValue:
    src = LEAF_SOURCES[leaf]
    return LeafValue(None, "NOT_AVAILABLE", (), None,
                     Missing(src["kind"], src["family"], cause, None, (), src.get("words"), None), None)


def _plant(reg: Registry, target: str, **changes) -> Registry:
    rows = tuple(dataclasses.replace(r, **changes) if r.factor_id == target else r for r in reg.rows)
    assert repr(rows) != repr(reg.rows), f"plant did not touch {target}"  # repr: a float 0.0 equals Decimal 0
    return dataclasses.replace(reg, rows=rows)


def _raises(code: str, fn, *args) -> StructureError:
    with pytest.raises(StructureError) as caught:
        fn(*args)
    assert caught.value.code == code, str(caught.value)
    return caught.value


def site_structure(site: str, leaves: dict[str, LeafValue] | None = None):
    from assetops_backend.structure.evaluate import SiteStructure
    return SiteStructure(site, "2026-10", MG.structure_key, MG.version, evaluate(MG, leaves or pack_leaves(site)))


# ---------------------------------------------------------------- T1 actual-side parity


@pytest.mark.parametrize("site", SITES)
def test_t1_actual_side_equals_the_pack_to_the_cent(site):
    values = evaluate(MG, pack_leaves(site))
    expected = DERIVED["sites"][f"lakeside-power/{site}"]["actual"]["nodes"]
    assert set(expected) == set(values) and len(values) == 47
    for factor_id, x in expected.items():
        got = values[factor_id].value
        assert got is not None and got.quantize(CENT) == _cent(x), (site, factor_id, got, x)


@pytest.mark.parametrize("site", SITES)
def test_t1_actual_side_blocks_equal_the_pack(site):
    values = evaluate(MG, pack_leaves(site))
    leaf_entries = [e for e in _entries(site, "actual") if "leaf" in e]
    assert (site == "Kisiwa") == bool(leaf_entries)  # Kisiwa `om` is the pack's only actual-side leaf entry
    for entry in leaf_entries:
        fv = values[entry["leaf"]]
        assert fv.missing.blocks == tuple(entry["blocks"])
        assert fv.missing.carried_as == "TARGET" and fv.missing.note == entry["note"]
        assert fv.evidence == "ESTIMATED"
        for node in entry["blocks"]:
            assert values[node].evidence == "ESTIMATED" and entry["leaf"] in values[node].assumed_leaves


# ---------------------------------------------------------------- T2 plan side and assumptions


@pytest.mark.parametrize("site", SITES)
def test_t2_plan_side_equals_the_pack_and_assumptions_reach_every_ancestor(site):
    values = evaluate(MG, pack_leaves(site, "plan"))
    expected = DERIVED["sites"][f"lakeside-power/{site}"]["plan"]["nodes"]
    for factor_id, x in expected.items():
        assert values[factor_id].value.quantize(CENT) == _cent(x), (site, factor_id)
    groups = [e for e in _entries(site, "plan") if e["carried_as"] == "ASSUMPTION"]
    assert groups
    above: set[str] = set()
    for group in groups:
        assert blocks_of(MG, group["leaves"]) == tuple(group["blocks"])  # R11
        above |= set(group["blocks"])
        for node in group["blocks"]:
            fv = values[node]
            assert fv.evidence == "ESTIMATED", (site, node)
            assert fv.assumed_leaves and set(fv.assumed_leaves) <= set(group["leaves"])
        assert set(values["contribution"].assumed_leaves) == set(group["leaves"])
    for row in MG.rows:
        if not row.is_leaf and row.factor_id not in above:
            assert values[row.factor_id].evidence in ("DECLARED", "NEUTRAL"), (site, row.factor_id)
            assert values[row.factor_id].assumed_leaves == ()


def test_t2_probe_candidate_l_assumed_makes_fuel_cost_estimated():
    leaves = pack_leaves("Kobo", "plan")
    leaves = {f: (dataclasses.replace(v, evidence="DECLARED", missing=None) if v.evidence == "ESTIMATED" else v)
              for f, v in leaves.items()}
    entry = _entries("Kobo", "plan")[0]
    leaves["candidate_l"] = dataclasses.replace(leaves["candidate_l"], evidence="ESTIMATED",
                                                missing=_missing_of(entry, "ASSUMPTION"))
    values = evaluate(MG, leaves)
    for node in ("diesel_l", "fuel_cost", "cost_to_serve", "contribution"):
        assert values[node].evidence == "ESTIMATED" and values[node].assumed_leaves == ("candidate_l",)
    assert values["revenue"].evidence == "DECLARED"


# ---------------------------------------------------------------- T3 portfolio


def _sums(side: str = "actual") -> dict:
    return DERIVED["portfolio"]["lakeside-power"][side]["sums"]


def test_t3_sum_list_is_the_registry_flag():
    assert {r.factor_id for r in MG.rows if r.composes == "SUM"} == set(SUM)
    assert {r.factor_id for r in MG.rows if r.composes == "NONE"} == set(NONE)
    assert len(SUM) + len(NONE) == 47


def test_t3_composition_equals_the_pack_sums():
    comp = compose(MG, {s: site_structure(s) for s in SITES})
    assert comp.sites == SITES and dict(comp.sites_excluded) == {}
    assert set(comp.values) == set(SUM)
    for factor_id in SUM:
        pv = comp.values[factor_id]
        assert pv.included == SITES and dict(pv.excluded) == {}
        assert pv.value.value.quantize(CENT) == _cent(_sums()[factor_id]), factor_id
    assert set(comp.not_composed) == set(NONE)
    assert not set(NONE) & set(comp.values)
    assert comp.values["contribution"].value.currency == USD
    assert comp.values["contribution"].value.assumed_leaves == ("Kisiwa:om",)
    assert comp.values["contribution"].value.evidence == "ESTIMATED"


def test_t3_every_site_without_om_leaves_contribution_without_value_but_keeps_protect():
    per_site = {}
    for s in SITES:
        leaves = pack_leaves(s)
        leaves["om"] = _absent("om")
        per_site[s] = site_structure(s, leaves)
    comp = compose(MG, per_site)
    contribution = comp.values["contribution"]
    assert contribution.value.value is None and contribution.value.evidence == "NOT_AVAILABLE"
    assert contribution.included == ()
    assert set(contribution.excluded) == set(SITES)
    assert all("om" in leaves for leaves in contribution.excluded.values())
    assert contribution.value.missing_leaves == ("Kisiwa:om", "Kobo:om", "Mto:om")
    unserved = comp.values["unserved_critical_kwh"]
    assert unserved.included == SITES and unserved.value.value.quantize(CENT) == _cent(_sums()["unserved_critical_kwh"])
    assert comp.values["revenue"].included == SITES


def test_t3_one_site_without_om_is_excluded_by_name():
    per_site = {s: site_structure(s) for s in SITES}
    leaves = pack_leaves("Kisiwa")
    leaves["om"] = _absent("om")
    per_site["Kisiwa"] = site_structure("Kisiwa", leaves)
    contribution = compose(MG, per_site).values["contribution"]
    assert contribution.included == ("Kobo", "Mto")
    assert dict(contribution.excluded) == {"Kisiwa": ("om",)}
    want = sum((_pack_decimal(s, "actual", "contribution") for s in ("Kobo", "Mto")), Decimal(0))
    assert contribution.value.value.quantize(CENT) == want.quantize(CENT)


def test_t3_two_currencies_and_another_version():
    per_site = {s: site_structure(s) for s in ("Kobo", "Kisiwa")}
    per_site["Mto"] = site_structure("Mto", pack_leaves("Mto", currency="KES"))
    revenue = compose(MG, per_site).values["revenue"]
    assert revenue.value.value is None and revenue.value.missing.record_kind == "CURRENCY_MISMATCH:KES,USD"
    assert compose(MG, per_site).values["unserved_critical_kwh"].value.value is not None
    per_site["Mto"] = dataclasses.replace(per_site["Mto"], structure_version=1)
    error = _raises("STRUCTURE_COMPOSE", compose, MG, per_site)
    assert str(error) == "STRUCTURE_COMPOSE MINI_GRID/Mto"
    per_site["Mto"] = dataclasses.replace(per_site["Mto"], structure_version=MG.version, structure_key="COLD_CHAIN")
    _raises("STRUCTURE_COMPOSE", compose, MG, per_site)


def test_t3_empty_portfolio_is_never_zero():
    comp = compose(MG, {})
    assert all(pv.value.value is None and pv.included == () for pv in comp.values.values())


# ---------------------------------------------------------------- T4 unknown is never zero


def test_t4_om_missing_blocks_exactly_its_ancestors():
    leaves = pack_leaves("Kobo")
    leaves["om"] = _absent("om")
    values = evaluate(MG, leaves)
    pack_blocks = next(e["blocks"] for e in _entries("Kisiwa", "actual") if e.get("leaf") == "om")  # the pack's
    assert values["om"].missing.blocks == tuple(pack_blocks)
    for node in pack_blocks:
        assert values[node].value is None and values[node].evidence == "NOT_AVAILABLE"
        assert "om" in values[node].missing_leaves and values[node].missing is None
    for row in MG.rows:
        if row.factor_id not in pack_blocks and row.factor_id != "om":
            assert values[row.factor_id].value is not None, row.factor_id
            assert "om" not in values[row.factor_id].missing_leaves


# ---------------------------------------------------------------- T5 carried items and leaf-value checks


def _shortfall(expression: str, standby: str, lost: str):
    reg = _plant(MG, "shortfall_backed", expression=expression)
    leaves = pack_leaves("Kobo")
    leaves["standby_kw"] = dataclasses.replace(leaves["standby_kw"], value=Decimal(standby))
    leaves["lost_unit_kw"] = dataclasses.replace(leaves["lost_unit_kw"], value=Decimal(lost))
    return reg, evaluate(reg, leaves)


def test_t5_division_by_zero_has_no_value():
    reg, values = _shortfall("standby_kw / lost_unit_kw", "30", "0")
    fv = values["shortfall_backed"]
    assert fv.value is None and fv.evidence == "NOT_AVAILABLE"
    assert fv.missing == Missing("ZERO_DENOMINATOR:lost_unit_kw", "OBSERVER", "NOT_CALCULATED_YET", None,
                                 ("obligation_hours_without_backup",), None, None, None)
    assert values["obligation_hours_without_backup"].value is None
    _, values = _shortfall("standby_kw / max(lost_unit_kw, 0)", "30", "0")
    assert values["shortfall_backed"].missing.record_kind == "ZERO_DENOMINATOR:max(lost_unit_kw, 0)"


def test_t5_floor_and_ceil_are_mathematical():
    _, values = _shortfall("floor(standby_kw / lost_unit_kw)", "-3", "2")
    assert values["shortfall_backed"].value == Decimal("-2")
    _, values = _shortfall("ceil(standby_kw / lost_unit_kw)", "-3", "2")
    assert values["shortfall_backed"].value == Decimal("-1")


def test_t5_global_context_is_untouched_and_ignored():
    leaves = pack_leaves("Kisiwa")
    with decimal.localcontext() as ctx:
        ctx.prec = 5
        ctx.rounding = decimal.ROUND_DOWN
        values = evaluate(MG, leaves)
        assert decimal.getcontext().prec == 5 and decimal.getcontext().rounding == decimal.ROUND_DOWN
    expected = DERIVED["sites"]["lakeside-power/Kisiwa"]["actual"]["nodes"]
    assert all(values[f].value.quantize(CENT) == _cent(x) for f, x in expected.items())
    big = pack_leaves("Kobo")
    big["delivered_kwh"] = dataclasses.replace(big["delivered_kwh"], value=Decimal("1234567.89"))
    with decimal.localcontext() as ctx:
        ctx.prec = 5
        got = evaluate(MG, big)["metered_kwh"].value
    assert got == Decimal("1234567.89") - _pack_decimal("Kobo", "actual", "technical_loss_kwh") - \
        _pack_decimal("Kobo", "actual", "unexplained_loss_kwh")


def test_t5_neutral_values_are_the_manifest_literals():
    fm = MANIFEST["factor_map"]["MINI_GRID"]
    for row in MG.rows:
        if row.factor_id in OPTION_ONLY:
            assert row.neutral == Decimal(str(fm[row.factor_id])) and isinstance(row.neutral, Decimal)
        else:
            assert row.neutral is None
    assert set(OPTION_ONLY) == {"extra_l", "battery_throughput_kwh", "collection_cost"}
    assert MG.version == 2


@pytest.mark.parametrize("target,neutral", [
    ("om", Decimal("0")),                       # not OPTION_ONLY
    ("fuel_cost", Decimal("0")),                # a node
    ("extra_l", None),                          # OPTION_ONLY without it
    ("extra_l", 0.0),                           # a float
    ("extra_l", Decimal("NaN")),
    ("extra_l", Decimal("Infinity")),
])
def test_t5_structure_neutral(target, neutral):
    with pytest.raises(StructureError) as caught:
        check(_plant(MG, target, neutral=neutral))
    assert str(caught.value) == f"STRUCTURE_NEUTRAL MINI_GRID/{target}"


@pytest.mark.parametrize("target,composes", [("om", "MAYBE"), ("om", None), ("tariff", "SUM"),
                                             ("standby_kw", "SUM")])
def test_t5_structure_composes(target, composes):
    with pytest.raises(StructureError) as caught:
        check(_plant(MG, target, composes=composes))
    assert str(caught.value) == f"STRUCTURE_COMPOSES MINI_GRID/{target}"


@pytest.mark.parametrize("pct", [2.0, Decimal("Infinity"), Decimal("NaN"), Decimal("0"), Decimal("-Infinity")])
def test_t5_l1_tolerance_refuses_with_the_full_text(pct):
    reg = _plant(MG, "unexplained_l", tolerance=Tolerance("diesel_l", pct))
    with pytest.raises(StructureError) as caught:
        check(reg)
    assert str(caught.value) == "STRUCTURE_TOLERANCE MINI_GRID/unexplained_l"


def test_t5_parse_once(monkeypatch):
    registry_module.parsed_text.cache_clear()
    fresh = dataclasses.replace(MG)
    calls: list[str] = []
    real = expressions.parse

    def counting(text):
        calls.append(text)
        return real(text)

    monkeypatch.setattr(expressions, "parse", counting)
    leaves = pack_leaves("Kobo")
    evaluate(fresh, leaves)
    evaluate(fresh, leaves)
    node_texts = [r.expression for r in MG.rows if not r.is_leaf]
    assert sorted(calls) == sorted(node_texts) and len(calls) == 16
    registry_module.parsed_text.cache_clear()


_ASSUMED_MISSING = Missing("EXPENSE (OM)", "COMMERCIAL_RECORD", "NOT_RECEIVED", "TARGET", (), None, None)


@pytest.mark.parametrize("code,leaf,change", [
    ("STRUCTURE_MISSING", "om", dict(value=None, evidence="NOT_AVAILABLE", missing=None)),
    ("STRUCTURE_MISSING", "om", dict(missing=dataclasses.replace(_ASSUMED_MISSING, carried_as=None))),
    ("STRUCTURE_MISSING", "om", dict(value=None, evidence="NOT_AVAILABLE", currency=None, missing=_ASSUMED_MISSING)),
    ("STRUCTURE_MISSING", "om", dict(evidence="ESTIMATED",
                                     missing=dataclasses.replace(_ASSUMED_MISSING, blocks=("contribution",)))),
    ("STRUCTURE_EVIDENCE", "om", dict(evidence="GUESSED")),
    ("STRUCTURE_EVIDENCE", "om", dict(evidence="MEASURED", missing=_ASSUMED_MISSING)),  # probe P9
    ("STRUCTURE_EVIDENCE", "om", dict(value=None, evidence="MEASURED", currency=None,
                                      missing=dataclasses.replace(_ASSUMED_MISSING, carried_as=None))),
    ("STRUCTURE_EVIDENCE", "om", dict(evidence="NEUTRAL")),
    ("STRUCTURE_EVIDENCE", "extra_l", dict(value=Decimal("5"))),
    ("STRUCTURE_CURRENCY", "om", dict(currency=None)),
    ("STRUCTURE_CURRENCY", "tariff", dict(currency=None)),
])
def test_t5_leaf_value_checks(code, leaf, change):
    leaves = pack_leaves("Kobo")
    leaves[leaf] = dataclasses.replace(leaves[leaf], **change)
    error = _raises(code, evaluate, MG, leaves)
    assert str(error) == f"{code} MINI_GRID/{leaf}"


def test_t5_neutral_money_leaf_needs_no_currency_and_a_missing_input_is_refused():
    leaves = pack_leaves("Kobo")
    assert leaves["collection_cost"].currency is None and leaves["collection_cost"].evidence == "NEUTRAL"
    evaluate(MG, leaves)
    del leaves["staff"]
    assert str(_raises("STRUCTURE_LEAF_INPUT", evaluate, MG, leaves)) == "STRUCTURE_LEAF_INPUT MINI_GRID/staff"


def test_t5_neutral_identity():
    leaves = pack_leaves("Kobo")
    leaves["wear_rate"] = _absent("wear_rate", "NOT_CONNECTED")
    values = evaluate(MG, leaves)
    assert values["battery_wear"].value == 0 and values["battery_wear"].evidence == "NEUTRAL"
    assert values["battery_wear"].missing_leaves == ()
    assert values["cost_to_serve"].evidence == "MEASURED" and values["contribution"].value is not None
    # Any other zero times an unknown has no value.
    leaves["battery_throughput_kwh"] = LeafValue(Decimal("0"), "MEASURED", ("meter",), None, None, None)
    values = evaluate(MG, leaves)
    assert values["battery_wear"].value is None and values["battery_wear"].missing_leaves == ("wear_rate",)
    assert values["contribution"].value is None


def test_t5_a_node_over_two_currencies_has_no_value():
    leaves = pack_leaves("Kobo")
    leaves["diesel_price"] = dataclasses.replace(leaves["diesel_price"], currency="KES")
    values = evaluate(MG, leaves)
    assert values["fuel_cost"].currency == "KES" and values["fuel_cost"].value is not None
    fv = values["cost_to_serve"]
    assert fv.value is None and fv.evidence == "NOT_AVAILABLE"
    assert fv.missing == Missing("CURRENCY_MISMATCH:KES,USD", "OBSERVER", "NOT_CALCULATED_YET", None,
                                 ("contribution",), None, None, None)
    assert values["contribution"].value is None


@pytest.mark.parametrize("expression", ["revenue - revenue", "-(revenue - revenue)", "revenue * 0 * -1"])
def test_t5_zero_is_never_negative(expression):
    values = evaluate(_plant(MG, "contribution", expression=expression), pack_leaves("Kobo"))
    assert values["contribution"].value == 0 and not values["contribution"].value.is_signed()
    assert not str(values["contribution"].value).startswith("-")


# ---------------------------------------------------------------- T6 sources (fakes)

TZ = "Africa/Nairobi"
TENANT = uuid4()
KOBO = SiteRef(TENANT, uuid4(), "KOBO-001", "MINIGRID", TZ)
OCT = [date(2026, 10, d) for d in range(1, 32)]
AFTER = datetime(2026, 11, 20, tzinfo=timezone.utc)


def _snap(day, grade="COMPLETE", unserved="1.5", measure="critical_served", evidence="MEASURED"):
    return SimpleNamespace(local_day=day, measure=measure, evidence_class=evidence, grade=grade,
                           value=None if unserved is None else {"unserved_kwh": unserved, "served_kwh": "10"})


class FakeSnapshots:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.calls = []

    def latest(self, tenant_id, site_id, from_day, to_day, measures=None, known_at=None):
        self.calls.append((tenant_id, site_id, from_day, to_day, tuple(measures), known_at))
        return [r for r in self.rows if from_day <= r.local_day <= to_day]


class FakePrices:
    def __init__(self, selections=None):
        self.selections = selections or {}
        self.calls = []

    def __call__(self, tenant_id, site_id, key, start, end, known_at):
        self.calls.append((key, start, end, known_at))
        return self.selections.get(key, PriceSelection("UNPRICED", "NO_PRICE"))


def _source(rows=(), prices=None, now=AFTER):
    return ProductLeafSource(FakeSnapshots(rows), prices or FakePrices(), lambda: now)


def _leaf(source, factor_id, month="2026-10", known_at=None, site=KOBO):
    return source.leaf(ReadContext(site, month, known_at), factor_id)


def test_t6_source_state_is_the_spec_table():
    states = SOURCE_STATE["MINI_GRID"]
    assert set(states) == set(LEAVES) and len(states) == 31
    assert {s: {f for f, x in states.items() if x == s} for s in STATE_TABLE} == STATE_TABLE


def test_t6_each_state_yields_its_leaf_value_on_its_own_record():
    source = _source()
    for state, leaves in STATE_TABLE.items():
        for factor_id in leaves:
            got = _leaf(source, factor_id)
            src = LEAF_SOURCES[factor_id]
            if state == "OPTION_ONLY":
                assert got == LeafValue(Decimal("0"), "NEUTRAL", ("option-only neutral",), None, None, None)
                continue
            if factor_id == "period_days":
                continue
            assert got.value is None and got.evidence == "NOT_AVAILABLE", factor_id
            assert (got.missing.record_kind, got.missing.source_family) == (src["kind"], src["family"]), factor_id
            assert got.missing.record_words == src.get("words") and got.missing.blocks == ()
            cause = {"HELD_NOT_CALCULATED": "NOT_CALCULATED_YET", "NOT_CONNECTED": "NOT_CONNECTED",
                     "ASSUMED": "NOT_CONNECTED", "PROVIDED": "NOT_RECEIVED"}[state]
            assert got.missing.cause == cause, factor_id
    for factor_id, src in LEAF_SOURCES.items():
        if src["absent"] == "ZERO_WHEN_HELD":
            assert _leaf(source, factor_id).value is None, factor_id  # never 0
    assert _leaf(source, "productive_kwh").missing.cause == "NOT_CONNECTED"
    assert _leaf(source, "adjustments_kwh").value is None


def test_t6_period_days():
    assert _leaf(_source(), "period_days") == LeafValue(Decimal(31), "DERIVED", ("calendar",), None, None, None)
    assert _leaf(_source(), "period_days", "2026-02").value == 28


def test_t6_unserved_critical_needs_a_closed_fully_covered_month():
    full = [_snap(d) for d in OCT]
    got = _leaf(_source(full), "unserved_critical_kwh")
    assert got.value == Decimal("46.5") and got.evidence == "MEASURED" and got.missing is None
    assert (got.coverage.covered, got.coverage.expected) == (31, 31)
    for gap in ([_snap(d, "PARTIAL") if d.day == 9 else _snap(d) for d in OCT],
                [_snap(d) for d in OCT if d.day != 9],
                [_snap(d, "NO_DATA", None) if d.day == 9 else _snap(d) for d in OCT]):
        got = _leaf(_source(gap), "unserved_critical_kwh")
        assert got.value is None and got.missing.cause == "NOT_RECEIVED"
        assert (got.coverage.covered, got.coverage.expected) == (30, 31)
        assert got.missing.record_kind == "critical_load_delivered_power" and got.missing.source_family == "READING"
    # An open month: no value, even when every day so far is complete.
    got = _leaf(_source(full, now=datetime(2026, 10, 31, 12, tzinfo=timezone.utc)), "unserved_critical_kwh")
    assert got.value is None and got.missing.cause == "NOT_RECEIVED"
    # known_at decides "closed" when given.
    got = _leaf(_source(full), "unserved_critical_kwh", known_at=datetime(2026, 10, 30, tzinfo=timezone.utc))
    assert got.value is None
    # No expected day: no reading role declared.
    none = [_snap(d, "NOT_EXPECTED", None) for d in OCT]
    got = _leaf(_source(none), "unserved_critical_kwh")
    assert got.value is None and got.missing.cause == "NOT_CONNECTED" and got.coverage.expected == 0
    # A DECLARED row is not authoritative and counts nothing.
    got = _leaf(_source([_snap(d, evidence="DECLARED") for d in OCT]), "unserved_critical_kwh")
    assert got.value is None


def test_t6_month_window_is_site_local():
    prices = FakePrices()
    snaps = FakeSnapshots()
    ProductLeafSource(snaps, prices, lambda: AFTER).leaf(ReadContext(KOBO, "2026-10", None), "diesel_price")
    ProductLeafSource(snaps, prices, lambda: AFTER).leaf(ReadContext(KOBO, "2026-10", None), "unserved_critical_kwh")
    _, start, end, _ = prices.calls[0]
    assert start == datetime(2026, 9, 30, 21, tzinfo=timezone.utc)
    assert end == datetime(2026, 10, 31, 21, tzinfo=timezone.utc)
    assert snaps.calls[0][2:5] == (date(2026, 10, 1), date(2026, 10, 31), ("critical_served",))


def test_t6_prices():
    priced = PriceSelection("PRICED", None, "rev-1", Decimal("1.30"), "USD", "a-1")
    source = _source(prices=FakePrices({"diesel_price_per_litre": priced,
                                        "productive_use_price_per_kwh": priced}))
    got = _leaf(source, "diesel_price")
    assert got == LeafValue(Decimal("1.30"), "ESTIMATED", ("assumption:rev-1",), None,
                            Missing("EXPENSE (FUEL)", "COMMERCIAL_RECORD", "NOT_CONNECTED", "ASSUMPTION", (), None,
                                    "Declared diesel price per litre, not a fuel invoice", None), "USD")
    got = _leaf(source, "productive_tariff")
    assert got.missing.assumption == "Declared productive-use price per kWh, not a tariff schedule"
    assert got.missing.record_kind == "TARIFF_SCHEDULE" and got.currency == "USD"
    for reason in ("NO_PRICE", "PRICE_CONFLICT", "PRICE_SPANS_WINDOW", "PRICE_REVISION_MISSING",
                   "PRICE_UNIT_MISMATCH", "PRICE_INVALID"):
        source = _source(prices=FakePrices({"diesel_price_per_litre": PriceSelection("UNPRICED", reason)}))
        got = _leaf(source, "diesel_price")
        assert got.value is None and got.missing.note == reason and got.missing.carried_as is None
        assert got.missing.cause == "NOT_CONNECTED" and got.missing.record_kind == "EXPENSE (FUEL)"


def test_t6_the_read_evaluates_today_and_names_what_is_missing():
    priced = PriceSelection("PRICED", None, "rev-1", Decimal("1.30"), "USD", "a-1")
    source = _source([_snap(d) for d in OCT], FakePrices({"diesel_price_per_litre": priced}))
    result = StructureRead(source).site(KOBO, "2026-10")
    assert (result.structure_key, result.structure_version, result.site_code) == ("MINI_GRID", 2, "KOBO-001")
    values = result.values
    assert values["unserved_critical_kwh"].value == Decimal("46.5")
    assert values["contribution"].value is None and values["contribution"].evidence == "NOT_AVAILABLE"
    assert {"om", "tariff", "delivered_kwh"} <= set(values["contribution"].missing_leaves)
    assert values["battery_wear"].value == 0 and values["battery_wear"].evidence == "NEUTRAL"
    assert values["fuel_cost"].value is None
    for factor_id in STATE_TABLE["NOT_CONNECTED"] | STATE_TABLE["HELD_NOT_CALCULATED"]:
        assert values[factor_id].value is None and values[factor_id].missing.blocks == blocks_of(MG, [factor_id])


def test_t6_portfolio_refuses_duplicates_and_other_tenants_and_excludes_undeclared_types():
    read = StructureRead(_source([_snap(d) for d in OCT]))
    cold = SiteRef(TENANT, uuid4(), "ROOM-A", "COLDCHAIN", TZ)
    mto = SiteRef(TENANT, uuid4(), "MTO-001", "MINIGRID", TZ)
    result = read.portfolio(TENANT, [KOBO, cold, mto], "2026-10")
    assert result.sites == ("KOBO-001", "ROOM-A", "MTO-001")
    assert dict(result.composition.sites_excluded) == {"ROOM-A": ("STRUCTURE_NOT_DECLARED",)}
    assert result.composition.sites == ("KOBO-001", "MTO-001")
    unserved = result.composition.values["unserved_critical_kwh"]
    assert unserved.included == ("KOBO-001", "MTO-001") and unserved.value.value == Decimal("93.0")
    contribution = result.composition.values["contribution"]
    assert contribution.value.value is None and set(contribution.excluded) == {"KOBO-001", "MTO-001"}
    _raises("STRUCTURE_COMPOSE", read.portfolio, TENANT, [KOBO, KOBO], "2026-10")
    _raises("STRUCTURE_COMPOSE", read.portfolio, TENANT, [KOBO, dataclasses.replace(mto, tenant_id=uuid4())],
            "2026-10")
    with pytest.raises(ValueError):
        read.site(KOBO, "2026-13")


# ---------------------------------------------------------------- T7 evidence order


def test_t7_evidence_order():
    leaves = pack_leaves("Kobo")
    leaves["tariff"] = dataclasses.replace(leaves["tariff"], evidence="DECLARED")
    values = evaluate(MG, leaves)
    assert values["revenue"].evidence == "DECLARED"
    assert values["diesel_l"].evidence == "MEASURED"  # MEASURED and NEUTRAL children
    leaves["staff"] = _absent("staff")
    assert evaluate(MG, leaves)["cost_to_serve"].evidence == "NOT_AVAILABLE"
    leaves = pack_leaves("Kobo")
    leaves["necessary_l"] = dataclasses.replace(leaves["necessary_l"], evidence="MODELLED")
    assert evaluate(MG, leaves)["diesel_l"].evidence == "MODELLED"


# ---------------------------------------------------------------- coverage (R7)


def test_r7_a_node_keeps_the_smallest_share_coverage_and_the_portfolio_sums_it():
    from assetops_backend.structure.evaluate import Coverage

    low = Coverage(20, 31, {"COMPLETE": 20, "NO_DATA": 11})
    high = Coverage(30, 31, {"COMPLETE": 30, "PARTIAL": 1})
    tie = Coverage(40, 62, {"COMPLETE": 40, "NO_DATA": 22})  # the same share as `low`, later in names() order
    leaves = pack_leaves("Kobo")
    leaves["delivered_kwh"] = dataclasses.replace(leaves["delivered_kwh"], coverage=high)
    leaves["technical_loss_kwh"] = dataclasses.replace(leaves["technical_loss_kwh"], coverage=low)
    leaves["unexplained_loss_kwh"] = dataclasses.replace(leaves["unexplained_loss_kwh"], coverage=tie)
    kobo = evaluate(MG, leaves)
    assert kobo["metered_kwh"].coverage is low
    assert kobo["billed_kwh"].coverage is low and kobo["revenue"].coverage is low
    assert kobo["diesel_l"].coverage is None
    leaves = pack_leaves("Mto")
    leaves["delivered_kwh"] = dataclasses.replace(leaves["delivered_kwh"], coverage=high)
    per_site = {"Kobo": site_structure("Kobo", {**pack_leaves("Kobo"), "delivered_kwh": dataclasses.replace(
        pack_leaves("Kobo")["delivered_kwh"], coverage=low)}), "Mto": site_structure("Mto", leaves),
        "Kisiwa": site_structure("Kisiwa")}
    summed = compose(MG, per_site).values["delivered_kwh"].value.coverage
    assert (summed.covered, summed.expected) == (50, 62)
    assert dict(summed.grades) == {"COMPLETE": 50, "NO_DATA": 11, "PARTIAL": 1}
