# DD-1b2b handoff (steps 1-5 and P0 done; resume at step 6, the rehearsal)

Card: `build-sheet-DD-1.md` "DD1b2-R6", amended by "DD1b2-R7" (Q7 start window and memory rules, Q8 start time), "DD1b2-R8" (C1 non-fatal drain, C2 manifest always written, C4 P0, A the after tool) and "DD1b2-R9" (COH-2, DS-1 clause, step-7 tree form). Pre-flight `.agent/DD-1b2b-preflight.md`. P0 evidence: `.agent/DD-1b2b-p0.json` (read it). Worktree `AssetOpsV1-dd1b2`, branch `task/DD-1b2-finish-rehearsal`. **Code freeze: the prepare archives HEAD (`backend gateway host simulator contracts config contract-fixtures tools`), so nothing in those may change until step 6 starts.** Commit this file before step 6 (`.agent` is not archived). Do not push or merge.

## Rules for this builder

Write/Edit tools only for repo files (no sed, heredoc, `cat >>`, `Set-Content`, `git stash`). Only this unit's `*_test` DBs, host 127.0.0.1:55432; never `assetops_demo3_full_test` or polish DBs. Never pass `-ExecutionPolicy`. Kill by PID only; never stop keep-awake. No other full suite, no `test_demo_combined_postgres`. Never tune numbers. The PowerShell tool's default directory is a stale checkout: give the worktree path explicitly. PYTHONPATH absolute: `backend;contracts;tools;simulator;gateway;host;field` under the worktree. Python `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`. `.agent` files need `git add -f`. Commits end `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. (The scratchpad `mkdb.py` only accepts names starting `assetops_dd1b2`; the prepare itself drops and recreates `assetops_demo3_dd1b2_test` at its start.)

## What exists (commits)

| Step | Commit |
|---|---|
| O1 link fix | `44919e51f` |
| O2/O3 drain, cap, timings | `83f4926b6` |
| O7 text | `d43340006` |
| Finish rows, `--story`, EX-1 tool, L0s | `d2f53caa0` |
| Stale-test fixes | `d837b539c` |
| R8 B fixes, C1 non-fatal drain, C2 manifest in `finally`, L0s | `78f3b1c7f` |
| P0 day list | `f4454f2d5` |
| R9 COH-2 named expectation (`coh_split`, `recorded_action_ids`), L0 with 3 non-vacuity mutations | `2002db962` (after `b44c0f01b`); BL-47 `c02e12407` |
| P0 results | `3280dbb80` |

Detail of the step-4 rows (F-DRAIN, F-COH, F-COH3, F-CAL, MILL-3, F-THREADS, WK-2c, MONEY-B, WK-2b), `perf_budget --story` and `demo_combined_ex1.py` is in the earlier handoff (git history, `9faf45ce4`) and the commits above.

## What P0 proved (MEASURED; `.agent/DD-1b2b-p0.json`)

- A 6-day partial prepare (`--sites kobo,cold,ev --no-finish`) ran in 226 s, exit 0 (Kobo 193 s, Cold 11.5 s, EV 11.8 s).
- The real `Demo.drain` with real tick and `counts` children works: snapshots 10150 -> 0 in tick 1, every tick exit 0. The first `tick --until-drained` failed "past 2N" only because `--no-finish` skips `drain_mini` (Kobo `mini_deferred` 570). After `drain_mini` it drained in 1 tick (N=2, 62 s). The rehearsal prepare runs `drain_mini()` before each drain (R9 section 2), so this does not recur there.
- `check` in the tree form: 17 pass, 15 fail on P0's thin data. Every failure was classed as absent data from the error text (no `drain-1.json`, no `mill.json`, S-21/Cold S-7/MG-1 not in P0, no objective, empty window); that classification is READ, not traced row by row. COH-2 was the only tool-side finding.
- B1: before the S2 comparison every Kobo board read PARTIAL / PRODUCER_NOT_SETTLED and was flagged; after, all 10 story boards AVAILABLE.
- EX-1 on the P0 DB at 11:06Z: add-day 31.9 s, drain 84.0 s, 1 tick, boards unchanged, 125 s total.
- F-COH with the R9 expectation: COH-2 allowed on Cold (week, S, month) and EV (week, month), 5 entries, nothing else; F-COH3 still fires COH-10.

## What P0 did not prove

`perf_budget --story`; the mill step's place in the drain order; F-THREADS; MILL-3; full-list values; timings; the deferred-drain self-check path (L0 only); and the CO-5/SP, WK-1/2a/2b/4/6, CO-6/11 rows on full data (absent data on P0; first real run is the rehearsal).

## Step 6 (rehearsal)

- `python tools/demo_combined.py --db assetops_demo3_dd1b2_test --work var/demo3_dd1b2 prepare --cap-seconds 10800`, no `--days`, no `--sites`. Never prepare twice; a mill-step failure means stop and report (a rerun needs the owner). A self-check or drain failure is not a lost run (R8 C1-C3): the DB and work folder stay, `check` is rerun after a fix.
- **Start window (R7 Q8):** by 17:30Z today, else the next morning at or after 05:00Z (S moves a day, harmless).
- **Start condition (R7 Q7):** no other check-all, pytest, prepare or build running (process list, PIDs into the packet) and free RAM >= 2.5 GB for 2 minutes. During the run, free RAM under 2 GB is recorded (minimum, duration, step), not a stop. **Stop** only if free RAM < 1 GB on two consecutive 30 s samples, or the stall monitor sees no child/tick output for 15 min. Sampler: a scratchpad script every 30 s (free RAM, python working sets, `docker stats`). Keep-awake is already running; never stop it. Kill by PID only.
- Over 10800 s: the B-16 projection goes to the owner. Stops per R6 section 7: R8 past 2N or two flat ticks or the same stuck ids; a COH finding other than the named COH-17 and the named COH-2 below; prebuild non-200 for COLD/EV; MILL-3 differing from 42.00 -> 110.00 or outcome count not 1. A FAILED tick other than a stage TIMEOUT is a stop back to the Architect, DB kept; list every FAILED tick in the packet.
- **COH-2 expectation (R9 item 1):** F-COH allows COH-2 only on COLD-LAB-001 / EV-LAB-001 when the evidence is `action_index.<that Site>` and the Action id is recorded. Cold's Action id is not in `cold.json`; it is in `cold-replay-*/**/positive.json` (`fixture.action.id`), which `demo_combined_finish.f_coh` reads as well (a declared deviation from R9's "cold.json/ev.json"). COH-2 on Kobo, or on any other Action, is a fault. Reason text: "Portfolio does not join domain-Site Actions (estate/index.py:193); known, DS-1 covers it; BL-47". The allowed entries appear in F-COH's `allowed_coh2`; list them in the packet.
- **DS-1 clause (R9 item 2):** add "Never run `tick --until-drained` after an add made without `--assess-now`."

## Step 7 (reads after the prepare)

**Every served read runs in the tree form** (R9 item 3; the worktree form lacks `tree/var/sites/kobo-001.yaml` and gives false 409s on CO-2, SP-4, WK-6):

- cwd `var/demo3_dd1b2/tree/backend/tests`
- `PYTHONPATH` = the tree's nine parts: `backend, backend/tests, contracts, gateway, simulator, host, host/tests, gateway/tests, tools`, each under `var/demo3_dd1b2/tree` (`demo_combined.py:297-299`)
- `DATABASE_URL` and `ASSETOPS_TEST_DATABASE_URL` = the build's URL (`postgresql+psycopg://assetops:<pw>@127.0.0.1:55432/assetops_demo3_dd1b2_test`; drop `ASSETOPS_TEST_RUN_ID` and `ASSETOPS_TEST_DATABASE_BASE_URL`)
- the tool path inside the tree: `tree/tools/demo_combined_finish.py check <url> <work>`

So the `check` rerun is `tree/tools/demo_combined_finish.py check <url> <work>` with that env and cwd, not `python tools/demo_combined_finish.py ...` from the worktree. The same form applies to `perf_budget --story` (`tree/tools/checks/perf_budget.py --database-url <url> --work var/demo3_dd1b2 --story var/demo3_dd1b2/story.json --report --runs 3`), the O8/O10/O11 reads, and the after tool. A tool fixed in step 7 is committed in the worktree, then copied into `tree/tools/`; the packet names each copied file and its commit. Never copy backend code into the tree; a backend fault is an R6 section 7 stop. P0 copied the two R9 files into its tree this way.

**Still owed (R8 A), not built:** `tools/demo_combined_after.py` (O14 unused-solar recompute, O15 litre recompute, O16 fuel-row trace and S-14/S-7 PRICED quantity 0, the F-THREADS recomputes and the other listed items; reads only, none added to `CHECKS`). It may be written while the rehearsal runs (the prepare archived HEAD at its start); its L0 runs after the prepare ends. Without it, DS-1 loses "about 96 / about 22" and the litre figure (R8 A fallbacks).

## Step 8 (clone and EX-1)

- Clone `dd1b2` by `TEMPLATE` into another own `*_test` DB and work folder, then run EX-1.
- **Owed before step 8 (R8 A):** EX-1 must check that S+2's renewable selections exist (stored-row count of S+2's PV hours) between the add and the first tick, in `tools/demo_combined_ex1.py`. Edit it only after the prepare has started (the rehearsal tree is already archived), with an L0, and commit before step 8.
- **EX-1 invocation (MEASURED in P0):** run `tools/demo_combined_ex1.py` from the *worktree* (not `tree/tools`: from the tree, `demo_combined.py`'s REPO is the tree and `--work` is refused, `demo_combined.py:287-290`) with the tree environment above (cwd `<clone work>/tree/backend/tests`) and `--db <clone db> --work <clone work>`.
- **Time:** S+2's day ends after 11:00Z, but `add-day` refuses until DB now minus 5 minutes is past that end, so start EX-1 at or after 11:05Z on S+2 (P0: refused at 11:00:52Z with DAY_NOT_IN_PAST, ran at 11:06Z).
- EX-1 adds one assessed day (about 32 s), drains (about 84 s, 1 tick), and compares boards.

## Step 9

O18 and the packet as in R6 sections 6 and 8. Keep `dd1b2` and the clone until the review verdict.

## Open question

COH-2 is resolved by DD1b2-R9 (named expectation; BL-47 in `.agent/backlog-post-demo.md`); no product change. A COH-2 outside the allowed shape (Kobo, estate-index source, an unrecorded Action) is a fault.

## Process notes

P0's first two EX-1 attempts were not tool faults (invocation form; the 5-minute margin). Shell-rule slips this session: scratch runner scripts were written through a heredoc, and the mutation proofs on `tools/demo_combined_rows.py` through a python heredoc (reverted with `git checkout` after committing); no kept repo edit was made that way. P0's DB `assetops_demo3_dd1b2t_test` and `var/demo3_dd1b2t` were dropped and deleted at the end (confirmed by query).
