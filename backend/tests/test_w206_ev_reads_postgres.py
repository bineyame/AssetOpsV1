"""W2-06 commit 4: the selected EV session and Finding reads over the six registered W2-05b replays.

`.agent/W2-06-build-spec.md` "Commit 4: selected reads and refusal dry-read" and "Run 5 rulings (r5)". Each chain
runs through the registered Commit/gateway/S2 path (`test_w205b_ev_replay_postgres.chain`), the EV worker writes
the assessment, and the reads go through `build_ev_assessment_router` with the real `EvReadService`. Nothing here
seeds analytic results or accepted evidence. Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from test_w205b_ev_replay_postgres import CASES, SELECTED, URL, VECTORS, _connector_asset, chain  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_w206_ev_store_postgres import _withdrawal, run_worker
    from test_w206_ev_store_postgres import findings as stored_findings

    from assetops_backend.analytics.adapters.postgres_assessment_store import EvReadService
    from assetops_backend.analytics.ev_reads import encode_cursor
    from assetops_backend.ev_assessment_api import build_ev_assessment_router

CODE = "EV-LAB-001"
ENVELOPE = {"site_id", "window", "currentness", "source_provenance", "limitations"}
ITEM = {"session_id", "external_session_id", "charger_asset_id", "connector_asset_id", "connector_display_name",
        "revision_id", "revision_no", "basis_sha256", "state", "start_at", "end_at", "start_bounds", "end_bounds",
        "supported_kwh", "energy_complete", "unknown_meter_seconds", "reason_codes", "fault_evidence_id",
        "finding_id", "completeness", "as_of", "source_provenance", "links"}
COUNTS = {"started", "completed", "observed_abort", "incomplete", "contradictory", "orphan", "confirmed_delivery",
          "fault_aborted", "as_of", "limitation"}
LINKS = {"self", "evidence", "analysis", "finding", "financials"}


def _vectors() -> dict:
    return json.loads(VECTORS.read_text(encoding="utf-8"))["cases"]


def _at(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value.replace("Z", "+00:00"))


def client(built, *, site_type="EV_CHARGING", tenant=None, access=None, disclosure=None, reads="real") -> TestClient:
    site = SimpleNamespace(id=built.site_id, site_type=site_type)
    registry = SimpleNamespace(imported=lambda code: site if code == CODE else None,
                               tenant=lambda: SimpleNamespace(id=tenant or built.tenant_id))
    kw = {k: v for k, v in (("access", access), ("disclosure", disclosure)) if v is not None}
    app = FastAPI()
    app.include_router(build_ev_assessment_router(registry, EvReadService(URL) if reads == "real" else reads, **kw))
    return TestClient(app)


def get(c: TestClient, path: str, status: int = 200) -> dict:
    response = c.get(path if path.startswith("/") else f"/api/sites/{CODE}/ev/{path}")
    assert response.status_code == status, response.text
    return response.json()


def error(c: TestClient, path: str, status: int) -> str:
    body = get(c, path, status)
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}, body
    return body["error"]["code"]


def _q(body: dict) -> str:
    w = body["window"]
    return f"from={w['from']}&to={w['to']}&known_at={w['known_at']}"


def _session_matches(item: dict, expected: dict) -> None:
    assert item["state"] == expected["state"]
    assert _at(item["start_at"]) == _at(expected["start_at"]) and _at(item["end_at"]) == _at(expected["end_at"])
    assert item["supported_kwh"] == expected["supported_kwh"]
    assert item["energy_complete"] is expected["energy_complete"]
    assert item["unknown_meter_seconds"] == expected["unknown_meter_seconds"]
    assert item["reason_codes"] == expected["reason_codes"]
    assert item["fault_evidence_id"] == expected["fault_evidence_id"]


def _read_case(c: TestClient, built, case: str, vector: dict) -> dict:
    body = get(c, "sessions")
    assert ENVELOPE | {"status", "denominator", "items", "next_cursor"} == set(body)
    assert set(body["denominator"]) == COUNTS and set(body["currentness"]) == {"state", "as_of", "limitation"}
    assert set(body["source_provenance"]) == {"classification", "source_ids", "evidence_ids", "basis_sha256"}
    assert body["source_provenance"]["classification"] == "REGISTERED_SIMULATION"
    assert body["source_provenance"]["evidence_ids"] == sorted(body["source_provenance"]["evidence_ids"])
    asset = str(_connector_asset(built, SELECTED[case])).lower()
    [item] = [x for x in body["items"] if x["connector_asset_id"] == asset]
    assert set(item) == ITEM and set(item["links"]) == LINKS
    assert item["connector_display_name"] == f"Connector {SELECTED[case]}"
    assert all(item["links"][k] is None for k in ("evidence", "analysis", "financials"))
    return {"body": body, "item": item}


@pytest.mark.parametrize("case", CASES)
def test_six_replays_read_through_the_selected_api(chain, case) -> None:  # noqa: F811
    vector = _vectors()[case]
    built = chain(case)
    built.start_release_upload()
    run_worker(built)
    c = client(built)
    read = _read_case(c, built, case, vector)
    body, item = read["body"], read["item"]
    counts = body["denominator"]
    assert counts["started"] == counts["completed"] + counts["observed_abort"] + counts["incomplete"] \
        + counts["contradictory"]
    if case == "late-record":
        first = vector["first_cutoff"]
        _session_matches(item, {**first, "end_at": None})
        assert body["currentness"]["state"] == "CURRENT" and counts["incomplete"] == 1
        assert item["completeness"] == {"start": True, "terminal": False, "meter": True, "clock": True}
        first_q, first_item = _q(body), item
        built.advance_late()
        pending = get(c, "sessions")  # the late END is accepted; its job is not run yet
        assert pending["currentness"]["state"] == "PENDING_RECOMPUTE"
        assert pending["currentness"]["limitation"] == "New evidence is being assessed. The previous result may change."
        assert [x["revision_id"] for x in pending["items"]] == [x["revision_id"] for x in body["items"]]
        run_worker(built)
        read = _read_case(c, built, case, vector)
        body, item = read["body"], read["item"]
        assert body["currentness"]["state"] == "CURRENT" and item["revision_no"] == 2
        historical = get(c, f"sessions?{first_q}")
        assert historical["currentness"]["state"] == "HISTORICAL"
        assert historical["currentness"]["limitation"] == "This result reflects records known at the selected cutoff."
        assert [x["revision_id"] for x in historical["items"]] == [first_item["revision_id"]]
        detail = get(c, f"sessions/{item['session_id']}?{_q(body)}")
        assert [h["state"] for h in detail["history"]] == ["INCOMPLETE", "COMPLETED"]
        old = get(c, f"sessions/{item['session_id']}?{first_q}")
        assert old["revision_id"] == first_item["revision_id"] and [h["revision_no"] for h in old["history"]] == [1]
    else:
        assert body["currentness"]["state"] == "CURRENT"
    _session_matches(item, vector["expected"])
    detail = get(c, item["links"]["self"])
    assert {k: detail[k] for k in ITEM} == item
    assert {"evidence", "meter_intervals", "history", "status", "denominator"} <= set(detail)
    expected_intervals = vector["expected"]["intervals"]
    assert [(x["evidence_id"], x["kwh"], x["use"], x["reason"]) for x in detail["meter_intervals"]] == \
        [(x["evidence_id"], x["kwh"], x["use"], x["reason"]) for x in expected_intervals]
    assert [x["evidence_id"] for x in detail["evidence"]] == [
        x["evidence_id"] for x in sorted(detail["evidence"], key=lambda e: (e["source_time"], e["evidence_id"]))]
    assert all(set(e) == {"evidence_id", "content_sha256", "use", "reason", "source_time", "received_at"}
               for e in detail["evidence"])
    findings = get(c, f"findings?{_q(body)}")
    if case == "interrupted":
        assert counts["fault_aborted"] == 1 and counts["confirmed_delivery"] == 0
        assert item["finding_id"] is not None and item["links"]["finding"] is not None
        finding = get(c, item["links"]["finding"])  # the proved link resolves at the same Site/window/cutoff
        assert finding["finding_id"] == item["finding_id"] and finding["lifecycle"] == "SUPPORTED"
        assert finding["claim"]["session_id"] == item["session_id"]
        assert set(finding["claim"]) == {"session_id", "external_session_id", "connector_asset_id", "start_at",
                                         "abort_at", "fault_evidence_id", "supported_kwh", "energy_complete"}
        assert sorted(e["evidence_id"] for e in finding["evidence"]) == \
            vector["expected"]["finding_support_evidence_ids"]
        assert [h["transition"] for h in finding["history"]] == ["OPENED"]
        assert finding["limitations"][0] == ("A connector fault and session abort were observed; component cause "
                                             "and unmet demand remain unknown.")
        assert [x["finding_id"] for x in findings["items"]] == [item["finding_id"]]
        assert set(findings["items"][0]) == {"finding_id", "revision_id", "revision_no", "basis_sha256",
                                             "session_id", "title", "claim_level", "lifecycle", "as_of", "links"}
        # Withdrawal (the FAULT source's clock proof revoked): the Finding leaves the list and the session; its
        # detail at the new selection is history only.
        _withdrawal(built, stored_findings(built)[0])
        now = get(c, "sessions")
        [after] = [x for x in now["items"] if x["session_id"] == item["session_id"]]
        assert after["finding_id"] is None and after["links"]["finding"] is None
        assert get(c, f"findings?{_q(now)}")["items"] == []
        gone = get(c, f"findings/{item['finding_id']}?{_q(now)}")
        assert gone["lifecycle"] == "NO_LONGER_SUPPORTED" and gone["claim"]["fault_evidence_id"] is None
        assert [h["transition"] for h in gone["history"]] == ["OPENED", "NO_LONGER_SUPPORTED"]
    else:
        assert findings["items"] == [] and item["finding_id"] is None and item["links"]["finding"] is None
    if case == "complete":
        assert counts["confirmed_delivery"] == 1 and item["completeness"] == {
            "start": True, "terminal": True, "meter": True, "clock": True}
    if case == "missing-meter":
        assert counts["confirmed_delivery"] == 0 and item["completeness"]["meter"] is False
    if case == "contradictory":
        assert body["status"]["state"] == "CONTRADICTORY" and item["completeness"]["meter"] is False
    if case == "fault":
        c1 = str(_connector_asset(built, "c1")).lower()
        assert [x for x in body["items"] if x["connector_asset_id"] == c1] == []


def test_refusals_unknown_and_one_snapshot_paging(chain) -> None:  # noqa: F811
    built = chain("complete")
    built.start_release_upload()
    run_worker(built)
    c = client(built)
    body = get(c, "sessions")
    [item] = body["items"]
    q = _q(body)
    w = body["window"]
    lo, hi, known = _at(w["from"]), _at(w["to"]), _at(w["known_at"])
    basis = body["source_provenance"]["basis_sha256"]

    # 401/403/404/503 seams, before any record lookup.
    deny = client(built, access=lambda request, code: 401).get(f"/api/sites/{CODE}/ev/sessions")
    assert deny.status_code == 401 and deny.headers["WWW-Authenticate"] == "Bearer"
    assert deny.json()["error"]["code"] == "UNAUTHENTICATED"
    assert error(client(built, access=lambda request, code: 403), "sessions", 403) == "SITE_SCOPE_FORBIDDEN"
    assert error(client(built, disclosure=lambda *a: False), "findings", 403) == "EV_SOURCE_DISCLOSURE_FORBIDDEN"
    assert error(c, "/api/sites/NOPE/ev/sessions", 404) == "SITE_NOT_FOUND"
    assert error(client(built, site_type="COLDCHAIN"), "sessions", 404) == "SITE_NOT_FOUND"
    assert error(client(built, reads=None), "sessions", 503) == "EV_READ_UNAVAILABLE"
    dead = client(built, reads=EvReadService("postgresql+psycopg://assetops:x@127.0.0.1:1/none_test"))
    refused = get(dead, "sessions", 503)
    assert refused["error"]["code"] == "EV_READ_UNAVAILABLE" and "127.0.0.1" not in refused["error"]["message"]

    # 404 for malformed, unknown, wrong-kind and foreign IDs; the same scoped code.
    for path in (f"sessions/not-a-uuid?{q}", f"sessions/{uuid4()}?{q}", f"findings/{item['session_id']}?{q}",
                 f"sessions/{item['revision_id']}?{q}"):
        assert error(c, path, 404) == "EV_RECORD_NOT_FOUND", path
    foreign = client(built, tenant=uuid4())
    assert error(foreign, f"sessions/{item['session_id']}?{q}", 404) == "EV_RECORD_NOT_FOUND"
    unknown = get(foreign, "sessions")
    assert unknown["currentness"]["state"] == "UNKNOWN" and unknown["items"] == []
    assert all(unknown["denominator"][k] is None for k in COUNTS - {"limitation"})

    # 422 parameter, time, window, limit and cursor refusals.
    for path, code in (
            ("sessions?from=2026-10-06T08:00:00Z", "EV_WINDOW_INVALID"),
            ("sessions?from=2026-10-06T09:00:00Z&to=2026-10-06T08:00:00Z", "EV_WINDOW_INVALID"),
            ("sessions?from=2026-10-01T00:00:00Z&to=2026-11-02T00:00:00Z", "EV_WINDOW_TOO_LONG"),
            ("sessions?from=2026-10-06T08:00:00%2B01:00&to=2026-10-06T09:00:00Z", "EV_TIME_INVALID"),
            ("sessions?known_at=2026-10-06T09:00:00.0000001Z", "EV_TIME_INVALID"),
            ("sessions?known_at=2026-10-06", "EV_TIME_INVALID"),
            ("sessions?known_at=2026-10-07T00:00:00Z", "EV_TIME_INVALID"),
            ("sessions?colour=red", "EV_PARAMETER_UNKNOWN"),
            ("sessions?limit=1&limit=2", "EV_PARAMETER_UNKNOWN"),
            (f"sessions/{item['session_id']}?{q}&limit=1", "EV_PARAMETER_UNKNOWN"),
            ("sessions?limit=0", "EV_LIMIT_INVALID"), ("sessions?limit=201", "EV_LIMIT_INVALID"),
            ("findings?limit=x", "EV_LIMIT_INVALID"),
            (f"sessions?{q}&cursor=not-a-cursor", "EV_CURSOR_INVALID")):
        assert error(c, path, 422) == code, path

    # A valid window without a selected assessment is 200 UNKNOWN, never 404 or 503.
    empty = get(c, "sessions?from=2026-10-01T00:00:00Z&to=2026-10-01T01:00:00Z")
    assert empty["currentness"] == {"state": "UNKNOWN", "as_of": None,
                                    "limitation": "No selected EV session assessment covers this window yet."}
    assert empty["items"] == [] and empty["status"]["state"] == "UNKNOWN"
    assert empty["window"]["from"] == "2026-10-01T00:00:00.000000Z"

    # Cursor bound to window/cutoff/basis: a changed basis is 409; a page after the last row is empty.
    before = encode_cursor(lo, hi, known, basis, lo - timedelta(seconds=1), UUID(int=0))
    assert [x["session_id"] for x in get(c, f"sessions?{q}&cursor={before}")["items"]] == [item["session_id"]]
    after = encode_cursor(lo, hi, known, basis, _at(item["start_at"]), UUID(item["session_id"]))
    assert get(c, f"sessions?{q}&cursor={after}&limit=1")["items"] == []
    changed = encode_cursor(lo, hi, known, "0" * 64, lo, UUID(int=0))
    assert error(c, f"sessions?{q}&cursor={changed}", 409) == "EV_CURSOR_BASIS_CHANGED"
    assert error(c, f"findings?{q}&cursor={changed}", 409) == "EV_CURSOR_BASIS_CHANGED"
    page = get(c, f"sessions?{q}&limit=1")
    assert page["next_cursor"] is None and page["denominator"] == body["denominator"]
    with built.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM analytic_run WHERE site_id = :s"),
                            {"s": built.site_id}).scalar_one() >= 1
