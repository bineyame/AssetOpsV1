"""S4-03 phase 1: Finding Evidence and History reads over `s4-finding-cases-v1` (PostgreSQL).

The committed specification runs through ingestion, the S3 worker and the matcher (the S4-01 pipeline; no
Finding truth is inserted). Every revision's Evidence and every Finding's History are read through the HTTP
routes in small pages and compared with the stored relations. One test then breaks an accepted row and an
envelope in its own disposable test database to prove a broken join is named, never dropped or zero.
Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import pytest

from test_s4_finding_store_postgres import SPEC, URL, CaseRunner, _t, run_case  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.evidence.composition import build_public_provenance
    from assetops_backend.evidence.public_provenance import basis_sha256
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
    from assetops_backend.analytics.dispatch_read import DispatchReadService
    from assetops_backend.analytics.finding_read import FindingReadService
    from assetops_backend.finding_api import build_finding_router

SITE = "KOBO-001"


def client_for(runner: "CaseRunner", gate_open: bool = True) -> "TestClient":
    # W3-01 Run 3 q3: the production composition's public resolver (`build_finding_read_service`).
    reads = FindingReadService(PostgresFindingStore(URL), DispatchReadService(PostgresAssessmentStore(URL)),
                               build_public_provenance(URL))
    # OTHER-001 is a second Site code in the same tenant with a different Site ID: cross-Site denial.
    scope = {SITE: (SITE, runner.tenant, runner.site), "OTHER-001": ("OTHER-001", runner.tenant, uuid4())}
    app = FastAPI()
    app.include_router(build_finding_router(reads, scope.get, gate=lambda code, t, s: (
        gate_open, "test: gate open" if gate_open else "test: Performance comparison has not passed")))
    return TestClient(app)


def _get(client, path: str, **params) -> dict:
    response = client.get(path, params=params)
    assert response.status_code == 200, response.text
    return response.json()


def all_evidence(client, finding_id, revision_id, limit: int = 7) -> tuple[dict, list[dict]]:
    """Walk every Evidence page; returns the first body and every record."""
    first, records, offset = None, [], 0
    while True:
        body = _get(client, f"/api/sites/{SITE}/findings/{finding_id}/evidence", revision_id=revision_id,
                    offset=offset, limit=limit)
        first = first or body
        assert body["page"]["total"] == first["page"]["total"] and body["page"]["offset"] == offset
        records += body["records"]
        if body["page"]["next_offset"] is None:
            return first, records
        assert body["links"]["api_next_page"].endswith(f"offset={body['page']['next_offset']}&limit={limit}")
        offset = body["page"]["next_offset"]


def all_history(client, finding_id, limit: int = 2, **params) -> tuple[dict, list[dict]]:
    first, rows, after = None, [], 0
    while True:
        body = _get(client, f"/api/sites/{SITE}/findings/{finding_id}/history", after_revision_no=after,
                    limit=limit, **params)
        first = first or body
        rows += body["revisions"]
        if body["page"]["next_after_revision_no"] is None:
            return first, rows
        after = body["page"]["next_after_revision_no"]


def by_anchor(rows: dict, at: str) -> dict:
    return next(f for f in rows["findings"] if f["anchor_start"] == _t(at))


def _iso(value) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if value else None


def _same_instant(a: str | None, b: datetime | None) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return datetime.fromisoformat(a.replace("Z", "+00:00")) == b


class TestFindingEvidenceAndHistory:
    def test_every_revision_evidence_and_history_match_stored_rows(self, store, engine) -> None:
        runner = CaseRunner(store, engine)
        for case in SPEC["cases"]:
            run_case(runner, case)
        rows = runner.reload()
        client = client_for(runner)
        with engine.connect() as c:
            accepted = {str(r["id"]): dict(r) for r in (x._mapping for x in c.execute(text(
                "SELECT e.*, d.decided_at FROM accepted_evidence e JOIN ingestion_disposition d "
                "ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal WHERE e.site_id = :s"), {"s": runner.site}))}
            run_inputs = {}
            for run_id, eid in c.execute(text("SELECT run_id::text, evidence_id::text FROM analytic_run_evidence "
                                              "WHERE site_id = :s"), {"s": runner.site}):
                run_inputs.setdefault(run_id, set()).add(eid)
        cites = {}
        for a in rows["assessments"]:
            cites.setdefault(str(a["finding_revision_id"]), []).append(a)
        checked_records = 0
        for f in rows["findings"]:
            stored = [r for r in rows["revisions"] if r["finding_id"] == f["id"]]
            first, history = all_history(client, f["id"])
            # History: every stored revision in revision_no order, exhaustively paged, with stored facts.
            assert [h["id"] for h in history] == [str(r["id"]) for r in stored]
            assert first["page"]["total"] == len(stored)
            assert first["earlier_versions"] == ("NONE" if len(stored) == 1 else "PRESENT")
            assert first["selection"]["selected_by"] == "LATEST_RECORDED"
            assert [h["is_latest"] for h in history] == [i == len(stored) - 1 for i in range(len(stored))]
            for h, r in zip(history, stored):
                assert (h["revision_no"], h["transition"], h["lifecycle"]) == (r["revision_no"], r["transition"],
                                                                               r["lifecycle"])
                assert {k: float(v) for k, v in h["minutes"].items()} == {
                    "candidate": float(r["candidate_minutes"]), "necessary": float(r["necessary_minutes"]),
                    "indeterminate": float(r["indeterminate_minutes"])}
                assert _same_instant(h["times"]["recorded_at"], r["created_at"])
                assert h["primary_assessment_revision_id"] == str(r["assessment_revision_id"])
                assert h["cited_evidence"]["accepted_rows"] == "ALL_RESOLVED" and "lineage" not in h["cited_evidence"]
                assert "knowledge_at" not in h and "knowledge_cutoff" not in h["times"]

            for r in stored:
                rid = str(r["id"])
                body, records = all_evidence(client, f["id"], rid)
                cited = {str(e["evidence_id"]) for e in rows["evidence"] if str(e["finding_revision_id"]) == rid}
                # Complete cited membership across pages; distinct from (and inside) the run input set.
                assert [x["evidence_id"] for x in records] and {x["evidence_id"] for x in records} == cited
                # W3-01 Run 3 q3: the selected revision's W1 block with the public keys over its exact citations.
                sp = body["source_provenance"]
                assert sp["finding_revision_id"] == rid and sp["evidence_ids"] == sorted(cited)
                assert sp["classification"] == sp["state"] and "detail" in sp
                assert sp["basis_sha256"] == basis_sha256(runner.tenant, runner.site, [rid], sorted(cited))
                assert len(records) == len(cited) == body["counts"]["cited_total"] == body["counts"]["cited_resolved"]
                runs = {str(a["analytic_run_id"]) for a in cites[rid]}
                inputs = set().union(*(run_inputs.get(x, set()) for x in runs))
                assert body["counts"]["input_distinct_total"] == len(inputs) and cited <= inputs
                assert {x["analytic_run_id"]: x["input_evidence_count"] for x in body["counts"]["input_by_run"]} == {
                    x: len(run_inputs.get(x, set())) for x in runs}
                assert body["lineage"]["status"] == "COMPLETE", body["lineage"]
                # N1: the by-measurement aggregate covers the whole cited set, equal to the stored rows' roles.
                by_role: dict[str, set] = {}
                for e in cited:
                    by_role.setdefault(accepted[e]["role"], set()).add(e)
                assert {g["role"]: g["count"] for g in body["provenance"]["cited_evidence_by_role"]} == {
                    k: len(v) for k, v in by_role.items()}
                assert {g["role"]: set(g["source_ids"]) for g in body["provenance"]["cited_evidence_by_role"]} == {
                    k: {str(accepted[e]["source_id"]) for e in v} for k, v in by_role.items()}
                assert body["lineage"]["cited_set_digest"]["status"] == "VERIFIED"
                assert body["selection"] == {**body["selection"], "revision_id": rid,
                                             "selected_by": "EXACT_REVISION_ID"}
                assert {a["assessment_revision_id"] for a in body["assessments"]} == {
                    str(a["assessment_revision_id"]) for a in cites[rid]}
                assert set(body["links"]["assessment_revisions"]) == {a["assessment_revision_id"]
                                                                      for a in body["assessments"]}
                for x in records:
                    row = accepted[x["evidence_id"]]
                    assert x["lineage_status"] == "RESOLVED" and x["broken_links"] == []
                    assert x["envelope"] == {"sha256": row["envelope_sha256"], "digest_verified": True}
                    assert hashlib.sha256(row["envelope_text"].encode("utf-8")).hexdigest() == row["envelope_sha256"]
                    assert (x["message_id"], x["batch"]["batch_id"], x["role"], x["unit"], x["quality"]) == (
                        row["message_id"], str(row["batch_id"]), row["role"], row["normalized_unit"],
                        row["quality"])
                    assert x["value"] == row["normalized_value_text"]
                    assert (x["source"]["gateway_id"], x["source"]["source_id"], x["source"]["sequence_epoch"],
                            x["source"]["sequence"], x["source"]["source_mode"]) == (
                        str(row["gateway_id"]), str(row["source_id"]), row["sequence_epoch"], row["sequence"],
                        row["source_mode"])
                    assert _same_instant(x["source_time"], row["source_time"])
                    assert _same_instant(x["accepted_at"], row["decided_at"])
                    assert (x["accepted_as"]["foundation_revision_id"], x["accepted_as"]["binding_set_revision_id"],
                            x["accepted_as"]["binding_revision_id"]) == (
                        str(row["foundation_revision_id"]), str(row["binding_set_revision_id"]),
                        str(row["binding_revision_id"]))
                    assert set(x["used_by"]["assessment_revision_ids"]) <= {
                        str(a["assessment_revision_id"]) for a in cites[rid]}
                    assert x["used_by"]["run_ids"] and set(x["used_by"]["run_ids"]) <= runs
                    checked_records += 1
                # Record links use the exact accepted evidence ID, never the message ID.
                first_page = body["records"]
                assert body["links"]["records"] == {
                    x["evidence_id"]: f"/api/sites/{SITE}/evidence/records/{x['evidence_id']}" for x in first_page}
        assert checked_records > 0

        # F01-gateway is environment-bound (tools/s4_finding_cases.py); here every case is the labelled fixture.
        # F04: the old revision's cited set and minutes stay pinned; late-accepted IDs appear only on revision 2.
        f04 = by_anchor(rows, "2026-10-13T08:30:00Z")
        _, h04 = all_history(client, f04["id"])
        assert [h["transition"] for h in h04[:2]] == ["OPENED", "SUPPORT_CHANGED"]
        old_body, old = all_evidence(client, f04["id"], h04[0]["id"])
        _, new = all_evidence(client, f04["id"], h04[1]["id"])
        late = _t("2026-10-30T11:30:00Z")
        old_ids, new_ids = {x["evidence_id"] for x in old}, {x["evidence_id"] for x in new}
        assert new_ids - old_ids and all(_same_instant(x["accepted_at"], accepted[x["evidence_id"]]["decided_at"])
                                         for x in new)
        assert all(accepted[i]["decided_at"] < late for i in old_ids)
        assert any(accepted[i]["decided_at"] >= late for i in new_ids - old_ids)
        assert old_body["revision"]["minutes"] == h04[0]["minutes"] and h04[0]["minutes"] != h04[1]["minutes"]
        pinned_first, pinned_history = all_history(client, f04["id"], revision_id=h04[0]["id"])
        assert pinned_first["selection"]["selected_by"] == "EXACT_REVISION_ID"
        assert [h["is_selected"] for h in pinned_history][:2] == [True, False]
        assert pinned_history[0]["is_latest"] is False

        # F05: closure/unconfirmed transitions remain recorded history.
        f05 = next(f for f in rows["findings"] if f["anchor_start"].date() == date(2026, 10, 21))
        _, h05 = all_history(client, f05["id"])
        transitions = [h["transition"] for h in h05]
        assert "UNCONFIRMED" in transitions and transitions[-1] == "NO_LONGER_SUPPORTED"
        assert h05[-1]["is_latest"] and not h05[0]["is_latest"]

        # F06: merged Finding keeps its own History and Evidence; the relation names the canonical one.
        [merge] = rows["merges"]
        old_first, old_history = all_history(client, merge["superseded_finding_id"])
        assert old_first["relations"]["canonical_finding_id"] == str(merge["canonical_finding_id"])
        assert old_history[-1]["lifecycle"] == "MERGED"
        all_evidence(client, merge["superseded_finding_id"], old_history[-1]["id"])

        # F08: retry/absent basis records no Finding over 2026-10-19 (not an empty History).
        assert not any(_t("2026-10-19T00:00:00Z") <= f["anchor_start"] < _t("2026-10-20T00:00:00Z")
                       for f in rows["findings"])
        before = len(rows["revisions"])
        runner.match()
        assert len(runner.reload()["revisions"]) == before

        # Refusals: unknown root, foreign revision, cross-Site, unknown Site, malformed IDs.
        target = rows["findings"][0]
        foreign = next(r for r in rows["revisions"] if r["finding_id"] != target["id"])
        for child in ("evidence", "history"):
            base = f"/api/sites/{SITE}/findings"
            assert client.get(f"{base}/{uuid4()}/{child}").status_code == 404
            assert client.get(f"{base}/{target['id']}/{child}", params={"revision_id": foreign["id"]}
                              ).status_code == 404
            assert client.get(f"/api/sites/OTHER-001/findings/{target['id']}/{child}").status_code == 404
            assert client.get(f"/api/sites/NOPE/findings/{target['id']}/{child}").status_code == 404
            assert client.get(f"{base}/not-a-uuid/{child}").status_code == 422

        # Closed Performance cutover: unpinned child reads are 409; pinned ones are audit material only.
        closed = client_for(runner, gate_open=False)
        for child in ("evidence", "history"):
            response = closed.get(f"/api/sites/{SITE}/findings/{f04['id']}/{child}")
            assert response.status_code == 409 and response.json()["detail"]["code"] == "PERFORMANCE_CUTOVER_CLOSED"
        audit = _get(closed, f"/api/sites/{SITE}/findings/{f04['id']}/evidence", revision_id=h04[0]["id"])
        assert audit["audit_only"]["non_current"] and audit["links"]["assessment_revisions"] == {}
        assert audit["currentness"]["state"] == "SOURCE_CLOSED" and audit["links"]["performance"]["status"] == "CLOSED"
        assert {x["evidence_id"] for x in audit["records"]} <= old_ids
        audit_history = _get(closed, f"/api/sites/{SITE}/findings/{f04['id']}/history", revision_id=h04[0]["id"])
        assert audit_history["audit_only"]["non_current"] and audit_history["selection"]["revision_id"] == h04[0]["id"]

    def test_a_broken_accepted_or_envelope_join_is_named_not_dropped(self, store, engine) -> None:
        runner = CaseRunner(store, engine)
        run_case(runner, SPEC["cases"][0])
        rows = runner.reload()
        [f] = rows["findings"]
        rid = str(rows["revisions"][-1]["id"])
        client = client_for(runner)
        _, records = all_evidence(client, f["id"], rid, limit=500)
        gone, tampered = records[0]["evidence_id"], records[1]["evidence_id"]
        # Test-only corruption of this disposable database: replica mode skips FK and immutability triggers.
        with engine.begin() as c:
            c.execute(text("SET LOCAL session_replication_role = replica"))
            c.execute(text("UPDATE accepted_evidence SET envelope_text = envelope_text || ' ' WHERE id = :e"),
                      {"e": UUID(tampered)})
            c.execute(text("DELETE FROM analytic_run_evidence WHERE evidence_id = :e"), {"e": UUID(gone)})
            c.execute(text("DELETE FROM ingestion_disposition WHERE accepted_evidence_id = :e"), {"e": UUID(gone)})
            c.execute(text("DELETE FROM accepted_evidence WHERE id = :e"), {"e": UUID(gone)})
        body, after = all_evidence(client, f["id"], rid, limit=500)
        assert body["counts"]["cited_total"] == len(records) and body["counts"]["cited_unresolved"] == 1
        assert body["counts"]["cited_resolved"] == len(records) - 1
        assert body["lineage"]["status"] == "BROKEN"
        assert sum(g["count"] for g in body["provenance"]["cited_evidence_by_role"]) == len(records) - 1
        assert body["lineage"]["cited_set_digest"]["status"] == "NOT_VERIFIED"
        broken = {b["evidence_id"]: b["links"] for b in body["lineage"]["broken_records"]}
        assert broken == {gone: ["ACCEPTED_EVIDENCE"], tampered: ["ENVELOPE_DIGEST"]}
        row = {x["evidence_id"]: x for x in after}
        assert row[gone]["resolved"] is False and "role" not in row[gone] and "withheld" in row[gone]
        # Q2: product-safe human words served with the stable codes (no engineering vocabulary).
        assert body["lineage"]["words"]["ENVELOPE_DIGEST"] == "the stored original message does not match its saved fingerprint"
        assert row[gone]["withheld"] == ("no accepted record with this reference exists for this site, "
                                         "so no measurement, source or message is shown")
        assert not any(w in row[gone]["withheld"].lower() for w in ("envelope", "binding", "mapping"))
        assert row[tampered]["envelope"]["digest_verified"] is False and row[tampered]["lineage_status"] == "BROKEN"
        assert gone not in body["links"]["records"] and tampered in body["links"]["records"]
        history = _get(client, f"/api/sites/{SITE}/findings/{f['id']}/history")
        [h] = [x for x in history["revisions"] if x["id"] == rid]
        assert h["cited_evidence"]["count"] == len(records) and h["cited_evidence"]["resolved"] == len(records) - 1
        assert h["cited_evidence"]["accepted_rows"] == "UNRESOLVED_PRESENT" and "lineage" not in h["cited_evidence"]

    def test_envelope_only_tamper_is_broken_in_evidence_and_not_complete_in_history(self, store, engine) -> None:
        runner = CaseRunner(store, engine)
        run_case(runner, SPEC["cases"][0])
        rows = runner.reload()
        [f] = rows["findings"]
        rid = str(rows["revisions"][-1]["id"])
        client = client_for(runner)
        _, records = all_evidence(client, f["id"], rid, limit=500)
        tampered = records[0]["evidence_id"]
        with engine.begin() as c:
            c.execute(text("SET LOCAL session_replication_role = replica"))
            c.execute(text("UPDATE accepted_evidence SET envelope_text = envelope_text || ' ' WHERE id = :e"),
                      {"e": UUID(tampered)})
        body, _ = all_evidence(client, f["id"], rid, limit=500)
        assert body["lineage"]["status"] == "BROKEN"
        assert {b["evidence_id"]: b["links"] for b in body["lineage"]["broken_records"]} == {
            tampered: ["ENVELOPE_DIGEST"]}
        history = _get(client, f"/api/sites/{SITE}/findings/{f['id']}/history")
        [h] = [x for x in history["revisions"] if x["id"] == rid]
        # All accepted rows still resolve, so History says only that; it makes no lineage claim.
        assert h["cited_evidence"]["accepted_rows"] == "ALL_RESOLVED"
        assert "lineage" not in h["cited_evidence"] and "COMPLETE" not in str(h["cited_evidence"])
        assert "Evidence read" in h["cited_evidence"]["note"]
