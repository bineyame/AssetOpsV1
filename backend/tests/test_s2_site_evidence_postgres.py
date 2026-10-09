"""S2-02 phase 3a: Site Evidence reads over the central ledger, behind the legacy comparison gate.

Against a real migrated PostgreSQL (`ASSETOPS_TEST_DATABASE_URL`). The four Site
Evidence routes answer from the ledger for an imported Site only once its newest
comparison record permits it; otherwise they keep 409 AWAITING_EVIDENCE_MIGRATION.
"""

from __future__ import annotations

import json
import os
from datetime import timedelta
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import (
        LEDGER_TABLES,
        RECEIVED,
        Kit,
        _z,
        converted_enabled,
        submit,
    )

    from assetops_backend.evidence.adapters.legacy_comparison_file import ComparisonReportFiles
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_reads import ImportedEvidenceReads
    from assetops_backend.evidence.ledger_service import BatchIngestionService, SimulatedCrash
    from assetops_backend.evidence.legacy_comparison import (
        compare,
        environment_identity,
        legacy_inventory,
        store_root_identity,
    )
    from assetops_backend.evidence.models import SiteEvidence
    from assetops_backend.evidence_api import build_evidence_router
    from assetops_backend.evidence_migration import main as comparison_cli

LATER = RECEIVED + timedelta(minutes=7)
ENV = environment_identity(URL) if URL else None
ROOT = store_root_identity("c:\ws-a\var\evidence", "c:\ws-a\var\commits") if URL else None


class _NoSites:
    def get_site(self, site_id):  # pragma: no cover - an imported Site never reaches the legacy path
        raise AssertionError(site_id)


@pytest.fixture()
def kit(store, engine):  # noqa: F811
    _, outcome = converted_enabled(store, engine)
    return Kit(engine, outcome.published.changed.id)


def empty_set_report(kit, **changes) -> dict:
    report = compare(
        site_code="KOBO-001", tenant_id=kit.principal.tenant_id, site_id=kit.principal.site_id,
        legacy=SiteEvidence(site_id="KOBO-001"), ledger_digests={}, bound_channels=(),
        legacy_dispatch_claims=[], recompute_jobs=[], compared_at="2026-10-09T09:00:00.000000Z",
        committed_artifacts=(), environment=ENV, store_root=ROOT,
    )
    report.update(changes)
    return report


def client(kit, report: dict | None, legacy: SiteEvidence | None = None, store_root: str | None = None) -> TestClient:
    from assetops_backend.evidence.service import IngestionService

    principal = kit.principal
    reads = ImportedEvidenceReads(
        PostgresEvidenceLedger(URL),
        lambda code: ("KOBO-001", principal.tenant_id, principal.site_id) if code.lower() == "kobo-001" else None,
        lambda code: report,
        lambda code: legacy_inventory(SiteEvidence(site_id=code) if legacy is None else legacy, ()),
        ENV,
        lambda: ROOT if store_root is None else store_root,
    )
    app = FastAPI()
    app.include_router(build_evidence_router(
        IngestionService(None, _NoSites()), _NoSites(), imported_reads=reads))  # type: ignore[arg-type]
    return TestClient(app)


def window(kit, first_minute: int, last_minute: int) -> str:
    return f"from={_z(kit.start + timedelta(minutes=first_minute))}&to={_z(kit.start + timedelta(minutes=last_minute))}"


def load_scenario(kit) -> dict:
    """Accepted, duplicate, conflict, rejected sibling, a rejected-only minute and
    a partial batch resumed later. Returns the receipts by name."""
    pv = "pv-inverter-controller"
    receipts = {"accepted": submit(kit, kit.seal(kit.pv(3))).receipt}
    receipts["duplicate"] = submit(kit, kit.seal([kit.pv(1)[0], kit.envelope(pv, 4, 3, "1.5")])).receipt
    receipts["conflict"] = submit(kit, kit.seal([kit.envelope(pv, 2, 1, "7")])).receipt
    receipts["sibling"] = submit(kit, kit.seal([
        kit.envelope(pv, 5, 30, "2"), kit.envelope(pv, 6, 31, "2", signal_id="unbound-signal")])).receipt
    receipts["rejected_only"] = submit(kit, kit.seal([kit.envelope(pv, 7, 60, "2", signal_id="unbound-signal")])).receipt
    partial = kit.seal([kit.envelope(pv, 10 + i, 120 + i, "3") for i in range(5)])
    with pytest.raises(SimulatedCrash):
        submit(kit, partial, chunk_size=2, crash_after_chunks=1)
    receipts["partial_body"] = partial
    return receipts


class TestCutoverGate:
    ROUTES = ("evidence", "evidence/records", "evidence/records/x", "evidence/rejections")

    @pytest.mark.parametrize("report_change", [
        "missing", "failed", "exceptions", "other-site", "unstated-empty-set",
    ])
    def test_every_route_stays_awaiting_migration_without_a_passing_record(self, kit, report_change) -> None:
        report = {
            "missing": None,
            "failed": empty_set_report(kit, outcome="FAILED"),
            "exceptions": empty_set_report(kit, outcome="EXCEPTIONS"),
            "other-site": empty_set_report(kit, site_uuid=str(UUID(int=7))),
            "unstated-empty-set": empty_set_report(kit, statement="matched"),
        }[report_change]
        http = client(kit, report)
        for route in self.ROUTES:
            answer = http.get(f"/api/sites/KOBO-001/{route}")
            assert answer.status_code == 409, route
            assert answer.json()["detail"]["code"] == "AWAITING_EVIDENCE_MIGRATION"

    def test_an_explicit_empty_set_comparison_opens_the_ledger_reads_and_says_so(self, kit) -> None:
        body = client(kit, empty_set_report(kit)).get("/api/sites/KOBO-001/evidence").json()
        assert body["store"] == "POSTGRES" and body["state"] == "NO_DATA"
        assert body["migration"]["outcome"] == "PASSED" and body["migration"]["empty_set"] is True
        assert body["migration"]["statement"].startswith("Empty-set comparison")
        assert "store_root" not in body["migration"] and ROOT not in json.dumps(body)


class TestCutoverStoreRoot:
    def test_same_database_and_zero_inventory_from_another_store_root_stays_closed(self, kit, tmp_path) -> None:
        """Q26: the same tenant, Site, database and zero inventory read through a second
        workspace's store root keeps every route closed; no path or root is served."""
        other = store_root_identity(str(tmp_path / "evidence"), str(tmp_path / "commits"))
        http = client(kit, empty_set_report(kit), store_root=other)
        for route in TestCutoverGate.ROUTES:
            answer = http.get(f"/api/sites/KOBO-001/{route}")
            assert answer.status_code == 409, route
            assert answer.json()["detail"]["code"] == "AWAITING_EVIDENCE_MIGRATION"
            assert "another local evidence store" in answer.json()["detail"]["message"]
            assert str(tmp_path) not in answer.text and other not in answer.text


class TestCutoverFreshness:
    def test_legacy_evidence_added_after_an_empty_set_pass_returns_awaiting_migration(self, kit) -> None:
        from test_s2_legacy_comparison import legacy_record, legacy_site

        assert client(kit, empty_set_report(kit)).get("/api/sites/KOBO-001/evidence").status_code == 200
        http = client(kit, empty_set_report(kit), legacy=legacy_site([legacy_record(1)]))
        for route in TestCutoverGate.ROUTES:
            answer = http.get(f"/api/sites/KOBO-001/{route}")
            assert answer.status_code == 409, route
            assert answer.json()["detail"]["code"] == "AWAITING_EVIDENCE_MIGRATION"
            assert "changed" in answer.json()["detail"]["message"]


class TestSelectedWindow:
    def test_states_counts_clocks_and_received_at_for_the_selected_window(self, kit) -> None:
        receipts = load_scenario(kit)
        http = client(kit, empty_set_report(kit))
        whole = http.get("/api/sites/KOBO-001/evidence").json()
        assert whole["window"]["basis"] == "ALL" and whole["window"]["half_open"] is True
        assert set(whole["states"]) >= {"ACCEPTED", "PARTIAL_BATCH", "CONFLICTING", "STALE_PROJECTION"}
        assert whole["projection"]["status"] == "STALE" and whole["projection"]["pending_jobs"] >= 1
        assert [b["partial"] for b in whole["batches"]].count(True) == 1

        first = http.get(f"/api/sites/KOBO-001/evidence?{window(kit, 0, 10)}").json()
        assert first["counts"] == {"accepted": 4, "duplicates": 1, "rejected": 0, "conflicts": 1,
                                   "rejected_without_source_time": 0}
        assert "CONFLICTING" in first["states"]
        source = next(s for s in first["sources"] if s["accepted_in_window"])
        assert source["clocks"] == {"source_time": "RUN_VIRTUAL", "published_at": "RUN_VIRTUAL",
                                    "received_at": "SERVER_RECEIVED_AT"}
        assert source["last_received_at"] == "2026-10-09T08:30:00.123456Z"
        assert first["extent"]["accepted_total"] == 4 + 1 + 2  # plus minute 30 and the 2 decided partial ordinals

        sibling = http.get(f"/api/sites/KOBO-001/evidence?{window(kit, 30, 32)}").json()
        assert sibling["state"] == "ACCEPTED" and sibling["counts"]["rejected"] == 1
        rejected_only = http.get(f"/api/sites/KOBO-001/evidence?{window(kit, 60, 61)}").json()
        assert rejected_only["state"] == "REJECTED_ONLY" and rejected_only["counts"]["accepted"] == 0
        nothing = http.get(f"/api/sites/KOBO-001/evidence?{window(kit, 90, 91)}").json()
        assert nothing["state"] == "NO_DATA"
        partial = http.get(f"/api/sites/KOBO-001/evidence?{window(kit, 120, 130)}").json()
        assert "PARTIAL_BATCH" in partial["states"]
        assert receipts["accepted"].received_at == "2026-10-09T08:30:00.123456Z"

    def test_records_page_by_a_stable_cursor_and_a_window_is_half_open(self, kit) -> None:
        load_scenario(kit)
        http = client(kit, empty_set_report(kit))
        seen, cursor = [], None
        while True:
            query = f"limit=2&{window(kit, 0, 31)}" + (f"&cursor={cursor}" if cursor else "")
            page = http.get(f"/api/sites/KOBO-001/evidence/records?{query}").json()
            assert page["total"] == 5
            seen += [r["message_id"] for r in page["records"]]
            cursor = page["next_cursor"]
            if cursor is None:
                break
        assert len(seen) == len(set(seen)) == 5  # minute 31 is the excluded end; minute 30 is in
        bad = http.get("/api/sites/KOBO-001/evidence/records?cursor=nope")
        assert bad.status_code == 422 and bad.json()["detail"]["code"] == "INVALID_CURSOR"
        inverted = http.get(f"/api/sites/KOBO-001/evidence?{window(kit, 5, 1)}")
        assert inverted.status_code == 422


class TestRecordLineage:
    def test_a_record_opens_values_envelope_accepted_as_revisions_receipt_and_duplicate(self, kit, engine) -> None:  # noqa: F811
        receipts = load_scenario(kit)
        http = client(kit, empty_set_report(kit))
        first_id = receipts["accepted"].dispositions[0].evidence_id
        record = http.get(f"/api/sites/KOBO-001/evidence/records/{first_id}").json()
        assert record["original"]["value"] == "1.5" and record["normalized"]["unit"]
        assert record["envelope"]["text"] == kit.pv(1)[0]
        assert record["accepted_as"]["binding_revision_id"] and record["accepted_as"]["foundation_revision_id"]
        assert record["receipt"]["batch_id"] == receipts["accepted"].batch_id
        assert (record["receipt"]["ordinal"], record["receipt"]["decision"]) == (0, "ACCEPTED")
        assert [d["batch_id"] for d in record["duplicates"]] == [receipts["duplicate"].batch_id]
        by_message = http.get(f"/api/sites/KOBO-001/evidence/records/{record['message_id']}").json()
        assert by_message["evidence_id"] == first_id

        rejections = http.get("/api/sites/KOBO-001/evidence/rejections").json()
        assert rejections["duplicates"][0]["first_accepted_evidence_id"] == first_id
        assert http.get("/api/sites/KOBO-001/evidence/records/00000000-0000-0000-0000-000000000000").status_code == 404

    def test_a_conflict_preserves_the_original_and_opens_the_conflicting_envelope(self, kit) -> None:
        receipts = load_scenario(kit)
        http = client(kit, empty_set_report(kit))
        original_id = receipts["accepted"].dispositions[1].evidence_id
        record = http.get(f"/api/sites/KOBO-001/evidence/records/{original_id}").json()
        assert record["original"]["value"] == "1.5"
        [conflict] = record["conflicts"]
        assert conflict["batch_id"] == receipts["conflict"].batch_id and conflict["kind"] == "MESSAGE_CONFLICT"
        assert json.loads(conflict["envelope_text"])["payload"]["value"] == "7"
        listed = http.get(f"/api/sites/KOBO-001/evidence/rejections?batch={receipts['conflict'].batch_id}").json()
        assert listed["conflicts"][0]["conflicts_with_evidence_id"] == original_id

    def test_a_conflict_is_placed_by_its_own_source_time_with_the_original_as_lineage(self, kit) -> None:
        pv = "pv-inverter-controller"
        accepted = submit(kit, kit.seal(kit.pv(3))).receipt
        original_id = accepted.dispositions[1].evidence_id
        submit(kit, kit.seal([kit.envelope(pv, 2, 45, "7")]))  # same message, a different source time
        http = client(kit, empty_set_report(kit))
        original = http.get(f"/api/sites/KOBO-001/evidence/records/{original_id}").json()
        own = http.get(f"/api/sites/KOBO-001/evidence?{window(kit, 40, 50)}").json()
        assert own["counts"]["conflicts"] == 1 and "CONFLICTING" in own["states"]
        before = http.get(f"/api/sites/KOBO-001/evidence?{window(kit, 0, 10)}").json()
        assert before["counts"]["conflicts"] == 0 and "CONFLICTING" not in before["states"]
        [conflict] = http.get("/api/sites/KOBO-001/evidence/rejections").json()["conflicts"]
        assert conflict["source_time"] == _z(kit.start + timedelta(minutes=45))
        assert conflict["conflicts_with_source_time"] == original["source_time"] != conflict["source_time"]

    def test_received_at_is_the_first_batch_receipt_not_a_later_ordinal_decision(self, kit) -> None:
        receipts = load_scenario(kit)
        resumed = BatchIngestionService(PostgresEvidenceLedger(URL), Clock(LATER), chunk_size=2)
        done = resumed.submit(kit.principal, receipts["partial_body"].encode()).receipt
        assert done.status == "COMPLETED"
        http = client(kit, empty_set_report(kit))
        last = done.dispositions[-1].evidence_id
        record = http.get(f"/api/sites/KOBO-001/evidence/records/{last}").json()
        assert record["received_at"] == record["receipt"]["received_at"] == "2026-10-09T08:30:00.123456Z"
        assert record["receipt"]["decided_at"] == "2026-10-09T08:37:00.123456Z"
        after = http.get(f"/api/sites/KOBO-001/evidence?{window(kit, 120, 130)}").json()
        assert "PARTIAL_BATCH" not in after["states"] and after["counts"]["accepted"] == 5


class TestComparisonCli:
    def test_the_explicit_run_records_an_empty_set_without_writing_the_ledger(self, kit, tmp_path, capsys) -> None:
        load_scenario(kit)
        before = kit.counts()

        class _Legacy:
            def list_sites(self):
                return ["SITET26"]

            def load_site(self, site_id):  # pragma: no cover - KOBO-001 has no legacy evidence here
                raise AssertionError(site_id)

            def canonical_root(self):
                return str(tmp_path / "evidence")

        class _Assessments:
            def load_history(self, site_id):
                from assetops_backend.analytics.models import AssessmentHistory
                return AssessmentHistory(site_id=site_id)

        class _NoCommits:
            def site_artifacts(self, site_key):
                return []

            def canonical_root(self):
                return str(tmp_path / "commits")

        reports = ComparisonReportFiles(tmp_path)
        code = comparison_cli(["run", "--tenant", "demo", "--site", "KOBO-001"], evidence_store=_Legacy(),
                              ledger=PostgresEvidenceLedger(URL), reports=reports, assessments=_Assessments(),
                              commit_store=_NoCommits(), environment=ENV)
        assert code == 0
        report = reports.latest("KOBO-001")
        assert (report["outcome"], report["empty_set"]) == ("PASSED", True)
        assert report["exceptions"] == [] and report["legacy"]["accepted_records"] == 0
        assert report["site_uuid"] == str(kit.principal.site_id)
        assert report["store_root"] == store_root_identity(str(tmp_path / "evidence"), str(tmp_path / "commits"))
        assert str(tmp_path) not in json.dumps(report)
        jobs = report["s3_fixtures"]["recompute_jobs"]
        assert jobs and {j["domain"] for j in jobs} == {"dispatch"}
        assert kit.counts() == before
        assert "Evidence cutover: permitted" in capsys.readouterr().out
        assert set(LEDGER_TABLES) <= set(before)
