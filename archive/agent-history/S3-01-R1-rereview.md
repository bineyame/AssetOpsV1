# S3-01 R1 fix re-review

Reviewer: fresh Claude reviewer (not the author). Target: commit 868ba66 on task/S3-01-dispatch-assessment.

**Verdict: accept. R1 is resolved.** No block findings. Two carries.

## Verified
- `_LIVE_JOBS` (postgres_assessment_store.py:86-92): PENDING/LEASED always count. FAILED counts unless a selection row exists with same tenant, site and `analytic_id = :a`, `selected_at > available_at`, and window overlap. Selections are written only for `out.selection == "DEFAULT"` (`_select`, line 343-347), so non-default runs cannot supersede. A selection for another analytic or non-overlapping window does not.
- The predicate is used in both `window_snapshot` and `selected_intervals`; `:a` is bound in both (selected_intervals via the shared params `p`, the second query explicitly with `analytic_id`).
- FAILED rows are not deleted or mutated; history stays (test asserts FAILED still in `jobs()`).
- `fail_job`: final failure stores `now` in `available_at`; retry path unchanged (`now + backoff*attempts`). A FAILED job is never leased again (claim filters PENDING/LEASED), so reusing `available_at` is safe.
- Old failed jobs have `available_at` = failure + backoff offset: they recover only on a selection later than that offset. This is conservative (stays FAILED slightly longer), never wrongly cleared. Matches the packet's Known note.
- Comparison no longer sees the superseded job: it consumes `selected_intervals` `window_jobs`, which the test asserts has no FAILED after recovery.
- Nothing else moved (3 files: store, test, packet).

## Checks run
- Isolated DB `assetops_r1rr_test` on the local compose Postgres (dropped afterwards): `test_s3_dispatch_read_postgres.py`, `test_s3_performance_cutover.py`, `test_s3_dispatch_assessment_postgres.py`: 37 passed. This includes both new tests. I did not re-run the fail-before (stash) check or the full backend suite, check-all, or the frontend suite; those are the implementer's claims, unverified by me.

## Findings
- C1 (CARRY) No direct test that `compare` / the performance comparison stops classifying recovered intervals STALE_PROJECTION. Coverage is indirect (the `window_jobs` input has no FAILED entry). The original review asked for a comparison recovery test; add one when convenient (e.g. in test_s3_performance_cutover.py after a recovery).
- C2 (CARRY, low) Supersession is overlap-based, not full coverage: a selection overlapping only part of a failed job's window clears it. With daily windows this is likely moot; note it if window sizes ever differ.

R2-R5 untouched, still carried.
