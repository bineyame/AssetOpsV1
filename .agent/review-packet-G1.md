# Review packet: OWN-G1 add-dates (with R5 settle and R6 closing tick / WK-6)

Branch `task/OWN-G1-add-dates`, HEAD at packet time = the commit after `5d7a62039`. Spec: build sheet OWN-GAPS §4, R2-G1,
R3.7/R3.8, R5, R6 (in `AssetOpsV1-plan2/.agent/`). No task file exists for G1 (the build sheet is the task), so no `Status:` to set.
USER_REVIEW_REQUIRED: not stated for G1 in the sheet; this is a demo-tooling slice, needs fresh independent review.

## Outcome

`tools/demo_combined.py add-dates` adds the missing dates per Site (Kobo/Cold/EV days, Kisiwa nights), date-major, then
runs `finish check`. This round added: R5.2 each date is settled (mini-depth worker, then scheduled ticks until every drain
count is 0) before it is called checked; a closing settle for work left by an earlier run; R6.1 one scheduled tick (plus the
Kisiwa `fuel_night` retry) immediately before `finish check`; R6.2 WK-6 selects the study by its last day
(`demo_combined_rows.study_ending`). R5.6: K7 skip-branch count 12 -> 13.

## Commits (this round, on top of phase 1-2: d9540c26c)

776f4fc03 R5.2 settle; 1fb1bb959 R5.3 nine no-DB tests; 8cd2e29b2 R5.6 K7 12->13 (13 `raise KisiwaMissing()` = 13 `@row("KIS-*")`
rows one-to-one); 7bf811898 phase-3 handoff; 6f1e5aaaf R6.1 closing tick + test changes; 5d7a62039 R6.2 `study_ending` + WK-6 + test.

## Files

`tools/demo_combined.py` (settle, settled_date, closing settle, closing tick), `tools/demo_combined_rows.py` (`study_ending`),
`tools/demo_combined_finish.py` (WK-6 only), `backend/tests/test_own_g1_add_dates.py`, `backend/tests/test_k7_kisiwa_story.py`.

## Tests (no DB)

- G1 file: 38 pass. Adjacent 16 files + `host/tests/test_own_g3_entry_env.py`: 434 pass, 4 fail = the pre-existing four
  (mill x2, `ch5c_env_parity`, `ch5c2_clock_guard`; identical on main). K7 now passes. The adjacent set is my own selection
  (non-Postgres demo_combined, ch5c, own_g1/g2/g3, k7); the handoff did not list its 21 files.
- Must-fail proofs (committed first, mutated, reverted by `git checkout`): removing the closing-tick block fails 5 tests incl.
  the "nothing added, nothing pending" test; `max()` in place of `study_ending` fails the WK-6 test; removing `drain_mini` from
  `settle()` failed 3 tests (earlier round).
- Guards: `check-architecture.ps1` passed, `check-agent-workflow.ps1` passed (before the docs edits; re-run after, see below).

## Rehearsal (fresh clone `assetops_demo3_g1audit_test`, work `var/demo3_g1audit`, HEAD tree 5d7a62039; template `assetops_k9_audit_r3u`)

Setup: clone, robocopy without `tree`, `tree` from `git archive` HEAD, then evidence_migration (KOBO-001) and
performance_migration (KOBO-001, KISIWA-001): all "cutover: permitted" (R6.3 recipe).

- **Run A** (`add-dates --site KOBO-001,KISIWA-001,EV-LAB-001 --to 2026-11-08`), wall 2545 s (07:48-08:30 local), exit 0.
  Plan: Kisiwa 2026-11-07, Kobo 2026-11-08 (EV nothing; Kisiwa 11-08 skipped NIGHT_NOT_OVER). `settle-2026-11-07.json`: done,
  1 tick, 87.2 s, 90 mini jobs, no tick failures. `settle-2026-11-08.json`: done, 1 tick, 109.6 s, 34 mini jobs, no tick
  failures. Items: Kisiwa `WITHIN_MARGIN (revision 1)`, Kobo `settled (1 ticks)`, every `tick_failures` empty. Closing
  tick then **finish check 51/51 PASS** (`check-runA.json`); F-THREADS, CO-2, WK-6, KIS-11 pass. The closing tick's seconds
  were not timed separately (it is one scheduled tick plus Performance and pre-build, about 120 s as in the settle drains).
- **Run B** (same command), started 08:41:01, 10 min 31 s after A ended (08:30:28), wall 1364 s, exit 0: nothing added
  (the plan is empty after the delivered-day filter; only the Kisiwa 11-08 NIGHT_NOT_OVER line), counts all 0 so no settle (no
  `settle-close.json`), one closing tick, **finish check 51/51 PASS** (`check-runB.json`). CO-2 passed on a heartbeat that was
  stale (more than 10 min) when the run began, so R6.1 is proven on real wall time.
- `--to` today refusal: not repeated (run-1 evidence stands, `var/demo3_g1audit_run1`).

## Read-only proofs after run B

- Drain `counts`: 0 for every field on all four Sites.
- Kisiwa boards through the app: `night_date 2026-11-07` status 200 `board_faults == []`; next board day 2026-11-08 status 200
  `board_faults == []` (not blocking, recorded).
- EX-2 is met by the F-COH row in `finish check` (`chain_coherence check` with no expectation file), which PASSED in runs A and B;
  F-COH3 proves the row is not vacuous. The standalone run (`collect` 336 requests, all 200, then `check` against the old fixture
  threads file) showed 8 findings: 3 x COH-10 from that fixture's stale thread names (kobo-generator, cold-start-failure,
  ev-interruption) and 5 x COH-2, the known BL-47 entries F-COH allows. G1 adds none, 0 on Kisiwa. (Corrected per review L1.)

## Known deviations / open points

1. EX-2: not identifiable in `chain_coherence` output; reported as "0 new relative to the template baseline, 8 pre-existing". Needs
   a one-line Architect confirmation that this satisfies "EX-2 = 0".
2. R5.3 test order: the sheet lists `add_kisiwa_night` before `_add_core_day`; the code visits Kobo before Kisiwa, so the test
   follows the code.
3. Closing tick seconds not measured separately (above).
4. Tree rebuild on the first clone deleted the file-backed legacy comparison report (R6.3, recipe fix only).
5. Run 1 evidence kept: `var/demo3_g1audit_run1` (check.json 49/51 = CO-2, WK-6 input to R6). That DB was dropped.
6. Process: I wrote scratch scripts under the scratchpad with `Set-Content` once (clone.py); not repo content.

## Residual risk / review focus

- Settle is bounded by `drain`'s failure guards; a drain failure aborts the command with earlier dates in place (append-only).
- Closing tick runs only when the check runs (not under `--no-check`); a live `serve` must be running on demo days.
- Review focus: `settled_date` ordering for Kisiwa dates (drain_mini, tick_and_verify, drain), the `DRAIN FAILED`-only wrapper,
  `study_ending` as the sole WK-6 change, and BL-52 (Kisiwa added-night board row) remaining a backlog item.

Clone kept until review ACCEPT: database `assetops_demo3_g1audit_test`, folder `var/demo3_g1audit`.

## Fix round (review H1)

Code and tests are in commit `cf6c468ce`; the DB rehearsal was not re-run (these paths are covered by no-DB tests).

- **H1.** `plan_add_dates` (Kisiwa) now starts after the last story night or last DONE night, so a PUBLISHED night is planned first and
  resumed (`GAP_NOT_ALLOWED` is measured from the same point). `kis.plan_night` refuses a new night while an earlier PUBLISHED entry
  exists: `NIGHT_NOT_FINISHED`, naming the night and `--from <date>`; it raises before any write. Tests:
  `test_planner_resumes_a_published_night_first`, `test_child_refuses_a_new_night_while_an_earlier_one_is_published`;
  `test_plan_night_refusals_and_resume` updated (chaining is asserted from a DONE night, PUBLISHED refuses).
  Mutations: planner back to `kis.last_night` fails the planner test; `if False and stuck` fails the child test and the updated
  refusals test. Both restored.
- **L2.** `test_wk6_calls_study_ending` (source of `wk6` must call `study_ending`, no `max(`). Mutation: `max(found, ...)` fails it.
- **L3.** On any stop, `add_dates` prints the dates already added and settled. `test_a_stopped_command_prints_the_dates_already_added`.
  Mutation: handler disabled fails it.
- **L4.** The per-date wrapper also matches "mini-depth FAILED". `test_a_mini_depth_failure_in_a_settle_gets_the_drain_wording`.
  Mutation: back to DRAIN FAILED only fails it.
- **L5.** `--dry-run` runs the preflight before printing the plan, so refusals show; no `.busy`, no add, no drain, no tick. The preflight
  child still writes its own log under `<work>/logs` (as on a real run). `test_dry_run_runs_the_preflight_refusals_and_writes_nothing`
  and the updated `test_dry_run_writes_nothing_and_calls_no_child`. Mutation: ignoring the refusal under dry run fails it.
- **L1.** Packet and CODE_STATE wording corrected (EX-2 = F-COH PASS in runs A and B).
- Deviation: the fix and its tests share one file, so H1, L2-L5 are one commit, not one each.
- Checks: G1 + K7 files 143 passed; with the adjacent no-DB set 351 passed, 4 failed (the known mill x2, ch5c_env_parity,
  ch5c2_clock_guard).
