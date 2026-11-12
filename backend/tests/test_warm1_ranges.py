"""WARM-1 (rev 7 §7.1): the range enumeration, the throttle, the retry and degraded rules, `--verify`'s gate, and
the pre-build's HTTP mode. No database, no server."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import warm_ranges as wr  # noqa: E402

from assetops_backend.chain import prebuild  # noqa: E402

D = date.fromisoformat
SITES = {"KOBO-001": (D("2026-10-11"), D("2026-11-09")), "COLD-LAB-001": (D("2026-11-01"), D("2026-11-09")),
         "EV-LAB-001": (D("2026-10-20"), D("2026-11-03")), "KISIWA-001": (D("2026-10-30"), D("2026-11-08"))}


def test_presets_equal_the_frontend_cases():
    # frontend/src/shell/__tests__/sharedRange.test.tsx, NOW = 2026-10-07T10:00:00Z
    today = D("2026-10-07")
    assert {p: wr.preset_range(p, today) for p in wr.PRESETS} == {
        "yesterday": (D("2026-10-06"), D("2026-10-06")), "7d": (D("2026-09-30"), D("2026-10-06")),
        "30d": (D("2026-09-07"), D("2026-10-06")), "month": (D("2026-10-01"), D("2026-10-06")),
        "lastmonth": (D("2026-09-01"), D("2026-09-30"))}
    # "This month" on the 1st is the 1st alone; "Last month" in January is last December
    assert wr.preset_range("month", D("2026-11-01")) == (D("2026-11-01"), D("2026-11-01"))
    assert wr.preset_range("lastmonth", D("2027-01-15")) == (D("2026-12-01"), D("2026-12-31"))


def test_preset_query_is_the_bar_window_byte_for_byte():
    r = wr.Range("7d", *wr.preset_range("7d", D("2026-11-17")))
    assert r.window() == ("2026-11-10T00:00:00Z", "2026-11-17T00:00:00Z")
    portfolio, *_ = wr.range_requests(r, {})
    # URLSearchParams({from, to, limit}).toString(): ':' as %3A, `lens=all` left out (estateQueryString)
    assert portfolio.target == ("/api/estate/portfolio?from=2026-11-10T00%3A00%3A00Z&to=2026-11-17T00%3A00%3A00Z"
                                "&limit=50")


def test_windows_lie_inside_the_data_window_and_never_before_the_first_day():
    first, last = wr.data_window(SITES)
    assert (first, last) == (D("2026-10-11"), D("2026-11-09"))
    ws = wr.windows(first, last)
    assert all(first <= w.first and w.last <= last for w in ws)
    counts = {n: sum(1 for w in ws if w.days == n) for n in wr.LENGTHS}
    assert counts == {7: 24, 14: 17, 30: 1, 31: 0}
    assert ws[0].last == last and ws[0].days == 7  # newest first, shortest first
    assert all(a.last >= b.last for a, b in zip(ws, ws[1:]))


def test_presets_come_first_and_each_range_once():
    rs = wr.ranges(D("2026-11-10"), D("2026-10-11"), D("2026-11-09"))
    assert [r.name for r in rs[:5]] == list(wr.PRESETS)
    assert len({(r.first, r.last) for r in rs}) == len(rs)  # the 7d preset 11-03..11-09 is not listed twice


def test_requests_per_range_and_board_forms():
    r = wr.Range("14d", D("2026-10-27"), D("2026-11-09"))
    reqs = {q.target for q in wr.range_requests(r, SITES)}
    f, t = "from=2026-10-27T00%3A00%3A00Z", "to=2026-11-10T00%3A00%3A00Z"
    assert f"/api/estate/outcome-summary?{f}&{t}" in reqs
    assert f"/api/estate/findings?{f}&{t}" in reqs
    assert f"/api/estate/portfolio?{f}&{t}&lens=risks&limit=50" in reqs
    assert f"/api/sites/COLD-LAB-001/outcome-board?{f}&{t}" in reqs
    assert "/api/sites/KOBO-001/outcome-board?date=2026-11-09" in reqs  # miniBoardDay(to)
    assert len(reqs) == 10


def test_plan_dedupes_and_adds_mini_days_and_story():
    routes = {"requests": [{"id": "x", "path": "/api/estate/portfolio", "query": "from=a&to=b&lens=all"},
                           {"id": "dup", "path": "/api/sites/KOBO-001/outcome-board", "query": "date=2026-11-09"}]}
    rs, reqs = wr.plan(D("2026-11-17"), SITES, routes)
    keys = [(q.path, q.query) for q in reqs]
    assert len(keys) == len(set(keys))
    days = [q for q in reqs if q.path == "/api/sites/KISIWA-001/outcome-board"]
    assert {q.query for q in days} >= {f"date=2026-10-{d}" for d in (30, 31)}
    assert [q.id for q in reqs[-4:]] == ["story.x"] + [f"findings.{lens}.story:a..b" for lens in wr.PORTFOLIO_LENSES]


STORY = {"requests": [
    {"id": "portfolio.week", "path": "/api/estate/portfolio",
     "query": "from=2026-11-02T00%3A00%3A00Z&to=2026-11-09T00%3A00%3A00Z&lens=all"},
    {"id": "summary.week", "path": "/api/estate/outcome-summary",
     "query": "from=2026-11-02T00%3A00%3A00Z&to=2026-11-09T00%3A00%3A00Z"},
    {"id": "board.day:kobo:2026-11-08", "path": "/api/sites/KOBO-001/outcome-board", "query": "date=2026-11-08"}]}


def test_findings_lens_pages_for_presets_and_story_ranges_only():
    # D-WARM.5
    rs, reqs = wr.plan(D("2026-11-17"), SITES, STORY)
    lens = [q for q in reqs if q.path == "/api/estate/findings" and "lens=" in q.query]
    assert wr.story_windows(STORY) == [("2026-11-02T00:00:00Z", "2026-11-09T00:00:00Z")]
    assert len(lens) == 3 * (len(wr.PRESETS) + 1)
    assert ("/api/estate/findings?from=2026-11-10T00%3A00%3A00Z&to=2026-11-17T00%3A00%3A00Z&lens=cost"
            in {q.target for q in lens})  # the 7d preset on 17 Nov
    assert "/api/estate/findings?from=2026-11-02T00%3A00%3A00Z&to=2026-11-09T00%3A00%3A00Z&lens=opportunities" in {
        q.target for q in lens}
    window = wr.Range("14d", D("2026-10-27"), D("2026-11-09"))
    f, t = window.window()
    assert not any(f in q.query.replace("%3A", ":") and t in q.query.replace("%3A", ":") for q in lens)


def test_unstored_plan_covers_presets_and_story_ranges():
    # D-WARM.2: estate scope, actions, evidence, financials; each Site's Overview and Site Findings read
    reqs = wr.unstored_plan(D("2026-11-17"), SITES, STORY)
    # 6 windows x 12 reads, less the mini-grid Overviews four presets share (all end 16 Nov): 2 Sites x 3 repeats
    assert len(reqs) == (4 + 2 * len(SITES)) * (len(wr.PRESETS) + 1) - 2 * 3
    targets = {q.target for q in reqs}
    w = "from=2026-11-02T00%3A00%3A00Z&to=2026-11-09T00%3A00%3A00Z"
    assert {f"/api/estate/{n}?{w}" for n in ("scope", "actions", "evidence", "financials")} <= targets
    assert "/api/sites/KOBO-001/overview?date=2026-11-08" in targets  # miniBoardDay(to)
    assert f"/api/sites/COLD-LAB-001/cold/overview?{w}" in targets
    assert f"/api/sites/EV-LAB-001/ev/findings?{w}" in targets
    assert f"/api/sites/KISIWA-001/findings?{w}" in targets
    stored = {q.target for q in wr.plan(D("2026-11-17"), SITES, STORY)[1]}
    assert not targets & stored


def test_unstored_times_are_reported_but_never_gate():
    section = wr.unstored_section([wr.Result("u", "/api/estate/scope?x", 200, "none", 5400),
                                   wr.Result("v", "/api/estate/actions?x", 200, "none", 300)])
    assert section["gated"] is False and section["max_ms"] == 5400
    assert section["over_2s"] == [{"url": "/api/estate/scope?x", "ms": 5400}]
    assert wr.summarise([wr.Result("a", "/a", 200, "hit", 100)], verify=True, wall_s=0)["pass"] is True


def test_report_names_the_reason_per_failing_request():
    # D-WARM.6
    warm = wr.summarise([wr.Result("a", "/a", 200, "race", 10, attempts=4), wr.Result("b", "/b", 503, "unavailable", 1, 4),
                         wr.Result("c", "/c", 404, "none", 1)], verify=False, wall_s=0)
    assert warm["reasons"] == {"/a": "not stored after 4 attempts: race",
                               "/b": "degraded after 4 attempts: HTTP 503 unavailable", "/c": "failed: HTTP 404"}
    verify = wr.summarise([wr.Result("d", "/d", 200, "stored", 1), wr.Result("e", "/e", 200, "hit", 2500)],
                          verify=True, wall_s=0)
    assert verify["reasons"] == {"/d": "miss: stored", "/e": "over 2 s: 2500 ms"}


class Clock:
    def __init__(self, steps):
        self.steps = list(steps)

    def __call__(self):
        return self.steps.pop(0)


def test_retry_rule_2_5_10_and_still_degraded():
    answers = [(503, "unavailable"), (200, "stale"), (200, "stored")]
    waits: list[float] = []
    res = wr.send(wr.Req("a", "/p", "q=1"), lambda t: answers.pop(0), retry=True, sleep=waits.append)
    assert (res.status, res.state, res.attempts, waits) == (200, "stored", 3, [2, 5])
    waits.clear()
    res = wr.send(wr.Req("a", "/p", ""), lambda t: (503, "unavailable"), retry=True, sleep=waits.append)
    assert waits == [2, 5, 10] and res.attempts == 4
    report = wr.summarise([res], verify=False, wall_s=1.0)
    assert not report["pass"] and report["degraded"] == ["/p"]


def test_warm_counts_an_unstored_body_as_a_failure():
    res = wr.send(wr.Req("a", "/p", ""), lambda t: (200, "race"), retry=True, sleep=lambda s: None)
    assert res.attempts == 4
    assert wr.summarise([res], verify=False, wall_s=0)["pass"] is False
    ok = wr.send(wr.Req("a", "/p", ""), lambda t: (200, "hit"), retry=True, sleep=lambda s: None)
    assert ok.attempts == 1 and wr.summarise([ok], verify=False, wall_s=0)["pass"] is True


def test_verify_fails_on_one_miss_or_one_slow_request():
    hit = wr.Result("a", "/a", 200, "hit", 120)
    assert wr.summarise([hit, hit], verify=True, wall_s=0)["pass"] is True
    miss = wr.Result("b", "/b", 200, "stored", 90)
    report = wr.summarise([hit, miss], verify=True, wall_s=0)
    assert report["pass"] is False and report["misses"] == ["/b"]
    slow = wr.Result("c", "/c", 200, "hit", 2001)
    report = wr.summarise([hit, slow], verify=True, wall_s=0)
    assert report["pass"] is False and report["over_2s"] == ["/c"] and report["max_ms"] == 2001
    assert wr.summarise([wr.Result("d", "/d", 200, "hit", 2000)], verify=True, wall_s=0)["pass"] is True


def test_verify_sends_once_and_times_client_side():
    res = wr.send(wr.Req("a", "/p", ""), lambda t: (200, "stored"), retry=False, clock=Clock([10.0, 12.5]))
    assert res.attempts == 1 and res.ms == 2500


def test_throttle_waits_while_connections_above_150():
    seen = iter([180, 151, 150])
    waits: list[float] = []
    assert wr.throttle(lambda: next(seen), sleep=waits.append, say=lambda s: None) == 2
    assert waits == [wr.CONNECTION_WAIT_SECONDS] * 2
    assert wr.throttle(None) == 0
    assert wr.throttle(lambda: None, sleep=waits.append) == 0


def test_run_throttles_before_each_batch_and_keeps_order():
    calls: list[str] = []
    reqs = [wr.Req(str(i), f"/p{i}", "") for i in range(5)]
    counter = {"n": 0}

    def connections():
        counter["n"] += 1
        return 10

    out = wr.run(reqs, lambda t: (calls.append(t) or (200, "stored")), workers=2, verify=False,
                 connections=connections, say=lambda s: None)
    assert [r.id for r in out] == [str(i) for i in range(5)]
    assert counter["n"] == 3  # batches of 2: 2 + 2 + 1


def test_serve_ticks_over_http_then_starts_the_warm(tmp_path, monkeypatch):
    import urllib.request

    import demo_combined as dc

    state = {"polls": 0, "warm": [], "envs": []}

    class Api:
        pid = 1

        def poll(self):  # alive for the first tick, then gone
            state["polls"] += 1
            return None if state["polls"] <= 3 else 0

    monkeypatch.setattr(dc.subprocess, "Popen", lambda *a, **k: Api())
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: type("R", (), {"read": lambda s: b"ok"})())
    monkeypatch.setattr(dc, "_kill_tree", lambda pid: None)
    monkeypatch.setattr(dc, "prewarm", lambda *a: None)
    monkeypatch.setattr(dc.time, "sleep", lambda s: None)
    demo = object.__new__(dc.Demo)
    demo.work = demo.tree = tmp_path
    demo.story = lambda: {}
    demo.write_prebuilt_routes = lambda: None
    demo.links = lambda web: None
    demo.env = lambda keys=False: {}
    demo.tick = lambda times=1: state["envs"].append(dc.Demo.serve_env(demo).get(dc.PREBUILD_BASE_ENV))
    demo.start_warm = lambda port: state["warm"].append(port) or Api()
    demo.serve(8990, 5490)
    assert state["envs"] == ["http://127.0.0.1:8990"]  # the tick's prebuild env names the serve
    assert state["warm"] == [8990]
    assert dc.PREBUILD_BASE_ENV == prebuild.BASE_URL_ENV


def test_prebuild_http_mode_reads_status_and_header(monkeypatch):
    import io
    import urllib.error

    class Resp(io.BytesIO):
        status = 200
        headers = {"X-AssetOps-Stored": "stored"}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    from assetops_backend.chain.adapters.http_prebuild_client import HttpClient

    client = HttpClient("http://h:1/", opener=lambda url, timeout: Resp(b"{}"))
    response = client.get("/api/x?a=1")
    assert response.status_code == 200 and response.headers.get(prebuild.HEADER) == "stored"

    def refuse(url, timeout):
        raise urllib.error.HTTPError(url, 503, "x", {"X-AssetOps-Stored": "unavailable"}, None)

    response = HttpClient("http://h:1", opener=refuse).get("/api/x")
    assert response.status_code == 503 and prebuild._is_degraded(response)
    monkeypatch.delenv(prebuild.BASE_URL_ENV, raising=False)
    assert prebuild.http_client() is None
    monkeypatch.setenv(prebuild.BASE_URL_ENV, "http://127.0.0.1:8990")
    assert prebuild.http_client().base_url == "http://127.0.0.1:8990"
