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

## D-SR.58 (merged from main)
- Q1 applied: SR-10's ee97829ef already nulls `sequences` on an absent day; pinned in `test_an_absent_day_is_unknown_not_zero`
  (absent `sequences` null, stored NO_SEQUENCE day `[]`). 17 no-DB passed.
- Q3: accepted, no change.
- Q2: withdrawn by **D-SR.60**. Start successes stay the hour-card sum (null rule unchanged), no label, no
  `start_pair`. Premise pinned by `test_chain_ids_are_unique_across_one_stored_days_hours` (pure: 24 projected hours of
  `rules.assess_backup_hour`, outages spanning an hour and local midnight, 3 chain_ids, unique; next day's 00:00 hour
  adds none). The D-SR.51.4 chain_id de-dup of `sequence_counts` stays as a guard.

## Parity spec additions (SR-11 parity JSON)
- `duplicate_chain_ids` per Site (KOBO-001, KISIWA-001) and window (7/14/31 days): chain_ids appearing in more than one
  stored hour of a `mini_depth.backup_day` row or across days of the window. **Gate 0**; non-zero means the hour rule
  changed: stop and ask (D-SR.60).
- Each live range route's `days[].state` vs `chain.read.day_grade` for the same day (D-SR.58 Q3), gate 0.

## Re-check after merging main + SR-10 guard fix 95a71e92d
- No-DB SR-11 + SR-10 route/summary tests: 46 passed.
- `tools/check-architecture.ps1`: "Architecture check passed." (the DBAPIError import is gone). Full check-all not rerun.

## Residual risk
- `main.py`: SR-8's renewable range router lands next to the same block; the second merger resolves.

USER_REVIEW_REQUIRED: no (server slice; the page waits for SR-4).

## Merge of SR-10 D-SR.70-72 (2026-11-12)
Merged task/SR-10-fuel-range (347d9765a): NO_DATA day state, no_reading_days, parity gate. No merge conflicts; added route test for backup NO_DATA (D3 absent, D5 stored). No-DB tests: 51+ passed (sr11 route 19, sr10 summary/route 32). Parity rerun and Postgres: pending (coordinator). check-all: for coordinator.

## D-SR.70-72 review fix round
Merged task/SR-10-fuel-range (M-1: pending computed with no stored row). L-2: the tautology in
`test_no_reading_days_read_no_data...` is replaced by a `totals` assertion (3 counted of 7, partial, sequence_counts
unchanged). SR-11 route tests: 19 passed.

## Page (lane J, branch `task/SR-7-11-pages`, commit 8e8bb73d8; Lows in f7ea60304)
- `sites/MiniBackupRange.tsx` (MOCK DEVIATION R728); `MiniBackup` branches on `miniRangeView` exactly as Service (SR-7
  packet). Status line "{n} backup starts: p passed, f failed, i incomplete, for n of m days analysed · <gap days>"
  (server totals, D-SR.51.4) plus "Start successes: x" (D-SR.60; null → "No witnessed start request and result").
  Day table: "n backup starts: p passed, f failed, i incomplete" / "Slowest recovery m min (target t)" / state words /
  "Open the 12:00 hour". STILL_PROCESSING "Still being prepared" and NO_DATA "No readings this day" span the row with no
  figures (D-SR.51.3, D-SR.70-72); NOT_EXPECTED, NO_ASSESSMENT likewise. Partial counted day: "· Partial day: a of e hours
  assessed". Never an outage word or count.
- "Sequences in this range": the counted days' sequences once each by `chain_id` (latest day wins, as the totals),
  columns When / Outcome for service / Recovery / Result. **Deviation (question Q-J6):** 10b.3 says "the existing backup
  chain table component fed with the days' sequences", but the stored day rows carry no `steps`, so the hour table's
  six step columns would read "No accepted record" falsely; the range table shows only the fields the rows carry.
- D-SR.57: range view declares nothing; hour view declares once (`miniBackupRange.test.tsx`); Back as SR-7.
- Tests: new `miniBackupRange.test.tsx` 6; `miniBackupRoutes` two-hour + off-clock-hour cases re-pinned to the range view;
  `sr2RequestUrls` pins Kobo and Kisiwa Backup 7 days → `backup-range?from&to`.
- Review Lows: Low 1 the D-SR.60 pin now includes a witnessed request/result pair (`correlation_id` "corr-1" in the
  ids, hour-card start successes sum 1); Low 2 `absent["sequences"] is None` added to the Postgres test (not run: DB
  slot). No-DB SR-11 + SR-10 route/summary: 54 passed.
- Not done: `RANGE_MATRIX` (not on main); Postgres run of the Low 2 line (coordinator DB slot).
