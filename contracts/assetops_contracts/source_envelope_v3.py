"""SourceEnvelope V3: the durable-gateway wire record (S2-01b, technical design 3).

V3 is a separate module so the v1/v2 reader in `source_envelope` keeps its
identity semantics byte for byte: historical stages and committed artifacts
are still read by that module and nothing here changes them.

## What changed from v2: identity is an allocated sequence, not content

A v2 `message_id` was a digest over (site, gateway, source, device, signal,
source_time), so two distinct reports at one source time collided. A V3
`message_id` is SHA-256 over the length-delimited tuple

    (MESSAGE_ID_V3_DOMAIN, site_id, gateway_id, source_id, sequence_epoch,
     decimal(sequence))

where the gateway allocates `(gateway, source, epoch, sequence)` exactly once in
the same SQLite transaction that stores the envelope. The parser recomputes the
id; a sender-supplied digest is never trusted.

## Framing (`length_delimited`)

Each field is UTF-8 encoded and written as a 4-byte unsigned big-endian byte
length followed by the bytes; fields are concatenated in order. The domain is
the first field. `sequence` is written as its canonical decimal text (no sign,
no leading zeros). Without the length prefix, ("ab","c") and ("a","bc") would
hash identically; `contract-fixtures/source-envelope-v3-vectors.json` pins the
vectors, including that pair.

## Canonical text

Sorted keys, no insignificant whitespace, UTF-8 (`ensure_ascii=False`), every
key of the fixed key set present (an absent optional is `null`, never omitted),
no binary numbers anywhere except the integers `schema.version`,
`mapping.version` and `message.sequence`. A value is a canonical decimal string
(`-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?`, no `-0`, no exponent, no ratio form), a
discrete member in the `state` unit, or `null` when the reading is UNAVAILABLE.
Instants are UTC `YYYY-MM-DDTHH:MM:SSZ`. `envelope_sha256` is SHA-256 over the
UTF-8 bytes of exactly that text.

## Families

V3 names three families. This build writes and reads MEASUREMENT only; POLICY
and OPERATIONAL_RECORD need a versioned `record_detail` contract that does not
exist yet, so they are refused as `SCHEMA_UNSUPPORTED` rather than read loosely.

`published_at` is the instant the gateway sealed the envelope, never a corrected
source time, and never earlier than `source_time`. No field can carry a Lab run
id, a cause, an event label, a true value or an oracle: every level has an
exact key set and an unknown key is refused.
"""

from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from assetops_contracts.control import DISCRETE_UNIT
from assetops_contracts.source_envelope import (
    ENVELOPE_MEASUREMENTS,
    ENVELOPE_UNAVAILABLE_REASONS,
    EnvelopeRejected,
    canonical_json,
    load_canonical_json,
)

SOURCE_ENVELOPE_V3_SCHEMA_ID = "assetops.source-envelope"
SOURCE_ENVELOPE_V3_SCHEMA_VERSION = 3
MESSAGE_ID_V3_DOMAIN = "assetops.source-envelope.message-id.v3"

#: SQLite INTEGER is signed 64-bit; a sequence past this needs a new epoch.
MAX_SEQUENCE = 2**63 - 1

V3_FAMILIES_WRITTEN = frozenset({"MEASUREMENT"})
V3_FAMILIES_NAMED = frozenset({"MEASUREMENT", "POLICY", "OPERATIONAL_RECORD"})
V3_QUALITIES = frozenset({"GOOD", "SUSPECT", "UNAVAILABLE"})

_IDENTIFIER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?")
_UNIT = re.compile(r"[A-Za-z%][A-Za-z0-9%/]{0,15}")
_DIGEST = re.compile(r"[0-9a-f]{64}")
_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?")
_MEMBER = re.compile(r"[A-Z][A-Z0-9_]{0,63}")


# --- framing and identity -----------------------------------------------------


def length_delimited(fields: list[str] | tuple[str, ...]) -> bytes:
    """Each field as a 4-byte big-endian length and its UTF-8 bytes."""
    out = bytearray()
    for field in fields:
        if type(field) is not str:
            raise TypeError("every framed field is text")
        data = field.encode("utf-8")
        out += struct.pack(">I", len(data))
        out += data
    return bytes(out)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_sha256(text: str) -> str:
    """SHA-256 over the UTF-8 bytes of a canonical text."""
    return sha256_hex(text.encode("utf-8"))


def v3_message_id(
    *,
    site_id: str,
    gateway_id: str,
    source_id: str,
    sequence_epoch: str,
    sequence: int,
) -> str:
    if type(sequence) is not int or sequence < 1 or sequence > MAX_SEQUENCE:
        raise ValueError(f"sequence {sequence!r} is outside 1..{MAX_SEQUENCE}")
    return sha256_hex(
        length_delimited(
            [
                MESSAGE_ID_V3_DOMAIN,
                site_id,
                gateway_id,
                source_id,
                sequence_epoch,
                str(sequence),
            ]
        )
    )


def is_canonical_decimal(text: str) -> bool:
    return bool(_DECIMAL.fullmatch(text)) and text != "-0"


def instant_text(moment: datetime) -> str:
    if moment.tzinfo is None:
        raise ValueError("an instant without a zone is ambiguous")
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- record -------------------------------------------------------------------


@dataclass(frozen=True)
class SourceEnvelopeV3:
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
    measurement: str
    value: str | None
    unit: str
    quality: str
    unavailable_reason: str | None

    def __post_init__(self) -> None:
        _validate(self)


def _ident(value: object, field: str) -> str:
    if type(value) is not str:
        raise EnvelopeRejected("WRONG_TYPE", field, "an identifier is text")
    if not _IDENTIFIER.fullmatch(value):
        raise EnvelopeRejected("INVALID_IDENTITY", field, f"{value!r} is not an identifier")
    return value


def _instant(value: object, field: str) -> datetime:
    if type(value) is not str:
        raise EnvelopeRejected("WRONG_TYPE", field, "an instant is text")
    if not _INSTANT.fullmatch(value):
        raise EnvelopeRejected(
            "INVALID_TIMING", field, f"{value!r} is not a UTC instant YYYY-MM-DDTHH:MM:SSZ"
        )
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise EnvelopeRejected("INVALID_TIMING", field, f"{value!r} is not a calendar instant") from error


def _int(value: object, field: str, floor: int, ceiling: int) -> int:
    if type(value) is not int:
        raise EnvelopeRejected("WRONG_TYPE", field, "a whole number is wanted")
    if value < floor or value > ceiling:
        raise EnvelopeRejected("INVALID_IDENTITY", field, f"{value} is outside {floor}..{ceiling}")
    return value


def _validate(e: SourceEnvelopeV3) -> None:
    for field in (
        "site_id",
        "gateway_id",
        "source_id",
        "device_id",
        "signal_id",
        "binding_set_id",
        "sequence_epoch",
    ):
        _ident(getattr(e, field), field)
    _int(e.sequence, "message.sequence", 1, MAX_SEQUENCE)
    _int(e.binding_version, "mapping.version", 1, MAX_SEQUENCE)
    if type(e.message_id) is not str or not _DIGEST.fullmatch(e.message_id):
        raise EnvelopeRejected("INVALID_IDENTITY", "message.message_id", "not a SHA-256 hex digest")
    expected = v3_message_id(
        site_id=e.site_id,
        gateway_id=e.gateway_id,
        source_id=e.source_id,
        sequence_epoch=e.sequence_epoch,
        sequence=e.sequence,
    )
    if e.message_id != expected:
        raise EnvelopeRejected(
            "INVALID_IDENTITY",
            "message.message_id",
            "does not match the length-delimited identity of this envelope",
        )
    source = _instant(e.source_time, "timing.source_time")
    published = _instant(e.published_at, "timing.published_at")
    if published < source:
        raise EnvelopeRejected(
            "INVALID_TIMING", "timing.published_at", "published before the source time"
        )
    if e.family not in V3_FAMILIES_NAMED:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.family", f"{e.family!r} is not a family")
    if e.family not in V3_FAMILIES_WRITTEN:
        raise EnvelopeRejected(
            "SCHEMA_UNSUPPORTED",
            "payload.family",
            f"{e.family} has no versioned record_detail contract in V3 yet",
        )
    if e.measurement not in ENVELOPE_MEASUREMENTS:
        raise EnvelopeRejected(
            "INVALID_PAYLOAD", "payload.measurement", f"{e.measurement!r} is not a measurement"
        )
    if type(e.unit) is not str or not _UNIT.fullmatch(e.unit):
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.unit", f"{e.unit!r} is not a unit")
    if e.quality not in V3_QUALITIES:
        raise EnvelopeRejected("INVALID_PAYLOAD", "payload.quality", f"{e.quality!r} is not a quality")
    if e.quality == "UNAVAILABLE":
        if e.value is not None:
            raise EnvelopeRejected("INVALID_PAYLOAD", "payload.value", "an unavailable reading has no value")
        if e.unavailable_reason not in ENVELOPE_UNAVAILABLE_REASONS:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.unavailable_reason",
                f"{e.unavailable_reason!r} is not an unavailable reason",
            )
    else:
        if e.unavailable_reason is not None:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD", "payload.unavailable_reason", "only an unavailable reading has a reason"
            )
        if type(e.value) is not str:
            raise EnvelopeRejected("WRONG_TYPE", "payload.value", "a value is text")
        if e.unit == DISCRETE_UNIT:
            if not _MEMBER.fullmatch(e.value):
                raise EnvelopeRejected(
                    "INVALID_PAYLOAD", "payload.value", f"{e.value!r} is not a discrete member"
                )
        elif not is_canonical_decimal(e.value):
            raise EnvelopeRejected(
                "NOT_CANONICAL", "payload.value", f"{e.value!r} is not a canonical decimal string"
            )
    if e.measurement == "INTERVAL_MEAN":
        if e.interval_start is None or e.interval_end is None:
            raise EnvelopeRejected("INVALID_TIMING", "payload.interval_start", "an interval mean states its interval")
        start = _instant(e.interval_start, "payload.interval_start")
        _instant(e.interval_end, "payload.interval_end")
        if e.interval_end != e.source_time:
            raise EnvelopeRejected("INVALID_TIMING", "payload.interval_end", "an interval ends at its source time")
        if start >= source:
            raise EnvelopeRejected("INVALID_TIMING", "payload.interval_start", "an interval has positive length")
    elif e.interval_start is not None or e.interval_end is not None:
        raise EnvelopeRejected(
            "INVALID_TIMING", "payload.interval_start", "a state-at-instant reading has no interval"
        )


# --- canonical text -----------------------------------------------------------


def envelope_v3_document(e: SourceEnvelopeV3) -> dict[str, Any]:
    return {
        "schema": {"id": SOURCE_ENVELOPE_V3_SCHEMA_ID, "version": SOURCE_ENVELOPE_V3_SCHEMA_VERSION},
        "message": {
            "message_id": e.message_id,
            "sequence_epoch": e.sequence_epoch,
            "sequence": e.sequence,
        },
        "source": {
            "site_id": e.site_id,
            "gateway_id": e.gateway_id,
            "source_id": e.source_id,
            "device_id": e.device_id,
            "signal_id": e.signal_id,
        },
        "mapping": {"binding_set_id": e.binding_set_id, "version": e.binding_version},
        "timing": {
            "source_time": e.source_time,
            "published_at": e.published_at,
            "interval_start": e.interval_start,
            "interval_end": e.interval_end,
        },
        "payload": {
            "family": e.family,
            "measurement": e.measurement,
            "value": e.value,
            "unit": e.unit,
            "quality": e.quality,
            "unavailable_reason": e.unavailable_reason,
        },
    }


def canonical_envelope_v3_text(e: SourceEnvelopeV3) -> str:
    return canonical_json(envelope_v3_document(e))


_KEYS = {
    "": frozenset({"schema", "message", "source", "mapping", "timing", "payload"}),
    "schema": frozenset({"id", "version"}),
    "message": frozenset({"message_id", "sequence_epoch", "sequence"}),
    "source": frozenset({"site_id", "gateway_id", "source_id", "device_id", "signal_id"}),
    "mapping": frozenset({"binding_set_id", "version"}),
    "timing": frozenset({"source_time", "published_at", "interval_start", "interval_end"}),
    "payload": frozenset({"family", "measurement", "value", "unit", "quality", "unavailable_reason"}),
}


def _exact(document: object, where: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise EnvelopeRejected("NOT_AN_ENVELOPE" if not where else "WRONG_TYPE", where or "envelope", "an object is wanted")
    wanted = _KEYS[where]
    for key in sorted(document):
        if key not in wanted:
            path = f"{where}.{key}" if where else key
            raise EnvelopeRejected("UNKNOWN_FIELD", path, "not a field of a V3 envelope")
    for key in sorted(wanted):
        if key not in document:
            path = f"{where}.{key}" if where else key
            raise EnvelopeRejected("MISSING_FIELD", path, "required (null when absent)")
    return document


def parse_source_envelope_v3(document: object) -> SourceEnvelopeV3:
    top = _exact(document, "")
    schema = _exact(top["schema"], "schema")
    if schema["id"] != SOURCE_ENVELOPE_V3_SCHEMA_ID or schema["version"] != SOURCE_ENVELOPE_V3_SCHEMA_VERSION or type(schema["version"]) is not int:
        raise EnvelopeRejected(
            "SCHEMA_UNSUPPORTED", "schema", f"{schema['id']!r} v{schema['version']!r} is not a V3 envelope"
        )
    message = _exact(top["message"], "message")
    source = _exact(top["source"], "source")
    mapping = _exact(top["mapping"], "mapping")
    timing = _exact(top["timing"], "timing")
    payload = _exact(top["payload"], "payload")
    return SourceEnvelopeV3(
        message_id=message["message_id"],
        sequence_epoch=message["sequence_epoch"],
        sequence=message["sequence"],
        site_id=source["site_id"],
        gateway_id=source["gateway_id"],
        source_id=source["source_id"],
        device_id=source["device_id"],
        signal_id=source["signal_id"],
        binding_set_id=mapping["binding_set_id"],
        binding_version=mapping["version"],
        source_time=timing["source_time"],
        published_at=timing["published_at"],
        interval_start=timing["interval_start"],
        interval_end=timing["interval_end"],
        family=payload["family"],
        measurement=payload["measurement"],
        value=payload["value"],
        unit=payload["unit"],
        quality=payload["quality"],
        unavailable_reason=payload["unavailable_reason"],
    )


def parse_canonical_envelope_v3_text(text: object) -> SourceEnvelopeV3:
    """Stored bytes back as the envelope; refuses anything not already canonical."""
    envelope = parse_source_envelope_v3(load_canonical_json(text))
    if canonical_envelope_v3_text(envelope) != text:
        raise EnvelopeRejected(
            "NOT_CANONICAL", "envelope", "the text parses and is not its own canonical text"
        )
    return envelope
