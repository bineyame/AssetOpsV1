"""S3-01 phase 2: durable dispatch assessment over the S2 ledger (PostgreSQL).

Real Batch V2 ingestion into the ledger, then the recompute worker: two-cutoff
late acceptance, idempotent replay, the leased-job race, retry/failure and lost
lease, backdated configuration and model-version reconciliation, scoping and
append-only revisions. Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

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
    from assetops_backend import record_clock_attestation as record_cli
    from assetops_backend.analytics.assessment_worker import DISPATCH_ROLES, DispatchAssessmentWorker, day_windows
    from assetops_backend.analytics.clock_attestation import (
        SYSTEM_ATTESTER,
        AttestationChange,
        AttestationRefused,
        AttesterPrincipal,
    )
    from assetops_backend.analytics.dispatch_read import STALE, DispatchReadService
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
        for device, signal, when, value, *explicit in rows:
            # An explicit fifth element is the source's own sequence number (on-time sequencing); otherwise the
            # next one on intake, as this project's gateway numbers a delayed reading.
            source = self.kit.binding(device, signal)["source_id"]
            seq = explicit[0] if explicit else self.seq.get((source, epoch), 0) + 1
            self.seq[(source, epoch)] = max(seq, self.seq.get((source, epoch), 0))
            by_device.setdefault(device, []).append(self.kit.envelope(
                device, seq, 0, value, source_time=_z(when), epoch=epoch, bound_signal=signal))
        ids = []
        # S4-07: fixture ordering pins the decision instant through the test-only override (never production).
        service = BatchIngestionService(
            PostgresEvidenceLedger(URL, test_decision_clock_override=Clock(decided_at)), Clock(decided_at))
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
    # W4-02 q1 ruling 2: dispatch jobs only; this MINIGRID Site also enqueues 0029 mini work.
    return rows(engine, "SELECT status, attempts, window_start, window_end, last_error FROM recompute_job "
                        "WHERE domain = 'dispatch' ORDER BY created_at, id")


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


# --- LR-01 phase 1: clock attestations, source-time reassessment and affected-window requeue -----------------

ATTEST_ERROR = timedelta(seconds=30)


def gen_source(site) -> str:
    return site.kit.binding("generator-controller", "status")["source_id"]


def attest(site, now, *, kind="RECORDED", key="a1", lo=None, hi=None, attestation=None, expected=None,
           principal=None, reason=None, epoch="epoch-1", error=ATTEST_ERROR):
    change = AttestationChange(
        event_kind=kind, source_id=UUID(gen_source(site)), sequence_epoch=epoch, idempotency_key=key,
        channel="SYSTEM_CLI", authority="lab-simulated-clock" if kind in ("RECORDED", "REPLACED") else None,
        label="SIMULATED demonstration clock (LR-01)" if kind in ("RECORDED", "REPLACED") else None,
        max_utc_error=error if kind in ("RECORDED", "REPLACED") else None,
        valid_from=lo if kind in ("RECORDED", "REPLACED") else None, valid_to=hi, attestation_id=attestation,
        expected_version=expected, reason=reason)
    return PostgresAssessmentStore(URL).record_clock_attestation(site.tenant, site.site, change,
                                                                 principal or SYSTEM_ATTESTER, now)


def window_head(site, window=None):
    """(run id, input sha, window claim, limitations, cohort payload) of the latest DEFAULT selection."""
    w = window or WINDOW
    run_id, sha, cohort = rows(site.engine, "SELECT r.id, r.input_sha256, r.cohort FROM analytic_run_selection x "
                                            "JOIN analytic_run r ON r.id = x.run_id WHERE x.window_start = :ws "
                                            "ORDER BY x.seq DESC LIMIT 1", ws=w.start)[0]
    claim, result = rows(site.engine, "SELECT v.claim_level, v.result FROM analytic_run_assessment l JOIN "
                                      "assessment_revision v ON v.id = l.assessment_revision_id WHERE l.run_id = :r "
                                      "AND l.scope = 'WINDOW'", r=run_id)[0]
    return run_id, sha, claim, result["limitations"], cohort


def status_rows(skip=()):
    """The generator status rows of `interval_rows(5, 6)` with their on-time sequence numbers."""
    out = [r for r in interval_rows(5, 6) if r[0] == "generator-controller"]
    return [(*r, i + 1) for i, r in enumerate(out) if i + 1 not in skip]


class TestClockAttestation:
    LATE = at(5, 30)

    def _run_one(self, site):
        """Run 1: the 05:30 generator status arrives late and the gateway sequences it on intake."""
        rest = [r for r in interval_rows(5, 6) if not (r[0] == "generator-controller" and r[2] == self.LATE)]
        site.feed.deliver(rest, T1)
        worker(T1 + timedelta(minutes=1)).run_pending()
        site.feed.deliver([("generator-controller", "status", self.LATE, "RUNNING")], T1 + timedelta(hours=1))
        worker(T1 + timedelta(hours=1, minutes=1)).run_pending()

    def test_run_one_withheld_then_attested_is_pending_then_reassessed_in_source_order(self, site) -> None:
        self._run_one(site)
        run_b, sha_b, claim_b, limits_b, cohort_b = window_head(site)
        assert claim_b == dispatch_v3.WINDOW_INDETERMINATE
        assert any(x.startswith("GENERATOR_SERIES_AMBIGUOUS") for x in limits_b)
        assert any(x.startswith("SEQUENCE_ORDER_INVERTED: generator_state") and "clock NO_ATTESTATION" in x
                   for x in limits_b)
        assert cohort_b["rules"] == "cohort-4" and cohort_b["clock_basis"] == []
        history = rows(site.engine, "SELECT id, revision_no, basis_sha256 FROM assessment_revision ORDER BY id")
        selections = rows(site.engine, "SELECT seq, run_id FROM analytic_run_selection ORDER BY seq")

        out = attest(site, T1 + timedelta(hours=2), lo=at(0), hi=at(23))
        event = out["event"]
        assert out["created"] and (event.version, event.event_kind) == (1, "RECORDED")
        assert [(w.start, w.end) for w in out["requeued"]] == [(at(4, 45), at(6, 15) + timedelta(microseconds=1))]
        assert [j[0] for j in jobs(site.engine)][-1] == "PENDING"
        # Pending: the selected run is stale (the attestation changes the input basis) while work is queued.
        read = DispatchReadService(PostgresAssessmentStore(URL)).window(site.tenant, site.site, DAY.date())
        assert read["status"] == STALE
        assert any(r.startswith("INPUT_BASIS_CHANGED") for r in read["status_reasons"])
        assert any(r.startswith("RECOMPUTE_OUTSTANDING") for r in read["status_reasons"])
        assert window_head(site)[0] == run_b

        worker(T1 + timedelta(hours=3)).run_pending()
        run_c, sha_c, claim_c, limits_c, cohort_c = window_head(site)
        assert run_c != run_b and sha_c != sha_b
        assert claim_c != dispatch_v3.WINDOW_INDETERMINATE
        assert not any(x.startswith(("GENERATOR_SERIES_AMBIGUOUS", "SEQUENCE_ORDER_INVERTED")) for x in limits_c)
        assert [(b["attestation_id"], b["version"], b["event_id"]) for b in cohort_c["clock_basis"]] == [
            (str(event.attestation_id), 1, str(event.event_id))]
        # Append-only: every earlier revision and selection is unchanged; the new run is a new selection.
        after = {r[0]: r for r in rows(site.engine, "SELECT id, revision_no, basis_sha256 FROM assessment_revision")}
        assert all(after[r[0]] == r for r in history)
        assert rows(site.engine, "SELECT seq, run_id FROM analytic_run_selection ORDER BY seq")[:len(selections)] \
            == selections
        assert rows(site.engine, "SELECT run_id FROM analytic_run_selection ORDER BY seq DESC LIMIT 1")[0][0] == run_c

        # Replay at run 1's cutoff (before the attestation) reproduces its basis and reuses its run.
        cutoff_b = rows(site.engine, "SELECT knowledge_cutoff FROM analytic_run WHERE id = :r", r=run_b)[0][0]
        replay = worker(T1 + timedelta(hours=4)).compute(site.tenant, site.site, WINDOW, cutoff_b)
        assert replay.inputs.input_sha256 == sha_b
        assert PostgresAssessmentStore(URL).record_runs([replay], T1 + timedelta(hours=4))[0].run_id == run_b

        # Idempotent: the same request answers the stored event and queues nothing; a settled pass is a no-op.
        again = attest(site, T1 + timedelta(hours=5), lo=at(0), hi=at(23))
        assert not again["created"] and again["event"].event_id == event.event_id and again["requeued"] == []
        counts = rows(site.engine, "SELECT (SELECT count(*) FROM analytic_run), (SELECT count(*) FROM "
                                   "assessment_revision), (SELECT count(*) FROM source_clock_attestation)")[0]
        assert all(not r.created for o in worker(T1 + timedelta(hours=5)).run_pending() for r in o.runs)
        assert rows(site.engine, "SELECT (SELECT count(*) FROM analytic_run), (SELECT count(*) FROM "
                                 "assessment_revision), (SELECT count(*) FROM source_clock_attestation)")[0] == counts
        with pytest.raises(AttestationRefused) as conflict:
            attest(site, T1 + timedelta(hours=5), lo=at(0), hi=at(22))
        assert conflict.value.code == "IDEMPOTENCY_CONFLICT"

    def test_on_time_sequenced_late_upload_under_attestation_is_one_series(self, site) -> None:
        others = [r for r in interval_rows(5, 6) if r[0] != "generator-controller"]
        site.feed.deliver(others + status_rows(skip=(4,)), T1)  # 05:30 is sequence 4, withheld
        attest(site, T1 + timedelta(minutes=1), lo=at(0), hi=at(23))
        site.feed.deliver([r for r in status_rows() if r[4] == 4], T1 + timedelta(hours=1))
        worker(T1 + timedelta(hours=1, minutes=1)).run_pending()
        _, _, claim, limits, cohort = window_head(site)
        assert claim != dispatch_v3.WINDOW_INDETERMINATE and len(cohort["clock_basis"]) == 1
        assert not any(x.startswith(("GENERATOR_SERIES_AMBIGUOUS", "SEQUENCE_ORDER_INVERTED", "REPORTS_OVERLAP"))
                       for x in limits)

    def test_simulated_data_without_attestation_stays_limited(self, site) -> None:
        self._run_one(site)
        attest(site, T1 + timedelta(hours=2), lo=at(0), hi=at(23), epoch="another-epoch")  # proves nothing here
        worker(T1 + timedelta(hours=3)).run_pending()
        _, _, claim, limits, _ = window_head(site)
        assert claim == dispatch_v3.WINDOW_INDETERMINATE
        assert any(x.startswith("GENERATOR_SERIES_AMBIGUOUS") for x in limits)

    def test_an_attestation_not_touching_a_limited_window_leaves_it_current(self, site) -> None:
        # Phase-1 review F1: the stream's FIRST attestation, and revoking its LAST, both elsewhere in time (two
        # days later), neither change the limited window's input basis nor leave it stale without work.
        self._run_one(site)
        run_b, sha_b, claim_b, _, _ = window_head(site)
        assert claim_b == dispatch_v3.WINDOW_INDETERMINATE
        later = timedelta(days=2)

        def read():
            return DispatchReadService(PostgresAssessmentStore(URL)).window(site.tenant, site.site, DAY.date())

        created = attest(site, T1 + timedelta(hours=2), key="far", lo=at(0) + later, hi=at(23) + later)["event"]
        worker(T1 + timedelta(hours=2, minutes=1)).run_pending()
        r = read()
        assert (r["status"], r["status_reasons"]) == ("CURRENT", []), r["status_reasons"]
        assert window_head(site)[:2] == (run_b, sha_b)
        attest(site, T1 + timedelta(hours=3), kind="REVOKED", key="far-v", reason="withdrawn",
               attestation=created.attestation_id, expected=1)
        worker(T1 + timedelta(hours=3, minutes=1)).run_pending()
        r = read()
        assert (r["status"], r["status_reasons"]) == ("CURRENT", []), r["status_reasons"]
        assert window_head(site)[:2] == (run_b, sha_b)

    def test_creation_replacement_expiry_and_revocation_requeue_old_and_new_validity(self, site) -> None:
        day3 = timedelta(days=2)
        site.feed.deliver(status_rows(), T1)
        site.feed.deliver([(d, s, w + day3, v) for d, s, w, v, _ in status_rows()], T1)
        worker(T1 + timedelta(minutes=1)).run_pending()
        span_1 = (at(4, 45), at(6, 15) + timedelta(microseconds=1))
        span_3 = (span_1[0] + day3, span_1[1] + day3)

        def step(now, **kw):
            out = attest(site, now, **kw)
            spans = [(w.start, w.end) for w in out["requeued"]]
            pending = [(j[2], j[3]) for j in jobs(site.engine) if j[0] == "PENDING"]
            done = worker(now + timedelta(minutes=1)).run_pending()
            # The worker expands each job by the six-hour bracket: 04:45 - 6 h reaches the previous UTC day.
            windows = sorted({w.start for o in done for w in day_windows(*_job_window(site, o.job_id))})
            return out["event"], spans, pending, windows

        created, spans, pending, windows = step(T1 + timedelta(hours=1), key="c", lo=at(0), hi=at(23))
        assert spans == [span_1] and pending == [span_1]
        assert windows == [DAY - timedelta(days=1), DAY]
        replaced, spans, _, _ = step(T1 + timedelta(hours=2), kind="REPLACED", key="r", lo=at(0) + day3,
                                     hi=at(23) + day3, attestation=created.attestation_id, expected=1)
        assert replaced.version == 2 and spans == [span_1, span_3]  # old validity and new validity
        expired, spans, _, _ = step(T1 + timedelta(hours=3), kind="EXPIRED", key="e", hi=at(5, 10) + day3,
                                    attestation=created.attestation_id, expected=2)
        assert expired.version == 3 and spans == [span_3]
        revoked, spans, _, _ = step(T1 + timedelta(hours=4), kind="REVOKED", key="v", reason="clock proof withdrawn",
                                    attestation=created.attestation_id, expected=3)
        assert revoked.version == 4 and spans == [(span_3[0], at(5) + day3 + timedelta(microseconds=1))]
        stored = PostgresAssessmentStore(URL).clock_attestation_events(site.tenant, site.site)
        assert [(e.version, e.event_kind) for e in stored] == [(1, "RECORDED"), (2, "REPLACED"), (3, "EXPIRED"),
                                                               (4, "REVOKED")]
        with pytest.raises(AttestationRefused) as stale:
            attest(site, T1 + timedelta(hours=5), kind="REVOKED", key="v2", reason="again",
                   attestation=created.attestation_id, expected=3)
        assert stale.value.code == "VERSION_CONFLICT"

    def test_only_the_system_attester_writes_and_events_are_append_only(self, site) -> None:
        site.feed.deliver(status_rows(), T1)
        before = jobs(site.engine)
        for principal in (site.kit.principal, AttesterPrincipal("user:owner", "client request")):
            with pytest.raises(AttestationRefused) as refused:
                attest(site, T1, lo=at(0), hi=at(23), principal=principal)
            assert refused.value.code == "SYSTEM_ATTESTER_REQUIRED"
        with pytest.raises(AttestationRefused) as foreign:
            PostgresAssessmentStore(URL).record_clock_attestation(
                site.tenant, site.site, AttestationChange(
                    "RECORDED", uuid4(), "epoch-1", "k", "SYSTEM_CLI", authority="a", label="SIMULATED x",
                    max_utc_error=ATTEST_ERROR, valid_from=at(0), valid_to=at(23)), SYSTEM_ATTESTER, T1)
        assert foreign.value.code == "SOURCE_NOT_IN_SITE"
        assert rows(site.engine, "SELECT count(*) FROM source_clock_attestation")[0][0] == 0
        assert jobs(site.engine) == before
        attest(site, T1, lo=at(0), hi=at(23))
        for sql in ("UPDATE source_clock_attestation SET max_utc_error_ms = 0", "DELETE FROM source_clock_attestation"):
            with pytest.raises(DBAPIError, match="append-only"), site.engine.begin() as c:
                c.execute(text(sql))

    def test_the_cli_records_through_the_system_attester_only(self, site, capsys) -> None:
        site.feed.deliver(status_rows(), T1)
        code = rows(site.engine, "SELECT site_code FROM site WHERE id = :s", s=site.site)[0][0]
        slug = rows(site.engine, "SELECT slug FROM tenant WHERE id = :t", t=site.tenant)[0][0]
        argv = ["record", "--site", code, "--tenant", slug, "--source", gen_source(site), "--epoch", "epoch-1",
                "--idempotency-key", "cli-1", "--authority", "lab-simulated-clock", "--label", "SIMULATED cli",
                "--max-error-seconds", "30", "--valid-from", "2026-10-06T00:00:00Z",
                "--valid-to", "2026-10-07T00:00:00Z"]
        assert slug == "demo"  # the development tenant the CLI accepts
        assert record_cli.main(argv, store=PostgresAssessmentStore(URL), now=T1) == 0
        line = json.loads(capsys.readouterr().out)
        assert line["actor_id"] == SYSTEM_ATTESTER.actor_id and line["version"] == 1 and line["requeued"]
        bad = argv[:-2] + ["--valid-to", "2026-10-06T00:00:00Z", "--idempotency-key", "cli-2"]
        assert record_cli.main(bad, store=PostgresAssessmentStore(URL), now=T1) == 3
        assert "VALIDITY_EMPTY" in capsys.readouterr().err
        assert rows(site.engine, "SELECT count(*), min(recorded_by) FROM source_clock_attestation")[0] == (
            1, SYSTEM_ATTESTER.actor_id)


def _job_window(site, job_id):
    start, end = rows(site.engine, "SELECT window_start, window_end FROM recompute_job WHERE id = :j", j=job_id)[0]
    return start, end
