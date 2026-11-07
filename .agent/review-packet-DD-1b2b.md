# Review packet: DD-1b2b (rehearsal finish, steps 7-9)

Branch `task/DD-1b2-finish-rehearsal`. Rulings: DD1b2-R6..R12 in `.agent/build-sheet-DD-1.md`. Rehearsal state: `.agent/DD-1b2b-rehearsal-handoff.md`. EX-1 results: `.agent/DD-1b2b-rehearsal.json` (two runs; the first is marked "invalid read form (R11 §2)").
Kept until the review verdict: DB `assetops_demo3_dd1b2_test` / `var/demo3_dd1b2` (rehearsal, no tick since the prepare) and DB `assetops_demo3_dd1b2d_test` / `var/demo3_dd1b2d` (EX-1 clone with the EX-1 day added). Dropped: `assetops_demo3_dd1b2c_test` / `var/demo3_dd1b2c`. Not pushed.

## Commits
- `8ae1d0814` the 12 failing rows restated per R10 (`tools/demo_combined_finish.py`, `tools/demo_combined_rows.py`) + L0s with must-fail cases.
- `411817ae8` `tools/demo_combined_after.py` (O8, O14, O15), EX-1's S+2 renewable-selection check, one L0.
- `6f7021d78` B1: `tools/demo_combined_ex1.py` refuses outside the tree form, reruns the S2 comparison, asserts AVAILABLE, compares whole canonical rows plus `read_state` (Findings as a set per row), fails only on R6 O9's items; `backend/tests/test_demo_combined_ex1.py` (6 passed, with must-fail cases).
- `a749fa346` B4 (O18): `EXPECTED_SECONDS` gains `mill` 20 and `drain` 340 (mill 18.7 s; drain 278.4 + 58.3 = 336.7 s, rounded up to 10 s).
- `8f2e164d3`, `b77699390` backlog BL-48 and BL-49 (BL-49 wording per R12 (d)); `b77699390` also adds R12 (a): EX-1 reruns the Performance comparison (Kobo) after S2.
- Copied into `var/demo3_dd1b2/tree/tools/`: `demo_combined_finish.py`, `demo_combined_rows.py` (`8ae1d0814`), `demo_combined_after.py` (`411817ae8`).
- L0: `test_demo_combined_finish_rows.py` 21 passed; `test_demo_combined_ex1.py` 6 passed (those files only, plan2 venv). Mutation proofs: dropped as a separate step (R11 §3); must-fail cases are in the tests.

## `check` rerun (tree form, once; 31 pass, 1 fail)
All 11 R10 rows plus F-COH, F-CAL, F-THREADS pass. One failure, **CO-2**: `/overview` STALE_PROJECTION (schedule heartbeat 1914 s old vs 300 s). Per R11 §1 this is the age of the build (the heartbeat is written only when a tick completes; nothing ticked `dd1b2` after the prepare), not a product fault. It passed at build in the rehearsal's own self-check. Recorded: **passed at build; age-dependent at rerun.** The row is not edited. E3 measures it under `serve` (R11 §1 E3 step).

## Step 7 measurements (`var/demo3_dd1b2/after.json`)
- Recurrence (O8): OPP-000001 (10-17..21, LIMITED, 5), OPP-000002 (ends S-1, UNKNOWN, 1), OPP-000003 (0), OPP-000004 (0). Mill thread: OPEN 10-17, ACTION_IN_HAND 10-26, CHANGE_APPLIED 10-27, RESOLVED_MONITORING 10-27, RECURRED 10-31. Renewable selections: S-3 6, S-1 6, S 7, S+1 7.
- O14 unused solar: pre available 374.0, delivered 277.6, unused 96.4; post 374.0 / 351.6 / 22.4. "about 96 / about 22" may be quoted (closed per R11).
- O15 litres: not recomputable (no fuel signal reaches evidence on this Site); stored generator kWh 3.244 per steady-before night with a run. DS-1 generator line keeps "about 15 minutes" with no litre figure. Closed per R11.
- `perf_budget --story --report --runs 3`: 0 breaches; 3 rows NOT MEASURED, 2 NO_BUDGET.
- **O11 (cites the logs, R11 §3):** `var/demo3_dd1b2/logs/20-prebuild.log`, `29-prebuild.log`, `34-prebuild.log`. Each ends `{"code": "OK", "requests": 23, ... "non_200": {} ...}`: 23 requests, non-200 count 0, in all three.
- **O10 (B2, read-only, `Demo.delivered_days("KOBO-001")` on `dd1b2`; scratch script `o10_o16.py`):** the set has 21 days; every built Kobo day in `days.json` (kind not `missing`) is present (0 absent); S-10 (2026-10-26) is the `missing` day and is absent from the set; S-4 (2026-11-01) is not in `days.json` and is absent; nothing in the set is outside `days.json`. **Pass.** EX-1's add was not refused on it (below).
- **O16 (B3, stored rows plus `check.json`):** `financial_consequence_revision` for KOBO-001 has 11 rows on 3 findings: `8256c653` on 2026-10-22 (S-14, kind overuse), `b37dc42f` on 2026-10-29 (S-7, overuse), `fcb15cac` on 2026-11-05 (S, trial-before). All 11 rows are PRICED, quantity_state AVAILABLE, quantity 0 L, price 1.25, amount 0.00 USD (so S-14 and S-7 are PRICED with quantity 0: not proof of equal non-zero money). Each fuel row traces to a story-day Finding; none sits on a steady or steady-before day. The Cost headline on steady-before 2026-10-17 and on steady 2026-10-28 reads "No fuel cost estimated for this day", no money (MONEY-B pass in `check.json`). WK-2a: 42.08 USD (168.3 kWh x 0.25) pass. Nothing differs from what the owner was told. (Rows repeat per finding window as stored by the consequence store; not investigated further.)
- O13: API stand-in met by MILL-3 (VERIFIED 42.00 -> 110.00) and F-THREADS (R11 §3); the browser click path moves to E3. O17: dropped for step 7 (rehearsal minimum free RAM 3.07 GB, wall 3585 s). O20: items 3, 27, the EV "twice" item and a seeded `delivered_days` L2 are not done, for the reasons in R6.

## Step 8: clone and EX-1 (valid run, 2026-11-07 about 13:15Z)
- First attempt on `dd1b2c` (12:42Z) was an invalid read form (worktree-form reads, and the copy's S2 gate closed): R11 §2. Its board difference was the two gates, not the live add.
- Second attempt on `dd1b2d` stopped before the add: after the S2 rerun S still read PARTIAL (`dispatch` and `chain_findings` closed by the Performance gate bound to the database name). R12 (a) added the Performance rerun (Kobo, after S2).
- **Valid run on `dd1b2d` (tree form):** S2 "Evidence cutover: permitted", Performance "Performance cutover: permitted". `read_state` AVAILABLE on S and S+1, before and after. **Boards unchanged: whole rows identical on S and S+1, diff empty, failures none** (Assure count/headline/state, trial/Action lines, Findings). add-day 58.9 s (rc 0), S+2 stored renewable selections after the add and before the tick: 6, `tick --until-drained` 180.1 s wall, 1 tick, over_n false. The add was not refused (so O10 holds in use).
- **Writes on `dd1b2d` (R12 (b)), declared:** the two comparison reports (S2, Performance) written by the EX-1 reruns, stale `chain_response` rows from the failed read, and the EX-1 add and tick. `dd1b2` itself had no tick or add in this round.

## Lines carried (R11, R12)
- **E2/E3 on any copy (R12 (c)):** "Present only from the database the prepare built, served from its own work folder. On any TEMPLATE clone or copied folder, first run in the tree form `python -m assetops_backend.evidence_migration run --tenant demo --site KOBO-001`, then `python -m assetops_backend.performance_migration run --tenant demo --site KOBO-001`. Then check that the Kobo S board reads `read_state` AVAILABLE before using it. Otherwise every Kobo board reads 'could not be loaded' and Unknown." Applies to E2's copy of the E3 build.
- **DS-1:** "Start the demo with `serve` and wait for 'ready:'. Leave it running the whole time. If a Site page says its figures are being reassessed, wait about two minutes for the next update before showing it." Add-day: "It takes about five minutes on the rehearsal machine (add about 65 s, tick until drained about 200 s)" (this rerun: add 58.9 s, tick 180.1 s); the add changes nothing already on the story-day boards. Also: "Never run `tick --until-drained` after an add made without `--assess-now`."
- **E3 step (R11 §1):** `serve` heartbeat age every 30 s for 15 minutes including the live add; pass if max <= 240 s and never STALE_PROJECTION, else `TICK_EVERY_SECONDS = 60`; also record whether `tick --until-drained` beside `serve` hits a lock timeout (stop and report if so).

## Known deviations / process
- CO-2 recorded as age-dependent. Mutation proofs not run as a separate step (R11).
- Process (this unit): an earlier empty `python - <<` heredoc (no file written); a no-op `sed -i` against `/dev/null` in the previous round (nothing edited). This round: none. All repo edits used Write/Edit; scratch scripts (`run_ex1.ps1`, `run_diag.ps1`, `diag_ex1.py`, `o10_o16.py`, `combine_ex1.py`) are in the session scratchpad, and `combine_ex1.py` wrote `.agent/DD-1b2b-rehearsal.json`.
