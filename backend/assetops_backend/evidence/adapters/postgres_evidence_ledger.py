"""The central evidence ledger's PostgreSQL adapter (S2-02 phase 1).

The sole writer of the ledger tables created by migration 0005
(`ingestion_batch`, `accepted_evidence`, `evidence_rejection`,
`ingestion_disposition`, `batch_refusal`, `recompute_job`). It writes no
registration or configuration row; it only reads them. Every statement is
scoped by the authenticated principal's tenant and Site.

Each chunk is one short READ COMMITTED transaction: lock the batch row, read the
persisted watermark, decide the next ordinals, insert each decision with its
disposition, advance counters/status and coalesce the recompute job, commit.
The message-key unique constraint arbitrates concurrent duplicate deliveries.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Callable, Sequence
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError

from assetops_backend.evidence.ledger import (
    RECOMPUTE_DOMAIN,
    Accepted,
    AcceptedAsBasis,
    BatchHandle,
    Decision,
    GatewayPrincipal,
    LedgerUnavailable,
    RegisteredScope,
    Rejected,
    StoredBindingSet,
    recompute_window,
)
from assetops_backend.evidence.publication import (
    REGISTERED_SIMULATION,
    PublicationMismatch,
    PublicationRecord,
    PublicationRefused,
    Registered,
)
from assetops_backend.evidence.source_provenance import LinkRow
from assetops_contracts.ingestion_receipt_v2 import (
    IngestionReceiptV2,
    ReceiptCounts,
    ReceiptDisposition,
    ReceiptRejection,
)


def _instant(value: datetime | None) -> str | None:
    """Server real-UTC instant text with exactly six fractional digits (Receipt V2)."""
    return None if value is None else value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def admission_lock_key(tenant_id: UUID, site_id: UUID, external_batch_id: str) -> int:
    """The signed 64-bit advisory-lock key of one Site batch slot (S4-05a contract 2).

    Registration and `open_batch` take this same transaction-scoped lock. The slot is the admission
    uniqueness scope (`ingestion_batch_external_unique` is Site + external batch ID), so every gateway/source
    contending for the slot serializes; gateway, source and digest are then compared under the lock.
    """
    material = f"assetops.batch-admission|{tenant_id}|{site_id}|{external_batch_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big", signed=True)


def _lock_slot(c: Connection, tenant_id: UUID, site_id: UUID, external_batch_id: str) -> None:
    c.execute(text("SELECT pg_advisory_xact_lock(:k)"),
              {"k": admission_lock_key(tenant_id, site_id, external_batch_id)})


_PUBLICATION_COLUMNS = (
    "id, tenant_id, site_id, gateway_id, source_id, external_batch_id, payload_sha256, source_class, fixture_id, "
    "fixture_version, run_id, run_identity_sha256, actor_kind, actor_id, authorization_basis, channel, "
    "publication_trigger, recorded_at"
)


def _uuid_or_none(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None


class PostgresEvidenceLedger:
    """`EvidenceLedger` over a migrated PostgreSQL database."""

    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

    def _connect_engine(self) -> Engine:
        if not self._database_url:
            raise LedgerUnavailable("DATABASE_URL is not set, so the evidence ledger cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def _run(self, work, *, write: bool = False):
        engine = self._connect_engine()
        try:
            if write:
                with engine.begin() as connection:
                    return work(connection)
            with engine.connect() as connection:
                return work(connection)
        except (OperationalError, ProgrammingError) as error:
            raise LedgerUnavailable(f"The evidence ledger could not be read or written: {error.orig}") from error
        except DBAPIError as error:
            if error.connection_invalidated:
                raise LedgerUnavailable(str(error.orig)) from error
            raise

    # --- registered scope ---------------------------------------------------

    def registered_scope(self, principal: GatewayPrincipal, source_id: str) -> RegisteredScope:
        source_uuid = _uuid_or_none(source_id)

        def work(c: Connection) -> RegisteredScope:
            gateway = c.execute(
                text("SELECT site_id, mode, disabled_at FROM gateway WHERE tenant_id = :t AND id = :g"),
                {"t": principal.tenant_id, "g": principal.gateway_id},
            ).first()
            source = None
            if source_uuid is not None:
                source = c.execute(
                    text("SELECT gateway_id, site_id, disabled_at FROM source WHERE tenant_id = :t AND id = :s"),
                    {"t": principal.tenant_id, "s": source_uuid},
                ).first()
            return RegisteredScope(
                gateway_site_id=None if gateway is None else gateway.site_id,
                gateway_mode=None if gateway is None else gateway.mode,
                gateway_disabled=gateway is not None and gateway.disabled_at is not None,
                source_gateway_id=None if source is None else source.gateway_id,
                source_site_id=None if source is None else source.site_id,
                source_disabled=source is not None and source.disabled_at is not None,
            )

        return self._run(work)

    def binding_set(
        self, principal: GatewayPrincipal, binding_set_id: str, binding_version: int
    ) -> StoredBindingSet | None:
        set_uuid = _uuid_or_none(binding_set_id)
        if set_uuid is None:
            return None

        def work(c: Connection) -> StoredBindingSet | None:
            row = c.execute(
                text(
                    "SELECT s.id, s.foundation_revision_id, s.snapshot_sha256, s.snapshot_canonical, "
                    "s.superseded_at IS NOT NULL AS set_superseded, "
                    "f.superseded_at IS NOT NULL AS foundation_superseded "
                    "FROM signal_binding_set_revision s "
                    "JOIN foundation_revision f ON f.id = s.foundation_revision_id AND f.site_id = s.site_id "
                    "WHERE s.tenant_id = :t AND s.site_id = :site AND s.binding_set_id = :b AND s.version = :v"
                ),
                {"t": principal.tenant_id, "site": principal.site_id, "b": set_uuid, "v": binding_version},
            ).first()
            if row is None:
                return None
            return StoredBindingSet(
                binding_set_revision_id=row.id,
                foundation_revision_id=row.foundation_revision_id,
                snapshot_sha256=row.snapshot_sha256,
                snapshot_canonical=bytes(row.snapshot_canonical),
                set_superseded=row.set_superseded,
                foundation_superseded=row.foundation_superseded,
            )

        return self._run(work)

    # --- refusals -----------------------------------------------------------

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
    ) -> UUID:
        def work(c: Connection) -> UUID:
            inserted = c.execute(
                text(
                    "INSERT INTO batch_refusal (id, tenant_id, site_id, gateway_id, external_batch_id, "
                    "payload_sha256, kind, field, detail, received_at) "
                    "VALUES (:id, :t, :site, :g, :b, :sha, :kind, :field, :detail, :at) "
                    "ON CONFLICT ON CONSTRAINT batch_refusal_identity DO NOTHING RETURNING id"
                ),
                {
                    "id": uuid4(), "t": principal.tenant_id, "site": principal.site_id,
                    "g": principal.gateway_id, "b": external_batch_id, "sha": payload_sha256,
                    "kind": kind, "field": field, "detail": detail, "at": received_at,
                },
            ).first()
            if inserted is not None:
                return inserted.id
            return c.execute(
                text(
                    "SELECT id FROM batch_refusal WHERE tenant_id = :t AND site_id = :site "
                    "AND external_batch_id IS NOT DISTINCT FROM :b AND payload_sha256 = :sha AND kind = :kind"
                ),
                {"t": principal.tenant_id, "site": principal.site_id, "b": external_batch_id,
                 "sha": payload_sha256, "kind": kind},
            ).scalar_one()

        return self._run(work, write=True)

    # --- batches ------------------------------------------------------------

    def find_batch(self, principal: GatewayPrincipal, external_batch_id: str) -> BatchHandle | None:
        def work(c: Connection) -> BatchHandle | None:
            row = c.execute(
                text(
                    "SELECT id, payload_sha256, status FROM ingestion_batch "
                    "WHERE tenant_id = :t AND site_id = :site AND external_batch_id = :b"
                ),
                {"t": principal.tenant_id, "site": principal.site_id, "b": external_batch_id},
            ).first()
            return None if row is None else BatchHandle(row.id, row.payload_sha256, row.status)

        return self._run(work)

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
    ) -> BatchHandle:
        def work(c: Connection) -> BatchHandle:
            # S4-05a: the same slot lock registration takes; the preauthorized commitment is read under it.
            _lock_slot(c, principal.tenant_id, principal.site_id, external_batch_id)
            publication = c.execute(
                text(
                    "SELECT id, gateway_id, source_id, payload_sha256 FROM evidence_publication "
                    "WHERE tenant_id = :t AND site_id = :site AND external_batch_id = :b"
                ),
                {"t": principal.tenant_id, "site": principal.site_id, "b": external_batch_id},
            ).first()
            source_uuid = UUID(source_id)
            if publication is not None and (
                    publication.gateway_id != principal.gateway_id or publication.source_id != source_uuid
                    or publication.payload_sha256 != payload_sha256):
                raise PublicationMismatch(
                    publication.id,
                    "this batch ID was published for another gateway, source or payload digest; it is not admitted")
            new_id = uuid4()
            inserted = c.execute(
                text(
                    "INSERT INTO ingestion_batch (id, tenant_id, site_id, gateway_id, source_id, external_batch_id, "
                    "payload_sha256, schema_version, source_mode, foundation_revision_id, binding_set_revision_id, "
                    "snapshot_sha256, batch_text, status, total_count, received_at) "
                    "VALUES (:id, :t, :site, :g, :src, :b, :sha, 2, :mode, :f, :bs, :snap, :body, 'IN_PROGRESS', "
                    ":total, :at) ON CONFLICT ON CONSTRAINT ingestion_batch_external_unique DO NOTHING RETURNING id"
                ),
                {
                    "id": new_id, "t": principal.tenant_id, "site": principal.site_id, "g": principal.gateway_id,
                    "src": source_uuid, "b": external_batch_id, "sha": payload_sha256, "mode": source_mode,
                    "f": basis.foundation_revision_id, "bs": basis.binding_set_revision_id,
                    "snap": basis.snapshot_sha256, "body": batch_text, "total": total, "at": received_at,
                },
            ).first()
            if inserted is not None and publication is not None:
                # Bound only here, in the admission transaction that inserts the batch; never afterwards.
                c.execute(
                    text("INSERT INTO batch_publication_link (batch_id, publication_id, tenant_id, site_id, gateway_id, source_id, external_batch_id, payload_sha256, linked_at) VALUES (:batch, :pub, :t, :site, :g, :src, :b, :sha, :at)"),
                    {"batch": new_id, "pub": publication.id, "t": principal.tenant_id, "site": principal.site_id,
                     "g": principal.gateway_id, "src": source_uuid, "b": external_batch_id, "sha": payload_sha256,
                     "at": received_at},
                )
            row = c.execute(
                text(
                    "SELECT id, payload_sha256, status FROM ingestion_batch "
                    "WHERE tenant_id = :t AND site_id = :site AND external_batch_id = :b"
                ),
                {"t": principal.tenant_id, "site": principal.site_id, "b": external_batch_id},
            ).one()
            return BatchHandle(row.id, row.payload_sha256, row.status)

        return self._run(work, write=True)

    def register_publication(self, record: PublicationRecord) -> Registered:
        """Record one pre-admission publication (S4-05a contract 1-2). Refusals write nothing.

        Under the slot lock: refuse once any admission of the slot exists (even a partial one); an identical
        retry returns the stored ID; a different commitment for the slot, or a reused publication ID, fails.
        The gateway/source registration is re-read here; `REGISTERED_SIMULATION` needs a `SIMULATED` gateway.
        """
        def work(c: Connection) -> Registered:
            _lock_slot(c, record.tenant_id, record.site_id, record.external_batch_id)
            admitted = c.execute(
                text("SELECT id, status FROM ingestion_batch WHERE site_id = :site AND external_batch_id = :b"),
                {"site": record.site_id, "b": record.external_batch_id},
            ).first()
            if admitted is not None:
                raise PublicationRefused(
                    "ALREADY_ADMITTED",
                    f"batch {record.external_batch_id} was already admitted ({admitted.status}); a publication "
                    "is recorded only before admission and never assigned afterwards")
            gateway = c.execute(
                text("SELECT site_id, mode FROM gateway WHERE tenant_id = :t AND id = :g"),
                {"t": record.tenant_id, "g": record.gateway_id},
            ).first()
            if gateway is None or gateway.site_id != record.site_id:
                raise PublicationRefused("GATEWAY_NOT_REGISTERED", "the gateway is not registered to this tenant Site")
            source = c.execute(
                text("SELECT gateway_id, site_id FROM source WHERE tenant_id = :t AND id = :s"),
                {"t": record.tenant_id, "s": record.source_id},
            ).first()
            if source is None or source.gateway_id != record.gateway_id or source.site_id != record.site_id:
                raise PublicationRefused("SOURCE_NOT_AFFILIATED", "the source is not registered to this gateway and Site")
            if record.source_class == REGISTERED_SIMULATION and gateway.mode != "SIMULATED":
                raise PublicationRefused("GATEWAY_NOT_SIMULATED",
                                         f"a registered simulation needs a SIMULATED gateway, not {gateway.mode}")
            wanted = (
                record.tenant_id, record.site_id, record.gateway_id, record.source_id, record.external_batch_id,
                record.payload_sha256, record.source_class, record.fixture_id, record.fixture_version,
                record.run_id, record.run_identity_sha256,
            )

            def content(row) -> tuple:
                return (row.tenant_id, row.site_id, row.gateway_id, row.source_id, row.external_batch_id,
                        row.payload_sha256, row.source_class, row.fixture_id, row.fixture_version, row.run_id,
                        row.run_identity_sha256)

            existing = c.execute(
                text(f"SELECT {_PUBLICATION_COLUMNS} FROM evidence_publication "
                     "WHERE tenant_id = :t AND site_id = :site AND external_batch_id = :b"),
                {"t": record.tenant_id, "site": record.site_id, "b": record.external_batch_id},
            ).first()
            if existing is not None:
                if content(existing) != wanted or record.publication_id not in (None, existing.id):
                    raise PublicationRefused(
                        "PUBLICATION_CONFLICT",
                        f"batch {record.external_batch_id} is already published with another commitment or ID")
                return Registered(existing.id, False)
            if record.publication_id is not None:
                reused = c.execute(text("SELECT 1 FROM evidence_publication WHERE id = :id"),
                                   {"id": record.publication_id}).first()
                if reused is not None:
                    raise PublicationRefused("PUBLICATION_ID_REUSED",
                                             "this publication ID already designates another batch")
            publication_id = record.publication_id or uuid4()
            a = record.authority
            c.execute(
                text("INSERT INTO evidence_publication (id, tenant_id, site_id, gateway_id, source_id, external_batch_id, payload_sha256, source_class, fixture_id, fixture_version, run_id, run_identity_sha256, actor_kind, actor_id, authorization_basis, channel, publication_trigger, recorded_at) VALUES (:id, :t, :site, :g, :src, :b, :sha, :cls, :fx, :fv, :run, :rd, :kind, :actor, :basis, :channel, :trig, clock_timestamp())"),
                {"id": publication_id, "t": record.tenant_id, "site": record.site_id, "g": record.gateway_id,
                 "src": record.source_id, "b": record.external_batch_id, "sha": record.payload_sha256,
                 "cls": record.source_class, "fx": record.fixture_id, "fv": record.fixture_version,
                 "run": record.run_id, "rd": record.run_identity_sha256, "kind": a.actor_kind, "actor": a.actor_id,
                 "basis": a.authorization_basis, "channel": a.channel, "trig": a.trigger},
            )
            return Registered(publication_id, True)

        return self._run(work, write=True)

    def decide_chunk(
        self,
        batch: BatchHandle,
        envelopes: Sequence[str],
        decide_one: Callable[[int, str], Decision],
        *,
        limit: int,
        decided_at: datetime,
    ) -> str:
        def work(c: Connection) -> str:
            row = c.execute(
                text(
                    "SELECT id, tenant_id, site_id, gateway_id, source_id, source_mode, foundation_revision_id, "
                    "binding_set_revision_id, status, total_count, processed_count, received_at "
                    "FROM ingestion_batch WHERE id = :id FOR UPDATE"
                ),
                {"id": batch.id},
            ).one()
            if row.status == "COMPLETED":
                return row.status
            if len(envelopes) != row.total_count:
                raise ValueError("the retried bytes do not hold the stored batch's ordinals")
            start = row.processed_count
            end = min(row.total_count, start + limit)
            tally = {"ACCEPTED": 0, "DUPLICATE": 0, "REJECTED": 0, "CONFLICT": 0}
            accepted: list[Accepted] = []
            first_new: UUID | None = None
            for ordinal in range(start, end):
                decision = decide_one(ordinal, envelopes[ordinal])
                outcome, evidence_id, rejection_id = self._persist(c, row, decision, decided_at)
                tally[outcome] += 1
                if outcome == "ACCEPTED":
                    accepted.append(decision)  # type: ignore[arg-type]
                    first_new = first_new or evidence_id
                c.execute(
                    text(
                        "INSERT INTO ingestion_disposition (batch_id, ordinal, tenant_id, site_id, message_id, "
                        "decision, accepted_evidence_id, rejection_id, decided_at) "
                        "VALUES (:b, :o, :t, :site, :m, :d, :e, :r, :at)"
                    ),
                    {
                        "b": row.id, "o": ordinal, "t": row.tenant_id, "site": row.site_id,
                        "m": decision.envelope.message_id if isinstance(decision, Accepted) else decision.message_id,
                        "d": outcome, "e": evidence_id, "r": rejection_id, "at": decided_at,
                    },
                )
            done = end == row.total_count
            c.execute(
                text(
                    "UPDATE ingestion_batch SET processed_count = :p, "
                    "accepted_count = accepted_count + :a, duplicate_count = duplicate_count + :du, "
                    "rejected_count = rejected_count + :r, conflict_count = conflict_count + :c, "
                    "status = :s, completed_at = :done_at WHERE id = :id"
                ),
                {
                    "p": end, "a": tally["ACCEPTED"], "du": tally["DUPLICATE"], "r": tally["REJECTED"],
                    "c": tally["CONFLICT"], "s": "COMPLETED" if done else "IN_PROGRESS",
                    "done_at": decided_at if done else None, "id": row.id,
                },
            )
            window = recompute_window(accepted)
            if window is not None:
                self._coalesce_job(c, row.tenant_id, row.site_id, window, first_new, decided_at)
            return "COMPLETED" if done else "IN_PROGRESS"

        return self._run(work, write=True)

    def _persist(self, c: Connection, batch, decision: Decision, decided_at: datetime):
        if isinstance(decision, Rejected):
            return "REJECTED", None, self._reject(
                c, batch, decision.ordinal, decision.message_id or None, decision.kind, decision.field,
                decision.detail, decision.envelope_sha256, None,
            )
        e = decision.envelope
        new_id = uuid4()
        inserted = c.execute(
            text(
                "INSERT INTO accepted_evidence (id, tenant_id, site_id, batch_id, ordinal, gateway_id, source_id, "
                "message_id, sequence_epoch, sequence, device_id, signal_id, asset_id, role, family, measurement, "
                "source_time, published_at, received_at, interval_start, interval_end, quality, unavailable_reason, "
                "original_value_text, original_unit, normalized_value_text, normalized_unit, conversion_kind, "
                "envelope_sha256, envelope_text, foundation_revision_id, binding_set_revision_id, "
                "binding_revision_id, configuration_outdated, source_mode) VALUES (:id, :t, :site, :b, :o, :g, :src, "
                ":m, :epoch, :seq, :dev, :sig, :asset, :role, :family, :measurement, :st, :pub, :recv, :is, :ie, "
                ":q, :ur, :ov, :ou, :nv, :nu, :ck, :sha, :body, :f, :bs, :br, :outdated, :mode) "
                "ON CONFLICT ON CONSTRAINT accepted_evidence_message_unique DO NOTHING RETURNING id"
            ),
            {
                "id": new_id, "t": batch.tenant_id, "site": batch.site_id, "b": batch.id, "o": decision.ordinal,
                "g": batch.gateway_id, "src": batch.source_id, "m": e.message_id, "epoch": e.sequence_epoch,
                "seq": e.sequence, "dev": e.device_id, "sig": e.signal_id, "asset": decision.binding.asset_id,
                "role": decision.binding.role, "family": e.family, "measurement": e.measurement,
                "st": decision.source_time, "pub": decision.published_at, "recv": batch.received_at,
                "is": decision.interval_start, "ie": decision.interval_end, "q": e.quality,
                "ur": e.unavailable_reason, "ov": e.value, "ou": e.unit, "nv": decision.normalized_value_text,
                "nu": decision.normalized_unit, "ck": decision.conversion_kind, "sha": decision.envelope_sha256,
                "body": decision.envelope_text, "f": batch.foundation_revision_id,
                "bs": batch.binding_set_revision_id, "br": decision.binding.binding_revision_id,
                "outdated": decision.configuration_outdated, "mode": batch.source_mode,
            },
        ).first()
        if inserted is not None:
            return "ACCEPTED", new_id, None
        first = c.execute(
            text(
                "SELECT id, envelope_sha256 FROM accepted_evidence WHERE site_id = :site AND gateway_id = :g "
                "AND source_id = :src AND message_id = :m"
            ),
            {"site": batch.site_id, "g": batch.gateway_id, "src": batch.source_id, "m": e.message_id},
        ).one()
        if first.envelope_sha256 == decision.envelope_sha256:
            return "DUPLICATE", first.id, None
        return "CONFLICT", None, self._reject(
            c, batch, decision.ordinal, e.message_id, "MESSAGE_CONFLICT", "message.message_id",
            "this message ID was first accepted with different envelope bytes; the original is kept",
            decision.envelope_sha256, first.id,
        )

    def _reject(self, c, batch, ordinal, message_id, kind, field, detail, sha, conflicts_with) -> UUID:
        rejection_id = uuid4()
        c.execute(
            text(
                "INSERT INTO evidence_rejection (id, tenant_id, site_id, batch_id, ordinal, message_id, kind, field, "
                "detail, envelope_sha256, conflicts_with_evidence_id, received_at) "
                "VALUES (:id, :t, :site, :b, :o, :m, :kind, :field, :detail, :sha, :cw, :at)"
            ),
            {
                "id": rejection_id, "t": batch.tenant_id, "site": batch.site_id, "b": batch.id, "o": ordinal,
                "m": message_id, "kind": kind, "field": field, "detail": detail, "sha": sha, "cw": conflicts_with,
                "at": batch.received_at,
            },
        )
        return rejection_id

    def _coalesce_job(self, c, tenant_id, site_id, window, cause: UUID | None, now: datetime) -> None:
        start, end = window
        c.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(CAST(:site AS text) || ':' || :d, 0))"),
            {"site": site_id, "d": RECOMPUTE_DOMAIN},
        )
        job = c.execute(
            text(
                "SELECT id, window_start, window_end FROM recompute_job WHERE site_id = :site AND domain = :d "
                "AND status = 'PENDING' AND window_start <= :end AND window_end >= :start "
                "ORDER BY window_start LIMIT 1 FOR UPDATE"
            ),
            {"site": site_id, "d": RECOMPUTE_DOMAIN, "start": start, "end": end},
        ).first()
        if job is None:
            c.execute(
                text(
                    "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, "
                    "cause_evidence_id, status, available_at, created_at) "
                    "VALUES (:id, :t, :site, :d, :start, :end, :cause, 'PENDING', :now, :now)"
                ),
                {"id": uuid4(), "t": tenant_id, "site": site_id, "d": RECOMPUTE_DOMAIN, "start": start,
                 "end": end, "cause": cause, "now": now},
            )
            return
        c.execute(
            text("UPDATE recompute_job SET window_start = :start, window_end = :end WHERE id = :id"),
            {"start": min(start, job.window_start), "end": max(end, job.window_end), "id": job.id},
        )

    # --- receipt ------------------------------------------------------------

    def receipt(self, principal: GatewayPrincipal, external_batch_id: str) -> IngestionReceiptV2 | None:
        def work(c: Connection) -> IngestionReceiptV2 | None:
            batch = c.execute(
                text(
                    "SELECT * FROM ingestion_batch WHERE tenant_id = :t AND site_id = :site "
                    "AND gateway_id = :g AND external_batch_id = :b"
                ),
                {"t": principal.tenant_id, "site": principal.site_id, "g": principal.gateway_id,
                 "b": external_batch_id},
            ).first()
            if batch is None:
                return None
            rows = c.execute(
                text(
                    "SELECT d.ordinal, d.message_id, d.decision, d.accepted_evidence_id, r.id AS rejection_id, "
                    "r.kind, r.field, r.detail, r.conflicts_with_evidence_id "
                    "FROM ingestion_disposition d LEFT JOIN evidence_rejection r ON r.id = d.rejection_id "
                    "WHERE d.batch_id = :b ORDER BY d.ordinal"
                ),
                {"b": batch.id},
            ).all()
            return IngestionReceiptV2(
                batch_id=batch.external_batch_id,
                payload_sha256=batch.payload_sha256,
                site_id=str(batch.site_id),
                gateway_id=str(batch.gateway_id),
                source_id=str(batch.source_id),
                status=batch.status,
                received_at=_instant(batch.received_at),
                completed_at=_instant(batch.completed_at),
                counts=ReceiptCounts(
                    total=batch.total_count, processed=batch.processed_count, accepted=batch.accepted_count,
                    duplicate=batch.duplicate_count, rejected=batch.rejected_count, conflict=batch.conflict_count,
                ),
                dispositions=tuple(
                    ReceiptDisposition(
                        ordinal=r.ordinal,
                        message_id=r.message_id,
                        decision=r.decision,
                        evidence_id=None if r.accepted_evidence_id is None else str(r.accepted_evidence_id),
                        rejection=None
                        if r.rejection_id is None
                        else ReceiptRejection(
                            rejection_id=str(r.rejection_id), kind=r.kind, field=r.field, detail=r.detail,
                            conflicts_with_evidence_id=None
                            if r.conflicts_with_evidence_id is None
                            else str(r.conflicts_with_evidence_id),
                        ),
                    )
                    for r in rows
                ),
            )

        return self._run(work)

    # --- Site Evidence reads (S2-02 phase 3a; read-only) ---------------------
    #
    # Plain row dictionaries for the pure builder in `evidence/ledger_reads.py`.
    # Every statement is scoped by the imported Site's tenant and Site UUIDs;
    # the source-time window is half-open [start, end), either bound optional.

    _WINDOW = (
        "(CAST(:start AS timestamptz) IS NULL OR e.source_time >= CAST(:start AS timestamptz)) "
        "AND (CAST(:end AS timestamptz) IS NULL OR e.source_time < CAST(:end AS timestamptz))"
    )

    def site_scope(self, tenant_slug: str, site_code: str) -> tuple[UUID, UUID] | None:
        def work(c: Connection):
            row = c.execute(
                text("SELECT t.id AS tenant_id, s.id AS site_id FROM site s JOIN tenant t ON t.id = s.tenant_id "
                     "WHERE t.slug = :slug AND s.site_code_key = lower(:code)"),
                {"slug": tenant_slug, "code": site_code},
            ).first()
            return None if row is None else (row.tenant_id, row.site_id)

        return self._run(work)

    def site_window(self, tenant_id: UUID, site_id: UUID, start: datetime | None, end: datetime | None) -> dict:
        scope = {"t": tenant_id, "site": site_id, "start": start, "end": end}
        in_window = (
            "WITH w AS (SELECT e.* FROM accepted_evidence e WHERE e.tenant_id = :t AND e.site_id = :site AND "
            + self._WINDOW + ") "
        )

        def work(c: Connection) -> dict:
            def rows(sql: str) -> list[dict]:
                return [dict(r._mapping) for r in c.execute(text(sql), scope).all()]

            sources = rows(
                in_window
                + "SELECT src.id AS source_id, src.source_external_id, g.id AS gateway_id, g.gateway_external_id, "
                "g.mode AS source_mode, count(w.id) AS accepted, max(w.source_time) AS last_source_time, "
                "max(w.published_at) AS last_published_at, max(w.received_at) AS last_received_at, "
                "(SELECT count(*) FROM ingestion_disposition d JOIN w w2 ON w2.id = d.accepted_evidence_id "
                " WHERE d.decision = 'DUPLICATE' AND w2.source_id = src.id) AS duplicates, "
                "(SELECT count(*) FROM evidence_rejection r JOIN w w3 ON w3.id = r.conflicts_with_evidence_id "
                " WHERE w3.source_id = src.id) AS conflicts "
                "FROM source src JOIN gateway g ON g.id = src.gateway_id AND g.tenant_id = src.tenant_id "
                "LEFT JOIN w ON w.source_id = src.id WHERE src.tenant_id = :t AND src.site_id = :site "
                "GROUP BY src.id, src.source_external_id, g.id, g.gateway_external_id, g.mode "
                "ORDER BY src.source_external_id, src.id"
            )
            coverage = rows(
                in_window
                + "SELECT device_id, signal_id, role, normalized_unit, count(*) AS records, "
                "count(*) FILTER (WHERE quality = 'GOOD') AS good, "
                "count(*) FILTER (WHERE configuration_outdated) AS outdated, "
                "min(source_time) AS first_source_time, max(source_time) AS last_source_time "
                "FROM w GROUP BY device_id, signal_id, role, normalized_unit ORDER BY device_id, signal_id"
            )
            batches = rows(
                in_window
                + "SELECT b.id, b.external_batch_id, b.source_id, b.status, b.payload_sha256, b.total_count, "
                "b.processed_count, b.accepted_count, b.duplicate_count, b.rejected_count, b.conflict_count, "
                "b.received_at, b.completed_at, "
                "(SELECT count(*) FROM w WHERE w.batch_id = b.id) AS accepted_in_window "
                "FROM ingestion_batch b WHERE b.tenant_id = :t AND b.site_id = :site "
                "ORDER BY b.received_at, b.external_batch_id"
            )
            projection = rows(
                "SELECT status, count(*) AS jobs, min(created_at) AS oldest_created_at, "
                "min(window_start) AS window_start, max(window_end) AS window_end FROM recompute_job "
                "WHERE tenant_id = :t AND site_id = :site AND status IN ('PENDING','LEASED','FAILED') "
                "AND (CAST(:end AS timestamptz) IS NULL OR window_start < CAST(:end AS timestamptz)) "
                "AND (CAST(:start AS timestamptz) IS NULL OR window_end > CAST(:start AS timestamptz)) "
                "GROUP BY status ORDER BY status"
            )
            extent = rows(
                "SELECT min(source_time) AS first_source_time, max(source_time) AS last_source_time, "
                "max(received_at) AS last_received_at, count(*) AS accepted_total FROM accepted_evidence "
                "WHERE tenant_id = :t AND site_id = :site"
            )[0]
            return {"sources": sources, "coverage": coverage, "batches": batches, "projection": projection,
                    "extent": extent, "rejections": self._rejection_rows(c, tenant_id, site_id, None)}

        return self._run(work)

    def _rejection_rows(self, c: Connection, tenant_id: UUID, site_id: UUID, batch: str | None) -> list[dict]:
        found = [dict(r._mapping) for r in c.execute(
            text(
                "SELECT r.id AS rejection_id, r.batch_id, b.external_batch_id, b.source_id, r.ordinal, r.message_id, "
                "r.kind, r.field, r.detail, r.envelope_sha256, r.conflicts_with_evidence_id, r.received_at, "
                "d.decided_at, d.decision, ce.source_time AS original_source_time "
                "FROM evidence_rejection r JOIN ingestion_batch b ON b.id = r.batch_id "
                "LEFT JOIN ingestion_disposition d ON d.rejection_id = r.id "
                "LEFT JOIN accepted_evidence ce ON ce.id = r.conflicts_with_evidence_id "
                "WHERE r.tenant_id = :t AND r.site_id = :site "
                "AND (CAST(:batch AS text) IS NULL OR b.external_batch_id = :batch) "
                "ORDER BY r.received_at, b.external_batch_id, r.ordinal"
            ),
            {"t": tenant_id, "site": site_id, "batch": batch},
        ).all()]
        texts = self._batch_texts(c, {row["batch_id"] for row in found})
        for row in found:
            row["envelope_text"] = _envelope_at(texts.get(row["batch_id"]), row["ordinal"])
        return found

    def _batch_texts(self, c: Connection, batch_ids: set) -> dict:
        if not batch_ids:
            return {}
        return {
            r.id: r.batch_text
            for r in c.execute(
                text("SELECT id, batch_text FROM ingestion_batch WHERE id = ANY(:ids)"), {"ids": list(batch_ids)}
            ).all()
        }

    def records_page(self, tenant_id: UUID, site_id: UUID, *, start, end, device, signal, source,
                     after: tuple[datetime, UUID] | None, limit: int) -> dict:
        params = {"t": tenant_id, "site": site_id, "start": start, "end": end, "device": device,
                  "signal": signal, "source": source, "limit": limit + 1,
                  "after_time": None if after is None else after[0], "after_id": None if after is None else after[1]}
        where = (
            "WHERE e.tenant_id = :t AND e.site_id = :site AND " + self._WINDOW + " "
            "AND (CAST(:device AS text) IS NULL OR e.device_id = :device) "
            "AND (CAST(:signal AS text) IS NULL OR e.signal_id = :signal) "
            "AND (CAST(:source AS text) IS NULL OR src.id::text = :source OR src.source_external_id = :source) "
        )
        joins = ("FROM accepted_evidence e JOIN source src ON src.id = e.source_id "
                 "JOIN gateway g ON g.id = e.gateway_id JOIN ingestion_batch b ON b.id = e.batch_id ")

        def work(c: Connection) -> dict:
            total = c.execute(text("SELECT count(*) " + joins + where), params).scalar_one()
            page = [dict(r._mapping) for r in c.execute(
                text(
                    "SELECT e.id, e.message_id, e.source_id, src.source_external_id, e.gateway_id, "
                    "g.gateway_external_id, e.device_id, e.signal_id, e.role, e.family, e.measurement, e.quality, "
                    "e.unavailable_reason, e.original_value_text, e.original_unit, e.normalized_value_text, "
                    "e.normalized_unit, e.source_time, e.published_at, b.received_at, e.interval_start, "
                    "e.interval_end, e.configuration_outdated, e.source_mode, b.external_batch_id, e.ordinal "
                    + joins + where
                    + "AND (CAST(:after_time AS timestamptz) IS NULL OR (e.source_time, e.id) > "
                    "(CAST(:after_time AS timestamptz), CAST(:after_id AS uuid))) "
                    "ORDER BY e.source_time, e.id LIMIT :limit"
                ),
                params,
            ).all()]
            return {"total": total, "rows": page}

        return self._run(work)

    def record_detail(self, tenant_id: UUID, site_id: UUID, key: str) -> list[dict]:
        """The accepted record named by its evidence UUID, else by message ID (every match)."""
        evidence_id = _uuid_or_none(key)

        def work(c: Connection) -> list[dict]:
            found = [dict(r._mapping) for r in c.execute(
                text(
                    "SELECT e.*, src.source_external_id, g.gateway_external_id, b.external_batch_id, "
                    "b.payload_sha256, b.status AS batch_status, b.received_at AS batch_received_at, "
                    "b.completed_at AS batch_completed_at, b.total_count, b.processed_count, "
                    "d.decision, d.decided_at "
                    "FROM accepted_evidence e JOIN source src ON src.id = e.source_id "
                    "JOIN gateway g ON g.id = e.gateway_id JOIN ingestion_batch b ON b.id = e.batch_id "
                    "LEFT JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
                    "WHERE e.tenant_id = :t AND e.site_id = :site AND "
                    + ("e.id = :id" if evidence_id is not None else "e.message_id = :key")
                    + " ORDER BY e.source_id, e.id"
                ),
                {"t": tenant_id, "site": site_id, "id": evidence_id, "key": key},
            ).all()]
            for row in found:
                row["duplicates"] = [dict(r._mapping) for r in c.execute(
                    text("SELECT b.external_batch_id, d.ordinal, d.decided_at, b.received_at "
                         "FROM ingestion_disposition d JOIN ingestion_batch b ON b.id = d.batch_id "
                         "WHERE d.accepted_evidence_id = :id AND d.decision = 'DUPLICATE' "
                         "ORDER BY b.received_at, d.ordinal"),
                    {"id": row["id"]},
                ).all()]
                conflicts = [dict(r._mapping) for r in c.execute(
                    text("SELECT r.id AS rejection_id, r.batch_id, b.external_batch_id, r.ordinal, r.kind, "
                         "r.detail, r.envelope_sha256, b.received_at, d.decided_at "
                         "FROM evidence_rejection r JOIN ingestion_batch b ON b.id = r.batch_id "
                         "LEFT JOIN ingestion_disposition d ON d.rejection_id = r.id "
                         "WHERE r.conflicts_with_evidence_id = :id ORDER BY b.received_at, r.ordinal"),
                    {"id": row["id"]},
                ).all()]
                texts = self._batch_texts(c, {x["batch_id"] for x in conflicts})
                for conflict in conflicts:
                    conflict["envelope_text"] = _envelope_at(texts.get(conflict["batch_id"]), conflict["ordinal"])
                row["conflicts"] = conflicts
            return found

        return self._run(work)

    def rejections(self, tenant_id: UUID, site_id: UUID, batch: str | None) -> dict:
        def work(c: Connection) -> dict:
            duplicates = [dict(r._mapping) for r in c.execute(
                text("SELECT b.external_batch_id, d.ordinal, d.message_id, d.accepted_evidence_id, "
                     "d.decided_at, b.received_at FROM ingestion_disposition d "
                     "JOIN ingestion_batch b ON b.id = d.batch_id "
                     "WHERE d.tenant_id = :t AND d.site_id = :site AND d.decision = 'DUPLICATE' "
                     "AND (CAST(:batch AS text) IS NULL OR b.external_batch_id = :batch) "
                     "ORDER BY b.received_at, b.external_batch_id, d.ordinal"),
                {"t": tenant_id, "site": site_id, "batch": batch},
            ).all()]
            return {"rejections": self._rejection_rows(c, tenant_id, site_id, batch), "duplicates": duplicates}

        return self._run(work)

    def dispatch_jobs(self, tenant_id: UUID, site_id: UUID) -> list[dict]:
        """Every `dispatch` recompute job for the Site (S3 hand-off fixtures); read-only."""
        def work(c: Connection) -> list[dict]:
            return [dict(r._mapping) for r in c.execute(
                text("SELECT id, domain, window_start, window_end, cause_evidence_id, status, available_at, "
                     "attempts, created_at FROM recompute_job WHERE tenant_id = :t AND site_id = :site "
                     "ORDER BY created_at, id"),
                {"t": tenant_id, "site": site_id},
            ).all()]

        return self._run(work)

    def message_digests(self, tenant_id: UUID, site_id: UUID, message_ids: Sequence[str]) -> dict[str, str]:
        """Accepted envelope digests by message ID, for the legacy comparison; read-only."""
        if not message_ids:
            return {}

        def work(c: Connection) -> dict[str, str]:
            return {
                r.message_id: r.envelope_sha256
                for r in c.execute(
                    text("SELECT message_id, envelope_sha256 FROM accepted_evidence "
                         "WHERE tenant_id = :t AND site_id = :site AND message_id = ANY(:ids)"),
                    {"t": tenant_id, "site": site_id, "ids": list(message_ids)},
                ).all()
            }

        return self._run(work)

    def bound_channels(self, tenant_id: UUID, site_id: UUID) -> set[tuple[str, str]]:
        """Every (device_id, signal_id) registered in any binding revision of the Site."""
        def work(c: Connection) -> set[tuple[str, str]]:
            return {
                (r.device_id, r.signal_id)
                for r in c.execute(
                    text("SELECT DISTINCT device_id, signal_id FROM signal_binding_revision "
                         "WHERE tenant_id = :t AND site_id = :site"),
                    {"t": tenant_id, "site": site_id},
                ).all()
            }

        return self._run(work)

    # --- S4-05a source provenance reads (read-only; the resolver is evidence/source_provenance.py) ----------
    # Every query is scoped by tenant and Site. The provenance chain is joined LEFT and unscoped past the
    # accepted row, so a link or publication that disagrees with the scoped batch commitment comes back for the
    # resolver to name as broken, never silently dropped. Another tenant's rows are never reported.

    def link_rows(self, tenant_id: UUID, site_id: UUID, evidence_ids: list[str]) -> list[LinkRow]:
        def work(c: Connection) -> list[LinkRow]:
            rows = c.execute(_LINKS, {"t": tenant_id, "s": site_id, "ids": [str(i) for i in evidence_ids]}).all()
            return [LinkRow(
                requested_id=r.requested_id, in_scope=r.in_scope, in_tenant_elsewhere=r.in_tenant_elsewhere,
                batch_id=r.batch_id,
                evidence_gateway_source=None if r.e_gateway is None else (r.e_gateway, r.e_source),
                batch=_commitment(r, "b"), link_publication_id=r.l_pub, link=_commitment(r, "l"),
                publication=_commitment(r, "p"), source_class=r.source_class, fixture_id=r.fixture_id,
                fixture_version=r.fixture_version, run_id=r.run_id, run_identity_sha256=r.run_identity_sha256)
                for r in rows]
        return self._run(work)

    def finding_revision_evidence(self, tenant_id: UUID, site_id: UUID,
                                  finding_revision_id: UUID) -> list[str] | None:
        def work(c: Connection) -> list[str] | None:
            p = {"t": tenant_id, "s": site_id, "r": finding_revision_id}
            if c.execute(text("SELECT 1 FROM finding_revision WHERE tenant_id = :t AND site_id = :s AND id = :r"),
                         p).first() is None:
                return None
            return self._cited(c, p)
        return self._run(work)

    @staticmethod
    def _cited(c: Connection, p: dict) -> list[str]:
        return list(c.execute(text(
            "SELECT CAST(evidence_id AS text) FROM finding_revision_evidence WHERE tenant_id = :t "
            "AND site_id = :s AND finding_revision_id = :r ORDER BY evidence_id"), p).scalars())

    def consequence_inputs(self, tenant_id: UUID, site_id: UUID, consequence_revision_id: UUID
                           ) -> tuple[str, list[str], list[str]] | None:
        def work(c: Connection) -> tuple[str, list[str], list[str]] | None:
            p = {"t": tenant_id, "s": site_id, "c": consequence_revision_id}
            finding_revision_id = c.execute(text(
                "SELECT CAST(finding_revision_id AS text) FROM financial_consequence_revision "
                "WHERE tenant_id = :t AND site_id = :s AND id = :c"), p).scalar_one_or_none()
            if finding_revision_id is None:
                return None
            cited = self._cited(c, {"t": tenant_id, "s": site_id, "r": finding_revision_id})
            power = list(c.execute(text(
                "SELECT CAST(evidence_id AS text) FROM financial_consequence_power_interval WHERE tenant_id = :t "
                "AND site_id = :s AND consequence_revision_id = :c ORDER BY evidence_id"), p).scalars())
            return finding_revision_id, cited, power
        return self._run(work)


_LINKS = text(
    "SELECT CAST(q.id AS text) AS requested_id, e.id IS NOT NULL AS in_scope, "
    "EXISTS (SELECT 1 FROM accepted_evidence o WHERE o.id = q.id AND o.tenant_id = :t "
    "AND o.site_id <> :s) AS in_tenant_elsewhere, "
    "CAST(e.batch_id AS text) AS batch_id, CAST(e.gateway_id AS text) AS e_gateway, "
    "CAST(e.source_id AS text) AS e_source, "
    "CAST(b.id AS text) AS b_id, CAST(b.tenant_id AS text) AS b_tenant, CAST(b.site_id AS text) AS b_site, "
    "CAST(b.gateway_id AS text) AS b_gateway, CAST(b.source_id AS text) AS b_source, "
    "b.external_batch_id AS b_ext, b.payload_sha256 AS b_sha, "
    "CAST(l.batch_id AS text) AS l_batch, CAST(l.publication_id AS text) AS l_pub, "
    "CAST(l.tenant_id AS text) AS l_tenant, CAST(l.site_id AS text) AS l_site, "
    "CAST(l.gateway_id AS text) AS l_gateway, CAST(l.source_id AS text) AS l_source, "
    "l.external_batch_id AS l_ext, l.payload_sha256 AS l_sha, "
    "CAST(p.id AS text) AS p_id, CAST(p.tenant_id AS text) AS p_tenant, CAST(p.site_id AS text) AS p_site, "
    "CAST(p.gateway_id AS text) AS p_gateway, CAST(p.source_id AS text) AS p_source, "
    "p.external_batch_id AS p_ext, p.payload_sha256 AS p_sha, p.source_class, p.fixture_id, "
    "p.fixture_version, p.run_id, p.run_identity_sha256 "
    "FROM unnest(CAST(:ids AS uuid[])) AS q(id) "
    "LEFT JOIN accepted_evidence e ON e.tenant_id = :t AND e.site_id = :s AND e.id = q.id "
    "LEFT JOIN ingestion_batch b ON b.tenant_id = e.tenant_id AND b.site_id = e.site_id AND b.id = e.batch_id "
    "LEFT JOIN batch_publication_link l ON l.batch_id = e.batch_id "
    "LEFT JOIN evidence_publication p ON p.id = l.publication_id")


def _commitment(r, prefix: str) -> tuple[str, ...] | None:
    if getattr(r, f"{prefix}_tenant") is None:
        return None
    return tuple(getattr(r, f"{prefix}_{k}") for k in ("tenant", "site", "gateway", "source", "ext", "sha"))


def _envelope_at(batch_text: str | None, ordinal: int) -> str | None:
    """The submitted envelope text at `ordinal` of a stored Batch V2 text, if readable."""
    if batch_text is None:
        return None
    try:
        found = json.loads(batch_text)["envelopes"][ordinal]
    except (ValueError, KeyError, IndexError, TypeError):
        return None
    return found if isinstance(found, str) else None
