"""DEMO-SPARSE U2/U4: the sparse story calendar resolver (`tools/demo_story_days.py`), pure and fast."""

from __future__ import annotations

import copy
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import demo_story_days as sd  # noqa: E402

S = datetime(2026, 10, 29, tzinfo=timezone.utc)


def _codes(doc, s=S, **kw):
    with pytest.raises(sd.StoryDaysError) as err:
        sd.resolve(doc, s, **kw)
    return err.value.error_code


def test_offsets_resolve_against_s_and_the_entry_day():
    runs = {(r.site, r.offset): r for r in sd.resolve(sd.load(), S)}
    normal = runs[("kobo", -28)]
    assert normal.day == "2026-10-01" and normal.kind == "normal"
    assert normal.start == datetime(2026, 10, 1, 3, tzinfo=timezone.utc)
    assert normal.end == datetime(2026, 10, 1, 11, tzinfo=timezone.utc)
    assert normal.received_at == datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    late = runs[("kobo", -3)]
    assert late.as_kind == "normal" and late.scenario == normal.scenario
    assert late.received_at == datetime(2026, 10, 28, 12, 30, tzinfo=timezone.utc)  # after S-1's 12:00 delivery
    gap = runs[("kobo", -10)]
    assert gap.kind == "missing" and not gap.has_run and gap.epoch is None and gap.scenario is None


def test_build_order_is_by_received_at_with_fresh_epochs():
    runs = sd.resolve(sd.load(), S)
    received = [r.received_at for r in runs if r.has_run]
    assert received == sorted(received)
    # DD1a1-R8: an isolated day keeps its build-order `day-<n>`; the Kobo S-1/S/S+1 stream shares its first day's
    story = [r for r in runs if r.has_run and not r.complement_of]
    stream = {r.day for r in story if r.site == "kobo" and r.offset in (-1, 0, 1)}
    assert len(stream) == 3 and len({r.epoch for r in story if r.day in stream and r.site == "kobo"}) == 1
    assert [r.epoch for r in story if not (r.site == "kobo" and r.day in stream)] == [
        f"day-{n}" for n, r in enumerate(story, 1) if not (r.site == "kobo" and r.day in stream)]
    kobo = [r for r in runs if r.site == "kobo"]
    late = next(i for i, r in enumerate(kobo) if r.kind == "late")
    before = next(i for i, r in enumerate(kobo) if r.kind == "trial-before")
    assert late < before
    assert datetime(2026, 10, 28, 12, tzinfo=timezone.utc) <= kobo[late].received_at < kobo[before].received_at
    # the late S-3 day sorts after the S-1 12:00 boundary and before the S 12:00 trial-before delivery
    assert kobo[late].received_at > S - timedelta(days=1, hours=1)


@pytest.mark.parametrize("s", [S, datetime(2027, 3, 1, tzinfo=timezone.utc)])
def test_default_file_validates_on_relative_dates(s):
    db_now = s + timedelta(days=2, hours=4)
    installs = {"kobo": s + timedelta(days=-29, hours=11), "cold": s + timedelta(days=-26, hours=6),
                "ev": s + timedelta(days=-26, hours=6, minutes=30)}
    runs = sd.resolve(sd.load(), s, db_now=db_now, installs=installs)
    assert {r.site for r in runs} == {"kobo", "cold", "ev"}
    assert sum(r.has_run for r in runs if r.site == "kobo") == 8


@pytest.mark.parametrize("s", [S, datetime(2026, 11, 3, tzinfo=timezone.utc), datetime(2027, 3, 1, tzinfo=timezone.utc)])
def test_ev_days_fall_back_to_the_ruled_tuesday(s):
    """ev-charger/1 runs only on a TUESDAY (`host/ev_publication.py` `ev_parameters`): each EV day is the Tuesday on
    or before its listed day; other Sites keep the listed day."""
    runs = sd.resolve(sd.load(), s)
    ev = {r.kind: r for r in runs if r.site == "ev"}
    for r in ev.values():
        assert datetime.fromisoformat(r.day).weekday() == 1 and r.start.weekday() == 1, (r.kind, r.day)
    assert -6 <= ev["fault"].offset <= 0 and ev["normal"].offset == ev["fault"].offset - 7
    assert s.weekday() != 1 or ev["fault"].offset == 0
    cold = {r.kind: r for r in runs if r.site == "cold"}
    assert cold["failure"].offset == 0 and cold["normal"].offset == -7
    current = [r for r in runs]
    nxt = sd.plan_add_day(sd.load(), current, "ev", "normal", s, s + timedelta(days=30))
    assert nxt.offset == ev["fault"].offset + 7 and datetime.fromisoformat(nxt.day).weekday() == 1


def test_unknown_kind():
    doc = copy.deepcopy(sd.load())
    doc["sites"]["kobo"].append({"day": "S-5d", "kind": "sunny"})
    assert _codes(doc) == "UNKNOWN_KIND"
    doc = copy.deepcopy(sd.load())
    doc["sites"]["ev"].append({"day": "S-5d", "kind": "overuse"})
    assert _codes(doc) == "UNKNOWN_KIND"
    doc = copy.deepcopy(sd.load())
    doc["sites"]["kobo"][5].pop("as")
    assert _codes(doc) == "UNKNOWN_KIND"


def test_duplicate_day():
    doc = copy.deepcopy(sd.load())
    doc["sites"]["kobo"].append({"day": "S-14d", "kind": "normal"})
    assert _codes(doc) == "DUPLICATE_DAY"


def test_duplicate_received_at():
    # S-3 late (D+2d) set back to 12:00 shares S-1 normal's 12:00 delivery; acceptance is counted by received_at
    doc = copy.deepcopy(sd.load())
    doc["kinds"]["kobo"]["late"]["received_at"] = "D+2d 12:00"
    assert _codes(doc) == "DUPLICATE_RECEIVED_AT"


@pytest.mark.parametrize("change", ["drop_after", "after_not_next_day", "two_before"])
def test_trial_pair_invalid(change):
    doc = copy.deepcopy(sd.load())
    kobo = doc["sites"]["kobo"]
    if change == "drop_after":
        kobo[:] = [e for e in kobo if e["kind"] != "trial-after"]
    elif change == "after_not_next_day":
        next(e for e in kobo if e["kind"] == "trial-after")["day"] = "S+2d"
    else:
        kobo.append({"day": "S-2d", "kind": "trial-before"})
    assert _codes(doc) == "TRIAL_PAIR_INVALID"


def test_day_before_install():
    installs = {"kobo": S + timedelta(days=-28, hours=2, minutes=30)}  # S-28 03:00 run is < install + 1 h
    assert _codes(sd.load(), installs=installs) == "DAY_BEFORE_INSTALL"
    sd.resolve(sd.load(), S, installs={"kobo": S + timedelta(days=-29, hours=11, minutes=30)})
    # Q1 ruling: every run knows its Foundation at or after install + 30 min (trial-before knows it at D-6d 12:00)
    doc = copy.deepcopy(sd.load())
    doc["sites"]["kobo"] = [e for e in doc["sites"]["kobo"] if e["kind"].startswith("trial-")]
    assert _codes(doc, installs={"kobo": S + timedelta(days=-6, hours=11, minutes=31)}) == "DAY_BEFORE_INSTALL"
    sd.resolve(doc, S, installs={"kobo": S + timedelta(days=-6, hours=11, minutes=30)})


def test_day_not_in_past():
    # trial-after is received S+1 12:00; a DB clock less than 5 min after it refuses
    assert _codes(sd.load(), db_now=S + timedelta(days=1, hours=12, minutes=4)) == "DAY_NOT_IN_PAST"
    sd.resolve(sd.load(), S, db_now=S + timedelta(days=1, hours=12, minutes=5))


def test_outside_board_window():
    doc = copy.deepcopy(sd.load())
    doc["sites"]["cold"].append({"day": "S-31d", "kind": "normal"})
    assert _codes(doc) == "OUTSIDE_BOARD_WINDOW"


def test_payload_round_trip():
    runs = sd.resolve(sd.load(), S)
    assert sd.from_payload([r.payload() for r in runs]) == runs


# ---- U4: add-day planning (refusals; the live path runs once in the slow build test) --------------------------
NOW = S + timedelta(days=2, hours=4)
INSTALLS = {"kobo": S + timedelta(days=-29, hours=11), "cold": S + timedelta(days=-26, hours=6),
            "ev": S + timedelta(days=-26, hours=6, minutes=30)}


def _plan(site, kind, **kw):
    doc = sd.load()
    current = sd.resolve(doc, S, db_now=NOW, installs=INSTALLS)
    return sd.plan_add_day(doc, current, site, kind, S, kw.pop("db_now", NOW), installs=INSTALLS, **kw)


def _refused(site, kind, **kw):
    with pytest.raises(sd.StoryDaysError) as err:
        _plan(site, kind, **kw)
    return err.value.error_code


def test_add_day_defaults_to_the_next_free_day_on_real_time():
    later = S + timedelta(days=2, hours=12)  # the default day S+2 is today; its 03:00-11:00 run has ended
    planned = _plan("kobo", "late", db_now=later)
    assert planned.day == (S + timedelta(days=2)).date().isoformat() and planned.as_kind == "normal"
    assert planned.received_at == later and planned.known_at == later and planned.assess == "tick"
    assert planned.epoch == "day-13"  # max+1 over 11 epochs (R8: the Kobo S-1/S/S+1 stream shares one)
    gap = _plan("cold", "normal", day="S-10d")
    assert gap.day == "2026-10-19" and gap.has_run
    assert not _plan("kobo", "missing", day="S-11d").has_run


def test_add_day_refusals():
    assert _refused("kobo", "normal", day="S-14d") == "DUPLICATE_DAY"
    # evidence is the append-only basis: a delivered day refuses as delivered even when the calendar also holds it
    assert _refused("kobo", "normal", day="S-14d", delivered_days={"2026-10-15"}) == "DAY_HAS_EVIDENCE"
    assert _refused("kobo", "normal", day="S-11d", delivered_days={"2026-10-18"}) == "DAY_HAS_EVIDENCE"
    assert _refused("kobo", "normal", day="S+3d") == "DAY_NOT_IN_PAST"
    assert _refused("kobo", "normal", db_now=S + timedelta(days=2, hours=11)) == "DAY_NOT_IN_PAST"  # run ends 11:00
    assert _refused("cold", "normal", day="S-27d") == "DAY_BEFORE_INSTALL"
    assert _refused("kobo", "sunny") == "UNKNOWN_KIND"
    assert _refused("kobo", "trial-before", day="S-1d") == "PREPARE_ONLY_KIND"
    assert _refused("cold", "failure", day="S-1d") == "PREPARE_ONLY_KIND"
    assert _refused("ev", "fault", day="S-1d") == "PREPARE_ONLY_KIND"
    assert _refused("kobo", "normal", day="S-31d") == "OUTSIDE_BOARD_WINDOW"


# ---- CH-9 u4 (CH9-R2:Q8): the `mill-midday` kind (prepare-only; not scheduled in `sites`) --------------------
def test_mill_midday_kind_resolves_and_validates_when_scheduled():
    import yaml

    doc = copy.deepcopy(sd.load())
    assert all(e["kind"] != "mill-midday" for entries in doc["sites"].values() for e in entries)
    spec = doc["kinds"]["kobo"]["mill-midday"]
    scenario = yaml.safe_load((Path(sd.DEFAULT_FILE).parents[2] / "config" / "scenarios" / "kobo-daytime.yaml")
                              .read_text(encoding="utf-8"))
    assert (spec["scenario_id"], spec["scenario_version"]) == (scenario["scenario_id"],
                                                               scenario["version"]["scenario_version"])
    doc["sites"]["kobo"].append({"day": "S-5d", "kind": "mill-midday"})
    runs = sd.resolve(doc, S, db_now=NOW, installs=INSTALLS)
    mill = next(r for r in runs if r.kind == "mill-midday")
    D = datetime(2026, 10, 24, tzinfo=timezone.utc)
    assert mill.site == "kobo" and mill.day == "2026-10-24" and mill.has_run and mill.assess == "build"
    assert (mill.start, mill.end, mill.received_at) == (D + timedelta(hours=3), D + timedelta(hours=15),
                                                        D + timedelta(hours=16))
    assert mill.scenario == {"scenario_id": "kobo-daytime", "scenario_version": 2}
    assert sd.from_payload([r.payload() for r in runs]) == runs


def test_mill_midday_is_prepare_only():
    assert "mill-midday" not in sd.ADD_DAY_KINDS["kobo"]
    assert _refused("kobo", "mill-midday", day="S-2d") == "PREPARE_ONLY_KIND"


# DD-1a1 v2 day list (DD1a1-R Q7, R4): full days tile the local day; the mill kind points at the derived file.
def _v2():
    return sd.load(sd.V2_FILE)


def _v2_with_mill():
    doc = copy.deepcopy(_v2())
    doc["sites"]["kobo"] = [{"day": "S-5d", "kind": "mill-midday"}] + doc["sites"]["kobo"]
    return doc


def test_v2_only_the_mill_day_is_a_full_day_and_it_tiles_the_local_day_00_to_24():
    # DD1a1-R16: every other Kobo story day, and every Cold and EV day, is its one story run (partly checked).
    runs = sd.resolve(_v2_with_mill(), S)
    by_day: dict = {}
    for r in runs:
        by_day.setdefault((r.site, r.day), []).append(r)
    full = {k: v for k, v in by_day.items() if len(v) > 1}
    assert list(full) == [("kobo", "2026-10-24")]
    group = full[("kobo", "2026-10-24")]
    D = datetime.fromisoformat("2026-10-24").replace(tzinfo=timezone.utc)
    ordered = sorted(group, key=lambda r: r.start)
    assert [r.kind for r in ordered] == ["night-early", "mill-midday", "mill-rest"]
    assert ordered[0].start == D - timedelta(hours=3)
    for a, b in zip(ordered, ordered[1:]):
        assert (a.covers_end or a.end) == b.start
    assert (ordered[-1].covers_end or ordered[-1].end) == D + timedelta(hours=21)
    assert not [k for k in by_day if k not in full and len(by_day[k]) != 1]
    assert not [k for k, v in _v2()["kinds"]["kobo"].items() if v.get("complement") and k != "mill-midday"]


def test_v2_tiling_check_is_not_vacuous():
    doc = copy.deepcopy(_v2_with_mill())
    doc["kinds"]["kobo"]["mill-rest"]["start"] = "D+0d 12:00"  # a three-hour gap
    assert _codes(doc) == "DAY_NOT_TILED"


def test_full_day_only_where_every_join_is_stopped():
    # DD1a1-R16 guard. A complement on a story whose joins are not measured STOPPED is refused ...
    doc = copy.deepcopy(_v2_with_mill())
    doc["kinds"]["kobo"]["normal"]["complement"] = ["night-early", "mill-rest"]  # N ends RUNNING on the registered Site
    assert _codes(doc) == "FULL_DAY_JOIN_NOT_STOPPED"
    # ... and so is the mill day itself once one of its measured joins reads RUNNING (the guard can fail).
    joins = copy.deepcopy(sd.full_day_joins())
    assert [j["generator"] for j in joins["kobo-mill-midday"]["joins"]] == ["STOPPED", "STOPPED"]
    joins["kobo-mill-midday"]["joins"][1]["generator"] = "RUNNING"
    with pytest.raises(sd.StoryDaysError) as err:
        sd.check_full_day("kobo", "2026-10-24", "kobo-mill-midday", joins)
    assert err.value.error_code == "FULL_DAY_JOIN_NOT_STOPPED"


def test_v2_mill_midday_points_at_the_derived_file_and_v1_is_unchanged():
    assert _v2()["kinds"]["kobo"]["mill-midday"]["scenario_id"] == "kobo-mill-midday"
    assert sd.load()["kinds"]["kobo"]["mill-midday"]["scenario_id"] == "kobo-daytime"


def test_v2_complements_are_received_after_their_own_end_and_inherit_knowledge():
    runs = sd.resolve(_v2_with_mill(), S)
    story = {(r.site, r.day): r for r in runs if not r.complement_of and r.has_run}
    for r in runs:
        if r.complement_of:
            assert r.received_at >= r.end and r.known_at == story[(r.site, r.day)].known_at


# DD1a1-R8: one epoch per maximal run of consecutive built days of one Site; each instant is sent once per Site-day
# (the stream's runs), and the story runs equal v1's save the epoch.
def _streams(runs):
    out: dict = {}
    for site in {r.site for r in runs}:
        days = sorted({r.day for r in runs if r.site == site})
        cur: list = []
        for d in days:
            if cur and datetime.fromisoformat(d) - datetime.fromisoformat(cur[-1]) == timedelta(days=1):
                cur.append(d)
            else:
                cur = [d]
                out.setdefault(site, []).append(cur)
    return out


def test_v2_one_epoch_per_stream():
    runs = [r for r in sd.resolve(_v2_with_mill(), S) if r.has_run]
    streams = _streams(runs)
    assert any(len(st) > 1 for v in streams.values() for st in v)
    seen = set()
    for site, lst in streams.items():
        for st in lst:
            epochs = {r.epoch for r in runs if r.site == site and r.day in st}
            assert len(epochs) == 1, (site, st, epochs)
            assert not (epochs & seen)  # a day with no run is a gap: the next stream has a fresh epoch
            seen |= epochs


def test_v2_epoch_guards():
    doc = _v2()
    kobo = doc["sites"]["kobo"]
    late = next(e for e in kobo if e["kind"] == "late")
    # a late day adjacent to a built day joins a stream: refused
    bad = copy.deepcopy(doc); bad["sites"]["kobo"] = [e for e in kobo if e is not late] + [
        {**late, "day": "S-2d"}]
    with pytest.raises(sd.StoryDaysError) as e:
        sd.resolve(bad, S)
    assert e.value.error_code == "LATE_IN_STREAM"
    bad = copy.deepcopy(doc)
    bad["sites"]["cold"] = [{**x, "day": "S-4d"} if x["day"] == "S-3d" else x for x in bad["sites"]["cold"]]
    bad["sites"]["cold"].append({"day": "S-3d", "kind": "normal"})
    with pytest.raises(sd.StoryDaysError) as e:
        sd.resolve(bad, S)
    assert e.value.error_code == "BUILT_DAY_AFTER_DEGRADED"


def _sent(r, minute):
    keep = r.keep()
    return (r.start <= minute <= r.end) if keep is None else keep(sd.iso(minute))


def _not_once(runs):
    """Every minute of each full local day that is not sent by exactly one run of its stream, and every complement
    that sends the shared 21:00Z day edge (it goes to the later day)."""
    by_day: dict = {}
    for r in runs:
        by_day.setdefault((r.site, r.day), []).append(r)
    bad, checked = [], 0
    for (site, day), group in by_day.items():
        if len(group) == 1:
            continue
        D = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
        t, hi = D - timedelta(hours=3), D + timedelta(hours=21)
        while t < hi:
            senders = [r.kind for r in group if _sent(r, t)]
            if len(senders) != 1:
                bad.append((site, day, sd.iso(t), senders))
            t += timedelta(minutes=1)
            checked += 1
        bad += [(site, day, "21:00Z", r.kind) for r in group if r.complement_of and _sent(r, hi)]
    return bad, checked


def test_v2_each_instant_is_sent_once_per_stream():
    bad, checked = _not_once([r for r in sd.resolve(_v2_with_mill(), S) if r.has_run])
    assert bad == [] and checked > 0, bad[:5]


def test_v2_cold_days_are_the_v1_days():
    """DD1a1-R14: Cold days are the v1 shape (one story run, partly checked), with no complement or fill-in."""
    cold = [r for r in sd.resolve(_v2(), S) if r.site == "cold"]
    assert cold and not any(r.complement_of for r in cold)
    assert "steady" not in _v2()["kinds"]["cold"]
    assert not any("complement" in k or "covers_end" in k for k in _v2()["kinds"]["cold"].values())


def test_v2_instant_check_is_not_vacuous():
    runs = [r for r in sd.resolve(_v2_with_mill(), S) if r.has_run]
    loose = [sd.replace(r, owned=()) for r in runs]  # complements that ignore the story's instants
    closed = [sd.replace(r, emit_until=r.emit_until + timedelta(minutes=1)) if r.complement_of else r for r in runs]
    assert _not_once(loose)[0] and _not_once(closed)[0]

def test_v2_story_runs_equal_v1():
    drop = ("covers_end", "emit_until", "owned", "complement_of", "epoch")
    cold = [r for r in sd.resolve(sd.load(), S) if r.site == "cold"]
    assert cold and [r.payload() for r in cold] == [r.payload() for r in sd.resolve(_v2(), S) if r.site == "cold"]
    v1 = [{k: v for k, v in r.payload().items() if k not in drop} for r in sd.resolve(sd.load(), S)]
    v2 = [{k: v for k, v in r.payload().items() if k not in drop}
          for r in sd.resolve(_v2(), S) if not r.complement_of]
    assert v2 == v1 and v1
    assert all(r.keep() is None for r in sd.resolve(_v2(), S) if not r.complement_of)
    assert not [r for r in sd.resolve(_v2(), S) if r.complement_of]  # DD1a1-R16: no Kobo story day carries a complement


# DD1a1-R7/R7a: the trial-after night is split at the reserve change (S+1d 00:00Z); part A is the derived
# `kobo-night-early-until-0300`, part B `kobo-night-early-from-0300`.
def _split_runs():
    cut = S - timedelta(days=5)  # the mill day (S-5d), the one full day, crossing a revision at its 00:00Z
    runs = sd.resolve(_v2_with_mill(), S, revision_boundaries=(cut,))
    return cut, [r for r in runs if r.site == "kobo" and r.day == cut.date().isoformat() and r.has_run]


def test_v2_trial_after_day_has_five_runs_split_at_the_revision_boundary():
    cut, day = _split_runs()
    day.sort(key=lambda r: r.start)
    assert len(day) == 4
    a, b = day[0], day[1]
    assert (a.scenario["scenario_id"], b.scenario["scenario_id"]) == ("kobo-night-early-until-0255",
                                                                      "kobo-night-early-from-0300")
    # DD1a1-R7b: part A runs 175 min, ends 5 min before the cut and covers/sends to the cut; B starts at the cut
    assert a.end == cut - timedelta(minutes=5) and a.covers_end == cut == b.start and b.end == cut + timedelta(hours=3)
    assert a.epoch == b.epoch  # one epoch for the stream
    # the day still tiles 00:00-24:00 local (resolve raises DAY_NOT_TILED otherwise)
    assert all(len(v) == 3 for v in _non_split_days().values())


def _non_split_days():
    runs = sd.resolve(_v2_with_mill(), S, revision_boundaries=(S + timedelta(days=1),))
    cut_day = (S + timedelta(days=1)).date().isoformat()
    by_day: dict = {}
    for r in runs:
        if r.site == "kobo" and r.day != cut_day and r.has_run and (r.complement_of or True):
            by_day.setdefault(r.day, []).append(r)
    return {d: v for d, v in by_day.items() if len(v) > 1}


def test_split_night_files_windows_equal_the_parents():
    import derive_steady_scenarios as derive

    def events(sid):
        doc = derive.yaml.safe_load((derive.SCENARIOS / f"{sid}.yaml").read_text(encoding="utf-8"))
        return doc["timeline"], doc["public_parameters"]

    parent, p_params = events("kobo-night-early")
    a, a_params = events("kobo-night-early-until-0255")
    probe, _ = events("kobo-night-early-until-0300")
    b, _ = events("kobo-night-early-from-0300")
    assert a_params == p_params  # same start state as the parent

    def cells(ev, lo, hi, shift):
        # (series, value) of every event overlapping [lo, hi) minutes, with offsets re-based by `shift`
        out = []
        for e in ev:
            s, d = e["offset_minutes"], e["timing"]["duration_minutes"]
            if s < hi and s + d > lo:
                out.append((e["event_id"].split("-")[1], e["parameters"][0]["value"], max(s, lo) - shift, min(s + d, hi) - shift))
        return sorted(out)

    assert len(cells(parent, 0, 180, 0)) == 8 and cells(b, 0, 180, 0)  # non-empty sets
    assert cells(a, 0, 175, 0) == cells(parent, 0, 175, 0) and cells(a, 0, 175, 0)  # part A = the parent's first 175 min
    assert max(e["offset_minutes"] + e["timing"]["duration_minutes"] for e in a) == 175  # nothing past 02:55
    assert cells(probe, 0, 180, 0) == cells(parent, 0, 180, 0)  # the R7a probe file stays the parent's first 3 h
    assert cells(b, 0, 180, 0) == cells(parent, 180, 360, 180)  # part B = from 03:00 local


# DD1a1-R10: a Kobo full-day degraded day is held until BL-18 (source-time outage cut).
def _with_kobo_degraded():
    doc = _v2()
    doc["kinds"]["kobo"]["degraded"]["complement"] = ["night-early", "mill-rest"]
    doc["sites"] = {"kobo": [{"day": "S-3d", "kind": "degraded"}, {"day": "S+0d", "kind": "trial-before"},
                          {"day": "S+1d", "kind": "trial-after"}]}
    return doc


def test_r10_no_shown_calendar_holds_a_kobo_full_day_degraded_day():
    for path in (sd.DEFAULT_FILE, sd.V2_FILE):
        doc = sd.load(path)
        held = [e for e in doc["sites"].get("kobo", []) if e["kind"] == "degraded"]
        assert held == [], path.name
    import re
    root = Path(__file__).resolve().parents[2]
    hint = re.compile(r"add-day[^\n]*(KOBO-001[^\n]*degraded|degraded[^\n]*KOBO-001)")
    texts = [p for pat in ("tools/*.py", "docs/*.md", "docs/**/*.md") for p in root.glob(pat)]
    assert [p.name for p in texts if hint.search(p.read_text(encoding="utf-8", errors="ignore"))] == []


def test_r10_degraded_day_is_refused_in_a_calendar_and_by_add_day_and_only_the_flag_lets_it_through():
    doc = _with_kobo_degraded()
    assert _codes(doc) == "DEGRADED_DAY_HELD"
    with pytest.raises(sd.StoryDaysError) as err:
        sd.plan_add_day(doc, [], "kobo", "degraded", S, S + timedelta(days=10))
    assert err.value.error_code == "DEGRADED_DAY_HELD"
    sd.DEGRADED_PROBE = True
    try:
        # the flag lets the day past the R10 hold; the R16 guard (joins not measured STOPPED) then still refuses it
        assert _codes(doc) == "FULL_DAY_JOIN_NOT_STOPPED"
    finally:
        sd.DEGRADED_PROBE = False


# DD1a2-R Q8.4: the hold does not depend on a complement, and Cold's own `degraded` kind stays allowed.
def test_q84_kobo_degraded_is_refused_without_a_complement_and_cold_degraded_stays():
    doc = _with_kobo_degraded()
    doc["kinds"]["kobo"]["degraded"].pop("complement")
    assert _codes(doc) == "DEGRADED_DAY_HELD"
    with pytest.raises(sd.StoryDaysError) as err:
        sd.plan_add_day(doc, [], "kobo", "degraded", S, S + timedelta(days=10))
    assert err.value.error_code == "DEGRADED_DAY_HELD"
    sd.DEGRADED_PROBE = True
    try:
        assert [r.kind for r in sd.resolve(doc, S) if r.offset == -3] == ["degraded"]  # the flag is the only way past
    finally:
        sd.DEGRADED_PROBE = False
    cold = sd.load(sd.V2_FILE)
    assert {"day": "S-3d", "kind": "degraded"} in cold["sites"]["cold"]
    assert sd.plan_add_day(cold, [], "cold", "degraded", S, S + timedelta(days=10), day="S+2d").kind == "degraded"


# DD1a2-R Q4: add-day may not put a Kobo day next to a late day; the late day itself is not moved.
@pytest.mark.parametrize("day", ["S-4d", "S-2d"])
def test_q4_add_day_next_to_a_late_kobo_day_is_refused(day):
    doc = _v2()
    current = sd.resolve(doc, S)
    assert [r.offset for r in current if r.site == "kobo" and r.kind == "late"] == [-3]  # the refused neighbour exists
    with pytest.raises(sd.StoryDaysError) as err:
        sd.plan_add_day(doc, current, "kobo", "normal", S, S + timedelta(days=10), day=day)
    assert err.value.error_code == "LATE_IN_STREAM"


def test_q4_add_day_two_days_from_a_late_kobo_day_is_not_refused_and_cold_has_no_such_rule():
    doc = _v2()
    current = sd.resolve(doc, S)
    assert sd.plan_add_day(doc, current, "kobo", "normal", S, S + timedelta(days=10), day="S-5d").offset == -5
    late = [replace(r, kind="late") if r.site == "cold" and r.offset == -3 else r for r in current]
    assert sd.plan_add_day(doc, late, "cold", "normal", S, S + timedelta(days=10), day="S-4d").offset == -4


# DD1a2-R Q6: the B-16 fallback is a switch on the one day list. EV `S-14d normal` (accepted in DD1a2-R) is the entry
# the v3 list carries; here it sits on a test list because v3 waits on the owner's answers.
def _baseline_doc():
    doc = copy.deepcopy(_v2())
    doc["sites"]["ev"] = [{"day": "S-14d", "kind": "normal"}, *doc["sites"]["ev"]]
    return doc


MILL3_OFFSETS = {-13, -12, -11, -9, -8, -6, -5}


@pytest.mark.parametrize("weekday", range(7))
def test_q6_b16_drops_only_resolved_offsets_s20_to_s15(weekday):
    s = S + timedelta(days=(weekday - S.weekday()) % 7)
    doc = _baseline_doc()
    doc["sites"]["kobo"] += [{"day": f"S{n:+d}d", "kind": "normal"} for n in (-20, -15, *sorted(MILL3_OFFSETS))]
    out = sd.apply_baseline(doc, s, "b16")
    kept = {site: {sd.weekday_offset(site, s, sd.day_offset(e["day"])) for e in entries}
            for site, entries in out["sites"].items()}
    every = {site: {sd.weekday_offset(site, s, sd.day_offset(e["day"])) for e in entries}
             for site, entries in doc["sites"].items()}
    for site in every:
        assert kept[site] == {n for n in every[site] if not -20 <= n <= -15}, site
    assert {-20, -15} <= every["kobo"] and not {-20, -15} & kept["kobo"]  # the dropped set is not empty
    assert {-28, -21} <= kept["kobo"]  # the earlier story days stay
    assert MILL3_OFFSETS <= kept["kobo"]  # the MILL-3 days survive the fallback
    assert sd.apply_baseline(doc, s, "b22")["sites"] == doc["sites"]
    ev_entry = sd.weekday_offset("ev", s, -14)
    assert (ev_entry in kept["ev"]) == (ev_entry == -14)  # an EV Tuesday landing in the range goes; S-14 itself stays


def test_q6_unknown_baseline_is_refused():
    with pytest.raises(sd.StoryDaysError) as err:
        sd.apply_baseline(_v2(), S, "b10")
    assert err.value.error_code == "UNKNOWN_BASELINE"


@pytest.mark.parametrize("weekday", range(7))
def test_ev_s14_entry_gives_three_tuesdays_and_a_fourth_is_reported_not_moved(weekday):
    s = S + timedelta(days=(weekday - S.weekday()) % 7)
    doc = _baseline_doc()
    landed = sorted(sd.weekday_offset("ev", s, sd.day_offset(e["day"])) for e in doc["sites"]["ev"])
    assert len(set(landed)) == 3 and all(-20 <= n <= 1 for n in landed)
    assert all((s + timedelta(days=n)).weekday() == sd.SITE_WEEKDAY["ev"] for n in landed)
    # S on a Monday is the only week with a 4th Tuesday in the window: S+1
    want = [(s + timedelta(days=1)).date().isoformat()] if s.weekday() == 0 else []
    assert sd.uncovered_weekdays(doc, s)["ev"] == want
    # without the new entry a Tuesday is reported, so the report is not vacuous
    assert sd.uncovered_weekdays(_v2(), s)["ev"]
