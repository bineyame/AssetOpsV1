"""S3-01 phase 3: file-backed dispatch comparison, the Performance cutover gate and its read routes (no database)."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.analytics.assessment_ports import AssessmentStoreUnavailable
from assetops_backend.analytics.performance_comparison import (
    SCHEMA, claims_digest, compare, permits_performance_cutover)
from assetops_backend.performance_api import build_performance_router

TENANT, SITE = str(UUID(int=1)), str(UUID(int=2))
CLEAN = {"selected_runs": 3, "orphan_revisions": 0, "unselected_heads": 0}


def legacy(claim: str, lo: str = "2026-10-06T05:00:00Z", hi: str = "2026-10-06T06:00:00Z",
           ids: tuple[str, ...] = ("m1", "m2"), aid: str = "a1") -> dict:
    return {"assessment_id": aid, "revisions": [{"revision": 1, "model_version": "dispatch-2", "assessment": {
        "claim_level": claim, "interval": {"first_running_observed": lo, "last_running_observed": hi},
        "evidence_basis": {"message_ids": list(ids)}}}]}


MODEL = "dispatch-3.1"


def evidence(message_id: str) -> str:
    return f"ev-{message_id}"


def interval(claim: str, lo: str = "2026-10-06T05:00:00+00:00", hi: str = "2026-10-06T06:00:00+00:00",
             limits: tuple[str, ...] = (), *, model: str = MODEL, missing: tuple[str, ...] = (),
             evidence_ids: tuple[str, ...] = ("m1", "m2"), jobs: tuple[str, ...] = ()) -> dict:
    segments = [{"classification": claim if claim != "CANDIDATE_AVOIDABLE" else "CANDIDATE_AVOIDABLE",
                 "missing": list(missing)}]
    return {"id": uuid4(), "claim_level": claim, "model_version": model,
            "result": {"interval": {"first_on": lo, "last_on": hi}, "segments": segments, "limitations": []},
            "evidence_ids": [evidence(m) for m in evidence_ids], "window_limitations": list(limits),
            "window_jobs": [{"id": str(uuid4()), "status": s} for s in jobs]}


def run_compare(claims: list[dict], intervals: list[dict], accepted=("m1", "m2"), lineage=CLEAN,
                model: str = MODEL) -> dict:
    return compare(site_code="KOBO-001", tenant_id=TENANT, site_id=SITE, environment="demo", legacy_claims=claims,
                   accepted_evidence={m: evidence(m) for m in accepted}, intervals=intervals, lineage=dict(lineage),
                   compared_at="2026-10-11T00:00:00Z", model_version=model)


def gate(report, claims, lineage=CLEAN, *, site_code="KOBO-001", site_id=SITE, tenant_id=TENANT, env="demo",
         model: str = MODEL):
    return permits_performance_cutover(report, site_code, site_id, tenant_id=tenant_id, environment=env,
                                       legacy_claims=claims, live_lineage=lineage, model_version=model)


PV_MISSING = "PV available power: not bound in the selected role set (missing role)"


class TestComparison:
    def test_each_class(self) -> None:
        assert run_compare([legacy("NECESSARY")], [interval("NECESSARY")])["claims"][0]["class"] == "MATCH"
        delta = run_compare([legacy("CANDIDATE_AVOIDABLE")], [interval("INDETERMINATE", missing=(PV_MISSING,))])
        row = delta["claims"][0]
        assert row["class"] == "INTENTIONAL_DELTA" and row["rule"] == "CAPABILITY_CHANNELS_REQUIRED"
        assert row["rule_change"]["from"] == "dispatch-2" and row["rule_change"]["to"] == MODEL
        assert row["interval_limitations"] == [PV_MISSING] and row["compared_evidence_ids"] == ["ev-m1", "ev-m2"]
        missing = run_compare([legacy("NECESSARY", ids=("m1", "m9"))], [interval("NECESSARY")])
        assert missing["claims"][0]["class"] == "MISSING_SOURCE" and missing["claims"][0]["missing_message_ids"] == ["m9"]
        assert missing["outcome"] == "EXCEPTIONS"
        unproven = run_compare([legacy("CANDIDATE_AVOIDABLE")], [interval("NECESSARY")])
        assert unproven["claims"][0]["class"] == "UNPROVEN" and unproven["outcome"] == "FAILED"
        none = run_compare([legacy("NECESSARY")], [interval("NECESSARY", "2026-10-06T08:00:00+00:00",
                                                                     "2026-10-06T09:00:00+00:00")])
        assert none["claims"][0]["class"] == "UNPROVEN" and "0 selected" in none["claims"][0]["reason"]

    def test_indeterminate_without_named_limitation_is_not_an_intentional_delta(self) -> None:
        assert run_compare([legacy("NECESSARY")], [interval("INDETERMINATE")])["claims"][0]["class"] == "UNPROVEN"

    def test_a_window_limitation_elsewhere_does_not_prove_a_delta(self) -> None:
        """Q11: an Indeterminate interval in a window that names any limitation is not causation."""
        row = run_compare([legacy("CANDIDATE_AVOIDABLE")],
                          [interval("INDETERMINATE", limits=("MISSING_ROLE: pv_available_power over x..y",))])
        assert row["claims"][0]["class"] == "UNPROVEN" and row["outcome"] == "FAILED"
        assert "no documented dispatch-2 to dispatch-3.1 rule difference" in row["claims"][0]["reason"]

    def test_a_delta_needs_the_claim_records_in_the_selected_interval(self) -> None:
        row = run_compare([legacy("CANDIDATE_AVOIDABLE")],
                          [interval("INDETERMINATE", missing=(PV_MISSING,), evidence_ids=("m1",))])["claims"][0]
        assert row["class"] == "UNPROVEN" and "not all in the selected interval's evidence" in row["reason"]

    def test_a_delta_rule_only_explains_its_own_claim_change(self) -> None:
        row = run_compare([legacy("NECESSARY")], [interval("INDETERMINATE", missing=(PV_MISSING,))])["claims"][0]
        assert row["class"] == "UNPROVEN"

    def test_a_selected_dispatch_3_interval_is_stale_not_a_match(self) -> None:
        row = run_compare([legacy("NECESSARY")], [interval("NECESSARY", model="dispatch-3")])["claims"][0]
        assert row["class"] == "UNPROVEN" and row["reason"].startswith("STALE_MODEL")

    def test_an_outstanding_job_keeps_a_matching_prior_result_stale(self) -> None:
        for status in ("PENDING", "LEASED", "FAILED"):
            report = run_compare([legacy("NECESSARY")], [interval("NECESSARY", jobs=(status,))])
            row = report["claims"][0]
            assert row["class"] == "UNPROVEN" and row["reason"].startswith("STALE_PROJECTION"), status
            assert report["outcome"] == "FAILED"

    def test_a_claim_citing_no_record_is_a_missing_source(self) -> None:
        row = run_compare([legacy("NECESSARY", ids=())], [interval("NECESSARY")])["claims"][0]
        assert row["class"] == "MISSING_SOURCE" and row["reason"] == "the claim cites no record"

    def test_empty_set_is_stated_as_such(self) -> None:
        report = run_compare([], [interval("NECESSARY")])
        assert report["empty_set"] is True and report["outcome"] == "PASSED"
        assert report["model_version"] == MODEL and report["schema"] == "s3-performance-comparison-v2"
        assert report["statement"].startswith("Empty-set comparison") and "no claim is said to match" in report["statement"]
        assert report["counts"] == {"MATCH": 0, "INTENTIONAL_DELTA": 0, "MISSING_SOURCE": 0, "UNPROVEN": 0}
        assert gate(report, []) == (True, report["statement"])

    def test_lineage_break_fails_the_comparison(self) -> None:
        report = run_compare([legacy("NECESSARY")], [interval("NECESSARY")], lineage={**CLEAN, "orphan_revisions": 1})
        assert report["outcome"] == "FAILED" and report["lineage_breaks"] == {"orphan_revisions": 1}
        assert report["statement"].endswith("Lineage breaks: {'orphan_revisions': 1}.")


class TestGate:
    claims = [legacy("NECESSARY")]

    def passed(self) -> dict:
        report = run_compare(self.claims, [interval("NECESSARY")])
        assert report["outcome"] == "PASSED" and report["schema"] == SCHEMA
        return report

    def test_passed_report_with_current_digest_and_clean_lineage_opens(self) -> None:
        allowed, reason = gate(self.passed(), self.claims)
        assert allowed and reason.startswith("1 file-backed dispatch claims")

    def test_every_refusal(self) -> None:
        report = self.passed()
        refusals = {
            "no report": gate(None, self.claims),
            "schema": gate({**report, "schema": "other"}, self.claims),
            "site code": gate(report, self.claims, site_code="OTHER-001"),
            "site uuid": gate(report, self.claims, site_id=str(UUID(int=9))),
            "tenant": gate(report, self.claims, tenant_id=str(UUID(int=9))),
            "env missing": gate(report, self.claims, env=None),
            "env": gate(report, self.claims, env="prod"),
            "outcome": gate(run_compare(self.claims, [interval("CANDIDATE_AVOIDABLE")]), self.claims),
            "digest": gate(report, [legacy("CANDIDATE_AVOIDABLE")]),
            "lineage unread": gate(report, self.claims, lineage=None),
            "lineage break": gate(report, self.claims, lineage={**CLEAN, "unselected_heads": 2}),
            "missing source": gate(run_compare([legacy("NECESSARY", ids=("m1", "m9"))], [interval("NECESSARY")]),
                                   [legacy("NECESSARY", ids=("m1", "m9"))]),
            "model": gate(report, self.claims, model="dispatch-3.2"),
            "report model": gate({**report, "model_version": "dispatch-3"}, self.claims),
            "stale heads": gate(report, self.claims, lineage={**CLEAN, "selected_heads_other_model": 1}),
        }
        assert all(allowed is False for allowed, _ in refusals.values()), refusals
        assert "changed after the comparison" in refusals["digest"][1]
        assert "lineage is broken" in refusals["lineage break"][1]
        assert "FAILED" in refusals["outcome"][1]
        assert "EXCEPTIONS" in refusals["missing source"][1]
        assert "another model version" in refusals["model"][1] and "another model version" in refusals["report model"][1]
        assert "still selected under another model version" in refusals["stale heads"][1]
        assert claims_digest(self.claims) == report["legacy_claims_sha256"]


class FakeReads:
    def __init__(self, fail: bool = False) -> None:
        self.fail, self.revision_id = fail, uuid4()

    def _check(self) -> None:
        if self.fail:
            raise AssessmentStoreUnavailable("database down")

    def window(self, tenant_id, site_id, day):
        self._check()
        return {"status": "CURRENT", "day": day.isoformat()}

    def run(self, tenant_id, site_id, run_id):
        self._check()
        return None

    def revision(self, tenant_id, site_id, revision_id):
        self._check()
        if revision_id != self.revision_id:
            return None
        return {"id": revision_id, "evidence": [{"as_accepted": {"foundation_revision_id": "f1"},
                                                 "selection_note": "a backdated correction"}],
                "selected_configuration": {"foundation_revision_ids": ["f2"]}}


SCOPE = ("KOBO-001", UUID(TENANT), UUID(SITE))


def client(reads=None, allowed=True, gate_error=False) -> TestClient:
    def g(code, tenant_id, site_id):
        if gate_error:
            raise AssessmentStoreUnavailable("lineage unreadable")
        return allowed, "PASSED" if allowed else "No Performance comparison report exists for this Site."
    app = FastAPI()
    app.include_router(build_performance_router(reads, lambda code: SCOPE if code == "KOBO-001" else None, g))
    return TestClient(app)


BASE = "/api/sites/{}/performance/dispatch"


class TestRoutes:
    @pytest.mark.parametrize("tail", ["cutover", "windows/2026-10-06", f"runs/{uuid4()}", f"revisions/{uuid4()}"])
    def test_unknown_or_foreign_site_is_404(self, tail) -> None:
        assert client(FakeReads()).get(f"{BASE.format('FOREIGN-9')}/{tail}").status_code == 404

    def test_closed_gate_is_409_and_cutover_says_why(self) -> None:
        c = client(FakeReads(), allowed=False)
        response = c.get(f"{BASE.format('KOBO-001')}/windows/2026-10-06")
        assert response.status_code == 409 and response.json()["detail"]["code"] == "PERFORMANCE_CUTOVER_CLOSED"
        body = c.get(f"{BASE.format('KOBO-001')}/cutover").json()
        assert body["read"] == "CLOSED" and body["permitted"] is False and "comparison" in body["reason"]

    def test_store_unavailable_is_503(self) -> None:
        assert client(None).get(f"{BASE.format('KOBO-001')}/windows/2026-10-06").status_code == 503
        failing = client(FakeReads(fail=True)).get(f"{BASE.format('KOBO-001')}/windows/2026-10-06")
        assert failing.status_code == 503 and failing.json()["detail"]["code"] == "ASSESSMENT_STORE_UNAVAILABLE"
        assert client(FakeReads(), gate_error=True).get(f"{BASE.format('KOBO-001')}/windows/2026-10-06").status_code == 503
        cut = client(FakeReads(), gate_error=True).get(f"{BASE.format('KOBO-001')}/cutover").json()
        assert cut["permitted"] is False and "unavailable" in cut["reason"]

    def test_open_gate_serves_window_and_pinned_drill_down(self) -> None:
        reads = FakeReads()
        c = client(reads)
        assert c.get(f"{BASE.format('KOBO-001')}/cutover").json()["read"] == "POSTGRES_DISPATCH_3"
        assert c.get(f"{BASE.format('KOBO-001')}/windows/2026-10-06").json()["status"] == "CURRENT"
        detail = c.get(f"{BASE.format('KOBO-001')}/revisions/{reads.revision_id}")
        assert detail.status_code == 200
        [item] = detail.json()["evidence"]
        assert item["as_accepted"] == {"foundation_revision_id": "f1"} and item["selection_note"]
        assert c.get(f"{BASE.format('KOBO-001')}/revisions/{uuid4()}").status_code == 404
        assert c.get(f"{BASE.format('KOBO-001')}/runs/{uuid4()}").status_code == 404
        assert c.get(f"{BASE.format('KOBO-001')}/windows/not-a-day").status_code == 422
