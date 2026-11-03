"""QW-1 (design proposal §14b): per-read timing. No database.

`Reads` records names, call counts and elapsed time and never changes a return value or the failure handling; the
request recorder collects them; one `assetops.perf` line per request; the `Server-Timing` header only when
`ASSETOPS_SERVER_TIMING=1`."""
from __future__ import annotations

import json
import logging
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend import perf
from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
from assetops_backend.estate_portfolio_api import build_estate_portfolio_router
from assetops_backend.site_outcomes.mini import Reads

WINDOW = "from=2026-10-25T00:00:00Z&to=2026-11-01T00:00:00Z"


def slow(value, seconds=0.01):
    time.sleep(seconds)
    return value


def boom():
    raise RuntimeError("refused")


def test_reads_records_names_counts_and_time_without_changing_values() -> None:
    reads = Reads()
    body = {"a": 1}
    assert reads.call("one", slow, body) is body
    assert reads.call("one", slow, body) is body
    assert reads.call("two", lambda: None) is None
    assert reads.timings["one"][0] == 2 and reads.timings["one"][1] >= 15
    assert reads.timings["two"][0] == 1
    assert reads.failed == []


def test_reads_failure_handling_unchanged_and_still_timed() -> None:
    reads = Reads()
    assert reads.call("bad", boom) is None
    assert reads.call("bad", boom) is None
    assert reads.failed == ["bad"]
    assert reads.timings["bad"][0] == 2


def test_reads_pages_count_each_page() -> None:
    bodies = {None: {"rows": [1], "next_cursor": "c1"}, "c1": {"rows": [2], "next_cursor": None}}
    reads = Reads()
    assert reads.pages("paged", lambda cursor: bodies[cursor]) == [1, 2]
    assert reads.timings["paged"][0] == 2


def test_request_recorder_collects_reads_and_is_a_no_op_outside_a_request() -> None:
    Reads().call("outside", lambda: 1)  # no recorder: nothing raised, nothing kept
    with perf.request("/r") as rec:
        Reads().call("inside", lambda: 1)
        Reads().call("inside", boom)
        with perf.timed("section"):
            pass
    assert rec.timings["read.inside"][0] == 2
    assert rec.timings["section"][0] == 1
    assert "read.outside" not in rec.timings


def test_laps_record_each_section() -> None:
    with perf.request("/r") as rec:
        lap = perf.Laps("p")
        lap("a")
        time.sleep(0.005)
        lap("b")
    assert set(rec.timings) == {"p.a", "p.b"} and rec.timings["p.b"][1] >= 4


class _Service:
    def portfolio(self, tenant_id, req, admit):
        Reads().call("fake_read", lambda: 1)
        return {"rows": [], "total_count": 0}


def _client(monkeypatch) -> TestClient:
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "3e" * 32)
    app = FastAPI()
    app.include_router(build_estate_portfolio_router(_Service(), lambda: None, access=lambda request, code: None))
    return TestClient(app)


def test_one_structured_line_per_request_and_no_header_when_off(monkeypatch, caplog) -> None:
    monkeypatch.delenv(perf.SERVER_TIMING_ENV, raising=False)
    client = _client(monkeypatch)
    with caplog.at_level(logging.INFO, logger="assetops.perf"):
        response = client.get(f"/api/estate/portfolio?{WINDOW}")
    assert response.status_code == 200 and response.json() == {"rows": [], "total_count": 0}
    assert "server-timing" not in {k.lower() for k in response.headers}
    lines = [json.loads(r.getMessage()) for r in caplog.records if r.name == "assetops.perf"]
    assert len(lines) == 1
    assert lines[0]["route"] == "/api/estate/portfolio" and lines[0]["status"] == "ok"
    assert [t["name"] for t in lines[0]["timings"]] == ["read.fake_read"]


def test_header_present_only_when_the_setting_is_one(monkeypatch) -> None:
    client = _client(monkeypatch)
    monkeypatch.setenv(perf.SERVER_TIMING_ENV, "true")
    assert "server-timing" not in {k.lower() for k in client.get(f"/api/estate/portfolio?{WINDOW}").headers}
    monkeypatch.setenv(perf.SERVER_TIMING_ENV, "1")
    on = client.get(f"/api/estate/portfolio?{WINDOW}")
    off_body = on.json()
    assert on.headers["server-timing"].startswith("total;dur=")
    assert 'read.fake_read;dur=' in on.headers["server-timing"]
    assert off_body == {"rows": [], "total_count": 0}  # the body never changes


def test_refusal_is_logged_as_error_without_header(monkeypatch, caplog) -> None:
    monkeypatch.setenv(perf.SERVER_TIMING_ENV, "1")
    client = _client(monkeypatch)
    with caplog.at_level(logging.INFO, logger="assetops.perf"):
        response = client.get("/api/estate/portfolio?from=bad")
    assert response.status_code == 422
    assert "server-timing" not in {k.lower() for k in response.headers}
    lines = [json.loads(r.getMessage()) for r in caplog.records if r.name == "assetops.perf"]
    assert [x["status"] for x in lines] == ["error"]
