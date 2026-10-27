"""TEL-01 interval and state rules (D10 as amended by amendment 3, card correction D10)."""

from __future__ import annotations

import sys
from datetime import timedelta
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from field_fixtures import at, profile_document, row_document  # noqa: E402

from assetops_field.aggregate import (  # noqa: E402
    IntervalAggregator,
    Poll,
    PollOutcome,
    StateSampler,
    expected_polls,
    interval_bounds,
    publish_instants,
)
from assetops_field.decode import Decoded  # noqa: E402
from assetops_field.profile import parse_profile  # noqa: E402

PROFILE = parse_profile(profile_document())
PV, SOC = PROFILE.rows
START, END = at("2026-09-30T06:00:00Z"), at("2026-09-30T06:15:00Z")
POLLS = [at("2026-09-30T06:02:30Z"), at("2026-09-30T06:07:30Z"), at("2026-09-30T06:12:30Z")]


def value(instant, number) -> Poll:
    return Poll(instant, PollOutcome.VALUE, Decoded("VALUE", value=Fraction(number)))


def outcome(instant, kind: PollOutcome) -> Poll:
    return Poll(instant, kind, Decoded("SENTINEL") if kind is PollOutcome.NO_VALUE else None)


def aggregate(polls, session_start=START):
    aggregator = IntervalAggregator(PV, session_start, END)
    for poll in polls:
        aggregator.add(poll)
    return aggregator.close()


def test_expected_polls_sit_at_mid_period():
    assert expected_polls(PV, START) == POLLS
    assert interval_bounds(PV, END) == (START, END)


def test_all_polls_answered_is_good_with_the_mean_quantized_once():
    result = aggregate([value(POLLS[0], 1), value(POLLS[1], 1), value(POLLS[2], 2)])
    assert result.quality == "GOOD" and result.reason is None
    assert result.value == Fraction(1333, 1000)  # 4/3 -> 1.333 at 0.001
    assert result.source_time == END and result.interval_start == START


def test_one_missing_expected_poll_is_no_measurement_with_span():
    result = aggregate([value(POLLS[0], 1), value(POLLS[2], 1)])
    assert (result.quality, result.reason, result.value) == ("UNAVAILABLE", "NO_MEASUREMENT", None)
    assert result.interval_start == START and result.source_time == END


@pytest.mark.parametrize("bad", [PollOutcome.NO_VALUE, PollOutcome.FAILED, PollOutcome.NO_ANSWER,
                                 PollOutcome.CONFIG_FAULT])
def test_any_bad_poll_among_answered_ones_is_no_measurement(bad):
    result = aggregate([value(POLLS[0], 1), outcome(POLLS[1], bad), value(POLLS[2], 1)])
    assert (result.quality, result.reason) == ("UNAVAILABLE", "NO_MEASUREMENT")


def test_only_sentinel_answers_are_still_no_measurement():
    result = aggregate([outcome(p, PollOutcome.NO_VALUE) for p in POLLS])
    assert (result.quality, result.reason) == ("UNAVAILABLE", "NO_MEASUREMENT")


def test_a_fully_failed_interval_publishes_nothing():
    assert aggregate([outcome(p, PollOutcome.NO_ANSWER) for p in POLLS]) is None
    assert aggregate([outcome(POLLS[0], PollOutcome.FAILED)]) is None
    assert aggregate([]) is None


def test_the_sessions_first_interval_is_no_completed_interval_with_span():
    result = aggregate([value(POLLS[2], 5)], session_start=at("2026-09-30T06:05:00Z"))
    assert (result.quality, result.reason, result.value) == ("UNAVAILABLE", "NO_COMPLETED_INTERVAL", None)
    assert result.interval_start == START
    started_on_boundary = aggregate([value(p, 5) for p in POLLS], session_start=START)
    assert started_on_boundary.quality == "GOOD"


def test_add_refuses_unknown_duplicate_and_late_polls():
    aggregator = IntervalAggregator(PV, START, END)
    with pytest.raises(ValueError):
        aggregator.add(value(START, 1))  # an edge, not mid-period
    aggregator.add(value(POLLS[0], 1))
    with pytest.raises(ValueError):
        aggregator.add(value(POLLS[0], 1))
    aggregator.close()
    with pytest.raises(ValueError):
        aggregator.add(value(POLLS[1], 1))


def test_publish_instants_are_cadence_multiples_in_the_half_open_range():
    hourly = parse_profile(profile_document(rows=[row_document(cadence_seconds=3600)])).rows[0]
    assert publish_instants(PV, START, at("2026-09-30T06:45:00Z")) == [
        at("2026-09-30T06:15:00Z"), at("2026-09-30T06:30:00Z"), at("2026-09-30T06:45:00Z")]
    assert publish_instants(hourly, at("2026-09-30T06:00:01Z"), at("2026-09-30T08:00:00Z")) == [
        at("2026-09-30T07:00:00Z"), at("2026-09-30T08:00:00Z")]
    assert interval_bounds(hourly, at("2026-09-30T07:00:00Z")) == (at("2026-09-30T06:45:00Z"),
                                                                  at("2026-09-30T07:00:00Z"))
    with pytest.raises(ValueError):
        interval_bounds(hourly, at("2026-09-30T06:15:00Z"))


# --- state ---------------------------------------------------------------------------------------------------

B = at("2026-09-30T06:15:00Z")


def test_state_attempt_at_b_plus_1_is_good_at_b():
    result = StateSampler(SOC, 2).sample(B, [value(B + timedelta(seconds=1), Fraction(87))])
    assert (result.quality, result.value, result.source_time, result.interval_start) == ("GOOD", 87, B, None)


def test_state_attempt_after_the_skew_is_no_sample():
    assert StateSampler(SOC, 2).sample(B, [value(B + timedelta(seconds=3), 87)]) is None
    assert StateSampler(SOC, 2).sample(B, []) is None


def test_failed_first_attempt_then_good_retry_at_b_plus_2_is_good():
    attempts = [outcome(B + timedelta(seconds=1), PollOutcome.NO_ANSWER), value(B + timedelta(seconds=2), 64)]
    result = StateSampler(SOC, 2).sample(B, attempts)
    assert (result.quality, result.value, result.source_time) == ("GOOD", 64, B)


def test_state_sentinel_is_no_measurement_and_failures_are_no_sample():
    result = StateSampler(SOC, 2).sample(B, [outcome(B + timedelta(seconds=1), PollOutcome.NO_VALUE)])
    assert (result.quality, result.reason, result.value) == ("UNAVAILABLE", "NO_MEASUREMENT", None)
    for kind in (PollOutcome.FAILED, PollOutcome.NO_ANSWER, PollOutcome.CONFIG_FAULT):
        assert StateSampler(SOC, 2).sample(B, [outcome(B + timedelta(seconds=1), kind)]) is None


def test_state_number_value_is_quantized_to_output_resolution():
    result = StateSampler(SOC, 2).sample(B, [value(B + timedelta(seconds=1), Fraction(175, 2))])
    assert result.value == Fraction(88)  # 87.5 half-even at 1 -> 88
