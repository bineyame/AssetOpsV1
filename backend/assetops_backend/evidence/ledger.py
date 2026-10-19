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
  normalization (IDENTITY, ENUM, or W2-05b's EV-energy IDENTITY_KWH of the selected binding) or a specific
  rejection. It never infers a mapping that the referenced set does not hold.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Mapping, Protocol, Sequence
from uuid import UUID

from assetops_contracts.ingestion_receipt_v2 import IngestionReceiptV2
from assetops_contracts.source_envelope import EnvelopeRejected
from assetops_contracts.source_envelope_v3 import (
    SourceEnvelopeV3,
    is_canonical_decimal,
    text_sha256,
)
from assetops_contracts.source_envelope_v4 import (
    EV_KINDS,
    V4_BINDING_METADATA_KEYS,
    V4_CHANNEL_MAPPINGS,
    SourceEnvelopeV4,
    canonical_binding_metadata,
    header_message_id,
    parse_canonical_source_envelope_text,
    uses_v4_header_path,
)

#: S3's first analytic consumes this queue; S2-02 only enqueues (questions-1 Q4).
RECOMPUTE_DOMAIN = "dispatch"
#: W2-03: a new accepted v4 record bound to a `cold-roles-1` role enqueues the cold assessment job.
COLD_RECOMPUTE_DOMAIN = "cold_chain"

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
    # W2-00 ruling 4: the optional v4 snapshot binding-row keys; absent (a v3 row) reads as None.
    allowed_record_kinds: Sequence[str] | None = None
    allowed_outcomes: Mapping[str, Sequence[str]] | None = None
    requires_correlation: bool | None = None
    requires_session: bool | None = None
    allowed_units: Sequence[str] | None = None
    #: The bound asset's frozen public identifier (`asset.asset_code`, its Foundation component ID): an EV
    #: connector's canonical public identifier. None when the binding has no asset.
    asset_code: str | None = None

    def v4_metadata(self) -> dict[str, Any] | None:
        return canonical_binding_metadata({k: getattr(self, k) for k in V4_BINDING_METADATA_KEYS})


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
    #: `asset.asset_code` by asset UUID for the principal's Site (immutable registration facts).
    asset_codes: Mapping[UUID, str] = field(default_factory=dict)


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
        asset_id = None if row["asset_id"] is None else UUID(row["asset_id"])
        bindings[(row["device_id"], row["signal_id"])] = BindingBasis(
            binding_revision_id=UUID(row["binding_revision_id"]),
            device_id=row["device_id"],
            signal_id=row["signal_id"],
            source_id=row["source_id"],
            asset_id=asset_id,
            role=row["role"],
            source_unit=row["source_unit"],
            canonical_unit=row["canonical_unit"],
            conversion=row["conversion"],
            allowed_record_kinds=row.get("allowed_record_kinds"),
            allowed_outcomes=row.get("allowed_outcomes"),
            requires_correlation=row.get("requires_correlation"),
            requires_session=row.get("requires_session"),
            allowed_units=row.get("allowed_units"),
            asset_code=None if asset_id is None else stored.asset_codes.get(asset_id),
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
    envelope: SourceEnvelopeV3 | SourceEnvelopeV4
    envelope_text: str
    envelope_sha256: str
    binding: BindingBasis
    normalized_value_text: str | None
    normalized_unit: str | None
    conversion_kind: str | None
    source_time: datetime
    published_at: datetime
    interval_start: datetime | None
    interval_end: datetime | None
    configuration_outdated: bool

    @property
    def is_v4(self) -> bool:
        return isinstance(self.envelope, SourceEnvelopeV4)


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


#: W2-05b q3 Q17: the one binding shape `IDENTITY_KWH` normalizes.
IDENTITY_KWH = "IDENTITY_KWH"
IDENTITY_KWH_ROLE = "ev_connector_energy"
KWH_UNIT = "kWh"


def _normalize(binding: BindingBasis, value: str | None) -> tuple[str | None, str | None, str | None]:
    """(normalized value, conversion kind, refusal kind) under the selected binding's conversion."""
    kind = binding.conversion.get("kind")
    if kind == "IDENTITY":
        return value, kind, None
    if kind == IDENTITY_KWH:
        # W2-05b q3 Q17: the unchanged canonical kWh decimal, only for the selected EV energy binding shape. It is
        # never a counter or a unit conversion; the v4 delta/session/connector checks stay authoritative.
        if (binding.role != IDENTITY_KWH_ROLE or binding.source_unit != KWH_UNIT
                or binding.canonical_unit != KWH_UNIT or binding.conversion.get("parameters") != {}
                or (value is not None and not is_canonical_decimal(value))):
            return None, kind, "CONVERSION_UNSUPPORTED"
        return value, kind, None
    if kind == "ENUM":
        mapping = binding.conversion.get("parameters", {}).get("map", {})
        if value is None:
            return None, kind, None
        if value not in mapping:
            return None, kind, "INVALID_ENUM"
        return mapping[value], kind, None
    return None, kind, "CONVERSION_UNSUPPORTED"


def decide(basis: AcceptedAsBasis, ordinal: int, envelope_text: str) -> Decision:
    """One envelope against its batch's accepted-as basis. Pure and deterministic.

    W2-00: dispatch by stated schema only. V3 texts keep their frozen parse and decision; a V4 text (or a V4-only
    kind under V3) that the parser refuses is an ordinal refusal carrying its valid header's message ID.
    """
    digest = text_sha256(envelope_text)
    try:
        envelope = parse_canonical_source_envelope_text(envelope_text)
    except EnvelopeRejected as error:
        message_id = header_message_id(envelope_text) if uses_v4_header_path(envelope_text) else ""
        return Rejected(ordinal, message_id, error.kind, error.field, error.detail, digest)

    def reject(kind: str, field: str, detail: str) -> Rejected:
        return Rejected(ordinal, envelope.message_id, kind, field, detail, digest)

    if isinstance(envelope, SourceEnvelopeV4):
        return _decide_v4(basis, ordinal, envelope_text, digest, envelope, reject)
    if envelope.family != "MEASUREMENT":
        return reject("SCHEMA_UNSUPPORTED", "payload.family", f"{envelope.family} is not ingested in this release")
    binding = basis.bindings.get((envelope.device_id, envelope.signal_id))
    if binding is None or binding.source_id != envelope.source_id:
        return _unbound(basis, envelope, reject)
    source_time = parse_instant(envelope.source_time)
    refused = _outside_periods(basis, envelope, source_time, reject)
    if refused is not None:
        return refused
    if envelope.unit != binding.source_unit:
        return reject(
            "UNIT_INCOMPATIBLE", "payload.unit",
            f"{envelope.unit!r} is not the registered source unit {binding.source_unit!r}",
        )
    normalized, kind, refusal = _normalize(binding, envelope.value)
    if refusal == "INVALID_ENUM":
        return reject("INVALID_ENUM", "payload.value", f"{envelope.value!r} is not in the registered ENUM map")
    if refusal is not None:
        return reject("CONVERSION_UNSUPPORTED", "mapping", f"conversion {kind!r} is not applied in this release")
    return _accepted(basis, ordinal, envelope_text, digest, envelope, binding, normalized, binding.canonical_unit,
                     kind, source_time)


def _unbound(basis: AcceptedAsBasis, envelope, reject) -> Rejected:
    return reject(
        "BINDING_NOT_REGISTERED", "source.signal_id",
        f"binding set v{basis.binding_version} registers no channel {envelope.device_id}/{envelope.signal_id} "
        "for this source",
    )


def _outside_periods(basis: AcceptedAsBasis, envelope, source_time: datetime, reject) -> Rejected | None:
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
    return None


def _accepted(basis, ordinal, envelope_text, digest, envelope, binding, normalized, normalized_unit, kind,
              source_time) -> Accepted:
    return Accepted(
        ordinal=ordinal,
        envelope=envelope,
        envelope_text=envelope_text,
        envelope_sha256=digest,
        binding=binding,
        normalized_value_text=normalized,
        normalized_unit=normalized_unit,
        conversion_kind=kind,
        source_time=source_time,
        published_at=parse_instant(envelope.published_at),
        interval_start=None if envelope.interval_start is None else parse_instant(envelope.interval_start),
        interval_end=None if envelope.interval_end is None else parse_instant(envelope.interval_end),
        configuration_outdated=basis.outdated,
    )


def _decide_v4(basis: AcceptedAsBasis, ordinal: int, envelope_text: str, digest: str, envelope: SourceEnvelopeV4,
               reject) -> Decision:
    """Ruling 4: the exact closed channel tuple and the pinned row's v4 metadata must agree before acceptance."""
    binding = basis.bindings.get((envelope.device_id, envelope.signal_id))
    if binding is None or binding.source_id != envelope.source_id:
        return _unbound(basis, envelope, reject)
    entry = V4_CHANNEL_MAPPINGS.get((envelope.device_id, envelope.signal_id))
    pinned = binding.v4_metadata()
    if entry is None or pinned is None or pinned != entry.metadata():
        return reject(
            "MAPPING_INCOMPATIBLE", "mapping",
            f"channel {envelope.device_id}/{envelope.signal_id} has no V4 mapping entry that the closed "
            "simulator-lab-gateway-cold/1 table and the pinned binding row both state identically",
        )
    if entry.role is not None and binding.role != entry.role:
        # W2-01 (W2-00 review Low 2): the closed table names the role each channel serves.
        return reject("MAPPING_INCOMPATIBLE", "mapping",
                      f"channel {envelope.device_id}/{envelope.signal_id} serves {entry.role}, "
                      f"not the pinned binding's {binding.role}")
    carried = envelope.measurement or envelope.record_kind
    if envelope.family != entry.family or envelope.measurement != entry.measurement:
        return reject("MAPPING_INCOMPATIBLE", "mapping",
                      f"this channel does not carry {envelope.family} {carried}")
    if envelope.family == "EVENT":
        if envelope.record_kind not in pinned["allowed_record_kinds"]:
            return reject("MAPPING_INCOMPATIBLE", "mapping", f"{carried} is not a record kind of this channel")
        if envelope.outcome not in pinned["allowed_outcomes"].get(envelope.record_kind, []):
            return reject("MAPPING_INCOMPATIBLE", "mapping",
                          f"{envelope.outcome} is not an allowed {carried} outcome on this channel")
        if pinned["requires_correlation"] and envelope.correlation_id is None:
            return reject("CORRELATION_INVALID", "payload.correlation_id", "this channel requires correlation")
        if pinned["requires_session"] and envelope.session_id is None:
            return reject("CORRELATION_INVALID", "payload.session_id", "this channel requires a session ID")
    source_time = parse_instant(envelope.source_time)
    refused = _outside_periods(basis, envelope, source_time, reject)
    if refused is not None:
        return refused
    if envelope.unit is not None and (envelope.unit not in pinned["allowed_units"]
                                      or envelope.unit != binding.source_unit):
        return reject("UNIT_INCOMPATIBLE", "payload.unit",
                      f"{envelope.unit!r} is not this channel's registered unit {binding.source_unit!r}")
    ev_scoped = envelope.record_kind in EV_KINDS or envelope.measurement == "INTERVAL_DELTA"
    if ev_scoped and envelope.connector_id is not None and envelope.connector_id != binding.asset_code:
        return reject("EV_CONNECTOR_MISMATCH", "payload.connector_id",
                      f"{envelope.connector_id!r} is not the bound connector's public identifier")
    if envelope.family == "EVENT":
        if envelope.value is None:
            return _accepted(basis, ordinal, envelope_text, digest, envelope, binding, None, None, None, source_time)
        normalized, kind, refusal = _normalize(binding, envelope.value)
        if kind != "IDENTITY" or refusal is not None:
            return reject("CONVERSION_UNSUPPORTED", "mapping",
                          f"a quantitative event needs the IDENTITY conversion, not {kind!r}")
        return _accepted(basis, ordinal, envelope_text, digest, envelope, binding, normalized,
                         binding.canonical_unit, None, source_time)
    normalized, kind, refusal = _normalize(binding, envelope.value)
    if refusal == "INVALID_ENUM":
        return reject("INVALID_ENUM", "payload.value", f"{envelope.value!r} is not in the registered ENUM map")
    if refusal is not None:
        return reject("CONVERSION_UNSUPPORTED", "mapping", f"conversion {kind!r} is not applied in this release")
    return _accepted(basis, ordinal, envelope_text, digest, envelope, binding, normalized, binding.canonical_unit,
                     kind, source_time)


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
        completed_at: datetime,
    ) -> str:
        """Decide the next `limit` undecided ordinals in one transaction (S4-07).

        `completed_at` is the caller's application-clock receipt instant, written to the batch's
        `completed_at` only when this chunk completes it. It is never the decision instant: the adapter
        stamps each newly decided ordinal's `decided_at`, and a recompute job it inserts, with one
        database-time instant taken inside the chunk transaction after the batch row lock.
        """
        ...

    def receipt(self, principal: GatewayPrincipal, external_batch_id: str) -> IngestionReceiptV2 | None: ...
