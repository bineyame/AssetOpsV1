"""WALK-perf F1-F3: the Performance gate runs only on a store miss (Overview, Site Finding index), the Finding
Financials is a stored route, the prebuild builds it after an Overview/index, and warm ranges follow a change."""
from __future__ import annotations

import sys
import types
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from assetops_backend import finding_index_api as index_api
from assetops_backend.chain import prebuild
from assetops_backend.finding_api import build_finding_router

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

T, S = uuid4(), uuid4()


class Store:
    """A fake ResponseStore: the first request per key composes, the same key again is a hit (no compose)."""

    def __init__(self) -> None:
        self.rows: dict = {}
        self.requests: list = []

    def serve(self, req, compose, if_none_match=None):
        self.requests.append(req)
        key = (req.route, repr(sorted(req.request.items())))
        if key in self.rows:
            return JSONResponse(self.rows[key], headers={"X-AssetOps-Stored": "hit"})
        body = compose()[req.route]  # a refusal raises here, before anything is stored
        self.rows[key] = body
        return JSONResponse(body, headers={"X-AssetOps-Stored": "stored"})


class Gate:
    def __init__(self, permitted=True) -> None:
        self.permitted, self.calls = permitted, 0

    def __call__(self, code, tenant_id, site_id):
        self.calls += 1
        return self.permitted, "comparison passed" if self.permitted else "lineage broken"


# ---- F1: Overview -------------------------------------------------------------------------------------------
def overview_client(store: Store, gate: Gate):
    from test_s5_overview_read import World, build_evidence_router, Imported, LegacySites, SiteOverviewRoute

    seen: list = []
    service = World().service()
    real = service.read

    def read(*a, **k):
        seen.append((k["source_open"], k["source_reason"]))
        return real(*a, **k)

    service.read = read
    route = SiteOverviewRoute(service, {"KOBO-001": ("KOBO-001", T, S)}.get, gate, lambda r, c: None, "DEV", responses=store)
    app = FastAPI()
    app.include_router(build_evidence_router(types.SimpleNamespace(store=None), LegacySites(),
                                             imported_reads=Imported(True), site_overview=route))
    return TestClient(app), seen


def test_overview_hit_skips_the_gate_and_a_miss_runs_it_once() -> None:
    store, gate = Store(), Gate()
    c, seen = overview_client(store, gate)
    url = "/api/sites/KOBO-001/overview?date=2026-10-24"
    assert c.get(url).status_code == 200 and gate.calls == 1
    assert seen == [(True, "comparison passed")]  # source_open and reason follow the gate
    assert c.get(url).headers["X-AssetOps-Stored"] == "hit" and gate.calls == 1


# ---- F1: Site Finding index ---------------------------------------------------------------------------------
def index_client(store: Store, gate: Gate):
    class Index:
        def read(self, *a, **k):
            return {"rows": [{"finding_id": "f", "finding_revision_id": "r"}]}

    real = index_api.parse_request
    index_api.parse_request = lambda *a: types.SimpleNamespace()
    app = FastAPI()
    app.include_router(index_api.build_finding_index_router(Index(), {"K": ("K", T, S)}.get, gate=gate, responses=store))
    return TestClient(app), real


def test_index_hit_skips_the_gate_and_a_closed_miss_is_409_and_not_stored() -> None:
    store, gate = Store(), Gate()
    c, real = index_client(store, gate)
    try:
        url = "/api/sites/K/finding-index?domain=mini-grid-dispatch&from=2026-10-24T00:00:00Z&to=2026-10-25T00:00:00Z&limit=2"
        first = c.get(url)
        assert first.status_code == 200 and gate.calls == 1 and first.json()["source_gate"]["permitted"] is True
        assert c.get(url).headers["X-AssetOps-Stored"] == "hit" and gate.calls == 1
        closed_store, closed = Store(), Gate(permitted=False)
        c2, _ = index_client(closed_store, closed)
        r = c2.get(url)
        assert r.status_code == 409 and r.json()["detail"]["code"] == "PERFORMANCE_CUTOVER_CLOSED"
        assert closed_store.rows == {}
    finally:
        index_api.parse_request = real


# ---- F2: Financials -----------------------------------------------------------------------------------------
class Reads:
    def __init__(self) -> None:
        self.calls = 0

    def finding(self, tenant_id, site_id, finding_id, revision_id=None, **page):
        self.calls += 1
        rid = str(revision_id or "r1")
        return {"selection": {"revision_id": rid, "revision_no": 1, "is_latest": True}, "finding": {"id": str(finding_id)},
                "relations": {"canonical_finding_id": "f1"},
                "revision": {"episode": {}, "title": "t", "lifecycle": "OPEN", "claim_level": "C", "assessments": [],
                             "currentness": {"windows": []}}}


def financials_client(store: Store | None, gate: Gate, reads: Reads) -> TestClient:
    app = FastAPI()
    app.include_router(build_finding_router(reads, {"KOBO-001": ("KOBO-001", T, S)}.get, (), gate=gate, responses=store))
    return TestClient(app)


def test_financials_is_stored_hit_skips_gate_and_reads_and_key_follows_finding_and_revision() -> None:
    store, gate, reads = Store(), Gate(), Reads()
    c = financials_client(store, gate, reads)
    f1, f2, rev = uuid4(), uuid4(), uuid4()
    url = f"/api/sites/KOBO-001/findings/{f1}/financials"
    first = c.get(url)
    assert first.status_code == 200 and first.headers["X-AssetOps-Stored"] == "stored"
    assert (gate.calls, reads.calls) == (1, 1)
    again = c.get(url)
    assert again.headers["X-AssetOps-Stored"] == "hit" and (gate.calls, reads.calls) == (1, 1)
    c.get(f"/api/sites/KOBO-001/findings/{f2}/financials")
    c.get(f"{url}?revision_id={rev}")
    keys = {repr(sorted(r.request.items())) for r in store.requests}
    assert len(keys) == 3 and (gate.calls, reads.calls) == (3, 3)


def test_financials_closed_gate_without_a_revision_is_409_and_not_stored() -> None:
    store, reads = Store(), Reads()
    c = financials_client(store, Gate(permitted=False), reads)
    r = c.get(f"/api/sites/KOBO-001/findings/{uuid4()}/financials")
    assert r.status_code == 409 and store.rows == {} and reads.calls == 0


def test_financials_without_a_store_composes_as_before() -> None:
    reads = Reads()
    r = financials_client(None, Gate(), reads).get(f"/api/sites/KOBO-001/findings/{uuid4()}/financials")
    assert r.status_code == 200 and "X-AssetOps-Stored" not in r.headers


# ---- F2: prebuild -------------------------------------------------------------------------------------------
class Resp:
    def __init__(self, body, status=200, stored="hit") -> None:
        self._b, self.status_code, self.headers = body, status, {"X-AssetOps-Stored": stored}

    def json(self):
        return self._b


def test_financials_paths_from_an_overview_and_an_index() -> None:
    ov = prebuild.financials_paths("/api/sites/KOBO-001/overview?date=2026-10-24",
                                   Resp({"known_finding": {"id": "f1", "revision_id": "r1"}}))
    assert ov == ["/api/sites/KOBO-001/findings/f1/financials?revision_id=r1"]
    ix = prebuild.financials_paths("/api/sites/KOBO-001/finding-index?domain=x&limit=2",
                                   Resp({"rows": [{"finding_id": "f1", "finding_revision_id": "r1"},
                                                  {"finding_id": "f2", "finding_revision_id": "r2"}]}))
    assert len(ix) == 2 and ix[1].endswith("/f2/financials?revision_id=r2")
    assert prebuild.financials_paths("/api/estate/portfolio?x=1", Resp({})) == []
    assert prebuild.financials_paths("/api/sites/K/overview?date=d", Resp({"known_finding": None})) == []


def test_prebuild_fetches_each_financials_once_with_the_infra1_retries(monkeypatch) -> None:
    ov, ix = "/api/sites/K/overview?date=d", "/api/sites/K/finding-index?limit=2"
    fin = {"f1": "/api/sites/K/findings/f1/financials?revision_id=r1", "f2": "/api/sites/K/findings/f2/financials?revision_id=r2"}
    bodies = {ov: {"known_finding": {"id": "f1", "revision_id": "r1"}},
              ix: {"rows": [{"finding_id": "f1", "finding_revision_id": "r1"}, {"finding_id": "f2", "finding_revision_id": "r2"}]}}
    gets: list[str] = []

    class Client:
        def get(self, path):
            gets.append(path)
            if path == fin["f2"] and gets.count(path) == 1:
                return Resp({}, status=503, stored="none")  # degraded once: retried
            return Resp(bodies.get(path, {}))

    from assetops_backend.chain.watermark import SERVE_KEYS

    class Rows:
        def prune(self):
            return 0

        def dispose(self):
            pass

        def connections(self):
            return 1

    monkeypatch.setenv("ASSETOPS_RESPONSE_STORE", "on")
    for k in SERVE_KEYS:
        monkeypatch.setenv(k, "x")
    monkeypatch.setattr(prebuild, "build_response_store", lambda url: Rows())
    monkeypatch.setattr(prebuild, "paths", lambda: [ov, ix])
    monkeypatch.setattr(prebuild, "_sleep", lambda s: None)
    out = prebuild.run("postgresql://x", Client())
    assert gets.count(fin["f1"]) == 1 and gets.count(fin["f2"]) == 2  # overlap built once; f2 retried
    assert out["requests"] == 2 + 1 + 2 and out["degraded"] == {fin["f2"]: 2}


# ---- F3 ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("states,last,now,due", [
    ({"hit": 5}, None, 100.0, True),          # first tick
    ({"hit": 5}, 100.0, 200.0, False),        # nothing changed
    ({"hit": 4, "stored": 1}, 100.0, 200.0, True),
    ({"hit": 5}, 100.0, 100.0 + 1800, True),  # 30 minutes
    ({"hit": 5}, 100.0, 100.0 + 1799, False),
    (None, 100.0, 200.0, True),               # unknown states: warm
    ({}, 100.0, 200.0, False),
])
def test_warm_due(states, last, now, due) -> None:
    from demo_combined import warm_due

    assert warm_due(states, last, now) is due
