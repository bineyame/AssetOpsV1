"""D-DD.164 (DD3b fix round): a history seed never covers a value written back from the run it seeds.

The October keys `M` takes from a run (`scope.RUN_WRITTEN`) leave the scope digest, so writing them cannot re-seed
July-September; the history still reads them as values. A key not in the table stays in the digest (plant: Kobo
`delivered_kwh`). Every Site type is named: the three Lakeside mini-grids (the ruled guard), the cold rooms and the
depots.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from assetops_simulator.world import scope as scope_module
from assetops_simulator.world.history import _Scope

from .conftest import load_fixture, site_of, tenant_of

#: Stated here, independently of `scope.RUN_WRITTEN` (D-DD.164; EV from D-DD.20 and D-DD.158).
EXPECTED = {
    "MINI_GRID": {
        "actual": ("diesel_l", "necessary_l", "candidate_l", "diesel_cost", "contribution", "variance"),
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
        "plan": {"diesel_l": 3},
        "coverage": {},
    }
    assert scope_module.period_input(site_doc, "UNKNOWN_VERTICAL") == site_doc["period"]
