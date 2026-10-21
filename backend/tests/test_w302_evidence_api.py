"""W3-02 commit 1: the estate Evidence root over a fake one-transaction snapshot (no database).

Router refusals with `gaps:null`, the literal empty-scope vector, W1 day rows, grouped cold/EV window rows with
their own citations, typed gaps (no BILLING_GAP), placeholders, row-local links, the 3-part cursor and its fence,
and the partial-coverage count rule. The Postgres proof is `test_w302_evidence_scope_snapshot_postgres.py`.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import urlencode
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.analytics.cold_site_reads import EXC, START
from assetops_backend.analytics.dispatch import CANDIDATE
from assetops_backend.analytics.claim_limit_read import ClaimLimitRefusal
from assetops_backend.estate import evidence_money
from assetops_backend.estate.adapters.postgres_evidence_money_read import EvidenceMoneySnapshot
from assetops_backend.estate.evidence_money import EstateEvidenceService
from assetops_backend.estate.scope import EstateSelectionInconsistent, EstateStoreUnavailable, decode_cursor
from assetops_backend.estate_evidence_money_api import build_estate_evidence_money_router

T = UUID("10000000-0000-4000-8000-000000000001")
MG, CO, EVS = (UUID(f"10000000-0000-4000-8000-0000000000{n}") for n in ("11", "12", "13"))
READ_AT = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)
WINDOW = {"from": "2026-10-13T00:00:00Z", "to": "2026-10-20T00:00:00Z"}
D0 = datetime(2026, 10, 13, tzinfo=timezone.utc)
CUT = datetime(2026, 10, 20, 6, tzinfo=timezone.utc)
A = {n: f"20000000-0000-4000-8000-0000000000{n:02d}" for n in range(1, 50)}


def site(sid, code, kind):
    return {"site_id": sid, "site_code": code, "site_name": f"{code} name", "site_type": kind,
            "site_code_key": code.lower()}


SITES = [site(MG, "KOBO-001", "MINIGRID"), site(CO, "COLD 1", "COLDCHAIN"), site(EVS, "EV-1", "EV_CHARGING")]


def interval(rid, state, *, ceiling=CANDIDATE, statement="Candidate in supported portions", reasons=(),
             evidence=()):
    current = state in ("FULL", "LIMITED", "NONE")
    return {"assessment_revision_id": rid, "state": state, "currentness": "CURRENT" if current else "HISTORICAL",
            "ceiling": ceiling if current else None, "statement": statement if current else None,
            "support": "COMPLETE" if state == "FULL" else state, "supported_minutes": None,
            "current_positive_claim": current, "historical_ceiling": None, "reasons": list(reasons),
            "accepted_evidence_ids": list(evidence), "selected": True}


def projection(day, intervals, *, currentness="CURRENT", window=None, available=True):
    return {"available": available, "currentness": currentness, "intervals": intervals, "day": day.isoformat(),
            "window_assessment_revision_id": window, "known_at": READ_AT, "site_id": str(MG), "reasons": []}


def cold_caps(states, missing=None):
    missing = missing or {}
    return [{"claim": c, "state": states.get(c, "SUPPORTED"), "missing_roles": missing.get(c, []),
             "limitation": None if states.get(c, "SUPPORTED") == "SUPPORTED" else f"{c} limited"}
            for c in ("TEMPERATURE_POINT", "EXCURSION_BOUNDS", "BACKUP_START_RESULT", "TRANSFER_POSITION",
                      "COOLING_RESPONSE", "PRODUCT_EXPOSURE")]


def ev_caps(missing=None):
    missing = missing or {}
    out = []
    for claim in ("SESSION_OUTCOME", "SERVICE_STATE", "DELIVERED_ENERGY", "FAULT_ASSOCIATION", "SITE_POWER_CONTEXT",
                  "POWER_CONSTRAINT", "GROSS_TARIFF_SCENARIO"):
        roles = missing.get(claim, [])
        out.append({"claim": claim, "state": "LIMITED" if roles else "SUPPORTED", "missing_roles": roles,
                    "limitation": None, "accepted_evidence_ids": [A[30 + len(out)]]})
    return out


def pin(lo, state="CURRENT"):
    return {"lo": lo, "hi": lo + timedelta(days=1), "known": CUT, "watermark": CUT, "state": state}


class FakeSnapshot:
    def __init__(self, sites=SITES, *, cold_pins=None, ev_pins=None, days=None, historical=False,
                 unknown_meter=False, sessions=(A[40],)):
        self.read_at, self.historical, self.continuation = READ_AT, False, False
        self.basis_historical, self._sites = historical, list(sites)
        self.cold_pins = [pin(D0), pin(D0 + timedelta(days=1))] if cold_pins is None else cold_pins
        self.ev_pins = [pin(D0)] if ev_pins is None else ev_pins
        self.days = days if days is not None else [
            (date(2026, 10, 13), projection(date(2026, 10, 13), [
                interval(A[1], "LIMITED", evidence=[A[20]], reasons=[
                    {"code": "MISSING_ROLE", "role": "battery_soc", "text": "x"},
                    {"code": "LIMITED", "text": "role-less"}])], window=A[2])),
            (date(2026, 10, 14), projection(date(2026, 10, 14), [], currentness="UNASSESSED")),
        ]
        self.provenance_calls, self.basis_modes = [], []
        self.unknown_meter, self.sessions = unknown_meter, list(sessions)

    def imported_sites(self, t, to):
        return self._sites

    def evidence_cutoff(self, t, s, k):
        return CUT

    def dispatch_days(self, t, s, from_, to, k):
        return [{"day": d, "window_start": datetime(d.year, d.month, d.day, tzinfo=timezone.utc),
                 "window_end": datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(days=1),
                 "available": p["available"], "selection": {"seq": 1} if p["intervals"] else None,
                 "window_assessment_revision_id": p["window_assessment_revision_id"]} for d, p in self.days]

    def claim_limit_on(self, t, s, day, revision, k, basis_mode):
        self.basis_modes.append(basis_mode)
        return dict(self.days)[day]

    def pinned_windows(self, t, s, domain, from_, to, cutoff, k):
        return self.cold_pins if domain == "cold_chain" else self.ev_pins

    def cold_capabilities(self, p):
        n = self.cold_pins.index(p)
        states = {"EXCURSION_BOUNDS": "LIMITED", "TRANSFER_POSITION": "CONTRADICTORY"} if n == 0 else {}
        return {"assessment_revision_ids": {EXC: A[3 + 2 * n], START: A[4 + 2 * n]},
                "evidence_by_analytic": {EXC: [A[10 + n]], START: [A[12 + n]]},
                "capabilities": cold_caps(states, {"EXCURSION_BOUNDS": ["cold_policy_low"]} if n == 0 else {})}

    def ev_capabilities(self, p):
        return {"assessment_revision_id": A[8], "evidence_ids": [A[30]], "unknown_meter": self.unknown_meter,
                "session_revision_ids": self.sessions,
                "capabilities": ev_caps({"SERVICE_STATE": ["connector_status"],
                                         "POWER_CONSTRAINT": ["requested_power", "allocated_limit"]})}

    def cited_provenance(self, t, s, cited, selected):
        self.provenance_calls.append((str(s), list(cited), list(selected)))
        return {"classification": "SUPPORTED", "state": "SUPPORTED", "source_ids": [], "evidence_ids": list(cited),
                "basis_sha256": "sha256:" + "0" * 64, "reasons": []}


class FakeStore:
    def __init__(self, *outcomes):
        self.outcomes, self.calls = list(outcomes), 0

    def read(self, work):
        self.calls += 1
        outcome = self.outcomes[min(self.calls, len(self.outcomes)) - 1]
        if isinstance(outcome, BaseException):
            raise outcome
        return work(outcome)


@pytest.fixture(autouse=True)
def coverage(monkeypatch):
    """The W3-01 per-Site coverage is proved by its own suites; here it is a CURRENT stub per domain."""
    states = {}

    def fake(snap, t, s, domain, from_, to, k):
        return {"selection_id": None, "watermark": CUT, "match_state": "COMPLETE", "job_state": "SETTLED",
                "source_freshness": "RECENT", "state": states.get(s, "HISTORICAL" if snap.basis_historical
                                                                      else "CURRENT"), "rows": []}
    monkeypatch.setattr(evidence_money, "site_coverage", fake)
    return states


def client(store, tenant=T, authenticate=lambda request: None, service=True, access=None):
    app = FastAPI()
    kwargs = {} if access is None else {"access": access}
    app.include_router(build_estate_evidence_money_router(EstateEvidenceService(store) if service else None,
                                                          lambda: tenant, authenticate=authenticate, **kwargs))
    return TestClient(app)


def get(c, query):
    return c.get("/api/estate/evidence?" + (query if isinstance(query, str) else urlencode(query)))


def test_w302_evidence_api_errors_and_empty_scope() -> None:
    store = FakeStore(FakeSnapshot(sites=[]))
    response = get(client(store, authenticate=lambda r: 401), "from=bad&nope=1")
    assert response.status_code == 401 and response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": {"code": "UNAUTHENTICATED", "message": "Sign in to read estate records.",
                                          "rows": None, "total_count": None, "gaps": None}}
    assert store.calls == 0
    c = client(store)
    for query, code in [("to=2026-10-20T00:00:00Z", "INVALID_WINDOW"),
                        (urlencode(WINDOW) + "&lens=all", "INVALID_CURSOR"),
                        (urlencode(WINDOW) + "&limit=1&limit=2", "INVALID_CURSOR"),
                        (urlencode(WINDOW) + "&limit=0", "INVALID_LIMIT"),
                        (urlencode(WINDOW) + "&limit=101", "INVALID_LIMIT"),
                        (urlencode(WINDOW) + "&known_at=2026-10-20T12:00:00", "INVALID_KNOWN_AT"),
                        (urlencode(WINDOW) + "&cursor=abc", "INVALID_CURSOR")]:
        response = get(c, query)
        assert response.status_code == 422, query
        assert response.json() == {"detail": {"code": code, "message": response.json()["detail"]["message"],
                                              "rows": None, "total_count": None, "gaps": None}}
    later = get(c, {**WINDOW, "known_at": "2026-10-21T00:00:00Z"})
    assert (later.status_code, later.json()["detail"]["code"]) == (422, "INVALID_KNOWN_AT")
    for outcome, status, code in [(EstateStoreUnavailable("x"), 503, "ESTATE_STORE_UNAVAILABLE"),
                                  (EstateSelectionInconsistent("x"), 409, "ESTATE_SELECTION_INCONSISTENT")]:
        response = get(client(FakeStore(outcome)), WINDOW)
        assert response.status_code == status
        assert response.json()["detail"]["code"] == code and response.json()["detail"]["gaps"] is None
        assert "rows" not in response.json()
    no_db = get(client(store, service=False), WINDOW)
    assert no_db.status_code == 503 and no_db.json()["detail"] == {
        "code": "ESTATE_STORE_UNAVAILABLE", "message": "Estate records could not be read.", "rows": None,
        "total_count": None, "gaps": None}
    # The literal closure-1 empty-scope vector with the closure-4 `/2` selection token.
    body = get(c, {**WINDOW, "known_at": "2026-10-20T12:00:00Z"}).json()
    assert body == {
        "schema_version": "estate-evidence-1",
        "scope": {"tenant_id": str(T), "authorized_site_count": 0, "covered_site_count": 0,
                  "access_basis": "sha256:df70eb2392c008ed241b3251f79f7ed2c9130159aa73c0c4d96cf7ec36fceea1"},
        "window": {"from": "2026-10-13T00:00:00Z", "to": "2026-10-20T00:00:00Z", "bounds": "[from, to)",
                   "known_at": "2026-10-20T12:00:00Z"},
        "status": "EMPTY_SCOPE", "coverage": {"state": "EMPTY", "sites": []},
        "summary": {"limited_site_count": 0, "priority_gap_count": None, "unsupported_claim_count": None,
                    "capability_count": 0, "full_count": 0, "limited_count": 0, "none_count": 0,
                    "unknown_count": 0},
        "order": "site_code_key asc, site_id asc, capability_key asc", "total_count": 0, "rows": [], "gaps": [],
        "next_cursor": None,
        "selection_token": "sha256:5944cb919416dc307e7ce4b40c4cc4d047bcee9ec2d72b1a41815716b1d8765e"}
    # A denied Site never enters a row, count or digest.
    denied = get(client(FakeStore(FakeSnapshot()), access=lambda request, code: 403), WINDOW).json()
    assert denied["status"] == "EMPTY_SCOPE" and denied["rows"] == []


def test_w302_evidence_authorized_scope_and_placeholders(coverage) -> None:
    snap = FakeSnapshot(cold_pins=[], ev_pins=[])
    body = get(client(FakeStore(snap)), WINDOW).json()
    keys = [(r["site_code"], r["capability_key"]) for r in body["rows"]]
    # W1: one row per intersecting day; cold/EV without a selected window: four unsuffixed placeholders.
    assert keys == [("COLD 1", k) for k in ("backup", "cooling", "exposure", "temperature")] + \
        [("EV-1", k) for k in ("availability", "cause", "energy", "sessions")] + \
        [("KOBO-001", "GENERATOR_SUPPORT@2026-10-13"), ("KOBO-001", "GENERATOR_SUPPORT@2026-10-14")]
    holders = [r for r in body["rows"] if r["raw_state"] == "UNASSESSED"]
    assert len(holders) == 9
    for row in holders:
        assert row["readiness"] == "UNKNOWN" and row["current_ceiling"] is None and row["next_evidence"] is None
        assert row["selected_revision_ids"] == [] and row["source_provenance"]["basis_sha256"] is None
        assert row["links"]["site_readiness_label"] == "Opens current Site view"
    assert next(r for r in holders if r["site_code"] == "COLD 1")["links"]["site"] == "/sites/COLD%201"
    assert body["total_count"] == body["summary"]["capability_count"] == 10
    assert body["summary"]["unknown_count"] == 9 and body["summary"]["limited_count"] == 1
    assert [s["site_id"] for s in body["coverage"]["sites"]] == [str(MG), str(CO), str(EVS)]
    assert set(body["coverage"]["sites"][0]) == {"site_id", "state", "committed_watermark", "selection_id",
                                                 "match_state", "job_state", "source_freshness"}
    # Partial coverage: total_count still counts display rows; truth-dependent counts are null.
    coverage[EVS] = "UNKNOWN"
    partial = get(client(FakeStore(FakeSnapshot(cold_pins=[], ev_pins=[]))), WINDOW).json()
    assert partial["coverage"]["state"] == "PARTIAL" and partial["status"] == "UNKNOWN"
    assert partial["total_count"] == partial["summary"]["capability_count"] == 10
    assert all(partial["summary"][k] is None for k in ("limited_site_count", "full_count", "limited_count",
                                                       "none_count", "unknown_count"))


def test_w302_evidence_grouped_rows_and_full_citations() -> None:
    snap = FakeSnapshot()
    body = get(client(FakeStore(snap)), {**WINDOW, "limit": 100}).json()
    rows = {(r["site_code"], r["capability_key"]): r for r in body["rows"]}
    w0 = "@2026-10-13T00:00:00.000000Z/2026-10-14T00:00:00.000000Z"
    w1 = "@2026-10-14T00:00:00.000000Z/2026-10-15T00:00:00.000000Z"
    assert body["total_count"] == 2 + 8 + 4  # W1 days, two cold windows x four, one EV window x four
    temp, backup = rows[("COLD 1", "temperature" + w0)], rows[("COLD 1", "backup" + w0)]
    assert (temp["readiness"], backup["readiness"], rows[("COLD 1", "backup" + w1)]["readiness"]) == (
        "LIMITED", "CONTRADICTORY", "FULL")
    assert temp["selected_revision_ids"] == [A[3]] and backup["selected_revision_ids"] == [A[4]]
    assert [c["claim"] for c in temp["disclosure"]["constituents"]] == ["TEMPERATURE_POINT", "EXCURSION_BOUNDS"]
    assert temp["current_ceiling"] == "EXCURSION_BOUNDS limited" and temp["ceiling_source"] == "COLD_LIMITATION"
    # Never borrow from another window: the second window cites its own analytic revisions and Evidence.
    assert rows[("COLD 1", "temperature" + w1)]["selected_revision_ids"] == [A[5]]
    cited = {tuple(sel): tuple(c) for _, c, sel in snap.provenance_calls}
    assert cited[(A[3],)] == (A[10],) and cited[(A[5],)] == (A[11],) and cited[(A[6],)] == (A[13],)
    kobo = rows[("KOBO-001", "GENERATOR_SUPPORT@2026-10-13")]
    assert (kobo["raw_state"], kobo["readiness"], kobo["current_ceiling"], kobo["ceiling"]) == (
        "LIMITED", "LIMITED", "Candidate in supported portions", CANDIDATE)
    assert kobo["ceiling_source"] == "W1_CLAIM_LIMIT" and kobo["selected_revision_ids"] == [A[1]]
    assert kobo["disclosure"]["window_assessment_revision_id"] == A[2]
    ev = rows[("EV-1", "availability" + w0)]
    assert ev["links"]["site_readiness"] == (
        "/sites/EV-1/ev/evidence?from=2026-10-13T00%3A00%3A00.000000Z&to=2026-10-14T00%3A00%3A00.000000Z"
        "&known_at=2026-10-20T06%3A00%3A00.000000Z") and ev["links"]["site_readiness_label"] is None
    assert temp["links"]["site_readiness"].startswith("/sites/COLD%201/evidence?from=2026-10-13")
    assert [c["claim"] for c in ev["disclosure"]["supporting_claims"]] == [
        "SITE_POWER_CONTEXT", "POWER_CONSTRAINT", "GROSS_TARIFF_SCENARIO"]
    assert body["summary"]["limited_site_count"] is None  # a CONTRADICTORY row nulls the affected count
    # A row-local cutoff later than the estate cutoff (or unequal to the Site cutoff) falls back to the base route.
    bad = evidence_money.window_links("EV-1", "ev_charging", pin(D0), CUT - timedelta(hours=1), READ_AT)
    assert bad == {"site": "/sites/EV-1", "site_readiness": "/sites/EV-1",
                   "site_readiness_label": "Opens current Site view"}
    late = evidence_money.window_links("EV-1", "ev_charging", pin(D0), CUT, CUT - timedelta(hours=1))
    assert late["site_readiness"] == "/sites/EV-1"


def test_w302_evidence_typed_gaps_exclude_billing() -> None:
    body = get(client(FakeStore(FakeSnapshot())), {**WINDOW, "limit": 100}).json()
    gaps = {(g["domain"], g["gap_code"], g["missing_role"]): g for g in body["gaps"]}
    assert list(gaps) == sorted(gaps, key=lambda k: (k[0], k[1], k[2] or ""))
    assert set(gaps) == {("cold_chain", "MISSING_ROLE", "cold_policy_low"),
                         ("ev_charging", "INDEPENDENT_POWER_GAP", None), ("ev_charging", "STATUS_GAP", None),
                         ("mini_grid", "MISSING_ROLE", "battery_soc")}
    assert all(g["gap_code"] != "BILLING_GAP" for g in body["gaps"])
    soc = gaps[("mini_grid", "MISSING_ROLE", "battery_soc")]
    assert (soc["label"], soc["next_step"]) == ("Missing Battery state of charge", "Record Battery state of charge")
    assert soc["site_ids"] == [str(MG)] and soc["unlocks"] == ["GENERATOR_SUPPORT@2026-10-13"]
    status = gaps[("ev_charging", "STATUS_GAP", None)]
    assert (status["label"], status["next_step"]) == ("Missing connector status history",
                                                      "Recover connector status history")
    assert status["unlocks"] == ["availability@2026-10-13T00:00:00.000000Z/2026-10-14T00:00:00.000000Z"]
    assert gaps[("ev_charging", "INDEPENDENT_POWER_GAP", None)]["unlocks"] == []  # supporting claim only
    policy = gaps[("cold_chain", "MISSING_ROLE", "cold_policy_low")]
    assert (policy["label"], policy["next_step"]) == ("Missing Temperature policy low",
                                                      "Connect or record Temperature policy low")
    rows = {r["capability_key"]: r for r in body["rows"]}
    assert rows["GENERATOR_SUPPORT@2026-10-13"]["gap_codes"] == ["MISSING_ROLE"]
    assert rows["GENERATOR_SUPPORT@2026-10-13"]["next_evidence"] == "Record Battery state of charge"
    # Historical: IDs kept, no current claim, no current gap group.
    old = get(client(FakeStore(FakeSnapshot(historical=True))), {**WINDOW, "known_at": "2026-10-20T06:00:00Z"})
    hist = old.json()
    assert hist["status"] == "HISTORICAL" and hist["summary"]["as_of"] == "2026-10-20T06:00:00Z"
    cold_rows = [r for r in hist["rows"] if r["domain"] == "cold_chain"]
    assert {r["raw_state"] for r in cold_rows} == {"HISTORICAL"}
    assert all(r["current_ceiling"] is None and r["gap_codes"] == [] and r["selected_revision_ids"]
               for r in cold_rows)
    assert {r["readiness"] for r in cold_rows} == {"UNKNOWN", "CONTRADICTORY"}
    # c1-q1: the estate basis labels the W1 day HISTORICAL too, even though its fake projection is CURRENT.
    day = next(r for r in hist["rows"] if r["capability_key"] == "GENERATOR_SUPPORT@2026-10-13")
    assert (day["raw_state"], day["readiness"], day["current_ceiling"], day["gap_codes"]) == (
        "HISTORICAL", "UNKNOWN", None, [])
    assert day["disclosure"]["historical"]["label"] == "Historical as of 2026-10-20T06:00:00Z"
    assert day["selected_revision_ids"] and hist["gaps"] == []


def test_w302_evidence_gap_site_names_cover_rows_on_other_pages() -> None:
    """c2-q1: `gaps[].site_names` is the full group's stored names, parallel to `site_ids`/`site_codes`, built
    before row pagination, so a gap whose Site rows are all on another page still names its Sites."""
    full = get(client(FakeStore(FakeSnapshot())), {**WINDOW, "limit": 100}).json()
    first = get(client(FakeStore(FakeSnapshot())), {**WINDOW, "limit": 1}).json()
    on_page = {r["site_id"] for r in first["rows"]}
    off_page = [g for g in first["gaps"] if not on_page & set(g["site_ids"])]
    assert off_page, "expected a gap whose Site rows are all on a later page"
    assert first["gaps"] == full["gaps"]
    for gap in first["gaps"]:
        assert len(gap["site_names"]) == len(gap["site_codes"]) == len(gap["site_ids"])
        assert gap["site_names"] == [f"{code} name" for code in gap["site_codes"]]


def test_w302_evidence_meter_gap_and_frozen_basis_mode() -> None:
    """c1-q2: the public `unknown_meter` gives METER_GAP on the energy row; c1-q7: W1 receives the frozen basis."""
    snap = FakeSnapshot(unknown_meter=True)
    body = get(client(FakeStore(snap)), {**WINDOW, "limit": 100}).json()
    meter = next(g for g in body["gaps"] if g["gap_code"] == "METER_GAP")
    assert meter["unlocks"] == ["energy@2026-10-13T00:00:00.000000Z/2026-10-14T00:00:00.000000Z"]
    assert set(snap.basis_modes) == {"live"}
    assert all(g["gap_code"] != "METER_GAP" for g in get(client(FakeStore(FakeSnapshot())), WINDOW).json()["gaps"])
    old = FakeSnapshot(historical=True)
    get(client(FakeStore(old)), {**WINDOW, "known_at": "2026-10-20T06:00:00Z"})
    assert set(old.basis_modes) == {"historical"}
    # c1 r1 M1: on a live basis a W2 pin HISTORICAL is the as-of selection, not an unknown pin; a missing pin is.
    live = get(client(FakeStore(FakeSnapshot(cold_pins=[pin(D0, "HISTORICAL"), pin(D0 + timedelta(days=1))],
                                            ev_pins=[pin(D0, "HISTORICAL")]))), {**WINDOW, "limit": 100}).json()
    base = get(client(FakeStore(FakeSnapshot())), {**WINDOW, "limit": 100}).json()
    assert live["status"] == "CURRENT"
    assert [(r["capability_key"], r["raw_state"], r["readiness"]) for r in live["rows"]] == [
        (r["capability_key"], r["raw_state"], r["readiness"]) for r in base["rows"]]
    assert live["gaps"] == base["gaps"]
    odd = get(client(FakeStore(FakeSnapshot(ev_pins=[pin(D0, "MISSING")]))), {**WINDOW, "limit": 100}).json()
    assert {r["raw_state"] for r in odd["rows"] if r["domain"] == "ev_charging"} == {"UNKNOWN"}


def test_w302_evidence_cursor_same_selection_and_changed_grant() -> None:
    store = FakeStore(FakeSnapshot())
    c = client(store)
    first = get(c, {**WINDOW, "limit": 5}).json()
    assert len(first["rows"]) == 5 and first["next_cursor"] is not None
    payload = decode_cursor("evidence", first["next_cursor"])
    assert payload["kind"] == "evidence" and payload["page_one_mode"] == "live"
    assert payload["after"] == ["cold 1", str(CO).lower(), first["rows"][-1]["capability_key"]]
    seen, cursor = list(first["rows"]), first["next_cursor"]
    while cursor:
        page = get(c, {**WINDOW, "limit": 5, "cursor": cursor}).json()
        assert page["selection_token"] == first["selection_token"] and page["total_count"] == first["total_count"]
        seen += page["rows"]
        cursor = page["next_cursor"]
    assert [r["capability_key"] for r in seen] == [r["capability_key"] for r in
                                                   get(c, {**WINDOW, "limit": 100}).json()["rows"]]
    # A changed grant (one Site denied) is 409 on the old cursor; a changed selection likewise.
    denied = client(FakeStore(FakeSnapshot()), access=lambda request, code: 403 if code == "EV-1" else None)
    response = get(denied, {**WINDOW, "limit": 5, "cursor": first["next_cursor"]})
    assert (response.status_code, response.json()["detail"]["code"]) == (409, "ESTATE_BASIS_CHANGED")
    changed = client(FakeStore(FakeSnapshot(ev_pins=[])))
    response = get(changed, {**WINDOW, "limit": 5, "cursor": first["next_cursor"]})
    assert (response.status_code, response.json()["detail"]["code"]) == (409, "ESTATE_BASIS_CHANGED")
    # c1-q3(5): a session-only correction (same assessment, new session revision) also moves the fence.
    corrected = client(FakeStore(FakeSnapshot(sessions=(A[41],))))
    response = get(corrected, {**WINDOW, "limit": 5, "cursor": first["next_cursor"]})
    assert (response.status_code, response.json()["detail"]["code"]) == (409, "ESTATE_BASIS_CHANGED")
    assert response.json()["detail"]["gaps"] is None
    # A wrong-kind cursor is 422.
    from assetops_backend.estate.scope import encode_cursor
    wrong = encode_cursor({**payload, "kind": "financials"})
    response = get(c, {**WINDOW, "cursor": wrong})
    assert (response.status_code, response.json()["detail"]["code"]) == (422, "INVALID_CURSOR")


REFUSALS = (("UNSUPPORTED_RULE_VERSION", 422), ("ASSESSMENT_REVISION_NOT_FOUND", 404),
            ("REVISION_OUTSIDE_WINDOW", 422), ("REVISION_NOT_WINDOW", 422), ("ACCEPTED_LINEAGE_ABSENT", 409))
MG2 = UUID("10000000-0000-4000-8000-000000000014")


class RefusingSnapshot(FakeSnapshot):
    """The real adapter mapping over a claim-limit store that refuses one Site's day."""
    claim_limit_on = EvidenceMoneySnapshot.claim_limit_on

    def __init__(self, refuse_site, code, **kwargs):
        super().__init__(**kwargs)
        outer = self

        class Limits:
            def claim_limit_on(self, c, t, s, day, revision, k, basis_mode):
                if s == refuse_site:
                    raise ClaimLimitRefusal(dict(REFUSALS)[code], code, f"refused {code}")
                return dict(outer.days)[day]
        self._o, self._c = SimpleNamespace(claim_limits=Limits(), claim_limit_refused=ClaimLimitRefusal), None


@pytest.mark.parametrize("code,status", REFUSALS)
def test_w302_evidence_w1_refusals_are_unknown_days(code, status) -> None:
    sites = [SITES[0], site(MG2, "KOBO-002", "MINIGRID")]
    response = get(client(FakeStore(RefusingSnapshot(MG, code, sites=sites))), {**WINDOW, "limit": 100})
    assert response.status_code == 200
    rows = {(r["site_code"], r["capability_key"]): r for r in response.json()["rows"]}
    for day in ("2026-10-13", "2026-10-14"):  # every day of the refused Site is a refused day
        r = rows[("KOBO-001", f"GENERATOR_SUPPORT@{day}")]
        assert (r["raw_state"], r["readiness"], r["current_ceiling"], r["next_evidence"]) == (
            "UNKNOWN", "UNKNOWN", None, None)
        assert r["gap_codes"] == [] and r["selected_revision_ids"] == []
        assert [x["code"] for x in r["disclosure"]["reasons"]] == ["HISTORICAL_SELECTION_UNAVAILABLE", code]
        assert r["disclosure"]["window_assessment_revision_id"] is None
    other = rows[("KOBO-002", "GENERATOR_SUPPORT@2026-10-13")]  # other Sites still render
    assert (other["raw_state"], other["readiness"], other["selected_revision_ids"]) == ("LIMITED", "LIMITED", [A[1]])


def test_w302_evidence_w1_refusal_preserves_other_sites() -> None:
    sites = [SITES[0], site(MG2, "KOBO-002", "MINIGRID"), SITES[1], SITES[2]]
    body = get(client(FakeStore(RefusingSnapshot(MG, "UNSUPPORTED_RULE_VERSION", sites=sites))),
               {**WINDOW, "limit": 100}).json()
    by_site: dict = {}
    for r in body["rows"]:
        by_site.setdefault(r["site_code"], set()).add(r["raw_state"])
    assert by_site["KOBO-001"] == {"UNKNOWN"} and "LIMITED" in by_site["KOBO-002"]
    assert by_site["COLD 1"] != {"UNKNOWN"} and by_site["EV-1"] != {"UNKNOWN"}
    assert all(str(MG) not in g["site_ids"] for g in body["gaps"])


def _w1_days(spec):
    return [(date(2026, 10, 13 + n), projection(date(2026, 10, 13 + n), [
        interval(A[1 + n], state, evidence=[A[20]], reasons=reasons)], window=A[2 + n], currentness=current))
        for n, (state, reasons, current) in enumerate(spec)]


def test_w302_evidence_w1_unobserved_role_copy() -> None:
    days = _w1_days([("LIMITED", [{"code": "GENERATOR_UNOBSERVED", "role": "feeder_demand", "text": "x"},
                                  {"code": "GENERATOR_UNOBSERVED", "role": "generator_state", "text": "y"}],
                      "CURRENT")])
    body = get(client(FakeStore(FakeSnapshot(sites=[SITES[0]], days=days))), {**WINDOW, "limit": 100}).json()
    groups = {g["missing_role"]: g for g in body["gaps"] if g["gap_code"] == "GENERATOR_UNOBSERVED"}
    assert set(groups) == {"feeder_demand", "generator_state"}
    assert (groups["feeder_demand"]["label"], groups["feeder_demand"]["next_step"]) == (
        "Load (feeder demand) not observed", "Record Load (feeder demand)")
    assert (groups["generator_state"]["label"], groups["generator_state"]["next_step"]) == (
        "Generator state not observed", "Record generator state")
    assert evidence_money.w1_gap("GENERATOR_UNOBSERVED", "odd_role")["label"] == "odd_role not observed"


def test_w302_evidence_w1_interval_reasons_and_prior_selection() -> None:
    conflict = {"code": "CONFLICTING", "role": "battery_soc", "text": "SOC sources disagree"}
    days = _w1_days([("CONTRADICTORY", [conflict], "CURRENT"),
                     ("LIMITED", [{"code": "MISSING_ROLE", "role": "battery_soc", "text": "gone"}], "PENDING"),
                     ("LIMITED", [{"code": "MISSING_ROLE", "role": "pv_available_power", "text": "gone2"}],
                      "STALE")])
    body = get(client(FakeStore(FakeSnapshot(sites=[SITES[0]], days=days))), {**WINDOW, "limit": 100}).json()
    rows = {r["capability_key"][-2:]: r for r in body["rows"]}
    cur = rows["13"]
    assert conflict in cur["disclosure"]["reasons"] and conflict in cur["disclosure"]["constituents"][0]["reasons"]
    for day in ("14", "15"):
        r = rows[day]
        prior = r["disclosure"]["prior_selection"]
        assert prior["interval_ceilings"][0]["reasons"] and prior["reasons"] and r["gap_codes"] == []
        assert r["disclosure"]["constituents"][0]["reasons"] == prior["reasons"]
    assert [(g["gap_code"], g["missing_role"]) for g in body["gaps"]] == [("CONFLICTING", "battery_soc")]  # current day only


def test_w302_evidence_ev_full_token_citations(monkeypatch) -> None:
    """L1: the Site token cites the selected assessment's complete evidence IDs; a claimless row cites nothing."""
    seen = []
    real = evidence_money.selection_token
    monkeypatch.setattr(evidence_money, "selection_token", lambda *a: seen.append(a[-1]) or real(*a))
    snap = FakeSnapshot(sites=[SITES[2]])
    full = [A[30], A[45]]  # A[45]: a supporting-only citation no display claim carries
    snap.ev_capabilities = lambda p: {**FakeSnapshot.ev_capabilities(snap, p), "evidence_ids": full}
    body = get(client(FakeStore(snap)), {**WINDOW, "limit": 100}).json()
    display = {A[30 + n] for n in range(4)}  # ev_caps numbering: SESSION_OUTCOME..FAULT_ASSOCIATION
    assert seen[-1][0]["cited_accepted_evidence_ids"] == sorted({*display, A[45]})
    own = [tuple(c) for _, c, _ in snap.provenance_calls]  # a row's provenance stays its own constituents'
    assert (A[30],) in own and all(A[45] not in c for c in own)
    snap2 = FakeSnapshot(sites=[SITES[2]])  # claimless control: cites nothing, no all-window fallback
    snap2.ev_capabilities = lambda p: {**FakeSnapshot.ev_capabilities(snap2, p), "capabilities": []}
    get(client(FakeStore(snap2)), {**WINDOW, "limit": 100})
    assert all(c == [] for _, c, _ in snap2.provenance_calls) and seen[-1][0]["cited_accepted_evidence_ids"] == [A[30]]
    assert body["total_count"] == 4


def test_w302_evidence_live_cursor_summary_counts() -> None:
    first = get(client(FakeStore(FakeSnapshot())), {**WINDOW, "limit": 5}).json()
    later = FakeSnapshot()
    later.read_at = READ_AT + timedelta(hours=1)  # page two reads after the frozen cutoff
    page = get(client(FakeStore(later)), {**WINDOW, "limit": 5, "cursor": first["next_cursor"]}).json()
    assert page["status"] == "HISTORICAL"  # the presentation label (Run 8 ruling 2)
    assert first["summary"]["full_count"] is not None
    assert {k: v for k, v in page["summary"].items() if k != "as_of"} == first["summary"]
    old = get(client(FakeStore(FakeSnapshot(historical=True))), {**WINDOW, "known_at": "2026-10-20T06:00:00Z"}).json()
    assert old["summary"]["full_count"] is None  # an explicitly historical basis keeps the limit


def test_w302_evidence_composition_mount_no_db_503(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from assetops_backend.main import create_app
    response = TestClient(create_app()).get("/api/estate/evidence?" + urlencode(WINDOW))
    assert response.status_code in (401, 503)
    if response.status_code == 503:
        assert response.json()["detail"]["code"] == "ESTATE_STORE_UNAVAILABLE"
        assert response.json()["detail"]["gaps"] is None
