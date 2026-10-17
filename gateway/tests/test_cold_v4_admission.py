"""W2-02: the gateway's DeviceReport v2 -> SourceEnvelope V4 branch (`D-2026-10-17-w2-02-buildspec`)."""

from __future__ import annotations

from dataclasses import replace

from assetops_contracts.gateway_report import (
    DeviceReportV2,
    cold_report_key,
    device_report_v2_text,
)
from assetops_contracts.source_envelope_v3 import (
    SourceEnvelopeV3,
    canonical_envelope_v3_text,
    v3_message_id,
)
from assetops_contracts.source_envelope_v4 import V4_CHANNEL_MAPPINGS, parse_canonical_envelope_v4_text
from assetops_gateway.service import GatewayReader, GatewayService

from conftest import EPOCH, GATEWAY, SITE, SRC_BMS, SRC_GEN, _rows, report, snapshot

SCENARIO = "b" * 64
AT = "2026-10-06T19:05:00Z"
RUN = "lab-run-cold-1"


def _cold_row(rev: str, device: str, signal: str, role: str, unit: str, *, metadata: bool = True) -> dict:
    row = {
        "binding_revision_id": rev, "device_id": device, "signal_id": signal, "source_id": SRC_GEN,
        "gateway_id": GATEWAY, "asset_id": None, "role": role, "source_unit": unit, "canonical_unit": unit,
        "conversion": {"kind": "IDENTITY", "parameters": {}},
    }
    if metadata:
        row.update(V4_CHANNEL_MAPPINGS[(device, signal)].metadata())
    return row


def _activate(gateway: GatewayService, *, door_metadata: bool = True) -> str:
    rows = _rows() + [
        _cold_row("b-4", "chamber-probe", "temperature", "chamber_temperature", "degC"),
        _cold_row("b-5", "door-sensor", "event", "door_event", "event", metadata=door_metadata),
    ]
    text, claimed = snapshot(rows=rows)
    gateway.activate(text, claimed)
    return claimed.snapshot_sha256


def _probe(value: str = "3.8", at: str = AT) -> DeviceReportV2:
    return DeviceReportV2(
        report_key=cold_report_key(scenario_sha256=SCENARIO, device_id="chamber-probe", signal_id="temperature",
                                   source_time=at, record_kind=None, event_id=None, interval_start=None),
        device_id="chamber-probe", signal_id="temperature", source_time=at, family="MEASUREMENT",
        measurement="STATE_AT_INSTANT", interval_start=None, interval_end=None, value=value, unit="degC",
        quality="GOOD", unavailable_reason=None, record_kind=None, event_id=None, correlation_id=None,
        component_id=None, actor=None, outcome=None, session_id=None, connector_id=None,
    )


def _door(kind: str = "DOOR_OPEN", outcome: str = "OPEN", ordinal: int = 1) -> DeviceReportV2:
    # The gateway branch is tested with a V4-valid identifier; the `cold:`-prefixed generator form is an open
    # question (the V4 identifier grammar has no ':'), see `.agent/W2-02-phase-3-handoff.md`.
    event_id = f"cold-door-event-{ordinal}"
    return DeviceReportV2(
        report_key=cold_report_key(scenario_sha256=SCENARIO, device_id="door-sensor", signal_id="event",
                                   source_time=AT, record_kind=kind, event_id=event_id, interval_start=None),
        device_id="door-sensor", signal_id="event", source_time=AT, family="EVENT", measurement=None,
        interval_start=None, interval_end=None, value=None, unit=None, quality="GOOD", unavailable_reason=None,
        record_kind=kind, event_id=event_id, correlation_id="cold-door-1", component_id="room-1", actor="SENSOR",
        outcome=outcome, session_id=None, connector_id=None,
    )


def _stage(db_path) -> list:
    with GatewayReader(db_path) as reader:
        return list(reader.run_stage(RUN).envelopes)


def test_gateway_allocates_v4_sequence(gateway: GatewayService, db_path) -> None:
    sha = _activate(gateway)
    first = gateway.admit(device_report_v2_text(_door()), snapshot_sha256=sha, lab_run_ref=RUN)
    second = gateway.admit(device_report_v2_text(_probe()), snapshot_sha256=sha, lab_run_ref=RUN)
    # A v1 report on the same source shares the one (gateway, source, epoch) sequence.
    third = gateway.admit(report(device="generator-controller", signal="status", value="RUNNING", unit="state",
                                 at=AT), snapshot_sha256=sha, lab_run_ref=RUN)
    assert [a.outcome for a in (first, second, third)] == ["ADMITTED"] * 3
    assert [a.sequence for a in (first, second, third)] == [1, 2, 3]
    for admission in (first, second, third):
        assert admission.message_id == v3_message_id(site_id=SITE, gateway_id=GATEWAY, source_id=SRC_GEN,
                                                     sequence_epoch=EPOCH, sequence=admission.sequence)
    envelopes = {e.sequence: e for e in _stage(db_path)}
    door = parse_canonical_envelope_v4_text(envelopes[1].envelope_text)
    assert (door.family, door.record_kind, door.outcome, door.event_id, door.correlation_id) == (
        "EVENT", "DOOR_OPEN", "OPEN", _door().event_id, "cold-door-1")
    assert (door.message_id, door.sequence, door.source_id, door.published_at) == (
        first.message_id, 1, SRC_GEN, "2026-10-08T12:00:00Z")
    probe = parse_canonical_envelope_v4_text(envelopes[2].envelope_text)
    assert (probe.family, probe.measurement, probe.value, probe.unit) == ("MEASUREMENT", "STATE_AT_INSTANT",
                                                                           "3.8", "degC")
    assert '"version":3' in envelopes[3].envelope_text
    # The mixed V3/V4 group seals through the Batch V2 header path, as one batch.
    batches = gateway.seal()
    assert len(batches) == 1
    assert {e.batch_id for e in _stage(db_path)} == set(batches)


def test_replay_same_report_key(gateway: GatewayService, db_path) -> None:
    sha = _activate(gateway)
    text = device_report_v2_text(_door())
    first = gateway.admit(text, snapshot_sha256=sha, lab_run_ref=RUN)
    again = gateway.admit(text, snapshot_sha256=sha, lab_run_ref=RUN)
    assert (again.outcome, again.message_id, again.sequence) == ("ALREADY_ADMITTED", first.message_id, 1)
    following = gateway.admit(device_report_v2_text(_probe()), snapshot_sha256=sha, lab_run_ref=RUN)
    assert following.sequence == 2  # the replay allocated nothing
    assert len(_stage(db_path)) == 2


def test_conflicting_report_key_held(gateway: GatewayService, db_path) -> None:
    sha = _activate(gateway)
    original = _probe()
    gateway.admit(device_report_v2_text(original), snapshot_sha256=sha, lab_run_ref=RUN)
    conflict = gateway.admit(device_report_v2_text(replace(original, value="3.9")), snapshot_sha256=sha,
                             lab_run_ref=RUN)
    assert (conflict.outcome, conflict.kind, conflict.field) == ("HELD", "CONFLICTING_REPORT", "report_key")
    # V4 parser refusals are held before any sequence is allocated.
    bad_outcome = gateway.admit(device_report_v2_text(_door(outcome="CLOSED", ordinal=2)), snapshot_sha256=sha,
                                lab_run_ref=RUN)
    assert (bad_outcome.outcome, bad_outcome.kind, bad_outcome.field) == ("HELD", "INVALID_PAYLOAD",
                                                                          "payload.outcome")
    wrong_kind = gateway.admit(device_report_v2_text(_door(kind="START_REQUEST", outcome="REQUESTED", ordinal=3)),
                               snapshot_sha256=sha, lab_run_ref=RUN)
    assert (wrong_kind.outcome, wrong_kind.kind) == ("HELD", "RECORD_KIND_UNSUPPORTED")
    no_correlation = gateway.admit(device_report_v2_text(replace(_door(ordinal=4), correlation_id=None)),
                                   snapshot_sha256=sha, lab_run_ref=RUN)
    assert (no_correlation.outcome, no_correlation.kind) == ("HELD", "CORRELATION_INVALID")
    next_one = gateway.admit(device_report_v2_text(_door()), snapshot_sha256=sha, lab_run_ref=RUN)
    assert (next_one.outcome, next_one.sequence) == ("ADMITTED", 2)


def test_conflicting_v4_mapping_metadata_held(gateway: GatewayService) -> None:
    sha = _activate(gateway, door_metadata=False)
    held = gateway.admit(device_report_v2_text(_door()), snapshot_sha256=sha, lab_run_ref=RUN)
    assert (held.outcome, held.kind, held.field) == ("HELD", "MAPPING_INCOMPATIBLE", "mapping")
    # A v1 report on an unchanged v3 row still admits.
    v1 = gateway.admit(report(), snapshot_sha256=sha, lab_run_ref=RUN)
    assert v1.outcome == "ADMITTED"


def test_v3_branch_unchanged(gateway: GatewayService, db_path) -> None:
    sha = _activate(gateway)
    admitted = gateway.admit(report(at=AT), snapshot_sha256=sha, lab_run_ref=RUN)
    expected = canonical_envelope_v3_text(SourceEnvelopeV3(
        message_id=v3_message_id(site_id=SITE, gateway_id=GATEWAY, source_id=SRC_BMS, sequence_epoch=EPOCH,
                                 sequence=1),
        sequence_epoch=EPOCH, sequence=1, site_id=SITE, gateway_id=GATEWAY, source_id=SRC_BMS,
        device_id="battery-bms", signal_id="soc", binding_set_id="bs-kobo", binding_version=2, source_time=AT,
        published_at="2026-10-08T12:00:00Z", interval_start=None, interval_end=None, family="MEASUREMENT",
        measurement="STATE_AT_INSTANT", value="61.5", unit="%", quality="GOOD", unavailable_reason=None,
    ))
    (envelope,) = _stage(db_path)
    assert (admitted.outcome, envelope.envelope_text) == ("ADMITTED", expected)
