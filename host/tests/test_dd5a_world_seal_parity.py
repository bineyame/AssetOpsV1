"""DD5a unit 2 (D-DD.139): `seal_readings` parity against the gateway's own envelopes and seal, one row of each kind
(v3 mini, v4 cold measurement, v4 cold event, v4 EV connector energy with session). Here, not in backend/tests: only
the Lab host side may compose the gateway (dependency direction)."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "tests"))

from test_dd5a_world_seal import FOUNDATION_DIGEST, GATEWAY, SET, SHA, SITE, SOURCES, _context, _day, _five_minute_day, _only_envelope  # noqa: E402,E501

from assetops_backend.evidence.world_seal import seal_readings  # noqa: E402
from assetops_contracts import gateway_report  # noqa: E402
from assetops_contracts.gateway_report import DeviceReport, DeviceReportV2, cold_event_id  # noqa: E402
from assetops_gateway.service import GatewayService, _envelope_v4, _seal  # noqa: E402


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


def test_the_sealed_batch_is_the_gateway_seal_of_the_same_envelopes() -> None:
    (batch,) = seal_readings(_context(), [_day(_five_minute_day(date(2026, 10, 12))[:3])])
    provisioning, snapshot = _gateway_side()
    _, text = _seal(provisioning, snapshot, SOURCES["meter"], json.loads(batch.text)["envelopes"])
    assert batch.text == text
