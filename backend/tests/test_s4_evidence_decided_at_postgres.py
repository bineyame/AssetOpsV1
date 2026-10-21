"""S4-07: an accepted decision's `decided_at` is DB time, so a scheduled DB-time cutoff either sees it or live work
remains for a later tick.

Packet `tasks/S4-07-evidence-decided-at.md` build items 2-3 and coordinator carries L-a/L-b. Every ingestion here
runs the **production** path: `PostgresEvidenceLedger(URL)` with no `test_decision_clock_override`, under
deliberately fast and slow `BatchIngestionService` app clocks that stamp only the receipt. Orders proved against
an overlapping PENDING job and the scheduled (DB-clock) worker:

- ingestion first: it holds the widened job's row lock; the tick's SKIP LOCKED lease passes it by;
- worker first: the lease transaction holds the job; ingestion, already stamped, waits on that row lock, re-checks
  it as LEASED and inserts a new PENDING job due at its decision instant (L-b);
- cutoff sampled, then ingestion commits a widening, then the lease runs at the earlier cutoff: the widened job's
  `available_at` is lifted to the decision instant, so that lease cannot consume it;
- a tick passes while a new job is still uncommitted.

The invariant: no committed accepted decision is excluded by a finished run with no live work. Restart cases replay
a crashed batch and run ticks without the override, including a chunk spanning two default windows, a
duplicate-only chunk and another Site. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone

import pytest

from test_s4_schedule_tick_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    import test_s4_finding_store_postgres as finding_cases
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import _release_connections  # noqa: F401
    from test_s4_schedule_tick_postgres import (  # noqa: F401
        DAY_A, FAST, block, deliver, kobo, make_tick, rows,
    )
    from test_s4_schedule_health_postgres import db_now, seam

    from assetops_backend.analytics.composition import build_dispatch_assessment_worker
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_service import BatchIngestionService, SimulatedCrash
    from assetops_backend.scheduling import stages
    from assetops_backend.scheduling.tick import TickLimits

UTC = timezone.utc
SKEWS = {"fast": timedelta(hours=2), "slow": -timedelta(hours=2)}


def pv(day: datetime, h0: int, h1: int) -> dict:
    """One device's readings (one batch per submit), so a batch's chunks are the only decision instants."""
    return {**block(day, h0, h1), "only": ["pv"], "stop_before": False, "stop_after": False}


def sealed(runner, *blocks) -> list[tuple[str, str]]:
    rules = finding_cases.SPEC["reading_rules"]
    raw = [(r, False) for b in blocks for r in finding_cases.block_rows(b, rules)]
    now_, _ = runner.seal(sorted(raw, key=lambda x: x[0][2]), "epoch-1")
    return now_


def body(runner, envelopes) -> bytes:
    (device,) = {d for d, _ in envelopes}
    return runner.kit.seal([t for _, t in envelopes], device_id=device).encode("utf-8")


def production(runner, payload: bytes, app_at: datetime, ledger=None, **options):
    """The production ingestion path: no decision override; the app clock stamps only the receipt."""
    ledger = ledger or PostgresEvidenceLedger(URL)
    assert ledger.test_decision_clock_override is None
    try:
        answer = BatchIngestionService(ledger, Clock(app_at), **options).submit(runner.kit.principal, payload)
    finally:
        ledger._engine and ledger._engine.dispose()
    assert answer.status in (200, 202), answer
    return answer.receipt


def batch(engine, site, external_id: str) -> dict:  # noqa: F811
    (b,) = rows(engine, "SELECT id, received_at, completed_at, status FROM ingestion_batch WHERE site_id = :s "
                        "AND external_batch_id = :x", s=site, x=external_id)
    b["dispositions"] = rows(engine, "SELECT ordinal, decision, accepted_evidence_id, decided_at FROM "
                                     "ingestion_disposition WHERE batch_id = :b ORDER BY ordinal", b=b["id"])
    return b


def jobs(engine, site) -> list[dict]:  # noqa: F811
    return rows(engine, "SELECT id, status, window_start, window_end, available_at, created_at FROM recompute_job "
                        "WHERE site_id = :s AND domain = 'dispatch' ORDER BY created_at, id", s=site)  # W4-02 q1 R2


def selected(engine, site, day: datetime) -> dict | None:  # noqa: F811
    """The window's latest selected run: its cutoff, job and the accepted IDs it cites."""
    found = rows(engine, "SELECT s.seq, s.run_id, r.knowledge_cutoff, r.job_id FROM analytic_run_selection s "
                         "JOIN analytic_run r ON r.id = s.run_id WHERE s.site_id = :s AND s.window_start = :w "
                         "ORDER BY s.seq DESC LIMIT 1", s=site, w=day)
    if not found:
        return None
    run = found[0]
    run["cites"] = {r["evidence_id"] for r in rows(engine, "SELECT evidence_id FROM analytic_run_evidence "
                                                            "WHERE run_id = :r", r=run["run_id"])}
    return run


def status(runner, day: datetime, env: str) -> str:
    return seam(runner.tenant, runner.site, day, env=env)["eligibility"]["status"]


def live(engine, site) -> list[dict]:  # noqa: F811
    return [j for j in jobs(engine, site) if j["status"] in ("PENDING", "LEASED")]


def assert_db_decided(b: dict, app_at: datetime, lo: datetime, hi: datetime) -> datetime:
    """One DB instant per chunk (single-chunk batch here), inside the DB-time bracket, never the app clock.
    The batch's receipt fields stay app-clock (packet L1); their order against the decision is not asserted (L-a)."""
    instants = {d["decided_at"] for d in b["dispositions"]}
    assert len(instants) == 1, instants
    (decided,) = instants
    assert lo <= decided <= hi and decided != app_at, (lo, decided, hi, app_at)
    assert b["received_at"] == app_at and b["completed_at"] == app_at
    return decided


def accepted_ids(b: dict) -> set:
    ids = {d["accepted_evidence_id"] for d in b["dispositions"] if d["decision"] == "ACCEPTED"}
    assert ids
    return ids


def settle(tick, runner, day: datetime, env: str, ids: set, engine, ticks: int = 4) -> dict:  # noqa: F811
    """Run ticks until the window reads CURRENT; while it does not, live work must exist or the window must be
    non-CURRENT (never a CURRENT read missing the decision). Returns the final selected run."""
    for _ in range(ticks):
        assert tick.tick().outcome == "COMPLETED"
        run = selected(engine, runner.site, day)
        if status(runner, day, env) == "CURRENT":
            assert run is not None and ids <= run["cites"], "CURRENT without the committed decision"
            return run
    raise AssertionError(f"window {day.date()} never reached CURRENT: {jobs(engine, runner.site)}")


def no_stale_gap(engine, runner, day: datetime, ids: set, env: str) -> None:  # noqa: F811
    """The invariant: a finished run that excludes a committed decision leaves live work (or a non-CURRENT read)."""
    run = selected(engine, runner.site, day)
    if run is not None and not ids <= run["cites"]:
        assert live(engine, runner.site), f"terminal gap: run {run['run_id']} excludes {ids} and no job is live"
        assert status(runner, day, env) != "CURRENT"


@pytest.mark.parametrize("skew", list(SKEWS))
class TestRaceOnTheProductionPath:
    def test_ingestion_first_holds_the_widened_job_so_the_tick_cannot_lease_it_until_commit(
            self, skew, kobo, engine) -> None:  # noqa: F811
        tick, _ = make_tick(TickLimits(**FAST))
        env = tick.environment
        deliver(kobo, block(DAY_A, 10, 12))  # job J (fixture-time decision)
        (job,) = live(engine, kobo.site)
        app_at = db_now(engine) + SKEWS[skew]
        payload = body(kobo, sealed(kobo, pv(DAY_A, 11, 13)))
        ledger = PostgresEvidenceLedger(URL)
        widened, go = threading.Event(), threading.Event()

        def hold(c, *a, **k):
            PostgresEvidenceLedger._coalesce_job(ledger, c, *a, **k)
            widened.set()
            assert go.wait(60)

        ledger._coalesce_job = hold
        out: list = []
        lo = db_now(engine)
        worker = threading.Thread(target=lambda: out.append(production(kobo, payload, app_at, ledger)))
        worker.start()
        assert widened.wait(30)
        watchdog = threading.Timer(45, go.set)  # a blocked tick fails its assertions instead of hanging
        watchdog.start()
        try:
            assert tick.tick().outcome == "COMPLETED"  # J is row-locked: SKIP LOCKED passes it by
            (still,) = live(engine, kobo.site)
            assert still["id"] == job["id"] and still["status"] == "PENDING"
            assert selected(engine, kobo.site, DAY_A) is None and status(kobo, DAY_A, env) != "CURRENT"
        finally:
            go.set()
            watchdog.cancel()
            worker.join(60)
        hi = db_now(engine)
        (receipt,) = out
        b = batch(engine, kobo.site, receipt.batch_id)
        decided = assert_db_decided(b, app_at, lo, hi)
        ids = accepted_ids(b)
        (widened_job,) = live(engine, kobo.site)
        assert widened_job["id"] == job["id"] and widened_job["created_at"] == job["created_at"]
        assert widened_job["available_at"] == decided  # lifted to the decision instant (S4-07)
        assert widened_job["window_end"] > job["window_end"]
        no_stale_gap(engine, kobo, DAY_A, ids, env)
        run = settle(tick, kobo, DAY_A, env, ids, engine)
        assert run["knowledge_cutoff"] >= decided and run["job_id"] == job["id"]

    def test_worker_first_holds_the_lease_and_the_stamped_ingestion_waits_then_inserts_a_new_job(
            self, skew, kobo, engine) -> None:  # noqa: F811
        """L-b: the decision instant precedes the job-lock wait; after the wait the job is LEASED, so ingestion
        inserts a new PENDING job due at its decision instant and the finished run's exclusion is not terminal."""
        tick, _ = make_tick(TickLimits(**FAST))
        env = tick.environment
        deliver(kobo, block(DAY_A, 10, 12))
        (job,) = live(engine, kobo.site)
        app_at = db_now(engine) + SKEWS[skew]
        payload = body(kobo, sealed(kobo, pv(DAY_A, 11, 13)))
        s3 = build_dispatch_assessment_worker(URL, clock=stages.db_clock(URL))
        store_ = s3.store
        leased, go = threading.Event(), threading.Event()
        original_run = store_._run

        def lease_job(*a, **k):
            def held(work, write=False):
                def w(c):
                    result = work(c)
                    leased.set()
                    assert go.wait(60)
                    return result
                return original_run(w, write=write)
            store_._run = held
            try:
                return type(store_).lease_job(store_, *a, **k)
            finally:
                store_._run = original_run

        store_.lease_job = lease_job
        outcomes: list = []
        runner = threading.Thread(target=lambda: outcomes.extend(s3.run_site(kobo.tenant, kobo.site, 1)))
        runner.start()
        assert leased.wait(30)
        out: list = []
        lo = db_now(engine)
        ingest = threading.Thread(target=lambda: out.append(production(kobo, payload, app_at)))
        ingest.start()
        waited = False
        for _ in range(100):  # the stamped chunk is waiting on J's row lock (the lease is uncommitted)
            waited = bool(rows(engine, "SELECT pid FROM pg_stat_activity WHERE wait_event_type = 'Lock' AND "
                                       "query LIKE '%FROM recompute_job WHERE site_id%FOR UPDATE%'"))
            if waited:
                break
            time.sleep(0.1)
        go.set()
        runner.join(60)
        ingest.join(60)
        assert waited, "ingestion never waited on the leased job's row lock"
        hi = db_now(engine)
        (receipt,) = out
        b = batch(engine, kobo.site, receipt.batch_id)
        decided = assert_db_decided(b, app_at, lo, hi)
        ids = accepted_ids(b)
        assert [o.status for o in outcomes] == ["DONE"]
        run = selected(engine, kobo.site, DAY_A)
        assert run["job_id"] == job["id"] and run["knowledge_cutoff"] < decided and not ids & run["cites"]
        (new,) = live(engine, kobo.site)  # the leased J was not widened: a new job carries the decision
        assert new["id"] != job["id"] and new["status"] == "PENDING"
        assert new["available_at"] == new["created_at"] == decided
        assert status(kobo, DAY_A, env) != "CURRENT"
        no_stale_gap(engine, kobo, DAY_A, ids, env)
        run = settle(tick, kobo, DAY_A, env, ids, engine)
        assert run["knowledge_cutoff"] >= decided and run["job_id"] == new["id"]

    def test_a_cutoff_sampled_before_a_committed_widening_cannot_lease_the_widened_job(
            self, skew, kobo, engine) -> None:  # noqa: F811
        """The scheduled worker takes its DB-time cutoff, then ingestion widens J and commits, then the lease runs
        at the earlier cutoff. J's `available_at` is now the decision instant, so that lease cannot take it."""
        tick, _ = make_tick(TickLimits(**FAST))
        env = tick.environment
        deliver(kobo, block(DAY_A, 10, 12))
        (job,) = live(engine, kobo.site)
        app_at = db_now(engine) + SKEWS[skew]
        payload = body(kobo, sealed(kobo, pv(DAY_A, 11, 13)))
        s3 = build_dispatch_assessment_worker(URL, clock=stages.db_clock(URL))
        out: list = []

        def lease_job(domain, now, *a, **k):
            if not out:
                out.append((now, production(kobo, payload, app_at)))
            return type(s3.store).lease_job(s3.store, domain, now, *a, **k)

        s3.store.lease_job = lease_job
        outcomes = s3.run_site(kobo.tenant, kobo.site, 5)
        ((cutoff, receipt),) = out
        b = batch(engine, kobo.site, receipt.batch_id)
        decided = assert_db_decided(b, app_at, cutoff, db_now(engine))
        ids = accepted_ids(b)
        assert outcomes == [], "a lease at a cutoff before the decision consumed the widened job"
        (still,) = live(engine, kobo.site)
        assert still["id"] == job["id"] and still["status"] == "PENDING" and still["available_at"] == decided
        assert selected(engine, kobo.site, DAY_A) is None and status(kobo, DAY_A, env) != "CURRENT"
        run = settle(tick, kobo, DAY_A, env, ids, engine)
        assert run["knowledge_cutoff"] >= decided and run["job_id"] == job["id"]

    def test_a_tick_passing_an_uncommitted_new_job_leaves_it_for_the_next_tick(
            self, skew, kobo, engine) -> None:  # noqa: F811
        tick, _ = make_tick(TickLimits(**FAST))
        env = tick.environment
        deliver(kobo, block(DAY_A, 10, 12))
        first = settle(tick, kobo, DAY_A, env, set(), engine)
        assert live(engine, kobo.site) == []
        app_at = db_now(engine) + SKEWS[skew]
        payload = body(kobo, sealed(kobo, pv(DAY_A, 13, 14)))
        ledger = PostgresEvidenceLedger(URL)
        inserted, go = threading.Event(), threading.Event()

        def hold(c, *a, **k):
            PostgresEvidenceLedger._coalesce_job(ledger, c, *a, **k)
            inserted.set()
            assert go.wait(60)

        ledger._coalesce_job = hold
        out: list = []
        lo = db_now(engine)
        worker = threading.Thread(target=lambda: out.append(production(kobo, payload, app_at, ledger)))
        worker.start()
        assert inserted.wait(30)
        watchdog = threading.Timer(45, go.set)
        watchdog.start()
        try:
            assert tick.tick().outcome == "COMPLETED"  # the new job is invisible until commit
            assert live(engine, kobo.site) == [] and selected(engine, kobo.site, DAY_A)["seq"] == first["seq"]
        finally:
            go.set()
            watchdog.cancel()
            worker.join(60)
        (receipt,) = out
        b = batch(engine, kobo.site, receipt.batch_id)
        decided = assert_db_decided(b, app_at, lo, db_now(engine))
        ids = accepted_ids(b)
        (new,) = live(engine, kobo.site)
        assert new["available_at"] == new["created_at"] == decided
        assert status(kobo, DAY_A, env) != "CURRENT"
        no_stale_gap(engine, kobo, DAY_A, ids, env)
        run = settle(tick, kobo, DAY_A, env, ids, engine)
        assert run["knowledge_cutoff"] >= decided and run["job_id"] == new["id"]


class TestRestartOnTheProductionPath:
    def test_a_crash_between_chunks_replays_to_one_record_per_message_and_current_across_two_windows(
            self, kobo, engine) -> None:  # noqa: F811
        """The first chunk spans two default (day) windows and commits; the process dies before the next tick; the
        same bytes are replayed and ticks run: one accepted record per message, the committed chunk keeps its
        dispositions, the job is not lost and neither window reads CURRENT before it cites the decisions. A later
        duplicate-only chunk decides DUPLICATE and enqueues nothing."""
        tick, _ = make_tick(TickLimits(**FAST))
        env = tick.environment
        day_b = DAY_A + timedelta(days=1)
        envs = sealed(kobo, pv(DAY_A, 23, 25))  # 23:00 to 01:00 next day
        payload = body(kobo, envs)
        app_at = db_now(engine) + SKEWS["fast"]
        size = len(envs) * 2 // 3  # chunk 1 crosses midnight
        with pytest.raises(SimulatedCrash):
            production(kobo, payload, app_at, chunk_size=size, crash_after_chunks=1)
        (b0,) = rows(engine, "SELECT external_batch_id FROM ingestion_batch WHERE site_id = :s AND status = "
                             "'IN_PROGRESS'", s=kobo.site)
        partial = batch(engine, kobo.site, b0["external_batch_id"])
        assert len(partial["dispositions"]) == size and partial["completed_at"] is None
        assert live(engine, kobo.site), "the committed chunk left no job"
        for day in (DAY_A, day_b):
            assert selected(engine, kobo.site, day) is None and status(kobo, day, env) != "CURRENT"
        replayed = production(kobo, payload, app_at + timedelta(minutes=5), chunk_size=size)
        assert replayed.status == "COMPLETED" and replayed.batch_id == b0["external_batch_id"]
        done = batch(engine, kobo.site, b0["external_batch_id"])
        assert done["dispositions"][:size] == partial["dispositions"]  # the retry kept its stored decisions
        assert len({d["decided_at"] for d in done["dispositions"]}) == 2  # one DB instant per chunk
        ids = accepted_ids(done)
        assert rows(engine, "SELECT count(*) AS n FROM accepted_evidence WHERE batch_id = :b",
                    b=done["id"])[0]["n"] == len(envs) == len(ids)
        before = jobs(engine, kobo.site)
        dup = production(kobo, body(kobo, envs[:2]), app_at)
        assert {d.decision for d in dup.dispositions} == {"DUPLICATE"}
        assert jobs(engine, kobo.site) == before
        last = max(d["decided_at"] for d in done["dispositions"])
        settle(tick, kobo, DAY_A, env, set(), engine)
        cited = set()
        for day in (DAY_A, day_b):
            run = selected(engine, kobo.site, day)
            assert status(kobo, day, env) == "CURRENT" and run["knowledge_cutoff"] >= last
            cited |= run["cites"]
        assert ids <= cited and live(engine, kobo.site) == []

    def test_another_sites_crashed_batch_is_isolated_and_settles_on_its_own_job(
            self, kobo, store, engine, monkeypatch) -> None:  # noqa: F811
        """Site B's crashed, replayed batch takes its own DB instant and job; Site A's settled window, job list and
        selection are untouched, and the tick settles B without the override."""
        from test_s1_bindings_postgres import FIXTURE, NOW, imported
        from test_s2_evidence_ledger_postgres import enable

        from assetops_backend.sites.binding_conversion import convert
        from assetops_backend.sites.binding_service import BindingService

        tick, _ = make_tick(TickLimits(**FAST))
        env = tick.environment
        deliver(kobo, block(DAY_A, 10, 12))
        settle(tick, kobo, DAY_A, env, set(), engine)
        a_jobs, a_run = jobs(engine, kobo.site), selected(engine, kobo.site, DAY_A)

        def site_b(store_, engine_):
            result = imported(store_, code="KOBO-002")
            outcome = convert(store_, BindingService(store_, Clock(NOW - timedelta(hours=1))), result.tenant,
                              result.site, {**FIXTURE, "site_code": "KOBO-002"})
            enable(engine_, result.site.id)
            return result, outcome

        monkeypatch.setattr(finding_cases, "converted_enabled", site_b)
        monkeypatch.setattr(finding_cases, "DEMO", {**finding_cases.DEMO, "site_code": "KOBO-002"})
        b_runner = finding_cases.CaseRunner(store, engine)
        try:
            assert b_runner.site != kobo.site
            envs = sealed(b_runner, pv(DAY_A, 10, 12))
            payload = body(b_runner, envs)
            app_at = db_now(engine) + SKEWS["slow"]
            with pytest.raises(SimulatedCrash):
                production(b_runner, payload, app_at, chunk_size=len(envs) // 2, crash_after_chunks=1)
            assert live(engine, b_runner.site) and live(engine, kobo.site) == []
            receipt = production(b_runner, payload, app_at, chunk_size=len(envs) // 2)
            done = batch(engine, b_runner.site, receipt.batch_id)
            ids = accepted_ids(done)
            assert status(b_runner, DAY_A, env) != "CURRENT"
            run = settle(tick, b_runner, DAY_A, env, ids, engine)
            assert run["knowledge_cutoff"] >= max(d["decided_at"] for d in done["dispositions"])
            assert jobs(engine, kobo.site) == a_jobs and selected(engine, kobo.site, DAY_A) == a_run
            assert not ids & a_run["cites"]
        finally:
            b_runner.findings._engine and b_runner.findings._engine.dispose()
