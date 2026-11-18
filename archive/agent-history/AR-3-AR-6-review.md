# AR-3 + AR-6 review (task/ANY-2-AR3-AR6, head 7a6e29c19)

Reviewer: fresh Claude reviewer (did not author). Base: merge-base with main `bb171b72b`; merged-in main content ignored.
Spec: sequence 2026-11-11 AR-3/AR-6 card; D-ANY.5, D-ANY.6, D-ANY.6a, D-ANY.7. Packet: `.agent/AR-3-AR-6-packet.md`.

## Verdict: ACCEPT WITH NOTES (M1 fixed on the branch before merge)

## Findings

- **M1 Medium - 507 ignored `.pyc` files committed** (commit `2dae82d48`, `backend/tests/__pycache__/*.pyc`; `.gitignore:10`
  ignores `__pycache__/`; the `git add -f` for `.agent` swept them in). Merging adds 507 binary files to main and
  stale bytecode risk for other checkouts. Fix: `git rm -r --cached backend/tests/__pycache__` (and any other
  `__pycache__` in `git diff --name-only bb171b72b HEAD | grep pyc`), commit. No code change.
- **L1 Low - rows read outside the request snapshot** (`estate/coverage.py:66-75`, `chain/dispatch_day_rows.py:175`):
  the live rows read is unbounded (latest revision) on its own connection, while `finding_index` / `match_pass` come
  from the request snapshot at k. A row built between the two can name a selection seq past the match pass and read
  transiently PENDING (unmatched). Same shape as AR-2; honest direction (pending, never a false CURRENT). No fix needed
  now; note for AR-4.
- **L2 Low (residual risk) - builder registered everywhere** (`chain/composition.py:77-87`): after merge the tick builds
  `dispatch.day` rows for every dirty MINIGRID day on every DB, independent of the kill switch (each ~0.2-0.7 s of
  compose, packet item 5). Harmless for correctness; adds worker load during live add-dates. Name it in the runbook.

## Checked and correct

- Row/compose equality: body = `select_dispatch_days_on` day minus `known_at`, type-tagged codec round-trips
  (datetime/date/UUID/Decimal); builder reads in its own READ ONLY REPEATABLE READ at `clock_timestamp()`.
- PENDING/known_at: `known_at` re-attached per request; PENDING at k (outbox, dirty mark, old builder version) adds
  one synthetic PENDING job, which coverage maps to PENDING_RECOMPUTE. D-ANY.6a class checked: dispatch jobs are
  filtered by `created_at <= k` and status (not `available_at`), and every `recompute_job` insert/status/window change
  emits `job.changed` (0044 trigger) with `job_domains: [dispatch]` in the register, so no event-less job path.
- Absent rows: D-ANY.5 no-row rule (no selection, UNASSESSED, `NOT_BUILT` reason), logged/counted via
  `PeriodReader` absent. D-ANY.7 (AR-4 claim days) does not apply: here the absent day has no page-selected revision.
- Kill switch: `served_kinds()` default empty -> provider returns None -> `snapshot.dispatch_days` (today's compose).
  No branch file adds `dispatch.day` to `ASSETOPS_PERIOD_READ_KINDS`.
- Merge resolutions: `composition.py` unions mini kinds + `dispatch.day` in builders, versions and `__all__`; register
  has the 4 `mini_depth.*` kinds and `dispatch.day` (grain `s3_day`) in one `kinds:` map; `s3_day` resolution only
  touches s3 kinds.
- Clock-guard allowlist `PostgresAssessmentStore.dispatch_day_now.work` (`test_ch5c2_clock_guard.py:43-45`):
  justified (row builder's own read instant, transaction time per D-ANY.5, never a stored compose).
- AR-6: `read_many` runs `_page` per request in one `snapshot`; `read` is the one-request case; prefetch only on a
  first-page `incidents` call, misses/cursors/failures fall back to the four single reads; pin memo deep-copied.

## Checks run (by me, no DB)

- Focused: ar3, ar6, any1, ar2, ch1b_drain, ch1b_register, ch5c2_clock_guard, tools event_register: **145 passed**.
- Adjacent non-Postgres (site_outcome/out_b/work_index/site_index/outc_/visits/board/cov/estate_): **566 passed**.
- `tools/check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` = plan2 venv): "Architecture check passed.", exit 0.
- Not run (lane rules): Postgres files, parity, perf. Packet's Postgres (2 + 1 + 4 + 3 passed) and client4
  `--kinds dispatch.day` parity PASS (59 cases, 0 mismatch) are cited, not re-verified.

## NOT DONE items: should merge wait?

- **No for merge.** With the kill switch empty by default, merge changes no served read; dispatch.day equality is
  proven alone (direct probe 29 days x 2 Sites, parity PASS).
- **Combined-kinds parity (AR-2 kinds + dispatch.day) must pass before `dispatch.day` is added to
  `ASSETOPS_PERIOD_READ_KINDS` on any demo DB.**
- `perf_budget --any-range` is measurement: AR-3's Portfolio gain is not realisable until AR-4 switches
  `evidence_money.mini_grid_rows` (deviation 4). AR-6's "Cold/EV boards < 1 s cold" acceptance is **unverified**
  (no before/after timing); run it before claiming the AR-6 speed target.
