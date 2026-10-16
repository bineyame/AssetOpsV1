# S3-02a â€” Selected assessment capability and claim-limit reads

Status: done (merged to main 2026-10-16; non-UI; review ACCEPT after fix round 1); was in_review (built 2026-10-16 on `task/S3-02a-capability-read`; packet `.agent/S3-02a-review-packet.md`). USER_REVIEW_REQUIRED: false; non-UI, mergeable after independent review. Size M, two phases. Branch `task/S3-02a-capability-read` from merged main. Depends on reviewed/merged S3-01 selected assessment and accepted `I-sim-dispatch-cases`. Authority: `.agent/architect-W1-remaining-answers.md`; `.ai/DECISIONS.md` `D-2026-10-16-s302-capability`, `D-2026-10-09-pre-s3-evidence-readiness-health`; registry `I-capability-read`, `I-claim-limit-read`. This part does not promote `evidence-analysis:2#b`.

## Verified seams and read contract

Existing selected day/window status, basis, coverage, watermarks and limitations: `backend/assetops_backend/analytics/dispatch_read.py:123-166`; exact revision lineage `:178-202`; routes `backend/assetops_backend/performance_api.py:88-101`; S3 tests `backend/tests/test_s3_dispatch_read_postgres.py`, `test_s3_dispatch_assessment_postgres.py`. S2 explanation is separate in `frontend/src/sites/LedgerSiteEvidence.tsx:1115`. **New:** versioned `CapabilityReadiness` and claim-ceiling service/API for one authenticated mini-grid Site, half-open UTC day and exact selected S3 dispatch window/interval `assessment_revision_id`, using that assessment's accepted public `EvidenceQuery`/`AnalyticInputSet`. Do not select later readings or another revision.

Apply the same Performance cutover gate as `performance_api.py:51-61` before serving this new read: a closed gate returns typed `409 PERFORMANCE_CUTOVER_CLOSED`, never `UNASSESSED` or an empty success. Use the request-level `finding_api.Access`/`development_access` identity seam shown in `finding_index_api.py:28,44-50` for 401/403/404; `open_scope` alone does not provide request access control.

Echo tenant/Site, day/window, revision, run/model/cohort, knowledge cutoff, effective Foundation/binding IDs, accepted evidence IDs, source/analytic watermarks, `built_at` and `read_at`. Return per-required-role covered duration/quality, missing/conflicted spans, selection/rule basis and named limitations. Versioned claim-limit mapping bounds the selected dispatch classification to Candidate/Necessary/Indeterminate support; no physical capacity inferred from configured capability. Positive ceiling requires current exact S3 selection, complete relevant rule assessment and accepted public role evidence. Current assessment may still be `LIMITED` or `UNKNOWN` in portions. No assessment = `UNASSESSED`; pending/failed/dirty/changed selection = `PENDING`/`FAILED`/`STALE_PROJECTION` and no current positive claim. Prior exact revision may be read as historical only. Reject foreign Site/revision, revision outside selected window, unsupported rule version and absent accepted lineage; 401/403/404 identity boundary applies.

## Phases and proof

| Phase | Deliverable and focused checks |
| --- | --- |
| 1. Fixture and read | Check `I-sim-dispatch-cases` exact accepted IDs against this rule. **New** callable `backend/tests/s3_claim_limit_records.py::build` composes the reviewed public-ingestion fixture (or adds only missing cases via registered simulated gateway, Batch V2 and S3 assessment): full Candidate-capability interval, missing PV-available or PCS-discharge-capability interval, poor-quality/conflict interval, late revision withdrawing currentness. It returns a manifest of selected assessment and exact accepted IDs for S3-02b's walkthrough. **New** `backend/tests/test_s3_capability_read_postgres.py` covers duration/quality, IDs, rule basis and reload; no private simulator truth. |
| 2. Ceiling/review | **New** `backend/tests/test_s3_claim_limit_postgres.py`: Candidate/Necessary/Indeterminate bounds, missing role/quality/conflict/open-bound/cohort/configuration, pending/failed/stale/unassessed, closed Performance cutover gate (`409 PERFORMANCE_CUTOVER_CLOSED`), wrong Site/window/revision, unsupported rule and exact Evidence links. Audit new SQL writers against statement-level rule 8; run `python tools/writer_guard_probes.py`. No migration expected; main head `0018_finding_match_deferral`, S6-02a's unmerged `0019_verification_core` means any new migration re-chains at merge. Run registry checker, `tools/check-all.ps1`, then one final-revision full backend suite per `backend/TESTING.md:104,112-125` with private `*_test` DB: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --junitxml=.pytest-junit.xml`, keep-awake, 20-minute cap, zero skipped/failed. Fresh independent review permits merge. |

## Architect questions

1. **Recommendation:** return role coverage as exact interval spans plus duration, with one versioned rule identifier; do not aggregate away a missing or conflicted subspan.

## Plan fix round 1

Required the Performance cutover and request identity gates, added closed-gate proof, and named a callable public-ingestion fixture for the UI walkthrough.
