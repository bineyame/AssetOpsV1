"""D-SR.83b review M1: the watermark guard's per-route exemption (`route_terms`) never excuses another route."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import chain_watermark_guard as guard  # noqa: E402

HEADS = {"schedule_tick_head", "schedule_site_head"}


def test_route_terms_matches_the_overview_path_only() -> None:
    assert guard.route_terms("/api/sites/KOBO-001/overview") == HEADS
    for other in ("/api/sites/KOBO-001/outcome-board", "/api/estate/scope", "/api/sites/KOBO-001/finding-index",
                  "/a/b/overview", "/api/sites/A/B/overview"):
        assert guard.route_terms(other) == set(), other
    assert guard.route_terms(None) == set()  # no route, no exemption
    assert guard.all_route_terms() == HEADS


def test_one_routes_exemption_does_not_pass_the_overall_verdict_of_another() -> None:
    ok = {"ok": True}
    assert guard.overall({"/a": ok, "/b": ok}, {"ok": True}) is True
    assert guard.overall({"/a": ok, "/b": {"ok": False}}, {"ok": True}) is False
    assert guard.overall({"/a": ok}, {"ok": False}) is False


URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
if URL:
    from test_s1_bindings_postgres import engine  # noqa: F401


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set")
def test_a_non_exempt_route_reading_a_head_table_fails_the_overall_verdict(engine) -> None:  # noqa: F811
    sql = ["SELECT * FROM schedule_tick_head"]
    with engine.connect() as c:
        overview = guard.check(c, sql, "/api/sites/KOBO-001/overview")
        board = guard.check(c, sql, "/api/sites/KOBO-001/outcome-board")
        total = guard.check(c, sql + sql, exempt=guard.all_route_terms())
    assert overview["ok"] is True and board["ok"] is False and "schedule_tick_head" in board["untracked"]
    assert total["ok"] is True  # the union alone would pass...
    assert guard.overall({"/overview": overview, "/board": board}, total) is False  # ...the overall verdict does not
