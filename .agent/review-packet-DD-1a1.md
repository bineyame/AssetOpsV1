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

### DD1a1-R10 result (builder 15): R6 assertion 7 restated and PASSES
- Assertion 7 is now fixed checks (`tools/dd1a1_degraded_check.py compare`), no comparison to v1 times or classes:
  7a one epoch, 7b 0 AMBIGUOUS, 7c no Finding, 7d window LIMITED with incomplete-evidence limitations, 7e no interval
  past the last delivered reading (11:00Z) except OPEN_BOUND (with: 02:05-02:55Z, open), 7f the day's grade after the
  story run equals the final grade after the complements (the in-build form of "with equals without on the same
  delivered set"; the two builds draw different source ids, so a cross-build equality cannot be asked). 7a-7d hold for
  v1 and with. Result `deg_compare.log`: 1-6 and 7a-7f all PASS (with build rerun, own DB, dropped).
- Guard (`85c8263a7`): `demo_story_days._entry` refuses a Kobo `degraded` day whose kind has a `complement` with
  `DEGRADED_DAY_HELD` (calendar resolve, prepare and `plan_add_day` all pass through it) unless the check script sets
  `DEGRADED_PROBE`. `test_demo_story_days.py` r10 tests: shown calendars (v1, v2) hold none, a script/doc scan finds no
  `add-day ... KOBO-001 ... degraded`, calendar and add-day refuse. Proven to fail: guard disabled -> refusal test
  fails; a planted `add-day --site KOBO-001 --kind degraded` line -> scan test fails; both reverted. 35 passed.

## R3 L2 checks (builder 15; `tools/dd1a1_r3_check.py`, plus `dd1a1_fullday_compare`; one `without` 330 s / 8 runs and one
## `with` 1075 s / 33 runs on the registered Kobo Site; the first `with` attempt died on a transient SSL EOF in the
## local ingestion server (batch-count assert), the identical rerun passed)
1. Night shape PASS on 8 nights: at most 1 start (7 nights 1 start at 02:05Z = 05:05 local, after 04:00; 11-05 none after the
   25 % reserve change), clinic requested == delivered every reading (MG-5). Fuel 0.0 L is NOT measurable: the Site has
   no persisted fuel reading (fuel_level role 0 readings), so it rests on the step note (BL-16).
2. MG-2 PASS: candidate-avoidable intervals per window equal with and without nights (10-21, 10-28, 11-04: 1 each).
   ACT-K1: action, action_event, policy change, work_case, verification_metric (12), verification_outcome, trial cost EQUAL.
   Differences, reported not hidden: `finding_revision` 7 vs 15 and `financial_consequence_work` 9 vs 17 (revision
   counts, R8 allows), and `verification_plan` differs only in `baseline_selection` (selection_seq 15 vs 54; the 11-04
   baseline window has 2 interval revisions with nights, the extra being the 05:05 NECESSARY night start). Outcome VERIFIED equal.
3. Mill/spare solar PASS as far as stored: the story-window readings are identical (9472 = 9472, 0 only-with), so
   whatever reads daylight is unchanged; no spare-solar row is persisted to compare. Each of 13 full days COMPLETE with
   nights; without nights 10-07, 10-14, 11-01 were LIMITED (the intended gain). The 10-06 lead-in (night only) is LIMITED.
4. No new Findings (3 = 3 equal), actions, thread events or money rows beyond the revision counts above.
5. 06:00 seam reported: SoC 31.46 % -> 40 % (42.5 % on the 10-21, 10-28, 11-04, 11-05 days), generator RUNNING -> STOPPED
   (11-05: STOPPED -> STOPPED). A step, as DD1a1-R Q3 expects.
- Q8 (build wall times only, no prepare): Kobo `without` 330 s -> `with` 1075 s, +226 %. This exceeds the +50 % prepare
  budget on this measure; the whole-prepare ratio (Cold/EV unchanged) was not measured. **Architect to rule.**

## Open
- Cold failure day with full days: BLOCKED, Architect to rule (below). Nothing else outstanding for DD-1a1 lane 2.

## Mill day (builder 17; probe modes `mill` / `mill-without`, `mill-midday` placed at S-5d, 10-30)
- Generator starts inside the mill window (03:00-11:00Z): 0 with and without. Mill-day productive kWh equal (110.000);
  grade PARTIAL 50% (without) -> COMPLETE 98.96% (with). 11-01/11-03 168.333 -> 210.333, 11-04/11-05 0 -> 42 (honest
  daylight use in the 14-18 local complement, DD1a1-R12 item 2). `vf.assess` not run: no 3 COMPLETE baseline days (MILL-3,
  DD-1a2/1b2, not this unit).
- 15:50Z start: a defect (DD1a1-R12); fixed below. After R12 the mill build has 0 dusk starts.

## DD1a1-R12 dusk start state (builder 17; L2 own `*_test` DBs, mill 665 s/21 runs vs mill-without 197 s/5, with 1165 s/33 vs without 310 s/8)
- Probes S-dusk (probe S windows 1-6, 06:00-18:00) and M-dusk (`kobo-mill-midday`) in `tools/probe_kobo_nights.py`
  measure 18:00 (15:00Z): SoC 89.4737 %, fuel 300.0 L, generator STOPPED (full precision, `kobo-night-handover-v1.json`
  `handover`). `kobo-steady-dusk` is regenerated from it; derived `kobo-mill-dusk` added; v2 `mill-midday` complement now
  uses kind `mill-dusk`. Both in `derive_steady_scenarios.py --check` (rc 0) and `probe_kobo_nights.py --check` ("current").
  Each dusk file run 15:00Z-17:00Z from its start: 0 generator starts, 0 running minutes, ends 69.47 % (= probe S at 20:00).
- `tools/dd1a1_r12_check.py`: no generator start in 15:00Z-17:00Z (mill build, with-builds): PASS. 10-30 has 1 start (02:05Z
  night, accepted R3 Q2). 18:00 seam 10-30: SoC step -0.439 against a largest other step of 1.307: no jump.
- Equal with and without full days (`dd1a1_fullday_compare`): findings 1 = 1 (mill) and 3 = 3 (steady), action, action_event,
  policy change, work_case(+revision), work_event, verification_metric, outcome, trial cost, assumption revisions; MG-2
  candidate-avoidable interval counts per window equal (R3 check 2 PASS, both pairs). Differences, as in R3 and allowed
  by R8: finding_revision (7 vs 15; mill 3 vs 7), financial_consequence_work (9 vs 17; 5 vs 9), verification_plan
  baseline_selection only. (R3 check "without holds nothing outside story windows" FAILS on the mill pair only because it
  assumes 03-11Z story windows; the mill window is 03-15Z. Not a defect.)
- Observation for the Architect: `kobo-steady-dusk` is used by NO day in the v2/B-22 calendar (steady days end their story
  window at 11:00Z and use `steady-afternoon`, 14:00-20:00 local); R12's "every steady day runs kobo-steady-dusk" does not
  match it. The steady-afternoon complement gives one generator start per steady day at 12:05Z (15:05 local), 7 days, plus
  11-05 at 12:45Z. Its 11:00Z seam is continuous (SoC step <= 0.16), so this is the day's own state, not a declared reset;
  not changed, reported. If R12's concern covers it, rule.

## Cold failure day with full days: FAILS (builder 17; `cold` / `cold-without`, DBs `..d12cold_test`, `..d12cold-without_test`)
- `cold-without` builds (3 days, failure day: 3 Findings, 27 s). `cold` (full days, 24 runs per day) dies on the failure day
  (11-04, after 19 steady runs): `AssertionError: the shifted replay wrote no cold Finding (COLD_START_FAILURE)` from
  `test_w502_cold_scenario_producer.finding_revision`, which selects the Finding whose analytic run window equals the case's
  exact window. With the full-day tiling the failure replay's analytic run no longer has that window. So Finding/cost equality
  with and without full days cannot be shown. **Architect to rule** (cold failure day needs the w502 BUILD body to select by
  the failure run, or a different tiling). Not worked around.

## Q8 and the build-time fallback
- Q8 is ruled in DD1a1-R11: keep B-22. The owner chose B-16 as the fallback if the DD-1b2 rehearsal measures the whole
  prepare over 3 h (`.agent/owner-build-time-2026-11-06.md`).
- Kobo build wall: `without` 310 s -> `with` 1165 s (this revision; 1075 s earlier).

## Guards
- `tools/check-all.ps1` (Python = plan2 venv, NODE_PATH = plan2 `frontend/node_modules`), run before the R12 change: "All 17
  guards passed" (estate self-tests 1386 s). The R12 change touched only scenario/tooling files; guards not rerun after it.

## Residual risk
- A real restatement whose only change is in the WINDOW summary is not a baseline fact by this projection; the
  verification does not read it, so this follows the ruling's "assessments that the verification reads".

## User review
Not required for R9 (Architect: owner informed, not blocking). The verification diff needs its own reviewer pass.

## R13 (builder 18): Cold failure day probe, standing checks (STOPPED: two blockers need the Architect)
- Probe on the `cold` build to the failure day (DB kept until answered, then dropped). Neither (a) nor (b):
  - No Finding of any kind exists on that DB (0 `finding`, 0 `finding_revision`). Not a window-match fault.
  - No double send: 0 (asset, role, record kind, source time) sent twice in 15:00Z-17:10Z. Failure run is [16:00Z, 17:05Z], fill-ins
    own spans outside it (`owned`), so (b) does not occur; there is no fill-in after the failure run in this build.
  - Cause: the failure run's COLD start-response assessment is OBSERVED_FAILURE but limitation "The source classification does not
    permit a Finding" (`cold.py` `failure_finding = failure and gate.permitted`). The analytic window is the whole local day
    [21:00Z prev, 17:05Z) and its evidence is published by many runs (68 distinct `evidence_publication.run_id`); `source_provenance.classify`
    returns MIXED (`MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS`, "N-L2: several runs are never coherent"), so `gate.permitted` is false.
    Without full days the window holds one run. Same for COLD_EXCURSION (the 11-04 excursion has no Finding either).
  - R13 acceptance cannot be met by a (a)/(b) fix: it needs a ruling on the S4-05 multi-run gate (a compatible-run-basis for tool-made
    complement runs of one Site-day) or a different Cold full-day design. Not worked around.
- Standing checks added: `tools/dd1a1_r12_check.py <without> <with> [days.json]` (seam <= 0.5 pp with equal generator state; pure steady day
  0 starts 06:00-20:00 local, INFO-only here since this calendar has none; MG-2 equal) and `tools/dd1a1_r3_check.py ... [days.json]`
  (the "nothing outside story windows" line now uses the build's story runs: 8 windows, 9576 readings, 0 outside, PASS).
- Kobo `without`/`with` rebuilt (revision after commit of the checks): R3 L2 checks all PASS; r12: dusk starts 0 PASS, MG-2 equal PASS
  (8 windows), **seam check FAILS**: 34 seams, 24 over 0.5 pp. Measured steps (every Kobo story day alike): 03:00Z night->story +8.5 pp
  (+11.0 on 11-04/11-05), generator RUNNING -> STOPPED; 11:00Z -0.16 (11-04/05: 0.0) PASS; 15:00Z +0.95 pp, generator RUNNING both sides
  (11-05: -0.70); 17:00Z +38.2 pp (11-05: +44.0), RUNNING -> STOPPED; 21:00Z -0.25 PASS. The 17:00Z and 03:00Z seams are the measured
  start states (R12 dusk/night), i.e. declared resets, not continuous; 15:00Z is an equal-state seam over the bound. Stopped per R13;
  Architect to say which seams the 0.5 pp bound covers (equal-state only?) and rule on 15:00Z.
- Guard V (`test_out_b2_vocabulary`) 4 passed. Guards A and W not run (names not in the brief and the change is tools only); no full suite.

## DD1a1-R14 (builder 19): PART 1 DONE, parts 2-3 PARTIAL (stopped at context)
- Part 1 (Cold full days withdrawn): v2 Cold kinds lose `complement`/`covers_end`, kind `steady` and `config/scenarios/cold-steady.yaml`
  removed, `cold()` removed from `tools/derive_steady_scenarios.py`; L0 (`backend/tests/test_demo_story_days.py`, 35 passed) now asserts Cold v2 days
  equal v1 days (one story run, no fill-ins). L2: `cold` vs `cold-without` (own `*_test` DBs, 27 s / 26 s, 3 runs each): 3 Findings on the failure
  day, 4 in all, every compared table EQUAL (finding, work_case, work_event, money tables 0 = 0), accepted_evidence 280 = 280, 0 AMBIGUOUS. DBs dropped.
- Parts 2-3: NOT landed. WIP copies (NOT in the build) are in `.agent/DD-1a1-r14-wip/` (v2 list with chain kinds + `after`, derive and probe changes).
  `tools/demo_story_days.py` already carries the inert `after` hook. Guards V/A/W not run (no code that they cover changed in part 1; no full suite).
- Finding for the Architect (blocks part 2 as designed): the template-Site probe of the story run is NOT the registered-Site run. Template probe N
  (`kobo-s3-dispatch-necessary-run`, 03:00-11:00Z) ends 30.0 %, 217.65 L, generator RUNNING; R30/R25 end 100 %, 300 L, STOPPED. Run setup accepts only
  STOPPED as a start, so every N-chain seam after a RUNNING end (11:00Z afternoon, 17:00Z late night, 24:00 early night) breaks "equal generator state" and
  adds a start/interval, so the R14 stop applies if the registered Site agrees. The R13 measurement (11:00Z step -0.16, equal state) disagrees with the
  template probe, so chains must be probed on the registered Site (`_shifted` drafter of `host/tests/test_dd1a1_registered_kobo.py`), and the R25 (25 %
  reserve after S+1) probe needs the Foundation revision on that Site. Neither is done.

## DD1a1-R15 (builder 20): STOPPED at the registered-Site probe (A' stop conditions 1 and 2 fire)
- Probe: registered KOBO-001 (`_shifted` drafter of `host/tests/test_dd1a1_registered_kobo.py`, own `*_test` DB, mini-grid v6,
  5 min, dropped after). R25 = `publish_battery_reserve` 25 % (recorded 2026-10-14T02:00Z, effective 2026-10-15T00:00Z) and
  known-at after it. Rest-of-day = evening windows 2-4 (mill: window 4) then the R2 late night, one run, start = story end at
  full precision. Script, derive draft and raw output: `.agent/DD-1a1-r15-wip/` (`r15probe.json`).
- Results (local time; generator RUNNING intervals):

| chain | story end (14:00; mill 18:00) | story gen | rest end 24:00 | rest gen | early night 03:00 / 06:00 |
|---|---|---|---|---|---|
| N | **RUNNING**, 30.0 %, 217.65 L | 06:25-14:00 | **RUNNING**, 30.0 %, 174.19 L | 14:05-24:00 | RUNNING / RUNNING (00:05-06:00) |
| R30 | STOPPED, 100 %, 300 L | 07:05-10:55 | **RUNNING**, 30.57 %, 298.03 L | 22:05-24:00 | RUNNING / RUNNING (00:05-06:00) |
| R25 | STOPPED, 100 %, 300 L | none | **RUNNING**, 27.37 %, 300 L | 23:25-24:00 | RUNNING / RUNNING (00:05-06:00) |
| Mill | STOPPED, 89.47 %, 300 L | none | STOPPED, 48.42 %, 300 L | none | STOPPED / RUNNING (05:10-06:00, 06:00 exempt) |

- Stops (R15 "Stops"): a story run ends RUNNING at 14:00 (N; the registered Site agrees with the template, R14 blocker);
  three rest-of-day runs end RUNNING at 24:00 (N, R30, R25). So the 24:00 cut and the R7 03:00 split are not STOPPED on both
  sides for N/R30/R25. Only the mill chain passes A'. Nothing was derived or built; no Kobo builds, R5-R13 checks or guards
  were run (they depend on the files A' would derive). Also for the Architect: the mill story run ends at 18:00, not 14:00, so
  its rest-of-day cut is at 18:00 (not in R15's cut list); the probe shows STOPPED there.
- Per R15 this is the point where D (story-only or "partly checked" Kobo days) goes to the owner with these numbers.

## DD1a1-R16 (builder 21): hybrid Kobo days (owner-approved 2026-11-07), built
- Commits on `task/DD-1a1-steady-fullday` (main merged `00583fb92`): `8b68aaa14` (design), `b71389273` (registered dry run), checks commit after it.
- Design: a day is full only where every join is STOPPED, measured on the registered Site. Only the mill day (`mill-midday`) is full:
  `complement` = `night-early`, `mill-rest` (`kobo-rest-mill`, 18:00-24:00 in ONE run: evening window 4 verbatim, then the R2 late-night
  windows verbatim, each with its `# source:` line; start = the story run's measured 18:00 end at full precision, 89.47 %, 300 L, STOPPED).
  Joins measured: 18:00 STOPPED, 24:00 STOPPED (48.42 %, 300 L), recorded under `full_days` in `kobo-night-handover-v1.json`
  (probe tool refuses to write a RUNNING join). N, R30 and R25 story days (and degraded/trial days) lost their `complement`: v1-equal story-only
  ("partly checked"). Retired kinds/files: `steady-afternoon`, `steady-dusk`, `mill-dusk`, `night-late` kinds; `kobo-mill-dusk.yaml` (replaced by
  `kobo-rest-mill.yaml`). The steady-day files (`kobo-steady-*`, night files) stay for DD-1a2 (B-22, probed per day; not built here).
- Guard (non-vacuous): `demo_story_days.check_full_day` raises `FULL_DAY_JOIN_NOT_STOPPED` for a `complement` whose story has no measured
  all-STOPPED joins. `test_full_day_only_where_every_join_is_stopped`: a complement on the N kind is refused; the mill day with one join set to
  RUNNING is refused. R10's degraded hold test now also shows the R16 guard refuses a degraded day past the flag.
- Seam bound (mill day, `dd1a1_r12_check.py`, full days only, from days.json): 15:00Z join STOPPED both sides, SoC step 0.439 pp (<= 0.5), day end
  STOPPED; fuel step 0.0 L (probe: 300.0 -> 300.0; fuel is not a persisted signal). 06:00 story start exempt (SoC 31.46 -> 55 %, RUNNING -> STOPPED,
  the 05:05 pre-dawn start is in the early night, not the mill window). Fails by design (non-vacuous) on a build with no full day.
- Builds, one at a time (build wall: mill 274 s, mill-without 211 s; full calendar without 6 min / with 381 s):
  - Mill pair (mill day S-5d + stream): findings, finding_revision, action(+events, policy change), work cases, verification_metric (12), outcome
    VERIFIED, trial cost, money all EQUAL; `verification_plan` differs only in baseline-selection bookkeeping as before (R9). MG-2 counts equal
    (5 windows). Mill day 2026-10-30 COMPLETE; 0 generator starts in 06:00-24:00 of the mill day (one 05:05 pre-dawn start, in the night); story-window
    readings identical (5920 = 5920) so mill/spare-solar verdict reads the same data. 0 AMBIGUOUS expected unchanged (finding counts equal).
  - Full calendar with/without: 3 Findings = 3 (7 = 7 revisions), ACT-K1 VERIFIED, metrics 12 = 12, money tables EQUAL, MG-2 equal over 8 windows. The
    calendar has no complement now, so the two builds are the same inputs (equal by construction; recorded, not a finding).
- R6/R7/R7b/R12/R13 re-check: R6 (degraded outage split across complements) no longer applies (degraded day is story-only; `_OUTAGE` path untouched).
  R7/R7b (03:00 split) no longer applies to the calendar (trial days story-only); the split machinery still resolves on a mill day crossing a revision
  (tested). R12 dusk-window starts: 0. R13 seam check re-stated for full days (PASS above). R3 checks 1-3: PASS on the mill day (night: 1 start 05:05
  local, MG-5 supply complete; COMPLETE). R3 check 3 now holds only full days to COMPLETE; story-only days are listed, not held.
- Guards one at a time: V (4 passed), A (architecture), W (agent workflow), navigation, dependency registry, delivery, mock-gap, missing-claim scan +
  fixtures, evidence width, mock labels, ledger, chain coherence, event register, chain graph, perf, hard-wiring: all PASS. Estate guard: see handoff.
  `test_demo_story_days.py` 36 passed; registered-Site dry run (`host/tests/test_dd1a1_registered_kobo.py`, own `_test` DB) 2 passed.
- Not done / open: MILL-3 join rule in the DD-1a2 dry run is DD-1a2's; Q8 wall time now 381 s vs 6 min story-only is moot (complements only on the mill day).
