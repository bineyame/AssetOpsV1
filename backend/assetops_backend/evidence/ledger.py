"""The central evidence ledger's domain: principal, accepted-as basis, per-ordinal decisions (S2-02).

Pure code only; the Postgres adapter (`evidence/adapters/postgres_evidence_ledger.py`)
persists what this module decides, and `ledger_service.py` orchestrates it.

* `GatewayPrincipal` is the authenticated registered scope. It is derived from a
  credential and its registered gateway row, never from caller fields
  (`D-2026-10-09-s2-pilot-gateway-upload-credential`). Phase 1 injects it; the
  default resolver keeps network uploads closed.
* `AcceptedAsBasis` is built from the **pinned snapshot bytes** of the binding
  set revision the batch names, so the accepted-as Foundation and binding
  revisions are immutable original registrations, not today's mutable names
  (S2-02 AC3/AC4, technical design section 1).
* `decide` turns one canonical V3 envelope into an acceptance with central
  normalization (IDENTITY or ENUM of the selected binding) or a specific
  rejection. It never infers a mapping that the referenced set does not hold.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Mapping, Protocol, Sequence
from uuid import UUID

from assetops_contracts.ingestion_receipt_v2 import IngestionReceiptV2
from assetops_contracts.source_envelope import EnvelopeRejected
from assetops_contracts.source_envelope_v3 import (
    SourceEnvelopeV3,
    parse_canonical_envelope_v3_text,
    text_sha256,
)

#: S3's first analytic consumes this queue; S2-02 only enqueues (questions-1 Q4).
RECOMPUTE_DOMAIN = "dispatch"

ACKNOWLEDGED_SNAPSHOT_SCHEMA = "assetops.acquisition-snapshot/1"


# --- principal ---------------------------------------------------------------


@dataclass(frozen=True)
class GatewayPrincipal:
    """Authenticated registered scope of one gateway. Immutable registration facts only."""

    tenant_id: UUID
    site_id: UUID
    gateway_id: UUID
    mode: str


class PrincipalRefused(Exception):
    """Authentication (401) or authorization (403) refused; never a Site ledger row."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


class GatewayPrincipalResolver(Protocol):
    def resolve(self, authorization: str | None) -> GatewayPrincipal:
        """The principal for this request's credential, or raise `PrincipalRefused(401, ...)`."""


class ClosedGatewayPrincipals:
    """Default: no network upload authority exists until the TLS/bearer verifier lands (phase 2)."""

    def resolve(self, authorization: str | None) -> GatewayPrincipal:
        raise PrincipalRefused(
            401,
            "GATEWAY_UPLOAD_CLOSED",
            "Central gateway upload is closed: no registered gateway credential verifier is "
            "configured. The local IPC credential and the development tenant grant no upload authority.",
        )


# --- registered scope facts ----------------------------------------------------


@dataclass(frozen=True)
class RegisteredScope:
    """Current registration rows a batch's claims are checked against."""

    gateway_site_id: UUID | None
    gateway_mode: str | None
    gateway_disabled: bool
    source_gateway_id: UUID | None
    source_site_id: UUID | None
    source_disabled: bool


# --- accepted-as basis -----------------------------------------------------------


@dataclass(frozen=True)
class BindingBasis:
    binding_revision_id: UUID
    device_id: str
    signal_id: str
    source_id: str
    asset_id: UUID | None
    role: str
    source_unit: str
    canonical_unit: str
    conversion: Mapping[str, Any]


@dataclass(frozen=True)
class AcceptedAsBasis:
    foundation_revision_id: UUID
    foundation_version: int
    foundation_valid_from_text: str
    foundation_valid_from: datetime
    foundation_valid_to: datetime | None
    binding_set_revision_id: UUID
    binding_set_id: str
    binding_version: int
    binding_valid_from: datetime
    binding_valid_to: datetime | None
    gateway_id: str
    snapshot_sha256: str
    outdated: bool
    bindings: Mapping[tuple[str, str], BindingBasis]


@dataclass(frozen=True)
class StoredBindingSet:
    """What the adapter reads for a referenced binding set revision."""

    binding_set_revision_id: UUID
    foundation_revision_id: UUID
    snapshot_sha256: str
    snapshot_canonical: bytes
    set_superseded: bool
    foundation_superseded: bool


class ConfigurationRefused(Exception):
    def __init__(self, kind: str, field: str, detail: str) -> None:
        super().__init__(detail)
        self.kind = kind
        self.field = field
        self.detail = detail


def parse_instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def basis_from_snapshot(
    stored: StoredBindingSet,
    *,
    foundation_version: int,
    foundation_valid_from: str,
    binding_set_id: str,
    binding_version: int,
    snapshot_sha256: str,
) -> AcceptedAsBasis:
    """Check a batch's configuration reference against the pinned snapshot; build the basis.

    Any mismatch is a whole-batch `CONFIGURATION_MISMATCH`: the spelling of
    `foundation_valid_from` must equal the pinned text exactly (fractional
    seconds included, `D-2026-10-08-s2-v3-source-payload-and-period-reference`).
    """
    if stored.snapshot_sha256 != snapshot_sha256:
        raise ConfigurationRefused(
            "CONFIGURATION_MISMATCH", "mapping.snapshot_sha256",
            "the batch's snapshot digest is not the one pinned for this binding set version",
        )
    if text_sha256(stored.snapshot_canonical.decode("utf-8")) != stored.snapshot_sha256:
        raise ConfigurationRefused(
            "CONFIGURATION_UNREADABLE", "mapping.snapshot_sha256", "the stored snapshot does not hash to its pin"
        )
    doc = json.loads(stored.snapshot_canonical.decode("utf-8"))
    if doc.get("schema") != ACKNOWLEDGED_SNAPSHOT_SCHEMA:
        raise ConfigurationRefused(
            "CONFIGURATION_UNREADABLE", "mapping", f"snapshot schema {doc.get('schema')!r} is not supported"
        )
    foundation, mapping = doc["foundation"], doc["mapping"]
    if foundation["revision_id"] != str(stored.foundation_revision_id):
        raise ConfigurationRefused(
            "CONFIGURATION_UNREADABLE", "configuration", "the snapshot names another Foundation revision"
        )
    if foundation["version"] != foundation_version:
        raise ConfigurationRefused(
            "CONFIGURATION_MISMATCH", "configuration.foundation_version",
            f"the binding set version was pinned to Foundation v{foundation['version']}, not v{foundation_version}",
        )
    if foundation["valid_from"] != foundation_valid_from:
        raise ConfigurationRefused(
            "CONFIGURATION_MISMATCH", "configuration.foundation_valid_from",
            f"{foundation_valid_from!r} is not the registered spelling {foundation['valid_from']!r}",
        )
    if mapping["binding_set_id"] != binding_set_id or mapping["version"] != binding_version:
        raise ConfigurationRefused("CONFIGURATION_UNREADABLE", "mapping", "the snapshot names another binding set")
    bindings: dict[tuple[str, str], BindingBasis] = {}
    for row in doc["bindings"]:
        bindings[(row["device_id"], row["signal_id"])] = BindingBasis(
            binding_revision_id=UUID(row["binding_revision_id"]),
            device_id=row["device_id"],
            signal_id=row["signal_id"],
            source_id=row["source_id"],
            asset_id=None if row["asset_id"] is None else UUID(row["asset_id"]),
            role=row["role"],
            source_unit=row["source_unit"],
            canonical_unit=row["canonical_unit"],
            conversion=row["conversion"],
        )
    return AcceptedAsBasis(
        foundation_revision_id=stored.foundation_revision_id,
        foundation_version=foundation["version"],
        foundation_valid_from_text=foundation["valid_from"],
        foundation_valid_from=parse_instant(foundation["valid_from"]),
        foundation_valid_to=None if foundation["valid_to"] is None else parse_instant(foundation["valid_to"]),
        binding_set_revision_id=stored.binding_set_revision_id,
        binding_set_id=binding_set_id,
        binding_version=binding_version,
        binding_valid_from=parse_instant(mapping["valid_from"]),
        binding_valid_to=None if mapping["valid_to"] is None else parse_instant(mapping["valid_to"]),
        gateway_id=doc["gateway"]["gateway_id"],
        snapshot_sha256=stored.snapshot_sha256,
        outdated=stored.set_superseded or stored.foundation_superseded,
        bindings=bindings,
    )


# --- per-ordinal decisions -------------------------------------------------------


@dataclass(frozen=True)
class Accepted:
    ordinal: int
    envelope: SourceEnvelopeV3
    envelope_text: str
    envelope_sha256: str
    binding: BindingBasis
    normalized_value_text: str | None
    normalized_unit: str
    conversion_kind: str
    source_time: datetime
    published_at: datetime
    interval_start: datetime | None
    interval_end: datetime | None
    configuration_outdated: bool


@dataclass(frozen=True)
class Rejected:
    ordinal: int
    message_id: str
    kind: str
    field: str
    detail: str
    envelope_sha256: str


Decision = Accepted | Rejected


def _within(instant: datetime, start: datetime, end: datetime | None) -> bool:
    return start <= instant and (end is None or instant < end)


def decide(basis: AcceptedAsBasis, ordinal: int, envelope_text: str) -> Decision:
    """One envelope against its batch's accepted-as basis. Pure and deterministic."""
    digest = text_sha256(envelope_text)
    try:
        envelope = parse_canonical_envelope_v3_text(envelope_text)
    except EnvelopeRejected as error:
        return Rejected(ordinal, "", error.kind, error.field, error.detail, digest)

    def reject(kind: str, field: str, detail: str) -> Rejected:
        return Rejected(ordinal, envelope.message_id, kind, field, detail, digest)

    if envelope.family != "MEASUREMENT":
        return reject("SCHEMA_UNSUPPORTED", "payload.family", f"{envelope.family} is not ingested in this release")
    binding = basis.bindings.get((envelope.device_id, envelope.signal_id))
    if binding is None or binding.source_id != envelope.source_id:
        return reject(
            "BINDING_NOT_REGISTERED", "source.signal_id",
            f"binding set v{basis.binding_version} registers no channel {envelope.device_id}/{envelope.signal_id} "
            "for this source",
        )
    source_time = parse_instant(envelope.source_time)
    if not _within(source_time, basis.foundation_valid_from, basis.foundation_valid_to):
        return reject(
            "OUTSIDE_FOUNDATION_PERIOD", "timing.source_time",
            f"{envelope.source_time} is outside Foundation v{basis.foundation_version}'s registered period "
            f"[{basis.foundation_valid_from_text}, {_text(basis.foundation_valid_to)})",
        )
    if not _within(source_time, basis.binding_valid_from, basis.binding_valid_to):
        return reject(
            "OUTSIDE_BINDING_PERIOD", "timing.source_time",
            f"{envelope.source_time} is outside binding set v{basis.binding_version}'s registered period "
            f"[{_text(basis.binding_valid_from)}, {_text(basis.binding_valid_to)})",
        )
    if envelope.unit != binding.source_unit:
        return reject(
            "UNIT_INCOMPATIBLE", "payload.unit",
            f"{envelope.unit!r} is not the registered source unit {binding.source_unit!r}",
        )
    kind = binding.conversion.get("kind")
    value = envelope.value
    if kind == "IDENTITY":
        normalized = value
    elif kind == "ENUM":
        mapping = binding.conversion.get("parameters", {}).get("map", {})
        if value is None:
            normalized = None
        elif value not in mapping:
            return reject("INVALID_ENUM", "payload.value", f"{value!r} is not in the registered ENUM map")
        else:
            normalized = mapping[value]
    else:
        return reject("CONVERSION_UNSUPPORTED", "mapping", f"conversion {kind!r} is not applied in this release")
    return Accepted(
        ordinal=ordinal,
        envelope=envelope,
        envelope_text=envelope_text,
        envelope_sha256=digest,
        binding=binding,
        normalized_value_text=normalized,
        normalized_unit=binding.canonical_unit,
        conversion_kind=kind,
        source_time=source_time,
        published_at=parse_instant(envelope.published_at),
        interval_start=None if envelope.interval_start is None else parse_instant(envelope.interval_start),
        interval_end=None if envelope.interval_end is None else parse_instant(envelope.interval_end),
        configuration_outdated=basis.outdated,
    )


def _text(value: datetime | None) -> str:
    return "no end" if value is None else value.isoformat().replace("+00:00", "Z")


def recompute_window(accepted: Sequence[Accepted]) -> tuple[datetime, datetime] | None:
    """The half-open source-time window an analytic must revisit for these acceptances."""
    if not accepted:
        return None
    starts = [a.interval_start or a.source_time for a in accepted]
    ends = [a.interval_end or (a.source_time + timedelta(microseconds=1)) for a in accepted]
    return min(starts), max(ends)


# --- ledger port -----------------------------------------------------------------


@dataclass(frozen=True)
class BatchHandle:
    id: UUID
    payload_sha256: str
    status: str


class LedgerUnavailable(Exception):
    """The ledger cannot be read or written."""


class BatchIdConflict(Exception):
    """Same external batch ID, different bytes; the stored batch is untouched."""


class EvidenceLedger(Protocol):
    def registered_scope(self, principal: GatewayPrincipal, source_id: str) -> RegisteredScope: ...

    def binding_set(
        self, principal: GatewayPrincipal, binding_set_id: str, binding_version: int
    ) -> StoredBindingSet | None: ...

    def record_refusal(
        self,
        principal: GatewayPrincipal,
        *,
        external_batch_id: str | None,
        payload_sha256: str,
        kind: str,
        field: str,
        detail: str,
        received_at: datetime,
    ) -> UUID: ...

    def find_batch(self, principal: GatewayPrincipal, external_batch_id: str) -> BatchHandle | None: ...

    def open_batch(
        self,
        principal: GatewayPrincipal,
        *,
        external_batch_id: str,
        payload_sha256: str,
        source_id: str,
        source_mode: str,
        basis: AcceptedAsBasis,
        batch_text: str,
        total: int,
        received_at: datetime,
    ) -> BatchHandle: ...

    def decide_chunk(
        self,
        batch: BatchHandle,
        envelopes: Sequence[str],
        decide_one: Callable[[int, str], Decision],
        *,
        limit: int,
        decided_at: datetime,
    ) -> str: ...

    def receipt(self, principal: GatewayPrincipal, external_batch_id: str) -> IngestionReceiptV2 | None: ...
