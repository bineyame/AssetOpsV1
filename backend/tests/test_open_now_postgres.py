"""OPEN-NOW: the Work list responses carry `open_now`, the open requests and incidents at the read's cutoff with no
date filter (`.agent/architect-sequence-client-scope-2026-11-11.md`, card OPEN-NOW; portfolio-layout proposal, Work
pages). The window decides the rows; it never decides `open_now`. The `known_at` cutoff and the Site scope do."""

from __future__ import annotations

from datetime import timedelta

import pytest

from test_s4_finding_store_postgres import URL, run_case  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s6_action_store_postgres import runner  # noqa: F401
    from test_w401_site_indexes_postgres import DAY, Lists, iso
    from test_w401_work_service_postgres import POSITIVE_NOW, Ctx, VirtualDbClock, event, incident, request
    from test_w601a_global_incidents import Api, seed

    from assetops_backend.work.open_now import open_now_line

# The incidents fixture of `test_w601a_global_incidents` occurs on 20 Oct; this window holds none of them.
NARROW = {"from": "2026-10-21T00:00:00Z", "to": "2026-10-22T00:00:00Z"}


def test_line_words() -> None:
    from assetops_backend.work.open_now import open_now_line as line

    assert line({"incidents": 0, "requests": 0}) == "Nothing open now"
    assert line({"incidents": 1, "requests": 3}) == "Open now: 1 incident, 3 requests, whatever the dates"
    assert line({"incidents": 2, "requests": 0}) == "Open now: 2 incidents, whatever the dates"
    assert line({"incidents": 0, "requests": 1}) == "Open now: 1 request, whatever the dates"


def test_site_open_now_ignores_the_window_and_obeys_known_at(runner) -> None:  # noqa: F811
    t, s = runner.tenant, runner.site
    ctx = Ctx(runner, VirtualDbClock(POSITIVE_NOW))
    try:
        _, a = ctx.case(incident("open-now-a", occurred_at="2026-10-06T10:00:00Z"))
        _, old = ctx.case(incident("open-now-old", occurred_at="2026-10-10T10:00:00Z"))  # outside every window read
        _, shut = ctx.case(incident("open-now-shut", occurred_at="2026-10-11T10:00:00Z"))
        _, r1 = ctx.case(request("open-now-r1", occurred_at="2026-10-12T08:00:00Z"))
        status, _ = ctx.event(shut["id"], event("CLOSE", {"reason": "Resolved"}, "open-now-close",
                                                  occurred_at="2026-10-11T12:00:00Z"))
        assert status in (200, 201), status
        k = POSITIVE_NOW + timedelta(seconds=4, microseconds=500_000)  # five commands, one tick each; before `late`
        _, late = ctx.case(request("open-now-late", occurred_at="2026-10-13T08:00:00Z"))
    finally:
        ctx.close()
    assert late["event"]["recorded_at"] > iso(k), late
    lists = Lists(POSITIVE_NOW + timedelta(minutes=5))
    empty_day = ("2026-10-01T00:00:00Z", "2026-10-02T00:00:00Z")
    try:
        day = lists.get(t, s, "incidents")
        nothing = lists.get(t, s, "incidents", empty_day)
        maint = lists.get(t, s, "maintenance", empty_day)
        at_k = lists.get(t, s, "maintenance", empty_day, known_at=iso(k))
        page_two = lists.get(t, s, "incidents", empty_day, limit="1")
    finally:
        lists.close()
    assert day["total_count"] == 1 and [r["case_id"] for r in day["rows"]] == [a["id"]]
    assert nothing["total_count"] == 0 and maint["total_count"] == 0  # the window holds nothing
    now = {"incidents": 2, "requests": 2, "line": "Open now: 2 incidents, 2 requests, whatever the dates"}
    for body in (day, nothing, maint, page_two):  # closed `shut` never counts; `old` counts at any window
        assert body["open_now"] == now, body["open_now"]
    assert old["id"] and r1["id"]
    assert at_k["open_now"] == {"incidents": 2, "requests": 1,
                                "line": "Open now: 2 incidents, 1 request, whatever the dates"}


def test_global_open_now_ignores_the_window_and_obeys_known_at(store, monkeypatch) -> None:  # noqa: F811
    from assetops_backend.work.global_index import CURSOR_KEY_ENV

    monkeypatch.setenv(CURSOR_KEY_ENV, "a1" * 32)
    info = seed("historical")
    demo = info["tenants"]["demo"]
    api, nobody = Api(demo), Api(demo, deny=("KOBO-001", "KOBO-002"))
    try:
        old_full = api.ok(known_at="2026-10-22T12:00:00Z")
        now_full = api.ok()
        old_narrow = api.ok(known_at="2026-10-22T12:00:00Z", **NARROW)
        now_narrow = api.ok(**NARROW)
        maintenance = api.client.get("/api/work/maintenance", params=NARROW).json()
        preventive = api.client.get("/api/work/preventive", params=NARROW).json()
        empty = nobody.ok(**NARROW)
    finally:
        api.close()
        nobody.close()
    assert old_narrow["total_count"] == 0 == now_narrow["total_count"]

    def opened(body: dict) -> int:
        return body["state_counts"]["OPEN"] + body["state_counts"]["IN_PROGRESS"]

    assert old_narrow["open_now"]["incidents"] == opened(old_full) == old_full["open_now"]["incidents"]
    assert now_narrow["open_now"]["incidents"] == opened(now_full) == now_full["open_now"]["incidents"]
    assert now_narrow["open_now"]["incidents"] > old_narrow["open_now"]["incidents"]  # the later case is open
    assert maintenance["open_now"] == now_narrow["open_now"]
    assert now_narrow["open_now"]["line"] == open_now_line(now_narrow["open_now"])
    assert "open_now" not in preventive
    assert empty["open_now"] == {"incidents": 0, "requests": 0, "line": "Nothing open now"}
