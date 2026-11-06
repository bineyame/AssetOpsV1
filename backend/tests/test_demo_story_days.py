"""DEMO-SPARSE U2/U4: the sparse story calendar resolver (`tools/demo_story_days.py`), pure and fast."""

from __future__ import annotations

import copy
import sys
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
    assert [r.epoch for r in runs if r.has_run] == [f"day-{n}" for n in range(1, len(received) + 1)]
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
    assert planned.epoch == "day-14"  # after the 13 prepared runs (8 Kobo, 3 cold, 2 EV)
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
    doc["sites"]["kobo"].append({"day": "S-2d", "kind": "mill-midday"})
    runs = sd.resolve(doc, S, db_now=NOW, installs=INSTALLS)
    mill = next(r for r in runs if r.kind == "mill-midday")
    D = datetime(2026, 10, 27, tzinfo=timezone.utc)
    assert mill.site == "kobo" and mill.day == "2026-10-27" and mill.has_run and mill.assess == "build"
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


def test_v2_every_day_tiles_the_local_day_00_to_24():
    runs = sd.resolve(_v2(), S)
    by_day: dict = {}
    for r in runs:
        by_day.setdefault((r.site, r.day), []).append(r)
    full = {k: v for k, v in by_day.items() if len(v) > 1}
    assert {k[0] for k in full} == {"kobo", "cold"}
    for (site, day), group in full.items():
        D = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
        ordered = sorted(group, key=lambda r: r.start)
        assert ordered[0].start == D - timedelta(hours=3), (site, day)
        for a, b in zip(ordered, ordered[1:]):
            assert (a.covers_end or a.end) == b.start, (site, day, a.kind, b.kind)
        assert (ordered[-1].covers_end or ordered[-1].end) == D + timedelta(hours=21), (site, day)
    assert all(len(v) == 4 for (s, _), v in full.items() if s == "kobo")
    assert all(len(v) == 24 for (s, _), v in full.items() if s == "cold")


def test_v2_tiling_check_is_not_vacuous():
    doc = copy.deepcopy(_v2())
    doc["kinds"]["kobo"]["steady-afternoon"]["start"] = "D+0d 12:00"  # a one-hour gap
    assert _codes(doc) == "DAY_NOT_TILED"
    doc = copy.deepcopy(_v2())
    doc["kinds"]["cold"]["steady"]["covers_minutes"] = 65  # overlaps the next hour
    assert _codes(doc) == "DAY_NOT_TILED"


def test_v2_mill_midday_points_at_the_derived_file_and_v1_is_unchanged():
    assert _v2()["kinds"]["kobo"]["mill-midday"]["scenario_id"] == "kobo-mill-midday"
    assert sd.load()["kinds"]["kobo"]["mill-midday"]["scenario_id"] == "kobo-daytime"


def test_v2_complements_are_received_after_their_own_end_and_inherit_knowledge():
    runs = sd.resolve(_v2(), S)
    story = {(r.site, r.day): r for r in runs if not r.complement_of and r.has_run}
    for r in runs:
        if r.complement_of:
            assert r.received_at >= r.end and r.known_at == story[(r.site, r.day)].known_at
