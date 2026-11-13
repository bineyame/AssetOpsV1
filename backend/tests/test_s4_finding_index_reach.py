"""S4-04 slice review L1: the S3 Candidate edge reach covers BOTH UTC-day edges (no database)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from assetops_backend.analytics import dispatch as dispatch_contract
from assetops_backend.analytics.finding_index import candidate_reach, discover

UTC = timezone.utc
DAY = date(2026, 10, 12)


def read_with(start: str, end: str, cls: str = dispatch_contract.CANDIDATE) -> dict:
    return {"intervals": [{"result": {"segments": [{"classification": cls, "start": start, "end": end}]}}]}


def test_candidate_reach_reports_each_edge_independently() -> None:
    assert candidate_reach(read_with("2026-10-12T00:00:00Z", "2026-10-12T00:20:00Z"), DAY) == (True, False)
    assert candidate_reach(read_with("2026-10-12T23:40:00Z", "2026-10-13T00:00:00Z"), DAY) == (False, True)
    assert candidate_reach(read_with("2026-10-12T00:21:00Z", "2026-10-12T23:39:00Z"), DAY) == (False, False)
    assert candidate_reach(read_with("2026-10-12T00:00:00Z", "2026-10-12T00:20:00Z", "NOT_A_CANDIDATE"),
                           DAY) == (False, False)


def test_discover_grows_across_the_lower_and_the_upper_edge() -> None:
    lo, hi = datetime(2026, 10, 12, tzinfo=UTC), datetime(2026, 10, 13, tzinfo=UTC)
    low = read_with("2026-10-12T00:00:00Z", "2026-10-12T00:20:00Z")  # cluster 00:00-00:20 reaches the previous day
    up = read_with("2026-10-12T23:40:00Z", "2026-10-13T00:00:00Z")
    quiet = {"intervals": []}

    def reach(table):
        return lambda day: candidate_reach(table.get(day, quiet), day)

    assert discover([], lo, hi, edge_reach=reach({DAY: low})) == [date(2026, 10, 11), DAY]
    assert discover([], lo, hi, edge_reach=reach({DAY: up})) == [DAY, date(2026, 10, 13)]
    assert discover([], lo, hi, edge_reach=reach({})) == [DAY]


def test_a_cursor_request_is_never_stored_and_page_one_is() -> None:
    """D-SR.83 (Q11): only page 1 of the Finding index is a stored route; a cursor request composes."""
    import types
    from uuid import uuid4

    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.testclient import TestClient

    from assetops_backend import finding_index_api as api

    class Index:
        def read(self, *a, **k):
            return {"rows": []}

    class Store:
        def __init__(self) -> None:
            self.routes: list = []

        def serve(self, req, compose):
            self.routes.append(req)
            return JSONResponse(compose()[req.route])

    store = Store()
    t, s = uuid4(), uuid4()
    real = api.parse_request
    api.parse_request = lambda *a: types.SimpleNamespace()
    try:
        app = FastAPI()
        app.include_router(api.build_finding_index_router(Index(), {"K": ("K", t, s)}.get, gate=lambda c, t, s: (True, "r"),
                                                          responses=store))
        c = TestClient(app)
        base = "/api/sites/K/finding-index?domain=mini-grid-dispatch&from=2026-10-24T00:00:00Z&to=2026-10-25T00:00:00Z"
        assert c.get(base + "&limit=2").status_code == 200 and len(store.routes) == 1
        assert store.routes[0].request["limit"] == "2"
        assert c.get(base + "&cursor=abc").status_code == 200 and len(store.routes) == 1  # not stored
    finally:
        api.parse_request = real
