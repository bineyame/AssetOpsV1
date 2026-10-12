"""Why a Not confirmed Finding version could not decide (S4-01 fix round 4, re-review R2/C8).

The read classifies each Indeterminate portion of the selected revision's cited interval assessments with the
dispatch-3.1 window rule (`_NOT_EVIDENCE_GAPS`): any other `missing` entry is a record gap. The strings below are
the real shapes dispatch-3.1 writes, built with its own helpers where it has one. No database.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from assetops_backend.analytics.dispatch_v3 import LOAD, PV_AVAILABLE, _missing
from assetops_backend.analytics.finding_read import (
    MODELLING, RECORD_GAP, UNSTATED, FindingReadService, indeterminate_cause, portion_cause)

T, S = uuid4(), uuid4()
RUNTIME = ("possibly within the configured minimum runtime (120 min from the first ON report); Candidate withheld, "
           "no policy Necessary claimed")
TRANSITION = "transition inside the segment: Candidate only when both ends are Candidate"
NOT_OBSERVED = "generator state not observed (gap over 20 minutes or unobserved)"
ENGINE_TERMS = ("PV", "PCS", "Candidate", "Necessary", "reserve 20", "headroom", "settings now in force")


def seg(classification: str, missing: list[str], reasons: list[str] | None = None) -> dict:
    return {"start": "2026-10-09T08:00:00Z", "end": "2026-10-09T08:10:00Z", "classification": classification,
            "reasons": reasons or ["PV available plus PCS discharge capability covers load with 10 % headroom",
                                   "reserve 20.0 %"], "missing": missing}


class Dispatch:
    def __init__(self, results: dict[str, list[dict]]) -> None:
        self.results, self.read = results, []

    def revision(self, tenant_id, site_id, revision_id):
        self.read.append(str(revision_id))
        return {"result": {"segments": self.results[str(revision_id)]}}

    def window(self, tenant_id, site_id, day):
        return {"status": "CURRENT", "status_reasons": [], "window_assessment": None}

    def _annotate(self, ids):
        return []


def rev(no: int, interval_id: UUID, limitations: list[str], lifecycle: str = "UNCONFIRMED") -> dict:
    at = datetime(2026, 10, 9, 8, tzinfo=timezone.utc)
    return {"id": uuid4(), "revision_no": no, "created_at": at, "transition": "UNCONFIRMED", "lifecycle": lifecycle,
            "claim_level": "LIMITED", "model_version": "dispatch-3.1", "matcher_version": "m",
            "episode_start": at, "episode_end": at, "candidate_minutes": 0, "necessary_minutes": 0,
            "indeterminate_minutes": 10, "basis_sha256": "b", "support_sha256": "s",
            "assessment_revision_id": interval_id, "cited_evidence_count": 0, "title": "t", "mechanism": "m",
            "analytic_id": "a", "analytic_run_id": 1, "window_assessment_revision_id": None, "claim": {},
            "limitations": limitations, "cited_evidence_sha256": "c", "input_evidence_sha256": "i",
            "assessments": [{"scope": "INTERVAL", "assessment_revision_id": interval_id, "window_start": at}]}


class Store:
    def __init__(self, revisions: list[dict]) -> None:
        self.revisions = revisions

    def finding_detail(self, tenant_id, site_id, finding_id):
        root = {k: None for k in ("id", "finding_key", "domain", "mechanism", "analytic_id", "generator_asset_id",
                                  "anchor_start", "anchor_assessment_revision_id", "cohort_sha256",
                                  "matcher_version", "opened_at", "recurs_after_finding_id", "split_from_finding_id")}
        return {"finding": root, "revisions": self.revisions,
                "relations": {"merged_into": [], "merged_from": [], "split_parts": [], "recurred_by": []}}

    def revision_lineage(self, tenant_id, site_id, finding_revision_id, off_bounds):
        return {"evidence": [], "runs": [], "off_reports": []}


def test_real_record_gap_shapes_classify_as_record_gaps() -> None:
    for missing in ([_missing(PV_AVAILABLE, "MISSING")], [_missing(LOAD, "NOT_GOOD")], [NOT_OBSERVED],
                    [RUNTIME, _missing(LOAD, "CONFLICTING")]):
        assert portion_cause(missing) == (RECORD_GAP, [])
    assert _missing(PV_AVAILABLE, "MISSING").endswith(": no accepted reading")


def test_minimum_runtime_reads_as_a_setting_in_plain_words() -> None:
    kind, plain = portion_cause([RUNTIME])
    assert kind == MODELLING
    cause = indeterminate_cause([{"kind": kind, "plain": plain}])
    assert cause["kind"] == MODELLING
    assert "No records are missing" in cause["sentence"]
    assert "120-minute minimum operating time after starting" in cause["sentence"]
    assert not any(term in cause["sentence"] for term in ENGINE_TERMS)


def test_unstated_and_empty() -> None:
    assert portion_cause([]) == (UNSTATED, [])
    assert indeterminate_cause([]) is None
    assert indeterminate_cause([{"kind": UNSTATED, "plain": []}])["kind"] == UNSTATED


def test_read_classifies_the_selected_revision_not_the_latest_and_ignores_open_bound_limitations() -> None:
    gap_id, setting_id = uuid4(), uuid4()
    dispatch = Dispatch({str(gap_id): [seg("CANDIDATE", []), seg("INDETERMINATE", [_missing(PV_AVAILABLE, "MISSING")])],
                         str(setting_id): [seg("INDETERMINATE", [RUNTIME, TRANSITION])]})
    # The earlier version has only OPEN_BOUND (a revision never carries EVIDENCE_GAP) and a minimum-runtime cause;
    # the latest version has a genuine missing reading and no limitation at all.
    first = rev(1, setting_id, ["OPEN_BOUND: interval end not observed"])
    latest = rev(2, gap_id, [])
    service = FindingReadService(Store([first, latest]), dispatch)

    body = service.finding(T, S, uuid4(), first["id"])
    r = body["revision"]
    assert dispatch.read == [str(setting_id)]
    assert [p["kind"] for p in r["indeterminate_reasons"]] == [MODELLING]
    assert r["indeterminate_reasons"][0]["missing"] == [RUNTIME, TRANSITION]
    assert r["indeterminate_cause"]["kind"] == MODELLING
    assert "minimum operating time" in r["indeterminate_cause"]["sentence"]

    body = service.finding(T, S, uuid4())
    assert body["revision"]["indeterminate_cause"] == {
        "kind": RECORD_GAP, "sentence": "Some records it needs are missing or conflict over part of the period."}
    assert [p["kind"] for p in body["revision"]["indeterminate_reasons"]] == [RECORD_GAP]


def test_source_closed_reads_no_assessment_and_states_no_cause() -> None:
    gap_id = uuid4()
    dispatch = Dispatch({str(gap_id): [seg("INDETERMINATE", [_missing(PV_AVAILABLE, "MISSING")])]})
    only = rev(1, gap_id, [])
    body = FindingReadService(Store([only]), dispatch).finding(T, S, uuid4(), only["id"], source_open=False)
    assert dispatch.read == []
    assert body["revision"]["indeterminate_reasons"] == []
    assert body["revision"]["indeterminate_cause"] is None
