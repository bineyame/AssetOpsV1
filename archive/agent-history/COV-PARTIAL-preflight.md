# COV-PARTIAL pre-flight (one batch)

Worktree `AssetOpsV1-covp`, branch `task/COV-PARTIAL-estate-coverage` at `0796218fc`, clean. No code written yet.

## Confirmed
- `dispatch_days` returns one entry per UTC day intersecting `[from, to)`
  (`analytics/adapters/postgres_assessment_store.py:934-940`), and every estate root refuses windows that are not
  midnight-aligned (`estate/scope.py:108-110`). So `requested == len(days)` on every real read. C5 only matters for fakes.
- Rules followed: never `-ExecutionPolicy`; no BOM; test DBs `assetops_covp_<x>_test` only.
- `frontend/node_modules` is missing. Plan: an absolute junction to plan2's copy.

## Literals asserting a live mini-grid gap period UNKNOWN (would flip to PARTIAL)
1. Golden `backend/tests/fixtures/w3/w301-estate-golden.json:3068`: KOBO-001 `state` "UNKNOWN" in case
   "findings-mixed-week" (live, 10-06..10-12, match COMPLETE, job SETTLED). Becomes PARTIAL.
2. Same golden `:2991`: KOBO-001 `coverage_state` "UNKNOWN" in case "scope-mixed" (same window). Becomes PARTIAL.
3. `backend/tests/test_w301_estate_index_postgres.py:561`: `gap["coverage"]["sites"][0]["state"] == "UNKNOWN"`
   across the four lenses (PowerSite, 10-06..10-09 live, 10-07 unassessed). Becomes PARTIAL. `total_count is None`
   still holds.
- These stay UNKNOWN: `test_w301_estate_api.py:226`, a fake that returns 2 days for a 1-day span (C5 mismatch);
  single-day and all-gap cases; historical cases; and stubbed `site_coverage` tests.
- `test_w301_estate_coverage.py` has only cold tests, so no literals change there.

## Questions
Q1. The sheet says the golden diff may only add `days`. Items 1 and 2 contradict that, because the rule itself flips
    KOBO-001 to PARTIAL. May the regeneration also carry those two state changes, plus the PARTIAL `days.text` and the
    non-null fields that follow (rows from checked days, if any)? Or do I stop?
Q2. May I update `test_w301_estate_index_postgres.py:561` to PARTIAL? The sheet only allows edits to
    `test_w301_estate_coverage.py` literals.
Q3. For C5: if `len(days) != requested`, I fall back to today's rule, which gives UNKNOWN when there is a gap and
    unchanged otherwise. A gap-free case would then never turn UNKNOWN through C5. OK?
Q4. `tools/demo_combined_finish.py` (CO-6) exists only on `task/DEMO-A-combined-dataset`. Under §6 I leave CO-6 to
    DEMO-A if it merges after this slice, and I don't touch it here. Confirm.
Q5. U3 captures at 390 and 1440 need a running backend and frontend on a multi-day window with a gap. Is there an
    existing producer with a `_test` DB to use? If not, I propose seeding the U4 scenario into
    `assetops_covp_capture_test` with a small script, serving the backend and dev server on it, and capturing. That
    needs a browser, so I need your go. Otherwise I record "layout evidence: not run".
