"""DD5a unit 2 (D-DD.139, D-DD.91): `evidence/world_seal.seal_readings` mirrors the gateway's envelopes and Batch V2
sealing, splits a source-day at 256 envelopes and runs one sequence per source over the span. Pure; no database."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from assetops_backend.evidence import world_seal
from assetops_backend.evidence.world_seal import SealContext, seal_readings
from assetops_contracts import gateway_report
from assetops_contracts.gateway_report import DeviceReport, DeviceReportV2, cold_event_id
from assetops_contracts.ingestion_batch_v2 import MAX_BATCH_ENVELOPES, parse_canonical_batch_v2_text
from assetops_gateway.service import GatewayService, _envelope_v4, _seal

SITE = "11111111-1111-4111-8111-111111111111"
GATEWAY = "22222222-2222-4222-8222-222222222222"
SET = "33333333-3333-4333-8333-333333333333"
SHA = "a" * 64
FOUNDATION_DIGEST = "b" * 64
SOURCES = {"meter": "44444444-4444-4444-8444-444444444444", "door": "55555555-5555-4555-8555-555555555555",
           "ev": "66666666-6666-4666-8666-666666666666"}
CHANNELS = {
    ("generator-meter", "output-power"): ("meter", "generator_power"),
    ("chamber-probe", "temperature"): ("meter", "chamber_temperature"),
    ("door-sensor", "event"): ("door", "door_event"),
    ("ch-k1-c1-connector-meter", "energy"): ("ev", "ev_connector_energy"),
}


def _context(**change) -> SealContext:
    bindings = {k: {"device_id": k[0], "signal_id": k[1], "source_id": SOURCES[s], "gateway_id": GATEWAY, "role": r}
                for k, (s, r) in CHANNELS.items()}
    base = dict(site_code="COLD-X", site_id=SITE, gateway_id=GATEWAY, source_mode="SIMULATED", foundation_version=1,
                foundation_valid_from="2026-06-30T21:00:00Z", binding_set_id=SET, binding_version=1,
                snapshot_sha256=SHA, foundation_digest=FOUNDATION_DIGEST, v4=True, bindings=bindings)
    return SealContext(**{**base, **change})


def _only_envelope(batches) -> str:
    (batch,) = batches
    (text,) = json.loads(batch.text)["envelopes"]
    return text


def _gateway_side():
    provisioning = SimpleNamespace(site_id=SITE, gateway_id=GATEWAY, source_mode="SIMULATED")
    snapshot = SimpleNamespace(binding_set_id=SET, binding_set_version=1, foundation_version=1,
                               foundation_valid_from="2026-06-30T21:00:00Z", snapshot_sha256=SHA)
    return provisioning, snapshot


def _v2(device, signal, **kw) -> DeviceReportV2:
    base = dict(report_key=None, device_id=device, signal_id=signal, source_time=None, family="MEASUREMENT",
                measurement=None, interval_start=None, interval_end=None, value=None, unit=None, quality="GOOD",
                unavailable_reason=None, record_kind=None, event_id=None, correlation_id=None, component_id=None,
                actor=None, outcome=None, session_id=None, connector_id=None)
    return DeviceReportV2(**{**base, **kw})


def _gateway_v4(report: DeviceReportV2, source: str) -> str:
    from assetops_contracts.source_envelope_v4 import canonical_envelope_v4_text

    provisioning, snapshot = _gateway_side()
    envelope = _envelope_v4(report, provisioning, snapshot, SimpleNamespace(source_id=SOURCES[source]), "1", 1,
                            report.source_time)
    return canonical_envelope_v4_text(envelope)


def _day(rows, day=date(2026, 10, 12)):
    return (day, rows)


def test_v3_mini_grid_row_matches_the_gateway() -> None:
    row = {"source_id": "generator-meter", "signal_id": "output-power", "start": "2026-10-12T09:25:00+03:00",
           "end": "2026-10-12T09:30:00+03:00", "value": "12.5", "unit": "kW"}
    ours = _only_envelope(seal_readings(_context(v4=False), [_day([row])]))
    provisioning, snapshot = _gateway_side()
    report = DeviceReport(report_key=None, device_id="generator-meter", signal_id="output-power",
                          source_time="2026-10-12T06:30:00Z", measurement="INTERVAL_MEAN",
                          interval_start="2026-10-12T06:25:00Z", value="12.5", unit="kW", quality="GOOD",
                          unavailable_reason=None)
    from assetops_contracts.source_envelope_v3 import v3_message_id

    message_id = v3_message_id(site_id=SITE, gateway_id=GATEWAY, source_id=SOURCES["meter"], sequence_epoch="1",
                               sequence=1)
    theirs = GatewayService._envelope_v3_text(report, provisioning, snapshot, SimpleNamespace(source_id=SOURCES["meter"]),
                                              "1", 1, message_id, "2026-10-12T06:30:00Z")
    assert ours == theirs


def test_v4_cold_measurement_matches_the_gateway() -> None:
    row = {"source_id": "chamber-probe", "signal_id": "temperature", "start": "2026-10-12T09:30:00+03:00",
           "end": "2026-10-12T09:30:00+03:00", "value": "4.2", "unit": "degC"}
    ours = _only_envelope(seal_readings(_context(), [_day([row])]))
    theirs = _gateway_v4(_v2("chamber-probe", "temperature", source_time="2026-10-12T06:30:00Z",
                             measurement="STATE_AT_INSTANT", value="4.2", unit="degC"), "meter")
    assert ours == theirs


def test_v4_cold_event_matches_the_gateway_with_the_d_dd_91_ids() -> None:
    row = {"source_id": "door-sensor", "signal_id": "event", "start": "2026-10-12T09:31:00+03:00",
           "end": "2026-10-12T09:31:00+03:00", "value": None, "unit": "event",
           "event": {"record_kind": "DOOR_OPEN", "outcome": "OPEN", "actor": "SENSOR", "component_id": "chamber",
                     "ordinal": 7, "correlation": ["door", 4]}}
    ours = _only_envelope(seal_readings(_context(), [_day([row])]))
    theirs = _gateway_v4(_v2(
        "door-sensor", "event", source_time="2026-10-12T06:31:00Z", family="EVENT", record_kind="DOOR_OPEN",
        outcome="OPEN", actor="SENSOR", component_id="chamber",
        event_id=cold_event_id(scenario_sha256=FOUNDATION_DIGEST, device_id="door-sensor", signal_id="event",
                               transition_ordinal=7),
        correlation_id=gateway_report.cold_correlation_id(scenario_sha256=FOUNDATION_DIGEST,
                                                          correlation_key=("door", 4))), "door")
    assert ours == theirs


def test_v4_ev_connector_energy_with_session_matches_the_gateway() -> None:
    row = {"source_id": "ch-k1-c1-connector-meter", "signal_id": "energy", "start": "2026-10-12T09:25:00+03:00",
           "end": "2026-10-12T09:30:00+03:00", "value": "1.25", "unit": "kWh",
           "session": {"ordinal": 3, "connector_id": "ch-k1-c1"}}
    ours = _only_envelope(seal_readings(_context(), [_day([row])]))
    session = gateway_report.ev_session_id(foundation_digest=FOUNDATION_DIGEST, connector_id="ch-k1-c1",
                                           session_ordinal=3)
    theirs = _gateway_v4(_v2("ch-k1-c1-connector-meter", "energy", source_time="2026-10-12T06:30:00Z",
                             measurement="INTERVAL_DELTA", interval_start="2026-10-12T06:25:00Z",
                             interval_end="2026-10-12T06:30:00Z", value="1.25", unit="kWh", session_id=session,
                             connector_id="ch-k1-c1"), "ev")
    assert ours == theirs and session.startswith("ev-")


def _five_minute_day(day: date) -> list[dict]:
    midnight = datetime(day.year, day.month, day.day, tzinfo=timezone(timedelta(hours=3)))
    return [{"source_id": "chamber-probe", "signal_id": "temperature",
             "start": (midnight + timedelta(minutes=5 * i)).isoformat(),
             "end": (midnight + timedelta(minutes=5 * i)).isoformat(), "value": "4.000", "unit": "degC"}
            for i in range(288)]


def test_a_288_row_source_day_gives_two_batches_and_sequences_run_across_days() -> None:
    days = [date(2026, 10, 12), date(2026, 10, 13)]
    batches = seal_readings(_context(), [(d, _five_minute_day(d)) for d in days])
    assert [b.name for b in batches] == [
        f"COLD-X.{SOURCES['meter']}.2026-10-12.1.batch.json", f"COLD-X.{SOURCES['meter']}.2026-10-12.2.batch.json",
        f"COLD-X.{SOURCES['meter']}.2026-10-13.1.batch.json", f"COLD-X.{SOURCES['meter']}.2026-10-13.2.batch.json"]
    assert [b.count for b in batches] == [MAX_BATCH_ENVELOPES, 32, MAX_BATCH_ENVELOPES, 32]
    sequences = [json.loads(t)["message"]["sequence"] for b in batches for t in json.loads(b.text)["envelopes"]]
    assert sequences == list(range(1, 577))
    ids = [json.loads(t)["message"]["message_id"] for b in batches for t in json.loads(b.text)["envelopes"]]
    assert len(set(ids)) == len(ids)
    for b in batches:
        assert len(parse_canonical_batch_v2_text(b.text).envelopes) == b.count


def test_the_sealed_batch_is_the_gateway_seal_of_the_same_envelopes() -> None:
    (batch,) = seal_readings(_context(), [_day(_five_minute_day(date(2026, 10, 12))[:3])])
    provisioning, snapshot = _gateway_side()
    _, text = _seal(provisioning, snapshot, SOURCES["meter"], json.loads(batch.text)["envelopes"])
    assert batch.text == text


def test_an_unbound_channel_refuses() -> None:
    row = {"source_id": "ghost", "signal_id": "x", "start": "2026-10-12T09:30:00+03:00",
           "end": "2026-10-12T09:30:00+03:00", "value": "1", "unit": "kW"}
    with pytest.raises(world_seal.WorldSealRefused) as raised:
        seal_readings(_context(), [_day([row])])
    assert raised.value.code == "WORLD_TELEMETRY_UNRESOLVED"


def test_a_millesimal_reading_seals_in_canonical_spelling() -> None:
    assert [world_seal._value(v) for v in ("4.000", "12.500", "0.000", "-1.250", "100", "ON", None)] == [
        "4", "12.5", "0", "-1.25", "100", "ON", None]
