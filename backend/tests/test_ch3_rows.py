"""CH-3 L0 (build sheet §8.1): the row effect. The Signal from the thread state, the four thread lines, the I-11
scope line, the money rule for each cost-check state (CH3-R: a per-kWh rate is never money), the Portfolio counts
and segment join, and the tuple copies pinned to `chain/lifecycle.py` (CH3-R item 4). Pure; no database."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from assetops_backend.chain import lifecycle as lc
from assetops_backend.estate import portfolio
from assetops_backend.outcomes import credit
from assetops_backend.site_outcomes import board
from assetops_backend.chain.lookup import state_classes
from assetops_backend.site_outcomes.board import ActionFact, FindingFact, SiteFacts

E = date(2026, 11, 1)   # the change's effective day


def test_board_and_portfolio_tuple_copies_match_lifecycle():
    """CH3-R item 4; CH-5a1 deleted the board's copies (the thread view carries `applied/verified/later`)."""
    assert not hasattr(board, "THREAD_APPLIED_STATES") and not hasattr(board, "THREAD_VERIFIED_STATES")
    assert portfolio.VERIFIED_THREAD_STATES == lc.VERIFIED_STATES
    assert portfolio.ATTENTION_THREAD_STATES == lc.ATTENTION_STATES


def _finding(state, view=None, lifecycle="SUPPORTED", seg=1):
    return FindingFact("F1", "R1", "Generator support", "GENERATOR_SUPPORT_CANDIDATE", lifecycle, None,
                       thread={"id": "t1", "occurrence_no": 1, "occurrences": 1, "segment_no": seg, "state": state,
                               "state_effective_day": None, **state_classes(state)},
                       lifecycle_view=view)


def _action(seg=1, code="ACT-000001", verification="VERIFIED", **kw):
    return ActionFact("A1", code, "Trial", "F1", "R1", True, False, verification, None, thread_id="t1",
                      segment_no=seg, **kw)


def _view(**kw):
    base = {"segment_no": 1, "segment_current": 1, "change_day": E, "first_complete_after_change": None,
            "checked_days": 0, "close_after": 7, "recurred_day": None, "closed_day": None, "events": [],
            "applied_states": lc.APPLIED_OR_LATER, "verified_states": lc.VERIFIED_STATES}
    base.update(kw)
    return base


def _facts(f, actions=(), day=E):
    return SiteFacts("mini", "KOBO", findings=(f,), actions=tuple(actions), day=day)


@pytest.mark.parametrize("state,open_,applied", [
    ("OPEN", True, False), ("ACTION_IN_HAND", True, False), ("CHANGE_APPLIED", True, True),
    ("RESOLVED_MONITORING", False, True), ("CLOSED", False, True), ("RECURRED", True, False),
    ("REOPENED", True, False)])
def test_signal_from_thread_state(state, open_, applied):
    assert board.finding_signal_state(_finding(state), [_action()]) == (open_, applied)


def test_signal_without_thread_keeps_exact_revision_rule():
    f = FindingFact("F1", "R1", "t", None, "SUPPORTED", None)
    assert board.finding_signal_state(f, [_action()]) == (True, True)
    assert board.finding_signal_state(f, []) == (True, False)


def test_line_before_the_change_not_judged_and_judged():
    f = _finding("CHANGE_APPLIED", _view())
    day = date(2026, 10, 31)
    assert board.thread_line(f, _facts(f, [_action()], day)) == (
        "Before the change on 1 Nov · after the change: not judged yet, no fully checked day since 1 Nov")
    judged = _finding("CHANGE_APPLIED", _view(first_complete_after_change=date(2026, 11, 3)))
    assert board.thread_line(judged, _facts(judged, [_action()], day), lambda d: "On track") == (
        "Before the change on 1 Nov · after the change: On track from 3 Nov")


def test_line_monitoring_counts_fully_checked_days_left():
    f = _finding("RESOLVED_MONITORING", _view(checked_days=2))
    assert board.thread_line(f, _facts(f, [_action()])) == (
        "Fix verified, monitoring (ACT-001) · 5 more fully checked days to close")
    none_yet = _finding("RESOLVED_MONITORING", _view())
    assert board.thread_line(none_yet, _facts(none_yet, [_action()])) == (
        "Fix verified, monitoring (ACT-001) · 7 more fully checked days to close")


def test_line_closed():
    f = _finding("CLOSED", _view(closed_day=date(2026, 11, 9)))
    assert board.thread_line(f, _facts(f, [_action()], date(2026, 11, 10))) == (
        "Fix verified and closed (ACT-001) · no return in 7 fully checked days")


def test_line_recurred_names_the_earlier_action_and_it_is_never_in_hand():
    f = _finding("RECURRED", _view(segment_no=2, segment_current=2, recurred_day=date(2026, 11, 3)), seg=2)
    facts = _facts(f, [_action(seg=1)], date(2026, 11, 4))
    assert board.thread_line(f, facts) == "Came back on 3 Nov after the fix (ACT-001)"
    assert board._earlier_segment(facts.actions[0], facts) is True


@pytest.mark.parametrize("state", ["OPEN", "ACTION_IN_HAND"])
def test_no_line_when_none_applies(state):
    f = _finding(state, _view(change_day=None))
    assert board.thread_line(f, _facts(f, [_action()])) is None


def test_four_lines_are_declared_literals():
    assert board.THREAD_BEFORE == "Before the change on {e}"
    assert board.THREAD_MONITORING.startswith("Fix verified, monitoring (")
    assert board.THREAD_CLOSED.startswith("Fix verified and closed (")
    assert board.THREAD_RECURRED == "Came back on {day} after the fix ({code})"


def test_trial_scope_line():
    hours = {"later_local": {"start": "10:00", "end": "11:00", "day": date(2026, 11, 1)}}
    assert board.trial_scope(hours) == " · checked over 10:00–11:00 on 1 Nov"
    assert board.trial_scope({}) == ""


PRICED = {"state": "MODELLED_IMPROVEMENT", "nominal": "1/24", "upper": "1/12", "currency": "ETB"}


@pytest.mark.parametrize("cc,verification,expected", [
    (PRICED, "VERIFIED", board.COST_CHANGE.format(amount="0.042–0.083", currency="ETB")),  # rate + unit
    (PRICED, "INEFFECTIVE", board.COST_NOT_CREDITED),
    ({"state": "MODELLED_NO_IMPROVEMENT", "currency": "ETB"}, "VERIFIED", board.COST_NO_CHANGE),
    ({"state": "NOT_CALCULATED", "reason": "UNKNOWN"}, "VERIFIED", board.COST_NOT_YET),
    (None, "VERIFIED", board.COST_NOT_YET),
])
def test_board_cost_line_per_cost_check_state(cc, verification, expected):
    assert board.cost_line(_action(verification=verification, cost_check=cc)) == expected


@pytest.mark.parametrize("cc,outcome", [
    (PRICED, "VERIFIED"), (PRICED, "INEFFECTIVE"), ({"state": "MODELLED_NO_IMPROVEMENT", "currency": "ETB"},
                                                      "VERIFIED"),
    ({"state": "NOT_CALCULATED"}, "VERIFIED"), (None, "VERIFIED")])
def test_per_kwh_nominal_never_produces_an_amount(cc, outcome):
    """CH3-R money unit: the per-kWh rate (`nominal`) is never credited, summed or shown as money."""
    assert credit.credited(cc, outcome) is None
    assert credit.recovered_value([(cc, outcome), (cc, outcome)]) == {
        "state": "NOT_CREDITED", "text": "No money credited · modelled, not saved", "items": []}


def _total(amount, cur, basis="7 days after the change", key="o1"):
    return {**PRICED, "outcome_id": key, "priced_total": {"amount": amount, "currency": cur, "basis": basis}}


def test_priced_total_credited_per_result_only_when_verified_with_basis():
    total = _total
    assert credit.credited(total("120", "ETB"), "VERIFIED") == ((120, 1), "ETB")
    assert credit.credited(total("1/24", "ETB"), "VERIFIED") == ((1, 24), "ETB")
    assert credit.credited(total("abc", "ETB"), "VERIFIED") is None
    assert credit.credited(total("1/0", "ETB"), "VERIFIED") is None
    assert credit.recovered_value([(total("1/2000", "ETB"), "VERIFIED")])["items"][0]["amount"] == "0.000"  # half-even
    assert credit.recovered_value([(total("3/2000", "ETB"), "VERIFIED")])["items"][0]["amount"] == "0.002"
    assert credit.credited(total("120", "ETB"), "INEFFECTIVE") is None
    assert credit.credited(total("120", "ETB", basis=None), "VERIFIED") is None
    assert credit.credited(total("-5", "ETB"), "VERIFIED") is None
    out = credit.recovered_value([(total("100", "ETB", key="o1"), "VERIFIED"),
                                  (total("20.5", "ETB", key="o2"), "VERIFIED"),
                                  (total("3", "USD", key="o3"), "VERIFIED")])
    assert out == {"state": "CREDITED", "text": None, "items": [
        {"key": "o1", "currency": "ETB", "amount": "100.000", "basis": "7 days after the change"},
        {"key": "o2", "currency": "ETB", "amount": "20.500", "basis": "7 days after the change"},
        {"key": "o3", "currency": "USD", "amount": "3.000", "basis": "7 days after the change"}]}


def test_recovered_value_never_sums_two_items_in_one_currency():
    """FUEL-1 A2 (owner: never a combined savings total): two credited items in the same currency stay two items,
    and no field anywhere in the result equals their sum."""
    out = credit.recovered_value([(_total("4.125", "USD", "TRIAL_HOUR_MODELLED_FUEL", "o1"), "VERIFIED"),
                                  (_total("17", "USD", "ESTIMATED_SALES_AT_DECLARED_PRICE", "o2"), "VERIFIED")])
    assert [(i["key"], i["amount"], i["basis"]) for i in out["items"]] == [
        ("o1", "4.125", "TRIAL_HOUR_MODELLED_FUEL"), ("o2", "17.000", "ESTIMATED_SALES_AT_DECLARED_PRICE")]
    assert "amounts" not in out and set(out) == {"state", "text", "items"}

    def leaves(value):
        if isinstance(value, dict):
            for v in value.values():
                yield from leaves(v)
        elif isinstance(value, list):
            for v in value:
                yield from leaves(v)
        else:
            yield value
    total = Decimal("4.125") + Decimal("17")
    numeric = [Decimal(v) for v in leaves(out) if isinstance(v, str) and v.replace(".", "", 1).isdigit()]
    assert numeric and total not in numeric, numeric


def test_recovered_value_fails_loud_on_two_items_with_one_key():
    with pytest.raises(ValueError, match="share the key"):
        credit.recovered_value([(_total("1", "USD", key="o1"), "VERIFIED"), (_total("2", "USD", key="o1"), "VERIFIED")])
    with pytest.raises(ValueError, match="no outcome id"):
        credit.recovered_value([(_total("1", "USD", key=None), "VERIFIED")])


def test_portfolio_counts_from_thread_states():
    rows = [{"site_id": "S1", "_thread": {"id": "t1", "state": "RESOLVED_MONITORING"}},
            {"site_id": "S1", "_thread": {"id": "t1", "state": "RESOLVED_MONITORING"}},   # same thread once
            {"site_id": "S1", "_thread": {"id": "t2", "state": "OPEN"}},
            {"site_id": "S2", "_thread": {"id": "t3", "state": "ACTION_IN_HAND"}},
            {"site_id": "S3", "_thread": {"id": "t4", "state": "RECURRED"}},
            {"site_id": "S4", "_thread": {"id": "t5", "state": "CLOSED"}},
            {"site_id": "S5", "_thread": None}]
    assert portfolio.thread_progress(rows) == {"verified_resolution_count": 2, "priority_site_count": 2}
    assert portfolio.thread_progress([{"site_id": "S1", "_thread": None}]) is None


def _a_row(aid, seg, finding="F1", rev="R1"):
    return {"action_id": aid, "source_finding_id": finding, "source_finding_revision_id": rev, "_thread_id": "t1",
            "_segment_no": seg, "_raw": {"_selected_recorded_at": datetime(2026, 11, 1, tzinfo=timezone.utc)}}


def test_portfolio_action_join_respects_segment():
    later = {"finding_id": "F4", "finding_revision_id": "R4", "_thread": {"id": "t1", "segment_no": 2}}
    assert portfolio._action_for(later, [_a_row("A1", 1)]) is None
    assert portfolio._action_for(later, [_a_row("A2", 2, "F9", "R9")])["action_id"] == "A2"


# ---- fix round 2 ------------------------------------------------------------------------------------------------

def test_thread_wire_keys_come_with_the_view():
    """Review L4a / CH-5a1 §A5: the board holds no copy of the wire keys; the thread view hands it PUBLIC_KEYS."""
    from assetops_backend.chain.lookup import PUBLIC_KEYS
    assert not hasattr(board, "THREAD_WIRE_KEYS") and state_classes("OPEN")["wire_keys"] == PUBLIC_KEYS


def _work_facts(f, actions=(), day=date(2026, 11, 1)):
    lo = datetime(2026, 10, 2, tzinfo=timezone.utc)
    from assetops_backend.outcomes.catalogue import MINI
    return SiteFacts(MINI, "KOBO", findings=(f,), actions=tuple(actions), day=day,
                     work_window=(lo, datetime(2026, 11, 2, tzinfo=timezone.utc)))


def _out_of_day(state, view, *, in_work=True):
    return FindingFact("F1", "R1", "Generator support", "GENERATOR_SUPPORT_CANDIDATE", "SUPPORTED", None,
                       thread={"id": "t1", "occurrence_no": 1, "occurrences": 1, "segment_no": 1, "state": state,
                               "state_effective_day": None, "state_day": None, **state_classes(state)},
                       lifecycle_view=view, in_window=False, in_work_window=in_work)


@pytest.mark.parametrize("state", ["RESOLVED_MONITORING", "CLOSED", "RECURRED"])
def test_thread_line_is_thread_level_after_the_finding_left_the_day(state):
    """CH3-R M3: the thread's Finding is out of the overview day but in the 31-day work window: its line shows."""
    f = _out_of_day(state, _view())
    assert board.thread_line_findings(_work_facts(f, [_action()])) == [f]


def test_thread_line_not_shown_out_of_the_work_window_or_in_other_states():
    out = _out_of_day("RESOLVED_MONITORING", _view(), in_work=False)
    assert board.thread_line_findings(_work_facts(out)) == []                      # no occurrence, no Action
    assert board.thread_line_findings(_work_facts(out, [_action()])) == [out]      # an Action of it is in window
    applied = _out_of_day("CHANGE_APPLIED", _view())
    assert board.thread_line_findings(_work_facts(applied, [_action()])) == []
    f = _out_of_day("RESOLVED_MONITORING", _view())
    assert board.thread_line_findings(SiteFacts("cold", "C", findings=(f,), actions=(_action(),))) == []


def test_mini_board_day_after_the_episode_carries_fix_verified_monitoring():
    """CH3-R M3: a board day after the Finding's episode: the row it moves (primary outcome) carries the line in
    its subline, and the Earlier entry still lists the Action."""
    f = _out_of_day("RESOLVED_MONITORING", _view(checked_days=0))
    a = _action(verification="VERIFIED")
    rows = board.assemble(_work_facts(f, [a]))
    sub = [r["subline"] for r in rows if r.get("subline")]
    assert any("Fix verified, monitoring (ACT-001) · 7 more fully checked days to close" in x for x in sub), sub
    assert any(e["text"].startswith("ACT-001") for r in rows for e in r.get("earlier") or ()), rows


def test_portfolio_counts_are_per_thread_state_independent_of_row_order():
    """Review L3: after a RECURRED, segment 1 reads RESOLVED_MONITORING and segment 2 RECURRED; the thread counts
    once, by its current (highest-segment) state, in either row order."""
    rows = [{"site_id": "S1", "_thread": {"id": "t1", "segment_no": 1, "occurrence_no": 1,
                                          "state": "RESOLVED_MONITORING"}},
            {"site_id": "S1", "_thread": {"id": "t1", "segment_no": 2, "occurrence_no": 4, "state": "RECURRED"}}]
    want = {"verified_resolution_count": 0, "priority_site_count": 1}
    assert portfolio.thread_progress(rows) == want
    assert portfolio.thread_progress(list(reversed(rows))) == want


def test_portfolio_action_segment_is_read_at_the_rows_cutoff():
    """Review side-question 1: the Action segment compared with a row's segment is the one read at its cutoff."""
    k1, k2 = datetime(2026, 10, 31, tzinfo=timezone.utc), datetime(2026, 11, 4, tzinfo=timezone.utc)
    a = {**_a_row("A1", 2), "_segment_at": {k1: 1, k2: 2}}
    row = {"finding_id": "F4", "finding_revision_id": "R4", "_thread": {"id": "t1", "segment_no": 1},
           "_thread_cutoff": k1}
    assert portfolio._action_for(row, [a])["action_id"] == "A1"
    assert portfolio._action_for({**row, "_thread_cutoff": k2}, [a]) is None


def test_attach_threads_reads_actions_in_every_cutoff_group():
    k, cold_k = datetime(2026, 11, 4, tzinfo=timezone.utc), datetime(2026, 10, 31, tzinfo=timezone.utc)
    calls = []

    def port(t, fids, aids, **kw):
        calls.append((tuple(fids), tuple(aids), kw.get("known_at")))
        seg = 1 if kw.get("known_at") == cold_k else 2
        return {"findings": {f.lower(): {"id": "t1", "segment_no": seg} for f in fids},
                "actions": {a.lower(): "t1" for a in aids}, "action_segments": {a.lower(): seg for a in aids}}

    snap = type("S", (), {"threads": staticmethod(port)})()
    # CH-5a2 B3 (R7): the cold Site's cutoff comes from the one Site -> cutoff map, not a per-row value.
    f_rows = [{"finding_id": "FM", "site_code": "MG"}, {"finding_id": "FC", "site_code": "COLD"}]
    a_rows = [{"action_id": "A1"}]
    req = type("R", (), {"to": k, "known_at": None})()
    portfolio.attach_threads(snap, "t", f_rows, a_rows, req, k, {"MG": None, "COLD": cold_k})
    # D-E4.2 (CH6b2-R2): the cold Site's evidence cutoff no longer bounds the lifecycle; one group at k.
    assert calls == [(("FM", "FC"), ("A1",), k)]
    assert a_rows[0]["_segment_no"] == 2 and a_rows[0]["_segment_at"] == {k: 2}
    assert all(r["_thread_cutoff"] == k for r in f_rows)


# CH-5a2 B4: the structured ThreadLine; its text is the CH-3 literal thread_line renders.
def test_thread_line_items_are_structured_and_their_text_is_the_line():
    ref = {"kind": "THREAD", "site": "KOBO", "id": "t1"}
    judged = _finding("CHANGE_APPLIED", _view(first_complete_after_change=date(2026, 11, 3)))
    facts = _facts(judged, [_action()], date(2026, 10, 31))
    item = board.thread_line_item(judged, facts, lambda d: ("ON_TRACK", "on track"))
    assert item == {"kind": "BEFORE_CHANGE", "thread_id": "t1", "action_code": "ACT-000001",
                    "effective_day": "2026-11-01", "after": {"state": "ON_TRACK", "day": "2026-11-03"},
                    "remaining_days": None, "clean_days": None, "ref": ref,
                    "text": "Before the change on 1 Nov · after the change: on track from 3 Nov"}
    assert board.thread_line_item(judged, facts)["after"] is None  # not judged: no after
    assert board.thread_line_item(judged, facts)["text"] == board.thread_line(judged, facts)
    mon = _finding("RESOLVED_MONITORING", _view(checked_days=2))
    m = board.thread_line_item(mon, _facts(mon, [_action()]))
    assert (m["kind"], m["remaining_days"], m["clean_days"], m["text"]) == (
        "MONITORING", 5, None, board.thread_line(mon, _facts(mon, [_action()])))
    closed = _finding("CLOSED", _view(closed_day=date(2026, 11, 9)))
    c = board.thread_line_item(closed, _facts(closed, [_action()], date(2026, 11, 10)))
    assert (c["kind"], c["clean_days"], c["remaining_days"]) == ("CLOSED", 7, None)
    rec = _finding("RECURRED", _view(segment_no=2, segment_current=2, recurred_day=date(2026, 11, 3)), seg=2)
    r = board.thread_line_item(rec, _facts(rec, [_action(seg=1)], date(2026, 11, 4)))
    assert (r["kind"], r["effective_day"], r["action_code"], r["ref"]) == ("RECURRED", "2026-11-03", "ACT-000001", ref)
    none = _finding("OPEN", _view(change_day=None))
    assert board.thread_line_item(none, _facts(none, [_action()])) is None
