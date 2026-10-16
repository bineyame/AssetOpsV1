"""S3-02a phase 2: the claim-limit route over `s3-claim-limit-records-v1` (PostgreSQL).

Candidate / Necessary / Indeterminate bounds, missing role, poor quality, conflict, open bound, cohort and
configuration reasons, pending / failed / stale / unassessed / historical currentness, the closed Performance cutover
gate, the request identity seam, wrong Site / window / revision, unsupported rule or model, absent accepted lineage
and exact Evidence links. Tests run in file order: the last ones add a pending day and a failing recompute.
Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import copy
import os
from datetime import timedelta
from uuid import UUID, uuid4

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, engine  # noqa: F401
    from test_s4_finding_store_postgres import CaseRunner

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker
    from assetops_backend.analytics.claim_limit_read import RULE_ID, ClaimLimitReadService
    from assetops_backend.claim_limit_api import build_claim_limit_router
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

import s3_claim_limit_records as records

CLOSED = "No Performance comparison report exists for this Site."
BASE = "/api/sites/KOBO-001/performance/dispatch/windows"


@pytest.fixture(scope="module")
def built(engine):
    pg_harness.empty_tables(engine, ("foundation_revision", "source", "gateway", "asset", "site_import", "site",
                                     "tenant"))
    store = PostgresFoundationStore(URL)
    runner = CaseRunner(store, engine)
    manifest = records.build(runner, URL)
    yield runner, manifest
    pg_harness.dispose(store)


def client(built, *, gate_open=True, access=None, store=None) -> "TestClient":
    runner = built[0]
    scope = {"KOBO-001": ("KOBO-001", runner.tenant, runner.site),
             "OTHER-1": ("OTHER-1", uuid4(), uuid4())}
    app = FastAPI()
    app.include_router(build_claim_limit_router(
        ClaimLimitReadService(store or PostgresAssessmentStore(URL)), scope.get,
        gate=lambda code, t, s: (gate_open, "test: gate open" if gate_open else CLOSED),
        **({} if access is None else {"access": access})))
    return TestClient(app)


def case(built, name: str) -> dict:
    return built[1]["cases"][name]


def get(built, name: str, revision: str | None = "interval", **kw) -> "object":
    c = case(built, name)
    rid = c["interval_revision_ids"][0] if revision == "interval" else revision
    params = {} if rid is None else {"revision": rid}
    params.update(kw.pop("params", {}))
    return client(built, **kw).get(f"{BASE}/{c['day']}/claim-limit", params=params)


def ok(response) -> dict:
    assert response.status_code == 200, response.text
    return response.json()


def refused(response, status: int, code: str) -> dict:
    assert response.status_code == status, response.text
    detail = response.json()["detail"]
    assert detail["code"] == code, detail
    assert "ceiling" not in str(detail) or detail.get("claim_limit") is None
    return detail


def codes(body: dict) -> set[str]:
    return {r["code"] for r in body["claim_limit"]["reasons"]}


class Mutating(PostgresAssessmentStore):
    """The real snapshot with one deliberate change to the pinned revision (unsupported model, absent lineage,
    unusable cohort, open bound, a role problem inside the claim-carrying segment)."""

    def __init__(self, change) -> None:
        super().__init__(URL)
        self.change = change

    def claim_limit_snapshot(self, *args):
        snap, revision = super().claim_limit_snapshot(*args)
        revision = copy.deepcopy(revision)
        self.change(revision)
        return snap, revision


class TestCeilings:
    def test_full_candidate_is_a_current_complete_candidate_ceiling_with_echoed_lineage(self, built) -> None:
        body = ok(get(built, "full-candidate"))
        limit = body["claim_limit"]
        assert (body["currentness"], limit["ceiling"], limit["support"]) == (
            "CURRENT", "CANDIDATE_AVOIDABLE", "COMPLETE")
        assert limit["current_positive_claim"] is True and limit["historical_ceiling"] is None
        assert limit["rule_id"] == body["rule_id"] == RULE_ID and limit["supported_minutes"] == "30"
        assert "never the whole interval" in limit["statement"]
        c = case(built, "full-candidate")
        assert body["assessment_revision_id"] == c["interval_revision_ids"][0]
        assert body["run"]["run_id"] == c["run_id"] == body["current_selection"]["run_id"]
        assert body["tenant_id"] == str(built[0].tenant) and body["site_id"] == str(built[0].site)
        assert body["window"]["start"].startswith("2026-10-06T00:00:00") and body["day"] == "2026-10-06"
        for key in ("knowledge_cutoff", "cohort_sha256", "foundation_revision_ids", "binding_set_revision_ids",
                    "built_at"):
            assert body["run"][key], key
        assert body["watermarks"]["source"]["accepted_at"] and body["read_at"] and body["built_at"]
        assert body["source_gate"]["permitted"] is True and "not observed capability" in body["not_inferred"]

    def test_exact_evidence_links_are_the_revisions_pinned_accepted_ids(self, built) -> None:
        body = ok(get(built, "poor-quality-conflict"))
        with built[0].engine.connect() as c:
            pinned = {str(x) for x in c.execute(text(
                "SELECT evidence_ids FROM assessment_revision WHERE id = :r"),
                {"r": UUID(body["assessment_revision_id"])}).scalar_one()}
            accepted = {str(x) for x in c.execute(text(
                "SELECT id FROM accepted_evidence WHERE id = ANY(:ids)"), {"ids": [UUID(i) for i in pinned]}).scalars()}
        assert set(body["accepted_evidence_ids"]) == pinned == accepted
        spans = [s for item in body["capability"]["roles"].values() for s in item["spans"]]
        assert {e for s in spans for e in s["evidence_ids"]} <= pinned

    def test_missing_pv_bounds_the_claim_to_indeterminate(self, built) -> None:
        body = ok(get(built, "missing-pv"))
        limit = body["claim_limit"]
        assert body["currentness"] == "CURRENT"
        assert (limit["ceiling"], limit["support"], limit["current_positive_claim"]) == ("INDETERMINATE", "NONE", False)
        assert "MISSING_ROLE" in codes(body)

    def test_poor_quality_and_conflict_limit_the_candidate_without_hiding_subspans(self, built) -> None:
        body = ok(get(built, "poor-quality-conflict"))
        limit = body["claim_limit"]
        assert (limit["ceiling"], limit["support"], limit["current_positive_claim"]) == (
            "CANDIDATE_AVOIDABLE", "LIMITED", True)
        assert {"POOR_QUALITY", "CONFLICTING"} <= codes(body)
        poor = [r for r in limit["reasons"] if r["code"] == "POOR_QUALITY"]
        assert [(r["role"], r["minutes"]) for r in poor] == [("pcs_discharge_capability", 15.0)]
        assert float(limit["supported_minutes"]) < 30

    def test_necessary_ceiling_from_a_low_capability_interval(self, built) -> None:
        def necessary(rev):
            rev["claim_level"] = "NECESSARY"
            rev["result"]["portions_minutes"]["necessary"] = "30"
            for s in rev["result"]["segments"]:
                s["classification"] = "NECESSARY"
        body = ok(get(built, "full-candidate", store=Mutating(necessary)))
        assert (body["claim_limit"]["ceiling"], body["claim_limit"]["supported_minutes"]) == ("NECESSARY", "30")

    @pytest.mark.parametrize(("label", "change", "code"), [
        ("cohort", lambda r: r["run"].update(cohort_status="AMBIGUOUS"), "COHORT"),
        ("role inside the claim", lambda r: r["result"]["segments"][0]["missing"].append(
            "PV available power: reading not GOOD quality"), "RULE_BASIS_INCOMPLETE"),
    ])
    def test_fail_closed_rules_withhold_a_positive_ceiling(self, built, label, change, code) -> None:
        body = ok(get(built, "full-candidate", store=Mutating(change)))
        limit = body["claim_limit"]
        assert (limit["ceiling"], limit["current_positive_claim"]) == ("INDETERMINATE", False), label
        assert code in codes(body), label

    def test_open_bound_and_configuration_are_named_reasons(self, built) -> None:
        def change(rev):
            rev["result"]["limitations"].append("OPEN_BOUND: no OFF evidence after the interval in the read range")
            [w] = [r for r in rev["run"]["revisions"] if r["scope"] == "WINDOW"]
            w["result"]["limitations"].append("No unique Foundation revision at 2026-10-06T08:00:00Z")
        limit = ok(get(built, "full-candidate", store=Mutating(change)))["claim_limit"]
        assert (limit["ceiling"], limit["support"]) == ("CANDIDATE_AVOIDABLE", "LIMITED")
        assert {"OPEN_BOUND", "CONFIGURATION"} <= {r["code"] for r in limit["reasons"]}


class TestCurrentness:
    def test_late_revision_withdraws_the_first_revision_to_history(self, built) -> None:
        c = case(built, "late-revision")
        old = ok(get(built, "late-revision", c["withdrawn"]["interval_revision_ids"][0]))
        assert old["currentness"] == "HISTORICAL" and old["window_status"] == "CURRENT"
        assert old["claim_limit"]["ceiling"] is None and not old["claim_limit"]["current_positive_claim"]
        assert old["claim_limit"]["historical_ceiling"]["ceiling"] and "NOT_CURRENT" in codes(old)
        new = ok(get(built, "late-revision"))
        assert new["currentness"] == "CURRENT" and new["assessment_key"] == old["assessment_key"]
        assert new["revision_no"] == old["revision_no"] + 1

    def test_stale_selection_makes_no_current_positive_claim(self, built) -> None:
        body = ok(get(built, "stale-selection"))
        limit = body["claim_limit"]
        assert body["currentness"] == body["window_status"] == "STALE_PROJECTION"
        assert limit["ceiling"] is None and limit["current_positive_claim"] is False
        assert limit["historical_ceiling"]["ceiling"] == "CANDIDATE_AVOIDABLE" and "NOT_CURRENT" in codes(body)

    def test_unassessed_and_no_revision_selected(self, built) -> None:
        empty = ok(client(built).get(f"{BASE}/2026-10-20/claim-limit"))
        assert (empty["window_status"], empty["currentness"], empty["capability"]) == ("UNASSESSED", "UNASSESSED",
                                                                                      None)
        unselected = ok(get(built, "full-candidate", None))
        assert unselected["window_status"] == "CURRENT" and unselected["currentness"] == "UNASSESSED"
        assert unselected["claim_limit"]["ceiling"] is None and "NO_REVISION_SELECTED" in codes(unselected)


class TestRefusals:
    def test_closed_cutover_gate_is_409_never_unassessed(self, built) -> None:
        detail = refused(get(built, "full-candidate", gate_open=False), 409, "PERFORMANCE_CUTOVER_CLOSED")
        assert detail["message"] == CLOSED and detail["claim_limit"] is None and detail["capability"] is None
        refused(client(built, gate_open=False).get(f"{BASE}/2026-10-20/claim-limit"), 409,
                "PERFORMANCE_CUTOVER_CLOSED")

    def test_identity_boundary(self, built) -> None:
        refused(get(built, "full-candidate", access=lambda req, code: 401), 401, "UNAUTHENTICATED")
        refused(get(built, "full-candidate", access=lambda req, code: 403), 403, "SITE_SCOPE_FORBIDDEN")
        c = case(built, "full-candidate")
        assert client(built).get(f"/api/sites/NOPE/performance/dispatch/windows/{c['day']}/claim-limit",
                                 params={"revision": c["interval_revision_ids"][0]}).status_code == 404

    def test_wrong_site_window_revision_and_rule(self, built) -> None:
        c = case(built, "full-candidate")
        rid = c["interval_revision_ids"][0]
        foreign = client(built).get(f"/api/sites/OTHER-1/performance/dispatch/windows/{c['day']}/claim-limit",
                                    params={"revision": rid})
        refused(foreign, 404, "ASSESSMENT_REVISION_NOT_FOUND")
        refused(get(built, "full-candidate", str(uuid4())), 404, "ASSESSMENT_REVISION_NOT_FOUND")
        refused(get(built, "missing-pv", rid), 422, "REVISION_OUTSIDE_WINDOW")
        refused(get(built, "full-candidate", "not-a-uuid"), 422, "INVALID_REVISION_ID")
        refused(get(built, "full-candidate", params={"rule": "s3-claim-limit-0"}), 422, "UNSUPPORTED_RULE_VERSION")
        assert ok(get(built, "full-candidate", params={"rule": RULE_ID}))["claim_limit"]["ceiling"]

    def test_unsupported_model_and_absent_lineage(self, built) -> None:
        refused(get(built, "full-candidate", store=Mutating(lambda r: r.update(model_version="dispatch-3.1"))), 422,
                "UNSUPPORTED_RULE_VERSION")
        refused(get(built, "full-candidate", store=Mutating(lambda r: r["evidence"].pop())), 409,
                "ACCEPTED_LINEAGE_ABSENT")
        refused(get(built, "full-candidate", store=Mutating(lambda r: r["evidence"][0].update(disposition="X"))),
                409, "ACCEPTED_LINEAGE_ABSENT")


class TestLaterStates:
    """Run last: they add a pending day and a failing recompute to the module database."""

    def test_pending_day_has_no_revision_and_no_claim(self, built) -> None:
        runner = built[0]
        records.deliver(runner, records.block("2026-10-24"), "2026-10-30T11:00:00Z")
        body = ok(client(built).get(f"{BASE}/2026-10-24/claim-limit"))
        assert body["window_status"] == "PENDING" and body["claim_limit"]["ceiling"] is None

    def test_failed_recompute_keeps_the_prior_selection_as_non_current(self, built) -> None:
        class Broken:
            ANALYTIC_ID, MODEL_VERSION = "dispatch", "dispatch-3.2"

            @staticmethod
            def assess(_inputs):
                raise RuntimeError("model crashed")

        runner = built[0]
        now = runner.tick()
        for _ in range(3):
            DispatchAssessmentWorker(PostgresAssessmentStore(URL), clock=Clock(now), model=Broken,
                                     backoff=timedelta(0)).run_pending(reconcile=False)
            now += timedelta(minutes=1)
        body = ok(get(built, "stale-selection"))
        assert body["window_status"] == body["currentness"] == "FAILED"
        assert body["claim_limit"]["ceiling"] is None and body["claim_limit"]["current_positive_claim"] is False
        assert any("model crashed" in r for r in body["window_status_reasons"])
