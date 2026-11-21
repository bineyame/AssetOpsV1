"""4d unit 3 (spec §4, §6 Postgres tests 1 to 3): the litre adapters and the composition on a real `*_test` database.

1. `PostgresAssessmentStore.dispatch_spans` on the S4 F06 world (`test_ar3_dispatch_day_rows_postgres.py`'s day).
2. `PostgresFuelBalanceStore.read_at` on K3's Kobo world (`test_k3_fuel_balance_postgres.py`'s `kobo` fixture).
3. `build_structure_read(url)` for a Site with no active assets; its `dispose`; a failing fourth builder.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (run under `tools/heavy-slot.sh --db`); skipped otherwise.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest

from test_s4_finding_store_postgres import SPEC, URL, CaseRunner  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

UTC = timezone.utc
F06 = next(c for c in SPEC["cases"] if c["case_id"] == "F06")
F06_DAY = datetime(2026, 10, 15, tzinfo=UTC)
LEAVES = ("necessary_l", "candidate_l", "unexplained_l")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_k3_fuel_balance_postgres import dip, kobo  # noqa: F401
    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401

    import pg_harness
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.chain.ports import SiteRef
    from assetops_backend.structure.composition import build_structure_read


def _db_now(engine) -> datetime:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@pytest.fixture()
def runner(store, engine):  # noqa: F811
    owned = CaseRunner(store, engine)
    yield owned
    pg_harness.dispose(owned.findings)


# --- 1. dispatch_spans ------------------------------------------------------------------------------------------------

def test_1_dispatch_spans_reads_the_current_selection(runner, engine) -> None:  # noqa: F811
    runner.step(F06["steps"][0])  # deliver: the recompute job is recorded
    runner.step(F06["steps"][1])  # assess: the job completes and selects the day's first run
    k = _db_now(engine)
    t, s = runner.tenant, runner.site
    lo, hi = F06_DAY - timedelta(hours=12), F06_DAY + timedelta(days=1, hours=6)
    assess = PostgresAssessmentStore(URL)
    try:
        days = assess.dispatch_spans(t, s, lo, hi, k)
        with engine.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
            composed = assess.select_dispatch_days_on(c, t, s, lo, hi, k)
        assert [d["day"] for d in days] == [d["day"] for d in composed] and len(days) == 3
        assert set(days[0]) == {"day", "available", "status", "selected", "accepted_reading_count", "run_id",
                                "spans"}
        current, started = 0, None
        for got, want in zip(days, composed):
            assert got["selected"] is (want["selection"] is not None)
            assert got["status"] == want["status"] and got["available"] == want["available"]
            assert got["accepted_reading_count"] == want["accepted_reading_count"]
            assert got["run_id"] == (None if want["selection"] is None else str(want["selection"]["run_id"]))
            if got["selected"] and got["status"] == "CURRENT":
                current += 1
                started = min(r["created_at"] for r in assess.run_detail(t, s, UUID(got["run_id"]))["revisions"])
                ids = {str(i) for i in want["assessment_revision_ids"]}
                detail = assess.run_detail(t, s, UUID(got["run_id"]))
                expected = tuple((_parse(seg["start"]), _parse(seg["end"]), seg["classification"])
                                 for rev in detail["revisions"] if str(rev["id"]) in ids and rev["scope"] != "WINDOW"
                                 for seg in rev["result"]["segments"])
                assert expected, "the selected run must have interval segments (non-vacuous)"
                assert got["spans"] == expected
                assert all(c in ("NECESSARY", "CANDIDATE_AVOIDABLE", "INDETERMINATE") for _, _, c in got["spans"])
            else:
                assert got["spans"] == ()
        assert current == 1, "the fixture must select exactly the F06 day (non-vacuous)"
        assert any(not d["selected"] and d["spans"] == () for d in days), "a day without a selection"
        early = assess.dispatch_spans(t, s, lo, hi, started - timedelta(microseconds=1))  # before the run
        assert [d["day"] for d in early] == [d["day"] for d in days]
        assert not any(d["selected"] for d in early) and all(d["spans"] == () for d in early)
    finally:
        assess.dispose()
        assert assess._engine is None


# --- 2. read_at -------------------------------------------------------------------------------------------------------

def test_2_read_at_is_one_read_only_transaction_at_known_at(kobo) -> None:  # noqa: F811
    tank, gen = kobo.assets["fuel-tank"], kobo.assets["generator"]
    lo, hi = datetime(2026, 9, 30, 21, tzinfo=UTC), datetime(2026, 10, 31, 21, tzinfo=UTC)
    kobo.work_clock.now = datetime(2026, 11, 1, 6, tzinfo=UTC)
    posted = kobo.post(dip(tank, "4d-pg-2-dip", datetime(2026, 10, 31, 22, tzinfo=UTC), "500"))
    known_at = datetime(2026, 11, 2, tzinfo=UTC)

    def work(tx):
        assets = tx.active_assets()
        records = tx.fuel_records(tank, lo - timedelta(hours=24), hi + timedelta(hours=24))
        sfc = tx.sfc_history(gen, lo, hi)
        with pytest.raises(DBAPIError, match="read-only transaction"):
            tx.c.execute(text("INSERT INTO tenant (id) VALUES (gen_random_uuid())"))
        return assets, records, sfc, tx.known_at

    assets, records, sfc, k = kobo.fb.read_at(kobo.t, kobo.s, known_at, work)
    assert sorted(a.asset_type for a in assets if a.asset_type in ("GENERATOR", "FUEL_TANK")) == [
        "FUEL_TANK", "GENERATOR"]
    assert [(r.kind, str(r.root_id), str(r.quantity_l)) for r in records] == [("TANK_DIP", posted["id"], "500")]
    assert len(sfc) >= 1 and all(v.value_l_per_kwh > 0 for v in sfc)
    assert k == known_at
    before, *_ = kobo.fb.read_at(kobo.t, kobo.s, datetime(2026, 11, 1, 5, tzinfo=UTC),
                                 lambda tx: (tx.fuel_records(tank, lo, hi + timedelta(hours=24)),))
    assert before == ()  # pinned: the dip was recorded after this known_at


# --- 3. the composition -----------------------------------------------------------------------------------------------

def test_3_a_site_with_no_assets_says_so_and_dispose_releases_both_stores(store, engine, monkeypatch) -> None:  # noqa: F811
    from assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store import PostgresFuelBalanceStore

    result = imported(store, "BARE-001")
    with engine.begin() as c:
        c.execute(text("UPDATE asset SET retired_at = now() WHERE site_id = :s"), {"s": result.site.id})
    site = SiteRef(result.tenant.id, result.site.id, "BARE-001", "MINIGRID", "Africa/Nairobi")
    disposed: list[str] = []
    for cls, name in ((PostgresAssessmentStore, "assessments"), (PostgresFuelBalanceStore, "fuel")):
        original = cls.dispose
        monkeypatch.setattr(cls, "dispose", lambda self, o=original, n=name: (disposed.append(n), o(self))[1])
    service = build_structure_read(URL)
    try:
        inputs = service.read.site_inputs(site, "2026-10", datetime(2026, 11, 20, 8, tzinfo=UTC))
        for leaf in LEAVES:
            lv = inputs.leaves[leaf]
            assert lv.value is None and lv.evidence == "NOT_AVAILABLE", leaf
            assert (lv.missing.cause, lv.missing.note) == ("NOT_RECEIVED", "GENERATOR_OR_TANK_NOT_DECLARED"), leaf
    finally:
        service.dispose()
    assert sorted(disposed) == ["assessments", "fuel"]


def test_3_a_failing_fourth_builder_disposes_the_three_before_it(monkeypatch) -> None:
    import assetops_backend.chain.composition as chain_composition
    import assetops_backend.commercial.composition as commercial_composition
    import assetops_backend.financials.composition as fin_composition
    import assetops_backend.structure.litres.composition as litre_composition

    log: list[str] = []
    monkeypatch.setattr(chain_composition, "build_snapshot_store",
                        lambda url: SimpleNamespace(dispose=lambda: log.append("snapshots")))
    monkeypatch.setattr(fin_composition, "build_window_price_selection",
                        lambda url: SimpleNamespace(select=None, dispose=lambda: log.append("prices")))
    monkeypatch.setattr(commercial_composition, "build_commercial_reads",
                        lambda url: SimpleNamespace(months=None, store=None, dispose=lambda: log.append("commercial")))

    def boom(url):
        raise RuntimeError("litre builder failed")

    monkeypatch.setattr(litre_composition, "build_litre_inputs", boom)
    with pytest.raises(RuntimeError, match="litre builder failed"):
        build_structure_read(URL)
    assert sorted(log) == ["commercial", "prices", "snapshots"]
