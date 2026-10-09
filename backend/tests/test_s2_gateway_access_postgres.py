"""S2-02 phase 2: gateway credential, provisioning, TLS boundary and central diagnostics.

Runs against the Postgres test database (`ASSETOPS_TEST_DATABASE_URL`).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import Clock, converted, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import LEDGER_TABLES, RECEIVED, Kit, ingestion

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess
    from assetops_backend.evidence.gateway_access import (
        DiagnosticIngestionService,
        StoreGatewayPrincipals,
    )
    from assetops_backend.evidence.provision_gateway import main as provision
    from assetops_backend.evidence.service import IngestionService
    from assetops_backend.evidence_api import build_evidence_router
    from assetops_backend.gateway_api import build_gateway_router, install_gateway_tls_boundary
    from assetops_contracts.gateway_diagnostics import seal_gateway_diagnostics_v1
    from assetops_contracts.ingestion_receipt_v2 import parse_canonical_receipt_v2_text

ACCESS_TABLES = ("gateway_credential", "gateway_access_event", "gateway_diagnostic", "gateway_diagnostic_refusal")
REAL_NOW = datetime(2026, 10, 9, 9, 0, 0, tzinfo=timezone.utc)


class _NoSites:
    def get_site(self, site_id):  # pragma: no cover - never reached by these routes
        raise AssertionError


class Rig:
    """A converted Kobo Site exactly as import leaves it: gateway and sources disabled."""

    def __init__(self, store, engine, tmp_path) -> None:
        result, outcome = converted(store)
        self.kit = Kit(engine, outcome.published.changed.id)
        self.engine = engine
        self.tmp = tmp_path
        self.site_code = result.site.site_code
        self.site_uuid = result.site.id
        self.tenant_uuid = result.tenant.id
        with engine.connect() as c:
            self.gateway_external = c.execute(
                text("SELECT gateway_external_id FROM gateway WHERE id = :g"),
                {"g": self.kit.principal.gateway_id}).scalar_one()
            self.sources = {r.id: r.source_external_id for r in c.execute(
                text("SELECT id, source_external_id FROM source WHERE gateway_id = :g"),
                {"g": self.kit.principal.gateway_id}).all()}
        self.pv_source = UUID(self.kit.binding("pv-inverter-controller")["source_id"])
        self.access = PostgresGatewayAccess(URL)
        self.clock = Clock(REAL_NOW)

    def provision(self, *args: str) -> int:
        return provision(["--tenant", "demo", "--site", self.site_code, "--gateway", self.gateway_external, *args],
                         store=self.access, now=self.clock())

    def issue(self, *sources: str, out: str = "cred") -> str:
        flags = [x for s in sources for x in ("--enable-source", s)]
        assert self.provision("issue", "--credential-out", str(self.tmp / out), *flags) == 0
        return (self.tmp / out).read_text(encoding="ascii").strip()

    def client(self, *, https: bool = True) -> TestClient:
        app = FastAPI()
        install_gateway_tls_boundary(app)
        principals = StoreGatewayPrincipals(self.access)
        app.include_router(build_evidence_router(
            IngestionService(None, _NoSites()), _NoSites(),  # type: ignore[arg-type]
            batch_ingestion=ingestion(), gateway_principals=principals))
        app.include_router(build_gateway_router(
            principals, DiagnosticIngestionService(self.access, self.clock), self.access,
            lambda code: (self.tenant_uuid, self.site_uuid) if code == self.site_code else None, self.clock))
        return TestClient(app, base_url="https://testserver" if https else "http://testserver")

    def counts(self, tables) -> dict[str, int]:
        with self.engine.connect() as c:
            return {t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in tables}

    def diagnostic(self, sequence: int = 1, *, contacts=None, queue: int = 3, site=None, gateway=None):
        return seal_gateway_diagnostics_v1(
            site_id=site or str(self.site_uuid), gateway_id=gateway or str(self.kit.principal.gateway_id),
            sequence_epoch="epoch-1", diagnostic_sequence=sequence, observed_at="2026-10-09T08:59:58Z",
            last_device_contact_by_source=(
                {str(self.pv_source): "2026-10-09T08:59:00Z"} if contacts is None else contacts),
            queue_count=queue, oldest_queue_age_seconds=42, disk_pressure="OK", clock_offset_ms=None,
            mapping_error_count=0)[1]


@pytest.fixture()
def rig(store, engine, tmp_path):
    return Rig(store, engine, tmp_path)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestProvisioning:
    def test_issue_stores_only_a_verifier_and_enables_exactly_the_named_sources(self, rig) -> None:
        pv_external = rig.sources[rig.pv_source]
        token = rig.issue(pv_external)
        selector, secret = token.split(".")[1:]
        with rig.engine.connect() as c:
            row = c.execute(text("SELECT * FROM gateway_credential")).mappings().one()
            gateway = c.execute(text("SELECT credential_ref, disabled_at FROM gateway WHERE id = :g"),
                                {"g": rig.kit.principal.gateway_id}).one()
            sources = {r.id: r.disabled_at for r in c.execute(text("SELECT id, disabled_at FROM source")).all()}
            events = [r.kind for r in c.execute(text("SELECT kind FROM gateway_access_event ORDER BY kind")).all()]
            dump = " ".join(str(v) for t in ("gateway_credential", "gateway_access_event", "gateway", "source")
                            for r in c.execute(text(f"SELECT * FROM {t}")).all() for v in r)
        assert row["selector"] == selector and gateway.credential_ref == selector and gateway.disabled_at is None
        assert secret not in dump and token not in dump
        assert sources[rig.pv_source] is None
        assert all(at is not None for s, at in sources.items() if s != rig.pv_source)
        assert events == ["CREDENTIAL_ISSUED", "GATEWAY_ENABLED", "SOURCE_ENABLED"]

    def test_unknown_source_or_gateway_is_refused(self, rig, tmp_path) -> None:
        assert rig.provision("enable-source", "--source", "no-such-source") == 2
        assert provision(["issue", "--tenant", "demo", "--site", rig.site_code, "--gateway", "nope",
                          "--credential-out", str(tmp_path / "x")], store=rig.access) == 2
        assert not (tmp_path / "x").exists()


class TestBearerBoundary:
    def test_plaintext_is_refused_before_authentication(self, rig) -> None:
        token = rig.issue(rig.sources[rig.pv_source])
        body = rig.kit.seal(rig.kit.pv(1))
        answer = rig.client(https=False).post("/api/ingestion/batches", content=body, headers=bearer(token))
        assert answer.status_code == 426 and answer.json()["detail"]["code"] == "GATEWAY_TLS_REQUIRED"
        diag = rig.client(https=False).post(f"/api/gateways/{rig.kit.principal.gateway_id}/diagnostics",
                                            content=rig.diagnostic(), headers=bearer(token))
        assert diag.status_code == 426
        assert rig.counts(LEDGER_TABLES + ("gateway_diagnostic",)) == {t: 0 for t in LEDGER_TABLES + ("gateway_diagnostic",)}

    def test_a_provisioned_credential_uploads_over_tls_and_reads_its_receipt(self, rig) -> None:
        token = rig.issue(rig.sources[rig.pv_source])
        client = rig.client()
        body = rig.kit.seal(rig.kit.pv(2))
        posted = client.post("/api/ingestion/batches", content=body, headers=bearer(token))
        assert posted.status_code == 200
        receipt = parse_canonical_receipt_v2_text(posted.text)
        assert receipt.status == "COMPLETED"
        assert client.get(f"/api/ingestion/batches/{receipt.batch_id}", headers=bearer(token)).text == posted.text

    def test_wrong_malformed_and_revoked_credentials_are_401_with_no_rows(self, rig) -> None:
        token = rig.issue(rig.sources[rig.pv_source])
        client = rig.client()
        body = rig.kit.seal(rig.kit.pv(1))
        selector = token.split(".")[1]
        forged = f"aog1.{selector}.{'A' * 43}"
        for header in (bearer(forged), bearer("aog1.short"), {"Authorization": "Basic abc"}, bearer("")):
            answer = client.post("/api/ingestion/batches", content=body, headers=header)
            assert answer.status_code == 401, header
            assert token.split(".")[2] not in answer.text
        assert rig.provision("revoke", "--selector", selector) == 0
        revoked = client.post("/api/ingestion/batches", content=body, headers=bearer(token))
        assert revoked.status_code == 401 and revoked.json()["detail"]["code"] == "GATEWAY_CREDENTIAL_INVALID"
        assert rig.counts(LEDGER_TABLES) == {t: 0 for t in LEDGER_TABLES}

    def test_rotation_retires_the_old_credential_and_retries_the_same_bytes(self, rig) -> None:
        old = rig.issue(rig.sources[rig.pv_source])
        client = rig.client()
        body = rig.kit.seal(rig.kit.pv(2))
        first = client.post("/api/ingestion/batches", content=body, headers=bearer(old))
        new = rig.issue(rig.sources[rig.pv_source], out="cred2")
        assert new != old
        assert client.post("/api/ingestion/batches", content=body, headers=bearer(old)).status_code == 401
        again = client.post("/api/ingestion/batches", content=body, headers=bearer(new))
        assert again.status_code == 200 and again.text == first.text  # same sealed bytes, same receipt
        assert rig.counts(("ingestion_batch",)) == {"ingestion_batch": 1}

    def test_disabled_gateway_and_disabled_source_refuse_even_an_identical_retry(self, rig) -> None:
        token = rig.issue(rig.sources[rig.pv_source])
        client = rig.client()
        body = rig.kit.seal(rig.kit.pv(1))
        assert client.post("/api/ingestion/batches", content=body, headers=bearer(token)).status_code == 200
        assert rig.provision("disable-source", "--source", rig.sources[rig.pv_source]) == 0
        assert client.post("/api/ingestion/batches", content=body, headers=bearer(token)).status_code == 403
        assert rig.provision("enable-source", "--source", rig.sources[rig.pv_source]) == 0
        assert rig.provision("disable-gateway") == 0
        refused = client.post("/api/ingestion/batches", content=body, headers=bearer(token))
        assert refused.status_code == 403 and refused.json()["detail"]["code"] == "GATEWAY_DISABLED"
        assert rig.provision("enable-gateway") == 0
        assert client.post("/api/ingestion/batches", content=body, headers=bearer(token)).status_code == 200

    def test_a_source_not_named_at_provisioning_stays_closed(self, rig) -> None:
        token = rig.issue()  # gateway only, no source named
        body = rig.kit.seal(rig.kit.pv(1))
        answer = rig.client().post("/api/ingestion/batches", content=body, headers=bearer(token))
        assert answer.status_code == 403
        assert rig.counts(LEDGER_TABLES) == {t: 0 for t in LEDGER_TABLES}

    def test_a_cross_site_claim_is_403_with_no_rows(self, rig) -> None:
        token = rig.issue(rig.sources[rig.pv_source])
        other = "00000000-0000-4000-8000-000000000001"
        diag = rig.client().post(f"/api/gateways/{rig.kit.principal.gateway_id}/diagnostics",
                                 content=rig.diagnostic(site=other), headers=bearer(token))
        assert diag.status_code == 403
        path = rig.client().post(f"/api/gateways/{other}/diagnostics", content=rig.diagnostic(),
                                 headers=bearer(token))
        assert path.status_code == 403
        assert rig.counts(ACCESS_TABLES[2:]) == {t: 0 for t in ACCESS_TABLES[2:]}


class TestDiagnostics:
    def _post(self, rig, token, body):
        return rig.client().post(f"/api/gateways/{rig.kit.principal.gateway_id}/diagnostics",
                                 content=body, headers=bearer(token))

    def test_store_identical_retry_conflict_and_health_freshness(self, rig) -> None:
        token = rig.issue(rig.sources[rig.pv_source])
        client = rig.client()
        before = client.get(f"/api/sites/{rig.site_code}/gateway-health").json()
        assert before["gateways"][0]["status"] == "UNKNOWN" and before["gateways"][0]["last_server_contact"] is None
        body = rig.diagnostic()
        first = self._post(rig, token, body)
        assert first.status_code == 201
        rig.clock.now = REAL_NOW + timedelta(seconds=5)
        again = self._post(rig, token, body)
        assert again.status_code == 200 and again.json() == first.json()  # same row, original receive time
        changed = self._post(rig, token, rig.diagnostic(queue=9))
        assert changed.status_code == 409 and changed.json()["detail"]["refusal_id"]
        assert rig.counts(("gateway_diagnostic", "gateway_diagnostic_refusal")) == {
            "gateway_diagnostic": 1, "gateway_diagnostic_refusal": 1}
        health = client.get(f"/api/sites/{rig.site_code}/gateway-health").json()["gateways"][0]
        assert health["status"] == "CURRENT" and health["status_basis"] == "SERVER_RECEIVED_AT"
        assert health["declared_cadence_seconds"] == 60 and health["queue_count"] == 3
        assert health["disk_pressure_provenance"] == "REPORTED_SIMULATED_GATEWAY"
        pv = next(s for s in health["source_contacts"] if s["source_id"] == str(rig.pv_source))
        assert pv["last_contact"] == "2026-10-09T08:59:00Z" and pv["contact_provenance"] == "OBSERVED_SIMULATED_REPORT"
        # Silence: after two declared cadences without a receipt the gateway is STALE.
        rig.clock.now = REAL_NOW + timedelta(seconds=121)
        stale = client.get(f"/api/sites/{rig.site_code}/gateway-health").json()["gateways"][0]
        assert stale["status"] == "STALE" and stale["last_server_contact"] == health["last_server_contact"]

    def test_a_disabled_source_keeps_historical_contact_but_a_foreign_source_is_refused(self, rig) -> None:
        token = rig.issue(rig.sources[rig.pv_source])
        disabled = next(s for s in rig.sources if s != rig.pv_source)
        contacts = {str(rig.pv_source): "2026-10-09T08:59:00Z", str(disabled): "2026-10-09T07:00:00Z"}
        assert self._post(rig, token, rig.diagnostic(contacts=contacts)).status_code == 201
        health = rig.client().get(f"/api/sites/{rig.site_code}/gateway-health").json()["gateways"][0]
        row = next(s for s in health["source_contacts"] if s["source_id"] == str(disabled))
        assert row["registration"] == "DISABLED" and row["last_contact"] == "2026-10-09T07:00:00Z"
        foreign = {"00000000-0000-4000-8000-0000000000aa": None}
        answer = self._post(rig, token, rig.diagnostic(2, contacts=foreign))
        assert answer.status_code == 403 and answer.json()["detail"]["code"] == "SOURCE_NOT_AFFILIATED"

    def test_malformed_is_422_with_an_audited_refusal_and_never_evidence(self, rig) -> None:
        token = rig.issue(rig.sources[rig.pv_source])
        answer = self._post(rig, token, b'{"not": "a diagnostic"}')
        assert answer.status_code == 422 and answer.json()["detail"]["refusal_id"]
        assert self._post(rig, token, rig.diagnostic()).status_code == 201
        assert rig.counts(LEDGER_TABLES) == {t: 0 for t in LEDGER_TABLES}

    def test_diagnostic_rows_are_append_only(self, rig) -> None:
        token = rig.issue(rig.sources[rig.pv_source])
        assert self._post(rig, token, rig.diagnostic()).status_code == 201
        with pytest.raises(DBAPIError):
            with rig.engine.begin() as c:
                c.execute(text("UPDATE gateway_diagnostic SET queue_count = 0"))
        with pytest.raises(DBAPIError):
            with rig.engine.begin() as c:
                c.execute(text("UPDATE gateway_credential SET verifier_sha256 = repeat('0', 64)"))


class TestComposition:
    """`create_app` wires the store verifier, the TLS boundary and both routes."""

    def test_create_app_serves_diagnostics_and_health_behind_tls(self, rig, store, tmp_path) -> None:
        import shutil

        from test_s1_foundation_postgres import KOBO_SOURCE, app_for

        root = tmp_path / "sites"
        root.mkdir()
        shutil.copy(KOBO_SOURCE, root / "kobo-001.yaml")
        token = rig.issue(rig.sources[rig.pv_source])
        client = app_for(store, root, evidence_ledger=PostgresEvidenceLedger(URL),
                         gateway_access=rig.access, gateway_clock=rig.clock)
        path = f"/api/gateways/{rig.kit.principal.gateway_id}/diagnostics"
        plain = client.post(path, content=rig.diagnostic(), headers=bearer(token))
        assert plain.status_code == 426
        client.base_url = "https://testserver"
        assert client.post(path, content=rig.diagnostic(), headers=bearer(token)).status_code == 201
        health = client.get(f"/api/sites/{rig.site_code}/gateway-health")
        assert health.status_code == 200 and health.json()["gateways"][0]["status"] == "CURRENT"
        assert client.get("/api/sites/NOT-A-SITE/gateway-health").status_code == 404
