"""DATA-13 (D-17N.4, C17): the Cold, EV and Kisiwa story Actions carry a due date. No database: each producer's Action
body is pinned (Cold by the BUILD source and the demo namespace, EV by `action_body`, Kisiwa by `record_action` against
a fake domain service); the Postgres proof is the VPS scratch prepare named in `.agent/DATA-17N-packet.md`."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import demo_story_clock as clock

RAISED = datetime(2026, 11, 3, 13, 0, tzinfo=timezone.utc)
TOOLS = Path(__file__).resolve().parents[2] / "tools"


def test_the_rule_is_fourteen_days_and_inside_the_domain_due_limit() -> None:
    from assetops_backend.work.domain_action import DUE_LIMIT

    assert clock.STORY_ACTION_DUE == timedelta(days=14)
    assert clock.story_action_due(RAISED) == RAISED + timedelta(days=14)
    assert RAISED < clock.story_action_due(RAISED) <= RAISED + DUE_LIMIT


def test_ev_action_body_takes_the_demo_due_only_when_set(monkeypatch) -> None:
    import w504_ev_work_cases as P

    selected = SimpleNamespace(k0=RAISED - timedelta(hours=1), finding_id="f", finding_revision_id="r")
    assert P.DEMO_ACTION_DUE is None
    assert P.action_body(selected, RAISED, "k" * 20)["due_at"] is None  # standalone w504 is unchanged
    monkeypatch.setattr(P, "DEMO_ACTION_DUE", clock.STORY_ACTION_DUE)
    body = P.action_body(selected, RAISED, "k" * 20)
    assert P.instant(body["due_at"]) == RAISED + timedelta(days=14)
    assert (body["title"], body["owner_label"]) == (P.ACTION["title"], P.ACTION["owner_label"])


def test_cold_build_posts_the_demo_due() -> None:
    import w502_cold_work_walkthrough as W

    assert '"due_at": fixture_due, "raised_at": iso(raised)' in W.BUILD
    assert 'globals().get("DEMO_ACTION_DUE")' in W.BUILD
    cold = (TOOLS / "demo_combined_cold.py").read_text(encoding="utf-8")
    assert '"DEMO_ACTION_DUE": STORY_ACTION_DUE' in cold


def test_ev_demo_sets_and_restores_the_due() -> None:
    ev = (TOOLS / "demo_combined_ev.py").read_text(encoding="utf-8")
    assert "W.P.DEMO_ACTION_DUE = STORY_ACTION_DUE" in ev
    assert "W._db_now, W.P.DEMO_ACTION_DUE = saved, saved_due" in ev


def test_kisiwa_action_is_posted_with_its_due(monkeypatch) -> None:
    import demo_combined as dc
    import demo_combined_kisiwa as kis
    from assetops_backend.work import composition

    kisiwa = dc.resolve_story(datetime(2026, 11, 8, 10, 0, tzinfo=timezone.utc), kisiwa=True)["kisiwa"]
    posted: list[dict] = []
    store = SimpleNamespace(test_db_clock_override=None, dispose=lambda: None)
    domain = SimpleNamespace(_store=store, create_action=lambda t, s, c, body, p: posted.append(body) or (409, {}))
    monkeypatch.setattr(composition, "build_domain_intent_service", lambda url: domain)
    monkeypatch.setattr(composition, "build_work_service", lambda url: SimpleNamespace(_store=store))
    with pytest.raises(SystemExit, match="ACTION_REFUSED"):
        kis.record_action("postgresql://unused", None, "t", "s", kisiwa, {"finding_id": "f", "revision_id": "r"})
    [body] = posted
    raised = kis.at(kisiwa["action"]["raised_at"])
    assert kis.at(body["due_at"]) == raised + timedelta(days=14)


def test_the_kobo_mill_action_is_unchanged() -> None:
    """Scope: Cold, EV and Kisiwa (C17); Kobo's Actions are a packet question."""
    mill = (TOOLS / "demo_combined_mill.py").read_text(encoding="utf-8")
    assert '"due_at": None' in mill
