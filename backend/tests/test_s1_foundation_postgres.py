"""S1-01 persisted Foundation, against a disposable PostgreSQL test database.

Every test here needs `ASSETOPS_TEST_DATABASE_URL` naming a database whose
name ends in `_test` (the Compose service creates `assetops_test`). The
module drops that database's `public` schema and runs every Alembic migration
from zero, then truncates between tests. Without the variable the module is
SKIPPED - reported as skipped, never as passed. No SQLite stand-in exists.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from alembic import command
    from alembic.config import Config
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    from assetops_backend.config import FeatureFlags
    from assetops_backend.main import create_app
    from assetops_backend.sites.adapters.composite_site_repository import CompositeSiteRepository
    from assetops_backend.sites.adapters.import_files import read_import_source
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.sites.adapters.yaml_shipped_site_store import ReadOnlyYamlSiteStore
    from assetops_backend.sites.adapters.yaml_user_site_store import WritableYamlSiteStore
    from assetops_backend.sites.cutover import ImportedSiteRegistry, LegacySiteGate
    from assetops_backend.sites.foundation_records import (
        FoundationOverlap,
        FoundationSiteNotFound,
        PublishPlan,
        RevisionRow,
        TenantRef,
    )
    from assetops_backend.sites.foundation_service import (
        FoundationRefused,
        FoundationService,
        ImportConflict,
        ImportSource,
        LegacyDocument,
        import_site,
        plan_import,
    )
    from assetops_backend.sites.ports import SiteAwaitingMigration, SiteIdentityConflict

BACKEND = Path(__file__).resolve().parents[1]
KOBO_SOURCE = BACKEND / "tests" / "fixtures" / "s1" / "kobo-001.yaml"
KOBO_PATH = "var/sites/kobo-001.yaml"
NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
ENABLED = None if not URL else FeatureFlags(simulator_lab_enabled=True)


@pytest.fixture(scope="module")
def engine():
    url = make_url(URL)
    assert url.database and url.database.endswith("_test"), (
        "Refusing to run destructive tests against a database not named *_test"
    )
    eng = create_engine(URL)
    with eng.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        connection.execute(text("DROP EXTENSION IF EXISTS btree_gist"))
    config = Config(str(BACKEND / "alembic.ini"))
    config.attributes["database_url"] = URL
    command.upgrade(config, "head")
    yield eng
    eng.dispose()


@pytest.fixture()
def store(engine):
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE foundation_revision, source, gateway, asset, site_import, site, tenant CASCADE")
        )
    return PostgresFoundationStore(URL)


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def kobo_source(path: str = KOBO_PATH, **changes) -> ImportSource:
    source = read_import_source(str(KOBO_SOURCE))
    return ImportSource(path=path, sha256=changes.get("sha256", source.sha256), record=changes.get("record", source.record))


def do_import(store, source=None, *, tenant="demo", legacy=(), clock=None):
    return import_site(
        store,
        tenant_slug=tenant,
        configured_tenant_slug="demo",
        source=source or kobo_source(),
        legacy_documents=legacy,
        clock=clock or Clock(NOW - timedelta(hours=1)),
    )


def count(engine, table: str) -> int:
    with engine.connect() as connection:
        return connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()


# --- migrations ---------------------------------------------------------------


class TestMigrationsFromZero:
    def test_every_table_the_extension_and_the_exclusion_constraint_exist(self, engine, store) -> None:
        with engine.connect() as connection:
            tables = set(
                connection.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                ).scalars()
            )
            extension = connection.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'btree_gist'")
            ).first()
            exclusion = connection.execute(
                text(
                    "SELECT 1 FROM pg_constraint WHERE conname = "
                    "'foundation_revision_no_current_overlap' AND contype = 'x'"
                )
            ).first()
        assert {"tenant", "site", "site_import", "asset", "gateway", "source", "foundation_revision"} <= tables
        assert extension is not None and exclusion is not None

    def test_revision_content_is_immutable_and_rows_cannot_be_deleted(self, engine, store) -> None:
        result = do_import(store)
        for statement in (
            "UPDATE foundation_revision SET content = '{}'::jsonb",
            "UPDATE foundation_revision SET valid_from = valid_from - interval '1 day'",
            "DELETE FROM foundation_revision",
            "DELETE FROM site",
        ):
            with pytest.raises(Exception), engine.begin() as connection:
                connection.execute(text(statement))
        assert store.revisions(result.tenant.id, result.site.id)[0].content == result.revision.content


# --- import -------------------------------------------------------------------


class TestImport:
    def test_the_fixture_imports_with_its_own_identity_and_ten_assets(self, store) -> None:
        result = do_import(store)
        site, regs, revision = result.site, result.registrations, result.revision
        assert (site.site_code, site.name, site.site_type, site.timezone, site.lifecycle) == (
            "KOBO-001", "Kobo mini-grid", "MINIGRID", "Africa/Addis_Ababa", "PLANNED",
        )
        assert revision.version == 1
        assert revision.valid_from == datetime(2026, 9, 29, 11, 57, 49, tzinfo=timezone.utc)
        assert revision.valid_to is None
        assert sorted(a.asset_code for a in regs.assets) == sorted([
            "pv-array", "pv-inverter", "battery", "battery-pcs", "generator",
            "fuel-tank", "ac-bus", "load-res", "load-clinic", "load-mill",
        ])
        assert [g.gateway_external_id for g in regs.gateways] == ["edge-kobo-001"]
        gateway = regs.gateways[0]
        assert gateway.credential_ref is None and gateway.disabled_at is not None
        assert gateway.mode == "SIMULATED"
        assert len(regs.sources) == 8
        assert {s.gateway_id for s in regs.sources} == {gateway.id}
        assert site.import_record.source_path == KOBO_PATH
        assert site.import_record.source_sha256 == hashlib.sha256(KOBO_SOURCE.read_bytes()).hexdigest()

    def test_reimport_of_the_same_path_and_digest_returns_the_same_rows(self, engine, store) -> None:
        first = do_import(store)
        second = do_import(store, clock=Clock(NOW + timedelta(hours=1)))
        assert not second.created
        assert (second.site.id, second.revision.id) == (first.site.id, first.revision.id)
        assert count(engine, "foundation_revision") == 1 and count(engine, "asset") == 10

    def test_changed_bytes_a_different_source_and_another_tenant_conflict(self, engine, store) -> None:
        do_import(store)
        with pytest.raises(ImportConflict, match="changed"):
            do_import(store, kobo_source(sha256="0" * 64))
        with pytest.raises(ImportConflict, match="different source"):
            do_import(store, kobo_source(path="elsewhere/kobo-copy.yaml"))
        with pytest.raises(ImportConflict, match="tenant"):
            do_import(store, tenant="other")
        assert count(engine, "site") == 1 and count(engine, "foundation_revision") == 1

    def test_a_different_legacy_document_with_the_same_code_is_a_conflict(self, engine, store) -> None:
        legacy = (LegacyDocument("kobo-001", "config/sites/kobo.yaml", "f" * 64),)
        with pytest.raises(ImportConflict, match="also declared"):
            do_import(store, legacy=legacy)
        assert count(engine, "site") == 0

    def test_the_registered_document_itself_is_the_expected_source(self, store) -> None:
        legacy = (LegacyDocument("KOBO-001", KOBO_PATH, kobo_source().sha256),)
        assert do_import(store, legacy=legacy).created


# --- tenant isolation -----------------------------------------------------------


def second_tenant_copy(store) -> tuple[TenantRef, object]:
    other = store.ensure_tenant("other", "Other tenant", now=NOW)
    record = kobo_source().record
    plan = plan_import(other, ImportSource(path="other/kobo.yaml", sha256="a" * 64, record=record), NOW)
    plan = plan.__class__(
        plan.site, plan.assets,
        plan.gateway.__class__(**{**plan.gateway.__dict__, "gateway_external_id": "edge-other-kobo"}),
        plan.sources, plan.revision,
    )
    store.insert_import(other.id, plan)
    return other, store.find_site(other.id, "KOBO-001")


class TestTenantIsolation:
    def test_the_same_code_in_two_tenants_resolves_within_each(self, store) -> None:
        demo = do_import(store)
        other, other_site = second_tenant_copy(store)
        assert other_site.id != demo.site.id
        assert store.find_site(demo.tenant.id, "kobo-001").id == demo.site.id
        assert store.find_site(other.id, "KOBO-001").id == other_site.id

    def test_a_uuid_from_another_tenant_is_not_found_and_not_writable(self, engine, store) -> None:
        demo = do_import(store)
        other, other_site = second_tenant_copy(store)
        assert store.find_site_by_id(demo.tenant.id, other_site.id) is None
        assert store.revisions(demo.tenant.id, other_site.id) == ()
        assert store.registrations(demo.tenant.id, other_site.id).assets == ()
        before = count(engine, "foundation_revision")
        service = FoundationService(store, "demo", Clock(NOW))
        with pytest.raises(FoundationRefused, match="Site"):
            service.publish_battery_reserve(
                demo.tenant, other_site, asset_code="battery", value=25.0,
                effective_from=NOW + timedelta(days=1), note=None,
            )
        assert count(engine, "foundation_revision") == before

    def test_a_cross_tenant_composite_reference_is_refused_by_the_database(self, engine, store) -> None:
        demo = do_import(store)
        other, other_site = second_tenant_copy(store)
        with pytest.raises(Exception), engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO asset (id, tenant_id, site_id, asset_code, asset_type, attributes, created_at) "
                    "VALUES (:id, :tenant, :site, 'x', 'LOAD', '{}'::jsonb, now())"
                ),
                {"id": uuid4(), "tenant": demo.tenant.id, "site": other_site.id},
            )


# --- time-valid publish -----------------------------------------------------------


def reserve_of(view) -> float:
    for component in view.revision.content["components"]:
        for item in component.get("properties") or ():
            if item["property_key"] == "reserve-state-of-charge":
                return item["value"]
    raise AssertionError("no reserve")


class TestPublish:
    def test_a_future_change_splits_the_open_period_and_keeps_the_old_basis(self, engine, store) -> None:
        imported = do_import(store)
        clock = Clock(NOW)
        service = FoundationService(store, "demo", clock)
        tenant = service.tenant()
        site = service.site(tenant, "KOBO-001")
        effective = NOW + timedelta(days=3)
        result = service.publish_battery_reserve(
            tenant, site, asset_code="battery", value=25.0, effective_from=effective, note="seasonal"
        )
        assert [r.origin for r in result.plan.inserts] == ["SPLIT", "PUBLISH"]
        assert result.changed.version == 3 and result.changed.valid_from == effective
        clock.now = NOW + timedelta(minutes=5)
        assert reserve_of(service.read(site, tenant, NOW, None)) == 30.0
        assert reserve_of(service.read(site, tenant, effective, None)) == 25.0
        before = service.read(site, tenant, effective, NOW - timedelta(seconds=1))
        assert before.revision.id == imported.revision.id and reserve_of(before) == 30.0
        rows = store.revisions(tenant.id, site.id)
        assert [(r.version, r.superseded_at is None) for r in rows] == [(1, False), (2, True), (3, True)]
        assert rows[0].content == imported.revision.content

    def test_a_backdated_correction_preserves_the_previous_knowledge_basis(self, store) -> None:
        do_import(store)
        clock = Clock(NOW)
        service = FoundationService(store, "demo", clock)
        tenant = service.tenant()
        site = service.site(tenant, "KOBO-001")
        backdated = NOW - timedelta(days=2)
        service.publish_battery_reserve(
            tenant, site, asset_code="battery", value=35.0, effective_from=backdated, note=None
        )
        clock.now = NOW + timedelta(seconds=1)
        corrected = service.read(site, tenant, NOW - timedelta(days=1), None)
        prior = service.read(site, tenant, NOW - timedelta(days=1), NOW - timedelta(seconds=1))
        assert reserve_of(corrected) == 35.0 and reserve_of(prior) == 30.0

    def test_invalid_values_and_periods_leave_no_partial_revision(self, engine, store) -> None:
        do_import(store)
        service = FoundationService(store, "demo", Clock(NOW))
        tenant = service.tenant()
        site = service.site(tenant, "KOBO-001")
        cases = [
            dict(asset_code="battery", value=150.0, effective_from=NOW + timedelta(days=1)),
            dict(asset_code="battery", value=25.0, effective_from=datetime(2020, 1, 1, tzinfo=timezone.utc)),
            dict(asset_code="generator", value=25.0, effective_from=NOW + timedelta(days=1)),
            dict(asset_code="battery", value=30.0, effective_from=NOW + timedelta(days=1)),
        ]
        for case in cases:
            with pytest.raises(FoundationRefused):
                service.publish_battery_reserve(tenant, site, note=None, **case)
        assert count(engine, "foundation_revision") == 1
        assert store.revisions(tenant.id, site.id)[0].superseded_at is None

    def test_an_overlapping_current_period_is_refused_by_the_constraint(self, engine, store) -> None:
        imported = do_import(store)
        overlapping = RevisionRow(**{**imported.revision.__dict__, "id": uuid4(), "version": 9})

        def planner(rows):
            return PublishPlan(supersede_ids=(), superseded_at=NOW, inserts=(overlapping,))

        with pytest.raises(FoundationOverlap):
            store.publish(imported.tenant.id, imported.site.id, planner)
        assert count(engine, "foundation_revision") == 1

    def test_publish_to_an_unknown_site_uuid_writes_nothing(self, engine, store) -> None:
        imported = do_import(store)
        with pytest.raises(FoundationSiteNotFound):
            store.publish(imported.tenant.id, uuid4(), lambda rows: None)


# --- API, cutover and Lab ---------------------------------------------------------


@pytest.fixture()
def legacy_root(tmp_path):
    root = tmp_path / "sites"
    root.mkdir()
    shutil.copy(KOBO_SOURCE, root / "kobo-001.yaml")
    other = KOBO_SOURCE.read_text(encoding="utf-8").replace("site_id: KOBO-001", "site_id: MG-LEGACY-1")
    (root / "mg-legacy-1.yaml").write_text(other, encoding="utf-8")
    return root


def app_for(store, legacy_root, clock=None, **overrides):
    legacy = CompositeSiteRepository(
        shipped=ReadOnlyYamlSiteStore(legacy_root), user=WritableYamlSiteStore(legacy_root / "user")
    )
    documents = lambda: (LegacyDocument("KOBO-001", KOBO_PATH, kobo_source().sha256),)  # noqa: E731
    return TestClient(
        create_app(
            overrides.pop("flags", FeatureFlags(simulator_lab_enabled=False)),
            site_repository=overrides.pop("site_repository", legacy),
            foundation_store=store,
            foundation_clock=clock or Clock(NOW),
            legacy_documents=overrides.pop("legacy_documents", documents),
            **overrides,
        )
    )


class TestFoundationApi:
    def test_index_lists_the_imported_site_once_beside_legacy_sites(self, store, legacy_root) -> None:
        imported = do_import(store)
        client = app_for(store, legacy_root)
        sites = client.get("/api/sites").json()["sites"]
        assert [(s["site_id"], s["configuration_store"]) for s in sites] == [
            ("KOBO-001", "POSTGRES"), ("MG-LEGACY-1", "LEGACY_FILE"),
        ]
        detail = client.get("/api/sites/kobo-001").json()
        assert detail["site_uuid"] == str(imported.site.id)
        assert detail["foundation_revision_id"] == str(imported.revision.id)
        assert client.get("/api/sites/MG-LEGACY-1").json()["configuration_store"] == "LEGACY_FILE"

    def test_a_changed_or_foreign_legacy_document_is_an_error_not_a_precedence(self, store, legacy_root) -> None:
        do_import(store)
        changed = app_for(store, legacy_root, legacy_documents=lambda: (LegacyDocument("KOBO-001", KOBO_PATH, "0" * 64),))
        assert changed.get("/api/sites").status_code == 503
        foreign = app_for(store, legacy_root, legacy_documents=lambda: (LegacyDocument("kobo-001", "x.yaml", "0" * 64),))
        assert foreign.get("/api/sites/KOBO-001").status_code == 503

    def test_read_versions_and_publish_round_trip(self, store, legacy_root) -> None:
        imported = do_import(store)
        clock = Clock(NOW)
        client = app_for(store, legacy_root, clock)
        body = client.get("/api/sites/KOBO-001/foundation", headers={"X-Tenant": "other"}).json()
        assert body["site"]["tenant"] == "demo"
        assert body["revision"]["revision_id"] == str(imported.revision.id)
        assert body["controls"]["battery_reserve"]["value"] == 30.0
        assert body["controls"]["generator_start_stop"]["state"] == "NOT_CONFIGURED"
        assert body["controls"]["generator_minimum_runtime"]["value"] == 30.0
        assert body["bindings"]["state"] == "INCOMPLETE"
        assert body["acquisition_snapshot"]["available"] is False
        assert body["configuration_gaps"] == []
        assert body["provenance"]["source_sha256"] == imported.site.import_record.source_sha256
        assert len(body["sources"]) == 8 and body["gateways"][0]["status"] == "PENDING"
        assert body["detail"]["foundation"]["version"] == 1
        published = client.post(
            "/api/sites/KOBO-001/foundation/revisions",
            json={"asset_code": "battery", "property_key": "reserve-state-of-charge",
                  "value": 25, "unit": "%", "valid_from": "2026-10-10T00:00:00Z"},
        )
        assert published.status_code == 201, published.text
        clock.now = NOW + timedelta(minutes=1)
        versions = client.get("/api/sites/KOBO-001/foundation/versions").json()["revisions"]
        assert [(v["version"], v["recorded_state"]) for v in versions] == [
            (1, "SUPERSEDED"), (2, "CURRENT"), (3, "CURRENT"),
        ]
        later = client.get("/api/sites/KOBO-001/foundation", params={"at": "2026-10-11T00:00:00Z"}).json()
        assert later["controls"]["battery_reserve"]["value"] == 25.0 and later["revision"]["is_current"] is False
        audit = client.get("/api/sites/KOBO-001/foundation", params={
            "at": "2026-10-11T00:00:00Z", "knowledge_at": "2026-10-07T11:00:00Z"}).json()
        assert audit["revision"]["version"] == 1

    def test_invalid_empty_unimported_and_unsupported_requests(self, store, legacy_root) -> None:
        do_import(store)
        client = app_for(store, legacy_root)
        assert client.get("/api/sites/KOBO-001/foundation", params={"at": "yesterday"}).status_code == 422
        assert client.get("/api/sites/KOBO-001/foundation", params={"at": "2026-10-07T00:00:00"}).status_code == 422
        empty = client.get("/api/sites/KOBO-001/foundation", params={"at": "2020-01-01T00:00:00Z"})
        assert empty.status_code == 404 and empty.json()["detail"]["code"] == "FOUNDATION_REVISION_NOT_FOUND"
        legacy = client.get("/api/sites/MG-LEGACY-1/foundation/versions")
        assert legacy.status_code == 409 and legacy.json()["detail"]["code"] == "FOUNDATION_MIGRATION_REQUIRED"
        assert client.get("/api/sites/NOPE-1/foundation").status_code == 404
        priority = client.post("/api/sites/KOBO-001/foundation/revisions", json={
            "asset_code": "battery", "property_key": "source-priority", "value": 1, "unit": "%",
            "valid_from": "2026-10-10T00:00:00Z"})
        assert priority.json()["detail"]["code"] == "FOUNDATION_CHANGE_UNSUPPORTED"
        tenant_field = client.post("/api/sites/KOBO-001/foundation/revisions", json={
            "asset_code": "battery", "property_key": "reserve-state-of-charge", "value": 25, "unit": "%",
            "valid_from": "2026-10-10T00:00:00Z", "tenant": "other"})
        assert tenant_field.status_code == 422

    def test_legacy_evidence_surfaces_answer_awaiting_migration(self, store, legacy_root) -> None:
        do_import(store)
        client = app_for(store, legacy_root)
        for path in ("evidence", "overview", "dispatch", "analytics", "findings"):
            response = client.get(f"/api/sites/KOBO-001/{path}")
            assert response.status_code == 409, path
            assert response.json()["detail"]["code"] == "AWAITING_EVIDENCE_MIGRATION"
            assert client.get(f"/api/sites/MG-LEGACY-1/{path}").status_code != 409, path

    def test_the_gap_fixture_reports_its_exact_configuration_gap(self, store, tmp_path) -> None:
        text_ = KOBO_SOURCE.read_text(encoding="utf-8").replace("site_id: KOBO-001", "site_id: KOBO-GAP-001")
        start = text_.index("    - property_key: reserve-state-of-charge")
        end = text_.index("  - component_id: battery-pcs")
        gap_file = tmp_path / "kobo-gap-001.yaml"
        gap_file.write_text(text_[:start] + text_[end:], encoding="utf-8")
        source = read_import_source(str(gap_file))
        do_import(store, source)
        client = app_for(store, tmp_path, legacy_documents=lambda: ())
        body = client.get("/api/sites/KOBO-GAP-001/foundation").json()
        assert [g["code"] for g in body["configuration_gaps"]] == ["BATTERY_RESERVE_MISSING"]
        assert body["controls"]["battery_reserve"]["state"] == "NOT_CONFIGURED"


class TestLabRefusesImportedSites:
    def test_controls_and_commit_refuse_while_history_stays_readable(self, store, legacy_root) -> None:
        from run_fixtures import FakeSites, site as fixture_site
        from test_run_execution_api import FakeExecution, persisted_draft

        record, runs = persisted_draft()
        target = fixture_site()
        tenant = store.ensure_tenant("demo", "Development tenant", now=NOW)
        source = ImportSource(path="tests/mg-900.yaml", sha256="b" * 64, record=target)
        import_site(store, tenant_slug="demo", configured_tenant_slug="demo", source=source,
                    legacy_documents=(), clock=Clock(NOW))
        execution = FakeExecution()
        client = app_for(
            store, legacy_root, flags=FeatureFlags(simulator_lab_enabled=True),
            site_repository=FakeSites((target,)), run_repository=runs, execution=execution,
            legacy_documents=lambda: (),
        )
        base = f"/api/simulator-lab/runs/{record.run_id}"
        for path, body in (
            ("/execution/start", None),
            ("/execution/step", {"boundaries": 1, "from_boundary": 0}),
            ("/execution/run-to-end", None),
            ("/commit", None),
        ):
            response = client.post(base + path, json=body)
            assert response.status_code == 409, (path, response.text)
            assert response.json()["detail"]["code"] == "SITE_AWAITING_MIGRATION"
        assert execution.calls == []
        assert client.get(base).status_code == 200
        setup = client.post("/api/simulator-lab/runs", json=__import__("run_fixtures").setup_request())
        assert setup.status_code == 422
        assert setup.json()["detail"]["refusal_kind"] == "SITE_AWAITING_MIGRATION"

    def test_the_gate_refuses_creating_a_legacy_site_with_an_imported_code(self, store) -> None:
        from run_fixtures import FakeSites, site as fixture_site

        imported = do_import(store)
        gate = LegacySiteGate(FakeSites(()), ImportedSiteRegistry(FoundationService(store, "demo", Clock(NOW))))
        with pytest.raises(SiteIdentityConflict):
            gate.create_site(fixture_site(site_id="kobo-001"))
        with pytest.raises(SiteAwaitingMigration):
            gate.get_site(imported.site.site_code)
