"""ANY-1 phase 2 (D-ANY.5 M3): the 0059 migration up/down, the period read store round-trip, and a late reading read
live and as known at k, on a real `*_test` database.

Every `<= k` comparison is on the transaction-time columns (`site_period_read.computed_at`, `event_outbox.recorded_at`,
`event_consumption.processed_at`, all wall-clock `clock_timestamp()`): k is taken from the stored instants, never from
story time (D-ANY.5 M1).

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped otherwise.
"""
from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    import test_w402_reads_postgres as w402
    from assetops_backend.chain.adapters.postgres_period_read_store import PostgresPeriodReadStore
    from assetops_backend.chain.events import parse_register
    from assetops_backend.chain.period_read import NO_ROW_STATE, PeriodReadBuilder, PeriodReader
    from assetops_backend.chain.ports import PeriodKey, ProvenanceBlock, SiteRef
    from test_any1_period_read import KIND, HourKind

D = date(2026, 10, 21)
D2 = D + timedelta(days=1)


def _register():
    # Only the reading event: the install's foundation events must not make every day of the Site pending here.
    return parse_register({
        "register_version": 1,
        "events": {"reading.accepted@1": {"days": "span_local", "measures": "by_role"}},
        "inputs": {"productive_kwh": {"roles": ["feeder_demand"]}},
        "kinds": {KIND: {"grain": "hour", "site_types": ["MINIGRID"],
                         "inputs": {"roles": ["pv_available_power"], "mini_depth": ["renewable"]}}},
    })


def _site(t, s):
    return SiteRef(t, s, w402.CODE, "MINIGRID", w402.ZONE)


def _computed(engine, s, revision):
    with engine.connect() as c:
        return c.execute(text("SELECT min(computed_at), max(computed_at) FROM site_period_read WHERE site_id = :s "
                              "AND revision = :r"), {"s": s, "r": revision}).one()


def _late_reading(engine, t, s):
    """A pv reading for D recorded into the outbox now (wall clock); returns (event_id, recorded_at)."""
    subject = {"roles": ["pv_available_power"], "span": ["2026-10-21T06:00:00Z", "2026-10-21T07:00:00Z"]}
    with engine.begin() as c:
        return c.execute(text(
            "INSERT INTO event_outbox (type, schema_version, occurred_at, source, tenant_id, site_id, subject, "
            "idempotency_key) VALUES ('reading.accepted', 1, :o, 'accepted_evidence', :t, :s, CAST(:subj AS jsonb), "
            ":idem) RETURNING event_id, recorded_at"),
            {"o": datetime.fromisoformat("2026-10-21T06:00:00+00:00"), "t": t, "s": s,
             "subj": json.dumps(subject), "idem": f"any1-{uuid4()}"}).one()


def _consume(engine, event_id):
    with engine.begin() as c:
        return c.execute(text("INSERT INTO event_consumption (consumer, event_id) VALUES ('snapshots', :e) "
                              "RETURNING processed_at"), {"e": event_id}).scalar_one()


def test_0059_catalogue_insert_only_and_store_round_trip(store, engine) -> None:  # noqa: F811
    with engine.connect() as c:
        indexes = {r[0] for r in c.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = "
                                                "'site_period_read'"))}
        triggers = {r[0] for r in c.execute(text(
            "SELECT tgname FROM pg_trigger WHERE tgrelid IN ('site_period_read'::regclass, "
            "'revision_provenance'::regclass) AND NOT tgisinternal"))}
    assert "site_period_read_day" in indexes
    assert {"site_period_read_immutable", "revision_provenance_immutable"} <= triggers

    _, t, s = w402._setup(store, engine)
    periods = PostgresPeriodReadStore(URL)
    try:
        kind = HourKind()
        rid = uuid4()
        kind.provenance = {rid: {"classes": {"MEASURED": 3}}}
        builder = PeriodReadBuilder(periods, {KIND: kind})
        first = builder.build(t, _site(t, s), D, KIND)
        assert [w.written for w in first] == [True, True] and {w.row.revision for w in first} == {1}
        assert [w.written for w in builder.build(t, _site(t, s), D, KIND)] == [False, False]
        key = PeriodKey(t, s, KIND, first[0].row.period_start)
        assert periods.latest(key) == (1, first[0].row.input_fp, "v1")
        assert periods.provenance(t, [rid], "v1") == {rid: {"classes": {"MEASURED": 3}}}
        assert periods.append_provenance(ProvenanceBlock(t, rid, "v1", {"classes": {"MEASURED": 9}})) is False
        assert periods.provenance(t, [rid], "v1") == {rid: {"classes": {"MEASURED": 3}}}  # never overwritten

        rows = periods.read_latest(t, [s], [KIND], D, D, None)
        assert sorted(r.body["hour"] for r in rows) == [6, 7]
        assert all(r.state == "CURRENT" and r.local_day == D and r.computed_at is not None for r in rows)
        assert rows[0].body == next(w.row.body for w in first if w.row.period_start == rows[0].period_start)

        for sql in ("UPDATE site_period_read SET state = 'STALE'", "DELETE FROM site_period_read",
                    "UPDATE revision_provenance SET block = '{}'::jsonb", "DELETE FROM revision_provenance"):
            with pytest.raises(DBAPIError):
                with engine.begin() as c:
                    c.execute(text(sql))
        with pytest.raises(DBAPIError):  # a refused CHECK: a lower-case state
            with engine.begin() as c:
                c.execute(text(
                    "INSERT INTO site_period_read (tenant_id, site_id, kind, period_start, period_end, local_day, "
                    "revision, builder_version, input_fp, state, body) VALUES (:t, :s, :k, :p, :e, :d, 9, 'v1', :fp, "
                    "'current', '{}'::jsonb)"),
                    {"t": t, "s": s, "k": KIND, "p": first[0].row.period_start, "e": first[0].row.period_end,
                     "d": D, "fp": "a" * 64})
    finally:
        periods.dispose()


def test_late_reading_live_and_as_known_at_k(store, engine) -> None:  # noqa: F811
    _, t, s = w402._setup(store, engine)
    site = _site(t, s)
    periods = PostgresPeriodReadStore(URL)
    try:
        kind = HourKind()
        builder = PeriodReadBuilder(periods, {KIND: kind})
        builder.build(t, site, D, KIND)  # revision 1
        rev1_lo, rev1_hi = _computed(engine, s, 1)
        event_id, recorded = _late_reading(engine, t, s)
        reader = PeriodReader(periods, _register(), builder.versions())

        live = reader.read(t, [site], [KIND], D, D2)
        assert live.pending == {(s, D, KIND): ("event",)}
        assert [r.row.revision for r in live.rows] == [1, 1] and all(r.pending == ("event",) for r in live.rows)
        assert live.absent == ((s, D2, KIND),)  # a requested day with no row is reported, never silent
        assert live.day_state(s, D, KIND) == "PENDING" and live.day_state(s, D2, KIND) == NO_ROW_STATE

        processed = _consume(engine, event_id)
        time.sleep(1.0)  # revision 2 a whole second after revision 1: `known_at` travels in whole seconds
        kind.inputs = {"ids": ["r1", "r2"]}  # the late reading lands: revision 2
        assert {w.row.revision for w in builder.build(t, site, D, KIND) if w.written} == {2}
        rev2_lo, _ = _computed(engine, s, 2)
        assert rev1_hi < recorded < processed < rev2_lo  # one wall clock for every ledger

        now = reader.read(t, [site], [KIND], D, D)
        assert [r.row.revision for r in now.rows] == [2, 2] and not now.pending and now.absent == ()

        # k between revision 1 and revision 2, after the event's consumption: revision 1 is served, not pending
        k = processed + (rev2_lo - processed) / 2
        hist = reader.read(t, [site], [KIND], D, D, known_at=k)
        assert [r.row.revision for r in hist.rows] == [1, 1] and not hist.pending and hist.absent == ()
        assert hist.day_state(s, D, KIND) is None  # rows render

        # k after the event was recorded and before it was consumed: revision 1, PENDING at k
        k = recorded + (processed - recorded) / 2
        hist = reader.read(t, [site], [KIND], D, D, known_at=k)
        assert [r.row.revision for r in hist.rows] == [1, 1]
        assert hist.pending == {(s, D, KIND): ("event",)} and hist.day_state(s, D, KIND) == "PENDING"

        # k before revision 1: nothing known yet - absent, rendered by the no-row rule
        k = rev1_lo - timedelta(microseconds=1)
        hist = reader.read(t, [site], [KIND], D, D, known_at=k)
        assert hist.rows == [] and not hist.pending
        assert hist.absent == ((s, D, KIND),) and hist.day_state(s, D, KIND) == NO_ROW_STATE == "NO_DATA"

        # the parity harness takes its between-revisions k from the same rows (D-ANY.5 step 5)
        from urllib.parse import parse_qs, urlsplit

        import period_read_parity

        case = period_read_parity.between_revisions_case(URL)
        assert case.id == "any.between_revisions.site_period_read"
        q = parse_qs(urlsplit(case.path).query)
        assert case.path.startswith(f"/api/sites/{w402.CODE}/outcome-board?") and q["date"] == [D.isoformat()]
        k = datetime.fromisoformat(q["known_at"][0].replace("Z", "+00:00"))
        assert rev1_hi < k < rev2_lo and k.microsecond == 0  # whole seconds on the wire, strictly between
        served = reader.read(t, [site], [KIND], D, D, known_at=k)
        assert [r.row.revision for r in served.rows] == [1, 1]
    finally:
        periods.dispose()


def test_downgrade_refused_with_rows_then_allowed(store, engine) -> None:  # noqa: F811
    from alembic import command

    _, t, s = w402._setup(store, engine)
    periods = PostgresPeriodReadStore(URL)
    try:
        PeriodReadBuilder(periods, {KIND: HourKind()}).build(t, _site(t, s), D, KIND)
    finally:
        periods.dispose()
    cfg = pg_harness._alembic(URL)
    with pytest.raises(Exception, match="stored read periods exist"):
        command.downgrade(cfg, "0058_fuel_watermark_inputs")
    with engine.begin() as c:  # TRUNCATE is not a row DELETE; the append-only trigger does not fire on it
        c.execute(text("TRUNCATE site_period_read, revision_provenance"))
    command.downgrade(cfg, "0058_fuel_watermark_inputs")
    with engine.connect() as c:
        assert c.execute(text("SELECT to_regclass('site_period_read')")).scalar_one() is None
        assert c.execute(text("SELECT to_regclass('revision_provenance')")).scalar_one() is None
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)
