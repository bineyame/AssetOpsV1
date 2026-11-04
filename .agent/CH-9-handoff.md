# CH-9 handoff (PARTIAL: u1 landed, resume at u1-tail then u2)

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
