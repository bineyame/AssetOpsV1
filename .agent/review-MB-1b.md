# Review MB-1b: the mill's thread line on the Kobo board's Grow row

- Reviewer: fresh Claude (Opus), independent first review. I did not write this work.
- Branch `task/FUEL-MB1b-mill-thread-line`, worktree `AssetOpsV1-mb1b`, HEAD `8ebaf59d0` (build `132e2f9c8` + main/PV-1 merge `5220ad13a` + packet commits).
- Diff: `git diff main...HEAD` (merge base `393e608b8`): 6 files, +504/-8.
- Spec: `.agent/build-sheet-FUEL-1.md` MB-1-R §1 Q2/Q3/Q6 and §3 (the MB-1b card), MB-1a-R2 §1.

## Verdict: FIX (one Medium, fixed on the branch; then ACCEPT without a re-review of the code)

The code is correct against the card. It uses the three literals verbatim, computes k with the runner's own rule, applies the omission rules, keeps byte-equality, and merges cleanly with PV-1. The one Medium is about the E3 proof. MILL-4 cannot detect the cutoff leak the card is meant to prevent, and the packet claims E3 proves k when it does not.

## Findings

### M1 (Medium): MILL-4 would pass a future-dated line or a wrong k at E3, and the packet says it proves them

- **Where.** `tools/demo_combined_finish.py:868-880` (`mill_thread_line`), `:876` (kind check), `:883-891` (`mill4`). The packet claim is at `.agent/review-packet-MB-1b.md:86`.
- **What is wrong.**
  - `mill_thread_line` checks four things:
    - exactly one line;
    - kind ∈ {MONITORING, CLOSED, RECURRED};
    - the text is self-consistent with the item's own fields;
    - ref = THREAD.
  - It never compares the line with the board day it was read for.
  - The packet (residual risk) says "the real `k` for S-8 and whether the 10-31 recurrence is a visible started occurrence ... are only proven at E3 (MILL-4)". MILL-4 proves neither. Any k from 0 to 7 that matches its own `remaining_days` passes.
- **Failure scenario.** On real rows, suppose the "started by the board day" selection or the segment logic misbehaves: say the S-8 board picks the 10-31 occurrence.
  - The S-8 Grow row would then read "Spare solar seen again on 31 Oct after the change (ACT-002)" on a board dated about 28 Oct. That is a future-dated line, a client-visible leak past the cutoff.
  - MILL-4 passes it: the kind is in the allowed set, the text matches `effective_day`, the ref is THREAD.
  - F-THREADS only reports the kind.
  - The same holds for a wrong k on S-8, for example S-i, where `day_facts.rows` misses a day the runner counted. It renders "7 more" instead of "6 more" and passes.
  - E3 is the only real-row check of this line: no Postgres test reads `thread_lines` for the mill (grep). So the first time anyone sees it is the demo build.
- **Fix (small, no typed expectation).** In `mill_thread_line`, take the board day (`board["day"]`, or pass `ctx.day(n)`) and assert:
  - when present, `effective_day <= board day`, which applies to RECURRED;
  - for MONITORING, `0 <= remaining_days <= close_after`. (The item carries no `close_after`, so assert `remaining_days <= 7` from the policy, or skip.)
  - Add one self-test fail case: a RECURRED item whose `effective_day` is after the body's day.
  - Optional, an Architect call because it goes beyond the card's "kind in three": pin the S-8 kind to MONITORING. The ruling's table states that S-8 is MONITORING unconditionally (verified S-9, recurrence 10-31).
  - Correct packet line 86 to: MILL-4 proves the line exists, its kind, its text-field consistency and its ref. k's correctness rests on the L0 parity (same function, same inputs) and on `day_facts.rows` holding every `daylight_headroom_kw` day the runner counted. E3 does not check the latter.

### L1 (Low): no test distinguishes the policy's `close_after` from a hard-coded 7

- **Where.** `backend/tests/test_mb1_thread_line.py:32`; code at `backend/assetops_backend/site_outcomes/mini.py:605`.
- **Problem.** `POLICY` has default 7 and empty `by_site_type`, and every compose test expects 7. Two mutations would pass the suite:
  - replacing `ct.policy.close_after(SITE_TYPE_OF_DOMAIN[MINI])` with `7`;
  - passing `MINI` ("mini_grid") instead of "MINIGRID", which silently falls back to the default.
- **Why it matters.** Today the policy's value is 7 (`config/chain/thread-lifecycle-v1.json`), so no on-screen error now. It is a test-strength gap for "k is computed, never typed".
- **Fix.** One compose case with `LifecyclePolicy(..., {"MINIGRID": 5}, ...)` asserting `remaining_days == 5 - checked`.

## Checks against the dispatch

1. **Literals.**
   - `board.py:77-79` are byte-for-byte the card's §3.2 text, with the card's two comment lines.
   - BEFORE_CHANGE is bare `THREAD_BEFORE`, as the card rules.
   - The shown code is `display_code(o.code)` ("ACT-002"). That matches Finding thread lines (`thread_line_item` uses `display_code(a.code)`), PV-1's `VALUE_LINE_MILL` ("ACT-002") and the card's §3.3 rule.
   - `action_code` on the item stays the stored "ACT-000002". MILL-4 compares it with `mill.json`'s stored `action_code` (`demo_combined_mill.py:179`), so it is consistent.
   - The card's expected-view table writes "(ACT-000002)". That is a typo in the card, contradicted by its own §3.3. It is not a code issue.
2. **k computed.** `mini.opportunity_thread` follows the card's §3.3 steps 1-7.
   - **P1 (effective day).** MONITORING and CLOSED take the change day, RECURRED takes `recurred_day`. This is identical to `thread_line_item`.
   - **P2 (starts).** `starts` holds every visible occurrence's local start day: the runner's rule (`lifecycle_run.thread_clean_days`) and the Finding lookup's rule (`postgres_thread_sources.py:281-293`). Later starts only remove days after the board day, and `thread_view` counts only `since < d <= day`, so they cannot change k.
   - **Same counting.** `thread_view`'s `checked` (days > the last RESOLVED_MONITORING day, ≤ day) matches `plan_lifecycle.maybe_close` (`d > h.effective_day`).
   - **Same rows.** The board's rows (`ChainRequest.day` → `snapshots.latest`, latest revision per day) are the same shape as the runner's `_SNAPSHOTS` (DISTINCT ON … revision DESC).
   - **Measure in the read.** `daylight_headroom_kw` is a MINIGRID SITE measure (`chain/measures.py:49`), so it is in the board's `chain_day` measure set.
   - **Close-after site type.** `SITE_TYPE_OF_DOMAIN[MINI]` = "MINIGRID", the runner's site-type key.
   - **Real-row keys.** The occurrence keys used (`mechanism`, `subject_ref`, `opportunity_id`, `finding_id`, `occurrence_no`, `episode_start`) exist on the real `_SITE_OCCURRENCES` read (`postgres_chain_read.py:67-77`).
3. **Omission rules.**
   - **No policy:** no view and no line; a test pins it.
   - **Verified day before the window:** `count_known` False removes MONITORING only. CLOSED and RECURRED need no count, as the card rules. A test pins it.
   - **Action in the recurred segment:** None; a parametrised case pins it.
   - **Recurrence after the board day:**
     - excluded by `episode_start < end`;
     - `state_on` and the verified-day filter are bounded by `day`;
     - `actions_of` uses `segment_on(accepted_day)`.
     - With k None ("as known now") all events are visible, but none is used past the day. `test_s8_shape_...` pins it.
4. **Byte-equality.**
   - `_line_item` has the same keys, order and values; `thread_line_item` delegates with the same arguments.
   - `test_ch3_rows.py` passes, and so does `test_out_b3_cold_ev.py`, which is unchanged.
   - The new test compares Optimize, Protect and Assure with and without the line. It compares Optimize and Protect, and Grow minus `thread_lines`/`subline`, against a board with no mill.
   - Opportunity threads have no FindingFacts, so `thread_line_findings` cannot emit a second, Finding-worded line for the mill.
5. **Checks.**
   - MILL-4 and the F-THREADS `mill_line_s8` follow the card's wording, and the self-test has 3 passing and 8 failing bodies.
   - Gap: M1.
6. **Wording and labels.**
   - MD-FUEL-MB1-2 appears in the `opportunity_line_item` docstring, in the `_row` comment, and in the packet's deviation row.
   - "Change checked and working", "spare solar not seen again" and "Spare solar seen again on … after the change" read as a change to use spare solar, not as a fault fix.
   - `test_out_b2_vocabulary.py` (guards V/N) passes.
7. **PV-1 merge.** Merge `5220ad13a` (parents `132e2f9c8`, `393e608b8`).
   - The +/- lines of `diff(393e608b8, HEAD)` over backend/tools equal MB-1b's own build diff from its base `da51c7a8a`.
   - The lines of `diff(132e2f9c8, HEAD)` over backend/tools/frontend equal PV-1's side from the same base.
   - Nothing was lost on either side. PV-1's tests pass on HEAD.
8. **Test strength.** These mutations are caught:
   - dropping the started filter (S-8 test);
   - wrong starts (parity test);
   - dropping `count_known` (window test);
   - dropping the policy guard (AttributeError, so the no-policy test fails);
   - `<=` in place of `<` on the segment (no-line case).
   This one is not caught: a hard-coded or wrong-site-type `close_after` (L1).
9. **Main-branch failure.** `test_ch1a_grading.py::test_period_bounds_addis_utc_tue_only_and_24h` fails with `ValueError: unknown period 'midday'` on a `git archive main` snapshot run in scratch (1 failed, 24 passed). `chain/grading.py`, `chain/policy.py`, `config/chain` and the test are untouched by `main...HEAD`. It is not caused by MB-1b.

## Checks run (by me, HEAD `8ebaf59d0`)

- **Python.** `AssetOpsV1-plan2\.venv`, with PYTHONPATH absolute under the worktree. `assetops_backend`, `assetops_contracts` and `demo_combined_finish` resolve into `AssetOpsV1-mb1b`. Free RAM was 4.1 GB.
- **First L0 run: 1 failed, 401 passed (23 s).** The only failure is the main-branch grading test above. Files:
  - `test_mb1_thread_line.py`, `test_ch3_rows.py`, `test_out_b2_mini.py`, `test_out_b3_cold_ev.py`, `test_out_b2_vocabulary.py`;
  - `test_mb1_opportunity_board.py`, `test_demo_combined_finish_rows.py`, `test_ch5a2_contract.py`;
  - `tools/checks/test_chain_coherence.py`, `test_ch1a_grading.py`.
- **Second L0 run: 54 passed.** Files: `test_pv1_value_lines.py`, `test_out_b4_imports.py`, `test_ch5a1_board_contract.py`, `test_demo_combined_finish_co1.py`, `test_ch9b1_origin_readers.py`.
- **Main snapshot.** `test_ch1a_grading.py` on main: the same failure.
- **Postgres.** Not run by me. The builder's 26 passed on `assetops_mb1b_test` are from the pre-merge build commit `132e2f9c8`. None of those files reads the mill's `thread_lines`, so they do not exercise this line on real rows.
- **Guards.**
  - `tools/check-architecture.ps1` was started without `-ExecutionPolicy`, per the dispatch. Its result: see the hand-off report.
  - `check-agent-workflow.ps1` was not run.
- **Not run, per dispatch.** Full suite, prepare, `test_demo_combined_postgres`, frontend (no frontend change in the diff).

## Residual risk (beyond the packet)

- The line has never been computed on real rows. Its first real evaluation is E3, and E3 checks only self-consistency until M1 is fixed.
- The S-8 k is 7 or 6: verified S-9, and S-8 is the only day counted. So a one-day gap in `day_facts.rows` (S-i) changes the on-screen number with no check firing.
- On S+0, MILL-4 needs the thread's state on the board day to still be RECURRED. If any later lifecycle event lands in the recurred segment by S+0, the mill line disappears (correct per case 5) and MILL-4 fails at E3. That would be a story fact to report, not a code fault.
