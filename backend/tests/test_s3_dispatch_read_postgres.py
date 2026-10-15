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

    @staticmethod
    def _exhaust_a_recompute(site, rows=None, late=(5, 40)):
        site.feed.deliver(rows or interval_rows(5, 6), T1)
        worker(T1 + timedelta(minutes=1)).run_pending()
        site.feed.deliver([("battery-pcs-controller", "state-of-charge", datetime(2026, 10, 6, *late,
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
        return now

    @staticmethod
    def _intervals(site):
        return PostgresAssessmentStore(URL).selected_intervals(site.tenant, site.site, "dispatch", "dispatch",
                                                               timedelta(hours=6))

    def test_a_later_successful_reassessment_supersedes_the_failed_job(self, site) -> None:
        now = self._exhaust_a_recompute(site)
        assert reads().window(site.tenant, site.site, DAY)["status"] == "FAILED"
        assert any(j["status"] == "FAILED" for r in self._intervals(site) for j in r["window_jobs"])
        site.feed.deliver([("battery-pcs-controller", "state-of-charge", datetime(2026, 10, 6, 5, 50,
                                                                                    tzinfo=timezone.utc), "30")],
                          now + timedelta(minutes=1))
        worker(now + timedelta(minutes=2)).run_pending(reconcile=False)
        body = reads().window(site.tenant, site.site, DAY)
        assert body["status"] == "CURRENT" and not body["stale"], body["status_reasons"]
        assert "FAILED" in [j[0] for j in jobs(site.engine)]
        assert not any(j["status"] == "FAILED" for r in self._intervals(site) for j in r["window_jobs"])

    @staticmethod
    def _classify_against_selection(site):
        """Classify a file-backed claim built from the selected interval itself (same level, span and cited
        records), so the only thing that can make it UNPROVEN is the projection's freshness."""
        from sqlalchemy import text

        from assetops_backend.analytics.performance_comparison import _pg_span, classify
        [hit] = TestDispatchRead._intervals(site)
        lo, hi = _pg_span(hit)
        with site.engine.connect() as c:
            messages = [r[0] for r in c.execute(text("SELECT message_id FROM accepted_evidence WHERE id = ANY(:i)"),
                                                {"i": [str(e) for e in hit["evidence_ids"]]}).all()]
        claim = {"assessment_id": "legacy-1", "revisions": [{"revision": 1, "model_version": "dispatch-2",
                 "assessment": {"claim_level": hit["claim_level"], "evidence_basis": {"message_ids": messages},
                                "interval": {"first_running_observed": lo, "last_running_observed": hi}}}]}
        accepted = PostgresAssessmentStore(URL).accepted_evidence(site.tenant, site.site, messages)
        return classify(claim, accepted, [hit], hit["model_version"])

    def test_comparison_classifies_a_recovered_interval_after_a_superseded_failed_job_r1_c1(self, site) -> None:
        now = self._exhaust_a_recompute(site)
        stale = self._classify_against_selection(site)
        assert stale["class"] == "UNPROVEN" and stale["reason"].startswith("STALE_PROJECTION"), stale
        site.feed.deliver([("battery-pcs-controller", "state-of-charge", datetime(2026, 10, 6, 5, 50,
                                                                                    tzinfo=timezone.utc), "30")],
                          now + timedelta(minutes=1))
        worker(now + timedelta(minutes=2)).run_pending(reconcile=False)
        assert "FAILED" in [j[0] for j in jobs(site.engine)]
        recovered = self._classify_against_selection(site)
        assert recovered["class"] == "MATCH", recovered

    def test_a_neighbouring_window_in_the_bracket_recovers_with_it(self, site) -> None:
        now = self._exhaust_a_recompute(site, interval_rows(22, 23) + interval_rows(25, 26),
                                       late=(23, 50))
        nxt = DAY + timedelta(days=1)
        assert reads().window(site.tenant, site.site, nxt)["status"] == "FAILED"
        site.feed.deliver([("battery-pcs-controller", "state-of-charge", datetime(2026, 10, 6, 23, 55,
                                                                                    tzinfo=timezone.utc), "30")],
                          now + timedelta(minutes=1))
        worker(now + timedelta(minutes=2)).run_pending(reconcile=False)
        assert reads().window(site.tenant, site.site, nxt)["status"] == "CURRENT"
        assert reads().window(site.tenant, site.site, DAY)["status"] == "CURRENT"

    def test_routes_serve_the_pinned_drill_down_only_through_the_open_gate(self, site) -> None:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from assetops_backend.performance_api import build_performance_router

        site.feed.deliver(interval_rows(5, 6), T1)
        worker(T1 + timedelta(minutes=1)).run_pending()
        state = {"open": False}
        scope = lambda code: ("KOBO-T", site.tenant, site.site) if code == "KOBO-T" else None  # noqa: E731
        app = FastAPI()
        app.include_router(build_performance_router(reads(), scope, lambda *_: (state["open"], "gate")))
        c, base = TestClient(app), "/api/sites/KOBO-T/performance/dispatch"
        assert c.get(f"{base}/windows/{DAY}").status_code == 409
        state["open"] = True
        window = c.get(f"{base}/windows/{DAY}").json()
        assert window["status"] == "CURRENT" and window["site_code"] == "KOBO-T"
        [interval] = window["intervals"]
        detail = c.get(f"{base}/revisions/{interval['id']}").json()
        assert {e["evidence_id"] for e in detail["evidence"]} == {str(x) for x in interval["evidence_ids"]}
        assert all(e["as_accepted"]["foundation_revision_id"] for e in detail["evidence"])
        assert c.get(f"{base}/runs/{window['selection']['run_id']}").status_code == 200
        assert c.get(f"/api/sites/OTHER-1/performance/dispatch/revisions/{interval['id']}").status_code == 404

    def test_stored_dispatch_3_windows_are_reassessed_under_the_current_model_and_kept_as_history(
            self, site, monkeypatch) -> None:
        """D-2026-10-11-s3-phase-3a-version-and-cutover: a stored default `dispatch-3` window reads stale,
        the normal worker pass reconciles and reassesses it under the current model (`dispatch-3.1`, now `dispatch-3.2`), and the `dispatch-3`
        run and revisions stay unchanged and addressable, marked as an older rule result."""
        from assetops_backend.analytics import dispatch_v3

        site.feed.deliver(interval_rows(5, 6), T1)
        with monkeypatch.context() as pre_bump:  # the stored rows the pre-bump code wrote
            pre_bump.setattr(dispatch_v3, "MODEL_VERSION", "dispatch-3")
            worker(T1 + timedelta(minutes=1)).run_pending(reconcile=False)
        lineage = PostgresAssessmentStore(URL).lineage_breaks
        assert lineage(site.tenant, site.site, "dispatch", dispatch_v3.MODEL_VERSION)["selected_heads_other_model"] == 1
        old = reads().window(site.tenant, site.site, DAY)
        assert old["selection"]["model_version"] == "dispatch-3" and old["status"] == "STALE_PROJECTION"
        changed = "MODEL_VERSION_CHANGED: selected run used dispatch-3, current is " + dispatch_v3.MODEL_VERSION
        assert any(r.startswith(changed)
                   for r in old["status_reasons"])
        [old_interval] = old["intervals"]

        worker(T1 + timedelta(minutes=2)).run_pending()  # reconcile + reassess, no operator step
        new = reads().window(site.tenant, site.site, DAY)
        assert new["status"] == "CURRENT" and new["selection"]["model_version"] == dispatch_v3.MODEL_VERSION
        assert new["selection"]["run_id"] != old["selection"]["run_id"]
        [new_interval] = new["intervals"]
        assert new_interval["assessment_key"] == old_interval["assessment_key"]
        assert new_interval["revision_no"] > old_interval["revision_no"]
        assert lineage(site.tenant, site.site, "dispatch", dispatch_v3.MODEL_VERSION)["selected_heads_other_model"] == 0

        kept = reads().revision(site.tenant, site.site, old_interval["id"])
        assert kept["model_version"] == "dispatch-3" and kept["basis_sha256"] == old_interval["basis_sha256"]
        assert kept["model_note"].startswith("OLDER_RULE_RESULT: produced by dispatch-3")
        assert reads().revision(site.tenant, site.site, new_interval["id"])["model_note"] is None
        old_run = reads().run(site.tenant, site.site, old["selection"]["run_id"])
        assert old_run["model_version"] == "dispatch-3" and old_run["model_note"].startswith("OLDER_RULE_RESULT")
        assert worker(T1 + timedelta(minutes=3)).reconcile(site.tenant, site.site) == []
