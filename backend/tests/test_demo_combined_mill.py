"""DD-1b2a L0 (DD1b2-R Q2, Q4, Q6): the mill step's story instants, the order of the steps after the Site children, and
the store seam's refusal. No database and no work folder; the order is driven on the shape `prepare` passes (H1's style)."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import demo_combined as tool  # noqa: E402
import demo_combined_mill as mill_tool  # noqa: E402

from assetops_backend.mini_decisions.store import _INSERT_OPPORTUNITY_REVISION, _INSERT_OPPORTUNITY_SELECTION  # noqa: E402
from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore  # noqa: E402
from assetops_backend.prepare_clock import PrepareClockRefused  # noqa: E402

DB_NOW = datetime(2026, 11, 7, 10, 30, tzinfo=timezone.utc)
THREE = tool.SITES


@pytest.fixture()
def resolved() -> tuple[dict, list[dict]]:
    """As `prepare`: the real `resolve_story` on the shipped files, `days` popped, `sites` set."""
    story = tool.resolve_story(DB_NOW)
    days = story.pop("days")
    story["sites"] = [s for s in story["install_order"] if s in THREE]
    return story, days


class Recording(tool.Demo):
    """The real sequence methods; only the child launcher is replaced."""

    def __init__(self, work: Path) -> None:
        self.db, self.work, self.tree = "assetops_demo3_fake_test", work, work / "tree"
        self.url, self.deadline, self.started, self.holds_busy = "fake", None, [], False
        self.calls: list[str] = []
        self.drains: dict[str, float] = {}

    def drain(self, name: str = "drain") -> dict:
        """DD-1b2b O2: the R8 drain is its own tested unit (`test_dd1b2b_drain.py`); here only its place is recorded."""
        self.calls.append(name)
        self.drains[name] = 0.0
        return {}

    def py(self, *argv: str, label: str = "", **kw) -> subprocess.CompletedProcess:
        self.calls.append(label or argv[0])
        return subprocess.CompletedProcess(argv, 0, "[]\n", "")


def _order(demo: Recording) -> list[str]:
    return [c.split(" ")[0] for c in demo.calls]


def test_three_sites_run_the_mill_sequence_before_the_finish(resolved, tmp_path) -> None:
    story, days = resolved
    demo = Recording(tmp_path)
    timings: dict[str, float] = {}
    demo.finish_build(story, days, True, timings)
    order = _order(demo)
    assert order[:4] == ["mini-depth", "backfill-a", "mill", "backfill-bcd"]
    assert order.index("objectives") > order.index("backfill-bcd")
    assert order.index("tick") > order.index("backfill-bcd"), "no tick may run before the mill step"
    assert order.index("s2-comparison") < order[4:].index("mini-depth") + 4
    assert {"after_children", "finish"} <= set(timings)


def test_a_one_site_prepare_keeps_the_plain_finish(resolved, tmp_path) -> None:
    story, days = resolved
    story["sites"] = ["kobo"]
    demo = Recording(tmp_path)
    demo.finish_build(story, days, True, {})
    assert "mill" not in demo.calls and "backfill-a" not in demo.calls
    assert demo.calls[0] == "s2-comparison"


def test_no_finish_runs_no_step_after_the_children(resolved, tmp_path) -> None:
    story, days = resolved
    demo = Recording(tmp_path)
    demo.finish_build(story, days, False, {})
    assert demo.calls == []


def test_after_children_refuses_a_day_list_with_no_mill_day(resolved, tmp_path) -> None:
    story, days = resolved
    demo = Recording(tmp_path)
    with pytest.raises(SystemExit, match="mill-midday"):
        demo.after_children(story, [d for d in days if d["kind"] != "mill-midday"])
    assert demo.calls == []


def test_the_story_block_resolves_to_the_ruled_instants(resolved) -> None:
    story, _ = resolved
    S, m = tool.at(story["S"]), story["kobo"]["mill"]
    def on(day: int, hour: int, minute: int = 0) -> datetime:
        return S + timedelta(days=day, hours=hour, minutes=minute)
    assert tool.at(m["study"]["from"]) == on(-20, 21) and tool.at(m["study"]["to"]) == on(-15, 21)
    assert tool.at(m["study"]["at"]) == on(-14, 6)
    assert tool.at(m["action_at"]) == on(-10, 9)
    assert [tool.at(m[k]["occurred_at"]) for k in ("request", "record")] == [on(-9, 4), on(-9, 4, 30)]
    assert tool.at(m["assign_at"]) == on(-9, 4, 40) and tool.at(m["complete_at"]) == on(-9, 5)
    assert tool.at(m["commands_recorded_from"]) == on(-9, 5, 10)
    assert tool.at(m["case_link_at"]) == on(-9, 5, 20) and tool.at(m["freeze_at"]) == on(-9, 5, 25)
    assert tool.at(m["evaluate_at"]) == on(-5, 23)


def test_the_story_instants_are_in_the_required_order(resolved) -> None:
    story, _ = resolved
    assert mill_tool.instants_in_order(story["kobo"]["mill"]) == []


def test_an_instant_out_of_order_is_named(resolved) -> None:
    story, _ = resolved
    m = story["kobo"]["mill"]
    assert "action_at >= request" in mill_tool.instants_in_order({**m, "action_at": m["freeze_at"]})
    late = {**m, "study": {**m["study"], "at": m["study"]["from"]}}
    assert "study.from < study.to < study.at" in mill_tool.instants_in_order(late)


def test_evaluate_is_after_the_last_delivery_of_day_s_minus_5(resolved) -> None:
    """Q6: 22:00Z is exactly the S-5 `mill-rest` delivery; at 23:00Z every row read had been delivered."""
    story, days = resolved
    last = max(tool.at(d["received_at"]) for d in days if d["site"] == "kobo" and d["offset"] == -5 and d["received_at"])
    assert last < tool.at(story["kobo"]["mill"]["evaluate_at"])
    # and the study follows S-15's last delivery, so the pinned window was whole when it was projected
    last_15 = max(tool.at(d["received_at"]) for d in days if d["site"] == "kobo" and d["offset"] == -15 and d["received_at"])
    assert last_15 < tool.at(story["kobo"]["mill"]["study"]["at"])


def test_the_reader_drops_known_at() -> None:
    seen = {}
    def latest(*args):
        seen["args"] = args
        return ["row"]
    reader = mill_tool._AllKnown(SimpleNamespace(latest=latest))
    assert reader.latest("t", "s", "a", "b", ["m"], known_at="ignored") == ["row"]
    assert seen["args"] == ("t", "s", "a", "b", ["m"])


# --- Q2: the store seam ----------------------------------------------------------------------------------------------

def test_store_unset_binds_none_so_the_database_time_applies() -> None:
    store = PostgresMiniDecisionStore(engine=None)
    assert store._story_instant() is None
    for sql, name in ((_INSERT_OPPORTUNITY_REVISION, "created_at"), (_INSERT_OPPORTUNITY_SELECTION, "selected_at")):
        assert f"COALESCE(CAST(:{name} AS timestamptz), clock_timestamp())" in sql


def test_store_set_returns_the_instant() -> None:
    instant = datetime(2026, 10, 20, 6, tzinfo=timezone.utc)
    assert PostgresMiniDecisionStore(engine=None, story_clock=lambda: instant)._story_instant() == instant


@pytest.mark.parametrize("database", ["assetops", "assetops_demo3_x", "assetops_prod"])
def test_story_clock_is_refused_outside_a_prepare_database(database) -> None:
    with pytest.raises(PrepareClockRefused):
        PostgresMiniDecisionStore.from_url(f"postgresql+psycopg://u:p@127.0.0.1:1/{database}",
                                           story_clock=lambda: DB_NOW)


def test_no_clock_is_never_refused_by_name() -> None:
    store = PostgresMiniDecisionStore.from_url("postgresql+psycopg://u:p@127.0.0.1:1/assetops")
    assert store._story_instant() is None
    store.dispose()
