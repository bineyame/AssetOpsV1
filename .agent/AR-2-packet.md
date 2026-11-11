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

## Checks run

PLACEHOLDER

## Known deviations

1. `mini_depth.renewable` is a local-day row holding its hours (register grain `local_day`), not one row per hour:
   a day with no expected hour must be a stored empty list, not an absent row; dirtying is per day anyway.
2. Fuel/service/backup store only the local-noon hour the board reads. Any other hour (the `/mini-depth` API with
   another hour) stays on the compose path - a scope boundary, not a fallback for absent rows.
3. The envelope is still composed per request from stored facts (known_at, HISTORICAL and the cross-day aggregate are
   request properties); the stored body is facts, not the final fragment.
4. Provenance link rows are stored as of build time; today's compose reads them live without a cutoff. A link row
   added later for an old evidence ID is not seen until the day is rebuilt.
5. A job whose `available_at` is later than the build but `<= k` has no event at that instant; it becomes visible
   when its `job.changed` event dirties the day.
6. The risks-table AST guard is a runtime guard instead: the no-DB and Postgres tests make every raw-read function
   raise on the row path.

## Residual risk

PLACEHOLDER
