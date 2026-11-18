# FIX-W301 review packet

Task: tasks/FIX-W301-estate-index-tests.md. Branch task/FIX-W301-estate-index-tests, from main 15eed62c8.

## Diagnosis
- `test_historical_minigrid_outstanding_marker_page_two_keeps_basis`: cause is a fixed date vs the real clock.
  `LATE["decided"]` (test_w301_estate_index_postgres.py:757, added 2026-10-20 in 6cf1cb023) was `2026-10-31T08:00:00Z`.
  It was in the future when written; on 2026-10-31 after 08:00 UTC it is behind the database clock, so the recompute
  job the step leaves PENDING is stamped after the test's cutoff and page one returns no `next_cursor`
  (INVALID_CURSOR at :897). Same class as the 2026-10-30 fix 70b00b738. Product code is correct.
  Proof: moving the date to 2026-11-02 made the test pass.
- `test_cold_revision_waits_for_its_selected_assessment`: NOT reproduced. It passed alone 4 times on this worktree
  and once on unmodified main code (worktree at 15eed62c8), and 2 times inside full-file runs. It does not use
  `LATE` or a fixed date after 2026-10-06. The reported KeyError at :952 (`seen[finding]`) is unexplained; the
  likeliest cause is contention with the concurrent demo-data Postgres lane (timing of the sub-second
  `selected_at` re-date), but that is unproven. Left unchanged; recheck if it recurs.

## Change
`LATE["decided"]` is now computed as the real clock plus one day, truncated to the hour (always ahead of the DB clock).
Comment explains why. Only file changed: backend/tests/test_w301_estate_index_postgres.py.

## Checks
- Whole file alone, run twice: 20 passed (402s) and 20 passed (410s), plan2 venv, assetops_test DB.
- Targeted failing test alone: passed.
- tools\check-all.ps1: see below.
