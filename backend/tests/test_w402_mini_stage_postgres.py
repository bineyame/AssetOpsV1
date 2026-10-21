"""W4-02 q7 rulings 1-4 against PostgreSQL: four-domain live mini-job discovery, the tick's real MINI stage on
MG-W402-001 (order, count budget, token-scoped counters, report), a decommissioned Site kept for its mini work, the
canonical digest and reuse (R1), a refused input set retried then FAILED with no revision (R2), and explicit
reconcile hours, domains and cutoffs with job rows unchanged (R3). Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
import re
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import enable
    from test_s4_consequence_store_postgres import site  # noqa: F401
    from test_s4_schedule_tick_postgres import FAST, InProcessRunner, make_tick
    from test_w203_cold_migration_postgres import _replica
    from test_w402_authored_v4_postgres import RECEIVED, cases, ingestion, install, principal, snapshot
    from test_w402_migration_postgres import mg, revision  # noqa: F401
    from test_w402_mini_lease_postgres import job

    from assetops_backend.analytics import dispatch_v3
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.mini_depth.inputs import local_noon
    from assetops_backend.mini_depth.store import PostgresMiniDepthStore
    from assetops_backend.mini_depth.worker import MiniDepthWorker
    from assetops_backend.scheduling.tick import TickLimits, select_sites

UTC = timezone.utc
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
TZ = "Africa/Nairobi"


def ids(rows) -> set:
    return {r["id"] for r in rows}


def test_live_mini_jobs_four_domains_and_failed_supersession(mg, engine) -> None:  # noqa: F811
    """q7 ruling 2: PENDING/LEASED live; FAILED live until a later selection of the same Site, domain and an
    overlapping hour; an earlier selection, another domain or a disjoint hour cannot clear it; dispatch-only
    `live_jobs` never shows mini work."""
    store = PostgresAssessmentStore(URL)
    lo = datetime(2026, 10, 6, 9, tzinfo=UTC)
    other = None
    try:
        sel = PostgresMiniDepthStore(engine).append_selection(
            revision(mg.ctx, lo=lo, hi=lo + timedelta(hours=1), domain="service"), job_id=None, backfill=True)
        with engine.connect() as c:
            selected_at = c.execute(text("SELECT selected_at FROM mini_depth_selection WHERE seq = :q"),
                                    {"q": sel.seq}).scalar_one()
        pending = job(engine, mg.ctx, "mini_backup", lo)
        before = job(engine, mg.ctx, "mini_service", lo, available=selected_at - timedelta(minutes=1))
        after = job(engine, mg.ctx, "mini_service", lo, available=selected_at + timedelta(minutes=1))
        other_domain = job(engine, mg.ctx, "mini_fuel", lo, available=selected_at - timedelta(minutes=1))
        disjoint = job(engine, mg.ctx, "mini_service", lo + timedelta(hours=2),
                       available=selected_at - timedelta(minutes=1))
        failed = [before, after, other_domain, disjoint]
        _replica(engine, "UPDATE recompute_job SET status = 'FAILED', attempts = 3 WHERE id IN ("
                 + ", ".join(f"'{j}'" for j in failed) + ")")
        live = store.live_mini_jobs(mg.ctx.t, mg.ctx.s)
        assert ids(live) == {pending, after, other_domain, disjoint}  # `before` is superseded by the selection
        assert {r["domain"] for r in live} == {"mini_backup", "mini_service", "mini_fuel"}
        assert ids(store.live_mini_jobs()) >= ids(live)
        assert not ids(store.live_jobs(dispatch_v3.ANALYTIC_ID, "dispatch", mg.ctx.t, mg.ctx.s)) & ids(live)
        order = [(r["available_at"], r["created_at"]) for r in live]
        assert order == sorted(order)

        # q8 ruling 4: a later selection of ANOTHER Site (same tenant, domain and overlapping hour) supersedes none
        # of this Site's FAILED jobs, and a FAILED-only Site is not made schedulable (q8 ruling 2).
        other = _other_site(engine, mg.ctx)
        sel2 = PostgresMiniDepthStore(engine).append_selection(
            revision(SimpleNamespace(t=mg.ctx.t, s=other), lo=lo, hi=lo + timedelta(hours=1), domain="service",
                     digest="b"), job_id=None, backfill=True)
        with engine.connect() as c:
            other_at = c.execute(text("SELECT selected_at FROM mini_depth_selection WHERE seq = :q"),
                                 {"q": sel2.seq}).scalar_one()
        assert other_at > selected_at
        across = job(engine, mg.ctx, "mini_service", lo, available=selected_at + (other_at - selected_at) / 2)
        _replica(engine, f"UPDATE recompute_job SET status = 'FAILED', attempts = 3, last_error = 'boom' "
                         f"WHERE id = '{across}'")
        live = store.live_mini_jobs(mg.ctx.t, mg.ctx.s)
        assert across in ids(live) and after in ids(live)
        failed_only = [r for r in live if r["status"] == "FAILED"]
        assert failed_only and {r["last_error"] for r in failed_only if r["id"] == across} == {"boom"}
        inventory = [{"tenant_id": mg.ctx.t, "site_id": mg.ctx.s, "site_code": "ORIG", "lifecycle": "DECOMMISSIONED",
                      "has_evidence": True, "enrolled": False}]
        assert select_sites({"inventory": inventory, "live_jobs": [], "live_mini_jobs": failed_only,
                             "pending_work_sites": []}) == ([], [], 1)
    finally:
        if other is not None:
            _replica(engine, f"DELETE FROM mini_depth_selection WHERE site_id = '{other}'",
                     f"DELETE FROM mini_depth_revision WHERE site_id = '{other}'",
                     f"DELETE FROM site WHERE id = '{other}'")
        store._connect_engine().dispose()


def _other_site(engine, ctx):  # noqa: F811
    """A second MINIGRID Site of the same tenant (test-only row copied from the fixture Site)."""
    other = uuid4()
    code = f"W402-OTHER-{other.hex[:8]}"
    _replica(engine, "INSERT INTO site (id, tenant_id, site_code, site_code_key, name, site_type, timezone, lifecycle, "
                     "country, locality, origin, proposed_source_mode, template_id, template_version, created_at) "
                     f"SELECT '{other}', tenant_id, '{code}', '{code.lower()}', name, site_type, timezone, lifecycle, "
                     "country, locality, origin, proposed_source_mode, template_id, template_version, created_at "
                     f"FROM site WHERE id = '{ctx.s}'")
    return other


def _installed(store, engine):  # noqa: F811
    installed = install(store)
    tenant_id, site_id = installed.result.site.tenant_id, installed.result.site.id
    enable(engine, site_id)
    doc, sha = snapshot(engine, installed.binding_set.id)
    service = ingestion()
    for b in cases.build_batches(cases.load_spec(), doc, sha, "positive"):
        service.submit(principal(doc), b.body.encode("utf-8"))
    return tenant_id, site_id


def _rows(engine, sql, **p) -> list[dict]:  # noqa: F811
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(sql), p)]


def test_tick_runs_the_mini_stage_between_s3_and_s4(store, engine) -> None:  # noqa: F811
    """q7 rulings 1-3: the tick's MINI stage leases at most ten of this Site's mini jobs between S3 and S4, writes
    the three counters under the Site claim and reports them; a decommissioned Site with only mini work is still
    visited as EXCLUDED_WITH_WORK and named in the excluded diagnostics."""
    tenant_id, site_id = _installed(store, engine)
    live_before = len(_rows(engine, "SELECT id FROM recompute_job WHERE site_id = :s AND domain LIKE 'mini\\_%' "
                                    "AND status = 'PENDING'", s=site_id))
    assert live_before > 10
    tick, runner = make_tick(TickLimits(**FAST))
    report = tick.tick()
    assert report.outcome == "COMPLETED", report.failure
    [site_result] = [s for s in report.selected if s.site_id == site_id]
    assert [c for c, s in runner.calls if s in (None, str(site_id))] == ["discover", "s3", "mini", "s4", "consequence"]
    mini = site_result.stages["mini"]
    assert mini["code"] == "OK" and mini["processed"] == 10 and mini["failed"] == 0, mini
    assert mini["deferred"] == live_before - 10
    assert site_result.failure is None or site_result.failure[0] != "MINI", site_result.failure
    head = tick.store.site_head(tenant_id, site_id)
    assert (head["mini_processed"], head["mini_deferred"], head["mini_failed"]) == (10, live_before - 10, 0)
    assert head["stage"] == "IDLE" and head["claim_token"] is None
    as_json = [s for s in report.as_json()["sites"] if s["site_id"] == str(site_id)][0]
    assert {k: as_json["stages"]["mini"][k] for k in ("code", "processed", "deferred", "failed")} == {
        "code": "OK", "processed": 10, "deferred": live_before - 10, "failed": 0}
    done = _rows(engine, "SELECT j.id, r.input_sha256 FROM recompute_job j JOIN mini_depth_selection s ON "
                         "s.job_id = j.id JOIN mini_depth_revision r ON r.id = s.revision_id "
                         "WHERE j.site_id = :s AND j.status = 'DONE'", s=site_id)
    assert len(done) == 10 and all(DIGEST.match(d["input_sha256"]) for d in done)  # q7 R1

    # Decommissioned, with only mini work left: still visited, reported with its mini jobs.
    _replica(engine, f"DELETE FROM recompute_job WHERE site_id = '{site_id}' AND domain = 'dispatch'",
             f"UPDATE site SET lifecycle = 'DECOMMISSIONED' WHERE id = '{site_id}'")
    again, runner2 = make_tick(TickLimits(**FAST), env=tick.environment)
    report2 = again.tick()
    assert report2.outcome == "COMPLETED", report2.failure
    [visited] = [s for s in report2.selected if s.site_id == site_id]
    assert visited.reason == "EXCLUDED_WITH_WORK" and visited.stages["mini"]["processed"] == 10
    [excluded] = [e for e in report2.excluded_with_work if e["site_id"] == str(site_id)]
    assert excluded["lifecycle"] == "DECOMMISSIONED" and excluded["live_jobs"] == []
    assert len(excluded["live_mini_jobs"]) == live_before - 10
    assert ("mini", str(site_id)) in runner2.calls
    assert ("s4", str(site_id)) in runner2.calls and "s4" in visited.stages  # q8 ruling 2: S4 may run on the visit

    # q8 ruling 2: only terminal FAILED mini work left -> not selected, no MINI or S4; the rows stay queryable.
    _replica(engine, f"UPDATE recompute_job SET status = 'FAILED', attempts = 3, last_error = 'terminal' "
                     f"WHERE site_id = '{site_id}' AND domain LIKE 'mini\\_%' AND status IN ('PENDING', 'LEASED')")
    third, runner3 = make_tick(TickLimits(**FAST), env=tick.environment)
    report3 = third.tick()
    assert report3.outcome == "COMPLETED", report3.failure
    assert not [s for s in report3.selected if s.site_id == site_id]
    assert not [e for e in report3.excluded_with_work if e["site_id"] == str(site_id)]
    assert not [c for c, s in runner3.calls if s == str(site_id)]
    terminal = _rows(engine, "SELECT status, attempts, last_error FROM recompute_job WHERE site_id = :s "
                             "AND domain LIKE 'mini\\_%' AND last_error = 'terminal'", s=site_id)
    assert terminal
    assert {(t["status"], t["attempts"], t["last_error"]) for t in terminal} == {("FAILED", 3, "terminal")}
    reader = PostgresAssessmentStore(URL)
    try:  # q8 ruling 2: still returned for diagnostic/currentness reads
        live = reader.live_mini_jobs(tenant_id, site_id)
        assert live and all(r["status"] == "FAILED" for r in live)
    finally:
        reader._connect_engine().dispose()


def test_worker_digest_reuse_refusal_retry_and_reconcile(store, engine) -> None:  # noqa: F811
    """q7 R1-R3 on MG-W402-001."""
    tenant_id, site_id = _installed(store, engine)
    _replica(engine, f"DELETE FROM recompute_job WHERE site_id = '{site_id}' AND domain LIKE 'mini\\_%'")
    ctx = type("Ctx", (), {"t": tenant_id, "s": site_id})
    jobs, mini = PostgresAssessmentStore(URL), PostgresMiniDepthStore(engine)
    noon = local_noon(date(2026, 10, 6), TZ)
    T = RECEIVED + timedelta(days=1)
    try:
        # R1: one exact digest form, and the second job at the same cutoff reuses the stored revision.
        first, second = (job(engine, ctx, "mini_service", noon.start, available=T - timedelta(minutes=m))
                         for m in (2, 1))
        out = MiniDepthWorker(jobs, mini, test_lease_clock=lambda: T).run_pending(5, tenant_id, site_id)
        assert [(o.job_id, o.status) for o in out] == [(first, "DONE"), (second, "DONE")], [o.error for o in out]
        assert (out[0].selection.reused, out[1].selection.reused) == (False, True)
        assert out[0].selection.revision_id == out[1].selection.revision_id
        [digest] = {r["input_sha256"] for r in _rows(engine, "SELECT input_sha256 FROM mini_depth_revision "
                                                             "WHERE site_id = :s", s=site_id)}
        assert DIGEST.match(digest)

        # R2: a refused input set fails the job with its typed code, retried with back-off, then FAILED; no
        # revision or selection is appended for that hour.
        old = job(engine, ctx, "mini_fuel", datetime(2020, 1, 1, 9, tzinfo=UTC), available=T)
        seen = []
        for k in range(3):
            clock = T + timedelta(hours=k + 1)
            [o] = MiniDepthWorker(jobs, mini, test_lease_clock=lambda c=clock: c).run_pending(5, tenant_id, site_id)
            [st] = _rows(engine, "SELECT status, attempts, available_at, last_error FROM recompute_job "
                                 "WHERE id = :j", j=old)
            seen.append((o.status, st["status"], st["attempts"], st["last_error"].split(":")[0]))
            if k < 2:
                assert st["available_at"] > clock  # back-off
        assert seen == [("RETRY", "PENDING", 1, "CONFIGURATION_MISSING"),
                        ("RETRY", "PENDING", 2, "CONFIGURATION_MISSING"),
                        ("FAILED", "FAILED", 3, "CONFIGURATION_MISSING")]
        assert not _rows(engine, "SELECT id FROM mini_depth_revision WHERE site_id = :s AND window_start < :y",
                         s=site_id, y=datetime(2021, 1, 1, tzinfo=UTC))

        # R3: explicit reconcile over a partial boundary: local 11:00 and 12:00 only, renewable at noon only, one
        # DB cutoff per hour, backfill selections without job IDs, job rows unchanged.
        job_rows = _rows(engine, "SELECT * FROM recompute_job WHERE site_id = :s ORDER BY id", s=site_id)
        code = _rows(engine, "SELECT site_code FROM site WHERE id = :s", s=site_id)[0]["site_code"]
        done = MiniDepthWorker(jobs, mini).reconcile(code, noon.start - timedelta(minutes=90),
                                                     noon.end + timedelta(minutes=30))
        by_hour: dict = {}
        for o in done:
            by_hour.setdefault(o.window.start, []).append(o)
        assert sorted(by_hour) == [noon.start - timedelta(hours=1), noon.start]
        assert sorted(o.domain for o in by_hour[noon.start - timedelta(hours=1)]) == ["backup", "fuel", "service"]
        assert sorted(o.domain for o in by_hour[noon.start]) == ["backup", "fuel", "renewable", "service"]
        cutoffs = [{o.knowledge_cutoff for o in by_hour[h]} for h in sorted(by_hour)]
        assert [len(c) for c in cutoffs] == [1, 1] and min(cutoffs[0]) < min(cutoffs[1])
        assert all(o.job_id is None and o.status == "DONE" and o.selection.seq for o in done)
        assert _rows(engine, "SELECT * FROM recompute_job WHERE site_id = :s ORDER BY id", s=site_id) == job_rows
    finally:
        jobs._connect_engine().dispose()
