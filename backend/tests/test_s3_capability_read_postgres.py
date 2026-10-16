"""S3-02a phase 1: selected-assessment capability readiness over `s3-claim-limit-records-v1` (PostgreSQL).

The fixture (`s3_claim_limit_records.build`) is real Batch V2 ingestion plus the S3 worker; these tests read the
exact selected revisions back through `ClaimLimitReadService` and check per-role spans, durations, quality,
exact accepted Evidence IDs, the rule basis and that a reload returns the same answer. No simulator truth is read.
Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import json
import os
from datetime import date
from uuid import UUID

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine  # noqa: F401
    from test_s4_finding_store_postgres import CaseRunner

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.claim_limit_read import RULE_ID, ClaimLimitReadService
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

import s3_claim_limit_records as records


@pytest.fixture(scope="module")
def built(engine):
    pg_harness.empty_tables(engine, ("foundation_revision", "source", "gateway", "asset", "site_import", "site",
                                     "tenant"))
    store = PostgresFoundationStore(URL)
    runner = CaseRunner(store, engine)
    manifest = records.build(runner, URL)
    out = os.environ.get("ASSETOPS_S3_CLAIM_LIMIT_MANIFEST_OUT")
    if out:
        with open(out, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, default=str)
    assessments = PostgresAssessmentStore(URL)
    yield runner, manifest, ClaimLimitReadService(assessments)
    pg_harness.dispose(store, assessments, runner.findings)


def read(built, case: str, revision: str | None = "interval") -> dict:
    runner, manifest, reads = built
    c = manifest["cases"][case]
    rid = c["interval_revision_ids"][0] if revision == "interval" else revision
    return reads.read(runner.tenant, runner.site, date.fromisoformat(c["day"]), None if rid is None else UUID(rid))


def spans(body: dict, role: str) -> list[tuple[str, str, str]]:
    return [(s["status"], s["start"], s["end"]) for s in body["capability"]["roles"][role]["spans"]]


class TestCapabilityRead:
    def test_fixture_cases_select_the_expected_classifications(self, built) -> None:
        cases = built[1]["cases"]
        assert cases["full-candidate"]["interval_claims"] == ["CANDIDATE_AVOIDABLE"]
        assert cases["missing-pv"]["interval_claims"] == ["INDETERMINATE"]
        assert cases["poor-quality-conflict"]["interval_claims"] == ["CANDIDATE_AVOIDABLE"]
        late = cases["late-revision"]
        assert late["withdrawn"]["interval_revision_ids"] != late["interval_revision_ids"]
        assert cases["stale-selection"]["status"] == "STALE_PROJECTION"
        assert all(cases[k]["status"] == "CURRENT" for k in ("full-candidate", "missing-pv", "poor-quality-conflict",
                                                              "late-revision"))

    def test_full_candidate_covers_every_required_role_with_exact_accepted_ids(self, built) -> None:
        body = read(built, "full-candidate")
        assert body["rule_id"] == body["capability"]["rule_id"] == RULE_ID
        assert body["currentness"] == "CURRENT"
        for role, item in body["capability"]["roles"].items():
            assert item["status"] == "COVERED", (role, item)
            assert item["covered_minutes"] == 30.0, (role, item)
            assert item["evidence_ids"], role
        everything = {e for item in body["capability"]["roles"].values() for e in item["evidence_ids"]}
        assert everything <= set(body["accepted_evidence_ids"])
        with built[0].engine.connect() as c:
            roles = dict(c.execute(text("SELECT CAST(id AS text), role FROM accepted_evidence WHERE id = ANY(:ids)"),
                                   {"ids": [UUID(e) for e in everything]}).all())
        for role, item in body["capability"]["roles"].items():
            assert {roles[e] for e in item["evidence_ids"]} == {role}

    def test_missing_pv_is_a_missing_span_not_zero_capability(self, built) -> None:
        body = read(built, "missing-pv")
        pv = body["capability"]["roles"]["pv_available_power"]
        assert pv["status"] == "INCOMPLETE" and pv["covered_minutes"] == 0.0
        assert pv["minutes_by_status"] == {"MISSING": 30.0} and pv["evidence_ids"] == []
        assert spans(body, "pv_available_power") == [("MISSING", "2026-10-08T08:00:00.000000Z", "2026-10-08T08:30:00.000000Z")]
        assert body["capability"]["roles"]["pcs_discharge_capability"]["status"] == "COVERED"
        assert any(r["code"] == "MISSING_ROLE" and r["role"] == "pv_available_power"
                   for r in body["claim_limit"]["reasons"])

    def test_poor_quality_and_conflict_keep_their_exact_subspans(self, built) -> None:
        body = read(built, "poor-quality-conflict")
        dis = spans(body, "pcs_discharge_capability")
        assert ("POOR_QUALITY", "2026-10-11T08:05:00.000000Z", "2026-10-11T08:20:00.000000Z") in dis, dis
        assert dis[0][0] == "COVERED" and dis[-1][0] == "COVERED"
        pv = spans(body, "pv_available_power")
        assert any(s[0] == "CONFLICTED" for s in pv), pv
        conflicted = [s for s in body["capability"]["roles"]["pv_available_power"]["spans"]
                      if s["status"] == "CONFLICTED"]
        assert all(len(s["evidence_ids"]) >= 2 for s in conflicted), conflicted
        assert body["capability"]["roles"]["pv_available_power"]["covered_minutes"] < 30.0

    def test_reload_returns_the_same_capability_and_lineage(self, built) -> None:
        first, again = read(built, "poor-quality-conflict"), read(built, "poor-quality-conflict")
        for key in ("capability", "claim_limit", "accepted_evidence_ids", "run", "assessment_revision_id",
                    "watermarks"):
            assert first[key] == again[key], key
        assert first["read_at"] <= again["read_at"]
        run = first["run"]
        assert run["foundation_revision_ids"] and run["binding_set_revision_ids"] and run["knowledge_cutoff"]
        assert first["watermarks"]["source"]["accepted_at"] and first["watermarks"]["analytic_built_at"]
        assert run["cohort_status"] in ("SELECTED_UNIQUE", "SELECTED_EXPLICIT")

    def test_window_revision_lists_each_interval_without_a_single_ceiling(self, built) -> None:
        c = built[1]["cases"]["poor-quality-conflict"]
        body = read(built, "poor-quality-conflict", c["window_revision_id"])
        assert body["scope"] == "WINDOW" and body["claim_limit"]["ceiling"] is None
        assert [i["assessment_revision_id"] for i in body["claim_limit"]["interval_ceilings"]] == \
            c["interval_revision_ids"]

    def test_non_current_window_revisions_have_no_top_level_interval_ceilings(self, built) -> None:
        """A stale-selection or withdrawn window revision is not a current claim: its per-interval ceilings
        live only under `historical_ceiling`."""
        cases = built[1]["cases"]
        for name, window in (("stale-selection", cases["stale-selection"]["window_revision_id"]),
                             ("late-revision", cases["late-revision"]["withdrawn"]["window_revision_id"])):
            body = read(built, name, window)
            assert body["scope"] == "WINDOW" and body["currentness"] != "CURRENT", name
            cl = body["claim_limit"]
            assert "interval_ceilings" not in cl and cl["ceiling"] is None and not cl["current_positive_claim"], name
            hist = cl["historical_ceiling"]["interval_ceilings"]
            assert hist, name
            assert body["currentness"] in ("STALE_PROJECTION", "HISTORICAL"), name
        current = read(built, "late-revision", cases["late-revision"]["window_revision_id"])
        assert current["currentness"] == "CURRENT" and current["claim_limit"]["interval_ceilings"]
        assert current["claim_limit"]["historical_ceiling"] is None
