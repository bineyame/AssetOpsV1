"""S3-01 phase 3: derived projection status and pinned drill-down over the durable store (PostgreSQL)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from test_s3_dispatch_assessment_postgres import URL, T1, interval_rows, jobs, worker

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_s3_dispatch_assessment_postgres import site  # noqa: F401

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.dispatch_read import DispatchReadService
    from assetops_backend.sites.foundation_service import FoundationService

DAY = date(2026, 10, 6)


def reads() -> "DispatchReadService":
    return DispatchReadService(PostgresAssessmentStore(URL))


class TestDispatchRead:
    def test_current_window_and_pinned_drill_down(self, site) -> None:
        assert reads().window(site.tenant, site.site, DAY)["status"] == "UNASSESSED"
        site.feed.deliver(interval_rows(5, 6), T1)
        assert reads().window(site.tenant, site.site, DAY)["status"] == "PENDING"
        worker(T1 + timedelta(minutes=1)).run_pending()
        body = reads().window(site.tenant, site.site, DAY)
        assert body["status"] == "CURRENT" and not body["status_reasons"] and not body["stale"]
        assert body["selection"]["knowledge_cutoff_label"].startswith("worker selection timestamp")
        [interval] = body["intervals"]
        detail = reads().revision(site.tenant, site.site, interval["id"])
        assert {str(e["evidence_id"]) for e in detail["evidence"]} == set(interval["evidence_ids"])
        assert all(len(e["envelope_sha256"]) == 64 and e["disposition"] == "ACCEPTED" for e in detail["evidence"])
        assert all(e["as_accepted"]["foundation_revision_id"] and e["selection_note"] is None
                   for e in detail["evidence"])
        assert reads().run(site.tenant, site.site, body["selection"]["run_id"])["id"] == body["selection"]["run_id"]
        from uuid import uuid4
        assert reads().revision(uuid4(), site.site, interval["id"]) is None  # foreign tenant
        assert reads().run(site.tenant, site.site, uuid4()) is None

    def test_acceptance_racing_a_lease_is_never_current_until_reassessed(self, site) -> None:
        site.feed.deliver(interval_rows(5, 6), T1)
        worker(T1 + timedelta(minutes=1)).run_pending()
        old = reads().window(site.tenant, site.site, DAY)
        assert old["status"] == "CURRENT"
        late_at = T1 + timedelta(hours=1)
        site.feed.deliver([("battery-pcs-controller", "state-of-charge", datetime(2026, 10, 6, 5, 40,
                                                                                    tzinfo=timezone.utc), "31")],
                          late_at)
        stale = reads().window(site.tenant, site.site, DAY)
        assert stale["status"] == "STALE_PROJECTION" and stale["stale"]
        assert stale["selection"]["run_id"] == old["selection"]["run_id"]  # prior stays inspectable
        assert any(r.startswith("RECOMPUTE_OUTSTANDING") for r in stale["status_reasons"])
        assert any(r.startswith("INPUT_BASIS_CHANGED") for r in stale["status_reasons"])
        worker(late_at + timedelta(minutes=1)).run_pending()
        new = reads().window(site.tenant, site.site, DAY)
        assert new["status"] == "CURRENT" and new["selection"]["run_id"] != old["selection"]["run_id"]
        old_interval = old["intervals"][0]["id"]
        assert reads().revision(site.tenant, site.site, old_interval)["id"] == old_interval

    def test_backdated_configuration_reads_stale_then_is_reassessed_without_an_operator(self, site) -> None:
        site.feed.deliver(interval_rows(5, 6), T1)
        worker(T1 + timedelta(minutes=1)).run_pending()
        FoundationService(site.store, "demo", Clock(T1 + timedelta(minutes=3))).publish_battery_reserve(
            site.result.tenant, site.result.site, asset_code="battery", value=40.0,
            effective_from=datetime(2026, 10, 5, tzinfo=timezone.utc), note="backdated reserve")
        stale = reads().window(site.tenant, site.site, DAY)
        assert stale["status"] == "STALE_PROJECTION"
        assert any(r.startswith("CONFIGURATION_CHANGED") for r in stale["status_reasons"])
        worker(T1 + timedelta(minutes=5)).run_pending()  # no manual reconcile (F4)
        assert reads().window(site.tenant, site.site, DAY)["status"] == "CURRENT"

    def test_a_failed_recompute_reads_failed_with_the_prior_selection(self, site) -> None:
        site.feed.deliver(interval_rows(5, 6), T1)
        worker(T1 + timedelta(minutes=1)).run_pending()
        site.feed.deliver([("battery-pcs-controller", "state-of-charge", datetime(2026, 10, 6, 5, 40,
                                                                                    tzinfo=timezone.utc), "31")],
                          T1 + timedelta(hours=1))

        class Broken:
            ANALYTIC_ID, MODEL_VERSION = "dispatch", "dispatch-3"

            @staticmethod
            def assess(_inputs):
                raise RuntimeError("model crashed")

        now = T1 + timedelta(hours=2)
        for _ in range(3):
            worker(now, model=Broken, backoff=timedelta(0)).run_pending(reconcile=False)
            now += timedelta(minutes=1)
        assert "FAILED" in [j[0] for j in jobs(site.engine)]
        body = reads().window(site.tenant, site.site, DAY)
        assert body["status"] == "FAILED" and body["stale"] and body["selection"] is not None
        assert any("model crashed" in r for r in body["status_reasons"])
