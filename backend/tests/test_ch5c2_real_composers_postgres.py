"""CH-5c2 L2 on the real composers (build sheet §8.6 F4/F6, §8.7 C4): the Kobo `guardrail` case (OUT-B4's builder,
`test_out_b4_board_postgres._build_kobo`, with its Performance comparison report and settled chain) in its own
`assetops_out_ch5c2_guardrail_test` database, served by `create_app` with the response store on.

- F6: a new Performance report, and a planted FAILED one, between two identical board requests; on the summary, an
  S2 comparison report (`evidence_migration run`) and a planted FAILED one. The second request is never a `hit` and
  its body equals a store-less compose; the closing report changes the body.
- C4: the completeness sweep (`tools/chain_response_probe.sweep`) over every stored route, with a verification
  plan's later window and a verified outcome placed so their boundaries fall before `valid_until(t0)`.
- F4: the compose audit hook over every stored route records no file or socket read; a planted file read and a
  planted directory listing inside each compose are recorded for every route.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

CODE = "KOBO-001"
DAYS = "from=2026-10-01T00:00:00Z&to=2026-11-03T00:00:00Z"
BOARD = f"/api/sites/{CODE}/outcome-board?date=2026-10-06"
SUMMARY = f"/api/estate/outcome-summary?{DAYS}"
PATHS = [BOARD, SUMMARY, f"/api/estate/findings?{DAYS}", f"/api/estate/portfolio?{DAYS}&lens=all",
         f"/api/estate/portfolio/scope-ids?{DAYS}&lens=all"]


@pytest.fixture(scope="module")
def kobo(tmp_path_factory):
    import test_out_b4_board_postgres as b4

    work = tmp_path_factory.mktemp("ch5c2")
    with b4._case_db("guardrail", "ch5c2") as url:
        b4._build_kobo(url, work, "guardrail")
        yield url, work


def _app(monkeypatch, url: str, work: Path, mode: str, *, s2_stand_in: bool = True):
    import test_out_b4_board_postgres as b4

    monkeypatch.setenv("ASSETOPS_RESPONSE_STORE", mode)
    b4._serve(monkeypatch, url, work, s2_stand_in=s2_stand_in)
    return b4._client()


def _get(c, path: str):
    from assetops_backend.chain.response_store import HEADER

    r = c.get(path)
    assert r.status_code == 200, (path, r.status_code, r.text[:300])
    return r.headers.get(HEADER), r.json()


def _quiet(a: dict, b: dict) -> dict:
    from chain_response_probe import _mask

    return _mask(a, b)


def _plant_report(folder: Path, outcome: str) -> Path:
    """A copy of the newest report in `folder`, named to sort last, with `outcome` (the planted closing report)."""
    newest = sorted(folder.glob("*.json"))[-1]
    report = json.loads(newest.read_text(encoding="utf-8"))
    report["outcome"] = outcome
    report["report_id"] = f"planted-{outcome.lower()}"
    path = folder / f"99999999T999999999999Z-planted-{outcome.lower()}.json"
    path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def _second_is_fresh(monkeypatch, url, work, path, *, s2_stand_in: bool) -> dict:
    """The second request after a file write: not a hit, and equal to a store-less compose."""
    with _app(monkeypatch, url, work, "on", s2_stand_in=s2_stand_in) as c:
        state, body = _get(c, path)
    assert state in ("stored", "race"), state
    with _app(monkeypatch, url, work, "off", s2_stand_in=s2_stand_in) as c:
        _, fresh = _get(c, path)
    assert _quiet(body, fresh) == body
    return body


def test_f6_board_follows_a_new_and_a_closing_performance_report(kobo, monkeypatch) -> None:
    from assetops_backend.performance_migration import main as performance_migration

    url, work = kobo
    folder = work / "evidence" / "migration-performance" / CODE.lower()
    with _app(monkeypatch, url, work, "on") as c:
        _get(c, BOARD)
        state, opened = _get(c, BOARD)
    assert state == "hit"
    assert performance_migration(["run", "--tenant", "demo", "--site", CODE]) == 0  # a new PASSED report
    again = _second_is_fresh(monkeypatch, url, work, BOARD, s2_stand_in=True)
    assert _quiet(opened, again) == opened  # the same gate state (PASSED), recomposed
    planted = _plant_report(folder, "FAILED")
    try:
        closed = _second_is_fresh(monkeypatch, url, work, BOARD, s2_stand_in=True)
        assert _quiet(opened, closed) != opened  # the closed gate reaches the board
        print("\nCH-5c2 F6 board read_state", opened["read_state"], "->", closed["read_state"])
    finally:
        planted.unlink()


def test_f6_summary_follows_an_s2_report_and_a_closing_one(kobo, monkeypatch) -> None:
    from assetops_backend.evidence_migration import main as evidence_migration

    url, work = kobo
    with _app(monkeypatch, url, work, "on", s2_stand_in=False) as c:
        _get(c, SUMMARY)
        state, before = _get(c, SUMMARY)
    assert state == "hit"
    assert evidence_migration(["run", "--tenant", "demo", "--site", CODE]) == 0  # a real S2 comparison report
    after = _second_is_fresh(monkeypatch, url, work, SUMMARY, s2_stand_in=False)
    planted = _plant_report(work / "evidence" / "migration" / CODE.lower(), "FAILED")
    try:
        closed = _second_is_fresh(monkeypatch, url, work, SUMMARY, s2_stand_in=False)
        assert _quiet(after, closed) != after or _quiet(before, after) != before  # some report reached the body
        assert _quiet(before, closed) == before  # closed again: the body before any passing report
        print("\nCH-5c2 F6 summary changed on the S2 report:", _quiet(before, after) != before)
    finally:
        planted.unlink()


def _place(url: str, t0: datetime) -> dict:
    """C4 seed: one verification plan's later window shifted by whole days (the same-clock constraint) so its
    `later_end` lies after `t0`, and one verified outcome's `recorded_at` moved to `t0 - 30 d + 3 h`, under
    `session_replication_role = replica` (the append-only triggers; a seed edit, before `t0`)."""
    from sqlalchemy import create_engine, text

    from assetops_backend.estate.coverage import VERIFIED_LOOKBACK

    engine = create_engine(url)
    try:
        with engine.begin() as c:
            c.execute(text("SET LOCAL session_replication_role = replica"))
            plan = c.execute(text("SELECT id, later_end FROM verification_plan ORDER BY recorded_at LIMIT 1")).first()
            outcome = c.execute(text("SELECT id FROM verification_outcome ORDER BY recorded_at LIMIT 1")).first()
            placed = {"plan": None, "outcome": None}
            if plan is not None:
                days = (t0 - plan.later_end).days + 1
                c.execute(text("UPDATE verification_plan SET later_start = later_start + make_interval(days => :d), "
                               "later_end = later_end + make_interval(days => :d) WHERE id = :i"),
                          {"d": days, "i": plan.id})
                placed["plan"] = c.execute(text("SELECT later_end FROM verification_plan WHERE id = :i"),
                                           {"i": plan.id}).scalar_one()
            if outcome is not None:
                at = t0 - VERIFIED_LOOKBACK + timedelta(hours=3)
                c.execute(text("UPDATE verification_outcome SET recorded_at = :a WHERE id = :i"),
                          {"a": at, "i": outcome.id})
                placed["outcome"] = at
    finally:
        engine.dispose()
    return placed


def test_c4_sweep_over_every_stored_route(kobo, monkeypatch) -> None:
    from sqlalchemy import create_engine, text

    import chain_response_probe as probe
    from assetops_backend.estate.coverage import VERIFIED_LOOKBACK

    url, work = kobo
    t0 = datetime.now(timezone.utc) + timedelta(minutes=1)
    placed = _place(url, t0)
    print("\nCH-5c2 C4 placed", {k: v and v.isoformat() for k, v in placed.items()})
    assert placed["plan"] is not None and placed["outcome"] is not None, placed
    engine = create_engine(url)

    def until_of(tag: str):
        with engine.connect() as c:
            return c.execute(text("SELECT valid_until FROM chain_response WHERE etag = :e"), {"e": tag}).scalar_one()

    with engine.connect() as c:
        zones = sorted({r[0] for r in c.execute(text("SELECT DISTINCT timezone FROM site"))})
    seeded = probe.seeded_instants(url, t0 - VERIFIED_LOOKBACK - probe.HORIZON, t0 + probe.HORIZON)
    cands = probe.candidates(seeded, t0, zones, VERIFIED_LOOKBACK)
    try:
        with _app(monkeypatch, url, work, "on") as on, _app(monkeypatch, url, work, "compose") as composed:
            report = probe.sweep(on, composed, PATHS, until_of, t0, cands)
    finally:
        engine.dispose()
    print("CH-5c2 C4 sweep", json.dumps({"seeded": len(seeded), "candidates": len(cands),
                                         "paths": report["paths"]}, default=str))
    assert report["violations"] == [], report["violations"]
    # Non-empty: the placed outcome's lookback end is a candidate composed before some route's valid_until.
    assert sum(p["composed"] for p in report["paths"].values()) > 0, report["paths"]


def _audit(monkeypatch, url, work, plant=None):
    from chain_watermark_guard import ComposeAudit

    from assetops_backend.chain.response_store import ResponseStore

    if plant is not None:
        real = ResponseStore._composed

        def composed(self, req, compose):
            return real(self, req, lambda: (plant(), compose())[1])

        monkeypatch.setattr(ResponseStore, "_composed", composed)
    with _app(monkeypatch, url, work, "compose") as c, ComposeAudit() as audit:
        for path in PATHS:
            _get(c, path)
    return audit


def test_f4_no_unlisted_read_over_every_stored_route(kobo, monkeypatch) -> None:
    from chain_watermark_guard import listed_modules

    url, work = kobo
    audit = _audit(monkeypatch, url, work)
    assert audit.violations == [], audit.violations
    assert audit.modules and not audit.modules - set(listed_modules()), sorted(audit.modules - set(listed_modules()))


@pytest.mark.parametrize("event", ["open", "listdir"])
def test_f4_a_planted_read_is_recorded_on_every_route(kobo, monkeypatch, tmp_path, event) -> None:
    url, work = kobo
    target = tmp_path / "planted.txt"
    target.write_text("x", encoding="utf-8")
    plant = (lambda: target.read_text(encoding="utf-8")) if event == "open" else (lambda: os.listdir(tmp_path))
    audit = _audit(monkeypatch, url, work, plant)
    routes = {v["route"] for v in audit.violations if v["target"].startswith(os.path.normcase(str(tmp_path)))}
    from assetops_backend.estate_portfolio_api import PORTFOLIO, SCOPE_IDS
    from assetops_backend.outcome_api import BOARD_ROUTE, SUMMARY_ROUTE

    assert routes == {BOARD_ROUTE, SUMMARY_ROUTE, "/api/estate/findings", PORTFOLIO, SCOPE_IDS}, audit.violations
