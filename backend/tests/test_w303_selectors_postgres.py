"""W3-03 run 0a fix round (L1): value tests for the Portfolio row facts and verification IDs, and the
private per-Site `_windows_covered` of the financial selector (M1, pure), and the line-less `_pending_guard`
(r1b Q-1b-3, pure)."""

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
                        lambda snap, t, site, d, req, k, state: ([], site["site_id"] == "a", [], False))
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


class _GuardSnap:
    """Per-Site cold/EV reads for the real `windowed_lines` (no storage): `pins[s]` None means no evidence cutoff."""
    basis_historical = False

    def __init__(self, pins, cold=None, ev=None) -> None:
        self.pins, self.cold, self.ev = pins, cold or {}, ev or {}

    def evidence_cutoff(self, t, s, k):
        return None if self.pins.get(s) is None else datetime(2026, 10, 8, tzinfo=timezone.utc)

    def pinned_windows(self, t, s, domain, from_, to, cutoff, k):
        return self.pins[s]

    def cold_money(self, t, s, pin, k):
        return self.cold[s]

    def ev_money(self, pin):
        return self.ev[pin["site"]]

    def cited_provenance(self, *args):  # no line is emitted by any case below
        raise AssertionError("no consequence line expected")


def test_financial_scope_pending_guard_without_line(monkeypatch) -> None:
    """r1b Q-1b-3: `windowed_lines` returns `pending_guard`, true for a selected cold window that is `withheld`
    with zero consequences and for an EV window whose guard is ERROR_PENDING with no stored history, whether or not a
    line is emitted; false for an EV STALE_BASIS guard, a missing pin, an uncovered (stale) window and an ordinary
    cold read. `select_financial_scope` carries it as private `_pending_guard` on every per-Site coverage dict
    (false for mini-grid and non-applicable Sites). The W3-02 public golden bytes are proven unchanged by the
    W3-02 golden run, since `_pending_guard` never reaches a public field or the selection token. r1b3 P-1b-4: with
    the pure `test_money_table`, this fake-snapshot test is the EV guard-to-Portfolio proof; it claims no persisted
    EV pending head."""
    from assetops_backend.estate import financials as fin

    monkeypatch.setattr(fin, "_money_links", lambda *a: {})
    req = SimpleNamespace(from_=datetime(2026, 10, 1, tzinfo=timezone.utc), to=datetime(2026, 10, 8, tzinfo=timezone.utc))
    k = req.to
    cold_clear = {"withheld": False, "consequences": [], "finding_ids": {}, "hold": None}
    cold_withheld = {**cold_clear, "withheld": True}

    def ev(guard, head=None, history=()):
        return {"consequence": head, "guard": guard, "history": list(history), "session_revision_ids": [],
                "window_start": None, "window_end": None}

    pin = lambda s, state="CURRENT": [{"state": state, "site": s}]  # noqa: E731
    snap = _GuardSnap(
        pins={"cw": pin("cw"), "cc": pin("cc"), "cs": pin("cs", fin.STALE), "cn": None, "ep": pin("ep"),
              "eh": pin("eh"), "es": pin("es"), "en": None, "e0": []},
        cold={"cw": cold_withheld, "cc": cold_clear, "cs": cold_clear},
        ev={"ep": ev(fin.ERROR_PENDING, head={"revision_id": None}), "eh": ev(fin.ERROR_PENDING),
            "es": ev("STALE_BASIS", head={"revision_id": None})})
    cases = {"cw": (fin.COLD, True), "cc": (fin.COLD, False), "cs": (fin.COLD, False), "cn": (fin.COLD, False),
             "ep": (fin.EV, True), "eh": (fin.EV, True), "es": (fin.EV, False), "en": (fin.EV, False),
             "e0": (fin.EV, False)}
    for s, (domain, expected) in cases.items():
        site = {"site_id": s, "site_code": s}
        lines, covered, sessions, guard = fin.windowed_lines(snap, None, site, domain, req, k, "CURRENT")
        assert (lines, guard) == ([], expected), s
        if s in ("cw", "ep", "es", "cs"):
            assert covered is False, s  # a guard or stale window leaves the category's coverage unknown
    # the per-Site private field on the full-scope selector
    type_of = {d: t for t, d in fin.DOMAIN_OF_SITE_TYPE.items()}
    monkeypatch.setattr(fin, "site_coverage", lambda *a: {"state": "CURRENT", "rows": []})
    monkeypatch.setattr(fin, "mini_grid_lines", lambda *a: [])
    sites = [{"site_id": s, "site_code": s, "site_type": type_of[d]} for s, (d, _) in cases.items()]
    sites += [{"site_id": "m", "site_code": "m", "site_type": type_of[fin.MINI_GRID]},
              {"site_id": "x", "site_code": "x", "site_type": "NOT_A_DOMAIN"}]
    per_site, lines, *_ = fin.select_financial_scope(snap, None, req, {"k": k, "sites": sites})
    assert lines == []
    assert {str(ps[0]["site_id"]): ps[2]["_pending_guard"] for ps in per_site} == {
        **{s: expected for s, (_, expected) in cases.items()}, "m": False, "x": False}
