"""E4 D-E4.1 (C2), no database: `tools/demo_combined.prebuilt_routes` derives the pre-built route list from
`story_links`'s own rows (what is warmed is what the script opens) plus each Site's board for every date from S+1 to
its last added date, and the tool rewrites `<work>/prebuilt-routes.json` before every prebuild and at serve start."""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import demo_combined as tool  # noqa: E402

from assetops_backend.chain.prebuilt import parse  # noqa: E402

S = date(2026, 11, 7)
STORY = {"S": "2026-11-07T00:00:00Z", "S_date": "2026-11-07", "sites": ["kobo", "cold", "ev", "kisiwa"],
         "kisiwa": {"runs": [{"night_date": (S - timedelta(days=n)).isoformat()} for n in range(9, -1, -1)]}}
DAYS = [
    {"site": "kobo", "day": "2026-11-07", "offset": 0, "kind": "trial-before", "start": "x", "end": "y"},
    {"site": "kobo", "day": "2026-11-03", "offset": -4, "kind": "overuse", "start": "x", "end": "y"},
    {"site": "kobo", "day": "2026-11-08", "offset": 1, "kind": "trial-after", "start": "x", "end": "y"},
    {"site": "cold", "day": "2026-11-07", "offset": 0, "kind": "failure",
     "start": "2026-11-07T16:00:00Z", "end": "2026-11-07T17:05:00Z"},
    {"site": "cold", "day": "2026-11-04", "offset": -3, "kind": "degraded", "start": None, "end": None},
    {"site": "ev", "day": "2026-11-03", "offset": -4, "kind": "fault",
     "start": "2026-11-03T08:00:00Z", "end": "2026-11-03T09:00:00Z"},
]
KISIWA = {"action": {}, "finding": {}}
CODE_SITE = {v: k for k, v in tool.SITE_CODE.items()}


def _routes(last=None, days=DAYS):
    return tool.prebuilt_routes(STORY, days, KISIWA, last if last is not None else tool.sites_last_day(STORY, days, []))


def _board_dates(requests) -> set[tuple[str, str]]:
    out = set()
    for r in requests:
        if r["path"].endswith("/outcome-board"):
            q = dict(parse_qsl(r["query"]))
            out.add((CODE_SITE[r["path"].split("/")[3]], q.get("date") or q["from"][:10]))
    return out


def test_every_story_day_board_link_has_a_board_day_request_with_the_same_query() -> None:
    requests = _routes()
    by_key = {(r["path"], r["query"]): r for r in requests}
    links = tool.story_links(STORY, DAYS, None, 5490, KISIWA)
    boards = [(label, url) for label, url in links if " board" in label]
    assert len(boards) >= len(DAYS) + 2  # every story day, plus the two Kisiwa boards
    for label, url in boards:
        parts = urlsplit(url)
        code = parts.path.split("/")[2]
        key = (f"/api/sites/{code}/outcome-board", tool._api_query(parts.query))
        assert key in by_key, (label, url)
        assert by_key[key]["id"].startswith("board.day:"), by_key[key]
    # the frontend's encoding (`URLSearchParams`): `:` as `%3A`
    cold = by_key[("/api/sites/COLD-LAB-001/outcome-board", "from=2026-11-07T00%3A00%3A00Z&to=2026-11-08T00%3A00%3A00Z")]
    assert cold["id"] == "board.day:cold:2026-11-07"
    assert ("/api/sites/EV-LAB-001/outcome-board",
            "from=2026-11-03T00%3A00%3A00Z&to=2026-11-04T00%3A00%3A00Z") in by_key


def test_the_week_s_and_month_estate_requests() -> None:
    got = {r["id"]: (r["path"], r["query"]) for r in _routes()}
    week = "from=2026-11-01T00%3A00%3A00Z&to=2026-11-08T00%3A00%3A00Z"
    day_s = "from=2026-11-07T00%3A00%3A00Z&to=2026-11-08T00%3A00%3A00Z"
    month = "from=2026-10-10T00%3A00%3A00Z&to=2026-11-10T00%3A00%3A00Z"
    assert got["portfolio.week"] == ("/api/estate/portfolio", week + "&lens=all")
    assert got["summary.week"] == ("/api/estate/outcome-summary", week)
    assert got["findings.week"] == ("/api/estate/findings", week + "&lens=all&state=all")
    assert got["portfolio.S"] == ("/api/estate/portfolio", day_s + "&lens=all")
    assert got["summary.S"] == ("/api/estate/outcome-summary", day_s)
    assert got["portfolio.month"] == ("/api/estate/portfolio", month + "&lens=all")
    assert got["summary.month"] == ("/api/estate/outcome-summary", month)


def test_the_portfolio_lens_variants_are_prebuilt_for_week_s_and_month() -> None:
    """D-E5.23: the cost, risks and opportunities lens of each Portfolio window is a stored hit."""
    requests = _routes()
    got = {r["id"]: (r["path"], r["query"]) for r in requests}
    base = {"week": "from=2026-11-01T00%3A00%3A00Z&to=2026-11-08T00%3A00%3A00Z",
            "S": "from=2026-11-07T00%3A00%3A00Z&to=2026-11-08T00%3A00%3A00Z",
            "month": "from=2026-10-10T00%3A00%3A00Z&to=2026-11-10T00%3A00%3A00Z"}
    count = 0
    for name, q in base.items():
        for lens in ("cost", "risks", "opportunities"):
            assert got[f"portfolio.{name}.{lens}"] == ("/api/estate/portfolio", f"{q}&lens={lens}")
            count += 1
    assert count == 9
    keys = [(r["path"], r["query"]) for r in requests]
    assert len(keys) == len(set(keys))
    assert len({r["id"] for r in requests}) == len(requests)


def test_no_date_falls_outside_the_story_calendar_or_the_added_dates() -> None:
    last = {"kobo": date(2026, 11, 10), "cold": date(2026, 11, 9), "ev": None, "kisiwa": date(2026, 11, 8)}
    requests = _routes(last)
    story = {(d["site"], d["day"]) for d in DAYS} | {("kobo", "2026-11-07")}
    story |= {("kisiwa", (S - timedelta(days=5)).isoformat()), ("kisiwa", S.isoformat())}
    story |= {("kisiwa", (S + timedelta(days=1)).isoformat())}  # the Findings S-9d..S+1d link's warnings board
    added = {(site, (S + timedelta(days=n)).isoformat()) for site, hi in last.items() if hi
             for n in range(1, (hi - S).days + 1)}
    got = _board_dates(requests)
    # D-SR.83: Kobo and Kisiwa also get every day from the earliest story-link day (the date bar's start) to the last
    first = min(d for site, d in got if site == "kisiwa")
    span = {(site, (date.fromisoformat(first) + timedelta(days=n)).isoformat()) for site, hi in last.items()
            if hi and site in ("kobo", "kisiwa") for n in range((hi - date.fromisoformat(first)).days + 1)}
    assert got - story - added - span == set()
    assert added <= got  # every added date's board is warmed
    assert not any(site == "ev" and d > S.isoformat() for site, d in got)
    # Kobo and Kisiwa by `date`; Cold on the whole UTC day
    q = {(r["path"], r["query"]) for r in requests}
    assert ("/api/sites/KISIWA-001/outcome-board", "date=2026-11-08") in q
    assert ("/api/sites/KOBO-001/outcome-board", "date=2026-11-10") in q
    assert ("/api/sites/COLD-LAB-001/outcome-board",
            "from=2026-11-09T00%3A00%3A00Z&to=2026-11-10T00%3A00%3A00Z") in q
    assert len({(r["path"], r["query"]) for r in requests}) == len(requests)
    assert len({r["id"] for r in requests}) == len(requests)


def test_the_analysed_period_links_are_stored_hits_with_distinct_ids() -> None:
    """DATA-2: the Cold and EV analysed-period links map to board requests on their exact window."""
    requests = _routes()
    by_key = {(r["path"], r["query"]): r for r in requests}
    cold = by_key[("/api/sites/COLD-LAB-001/outcome-board", "from=2026-11-07T16%3A00%3A00Z&to=2026-11-07T17%3A05%3A00Z")]
    ev = by_key[("/api/sites/EV-LAB-001/outcome-board", "from=2026-11-03T08%3A00%3A00Z&to=2026-11-03T09%3A00%3A00Z")]
    assert cold["id"] == "board.day:cold:2026-11-07T16:00:00Z" and ev["id"].startswith("board.day:ev:")
    assert ("/api/sites/COLD-LAB-001/outcome-board",
            "from=2026-11-07T00%3A00%3A00Z&to=2026-11-08T00%3A00%3A00Z") in by_key  # the whole day stays
    assert len({r["id"] for r in requests}) == len(requests)


def test_a_site_findings_link_warms_the_board_its_warnings_panel_reads() -> None:
    """C2 review M1: the "KISIWA-001 Findings, story nights S-9d to S+1d" link (`to` = S+2d, a UTC midnight) opens a
    page whose warnings panel reads `/api/sites/KISIWA-001/outcome-board?date=miniBoardDay(to)` = S+1, even with no
    added Kisiwa night (`SiteAnalyticsFrames.tsx` `SiteEarlyWarnings`, `EarlyWarnings.tsx` `miniBoardDay`)."""
    q = {(r["path"], r["query"]) for r in _routes(last={})}
    assert ("/api/sites/KISIWA-001/outcome-board", "date=2026-11-08") in q
    assert tool._mini_board_day("2026-11-09T00:00:00Z") == "2026-11-08"
    assert tool._mini_board_day("2026-11-09T10:00:00Z") == "2026-11-09"
    assert tool._mini_board_day(None) is None


def test_a_cold_site_findings_link_warms_its_own_window(monkeypatch) -> None:
    """Cold and EV Findings pages read the board on the link's own window (`coldWindowFromParams`)."""
    monkeypatch.setattr(tool, "story_links", lambda *a, **k: [
        ("Cold findings", "http://localhost:0/sites/COLD-LAB-001/findings?from=2026-11-01T00:00:00Z"
                          "&to=2026-11-08T00:00:00Z")])
    requests = tool.prebuilt_routes({**STORY, "sites": ["cold"]}, [], None, {})
    assert ("/api/sites/COLD-LAB-001/outcome-board",
            "from=2026-11-01T00%3A00%3A00Z&to=2026-11-08T00%3A00%3A00Z") in {(r["path"], r["query"]) for r in requests}


def test_the_file_is_replaced_atomically(tmp_path) -> None:
    """C2 review L3: written to a temp file in the same folder, then `os.replace`d; no temp file is left."""
    demo = _demo(tmp_path)
    demo.write_prebuilt_routes()
    assert sorted(p.name for p in tmp_path.iterdir() if "prebuilt" in p.name) == [tool.PREBUILT_ROUTES_FILE]


def test_sites_last_day_reads_the_calendar_and_the_added_nights() -> None:
    nights = [{"night_date": "2026-11-08", "status": "DONE"}, {"night_date": "2026-11-09", "status": "PUBLISHED"},
              {"night_date": "2026-11-10", "status": "FAILED"}]
    last = tool.sites_last_day(STORY, DAYS, nights)
    assert last == {"kobo": date(2026, 11, 8), "cold": date(2026, 11, 7), "ev": date(2026, 11, 3),
                    "kisiwa": date(2026, 11, 9)}


def _demo(tmp_path):
    demo = tool.Demo("assetops_demo3_c2_test", "var/demo3_c2")
    demo.work, demo.tree = tmp_path, tmp_path / "tree"
    (tmp_path / "story.json").write_text(json.dumps(STORY), encoding="utf-8")
    (tmp_path / "days.json").write_text(json.dumps({"days": DAYS}), encoding="utf-8")
    (tmp_path / "kisiwa.json").write_text(json.dumps(KISIWA), encoding="utf-8")
    (tmp_path / "keys.json").write_text(json.dumps({}), encoding="utf-8")
    return demo


def test_the_file_is_rewritten_when_the_last_added_date_moves(tmp_path) -> None:
    demo = _demo(tmp_path)
    path = demo.write_prebuilt_routes()
    assert path == tmp_path / tool.PREBUILT_ROUTES_FILE
    first = json.loads(path.read_text(encoding="utf-8"))
    parse(first)  # the product's schema
    assert ("kobo", "2026-11-09") not in _board_dates(first["requests"])
    added = DAYS + [{"site": "kobo", "day": "2026-11-09", "offset": 2, "kind": "normal", "start": "x", "end": "y"}]
    (tmp_path / "days.json").write_text(json.dumps({"days": added}), encoding="utf-8")
    demo.write_prebuilt_routes()
    second = json.loads(path.read_text(encoding="utf-8"))
    assert ("kobo", "2026-11-09") in _board_dates(second["requests"])
    assert demo.serve_env()[tool.PREBUILT_ROUTES_ENV] == str(path)


def test_the_list_is_written_before_every_prebuild_and_at_serve_start(tmp_path, monkeypatch) -> None:
    demo = _demo(tmp_path)
    calls: list[tuple[str, bool]] = []

    def py(*argv, label="", serve_env=False, **kw):  # noqa: ARG001
        calls.append((label, (tmp_path / tool.PREBUILT_ROUTES_FILE).is_file()))

        class Done:
            stdout = "{}"
        return Done()

    monkeypatch.setattr(demo, "py", py)
    monkeypatch.setattr(demo, "read_site_mark", lambda site: None)  # E4-C4: no database; no mark means due
    demo.performance_and_prebuild()
    assert ("prebuild", True) in calls
    (tmp_path / tool.PREBUILT_ROUTES_FILE).unlink()

    (tmp_path / tool.Demo.EVIDENCE_TREE_MARK).write_text(str(demo.tree), encoding="utf-8")  # D-SR.67: comparison built here

    class Stop(Exception):
        pass

    def popen(*a, **kw):
        assert kw["env"][tool.PREBUILT_ROUTES_ENV] == str(tmp_path / tool.PREBUILT_ROUTES_FILE)
        raise Stop

    monkeypatch.setattr(tool.subprocess, "Popen", popen)
    try:
        demo.serve(1, 2)
    except Stop:
        pass
    assert (tmp_path / tool.PREBUILT_ROUTES_FILE).is_file()


def test_no_story_day_writes_nothing_and_sets_no_variable(tmp_path) -> None:
    demo = tool.Demo("assetops_demo3_c2_test", "var/demo3_c2")
    demo.work, demo.tree = tmp_path, tmp_path / "tree"
    (tmp_path / "story.json").write_text(json.dumps({"sites": ["kobo"]}), encoding="utf-8")
    (tmp_path / "keys.json").write_text(json.dumps({}), encoding="utf-8")
    assert demo.write_prebuilt_routes() is None
    assert tool.PREBUILT_ROUTES_ENV not in demo.serve_env()


# ---- D-SR.83: the Overview and the day Finding index over the date bar's whole span, and the estate scope ----

def _span_routes():
    first = tool.sites_first_day(STORY, DAYS, [])
    last = tool.sites_last_day(STORY, DAYS, [])
    return tool.prebuilt_routes(STORY, DAYS, KISIWA, last, first), first, last


def test_sites_first_day_is_the_earliest_core_day_and_kisiwas_first_night() -> None:
    first = tool.sites_first_day(STORY, DAYS, [{"night_date": "2026-10-20", "status": "DONE"}])
    assert first["kobo"] == date(2026, 11, 3) and first["cold"] == date(2026, 11, 4)
    assert first["kisiwa"] == date(2026, 10, 20)  # an added night earlier than the story's first run
    assert tool.sites_first_day(STORY, DAYS, [])["kisiwa"] == S - timedelta(days=9)


def test_overview_and_day_index_are_prebuilt_for_every_board_day_of_kobo_and_kisiwa() -> None:
    requests, first, last = _span_routes()
    by_id = {r["id"]: r for r in requests}
    for site in ("kobo", "kisiwa"):
        code = tool.SITE_CODE[site]
        d = first[site]
        assert d < S  # the span reaches back before S+1
        while d <= last[site]:
            iso = d.isoformat()
            assert by_id[f"board.day:{site}:{iso}"]["path"] == f"/api/sites/{code}/outcome-board"
            overview = by_id[f"overview.day:{site}:{iso}"]
            assert (overview["path"], overview["query"]) == (f"/api/sites/{code}/overview", f"date={iso}")
            index = by_id[f"index.day:{site}:{iso}"]
            nxt = (d + timedelta(days=1)).isoformat()
            assert index["path"] == f"/api/sites/{code}/finding-index"
            assert index["query"] == (f"domain=mini-grid-dispatch&from={iso}T00%3A00%3A00Z&"
                                      f"to={nxt}T00%3A00%3A00Z&limit=2")
            d += timedelta(days=1)
    assert not [i for i in by_id if i.startswith(("overview.", "index.")) and i.split(":")[1] in ("cold", "ev")]


def test_estate_scope_sits_beside_each_estate_findings_and_window_request() -> None:
    requests, _, _ = _span_routes()
    scopes = [r for r in requests if r["path"] == "/api/estate/scope"]
    assert {r["id"] for r in scopes} >= {"scope.week", "scope.S", "scope.month"}
    findings = next(r for r in requests if r["path"] == "/api/estate/findings")
    week = next(r for r in scopes if r["id"] == "scope.week")
    assert dict(parse_qsl(week["query"])) == {k: v for k, v in parse_qsl(findings["query"]) if k in ("from", "to")}


def test_each_site_findings_link_adds_its_finding_index_range() -> None:
    requests, _, _ = _span_routes()
    ranges = [r for r in requests if r["id"].startswith("index.range:")]
    assert ranges and all(r["path"].endswith("/finding-index") and "limit" not in r["query"] for r in ranges)
