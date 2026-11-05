# CH-9 handoff (PARTIAL: u1-u4 + Q2 landed, u5 deferred to CH-9b; resume at "Resume order for builder 7")

## Status 2026-11-05 (builder 6; stopped near the context cap, no process or DB job of mine running)
Merged `main` (CH-5a2b) at `c37fe981b`, clean. Commits: `2064fcb7b` read-test 5 Oct pv day; `a8f115f84` ch5a2 goldens
(+critical_served); `5761ba30a` Portfolio unit (CH9-R3 Q2); `08a5c0988` scenario row test keys; `a830b2d0c` ch1a
required seconds. All Postgres files in the list green; MD-0 templates `tpl_ca277a2e` / `tplc_ca277a2e` built;
L3m states and close checks 0 unexpected, COH-17 0; guards A, W, V pass. Packet draft `.agent/review-packet-CH-9.md`
(SCENARIO finding, rulings, owned tests, KDs). DBs left: `assetops_mechanism_test`, `assetops_mechanism_close_test`
(derived, normal state). No polish clone created.

## Resume order for builder 7
1. Polish clone (coordinator: re-collect after the CH-5a2b merge, COH-17 = 0): `tools/chain_clone.py create ch9
   --migrate`; `DATABASE_URL=<clone> python -m assetops_backend.chain.backfill --steps a,b,c,d`; `chain_clone.py settle
   ch9` (report tick job growth vs the CH-1b stage bound); collect with `PGOPTIONS` read-only into scratch; check
   `--expect tools/checks/fixtures/chain_coherence/expected-today.json`; owned `expected-today.json` changes (DD-1).
2. A collect from a temporary main worktree on the same clone (CH-5a2b packet "collect A") for: the per-window table of
   named days, day counts and why each day is not complete (CH5a2b-R2); old -> new `count_basis`; MD-0 values old -> new.
3. `tools/check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`.
4. Finish the packet OPEN section; task status `in_review`, ACTIVE_CONTEXT / CODE_STATE; drop the clone.

## Status 2026-11-05 (builder 5; stopped at the context cap, no process or DB job of mine running)
Commits: `4c4dff4ee` estateRoots fixture copy; `ababdaf53` mill-midday kind + L2 test; `d4b26a299` w403 worker/scenario
owned tests; guard fix (`mini_depth/store.py` `database_now` + `load_operating_calendar` via `chain.composition`;
`projection.py` drops `sqlalchemy`); `4a2db4a80` + next: w403 read shape owned tests. `main` = `692e4d57e`, ancestor.
- **Postgres runs** (host runner default URL, port 55432; NOT 5432): worker file 5/5 green; read file: 9 of 10
  green (shape test green after fix); `test_pending_stale_missing_historical_current_precedence_and_jobs` FAILS at
  `renewable_job(engine, t, s, date(2026, 10, 5))` (read test :202, helper :101): 0046 `mini_enqueue_hour`
  refuses "renewable work needs a positive pv_available_power reading in the hour" (5 Oct has no readings). Needs
  an owned fixture step: a positive pv reading in that hour before the enqueue (then re-check the STALE_SOURCE
  assertions that follow; 5 Oct's other 23 operating hours stay missing). Never weaken.
- `mg_published` (scenarios test) now seeds `_dark_hours(spec)` like `_ingest` (otherwise 23 missing hours -> UNKNOWN).
- Frontend: `tsc` 0 errors; vitest miniDecisions, estateRoots, estatePortfolio, miniRenewableRoutes green
  (`vitest related` breaks on a `.py` import; ran the importers directly). node_modules is a junction to plan2's.
  **Open:** `frontend/src/estate/EstatePortfolio.tsx:423` hard-codes "kW at midday" (Portfolio, demo-visible),
  test `estatePortfolio.test.tsx:435-436`. Not in sheet §3 files: packet item / Architect.
- **u4** `mill-midday` kind uses `kobo-daytime` **v2** (the registry holds only v2; Q8 said v1): Known Deviation.
  L2 test `test_demo_story_days.py` (resolve/validate, times, payload, prepare-only refusal); non-vacuous (end 14:00
  failed it). No prepare (owner rule): the 12 h interval acceptance by the kobo-daytime model is unproven.
- **u5 BLOCKED (Architect):** `domain_action.origin_finding_id` is NOT NULL with a Finding FK
  (`migrations/versions/0033_w5_cold_work.py:44-54`), and thread linking is by origin Finding
  (`chain/threads.py:296` `link_action`). The headroom thread is opportunity-only (`threads.py` `opportunity_source`,
  subject SITE, no Finding), so no domain Action can attach to it without a contract change. Nothing built.
- Guards: architecture PASS (after fix), agent-workflow PASS.

## Resume order for builder 6
1. Fix the read-test `renewable_job` fixture (above), rerun that one test (`-k pending_stale`, ~3 min).
2. Remaining Postgres files, 1-2 per call (each 5-15 min): `test_ch4_opportunity_postgres.py`,
   `test_w403_scenarios_postgres.py`, `test_w402_reads_postgres.py`, `test_ch1a_snapshot_postgres.py`,
   `test_ch1b_fix_postgres.py`, `test_ch9_daylight_postgres.py`, `test_w403_migration_postgres.py`.
3. MD-0 (when lane 1 idle; `chain_coherence.py collect` PIDs 28484/20560 were lane 1's): as builder-5 step 5 below.
4. Guards, packet (builder-5 step 6 items + u5 block + Portfolio label + kobo-daytime v2 + SCENARIO_BASIS_MISMATCH
   demo-visibility answer, not yet investigated).


## Status 2026-11-05 (builder 4; stopped at the context cap, no process or DB job left running by me)
Commits on `149563f7b`: `83037a50d` (u2 /2 + basis), `595ce7bb3` (measure + no-noon test), `fbf8973fe` (u3),
`905df84fd` (MD-0 Q1). `main` = `692e4d57e`, still an ancestor (no merge needed yet). **No Postgres test has been
run on builder 4's code**: lane-1 `tools/mechanism_dataset.py build --variant close --budget 540 --resume`
(PIDs 31352/21808, not mine) was running the whole time.

### Landed by builder 4 (anchors)
- **/2 bump** `mini_decisions/store.py:32-35` (`OPPORTUNITY_MODEL_VERSION` /2, `LEGACY_...` /1,
  `READABLE_...`); `opportunity_roots` = `DISTINCT ON (first_day,last_day)` over both, `/2` wins (lexical DESC).
  `latest_opportunity_sha`/`opportunity_root` stay producer-only (/2), so a /1-only study re-projects as /2.
  Frontend `MiniOpportunity.tsx` `OPPORTUNITY_MODELS` set (/1,/2) in `matchStudy`.
- **Basis** `read.py read_selected_renewable_basis(..., windows=None)`: default = per day
  `daylight_hours(...).study_hours` (new property, `store.py` `DaylightHours.study_hours`); `windows=` reads exact
  pinned hours. Consumers: `mini_decisions/opportunities.py` `_study` (/2: compares pin keys `(local_day,
  window_from)` with basis keys -> a changed hour set is SELECTION_CHANGED; /1: `pin_windows(pins)`),
  `day_read_row()` (day row `window_hours` stored or /1 default; day-level seq/revision only when the day has one
  pin; `hours[]` carry their pins), top-level `window_hours`, `_compatible` counts distinct days.
  `scenarios.py` `_pinned_windows` (scenario pins stay one per day, read at their revision's hour; `by_day` keyed
  `(local_day, window_start)`). **Packet item:** a scenario (one pin/day) is incompatible with a /2 study whose
  day has several hours -> SCENARIO_BASIS_MISMATCH; changing the scenario pin contract is out of scope.
- `window_hours: 1` removed: `chain/opportunities.py` `_item` reads stored `window_hours` (lookup SQL adds
  `window_hours`, `model_version`), /1 -> 1. `VALUE_LINE` = §2 text with `{h}` (`vocabulary.py`).
- **Measure** `daylight_headroom_kw` (`measures.py`, period operating_hours, 1.0, `mini.daylight_headroom@1`);
  `PERIOD_MIDDAY`/`MIDDAY_WINDOW_LOCAL` deleted (`policy.py`, `grading.py`); adapter `RenewableHeadroom`
  (`measure_impls.py`), port `renewable_hours` (`ports.py`, `postgres_chain_inputs.py`). Register: roles
  `[pv_available_power]` + mini_depth/job_domains; `thread-lifecycle-v1.json` clean-day measure renamed. All test
  literals renamed (ch1a/ch1b/ch5a1/md0 + ch5a2 fixtures, `tools/checks/test_event_register.py`).
- **No-noon test** `tests/test_ch9_no_noon_literal.py` (reconcile, hour_windows, basis, day_heads, measure +
  reader, day_row); `store.NO_PV_BINDING`; `renewable_noon_heads` -> `renewable_hour_heads`. Non-vacuous: adding
  `# noon` in `day_heads` failed it, reverted.
- **u3** `critical_served` (`measures.py`, 0.8, `mini.critical_served@1`; `CriticalServed` adapter; port
  `service_hours`, SQL `_SERVICE_HEADS`); register `critical_served`; `DayFacts.values` (`chain/read.py`);
  `site_outcomes/mini.py` `critical_served()` + `mini_readings(served=...)`: COMPLETE -> "{kwh} kWh not served over
  the whole day", PARTIAL/LOW -> `MG5_PARTIAL` "critical demand not measured over the whole day", else unmeasured.
  The noon depth reads for fuel/service/backup (`_depth`) stay (other board lines use them). CH-6a kpi record:
  noted for CH-6a. Tests: `tests/test_ch9_measures.py` (L0 truth tables), `test_out_d4_board.py` MG-5 (owned),
  `test_ch1b_register.py` all-of-site (+critical_served).
- **MD-0 Q1** `mechanism-v1.json` `busy_noon.window_local` 06:00-18:00 + `window_label` `CH9-R2:Q1`;
  `tests/mechanism_dataset.py` uses it; `test_md0_fixture.py` owned change (+ label test). 54 passed.
- Unit runs (all green): ch4_opportunities, w403_opportunity_result, w402_reads, walk1_5, ch9_no_noon, ch9_measures,
  ch1a_reassessment, ch1b_register/drain, ch5a1_board_contract, out_b2/b4/d4, idx_gaps, md0_fixture, event_register.

## Resume order for builder 5
1. Check lane-1 processes; when idle run Postgres files one or two per call: `test_w403_opportunity_worker_postgres.py`,
   `test_w403_opportunity_read_postgres.py`, `test_ch4_opportunity_postgres.py` (value line now "over 1 daylight
   hours"; `study` dict expects `window_hours` 1 for the seeded /1 study), `test_w403_scenarios_postgres.py`,
   `test_w402_reads_postgres.py`, `test_ch1a_snapshot_postgres.py`, `test_ch1b_fix_postgres.py`,
   `test_ch9_daylight_postgres.py`, `test_w403_migration_postgres.py`. Expect exact-shape detail tests to need the
   new `window_hours`/`hours[]` keys (owned) -- never weaken.
2. Frontend: `npx tsc --noEmit`; vitest `src/sites/__tests__/miniDecisions.test.tsx`, `src/estate/__tests__/estateRoots.test.tsx`
   (fixture value_line strings still say "at midday": update to §2 copy), MiniOpportunity tests.
3. u4: L2 test only for `mill-midday` (add the kind to `backend/conversions/demo-story-days-v1.json` kobo kinds:
   `kobo-daytime` v1, `D+0d 03:00`-`D+0d 15:00`, received `D+0d 16:00`, assess build; not scheduled in `sites`),
   prove it resolves (`tools/demo_story_days.py resolve/validate`); Known Deviation (no prepare; owner rule).
4. u5: domain Action "Run the grain mill at midday on sunny days" ACTION_ACCEPTED -> ACTION_APPLIED
   (`chain/lifecycle_run.py:62-67` already maps domain_actions/case_completions); add an L0/L2 proof.
5. MD-0: `status`, rebuild `--budget 540` in parts, L3m `check --threads --variant states` (+close if ensure
   selects it); 0 unexpected; list each changed MD-0 value old -> new (busy days now day-level EXCLUDED; measure key
   renamed; critical_served added).
6. Guards (`tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1`), `git log main` check, packet
   `.agent/review-packet-CH-9.md` per "Packet (per CH9-R2)" plus the items above (scenario incompatibility, dark
   covered day = noon placeholder missing head / measure NO_DATA, MG-5 PARTIAL on 8 h days).

## Status 2026-11-05 (builder 3; stopped at the context cap, no process or DB job left running by me)
Commits on `7e8bb70ad`: `bc08b81d8` (u1-tail), `badd2fbb9` (u2 partial). Not merged with main yet.

### Landed by builder 3
- **u1-tail (`bc08b81d8`).** `mini_depth/rules.py`: `DAY_PRECEDENCE`, pure `day_decision()` (CONFLICT > LIMITED >
  ELIGIBLE(any) > EXCLUDED), `summarize_renewable` counts DAYS by day decision (kW spans over ELIGIBLE hours of
  ELIGIBLE days; one hour/day reads as before). `mini_depth/read.py` `compose_renewable`: a day with any unselected
  hour is a missing day; `requested_days` = distinct days. Without this the renewable page counted hours as days.
- **Owned test change (packet):** `test_w402_reads_postgres.py` `_dark_hours()` seeds one hourly
  `pv_available_power` mean for every other operating hour (24 h default calendar) of each authored day, 0 kW
  (covered, not daylight), so measured daylight = the authored noon hour via the measured path (not the no-PV
  fallback). No assertion changed. `tools/w402_mini_depth_cases.py build_batches(..., extra=())` sequences the
  extras with the variant. New test `test_ch9_measured_day_reads_every_daylight_hour_as_one_day` (2 daylight hours
  on day 1 -> 2 windows, 6 rows, cards count days). **File run: 7 passed (505 s).**
- **u2 partial (`badd2fbb9`).** `mini_decisions/projection.py`: `day_heads(..., cutoff=None)` gives one
  `DayHead` per expected study hour (`daylight_hours` daylight + missing; noon when no binding; a day with neither
  keeps one missing noon head -> missing day, **record in packet**); `_head()`; `selected_hours` one pin per hour
  ordered `(day, start)`; `day_row` is now the per-hour copier; new `_fold_day` (missing hour -> missing day;
  ELIGIBLE day `opportunity_kwh` = sum of ELIGIBLE hours, `window_hours` = their count, 0 for non-eligible, None
  missing; constraints union in CONSTRAINT_CODES order; adds `hours[]`); `frozen_result` adds result
  `window_hours` = min over eligible days, headroom = `headroom_on_every_eligible_day` over every ELIGIBLE hour of
  ELIGIBLE days. `worker._changed` passes `self._scan_at(c)` as cutoff (`_project` uses DB now).
  `test_w403_opportunity_result.py`: exact-shape test updated (owned: adds `window_hours`/`hours`, values same) and
  new L0 `test_ch9_day_folds_its_daylight_hours` (= the **CH9-R2:Q1 per-hour L0 proof**: busy hour -> day ELIGIBLE,
  window_hours 3->2, hour EXCLUDED CHARGE_OBLIGATION_ACTIVE). L0: 56 passed (w403 result, ch4 opportunities,
  w402 reads).

## Resume order for builder 4
1. **Version bump** `OPPORTUNITY_MODEL_VERSION` -> `mini-opportunity/2` (`mini_decisions/store.py:32`). Ripple to
   decide/implement: reads filter `model_version = :v` (`store.py:364,386,415` `opportunity_roots`): "/1 stays
   readable, branched on model_version" -> roots read must accept both and prefer /2 for the same study (frontend
   `MiniOpportunity.tsx:28,417` picks exactly one study); `test_w403_*_postgres.py` and
   `test_ch4_opportunity_postgres.py` literal "/1" (seeded /1 rows are legitimate /1 history; worker test
   `test_w403_opportunity_worker_postgres.py:93,126` expects the produced version -> /2).
2. `read.py read_selected_renewable_basis` (~:515, `local_noon`) and its consumers `mini_decisions/opportunities.py
   :317-345` (pins zipped with basis rows; now several pins per day) and `scenarios.py:333,381` (`by_day`).
   Remove `window_hours: 1` at `chain/opportunities.py:120`, `mini_decisions/opportunities.py:395` (read result
   `window_hours`, default 1 for a /1 result).
3. Measure `daylight_headroom_kw` (sheet u2 list), event register, then the "no noon literal" test over the five
   readers (reconcile, hour_windows, read_selected_renewable_basis, day_heads, measure). Note `projection.py` still
   says "noon" in `day_row` integrity messages (:150-156) and docstrings; reword so the test can be strict.
4. u3 (`critical_served`, `site_outcomes/mini.py:561`), u4 L2 test only (Known Deviation), u5, MD-0 Q1 fixture
   (`mechanism-v1.json` `busy_noon` 06:00-18:00, label `CH9-R2:Q1`; L0 proof already landed), then MD-0 status /
   rebuild `--budget 540` in parts / L3m states (+close if ensure selects it), guards, packet, `git log main` check.
5. Postgres files to re-run after 1-2: `test_w403_opportunity_worker_postgres.py`,
   `test_w403_opportunity_read_postgres.py`, `test_ch4_opportunity_postgres.py`, `test_md0_mechanism_postgres.py`
   (one or two per call; ~3.5-8 min each). A lane-1 `chain_coherence.py collect` on `assetops_mechanism_test` was
   running (PIDs 12956/22516, not mine) at 2026-11-05; check before any MD-0 job.


## Status 2026-11-05 (builder 2)
- Commit `a116d2931` (on `3211e1c8e`): u1 core. Stopped at the context cap; no DB job or process left running by me.
- Coordinator ruling (owner rule): **no demo prepare of any kind**. Prove `mill-midday` with an L2 test and record
  it as a Known Deviation in the packet (real story day proved at end-game E3). u4 below is amended accordingly.
- **Migration head correction:** main's head at branch time is `0044_chain_events` (0044 re-points onto 0045), so
  `0046.down_revision = "0044_chain_events"`, not 0045.

### Landed in u1 (anchors)
- `backend/migrations/versions/0046_daylight_enqueue.py`: new SQL helper `mini_renewable_hour(t, s, lo, hi, tz)`
  (no pv binding overlapping the hour -> local 12 only; else a positive accepted pv reading overlapping the hour).
  The three 0029 bodies are loaded from 0029's own module text and text-patched (3 exact replacements, each
  asserted once); downgrade re-creates the 0029 bodies and drops the helper.
- `B/mini_depth/rules.py` end: pure `classify_daylight(windows, readings) -> (daylight, missing)` via `series`
  (gap or unusable row = missing; every segment > 0 = daylight).
- `B/mini_depth/store.py` end: `DaylightHours(hours, missing, measured)`, `NOON_HOURS`, `daylight_hours(c, t, s,
  day, k)`: expected hours = `chain.grading.period_bounds(calendar.entry_for(site_code), tz, day,
  PERIOD_OPERATING_HOURS)` (the shared period helper for `critical_served`); binding read as known at k.
- `worker.py` reconcile uses `daylight_hours(...).hours`; `RENEWABLE_LOCAL_HOUR` removed.
- `read.py` `hour_windows(..., daylight=callable)` returns each day's daylight + missing hours; `_read` passes
  `lambda d: daylight_hours(c, t, s, d, known)`.
- Tests: `backend/tests/test_ch9_daylight_postgres.py` (6 pass); `test_w402_migration_postgres.py` gains fixture
  `mg4_nopv` (pv bindings relabelled away) used by the 3 noon-enqueue tests (20 pass together).

### Not done in u1 (do first)
- `read.py` `read_selected_renewable_basis` (`:~515`, still `local_noon`): coupled to the study shape, do with u2.
  Its consumers zip basis rows with pins: `mini_decisions/opportunities.py:327-345` and `scenarios.py:333,381`
  (`by_day` keyed by local_day). Suggested: take explicit `windows` (from `/2` pins, one per daylight hour) and
  return per-hour rows; `/1` keeps noon by `model_version`.
- `B/mini_decisions/projection.py:82` and `site_outcomes/mini.py:561` still use `local_noon` (u2 / u3).
- Adjacent tests run at stop: see "Adjacent run" below.

## Original handoff (pre-flight, builder 1)

Worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch9`, branch `task/CH-9-measured-daylight`, base main `692e4d57e`.
Commits: `5af83b877` pre-flight. No product code, no DB touched, no process left running.
Why stopped: the pre-flight survey used most of the first agent's context, and the 5-unit build needs a fresh one.

## Read first (only these)
- plan2 `.agent/build-sheet-CH-9.md` §9 (OWN-1104) and **§10 CH9-R2 (wins on conflict)**; §2 copy; §5 ladder.
- `.agent/CH-9-preflight.md` (this worktree): every `path:line` anchor below is already verified there.

## Build order (ladder L0 -> L4, localised tests only)
1. **u1: 0046 + daylight helper.**
   - New `backend/migrations/versions/0046_daylight_enqueue.py`, with `down_revision` = `0044_chain_events` (corrected).
   - It does `CREATE OR REPLACE` on the three 0029 functions (`0029_w4_mini_depth.py:190,257,295`; copy their bodies from `:165-310`). Changes:
     - renewable work is enqueued for an hour holding an accepted `pv_available_power` reading > 0;
     - the late-feeder case: any renewable-role reading in such an hour also enqueues;
     - a Site with no in-force `pv_available_power` binding keeps noon;
     - `:190` refuses an hour with no positive reading.
   - The downgrade restores the 0029 bodies.
   - One period helper: the declared operating hours from `config/chain/operating-calendar-v1.json` (Kobo 24 h). `critical_served` shares it.
   - One function, `daylight_hours(site, day, cutoff)`, in `B/mini_depth/store.py` (or a new pure module plus a store query). It implements the §10 Q2/Q3 rules:
     - an hour not fully covered by pv readings (clipped union, `rules._coverage`, `received_at <= k`) is a missing hour;
     - daylight hours are the fully covered hours with every overlapping reading > 0;
     - it returns `(hours, missing)`;
     - a Site with no binding gets `(12,)`.
   - Replace `worker.py:35,117` and `read.py:98-117` (`hour_windows`), and `read.py:510` (`read_selected_renewable_basis`).
   - Test L2: `backend/tests/test_ch9_daylight_postgres.py` on `pg_harness.fresh_database()`.
2. **u2: R4 study `/2` (Q5 shape) and the measure.**
   - Study: `B/mini_decisions/projection.py:78-195` (`day_heads`, `day_row`, `frozen_result`) and `store.py:337` (`renewable_noon_heads` becomes per-day hour heads). Bump `OPPORTUNITY_MODEL_VERSION` to `/2`; `/1` stays readable, branched on `model_version`.
   - Day decision: CONFLICT > LIMITED > ELIGIBLE(any) > EXCLUDED; any missing hour makes the day missing.
   - Day headroom: `headroom_on_every_eligible_day` (`rules.py:400`) over the eligible hours; `window_hours` = eligible hours, minimum over eligible days.
   - Remove the hard-coded `window_hours: 1` at `B/chain/opportunities.py:120` and `B/mini_decisions/opportunities.py:395`.
   - Measure: `daylight_headroom_kw` replaces `noon_headroom_kw` (`B/chain/measures.py:48`, `PERIOD_MIDDAY` in `policy.py:20-27`; adapter `measure_impls.py:164-193`, reader `chain/adapters/postgres_chain_inputs.py:217,283` + `ports.py:145,161`).
   - Event register: `config/chain/event-register-v1.yaml:24` and `tools/checks/test_event_register.py:139,161`.
   - Add an AST/grep test that no noon or daylight literal remains in the five readers (Q4).
3. **u3: R9 `critical_served`.**
   - Adapter `mini.critical_served@1`, which sums the stored hourly `mini_service` heads at the cutoff (Q7). An hour with no head counts as uncovered.
   - Threshold 0.8. Value `{served_kwh, demand_kwh, unserved_kwh}`.
   - Delete the noon MG-5 read at `B/site_outcomes/mini.py:561,583-586`; MG-5 reads the measure. Word the basis as "over the whole day".
   - CH-6a is not on main, so the `kpi` record is noted for CH-6a.
4. **u4: R7 story kind.**
   - `mill-midday` in `backend/conversions/demo-story-days-v1.json`: `kobo-daytime` v1, start `D+0d 03:00`, end `D+0d 15:00`, received `D+0d 16:00`.
   - The partial prepare proves the kind, the measured daylight hours (expected 12; report actual) and the Action. The study class is proven at L2m.
   - **Conflict to raise:** the owner's message forbids "demo prepare". Ask the coordinator whether the §4.4 trimmed partial prepare is allowed. If it isn't, prove the kind with an L2 test only, and record it as a Known Deviation.
5. **u5: Action and copy.**
   - The domain Action "Run the grain mill at midday on sunny days" reaches ACTION_ACCEPTED -> ACTION_APPLIED (`B/chain/lifecycle_run.py:62-67`).
   - `VALUE_LINE` at `B/chain/vocabulary.py:17-18` becomes the §2 text "{lo}–{hi} kW over {h} daylight hours on every eligible day".
   - Frontend: `frontend/src/sites/MiniOpportunity.tsx:115-130`; vitest related.
6. **MD-0 (Q1).**
   - In `backend/conversions/mechanism-v1.json`, `noon.busy_noon` gets a request window 06:00-18:00, labelled `CH9-R2:Q1`. `backend/tests/mechanism_dataset.py:400-415` reads `busy_lo/busy_hi`; check where they come from.
   - L0 proof: one busy hour among eligible hours gives an ELIGIBLE day with `window_hours` reduced by one.
   - Then run MD-0 L3m: `status`, then a rebuild with `--budget 540` in parts, then `check --threads --variant states`, expecting 0 unexpected. List every MD-0 value that changes, old -> new.

## Rules (unchanged)
- No full suite, no `test_demo_combined_postgres`.
- `*_test` DBs only; never `assetops_demo3_full_test`.
- One heavy DB job at a time: check for `mechanism_dataset.py`/`chain_clone.py` processes first.
- Python: plan2 `.venv`, with an absolute PYTHONPATH of the worktree's `backend;contracts;tools;simulator;gateway;host;field`.
- `git add -f` for `.agent/`. Don't merge.

## Packet (per CH9-R2)
- Every client-visible change.
- Every study or thread state that changes on the polish clone. Today's 8-hour Kobo story days become missing study days and MG-5 is PARTIAL on them; these are owned `expected-today.json` changes, owner DD-1.
- Mini-depth job growth against the CH-1b stage bound.
- Lane-1 conflicts in `chain/vocabulary.py` and `site_outcomes/mini.py` are resolved by whichever slice merges second.

## Adjacent run (at `a116d2931`, 2026-11-05)
`run-host-tests.ps1 -- test_w402_reads_postgres.py test_w402_mini_stage_postgres.py test_w402_replay_selection_postgres.py
test_w402_reads.py test_walk1_5_solar_window.py`: **2 failed, 42 passed** (763 s; long, so run these one file at a time).
- `test_w402_reads_postgres.py::test_renewable_composes_five_selected_days`: the renewable page now returns 120
  windows (24 operating hours x 5 days) instead of 5 noon windows, because the fixture Site binds
  `pv_available_power` but holds pv rows only 08:00-08:30Z, so every other operating hour is missing (Q2).
- `test_w402_reads_postgres.py::test_published_authored_batches_select_authored_demonstration`: status UNKNOWN
  instead of SUPPORTED, same cause (missing hours -> missing day).
Both are the ruled Q2 consequence, not a defect. Fix as owned test changes: run those two tests on `mg4_nopv`-style
relabelling (pv bindings away -> noon, which is what they test), or seed full-day pv rows; then add one page-read
case for a measured day. Do not change the rule.

## Resume order for builder 3
1. Fix the two w402 read tests above; re-run that file alone.
2. u2 (with `read_selected_renewable_basis`), u3, u4 (L2 test only, Known Deviation), u5, MD-0 Q1, L3m, guards,
   packet, per the original order below.
