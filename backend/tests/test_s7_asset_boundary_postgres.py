"""S7-01a phase 2: configured-battery boundary read over the effective S1 Site basis.

Configured battery with missing causal inputs (KOBO-001 with its binding set), configured but
unbound battery (an import without a binding set), absent battery (a Site whose Foundation has no
BATTERY component) and wrong asset / wrong Site refusals. Basis and binding IDs are pinned after reload.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    import yaml
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_s1_bindings_postgres import KOBO_SOURCE, NOW, Clock, converted, engine, imported, store  # noqa: F401

    from assetops_backend.asset_boundary_api import build_asset_boundary_router
    from assetops_backend.sites.adapters.import_files import read_import_source
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.foundation_records import FoundationStoreUnavailable
    from assetops_backend.sites.foundation_service import FoundationService, ImportSource, import_site
    from assetops_backend.sites.battery_boundary import WITHHELD

    from datetime import timedelta


def without_battery(store, tmp_path, code="KOBO-NB"):
    """Import a Site whose effective Foundation has no BATTERY component."""
    doc = yaml.safe_load(KOBO_SOURCE.read_text(encoding="utf-8"))
    doc["site_id"] = code
    f = doc["foundation"]
    f["components"] = [c for c in f["components"] if c["component_id"] != "battery"]
    topology = f["topology"]
    topology["nodes"] = [n for n in topology["nodes"] if n["node_id"] != "battery"]
    topology["connections"] = [c for c in topology["connections"] if "battery" not in (c["from_node"], c["to_node"])]
    f["signal_mappings"] = [m for m in f["signal_mappings"] if m.get("component_id") != "battery"]
    for device in f["devices"]:
        device["signals"] = [s for s in device["signals"] if s["signal_id"] != "state-of-charge"]
    for control in f.get("site_controls", ()):
        if "members" in control:
            control["members"] = [m for m in control["members"] if m != "battery"]
    path = tmp_path / f"{code.lower()}.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    source = read_import_source(str(path))
    return import_site(store, tenant_slug="demo", configured_tenant_slug="demo",
                       source=ImportSource(path=f"var/sites/{code.lower()}.yaml", sha256=source.sha256,
                                           record=source.record),
                       legacy_documents=(), clock=Clock(NOW - timedelta(hours=2)))


def client(store, access=None) -> TestClient:
    app = FastAPI()
    registry = ImportedSiteRegistry(FoundationService(store, "demo", Clock(NOW)))
    app.include_router(build_asset_boundary_router(registry, **({} if access is None else {"access": access})))
    return TestClient(app)


@pytest.fixture()
def sites(store, tmp_path):
    configured, outcome = converted(store)
    unbound = imported(store, code="KOBO-UB")
    absent = without_battery(store, tmp_path)
    return configured, outcome, unbound, absent


class TestBatteryBoundary:
    def test_configured_battery_is_unknown_with_missing_causal_inputs_and_pinned_ids(self, store, sites) -> None:
        configured, outcome, _, _ = sites
        api = client(store)
        entry = api.get("/api/sites/KOBO-001/battery").json()
        assert entry["schema"] == {"id": "assetops.asset-boundary", "version": 1}
        assert entry["configuration"] == "CONFIGURED"
        [battery] = entry["batteries"]
        assert battery["asset_code"] == "battery"
        detail = api.get(battery["detail_path"])
        assert detail.status_code == 200
        body = detail.json()
        binding_set = outcome.published.changed
        assert body["basis"]["binding_set_revision_id"] == str(binding_set.id)
        assert body["basis"]["foundation_revision_id"] == str(binding_set.foundation_revision_id)
        assert body["binding_status"] == "BOUND"
        [soc] = body["bound_channels"]
        expected = next(b for b in binding_set.bindings if b.role == "battery_soc")
        assert soc["role"] == "battery_soc" and soc["binding_revision_id"] == str(expected.id)
        assert soc["label"] == "BOUND_CHANNEL_NOT_A_CONDITION_INPUT"
        condition = body["physical_condition"]
        assert condition["status"] == "UNKNOWN" and condition["reason"] == "NO_REVIEWED_CAUSAL_BATTERY_RULE"
        assert {m["input"] for m in condition["missing_causal_inputs"]} == {
            "ACCEPTED_BATTERY_TEMPERATURE_HISTORY", "ACCEPTED_MEASURED_CAPACITY", "ACCEPTED_CYCLE_STRESS_HISTORY"}
        assert body["declared_nameplate"]["label"] == "DECLARED_FOUNDATION_RATING"
        assert body["declared_nameplate"]["value"] == 200.0 and body["declared_nameplate"]["unit"] == "kWh"
        assert body["accepted_state_of_charge"]["included"] is False
        assert body["withheld"] == WITHHELD
        for word in ("degradation", "remaining_life", "warranty", "replacement", "stress_score", "diagnosis"):
            assert word not in {k.lower() for k in body}
        # Reload pins the same basis, asset and binding IDs.
        again = client(store).get(battery["detail_path"]).json()
        assert {k: again[k] for k in ("basis", "asset", "bound_channels")} == {
            k: body[k] for k in ("basis", "asset", "bound_channels")}

    def test_configured_but_unbound_battery(self, store, sites) -> None:
        _, _, unbound, _ = sites
        api = client(store)
        [battery] = api.get("/api/sites/KOBO-UB/battery").json()["batteries"]
        body = api.get(battery["detail_path"]).json()
        assert body["binding_status"] == "NO_BINDING_SET" and body["bound_channels"] == []
        assert body["basis"]["binding_set_revision_id"] is None
        assert body["physical_condition"]["status"] == "UNKNOWN"
        assert body["physical_condition"]["reason"] == "NO_BINDING_SET"

    def test_absent_battery_is_not_configured_without_an_asset_id(self, store, sites) -> None:
        body = client(store).get("/api/sites/KOBO-NB/battery").json()
        assert body["configuration"] == "NOT_CONFIGURED" and body["batteries"] == []
        assert body["reason"] == "NO_BATTERY_IN_EFFECTIVE_FOUNDATION"
        assert body["physical_condition"] == {"status": "UNKNOWN", "reason": "NOT_CONFIGURED",
                                              "missing_causal_inputs": []}
        assert "asset" not in body

    def test_wrong_asset_and_wrong_site_are_refused(self, store, sites) -> None:
        configured, _, unbound, _ = sites
        api = client(store)
        foreign = api.get("/api/sites/KOBO-UB/battery").json()["batteries"][0]["asset_id"]
        own = api.get("/api/sites/KOBO-001/battery").json()["batteries"][0]["asset_id"]
        pcs = next(a.id for a in store.registrations(configured.tenant.id, configured.site.id).assets
                   if a.asset_code == "battery-pcs")
        for asset in (foreign, pcs, uuid4()):
            answer = api.get(f"/api/sites/KOBO-001/assets/{asset}/battery")
            assert answer.status_code == 404
            assert answer.json()["detail"]["code"] == "ASSET_NOT_IN_EFFECTIVE_BASIS"
            assert answer.json()["detail"]["physical_condition"] is None
        assert api.get("/api/sites/KOBO-001/assets/not-a-uuid/battery").status_code == 422
        assert api.get(f"/api/sites/NOT-A-SITE/assets/{own}/battery").status_code == 404
        assert api.get("/api/sites/NOT-A-SITE/battery").status_code == 404

    def test_identity_seam_and_store_failure(self, store, sites) -> None:
        assert client(store, access=lambda r, c: 401).get("/api/sites/KOBO-001/battery").status_code == 401
        assert client(store, access=lambda r, c: 403).get("/api/sites/KOBO-001/battery").status_code == 403

        class Down:
            def __getattr__(self, name):
                def fail(*args, **kwargs):
                    raise FoundationStoreUnavailable("store down")
                return fail

        answer = client(Down()).get("/api/sites/KOBO-001/battery")
        assert answer.status_code == 503
        assert answer.json()["detail"]["code"] == "ASSET_BOUNDARY_UNAVAILABLE"


    def test_binding_set_of_another_foundation_revision_is_refused(self, store, sites, monkeypatch) -> None:
        """S7-01a review L6: a binding set naming another Foundation revision fails closed (409)."""
        from dataclasses import replace

        configured, _, _, _ = sites
        api = client(store)
        [battery] = api.get("/api/sites/KOBO-001/battery").json()["batteries"]
        real_read = FoundationService.read

        def mismatched(self, *args, **kwargs):
            view = real_read(self, *args, **kwargs)
            return replace(view, binding_set=replace(view.binding_set, foundation_revision_id=uuid4()))

        monkeypatch.setattr(FoundationService, "read", mismatched)
        answer = api.get(battery["detail_path"])
        assert answer.status_code == 409
        assert answer.json()["detail"]["code"] == "FOUNDATION_BASIS_UNAVAILABLE"
        assert answer.json()["detail"]["physical_condition"] is None
        assert "bound_channels" not in answer.text

class TestComposition:
    def test_create_app_serves_both_s7_reads(self, store, sites, tmp_path) -> None:
        import shutil

        from test_s1_foundation_postgres import app_for

        from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess

        root = tmp_path / "legacy"
        root.mkdir()
        shutil.copy(KOBO_SOURCE, root / "kobo-001.yaml")
        access = PostgresGatewayAccess(URL)
        try:
            api = app_for(store, root, gateway_access=access, gateway_clock=Clock(NOW))
            health = api.get("/api/sites/KOBO-001/source-health")
            assert health.status_code == 200 and health.json()["schema"]["id"] == "assetops.site-source-health"
            assert health.json()["summary"]["status"] == "NO_REGISTERED_SOURCE"
            battery = api.get("/api/sites/KOBO-001/battery")
            assert battery.status_code == 200 and battery.json()["configuration"] == "CONFIGURED"
            assert api.get(battery.json()["batteries"][0]["detail_path"]).status_code == 200
            assert api.get("/api/sites/NOT-A-SITE/source-health").status_code == 404
        finally:
            if access._engine is not None:
                access._engine.dispose()
