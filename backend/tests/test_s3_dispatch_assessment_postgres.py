"""S3-01 phase 2: durable dispatch assessment over the S2 ledger (PostgreSQL).

Real Batch V2 ingestion into the ledger, then the recompute worker: two-cutoff
late acceptance, idempotent replay, the leased-job race, retry/failure and lost
lease, backdated configuration and model-version reconciliation, scoping and
append-only revisions. Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import Kit, _z, converted_enabled

    from assetops_backend.analytics import dispatch_v3
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.assessment_inputs import EvidenceQuery, Window
    from assetops_backend.analytics.assessment_worker import DISPATCH_ROLES, DispatchAssessmentWorker
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.sites.foundation_service import FoundationService

DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)
WINDOW = Window(DAY, DAY + timedelta(days=1)) if URL else None
T1 = datetime(2026, 10, 9, 8, 0, tzinfo=timezone.utc)
FEEDERS = ("residential-meter", "clinic-meter", "mill-meter")


def at(h: int, m: int = 0) -> datetime:
    return DAY + timedelta(hours=h, minutes=m)


class Feeder:
    """Seals one Batch V2 per source and ingests it through the S2 service at a chosen decision time."""

    def __init__(self, kit: "Kit") -> None:
        self.kit = kit
        self.seq: dict[tuple, int] = {}

    def deliver(self, rows, decided_at: datetime, epoch: str = "epoch-1") -> list[str]:
        by_device: dict[str, list[str]] = {}
        for device, signal, when, value in rows:
            source = self.kit.binding(device, signal)["source_id"]
            self.seq[(source, epoch)] = self.seq.get((source, epoch), 0) + 1
            by_device.setdefault(device, []).append(self.kit.envelope(
                device, self.seq[(source, epoch)], 0, value, source_time=_z(when), epoch=epoch,
                bound_signal=signal))
        ids = []
        service = BatchIngestionService(PostgresEvidenceLedger(URL), Clock(decided_at))
        for device, texts in by_device.items():
            answer = service.submit(self.kit.principal, self.kit.seal(texts, device_id=device).encode("utf-8"))
            assert answer.status == 200 and answer.receipt.status == "COMPLETED", answer
            ids.append(answer.receipt.batch_id)
        return ids


def interval_rows(h0: int, h1: int, soc: str = "80"):
    rows = [("generator-controller", "status", at(h0 - 1, 45), "STOPPED")]
    t = at(h0)
    while t <= at(h1):
        rows.append(("generator-controller", "status", t, "RUNNING"))
        rows += [(f, None, t, "10") for f in FEEDERS]
        rows.append(("battery-pcs-controller", "state-of-charge", t, soc))
        t += timedelta(minutes=15)
    rows.append(("generator-controller", "status", at(h1, 15), "STOPPED"))
    return rows


@pytest.fixture()
def site(store, engine):
    result, outcome = converted_enabled(store, engine)
    kit = Kit(engine, outcome.published.changed.id)
    return SimpleNamespace(kit=kit, feed=Feeder(kit), result=result, store=store, engine=engine,
                           tenant=kit.principal.tenant_id, site=kit.principal.site_id)


def worker(now: datetime, **options) -> DispatchAssessmentWorker:
    return DispatchAssessmentWorker(PostgresAssessmentStore(URL), clock=Clock(now), **options)


def rows(engine, sql: str, **params):
    with engine.connect() as c:
        return c.execute(text(sql), params).all()


def jobs(engine):
    return rows(engine, "SELECT status, attempts, window_start, window_end, last_error FROM recompute_job "
                        "ORDER BY created_at, id")


def revisions(engine, key_like: str):
    return rows(engine, "SELECT id, revision_no, analytic_run_id, claim_level, evidence_ids FROM assessment_revision "
                        "WHERE assessment_key LIKE :k ORDER BY revision_no", k=key_like)


class TestDurableAssessment:
    def test_late_central_acceptance_appends_revisions_and_keeps_the_old_ones(self, site) -> None:
        site.feed.deliver(interval_rows(5, 6), T1)
        [first] = worker(T1 + timedelta(minutes=1)).run_pending()
        assert first.status == "DONE", first.error
        assert first.status == "DONE" and first.runs and all(r.created for r in first.runs)
        run_a = next(r for r in first.runs if r.new_revision_ids)
        window_a = revisions(site.engine, "dispatch:window:2026-10-06%")
        interval_a = revisions(site.engine, "dispatch:interval:%")
        assert len(window_a) == 1 and len(interval_a) == 1

        cutoff_b = T1 + timedelta(hours=1)
        site.feed.deliver([("battery-pcs-controller", "state-of-charge", at(5, 40), "31")], cutoff_b)
        late_id = rows(site.engine, "SELECT e.id FROM accepted_evidence e JOIN ingestion_disposition d ON "
                                    "d.batch_id = e.batch_id AND d.ordinal = e.ordinal WHERE d.decided_at = :k",
                       k=cutoff_b)[0][0]
        assert [j[0] for j in jobs(site.engine)] == ["DONE", "PENDING"]
        [second] = worker(cutoff_b + timedelta(minutes=1)).run_pending()
        assert second.status == "DONE"
        window_b = revisions(site.engine, "dispatch:window:2026-10-06%")
        interval_b = revisions(site.engine, "dispatch:interval:%")
        assert [r[1] for r in window_b] == [1, 2] and [r[1] for r in interval_b] == [1, 2]
        assert window_b[0] == window_a[0] and interval_b[0] == interval_a[0]  # old revisions unchanged
        assert str(late_id) in interval_b[1][4] and str(late_id) not in interval_a[0][4]
        old_links = rows(site.engine, "SELECT assessment_revision_id FROM analytic_run_assessment WHERE run_id = :r",
                         r=run_a.run_id)
        assert {r[0] for r in old_links} == {window_a[0][0], interval_a[0][0]}

        # Replaying the first cutoff reproduces the first basis: no new run, no new revision.
        replay = worker(cutoff_b).compute(site.tenant, site.site, WINDOW, T1 + timedelta(minutes=1))
        assert replay.inputs.input_sha256 == rows(site.engine, "SELECT input_sha256 FROM analytic_run WHERE id = :r",
                                                  r=run_a.run_id)[0][0]
        again = PostgresAssessmentStore(URL).record_runs([replay], cutoff_b)
        assert again[0].run_id == run_a.run_id and not again[0].created

    def test_same_basis_reassessment_is_idempotent(self, site) -> None:
        site.feed.deliver(interval_rows(5, 6), T1)
        worker(T1 + timedelta(minutes=1)).run_pending()
        counts = rows(site.engine, "SELECT (SELECT count(*) FROM analytic_run), (SELECT count(*) FROM "
                                   "assessment_revision)")[0]
        store = PostgresAssessmentStore(URL)
        store.enqueue(site.tenant, site.site, "dispatch", WINDOW, T1 + timedelta(minutes=2))
        [outcome] = worker(T1 + timedelta(minutes=3)).run_pending()
        assert outcome.status == "DONE" and not any(r.created for r in outcome.runs)
        assert rows(site.engine, "SELECT (SELECT count(*) FROM analytic_run), (SELECT count(*) FROM "
                                 "assessment_revision)")[0] == counts

    def test_acceptance_racing_a_leased_job_stays_dirty_and_is_reassessed(self, site) -> None:
        site.feed.deliver(interval_rows(5, 6), T1)
        store = PostgresAssessmentStore(URL)
        w = worker(T1 + timedelta(minutes=1))
        lease = store.lease_job("dispatch", T1 + timedelta(minutes=1), timedelta(minutes=5))
        outputs = [w.compute(site.tenant, site.site, WINDOW, lease.knowledge_cutoff)]
        # A new acceptance lands while the job is leased: S2 coalesces only into PENDING jobs.
        site.feed.deliver([("battery-pcs-controller", "state-of-charge", at(5, 40), "31")], T1 + timedelta(minutes=2))
        assert [j[0] for j in jobs(site.engine)] == ["LEASED", "PENDING"]
        store.complete_job(lease, outputs, T1 + timedelta(minutes=3))
        assert [j[0] for j in jobs(site.engine)] == ["DONE", "PENDING"]  # the new event is not lost
        [outcome] = worker(T1 + timedelta(minutes=4)).run_pending()
        assert outcome.status == "DONE"
        assert [r[1] for r in revisions(site.engine, "dispatch:interval:%")] == [1, 2]

    def test_a_failed_run_retries_then_fails_with_its_reason(self, site) -> None:
        site.feed.deliver(interval_rows(5, 6), T1)
        calls = {"n": 0}

        def flaky(inputs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("transient analytic failure")
            return dispatch_v3.assess(inputs)

        model = SimpleNamespace(ANALYTIC_ID=dispatch_v3.ANALYTIC_ID, MODEL_VERSION=dispatch_v3.MODEL_VERSION,
                                assess=flaky)
        [o1] = worker(T1, model=model).run_pending()
        assert o1.status == "RETRY" and jobs(site.engine)[0][:2] == ("PENDING", 1)
        assert "transient analytic failure" in jobs(site.engine)[0][4]
        assert rows(site.engine, "SELECT count(*) FROM analytic_run")[0][0] == 0
        assert worker(T1, model=model).run_pending() == []  # backing off
        [o2] = worker(T1 + timedelta(minutes=5), model=model).run_pending()
        assert o2.status == "DONE" and jobs(site.engine)[0][:2] == ("DONE", 2)

        broken = SimpleNamespace(ANALYTIC_ID="dispatch", MODEL_VERSION=dispatch_v3.MODEL_VERSION,
                                 assess=lambda inputs: 1 / 0)
        PostgresAssessmentStore(URL).enqueue(site.tenant, site.site, "dispatch", WINDOW, T1 + timedelta(minutes=6))
        clock = T1 + timedelta(minutes=6)
        statuses = []
        for _ in range(3):
            statuses += [o.status for o in worker(clock, model=broken, max_attempts=3).run_pending()]
            clock += timedelta(hours=1)
        assert statuses == ["RETRY", "RETRY", "FAILED"]
        assert jobs(site.engine)[-1][0] == "FAILED" and "ZeroDivisionError" in jobs(site.engine)[-1][4]

    def test_a_lost_lease_commits_nothing(self, site) -> None:
        site.feed.deliver(interval_rows(5, 6), T1)
        store = PostgresAssessmentStore(URL)
        slow = store.lease_job("dispatch", T1, timedelta(seconds=10))
        out = worker(T1).compute(site.tenant, site.site, WINDOW, slow.knowledge_cutoff)
        [taken] = worker(T1 + timedelta(minutes=1)).run_pending()  # lease expired: another worker takes it
        assert taken.status == "DONE"
        from assetops_backend.analytics.assessment_ports import LeaseLost
        with pytest.raises(LeaseLost):
            store.complete_job(slow, [out], T1 + timedelta(minutes=2))
        assert rows(site.engine, "SELECT count(*) FROM analytic_run")[0][0] == 1

    def test_a_lease_that_always_expires_reaches_failed(self, site) -> None:
        """Phase-2 review F6: an expired lease on the last allowed attempt is FAILED, not re-leased."""
        site.feed.deliver(interval_rows(5, 6), T1)
        store = PostgresAssessmentStore(URL)
        now = T1
        for attempt in (1, 2, 3):
            lease = store.lease_job("dispatch", now, timedelta(seconds=10), max_attempts=3)
            assert lease is not None and lease.attempts == attempt
            now += timedelta(minutes=1)  # the worker never completes: its lease expires
        assert store.lease_job("dispatch", now, timedelta(seconds=10), max_attempts=3) is None
        [(status, attempts, _, _, error)] = jobs(site.engine)
        assert (status, attempts) == ("FAILED", 3) and "lease expired on attempt 3 of 3" in error

    def test_backdated_configuration_and_model_version_schedule_reassessment(self, site) -> None:
        site.feed.deliver(interval_rows(5, 6), T1)
        worker(T1 + timedelta(minutes=1)).run_pending()
        assert worker(T1 + timedelta(minutes=2)).reconcile(site.tenant, site.site) == []
        FoundationService(site.store, "demo", Clock(T1 + timedelta(minutes=3))).publish_battery_reserve(
            site.result.tenant, site.result.site, asset_code="battery", value=40.0,
            effective_from=datetime(2026, 10, 5, tzinfo=timezone.utc), note="backdated reserve")
        scheduled = worker(T1 + timedelta(minutes=4)).reconcile(site.tenant, site.site)
        assert WINDOW in scheduled
        worker(T1 + timedelta(minutes=5)).run_pending()
        window = revisions(site.engine, "dispatch:window:2026-10-06%")
        assert len(window) == 2
        reserve = rows(site.engine, "SELECT foundation_revision_ids FROM analytic_run ORDER BY completed_at DESC "
                                    "LIMIT 1")[0][0]
        assert reserve != rows(site.engine, "SELECT foundation_revision_ids FROM analytic_run ORDER BY completed_at "
                                            "LIMIT 1")[0][0]
        assert worker(T1 + timedelta(minutes=6)).reconcile(site.tenant, site.site) == []

        shadow = SimpleNamespace(ANALYTIC_ID="dispatch", MODEL_VERSION="dispatch-3-shadow",
                                 assess=dispatch_v3.assess)
        assert WINDOW in worker(T1 + timedelta(minutes=7), model=shadow).reconcile(site.tenant, site.site)

    def test_the_query_is_tenant_and_site_scoped_and_cut_at_knowledge(self, site) -> None:
        site.feed.deliver(interval_rows(5, 6), T1)
        store = PostgresAssessmentStore(URL)
        ok = store.query_evidence(EvidenceQuery(site.tenant, site.site, "dispatch", WINDOW, T1, roles=DISPATCH_ROLES))
        assert ok.readings and {r.role for r in ok.readings} <= set(DISPATCH_ROLES)
        assert all(r.accepted_at <= T1 for r in ok.readings)
        assert ok.controls and ok.bindings
        before = store.query_evidence(EvidenceQuery(site.tenant, site.site, "dispatch", WINDOW,
                                                    T1 - timedelta(seconds=1)))
        assert before.readings == ()
        other = store.query_evidence(EvidenceQuery(uuid4(), site.site, "dispatch", WINDOW, T1))
        assert other.readings == () and other.controls == () and other.bindings == ()

    def test_runs_and_revisions_are_append_only(self, site) -> None:
        site.feed.deliver(interval_rows(5, 6), T1)
        worker(T1 + timedelta(minutes=1)).run_pending()
        for table in ("analytic_run", "assessment_revision", "analytic_run_evidence", "analytic_run_assessment"):
            with pytest.raises(DBAPIError):
                with site.engine.begin() as c:
                    c.execute(text(f"DELETE FROM {table}"))
