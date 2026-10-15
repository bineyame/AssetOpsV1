# S4-06 review packet - equal-start future price succession

Task: `tasks/S4-06-price-succession.md` (size S, non-UI, USER_REVIEW_REQUIRED false). Registry `I-price-equal-start-succession`. Branch `task/S4-06-price-succession` from main `7c72c6b3`. Review range: `git diff 7c72c6b3..HEAD`.

## Outcome delivered

A server-authorized SYSTEM SUCCESSION whose `valid_from` equals the start of the sole open-ended current assignment now closes that assignment's recorded tenure and inserts only the new revision's `[valid_from, infinity)` row. No zero-length left remainder is written. Later-start SUCCESSION, INITIAL and CORRECTION are unchanged; `valid_from < recorded_at`, bounded and multiple overlap stay 409 with the existing codes. No writer, migration or guard change: the single writer (`postgres_assumption_store.publish`) already closes every planned row and inserts every planned row in one locked transaction, so only the planner changed.

## Files materially changed

- `backend/assetops_backend/financials/assumptions.py` (`plan_assignments`, SUCCESSION branch): `<` relaxed to `<=` for the sole open-ended overlap; equal start returns `Plan((only.id,), (own,))`.
- `backend/tests/test_s4_assumption_publication.py` (`TestPlan`): three pure planner tests (equal start, CORRECTION tail, equal-start negatives).
- `backend/tests/test_s4_assumptions_postgres.py` (`TestEqualStartSuccession`, 5 real-Postgres tests).

## Acceptance criteria status

1. Planner change only for equality; no zero-length row; other kinds unchanged; 409s kept; SYSTEM server-side - **met**. Existing planner/Postgres tests for later-start SUCCESSION, INITIAL, CORRECTION and SYSTEM refusal pass unchanged.
2. Real-Postgres proof - **met** (`test_succession_at_the_scheduled_start_replaces_it_and_keeps_history`): INITIAL future price, then SUCCESSION at exactly its start against the current prior. One current assignment; old row keeps `valid_from = start`, `valid_to NULL`, `recorded_to = succession.recorded_at = new.recorded_from` (boundary continuity on both axes); every row has `valid_from < valid_to` or open end; `snapshot` at `recorded_at - 1us` returns the original assignment ID and revision (value 1.40), at `recorded_at` and `+1 day` the replacement ID and revision (1.55); revision/assignment IDs and recorded bounds asserted against those cutoffs.
3. Retry/refusals - **met**. Identical retry returns the same revision, `replayed`, same `recorded_at`, counts unchanged; same key changed value -> 409 `IDEMPOTENCY_KEY_REUSED`; stale prior -> 409 `PRIOR_REVISION_MISMATCH`; two racing equal-start publishers on one prior -> exactly one wins, the other 409 `PRIOR_REVISION_MISMATCH`, counts (2, 2) (`test_two_equal_start_publishers_on_one_prior_admit_exactly_one`). Bounded prior and >1 overlap at an equal start -> 409 `SUCCESSION_OVERLAP_NOT_PERMITTED`, nothing written. Earlier-price consequence selection (`fuel_cost.select_window_price` over `snapshot`) for windows inside and touching (ending at) the new start: same state, revision, assignment ID and value 1.20 before and after; crossing window stays `PRICE_SPANS_WINDOW`; window after start selects the replacement now and the schedule at the pre-publication cutoff.
- Coordinator note carries - **met**: earlier-price scenario (`test_an_earlier_price_keeps_selecting_windows_that_do_not_cross_the_new_start`, non-vacuous: the earlier price is a separate revision); CORRECTION tail (`test_equal_start_replaces_a_correction_tail_on_an_older_revision`: tail cites v1 while head is v2; after equal-start SUCCESSION the timeline is v1/v2/v3 with 5 rows total, pre-publication cutoff still shows the tail ID).

## Checks run (code revision `16fd46e3`)

- Focused: `test_s4_assumptions_postgres.py` 23 passed; with `test_s4_consequence_recompute_postgres.py`, `test_s4_consequence_store_postgres.py`, `test_s4_consequence_read.py`, `test_s4_assumption_publication.py`: 62 passed; `test_s4_fuel_cost.py` + publication: 72 passed.
- Mutations (each reverted with `git checkout --`, tree clean after):
  - M1 `<=` back to `<`: 6 failed (4 Postgres equal-start + 2 planner).
  - M2 equality branch disabled (left remainder `[t, t)` written): same 6 failed (DB `valid_range` refusal / planner shape).
  - M3 store prior check disabled: 2 failed (stale-prior and race tests).
- `tools/check-all.ps1`: All 9 guards passed (exit 0).
- Full suite: **NOT COMPLETED - stopped at the 20-minute cap.** Command `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=10 -p no:cacheprovider --junitxml=...` (PowerShell, keep-awake on, private base `assetops_s406_test`), revision `16fd46e3`, started after confirming no other full suite was running. At 20 min it had reached 53% with no failure or error marks; normal wall time is ~8 min. During the run sibling worktrees were running Postgres pytest (S4-05 `test_s405_publication_po...`) on the same Docker Postgres, the likely cause of the slowdown. Run killed, run-owned DBs dropped; no JUnit counts exist. Same-revision full-suite evidence is therefore still owed: rerun on `16fd46e3` (later commits are docs-only) when the machine is quiet.

## Known deviations

None. No migration was needed; rule-8 ownership (`tools/checks/configuration-persistence.ps1`) untouched.

## Residual risk

- No completed full backend suite on this revision (see Checks run); the change is confined to one planner branch whose callers are the assumption writer and its tests, all run green in the focused set.

- Equal-start tests use `now + 30 days` as the future start, so they depend on the server clock being near the test clock (same as the existing fixture's future-start assertion).
- The concurrency proof relies on the existing advisory lock + prior check; M3 shows the prior check is load-bearing for the equal-start race.

## User-review focus

None (USER_REVIEW_REQUIRED false). Reviewer: the SUCCESSION branch of `plan_assignments` and `TestEqualStartSuccession`.
