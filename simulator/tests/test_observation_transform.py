"""The reporting path as a component, tested without a kernel run.

`host/tests/test_lab_execution.py` proves what the transform does to a real
trajectory. This proves the things that are properties of the transform itself
and would be tested through six other moving parts if they were only asserted
there: the vocabularies are covered, the record refuses the combinations that
would let a fabricated value through, and the exact decimal a screen shows is the
decimal the arithmetic produced.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from assetops_contracts.observation import (
    READING_QUALITIES,
    READING_QUALITY_STATEMENTS,
    REPORTABLE_READING_CLASSES,
    SAMPLE_OUTCOME_STATEMENTS,
    SAMPLE_OUTCOMES,
    DeviceObservation,
    DeviceSignalSpec,
    FrozenReportingInputs,
    ReportedReading,
    ReportingPathWindow,
    exact_decimal_text,
)
from assetops_contracts.trajectory import BoundaryState
from assetops_contracts.world_inputs import FrozenInterval
from assetops_simulator.observation.transform import (
    generate_observations,
    reported_reading,
    world_value,
)

TANK = "fuel-tank-volume@tank"


def spec(**changes) -> DeviceSignalSpec:
    fields = dict(
        device_id="a-sensor",
        signal_id="a-signal",
        address=TANK,
        state_key="fuel-tank-volume",
        reading_class="STATE_SIGNAL",
        canonical_unit="L",
        cadence_minutes=15,
        bias=Fraction(0),
        dropout_per_thousand=0,
        statement="one sensor",
    )
    fields.update(changes)
    return DeviceSignalSpec(**fields)


def boundary(index: int, offset: int, **changes) -> BoundaryState:
    fields = dict(
        step_index=index,
        offset_minutes=offset,
        simulation_time=f"2026-09-21T{offset // 60:02d}:{offset % 60:02d}:00Z",
        stocks=((TANK, Fraction(400)),),
        forcing_exposures=(),
        state_samples=((TANK, Fraction(400)),),
        interval_measurements=(),
        has_preceding_interval=index > 0,
    )
    fields.update(changes)
    return BoundaryState(**fields)


def inputs(signals, gaps=(), timestep: int = 15) -> FrozenReportingInputs:
    return FrozenReportingInputs(
        run_id="run-0",
        publication_profile_id="a-profile",
        publication_profile_version=1,
        seed=7,
        interval=FrozenInterval(
            start_time="2026-09-21T00:00:00Z",
            end_time="2026-09-21T01:00:00Z",
            duration_minutes=60,
            timestep_minutes=timestep,
        ),
        signals=tuple(signals),
        gaps=tuple(gaps),
    )


class TestTheVocabulariesAreCoveredAndClosed:
    def test_every_sample_outcome_has_a_statement_and_no_other_does(
        self,
    ) -> None:
        assert SAMPLE_OUTCOMES
        assert set(SAMPLE_OUTCOME_STATEMENTS) == set(SAMPLE_OUTCOMES)
        for outcome in sorted(SAMPLE_OUTCOMES):
            assert len(SAMPLE_OUTCOME_STATEMENTS[outcome]) > 80

    def test_every_reading_quality_has_a_statement_and_no_other_does(
        self,
    ) -> None:
        assert READING_QUALITIES
        assert set(READING_QUALITY_STATEMENTS) == set(READING_QUALITIES)
        for quality in sorted(READING_QUALITIES):
            assert len(READING_QUALITY_STATEMENTS[quality]) > 60

    def test_a_controller_input_may_not_be_a_published_signal(self) -> None:
        """The third reading class is deliberately absent from this one.

        A controller's view is not published, so no device signal may be declared
        for it - which is `controller-view-is-not-the-published-observation` as a
        constructor rather than as a sentence.
        """
        assert "CONTROLLER_INPUT" not in REPORTABLE_READING_CLASSES

        with pytest.raises(ValueError) as raised:
            spec(reading_class="CONTROLLER_INPUT")

        assert "not published" in str(raised.value)


class TestAReadingRecordRefusesTheFabricatedCases:
    def test_an_absent_reading_may_not_carry_a_number(self) -> None:
        with pytest.raises(ValueError) as raised:
            DeviceObservation(
                device_id="a-sensor",
                signal_id="a-signal",
                address=TANK,
                state_key="fuel-tank-volume",
                reading_class="STATE_SIGNAL",
                at_offset_minutes=0,
                source_sample_time="2026-09-21T00:00:00Z",
                outcome="DROPPED",
                reported_value=Fraction(400),
                canonical_unit="L",
                suppression_reason="a reason",
            )

        assert "did not happen has no number" in str(raised.value)

    def test_a_published_reading_may_not_carry_a_reason(self) -> None:
        with pytest.raises(ValueError) as raised:
            DeviceObservation(
                device_id="a-sensor",
                signal_id="a-signal",
                address=TANK,
                state_key="fuel-tank-volume",
                reading_class="STATE_SIGNAL",
                at_offset_minutes=0,
                source_sample_time="2026-09-21T00:00:00Z",
                outcome="REPORTED",
                reported_value=Fraction(400),
                canonical_unit="L",
                suppression_reason="a reason",
            )

        assert "nothing to explain" in str(raised.value)

    def test_a_reading_published_now_is_not_a_retained_one(self) -> None:
        """`STALE` means the newest reading is older than this instant.

        A record saying both would be the one thing the quality exists to stop: a
        value shown as retained that was in fact taken now, or the reverse.
        """
        with pytest.raises(ValueError) as raised:
            ReportedReading(
                address=TANK,
                device_id="a-sensor",
                signal_id="a-signal",
                reading_class="STATE_SIGNAL",
                at_offset_minutes=30,
                value=Fraction(400),
                source_sample_time="2026-09-21T00:30:00Z",
                source_offset_minutes=30,
                quality="STALE",
                due=True,
                outcome="REPORTED",
                suppression_reason=None,
            )

        assert "not a retained one" in str(raised.value)

    def test_two_paths_may_not_share_one_key(self) -> None:
        with pytest.raises(ValueError) as raised:
            inputs((spec(), spec()))

        assert "one path with two" in str(raised.value)


class TestWhatTheTransformReads:
    def test_a_state_signal_reads_the_sample_and_not_the_stock(self) -> None:
        """A stock the model cannot sample is not reportable at all.

        The distinction only shows when the two differ, so they are made to: the
        stock says 400 and the sampling phase produced nothing, and the answer is
        that there is nothing to report rather than 400.
        """
        unsampled = boundary(0, 0, state_samples=())

        assert world_value(unsampled, spec(), None) is None
        assert unsampled.stock(TANK) == Fraction(400)

    def test_an_interval_signal_publishes_the_mean_over_the_span(self) -> None:
        """11.25 kWh over fifteen minutes is 45 kW, exactly.

        `an-interval-reading-is-a-mean-over-the-span`. Exact rational division,
        so a forced 45 kW comes back as 45 and not as 44.999999999999996.
        """
        measured = boundary(
            1,
            15,
            interval_measurements=((TANK, Fraction(45, 4)),),
        )
        power = spec(reading_class="INTERVAL_SIGNAL", canonical_unit="kW")

        assert world_value(measured, power, 15) == Fraction(45)
        # And a span it was not told about is not guessed at.
        assert world_value(measured, power, None) is None

    def test_the_bias_is_applied_to_the_reading_and_nowhere_else(self) -> None:
        published = generate_observations(
            (boundary(0, 0),), inputs((spec(bias=Fraction(-1, 2)),))
        )

        assert len(published) == 1
        assert published[0].reported_value == Fraction(799, 2)
        # The world is untouched: the boundary still says 400.
        assert boundary(0, 0).state_sample(TANK) == Fraction(400)

    def test_a_gap_suppresses_the_signal_it_names_and_not_its_neighbour(
        self,
    ) -> None:
        """Keyed on the whole signal key, not on the address.

        Two sensors on one tank are two paths. Cutting one says nothing about the
        other, and an address-keyed window would silence both.
        """
        first = spec(device_id="sensor-one")
        second = spec(device_id="sensor-two")
        window = ReportingPathWindow(
            event_id="a-gap",
            condition_address="fuel-level-reporting-availability@tank",
            device_id="sensor-one",
            signal_id="a-signal",
            address=TANK,
            offset_minutes=0,
            duration_minutes=30,
            interval_minutes=60,
        )

        published = generate_observations(
            (boundary(0, 0),), inputs((first, second), (window,))
        )
        by_device = {item.device_id: item.outcome for item in published}

        assert by_device == {
            "sensor-one": "SUPPRESSED_BY_GAP",
            "sensor-two": "REPORTED",
        }

    def test_a_window_is_half_open_at_both_ends(self) -> None:
        window = ReportingPathWindow(
            event_id="a-gap",
            condition_address="fuel-level-reporting-availability@tank",
            device_id="a-sensor",
            signal_id="a-signal",
            address=TANK,
            offset_minutes=15,
            duration_minutes=30,
            interval_minutes=60,
        )

        assert window.covers(15) is True
        assert window.covers(44) is True
        assert window.covers(45) is False
        assert window.covers(14) is False
        assert window.end_offset_minutes == 45

    def test_an_interval_wide_condition_runs_to_the_end_of_the_interval(
        self,
    ) -> None:
        """A `duration_minutes` of `None` is the run's own length.

        Stated here because the alternative reading - a window of zero length -
        would silence nothing at all while looking like a declared gap.
        """
        window = ReportingPathWindow(
            event_id="a-gap",
            condition_address="fuel-level-reporting-availability@tank",
            device_id="a-sensor",
            signal_id="a-signal",
            address=TANK,
            offset_minutes=0,
            duration_minutes=None,
            interval_minutes=60,
        )

        assert window.end_offset_minutes == 60
        assert window.covers(59) is True
        assert window.covers(60) is False

    def test_a_retained_reading_is_the_newest_one_at_or_before_the_instant(
        self,
    ) -> None:
        published = generate_observations(
            (boundary(0, 0), boundary(1, 15), boundary(2, 30)),
            inputs(
                (spec(),),
                (
                    ReportingPathWindow(
                        event_id="a-gap",
                        condition_address="x@tank",
                        device_id="a-sensor",
                        signal_id="a-signal",
                        address=TANK,
                        offset_minutes=15,
                        duration_minutes=30,
                        interval_minutes=60,
                    ),
                ),
            ),
        )

        fresh = reported_reading(published, spec(), 0)
        retained = reported_reading(published, spec(), 30)

        assert fresh.quality == "GOOD"
        assert fresh.source_offset_minutes == 0
        assert retained.quality == "STALE"
        assert retained.source_offset_minutes == 0
        assert retained.value == fresh.value
        assert retained.outcome == "SUPPRESSED_BY_GAP"


class TestTheExactDecimalAScreenShows:
    @pytest.mark.parametrize(
        "value,text",
        [
            (Fraction(500), "500"),
            (Fraction(2799, 800), "3.49875"),
            (Fraction(12701, 50), "254.02"),
            (Fraction(-1, 2), "-0.5"),
            (Fraction(0), "0"),
            (Fraction(1, 8), "0.125"),
        ],
    )
    def test_a_rational_with_a_decimal_is_shown_as_that_decimal(
        self, value: Fraction, text: str
    ) -> None:
        """No float anywhere on the way to a screen.

        2799/800 is exactly 3.49875, and a payload that printed
        3.4987499999999997 would state a precision the arithmetic does not have -
        in the one product whose numeric policy is that it never rounds.
        """
        assert exact_decimal_text(value) == text

    def test_a_rational_with_no_decimal_is_shown_as_the_ratio(self) -> None:
        """A third is not 0.333..., and rounding it would be inventing digits."""
        assert exact_decimal_text(Fraction(1, 3)) == "1/3"
