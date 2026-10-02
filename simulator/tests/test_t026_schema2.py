"""T026: envelope schema 2, records, delays and the absorbed parser carries.

AC1 (schema move with schema 1 still read), AC4 (record family), AC5 (strict
validation incl. R2/R3), AC7 (source vs publication time), AC8 (enum, never
noised) and the T025b enum-check-order carry.
"""

from __future__ import annotations

import copy
import json
from fractions import Fraction

import pytest

from assetops_contracts.observation import DeviceObservation, PublicationDelayWindow
from assetops_contracts.operational_records import (
    FrozenRecordInputs,
    OverrideCommand,
    PolicyDeclaration,
    RecordGap,
)
from assetops_contracts.source_envelope import (
    EnvelopeRejected,
    SourceMappingEntry,
    SourceMappingSet,
    canonical_envelope_json,
    check_against_mapping,
    envelope_message_id,
    mapping_set_document,
    parse_canonical_envelope_json,
    parse_mapping_set,
    parse_source_envelope,
)
from assetops_contracts.trajectory import BoundaryState
from assetops_simulator.gateway.mappings import (
    SIMULATOR_LAB_DISPATCH_MAPPINGS,
    SIMULATOR_LAB_GATEWAY_MAPPINGS,
)
from assetops_simulator.gateway.publish import publish
from assetops_simulator.observation.records import generate_records
from tests.test_gateway_publication import INTERVAL, fuel

IDS = dict(site_id="MG-001", source_id="simulator-lab-source", gateway_id="simulator-lab-gateway")


def status(offset: int, outcome: str = "REPORTED", value: str | None = "RUNNING"):
    minutes = f"{offset // 60:02d}:{offset % 60:02d}"
    return DeviceObservation(
        device_id="generator-controller",
        signal_id="status",
        address="generator-state@generator",
        state_key="generator-state",
        reading_class="STATE_SIGNAL",
        at_offset_minutes=offset,
        source_sample_time=f"2026-09-21T{minutes}:00Z",
        outcome=outcome,
        reported_value=value if outcome == "REPORTED" else None,
        canonical_unit="state",
        suppression_reason=None if outcome == "REPORTED" else "a reason",
    )


def soc(offset: int):
    minutes = f"{offset // 60:02d}:{offset % 60:02d}"
    return DeviceObservation(
        device_id="battery-pcs-controller",
        signal_id="state-of-charge",
        address="battery-state-of-charge@battery",
        state_key="battery-state-of-charge",
        reading_class="STATE_SIGNAL",
        at_offset_minutes=offset,
        source_sample_time=f"2026-09-21T{minutes}:00Z",
        outcome="REPORTED",
        reported_value=Fraction(55),
        canonical_unit="%",
    )


def dispatch(observations, **kwargs):
    return publish(tuple(observations), SIMULATOR_LAB_DISPATCH_MAPPINGS, INTERVAL, **IDS, **kwargs)


def boundaries(*offsets):
    return tuple(
        BoundaryState(
            step_index=index,
            offset_minutes=offset,
            simulation_time=f"2026-09-21T{offset // 60:02d}:{offset % 60:02d}:00Z",
            stocks=(),
            forcing_exposures=(),
            state_samples=(),
            interval_measurements=(),
            has_preceding_interval=index > 0,
        )
        for index, offset in enumerate(offsets)
    )


RECORDS = FrozenRecordInputs(
    run_id="run-1",
    interval=INTERVAL,
    policies=(
        PolicyDeclaration(
            device_id="generator-controller",
            signal_id="policy-stop-soc-threshold",
            control="generator-stop-soc-threshold",
            component_id="generator",
            value=Fraction(90),
            members=None,
            unit="%",
            policy_version=2,
            policy_source="FOUNDATION",
            effective_start="2026-09-01T00:00:00Z",
        ),
        PolicyDeclaration(
            device_id="site-controller",
            signal_id="policy-source-priority",
            control="source-priority",
            component_id=None,
            value=None,
            members=("pv-array", "battery", "generator"),
            unit="order",
            policy_version=2,
            policy_source="FOUNDATION",
            effective_start="2026-09-01T00:00:00Z",
        ),
    ),
    overrides=(
        OverrideCommand(
            event_id="stop-threshold-override",
            device_id="generator-controller",
            signal_id="override-command",
            control="generator-stop-soc-threshold",
            component_id="generator",
            value=Fraction(60),
            unit="%",
            occurrence_offset_minutes=30,
            effective_start_offset_minutes=30,
            effective_end_offset_minutes=90,
        ),
    ),
)


class TestSchemaTwoMeasurements:
    def test_a_status_is_published_as_its_member_and_round_trips(self) -> None:
        (envelope,) = dispatch([status(15)])
        assert envelope.schema_version == 2 and envelope.value == "RUNNING"
        text = canonical_envelope_json(envelope)
        assert '"value":"RUNNING"' in text and '"family":"MEASUREMENT"' in text
        assert parse_canonical_envelope_json(text) == envelope

    def test_a_member_the_mapping_does_not_declare_is_refused(self) -> None:
        (envelope,) = dispatch([status(15)])
        document = json.loads(canonical_envelope_json(envelope))
        document["payload"]["value"] = "IDLING"
        with pytest.raises(EnvelopeRejected) as refused:
            check_against_mapping(parse_source_envelope(document), SIMULATOR_LAB_DISPATCH_MAPPINGS)
        assert refused.value.kind == "MAPPING_INCOMPATIBLE"

    def test_a_member_disguised_as_a_number_is_refused(self) -> None:
        (envelope,) = dispatch([status(15)])
        document = json.loads(canonical_envelope_json(envelope))
        document["payload"]["value"] = "2"
        with pytest.raises(EnvelopeRejected):
            check_against_mapping(parse_source_envelope(document), SIMULATOR_LAB_DISPATCH_MAPPINGS)

    def test_schema_one_still_refuses_an_enum_and_a_family(self) -> None:
        (envelope,) = publish((fuel(15),), SIMULATOR_LAB_GATEWAY_MAPPINGS, INTERVAL, **IDS)
        document = json.loads(canonical_envelope_json(envelope))
        assert "family" not in document["payload"]
        document["payload"]["family"] = "MEASUREMENT"
        with pytest.raises(EnvelopeRejected) as refused:
            parse_source_envelope(document)
        assert refused.value.kind == "UNKNOWN_FIELD"
        document = json.loads(canonical_envelope_json(envelope))
        document["payload"]["unit"] = "state"
        with pytest.raises(EnvelopeRejected):
            parse_source_envelope(document)

    def test_a_schema_two_payload_without_a_family_is_refused(self) -> None:
        (envelope,) = dispatch([soc(15)])
        document = json.loads(canonical_envelope_json(envelope))
        del document["payload"]["family"]
        with pytest.raises(EnvelopeRejected) as refused:
            parse_source_envelope(document)
        assert refused.value.kind == "MISSING_FIELD"


class TestTheEnumCheckPrecedesTheSkip:
    """Backlog T025b C1: all-dropped and all-suppressed still refuse a disguise."""

    DISGUISED = SourceMappingSet(
        mapping_set_id="disguise",
        mapping_version=1,
        publication_latency_seconds=3,
        envelope_schema_version=2,
        entries=(
            SourceMappingEntry(
                device_id="generator-controller",
                signal_id="status",
                measurement="STATE_AT_INSTANT",
                unit="kW",
                publishes_unavailable=True,
                envelope_schema_version=2,
            ),
        ),
    )

    @pytest.mark.parametrize("outcome", ["DROPPED", "SUPPRESSED_BY_GAP"])
    def test_every_attempt_missing_still_refuses(self, outcome) -> None:
        with pytest.raises(EnvelopeRejected) as refused:
            publish((status(15, outcome), status(30, outcome)), self.DISGUISED, INTERVAL, **IDS)
        assert refused.value.kind == "UNIT_INCOMPATIBLE"

    @pytest.mark.parametrize("outcome", ["DROPPED", "SUPPRESSED_BY_GAP"])
    def test_schema_one_refuses_the_enum_with_every_attempt_missing(self, outcome) -> None:
        schema_one = SourceMappingSet(
            mapping_set_id="fuel-plus-status",
            mapping_version=1,
            publication_latency_seconds=3,
            entries=(
                SourceMappingEntry(
                    device_id="generator-controller",
                    signal_id="status",
                    measurement="STATE_AT_INSTANT",
                    unit="kW",
                    publishes_unavailable=True,
                ),
            ),
        )
        with pytest.raises(EnvelopeRejected) as refused:
            publish((status(15, outcome),), schema_one, INTERVAL, **IDS)
        assert refused.value.kind == "MAPPING_INCOMPATIBLE"


class TestRecords:
    def test_policy_and_override_records_publish_and_round_trip(self) -> None:
        records = generate_records(boundaries(0, 15, 30, 45), RECORDS)
        out = dispatch([], records=records)
        assert [e.family for e in out] == ["POLICY", "POLICY", "OPERATIONAL_RECORD"]
        for envelope in out:
            assert parse_canonical_envelope_json(canonical_envelope_json(envelope)) == envelope
            assert envelope.quality is None and envelope.measurement is None
        override = out[2]
        assert override.source_time == "2026-09-21T00:30:00Z"
        assert (override.effective_start, override.effective_end) == (
            "2026-09-21T00:30:00Z",
            "2026-09-21T01:30:00Z",
        )
        assert out[1].members == ("pv-array", "battery", "generator")

    def test_a_record_not_yet_reached_has_not_occurred(self) -> None:
        records = generate_records(boundaries(0, 15), RECORDS)
        assert [r.family for r in records] == ["POLICY", "POLICY"]

    def test_a_gap_on_the_channel_publishes_nothing_for_an_occurred_record(self) -> None:
        inputs = FrozenRecordInputs(
            **{**RECORDS.__dict__, "gaps": (RecordGap("gap", "generator-controller", "override-command", 30, 35),)}
        )
        records = generate_records(boundaries(0, 15, 30), inputs)
        assert records[-1].outcome == "SUPPRESSED_BY_GAP"
        assert [e.family for e in dispatch([], records=records)] == ["POLICY", "POLICY"]

    def test_a_record_payload_carries_no_telemetry_field(self) -> None:
        (envelope,) = dispatch([], records=generate_records(boundaries(0), RECORDS)[:1])
        document = json.loads(canonical_envelope_json(envelope))
        for name in ("quality", "measurement", "interval_start", "received_at"):
            smuggled = copy.deepcopy(document)
            smuggled["payload"][name] = None
            with pytest.raises(EnvelopeRejected) as refused:
                parse_source_envelope(smuggled)
            assert refused.value.kind == "UNKNOWN_FIELD"


class TestDelay:
    def test_a_delay_moves_publication_time_and_nothing_else(self) -> None:
        hold = (PublicationDelayWindow("hold", "battery-pcs-controller", "state-of-charge", 15, 25),)
        timely = dispatch([soc(15), soc(30)])
        late = dispatch([soc(15), soc(30)], delays=hold)
        assert late[0].published_at == "2026-09-21T00:25:03Z"
        assert timely[0].published_at == "2026-09-21T00:15:03Z"
        assert late[1] == timely[1]
        for a, b in zip(late, timely):
            assert (a.message_id, a.value, a.source_time) == (b.message_id, b.value, b.source_time)


class TestParserCarries:
    def test_a_trailing_newline_is_not_an_identifier_or_unit(self) -> None:
        """Review R3: `match` with `$` accepted a final newline."""
        (envelope,) = dispatch([soc(15)])
        for level, name in [("source", "device_id"), ("payload", "unit")]:
            document = json.loads(canonical_envelope_json(envelope))
            document[level][name] = document[level][name] + "\n"
            # The message id is recomputed, so only the newline can refuse it.
            document["message"]["message_id"] = envelope_message_id(
                site_id=document["source"]["site_id"],
                gateway_id=document["source"]["gateway_id"],
                source_id=document["source"]["source_id"],
                device_id=document["source"]["device_id"],
                signal_id=document["source"]["signal_id"],
                source_time=document["timing"]["source_time"],
            )
            with pytest.raises(EnvelopeRejected) as refused:
                parse_source_envelope(document)
            assert refused.value.field == f"{level}.{name}"

    def test_a_zero_denominator_is_a_refusal_not_an_exception(self) -> None:
        """Review R2: `1/0` matched the pattern and raised ZeroDivisionError."""
        (envelope,) = dispatch([soc(15)])
        document = json.loads(canonical_envelope_json(envelope))
        document["payload"]["value"] = "1/0"
        with pytest.raises(EnvelopeRejected) as refused:
            parse_source_envelope(document)
        assert refused.value.kind == "INVALID_PAYLOAD"

    def test_a_schema_one_mapping_persists_exactly_as_before(self) -> None:
        document = mapping_set_document(SIMULATOR_LAB_GATEWAY_MAPPINGS)
        assert set(document) == {
            "mapping_set_id",
            "mapping_version",
            "publication_latency_seconds",
            "entries",
        }
        assert parse_mapping_set(document) == SIMULATOR_LAB_GATEWAY_MAPPINGS
        two = mapping_set_document(SIMULATOR_LAB_DISPATCH_MAPPINGS)
        assert parse_mapping_set(two) == SIMULATOR_LAB_DISPATCH_MAPPINGS
        two["entries"][0]["smuggled"] = 1
        with pytest.raises(EnvelopeRejected):
            parse_mapping_set(two)
