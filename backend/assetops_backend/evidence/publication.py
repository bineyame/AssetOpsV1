"""S4-05a phase 1: server-authorized pre-admission source publication.

`D-2026-10-15-s405-stored-demo-provenance`, `.agent/architect-S4-05-answers.md` Q1 and Follow-up M1. A
publication positively designates one exact Batch V2 commitment (tenant/Site, gateway/source, external batch
ID, canonical payload SHA-256) before it is admitted, as either

- `AUTHORED_DEMONSTRATION`: an authored fixture/spec ID **and version** that the server can read from its own
  spec registry (P01 and the authored P02 late-power fixture), or
- `REGISTERED_SIMULATION`: ordinary simulator output proved to come from one server-recorded run: the run's
  record (its ID and an identity digest computed here, never supplied by a client) and the exact sealed batch
  the registered gateway staged for that run.

The actor, authorization basis, channel and trigger are the server's own constants, never request text.
`SIMULATED`/`LIVE` mode, a gateway credential, client text, a Site/day match or a private manifest alone
designates nothing. Private scenario truth stays out of the record: only the run ID and its digest are kept.

There is no HTTP route for this command (rule 8 refuses one). The ledger writer stores the row under the same
transaction-scoped lock `open_batch` takes, and refuses registration once any admission of the batch exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from assetops_contracts.ingestion_batch_v2 import BatchRejected, parse_canonical_batch_v2_text
from assetops_contracts.source_envelope_v3 import parse_canonical_envelope_v3_text

AUTHORED_DEMONSTRATION = "AUTHORED_DEMONSTRATION"
REGISTERED_SIMULATION = "REGISTERED_SIMULATION"
SOURCE_CLASSES = (AUTHORED_DEMONSTRATION, REGISTERED_SIMULATION)
CHANNELS = ("SYSTEM_CLI", "SYSTEM_FIXTURE", "SYSTEM_LAB_RELEASE")



@dataclass(frozen=True)
class PublicationAuthority:
    """A stable server-side SYSTEM principal. Never taken from a request or a command-line flag."""

    actor_id: str
    authorization_basis: str
    channel: str
    trigger: str
    actor_kind: str = "SYSTEM"


FIXTURE_PUBLISHER = PublicationAuthority(
    actor_id="service:assetops-source-publisher",
    authorization_basis=("SERVER_ADMINISTRATIVE_TRIGGER: authored fixture publication run by an operator with "
                         "database access; no human sign-in exists yet (D-2026-10-15-s405-stored-demo-provenance)"),
    channel="SYSTEM_CLI",
    trigger="AUTHORED_FIXTURE_PUBLICATION",
)
LAB_RELEASE_PUBLISHER = PublicationAuthority(
    actor_id="service:assetops-lab-release",
    authorization_basis=("SERVER_LAB_RELEASE: registered-run release verified against the server run record and "
                         "the registered gateway's sealed stage (D-2026-10-15-s405-stored-demo-provenance)"),
    channel="SYSTEM_LAB_RELEASE",
    trigger="REGISTERED_RUN_RELEASE",
)


class PublicationRefused(Exception):
    """A registration the server will not record. Nothing was written."""

    def __init__(self, kind: str, detail: str) -> None:
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


class PublicationMismatch(Exception):
    """`open_batch` found a publication for this batch slot whose commitment differs from the upload."""

    def __init__(self, publication_id: UUID, detail: str) -> None:
        super().__init__(detail)
        self.publication_id = publication_id
        self.detail = detail


@dataclass(frozen=True)
class PublicationRecord:
    """Everything one `evidence_publication` row pins. Built only by this module."""

    tenant_id: UUID
    site_id: UUID
    gateway_id: UUID
    source_id: UUID
    external_batch_id: str
    payload_sha256: str
    source_class: str
    fixture_id: str | None
    fixture_version: str | None
    run_id: str | None
    run_identity_sha256: str | None
    authority: PublicationAuthority
    publication_id: UUID | None = None  # an explicit ID for an idempotent retry; the ledger allocates otherwise


@dataclass(frozen=True)
class Registered:
    publication_id: UUID
    created: bool  # False for an identical retry, which returns the stored ID


class PublicationLedger(Protocol):
    def register_publication(self, record: PublicationRecord) -> Registered: ...


class FixtureSpecs(Protocol):
    """The server's authored fixture registry (`adapters/authored_fixture_specs.py`).

    `declared(id)` is the (spec ID, version) the server's own spec file declares, None for an ID outside the
    registry; it raises `PublicationRefused("FIXTURE_UNREADABLE")` when the file cannot be read.
    """

    def declared(self, fixture_id: str) -> tuple[str, str] | None: ...


@dataclass(frozen=True)
class StagedBatch:
    """One sealed batch the registered gateway staged for a run (read from the gateway ledger)."""

    batch_id: str
    payload_text: str
    sha256: str
    message_ids: tuple[str, ...]


@dataclass(frozen=True)
class RunAttestation:
    """A server-recorded run and the exact batches its registered gateway sealed for it.

    Built by `runs/source_publication.py` from the run store's record and the gateway Stage read; the
    evidence package never imports either.
    """

    run_id: str
    run_identity_sha256: str
    tenant_id: str
    site_id: str
    snapshot_sha256: str
    stage_run_id: str
    stage_status: str
    run_message_ids: frozenset[str]
    batches: tuple[StagedBatch, ...]


def _parse(batch_text: str):
    try:
        return parse_canonical_batch_v2_text(batch_text)
    except BatchRejected as error:
        raise PublicationRefused("BATCH_UNREADABLE", f"{error.kind} at {error.field}: {error.detail}") from None


def _authority(authority: PublicationAuthority) -> PublicationAuthority:
    if authority.actor_kind != "SYSTEM" or authority.channel not in CHANNELS:
        raise PublicationRefused("SYSTEM_PRINCIPAL_REQUIRED", "only a server SYSTEM principal may designate a source")
    return authority


def _uuid(value: str, field: str) -> UUID:
    try:
        return UUID(value)
    except (TypeError, ValueError):
        raise PublicationRefused("BATCH_UNREADABLE", f"{field} is not a UUID") from None


def _fixture_declared(specs: FixtureSpecs, fixture_id: str, fixture_version: str) -> None:
    declared = specs.declared(fixture_id)
    if declared is None:
        raise PublicationRefused("FIXTURE_UNKNOWN", f"{fixture_id!r} is not an authored fixture on this server")
    if declared != (fixture_id, fixture_version):
        raise PublicationRefused(
            "FIXTURE_VERSION_MISMATCH",
            f"the server's spec declares {declared[0]} v{declared[1]}, not {fixture_id} v{fixture_version}")


def authored_record(
    specs: FixtureSpecs,
    tenant_id: UUID,
    batch_text: str,
    *,
    fixture_id: str,
    fixture_version: str,
    authority: PublicationAuthority = FIXTURE_PUBLISHER,
    publication_id: UUID | None = None,
) -> PublicationRecord:
    """The record for one authored fixture batch: the spec must be the server's, the bytes canonical Batch V2.

    The digest is recomputed from the bytes (the parser refuses a stated digest that differs); a client
    digest is never taken.
    """
    _authority(authority)
    _fixture_declared(specs, fixture_id, fixture_version)
    batch = _parse(batch_text)
    return PublicationRecord(
        tenant_id=tenant_id, site_id=_uuid(batch.site_id, "site_id"), gateway_id=_uuid(batch.gateway_id, "gateway_id"),
        source_id=_uuid(batch.source_id, "source_id"), external_batch_id=batch.batch_id,
        payload_sha256=batch.payload_sha256, source_class=AUTHORED_DEMONSTRATION, fixture_id=fixture_id,
        fixture_version=fixture_version, run_id=None, run_identity_sha256=None, authority=authority,
        publication_id=publication_id,
    )


def simulation_records(
    attestation: RunAttestation, *, authority: PublicationAuthority = LAB_RELEASE_PUBLISHER
) -> tuple[PublicationRecord, ...]:
    """One record per sealed batch the run's registered gateway staged, each proved to be that run's output.

    Refuses unless the Stage read is this run's and fully `STAGED`, and each batch's bytes re-parse to the
    stated digest, carry exactly the run's registered tenant/Site and pinned snapshot, and hold only messages
    the run staged. The gateway's `SIMULATED` registration is checked by the ledger under its lock.
    """
    _authority(authority)
    if attestation.stage_run_id != attestation.run_id:
        raise PublicationRefused("RUN_STAGE_MISMATCH", "the Stage read belongs to another run")
    if attestation.stage_status != "STAGED" or not attestation.batches:
        raise PublicationRefused("RUN_NOT_STAGED", f"the run's Stage is {attestation.stage_status}, not fully sealed")
    records = []
    for staged in attestation.batches:
        batch = _parse(staged.payload_text)
        if batch.batch_id != staged.batch_id or batch.payload_sha256 != staged.sha256:
            raise PublicationRefused("RUN_BATCH_MISMATCH", f"staged batch {staged.batch_id} bytes do not match its record")
        if batch.site_id != attestation.site_id:
            raise PublicationRefused("RUN_SCOPE_MISMATCH", f"batch {staged.batch_id} names another Site than the run")
        if batch.snapshot_sha256 != attestation.snapshot_sha256:
            raise PublicationRefused("RUN_SNAPSHOT_MISMATCH",
                                     f"batch {staged.batch_id} was sealed against another binding snapshot")
        messages = tuple(parse_canonical_envelope_v3_text(e).message_id for e in batch.envelopes)
        if messages != staged.message_ids or not set(messages) <= attestation.run_message_ids:
            raise PublicationRefused("RUN_BATCH_FOREIGN", f"batch {staged.batch_id} holds messages the run did not stage")
        records.append(PublicationRecord(
            tenant_id=_uuid(attestation.tenant_id, "tenant_id"), site_id=_uuid(batch.site_id, "site_id"),
            gateway_id=_uuid(batch.gateway_id, "gateway_id"), source_id=_uuid(batch.source_id, "source_id"),
            external_batch_id=batch.batch_id, payload_sha256=batch.payload_sha256,
            source_class=REGISTERED_SIMULATION, fixture_id=None, fixture_version=None, run_id=attestation.run_id,
            run_identity_sha256=attestation.run_identity_sha256, authority=authority,
        ))
    return tuple(records)


def register_authored(ledger: PublicationLedger, specs: FixtureSpecs, tenant_id: UUID, batch_text: str, *,
                      fixture_id: str, fixture_version: str, publication_id: UUID | None = None) -> Registered:
    return ledger.register_publication(authored_record(
        specs, tenant_id, batch_text, fixture_id=fixture_id, fixture_version=fixture_version, publication_id=publication_id))


def register_run(ledger: PublicationLedger, attestation: RunAttestation) -> tuple[Registered, ...]:
    """Register every sealed batch of one run. Each batch is its own lock/transaction; a refusal stops the rest."""
    return tuple(ledger.register_publication(record) for record in simulation_records(attestation))
