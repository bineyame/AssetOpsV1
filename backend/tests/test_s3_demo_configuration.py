"""S3-01 phase 1b: the labelled simulated demo configuration (generator values + roles-2).

In-memory always; the Postgres path runs when `ASSETOPS_TEST_DATABASE_URL`
names a `*_test` database (skipped, never passed, without it).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from test_s1_bindings import CONVERTED_AT, converted
from test_s1_cutover import Clock

from assetops_backend.sites.binding_service import BindingService, readiness
from assetops_backend.sites.demo_configuration import (
    DemoConfigurationConflict,
    apply_demo_configuration,
)
from assetops_backend.sites.foundation_service import FoundationService, binding_set_at, revision_at

BACKEND = Path(__file__).resolve().parents[1]
DEMO = json.loads((BACKEND / "conversions" / "kobo-001-s3-dispatch-demo-config.json").read_text(encoding="utf-8"))
CONFIG_FROM = datetime(2026, 10, 1, tzinfo=timezone.utc)
BINDINGS_FROM = datetime(2026, 10, 2, tzinfo=timezone.utc)
BEFORE = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
FAR = datetime(9999, 1, 1, tzinfo=timezone.utc)
CAPABILITY = {
    ("pv-inverter-controller", "available-power", "pv_available_power"),
    ("battery-pcs-controller", "discharge-capability", "pcs_discharge_capability"),
}


def apply(store, result, when, steps=("properties", "bindings")):
    clock = Clock(when)
    return apply_demo_configuration(
        store, FoundationService(store, "demo", clock), BindingService(store, clock),
        result.tenant, result.site, DEMO, steps=steps,
    )


def assert_configured(store, result, outcome) -> None:
    sets = store.binding_sets(result.tenant.id, result.site.id)
    revisions = store.revisions(result.tenant.id, result.site.id)
    after, before = binding_set_at(sets, BINDINGS_FROM, FAR), binding_set_at(sets, CONFIG_FROM, FAR)
    assert after.role_set == "minigrid-roles-2" and before.role_set == "minigrid-roles-1"
    channels = {(b.device_id, b.signal_id, b.role) for b in after.bindings}
    assert CAPABILITY <= channels
    assert not CAPABILITY & {(b.device_id, b.signal_id, b.role) for b in before.bindings}
    # every roles-1 binding is carried unchanged
    assert {(b.device_id, b.signal_id, b.role, b.conversion["kind"]) for b in before.bindings} <= {
        (b.device_id, b.signal_id, b.role, b.conversion["kind"]) for b in after.bindings
    }
    revision = revision_at(revisions, CONFIG_FROM, FAR)
    later = revision_at(revisions, BINDINGS_FROM, FAR)
    assert next(c for c in later.content["components"] if c["component_id"] == "generator") == next(
        c for c in revision.content["components"] if c["component_id"] == "generator")
    generator = next(c for c in revision.content["components"] if c["component_id"] == "generator")
    props = {p["property_key"]: p for p in generator["properties"]}
    assert props["start-soc-threshold"]["value"] == 35 and props["start-soc-threshold"]["source"] == "TEMPLATE"
    assert props["start-delay"]["source_version"] == 2
    assert any("s3-dispatch-demo-config-v1" in (r.change_note or "") for r in revisions if r.valid_from == CONFIG_FROM)
    assert "start-delay" not in {
        p["property_key"]
        for c in revision_at(revisions, BEFORE, FAR).content["components"] for p in c.get("properties") or ()
    }
    first, second = outcome.periods
    assert (first["role_set"], first["foundation_version"]) == ("minigrid-roles-1", revision.version)
    assert (second["role_set"], second["binding_version"], second["foundation_version"]) == (
        "minigrid-roles-2", after.version, later.version)
    assert second["snapshot_sha256"] == after.snapshot_sha256 and len(outcome.capability_channels) == 2
    view = FoundationService(store, "demo", Clock(FAR)).read(result.site, result.tenant, BINDINGS_FROM, None)
    assert readiness(view.site, view.revision, view.registrations, view.binding_set)["state"] == "READY_TO_REPORT"


class TestInMemory:
    def test_publishes_properties_then_roles_2_and_replays_as_a_no_op(self) -> None:
        store, result, _ = converted()
        first = apply(store, result, CONVERTED_AT + timedelta(minutes=10))
        assert first.properties_published and first.bindings_published
        assert_configured(store, result, first)
        counts = (len(store.revisions(result.tenant.id, result.site.id)),
                  len(store.binding_sets(result.tenant.id, result.site.id)))
        again = apply(store, result, CONVERTED_AT + timedelta(minutes=20))
        assert not again.properties_published and not again.bindings_published
        assert again.to_wire() | {"properties_published": True, "bindings_published": True} == first.to_wire()
        assert counts == (len(store.revisions(result.tenant.id, result.site.id)),
                          len(store.binding_sets(result.tenant.id, result.site.id)))

    def test_properties_step_alone_leaves_no_capability_channel(self) -> None:
        store, result, _ = converted()
        only = apply(store, result, CONVERTED_AT + timedelta(minutes=10), steps=("properties",))
        assert only.properties_published and not only.bindings_published
        assert {p["role_set"] for p in only.periods} == {"minigrid-roles-1"} and only.capability_channels == ()
        both = apply(store, result, CONVERTED_AT + timedelta(minutes=20))
        assert not both.properties_published and both.bindings_published
        assert_configured(store, result, both)

    def test_bindings_step_alone_is_refused_until_properties_are_in_effect(self) -> None:
        store, result, _ = converted()
        before = (len(store.revisions(result.tenant.id, result.site.id)),
                  len(store.binding_sets(result.tenant.id, result.site.id)))
        with pytest.raises(DemoConfigurationConflict, match="properties step first"):
            apply(store, result, CONVERTED_AT + timedelta(minutes=10), steps=("bindings",))
        assert before == (len(store.revisions(result.tenant.id, result.site.id)),
                          len(store.binding_sets(result.tenant.id, result.site.id)))
        apply(store, result, CONVERTED_AT + timedelta(minutes=20), steps=("properties",))
        done = apply(store, result, CONVERTED_AT + timedelta(minutes=30), steps=("bindings",))
        assert done.bindings_published
        assert_configured(store, result, done)

    def test_a_fixture_for_another_site_or_unlabelled_writes_nothing(self) -> None:
        store, result, _ = converted()
        before = len(store.revisions(result.tenant.id, result.site.id))
        for bad in (DEMO | {"site_code": "OTHER-001"}, DEMO | {"status": "Site truth"}):
            with pytest.raises(DemoConfigurationConflict):
                apply_demo_configuration(store, FoundationService(store, "demo", Clock(CONVERTED_AT)),
                                         BindingService(store, Clock(CONVERTED_AT)), result.tenant, result.site, bad)
        assert len(store.revisions(result.tenant.id, result.site.id)) == before


URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
class TestPostgres:
    def test_same_publication_through_postgres(self) -> None:
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url

        from test_s1_bindings_postgres import NOW, converted as pg_converted, engine as _engine  # noqa: F401
        from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

        assert make_url(URL).database.endswith("_test")
        from alembic import command
        from alembic.config import Config

        eng = create_engine(URL)
        with eng.begin() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
            connection.execute(text("DROP EXTENSION IF EXISTS btree_gist"))
        config = Config(str(BACKEND / "alembic.ini"))
        config.attributes["database_url"] = URL
        command.upgrade(config, "head")
        eng.dispose()
        store = PostgresFoundationStore(URL)
        result, _ = pg_converted(store)
        first = apply(store, result, NOW - timedelta(minutes=30))
        assert first.properties_published and first.bindings_published
        assert_configured(store, result, first)
        again = apply(store, result, NOW - timedelta(minutes=20))
        assert not again.properties_published and not again.bindings_published
