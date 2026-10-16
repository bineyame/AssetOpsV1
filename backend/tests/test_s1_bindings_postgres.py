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

import pg_harness

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
    # A fresh, fully migrated database per module: cloned from this run's migrated
    # template, or reset and migrated in place when routing is off (pg_harness).
    pg_harness.fresh_database()
    eng = create_engine(URL)
    pg_harness.assert_at_head(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def store(engine):
    # Same tables as TRUNCATE ... CASCADE, without its forced file syncs (pg_harness.empty_tables).
    pg_harness.empty_tables(engine, ("foundation_revision", "source", "gateway", "asset", "site_import", "site", "tenant"))
    owned = PostgresFoundationStore(URL)
    yield owned
    pg_harness.dispose(owned)


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
        assert head == "0019_verification_core"
        assert {"signal_binding_set_revision", "signal_binding_revision"} <= tables


class TestPublishAndHistory:
    def test_conversion_change_and_historical_snapshot_through_postgres(self, store, engine) -> None:
        result, outcome = converted(store)
        assert outcome.created
        first = view(store, result, at=EARLIER)
        assert readiness(first.site, first.revision, first.registrations, first.binding_set)["state"] == "READY_TO_REPORT"
        original = acquisition_snapshot(result.tenant.id, first.site, first.revisions, first.registrations, first.binding_set)
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
            result.tenant.id, before_change.site, before_change.revisions, before_change.registrations,
            before_change.binding_set,
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


def _set_row(connection, result, *, role_set="other-roles", version=50, valid_from=EARLIER, foundation=None,
             body=b"{}", sha=None):
    set_id = uuid4()
    anchor = foundation or connection.execute(text(
        "SELECT id FROM foundation_revision WHERE site_id = :s AND superseded_at IS NULL "
        "AND valid_from <= :at AND (valid_to IS NULL OR valid_to > :at)"
    ), {"s": result.site.id, "at": valid_from}).scalar_one()
    gateway = connection.execute(text("SELECT id FROM gateway WHERE site_id = :s"), {"s": result.site.id}).scalar_one()
    connection.execute(text(
        "INSERT INTO signal_binding_set_revision (id, tenant_id, site_id, binding_set_id, version, role_set, "
        "valid_from, valid_to, recorded_at, bindings_sha256, origin, foundation_revision_id, gateway_id, "
        "snapshot_schema, snapshot_sha256, snapshot_canonical) VALUES (:id, :t, :s, :b, :v, :r, :from_, NULL, "
        ":rec, :sha, 'PUBLISH', :f, :g, 'assetops.acquisition-snapshot/1', :sha, :body)"
    ), {"id": set_id, "t": result.tenant.id, "s": result.site.id, "b": uuid4(), "v": version, "r": role_set,
        "from_": valid_from, "rec": NOW, "sha": sha or hashlib.sha256(body).hexdigest(), "f": anchor,
        "g": gateway, "body": body})
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


class TestDecisionRulesInTheDatabase:
    def test_a_binding_period_outside_its_foundation_revision_is_refused(self, store, engine) -> None:
        result = imported(store)
        with engine.connect() as connection:
            imported_rev = connection.execute(
                text("SELECT id FROM foundation_revision WHERE site_id = :s"), {"s": result.site.id}
            ).scalar_one()
        with pytest.raises(DBAPIError, match="within its Foundation revision"):
            with engine.begin() as connection:
                _set_row(connection, result, role_set="minigrid-roles-1",
                         valid_from=datetime(2020, 1, 1, tzinfo=timezone.utc), foundation=imported_rev)

    def test_the_pinned_snapshot_is_immutable(self, store, engine) -> None:
        result, outcome = converted(store)
        with pytest.raises(DBAPIError, match="immutable"):
            with engine.begin() as connection:
                connection.execute(text("UPDATE signal_binding_set_revision SET snapshot_sha256 = :sha WHERE id = :id"),
                                   {"sha": "1" * 64, "id": outcome.published.changed.id})

    def test_a_reserve_change_realigns_bindings_and_pins_new_snapshots(self, store, engine) -> None:
        result, outcome = converted(store)
        before = view(store, result, at=EARLIER)
        old = acquisition_snapshot(result.tenant.id, before.site, before.revisions, before.registrations, before.binding_set)
        FoundationService(store, "demo", Clock(NOW)).publish_battery_reserve(
            result.tenant, result.site, asset_code="battery", value=40.0, effective_from=CHANGE_FROM, note=None
        )
        sets = [s for s in store.binding_sets(result.tenant.id, result.site.id) if s.superseded_at is None]
        assert len(sets) == 2
        later = view(store, result)
        pinned = acquisition_snapshot(result.tenant.id, later.site, later.revisions, later.registrations, later.binding_set)
        assert pinned.sha256 == later.binding_set.snapshot_sha256
        assert pinned.foundation_revision_id == later.revision.id
        again = view(store, result, at=EARLIER, knowledge=NOW - timedelta(minutes=1))
        recovered = acquisition_snapshot(result.tenant.id, again.site, again.revisions, again.registrations, again.binding_set)
        assert recovered.body == old.body and recovered.sha256 == old.sha256


# --- S1-02 fix round (Codex review M1) --------------------------------------------


def _alembic():
    config = Config(str(BACKEND / "alembic.ini"))
    config.attributes["database_url"] = URL
    return config


def _download(store, result, **kw):
    v = view(store, result, **kw)
    return acquisition_snapshot(result.tenant.id, v.site, v.revisions, v.registrations, v.binding_set)


class TestReviewM1HistoricalBytesInTheDatabase:
    def test_registration_updates_do_not_change_a_published_download(self, store, engine) -> None:
        result, outcome = converted(store)
        original = _download(store, result)
        with engine.begin() as connection:
            # Operational (credential rotation, disable) and external-name updates are
            # permitted by the schema; neither may alter the historical bytes. Mode is
            # immutable since migration 0005 (S2-02 AC4).
            connection.execute(text(
                "UPDATE gateway SET credential_ref = 'vault://rotated', disabled_at = :now, "
                "gateway_external_id = 'renamed-gateway' WHERE site_id = :s"
            ), {"now": NOW, "s": result.site.id})
        again = _download(store, result)
        assert (again.body, again.sha256) == (original.body, original.sha256)
        assert again.sha256 == outcome.published.changed.snapshot_sha256
        assert b"renamed-gateway" not in again.body

    def test_the_database_refuses_bytes_that_miss_the_pinned_hash_and_any_edit(self, store, engine) -> None:
        result, outcome = converted(store)
        with pytest.raises(DBAPIError, match="immutable"):
            with engine.begin() as connection:
                connection.execute(text(
                    "UPDATE signal_binding_set_revision SET snapshot_canonical = :b WHERE id = :id"
                ), {"b": b"{}", "id": outcome.published.changed.id})
        with engine.connect() as connection:
            checks = set(connection.execute(text(
                "SELECT conname FROM pg_constraint WHERE conname = 'binding_set_snapshot_canonical_hashed'"
            )).scalars())
        assert checks == {"binding_set_snapshot_canonical_hashed"}

    def test_a_row_whose_bytes_miss_its_hash_is_refused_on_insert(self, store, engine) -> None:
        result = imported(store)
        with pytest.raises(IntegrityError, match="binding_set_snapshot_canonical_hashed"):
            with engine.begin() as connection:
                _set_row(connection, result, body=b"{}", sha="0" * 64)

    def test_migration_0004_backfills_only_bytes_that_reproduce_the_pinned_hash(self, store, engine) -> None:
        result, outcome = converted(store)
        original = _download(store, result)
        config = _alembic()
        try:
            command.downgrade(config, "0003_pinned_binding_snapshots")
            with engine.begin() as connection:
                connection.execute(text("UPDATE gateway SET gateway_external_id = 'renamed' WHERE site_id = :s"),
                                   {"s": result.site.id})
            with pytest.raises(RuntimeError, match="will not pin different bytes or recompute"):
                command.upgrade(config, "head")
            with engine.begin() as connection:
                connection.execute(
                    text("UPDATE gateway SET gateway_external_id = :g WHERE site_id = :s"),
                    {"g": original.document["gateway"]["gateway_external_id"], "s": result.site.id},
                )
            command.upgrade(config, "head")
        finally:
            command.upgrade(config, "head")
        again = _download(store, result)
        assert (again.body, again.sha256) == (original.body, original.sha256)


class TestN6LineageStopsAtAnExplicitReinstatement:
    def test_identical_content_published_explicitly_is_a_stop(self, store) -> None:
        result, _ = converted(store)
        service = BindingService(store, Clock(NOW))
        from_08 = datetime(2026, 10, 8, tzinfo=timezone.utc)

        def requests(drop=None):
            current = view(store, result, at=EARLIER).binding_set
            return [
                BindingRequest(b.device_id, b.signal_id, None if b.asset_id is None else str(b.asset_id), b.role,
                               b.source_unit, b.canonical_unit, b.conversion)
                for b in current.bindings
                if (b.device_id, b.signal_id) != drop
            ]

        service.publish(result.tenant, result.site, requests=requests(("fuel-level-sensor", "fuel-level")),
                        effective_from=from_08, note="fuel off")
        v4 = service.publish(result.tenant, result.site, requests=requests(), effective_from=from_08,
                             note="fuel sensor reinstated 10-08 (explicit)").changed.version
        out = service.publish(result.tenant, result.site,
                              requests=requests(("battery-pcs-controller", "state-of-charge")),
                              effective_from=EARLIER, note="SOC removed")
        assert out.applies_until == from_08 and out.stopped_by_version == v4

        def soc_bound(at):
            return any(b.role == "battery_soc" for b in view(store, result, at=at).binding_set.bindings)

        assert not soc_bound(from_08 - timedelta(hours=1))
        assert soc_bound(from_08 + timedelta(days=1))
        kept = [s for s in store.binding_sets(result.tenant.id, result.site.id)
                if s.superseded_at is None and s.version == v4]
        assert kept and kept[0].change_note == "fuel sensor reinstated 10-08 (explicit)"
