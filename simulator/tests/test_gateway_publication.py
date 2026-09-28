"""The simulated gateway: which observations become envelopes, and exactly how.

Built from hand-made `DeviceObservation` records rather than a kernel run, so
each claim is about the gateway alone. `host/tests/test_source_staging.py` proves
the same things against a real execution of the shipped Fuel Loss Event.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from assetops_contracts.observation import DeviceObservation
from assetops_contracts.source_envelope import (
    EnvelopeRejected,
    SourceMappingEntry,
    SourceMappingSet,
    canonical_envelope_json,
)
from assetops_contracts.world_inputs import FrozenInterval
from assetops_simulator.gateway.mappings import SIMULATOR_LAB_GATEWAY_MAPPINGS
from assetops_simulator.gateway.publish import publish

INTERVAL = FrozenInterval(
    start_time="2026-09-21T00:00:00Z",
    end_time="2026-09-21T02:00:00Z",
    duration_minutes=120,
    timestep_minutes=15,
)

WITH_POWER = SourceMappingSet(
    mapping_set_id="a-test-mapping",
    mapping_version=1,
    publication_latency_seconds=3,
    entries=(
        *SIMULATOR_LAB_GATEWAY_MAPPINGS.entries,
        SourceMappingEntry(
            device_id="generator-controller",
            signal_id="ac-power",
            measurement="INTERVAL_MEAN",
            unit="kW",
            publishes_unavailable=True,
        ),
    ),
)


def fuel(offset: int, outcome: str = "REPORTED", value: str | None = "373.52"):
    minutes = f"{offset // 60:02d}:{offset % 60:02d}"
    return DeviceObservation(
        device_id="fuel-level-sensor",
        signal_id="fuel-level",
        address="fuel-tank-volume@fuel-tank",
        state_key="fuel-tank-volume",
        reading_class="STATE_SIGNAL",
        at_offset_minutes=offset,
        source_sample_time=f"2026-09-21T{minutes}:00Z",
        outcome=outcome,
        reported_value=None if outcome != "REPORTED" else Fraction(value),
        canonical_unit="L",
        suppression_reason=(
            None
            if outcome == "REPORTED"
            else "fuel-level-reporting-gap forces the path unavailable"
        ),
    )


def power(offset: int, outcome: str = "REPORTED", value: str | None = "45"):
    minutes = f"{offset // 60:02d}:{offset % 60:02d}"
    return DeviceObservation(
        device_id="generator-controller",
        signal_id="ac-power",
        address="generator-output-power@generator",
        state_key="generator-output-power",
        reading_class="INTERVAL_SIGNAL",
        at_offset_minutes=offset,
        source_sample_time=f"2026-09-21T{minutes}:00Z",
        outcome=outcome,
        reported_value=None if outcome != "REPORTED" else Fraction(value),
        canonical_unit="kW",
        suppression_reason=None if outcome == "REPORTED" else "no interval",
    )


def published(observations, mapping=SIMULATOR_LAB_GATEWAY_MAPPINGS):
    return publish(
        tuple(observations),
        mapping,
        INTERVAL,
        site_id="MG-001",
        source_id="simulator-lab-source",
        gateway_id="simulator-lab-gateway",
    )


class TestAGeneratedSampleBecomesOneCanonicalEnvelope:
    def test_the_source_time_is_the_sample_time_and_publication_is_later(
        self,
    ) -> None:
        (envelope,) = published([fuel(45)])

        assert envelope.source_time == "2026-09-21T00:45:00Z"
        assert envelope.published_at == "2026-09-21T00:45:03Z"
        assert envelope.value == Fraction("373.52")
        assert envelope.quality == "GOOD"
        assert envelope.measurement == "STATE_AT_INSTANT"
        assert (envelope.interval_start, envelope.interval_end) == (None, None)
        assert envelope.mapping_set_id == "simulator-lab-gateway-fuel"
        assert envelope.mapping_version == 1

    def test_the_reported_value_is_what_the_device_said(self) -> None:
        # Bias included: the gateway publishes the device's number, not the
        # world's, and it has no way to reach the world's.
        (envelope,) = published([fuel(45, value="373.52")])
        assert envelope.value == Fraction("373.52")

    def test_sequences_count_one_signal_from_one(self) -> None:
        envelopes = published([fuel(0), fuel(15), fuel(30)])
        assert [item.sequence for item in envelopes] == [1, 2, 3]


class TestIntervalSemanticsSurviveConversion:
    def test_an_interval_mean_carries_the_span_that_ended_at_its_time(
        self,
    ) -> None:
        (envelope,) = published([power(60)], WITH_POWER)

        assert envelope.measurement == "INTERVAL_MEAN"
        assert envelope.source_time == "2026-09-21T01:00:00Z"
        assert envelope.interval_end == "2026-09-21T01:00:00Z"
        assert envelope.interval_start == "2026-09-21T00:45:00Z"
        assert envelope.value == Fraction(45)

    def test_no_completed_interval_is_a_typed_absence_with_no_span(self) -> None:
        (envelope,) = published(
            [power(0, outcome="NO_PRECEDING_INTERVAL")], WITH_POWER
        )
        assert envelope.quality == "UNAVAILABLE"
        assert envelope.value is None
        assert envelope.unavailable_reason == "NO_COMPLETED_INTERVAL"
        assert (envelope.interval_start, envelope.interval_end) == (None, None)

    def test_a_span_with_nothing_measured_names_the_span(self) -> None:
        (envelope,) = published(
            [power(60, outcome="NO_VALUE_AT_BOUNDARY")], WITH_POWER
        )
        assert envelope.unavailable_reason == "NO_MEASUREMENT"
        assert envelope.interval_start == "2026-09-21T00:45:00Z"
        assert envelope.value is None

    def test_the_last_span_of_an_undivided_interval_is_its_real_length(
        self,
    ) -> None:
        short = FrozenInterval(
            start_time="2026-09-21T00:00:00Z",
            end_time="2026-09-21T00:40:00Z",
            duration_minutes=40,
            timestep_minutes=15,
        )
        (envelope,) = publish(
            (replace(power(40), source_sample_time="2026-09-21T00:40:00Z"),),
            WITH_POWER,
            short,
            site_id="MG-001",
            source_id="simulator-lab-source",
            gateway_id="simulator-lab-gateway",
        )
        assert envelope.interval_start == "2026-09-21T00:30:00Z"


class TestNothingIsInventedForASampleThatWasNotPublished:
    @pytest.mark.parametrize("outcome", ["SUPPRESSED_BY_GAP", "DROPPED"])
    def test_a_sample_never_taken_or_never_arrived_publishes_nothing(
        self, outcome: str
    ) -> None:
        envelopes = published([fuel(0), fuel(15, outcome=outcome), fuel(30)])

        assert [item.source_time for item in envelopes] == [
            "2026-09-21T00:00:00Z",
            "2026-09-21T00:30:00Z",
        ]
        # The next publication's sequence does not skip: a sequence counts
        # publications, and the missing one was never published.
        assert [item.sequence for item in envelopes] == [1, 2]

    def test_the_suppression_sentence_never_crosses(self) -> None:
        envelopes = published(
            [fuel(0), fuel(15, outcome="SUPPRESSED_BY_GAP")], WITH_POWER
        )
        for item in envelopes:
            text = canonical_envelope_json(item)
            assert "reporting-gap" not in text
            assert "forces" not in text

    def test_a_signal_whose_mapping_publishes_no_unavailability_publishes_none(
        self,
    ) -> None:
        silent = SourceMappingSet(
            mapping_set_id="silent",
            mapping_version=1,
            publication_latency_seconds=0,
            entries=(replace(WITH_POWER.entries[1], publishes_unavailable=False),),
        )
        assert published([power(0, outcome="NO_PRECEDING_INTERVAL")], silent) == ()


class TestTheAllowlist:
    def test_the_shipped_allowlist_is_the_fuel_sensor_alone(self) -> None:
        assert [entry.key for entry in SIMULATOR_LAB_GATEWAY_MAPPINGS.entries] == [
            ("fuel-level-sensor", "fuel-level")
        ]

    def test_a_signal_off_the_allowlist_publishes_nothing(self) -> None:
        assert published([power(60)]) == ()

    def test_a_signal_whose_unit_disagrees_with_its_mapping_is_refused(
        self,
    ) -> None:
        with pytest.raises(EnvelopeRejected) as raised:
            published([replace(fuel(0), canonical_unit="mL")])
        assert raised.value.kind == "UNIT_INCOMPATIBLE"

    def test_a_signal_whose_class_disagrees_with_its_mapping_is_refused(
        self,
    ) -> None:
        with pytest.raises(EnvelopeRejected) as raised:
            published([replace(fuel(0), reading_class="INTERVAL_SIGNAL")])
        assert raised.value.kind == "MAPPING_INCOMPATIBLE"

    def test_anything_but_a_device_observation_is_refused(self) -> None:
        with pytest.raises(EnvelopeRejected) as raised:
            published([{"device_id": "fuel-level-sensor"}])
        assert raised.value.kind == "NOT_AN_ENVELOPE"


class TestARetryIsTheSamePublication:
    def test_republishing_a_series_yields_the_same_ids_and_bytes(self) -> None:
        series = [fuel(0), fuel(15), fuel(30, outcome="DROPPED"), fuel(45)]

        first = published(series)
        second = published(series)

        assert [canonical_envelope_json(item) for item in first] == [
            canonical_envelope_json(item) for item in second
        ]

    def test_a_longer_series_extends_without_changing_the_prefix(self) -> None:
        # Staging republishes the whole series after every step, so the
        # envelopes already staged must come out identical each time.
        prefix = published([fuel(0), fuel(15)])
        extended = published([fuel(0), fuel(15), fuel(30)])

        assert extended[: len(prefix)] == prefix

    def test_different_content_keeps_the_identity(self) -> None:
        (before,) = published([fuel(45, value="373.52")])
        (after,) = published([fuel(45, value="373.02")])

        assert before.message_id == after.message_id
        assert canonical_envelope_json(before) != canonical_envelope_json(after)
