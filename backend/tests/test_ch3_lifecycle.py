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
    """A cause known (and recorded) at noon UTC of its effective day unless `at` says otherwise (CH3-R M1: causes
    apply in known-time order)."""
    at = at or datetime(day.year, day.month, day.day, 12, tzinfo=UTC)
    return lc.Cause(cause, kind, cid, day, at, aid, at)


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


def test_rerun_after_an_out_of_order_skip_writes_nothing():
    """L3 finding (clone ch3): a domain case COMPLETE dated (story time) before its raise (build time) is skipped as
    ILLEGAL from OPEN; on the next run the head is ACTION_IN_HAND, and the cause, dated before the head, must not
    apply then (a rerun writes 0)."""
    open_ = _ev(1, "OPEN", "OCCURRENCE", "F1", date(2026, 10, 31))
    causes = [_cause(lc.ACTION_APPLIED, "DOMAIN_CASE", "w1", date(2026, 10, 31)),
              _cause(lc.ACTION_ACCEPTED, "ACTION_EVENT", "d1", date(2026, 11, 2))]
    first = _plan([open_], causes)
    assert _states(first) == ["ACTION_IN_HAND"] and first.skipped[0]["reason"] == "ILLEGAL_TRANSITION"
    again = _plan([open_, *first.events], causes)
    assert again.events == [] and again.skipped[0]["reason"] == "BEFORE_HEAD"


def test_visibility_is_bitemporal_on_the_cause_time():
    """CH3-R D-b (0045): an event is visible at k when coalesce(cause_known_at, recorded_at) <= k, so a backfilled
    event (recorded at build time) whose cause was recorded by the story cutoff shows, and one whose cause was
    recorded at build time stays hidden."""
    build, story = T0 + timedelta(days=30), T0 + timedelta(days=5)
    early = lc.Event(1, "OPEN", "OCCURRENCE", "F1", date(2026, 10, 28), build, T0)
    late = lc.Event(2, "ACTION_IN_HAND", "ACTION_EVENT", "e1", date(2026, 10, 29), build, build)
    legacy = lc.Event(3, "CHANGE_APPLIED", "ACTION_EVENT", "e2", date(2026, 10, 30), T0)   # no cause time stored
    assert [e.seq for e in lc.visible([early, late, legacy], story)] == [1, 3]
    assert [e.seq for e in lc.visible([early, late, legacy], None)] == [1, 2, 3]
    assert lc.thread_view([early, late], OCC1, date(2026, 10, 31), story)["state"] == "OPEN"
    # The lookup reads the stored cause time from the E row's at2.
    rows = [("F", "F1", "t1", 1, 1, None, None, ADDIS, "GENERATOR_SUPPORT_CANDIDATE", "G1", None),
            ("E", "F1", "t1", 1, None, build, T0, "OPEN", "OCCURRENCE", None, date(2026, 10, 28)),
            ("E", "e1", "t1", 2, None, build, build, "ACTION_IN_HAND", "ACTION_EVENT", None, date(2026, 10, 29))]
    assert thread_lookup(rows, day=date(2026, 10, 31), known_at=story)["findings"]["f1"]["state"] == "OPEN"
    assert thread_lookup(rows, day=date(2026, 10, 31), known_at=build)["findings"]["f1"]["state"] == "ACTION_IN_HAND"


def test_planned_events_carry_their_cause_time():
    """CH3-R D-b: each planned event carries its cause fact's recorded time (written as cause_known_at); the
    INCONCLUSIVE expiry is known only once its expiry has passed."""
    accepted = lc.Cause(lc.ACTION_ACCEPTED, "ACTION_EVENT", "e1", date(2026, 10, 29), T0, "A1", T0)
    (e,) = _plan([OPEN1], [accepted]).events
    assert e.state == "ACTION_IN_HAND" and e.known_at == T0
    end = datetime(2026, 10, 20, 12, tzinfo=UTC)
    (c,) = run.causes_for_site(_inconclusive_inputs(end, end + timedelta(days=8)), load_thread_lifecycle())
    assert c.known_at == end + timedelta(days=7)
    occ = run.thread_causes({"links": {}, "events": [], "occurrences": [("f9", T0)],
                             "occurrence_known": {"f9": T0 + timedelta(days=2)}}, [],
                            {"tz": "UTC", "finding_lifecycle": {}})
    assert occ[0].cause == lc.OCCURRENCE and occ[0].known_at == T0 + timedelta(days=2)


# ---- fix round 2 (review M1, L2, L4b; CH3-R consolidated ruling) -------------------------------------------------

def _at(d, hour=12):
    return datetime(d.year, d.month, d.day, hour, tzinfo=UTC)


CHANGE = date(2026, 10, 30)
REVERIFY = [_cause(lc.ACTION_ACCEPTED, "ACTION_EVENT", "e1", date(2026, 10, 29)),
            _cause(lc.ACTION_APPLIED, "ACTION_EVENT", "e2", CHANGE),
            # VERIFIED is dated on the change's effective day (A5) but known when recorded
            _cause(lc.VERIFIED, "VERIFICATION_OUTCOME", "o1", CHANGE, at=_at(date(2026, 10, 31))),
            _cause(lc.RESOLUTION_WITHDRAWN, "ACTION_EVENT", "e3", date(2026, 11, 2)),
            _cause(lc.VERIFIED, "VERIFICATION_OUTCOME", "o2", CHANGE, at=_at(date(2026, 11, 3)))]


def _stored(events):
    """Planned events as stored: the database stamps recorded_at; cause_known_at is the cause's known time."""
    return [lc.Event(e.seq, e.state, e.cause_kind, e.cause_id, e.effective_day, e.known_at or T0, e.known_at)
            for e in events]


def test_withdraw_then_reverify_returns_to_resolved_monitoring_in_one_run():
    """CH3-R M1: causes apply in known-time order, so the re-verification (dated on the change day, known after the
    withdrawal) applies after it, and the thread reads RESOLVED_MONITORING again on later days."""
    plan = _plan([OPEN1], REVERIFY)
    assert _states(plan) == ["ACTION_IN_HAND", "CHANGE_APPLIED", "RESOLVED_MONITORING", "CHANGE_APPLIED",
                             "RESOLVED_MONITORING"]
    assert plan.skipped == []
    evs = _stored([OPEN1, *plan.events])
    for d in (date(2026, 11, 3), date(2026, 11, 10)):
        assert lc.state_on(lc.visible(evs, None), d)[0] == "RESOLVED_MONITORING"
    # as known before the re-verification was recorded, the withdrawal holds from its day
    before = lc.visible(evs, _at(date(2026, 11, 2), 18))
    assert lc.state_on(before, date(2026, 11, 2))[0] == "CHANGE_APPLIED"
    assert _plan(evs, REVERIFY).events == []   # a rerun writes nothing


def test_withdraw_then_reverify_across_two_runs():
    first = _plan([OPEN1], REVERIFY[:4])
    assert _states(first)[-1] == "CHANGE_APPLIED"
    evs = _stored([OPEN1, *first.events])
    second = _plan(evs, REVERIFY)
    assert _states(second) == ["RESOLVED_MONITORING"] and second.skipped == []
    assert _plan(_stored([*evs, *second.events]), REVERIFY).events == []


def test_cause_known_before_the_head_is_before_head_by_known_time():
    """D-a by known times: a cause known before the head's cause is BEFORE_HEAD even when its effective day is
    later; one known after the head is judged (here legal) even when its effective day is earlier."""
    head = _stored([OPEN1, *_plan([OPEN1], REVERIFY[:3]).events])   # RESOLVED_MONITORING, known 31 Oct
    late_day_early_known = _cause(lc.RESOLUTION_WITHDRAWN, "ACTION_EVENT", "e8", date(2026, 11, 5),
                                  at=_at(date(2026, 10, 30)))
    plan = _plan(head, [late_day_early_known])
    assert plan.events == [] and plan.skipped[0]["reason"] == "BEFORE_HEAD"
    early_day_late_known = _cause(lc.RESOLUTION_WITHDRAWN, "ACTION_EVENT", "e9", date(2026, 10, 20),
                                  at=_at(date(2026, 11, 5)))
    assert _states(_plan(head, [early_day_late_known])) == ["CHANGE_APPLIED"]


def _outcome(oid, outcome, superseded, at):
    return {"id": oid, "action_id": "A1", "outcome": outcome, "superseded": superseded, "recorded_at": at,
            "effective_from": _at(CHANGE), "later_end": None}


def test_superseded_outcome_gives_no_cause():
    inputs = {"tz": "UTC", "now": _at(date(2026, 11, 4)), "action_events": [], "domain_actions": [],
              "case_completions": [],
              "outcomes": [_outcome("o1", "VERIFIED", True, _at(date(2026, 10, 31))),
                           _outcome("o0", "INEFFECTIVE", True, _at(date(2026, 10, 31))),
                           _outcome("o2", "VERIFIED", False, _at(date(2026, 11, 3)))]}
    causes = run.causes_for_site(inputs, load_thread_lifecycle())
    assert [c.cause_id for c in causes] == ["o2"]


def test_earlier_segment_skip_is_pinned_and_accepted_day_is_the_first_acceptance():
    """Review L4b: a cause legal from the current state but of an Action of an earlier segment is skipped as
    EARLIER_SEGMENT. The Action's ACCEPTED day is its first acceptance (one rule with the lookup), so a
    re-acceptance after the thread reopened does not move it into segment 2."""
    evs = [OPEN1, _ev(2, "ACTION_IN_HAND", "ACTION_EVENT", "e1", date(2026, 10, 29)),
           _ev(3, "CHANGE_APPLIED", "ACTION_EVENT", "e2", date(2026, 10, 30)),
           _ev(4, "REOPENED", "VERIFICATION_OUTCOME", "o1", date(2026, 11, 2))]
    causes = [_cause(lc.ACTION_ACCEPTED, "ACTION_EVENT", "e1", date(2026, 10, 29)),
              _cause(lc.ACTION_ACCEPTED, "ACTION_EVENT", "e9", date(2026, 11, 4))]
    plan = _plan(evs, causes)
    assert plan.events == [] and [s["reason"] for s in plan.skipped] == ["EARLIER_SEGMENT"]
    assert lc.accepted_day([date(2026, 11, 4), None, date(2026, 10, 29)]) == date(2026, 10, 29)
    assert lc.accepted_day([]) is None


def test_lookup_reads_the_per_site_type_close_override():
    """Review L2: the lookup reads each Finding's Site type for the close count; the lifecycle reads it from
    `lifecycle_inputs` (`site_type`)."""
    policy = lc.LifecyclePolicy("p", 7, {"MINIGRID": 3}, 7, {"GENERATOR_SUPPORT_CANDIDATE": ("m",)})
    assert policy.close_after("MINIGRID") == 3 and policy.close_after("COLDCHAIN") == 7
    rows = [("F", "F1", "t1", 1, 1, _at(date(2026, 10, 28)), None, "UTC", "GENERATOR_SUPPORT_CANDIDATE", "G1", None,
             "MINIGRID"),
            ("E", "o1", "t1", 1, None, T0, None, "RESOLVED_MONITORING", "VERIFICATION_OUTCOME", None, CHANGE, None)]
    assert thread_lookup(rows, close_after=policy.close_after)["lifecycle"]["f1"]["close_after"] == 3
    assert thread_lookup([r[:11] for r in rows], close_after=policy.close_after)["lifecycle"]["f1"][
        "close_after"] == 7


def test_run_lifecycle_passes_the_site_type_to_the_close_rule():
    seen = []

    class Policy(lc.LifecyclePolicy):
        def close_after(self, site_type=None):
            seen.append(site_type)
            return 7

    policy = Policy("p", 7, {}, 7, {})
    reader = SimpleNamespace(lifecycle_inputs=lambda t, s: {
        "tz": "UTC", "now": T0, "site_type": "MINIGRID", "action_events": [], "outcomes": [], "domain_actions": [],
        "case_completions": [], "finding_lifecycle": {}, "snapshots": []})
    thread = {"id": "t1", "links": {}, "events": [], "occurrences": [], "mechanism": "X", "subject_ref": "G1"}
    store = SimpleNamespace(site_threads=lambda t, s: [thread], thread_head=lambda tid: (None, None),
                            append_events=lambda t, s, th, planner, pv: planner([]))
    run.run_lifecycle(reader, store, "T", "S", policy)
    assert seen == ["MINIGRID"]
