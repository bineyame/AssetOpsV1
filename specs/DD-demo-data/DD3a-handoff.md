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
