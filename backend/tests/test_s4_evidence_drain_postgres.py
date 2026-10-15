"""S4-02c phase 2: the scoped `EVIDENCE_ACCEPTED` drain and the scheduled one-shot runner, against Postgres.

Packet `tasks/S4-02c-evidence-consequence-work.md` items 3-4, carries C4 (worker half), N1, N3, N4, N7, R2 and
phase 1 review L2: same-revision drain to `POWER_NOT_IN_ASSESSMENT_INPUTS` with the old consequence retained;
a non-GOOD same-asset mean in Candidate time derives (never a quality no-op); superseded revision, wrong role,
wrong asset and outside-Candidate-time no-ops with typed `no_op_reason`; a forged cross-Site locator refused
without fallback; append-then-crash replay; retry from the last FAILED attempt against an injected clock;
failing rows never starving newer work under `limit`; the Site claim (second runner skipped, a killed runner's
claim released); and a bounded batch over a day of five-minute means across several Findings with chunk
latency logged. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import BACKEND, Clock, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import POWER_DAY, PowerSite, _release_connections  # noqa: F401
    from test_s4_evidence_consequence_work_postgres import (
        accepted_id, body, clone_revision, evidence_work, power, site, submit)  # noqa: F401
    import test_s4_finding_store_postgres as finding_cases

    from assetops_backend.financials.composition import CONSEQUENCE_UNAVAILABLE
    from money_gate_stub import ELIGIBLE
    from assetops_backend.financials.consequence_read import ConsequenceReadService
    from assetops_backend.financials.recompute import (
        ERROR_EVIDENCE_LOCATOR_NOT_IN_SITE, ERROR_STORE_UNAVAILABLE, ERROR_WORK_SCOPE_MISMATCH, NO_OP_ASSET,
        NO_OP_OUTSIDE_CANDIDATE_TIME, NO_OP_ROLE, NO_OP_SUPERSEDED, ConsequenceRecomputeWorker)


def worker(site, store=None, clock=None) -> "ConsequenceRecomputeWorker":
    kw = {} if clock is None else {"clock": clock}
    return ConsequenceRecomputeWorker(store or site.store, site.prices, CONSEQUENCE_UNAVAILABLE, **kw)


def settle(site) -> None:
    """Price the Site and drain the bootstrap FindingRevision work, so only evidence work remains."""
    site.publish("v1")
    assert all(o.succeeded for o in worker(site).run_pending(site.tenant, site.site))


def consequences(engine, finding_revision_id) -> list[dict]:  # noqa: F811
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(
            "SELECT id, revision_no, state, quantity_state, quantity_reason, technical_input_sha256, "
            "consequence_basis_sha256 FROM financial_consequence_revision WHERE finding_revision_id = :r "
            "ORDER BY revision_no"), {"r": finding_revision_id})]


def attempts(engine, work_id) -> list[dict]:  # noqa: F811
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(
            "SELECT attempt_no, outcome, error_code, no_op_reason, consequence_revision_ids, finished_at "
            "FROM financial_consequence_work_attempt WHERE work_id = :w ORDER BY attempt_no"), {"w": work_id})]


def all_consequence_count(engine) -> int:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM financial_consequence_revision")).scalar_one()


def no_duplicate_basis(engine) -> None:  # noqa: F811
    with engine.connect() as c:
        dup = c.execute(text(
            "SELECT count(*) FROM (SELECT finding_revision_id, consequence_basis_sha256 FROM "
            "financial_consequence_revision GROUP BY 1, 2 HAVING count(*) > 1) d")).scalar_one()
    assert dup == 0


def candidate_spans(engine, rev) -> list[tuple[datetime, datetime]]:  # noqa: F811
    with engine.connect() as c:
        claim = c.execute(text("SELECT claim FROM finding_revision WHERE id = :r"), {"r": rev["id"]}).scalar_one()
    return [(datetime.fromisoformat(s["start"].replace("Z", "+00:00")),
             datetime.fromisoformat(s["end"].replace("Z", "+00:00"))) for s in claim["candidate_spans"]]


def clone_finding(engine, rev, *, generator_asset_id=None, episode=None) -> tuple:  # noqa: F811
    """A separate Finding of the same Site (test SQL; no product module writes work), with one revision cloned
    from `rev` (same claim) and optionally another generator or episode. Its revision's 0011 trigger enqueues
    FindingRevision work like any appended revision."""
    with engine.connect() as c:
        fcols = [r[0] for r in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'finding' "
            "ORDER BY ordinal_position"))]
        rcols = [r[0] for r in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'finding_revision' "
            "ORDER BY ordinal_position"))]
    fid, rid = uuid4(), uuid4()
    fover = {"id": "CAST(:fid AS uuid)", "finding_key": "finding_key || ':' || CAST(:fid AS text)"}
    if generator_asset_id is not None:
        fover["generator_asset_id"] = "CAST(:g AS uuid)"
    rover = {"id": "CAST(:rid AS uuid)", "finding_id": "CAST(:fid AS uuid)", "revision_no": "1"}
    if episode is not None:
        rover.update({"episode_start": "CAST(:e0 AS timestamptz)", "episode_end": "CAST(:e1 AS timestamptz)"})
    args = {"fid": str(fid), "rid": str(rid), "f": rev["finding_id"], "r": rev["id"],
            "g": None if generator_asset_id is None else str(generator_asset_id),
            "e0": None if episode is None else episode[0], "e1": None if episode is None else episode[1]}
    with engine.begin() as c:
        c.execute(text(f"INSERT INTO finding ({', '.join(fcols)}) SELECT "
                       f"{', '.join(fover.get(n, n) for n in fcols)} FROM finding WHERE id = :f"), args)
        c.execute(text(f"INSERT INTO finding_revision ({', '.join(rcols)}) SELECT "
                       f"{', '.join(rover.get(n, n) for n in rcols)} FROM finding_revision WHERE id = :r"), args)
    return fid, rid


def insert_evidence_work(engine, site, finding_id, revision_id, evidence_id, a, b):  # noqa: F811
    """A test-written `EVIDENCE_ACCEPTED` row for a reading the trigger would not select (role, other episode)."""
    with engine.begin() as c:
        return c.execute(text(
            "INSERT INTO financial_consequence_work (tenant_id, site_id, cause, finding_id, finding_revision_id, "
            "accepted_evidence_id, affected_from, affected_to) VALUES (:t, :s, 'EVIDENCE_ACCEPTED', :f, :r, :e, "
            ":a, :b) RETURNING id"),
            {"t": site.tenant, "s": site.site, "f": finding_id, "r": revision_id, "e": evidence_id, "a": a,
             "b": b}).scalar_one()


def late_mean(site, engine, rev, *, kw="30", quality="GOOD", minutes=5):  # noqa: F811
    a, _ = candidate_spans(engine, rev)[0]
    start = a + timedelta(minutes=minutes)
    answer = submit(site, body(site, [power(site, start, start + timedelta(minutes=5), kw=kw, quality=quality)]))
    assert [d.decision for d in answer.receipt.dispositions] == ["ACCEPTED"]
    return accepted_id(engine, site.site, start, start + timedelta(minutes=5)), start


class Crash(RuntimeError):
    pass


class CrashAfterAppend:
    """The real store, but `record_attempt` dies once after a successful append (the append-then-crash case)."""

    def __init__(self, real) -> None:
        self.real, self.crashed = real, False

    def __getattr__(self, name):
        return getattr(self.real, name)

    def record_attempt(self, *args, **kw):
        if kw.get("succeeded") and not self.crashed:
            self.crashed = True
            raise Crash("killed between append and record_attempt")
        return self.real.record_attempt(*args, **kw)


class FailFor:
    """The real store, but `load_input` is unavailable for the named FindingRevisions while `failing`."""

    def __init__(self, real, revision_ids) -> None:
        self.real, self.revision_ids, self.failing = real, set(revision_ids), True

    def __getattr__(self, name):
        return getattr(self.real, name)

    def load_input(self, tenant_id, site_id, finding_id, finding_revision_id):
        if self.failing and finding_revision_id in self.revision_ids:
            from assetops_backend.financials.composition import ConsequenceStoreUnavailable

            raise ConsequenceStoreUnavailable("source closed for this test")
        return self.real.load_input(tenant_id, site_id, finding_id, finding_revision_id)


class TestScopedDrain:
    def test_a_late_in_candidate_mean_drains_the_same_revision_to_power_not_in_assessment_inputs(
            self, site, engine) -> None:  # noqa: F811
        settle(site)
        rev = site.on(POWER_DAY)
        (first,) = consequences(engine, rev["id"])
        late, _ = late_mean(site, engine, rev)
        (w,) = evidence_work(engine, site.site)
        reads = ConsequenceReadService(site.store, site.prices, eligibility=ELIGIBLE)

        def read():
            return reads.read(site.tenant, site.site, rev["finding_id"], rev["id"], finding_revision_is_latest=True,
                              source_open=True)["currentness"]

        before = read()
        assert before["state"] == "STALE" and "TECHNICAL_INPUT_CHANGED" in before["reasons"]
        report = worker(site).run(site.tenant, site.site, limit=10)
        assert report.claimed and report.counts() == {"selected": 1, "appended": 1, "replayed": 0, "no_op": 0,
                                                      "failed": 0, "deferred": 0, "backlog": 0}
        (out,) = report.outcomes
        old, new = consequences(engine, rev["id"])
        assert old == first and new["revision_no"] == 2 and out.appended == [new["id"]]
        assert (new["state"], new["quantity_reason"]) == ("QUANTITY_UNAVAILABLE", "POWER_NOT_IN_ASSESSMENT_INPUTS")
        (att,) = attempts(engine, w["id"])
        assert (att["outcome"], att["no_op_reason"], att["consequence_revision_ids"]) == (
            "SUCCEEDED", None, [str(new["id"])])
        f = site.store.load_input(site.tenant, site.site, rev["finding_id"], rev["id"])
        assert str(late) in {r.evidence_id for r in f.readings}
        assert read()["state"] == "CURRENT"
        # Repeat: nothing pending, nothing appended.
        assert worker(site).run(site.tenant, site.site, limit=10).counts()["selected"] == 0
        no_duplicate_basis(engine)

    def test_a_non_good_same_asset_mean_in_candidate_time_derives_and_is_never_a_quality_no_op(
            self, site, engine) -> None:  # noqa: F811
        """Re-review N1."""
        settle(site)
        rev = site.on(POWER_DAY)
        late_mean(site, engine, rev, quality="SUSPECT")
        (out,) = worker(site).run(site.tenant, site.site, limit=10).outcomes
        assert out.succeeded and out.no_op_reason is None and len(out.appended) == 1
        assert [c["revision_no"] for c in consequences(engine, rev["id"])] == [1, 2]

    def test_append_then_crash_replays_the_same_consequence_without_a_duplicate_basis(
            self, site, engine) -> None:  # noqa: F811
        settle(site)
        rev = site.on(POWER_DAY)
        late_mean(site, engine, rev)
        (w,) = evidence_work(engine, site.site)
        crashing = CrashAfterAppend(site.store)
        with pytest.raises(Crash):
            worker(site, store=crashing).run(site.tenant, site.site, limit=10)
        (_, appended) = consequences(engine, rev["id"])
        assert attempts(engine, w["id"]) == []  # the crash left the work pending
        (out,) = worker(site).run(site.tenant, site.site, limit=10).outcomes  # restart
        assert out.succeeded and out.replayed == [appended["id"]] and out.appended == []
        assert len(consequences(engine, rev["id"])) == 2
        no_duplicate_basis(engine)

    def test_a_superseded_revision_no_ops_and_the_revised_revision_derives_its_own_work(
            self, site, engine) -> None:  # noqa: F811
        settle(site)
        rev = site.on(POWER_DAY)
        late_mean(site, engine, rev)
        (ev,) = evidence_work(engine, site.site)
        nid = clone_revision(engine, rev)
        report = worker(site).run(site.tenant, site.site, limit=10)
        by_cause = {o.cause: o for o in report.outcomes}
        assert set(by_cause) == {"EVIDENCE_ACCEPTED", "FINDING_REVISION_APPENDED"}
        noop = by_cause["EVIDENCE_ACCEPTED"]
        assert (noop.succeeded, noop.no_op_reason, noop.consequence_revision_ids) == (True, NO_OP_SUPERSEDED, [])
        (att,) = attempts(engine, ev["id"])
        assert (att["outcome"], att["no_op_reason"], att["consequence_revision_ids"]) == (
            "SUCCEEDED", NO_OP_SUPERSEDED, [])
        assert len(consequences(engine, rev["id"])) == 1  # the old revision got no consequence n+1
        (own,) = consequences(engine, nid)
        assert by_cause["FINDING_REVISION_APPENDED"].appended == [own["id"]]
        assert report.counts()["no_op"] == 1

    def test_wrong_role_wrong_asset_and_outside_candidate_time_are_typed_no_ops(self, site, engine) -> None:  # noqa: F811
        """N7: an enqueued-but-irrelevant reading (another asset's generator power) is proved here, with role and
        Candidate-time no-ops, each by a test-written work row the trigger itself would not select."""
        settle(site)
        rev = site.on(POWER_DAY)
        a, b = candidate_spans(engine, rev)[0]
        # Wrong role: a pv interval mean inside Candidate time.
        pv = power(site, a, a + timedelta(minutes=5), device="pv-inverter-controller",
                   signal=site.runner.kit.binding("pv-inverter-controller")["signal_id"], epoch="epoch-pv-mean")
        assert [d.decision for d in submit(site, body(site, [pv])).receipt.dispositions] == ["ACCEPTED"]
        with engine.connect() as c:
            pv_id, pv_asset = c.execute(text(
                "SELECT id, asset_id FROM accepted_evidence WHERE site_id = :s AND interval_start = :a "
                "AND interval_end = :b AND role <> 'generator_power'"),
                {"s": site.site, "a": a, "b": a + timedelta(minutes=5)}).one()
        w_role = insert_evidence_work(engine, site, rev["finding_id"], rev["id"], pv_id, a, a + timedelta(minutes=5))
        # Wrong asset: the same Site's generator-power mean, against a Finding of another asset (cloned).
        power_id, start = late_mean(site, engine, rev)
        other_f, other_r = clone_finding(engine, rev, generator_asset_id=pv_asset)
        w_asset = insert_evidence_work(engine, site, other_f, other_r, power_id, start, start + timedelta(minutes=5))
        # Outside Candidate time: a generator-power mean of the right asset one day later.
        day_after = b + timedelta(days=1)
        far = submit(site, body(site, [power(site, day_after, day_after + timedelta(minutes=5))]))
        assert [d.decision for d in far.receipt.dispositions] == ["ACCEPTED"]
        far_id = accepted_id(engine, site.site, day_after, day_after + timedelta(minutes=5))
        w_far = insert_evidence_work(engine, site, rev["finding_id"], rev["id"], far_id, day_after,
                                     day_after + timedelta(minutes=5))
        before = {r: len(consequences(engine, r)) for r in (rev["id"], other_r)}
        report = worker(site).run(site.tenant, site.site, limit=50)
        reasons = {o.work_id: o.no_op_reason for o in report.outcomes}
        assert (reasons[w_role], reasons[w_asset], reasons[w_far]) == (NO_OP_ROLE, NO_OP_ASSET,
                                                                       NO_OP_OUTSIDE_CANDIDATE_TIME)
        for wid in (w_role, w_asset, w_far):
            (att,) = attempts(engine, wid)
            assert (att["outcome"], att["consequence_revision_ids"]) == ("SUCCEEDED", [])
        # Only the trigger's own work for the late mean derived (revision 2 of the real Finding).
        assert len(consequences(engine, rev["id"])) == before[rev["id"]] + 1
        assert len(consequences(engine, other_r)) == before[other_r] + 1  # its own FindingRevision work only

    def test_a_forged_cross_site_locator_is_refused_without_fallback(self, site, store, engine,
                                                                     monkeypatch) -> None:  # noqa: F811
        """C4, worker half."""
        from test_s1_bindings_postgres import FIXTURE, NOW, imported
        from test_s2_evidence_ledger_postgres import enable

        from assetops_backend.sites.binding_conversion import convert
        from assetops_backend.sites.binding_service import BindingService

        def site_b(store_, engine_):
            result = imported(store_, code="KOBO-002")
            outcome = convert(store_, BindingService(store_, Clock(NOW - timedelta(hours=1))), result.tenant,
                              result.site, {**FIXTURE, "site_code": "KOBO-002"})
            enable(engine_, result.site.id)
            return result, outcome

        settle(site)
        rev = site.on(POWER_DAY)
        late_mean(site, engine, rev)
        (real,) = site.store.pending_work(site.tenant, site.site)
        monkeypatch.setattr(finding_cases, "converted_enabled", site_b)
        monkeypatch.setattr(finding_cases, "DEMO", {**finding_cases.DEMO, "site_code": "KOBO-002"})
        b = PowerSite.__new__(PowerSite)
        b.runner = finding_cases.CaseRunner(store, engine)
        b.tenant, b.site = b.runner.tenant, b.runner.site
        a0, _ = candidate_spans(engine, rev)[0]
        submit(b, body(b, [power(b, a0, a0 + timedelta(minutes=5))]))
        foreign = accepted_id(engine, b.site, a0, a0 + timedelta(minutes=5))
        count = all_consequence_count(engine)
        w = worker(site)
        # A Site A work row whose locator is forged to name Site B's accepted reading.
        out = w.process(site.tenant, site.site, {**real, "accepted_evidence_id": foreign})
        assert (out.succeeded, out.error_code, out.no_op_reason) == (False, ERROR_EVIDENCE_LOCATOR_NOT_IN_SITE, None)
        # A Site A work row processed under Site B's scope: refused, and nothing recorded in either Site.
        out_b = w.process(b.tenant, b.site, real)
        assert (out_b.succeeded, out_b.error_code, out_b.attempt_no) == (False, ERROR_WORK_SCOPE_MISMATCH, 0)
        assert all_consequence_count(engine) == count
        (att,) = attempts(engine, real["id"])
        assert (att["outcome"], att["error_code"]) == ("FAILED", ERROR_EVIDENCE_LOCATOR_NOT_IN_SITE)


class TestRunner:
    def test_a_failure_is_retried_on_the_attempt_derived_schedule_against_an_injected_clock(
            self, site, engine) -> None:  # noqa: F811
        """N4: `finished_at` is the database clock, compared with the injected `now`; nothing sleeps."""
        settle(site)
        rev = site.on(POWER_DAY)
        late_mean(site, engine, rev)
        (w,) = evidence_work(engine, site.site)
        failing = FailFor(site.store, {rev["id"]})
        run = worker(site, store=failing).run
        t0 = datetime.now(timezone.utc)
        r1 = run(site.tenant, site.site, limit=10, now=t0)
        (o1,) = r1.outcomes
        assert (o1.succeeded, o1.error_code, o1.attempt_no) == (False, ERROR_STORE_UNAVAILABLE, 1)
        # Phase 2 review L1: the failed item stays in the backlog after the run that failed it.
        assert (r1.counts()["failed"], r1.counts()["backlog"]) == (1, 1)
        f1 = attempts(engine, w["id"])[-1]["finished_at"]
        early = run(site.tenant, site.site, limit=10, now=f1 + timedelta(seconds=59))
        assert early.counts() == {"selected": 0, "appended": 0, "replayed": 0, "no_op": 0, "failed": 0,
                                  "deferred": 1, "backlog": 1}
        (o2,) = run(site.tenant, site.site, limit=10, now=f1 + timedelta(minutes=1)).outcomes
        assert (o2.succeeded, o2.attempt_no) == (False, 2)
        f2 = attempts(engine, w["id"])[-1]["finished_at"]
        assert run(site.tenant, site.site, limit=10, now=f2 + timedelta(seconds=119)).counts()["deferred"] == 1
        (o3,) = run(site.tenant, site.site, limit=10, now=f2 + timedelta(minutes=2)).outcomes
        assert o3.attempt_no == 3
        f3 = attempts(engine, w["id"])[-1]["finished_at"]
        assert run(site.tenant, site.site, limit=10, now=f3 + timedelta(seconds=239)).counts()["deferred"] == 1
        failing.failing = False  # the source returns
        (o4,) = run(site.tenant, site.site, limit=10, now=f3 + timedelta(minutes=4)).outcomes
        assert o4.succeeded and o4.attempt_no == 4 and len(o4.appended) == 1
        assert [a["outcome"] for a in attempts(engine, w["id"])] == ["FAILED", "FAILED", "FAILED", "SUCCEEDED"]

    def test_failing_rows_never_starve_newer_work_under_limit(self, site, engine) -> None:  # noqa: F811
        """Phase 1 review L2: an old failing row competes by the instant it became eligible again."""
        settle(site)
        rev = site.on(POWER_DAY)
        late_mean(site, engine, rev)
        (old,) = evidence_work(engine, site.site)
        fid, rid = clone_finding(engine, rev)  # newer FindingRevision work, enqueued after the evidence row
        failing = FailFor(site.store, {rev["id"]})
        run = worker(site, store=failing).run
        (first,) = run(site.tenant, site.site, limit=1, now=datetime.now(timezone.utc)).outcomes
        assert (first.work_id, first.succeeded) == (old["id"], False)
        f1 = attempts(engine, old["id"])[-1]["finished_at"]
        # The old row is due again, but the newer row became eligible (enqueued) before its retry time.
        (second,) = run(site.tenant, site.site, limit=1, now=f1 + timedelta(minutes=5)).outcomes
        assert second.cause == "FINDING_REVISION_APPENDED" and second.succeeded
        (third,) = run(site.tenant, site.site, limit=1, now=f1 + timedelta(minutes=5)).outcomes
        assert third.work_id == old["id"]

    def test_a_second_runner_skips_the_claimed_site_and_a_killed_runners_claim_is_released(
            self, site, engine) -> None:  # noqa: F811
        """N3: the claim is a session lock on one dedicated connection; it dies with a killed process."""
        settle(site)
        rev = site.on(POWER_DAY)
        late_mean(site, engine, rev)
        with site.store.claim_site(site.tenant, site.site) as held:
            assert held
            skipped = worker(site).run(site.tenant, site.site, limit=10)
            assert (skipped.claimed, skipped.outcomes) == (False, [])
            # Phase 2 review L1: the claim is keyed per Site (the held lock is this Site's runner key), so a
            # claim on another Site is not blocked by it.
            with engine.connect() as c:
                assert c.execute(text(
                    "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND granted AND database = "
                    "(SELECT oid FROM pg_database WHERE datname = current_database()) AND objsubid = 1 AND "
                    "((classid::bigint << 32) | objid::bigint) = hashtextextended(:k, 0)"),
                    {"k": "financial_consequence_runner:" + str(site.site)}).scalar_one() == 1
            with site.store.claim_site(site.tenant, uuid4()) as other_site:
                assert other_site
        assert len(site.store.pending_work(site.tenant, site.site)) == 1
        code = ("import sys, time\n"
                "from uuid import UUID\n"
                "from assetops_backend.financials.adapters.postgres_consequence_store import "
                "PostgresConsequenceStore\n"
                "s = PostgresConsequenceStore(sys.argv[1])\n"
                "with s.claim_site(UUID(sys.argv[2]), UUID(sys.argv[3])) as h:\n"
                "    print('held' if h else 'not-held', flush=True)\n"
                "    time.sleep(300)\n")
        proc = subprocess.Popen([sys.executable, "-c", code, URL, str(site.tenant), str(site.site)],
                                cwd=str(BACKEND), stdout=subprocess.PIPE, text=True)
        try:
            assert proc.stdout.readline().strip() == "held"
            assert worker(site).run(site.tenant, site.site, limit=10).claimed is False
        finally:
            proc.kill()
            proc.wait(30)
        deadline, report = time.monotonic() + 30, None
        while time.monotonic() < deadline:
            report = worker(site).run(site.tenant, site.site, limit=10)
            if report.claimed:
                break
            time.sleep(0.2)
        assert report is not None and report.claimed, "a killed runner's Site claim was never released"
        assert report.counts()["appended"] == 1 and site.store.pending_work(site.tenant, site.site) == []
        with engine.connect() as c:
            held_now = c.execute(text(
                "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND granted AND database = "
                "(SELECT oid FROM pg_database WHERE datname = current_database()) AND objsubid = 1 AND "
                "((classid::bigint << 32) | objid::bigint) = hashtextextended(:k, 0)"),
                {"k": "financial_consequence_runner:" + str(site.site)}).scalar_one()
        assert held_now == 0  # the claim was unlocked in `finally`, not left on a pooled connection

    def test_a_bounded_batch_over_a_day_of_five_minute_means_across_findings(self, site, engine) -> None:  # noqa: F811
        """R2 (with phase 1 review I1/I2): ingestion chunk latency under the Site enqueue lock is logged, and
        the runner drains a backlog of hundreds of rows in bounded runs with exact counts and no duplicate basis."""
        settle(site)
        rev = site.on(POWER_DAY)
        day0 = POWER_DAY
        clones = [clone_finding(engine, rev, episode=(day0, day0 + timedelta(days=1))) for _ in range(2)]
        assert all(o.succeeded for o in worker(site).run_pending(site.tenant, site.site))
        means = [day0 + timedelta(minutes=5 * i) for i in range(288)]
        latencies = []
        for i in range(0, len(means), 48):
            chunk = [power(site, t, t + timedelta(minutes=5), epoch="epoch-day") for t in means[i:i + 48]]
            t = time.perf_counter()
            answer = submit(site, body(site, chunk))
            latencies.append(time.perf_counter() - t)
            assert {d.decision for d in answer.receipt.dispositions} == {"ACCEPTED"}
        rows = evidence_work(engine, site.site)
        in_episode = sum(1 for t in means if t < rev["episode_end"] and rev["episode_start"] < t + timedelta(minutes=5))
        assert len(rows) == 2 * 288 + in_episode
        print(f"R2 chunk latency (48 accepted generator-power means per chunk, {len(rows)} work rows): "
              + ", ".join(f"{x:.3f}s" for x in latencies))
        total, now, drained = len(rows), datetime.now(timezone.utc), 0
        first = worker(site).run(site.tenant, site.site, limit=100, now=now)
        c1 = first.counts()
        assert (c1["selected"], c1["failed"], c1["deferred"], c1["backlog"]) == (100, 0, 0, total - 100)
        drained += c1["selected"]
        t = time.perf_counter()
        while True:
            r = worker(site).run(site.tenant, site.site, limit=100, now=now).counts()
            assert r["failed"] == 0 and r["selected"] <= 100
            drained += r["selected"]
            if r["backlog"] == 0:
                break
        print(f"R2 drain: {drained} rows (incl. the first run of 100); the remaining {drained - c1['selected']} "
              f"drained in {time.perf_counter() - t:.1f}s")
        assert drained == total and site.store.pending_work(site.tenant, site.site) == []
        no_duplicate_basis(engine)
        with engine.connect() as c:
            noop = dict(c.execute(text(
                "SELECT a.no_op_reason, count(*) FROM financial_consequence_work_attempt a JOIN "
                "financial_consequence_work w ON w.id = a.work_id WHERE w.site_id = :s AND "
                "w.cause = 'EVIDENCE_ACCEPTED' GROUP BY 1"), {"s": site.site}).all())
        assert noop.get(NO_OP_OUTSIDE_CANDIDATE_TIME, 0) > 0 and sum(noop.values()) == total
        assert all(clones)
