"""Interval means and state samples (rulings D10 as amended, D4 "State reads").

An interval `[start, end)` is `GOOD` only when every one of its N expected polls,
at `start + (k + 1/2) * poll_period`, returned a value; its exact mean is then
quantized once to `output_resolution`. A missing, failed or sentinel poll makes
it `UNAVAILABLE`/`NO_MEASUREMENT`; a span that began before the session is
`UNAVAILABLE`/`NO_COMPLETED_INTERVAL`; no answered poll at all publishes nothing.
Nothing is interpolated or carried forward.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from fractions import Fraction
from typing import Sequence

from assetops_contracts.observation import quantize_half_even

from assetops_field.decode import Decoded
from assetops_field.profile import ProfileRow

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class PollOutcome(Enum):
    VALUE = "VALUE"
    NO_VALUE = "NO_VALUE"
    FAILED = "FAILED"
    NO_ANSWER = "NO_ANSWER"
    CONFIG_FAULT = "CONFIG_FAULT"


ANSWERED = frozenset({PollOutcome.VALUE, PollOutcome.NO_VALUE})


@dataclass(frozen=True)
class Poll:
    at: datetime
    outcome: PollOutcome
    decoded: Decoded | None


@dataclass(frozen=True)
class Result:
    quality: str  # "GOOD" | "UNAVAILABLE"
    reason: str | None  # None | "NO_MEASUREMENT" | "NO_COMPLETED_INTERVAL"
    value: Fraction | str | None
    source_time: datetime
    interval_start: datetime | None


def _seconds(instant: datetime) -> int:
    if instant.tzinfo is None or instant.utcoffset() != timedelta(0) or instant.microsecond:
        raise ValueError(f"{instant!r} is not a whole-second UTC instant")
    return int((instant - _EPOCH).total_seconds())


def _interval_row(row: ProfileRow) -> None:
    if row.reading_class != "INTERVAL_SIGNAL" or row.span_seconds is None or row.poll_period_seconds is None:
        raise ValueError(f"row {row.row_id} is not a polled interval row")


def interval_bounds(row: ProfileRow, end: datetime) -> tuple[datetime, datetime]:
    _interval_row(row)
    if _seconds(end) % row.cadence_seconds:
        raise ValueError(f"{end} is not a multiple of cadence {row.cadence_seconds} s")
    return end - timedelta(seconds=row.span_seconds), end


def expected_polls(row: ProfileRow, start: datetime) -> list[datetime]:
    _interval_row(row)
    if _seconds(start) % row.span_seconds:
        raise ValueError(f"{start} is not a span boundary")
    period = row.poll_period_seconds
    count = row.span_seconds // period
    return [start + timedelta(seconds=k * period + period // 2) for k in range(count)]


def publish_instants(row: ProfileRow, after: datetime, until: datetime) -> list[datetime]:
    """The multiples of `cadence_seconds` from 00:00:00Z in `(after, until]`."""
    cadence = row.cadence_seconds
    first = (_seconds(after) // cadence + 1) * cadence
    last = _seconds(until)
    return [_EPOCH + timedelta(seconds=s) for s in range(first, last + 1, cadence)]


def _quantized(row: ProfileRow, value: Fraction) -> Fraction:
    if row.output_resolution is None:
        raise ValueError(f"row {row.row_id} has no output resolution")
    return quantize_half_even(value, row.output_resolution)


class IntervalAggregator:
    """One span of one interval row, ending at `end`."""

    def __init__(self, row: ProfileRow, session_start: datetime, end: datetime) -> None:
        self.row = row
        self.session_start = session_start
        self.start, self.end = interval_bounds(row, end)
        _seconds(session_start)
        self._expected = expected_polls(row, self.start)
        self._polls: dict[datetime, Poll] = {}
        self._closed = False

    def add(self, poll: Poll) -> None:
        if self._closed:
            raise ValueError("a poll was added after the interval closed")
        if poll.at not in self._expected:
            raise ValueError(f"{poll.at} is not an expected poll of [{self.start}, {self.end})")
        if poll.at in self._polls:
            raise ValueError(f"a second poll at {poll.at}")
        if poll.outcome is PollOutcome.VALUE and (poll.decoded is None or poll.decoded.kind != "VALUE"):
            raise ValueError("a VALUE interval poll carries a decoded value")
        self._polls[poll.at] = poll

    def close(self) -> Result | None:
        if self._closed:
            raise ValueError("the interval is already closed")
        self._closed = True
        unavailable = lambda reason: Result("UNAVAILABLE", reason, None, self.end, self.start)  # noqa: E731
        if self.session_start > self.start:
            return unavailable("NO_COMPLETED_INTERVAL")
        polls = list(self._polls.values())
        if not any(poll.outcome in ANSWERED for poll in polls):
            return None
        values = [poll.decoded.value for poll in polls if poll.outcome is PollOutcome.VALUE]
        if len(values) == len(self._expected):
            mean = sum(values, Fraction(0)) / len(values)
            return Result("GOOD", None, _quantized(self.row, mean), self.end, self.start)
        return unavailable("NO_MEASUREMENT")


class StateSampler:
    def __init__(self, row: ProfileRow, skew_max_seconds: int) -> None:
        if row.reading_class != "STATE_SIGNAL":
            raise ValueError(f"row {row.row_id} is not a state row")
        self.row = row
        self.skew = timedelta(seconds=skew_max_seconds)

    def sample(self, boundary: datetime, attempts: Sequence[Poll]) -> Result | None:
        _seconds(boundary)
        inside = [poll for poll in attempts if boundary <= poll.at <= boundary + self.skew]
        if not inside:
            return None
        last = inside[-1]
        if last.outcome is PollOutcome.VALUE:
            decoded = last.decoded
            if decoded is None:
                raise ValueError("a VALUE state poll carries a decoded value")
            if decoded.kind == "STATE":
                return Result("GOOD", None, decoded.state, boundary, None)
            if decoded.kind == "VALUE":
                return Result("GOOD", None, _quantized(self.row, decoded.value), boundary, None)
            raise ValueError(f"a VALUE state poll cannot carry {decoded.kind}")
        if last.outcome is PollOutcome.NO_VALUE:
            return Result("UNAVAILABLE", "NO_MEASUREMENT", None, boundary, None)
        return None
