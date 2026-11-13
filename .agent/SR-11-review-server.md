# SR-11 server review (Backup over the range), fresh independent Claude reviewer

- Branch `task/SR-11-backup-range`, worktree `/opt/assetecon/AssetOpsV1-sr11`, head `3989659c1`.
- Scope: SR-11's own commits, `git log --no-merges 95a71e92d..HEAD`. That is 7cf1526dc, d4acfdd41, 713bbf7d8, 10ba0893d and 3989659c1. Architect and coordinator commits (D-SR.55-60, lane rules) are excluded. SR-10 core is reviewed separately.
- Spec: rev 10b.1/10b.3 and 10d.4 (`window_days`); D-SR.31, 33, 45, 51, 58 and 60.

## Verdict: ACCEPT WITH NOTES

There are no High or Medium findings. The two Low notes below do not block the merge.

## What was checked

| Item | Result |
|---|---|
| `"backup"` is wired into the generic range router | `main.py:699-705` loops over `("fuel", "backup")` with the same readers, access, `unavailable` and `responses`. The lambdas do not capture the loop variable, so there is no late-binding bug. |
| Per day: backup start sequences, never an outage count | `test_never_an_outage_count` passes. It is non-vacuous: `outage_start` is present. The Postgres test makes the same check. |
| Start successes are the hour-card sum (D-SR.60) | `test_start_successes_sum_non_null_hours_and_are_null_when_all_are` gives `[1, 0, None, ...]`. The window total is 1. No `start_pair` was added. |
| The chain_id uniqueness pin is real | `test_chain_ids_are_unique_across_one_stored_days_hours` drives `rules.assess_backup_hour` and `projection._backup` over 24 Nairobi hours. Its outages span 11:50-13:20 (an hour boundary), 15:10-15:20 and 23:40-00:30 (local midnight). It asserts exactly 3 rows and 3 unique ids, and that the next day's 00:00 hour adds none. Per `rules.py:1007` and `:1029-1043`, `chain_id = correlation or str(loss_id)` is stable across hours, so `len(ids) == 3` would catch a chain that re-opens in a second hour. |
| `sequences` is null on an absent day and `[]` on a stored day with none | Pinned in `test_an_absent_day_is_unknown_not_zero` (`days[3]` gives null, `days[5]` gives `[]`). |
| `slowest_recovery` | A null is skipped (c6). A tie (90 s) goes to the earliest `outage_start`: c1 with target 120 beats c2 with target 150, so the target value tells them apart. An INCOMPLETE-only day gives null. |
| The main.py wiring test can fail | I verified this myself. I ran `git archive HEAD` into a scratch copy, set the loop to `("fuel",)`, and ran `test_main_wires_both_day_range_routes`: it FAILED. A first attempt that only put the copy on PYTHONPATH was invalid, because pytest's conftest imported the worktree code. The archive copy confirmed it imported the mutated `main.py`. |
| Parity spec in the packet | `duplicate_chain_ids` per Site (KOBO-001, KISIWA-001) × 7/14/31 days, gate 0, with "stop and ask" if it is non-zero. Each live route's `days[].state` is compared with `chain.read.day_grade`, gate 0 (D-SR.58 Q3). Both are present. The run itself is still pending in the coordinator's heavy-job queue. |
| Stub grades in the Postgres test | `Port()` stub, every day COMPLETE. This is documented in the docstring and accepted by D-SR.58 Q3, with the real grade path closed by the parity gate above. |
| Stray or ignored files | The SR-11 commits touch only `main.py`, the two test files and `.agent/SR-11-packet.md`. `git status --ignored` shows only the `frontend/node_modules` symlink, which lane rules expect. Nothing ignored is tracked. |

## Findings

**Low 1: the D-SR.60 pin covers only the loss-id path of `chain_id`.**
- Where: `backend/tests/test_sr11_backup_range_route.py:259-285`.
- What: the series has no START_REQUEST/START_RESULT events. Every `chain_id` is therefore `str(loss_id)`, and the `correlation_id` branch (`rules.py:1007`) is never exercised. That branch is the one in use whenever `start_success_count` is non-null.
- Why it is only Low: the structural part of the pin, one row per outage across 24 hours, does not depend on the id. `_start_steps` also reads only `[t0, end)` inside one hour. Real correlation-id reuse is a data property, which the parity `duplicate_chain_ids` gate covers.
- Optional fix: add one witnessed request/result pair to the 11:50-13:20 outage and assert the same count and uniqueness.

**Low 2: the Postgres absent-day assertions do not include `sequences is None`.**
- Where: `backend/tests/test_sr11_backup_range_postgres.py:91-92`.
- What: D-SR.58 Q1 is pinned only on stubs.
- Optional fix: add `absent["sequences"] is None`.

**Informational: the stub fixtures deliberately break D-SR.60's premise.**
- The fixtures put c1 in hours 02 and 03, and cX in D0 23:00 and D1 00:00.
- This is correct for exercising the D-SR.51.4 de-dup guard, which D-SR.60 keeps.
- A reader should not take these fixtures as the real hour rule.

## Checks run (by me, at 3989659c1, with PYTHONPATH set to the worktree)

- No-DB: `test_sr11_backup_range_route.py`, `test_sr10_fuel_range_route.py` and `test_sr10_day_summary.py` gave **46 passed** in 3.4 s.
- Postgres, `assetops_sr11_test` only: `test_sr11_backup_range_postgres.py` gave **1 passed** in 54 s wall.
  - On the W4-02 fixture the built day has no backup sequences, so the live-versus-stored sequence comparison compares two empty sets. The packet states this.
- Wiring mutation (scratch archive copy): FAILED as expected.

## Not run or not verified

- `check-all` was not run, as instructed; it is for the coordinator. The packet's architecture-check pass on the merged revision is unverified by me.
- No full suite was run.
- The page (`MiniBackupRange.tsx`), vitest, `RANGE_MATRIX` and `sr2RequestUrls` are not built.
- The backfill, `.agent/SR-11-parity.json` and the 2 s timing are pending.

## Residual risk

- The real grade path and the D-SR.60 premise on real data rest entirely on the pending parity run.
- The `main.py` block will conflict with SR-8's renewable range router, and the second merger resolves it. The packet names this.
