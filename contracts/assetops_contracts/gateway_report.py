"""The public device report a Lab host hands the separate gateway (S2-01b).

This is the only observation-shaped record that crosses the host-to-gateway
process boundary. It says what a device published - device, signal, sample
time, value as published, unit, availability - and nothing about why: no run
id, no true value, no cause, no event label, no scenario. Every level has an
exact key set, so a private field has nowhere to arrive (`UNKNOWN_FIELD`).

`report_key` is the device's own durable event identity when it has one. The
gateway uses it for duplicate suppression BEFORE allocating a sequence (technical
design 2): a replay of the same key and content reuses the admitted envelope; the
same key with different content is a held conflict. A report without a key is a
distinct physical event every time it arrives.

`report_from_observation` is the typed simulated adapter: one public
`DeviceObservation` becomes one report, or `None` when nothing was published
(dropped or suppressed observations publish nothing).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from typing import Any

from assetops_contracts.observation import DeviceObservation, exact_decimal_text
from assetops_contracts.source_envelope import EnvelopeRejected, canonical_json, load_canonical_json

DEVICE_REPORT_SCHEMA_ID = "assetops.simulated-device-report"
DEVICE_REPORT_SCHEMA_VERSION = 1

#: Observation outcomes that publish nothing at all.
NOT_PUBLISHED_OUTCOMES = frozenset({"SUPPRESSED_BY_GAP", "DROPPED"})
#: Observation outcomes published as an explicit UNAVAILABLE reading.
UNAVAILABLE_REASON_OF_OUTCOME = {
    "NO_PRECEDING_INTERVAL": "NO_COMPLETED_INTERVAL",
    "NO_VALUE_AT_BOUNDARY": "NO_MEASUREMENT",
}
MEASUREMENT_OF_READING_CLASS = {
    "STATE_SIGNAL": "STATE_AT_INSTANT",
    "INTERVAL_SIGNAL": "INTERVAL_MEAN",
}

_KEY = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._:-]{0,190}[A-Za-z0-9])?")
_KEYS = frozenset(
    {
        "schema",
        "report_key",
        "device_id",
        "signal_id",
        "source_time",
        "measurement",
        "interval_start",
        "value",
        "unit",
        "quality",
        "unavailable_reason",
    }
)


@dataclass(frozen=True)
class DeviceReport:
    """One public report. Field validity is the gateway's mapping decision;
    this record only fixes shape and types, so a bad value is held with its
    field rather than lost at the wire."""

    report_key: str | None
    device_id: str
    signal_id: str
    source_time: str
    measurement: str
    interval_start: str | None
    value: str | None
    unit: str
    quality: str
    unavailable_reason: str | None


def device_report_document(report: DeviceReport) -> dict[str, Any]:
    return {
        "schema": {"id": DEVICE_REPORT_SCHEMA_ID, "version": DEVICE_REPORT_SCHEMA_VERSION},
        "report_key": report.report_key,
        "device_id": report.device_id,
        "signal_id": report.signal_id,
        "source_time": report.source_time,
        "measurement": report.measurement,
        "interval_start": report.interval_start,
        "value": report.value,
        "unit": report.unit,
        "quality": report.quality,
        "unavailable_reason": report.unavailable_reason,
    }


def device_report_text(report: DeviceReport) -> str:
    return canonical_json(device_report_document(report))


def parse_device_report(document: object) -> DeviceReport:
    if not isinstance(document, dict):
        raise EnvelopeRejected("WRONG_TYPE", "report", "a report is an object")
    for key in sorted(document):
        if key not in _KEYS:
            raise EnvelopeRejected("UNKNOWN_FIELD", key, "not a field of a public device report")
    for key in sorted(_KEYS):
        if key not in document:
            raise EnvelopeRejected("MISSING_FIELD", key, "required (null when absent)")
    if document["schema"] != {"id": DEVICE_REPORT_SCHEMA_ID, "version": DEVICE_REPORT_SCHEMA_VERSION}:
        raise EnvelopeRejected("SCHEMA_UNSUPPORTED", "schema", f"{document['schema']!r}")
    for key in ("device_id", "signal_id", "source_time", "measurement", "unit", "quality"):
        if type(document[key]) is not str:
            raise EnvelopeRejected("WRONG_TYPE", key, "text is wanted")
    for key in ("report_key", "interval_start", "value", "unavailable_reason"):
        if document[key] is not None and type(document[key]) is not str:
            raise EnvelopeRejected("WRONG_TYPE", key, "text or null is wanted")
    key = document["report_key"]
    if key is not None and not _KEY.fullmatch(key):
        raise EnvelopeRejected("INVALID_IDENTITY", "report_key", f"{key!r} is not a report key")
    return DeviceReport(
        report_key=key,
        device_id=document["device_id"],
        signal_id=document["signal_id"],
        source_time=document["source_time"],
        measurement=document["measurement"],
        interval_start=document["interval_start"],
        value=document["value"],
        unit=document["unit"],
        quality=document["quality"],
        unavailable_reason=document["unavailable_reason"],
    )


def parse_device_report_text(text: object) -> DeviceReport:
    return parse_device_report(load_canonical_json(text))


def _at(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def report_from_observation(
    observation: DeviceObservation,
    *,
    interval_minutes: int,
    report_key: str | None,
) -> DeviceReport | None:
    """The simulated adapter: one public observation as one public report."""
    if not isinstance(observation, DeviceObservation):
        raise EnvelopeRejected("WRONG_TYPE", "observation", "only a DeviceObservation is adapted")
    if observation.outcome in NOT_PUBLISHED_OUTCOMES:
        return None
    measurement = MEASUREMENT_OF_READING_CLASS.get(observation.reading_class)
    if measurement is None:
        raise EnvelopeRejected("INVALID_PAYLOAD", "reading_class", f"{observation.reading_class!r}")
    interval_start = None
    if measurement == "INTERVAL_MEAN":
        start = _at(observation.source_sample_time) - timedelta(minutes=interval_minutes)
        interval_start = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    if observation.outcome == "REPORTED":
        raw = observation.reported_value
        value = exact_decimal_text(raw) if isinstance(raw, Fraction) else raw
        quality, reason = "GOOD", None
    else:
        value = None
        quality = "UNAVAILABLE"
        reason = UNAVAILABLE_REASON_OF_OUTCOME.get(observation.outcome)
        if reason is None:
            raise EnvelopeRejected("INVALID_PAYLOAD", "outcome", f"{observation.outcome!r}")
    return DeviceReport(
        report_key=report_key,
        device_id=observation.device_id,
        signal_id=observation.signal_id,
        source_time=observation.source_sample_time,
        measurement=measurement,
        interval_start=interval_start,
        value=value,
        unit=observation.canonical_unit,
        quality=quality,
        unavailable_reason=reason,
    )


# --- W2-02: DeviceReport v2 (cold events and measurements) ----------------------------------------------------
#
# `D-2026-10-17-w2-02-buildspec`, "DeviceReport v2 and gateway path". v1 above stays byte for byte. v2 carries
# what a SourceEnvelope V4 payload needs - a measurement or a witnessed event - and still nothing about why: no
# run ID, no private cause, no scenario. Every key is present on every report; an inapplicable field is null.
# Like v1, this record fixes shape and types only; the gateway validates the values with the V4 parser before
# any sequence is allocated.

DEVICE_REPORT_V2_SCHEMA_VERSION = 2

_KEYS_V2 = (
    "schema", "report_key", "device_id", "signal_id", "source_time", "family", "measurement", "interval_start",
    "interval_end", "value", "unit", "quality", "unavailable_reason", "record_kind", "event_id",
    "correlation_id", "component_id", "actor", "outcome", "session_id", "connector_id",
)
_REQUIRED_TEXT_V2 = ("device_id", "signal_id", "source_time", "family", "quality")


@dataclass(frozen=True)
class DeviceReportV2:
    """One public v2 report: a MEASUREMENT or an EVENT, every inapplicable field null."""

    report_key: str | None
    device_id: str
    signal_id: str
    source_time: str
    family: str
    measurement: str | None
    interval_start: str | None
    interval_end: str | None
    value: str | None
    unit: str | None
    quality: str
    unavailable_reason: str | None
    record_kind: str | None
    event_id: str | None
    correlation_id: str | None
    component_id: str | None
    actor: str | None
    outcome: str | None
    session_id: str | None
    connector_id: str | None


def device_report_v2_document(report: DeviceReportV2) -> dict[str, Any]:
    document: dict[str, Any] = {"schema": {"id": DEVICE_REPORT_SCHEMA_ID, "version": DEVICE_REPORT_V2_SCHEMA_VERSION}}
    for key in _KEYS_V2[1:]:
        document[key] = getattr(report, key)
    return document


def device_report_v2_text(report: DeviceReportV2) -> str:
    return canonical_json(device_report_v2_document(report))


def parse_device_report_v2(document: object) -> DeviceReportV2:
    if not isinstance(document, dict):
        raise EnvelopeRejected("WRONG_TYPE", "report", "a report is an object")
    for key in sorted(document):
        if key not in _KEYS_V2:
            raise EnvelopeRejected("UNKNOWN_FIELD", key, "not a field of a public device report")
    for key in sorted(_KEYS_V2):
        if key not in document:
            raise EnvelopeRejected("MISSING_FIELD", key, "required (null when absent)")
    if document["schema"] != {"id": DEVICE_REPORT_SCHEMA_ID, "version": DEVICE_REPORT_V2_SCHEMA_VERSION}:
        raise EnvelopeRejected("SCHEMA_UNSUPPORTED", "schema", f"{document['schema']!r}")
    for key in _KEYS_V2[1:]:
        value = document[key]
        if key in _REQUIRED_TEXT_V2:
            if type(value) is not str:
                raise EnvelopeRejected("WRONG_TYPE", key, "text is wanted")
        elif value is not None and type(value) is not str:
            raise EnvelopeRejected("WRONG_TYPE", key, "text or null is wanted")
    key = document["report_key"]
    if key is not None and not _KEY.fullmatch(key):
        raise EnvelopeRejected("INVALID_IDENTITY", "report_key", f"{key!r} is not a report key")
    return DeviceReportV2(**{k: document[k] for k in _KEYS_V2[1:]})


def parse_device_report_v2_text(text: object) -> DeviceReportV2:
    return parse_device_report_v2(load_canonical_json(text))


def device_report_schema_version(text: object) -> int | None:
    """The stated report schema version (1 or 2) of a report text, or None when it states neither.

    Dispatch only: the chosen parser then reads the whole report strictly."""
    try:
        document = load_canonical_json(text)
    except EnvelopeRejected:
        return None
    if not isinstance(document, dict):
        return None
    schema = document.get("schema")
    if isinstance(schema, dict) and schema.get("id") == DEVICE_REPORT_SCHEMA_ID:
        version = schema.get("version")
        if type(version) is int and version in (DEVICE_REPORT_SCHEMA_VERSION, DEVICE_REPORT_V2_SCHEMA_VERSION):
            return version
    return None


def _cold_digest(parts: list[object], prefix: str = "cold:") -> str:
    return prefix + hashlib.sha256(canonical_json(parts).encode("utf-8")).hexdigest()


def cold_event_id(*, scenario_sha256: str, device_id: str, signal_id: str, transition_ordinal: int) -> str:
    """`cold-` + SHA-256 of canonical `[scenario_sha256, device_id, signal_id, transition_ordinal]`.

    The V4 identifier grammar has no `:`; only report keys keep the `cold:` prefix."""
    return _cold_digest([scenario_sha256, device_id, signal_id, transition_ordinal], "cold-")


def cold_report_key(
    *,
    scenario_sha256: str,
    device_id: str,
    signal_id: str,
    source_time: str,
    record_kind: str | None,
    event_id: str | None,
    interval_start: str | None,
) -> str:
    """`cold:` + SHA-256 of canonical `(scenario_sha256, device_id, signal_id, source_time, record_kind,
    event_id, interval_start)`: deterministic, so a retransmission carries the same key."""
    return _cold_digest([scenario_sha256, device_id, signal_id, source_time, record_kind, event_id, interval_start])


def ev_event_id(*, scenario_sha256: str, device_id: str, signal_id: str, transition_ordinal: int) -> str:
    """W2-05b: `ev-` + lowercase SHA-256 of canonical `[scenario_sha256, device_id, signal_id, transition_ordinal]`.

    The ordinal increases per device/signal, ADD included, and never depends on publication time."""
    return _cold_digest([scenario_sha256, device_id, signal_id, transition_ordinal], "ev-")


def ev_fault_episode_id(*, scenario_sha256: str, connector_id: str, fault_ordinal: int) -> str:
    """W2-05b q3 Q16: `ev-` + lowercase SHA-256 of canonical `[scenario_sha256, "fault", connector_id,
    fault_ordinal]`, the correlation of a FAULT/CLEAR without an active session. `connector_id` is the bound
    `asset_code`; `fault_ordinal` the zero-based count of actual FAULT transitions on it in the run. An episode
    identity only: never a session ID or a charging-session token."""
    return _cold_digest([scenario_sha256, "fault", connector_id, fault_ordinal], "ev-")


def ev_report_key(
    *,
    scenario_sha256: str,
    device_id: str,
    signal_id: str,
    source_time: str,
    record_kind: str | None,
    event_id: str | None,
    interval_start: str | None,
) -> str:
    """W2-05b: the cold report-key identity inputs in an `ev:` namespace - `ev:` + SHA-256 of canonical
    `(scenario_sha256, device_id, signal_id, source_time, record_kind, event_id, interval_start)`."""
    return _cold_digest([scenario_sha256, device_id, signal_id, source_time, record_kind, event_id, interval_start],
                        "ev:")
