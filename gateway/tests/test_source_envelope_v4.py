"""W2-00: SourceEnvelope V4 vectors, refusals, event identity, Batch V2 header path and snapshot v4 keys."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from assetops_contracts.ingestion_batch_v2 import BatchRejected, parse_canonical_batch_v2_text, seal_batch_v2
from assetops_contracts.source_envelope import EnvelopeRejected, canonical_json  # shared base type
from assetops_contracts.source_envelope_v3 import SourceEnvelopeV3, text_sha256, v3_message_id
from assetops_contracts.source_envelope_v4 import (
    V4_CHANNEL_MAPPINGS,
    SourceEnvelopeV4,
    canonical_binding_metadata,
    event_identity_sha256,
    header_message_id,
    parse_canonical_envelope_v4_text,
    parse_canonical_source_envelope_text,
    uses_v4_header_path,
)

ROOT = Path(__file__).resolve().parents[2]
V4 = json.loads((ROOT / "contract-fixtures" / "source-envelope-v4-vectors.json").read_text(encoding="utf-8"))
V3 = json.loads((ROOT / "contract-fixtures" / "source-envelope-v3-vectors.json").read_text(encoding="utf-8"))


def vector(name: str) -> dict:
    return copy.deepcopy(next(v["document"] for v in V4["vectors"] if v["name"] == name))


def text(doc: dict) -> str:
    return canonical_json(doc)


def renumber(doc: dict, seq: int) -> dict:
    doc["message"]["sequence"] = seq
    s = doc["source"]
    doc["message"]["message_id"] = v3_message_id(site_id=s["site_id"], gateway_id=s["gateway_id"],
                                                 source_id=s["source_id"], sequence_epoch=doc["message"]["sequence_epoch"],
                                                 sequence=seq)
    return doc


def refused(doc_or_text, kind: str, field: str) -> None:
    body = doc_or_text if isinstance(doc_or_text, str) else text(doc_or_text)
    with pytest.raises(EnvelopeRejected) as caught:
        parse_canonical_source_envelope_text(body)
    assert (caught.value.kind, caught.value.field) == (kind, field), caught.value


# --- golden vectors ------------------------------------------------------------


@pytest.mark.parametrize("v", V4["vectors"], ids=lambda v: v["name"])
def test_v4_vectors_round_trip_canonically(v) -> None:
    assert text(v["document"]) == v["canonical_text"]
    envelope = parse_canonical_source_envelope_text(v["canonical_text"])
    assert isinstance(envelope, SourceEnvelopeV4)
    assert text_sha256(v["canonical_text"]) == v["envelope_sha256"]
    assert event_identity_sha256(v["canonical_text"]) == v["event_identity_sha256"]
    # explicit nulls: every key of the family's set is present
    payload = json.loads(v["canonical_text"])["payload"]
    assert "session_id" in payload and "connector_id" in payload


def test_v3_vectors_still_dispatch_to_the_frozen_v3_parser() -> None:
    for v in V3["envelopes"]:
        assert isinstance(parse_canonical_source_envelope_text(v["text"]), SourceEnvelopeV3)
        assert not uses_v4_header_path(v["text"])


def test_v4_text_is_refused_by_the_v4_only_parser_when_noncanonical() -> None:
    body = json.dumps(vector("cold event"), indent=1)
    with pytest.raises(EnvelopeRejected) as caught:
        parse_canonical_envelope_v4_text(body)
    assert caught.value.kind in {"NOT_CANONICAL", "MALFORMED_TEXT"}


# --- refusals ----------------------------------------------------------------------


def _v3_with(payload_patch: dict) -> dict:
    doc = vector("numeric point")
    doc["schema"]["version"] = 3
    doc["payload"] = {k: doc["payload"][k] for k in ("family", "measurement", "value", "unit", "quality",
                                                     "unavailable_reason")}
    doc["payload"].update(payload_patch)
    return doc


def test_v4_only_kinds_under_v3_are_schema_unsupported() -> None:
    event_v3 = vector("cold event")
    event_v3["schema"]["version"] = 3
    refused(event_v3, "SCHEMA_UNSUPPORTED", "payload.family")
    refused(_v3_with({"measurement": "INTERVAL_DELTA"}), "SCHEMA_UNSUPPORTED", "payload.measurement")


def _mut(name: str, path: str, value, drop: bool = False) -> dict:
    doc = vector(name)
    where, key = path.split(".")
    if drop:
        del doc[where][key]
    else:
        doc[where][key] = value
    return doc


REFUSALS = [
    # identifiers / correlation
    ("cold event", "payload.event_id", None, False, "CORRELATION_INVALID", "payload.event_id"),
    ("cold event", "payload.event_id", None, True, "CORRELATION_INVALID", "payload.event_id"),
    ("cold event", "payload.correlation_id", "bad id!", False, "CORRELATION_INVALID", "payload.correlation_id"),
    ("ev session start", "payload.session_id", None, False, "CORRELATION_INVALID", "payload.session_id"),
    ("ev session start", "payload.session_id", None, True, "CORRELATION_INVALID", "payload.session_id"),
    ("ev session start", "payload.connector_id", None, False, "CORRELATION_INVALID", "payload.connector_id"),
    ("ev session start", "payload.correlation_id", "other", False, "CORRELATION_INVALID", "payload.correlation_id"),
    ("ev connector fault", "payload.connector_id", None, True, "CORRELATION_INVALID", "payload.connector_id"),
    ("cold event", "payload.session_id", "sess-1", False, "CORRELATION_INVALID", "payload.session_id"),
    ("numeric point", "payload.connector_id", "connector-1", False, "CORRELATION_INVALID", "payload.connector_id"),
    ("ev interval delta", "payload.session_id", None, False, "CORRELATION_INVALID", "payload.session_id"),
    # W2-05a Run 8 M3: a connector mean (power, requested power, allocated limit) claims neither a session nor a connector.
    ("numeric point", "payload.session_id", "sess-1", False, "CORRELATION_INVALID", "payload.session_id"),
    # delta
    ("ev interval delta", "payload.unit", "Wh", False, "EV_DELTA_UNIT_INVALID", "payload.unit"),
    ("ev interval delta", "timing.interval_start", None, False, "EV_DELTA_INTERVAL_INVALID", "timing.interval_start"),
    ("ev interval delta", "timing.interval_start", "2026-10-06T19:05:00Z", False, "EV_DELTA_INTERVAL_INVALID",
     "timing.interval_start"),
    ("ev interval delta", "timing.interval_end", "2026-10-06T19:04:00Z", False, "EV_DELTA_INTERVAL_INVALID",
     "timing.interval_end"),
    ("ev interval delta", "payload.value", "-0.5", False, "EV_DELTA_VALUE_INVALID", "payload.value"),
    ("ev interval delta", "payload.value", None, False, "EV_DELTA_VALUE_INVALID", "payload.value"),
    # kind / outcome / unit / time / private field
    ("cold event", "payload.record_kind", "COMPRESSOR_TRIP", False, "RECORD_KIND_UNSUPPORTED", "payload.record_kind"),
    ("cold event", "payload.outcome", "OPEN", False, "INVALID_PAYLOAD", "payload.outcome"),
    ("cold event", "payload.actor", "ROBOT", False, "INVALID_PAYLOAD", "payload.actor"),
    ("cold event", "payload.quality", "UNAVAILABLE", False, "INVALID_PAYLOAD", "payload.quality"),
    ("cold event", "payload.value", "1", False, "INVALID_PAYLOAD", "payload.value"),
    ("cold event", "payload.component_id", None, False, "WRONG_TYPE", "payload.component_id"),
    ("manual log", "payload.unit", "degF", False, "UNIT_INCOMPATIBLE", "payload.unit"),
    ("manual log", "payload.value", "4.10", False, "NOT_CANONICAL", "payload.value"),
    ("numeric point", "payload.unit", "deg C", False, "INVALID_PAYLOAD", "payload.unit"),
    ("numeric point", "payload.measurement", "PEAK", False, "INVALID_PAYLOAD", "payload.measurement"),
    ("cold event", "timing.source_time", "2026-10-06 19:05:00", False, "INVALID_TIMING", "timing.source_time"),
    ("cold event", "timing.published_at", "2026-10-06T19:04:00Z", False, "INVALID_TIMING", "timing.published_at"),
    ("cold event", "timing.interval_start", "2026-10-06T19:00:00Z", False, "INVALID_TIMING", "timing.interval_start"),
    ("cold event", "payload.true_temperature", "5", False, "UNKNOWN_FIELD", "payload.true_temperature"),
    ("cold event", "payload.cause", "GENERATOR_FAILURE", False, "UNKNOWN_FIELD", "payload.cause"),
    ("numeric point", "payload.event_id", "evt-1", False, "UNKNOWN_FIELD", "payload.event_id"),
    ("cold event", "payload.quality", None, True, "MISSING_FIELD", "payload.quality"),
    ("cold event", "payload.family", "POLICY", False, "SCHEMA_UNSUPPORTED", "payload.family"),
]


@pytest.mark.parametrize("name,path,value,drop,kind,field", REFUSALS, ids=lambda x: str(x))
def test_v4_refusals_name_their_exact_code_and_field(name, path, value, drop, kind, field) -> None:
    refused(_mut(name, path, value, drop), kind, field)


def test_site_power_events_may_omit_their_component() -> None:
    assert parse_canonical_source_envelope_text(text(vector("site power event"))).component_id is None


# --- event identity ------------------------------------------------------------------


def test_event_identity_excludes_transport_and_covers_source_time_outcome_and_payload() -> None:
    base = vector("cold event")
    original = event_identity_sha256(text(base))
    transported = renumber(vector("cold event"), 99)
    transported["timing"]["published_at"] = "2026-10-06T19:06:00Z"
    transported["mapping"]["version"] = 7
    assert text(transported) != text(base)
    assert event_identity_sha256(text(transported)) == original
    for path, value in (("timing.source_time", "2026-10-06T19:04:00Z"), ("payload.outcome", "SUCCEEDED"),
                        ("payload.correlation_id", "attempt-2"), ("payload.quality", "SUSPECT")):
        assert event_identity_sha256(text(_mut("cold event", path, value))) != original, path


# --- Batch V2 header path -------------------------------------------------------------


def _seal(texts):
    return seal_batch_v2(site_id="site-a", gateway_id="gw-1", source_id="src-1", source_mode="SIMULATED",
                         foundation_version=1, foundation_valid_from="2026-10-01T00:00:00Z", binding_set_id="set-1",
                         binding_version=1, snapshot_sha256="0" * 64, envelope_texts=texts)


def test_a_valid_header_v4_batch_with_malformed_payloads_seals_and_reparses() -> None:
    good = vector("cold event")
    bad_payload = _mut("manual log", "payload.unit", "degF")
    bad_timing = renumber(_mut("ev session start", "timing.source_time", "not-a-time"), 20)
    noncanonical = json.dumps(renumber(vector("numeric point"), 30), indent=1)
    v3_kind = renumber(vector("cold event"), 40)
    v3_kind["schema"]["version"] = 3
    batch, body = _seal([text(good), text(bad_payload), text(bad_timing), noncanonical, text(v3_kind)])
    assert parse_canonical_batch_v2_text(body) == batch
    assert header_message_id(noncanonical) == renumber(vector("numeric point"), 30)["message"]["message_id"]


@pytest.mark.parametrize("mutate,field", [
    (lambda d: d["message"].update(message_id="0" * 64), "envelopes.message.message_id"),
    (lambda d: d["source"].pop("source_id"), "envelopes.source.source_id"),
    (lambda d: d["mapping"].update(version="1"), "envelopes.mapping.version"),
    (lambda d: d.pop("message"), "envelopes.message"),
])
def test_a_malformed_identity_or_scope_header_is_whole_batch_invalid_envelope(mutate, field) -> None:
    doc = vector("cold event")
    mutate(doc)
    with pytest.raises(BatchRejected) as caught:
        _seal([text(doc)])
    assert (caught.value.kind, caught.value.field) == ("INVALID_ENVELOPE", field)


def test_header_path_keeps_homogeneity_and_order() -> None:
    other_source = vector("cold event")
    other_source["source"]["source_id"] = "src-2"
    other_source = renumber(other_source, 6)
    with pytest.raises(BatchRejected) as caught:
        _seal([text(other_source)])
    assert caught.value.kind == "NOT_HOMOGENEOUS"
    with pytest.raises(BatchRejected) as caught:
        _seal([text(vector("manual log")), text(vector("cold event"))])
    assert caught.value.kind == "NOT_ORDERED"


# --- closed channel table and snapshot v4 keys ------------------------------------------


def test_closed_channel_table_holds_the_section_4_tuples_and_two_reserved_ev_tuples() -> None:
    # W2-05a adds the exact simulator-lab-gateway-ev/1 tuples (Q1); the cold twelve plus the two reserved stay.
    from assetops_contracts.source_envelope_v4 import V4_COLD_CHANNEL_MAPPINGS, V4_EV_CHANNEL_MAPPINGS

    assert len(V4_COLD_CHANNEL_MAPPINGS) == 12 and len(V4_EV_CHANNEL_MAPPINGS) == 15
    assert len(V4_CHANNEL_MAPPINGS) == 14 + 15
    assert V4_CHANNEL_MAPPINGS[("charger-controller", "session-event")].requires_session is True
    assert V4_CHANNEL_MAPPINGS[("connector-controller", "fault-event")].requires_session is False
    assert V4_CHANNEL_MAPPINGS[("operator-log", "temperature-event")].allowed_units == ("degC",)
    assert ("chamber-probe", "state") not in V4_CHANNEL_MAPPINGS  # no implicit alias across devices or signals
    for entry in V4_CHANNEL_MAPPINGS.values():
        assert canonical_binding_metadata(entry.metadata()) == entry.metadata()


def test_v3_binding_rows_have_no_v4_metadata() -> None:
    assert canonical_binding_metadata({"device_id": "pv", "signal_id": "p"}) is None


# --- gateway snapshot: optional v4 binding keys (ruling 4) ------------------------------------


def _v4_row(**extra) -> dict:
    from conftest import _rows

    row = dict(_rows()[0])
    row.update(V4_CHANNEL_MAPPINGS[("door-sensor", "event")].metadata(), **extra)
    return row


def test_gateway_snapshot_admits_v3_rows_and_v4_rows_with_all_five_keys() -> None:
    from conftest import PROVISIONING, _rows, snapshot

    from assetops_gateway.snapshot import verify_snapshot

    text3, claimed3 = snapshot()
    verify_snapshot(text3, claimed3, PROVISIONING)  # no v4 key anywhere
    text4, claimed4 = snapshot(rows=[_v4_row(), *_rows()[1:]])
    verify_snapshot(text4, claimed4, PROVISIONING)


@pytest.mark.parametrize("change,field", [
    ({"drop": "requires_session"}, "requires_session"),
    ({"requires_correlation": "yes"}, "requires_correlation"),
    ({"allowed_units": "degC"}, "allowed_units"),
    ({"allowed_outcomes": {"DOOR_OPEN": "OPEN"}}, "allowed_outcomes"),
    ({"private_cause": "x"}, "private_cause"),
])
def test_gateway_snapshot_refuses_partial_ill_typed_or_unknown_v4_keys(change, field) -> None:
    from conftest import PROVISIONING, _rows, snapshot

    from assetops_gateway.snapshot import SnapshotRefused, verify_snapshot

    row = _v4_row()
    if "drop" in change:
        del row[change["drop"]]
    else:
        row.update(change)
    text4, claimed4 = snapshot(rows=[row, *_rows()[1:]])
    with pytest.raises(SnapshotRefused) as caught:
        verify_snapshot(text4, claimed4, PROVISIONING)
    assert caught.value.kind == "MALFORMED_SNAPSHOT" and caught.value.field.endswith(field)


def test_v4_connector_mean_accepts_explicit_null_correlation() -> None:
    """W2-05a Run 8 M3: connector power / requested power / allocated limit are INTERVAL_MEAN, and connector state
    a point measurement, with explicit null session and connector IDs (the effective source binding supplies the
    connector); only connector energy carries them."""
    for name in ("interval mean", "state point"):
        doc = vector(name)
        assert doc["payload"]["session_id"] is None and doc["payload"]["connector_id"] is None
        assert isinstance(parse_canonical_source_envelope_text(text(doc)), SourceEnvelopeV4)
        for key in ("session_id", "connector_id"):
            refused(_mut_from(doc, f"payload.{key}", "x-1"), "CORRELATION_INVALID", f"payload.{key}")


def _mut_from(doc: dict, path: str, value) -> dict:
    out = copy.deepcopy(doc)
    where, key = path.split(".")
    out[where][key] = value
    return out
