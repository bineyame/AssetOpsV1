"""W2-02: DeviceReport v2 (`D-2026-10-17-w2-02-buildspec`, "DeviceReport v2 and gateway path")."""

from __future__ import annotations

import json

import pytest

from assetops_contracts.gateway_report import (
    DeviceReport,
    DeviceReportV2,
    cold_event_id,
    cold_report_key,
    device_report_schema_version,
    device_report_text,
    device_report_v2_text,
    parse_device_report_text,
    parse_device_report_v2_text,
)
from assetops_contracts.source_envelope import EnvelopeRejected

SCENARIO = "a" * 64
_NULLS = dict(measurement=None, interval_start=None, interval_end=None, value=None, unit=None,
              unavailable_reason=None, record_kind=None, event_id=None, correlation_id=None, component_id=None,
              actor=None, outcome=None, session_id=None, connector_id=None)


def _report(**fields) -> DeviceReportV2:
    base = dict(report_key=None, device_id="chamber-probe", signal_id="temperature",
                source_time="2026-10-06T19:05:00Z", family="MEASUREMENT", quality="GOOD", **_NULLS)
    base.update(fields)
    return DeviceReportV2(**base)


def test_measurement_event_unavailable_roundtrip() -> None:
    measurement = _report(measurement="STATE_AT_INSTANT", value="3.8", unit="degC")
    mean = _report(device_id="compressor-meter", signal_id="power", measurement="INTERVAL_MEAN",
                   interval_start="2026-10-06T19:00:00Z", interval_end="2026-10-06T19:05:00Z", value="3", unit="kW")
    event_id = cold_event_id(scenario_sha256=SCENARIO, device_id="door-sensor", signal_id="event",
                             transition_ordinal=1)
    event = _report(device_id="door-sensor", signal_id="event", family="EVENT", record_kind="DOOR_OPEN",
                    event_id=event_id, correlation_id="cold-door-1", component_id="room-1", actor="SENSOR",
                    outcome="OPEN",
                    report_key=cold_report_key(scenario_sha256=SCENARIO, device_id="door-sensor", signal_id="event",
                                               source_time="2026-10-06T19:05:00Z", record_kind="DOOR_OPEN",
                                               event_id=event_id, interval_start=None))
    unavailable = _report(measurement="STATE_AT_INSTANT", quality="UNAVAILABLE", unit="degC",
                          unavailable_reason="SENSOR_FAILURE")
    for report in (measurement, mean, event, unavailable):
        text = device_report_v2_text(report)
        document = json.loads(text)
        assert set(document) == {
            "schema", "report_key", "device_id", "signal_id", "source_time", "family", "measurement",
            "interval_start", "interval_end", "value", "unit", "quality", "unavailable_reason", "record_kind",
            "event_id", "correlation_id", "component_id", "actor", "outcome", "session_id", "connector_id"}
        assert document["schema"] == {"id": "assetops.simulated-device-report", "version": 2}
        assert parse_device_report_v2_text(text) == report
        assert device_report_schema_version(text) == 2
    assert event.event_id.startswith("cold-") and len(event.event_id) == 69
    # Deterministic for retransmission; a different ordinal is a different event.
    assert event_id == cold_event_id(scenario_sha256=SCENARIO, device_id="door-sensor", signal_id="event",
                                     transition_ordinal=1)
    assert event_id != cold_event_id(scenario_sha256=SCENARIO, device_id="door-sensor", signal_id="event",
                                     transition_ordinal=2)
    # A v2 text is not a v1 report, and every key is required.
    with pytest.raises(EnvelopeRejected) as v1:
        parse_device_report_text(device_report_v2_text(measurement))
    assert v1.value.kind == "UNKNOWN_FIELD"
    missing = json.loads(device_report_v2_text(measurement))
    del missing["connector_id"]
    with pytest.raises(EnvelopeRejected) as absent:
        parse_device_report_v2_text(json.dumps(missing, sort_keys=True, separators=(",", ":")))
    assert (absent.value.kind, absent.value.field) == ("MISSING_FIELD", "connector_id")


def test_v1_bytes_unchanged() -> None:
    report = DeviceReport(report_key="k-1", device_id="tank-1-level", signal_id="level",
                          source_time="2026-10-06T19:05:00Z", measurement="STATE_AT_INSTANT", interval_start=None,
                          value="41.5", unit="%", quality="GOOD", unavailable_reason=None)
    text = device_report_text(report)
    assert text == (
        '{"device_id":"tank-1-level","interval_start":null,"measurement":"STATE_AT_INSTANT","quality":"GOOD",'
        '"report_key":"k-1","schema":{"id":"assetops.simulated-device-report","version":1},"signal_id":"level",'
        '"source_time":"2026-10-06T19:05:00Z","unavailable_reason":null,"unit":"%","value":"41.5"}'
    )
    assert parse_device_report_text(text) == report
    assert device_report_schema_version(text) == 1
    with pytest.raises(EnvelopeRejected) as v2:
        parse_device_report_v2_text(text)
    assert v2.value.kind == "MISSING_FIELD"


@pytest.mark.parametrize("field", ["run_id", "true_temperature", "cause", "scenario_id"])
def test_private_field_refused(field: str) -> None:
    document = json.loads(device_report_v2_text(_report(measurement="STATE_AT_INSTANT", value="3.8", unit="degC")))
    document[field] = "private"
    with pytest.raises(EnvelopeRejected) as refused:
        parse_device_report_v2_text(json.dumps(document, sort_keys=True, separators=(",", ":")))
    assert (refused.value.kind, refused.value.field) == ("UNKNOWN_FIELD", field)
