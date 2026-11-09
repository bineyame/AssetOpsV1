# Review: OWN-G1 add-dates (first independent review)

Reviewer: Claude (fresh, not the author). Branch `task/OWN-G1-add-dates`, worktree `AssetOpsV1-g1`, HEAD `a7d87479d`,
base main `b73c65eb6` (merged at `3609ed5a2`). Spec read from `AssetOpsV1-plan2/.agent/build-sheet-OWN-GAPS-2026-11-08.md`
§4, R2-G1, R3, R5 and R6 (R5 and R6 in full). Packet `.agent/review-packet-G1.md`; handoffs phase 1-3.

## Verdict: REJECT (one High; small fix on the branch)

The settle, the closing tick, the Kisiwa retry, `study_ending`, the K7 count and the refusal paths are correct. The
rehearsal evidence on disk and in the clone matches the packet. There is no product code change. One High finding
blocks: the specified Kisiwa resume path (§4.5 step 9, R2-G1 Q2) cannot be reached by a default re-run. A night left
`PUBLISHED` is silently stepped over, and later nights are chained on top of it. That breaks the owner's standard of
honest refusals and no false "checked" claims. The fix is small and needs only no-DB proof.

## Findings

### H1 (High, acceptance gap): a PUBLISHED Kisiwa night is never resumed by a default run; the next night is added on top of it

- `tools/demo_combined.py:420-433` (`plan_add_dates`, Kisiwa branch). `last = kis.last_night(...)` counts both `DONE` and
  `PUBLISHED` entries (`tools/demo_combined_kisiwa.py` `last_night`), and the default start is `lo = date_from or last + 1`.
  So a night left `PUBLISHED` is never in the default plan. The child's `plan_night` for the following night then
  passes `NOT_NEXT_NIGHT`, because its `nxt` also counts `PUBLISHED`, and it chains `start_state` from the unverified night.
- Reproduced without a DB, using the test file's own `plan()` helper and an entry
  `{"night_date": "2026-11-07", "status": "PUBLISHED"}`:
  - default plan: `['2026-11-08', '2026-11-09', '2026-11-10', '2026-11-11']`, with nothing skipped and no message;
  - with explicit `--from 2026-11-07`: `['2026-11-07', ...]`, so the resume works only if the owner knows to type it.
- How a night is left `PUBLISHED`:
  - (a) a crash or Ctrl-C after step 4 and before step 5. The night's tank dips were never posted, and that data is now
    lost without any message.
  - (b) a crash between the child `add-day` and `verify-day`, which is the case R2-G1 Q2 says "Resume covers".
  - (c) most importantly, `ADD_NIGHT_UNEXPECTED`: `verify-day` does not mark the night DONE, so it stays `PUBLISHED`.
    On the next default run that night is stepped over. The new nights then print "checked: within margin",
    `links` lists the bad night as an "added night", and `finish check` passes, because the KIS rows are story-bounded
    and the added-night board row is BL-52. A night the tool once refused would end up in a build that passes its checks.
- Why it matters: the owner asked for a real mechanism that "can automatically update". An unattended re-run is that
  mechanism. It must finish or refuse a part-done night. It must not route around one.
- Tests: `test_plan_night_refusals_and_resume` covers `plan_night` with a `PUBLISHED` entry, but no test covers the
  planner, which is the only way a default run reaches it.
- Fix:
  1. In `plan_add_dates`, start Kisiwa's default range at the earliest `PUBLISHED` entry when one exists, or more
     simply at (last story night or last `DONE` night) + 1. Its existing `PUBLISHED` handling then routes it to
     resume. Keep `GAP_NOT_ALLOWED` measured from that same point.
  2. Defence in depth in the child: `plan_night` refuses a new night while an earlier `PUBLISHED` entry exists, for
     example with `NOT_NEXT_NIGHT` "finish {d} first".
  3. Add a no-DB test: a `PUBLISHED` 11-07 entry makes the default plan start at 11-07, and the child refuses 11-08
     while 11-07 is `PUBLISHED`. A must-fail check: the current code fails the first assertion.

  Re-verifying a night that is still bad then raises `ADD_NIGHT_UNEXPECTED` again. That is the honest outcome.

### L1 (Low, packet accuracy): "EX-2 = 0" is met, by F-COH, not by "0 new against the template"

- EX-2 is defined at `.agent/build-sheet-DD-1.md` R10 and `.agent/architect-combined-pass-2026-11-08.md:416`: run
  `chain_coherence check` with no expectation file. In `finish check` this is the **F-COH** row
  (`tools/demo_combined_finish.py:761-780`). That row runs the check with no `--expect`, on threads generated from this
  build, and allows only the known COH-2 entries (BL-47) and the recurring mill COH-17. **F-COH passed in both run A
  and run B** (`var/demo3_g1audit/check-runA.json`, `check-runB.json`). F-COH3, which proves the check is not vacuous,
  passed too. So the requirement is met.
- Where the builder's 8 findings come from:
  - The 3 COH-10 findings come from running `check` standalone against `THREADS_FILE`, which holds polish-build UUIDs.
    Their thread names `kobo-generator`, `cold-start-failure` and `ev-interruption` are the names in
    `tools/checks/fixtures/chain_coherence/expected-threads.json`. `.agent/DD-1b2-preflight.md:132` already records that
    this file fails COH-10 on any fresh build.
  - The 5 COH-2 findings are the BL-47 entries that F-COH lists under `allowed_coh2`.
  - None of them is a defect caused by G1, and none of them is a new end-game defect.
- Fix: in the packet and in the `CODE_STATE` "Open" line, replace "needs Architect confirmation" with "EX-2 = F-COH PASS
  in runs A and B". No Architect question is needed.

### L2 (Low): WK-6's use of `study_ending` has no no-DB guard

- The R6.2 must-fail test exercises the helper. If `wk6` went back to `max()`, no no-DB test would fail. Run A and run B
  are the only proof.
- Optional: a source assertion that `wk6` calls `demo_rows.study_ending`, or a fake-context test.

### L3 (Low): a stopped command does not print what it already added

- `add_dates` builds the summary and plain lines only after the loop (`tools/demo_combined.py`, the end of `add_dates`).
  A refusal partway through, such as a drain failure, `ADD_NIGHT_UNEXPECTED` or a per-night child refusal, prints only
  the error, even though earlier dates were added and settled. The process is append-only, so the owner should still be
  told what is now in the build.
- Fix: print the partial `added` and skipped lines before the exception propagates.

### L4 (Low): a mini-depth failure inside a settle is not given the R5.2 item 5 wording

- The per-date wrapper rewrites only messages that start with "DRAIN FAILED". A `drain_mini` failure ("mini-depth
  FAILED: …") raised inside `settle` or `settled_date` passes through unprefixed. It still stops the command, and
  `.busy` is still removed.
- Fix: also match "mini-depth FAILED".

### L5 (Low, spec tension): `--dry-run` does not show the preflight refusals

- §4.2 says `--dry-run` prints "the plan and the refusals". §4.7 and R5.3 test 9 say it makes no call. The code
  follows §4.7, so `BUILD_TOO_OLD`, `FUEL_STAGE_MISSING` and `ENTRY_DISABLED` appear only on a real run. The preflight
  writes nothing except its log, so running it under `--dry-run` would be safe.
- This is for the Architect to decide; it does not block.

## Focus items, judged

- **`settle` and `settled_date`**: match R5.2.
  - Kobo-only dates run `drain_mini` then `drain("settle-<d>")`, with no separate tick.
  - Kisiwa dates run `drain_mini`, then `tick_and_verify` (tick, then `verify-day`, with up to 2 retries 30 s apart),
    then `drain`.
  - `checked` becomes "settled (n ticks)" only after `drain` returns `done`. `tick_failures` comes from `record["log"]`.
- **Closing settle**: runs when `dr.total(counts) > 0`. `total` includes `mini_deferred` (`FIELDS` in
  `demo_combined_drain.py:14`). It runs under `--no-check` too.
- **Closing tick (R6.1)**: one `tick()`, then `retry_until_visited` when Kisiwa is in the build, immediately before
  `finish_check`. It does not run under `--no-check`. It rewrites `last-tick.json`; on disk that file has a KISIWA-001
  `fuel_night` entry with code OK.
- **`study_ending`**: it requires exactly one study whose last day matches, which is stricter than `max()`. No
  assertion on the content changed (`scenario_id`, the mill study and the tariff checks are untouched). This keeps WK-6
  strict and stays inside R6.2.
- **K7 count**: 13 `raise KisiwaMissing()`, matching the 13 `@row("KIS-*")` rows (KIS-1, 2, 3, 4, 5, 6, 7, 8, 8a, 9, 10,
  11, OV), counted myself. The comment names KIS-11 (OWN-G2). The test is still strict.
- **KIS bounds (R2-G1 Q3)**: KIS-1 windows, KIS-2 dispatch and `_kisiwa_read` records are bounded to the story calendar,
  as the pre-flight Q3 analysis set out and the ruling broadened. All three are covered by the no-DB test with one
  added night. Residual risk: a dispatch (mini_grid) Finding on an added night is now seen by no check. `verify-day`
  checks only fuel_balance Findings, and BL-52 is backlog. See the residual risks below.
- **Refusals write nothing**:
  - The planner's refusals (`DATE_NOT_PAST`, `STORY_DAY`, `GAP_NOT_ALLOWED`, `DATE_TOO_OLD`, `FROM_AFTER_TO`,
    `KIND_NEEDS_ONE_DATE`, `SITE_NOT_IN_BUILD`) all raise before any child, any `.busy` and any file write. The
    phase-2 handoff records unchanged file hashes and table counts after `DATE_NOT_PAST`.
  - The preflight refusals come after one child that posts an invalid body (422) and writes only its log under
    `<work>/logs`.
  - `--dry-run` calls nothing and writes nothing (tested).
- **`.busy`**:
  - It is checked before anything runs and then taken with `O_EXCL` (`hold_busy`), so a race is still refused.
  - It is removed in `finally` on every path, including a drain failure (tested) and a failed check, where it is
    removed before the `SystemExit`.
  - A Kisiwa `add-day` routes through `add_dates`, so `.busy` is taken once. A core `add-day` now takes `.busy` around
    `_add_core_day`.
- **Failure messages**: drain failures carry the R5.2 prefix and suffix (tested). L4 is the one gap.
- **Must-fail guards**: the R5.3 and R6.1 loop tests assert exact call lists. Removing the settle, the closing tick or
  `drain_mini` would fail them, as the packet's mutation notes and my reading of the code agree. The `study_ending` test
  fails with `max()`. Missing guards: H1's planner resume, and L2.
- **Product code**: `git diff --stat b73c65eb6..HEAD -- backend/assetops_backend host frontend` is empty. No product
  change.
- **Same paths as live data**:
  - Readings go through `rp._publish_and_accept`, received at DB now.
  - Records go through the G3a entry route; the clone shows REC-000029/30 written by `service:operator-entry`, with
    `oprec-entry-` keys.
  - The fuel window comes from the product's own `fuel_night` stage; the clone shows 11-07 revision 1 `WITHIN_MARGIN`.
  - Nothing in the product is special-cased.

## Evidence I checked (read-only)

- `var/demo3_g1audit/check-runA.json` and `check-runB.json`: 51 of 51 pass. F-THREADS, CO-2, WK-6, KIS-11, F-COH and
  F-COH3 all pass.
- `var/demo3_g1audit_run1/check.json`: 49 of 51 (CO-2 and WK-6 fail), the input to R6.
- `settle-2026-11-07.json`: done, 1 tick, 87.2 s, no tick failures, ending total 0.
- `settle-2026-11-08.json`: done, 1 tick, 109.6 s, no tick failures, ending total 0.
- `kisiwa-days.json`: 2026-11-07 DONE, normal, window revision 1 `WITHIN_MARGIN`, REC-000029/30. The fuel chain is
  continuous: the last story dip was 446 L and the first added dip is 446 L.
- DB `assetops_demo3_g1audit_test`, in a session with `default_transaction_read_only=on`:
  - `recompute_job` is all DONE (2665);
  - `fuel_balance_window` for 11-04 to 11-07 is revision 1 `WITHIN_MARGIN` with no limitations;
  - no `finding_revision` exists with an episode on an added night (the only recent revisions are the template's
    October dispatch Findings).
- CODE_STATE (process slip 2): the appended "OWN-G1" section is accurate apart from L1's wording. The committed blob
  is LF and valid UTF-8 (`§` is encoded correctly). The heredoc did no damage. The `Set-Content` scratch script was in the
  scratchpad and is not repo content.

## Checks I ran

- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- `pytest tests/test_own_g1_add_dates.py tests/test_k7_kisiwa_story.py` (plan2 `.venv`, PYTHONPATH as in the phase-1
  handoff): 137 passed.
- Adjacent no-DB files: `test_demo_combined_ex1`, `test_demo_combined_finish_co1`, `test_demo_combined_finish_days`,
  `test_demo_combined_finish_rows`, `test_demo_combined_links`, `test_demo_combined_mill`, `test_demo_story_days` and
  `test_k1_kisiwa_fixtures`. Result: 200 passed and 2 failed, the 2 being `test_demo_combined_mill` x2. Both fail the
  same way on main (`AssetOpsV1-plan2` at `d7b38bf23`: 13 passed, 2 failed).
- Not run, as the brief says: Postgres suites, the full backend suite, the rehearsal, the G2/G3 no-DB files,
  `test_ch5c*`, and the frontend. G1 changes no frontend code.

## Residual risks the packet does not name

- The rehearsal covered only Kobo and Kisiwa `normal`:
  - no Cold date (Cold is not in the specified command);
  - no EV Tuesday (the next Tuesday was 11-10, after the run);
  - no Kisiwa `delivery` night (the tank started at about 446 L, above 250 L).

  The owner wants "any Site". The Cold and EV per-date paths and the delivery path, including
  `DELIVERY_RECORDED_LATE` passing verify, are proven by no-DB tests only.
- `tick_failures` covers only the date's `drain` record. Failures in a Kisiwa date's first tick (inside
  `tick_and_verify`), in the `settle-close` drain and in the closing tick are not attached to any item. `finish check`
  is then the only judge.
- With the KIS rows story-bounded and BL-52 in the backlog, nothing checks an added Kisiwa night for a dispatch Finding
  or for board faults. `verify-day` checks fuel_balance only. This is acceptable for the demo under R5.4, and H1 makes
  the gap more serious until it is fixed.
