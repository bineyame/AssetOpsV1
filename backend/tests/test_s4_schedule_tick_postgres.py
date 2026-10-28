"""S4-02d phase 1: the bounded analytic/Finding worker tick, its schedule store and its stage children.

Packet `tasks/S4-02d-analytic-finding-worker-schedule.md` phase 1 and carries N2-N5: persisted active-Site
inventory across two tenants (a newly imported/enrolled PLANNED Site, gateway-without-evidence exclusion,
excluded-with-work and cross-tenant refusal), Site-scoped S3 leasing, a fair bounded tick over more Sites and jobs
than one tick takes, conditional S4 (idle ticks append no `finding_match_pass`; a new selection exactly one),
per-window currentness over a FAILED window with operator requeue by job ID, two concurrent ticks and a held Site
claim, crash/restart and idempotent replay, typed FENCE_MOVED vs the deterministic matcher defect, and real stage
children killed on a hang or timed out by a server-side lock timeout.
Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError
    import test_s1_bindings_postgres as s1
    import test_s4_finding_store_postgres as finding_cases
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import _release_connections  # noqa: F401

    from assetops_backend.analytics import assess_dispatch
    from assetops_backend.analytics.assessment_inputs import Window
    from assetops_backend.analytics.composition import build_dispatch_read_service, build_postgres_assessment_store
    from assetops_backend.scheduling import stages
    from assetops_backend.scheduling.composition import build_schedule_store
    from assetops_backend.scheduling.tick import ScheduleTick, StageRunner, TickLimits

UTC = timezone.utc
DAY_A = datetime(2026, 10, 6, tzinfo=UTC)
DAY_B = datetime(2026, 10, 8, tzinfo=UTC)
FAST = dict(discover_seconds=60, s3_seconds=60, s4_seconds=60, consequence_seconds=30, statement_timeout_ms=10_000,
            lock_timeout_ms=2_000, backoff_base_seconds=0)


def _iso(day: datetime, hh: int, mm: int = 0) -> str:
    return (day + timedelta(hours=hh, minutes=mm)).strftime("%Y-%m-%dT%H:%M:%SZ")


def block(day: datetime, h0: int, h1: int) -> dict:
    return {"from": _iso(day, h0), "to": _iso(day, h1), "pv": "40", "dis": "20", "soc": "80",
            "stop_before": True, "stop_after": True}


class InProcessRunner(StageRunner):
    """The real stage functions, called in this process (no kill bound): for ordering/fairness proofs, where a
    child per stage would only add start-up time. The killable-child path is proved with `StageRunner` below."""

    def __init__(self, limits: TickLimits, before=None, results=None) -> None:
        super().__init__(URL, limits)
        self.calls: list[tuple[str, str | None]] = []
        self.before, self.results = before or {}, results or {}

    def run(self, stage, args, seconds):
        args = json.loads(json.dumps(args, default=str))
        self.calls.append((stage, args.get("site_id")))
        if stage in self.before:
            self.before[stage](args)
        if stage in self.results and self.results[stage]:
            return self.results[stage].pop(0)
        try:
            result = stages.STAGES[stage](URL, args)
        except Exception as error:  # noqa: BLE001
            result = {"code": stages.classify(error), "error": f"{type(error).__name__}: {error}"}
        return json.loads(json.dumps(result, default=str))


@pytest.fixture()
def kobo(store, engine, monkeypatch):  # noqa: F811
    """KOBO-001 (tenant `demo`, imported PLANNED) with labelled controls recorded in the real past, so stage
    children running on the wall clock see them (the shared fixture's 2026-10-29 setup lies ahead of it)."""
    monkeypatch.setattr(finding_cases, "SETUP_AT", datetime(2026, 10, 10, 12, tzinfo=UTC))
    runner = finding_cases.CaseRunner(store, engine)
    yield runner
    runner.findings._engine and runner.findings._engine.dispose()


def deliver(r, *blocks, decided: str = "2026-10-11T08:00:00Z") -> None:
    r.step({"do": "deliver", "decided": decided, "blocks": list(blocks)})


def import_site(store, code: str, tenant: str = "demo"):  # noqa: F811
    src = s1.read_import_source(str(s1.KOBO_SOURCE))
    return s1.import_site(store, tenant_slug=tenant, configured_tenant_slug=tenant,
                          source=s1.ImportSource(path=f"var/sites/{code.lower()}.yaml", sha256=src.sha256,
                                                 record=replace(src.record, site_id=code)),
                          legacy_documents=(), clock=Clock(s1.NOW))


def rows(engine, sql: str, **p) -> list[dict]:  # noqa: F811
    with engine.connect() as c:
        return [dict(x._mapping) for x in c.execute(text(sql), p)]


def count(engine, table: str, site=None) -> int:  # noqa: F811
    where = "" if site is None else " WHERE site_id = :s"
    if table == "recompute_job":  # W4-02 q1 ruling 2: dispatch jobs only; the MINIGRID Site also enqueues mini work
        where += (" AND" if where else " WHERE") + " domain = 'dispatch'"
    return rows(engine, f"SELECT count(*) AS n FROM {table}{where}", s=site)[0]["n"]


def ledger_counts(engine, site) -> dict:  # noqa: F811
    return {t: count(engine, t, site) for t in ("analytic_run", "analytic_run_selection", "finding",
                                                "finding_revision", "finding_match_pass",
                                                "financial_consequence_revision", "recompute_job")}


def jobs(engine, site) -> list[dict]:  # noqa: F811
    return rows(engine, "SELECT id, status, window_start, window_end, attempts, lease_until, last_error, "
                        "available_at FROM recompute_job WHERE site_id = :s AND domain = 'dispatch' ORDER BY created_at",
                s=site)  # W4-02 q1 ruling 2: dispatch jobs only; the MINIGRID Site also enqueues 0029 mini work


def make_tick(limits: TickLimits, runner=None, env=None, owner=None):
    sched = build_schedule_store(URL, statement_timeout_ms=limits.statement_timeout_ms,
                                 lock_timeout_ms=limits.lock_timeout_ms)
    runner = runner or InProcessRunner(limits)
    return ScheduleTick(sched, runner, limits, environment=env or f"test-{uuid4().hex[:12]}", owner=owner), runner


def by_site(report) -> dict:
    return {str(s.site_id): s for s in report.selected}


class TestInventoryAndIsolation:
    def test_active_site_predicate_two_tenants_enrolment_exclusion_and_cross_tenant_refusal(
            self, kobo, store, engine) -> None:  # noqa: F811
        lim = TickLimits(**FAST)
        tick, runner = make_tick(lim)
        deliver(kobo, block(DAY_A, 8, 9))
        k1 = str(kobo.site)
        lifecycle = rows(engine, "SELECT lifecycle FROM site WHERE id = :s", s=kobo.site)[0]["lifecycle"]
        assert lifecycle == "PLANNED"
        k2 = import_site(store, "KOBO-002").site.id  # gateway and sources registered, no evidence
        assert count(engine, "gateway", k2) == 1 and count(engine, "accepted_evidence", k2) == 0
        acme = import_site(store, "ACME-001", tenant="acme")
        k3 = import_site(store, "KOBO-003").site.id
        with engine.begin() as c:
            c.execute(text("UPDATE site SET lifecycle = 'DECOMMISSIONED' WHERE id = :s"), {"s": k3})
        a = build_postgres_assessment_store(URL)
        a.enqueue(acme.tenant.id, acme.site.id, "dispatch", Window(DAY_A, DAY_A + timedelta(days=1)),
                  datetime.now(UTC) - timedelta(minutes=5))
        a.enqueue(kobo.tenant, k3, "dispatch", Window(DAY_A, DAY_A + timedelta(days=1)),
                  datetime.now(UTC) - timedelta(minutes=5))

        first = tick.tick()
        assert first.outcome == "COMPLETED", first.as_json()
        sel = by_site(first)
        # KOBO-001: PLANNED with accepted evidence. KOBO-002: gateway but no evidence, not enrolled -> excluded
        # (N4: registered evidence = at least one accepted_evidence row). ACME-001: no evidence, not enrolled,
        # but a live job keeps it selected. KOBO-003: DECOMMISSIONED with a live job -> selected, reported.
        assert sel[k1].reason == "EVIDENCE" and sel[k1].result == "COMPLETED"
        assert str(k2) not in sel
        assert sel[str(acme.site.id)].reason == "EXCLUDED_WITH_WORK"
        assert sel[str(k3)].reason == "EXCLUDED_WITH_WORK"
        reported = {e["site_id"]: e for e in first.excluded_with_work}
        assert reported[str(k3)]["lifecycle"] == "DECOMMISSIONED" and len(reported[str(k3)]["live_jobs"]) == 1
        assert first.not_selected == 1
        # Tenant isolation: each tenant's job was leased only inside its own Site's stage.
        assert [j["status"] for j in jobs(engine, acme.site.id)] == ["DONE"]
        assert [j["status"] for j in jobs(engine, k3)] == ["DONE"]
        for visited in first.selected:  # Site-scoped leasing: a Site's stage leased only its own jobs
            own = {str(j["id"]) for j in jobs(engine, visited.site_id)}
            leased = {str(o["job_id"]) for o in visited.stages["s3"]["outcomes"]}
            assert leased <= own, (visited.site_code, leased, own)
        assert {str(o["job_id"]) for o in sel[str(k3)].stages["s3"]["outcomes"]} == {
            str(j["id"]) for j in jobs(engine, k3)}
        s3_calls = [site for stage, site in runner.calls if stage == "s3"]
        assert sorted(s3_calls) == sorted([k1, str(acme.site.id), str(k3)])

        # Newly enrolled PLANNED Site (and the other tenant's Site) are selected on the next tick; the
        # decommissioned Site whose work is resolved drops out.
        sched = tick.store
        sched.enrol(kobo.tenant, k2, True, "test-operator")
        sched.enrol(acme.tenant.id, acme.site.id, True, "test-operator")
        second = by_site(tick.tick())
        assert second[str(k2)].reason == "ENROLLED" and second[str(k2)].result == "COMPLETED"
        assert second[str(acme.site.id)].reason == "ENROLLED"
        assert str(k3) not in second
        heads = {str(h["site_id"]): h for h in sched.site_heads()}
        assert heads[str(acme.site.id)]["tenant_id"] == acme.tenant.id
        assert heads[str(k2)]["tenant_id"] == kobo.tenant

        # A foreign pairing (tenant demo, acme's Site) is refused by the schedule tables' scoped FK.
        with pytest.raises(IntegrityError):
            sched.enrol(kobo.tenant, acme.site.id, True, "test-operator")
        sched.enrol(kobo.tenant, k2, False, "test-operator")
        assert str(k2) not in by_site(tick.tick())


class TestBoundedFairTick:
    def test_more_sites_and_jobs_than_one_tick_are_served_fairly_by_the_durable_cursor(
            self, kobo, store, engine) -> None:  # noqa: F811
        deliver(kobo, block(DAY_A, 8, 9))
        others = [import_site(store, f"KOBO-10{i}").site.id for i in range(5)]
        lim = TickLimits(max_sites=2, s3_jobs_per_site=1, **FAST)
        tick, runner = make_tick(lim)
        for sid in others:
            tick.store.enrol(kobo.tenant, sid, True, "test-operator")
        a = build_postgres_assessment_store(URL)
        for d in (1, 2, 3):  # three more KOBO-001 jobs on empty days: more jobs than its per-tick bound
            day = datetime(2026, 10, d, tzinfo=UTC)
            a.enqueue(kobo.tenant, kobo.site, "dispatch", Window(day, day + timedelta(hours=1)),
                      datetime.now(UTC) - timedelta(minutes=5))
        all_sites = sorted([kobo.site, *others])
        visits: list[list[str]] = []
        for _ in range(3):
            report = tick.tick()
            assert report.outcome == "COMPLETED"
            visited = [str(s.site_id) for s in report.selected if s.result != "DEFERRED"]
            assert len(visited) == 2 and len(report.selected) == 6
            visits.append(visited)
        flat = [x for v in visits for x in v]
        assert sorted(flat) == sorted(str(s) for s in all_sites)  # every Site exactly once in three ticks
        assert flat == [str(s) for s in all_sites]  # in (tenant, site) order after the cursor
        assert tuple(tick.store.cursor(tick.environment)) == (kobo.tenant, all_sites[-1])
        head = tick.store.tick_head(tick.environment)
        assert (head["last_sites_selected"], head["last_sites_processed"], head["last_sites_deferred"]) == (6, 2, 4)
        # KOBO-001's stage leased at most one job: the rest stay live and counted as deferred in its head.
        k = tick.store.site_head(kobo.tenant, kobo.site)
        assert k["s3_processed"] == 1 and k["s3_deferred"] >= 1, k
        # The next rotation reaches KOBO-001 again (wrap-around) and drains one more.
        for _ in range(3):
            tick.tick()
        assert tick.store.site_head(kobo.tenant, kobo.site)["selected_count"] == 2


class TestConditionalMatchAndCurrentness:
    def test_idle_ticks_add_no_pass_a_new_selection_adds_one_and_a_failed_window_does_not_freeze_others(
            self, kobo, store, engine, monkeypatch) -> None:  # noqa: F811
        lim = TickLimits(**FAST)
        tick, runner = make_tick(lim)
        deliver(kobo, block(DAY_A, 8, 9), block(DAY_B, 8, 9))
        first = tick.tick()
        assert by_site(first)[str(kobo.site)].stages["s4"]["code"] == "MATCHED"
        base = ledger_counts(engine, kobo.site)
        assert base["finding_match_pass"] == 1 and base["finding"] >= 2
        assert all(j["status"] == "DONE" for j in jobs(engine, kobo.site))
        for _ in range(3):  # idle ticks: S3 leases nothing, S4 skips, nothing is appended anywhere
            r = by_site(tick.tick())[str(kobo.site)]
            assert r.stages["s4"]["code"] == "SKIPPED_UNCHANGED_FENCE" and r.result == "COMPLETED"
        assert ledger_counts(engine, kobo.site) == base
        head = tick.store.site_head(kobo.tenant, kobo.site)
        assert head["s4_outcome"] == "SKIPPED_UNCHANGED_FENCE" and head["matched_version"] == "finding-episode-3"

        read = build_dispatch_read_service(URL)
        revs_b = rows(engine, "SELECT r.id FROM finding_revision r WHERE r.site_id = :s AND "
                              "r.episode_start >= :b", s=kobo.site, b=DAY_B)
        # Day B gets new evidence whose job terminally fails; day A gets a new episode.
        deliver(kobo, block(DAY_B, 12, 13), decided="2026-10-12T08:00:00Z")
        failed_job = [j for j in jobs(engine, kobo.site) if j["status"] == "PENDING"][0]
        with engine.begin() as c:
            c.execute(text("UPDATE recompute_job SET status = 'FAILED', attempts = 3, available_at = now(), "
                           "last_error = 'injected terminal failure' WHERE id = :j"), {"j": failed_job["id"]})
        deliver(kobo, block(DAY_A, 12, 13), decided="2026-10-12T09:00:00Z")
        r = by_site(tick.tick())[str(kobo.site)]
        assert r.stages["s4"]["code"] == "MATCHED"
        after = ledger_counts(engine, kobo.site)
        assert after["finding_match_pass"] == base["finding_match_pass"] + 1  # exactly one pass
        assert after["finding_revision"] > base["finding_revision"]  # day A advanced
        assert rows(engine, "SELECT r.id FROM finding_revision r WHERE r.site_id = :s AND r.episode_start >= :b",
                    s=kobo.site, b=DAY_B) == revs_b  # day B episodes unchanged over the FAILED window
        assert read.window(kobo.tenant, kobo.site, DAY_B.date())["status"] != "CURRENT"
        assert read.window(kobo.tenant, kobo.site, DAY_A.date())["status"] == "CURRENT"
        live = build_postgres_assessment_store(URL).live_jobs("dispatch", "dispatch", kobo.tenant, kobo.site)
        assert [(str(j["id"]), j["status"], j["last_error"]) for j in live] == [
            (str(failed_job["id"]), "FAILED", "injected terminal failure")]

        # Operator recovery by the failed job's ID (N5), through AssessmentStore.enqueue; refusals first.
        monkeypatch.setenv("DATABASE_URL", URL)
        assert assess_dispatch.main(["requeue", "--tenant-id", str(kobo.tenant), "--site-id", str(uuid4()),
                                     "--job-id", str(failed_job["id"])]) == 2
        done = [j for j in jobs(engine, kobo.site) if j["status"] == "DONE"][0]
        assert assess_dispatch.main(["requeue", "--tenant-id", str(kobo.tenant), "--site-id", str(kobo.site),
                                     "--job-id", str(done["id"])]) == 2
        assert assess_dispatch.main(["requeue", "--tenant-id", str(kobo.tenant), "--site-id", str(kobo.site),
                                     "--job-id", str(failed_job["id"])]) == 0
        r = by_site(tick.tick())[str(kobo.site)]
        assert r.result == "COMPLETED" and r.stages["s4"]["code"] == "MATCHED"
        assert build_postgres_assessment_store(URL).live_jobs("dispatch", "dispatch", kobo.tenant, kobo.site) == []
        assert read.window(kobo.tenant, kobo.site, DAY_B.date())["status"] == "CURRENT"
        assert assess_dispatch.main(["requeue", "--tenant-id", str(kobo.tenant), "--site-id", str(kobo.site),
                                     "--job-id", str(failed_job["id"])]) == 2  # superseded: not live any more


class TestFenceMovedTyping:
    def test_a_moved_fence_is_retryable_typed_and_counted_apart_from_the_deterministic_defect(
            self, kobo, engine, monkeypatch) -> None:  # noqa: F811
        from assetops_backend.analytics import composition
        from assetops_backend.analytics.adapters.postgres_finding_store import FindingFenceMoved

        deliver(kobo, block(DAY_A, 8, 9))
        messages = iter(["a selection, recompute job or Finding changed since the matcher read; re-plan",
                         "a cited evidence ID is not accepted in this Site"])

        class Raising:
            def match(self, tenant_id, site_id):
                raise FindingFenceMoved(next(messages))

        monkeypatch.setattr(composition, "build_finding_matcher", lambda url: Raising())
        tick, _ = make_tick(TickLimits(**FAST))
        r1 = by_site(tick.tick())[str(kobo.site)]
        assert r1.stages["s4"]["code"] == "FENCE_MOVED" and r1.failure[:2] == ("S4", "FENCE_MOVED")
        assert tick.store.site_head(kobo.tenant, kobo.site)["fence_moved_streak"] == 1
        r2 = by_site(tick.tick())[str(kobo.site)]
        assert r2.stages["s4"]["code"] == "MATCH_EVIDENCE_NOT_ACCEPTED"
        head = tick.store.site_head(kobo.tenant, kobo.site)
        assert head["last_failure_code"] == "MATCH_EVIDENCE_NOT_ACCEPTED" and head["consecutive_failures"] == 2
        assert head["fence_moved_streak"] == 1 and head["matched_fence"] is None
        assert count(engine, "finding_match_pass", kobo.site) == 0
        monkeypatch.undo()
        monkeypatch.setattr(finding_cases, "SETUP_AT", datetime(2026, 10, 10, 12, tzinfo=UTC))
        r3 = by_site(tick.tick())[str(kobo.site)]
        assert r3.stages["s4"]["code"] == "MATCHED" and r3.result == "COMPLETED"
        head = tick.store.site_head(kobo.tenant, kobo.site)
        assert head["fence_moved_streak"] == 0 and head["consecutive_failures"] == 0


class TestClaimsCrashAndReplay:
    def test_two_concurrent_ticks_and_a_held_site_claim(self, kobo, engine) -> None:  # noqa: F811
        deliver(kobo, block(DAY_A, 8, 9))
        env = f"test-{uuid4().hex[:12]}"
        lim = TickLimits(**FAST)
        slow = InProcessRunner(lim, before={"discover": lambda a: time.sleep(2.0)})
        a, _ = make_tick(lim, slow, env=env, owner="host-a")
        b, runner_b = make_tick(lim, env=env, owner="host-b")
        out: dict = {}
        thread = threading.Thread(target=lambda: out.setdefault("a", a.tick()))
        thread.start()
        time.sleep(0.7)
        out["b"] = b.tick()
        thread.join()
        assert out["a"].outcome == "COMPLETED" and out["b"].outcome == "SKIPPED_CLAIMED"
        assert runner_b.calls == []  # the second host touched nothing
        head = a.store.tick_head(env)
        assert head["claim_skips"] == 0 and head["heartbeat_at"] is not None  # the completion reset skips
        beat = head["heartbeat_at"]

        # Another host holds KOBO-001's Site claim: this tick completes but reports the Site skipped.
        a.store.claim_site(kobo.tenant, kobo.site, uuid4(), "host-c", 120)
        r = by_site(b.tick())[str(kobo.site)]
        assert r.result == "SKIPPED_CLAIMED" and r.stages == {}
        site_head = a.store.site_head(kobo.tenant, kobo.site)
        assert site_head["claim_skips"] == 1 and site_head["claim_owner"] == "host-c"
        assert a.store.tick_head(env)["heartbeat_at"] > beat

    def test_a_crashed_tick_resumes_after_its_claims_expire_and_replay_appends_nothing(
            self, kobo, engine) -> None:  # noqa: F811
        deliver(kobo, block(DAY_A, 8, 9))
        lim = TickLimits(**FAST)
        tick, _ = make_tick(lim)
        crashed = uuid4()
        # The crashed process left: the environment claim, the Site claim mid-S3, and a leased S3 job.
        assert tick.store.claim_tick(tick.environment, crashed, "crashed-host", 1)["claimed"]
        assert tick.store.claim_site(kobo.tenant, kobo.site, crashed, "crashed-host", 1)["claimed"]
        tick.store.set_stage(kobo.tenant, kobo.site, crashed, "S3")
        lease = build_postgres_assessment_store(URL).lease_job(
            "dispatch", datetime.now(UTC), timedelta(minutes=5), tenant_id=kobo.tenant, site_id=kobo.site)
        assert lease is not None and lease.attempts == 1
        assert tick.tick().outcome == "SKIPPED_CLAIMED"  # its lease has not expired yet
        time.sleep(1.2)
        # The S3 job lease is five minutes; stand in for its expiry rather than waiting.
        with engine.begin() as c:
            c.execute(text("UPDATE recompute_job SET lease_until = now() - interval '1 second' WHERE id = :j"),
                      {"j": lease.job_id})
        resumed = tick.tick()
        assert resumed.outcome == "COMPLETED"
        r = by_site(resumed)[str(kobo.site)]
        assert r.result == "COMPLETED" and r.stages["s4"]["code"] == "MATCHED"
        (job,) = jobs(engine, kobo.site)
        assert job["status"] == "DONE" and job["attempts"] == 2
        # The crashed holder can no longer write either claim.
        assert not tick.store.finish_tick(tick.environment, crashed, sites_selected=0, sites_processed=0,
                                          sites_deferred=0, excluded_with_work=0, reconcile_ms=None)
        assert not tick.store.release_site(kobo.tenant, kobo.site, crashed, failure=None)
        before = ledger_counts(engine, kobo.site)
        for _ in range(2):
            assert tick.tick().outcome == "COMPLETED"
        assert ledger_counts(engine, kobo.site) == before


class TestKillableStagesAndServerTimeouts:
    @pytest.mark.slow  # PERF-01 R5: waits on the real clock by design (backend/TESTING.md "Slow tier")
    def test_a_hung_stage_is_killed_its_job_lease_is_exposed_and_a_db_stall_is_a_typed_timeout(
            self, kobo, engine) -> None:  # noqa: F811
        deliver(kobo, block(DAY_A, 8, 9))
        lim = TickLimits(discover_seconds=60, s3_seconds=8, s4_seconds=60, consequence_seconds=30,
                         statement_timeout_ms=3_000, lock_timeout_ms=1_000, backoff_base_seconds=1)
        hang = [sys.executable, "-c",
                "import json, os, sys, time\n"
                "from datetime import datetime, timedelta, timezone\n"
                "from uuid import UUID\n"
                "from assetops_backend.analytics.composition import build_postgres_assessment_store\n"
                "a = json.loads(sys.argv[1])\n"
                "s = build_postgres_assessment_store(os.environ['DATABASE_URL'])\n"
                "s.lease_job('dispatch', datetime.now(timezone.utc), timedelta(minutes=5),\n"
                "            tenant_id=UUID(a['tenant_id']), site_id=UUID(a['site_id']))\n"
                "print('leased', flush=True)\n"
                "time.sleep(120)\n"]
        tick, _ = make_tick(lim, StageRunner(URL, lim, overrides={"s3": hang}))
        started = time.monotonic()
        report = tick.tick()
        r = by_site(report)[str(kobo.site)]
        assert r.stages["s3"]["code"] == "TIMEOUT" and r.stages["s3"].get("elapsed_ms", 0) < 30_000
        assert r.failure[:2] == ("S3", "TIMEOUT") and r.result == "FAILED"
        assert time.monotonic() - started < 90
        (job,) = jobs(engine, kobo.site)
        # The killed child's job is LEASED until its five-minute lease expires; not complete, not lost.
        assert job["status"] == "LEASED" and job["attempts"] == 1
        assert job["lease_until"] > datetime.now(UTC) + timedelta(minutes=3)
        head = tick.store.site_head(kobo.tenant, kobo.site)
        assert head["last_failure_stage"] == "S3" and head["last_failure_code"] == "TIMEOUT"
        assert head["retry_due_at"] is not None and head["stage"] == "IDLE" and head["claim_token"] is None
        beat = tick.store.tick_head(tick.environment)["heartbeat_at"]

        # Lease expiry (stood in by SQL), then a real-children tick re-leases and completes it.
        with engine.begin() as c:
            c.execute(text("UPDATE recompute_job SET lease_until = now() - interval '1 second' WHERE id = :j"),
                      {"j": job["id"]})
        time.sleep(1.5)  # schedule-level back-off of one second
        real, _ = make_tick(lim, StageRunner(URL, lim), env=tick.environment)
        r = by_site(real.tick())[str(kobo.site)]
        assert r.result == "COMPLETED", r
        assert r.stages["s4"]["code"] == "MATCHED"
        (job,) = jobs(engine, kobo.site)
        assert job["status"] == "DONE" and job["attempts"] == 2
        assert real.store.tick_head(real.environment)["heartbeat_at"] > beat

        # DB stall inside a Site stage: Finding revisions are locked, so S4's fence read hits lock_timeout in its
        # child (PGOPTIONS, N2) and reports TIMEOUT; S3 and the drain still run.
        deliver(kobo, block(DAY_A, 12, 13), decided="2026-10-12T09:00:00Z")
        with engine.connect() as holder:
            tx = holder.begin()
            holder.execute(text("LOCK TABLE finding_revision IN ACCESS EXCLUSIVE MODE"))
            r = by_site(real.tick())[str(kobo.site)]
            tx.rollback()
        assert r.stages["s3"]["code"] == "OK" and r.stages["s4"]["code"] == "TIMEOUT", r.stages
        assert "killed" not in r.stages["s4"] and "lock timeout" in r.stages["s4"]["error"]  # server-side
        assert r.stages["consequence"]["code"] == "OK"
        assert real.store.site_head(kobo.tenant, kobo.site)["last_failure_code"] == "TIMEOUT"

        # DB stall in discovery: the tick fails typed, advances no heartbeat and backs off.
        beat = real.store.tick_head(real.environment)["heartbeat_at"]
        with engine.connect() as holder:
            tx = holder.begin()
            holder.execute(text("LOCK TABLE recompute_job IN ACCESS EXCLUSIVE MODE"))
            failed = real.tick()
            tx.rollback()
        assert failed.outcome == "FAILED" and failed.failure["code"] == "TIMEOUT", failed.as_json()
        assert "lock timeout" in failed.failure["error"]
        head = real.store.tick_head(real.environment)
        assert head["heartbeat_at"] == beat and head["consecutive_failures"] == 1
        assert head["last_failure_code"] == "TIMEOUT" and head["retry_due_at"] is not None
        assert real.tick().outcome == "RETRY_DUE"  # still inside the back-off
        time.sleep(1.5)
        recovered = real.tick()
        assert recovered.outcome == "COMPLETED"
        assert by_site(recovered)[str(kobo.site)].stages["s4"]["code"] == "MATCHED"
        assert real.store.tick_head(real.environment)["consecutive_failures"] == 0
