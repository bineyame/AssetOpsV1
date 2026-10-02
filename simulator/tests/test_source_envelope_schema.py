"""The canonical source envelope's strict schema, as a negative corpus.

Every case below starts from one valid envelope and breaks it in exactly ONE way,
so a refusal is attributable to the break rather than to a second malformation
the parser happened to reach first. Each case asserts the rejection KIND and the
FIELD, because "it raised" would pass for a parser that refused everything.

The privacy cases try to smuggle private data in, rather than searching a
happy-path payload for a field name that was never going to be there: a true
value, a cause, an event label, an oracle expectation, a controller intent, an
accepted flow set, a raw observation and a whole Lab projection are each offered
to the parser and to the stage, at the top level and nested inside the payload.
"""

from __future__ import annotations

import copy
import dataclasses
import json
from fractions import Fraction

import pytest

from assetops_contracts.execution_contract import EXECUTION_CONTRACT_VERSION
from assetops_contracts.observation import DeviceObservation
from assetops_contracts.source_envelope import (
    ENVELOPE_REJECTION_KINDS,
    SOURCE_ENVELOPE_SCHEMA_VERSION,
    EnvelopeRejected,
    SourceEnvelope,
    SourceMappingEntry,
    SourceMappingSet,
    canonical_envelope_json,
    check_against_mapping,
    envelope_document,
    envelope_message_id,
    parse_canonical_envelope_json,
    parse_source_envelope,
)
from assetops_contracts.source_stage import SourceStage, admit

MAPPING = SourceMappingSet(
    mapping_set_id="a-gateway-mapping",
    mapping_version=1,
    publication_latency_seconds=3,
    entries=(
        SourceMappingEntry(
            device_id="fuel-level-sensor",
            signal_id="fuel-level",
            measurement="STATE_AT_INSTANT",
            unit="L",
            publishes_unavailable=True,
        ),
        SourceMappingEntry(
            device_id="generator-controller",
            signal_id="ac-power",
            measurement="INTERVAL_MEAN",
            unit="kW",
            publishes_unavailable=False,
        ),
    ),
)


def envelope(**changes) -> SourceEnvelope:
    fields = dict(
        site_id="MG-001",
        source_id="simulator-lab-source",
        gateway_id="simulator-lab-gateway",
        device_id="fuel-level-sensor",
        signal_id="fuel-level",
        mapping_set_id="a-gateway-mapping",
        mapping_version=1,
        sequence=91,
        source_time="2026-09-22T00:45:00Z",
        published_at="2026-09-22T00:45:03Z",
        measurement="STATE_AT_INSTANT",
        value=Fraction(9338, 25),
        unit="L",
        quality="GOOD",
        unavailable_reason=None,
        interval_start=None,
        interval_end=None,
    )
    fields.update(changes)
    if "message_id" not in fields:
        fields["message_id"] = envelope_message_id(
            site_id=fields["site_id"],
            gateway_id=fields["gateway_id"],
            source_id=fields["source_id"],
            device_id=fields["device_id"],
            signal_id=fields["signal_id"],
            source_time=fields["source_time"],
        )
    return SourceEnvelope(**fields)


def document() -> dict:
    return envelope_document(envelope())


def rejected(candidate: object, kind: str, field: str | None = None) -> None:
    with pytest.raises(EnvelopeRejected) as raised:
        parse_source_envelope(candidate)
    assert raised.value.kind == kind, raised.value
    if field is not None:
        assert raised.value.field == field, raised.value


class TestTheValidEnvelope:
    def test_it_round_trips_losslessly_through_canonical_text(self) -> None:
        original = envelope()
        text = canonical_envelope_json(original)

        parsed = parse_canonical_envelope_json(text)

        assert parsed == original
        assert canonical_envelope_json(parsed) == text
        assert parsed.value == Fraction(9338, 25)
        assert '"value":"373.52"' in text

    def test_it_carries_every_field_criterion_one_names(self) -> None:
        doc = document()

        assert doc["source"] == {
            "site_id": "MG-001",
            "source_id": "simulator-lab-source",
            "gateway_id": "simulator-lab-gateway",
            "device_id": "fuel-level-sensor",
            "signal_id": "fuel-level",
        }
        assert doc["mapping"] == {
            "mapping_set_id": "a-gateway-mapping",
            "mapping_version": 1,
        }
        assert doc["schema"] == {
            "id": "assetops.source-envelope",
            "version": 1,
        }
        assert set(doc["message"]) == {"message_id", "sequence"}
        assert doc["timing"] == {
            "source_time": "2026-09-22T00:45:00Z",
            "published_at": "2026-09-22T00:45:03Z",
        }
        assert doc["payload"]["quality"] == "GOOD"
        assert doc["payload"]["unit"] == "L"

    def test_received_at_is_not_a_field_and_is_refused_by_name(self) -> None:
        assert "received_at" not in json.dumps(document())
        candidate = document()
        candidate["timing"]["received_at"] = "2026-09-22T00:45:05Z"

        rejected(candidate, "UNKNOWN_FIELD", "timing.received_at")

    def test_the_schema_version_is_not_the_execution_contract_version(
        self,
    ) -> None:
        # Independent numbers. If they happen to coincide one day that is not a
        # coupling, but this build proves they are not the same constant.
        assert SOURCE_ENVELOPE_SCHEMA_VERSION == 2
        assert EXECUTION_CONTRACT_VERSION == 9


class TestUnknownAndPrivateFieldsAreRefused:
    @pytest.mark.parametrize(
        ("level", "name", "value"),
        [
            (None, "true_value", "254.02"),
            (None, "private_state", [{"value": "254.02"}]),
            (None, "cause", "fuel-removal"),
            (None, "event_id", "fuel-level-reporting-gap"),
            (None, "expectation", {"kind": "TRAJECTORY"}),
            (None, "control_intent", {"requested_kw": "30"}),
            (None, "accepted_flow_set", {"accepted_kw": "22"}),
            (None, "suppression_reason", "fuel-level-reporting-gap forces"),
            (None, "notes", ["anything"]),
            ("payload", "true_value", "254.02"),
            ("payload", "cause", "fuel-removal"),
            ("payload", "oracle", "TRAJECTORY"),
            ("payload", "bias", "-0.5"),
            ("source", "address", "fuel-tank-volume@fuel-tank"),
            ("source", "scenario_id", "fuel-loss-event"),
            ("timing", "received_at", "2026-09-22T00:45:05Z"),
            ("message", "run_id", "run-1"),
            ("mapping", "entries", []),
            ("schema", "note", "x"),
        ],
    )
    def test_a_smuggled_field_is_refused_wherever_it_is_put(
        self, level: str | None, name: str, value: object
    ) -> None:
        candidate = document()
        (candidate if level is None else candidate[level])[name] = value

        rejected(candidate, "UNKNOWN_FIELD", f"{level or 'envelope'}.{name}")

    def test_a_raw_observation_is_not_an_envelope(self) -> None:
        observation = DeviceObservation(
            device_id="fuel-level-sensor",
            signal_id="fuel-level",
            address="fuel-tank-volume@fuel-tank",
            state_key="fuel-tank-volume",
            reading_class="STATE_SIGNAL",
            at_offset_minutes=1485,
            source_sample_time="2026-09-22T00:45:00Z",
            outcome="REPORTED",
            reported_value=Fraction(9338, 25),
            canonical_unit="L",
        )
        rejected(observation, "NOT_AN_ENVELOPE")
        # And its fields as a mapping: the shape is not the envelope's.
        rejected(dataclasses.asdict(observation), "UNKNOWN_FIELD")

    @pytest.mark.parametrize(
        "private",
        [
            {"world_state": {"fuel-tank-volume@fuel-tank": "254.02"}},
            {"control_intent": {"generator": "30"}, "interval": "[T, T+dt)"},
            {"accepted_flow_set": {"generator": "22"}},
            {"status": "RUNNING", "private_state": [], "observations": []},
            {"expectations": [{"kind": "TRAJECTORY"}]},
        ],
    )
    def test_a_private_record_shaped_as_data_is_not_an_envelope(
        self, private: dict
    ) -> None:
        rejected(private, "UNKNOWN_FIELD")

    def test_a_private_record_cannot_be_staged_either(self) -> None:
        stage = SourceStage(
            run_id="run-1",
            site_id="MG-001",
            source_id="simulator-lab-source",
            gateway_id="simulator-lab-gateway",
            mapping=MAPPING,
        )
        for candidate in (
            document(),
            {"true_value": "254.02"},
            DeviceObservation(
                device_id="fuel-level-sensor",
                signal_id="fuel-level",
                address="fuel-tank-volume@fuel-tank",
                state_key="fuel-tank-volume",
                reading_class="STATE_SIGNAL",
                at_offset_minutes=1485,
                source_sample_time="2026-09-22T00:45:00Z",
                outcome="REPORTED",
                reported_value=Fraction(9338, 25),
                canonical_unit="L",
            ),
            object(),
        ):
            with pytest.raises(EnvelopeRejected) as raised:
                admit(stage, [candidate])
            assert raised.value.kind == "NOT_AN_ENVELOPE"

    def test_there_is_no_free_text_field_to_smuggle_a_sentence_through(
        self,
    ) -> None:
        # Every string-valued field is either an identifier, a UTC instant, a
        # closed vocabulary value, a digest, or an exact number. A sentence fits
        # none of them.
        sentence = "the fuel was stolen at 01:00"
        for level, name in [
            ("source", "device_id"),
            ("payload", "quality"),
            ("payload", "measurement"),
            ("payload", "unavailable_reason"),
            ("payload", "unit"),
            ("payload", "value"),
            ("timing", "source_time"),
            ("message", "message_id"),
        ]:
            candidate = document()
            candidate[level][name] = sentence
            with pytest.raises(EnvelopeRejected):
                parse_source_envelope(candidate)


class TestIdentityAndStructure:
    @pytest.mark.parametrize(
        ("level", "name"),
        [
            ("source", "site_id"),
            ("source", "device_id"),
            ("mapping", "mapping_version"),
            ("timing", "published_at"),
            ("payload", "quality"),
            ("message", "sequence"),
            ("schema", "version"),
        ],
    )
    def test_a_missing_field_is_refused(self, level: str, name: str) -> None:
        candidate = document()
        del candidate[level][name]
        rejected(candidate, "MISSING_FIELD", f"{level}.{name}")

    def test_a_message_id_that_is_not_this_publication_is_refused(self) -> None:
        candidate = document()
        candidate["message"]["message_id"] = "0" * 64
        rejected(candidate, "INVALID_IDENTITY", "message.message_id")

    def test_changing_an_identity_field_invalidates_the_message_id(self) -> None:
        candidate = document()
        candidate["source"]["device_id"] = "another-sensor"
        rejected(candidate, "INVALID_IDENTITY", "message.message_id")

    @pytest.mark.parametrize("bad", ["", " MG-001", "MG 001", "mg/001", "-x", "a" * 129])
    def test_an_invalid_identifier_is_refused(self, bad: str) -> None:
        candidate = document()
        candidate["source"]["site_id"] = bad
        rejected(candidate, "INVALID_IDENTITY", "source.site_id")

    @pytest.mark.parametrize("bad", [0, -1, True, 1.0, "91"])
    def test_a_sequence_is_a_whole_number_from_one(self, bad: object) -> None:
        candidate = document()
        candidate["message"]["sequence"] = bad
        with pytest.raises(EnvelopeRejected) as raised:
            parse_source_envelope(candidate)
        assert raised.value.field == "message.sequence"

    def test_another_schema_version_is_refused_not_reinterpreted(self) -> None:
        candidate = document()
        candidate["schema"]["version"] = 3
        rejected(candidate, "SCHEMA_UNSUPPORTED", "schema.version")

    def test_another_schema_id_is_refused(self) -> None:
        candidate = document()
        candidate["schema"]["id"] = "something-else"
        rejected(candidate, "SCHEMA_UNSUPPORTED", "schema.id")


class TestTiming:
    @pytest.mark.parametrize(
        "bad",
        [
            "2026-09-22 00:45:00Z",
            "2026-09-22T00:45:00+00:00",
            "2026-09-22T00:45:00.000Z",
            "2026-02-30T00:45:00Z",
            "yesterday",
        ],
    )
    def test_a_malformed_instant_is_refused(self, bad: str) -> None:
        candidate = document()
        candidate["timing"]["source_time"] = bad
        rejected(candidate, "INVALID_TIMING", "timing.source_time")

    def test_publication_before_the_sample_is_refused(self) -> None:
        candidate = document()
        candidate["timing"]["published_at"] = "2026-09-22T00:44:59Z"
        rejected(candidate, "INVALID_TIMING", "timing.published_at")

    def test_a_state_reading_names_no_interval(self) -> None:
        candidate = document()
        candidate["payload"]["interval_start"] = "2026-09-22T00:30:00Z"
        candidate["payload"]["interval_end"] = "2026-09-22T00:45:00Z"
        rejected(candidate, "INVALID_TIMING")

    def test_an_interval_mean_ends_at_its_source_time(self) -> None:
        with pytest.raises(EnvelopeRejected) as raised:
            envelope(
                device_id="generator-controller",
                signal_id="ac-power",
                measurement="INTERVAL_MEAN",
                unit="kW",
                value=Fraction(45),
                interval_start="2026-09-22T00:15:00Z",
                interval_end="2026-09-22T00:30:00Z",
            )
        assert raised.value.field == "payload.interval_end"

    def test_an_interval_mean_names_the_span_it_summarises(self) -> None:
        with pytest.raises(EnvelopeRejected) as raised:
            envelope(
                device_id="generator-controller",
                signal_id="ac-power",
                measurement="INTERVAL_MEAN",
                unit="kW",
                value=Fraction(45),
            )
        assert raised.value.kind == "INVALID_TIMING"

    def test_a_valid_interval_mean_keeps_its_span(self) -> None:
        mean = envelope(
            device_id="generator-controller",
            signal_id="ac-power",
            measurement="INTERVAL_MEAN",
            unit="kW",
            value=Fraction(45),
            interval_start="2026-09-22T00:30:00Z",
            interval_end="2026-09-22T00:45:00Z",
        )
        parsed = parse_canonical_envelope_json(canonical_envelope_json(mean))
        assert (parsed.interval_start, parsed.interval_end) == (
            "2026-09-22T00:30:00Z",
            "2026-09-22T00:45:00Z",
        )
        assert parsed.measurement == "INTERVAL_MEAN"


class TestPayload:
    def test_a_float_value_is_refused(self) -> None:
        candidate = document()
        candidate["payload"]["value"] = 373.52
        rejected(candidate, "WRONG_TYPE", "payload.value")

    def test_a_float_anywhere_in_the_text_is_refused(self) -> None:
        text = canonical_envelope_json(envelope()).replace(
            '"sequence":91', '"sequence":91.0'
        )
        with pytest.raises(EnvelopeRejected) as raised:
            parse_canonical_envelope_json(text)
        assert raised.value.kind == "WRONG_TYPE"

    def test_a_non_canonical_number_spelling_is_refused(self) -> None:
        candidate = document()
        candidate["payload"]["value"] = "373.520"
        rejected(candidate, "NOT_CANONICAL", "payload.value")

    def test_non_canonical_text_is_refused_even_when_it_parses(self) -> None:
        text = json.dumps(document(), indent=2)
        with pytest.raises(EnvelopeRejected) as raised:
            parse_canonical_envelope_json(text)
        assert raised.value.kind == "NOT_CANONICAL"

    def test_a_duplicate_key_is_refused(self) -> None:
        text = canonical_envelope_json(envelope())
        doubled = text.replace('{"interval_end":null,', '{"interval_end":null,"interval_end":null,')
        with pytest.raises(EnvelopeRejected) as raised:
            parse_canonical_envelope_json(doubled)
        assert raised.value.kind == "MALFORMED_TEXT"

    def test_truncated_text_is_refused(self) -> None:
        text = canonical_envelope_json(envelope())
        with pytest.raises(EnvelopeRejected) as raised:
            parse_canonical_envelope_json(text[: len(text) // 2])
        assert raised.value.kind == "MALFORMED_TEXT"

    def test_a_good_reading_without_a_value_is_refused(self) -> None:
        candidate = document()
        candidate["payload"]["value"] = None
        rejected(candidate, "INVALID_PAYLOAD", "payload.value")

    def test_an_unavailable_reading_with_a_value_is_refused(self) -> None:
        # The fabricated value this whole vocabulary refuses.
        candidate = document()
        candidate["payload"]["quality"] = "UNAVAILABLE"
        candidate["payload"]["unavailable_reason"] = "NO_MEASUREMENT"
        rejected(candidate, "INVALID_PAYLOAD", "payload.value")

    @pytest.mark.parametrize(
        "quality", ["STALE", "SUPPRESSED_BY_GAP", "DROPPED", "good"]
    )
    def test_a_quality_outside_the_vocabulary_is_refused(
        self, quality: str
    ) -> None:
        candidate = document()
        candidate["payload"]["quality"] = quality
        rejected(candidate, "INVALID_PAYLOAD", "payload.quality")

    def test_an_unavailable_reason_outside_the_vocabulary_is_refused(
        self,
    ) -> None:
        candidate = document()
        candidate["payload"]["quality"] = "UNAVAILABLE"
        candidate["payload"]["value"] = None
        candidate["payload"]["unavailable_reason"] = "SUPPRESSED_BY_GAP"
        rejected(candidate, "INVALID_PAYLOAD", "payload.unavailable_reason")


class TestAgainstTheFrozenMapping:
    def test_a_mapped_envelope_passes(self) -> None:
        entry = check_against_mapping(envelope(), MAPPING)
        assert entry.key == ("fuel-level-sensor", "fuel-level")

    def test_an_incompatible_unit_is_refused_not_converted(self) -> None:
        with pytest.raises(EnvelopeRejected) as raised:
            check_against_mapping(
                envelope(unit="mL", value=Fraction(373520)), MAPPING
            )
        assert raised.value.kind == "UNIT_INCOMPATIBLE"

    def test_another_mapping_version_is_refused(self) -> None:
        with pytest.raises(EnvelopeRejected) as raised:
            check_against_mapping(envelope(mapping_version=2), MAPPING)
        assert raised.value.kind == "MAPPING_INCOMPATIBLE"

    def test_a_signal_off_the_allowlist_is_refused(self) -> None:
        with pytest.raises(EnvelopeRejected) as raised:
            check_against_mapping(
                envelope(device_id="bms", signal_id="soc", unit="%"), MAPPING
            )
        assert raised.value.kind == "MAPPING_INCOMPATIBLE"
        assert raised.value.field == "source.signal_id"

    def test_a_measurement_class_the_mapping_does_not_publish_is_refused(
        self,
    ) -> None:
        with pytest.raises(EnvelopeRejected) as raised:
            check_against_mapping(
                envelope(
                    measurement="INTERVAL_MEAN",
                    interval_start="2026-09-22T00:30:00Z",
                    interval_end="2026-09-22T00:45:00Z",
                ),
                MAPPING,
            )
        assert raised.value.kind == "MAPPING_INCOMPATIBLE"

    def test_unavailability_on_a_signal_that_does_not_publish_it_is_refused(
        self,
    ) -> None:
        with pytest.raises(EnvelopeRejected) as raised:
            check_against_mapping(
                envelope(
                    device_id="generator-controller",
                    signal_id="ac-power",
                    measurement="INTERVAL_MEAN",
                    unit="kW",
                    value=None,
                    quality="UNAVAILABLE",
                    unavailable_reason="NO_COMPLETED_INTERVAL",
                ),
                MAPPING,
            )
        assert raised.value.kind == "MAPPING_INCOMPATIBLE"


def test_every_rejection_kind_is_reached_by_this_corpus() -> None:
    """Anti-vacuity: a rejection kind nothing produces is a list, not a guard."""
    reached: set[str] = set()
    probes = []
    base = document()

    def probe(mutate) -> None:
        candidate = copy.deepcopy(base)
        mutate(candidate)
        probes.append(candidate)

    probe(lambda d: d["payload"].update(value="373.520"))
    probe(lambda d: d["timing"].update(received_at="x"))
    probe(lambda d: d["payload"].pop("unit"))
    probe(lambda d: d["payload"].update(value=1.5))
    probe(lambda d: d["schema"].update(version=3))
    probe(lambda d: d["message"].update(message_id="0" * 64))
    probe(lambda d: d["timing"].update(source_time="later"))
    probe(lambda d: d["payload"].update(quality="STALE"))
    for candidate in [*probes, "not a mapping"]:
        try:
            parse_source_envelope(candidate)
        except EnvelopeRejected as error:
            reached.add(error.kind)
    for text in ("{", '{"a":1,"a":2}'):
        try:
            parse_canonical_envelope_json(text)
        except EnvelopeRejected as error:
            reached.add(error.kind)
    for broken in (envelope(unit="mL"), envelope(mapping_version=2)):
        try:
            check_against_mapping(broken, MAPPING)
        except EnvelopeRejected as error:
            reached.add(error.kind)

    assert reached == ENVELOPE_REJECTION_KINDS
