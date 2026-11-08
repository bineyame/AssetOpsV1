# Re-review G2 (fix round R3.8), head a944415fd

Verdict: ACCEPT. M1 closed. No new findings.

## Diff since e2400a0d1
Only the build-sheet copy, packet fix-round section, model.py, postgres_fuel_balance_store.py, scheduled.py and three test files. Matches R3.8 line for line.

## M1 closure
- Step 4b in scheduled.py (due_nights): skips nights >= first_base, not ready, or with window start < known_at - RECORD_LOOKBACK; otherwise due if any stored (root, head) pair has a different or absent current head.
- Uses existing reads only (schedule_inputs keeps `fuel` heads and `stored` record_ids). `records` stays a 2-tuple. ScheduleInputs gains two trailing defaulted fields. No migration, no new query.
- Spin check: window records are read over [start, end] (service.py:90), so with window start >= read start every stored record occurs inside the record read; an unchanged record is always in record_heads with the same head. After re-assessment the stored pairs equal current heads, so the night stops being due. Proved live: P5b "again None", revision stays 3.
- Skip check: a corrected, moved or kind-changed record changes head or leaves the read, so the night is due. Not-ready nights untouched, as step 4.

## D-R3.10 (L3)
run_site records CLOCK_BACKWARDS as REFUSED per night, continues, raises one FuelBalanceRefused after the loop (CLOCK_BACKWARDS, lists nights). Other refusals still raise at once; ASSETS_UNSUPPORTED unchanged. Tests: clock-backwards replacement and test_any_other_refusal_still_fails_at_once assert call order and codes.

## Runs
- No-DB set (3 G2 files, ch0 tick timing, ch1b drain, cold_drain_stage, w402/w403 stage, finish rows, k3, k4a rules): 205 passed, 3 skipped (Postgres-gated) in 7.5 s.
- Postgres, test_own_g2_fuel_night_tick_postgres.py, one process, file order, -s, no -k/-n, DB g2_rereview_test (created by me): 6 passed in 1033 s. P5b: N9 rev 3 APPENDED, state WITHIN_MARGIN, limitations [], not due next tick.
- test_5b, test_p5b (last in file) exist and assert the R3.8 claims.

## Notes (Low, no action)
- Boundary: night start exactly equal to read start is compared (strict `<`); consistent with an inclusive read lower bound, no spin observed.
- Not rerun: architecture/workflow guards, tsc (backend-only change).
