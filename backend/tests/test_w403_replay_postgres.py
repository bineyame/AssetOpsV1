"""W4-03 unit 9a: the private two-Site replay of `backend/tests/fixtures/w4/w403-mini-decisions.json`.

`.agent/W4-03-build-spec.md` "Fixture and one-run commit proof", closure 2 Q1, closure 4 B1/B2/S6/S16 and u5 9a. The
replay is `tools/w403_mini_decisions_walkthrough.py:run_replay` itself; here its HTTP side is a TestClient over
`main.create_app` with the walkthrough's two injected callbacks, so the same bearer/scope/grant rules apply. W4-01
cases are seeded in process through `WorkService` (B2); nothing inserts accepted evidence directly.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "tools") not in sys.path:
    sys.path.insert(0, str(REPO / "tools"))

import w403_mini_decisions_walkthrough as walk  # noqa: E402

if URL:
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness

SECRET = "w403-test-bearer"


def http_for(client: TestClient, secret: str | None = SECRET):
    headers = {} if secret is None else {"Authorization": f"Bearer {secret}"}

    def call(method: str, path: str, body=None):
        r = client.request(method, path, json=body, headers=headers)
        return r.status_code, r.json()
    return call


def kobo_documents():
    """u9b PR-12.4: the imported KOBO fixture's own legacy document (path as recorded, digest of its bytes)."""
    import hashlib

    from assetops_backend.sites.foundation_service import LegacyDocument

    digest = hashlib.sha256(walk.KOBO_SOURCE.read_bytes()).hexdigest()
    return lambda: (LegacyDocument(site_code=walk.KOBO_CODE, path=walk.KOBO_RECORDED_PATH, sha256=digest),)


def app_client(monkeypatch, scopes, **kw) -> TestClient:
    from assetops_backend import main

    monkeypatch.setenv("DATABASE_URL", URL)
    access, principal = walk.fixture_callbacks(SECRET, scopes, **kw)
    return TestClient(main.create_app(mini_decision_command_access=access, mini_decision_principal=principal,
                                      legacy_documents=kobo_documents()))


def table_counts(engine) -> tuple:
    with engine.connect() as c:
        return tuple(c.execute(text(f"SELECT count(*) FROM {t}")).scalar_one()
                     for t in ("mini_scenario", "mini_alternative_revision", "mini_opportunity_scenario_link",
                               "mini_decision_work_link"))


@pytest.fixture
def sites(store, engine, monkeypatch, tmp_path):  # noqa: F811
    from assetops_backend.evidence.adapters import json_evidence_store

    monkeypatch.setenv("DATABASE_URL", URL)  # the worker CLI and the performance comparison read it
    # The comparison report lands in this test's own folder, never the repository's var/evidence.
    monkeypatch.setattr(json_evidence_store, "EVIDENCE_STORE_ROOT", tmp_path / "evidence")
    imported = walk.import_sites(store, engine)
    yield imported
    pg_harness.dispose(imported["runner"].findings)


def test_positive_missing_late_replay_and_fresh_reload(sites, engine, monkeypatch) -> None:  # noqa: F811
    fixture = walk.load_fixture()
    assert fixture["schema_version"] == "w403-mini-decisions/1"
    assert (fixture["opportunity_site_code"], fixture["alternative_site_code"], fixture["work_link_site_code"]) == (
        "MG-W402-001", "KOBO-001", "MG-W402-001")
    raw = walk.FIXTURE.read_bytes()
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert raw.decode("utf-8") == json.dumps(fixture, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    scopes = sites["scopes"]
    client = app_client(monkeypatch, scopes)
    mg = fixture["opportunity_site_code"]
    route = f"/api/sites/{mg}/financials/scenarios"
    body = walk.fill(fixture["commands"]["scenario_missing_tariff"], pinned_selection=[])

    # No credential, a wrong Site and a missing grant never reach a W4-03 write.
    before = table_counts(engine)
    refusals = [http_for(client, None)("POST", route, body),
                http_for(client, "not-the-secret")("POST", route, body),
                http_for(app_client(monkeypatch, {"KOBO-001": scopes["KOBO-001"]}))("POST", route, body),
                http_for(app_client(monkeypatch, scopes, grants=set()))("POST", route, body)]
    assert [(s, b["detail"]["code"]) for s, b in refusals] == [(403, "DECISION_WRITE_FORBIDDEN")] * 4
    assert table_counts(engine) == before

    # u9b PR-12.5: phase 1 (positive) only; no late or missing evidence exists yet.
    record = walk.run_replay_positive(engine, sites["installed"], fixture, scopes, http_for(client))
    assert record["performance_exit"] == 0
    assert record["performance_exits"] == {"MG-W402-001": 0, "KOBO-001": 0}
    # PR-12.4: the KOBO Site and its exact F02 Finding read are open before any capture.
    assert record["kobo_reads"]["site_status"] == 200
    assert record["kobo_reads"]["finding_code"] != "PERFORMANCE_CUTOVER_CLOSED"
    assert not {"k_before_late", "late_pending", "late_settled", "missing"} & set(record)
    assert set(record["accepted"]) == {"positive"}
    selection = record["positive_selection"]
    assert (selection["status"], selection["currentness"]["state"]) == ("SUPPORTED", "CURRENT")
    assert selection["pins"] == record["pins"]
    # A fresh app reloads the same positive/current selection before phase 2.
    status, reloaded = http_for(app_client(monkeypatch, scopes))(
        "GET", f"/api/sites/{mg}/opportunities/{selection['opportunity_id']}")
    assert status == 200
    assert (reloaded["status"], reloaded["currentness"]["state"]) == ("SUPPORTED", "CURRENT")
    assert reloaded["opportunity"]["revision_id"] == selection["revision_id"]
    assert reloaded["selected_source_provenance"] == selection["selected_source_provenance"]
    # Phase 2 runs on the phase-1 record as `positive.json` stores it (a JSON round trip), without new keys.
    stored = json.loads(json.dumps(record, sort_keys=True))
    before_late = table_counts(engine)
    record = walk.run_replay_late(engine, sites["installed"], fixture, http_for(client), stored)
    assert table_counts(engine) == before_late  # the five W4-03 commands are not repeated
    assert record["accepted"]["positive"] and record["accepted"]["late"] and record["accepted"]["missing"]

    # S16: all five 6-10 Oct selected noon tuples are pinned, the EXCLUDED 6 Oct day included.
    pins = record["pins"]
    assert [p["local_day"] for p in pins] == fixture["study_days"]
    assert all(p["selection_seq"] and p["mini_revision_id"] for p in pins)

    pos = record["positive"]
    opp = pos["opportunity"]
    o = opp["opportunity"]
    rows = o["day_rows"]
    eligible = [r for r in rows if r["decision"] == "ELIGIBLE"]
    assert (opp["status"], o["assessed_days"], o["eligible_days"], o["study_days"]) == ("SUPPORTED", 5, len(eligible), 5)
    assert rows[0]["local_day"] == "2026-10-06" and rows[0]["decision"] == "EXCLUDED"
    assert opp["currentness"]["state"] == "CURRENT"
    assert [(r["selection_seq"], r["mini_revision_id"]) for r in rows] == [
        (p["selection_seq"], p["mini_revision_id"]) for p in pins]
    assert o["scenario_id"] == record["writes"]["scenario"]["id"]
    assert opp["links"]["site_work"] == f"/sites/{scopes[mg][1]}/work/incidents"
    assert [link["scenario_id"] for link in opp["scenario_links"]] == [record["writes"]["scenario"]["id"]]

    # Money per eligible window, from the actual selected lower bounds; otherwise the ruled WITHHELD state.
    scenarios = {r["id"]: r for r in pos["scenarios"]["rows"]}
    positive = scenarios[record["writes"]["scenario"]["id"]]
    assert positive["revision_id"] == record["writes"]["corrected"]["revision_id"]
    if all(Decimal(r["opportunity_kwh"]["low"]) >= Decimal("10") for r in eligible):
        assert Decimal(positive["energy_kwh"]) == Decimal("10")
        assert Decimal(positive["gross_sales"]["amount"]) == Decimal("2.50")
        assert positive["gross_sales"]["currency"] == "USD"
    else:
        assert positive["calculation_state"] == "WITHHELD" and positive["gross_sales"] is None
    no_tariff = scenarios[record["writes"]["no_tariff"]["id"]]
    assert no_tariff["gross_sales"] is None and no_tariff["energy_kwh"] == positive["energy_kwh"]

    # The explicit association reaches the MG Incident only; the unlinked request keeps an empty context.
    contexts = pos["contexts"]["contexts"]
    incident, request = record["cases"]["w403-walk-case-incident"], record["cases"]["w403-walk-case-request"]
    # uF M5: the replay also links the scenario to the Incident, so the exact-cutoff order is OPPORTUNITY then SCENARIO.
    assert [c["kind"] for c in contexts[incident]] == ["OPPORTUNITY", "SCENARIO"] and contexts[request] == []
    assert contexts[incident][0]["label"] == o["code"]
    # The KOBO Alternative on the selected W1 Finding revision (its own Site, never the MG opportunity).
    # Reading 9a-4 (PR-11): the S4 F02 revision carries fixture time SETUP_AT; before it, the write is refused.
    alt = record["writes"]["alternative"]
    with engine.connect() as c:
        future = c.execute(text("SELECT min(created_at) > clock_timestamp() FROM finding_revision WHERE id = :r"),
                           {"r": record["finding"][1]}).scalar_one()
    # u9 PR-11.1: the replay decided the branch at POST time. The F02 revision carries the fixed fixture time
    # SETUP_AT (2026-10-29), which is in the past on every run date, so the revision is visible and the write is a 201.
    # The not-yet-visible exit (409 DECISION_BASIS_CHANGED) needs a future fixture time and is no longer exercised
    # here (a stale-basis 409 is covered by test_w403_alternative_postgres.py); no branch on the wall clock remains.
    assert record["alternative_basis_visible"] and not future
    assert alt["status"] == 201 and [r["revision_id"] for r in pos["alternatives"]["body"]["rows"]] == [
        alt["body"]["id"]]

    # Late contradictory evidence: pending before the rerun, a new head after it, the old cutoff keeps history.
    pending = record["late_pending"]["opportunity"]
    # Observed: accepting the late rows enqueues no mini job here, so the changed digest reads STALE_SOURCE
    # (u5 ruling 2 precedence) with the SOURCE_STALE read limitation; the frozen selection is unchanged.
    assert pending["currentness"]["state"] == fixture["expect"]["late"]["before_rerun"], pending["currentness"]
    assert "SOURCE_STALE" in [x["code"] for x in pending["limitations"]]
    assert pending["opportunity"]["revision_id"] == o["revision_id"]
    if pending["pending_source_provenance"] is not None:
        assert set(record["accepted"]["late"]) <= set(pending["pending_source_provenance"]["evidence_ids"])
    assert not set(record["accepted"]["late"]) & set(pending["selected_source_provenance"]["evidence_ids"])
    settled = record["late_settled"]["opportunity"]
    assert settled["opportunity"]["revision_id"] != o["revision_id"] and len(settled["history"]) == 2
    assert settled["history"][0]["current"] and settled["history"][1]["revision_id"] == o["revision_id"]
    old = record["late_old_cutoff"]["opportunity"]
    # Reading 9a-5: the harness ingestion stamps receipt at the fixed W4-02 RECEIVED time (13 Oct), before the old
    # cutoff, so the late rows are inside it and the old head reads STALE_SOURCE (which precedes HISTORICAL).
    assert old["opportunity"]["revision_id"] == o["revision_id"]
    assert old["currentness"]["state"] == fixture["expect"]["late"]["old_cutoff_currentness"] == "STALE_SOURCE"
    assert "SOURCE_STALE" in [x["code"] for x in old["limitations"]]
    # u9 PR-11.2: this vector never claims PENDING_RECOMPUTE.
    assert "PENDING_RECOMPUTE" not in (pending["currentness"]["state"], old["currentness"]["state"])
    assert [h["revision_id"] for h in old["history"]] == [o["revision_id"]]

    # Missing branch: the 8-12 Oct study holding the missing/conflicting day is never a positive display.
    # u9 PR-11.3: the second explicit window; the positive 6-10 Oct reconcile is unchanged.
    assert (fixture["missing_reconcile"]["from"], fixture["missing_reconcile"]["to"]) == (
        "2026-10-07T21:00:00.000000Z", "2026-10-12T21:00:00.000000Z")
    assert (fixture["reconcile"]["from"], fixture["reconcile"]["to"]) == (
        "2026-10-05T21:00:00.000000Z", "2026-10-10T21:00:00.000000Z")
    [missing] = [r for r in record["missing"]["rows"] if r["opportunity"]["first_day"] == "2026-10-08"]
    assert missing["status"] != "SUPPORTED"

    # A fresh app and service read the same persisted decisions.
    fresh = http_for(app_client(monkeypatch, scopes))
    again = walk.reads(fresh, fixture, record["writes"]["opportunity_id"], list(record["cases"].values()),
                       tuple(record["finding"]))
    authored = ("id", "code", "revision_id", "name", "kind", "narrative", "authored_at", "actor_id", "assumptions",
                "pinned_mini_revision_ids")
    assert [{k: r[k] for k in authored} for r in again["scenarios"]["rows"]] == [
        {k: r[k] for k in authored} for r in pos["scenarios"]["rows"]]
    # A default read stamps its own live `known_at` (database clock) and the selection token that digests it,
    # so only those two fields may differ.
    def without_read_time(read):
        body = {**read["body"], "window": {**read["body"]["window"], "known_at": None}, "selection_token": None}
        return {**read, "body": body}

    assert without_read_time(again["alternatives"]) == without_read_time(pos["alternatives"])
    assert again["opportunity"]["history"] == settled["history"]
    assert again["contexts"]["contexts"] == contexts


def test_authored_work_link_preserves_unlinked_case_count(sites, engine, monkeypatch) -> None:  # noqa: F811
    fixture = walk.load_fixture()
    scopes = sites["scopes"]
    mg, kobo = scopes["MG-W402-001"], scopes["KOBO-001"]
    walk.publish_and_ingest(engine, sites["installed"], fixture, "positive")
    walk.mini_days(engine, fixture["study_days"])
    walk.opportunity_cli(fixture["reconcile"])
    cases = {c["body"]["idempotency_key"]: walk.seed_case(scopes[c["site_code"]], c["body"])
             for c in fixture["commands"]["cases"]}
    foreign = walk.seed_case(kobo, {**fixture["commands"]["cases"][0]["body"], "idempotency_key": "w403-walk-kobo"})
    client = app_client(monkeypatch, scopes)
    call = http_for(client)
    from test_w403_opportunity_read_postgres import page, service

    oid = page(service(engine), mg[0], mg[1])["rows"][0]["opportunity"]["id"]
    now = datetime.now(timezone.utc)
    window = f"from={walk.iso(now - timedelta(days=20))}&to={walk.iso(now + timedelta(days=1))}"

    def lists():
        out = {}
        for k in ("incidents", "maintenance"):
            r = client.get(f"/api/sites/MG-W402-001/work/{k}?{window}")
            assert r.status_code == 200, r.text
            out[k] = r.json()
        return out

    before = lists()
    assert [before[k]["total_count"] for k in ("incidents", "maintenance")] == [1, 1]
    link = fixture["commands"]["work_link"]
    # A KOBO case cannot carry the MG opportunity (404 at the MG path); the MG Incident can.
    status, out = call("POST", "/api/sites/MG-W402-001/work/decision-links",
                       walk.fill(link, case_id=foreign, opportunity_id=oid))
    assert status == 404 and out["detail"]["code"] == "WORK_CASE_NOT_FOUND"
    status, out = call("POST", "/api/sites/MG-W402-001/work/decision-links",
                       walk.fill(link, case_id=cases["w403-walk-case-incident"], opportunity_id=oid))
    assert status == 201 and out["kind"] == "OPPORTUNITY"
    after = lists()
    for k in ("incidents", "maintenance"):
        assert after[k]["total_count"] == before[k]["total_count"]
        assert [r["case_id"] for r in after[k]["rows"]] == [r["case_id"] for r in before[k]["rows"]]
    status, ctx = call("GET", "/api/sites/MG-W402-001/work/decision-contexts?case_ids="
                              + ",".join(cases.values()))
    assert status == 200 and ctx["contexts"][cases["w403-walk-case-request"]] == []
    assert [c["id"] for c in ctx["contexts"][cases["w403-walk-case-incident"]]] == [oid]

    # u8 unit-9 dependency: same pair under a new key is 409 (u8 1); exact-cutoff order OPPORTUNITY then SCENARIO
    # (u8 6-7); a case created after the cutoff refuses the whole read (u8 6).
    incident = cases["w403-walk-case-incident"]
    status, out = call("POST", "/api/sites/MG-W402-001/work/decision-links",
                       {**walk.fill(link, case_id=incident, opportunity_id=oid), "idempotency_key": "w403-walk-relink"})
    assert (status, out) == (409, {"detail": {"code": "DECISION_DUPLICATE_KEY",
                                              "message": "This key was used for different decision content."}})
    with engine.connect() as c:
        k0 = walk.iso(c.execute(text("SELECT clock_timestamp()")).scalar_one())
    pins = walk.selected_pins(engine, mg, fixture["study_days"])
    status, scenario = call("POST", "/api/sites/MG-W402-001/financials/scenarios",
                            walk.fill(fixture["commands"]["scenario_missing_tariff"], pinned_selection=pins))
    assert status == 201
    status, out = call("POST", "/api/sites/MG-W402-001/work/decision-links", {
        **walk.fill(link, case_id=incident, opportunity_id=None), "scenario_id": scenario["id"],
        "idempotency_key": "w403-walk-scn-link"})
    assert status == 201 and out["kind"] == "SCENARIO"
    status, now_ctx = call("GET", f"/api/sites/MG-W402-001/work/decision-contexts?case_ids={incident}")
    assert status == 200 and [(c["kind"], c["id"]) for c in now_ctx["contexts"][incident]] == [
        ("OPPORTUNITY", oid), ("SCENARIO", scenario["id"])]
    assert now_ctx["contexts"][incident][1]["url"] is None
    status, old_ctx = call("GET", f"/api/sites/MG-W402-001/work/decision-contexts?case_ids={incident}&known_at={k0}")
    assert status == 200 and [c["kind"] for c in old_ctx["contexts"][incident]] == ["OPPORTUNITY"]
    later = walk.seed_case(mg, {**fixture["commands"]["cases"][1]["body"], "idempotency_key": "w403-walk-later"})
    status, out = call("GET", f"/api/sites/MG-W402-001/work/decision-contexts?case_ids={incident},{later}"
                              f"&known_at={k0}")
    assert status == 404 and out["detail"]["code"] == "WORK_CASE_NOT_FOUND"
