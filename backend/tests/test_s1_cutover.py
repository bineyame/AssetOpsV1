"""S1-01 cutover, Foundation API and Lab gate - default suite, no database.

These run on every `pytest` (review M2) over `InMemoryFoundationStore`, a fake
of the `FoundationStore` port. They cover the read router, the Foundation
read/versions/publish API, tenant isolation at the API layer, the legacy
surfaces' refusals (Evidence, Overview, analytics, ingestion), and every Lab
write route. PostgreSQL itself (constraint, triggers, foreign keys, migration
from zero) is tested in `test_s1_foundation_postgres.py`.
"""

from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from foundation_fakes import InMemoryFoundationStore
from run_fixtures import FakeSites, setup_request, site as fixture_site
from test_run_execution_api import FakeExecution, persisted_draft
from test_run_stage_api import a_view
from test_sites_api import FakeCatalog, request_body

from assetops_backend.config import FeatureFlags
from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore
from assetops_backend.main import create_app
from assetops_backend.sites.adapters.composite_site_repository import CompositeSiteRepository
from assetops_backend.sites.adapters.import_files import check_report_path, read_import_source
from assetops_backend.sites.adapters.yaml_shipped_site_store import ReadOnlyYamlSiteStore
from assetops_backend.sites.adapters.yaml_user_site_store import USER_SITE_STORE_ROOT, WritableYamlSiteStore
from assetops_backend.sites.foundation_service import (
    FoundationRefused,
    FoundationService,
    ImportConflict,
    ImportSource,
    LegacyDocument,
    import_site,
)
from assetops_backend.sites.ports import SiteConfigurationInvalid

BACKEND = Path(__file__).resolve().parents[1]
KOBO_SOURCE = BACKEND / "tests" / "fixtures" / "s1" / "kobo-001.yaml"
KOBO_PATH = "var/sites/kobo-001.yaml"
NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
OFF = FeatureFlags(simulator_lab_enabled=False)
ON = FeatureFlags(simulator_lab_enabled=True)


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def kobo_source(path: str = KOBO_PATH, sha256: str | None = None) -> ImportSource:
    source = read_import_source(str(KOBO_SOURCE))
    return ImportSource(path=path, sha256=sha256 or source.sha256, record=source.record)


def do_import(store, source=None, *, tenant="demo", configured="demo", legacy=(), when=None):
    return import_site(
        store,
        tenant_slug=tenant,
        configured_tenant_slug=configured,
        source=source or kobo_source(),
        legacy_documents=legacy,
        clock=Clock(when or NOW - timedelta(hours=1)),
    )


@pytest.fixture()
def legacy_root(tmp_path):
    root = tmp_path / "sites"
    root.mkdir()
    shutil.copy(KOBO_SOURCE, root / "kobo-001.yaml")
    other = KOBO_SOURCE.read_text(encoding="utf-8").replace("site_id: KOBO-001", "site_id: MG-LEGACY-1")
    (root / "mg-legacy-1.yaml").write_text(other, encoding="utf-8")
    return root


def kobo_documents():
    return (LegacyDocument("KOBO-001", KOBO_PATH, kobo_source().sha256),)


def app_for(store, legacy_root, clock=None, **overrides) -> TestClient:
    legacy = CompositeSiteRepository(
        shipped=ReadOnlyYamlSiteStore(legacy_root), user=WritableYamlSiteStore(legacy_root / "user")
    )
    return TestClient(
        create_app(
            overrides.pop("flags", OFF),
            site_repository=overrides.pop("site_repository", legacy),
            foundation_store=store,
            foundation_clock=clock or Clock(NOW),
            legacy_documents=overrides.pop("legacy_documents", kobo_documents),
            **overrides,
        )
    )


RESERVE = {"asset_code": "battery", "property_key": "reserve-state-of-charge", "unit": "%"}


# --- M1: a migrated store with no tenant row serves the legacy Sites ----------


class TestNoTenantYet:
    def test_legacy_sites_serve_when_nothing_has_been_imported(self, legacy_root) -> None:
        client = app_for(InMemoryFoundationStore(), legacy_root)
        sites = client.get("/api/sites")
        assert sites.status_code == 200
        assert [(s["site_id"], s["configuration_store"]) for s in sites.json()["sites"]] == [
            ("KOBO-001", "LEGACY_FILE"), ("MG-LEGACY-1", "LEGACY_FILE"),
        ]
        assert client.get("/api/sites/MG-LEGACY-1").status_code == 200
        assert client.get("/api/sites/MG-LEGACY-1/overview").status_code != 503
        versions = client.get("/api/sites/MG-LEGACY-1/foundation/versions")
        assert versions.status_code == 409
        assert versions.json()["detail"]["code"] == "FOUNDATION_MIGRATION_REQUIRED"

    def test_an_unreachable_store_still_fails_closed(self, legacy_root) -> None:
        client = app_for(InMemoryFoundationStore(unavailable=True), legacy_root)
        assert client.get("/api/sites").status_code == 503
        assert client.get("/api/sites/MG-LEGACY-1/foundation").status_code == 503


# --- import (domain) -------------------------------------------------------------


class TestImportRules:
    def test_reimport_is_idempotent_and_conflicts_write_nothing(self) -> None:
        store = InMemoryFoundationStore()
        first = do_import(store)
        again = do_import(store, when=NOW)
        assert not again.created and (again.site.id, again.revision.id) == (first.site.id, first.revision.id)
        with pytest.raises(ImportConflict, match="changed"):
            do_import(store, kobo_source(sha256="0" * 64))
        with pytest.raises(ImportConflict, match="different source"):
            do_import(store, kobo_source(path="elsewhere/kobo.yaml"))
        with pytest.raises(ImportConflict, match="tenant"):
            do_import(store, tenant="other")
        with pytest.raises(ImportConflict, match="also declared"):
            do_import(InMemoryFoundationStore(), legacy=(LegacyDocument("kobo-001", "config/sites/k.yaml", "f" * 64),))
        assert len(store.sites) == 1 and len(store.rows[first.site.id]) == 1

    def test_ten_assets_eight_sources_and_a_pending_gateway(self) -> None:
        result = do_import(InMemoryFoundationStore())
        regs = result.registrations
        assert len(regs.assets) == 10 and len(regs.sources) == 8
        assert regs.gateways[0].gateway_external_id == "edge-kobo-001"
        assert regs.gateways[0].credential_ref is None


# --- read router and Foundation API ---------------------------------------------


class TestReadRouterAndApi:
    def test_index_lists_the_imported_site_once(self, legacy_root) -> None:
        store = InMemoryFoundationStore()
        imported = do_import(store)
        client = app_for(store, legacy_root)
        sites = client.get("/api/sites").json()["sites"]
        assert [(s["site_id"], s["configuration_store"]) for s in sites] == [
            ("KOBO-001", "POSTGRES"), ("MG-LEGACY-1", "LEGACY_FILE"),
        ]
        assert client.get("/api/sites/kobo-001").json()["site_uuid"] == str(imported.site.id)

    def test_a_changed_or_foreign_legacy_document_is_an_error(self, legacy_root) -> None:
        store = InMemoryFoundationStore()
        do_import(store)
        changed = app_for(store, legacy_root, legacy_documents=lambda: (LegacyDocument("KOBO-001", KOBO_PATH, "0" * 64),))
        assert changed.get("/api/sites").status_code == 503
        foreign = app_for(store, legacy_root, legacy_documents=lambda: (LegacyDocument("kobo-001", "x.yaml", "0" * 64),))
        assert foreign.get("/api/sites/KOBO-001").status_code == 503

    def test_read_versions_publish_and_recover_both_bases(self, legacy_root) -> None:
        store = InMemoryFoundationStore()
        imported = do_import(store)
        clock = Clock(NOW)
        client = app_for(store, legacy_root, clock)
        body = client.get("/api/sites/KOBO-001/foundation", headers={"X-Tenant": "other"}).json()
        assert body["site"]["tenant"] == "demo"
        assert body["revision"]["revision_id"] == str(imported.revision.id)
        assert body["controls"]["battery_reserve"]["value"] == 30.0
        assert body["controls"]["generator_start_stop"]["state"] == "NOT_CONFIGURED"
        assert body["bindings"]["state"] == "NONE" and body["acquisition_snapshot"]["available"] is False
        published = client.post(
            "/api/sites/KOBO-001/foundation/revisions",
            json={**RESERVE, "value": 25, "valid_from": "2026-10-10T00:00:00Z"},
        )
        assert published.status_code == 201, published.text
        assert published.json()["revision"]["valid_to"] is None
        clock.now = NOW + timedelta(minutes=1)
        bounded = client.post(
            "/api/sites/KOBO-001/foundation/revisions",
            json={**RESERVE, "value": 35, "valid_from": "2026-10-01T00:00:00Z"},
        ).json()["revision"]
        assert (bounded["valid_from"], bounded["valid_to"]) == ("2026-10-01T00:00:00Z", "2026-10-10T00:00:00Z")
        clock.now = NOW + timedelta(minutes=2)
        later = client.get("/api/sites/KOBO-001/foundation", params={"at": "2026-10-11T00:00:00Z"}).json()
        assert later["controls"]["battery_reserve"]["value"] == 25.0
        audit = client.get("/api/sites/KOBO-001/foundation", params={
            "at": "2026-10-03T00:00:00Z", "knowledge_at": "2026-10-07T12:00:30Z"}).json()
        assert audit["controls"]["battery_reserve"]["value"] == 30.0
        corrected = client.get("/api/sites/KOBO-001/foundation", params={"at": "2026-10-03T00:00:00Z"}).json()
        assert corrected["controls"]["battery_reserve"]["value"] == 35.0

    def test_invalid_empty_unimported_and_unsupported_requests(self, legacy_root) -> None:
        store = InMemoryFoundationStore()
        do_import(store)
        client = app_for(store, legacy_root)
        assert client.get("/api/sites/KOBO-001/foundation", params={"at": "yesterday"}).status_code == 422
        empty = client.get("/api/sites/KOBO-001/foundation", params={"at": "2020-01-01T00:00:00Z"})
        assert empty.status_code == 404 and empty.json()["detail"]["code"] == "FOUNDATION_REVISION_NOT_FOUND"
        assert client.get("/api/sites/MG-LEGACY-1/foundation").json()["detail"]["code"] == "FOUNDATION_MIGRATION_REQUIRED"
        assert client.get("/api/sites/NOPE-1/foundation").status_code == 404
        priority = client.post("/api/sites/KOBO-001/foundation/revisions", json={
            **RESERVE, "property_key": "source-priority", "value": 1, "valid_from": "2026-10-10T00:00:00Z"})
        assert priority.json()["detail"]["code"] == "FOUNDATION_CHANGE_UNSUPPORTED"
        tenant_field = client.post("/api/sites/KOBO-001/foundation/revisions", json={
            **RESERVE, "value": 25, "valid_from": "2026-10-10T00:00:00Z", "tenant": "other"})
        assert tenant_field.status_code == 422

    def test_a_backwards_clock_is_a_typed_refusal_with_nothing_written(self, legacy_root) -> None:
        store = InMemoryFoundationStore()
        imported = do_import(store, when=NOW)
        client = app_for(store, legacy_root, Clock(NOW - timedelta(minutes=5)))
        response = client.post("/api/sites/KOBO-001/foundation/revisions",
                               json={**RESERVE, "value": 25, "valid_from": "2026-10-10T00:00:00Z"})
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "FOUNDATION_CLOCK_BEHIND"
        assert store.rows[imported.site.id] == [imported.revision]


class TestTenantIsolationAtTheApi:
    def test_another_tenants_site_is_neither_served_nor_writable(self, tmp_path) -> None:
        store = InMemoryFoundationStore()
        store.ensure_tenant("demo", "Development tenant", now=NOW)
        other = do_import(store, tenant="other", configured="other")
        client = app_for(store, tmp_path, legacy_documents=lambda: ())
        assert client.get("/api/sites").json()["sites"] == []
        assert client.get("/api/sites/KOBO-001/foundation").status_code == 404
        refused = client.post("/api/sites/KOBO-001/foundation/revisions",
                              json={**RESERVE, "value": 25, "valid_from": "2026-10-10T00:00:00Z"})
        assert refused.status_code == 404
        assert store.rows[other.site.id] == [other.revision]
        service = FoundationService(store, "demo", Clock(NOW))
        with pytest.raises(FoundationRefused):
            service.publish_battery_reserve(service.tenant(), other.site, asset_code="battery",
                                            value=25.0, effective_from=NOW, note=None)


# --- legacy surfaces ---------------------------------------------------------------


def import_mg900(store) -> None:
    source = ImportSource(path="tests/mg-900.yaml", sha256="b" * 64, record=fixture_site())
    import_site(store, tenant_slug="demo", configured_tenant_slug="demo", source=source,
                legacy_documents=(), clock=Clock(NOW - timedelta(hours=1)))


class TestLegacySurfacesRefuse:
    def test_evidence_overview_and_analytics_answer_awaiting_migration(self, legacy_root) -> None:
        store = InMemoryFoundationStore()
        do_import(store)
        client = app_for(store, legacy_root)
        for path in ("evidence", "evidence/records", "evidence/rejections", "overview",
                     "dispatch", "analytics", "findings"):
            response = client.get(f"/api/sites/KOBO-001/{path}")
            assert response.status_code == 409, path
            assert response.json()["detail"]["code"] == "AWAITING_EVIDENCE_MIGRATION"
            assert client.get(f"/api/sites/MG-LEGACY-1/{path}").status_code != 409, path
        assert all(row["site_id"] != "KOBO-001" for row in client.get("/api/findings").json()["findings"])

    def test_ingestion_refuses_an_imported_code_and_persists_nothing(self, tmp_path) -> None:
        from test_t027_ingestion import a_batch, envelope, ingestion_batch_document, texts

        store = InMemoryFoundationStore()
        import_mg900(store)
        evidence_root = tmp_path / "evidence"
        client = TestClient(create_app(
            OFF, site_repository=FakeSites((fixture_site(),)), foundation_store=store,
            foundation_clock=Clock(NOW), legacy_documents=lambda: (),
            evidence_store=JsonEvidenceStore(evidence_root),
        ))
        response = client.post("/api/ingestion/batches",
                               json=ingestion_batch_document(a_batch(texts(envelope(1)))))
        assert response.status_code == 409, response.text
        assert response.json()["refusal"]["kind"] == "AWAITING_EVIDENCE_MIGRATION"
        assert client.get("/api/ingestion/batches/batch-1").status_code == 404
        assert not any(evidence_root.rglob("*.json"))


# --- Lab ---------------------------------------------------------------------------


class StagedExecution(FakeExecution):
    def staged_envelopes(self, run):
        self.calls.append(("staged_envelopes", run.run_id))
        return a_view(run.run_id)


def lab_client(store, execution, runs, **overrides) -> TestClient:
    return TestClient(create_app(
        ON, site_repository=overrides.pop("site_repository", FakeSites((fixture_site(),))),
        run_repository=runs, execution=execution, foundation_store=store,
        foundation_clock=Clock(NOW), legacy_documents=lambda: (), **overrides,
    ))


WRITE_CONTROLS = (
    ("/execution/start", None),
    ("/execution/step", {"boundaries": 1, "from_boundary": 0}),
    ("/execution/run-to-end", None),
    ("/commit", None),
)


class TestLabRefusesImportedSites:
    @pytest.mark.parametrize("path,body", WRITE_CONTROLS)
    def test_each_write_control_refuses_before_the_port_runs(self, path, body) -> None:
        record, runs = persisted_draft()
        store = InMemoryFoundationStore()
        import_mg900(store)
        execution = StagedExecution()
        client = lab_client(store, execution, runs)
        response = client.post(f"/api/simulator-lab/runs/{record.run_id}{path}", json=body)
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["code"] == "SITE_AWAITING_MIGRATION"
        assert execution.calls == []

    def test_controls_still_reach_the_port_for_an_unimported_site(self) -> None:
        record, runs = persisted_draft()
        execution = StagedExecution()
        client = lab_client(InMemoryFoundationStore(), execution, runs)
        assert client.post(f"/api/simulator-lab/runs/{record.run_id}/execution/start").status_code == 200
        assert execution.calls and execution.calls[0][0] == "start"

    def test_setup_refuses_and_history_and_stage_stay_readable(self) -> None:
        record, runs = persisted_draft()
        store = InMemoryFoundationStore()
        import_mg900(store)
        client = lab_client(store, StagedExecution(), runs)
        setup = client.post("/api/simulator-lab/runs", json=setup_request())
        assert setup.status_code == 422 and setup.json()["detail"]["refusal_kind"] == "SITE_AWAITING_MIGRATION"
        assert client.get(f"/api/simulator-lab/runs/{record.run_id}").status_code == 200
        stage = client.get(f"/api/simulator-lab/runs/{record.run_id}/stage")
        assert stage.status_code == 200
        basis = stage.json()["frozen_basis"]
        assert basis["site_imported"] is True and basis["can_release"] is False
        assert basis["configuration_store"] == "LEGACY_FILE" and basis["site_id"] == "MG-900"

    def test_stage_read_has_a_defined_answer_when_the_store_cannot_be_asked(self) -> None:
        record, runs = persisted_draft()
        client = lab_client(InMemoryFoundationStore(unavailable=True), StagedExecution(), runs)
        stage = client.get(f"/api/simulator-lab/runs/{record.run_id}/stage")
        assert stage.status_code == 200
        assert stage.json()["frozen_basis"]["site_imported"] is None
        assert stage.json()["frozen_basis"]["can_release"] is False
        no_tenant = lab_client(InMemoryFoundationStore(), StagedExecution(), runs)
        assert no_tenant.get(f"/api/simulator-lab/runs/{record.run_id}/stage").json()["frozen_basis"]["site_imported"] is False

    def test_lab_create_site_refuses_an_imported_code_over_http(self) -> None:
        store = InMemoryFoundationStore()
        source = ImportSource(path="tests/mg-002.yaml", sha256="c" * 64, record=fixture_site(site_id="MG-002"))
        import_site(store, tenant_slug="demo", configured_tenant_slug="demo", source=source,
                    legacy_documents=(), clock=Clock(NOW))
        client = lab_client(store, StagedExecution(), persisted_draft()[1],
                            site_repository=FakeSites(()), site_template_catalog=FakeCatalog())
        response = client.post("/api/simulator-lab/sites", json=request_body())
        assert response.status_code == 409, response.text


# --- import report target (review m5) ---------------------------------------------


class TestReportTarget:
    def test_the_source_and_the_site_stores_are_refused(self, tmp_path) -> None:
        source = tmp_path / "kobo.yaml"
        source.write_bytes(KOBO_SOURCE.read_bytes())
        with pytest.raises(SiteConfigurationInvalid, match="import source"):
            check_report_path(str(source), str(source))
        with pytest.raises(SiteConfigurationInvalid, match="Site store"):
            check_report_path(str(USER_SITE_STORE_ROOT / "report.md"), str(source))
        check_report_path(str(tmp_path / "report.md"), str(source))

    def test_the_cli_refuses_before_importing_and_leaves_the_source_intact(self, tmp_path, monkeypatch) -> None:
        from assetops_backend.sites import import_kobo

        source = tmp_path / "kobo.yaml"
        source.write_bytes(KOBO_SOURCE.read_bytes())
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        monkeypatch.delenv("DATABASE_URL", raising=False)
        code = import_kobo.main(["--source", str(source), "--tenant", "demo", "--report", str(source)])
        assert code == 1
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest


class TestGapFixture:
    def test_the_gap_fixture_reports_its_exact_configuration_gap(self, tmp_path) -> None:
        store = InMemoryFoundationStore()
        text_ = KOBO_SOURCE.read_text(encoding="utf-8").replace("site_id: KOBO-001", "site_id: KOBO-GAP-001")
        start = text_.index("    - property_key: reserve-state-of-charge")
        end = text_.index("  - component_id: battery-pcs")
        gap_file = tmp_path / "kobo-gap-001.yaml"
        gap_file.write_text(text_[:start] + text_[end:], encoding="utf-8")
        do_import(store, read_import_source(str(gap_file)))
        client = app_for(store, tmp_path, legacy_documents=lambda: ())
        body = client.get("/api/sites/KOBO-GAP-001/foundation").json()
        assert [g["code"] for g in body["configuration_gaps"]] == ["BATTERY_RESERVE_MISSING"]
        assert body["controls"]["battery_reserve"]["state"] == "NOT_CONFIGURED"
