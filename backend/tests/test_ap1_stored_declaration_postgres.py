"""AP-1 (D-SR.75): the stored `/analytics` readiness read over `s3-claim-limit-records-v1` (PostgreSQL).

An imported mini Site (converted KOBO-001) with accepted readings through the S2 ingestion service and selected
dispatch-3.2 runs from the real recompute worker: role presence from the ledger, the range filter on the selected
intervals, the readiness scored from those revisions, and the panel's gaps against the claim-limit section on the
same day. Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from uuid import UUID

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_s1_bindings_postgres import Clock, engine  # noqa: F401
    from test_s4_finding_store_postgres import CaseRunner

    from assetops_backend.analytics import dispatch_v3
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.claim_limit_read import ClaimLimitReadService, GAP_CODES
    from assetops_backend.analytics.stored_declaration import stored_site_declaration
    from assetops_backend.analytics_api import build_analytics_router
    from assetops_backend.claim_limit_api import build_claim_limit_router
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

import s3_claim_limit_records as records


@pytest.fixture(scope="module")
def built(engine):
    pg_harness.empty_tables(engine, ("foundation_revision", "source", "gateway", "asset", "site_import", "site",
                                     "tenant"))
    store = PostgresFoundationStore(URL)
    runner = CaseRunner(store, engine)
    manifest = records.build(runner, URL)
    assessments = PostgresAssessmentStore(URL)
    yield runner, manifest, assessments
    pg_harness.dispose(store, assessments, runner.findings)


def _day(name: str) -> tuple[datetime, datetime]:
    lo = datetime.fromisoformat(f"{records.DAYS[name]}T00:00:00+00:00")
    return lo, lo + timedelta(days=1)


def declare(built, window=None) -> dict:
    runner, _, store = built
    return stored_site_declaration(store, runner.tenant, runner.site, "KOBO-001", window)


def test_role_presence_reads_the_bound_inputs_from_the_ledger(built):
    (row,) = declare(built)["analytics"]
    required = {(r["role"], r["device_id"], r["signal_id"]): r for r in row["required_evidence"]}
    for role, sig in (("Generator state", records.SIG["state"]), ("PV capability", records.SIG["pv"]),
                      ("Battery capability", records.SIG["dis"]), ("Battery state", records.SIG["soc"])):
        assert required[(role, *sig)]["available"] is True, required
        assert required[(role, *sig)]["last_source_time"] is not None
    loads = [r for r in row["required_evidence"] if r["role"] == "Load"]
    assert sorted(r["device_id"] for r in loads) == sorted(records.FEEDERS) and all(r["available"] for r in loads)
    assert {r["role"]: r["available"] for r in row["required_evidence"]}["Reserve policy"] is True


def test_site_wide_readiness_names_the_missing_pv_day(built):
    r = declare(built)["analytics"][0]["readiness"]
    assert r["level"] == "LIMITED" and r["assessed_intervals"] >= 4
    gaps = {g["role"] for g in r["missing_evidence"] if g["kind"] == "COVERAGE_GAP"}
    assert dispatch_v3.LABELS[dispatch_v3.PV_AVAILABLE] in gaps


def test_the_range_keeps_only_that_days_selected_intervals(built):
    full = declare(built, _day("full-candidate"))
    r = full["analytics"][0]["readiness"]
    assert r["assessed_intervals"] == len(built[1]["cases"]["full-candidate"]["interval_revision_ids"]) == 1
    # The fixture delivers no generator output reading, so that row alone is not accepted; the day has no coverage gap.
    assert [(g["kind"], g["role"]) for g in r["missing_evidence"]] == [("NOT_ACCEPTED", "Generator state and output")]
    missing = declare(built, _day("missing-pv"))["analytics"][0]["readiness"]
    assert missing["level"] == "LIMITED"
    lo = datetime.fromisoformat("2026-09-01T00:00:00+00:00")
    assert declare(built, (lo, lo + timedelta(days=1)))["analytics"][0]["readiness"]["assessed_intervals"] == 0


@pytest.mark.parametrize("name", ["full-candidate", "missing-pv", "poor-quality-conflict"])
def test_panel_gaps_equal_the_claim_limit_gaps_on_the_same_day(built, name):
    runner, manifest, store = built
    case = manifest["cases"][name]
    scope = {"KOBO-001": ("KOBO-001", runner.tenant, runner.site)}
    app = FastAPI()
    app.include_router(build_claim_limit_router(ClaimLimitReadService(store), scope.get,
                                                gate=lambda c, t, s: (True, "test: gate open")))
    app.include_router(build_analytics_router(
        None, None, None, scope=scope.get, gate=lambda c, t, s: (True, "test: gate open"),
        stored=lambda t, s, code, window, *, gate: stored_site_declaration(store, t, s, code, window, gate=gate)))
    client = TestClient(app)
    claim_roles: set[str] = set()
    for rid in case["interval_revision_ids"]:
        body = client.get(f"/api/sites/KOBO-001/performance/dispatch/windows/{case['day']}/claim-limit",
                          params={"revision": rid})
        assert body.status_code == 200, body.text
        claim_roles |= {x["role"] for x in body.json()["claim_limit"]["reasons"]
                        if x["code"] in GAP_CODES and x["code"] != "GENERATOR_UNOBSERVED" and x.get("role")}
    lo, hi = _day(name)
    panel = client.get("/api/sites/KOBO-001/analytics",
                       params={"from": lo.strftime("%Y-%m-%dT%H:%M:%SZ"), "to": hi.strftime("%Y-%m-%dT%H:%M:%SZ")})
    assert panel.status_code == 200, panel.text
    label_role = {v: k for k, v in dispatch_v3.LABELS.items()}
    gaps = panel.json()["analytics"][0]["readiness"]["missing_evidence"]
    panel_roles = {label_role[g["role"]] for g in gaps if g["kind"] == "COVERAGE_GAP" and g["role"] != "Generator state"}
    assert panel_roles == claim_roles, (name, panel_roles, claim_roles)
    assert isinstance(UUID(case["interval_revision_ids"][0]), UUID)
