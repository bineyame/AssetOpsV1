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
from assetops_contracts.ingestion_receipt_v2 import (
    IngestionReceiptV2,
    ReceiptCounts,
    ReceiptDisposition,
    ReceiptRejection,
)


def _instant(value: datetime | None) -> str | None:
    """Server real-UTC instant text with exactly six fractional digits (Receipt V2)."""
    return None if value is None else value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


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
            c.execute(
                text(
                    "INSERT INTO ingestion_batch (id, tenant_id, site_id, gateway_id, source_id, external_batch_id, "
                    "payload_sha256, schema_version, source_mode, foundation_revision_id, binding_set_revision_id, "
                    "snapshot_sha256, batch_text, status, total_count, received_at) "
                    "VALUES (:id, :t, :site, :g, :src, :b, :sha, 2, :mode, :f, :bs, :snap, :body, 'IN_PROGRESS', "
                    ":total, :at) ON CONFLICT ON CONSTRAINT ingestion_batch_external_unique DO NOTHING"
                ),
                {
                    "id": uuid4(), "t": principal.tenant_id, "site": principal.site_id, "g": principal.gateway_id,
                    "src": UUID(source_id), "b": external_batch_id, "sha": payload_sha256, "mode": source_mode,
                    "f": basis.foundation_revision_id, "bs": basis.binding_set_revision_id,
                    "snap": basis.snapshot_sha256, "body": batch_text, "total": total, "at": received_at,
                },
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
