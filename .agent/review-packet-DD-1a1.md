# Review packet: DD-1a1 (steady full days), state after DD1a1-R9 (builder 12)

Branch `task/DD-1a1-steady-fullday`; main merged before R9. **Partial packet**: R9 and its L2 acceptance are done;
the R6 degraded-day check, the five R3 L2 checks, the mill day, Q8 and the Cold failure day are **not run** (see Open).

## Outcome delivered (R9)
- Verification no longer blocks when a baseline day's selected run changes with identical baseline facts; it records
  `reselected`. A change of the facts still gives `BASELINE_SELECTION_CHANGED`.
- The Kobo trial chain admits every trial-span complement at its `received_at`, between the chain steps
  (freeze 15:00, afternoon 18:00, night-late 22:00, Part A 01:00, Part B 04:00, later 12:00, evaluate 13:00).
  ACT-K1 (accept, apply, `effective_from`, `freeze_at`, windows, values) is unchanged.

## Verification diff (own reviewer pass, DD1a1-R9)
`git diff 7861ab03b..HEAD -- backend/assetops_backend/actions backend/tests/test_dd1a1_r9_baseline_facts.py`
- `actions/verification.py`
  - `_baseline_facts(revisions, lo, hi)`: the INTERVAL assessments whose interval (`first_on`..`off_after`/`last_on`)
    or any segment meets `[lo, hi)`, as `{assessment_key, claim_level, result}`, sorted by key. Revision, run and
    evidence ids, basis digests and the WINDOW summary (whose cohort counts move with bracket data) are not facts.
    The verification reads exactly these via `rules.target_window`.
  - `_day_states(..., facts_window=None)`: on a run-id change with a window and the port, equal facts append
    `{"pinned_run_id","current_run_id","facts":"equal","assessments":n}` to `reselected` and do not set `moved`.
    `reselected` is present only when non-empty, so every earlier day-state body (S6-02b contract) is unchanged.
    Fails closed as moved when the port is absent, no window is given, or either run cannot be read.
  - Applied to baseline pins in `_assess`, `current_state` (`baseline_days`) and F2 attribution (`name == "baseline"`).
    Later pins keep "append a new later selection binding". No cohort, bracket or window rule changed.
  - `VerificationPorts.run_assessments(tenant, site, run_id)`: new optional port.
- `actions/composition.py`: wires it to `reads.store.run_detail(...)["revisions"]` (existing read; **pre-flight: no
  schema change**).
- Review focus: the fact projection (is the full `result` the right equality, too strict or too loose?), the
  intersection rule, and the fail-closed paths.
- **R9 review Lows 1-2 fixed (builder 14, `ac9655668`, fixture `33dfe724b`):**
  - Low 1: `meets()` treats an unparseable start as inside the window (fails closed as moved).
  - Low 2: `_baseline_target(revisions, lo)` recomputes `rules.target_window` per run; `reselected` also needs equal
    (state, candidate_seconds), so a conflicting duplicate outside the window makes the day moved.
  - Tests `test_an_interval_with_an_unreadable_time_counts_as_inside_the_window`,
    `test_a_conflicting_duplicate_outside_the_window_is_moved`. Each fails with its fix reverted (1 failed, 7 passed
    each); reverted by `git checkout`. The fixture's segments now use the rules' `CANDIDATE_AVOIDABLE` (it used
    `CANDIDATE`, an unknown class that made every fixture target INCONCLUSIVE, so Low 2's test was vacuous).
  - Rerun on `33dfe724b`, own DB: R9 unit + `test_s6_verification_evaluator_postgres`, `_holds_postgres`,
    `test_md0_fixture`, `test_out_b3_cold_ev`, `test_walk1_productive_sales`: **125 passed**, 351 s.

## Other files
- `tools/demo_combined_kobo.py`: `play()` and the `admit(until)` callback; `_trial_chain(..., admit)` calls it before
  the freeze (`freeze_at`), before the later run (`received_at - 1 µs`) and before the evaluation (`evaluate_at`).
- `tools/dd1a1_r9_check.py <db>` (new L2 check).

## Checks run (localised only; no full suite, no prepare, no baseline)
- Unit `backend/tests/test_dd1a1_r9_baseline_facts.py`: 6 passed (equal facts -> reselected; one changed value -> moved;
  changed segment -> moved; assessment outside the window ignored; new interval inside -> moved; fail-closed).
  Non-vacuity: mutating the comparison to always-equal fails 3 tests; reverted.
- Existing verification files (`test_s6_verification_evaluator_postgres`, `_holds_postgres`, `test_md0_fixture`,
  `test_out_b3_cold_ev`, `test_walk1_productive_sales`): first run 122 passed, 1 failed (S6-02b contract shape: the
  always-present `reselected: []`); fixed by the conditional key (`5470567b9`); the failing class re-run: 5 passed.
- L2 R8 probe (stream, own DB, 541 s, 17 runs): VERIFIED ACT-000001; `dd1a1_r8_check stream` all PASS (sequence 1..N
  across midnights, late complement accepted, all windows SELECTED_UNIQUE, 0 AMBIGUOUS); `dd1a1_r9_check`: 5
  post-freeze 11-04 selections (18:06, 22:06, 01:06, 04:06, 12:06Z), each facts-equal; outcome lists `reselected`.
- L2 full `with` (1082 s, 33 runs) and `without` (335 s, 8 runs), one at a time:
  - `with`: r9_check PASS (5 post-freeze re-selections, all equal facts); r8_check full all PASS incl. 0 AMBIGUOUS;
    r7_check (R7/R7b) all PASS. `without`: r9_check PASS (1 re-selection, equal); 0 AMBIGUOUS.
  - `dd1a1_fullday_compare`: finding 3=3, action, action_event, action_policy_change, work_case(+revision, event),
    verification_metric (12), verification_outcome (VERIFIED), trial_cost_comparison, financial_assumption EQUAL.
    Q6 metrics equal.
  - The 3 Findings (10-21, 10-28, 11-04 at 04:35) have equal final revisions: SUPPORTED / CANDIDATE_AVOIDABLE,
    200 min, 04:35-07:55, same recurrence; 11-04 is not UNCONFIRMED. Revision counts differ (7 vs 15; R8 allows it).
- Guards, one at a time: V (mock labels/vocabulary, 14 pass), A, W, N pass; M (missing-claim scan) passes with
  `NODE_PATH` set to the plan2 `frontend/node_modules` (this worktree has none; first attempt failed on the missing
  `typescript` module, a precondition, not a finding).

## Known deviations
- `verification_plan` differs with/without in `baseline_selection` only: `selection_seq` (54 vs 15, bookkeeping) and
  `interval_revision_ids` (2 vs 1 on 11-04: the pre-dawn complement adds an interval outside the baseline hour, at
  freeze). The target, metrics and outcome are equal.
- `reselected` appears only when non-empty (keeps the S6-02b contract byte-shape).

## R6 degraded-day check (builder 14) - assertions 1-6 PASS, 7 FAILS on grade: Architect rules
- Cause of builder 13's false fill: the gateway's background uploader (`gateway/assetops_gateway/uploader.py:409`,
  started by `ipc.attach_uploader`) runs a delivery pass on start, so each post-outage complement's gateway drained the
  withheld half at its own `received_at`. Fix (tool only, `6340405fa`): a post-outage complement starts its gateway
  with no `upload` block (`publish_first_half`, `outage_continues`); its ingestion stub must see 0 submissions; the
  story run's withheld half is read back at day end (`withheld_after`). `_OUTAGE` is now epoch -> story run id.
- `deg_compare.log` (own DBs, dropped): 1 night-early in full; 2 story 4/8 = v1; 3 complements 0; 4 no reading of the
  day received after 12:00Z on any later day (stray=[]); 5 outbox at night-late's end: story ACKED 4 / READY 4,
  complements READY 6/6 each; 6 own gateway per day; 7 0 AMBIGUOUS, findings equal ([]).
- **FAIL 7 grade.** v1: interval 03:25Z INDETERMINATE (OPEN_BOUND), window LIMITED (1 INDETERMINATE). With: interval
  02:05Z NECESSARY (the pre-dawn night start, R3 Q2), window LIMITED (1 NECESSARY); no 03:25 story interval.
  - Not caused by the complements' delivery: the delivered half is the gateway's first 4 batches in source-id order,
    and source ids are random per build. v1 delivered a 194/97/256+68 set whose 194-item source carried the generator;
    the with build delivered the other 194-item source, so the story window has no generator readings after 02:55
    (the night interval stays OPEN_BOUND). So v1's own degraded grade depends on the build's UUIDs.
  - Even with the same sources delivered, the with day holds the night interval as well, so the window counts cannot
    equal v1's; the ruling's "story run's assessment unchanged" needs the story-window interval compared alone.
  - Per R6 ("if any assertion fails, stop"), not adjusted. Architect question: make the outage's delivered half
    deterministic by role (a tool-side batch choice), or compare only story-window intervals and accept the order.
- Analytic-run count compare removed (complements are assessed too; not a finding).
- R5-R9 re-check on `33dfe724b` (after the R6 fix and the R9 Lows): one `with` build (own DB, 981 s, 33 runs);
  `dd1a1_r9_check` PASS (outcome VERIFIED, reselected iff run changed), `dd1a1_r8_check full` all PASS (36 streams,
  0 AMBIGUOUS), `dd1a1_r7_check` all PASS. DB dropped.

## Open (not run; next builder)
- After the R6 ruling: the five R3 L2 checks, the mill day (0 generator starts, CH-9b mill outcome unchanged), Q8
  cost per full day, the Cold failure day, guards. No tooling exists yet for R3/mill/Q8/Cold beyond the builds.

## Residual risk
- A real restatement whose only change is in the WINDOW summary is not a baseline fact by this projection; the
  verification does not read it, so this follows the ruling's "assessments that the verification reads".

## User review
Not required for R9 (Architect: owner informed, not blocking). The verification diff needs its own reviewer pass.
