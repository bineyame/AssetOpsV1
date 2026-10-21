"""W3-03 run 0a fix round (L1): value tests for the Portfolio row facts and verification IDs, and the
private per-Site `_windows_covered` of the financial selector (M1, pure)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from test_w301_estate_index_postgres import URL

if URL:
    from sqlalchemy import text
    from test_w301_estate_index_postgres import (  # noqa: F401 - fixtures
        CaseRunner, Estate, S4_CASES, engine, imported_before, iso, pin_read_at, pg_harness, run_case, store)
    from assetops_backend.estate import financials, index


def test_financial_scope_carries_private_per_site_windows_covered(monkeypatch) -> None:
    covered = {"state": "CURRENT", "rows": []}
    uncovered = {"state": "UNKNOWN", "rows": []}
    by_site = {"a": covered, "b": uncovered, "m": covered}
    monkeypatch.setattr(financials, "site_coverage", lambda snap, t, s, d, f, to, k: by_site[s])
    monkeypatch.setattr(financials, "windowed_lines",
                        lambda snap, t, site, d, req, k, state: ([], site["site_id"] == "a", []))
    monkeypatch.setattr(financials, "mini_grid_lines", lambda *a: [])
    ev = financials.DOMAIN_OF_SITE_TYPE
    types = {t: d for t, d in ev.items()}
    ev_type = next(t for t, d in types.items() if d == "ev_charging")
    mini_type = next(t for t, d in types.items() if d == financials.MINI_GRID)
    scope = {"k": None, "sites": [{"site_id": "a", "site_type": ev_type}, {"site_id": "b", "site_type": ev_type},
                                  {"site_id": "m", "site_type": mini_type}]}
    per_site, *_ = financials.select_financial_scope(None, None, SimpleNamespace(from_=None, to=None), scope)
    assert [ps[2]["_windows_covered"] for ps in per_site] == [True, False, True]


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
def test_portfolio_row_facts_and_verification_ids_match_stored_rows(store, engine, monkeypatch) -> None:  # noqa: F811
    from test_s6_verification_evaluator_postgres import (
        CLOSED, bound_plan, complete_windows, evaluate, verifying)

    runner = CaseRunner(store, engine)
    run_case(runner, S4_CASES["F01"])
    h = verifying(runner)
    pin_read_at(monkeypatch, lambda: max(h.clock.at, runner.now) + timedelta(minutes=1))
    imported_before(engine, runner.tenant, runner.site, datetime(2026, 10, 1, tzinfo=timezone.utc))
    estate = Estate(engine, runner.tenant)
    caught: dict = {"f": [], "a": []}
    real_f, real_a = index.select_finding_scope, index.select_action_scope
    monkeypatch.setattr(index, "select_finding_scope", lambda *a: caught["f"].append(real_f(*a)) or caught["f"][-1])
    monkeypatch.setattr(index, "select_action_scope", lambda *a: caught["a"].append(real_a(*a)) or caught["a"][-1])
    window = {"from": "2026-10-06T00:00:00Z", "to": "2026-11-03T00:00:00Z"}
    try:
        complete_windows(monkeypatch, h)
        action_id, plan, _ = bound_plan(runner, h)
        h.clock.at = CLOSED + timedelta(hours=1)
        outcome = evaluate(h, action_id, "eval-0001").json()["outcome"]
        assert outcome["outcome"] == "VERIFIED"
        estate.ok("findings", **{"from": "2026-10-06T00:00:00Z", "to": "2026-10-07T00:00:00Z"})
        estate.ok("actions", **window)
        with engine.connect() as c:
            stored = {str(r[0]): r[1] for r in c.execute(text("SELECT id, episode_end FROM finding_revision"))}
            site_type = c.execute(text("SELECT site_type FROM site WHERE id = :s"), {"s": runner.site}).scalar()
            plans = [(str(r[0]), r[1]) for r in c.execute(text(
                "SELECT id, recorded_at FROM verification_plan WHERE action_id = :a ORDER BY recorded_at, id"),
                {"a": action_id})]
            event_at = {str(r[0]): r[1] for r in c.execute(text(
                "SELECT id, recorded_at FROM action_event WHERE action_id = :a"), {"a": action_id})}
            outcome_id = str(c.execute(text(
                "SELECT id FROM verification_outcome WHERE action_id = :a"), {"a": action_id}).scalar())
        frows = [r for _, rows in caught["f"] for r in rows]
        assert frows
        for r in frows:
            assert r["_episode_end"] == stored[r["finding_revision_id"]]
            assert r["_domain"] == site_type and r["_mechanism"] is None
        (arow,) = [r for _, rows in caught["a"] for r in rows if r["action_id"] == action_id]
        raw = arow["_raw"]
        assert [(p["id"], p["recorded_at"]) for p in raw["_plans"]] == plans
        assert plan["plan_id"] == plans[0][0] and raw["_outcome_id"] == outcome_id
        assert raw["_outcomes"] and list(raw["_outcomes"]) == [outcome_id]
        # r1a Q-1a-1: the private tie key is the selected stored Action event's own recorded_at.
        assert raw["_selected_recorded_at"] == event_at[arow["selected_event_id"]]
    finally:
        h.close()
        pg_harness.dispose(runner.findings)
