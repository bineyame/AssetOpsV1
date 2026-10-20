"""S7-01a phase 1: `D-edge-health-cases` and the versioned two-clock Site source-health read.

Cases are persisted through registered gateway authentication and central ingestion
(`s7_health_cases.py`); the read selects registration and the latest diagnostic per gateway in one
repeatable-read transaction (`PostgresGatewayAccess.source_health_snapshot`). There is no derived
projection, so `STALE_PROJECTION` is not applicable; the inconsistent-selection refusal is tested.
"""

from __future__ import annotations

import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, converted, engine, imported, store  # noqa: F401

    from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess
    from assetops_backend.evidence.source_health import SelectionInconsistent, check_consistent
    from assetops_backend.source_health_api import build_source_health_router
    from s7_health_cases import DELAY, EPOCH, HealthCases

T0 = datetime(2026, 10, 16, 9, 0, 0, tzinfo=timezone.utc)
READ = T0 + timedelta(seconds=605)


class Rig:
    def __init__(self, store, engine, tmp_path) -> None:
        self.result, _ = converted(store)
        self.other = imported(store, code="KOBO-002")
        self.engine = engine
        self.clock = Clock(T0)
        self.cases = HealthCases(URL, "KOBO-001", tmp_path / "work", self.clock)
        self.access = PostgresGatewayAccess(URL)
        self.scopes = {
            "KOBO-001": ("KOBO-001", self.result.tenant.id, self.result.site.id),
            "KOBO-002": ("KOBO-002", self.other.tenant.id, self.other.site.id),
        }

    def advance(self, seconds: int) -> None:
        self.clock.now = self.clock.now + timedelta(seconds=seconds)

    def client(self, store=None, access=None) -> TestClient:
        app = FastAPI()
        kwargs = {} if access is None else {"access": access}
        app.include_router(build_source_health_router(
            self.access if store is None else store, lambda code: self.scopes.get(code.upper()), self.clock,
            **kwargs))
        return TestClient(app)

    def read(self, code: str = "KOBO-001", **kwargs):
        return self.client(**kwargs).get(f"/api/sites/{code}/source-health")


@pytest.fixture()
def rig(store, engine, tmp_path):
    owned = Rig(store, engine, tmp_path)
    yield owned
    owned.cases.close()
    pg_harness.dispose(owned.access)


@pytest.fixture()
def published(rig):
    rig.cases.register()
    receipts = rig.cases.publish(rig.advance)
    rig.clock.now = READ
    return receipts


def by_key(body: dict) -> dict[str, dict]:
    return {g["gateway_external_id"]: g for g in body["gateways"]}


class TestCentralCases:
    def test_six_cases_never_received_and_reload(self, rig, published) -> None:
        answer = rig.read()
        assert answer.status_code == 200
        body = answer.json()
        assert body["schema"] == {"id": "assetops.site-source-health", "version": 1}
        assert body["snapshot"] == {"isolation": "REPEATABLE_READ", "selection": "CONSISTENT"}
        assert body["stale_projection"]["applicable"] is False
        assert body["claim_scope"] == "GATEWAY_OPERATIONAL_REPORT" and "ASSET_CONDITION" in body["not_claimed"]
        rows = by_key(body)
        # The import gateway stays disabled and is reported as such; it is not counted as a source.
        assert rows["edge-kobo-001"]["registration"] == "DISABLED"
        assert body["summary"]["status"] == "NOT_ALL_CURRENT"
        assert body["summary"]["contact_counts"] == {"CURRENT": 6, "STALE": 1, "UNKNOWN": 1}
        assert body["summary"]["enabled_gateway_count"] == 8

        current = rows["s7-current"]
        assert current["contact"]["status"] == "CURRENT" and current["reported_facts"]["status"] == "CURRENT"
        assert current["sources"][0]["reported_contact_status"] == "REPORTED"
        assert current["sources"][0]["contact_basis"] == "GATEWAY_REPORTED_DEVICE_CONTACT"

        stale = rows["s7-stale-cadence"]
        assert stale["declared_cadence_seconds"] == 30
        assert stale["contact"]["status"] == "STALE"
        assert stale["contact"]["reason"] == "NO_RECEIPT_WITHIN_THRESHOLD_OUTAGE_START_NOT_DATED"
        assert stale["contact"]["last_received_at"] == "2026-10-16T09:00:00.000000Z"
        assert stale["reported_facts"]["status"] == "OLD"

        delayed = rows["s7-delayed-old"]
        assert delayed["contact"]["status"] == "CURRENT"
        assert delayed["reported_facts"]["status"] == "OLD"
        assert delayed["reported_facts"]["receipt_lag_seconds"] == int(DELAY.total_seconds())
        assert delayed["diagnostic"]["observed_at"] == "2026-10-16T03:10:00.000000Z"
        assert delayed["diagnostic"]["received_at"] == "2026-10-16T09:10:00.000000Z"

        queue = rows["s7-queue-growth"]
        assert queue["diagnostic"]["diagnostic_sequence"] == 2
        assert queue["reported_facts"]["queue"] == {"count": 900, "oldest_age_seconds": 5400, "as": "LAST_REPORTED"}

        clock = rows["s7-clock-offset"]
        assert clock["contact"]["status"] == "CURRENT"
        assert clock["reported_facts"]["clock"]["trust"] == "UNTRUSTED"
        assert clock["reported_facts"]["clock"]["offset_ms"] == 95_000
        assert clock["reported_facts"]["status"] == "UNKNOWN"
        assert clock["reported_facts"]["reason"] == "GATEWAY_CLOCK_UNTRUSTED"
        # D-2026-10-16-s701-clock L5: no age from an untrusted clock; the exact times stay for inspection.
        assert clock["reported_facts"]["fact_age_seconds"] is None
        assert clock["reported_facts"]["observed_at"] is not None
        assert clock["sources"][0]["reported_contact"] is not None
        assert clock["sources"][0]["reported_contact_age_seconds"] is None
        assert clock["reported_facts"]["clock"]["tolerance_ms"] == 5_000
        assert clock["reported_facts"]["clock"]["observed_after_receipt_allowance_ms"] == 5_000
        for row in body["gateways"]:
            ages = [row["reported_facts"]["fact_age_seconds"]] + [
                s["reported_contact_age_seconds"] for s in row["sources"]]
            assert all(a is None or a >= 0 for a in ages), row["gateway_external_id"]
        assert body["summary"]["reason"] is None

        stop = rows["s7-disk-stop"]["reported_facts"]
        assert stop["disk_pressure"] == {"value": "STOP", "as": "LAST_REPORTED",
                                         "provenance": "REPORTED_SIMULATED_GATEWAY"}
        assert stop["queue"]["count"] == 300
        recovery = rows["s7-disk-recovery"]
        assert recovery["diagnostic"]["diagnostic_sequence"] == 2
        assert recovery["reported_facts"]["disk_pressure"]["value"] == "OK"
        assert recovery["reported_facts"]["queue"] == {"count": 0, "oldest_age_seconds": None, "as": "LAST_REPORTED"}

        never = rows["s7-never-received"]
        assert never["registration"] == "ENABLED" and never["contact"]["status"] == "UNKNOWN"
        assert never["contact"]["reason"] == "NEVER_RECEIVED" and never["diagnostic"] is None
        assert never["reported_facts"]["status"] == "UNKNOWN" and never["reported_facts"]["queue"] is None
        assert never["sources"][0]["reported_contact_status"] == "NOT_IN_SELECTED_DIAGNOSTIC"

        # IDs, local sequence and both clocks match the stored rows and the ingestion receipts; reload is identical.
        for key, receipts in published.items():
            row = rows[key]
            assert row["diagnostic"]["diagnostic_id"] == receipts[-1]["diagnostic_id"]
            assert row["source_watermark"]["diagnostic_id"] == receipts[-1]["diagnostic_id"]
            assert row["diagnostic"]["sequence_epoch"] == EPOCH
        with rig.engine.connect() as c:
            stored = {str(r.id): r for r in c.execute(text(
                "SELECT id, diagnostic_sequence, received_at, observed_at FROM gateway_diagnostic"))}
        for row in body["gateways"]:
            if row["diagnostic"] is not None:
                s = stored[row["diagnostic"]["diagnostic_id"]]
                assert row["diagnostic"]["diagnostic_sequence"] == s.diagnostic_sequence
                assert row["diagnostic"]["received_at"] == s.received_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        assert len(stored) == 10  # the earlier queue/disk rows stay stored; only the latest is selected
        again = rig.read().json()
        assert again == body

    def test_deliver_gives_fresh_receipt_and_advances_the_local_sequence(self, rig, published) -> None:
        rig.clock.now = READ + timedelta(minutes=30)
        before = by_key(rig.read().json())
        assert before["s7-current"]["contact"]["status"] == "STALE"
        delivered = rig.cases.deliver()
        after = by_key(rig.read().json())
        for key in ("s7-current", "s7-delayed-old"):
            assert after[key]["contact"]["status"] == "CURRENT"
            assert after[key]["diagnostic"]["diagnostic_sequence"] == before[key]["diagnostic"]["diagnostic_sequence"] + 1
            assert after[key]["diagnostic"]["diagnostic_id"] == delivered[key]["diagnostic_id"]
        assert after["s7-current"]["reported_facts"]["status"] == "CURRENT"
        assert after["s7-delayed-old"]["reported_facts"]["status"] == "OLD"

    def test_deliver_all_current_contact_keys_keeps_each_case_meaning(self, rig, published) -> None:
        from s7_health_cases import CURRENT_CONTACT_KEYS
        rig.clock.now = READ + timedelta(minutes=30)
        rig.cases.deliver(CURRENT_CONTACT_KEYS)
        rows = by_key(rig.read().json())
        for key in CURRENT_CONTACT_KEYS:
            assert rows[key]["contact"]["status"] == "CURRENT", key
        assert rows["s7-stale-cadence"]["contact"]["status"] == "STALE"
        assert rows["s7-never-received"]["contact"]["status"] == "UNKNOWN"
        assert rows["s7-queue-growth"]["reported_facts"]["queue"]["count"] == 900
        assert rows["s7-clock-offset"]["reported_facts"]["reason"] == "GATEWAY_CLOCK_UNTRUSTED"
        assert rows["s7-disk-stop"]["reported_facts"]["disk_pressure"]["value"] == "STOP"
        assert rows["s7-disk-recovery"]["reported_facts"]["disk_pressure"]["value"] == "OK"
        assert rows["s7-delayed-old"]["reported_facts"]["status"] == "OLD"
        assert rows["s7-current"]["reported_facts"]["status"] == "CURRENT"

    def test_no_registered_source_and_wrong_site(self, rig, published) -> None:
        other = rig.read("KOBO-002").json()
        assert other["summary"]["status"] == "NO_REGISTERED_SOURCE"
        assert other["summary"]["enabled_gateway_count"] == 0
        assert other["summary"]["reason"] == "NO_ENABLED_GATEWAY"
        assert other["summary"]["source_watermark"]["selected_diagnostic_count"] == 0
        assert [g["gateway_external_id"] for g in other["gateways"]] == ["edge-kobo-002"]
        # A KOBO-001 gateway naming KOBO-002 is refused with no row; KOBO-002 still shows nothing received.
        cases = rig.cases
        cases.manifest = {**cases.manifest, "site_id": str(rig.other.site.id)}
        with pytest.raises(AssertionError, match="403"):
            cases.post("s7-current", 9, observed=rig.clock() - timedelta(seconds=2))
        assert rig.read("KOBO-002").json()["summary"]["source_watermark"]["selected_diagnostic_count"] == 0
        assert rig.read("NOT-A-SITE").status_code == 404


class TestRefusals:
    def test_identity_seam(self, rig) -> None:
        assert rig.read(access=lambda request, code: 401).status_code == 401
        assert rig.read(access=lambda request, code: 403).status_code == 403

    def test_store_failure_is_503_without_a_claim(self, rig) -> None:
        down = PostgresGatewayAccess("postgresql+psycopg://assetops:wrong@127.0.0.1:1/assetops_none_test?connect_timeout=2")
        answer = rig.read(store=down)
        assert answer.status_code == 503
        assert answer.json()["detail"]["code"] == "SOURCE_HEALTH_UNAVAILABLE"
        assert answer.json()["detail"]["gateways"] is None
        pg_harness.dispose(down)

    def test_inconsistent_selection_is_refused(self, rig, published) -> None:
        snapshot = rig.access.source_health_snapshot(rig.result.tenant.id, rig.result.site.id)
        check_consistent(snapshot, READ)  # the real selection is consistent
        diagnostic = snapshot.diagnostics[0]
        other_gateway = next(g.gateway_id for g in snapshot.gateways if g.gateway_id != diagnostic.gateway_id)
        doctored = (
            replace(snapshot, diagnostics=snapshot.diagnostics + (diagnostic,)),  # two latest for one gateway
            replace(snapshot, diagnostics=(replace(diagnostic, gateway_id=other_gateway),)),  # row/text disagree
            replace(snapshot, diagnostics=(replace(diagnostic, site_id=rig.other.site.id),)),  # foreign Site
            replace(snapshot, gateways=snapshot.gateways[1:]),  # registration missing a selected gateway
            replace(snapshot, isolation="read committed"),  # not one snapshot
        )
        for bad in doctored:
            with pytest.raises(SelectionInconsistent):
                check_consistent(bad, READ)
        with pytest.raises(SelectionInconsistent, match="after the read time"):
            check_consistent(snapshot, T0)

        class Doctored:
            def source_health_snapshot(self, tenant_id, site_id):
                return doctored[1]

        answer = rig.read(store=Doctored())
        assert answer.status_code == 409
        assert answer.json()["detail"]["code"] == "SOURCE_HEALTH_SELECTION_INCONSISTENT"
        assert answer.json()["detail"]["gateways"] is None

    def test_registration_and_diagnostics_share_one_snapshot(self, rig, published) -> None:
        """A diagnostic committed between the registration and diagnostic statements is not selected."""
        cases = rig.cases

        class Racing(PostgresGatewayAccess):
            @staticmethod
            def _health_latest(c, tenant_id, site_id):
                cases.post("s7-never-received", 1, observed=rig.clock() - timedelta(seconds=2))
                return PostgresGatewayAccess._health_latest(c, tenant_id, site_id)

        racing = Racing(URL)
        try:
            snapshot = racing.source_health_snapshot(rig.result.tenant.id, rig.result.site.id)
        finally:
            pg_harness.dispose(racing)
        never = next(g.gateway_id for g in snapshot.gateways if g.gateway_external_id == "s7-never-received")
        assert never not in {d.gateway_id for d in snapshot.diagnostics}
        assert snapshot.isolation == "repeatable read"
        # The next read sees it.
        assert by_key(rig.read().json())["s7-never-received"]["contact"]["status"] == "CURRENT"

    def test_s2_gateway_health_contract_is_unchanged(self, rig, published) -> None:
        from assetops_backend.gateway_api import build_gateway_router

        app = FastAPI()
        app.include_router(build_gateway_router(None, None, rig.access,
                                                lambda code: (rig.result.tenant.id, rig.result.site.id), rig.clock))
        row = next(g for g in TestClient(app).get("/api/sites/KOBO-001/gateway-health").json()["gateways"]
                   if g["gateway_external_id"] == "s7-delayed-old")
        assert row["status"] == "CURRENT" and "reported_facts" not in row and "contact" not in row

