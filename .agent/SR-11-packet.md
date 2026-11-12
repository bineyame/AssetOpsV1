# SR-11 packet: Backup over the range, server (lane J)

Branch `task/SR-11-backup-range` from SR-10a core 7f928edb2, + SR-10b route 3fc8c4c23, + main, + SR-10 D-SR.51 fix ee97829ef.
Spec: rev 10b.1/10b.3, 10d.4 (D-SR.45 `window_days`), D-SR.31/33/36/51-54.

## Outcome
- `GET /api/sites/{code}/backup-range`, schema `site-backup-range-1`: `main.py` wires `"backup"` through SR-10b's
  generic `build_day_range_router` (one loop over `("fuel", "backup")`, same readers, stored route, refusals
  `BACKUP_RANGE_NOT_APPLICABLE` / `SITE_BACKUP_RANGE_UNAVAILABLE`). No core file edited (core belongs to SR-10).
- Per day: backup start sequences de-duplicated by `chain_id` (latest hour wins); never an outage count.

## Files
- `backend/assetops_backend/main.py` (wiring only)
- `backend/tests/test_sr11_backup_range_route.py` (new, no-DB, 17 tests)
- `backend/tests/test_sr11_backup_range_postgres.py` (new, `assetops_sr11_test`; imports SR-10a's day-kind helpers)

## Acceptance (rev 10b.3 server part, D-SR.51)
| Item | Status |
|---|---|
| Route wired in `main.py` | Done; `test_main_wires_both_day_range_routes` (openapi paths). Non-vacuous: wiring reverted to fuel only -> fails, restored |
| Body: 7-day Nairobi window = 7 rows, states SEQUENCES_PASSED/FAILED/INCOMPLETE, NO_SEQUENCE, STILL_PROCESSING (absent + pending), NOT_EXPECTED, `partial`, hour link to `performance/backup` | Done (stub) |
| De-dup by chain_id within a day, latest hour wins | Done (stub + Postgres vs live one-hour cards) |
| Start successes: sum of non-null, null when all null | Done (stub) |
| D-SR.51.2 slowest recovery: null skipped, tie -> earliest start | Done (stub) |
| D-SR.51.3 absent day `stored: false`, null counts; stored rows `stored: true`, no null counts | Done (stub + Postgres) |
| D-SR.51.4 window totals de-dup by chain_id: a sequence crossing local midnight counts once | Done (stub; per-day PASS sum 5, total 4) |
| No outage key anywhere (except a sequence's `outage_start`) | Done (stub + Postgres; non-vacuous: `outage_start` present) |
| 422/404 (Cold, EV)/401/403/503, stored key + watermark Site, perf line, one period + one chain read with known_at | Done (stub) |
| Page `MiniBackupRange.tsx`, vitest, RANGE_MATRIX D->R, sr2RequestUrls | **Not started** (waits for SR-4) |
| Backfill, `.agent/SR-11-parity.json`, 2 s timing | **Pending** (coordinator heavy-job queue) |

## Checks
- No-DB: `test_sr11_backup_range_route.py` + `test_sr10_fuel_range_route.py` + `test_sr10_day_summary.py`:
  45 passed (on ec11b79ba, after merging SR-10 fix ee97829ef; before that merge the 4 D-SR.51 tests failed as expected).
- Postgres (`assetops_sr11_test`, created for this lane): `test_sr11_backup_range_postgres.py` 1 passed, 53 s wall.
  The W4-02 fixture has no backup-role readings, so the built day is NO_SEQUENCE and the live-vs-stored sequence
  comparison is an empty-set equality there; de-dup is pinned by the stubs.
- `check-all.ps1` on ec11b79ba (854 s): **2 of 19 failed**, both from one cause outside SR-11's files:
  "Database driver imported outside ... in backend/assetops_backend/mini_depth_api.py:20: from sqlalchemy.exc import
  DBAPIError" (Architecture seams; and the Estate guard self-tests, which re-run that check). The import comes from
  SR-10b 3fc8c4c23 (`git log -L20,20`); main's `mini_depth_api.py` has none. Core file, not edited here (coordinator
  instruction); SR-10 must drop it (e.g. pass the driver error through `unavailable=` from `main.py`).

## Depends on SR-10's choices (D-SR.51 confirmed 1, 2, 4; corrected 3)
- Pending/assessed/missing hour classes and "assessed hours only" sums (51.1).
- `days_counted` over the four backup states (51.4); totals `partial` = a requested day not counted or a counted day partial.

## Questions (not designed around)
1. Absent day `sequences`: D-SR.51.3 nulls the counts and figures but does not name `sequences`; tests do not pin it.
2. Window `start_success_count` with a sequence crossing midnight: it is a sum of hour cards, not per sequence, so
   "de-duplicate by chain_id" has no handle on it. The test keeps successes off the crossing hours and pins 1.
3. The Postgres test grades days with SR-10b's stub snapshot port (all COMPLETE), not a real `PostgresChainRead`;
   the grade order is pinned in the stubs. Say if the real chain port is wanted here.

## Residual risk
- `main.py`: SR-8's renewable range router lands next to the same block; the second merger resolves.

USER_REVIEW_REQUIRED: no (server slice; the page waits for SR-4).
