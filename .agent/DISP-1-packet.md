# DISP-1 packet (lane C) - branch fix/DISP-1-money-eligibility, off main 4fb0ccc11

Spec: D-ANY.11 in `.agent/build-sheet-OWN-GAPS-2026-11-08.md`.

## Built (steps 1-3, no DB)
- `financials/money_eligibility.py` `for_finding_on(..., known_at, *, select_days=None)`: when set, bracket days come from
  `select_days(from_, to)` (UTC day start / end+1d); `self.days is None` fail-closed applies only when `select_days` is None;
  any bracket day missing from the returned list -> `unavailable(fid, "HISTORICAL_DAY_UNAVAILABLE: DAY ...")` (no KeyError).
  `select_days=None` path is the original call and `selected[d]` lookup unchanged. `for_finding` untouched; no `estate` import.
- `estate/adapters/postgres_estate_read.py` `eligibility` passes `select_days=lambda f, to: coverage.dispatch_days(self, t, s, f, to, k)`
  (local import).
- Tests: `backend/tests/test_disp1_money_eligibility_select_days.py` (4): never calls `select_dispatch_days_on`; stored days == compose
  for ELIGIBLE and PENDING (unavailable day); works with no days store; short list fails closed.

## Checks run
- New + `test_lr01_money_eligibility.py`: 10 passed. Adjacent estate/coverage no-DB files (4): 154 passed.
- check-architecture: see report.

## Resume points (after AR-4 merges to main; not run)
4. `git merge main` into this branch. client4 parity `--kinds evidence.claim,dispatch.day`: 0 mismatches over the 61 cases. List which
   existing cases cover: ELIGIBLE with current amount, PENDING_REASSESSMENT, Finding bracket outside the request range, `before_build` k;
   add any that are missing.
5. Timings cold, store off, rows on, with profiles, week / 22 / 31 days, before (`786d2293a` + main) and after. Profile must show zero
   `select_dispatch_days_on` under `for_finding_on` on a fully built range. Report saving as measured. Check memory first (>=1.5 GB free),
   one DB job at a time, client4 not client7.
6. Open: the D-ANY.6 kill-switch fallback (`coverage.dispatch_days` falls back to `self.dispatch_days`) is covered only by existing coverage tests.

## Session 2026-11-12 (steps 4-5; main 118866a17 merged; client4, read-only)
- No-DB after merge: 92 passed, 6 skipped (Postgres files, not run): disp1, lr01, estate_coverage_local_days, w301_estate_coverage, ar2/ar3/ar4/ar6 files.
- **Parity** `--kinds evidence.claim,dispatch.day --seed 20261111 --random 16`, e3c polish_client4 work/story, prebuilt routes, 1382 s: **PASS (61 cases, 0 mismatch, 0 unstable)**, exit 0.
- Coverage of Finding money cases (by case type; bodies not inspected for ELIGIBLE/PENDING strings): Portfolio cases with `lens=all` (story + any.portfolio.* at 4-31 days, aligned/unaligned) run `for_finding_on` per Finding; `any.claim_rows.before_build` / `after_build` give historical k before/after the first and last row; `any.portfolio.4/8/12` are historical known_at; bracket days outside the request range arise on unaligned windows (any.portfolio.2/7/9/11/13). GAP: no case is asserted to contain an ELIGIBLE-with-amount or PENDING finding, or a bracket day outside the stored range; the harness does not label them.
- **Timings** (cold, store off, rows `evidence.claim,dispatch.day` on, wall under cProfile, one run): week 8.6 s (AR-4: 8.7), 22 d 17.4 s (22.2), 31 d 21.2 s (27.1). Saving 0.1 / 4.8 / 5.9 s (~+-15% noise on the week).
- Profile: `print_callers("select_dispatch_days_on")` returns no callers in all three runs (was 4 / 12 / 16 calls from `for_finding_on`) -> zero under `for_finding_on`. `_data_gaps` 0.15 / 0.13 / 0.15 s.
- Probe: scratchpad `prof_win.py`, not committed. Open: item 6 (kill-switch fallback) unchanged.
