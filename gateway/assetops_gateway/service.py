"""The durable simulated gateway: provisioning, activation, admission, sealing.

Transport-agnostic. Phase 2 binds this to the authenticated local IPC channel of
`D-2026-10-08-s2-local-gateway-snapshot-transfer`; every method here assumes its
caller has ALREADY authenticated the Lab host. Nothing in this package imports
the simulator kernel, world, scenario or oracle, the backend, or `host/`.

Crash sequence (technical design 2): report -> map/validate -> BEGIN IMMEDIATE ->
read/increment sequence -> derive message id -> insert canonical envelope bytes
-> COMMIT; sealing is a second transaction. A refused report is a `mapping_hold`
row with its kind, field and reason, and allocates no sequence.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from assetops_contracts.gateway_report import (
    DeviceReport,
    device_report_text,
    parse_device_report_text,
)
from assetops_contracts.ingestion_batch_v2 import MAX_BATCH_ENVELOPES, BatchRejected, seal_batch_v2
from assetops_contracts.source_envelope import EnvelopeRejected
from assetops_contracts.source_envelope_v3 import (
    MAX_SEQUENCE,
    SourceEnvelopeV3,
    canonical_envelope_v3_text,
    is_canonical_decimal,
    text_sha256,
    v3_message_id,
)

from assetops_gateway.ledger import open_reader_connection, open_writer_connection
from assetops_gateway.snapshot import (
    STATE_UNIT,
    Binding,
    ClaimedReferences,
    Provisioning,
    SnapshotRefused,
    VerifiedSnapshot,
    registered_instant,
    verify_snapshot,
)

_INSTANT = "%Y-%m-%dT%H:%M:%SZ"
_MEMBER_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _text(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime(_INSTANT)


class GatewayRefused(RuntimeError):
    def __init__(self, kind: str, detail: str) -> None:
        self.kind = kind
        self.detail = detail
        super().__init__(f"{kind}: {detail}")


@dataclass(frozen=True)
class Admission:
    """The gateway's answer to one report."""

    outcome: str  # ADMITTED | ALREADY_ADMITTED | HELD
    message_id: str | None = None
    sequence: int | None = None
    hold_id: int | None = None
    kind: str | None = None
    field: str | None = None
    detail: str | None = None


#: Upper bound on one admission chunk (one transaction).
MAX_ADMISSION_CHUNK = 1024


def _check_initial_state(initial_state: str) -> None:
    if initial_state not in ("STAGED", "READY"):
        raise ValueError("an envelope starts STAGED (Lab) or READY (live)")


class _Held(Exception):
    def __init__(self, kind: str, field: str, detail: str) -> None:
        self.kind, self.field, self.detail = kind, field, detail


def _seal(provisioning: Provisioning, snapshot: VerifiedSnapshot, source_id: str, texts: list[str]):
    return seal_batch_v2(
        site_id=provisioning.site_id,
        gateway_id=provisioning.gateway_id,
        source_id=source_id,
        source_mode=provisioning.source_mode,
        foundation_version=snapshot.foundation_version,
        foundation_valid_from=snapshot.foundation_valid_from,
        binding_set_id=snapshot.binding_set_id,
        binding_version=snapshot.binding_set_version,
        snapshot_sha256=snapshot.snapshot_sha256,
        envelope_texts=texts,
    )


def _fit(provisioning: Provisioning, snapshot: VerifiedSnapshot, source_id: str, members: list[tuple], limit: int):
    """`(chunk, batch, text)`: the longest sequence-ordered prefix that seals.

    The count-bounded prefix is tried first, so a group within both bounds
    seals exactly as before F1. Only a byte refusal shortens it: a batch grows
    with every envelope, so a binary search finds the longest prefix that fits.
    Raises `BatchRejected` when not even the first envelope can be sealed."""
    count = min(limit, len(members))
    try:
        return (members[:count], *_seal(provisioning, snapshot, source_id, [m[5] for m in members[:count]]))
    except BatchRejected as error:
        if error.field != "batch" or count == 1:
            raise
    low, high, best = 1, count - 1, None
    while low <= high:
        middle = (low + high) // 2
        try:
            best = (members[:middle], *_seal(provisioning, snapshot, source_id, [m[5] for m in members[:middle]]))
            low = middle + 1
        except BatchRejected as error:
            if error.field != "batch":
                raise
            high = middle - 1
    if best is None:
        return (members[:1], *_seal(provisioning, snapshot, source_id, [members[0][5]]))
    return best


#: Fault-injection points tests use to stop the process between steps.
FAULT_POINTS = ("after_sequence_read", "after_enqueue_commit", "after_seal_commit")


class GatewayService:
    def __init__(
        self,
        path: Path,
        *,
        clock: Callable[[], datetime] = _utc_now,
        fault: Callable[[str], None] | None = None,
    ) -> None:
        self.path = Path(path)
        self._clock = clock
        self._fault = fault
        self._db, self._lock = open_writer_connection(self.path)
        self._verified: dict[str, VerifiedSnapshot] = {}
        self._recover()

    # --- lifecycle -------------------------------------------------------------

    def close(self) -> None:
        try:
            self._db.close()
        finally:
            self._lock.release()

    def __enter__(self) -> "GatewayService":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _now(self) -> str:
        return _text(self._clock())

    def _hit(self, point: str) -> None:
        if self._fault is not None:
            self._fault(point)

    def _recover(self) -> None:
        """An interrupted local attempt is retryable with identical bytes."""
        with self._tx():
            in_flight = [r[0] for r in self._db.execute("SELECT batch_id FROM upload_batch WHERE state='IN_FLIGHT'")]
            for batch_id in in_flight:
                self._db.execute("UPDATE upload_batch SET state='READY' WHERE batch_id=?", (batch_id,))
                self._db.execute(
                    "UPDATE envelope_outbox SET state='READY' WHERE message_id IN "
                    "(SELECT message_id FROM batch_item WHERE batch_id=?)",
                    (batch_id,),
                )

    class _Tx:
        def __init__(self, db: sqlite3.Connection) -> None:
            self.db = db

        def __enter__(self) -> sqlite3.Connection:
            self.db.execute("BEGIN IMMEDIATE")
            return self.db

        def __exit__(self, kind: object, *_: object) -> None:
            self.db.execute("ROLLBACK" if kind is not None else "COMMIT")

    def _tx(self) -> "GatewayService._Tx":
        return GatewayService._Tx(self._db)

    # --- provisioning ----------------------------------------------------------

    def provision(self, provisioning: Provisioning, *, sequence_epoch: str) -> None:
        """Install this gateway's identity once; an identical repeat is a no-op."""
        with self._tx() as db:
            row = db.execute(
                "SELECT tenant_id, site_id, gateway_id, source_mode FROM gateway_identity"
            ).fetchone()
            sources = sorted(r[0] for r in db.execute("SELECT source_id FROM permitted_source"))
            if row is not None:
                same = row == (
                    provisioning.tenant_id,
                    provisioning.site_id,
                    provisioning.gateway_id,
                    provisioning.source_mode,
                ) and sources == sorted(provisioning.permitted_source_ids)
                if not same:
                    raise GatewayRefused("IDENTITY_FIXED", "this gateway is already provisioned differently")
                return
            now = self._now()
            db.execute(
                "INSERT INTO gateway_identity VALUES (1,?,?,?,?,?,?)",
                (
                    provisioning.tenant_id,
                    provisioning.site_id,
                    provisioning.gateway_id,
                    provisioning.source_mode,
                    sequence_epoch,
                    now,
                ),
            )
            db.executemany(
                "INSERT INTO permitted_source VALUES (?)",
                [(s,) for s in sorted(provisioning.permitted_source_ids)],
            )
            db.execute("INSERT INTO sequence_epoch_history VALUES (?,?)", (sequence_epoch, now))

    def reprovision_epoch(self, new_epoch: str) -> None:
        """The only way the sequence epoch changes. A used epoch never returns."""
        with self._tx() as db:
            self._provisioning(db)
            if db.execute("SELECT 1 FROM sequence_epoch_history WHERE sequence_epoch=?", (new_epoch,)).fetchone():
                raise GatewayRefused("EPOCH_REUSED", f"epoch {new_epoch!r} was already used")
            db.execute("UPDATE gateway_identity SET sequence_epoch=?", (new_epoch,))
            db.execute("INSERT INTO sequence_epoch_history VALUES (?,?)", (new_epoch, self._now()))

    def _provisioning(self, db: sqlite3.Connection) -> tuple[Provisioning, str]:
        row = db.execute(
            "SELECT tenant_id, site_id, gateway_id, source_mode, sequence_epoch FROM gateway_identity"
        ).fetchone()
        if row is None:
            raise GatewayRefused("NOT_PROVISIONED", "this gateway has no provisioned identity")
        sources = frozenset(r[0] for r in db.execute("SELECT source_id FROM permitted_source"))
        return Provisioning(row[0], row[1], row[2], row[3], sources), row[4]

    def identity(self) -> dict[str, object]:
        """This gateway's provisioned identity, as the host may check it."""
        with self._tx() as db:
            provisioning, epoch = self._provisioning(db)
        return {
            "tenant_id": provisioning.tenant_id,
            "site_id": provisioning.site_id,
            "gateway_id": provisioning.gateway_id,
            "source_mode": provisioning.source_mode,
            "permitted_source_ids": sorted(provisioning.permitted_source_ids),
            "sequence_epoch": epoch,
        }

    # --- activation ------------------------------------------------------------

    def activate(self, snapshot_text: str, claimed: ClaimedReferences) -> VerifiedSnapshot:
        """Verify and store an immutable mapping snapshot, then switch to it."""
        with self._tx() as db:
            provisioning, _ = self._provisioning(db)
            verified = verify_snapshot(snapshot_text, claimed, provisioning)
            stored = db.execute(
                "SELECT snapshot_text FROM mapping_snapshot WHERE snapshot_sha256=?",
                (verified.snapshot_sha256,),
            ).fetchone()
            now = self._now()
            if stored is not None:
                if stored[0] != snapshot_text:
                    raise SnapshotRefused("HASH_MISMATCH", "snapshot", "different bytes are stored under this hash")
            else:
                clash = db.execute(
                    "SELECT snapshot_sha256 FROM mapping_snapshot WHERE foundation_revision_id=? AND binding_set_revision_id=?",
                    (verified.foundation_revision_id, verified.binding_set_revision_id),
                ).fetchone()
                if clash is not None:
                    raise SnapshotRefused(
                        "REFERENCE_MISMATCH", "mapping", "these revisions are stored with a different snapshot hash"
                    )
                db.execute(
                    "INSERT INTO mapping_snapshot VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        verified.snapshot_sha256,
                        snapshot_text,
                        verified.schema,
                        verified.foundation_revision_id,
                        verified.foundation_version,
                        verified.foundation_valid_from,
                        verified.foundation_valid_to,
                        verified.binding_set_id,
                        verified.binding_set_revision_id,
                        verified.binding_set_version,
                        verified.binding_valid_from,
                        verified.binding_valid_to,
                        now,
                    ),
                )
                db.executemany(
                    "INSERT INTO device_signal_mapping VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [
                        (
                            verified.snapshot_sha256,
                            b.device_id,
                            b.signal_id,
                            b.binding_revision_id,
                            b.source_id,
                            b.role,
                            b.source_unit,
                            b.canonical_unit,
                            b.conversion_kind,
                            json.dumps(b.enum_map),
                        )
                        for b in verified.bindings
                    ],
                )
            db.execute(
                "INSERT INTO active_mapping VALUES (1,?,?) ON CONFLICT(singleton) DO UPDATE "
                "SET snapshot_sha256=excluded.snapshot_sha256, switched_at=excluded.switched_at",
                (verified.snapshot_sha256, now),
            )
            return verified

    def _snapshot(self, db: sqlite3.Connection, snapshot_sha256: str) -> VerifiedSnapshot | None:
        if snapshot_sha256 in self._verified:
            return self._verified[snapshot_sha256]
        row = db.execute(
            "SELECT snapshot_text, foundation_revision_id, foundation_version, binding_set_id, "
            "binding_set_revision_id, binding_set_version FROM mapping_snapshot WHERE snapshot_sha256=?",
            (snapshot_sha256,),
        ).fetchone()
        if row is None:
            return None
        provisioning, _ = self._provisioning(db)
        # Re-verified from the stored bytes once per process: a tampered row is
        # refused here too.
        verified = verify_snapshot(
            row[0],
            ClaimedReferences(snapshot_sha256, row[1], row[2], row[3], row[4], row[5]),
            provisioning,
        )
        self._verified[snapshot_sha256] = verified
        return verified

    # --- admission -------------------------------------------------------------

    def admit(
        self,
        report_text: str,
        *,
        snapshot_sha256: str,
        lab_run_ref: str | None = None,
        initial_state: str = "STAGED",
    ) -> Admission:
        """Admit one public report under one activated snapshot."""
        _check_initial_state(initial_state)
        with self._tx() as db:
            admission = self._admit_in(db, report_text, snapshot_sha256, lab_run_ref, initial_state)
        self._hit("after_enqueue_commit")
        return admission

    def admit_texts(
        self,
        report_texts: Iterable[str],
        *,
        snapshot_sha256: str,
        lab_run_ref: str | None = None,
        initial_state: str = "STAGED",
    ) -> list[Admission]:
        """Admit a bounded chunk of reports in ONE transaction.

        Same per-report rules as `admit`; the chunk commits or rolls back whole,
        so a crash leaves either every report of the chunk admitted or none.
        One transaction per report made a full-day Lab run slow (phase-1 risk)."""
        _check_initial_state(initial_state)
        texts = list(report_texts)
        if len(texts) > MAX_ADMISSION_CHUNK:
            raise ValueError(f"at most {MAX_ADMISSION_CHUNK} reports per admission chunk")
        with self._tx() as db:
            admissions = [self._admit_in(db, text, snapshot_sha256, lab_run_ref, initial_state) for text in texts]
        self._hit("after_enqueue_commit")
        return admissions

    def _admit_in(
        self,
        db: sqlite3.Connection,
        report_text: str,
        snapshot_sha256: str,
        lab_run_ref: str | None,
        initial_state: str,
    ) -> Admission:
        report_sha = text_sha256(report_text) if isinstance(report_text, str) else text_sha256(repr(report_text))
        report: DeviceReport | None = None
        snapshot: VerifiedSnapshot | None = None
        try:
            try:
                report = parse_device_report_text(report_text)
            except EnvelopeRejected as error:
                raise _Held("INVALID_REPORT", error.field, error.detail) from error
            provisioning, epoch = self._provisioning(db)
            snapshot = self._snapshot(db, snapshot_sha256)
            if snapshot is None:
                raise _Held("NO_ACTIVE_MAPPING", "snapshot_sha256", "no activated snapshot has this hash")
            binding = snapshot.binding_for(report.device_id, report.signal_id)
            if binding is None:
                raise _Held(
                    "UNKNOWN_CHANNEL",
                    "device_id/signal_id",
                    f"{report.device_id}/{report.signal_id} has no binding in this snapshot",
                )
            if binding.source_id not in provisioning.permitted_source_ids:
                raise _Held("SOURCE_NOT_PERMITTED", "source_id", f"{binding.source_id} is not permitted")
            published_at = self._now()
            self._check_report(report, binding, snapshot, published_at)
            if report.report_key is not None:
                earlier = db.execute(
                    "SELECT report_sha256, a.message_id, o.sequence FROM report_admission a "
                    "JOIN envelope_outbox o ON o.message_id=a.message_id "
                    "WHERE a.gateway_id=? AND a.source_id=? AND a.report_key=?",
                    (provisioning.gateway_id, binding.source_id, report.report_key),
                ).fetchone()
                if earlier is not None:
                    if earlier[0] != report_sha:
                        raise _Held(
                            "CONFLICTING_REPORT",
                            "report_key",
                            "this key was admitted with different content",
                        )
                    self._provenance(db, lab_run_ref, message_id=earlier[1])
                    return Admission("ALREADY_ADMITTED", message_id=earlier[1], sequence=earlier[2])
            key = (provisioning.gateway_id, binding.source_id, epoch)
            row = db.execute(
                "SELECT last_sequence FROM sequence_state WHERE gateway_id=? AND source_id=? AND sequence_epoch=?",
                key,
            ).fetchone()
            if row is not None and row[0] >= MAX_SEQUENCE:
                raise _Held("SEQUENCE_EXHAUSTED", "sequence", "reprovision a new epoch to continue")
            sequence = 1 if row is None else row[0] + 1
            self._hit("after_sequence_read")
            message_id = v3_message_id(
                site_id=provisioning.site_id,
                gateway_id=provisioning.gateway_id,
                source_id=binding.source_id,
                sequence_epoch=epoch,
                sequence=sequence,
            )
            try:
                envelope = SourceEnvelopeV3(
                    message_id=message_id,
                    sequence_epoch=epoch,
                    sequence=sequence,
                    site_id=provisioning.site_id,
                    gateway_id=provisioning.gateway_id,
                    source_id=binding.source_id,
                    device_id=report.device_id,
                    signal_id=report.signal_id,
                    binding_set_id=snapshot.binding_set_id,
                    binding_version=snapshot.binding_set_version,
                    source_time=report.source_time,
                    published_at=published_at,
                    interval_start=report.interval_start,
                    interval_end=report.source_time if report.measurement == "INTERVAL_MEAN" else None,
                    family="MEASUREMENT",
                    measurement=report.measurement,
                    value=report.value,
                    unit=report.unit,
                    quality=report.quality,
                    unavailable_reason=report.unavailable_reason,
                )
            except EnvelopeRejected as error:
                raise _Held(error.kind, error.field, error.detail) from error
            text = canonical_envelope_v3_text(envelope)
            self._check_batchable(provisioning, snapshot, binding.source_id, text)
            db.execute(
                "INSERT INTO envelope_outbox (message_id, gateway_id, source_id, sequence_epoch, sequence, "
                "source_time, snapshot_sha256, envelope_text, sha256, state, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    message_id,
                    provisioning.gateway_id,
                    binding.source_id,
                    epoch,
                    sequence,
                    report.source_time,
                    snapshot.snapshot_sha256,
                    text,
                    text_sha256(text),
                    initial_state,
                    published_at,
                ),
            )
            db.execute(
                "INSERT INTO sequence_state VALUES (?,?,?,?,?) ON CONFLICT DO UPDATE "
                "SET last_sequence=excluded.last_sequence, updated_at=excluded.updated_at",
                (*key, sequence, published_at),
            )
            if report.report_key is not None:
                db.execute(
                    "INSERT INTO report_admission VALUES (?,?,?,?,?)",
                    (provisioning.gateway_id, binding.source_id, report.report_key, report_sha, message_id),
                )
            self._provenance(db, lab_run_ref, message_id=message_id)
            admission = Admission("ADMITTED", message_id=message_id, sequence=sequence)
        except _Held as held:
            hold_id = self._hold(db, report_text, report_sha, report, snapshot_sha256, held)
            self._provenance(db, lab_run_ref, hold_id=hold_id)
            return Admission("HELD", hold_id=hold_id, kind=held.kind, field=held.field, detail=held.detail)
        return admission

    def admit_all(
        self, reports: Iterable[DeviceReport], *, snapshot_sha256: str, lab_run_ref: str | None = None
    ) -> list[Admission]:
        return [
            self.admit(device_report_text(r), snapshot_sha256=snapshot_sha256, lab_run_ref=lab_run_ref)
            for r in reports
        ]

    @staticmethod
    def _check_batchable(
        provisioning: Provisioning, snapshot: VerifiedSnapshot, source_id: str, envelope_text: str
    ) -> None:
        """F1: an envelope that cannot be sealed even alone is held, never sequenced.

        Raised before the outbox insert and the sequence-state write, so the
        held report consumes no sequence and the transaction stays whole."""
        try:
            _seal(provisioning, snapshot, source_id, [envelope_text])
        except BatchRejected as error:
            raise _Held(
                "UNBATCHABLE",
                "value",
                f"this report cannot fit one Batch V2 even alone ({error.kind} at {error.field})",
            ) from error

    @staticmethod
    def _check_report(report: DeviceReport, binding: Binding, snapshot: VerifiedSnapshot, now: str) -> None:
        try:
            source = datetime.strptime(report.source_time, _INSTANT).replace(tzinfo=timezone.utc)
        except ValueError as error:
            raise _Held("INVALID_TIMING", "source_time", f"{report.source_time!r} is not a UTC instant") from error
        if not snapshot.valid_at(source):
            raise _Held(
                "OUTSIDE_VALIDITY",
                "source_time",
                f"{report.source_time} is outside the snapshot's Foundation/binding valid periods",
            )
        if report.source_time > now:
            raise _Held("SOURCE_TIME_IN_FUTURE", "source_time", f"{report.source_time} is after sealing time {now}")
        if report.unit != binding.source_unit:
            raise _Held(
                "UNIT_INCOMPATIBLE",
                "unit",
                f"{report.unit!r} is not the binding's source unit {binding.source_unit!r}",
            )
        if report.quality == "UNAVAILABLE" or report.value is None:
            return  # shape is checked by the envelope itself
        if binding.conversion_kind == "ENUM":
            labels = {label for label, _ in binding.enum_map}
            if report.value not in labels:
                raise _Held("INVALID_ENUM", "value", f"{report.value!r} is not a label of the binding's ENUM map")
            if not report.value or not set(report.value) <= _MEMBER_CHARS:
                raise _Held("INVALID_ENUM", "value", f"{report.value!r} is not a publishable member label")
        elif binding.canonical_unit == STATE_UNIT or not is_canonical_decimal(report.value):
            raise _Held("INVALID_VALUE", "value", f"{report.value!r} is not a canonical decimal reading")

    def _hold(
        self,
        db: sqlite3.Connection,
        report_text: object,
        report_sha: str,
        report: DeviceReport | None,
        snapshot_sha256: str,
        held: _Held,
    ) -> int:
        now = self._now()
        text = report_text if isinstance(report_text, str) else repr(report_text)
        existing = db.execute(
            "SELECT hold_id FROM mapping_hold WHERE report_sha256=? AND snapshot_sha256 IS ?",
            (report_sha, snapshot_sha256),
        ).fetchone()
        if existing is not None:
            db.execute(
                "UPDATE mapping_hold SET last_seen_at=?, seen_count=seen_count+1 WHERE hold_id=?",
                (now, existing[0]),
            )
            return existing[0]
        cursor = db.execute(
            "INSERT INTO mapping_hold (snapshot_sha256, device_id, signal_id, source_time, kind, field, detail, "
            "report_text, report_sha256, first_seen_at, last_seen_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                snapshot_sha256,
                None if report is None else report.device_id,
                None if report is None else report.signal_id,
                None if report is None else report.source_time,
                held.kind,
                held.field,
                held.detail,
                text,
                report_sha,
                now,
                now,
            ),
        )
        return int(cursor.lastrowid)

    def _provenance(
        self,
        db: sqlite3.Connection,
        lab_run_ref: str | None,
        *,
        message_id: str | None = None,
        hold_id: int | None = None,
    ) -> None:
        if lab_run_ref is None:
            return
        db.execute(
            "INSERT OR IGNORE INTO lab_report_provenance VALUES (?,?,?,?)",
            (lab_run_ref, message_id, hold_id, self._now()),
        )

    # --- sealing ---------------------------------------------------------------

    def seal(self, *, max_envelopes: int = MAX_BATCH_ENVELOPES) -> list[str]:
        """Seal every unsealed envelope into homogeneous batches; return new ids.

        Each group (source, epoch, snapshot, state) is cut in sequence order into
        the longest prefixes that fit both `max_envelopes` and Batch V2's byte
        bound (F1). A group that cannot be sealed keeps its envelopes unbatched
        from that point, records a durable `seal_refusal`, and does not stop
        other groups; the call then raises `SEAL_REFUSED` after committing."""
        if not 1 <= max_envelopes <= MAX_BATCH_ENVELOPES:
            raise ValueError("batch bound out of range")
        created: list[str] = []
        refusals: list[str] = []
        with self._tx() as db:
            provisioning, _ = self._provisioning(db)
            rows = db.execute(
                "SELECT o.message_id, o.source_id, o.sequence_epoch, o.snapshot_sha256, o.sequence, "
                "o.envelope_text, o.state FROM envelope_outbox o "
                "LEFT JOIN batch_item b ON b.message_id=o.message_id "
                "WHERE b.message_id IS NULL AND o.state IN ('STAGED','READY') "
                "ORDER BY o.source_id, o.sequence_epoch, o.snapshot_sha256, o.state, o.sequence"
            ).fetchall()
            groups: dict[tuple[str, str, str, str], list[tuple]] = {}
            for row in rows:
                groups.setdefault((row[1], row[2], row[3], row[6]), []).append(row)
            for (source_id, epoch, snapshot_sha, state), members in groups.items():
                snapshot = self._snapshot(db, snapshot_sha)
                assert snapshot is not None
                start = 0
                try:
                    while start < len(members):
                        chunk, batch, text = _fit(provisioning, snapshot, source_id, members[start:], max_envelopes)
                        self._insert_batch(db, batch, text, epoch, snapshot, state, chunk)
                        created.append(batch.batch_id)
                        start += len(chunk)
                except BatchRejected as error:
                    self._record_seal_refusal(db, source_id, epoch, snapshot_sha, members[start][0], error)
                    refusals.append(f"{source_id}: {error}")
                    continue
                db.execute(
                    "DELETE FROM seal_refusal WHERE source_id=? AND sequence_epoch=? AND snapshot_sha256=?",
                    (source_id, epoch, snapshot_sha),
                )
        self._hit("after_seal_commit")
        if refusals:
            raise GatewayRefused("SEAL_REFUSED", "; ".join(refusals))
        return created

    def _insert_batch(
        self,
        db: sqlite3.Connection,
        batch,
        text: str,
        epoch: str,
        snapshot: VerifiedSnapshot,
        state: str,
        chunk: list[tuple],
    ) -> None:
        db.execute(
            "INSERT INTO upload_batch (batch_id, site_id, gateway_id, source_id, sequence_epoch, "
            "snapshot_sha256, foundation_version, binding_set_id, binding_set_version, payload_text, "
            "sha256, state, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                batch.batch_id,
                batch.site_id,
                batch.gateway_id,
                batch.source_id,
                epoch,
                snapshot.snapshot_sha256,
                snapshot.foundation_version,
                snapshot.binding_set_id,
                snapshot.binding_set_version,
                text,
                batch.payload_sha256,
                state,
                self._now(),
            ),
        )
        db.executemany(
            "INSERT INTO batch_item VALUES (?,?,?)",
            [(batch.batch_id, ordinal, m[0]) for ordinal, m in enumerate(chunk)],
        )

    def _record_seal_refusal(
        self,
        db: sqlite3.Connection,
        source_id: str,
        epoch: str,
        snapshot_sha: str,
        message_id: str,
        error: BatchRejected,
    ) -> None:
        now = self._now()
        db.execute(
            "INSERT INTO seal_refusal (source_id, sequence_epoch, snapshot_sha256, message_id, kind, field, "
            "detail, first_seen_at, last_seen_at) VALUES (?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT (source_id, sequence_epoch, snapshot_sha256) DO UPDATE SET "
            "message_id=excluded.message_id, kind=excluded.kind, field=excluded.field, "
            "detail=excluded.detail, last_seen_at=excluded.last_seen_at, seen_count=seen_count+1",
            (source_id, epoch, snapshot_sha, message_id, error.kind, error.field, error.detail, now, now),
        )

    # --- local delivery states (S2-02 adds the network) ------------------------

    def mark_ready(self, batch_id: str) -> None:
        self._move(batch_id, "STAGED", "READY")

    def begin_attempt(self, batch_id: str) -> str:
        """READY -> IN_FLIGHT; returns the exact sealed bytes to send."""
        with self._tx() as db:
            row = db.execute("SELECT state, payload_text FROM upload_batch WHERE batch_id=?", (batch_id,)).fetchone()
            if row is None or row[0] != "READY":
                raise GatewayRefused("NOT_READY", f"batch {batch_id} is {None if row is None else row[0]}")
            now = self._now()
            db.execute(
                "UPDATE upload_batch SET state='IN_FLIGHT', attempt_count=attempt_count+1, last_attempt_at=? "
                "WHERE batch_id=?",
                (now, batch_id),
            )
            db.execute(
                "UPDATE envelope_outbox SET state='IN_FLIGHT', last_attempt_at=? WHERE message_id IN "
                "(SELECT message_id FROM batch_item WHERE batch_id=?)",
                (now, batch_id),
            )
            return row[1]

    def attempt_failed(self, batch_id: str, *, next_attempt_at: str) -> None:
        with self._tx() as db:
            self._move_in(db, batch_id, "IN_FLIGHT", "READY")
            db.execute("UPDATE upload_batch SET next_attempt_at=? WHERE batch_id=?", (next_attempt_at, batch_id))

    def _move(self, batch_id: str, source: str, target: str) -> None:
        with self._tx() as db:
            self._move_in(db, batch_id, source, target)

    @staticmethod
    def _move_in(db: sqlite3.Connection, batch_id: str, source: str, target: str) -> None:
        row = db.execute("SELECT state FROM upload_batch WHERE batch_id=?", (batch_id,)).fetchone()
        if row is None or row[0] != source:
            raise GatewayRefused("WRONG_STATE", f"batch {batch_id} is {None if row is None else row[0]}, not {source}")
        db.execute("UPDATE upload_batch SET state=? WHERE batch_id=?", (target, batch_id))
        db.execute(
            "UPDATE envelope_outbox SET state=? WHERE message_id IN (SELECT message_id FROM batch_item WHERE batch_id=?)",
            (target, batch_id),
        )


# --- reads (no writer lock) -----------------------------------------------------


@dataclass(frozen=True)
class EnvelopeRow:
    message_id: str
    source_id: str
    sequence_epoch: str
    sequence: int
    source_time: str
    snapshot_sha256: str
    envelope_text: str
    sha256: str
    state: str
    batch_id: str | None
    ordinal: int | None


@dataclass(frozen=True)
class BatchRow:
    batch_id: str
    source_id: str
    sequence_epoch: str
    snapshot_sha256: str
    payload_text: str
    sha256: str
    state: str
    attempt_count: int
    message_ids: tuple[str, ...]


@dataclass(frozen=True)
class HoldRow:
    hold_id: int
    kind: str
    field: str
    detail: str
    device_id: str | None
    signal_id: str | None
    source_time: str | None
    seen_count: int


@dataclass(frozen=True)
class SealRefusalRow:
    """A durable sealing refusal for a group holding this run's unbatched envelopes."""

    source_id: str
    sequence_epoch: str
    snapshot_sha256: str
    message_id: str
    kind: str
    field: str
    detail: str
    last_seen_at: str
    seen_count: int


@dataclass(frozen=True)
class RunStage:
    """What a Lab run handed the gateway, as the durable ledger holds it."""

    lab_run_ref: str
    sequence_epoch: str | None
    envelopes: tuple[EnvelopeRow, ...]
    batches: tuple[BatchRow, ...]
    holds: tuple[HoldRow, ...]
    queue_depth_by_state: dict[str, int]
    seal_refusals: tuple[SealRefusalRow, ...] = ()


class GatewayReader:
    def __init__(self, path: Path) -> None:
        self._db = open_reader_connection(Path(path))

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "GatewayReader":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def run_stage(self, lab_run_ref: str) -> RunStage:
        db = self._db
        db.execute("BEGIN")
        try:
            epoch_row = db.execute("SELECT sequence_epoch FROM gateway_identity").fetchone()
            envelopes = tuple(
                EnvelopeRow(*r)
                for r in db.execute(
                    "SELECT o.message_id, o.source_id, o.sequence_epoch, o.sequence, o.source_time, "
                    "o.snapshot_sha256, o.envelope_text, o.sha256, o.state, b.batch_id, b.ordinal "
                    "FROM lab_report_provenance p JOIN envelope_outbox o ON o.message_id=p.message_id "
                    "LEFT JOIN batch_item b ON b.message_id=o.message_id WHERE p.lab_run_ref=? "
                    "ORDER BY o.source_id, o.sequence_epoch, o.sequence",
                    (lab_run_ref,),
                )
            )
            batch_ids = sorted({e.batch_id for e in envelopes if e.batch_id is not None})
            batches = []
            for batch_id in batch_ids:
                r = db.execute(
                    "SELECT batch_id, source_id, sequence_epoch, snapshot_sha256, payload_text, sha256, state, "
                    "attempt_count FROM upload_batch WHERE batch_id=?",
                    (batch_id,),
                ).fetchone()
                ids = tuple(
                    m[0]
                    for m in db.execute(
                        "SELECT message_id FROM batch_item WHERE batch_id=? ORDER BY ordinal", (batch_id,)
                    )
                )
                batches.append(BatchRow(*r, message_ids=ids))
            holds = tuple(
                HoldRow(*r)
                for r in db.execute(
                    "SELECT h.hold_id, h.kind, h.field, h.detail, h.device_id, h.signal_id, h.source_time, "
                    "h.seen_count FROM lab_report_provenance p JOIN mapping_hold h ON h.hold_id=p.hold_id "
                    "WHERE p.lab_run_ref=? ORDER BY h.hold_id",
                    (lab_run_ref,),
                )
            )
            unbatched = sorted(
                {(e.source_id, e.sequence_epoch, e.snapshot_sha256) for e in envelopes if e.batch_id is None}
            )
            refusals = []
            for group in unbatched:
                r = db.execute(
                    "SELECT source_id, sequence_epoch, snapshot_sha256, message_id, kind, field, detail, "
                    "last_seen_at, seen_count FROM seal_refusal "
                    "WHERE source_id=? AND sequence_epoch=? AND snapshot_sha256=?",
                    group,
                ).fetchone()
                if r is not None:
                    refusals.append(SealRefusalRow(*r))
        finally:
            db.execute("COMMIT")
        depth: dict[str, int] = {}
        for e in envelopes:
            depth[e.state] = depth.get(e.state, 0) + 1
        return RunStage(
            lab_run_ref=lab_run_ref,
            sequence_epoch=None if epoch_row is None else epoch_row[0],
            envelopes=envelopes,
            batches=tuple(batches),
            holds=holds,
            queue_depth_by_state=depth,
            seal_refusals=tuple(refusals),
        )
