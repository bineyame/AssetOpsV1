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
parser reads a document under exactly the schema version it states, 1 or 2 (T026
added 2 and kept 1's reader unchanged). Any other version is refused with
`SCHEMA_UNSUPPORTED` and is never read "as close enough": a field that means one
thing at one version and is read under another's meaning is the silent
reinterpretation this repository keeps paying for.

## Schema 2 (T026): three payload families

A schema-2 payload states its `family`. `MEASUREMENT` is telemetry as before,
and a reading in the discrete unit (`state`) carries its member as text - a
generator's `RUNNING` - checked against the members its mapping declares; it is
never a number and never noised. `POLICY` says which control value was in force
over which effective interval, at which Foundation version. `OPERATIONAL_RECORD`
says an operator commanded an override: occurrence (`source_time`), effective
interval and actor. Each family has its own exact key set.

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

from assetops_contracts.control import DISCRETE_UNIT
from assetops_contracts.identity import identity_digest
from assetops_contracts.observation import exact_decimal_text

SOURCE_ENVELOPE_SCHEMA_ID = "assetops.source-envelope"

#: Independent of the execution contract's version; see the module docstring.
#:
#: T026: the newest schema this build WRITES. Version 2 adds the payload
#: `family` (a measurement, a policy record or an operational record) and lets
#: a measurement in the discrete unit carry its member as text. Version 1 is
#: still READ, exactly as it was written: a stage staged under it parses and
#: verifies unchanged (`READABLE_ENVELOPE_SCHEMA_VERSIONS`). Which version a
#: stage carries is its frozen mapping's `envelope_schema_version`, never this
#: constant, so a run staged under the fuel-only mapping keeps publishing
#: schema 1.
SOURCE_ENVELOPE_SCHEMA_VERSION = 2

#: Every envelope schema this build reads. Equality per document still holds:
#: a document is read under the version it states and no other.
READABLE_ENVELOPE_SCHEMA_VERSIONS = frozenset({1, 2})

#: The two things a published value can be. They are the execution contract's
#: `STATE_SIGNAL` and `INTERVAL_SIGNAL` in wire terms, and the gateway's mapping
#: is what says which one a signal publishes.
ENVELOPE_MEASUREMENTS = frozenset({"STATE_AT_INSTANT", "INTERVAL_MEAN"})

#: T026, schema 2. What a published payload IS. A measurement is telemetry; a
#: policy record says which control value was in force over which operating
#: time and on whose authority; an operational record says that something was
#: commanded. Records are not telemetry: they have no quality, no measurement
#: class and no cadence, and they are present or absent as whole messages.
ENVELOPE_FAMILIES = frozenset({"MEASUREMENT", "POLICY", "OPERATIONAL_RECORD"})

#: Where a policy record's value came from. Closed: the Foundation the run
#: froze is the one source this build publishes policy for. An override is an
#: operational record, not a second policy source.
POLICY_SOURCES = frozenset({"FOUNDATION"})

#: What an operational record records. T026 introduces the family narrowly -
#: an operator-commanded override - and T030 extends it (delivery, hand dip).
OPERATIONAL_RECORD_KINDS = frozenset({"OVERRIDE_COMMAND"})

#: Who an operational record says acted. Closed, so no name or sentence fits.
RECORD_ACTORS = frozenset({"OPERATOR"})

#: The unit a policy carrying an ordered member list is published in.
ORDER_UNIT = "order"

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

# Applied with `fullmatch` (T026, review R3): `$` matches before a final
# newline, so `match` accepted "fuel-level-sensor\n" as an identifier.
_IDENTIFIER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?")
_UNIT = re.compile(r"[A-Za-z%][A-Za-z0-9%/]{0,15}")
_DIGEST = re.compile(r"[0-9a-f]{64}")
_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_EXACT = re.compile(r"-?\d+(?:\.\d+)?|-?\d+/\d+")
#: A discrete member as published: `RUNNING`, never a code or a sentence.
_MEMBER = re.compile(r"[A-Z][A-Z0-9_]{0,63}")


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
    if not _IDENTIFIER.fullmatch(value):
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
    if not _INSTANT.fullmatch(value):
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


def refuse_an_enum_under_schema_1(
    device_id: str, signal_id: str, unit: object, envelope_schema_version: int = 1
) -> None:
    """T025b: envelope schema 1 carries an exact number, or none, per envelope.

    A typed discrete reading (unit `state`: a generator's `RUNNING`) has no
    number, so a mapping promising one under schema 1 is refused - never
    silently omitted, never disguised as a decimal code, never published as
    UNAVAILABLE. T026: schema 2 carries the member as text, so the refusal
    holds for a schema-1 mapping only - which is every mapping a stage staged
    before T026 froze.
    """
    if unit == DISCRETE_UNIT and envelope_schema_version == 1:
        raise EnvelopeRejected(
            "MAPPING_INCOMPATIBLE",
            "mapping.unit",
            f"{device_id}/{signal_id} reports a typed discrete state, and "
            "source envelope schema 1 carries numbers only; a discrete reading "
            "is published under schema 2",
        )


def _members(value: object, field: str) -> tuple[str, ...]:
    """A closed, ordered, non-empty list of member names, each published once."""
    if type(value) is not tuple or not value:
        raise EnvelopeRejected(
            "INVALID_PAYLOAD", field, "a member list is a non-empty list"
        )
    for member in value:
        if type(member) is not str or not _MEMBER.fullmatch(member):
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                field,
                f"{member!r} is not a member: capitals, digits and '_'",
            )
    if len(set(value)) != len(value):
        raise EnvelopeRejected(
            "INVALID_PAYLOAD", field, "a member is listed twice"
        )
    return value


@dataclass(frozen=True)
class SourceMappingEntry:
    """One allowlisted device signal or record channel, and what it publishes.

    The allowlist IS the list of these. An observation from a signal with no
    entry is not converted, so a new signal crosses the boundary only when
    somebody writes it down here - which is v4 section 11.2's "explicit
    mapping" rather than a gateway that forwards whatever arrives.

    T026: `family` says what the channel publishes. A `MEASUREMENT` entry is a
    device signal as before; in the discrete unit (schema 2 only) it names the
    closed `members` a reading may carry, so a member nobody declared is
    refused rather than published. A `POLICY` or `OPERATIONAL_RECORD` entry is
    a record channel: it names the device a record is published as coming
    from, declared against an existing component, and the unit of the value it
    carries. A record has no measurement class and no typed unavailability.
    """

    device_id: str
    signal_id: str
    measurement: str | None
    unit: str
    #: Whether this signal publishes a typed-unavailable envelope when it was
    #: sampled and had no value. False means such a sample publishes nothing.
    publishes_unavailable: bool
    family: str = "MEASUREMENT"
    members: tuple[str, ...] | None = None
    #: The envelope schema of the mapping this entry belongs to.
    envelope_schema_version: int = 1

    def __post_init__(self) -> None:
        _identifier(self.device_id, "mapping.device_id")
        _identifier(self.signal_id, "mapping.signal_id")
        if self.envelope_schema_version not in READABLE_ENVELOPE_SCHEMA_VERSIONS:
            raise EnvelopeRejected(
                "SCHEMA_UNSUPPORTED",
                "mapping.envelope_schema_version",
                f"{self.envelope_schema_version!r} is not an envelope schema "
                f"this build reads ({sorted(READABLE_ENVELOPE_SCHEMA_VERSIONS)})",
            )
        if self.family not in ENVELOPE_FAMILIES:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "mapping.family",
                f"{self.family!r} is not one of {sorted(ENVELOPE_FAMILIES)}",
            )
        if self.family != "MEASUREMENT" and self.envelope_schema_version == 1:
            raise EnvelopeRejected(
                "MAPPING_INCOMPATIBLE",
                "mapping.family",
                f"{self.device_id}/{self.signal_id} publishes a {self.family} "
                "record, and envelope schema 1 carries measurements only",
            )
        if type(self.unit) is not str or not _UNIT.fullmatch(self.unit):
            raise EnvelopeRejected(
                "INVALID_PAYLOAD", "mapping.unit", f"{self.unit!r} is not a unit"
            )
        if type(self.publishes_unavailable) is not bool:
            raise EnvelopeRejected(
                "WRONG_TYPE",
                "mapping.publishes_unavailable",
                "whether a signal publishes unavailability is true or false",
            )
        if self.family != "MEASUREMENT":
            if self.measurement is not None or self.publishes_unavailable:
                raise EnvelopeRejected(
                    "MAPPING_INCOMPATIBLE",
                    "mapping.measurement",
                    "a record channel has no measurement class and publishes "
                    "no typed unavailability: a record is present or absent",
                )
            if self.members is not None:
                raise EnvelopeRejected(
                    "MAPPING_INCOMPATIBLE",
                    "mapping.members",
                    "a record channel declares no discrete members",
                )
            return
        if self.measurement not in ENVELOPE_MEASUREMENTS:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "mapping.measurement",
                f"{self.measurement!r} is not one of {sorted(ENVELOPE_MEASUREMENTS)}",
            )
        refuse_an_enum_under_schema_1(
            self.device_id, self.signal_id, self.unit, self.envelope_schema_version
        )
        if self.unit == DISCRETE_UNIT:
            if self.measurement != "STATE_AT_INSTANT":
                raise EnvelopeRejected(
                    "MAPPING_INCOMPATIBLE",
                    "mapping.measurement",
                    "a discrete member describes one instant; it is never an "
                    "interval mean",
                )
            _members(self.members, "mapping.members")
        elif self.members is not None:
            raise EnvelopeRejected(
                "MAPPING_INCOMPATIBLE",
                "mapping.members",
                "only a signal in the discrete unit declares members",
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

    T026: `envelope_schema_version` is the schema every envelope published
    under this mapping states. A schema-1 mapping persists exactly as it did
    before the field existed, so a stage staged under one reads and verifies
    byte for byte.
    """

    mapping_set_id: str
    mapping_version: int
    publication_latency_seconds: int
    entries: tuple[SourceMappingEntry, ...]
    envelope_schema_version: int = 1

    def __post_init__(self) -> None:
        _identifier(self.mapping_set_id, "mapping.mapping_set_id")
        _whole(self.mapping_version, "mapping.mapping_version", 1)
        if (
            type(self.envelope_schema_version) is not int
            or self.envelope_schema_version not in READABLE_ENVELOPE_SCHEMA_VERSIONS
        ):
            raise EnvelopeRejected(
                "SCHEMA_UNSUPPORTED",
                "mapping.envelope_schema_version",
                f"{self.envelope_schema_version!r} is not an envelope schema "
                f"this build reads ({sorted(READABLE_ENVELOPE_SCHEMA_VERSIONS)})",
            )
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
            if entry.envelope_schema_version != self.envelope_schema_version:
                raise EnvelopeRejected(
                    "MAPPING_INCOMPATIBLE",
                    "mapping.entries",
                    f"{entry.key} was declared under envelope schema "
                    f"{entry.envelope_schema_version} in a schema "
                    f"{self.envelope_schema_version} mapping",
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
    """The persisted mapping. Schema 1 keeps exactly its pre-T026 key set."""
    entries: list[dict[str, Any]] = []
    for entry in mapping.entries:
        row: dict[str, Any] = {
            "device_id": entry.device_id,
            "signal_id": entry.signal_id,
            "measurement": entry.measurement,
            "unit": entry.unit,
            "publishes_unavailable": entry.publishes_unavailable,
        }
        if mapping.envelope_schema_version >= 2:
            row["family"] = entry.family
            row["members"] = None if entry.members is None else list(entry.members)
        entries.append(row)
    document: dict[str, Any] = {
        "mapping_set_id": mapping.mapping_set_id,
        "mapping_version": mapping.mapping_version,
        "publication_latency_seconds": mapping.publication_latency_seconds,
        "entries": entries,
    }
    if mapping.envelope_schema_version >= 2:
        document["envelope_schema_version"] = mapping.envelope_schema_version
    return document


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
_MAPPING_SET_KEYS_2 = _MAPPING_SET_KEYS | {"envelope_schema_version"}
_MAPPING_ENTRY_KEYS = frozenset(
    {"device_id", "signal_id", "measurement", "unit", "publishes_unavailable"}
)
_MAPPING_ENTRY_KEYS_2 = _MAPPING_ENTRY_KEYS | {"family", "members"}


def parse_mapping_set(document: object) -> SourceMappingSet:
    """A persisted mapping set, read strictly, under the schema it states.

    A mapping that states no envelope schema is a schema-1 mapping and is read
    with schema 1's exact key sets; one that states 2 is read with schema 2's.
    """
    if not isinstance(document, dict):
        raise EnvelopeRejected("WRONG_TYPE", "mapping", "an object is wanted")
    schema = document.get("envelope_schema_version", 1)
    if "envelope_schema_version" in document and schema == 1:
        raise EnvelopeRejected(
            "NOT_CANONICAL",
            "mapping.envelope_schema_version",
            "a schema-1 mapping is persisted without the field",
        )
    if type(schema) is not int or schema not in READABLE_ENVELOPE_SCHEMA_VERSIONS:
        raise EnvelopeRejected(
            "SCHEMA_UNSUPPORTED",
            "mapping.envelope_schema_version",
            f"{schema!r} is not an envelope schema this build reads",
        )
    fields = _exact_keys(
        document, _MAPPING_SET_KEYS if schema == 1 else _MAPPING_SET_KEYS_2, "mapping"
    )
    entries = fields["entries"]
    if not isinstance(entries, list):
        raise EnvelopeRejected("WRONG_TYPE", "mapping.entries", "a list is wanted")
    parsed = []
    for index, row in enumerate(entries):
        entry = _exact_keys(
            row,
            _MAPPING_ENTRY_KEYS if schema == 1 else _MAPPING_ENTRY_KEYS_2,
            f"mapping.entries[{index}]",
        )
        members = entry.get("members")
        if members is not None and not isinstance(members, list):
            raise EnvelopeRejected(
                "WRONG_TYPE", f"mapping.entries[{index}].members", "a list is wanted"
            )
        parsed.append(
            SourceMappingEntry(
                device_id=entry["device_id"],
                signal_id=entry["signal_id"],
                measurement=entry["measurement"],
                unit=entry["unit"],
                publishes_unavailable=entry["publishes_unavailable"],
                family=entry.get("family", "MEASUREMENT"),
                members=None if members is None else tuple(members),
                envelope_schema_version=schema,
            )
        )
    return SourceMappingSet(
        mapping_set_id=fields["mapping_set_id"],
        mapping_version=fields["mapping_version"],
        publication_latency_seconds=fields["publication_latency_seconds"],
        entries=tuple(parsed),
        envelope_schema_version=schema,
    )


#: The schema-2 fields only a record carries.
_RECORD_FIELDS = (
    "control",
    "component_id",
    "members",
    "policy_version",
    "policy_source",
    "effective_start",
    "effective_end",
    "record_kind",
    "actor",
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
    measurement: str | None
    value: Fraction | str | None
    unit: str
    quality: str | None
    unavailable_reason: str | None
    interval_start: str | None
    interval_end: str | None
    #: Schema 1 unless stated: the gateway states its mapping's schema, and a
    #: record written before T026 states 1.
    schema_version: int = 1
    #: T026, schema 2. What the payload is; a schema-1 envelope is always a
    #: measurement and carries no such field on the wire.
    family: str = "MEASUREMENT"
    #: Records only (schema 2). The control a record is about, the component it
    #: governs (none for a Site Control), and the operating time it governs.
    control: str | None = None
    component_id: str | None = None
    members: tuple[str, ...] | None = None
    policy_version: int | None = None
    policy_source: str | None = None
    effective_start: str | None = None
    effective_end: str | None = None
    record_kind: str | None = None
    actor: str | None = None

    def __post_init__(self) -> None:
        if (
            type(self.schema_version) is not int
            or self.schema_version not in READABLE_ENVELOPE_SCHEMA_VERSIONS
        ):
            raise EnvelopeRejected(
                "SCHEMA_UNSUPPORTED",
                "schema.version",
                f"this build reads source envelope schemas "
                f"{sorted(READABLE_ENVELOPE_SCHEMA_VERSIONS)} and nothing else; "
                f"this one states {self.schema_version!r}. It is refused rather "
                "than read under a meaning it was not written with.",
            )
        for field in ("site_id", "source_id", "gateway_id", "device_id", "signal_id"):
            _identifier(getattr(self, field), f"source.{field}")
        _identifier(self.mapping_set_id, "mapping.mapping_set_id")
        _whole(self.mapping_version, "mapping.mapping_version", 1)
        _whole(self.sequence, "message.sequence", 1)
        if type(self.message_id) is not str or not _DIGEST.fullmatch(self.message_id):
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

        if self.family not in ENVELOPE_FAMILIES:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.family",
                f"{self.family!r} is not one of {sorted(ENVELOPE_FAMILIES)}",
            )
        if self.family != "MEASUREMENT":
            if self.schema_version == 1:
                raise EnvelopeRejected(
                    "INVALID_PAYLOAD",
                    "payload.family",
                    "envelope schema 1 carries measurements only",
                )
            self._check_record(sampled)
            return
        for name in _RECORD_FIELDS:
            if getattr(self, name) is not None:
                raise EnvelopeRejected(
                    "INVALID_PAYLOAD",
                    f"payload.{name}",
                    "a measurement carries no record field",
                )
        self._check_payload(sampled)

    def _check_record(self, sampled: datetime) -> None:
        """A policy or operational record: present, whole, and typed."""
        for name in (
            "measurement",
            "quality",
            "unavailable_reason",
            "interval_start",
            "interval_end",
        ):
            if getattr(self, name) is not None:
                raise EnvelopeRejected(
                    "INVALID_PAYLOAD",
                    f"payload.{name}",
                    "a record is not telemetry: it has no measurement class, "
                    "no quality and no interval",
                )
        _identifier(self.control, "payload.control")
        if self.component_id is not None:
            _identifier(self.component_id, "payload.component_id")
        if type(self.unit) is not str or not _UNIT.fullmatch(self.unit):
            raise EnvelopeRejected(
                "INVALID_PAYLOAD", "payload.unit", f"{self.unit!r} is not a unit"
            )
        start = _instant(self.effective_start, "payload.effective_start")
        if self.effective_end is not None:
            end = _instant(self.effective_end, "payload.effective_end")
            if not start < end:
                raise EnvelopeRejected(
                    "INVALID_TIMING",
                    "payload.effective_end",
                    "an effective interval runs forwards and has non-zero length",
                )
        if self.family == "POLICY":
            if self.record_kind is not None or self.actor is not None:
                raise EnvelopeRejected(
                    "INVALID_PAYLOAD",
                    "payload.record_kind",
                    "a policy record names no operational record kind or actor",
                )
            _whole(self.policy_version, "payload.policy_version", 1)
            if self.policy_source not in POLICY_SOURCES:
                raise EnvelopeRejected(
                    "INVALID_PAYLOAD",
                    "payload.policy_source",
                    f"{self.policy_source!r} is not one of {sorted(POLICY_SOURCES)}",
                )
            if (self.value is None) == (self.members is None):
                raise EnvelopeRejected(
                    "INVALID_PAYLOAD",
                    "payload.value",
                    "a policy carries a value or an ordered member list, "
                    "exactly one",
                )
            if self.members is not None:
                _members(self.members, "payload.members")
                if self.unit != ORDER_UNIT:
                    raise EnvelopeRejected(
                        "UNIT_INCOMPATIBLE",
                        "payload.unit",
                        f"an ordered member list is published in {ORDER_UNIT!r}",
                    )
            elif type(self.value) is not Fraction:
                raise EnvelopeRejected(
                    "WRONG_TYPE", "payload.value", "a policy value is exact"
                )
            return
        # OPERATIONAL_RECORD.
        if self.policy_version is not None or self.policy_source is not None:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.policy_version",
                "an operational record is not a policy version",
            )
        if self.members is not None:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD", "payload.members", "an override carries one value"
            )
        if self.record_kind not in OPERATIONAL_RECORD_KINDS:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.record_kind",
                f"{self.record_kind!r} is not one of "
                f"{sorted(OPERATIONAL_RECORD_KINDS)}",
            )
        if self.actor not in RECORD_ACTORS:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.actor",
                f"{self.actor!r} is not one of {sorted(RECORD_ACTORS)}",
            )
        if type(self.value) is not Fraction:
            raise EnvelopeRejected(
                "WRONG_TYPE", "payload.value", "an override value is exact"
            )
        if start < sampled:
            raise EnvelopeRejected(
                "INVALID_TIMING",
                "payload.effective_start",
                f"a command given at {self.source_time} cannot take effect "
                f"earlier, at {self.effective_start}",
            )

    def _check_payload(self, sampled: datetime) -> None:
        if self.measurement not in ENVELOPE_MEASUREMENTS:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.measurement",
                f"{self.measurement!r} is not one of {sorted(ENVELOPE_MEASUREMENTS)}",
            )
        if type(self.unit) is not str or not _UNIT.fullmatch(self.unit):
            raise EnvelopeRejected(
                "INVALID_PAYLOAD", "payload.unit", f"{self.unit!r} is not a unit"
            )
        if self.quality not in ENVELOPE_QUALITIES:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD",
                "payload.quality",
                f"{self.quality!r} is not one of {sorted(ENVELOPE_QUALITIES)}",
            )
        if self.unit == DISCRETE_UNIT:
            if self.schema_version == 1:
                raise EnvelopeRejected(
                    "INVALID_PAYLOAD",
                    "payload.unit",
                    "envelope schema 1 carries numbers only; a discrete member "
                    "is published under schema 2",
                )
            if self.measurement != "STATE_AT_INSTANT":
                raise EnvelopeRejected(
                    "INVALID_PAYLOAD",
                    "payload.measurement",
                    "a discrete member describes one instant",
                )
            if self.value is not None and (
                type(self.value) is not str or not _MEMBER.fullmatch(self.value)
            ):
                raise EnvelopeRejected(
                    "INVALID_PAYLOAD",
                    "payload.value",
                    f"{self.value!r} is not a discrete member: a member is "
                    "carried as itself, never as a number or a code",
                )
        elif self.value is not None and type(self.value) is not Fraction:
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


def _value_text(value: Fraction | str | None) -> str | None:
    if value is None or isinstance(value, str):
        return value
    return exact_decimal_text(value)


def _payload_document(envelope: SourceEnvelope) -> dict[str, Any]:
    if envelope.family == "MEASUREMENT":
        payload: dict[str, Any] = {
            "measurement": envelope.measurement,
            "value": _value_text(envelope.value),
            "unit": envelope.unit,
            "quality": envelope.quality,
            "unavailable_reason": envelope.unavailable_reason,
            "interval_start": envelope.interval_start,
            "interval_end": envelope.interval_end,
        }
        # Schema 1's payload is exactly what it was; the family is stated on
        # the wire from schema 2 on.
        if envelope.schema_version >= 2:
            payload["family"] = envelope.family
        return payload
    common: dict[str, Any] = {
        "family": envelope.family,
        "control": envelope.control,
        "component_id": envelope.component_id,
        "value": _value_text(envelope.value),
        "unit": envelope.unit,
        "effective_start": envelope.effective_start,
        "effective_end": envelope.effective_end,
    }
    if envelope.family == "POLICY":
        common.update(
            {
                "members": (
                    None if envelope.members is None else list(envelope.members)
                ),
                "policy_version": envelope.policy_version,
                "policy_source": envelope.policy_source,
            }
        )
    else:
        common.update({"record_kind": envelope.record_kind, "actor": envelope.actor})
    return common


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
        "payload": _payload_document(envelope),
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
#: Schema 2, one exact key set per family.
_RECORD_COMMON_KEYS = frozenset(
    {
        "family",
        "control",
        "component_id",
        "value",
        "unit",
        "effective_start",
        "effective_end",
    }
)
_PAYLOAD_KEYS_2 = {
    "MEASUREMENT": _PAYLOAD_KEYS | {"family"},
    "POLICY": _RECORD_COMMON_KEYS | {"members", "policy_version", "policy_source"},
    "OPERATIONAL_RECORD": _RECORD_COMMON_KEYS | {"record_kind", "actor"},
}


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
    if not _EXACT.fullmatch(value):
        raise EnvelopeRejected(
            "INVALID_PAYLOAD", "payload.value", f"{value!r} is not an exact number"
        )
    try:
        parsed = Fraction(value)
    except ZeroDivisionError as error:
        # Review R2: `1/0` matches the exact-number pattern and is no number.
        raise EnvelopeRejected(
            "INVALID_PAYLOAD", "payload.value", f"{value!r} divides by zero"
        ) from error
    if exact_decimal_text(parsed) != value:
        raise EnvelopeRejected(
            "NOT_CANONICAL",
            "payload.value",
            f"{value!r} is written as {exact_decimal_text(parsed)!r} canonically",
        )
    return parsed


def _member_or_exact(value: object, unit: object) -> Fraction | str | None:
    """A measurement value: a member in the discrete unit, else exact text."""
    if unit == DISCRETE_UNIT and isinstance(value, str) and _MEMBER.fullmatch(value):
        return value
    return _exact_value(value)


def _member_list(value: object) -> tuple[str, ...] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise EnvelopeRejected(
            "WRONG_TYPE", "payload.members", "a member list is a list"
        )
    return tuple(value)


def parse_source_envelope(document: object) -> SourceEnvelope:
    """One envelope document, read strictly, under the schema it states.

    Exact key sets at every level, exact types, canonical exact values, and every
    record-level rule `SourceEnvelope` enforces. A Python object that is not a
    plain mapping - a `DeviceObservation`, a `LabProjection`, anything with the
    right attribute names - is `NOT_AN_ENVELOPE`: an envelope is data, not an
    object graph that happens to look like one.

    T026: a schema-1 document is read with schema 1's key sets, exactly as
    before; a schema-2 document's payload is read with its family's key set.
    """
    top = _exact_keys(document, _TOP_KEYS, "envelope")
    schema = _exact_keys(top["schema"], _SCHEMA_KEYS, "schema")
    if schema["id"] != SOURCE_ENVELOPE_SCHEMA_ID:
        raise EnvelopeRejected(
            "SCHEMA_UNSUPPORTED",
            "schema.id",
            f"{schema['id']!r} is not {SOURCE_ENVELOPE_SCHEMA_ID!r}",
        )
    version = schema["version"]
    if type(version) is not int:
        raise EnvelopeRejected(
            "WRONG_TYPE", "schema.version", "a schema version is a whole number"
        )
    if version not in READABLE_ENVELOPE_SCHEMA_VERSIONS:
        raise EnvelopeRejected(
            "SCHEMA_UNSUPPORTED",
            "schema.version",
            f"this build reads source envelope schemas "
            f"{sorted(READABLE_ENVELOPE_SCHEMA_VERSIONS)}; this one states "
            f"{version!r}",
        )
    message = _exact_keys(top["message"], _MESSAGE_KEYS, "message")
    source = _exact_keys(top["source"], _SOURCE_KEYS, "source")
    mapping = _exact_keys(top["mapping"], _MAPPING_KEYS, "mapping")
    timing = _exact_keys(top["timing"], _TIMING_KEYS, "timing")
    raw_payload = top["payload"]
    if version == 1:
        payload = _exact_keys(raw_payload, _PAYLOAD_KEYS, "payload")
        family = "MEASUREMENT"
    else:
        if not isinstance(raw_payload, dict):
            raise EnvelopeRejected("WRONG_TYPE", "payload", "an object is wanted")
        family = raw_payload.get("family")
        if family not in _PAYLOAD_KEYS_2:
            raise EnvelopeRejected(
                "INVALID_PAYLOAD"
                if "family" in raw_payload
                else "MISSING_FIELD",
                "payload.family",
                f"{family!r} is not one of {sorted(ENVELOPE_FAMILIES)}",
            )
        payload = _exact_keys(raw_payload, _PAYLOAD_KEYS_2[family], "payload")
    common = dict(
        schema_version=version,
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
        unit=payload["unit"],
        family=family,
    )
    if family == "MEASUREMENT":
        return SourceEnvelope(
            **common,
            measurement=payload["measurement"],
            value=(
                _member_or_exact(payload["value"], payload["unit"])
                if version >= 2
                else _exact_value(payload["value"])
            ),
            quality=payload["quality"],
            unavailable_reason=_optional_text(
                payload["unavailable_reason"], "payload.unavailable_reason"
            ),
            interval_start=_optional_text(
                payload["interval_start"], "payload.interval_start"
            ),
            interval_end=_optional_text(
                payload["interval_end"], "payload.interval_end"
            ),
        )
    return SourceEnvelope(
        **common,
        measurement=None,
        value=_exact_value(payload["value"]),
        quality=None,
        unavailable_reason=None,
        interval_start=None,
        interval_end=None,
        control=payload["control"],
        component_id=payload["component_id"],
        members=_member_list(payload.get("members")),
        policy_version=payload.get("policy_version"),
        policy_source=payload.get("policy_source"),
        effective_start=payload["effective_start"],
        effective_end=_optional_text(
            payload["effective_end"], "payload.effective_end"
        ),
        record_kind=payload.get("record_kind"),
        actor=payload.get("actor"),
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
    if envelope.schema_version != mapping.envelope_schema_version:
        raise EnvelopeRejected(
            "MAPPING_INCOMPATIBLE",
            "schema.version",
            f"the envelope states schema {envelope.schema_version} and "
            f"{mapping.mapping_set_id} v{mapping.mapping_version} publishes "
            f"schema {mapping.envelope_schema_version}",
        )
    entry = mapping.entry(envelope.device_id, envelope.signal_id)
    if entry is None:
        raise EnvelopeRejected(
            "MAPPING_INCOMPATIBLE",
            "source.signal_id",
            f"{envelope.device_id}/{envelope.signal_id} is not on the allowlist "
            f"of {mapping.mapping_set_id} v{mapping.mapping_version}",
        )
    if envelope.family != entry.family:
        raise EnvelopeRejected(
            "MAPPING_INCOMPATIBLE",
            "payload.family",
            f"the mapping publishes {entry.family} on this channel and the "
            f"envelope is {envelope.family}",
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
    if (
        entry.members is not None
        and envelope.value is not None
        and envelope.value not in entry.members
    ):
        raise EnvelopeRejected(
            "MAPPING_INCOMPATIBLE",
            "payload.value",
            f"{envelope.value!r} is not one of the members this signal's "
            f"mapping declares ({list(entry.members)})",
        )
    return entry
