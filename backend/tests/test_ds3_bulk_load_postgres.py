"""DS3 (spec `specs/DS3-bulk-loader/spec.md` §4 tests 4 to 7): the bulk evidence load over PostgreSQL.

A module seed (`clone_database("ds3s")`: the converted Kobo Site, enabled, nothing ingested) is cloned afresh for
every test and every refusal case (`ds3c<n>`), each dropped in `finally`. No test connects to the module `URL`; it is
read only for the skip (D-DS3.14). The helpers here are shared by the parity and measurement modules.
Requires ASSETOPS_TEST_DATABASE_URL (backend/TESTING.md).
"""

from __future__ import annotations

import itertools
import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import IntegrityError
    from test_s2_evidence_ledger_postgres import Kit, _z, converted_enabled

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import (
        BulkAdmissionRefused,
        PostgresEvidenceLedger,
    )
    from assetops_backend.evidence.bulk_load import BulkEvidenceLoad, BulkLoaded, BulkLoadRefused
    from assetops_backend.evidence.ledger import decide
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_contracts.ingestion_batch_v2 import BatchRejected, parse_canonical_batch_v2_text, seal_batch_v2
    from assetops_contracts.source_envelope_v3 import SourceEnvelopeV3, canonical_envelope_v3_text, v3_message_id

DAY6 = datetime(2026, 10, 6, tzinfo=timezone.utc)
DAY7 = datetime(2026, 10, 7, tzinfo=timezone.utc)
FEEDERS = ("residential-meter", "clinic-meter", "mill-meter")
LEDGER_TABLES = ("ingestion_batch", "accepted_evidence", "ingestion_disposition", "evidence_rejection",
                 "batch_refusal", "recompute_job")
_CLONES = itertools.count(1)


# --- shared helpers (parity and measurement import these) ---------------------------------------------------------


def census(connection) -> dict[str, int]:
    """Row count of every base table of the schema, `alembic_version` apart (D-DS3.10)."""
    tables = connection.execute(text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
        "AND table_type = 'BASE TABLE' AND table_name <> 'alembic_version' ORDER BY table_name")).scalars().all()
    return {t: connection.execute(text(f'SELECT count(*) FROM "{t}"')).scalar_one() for t in tables}


def seed_database(tag: str, *, relabel: bool = False):
    """A clone of the run template holding the converted, enabled Kobo Site (and, with `relabel`, its current
    binding sets relabelled `minigrid-roles-4`, test-only as `v4_roles4`). Returns `(url, kit, census)`; every
    engine on it is disposed, so it can be cloned from."""
    url = pg_harness.clone_database(tag)
    store, eng = PostgresFoundationStore(url), create_engine(url)
    try:
        _, outcome = converted_enabled(store, eng)
        kit = Kit(eng, outcome.published.changed.id)
        if relabel:
            from test_w200_source_events_postgres import _delete_as_replica

            with eng.connect() as c:
                ids = c.execute(text("SELECT id FROM signal_binding_set_revision WHERE site_id = :s "
                                     "AND superseded_at IS NULL"), {"s": kit.principal.site_id}).scalars().all()
            assert ids
            _delete_as_replica(eng, ["UPDATE signal_binding_set_revision SET role_set = 'minigrid-roles-4' WHERE id IN ("
                                     + ", ".join(f"'{i}'" for i in ids) + ")"])
        with eng.connect() as c:
            baseline = census(c)
    except BaseException:
        pg_harness.dispose(store, eng)
        pg_harness.drop_database(url)
        raise
    pg_harness.dispose(store, eng)
    kit.engine = None  # never reconnect to the seed: a session on it would stop every clone
    return url, kit, baseline


def day_rows(day: datetime, devices: tuple[str, ...] | None = None):
    """One Kobo day, 00:00 to 23:45 every 15 minutes (spec §3): the generator RUNNING 06:00 to 08:00 and STOPPED
    otherwise, the three feeders at 10, the battery's state of charge 60 while the generator runs and 80 otherwise."""
    rows = []
    for i in range(96):
        t = day + timedelta(minutes=15 * i)
        running = day + timedelta(hours=6) <= t <= day + timedelta(hours=8)
        rows.append(("generator-controller", "status", t, "RUNNING" if running else "STOPPED"))
        rows += [(f, None, t, "10") for f in FEEDERS]
        rows.append(("battery-pcs-controller", "state-of-charge", t, "60" if running else "80"))
    return [r for r in rows if devices is None or r[0] in devices]


def seal_rows(kit, rows, sequences: dict) -> list[bytes]:
    """One SIMULATED batch per device, sequences per source as `Feeder.deliver` numbers them."""
    by_device: dict[str, list[str]] = {}
    for device, signal, when, value in rows:
        source = kit.binding(device, signal)["source_id"]
        sequences[source] = sequences.get(source, 0) + 1
        by_device.setdefault(device, []).append(kit.envelope(
            device, sequences[source], 0, value, source_time=_z(when), bound_signal=signal))
    return [kit.seal(texts, device_id=device).encode("utf-8") for device, texts in by_device.items()]


def kobo_days(kit, days) -> list[bytes]:
    sequences: dict = {}
    return [body for day in days for body in seal_rows(kit, day_rows(day), sequences)]


class Db:
    """One clone with its own engine and ledger; `close()` disposes both and drops the clone."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.engine = create_engine(url)
        self.ledger = PostgresEvidenceLedger(url)

    def load(self, raws, **options):
        return BulkEvidenceLoad(self.ledger, **options).load(raws)

    def counts(self) -> dict[str, int]:
        with self.engine.connect() as c:
            return {t: c.execute(text(f"SELECT count(*) FROM {t}" + (" WHERE domain = 'dispatch'"
                                                                     if t == "recompute_job" else ""))).scalar_one()
                    for t in LEDGER_TABLES}

    def rows(self, sql: str, **params):
        with self.engine.connect() as c:
            return c.execute(text(sql), params).all()

    def execute(self, sql: str, **params) -> None:
        with self.engine.begin() as c:
            c.execute(text(sql), params)

    def close(self) -> None:
        pg_harness.dispose(self.ledger, self.engine)
        pg_harness.drop_database(self.url)


# --- fixtures -----------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def seed():
    url, kit, _ = seed_database("ds3s")
    try:
        yield url, kit
    finally:
        pg_harness.drop_database(url)


@pytest.fixture()
def db(seed):
    url, kit = seed
    clone = Db(pg_harness.clone_database(f"ds3c{next(_CLONES)}", url))
    clone.kit = kit
    try:
        yield clone
    finally:
        clone.close()


def generator_day(kit, day=DAY6) -> bytes:
    [body] = seal_rows(kit, day_rows(day, ("generator-controller",)), {})
    return body


# --- test 4, 5: a day loads, a re-run loads nothing ---------------------------------------------------------------


def test_one_generator_status_day_loads_in_bulk(db) -> None:
    assert db.load([generator_day(db.kit)]) == BulkLoaded(1, 0, 96)
    [batch] = db.rows("SELECT status, total_count, processed_count, accepted_count, duplicate_count, rejected_count, "
                      "conflict_count, completed_at FROM ingestion_batch")
    assert batch[:7] == ("COMPLETED", 96, 96, 96, 0, 0, 0) and batch.completed_at is not None
    assert db.rows("SELECT count(*), min(ordinal), max(ordinal) FROM accepted_evidence")[0] == (96, 0, 95)
    assert db.rows("SELECT decision, count(*), min(ordinal), max(ordinal) FROM ingestion_disposition "
                   "GROUP BY decision") == [("ACCEPTED", 96, 0, 95)]
    [job] = db.rows("SELECT status, window_start, window_end FROM recompute_job WHERE domain = 'dispatch'")
    assert job.status == "PENDING"
    assert job.window_start <= DAY6 and job.window_end > DAY6 + timedelta(hours=23, minutes=45)
    # Every disposition names its own evidence row, ordinal for ordinal.
    assert db.rows("SELECT count(*) FROM ingestion_disposition d JOIN accepted_evidence e "
                   "ON e.id = d.accepted_evidence_id AND e.ordinal = d.ordinal AND e.message_id = d.message_id")[0][0] == 96


def test_the_same_bytes_again_load_nothing_new(db) -> None:
    body = generator_day(db.kit)
    db.load([body])
    before = db.counts()
    assert db.load([body]) == BulkLoaded(1, 1, 96)
    assert db.counts() == before


# --- test 6: refusals, each on a fresh clone, nothing written ------------------------------------------------------


def _foreign_gateway_batch(kit) -> bytes:
    gateway, b = str(uuid4()), kit.binding("generator-controller", "status")
    site = kit.doc["site"]["site_id"]
    when = _z(DAY6)
    envelope = canonical_envelope_v3_text(SourceEnvelopeV3(
        message_id=v3_message_id(site_id=site, gateway_id=gateway, source_id=b["source_id"], sequence_epoch="epoch-1",
                                 sequence=1),
        sequence_epoch="epoch-1", sequence=1, site_id=site, gateway_id=gateway, source_id=b["source_id"],
        device_id="generator-controller", signal_id=b["signal_id"], binding_set_id=kit.doc["mapping"]["binding_set_id"],
        binding_version=kit.doc["mapping"]["version"], source_time=when, published_at=when, interval_start=None,
        interval_end=None, family="MEASUREMENT", measurement="STATE_AT_INSTANT", value="STOPPED",
        unit=b["source_unit"], quality="GOOD", unavailable_reason=None))
    _, body = seal_batch_v2(
        site_id=site, gateway_id=gateway, source_id=b["source_id"], source_mode="SIMULATED",
        foundation_version=kit.doc["foundation"]["version"], foundation_valid_from=kit.doc["foundation"]["valid_from"],
        binding_set_id=kit.doc["mapping"]["binding_set_id"], binding_version=kit.doc["mapping"]["version"],
        snapshot_sha256=kit.sha, envelope_texts=[envelope])
    return body.encode("utf-8")


def _admission(db, raw: bytes):
    def refuse(*args):
        return AssertionError(args)

    admission = BatchIngestionService(db.ledger).admit(db.kit.principal, raw, datetime.now(timezone.utc), refuse)
    decisions = [decide(admission.basis, i, t) for i, t in enumerate(admission.batch.envelopes)]
    return admission, decisions


def _bulk_admit(db, admission, decisions, **change):
    batch = admission.batch
    now = datetime.now(timezone.utc)
    arguments = dict(external_batch_id=batch.batch_id, payload_sha256=batch.payload_sha256, source_id=batch.source_id,
                     source_mode=batch.source_mode, basis=admission.basis, batch_text=admission.text,
                     decisions=decisions, received_at=now, completed_at=now)
    return db.ledger.bulk_admit(db.kit.principal, **{**arguments, **change})


def case_live(db):
    body = db.kit.seal(db.kit.pv(2), mode="LIVE").encode()
    return lambda: db.load([body]), "BULK_NOT_SIMULATED"


def case_unknown_gateway(db):
    body = _foreign_gateway_batch(db.kit)
    return lambda: db.load([body]), "BULK_UNKNOWN_GATEWAY"


def case_gateway_disabled(db):
    db.execute("UPDATE gateway SET disabled_at = now() WHERE id = :g", g=db.kit.principal.gateway_id)
    body = db.kit.seal(db.kit.pv(2)).encode()
    return lambda: db.load([body]), "GATEWAY_DISABLED"


def case_source_disabled(db):
    db.execute("UPDATE source SET disabled_at = now() WHERE id = :s",
               s=UUID(db.kit.binding("pv-inverter-controller")["source_id"]))
    body = db.kit.seal(db.kit.pv(2)).encode()
    return lambda: db.load([body]), "SOURCE_DISABLED"


def case_rejected_ordinal(db):
    texts = db.kit.pv(3) + [db.kit.envelope("pv-inverter-controller", 4, 0, "1.5",
                                            source_time=_z(db.kit.start - timedelta(hours=1)))]
    body = db.kit.seal(texts).encode()
    return lambda: db.load([body]), "BULK_REJECTED_ORDINAL"


def case_v4_delta(db):
    """D-DS3.20: the real path stores a rejection for `v4.delta` (INTERVAL_DELTA on an EVENT channel) and accepts
    the rest; bulk refuses the whole batch. Test 6 does not call the real path for this case."""
    from test_w200_source_events_postgres import patched_v4

    v4 = patched_v4(db.kit, db.monkeypatch)
    body = db.kit.seal([v4.delta(100004)]).encode()
    return lambda: db.load([body]), "BULK_REJECTED_ORDINAL"


def case_batch_id_conflict(db):
    db.load([db.kit.seal(db.kit.pv(2)).encode()])
    changed = db.kit.seal(db.kit.pv(2, value="9.9")).encode()
    return lambda: db.load([changed]), "BATCH_ID_CONFLICT"


def case_lost_race(db):
    body = db.kit.seal(db.kit.pv(2)).encode()
    db.load([body])
    admission, decisions = _admission(db, body)
    return lambda: _bulk_admit(db, admission, decisions, payload_sha256="0" * 64), "BATCH_ID_CONFLICT"


def case_published(db):
    from test_s405_publication_postgres import P01, specs

    from assetops_backend.evidence.publication import register_authored

    body = db.kit.seal(db.kit.pv(3))
    assert register_authored(db.ledger, specs(), db.kit.principal.tenant_id, body, fixture_id=P01[0],
                             fixture_version=P01[1]).created
    return lambda: db.load([body.encode()]), "BULK_PUBLISHED_BATCH"


def case_coldchain_site(db):
    with db.engine.begin() as c:  # as test_w402_migration_postgres.set_type: before any evidence
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text("UPDATE site SET site_type = 'COLDCHAIN' WHERE id = :s"), {"s": db.kit.principal.site_id})
        c.execute(text("SET LOCAL session_replication_role = origin"))
    body = db.kit.seal(db.kit.pv(2)).encode()
    return lambda: db.load([body]), "BULK_SITE_TYPE_UNPROVEN"


def case_message_collision(db):
    db.load([db.kit.seal(db.kit.pv(3)).encode()])
    second = db.kit.seal(db.kit.pv(2, first=3)).encode()  # sequence 3 again, other bytes, another batch ID
    return lambda: db.load([second]), "BULK_MESSAGE_COLLISION"


def case_foreign_key(db):
    body = db.kit.seal(db.kit.pv(2)).encode()
    admission, decisions = _admission(db, body)
    broken = [replace(decisions[0], binding=replace(decisions[0].binding, binding_revision_id=uuid4())), *decisions[1:]]
    return lambda: _bulk_admit(db, admission, broken), IntegrityError


def case_malformed(db):
    body = b'{"schema": "not a batch"}'
    with pytest.raises(BatchRejected) as rejected:
        parse_canonical_batch_v2_text(body.decode())
    return lambda: db.load([body]), rejected.value.kind


CASES = [case_live, case_unknown_gateway, case_gateway_disabled, case_source_disabled, case_rejected_ordinal,
         case_v4_delta, case_batch_id_conflict, case_lost_race, case_published, case_coldchain_site, case_message_collision,
         case_foreign_key, case_malformed]


@pytest.mark.parametrize("case", CASES, ids=[c.__name__[5:] for c in CASES])
def test_a_refusal_writes_and_records_nothing(db, case, monkeypatch) -> None:
    db.monkeypatch = monkeypatch
    act, expected = case(db)
    before = db.counts()
    batches = db.rows("SELECT external_batch_id FROM ingestion_batch")
    if expected is IntegrityError:
        with pytest.raises(IntegrityError) as raised:
            act()
        assert "accepted_evidence_binding_fk" in str(raised.value)
    elif case is case_lost_race:
        with pytest.raises(BulkAdmissionRefused) as raised:
            act()
        assert raised.value.code == expected
    else:
        with pytest.raises(BulkLoadRefused) as raised:
            act()
        assert raised.value.code == expected, raised.value
        if case is case_rejected_ordinal:
            assert raised.value.detail.startswith("ordinal 3 ")
        if case is case_v4_delta:
            assert raised.value.detail.startswith("ordinal 0 ") and "MAPPING_INCOMPATIBLE" in raised.value.detail
    assert db.counts() == before
    assert db.rows("SELECT external_batch_id FROM ingestion_batch") == batches  # one transaction: no batch row left
    assert db.counts()["batch_refusal"] == 0


# --- test 7: a stopped load resumes ------------------------------------------------------------------------------


def test_a_load_stopped_at_its_third_batch_keeps_the_first_two_and_a_rerun_loads_the_rest(db) -> None:
    kobo = kobo_days(db.kit, [DAY6])[:4]
    bad = db.kit.seal(db.kit.pv(2), mode="LIVE").encode()
    with pytest.raises(BulkLoadRefused) as raised:
        db.load([kobo[0], kobo[1], bad, kobo[2], kobo[3]])
    assert raised.value.code == "BULK_NOT_SIMULATED"
    assert [r.status for r in db.rows("SELECT status FROM ingestion_batch")] == ["COMPLETED"] * 2
    assert db.load(kobo) == BulkLoaded(4, 2, 4 * 96)
    assert db.rows("SELECT count(*) FROM ingestion_batch WHERE status = 'COMPLETED'")[0][0] == 4
    assert db.rows("SELECT count(*) FROM accepted_evidence")[0][0] == 4 * 96
