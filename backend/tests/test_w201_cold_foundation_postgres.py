"""W2-01 cold Foundation persistence and the selected cold read against PostgreSQL.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped (never passed) without it.
`.agent/W2-technical-design-cold.md` section 3 and the W2-01 acceptance row; `tasks/W2-01-cold-foundation.md`
phase 1.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from alembic import command
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    from assetops_backend.cold_foundation_api import build_cold_foundation_router
    from assetops_backend.evidence.ledger import LedgerUnavailable
    from assetops_backend.sites.adapters.import_files import read_import_source
    from assetops_backend.sites.binding_conversion import convert
    from assetops_backend.sites.binding_service import BindingRefused, BindingRequest, BindingService
    from assetops_backend.sites.cold_foundation import (
        MESSAGE_POLICY,
        MESSAGE_PROBE,
        MESSAGE_START,
        MESSAGE_TRANSFER,
    )
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.foundation_service import (
        FoundationRefused,
        FoundationService,
        ImportSource,
        import_site,
    )
    from test_s1_bindings_postgres import KOBO_SOURCE, Clock, _alembic, engine, store  # noqa: F401

BACKEND = Path(__file__).resolve().parents[1]
FIXTURES = BACKEND / "tests" / "fixtures" / "w2"
NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
ORIGIN = datetime(2026, 10, 1, tzinfo=timezone.utc)
CHANGE = datetime(2026, 10, 10, tzinfo=timezone.utc)
OLD_AT = "2026-10-05T00:00:00Z"
NEW_AT = "2026-10-10T12:00:00Z"


def bindings_fixture(code: str) -> dict:
    return json.loads((BACKEND / "conversions" / f"{code.lower()}-bindings.json").read_text(encoding="utf-8"))


def imported(store, code: str, *, convert_bindings: bool = True, when: datetime = NOW - timedelta(hours=3)):
    source = read_import_source(str(FIXTURES / f"{code.lower()}.yaml"))
    result = import_site(
        store, tenant_slug="demo", configured_tenant_slug="demo",
        source=ImportSource(path=f"var/sites/{code.lower()}.yaml", sha256=source.sha256, record=source.record),
        legacy_documents=(), clock=Clock(when),
    )
    if convert_bindings:
        convert(store, BindingService(store, Clock(when + timedelta(minutes=5))), result.tenant, result.site,
                bindings_fixture(code))
    return result


def kobo(store):
    source = read_import_source(str(KOBO_SOURCE))
    return import_site(
        store, tenant_slug="demo", configured_tenant_slug="demo",
        source=ImportSource(path="var/sites/kobo-001.yaml", sha256=source.sha256, record=source.record),
        legacy_documents=(), clock=Clock(NOW - timedelta(hours=4)),
    )


@dataclass
class Diagnostic:
    received_at: datetime


@dataclass
class Facts:
    gateway_id: object
    cadence_seconds: int
    latest: Diagnostic | None


class Health:
    def __init__(self, received_at=None, fail=False):
        self.received_at, self.fail, self.calls = received_at, fail, []

    def gateway_health(self, tenant_id, site_id):
        self.calls.append((tenant_id, site_id))
        if self.fail:
            raise LedgerUnavailable("diagnostics store down")
        regs = self.store.registrations(tenant_id, site_id)
        latest = None if self.received_at is None else Diagnostic(self.received_at)
        return [Facts(g.id, 300, latest) for g in regs.gateways]


class OtherGatewayHealth(Health):
    """A health store whose only diagnostic belongs to a gateway this Site does not select."""

    def gateway_health(self, tenant_id, site_id):
        self.calls.append((tenant_id, site_id))
        return [Facts(uuid.uuid4(), 300, Diagnostic(NOW - timedelta(minutes=5)))]


def client(store, health=None, access=None, now=NOW):
    service = FoundationService(store, "demo", Clock(now))
    app = FastAPI()
    if health is not None:
        health.store = store
    kwargs = {} if access is None else {"access": access}
    app.include_router(build_cold_foundation_router(ImportedSiteRegistry(service), health, Clock(now), **kwargs))
    return TestClient(app)


def read(c, code="COLD-001", **params):
    return c.get(f"/api/sites/{code}/cold/foundation", params=params)


def codes(body):
    return [m["code"] for m in body["readiness"]["messages"]]


class TestPersistAndRead:
    def test_complete_fixture_persists_reloads_and_is_ready(self, store) -> None:
        result = imported(store, "COLD-001")
        view = FoundationService(store, "demo", Clock(NOW)).read(result.site, result.tenant, None, None)
        assert view.site.site_type == "COLDCHAIN" and view.binding_set.role_set == "cold-roles-1"
        assert len(view.binding_set.bindings) == 11
        assert {c["component_type"] for c in view.revision.content["components"]} >= {
            "COLD_ROOM", "TEMPERATURE_PROBE", "COMPRESSOR", "TRANSFER_SWITCH"}
        body = read(client(store, Health())).json()
        assert set(body) == {"foundation_revision_id", "valid_from", "valid_to", "rooms", "topology", "bindings",
                             "readiness", "commissioning", "contact"}
        assert body["foundation_revision_id"] == str(view.revision.id)
        assert body["readiness"] == {"state": "READY_TO_REPORT", "messages": []}
        assert body["commissioning"] == {"state": "UNCONFIRMED", "evidence_ids": []}
        assert body["contact"] == {"state": "NEVER", "as_of": None, "limitations": []}
        assets = {a.asset_code: str(a.id) for a in view.registrations.assets}
        [room] = body["rooms"]
        assert room == {"asset_id": assets["cold-room"],
                        "policy": {"low": 2.0, "high": 8.0, "unit": "degC", "revision_id": str(view.revision.id)},
                        "probe_ids": [assets["chamber-probe"]], "compressor_ids": [assets["compressor"]]}
        assert {e["medium"] for e in body["topology"]["edges"]} == {"SIGNAL", "THERMAL", "AC"}
        by_role = {b["role"]: b for b in body["bindings"]}
        assert by_role["chamber_temperature"]["cadence_seconds"] == 300
        assert by_role["chamber_temperature"]["publication_mode"] == "periodic"
        assert by_role["backup_start_event"]["cadence_seconds"] is None
        assert by_role["backup_start_event"]["publication_mode"] == "transition"
        assert by_role["backup_start_event"]["unit"] == "event"
        assert set(by_role["grid_state"]) == {"role", "asset_id", "source_id", "unit", "cadence_seconds",
                                              "publication_mode"}

    def test_missing_probe_fixture_says_what_to_add_and_transfer_is_unknown(self, store) -> None:
        imported(store, "COLD-002")
        body = read(client(store, Health()), "COLD-002").json()
        assert body["readiness"]["state"] == "CONFIGURATION_INCOMPLETE"
        messages = {m["code"]: m for m in body["readiness"]["messages"]}
        assert messages["PROBE_MISSING"]["message"] == MESSAGE_PROBE == (
            "Add a chamber temperature probe and bind its °C reading")
        assert messages["PROBE_MISSING"]["blocking"] is True
        assert messages["TRANSFER_UNREPORTED"]["message"] == MESSAGE_TRANSFER
        assert messages["TRANSFER_UNREPORTED"]["blocking"] is False
        assert body["rooms"][0]["probe_ids"] == []
        assert body["commissioning"] == {"state": "UNCONFIRMED", "evidence_ids": []}

    def test_missing_policy_and_start_event_name_their_gaps(self, store) -> None:
        result = imported(store, "COLD-001", convert_bindings=False)
        fixture = bindings_fixture("COLD-001")
        fixture["bindings"] = [b for b in fixture["bindings"] if b["role"] != "backup_start_event"]
        convert(store, BindingService(store, Clock(NOW - timedelta(hours=2))), result.tenant, result.site, fixture)
        body = read(client(store, Health())).json()
        assert "START_EVENT_MISSING" in codes(body)
        assert MESSAGE_START in [m["message"] for m in body["readiness"]["messages"]]
        # A Foundation without the room's policy band: the policy message names the gap.
        source = read_import_source(str(FIXTURES / "cold-001.yaml"))
        record = source.record
        room = next(c for c in record.foundation.components if c.component_id == "cold-room")
        stripped = replace(room, properties=tuple(p for p in room.properties if not p.property_key.startswith(
            "cold-policy")))
        foundation = replace(record.foundation, components=tuple(
            stripped if c.component_id == "cold-room" else c for c in record.foundation.components))
        other = import_site(
            store, tenant_slug="demo", configured_tenant_slug="demo",
            source=ImportSource(path="var/sites/cold-003.yaml", sha256="0" * 64,
                                record=replace(record, site_id="COLD-003", foundation=foundation)),
            legacy_documents=(), clock=Clock(NOW - timedelta(hours=2)))
        body = read(client(store, Health()), "COLD-003").json()
        policy = [m for m in body["readiness"]["messages"] if m["code"] == "POLICY_MISSING"]
        assert [m["message"] for m in policy] == [MESSAGE_POLICY]
        assert body["rooms"][0]["policy"]["low"] is None and other.created
        assert body["bindings"] == [] and "START_EVENT_MISSING" in codes(body)


class TestHistory:
    def test_old_and_current_selection_change_policy_bindings_and_topology_without_rewriting(self, store) -> None:
        result = imported(store, "COLD-001", when=datetime(2026, 10, 2, tzinfo=timezone.utc))
        later = Clock(datetime(2026, 10, 3, tzinfo=timezone.utc))
        service = FoundationService(store, "demo", later)
        before = {(r.id, r.content_sha256) for r in store.revisions(result.tenant.id, result.site.id)}
        service.publish_component_properties(
            result.tenant, result.site, asset_code="cold-room", effective_from=CHANGE, note="tighter band",
            properties=[{"property_key": "cold-policy-high", "value": 6.5, "unit": "degC", "source": "SITE",
                         "source_version": 1}])
        topology = json.loads(json.dumps(
            FoundationService(store, "demo", Clock(NOW)).read(result.site, result.tenant, None, None)
            .revision.content["topology"]))
        topology["connections"] = [e for e in topology["connections"] if e["medium"] != "SIGNAL"]
        FoundationService(store, "demo", Clock(datetime(2026, 10, 3, 1, tzinfo=timezone.utc))).publish_topology(
            result.tenant, result.site, topology=topology, effective_from=CHANGE + timedelta(days=1),
            note="probe link removed")
        fixture = bindings_fixture("COLD-001")
        regs = store.registrations(result.tenant.id, result.site.id)
        ids = {a.asset_code: str(a.id) for a in regs.assets}
        requests = [BindingRequest(b["device_id"], b["signal_id"], ids[b["asset_code"]], b["role"], b["source_unit"],
                                   b["canonical_unit"], b["conversion"])
                    for b in fixture["bindings"] if b["role"] != "door_event"]
        BindingService(store, Clock(datetime(2026, 10, 3, 2, tzinfo=timezone.utc))).publish(
            result.tenant, result.site, requests=requests, effective_from=CHANGE + timedelta(days=1),
            note="door sensor unbound")
        after = {(r.id, r.content_sha256) for r in store.revisions(result.tenant.id, result.site.id)}
        assert before <= after  # history kept: every earlier revision row still exists unchanged
        c = client(store, Health())
        old, new = read(c, at=OLD_AT).json(), read(c, at="2026-10-15T00:00:00Z").json()
        assert old["rooms"][0]["policy"]["high"] == 8.0 and new["rooms"][0]["policy"]["high"] == 6.5
        assert old["foundation_revision_id"] != new["foundation_revision_id"]
        assert "door_event" in {b["role"] for b in old["bindings"]}
        assert "door_event" not in {b["role"] for b in new["bindings"]}
        assert "SIGNAL" in {e["medium"] for e in old["topology"]["edges"]}
        assert "SIGNAL" not in {e["medium"] for e in new["topology"]["edges"]}
        assert old["readiness"]["state"] == "READY_TO_REPORT"
        assert new["readiness"]["state"] == "CONFIGURATION_INCOMPLETE" and "PROBE_MISSING" in codes(new)
        middle = read(c, at=NEW_AT).json()  # band changed, topology and bindings not yet
        assert middle["rooms"][0]["policy"]["high"] == 6.5 and "door_event" in {b["role"] for b in middle["bindings"]}


class TestRefusals:
    def revisions(self, store, result):
        return len(store.revisions(result.tenant.id, result.site.id))

    def test_policy_low_not_below_high_and_wrong_unit_are_refused_and_nothing_written(self, store) -> None:
        result = imported(store, "COLD-001")
        count = self.revisions(store, result)
        service = FoundationService(store, "demo", Clock(NOW))
        for value, unit, match in ((1.0, "degC", "must be below its high"), (9.0, "kW", "must be 'degC'")):
            with pytest.raises(FoundationRefused, match=match) as refused:
                service.publish_component_properties(
                    result.tenant, result.site, asset_code="cold-room", effective_from=CHANGE, note="bad",
                    properties=[{"property_key": "cold-policy-high" if unit == "degC" else "cold-policy-low",
                                 "value": value, "unit": unit, "source": "SITE", "source_version": 1}])
            assert refused.value.code == "FOUNDATION_VALUE_INVALID"
        assert self.revisions(store, result) == count

    @pytest.mark.parametrize("extra, match", [
        ({"connection_id": "room-to-ambient", "from_node": "cold-room", "to_node": "ambient-probe",
          "medium": "SIGNAL"}, "already has a primary chamber probe"),
        ({"connection_id": "dup", "from_node": "backup-bus", "to_node": "compressor", "medium": "AC"}, "duplicates"),
        ({"connection_id": "back", "from_node": "backup-bus", "to_node": "transfer-switch", "medium": "AC"},
         "does not declare"),
        ({"connection_id": "ghost", "from_node": "cold-room", "to_node": "ghost-switch", "medium": "SIGNAL"},
         "ghost-switch"),
    ])
    def test_bad_topology_revision_is_refused(self, store, extra, match) -> None:
        result = imported(store, "COLD-001")
        count = self.revisions(store, result)
        service = FoundationService(store, "demo", Clock(NOW))
        topology = json.loads(json.dumps(service.read(result.site, result.tenant, None, None)
                                         .revision.content["topology"]))
        topology["connections"].append(extra)
        with pytest.raises(FoundationRefused, match=match):
            service.publish_topology(result.tenant, result.site, topology=topology, effective_from=CHANGE,
                                     note="bad")
        assert self.revisions(store, result) == count

    def bind(self, store, result, mutate, effective_from=CHANGE):
        regs = store.registrations(result.tenant.id, result.site.id)
        ids = {a.asset_code: str(a.id) for a in regs.assets}
        items = mutate([dict(b) for b in bindings_fixture(result.site.site_code)["bindings"]], ids)
        requests = [BindingRequest(b["device_id"], b["signal_id"], b.get("asset_id") or ids[b["asset_code"]],
                                   b["role"], b["source_unit"], b["canonical_unit"], b["conversion"]) for b in items]
        return BindingService(store, Clock(NOW)).publish(result.tenant, result.site, requests=requests,
                                                         effective_from=effective_from, note="test")

    def refused_code(self, store, result, mutate, **kw):
        with pytest.raises(BindingRefused) as refused:
            self.bind(store, result, mutate, **kw)
        return {p["code"] for p in refused.value.problems} or {refused.value.code}

    def test_overlapping_and_stale_bindings_are_refused(self, store) -> None:
        result = imported(store, "COLD-001")
        count = len(store.binding_sets(result.tenant.id, result.site.id))
        twice = lambda items, ids: items + [dict(items[0])]  # noqa: E731
        assert "BINDING_CHANNEL_OVERLAP" in self.refused_code(store, result, twice)
        role_twice = lambda items, ids: items + [  # noqa: E731
            {**items[0], "device_id": "ambient-probe", "asset_code": "chamber-probe"}]
        assert self.refused_code(store, result, role_twice) & {"BINDING_ROLE_CONFLICT", "BINDING_CHANNEL_OVERLAP"}
        stale = self.refused_code(store, result, lambda items, ids: items,
                                  effective_from=ORIGIN - timedelta(days=30))
        assert stale & {"BINDING_FOUNDATION_MISSING", "BINDING_INTERVAL_INVALID", "FOUNDATION_INTERVAL_INVALID"}
        assert len(store.binding_sets(result.tenant.id, result.site.id)) == count

    def test_channel_role_and_unit_rules(self, store) -> None:
        result = imported(store, "COLD-001")

        def swap(items, ids):
            for b in items:
                if b["role"] == "grid_power_event":
                    b["device_id"], b["signal_id"] = "generator-controller", "start-event"
                if b["role"] == "backup_start_event":
                    b["device_id"], b["signal_id"] = "grid-meter", "event"
            return items

        assert "BINDING_CHANNEL_ROLE_MISMATCH" in self.refused_code(store, result, swap)

        def wrong_unit(items, ids):
            for b in items:
                if b["role"] == "chamber_temperature":
                    b["canonical_unit"] = "kW"
            return items

        assert "BINDING_UNIT_MISMATCH" in self.refused_code(store, result, wrong_unit)

        def event_on_number(items, ids):
            for b in items:
                if b["role"] == "backup_start_event":
                    b["role"], b["canonical_unit"] = "generator_state", "state"
            return [b for b in items if not (b["role"] == "generator_state" and b["signal_id"] == "state")]

        assert self.refused_code(store, result, event_on_number) & {
            "BINDING_CONVERSION_INVALID", "BINDING_CHANNEL_ROLE_MISMATCH"}

    def test_transfer_result_on_an_undeclared_transfer_switch_is_refused(self, store) -> None:
        result = imported(store, "COLD-001")

        def on_generator(items, ids):
            for b in items:
                if b["role"] == "transfer_result":
                    b["asset_code"] = "generator"
            return items

        assert "BINDING_ROLE_ASSET_MISMATCH" in self.refused_code(store, result, on_generator)

    def test_another_sites_asset_cannot_be_bound(self, store) -> None:
        first = imported(store, "COLD-001")
        second = imported(store, "COLD-002", when=NOW - timedelta(hours=2))
        foreign = {a.asset_code: str(a.id) for a in store.registrations(second.tenant.id, second.site.id).assets}

        def foreign_asset(items, ids):
            items[0]["asset_id"] = foreign["cold-room"] if items[0]["asset_code"] == "cold-room" else foreign[
                "ambient-probe"]
            return items

        assert "BINDING_ASSET_UNKNOWN" in self.refused_code(store, first, foreign_asset)


class TestReadRefusals:
    def test_access_type_and_parameter_refusals(self, store) -> None:
        imported(store, "COLD-001")
        kobo(store)
        c = client(store, Health())
        assert read(c, "KOBO-001").status_code == 404  # wrong Site type
        missing = read(c, "COLD-999")
        assert missing.status_code == 404 and missing.json()["error"]["code"] == "SITE_NOT_FOUND"
        for bad in ("yesterday", "2026-10-05T00:00:00", "2026-10-05T03:00:00+03:00"):
            refused = read(c, at=bad)
            assert refused.status_code == 422 and refused.json()["error"]["code"] == "COLD_TIME_INVALID"
        unknown = c.get("/api/sites/COLD-001/cold/foundation", params={"from": OLD_AT})
        assert unknown.status_code == 422 and unknown.json()["error"]["code"] == "COLD_PARAMETER_UNKNOWN"
        before = read(c, at="2026-09-01T00:00:00Z")
        assert before.status_code == 404 and before.json()["error"]["code"] == "FOUNDATION_REVISION_NOT_FOUND"
        for status in (401, 403):
            denied = read(client(store, Health(), access=lambda request, code, s=status: s))
            assert denied.status_code == status and set(denied.json()) == {"error"}
        forbidden_other = client(store, Health(), access=lambda request, code: 403 if code == "COLD-001" else None)
        assert read(forbidden_other).status_code == 403

    def test_contact_states_and_unavailable_store(self, store) -> None:
        result = imported(store, "COLD-001")
        recent = read(client(store, Health(NOW - timedelta(minutes=5)))).json()["contact"]
        assert recent == {"state": "RECENT", "as_of": "2026-10-17T11:55:00Z", "limitations": []}
        stale = read(client(store, Health(NOW - timedelta(hours=2)))).json()["contact"]
        assert stale["state"] == "STALE" and stale["as_of"] == "2026-10-17T10:00:00Z"
        # D-2026-10-17-f5-subtabs-and-contact: the two null cases are NEVER with as_of null and a naming limitation.
        no_store = read(client(store, None))
        assert no_store.status_code == 200
        assert no_store.json()["contact"] == {
            "state": "NEVER", "as_of": None, "limitations": ["No gateway health read is configured"]}
        unmatched = read(client(store, OtherGatewayHealth()))
        assert unmatched.status_code == 200
        assert unmatched.json()["contact"] == {
            "state": "NEVER", "as_of": None, "limitations": ["No diagnostic is recorded for the selected gateway"]}
        down = read(client(store, Health(fail=True)))
        assert down.status_code == 503 and down.json()["error"]["code"] == "GATEWAY_ACCESS_UNAVAILABLE"
        health = Health()
        read(client(store, health))
        assert health.calls == [(result.tenant.id, result.site.id)]  # scoped to the requested tenant/Site

    @pytest.mark.parametrize(
        "gateway_count, limitation",
        [(2, "No gateway is selected for this site"), (0, "No gateway is registered for this site")],
    )
    def test_no_binding_set_without_one_gateway_names_the_missing_selection(
        self, store, gateway_count, limitation
    ) -> None:
        # W2-01 re-review Low 1: with no binding set, two registered gateways leave none selected and zero leave
        # none registered (cold_foundation_api.py wanted-gateway branch); both are NEVER with as_of null.
        imported(store, "COLD-001", convert_bindings=False)

        class GatewayCountStore:
            def __init__(self, inner):
                self._inner = inner

            def __getattr__(self, name):
                return getattr(self._inner, name)

            def registrations(self, tenant_id, site_id):
                regs = self._inner.registrations(tenant_id, site_id)
                assert len(regs.gateways) == 1
                extra = replace(regs.gateways[0], id=uuid.uuid4(), gateway_external_id="edge-cold-extra")
                return replace(regs, gateways=(regs.gateways[0], extra)[:gateway_count])

        response = read(client(GatewayCountStore(store), Health(NOW - timedelta(minutes=5))))
        assert response.status_code == 200
        assert response.json()["contact"] == {"state": "NEVER", "as_of": None, "limitations": [limitation]}


class TestMigration0021:
    def test_upgrade_and_downgrade_touch_no_rows_and_old_reads_still_work(self, store, engine) -> None:
        imported(store, "COLD-001")
        kobo(store)
        tables = ("foundation_revision", "signal_binding_set_revision", "signal_binding_revision", "asset", "site")

        def snapshot():
            with engine.connect() as connection:
                return {t: sorted(map(str, connection.execute(text(f"SELECT * FROM {t}")).all())) for t in tables}

        def head():
            with engine.connect() as connection:
                return connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

        before = snapshot()
        assert head() == "0030_w4_mini_decisions"
        config = _alembic()
        engine.dispose()
        try:
            command.downgrade(config, "0020_w2_source_event")
            assert head() == "0020_w2_source_event" and snapshot() == before
        finally:
            command.upgrade(config, "head")
        assert head() == "0030_w4_mini_decisions" and snapshot() == before
        service = FoundationService(store, "demo", Clock(NOW))
        kobo_site = service.site(service.tenant(), "KOBO-001")
        assert service.read(kobo_site, service.tenant(), None, None).revision.content["components"]
        assert read(client(store, Health())).status_code == 200
