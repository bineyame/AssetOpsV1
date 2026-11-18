# Review packet R-1 (branch task/R-1-demo-fixes, from main afb0b9ccb)

Spec: `.agent/architect-combined-pass-2026-11-08.md` A.1, A.2, A.5. Product backend untouched.

## Files changed
- Frontend: `estate/EstatePortfolio.tsx`, `estate/__tests__/estatePortfolio.test.tsx`, `sites/MiniPerformance.tsx`, `sites/__tests__/miniServiceRoutes.test.tsx`.
- Backend tests: `test_ch1a_grading.py`, `test_out_b1_board.py`, `test_demo_a0_assumption_clock_seam.py`, `test_w502_domain_intent_api.py`, `test_s4_schedule_health_postgres.py`.
- `w301-estate-golden.json`: NOT changed (see Stop).

## Item evidence
- A1-a (fuel row bold thread label): R3p case edited (three assertions), new no-thread fallback case added. vitest `src/estate/__tests__` (4 files) + miniService*/miniPerformance*: 6 files, 134 tests passed.
- A1-b (`barLabel`, exported, used at the chart label): new `barLabel` describe, R309 unchanged and green (same 134-test run). Height check (Coverage visible, scrollHeight <= clientHeight at 1440) not run: belongs to the capture retake.
- T1 to T5: `test_ch1a_grading`, `test_out_b1_board`, `test_demo_a0_assumption_clock_seam`, `test_w502_domain_intent_api` with no DB URL: 56 passed, 8 skipped, 0 failed, 0 collection errors (w502 now collects and skips).
- T7: `test_s4_schedule_health_postgres.py` on `assetops_r1_test` (created for this run): 11 passed in 694 s, including the DB-time asserts. The file itself cannot be collected without a DB URL (pre-existing: `test_s4_schedule_tick_postgres` imports `StageRunner` under `if URL`), so it was not part of the no-URL run.

## Stop: T6 (w301 golden)
- Rewrite with `ASSETOPS_WRITE_W301_GOLDEN=1` on `assetops_r1_test` produced a diff of 99 insertions, 0 deletions, all `summary.claims["count.opportunities"]` entries (diff gate satisfied).
- But the verify run (flag off) FAILS: 4 failed, 2 passed (`public_replay[cold|ev|mixed]`, `golden_clock_plus_30_days[mixed]`). Causes are not claim diffs: `test_w203_cold_replay_postgres.py:80` `worker.run_pending(...)` returns `[]` (assert outcomes), and one case shows a Lab run `status FAILED` where COMPLETED expected. The same failures occurred before and after copying `var/` from the main checkout. This looks like an environmental or product problem (possibly the stale mechanism template, T8, or a date-dependent replay), not a stale manifest.
- Manifest reverted to HEAD (not committed), because a golden written from a failing replay is unsafe. Needs Architect/coordinator ruling.

## Residual
- Packet checks not run: `tools/check-all.ps1` (after merge per spec), layout evidence.
- Test DB `assetops_r1_test` left in the dev Postgres container (plus run-owned `assetops_r1_pt*` DBs).
