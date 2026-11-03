"""CH-2 L2 (build sheet §7.2): migration 0042 and the thread store on Postgres.

The 0042 catalogue (four tables, four append-only triggers, the link target trigger, the `chain_action` view);
downgrade refused while thread rows exist; the view returning both Action kinds; two concurrent placements of
one key giving one thread; and the property tests - the backfill run twice gives identical rows (a full table dump
compare, the second run writing nothing), and a shuffled source order gives the same rows.

Seeded through the existing Finding case runner (F01, F02) and one Action through the s6 accept harness; one
domain Action row is inserted directly (the cold producer is out of scope). Not registered in setup_cache
`FUNCTION_OPS`: `setup_cache.py` records that `CaseRunner` cannot be cached (packet deviation D-3).
"""

from __future__ import annotations

import hashlib
import random
import threading

from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s6_action_store_postgres import CASES, CaseRunner, harness, run_case
    from test_w203_cold_migration_postgres import head

    import pg_harness
    from assetops_backend.chain.backfill import run_threads
    from assetops_backend.chain.composition import build_thread_sources, build_thread_store
    from assetops_backend.chain.threads import MemoryThreads, ThreadRegistry, key_of

HEAD = "0042_chain_threads"
PREVIOUS = "0043_chain_snapshots"  # CH-1a merged first; 0042 sits on 0043
TABLES = ("finding_thread", "finding_thread_occurrence", "finding_thread_event", "chain_action_thread")
CLOCK_COLUMNS = {"joined_at", "recorded_at", "linked_at"}  # clock_timestamp() defaults; compared by count only


def dump(engine) -> dict[str, list[tuple]]:
    out = {}
    with engine.connect() as c:
        for t in TABLES:
            cols = [r[0] for r in c.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = :t ORDER BY ordinal_position"),
                {"t": t}) if r[0] not in CLOCK_COLUMNS]
            out[t] = [tuple(r) for r in c.execute(text(f"SELECT {', '.join(cols)} FROM {t} ORDER BY 1, 2, 3, 4"))]
    return out


@pytest.fixture()
def seeded(store, engine):  # noqa: F811
    runner = CaseRunner(store, engine)
    run_case(runner, CASES["F01"])
    run_case(runner, CASES["F02"])
    h = harness(runner)
    try:
        f01 = h.findings()["2026-10-06"]
        made = h.accept(f01, h.recommendation(f01).json()["proposal"])
        assert made.status_code == 201, made.text
    finally:
        h.close()
    with engine.begin() as c:
        rev = c.execute(text("SELECT id FROM finding_revision WHERE finding_id = :f ORDER BY revision_no DESC "
                             "LIMIT 1"), {"f": f01}).scalar_one()
        domain_id = uuid4()
        c.execute(text(
            "INSERT INTO domain_action (id, tenant_id, site_id, action_no, action_code, domain, origin_finding_id, "
            "origin_finding_revision_id, title, raised_at, actor_kind, actor_id, attestation, idempotency_key, "
            "payload_sha256) VALUES (:id, :t, :s, 900001, 'ACT-900001', 'COLDCHAIN', :f, :r, "
            "'Thread test', now(), 'SERVICE', 'ch2-test', 'CH-2 L2 seed', 'ch2-seed-0001', :sha)"),
            {"id": domain_id, "t": runner.tenant, "s": runner.site, "f": f01, "r": rev,
             "sha": hashlib.sha256(b"ch2").hexdigest()})
    reader, writer = build_thread_sources(URL), build_thread_store(URL)
    yield runner, reader, writer, f01, domain_id
    pg_harness.dispose(runner.findings, reader, writer)


def test_0042_catalogue_and_head(engine) -> None:  # noqa: F811
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_revision(HEAD).down_revision == PREVIOUS and script.get_heads() == [pg_harness.alembic_head()]
    assert head(engine) == pg_harness.alembic_head()
    with engine.connect() as c:
        tables = set(c.execute(text("SELECT tablename FROM pg_tables WHERE tablename = ANY(:t)"),
                               {"t": list(TABLES)}).scalars())
        triggers = set(c.execute(text(
            "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal AND tgrelid = ANY(CAST(:t AS regclass[]))"),
            {"t": list(TABLES)}).scalars())
        view = c.execute(text("SELECT count(*) FROM pg_views WHERE viewname = 'chain_action'")).scalar_one()
    assert tables == set(TABLES) and view == 1
    assert triggers == {f"{t}_immutable" for t in TABLES} | {"chain_action_thread_target"}


def test_backfill_links_is_idempotent_append_only_and_order_free(seeded, engine) -> None:  # noqa: F811
    runner, reader, writer, f01, domain_id = seeded
    t, s = runner.tenant, runner.site

    first = run_threads(reader, writer, t, s)
    assert first[0]["written"] >= 2 and first[1]["counts"] == {"LINKED": 2}, first
    rows = dump(engine)
    # F01 and F02 sit on one generator thread (one key), as occurrences 1 and 2; one OPEN event.
    with engine.connect() as c:
        occ = c.execute(text("SELECT o.occurrence_no, f.anchor_start FROM finding_thread_occurrence o "
                             "JOIN finding f ON f.id = o.finding_id ORDER BY 1")).all()
        kinds = dict(c.execute(text("SELECT kind, count(*) FROM chain_action WHERE thread_id IS NOT NULL "
                                    "GROUP BY kind")).all())
        unlinked = c.execute(text("SELECT count(*) FROM chain_action WHERE thread_id IS NULL")).scalar_one()
    assert [o[0] for o in occ] == [1, 2] and len(rows["finding_thread"]) == 1
    assert kinds == {"MINI_TRIAL": 1, "DOMAIN_INTENT": 1} and unlinked == 0

    # Property: a second run writes nothing and every row is identical.
    second = run_threads(reader, writer, t, s)
    assert [r["written"] for r in second] == [0, 0], second
    assert dump(engine) == rows

    # Property: a shuffled source order (same created_at ties included) gives the same rows.
    sources = reader.sources(t, s)
    shuffled = sources[:]
    random.Random(11).shuffle(shuffled)
    memory = MemoryThreads()
    ThreadRegistry(memory).place_all(shuffled)
    db_occ = sorted((str(r[2]), r[3], str(r[4])) for r in rows["finding_thread_occurrence"])
    mem_occ = sorted((str(o["thread_id"]), o["occurrence_no"], str(o["finding_id"]))
                     for o in memory.occurrences.values())
    assert db_occ == mem_occ and set(map(str, memory.threads)) == {str(r[0]) for r in rows["finding_thread"]}

    # Append-only: UPDATE and DELETE refused on every table.
    for table in TABLES:
        with pytest.raises(DBAPIError):
            with engine.begin() as c:
                c.execute(text(f"DELETE FROM {table}"))
    for table in TABLES:
        with pytest.raises(DBAPIError):
            with engine.begin() as c:
                c.execute(text(f"UPDATE {table} SET tenant_id = tenant_id"))
    # The target trigger refuses a link to a missing Action.
    with pytest.raises(DBAPIError, match="not in this tenant and Site"):
        with engine.begin() as c:
            tid = rows["finding_thread"][0][0]
            c.execute(text("INSERT INTO chain_action_thread (tenant_id, site_id, action_kind, action_id, thread_id, "
                           "origin_finding_id, linked_by) VALUES (:t, :s, 'MINI_TRIAL', :a, :th, :f, 'tick')"),
                      {"t": t, "s": s, "a": uuid4(), "th": tid, "f": f01})

    # Downgrade refused while thread rows exist; the head is unchanged.
    from alembic import command

    engine.dispose()
    with pytest.raises(DBAPIError, match="Downgrade of 0042_chain_threads refused"):
        command.downgrade(_alembic(), PREVIOUS)
    assert head(engine) == pg_harness.alembic_head()


def test_concurrent_placements_of_one_key_make_one_thread(seeded, engine) -> None:  # noqa: F811
    runner, reader, writer, _, _ = seeded
    first = reader.sources(runner.tenant, runner.site)[0]
    later = [x for x in reader.sources(runner.tenant, runner.site) if key_of(x) == key_of(first)
             and x.finding_id != first.finding_id]
    from assetops_backend.chain.threads import plan_place

    gate = threading.Barrier(2)
    errors: list[BaseException] = []

    def go(src) -> None:
        gate.wait()
        try:
            writer.place(src, plan_place, "tick")
        except BaseException as error:  # noqa: BLE001 - collected and asserted below
            errors.append(error)

    assert later, "F01 and F02 share one key (non-vacuous concurrency proof)"
    second = later[0]
    workers = [threading.Thread(target=go, args=(x,)) for x in (first, second)]
    for w in workers:
        w.start()
    for w in workers:
        w.join(timeout=60)
    assert not errors, errors
    with engine.connect() as c:
        threads = c.execute(text("SELECT count(*) FROM finding_thread")).scalar_one()
        occurrences = c.execute(text("SELECT count(*) FROM finding_thread_occurrence")).scalar_one()
        events = c.execute(text("SELECT count(*) FROM finding_thread_event")).scalar_one()
    assert threads == 1 and events == 1 and occurrences == 2
