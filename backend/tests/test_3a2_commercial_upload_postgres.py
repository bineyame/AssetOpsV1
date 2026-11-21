"""3A2 (spec §2, §3.5, §6 "Postgres"; D-3A2.2, D-3A2.4, D-3A2.13, D-3A2.16): migration 0065 and the upload methods of
the Postgres commercial store.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`.
"""
from __future__ import annotations

import os
import threading
import time
from dataclasses import replace
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
    from assetops_backend.commercial.model import Acceptance, StoreRefused, UploadDecisionRow
    from assetops_backend.commercial.service import CommercialRecords
    from assetops_backend.commercial.uploads import Actor, CommercialUploads, UploadRefused, UploadScope
    from test_3a1_commercial_postgres import Seeder
    from test_3a1_commercial_service import Clock
    from test_3a2_commercial_upload_service import (KEY, KISIWA, KOBO, T_SUBMIT, Keys, b_bill, b_budget, encode)

TABLES = ("commercial_upload", "commercial_upload_decision")
STORE_TABLES = ("commercial_intake", "commercial_record", "commercial_record_revision", "commercial_rejection",
                "commercial_upload", "commercial_upload_decision")
FIN, ANALYST, EXEC = "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST", "OPERATOR_EXECUTIVE"


def _person(engine, tenant_id: UUID, name: str) -> UUID:  # noqa: F811
    pid = uuid4()
    with engine.begin() as c:
        c.execute(text("INSERT INTO operator_account (id, tenant_id, email, email_key, display_name, created_at, "
                       "created_by) VALUES (:id, :t, :e, :e, :n, :at, 'service:test-seed')"),
                  {"id": pid, "t": tenant_id, "e": f"{name}@acme.example", "n": name.title(), "at": T_SUBMIT})
    return pid


@pytest.fixture()
def w(store, engine):  # noqa: F811 - `store` empties the tenant closure, these tables included
    seeder = Seeder(engine)
    tid = seeder.add_tenant("acme")
    kobo, kisiwa = seeder.add_site(tid, KOBO), seeder.add_site(tid, KISIWA)
    pg = PostgresCommercialStore(URL)
    clock = Clock(T_SUBMIT)
    records = CommercialRecords(pg, clock=clock)
    svc = CommercialUploads(records, pg, Keys({tid: KEY}), clock=clock, real_data=False)
    people = {n: _person(engine, tid, n) for n in ("ana", "fiona", "amina")}
    yield dict(store=pg, svc=svc, records=records, tid=tid, kobo_id=kobo, kisiwa_id=kisiwa,
               kobo=UploadScope(kobo, KOBO), org=UploadScope(None, None), ana=Actor(people["ana"], ANALYST),
               fiona=Actor(people["fiona"], FIN), amina=Actor(people["amina"], EXEC), people=people)
    pg.dispose()


def _count(engine, table: str) -> int:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()


def _counts(engine) -> list[int]:  # noqa: F811
    return [_count(engine, t) for t in STORE_TABLES]


def _submit(w, obj=None, scope=None) -> dict:
    return w["svc"].submit(w["tid"], scope or w["kobo"], w["ana"], encode(obj or b_bill()), file_name="kobo.json")


def _row(w, upload: dict):
    return w["store"].upload(w["tid"], UUID(upload["upload_id"])).upload


# --- 1: tables, triggers, CHECKs -----------------------------------------------------------------------------------

def test_1_tables_triggers_and_index(engine) -> None:  # noqa: F811
    with engine.connect() as c:
        for table in TABLES:
            assert c.execute(text("SELECT to_regclass(:t)"), {"t": table}).scalar_one() is not None
            assert c.execute(text("SELECT count(*) FROM pg_trigger WHERE tgrelid = to_regclass(:t) "
                                  "AND tgname = :t || '_immutable'"), {"t": table}).scalar_one() == 1
        assert c.execute(text("SELECT to_regclass('commercial_upload_tenant_at')")).scalar_one() is not None


def test_1_append_only(w, engine) -> None:  # noqa: F811
    upload = _submit(w)
    w["svc"].decide(w["tid"], w["kobo"], w["fiona"], upload["upload_id"], "DECLINE", "No.")
    for table in TABLES:
        for statement in (f"UPDATE {table} SET tenant_id = tenant_id", f"DELETE FROM {table}"):
            with pytest.raises(Exception, match="append-only|ledger"):
                with engine.begin() as c:
                    c.execute(text(statement))
    assert _count(engine, "commercial_upload") == _count(engine, "commercial_upload_decision") == 1


UPLOAD_PLANTS = {
    "file_name empty": dict(file_name=""), "file_name slash": dict(file_name="a/b"),
    "file_name backslash": dict(file_name="a\\b"), "file_name long": dict(file_name="x" * 201),
    "file_sha256": dict(file_sha256="ABC"), "file_bytes": dict(file_bytes=-1),
    "reader": dict(reader="Canonical"), "source_type": dict(source_type="Billing"), "source_system": dict(
        source_system=""), "provenance": dict(provenance="observed"), "batch_sha256": dict(batch_sha256="x"),
    "basis_sha256": dict(basis_sha256="x" * 64), "record_count": dict(record_count=-1, refused_count=-1 - 2),
    "new_count": dict(new_count=-1, revised_count=3), "revised_count": dict(revised_count=-1, new_count=3),
    "unchanged_count": dict(unchanged_count=-1, refused_count=1, refusal_index=(9,), refusal_code=("X",),
                            refusal_path=("record",)),
    "refused_count": dict(refused_count=-1, unchanged_count=1),
    "submitted_role": dict(submitted_role="SITE_MANAGER"), "sum": dict(record_count=3),
    "nothing new": dict(new_count=0, unchanged_count=2), "refusal cardinality": dict(refusal_index=(0,)),
    "month cardinality": dict(month_period=()), "row_map": dict(row_map=(1,)),
    "kept_index": dict(kept_index=(0,)),
}


@pytest.mark.parametrize("plant", sorted(UPLOAD_PLANTS))
def test_1_each_upload_check_refuses_a_planted_row(w, engine, plant) -> None:  # noqa: F811
    good = _row(w, _submit(w))
    with pytest.raises(StoreRefused) as raised:
        w["store"].add_upload(replace(good, id=uuid4(), **UPLOAD_PLANTS[plant]))
    assert raised.value.constraint and raised.value.constraint.startswith("commercial_upload"), plant
    assert _count(engine, "commercial_upload") == 1


@pytest.mark.parametrize("plant", ["decision", "reason empty", "reason padded", "reason long", "role",
                                   "declined without reason", "declined with intake"])
def test_1_each_decision_check_refuses_a_planted_row(w, engine, plant) -> None:  # noqa: F811
    upload_id = UUID(_submit(w)["upload_id"])
    accepted = w["records"].ingest(w["tid"], encode(b_budget()), entered_by="service:test-seed")
    base = UploadDecisionRow(uuid4(), w["tid"], upload_id, "DECLINED", "No.", None, w["fiona"].person_id, FIN,
                             T_SUBMIT)
    planted = {"decision": dict(decision="MAYBE"), "reason empty": dict(reason=""),
               "reason padded": dict(reason=" No."), "reason long": dict(reason="x" * 501),
               "role": dict(decided_role=ANALYST), "declined without reason": dict(reason=None),
               "declined with intake": dict(intake_id=accepted.intake_id)}[plant]
    with pytest.raises(StoreRefused) as raised:
        w["store"].write_decline(replace(base, **planted))
    assert raised.value.constraint and raised.value.constraint.startswith("commercial_upload_decision"), plant
    assert _count(engine, "commercial_upload_decision") == 0


# --- 2, 3: atomic acceptance and the lock ----------------------------------------------------------------------

def test_2_accept_is_atomic(w, engine) -> None:  # noqa: F811
    upload = _row(w, _submit(w))
    before = _counts(engine)
    planted = Acceptance(uuid4(), upload.id, w["ana"].person_id, ANALYST, upload.basis_sha256)  # role fails a CHECK
    with pytest.raises(StoreRefused) as raised:
        w["records"].ingest(w["tid"], upload.batch.encode("utf-8"), entered_by=f"person:{w['ana'].person_id}",
                            site_scope=upload.site_id, acceptance=planted)
    assert raised.value.constraint and raised.value.constraint.startswith("commercial_upload_decision")
    assert _counts(engine) == before == [0, 0, 0, 0, 1, 0]


def _waiting_on_advisory(engine) -> int:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted "
                              "AND database = (SELECT oid FROM pg_database WHERE datname = current_database())")
                         ).scalar_one()


def test_3_lock_two_accepts_of_one_upload(w, engine) -> None:  # noqa: F811
    upload = _row(w, _submit(w))
    conn = engine.connect()
    tx = conn.begin()
    conn.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('commercial:' || CAST(:v AS text), 0))"),
                 {"v": str(w["tid"])})
    results: list[object] = [None, None]
    actors = (w["fiona"], w["amina"])

    def run(i):
        try:
            results[i] = w["records"].ingest(
                w["tid"], upload.batch.encode("utf-8"), entered_by=f"person:{actors[i].person_id}",
                site_scope=upload.site_id,
                acceptance=Acceptance(uuid4(), upload.id, actors[i].person_id, actors[i].role, upload.basis_sha256))
        except Exception as error:  # noqa: BLE001 - reported as the outcome
            results[i] = error

    threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
    try:
        for thread in threads:
            thread.start()
        deadline = time.monotonic() + 10
        while _waiting_on_advisory(engine) < 2 and time.monotonic() < deadline:
            time.sleep(0.05)
        time.sleep(0.5)
        assert all(thread.is_alive() for thread in threads), "an accept finished while the lock was held"
        assert _waiting_on_advisory(engine) == 2
    finally:
        tx.commit()
        conn.close()
    for thread in threads:
        thread.join(30)
    assert sorted(type(r).__name__ for r in results) == ["IntakeResult", "UploadAlreadyDecided"], results
    accepted = next(r for r in results if not isinstance(r, Exception))
    with engine.connect() as c:
        rows = c.execute(text("SELECT decision, intake_id FROM commercial_upload_decision")).all()
    assert rows == [("ACCEPTED", accepted.intake_id)]
    assert _count(engine, "commercial_intake") == 1


# --- 4, 7: scrubbed errors -----------------------------------------------------------------------------------------

def _clean(error: BaseException, *markers: str) -> None:
    texts = [str(error), repr(error), str(error.__cause__), str(error.__context__)]
    assert error.__cause__ is None and error.__context__ is None
    assert all(m not in t and "Failing row" not in t and "DETAIL" not in t for t in texts for m in markers)


def test_4_data_and_integrity_errors_leave_scrubbed(w) -> None:
    marker = "PII-MARKER-7731.json"
    good = replace(_row(w, _submit(w)), file_name=marker)
    with pytest.raises(StoreRefused) as raised:
        w["store"].add_upload(replace(good, id=uuid4(), file_bytes=2**31))
    _clean(raised.value, marker, str(2**31))
    assert raised.value.constraint is None
    with pytest.raises(StoreRefused) as raised:
        w["store"].add_upload(good)  # the same ID again: the primary key
    _clean(raised.value, marker)
    assert raised.value.constraint == "commercial_upload_pkey"


def test_7_a_read_data_error_leaves_scrubbed(w) -> None:
    with pytest.raises(StoreRefused) as raised:
        w["store"].uploads_in_scope(w["tid"], w["kobo_id"], -1)
    assert raised.value.__cause__ is None and raised.value.__context__ is None


# --- 5: the reads round-trip -----------------------------------------------------------------------------------

def test_5_reads_round_trip(w, engine) -> None:  # noqa: F811
    site = _submit(w)
    org = _submit(w, b_budget(), w["org"])
    w["svc"].decide(w["tid"], w["org"], w["amina"], org["upload_id"], "ACCEPT")
    record = w["store"].upload(w["tid"], UUID(site["upload_id"]))
    assert record.submitted_by_name == "Ana" and record.decision is None and record.intake is None
    assert record.upload.kept_index == (0, 1) and record.upload.row_map is None
    assert record.upload.month_site_code == (KOBO,) and record.upload.month_period == ("2026-10",)
    accepted = w["store"].upload(w["tid"], UUID(org["upload_id"]))
    assert accepted.decided_by_name == "Amina" and accepted.decision.decision == "ACCEPTED"
    assert accepted.intake.intake.id == accepted.decision.intake_id and accepted.intake.intake.new_count == 2
    assert accepted.upload.month_site_code == (None, KOBO)
    assert [r.upload.id for r in w["store"].uploads_in_scope(w["tid"], w["kobo_id"], 50)] == [record.upload.id]
    assert [r.upload.id for r in w["store"].uploads_in_scope(w["tid"], None, 50)] == [accepted.upload.id]
    assert w["store"].uploads_in_scope(w["tid"], w["kisiwa_id"], 50) == ()
    assert w["store"].upload(uuid4(), record.upload.id) is None
    other = Seeder(engine).add_tenant("beta")  # a real second tenant, a real upload ID
    assert w["store"].upload(other, record.upload.id) is None
    assert w["store"].upload(w["tid"], record.upload.id) is not None
    answer = w["svc"].get(w["tid"], w["org"], org["upload_id"])
    assert answer["state"] == "ACCEPTED" and answer["result"]["counts"] == answer["preview"]
    with pytest.raises(UploadRefused):
        w["svc"].get(w["tid"], w["kobo"], org["upload_id"])


# --- 6: the downgrade ----------------------------------------------------------------------------------------------

def _this_migration(cfg):
    from alembic.script import ScriptDirectory

    for script in ScriptDirectory.from_config(cfg).walk_revisions():
        if "commercial_upload" in getattr(script.module, "TABLES", ()):
            return script
    raise AssertionError("no migration declares the upload tables")


def test_6_downgrade_refused_with_an_upload_then_down_and_up(w, engine) -> None:  # noqa: F811
    from alembic import command
    from alembic.script import ScriptDirectory

    cfg = pg_harness._alembic(URL)
    script = _this_migration(cfg)
    assert (script.revision, script.down_revision) == ("0065_commercial_upload", "0064_person_on_work")
    assert isinstance(script.down_revision, str) and script.down_revision != script.revision
    _submit(w)
    w["store"].dispose()
    with pytest.raises(Exception, match="refused: commercial uploads exist"):
        command.downgrade(cfg, script.down_revision)
    with engine.begin() as c:  # TRUNCATE is not a row DELETE; the append-only triggers do not fire on it
        c.execute(text("TRUNCATE " + ", ".join(TABLES)))
    command.downgrade(cfg, script.down_revision)
    with engine.connect() as c:
        for table in TABLES:
            assert c.execute(text("SELECT to_regclass(:t)"), {"t": table}).scalar_one() is None
        assert c.execute(text("SELECT to_regclass('commercial_intake')")).scalar_one() is not None
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)
