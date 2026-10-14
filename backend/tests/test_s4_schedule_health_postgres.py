"""S4-02d phase 2: schedule health and alarms, the S5 upstream currentness seam, DB time (I3) and the
overlapping-ingestion race (I4); plus the phase-1 review carries F2 (Site back-off) and F3 (lost Site claim).

Packet `tasks/S4-02d-analytic-finding-worker-schedule.md` phase 2 and `.agent/S4-02d-phase-1-review.md`.
Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from test_s4_schedule_tick_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    import test_s4_finding_store_postgres as finding_cases
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import POWER_DAY, _release_connections  # noqa: F401
    from test_s4_evidence_consequence_work_postgres import body, evidence_work, power, site, submit  # noqa: F401
    from test_s4_schedule_tick_postgres import (  # noqa: F401
        DAY_A, DAY_B, FAST, InProcessRunner, block, by_site, deliver, import_site, jobs, kobo, make_tick, rows,
    )

    from assetops_backend import recompute_consequences
    from assetops_backend.analytics import assess_dispatch, assessment_worker, finding_service
    from assetops_backend.analytics.composition import build_postgres_assessment_store
    from assetops_backend.financials import recompute
    from assetops_backend.financials.composition import CONSEQUENCE_UNAVAILABLE
    from assetops_backend.financials.recompute import ConsequenceRecomputeWorker
    from assetops_backend.scheduling.composition import build_schedule_health, build_upstream_currentness
    from assetops_backend.scheduling.health import HealthThresholds
    from assetops_backend.scheduling.tick import StageRunner, TickLimits

UTC = timezone.utc
NORMAL = HealthThresholds() if URL else None
SKEW = timedelta(hours=3)


def seam(tenant, site, day: datetime, th=None, env="default"):
    read = build_upstream_currentness(URL, th or NORMAL)
    try:
        return read.window(tenant, site, day, day + timedelta(days=1), env)
    finally:
        read.dispose()


def health(env, th=None) -> dict:
    report = build_schedule_health(URL, th or NORMAL)
    try:
        return report.report(env)
    finally:
        report.dispose()


def site_of(report, site) -> dict:
    return next(s for s in report["sites"] if s["site_id"] == str(site))


def codes(alarms) -> set:
    return {a["code"] for a in alarms}


def db_now(engine):  # noqa: F811
    return rows(engine, "SELECT clock_timestamp() AS n")[0]["n"]


class TestPhase1ReviewCarries:
    def test_f2_a_site_inside_its_backoff_runs_no_stage_and_the_cursor_still_advances(
            self, kobo, engine) -> None:  # noqa: F811
        deliver(kobo, block(DAY_A, 8, 9))
        lim = TickLimits(**{**FAST, "backoff_base_seconds": 60})
        runner = InProcessRunner(lim, results={"s3": [{"code": "FAILED", "error": "injected S3 failure"}]})
        tick, _ = make_tick(lim, runner)
        first = by_site(tick.tick())[str(kobo.site)]
        assert first.result == "FAILED" and first.failure[:2] == ("S3", "FAILED")
        head = tick.store.site_head(kobo.tenant, kobo.site)
        assert head["retry_due_at"] > db_now(engine) + timedelta(seconds=30)
        runner.calls.clear()
        report = tick.tick()
        second = by_site(report)[str(kobo.site)]
        assert report.outcome == "COMPLETED" and second.result == "RETRY_DUE" and second.stages == {}
        assert runner.calls == [("discover", None)]  # no s3/s4/consequence for the backed-off Site
        assert tick.store.cursor(tick.environment) == (kobo.tenant, kobo.site)
        assert site_of(health(tick.environment), kobo.site)["state"] == "RETRY_DUE"

    def test_f3_a_lost_site_claim_stops_the_site_before_its_next_stage(self, kobo, engine) -> None:  # noqa: F811
        deliver(kobo, block(DAY_A, 8, 9))
        lim = TickLimits(**FAST)
        thief = uuid4()

        def steal(args) -> None:  # the lease expires mid-stage and another host takes the Site claim
            with engine.begin() as c:
                c.execute(text("UPDATE schedule_site_head SET lease_until = clock_timestamp() - interval '1 second' "
                               "WHERE site_id = :s"), {"s": kobo.site})
            assert tick.store.claim_site(kobo.tenant, kobo.site, thief, "host-x", 120)["claimed"]

        runner = InProcessRunner(lim, before={"s3": steal})
        tick, _ = make_tick(lim, runner)
        r = by_site(tick.tick())[str(kobo.site)]
        assert r.result == "CLAIM_LOST" and r.failure[:2] == ("S4", "CLAIM_LOST")
        assert [c for c, _ in runner.calls] == ["discover", "s3"]  # no S4 and no drain after the loss
        head = tick.store.site_head(kobo.tenant, kobo.site)
        assert head["claim_owner"] == "host-x" and head["claim_token"] == thief

    def test_requeue_without_a_job_id_is_a_usage_error(self, capsys) -> None:
        with pytest.raises(SystemExit) as exit_:
            assess_dispatch.main(["requeue", "--tenant-id", str(uuid4()), "--site-id", str(uuid4())])
        assert exit_.value.code == 2 and "--job-id" in capsys.readouterr().err


class TestHealthAndSeam:
    def test_pending_current_stale_after_reload_idle_heartbeat_and_a_stopped_timer(
            self, kobo, engine) -> None:  # noqa: F811
        tick, _ = make_tick(TickLimits(**FAST))
        env = tick.environment
        deliver(kobo, block(DAY_A, 8, 9))
        first = seam(kobo.tenant, kobo.site, DAY_A, env=env)
        assert first["eligibility"]["status"] == "PENDING" and first["eligibility"]["stage"] == "S3"
        assert "LIVE_JOB" in first["eligibility"]["reasons"] and "SITE_NOT_OBSERVED" in first["eligibility"]["reasons"]
        assert health(env)["tick"]["state"] == "STOPPED"  # never observed: no completed tick yet

        assert tick.tick().outcome == "COMPLETED"
        beat = tick.store.tick_head(env)["heartbeat_at"]
        current = seam(kobo.tenant, kobo.site, DAY_A, env=env)
        assert current["eligibility"] == {"status": "CURRENT", "stage": None, "reasons": [], "errors": []}, \
            current["eligibility"]
        (day,) = current["days"]
        assert day["s3_status"] == "CURRENT" and day["watermark"]["selection_seq"] is not None
        assert day["run_id"] and day["window_assessment_revision_id"]
        assert all(m["matched"] for m in current["match"] if m["window_selection_seq"] is not None)
        assert current["findings"] and all(f["consequence_state"] == "CURRENT" for f in current["findings"])
        assert current["s3_jobs"] == [] and current["consequence_work"] == []
        assert abs((current["db_now"] - db_now(engine)).total_seconds()) < 30
        # After reload: a fresh composition (new engines) reads the same.
        again = seam(kobo.tenant, kobo.site, DAY_A, env=env)
        assert again["eligibility"]["status"] == "CURRENT" and again["days"][0]["watermark"] == day["watermark"]
        h = health(env)
        assert h["tick"]["state"] == "IDLE" and site_of(h, kobo.site)["state"] == "IDLE", h
        assert h["state"] == "IDLE" and h["alarm_count"] == 0

        # Idle ticks advance the heartbeat.
        assert tick.tick().outcome == "COMPLETED"
        assert tick.store.tick_head(env)["heartbeat_at"] > beat

        # New evidence: an older result under an advanced basis is STALE_PROJECTION, never queue-empty CURRENT.
        deliver(kobo, block(DAY_A, 12, 13), decided="2026-10-12T09:00:00Z")
        stale = seam(kobo.tenant, kobo.site, DAY_A, env=env)
        assert stale["eligibility"]["status"] == "STALE_PROJECTION" and stale["eligibility"]["stage"] == "S3"
        assert site_of(health(env), kobo.site)["state"] == "BACKLOG"
        assert tick.tick().outcome == "COMPLETED"
        assert seam(kobo.tenant, kobo.site, DAY_A, env=env)["eligibility"]["status"] == "CURRENT"

        # The timer stops: past the threshold (DB time) everything reads STOPPED and the seam blocks CURRENT with
        # empty queues; a completed tick recovers.
        tight = HealthThresholds(stop_after_seconds=1, site_stop_after_seconds=1)
        time.sleep(1.5)
        h = health(env, tight)
        assert h["state"] == "STOPPED" and "HEARTBEAT_STALE" in codes(h["tick"]["alarms"])
        assert site_of(h, kobo.site)["state"] == "STOPPED"
        blocked = seam(kobo.tenant, kobo.site, DAY_A, tight, env=env)
        assert blocked["s3_jobs"] == [] and blocked["consequence_work"] == []
        assert blocked["eligibility"]["status"] == "STALE_PROJECTION"
        assert blocked["eligibility"]["stage"] == "SCHEDULE" and "SCHEDULE_STOPPED" in blocked["eligibility"]["reasons"]
        # Another environment's live heartbeat does not observe this Site's schedule.
        assert seam(kobo.tenant, kobo.site, DAY_A, env="other-env")["eligibility"]["status"] != "CURRENT"
        assert tick.tick().outcome == "COMPLETED"
        assert seam(kobo.tenant, kobo.site, DAY_A, tight, env=env)["eligibility"]["status"] == "CURRENT"

    def test_fence_moved_streak_terminal_s3_failure_requeue_and_recovery(
            self, kobo, engine, monkeypatch) -> None:  # noqa: F811
        tick, _ = make_tick(TickLimits(**FAST))
        env = tick.environment
        deliver(kobo, block(DAY_A, 8, 9))
        assert tick.tick().outcome == "COMPLETED"

        # A failing matcher: typed FENCE_MOVED three times running alarms and blocks CURRENT.
        moved = {"code": "FENCE_MOVED", "error": "FindingFenceMoved: re-plan"}
        tick.runner = InProcessRunner(tick.limits, results={"s4": [dict(moved) for _ in range(3)]})
        for _ in range(3):
            assert by_site(tick.tick())[str(kobo.site)].stages["s4"]["code"] == "FENCE_MOVED"
        s = site_of(health(env), kobo.site)
        assert s["state"] == "FAILED" and {"FENCE_MOVED_STREAK", "SITE_FAILING"} <= codes(s["alarms"])
        e = seam(kobo.tenant, kobo.site, DAY_A, env=env)["eligibility"]
        assert e["status"] == "STALE_PROJECTION" and "FENCE_MOVED_STREAK" in e["reasons"]
        assert {"stage": "S4", "code": "FENCE_MOVED", "error": "FindingFenceMoved: re-plan",
                "source": "SCHEDULE"} in e["errors"]
        r = by_site(tick.tick())[str(kobo.site)]  # the real stage: unchanged fence, the streak clears
        assert r.stages["s4"]["code"] == "SKIPPED_UNCHANGED_FENCE" and r.result == "COMPLETED"
        assert site_of(health(env), kobo.site)["state"] == "IDLE"
        assert seam(kobo.tenant, kobo.site, DAY_A, env=env)["eligibility"]["status"] == "CURRENT"

        # A new selection whose match has not run (the S4 stage timed out once): not CURRENT, stage S4.
        deliver(kobo, block(DAY_A, 12, 13), decided="2026-10-12T07:00:00Z")
        tick.runner = InProcessRunner(tick.limits, results={"s4": [{"code": "TIMEOUT", "error": "lock timeout"}]})
        assert by_site(tick.tick())[str(kobo.site)].stages["s4"]["code"] == "TIMEOUT"
        e = seam(kobo.tenant, kobo.site, DAY_A, env=env)["eligibility"]
        assert e["status"] == "STALE_PROJECTION" and e["stage"] == "S4" and "MATCH_PENDING" in e["reasons"], e
        assert site_of(health(env), kobo.site)["s4"]["backlog"] is True
        tick.runner = InProcessRunner(tick.limits)
        assert by_site(tick.tick())[str(kobo.site)].stages["s4"]["code"] == "MATCHED"
        assert seam(kobo.tenant, kobo.site, DAY_A, env=env)["eligibility"]["status"] == "CURRENT"

        # Terminal S3 failure on a first build (no usable prior result): FAILED, typed, with the job ID.
        deliver(kobo, block(DAY_B, 8, 9), decided="2026-10-12T08:00:00Z")
        (job,) = [j for j in jobs(engine, kobo.site) if j["status"] == "PENDING"]
        with engine.begin() as c:
            c.execute(text("UPDATE recompute_job SET status = 'FAILED', attempts = 3, last_error = 'injected' "
                           "WHERE id = :j"), {"j": job["id"]})
        failed = seam(kobo.tenant, kobo.site, DAY_B, env=env)
        assert failed["eligibility"]["status"] == "FAILED" and failed["eligibility"]["stage"] == "S3"
        assert {"stage": "S3", "code": "RECOMPUTE_FAILED", "job_id": str(job["id"]),
                "error": "injected"} in failed["eligibility"]["errors"]
        tick.tick()
        s = site_of(health(env), kobo.site)
        assert s["state"] == "FAILED"
        (alarm,) = [a for a in s["alarms"] if a["code"] == "S3_JOB_FAILED"]
        assert alarm["job_id"] == str(job["id"]) and alarm["last_error"] == "injected"
        assert "requeue" in alarm["recovery"]
        # Day A stays CURRENT, but its bracket does not reach day B (6 h), so its eligibility is unaffected.
        assert seam(kobo.tenant, kobo.site, DAY_A, env=env)["eligibility"]["status"] == "CURRENT"

        monkeypatch.setenv("DATABASE_URL", URL)
        assert assess_dispatch.main(["requeue", "--tenant-id", str(kobo.tenant), "--site-id", str(kobo.site),
                                     "--job-id", str(job["id"])]) == 0
        assert tick.tick().outcome == "COMPLETED"
        assert site_of(health(env), kobo.site)["state"] == "IDLE"
        assert seam(kobo.tenant, kobo.site, DAY_B, env=env)["eligibility"]["status"] == "CURRENT"

        # A Site that leaves the active set with an unmatched selection keeps its S4 backlog in the report.
        deliver(kobo, block(DAY_A, 16, 17), decided="2026-10-12T10:00:00Z")
        tick.runner = InProcessRunner(tick.limits, results={"s4": [{"code": "TIMEOUT", "error": "lock timeout"}]})
        tick.tick()
        with engine.begin() as c:
            c.execute(text("UPDATE site SET lifecycle = 'DECOMMISSIONED' WHERE id = :s"), {"s": kobo.site})
        tick.runner = InProcessRunner(tick.limits)
        assert str(kobo.site) not in by_site(tick.tick())  # no live S3 or consequence work keeps it selected
        s = site_of(health(env), kobo.site)
        assert s["active"] is False and s["s4"]["backlog"] is True
        assert "S4_BACKLOG_OUTSIDE_ACTIVE_SET" in codes(s["alarms"]) and s["state"] == "BACKLOG"

    def test_repeated_claim_skips_and_a_stale_claim_alarm_then_recovery(self, kobo, engine) -> None:  # noqa: F811
        tick, _ = make_tick(TickLimits(**FAST))
        env = tick.environment
        deliver(kobo, block(DAY_A, 8, 9))
        assert tick.tick().outcome == "COMPLETED"
        holder = uuid4()
        assert tick.store.claim_site(kobo.tenant, kobo.site, holder, "hung-host", 3600)["claimed"]
        assert site_of(health(env), kobo.site)["state"] == "RUNNING"
        for _ in range(3):
            assert by_site(tick.tick())[str(kobo.site)].result == "SKIPPED_CLAIMED"
        s = site_of(health(env), kobo.site)
        assert s["state"] == "STOPPED" and "SITE_CLAIM_SKIPS" in codes(s["alarms"])
        assert s["claim"]["owner"] == "hung-host" and s["claim"]["claim_age_seconds"] >= 0
        assert health(env)["tick"]["state"] == "IDLE"  # the environment heartbeat still advances (review Q1)
        e = seam(kobo.tenant, kobo.site, DAY_A, env=env)["eligibility"]
        assert e["status"] == "STALE_PROJECTION" and "SITE_CLAIM_SKIPS" in e["reasons"]
        # Recovery: the holder ends (its own release), the next tick serves the Site.
        assert tick.store.release_site(kobo.tenant, kobo.site, holder, failure=None)
        assert by_site(tick.tick())[str(kobo.site)].result == "COMPLETED"
        assert site_of(health(env), kobo.site)["state"] == "IDLE"

        # A crashed holder: its claim outlives its lease (DB time) -> STOPPED until a tick takes it over.
        assert tick.store.claim_site(kobo.tenant, kobo.site, uuid4(), "crashed-host", 1)["claimed"]
        time.sleep(1.3)
        s = site_of(health(env), kobo.site)
        assert s["state"] == "STOPPED" and "SITE_CLAIM_STALE" in codes(s["alarms"])
        assert by_site(tick.tick())[str(kobo.site)].result == "COMPLETED"
        assert seam(kobo.tenant, kobo.site, DAY_A, env=env)["eligibility"]["status"] == "CURRENT"


class TestDatabaseTime:
    def test_skewed_application_clocks_do_not_move_s3_matcher_retry_or_health_times(
            self, kobo, engine, monkeypatch) -> None:  # noqa: F811
        class Ahead(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime.now(tz) + SKEW

        monkeypatch.setattr(assessment_worker, "datetime", Ahead)
        monkeypatch.setattr(finding_service, "datetime", Ahead)
        monkeypatch.setattr(recompute, "datetime", Ahead)  # the worker's default clock (`_utc_now`) reads this
        assert assessment_worker.utc_now() > datetime.now(UTC) + SKEW - timedelta(minutes=1)  # the skew is live

        tick, _ = make_tick(TickLimits(**FAST))
        env = tick.environment
        deliver(kobo, block(DAY_A, 8, 9))
        # A consequence derivation that fails deterministically (only the drain's; the read derives separately).
        real_derive = recompute.derive
        monkeypatch.setattr(recompute, "derive", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("defect")))
        r = by_site(tick.tick())[str(kobo.site)]
        assert r.stages["s4"]["code"] == "MATCHED"
        now = db_now(engine)
        (run,) = rows(engine, "SELECT knowledge_cutoff, started_at, completed_at FROM analytic_run "
                              "WHERE site_id = :s", s=kobo.site)
        revs = rows(engine, "SELECT created_at FROM finding_revision WHERE site_id = :s", s=kobo.site)
        for at in [run["knowledge_cutoff"], run["started_at"], run["completed_at"]] + [x["created_at"] for x in revs]:
            assert abs((at - now).total_seconds()) < 120, (at, now)  # DB time, not three hours ahead

        work = rows(engine, "SELECT w.id, count(a.*) AS n FROM financial_consequence_work w JOIN "
                            "financial_consequence_work_attempt a ON a.work_id = w.id WHERE w.site_id = :s "
                            "GROUP BY w.id", s=kobo.site)
        assert work and all(w["n"] == 1 for w in work)  # each failed once
        # Retry is due one minute after the failure in DB time; the app clock is three hours ahead, but the
        # scheduled drain uses DB time, so nothing is retried yet.
        tick.tick()
        again = rows(engine, "SELECT w.id, count(a.*) AS n FROM financial_consequence_work w JOIN "
                             "financial_consequence_work_attempt a ON a.work_id = w.id WHERE w.site_id = :s "
                             "GROUP BY w.id", s=kobo.site)
        assert sorted((str(w["id"]), w["n"]) for w in again) == sorted((str(w["id"]), 1) for w in work)

        # Health and the seam: failing consequence work is outstanding and alarms once attempts reach the bound.
        th = HealthThresholds(consequence_attempt_alarm=1)
        s = site_of(health(env, th), kobo.site)
        assert s["state"] == "FAILED" and "CONSEQUENCE_ATTEMPTS_GROWING" in codes(s["alarms"])
        assert s["consequence"]["pending"] == len(work) and s["consequence"]["oldest_age_seconds"] < 600
        e = seam(kobo.tenant, kobo.site, DAY_A, env=env)["eligibility"]
        assert e["status"] == "STALE_PROJECTION" and e["stage"] == "CONSEQUENCE"
        assert "WORK_OUTSTANDING" in e["reasons"]
        assert any(x["stage"] == "CONSEQUENCE" and x["code"] for x in e["errors"])

        # The one-off operator run: DB time by default (still not due), or an explicit override, reported.
        monkeypatch.setattr(recompute, "derive", real_derive)
        monkeypatch.setenv("DATABASE_URL", URL)
        assert recompute_consequences.main(["run", "--tenant", "demo", "--site", "KOBO-001"]) == 0
        assert rows(engine, "SELECT count(*) AS n FROM financial_consequence_work_attempt a JOIN "
                            "financial_consequence_work w ON w.id = a.work_id WHERE w.site_id = :s",
                    s=kobo.site)[0]["n"] == len(work)
        override = (db_now(engine) + timedelta(minutes=2)).isoformat()
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert recompute_consequences.main(["run", "--tenant", "demo", "--site", "KOBO-001",
                                                "--now", override]) == 0
        summary = json.loads(out.getvalue().strip().splitlines()[-1])
        assert summary["now_source"] == "override" and summary["selected"] == len(work)
        tick.tick()
        assert site_of(health(env, th), kobo.site)["state"] == "IDLE"
        assert seam(kobo.tenant, kobo.site, DAY_A, env=env)["eligibility"]["status"] == "CURRENT"
        # Heartbeat, claims and back-off were DB time throughout.
        head = tick.store.tick_head(env)
        assert abs((head["heartbeat_at"] - db_now(engine)).total_seconds()) < 120

        # A backdated configuration change: the discover stage's reconcile enqueues the window at DB time, so the
        # same tick's S3 stage (DB time) leases it; an app-clock enqueue would be three hours in the future.
        kobo.step({"do": "reserve", "value": 30, "effective_from": "2026-10-03T00:00:00Z",
                   "decided": "2026-10-12T11:00:00Z"})
        r = by_site(tick.tick())[str(kobo.site)]
        assert r.stages["s3"]["processed"] >= 1, r.stages["s3"]
        assert seam(kobo.tenant, kobo.site, DAY_A, env=env)["eligibility"]["status"] == "CURRENT"


class TestStaleNoWork:
    def test_a_pre_0012_stale_head_without_work_is_reported_with_ids_and_blocks_current(
            self, site, engine) -> None:  # noqa: F811
        site.publish("v1")
        worker = ConsequenceRecomputeWorker(site.store, site.prices, CONSEQUENCE_UNAVAILABLE)
        assert all(o.succeeded for o in worker.run_pending(site.tenant, site.site))
        rev = site.on(POWER_DAY)
        start = rev["episode_start"] + timedelta(minutes=5)
        submit(site, body(site, [power(site, start, start + timedelta(minutes=5), kw="30")]))
        (ev,) = evidence_work(engine, site.site)
        site.store.record_attempt(site.tenant, site.site, ev["id"], succeeded=True)  # as if no work was recorded
        env = f"test-{uuid4().hex[:12]}"
        s = site_of(health(env), site.site)
        (stale,) = s["stale_no_work"]
        assert stale["finding_id"] == str(rev["finding_id"]) and stale["finding_revision_id"] == str(rev["id"])
        assert stale["consequence_revision_id"] and "NO_WORK_RECORDED" in stale["reasons"]
        assert "STALE_NO_WORK" in codes(s["alarms"])
        day = datetime(rev["episode_start"].year, rev["episode_start"].month, rev["episode_start"].day, tzinfo=UTC)
        out = seam(site.tenant, site.site, day, env=env)
        assert out["eligibility"]["status"] != "CURRENT" and "STALE_NO_WORK" in out["eligibility"]["reasons"]
        (f,) = [f for f in out["findings"] if f["finding_revision_id"] == str(rev["id"])]
        assert f["stale_no_work"] is True and f["consequence_state"] == "STALE"


class TestOverlappingIngestionRace:
    def test_two_overlapping_chunks_during_an_active_tick_never_read_current_and_are_reprocessed(
            self, kobo, engine) -> None:  # noqa: F811
        """I4: two acceptances whose windows overlap commit concurrently while a tick holds the Site and runs S3.
        No deadlock is left unresolved, the selected window never reads CURRENT while that work is live, and
        later ticks reprocess the moved basis to CURRENT with every accepted reading."""
        tick, _ = make_tick(TickLimits(**FAST))
        env = tick.environment
        deliver(kobo, block(DAY_A, 6, 7))
        assert tick.tick().outcome == "COMPLETED"
        overlapped: list[bool] = []
        outcomes: list[tuple] = []
        for i, (a, b) in enumerate([((9, 11), (11, 13)), ((14, 16), (15, 17)), ((18, 19), (19, 20))]):
            envs = []
            for h0, h1 in (a, b):
                rows_ = [(r, False) for r in finding_cases.block_rows(block(DAY_A, h0, h1), finding_cases.SPEC[
                    "reading_rules"])]
                now_, _ = kobo.seal(sorted(rows_, key=lambda x: x[0][2]), "epoch-1")
                envs.append(now_)
            errors: list[BaseException] = []
            held: list[bool] = []
            gate = threading.Barrier(3)

            def chunk(envelopes, k):
                try:
                    gate.wait(10)
                    kobo.submit(envelopes, datetime(2026, 10, 12, 8, i, k, tzinfo=UTC))
                    held.append(tick.store.site_head(kobo.tenant, kobo.site)["claim_token"] is not None)
                except BaseException as error:  # noqa: BLE001 - reported below
                    errors.append(error)

            threads = [threading.Thread(target=chunk, args=(e, k)) for k, e in enumerate(envs)]

            # Round 0: the chunks commit as S3 starts (it then sees them); round 1: they race S3's lease and
            # processing; round 2: they commit after S3, while the tick runs S4 and the drain.
            stage, pause = (("s3", 0.2), ("s3", 0.0), ("s4", 0.5))[i]

            def during(args) -> None:
                for t in threads:
                    t.start()
                gate.wait(10)  # both chunks start while this tick holds the Site claim
                time.sleep(pause)

            tick.runner = InProcessRunner(tick.limits, before={stage: during})
            before = seam(kobo.tenant, kobo.site, DAY_A, env=env)["days"][0]["current_basis"]
            report = tick.tick()
            for t in threads:
                t.join(60)
            assert not any(t.is_alive() for t in threads), "an ingestion chunk did not finish (unresolved lock)"
            assert errors == [], f"ingestion defect under overlap (report to the evidence owner): {errors!r}"
            assert report.outcome == "COMPLETED"
            overlapped.append(any(held))
            mid = seam(kobo.tenant, kobo.site, DAY_A, env=env)
            assessments = build_postgres_assessment_store(URL)
            live = assessments.live_jobs("dispatch", "dispatch", kobo.tenant, kobo.site)
            assessments._engine.dispose()
            outcomes.append((mid["eligibility"]["status"], len(live)))
            if live:  # independent of the seam: live S3 work for the window is never CURRENT
                assert mid["eligibility"]["status"] != "CURRENT", mid["eligibility"]
            if mid["eligibility"]["status"] != "CURRENT":
                assert mid["eligibility"]["stage"] in ("S3", "S4", "CONSEQUENCE")
            tick.runner = InProcessRunner(tick.limits)
            for _ in range(4):
                tick.tick()
                out = seam(kobo.tenant, kobo.site, DAY_A, env=env)
                if out["eligibility"]["status"] == "CURRENT":
                    break
            assert out["eligibility"]["status"] == "CURRENT", out["eligibility"]
            basis = out["days"][0]["current_basis"]
            assert basis["accepted_reading_count"] > before["accepted_reading_count"]
        # The race was real: chunks committed while the tick held the Site claim, and at least one round left live
        # work behind the tick (otherwise the no-false-CURRENT assertion had nothing to bite on).
        assert any(overlapped), overlapped
        assert any(n > 0 for _, n in outcomes), outcomes


class TestTickCost:
    def test_measure_a_real_child_tick_over_one_and_four_sites(self, kobo, store, engine, capsys) -> None:  # noqa: F811
        lim = TickLimits(**FAST)
        deliver(kobo, block(DAY_A, 8, 9))
        tick, _ = make_tick(lim, StageRunner(URL, lim))
        sched = tick.store
        out = {}
        for label in ("one-site-first", "one-site-idle"):
            t0 = time.perf_counter()
            r = tick.tick()
            out[label] = {"wall_ms": int((time.perf_counter() - t0) * 1000), "reconcile_ms": r.reconcile_ms,
                          "stages_ms": {k: v.get("elapsed_ms") for s in r.visited() for k, v in s.stages.items()}}
        for code in ("COST-002", "COST-003", "COST-004"):
            sched.enrol(kobo.tenant, import_site(store, code).site.id, True, "cost-measure")
        t0 = time.perf_counter()
        r = tick.tick()
        out["four-sites-idle"] = {"wall_ms": int((time.perf_counter() - t0) * 1000), "reconcile_ms": r.reconcile_ms,
                                  "sites": len(r.visited())}
        assert r.outcome == "COMPLETED" and len(r.visited()) == 4
        with capsys.disabled():
            print("\nTICK_COST " + json.dumps(out))
