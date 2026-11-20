"""3A1 (spec §2, §4.1, §6; R2, R3, R4, R7, R11, R13, R14, D-3A1.12): migration 0063 and the Postgres commercial store.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`.
"""
from __future__ import annotations

import os
import threading
import time
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
    from assetops_backend.commercial.model import Plan, RecordOutcome, StoreRefused
    from assetops_backend.commercial.service import CommercialRecords
    from test_3a1_commercial_service import (BY, T0, Clock, MemoryCommercialStore, adjustment, assert_exact, batch,
                                             SITES, ds1b_batches, encode, expense, fixture_batches, ingest,
                                             ingest_ds1b, ingest_fixture, kinds, make_world, month_move)

TABLES = ("commercial_intake", "commercial_record", "commercial_record_revision", "commercial_rejection")


class Seeder:
    """`make_world`'s store interface over the database: tenants and Sites inserted as 3C0a's tests do."""

    def __init__(self, engine) -> None:  # noqa: F811
        self.engine = engine

    def add_tenant(self, slug: str) -> UUID:
        tid = uuid4()
        with self.engine.begin() as c:
            c.execute(text("INSERT INTO tenant (id, slug, name, created_at) VALUES (:id, :s, :s, :at)"),
                      {"id": tid, "s": slug, "at": T0})
        return tid

    def add_site(self, tenant_id: UUID, code: str) -> UUID:
        sid = uuid4()
        with self.engine.begin() as c:
            c.execute(text(
                "INSERT INTO site (id, tenant_id, site_code, site_code_key, name, site_type, timezone, lifecycle, "
                "origin, proposed_source_mode, created_at) VALUES (:id, :t, :c, lower(:c), :c, 'MINIGRID', 'UTC', "
                "'ACTIVE', 'IMPORTED', 'SIMULATED', :at)"), {"id": sid, "t": tenant_id, "c": code, "at": T0})
        return sid


@pytest.fixture()
def commercial(store, engine):  # noqa: F811 - `store` empties the tenant closure, these four tables included
    owned = PostgresCommercialStore(URL)
    yield owned
    owned.dispose()


@pytest.fixture()
def world(commercial, engine):  # noqa: F811
    w = make_world(Seeder(engine))
    clock = Clock()
    return dict(w, store=commercial, clock=clock, svc=CommercialRecords(commercial, clock=clock))


def mirror(w) -> dict:
    """An in-memory world with the same tenant and Site IDs, so the two stores' sort orders compare (P7)."""
    mem = MemoryCommercialStore()
    slugs = {tid: slug for slug, tid in w["tenants"].items()}
    mem.slugs.update(slugs)
    for slug, codes in SITES.items():
        for code in codes:
            mem.sites[(w["tenants"][slug], code.lower())] = w["sites"][code]
    clock = Clock()
    return dict(tenants=w["tenants"], sites=w["sites"], store=mem, clock=clock, svc=CommercialRecords(mem, clock=clock))


def _count(engine, table: str) -> int:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()


def _valid(engine, sql: str, params: dict) -> None:  # noqa: F811
    """The planted base row inserts (anti-vacuity), and is rolled back."""
    with engine.connect() as c:
        tx = c.begin()
        c.execute(text(sql), params)
        tx.rollback()


def _sqlstate(engine, sql: str, params: dict | None = None) -> str:  # noqa: F811
    with pytest.raises(DBAPIError) as raised:
        with engine.begin() as c:
            c.execute(text(sql), params or {})
    return raised.value.orig.sqlstate


# --- the schema -------------------------------------------------------------------------------------------------

def test_the_four_tables_their_triggers_and_indexes_exist(engine) -> None:  # noqa: F811
    with engine.connect() as c:
        for table in TABLES:
            assert c.execute(text("SELECT to_regclass(:t)"), {"t": table}).scalar_one() is not None, table
        triggers = {(r[0], r[1]) for r in c.execute(text(
            "SELECT tgrelid::regclass::text, tgname FROM pg_trigger WHERE NOT tgisinternal "
            "AND tgrelid::regclass::text = ANY(:t)"), {"t": list(TABLES)})}
        indexes = {r[0] for r in c.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = ANY(:t)"),
                                           {"t": list(TABLES)})}
        defaults = c.execute(text("SELECT count(*) FROM information_schema.columns WHERE table_name = ANY(:t) "
                                  "AND column_default IS NOT NULL"), {"t": list(TABLES)}).scalar_one()
        isolation = c.execute(text("SHOW default_transaction_isolation")).scalar_one()
    assert triggers == {(t, f"{t}_immutable") for t in TABLES}
    assert {"commercial_intake_tenant_at", "commercial_revision_read"} <= indexes
    assert defaults == 0
    assert isolation == "read committed"


def test_the_four_tables_are_append_only(world, engine) -> None:  # noqa: F811
    ingest_fixture(world)
    for table in TABLES:
        n = _count(engine, table)
        assert n >= 1, table
        assert _sqlstate(engine, f"UPDATE {table} SET tenant_id = tenant_id") == "23001"  # ledger_append_only()
        assert _sqlstate(engine, f"DELETE FROM {table}") == "23001"
        assert _count(engine, table) == n


# --- planted rows: each CHECK, the keys and the foreign keys ------------------------------------------------------

def _base(world) -> dict:
    """One valid STORED intake, record, revision and rejection, written through the service."""
    result = ingest(world, batch([expense("BASE"), expense("BASE-X", site="EV-EMB")]))
    tid = world["tenants"]["lakeside-power"]
    (rev,) = world["store"].record_history(tid, result.outcomes[0].record_id)
    return dict(tid=tid, intake=result.intake_id, record=result.outcomes[0].record_id, rev=rev)


INTAKE_SQL = ("INSERT INTO commercial_intake (id, tenant_id, source_type, source_system, provenance, produced_at, "
              "batch_sha256, state, refusal_code, refusal_path, record_count, new_count, revised_count, "
              "unchanged_count, refused_count, entered_by, entered_at) VALUES (:id, :tenant_id, :source_type, "
              ":source_system, :provenance, :produced_at, :batch_sha256, :state, :refusal_code, :refusal_path, "
              ":record_count, :new_count, :revised_count, :unchanged_count, :refused_count, :entered_by, :entered_at)")
RECORD_SQL = ("INSERT INTO commercial_record (id, tenant_id, site_id, kind, source_system, source_record_id, "
              "first_recorded_at) VALUES (:id, :tenant_id, :site_id, :kind, :source_system, :source_record_id, :at)")
REVISION_SQL = ("INSERT INTO commercial_record_revision (id, tenant_id, record_id, site_id, kind, revision_no, "
                "source_version, intake_id, record_sha256, canonical, provenance, recognition_period, occurred_at, "
                "settled_at, effective_from, effective_to, amount, currency, quantity, unit, status, "
                "supersedes_revision_id, recorded_at) VALUES (:id, :tenant_id, :record_id, :site_id, :kind, "
                ":revision_no, :source_version, :intake_id, :record_sha256, :canonical, :provenance, "
                ":recognition_period, :occurred_at, :settled_at, :effective_from, :effective_to, :amount, :currency, "
                ":quantity, :unit, :status, :supersedes_revision_id, :recorded_at)")
REJECTION_SQL = ("INSERT INTO commercial_rejection (id, tenant_id, intake_id, record_index, source_record_id, code, "
                 "path, recorded_at) VALUES (:id, :tenant_id, :intake_id, :record_index, :source_record_id, :code, "
                 ":path, :at)")


def _rows(b) -> dict:
    tid, rev = b["tid"], b["rev"]
    intake = dict(id=uuid4(), tenant_id=tid, source_type="expense_ledger", source_system="s", provenance="bench-tested",
                  produced_at=T0, batch_sha256="a" * 64, state="STORED", refusal_code=None, refusal_path=None,
                  record_count=1, new_count=1, revised_count=0, unchanged_count=0, refused_count=0, entered_by=BY,
                  entered_at=T0)
    record = dict(id=uuid4(), tenant_id=tid, site_id=rev.site_id, kind="EXPENSE", source_system="s",
                  source_record_id="R-1", at=T0)
    revision = dict(id=uuid4(), tenant_id=tid, record_id=b["record"], site_id=rev.site_id, kind="EXPENSE",
                    revision_no=2, source_version="v2", intake_id=b["intake"], record_sha256="b" * 64, canonical="{}",
                    provenance="source-emulated", recognition_period="2026-11", occurred_at=T0, settled_at=None,
                    effective_from=None, effective_to=None, amount=Decimal("1.50"), currency="USD", quantity=None,
                    unit=None, status="PAID", supersedes_revision_id=rev.id, recorded_at=T0)
    rejection = dict(id=uuid4(), tenant_id=tid, intake_id=b["intake"], record_index=7, source_record_id=None,
                     code="CANONICAL_REF", path="record.kind", at=T0)
    return dict(intake=intake, record=record, revision=revision, rejection=rejection)


SQL = {"intake": INTAKE_SQL, "record": RECORD_SQL, "revision": REVISION_SQL, "rejection": REJECTION_SQL}

CHECKS = [
    ("intake", dict(source_type="Bad-Type")), ("intake", dict(source_system="")), ("intake", dict(provenance="observed")),
    ("intake", dict(batch_sha256="A" * 64)), ("intake", dict(state="ACCEPTED")),
    ("intake", dict(state="REFUSED", refusal_code="lower", refusal_path="json", record_count=0, new_count=0)),
    ("intake", dict(refusal_path="x" * 301)), ("intake", dict(record_count=-1, new_count=-1)),
    ("intake", dict(new_count=-1, revised_count=2)), ("intake", dict(revised_count=-1, new_count=2)),
    ("intake", dict(unchanged_count=-1, new_count=2)), ("intake", dict(refused_count=-1, new_count=2)),
    ("intake", dict(entered_by="someone")), ("intake", dict(state="REFUSED", record_count=0, new_count=0)),
    ("intake", dict(refusal_code="INTAKE_X", refusal_path="batch")),
    ("intake", dict(provenance=None)), ("intake", dict(produced_at=None)), ("intake", dict(new_count=0)),
    ("record", dict(kind="SERVICE_TICKET")), ("record", dict(source_system="x" * 201)),
    ("record", dict(source_record_id="")), ("record", dict(site_id=None)),
    ("revision", dict(revision_no=0, supersedes_revision_id=None)), ("revision", dict(source_version="x" * 65)),
    ("revision", dict(record_sha256="z" * 64)), ("revision", dict(provenance="observed")),
    ("revision", dict(recognition_period="2026-13")), ("revision", dict(currency="usd")),
    ("revision", dict(unit="m3", quantity=Decimal("1"))), ("revision", dict(status="paid")),
    ("revision", dict(currency=None)), ("revision", dict(quantity=Decimal("2"))),
    ("revision", dict(supersedes_revision_id=None)), ("revision", dict(revision_no=1)),
    ("revision", dict(effective_from=date(2026, 11, 2), effective_to=date(2026, 11, 1))),
    ("rejection", dict(record_index=-1)), ("rejection", dict(source_record_id="")), ("rejection", dict(code="x")),
    ("rejection", dict(path="")),
]


def test_each_check_refuses_a_planted_row(world, engine) -> None:  # noqa: F811
    b = _base(world)
    for table in SQL:
        _valid(engine, SQL[table], _rows(b)[table])
    for table, change in CHECKS:
        assert _sqlstate(engine, SQL[table], _rows(b)[table] | change) == "23514", (table, change)


def test_the_keys_and_foreign_keys_hold(world, engine) -> None:  # noqa: F811
    b = _base(world)
    tid, rev = b["tid"], b["rev"]
    beta = world["tenants"]["harvest-cold"]
    rows = _rows(b)
    assert _sqlstate(engine, RECORD_SQL, rows["record"] | dict(site_id=world["sites"]["COLD-THIKA"])) == "23503"
    assert _sqlstate(engine, RECORD_SQL, rows["record"] | dict(site_id=uuid4())) == "23503"
    _valid(engine, RECORD_SQL, rows["record"] | dict(site_id=None, kind="BUDGET_LINE"))  # a null Site, a budget line
    assert _sqlstate(engine, RECORD_SQL, rows["record"] | dict(source_system="lakeside-accounts",
                                                             source_record_id="BASE")) == "23505"
    assert _sqlstate(engine, REVISION_SQL, rows["revision"] | dict(source_version="1")) == "23505"
    assert _sqlstate(engine, REVISION_SQL, rows["revision"] | dict(revision_no=1, supersedes_revision_id=None)) == "23505"
    assert _sqlstate(engine, REVISION_SQL, rows["revision"] | dict(kind="ADJUSTMENT")) == "23503"  # R11 kind
    assert _sqlstate(engine, REVISION_SQL, rows["revision"] | dict(tenant_id=beta)) == "23503"
    second = ingest(world, batch([expense("OTHER")]))
    (foreign,) = world["store"].record_history(tid, second.outcomes[0].record_id)
    assert _sqlstate(engine, REVISION_SQL, rows["revision"] | dict(supersedes_revision_id=foreign.id)) == "23503"
    assert _sqlstate(engine, REVISION_SQL, rows["revision"] | dict(intake_id=uuid4())) == "23503"
    assert _sqlstate(engine, REJECTION_SQL, rows["rejection"] | dict(record_index=1)) == "23505"
    assert _sqlstate(engine, REJECTION_SQL, rows["rejection"] | dict(tenant_id=beta)) == "23503"
    assert _sqlstate(engine, INTAKE_SQL, rows["intake"] | dict(tenant_id=uuid4())) == "23503"
    assert rev.revision_no == 1


# --- the adapter --------------------------------------------------------------------------------------------------

def test_every_port_method_round_trips(world, engine) -> None:  # noqa: F811
    store, tid = world["store"], world["tenants"]["lakeside-power"]
    assert store.tenant_slug(tid) == "lakeside-power" and store.tenant_slug(uuid4()) is None
    assert store.site_ids(tid, {"kobo-001", "MTO-001", "COLD-THIKA"}) == {
        "kobo-001": world["sites"]["KOBO-001"], "MTO-001": world["sites"]["MTO-001"]}
    first = ingest(world, batch([expense("A"), expense("B", site="EV-EMB")]))
    world["clock"].now = T0 + timedelta(hours=1)
    second = ingest(world, batch([expense("A", "2", amount="12.50"), expense("A", "3", amount="12.75")]))
    assert kinds(second) == ["REVISED", "REVISED"]
    (existing,) = store.existing(tid, "lakeside-accounts", {"A", "missing"}).values()
    history = store.record_history(tid, existing.record_id)
    assert dict(existing.versions) == {r.source_version: r.record_sha256 for r in history}
    assert dict(existing.provenances) == {"1": "source-emulated", "2": "source-emulated", "3": "source-emulated"}
    assert (existing.latest_revision_no, existing.latest_revision_id, existing.kind) == (3, history[-1].id, "EXPENSE")
    assert [r.revision_no for r in history] == [1, 2, 3] and history[2].amount == Decimal("12.75")
    assert history[1].recorded_at == T0 + timedelta(hours=1) and history[0].recorded_at == T0
    (latest,) = store.latest_revisions(tid)
    assert latest == history[-1] and latest.source_system == "lakeside-accounts" and latest.source_record_id == "A"
    summary = store.intake(tid, first.intake_id)
    assert summary.intake.new_count == 1 and summary.intake.refused_count == 1 and summary.intake.entered_by == BY
    assert [(r.record_index, r.code, r.source_record_id) for r in summary.rejections] == [(1, "INTAKE_SITE_UNKNOWN", "B")]
    assert summary.revision_ids == (history[0].id,)
    assert sorted(store.intake(tid, second.intake_id).revision_ids, key=str) == sorted(
        (history[1].id, history[2].id), key=str)
    assert store.intake(world["tenants"]["metro-bus"], first.intake_id) is None
    before = [_count(engine, t) for t in TABLES]
    seen: list = []

    def decide(found):
        seen.append(dict(found))
        return Plan(summary.intake, (), (), (), (RecordOutcome(0, "UNCHANGED", "A", existing.record_id, None, None,
                                                               None),))
    plan = store.write_intake(tid, "lakeside-accounts", {"A"}, decide, dry_run=True)
    assert plan.outcomes[0].outcome == "UNCHANGED" and list(seen[0]) == ["A"]
    assert [_count(engine, t) for t in TABLES] == before


def test_latest_after_a_correction_and_the_month_move(world) -> None:  # R7 in Postgres
    tid = month_move(world)
    store = world["store"]
    assert store.latest_revisions(tid, recognition_period="2026-10") == ()
    (row,) = store.latest_revisions(tid, recognition_period="2026-11")
    assert row.revision_no == 2 and [r.revision_no for r in store.record_history(tid, row.record_id)] == [1, 2]
    assert store.latest_revisions(tid, kind="EXPENSE", site_id=world["sites"]["KISIWA-001"]) == (row,)


def full_run(w, tmp_path) -> None:
    """2a's fixture with its refusal, DS1b's batches, an envelope refusal, a tenant mismatch and a conflict."""
    ingest_fixture(w)
    ingest_ds1b(w, ds1b_batches(tmp_path))
    ingest(w, b"{", tenant="metro-bus")
    ingest(w, encode(fixture_batches()[4]), tenant="harvest-cold")
    ingest(w, batch([expense("Q-KIS-0091", amount="1.00")]))


def test_the_full_fixture_run_keeps_its_invariants(world, engine, tmp_path) -> None:  # noqa: F811 - R2, R11, R3
    full_run(world, tmp_path)
    with engine.connect() as c:
        assert c.execute(text(
            "SELECT count(*) FROM commercial_record_revision v JOIN commercial_intake i ON i.id = v.intake_id "
            "WHERE i.state = 'REFUSED'")).scalar_one() == 0
        assert c.execute(text("SELECT count(*) FROM commercial_intake WHERE state = 'REFUSED'")).scalar_one() == 2
        assert c.execute(text(  # R11: n > 1 supersedes n - 1 of the same record
            "SELECT count(*) FROM commercial_record_revision v LEFT JOIN commercial_record_revision p "
            "ON p.id = v.supersedes_revision_id AND p.record_id = v.record_id AND p.revision_no = v.revision_no - 1 "
            "WHERE v.revision_no > 1 AND p.id IS NULL")).scalar_one() == 0
        assert c.execute(text(  # R11: revision and record agree on site_id
            "SELECT count(*) FROM commercial_record_revision v JOIN commercial_record r ON r.id = v.record_id "
            "WHERE v.site_id IS DISTINCT FROM r.site_id")).scalar_one() == 0
        assert c.execute(text("SELECT count(*) FROM commercial_record_revision")).scalar_one() == 164
        assert c.execute(text("SELECT count(*) FROM commercial_rejection")).scalar_one() == 2
    rows = [r for t in world["tenants"].values() for r in world["store"].latest_revisions(t)]
    assert len(rows) == 164 and {r.provenance for r in rows} == {"source-emulated"}
    assert assert_exact(rows) > 58


def test_the_two_stores_agree_and_sort_alike(world, tmp_path) -> None:  # P7, R7, R3 in both stores
    mem = mirror(world)
    files = ds1b_batches(tmp_path)
    for w in (world, mem):
        ingest_fixture(w)
        ingest_ds1b(w, files)
        month_move(w)
    for slug, tid in world["tenants"].items():
        key = lambda r: (r.site_id, r.kind, r.revision_no, r.recognition_period, r.source_system,  # noqa: E731
                         r.source_record_id, r.canonical, r.amount, r.quantity, r.provenance)
        for filters in ({}, {"recognition_period": "2026-10"}, {"kind": "BUDGET_LINE"},
                        {"site_id": world["sites"]["KOBO-001"]}):
            pg = world["store"].latest_revisions(tid, **filters)
            assert [key(r) for r in pg] == [key(r) for r in mem["store"].latest_revisions(tid, **filters)], (slug,
                                                                                                         filters)
    assert any(r.site_id is None for r in world["store"].latest_revisions(world["tenants"]["lakeside-power"]))


# --- R13: no value in an error -------------------------------------------------------------------------------------

def test_a_refused_row_leaves_no_value_in_the_error(world) -> None:
    marker = "PII-MARKER-4410"
    b = _base(world)
    store, tid = world["store"], b["tid"]
    rev = replace(b["rev"], id=uuid4(), revision_no=2, source_version="2", supersedes_revision_id=b["rev"].id,
                  currency="usd", canonical=marker, status="PAID")
    intake = store.intake(tid, b["intake"]).intake
    for planned in (replace(rev), replace(rev, currency="USD", source_version="1")):  # a CHECK, then a unique key
        plan = Plan(replace(intake, id=uuid4()), (), (planned,), (), ())
        planned_with_marker = replace(plan, intake=replace(plan.intake, source_system=marker))
        with pytest.raises(StoreRefused) as raised:
            store.write_intake(tid, "lakeside-accounts", set(), lambda _found: planned_with_marker, dry_run=False)
        error = raised.value
        texts = [str(error), repr(error), str(error.__cause__), str(error.__context__)]
        assert error.__cause__ is None and error.__context__ is None
        assert all(marker not in t and "Failing row" not in t and "Key (" not in t for t in texts)
        assert error.constraint and error.constraint.startswith("commercial_record_revision")
    assert store.intake(tid, b["intake"]) is not None


# --- R4: the lock -------------------------------------------------------------------------------------------------

def _waiting_on_advisory(engine) -> int:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted "
                              "AND database = (SELECT oid FROM pg_database WHERE datname = current_database())")
                         ).scalar_one()


def test_lock_two_intakes_of_one_new_record(world, engine) -> None:  # noqa: F811
    """The 3C0a R2 shape: hold the tenant's commercial lock, start two intakes of the same new record, prove both
    wait on it, release, and get one NEW and one UNCHANGED, never two records."""
    tid = world["tenants"]["lakeside-power"]
    data = batch([expense("RACE")])
    conn = engine.connect()
    tx = conn.begin()
    conn.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('commercial:' || CAST(:v AS text), 0))"),
                 {"v": str(tid)})
    results: list[object] = [None, None]

    def run(i):
        try:
            results[i] = world["svc"].ingest(tid, data, entered_by=BY)
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
        assert all(thread.is_alive() for thread in threads), "an intake finished while the lock was held"
        assert _waiting_on_advisory(engine) == 2
    finally:
        tx.commit()
        conn.close()
    for thread in threads:
        thread.join(30)
    assert all(not isinstance(r, Exception) for r in results), results
    assert sorted(kinds(r)[0] for r in results) == ["NEW", "UNCHANGED"]
    assert [_count(engine, t) for t in TABLES] == [2, 1, 1, 0]


# --- the downgrade (R14, D-3A1.12) --------------------------------------------------------------------------------

def _this_migration(cfg):
    from alembic.script import ScriptDirectory

    for script in ScriptDirectory.from_config(cfg).walk_revisions():
        if "commercial_intake" in getattr(script.module, "TABLES", ()):
            return script
    raise AssertionError("no migration declares the commercial tables")


def test_downgrade_refused_with_a_record_then_down_and_up(world, engine) -> None:  # noqa: F811
    from alembic import command

    cfg = pg_harness._alembic(URL)
    script = _this_migration(cfg)
    assert script.revision != script.down_revision and isinstance(script.down_revision, str)
    ingest(world, batch([expense()]))
    with pytest.raises(Exception, match="refused: commercial records exist"):
        command.downgrade(cfg, script.down_revision)
    with engine.begin() as c:  # TRUNCATE is not a row DELETE; the append-only triggers do not fire on it
        c.execute(text("TRUNCATE " + ", ".join(TABLES)))
    command.downgrade(cfg, script.down_revision)
    with engine.connect() as c:
        for table in TABLES:
            assert c.execute(text("SELECT to_regclass(:t)"), {"t": table}).scalar_one() is None
        assert c.execute(text("SELECT count(*) FROM pg_proc WHERE proname = 'ledger_append_only'")).scalar_one() == 1
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)
    from alembic.script import ScriptDirectory

    assert pg_harness.alembic_head() == ScriptDirectory.from_config(cfg).get_current_head()


def test_downgrade_refused_with_only_a_refused_intake(world, engine) -> None:  # noqa: F811 - L1: commercial_intake alone
    from alembic import command

    cfg = pg_harness._alembic(URL)
    script = _this_migration(cfg)
    result = ingest(world, b"not json")
    assert result.state == "REFUSED"
    assert [_count(engine, t) for t in TABLES] == [1, 0, 0, 0]
    with pytest.raises(Exception, match="refused: commercial records exist"):
        command.downgrade(cfg, script.down_revision)
    with engine.connect() as c:
        assert c.execute(text("SELECT to_regclass('commercial_intake')")).scalar_one() is not None
