# INFRA-1 review packet: no degraded store (D-E5.47, BL-71)

Branch `task/INFRA-1-no-degraded-store` (worktree `AssetOpsV1-infra1`), from main `bfe609500`. Commits
`0603dd486` (build + tests), `ad8db2a5f` (driver kept in the adapter for the guard; `latest_good` Postgres test),
then the packet. USER_REVIEW_REQUIRED: no (server rule + one retry notice; the
owner sees it only when the DB is refused).

## Outcome delivered
A read failure whose cause chain holds a DB/network connection error is never stored and never rendered as a data
fact. The store serves the newest good copy (`stale`) or a 503 `TEMPORARILY_UNAVAILABLE`; the prebuild retries and
reports `DEGRADED`; `demo_combined` exits non-zero; the frontend shows "Temporarily unavailable. Retrying…".
Honest deterministic states (a bare `LedgerUnavailable("DATABASE_URL is not set")`) stay PARTIAL and are stored.

## Files materially changed
- new `backend/assetops_backend/infra.py`: `is_transient` (walks `__cause__`, `__context__`, `.orig`),
  `is_connection_error`. It matches driver classes by defining module + name along the MRO, so it imports no DB
  driver (the configuration-persistence guard refused a driver import outside the adapters on the first guard run;
  fixed in `ad8db2a5f`).
- The `handle_error` backstop (`_on_handle_error`, `install_handle_error_hook`, idempotent, skips
  `ctx.is_pre_ping`) lives in `chain/adapters/postgres_response_store.py`, exposed through
  `chain/composition.install_handle_error_hook`, which `create_app` calls.
- `read_scope.py`: `ReadScope.degraded`, `note_failure(name, error)`, `mark_degraded(name)` (the hook's mark).
- `chain/response_store.py`: `serve` checks `sc.degraded` after the compose (also compose-only) -> `_degraded`;
  a transient lookup failure -> `_degraded` without composing; `_unavailable()` 503; `connections()`.
- `chain/adapters/postgres_response_store.py`: `latest_good(route, key, version)` (newest by `built_at`, any W,
  any `valid_until`), `connections()` (`pg_stat_activity`).
- `chain/prebuild.py`: retries a 503/`stale` path after 2, 5, 10 s (`RETRY_WAITS`, `_sleep` seam); summary gains
  `degraded`, `still_degraded`, `pg_stat_activity`; `code` `DEGRADED`. Logs `prebuild_start` with the count.
- `scheduling/run.py`: `prebuild` CLI exits 1 on `DEGRADED` as on `FAILED`.
- `tools/demo_combined.py`: `prebuild_refusal(stdout)`; `performance_and_prebuild` raises SystemExit naming the
  paths on `DEGRADED` (and on `FAILED`, see deviations).
- `main.py`: `create_app` calls `install_handle_error_hook()` (from `chain.composition`).
- Frontend: new `sites/temporarilyUnavailable.ts` (`fetchRetrying`, copy, 2/4/8 s); `outcomeBoardClient.ts`,
  `OutcomeBoard.tsx` (retrying / still-unavailable notice), `estateClient.ts` (`readEstate` retry for the summary
  only; `REFUSAL_COPY.TEMPORARILY_UNAVAILABLE`), `EstatePortfolio.tsx` (`SUMMARY_RETRYING`),
  `PortfolioOutcomes.tsx` (`OutcomeMatrixBody` shows the copy).

### note_failure call sites (rule 2 grep of `chain/`, `estate/`, `site_outcomes/`)
`mini.py` `Reads.call`; `read.py` 405 `site_selected_windows`, 597 `site_selected_windows_many`, 635
`seed_snapshots`, 684 `board.<SITE>`, 723 `estate_counts`; `cold.py` 145 `cold_findings`; `ev.py` 156
`ev_findings`; `claims.py` `opportunity_items`, `estate_count_claims` (2 catches), `EstateClaims.day_grades`,
`EstateClaims.__call__`; `estate/index.py` `opportunity_read`. Not marked: `mini.py:872` (`place()`, no read),
`response_store.py` 168/194 (the store's own catches; 168 now follows the rule when transient).
`from error` additions: none needed. `is_transient` walks `__context__`, which Python sets on every raise inside an
`except` (also under `from None`), so the 316 wrapper raises found by grep are classified without edits.

## Acceptance (pinned tests, D-E5.47)
| Test | File | Result | Fails before |
|---|---|---|---|
| T1 OperationalError mid-compose: nothing inserted, old bytes, `stale`, no ETag | `test_infra1_degraded_store.py` | pass | yes (served PARTIAL `stored`) |
| T2 empty store -> 503 `TEMPORARILY_UNAVAILABLE`, nothing inserted (+ compose-only, + transient lookup) | same | pass | yes (3 tests) |
| T3 bare `LedgerUnavailable` -> PARTIAL, stored | same | pass | passes on main: it pins the kept behaviour, it cannot fail before |
| T4 `is_transient` table (16 rows: wrapped cause, implicit context, bare wrapper, pool `TimeoutError`) | same | pass | yes on main (`infra` absent, ImportError); passes with only `infra.py` restored |
| T5 `handle_error` marks the scope on a refused connect; good read and statement error mark nothing; unhooked marks nothing | `test_infra1_handle_error_postgres.py` | 2 passed (Postgres, not skipped) | yes (`infra` absent on main) |
| T6 503 once then 200 -> OK; stale retried; always 503 -> `DEGRADED`, waits [2,5,10], `demo_combined` SystemExit, CLI exit 1 | `test_infra1_degraded_store.py` | pass | yes (3 errors: no retry/`_sleep`) |
| T7 503 -> "Temporarily unavailable. Retrying…", then "Still unavailable…", never "No target set yet"/Unknown/PARTIAL | `frontend/src/sites/__tests__/temporarilyUnavailable.test.tsx` | 6 passed | 4 of 6 fail on main sources |
| extra: real `latest_good` SQL serves the older-W row as `stale` | `test_ch5c_response_store_postgres.py` | pass | n/a (new) |

Fail-before method: build committed, then `git checkout main -- <changed sources>` (keeping new files), run, then
`git checkout HEAD -- <same>`; `git status` clean afterwards.

## Checks run (worktree, Python `AssetOpsV1-plan2\.venv`)
- `test_infra1_degraded_store.py` 25 passed; `test_infra1_handle_error_postgres.py` 2 passed (DB
  `assetops_infra1_test`, pg_stat_activity 110 before).
- Adjacent no-DB: `test_ch5c_store_off` 17, `test_ch5b_why` 49, `test_uq6a_message_seam` 31, `test_qw1_perf` 8,
  `test_qw2_reuse` 4, `test_out_c2_board` 13, `test_ch5a1_summary_ledger` 1, `test_ch5a1_scope` 7,
  `test_ch5a2b_claims` 31, `test_ch6b2_portfolio_cards` 55, `test_ch6b_estate_chain` 20: all passed, 0 skipped.
- Postgres (count 107-109 before each): `test_ch5c_response_store_postgres` 9 passed, `test_ch5c2_store_safety_postgres`
  10 passed, 0 skipped.
- Vitest: `temporarilyUnavailable` 6, `outcomeBoard` + `estatePortfolio` + `estatePortfolioRoutes` 116,
  `estateRoots` + `globalMaintenance` + `workRequestOverview` 92: all passed. `tsc --noEmit` clean.
- `tools/check-architecture.ps1`: ARCH_RESULT
- Not run (per dispatch): full suites, check-all, captures, layout evidence (`layout evidence: not run`, a status
  line only; no layout claim made).

## Known deviations
1. `infra.is_transient` treats the deterministic file-system `OSError` subclasses (`FileNotFoundError`,
   `PermissionError`, `FileExistsError`, `IsADirectoryError`, `NotADirectoryError`) as NOT transient. The ruling
   says `OSError`; read literally, a missing manifest would 503 forever instead of showing its honest state.
   Connection `OSError`s (`ConnectionError`, `TimeoutError`/`socket.timeout`, others) stay transient. Architect to
   confirm.
2. `demo_combined` now exits non-zero on prebuild `FAILED` too (before, it printed the line and continued). The
   ruling reads "treats DEGRADED like FAILED: prints the paths and exits non-zero"; this makes FAILED match.
3. Compose-only mode (`ASSETOPS_RESPONSE_STORE=compose`) touches no store row, so a degraded compose there is the
   503 directly (no `latest_good`).
4. A transient lookup failure does not compose (the DB is refusing); it re-reads the admitted Sites once for the
   key, and any failure there is the 503.
5. The frontend retry applies to the board and the summary fetches only; the Portfolio body's own 503 maps to the
   still-unavailable copy through `REFUSAL_COPY` but does not retry.

## Residual risk
- The serve loop's tick prebuild can now spend up to 17 s per degraded path (by design; the tick report's seconds
  show it).
- The hook marks the current scope for any `OperationalError` the engine reports during a compose, including one a
  composer would have recovered from; the safe direction (a stale copy, never a stored degraded body).
- Not covered: non-stored routes and the shared capped engine factory (deferred to BL-71 per the ruling).

## User-review focus
Deviation 1 (file `OSError`s) and 2 (`FAILED` now stops `demo_combined`).
