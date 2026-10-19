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
    from test_w206_ev_store_postgres import (
        LATE_HI,
        LATE_LO,
        _withdrawal,
        exact_heads,
        run_spying,
        run_worker,
        select_exact,
    )
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


# --- Run 7 rulings (r6): the five confirmed commit-4 choices, each with its named proof. ---

def _iso(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _settled(chain, case: str = "complete"):  # noqa: F811
    built = chain(case)
    built.start_release_upload()
    run_worker(built)
    return built, client(built)


def test_exact_window_does_not_use_covering_selection(chain) -> None:  # noqa: F811
    built, c = _settled(chain)
    body = get(c, "sessions")
    lo, hi, known = (_at(body["window"][k]) for k in ("from", "to", "known_at"))
    assert body["currentness"]["state"] == "CURRENT" and body["items"]
    assert get(c, f"sessions?{_q(body)}")["currentness"]["state"] == "CURRENT"
    # A narrower window the selection covers, and a wider window covering it: neither is the exact selected window.
    for a, b in ((lo, hi - timedelta(minutes=1)), (lo + timedelta(minutes=1), hi), (lo - timedelta(hours=1), hi)):
        q = f"from={_iso(a)}&to={_iso(b)}&known_at={_iso(known)}"
        for route in ("sessions", "findings"):
            other = get(c, f"{route}?{q}")
            assert other["currentness"]["state"] == "UNKNOWN" and other["items"] == [], (route, q)
            assert other["window"]["from"] == _iso(a) and other["window"]["to"] == _iso(b)
        assert all(get(c, f"sessions?{q}")["denominator"][k] is None for k in COUNTS - {"limitation"})
        assert error(c, f"sessions/{body['items'][0]['session_id']}?{q}", 404) == "EV_RECORD_NOT_FOUND"


def test_ev_source_age_never_emits_stale_source(chain) -> None:  # noqa: F811
    built, c = _settled(chain, "interrupted")
    body = get(c, "sessions")
    # The settled replay window is days older than the wall clock; source age alone never makes it stale.
    assert _at(body["window"]["to"]) < datetime.now(_at(body["window"]["to"]).tzinfo) - timedelta(days=1)
    q = _q(body)
    [item] = [x for x in body["items"] if x["finding_id"] is not None]
    reads = [body, get(c, f"sessions?{q}"), get(c, f"sessions/{item['session_id']}?{q}"),
             get(c, f"findings?{q}"), get(c, f"findings/{item['finding_id']}?{q}")]
    for read in reads:
        assert read["currentness"]["state"] == "CURRENT", read["currentness"]
        assert "STALE_SOURCE" not in json.dumps(read)


def test_historical_cutoff_precedes_pending_job(chain) -> None:  # noqa: F811
    built, c = _settled(chain, "late-record")
    first = get(c, "sessions")
    first_q = _q(first)
    [first_item] = first["items"]
    assert first["currentness"]["state"] == "CURRENT"
    built.advance_late()  # the late END is accepted and its overlapping job is PENDING, not yet run
    with built.engine.connect() as conn:
        jobs = conn.execute(text("SELECT count(*) FROM recompute_job WHERE site_id = :s AND domain = 'ev_charging' "
                                 "AND status = 'PENDING'"),
                            {"s": built.site_id}).scalar_one()
    assert jobs >= 1
    assert get(c, "sessions")["currentness"]["state"] == "PENDING_RECOMPUTE"
    for path in (f"sessions?{first_q}", f"sessions/{first_item['session_id']}?{first_q}", f"findings?{first_q}"):
        old = get(c, path)
        assert old["currentness"]["state"] == "HISTORICAL", path
        assert old["currentness"]["limitation"] == "This result reflects records known at the selected cutoff."
        assert old["window"]["known_at"] == first["window"]["known_at"]


def test_repeated_query_key_is_parameter_unknown(chain) -> None:  # noqa: F811
    built, c = _settled(chain)
    body = get(c, "sessions")
    w, sid = body["window"], body["items"][0]["session_id"]
    cursor = encode_cursor(_at(w["from"]), _at(w["to"]), _at(w["known_at"]),
                           body["source_provenance"]["basis_sha256"], _at(w["from"]), UUID(int=0))
    valid = {"from": w["from"], "to": w["to"], "known_at": w["known_at"], "limit": "5", "cursor": cursor}
    for route, keys in (("sessions", valid), ("findings", valid), (f"sessions/{sid}", ("from", "to", "known_at"))):
        base = "&".join(f"{k}={valid[k]}" for k in keys)
        for key in keys:
            # A repeat of an otherwise permitted key, valid or malformed, is refused before its value is parsed.
            for extra in (valid[key], "not-a-value"):
                path = f"{route}?{base}&{key}={extra}"
                assert error(c, path, 422) == "EV_PARAMETER_UNKNOWN", path


def test_only_cursor_basis_change_is_ev_read_409(chain) -> None:  # noqa: F811
    built, c = _settled(chain, "interrupted")
    body = get(c, "sessions")
    q, w = _q(body), body["window"]
    lo, hi, known = _at(w["from"]), _at(w["to"]), _at(w["known_at"])
    basis = body["source_provenance"]["basis_sha256"]
    item = next(x for x in body["items"] if x["finding_id"] is not None)
    changed = (encode_cursor(lo, hi, known, "0" * 64, lo, UUID(int=0)),  # basis changed
               encode_cursor(lo, hi, known - timedelta(seconds=1), basis, lo, UUID(int=0)))  # cutoff changed
    for cursor in changed:
        for route in ("sessions", "findings"):
            response = get(c, f"{route}?{q}&cursor={cursor}", 409)
            assert response == {"error": {"code": "EV_CURSOR_BASIS_CHANGED", "message": response["error"]["message"]}}
    # Every other non-cursor outcome is not a 409: no selection is 200 UNKNOWN, a scoped miss is 404.
    none = get(c, "sessions?from=2026-10-01T00:00:00Z&to=2026-10-01T01:00:00Z")
    assert none["currentness"]["state"] == "UNKNOWN"
    assert error(c, f"sessions/{uuid4()}?{q}", 404) == "EV_RECORD_NOT_FOUND"
    assert error(c, f"findings/{uuid4()}?{q}", 404) == "EV_RECORD_NOT_FOUND"
    for path in (f"sessions/{item['session_id']}?{q}", f"findings/{item['finding_id']}?{q}", f"findings?{q}"):
        assert c.get(f"/api/sites/{CODE}/ev/{path}").status_code == 200
    # The unsettled-selection code is not part of the reachable W2-06 contract.
    import assetops_backend.analytics.adapters.postgres_assessment_store as store
    import assetops_backend.analytics.ev_reads as rules
    import assetops_backend.ev_assessment_api as api
    for module in (api, rules, store):
        assert "SELECTION_UNSETTLED" not in open(module.__file__, encoding="utf-8").read(), module.__name__


def test_wider_replacement_never_leaves_exact_window_current_on_stale_head(chain) -> None:  # noqa: F811
    """r8 H1: a later wider DEFAULT selection over the exact key never supersedes the exact head by itself; the job
    that brings the late terminal re-heads every intersecting exact selection before any reads CURRENT."""
    built, c = _settled(chain, "late-record")
    lo, hi, wide = LATE_LO, LATE_HI, LATE_HI + timedelta(minutes=5)
    select_exact(built, lo, hi)
    select_exact(built, lo, wide)  # the wider/replacing selection, written after the exact one
    q = f"from={_iso(lo)}&to={_iso(hi)}"
    stale = get(c, f"sessions?{q}")
    [old_head] = exact_heads(built, lo, hi)
    assert stale["currentness"]["state"] == "CURRENT"
    assert stale["source_provenance"]["basis_sha256"] == old_head.basis_sha256
    assert [i["state"] for i in stale["items"]] == ["INCOMPLETE"]
    built.advance_late()
    pending = get(c, f"sessions?{q}")
    assert pending["currentness"]["state"] == "PENDING_RECOMPUTE"
    assert pending["source_provenance"]["basis_sha256"] == old_head.basis_sha256
    _outcomes, seen = run_spying(built, lo, hi)
    assert set(seen["status"]) == {"LEASED"} and set(seen["state"]) == {"PENDING_RECOMPUTE"}
    # One job transaction re-heads both exact keys; neither stands in for the other.
    assert any({(lo, hi), (lo, wide)} <= set(windows) for windows in seen["windows"])
    heads = exact_heads(built, lo, hi)
    assert heads[0].run_id == old_head.run_id and heads[-1].revision_no == old_head.revision_no + 1
    assert heads[-1].basis_sha256 != old_head.basis_sha256 and heads[-1].job_id is not None
    assert exact_heads(built, lo, wide)[-1].job_id == heads[-1].job_id
    current = get(c, f"sessions?{q}")
    assert current["currentness"]["state"] == "CURRENT"
    assert current["window"]["from"] == _iso(lo) and current["window"]["to"] == _iso(hi)
    assert current["source_provenance"]["basis_sha256"] == heads[-1].basis_sha256
    [item] = current["items"]
    assert item["state"] == "COMPLETED" and _at(item["end_at"]) == datetime(2026, 10, 6, 8, 31, tzinfo=lo.tzinfo)


@pytest.mark.parametrize("case, expected", [
    ("complete", {"start": True, "terminal": True, "meter": True, "clock": True}),
    ("contradictory", {"start": True, "terminal": False, "meter": False, "clock": True}),
    ("missing-meter", {"start": True, "terminal": True, "meter": False, "clock": True}),
])
def test_completeness_uses_selected_evidence_not_reason_absence(chain, case, expected) -> None:  # noqa: F811
    """r8 M2: the four booleans come from the selected revision's SUPPORT uses; the contradictory case's terminals
    are CONTEXT/CONFLICTING_TERMINAL, so no Terminal chip although no MISSING_TERMINAL reason is stored."""
    built, c = _settled(chain, case)
    body = get(c, "sessions")
    asset = str(_connector_asset(built, SELECTED[case])).lower()
    [item] = [x for x in body["items"] if x["connector_asset_id"] == asset]
    assert item["completeness"] == expected, case
    detail = get(c, f"sessions/{item['session_id']}?{_q(body)}")
    assert detail["completeness"] == expected
    support = [e for e in detail["evidence"] if e["use"] == "SUPPORT" and e["reason"] is None]
    if case == "contradictory":
        assert "MISSING_TERMINAL" not in item["reason_codes"]
        assert {e["reason"] for e in detail["evidence"] if e["use"] == "CONTEXT"} >= {"CONFLICTING_TERMINAL"}
        assert len(support) == 1  # the START alone
    # A revision with no SUPPORT row and no reason code shows no present chip (reason absence creates nothing).
    from assetops_backend.analytics.ev_reads import completeness
    assert completeness("COMPLETED", 0, [("EV_SESSION_START", "CONTEXT", None)], [("CONTEXT", None)]) == {
        "start": False, "terminal": False, "meter": False, "clock": False}


def test_finding_evidence_matches_selected_session_support(chain) -> None:  # noqa: F811
    """r8 M3: the selected Finding revision's evidence is exactly the selected session revision's SUPPORT START,
    FAULT and ABORT, matched by accepted ID and event kind, and the claim's fault is that FAULT."""
    built, c = _settled(chain, "interrupted")
    body = get(c, "sessions")
    q = _q(body)
    item = next(x for x in body["items"] if x["finding_id"] is not None)
    finding = get(c, f"findings/{item['finding_id']}?{q}")
    session = get(c, f"sessions/{item['session_id']}?{q}")
    with built.engine.connect() as conn:
        kinds = {str(i).lower(): k for i, k in conn.execute(text(
            "SELECT id, record_kind FROM accepted_evidence WHERE site_id = :s AND family = 'EVENT'"),
            {"s": built.site_id}).all()}
    support = {e["evidence_id"]: kinds.get(e["evidence_id"]) for e in session["evidence"]
               if e["use"] == "SUPPORT" and e["reason"] is None}
    wanted = {"EV_SESSION_START", "EV_CONNECTOR_FAULT", "EV_SESSION_ABORT"}
    by_kind = {k: i for i, k in support.items() if k in wanted}
    assert set(by_kind) == wanted
    cited = sorted(e["evidence_id"] for e in finding["evidence"])
    assert cited == sorted(by_kind.values())
    assert finding["claim"]["fault_evidence_id"] == by_kind["EV_CONNECTOR_FAULT"] == item["fault_evidence_id"]
    vector = _vectors()["interrupted"]["expected"]
    assert cited == sorted(vector["finding_support_evidence_ids"])
