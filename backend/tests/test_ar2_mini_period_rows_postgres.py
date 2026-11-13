"""ANY-1 AR-2 (D-ANY.5-6): the board's mini depth from `site_period_read` rows equals today's compose, on a real
`*_test` database.

The W4-02 fixture (five selected days) is built into rows by the real builder (`MiniDepthRead.build_period` through
`PeriodReadBuilder`); every board read (renewable 1 and 5 days, the noon hour of fuel, service and backup, live and
at an explicit cutoff) is then read with the kill switch empty (compose) and with every kind served (rows), and the
JSON must be equal byte for byte. A live job enqueued after the build reads PENDING_RECOMPUTE from the rows until the
rows are rebuilt and the event consumed; then the rows equal the compose again.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped otherwise.
"""
from __future__ import annotations

import json
import os
from datetime import timedelta

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import test_w402_reads_postgres as w402
    from assetops_backend.chain.adapters.file_chain_config import load_event_register
    from assetops_backend.chain.adapters.postgres_period_read_store import PostgresPeriodReadStore
    from assetops_backend.chain.composition import period_kind_versions
    from assetops_backend.chain.period_read import SERVED_KINDS_ENV, PeriodReadBuilder, PeriodReader
    from assetops_backend.chain.ports import SiteRef
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.mini_depth import period_rows as pr
    from assetops_backend.mini_depth import read as mread
    from assetops_backend.mini_depth.inputs import local_noon
    from assetops_backend.mini_depth.read import MiniDepthRead

ALL = ",".join(pr.KINDS) if URL else ""
#: The board's four kinds (SR-10a's whole-day kinds are built and pinned by `test_sr10_day_kinds_postgres.py`).
BOARD = tuple(k for k in pr.KINDS if k not in pr.DAY_KINDS) if URL else ()


def _consume_all(engine) -> None:
    with engine.begin() as c:
        c.execute(text("INSERT INTO event_consumption (consumer, event_id) SELECT 'snapshots', o.event_id "
                       "FROM event_outbox o WHERE NOT EXISTS (SELECT 1 FROM event_consumption x "
                       "WHERE x.consumer = 'snapshots' AND x.event_id = o.event_id)"))


def _build(engine, t, s, days) -> list:
    builder = PeriodReadBuilder(PostgresPeriodReadStore(engine=engine),
                                pr.kind_builders(MiniDepthRead(engine, link_rows_on)))
    site = SiteRef(t, s, w402.CODE, "MINIGRID", w402.ZONE)
    return [w for day in days for kind in BOARD for w in builder.build(t, site, day, kind)]


def _reader(engine) -> MiniDepthRead:
    st = PostgresPeriodReadStore(engine=engine)
    return MiniDepthRead(engine, link_rows_on,
                         period_rows=(PeriodReader(st, load_event_register(), period_kind_versions()), st))


def _both(monkeypatch, reader, t, s, domain, lo, hi, known_at=None) -> tuple[str, str, dict]:
    out = []
    for value in ("", ALL):
        monkeypatch.setenv(SERVED_KINDS_ENV, value)
        out.append(reader.read(tenant_id=t, site_id=s, site_code=w402.CODE, domain=domain, lo=lo, hi=hi,
                               known_at=known_at))
    return json.dumps(out[0], default=str), json.dumps(out[1], default=str), out[1]


def _now_clock(engine):
    from assetops_backend import read_scope

    with engine.connect() as c:
        at = read_scope.read_instant(c.execute(text("SELECT clock_timestamp()")).scalar_one())
    return lambda: at


def _cases():
    noon = local_noon(w402.DAYS[2], w402.ZONE)
    return [("renewable", w402._midnight(w402.DAYS[0]), w402._midnight(w402.DAYS[-1] + timedelta(days=1))),
            ("renewable", w402._midnight(w402.DAYS[3]), w402._midnight(w402.DAYS[4])),
            *[(d, noon.start, noon.end) for d in ("fuel", "service", "backup")]]


def test_board_rows_equal_compose_live_historical_and_after_a_late_job(store, engine, monkeypatch) -> None:  # noqa: F811
    installed, t, s = w402._setup(store, engine)
    w402._ingest(engine, installed)
    w402._reconcile(engine, w402.DAYS)
    written = _build(engine, t, s, w402.DAYS)
    assert len(written) == 4 * len(w402.DAYS) and all(w.written for w in written)
    assert not any(w.written for w in _build(engine, t, s, w402.DAYS))  # unchanged: no new revision
    _consume_all(engine)
    reader = _reader(engine)
    # A live read echoes its own clock_timestamp() as window.known_at; the two reads run apart, so one pinned read
    # clock (taken after the build) makes that echo equal and every other byte is compared as served.
    reader.test_read_clock_override = _now_clock(engine)
    for domain, lo, hi in _cases():
        compose, rows, body = _both(monkeypatch, reader, t, s, domain, lo, hi)
        assert rows == compose, (domain, lo)
        assert body["currentness"]["windows"] and any(w["selection_id"] for w in body["currentness"]["windows"])
    reader.test_read_clock_override = None
    with engine.connect() as c:
        k = c.execute(text("SELECT clock_timestamp()")).scalar_one()
    for domain, lo, hi in _cases():  # an explicit cutoff after the build: HISTORICAL in both
        compose, rows, body = _both(monkeypatch, reader, t, s, domain, lo, hi, known_at=k)
        assert rows == compose and body["currentness"]["state"] in ("HISTORICAL", "STALE_SOURCE", "UNKNOWN")

    # A live job on the service noon hour after the build: rows read PENDING_RECOMPUTE until rebuilt.
    noon = local_noon(w402.DAYS[2], w402.ZONE)
    with engine.begin() as c:
        c.execute(text("SELECT mini_enqueue_hour(:t, :s, 'mini_service', :lo, :hi, NULL, clock_timestamp())"),
                  {"t": t, "s": s, "lo": noon.start, "hi": noon.end})
    # The job has no outbox event (0029 `mini_enqueue_hour`): the rows path's live `_JOBS` check (D-ANY.6a) sees it.
    reader.test_read_clock_override = _now_clock(engine)
    fallback_before = mread.job_fallback_count()
    compose, rows, body = _both(monkeypatch, reader, t, s, "service", noon.start, noon.end)
    assert json.loads(compose)["currentness"]["state"] == "PENDING_RECOMPUTE"
    assert body["currentness"]["state"] == "PENDING_RECOMPUTE"  # never a silently CURRENT stored row
    assert rows == compose and mread.job_fallback_count() == fallback_before + 1
    reader.test_read_clock_override = None
    with engine.connect() as c:
        k_job = c.execute(text("SELECT clock_timestamp()")).scalar_one()
    compose, rows, body = _both(monkeypatch, reader, t, s, "service", noon.start, noon.end, known_at=k_job)
    assert rows == compose and body["currentness"]["state"] == "PENDING_RECOMPUTE"  # historical k as well
    _build(engine, t, s, [w402.DAYS[2]])
    _consume_all(engine)
    reader.test_read_clock_override = _now_clock(engine)
    compose, rows, body = _both(monkeypatch, reader, t, s, "service", noon.start, noon.end)
    assert rows == compose and body["currentness"]["job_state"] == "PENDING"
    assert body["pending_source_provenance"] is not None
    assert mread.job_fallback_count() == fallback_before + 2  # the rebuilt row holds the job: no fallback now


def test_rows_follow_a_job_moved_later_than_the_read(store, engine, monkeypatch) -> None:  # noqa: F811
    """D-ANY.6a: a row built while a PENDING job was visible must not keep reading PENDING_RECOMPUTE once that job's
    `available_at` is moved past the read (0029 `mini_enqueue_hour` coalescing; no event): the hour falls back."""
    installed, t, s = w402._setup(store, engine)
    w402._ingest(engine, installed)
    w402._reconcile(engine, w402.DAYS)
    noon = local_noon(w402.DAYS[2], w402.ZONE)
    p = {"t": t, "s": s, "lo": noon.start, "hi": noon.end}
    with engine.begin() as c:
        c.execute(text("SELECT mini_enqueue_hour(:t, :s, 'mini_service', :lo, :hi, NULL, clock_timestamp())"), p)
    _build(engine, t, s, [w402.DAYS[2]])
    _consume_all(engine)
    reader = _reader(engine)
    reader.test_read_clock_override = _now_clock(engine)
    compose, rows, body = _both(monkeypatch, reader, t, s, "service", noon.start, noon.end)
    assert rows == compose and body["currentness"]["job_state"] == "PENDING"  # the row holds the visible job
    with engine.begin() as c:  # the same PENDING job, moved one hour past now
        c.execute(text("SELECT mini_enqueue_hour(:t, :s, 'mini_service', :lo, :hi, NULL, "
                       "clock_timestamp() + interval '1 hour')"), p)
        moved = c.execute(text("SELECT count(*) FROM recompute_job WHERE tenant_id = :t AND site_id = :s "
                               "AND domain = 'mini_service' AND window_start = :lo AND status = 'PENDING' "
                               "AND available_at > clock_timestamp()"), p).scalar_one()
    assert moved == 1
    reader.test_read_clock_override = _now_clock(engine)
    before = mread.job_fallback_count()
    compose, rows, body = _both(monkeypatch, reader, t, s, "service", noon.start, noon.end)
    assert json.loads(compose)["currentness"]["state"] != "PENDING_RECOMPUTE"
    assert rows == compose and body["currentness"]["state"] != "PENDING_RECOMPUTE"
    assert mread.job_fallback_count() == before + 1


def test_rows_read_no_raw_reading(store, engine, monkeypatch) -> None:  # noqa: F811
    """The served path reads no raw reading, daylight hours, `_cutoff_sha` or link row: those raise here."""
    from assetops_backend.mini_depth import read as mread

    installed, t, s = w402._setup(store, engine)
    w402._ingest(engine, installed)
    w402._reconcile(engine, w402.DAYS)
    _build(engine, t, s, w402.DAYS)
    _consume_all(engine)

    def boom(*_a, **_k):
        raise AssertionError("raw read on the row path")
    for name in ("load_hour_inputs", "daylight_hours", "_cutoff_sha", "read_hour_rows", "_hour_ids"):
        monkeypatch.setattr(mread, name, boom)
    st = PostgresPeriodReadStore(engine=engine)
    reader = MiniDepthRead(engine, boom,
                           period_rows=(PeriodReader(st, load_event_register(), period_kind_versions()), st))
    monkeypatch.setenv(SERVED_KINDS_ENV, ALL)
    for domain, lo, hi in _cases():
        body = reader.read(tenant_id=t, site_id=s, site_code=w402.CODE, domain=domain, lo=lo, hi=hi, known_at=None)
        assert body["currentness"]["windows"]
