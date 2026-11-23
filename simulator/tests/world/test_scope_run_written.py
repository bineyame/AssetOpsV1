"""D-DD.164 (DD3b fix round): a history seed never covers a value written back from the run it seeds.

The October keys `M` takes from a run (`scope.RUN_WRITTEN`) leave the scope digest, so writing them cannot re-seed
July-September; the history still reads them as values. A key not in the table stays in the digest (plant: Kobo
`delivered_kwh`). Every Site type is named: the three Lakeside mini-grids (the ruled guard), the cold rooms and the
depots.
"""

from __future__ import annotations

import json
from fractions import Fraction

import pytest

from assetops_simulator.world import scope as scope_module
from assetops_simulator.world.history import _Scope

from .conftest import load_fixture, site_of, tenant_of

#: Stated here, independently of `scope.RUN_WRITTEN` (D-DD.164; EV from D-DD.20 and D-DD.158).
EXPECTED = {
    "MINI_GRID": {
        "actual": ("diesel_l", "necessary_l", "candidate_l", "diesel_cost", "contribution", "variance"),
        "plan": ("diesel_l", "necessary_l", "candidate_l", "unexplained_l", "diesel_cost", "contribution", "variance"),
        "period": ("fuel_balance", "bridge", "findings_expected"),
    },
    "COLD_CHAIN": {"actual": ("kwh",)},
    "EV_DEPOT": {"actual": ("peak_kwh", "offpeak_kwh", "kwh_2200_2400", "kwh_0000_0500", "max_kw")},
}

LAKESIDE = ("Kobo", "Kisiwa", "Mto")
SITES = {
    "lakeside-power": LAKESIDE,
    "harvest-cold": ("Room A · Mwea", "Room B · Thika", "Room C · Kirinyaga"),
    "metro-bus": ("Embakasi", "Kasarani", "Ruiru"),
}


def _months(view: dict) -> list[str]:
    return sorted(view["history"]["months"])


def _fingerprint(view: dict, tenant: str, site: str) -> dict:
    """Every July-September scope digest and jitter factor of one Site."""
    tenant_doc = tenant_of(view, tenant)
    site_doc = site_of(view, tenant, site)
    out = {}
    for month in _months(view):
        scope = _Scope(view, tenant_doc, site_doc, month, True)
        factors = {name: scope._jitter(name, name) for name in sorted(view["history"]["families"])}
        out[month] = (scope.digest, factors)
    return out


def _bump(period: dict, side: str, key: str) -> None:
    """Change one period key's value (adding it when the view does not carry it)."""
    block = period if side == "period" else period.setdefault(side, {})
    old = block.get(key)
    if isinstance(old, (int, float)) and not isinstance(old, bool):
        block[key] = old + 7
    elif isinstance(old, str):
        try:
            block[key] = str(Fraction(old) + 7)
        except ValueError:
            block[key] = old + " (planted)"
    else:
        block[key] = {"planted": [old, 7]}


def test_run_written_table_is_as_ruled() -> None:
    assert scope_module.RUN_WRITTEN == EXPECTED


@pytest.mark.parametrize("tenant,site", [(t, s) for t, sites in SITES.items() for s in sites])
def test_each_run_written_key_leaves_digest_and_jitter_unchanged(tenant: str, site: str) -> None:
    base = load_fixture()
    before = _fingerprint(base, tenant, site)
    vertical = tenant_of(base, tenant)["vertical"]
    keys = [(side, key) for side, names in EXPECTED[vertical].items() for key in names]
    assert keys
    for side, key in keys:
        view = load_fixture()
        _bump(site_of(view, tenant, site)["period"], side, key)
        assert _fingerprint(view, tenant, site) == before, f"{tenant}/{site} {side}.{key} re-seeds the history"


def test_a_key_not_in_the_table_still_reseeds() -> None:
    """Plant: Kobo `delivered_kwh` is a declared input, so it stays in the digest."""
    base = load_fixture()
    before = _fingerprint(base, "lakeside-power", "Kobo")
    view = load_fixture()
    _bump(site_of(view, "lakeside-power", "Kobo")["period"], "actual", "delivered_kwh")
    after = _fingerprint(view, "lakeside-power", "Kobo")
    assert all(after[m][0] != before[m][0] for m in _months(base))


def test_history_still_reads_a_run_written_key_as_a_value() -> None:
    """`_Scope.october` reads the full period: the leaf leaves the seed, not the history's inputs."""
    view = load_fixture()
    tenant_doc = tenant_of(view, "lakeside-power")
    site_doc = site_of(view, "lakeside-power", "Kisiwa")
    month = _months(view)[0]
    before = _Scope(view, tenant_doc, site_doc, month, True).october("actual", "necessary_l")
    site_doc["period"]["actual"]["necessary_l"] += 100
    after = _Scope(view, tenant_doc, site_doc, month, True).october("actual", "necessary_l")
    assert after - before == 100


def test_period_input_drops_only_listed_keys_and_skips_missing_ones() -> None:
    site_doc = {"period": {"actual": {"diesel_l": 1, "delivered_kwh": 2}, "plan": {"diesel_l": 3}, "coverage": {}}}
    assert scope_module.period_input(site_doc, "MINI_GRID") == {
        "actual": {"delivered_kwh": 2},
        "plan": {},
        "coverage": {},
    }
    assert scope_module.period_input(site_doc, "UNKNOWN_VERTICAL") == site_doc["period"]


# --- D-DD.176: what a run-written October key may move in the history ------------------------------------------------

from decimal import Decimal  # noqa: E402

from assetops_simulator.world import history as history_module  # noqa: E402
from assetops_simulator.world import telemetry as tel  # noqa: E402
from assetops_simulator.world.history import generate_scope  # noqa: E402

#: Stated here, independently of `history.RUN_DERIVED` (D-DD.176; listed from the code's rules in pre-flight).
EXPECTED_DERIVED = {
    "MINI_GRID": ("actual.necessary_l", "actual.candidate_l", "plan.diesel_l"),
    "COLD_CHAIN": ("actual.kwh",),
    "EV_DEPOT": ("actual.peak_kwh", "actual.offpeak_kwh", "actual.kwh_2200_2400", "actual.kwh_0000_0500", "actual.max_kw"),
}


def _flat(block: dict, prefix: str = "") -> dict:
    out = {}
    for key, value in block.items():
        if isinstance(value, dict):
            out.update(_flat(value, f"{prefix}{key}."))
        else:
            out[f"{prefix}{key}"] = value
    return out


def _history_paths(view: dict, tenant: str, site: str) -> dict:
    return {m: _flat(generate_scope(view, tenant, site, m)) for m in _months(view)}


def _bump_value(period: dict, side: str, key: str) -> bool:
    """Change one present period value, keeping its type (a decimal string stays one); False when absent."""
    block = period if side == "period" else period.get(side, {})
    old = block.get(key)
    if isinstance(old, bool) or old is None:
        return False
    if isinstance(old, (int, float)):
        block[key] = old + 7
    elif isinstance(old, str):
        block[key] = str(Decimal(old) + 7)
    else:
        return False
    return True


def _stray_paths(tenant: str, site: str) -> list[str]:
    """Every history path that a run-written key moved outside `RUN_DERIVED`, plus any physical read that moved."""
    base = load_fixture()
    vertical = tenant_of(base, tenant)["vertical"]
    derived = set(history_module.RUN_DERIVED[vertical])
    before = _history_paths(base, tenant, site)
    rules = scope_module.merged_rules(base["history"], vertical, tenant, site)
    physical = scope_module.physical_read(site_of(base, tenant, site), rules)
    stray, bumped = [], 0
    for side, keys in scope_module.RUN_WRITTEN[vertical].items():
        for key in keys:
            view = load_fixture()
            if not _bump_value(site_of(view, tenant, site)["period"], side, key):
                continue
            bumped += 1
            after = _history_paths(view, tenant, site)
            for month in after:
                for path in set(after[month]) | set(before[month]):
                    if after[month].get(path) != before[month].get(path):
                        if path not in derived:
                            stray.append(f"{side}.{key} -> {month} {path}")
            if scope_module.physical_read(site_of(view, tenant, site), rules) != physical:
                stray.append(f"{side}.{key} -> physical")
    if tenant == "lakeside-power":  # the ruled Sites carry their run-written leaves (Kasarani carries none)
        assert bumped, f"{tenant}/{site}: no run-written key present"
    return stray


SIDES_HISTORY = ("plan", "actual")


def test_run_derived_table_is_as_ruled_and_never_read_back() -> None:
    assert history_module.RUN_DERIVED == EXPECTED_DERIVED
    physical = {k for keys in scope_module.PHYSICAL_READS.values() for k in keys} | set(scope_module.PHYSICAL_READS)
    for vertical, keys in history_module.RUN_DERIVED.items():
        leaves = {path.split(".")[1] for path in keys}
        assert not leaves & physical
        assert not leaves & set(history_module.WRITER_READS[vertical])


def test_the_import_check_refuses_a_derived_key_a_writer_reads(monkeypatch) -> None:
    monkeypatch.setitem(history_module.RUN_DERIVED, "MINI_GRID", ("actual.necessary_l", "actual.delivered_kwh"))
    with pytest.raises(ValueError, match="RUN_DERIVED_READ_BACK MINI_GRID delivered_kwh"):
        history_module._run_derived_is_never_read_back()


@pytest.mark.parametrize("tenant,site", [(t, s) for t, sites in SITES.items() for s in sites])
def test_a_run_written_key_moves_only_run_derived_history_paths(tenant: str, site: str) -> None:
    assert _stray_paths(tenant, site) == []


def test_lakesides_run_written_keys_move_the_scaled_litres() -> None:
    """Non-empty: the guard's set is real (Kisiwa's necessary and candidate litres follow October's)."""
    view = load_fixture()
    before = _history_paths(view, "lakeside-power", "Kisiwa")
    site_of(view, "lakeside-power", "Kisiwa")["period"]["actual"]["necessary_l"] += 100
    after = _history_paths(view, "lakeside-power", "Kisiwa")
    assert all(after[m]["actual.necessary_l"] > before[m]["actual.necessary_l"] for m in after)


def test_plant_a_rule_that_also_scales_delivered_kwh_fails_the_guard(monkeypatch) -> None:
    """Plant: `delivered_kwh` made to follow October's necessary litres is caught."""
    real = history_module._value

    def planted(scope, side, leaf, tokens, made):
        value = real(scope, side, leaf, tokens, made)
        if leaf == "delivered_kwh" and side == "actual":
            return value * scope.october("actual", "necessary_l") / 100
        return value

    monkeypatch.setattr(history_module, "_value", planted)
    stray = _stray_paths("lakeside-power", "Kobo")
    assert any(path.endswith("actual.delivered_kwh") for path in stray), stray


def test_the_writers_read_no_run_derived_history_value() -> None:
    """`WRITER_READS` is the code's: changing every `RUN_DERIVED` value in the history leaves the books unchanged."""
    from assetops_simulator.world.telemetry_cold import cold_books_for

    from .books_support import built

    view, history, records, _ = built()

    def bumped() -> dict:
        out = json.loads(json.dumps(history))
        for tenant_doc in view["tenants"]:
            derived = history_module.RUN_DERIVED[tenant_doc["vertical"]]
            for months in out["tenants"][tenant_doc["tenant"]].values():
                for block in months.values():
                    for path in derived:
                        side, key = path.split(".")
                        if key in block[side]:
                            block[side][key] += 7
        return out

    planted = bumped()
    assert planted != history
    assert tel.books_for(view, planted, {"lakeside-power": ""}) == tel.books_for(view, history, {"lakeside-power": ""})
    assert cold_books_for(view, planted, records) == cold_books_for(view, history, records)
