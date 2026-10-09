"""S2-02 phase 3a item 5: the legacy replay comparison and the cutover predicate (no database)."""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from test_t027_ingestion import envelope

from assetops_backend.evidence.adapters.legacy_comparison_file import ComparisonReportFiles
from assetops_backend.evidence.legacy_comparison import compare, permits_cutover
from assetops_backend.evidence.models import AcceptedRecord, BatchProgress, SiteEvidence
from assetops_contracts.committed_artifact import envelope_content_digest
from assetops_contracts.source_envelope import canonical_envelope_json

TENANT, SITE = UUID(int=1), UUID(int=2)


def legacy_record(minute: int) -> AcceptedRecord:
    e = envelope(minute)
    body = canonical_envelope_json(e)
    return AcceptedRecord(
        message_id=e.message_id, envelope_text=body, content_digest=envelope_content_digest(body),
        site_id=e.site_id, source_id=e.source_id, gateway_id=e.gateway_id, device_id=e.device_id,
        signal_id=e.signal_id, family="MEASUREMENT", measurement=None, source_time=e.source_time,
        published_at=e.published_at, received_at=e.published_at, batch_id="b-1", source_mode="SIMULATED",
        mapping_set_id="kobo-gateway-map", mapping_version=1, foundation_version=1,
        foundation_valid_from="2026-01-01T00:00:00Z", original_value="100", original_unit="L",
        normalized_value="100", normalized_unit="L", quality="GOOD", unavailable_reason=None,
        interval_start=None, interval_end=None,
    )


def legacy_site(records: list[AcceptedRecord]) -> SiteEvidence:
    batch = BatchProgress(
        batch_id="b-1", site_id="SITE", source_id="s", gateway_id="g", source_mode="SIMULATED", batch_digest="d",
        total=len(records), processed=len(records), accepted=len(records), duplicates=0, rejected=0, conflicts=0,
        status="COMPLETED", refusal_kind=None, refusal_detail=None, started_at="2026-09-22T00:00:00Z",
        completed_at="2026-09-22T00:00:00Z", window_start=None, window_end=None,
    )
    return SiteEvidence(site_id="SITE", records=tuple(records), batches=(batch,))


def run(legacy: SiteEvidence, *, digests=None, bound=None) -> dict:
    channels = {("fuel-level-sensor", "fuel-level")} if bound is None else bound
    return compare(site_code="KOBO-001", tenant_id=TENANT, site_id=SITE, legacy=legacy,
                   ledger_digests=digests or {}, bound_channels=channels,
                   legacy_dispatch_claims=[{"analytic_id": "dispatch"}], recompute_jobs=[],
                   compared_at="2026-10-09T09:00:00.000000Z")


def test_a_replayed_legacy_set_that_matches_passes_as_a_non_empty_comparison() -> None:
    report = run(legacy_site([legacy_record(1), legacy_record(2)]))
    assert (report["outcome"], report["empty_set"], report["replay"]["matched"]) == ("PASSED", False, 2)
    assert report["s3_fixtures"]["legacy_dispatch_claims"] == [{"analytic_id": "dispatch"}]
    assert permits_cutover(report, "KOBO-001", SITE) == (True, "")


def test_a_tampered_envelope_or_ledger_mismatch_fails_and_closes_the_cutover() -> None:
    tampered = replace(legacy_record(1), content_digest="0" * 64)
    report = run(legacy_site([tampered]))
    assert report["outcome"] == "FAILED" and report["exceptions"][0]["kind"] == "DIGEST_MISMATCH"
    assert permits_cutover(report, "KOBO-001", SITE)[0] is False
    good = legacy_record(1)
    other = run(legacy_site([good]), digests={good.message_id: "f" * 64})
    assert [e["kind"] for e in other["exceptions"]] == ["LEDGER_DIGEST_MISMATCH"]
    unparseable = run(legacy_site([replace(good, envelope_text="{}")]))
    assert "REPLAY_PARSE_FAILED" in {e["kind"] for e in unparseable["exceptions"]}


def test_an_unmapped_legacy_channel_is_a_recorded_exception_not_a_guessed_mapping() -> None:
    report = run(legacy_site([legacy_record(1)]), bound=set())
    assert report["outcome"] == "EXCEPTIONS"
    assert [e["kind"] for e in report["exceptions"]] == ["CONFIGURATION_UNMAPPED"]
    assert permits_cutover(report, "KOBO-001", SITE)[0] is False


def test_an_empty_set_is_stated_and_reports_are_never_overwritten(tmp_path) -> None:
    report = run(SiteEvidence(site_id="KOBO-001"))
    assert report["empty_set"] is True and report["statement"].startswith("Empty-set comparison")
    files = ComparisonReportFiles(tmp_path)
    first = files.write(report)
    newer = dict(report, report_id="z" * 8, compared_at="2026-10-09T10:00:00.000000Z", outcome="FAILED")
    files.write(newer)
    assert first.exists() and files.latest("kobo-001")["outcome"] == "FAILED"
    assert permits_cutover(files.latest("KOBO-001"), "KOBO-001", SITE)[0] is False
    assert permits_cutover(None, "KOBO-001", SITE)[0] is False
