# Review packet: DD-1b2b (rehearsal finish, steps 7-9)

Branch `task/DD-1b2-finish-rehearsal`. Rulings: DD1b2-R6..R10 in `.agent/build-sheet-DD-1.md`. Rehearsal state: `.agent/DD-1b2b-rehearsal-handoff.md`.
Kept: DB `assetops_demo3_dd1b2_test` / `var/demo3_dd1b2` (rehearsal), DB `assetops_demo3_dd1b2c_test` / `var/demo3_dd1b2c` (clone with the EX-1 day added). Not pushed.

## Commits (this continuation)
- `8ae1d0814` the 12 failing rows restated per R10 (`tools/demo_combined_finish.py`, `tools/demo_combined_rows.py`) + L0s with must-fail cases.
- `411817ae8` `tools/demo_combined_after.py` (O8, O14, O15), EX-1's S+2 renewable-selection check (`tools/demo_combined_ex1.py`), one L0.
- Copied into `var/demo3_dd1b2/tree/tools/`: `demo_combined_finish.py`, `demo_combined_rows.py` (commit `8ae1d0814`, hashes equal), `demo_combined_after.py` (commit `411817ae8`).
- L0: `backend/tests/test_demo_combined_finish_rows.py`, 21 passed (that file only). Mutation proofs: not run (must-fail cases are in the tests; the index-gap helper was also checked against `days.json`: it returns exactly the served gap set, 10-06, 10-07, 10-09..14, 11-01, 11-03).

## Rerun of `check` (tree form, once; about 12 min; 31 pass, 1 fail)
All 11 R10 rows plus F-COH, F-CAL, F-THREADS now pass (CO-5/SP-1, CO-5/SP-2, CO-6, SP-4, WK-1, WK-2b, WK-2c, WK-4, WK-6, F-COH, F-CAL, F-THREADS). F-COH reads the stored studies (2 headroom occurrences = served count).
**One failure: CO-2** (it passed in the rehearsal). Cause (READ from the error): `/overview` freshness is `STALE_PROJECTION`, reasons `SCHEDULE_STOPPED`, `SITE_VISIT_STALE`; the schedule heartbeat was 1914 s old (threshold 300 s) because nothing has ticked the kept DB since the prepare ended. This is the age of the build, not a product fault; it passes only within minutes of a tick. Not edited. Classed non-product by me, not by the Architect.

## Step 7 measurements (`var/demo3_dd1b2/after.json`)
- Recurrence (O8): studies OPP-000001 (10-17..21, LIMITED, 5), OPP-000002 (ends S-1, UNKNOWN, 1), OPP-000003 (0), OPP-000004 (0). Mill thread: OPEN 10-17, ACTION_IN_HAND 10-26, CHANGE_APPLIED 10-27, RESOLVED_MONITORING 10-27, RECURRED 10-31. Renewable selections: S-3 6, S-1 6, S 7, S+1 7. Boards S-5/S-1/S/S+1 and Portfolio week/month summaries are in the file.
- O14 unused solar: pre (S-13..S-11, 10-23..25) available 374.0, delivered 277.6, unused 96.4, mill 42.0; post (S-8, S-6, S-5) 374.0, 351.6, 22.4, 110.0. Matches 96.4 / 22.4: **yes, "about 96 / about 22" may be quoted.** Source: `accepted_evidence` pv-inverter-controller available-power / ac-power and mill-meter active-power, 5-minute kW x 5/60 per Site-local (UTC+3) day.
- O15 litres: **not recomputable.** No fuel signal reaches evidence on this Site (build-sheet R4: 0 `fuel_level` rows), so litres are not stored. The stored measure is generator kWh: 3.244 kWh on each steady-before night with a run (10-17..21, 10-24, 10-25; 0 on 10-16 and 10-23), which equals the post-fix 3.244 figure. No litre figure goes to DS-1 and no owner litre line is triggered by this read; the DS-1 generator line stays "about 15 minutes" without a litre figure (R8 A fallback).
- `perf_budget --story --report --runs 3`: 0 breaches; every measured route passes (cold <= 525 ms vs 1000, warm p95 <= 113 ms vs 300, bytes within limits); 3 rows NOT MEASURED (snapshot_rebuild, tick_chain_stage_fraction, why_trace), 2 NO_BUDGET.
- O11: prebuild non-200 count 0 (rehearsal logs, 23 requests each time; from the handoff). O10, O13 (browser), O16 fuel-row trace and S-14/S-7 PRICED quantity 0, O17 sampler beyond the handoff: **not done** in this pass.

## Step 8: clone and EX-1 (run at 12:42Z-12:46Z on 2026-11-07, after 11:05Z)
Clone made with `CREATE DATABASE ... TEMPLATE` (0 open sessions) and a folder copy. EX-1: add-day 64.7 s (rc 0, 34 mini jobs), S+2 stored renewable selections after the add and before the tick: 6, `tick --until-drained` 197.0 s wall (tool-reported 89.1 s), 1 tick, N=2, over_n false.
**Boards NOT unchanged** (`comparison.unchanged` false): Assure headline/count/state unchanged on S and S+1 ("1 verified result"); but S `cost_lines` went from [ACT-001] to [ACT-001, "Trial a lower generator stop setting", safeguards line], S gained Finding fcb15cac... (listed twice), S+1 gained the safeguards line. The "before" read shows no Finding on S, although CO-1 saw it on this same data in the rehearsal, so the "before" read may have been taken on a stale projection (the clone also had the stale heartbeat). This is a hypothesis, not measured. Needs the Architect.

## Known deviations / process
- CO-2 failure above (age of the build). EX-1 board change above.
- O10, O13, O16, O17 sampler not done; litres not recomputable.
- Process: one empty `python - <<'EOF'` heredoc was run once by mistake (no file written, nothing mutated). All repo edits used Write/Edit; scratch scripts are in the session scratchpad.
