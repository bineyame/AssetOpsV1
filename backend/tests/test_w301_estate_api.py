"""W3-01 commit 2: estate router refusals, the strict parser, empty-scope zeros, the `estate-selection/2` token and
the pure per-Site reductions (mini-grid gates, Action reduce) over a fake one-transaction snapshot. No database."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.estate import coverage
from assetops_backend.estate.index import EstateIndexService
from assetops_backend.estate.scope import (
    EstateSelectionInconsistent, EstateStoreUnavailable, decode_cursor, encode_cursor, selection_token)
from assetops_backend.estate_api import build_estate_router
from assetops_backend.evidence.public_provenance import basis_sha256

T = UUID("10000000-0000-4000-8000-000000000001")
S = UUID("10000000-0000-4000-8000-000000000011")
READ_AT = datetime(2026, 10, 7, tzinfo=timezone.utc)
DAY = {"from": "2026-10-06T00:00:00Z", "to": "2026-10-07T00:00:00Z"}
D0, D1 = datetime(2026, 10, 6, tzinfo=timezone.utc), datetime(2026, 10, 7, tzinfo=timezone.utc)


class FakeSnapshot:
    def __init__(self, sites=(), **reads) -> None:
        self.read_at, self.historical, self._sites, self.reads = READ_AT, False, list(sites), reads
        self.continuation = self.basis_historical = False

    def imported_sites(self, t, to):
        return self._sites

    def __getattr__(self, name):
        return self.reads[name]


class FakeStore:
    def __init__(self, *outcomes) -> None:
        self.outcomes, self.calls = list(outcomes), 0

    def read(self, work):
        self.calls += 1
        outcome = self.outcomes[min(self.calls, len(self.outcomes)) - 1]
        if isinstance(outcome, BaseException):
            raise outcome
        return work(outcome)


def client(store, tenant=T, authenticate=lambda request: None, service=True):
    app = FastAPI()
    app.include_router(build_estate_router(EstateIndexService(store) if service else None, lambda: tenant,
                                           authenticate=authenticate))
    return TestClient(app)


def call(c, root, query) -> tuple[int, str | None]:
    response = c.get(f"/api/estate/{root}?" + (query if isinstance(query, str) else urlencode(query)))
    body = response.json()
    return response.status_code, body["detail"]["code"] if response.status_code != 200 else None


def test_401_409_422_503_refusals() -> None:
    store = FakeStore(FakeSnapshot())
    unauthenticated = client(store, authenticate=lambda request: 401)
    response = unauthenticated.get("/api/estate/findings?from=bad&lens=nope")
    assert response.status_code == 401 and response.headers["www-authenticate"] == "Bearer"
    assert response.json()["detail"] == {"code": "UNAUTHENTICATED", "message": "Sign in to read estate records.",
                                         "rows": None, "total_count": None}
    assert store.calls == 0  # no tenant lookup, Site enumeration or parse before 401
    c = client(store)
    window = "from=2026-10-06T00:00:00Z&to=2026-10-07T00:00:00Z"
    for root, query, code in [
        ("findings", "to=2026-10-07T00:00:00Z", "INVALID_WINDOW"),
        ("findings", window + "&to=2026-10-07T00:00:00Z", "INVALID_WINDOW"),
        ("findings", "from=2026-10-06T01:00:00Z&to=2026-10-07T00:00:00Z", "INVALID_WINDOW"),
        ("findings", "from=2026-10-07T00:00:00Z&to=2026-10-06T00:00:00Z", "INVALID_WINDOW"),
        ("findings", "from=2026-09-01T00:00:00Z&to=2026-10-03T00:00:00Z", "INVALID_WINDOW"),
        ("findings", "from=2026-10-06T00:00:00+03:00&to=2026-10-07T00:00:00Z", "INVALID_WINDOW"),
        ("findings", window + "&known_at=2026-10-06T10:00:00", "INVALID_KNOWN_AT"),
        ("findings", window + "&known_at=2026-10-08T00:00:00Z", "INVALID_KNOWN_AT"),
        ("findings", window + "&lens=priced", "INVALID_LENS"),
        ("findings", window + "&state=open", "INVALID_LENS"),
        ("findings", window + "&limit=0", "INVALID_LIMIT"),
        ("findings", window + "&limit=101", "INVALID_LIMIT"),
        ("findings", window + "&limit=x", "INVALID_LIMIT"),
        ("findings", window + "&site=KOBO-001", "INVALID_CURSOR"),
        ("findings", window + "&lens=all&lens=cost", "INVALID_CURSOR"),
        ("findings", window + "&cursor=not-a-cursor", "INVALID_CURSOR"),
        ("actions", window + "&lens=all", "INVALID_CURSOR"),
        ("scope", window + "&limit=5", "INVALID_CURSOR"),
    ]:
        assert call(c, root, query) == (422 if code != "ESTATE_BASIS_CHANGED" else 409, code), (root, query)
    assert call(client(store, service=False), "findings", window) == (503, "ESTATE_STORE_UNAVAILABLE")
    assert call(client(FakeStore(EstateStoreUnavailable("down"))), "actions", window) == (
        503, "ESTATE_STORE_UNAVAILABLE")
    twice = FakeStore(EstateSelectionInconsistent("pin"))
    assert call(client(twice), "findings", window) == (409, "ESTATE_SELECTION_INCONSISTENT") and twice.calls == 2
    once = FakeStore(EstateSelectionInconsistent("pin"), FakeSnapshot())
    assert call(client(once), "findings", window) == (200, None) and once.calls == 2


def test_empty_is_zero_only_after_complete_read() -> None:
    for tenant in (T, None):
        c = client(FakeStore(FakeSnapshot()), tenant=tenant)
        findings = c.get("/api/estate/findings?" + urlencode(DAY)).json()
        assert findings["schema_version"] == "estate-finding-index-2"  # Run 8 ruling 3: Finding wire v2
        assert findings["coverage"] == {"state": "COMPLETE", "sites": []} and findings["status"] == "CURRENT"
        assert findings["rows"] == [] and findings["total_count"] == 0
        assert findings["summary"] == {"high_priority": None, "low_confidence": None, "awaiting_verification": 0,
                                       "basis_count": 0, "supported_findings": 0}
        actions = c.get("/api/estate/actions?" + urlencode(DAY)).json()
        assert actions["summary"] == {"open_actions": 0, "due_overdue": None, "verification_window": 0,
                                      "verified_in_30_days": 0, "basis_count": 0}
        assert findings["window"] == {"from": DAY["from"], "to": DAY["to"], "bounds": "[from, to)",
                                      "known_at": "2026-10-07T00:00:00Z"}
    site = {"site_id": S, "site_code": "KOBO-001", "site_name": "Kobo", "site_type": "MINIGRID"}
    missing = FakeSnapshot([site], evidence_cutoff=lambda *a: None, dispatch_days=lambda *a: [
        {"day": "2026-10-06", "available": True, "selection": None, "jobs": [], "status": None}],
        finding_index=lambda *a: {"heads": [], "match_pass": None, "deferred_windows": []})
    body = client(FakeStore(missing)).get("/api/estate/findings?" + urlencode(DAY)).json()
    assert body["coverage"]["state"] == "UNKNOWN" and body["status"] == "UNKNOWN"
    assert body["total_count"] is None and all(v is None for v in body["summary"].values())
    assert body["coverage"]["sites"] == [{"site_id": str(S), "state": "UNKNOWN", "committed_watermark": None,
                                          "selection_id": None, "match_state": "MISSING", "job_state": "NONE",
                                          "source_freshness": "UNKNOWN"}]


def test_selection_token_v2_endpoint_cursor_compatibility() -> None:
    site = {"site_id": S, "domain": "actions", "selection_id": None, "watermark": None,
            "match_state": "NOT_APPLICABLE", "job_state": "NOT_APPLICABLE", "source_freshness": "NOT_APPLICABLE"}
    token = selection_token(T, [S], D0, D1, READ_AT, None, None, [site])
    canonical = {"version": "estate-selection/2", "tenant_id": str(T), "authorized_site_ids": [str(S)],
                 "from": "2026-10-06T00:00:00.000000Z", "to": "2026-10-07T00:00:00.000000Z",
                 "known_at": "2026-10-07T00:00:00.000000Z", "lens": None, "state_filter": None,
                 "sites": [{**{k: v for k, v in site.items()}, "site_id": str(S),
                            **{key: [] for key in ("selected_finding_revision_ids", "selected_action_event_ids",
                                                   "selected_assessment_revision_ids",
                                                   "selected_consequence_revision_ids",
                                                   "selected_assumption_revision_ids",
                                                   "cited_accepted_evidence_ids")}}]}
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert token == "sha256:" + hashlib.sha256(raw).hexdigest()  # empty arrays are literal []
    cited = selection_token(T, [S], D0, D1, READ_AT, None, None,
                            [{**site, "cited_accepted_evidence_ids": ["00000001-0000-4000-8000-00000000014c"]}])
    assert cited != token  # a changed citation changes the full-set token
    # W20 D3 empty-citation Action digest literal (selected IDs: action, event, origin revision, basis, Foundation).
    ids = [f"10000000-0000-4000-8000-000000000{n}" for n in (201, 202, 102, 203, 204)]
    assert basis_sha256(T, S, ids, []) == (
        "sha256:ed86298acb47897962bf2baa31e72a852723b994b43134f3eab8546742fe3e85")
    # Cursors: a findings cursor is not an actions cursor and vice versa; a scope root takes none.
    payload = {"v": 1, "tenant_id": str(T), "authorized_site_ids": [str(S)], "access_basis": "sha256:x",
               "from": DAY["from"], "to": DAY["to"], "known_at": "2026-10-07T00:00:00.000000Z", "lens": "all",
               "state_filter": "all", "selection_token": token, "after": ["2026-10-06T10:00:00.000000Z", "id"], "page_one_mode": "live"}
    assert decode_cursor("findings", encode_cursor(payload)) == payload
    for kind, body in (("actions", payload), ("scope", payload)):
        with pytest.raises(Exception, match="INVALID_CURSOR"):
            decode_cursor(kind, encode_cursor(body))


def head(fid: str, frid: str, lifecycle: str = "SUPPORTED") -> dict:
    return {"finding_id": fid, "finding_revision_id": frid, "merged_into_finding_id": None, "lifecycle": lifecycle,
            "title": "t", "episode_start": D0 + timedelta(hours=2), "episode_end": None}


def mini_grid(days, *, consequence=None, eligible="ELIGIBLE", gate="AUTHORED_DEMONSTRATION", matched=5):
    fid, frid = "10000000-0000-4000-8000-000000000101", "10000000-0000-4000-8000-000000000102"
    return FakeSnapshot(
        evidence_cutoff=lambda *a: D0, dispatch_days=lambda *a: days,
        finding_index=lambda *a: {"heads": [head(fid, frid)], "deferred_windows": [],
                                  "match_pass": {"matched_through_selection_seq": matched}},
        finding_lineage=lambda *a: {"evidence": [{"finding_revision_id": frid, "evidence_id": "e1"}],
                                    "assessments": [{"assessment_revision_id": "a1"}]},
        finding_provenance=lambda *a: {"state": "AUTHORED_DEMONSTRATION"},
        consequence=lambda *a: consequence or {"consequence_revision_id": None},
        consequence_provenance=lambda *a: {"classification": gate, "state": gate, "source_ids": [],
                                           "evidence_ids": [], "basis_sha256": "sha256:c", "reasons": []},
        eligibility=lambda *a: {"state": eligible})


def day(seq=5, status="CURRENT", available=True, jobs=()) -> dict:
    return {"available": available, "selection": {"seq": seq}, "status": status, "jobs": list(jobs),
            "window_start": D0, "assessment_revision_ids": ["a0"], "window_assessment_revision_id": "w0"}


PRICED = {"consequence_revision_id": "c1", "consequence_state": "PRICED", "currentness": {"state": "CURRENT"},
          "amount_low": "10.00", "amount_high": "12.50", "currency": "USD",
          "cited": {"assumption_revision_ids": ["p1"], "power_evidence_ids": ["e2"]}}


def test_mini_grid_currentness_rows_and_money_gates() -> None:
    cov = coverage.site_coverage(mini_grid([day()], consequence=PRICED), T, S, "mini_grid", D0, D1, READ_AT)
    assert (cov["state"], cov["match_state"], cov["job_state"], cov["source_freshness"]) == (
        "CURRENT", "COMPLETE", "SETTLED", "RECENT")
    (row,) = cov["rows"]
    assert row["consequence"] == {"state": "PRICED", "amount": "10.00", "amount_low": "10.00",
                                  "amount_high": "12.50", "currency": "USD", "source_revision_id": "c1"}
    assert cov["selected_consequence_revision_ids"] == ["c1"] and cov["selected_assumption_revision_ids"] == ["p1"]
    assert cov["cited_accepted_evidence_ids"] == ["e1", "e2"] and set(cov["selected_assessment_revision_ids"]) == {
        "a0", "a1", "w0"}
    for snap in (mini_grid([day()], consequence=PRICED, eligible="PENDING_REASSESSMENT"),
                 mini_grid([day()], consequence=PRICED, gate="MIXED"),
                 mini_grid([day()], consequence={**PRICED, "currentness": {"state": "STALE"}})):
        (row,) = coverage.site_coverage(snap, T, S, "mini_grid", D0, D1, READ_AT)["rows"]
        assert row["consequence"] == {"state": "UNKNOWN", "amount": None,
                                      "amount_low": None, "amount_high": None, "currency": None,
                                      "source_revision_id": "c1"}
    (row,) = coverage.site_coverage(mini_grid([day()], consequence={**PRICED, "consequence_state": "UNPRICED"}),
                                    T, S, "mini_grid", D0, D1, READ_AT)["rows"]
    assert row["consequence"]["state"] == "UNPRICED" and row["consequence"]["source_revision_id"] == "c1"
    (row,) = coverage.site_coverage(mini_grid([day()]), T, S, "mini_grid", D0, D1, READ_AT)["rows"]
    assert row["consequence"] == {"state": "UNPRICED", "amount": None,
                                  "amount_low": None, "amount_high": None, "currency": None,
                                  "source_revision_id": None}
    historical = mini_grid([day(jobs=[{"status": "PENDING"}])], consequence=PRICED)
    historical.historical = historical.basis_historical = True
    cov = coverage.site_coverage(historical, T, S, "mini_grid", D0, D1, D0 + timedelta(hours=20))
    assert cov["state"] == "HISTORICAL" and cov["job_state"] == "PENDING"  # the marker does not demote
    assert cov["rows"][0]["consequence"]["state"] == "UNKNOWN"  # a prior amount is never a current-money claim
    for days, state in (([day(seq=6)], "PENDING_RECOMPUTE"), ([day(status="PENDING")], "PENDING_RECOMPUTE"),
                        ([day(status="STALE_PROJECTION")], "STALE_SOURCE"), ([day(available=False)], "UNKNOWN"),
                        ([day(), {**day(), "selection": None}], "UNKNOWN")):
        cov = coverage.site_coverage(mini_grid(days), T, S, "mini_grid", D0, D1, READ_AT)
        assert cov["state"] == state and cov["rows"] == [], days  # reading 6: no rows from an unsettled Site


def test_action_reduce_and_verification_counts() -> None:
    def event(aid, n, kind, hours, **extra):
        return {"id": f"{aid}-e{n}", "action_id": aid, "kind": kind, "recorded_at": D0 + timedelta(hours=hours),
                **extra}

    k = D0 + timedelta(hours=20)
    actions = [{"id": a, "action_code": f"ACT-00000{i}", "created_at": D0 + timedelta(hours=i),
                "origin_finding_id": "f", "origin_finding_revision_id": "fr"} for i, a in enumerate("abcd", 1)]
    events = [event("a", 1, "ACCEPTED", 1), event("b", 1, "ACCEPTED", 2), event("b", 2, "APPLIED", 3),
              event("c", 1, "ACCEPTED", 3), event("c", 2, "APPLIED", 4),
              event("c", 3, "RESOLVED", 5, verification_outcome_id="o1", payload={"outcome": "VERIFIED"})]
    snap = FakeSnapshot(
        actions=lambda *a: {"actions": actions, "events": events},
        action_basis=lambda t, s, ids: {str(i): {"primary": "p", "foundation": "fd", "assessments": ["b1"],
                                                  "evidence": [], "origin_evidence": []} for i in ids},
        verification=lambda *a: {"b": {"plans": [{"later_start": D0, "later_end": D1}], "outcomes": {}},
                                 "c": {"plans": [{"later_start": D0, "later_end": D1}],
                                       "outcomes": {"o1": D0 + timedelta(hours=5)}}},
        cited_provenance=lambda t, s, cited, selected: {"selected": sorted(selected), "cited": cited})
    cov = coverage.site_coverage(snap, T, S, "actions", D0, D1, k)
    rows = {r["action_id"]: r for r in cov["rows"]}
    assert set(rows) == {"a", "b", "c"}  # `d` has no event by the cutoff: no row
    assert [rows[x]["application_state"] for x in "abc"] == ["PENDING", "APPLIED", "APPLIED"]
    assert rows["c"]["resolution_state"] == "RESOLVED" and rows["c"]["verification_outcome"] == "VERIFIED"
    assert [x for x in "abc" if rows[x]["_open"]] == ["a", "b"]
    assert [x for x in "abc" if rows[x]["_verification_window"]] == ["b"]
    assert [x for x in "abc" if rows[x]["_verified_recent"]] == ["c"]
    assert rows["a"]["action_title"] == "Action ACT-000001" and rows["a"]["success_criterion"] is None
    assert rows["a"]["source_provenance"]["selected"] == sorted(["a", "a-e1", "fr", "p", "fd", "b1"])
    assert cov["selected_action_event_ids"] == ["a-e1", "b-e2", "c-e3"] and cov["state"] == "CURRENT"


# --- c2 r1 L1: a link-reader failure is not a selected-lineage conflict ---------------------------------------------

class _Result:
    def __init__(self, value) -> None:
        self.value = value

    def scalar_one(self):
        return self.value


class _Conn:
    def execution_options(self, **_):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def begin(self):
        return self

    def execute(self, *_a, **_k):
        return _Result(READ_AT)


class _Engine:
    def connect(self):
        return _Conn()


def _real_read(raises) -> object:
    """The real `PostgresEstateRead.read` seam over a fake connection, wired as `composition` wires it."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import SelectionPinRefused, _bound_link_rows
    from assetops_backend.analytics.cold_reads import ColdPinnedLineageUnavailable, ColdReadUnavailable
    from assetops_backend.analytics.ev_reads import EvPinnedLineageUnavailable, EvReadUnavailable
    from assetops_backend.estate.adapters.postgres_estate_read import PostgresEstateRead

    store = PostgresEstateRead(
        None, findings=None, assessments=None, actions=None, consequences=None, eligibility=None, cold=None, ev=None,
        provenance_reads=lambda c: None,
        inconsistent=(ColdPinnedLineageUnavailable, EvPinnedLineageUnavailable, SelectionPinRefused),
        unavailable=(ColdReadUnavailable, EvReadUnavailable), engine=_Engine())
    calls = {"n": 0}

    class Service(EstateIndexService):
        def _findings(self, snap, tenant_id, req, admit):
            calls["n"] += 1
            return raises(_bound_link_rows)

    return TestClient(_router(Service(store)), raise_server_exceptions=False), calls


def _router(service):
    app = FastAPI()
    app.include_router(build_estate_router(service, lambda: T, authenticate=lambda request: None))
    return app


def _get(c):
    response = c.get("/api/estate/findings?" + urlencode(DAY))
    if response.status_code in (200, 500):
        return response.status_code, None
    return response.status_code, response.json()["detail"]["code"]


def test_link_reader_programming_error_is_not_selection_409() -> None:
    def fail(bound):
        def link_rows(c, t, s, ids):
            raise TypeError("a programming error in the link reader")
        return bound(None, link_rows, Exception)(T, S, ["x"])

    c, calls = _real_read(fail)
    assert _get(c)[0] == 500 and calls["n"] == 1  # never retried, never a selection conflict


def test_typed_lineage_refusal_retries_once_then_409() -> None:
    from assetops_backend.analytics.cold_reads import ColdPinnedLineageUnavailable
    from assetops_backend.analytics.ev_reads import EvPinnedLineageUnavailable

    for error in (ColdPinnedLineageUnavailable, EvPinnedLineageUnavailable):
        def fail(bound, error=error):
            raise error("a pinned lineage cannot be read")
        c, calls = _real_read(fail)
        assert _get(c) == (409, "ESTATE_SELECTION_INCONSISTENT") and calls["n"] == 2


def test_absent_link_reader_and_broad_unavailable_are_503() -> None:
    from assetops_backend.analytics.cold_reads import ColdReadUnavailable
    from assetops_backend.analytics.ev_reads import EvReadUnavailable

    for error in (ColdReadUnavailable, EvReadUnavailable):
        def fail(bound, error=error):
            raise error("The source provenance reader is not wired.")
        c, calls = _real_read(fail)
        assert _get(c)[0] == 503 and calls["n"] == 1
