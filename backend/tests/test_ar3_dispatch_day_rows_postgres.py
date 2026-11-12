"""ANY-2 AR-3 (D-ANY.5-6): the Portfolio's S3 dispatch days from `dispatch.day` rows equal today's compose, on a real
`*_test` database.

The S4 F06 fixture (a delivered then assessed day, later re-selected) is built into rows by the real builder
(`DispatchDayKindBuilder` over `PostgresAssessmentStore.dispatch_day_now` through `PeriodReadBuilder`). Then:
(a) the live rows read by `DispatchDayRows` equal `select_dispatch_days_on` for the same days (and `dispatch_day_now`
equals it too); (b) a cutoff between two builds serves the first build, a cutoff before any build reads the day
absent (unchecked); (c) an event not yet consumed reads PENDING from the rows until the drain and the rebuild, then
the rows equal the compose again; (d) with the kill switch empty the provider answers None (today's compose).

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped otherwise.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from test_s4_finding_store_postgres import SPEC, URL, CaseRunner  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

F06 = next(c for c in SPEC["cases"] if c["case_id"] == "F06")
F06_DAY = datetime(2026, 10, 15, tzinfo=timezone.utc)

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.chain import dispatch_day_rows as ddr
    from assetops_backend.estate import coverage
    from assetops_backend.chain.adapters.file_chain_config import load_event_register
    from assetops_backend.chain.adapters.postgres_event_store import PostgresEventStore
    from assetops_backend.chain.adapters.postgres_period_read_store import PostgresPeriodReadStore
    from assetops_backend.chain.composition import period_kind_versions
    from assetops_backend.chain.period_read import SERVED_KINDS_ENV, PeriodReadBuilder, PeriodReader


@pytest.fixture()
def runner(store, engine):  # noqa: F811
    owned = CaseRunner(store, engine)
    yield owned
    pg_harness.dispose(owned.findings)


def _drain(engine) -> None:
    with engine.begin() as c:
        c.execute(text("INSERT INTO event_consumption (consumer, event_id) SELECT 'snapshots', o.event_id "
                       "FROM event_outbox o WHERE NOT EXISTS (SELECT 1 FROM event_consumption x "
                       "WHERE x.consumer = 'snapshots' AND x.event_id = o.event_id)"))


def _db_now(engine) -> datetime:
    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


class Rig:
    def __init__(self, runner, monkeypatch) -> None:
        self.runner, self.t, self.s, self.engine = runner, runner.tenant, runner.site, runner.engine
        self.assess = PostgresAssessmentStore(URL)
        self.events = PostgresEventStore(URL)
        self.rows = PostgresPeriodReadStore(URL)
        self.site = self.events.site(self.t, self.s)
        assert self.site is not None
        self.builder = PeriodReadBuilder(self.rows, {ddr.KIND: ddr.DispatchDayKindBuilder(self.assess.dispatch_day_now)})
        self.provider = ddr.DispatchDayRows(
            PeriodReader(self.rows, load_event_register(), period_kind_versions()), self.events.site)
        self.lo, self.hi = F06_DAY - timedelta(hours=12), F06_DAY + timedelta(days=1, hours=6)
        self.days = ddr.dispatch_spans(self.lo, self.hi)
        monkeypatch.setenv(SERVED_KINDS_ENV, ddr.KIND)
        self.mp = monkeypatch

    def build(self) -> None:
        for d in self.days:
            self.builder.build(self.t, self.site, d, ddr.KIND)

    def compose(self) -> list[dict]:
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
            with c.begin():
                k = c.execute(text("SELECT clock_timestamp()")).scalar_one()
                return self.assess.select_dispatch_days_on(c, self.t, self.s, self.lo, self.hi, k)

    def serve(self, k=None, explicit=False) -> list[dict]:
        k = k or _db_now(self.engine)
        self.mp.setattr(coverage, "dispatch_rows_provider", self.provider)
        # D-ANY.10: absent days are composed by `coverage.dispatch_days` at the same k (the real compose, not a double)
        days = coverage.dispatch_days(_ComposeSnap(self, explicit), self.t, self.s, self.lo, self.hi, k)
        assert days is not None
        return days

    def dispose(self) -> None:
        for p in (self.assess, self.events, self.rows):
            pg_harness.dispose(p)


class _ComposeSnap:
    """The slice of the estate snapshot `coverage.dispatch_days` uses, composing on the real store at k."""

    continuation = False

    def __init__(self, rig, historical: bool) -> None:
        self._rig, self.basis_historical = rig, historical

    def dispatch_days(self, t, s, from_, to, k):
        with self._rig.engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
            with c.begin():
                return self._rig.assess.select_dispatch_days_on(c, t, s, from_, to, k)


def _same(a: list[dict], b: list[dict]) -> bool:
    strip = lambda ds: [ddr.encode({k: v for k, v in d.items() if k != "known_at"}) for d in ds]  # noqa: E731
    return strip(a) == strip(b)


@pytest.fixture()
def rig(runner, monkeypatch):
    r = Rig(runner, monkeypatch)
    yield r
    r.dispose()


def test_rows_equal_compose_historical_cutoffs_and_pending(rig) -> None:
    runner = rig.runner
    runner.step(F06["steps"][0])  # deliver: the recompute job is recorded
    runner.step(F06["steps"][1])  # assess: the job completes and selects the day's first run
    _drain(rig.engine)
    before_any_build = _db_now(rig.engine)
    rig.build()
    first_built = _db_now(rig.engine)

    # (a) live rows == compose, and dispatch_day_now == compose for the selected day
    composed = rig.compose()
    assert any(d["status"] and d["selection"] for d in composed), "the fixture must select a day (non-vacuous)"
    assert _same(rig.serve(), composed)
    assert _same([rig.assess.dispatch_day_now(rig.t, rig.s, d) for d in rig.days], composed)

    # (b) D-ANY.10: a cutoff after the revision but before any build has no row, so it reads today's compose of the
    # day at that k (the selection), not "nothing known"; the row bodies stay as built after a later revision
    absent = rig.serve(before_any_build, explicit=True)
    assert any(d["selection"] for d in absent), "k between the revision and its row's build must read the selection"
    assert all(d["status_reasons"] != [ddr.ABSENT_REASON] for d in absent)
    assert _same(absent, composed)
    for step in F06["steps"][3:5]:  # release, assess: a later selection of the same day
        runner.step(step)
    _drain(rig.engine)
    rig.build()
    revised = rig.compose()
    assert not _same(revised, composed), "the second revision must change the day (non-vacuous)"
    assert _same(rig.serve(), revised)
    assert _same(rig.serve(first_built, explicit=True), composed)  # k between the builds serves the first build

    # (c) a late event is PENDING from the rows until the drain and the rebuild; then equal again
    for step in F06["steps"][5:]:  # later steps: events not yet consumed, rows not yet rebuilt
        runner.step(step)
    pending_day = rig.serve()
    assert any(j.get("status") == ddr.PENDING_JOB["status"] for d in pending_day for j in d["jobs"]),         "an unconsumed event must read PENDING from the rows"
    _drain(rig.engine)
    rig.build()
    assert _same(rig.serve(), rig.compose())


def test_kill_switch_empty_answers_none(rig, monkeypatch) -> None:
    monkeypatch.setenv(SERVED_KINDS_ENV, "")
    assert rig.provider(rig.t, rig.s, rig.lo, rig.hi, _db_now(rig.engine), False) is None
