"""W3-02 commit 1: the estate Evidence root over the real one-transaction estate snapshot.

Real persisted chains only: the W2-02/W2-03 cold `late-reading` replay and the S4 mini-grid `CaseRunner` (F02, two
selected UTC days). Read through the local Evidence router; Lane A mounts it in `main.py`. The EV replay is in
`test_w302_evidence_ev_postgres.py` (its `chain` fixture shares this name). Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import uuid4

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    from test_w202_cold_replay_postgres import chain  # noqa: F401 - the W2-02 replay fixture
    from test_s1_bindings_postgres import engine, store  # noqa: F401 - the S4 mini-grid fixtures
    from test_s4_finding_store_postgres import SPEC, CaseRunner
    from test_w301_estate_index_postgres import (
        DAY, ESTATE_KEYS, Estate, add_empty_site, cold_estate, db_now, imported_before, iso, watermark)

    import pg_harness
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.claim_limit_read import ClaimLimitReadService, ClaimLimitRefusal, reduce_day
    from assetops_backend.estate.adapters import postgres_evidence_money_read as pemr
    from assetops_backend.estate.composition import build_estate_read
    from assetops_backend.estate.evidence_money import EstateEvidenceService
    from assetops_backend.estate.scope import decode_cursor
    from assetops_backend.estate_evidence_money_api import build_estate_evidence_money_router


def evidence_read(engine):  # noqa: F811
    """TEST-SCOPED stand-in for Lane A's composition (`.agent/W3-02-lane-a-requests.md`): the W3-01 estate read's
    exact collaborators plus the W1 claim-limit service over the same assessment store."""
    url = engine.url.render_as_string(hide_password=False)
    base = build_estate_read(url)
    keys = ("findings", "assessments", "actions", "consequences", "eligibility", "cold", "ev", "provenance_reads",
            "inconsistent", "unavailable", "cold_site", "ev_site", "ev_money")
    return pemr.PostgresEvidenceMoneyRead(
        url, claim_limits=ClaimLimitReadService(base.assessments), claim_limit_refused=(ClaimLimitRefusal,),
        engine=engine, **{k: getattr(base, k) for k in keys})


class Evidence:
    def __init__(self, engine, tenant_id, admit=lambda code: True) -> None:  # noqa: F811
        self.read = evidence_read(engine)
        self.admit = admit
        app = FastAPI()
        app.include_router(build_estate_evidence_money_router(
            EstateEvidenceService(self.read), lambda: tenant_id,
            access=lambda request, code: None if self.admit(code) else 403))
        self.client = TestClient(app)

    def get(self, **params):
        return self.client.get("/api/estate/evidence?" + urlencode(params))

    def ok(self, **params) -> dict:
        response = self.get(**params)
        assert response.status_code == 200, response.text
        return response.json()


def test_w302_evidence_cold_scope_windows_and_citations(chain) -> None:  # noqa: F811
    """Every authorized Site appears (a Site without selection has four placeholders), a foreign tenant is an
    empty scope, each cold window gives four grouped rows citing only that window's own analytic revisions and
    accepted Evidence, row links carry the row's exact window and row-local cutoff, and the 3-part cursor pages
    the full ordered set under one selection token, with a changed grant refused 409."""
    built, estate = cold_estate(chain)
    empty = add_empty_site(built.engine, built.site_id, "W302-EMPTY-001")
    evidence = Evidence(built.engine, built.tenant_id)
    day = {"from": iso(DAY), "to": iso(DAY + timedelta(days=1))}
    body = evidence.ok(**day, limit=100)
    known = db_now(built.engine)
    windows = estate.windows(built.tenant_id, built.site_id, "cold_chain", DAY, DAY + timedelta(days=1), known)
    assert windows, ("the late-reading replay selects at least one cold window on the day",
                     [(r["capability_key"], r["raw_state"]) for r in body["rows"]])
    cold_rows = [r for r in body["rows"] if r["site_id"] == str(built.site_id)]
    assert len(cold_rows) == 4 * len(windows) and body["total_count"] == len(cold_rows) + 4
    mark = watermark(built.engine, built.site_id)
    with built.engine.connect() as c:
        code = c.execute(text("SELECT site_code FROM site WHERE id = :s"), {"s": built.site_id}).scalar_one()
    for w in windows:
        suffix = f"@{w['window_start'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')}/" \
                 f"{w['window_end'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"
        mine = [r for r in cold_rows if r["capability_key"].endswith(suffix)]
        assert sorted(r["capability_key"].split("@")[0] for r in mine) == ["backup", "cooling", "exposure",
                                                                           "temperature"]
        # Each row cites exactly one of the window's selected analytic revisions; together they are the window's.
        assert all(len(r["selected_revision_ids"]) == 1 for r in mine)
        assert {x for r in mine for x in r["selected_revision_ids"]} == set(w["assessment_revision_ids"])
        cited = {e for r in mine for e in r["source_provenance"]["evidence_ids"]}
        assert cited == set(w["evidence_ids"])
        for r in mine:
            assert set(r["source_provenance"]) == ESTATE_KEYS and r["source_provenance"]["basis_sha256"]
            assert r["raw_state"] in ("FULL", "LIMITED", "NONE", "CONTRADICTORY")
            link = urlsplit(r["links"]["site_readiness"])
            q = parse_qs(link.query)
            assert link.path == f"/sites/{code}/evidence"
            assert q["from"][0].startswith(w["window_start"].strftime("%Y-%m-%dT%H:%M:%S"))
            assert datetime.fromisoformat(q["known_at"][0].replace("Z", "+00:00")) == mark
    placeholders = [r for r in body["rows"] if r["site_id"] == empty]
    assert [r["capability_key"] for r in placeholders] == ["backup", "cooling", "exposure", "temperature"]
    assert {r["raw_state"] for r in placeholders} == {"UNASSESSED"}
    assert all(r["links"]["site_readiness"] == "/sites/W302-EMPTY-001" for r in placeholders)
    assert body["coverage"]["state"] == "PARTIAL" and body["status"] == "UNKNOWN"
    assert body["summary"]["full_count"] is None and body["summary"]["capability_count"] == body["total_count"]
    assert all(g["gap_code"] == "MISSING_ROLE" and g["missing_role"] for g in body["gaps"])
    # The full ordered set pages under one token; the 3-part marker resumes exactly.
    seen, cursor, first = [], None, None
    while True:
        page = evidence.ok(**day, limit=3, **({"cursor": cursor} if cursor else {}))
        first = first or page
        # a live page one fixes its own read time; every continuation keeps that page's token
        assert page["selection_token"] == first["selection_token"] and page["total_count"] == body["total_count"]
        seen += page["rows"]
        cursor = page["next_cursor"]
        if cursor is None:
            break
        assert len(decode_cursor("evidence", cursor)["after"]) == 3
    assert [(r["site_id"], r["capability_key"]) for r in seen] == [
        (r["site_id"], r["capability_key"]) for r in body["rows"]]
    evidence.admit = lambda code: code != "W302-EMPTY-001"
    changed = evidence.get(**day, limit=3, cursor=first["next_cursor"])
    assert changed.status_code == 409 and changed.json()["detail"] == {
        "code": "ESTATE_BASIS_CHANGED", "message": changed.json()["detail"]["message"], "rows": None,
        "total_count": None, "gaps": None}
    # A foreign tenant reads a complete empty scope; no row of this tenant leaks.
    foreign = Evidence(built.engine, uuid4()).ok(**day)
    assert foreign["status"] == "EMPTY_SCOPE" and foreign["coverage"] == {"state": "EMPTY", "sites": []}
    assert foreign["rows"] == [] and str(built.site_id) not in str(foreign)


# --- mini-grid W1 days ------------------------------------------------------------------------------------------

F02 = next(c for c in SPEC["cases"] if c["case_id"] == "F02") if URL else None
F02_DAY = datetime(2026, 10, 8, tzinfo=timezone.utc)


@pytest.fixture()
def mini(store, engine, monkeypatch):  # noqa: F811
    """TEST-SCOPED: the S4 fixture clock runs ahead of the database clock; pin the snapshot read time and the
    assessment store's live-or-historical test to the fixture's present, as W3-01's `pin_read_at` does."""
    runner = CaseRunner(store, engine)
    present = lambda: runner.now + timedelta(minutes=1)  # noqa: E731
    real = pemr.EvidenceMoneySnapshot

    class Pinned(real):
        def __init__(self, owner, c, read_at) -> None:
            super().__init__(owner, c, present())

    monkeypatch.setattr(pemr, "EvidenceMoneySnapshot", Pinned)
    monkeypatch.setattr(PostgresAssessmentStore, "_transaction_time", staticmethod(lambda c: present()))
    imported_before(engine, runner.tenant, runner.site, datetime(2026, 10, 1, tzinfo=timezone.utc))
    yield runner, Evidence(engine, runner.tenant)
    pg_harness.dispose(runner.findings)


def test_w302_evidence_w1_days_reduced_and_historical(mini, monkeypatch) -> None:
    """F02: one `GENERATOR_SUPPORT@day` row per intersecting UTC day, citing exactly that day's selected interval
    revisions (the window revision stays in disclosure). An explicit earlier cutoff keeps the IDs as HISTORICAL with
    no current claim and no current gap group. Only the estate connection is used: the assessment store's own
    transaction entry points fail the test."""
    runner, evidence = mini
    for step in F02["steps"][:2]:  # deliver both sides of midnight, assess
        runner.step(step)
    cutoff = runner.now
    for name in ("_snapshot", "_run", "_connect_engine"):
        monkeypatch.setattr(PostgresAssessmentStore, name, lambda *a, **k: pytest.fail("second transaction"))
    window = {"from": iso(F02_DAY), "to": iso(F02_DAY + timedelta(days=2))}
    live = evidence.ok(**window)
    rows = [r for r in live["rows"] if r["domain"] == "mini_grid"]
    assert [r["capability_key"] for r in rows] == ["GENERATOR_SUPPORT@2026-10-08", "GENERATOR_SUPPORT@2026-10-09"]
    with runner.engine.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
        store = evidence.read.assessments
        service = ClaimLimitReadService(store)
        expected = {}
        for d in store.select_dispatch_days_on(c, runner.tenant, runner.site, F02_DAY,
                                               F02_DAY + timedelta(days=2), runner.now + timedelta(minutes=1)):
            expected[d["day"].isoformat()] = reduce_day(service.claim_limit_on(
                c, runner.tenant, runner.site, d["day"], d["window_assessment_revision_id"],
                runner.now + timedelta(minutes=1)))
    for row in rows:
        r = expected[row["capability_key"].split("@")[1]]
        assert row["selected_revision_ids"] == r["assessment_revision_ids"] and row["selected_revision_ids"]
        assert row["disclosure"]["window_assessment_revision_id"] == r["window_assessment_revision_id"]
        assert r["window_assessment_revision_id"] not in row["selected_revision_ids"]
        assert row["readiness"] == r["state"] and row["current_ceiling"] == r["ceiling_statement"]
        assert set(row["source_provenance"]["evidence_ids"]) == set(r["accepted_evidence_ids"])
        assert set(row["gap_codes"]) == {g["gap_code"] for g in r["gaps"]}
    old = evidence.ok(**window, known_at=iso(cutoff))
    assert old["status"] == "HISTORICAL" and old["summary"]["as_of"] == iso(cutoff)
    hist = [r for r in old["rows"] if r["domain"] == "mini_grid"]
    assert [r["selected_revision_ids"] for r in hist] == [r["selected_revision_ids"] for r in rows]
    for row in hist:
        assert row["raw_state"] == "HISTORICAL" and row["readiness"] in ("UNKNOWN", "CONTRADICTORY")
        assert row["current_ceiling"] is None and row["ceiling_source"] == "NONE" and row["gap_codes"] == []
        assert row["disclosure"]["historical"]["label"] == f"Historical as of {old['window']['known_at']}"
    assert all(g["domain"] != "mini_grid" for g in old["gaps"])
    assert old["summary"]["full_count"] is None and old["summary"]["limited_site_count"] is None
