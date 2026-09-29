"""The canonical source envelope: the one simulator payload the product may ingest.

v4 section 3.1's one-crossing rule, as a record. Everything a simulated gateway
publishes toward AssetOps is a `SourceEnvelope` and nothing else is: not a
`DeviceObservation`, not a `LabProjection`, not a trajectory, not a controller
intent, and not any mapping somebody assembled from one of those. This module is
the schema and its strict parser, and it is dependency-neutral because both sides
speak it - the simulator's gateway constructs envelopes, and a later ingestion
(T027) will parse exactly the canonical text this module writes.

## Its version is its own

`SOURCE_ENVELOPE_SCHEMA_VERSION` is independent of `EXECUTION_CONTRACT_VERSION`.
The execution contract says what a frozen Draft MEANS when it runs; this says
what a published message LOOKS LIKE on the wire. A kernel change that moves the
execution contract does not change one byte an envelope carries, and a new
envelope field does not change what any frozen Draft means - so neither number
moves the other, and a reader comparing two envelopes compares this number only.

**Compatibility is equality, and a refusal is the answer to anything else.** The
parser accepts exactly schema version 1. A document stating another version is
refused with `SCHEMA_UNSUPPORTED` and is never read "as close enough": a field
that means one thing at version 2 and is read under version 1's meaning is the
silent reinterpretation this repository keeps paying for.

## What an envelope can carry, and why that is the privacy argument

The privacy argument is the shape, the same argument `FrozenWorldInputs` makes.
Every level has an exact key set and an unknown key is refused, so a private
field - a true value, a cause, an event label, an oracle, an intent - has nowhere
to arrive. There is no free-text field at all: identities are validated
identifiers, the payload's categories are closed vocabularies, the value is a
canonical exact decimal, and the times are UTC instants. A sentence explaining
WHY a reading is missing is the Lab's business and carries the scenario's event
names, which is exactly why no envelope has a place to put one.

## Identity, and why the message id is derived rather than assigned

`message_id` is a BLAKE2b-256 digest over the publication's identity - Site,
gateway, source, device, signal and source time - and the parser recomputes it.
So a retry of the same publication carries the same id by construction, two
different publications cannot share one, and an envelope whose id does not match
its own identity fields is refused as `INVALID_IDENTITY` rather than trusted.
Content is deliberately NOT in the id: "same id, different content" has to be
expressible, because it is the conflict the stage refuses rather than overwrites.

## Stock versus interval, kept apart on the wire

`measurement` says which of the execution contract's two reportable reading
classes the value is. `STATE_AT_INSTANT` describes the world at `source_time` and
carries no interval. `INTERVAL_MEAN` summarises the span that ENDED at
`source_time`, and carries that span as `interval_start`/`interval_end` so a
consumer does not have to know the run's timestep to know what the number is a
mean over. `interval_end` equals `source_time`, always: that is
`interval-signal-describes-the-preceding-interval` written into the schema.

## Times, and the one that is absent

`source_time` is the device's sample (or interval end) instant. `published_at`
is the gateway's publication instant and is never earlier. `received_at` belongs
to ingestion (`.ai/ARCHITECTURE.md` Evidence Loop Boundaries) and is not a field
here; a document carrying one is refused as an unknown field, by name.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

from assetops_contracts.identity import identity_digest
from assetops_contracts.observation import exact_decimal_text

SOURCE_ENVELOPE_SCHEMA_ID = "assetops.source-envelope"

#: Independent of the execution contract's version; see the module docstring.
SOURCE_ENVELOPE_SCHEMA_VERSION = 1

#: The two things a published value can be. They are the execution contract's
#: `STATE_SIGNAL` and `INTERVAL_SIGNAL` in wire terms, and the gateway's mapping
#: is what says which one a signal publishes.
ENVELOPE_MEASUREMENTS = frozenset({"STATE_AT_INSTANT", "INTERVAL_MEAN"})

#: Whether an envelope carries a value. Two, deliberately: `STALE` is something a
#: CONSUMER concludes about an old reading, and a device does not publish it.
ENVELOPE_QUALITIES = frozenset({"GOOD", "UNAVAILABLE"})

#: Why a device that WAS publishing sent no value. Closed, so no sentence can be
#: smuggled through it. A sample that was never taken - a reporting path forced
#: down, a publication lost - produces no envelope at all rather than one of
#: these, because nothing was published.
ENVELOPE_UNAVAILABLE_REASONS = frozenset(
    {"NO_COMPLETED_INTERVAL", "NO_MEASUREMENT"}
)

#: Why a document was refused. One kind per fact a caller can act on.
ENVELOPE_REJECTION_KINDS = frozenset(
    {
        "NOT_AN_ENVELOPE",
        "MALFORMED_TEXT",
        "NOT_CANONICAL",
        "UNKNOWN_FIELD",
        "MISSING_FIELD",
        "WRONG_TYPE",
        "SCHEMA_UNSUPPORTED",
        "INVALID_IDENTITY",
        "INVALID_TIMING",
        "INVALID_PAYLOAD",
        "MAPPING_INCOMPATIBLE",
        "UNIT_INCOMPATIBLE",
    }
)

#: The domain every message id is derived under, kept apart from every other
#: identity this product computes.
MESSAGE_ID_DOMAIN = "source-envelope-message-v1"

_IDENTIFIER = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?$")
_UNIT = re.compile(r"^[A-Za-z%][A-Za-z0-9%/]{0,15}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_INSTANT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_EXACT = re.compile(r"^-?\d+(?:\.\d+)?$|^-?\d+/\d+$")


class EnvelopeRejected(ValueError):
    """A document or record is not a canonical source envelope.

    `kind` is one of `ENVELOPE_REJECTION_KINDS`; `field` is the dotted path the
    refusal is about, so a negative corpus can assert WHERE it was refused and
    not merely that it was.
    """

    def __init__(self, kind: str, field: str, detail: str) -> None:
        if kind not in ENVELOPE_REJECTION_KINDS:
            raise ValueError(f"{kind!r} is not an envelope rejection kind.")
        self.kind = kind
        self.field = field
        self.detail = detail
        super().__init__(f"{kind} at {field}: {detail}")


def _identifier(value: object, field: str) -> str:
    if type(value) is not str:
        raise EnvelopeRejected(
            "WRONG_TYPE", field, f"an identifier is text, not {type(value).__name__}"
        )
    if not _IDENTIFIER.match(value):
        raise EnvelopeRejected(
            "INVALID_IDENTITY",
            field,
            f"{value!r} is not an identifier: letters, digits, '.', '_' and '-', "
            "starting and ending with a letter or digit, at most 128 characters",
        )
    return value


def _instant(value: object, field: str) -> datetime:
    if type(value) is not str:
        raise EnvelopeRejected(
            "WRONG_TYPE", field, f"an instant is text, not {type(value).__name__}"
        )
    if not _INSTANT.match(value):
        raise EnvelopeRejected(
            "INVALID_TIMING",
            field,
            f"{value!r} is not a UTC instant written YYYY-MM-DDTHH:MM:SSZ",
        )
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as error:
        raise EnvelopeRejected(
            "INVALID_TIMING", field, f"{value!r} is not a calendar instant"
        ) from error


def _whole(value: object, field: str, floor: int) -> int:
    if type(value) is not int:
        raise EnvelopeRejected(
            "WRONG_TYPE",
            field,
            f"a whole number is wanted and this is {type(value).__name__} "
            f"({value!r})",
        )
    if value < floor:
        raise EnvelopeRejected(
            "INVALID_IDENTITY", field, f"{value} is below {floor}"
        )
    return value


def instant_text(moment: datetime) -> str:
    """One UTC instant in the only spelling an envelope accepts."""
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def envelope_message_id(
    *,
    site_id: str,
    gateway_id: str,
    source_id: str,
    device_id: str,
    signal_id: str,
    source_time: str,
) -> str:
    """The identity of one publication, independent of what it carried."""
    return identity_digest(
        [
            MESSAGE_ID_DOMAIN,
            site_id,
            gateway_id,
            source_id,
            device_id,
            signal_id,
            source_time,
        ]
    )


@dataclass(frozen=True)
class SourceMappingEntry:
    """One allowlisted device signal: what it publishes, in what unit.

    The allowlist IS the list of these. An observation from a signal with no
    entry is not converted, so a new signal crosses the boundary only when
    somebody writes it down here - which is v4 section 11.2's "explicit
    mapping" rather than a gateway that forwards whatever arrives.
    """

    device_id: str
    signal_id: str
    measurement: str
    unit: str
    #: Whether this signal publishes a typed-unavailable envelope when it was
    #: sampled and had no value. False means such a sample publishes nothing.
    publishes_unavailable: bool

    def __post_init__(self) -> None:
        _identifier(self.device_id, "mapping.device_id")
        _identifier(self.signal_id, "mapping.signal_id")
        if self.measurement not in ENVELOPE_MEASUREMENTS:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "mapping.measurement",
                f"{self.measurement!r} is not one of {sorted(ENVELOPE_MEASUREMENTS)}",
            )
        if type(self.unit) is not str or not _UNIT.match(self.unit):
            raise EnvelopeRejected(
                "INVALID_PAYLOAD", "mapping.unit", f"{self.unit!r} is not a unit"
            )
        if type(self.publishes_unavailable) is not bool:
            raise EnvelopeRejected(
                "WRONG_TYPE",
                "mapping.publishes_unavailable",
                "whether a signal publishes unavailability is true or false",
            )

    @property
    def key(self) -> tuple[str, str]:
        return (self.device_id, self.signal_id)


@dataclass(frozen=True)
class SourceMappingSet:
    """A versioned gateway mapping: the allowlist and the publication latency.

    Frozen INTO every stage that uses it (see `source_stage`), so what a staged
    envelope meant is read from the stage and never from whatever the current
    mapping says. `publication_latency_seconds` is the gateway's declared,
    deterministic delay between a sample and its publication; buffering, outage
    and retry timing are T026A's and are not modelled here.
    """

    mapping_set_id: str
    mapping_version: int
    publication_latency_seconds: int
    entries: tuple[SourceMappingEntry, ...]

    def __post_init__(self) -> None:
        _identifier(self.mapping_set_id, "mapping.mapping_set_id")
        _whole(self.mapping_version, "mapping.mapping_version", 1)
        if type(self.publication_latency_seconds) is not int or (
            self.publication_latency_seconds < 0
        ):
            raise EnvelopeRejected(
                "INVALID_TIMING",
                "mapping.publication_latency_seconds",
                "a publication latency is a whole number of seconds, not negative",
            )
        seen: set[tuple[str, str]] = set()
        for entry in self.entries:
            if type(entry) is not SourceMappingEntry:
                raise EnvelopeRejected(
                    "WRONG_TYPE", "mapping.entries", "an entry is a SourceMappingEntry"
                )
            if entry.key in seen:
                raise EnvelopeRejected(
                    "MAPPING_INCOMPATIBLE",
                    "mapping.entries",
                    f"{entry.key} is mapped twice, so nothing says which applies",
                )
            seen.add(entry.key)

    def entry(self, device_id: str, signal_id: str) -> SourceMappingEntry | None:
        for item in self.entries:
            if item.key == (device_id, signal_id):
                return item
        return None


def mapping_set_document(mapping: SourceMappingSet) -> dict[str, Any]:
    return {
        "mapping_set_id": mapping.mapping_set_id,
        "mapping_version": mapping.mapping_version,
        "publication_latency_seconds": mapping.publication_latency_seconds,
        "entries": [
            {
                "device_id": entry.device_id,
                "signal_id": entry.signal_id,
                "measurement": entry.measurement,
                "unit": entry.unit,
                "publishes_unavailable": entry.publishes_unavailable,
            }
            for entry in mapping.entries
        ],
    }


def _exact_keys(
    document: object, expected: frozenset[str], field: str
) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise EnvelopeRejected(
            "NOT_AN_ENVELOPE" if field == "envelope" else "WRONG_TYPE",
            field,
            f"an object is wanted and this is {type(document).__name__}",
        )
    for key in document:
        if type(key) is not str:
            raise EnvelopeRejected("WRONG_TYPE", field, f"key {key!r} is not text")
    unknown = sorted(set(document) - expected)
    if unknown:
        raise EnvelopeRejected(
            "UNKNOWN_FIELD",
            f"{field}.{unknown[0]}",
            f"{field} carries {unknown}, which the schema does not declare. "
            "Nothing is accepted beside the declared fields.",
        )
    missing = sorted(expected - set(document))
    if missing:
        raise EnvelopeRejected(
            "MISSING_FIELD",
            f"{field}.{missing[0]}",
            f"{field} does not carry {missing}",
        )
    return document


_MAPPING_SET_KEYS = frozenset(
    {"mapping_set_id", "mapping_version", "publication_latency_seconds", "entries"}
)
_MAPPING_ENTRY_KEYS = frozenset(
    {"device_id", "signal_id", "measurement", "unit", "publishes_unavailable"}
)


def parse_mapping_set(document: object) -> SourceMappingSet:
    """A persisted mapping set, read strictly."""
    fields = _exact_keys(document, _MAPPING_SET_KEYS, "mapping")
    entries = fields["entries"]
    if not isinstance(entries, list):
        raise EnvelopeRejected("WRONG_TYPE", "mapping.entries", "a list is wanted")
    parsed = []
    for index, row in enumerate(entries):
        entry = _exact_keys(row, _MAPPING_ENTRY_KEYS, f"mapping.entries[{index}]")
        parsed.append(
            SourceMappingEntry(
                device_id=entry["device_id"],
                signal_id=entry["signal_id"],
                measurement=entry["measurement"],
                unit=entry["unit"],
                publishes_unavailable=entry["publishes_unavailable"],
            )
        )
    return SourceMappingSet(
        mapping_set_id=fields["mapping_set_id"],
        mapping_version=fields["mapping_version"],
        publication_latency_seconds=fields["publication_latency_seconds"],
        entries=tuple(parsed),
    )


@dataclass(frozen=True)
class SourceEnvelope:
    """One canonical published message. Invalid ones cannot be constructed.

    Every check the parser makes is made here, in `__post_init__`, so there is
    no way to hold a `SourceEnvelope` that the parser would refuse - including
    one a gateway built directly rather than parsed.
    """

    message_id: str
    sequence: int
    site_id: str
    source_id: str
    gateway_id: str
    device_id: str
    signal_id: str
    mapping_set_id: str
    mapping_version: int
    source_time: str
    published_at: str
    measurement: str
    value: Fraction | None
    unit: str
    quality: str
    unavailable_reason: str | None
    interval_start: str | None
    interval_end: str | None
    schema_version: int = SOURCE_ENVELOPE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or (
            self.schema_version != SOURCE_ENVELOPE_SCHEMA_VERSION
        ):
            raise EnvelopeRejected(
                "SCHEMA_UNSUPPORTED",
                "schema.version",
                f"this build reads source envelope schema "
                f"{SOURCE_ENVELOPE_SCHEMA_VERSION} and nothing else; this one "
                f"states {self.schema_version!r}. It is refused rather than read "
                "under a meaning it was not written with.",
            )
        for field in ("site_id", "source_id", "gateway_id", "device_id", "signal_id"):
            _identifier(getattr(self, field), f"source.{field}")
        _identifier(self.mapping_set_id, "mapping.mapping_set_id")
        _whole(self.mapping_version, "mapping.mapping_version", 1)
        _whole(self.sequence, "message.sequence", 1)
        if type(self.message_id) is not str or not _DIGEST.match(self.message_id):
            raise EnvelopeRejected(
                "INVALID_IDENTITY",
                "message.message_id",
                "a message id is 64 lowercase hexadecimal characters",
            )

        sampled = _instant(self.source_time, "timing.source_time")
        published = _instant(self.published_at, "timing.published_at")
        if published < sampled:
            raise EnvelopeRejected(
                "INVALID_TIMING",
                "timing.published_at",
                f"published at {self.published_at}, before the sample it carries "
                f"was taken at {self.source_time}",
            )

        expected = envelope_message_id(
            site_id=self.site_id,
            gateway_id=self.gateway_id,
            source_id=self.source_id,
            device_id=self.device_id,
            signal_id=self.signal_id,
            source_time=self.source_time,
        )
        if self.message_id != expected:
            raise EnvelopeRejected(
                "INVALID_IDENTITY",
                "message.message_id",
                "the message id is not the identity of this publication: it is "
                "derived from the site, gateway, source, device, signal and "
                "source time, and does not match them",
            )

        self._check_payload(sampled)

    def _check_payload(self, sampled: datetime) -> None:
        if self.measurement not in ENVELOPE_MEASUREMENTS:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.measurement",
                f"{self.measurement!r} is not one of {sorted(ENVELOPE_MEASUREMENTS)}",
            )
        if type(self.unit) is not str or not _UNIT.match(self.unit):
            raise EnvelopeRejected(
                "INVALID_PAYLOAD", "payload.unit", f"{self.unit!r} is not a unit"
            )
        if self.quality not in ENVELOPE_QUALITIES:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.quality",
                f"{self.quality!r} is not one of {sorted(ENVELOPE_QUALITIES)}",
            )
        if self.value is not None and type(self.value) is not Fraction:
            raise EnvelopeRejected(
                "WRONG_TYPE",
                "payload.value",
                "a value is exact; a binary float is never carried",
            )
        if (self.quality == "GOOD") != (self.value is not None):
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.value",
                f"quality {self.quality} with "
                f"{'a' if self.value is not None else 'no'} value: a GOOD "
                "envelope carries a value and an UNAVAILABLE one carries none, "
                "so nothing is ever invented to fill a missing reading",
            )
        if (self.quality == "UNAVAILABLE") != (self.unavailable_reason is not None):
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.unavailable_reason",
                "an UNAVAILABLE envelope names why and a GOOD one names nothing",
            )
        if (
            self.unavailable_reason is not None
            and self.unavailable_reason not in ENVELOPE_UNAVAILABLE_REASONS
        ):
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.unavailable_reason",
                f"{self.unavailable_reason!r} is not one of "
                f"{sorted(ENVELOPE_UNAVAILABLE_REASONS)}",
            )

        if self.measurement == "STATE_AT_INSTANT":
            if self.interval_start is not None or self.interval_end is not None:
                raise EnvelopeRejected(
                    "INVALID_TIMING",
                    "payload.interval_start",
                    "a state reading describes one instant and summarises no "
                    "interval",
                )
            if self.unavailable_reason == "NO_COMPLETED_INTERVAL":
                raise EnvelopeRejected(
                    "INVALID_PAYLOAD",
                    "payload.unavailable_reason",
                    "a state reading does not wait for an interval to complete",
                )
            return

        # INTERVAL_MEAN.
        if self.unavailable_reason == "NO_COMPLETED_INTERVAL":
            if self.interval_start is not None or self.interval_end is not None:
                raise EnvelopeRejected(
                    "INVALID_TIMING",
                    "payload.interval_start",
                    "no interval had completed, so there is no span to name",
                )
            return
        if self.interval_start is None or self.interval_end is None:
            raise EnvelopeRejected(
                "INVALID_TIMING",
                "payload.interval_start",
                "an interval measurement names the span it summarises",
            )
        start = _instant(self.interval_start, "payload.interval_start")
        end = _instant(self.interval_end, "payload.interval_end")
        if end != sampled:
            raise EnvelopeRejected(
                "INVALID_TIMING",
                "payload.interval_end",
                f"an interval measurement at {self.source_time} summarises the "
                f"span that ENDED then, and this one names {self.interval_end}",
            )
        if not start < end:
            raise EnvelopeRejected(
                "INVALID_TIMING",
                "payload.interval_start",
                "an interval runs forwards and has non-zero length",
            )


def envelope_document(envelope: SourceEnvelope) -> dict[str, Any]:
    """One envelope as its canonical nested document."""
    return {
        "schema": {
            "id": SOURCE_ENVELOPE_SCHEMA_ID,
            "version": envelope.schema_version,
        },
        "message": {
            "message_id": envelope.message_id,
            "sequence": envelope.sequence,
        },
        "source": {
            "site_id": envelope.site_id,
            "source_id": envelope.source_id,
            "gateway_id": envelope.gateway_id,
            "device_id": envelope.device_id,
            "signal_id": envelope.signal_id,
        },
        "mapping": {
            "mapping_set_id": envelope.mapping_set_id,
            "mapping_version": envelope.mapping_version,
        },
        "timing": {
            "source_time": envelope.source_time,
            "published_at": envelope.published_at,
        },
        "payload": {
            "measurement": envelope.measurement,
            "value": (
                None if envelope.value is None else exact_decimal_text(envelope.value)
            ),
            "unit": envelope.unit,
            "quality": envelope.quality,
            "unavailable_reason": envelope.unavailable_reason,
            "interval_start": envelope.interval_start,
            "interval_end": envelope.interval_end,
        },
    }


def canonical_json(document: object) -> str:
    """The one canonical text of a JSON document: sorted keys, no whitespace."""
    return json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def canonical_envelope_json(envelope: SourceEnvelope) -> str:
    """The exact bytes (as text) a stage persists and an inspector shows."""
    return canonical_json(envelope_document(envelope))


_TOP_KEYS = frozenset({"schema", "message", "source", "mapping", "timing", "payload"})
_SCHEMA_KEYS = frozenset({"id", "version"})
_MESSAGE_KEYS = frozenset({"message_id", "sequence"})
_SOURCE_KEYS = frozenset(
    {"site_id", "source_id", "gateway_id", "device_id", "signal_id"}
)
_MAPPING_KEYS = frozenset({"mapping_set_id", "mapping_version"})
_TIMING_KEYS = frozenset({"source_time", "published_at"})
_PAYLOAD_KEYS = frozenset(
    {
        "measurement",
        "value",
        "unit",
        "quality",
        "unavailable_reason",
        "interval_start",
        "interval_end",
    }
)


def _optional_text(value: object, field: str) -> str | None:
    if value is None or type(value) is str:
        return value
    raise EnvelopeRejected(
        "WRONG_TYPE", field, f"text or null is wanted, not {type(value).__name__}"
    )


def _exact_value(value: object) -> Fraction | None:
    if value is None:
        return None
    if type(value) is not str:
        raise EnvelopeRejected(
            "WRONG_TYPE",
            "payload.value",
            f"a value is exact decimal text, not {type(value).__name__}; a "
            "binary number cannot say what was published exactly",
        )
    if not _EXACT.match(value):
        raise EnvelopeRejected(
            "INVALID_PAYLOAD", "payload.value", f"{value!r} is not an exact number"
        )
    parsed = Fraction(value)
    if exact_decimal_text(parsed) != value:
        raise EnvelopeRejected(
            "NOT_CANONICAL",
            "payload.value",
            f"{value!r} is written as {exact_decimal_text(parsed)!r} canonically",
        )
    return parsed


def parse_source_envelope(document: object) -> SourceEnvelope:
    """One envelope document, read strictly.

    Exact key sets at every level, exact types, canonical exact values, and every
    record-level rule `SourceEnvelope` enforces. A Python object that is not a
    plain mapping - a `DeviceObservation`, a `LabProjection`, anything with the
    right attribute names - is `NOT_AN_ENVELOPE`: an envelope is data, not an
    object graph that happens to look like one.
    """
    top = _exact_keys(document, _TOP_KEYS, "envelope")
    schema = _exact_keys(top["schema"], _SCHEMA_KEYS, "schema")
    if schema["id"] != SOURCE_ENVELOPE_SCHEMA_ID:
        raise EnvelopeRejected(
            "SCHEMA_UNSUPPORTED",
            "schema.id",
            f"{schema['id']!r} is not {SOURCE_ENVELOPE_SCHEMA_ID!r}",
        )
    if type(schema["version"]) is not int:
        raise EnvelopeRejected(
            "WRONG_TYPE", "schema.version", "a schema version is a whole number"
        )
    message = _exact_keys(top["message"], _MESSAGE_KEYS, "message")
    source = _exact_keys(top["source"], _SOURCE_KEYS, "source")
    mapping = _exact_keys(top["mapping"], _MAPPING_KEYS, "mapping")
    timing = _exact_keys(top["timing"], _TIMING_KEYS, "timing")
    payload = _exact_keys(top["payload"], _PAYLOAD_KEYS, "payload")
    return SourceEnvelope(
        schema_version=schema["version"],
        message_id=message["message_id"],
        sequence=message["sequence"],
        site_id=source["site_id"],
        source_id=source["source_id"],
        gateway_id=source["gateway_id"],
        device_id=source["device_id"],
        signal_id=source["signal_id"],
        mapping_set_id=mapping["mapping_set_id"],
        mapping_version=mapping["mapping_version"],
        source_time=timing["source_time"],
        published_at=timing["published_at"],
        measurement=payload["measurement"],
        value=_exact_value(payload["value"]),
        unit=payload["unit"],
        quality=payload["quality"],
        unavailable_reason=_optional_text(
            payload["unavailable_reason"], "payload.unavailable_reason"
        ),
        interval_start=_optional_text(
            payload["interval_start"], "payload.interval_start"
        ),
        interval_end=_optional_text(payload["interval_end"], "payload.interval_end"),
    )


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise EnvelopeRejected(
                "MALFORMED_TEXT", key, "a key appears twice in one object"
            )
        seen[key] = value
    return seen


def _no_float(text: str) -> Any:
    raise EnvelopeRejected(
        "WRONG_TYPE",
        "envelope",
        f"{text} is a binary number, and nothing in an envelope is one",
    )


def _no_constant(text: str) -> Any:
    raise EnvelopeRejected("MALFORMED_TEXT", "envelope", f"{text} is not JSON")


def load_canonical_json(text: object) -> Any:
    """Canonical JSON text as a document: no duplicate keys, no floats, no NaN."""
    if type(text) is not str:
        raise EnvelopeRejected(
            "MALFORMED_TEXT", "envelope", "canonical content is text"
        )
    try:
        return json.loads(
            text,
            object_pairs_hook=_no_duplicate_keys,
            parse_float=_no_float,
            parse_constant=_no_constant,
        )
    except json.JSONDecodeError as error:
        raise EnvelopeRejected(
            "MALFORMED_TEXT", "envelope", f"not JSON: {error.msg}"
        ) from error


def parse_canonical_envelope_json(text: object) -> SourceEnvelope:
    """The exact persisted text of one envelope, back as the envelope.

    Refuses anything that is not ALREADY canonical: the same envelope written
    with other whitespace, key order or number spelling is a different byte
    string, and a stage whose persisted bytes are not the bytes it would write
    has been edited by something other than this contract.
    """
    envelope = parse_source_envelope(load_canonical_json(text))
    if canonical_envelope_json(envelope) != text:
        raise EnvelopeRejected(
            "NOT_CANONICAL",
            "envelope",
            "the text parses, and is not the canonical text of what it parses to",
        )
    return envelope


def check_against_mapping(
    envelope: SourceEnvelope, mapping: SourceMappingSet
) -> SourceMappingEntry:
    """Whether an envelope is what this frozen mapping would publish.

    The allowlist, the mapping identity and version, the measurement class, the
    unit, and whether the signal publishes unavailability at all. Every one is a
    refusal rather than a coercion: a litre value arriving as millilitres is not
    converted here, it is refused, because a converter at this boundary is a
    second mapping nobody versioned.
    """
    if (envelope.mapping_set_id, envelope.mapping_version) != (
        mapping.mapping_set_id,
        mapping.mapping_version,
    ):
        raise EnvelopeRejected(
            "MAPPING_INCOMPATIBLE",
            "mapping",
            f"the envelope was mapped by {envelope.mapping_set_id} "
            f"v{envelope.mapping_version} and this stage froze "
            f"{mapping.mapping_set_id} v{mapping.mapping_version}",
        )
    entry = mapping.entry(envelope.device_id, envelope.signal_id)
    if entry is None:
        raise EnvelopeRejected(
            "MAPPING_INCOMPATIBLE",
            "source.signal_id",
            f"{envelope.device_id}/{envelope.signal_id} is not on the allowlist "
            f"of {mapping.mapping_set_id} v{mapping.mapping_version}",
        )
    if envelope.measurement != entry.measurement:
        raise EnvelopeRejected(
            "MAPPING_INCOMPATIBLE",
            "payload.measurement",
            f"the mapping publishes {entry.measurement} for this signal and the "
            f"envelope says {envelope.measurement}",
        )
    if envelope.unit != entry.unit:
        raise EnvelopeRejected(
            "UNIT_INCOMPATIBLE",
            "payload.unit",
            f"the mapping publishes this signal in {entry.unit!r} and the "
            f"envelope carries {envelope.unit!r}; nothing converts at this "
            "boundary",
        )
    if envelope.quality == "UNAVAILABLE" and not entry.publishes_unavailable:
        raise EnvelopeRejected(
            "MAPPING_INCOMPATIBLE",
            "payload.quality",
            "this signal's mapping does not publish unavailability",
        )
    return entry
