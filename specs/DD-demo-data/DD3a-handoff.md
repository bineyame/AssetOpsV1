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
