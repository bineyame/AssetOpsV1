"""2a: the leaf factor catalogue against the pack manifest (spec §9, T1-T4).

The independent check (W2): it reads only the manifest and the public names of
`assetops_contracts.canonical`. It shares no list with `factors.py`: the leaf IDs
come from the manifest's `factor_map`, the kinds from `KINDS` and `KIND_SPECS`.
It needs `yaml`; without it the import fails, never skips.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from assetops_contracts.canonical import (
    DAY,
    HOUR,
    KINDS,
    KIND_SPECS,
    KWH,
    LEAF_FACTORS,
    MINUTE,
    MONEY,
    STRUCTURE_KEYS,
    leaves_of,
)

MANIFEST = (
    Path(__file__).resolve().parents[2]
    / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml"
)

# The existing operational kinds a leaf may name outside version 1 (T3).
OUTSIDE_KINDS = frozenset({"FUEL_DELIVERY", "TANK_DIP", "work case"})


def _manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def test_t1_leaves_equal_factor_map_per_structure_key():
    factor_map = _manifest()["factor_map"]
    assert set(factor_map) == set(STRUCTURE_KEYS)
    for key in STRUCTURE_KEYS:
        assert set(leaves_of(key)) == set(factor_map[key]), key
        assert len(leaves_of(key)) == len(set(leaves_of(key))), key
    union = set().union(*(set(leaves_of(key)) for key in STRUCTURE_KEYS))
    assert union == set(LEAF_FACTORS)
    for factor_id, factor in LEAF_FACTORS.items():
        assert factor.id == factor_id
        assert factor.structures, factor_id
        assert factor.structures <= set(STRUCTURE_KEYS), factor_id
    assert len(LEAF_FACTORS) == 73


def test_t1_unknown_structure_key_raises_key_error():
    try:
        leaves_of("EV_DEPOT")
    except KeyError:
        return
    raise AssertionError("leaves_of accepted an unknown structure key")


def test_t2_shared_ids_are_one_factor_holding_every_key():
    factor_map = _manifest()["factor_map"]
    seen: dict[str, set[str]] = {}
    for key, leaves in factor_map.items():
        for factor_id in leaves:
            seen.setdefault(factor_id, set()).add(key)
    shared = {factor_id: keys for factor_id, keys in seen.items() if len(keys) > 1}
    assert shared, "the manifest holds no shared leaf; the check would prove nothing"
    for factor_id, keys in seen.items():
        assert LEAF_FACTORS[factor_id].structures == frozenset(keys), factor_id


def test_t3_leaf_sources_name_v1_kinds_or_the_existing_operational_kinds():
    leaf_sources = _manifest()["empty_states"]["leaf_sources"]
    checked = {"COMMERCIAL_RECORD": 0, "OPERATIONAL_RECORD": 0, "DOCUMENT": 0}
    for key, rows in leaf_sources.items():
        for factor_id, row in rows.items():
            family = row["family"]
            named = str(row["kind"]).split(" (", 1)[0]
            where = f"{key}.{factor_id}: {row['kind']}"
            if family in ("COMMERCIAL_RECORD", "OPERATIONAL_RECORD"):
                checked[family] += 1
                assert named in KINDS or named in OUTSIDE_KINDS, where
                if named in KINDS:
                    assert KIND_SPECS[named].store_family == family, where
                if named == "SERVICE_TICKET":
                    assert KIND_SPECS[named].store_family == "OPERATIONAL_RECORD", where
            elif family == "DOCUMENT":
                checked[family] += 1
                assert named == "CONTRACT_DOCUMENT", where
                assert named in KINDS, where
    assert all(checked.values()), checked


def _u(factor_id: str):
    return LEAF_FACTORS[factor_id].unit


def test_t4_unit_composition_of_hand_listed_terms():
    money_terms = [
        ("tariff", "delivered_kwh"),
        ("diesel_price", "candidate_l"),
        ("battery_throughput_kwh", "wear_rate"),
        ("crate_days", "rate"),
        ("elec_price", "excess_kwh"),
        ("peak_kwh", "peak_price"),
        ("max_kw", "demand_rate"),
        ("spare_bus_nights", "penalty_rate"),
    ]
    for a, b in money_terms:
        assert _u(a) * _u(b) == MONEY, (a, b, str(_u(a) * _u(b)))
        assert (_u(a) * _u(b)).is_money
    assert _u("reduced_days") * _u("hours_per_day") == HOUR
    assert _u("k_kwh_per_crate_day") * _u("crate_days") == KWH
    assert _u("period_days") * _u("minutes_per_day") == MINUTE
    assert _u("chargers_in_service") * _u("charger_kw") == _u("import_limit_kw")
    assert _u("charger_kw") * _u("window_h") == _u("kwh_per_bus_night")
    assert _u("buses") * _u("nights_in_period") == _u("spare_bus_nights")
    assert _u("spare_bus_nights") == DAY
