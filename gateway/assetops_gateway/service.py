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
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable

from assetops_contracts.gateway_report import (
    DeviceReport,
    device_report_text,
    parse_device_report_text,
)
from assetops_contracts.gateway_diagnostics import (
    DISK_PRESSURES,
    DiagnosticConfig,
    parse_diagnostic_config_text,
    seal_gateway_diagnostics_v1,
)
from assetops_contracts.ingestion_batch_v2 import MAX_BATCH_ENVELOPES, BatchRejected, seal_batch_v2
from assetops_contracts.ingestion_receipt_v2 import (
    RECEIPT_DECISIONS,
    IngestionReceiptV2,
    ReceiptRejected,
    parse_canonical_receipt_v2_text,
    receipt_v2_sha256,
)
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


#: The hold kinds the diagnostic `mapping_error_count` counts
#: (`D-2026-10-09-s2-gateway-diagnostic-semantics`). Invalid values, conflicting
#: reports, exhausted sequences and batching refusals are holds, not mapping errors.
MAPPING_ERROR_KINDS = (
    "NO_ACTIVE_MAPPING",
    "UNKNOWN_CHANNEL",
    "SOURCE_NOT_PERMITTED",
    "OUTSIDE_VALIDITY",
    "UNIT_INCOMPATIBLE",
    "INVALID_ENUM",
)


#: Which clock stamps V3 `published_at` for an admission.
GATEWAY_UTC = "GATEWAY_UTC"
RUN_VIRTUAL = "RUN_VIRTUAL"


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
FAULT_POINTS = (
    "after_sequence_read",
    "after_enqueue_commit",
    "after_seal_commit",
    "after_diagnostic_sequence_read",
    "after_diagnostic_commit",
    "after_receipt_commit",
)

#: S2-02: retry back-off for a failed upload attempt (seconds).
RETRY_BASE_SECONDS = 5
RETRY_CAP_SECONDS = 300

#: Outbox states still awaiting a central disposition: the local queue.
QUEUED_STATES = ("STAGED", "READY", "IN_FLIGHT")
#: `health_observation` names. Contacts are `source_contact:<source_id>`.
_CONTACT = "source_contact:"
_CLOCK_OFFSET = "clock_offset_ms"
_DISK_PRESSURE = "disk_pressure"
INJECTED = "INJECTED_FAULT_FIXTURE"


def _default_disk_free(path: Path) -> Callable[[], int]:
    return lambda: shutil.disk_usage(path.parent).free


class GatewayService:
    def __init__(
        self,
        path: Path,
        *,
        clock: Callable[[], datetime] = _utc_now,
        fault: Callable[[str], None] | None = None,
        disk_free: Callable[[], int] | None = None,
    ) -> None:
        self.path = Path(path)
        self._clock = clock
        self._fault = fault
        #: The measured free-space probe behind MEASURED disk pressure.
        self._disk_free = disk_free or _default_disk_free(self.path)
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
            # S2-02: an interrupted diagnostic send is retried with its exact bytes.
            self._db.execute("UPDATE diagnostic_outbox SET state='READY' WHERE state='IN_FLIGHT'")

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

    def provision(
        self, provisioning: Provisioning, *, sequence_epoch: str, diagnostics: DiagnosticConfig | None = None
    ) -> None:
        """Install this gateway's identity once; an identical repeat is a no-op.

        The diagnostic configuration (cadence, pressure triggers) is frozen with
        it: installed when absent (also on a ledger migrated from S2-01b), and a
        different declaration later refuses rather than silently moving the
        cadence a freshness judgement relies on."""
        with self._tx() as db:
            self._freeze_diagnostic_config(db, diagnostics or DiagnosticConfig())
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

    def _freeze_diagnostic_config(self, db: sqlite3.Connection, config: DiagnosticConfig) -> None:
        text = config.text()
        row = db.execute("SELECT config_text FROM diagnostic_config").fetchone()
        if row is None:
            db.execute("INSERT INTO diagnostic_config VALUES (1,?,?,?)", (text, text_sha256(text), self._now()))
        elif row[0] != text:
            raise GatewayRefused("DIAGNOSTIC_CONFIG_FIXED", "this gateway's diagnostic configuration is frozen")

    @staticmethod
    def _diagnostic_config(db: sqlite3.Connection) -> tuple[DiagnosticConfig, str, str]:
        row = db.execute("SELECT config_text, sha256 FROM diagnostic_config").fetchone()
        if row is None:
            raise GatewayRefused("NOT_PROVISIONED", "this gateway has no diagnostic configuration")
        return parse_diagnostic_config_text(row[0]), row[0], row[1]

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

    # --- the per-run virtual publication clock (S2-01c phase 2) -----------------

    def _publication_instant(self, db: sqlite3.Connection, clock: str, lab_run_ref: str | None) -> str | None:
        """None for the gateway's real UTC; the run's current virtual instant otherwise."""
        if clock == GATEWAY_UTC:
            return None
        if clock != RUN_VIRTUAL:
            raise ValueError(f"publication clock is one of {[GATEWAY_UTC, RUN_VIRTUAL]}")
        if not lab_run_ref:
            raise GatewayRefused("NO_PUBLICATION_CLOCK", "a virtual publication clock is scoped to a Lab run")
        row = db.execute("SELECT instant FROM publication_clock WHERE lab_run_ref=?", (lab_run_ref,)).fetchone()
        if row is None:
            raise GatewayRefused(
                "NO_PUBLICATION_CLOCK", "this run's publication clock has not been advanced; nothing is admitted"
            )
        return row[0]

    def advance_publication_clock(self, lab_run_ref: str, instant: str) -> dict[str, object]:
        """Move one run's virtual publication clock forward to `instant`.

        SIMULATED gateways only. An earlier instant refuses
        (`PUBLICATION_CLOCK_BACKWARD`); the same instant is idempotent. Nothing
        is admitted or released here: the clock only says what instant the
        next admission for this run is stamped with."""
        if not isinstance(lab_run_ref, str) or not lab_run_ref:
            raise ValueError("a publication clock is scoped to a non-empty Lab run reference")
        try:
            datetime.strptime(instant, _INSTANT)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{instant!r} is not a UTC instant (YYYY-MM-DDTHH:MM:SSZ)") from error
        with self._tx() as db:
            self._require_simulated(db)
            row = db.execute("SELECT instant FROM publication_clock WHERE lab_run_ref=?", (lab_run_ref,)).fetchone()
            if row is not None and instant < row[0]:
                raise GatewayRefused(
                    "PUBLICATION_CLOCK_BACKWARD", f"the run's publication clock is at {row[0]}, after {instant}"
                )
            advanced = row is None or instant > row[0]
            if row is None:
                db.execute("INSERT INTO publication_clock VALUES (?,?,?)", (lab_run_ref, instant, self._now()))
            elif advanced:
                db.execute(
                    "UPDATE publication_clock SET instant=?, updated_at=? WHERE lab_run_ref=?",
                    (instant, self._now(), lab_run_ref),
                )
        return {"lab_run_ref": lab_run_ref, "instant": instant, "advanced": advanced}

    def _clock_at(
        self, db: sqlite3.Connection, clock: str, lab_run_ref: str | None, at_instant: str
    ) -> tuple[str, bool]:
        """Advance the run clock to `at_instant` in `db`; (instant, passed)."""
        if clock != RUN_VIRTUAL:
            raise ValueError("an admission instant is a RUN_VIRTUAL admission's")
        if not lab_run_ref:
            raise GatewayRefused("NO_PUBLICATION_CLOCK", "a virtual publication clock is scoped to a Lab run")
        try:
            datetime.strptime(at_instant, _INSTANT)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{at_instant!r} is not a UTC instant (YYYY-MM-DDTHH:MM:SSZ)") from error
        self._require_simulated(db)
        row = db.execute("SELECT instant FROM publication_clock WHERE lab_run_ref=?", (lab_run_ref,)).fetchone()
        if row is None:
            db.execute("INSERT INTO publication_clock VALUES (?,?,?)", (lab_run_ref, at_instant, self._now()))
        elif at_instant > row[0]:
            db.execute(
                "UPDATE publication_clock SET instant=?, updated_at=? WHERE lab_run_ref=?",
                (at_instant, self._now(), lab_run_ref),
            )
        return at_instant, row is not None and at_instant < row[0]

    def publication_clock(self, lab_run_ref: str) -> str | None:
        with self._tx() as db:
            row = db.execute("SELECT instant FROM publication_clock WHERE lab_run_ref=?", (lab_run_ref,)).fetchone()
        return None if row is None else row[0]

    # --- admission -------------------------------------------------------------

    def admit(
        self,
        report_text: str,
        *,
        snapshot_sha256: str,
        lab_run_ref: str | None = None,
        initial_state: str = "STAGED",
        publication_clock: str = GATEWAY_UTC,
    ) -> Admission:
        """Admit one public report under one activated snapshot."""
        _check_initial_state(initial_state)
        with self._tx() as db:
            self._refuse_at_stop(db)
            published_at = self._publication_instant(db, publication_clock, lab_run_ref)
            admission = self._admit_in(db, report_text, snapshot_sha256, lab_run_ref, initial_state, published_at)
        self._hit("after_enqueue_commit")
        return admission

    def admit_texts(
        self,
        report_texts: Iterable[str],
        *,
        snapshot_sha256: str,
        lab_run_ref: str | None = None,
        initial_state: str = "STAGED",
        publication_clock: str = GATEWAY_UTC,
        at_instant: str | None = None,
    ) -> list[Admission]:
        """Admit a bounded chunk of reports in ONE transaction.

        Same per-report rules as `admit`; the chunk commits or rolls back whole,
        so a crash leaves either every report of the chunk admitted or none.
        One transaction per report made a full-day Lab run slow (phase-1 risk).

        `at_instant` (RUN_VIRTUAL only; `D-2026-10-09-s2-ordered-publication-
        and-closing-boundary`): the reports' own reached boundary. The run clock
        moves forward to it in this same transaction, and the chunk is stamped
        with it. If the clock has already passed it, nothing new is admitted: a
        report already admitted answers with its first identity, and any other
        refuses the whole chunk `PUBLICATION_INSTANT_PASSED` rather than be
        stamped with a later, undeclared publication instant."""
        _check_initial_state(initial_state)
        texts = list(report_texts)
        if len(texts) > MAX_ADMISSION_CHUNK:
            raise ValueError(f"at most {MAX_ADMISSION_CHUNK} reports per admission chunk")
        with self._tx() as db:
            self._refuse_at_stop(db)
            passed = False
            if at_instant is not None:
                published_at, passed = self._clock_at(db, publication_clock, lab_run_ref, at_instant)
            else:
                published_at = self._publication_instant(db, publication_clock, lab_run_ref)
            admissions = [
                self._admit_in(
                    db, text, snapshot_sha256, lab_run_ref, initial_state, published_at, replay_only=passed
                )
                for text in texts
            ]
        self._hit("after_enqueue_commit")
        return admissions

    def _admit_in(
        self,
        db: sqlite3.Connection,
        report_text: str,
        snapshot_sha256: str,
        lab_run_ref: str | None,
        initial_state: str,
        virtual_published_at: str | None = None,
        *,
        replay_only: bool = False,
    ) -> Admission:
        """`virtual_published_at` is the run's virtual publication instant
        (`D-2026-10-09-s2-simulated-publication-clock`), or None for the
        gateway's real UTC. Either way the outbox creation time, the sequence
        update and the contact stay on real UTC: queue age is operational."""
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
            self._record_contact(db, provisioning, binding.source_id)
            created_at = self._now()
            published_at = created_at if virtual_published_at is None else virtual_published_at
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
            if replay_only:
                # The run clock is past this report's boundary and it was never
                # admitted: stamping it now would fabricate a publication delay.
                raise GatewayRefused(
                    "PUBLICATION_INSTANT_PASSED",
                    f"the run's publication clock is past {virtual_published_at}; "
                    f"{report.device_id}/{report.signal_id} at {report.source_time} was never admitted there",
                )
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
                    created_at,
                ),
            )
            db.execute(
                "INSERT INTO sequence_state VALUES (?,?,?,?,?) ON CONFLICT DO UPDATE "
                "SET last_sequence=excluded.last_sequence, updated_at=excluded.updated_at",
                (*key, sequence, created_at),
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
            if error.kind == "TOO_LARGE" and error.field == "batch":
                raise _Held(
                    "UNBATCHABLE",
                    "value",
                    f"this report cannot fit one Batch V2 even alone ({error.kind} at {error.field})",
                ) from error
            # Any other cause keeps its actual kind and field as a typed refusal.
            raise _Held(error.kind, error.field, error.detail) from error

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
                    self._record_seal_refusal(db, source_id, epoch, snapshot_sha, state, members[start][0], error)
                    refusals.append(f"{source_id}: {error}")
                    continue
                # R1: only this group's own refusal clears; a sibling group of
                # the same source/epoch/snapshot in another state keeps its own.
                db.execute(
                    "DELETE FROM seal_refusal WHERE source_id=? AND sequence_epoch=? AND snapshot_sha256=? "
                    "AND outbox_state=?",
                    (source_id, epoch, snapshot_sha, state),
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
        state: str,
        message_id: str,
        error: BatchRejected,
    ) -> None:
        now = self._now()
        db.execute(
            "INSERT INTO seal_refusal (source_id, sequence_epoch, snapshot_sha256, outbox_state, message_id, kind, "
            "field, detail, first_seen_at, last_seen_at) VALUES (?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT (source_id, sequence_epoch, snapshot_sha256, outbox_state) DO UPDATE SET "
            "message_id=excluded.message_id, kind=excluded.kind, field=excluded.field, "
            "detail=excluded.detail, last_seen_at=excluded.last_seen_at, seen_count=seen_count+1",
            (source_id, epoch, snapshot_sha, state, message_id, error.kind, error.field, error.detail, now, now),
        )

    # --- diagnostics (S2-01c phase 1) -------------------------------------------

    def _record_contact(self, db: sqlite3.Connection, provisioning: Provisioning, source_id: str) -> None:
        """A public report naming this source arrived: the gateway heard it now.

        Recorded once the report resolves to a permitted source, whether it is
        then admitted or held. The time is the gateway's own (real UTC) clock,
        not the report's source time. On a SIMULATED gateway the provenance
        says so: it is not proof of contact with a physical device."""
        provenance = "OBSERVED_SIMULATED_REPORT" if provisioning.source_mode == "SIMULATED" else "OBSERVED_DEVICE_REPORT"
        now = self._now()
        db.execute(
            "INSERT INTO health_observation VALUES (?,?,?,?) ON CONFLICT (name) DO UPDATE SET "
            "value_text=excluded.value_text, observed_at=excluded.observed_at, provenance=excluded.provenance",
            (_CONTACT + source_id, now, now, provenance),
        )

    def _disk(self, db: sqlite3.Connection, config: DiagnosticConfig) -> dict[str, object]:
        """The operative disk pressure and where it came from.

        An injected fault-fixture level wins and is labelled INJECTED: it never
        claims actual storage pressure. Otherwise the free-space probe is
        compared with the frozen WARN/STOP triggers. A probe that fails is
        STOP (fail closed), labelled UNMEASURABLE."""
        row = db.execute(
            "SELECT value_text, observed_at FROM health_observation WHERE name=?", (_DISK_PRESSURE,)
        ).fetchone()
        if row is not None:
            return {"level": row[0], "provenance": INJECTED, "free_bytes": None, "observed_at": row[1]}
        try:
            free = int(self._disk_free())
        except (OSError, ValueError, TypeError):
            return {"level": "STOP", "provenance": "UNMEASURABLE", "free_bytes": None, "observed_at": self._now()}
        return {"level": config.pressure(free), "provenance": "MEASURED", "free_bytes": free, "observed_at": self._now()}

    def _refuse_at_stop(self, db: sqlite3.Connection) -> None:
        config, _, _ = self._diagnostic_config(db)
        disk = self._disk(db, config)
        if disk["level"] == "STOP":
            raise GatewayRefused(
                "DISK_PRESSURE_STOP",
                f"acquisition refused before any sequence ({disk['provenance']} disk pressure STOP); "
                "existing envelopes and batches are retained",
            )

    def _require_simulated(self, db: sqlite3.Connection) -> None:
        provisioning, _ = self._provisioning(db)
        if provisioning.source_mode != "SIMULATED":
            raise GatewayRefused("NOT_SIMULATED", "fault-fixture injection exists only on a SIMULATED gateway")

    def inject_disk_pressure(self, level: str | None) -> None:
        """Fault fixture: force OK/WARN/STOP, or clear (None) back to measurement."""
        if level is not None and level not in DISK_PRESSURES:
            raise ValueError(f"disk pressure is one of {list(DISK_PRESSURES)} or None")
        with self._tx() as db:
            self._require_simulated(db)
            if level is None:
                db.execute("DELETE FROM health_observation WHERE name=?", (_DISK_PRESSURE,))
            else:
                db.execute(
                    "INSERT OR REPLACE INTO health_observation VALUES (?,?,?,?)",
                    (_DISK_PRESSURE, level, self._now(), INJECTED),
                )

    def inject_clock_offset(self, offset_ms: int | None) -> None:
        """Fault fixture: a labelled clock offset, or clear (None) back to unknown."""
        if offset_ms is not None and type(offset_ms) is not int:
            raise ValueError("a clock offset is whole milliseconds")
        with self._tx() as db:
            self._require_simulated(db)
            if offset_ms is None:
                db.execute("DELETE FROM health_observation WHERE name=?", (_CLOCK_OFFSET,))
            else:
                db.execute(
                    "INSERT OR REPLACE INTO health_observation VALUES (?,?,?,?)",
                    (_CLOCK_OFFSET, str(offset_ms), self._now(), INJECTED),
                )

    def _health(self, db: sqlite3.Connection, provisioning: Provisioning, config: DiagnosticConfig, now: datetime):
        """Every counter, derived from ledger rows at `now`."""
        queued = "('STAGED','READY','IN_FLIGHT')"
        count, oldest = db.execute(
            f"SELECT COUNT(*), MIN(created_at) FROM envelope_outbox WHERE state IN {queued}"
        ).fetchone()
        age = None
        if count:
            moment = datetime.strptime(oldest, _INSTANT).replace(tzinfo=timezone.utc)
            age = max(0, int((now - moment).total_seconds()))
        sealed_envelopes = db.execute(
            "SELECT COUNT(*) FROM envelope_outbox o JOIN batch_item b ON b.message_id=o.message_id "
            f"WHERE o.state IN {queued}"
        ).fetchone()[0]
        queue = {
            "queue_count": count,
            "oldest_queued_at": oldest if count else None,
            "oldest_queue_age_seconds": age,
            "sealed_pending_batches": db.execute(
                f"SELECT COUNT(*) FROM upload_batch WHERE state IN {queued}"
            ).fetchone()[0],
            "sealed_pending_envelopes": sealed_envelopes,
            "unbatched_envelopes": count - sealed_envelopes,
            "held_reports": db.execute("SELECT COUNT(*) FROM mapping_hold").fetchone()[0],
            "active_seal_refusals": db.execute("SELECT COUNT(*) FROM seal_refusal").fetchone()[0],
            "dead_letter_envelopes": db.execute(
                "SELECT COUNT(*) FROM envelope_outbox WHERE state='DEAD_LETTER'"
            ).fetchone()[0],
        }
        contacts = []
        for source_id in sorted(provisioning.permitted_source_ids):
            row = db.execute(
                "SELECT value_text, provenance FROM health_observation WHERE name=?", (_CONTACT + source_id,)
            ).fetchone()
            contacts.append(
                {
                    "source_id": source_id,
                    "last_contact_at": None if row is None else row[0],
                    "provenance": None if row is None else row[1],
                }
            )
        clock = db.execute(
            "SELECT value_text, provenance, observed_at FROM health_observation WHERE name=?", (_CLOCK_OFFSET,)
        ).fetchone()
        return {
            "queue": queue,
            # D-2026-10-09-s2-gateway-diagnostic-semantics: mapping/registration
            # holds only; every other hold stays in `held_reports`.
            "mapping_error_count": db.execute(
                "SELECT COUNT(*) FROM mapping_hold WHERE kind IN (%s)" % ",".join("?" * len(MAPPING_ERROR_KINDS)),
                MAPPING_ERROR_KINDS,
            ).fetchone()[0],
            "source_contacts": contacts,
            "clock_offset": {
                "value_ms": None if clock is None else int(clock[0]),
                "provenance": None if clock is None else clock[1],
                "observed_at": None if clock is None else clock[2],
            },
            "disk_pressure": self._disk(db, config),
        }

    def emit_diagnostic(self) -> "DiagnosticRow":
        """Allocate and store one GatewayDiagnosticsV1 for the current cadence slot.

        One transaction allocates the sequence and stores the exact bytes and
        hash. At most one diagnostic exists per declared cadence slot, so a
        retry (or a restart) inside the slot returns the same identity and
        bytes instead of a second report. The row starts and stays READY:
        nothing here sends it or marks it received (S2-02). Emission is not
        acquisition, so it continues at STOP pressure while storage permits."""
        with self._tx() as db:
            provisioning, epoch = self._provisioning(db)
            config, _, _ = self._diagnostic_config(db)
            now = self._clock()
            slot = int(now.timestamp()) // config.emission_cadence_seconds
            existing = db.execute(
                f"SELECT {_DIAGNOSTIC_COLUMNS} FROM diagnostic_outbox "
                "WHERE gateway_id=? AND sequence_epoch=? AND cadence_slot=?",
                (provisioning.gateway_id, epoch, slot),
            ).fetchone()
            if existing is not None:
                return DiagnosticRow(*existing)
            last_sequence, last_slot = db.execute(
                "SELECT MAX(diagnostic_sequence), MAX(cadence_slot) FROM diagnostic_outbox "
                "WHERE gateway_id=? AND sequence_epoch=?",
                (provisioning.gateway_id, epoch),
            ).fetchone()
            if last_slot is not None and slot < last_slot:
                raise GatewayRefused("CLOCK_BEHIND", "the gateway clock is behind its last diagnostic")
            if last_sequence is not None and last_sequence >= MAX_SEQUENCE:
                raise GatewayRefused("SEQUENCE_EXHAUSTED", "reprovision a new epoch to continue diagnostics")
            sequence = 1 if last_sequence is None else last_sequence + 1
            self._hit("after_diagnostic_sequence_read")
            health = self._health(db, provisioning, config, now)
            observed_at = _text(now)
            diagnostic, text = seal_gateway_diagnostics_v1(
                site_id=provisioning.site_id,
                gateway_id=provisioning.gateway_id,
                sequence_epoch=epoch,
                diagnostic_sequence=sequence,
                observed_at=observed_at,
                last_device_contact_by_source={c["source_id"]: c["last_contact_at"] for c in health["source_contacts"]},
                queue_count=health["queue"]["queue_count"],
                oldest_queue_age_seconds=health["queue"]["oldest_queue_age_seconds"],
                disk_pressure=health["disk_pressure"]["level"],
                clock_offset_ms=health["clock_offset"]["value_ms"],
                mapping_error_count=health["mapping_error_count"],
            )
            db.execute(
                "INSERT INTO diagnostic_outbox (gateway_id, sequence_epoch, diagnostic_sequence, cadence_slot, "
                "payload_text, sha256, state, observed_at) VALUES (?,?,?,?,?,?,'READY',?)",
                (provisioning.gateway_id, epoch, sequence, slot, text, diagnostic.payload_sha256, observed_at),
            )
            row = DiagnosticRow(
                provisioning.gateway_id, epoch, sequence, observed_at, text, diagnostic.payload_sha256, "READY", None
            )
        self._hit("after_diagnostic_commit")
        return row

    def local_diagnostics(self, *, limit: int = 20) -> dict[str, object]:
        """The local read: frozen configuration, live counters and stored diagnostics.

        `observed_at` is the real UTC time of this read. Nothing in it is a
        server receipt; every stored diagnostic is pending upload (S2-02)."""
        if not 1 <= limit <= 200:
            raise ValueError("limit out of range")
        with self._tx() as db:
            provisioning, epoch = self._provisioning(db)
            config, config_text, config_sha = self._diagnostic_config(db)
            now = self._clock()
            health = self._health(db, provisioning, config, now)
            rows = [
                DiagnosticRow(*r)
                for r in db.execute(
                    f"SELECT {_DIAGNOSTIC_COLUMNS} FROM diagnostic_outbox "
                    "ORDER BY sequence_epoch DESC, diagnostic_sequence DESC LIMIT ?",
                    (limit,),
                )
            ]
            total, pending = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(state<>'ACKED'),0) FROM diagnostic_outbox"
            ).fetchone()
        return {
            "site_id": provisioning.site_id,
            "gateway_id": provisioning.gateway_id,
            "source_mode": provisioning.source_mode,
            "sequence_epoch": epoch,
            "observed_at": _text(now),
            "config": {"text": config_text, "sha256": config_sha, **config.document()},
            **health,
            "acquisition": "REFUSED_DISK_PRESSURE_STOP" if health["disk_pressure"]["level"] == "STOP" else "ACCEPTING",
            "diagnostics": [dict(r.__dict__) for r in rows],
            "diagnostic_count": total,
            "pending_diagnostic_count": pending,
            # S2-02: ACKED only once every stored diagnostic has a verified central receipt.
            "upload": "ACKED" if total and not pending else "PENDING",
        }

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

    # --- S2-02 phase 2: Lab Commit release and authenticated delivery ----------

    def release_run(self, lab_run_ref: str) -> dict[str, object]:
        """Lab Commit: authorize this run's sealed `STAGED` batches for upload.

        One transaction moves every STAGED batch whose every item this run
        handed the gateway (`lab_report_provenance`) to READY, with its
        envelopes, and appends one `release_manifest` row per batch. Idempotent:
        a second call releases nothing new and returns the same summary. A batch
        that also carries another run's envelope is never released here (it
        would upload a report that run did not commit); it is reported and keeps
        the run from being complete. Unbatched envelopes, seal refusals and holds
        are untouched: a partial run releases what is sealed and says so."""
        released: list[str] = []
        with self._tx() as db:
            now = self._now()
            for batch_id, foreign in _run_batches(db, lab_run_ref):
                if foreign:
                    continue
                state = db.execute("SELECT state FROM upload_batch WHERE batch_id=?", (batch_id,)).fetchone()[0]
                if state == "STAGED":
                    self._move_in(db, batch_id, "STAGED", "READY")
                inserted = db.execute(
                    "INSERT OR IGNORE INTO release_manifest (lab_run_ref, batch_id, released_at) VALUES (?,?,?)",
                    (lab_run_ref, batch_id, now),
                ).rowcount
                if inserted:
                    released.append(batch_id)
            summary = run_delivery_in(db, lab_run_ref)
        return {"released_batch_ids": released, "released_now": len(released), "delivery": summary}

    def due_batches(self, limit: int) -> list[str]:
        """READY batches whose retry time has come, oldest first, at most `limit`."""
        with self._tx() as db:
            now = self._now()
            return [
                r[0]
                for r in db.execute(
                    "SELECT batch_id FROM upload_batch WHERE state='READY' "
                    "AND (next_attempt_at IS NULL OR next_attempt_at <= ?) "
                    "ORDER BY created_at, rowid LIMIT ?",
                    (now, limit),
                )
            ]

    def batch_expectation(self, batch_id: str) -> "BatchExpectation":
        with self._tx() as db:
            row = db.execute(
                "SELECT site_id, gateway_id, source_id, sha256 FROM upload_batch WHERE batch_id=?", (batch_id,)
            ).fetchone()
            if row is None:
                raise GatewayRefused("UNKNOWN_BATCH", batch_id)
            items = tuple(
                (o, m)
                for o, m in db.execute(
                    "SELECT ordinal, message_id FROM batch_item WHERE batch_id=? ORDER BY ordinal", (batch_id,)
                )
            )
        return BatchExpectation(batch_id, row[0], row[1], row[2], row[3], items)

    def record_receipt(self, batch_id: str, receipt_text: str) -> dict[str, int]:
        """Persist a COMPLETED, verified receipt: acks, receipt, terminal states, in ONE transaction.

        The receipt is verified here against the batch's own identity, digest
        and items before anything is written; a mismatch raises
        `ReceiptMismatch` and writes nothing. ACCEPTED/DUPLICATE envelopes
        become ACKED; REJECTED/CONFLICT envelopes become DEAD_LETTER (the
        server's durable terminal decision, never retried). The batch is ACKED."""
        receipt = verify_receipt(receipt_text, self.batch_expectation(batch_id), complete=True)
        receipt_sha = receipt_v2_sha256(receipt)
        tally = {d: 0 for d in RECEIPT_DECISIONS}
        with self._tx() as db:
            state = db.execute("SELECT state FROM upload_batch WHERE batch_id=?", (batch_id,)).fetchone()[0]
            if state != "IN_FLIGHT":
                raise GatewayRefused("WRONG_STATE", f"batch {batch_id} is {state}, not IN_FLIGHT")
            for d in receipt.dispositions:
                db.execute(
                    "INSERT INTO acknowledgement (batch_id, ordinal, message_id, decision, server_evidence_id, "
                    "server_rejection_id, received_at, receipt_sha256) VALUES (?,?,?,?,?,?,?,?)",
                    (
                        batch_id,
                        d.ordinal,
                        d.message_id,
                        d.decision,
                        d.evidence_id,
                        None if d.rejection is None else d.rejection.rejection_id,
                        receipt.received_at,
                        receipt_sha,
                    ),
                )
                db.execute(
                    "UPDATE envelope_outbox SET state=? WHERE message_id=?",
                    ("ACKED" if d.decision in ("ACCEPTED", "DUPLICATE") else "DEAD_LETTER", d.message_id),
                )
                tally[d.decision] += 1
            db.execute(
                "INSERT INTO batch_receipt (batch_id, receipt_text, receipt_sha256, server_received_at, "
                "server_completed_at, stored_at) VALUES (?,?,?,?,?,?)",
                (batch_id, receipt_text, receipt_sha, receipt.received_at, receipt.completed_at, self._now()),
            )
            db.execute(
                "UPDATE upload_batch SET state='ACKED', last_error_code=NULL, last_error_at=NULL, "
                "next_attempt_at=NULL WHERE batch_id=?",
                (batch_id,),
            )
        self._hit("after_receipt_commit")
        return tally

    def _retry_at(self, attempts: int, retry_after_seconds: float | None) -> str:
        """`retry_after_seconds` None backs off by attempts (5 s doubling, at most 300 s)."""
        if retry_after_seconds is None:
            retry_after_seconds = min(RETRY_BASE_SECONDS * 2 ** max(attempts - 1, 0), RETRY_CAP_SECONDS)
        return _text(self._clock() + timedelta(seconds=retry_after_seconds))

    def record_retry(self, batch_id: str, *, code: str | None, retry_after_seconds: float | None) -> None:
        """IN_FLIGHT -> READY with unchanged bytes, the failure code and the next due time."""
        with self._tx() as db:
            self._move_in(db, batch_id, "IN_FLIGHT", "READY")
            attempts = db.execute("SELECT attempt_count FROM upload_batch WHERE batch_id=?", (batch_id,)).fetchone()[0]
            db.execute(
                "UPDATE upload_batch SET next_attempt_at=?, last_error_code=?, last_error_at=? WHERE batch_id=?",
                (self._retry_at(attempts, retry_after_seconds), code, None if code is None else self._now(), batch_id),
            )

    def record_batch_refusal(self, batch_id: str, *, http_status: int, code: str, detail: str) -> None:
        """An authenticated terminal whole-batch refusal: REFUSED, envelopes DEAD_LETTER."""
        with self._tx() as db:
            row = db.execute("SELECT state FROM upload_batch WHERE batch_id=?", (batch_id,)).fetchone()
            if row is None or row[0] != "IN_FLIGHT":
                raise GatewayRefused("WRONG_STATE", f"batch {batch_id} is not IN_FLIGHT")
            now = self._now()
            db.execute(
                "INSERT INTO batch_refusal (batch_id, http_status, code, detail, refused_at) VALUES (?,?,?,?,?)",
                (batch_id, http_status, code, detail[:500], now),
            )
            db.execute(
                "UPDATE upload_batch SET state='REFUSED', last_error_code=?, last_error_at=?, next_attempt_at=NULL "
                "WHERE batch_id=?",
                (code, now, batch_id),
            )
            db.execute(
                "UPDATE envelope_outbox SET state='DEAD_LETTER' WHERE message_id IN "
                "(SELECT message_id FROM batch_item WHERE batch_id=?)",
                (batch_id,),
            )

    def due_diagnostics(self, limit: int) -> list[tuple[str, str, int]]:
        with self._tx() as db:
            now = self._now()
            return [
                (r[0], r[1], r[2])
                for r in db.execute(
                    "SELECT gateway_id, sequence_epoch, diagnostic_sequence FROM diagnostic_outbox "
                    "WHERE state='READY' AND refusal_code IS NULL "
                    "AND (next_attempt_at IS NULL OR next_attempt_at <= ?) "
                    "ORDER BY observed_at, diagnostic_sequence LIMIT ?",
                    (now, limit),
                )
            ]

    def begin_diagnostic(self, key: tuple[str, str, int]) -> tuple[str, str]:
        """READY -> IN_FLIGHT; returns the exact stored bytes and their hash."""
        with self._tx() as db:
            row = db.execute(
                "SELECT state, payload_text, sha256 FROM diagnostic_outbox "
                "WHERE gateway_id=? AND sequence_epoch=? AND diagnostic_sequence=?",
                key,
            ).fetchone()
            if row is None or row[0] != "READY":
                raise GatewayRefused("NOT_READY", f"diagnostic {key} is {None if row is None else row[0]}")
            db.execute(
                "UPDATE diagnostic_outbox SET state='IN_FLIGHT', last_attempt_at=? "
                "WHERE gateway_id=? AND sequence_epoch=? AND diagnostic_sequence=?",
                (self._now(), *key),
            )
            return row[1], row[2]

    def diagnostic_acked(self, key: tuple[str, str, int], *, server_received_at: str) -> None:
        with self._tx() as db:
            db.execute(
                "UPDATE diagnostic_outbox SET state='ACKED', server_received_at=?, last_error_code=NULL, "
                "next_attempt_at=NULL WHERE gateway_id=? AND sequence_epoch=? AND diagnostic_sequence=? "
                "AND state='IN_FLIGHT'",
                (server_received_at, *key),
            )

    def diagnostic_failed(
        self, key: tuple[str, str, int], *, code: str, retry_after_seconds: float | None, refused: bool = False
    ) -> None:
        """Back to READY, never ACKED. A refusal (409/422) is recorded and not retried."""
        next_attempt_at = self._retry_at(1, retry_after_seconds)
        with self._tx() as db:
            db.execute(
                "UPDATE diagnostic_outbox SET state='READY', last_error_code=?, next_attempt_at=?, "
                "refusal_code=CASE WHEN ? THEN ? ELSE refusal_code END "
                "WHERE gateway_id=? AND sequence_epoch=? AND diagnostic_sequence=? AND state='IN_FLIGHT'",
                (code, next_attempt_at, 1 if refused else 0, code, *key),
            )

    def run_delivery(self, lab_run_ref: str) -> dict[str, object]:
        with self._tx() as db:
            return run_delivery_in(db, lab_run_ref)


# --- S2-02 phase 2: receipt verification and the run delivery read -------------


class ReceiptMismatch(RuntimeError):
    """A receipt that does not answer exactly this batch: a local integrity error.

    Never acknowledged; the batch stays retryable with unchanged bytes."""

    code = "RECEIPT_MISMATCH"

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"RECEIPT_MISMATCH: {detail}")


@dataclass(frozen=True)
class BatchExpectation:
    """What a receipt for this batch must say, from the gateway's own ledger."""

    batch_id: str
    site_id: str
    gateway_id: str
    source_id: str
    payload_sha256: str
    items: tuple[tuple[int, str], ...]


def verify_receipt(text: object, expected: BatchExpectation, *, complete: bool) -> IngestionReceiptV2:
    """Parse the exact received text and check it answers exactly `expected`.

    `complete=True` wants a COMPLETED receipt covering every ordinal (HTTP 200);
    `complete=False` wants an IN_PROGRESS prefix (HTTP 202). Either way the
    receipt's own hash, batch ID, payload digest, Site/gateway/source, total
    count and every listed ordinal's message ID must match the sealed batch."""
    try:
        receipt = parse_canonical_receipt_v2_text(text)
    except ReceiptRejected as error:
        raise ReceiptMismatch(f"unparseable receipt: {error.kind} at {error.field}") from error
    if receipt.batch_id != expected.batch_id:
        raise ReceiptMismatch("batch_id differs")
    if receipt.payload_sha256 != expected.payload_sha256:
        raise ReceiptMismatch("payload_sha256 differs from the sealed bytes")
    if (receipt.site_id, receipt.gateway_id, receipt.source_id) != (
        expected.site_id,
        expected.gateway_id,
        expected.source_id,
    ):
        raise ReceiptMismatch("site, gateway or source differs")
    if receipt.counts.total != len(expected.items):
        raise ReceiptMismatch("ordinal count differs from the sealed batch")
    if receipt.status != ("COMPLETED" if complete else "IN_PROGRESS"):
        raise ReceiptMismatch(f"status {receipt.status} does not fit the HTTP answer")
    if complete and len(receipt.dispositions) != len(expected.items):
        raise ReceiptMismatch("a completed receipt must decide every ordinal")
    for d in receipt.dispositions:
        if d.ordinal >= len(expected.items) or expected.items[d.ordinal] != (d.ordinal, d.message_id):
            raise ReceiptMismatch(f"ordinal {d.ordinal} names a different message")
    return receipt


def _run_batches(db: sqlite3.Connection, lab_run_ref: str) -> list[tuple[str, bool]]:
    """This run's batches (as `run_stage` scopes them), oldest first, each with
    whether it also carries an envelope this run did not hand the gateway."""
    return [
        (r[0], bool(r[1]))
        for r in db.execute(
            "SELECT b.batch_id, EXISTS (SELECT 1 FROM batch_item i WHERE i.batch_id=b.batch_id AND NOT EXISTS "
            "(SELECT 1 FROM lab_report_provenance q WHERE q.lab_run_ref=? AND q.message_id=i.message_id)) "
            "FROM upload_batch b WHERE b.batch_id IN (SELECT i.batch_id FROM batch_item i JOIN "
            "lab_report_provenance p ON p.message_id=i.message_id WHERE p.lab_run_ref=?) "
            "ORDER BY b.created_at, b.rowid",
            (lab_run_ref, lab_run_ref),
        )
    ]


def run_delivery_in(db: sqlite3.Connection, lab_run_ref: str) -> dict[str, object]:
    """One run's local delivery state, from the ledger alone.

    `gateway_complete` is the gateway's share of a "fully released" claim:
    Stage `STAGED` (every admitted envelope sealed, no active seal refusal),
    no batch shared with another run, and every batch of the run released and
    ACKED. The gateway cannot see the Lab's publication schedule, so
    `publication_gap` is `UNKNOWN_TO_GATEWAY` and the host combines it. Held
    reports are counted apart and never as accepted."""
    envelopes = db.execute(
        "SELECT o.source_id, o.sequence_epoch, o.snapshot_sha256, o.state, b.batch_id "
        "FROM lab_report_provenance p JOIN envelope_outbox o ON o.message_id=p.message_id "
        "LEFT JOIN batch_item b ON b.message_id=o.message_id WHERE p.lab_run_ref=?",
        (lab_run_ref,),
    ).fetchall()
    holds = db.execute(
        "SELECT COUNT(*) FROM lab_report_provenance WHERE lab_run_ref=? AND hold_id IS NOT NULL", (lab_run_ref,)
    ).fetchone()[0]
    unbatched = {(e[0], e[1], e[2], e[3]) for e in envelopes if e[4] is None}
    refused = any(
        db.execute(
            "SELECT 1 FROM seal_refusal WHERE source_id=? AND sequence_epoch=? AND snapshot_sha256=? "
            "AND outbox_state=?",
            group,
        ).fetchone()
        for group in unbatched
    )
    if unbatched:
        stage_status = "SEALING_REFUSED" if refused else "SEALING_PENDING"
    elif envelopes:
        stage_status = "STAGED"
    else:
        stage_status = "HELD" if holds else "NOT_STAGED"
    batches = _run_batches(db, lab_run_ref)
    by_state = {s: 0 for s in ("STAGED", "READY", "IN_FLIGHT", "ACKED", "REFUSED")}
    released = 0
    shared: list[str] = []
    last_error = None
    rows: list[dict[str, object]] = []
    for batch_id, foreign in batches:
        state, code, at, source_id = db.execute(
            "SELECT state, last_error_code, last_error_at, source_id FROM upload_batch WHERE batch_id=?",
            (batch_id,),
        ).fetchone()
        by_state[state] += 1
        if foreign:
            shared.append(batch_id)
        is_released = (
            db.execute(
                "SELECT 1 FROM release_manifest WHERE lab_run_ref=? AND batch_id=?", (lab_run_ref, batch_id)
            ).fetchone()
            is not None
        )
        if is_released:
            released += 1
        receipt = db.execute(
            "SELECT receipt_sha256, server_received_at, server_completed_at FROM batch_receipt WHERE batch_id=?",
            (batch_id,),
        ).fetchone()
        batch_decisions = {d: 0 for d in RECEIPT_DECISIONS}
        for decision, count in db.execute(
            "SELECT decision, COUNT(*) FROM acknowledgement WHERE batch_id=? GROUP BY decision", (batch_id,)
        ):
            batch_decisions[decision] = count
        # Per batch, for the Lab Commit view (S2-02 phase 3): its state, whether
        # this run released it, whether it is shared (never released under one
        # run's authority) and its verified receipt's server times, if any.
        rows.append(
            {
                "batch_id": batch_id,
                "source_id": source_id,
                "state": state,
                "released": is_released,
                "shared_with_another_run": foreign,
                "item_count": db.execute(
                    "SELECT COUNT(*) FROM batch_item WHERE batch_id=?", (batch_id,)
                ).fetchone()[0],
                "receipt": None
                if receipt is None
                else {
                    "receipt_sha256": receipt[0],
                    "server_received_at": receipt[1],
                    "server_completed_at": receipt[2],
                },
                "decisions": batch_decisions,
                "last_error_code": code if state != "ACKED" else None,
            }
        )
        if code is not None and state != "ACKED" and (last_error is None or at > last_error["at"]):
            last_error = {"batch_id": batch_id, "code": code, "at": at}
    decisions = {d: 0 for d in RECEIPT_DECISIONS}
    for decision, count in db.execute(
        "SELECT a.decision, COUNT(*) FROM acknowledgement a JOIN lab_report_provenance p "
        "ON p.message_id=a.message_id WHERE p.lab_run_ref=? GROUP BY a.decision",
        (lab_run_ref,),
    ):
        decisions[decision] = count
    refusals = [
        {"batch_id": r[0], "http_status": r[1], "code": r[2], "detail": r[3], "refused_at": r[4]}
        for r in db.execute(
            "SELECT f.batch_id, f.http_status, f.code, f.detail, f.refused_at FROM batch_refusal f "
            "WHERE f.batch_id IN (SELECT i.batch_id FROM batch_item i JOIN lab_report_provenance p "
            "ON p.message_id=i.message_id WHERE p.lab_run_ref=?) ORDER BY f.refused_at, f.batch_id",
            (lab_run_ref,),
        )
    ]
    total = len(batches)
    terminal = by_state["ACKED"] + by_state["REFUSED"]
    if released == 0:
        release_state = "NOT_RELEASED"
    elif terminal == 0:
        release_state = "PENDING"
    elif terminal < total or released < total:
        release_state = "PARTIAL"
    else:
        release_state = "TERMINAL"
    gateway_complete = (
        stage_status == "STAGED" and not shared and total > 0 and released == total and by_state["ACKED"] == total
    )
    return {
        "lab_run_ref": lab_run_ref,
        "stage_status": stage_status,
        "envelope_count": len(envelopes),
        "unbatched_envelope_count": sum(1 for e in envelopes if e[4] is None),
        "held_report_count": holds,
        "batch_count": total,
        "released_batch_count": released,
        "batches_by_state": by_state,
        "shared_batch_ids": shared,
        "batches": rows,
        "decisions": decisions,
        "refusals": refusals,
        "last_upload_error": last_error,
        "release_state": release_state,
        "publication_gap": "UNKNOWN_TO_GATEWAY",
        "gateway_complete": gateway_complete,
    }


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
    #: R1: the outbox state of the refused group (STAGED or READY).
    outbox_state: str


_DIAGNOSTIC_COLUMNS = (
    "gateway_id, sequence_epoch, diagnostic_sequence, observed_at, payload_text, sha256, state, last_attempt_at, "
    "last_error_code, refusal_code"
)


@dataclass(frozen=True)
class DiagnosticRow:
    """One stored GatewayDiagnosticsV1, exactly as allocated."""

    gateway_id: str
    sequence_epoch: str
    diagnostic_sequence: int
    observed_at: str
    payload_text: str
    sha256: str
    state: str
    last_attempt_at: str | None
    #: S2-02 Q21: the last failed upload's typed code (cleared on a receipt), and
    #: the server's refusal code when it refused the diagnostic (not retried).
    last_error_code: str | None = None
    refusal_code: str | None = None


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

    def run_delivery(self, lab_run_ref: str) -> dict[str, object]:
        db = self._db
        db.execute("BEGIN")
        try:
            return run_delivery_in(db, lab_run_ref)
        finally:
            db.execute("COMMIT")

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
                {(e.source_id, e.sequence_epoch, e.snapshot_sha256, e.state) for e in envelopes if e.batch_id is None}
            )
            refusals = []
            for group in unbatched:
                r = db.execute(
                    "SELECT source_id, sequence_epoch, snapshot_sha256, message_id, kind, field, detail, "
                    "last_seen_at, seen_count, outbox_state FROM seal_refusal "
                    "WHERE source_id=? AND sequence_epoch=? AND snapshot_sha256=? AND outbox_state=?",
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
