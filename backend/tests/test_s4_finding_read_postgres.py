"""S4-01 phase 2: exact Finding root/revision read over `s4-finding-cases-v1` (PostgreSQL).

Runs the committed specification through ingestion, the S3 worker and the matcher (as phase 1 does), then
reads every Finding through the HTTP route and compares the returned IDs with the stored relations.
Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from test_s4_finding_store_postgres import SPEC, URL, CaseRunner, _t, run_case  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
    from assetops_backend.analytics.dispatch_read import DispatchReadService
    from assetops_backend.analytics.finding_read import FindingReadService
    from assetops_backend.finding_api import build_finding_router
    from assetops_backend.evidence.composition import build_public_provenance
    from assetops_backend.evidence.public_provenance import basis_sha256


def client_for(runner: "CaseRunner", gate_open: bool = True, provenance=None) -> "TestClient":
    reads = FindingReadService(PostgresFindingStore(URL), DispatchReadService(PostgresAssessmentStore(URL)),
                               provenance)
    scope = {"KOBO-001": ("KOBO-001", runner.tenant, runner.site)}
    app = FastAPI()
    app.include_router(build_finding_router(reads, scope.get, gate=lambda code, t, s: (
        gate_open, "test: gate open" if gate_open else "test: Performance comparison has not passed")))
    return TestClient(app)


# Every fixture day 10-05..10-23 (review B1). The fixture has no complete assessed day without Candidate, so
# NO_FINDING is pinned by `test_a_complete_day_without_candidate_is_no_finding`.
EXPECTED_DAYS = {
    "2026-10-05": "NOT_ASSESSED",
    "2026-10-06": "FINDINGS_RECORDED",
    "2026-10-07": "NOT_ASSESSED",
    "2026-10-08": "FINDINGS_RECORDED",
    "2026-10-09": "FINDINGS_RECORDED",
    "2026-10-10": "NOT_ASSESSED",
    "2026-10-11": "FINDINGS_RECORDED",
    "2026-10-12": "NOT_ASSESSED",
    "2026-10-13": "FINDINGS_RECORDED",
    "2026-10-14": "NOT_ASSESSED",
    "2026-10-15": "FINDINGS_RECORDED",
    "2026-10-16": "NOT_ASSESSED",
    "2026-10-17": "NOT_ASSESSED",
    "2026-10-18": "NOT_ASSESSED",
    "2026-10-19": "NOT_DETERMINABLE",
    "2026-10-20": "NOT_ASSESSED",
    "2026-10-21": "FINDINGS_RECORDED",
    "2026-10-22": "NOT_ASSESSED",
    "2026-10-23": "NOT_ASSESSED",
}


def by_anchor(rows: dict, at: str) -> dict:
    return next(f for f in rows["findings"] if f["anchor_start"] == _t(at))


def get(client, finding_id, **params) -> dict:
    response = client.get(f"/api/sites/KOBO-001/findings/{finding_id}", params=params)
    assert response.status_code == 200, response.text
    return response.json()


class TestFindingRead:
    def test_every_case_reads_back_exactly_with_pinned_lineage(self, store, engine) -> None:
        runner = CaseRunner(store, engine)
        for case in SPEC["cases"]:
            run_case(runner, case)
        rows = runner.reload()
        client = client_for(runner)
        public = client_for(runner, provenance=build_public_provenance(URL))
        cites = {}
        for c in rows["assessments"]:
            cites.setdefault(str(c["finding_revision_id"]), []).append(c)

        # Every Finding: latest selected, every revision listed in order with its exact stored citations.
        for f in rows["findings"]:
            stored = [r for r in rows["revisions"] if r["finding_id"] == f["id"]]
            body = get(client, f["id"])
            assert body["selection"]["selected_by"] == "LATEST_RECORDED"
            assert body["selection"]["revision_id"] == str(stored[-1]["id"]) and body["selection"]["is_latest"]
            assert [r["id"] for r in body["revisions"]] == [str(r["id"]) for r in stored]
            for r in body["revisions"]:
                mine = cites[r["id"]]
                assert r["window_assessment_revision_ids"] == sorted(
                    str(c["assessment_revision_id"]) for c in mine if c["scope"] == "WINDOW")
                assert r["interval_assessment_revision_ids"] == sorted(
                    str(c["assessment_revision_id"]) for c in mine if c["scope"] == "INTERVAL")
                assert r["support_changed"] == (r["transition"] != "BASIS_REFRESHED")
            cited = {str(e["evidence_id"]) for e in rows["evidence"]
                     if e["finding_revision_id"] == stored[-1]["id"]}
            assert {e["evidence_id"] for e in body["revision"]["cited_evidence"]} == cited
            assert all(e["disposition"] == "ACCEPTED" for e in body["revision"]["cited_evidence"])
            expected = "MERGED_INTO_CANONICAL" if stored[-1]["lifecycle"] == "MERGED" else "CURRENT"
            assert body["state"]["projection"] == expected, (body["state"], body["revisions"][-1]["transition"],
                                                              body["revision"]["currentness"])
            assert "knowledge_at" not in body["selection"] and "no arbitrary" in body["selection"]["replay"]
            assert body["links"]["canonical"] == f"/sites/KOBO-001/findings/{f['id']}"
            # W3-01 Run 3 q3: unwired keeps the fail-closed W1 shape; the composed public resolver adds the public
            # keys to the W1 fields, digesting the selected `{finding_revision.id}` and its exact citations.
            unwired = body["source_provenance"]
            assert unwired["state"] == "UNKNOWN" and unwired["reasons"][0]["code"] == "PROVENANCE_NOT_WIRED"
            assert not ({"classification", "evidence_ids", "basis_sha256", "detail"} & set(unwired))
            sp = get(public, f["id"])["source_provenance"]
            assert set(unwired) - {"reasons"} <= set(sp) and sp["classification"] == sp["state"]
            assert sp["finding_revision_id"] == str(stored[-1]["id"])
            assert sp["evidence_ids"] == sorted(cited) == sorted(sp["accepted_evidence_ids"])
            assert sp["basis_sha256"] == basis_sha256(runner.tenant, runner.site, [stored[-1]["id"]], sorted(cited))

        # F04: revision 1 stays pinned after late earlier acceptance; revision 2 selects a new S3 revision.
        f04 = by_anchor(rows, "2026-10-13T08:30:00Z")
        latest = get(client, f04["id"])
        r1, r2 = latest["revisions"][0], latest["revisions"][1]
        pinned = get(client, f04["id"], revision_id=r1["id"])
        assert pinned["selection"] == {**pinned["selection"], "revision_id": r1["id"], "is_latest": False,
                                       "selected_by": "EXACT_REVISION_ID"}
        assert pinned["revision"]["episode"]["start"].startswith("2026-10-13T08:30")
        assert r2["primary_assessment_revision_id"] != r1["primary_assessment_revision_id"]
        assert r2["prior_interval_assessment_revision_ids"] == r1["interval_assessment_revision_ids"]
        assert pinned["finding"]["anchor_start"] == latest["finding"]["anchor_start"]
        # Review B2: a pinned non-latest revision is superseded, not "match pending"; the current state is the
        # latest revision's and says so.
        assert pinned["revision"]["currentness"]["state"] == "SUPERSEDED_BY_LATER_REVISION"
        assert pinned["revision"]["currentness"]["latest_revision_id"] == latest["selection"]["revision_id"]
        assert pinned["revision"]["currentness"]["windows"]
        assert pinned["state"]["claim_is_current_refers_to"] == "LATEST_REVISION"
        assert pinned["state"]["projection"] == latest["state"]["projection"] == "CURRENT"
        assert latest["revision"]["currentness"]["state"] == "CURRENT"
        # Q19: with the Performance source closed, the default read is 409 and the pinned one is audit-only.
        closed = client_for(runner, gate_open=False)
        assert closed.get(f"/api/sites/KOBO-001/findings/{f04['id']}").status_code == 409
        audit = get(closed, f04["id"], revision_id=r1["id"])
        assert audit["state"]["projection"] == "SOURCE_CLOSED" and not audit["state"]["claim_is_current"]
        assert audit["audit_only"]["non_current"] and audit["links"]["assessment_revisions"] == {}
        assert closed.get("/api/sites/KOBO-001/finding-windows/2026-10-06").status_code == 409

        # F05: UNCONFIRMED then NO_LONGER_SUPPORTED on one ID; provenance-only entries grouped, never squashed.
        f05 = by_anchor(rows, "2026-10-21T08:00:00Z") if any(
            f["anchor_start"] == _t("2026-10-21T08:00:00Z") for f in rows["findings"]) else next(
            f for f in rows["findings"] if f["anchor_start"].date() == date(2026, 10, 21))
        body = get(client, f05["id"])
        transitions = [r["transition"] for r in body["revisions"]]
        assert "UNCONFIRMED" in transitions and transitions[-1] == "NO_LONGER_SUPPORTED"
        assert body["state"]["lifecycle"] == "NO_LONGER_SUPPORTED" and not body["state"]["claim_is_current"]
        assert sum(g["count"] for g in body["revision_groups"]) == len(body["revisions"])
        refreshed = [r for r in rows["revisions"] if r["transition"] == "BASIS_REFRESHED"]
        assert refreshed, "the fixture records provenance-only revisions"
        some = get(client, refreshed[0]["finding_id"])
        [group] = [g for g in some["revision_groups"] if str(refreshed[0]["id"]) in g["revision_ids"]]
        assert group["kind"] == "BASIS_REFRESHED" and group["support_changed"] is False

        # F03: linked recurrence names both OFF reports (resolved to accepted evidence) and covered windows.
        linked = [f for f in rows["findings"] if f["recurs_after_finding_id"]]
        assert linked
        for f in linked:
            body = get(client, f["id"])
            rec = body["relations"]["recurrence"]
            assert rec["status"] == "LINKED" and rec["prior_finding_id"] == str(f["recurs_after_finding_id"])
            offs = {(o["assessment_revision_id"], o["at"]): o["evidence_ids"] for o in body["revision"]["off_reports"]}
            assert offs[(rec["off_after_prior"]["assessment_revision_id"], rec["off_after_prior"]["at"])]
            assert offs[(rec["off_before_new"]["assessment_revision_id"], rec["off_before_new"]["at"])]
            assert rec["covered_window_revision_ids"]
            assert str(f["id"]) in get(client, f["recurs_after_finding_id"])["relations"]["recurred_by"]
        unlinked = [f for f in rows["findings"] if not f["recurs_after_finding_id"] and not f["split_from_finding_id"]]
        assert all(get(client, f["id"])["relations"]["recurrence"]["status"] == "NOT_ESTABLISHED"
                   for f in unlinked)

        # F06: merge keeps both URLs; only the canonical is the active episode.
        [merge] = rows["merges"]
        old = get(client, merge["superseded_finding_id"])
        canonical = get(client, merge["canonical_finding_id"])
        assert old["state"]["merged_into_finding_id"] == str(merge["canonical_finding_id"])
        assert old["relations"]["canonical_finding_id"] == str(merge["canonical_finding_id"])
        assert str(merge["superseded_finding_id"]) in {m["superseded_finding_id"]
                                                       for m in canonical["relations"]["merged_from"]}
        assert old["links"]["canonical_finding"].endswith(str(merge["canonical_finding_id"]))

        # F02: the cross-midnight continuity records what bridged it and adds no Candidate minutes.
        f02 = next(f for f in rows["findings"] if f["anchor_start"].date() == date(2026, 10, 8))
        gaps = get(client, f02["id"])["revision"]["claim"]["continuity"]
        assert gaps and all(g["candidate_minutes_added"] == "0" and g["bridged_by"] for g in gaps)
        # Q17: every bridging stop is confirmed by the selected runs' accepted generator reports.
        stops = [x for g in gaps for x in g["stops"]]
        assert all(x["proof"]["status"] == "CONFIRMED" and x["proof"]["checked_evidence_ids"]
                   and x["proof"]["off_after_evidence_ids"] and x["proof"]["off_before_evidence_ids"] for x in stops)

        # 404 matrix: unknown/foreign root, a revision of another Finding, unknown Site; malformed ID is 422.
        assert client.get(f"/api/sites/KOBO-001/findings/{uuid4()}").status_code == 404
        other = str(rows["revisions"][0]["id"])
        target = next(f for f in rows["findings"] if f["id"] != rows["revisions"][0]["finding_id"])
        assert client.get(f"/api/sites/KOBO-001/findings/{target['id']}",
                          params={"revision_id": other}).status_code == 404
        assert client.get(f"/api/sites/NOPE/findings/{target['id']}").status_code == 404
        assert client.get("/api/sites/KOBO-001/findings/not-a-uuid").status_code == 422

        # Window states: recorded Findings, an assessed day with none, and a day never assessed.
        assert client.get("/api/sites/KOBO-001/finding-windows/2026-10-06").json()["state"] == "FINDINGS_RECORDED"
        assert client.get("/api/sites/KOBO-001/finding-windows/2026-09-01").json()["state"] == "NOT_ASSESSED"
        windows = {d: client.get(f"/api/sites/KOBO-001/finding-windows/{d}").json()
                   for d in (f"2026-10-{n:02d}" for n in range(5, 24))}
        states = {d: w["state"] for d, w in windows.items()}
        # Review B1: each day's expected state is pinned; F08's ambiguous-cohort day is not an empty verdict.
        assert states == EXPECTED_DAYS, states
        assert windows["2026-10-15"]["window_claim_level"] == "LIMITED" and windows["2026-10-15"]["window_limitations"]
        assert windows["2026-10-19"]["window_claim_level"] == "INDETERMINATE"
        assert any(x.startswith("AMBIGUOUS_COHORT") for x in windows["2026-10-19"]["window_limitations"])
        for d, w in windows.items():
            if w["state"] == "NO_FINDING":
                assert w["assessment_status"] == "CURRENT" and w["window_claim_level"] != "INDETERMINATE"

    def test_stale_and_match_pending_are_not_verdicts(self, store, engine) -> None:
        runner = CaseRunner(store, engine)
        run_case(runner, SPEC["cases"][0])
        client = client_for(runner)
        [f] = runner.reload()["findings"]
        runner.step({"do": "deliver", "decided": "2026-10-31T08:00:00Z", "blocks": [
            {"from": "2026-10-06T08:25:00Z", "to": "2026-10-06T08:30:00Z", "pv": "41", "only": ["pv"]}]})
        body = get(client, f["id"])
        assert body["state"]["projection"] == "STALE" and not body["state"]["claim_is_current"]
        assert body["state"]["lifecycle"] == "SUPPORTED"  # as recorded, not current
        window = client.get("/api/sites/KOBO-001/finding-windows/2026-10-06").json()
        assert window["state"] == "STALE" and "not a no-Finding verdict" in window["note"]
        runner.step({"do": "assess"})
        assert get(client, f["id"])["state"]["projection"] == "FINDING_MATCH_PENDING"
        assert client.get("/api/sites/KOBO-001/finding-windows/2026-10-06").json()["state"] == "FINDING_MATCH_PENDING"
        runner.match()
        assert get(client, f["id"])["state"]["projection"] == "CURRENT"

    def test_a_complete_day_without_candidate_is_no_finding(self, store, engine) -> None:
        runner = CaseRunner(store, engine)
        runner.step({"do": "deliver", "decided": "2026-10-30T08:00:00Z", "blocks": [
            {"from": "2026-10-25T08:00:00Z", "to": "2026-10-25T09:00:00Z", "pv": "5", "dis": "5", "soc": "80",
             "stop_before": True, "stop_after": True}]})
        runner.step({"do": "assess"})
        client = client_for(runner)
        before = client.get("/api/sites/KOBO-001/finding-windows/2026-10-25").json()
        runner.match()
        window = client.get("/api/sites/KOBO-001/finding-windows/2026-10-25").json()
        assert not window["has_candidate_segment"] and window["findings"] == [], window
        assert window["assessment_status"] == "CURRENT" and window["window_claim_level"] != "INDETERMINATE"
        # Q18: before any matcher pass covers the selection it is not yet a no-Finding verdict
        assert before["state"] == "FINDING_MATCH_PENDING" and not before["finding_match"]["matched"]
        assert window["state"] == "NO_FINDING" and window["finding_match"]["matched"]
        assert window["selected_window_assessment_revision_id"] and window["selected_run_id"]
