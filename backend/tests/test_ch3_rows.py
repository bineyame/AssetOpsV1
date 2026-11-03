"""CH-3 L0 (build sheet §8.1): the row effect. The Signal from the thread state, the four thread lines, the I-11
scope line, the money rule for each cost-check state (CH3-R: a per-kWh rate is never money), the Portfolio counts
and segment join, and the tuple copies pinned to `chain/lifecycle.py` (CH3-R item 4). Pure; no database."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from assetops_backend.chain import lifecycle as lc
from assetops_backend.estate import portfolio
from assetops_backend.outcomes import credit
from assetops_backend.site_outcomes import board
from assetops_backend.site_outcomes.board import ActionFact, FindingFact, SiteFacts

E = date(2026, 11, 1)   # the change's effective day


def test_board_and_portfolio_tuple_copies_match_lifecycle():
    """CH3-R item 4: the board may import only outcomes/ and the stdlib, so it holds copies; CH-5a removes them."""
    assert board.THREAD_APPLIED_STATES == lc.APPLIED_OR_LATER
    assert board.THREAD_VERIFIED_STATES == lc.VERIFIED_STATES
    assert portfolio.VERIFIED_THREAD_STATES == lc.VERIFIED_STATES
    assert portfolio.ATTENTION_THREAD_STATES == lc.ATTENTION_STATES


def _finding(state, view=None, lifecycle="SUPPORTED", seg=1):
    return FindingFact("F1", "R1", "Generator support", "GENERATOR_SUPPORT_CANDIDATE", lifecycle, None,
                       thread={"id": "t1", "occurrence_no": 1, "occurrences": 1, "segment_no": seg, "state": state,
                               "state_effective_day": None},
                       lifecycle_view=view)


def _action(seg=1, code="ACT-000001", verification="VERIFIED", **kw):
    return ActionFact("A1", code, "Trial", "F1", "R1", True, False, verification, None, thread_id="t1",
                      segment_no=seg, **kw)


def _view(**kw):
    base = {"segment_no": 1, "segment_current": 1, "change_day": E, "first_complete_after_change": None,
            "checked_days": 0, "close_after": 7, "recurred_day": None, "closed_day": None, "events": []}
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
        "state": "NOT_CREDITED", "text": "No money credited · modelled, not saved", "amounts": []}


def test_priced_total_credited_per_currency_only_when_verified_with_basis():
    def total(amount, cur, basis="7 days after the change"):
        return {**PRICED, "priced_total": {"amount": amount, "currency": cur, "basis": basis}}
    assert credit.credited(total("120", "ETB"), "VERIFIED") == (120, "ETB")
    assert credit.credited(total("120", "ETB"), "INEFFECTIVE") is None
    assert credit.credited(total("120", "ETB", basis=None), "VERIFIED") is None
    assert credit.credited(total("-5", "ETB"), "VERIFIED") is None
    out = credit.recovered_value([(total("100", "ETB"), "VERIFIED"), (total("20.5", "ETB"), "VERIFIED"),
                                  (total("3", "USD"), "VERIFIED")])
    assert out["amounts"] == [{"currency": "ETB", "amount": "120.500"}, {"currency": "USD", "amount": "3.000"}]


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
