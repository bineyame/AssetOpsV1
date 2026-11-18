# FIX-AR3-absent review (D-ANY.10)

Reviewer: fresh Claude (read-only). Branch `fix/AR-3-absent-compose`, commits eb2ff7d17 + 58c5d8aff, diff vs main 49c0ca628.

## Verdict: ACCEPT (Low findings only, none blocking)

## Checked
- Same k, byte-equal: `coverage._fill_absent_runs` (estate/coverage.py:84-99) calls `snapshot.dispatch_days(t, s, run[0].window_start, run[-1].window_end, k)` with the caller's k. `select_dispatch_days_on` (postgres_assessment_store.py:1019-1052) composes each UTC day independently of the query window (per-day `EvidenceQuery`/`_dispatch_day_on`), so a run-window compose equals a full-range compose for that day. Postgres case (b) asserts `_same(absent, composed)` (claimed 2 pass; not rerun, no-DB lane).
- Run boundaries: all-missing (one run, one compose), single-day first run [D1], multi-day last run [D3,D4], stored day between runs never composed (compose double holds a different D2 that must not surface). Contiguity rule is identical in the provider log loop (dispatch_day_rows.py:192-198) and the splice, so logs and composes agree 1:1.
- No double compose; all-stored range composes 0 times; kill switch path unchanged (coverage.py:70-75, test asserts one plain compose, unmarked).
- PENDING: stored-day PENDING -> synthetic `PENDING_JOB` path unchanged (dispatch_day_rows.py:191, test line ~164 still asserts it; `test_coverage_pending_and_absent_rows` still asserts PENDING_RECOMPUTE/PENDING). Absent+pending now takes compose's own job state, as D-ANY.10 states.
- Changed assertions justified: provider now returns marked days (ruled shape); `compose_calls` 0->1 is the D3 absent run now composed, and `absent == oracle` is kept. Postgres (b) reverses ABSENT_REASON to "reads the selection" - that is the ruling itself, and it is stronger (non-vacuous `any(selection)` + equality).
- Logging: one `period_row_absent` + one count per run (`record_absent_run`, period_read.py:330); reader's per-day log suppressed for this kind via `log_absent=False`. Not per-day spam.
- Connection: prod compose uses the snapshot's own connection (postgres_estate_read.py:163-164), no new connection; test double uses `with engine.connect()`. No leak.
- Mark constant duplicated (`_absent_row` in coverage.py:78 vs ABSENT_MARK) but guarded: test asserts no ABSENT_MARK survives coverage.

## Findings
- Low - backend/tests/test_ar3_dispatch_day_rows.py: no coverage-level test of a stored PENDING day next to an absent run (mixed case). Code paths are independent so risk is small; add one assertion when convenient.
- Low - backend/assetops_backend/chain/period_read.py:330: `absent_count()` now mixes units (per absent day on other kinds, per run on dispatch.day) feeding `perf_budget.py:224`. Ruled "counted per run"; note it where the perf number is read.
- Low - chain/dispatch_day_rows.py:114 `absent_day` docstring still reads as the D-ANY.5 render rule; it is now only the compose-returned-nothing fallback.
- Low - .agent/fix-ar3-parity.json records no commit/revision; packet ties it to the branch only. Process: packet admits one python-heredoc edit against lane rules (no product impact).

## Checks run by reviewer
- No-DB: test_ar3_dispatch_day_rows.py + test_any1_period_read.py + test_ar3_dispatch_day_rows_postgres.py -> 60 passed, 2 skipped (Postgres, no URL), 1.9 s. tools/checks/test_perf_budget.py -> 19 passed.
- Not verified (lane: no Postgres/parity): Postgres 2 pass, client4 parity 59/0/0 (parity JSON summary reads cases 59, pass 59, mismatch 0, unstable 0), check-all 17/19.
