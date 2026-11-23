"""3B6: the cold-room and captive-EV structures, declared and tested from the start (spec §6, tests 1 to 8).

Tests 1, 2, 4 and 4b are the independent check (W2): their expected values come from the pack
(`demo-site-scenario-manifest.yaml`, `derived-values.json`) or from this file's own literals; nothing expected is read
from `rows_cold_chain.py`, `rows_ev_depot.py`, `HOMES`, `SOURCE_STATE` or the evaluator. Test 3 passes its own
mappings to `check` and `check_all`, so a data plant on the real rows cannot fail it (D-3B6.16). No database: run
with `DATABASE_URL` and `ASSETOPS_TEST_DATABASE_URL` unset.

"Revenue not applicable" is declared, checked and queryable (`applicability()`); no read record carries it until
`3B5` (D-3B6.14), so no test here asserts that a read shows it.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from uuid import uuid4

import pytest
import yaml

from assetops_backend.chain.ports import SiteRef
from assetops_backend.config import ConfigurationError
from assetops_backend.structure import money as money_module
from assetops_backend.structure import pins
from assetops_backend.structure import registry as registry_module
from assetops_backend.structure import sources as sources_module
from assetops_backend.structure.attribution.read import BridgeRead
from assetops_backend.structure.check import CODES, StructureError, check, check_all
from assetops_backend.structure.energy.source import EnergyLeafSource
from assetops_backend.structure.evaluate import LeafValue, compose, evaluate
from assetops_backend.structure.expressions import parse, unit_of
from assetops_backend.structure.litres.source import LitreLeafSource
from assetops_backend.structure.money import CommercialLeafSource
from assetops_backend.structure.read import (
    KEY_NOT_READ,
    NOT_DECLARED,
    OTHER_STRUCTURE,
    StructureRead,
    sites_excluded,
)
from assetops_backend.structure.registry import (
    APPLIES,
    NOT_APPLICABLE,
    NOT_IN_STRUCTURE,
    REGISTRIES,
    applicability,
)
from assetops_backend.structure.sources import (
    COMMERCIAL_LEAVES,
    ENERGY_LEAVES,
    LITRE_LEAVES,
    SOURCE_STATE,
    ProductLeafSource,
)
from assetops_backend.structure.targets.read import TargetRead
from assetops_backend.structure_snapshot.read import SnapshotRead
from assetops_contracts.canonical import leaves_of
from assetops_contracts.canonical.units import DAY, HOUR, KWH, MINUTE, MONEY, ONE

REPO = Path(__file__).resolve().parents[2]
PACK = REPO / "Docs/demo-sprint/product-direction-layer4"
PKG = REPO / "backend/assetops_backend"
_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
MANIFEST = yaml.load((PACK / "demo-site-scenario-manifest.yaml").read_text(encoding="utf-8"), Loader=_LOADER)
DERIVED = json.loads((PACK / "derived-values.json").read_text(encoding="utf-8"))

COLD, EV, MG_KEY = "COLD_CHAIN", "EV_DEPOT_CAPTIVE", "MINI_GRID"
KEYS = (COLD, EV)
CENT = Decimal("0.01")
USD = "USD"

# The test's own home map (3B1's OWN_HOME_MAP, copied; W2).
OWN_HOME_MAP = {
    "grow": "GROW_REVENUE",
    "optimize": "OPTIMIZE_COST",
    "protect": "PROTECT_ASSET",
    "assure": "ASSURE_PERFORMANCE",
    "above": "ABOVE",
    "calendar": "CALENDAR",
}
COUNTS = {COLD: (23, 13), EV: (23, 20)}  # DD4.5 (D-DD.125): + buses_full_by_charger

# ---------------------------------------------------------------- spec §2.2.1 and §2.2.2, written again (W2)

NONE_LEAVES = {
    COLD: {"rate", "contract_rate", "k_kwh_per_crate_day", "model_factor", "elec_price", "minutes_per_day",
           "period_days"},
    EV: {"charger_kw", "import_limit_kw", "window_h", "kwh_per_bus_night", "nights_in_period", "max_kw", "peak_price",
         "offpeak_price", "night_price", "demand_rate", "penalty_rate"},
}
NEUTRAL = {
    COLD: {"contract_crate_days": Decimal("0"), "contract_rate": Decimal("0"), "model_factor": Decimal("1"),
           "handling": Decimal("0")},
    EV: {"covered_bus_nights": Decimal("0"), "extra_missed_departures": Decimal("0")},
}
_NODE_TABLE = (
    (COLD, ("revenue", "received", "energy", "cost_to_serve", "contribution"), MONEY, "SUM"),
    (COLD, ("kwh_model", "kwh"), KWH, "SUM"),
    (COLD, ("nights_without_backup_cover", "days_backup_start_unproven", "occupied_total_crate_days",
            "crate_days_without_excursion"), DAY, "SUM"),
    (COLD, ("chamber_minutes", "cooling_available_minutes"), MINUTE, "SUM"),
    (EV, ("deliverable_kwh_night", "scheduled_kwh_night", "supplied_kwh_night", "required_kwh_night"), KWH / DAY,
     "NONE"),
    (EV, ("buses_full_by_charger", "buses_short_per_night"), ONE, "NONE"),  # DD4.5 (D-DD.125)
    (EV, ("departures_required", "departures_missed", "nights_below_required", "charger_days_out_of_service",
          "departures_met"), DAY, "SUM"),
    (EV, ("peak_cost", "offpeak_cost", "night_cost", "demand_cost", "energy_cost", "penalties", "cost_to_serve",
          "contribution"), MONEY, "SUM"),
    (EV, ("cost_per_departure_met",), MONEY / DAY, "NONE"),
)
NODE_UNITS = {(k, f): (u, c) for k, ids, u, c in _NODE_TABLE for f in ids}

#: The 15 per-registry codes of `main` before 3B6, in order.
CODES_BEFORE = ("STRUCTURE_DUPLICATE", "STRUCTURE_EXPRESSION", "STRUCTURE_UNKNOWN_FACTOR", "STRUCTURE_CYCLE",
                "STRUCTURE_CATALOGUE", "STRUCTURE_LEAF_SOURCE", "STRUCTURE_LEAF_ABSENT", "STRUCTURE_NEUTRAL",
                "STRUCTURE_TOLERANCE", "STRUCTURE_UNIT", "STRUCTURE_COMPOSES", "STRUCTURE_STATED",
                "STRUCTURE_CATEGORY", "STRUCTURE_OBJECTIVE", "STRUCTURE_MONEY_HOME")


def _home(entry: list) -> tuple[str, str | None]:
    return OWN_HOME_MAP[entry[0]], (entry[1] if len(entry) > 1 else None)


# ---------------------------------------------------------------- test 1: parity with the manifest (T1)


@pytest.mark.parametrize("key", KEYS)
def test_1_nodes_and_expressions_equal_the_manifest(key):
    nodes = {r.factor_id: r.expression for r in REGISTRIES[key].rows if not r.is_leaf}
    assert nodes == MANIFEST["structures"][key]


@pytest.mark.parametrize("key", KEYS)
def test_1_leaf_set_sources_absence_and_words(key):
    reg = REGISTRIES[key]
    leaves = [r for r in reg.rows if r.is_leaf]
    assert {r.factor_id for r in leaves} == set(MANIFEST["factor_map"][key])
    sources = MANIFEST["empty_states"]["leaf_sources"][key]
    assert {r.factor_id for r in leaves} == set(sources)
    for row in leaves:
        declared = sources[row.factor_id]
        assert (row.filled_by.family, row.filled_by.kind, row.filled_by.words) == (
            declared["family"], declared["kind"], declared.get("words")), row.factor_id
        assert row.absent == declared["absent"], row.factor_id
    assert any(r.filled_by.words for r in leaves)  # the words field is not vacuous


@pytest.mark.parametrize("key", KEYS)
def test_1_every_row_home_equals_home_categories(key):
    reg = REGISTRIES[key]
    homes = MANIFEST["home_categories"]["nodes"][key]
    for row in reg.rows:
        assert (row.home.category, row.home.objective) == _home(homes[row.factor_id]), row.factor_id
    assert set(homes) - {r.factor_id for r in reg.rows} == {"cover_not_claimable"}


@pytest.mark.parametrize("key", KEYS)
def test_1_order_counts_and_version(key):
    reg = REGISTRIES[key]
    n_leaves, n_nodes = COUNTS[key]
    ids = [r.factor_id for r in reg.rows]
    assert reg.structure_key == key and reg.version == 1
    assert len(ids) == n_leaves + n_nodes == {COLD: 36, EV: 43}[key]
    assert ids[:n_leaves] == list(leaves_of(key))
    assert ids[n_leaves:] == list(MANIFEST["structures"][key])
    assert all(r.tolerance is None and r.stated_by is None for r in reg.rows)  # D-3B6.2, .9
    assert {r.factor_id: r.levers for r in reg.rows if r.levers} == {  # 6h spec §5.2 (D-P6.66 N3)
        COLD: {"uncovered_nights": ("backup_cover",), "excursion_crates": ("backup_cover",),
               "excess_kwh": ("chamber_efficiency",), "contract_crate_days": ("storage_contract",),
               "nights_without_backup_cover": ("backup_cover",)},
        EV: {"chargers_in_service": ("charger_restore",), "buses": ("fleet_capacity_use",),
             "peak_kwh": ("charging_schedule",), "departures_missed": ("charger_restore",)}}[key]


@pytest.mark.parametrize("key", (MG_KEY, COLD, EV))
def test_1_not_applicable_equals_the_chain_model(key):
    declared = tuple(f for f, v in MANIFEST["chain_model"][key].items() if v == "NOT_APPLICABLE")
    assert REGISTRIES[key].not_applicable == declared
    assert {MG_KEY: (), COLD: (), EV: ("revenue",)}[key] == declared  # the pack's reading, stated here too


# ---------------------------------------------------------------- test 2: units and composes (T2)


def test_2_check_all_passes():
    check_all()


@pytest.mark.parametrize("key", KEYS)
def test_2_node_units_and_composes_equal_the_table(key):
    reg = REGISTRIES[key]
    declared = {r.factor_id: r.unit for r in reg.rows}
    nodes = [r for r in reg.rows if not r.is_leaf]
    assert {(key, r.factor_id) for r in nodes} == {k for k in NODE_UNITS if k[0] == key}
    for row in nodes:
        unit, composes = NODE_UNITS[(key, row.factor_id)]
        assert row.unit == unit, row.factor_id
        assert unit_of(parse(row.expression), declared) == unit, row.factor_id
        assert row.composes == composes, row.factor_id


@pytest.mark.parametrize("key", KEYS)
def test_2_leaf_composes_and_neutral(key):
    reg = REGISTRIES[key]
    sources = MANIFEST["empty_states"]["leaf_sources"][key]
    for row in (r for r in reg.rows if r.is_leaf):
        assert row.composes == ("NONE" if row.factor_id in NONE_LEAVES[key] else "SUM"), row.factor_id
        if sources[row.factor_id]["absent"] == "OPTION_ONLY":
            literal = Decimal(MANIFEST["factor_map"][key][row.factor_id])
            assert row.neutral == literal == NEUTRAL[key][row.factor_id], row.factor_id
        else:
            assert row.neutral is None, row.factor_id
    assert {r.factor_id for r in reg.rows if r.neutral is not None} == set(NEUTRAL[key])


# ---------------------------------------------------------------- test 3: the check (T3)


def _ev(not_applicable) -> registry_module.Registry:
    return dataclasses.replace(REGISTRIES[EV], not_applicable=not_applicable)


@pytest.mark.parametrize("planted, text", [
    (("Revenue",), "STRUCTURE_NOT_APPLICABLE EV_DEPOT_CAPTIVE/Revenue"),
    (("revenue", "revenue"), "STRUCTURE_NOT_APPLICABLE EV_DEPOT_CAPTIVE/revenue"),
    (("cost_to_serve",), "STRUCTURE_NOT_APPLICABLE EV_DEPOT_CAPTIVE/cost_to_serve"),
])
def test_3_per_registry_refusals(planted, text):
    with pytest.raises(StructureError) as caught:
        check(_ev(planted))
    assert str(caught.value) == text


def test_3_the_real_declaration_passes_per_registry():
    check(_ev(("revenue",)))  # the repeat plant above refuses the second entry only


def test_3_mapping_level_refusals():
    three = {MG_KEY: REGISTRIES[MG_KEY], COLD: REGISTRIES[COLD], EV: _ev(("revenu",))}
    with pytest.raises(StructureError) as caught:
        check_all(registries=three)
    assert str(caught.value) == "STRUCTURE_NOT_APPLICABLE EV_DEPOT_CAPTIVE/revenu"
    with pytest.raises(StructureError) as caught:
        check_all(registries={EV: REGISTRIES[EV]})
    assert str(caught.value) == "STRUCTURE_NOT_APPLICABLE EV_DEPOT_CAPTIVE/revenue"
    with pytest.raises(StructureError) as caught:
        check_all(registries={COLD: REGISTRIES[EV]})
    assert str(caught.value) == "STRUCTURE_CATALOGUE COLD_CHAIN/-"
    check_all(registries={MG_KEY: REGISTRIES[MG_KEY], EV: REGISTRIES[EV]})  # revenue is a mini-grid row


def test_3_codes_append_not_applicable_last():
    assert CODES[-1] == "STRUCTURE_NOT_APPLICABLE"
    assert CODES[:-1] == CODES_BEFORE


def test_3_create_app_refuses_a_not_applicable_typo(monkeypatch):
    from assetops_backend.main import create_app

    planted = {**REGISTRIES, EV: _ev(("revenu",))}
    monkeypatch.setattr(registry_module, "REGISTRIES", MappingProxyType(planted))
    with pytest.raises(ConfigurationError, match=r"^STRUCTURE_NOT_APPLICABLE EV_DEPOT_CAPTIVE/revenu$") as caught:
        create_app()
    assert isinstance(caught.value.__cause__, StructureError)


# ---------------------------------------------------------------- test 4: the six Sites (T4)

#: The test's own money leaves (W2).
MONEY_LEAVES = {
    COLD: {"rate", "contract_rate", "elec_price", "staff", "maint", "liability", "handling", "outstanding"},
    EV: {"peak_price", "offpeak_price", "night_price", "demand_rate", "maintenance", "penalty_rate"},
}
SIDES = (
    ("harvest-cold/Room A · Mwea", "actual", COLD), ("harvest-cold/Room A · Mwea", "plan", COLD),
    ("harvest-cold/Room B · Thika", "actual", COLD), ("harvest-cold/Room B · Thika", "plan", COLD),
    ("harvest-cold/Room C · Kirinyaga", "actual", COLD), ("harvest-cold/Room C · Kirinyaga", "plan", COLD),
    ("metro-bus/Embakasi", "actual", EV), ("metro-bus/Embakasi", "plan", EV),
    ("metro-bus/Kasarani", "actual", EV), ("metro-bus/Kasarani", "plan", EV),
    ("metro-bus/Kasarani", "november_to_date", EV),
    ("metro-bus/Ruiru", "actual", EV), ("metro-bus/Ruiru", "november_to_date", EV),
)
#: Skipped with its reason: a stated total with no factor behind it (manifest `home_categories.residuals`).
SKIPPED = {("metro-bus/Ruiru", "plan"): "a stated total with no factor behind it; no nodes in derived-values.json"}
HAND = {
    ("harvest-cold/Room A · Mwea", "actual"): {"contribution": "202.74", "kwh_model": "1544.44",
                                               "chamber_minutes": "44640"},
    ("harvest-cold/Room B · Thika", "actual"): {"contribution": "843.73", "crate_days_without_excursion": "8560"},
    ("metro-bus/Embakasi", "actual"): {"cost_to_serve": "22744.80", "cost_per_departure_met": "36.69",
                                       "contribution": "-22744.80"},
    ("metro-bus/Ruiru", "actual"): {"charger_days_out_of_service": "26"},
}


def _q(x) -> Decimal:
    return Decimal(str(x)).quantize(CENT, ROUND_HALF_EVEN)


def cold_ev_leaves(site: str, side: str, key: str) -> dict[str, LeafValue]:
    """The pack's leaves of one side, built as `test_3b3_structure_evaluate.pack_leaves` builds them."""
    nodes = DERIVED["sites"][site][side]["nodes"]
    sources = MANIFEST["empty_states"]["leaf_sources"][key]
    base = "DECLARED" if side == "plan" else "MEASURED"
    out = {}
    for leaf in MANIFEST["factor_map"][key]:
        value = Decimal(str(nodes[leaf]))
        if leaf == "k_kwh_per_crate_day":  # DD4.6 (D-DD.144): derived-values.json holds nodes at 2 decimals (0.06); the slope is M's own
            value = Decimal(str(next(t for t in MANIFEST["tenants"] if t["tenant"] == "harvest-cold")["energy_model"][leaf]))
        if sources[leaf]["absent"] == "OPTION_ONLY":
            out[leaf] = LeafValue(value, "NEUTRAL", ("pack",), None, None, None)
        else:
            out[leaf] = LeafValue(value, base, (f"pack:{side}",), None, None,
                                  USD if leaf in MONEY_LEAVES[key] else None, ("source-emulated",))
    return out


def _evaluated(site: str, side: str, key: str):
    return evaluate(REGISTRIES[key], cold_ev_leaves(site, side, key))


def test_4_the_sides_and_the_skip_set_are_the_pack():
    pack = {(s, side) for s in DERIVED["sites"] if s.split("/")[0] in ("harvest-cold", "metro-bus")
            for side in DERIVED["sites"][s]}
    assert pack == {(s, side) for s, side, _ in SIDES} | set(SKIPPED)
    assert len(SIDES) == 13
    for site, side in SKIPPED:
        assert "nodes" not in DERIVED["sites"][site][side]


@pytest.mark.parametrize("site, side, key", SIDES)
def test_4_every_factor_equals_the_pack_to_the_cent(site, side, key):
    out = _evaluated(site, side, key)
    nodes = DERIVED["sites"][site][side]["nodes"]
    assert list(out) == [r.factor_id for r in REGISTRIES[key].rows]
    for factor_id, fv in out.items():
        assert fv.value is not None, factor_id
        assert _q(fv.value) == _q(nodes[factor_id]), factor_id
    for factor_id, literal in HAND.get((site, side), {}).items():
        assert _q(out[factor_id].value) == _q(literal), factor_id


# ---------------------------------------------------------------- test 4b: the two portfolios (T4b)

PORTFOLIOS = {
    "harvest-cold": (COLD, ("Room A · Mwea", "Room B · Thika", "Room C · Kirinyaga"),
                     {"contribution": "2127.75", "revenue": "4588.00", "excursion_crates": "120"}),
    "metro-bus": (EV, ("Embakasi", "Kasarani", "Ruiru"),
                  {"cost_to_serve": "41705.12", "departures_met": "1302", "charger_out_days": "26"}),
}


@pytest.mark.parametrize("tenant", sorted(PORTFOLIOS))
def test_4b_the_portfolio_sums_equal_the_pack(tenant):
    """Every SUM factor equals the pack's sum; the pack's sums of prices and per-night rates are not compared
    (they are NONE here)."""
    key, sites, literals = PORTFOLIOS[tenant]
    reg = REGISTRIES[key]
    from assetops_backend.structure.evaluate import SiteStructure

    per_site = {s: SiteStructure(s, "2026-10", key, reg.version, _evaluated(f"{tenant}/{s}", "actual", key))
                for s in sites}
    comp = compose(reg, per_site)
    sums = DERIVED["portfolio"][tenant]["actual"]["sums"]
    summed = [r.factor_id for r in reg.rows if r.composes == "SUM"]
    assert set(comp.values) == set(summed)
    for factor_id in summed:
        assert _q(comp.values[factor_id].value.value) == _q(sums[factor_id]), factor_id
    for row in reg.rows:
        if row.composes == "NONE":
            assert row.factor_id in comp.not_composed and row.factor_id not in comp.values, row.factor_id
    for factor_id, literal in literals.items():
        assert _q(comp.values[factor_id].value.value) == _q(literal), factor_id


# ---------------------------------------------------------------- shared: the product read of §5.3


class Boom:
    """A fake that fails the test when anything on it is touched."""

    def __init__(self, name: str) -> None:
        self._name = name

    def __getattr__(self, attr: str):
        raise AssertionError(f"{self._name}.{attr} was called")

    def __call__(self, *args, **kwargs):
        raise AssertionError(f"{self._name} was called")


TENANT = uuid4()
NAIROBI = "Africa/Nairobi"
COLD_SITE = SiteRef(TENANT, uuid4(), "COLD-THIKA", "COLDCHAIN", NAIROBI)
EV_SITE = SiteRef(TENANT, uuid4(), "EV-RUI", "EV_CHARGING", NAIROBI)
KNOWN_AT = datetime(2026, 11, 6, tzinfo=timezone.utc)
NOW = KNOWN_AT
MONTHS = {"2026-10": 31, "2026-02": 28, "2026-11": 30, "2028-02": 29}


def product() -> ProductLeafSource:
    return ProductLeafSource(Boom("snapshots"), Boom("window_price"), lambda: NOW)


def chain() -> EnergyLeafSource:
    """The production chain as `structure/composition.py` builds it (D-3B6.20), every store a raising fake."""
    litres = LitreLeafSource(Boom("litre inputs"), product(), lambda: NOW)
    commercial = CommercialLeafSource(Boom("commercial months"), Boom("commercial store"), litres)
    return EnergyLeafSource(Boom("energy inputs"), commercial, lambda: NOW)


#: The test's own copy of spec §4.2's state table (W2).
STATE_TABLE = {
    COLD: {
        "PROVIDED": {"period_days", "minutes_per_day"},
        "OPTION_ONLY": {"contract_crate_days", "contract_rate", "model_factor", "handling"},
        "HELD_NOT_CALCULATED": {"cooling_minutes_unavailable"},
        "NOT_CONNECTED": {"outstanding", "staff", "liability", "crate_days", "rate", "base_kwh",
                          "k_kwh_per_crate_day", "excess_kwh", "elec_price", "maint", "uncovered_nights",
                          "backup_unproven_days", "excursion_crates", "excursion_days", "batches_exposed",
                          "capacity_crate_days"},
    },
    EV: {
        "PROVIDED": {"nights_in_period"},
        "OPTION_ONLY": {"covered_bus_nights", "extra_missed_departures"},
        "HELD_NOT_CALCULATED": {"chargers_in_service", "import_limit_kw", "chargers_installed"},
        "NOT_CONNECTED": {"charger_kw", "charger_out_days", "window_h", "buses", "kwh_per_bus_night", "peak_kwh",
                          "kwh_2200_2400", "kwh_0000_0500", "max_kw", "peak_price", "offpeak_price", "night_price",
                          "demand_rate", "maintenance", "short_nights", "spare_bus_nights", "penalty_rate"},
    },
}
STATE_COUNTS = {COLD: (2, 4, 1, 16), EV: (1, 2, 3, 17)}
CALENDAR = {COLD: {"period_days": "days", "minutes_per_day": 1440}, EV: {"nights_in_period": "days"}}
MONEY_NODES = {COLD: ("revenue", "received", "energy", "cost_to_serve", "contribution"),
               EV: ("peak_cost", "offpeak_cost", "night_cost", "demand_cost", "energy_cost", "penalties",
                    "cost_to_serve", "contribution")}
#: Nodes resting only on OPTION_ONLY leaves and the calendar, which may read 0 (none today).
ZERO_ALLOWED_NODES: set[str] = set()


def _read(site: SiteRef, month: str, source=None):
    return StructureRead(source if source is not None else product()).site(site, month, KNOWN_AT).values


# ---------------------------------------------------------------- test 5a: revenue declared not applicable (T5a)


def test_5a_revenue_is_declared_not_applicable_never_a_row_or_zero():
    """Declared, checked and queryable only: no read record carries applicability (D-3B6.14)."""
    ev, mg, cold = REGISTRIES[EV], REGISTRIES[MG_KEY], REGISTRIES[COLD]
    assert all(r.factor_id != "revenue" for r in ev.rows)
    assert applicability(ev, "revenue") == NOT_APPLICABLE
    assert applicability(ev, "tariff") == NOT_IN_STRUCTURE
    assert applicability(ev, "cost_to_serve") == APPLIES
    assert applicability(mg, "revenue") == applicability(cold, "revenue") == APPLIES
    assert applicability(ev, "Not An ID") == NOT_IN_STRUCTURE  # total: never raises
    read = _read(EV_SITE, "2026-10")
    sides = [_evaluated(s, side, k) for s, side, k in SIDES if k == EV]
    for values in [read, *sides]:
        assert not {"revenue", "received", "collected"} & set(values)
    for values in sides:
        assert values["contribution"].value == -values["cost_to_serve"].value
    assert read["contribution"].value is None and read["cost_to_serve"].value is None
    embakasi = _evaluated("metro-bus/Embakasi", "actual", EV)
    assert "revenue" not in embakasi and _q(embakasi["contribution"].value) == _q("-22744.80")


# ---------------------------------------------------------------- test 5b: the product read (T5b)


@pytest.mark.parametrize("key", KEYS)
def test_5b_source_state_is_the_table(key):
    assert set(SOURCE_STATE[key]) == {r.factor_id for r in REGISTRIES[key].rows if r.is_leaf}
    table = {f: state for state, ids in STATE_TABLE[key].items() for f in ids}
    assert dict(SOURCE_STATE[key]) == table
    counts = tuple(len(STATE_TABLE[key][s]) for s in ("PROVIDED", "OPTION_ONLY", "HELD_NOT_CALCULATED",
                                                      "NOT_CONNECTED"))
    assert counts == STATE_COUNTS[key]


def _check_product_read(key: str, site: SiteRef, month: str, values) -> None:
    days = MONTHS[month]
    sources = MANIFEST["empty_states"]["leaf_sources"][key]
    neutral = {f: Decimal(MANIFEST["factor_map"][key][f]) for f in STATE_TABLE[key]["OPTION_ONLY"]}
    for leaf, expected in CALENDAR[key].items():
        fv = values[leaf]
        assert (fv.value, fv.evidence) == (Decimal(days if expected == "days" else expected), "DERIVED"), leaf
    for leaf in STATE_TABLE[key]["OPTION_ONLY"]:
        assert (values[leaf].value, values[leaf].evidence) == (neutral[leaf], "NEUTRAL"), leaf
    for state, cause in (("NOT_CONNECTED", "NOT_CONNECTED"), ("HELD_NOT_CALCULATED", "NOT_CALCULATED_YET")):
        for leaf in STATE_TABLE[key][state]:
            fv = values[leaf]
            assert (fv.value, fv.evidence) == (None, "NOT_AVAILABLE"), leaf
            assert fv.missing.cause == cause, leaf
            declared = sources[leaf]
            assert (fv.missing.record_kind, fv.missing.source_family, fv.missing.record_words) == (
                declared["kind"], declared["family"], declared.get("words")), leaf
    for node in MONEY_NODES[key]:
        assert values[node].value is None, node
        assert values[node].missing_leaves, node
    zero = {f for f, fv in values.items() if fv.value is not None and fv.value == 0}
    assert zero <= {f for f in STATE_TABLE[key]["OPTION_ONLY"] if neutral[f] == 0} | ZERO_ALLOWED_NODES


@pytest.mark.parametrize("month", sorted(MONTHS))
def test_5b_cold_site_read(month):
    values = _read(COLD_SITE, month)
    _check_product_read(COLD, COLD_SITE, month, values)
    assert (values["chamber_minutes"].value, values["chamber_minutes"].evidence) == (
        Decimal(MONTHS[month] * 1440), "DERIVED")
    assert {"2026-10": 44640, "2026-02": 40320, "2026-11": 43200, "2028-02": 41760}[month] == \
        values["chamber_minutes"].value
    assert values["cooling_available_minutes"].value is None


@pytest.mark.parametrize("month", sorted(MONTHS))
def test_5b_ev_site_read(month):
    values = _read(EV_SITE, month)
    _check_product_read(EV, EV_SITE, month, values)
    assert values["departures_required"].value is None
    assert values["contribution"].value is None


# ---------------------------------------------------------------- test 5c: held records exist (T5c)

HELD_RECORDS = {
    (COLD, "cooling_minutes_unavailable"): (("sites/binding_roles.py", '"compressor_state"'),),
    (EV, "chargers_in_service"): (("sites/binding_roles.py", '"ev_connector_state"'),
                                  ("sites/binding_roles.py", '"ev_connector_fault"')),
    (EV, "import_limit_kw"): (("sites/ev_foundation.py", '"ev-site-import-limit"'),),
    (EV, "chargers_installed"): (("sites/ev_foundation.py", '"EV_CHARGER"'),),
}


def test_5c_every_held_leaf_cites_a_record_that_exists():
    held = {(k, f) for k in KEYS for f, state in SOURCE_STATE[k].items() if state == "HELD_NOT_CALCULATED"}
    assert held == set(HELD_RECORDS)
    for leaf, cited in HELD_RECORDS.items():
        for path, token in cited:
            assert token in (PKG / path).read_text(encoding="utf-8"), (leaf, path, token)


# ---------------------------------------------------------------- test 6: no other store, no shared-ID routing (T6)


@pytest.mark.parametrize("site, key", ((COLD_SITE, COLD), (EV_SITE, EV)))
def test_6a_the_production_chain_reads_like_the_product_source(site, key):
    for month in MONTHS:
        through_chain = StructureRead(chain(), stated=chain()).site(site, month, KNOWN_AT).values
        assert through_chain == _read(site, month), month


@pytest.mark.parametrize("key", KEYS)
def test_6b_no_cold_or_ev_leaf_is_served_by_a_commercial_litre_or_energy_provider(key):
    routed = COMMERCIAL_LEAVES | LITRE_LEAVES | set(money_module._ROWS) | ENERGY_LEAVES
    for factor_id, state in SOURCE_STATE[key].items():
        if factor_id in routed:
            assert state not in ("PROVIDED", "PROVIDED_ELSE_ASSUMED"), factor_id
    assert "staff" in routed and "staff" in SOURCE_STATE[COLD]  # the assertion is by state: the ID is shared


def test_6c_a_provided_cold_staff_cannot_route_through_mini_grid_rows(monkeypatch):
    patched = {**SOURCE_STATE, COLD: MappingProxyType({**SOURCE_STATE[COLD], "staff": "PROVIDED"})}
    for module in (sources_module, money_module):
        monkeypatch.setattr(module, "SOURCE_STATE", MappingProxyType(patched))
    values = StructureRead(chain()).site(COLD_SITE, "2026-10", KNOWN_AT).values
    fb = REGISTRIES[COLD].row("staff").filled_by
    staff = values["staff"]
    assert (staff.value, staff.evidence, staff.missing.cause) == (None, "NOT_AVAILABLE", "NOT_CONNECTED")
    assert (staff.missing.record_kind, staff.missing.source_family, staff.missing.record_words) == (
        fb.kind, fb.family, fb.words)


# ---------------------------------------------------------------- test 7: pins (T7)

OWN_PINS = {
    "GENERATOR_SUPPORT_CANDIDATE": (MG_KEY, "candidate_l"),
    "UNEXPLAINED_FUEL": (MG_KEY, "unexplained_l"),
    "COLD_START_FAILURE": (COLD, "uncovered_nights"),
    "COLD_EXCURSION": (COLD, "excursion_crates"),
    "EV_INTERRUPTION": (EV, "chargers_in_service"),
}


def test_7_pins():
    assert {m: (p.structure_key, p.factor_id) for m, p in pins.PINS.items()} == OWN_PINS
    assert dict(pins.PENDING_PINS) == {}
    check_all()
    assert [d.mechanism for d in pins.parity()] == ["UNEXPLAINED_FUEL"]
    for mechanism in ("COLD_START_FAILURE", "COLD_EXCURSION", "EV_INTERRUPTION"):
        assert pins.pinned_category(mechanism) == "PROTECT_ASSET", mechanism


# ---------------------------------------------------------------- test 8: the readers (T8)

KOBO = SiteRef(TENANT, uuid4(), "KOBO-001", "MINIGRID", NAIROBI)
HYDRO = SiteRef(TENANT, uuid4(), "HYDRO-1", "HYDRO", NAIROBI)
COLD_B = SiteRef(TENANT, uuid4(), "COLD-MWEA", "COLDCHAIN", NAIROBI)
OCT = "2026-10"


def _priced_product() -> ProductLeafSource:
    """A product source whose snapshot and price ports answer "nothing held" (3B7a's `priced` shape)."""
    def window(*args):
        return SimpleNamespace(state="NO_PRICE", value=None, currency=None, revision_id=None, reason="NO_PRICE")
    return ProductLeafSource(SimpleNamespace(latest=lambda *a, **k: ()), window, lambda: NOW)


def test_8_sites_excluded_names_each_reason_in_order():
    assert dict(sites_excluded([KOBO, COLD_SITE, EV_SITE, HYDRO], MG_KEY)) == {
        "COLD-THIKA": OTHER_STRUCTURE, "EV-RUI": OTHER_STRUCTURE, "HYDRO-1": NOT_DECLARED}
    assert list(sites_excluded([KOBO, COLD_SITE, EV_SITE, HYDRO], MG_KEY)) == ["COLD-THIKA", "EV-RUI", "HYDRO-1"]
    assert dict(sites_excluded([KOBO, COLD_SITE], COLD)) == {"KOBO-001": OTHER_STRUCTURE}
    assert isinstance(sites_excluded([], MG_KEY), MappingProxyType)


def test_8_structure_portfolio_per_key():
    read = StructureRead(_priced_product())
    p = read.portfolio(TENANT, [KOBO, COLD_SITE, EV_SITE, HYDRO], OCT)
    assert p.structure_key == MG_KEY and p.composition.sites == ("KOBO-001",)
    assert list(p.composition.sites_excluded.items()) == [
        ("COLD-THIKA", OTHER_STRUCTURE), ("EV-RUI", OTHER_STRUCTURE), ("HYDRO-1", NOT_DECLARED)]
    c = read.portfolio(TENANT, [COLD_SITE, COLD_B, KOBO], OCT, structure_key=COLD)
    assert c.structure_key == COLD and c.composition.sites == ("COLD-THIKA", "COLD-MWEA")
    assert dict(c.composition.sites_excluded) == {"KOBO-001": OTHER_STRUCTURE}
    assert c.composition.values["chamber_minutes"].value.value == Decimal(2 * 44640)
    with pytest.raises(StructureError) as caught:
        read.portfolio(TENANT, [KOBO], OCT, structure_key="NOPE")
    assert str(caught.value) == "STRUCTURE_NOT_DECLARED NOPE/-"


def _refuses_key_not_read(call, site: SiteRef) -> None:
    with pytest.raises(StructureError) as caught:
        call()
    assert (caught.value.code, caught.value.factor_id) == (KEY_NOT_READ, site.site_code)


@pytest.mark.parametrize("site", (COLD_SITE, EV_SITE))
def test_8_mini_grid_only_site_readers_refuse_before_any_read(site):
    actual = StructureRead(Boom("leaf source"))
    actual.site_inputs = Boom("site_inputs")  # the actual side must not be read
    targets = TargetRead(Boom("budget lines"), actual)
    _refuses_key_not_read(lambda: targets.site(site, OCT, KNOWN_AT), site)
    bridge = BridgeRead(actual, targets, lambda: NOW)
    _refuses_key_not_read(lambda: bridge.site(site, OCT, KNOWN_AT), site)
    snapshots = SnapshotRead(Boom("store"), Boom("months"), Boom("kinds"), "a" * 64, lambda: NOW)
    _refuses_key_not_read(lambda: snapshots.site(TENANT, site, OCT), site)


def test_8_target_bridge_and_snapshot_portfolios_name_the_cold_site():
    import test_3b7a_structure_snapshot as t3b7a

    s = t3b7a.setup(t3b7a.lakeside())
    w, r = s.w, s.r
    kobo, cold = t3b7a.by_code(w)["KOBO-001"], t3b7a.by_code(w)["THIKA-001"]
    called: list[str] = []
    real = r.actual.site_inputs

    def recording(site, month, known_at=None):
        called.append(site.site_code)
        return real(site, month, known_at)
    r.actual.site_inputs = recording

    pt = r.targets.portfolio(w["tid"], [kobo, cold], OCT, t3b7a.AS_OF)
    assert tuple(pt.sites) == ("KOBO-001",)
    assert dict(pt.structure.composition.sites_excluded) == {"THIKA-001": OTHER_STRUCTURE}
    assert called == ["KOBO-001"]
    called.clear()
    pb = BridgeRead(r.actual, r.targets, t3b7a.Clock(t3b7a.AS_OF)).portfolio(w["tid"], [kobo, cold], OCT)
    assert tuple(pb.sites) == ("KOBO-001",) and set(called) == {"KOBO-001"}
    rows = [row for root in pb.rows.values() for row in root.values()]
    assert rows and all(("THIKA-001", OTHER_STRUCTURE) in row.out for row in rows)
    result = s.builder.build(w["tid"], [kobo, cold], OCT, built_by=t3b7a.BY)
    (stored,) = s.store.get(w["tid"], [result.portfolio_snapshot_id])
    from assetops_backend.structure_snapshot import codec

    assert dict(codec.decode_portfolio(stored, {}).sites_excluded) == {"THIKA-001": OTHER_STRUCTURE}
