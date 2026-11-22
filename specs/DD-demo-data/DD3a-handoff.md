# DD3a handoff (PARTIAL; context limit)

Branch `task/DD3a-mini-reality`, worktree `/opt/assetecon/AssetOpsV1-dd3a`, head `3bfe1451d` (base `main` 19c8b2b3b).
Spec `specs/DD-demo-data/spec.md` §7 DD3.1, DD3.2, §4.1, §4.2, §6; rulings D-DD.17, .19, .30, .41, .43, .44.
Owner Q7 is answered: 0.62 L/h, DATASHEET_FIT (`owner/owner-demo-data-answers-2026-11-22.md:8`). Commit 2 may use it.

## Done (commit `3bfe1451d`, "DD3.2 commit 1a")
- `config/datasheets/kobo-equipment.json`: the slot, verbatim from spec §6.
- `tools/datasheet_template.py`: map_slot, fit_intercept (exact least squares), apply, CLI `--check | --write`.
  - Refusals: DATASHEET_CURVE_INVALID, DATASHEET_FIT_MISMATCH, DATASHEET_UNSTATED, DATASHEET_SITE, plus v8's curve
    codes through `generator_curve.fuel_curve`.
  - Residuals printed: 10.50/10.50, 7.80/8.03, 5.60/5.56 (the spec's).
  - `--check` on the committed Lakeside file exits 1, because commit 2 has not been written.
- `sites/models.py`: three `-basis` siblings (definitions, state values, carriers) and DATASHEET_FIT on the no-load basis.
- `i18n/statements/en/foundation.py`: `component_property.basis`, three variants. Cases are in
  `backend/tests/statement_cases/component_property.py`, and T8's key set is extended.
- Tests: `backend/tests/test_dd3_datasheet_template.py` passes 14 of 14. `test_sc1_statements.py` and
  `test_0k4b_properties.py` pass; together with the 14, 420 passed. The tests were shown failing first: ImportError for
  the tool, vocabulary and parse failures for the rest.

## Next
1. **DD3.1 writer** (`simulator/assetops_simulator/world/telemetry.py`, `tools/world_history.py site-inputs` and
   `telemetry`). Code anchors from the survey:
   - Kernel: `S/kernel/execute.py:1880 start()`, `Execution.advance(n)` (~:1784), `:1893 execute()`.
   - Inputs record: `contracts/assetops_contracts/world_inputs.py:270 FrozenWorldInputs`, ForcingInput :143,
     DeclaredCause :171.
   - Template harness: `tools/kobo_replay_study.py:119` and `host/tests/kobo_season.py:120-245` (season v2 forcings
     :84-202; initial values by address :204-212).
   - Load and sun are WINDOW forcings per 5-minute step on `load-demand@load-res|clinic|mill` (kW) and
     `site:plane-of-array-irradiance` (W/m2). A step with no forcing is UNAVAILABLE and the run refuses.
   - Deliveries and the 02:00 draw are DeclaredCause on `fuel-tank-volume@fuel-tank`: INCREASE POINT and DECREASE POINT
     (`tools/probe_kisiwa_fuel.py:177-215`).
   - Overfill caps only with an UPPER DeclaredBound (`execution_adapter.py:225`). Wire it so an overfill is recorded
     and refused as TEL_PACK. An empty tank fails as INTEGRATION_BOUND_FAILURE.
   - Foundation-to-parameter map: `backend/assetops_backend/runs/profiles.py:1180-1230, :1419-1434`.
   - **Chaining (default to record):** v8 cannot start from a RUNNING or STARTING generator
     (`mini_grid.py:93-113`, `execute.py:507-530`). Run ONE continuous execution and `advance(288)` per day, writing
     each day from its boundaries. This equals chaining from the previous day's end state, without the
     STOPPED-at-midnight limit.
   - Public signals and their bindings: `KOBO-001-bindings.json` gives (device_id, signal_id) per role.
     `source_id` = device_id is the default to confirm. No unserved signal is published: unserved energy goes into
     `measured.json` and the manifest from `accepted.loads[].unserved_energy`.
   - Determinism: the kernel has no RNG. Seeds feed only the reporting path.
   - C-DD11 (two processes, same bytes) and C-DD12 (static scan for `oracle` plus TEL_ORACLE_READ) go into
     `tools/dd_check.py`. DD2a also edits that file, so append only.
2. **DD3.2 commit 1b:** the pure run on Kobo, Jul-Oct, at 0.62 and at 3.3. Print per month: delivered, burned, drawn,
   tank min/max, balance, candidate litres.
3. **DD3.2 commit 2:** `tools/datasheet_template.py --write` on Lakeside's `/2` file. Kobo `physical` in the manifest
   (genset_kw 36, sfc 0.2917, battery_kwh 191.5) with a rev note. Then regenerate history.json, the goldens
   (`simulator/tests/world/golden/`), the pinned export digests (`test_3a3_exports.py:142` PINNED) and
   derived-values.json, and re-run check_manifest.py and check_alignment.py (H8_DERIVED_SHA at
   `check_manifest.py:1271`). List every moved figure. C-DD16 goes live in dd_check.
4. Packet `specs/DD-demo-data/packet-DD3a.md`, state entry 201 in `.ai/state/index-3.md`, spec status.

## Defaults taken (for the packet)
- The tool writes property `source` "SITE", `source_version` 1. No new source value (D-DD.17).
- **Kisiwa and Mto are out of DD3a's pure run.** They need v9 (DD3.3), and DD3.1's card is "for Kobo". Their pure run
  under D-DD.19 moves to DD3b, which is still before DD3 merges.
- The basis slots are `optional` name slots. The catalogue's `absent` means an Absent fact, not an omitted slot.

## Risks and Architect questions
- `financials/fuel_cost_v2.py:35 NO_LOAD_BASES` is an immutable model parameter and lacks DATASHEET_FIT, so fuel-cost-2
  would not read Kobo's 0.62 rate.
- `chain/vocabulary.py:117 NO_LOAD_BASIS_WORDS` has no DATASHEET_FIT word, so it falls back to "a declared idle fuel
  rate". Default: leave both untouched; Architect to rule. `fuel_balance/service.py:25` already follows
  STATE_PROPERTY_VALUES, so it admits DATASHEET_FIT.
- DD2a (`task/DD2-books`, not on main) produces the Jul-Sep fuel notes and SOURCE_VERSION "2". The writer's pure run
  needs them as input files: run DD2a's exports from its own checkout, or wait for it to merge. Commit 2's export
  digests depend on DD2a too, so regenerate after both merge.
- The architecture guard and the statement-catalogue guard have not been run yet.


---
# Update 2 (session 2; PARTIAL; context limit). Head after this note: see `git log -1`.

## Done since
- `git merge main` (DD2a and rulings round 8 in). Commit `2e2b697cc`: D-DD.67 and D-DD.68 complete.
  - `fuel_cost_v2.NO_LOAD_BASES` and `NO_LOAD_BASIS_WORDS` carry DATASHEET_FIT; `trial_fuel_comparison.py:69` comment.
  - `backend/tests/test_dd3_no_load_basis_parity.py` (5 tests) plus golden `backend/tests/fixtures/dd3_no_load_basis_parity.json`,
    generated before the change from main's code (this branch's financials/vocabulary were identical to main 80661e824 then).
    Shown failing first: the one-vocabulary test, the AVAILABLE test and the words test failed (KeyError DATASHEET_FIT); the golden test passed.
  - Not yet run: the wider "every test importing a touched module" scope (models.py, fuel_cost_v2, vocabulary), the architecture guard,
    the statement-catalogue guard. Do these before the packet.

## Survey for the writer (all verified this session; saves a re-survey)
- Inputs live in `/2` file `backend/tests/fixtures/on1/lakeside-power.onboarding.json` (`assetops.operator-onboarding/2`; keys
  format, data, operator, sites[code,name,timezone,country,locality,lifecycle,valid_from,components,devices,topology], people).
  Binding rows: `backend/conversions/world/KOBO-001-bindings.json` (`bindings[]`: device_id, signal_id, asset_code, role, canonical_unit;
  roles pv_power, pv_available_power, pv_irradiance, battery_power, battery_soc, pcs_discharge_capability, generator_power,
  generator_state, fuel_level, feeder_demand x3 on residential-meter / clinic-meter / mill-meter).
- A pure writer cannot import `assetops_backend` (simulator package). So it builds `FrozenWorldInputs` itself. The harness
  (`host/tests/kobo_season.py base_run(days, version=8, site_edit=season_site_v2)` + `host/execution_adapter.frozen_world_inputs`)
  gave this shape for Kobo v8 (probe at `/tmp/claude-1001/.../scratchpad/probe1.py`, delete not needed):
  - run_id, execution_contract_version 9, scenario_version 2, model `mini-grid` v8, publication `simulator-lab-publication` v3, seed 20260929.
  - `initial_values` (address; parameter_id; unit; dimension; answered_by): pv-rated-power@pv-array, inverter-ac-limit@pv-inverter,
    battery-energy-capacity@battery, pcs-charge-limit / pcs-discharge-limit / pcs-conversion-efficiency@battery-pcs,
    battery-reserve-state-of-charge@battery (`model-need:<foundation key>`, SITE_FOUNDATION); generator-rated-power,
    generator-specific-fuel-consumption (L/kWh), generator-start-soc-threshold, generator-stop-soc-threshold,
    generator-minimum-runtime (min), generator-start-delay (min), generator-no-load-fuel-rate (**L/min**: 3.3 L/h is 11/200),
    generator-minimum-load, battery-charge-taper-start @generator/@battery; fuel-tank-capacity@fuel-tank;
    scenario ones: battery-state-of-charge@battery (`starting-state-of-charge`, SCENARIO), fuel-tank-volume@fuel-tank (`starting-fuel`).
  - `discrete_initial_values`: generator-state@generator STOPPED (SCENARIO). `bounds` empty (add the UPPER bound on the tank for TEL_PACK overfill).
  - `site_controls`: source-priority (pv-array, battery, generator); critical-load-priority (load-clinic, load-res, load-mill).
  - `bus_attachments`: PV_SOURCE pv-array via pv-inverter, STORAGE battery via battery-pcs, GENERATION generator, loads; bus ac-bus.
  - forcings WINDOW per step: `site:plane-of-array-irradiance` (W/m2) and `load-demand@load-res|load-clinic|load-mill` (kW).
  - model: `host/execution_adapter.model_for(run)` resolves `EXECUTABLE_MODELS`; the pack model is `MINI_GRID_V8_MODEL` in
    `backend/.../runs/profiles.py:1419` (the executable `ModelSpec` lives in `simulator/.../packs/mini_grid.py`).
- Public records (what each device signal reads): publication profile `simulator-lab-publication` (`backend/.../runs/profiles.py:1492-1650`):
  fuel-level-sensor/fuel-level = fuel-tank-volume STATE (L); generator-controller/ac-power = generator-output-power INTERVAL (kW);
  generator-controller/status = generator-state (discrete, text); battery-pcs-controller/state-of-charge = battery-state-of-charge STATE (%);
  battery-pcs-controller/ac-power = battery-ac-power INTERVAL; pv-inverter-controller/ac-power = pv-ac-power INTERVAL;
  residential|clinic|mill-meter/active-power = load-served-power INTERVAL. Value rule: `observation/transform.py:69 world_value`
  (STATE reads `boundary.state_sample(address)`, discrete `boundary.discrete_state`, INTERVAL `interval_measurement / (span/60)`).
  `available-power`, `discharge-capability` and irradiance have their own measures (v2/v3 `_add_*_measures` in `packs/mini_grid.py`).
  The writer calls `world_value`-style reads directly (no dropout, bias or cadence: every 5-minute step), quantised as spec §4.1 says.
- Kernel: `kernel/execute.py:1880 start(inputs, model)`, `Execution.advance(n)`; boundaries are `BoundaryState` (`contracts/.../trajectory.py:240`).

## Next (unchanged order)
1. DD3.1: `simulator/assetops_simulator/world/telemetry.py` (`build_telemetry`), `tools/world_history.py site-inputs|telemetry`, C-DD11/12
   (append to `tools/dd_check.py`), tests: 288x2 == 576 bytes, TEL_BINDING + every Kobo pair resolves to one binding row, TEL_INPUT_TOTAL,
   TEL_PACK on overfill, determinism across two processes.
2. DD3.2 commit 1b (pure run, gate 0.62 and 3.3), commit 2 (the /2 write by `tools/datasheet_template.py --write`, manifest Kobo physical, regenerate).
3. Packet `specs/DD-demo-data/packet-DD3a.md`, state entry in `.ai/state/index-3.md`, spec status.

## Update 3 (guards)
- Scope run (every non-postgres test file importing fuel_cost_v2, vocabulary, sites.models, trial_fuel_comparison): after fixing three
  stale exact-set tests (`test_w205a_ev_vocabulary`, `test_w402_roles_properties`, `test_a3_idle_fuel`) all pass (2059 + 41 re-run).
  Postgres-named files importing them (3) not yet run: `tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- <files>`.
- Architecture guard passes. Statement-catalogue: baseline updated by hand for my 4 new hand-built fingerprints (precedent DD1.2);
  `test_statement_catalogue.py` still fails 2 tests on ONE finding not mine:
  `HAND_BUILT_NEW decisions/adapters/structure_read.py:24 j:GuardedStructureRead.site_inputs:d0bac1208c82` (file identical to main; report to coordinator).
- Still to do: all of "Next" above (writer, C-DD11/12, pure run, commit 2, packet, state entry).

---
# Update 4 (session 3; PARTIAL; context limit). Head: see `git log -1` (commits 2d0a68f3a, then the CLI/dd_check commit).

## Done
- `git merge main` (903ebf0f2): the structure_read baseline failure is gone with main's allow entry.
- **DD3.1 writer**: `simulator/assetops_simulator/world/telemetry.py` (`site_inputs`, `frozen_inputs`, `SiteRun`, `day_file`,
  `build_telemetry`, `books_for`, `measured_for`, `TelemetryRefused` with TEL_FOUNDATION / TEL_INPUT_TOTAL / TEL_BINDING / TEL_PACK /
  TEL_EVENT_UNPLACED / TEL_ORACLE_READ), tests `simulator/tests/world/test_dd3_telemetry.py` (13 pass; shown failing first: ImportError, then 2 failures fixed).
  - Own `NEEDS` table (17 rows). Parity: `tools/dd_check.py` **C-DD21** (writer table vs the backend's frozen Kobo v8 initial values), made to fail by editing a unit.
  - **C-DD11** (two processes, `exports` + `site-inputs` + `telemetry` on a 2-day Kobo window, byte compare) and **C-DD12** (AST scan of
    `world/` and `tools/world_history.py` for the answer block; C-DD12 made to fail by planting a key). C-DD11 needs commit 2's /2 file (curve properties) to run: NOT yet run green.
  - CLI: `tools/world_history.py site-inputs --onboarding DIR --bindings DIR --out F`, `telemetry --manifest --sites --books DIR --out --start --end --site`.
  - `tools/dd3_pure_run.py --books DIR --no-load 0.62|3.3`: the commit 1b table. Applies the datasheet slot in memory (3.3 restates the slot's item as GENERIC_DEFAULT).
    `DIR` = output of `world_history.py exports` (needs `lakeside-power.expenses.csv`).
- Design choices to put in the packet (spec silent): load and sun are **hour-block WINDOW forcings** (96 per day, not 5-minute ones) because
  the kernel scans every forcing at every step (O(forcings x steps)); Wh allocated by largest remainder per (day, feeder, hour) over the month, so month totals are exact;
  load shape = season v2's 2-hour blocks read hourly (`LOAD_SHAPE_KW`), day weight from `history.families.demand.day`; sun = season v2 clear/overcast, overcast calendar indexed from 1 Sep (Jul/Aug all clear);
  critical-load order clinic, res, mill; notes outside the span are skipped; Kobo only (`supported()`); Kisiwa/Mto listed `not_written` in their manifest. Readings: millesimal half-even, one JSON line per row.
  v8 caps burn at the tank (fuel-limited, unserved appears); an empty tank from a declared DRAW fails INTEGRATION_BOUND; overfill = BOUNDED_AND_RECORDED, refused as TEL_PACK (strict) or tabled (pure run).
- Early finding: **Kobo's tank is 400 L (the /2 file) and the notes are 400 L deliveries (3 a month)**; the tank starts at 200 L, so the first note (1 Jul 10:00) already overfills. A 7-day pure run shows refused litres. This is the D-DD.19 / D-DD.70 gate: report to the Architect before DD3a merges. Nothing is tuned.

## Next
1. Read the full-span pure run (`/tmp/claude-1001/.../scratchpad/pure062.txt` may be gone; rerun: `tools/heavy-slot.sh -- python tools/dd3_pure_run.py --books <exports dir>` at 0.62 and `--no-load 3.3`; ~minutes). Record both tables in the packet. Gate figures: 0.62 and 3.3 L/h.
2. Commit 2: `python tools/datasheet_template.py --slot config/datasheets/kobo-equipment.json --onboarding backend/tests/fixtures/on1/lakeside-power.onboarding.json --site KOBO-001 --write`;
   manifest Kobo `physical` (genset_kw 36, sfc 0.2917, battery_kwh 191.5) + rev note; regenerate history.json, goldens (`simulator/tests/world/golden/`), PINNED digests (`test_3a3_exports.py:142`), derived-values.json; check_manifest.py, check_alignment.py (H8_DERIVED_SHA `check_manifest.py:1271`); list every moved figure; C-DD16 live in dd_check. Then C-DD11 green.
   Because the hand-written test fixture `_kobo()` adds the curve properties itself, tests keep passing after commit 2; drop that helper then.
3. Scope run: every test file importing a touched module (telemetry, world_history, dd_check, datasheet_template, sites.models, fuel_cost_v2, vocabulary) incl. the 3 postgres-named files (`tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- <files>`), on branch AND main. Architecture guard (`ASSETOPS_GUARD_PYTHON=/opt/assetecon/AssetOpsV1/.venv/bin/python`), statement-catalogue guard.
4. `specs/DD-demo-data/packet-DD3a.md` (all rounds), state entry + index line (next free number in `.ai/state/index-3.md`), spec Status in_review.

## Update 4 addendum: full-span speed (blocking finding)
The full 123-day Kobo pure run did not finish in over 15 minutes (7 days: 11 s). The kernel scans every forcing at every step
(`kernel/execute.py:1280`), so one continuous execution over the span costs O(steps x forcings) even with hour-block windows (about 11.8k forcings).
Options for the Architect (not taken): (a) a kernel exposure index by offset (protected seam), (b) the writer runs the span in
windows with a hand-off of end state (conflicts with D-DD.69 for RUNNING generators), (c) wider constant windows. Ask before building more.
The pure-run table at 0.62 and 3.3 is therefore NOT produced; commit 1b and commit 2 are not started.

---
# Update 5 (session 4; PARTIAL; D-DD.75 stop rule hit). Head: see `git log -1`.

## Done (D-DD.79 order)
- `git merge main` (05ecb21d4): conflicts resolved in `tools/world_history.py` (telemetry + site-inputs commands kept beside
  D-DD.74 `--tenant`) and `backend/tests/test_sc1_statements.py` (key set holds both `component_property.basis` and 6h's lever keys).
- (1) `e347205d6` parity golden on the unchanged kernel (`git diff main -- simulator/assetops_simulator/kernel` empty):
  `host/tests/test_kernel_forcing_index_parity.py` + `host/tests/fixtures/kernel_forcing_index_parity.json`, cases K1-K8, D1, F1,
  X1, W1, S1; shown failing first (no golden). Regenerate an entry only when its INPUTS move:
  `python host/tests/test_kernel_forcing_index_parity.py --reference main W1` (loads main's `kernel/execute.py` as a separate module).
  Interpretations: K cases use `season_inputs(run, 2)` (= `frozen_world_inputs` + the season's forcings) because the bare frozen
  inputs carry 8 h of sun and every version FAILS at 480 min; K8 adds `assumed_site` (v8 is BLOCKED without it, as 0K4a runs it);
  every case pins `run_id` (a draft's id is random and is in the digest); W1 uses books fixed in the test and sets the tank and
  curve rows itself, so later commits move it only through the writer's rules.
- (2) `776285ae1` lazy `_forcing_index` in `kernel/execute.py` exactly as D-DD.75; parity 14/14 green. Cold/EV: grep confirms
  only `_compute_exposures`' two callers in `execute.py` reach it (`ColdExecution` does not).
  Edge (packet): a zero-length forcing (POINT, or WINDOW of 0) that passes `_excluded` and has a handler made the old loop raise
  `ValueError` from `window_span`; the index skips it (`end <= start`, as ruled). No case reaches it.
- (3) `afce2bd40` D-DD.77 sun: `_sun` in `world/telemetry.py`; books carry `sun_weights` from the view's `solar_surplus` family
  (`DEFAULT_SUN_WEIGHTS` mirrors the manifest); manifest `conditions.sun_outside_calendar`. 3 tests failing first. W1 golden
  regenerated with main's kernel.
- (4) `ab349bb8d` D-DD.76 tanks in the `/2` file: Kisiwa 5000, Kobo 2500, Mto 1000 L, source SITE v1. Inputs printed by a rule
  test: Kisiwa Jul 2397 / Aug 2305 / Sep 2183 / Oct 2400; Kobo 983 / 967 / 1035 / 1180; Mto 314 / 309 / 288 / 320.
  **Deviation:** `lakeside-power.v1.onboarding.json` declares no FUEL_TANK (four rated components a Site, no property rows), so
  there is no tank row to change there; nothing added (would be design). Sweep: 111 pass in the 4 non-Postgres backend files
  reading the `/2` file; `test_dd3_telemetry.py` 17 pass. Architecture guard passes.

## Timings (wall)
- 7-day Kobo pure run: 7.3 s before the index, 5.5 s after, output byte-identical.
- 14 days 15.3 s; 28 days 74.8 s; 123 days at 0.62 L/h (400 L tank, before D-DD.77): over 10 min (stopped at about 10.5 min).
  3.3 not run. **Stop rule hit: no further kernel edit made.**

## cProfile, 28 days (`python -m cProfile tools/dd3_pure_run.py --end 2026-07-28`, 99.7 s), top 15 by tottime
```
         60034538 function calls (60008327 primitive calls) in 99.668 seconds
   249984   53.211    0.000   53.211    0.000 contracts/assetops_contracts/execution_contract.py:1671(point_due_at)
   983860    4.944    0.000    9.434    0.000 simulator/assetops_simulator/packs/minigrid.py:372(_one)
 17956488    4.670    0.000    4.670    0.000 {method 'split' of 'str' objects}
  2082153    2.015    0.000    2.490    0.000 fractions.py:317(_from_coprime_ints)
    72580    1.594    0.000    8.746    0.000 simulator/assetops_simulator/packs/minigrid.py:423(_plant)
  2050217    1.537    0.000    7.789    0.000 fractions.py:613(forward)
     8064    1.472    0.000   12.789    0.002 simulator/assetops_simulator/packs/mini_grid.py:1494(_resolve_cycle)
    64515    1.282    0.000    6.645    0.000 simulator/assetops_simulator/packs/mini_grid.py:266(_generator)
   112900    1.005    0.000    1.268    0.000 simulator/assetops_simulator/kernel/model.py:535(exposures_of)
   901318    1.000    0.000    1.988    0.000 fractions.py:710(_add)
  3331604    0.949    0.000    1.835    0.000 {built-in method builtins.isinstance}
   872930    0.896    0.000    1.126    0.000 fractions.py:186(__new__)
     8067    0.893    0.000    0.893    0.000 contracts/assetops_contracts/world_inputs.py:77(step_starts)
   479544    0.819    0.000    1.220    0.000 {built-in method builtins.sorted}
     8065    0.808    0.000   95.071    0.012 simulator/assetops_simulator/kernel/execute.py:1845(_advance_one)
```
Reading (for the Architect; not acted on): the remaining O(steps^2) term is the same class as D-DD.75, for CAUSES.
`_phase_apply_events` (`kernel/execute.py:1079`, cause loop at ~1100) calls `point_due_at` (`contracts/.../execution_contract.py:1671`,
a linear scan of every step start) for every cause at every boundary: 250k calls, 53 s of 100 at 28 days (fuel notes and one
02:00 draw a day are POINT causes). `interval.step_starts` (`world_inputs.py:77`) is also rebuilt once per boundary (8064 calls).

## Next (blocked on the Architect)
- A ruling on the cause path, then: the 123-day pure run at 0.62 and 3.3 on the 2500 L tank (commit 1b, gates the merge);
  commit 2 (§6: `datasheet_template.py --write`, manifest Kobo `physical` + rev note, regenerate history.json / goldens / PINNED /
  derived-values.json, check_manifest + check_alignment, moved figures, C-DD16, C-DD11 green); scope runs on branch and main incl.
  Postgres files; statement-catalogue guard; packet; state entry (index-3, next free 205).
- Owner Q7 is answered 0.62 L/h (`owner/owner-demo-data-answers-2026-11-22.md`), so commit 2 takes the default.
- Moved figures from D-DD.76 so far: the writer's Kobo tank start (200 to 1250 L) and bound (400 to 2500 L); any run at a Lakeside
  Site now freezes `fuel-tank-capacity` 2500/5000/1000 from the foundation (`runs/profiles.py:910`), which bounds its tank and its
  operational actions (`runs/operational_actions.py:200`). No story figure moves.
