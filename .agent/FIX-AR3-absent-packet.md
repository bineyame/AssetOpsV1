# FIX-AR3-absent packet (D-ANY.10)

Branch `fix/AR-3-absent-compose` off main 49c0ca628. Not merged.

## Change
- `chain/dispatch_day_rows.py`: `DispatchDayRows` marks a day with no row at k (live or explicit) with `ABSENT_MARK`
  instead of rendering `absent_day`; logs and counts one `period_row_absent` per contiguous run (`record_absent_run`,
  new in `chain/period_read.py`; the reader's own absent log is skipped for this kind via `log_absent=False`).
  Module doc cites D-ANY.10 (overrides D-ANY.5 no-fallback for this kind only).
- `estate/coverage.py`: `dispatch_days` -> `_fill_absent_runs`: one `snapshot.dispatch_days` per run over that run's
  window at the same k; stored days are never composed; if compose returns no such day the `absent_day` stays
  (mark stripped). Kill switch path unchanged.

## Tests
- No-DB `backend/tests/test_ar3_dispatch_day_rows.py` (+ `test_any1_period_read.py`): 60 passed. New: absent day at
  explicit k returns the compose day exactly and logs/counts (1 run, 1 compose); two absent runs split by a stored day
  compose twice, the stored day is the row not compose; all-stored never composes; kill switch unchanged. Two existing
  assertions updated (provider returns marked days; one more compose in the pending/absent coverage test).
- Postgres `test_ar3_dispatch_day_rows_postgres.py` via `tools/run-host-tests.ps1`: 2 passed, 37.7 s. Case (b) now
  asserts k between the revision and the build reads the selection (equals compose), not ABSENT_REASON.
- Parity and check-all: see below.

## Parity (client4, `assetops_polish_client4_test`)
`period_read_parity.py --database-url <client4> --work e3c/var/polish_client4 --story .../story.json --seed 20261111
--random 16 --kinds dispatch.day`: **PASS, 59 cases, 0 mismatch, 0 unstable** (includes
`any.between_revisions.site_period_read`). The `any.claim_rows.before_build` case does NOT exist on main (it is AR-4's
parity file); the Postgres test case (b) is the proof on this branch (k between revision and row build reads the
selection); AR-4 must re-run its 61 cases after rebasing onto this fix.

## check-all (19 guards)
17 pass; 2 fail on environment: Missing-claim orphan scan and fixtures, `MODULE_NOT_FOUND` (no
`frontend/node_modules` in this worktree). Estate guard self-tests 16 passed (25 min under load).

## Note
One early edit used a python heredoc (lane rule says Write/Edit only); the change is in the commit, no side effects.
