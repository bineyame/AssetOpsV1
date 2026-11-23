"""D-DD.90 (DD4a): November is declared `short_rains` in `M`'s one season map, and a scope digest covers only the
history's months plus the anchor, so every scope digest stays byte-identical to main's.

The golden (`golden/scope_seasons_main.json`) was written from main at DD3a's merge (759759598), before D-DD.90: every
scope digest of the fixture view and the sha256 of history.json's scope blocks. `meta.view_digest` covers the whole
view by design (DS1), so it moves with the new key; the packet records it (D-DD.90: "the packet lists any pin that
moves").

Re-pinned at DD3b3 (D-DD.131/150/151, M rev 16.20): October's Lakeside litres moved in `period.actual`, which every scope
digest of a Lakeside Site reads, so the Lakeside scope digests were re-drawn once and the golden holds the regenerated
values (D-DD.30 chain, D-DD.93 rule); the depots' and cold rooms' digests are main's still.

Re-pinned at the DD3b fix round (D-DD.164, 2026-11-23): `scope.RUN_WRITTEN` leaves every scope digest, so all 27
digests were re-drawn once from the tool; the D-DD.90 property (a season past the anchor moves none) is unchanged.
"""

from __future__ import annotations

import json

import yaml

from assetops_simulator.world import telemetry as tel
from assetops_simulator.world.canonical import canonical_bytes, sha256_hex
from assetops_simulator.world.history import generate_history
from assetops_simulator.world.scope import merged_rules, scope_input
from assetops_simulator.world.view import ManifestView

from .conftest import HERE, REPOSITORY_ROOT, load_fixture, site_of, tenant_of

GOLDEN = json.loads((HERE / "golden" / "scope_seasons_main.json").read_text(encoding="utf-8"))
LAYER4 = REPOSITORY_ROOT / "Docs" / "demo-sprint" / "product-direction-layer4"


def _manifest() -> dict:
    return yaml.safe_load((LAYER4 / "demo-site-scenario-manifest.yaml").read_text(encoding="utf-8"))


def _digests(history: dict) -> dict:
    return {f"{t}/{s}/{m}": b["scope_digest"] for t, sites in history["tenants"].items()
            for s, months in sites.items() for m, b in months.items()}


def test_m_declares_november_short_rains_and_the_fixture_is_ms_view() -> None:
    manifest = _manifest()
    assert manifest["history"]["seasons"]["2026-11"] == "short_rains"
    assert canonical_bytes(ManifestView.from_document(manifest)) == canonical_bytes(load_fixture())


def test_every_scope_digest_of_the_fixture_view_equals_mains() -> None:
    view = load_fixture()
    assert "2026-11" in view["history"]["seasons"]
    digests = _digests(generate_history(view))
    assert len(digests) == 27
    assert digests == GOLDEN["scope_digests"]


def test_a_season_planted_past_the_anchor_moves_no_scope_digest() -> None:
    view = load_fixture()
    view["history"]["seasons"]["2027-01"] = "cool_dry"
    assert _digests(generate_history(view)) == GOLDEN["scope_digests"]


def test_history_json_scope_blocks_equal_mains() -> None:
    history = json.loads((LAYER4 / "history.json").read_text(encoding="utf-8"))
    assert sha256_hex(canonical_bytes(history["tenants"])) == GOLDEN["tenants_sha256"]
    assert _digests(history) == GOLDEN["scope_digests"]


def test_the_scope_reads_seasons_of_its_months_and_anchor_only() -> None:
    view = load_fixture()
    tenant = tenant_of(view, "harvest-cold")
    site = site_of(view, "harvest-cold", "Room B · Thika")
    rules = merged_rules(view["history"], tenant["vertical"], tenant["tenant"], site["site"])
    seasons = scope_input(view, tenant, site, "2026-07", rules)["history_global"]["seasons"]
    assert sorted(seasons) == ["2026-07", "2026-08", "2026-09", "2026-10"]


def test_the_default_sun_table_follows_ms_seasons() -> None:
    assert tel.DEFAULT_SUN_WEIGHTS["seasons"] == _manifest()["history"]["seasons"]
