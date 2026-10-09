"""The gateway's SQLite acquisition ledger (technical design 2, S2-01b phase 1).

SQLite here is an acquisition ledger, not a product database. One process holds
the writer: `GatewayLedger.open_writer` takes an OS file lock beside the
database that the OS releases if the process dies, so a crashed gateway never
leaves a stale lock and two live writers cannot coexist. Readers open the file
read-only and never take the lock.

Every connection sets WAL, `foreign_keys=ON` and a busy timeout. The schema is
versioned in `schema_migration`. Sealed bytes are immutable at the database
boundary: triggers refuse any UPDATE of an envelope's or batch's text/hash and
any DELETE of an envelope, batch, batch item, mapping snapshot or mapping row.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

SCHEMA_VERSION = 5
BUSY_TIMEOUT_MS = 5000

OUTBOX_STATES = ("STAGED", "READY", "IN_FLIGHT", "ACKED", "DEAD_LETTER")
BATCH_STATES = ("STAGED", "READY", "IN_FLIGHT", "ACKED", "REFUSED")

_STATES = ",".join(f"'{s}'" for s in OUTBOX_STATES)
_BATCH_STATES = ",".join(f"'{s}'" for s in BATCH_STATES)

MIGRATION_1 = f"""
CREATE TABLE schema_migration (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);
CREATE TABLE gateway_identity (
  singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
  tenant_id TEXT NOT NULL,
  site_id TEXT NOT NULL,
  gateway_id TEXT NOT NULL,
  source_mode TEXT NOT NULL CHECK (source_mode IN ('SIMULATED','LIVE')),
  sequence_epoch TEXT NOT NULL,
  configured_at TEXT NOT NULL
);
CREATE TABLE permitted_source (
  source_id TEXT PRIMARY KEY
);
CREATE TABLE sequence_epoch_history (
  sequence_epoch TEXT PRIMARY KEY,
  provisioned_at TEXT NOT NULL
);
CREATE TABLE mapping_snapshot (
  snapshot_sha256 TEXT PRIMARY KEY,
  snapshot_text TEXT NOT NULL,
  schema TEXT NOT NULL,
  foundation_revision_id TEXT NOT NULL,
  foundation_version INTEGER NOT NULL,
  foundation_valid_from TEXT NOT NULL,
  foundation_valid_to TEXT,
  binding_set_id TEXT NOT NULL,
  binding_set_revision_id TEXT NOT NULL,
  binding_set_version INTEGER NOT NULL,
  binding_valid_from TEXT NOT NULL,
  binding_valid_to TEXT,
  activated_at TEXT NOT NULL,
  UNIQUE (foundation_revision_id, binding_set_revision_id)
);
CREATE TABLE device_signal_mapping (
  snapshot_sha256 TEXT NOT NULL REFERENCES mapping_snapshot(snapshot_sha256),
  device_id TEXT NOT NULL,
  signal_id TEXT NOT NULL,
  binding_revision_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  role TEXT NOT NULL,
  source_unit TEXT NOT NULL,
  canonical_unit TEXT NOT NULL,
  conversion_kind TEXT NOT NULL,
  enum_map_json TEXT NOT NULL,
  PRIMARY KEY (snapshot_sha256, device_id, signal_id)
);
CREATE TABLE active_mapping (
  singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
  snapshot_sha256 TEXT NOT NULL REFERENCES mapping_snapshot(snapshot_sha256),
  switched_at TEXT NOT NULL
);
CREATE TABLE sequence_state (
  gateway_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  sequence_epoch TEXT NOT NULL,
  -- The last allocated sequence, so the 64-bit maximum itself is storable.
  last_sequence INTEGER NOT NULL CHECK (last_sequence >= 1),
  updated_at TEXT NOT NULL,
  PRIMARY KEY (gateway_id, source_id, sequence_epoch)
);
CREATE TABLE envelope_outbox (
  message_id TEXT PRIMARY KEY,
  gateway_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  sequence_epoch TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  source_time TEXT NOT NULL,
  snapshot_sha256 TEXT NOT NULL REFERENCES mapping_snapshot(snapshot_sha256),
  envelope_text TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ({_STATES})),
  created_at TEXT NOT NULL,
  last_attempt_at TEXT,
  UNIQUE (gateway_id, source_id, sequence_epoch, sequence)
);
CREATE TABLE report_admission (
  gateway_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  report_key TEXT NOT NULL,
  report_sha256 TEXT NOT NULL,
  message_id TEXT NOT NULL UNIQUE REFERENCES envelope_outbox(message_id),
  PRIMARY KEY (gateway_id, source_id, report_key)
);
CREATE TABLE upload_batch (
  batch_id TEXT PRIMARY KEY,
  site_id TEXT NOT NULL,
  gateway_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  sequence_epoch TEXT NOT NULL,
  snapshot_sha256 TEXT NOT NULL REFERENCES mapping_snapshot(snapshot_sha256),
  foundation_version INTEGER NOT NULL,
  binding_set_id TEXT NOT NULL,
  binding_set_version INTEGER NOT NULL,
  payload_text TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ({_BATCH_STATES})),
  attempt_count INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  last_attempt_at TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE batch_item (
  batch_id TEXT NOT NULL REFERENCES upload_batch(batch_id),
  ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
  message_id TEXT NOT NULL UNIQUE REFERENCES envelope_outbox(message_id),
  PRIMARY KEY (batch_id, ordinal)
);
-- The receipt slot S2-02 fills. Nothing in S2-01b writes it.
CREATE TABLE acknowledgement (
  batch_id TEXT NOT NULL REFERENCES upload_batch(batch_id),
  ordinal INTEGER NOT NULL,
  message_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  server_evidence_id TEXT,
  server_rejection_id TEXT,
  received_at TEXT NOT NULL,
  receipt_sha256 TEXT NOT NULL,
  PRIMARY KEY (batch_id, ordinal)
);
CREATE TABLE mapping_hold (
  hold_id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_sha256 TEXT,
  device_id TEXT,
  signal_id TEXT,
  source_time TEXT,
  kind TEXT NOT NULL,
  field TEXT NOT NULL,
  detail TEXT NOT NULL,
  report_text TEXT NOT NULL,
  report_sha256 TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  seen_count INTEGER NOT NULL DEFAULT 1,
  UNIQUE (report_sha256, snapshot_sha256)
);
-- Local, private provenance: which Lab run handed which report. Never part of
-- an envelope or a batch.
CREATE TABLE lab_report_provenance (
  lab_run_ref TEXT NOT NULL,
  message_id TEXT REFERENCES envelope_outbox(message_id),
  hold_id INTEGER REFERENCES mapping_hold(hold_id),
  recorded_at TEXT NOT NULL,
  CHECK ((message_id IS NULL) <> (hold_id IS NULL))
);
CREATE UNIQUE INDEX lab_report_provenance_message ON lab_report_provenance(lab_run_ref, message_id) WHERE message_id IS NOT NULL;
CREATE UNIQUE INDEX lab_report_provenance_hold ON lab_report_provenance(lab_run_ref, hold_id) WHERE hold_id IS NOT NULL;

CREATE TRIGGER envelope_bytes_immutable BEFORE UPDATE OF envelope_text, sha256, message_id, sequence,
  sequence_epoch, source_id, gateway_id, snapshot_sha256 ON envelope_outbox
BEGIN SELECT RAISE(ABORT, 'sealed envelope bytes are immutable'); END;
CREATE TRIGGER envelope_never_deleted BEFORE DELETE ON envelope_outbox
BEGIN SELECT RAISE(ABORT, 'envelopes are retained'); END;
CREATE TRIGGER batch_bytes_immutable BEFORE UPDATE OF payload_text, sha256, batch_id, source_id,
  snapshot_sha256 ON upload_batch
BEGIN SELECT RAISE(ABORT, 'sealed batch bytes are immutable'); END;
CREATE TRIGGER batch_never_deleted BEFORE DELETE ON upload_batch
BEGIN SELECT RAISE(ABORT, 'batches are retained'); END;
CREATE TRIGGER batch_item_immutable BEFORE UPDATE ON batch_item
BEGIN SELECT RAISE(ABORT, 'batch items are immutable'); END;
CREATE TRIGGER batch_item_never_deleted BEFORE DELETE ON batch_item
BEGIN SELECT RAISE(ABORT, 'batch items are retained'); END;
CREATE TRIGGER snapshot_immutable BEFORE UPDATE ON mapping_snapshot
BEGIN SELECT RAISE(ABORT, 'mapping snapshots are immutable'); END;
CREATE TRIGGER snapshot_never_deleted BEFORE DELETE ON mapping_snapshot
BEGIN SELECT RAISE(ABORT, 'mapping snapshots are retained'); END;
CREATE TRIGGER mapping_row_immutable BEFORE UPDATE ON device_signal_mapping
BEGIN SELECT RAISE(ABORT, 'mapping rows are immutable'); END;
CREATE TRIGGER mapping_row_never_deleted BEFORE DELETE ON device_signal_mapping
BEGIN SELECT RAISE(ABORT, 'mapping rows are retained'); END;
"""

# S2-01b fix round 1 (F1): a sealing refusal is durable, so a read after a
# restart says the group is unsealed and why, instead of a lost session note.
# One row per stuck (source, epoch, snapshot) group, naming the first envelope
# that could not be sealed; sealing that group later deletes the row.
MIGRATION_2 = """
CREATE TABLE seal_refusal (
  source_id TEXT NOT NULL,
  sequence_epoch TEXT NOT NULL,
  snapshot_sha256 TEXT NOT NULL,
  message_id TEXT NOT NULL REFERENCES envelope_outbox(message_id),
  kind TEXT NOT NULL,
  field TEXT NOT NULL,
  detail TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  seen_count INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (source_id, sequence_epoch, snapshot_sha256)
);
"""

# S2-01c phase 1.
#
# R1: a sealing group is (source, epoch, snapshot, outbox state), so the
# durable refusal is keyed by all four. A version-2 row takes the state of the
# envelope it names: that envelope is unbatched, and an unbatched envelope's
# state never changes (only batch moves change states), so it is exactly the
# state of the group that was refused.
#
# Diagnostics: the frozen emission configuration, the GatewayDiagnosticsV1
# outbox and local health observations (last simulated source contact, clock
# offset, injected disk pressure), each with its provenance. Nothing here is a
# receipt: `server_received_at` stays NULL until S2-02 stores a central row,
# and no state other than READY is written locally.
MIGRATION_3 = """
CREATE TABLE seal_refusal_v3 (
  source_id TEXT NOT NULL,
  sequence_epoch TEXT NOT NULL,
  snapshot_sha256 TEXT NOT NULL,
  outbox_state TEXT NOT NULL CHECK (outbox_state IN ('STAGED','READY')),
  message_id TEXT NOT NULL REFERENCES envelope_outbox(message_id),
  kind TEXT NOT NULL,
  field TEXT NOT NULL,
  detail TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  seen_count INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (source_id, sequence_epoch, snapshot_sha256, outbox_state)
);
INSERT INTO seal_refusal_v3 (source_id, sequence_epoch, snapshot_sha256, outbox_state, message_id, kind, field,
  detail, first_seen_at, last_seen_at, seen_count)
SELECT r.source_id, r.sequence_epoch, r.snapshot_sha256, o.state, r.message_id, r.kind, r.field, r.detail,
  r.first_seen_at, r.last_seen_at, r.seen_count
FROM seal_refusal r JOIN envelope_outbox o ON o.message_id = r.message_id
WHERE o.state IN ('STAGED','READY');
DROP TABLE seal_refusal;
ALTER TABLE seal_refusal_v3 RENAME TO seal_refusal;
CREATE TABLE diagnostic_config (
  singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
  config_text TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  configured_at TEXT NOT NULL
);
CREATE TABLE diagnostic_outbox (
  gateway_id TEXT NOT NULL,
  sequence_epoch TEXT NOT NULL,
  diagnostic_sequence INTEGER NOT NULL CHECK (diagnostic_sequence >= 1),
  cadence_slot INTEGER NOT NULL,
  payload_text TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('READY','IN_FLIGHT','ACKED')),
  observed_at TEXT NOT NULL,
  last_attempt_at TEXT,
  server_received_at TEXT,
  PRIMARY KEY (gateway_id, sequence_epoch, diagnostic_sequence),
  UNIQUE (gateway_id, sequence_epoch, cadence_slot)
);
CREATE TABLE health_observation (
  name TEXT PRIMARY KEY,
  value_text TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  provenance TEXT NOT NULL CHECK (provenance IN ('OBSERVED_SIMULATED_REPORT','OBSERVED_DEVICE_REPORT','MEASURED','INJECTED_FAULT_FIXTURE'))
);
CREATE TRIGGER diagnostic_bytes_immutable BEFORE UPDATE OF payload_text, sha256, gateway_id, sequence_epoch,
  diagnostic_sequence, cadence_slot, observed_at ON diagnostic_outbox
BEGIN SELECT RAISE(ABORT, 'diagnostic bytes are immutable'); END;
CREATE TRIGGER diagnostic_never_deleted BEFORE DELETE ON diagnostic_outbox
BEGIN SELECT RAISE(ABORT, 'diagnostics are retained'); END;
CREATE TRIGGER diagnostic_config_immutable BEFORE UPDATE ON diagnostic_config
BEGIN SELECT RAISE(ABORT, 'the diagnostic configuration is frozen'); END;
CREATE TRIGGER diagnostic_config_never_deleted BEFORE DELETE ON diagnostic_config
BEGIN SELECT RAISE(ABORT, 'the diagnostic configuration is retained'); END;
"""

#: S2-01c phase 2 (`D-2026-10-09-s2-simulated-publication-clock`): one virtual
#: publication clock per registered Lab run, owned and persisted here. It only
#: moves forward; V3 `published_at` for that run's admissions is read from it,
#: while every operational time (outbox creation, contact, diagnostics) stays
#: on the gateway's real UTC clock.
MIGRATION_4 = """
CREATE TABLE publication_clock (
  lab_run_ref TEXT PRIMARY KEY,
  instant TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TRIGGER publication_clock_forward_only BEFORE UPDATE OF instant ON publication_clock
WHEN NEW.instant < OLD.instant
BEGIN SELECT RAISE(ABORT, 'a publication clock never moves backward'); END;
CREATE TRIGGER publication_clock_never_deleted BEFORE DELETE ON publication_clock
BEGIN SELECT RAISE(ABORT, 'publication clocks are retained'); END;
"""

#: S2-02 phase 2 (`D-2026-10-09-s2-gateway-sealing-state-and-partial-progress`,
#: `D-2026-10-09-s2-pilot-gateway-upload-credential`): delivery through the
#: authenticated HTTPS route.
#:
#: - `release_manifest` is the private Lab Commit record linking one run to the
#:   existing sealed batch IDs it authorized (`STAGED -> READY`). Append-only.
#: - `batch_receipt` holds the whole verified Receipt V2 text of a COMPLETED
#:   batch; `acknowledgement` (migration 1) holds its per-ordinal decisions.
#:   Both are written in the same transaction that moves the batch to ACKED and
#:   are immutable afterwards.
#: - `batch_refusal` is an authenticated terminal whole-batch refusal (HTTP
#:   409/413/422): the batch is REFUSED and its envelopes DEAD_LETTER.
#: - `last_error_code` columns record the latest retryable failure (transport,
#:   credential, receipt mismatch). They are codes only: the upload secret is
#:   never stored in this ledger.
#: - A diagnostic `refusal_code` (HTTP 409/422) is terminal for that row: it
#:   stays not-ACKED and is not retried.
#: ACKED and REFUSED batches, and ACKED/DEAD_LETTER envelopes, never move again.
MIGRATION_5 = """
CREATE TABLE release_manifest (
  lab_run_ref TEXT NOT NULL,
  batch_id TEXT NOT NULL REFERENCES upload_batch(batch_id),
  released_at TEXT NOT NULL,
  PRIMARY KEY (lab_run_ref, batch_id)
);
CREATE TRIGGER release_manifest_immutable BEFORE UPDATE ON release_manifest
BEGIN SELECT RAISE(ABORT, 'the release manifest is append-only'); END;
CREATE TRIGGER release_manifest_never_deleted BEFORE DELETE ON release_manifest
BEGIN SELECT RAISE(ABORT, 'the release manifest is append-only'); END;
CREATE TABLE batch_receipt (
  batch_id TEXT PRIMARY KEY REFERENCES upload_batch(batch_id),
  receipt_text TEXT NOT NULL,
  receipt_sha256 TEXT NOT NULL,
  server_received_at TEXT NOT NULL,
  server_completed_at TEXT NOT NULL,
  stored_at TEXT NOT NULL
);
CREATE TRIGGER batch_receipt_immutable BEFORE UPDATE ON batch_receipt
BEGIN SELECT RAISE(ABORT, 'a verified receipt is immutable'); END;
CREATE TRIGGER batch_receipt_never_deleted BEFORE DELETE ON batch_receipt
BEGIN SELECT RAISE(ABORT, 'receipts are retained'); END;
CREATE TRIGGER acknowledgement_immutable BEFORE UPDATE ON acknowledgement
BEGIN SELECT RAISE(ABORT, 'acknowledgements are immutable'); END;
CREATE TRIGGER acknowledgement_never_deleted BEFORE DELETE ON acknowledgement
BEGIN SELECT RAISE(ABORT, 'acknowledgements are retained'); END;
CREATE TABLE batch_refusal (
  batch_id TEXT PRIMARY KEY REFERENCES upload_batch(batch_id),
  http_status INTEGER NOT NULL,
  code TEXT NOT NULL,
  detail TEXT NOT NULL,
  refused_at TEXT NOT NULL
);
CREATE TRIGGER batch_refusal_immutable BEFORE UPDATE ON batch_refusal
BEGIN SELECT RAISE(ABORT, 'a batch refusal is immutable'); END;
CREATE TRIGGER batch_refusal_never_deleted BEFORE DELETE ON batch_refusal
BEGIN SELECT RAISE(ABORT, 'batch refusals are retained'); END;
ALTER TABLE upload_batch ADD COLUMN last_error_code TEXT;
ALTER TABLE upload_batch ADD COLUMN last_error_at TEXT;
CREATE TRIGGER batch_terminal_state BEFORE UPDATE OF state ON upload_batch
WHEN OLD.state IN ('ACKED','REFUSED') AND NEW.state <> OLD.state
BEGIN SELECT RAISE(ABORT, 'a terminal batch never moves'); END;
CREATE TRIGGER envelope_terminal_state BEFORE UPDATE OF state ON envelope_outbox
WHEN OLD.state IN ('ACKED','DEAD_LETTER') AND NEW.state <> OLD.state
BEGIN SELECT RAISE(ABORT, 'a terminal envelope never moves'); END;
ALTER TABLE diagnostic_outbox ADD COLUMN next_attempt_at TEXT;
ALTER TABLE diagnostic_outbox ADD COLUMN last_error_code TEXT;
ALTER TABLE diagnostic_outbox ADD COLUMN refusal_code TEXT;
CREATE TRIGGER diagnostic_terminal_state BEFORE UPDATE OF state ON diagnostic_outbox
WHEN OLD.state = 'ACKED' AND NEW.state <> OLD.state
BEGIN SELECT RAISE(ABORT, 'an acknowledged diagnostic never moves'); END;
"""

MIGRATIONS = {1: MIGRATION_1, 2: MIGRATION_2, 3: MIGRATION_3, 4: MIGRATION_4, 5: MIGRATION_5}


class WriterBusy(RuntimeError):
    """Another live process holds this ledger's single writer."""


class _WriterLock:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o600)
        try:
            if sys.platform == "win32":
                import msvcrt

                os.lseek(self._fd, 0, os.SEEK_SET)
                msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            os.close(self._fd)
            raise WriterBusy(f"{path} is held by another gateway writer") from error

    def release(self) -> None:
        if self._fd is None:
            return
        try:
            if sys.platform == "win32":
                import msvcrt

                os.lseek(self._fd, 0, os.SEEK_SET)
                msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fd, fcntl.LOCK_UN)
        finally:
            os.close(self._fd)
            self._fd = None  # type: ignore[assignment]


def _configure(connection: sqlite3.Connection) -> None:
    connection.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA foreign_keys = ON")


def open_writer_connection(path: Path) -> tuple[sqlite3.Connection, _WriterLock]:
    """The single writer: lock, connect, WAL, migrate."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = _WriterLock(path.with_name(path.name + ".writer.lock"))
    try:
        connection = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False)
        _configure(connection)
        mode = connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]
        if str(mode).lower() != "wal":
            raise RuntimeError(f"WAL is required, SQLite reported {mode!r}")
        connection.execute("PRAGMA synchronous = FULL")
        _migrate(connection)
    except BaseException:
        lock.release()
        raise
    return connection, lock


def open_reader_connection(path: Path) -> sqlite3.Connection:
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, isolation_level=None, check_same_thread=False)
    _configure(connection)
    return connection


def _migrate(connection: sqlite3.Connection) -> None:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migration'"
    ).fetchone()
    current = 0
    if exists:
        current = connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] or 0
    if current > SCHEMA_VERSION:
        raise RuntimeError(f"ledger schema {current} is newer than this gateway ({SCHEMA_VERSION})")
    for version in range(current + 1, SCHEMA_VERSION + 1):
        connection.execute("BEGIN IMMEDIATE")
        try:
            for statement in _statements(MIGRATIONS[version]):
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migration(version, applied_at) "
                "VALUES (?, strftime('%Y-%m-%dT%H:%M:%SZ','now'))",
                (version,),
            )
            connection.execute("COMMIT")
        except BaseException:
            connection.execute("ROLLBACK")
            raise


def _statements(script: str) -> list[str]:
    """Split the migration on statement ends, keeping trigger bodies whole."""
    statements: list[str] = []
    buffer = ""
    for line in script.splitlines():
        if line.strip().startswith("--"):
            continue
        buffer += line + "\n"
        if sqlite3.complete_statement(buffer):
            statements.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        raise RuntimeError("incomplete statement in migration")
    return statements
