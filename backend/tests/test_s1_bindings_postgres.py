"""S1-02 signal bindings against a disposable PostgreSQL test database.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped (never
passed) without it. Covers what only the database guarantees: migration 0002
from zero, the current-set and current-channel exclusion constraints, the
same-Site and source-of-gateway foreign keys, the immutability and
close-rows triggers, and the full conversion -> change -> historical read path
through `PostgresFoundationStore`.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
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
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import DBAPIError, IntegrityError

    from assetops_backend.sites.adapters.import_files import read_import_source
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.sites.binding_conversion import convert
    from assetops_backend.sites.binding_service import (
        BindingRefused,
        BindingRequest,
        BindingService,
        acquisition_snapshot,
        readiness,
    )
    from assetops_backend.sites.foundation_records import BindingOverlap, ConfigurationPlan
    from assetops_backend.sites.foundation_service import FoundationService, ImportSource, import_site

BACKEND = Path(__file__).resolve().parents[1]
KOBO_SOURCE = BACKEND / "tests" / "fixtures" / "s1" / "kobo-001.yaml"
FIXTURE = json.loads((BACKEND / "conversions" / "kobo-001-bindings.json").read_text(encoding="utf-8"))
NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
CHANGE_FROM = datetime(2026, 10, 5, tzinfo=timezone.utc)
EARLIER = datetime(2026, 10, 4, tzinfo=timezone.utc)


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture(scope="module")
def engine():
    url = make_url(URL)
    assert url.database and url.database.endswith("_test"), "Refusing a database not named *_test"
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


def imported(store, code="KOBO-001", when=NOW - timedelta(hours=2)):
    source = read_import_source(str(KOBO_SOURCE))
    record = source.record if code == "KOBO-001" else replace(source.record, site_id=code)
    return import_site(
        store,
        tenant_slug="demo",
        configured_tenant_slug="demo",
        source=ImportSource(path=f"var/sites/{code.lower()}.yaml", sha256=source.sha256, record=record),
        legacy_documents=(),
        clock=Clock(when),
    )


def converted(store):
    result = imported(store)
    outcome = convert(store, BindingService(store, Clock(NOW - timedelta(hours=1))), result.tenant, result.site, FIXTURE)
    return result, outcome


def view(store, result, at=None, knowledge=None):
    return FoundationService(store, "demo", Clock(NOW)).read(result.site, result.tenant, at, knowledge)


class TestMigration:
    def test_head_includes_the_binding_tables(self, engine) -> None:
        with engine.connect() as connection:
            head = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            tables = set(connection.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )).scalars())
        assert head == "0002_signal_bindings"
        assert {"signal_binding_set_revision", "signal_binding_revision"} <= tables


class TestPublishAndHistory:
    def test_conversion_change_and_historical_snapshot_through_postgres(self, store, engine) -> None:
        result, outcome = converted(store)
        assert outcome.created
        first = view(store, result, at=EARLIER)
        assert readiness(first.site, first.revision, first.registrations, first.binding_set)["state"] == "READY_TO_REPORT"
        original = acquisition_snapshot(first.site, first.revision, first.registrations, first.binding_set)
        assert hashlib.sha256(original.body).hexdigest() == original.sha256

        current = first.binding_set
        requests = [
            BindingRequest(b.device_id, b.signal_id, None if b.asset_id is None else str(b.asset_id), b.role,
                           b.source_unit, b.canonical_unit, b.conversion)
            for b in current.bindings
            if b.role != "battery_soc"
        ]
        BindingService(store, Clock(NOW)).publish(
            result.tenant, result.site, requests=requests, effective_from=CHANGE_FROM, note="remove SOC"
        )
        later = view(store, result)
        ready = readiness(later.site, later.revision, later.registrations, later.binding_set)
        assert ready["missing_roles"] == ["Battery state of charge"]
        before_change = view(store, result, at=EARLIER, knowledge=NOW - timedelta(minutes=1))
        again = acquisition_snapshot(
            before_change.site, before_change.revision, before_change.registrations, before_change.binding_set
        )
        assert again.sha256 == original.sha256 and again.body == original.body
        with engine.connect() as connection:
            closed = connection.execute(text(
                "SELECT count(*) FROM signal_binding_revision WHERE binding_set_revision_id = :id "
                "AND superseded_at IS NOT NULL"
            ), {"id": current.id}).scalar_one()
        assert closed == len(current.bindings)  # the close-rows trigger closed every row

    def test_a_refused_publish_writes_nothing(self, store, engine) -> None:
        result, outcome = converted(store)
        bad = [BindingRequest("battery-pcs-controller", "state-of-charge", None, "battery_soc", "%", "%",
                              {"kind": "IDENTITY", "parameters": {}})]
        with pytest.raises(BindingRefused):
            BindingService(store, Clock(NOW)).publish(
                result.tenant, result.site, requests=bad, effective_from=CHANGE_FROM, note=None
            )
        assert len(store.binding_sets(result.tenant.id, result.site.id)) == 1

    def test_an_overlapping_current_set_from_the_store_is_refused(self, store) -> None:
        result, outcome = converted(store)
        current = outcome.published.changed

        def planner(state):
            twin = replace(current, id=uuid4(), version=99, bindings=())
            return ConfigurationPlan(NOW, (), (), (), (twin,))

        with pytest.raises(BindingOverlap):
            store.publish_configuration(result.tenant.id, result.site.id, planner)
        assert len(store.binding_sets(result.tenant.id, result.site.id)) == 1


def _set_row(connection, result, *, role_set="other-roles", version=50):
    set_id = uuid4()
    connection.execute(text(
        "INSERT INTO signal_binding_set_revision (id, tenant_id, site_id, binding_set_id, version, role_set, "
        "valid_from, valid_to, recorded_at, bindings_sha256, origin) VALUES (:id, :t, :s, :b, :v, :r, "
        ":from_, NULL, :rec, :sha, 'PUBLISH')"
    ), {"id": set_id, "t": result.tenant.id, "s": result.site.id, "b": uuid4(), "v": version, "r": role_set,
        "from_": EARLIER, "rec": NOW, "sha": "0" * 64})
    return set_id


def _binding_row(connection, result, set_id, *, source, device_id, asset_id, version=50):
    connection.execute(text(
        "INSERT INTO signal_binding_revision (id, tenant_id, site_id, binding_set_revision_id, binding_set_id, "
        "version, gateway_id, source_id, device_id, signal_id, asset_id, role, source_unit, canonical_unit, "
        "conversion, valid_from, valid_to, recorded_at) SELECT :id, :t, :s, :set_id, binding_set_id, version, "
        ":g, :src, :dev, 'state-of-charge', :asset, 'battery_soc', '%', '%', '{}'::jsonb, valid_from, valid_to, "
        "recorded_at FROM signal_binding_set_revision WHERE id = :set_id"
    ), {"id": uuid4(), "t": result.tenant.id, "s": result.site.id, "set_id": set_id, "g": source.gateway_id,
        "src": source.id, "dev": device_id, "asset": asset_id})


class TestDatabaseRules:
    def test_overlapping_current_sets_of_one_role_set_are_refused(self, store, engine) -> None:
        result, _ = converted(store)
        with pytest.raises(IntegrityError, match="binding_set_no_current_overlap"):
            with engine.begin() as connection:
                _set_row(connection, result, role_set="minigrid-roles-1")

    def test_a_channel_bound_in_two_current_sets_is_refused(self, store, engine) -> None:
        result, _ = converted(store)
        regs = store.registrations(result.tenant.id, result.site.id)
        pcs = next(s for s in regs.sources if s.source_external_id == "battery-pcs-controller")
        battery = next(a for a in regs.assets if a.asset_code == "battery")
        with pytest.raises(IntegrityError, match="binding_no_current_channel_overlap"):
            with engine.begin() as connection:
                set_id = _set_row(connection, result)
                _binding_row(connection, result, set_id, source=pcs, device_id=pcs.source_external_id,
                             asset_id=battery.id)

    def test_another_sites_asset_and_a_mismatched_device_are_refused(self, store, engine) -> None:
        result = imported(store)
        other = imported(store, code="KOBO-002")
        regs = store.registrations(result.tenant.id, result.site.id)
        pcs = next(s for s in regs.sources if s.source_external_id == "battery-pcs-controller")
        foreign = next(a for a in other.registrations.assets if a.asset_code == "battery")
        with pytest.raises(IntegrityError, match="binding_asset_same_site"):
            with engine.begin() as connection:
                set_id = _set_row(connection, result)
                _binding_row(connection, result, set_id, source=pcs, device_id=pcs.source_external_id,
                             asset_id=foreign.id)
        battery = next(a for a in regs.assets if a.asset_code == "battery")
        with pytest.raises(IntegrityError, match="binding_source_of_gateway"):
            with engine.begin() as connection:
                set_id = _set_row(connection, result)
                _binding_row(connection, result, set_id, source=pcs, device_id="clinic-meter", asset_id=battery.id)

    def test_rows_are_immutable_and_join_only_a_current_set(self, store, engine) -> None:
        result, outcome = converted(store)
        set_id = outcome.published.changed.id
        with pytest.raises(DBAPIError, match="immutable"):
            with engine.begin() as connection:
                connection.execute(text("UPDATE signal_binding_revision SET role = 'fuel_level' "
                                        "WHERE binding_set_revision_id = :id"), {"id": set_id})
        with pytest.raises(DBAPIError, match="append-only"):
            with engine.begin() as connection:
                connection.execute(text("DELETE FROM signal_binding_set_revision WHERE id = :id"), {"id": set_id})
        regs = store.registrations(result.tenant.id, result.site.id)
        pcs = next(s for s in regs.sources if s.source_external_id == "battery-pcs-controller")
        with pytest.raises(DBAPIError, match="currently recorded"):
            with engine.begin() as connection:
                closed = _set_row(connection, result)
                connection.execute(text("UPDATE signal_binding_set_revision SET superseded_at = :at "
                                        "WHERE id = :id"), {"at": NOW, "id": closed})
                _binding_row(connection, result, closed, source=pcs, device_id=pcs.source_external_id,
                             asset_id=None)
