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
