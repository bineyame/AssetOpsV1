"""Source clocks shared by the poller and the emulator (build spec 0.8, Q-T25).

`WallClock` is real UTC in whole seconds. `ReplayClock(start, rate,
wall_epoch)` maps wall time to source time as `start + (wall - wall_epoch) *
rate`, floored to whole seconds, so two processes given the same three
arguments and synchronised wall clocks agree on source time. Both take an
injectable `wall` and `sleep`, so tests never really sleep.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol

_US = timedelta(microseconds=1)
SPIN_SECONDS = 0.002
MAX_SLEEP_SECONDS = 0.5
MAX_RATE = 600


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(name: str, instant: datetime) -> None:
    if instant.tzinfo is None or instant.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be an aware UTC instant")


class Clock(Protocol):
    def now(self) -> datetime: ...

    def sleep_until(self, instant: datetime) -> None: ...


def _sleep_until_wall(target: datetime, wall: Callable[[], datetime], sleep: Callable[[float], None]) -> None:
    """Sleep in bounded steps, re-reading the wall each loop, then spin out the last 2 ms."""
    while True:
        remaining = (target - wall()).total_seconds()
        if remaining <= SPIN_SECONDS:
            break
        sleep(min(remaining - SPIN_SECONDS, MAX_SLEEP_SECONDS))
    while wall() < target:
        pass


class WallClock:
    def __init__(self, *, wall: Callable[[], datetime] = utc_now, sleep: Callable[[float], None] = time.sleep) -> None:
        self._wall, self._sleep = wall, sleep

    def now(self) -> datetime:
        return self._wall().astimezone(timezone.utc).replace(microsecond=0)

    def sleep_until(self, instant: datetime) -> None:
        _aware("instant", instant)
        _sleep_until_wall(instant, self._wall, self._sleep)


class ReplayClock:
    def __init__(
        self,
        start: datetime,
        rate: int,
        wall_epoch: datetime,
        *,
        wall: Callable[[], datetime] = utc_now,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        _aware("start", start)
        _aware("wall_epoch", wall_epoch)
        if start.microsecond:
            raise ValueError("a replay start is a whole-second instant")
        if type(rate) is not int or not 1 <= rate <= MAX_RATE:
            raise ValueError(f"a replay rate is an integer 1..{MAX_RATE}")
        self.start, self.rate, self.wall_epoch = start, rate, wall_epoch
        self._wall, self._sleep = wall, sleep

    def now(self) -> datetime:
        elapsed_us = (self._wall() - self.wall_epoch) // _US
        return self.start + timedelta(seconds=(elapsed_us * self.rate) // 1_000_000)

    def wall_at(self, instant: datetime) -> datetime:
        """The first wall instant at which `now()` reaches `instant`."""
        _aware("instant", instant)
        source_us = (instant - self.start) // _US
        return self.wall_epoch + timedelta(microseconds=-((-source_us) // self.rate))

    def sleep_until(self, instant: datetime) -> None:
        _sleep_until_wall(self.wall_at(instant), self._wall, self._sleep)
