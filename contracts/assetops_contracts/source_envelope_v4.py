"""SourceEnvelope V4: ordinary source events and EV interval deltas (W2-00).

`.agent/W2-technical-design-cold.md` section 1 and `D-2026-10-17-w2-00-answers`. V4 is a separate module so
the V3 parser (`source_envelope_v3`) and the shared measurement allowlist stay frozen byte for byte.

V4 keeps V3's allocated message identity (`v3_message_id`), its canonical JSON, its UTC instants, exact
numeric text and its exact top-level, `message`, `source`, `mapping` and `timing` key sets. Only the
`payload` changes, and its exact key set depends on the family:

* MEASUREMENT: `family,measurement,value,unit,quality,unavailable_reason,session_id,connector_id`.
  `V4_MEASUREMENTS` adds `INTERVAL_DELTA` (nonnegative kWh over a positive interval ending at source time,
  with both EV IDs). Every other measurement carries both EV IDs as explicit null.
* EVENT: `family,record_kind,event_id,correlation_id,component_id,actor,outcome,unit,value,quality,
  session_id,connector_id`. An event is a witnessed public transition at its source time (no interval).

`event_identity_sha256` is the event-equality digest: SHA-256 of canonical JSON
`{source, timing:{source_time,interval_start,interval_end}, payload}`. Transport (`schema`, `message`,
`mapping`, `timing.published_at`) is excluded, so a retransmitted event under a new message ID compares equal.

`V4_CHANNEL_MAPPINGS` is the closed v4 channel table: the `simulator-lab-gateway-cold/1` entries (design
section 4), the two reserved W2-00 EV tuples, and the W2-05a `simulator-lab-gateway-ev/1` exact connector and
Site-import tuples (`D-2026-10-18-w2-05-buildspec` Q1/Q8). `V4_CHANNEL_MAPPINGS_BY_PROFILE` is the explicit
profile-to-closed-table lookup; the cold profile, its version and its entries are unchanged.

`read_envelope_header` is the Batch V2 header-only reader for V4 texts (ruling 3): it checks only the message
identity and the source/mapping fields that batch homogeneity and identity need.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any, Mapping

from assetops_contracts.control import DISCRETE_UNIT
from assetops_contracts.source_envelope import (
    ENVELOPE_UNAVAILABLE_REASONS,
    EnvelopeRejected as _SharedEnvelopeRejected,
    canonical_json,
    load_canonical_json,
)
from assetops_contracts.source_envelope_v3 import (
    _DIGEST,
    _IDENTIFIER,
    _MEMBER,
    _UNIT,
    MAX_SEQUENCE,
    SOURCE_ENVELOPE_V3_SCHEMA_ID,
    SOURCE_ENVELOPE_V3_SCHEMA_VERSION,
    SourceEnvelopeV3,
    _instant,
    is_canonical_decimal,
    parse_canonical_envelope_v3_text,
    text_sha256,
    v3_message_id,
)

SOURCE_ENVELOPE_V4_SCHEMA_ID = SOURCE_ENVELOPE_V3_SCHEMA_ID
SOURCE_ENVELOPE_V4_SCHEMA_VERSION = 4

V4_FAMILIES_WRITTEN = frozenset({"MEASUREMENT", "EVENT"})
V4_FAMILIES_NAMED = frozenset({"MEASUREMENT", "EVENT", "POLICY", "OPERATIONAL_RECORD"})
V4_MEASUREMENTS = frozenset({"STATE_AT_INSTANT", "INTERVAL_MEAN", "INTERVAL_DELTA"})
V4_ONLY_MEASUREMENTS = frozenset({"INTERVAL_DELTA"})
V4_MEASUREMENT_QUALITIES = frozenset({"GOOD", "SUSPECT", "UNAVAILABLE"})
V4_EVENT_QUALITIES = frozenset({"GOOD", "SUSPECT"})
V4_ACTORS = frozenset({"CONTROLLER", "SENSOR", "OPERATOR"})
DELTA_UNIT = "kWh"
MANUAL_LOG_UNIT = "degC"

#: The exact kind-to-outcome allowlist (design section 1). Every other pair is INVALID_PAYLOAD.
V4_EVENT_OUTCOMES: Mapping[str, frozenset[str]] = {
    "DOOR_OPEN": frozenset({"OPEN"}),
    "DOOR_CLOSE": frozenset({"CLOSED"}),
    "START_REQUEST": frozenset({"REQUESTED"}),
    "START_RESULT": frozenset({"SUCCEEDED", "FAILED"}),
    "TRANSFER_RESULT": frozenset({"SUCCEEDED", "FAILED"}),
    "POWER_LOSS": frozenset({"LOST"}),
    "POWER_RESTORED": frozenset({"RESTORED"}),
    "MANUAL_LOG": frozenset({"OBSERVED"}),
    "EV_SESSION_START": frozenset({"STARTED"}),
    "EV_SESSION_END": frozenset({"COMPLETED"}),
    "EV_SESSION_ABORT": frozenset({"ABORTED"}),
    "EV_CONNECTOR_FAULT": frozenset({"FAULTED"}),
    "EV_CONNECTOR_CLEAR": frozenset({"CLEARED"}),
}
V4_EVENT_KINDS = frozenset(V4_EVENT_OUTCOMES)
SITE_POWER_KINDS = frozenset({"POWER_LOSS", "POWER_RESTORED"})
EV_SESSION_KINDS = frozenset({"EV_SESSION_START", "EV_SESSION_END", "EV_SESSION_ABORT"})
EV_CONNECTOR_KINDS = frozenset({"EV_CONNECTOR_FAULT", "EV_CONNECTOR_CLEAR"})
EV_KINDS = EV_SESSION_KINDS | EV_CONNECTOR_KINDS

#: The V4 refusal kinds S2 records per ordinal (beyond the shared envelope kinds).
V4_REJECTION_KINDS = frozenset({
    "MAPPING_INCOMPATIBLE", "UNIT_INCOMPATIBLE", "RECORD_KIND_UNSUPPORTED", "CORRELATION_INVALID",
    "EV_CONNECTOR_MISMATCH", "EV_DELTA_UNIT_INVALID", "EV_DELTA_INTERVAL_INVALID", "EV_DELTA_VALUE_INVALID",
})

_ID_KEYS = frozenset({"event_id", "correlation_id", "session_id", "connector_id"})

#: Refusal kinds only the V4 parser raises. The shared `ENVELOPE_REJECTION_KINDS` vocabulary of the v1/v2/v3
#: readers stays unchanged; V4 refusals are a subclass, so every caller catching the shared type still does.
V4_PARSER_REJECTION_KINDS = frozenset({
    "RECORD_KIND_UNSUPPORTED", "CORRELATION_INVALID", "EV_DELTA_UNIT_INVALID", "EV_DELTA_INTERVAL_INVALID",
    "EV_DELTA_VALUE_INVALID",
})


class EnvelopeRejected(_SharedEnvelopeRejected):
    """A V4 refusal: the shared envelope kinds plus `V4_PARSER_REJECTION_KINDS`."""

    def __init__(self, kind: str, field: str, detail: str) -> None:
        if kind not in V4_PARSER_REJECTION_KINDS:
            super().__init__(kind, field, detail)
            return
        self.kind = kind
        self.field = field
        self.detail = detail
        ValueError.__init__(self, f"{kind} at {field}: {detail}")


# --- record -------------------------------------------------------------------


@dataclass(frozen=True)
class SourceEnvelopeV4:
    message_id: str
    sequence_epoch: str
    sequence: int
    site_id: str
    gateway_id: str
    source_id: str
    device_id: str
    signal_id: str
    binding_set_id: str
    binding_version: int
    source_time: str
    published_at: str
    interval_start: str | None
    interval_end: str | None
    family: str
    value: str | None
    unit: str | None
    quality: str
    session_id: str | None
    connector_id: str | None
    # MEASUREMENT only (None for an EVENT)
    measurement: str | None = None
    unavailable_reason: str | None = None
    # EVENT only (None for a MEASUREMENT)
    record_kind: str | None = None
    event_id: str | None = None
    correlation_id: str | None = None
    component_id: str | None = None
    actor: str | None = None
    outcome: str | None = None

    schema_version = SOURCE_ENVELOPE_V4_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _validate(self)


def _ident(value: object, field: str, kind: str = "INVALID_IDENTITY") -> str:
    if type(value) is not str:
        raise EnvelopeRejected("WRONG_TYPE" if kind == "INVALID_IDENTITY" else kind, field, "an identifier is text")
    if not _IDENTIFIER.fullmatch(value):
        raise EnvelopeRejected(kind, field, f"{value!r} is not an identifier")
    return value


def _correlation(value: object, field: str, *, required: bool) -> None:
    """EV/event identifiers: absent, null where required, wrong type or malformed are CORRELATION_INVALID."""
    if value is None:
        if required:
            raise EnvelopeRejected("CORRELATION_INVALID", field, "this record requires the identifier")
        return
    if type(value) is not str or not _IDENTIFIER.fullmatch(value):
        raise EnvelopeRejected("CORRELATION_INVALID", field, f"{value!r} is not an identifier")


def _no_correlation(value: object, field: str) -> None:
    if value is not None:
        raise EnvelopeRejected("CORRELATION_INVALID", field, "this record carries the identifier as explicit null")


def _int(value: object, field: str) -> int:
    if type(value) is not int:
        raise EnvelopeRejected("WRONG_TYPE", field, "a whole number is wanted")
    if value < 1 or value > MAX_SEQUENCE:
        raise EnvelopeRejected("INVALID_IDENTITY", field, f"{value} is outside 1..{MAX_SEQUENCE}")
    return value


def _validate_identity(e: SourceEnvelopeV4) -> None:
    for field in ("site_id", "gateway_id", "source_id", "device_id", "signal_id", "binding_set_id", "sequence_epoch"):
        _ident(getattr(e, field), field)
    _int(e.sequence, "message.sequence")
    _int(e.binding_version, "mapping.version")
    if type(e.message_id) is not str or not _DIGEST.fullmatch(e.message_id):
        raise EnvelopeRejected("INVALID_IDENTITY", "message.message_id", "not a SHA-256 hex digest")
    expected = v3_message_id(site_id=e.site_id, gateway_id=e.gateway_id, source_id=e.source_id,
                             sequence_epoch=e.sequence_epoch, sequence=e.sequence)
    if e.message_id != expected:
        raise EnvelopeRejected("INVALID_IDENTITY", "message.message_id",
                               "does not match the length-delimited identity of this envelope")


def _validate(e: SourceEnvelopeV4) -> None:
    _validate_identity(e)
    source = _instant(e.source_time, "timing.source_time")
    published = _instant(e.published_at, "timing.published_at")
    if published < source:
        raise EnvelopeRejected("INVALID_TIMING", "timing.published_at", "published before the source time")
    if e.family not in V4_FAMILIES_NAMED:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.family", f"{e.family!r} is not a family")
    if e.family not in V4_FAMILIES_WRITTEN:
        raise EnvelopeRejected("SCHEMA_UNSUPPORTED", "payload.family",
                               f"{e.family} has no versioned record_detail contract in V4 yet")
    if e.family == "MEASUREMENT":
        _validate_measurement(e, source)
    else:
        _validate_event(e)


def _quantity(e: SourceEnvelopeV4) -> None:
    """V3's value rules for a GOOD/SUSPECT/UNAVAILABLE measurement."""
    if type(e.unit) is not str or not _UNIT.fullmatch(e.unit):
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.unit", f"{e.unit!r} is not a unit")
    if e.quality not in V4_MEASUREMENT_QUALITIES:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.quality", f"{e.quality!r} is not a quality")
    if e.quality == "UNAVAILABLE":
        if e.value is not None:
            raise EnvelopeRejected("INVALID_PAYLOAD", "payload.value", "an unavailable reading has no value")
        if e.unavailable_reason not in ENVELOPE_UNAVAILABLE_REASONS:
            raise EnvelopeRejected("INVALID_PAYLOAD", "payload.unavailable_reason",
                                   f"{e.unavailable_reason!r} is not an unavailable reason")
        return
    if e.unavailable_reason is not None:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.unavailable_reason",
                               "only an unavailable reading has a reason")
    if type(e.value) is not str:
        raise EnvelopeRejected("WRONG_TYPE", "payload.value", "a value is text")
    if e.unit == DISCRETE_UNIT:
        if not _MEMBER.fullmatch(e.value):
            raise EnvelopeRejected("INVALID_PAYLOAD", "payload.value", f"{e.value!r} is not a discrete member")
    elif not is_canonical_decimal(e.value):
        raise EnvelopeRejected("NOT_CANONICAL", "payload.value", f"{e.value!r} is not a canonical decimal string")


def _validate_measurement(e: SourceEnvelopeV4, source) -> None:
    if e.measurement not in V4_MEASUREMENTS:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.measurement", f"{e.measurement!r} is not a measurement")
    if e.measurement == "INTERVAL_DELTA":
        _validate_delta(e, source)
        return
    _quantity(e)
    if e.measurement == "INTERVAL_MEAN":
        if e.interval_start is None or e.interval_end is None:
            raise EnvelopeRejected("INVALID_TIMING", "timing.interval_start", "an interval mean states its interval")
        start = _instant(e.interval_start, "timing.interval_start")
        _instant(e.interval_end, "timing.interval_end")
        if e.interval_end != e.source_time:
            raise EnvelopeRejected("INVALID_TIMING", "timing.interval_end", "an interval ends at its source time")
        if start >= source:
            raise EnvelopeRejected("INVALID_TIMING", "timing.interval_start", "an interval has positive length")
    elif e.interval_start is not None or e.interval_end is not None:
        raise EnvelopeRejected("INVALID_TIMING", "timing.interval_start", "a state-at-instant reading has no interval")
    _no_correlation(e.session_id, "payload.session_id")
    _no_correlation(e.connector_id, "payload.connector_id")


def _validate_delta(e: SourceEnvelopeV4, source) -> None:
    """Ruling 2: the three EV_DELTA_* codes, then CORRELATION_INVALID for the paired EV IDs."""
    if e.unit != DELTA_UNIT:
        raise EnvelopeRejected("EV_DELTA_UNIT_INVALID", "payload.unit", f"an interval delta is {DELTA_UNIT}, not {e.unit!r}")
    if e.interval_start is None:
        raise EnvelopeRejected("EV_DELTA_INTERVAL_INVALID", "timing.interval_start", "an interval delta states its start")
    if e.interval_end is None:
        raise EnvelopeRejected("EV_DELTA_INTERVAL_INVALID", "timing.interval_end", "an interval delta states its end")
    start = _instant(e.interval_start, "timing.interval_start")
    end = _instant(e.interval_end, "timing.interval_end")
    if end != source:
        raise EnvelopeRejected("EV_DELTA_INTERVAL_INVALID", "timing.interval_end", "an interval delta ends at its source time")
    if start >= end:
        raise EnvelopeRejected("EV_DELTA_INTERVAL_INVALID", "timing.interval_start", "an interval delta has positive length")
    if e.quality not in V4_MEASUREMENT_QUALITIES:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.quality", f"{e.quality!r} is not a quality")
    if e.quality == "UNAVAILABLE" or e.value is None:
        raise EnvelopeRejected("EV_DELTA_VALUE_INVALID", "payload.value", "an interval delta states an available value")
    if e.unavailable_reason is not None:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.unavailable_reason", "only an unavailable reading has a reason")
    if type(e.value) is not str:
        raise EnvelopeRejected("WRONG_TYPE", "payload.value", "a value is text")
    if not is_canonical_decimal(e.value):
        raise EnvelopeRejected("NOT_CANONICAL", "payload.value", f"{e.value!r} is not a canonical decimal string")
    if e.value.startswith("-"):
        raise EnvelopeRejected("EV_DELTA_VALUE_INVALID", "payload.value", "an interval delta is nonnegative")
    _correlation(e.session_id, "payload.session_id", required=True)
    _correlation(e.connector_id, "payload.connector_id", required=True)


def _validate_event(e: SourceEnvelopeV4) -> None:
    kind = e.record_kind
    if type(kind) is not str:
        raise EnvelopeRejected("WRONG_TYPE", "payload.record_kind", "a record kind is text")
    if kind not in V4_EVENT_KINDS:
        raise EnvelopeRejected("RECORD_KIND_UNSUPPORTED", "payload.record_kind", f"{kind!r} is not a V4 event kind")
    if e.interval_start is not None or e.interval_end is not None:
        raise EnvelopeRejected("INVALID_TIMING", "timing.interval_start",
                               "an event is an observed transition at its source time, not a duration")
    _correlation(e.event_id, "payload.event_id", required=True)
    _correlation(e.correlation_id, "payload.correlation_id", required=True)
    if kind in SITE_POWER_KINDS and e.component_id is None:
        pass
    else:
        _ident(e.component_id, "payload.component_id")
    if e.actor not in V4_ACTORS:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.actor", f"{e.actor!r} is not an actor")
    if e.outcome not in V4_EVENT_OUTCOMES[kind]:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.outcome", f"{e.outcome!r} is not an outcome of {kind}")
    if e.quality not in V4_EVENT_QUALITIES:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.quality", f"{e.quality!r} is not an event quality")
    if kind == "MANUAL_LOG":
        if type(e.unit) is not str:
            raise EnvelopeRejected("WRONG_TYPE", "payload.unit", "a manual log states its unit")
        if e.unit != MANUAL_LOG_UNIT:
            raise EnvelopeRejected("UNIT_INCOMPATIBLE", "payload.unit", f"a manual log is {MANUAL_LOG_UNIT}, not {e.unit!r}")
        if type(e.value) is not str:
            raise EnvelopeRejected("WRONG_TYPE", "payload.value", "a value is text")
        if not is_canonical_decimal(e.value):
            raise EnvelopeRejected("NOT_CANONICAL", "payload.value", f"{e.value!r} is not a canonical decimal string")
    elif e.unit is not None or e.value is not None:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.value", f"a {kind} event has null value and unit")
    if kind in EV_SESSION_KINDS:
        _correlation(e.session_id, "payload.session_id", required=True)
        _correlation(e.connector_id, "payload.connector_id", required=True)
        if e.correlation_id != e.session_id:
            raise EnvelopeRejected("CORRELATION_INVALID", "payload.correlation_id",
                                   "a session event's correlation ID is its session ID")
    elif kind in EV_CONNECTOR_KINDS:
        _correlation(e.session_id, "payload.session_id", required=False)
        _correlation(e.connector_id, "payload.connector_id", required=True)
    else:
        _no_correlation(e.session_id, "payload.session_id")
        _no_correlation(e.connector_id, "payload.connector_id")


# --- canonical text -----------------------------------------------------------


def envelope_v4_document(e: SourceEnvelopeV4) -> dict[str, Any]:
    if e.family == "EVENT":
        payload = {
            "family": e.family, "record_kind": e.record_kind, "event_id": e.event_id,
            "correlation_id": e.correlation_id, "component_id": e.component_id, "actor": e.actor,
            "outcome": e.outcome, "unit": e.unit, "value": e.value, "quality": e.quality,
            "session_id": e.session_id, "connector_id": e.connector_id,
        }
    else:
        payload = {
            "family": e.family, "measurement": e.measurement, "value": e.value, "unit": e.unit,
            "quality": e.quality, "unavailable_reason": e.unavailable_reason,
            "session_id": e.session_id, "connector_id": e.connector_id,
        }
    return {
        "schema": {"id": SOURCE_ENVELOPE_V4_SCHEMA_ID, "version": SOURCE_ENVELOPE_V4_SCHEMA_VERSION},
        "message": {"message_id": e.message_id, "sequence_epoch": e.sequence_epoch, "sequence": e.sequence},
        "source": {"site_id": e.site_id, "gateway_id": e.gateway_id, "source_id": e.source_id,
                   "device_id": e.device_id, "signal_id": e.signal_id},
        "mapping": {"binding_set_id": e.binding_set_id, "version": e.binding_version},
        "timing": {"source_time": e.source_time, "published_at": e.published_at,
                   "interval_start": e.interval_start, "interval_end": e.interval_end},
        "payload": payload,
    }


def canonical_envelope_v4_text(e: SourceEnvelopeV4) -> str:
    return canonical_json(envelope_v4_document(e))


def event_identity_text(e: SourceEnvelopeV4) -> str:
    """Ruling 1: canonical `{source, timing minus published_at, payload}`; transport excluded."""
    doc = envelope_v4_document(e)
    timing = doc["timing"]
    return canonical_json({
        "source": doc["source"],
        "timing": {"source_time": timing["source_time"], "interval_start": timing["interval_start"],
                   "interval_end": timing["interval_end"]},
        "payload": doc["payload"],
    })


def event_identity_sha256(envelope_text: str) -> str:
    """The event-equality digest computed from a stored canonical V4 envelope text (no stored column)."""
    return text_sha256(event_identity_text(parse_canonical_envelope_v4_text(envelope_text)))


_KEYS = {
    "": frozenset({"schema", "message", "source", "mapping", "timing", "payload"}),
    "schema": frozenset({"id", "version"}),
    "message": frozenset({"message_id", "sequence_epoch", "sequence"}),
    "source": frozenset({"site_id", "gateway_id", "source_id", "device_id", "signal_id"}),
    "mapping": frozenset({"binding_set_id", "version"}),
    "timing": frozenset({"source_time", "published_at", "interval_start", "interval_end"}),
    "payload.MEASUREMENT": frozenset({"family", "measurement", "value", "unit", "quality", "unavailable_reason",
                                      "session_id", "connector_id"}),
    "payload.EVENT": frozenset({"family", "record_kind", "event_id", "correlation_id", "component_id", "actor",
                                "outcome", "unit", "value", "quality", "session_id", "connector_id"}),
}


def _exact(document: object, where: str, keys: str | None = None) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise EnvelopeRejected("NOT_AN_ENVELOPE" if not where else "WRONG_TYPE", where or "envelope",
                               "an object is wanted")
    wanted = _KEYS[keys or where]
    for key in sorted(document):
        if key not in wanted:
            raise EnvelopeRejected("UNKNOWN_FIELD", f"{where}.{key}" if where else key, "not a field of a V4 envelope")
    for key in sorted(wanted):
        if key not in document:
            path = f"{where}.{key}" if where else key
            if where == "payload" and key in _ID_KEYS:
                # Ruling 2: an absent EV/event identifier key is CORRELATION_INVALID, not generic MISSING_FIELD.
                raise EnvelopeRejected("CORRELATION_INVALID", path, "required (null when absent)")
            raise EnvelopeRejected("MISSING_FIELD", path, "required (null when absent)")
    return document


def parse_source_envelope_v4(document: object) -> SourceEnvelopeV4:
    top = _exact(document, "")
    schema = _exact(top["schema"], "schema")
    if (schema["id"] != SOURCE_ENVELOPE_V4_SCHEMA_ID or type(schema["version"]) is not int
            or schema["version"] != SOURCE_ENVELOPE_V4_SCHEMA_VERSION):
        raise EnvelopeRejected("SCHEMA_UNSUPPORTED", "schema",
                               f"{schema['id']!r} v{schema['version']!r} is not a V4 envelope")
    message = _exact(top["message"], "message")
    source = _exact(top["source"], "source")
    mapping = _exact(top["mapping"], "mapping")
    timing = _exact(top["timing"], "timing")
    raw = top["payload"]
    if not isinstance(raw, dict):
        raise EnvelopeRejected("WRONG_TYPE", "payload", "an object is wanted")
    if "family" not in raw:
        raise EnvelopeRejected("MISSING_FIELD", "payload.family", "required")
    family = raw["family"]
    if family not in V4_FAMILIES_NAMED:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.family", f"{family!r} is not a family")
    if family not in V4_FAMILIES_WRITTEN:
        raise EnvelopeRejected("SCHEMA_UNSUPPORTED", "payload.family",
                               f"{family} has no versioned record_detail contract in V4 yet")
    payload = _exact(raw, "payload", f"payload.{family}")
    common = dict(
        message_id=message["message_id"], sequence_epoch=message["sequence_epoch"], sequence=message["sequence"],
        site_id=source["site_id"], gateway_id=source["gateway_id"], source_id=source["source_id"],
        device_id=source["device_id"], signal_id=source["signal_id"],
        binding_set_id=mapping["binding_set_id"], binding_version=mapping["version"],
        source_time=timing["source_time"], published_at=timing["published_at"],
        interval_start=timing["interval_start"], interval_end=timing["interval_end"],
        family=family, value=payload["value"], unit=payload["unit"], quality=payload["quality"],
        session_id=payload["session_id"], connector_id=payload["connector_id"],
    )
    if family == "MEASUREMENT":
        return SourceEnvelopeV4(**common, measurement=payload["measurement"],
                                unavailable_reason=payload["unavailable_reason"])
    return SourceEnvelopeV4(
        **common, record_kind=payload["record_kind"], event_id=payload["event_id"],
        correlation_id=payload["correlation_id"], component_id=payload["component_id"],
        actor=payload["actor"], outcome=payload["outcome"],
    )


def parse_canonical_envelope_v4_text(text: object) -> SourceEnvelopeV4:
    """Stored bytes back as the V4 envelope; refuses anything not already canonical."""
    envelope = parse_source_envelope_v4(load_canonical_json(text))
    if canonical_envelope_v4_text(envelope) != text:
        raise EnvelopeRejected("NOT_CANONICAL", "envelope", "the text parses and is not its own canonical text")
    return envelope


# --- version dispatch -----------------------------------------------------------


def _loose(text: object) -> Any:
    if type(text) is not str:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def _stated(document: Any) -> tuple[Any, Any]:
    """(schema version, payload) as stated, without validating either."""
    if not isinstance(document, dict):
        return None, None
    schema = document.get("schema")
    version = schema.get("version") if isinstance(schema, dict) else None
    return version, document.get("payload")


def _v4_only_kind(payload: Any) -> str | None:
    """The field naming a V4-only kind in a payload, or None."""
    if not isinstance(payload, dict):
        return None
    if payload.get("family") == "EVENT":
        return "payload.family"
    if payload.get("measurement") in V4_ONLY_MEASUREMENTS:
        return "payload.measurement"
    return None


def uses_v4_header_path(text: object) -> bool:
    """Ruling 3: schema 4, or schema 3 carrying a V4-only kind, is admitted to a batch by its header only."""
    version, payload = _stated(_loose(text))
    if type(version) is not int:
        return False
    return version == SOURCE_ENVELOPE_V4_SCHEMA_VERSION or (
        version == SOURCE_ENVELOPE_V3_SCHEMA_VERSION and _v4_only_kind(payload) is not None)


def parse_canonical_source_envelope_text(text: object) -> SourceEnvelopeV3 | SourceEnvelopeV4:
    """Dispatch by stated schema only: V3 stays strict and frozen; a V4-only kind under V3 is SCHEMA_UNSUPPORTED."""
    version, payload = _stated(_loose(text))
    if type(version) is int and version == SOURCE_ENVELOPE_V4_SCHEMA_VERSION:
        return parse_canonical_envelope_v4_text(text)
    if type(version) is int and version == SOURCE_ENVELOPE_V3_SCHEMA_VERSION:
        field = _v4_only_kind(payload)
        if field is not None:
            raise EnvelopeRejected("SCHEMA_UNSUPPORTED", field, "this kind is a V4 record and V3 cannot carry it")
    return parse_canonical_envelope_v3_text(text)


# --- Batch V2 header-only reader ------------------------------------------------


@dataclass(frozen=True)
class EnvelopeHeader:
    """The header fields Batch V2 homogeneity and identity need; payload, timing and canonical bytes unchecked."""

    message_id: str
    sequence_epoch: str
    sequence: int
    site_id: str
    gateway_id: str
    source_id: str
    binding_set_id: str
    binding_version: int


def read_envelope_header(text: object) -> EnvelopeHeader:
    document = _loose(text)
    if not isinstance(document, dict):
        raise EnvelopeRejected("MALFORMED_TEXT", "envelope", "a JSON object is wanted")
    message = _exact(document.get("message"), "message")
    source = document.get("source")
    mapping = document.get("mapping")
    if not isinstance(source, dict):
        raise EnvelopeRejected("WRONG_TYPE", "source", "an object is wanted")
    if not isinstance(mapping, dict):
        raise EnvelopeRejected("WRONG_TYPE", "mapping", "an object is wanted")
    for where, holder, key in (("source.site_id", source, "site_id"), ("source.gateway_id", source, "gateway_id"),
                               ("source.source_id", source, "source_id"),
                               ("mapping.binding_set_id", mapping, "binding_set_id"),
                               ("message.sequence_epoch", message, "sequence_epoch")):
        if key not in holder:
            raise EnvelopeRejected("MISSING_FIELD", where, "required")
        _ident(holder[key], where)
    if "version" not in mapping:
        raise EnvelopeRejected("MISSING_FIELD", "mapping.version", "required")
    sequence = _int(message["sequence"], "message.sequence")
    version = _int(mapping["version"], "mapping.version")
    message_id = message["message_id"]
    if type(message_id) is not str or not _DIGEST.fullmatch(message_id):
        raise EnvelopeRejected("INVALID_IDENTITY", "message.message_id", "not a SHA-256 hex digest")
    if message_id != v3_message_id(site_id=source["site_id"], gateway_id=source["gateway_id"],
                                   source_id=source["source_id"], sequence_epoch=message["sequence_epoch"],
                                   sequence=sequence):
        raise EnvelopeRejected("INVALID_IDENTITY", "message.message_id",
                               "does not match the length-delimited identity of this envelope")
    return EnvelopeHeader(message_id=message_id, sequence_epoch=message["sequence_epoch"], sequence=sequence,
                          site_id=source["site_id"], gateway_id=source["gateway_id"], source_id=source["source_id"],
                          binding_set_id=mapping["binding_set_id"], binding_version=version)


def header_message_id(text: object) -> str:
    """The valid header's message ID for an ordinal refusal, or '' when the header itself is invalid."""
    try:
        return read_envelope_header(text).message_id
    except EnvelopeRejected:
        return ""


# --- closed channel table -------------------------------------------------------

V4_MAPPING_PROFILE_ID = "simulator-lab-gateway-cold"
V4_MAPPING_PROFILE_VERSION = 1
#: W2-05a Q8: the distinct EV profile EV-LAB-001 binds under; 05b registers its producer.
V4_EV_MAPPING_PROFILE_ID = "simulator-lab-gateway-ev"
V4_EV_MAPPING_PROFILE_VERSION = 1
#: W4-02 closure 4 B2: the *authored* (non-Lab) mini-grid depth profile `minigrid-roles-4` binds its three v4 roles
#: under. No simulator publication emits these tuples.
V4_MINI_MAPPING_PROFILE_ID = "authored-mini-depth-cases"
V4_MINI_MAPPING_PROFILE_VERSION = 1


@dataclass(frozen=True)
class ChannelMapping:
    """One closed `(device_id, signal_id)` entry: the family/measurement it carries and its v4 metadata."""

    family: str
    measurement: str | None
    allowed_record_kinds: tuple[str, ...]
    requires_correlation: bool
    requires_session: bool
    allowed_units: tuple[str, ...]
    #: W2-01 (W2-00 review Low 2, design section 3 W2-02 channel closure): the exact `cold-roles-1` role the
    #: channel serves. None only for the reserved EV tuples, whose roles W2-05a defines.
    role: str | None = None

    @property
    def allowed_outcomes(self) -> dict[str, list[str]]:
        return {k: sorted(V4_EVENT_OUTCOMES[k]) for k in self.allowed_record_kinds}

    def metadata(self) -> dict[str, Any]:
        """The five snapshot binding-row keys this entry requires, in their canonical spelling."""
        return {
            "allowed_record_kinds": sorted(self.allowed_record_kinds),
            "allowed_outcomes": self.allowed_outcomes,
            "requires_correlation": self.requires_correlation,
            "requires_session": self.requires_session,
            "allowed_units": sorted(self.allowed_units),
        }


def _point(unit: str) -> ChannelMapping:
    return ChannelMapping("MEASUREMENT", "STATE_AT_INSTANT", (), False, False, (unit,))


def _events(*kinds: str, session: bool = False, units: tuple[str, ...] = ()) -> ChannelMapping:
    return ChannelMapping("EVENT", None, tuple(kinds), True, session, units)


#: Design section 4: the closed `simulator-lab-gateway-cold/1` table. Same signal ID on a different device is
#: not an alias. Schema 4.
V4_COLD_CHANNEL_MAPPINGS: Mapping[tuple[str, str], ChannelMapping] = {
    ("chamber-probe", "temperature"): replace(_point("degC"), role="chamber_temperature"),
    ("ambient-probe", "temperature"): replace(_point("degC"), role="ambient_temperature"),
    ("grid-meter", "state"): replace(_point(DISCRETE_UNIT), role="grid_state"),
    ("generator-controller", "state"): replace(_point(DISCRETE_UNIT), role="generator_state"),
    ("compressor-controller", "state"): replace(_point(DISCRETE_UNIT), role="compressor_state"),
    ("backup-bus-meter", "state"): replace(_point(DISCRETE_UNIT), role="backup_bus_state"),
    ("compressor-meter", "power"): ChannelMapping("MEASUREMENT", "INTERVAL_MEAN", (), False, False, ("kW",),
                                                  role="compressor_power"),
    ("door-sensor", "event"): replace(_events("DOOR_OPEN", "DOOR_CLOSE"), role="door_event"),
    ("generator-controller", "start-event"): replace(_events("START_REQUEST", "START_RESULT"),
                                                     role="backup_start_event"),
    ("transfer-controller", "event"): replace(_events("TRANSFER_RESULT"), role="transfer_result"),
    ("grid-meter", "event"): replace(_events("POWER_LOSS", "POWER_RESTORED"), role="grid_power_event"),
    ("operator-log", "temperature-event"): replace(_events("MANUAL_LOG", units=(MANUAL_LOG_UNIT,)),
                                                   role="manual_temperature"),
}


def _interval(unit: str, *, session: bool = False) -> ChannelMapping:
    return ChannelMapping("MEASUREMENT", "INTERVAL_MEAN", (), False, session, (unit,))


def _ev_connector(prefix: str) -> dict[tuple[str, str], ChannelMapping]:
    """W2-05a Q1 and Run 8 M3: one connector's seven exact tuples. Only connector energy (`INTERVAL_DELTA`) carries
    nonnull `session_id` and `connector_id`. Power, requested power and allocated limit are `INTERVAL_MEAN`, and
    connector state is a point measurement, each with explicit null for both IDs: the exact effective source
    binding supplies the connector, and a mean claims no session."""
    return {
        (f"{prefix}-charger-controller", "session-event"): replace(
            _events(*sorted(EV_SESSION_KINDS), session=True), role="ev_session_event"),
        (f"{prefix}-connector-controller", "fault-event"): replace(
            _events(*sorted(EV_CONNECTOR_KINDS)), role="ev_connector_fault"),
        (f"{prefix}-connector-controller", "state"): replace(_point(DISCRETE_UNIT), role="ev_connector_state"),
        (f"{prefix}-connector-controller", "requested-power"): replace(_interval("kW"), role="ev_requested_power"),
        (f"{prefix}-connector-controller", "allocated-limit"): replace(_interval("kW"), role="ev_allocated_limit"),
        (f"{prefix}-connector-meter", "energy"): ChannelMapping("MEASUREMENT", "INTERVAL_DELTA", (), False, True,
                                                                (DELTA_UNIT,), role="ev_connector_energy"),
        (f"{prefix}-connector-meter", "power"): replace(_interval("kW"), role="ev_connector_power"),
    }


#: W2-05a: the closed `simulator-lab-gateway-ev/1` table - exactly the c1/c2 tuples and the one Site import.
V4_EV_CHANNEL_MAPPINGS: Mapping[tuple[str, str], ChannelMapping] = {
    **_ev_connector("c1"),
    **_ev_connector("c2"),
    ("site-meter", "import"): replace(_interval("kW"), role="ev_site_import"),
}

#: W4-02 closure 4 B2: the closed `authored-mini-depth-cases/1` table - exactly these three tuples. Distinct role
#: names from cold's `backup_start_event`/`backup_bus_state`; the cold table above is unchanged.
V4_MINI_CHANNEL_MAPPINGS: Mapping[tuple[str, str], ChannelMapping] = {
    ("mini-primary-bus-meter", "state"): replace(_point(DISCRETE_UNIT), role="site_supply_state"),
    ("mini-generator-controller", "start-event"): replace(_events("START_REQUEST", "START_RESULT"),
                                                          role="mini_backup_start_event"),
    ("mini-backup-bus-meter", "state"): replace(_point(DISCRETE_UNIT), role="mini_backup_bus_state"),
}

#: Every closed v4 tuple: the cold table, the two reserved W2-00 EV tuples (kept for their tests, now labelled
#: with their EV roles, never bound by EV-LAB-001) and the EV table.
V4_CHANNEL_MAPPINGS: Mapping[tuple[str, str], ChannelMapping] = {
    **V4_COLD_CHANNEL_MAPPINGS,
    ("charger-controller", "session-event"): replace(
        _events("EV_SESSION_START", "EV_SESSION_END", "EV_SESSION_ABORT", session=True), role="ev_session_event"),
    ("connector-controller", "fault-event"): replace(_events("EV_CONNECTOR_FAULT", "EV_CONNECTOR_CLEAR"),
                                                     role="ev_connector_fault"),
    **V4_EV_CHANNEL_MAPPINGS,
    **V4_MINI_CHANNEL_MAPPINGS,
}

#: The explicit profile-to-closed-table lookup (Q8).
V4_CHANNEL_MAPPINGS_BY_PROFILE: Mapping[tuple[str, int], Mapping[tuple[str, str], ChannelMapping]] = {
    (V4_MAPPING_PROFILE_ID, V4_MAPPING_PROFILE_VERSION): V4_COLD_CHANNEL_MAPPINGS,
    (V4_EV_MAPPING_PROFILE_ID, V4_EV_MAPPING_PROFILE_VERSION): V4_EV_CHANNEL_MAPPINGS,
    (V4_MINI_MAPPING_PROFILE_ID, V4_MINI_MAPPING_PROFILE_VERSION): V4_MINI_CHANNEL_MAPPINGS,
}

V4_BINDING_METADATA_KEYS = ("allowed_record_kinds", "allowed_outcomes", "requires_correlation",
                            "requires_session", "allowed_units")


def canonical_binding_metadata(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """A snapshot binding row's five v4 keys in canonical spelling, or None when any is absent or ill-typed."""
    if any(row.get(k) is None for k in V4_BINDING_METADATA_KEYS):
        return None
    kinds, outcomes, units = row["allowed_record_kinds"], row["allowed_outcomes"], row["allowed_units"]
    if (not isinstance(kinds, (list, tuple)) or not all(type(k) is str for k in kinds)
            or not isinstance(units, (list, tuple)) or not all(type(u) is str for u in units)
            or not isinstance(outcomes, Mapping)
            or not all(type(k) is str and isinstance(v, (list, tuple)) and all(type(o) is str for o in v)
                       for k, v in outcomes.items())
            or type(row["requires_correlation"]) is not bool or type(row["requires_session"]) is not bool):
        return None
    return {
        "allowed_record_kinds": sorted(kinds),
        "allowed_outcomes": {k: sorted(v) for k, v in outcomes.items()},
        "requires_correlation": row["requires_correlation"],
        "requires_session": row["requires_session"],
        "allowed_units": sorted(units),
    }

