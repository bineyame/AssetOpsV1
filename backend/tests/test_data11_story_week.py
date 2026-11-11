"""DATA-11 (D-E5.37, `.agent/architect-answer-non-kobo-sites-2026-11-10.md`): the Cold story week holds an ordinary
day on every day S-7..S, through the existing prepare path (`tools/demo_story_days.py`, the v4 day list). Pure: the
resolved calendar and plan only (no prepare runs here; Saturday's rehearsal build proves the rows)."""

from __future__ import annotations

import copy
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import demo_story_days as sd  # noqa: E402

UTC = timezone.utc
NEW_COLD = (-6, -5, -4, -2, -1)
#: a Thursday (the Saturday-rehearsal story day: prepare 14 Nov - 2 d), a Sunday and a Tuesday
STORY_DAYS = [datetime(2026, 11, 12, tzinfo=UTC), datetime(2026, 11, 8, tzinfo=UTC),
              datetime(2026, 11, 10, tzinfo=UTC)]


def _installs(s):
    return {"kobo": s + timedelta(days=-29, hours=11), "cold": s + timedelta(days=-26, hours=6),
            "ev": s + timedelta(days=-26, hours=6, minutes=30)}


def _resolve(doc, s):
    return sd.resolve(doc, s, db_now=s + timedelta(days=2, hours=4), installs=_installs(s))


def _before(doc):
    """The day list as it stood before DATA-11: no Cold `ordinary` entry."""
    old = copy.deepcopy(doc)
    old["sites"]["cold"] = [e for e in old["sites"]["cold"] if e["kind"] != "ordinary"]
    old["kinds"]["cold"].pop("ordinary", None)
    return old


@pytest.mark.parametrize("s", STORY_DAYS)
def test_cold_has_a_built_day_on_every_day_of_the_story_week(s):
    cold = {r.offset: r for r in _resolve(sd.load(), s) if r.site == "cold"}
    assert sorted(cold) == list(range(-7, 1))
    assert {o: cold[o].kind for o in (-7, -3, 0)} == {-7: "normal", -3: "degraded", 0: "failure"}
    for o in NEW_COLD:
        r = cold[o]
        D = s + timedelta(days=o)
        assert r.kind == "ordinary" and r.has_run and r.assess == "build"
        assert r.scenario == {"scenario_id": "cold-normal", "scenario_version": 1}
        assert (r.start, r.end, r.received_at) == (D + timedelta(hours=16), D + timedelta(hours=17, minutes=5),
                                                   D + timedelta(hours=17, minutes=5))
        # inside the Site's local day (UTC+3): [D-3h, D+21h); no run crosses a day boundary
        assert D + sd.LOCAL_DAY_START <= r.start < r.end <= D + sd.LOCAL_DAY_START + timedelta(hours=24)
        # a story run with no complement: sent unchanged, no keep filter, no seam
        assert r.keep() is None and r.keep_observation() is None and not r.seam and not r.complement_of


@pytest.mark.parametrize("s", STORY_DAYS)
def test_each_cold_day_is_its_own_recording_session(s):
    runs = _resolve(sd.load(), s)
    cold = [r for r in runs if r.site == "cold" and r.has_run]
    assert len(cold) == 8 and len({r.epoch for r in cold}) == 8
    others = {r.epoch for r in runs if r.has_run and r.site != "cold"}
    assert not ({r.epoch for r in cold} & others)
    # one run per Cold day, so no epoch is shared inside a day either (PB-6: no two sessions on one day)
    assert len({r.day for r in cold}) == 8


@pytest.mark.parametrize("s", STORY_DAYS)
def test_existing_days_keep_every_value_but_the_epoch_label(s):
    doc = sd.load()
    old = {(r.site, r.day, r.kind, r.start): r for r in _resolve(_before(doc), s)}
    new = {(r.site, r.day, r.kind, r.start): r for r in _resolve(doc, s)}
    assert set(old) <= set(new)
    added = set(new) - set(old)
    assert {(k[0], k[2]) for k in added} == {("cold", "ordinary")} and len(added) == 5
    for key, r in old.items():
        a, b = r.payload(), new[key].payload()
        a.pop("epoch"), b.pop("epoch")
        assert a == b, key
    # Kobo's multi-day streams group exactly as before (DD1a1-R8 unchanged for Kobo)
    def groups(rs):
        by: dict = {}
        for r in rs.values():
            if r.site == "kobo" and r.has_run:
                by.setdefault(r.epoch, set()).add(r.day)
        return sorted(sorted(v) for v in by.values())
    assert groups(old) == groups(new)


@pytest.mark.parametrize("s", STORY_DAYS)
def test_ev_days_are_unchanged_and_stay_on_the_ruled_tuesday(s):
    """ev-charger/1 runs only on a TUESDAY: the story week S-6..S holds one Tuesday, already the EV fault day, so
    DATA-11 adds no EV day (the packet's Known Deviation)."""
    doc = sd.load()
    ev = [r for r in _resolve(doc, s) if r.site == "ev"]
    assert [r.kind for r in sorted(ev, key=lambda r: r.offset)] == ["normal", "normal", "fault"]
    week = [o for o in range(-6, 1) if (s + timedelta(days=o)).weekday() == 1]
    assert len(week) == 1 and next(r for r in ev if r.kind == "fault").offset == week[0]


def test_a_cold_degraded_day_mid_week_is_not_a_stream_break():
    """The Cold `degraded` kind (`cold-missing-probe`) sits mid-week with built days after it: each Cold day is its
    own session, so DD1a1-R8's stream refusals (Kobo) do not apply to it."""
    s = STORY_DAYS[0]
    runs = _resolve(sd.load(), s)
    degraded = next(r for r in runs if r.site == "cold" and r.kind == "degraded")
    assert any(r.site == "cold" and r.has_run and r.offset > degraded.offset for r in runs)


def test_the_story_week_adds_five_cold_runs_to_the_build():
    s = STORY_DAYS[0]
    doc = sd.load()
    assert len([r for r in _resolve(doc, s) if r.has_run]) - len([r for r in _resolve(_before(doc), s)
                                                                  if r.has_run]) == 5
