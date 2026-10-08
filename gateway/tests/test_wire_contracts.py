"""SourceEnvelope V3, Batch V2 and the public device report: pinned vectors and refusals."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from assetops_contracts.gateway_report import parse_device_report_text, report_from_observation
from assetops_contracts.ingestion_batch_v2 import (
    BatchRejected,
    parse_canonical_batch_v2_text,
    seal_batch_v2,
)
from assetops_contracts.observation import DeviceObservation
from assetops_contracts.source_envelope import EnvelopeRejected, parse_canonical_envelope_json
from assetops_contracts.source_envelope_v3 import (
    MESSAGE_ID_V3_DOMAIN,
    canonical_envelope_v3_text,
    length_delimited,
    parse_canonical_envelope_v3_text,
    text_sha256,
    v3_message_id,
)

VECTORS = json.loads(
    (Path(__file__).resolve().parents[2] / "contract-fixtures" / "source-envelope-v3-vectors.json").read_text(
        encoding="utf-8"
    )
)


def test_message_id_vectors_are_sha256_over_length_delimited_fields() -> None:
    assert VECTORS["message_id_domain"] == MESSAGE_ID_V3_DOMAIN
    for vector in VECTORS["message_ids"]:
        fields = [
            MESSAGE_ID_V3_DOMAIN,
            vector["site_id"],
            vector["gateway_id"],
            vector["source_id"],
            vector["sequence_epoch"],
            str(vector["sequence"]),
        ]
        # Restated independently of `length_delimited`: 4-byte BE length + UTF-8.
        framed = b"".join(len(f.encode()).to_bytes(4, "big") + f.encode() for f in fields)
        assert framed.hex() == vector["framed_hex"]
        assert hashlib.sha256(framed).hexdigest() == vector["message_id"]
        assert v3_message_id(
            site_id=vector["site_id"],
            gateway_id=vector["gateway_id"],
            source_id=vector["source_id"],
            sequence_epoch=vector["sequence_epoch"],
            sequence=vector["sequence"],
        ) == vector["message_id"]


def test_framing_separates_what_concatenation_would_merge() -> None:
    pair = VECTORS["unframed_collision"]
    assert "".join(pair["a"]) == "".join(pair["b"])
    assert length_delimited(pair["a"]).hex() == pair["a_framed_hex"]
    assert pair["a_framed_hex"] != pair["b_framed_hex"]


def test_envelope_vectors_round_trip_exactly() -> None:
    for vector in VECTORS["envelopes"]:
        envelope = parse_canonical_envelope_v3_text(vector["text"])
        assert canonical_envelope_v3_text(envelope) == vector["text"]
        assert text_sha256(vector["text"]) == vector["sha256"]


def test_v3_text_is_not_read_by_the_historical_v1_v2_parser() -> None:
    with pytest.raises(EnvelopeRejected):
        parse_canonical_envelope_json(VECTORS["envelopes"][0]["text"])


def _doc() -> dict:
    return json.loads(VECTORS["envelopes"][0]["text"])


def _text(document: dict) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@pytest.mark.parametrize(
    ("mutate", "kind", "field"),
    [
        (lambda d: d["payload"].__setitem__("value", "61.50"), "NOT_CANONICAL", "payload.value"),
        (lambda d: d["payload"].__setitem__("value", "1/3"), "NOT_CANONICAL", "payload.value"),
        (lambda d: d["payload"].__setitem__("value", "-0"), "NOT_CANONICAL", "payload.value"),
        (lambda d: d["payload"].__setitem__("value", "1e3"), "NOT_CANONICAL", "payload.value"),
        (lambda d: d["payload"].__setitem__("truth", "60"), "UNKNOWN_FIELD", "payload.truth"),
        (lambda d: d.__setitem__("lab_run_id", "run-1"), "UNKNOWN_FIELD", "lab_run_id"),
        (lambda d: d["timing"].pop("interval_end"), "MISSING_FIELD", "timing.interval_end"),
        (lambda d: d["message"].__setitem__("sequence", 2), "INVALID_IDENTITY", "message.message_id"),
        (lambda d: d["message"].__setitem__("message_id", "0" * 64), "INVALID_IDENTITY", "message.message_id"),
        (lambda d: d["timing"].__setitem__("published_at", "2026-09-30T00:00:00Z"), "INVALID_TIMING", "timing.published_at"),
        (lambda d: d["timing"].__setitem__("source_time", "2026-10-01T08:00:00+00:00"), "INVALID_TIMING", "timing.source_time"),
        (lambda d: d["schema"].__setitem__("version", 2), "SCHEMA_UNSUPPORTED", "schema"),
        (lambda d: d["payload"].__setitem__("family", "POLICY"), "SCHEMA_UNSUPPORTED", "payload.family"),
        (lambda d: d["payload"].__setitem__("quality", "STALE"), "INVALID_PAYLOAD", "payload.quality"),
    ],
)
def test_envelope_refusals_name_their_field(mutate, kind: str, field: str) -> None:
    document = _doc()
    mutate(document)
    with pytest.raises(EnvelopeRejected) as caught:
        parse_canonical_envelope_v3_text(_text(document))
    assert (caught.value.kind, caught.value.field) == (kind, field)


def test_non_canonical_spelling_and_float_are_refused() -> None:
    text = VECTORS["envelopes"][0]["text"]
    with pytest.raises(EnvelopeRejected):
        parse_canonical_envelope_v3_text(json.dumps(json.loads(text), indent=1, sort_keys=True))
    with pytest.raises(EnvelopeRejected):
        parse_canonical_envelope_v3_text(text.replace('"version":2', '"version":2.0'))


def test_batch_vector_parses_and_its_digest_excludes_itself() -> None:
    vector = VECTORS["batch"]
    batch = parse_canonical_batch_v2_text(vector["text"])
    assert (batch.batch_id, batch.payload_sha256) == (vector["batch_id"], vector["payload_sha256"])
    body = json.loads(vector["text"])
    body.pop("payload_sha256")
    assert hashlib.sha256(_text(body).encode("utf-8")).hexdigest() == vector["payload_sha256"]
    assert batch.envelopes == tuple(e["text"] for e in VECTORS["envelopes"])


@pytest.mark.parametrize(
    ("mutate", "kind"),
    [
        (lambda d: d.__setitem__("payload_sha256", "0" * 64), "DIGEST_MISMATCH"),
        (lambda d: d.__setitem__("batch_id", "0" * 64), "INVALID_IDENTITY"),
        (lambda d: d.__setitem__("lab_run_id", "run-1"), "UNKNOWN_FIELD"),
        (lambda d: d.__setitem__("source_id", "src-2"), "NOT_HOMOGENEOUS"),
        (lambda d: d["mapping"].__setitem__("version", 3), "NOT_HOMOGENEOUS"),
        (lambda d: d.__setitem__("envelopes", list(reversed(d["envelopes"]))), "NOT_ORDERED"),
        (lambda d: d.__setitem__("envelopes", []), "EMPTY"),
        (lambda d: d["schema"].__setitem__("version", 1), "SCHEMA_UNSUPPORTED"),
    ],
)
def test_batch_refusals(mutate, kind: str) -> None:
    document = json.loads(VECTORS["batch"]["text"])
    mutate(document)
    with pytest.raises(BatchRejected) as caught:
        parse_canonical_batch_v2_text(_text(document))
    assert caught.value.kind == kind


def test_batch_bound_is_enforced() -> None:
    text = VECTORS["envelopes"][0]["text"]
    with pytest.raises(BatchRejected) as caught:
        seal_batch_v2(
            site_id="site-a",
            gateway_id="gw-1",
            source_id="src-1",
            source_mode="SIMULATED",
            foundation_version=3,
            foundation_valid_from="2026-09-29T11:57:49Z",
            binding_set_id="bs-kobo",
            binding_version=2,
            snapshot_sha256="b" * 64,
            envelope_texts=[text] * 257,
        )
    assert caught.value.kind == "TOO_LARGE"


def _observation(**changes) -> DeviceObservation:
    base = dict(
        device_id="pv-inverter",
        signal_id="ac_power",
        address="pv/ac",
        state_key="pv_power",
        reading_class="INTERVAL_SIGNAL",
        at_offset_minutes=15,
        source_sample_time="2026-10-01T08:15:00Z",
        outcome="REPORTED",
        reported_value=Fraction(2799, 800),
        canonical_unit="kW",
    )
    base.update(changes)
    return DeviceObservation(**base)


def test_adapter_publishes_only_public_fields() -> None:
    report = report_from_observation(_observation(), interval_minutes=15, report_key="k-1")
    assert report is not None
    assert (report.value, report.interval_start, report.measurement) == (
        "3.49875",
        "2026-10-01T08:00:00Z",
        "INTERVAL_MEAN",
    )
    assert "address" not in report.__dataclass_fields__ and "state_key" not in report.__dataclass_fields__


def test_adapter_drops_unpublished_and_keeps_unavailable_explicit() -> None:
    assert report_from_observation(
        _observation(outcome="DROPPED", reported_value=None, suppression_reason="DROPPED"), interval_minutes=15, report_key=None
    ) is None
    assert report_from_observation(
        _observation(outcome="SUPPRESSED_BY_GAP", reported_value=None, suppression_reason="GAP"),
        interval_minutes=15,
        report_key=None,
    ) is None
    unavailable = report_from_observation(
        _observation(outcome="NO_PRECEDING_INTERVAL", reported_value=None, suppression_reason="NO_PRECEDING_INTERVAL"), interval_minutes=15, report_key=None
    )
    assert unavailable is not None
    assert (unavailable.quality, unavailable.value, unavailable.unavailable_reason) == (
        "UNAVAILABLE",
        None,
        "NO_COMPLETED_INTERVAL",
    )


def test_report_wire_refuses_private_fields() -> None:
    from conftest import report

    document = json.loads(report())
    document["true_value"] = "60"
    with pytest.raises(EnvelopeRejected) as caught:
        parse_device_report_text(_text(document))
    assert (caught.value.kind, caught.value.field) == ("UNKNOWN_FIELD", "true_value")
