"""D-DD.102 (DD3a fix round): a scope digest covers only the `physical` keys its rules read.

Shared behaviour, every Site type named: the cold rooms (no `physical` block) stay byte-identical to main; a
mini-grid Site's kit (no rule reads it) and a depot's unread keys never re-seed a history; a depot's read keys
(`buses`, `kwh_per_bus_night`) move only that depot's scopes.
"""

from __future__ import annotations

import json

import pytest

from assetops_simulator.world import history as history_module
from assetops_simulator.world import scope as scope_module
from assetops_simulator.world.canonical import canonical_bytes, sha256_hex
from assetops_simulator.world.history import generate_history
from assetops_simulator.world.scope import merged_rules, scope_input

from .conftest import HERE, REPOSITORY_ROOT, load_fixture, scope_blocks, site_of, tenant_of

COLD_GOLDEN = HERE / "golden" / "physical_reads_cold_main.json"
HISTORY_JSON = REPOSITORY_ROOT / "Docs" / "demo-sprint" / "product-direction-layer4" / "history.json"

#: Stated here, independently of `scope.PHYSICAL_READS`: the keys each vertical's rules read today.
READ_SETS = {"MINI_GRID": set(), "EV_DEPOT": {"buses", "kwh_per_bus_night"}, "COLD_CHAIN": set()}
#: Main's Kobo kit (before DD3a's data sheets), D-DD.102's named kit-invariance case.
MAIN_KOBO_KIT = {"genset_kw": 40, "sfc_l_per_kwh": "0.30", "battery_kwh": 200}

SITES = {
    "lakeside-power": ("Kobo", "Kisiwa", "Mto"),
    "metro-bus": ("Embakasi", "Kasarani", "Ruiru"),
    "harvest-cold": ("Room A · Mwea", "Room B · Thika", "Room C · Kirinyaga"),
}


def _sha(block: dict) -> str:
    return sha256_hex(canonical_bytes(block))


def _cold(blocks: dict) -> dict:
    return {k: v for k, v in blocks.items() if k.startswith("harvest-cold/")}


def _golden() -> dict:
    return json.loads(COLD_GOLDEN.read_text(encoding="utf-8"))


# ---- cold: unchanged from main ---------------------------------------------------------


def test_cold_fixture_scopes_equal_main() -> None:
    cold = _cold(scope_blocks(generate_history(load_fixture())))
    expected = _golden()["fixture_view"]
    assert len(cold) == 9
    assert {k: {"scope_digest": b["scope_digest"], "block_sha256": _sha(b)} for k, b in cold.items()} == expected


def test_cold_history_json_blocks_equal_main() -> None:
    cold = _cold(scope_blocks(json.loads(HISTORY_JSON.read_text(encoding="utf-8"))))
    expected = _golden()["history_json"]
    assert len(cold) == 9
    assert {k: {"scope_digest": b["scope_digest"], "block_sha256": _sha(b)} for k, b in cold.items()} == expected


# ---- kit invariance: unread keys never re-seed ----------------------------------------


def _with_physical(view: dict, tenant: str, site: str, change) -> dict:
    site_doc = site_of(view, tenant, site)
    site_doc["physical"] = change(dict(site_doc["physical"]))
    return view


@pytest.mark.parametrize("tenant,site", [(t, s) for t in ("lakeside-power", "metro-bus") for s in SITES[t]])
def test_unread_keys_changed_leave_every_block_identical(tenant: str, site: str) -> None:
    base = generate_history(load_fixture())
    view = load_fixture()
    read = READ_SETS[tenant_of(view, tenant)["vertical"]]
    unread = sorted(set(site_of(view, tenant, site)["physical"]) - read)
    assert unread, f"{site} has no unread physical key to change"

    def change(physical: dict) -> dict:
        for key in unread:
            physical[key] = ["changed", physical[key]]
        physical["added_by_a_future_sheet"] = 1
        return physical

    after = generate_history(_with_physical(view, tenant, site, change))
    assert canonical_bytes(after) == canonical_bytes(base)


def test_kobo_main_kit_leaves_every_block_identical() -> None:
    base = generate_history(load_fixture())
    view = _with_physical(load_fixture(), "lakeside-power", "Kobo", lambda p: {**p, **MAIN_KOBO_KIT})
    assert canonical_bytes(generate_history(view)) == canonical_bytes(base)


def test_history_json_is_the_fixture_views_history() -> None:
    """The committed history.json is what the fixture view generates, so kit invariance holds for its blocks too."""
    assert canonical_bytes(json.loads(HISTORY_JSON.read_text(encoding="utf-8"))) == canonical_bytes(
        generate_history(load_fixture()))


# ---- read sensitivity: a read key moves only its own Site ------------------------------


def test_embakasi_buses_move_only_embakasi() -> None:
    base = scope_blocks(generate_history(load_fixture()))
    view = _with_physical(load_fixture(), "metro-bus", "Embakasi", lambda p: {**p, "buses": int(p["buses"]) + 1})
    after = scope_blocks(generate_history(view))
    moved = {k for k in base if base[k]["scope_digest"] != after[k]["scope_digest"]}
    assert moved == {f"metro-bus/Embakasi/{m}" for m in ("2026-07", "2026-08", "2026-09")}


# ---- the digest input itself ------------------------------------------------------------


def _inputs(view: dict, tenant: str, site: str, month: str = "2026-07") -> dict:
    tenant_doc = tenant_of(view, tenant)
    site_doc = site_of(view, tenant, site)
    rules = merged_rules(view["history"], tenant_doc["vertical"], tenant, site)
    return scope_input(view, tenant_doc, site_doc, month, rules)


@pytest.mark.parametrize("site", SITES["lakeside-power"])
def test_mini_grid_scope_input_has_no_physical(site: str) -> None:
    assert "physical" not in _inputs(load_fixture(), "lakeside-power", site)["site"]


@pytest.mark.parametrize("site", SITES["harvest-cold"])
def test_cold_scope_input_has_no_physical(site: str) -> None:
    assert "physical" not in _inputs(load_fixture(), "harvest-cold", site)["site"]


@pytest.mark.parametrize("site", SITES["metro-bus"])
def test_depot_scope_input_holds_only_the_read_keys(site: str) -> None:
    view = load_fixture()
    physical = site_of(view, "metro-bus", site)["physical"]
    assert _inputs(view, "metro-bus", site)["site"]["physical"] == {k: physical[k] for k in sorted(READ_SETS["EV_DEPOT"])}


def test_physical_reads_table_is_declared() -> None:
    assert scope_module.PHYSICAL_READS == {"fleet_kwh": ("buses", "kwh_per_bus_night"), "fleet_nights": ("buses",)}


def test_a_read_not_declared_for_its_word_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    """The table cannot drift from the reads: a rule reading an undeclared key refuses (HISTORY_RULE_REF)."""
    monkeypatch.setattr(scope_module, "PHYSICAL_READS", {"fleet_kwh": ("buses",), "fleet_nights": ("buses",)})
    with pytest.raises(ValueError, match=r"^HISTORY_RULE_REF metro-bus/"):
        generate_history(load_fixture())


def test_history_reads_through_the_restricted_dict() -> None:
    assert history_module.physical_read is scope_module.physical_read
