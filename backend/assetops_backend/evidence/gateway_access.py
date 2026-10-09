"""Gateway upload credentials, principal resolution and central diagnostics (S2-02 phase 2).

`D-2026-10-09-s2-pilot-gateway-upload-credential`: one opaque high-entropy
bearer credential per registered gateway, over TLS, for Batch V2 and
GatewayDiagnosticsV1 upload. The raw secret is shown once at issue and written
only into protected gateway configuration; the server keeps a public selector
and a one-way verifier. The principal is derived from the credential row and
the immutable gateway registration only; caller-supplied IDs and mode are
claims compared against it.

Diagnostics (`D-2026-10-09-s2-gateway-diagnostic-semantics`) are operational
records: never AcceptedEvidence, asset health or proof of physical contact.
Central freshness comes from the server's `received_at` and the registered
declared cadence, never from the gateway or Lab virtual clock.

This module is pure: no SQL, no driver. Persistence is the
`GatewayAccessStore` port, implemented in `adapters/postgres_gateway_access.py`.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol
from uuid import UUID

from assetops_backend.evidence.ledger import (
    GatewayPrincipal,
    LedgerUnavailable,
    PrincipalRefused,
)
from assetops_contracts.gateway_diagnostics import (
    MAX_DIAGNOSTIC_BYTES,
    DiagnosticRejected,
    GatewayDiagnosticsV1,
    parse_canonical_gateway_diagnostics_v1_text,
)

CREDENTIAL_PREFIX = "aog1"
_TOKEN = re.compile(r"aog1\.([0-9a-f]{32})\.([A-Za-z0-9_-]{43})")
_VERIFIER_DOMAIN = b"assetops.gateway-credential/1\n"

#: A gateway is CURRENT while its last diagnostic was received within this many
#: declared cadences. Emission is at most one per cadence slot at any point in
#: the slot, so two consecutive receipts can be up to two cadences apart.
FRESHNESS_CADENCES = 2


# --- credentials -----------------------------------------------------------------


@dataclass(frozen=True)
class IssuedCredential:
    """Returned once by issue; `token` is the only copy of the secret."""

    selector: str
    token: str
    verifier_sha256: str


def credential_verifier(selector: str, secret: str) -> str:
    """One-way verifier. The secret is 256 random bits, so a keyed slow hash adds nothing."""
    return hashlib.sha256(_VERIFIER_DOMAIN + selector.encode("ascii") + b"\n" + secret.encode("ascii")).hexdigest()


def new_credential() -> IssuedCredential:
    selector = secrets.token_hex(16)
    secret = secrets.token_urlsafe(32)  # 43 url-safe characters, 256 bits
    return IssuedCredential(
        selector=selector,
        token=f"{CREDENTIAL_PREFIX}.{selector}.{secret}",
        verifier_sha256=credential_verifier(selector, secret),
    )


def redact(token: str) -> str:
    """The loggable form of a credential: prefix and selector, never the secret."""
    match = _TOKEN.fullmatch(token)
    return f"{CREDENTIAL_PREFIX}.{match.group(1)}.<redacted>" if match else "<redacted>"


@dataclass(frozen=True)
class CredentialRecord:
    """The stored credential joined to its gateway's current registration row."""

    selector: str
    verifier_sha256: str
    revoked: bool
    tenant_id: UUID
    site_id: UUID
    gateway_id: UUID
    gateway_mode: str
    gateway_disabled: bool


@dataclass(frozen=True)
class SourceRegistration:
    source_id: UUID
    gateway_id: UUID
    site_id: UUID
    disabled: bool


@dataclass(frozen=True)
class StoredDiagnostic:
    diagnostic_id: UUID
    gateway_id: UUID
    sequence_epoch: str
    diagnostic_sequence: int
    payload_sha256: str
    diagnostic_text: str
    received_at: datetime


class DiagnosticIdentityConflict(Exception):
    def __init__(self, existing: StoredDiagnostic) -> None:
        super().__init__("diagnostic identity reused with different bytes")
        self.existing = existing


@dataclass(frozen=True)
class GatewayHealthFacts:
    gateway_id: UUID
    gateway_external_id: str
    mode: str
    disabled: bool
    cadence_seconds: int
    sources: tuple[tuple[UUID, str, bool], ...]  # (source_id, external id, disabled)
    latest: StoredDiagnostic | None
    latest_fields: dict | None


class GatewayAccessStore(Protocol):
    def credential(self, selector: str) -> CredentialRecord | None: ...

    def sources(self, tenant_id: UUID, source_ids: tuple[UUID, ...]) -> dict[UUID, SourceRegistration]: ...

    def find_diagnostic(self, principal: GatewayPrincipal, epoch: str, sequence: int) -> StoredDiagnostic | None: ...

    def insert_diagnostic(
        self, principal: GatewayPrincipal, diagnostic: GatewayDiagnosticsV1, text: str, received_at: datetime
    ) -> tuple[StoredDiagnostic, bool]:
        """Insert or return the existing identical row (created flag); raise
        `DiagnosticIdentityConflict` when the identity holds different bytes."""

    def record_diagnostic_refusal(
        self, principal: GatewayPrincipal, *, epoch: str | None, sequence: int | None,
        payload_sha256: str, kind: str, field: str, detail: str, received_at: datetime,
    ) -> UUID: ...

    def gateway_health(self, tenant_id: UUID, site_id: UUID) -> list[GatewayHealthFacts]: ...


class ProvisioningRefused(Exception):
    """An operator provisioning step named something that is not registered."""


class StoreGatewayPrincipals:
    """The network `GatewayPrincipalResolver`: bearer credential -> registered principal.

    401 for a missing, malformed, unknown, revoked or mismatched credential (one
    message, so a probe learns nothing about which); 403 for a valid credential
    whose gateway is disabled. Revocation and disable take effect on the next
    request because nothing is cached."""

    def __init__(self, store: GatewayAccessStore) -> None:
        self._store = store

    def resolve(self, authorization: str | None) -> GatewayPrincipal:
        if not authorization or not authorization.startswith("Bearer "):
            raise PrincipalRefused(401, "GATEWAY_CREDENTIAL_REQUIRED", "A registered gateway bearer credential is required.")
        match = _TOKEN.fullmatch(authorization[len("Bearer "):])
        if match is None:
            raise _invalid()
        selector, secret = match.group(1), match.group(2)
        record = self._store.credential(selector)
        presented = credential_verifier(selector, secret)
        if record is None or record.revoked or not hmac.compare_digest(presented, record.verifier_sha256):
            raise _invalid()
        if record.gateway_disabled:
            raise PrincipalRefused(403, "GATEWAY_DISABLED", "The registered gateway is disabled.")
        return GatewayPrincipal(
            tenant_id=record.tenant_id, site_id=record.site_id,
            gateway_id=record.gateway_id, mode=record.gateway_mode,
        )


def _invalid() -> PrincipalRefused:
    return PrincipalRefused(401, "GATEWAY_CREDENTIAL_INVALID", "The gateway credential is not valid.")


# --- diagnostics -----------------------------------------------------------------


class DiagnosticRefused(Exception):
    def __init__(self, status: int, code: str, kind: str, field: str, detail: str,
                 refusal_id: UUID | None = None) -> None:
        super().__init__(detail)
        self.status, self.code, self.kind, self.field, self.detail = status, code, kind, field, detail
        self.refusal_id = refusal_id


@dataclass(frozen=True)
class DiagnosticReceipt:
    status: int  # 201 created, 200 identical retry
    diagnostic_id: UUID
    received_at: datetime
    payload_sha256: str


def _uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None


class DiagnosticIngestionService:
    def __init__(self, store: GatewayAccessStore, clock: Callable[[], datetime]) -> None:
        self._store = store
        self._clock = clock

    def submit(self, principal: GatewayPrincipal, path_gateway_id: str, raw: bytes) -> DiagnosticReceipt:
        if _uuid(path_gateway_id) != principal.gateway_id:
            raise DiagnosticRefused(403, "GATEWAY_SCOPE_MISMATCH", "SCOPE", "gateway_id",
                                    "the path gateway is not the authenticated gateway")
        received_at = self._clock()
        if len(raw) > MAX_DIAGNOSTIC_BYTES:
            raise DiagnosticRefused(413, "DIAGNOSTIC_REFUSED", "TOO_LARGE", "diagnostic",
                                    f"more than {MAX_DIAGNOSTIC_BYTES} bytes")
        digest = hashlib.sha256(raw).hexdigest()
        try:
            text = raw.decode("utf-8")
            diagnostic = parse_canonical_gateway_diagnostics_v1_text(text)
        except (UnicodeDecodeError, DiagnosticRejected) as error:
            kind = getattr(error, "kind", "MALFORMED_TEXT")
            field = getattr(error, "field", "diagnostic")
            detail = getattr(error, "detail", "not UTF-8")
            refusal = self._store.record_diagnostic_refusal(
                principal, epoch=None, sequence=None, payload_sha256=digest,
                kind=kind, field=field, detail=detail, received_at=received_at)
            raise DiagnosticRefused(422, "DIAGNOSTIC_REFUSED", kind, field, detail, refusal) from error
        # Claims are compared with the authenticated registration (403, no row).
        if _uuid(diagnostic.gateway_id) != principal.gateway_id:
            raise DiagnosticRefused(403, "GATEWAY_SCOPE_MISMATCH", "SCOPE", "gateway_id",
                                    "the diagnostic names another gateway")
        if _uuid(diagnostic.site_id) != principal.site_id:
            raise DiagnosticRefused(403, "GATEWAY_SCOPE_MISMATCH", "SCOPE", "site_id",
                                    "the diagnostic names another Site")
        source_ids: list[UUID] = []
        for source_text, _ in diagnostic.last_device_contact_by_source:
            source_id = _uuid(source_text)
            if source_id is None:
                raise DiagnosticRefused(403, "SOURCE_NOT_REGISTERED", "SCOPE", "last_device_contact_by_source",
                                        f"{source_text!r} is not a registered source")
            source_ids.append(source_id)
        registered = self._store.sources(principal.tenant_id, tuple(source_ids))
        for source_id in source_ids:
            reg = registered.get(source_id)
            # A disabled source keeps its historical contact; affiliation must still hold.
            if reg is None or reg.gateway_id != principal.gateway_id or reg.site_id != principal.site_id:
                raise DiagnosticRefused(403, "SOURCE_NOT_AFFILIATED", "SCOPE", "last_device_contact_by_source",
                                        f"source {source_id} is not registered to this gateway and Site")
        try:
            stored, created = self._store.insert_diagnostic(principal, diagnostic, text, received_at)
        except DiagnosticIdentityConflict as conflict:
            refusal = self._store.record_diagnostic_refusal(
                principal, epoch=diagnostic.sequence_epoch, sequence=diagnostic.diagnostic_sequence,
                payload_sha256=digest, kind="IDENTITY_CONFLICT", field="diagnostic_sequence",
                detail=f"identity holds diagnostic {conflict.existing.diagnostic_id} with different bytes",
                received_at=received_at)
            raise DiagnosticRefused(409, "DIAGNOSTIC_CONFLICT", "IDENTITY_CONFLICT", "diagnostic_sequence",
                                    "the same epoch and diagnostic sequence were stored with different bytes",
                                    refusal) from None
        return DiagnosticReceipt(
            status=201 if created else 200, diagnostic_id=stored.diagnostic_id,
            received_at=stored.received_at, payload_sha256=stored.payload_sha256,
        )


def _z(instant: datetime | None) -> str | None:
    return None if instant is None else instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def freshness(received_at: datetime | None, cadence_seconds: int, now: datetime) -> str:
    """`CURRENT|STALE|UNKNOWN` from server receive time only."""
    if received_at is None:
        return "UNKNOWN"
    return "CURRENT" if now - received_at <= timedelta(seconds=FRESHNESS_CADENCES * cadence_seconds) else "STALE"


def gateway_health_document(facts: list[GatewayHealthFacts], site_id: UUID, now: datetime) -> dict:
    """The Site gateway-health read. Operational only: no asset or device health claim."""
    gateways = []
    for g in facts:
        latest = g.latest_fields
        contacts = dict(latest["last_device_contact_by_source"]) if latest else {}
        gateways.append({
            "gateway_id": str(g.gateway_id),
            "gateway_external_id": g.gateway_external_id,
            "mode": g.mode,
            "registration": "DISABLED" if g.disabled else "ENABLED",
            "declared_cadence_seconds": g.cadence_seconds,
            "status": freshness(None if g.latest is None else g.latest.received_at, g.cadence_seconds, now),
            "status_basis": "SERVER_RECEIVED_AT",
            "last_server_contact": _z(None if g.latest is None else g.latest.received_at),
            "diagnostic_id": None if g.latest is None else str(g.latest.diagnostic_id),
            "gateway_observed_at": None if latest is None else latest["observed_at"],
            "observed_at_clock": "GATEWAY_REAL_UTC",
            "queue_count": None if latest is None else latest["queue_count"],
            "oldest_queue_age_seconds": None if latest is None else latest["oldest_queue_age_seconds"],
            "disk_pressure": None if latest is None else latest["disk_pressure"],
            "disk_pressure_provenance": (
                None if latest is None else
                "REPORTED_SIMULATED_GATEWAY" if g.mode == "SIMULATED" else "REPORTED_GATEWAY"),
            "clock_offset_ms": None if latest is None else latest["clock_offset_ms"],
            "mapping_error_count": None if latest is None else latest["mapping_error_count"],
            "source_contacts": [
                {
                    "source_id": str(source_id),
                    "source_external_id": external,
                    "registration": "DISABLED" if disabled else "ENABLED",
                    "last_contact": contacts.get(str(source_id)),
                    "contact_provenance": (
                        "OBSERVED_SIMULATED_REPORT" if g.mode == "SIMULATED" else "OBSERVED_REPORT"),
                }
                for source_id, external, disabled in g.sources
            ],
        })
    return {
        "site_id": str(site_id),
        "read_at": _z(now),
        "read_at_clock": "SERVER_REAL_UTC",
        "claim_scope": "GATEWAY_OPERATIONAL_REPORT",
        "gateways": gateways,
    }


__all__ = [
    "CredentialRecord", "DiagnosticIdentityConflict", "DiagnosticIngestionService", "DiagnosticReceipt",
    "DiagnosticRefused", "ProvisioningRefused", "GatewayAccessStore", "GatewayHealthFacts", "IssuedCredential", "LedgerUnavailable",
    "SourceRegistration", "StoreGatewayPrincipals", "StoredDiagnostic", "credential_verifier",
    "freshness", "gateway_health_document", "new_credential", "redact",
]
