"""TEL-01 clocks (build spec 0.8, Q-T25): FakeWall and a sleep that advances it; nothing really sleeps."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from field_fixtures import FakeWall, RecordingSleep, at  # noqa: E402

from assetops_field.clock import ReplayClock, WallClock  # noqa: E402

WALL0 = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)


def test_wall_clock_is_whole_second_utc():
    wall = FakeWall(WALL0 + timedelta(microseconds=999_999))
    assert WallClock(wall=wall).now() == WALL0


def test_replay_clock_maps_wall_to_source_at_rate_and_floors():
    wall = FakeWall(WALL0)
    clock = ReplayClock(at("2026-09-30T06:00:00Z"), 120, WALL0, wall=wall)
    assert clock.now() == at("2026-09-30T06:00:00Z")
    wall.set(WALL0 + timedelta(seconds=1))
    assert clock.now() == at("2026-09-30T06:02:00Z")
    wall.set(WALL0 + timedelta(microseconds=8_333))  # 0.99996 source seconds
    assert clock.now() == at("2026-09-30T06:00:00Z")
    wall.set(WALL0 - timedelta(seconds=5))
    assert clock.now() == at("2026-09-30T05:50:00Z")  # earlier than start before the epoch


def test_two_replay_clocks_with_the_same_arguments_agree():
    wall = FakeWall(WALL0 + timedelta(seconds=3, microseconds=123_456))
    a = ReplayClock(at("2026-09-30T08:00:00Z"), 12, WALL0, wall=wall)
    b = ReplayClock(at("2026-09-30T08:00:00Z"), 12, WALL0, wall=wall)
    assert a.now() == b.now() == at("2026-09-30T08:00:37Z")


@pytest.mark.parametrize("rate", [0, 601, 1.5])
def test_replay_rate_is_an_integer_1_to_600(rate):
    with pytest.raises(ValueError):
        ReplayClock(at("2026-09-30T08:00:00Z"), rate, WALL0)


def test_sleep_until_steps_then_spins_and_reaches_the_instant():
    wall = FakeWall(WALL0, tick=timedelta(microseconds=100))
    sleep = RecordingSleep(wall)
    clock = ReplayClock(at("2026-09-30T06:00:00Z"), 120, WALL0, wall=wall, sleep=sleep)
    clock.sleep_until(at("2026-09-30T06:02:01Z"))  # 121 source s = 1.008333 wall s
    assert clock.now() >= at("2026-09-30T06:02:01Z")
    assert all(0 < s <= 0.5 for s in sleep.calls) and len(sleep.calls) >= 3
    assert timedelta(microseconds=1_008_334) <= wall.instant - WALL0 < timedelta(microseconds=1_009_000)


def test_sleep_until_a_past_instant_returns_at_once():
    wall = FakeWall(WALL0)
    sleep = RecordingSleep(wall)
    WallClock(wall=wall, sleep=sleep).sleep_until(WALL0 - timedelta(seconds=10))
    assert sleep.calls == []


def test_sleep_until_absorbs_a_wall_step():
    wall = FakeWall(WALL0, tick=timedelta(microseconds=100))
    steps: list[float] = []

    def stepping_sleep(seconds: float) -> None:
        steps.append(seconds)
        wall.instant += timedelta(seconds=seconds)
        if len(steps) == 1:
            wall.instant += timedelta(seconds=30)  # an NTP step forward

    WallClock(wall=wall, sleep=stepping_sleep).sleep_until(WALL0 + timedelta(seconds=10))
    assert len(steps) == 1  # the wall is re-read, so the remaining wait vanished
    assert wall.instant >= WALL0 + timedelta(seconds=10)
