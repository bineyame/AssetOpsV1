"""ANY-2 AR-4 (D-ANY.5, D-ANY.6a): the estate Evidence page's mini-grid claim days from stored `evidence.claim` rows
equal today's compose, byte for byte, on a real `*_test` database.

The S4 `CaseRunner` F02 chain (two selected UTC days) is built into rows by the real builder over the real estate
Evidence reader; `/api/estate/evidence` is then read with the kill switch empty (compose) and with `evidence.claim`
served (rows), live and at historical cutoffs, and the JSON must be equal. Then a later assessment (F02 steps 4-5)
selects new window revisions: the stale rows are never served (read as today, counted) until they are rebuilt.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped otherwise.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_finding_store_postgres import SPEC
    from test_w301_estate_index_postgres import iso
    from test_w302_evidence_scope_snapshot_postgres import mini  # noqa: F401 - the F02 runner + Evidence client

    from assetops_backend.chain.adapters.file_chain_config import load_event_register
    from assetops_backend.chain.adapters.postgres_period_read_store import PostgresPeriodReadStore
    from assetops_backend.chain.composition import period_kind_versions
    from assetops_backend.chain.period_read import SERVED_KINDS_ENV, PeriodReadBuilder, PeriodReader
    from assetops_backend.chain.ports import SiteRef
    from assetops_backend.estate import period_rows as pr

F02 = next(c for c in SPEC["cases"] if c["case_id"] == "F02") if URL else None
F02_DAY = datetime(2026, 10, 8, tzinfo=timezone.utc)


def _consume_all(engine) -> None:  # noqa: F811
    with engine.begin() as c:
        c.execute(text("INSERT INTO event_consumption (consumer, event_id) SELECT 'snapshots', o.event_id "
                       "FROM event_outbox o WHERE NOT EXISTS (SELECT 1 FROM event_consumption x "
                       "WHERE x.consumer = 'snapshots' AND x.event_id = o.event_id)"))
        c.execute(text("DELETE FROM snapshot_dirty"))


def _site(engine, t, s) -> "SiteRef":  # noqa: F811
    with engine.connect() as c:
        code, tz = c.execute(text("SELECT site_code, timezone FROM site WHERE id = :s"), {"s": s}).one()
    return SiteRef(t, s, code, "MINIGRID", tz)


def _build(engine, read, site) -> list:  # noqa: F811
    builder = PeriodReadBuilder(PostgresPeriodReadStore(engine=engine), pr.kind_builders(read))
    return builder.build_range(site.tenant_id, site, F02_DAY.date() - timedelta(days=1),
                               F02_DAY.date() + timedelta(days=2), [pr.KIND_CLAIM])


def _both(monkeypatch, evidence, **params) -> tuple[str, str, int]:
    out, before = [], pr.row_misses()
    for value in ("", pr.KIND_CLAIM):
        monkeypatch.setenv(SERVED_KINDS_ENV, value)
        out.append(evidence.ok(**params))
    return json.dumps(out[0], sort_keys=True), json.dumps(out[1], sort_keys=True), pr.row_misses() - before


def test_claim_rows_equal_compose_live_historical_and_after_a_late_revision(mini, engine, monkeypatch) -> None:  # noqa: F811
    runner, evidence = mini
    before_any = runner.now
    for step in F02["steps"][:2]:  # deliver both sides of midnight, assess
        runner.step(step)
    cutoff = runner.now
    site = _site(engine, runner.tenant, runner.site)
    written = _build(engine, evidence.read, site)
    # a UTC claim day is touched by two Site-local days: the second build of the same day writes nothing new
    assert {w.row.local_day for w in written if w.written} >= {F02_DAY.date(), F02_DAY.date() + timedelta(days=1)}
    assert not any(w.written for w in _build(engine, evidence.read, site))  # unchanged: no new revision
    _consume_all(engine)
    store = PostgresPeriodReadStore(engine=engine)
    evidence.read.period_rows = pr.EvidenceRows(PeriodReader(store, load_event_register(), period_kind_versions()),
                                                store)
    window = {"from": iso(F02_DAY), "to": iso(F02_DAY + timedelta(days=2))}

    compose, rows, misses = _both(monkeypatch, evidence, **window)
    assert rows == compose and misses == 0  # live: every selected claim day served from its row
    mini_rows = [r for r in json.loads(rows)["rows"] if r["domain"] == "mini_grid"]
    assert [r["capability_key"] for r in mini_rows] == ["GENERATOR_SUPPORT@2026-10-08",
                                                        "GENERATOR_SUPPORT@2026-10-09"]
    assert all(r["selected_revision_ids"] for r in mini_rows)

    compose, rows, _ = _both(monkeypatch, evidence, **window, known_at=iso(cutoff))  # historical k
    assert rows == compose and json.loads(rows)["status"] == "HISTORICAL"
    compose, rows, _ = _both(monkeypatch, evidence, **window, known_at=iso(before_any))  # before revision 1
    assert rows == compose
    one = {"from": iso(F02_DAY + timedelta(days=1)), "to": iso(F02_DAY + timedelta(days=2))}
    compose, rows, misses = _both(monkeypatch, evidence, **one)  # a sub-range (the API refuses unaligned windows)
    assert rows == compose and misses == 0

    # A late assessment selects new window revisions: the stored rows are never served for them.
    for step in F02["steps"][3:5]:
        runner.step(step)
    compose, rows, misses = _both(monkeypatch, evidence, **window)
    assert rows == compose and misses == 2  # read as today, both days counted
    _build(engine, evidence.read, site)
    _consume_all(engine)
    compose, rows, misses = _both(monkeypatch, evidence, **window)
    assert rows == compose and misses == 0  # rebuilt: served from rows again
