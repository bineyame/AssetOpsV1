"""GatewayDiagnosticsV1: the gateway's own operational report (S2-01c).

Technical design 3. A diagnostic is published independently of readings, so an
idle or disconnected source still leaves gateway state on record. It describes
the gateway's local queue and sources as the gateway itself observed them; it
is never evidence, never enters `AcceptedEvidence` and never asserts that a
device or asset is healthy.

## Identity and digest

Identity is `(gateway_id, sequence_epoch, diagnostic_sequence)`; the gateway
allocates the sequence once, in the same SQLite transaction that stores the
exact bytes. `payload_sha256` is SHA-256 over the UTF-8 bytes of the canonical
JSON of the document WITHOUT the `payload_sha256` key (sorted keys, no
whitespace, `ensure_ascii=False`), as for Batch V2. The parser recomputes it;
a sender digest is never trusted.

## Fields

`last_device_contact_by_source` names every source the gateway is permitted to
hear; a source never heard is `null` (unknown), never a made-up time.
`oldest_queue_age_seconds` is `null` when nothing is queued. `clock_offset_ms`
is `null` unless an offset was actually measured (or injected by a labelled
fault fixture, which the gateway's local read says). `disk_pressure` is the
gateway's operative storage state; its provenance (measured or injected) is a
local read fact and not part of this wire. There is no `received_at`: the
server sets that (S2-02). No field can carry a Lab run id, scenario control or
private cause: the key set is exact.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from assetops_contracts.source_envelope import EnvelopeRejected, canonical_json, load_canonical_json
from assetops_contracts.source_envelope_v3 import MAX_SEQUENCE, text_sha256

GATEWAY_DIAGNOSTICS_SCHEMA_ID = "assetops.gateway-diagnostics"
GATEWAY_DIAGNOSTICS_SCHEMA_VERSION = 1
DISK_PRESSURES = ("OK", "WARN", "STOP")
#: Bounds: a diagnostic is small. Sources are bounded so the text is bounded.
MAX_DIAGNOSTIC_SOURCES = 256
MAX_DIAGNOSTIC_BYTES = 65_536
#: Whole-number fields fit SQLite INTEGER and are never negative, except the
#: clock offset, whose magnitude is bounded to about 31 years.
MAX_COUNT = 2**63 - 1
MAX_CLOCK_OFFSET_MS = 10**12

_IDENTIFIER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?")
_DIGEST = re.compile(r"[0-9a-f]{64}")
_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

_KEYS = frozenset(
    {
        "schema",
        "site_id",
        "gateway_id",
        "sequence_epoch",
        "diagnostic_sequence",
        "observed_at",
        "last_device_contact_by_source",
        "queue_count",
        "oldest_queue_age_seconds",
        "disk_pressure",
        "clock_offset_ms",
        "mapping_error_count",
        "payload_sha256",
    }
)


class DiagnosticRejected(ValueError):
    def __init__(self, kind: str, field: str, detail: str) -> None:
        self.kind = kind
        self.field = field
        self.detail = detail
        super().__init__(f"{kind} at {field}: {detail}")


@dataclass(frozen=True)
class GatewayDiagnosticsV1:
    site_id: str
    gateway_id: str
    sequence_epoch: str
    diagnostic_sequence: int
    observed_at: str
    #: Sorted `(source_id, last contact or None)` pairs.
    last_device_contact_by_source: tuple[tuple[str, str | None], ...]
    queue_count: int
    oldest_queue_age_seconds: int | None
    disk_pressure: str
    clock_offset_ms: int | None
    mapping_error_count: int
    payload_sha256: str


def _whole(value: object, field: str, *, low: int, high: int, optional: bool = False) -> None:
    if value is None and optional:
        return
    if type(value) is not int or not low <= value <= high:
        raise DiagnosticRejected("INVALID_FIELD", field, f"a whole number in [{low}, {high}] is wanted")


def _body(
    *,
    site_id: str,
    gateway_id: str,
    sequence_epoch: str,
    diagnostic_sequence: int,
    observed_at: str,
    last_device_contact_by_source: dict[str, str | None],
    queue_count: int,
    oldest_queue_age_seconds: int | None,
    disk_pressure: str,
    clock_offset_ms: int | None,
    mapping_error_count: int,
) -> dict[str, Any]:
    for field, value in (("site_id", site_id), ("gateway_id", gateway_id), ("sequence_epoch", sequence_epoch)):
        if type(value) is not str or not _IDENTIFIER.fullmatch(value):
            raise DiagnosticRejected("INVALID_FIELD", field, "not an identifier")
    _whole(diagnostic_sequence, "diagnostic_sequence", low=1, high=MAX_SEQUENCE)
    if type(observed_at) is not str or not _INSTANT.fullmatch(observed_at):
        raise DiagnosticRejected("INVALID_TIMING", "observed_at", "a UTC instant to the second is wanted")
    if type(last_device_contact_by_source) is not dict:
        raise DiagnosticRejected("WRONG_TYPE", "last_device_contact_by_source", "an object is wanted")
    if len(last_device_contact_by_source) > MAX_DIAGNOSTIC_SOURCES:
        raise DiagnosticRejected("TOO_LARGE", "last_device_contact_by_source", "too many sources")
    for source_id, contact in last_device_contact_by_source.items():
        if type(source_id) is not str or not _IDENTIFIER.fullmatch(source_id):
            raise DiagnosticRejected("INVALID_FIELD", "last_device_contact_by_source", "not a source identifier")
        if contact is not None and (type(contact) is not str or not _INSTANT.fullmatch(contact)):
            raise DiagnosticRejected(
                "INVALID_TIMING", f"last_device_contact_by_source.{source_id}", "a UTC instant or null is wanted"
            )
        if contact is not None and contact > observed_at:
            raise DiagnosticRejected(
                "INVALID_TIMING", f"last_device_contact_by_source.{source_id}", "a contact after observed_at"
            )
    _whole(queue_count, "queue_count", low=0, high=MAX_COUNT)
    _whole(oldest_queue_age_seconds, "oldest_queue_age_seconds", low=0, high=MAX_COUNT, optional=True)
    if (queue_count == 0) != (oldest_queue_age_seconds is None):
        raise DiagnosticRejected(
            "INCONSISTENT", "oldest_queue_age_seconds", "an age exists exactly when something is queued"
        )
    if disk_pressure not in DISK_PRESSURES:
        raise DiagnosticRejected("INVALID_FIELD", "disk_pressure", f"one of {list(DISK_PRESSURES)} is wanted")
    _whole(clock_offset_ms, "clock_offset_ms", low=-MAX_CLOCK_OFFSET_MS, high=MAX_CLOCK_OFFSET_MS, optional=True)
    _whole(mapping_error_count, "mapping_error_count", low=0, high=MAX_COUNT)
    return {
        "schema": {"id": GATEWAY_DIAGNOSTICS_SCHEMA_ID, "version": GATEWAY_DIAGNOSTICS_SCHEMA_VERSION},
        "site_id": site_id,
        "gateway_id": gateway_id,
        "sequence_epoch": sequence_epoch,
        "diagnostic_sequence": diagnostic_sequence,
        "observed_at": observed_at,
        "last_device_contact_by_source": dict(sorted(last_device_contact_by_source.items())),
        "queue_count": queue_count,
        "oldest_queue_age_seconds": oldest_queue_age_seconds,
        "disk_pressure": disk_pressure,
        "clock_offset_ms": clock_offset_ms,
        "mapping_error_count": mapping_error_count,
    }


def seal_gateway_diagnostics_v1(**fields: Any) -> tuple[GatewayDiagnosticsV1, str]:
    """`(diagnostic, canonical text)` for validated fields; the digest is computed here."""
    body = _body(**fields)
    digest = text_sha256(canonical_json(body))
    text = canonical_json({**body, "payload_sha256": digest})
    if len(text.encode("utf-8")) > MAX_DIAGNOSTIC_BYTES:
        raise DiagnosticRejected("TOO_LARGE", "diagnostic", f"over {MAX_DIAGNOSTIC_BYTES} bytes")
    return (
        GatewayDiagnosticsV1(
            site_id=body["site_id"],
            gateway_id=body["gateway_id"],
            sequence_epoch=body["sequence_epoch"],
            diagnostic_sequence=body["diagnostic_sequence"],
            observed_at=body["observed_at"],
            last_device_contact_by_source=tuple(body["last_device_contact_by_source"].items()),
            queue_count=body["queue_count"],
            oldest_queue_age_seconds=body["oldest_queue_age_seconds"],
            disk_pressure=body["disk_pressure"],
            clock_offset_ms=body["clock_offset_ms"],
            mapping_error_count=body["mapping_error_count"],
            payload_sha256=digest,
        ),
        text,
    )


def parse_canonical_gateway_diagnostics_v1_text(text: object) -> GatewayDiagnosticsV1:
    """Exact stored/received bytes back as a diagnostic; every rule re-checked."""
    if type(text) is str and len(text.encode("utf-8")) > MAX_DIAGNOSTIC_BYTES:
        raise DiagnosticRejected("TOO_LARGE", "diagnostic", f"over {MAX_DIAGNOSTIC_BYTES} bytes")
    try:
        document = load_canonical_json(text)
    except EnvelopeRejected as error:
        raise DiagnosticRejected("MALFORMED_TEXT", "diagnostic", error.detail) from error
    if not isinstance(document, dict):
        raise DiagnosticRejected("WRONG_TYPE", "diagnostic", "an object is wanted")
    for key in sorted(document):
        if key not in _KEYS:
            raise DiagnosticRejected("UNKNOWN_FIELD", key, "not a GatewayDiagnosticsV1 field")
    for key in sorted(_KEYS):
        if key not in document:
            raise DiagnosticRejected("MISSING_FIELD", key, "required")
    if document["schema"] != {"id": GATEWAY_DIAGNOSTICS_SCHEMA_ID, "version": GATEWAY_DIAGNOSTICS_SCHEMA_VERSION}:
        raise DiagnosticRejected("SCHEMA_UNSUPPORTED", "schema", f"{document['schema']!r}")
    fields = {k: v for k, v in document.items() if k not in ("schema", "payload_sha256")}
    diagnostic, rebuilt = seal_gateway_diagnostics_v1(**fields)
    if type(document["payload_sha256"]) is not str or not _DIGEST.fullmatch(document["payload_sha256"]):
        raise DiagnosticRejected("INVALID_FIELD", "payload_sha256", "not a SHA-256 hex digest")
    if document["payload_sha256"] != diagnostic.payload_sha256:
        raise DiagnosticRejected("DIGEST_MISMATCH", "payload_sha256", "does not match the canonical bytes")
    if rebuilt != text:
        raise DiagnosticRejected("NOT_CANONICAL", "diagnostic", "the text is not its own canonical text")
    return diagnostic


# --- the frozen emission configuration ------------------------------------------

GATEWAY_DIAGNOSTICS_CONFIG_SCHEMA_ID = "assetops.gateway-diagnostics-config"
GATEWAY_DIAGNOSTICS_CONFIG_SCHEMA_VERSION = 1
MIN_CADENCE_SECONDS = 10
MAX_CADENCE_SECONDS = 86_400
_CONFIG_KEYS = frozenset(
    {
        "schema",
        "emission_cadence_seconds",
        "disk_warn_free_bytes",
        "disk_stop_free_bytes",
        "max_sources",
        "max_payload_bytes",
    }
)


@dataclass(frozen=True)
class DiagnosticConfig:
    """What the gateway declares about its diagnostics, frozen at provisioning.

    `emission_cadence_seconds` is the declared heartbeat: at most one diagnostic
    per cadence slot, so S2-02 can judge freshness from server receive time.
    Disk pressure is `STOP` below `disk_stop_free_bytes` free, `WARN` below
    `disk_warn_free_bytes`, else `OK` - the explicit measured triggers. The
    wire limits are this contract's bounds, returned so a reader knows them."""

    emission_cadence_seconds: int = 60
    disk_warn_free_bytes: int = 1_073_741_824
    disk_stop_free_bytes: int = 268_435_456

    def document(self) -> dict[str, Any]:
        _whole(
            self.emission_cadence_seconds,
            "emission_cadence_seconds",
            low=MIN_CADENCE_SECONDS,
            high=MAX_CADENCE_SECONDS,
        )
        _whole(self.disk_stop_free_bytes, "disk_stop_free_bytes", low=0, high=MAX_COUNT)
        _whole(self.disk_warn_free_bytes, "disk_warn_free_bytes", low=0, high=MAX_COUNT)
        if self.disk_warn_free_bytes < self.disk_stop_free_bytes:
            raise DiagnosticRejected("INCONSISTENT", "disk_warn_free_bytes", "the WARN trigger is below STOP")
        return {
            "schema": {"id": GATEWAY_DIAGNOSTICS_CONFIG_SCHEMA_ID, "version": GATEWAY_DIAGNOSTICS_CONFIG_SCHEMA_VERSION},
            "emission_cadence_seconds": self.emission_cadence_seconds,
            "disk_warn_free_bytes": self.disk_warn_free_bytes,
            "disk_stop_free_bytes": self.disk_stop_free_bytes,
            "max_sources": MAX_DIAGNOSTIC_SOURCES,
            "max_payload_bytes": MAX_DIAGNOSTIC_BYTES,
        }

    def text(self) -> str:
        return canonical_json(self.document())

    def pressure(self, free_bytes: int) -> str:
        if free_bytes < self.disk_stop_free_bytes:
            return "STOP"
        if free_bytes < self.disk_warn_free_bytes:
            return "WARN"
        return "OK"


def parse_diagnostic_config_text(text: object) -> DiagnosticConfig:
    try:
        document = load_canonical_json(text)
    except EnvelopeRejected as error:
        raise DiagnosticRejected("MALFORMED_TEXT", "config", error.detail) from error
    if not isinstance(document, dict) or set(document) != _CONFIG_KEYS:
        raise DiagnosticRejected("UNKNOWN_FIELD", "config", f"exactly {sorted(_CONFIG_KEYS)} are wanted")
    config = DiagnosticConfig(
        emission_cadence_seconds=document["emission_cadence_seconds"],
        disk_warn_free_bytes=document["disk_warn_free_bytes"],
        disk_stop_free_bytes=document["disk_stop_free_bytes"],
    )
    if config.text() != text:
        raise DiagnosticRejected("NOT_CANONICAL", "config", "the text is not its own canonical text")
    return config
