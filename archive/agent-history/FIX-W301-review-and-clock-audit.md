# FIX-W301 review and clock time-bomb audit

Reviewer: fresh Claude reviewer, 2026-10-31 (real clock about 12:35 UTC at start). Branch
`task/FIX-W301-estate-index-tests`, commit `db37fc680`, base main `15eed62c8`. All runs used a
`git archive db37fc680` snapshot, the plan2 venv, and `assetops_test` (template-routed private DBs).

## Job 1: FIX-W301. Verdict: ACCEPT

### What was checked
- The diff is test-only: `backend/tests/test_w301_estate_index_postgres.py:757-761`, plus the task file and packet.
  `LATE["decided"]` becomes `iso((now_utc + 1 day).replace(minute=0, second=0, microsecond=0))`.
- **Run from the snapshot:** `pytest tests/test_w301_estate_index_postgres.py -q` gave **20 passed in 401.10 s**.
  That matches the packet's 20 passed (402 s and 410 s).

### Is the fix sound? Yes.
- `CaseRunner.step` moves `runner.now` to `max(now + 1 min, decided)` (`test_s4_finding_store_postgres.py:128-130`).
  The ledger stamps the mini-grid job and evidence with `decided` (`test_decision_clock_override`).
- `test_historical_minigrid_outstanding_marker_page_two_keeps_basis` uses `k = runner.now` as an explicit `known_at`.
  The cold `late-reading` replay in the `pair` fixture runs on the real clocks, so its Findings and selections carry
  database-clock stamps.
- With a fixed `k = 2026-10-31T08:00Z` and the real clock past it, the cold Site has nothing selected by `k`. Page one
  then has no second row and no `next_cursor`, so page two fails. That matches the packet's account. With `k` a day
  ahead of the real clock, every database-clock row is at or before `k`, and the read time is pinned to
  `max(runner.now + 1 min, db_now) + tick`, which stays above `k`.
- **Other assertions on the old instant:** none. `LATE` is used only at `:812` (`test_live_pending_minigrid_page_two_keeps_basis`)
  and `:893`. Neither asserts the literal value; both read the `PENDING_RECOMPUTE` state and the cursor mode, which do
  not depend on the exact instant. The other fixed instant in the file, `:493` (`decided 2026-10-30T16:00Z`, in
  `test_late_support_change_recurrence_at_exact_cutoff`), is already in the past and passes. The DB-clock audit below
  (+77 days, same mechanism) shows the same pattern is harmless in idx_gaps and s4_finding_index.
- **Midnight and DST:** no issue. The arithmetic is on an aware UTC datetime, so there is no DST, and `+1 day` across
  midnight or month end is ordinary timedelta arithmetic. Truncating to the hour still leaves at least 23 h of margin.
- **Residual (Low, not blocking):**
  1. `LATE` is computed once, at module import. It holds only while a pytest process takes less than 23 h from
     collection to these tests, which is far beyond any tier.
  2. The comment calls the value "always ahead of the DB clock". That assumes the container clock and the host clock
     agree to within that margin, which they do.

### The unreproduced `test_cold_revision_waits_for_its_selected_assessment` KeyError
The packet is honest: the KeyError was not reproduced, nothing was changed, and the test is to be rechecked if it
recurs. I accept that. Its cause is weak, though: "contention with the demo-data lane" is a guess.

The test is not a fixed-date bomb. It runs entirely on the database clock, with `k = selected - 500 ms`.

The KeyError is on `seen[finding]` (`:955` now, `:952` before the fix). The loop at `:954` walks every `moved`
Finding, meaning every cold Finding whose revision carries the last selection's transaction time. It never checks
that the Finding was in `old`, or that its row falls in the one-day window. Two cases would make `seen` lack it:
- the late run created a new Finding in that last transaction;
- the last job processed covered a Finding outside `DAY`.

Both are order-dependent: which job's selection is `max(selected_at)` can vary with job processing order. That is a
more concrete candidate than contention.

**Suggestion (Low, follow-up only):** add `assert set(moved) <= set(old), (moved, old)` before the loop. The next
occurrence would then be diagnosable instead of a bare KeyError. It does not block this fix.

### Checks not run
I did not run `check-all.ps1`, the architecture guard, the workflow guard, or the frontend suite: the change is
test-only and backend-only. The packet's `tools\check-all.ps1: see below` has no result under it, which is a packet
gap (Low).

## Job 2: clock time-bomb audit

### Method
I added a review-only pytest plugin, kept in scratchpad and outside the repo:
`...\scratchpad\plug\fakeclock_plugin.py`.

- It creates a `fakeclock` schema in this run's private template DB and its clones.
- It defines `now()`, `clock_timestamp()`, `transaction_timestamp()` and `statement_timestamp()` as the real value
  plus N days.
- It puts that schema before `pg_catalog` through the URL option `search_path=public,fakeclock,pg_catalog`. Column
  defaults, triggers, inline SQL and the estate/S3 `now()` reads all see the shifted clock.
- **Sanity check:** a +5 day run reported `db now 2026-11-05`, 107 public tables, and Python now `2026-10-31`.
- No machine clock was changed, and no shared database was touched.

**Limitation:** the Python clock is not shifted. Tests whose processes use the real Python clock alongside the
database (cold and EV host replays, `datetime.now` in tests) show a skew that cannot happen in reality. Every
failure of that kind is classed below as an artifact, with the evidence for that call.

### Runs (DB clock +77 days, so about 2027-01-16; this covers every fixed instant through 2026-12)
- **Batch A** (S6 store, apply, records, site action index, verification plan, evaluator, holds; idx_gaps;
  s4_finding_index; s3_claim_limit; all 4 w401 Postgres files; all 4 w303 Postgres files): 109 passed, 7 failed,
  8 errors, 1197.7 s.
- **Batch B** (w402_migration, out_b4_board, s4_consequence_store, s4_finding_read, s4_finding_store,
  s4_consequence_history, s4_finding_evidence_history, w301_estate_golden): 52 passed, 5 failed, 1240.0 s.
- **Bisect** of the one real bomb: +0 days passed (13.4 s); +0.6 days (DB at 2026-11-01 03:21Z) failed (12.9 s).

### Time bombs, ranked by break date

| # | Break date (UTC) | File:line | Why |
|---|---|---|---|
| 1 | **2026-11-01 01:01** (tonight, 04:01 at +03:00) | `backend/tests/test_w401_site_indexes_postgres.py:175-181` (`test_pending_link_and_missing_source_keep_gap`; the failing assertion is `:189`) | The test re-selects the dispatch day with `selected_at = clock_timestamp()` (the real DB clock), then reads at the fixed `Lists(POSITIVE_NOW + 1 min)` = `2026-11-01T01:01Z` (`POSITIVE_NOW`, `test_w401_work_service_postgres.py:111`). Once the DB clock passes 01:01Z, the reselection is after the read cutoff and invisible. The fence reads `CURRENT` and the assertion expects `PENDING_RECOMPUTE`. **Confirmed:** passes at +0, fails at +0.6 d and +77 d. Fix: stamp the reselection inside the virtual clock, e.g. `POSITIVE_NOW + 30 s` instead of `clock_timestamp()`; or read at `max(POSITIVE_NOW, db_now) + 1 min`, as `:333` and `:400` already do. |

**No other confirmed bombs.** In particular, everything in the brief's heavy list passed at +77 days on the DB-clock
mechanism:
- the S6 suites (`T_ACCEPT` 11-01, `CLOSED` 11-02, `LATER` 11-02, `NEXT_LATER` 11-03, `h.clock` 11-02 instants);
- idx_gaps and s4_finding_index (`decided 2026-10-31T08:00Z`);
- s3_claim_limit;
- the w303 portfolio comparison;
- the s4 store and read tests.

Their fixtures inject fixture clocks end to end: ledger decision override, `received_at` from the service clock,
action and verification `Clock`, `VirtualDbClock`, and `max(..., db_now)` pins.

### Failures classed as artifacts of the unshifted Python clock (not bombs)
All of these fail inside a real-clock host replay, before any assertion that compares fixture dates:
- `test_w203_cold_replay_postgres.py:80` `run(...)` returns `outcomes == []`: the worker runs at Python time, below
  the shifted job `available_at`.
- Or the W502/W504 producer subprocess fails.

| Test | Failure site |
|---|---|
| w303_portfolio_comparison (8 setup errors, `build_portfolio_fixture`), w303_portfolio_scope_snapshot `test_late_revision_pending_historical_and_mixed_source[a,b,c1,c2]`, w401 `test_cold_ev_pinned_list_fence_and_reselection`, w401_work_read `test_cold_pinned_link_keeps_its_seq_after_reselection` | cold `run(cold)` gives `outcomes == []` |
| w301_estate_golden `public_replay[cold]`, `public_replay[mixed]`, `clock_plus_30_days[mixed]` | the same, in `cold_replay` (the mini_grid branches passed) |
| out_b4_board `test_cold_w502_positive`, `test_ev_w504_positive` | the W502/W504 producer subprocess fails (real-clock replay) |

In real life the host and the database move together, so these paths are consistent. They are not proven safe on
their own terms, though: a mechanism that needs both clocks shifted could not be simulated here.

### Not covered
- Fixed instants compared against the Python wall clock (`datetime.now` or a default `utc_now`) cannot be shifted
  without a time library, and the venv has none. A grep found no test that pairs `datetime.now()` with a fixed
  future fixture instant. The unit tests (e.g. `test_s6_site_action_index.py`) inject their clocks
  (`clock=lambda: T0 + ...`), so they cannot fire on a date.
- `test_w301_estate_index_postgres.py` was not run shifted: its new `LATE` reads the Python clock, so a DB-only shift
  would be a false positive.
- The +77-day probe finds comparisons that flip once. A test that passes both today and at +77 but fails in between
  would need two opposite comparisons; none was seen in the code read.
