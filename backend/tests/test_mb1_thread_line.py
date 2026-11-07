"""MB-1b (FUEL-1 MB-1-R §3.4, MB-1a-R2 §1): the mill's thread line on the Kobo board's Grow row (L0, no DB).

The line function's kinds, the compose-side view (occurrence selection, the runner's fully checked days, the
work-window guard, no policy -> no line), the category, the subline join, the other rows byte-equal, and the MILL-4
finish row's self-test."""
from __future__ import annotations

import sys
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from assetops_backend.chain import lifecycle as lc
from assetops_backend.chain import lifecycle_run
from assetops_backend.outcomes.catalogue import MINI
from assetops_backend.outcomes.display_code import display_code
from assetops_backend.outcomes.outcome_map import categories_for, thread_signal_key
from assetops_backend.site_outcomes import board, mini
from assetops_backend.site_outcomes.board import OpportunityActionFact, SiteFacts

import test_out_b2_mini as B2

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import demo_combined_finish as finish  # noqa: E402

MILL, MILL_T, CODE = "a-mill", "t-mill", "ACT-000002"
SHOWN = display_code(CODE)  # "ACT-002"
MECH, MEASURE = "PRODUCTIVE_USE_HEADROOM", "daylight_headroom_kw"
POLICY = lc.LifecyclePolicy("test-v1", 7, {}, 14, {MECH: (MEASURE,)})
D = lambda m, d: date(2026, m, d)  # noqa: E731


# ---- 1. opportunity_line_item, one case per kind ------------------------------------------------------------------

def _view(state, seg=1, change=D(10, 7), checked=0, close_after=7, recurred=None):
    return {"segment_no": seg, "state": state, "change_day": change, "checked_days": checked,
            "close_after": close_after, "recurred_day": recurred}


def _fact(view, seg=1, count_known=True, category="GROW_REVENUE"):
    return OpportunityActionFact(MILL, CODE, MILL_T, "VERIFIED", {"kind": "DOMAIN_VERDICT"}, view=view,
                                 action_segment=seg, category=category, count_known=count_known)


def _facts(*opp, day=D(10, 20)):
    return SiteFacts(MINI, "KOBO-001", day=day, opportunity_actions=tuple(opp))


def _line(o, day=D(10, 20)):
    return board.opportunity_line_item(o, _facts(o, day=day))


def test_monitoring_counts_the_remaining_fully_checked_days_from_the_view() -> None:
    item = _line(_fact(_view("RESOLVED_MONITORING", checked=4)))
    assert item["kind"] == "MONITORING" and item["remaining_days"] == 3 and item["clean_days"] is None
    assert item["text"] == board.OPP_THREAD_MONITORING.format(code=display_code(CODE), k=3)
    assert item["text"] == f"Change checked and working ({SHOWN}) · 3 more fully checked days to close"
    assert item["action_code"] == CODE and item["thread_id"] == MILL_T and item["effective_day"] == "2026-10-07"
    assert item["ref"]["kind"] == "THREAD" and item["after"] is None
    assert _line(_fact(_view("RESOLVED_MONITORING", checked=9)))["remaining_days"] == 0  # never negative


def test_closed_names_the_close_rule_days() -> None:
    item = _line(_fact(_view("CLOSED", close_after=7)))
    assert (item["kind"], item["clean_days"], item["remaining_days"]) == ("CLOSED", 7, None)
    assert item["text"] == board.OPP_THREAD_CLOSED.format(code=display_code(CODE), n=7)


def test_recurred_names_the_day_when_the_action_is_in_an_earlier_segment() -> None:
    item = _line(_fact(_view("RECURRED", seg=2, recurred=D(10, 18)), seg=1))
    assert item["kind"] == "RECURRED" and item["effective_day"] == "2026-10-18"
    assert item["text"] == f"Spare solar seen again on 18 Oct after the change ({SHOWN})"


def test_before_the_change_is_the_bare_before_line() -> None:
    item = _line(_fact(_view("ACTION_IN_HAND", change=D(10, 22))))
    assert item["kind"] == "BEFORE_CHANGE" and item["text"] == board.THREAD_BEFORE.format(e="22 Oct")
    assert item["effective_day"] == "2026-10-22"


@pytest.mark.parametrize("o", [
    _fact(None),                                                          # no view
    _fact(_view("ACTION_IN_HAND")),                                       # anything else
    _fact(_view("CHANGE_APPLIED")),
    _fact(_view("RECURRED", seg=2, recurred=D(10, 18)), seg=2),           # the Action is in the recurred segment
    _fact(_view("RECURRED", seg=2, recurred=None), seg=1),                # no recurred day
    _fact(_view("RESOLVED_MONITORING", seg=2), seg=1),                    # another segment's verification
    _fact(_view("CLOSED", seg=2), seg=1),
    _fact(_view("RESOLVED_MONITORING", checked=2), count_known=False),    # the window cannot see every checked day
])
def test_no_line(o) -> None:
    assert _line(o) is None


def test_no_board_day_gives_no_line() -> None:
    o = _fact(_view("RESOLVED_MONITORING"))
    assert board.opportunity_line_item(o, SiteFacts(MINI, "KOBO-001", opportunity_actions=(o,))) is None


# ---- 2. compose: the view ----------------------------------------------------------------------------------------

def _occ(no, opp, start):
    return {"thread_id": MILL_T, "mechanism": MECH, "subject_ref": "SITE", "occurrence_no": no, "finding_id": None,
            "opportunity_id": opp, "opportunity_no": 7, "episode_start": start, "episode_end": None}


def _ev(seq, state, day, cause_kind="X", cause_id="c"):
    return {"thread_id": MILL_T, "seq": seq, "state": state, "cause_kind": cause_kind, "cause_id": cause_id,
            "effective_day": day, "recorded_at": datetime(2026, 9, 1, tzinfo=B2.T(1).tzinfo), "cause_known_at": None}


def _act(accepted=B2.T(6)):
    return {"action_id": MILL, "action_code": CODE, "kind": "DOMAIN_INTENT", "thread_id": MILL_T,
            "origin_finding_id": None, "origin_opportunity_id": "o1", "accepted_at": accepted,
            "outcome": "VERIFIED", "outcome_recorded_at": B2.T(10)}


#: The mill story on a 20 Oct board (Nairobi): opportunity 5 Oct, accepted 6 Oct, change 7 Oct, verified 10 Oct.
BASE = [_ev(1, "OPEN", D(10, 5), "OCCURRENCE", "o1"), _ev(2, "ACTION_IN_HAND", D(10, 6)),
        _ev(3, "CHANGE_APPLIED", D(10, 7)), _ev(4, "RESOLVED_MONITORING", D(10, 10))]


def _snap(day, grade="COMPLETE", measure=MEASURE, kind="SITE", ref="SITE"):
    return SimpleNamespace(local_day=day, subject_kind=kind, subject_ref=ref, measure=measure, grade=grade)


#: 11-14 Oct complete (4), 15 Oct PARTIAL, 16 Oct another measure only, 18 Oct complete but an occurrence starts.
SNAPS = (*(_snap(D(10, d)) for d in (11, 12, 13, 14)), _snap(D(10, 15), "PARTIAL"),
         _snap(D(10, 16), measure="critical_served"), _snap(D(10, 18)), _snap(D(10, 9)))


def _ports(events, occs, *, policy=POLICY, snaps=SNAPS, accepted=B2.T(6)):
    fake = B2.Fake(day={"rows": tuple(snaps)})
    rows = {"occurrences": tuple(occs), "events": tuple(events), "actions": (_act(accepted),)}
    return replace(fake.ports(), chain_threads=lambda: mini.ChainThreads(rows, None, policy))


def _compose(ports):
    """`read.py` board() sets the board day on the facts after compose (as for every thread line); so does this."""
    comp = mini.compose(ports, site_code=B2.C, day=B2.DAY, site_timezone=B2.ZONE)
    comp = replace(comp, facts=replace(comp.facts, day=B2.DAY))
    return comp, {r["category"]: r for r in B2.assemble(comp.facts)}


def _mill_fact(comp) -> OpportunityActionFact:
    (o,) = comp.facts.opportunity_actions
    return o


def test_s8_shape_excludes_an_occurrence_starting_after_the_board_day() -> None:
    """The recurrence starts 25 Oct, after the 20 Oct board: the line is MONITORING over the first occurrence."""
    events = [*BASE, _ev(5, "RECURRED", D(10, 25), "OCCURRENCE", "o2")]
    comp, rows = _compose(_ports(events, [_occ(1, "o1", B2.T(5, 6)), _occ(2, "o2", B2.T(25, 6))]))
    o = _mill_fact(comp)
    assert (o.view["segment_no"], o.view["state"], o.action_segment) == (1, "RESOLVED_MONITORING", 1)
    (line,) = rows[mini.GROW]["thread_lines"]
    assert line["kind"] == "MONITORING" and line["remaining_days"] == 7 - 5  # 11-14 Oct and 18 Oct
    assert line["text"] == f"Change checked and working ({SHOWN}) · 2 more fully checked days to close"


def test_s0_shape_reads_the_recurrence_started_by_the_board_day() -> None:
    events = [*BASE, _ev(5, "RECURRED", D(10, 18), "OCCURRENCE", "o2")]
    comp, rows = _compose(_ports(events, [_occ(1, "o1", B2.T(5, 6)), _occ(2, "o2", B2.T(18, 6))]))
    o = _mill_fact(comp)
    assert (o.view["segment_no"], o.view["state"], o.action_segment) == (2, "RECURRED", 1)
    (line,) = rows[mini.GROW]["thread_lines"]
    assert (line["kind"], line["text"]) == ("RECURRED", f"Spare solar seen again on 18 Oct after the change ({SHOWN})")


def test_closed_shape() -> None:
    events = [*BASE, _ev(5, "CLOSED", D(10, 19))]
    _, rows = _compose(_ports(events, [_occ(1, "o1", B2.T(5, 6))]))
    (line,) = rows[mini.GROW]["thread_lines"]
    assert line["kind"] == "CLOSED" and line["text"] == board.OPP_THREAD_CLOSED.format(code=display_code(CODE), n=7)


def test_parity_the_view_counts_the_lifecycle_runners_fully_checked_days(monkeypatch) -> None:
    """MB-1-R Q3: `complete` equals `lifecycle_run.thread_clean_days` over the same snapshot and occurrence rows."""
    occs = [_occ(1, "o1", B2.T(5, 6)), _occ(2, "o2", B2.T(18, 6))]
    seen = {}
    real = lc.fully_checked_days

    def spy(*a, **kw):
        seen["complete"] = real(*a, **kw)
        return seen["complete"]

    monkeypatch.setattr(lc, "fully_checked_days", spy)
    _compose(_ports([*BASE, _ev(5, "RECURRED", D(10, 18), "OCCURRENCE", "o2")], occs))
    monkeypatch.undo()
    thread = {"mechanism": MECH, "subject_ref": "SITE",
              "occurrences": [(o["opportunity_id"], o["episode_start"]) for o in occs]}
    runner = lifecycle_run.thread_clean_days(thread, {"tz": B2.ZONE, "snapshots": SNAPS}, POLICY)
    assert seen["complete"] == runner == {D(10, d) for d in (9, 11, 12, 13, 14)}  # 18 Oct is an occurrence start


def test_no_policy_gives_no_view_and_no_line() -> None:
    """MB-1a-R2 §1: no policy -> no view, never a guessed `close_after`."""
    comp, rows = _compose(_ports(BASE, [_occ(1, "o1", B2.T(5, 6))], policy=None))
    assert _mill_fact(comp).view is None and rows[mini.GROW]["thread_lines"] == []


def test_a_verified_day_before_the_work_window_gives_no_monitoring_line() -> None:
    """MB-1-R Q3: the 31-day window (from 20 Sep) cannot see every checked day since 10 Sep -> no line."""
    sep = [_ev(1, "OPEN", D(9, 1), "OCCURRENCE", "o1"), _ev(2, "ACTION_IN_HAND", D(9, 2)),
           _ev(3, "CHANGE_APPLIED", D(9, 3)), _ev(4, "RESOLVED_MONITORING", D(9, 10))]
    start = datetime(2026, 9, 1, 6, tzinfo=B2.T(1).tzinfo)
    comp, rows = _compose(_ports(sep, [_occ(1, "o1", start)], accepted=datetime(2026, 9, 2, 6, tzinfo=start.tzinfo)))
    o = _mill_fact(comp)
    assert o.view["state"] == "RESOLVED_MONITORING" and o.count_known is False
    assert rows[mini.GROW]["thread_lines"] == []


def test_the_mill_category_is_grow_revenue() -> None:
    moves = [i for i in categories_for(thread_signal_key(MECH), MINI)["items"] if i["role"] == "MOVES"]
    assert moves[0]["category"] == "GROW_REVENUE"
    comp, _ = _compose(_ports(BASE, [_occ(1, "o1", B2.T(5, 6))]))
    assert _mill_fact(comp).category == "GROW_REVENUE" == mini.GROW


def test_the_grow_subline_is_the_sales_subline_then_the_line() -> None:
    comp, rows = _compose(_ports(BASE, [_occ(1, "o1", B2.T(5, 6))]))
    grow = rows[mini.GROW]
    (line,) = grow["thread_lines"]
    sales = comp.facts.subline.get(mini.GROW)
    assert sales, "the fake board has no sales subline: the join is not exercised"
    assert grow["subline"] == sales + " · " + line["text"]


def test_optimize_protect_and_assure_rows_are_byte_equal_with_and_without_the_line() -> None:
    _, with_line = _compose(_ports(BASE, [_occ(1, "o1", B2.T(5, 6))]))
    _, no_view = _compose(_ports(BASE, [_occ(1, "o1", B2.T(5, 6))], policy=None))
    assert with_line[mini.GROW]["thread_lines"] and not no_view[mini.GROW]["thread_lines"]
    for cat in (mini.COST, mini.PROTECT, mini.ASSURE):
        assert with_line[cat] == no_view[cat], cat
    _, without_mill = _compose(B2.Fake(day={"rows": SNAPS}).ports())
    for cat in (mini.COST, mini.PROTECT):
        assert with_line[cat] == without_mill[cat], cat
    strip = lambda r: {k: v for k, v in r.items() if k not in ("thread_lines", "subline")}  # noqa: E731
    assert strip(with_line[mini.GROW]) == strip(without_mill[mini.GROW])


# ---- 3. MILL-4 self-test ------------------------------------------------------------------------------------------

def _body(*lines):
    return {"rows": [{"category": "GROW_REVENUE", "thread_lines": list(lines)},
                     {"category": "OPTIMIZE_COST", "thread_lines": []}]}


GOOD = {
    "MONITORING": _line(_fact(_view("RESOLVED_MONITORING", checked=4))),
    "CLOSED": _line(_fact(_view("CLOSED"))),
    "RECURRED": _line(_fact(_view("RECURRED", seg=2, recurred=D(10, 31)), seg=1)),
}


@pytest.mark.parametrize("kind", sorted(GOOD))
def test_mill4_passes_each_kind(kind) -> None:
    assert finish.mill_thread_line(_body(GOOD[kind]), CODE) == GOOD[kind]


@pytest.mark.parametrize("bad", [
    _body(),                                                                      # no line
    _body(GOOD["MONITORING"], GOOD["CLOSED"]),                                    # two lines
    _body({**GOOD["MONITORING"], "remaining_days": 4}),                           # text not from its own fields
    _body({**GOOD["CLOSED"], "text": GOOD["CLOSED"]["text"].replace("7", "6")}),
    _body({**GOOD["RECURRED"], "effective_day": "2026-10-30"}),
    _body(_line(_fact(_view("ACTION_IN_HAND", change=D(10, 22))))),              # BEFORE_CHANGE kind
    _body({**GOOD["MONITORING"], "ref": {"kind": "ACTION"}}),                     # not the thread page
    _body({**GOOD["MONITORING"], "action_code": "ACT-000009"}),                   # another Action's line
])
def test_mill4_fails(bad) -> None:
    with pytest.raises(AssertionError):
        finish.mill_thread_line(bad, CODE)
