"""CH-2 L0 (build sheet §7.1): the pure thread core - `plan_place`, `key_of` per kind, uuid5 determinism and the
Site-local `effective_day`; the in-memory registry; the board's thread match and the Portfolio thread join."""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from assetops_backend.chain import threads as th
from assetops_backend.chain.lookup import thread_lookup

T, S = UUID(int=1), UUID(int=2)
T0 = datetime(2026, 10, 17, 6, 0, tzinfo=timezone.utc)


def finding_row(domain: str = "mini_grid", **over) -> dict:
    row = {"tenant_id": T, "site_id": S, "site_tz": "Africa/Addis_Ababa", "finding_id": uuid4(), "domain": domain,
           "mechanism": "GENERATOR_SUPPORT_CANDIDATE", "matcher_version": "m/3",
           "generator_asset_id": "gen-1" if domain == "mini_grid" else None,
           "subject_asset_id": None if domain == "mini_grid" else "asset-7", "transition": "OPENED",
           "lifecycle": "SUPPORTED", "episode_start": T0, "episode_end": T0 + timedelta(hours=2),
           "created_at": T0 + timedelta(hours=3), "revision_id": uuid4()}
    row.update(over)
    return row


def src(**over) -> th.Source:
    return th.finding_source(finding_row(**over))


# --- key_of per kind ------------------------------------------------------------------------------------------

def test_key_of_mini_grid_uses_the_generator():
    s = src()
    assert th.key_of(s) == (T, S, "GENERATOR_SUPPORT_CANDIDATE", "ASSET", "gen-1")
    assert s.finding_type == "GENERATOR_SUPPORT_CANDIDATE@m/3"


@pytest.mark.parametrize("domain", ["cold_chain", "ev_charging"])
def test_key_of_cold_and_ev_use_the_subject_asset(domain):
    s = src(domain=domain, mechanism="COLD_START_FAILURE")
    assert th.key_of(s) == (T, S, "COLD_START_FAILURE", "ASSET", "asset-7")


def test_key_of_opportunity_is_the_site_headroom_thread():
    o = th.opportunity_source({"tenant_id": T, "site_id": S, "site_tz": "UTC", "opportunity_id": uuid4(),
                               "created_at": T0, "revision_id": uuid4()})
    assert th.key_of(o) == (T, S, "PRODUCTIVE_USE_HEADROOM", "SITE", "SITE")
    assert o.finding_type == "PRODUCTIVE_USE_HEADROOM@1" and o.episode_start is None


def test_a_fourth_domain_needs_only_a_mapping_row(monkeypatch):
    """DS-R1 item 3: no generator assumption outside the mini_grid mapping row."""
    with pytest.raises(KeyError):
        src(domain="water_pumping")
    monkeypatch.setitem(th.SUBJECT_COLUMN, "water_pumping", "subject_asset_id")
    assert th.key_of(src(domain="water_pumping", generator_asset_id=None))[3:] == ("ASSET", "asset-7")


# --- uuid5 determinism ----------------------------------------------------------------------------------------

def test_thread_ids_are_uuid5_of_the_key():
    key = th.key_of(src())
    assert th.thread_id_of(key) == th.thread_id_of(tuple(key)) and th.thread_id_of(key).version == 5
    assert th.thread_id_of(key) != th.thread_id_of((*key[:4], "gen-2"))


# --- effective_day --------------------------------------------------------------------------------------------

def test_effective_day_is_site_local():
    late = datetime(2026, 10, 16, 22, 30, tzinfo=timezone.utc)  # 01:30 on the 17th in Addis (UTC+3)
    assert th.effective_day(src(episode_start=late)) == date(2026, 10, 17)
    assert th.effective_day(src(episode_start=late, site_tz="UTC")) == date(2026, 10, 16)
    no_start = th.opportunity_source({"tenant_id": T, "site_id": S, "site_tz": "Africa/Addis_Ababa",
                                      "opportunity_id": uuid4(), "created_at": late, "revision_id": uuid4()})
    assert th.effective_day(no_start) == date(2026, 10, 17)


def test_opportunity_episode_is_the_study_window_in_site_time_not_build_time():
    """M1 / DS-R1: OPEN event day and opened_at come from first_day..last_day, never from created_at."""
    built = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)
    row = {"tenant_id": T, "site_id": S, "site_tz": "Africa/Addis_Ababa", "opportunity_id": uuid4(),
           "first_day": date(2026, 10, 29), "last_day": date(2026, 10, 31), "created_at": built,
           "revision_id": uuid4()}
    o = th.opportunity_source(row)
    assert o.episode_start == datetime(2026, 10, 28, 21, 0, tzinfo=timezone.utc)  # 00:00 on the 29th at UTC+3
    assert o.episode_end == datetime(2026, 10, 31, 21, 0, tzinfo=timezone.utc)    # end of the 31st
    p = th.plan_place(o, False, None)
    assert p.event["effective_day"] == date(2026, 10, 29) and p.create_thread["opened_at"] == o.episode_start
    assert p.occurrence["episode_start"] == o.episode_start and p.occurrence["episode_end"] == o.episode_end
    assert p.occurrence["time_basis"] == "story_time"
    fallback = th.plan_place(th.opportunity_source({**row, "first_day": None}), False, None)
    assert fallback.occurrence["time_basis"] == "recorded_at"  # created_at only where no story time is stored
    assert p.event["effective_day"] != th.effective_day(th.opportunity_source({**row, "first_day": None}))


# --- plan_place truth table -----------------------------------------------------------------------------------

def head(state, occ=1, events=1):
    return th.ThreadHead(UUID(int=9), occ, state, events)


def test_new_key_creates_thread_occurrence_one_and_open():
    s = src()
    p = th.plan_place(s, False, None)
    assert p.action == "PLACE" and p.thread_id == th.thread_id_of(th.key_of(s))
    assert p.create_thread["opened_at"] == s.episode_start and p.occurrence["occurrence_no"] == 1
    assert (p.event["state"], p.event["seq"], p.event["cause_kind"], p.event["cause_id"]) == (
        "OPEN", 1, "OCCURRENCE", str(s.finding_id))
    assert p.event["policy_version"] == "thread-lifecycle/1" and p.occurrence["evidence_class"] == "MEASURED"


def test_existing_occurrence_and_merged_into_are_noops():
    assert th.plan_place(src(), True, head("OPEN")).action == "NOOP"
    assert th.plan_place(src(transition="MERGED_INTO"), False, head("OPEN")).reason == "MERGED_INTO"


@pytest.mark.parametrize("state,event", [
    ("RESOLVED_MONITORING", "RECURRED"), ("CLOSED", "RECURRED"), (None, "OPEN"), ("WITHDRAWN", "OPEN"),
    ("OPEN", None), ("ACTION_IN_HAND", None), ("CHANGE_APPLIED", None), ("RECURRED", None), ("REOPENED", None)])
def test_each_thread_state(state, event):
    p = th.plan_place(src(), False, head(state, occ=2, events=3))
    assert p.action == "PLACE" and p.create_thread is None and p.occurrence["occurrence_no"] == 3
    assert (None if p.event is None else p.event["state"]) == event
    if p.event is not None:
        assert p.event["seq"] == 4


def test_split_off_finding_is_a_new_occurrence_on_the_same_thread():
    reg = th.MemoryThreads()
    first = src(created_at=T0)
    split = src(created_at=T0 + timedelta(hours=4), transition="SPLIT")
    r = th.ThreadRegistry(reg)
    r.place_all([first, split])
    assert len(reg.threads) == 1 and sorted(n for (_, n) in reg.occurrences) == [1, 2]
    assert len(reg.events) == 1  # OPEN once; the split is an added occurrence


# --- the registry over memory: Kobo-shaped recurrence, links, determinism ---------------------------------------

def kobo_sources():
    out = []
    for week in range(3):
        fid = uuid4()
        at = T0 + timedelta(days=7 * week)
        out.append(src(finding_id=fid, episode_start=at, created_at=at + timedelta(hours=3)))
        out.append(src(finding_id=fid, episode_start=at, created_at=at + timedelta(hours=5),
                       transition="SUPPORT_CHANGED"))
    return out


def test_three_findings_one_thread_and_a_second_run_writes_nothing():
    reg = th.MemoryThreads()
    report = th.ThreadRegistry(reg).place_all(kobo_sources())
    assert len(reg.threads) == 1 and len(reg.occurrences) == 3
    assert report.counts == {"NEW_THREAD": 1, "ADDED": 2, "ALREADY_PLACED": 3}


def test_shuffled_order_gives_the_same_rows():
    srcs = kobo_sources()
    a, b = th.MemoryThreads(), th.MemoryThreads()
    th.ThreadRegistry(a).place_all(srcs)
    shuffled = srcs[:]
    random.Random(7).shuffle(shuffled)
    th.ThreadRegistry(b).place_all(shuffled)
    assert (a.threads, a.occurrences, a.events) == (b.threads, b.occurrences, b.events)


def test_link_action_pending_then_linked_then_idempotent():
    reg = th.MemoryThreads()
    r = th.ThreadRegistry(reg)
    s = src()
    action = uuid4()
    assert r.link_action("MINI_TRIAL", action, s.finding_id) == th.PENDING_PLACEMENT and not reg.links
    r.place_all([s])
    assert r.link_action("MINI_TRIAL", action, s.finding_id) == th.LINKED
    assert r.link_action("MINI_TRIAL", action, s.finding_id) == th.ALREADY_LINKED and len(reg.links) == 1
    with pytest.raises(ValueError):
        r.link_action("OTHER", action, s.finding_id)


def test_lookup_rows_reduce_to_findings_and_actions():
    # CH-3 widened the row (story start, zone, mechanism, subject, events) and added state and segment.
    out = thread_lookup([("F", "ABC", "t1", 2, 3, None, None, "UTC", "M", "s", None),
                         ("A", "X", "t1", None, None, None, None, "UTC", "abc", None, None)])
    assert out["findings"] == {"abc": {"id": "t1", "occurrence_no": 2, "occurrences": 3, "segment_no": 1,
                                       "state": None, "state_effective_day": None}}
    assert out["actions"] == {"x": "t1"} and out["action_segments"] == {"x": 1}


# --- the two read-path joins ----------------------------------------------------------------------------------

def _action(aid, fid, frid, thread=None, at=T0):
    return {"action_id": aid, "source_finding_id": fid, "source_finding_revision_id": frid, "_thread_id": thread,
            "_raw": {"_selected_recorded_at": at}}


def test_portfolio_join_matches_on_thread_with_exact_fallback():
    from assetops_backend.estate.portfolio import _action_for, attach_threads

    row = {"finding_id": "f3", "finding_revision_id": "r3"}
    act = _action("a1", "f1", "r1", thread="t1")
    assert _action_for(row, [act]) is None  # no thread on the row: the exact join alone
    row["_thread"] = {"id": "t1", "occurrence_no": 3, "occurrences": 3}
    assert _action_for(row, [act]) is act
    exact = _action("a2", "f3", "r3")
    assert _action_for({"finding_id": "f3", "finding_revision_id": "r3", "_thread": None}, [exact]) is exact

    class Snap:
        def threads(self, t, fids, aids):
            return {"findings": {"f3": {"id": "t1", "occurrence_no": 3, "occurrences": 3}}, "actions": {"a1": "t1"}}

    rows, acts = [{"finding_id": "F3", "finding_revision_id": "r3"}], [{"action_id": "A1"}]
    attach_threads(Snap(), T, rows, acts)
    assert rows[0]["_thread"]["id"] == "t1" and acts[0]["_thread_id"] == "t1"
    plain = [{"finding_id": "f9"}]
    attach_threads(object(), T, plain, [])
    assert plain[0]["_thread"] is None


def test_board_lists_a_domain_action_in_hand_by_thread():
    from assetops_backend.site_outcomes import board

    shown = board.FindingFact("f2", "r2", "Start failure", "COLD_START_FAILURE", "SUPPORTED", None,
                              asset_id="asset-7")
    act = board.ActionFact("a1", "ACT-000002", "Start test", "f1", "r1", False, True, None, "/x", is_domain=True)
    facts = board.SiteFacts(domain="cold_chain", site_code="COLD-LAB-001", findings=(shown,), actions=(act,))
    before = board.assemble(facts)
    threaded = board.with_threads(facts, {"findings": {"f2": {"id": "t1", "occurrence_no": 2, "occurrences": 2}},
                                          "actions": {"a1": "t1"}})
    after = board.assemble(threaded)

    def in_hand(rows):
        return [(r["category"], i["text"], i["state_label"]) for r in rows for i in r["in_hand"]]

    assert in_hand(after) and all(label == "Open" for _, _, label in in_hand(after))
    assert in_hand(before) != in_hand(after)  # unthreaded, the origin is unresolved (suffix or other row)
    refs = [i["ref"] for r in after for i in r["issues"] if i["kind"] == "FINDING"]
    assert all(ref["thread"] == {"id": "t1", "occurrence_no": 2, "occurrences": 2} for ref in refs)
