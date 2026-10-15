"""Source clock attestations: the public proof that lets S3 order a channel by source time (LR-01 phase 1).

Authority: `D-2026-10-15-lr01-source-time-cohort` and `.agent/architect-LR-01-answers.md` (Q1-Q4, Follow-up M1).

An attestation is scoped to one tenant/Site/registered source/sequence epoch. It names its authority, the
proven maximum UTC error of the source clock (an admission ceiling of 60 seconds, not a claim about any
gateway) and a half-open validity interval `[valid_from, valid_to)`. It is stored as append-only events
(migration 0014): `RECORDED` (version 1), then `REPLACED` (new authority/error/validity), `EXPIRED` (validity
ended earlier) or `REVOKED` (no longer proof at all), each a new version of the same `attestation_id`.

The effective proof at a knowledge cutoff `k` is, per attestation, its latest version recorded at or before
`k`, unless that version is `REVOKED`. Reading as of `k` keeps every historical run's input digest stable.

LR-01 has no real-source path: the only proof class is `SIMULATED`, a labelled simulated attestation that is
recorded by the server-side SYSTEM attester for a simulated Site and covers only readings accepted with
`source_mode = SIMULATED`. `source_mode = SIMULATED` alone proves no clock. No Lab private truth is consulted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from assetops_backend.analytics.assessment_inputs import iso

#: The admission ceiling for source-time ordering (Q1). Proof with a larger error is refused at write and,
#: defensively, never used by the cohort.
MAX_UTC_ERROR = timedelta(seconds=60)

PROOF_SIMULATED = "SIMULATED"
PROOF_CLASSES = (PROOF_SIMULATED,)
EVENT_KINDS = ("RECORDED", "REPLACED", "EXPIRED", "REVOKED")
SYSTEM_CHANNELS = ("SYSTEM_CLI", "SYSTEM_FIXTURE")


@dataclass(frozen=True)
class AttesterPrincipal:
    """The stable server-side attester. Never taken from a request, a gateway credential or a CLI flag."""

    actor_id: str
    authorization_basis: str
    actor_kind: str = "SYSTEM"


SYSTEM_ATTESTER = AttesterPrincipal(
    actor_id="service:assetops-clock-attester",
    authorization_basis=("SERVER_ADMINISTRATIVE_TRIGGER: a labelled simulated clock attestation recorded by the "
                         "server-side attester run by an operator with database access; no real-source "
                         "attestation path exists in LR-01 (D-2026-10-15-lr01-source-time-cohort)"))


class AttestationRefused(Exception):
    """A typed refusal: `status` is the HTTP-equivalent code (403 authority, 404 scope, 409 conflict, 422 invalid)."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.status, self.code, self.message = status, code, message


@dataclass(frozen=True)
class ClockAttestation:
    """One stored attestation event; as an effective proof, the latest non-revoked version at a cutoff."""

    event_id: UUID
    attestation_id: UUID
    version: int
    event_kind: str
    source_id: UUID
    sequence_epoch: str
    proof_class: str
    authority: str
    label: str
    max_utc_error: timedelta
    valid_from: datetime
    valid_to: datetime
    recorded_at: datetime

    @property
    def ref(self) -> str:
        return f"{self.attestation_id}@v{self.version}"

    def covers(self, start: datetime, end: datetime) -> bool:
        """Whether `[start, end]` (a reading's measurement interval, or its instant) lies inside the validity."""
        return self.valid_from <= start and end < self.valid_to

    def touches(self, start: datetime, end: datetime) -> bool:
        return start < self.valid_to and self.valid_from <= end

    def payload(self) -> dict[str, Any]:
        """What an analytic input basis pins (the input digest covers it)."""
        return {"attestation_id": str(self.attestation_id), "version": self.version, "event_id": str(self.event_id),
                "event_kind": self.event_kind, "source_id": str(self.source_id),
                "sequence_epoch": self.sequence_epoch, "proof_class": self.proof_class, "authority": self.authority,
                "label": self.label, "max_utc_error_ms": int(self.max_utc_error / timedelta(milliseconds=1)),
                "valid_from": iso(self.valid_from), "valid_to": iso(self.valid_to)}


def effective_as_of(events: tuple[ClockAttestation, ...] | list[ClockAttestation],
                    knowledge_at: datetime) -> tuple[ClockAttestation, ...]:
    """Per attestation, the latest version recorded at or before `knowledge_at`, dropping a revoked one."""
    latest: dict[UUID, ClockAttestation] = {}
    for e in events:
        if e.recorded_at > knowledge_at:
            continue
        held = latest.get(e.attestation_id)
        if held is None or e.version > held.version:
            latest[e.attestation_id] = e
    return tuple(sorted((e for e in latest.values() if e.event_kind != "REVOKED"),
                        key=lambda e: (str(e.source_id), e.sequence_epoch, e.valid_from, str(e.attestation_id))))


@dataclass(frozen=True)
class AttestationChange:
    """One requested event. `RECORDED` starts a new attestation; the others name it and its expected version."""

    event_kind: str
    source_id: UUID
    sequence_epoch: str
    idempotency_key: str
    channel: str
    proof_class: str = PROOF_SIMULATED
    authority: str | None = None
    label: str | None = None
    max_utc_error: timedelta | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    attestation_id: UUID | None = None
    expected_version: int | None = None
    reason: str | None = None


def _zoned(value: datetime | None) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def validate_change(change: AttestationChange, principal: Any) -> None:
    """Shape and authority checks that need no stored state (the store checks scope and the prior version)."""
    def refuse(code: str, message: str, status: int = 422) -> None:
        raise AttestationRefused(status, code, message)

    if not isinstance(principal, AttesterPrincipal) or principal.actor_kind != "SYSTEM" \
            or principal != SYSTEM_ATTESTER:
        refuse("SYSTEM_ATTESTER_REQUIRED", "Only the server-side SYSTEM attester records a clock attestation; "
               "gateway credentials and client authorship are refused.", 403)
    if change.channel not in SYSTEM_CHANNELS:
        refuse("CHANNEL_NOT_SYSTEM", "Clock attestations are recorded only through the server-side SYSTEM channel.",
               403)
    if change.proof_class not in PROOF_CLASSES:
        refuse("REAL_SOURCE_PROOF_UNAVAILABLE", "Only a labelled SIMULATED attestation can be recorded in LR-01; "
               "real-source clock proof needs a separately validated path.", 403)
    if change.event_kind not in EVENT_KINDS:
        refuse("UNKNOWN_EVENT_KIND", f"event_kind must be one of {', '.join(EVENT_KINDS)}.")
    if not (change.idempotency_key or "").strip():
        refuse("IDEMPOTENCY_KEY_REQUIRED", "An idempotency key is required.")
    if not (change.sequence_epoch or "").strip():
        refuse("EPOCH_REQUIRED", "An attestation names one sequence epoch.")
    if change.event_kind == "RECORDED":
        if change.attestation_id is not None or change.expected_version is not None:
            refuse("RECORDED_IS_NEW", "RECORDED starts a new attestation; it names no prior attestation or version.")
    elif change.attestation_id is None or change.expected_version is None:
        refuse("PRIOR_REQUIRED", f"{change.event_kind} names the attestation and its expected current version.")
    if change.event_kind in ("RECORDED", "REPLACED"):
        if not (change.authority or "").strip():
            refuse("AUTHORITY_REQUIRED", "An attestation identifies its authority.")
        if not (change.label or "").strip():
            refuse("SIMULATED_LABEL_REQUIRED", "A simulated attestation carries an explicit simulated label.")
        if change.max_utc_error is None or change.max_utc_error < timedelta(0):
            refuse("ERROR_REQUIRED", "An attestation states its proven maximum UTC error.")
        if change.max_utc_error > MAX_UTC_ERROR:
            refuse("ERROR_ABOVE_CEILING", "The proven maximum UTC error exceeds the 60-second admission ceiling.")
        if not (_zoned(change.valid_from) and _zoned(change.valid_to)):
            refuse("VALIDITY_NOT_ZONED", "valid_from and valid_to must be timezone-aware instants.")
        if not change.valid_from < change.valid_to:
            refuse("VALIDITY_EMPTY", "valid_from must be before valid_to (half-open, non-empty).")
    if change.event_kind == "EXPIRED" and not _zoned(change.valid_to):
        refuse("VALIDITY_NOT_ZONED", "EXPIRED names the instant the validity now ends (valid_to).")
    if change.event_kind == "REVOKED" and not (change.reason or "").strip():
        refuse("REASON_REQUIRED", "A revocation states its reason.")


def next_event(change: AttestationChange, prior: ClockAttestation | None, *, event_id: UUID, attestation_id: UUID,
               recorded_at: datetime) -> ClockAttestation:
    """The stored event a validated change produces against the current version `prior` (None for RECORDED)."""
    if change.event_kind == "RECORDED":
        return ClockAttestation(event_id, attestation_id, 1, "RECORDED", change.source_id, change.sequence_epoch,
                                change.proof_class, change.authority.strip(), change.label.strip(),
                                change.max_utc_error, change.valid_from, change.valid_to, recorded_at)
    if prior is None:
        raise AttestationRefused(404, "ATTESTATION_UNKNOWN", "No attestation with that ID exists in this scope.")
    if prior.version != change.expected_version:
        raise AttestationRefused(409, "VERSION_CONFLICT", f"The attestation is at version {prior.version}, "
                                 f"not the expected {change.expected_version}.")
    if prior.event_kind == "REVOKED":
        raise AttestationRefused(409, "ATTESTATION_REVOKED", "A revoked attestation takes no further events.")
    if (prior.source_id, prior.sequence_epoch) != (change.source_id, change.sequence_epoch):
        raise AttestationRefused(409, "SCOPE_MISMATCH", "An attestation keeps its source and sequence epoch.")
    base = dict(event_id=event_id, attestation_id=prior.attestation_id, version=prior.version + 1,
                event_kind=change.event_kind, source_id=prior.source_id, sequence_epoch=prior.sequence_epoch,
                proof_class=prior.proof_class, authority=prior.authority, label=prior.label,
                max_utc_error=prior.max_utc_error, valid_from=prior.valid_from, valid_to=prior.valid_to,
                recorded_at=recorded_at)
    if change.event_kind == "REPLACED":
        base.update(authority=change.authority.strip(), label=change.label.strip(),
                    max_utc_error=change.max_utc_error, valid_from=change.valid_from, valid_to=change.valid_to)
    elif change.event_kind == "EXPIRED":
        if not prior.valid_from < change.valid_to < prior.valid_to:
            raise AttestationRefused(422, "EXPIRY_OUTSIDE_VALIDITY", "An expiry ends the validity strictly inside "
                                     "its current interval.")
        base.update(valid_to=change.valid_to)
    return ClockAttestation(**base)
