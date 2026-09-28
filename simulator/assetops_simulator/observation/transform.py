"""Generate what each configured device published, and why it sometimes did not.

The observation transform of v4 section 6.1 phase C, as a component the kernel
composes with rather than a branch inside it. It is keyed on
`(address, device_id, signal_id)` - the address being the `addressed_key` the
whole product already keys on, which is a `StateRef`'s own spelling - so two
devices reporting one tank, and one device carrying two signals about it, are
three reporting paths and not one.

## What it is allowed to read, and what that rules out

Two arguments: the boundaries a kernel recorded, and `FrozenReportingInputs`.
There is no `FrozenWorldInputs` here and no `ModelSpec`, so nothing in this module
can move a stock, apply a bound, or run a law - and nothing the kernel is handed
carries a cadence, a bias or a dropout. `reporting-parameters-move-no-world-
quantity` is the rule; these two signatures are why it holds rather than being
remembered.

It reads a boundary's `state_samples` rather than its `stocks`, and that is not
interchangeable. A sample is what the model's `REPORTED_OBSERVATION` handler
answered at that instant, in the sampling phase and after that instant's events.
A stock the model cannot sample is not reportable at all, so reading the stock
would generate a reading out of a state nothing answered for.

## Every rule it applies is published, and it calls the published one

`sample_due_at` and `cadence_is_expressible` live in the execution contract beside
the sentences that describe them, and `draw_selects` lives in the neutral
observation contract beside the draw domain. Nothing here re-derives any of the
three. That is the T020B lesson applied to this slice: four review rounds were
spent on prose that restated a subset of what a formula did, and the formula was
right every time.

## The four reasons a due sample publishes nothing, in the order they are asked

1. the reporting path is forced unavailable across a declared window - the path is
   down, so nothing is sampled and the world carries on unobserved;
2. an interval reading is due at the run's first boundary, where no span has
   completed;
3. the sample was taken and this model measured nothing at that address in the
   span that ended;
4. the draw says this publication did not happen.

The gap is asked first because it is a fact about the path rather than about the
sample: a device on a dead line does not take a reading and then fail to send it.
Nothing about the ORDER changes which samples drop, because a draw is a function
of its own arguments and not of how many draws preceded it - so this is a
statement about what each outcome means rather than about arithmetic.
"""

from __future__ import annotations

from fractions import Fraction

from assetops_contracts.observation import (
    DeviceObservation,
    DeviceSignalSpec,
    FrozenReportingInputs,
    ReportedReading,
    draw_selects,
)
from assetops_contracts.trajectory import BoundaryState


def world_value(
    boundary: BoundaryState,
    signal: DeviceSignalSpec,
    span_minutes: int | None,
) -> Fraction | None:
    """The private quantity one signal would report at one boundary, or nothing.

    A `STATE_SIGNAL` reads the sample taken at this instant and an
    `INTERVAL_SIGNAL` reads the measurement for the span that ended at it. The two
    classes are the execution contract's and the asymmetry is
    `interval-signal-describes-the-preceding-interval`: at one timestamp a stock
    reading describes that instant and an interval reading describes the interval
    before it.

    An interval measurement is divided by the span it accumulated over, which is
    `an-interval-reading-is-a-mean-over-the-span`: 11.25 kWh over fifteen minutes
    is 45 kW, and that is the number a controller's power telemetry carries. The
    division is exact, so the mean of a dispatch forced at 45 kW is 45 kW and not
    44.999999999999996.
    """
    if signal.reading_class == "STATE_SIGNAL":
        return boundary.state_sample(signal.address)
    measured = boundary.interval_measurement(signal.address)
    if measured is None or span_minutes is None:
        return None
    return measured / Fraction(span_minutes, 60)


def _attempt(
    boundary: BoundaryState,
    signal: DeviceSignalSpec,
    reporting: FrozenReportingInputs,
    span_minutes: int | None,
) -> DeviceObservation:
    """One due sample, as what it published or as why it did not."""

    def observation(
        outcome: str,
        *,
        value: Fraction | None = None,
        reason: str | None = None,
    ) -> DeviceObservation:
        return DeviceObservation(
            device_id=signal.device_id,
            signal_id=signal.signal_id,
            address=signal.address,
            state_key=signal.state_key,
            reading_class=signal.reading_class,
            at_offset_minutes=boundary.offset_minutes,
            source_sample_time=boundary.simulation_time,
            outcome=outcome,
            reported_value=value,
            canonical_unit=signal.canonical_unit,
            suppression_reason=reason,
        )

    gaps = reporting.gaps_covering(signal, boundary.offset_minutes)
    if gaps:
        window = gaps[0]
        return observation(
            "SUPPRESSED_BY_GAP",
            reason=(
                f"{window.event_id} forces {window.condition_address} "
                f"unavailable from offset {window.offset_minutes} up to but not "
                f"including {window.end_offset_minutes}, so this signal took no "
                "sample here."
            ),
        )

    if (
        signal.reading_class == "INTERVAL_SIGNAL"
        and not boundary.has_preceding_interval
    ):
        return observation(
            "NO_PRECEDING_INTERVAL",
            reason=(
                "No interval has completed at this instant, so there is no span "
                f"for {signal.signal_id} to summarise."
            ),
        )

    value = world_value(boundary, signal, span_minutes)
    if value is None:
        return observation(
            "NO_VALUE_AT_BOUNDARY",
            reason=(
                f"This model produced no {signal.reading_class} for "
                f"{signal.address} at this instant, so the sample had nothing "
                "to read."
            ),
        )

    # v4 section 9.2's identity: seed, stream name, step index, ordinal. The
    # stream name already identifies the signal - `dropout:<device>:<signal>`,
    # which is the shape of the specification's own `sensor-noise:TANK-001:level`
    # - so the address is not a field of the draw, and since this function was
    # last reviewed there is nowhere to pass one.
    #
    # The ordinal is zero because this mechanism makes exactly one draw per
    # stream per step. A second draw at one step would be one.
    if draw_selects(
        reporting.seed,
        signal.dropout_stream,
        signal.dropout_per_thousand,
        boundary.step_index,
    ):
        return observation(
            "DROPPED",
            reason=(
                f"{signal.dropout_per_thousand} in a thousand of this signal's "
                "due samples do not publish, and the draw for this instant "
                "selected it."
            ),
        )

    return observation("REPORTED", value=value + signal.bias)


def generate_observations(
    boundaries: tuple[BoundaryState, ...], reporting: FrozenReportingInputs
) -> tuple[DeviceObservation, ...]:
    """Every sample attempt across the boundaries so far, in order.

    Ordered by instant and then by the order the publication profile declares its
    signals in, so the series is a function of the content rather than of a
    dictionary's iteration. That is what lets `observation_series_digest` be
    compared between two executions at all.

    Safe to call mid-flight, and called mid-flight by the Lab: the boundaries a
    run has reached are the boundaries there are readings for, and a transform
    that needed a finished trajectory would make a stepped run unobservable.

    Raises:
        ReportingResolutionUnrepresentable: a declared cadence is not a whole
            multiple of the run's timestep, so some sample would be due between
            two boundaries.
    """
    reporting.refuse_a_cadence_the_run_cannot_express()
    attempts: list[DeviceObservation] = []
    previous_offset: int | None = None
    for boundary in boundaries:
        # The span that ended at this boundary, read off the boundaries rather
        # than assumed to be the timestep. The last step of an interval the
        # timestep does not divide is shorter than the rest, and a mean taken over
        # the timestep there would be a number divided by a span it did not cover.
        span = (
            None
            if previous_offset is None
            else boundary.offset_minutes - previous_offset
        )
        for signal in reporting.signals:
            if signal.due_at(boundary.offset_minutes):
                attempts.append(_attempt(boundary, signal, reporting, span))
        previous_offset = boundary.offset_minutes
    return tuple(attempts)


def reported_reading(
    observations: tuple[DeviceObservation, ...],
    signal: DeviceSignalSpec,
    at_offset_minutes: int,
) -> ReportedReading:
    """What a consumer of one signal sees at one instant.

    `a-retained-reading-carries-its-own-time` in full. The newest published
    reading at or before this instant is shown with ITS source time, marked `GOOD`
    when that instant is this one and `STALE` when it is earlier. Nothing is
    restamped, nothing is interpolated, and where no reading has ever been
    published the value is `UNAVAILABLE` - which is a different statement from
    stale and is kept as one.

    Computed from the reading series and nothing else. A consumer that could reach
    the world to fill a gap would not be a consumer of readings.
    """
    mine = [
        item
        for item in observations
        if item.key == signal.key and item.at_offset_minutes <= at_offset_minutes
    ]
    attempt = next(
        (item for item in mine if item.at_offset_minutes == at_offset_minutes),
        None,
    )
    published = [item for item in mine if item.outcome == "REPORTED"]
    # By the newest instant rather than by position in the series. The series is
    # already in instant order, and relying on that would make this function's
    # correctness depend on another function's iteration.
    freshest = (
        max(published, key=lambda item: item.at_offset_minutes)
        if published
        else None
    )

    if freshest is None:
        quality = "UNAVAILABLE"
    elif freshest.at_offset_minutes == at_offset_minutes:
        quality = "GOOD"
    else:
        quality = "STALE"

    return ReportedReading(
        address=signal.address,
        device_id=signal.device_id,
        signal_id=signal.signal_id,
        reading_class=signal.reading_class,
        at_offset_minutes=at_offset_minutes,
        value=None if freshest is None else freshest.reported_value,
        source_sample_time=(
            None if freshest is None else freshest.source_sample_time
        ),
        source_offset_minutes=(
            None if freshest is None else freshest.at_offset_minutes
        ),
        quality=quality,
        due=signal.due_at(at_offset_minutes),
        outcome=None if attempt is None else attempt.outcome,
        suppression_reason=None if attempt is None else attempt.suppression_reason,
    )


def outcome_counts(
    observations: tuple[DeviceObservation, ...]
) -> dict[str, int]:
    """How many sample attempts reached each outcome.

    Counted rather than asserted, because "the gap suppressed something" is the
    claim, and a count of zero is what a suppression that never happened looks
    like. A screen showing these numbers is showing whether the mechanism did
    anything at all.
    """
    counts: dict[str, int] = {}
    for item in observations:
        counts[item.outcome] = counts.get(item.outcome, 0) + 1
    return counts
