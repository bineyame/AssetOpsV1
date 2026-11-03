"""CH-3 L0 (build sheet §8.1): the thread state machine, effective days, INCONCLUSIVE expiry, CLEAN_DAYS, segments
and the one "fully checked day" rule (CH3-R). Pure; no database."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from assetops_backend.chain import lifecycle as lc
from assetops_backend.chain import lifecycle_run as run
from assetops_backend.chain.adapters.file_chain_config import load_thread_lifecycle
from assetops_backend.chain.lookup import thread_lookup

UTC = timezone.utc
ADDIS = "Africa/Addis_Ababa"
T0 = datetime(2026, 10, 25, 9, 0, tzinfo=UTC)


def _ev(seq, state, kind, cid, day, at=None):
    return lc.Event(seq, state, kind, cid, day, at or T0)


def _cause(cause, kind, cid, day, aid="A1", at=None):
    return lc.Cause(cause, kind, cid, day, at or T0, aid)


OPEN1 = _ev(1, "OPEN", "OCCURRENCE", "F1", date(2026, 10, 28))
OCC1 = lc.Occurrence("F1", date(2026, 10, 28))
ACTIONS = {"A1": "F1"}


def _plan(events, causes, clean=(), close_after=7, actions=ACTIONS, occs=(OCC1,)):
    return lc.plan_lifecycle("T1", events, occs, actions, causes, close_after=close_after, clean_days=clean)


def _states(plan):
    return [e.state for e in plan.events]


def test_policy_file_loads_declared_values():
    p = load_thread_lifecycle()
    assert p.policy_version == "thread-lifecycle/1"
    assert p.close_after() == 7 and p.inconclusive_expiry_days == 7
    assert p.measures_for("GENERATOR_SUPPORT_CANDIDATE") == ("avoidable_gen_min",)
    assert p.measures_for("UNKNOWN") == ()


def test_accept_apply_verify_withdraw_close_chain():
    causes = [_cause(lc.ACTION_ACCEPTED, "ACTION_EVENT", "e1", date(2026, 10, 29)),
              _cause(lc.ACTION_APPLIED, "ACTION_EVENT", "e2", date(2026, 10, 30)),
              _cause(lc.VERIFIED, "VERIFICATION_OUTCOME", "o1", date(2026, 10, 31))]
    plan = _plan([OPEN1], causes)
    assert _states(plan) == ["ACTION_IN_HAND", "CHANGE_APPLIED", "RESOLVED_MONITORING"]
    assert plan.skipped == []
    withdrawn = _plan([OPEN1, *plan.events], [*causes, _cause(lc.RESOLUTION_WITHDRAWN, "ACTION_EVENT", "e3",
                                                             date(2026, 11, 1))])
    assert _states(withdrawn) == ["CHANGE_APPLIED"]


@pytest.mark.parametrize("cause", [lc.INEFFECTIVE, lc.INCONCLUSIVE_EXPIRED])
def test_ineffective_and_expired_reopen(cause):
    evs = [OPEN1, _ev(2, "ACTION_IN_HAND", "ACTION_EVENT", "e1", date(2026, 10, 29)),
           _ev(3, "CHANGE_APPLIED", "ACTION_EVENT", "e2", date(2026, 10, 30))]
    plan = _plan(evs, [_cause(cause, "VERIFICATION_OUTCOME", "o1", date(2026, 11, 2))])
    assert _states(plan) == ["REOPENED"]


def test_illegal_transition_skipped_and_reported_later_causes_still_apply():
    causes = [_cause(lc.ACTION_APPLIED, "ACTION_EVENT", "e2", date(2026, 10, 29)),   # APPLIED from OPEN: illegal
              _cause(lc.ACTION_ACCEPTED, "ACTION_EVENT", "e1", date(2026, 10, 30))]
    plan = _plan([OPEN1], causes)
    assert _states(plan) == ["ACTION_IN_HAND"]
    assert plan.skipped == [{"thread_id": "T1", "cause": lc.ACTION_APPLIED, "cause_id": "e2", "from_state": "OPEN",
                             "reason": "ILLEGAL_TRANSITION"}]


def test_idempotent_on_cause_kind_and_id():
    causes = [_cause(lc.ACTION_ACCEPTED, "ACTION_EVENT", "e1", date(2026, 10, 29))]
    first = _plan([OPEN1], causes)
    again = _plan([OPEN1, *first.events], causes)
    assert again.events == [] and again.skipped == []


def test_action_not_on_thread_is_skipped():
    plan = _plan([OPEN1], [_cause(lc.ACTION_ACCEPTED, "ACTION_EVENT", "e9", date(2026, 10, 29), aid="A9")])
    assert plan.events == [] and plan.skipped[0]["reason"] == "ACTION_NOT_ON_THREAD"


def test_support_lost_withdraws_only_without_an_action():
    lost = [_cause(lc.SUPPORT_LOST, "SUPPORT_LOST", "r1", date(2026, 10, 30), aid=None)]
    assert _states(_plan([OPEN1], lost, actions={})) == ["WITHDRAWN"]
    guarded = _plan([OPEN1], lost)
    assert guarded.events == [] and guarded.skipped[0]["reason"] == "ACTION_ON_THREAD"


def test_effective_day_addis_vs_utc():
    at = datetime(2026, 10, 31, 22, 30, tzinfo=UTC)          # 01:30 on 1 Nov in Addis (UTC+3)
    assert lc.local_day(at, ADDIS) == date(2026, 11, 1)
    assert lc.local_day(at, "UTC") == date(2026, 10, 31)
    inputs = {"tz": ADDIS, "now": at, "outcomes": [], "domain_actions": [], "case_completions": [],
              "action_events": [{"id": "e1", "kind": "APPLIED", "action_id": "A1", "recorded_at": at + timedelta(
                  days=3), "effective_from": at}]}
    (c,) = run.causes_for_site(inputs, load_thread_lifecycle())
    assert c.cause == lc.ACTION_APPLIED and c.effective_day == date(2026, 11, 1)   # change effective_from, local


def _inconclusive_inputs(later_end, now):
    return {"tz": "UTC", "now": now, "action_events": [], "domain_actions": [], "case_completions": [],
            "outcomes": [{"id": "o1", "action_id": "A1", "outcome": "INCONCLUSIVE", "superseded": False,
                          "recorded_at": later_end, "later_end": later_end}]}


def test_inconclusive_expires_after_later_end_plus_seven_days():
    policy = load_thread_lifecycle()
    end = datetime(2026, 10, 20, 12, tzinfo=UTC)
    assert run.causes_for_site(_inconclusive_inputs(end, end + timedelta(days=6)), policy) == []
    (c,) = run.causes_for_site(_inconclusive_inputs(end, end + timedelta(days=8)), policy)
    assert c.cause == lc.INCONCLUSIVE_EXPIRED and c.cause_id == "o1" and c.effective_day == date(2026, 10, 27)


def _snap(day, grade, measure="avoidable_gen_min", ref="G1", kind="ASSET"):
    return SimpleNamespace(local_day=day, grade=grade, measure=measure, subject_ref=ref, subject_kind=kind)


def test_clean_days_close_after_n_and_partial_days_never_count():
    verified = [OPEN1, _ev(2, "ACTION_IN_HAND", "ACTION_EVENT", "e1", date(2026, 10, 29)),
                _ev(3, "CHANGE_APPLIED", "ACTION_EVENT", "e2", date(2026, 10, 30)),
                _ev(4, "RESOLVED_MONITORING", "VERIFICATION_OUTCOME", "o1", date(2026, 11, 1))]
    days = [date(2026, 11, 1) + timedelta(days=i) for i in range(1, 9)]
    rows = [_snap(d, "PARTIAL" if i == 2 else "COMPLETE") for i, d in enumerate(days)]
    clean = lc.fully_checked_days(rows, "G1", ("avoidable_gen_min",))
    assert days[2] not in clean and len(clean) == 7
    plan = _plan(verified, [], clean=clean, close_after=7)
    assert _states(plan) == ["CLOSED"]
    assert plan.events[0].effective_day == days[-1] and plan.events[0].cause_id == f"T1:{days[-1].isoformat()}"
    all_partial = lc.fully_checked_days([_snap(d, "PARTIAL") for d in days], "G1", ("avoidable_gen_min",))
    assert all_partial == set() and _plan(verified, [], clean=all_partial).events == []


def test_one_fully_checked_day_rule_for_close_and_count():
    """CH3-R: the close rule and the board's "k more" count use the same days; an occurrence-start day is not one."""
    days = [date(2026, 11, 2), date(2026, 11, 3), date(2026, 11, 4)]
    rows = [_snap(d, "COMPLETE") for d in days]
    starts = [date(2026, 11, 3)]
    one = lc.fully_checked_days(rows, "G1", ("avoidable_gen_min",), starts)
    assert one == {date(2026, 11, 2), date(2026, 11, 4)}
    thread = {"mechanism": "GENERATOR_SUPPORT_CANDIDATE", "subject_ref": "G1",
              "occurrences": [("F1", datetime(2026, 11, 3, 6, tzinfo=UTC))]}
    assert run.thread_clean_days(thread, {"tz": "UTC", "snapshots": rows}, load_thread_lifecycle()) == one
    evs = [OPEN1, _ev(2, "RESOLVED_MONITORING", "VERIFICATION_OUTCOME", "o1", date(2026, 11, 1))]
    view = lc.thread_view(evs, OCC1, date(2026, 11, 4), None, one, 7)
    assert view["checked_days"] == len(one) == 2


def test_complete_days_needs_every_measure_and_matches_subject():
    rows = [_snap(date(2026, 11, 2), "COMPLETE"), _snap(date(2026, 11, 2), "COMPLETE", ref="OTHER"),
            _snap(date(2026, 11, 3), "COMPLETE", measure="x"), _snap(date(2026, 11, 4), "COMPLETE", kind="SITE",
                                                                        ref="S")]
    # a SITE-kind row counts for any subject of the Site; another asset's row does not
    assert lc.complete_days(rows, "G1", ("avoidable_gen_min",)) == {date(2026, 11, 2), date(2026, 11, 4)}
    assert lc.complete_days(rows, "G1", ("avoidable_gen_min", "x")) == set()
    assert lc.complete_days(rows, "G1", ()) == set()


def _occ4_events():
    return [OPEN1, _ev(2, "ACTION_IN_HAND", "ACTION_EVENT", "e1", date(2026, 10, 29)),
            _ev(3, "CHANGE_APPLIED", "ACTION_EVENT", "e2", date(2026, 10, 30)),
            _ev(4, "RESOLVED_MONITORING", "VERIFICATION_OUTCOME", "o1", date(2026, 11, 1)),
            _ev(5, "RECURRED", "OCCURRENCE", "F4", date(2026, 11, 3))]


def test_occurrence_four_recurs_with_no_in_hand_action():
    """§3 test: occurrences 1-3, VERIFIED, then occurrence 4: RECURRED, and ACT-001 is in the earlier segment."""
    evs = _occ4_events()
    v4 = lc.thread_view(evs, lc.Occurrence("F4", date(2026, 11, 3)), date(2026, 11, 3), None)
    assert v4["segment_no"] == 2 and v4["state"] == "RECURRED" and v4["recurred_day"] == date(2026, 11, 3)
    for occ in ("F1", "F2", "F3"):
        v = lc.thread_view(evs, lc.Occurrence(occ, date(2026, 10, 28)), date(2026, 11, 3), None)
        assert v["segment_no"] == 1 and v["state"] == "RESOLVED_MONITORING"
    assert lc.action_segment(evs, OCC1, date(2026, 10, 29)) == 1 < v4["segment_current"] == 2
    # a later VERIFIED outcome of the earlier-segment Action does not move segment 2
    plan = _plan(evs, [_cause(lc.VERIFIED, "VERIFICATION_OUTCOME", "o2", date(2026, 11, 4))],
                 occs=(OCC1, lc.Occurrence("F4", date(2026, 11, 3))))
    assert plan.events == [] and plan.skipped[0]["reason"] in ("EARLIER_SEGMENT", "ILLEGAL_TRANSITION")


def test_occurrence_cause_after_verified_day_recurs_but_not_on_or_before():
    evs = _occ4_events()[:4]
    occs = (OCC1, lc.Occurrence("F4", date(2026, 11, 3)))
    same = _plan(evs, [lc.Cause(lc.OCCURRENCE, "OCCURRENCE", "F4", date(2026, 11, 1), T0)], occs=occs)
    assert same.events == []
    later = _plan(evs, [lc.Cause(lc.OCCURRENCE, "OCCURRENCE", "F4", date(2026, 11, 3), T0)], occs=occs)
    assert _states(later) == ["RECURRED"]


def test_state_on_day_and_known_at():
    evs = _occ4_events()[:4]
    assert lc.state_on(evs, date(2026, 10, 31)) == ("CHANGE_APPLIED", date(2026, 10, 30))
    assert lc.state_on(evs, date(2026, 11, 1)) == ("RESOLVED_MONITORING", date(2026, 11, 1))
    late = [*evs[:3], _ev(4, "RESOLVED_MONITORING", "VERIFICATION_OUTCOME", "o1", date(2026, 11, 1),
                          at=T0 + timedelta(days=30))]
    assert lc.thread_view(late, OCC1, date(2026, 11, 1), T0 + timedelta(days=1))["state"] == "CHANGE_APPLIED"


def test_lookup_day_at_reads_each_site_local_day():
    """CH3-R (AG-27): the Portfolio reads each Finding on its own Site's local day holding the window's last
    instant, as the board does, never on the UTC day."""
    events = [("E", "o1", "t1", 1, None, T0, None, "OPEN", "OCCURRENCE", None, date(2026, 10, 28)),
              ("E", "o2", "t1", 2, None, T0, None, "RESOLVED_MONITORING", "VERIFICATION_OUTCOME", None,
               date(2026, 11, 1))]
    rows = [("F", "F1", "t1", 1, 1, None, None, ADDIS, "GENERATOR_SUPPORT_CANDIDATE", "G1", None), *events]
    last = datetime(2026, 10, 31, 22, 0, tzinfo=UTC)          # UTC 31 Oct, Addis 1 Nov
    by_utc = thread_lookup(rows, day=last.date())
    by_site = thread_lookup(rows, day_at=last)
    assert by_utc["findings"]["f1"]["state"] == "OPEN"
    assert by_site["findings"]["f1"]["state"] == "RESOLVED_MONITORING"
