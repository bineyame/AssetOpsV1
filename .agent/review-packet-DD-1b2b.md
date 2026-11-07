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

# Fix round (DD1b2-R13, R14): evidence

Commits: `28bb723d0` (M1, after-tool asserts, L1), `2c2f49e8b` (R14: S-5 and Cold "Why?" asserts). L0s: `test_demo_combined_finish_rows.py` 27 passed, `test_demo_combined_ex1.py` 9 passed (plan2 venv, worktree PYTHONPATH; those files only). Not run: any full suite, prepare, tick, add-day.

**Lineage (L2a).** The first after-tool run used a tree copy that differed from `411817ae8` (top-level import, equivalent). Both reruns below used the committed `2c2f49e8b` `demo_combined_after.py` and `demo_combined_rows.py`, copied into `var/demo3_dd1b2/tree/tools/` and `var/demo3_dd1b2d/tree/tools/` by `run_after_r13.ps1` (scratchpad). Tree form, `ASSETOPS_RESPONSE_STORE=compose` (nothing stored), no DB write. The tool writes `<work>/after.json` (this overwrote the earlier `dd1b2` and the stale `dd1b2d` copies). The first R13 run stopped on two asserts, both ruled in R14.

**Results (exit 0, no failed assert on either run).** Evidence: `var/demo3_dd1b2/after.json`, `var/demo3_dd1b2d/after.json` (S+2 mode, `--ref` the dd1b2 file).

| Item | Result | Evidence |
|---|---|---|
| M1 COH-17 | Narrowed to the L3 shape; eight L0s incl. must-fail cases; no `check` rerun (`allowed_coh17` is `[]`) | `demo_combined_rows.py`, L0s |
| O8 clone half (S+2, `dd1b2d`) | Study OPP-000005 ends 2026-11-07, UNKNOWN, 0 eligible. Thread events unchanged: one RECURRED, effective 2026-10-31, no WITHDRAWN or CLOSED, none on S+2. Assure unchanged on S-5, S-1, S+0, S+1; S+2 reads WATCH, "1 verified result". Portfolio Grow `open_findings` 1 on week, month, week_s2, month_s2. S+2 renewable selections 6 | `dd1b2d` after.json: `o8_*`, `portfolio_grow_counts_mill_thread_open` |
| O12 | S-8 potential "No potential found yet", contributor "Spare solar on 4 of 4 well-observed days". S-5 (R14 §1) potential "Not judged yet: 4 of the 5 study days have no reading", no kW, no money; thread label on S-5 is "Seen again" | `o12_grow_nodes_S-8`, `_S-5` |
| O19 | Closed by statement: "E2 runs `test_demo_combined_postgres` on a TEMPLATE clone of the E3 build, with the DB named by env. On that clone it first runs R12 (c)'s two comparison reruns in the tree form and checks that the Kobo S board reads AVAILABLE. The env var and the fixture branch are written at E2, when they first run (DD1b2-R Q12)." | R13 §2 |
| F-THREADS earnings | 42.08 USD = 168.3 kWh x 0.25 | `check.json` WK-2a |
| F-THREADS ONE-SOURCE | EV WK-1: money null with "0 of 1 day checked" (no money with no checked day). Kobo goes with the next row | `check.json` WK-1 |
| "Why?" price line (S-11) | "42 kWh x 0.25 USD/kWh" equals the stored selection price 0.25 USD; Grow money 10.50 = 42 x 0.25 | `kobo_why_price_line_S-11` |
| Protect "Why?" (R14 §2) | On S's Site-local day it names `aacec8fa`, ACT-000002's thread (text "ACT-002 · Open · linked finding outside this view"). `b13f2110` is not named: recorded as **BL-50 known gap**, not a failure | `cold_protect_why_names_act_002_thread` |
| "Action agreed" ACT-002/003 | Cold ["Action agreed", "Open"], EV ["Action agreed"]; the check is that each Site's Action thread reads "Action agreed" (R14 §3b). The Cold "Open" thread has no Action | `action_agreed_act_002_003` |
| MG-2 line | `check.json` CO-5/SP-1: branch NOT_JUDGED, state UNKNOWN, `MG-2: ["UNKNOWN", "OBJECTIVE_NOT_JUDGED"]` | `check.json` |
| L4 `domain_action_index` | Cold: 1 row on the day, 1 on the week, ACT-000002 present. EV: 1 and 1, ACT-000003 present | `l4_action_index_*` |
| O16 | 11 fuel rows (S-14 4, S-7 4, S+0 3); each on a story day, none on a steady or steady-before day; S-14 and S-7 PRICED, quantity 0 | `o16_fuel_rows` |
| `known_at` links | 4 listed in `known_at_links` | after.json |
| Portfolio landing, Cold and EV | Reported: 17 Portfolio paths name Cold or EV (Site page, evidence, financials, Finding links with from/to/known_at); statement in `portfolio_landing`. DS-1 opens Cold and EV from the story-day links (R9 §1) | after.json |
| L1 | EX-1 exits non-zero on a failed compare or non-AVAILABLE read; `counts` read; any `in_hand` change fails; three L0s | `demo_combined_ex1.py` |
| E3 items | E3.2 reruns this tool on the E3 build (with BL-50 asserting both Cold threads if it merged); E3.3 `check` rerun after the add (CO-2, post-add F-COH); E3.4 browser path; E3.5 `perf_budget --record` naming each NOT MEASURED route | R13 §4 |

**DS-1 lines added by R14.**
- On 28 Oct (S-8): "The day after the change, the mill is checked and working. Spare solar was still seen on the well-observed days; the opportunity's size isn't repeated while the change is being checked."
- On 31 Oct (S-5): "From 31 October the system saw spare solar again, so the opportunity is open again. Only one of its five check days has full readings so far, so it isn't sized yet." S-5's recorded label is "Seen again", so that phrase may be used. Say no kW or money figure on S-5.
- Cold Room: "Explain the failure from the day's board and its Action. Do not open the Protect 'Why?' on the failure day." If a client opens it: it names the earlier cooling problem and says a linked finding is outside the view; that is a known display gap and the board above is complete.

**BL-50** (new, `.agent/backlog-post-demo.md`): the Site "Why?" uses the board's visibility, not Cold/EV's evidence-end cutoff, so a Finding assessed after its evidence ends is missing from it. Not demo-critical; est. 0.25; on the owner's walkthrough list.

**DS-1 source index (R13 §6; lines come from the rulings).** R6 §4 (mill route; R4 "about 96 / about 22", allowed by R11 §3 O14; generator line "about 15 minutes" with no litre figure, R11 §3 O15; "Do not add a Cold or EV day live"; its L6 line is replaced by R14 §1). The add-day line: R6 §3's replacement plus R9 §2's `--assess-now` clause and R11 §2's numbers. Q7 "recurs" lines at `build-sheet-DD-1.md:1561-1564`; "Seen again" stays (R10 §2). R10 §4 (month-start MG-1 line; Depot fault-day income line). R11 §1 (`serve` line). R12 (c) (copy line; E2/E3, not a presenter line).

**Process this round.** No heredocs, sed or redirection into files. Scratch files (`run_after_r13.ps1`, `show_after.py`) are in the session scratchpad. Nothing was written into `.agent` by a tool. Both DBs and work folders are kept.
