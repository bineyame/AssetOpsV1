# S3-01 phase 3a handoff (PARTIAL: built and committed; closeout, proofs and full suites remain)

Branch `task/S3-01-dispatch-assessment`. Commits: `aaa47ae`, `79161dc`, `6314b64`, `d47c03d` (fixture subagent), `6f23429`. Status stays `active`. Open questions: `.agent/S3-01-questions-3.md` (Q9-Q12, fail-closed defaults built).

## What landed

- **F3**: `analytics/cohort.py` `_multi_epoch`. With two or more epochs of one source in a window, the default cohort is AMBIGUOUS. This holds whether or not the epochs overlap. Covered by tests `test_full_role_fixture_epoch_beside_ordinary_epoch_is_never_positive_by_default` (the reviewer's repro) and `test_sequential_epochs_are_not_blended_by_default_but_explicitly_selectable` in `test_s3_dispatch_v3_analytic.py`. The table row "Successive epochs" was amended (Q9).
- **F6**: in `postgres_assessment_store.lease_job(..., max_attempts)`, an expired lease on its last attempt becomes FAILED with the error "lease expired on attempt N of M". The worker passes `max_attempts`. Test: `test_a_lease_that_always_expires_reaches_failed`.
- **F4**: `DispatchAssessmentWorker.run_pending(reconcile=True)` calls `reconcile_all()`, which reconciles each Site found in `store.assessed_sites`. The read also reports CONFIGURATION_CHANGED or MODEL_VERSION_CHANGED as `STALE_PROJECTION`.
- **Selection log**: migration `0008_assessment_selection` adds `analytic_run_selection`, append-only, with commit order in `seq`. It is written by `_persist._select` for each DEFAULT run, created or reused. `run_heads` now reads it, so it no longer depends on `completed_at`. Guard rule 8 was extended for this table. The head-revision asserts in the two S1/S2 test files were bumped.
- **Read service** (`analytics/dispatch_read.py`):
  - `derive_status` returns one of UNASSESSED, PENDING, CURRENT, STALE_PROJECTION or FAILED, plus reasons.
  - `DispatchReadService.window`, `.run` and `.revision` are the read entry points. Each reading carries its as-accepted revisions and a `selection_note` naming any backdated correction (Q1). They also carry `CUTOFF_LABEL` (Q6), the `UNAVAILABLE` typed gaps (Q2), and `superseded_keys` (Q8).
  - Consistency comes from `store.window_snapshot`, a single REPEATABLE READ transaction. The current basis uses `OPEN_CUTOFF` together with `assessment_worker.input_basis`.
- **Demo annotation**: `analytics/adapters/demo_manifest_file.py` reads env `ASSETOPS_DEMO_FIXTURE_MANIFEST`. It matches fault-fixture cases by exact evidence IDs and sits apart from central provenance.
- **API**: `backend/assetops_backend/performance_api.py` is mounted in `main.py` after the analytics router. Routes:
  - `GET /api/sites/{site_code}/performance/dispatch/cutover`: always served.
  - `.../windows/{YYYY-MM-DD}`, `.../runs/{run_id}` and `.../revisions/{revision_id}`: return 409 `PERFORMANCE_CUTOVER_CLOSED` until the gate opens. They return 404 for an unknown Site, run or revision, or a foreign tenant, and 503 when the store is unavailable.
- **Comparison and gate**: `analytics/performance_comparison.py` provides `compare` and `permits_performance_cutover`. The CLI is `python -m assetops_backend.performance_migration run --tenant demo --site KOBO-001`. Reports go to `<EVIDENCE_STORE_ROOT>/migration-performance/<site>/` (`evidence/composition.build_performance_comparison_reports`).
- **F5 and fixture determinism**: see commit `d47c03d` from the fixture subagent. It adds the new scenario `kobo-s3-dispatch-necessary-run` v1 on 2026-10-09, and the SOC template is now chosen by minimum `(source_time, sequence)`. The subagent's report covers the established cause of the SOC difference and its producer run; if that report is missing here, take these from its commit message and from `.agent/S3-01-dispatch-cases-run.txt`.

## Checks so far

- `tools/check-all.ps1`: all 6 guards passed (at `6314b64`).
- Analytic: 18 passed.
- S3 Postgres (`test_s3_dispatch_read_postgres.py` + `test_s3_dispatch_assessment_postgres.py`) on isolated DB `assetops_s3p3a_test` at 127.0.0.1:55432: 13 passed. Drop that DB when finished.

## Resume here (3a remainder)

1. Write pure tests for `performance_comparison`: each of MATCH, INTENTIONAL_DELTA, MISSING_SOURCE and UNPROVEN, the empty set, and every refusal reason in `permits_performance_cutover`. Add a TestClient test of `performance_api`: 404 for an unknown Site, 409 while closed, 200 once a PASSED report and clean lineage exist. Write to a temp `EVIDENCE_STORE_ROOT`.
2. Prove three guards non-vacuous:
   - Remove the `_multi_epoch` branch in `cohort.py`; the F3 test must fail.
   - Drop the `UPDATE ... 'FAILED'` in `lease_job`; the F6 test must fail.
   - Delete `analytic_run_selection` from guard rule 8's list; check-all must fail.

   Revert each with `git checkout --`.
3. Run the full suites, then the producer and its verify:
   - backend with Postgres on an isolated DB;
   - host and gateway;
   - simulator, from `simulator/`;
   - `tools/check-all.ps1`;
   - producer `run` then `verify`, if it has not run since `6f23429`. The fixture subagent's run predates `6f23429` but includes the cohort change from `aaa47ae`.

   Then run `performance_migration run` against the s3cases DB to prove the gate goes from closed to permitted.
4. Write the phase-3a review packet `.agent/S3-01-phase-3a-review-packet.md` and a CODE_STATE entry "S3-01 phase 3a". Update ACTIVE_CONTEXT and the task Status note (keep `active`).

## Anchors for 3b (UI)

- Client: add calls in `frontend/src/sites/siteAnalyticsClient.ts` for the four routes above. Response shape: see `DispatchReadService.window` and `revision` in `analytics/dispatch_read.py`.
- `SitePerformance.tsx` `DispatchView` (about :173) currently calls the file-backed `/dispatch`, which answers 409 for imported Sites (the `AwaitingEvidenceMigration` path at about :208). For imported Sites, switch it to `/performance/dispatch/cutover` and then `windows/{day}`. Show:
  - every status and reason;
  - the stale prior selection;
  - the `UNAVAILABLE` gaps;
  - `demo_annotations`, kept visibly separate from provenance;
  - interval revisions;
  - revision drill-down with `as_accepted` versus the selected configuration.
- The Necessary, Candidate and Indeterminate reviewer path is in fixture days 10-09, 10-02 and 10-03 or 10-01 respectively.

## Open risks

- `INTENTIONAL_DELTA` heuristic (Q11).
- A large window read evaluates the full input basis on every request (about 3k rows per day; acceptable for the demo).
- `run_pending` reconciles every assessed Site on each pass, at a cost of O(windows) configuration reads.

## Fixture producer result (commit `93cc3ef`)

- The producer was rerun with the cohort change. It reports `VERIFY PASSED`, and every case is `check met`.
- The new case `necessary-interval` is on 2026-10-09 and uses epoch `s3-cases-epoch-2`. Its window is `LIMITED` and its interval is `NECESSARY`; see `.agent/S3-01-dispatch-cases-run.txt` lines 112-178.
- The run predates the read-test commit `6f23429`, which changed tests only, so it does not need a rerun for that.
- I handed off before the subagent's written report arrived. Read the SOC-difference cause from the commit messages of `d47c03d` and `93cc3ef`. If they do not establish it, it is still open.
- The scenario is registered in the backend guards (`test_scenario_fingerprints.py` pin `ad889dbe…5f14`, `NEVER_SHIPPED_AS_V1`, count 12): 49 passed.
- Subagent findings:
  - **SOC cause:** established as batch walk order only. The batch ID digests the per-run gateway ID, and the simulator is deterministic (69.1875, 30 and 58.5 all lie on one prolonged-day-02 trajectory).
  - **Contradiction values:** now `['40', '47.5']`.
- Unconfirmed: the necessary-interval window reads `LIMITED` with an empty limitations list. Check `dispatch_v3` window claim logic, likely the open upper bound. A `LIMITED` claim with no named limitation may be a defect to fix in 3a.
