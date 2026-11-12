"""SR-10a (rev 10b.3 tests, D-SR.31/36): the `mini_depth.fuel_day` / `mini_depth.backup_day` stored day rows on a
real `*_test` database, over the W4-02 fixture (Kobo-shaped mini-grid, Nairobi).

- a built day row holds every Site-local hour (24), and each stored hour equals a live `MiniDepthRead._hour` read;
- an absent day row reads STILL_PROCESSING ("Still being prepared"), never "nothing known";
- a new accepted reading's event dirties the day kinds; the tick's consume + drain rebuilds the row;
- for 3 sampled hours (the 12:00 drill-in link and two more), the stored hour equals the one-hour route's card.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped otherwise.
"""
from __future__ import annotations

import json
import os
from datetime import timedelta
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import test_w402_reads_postgres as w402
    from assetops_backend.chain.adapters.file_chain_config import load_event_register
    from assetops_backend.chain.adapters.postgres_event_store import PostgresEventStore
    from assetops_backend.chain.adapters.postgres_period_read_store import PostgresPeriodReadStore
    from assetops_backend.chain.composition import period_kind_versions
    from assetops_backend.chain.drain import drain
    from assetops_backend.chain.events import SiteInfo, consume
    from assetops_backend.chain.period_read import SERVED_KINDS_ENV, PeriodReadBuilder, PeriodReader
    from assetops_backend.chain.ports import SiteRef
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.mini_depth import day_summary as ds
    from assetops_backend.mini_depth import period_rows as pr
    from assetops_backend.mini_depth.inputs import local_hour
    from assetops_backend.mini_depth.read import MiniDepthRead
    from assetops_backend.mini_depth.store import PostgresMiniDepthStore
    from assetops_backend.mini_depth.worker import MiniDepthWorker

DAY_KINDS = tuple(pr.DAY_KINDS) if URL else ()
SAMPLED = (6, 12, 18)  # local hours given a selected head; 12 is the drill-in link's hour


def _consume_all(engine) -> None:
    with engine.begin() as c:
        c.execute(text("INSERT INTO event_consumption (consumer, event_id) SELECT 'snapshots', o.event_id "
                       "FROM event_outbox o WHERE NOT EXISTS (SELECT 1 FROM event_consumption x "
                       "WHERE x.consumer = 'snapshots' AND x.event_id = o.event_id)"))


def _site(t, s):
    return SiteRef(t, s, w402.CODE, "MINIGRID", w402.ZONE)


def _builder(engine) -> PeriodReadBuilder:
    builders = pr.kind_builders(MiniDepthRead(engine, link_rows_on))
    return PeriodReadBuilder(PostgresPeriodReadStore(engine=engine), {k: builders[k] for k in DAY_KINDS})


def _periods(engine) -> PeriodReader:
    return PeriodReader(PostgresPeriodReadStore(engine=engine), load_event_register(), period_kind_versions())


def _fixture(store, engine):  # noqa: F811
    installed, t, s = w402._setup(store, engine)
    w402._ingest(engine, installed)
    worker = MiniDepthWorker(None, PostgresMiniDepthStore(engine))
    day = w402.DAYS[2]
    for h in SAMPLED:  # every domain of three hours of the day gets a selected head
        w = local_hour(day, h, w402.ZONE)
        assert all(o.status == "DONE" for o in worker.reconcile(w402.CODE, w.start, w.end))
    return t, s, day


def _stored(engine, t, s, day, kind):
    result = _periods(engine).read(t, [_site(t, s)], [kind], day, day)
    (row,) = [r for r in result.rows if r.row.kind == kind]
    return row, result


def _strip(h: dict) -> dict:
    return {k: v for k, v in h.items() if k != "pending_link_rows"}


def test_day_rows_hold_every_local_hour_equal_to_live_hour_reads(store, engine) -> None:  # noqa: F811
    t, s, day = _fixture(store, engine)
    written = [w for kind in DAY_KINDS for w in _builder(engine).build(t, _site(t, s), day, kind)]
    assert len(written) == 2 and all(w.written for w in written)
    assert not any(w.written for kind in DAY_KINDS for w in _builder(engine).build(t, _site(t, s), day, kind))
    reader = MiniDepthRead(engine, link_rows_on)
    with engine.connect() as c:
        known = c.execute(text("SELECT clock_timestamp()")).scalar_one()
        for kind, domain in pr.DAY_KINDS.items():
            row, _ = _stored(engine, t, s, day, kind)
            stored = row.row.body["hours"]
            assert len(stored) == 24
            live = [pr.hour_json(reader._hour(c, t, s, domain, day, local_hour(day, i, w402.ZONE), known, False))
                    for i in range(24)]
            assert [_strip(h) for h in stored] == [_strip(h) for h in live], kind
            heads = [h for h in stored if h["head"] is not None]
            assert len(heads) == len(SAMPLED)  # non-vacuous: three selected hours, the rest missing
            summary = (ds.fuel_day_summary if domain == "fuel" else ds.backup_day_summary)(
                day, ds.hours_of(row.row.body, historical=False, pending=False))
            assert (summary["hours_expected"], summary["hours_assessed"], summary["hours_missing"]) == (24, 3, 21)


def test_absent_day_row_reads_still_processing(store, engine) -> None:  # noqa: F811
    t, s, day = _fixture(store, engine)
    for kind in DAY_KINDS:
        _builder(engine).build(t, _site(t, s), day, kind)
    _consume_all(engine)
    days = [day, day + timedelta(days=1)]  # the second day has no built row
    for kind, domain in pr.DAY_KINDS.items():
        result = _periods(engine).read(t, [_site(t, s)], [kind], days[0], days[-1])
        assert result.is_absent(s, days[1], kind) and not result.is_absent(s, days[0], kind)
        body = ds.compose(domain, {"id": s, "site_code": w402.CODE, "site_name": None, "timezone": w402.ZONE},
                          {}, days, result, {d: "COMPLETE" for d in days}, historical=False)
        assert [d["state"] for d in body["days"]][1] == "STILL_PROCESSING"
        assert body["days"][0]["state"] != "STILL_PROCESSING" and body["days"][0]["partial"] is True


def test_a_new_accepted_reading_dirties_and_the_tick_rebuilds_the_day_rows(store, engine) -> None:  # noqa: F811
    t, s, day = _fixture(store, engine)
    for kind in DAY_KINDS:
        _builder(engine).build(t, _site(t, s), day, kind)
    _consume_all(engine)
    before = {k: _stored(engine, t, s, day, k)[0].row.revision for k in DAY_KINDS}
    w = local_hour(day, 9, w402.ZONE)
    with engine.begin() as c:  # the ledger's accepted-reading event for a fuel_level reading in the 09:00 hour
        c.execute(text(
            "INSERT INTO event_outbox (type, schema_version, occurred_at, source, tenant_id, site_id, subject, "
            "idempotency_key) VALUES ('reading.accepted', 1, :o, 'accepted_evidence', :t, :s, CAST(:subj AS jsonb), "
            ":idem)"), {"o": w.start, "t": t, "s": s, "idem": f"sr10-{uuid4()}", "subj": json.dumps(
                {"roles": ["fuel_level"], "asset_ids": [], "span": [w.start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                                         w.end.strftime("%Y-%m-%dT%H:%M:%SZ")]})})
        # and a live recompute of that hour, so the rebuilt row differs (non-vacuous)
        for jd in ("mini_fuel", "mini_backup"):
            c.execute(text("SELECT mini_enqueue_hour(:t, :s, :jd, :lo, :hi, NULL, clock_timestamp())"),
                      {"t": t, "s": s, "jd": jd, "lo": w.start, "hi": w.end})
    for kind, domain in pr.DAY_KINDS.items():
        row, result = _stored(engine, t, s, day, kind)
        assert result.is_pending(s, day, kind)  # the unconsumed event dirties the day kind
        body = ds.compose(domain, {"id": s, "site_code": w402.CODE, "site_name": None, "timezone": w402.ZONE},
                          {}, [day], result, {day: "COMPLETE"}, historical=False)
        assert body["days"][0]["state"] == "STILL_PROCESSING"
    events = PostgresEventStore(engine=engine)
    consumed = consume(events, load_event_register(), "snapshots", t, s, SiteInfo("MINIGRID", w402.ZONE), 500)
    assert consumed.consumed >= 1

    class NoMeasures:
        def build(self, *_a, **_k):
            return []

    report = drain(events, NoMeasures(), t, _site(t, s), 500, period_builder=_builder(engine))
    assert all(report.by_measure.get(k) == 1 for k in DAY_KINDS), report.as_json()
    for kind in DAY_KINDS:
        row, result = _stored(engine, t, s, day, kind)
        assert row.row.revision == before[kind] + 1 and not result.is_pending(s, day, kind)
        nine = next(h for h in row.row.body["hours"] if h["window_start"].startswith(w.start.strftime("%Y-%m-%dT%H")))
        assert nine["job_state"] == "PENDING"


def test_sampled_hours_equal_the_one_hour_route_card(store, engine, monkeypatch) -> None:  # noqa: F811
    t, s, day = _fixture(store, engine)
    for kind in DAY_KINDS:
        _builder(engine).build(t, _site(t, s), day, kind)
    _consume_all(engine)
    monkeypatch.setenv(SERVED_KINDS_ENV, "")  # the one-hour route as served without stored rows: today's compose
    reader = MiniDepthRead(engine, link_rows_on)
    for kind, domain in pr.DAY_KINDS.items():
        row, _ = _stored(engine, t, s, day, kind)
        by_start = {h["window_start"]: h for h in row.row.body["hours"]}
        for h in SAMPLED:
            w = local_hour(day, h, w402.ZONE)
            card = reader.read(tenant_id=t, site_id=s, site_code=w402.CODE, domain=domain, lo=w.start, hi=w.end,
                               known_at=None)
            (window,) = card["currentness"]["windows"]
            stored = by_start[window["window_start"]]
            assert stored["head"] is not None and window["selection_id"] == stored["head"]["seq"]
            assert window["assessment_revision_id"] == stored["head"]["revision_id"]
            if domain == "fuel":
                assert card["cards"]["expected_use_l"] == stored["head"]["result"]["cards"]["expected_use_l"]
            else:
                assert card["cards"]["start_success_count"] == stored["head"]["result"]["cards"]["start_success_count"]
                assert [r["chain_id"] for r in card["rows"]] == [r["chain_id"] for r in stored["head"]["result"]["rows"]]
            if h == 12:  # the drill-in link names exactly this hour
                link = ds.hour_link(domain, w402.CODE, day, w402.ZONE)
                assert w.start.strftime("%Y-%m-%dT%H:%M:%SZ") in link.replace("%3A", ":")
