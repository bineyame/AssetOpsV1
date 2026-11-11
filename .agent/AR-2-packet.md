# AR-2 packet: Site boards' mini depth served from period-read rows (D-ANY.6)

Branch `task/ANY-1-AR2` (worktree `AssetOpsV1-ar2`) from `bb3d7645c` (ANY-1 phase 1-2 head).
Spec: `.agent/architect-answer-any-range-speed-2026-11-10.md` §4 card AR-2; D-ANY.1-6
(`build-sheet-OWN-GAPS-2026-11-08.md` @ `6d81b8931`). USER_REVIEW_REQUIRED: no (D-ANY.6: reviewer ACCEPT gates merge).

## Outcome delivered

| Item | Where |
|---|---|
| Kinds `mini_depth.{renewable,fuel,service,backup}`: body = the hour facts `_hour` derives today (selected head, live jobs, the `_cutoff_sha` stale answer, pending IDs), built once per (Site, day, kind) by `MiniDepthRead.build_period` through `_hour` itself; renewable = one local-day row of its daylight/missing hours, fuel/service/backup = the local-noon hour the board reads | `mini_depth/period_rows.py`, `mini_depth/read.py` `build_period` |
| Revision provenance: the link rows of each selected revision's accepted IDs stored once in `revision_provenance` (`{"link_rows"}`); pending IDs' link rows in the hour body; the read runs the same `mini_blocks` over them (`StoredLinkRows`; a missing ID = 503) | `period_rows.py`, `read.py` `_row_hours` |
| `mini_depth/read.py` reads rows: `_read` -> `_row_hours` (1 row statement + ledger + dirty + 1 provenance statement; no raw reading, no daylight, no link-row SQL, no `_cutoff_sha`) else compose; both feed one `_envelope` | `read.py` |
| Rendering at k: CURRENT -> HISTORICAL for an earlier explicit k; a PENDING period (unconsumed event / dirty / older builder) -> PENDING_RECOMPUTE over its stored head; absent -> head none, UNKNOWN, job NONE (renewable absent day: the calendar's no-binding hours, `absent_renewable_windows`) | `period_rows.py` |
| Kill switch: `ASSETOPS_PERIOD_READ_KINDS` empty/unset (or kind not listed, or a non-board hour) -> today's compose; `_cutoff_sha` stays only on the compose path (oracle) | `read.py` `_row_hours` |
| Register declares the four kinds (all mini roles, own selection domain, job domain, Foundation) | `config/chain/event-register-v1.yaml` |
| Wiring: `period_kind_builders(inputs)` (tick drain + backfill), `period_kind_versions()`, `build_mini_period_rows()`; `main.py` gives the board's `MiniDepthRead` the row reader | `chain/composition.py`, `main.py` |
| Prepare: `build_period_rows` after `drain-2`, before the self-check; backfill CLI `--quiet` per mini Site, timed per Site and total, 15-minute cap; over cap/failure prints "serve with ASSETOPS_PERIOD_READ_KINDS= (empty)", writes `period-rows.json`, prepare goes on | `tools/demo_combined.py`, `chain/period_backfill.py` |

## D-ANY.6a fix (commit `28dd36c84`)

`mini_depth/read.py`: `_JOBS` is now built from one predicate `_JOBS_WHERE`; `_JOBS_BATCH` runs that same predicate
over all the request's hours in one statement (`unnest(...) WITH ORDINALITY`) at k, live and historical.
`MiniDepthRead._job_fallback`: an hour whose live job IDs (and the job state they give) equal its row's renders from
the row; any other hour (absent rows included, stored set empty) is replaced by `_hour` for that hour only, logged
`period_row_job_fallback` (WARNING, `assetops.mini_depth.read`) and counted (`job_fallback_count()`); a read with any
fallback takes link rows live, as the compose does. Migration 0029 untouched; no events, no timing rules.

## Checks run

- No-DB `backend/tests/test_ar2_mini_period_rows.py`: 14 passed (new `test_job_set_differs_falls_back_...` x3:
  new job, moved-later job, status change). Non-vacuity: `_job_fallback` returning 0 -> 9 failed (the three fallback
  cases among them); reverted by `git checkout`.
- Postgres, own `assetops_ar2_test` (created, routed run DBs, dropped after), rev `28dd36c84`:
  `pytest test_ar2_mini_period_rows_postgres.py test_ar2_mini_period_rows.py` -> **17 passed**, wall 415 s, JUnit
  tests 17 / failures 0 / errors 0 / skipped 0. `:116` passes (rows == compose, PENDING_RECOMPUTE, live and at a
  historical k, one fallback each); new `test_rows_follow_a_job_moved_later_than_the_read` passes.
- client4 (`assetops_polish_client4_test`, 0059) row build: KOBO-001 128/128 written 69.1 s; KISIWA-001 52/52
  written 38.7 s; **total 107.8 s** (cap 15 min).
- client4 parity `--kinds mini_depth.{renewable,fuel,service,backup}` (seed 20261111, random 16, `--work`/`--story`
  e3c polish_client4, prebuilt routes), rev `28dd36c84`, wall 976.7 s:
  **`period_read_parity: FAIL (59 cases, 0 mismatch, 7 unstable)`**, exit 1. All 7 UNSTABLE are live estate reads
  (story.0/3/36/39, any.portfolio.1/3/5: `/api/estate/portfolio`, `/api/estate/findings`); the oracle differs from
  itself at `selection_token` (`estate/scope.py` `selection_token(..., token_k, ...)` hashes the live now), which
  `normalise_live_now` does not normalise. No mini-depth/board case is unstable or mismatched. Harness defect.
- Harness fix `aa5a6c9b3` (`tools/checks/period_read_parity.py`): in a live request only, `"selection_token"` is
  normalised to `<live-token>` like the `known_at` echo. Self-test PASS; `test_period_read_parity.py` 7 passed; new
  self-test cases: a historical request's token difference -> MISMATCH, a live real body difference beside the token
  -> MISMATCH; non-vacuity tests: normalising the token on historical reads, or not normalising the live token, each
  make the self-test fail.
- client4 parity `--kinds` (four kinds), rev `aa5a6c9b3`, start 18:20, wall 785.7 s:
  **`period_read_parity: PASS (59 cases, 0 mismatch, 0 unstable)`**, exit 0. `any.between_revisions.site_day_snapshot`
  PASS.
- client4 full parity (no `--kinds`), rev `aa5a6c9b3`, start 18:33, wall 872.7 s:
  **`period_read_parity: PASS (59 cases, 0 mismatch, 0 unstable)`**, exit 0.
- `perf_budget.py --any-range --store off --runs 1 --report` (client4, `--story`), rows off / on (`--kinds` four):
  verdict both `FAIL (12 breach, 0 not measured) [report mode: exit 0]`. Board cold ms off -> on:
  KISIWA 10-25 (board.0) 1580.9 -> 1763.5; board.6 1625.7 -> 1693.9; KISIWA 10-17 (board.10) 1303.3 -> **2187.0
  BREACH**; KOBO 10-20 (board.14) **4189.8 BREACH** -> 1922.1; KISIWA 10-22 (board.15) 1468.3 -> 1448.2.
  Portfolio (not touched by AR-2): portfolio.1/3/5 10.8-26.3 s breach in both; portfolio.2/4/7/8/9/11/12/13 return
  **422** in both (pre-existing, not AR-2). One run each: single-sample noise is large.

## Known deviations

1. `mini_depth.renewable` is a local-day row holding its hours (register grain `local_day`), not one row per hour:
   a day with no expected hour must be a stored empty list, not an absent row; dirtying is per day anyway.
2. Fuel/service/backup store only the local-noon hour the board reads. Any other hour (the `/mini-depth` API with
   another hour) stays on the compose path - a scope boundary, not a fallback for absent rows.
3. The envelope is still composed per request from stored facts (known_at, HISTORICAL and the cross-day aggregate are
   request properties); the stored body is facts, not the final fragment.
4. Provenance link rows are stored as of build time; today's compose reads them live without a cutoff. A link row
   added later for an old evidence ID is not seen until the day is rebuilt.
5. (Closed by D-ANY.6a.) A job created, moved later, or changed in status after the build is seen at read time by the
   batched `_JOBS` check; that hour is served by `_hour` until the row is rebuilt.
6. The risks-table AST guard is a runtime guard instead: the no-DB and Postgres tests make every raw-read function
   raise on the row path.

## Residual risk

1. Speed gain is modest and uneven: the worst board (KOBO 10-20) drops 4.2 s -> 1.9 s; the others stay ~1.4-1.8 s
   (mini depth was not their dominant cost). One cold run per case, so no p95 claim.
2. Rows exist only for the built range (KOBO 10-11..11-11, KISIWA 10-30..11-11). Earlier days read as absent
   (`period_row_absent`, nothing known at k); parity shows this equals the compose on client4, but a database whose
   selections predate its row range would show UNKNOWN where the compose shows a head. Rebuild rows after add-dates.
3. While a recompute is in flight (add-dates), affected hours take `_hour` (old speed) until the row is rebuilt;
   watch `period_row_job_fallback` in the log. Correct by construction, not faster.
4. Deviation 4 (provenance link rows frozen at build) remains.
5. The Postgres test uses the W4-02 fixture; client4 parity (59 cases, seed 20261111) is the only real-data proof.

## Prepare-time impact

`build_period_rows` after `drain-2`: client4 KOBO-001 69.1 s (128 periods) + KISIWA-001 38.7 s (52) = **107.8 s**
(cap 15 min). Over the cap or on failure, prepare continues and prints the kill-switch line; see `period-rows.json`.

## Kill switch (demo fallback)

Set `ASSETOPS_PERIOD_READ_KINDS=` (empty, or unset it) in the backend's environment and restart the backend: every
board reads today's compose (the oracle); stored rows are ignored and nothing needs deleting. To serve rows:
`ASSETOPS_PERIOD_READ_KINDS=mini_depth.renewable,mini_depth.fuel,mini_depth.service,mini_depth.backup`. Rebuild a
Site's rows: `python -m assetops_backend.chain.period_backfill build --site KOBO-001 --quiet` (`DATABASE_URL` set).
