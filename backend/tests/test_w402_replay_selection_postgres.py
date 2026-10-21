"""W4-02 unit 4 step 5: the authored replay over `POST /api/ingestion/batches`, the mini worker and the recorded
selection seqs (`D-2026-10-20-w4-02-buildspec` Run 3 rulings q3 11-12, Run 6 rulings q6).

Both authored variants are posted as public Batch V2 content with an MG-W402-001 gateway credential issued by the
provisioning CLI (the HTTP path, not `BatchIngestionService.submit`); the worker then settles every mini job, and the
replay record's `selections` are joined back to their exact Site/domain/hour revision and full accepted-ID set.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_w402_authored_v4_postgres import RECEIVED, cases, ingestion, install, snapshot

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess
    from assetops_backend.evidence.gateway_access import StoreGatewayPrincipals
    from assetops_backend.evidence.provision_gateway import main as provision
    from assetops_backend.evidence.service import IngestionService
    from assetops_backend.evidence_api import build_evidence_router
    from assetops_backend.gateway_api import install_gateway_tls_boundary
    from assetops_backend.mini_depth.inputs import local_noon
    from assetops_backend.mini_depth.store import PostgresMiniDepthStore
    from assetops_backend.mini_depth.worker import MiniDepthWorker

ZONE = "Africa/Nairobi"
POSITIVE_DAYS = [date(2026, 10, d) for d in range(6, 11)]
MISSING_DAY = date(2026, 10, 12)


class _NoSites:
    def get_site(self, site_id):  # pragma: no cover - never reached by the batch route
        raise AssertionError


def _issue(engine, access, tmp_path, site_id) -> str:
    """Issue the MG-W402-001 gateway credential with every registered source enabled (provisioning CLI)."""
    with engine.connect() as c:
        gateway = c.execute(text("SELECT id, gateway_external_id FROM gateway WHERE site_id = :s"),
                            {"s": site_id}).one()
        sources = c.execute(text("SELECT source_external_id FROM source WHERE gateway_id = :g ORDER BY 1"),
                            {"g": gateway.id}).scalars().all()
    flags = [x for s in sources for x in ("--enable-source", s)]
    assert provision(["--tenant", "demo", "--site", cases.SITE_CODE, "--gateway", gateway.gateway_external_id,
                      "issue", "--credential-out", str(tmp_path / "cred"), *flags],
                     store=access, now=Clock(RECEIVED - timedelta(hours=1))()) == 0
    [issued] = list(tmp_path.glob("cred.*"))
    return issued.read_text(encoding="ascii").strip()


def _client(access) -> TestClient:
    app = FastAPI()
    install_gateway_tls_boundary(app)
    app.include_router(build_evidence_router(
        IngestionService(None, _NoSites()), _NoSites(),  # type: ignore[arg-type]
        batch_ingestion=ingestion(), gateway_principals=StoreGatewayPrincipals(access)))
    return TestClient(app, base_url="https://testserver")


def test_w402_http_replay_records_selection_seqs_joined_to_revisions(store, engine, tmp_path) -> None:
    installed = install(store)
    tenant_id, site_id = installed.result.site.tenant_id, installed.result.site.id
    access = PostgresGatewayAccess(URL)
    jobs = PostgresAssessmentStore(URL)
    mini = PostgresMiniDepthStore(engine)
    try:
        token = _issue(engine, access, tmp_path, site_id)
        doc, sha = snapshot(engine, installed.binding_set.id)
        spec = cases.load_spec()
        client = _client(access)
        accepted: dict[str, list[str]] = {}
        for variant in spec["variants"]:
            batches = cases.build_batches(spec, doc, sha, variant["variant"])
            for b in batches:
                response = client.post("/api/ingestion/batches", content=b.body,
                                       headers={"Authorization": f"Bearer {token}",
                                                "Content-Type": "application/json"})
                assert response.status_code == 200, response.text
            with engine.connect() as c:
                accepted[variant["variant"]] = cases.accepted_ids(c, str(site_id), cases.message_ids(batches))
            assert accepted[variant["variant"]], variant["variant"]
        all_accepted = {i for ids in accepted.values() for i in ids}

        outcomes = MiniDepthWorker(jobs, mini).run_pending(500, tenant_id, site_id)
        assert outcomes and all(o.status == "DONE" for o in outcomes), [(o.domain, o.status, o.error)
                                                                        for o in outcomes if o.status != "DONE"]
        identity = {"binding_set_revision_id": str(installed.binding_set.id), "role_set": "minigrid-roles-4",
                    "snapshot_sha256": sha}
        record = cases.replay_record(spec, identity, doc, accepted)
        record["selections"] = cases.selection_record(mini.site_selections(tenant_id, site_id), ZONE)
        assert token not in json.dumps(record)  # no credential material in the replay artifact

        selections = record["selections"]
        assert [s["seq"] for s in selections] == sorted(s["seq"] for s in selections)
        assert {s["seq"] for s in selections} == {o.selection.seq for o in outcomes}
        # Join each recorded seq to its exact Site/domain/hour revision and full accepted-ID set.
        with engine.connect() as c:
            for s in selections:
                row = c.execute(text(
                    "SELECT r.tenant_id, r.site_id, r.domain, r.window_start, r.window_end, r.input_sha256, "
                    "r.result FROM mini_depth_selection x JOIN mini_depth_revision r ON r.id = x.revision_id "
                    "AND r.tenant_id = x.tenant_id AND r.site_id = x.site_id WHERE x.seq = :q AND r.id = :r"),
                    {"q": s["seq"], "r": UUID(s["revision_id"])}).one()
                ids = sorted(str(i) for i in c.execute(text(
                    "SELECT evidence_id FROM mini_depth_revision_evidence WHERE revision_id = :r"),
                    {"r": UUID(s["revision_id"])}).scalars())
                assert (row.tenant_id, row.site_id, row.domain) == (tenant_id, site_id, s["domain"])
                assert (cases._z(row.window_start), cases._z(row.window_end)) == (s["window_start"], s["window_end"])
                assert row.window_end - row.window_start == timedelta(hours=1)
                assert row.input_sha256 == s["input_sha256"] and ids == s["accepted_evidence_ids"]
                assert row.result["basis"]["accepted_evidence_ids"] == ids
                assert set(ids) <= all_accepted
                assert s["binding_set_revision_ids"] == [str(installed.binding_set.id)]

        # q3 11: one selected noon revision per local day for each page domain (five positive days + 12 October).
        def by(domain: str) -> dict[str, dict]:
            """The one selection of each authored local day's noon hour (other hours are selected too: the install's
            publication enqueues mini work for every hour since its effective time, q1 ruling 2)."""
            out: dict[str, dict] = {}
            for day in [*POSITIVE_DAYS, MISSING_DAY]:
                noon = local_noon(day, ZONE)
                hits = [s for s in selections if s["domain"] == domain and s["local_day"] == day.isoformat()
                        and (s["window_start"], s["window_end"]) == (cases._z(noon.start), cases._z(noon.end))]
                assert len(hits) == 1, (domain, day, hits)
                out[day.isoformat()] = hits[0]
            return out

        for domain in ("renewable", "service", "fuel", "backup"):
            for day, s in by(domain).items():
                assert set(s["accepted_evidence_ids"]) & all_accepted, (domain, day)

        def result(domain: str, day: date) -> dict:
            rid = by(domain)[day.isoformat()]["revision_id"]
            with engine.connect() as c:
                return c.execute(text("SELECT result FROM mini_depth_revision WHERE id = :r"),
                                 {"r": UUID(rid)}).scalar_one()

        # Positive variant: the 6 October chain is an observed outage; its renewable day is EXCLUDED.
        backup = result("backup", POSITIVE_DAYS[0])
        assert len(backup["rows"]) == 1 and backup["rows"][0]["steps"][0]["state"] == "OBSERVED"
        assert backup["cards"]["outage_count"] is None
        assert result("renewable", POSITIVE_DAYS[0])["hour"]["decision"] == "EXCLUDED"
        # Missing/conflicting variant: null/limited outcomes only.
        missing = {d: result(d, MISSING_DAY) for d in ("renewable", "service", "fuel", "backup")}
        assert missing["renewable"]["hour"]["decision"] not in ("ELIGIBLE", "EXCLUDED")
        assert missing["backup"]["status"] == "LIMITED" and missing["backup"]["cards"]["critical_recovery"] is None
        assert missing["fuel"]["cards"]["residual_l"] is None and missing["fuel"]["status"] != "SUPPORTED"
        for d, r in missing.items():
            assert r["basis"]["source_freshness"] == "UNKNOWN", d
        record_path = tmp_path / "replay.json"
        record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    finally:
        pg_harness.dispose(access, jobs)
