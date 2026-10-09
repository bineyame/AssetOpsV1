"""The durable ledger: identity, holds, sealing, immutability and restart."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from assetops_contracts.ingestion_batch_v2 import MAX_BATCH_BYTES, parse_canonical_batch_v2_text
from assetops_contracts.source_envelope_v3 import MAX_SEQUENCE, parse_canonical_envelope_v3_text, v3_message_id
from assetops_gateway.ledger import SCHEMA_VERSION, WriterBusy
from assetops_gateway.service import GatewayReader, GatewayRefused, GatewayService
from assetops_gateway.snapshot import ClaimedReferences, SnapshotRefused
from conftest import EPOCH, GATEWAY, PROVISIONING, SITE, SRC_BMS, SRC_PV, report, snapshot


def _count(db_path: Path, sql: str) -> int:
    with sqlite3.connect(db_path) as db:
        return db.execute(sql).fetchone()[0]


def _envelopes(db_path: Path) -> list[tuple]:
    with sqlite3.connect(db_path) as db:
        return db.execute(
            "SELECT message_id, source_id, sequence_epoch, sequence, envelope_text, sha256, state "
            "FROM envelope_outbox ORDER BY source_id, sequence"
        ).fetchall()


# --- database setup -------------------------------------------------------------


def test_ledger_uses_wal_foreign_keys_and_a_migration_version(gateway, db_path: Path) -> None:
    db = gateway._db
    assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert db.execute("PRAGMA busy_timeout").fetchone()[0] > 0
    assert db.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0] == SCHEMA_VERSION


def test_one_writer_at_a_time(gateway, db_path: Path) -> None:
    with pytest.raises(WriterBusy):
        GatewayService(db_path)


# --- identity -------------------------------------------------------------------


def test_admission_allocates_a_monotonic_sequence_per_source(gateway, active: str, db_path: Path) -> None:
    a = gateway.admit(report(at="2026-10-01T08:00:00Z"), snapshot_sha256=active)
    b = gateway.admit(report(at="2026-10-01T08:15:00Z"), snapshot_sha256=active)
    c = gateway.admit(
        report(device="pv-inverter", signal="ac_power", unit="kW", value="3.5"), snapshot_sha256=active
    )
    assert (a.outcome, a.sequence, b.sequence, c.sequence) == ("ADMITTED", 1, 2, 1)
    assert a.message_id == v3_message_id(
        site_id=SITE, gateway_id=GATEWAY, source_id=SRC_BMS, sequence_epoch=EPOCH, sequence=1
    )
    text = _envelopes(db_path)[0][4]
    envelope = parse_canonical_envelope_v3_text(text)
    assert (envelope.published_at, envelope.source_time) == ("2026-10-08T12:00:00Z", "2026-10-01T08:00:00Z")


def test_replayed_report_reuses_identity_and_bytes(gateway, active: str, db_path: Path, clock) -> None:
    first = gateway.admit(report(key="obs-1"), snapshot_sha256=active)
    before = _envelopes(db_path)
    clock.now = clock.now.replace(hour=13)
    again = gateway.admit(report(key="obs-1"), snapshot_sha256=active)
    assert again.outcome == "ALREADY_ADMITTED"
    assert (again.message_id, again.sequence) == (first.message_id, first.sequence)
    assert _envelopes(db_path) == before
    assert _count(db_path, "SELECT last_sequence FROM sequence_state") == 1


def test_two_reports_at_one_source_time_are_two_events(gateway, active: str) -> None:
    a = gateway.admit(report(key="obs-1"), snapshot_sha256=active)
    b = gateway.admit(report(key="obs-2"), snapshot_sha256=active)
    unkeyed = gateway.admit(report(), snapshot_sha256=active)
    assert len({a.message_id, b.message_id, unkeyed.message_id}) == 3
    assert [a.sequence, b.sequence, unkeyed.sequence] == [1, 2, 3]


def test_same_key_different_content_is_held(gateway, active: str, db_path: Path) -> None:
    gateway.admit(report(key="obs-1", value="61.5"), snapshot_sha256=active)
    conflict = gateway.admit(report(key="obs-1", value="70"), snapshot_sha256=active)
    assert (conflict.outcome, conflict.kind, conflict.field) == ("HELD", "CONFLICTING_REPORT", "report_key")
    assert _count(db_path, "SELECT COUNT(*) FROM envelope_outbox") == 1


def test_sequence_overflow_refuses_acquisition(gateway, active: str, db_path: Path) -> None:
    gateway.admit(report(), snapshot_sha256=active)
    gateway._db.execute("UPDATE sequence_state SET last_sequence=?", (MAX_SEQUENCE - 1,))
    last = gateway.admit(report(at="2026-10-01T08:30:00Z"), snapshot_sha256=active)
    assert (last.outcome, last.sequence) == ("ADMITTED", MAX_SEQUENCE)
    held = gateway.admit(report(at="2026-10-01T09:00:00Z"), snapshot_sha256=active)
    assert (held.outcome, held.kind) == ("HELD", "SEQUENCE_EXHAUSTED")
    assert _count(db_path, "SELECT COUNT(*) FROM envelope_outbox") == 2


def test_epoch_changes_only_by_explicit_reprovisioning(gateway, active: str) -> None:
    assert gateway.admit(report(), snapshot_sha256=active).sequence == 1
    gateway.reprovision_epoch("epoch-2")
    second = gateway.admit(report(at="2026-10-01T09:00:00Z"), snapshot_sha256=active)
    assert second.sequence == 1
    assert second.message_id == v3_message_id(
        site_id=SITE, gateway_id=GATEWAY, source_id=SRC_BMS, sequence_epoch="epoch-2", sequence=1
    )
    with pytest.raises(GatewayRefused):
        gateway.reprovision_epoch(EPOCH)


def test_identity_is_fixed_once_provisioned(gateway) -> None:
    gateway.provision(PROVISIONING, sequence_epoch=EPOCH)  # identical: no-op
    with pytest.raises(GatewayRefused):
        gateway.provision(
            type(PROVISIONING)(**{**PROVISIONING.__dict__, "site_id": "99999999-9999-4999-8999-999999999999"}),
            sequence_epoch=EPOCH,
        )


# --- holds ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "kind", "field"),
    [
        (dict(device="unknown-meter", signal="kwh"), "UNKNOWN_CHANNEL", "device_id/signal_id"),
        (dict(unit="kW"), "UNIT_INCOMPATIBLE", "unit"),
        (dict(device="generator-controller", signal="status", unit="state", value="IDLE"), "INVALID_ENUM", "value"),
        (dict(value="sixty"), "INVALID_VALUE", "value"),
        (dict(at="2026-09-29T11:00:00Z"), "OUTSIDE_VALIDITY", "source_time"),
        (dict(at="2026-10-09T00:00:00Z"), "SOURCE_TIME_IN_FUTURE", "source_time"),
        (dict(quality="UNAVAILABLE", value="1", reason="NO_MEASUREMENT"), "INVALID_PAYLOAD", "payload.value"),
    ],
)
def test_refused_reports_are_inspectable_holds_without_a_sequence(
    gateway, active: str, db_path: Path, kwargs: dict, kind: str, field: str
) -> None:
    held = gateway.admit(report(**kwargs), snapshot_sha256=active, lab_run_ref="run-1")
    assert (held.outcome, held.kind, held.field) == ("HELD", kind, field)
    assert held.detail
    assert _count(db_path, "SELECT COUNT(*) FROM envelope_outbox") == 0
    assert _count(db_path, "SELECT COUNT(*) FROM sequence_state") == 0
    with GatewayReader(db_path) as reader:
        stage = reader.run_stage("run-1")
    assert [(h.kind, h.field) for h in stage.holds] == [(kind, field)]


def test_a_malformed_or_private_report_is_held_not_read(gateway, active: str, db_path: Path) -> None:
    document = json.loads(report())
    document["cause"] = "fuel theft"
    held = gateway.admit(json.dumps(document, sort_keys=True), snapshot_sha256=active)
    assert held.kind == "INVALID_REPORT" and held.field == "cause"
    assert _count(db_path, "SELECT COUNT(*) FROM envelope_outbox") == 0


def test_no_activated_snapshot_is_a_hold(gateway, db_path: Path) -> None:
    held = gateway.admit(report(), snapshot_sha256="c" * 64)
    assert held.kind == "NO_ACTIVE_MAPPING"


def test_repeated_hold_is_one_row(gateway, active: str, db_path: Path) -> None:
    for _ in range(3):
        gateway.admit(report(unit="kW"), snapshot_sha256=active)
    assert _count(db_path, "SELECT seen_count FROM mapping_hold") == 3
    assert _count(db_path, "SELECT COUNT(*) FROM mapping_hold") == 1


def test_unavailable_and_enum_readings_are_published(gateway, active: str, db_path: Path) -> None:
    unavailable = gateway.admit(
        report(quality="UNAVAILABLE", value=None, reason="NO_MEASUREMENT"), snapshot_sha256=active
    )
    running = gateway.admit(
        report(device="generator-controller", signal="status", unit="state", value="RUNNING"),
        snapshot_sha256=active,
    )
    assert (unavailable.outcome, running.outcome) == ("ADMITTED", "ADMITTED")


# --- activation -------------------------------------------------------------------


def _claimed(claimed: ClaimedReferences, **changes) -> ClaimedReferences:
    return ClaimedReferences(**{**claimed.__dict__, **changes})


@pytest.mark.parametrize(
    ("build", "kind"),
    [
        (lambda: (lambda t, c: (t.replace("KOBO", "KOBX"), c))(*snapshot()), "HASH_MISMATCH"),
        (lambda: snapshot(site="99999999-9999-4999-8999-999999999999"), "OUT_OF_SCOPE"),
        (lambda: snapshot(tenant="99999999-9999-4999-8999-999999999999"), "OUT_OF_SCOPE"),
        (lambda: snapshot(mode="LIVE"), "OUT_OF_SCOPE"),
        (lambda: (lambda t, c: (t, _claimed(c, foundation_version=4)))(*snapshot()), "REFERENCE_MISMATCH"),
        (lambda: (lambda t, c: (t, _claimed(c, binding_set_revision_id="other")))(*snapshot()), "REFERENCE_MISMATCH"),
    ],
)
def test_activation_refusals(gateway, build, kind: str) -> None:
    text, claimed = build()
    with pytest.raises(SnapshotRefused) as caught:
        gateway.activate(text, claimed)
    assert caught.value.kind == kind


def _rehash(text: str) -> tuple[str, ClaimedReferences]:
    _, claimed = snapshot()
    import hashlib

    return text, _claimed(claimed, snapshot_sha256=hashlib.sha256(text.encode()).hexdigest())


def test_activation_refuses_schema_canonicality_scope_and_row_tampering(gateway) -> None:
    text, _ = snapshot()
    document = json.loads(text)
    cases = []
    unsupported = dict(document, schema="assetops.acquisition-snapshot/2")
    cases.append((json.dumps(unsupported, sort_keys=True, separators=(",", ":")), "SCHEMA_UNSUPPORTED"))
    cases.append((json.dumps(document, sort_keys=True), "NOT_CANONICAL"))
    tampered = json.loads(text)
    tampered["bindings"][0]["source_unit"] = "kW"
    tampered["bindings"][0]["canonical_unit"] = "kW"
    cases.append((json.dumps(tampered, sort_keys=True, separators=(",", ":")), "INCONSISTENT_SNAPSHOT"))
    foreign = json.loads(text)
    foreign["sources"][0]["source_id"] = "44444444-4444-4444-8444-444444444444"
    foreign["bindings"][0]["source_id"] = "44444444-4444-4444-8444-444444444444"
    cases.append((json.dumps(foreign, sort_keys=True, separators=(",", ":")), "OUT_OF_SCOPE"))
    for body, kind in cases:
        with pytest.raises(SnapshotRefused) as caught:
            gateway.activate(*_rehash(body))
        assert caught.value.kind == kind, body[:80]


def test_activation_is_idempotent_and_revisions_cannot_rebind(gateway, db_path: Path) -> None:
    text, claimed = snapshot()
    gateway.activate(text, claimed)
    gateway.activate(text, claimed)
    assert _count(db_path, "SELECT COUNT(*) FROM mapping_snapshot") == 1
    other, other_claimed = snapshot(valid_from="2026-09-30T00:00:00Z")
    with pytest.raises(SnapshotRefused) as caught:
        gateway.activate(other, other_claimed)
    assert caught.value.kind == "REFERENCE_MISMATCH"


# --- sealing -------------------------------------------------------------------------


def _publish_series(gateway: GatewayService, sha: str, run: str = "run-1") -> None:
    for minute in ("00", "15", "30"):
        at = f"2026-10-01T08:{minute}:00Z"
        gateway.admit(report(at=at, key=f"{run}-bms-{minute}"), snapshot_sha256=sha, lab_run_ref=run)
        gateway.admit(
            report(device="pv-inverter", signal="ac_power", unit="kW", value="3.5", at=at, key=f"{run}-pv-{minute}"),
            snapshot_sha256=sha,
            lab_run_ref=run,
        )


def test_sealing_splits_by_source_with_ordered_items(gateway, active: str, db_path: Path) -> None:
    _publish_series(gateway, active)
    batch_ids = gateway.seal()
    assert len(batch_ids) == 2
    with GatewayReader(db_path) as reader:
        stage = reader.run_stage("run-1")
    assert {b.source_id for b in stage.batches} == {SRC_BMS, SRC_PV}
    for batch in stage.batches:
        parsed = parse_canonical_batch_v2_text(batch.payload_text)
        assert parsed.payload_sha256 == batch.sha256
        assert parsed.source_mode == "SIMULATED"
        assert [parse_canonical_envelope_v3_text(t).message_id for t in parsed.envelopes] == list(batch.message_ids)
        assert batch.state == "STAGED"
        assert "run-1" not in batch.payload_text
    assert stage.queue_depth_by_state == {"STAGED": 6}
    assert gateway.seal() == []  # nothing left unsealed; sealed bytes never rewritten


def test_replaying_the_whole_series_changes_nothing(gateway, active: str, db_path: Path, clock) -> None:
    _publish_series(gateway, active)
    gateway.seal()
    with GatewayReader(db_path) as reader:
        before = reader.run_stage("run-1")
    clock.now = clock.now.replace(hour=14)
    _publish_series(gateway, active)
    assert gateway.seal() == []
    with GatewayReader(db_path) as reader:
        after = reader.run_stage("run-1")
    assert after == before


def test_batch_bound_splits_a_source(gateway, active: str) -> None:
    _publish_series(gateway, active)
    assert len(gateway.seal(max_envelopes=2)) == 4


def test_a_new_basis_opens_new_batches_and_leaves_old_ones(gateway, active: str, db_path: Path) -> None:
    _publish_series(gateway, active)
    old = gateway.seal()
    with sqlite3.connect(db_path) as db:
        old_bytes = db.execute("SELECT batch_id, payload_text, sha256 FROM upload_batch ORDER BY batch_id").fetchall()
    later, later_claimed = snapshot(foundation_rev="f-rev-2", foundation_version=4, binding_rev="bs-rev-2", binding_version=3)
    gateway.activate(later, later_claimed)
    gateway.admit(report(at="2026-10-01T09:00:00Z", key="later-1"), snapshot_sha256=later_claimed.snapshot_sha256)
    new = gateway.seal()
    assert len(new) == 1 and not set(new) & set(old)
    with sqlite3.connect(db_path) as db:
        assert db.execute(
            "SELECT batch_id, payload_text, sha256 FROM upload_batch WHERE batch_id IN (%s) ORDER BY batch_id"
            % ",".join("?" * len(old)),
            old,
        ).fetchall() == old_bytes
        version = db.execute("SELECT binding_set_version FROM upload_batch WHERE batch_id=?", new).fetchone()[0]
    assert version == 3


def test_sealed_bytes_are_immutable_at_the_database(gateway, active: str, db_path: Path) -> None:
    _publish_series(gateway, active)
    gateway.seal()
    with sqlite3.connect(db_path) as db:
        for statement in (
            "UPDATE envelope_outbox SET envelope_text='x'",
            "UPDATE upload_batch SET payload_text='x'",
            "DELETE FROM envelope_outbox",
            "DELETE FROM upload_batch",
            "UPDATE batch_item SET ordinal=ordinal+10",
            "UPDATE mapping_snapshot SET snapshot_text='x'",
        ):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(statement)


def test_local_delivery_states_and_restart_retry_identical_bytes(clock, db_path: Path) -> None:
    service = GatewayService(db_path, clock=clock)
    service.provision(PROVISIONING, sequence_epoch=EPOCH)
    text, claimed = snapshot()
    service.activate(text, claimed)
    _publish_series(service, claimed.snapshot_sha256)
    batch_id = service.seal()[0]
    with pytest.raises(GatewayRefused):
        service.begin_attempt(batch_id)  # a Lab batch is STAGED: no upload before S2-02
    service.mark_ready(batch_id)
    sent = service.begin_attempt(batch_id)
    service.close()  # the process dies mid-attempt

    restarted = GatewayService(db_path, clock=clock)
    try:
        with sqlite3.connect(db_path) as db:
            state, attempts, payload = db.execute(
                "SELECT state, attempt_count, payload_text FROM upload_batch WHERE batch_id=?", (batch_id,)
            ).fetchone()
            assert _count(db_path, "SELECT COUNT(*) FROM acknowledgement") == 0
        assert (state, attempts, payload) == ("READY", 1, sent)
        assert restarted.begin_attempt(batch_id) == sent
    finally:
        restarted.close()


# --- crash windows (a real process killed between steps) ---------------------------------

_CRASH = textwrap.dedent(
    """
    import os, sys
    from datetime import datetime, timezone
    sys.path.insert(0, {tests!r})
    from conftest import PROVISIONING, EPOCH, snapshot, report
    from assetops_gateway.service import GatewayService

    point = sys.argv[1]
    def fault(at):
        if at == point:
            os._exit(17)
    service = GatewayService({db!r}, clock=lambda: datetime(2026, 10, 8, 12, tzinfo=timezone.utc), fault=fault)
    service.provision(PROVISIONING, sequence_epoch=EPOCH)
    text, claimed = snapshot()
    service.activate(text, claimed)
    for i, minute in enumerate(("00", "15")):
        service.admit(report(at=f"2026-10-01T08:{{minute}}:00Z", key=f"k-{{minute}}"),
                      snapshot_sha256=claimed.snapshot_sha256, lab_run_ref="run-1")
    service.seal()
    os._exit(0)
    """
)


def _crash(db_path: Path, point: str) -> int:
    script = _CRASH.format(tests=str(Path(__file__).parent), db=str(db_path))
    return subprocess.run([sys.executable, "-c", script, point], timeout=60).returncode


def test_kill_inside_the_enqueue_transaction_allocates_nothing(db_path: Path, clock) -> None:
    assert _crash(db_path, "after_sequence_read") == 17
    assert _count(db_path, "SELECT COUNT(*) FROM envelope_outbox") == 0
    assert _count(db_path, "SELECT COUNT(*) FROM sequence_state") == 0


def test_kill_after_enqueue_then_restart_keeps_identity(db_path: Path, clock) -> None:
    assert _crash(db_path, "after_enqueue_commit") == 17
    before = _envelopes(db_path)
    assert [row[3] for row in before] == [1]
    with GatewayService(db_path, clock=clock) as service:
        sha = snapshot()[1].snapshot_sha256
        again = service.admit(report(at="2026-10-01T08:00:00Z", key="k-00"), snapshot_sha256=sha, lab_run_ref="run-1")
        nxt = service.admit(report(at="2026-10-01T08:15:00Z", key="k-15"), snapshot_sha256=sha, lab_run_ref="run-1")
        assert (again.outcome, again.message_id) == ("ALREADY_ADMITTED", before[0][0])
        assert nxt.sequence == 2
    assert _envelopes(db_path)[0] == before[0]


def test_kill_after_sealing_then_restart_keeps_batch_bytes(db_path: Path, clock) -> None:
    assert _crash(db_path, "after_seal_commit") == 17
    with sqlite3.connect(db_path) as db:
        before = db.execute("SELECT batch_id, payload_text, sha256, state FROM upload_batch").fetchall()
        items = db.execute("SELECT batch_id, ordinal, message_id FROM batch_item ORDER BY ordinal").fetchall()
    assert len(before) == 1 and before[0][3] == "STAGED" and [i[1] for i in items] == [0, 1]
    with GatewayService(db_path, clock=clock) as service:
        assert service.seal() == []
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT batch_id, payload_text, sha256, state FROM upload_batch").fetchall() == before
        assert db.execute("SELECT batch_id, ordinal, message_id FROM batch_item ORDER BY ordinal").fetchall() == items
    with GatewayReader(db_path) as reader:
        stage = reader.run_stage("run-1")
    assert [b.payload_text for b in stage.batches] == [before[0][1]]
    assert {e.source_id for e in stage.envelopes} == {SRC_BMS}


# --- F1 (fix round 1): batches are bounded by bytes as well as count ---------

LONG_VALUE = "9" * 4096


def test_sealing_fits_batches_by_bytes_as_well_as_count(gateway, active: str, db_path: Path) -> None:
    """The reviewer's case: 256 admitted reports that together exceed 1 MiB."""
    admissions = [
        gateway.admit(report(value=LONG_VALUE, key=f"long-{n}"), snapshot_sha256=active, lab_run_ref="run-1")
        for n in range(256)
    ]
    assert {a.outcome for a in admissions} == {"ADMITTED"}
    batch_ids = gateway.seal()
    assert len(batch_ids) >= 2
    with GatewayReader(db_path) as reader:
        stage = reader.run_stage("run-1")
    assert all(e.batch_id is not None for e in stage.envelopes)
    sequences: list[int] = []
    for batch in stage.batches:
        assert len(batch.payload_text.encode("utf-8")) <= MAX_BATCH_BYTES
        parsed = parse_canonical_batch_v2_text(batch.payload_text)
        sequences += [parse_canonical_envelope_v3_text(t).sequence for t in parsed.envelopes]
    assert sorted(sequences) == list(range(1, 257))
    assert stage.seal_refusals == ()
    assert gateway.seal() == []


def test_an_individually_unbatchable_report_is_held_before_a_sequence(gateway, active: str, db_path: Path) -> None:
    held = gateway.admit(report(value="9" * MAX_BATCH_BYTES, key="huge"), snapshot_sha256=active, lab_run_ref="run-1")
    assert (held.outcome, held.kind, held.field) == ("HELD", "UNBATCHABLE", "value")
    assert held.sequence is None
    assert _count(db_path, "SELECT COUNT(*) FROM envelope_outbox") == 0
    assert _count(db_path, "SELECT COUNT(*) FROM sequence_state") == 0
    after = gateway.admit(report(key="normal"), snapshot_sha256=active, lab_run_ref="run-1")
    assert (after.outcome, after.sequence) == ("ADMITTED", 1)


def test_a_non_size_singleton_seal_failure_keeps_its_own_kind_and_field(
    gateway, active: str, db_path: Path, monkeypatch
) -> None:
    import assetops_gateway.service as service_module
    from assetops_contracts.ingestion_batch_v2 import BatchRejected

    def refuse(**kwargs):
        raise BatchRejected("INVALID_FIELD", "mapping.snapshot_sha256", "forced for the test")

    monkeypatch.setattr(service_module, "seal_batch_v2", refuse)
    held = gateway.admit(report(key="odd"), snapshot_sha256=active, lab_run_ref="run-1")
    assert (held.outcome, held.kind, held.field) == ("HELD", "INVALID_FIELD", "mapping.snapshot_sha256")
    assert held.sequence is None
    assert _count(db_path, "SELECT COUNT(*) FROM envelope_outbox") == 0
    assert _count(db_path, "SELECT COUNT(*) FROM sequence_state") == 0


def test_a_seal_refusal_is_durable_and_leaves_the_group_unbatched(
    gateway, active: str, db_path: Path, clock, monkeypatch
) -> None:
    import assetops_gateway.service as service_module
    from assetops_contracts.ingestion_batch_v2 import BatchRejected

    _publish_series(gateway, active)
    real = service_module.seal_batch_v2

    def refuse_bms(**kwargs):
        if kwargs["source_id"] == SRC_BMS:
            raise BatchRejected("TOO_LARGE", "batch", "forced for the test")
        return real(**kwargs)

    monkeypatch.setattr(service_module, "seal_batch_v2", refuse_bms)
    with pytest.raises(GatewayRefused) as refused:
        gateway.seal()
    assert refused.value.kind == "SEAL_REFUSED"
    gateway.close()
    monkeypatch.setattr(service_module, "seal_batch_v2", real)
    with GatewayReader(db_path) as reader:  # a fresh read, as after a restart
        stage = reader.run_stage("run-1")
    assert {b.source_id for b in stage.batches} == {SRC_PV}
    assert [e.batch_id for e in stage.envelopes if e.source_id == SRC_BMS] == [None] * 3
    assert [(r.source_id, r.kind, r.field) for r in stage.seal_refusals] == [(SRC_BMS, "TOO_LARGE", "batch")]
    reopened = GatewayService(db_path, clock=clock)
    try:
        assert len(reopened.seal()) == 1  # the cause is gone: the group seals, the refusal clears
    finally:
        reopened.close()
    with GatewayReader(db_path) as reader:
        assert reader.run_stage("run-1").seal_refusals == ()


def test_a_version_1_ledger_migrates_to_record_seal_refusals(db_path: Path, clock) -> None:
    from assetops_gateway.ledger import MIGRATION_1, _statements

    db = sqlite3.connect(db_path)
    for statement in _statements(MIGRATION_1):
        db.execute(statement)
    db.execute("INSERT INTO schema_migration(version, applied_at) VALUES (1, '2026-10-01T00:00:00Z')")
    db.commit()
    db.close()
    service = GatewayService(db_path, clock=clock)
    try:
        versions = [r[0] for r in service._db.execute("SELECT version FROM schema_migration ORDER BY version")]
        assert versions == [1, 2, 3, 4] and SCHEMA_VERSION == 4
        assert service._db.execute("SELECT COUNT(*) FROM seal_refusal").fetchone()[0] == 0
    finally:
        service.close()


def test_staged_statement_claims_only_admitted_envelopes() -> None:
    from assetops_contracts.gateway_stage import REGISTERED_STAGE_STATEMENTS

    text = REGISTERED_STAGE_STATEMENTS["STAGED"]
    assert "Every report the gateway admitted" in text and "held reports are listed separately" in text
