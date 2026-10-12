# S3-01 phase 3b handoff (PARTIAL: 3b1 and most of 3b2 built and committed; closeout remains)

Branch `task/S3-01-dispatch-assessment`. Status stays `active` until closeout. Commits start at `b04b904`.

## What landed

- **Cutover summary, R2, R3 and R1-C1** (`b04b904`):
  - `analytics/performance_comparison.py` adds `comparison_summary` (outcome, statement, counts, model version, per-claim missing IDs, delta rule, rule change, interval limitations, compared IDs) and `classified_revision_ids`.
  - **R2.** `permits_performance_cutover(..., selected_revision_ids=)` refuses when a classified MATCH or INTENTIONAL_DELTA revision is no longer selected, or when the selection cannot be read. An empty-set report needs no recheck.
  - **Wiring.** `main.py` `performance_gate` and the `performance_migration` CLI pass the live `selected_intervals`. `main.py` also provides `performance_report`.
  - **R3.** In `performance_api.py`, the cutover route returns `comparison`. File-store errors (`EvidenceStoreUnavailable` and the file `analytics.ports.AssessmentStoreUnavailable`) give a 503. The cutover route's 503 carries a closed body: `read: CLOSED`, `permitted: false`, `unavailable.code` set to `COMPARISON_STORE_UNAVAILABLE` or `ASSESSMENT_STORE_UNAVAILABLE`.
  - **Tests.** `tests/test_s3_performance_cutover.py` covers R2, R3 and the summary (27 pass). `tests/test_s3_dispatch_read_postgres.py::test_comparison_classifies_a_recovered_interval_after_a_superseded_failed_job_r1_c1` reads UNPROVEN STALE_PROJECTION before recovery and MATCH after (9 pass on isolated DB `assetops_s3p3b_test`; drop it at the end).
- **Walkthrough tool** (`tools/s3_dispatch_walkthrough.py`):
  - `prepare` copies `assetops_s3cases` into `assetops_s3walk` (TEMPLATE), builds a private git-archive tree with its own `var/`, runs the comparison (PASSED, empty set) and stages FAILED 10-07 and PENDING 10-05.
  - `serve` runs the API on port 8820. `recover` runs the real worker over the staged days.
  - It uses the producer's work-dir manifest. Finding: the committed `.agent/S3-01-dispatch-cases-v1.manifest.json` is from an earlier producer run and matches no evidence ID in `assetops_s3cases`.
- **UI:**
  - `frontend/src/sites/performanceDispatchClient.ts` (cutover, window and revision reads; the 503 cutover body is kept).
  - `dispatchWords.ts` (plain words).
  - `PerformanceDispatch.tsx`: Overview with status line, totals, periods and 15-minute blocks, selected period/block, limitations, coverage, comparison line and records drill-down. Also the Analysis view with constraints, confidence/coverage/unavailable, the gated fuel/money/Finding panel, the stored record, history and the full comparison.
  - `SitePerformance.tsx` renders it when the legacy declaration is AWAITING_EVIDENCE_MIGRATION.
  - CSS is at the end of `ui/primitives.css`.
  - Address state: `?day=&revision=&block=&view=`.
- **Tests:** `frontend/src/sites/__tests__/performanceDispatch.test.tsx` has 12 passing tests. They cover the closed and 503 gate, the plain limitations, the empty-set "not a match", every status, block selection plus address plus records, the pinned older-rule note, the missing revision, demo notes kept apart from provenance, and the Analysis unavailable portions. `tsc` is clean.
- **V-01, layout and interaction evidence:** `tools/s3-dispatch-evidence.mjs`, with output in `.agent/S3-01-phase-3b-dispatch-evidence.txt`. 32/32 claims pass at desktop 1440 and narrow 390:
  - mock panels;
  - 10-02, 10-09 and 10-01 populated, with no sideways scroll;
  - keyboard Enter selects a block, and reload keeps the revision, block and records;
  - STALE, FAILED and UNASSESSED;
  - a pinned revision on another day;
  - the Analysis portions.

  Screenshots are in `.agent/S3-01-phase-3b-shots/`. A narrow-overflow defect was found by the measurement and fixed: a `minmax(0, 1fr)` grid column.
- **Owner walkthrough:** `.agent/S3-01-owner-walkthrough.md`.

## Resume here (closeout)

1. Commit anything uncommitted (`git status`; force-add `.agent`). Do not commit `.agent/coordinator-handoff.md`.
2. Run the full suites once, with output trimmed:
   - backend with Postgres: `ASSETOPS_TEST_DATABASE_URL=.../assetops_s3p3b_test`, `.venv/Scripts/python -m pytest backend/tests -q`;
   - host;
   - gateway;
   - simulator, from `simulator/`;
   - frontend `npx vitest run`, `npx tsc --noEmit -p .`, `npm run build`;
   - `tools/check-all.ps1`.
3. Write the review packet `.agent/S3-01-review-packet.md` covering phases 1, 2, 3a, dispatch-3.1 and 3b. Cite the earlier packets; do not restate them. Include:
   - the V-01 table: mock `dispatch:1-3` versus the app, with supported portions and deliberate omissions (single-hour EAT window, fuel notice, Finding link, chart of power readings);
   - `analysis:1,3` supported portions, with `:2` fuel gated;
   - known deviations (below).
4. Add a CODE_STATE entry "S3-01 phase 3b" (under 40 lines). Point ACTIVE_CONTEXT at review. Set the task `Status: in_review` with USER_REVIEW_REQUIRED true.
5. Write `.agent/S3-01-questions-5.md` with fail-closed defaults:
   - (a) the default day when `?day=` is absent (today UTC, which usually reads UNASSESSED; a list-of-assessed-days route is not built);
   - (b) whether to refresh the committed fixture manifest;
   - (c) whether the walkthrough should stage an older-rule result (not done, because labelling a 3.1 run "dispatch-3" would be dishonest).
6. Drop `assetops_s3p3b_test`. Keep `assetops_s3walk` for the owner walkthrough (it is recreated by `prepare`).

## Known deviations and risks

- No dispatch-3 run exists in the rebuilt fixture data. The older-rule label and the late-evidence revision history are proven by tests only, not in the walkthrough.
- Demo annotations do not surface on the walkthrough data: the fault-fixture days are AMBIGUOUS and carry no run evidence. This is proven by test.
- The staged FAILED and STALE days have no interval, so the "prior result kept" is the window assessment only.
- `classified_revision_ids` rechecks are skipped for empty-set reports by design.
- The evidence table lists at most 60 rows per scope.
