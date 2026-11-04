"""CH-1b L2 (build sheet CH-1b §6 step 2): the 0044 catalogue, producers in the fact's transaction (rollback leaves
no event, one event per statement, the job UPDATE rule), the event store (idempotent consumption, the re-mark
surviving compare-and-delete, the backfill event) and the drain against the real snapshot store.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped otherwise.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    from test_s1_bindings_postgres import engine, store  # noqa: F401
    import test_ch1a_snapshot_postgres as ch1a
    import test_w402_reads_postgres as w402
    from assetops_backend.chain.adapters.postgres_event_store import PostgresEventStore
    from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
    from assetops_backend.chain.drain import drain

UTC = timezone.utc
T0 = datetime(2026, 10, 6, 6, tzinfo=UTC)
PRODUCER_TABLES = ("accepted_evidence", "analytic_run_selection", "mini_depth_selection", "recompute_job",
                   "financial_assumption_revision", "foundation_revision", "finding_revision",
                   "mini_opportunity_revision", "action_event", "domain_action", "verification_outcome",
                   "outcome_objective_revision")


def _events(c, s, type_: str) -> int:
    return c.execute(text("SELECT count(*) FROM event_outbox WHERE site_id = :s AND type = :y"),
                     {"s": s, "y": type_}).scalar_one()


def test_0044_catalogue(engine) -> None:  # noqa: F811
    with engine.connect() as c:
        triggers = {(r[0], r[1]) for r in c.execute(text(
            "SELECT tgrelid::regclass::text, tgname FROM pg_trigger WHERE NOT tgisinternal "
            "AND (tgname LIKE '%chain_event%' OR tgname LIKE 'event_%immutable')"))}
        tables = set(c.execute(text("SELECT tablename FROM pg_tables WHERE tablename IN "
                                    "('event_outbox', 'event_consumption', 'snapshot_dirty')")).scalars())
    assert tables == {"event_outbox", "event_consumption", "snapshot_dirty"}
    assert {(t, f"{t}_chain_event") for t in PRODUCER_TABLES} <= triggers
    assert ("recompute_job", "recompute_job_chain_event_update") in triggers
    assert {("event_outbox", "event_outbox_immutable"), ("event_consumption", "event_consumption_immutable")} <= triggers


def _jobs(c, t, s, n: int) -> list:
    ids = [uuid4() for _ in range(n)]
    values = ", ".join(f"(:id{i}, :t, :s, 'mini_opportunity', :lo, :hi, NULL, 'PENDING', :at, :at)" for i in range(n))
    params = {"t": t, "s": s, "lo": T0, "hi": T0 + timedelta(hours=1), "at": T0} | {f"id{i}": v for i, v in enumerate(ids)}
    c.execute(text("INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, "
                   f"cause_evidence_id, status, available_at, created_at) VALUES {values}"), params)
    return ids


def test_producers_write_in_the_fact_transaction_one_event_per_statement(store, engine) -> None:  # noqa: F811
    _, t, s = w402._setup(store, engine)
    with engine.connect() as c:
        assert _events(c, s, "foundation.revised") >= 1  # the set-up's own Foundation publication
        before = _events(c, s, "job.changed")
    with engine.connect() as c:  # rollback: no event
        tx = c.begin()
        _jobs(c, t, s, 3)
        assert _events(c, s, "job.changed") == before + 1
        tx.rollback()
    with engine.begin() as c:  # one 3-row statement: one event
        ids = _jobs(c, t, s, 3)
    with engine.connect() as c:
        assert _events(c, s, "job.changed") == before + 1
    with engine.begin() as c:  # a status change is an event; a coalescing available_at move is not
        c.execute(text("UPDATE recompute_job SET status = 'LEASED' WHERE id = ANY(:i)"), {"i": ids})
        c.execute(text("UPDATE recompute_job SET available_at = available_at + interval '1 minute' "
                       "WHERE id = ANY(:i)"), {"i": ids})
    with engine.connect() as c:
        assert _events(c, s, "job.changed") == before + 2
        subject = c.execute(text("SELECT subject FROM event_outbox WHERE site_id = :s AND type = 'job.changed' "
                                 "ORDER BY recorded_at DESC LIMIT 1"), {"s": s}).scalar_one()
    assert subject["status"] == "LEASED" and subject["domain"] == "mini_opportunity"
    for sql in ("UPDATE event_outbox SET payload = '{}'::jsonb", "DELETE FROM event_outbox"):
        with pytest.raises(DBAPIError):
            with engine.begin() as c:
                c.execute(text(sql))


def test_event_store_consume_re_mark_and_drain(store, engine) -> None:  # noqa: F811
    _, t, s = w402._setup(store, engine)
    events, snaps = PostgresEventStore(URL), PostgresSnapshotStore(URL)
    day = ch1a.DAYS3[0]
    try:
        events.record_backfill(t, s, T0, {"from": "2026-10-06"}, f"{s}|a")
        events.record_backfill(t, s, T0, {"from": "2026-10-06"}, f"{s}|a")  # the same range: the same event
        events.record_backfill(t, s, T0, {"from": "2026-10-06"}, f"{s}|b")
        first, second = events.unconsumed("snapshots", t, s, ["backfill.site"], 10)
        assert first.recorded_at <= second.recorded_at
        events.mark_and_consume("snapshots", first, [(day, "productive_kwh")])
        assert [e.event_id for e in events.unconsumed("snapshots", t, s, ["backfill.site"], 10)] == [second.event_id]
        with pytest.raises(DBAPIError):  # consumption is recorded once per consumer and event
            events.mark_and_consume("snapshots", first, [])
        (row,) = events.pop(t, s, 10)
        events.mark_and_consume("snapshots", second, [(day, "productive_kwh")])  # a re-mark during the build
        assert events.done(t, s, row) is False and events.queued(t, s) == 1
        with engine.connect() as c:
            first_id = c.execute(text("SELECT first_event_id FROM snapshot_dirty WHERE site_id = :s"),
                                 {"s": s}).scalar_one()
        assert first_id == first.event_id  # the re-mark keeps the first cause
        builder = ch1a._builder(ch1a.StubInputs({day: 8}), snaps)
        report = drain(events, builder, t, ch1a._site(t, s), limit=10)
        assert (report.processed, report.written, report.deferred, report.re_marked) == (1, 1, 0, 0)
        # mark again with no new input: the drain writes nothing
        events.record_backfill(t, s, T0, {"from": "2026-10-06"}, f"{s}|c")
        (third,) = events.unconsumed("snapshots", t, s, ["backfill.site"], 10)
        events.mark_and_consume("snapshots", third, [(day, "productive_kwh")])
        again = drain(events, builder, t, ch1a._site(t, s), limit=10)
        assert (again.processed, again.written, again.unchanged, again.deferred) == (1, 0, 1, 0)
    finally:
        events.dispose()
        snaps.dispose()


def test_tick_stages_consume_drain_and_defer_on_a_cap(store, engine) -> None:  # noqa: F811
    """The real `chain_snapshots` and `chain_threads` stage bodies: the set-up's facts are consumed, the marked days
    rebuilt, a rerun consumes and writes nothing, and an item cap is an OK result with the rest deferred."""
    from assetops_backend.scheduling import stages

    _, t, s = w402._setup(store, engine)
    ids = {"tenant_id": str(t), "site_id": str(s)}
    from assetops_backend.chain.adapters.file_chain_config import load_event_register

    names = sorted({k.partition("@")[0] for k in load_event_register().consumes("snapshots")})
    events = PostgresEventStore(URL)
    try:
        total = events.pending("snapshots", t, s, names)
    finally:
        events.dispose()
    capped = stages.chain_snapshots(URL, {**ids, "consume_limit": 1, "items": 1})
    assert capped["code"] == "OK" and capped["consume"]["consumed"] == 1
    assert capped["deferred"] >= total - 1 > 0  # the unconsumed rest is deferred, never a failure
    first = stages.chain_snapshots(URL, {**ids, "consume_limit": 500, "items": 500})
    assert first["code"] == "OK" and first["deferred"] == 0 and first["consume"]["consumed"] == total - 1
    assert first["drain"]["processed"] >= 1
    again = stages.chain_snapshots(URL, {**ids, "consume_limit": 500, "items": 500})
    assert again["code"] == "OK" and again["consume"]["consumed"] == 0 and again["drain"]["processed"] == 0
    threads = stages.chain_threads(URL, {**ids, "limit": 500})
    assert threads["code"] == "OK" and threads["deferred"] == 0
    rerun = stages.chain_threads(URL, {**ids, "limit": 500})
    assert rerun["code"] == "OK" and rerun["consumed"]["threads"]["consumed"] == 0 and rerun["processed"] == 0
