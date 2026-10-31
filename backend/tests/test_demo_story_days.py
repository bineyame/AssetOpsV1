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
    assert late.received_at == datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
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
    assert sum(r.has_run for r in runs if r.site == "kobo") == 7


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


@pytest.mark.parametrize("change", ["drop_after", "after_not_next_day", "two_before"])
def test_trial_pair_invalid(change):
    doc = copy.deepcopy(sd.load())
    kobo = doc["sites"]["kobo"]
    if change == "drop_after":
        kobo[:] = [e for e in kobo if e["kind"] != "trial-after"]
    elif change == "after_not_next_day":
        next(e for e in kobo if e["kind"] == "trial-after")["day"] = "S+2d"
    else:
        kobo.append({"day": "S-1d", "kind": "trial-before"})
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
