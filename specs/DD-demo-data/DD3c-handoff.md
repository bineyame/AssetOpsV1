# DD3c handoff (partial: parts 1, 2 and part 3's fuel balance, of 5; D-DD.116)

- Done, part 1 (+ D-DD.111, D-DD.112): `backend/assetops_backend/sites/unit_roles.py`. `site_generator_state` states
  RUNNING when any unit with a state runs, else absent (named by unit) while any unit is silent, else D-DD.41's
  cascade. `site_rating` is replaced by `site_installed_rating(components)` and
  `site_available_rating(components, states)`: every unit FAILED gives `Decimal("0")`, no missing units; a silent unit
  gives absent, named; no GENERATOR gives absent. Tests: `backend/tests/test_dd3c_unit_roles.py` (39). Plants, each
  reverted: empty sum returns absent (1 fail); RUNNING checked after the absent check (1 fail).
- Done, part 2 (D-DD.109, D-DD.108 Q1): `migrations/versions/0074_unit_role_sets.py`, built from 0048's texts; each
  replacement counted once; downgrade re-runs 0048's bodies. `sites/binding_roles.MINI_DEPTH_ROLE_SETS`. Reaches:
  SQL gate S1 and renewable hour S2; `store.read_hour_rows` (now `role_sets=`, `= ANY`); `inputs.load_hour_inputs`
  (count spans both names, refusal names both); `read._hour_ids`; `read.feeder_month`; `store._PV_BOUND`/
  `daylight_hours`; `assessment_worker.ROLES_BY_SET` from `SERVED_ROLE_SETS_BY_SITE_TYPE["MINIGRID"]`. Statement
  catalogue: one fingerprint re-hashed (`a:load_hour_inputs` 9583b4388d8a -> 520cb3259def, D-DD.109), exit 0.
- Parity: goldens `backend/tests/fixtures/dd3c/role-sets-golden.json` captured on main 23d2cd9f6 (roles-4), committed
  in e201a8318 before the change. `test_dd3c_role_sets_postgres.py`: T1-T5, T7, plus P1-P4 (in-run roles-4 vs
  roles-5). `test_dd3c_migration_0074.py`: T6, the constant, P5. On main the new tests fail as they should (T2, T3, T5,
  T7, P1-P4, all T6: 10 failed + 4 errors); T1 and T4 pass on main (parity). Branch targeted rerun (09bd3ba99): T1-T5,
  T7 pass. SQL plant (roles-5 dropped from 0074's list, reverted): T2 and T5 fail.
- P1-P4: the rewritten test (write once, one cutoff, read under each label) run alone on d53718c72: `test_dd3c_role_sets_postgres.py` 7 passed, 23.5 s. Part 2 closed.
- Scope, 81 files (every test importing a touched module, plus the migration tests):
  - Branch 450d5ed58: 1055 passed, 6 failed, 1 skipped, 3880 s.
  - Main 23d2cd9f6, same files without the new-module test: 1008 passed, 10 failed, 4 errors, 3717 s.
  - Failing on both trees: `test_ch5c2_clock_guard` (actions/composition:226) and
    `test_w204_cold_migration::TestMigration0023`.
  - Fixed in 09bd3ba99: T3 test order, the P-read cutoff, and 6h's head pin (now one head, since 0074 follows;
    6a's precedent).
  - `test_evhb_ev_window::test_run_day_records...` failed once on the branch and passed in the rerun (flaky).
- Done, part 3a (D-DD.117, fuel balance): `fuel_balance/rules.py` `GeneratorUnit(asset_id, sfc, no_load)`;
  `assess(..., units=...)` and `input_sha256(..., units=...)` replace the generator/sfc/no_load keywords; each unit
  burns on its own SFC and no-load rate, summed (any unit unknown gives unknown; any unit's SFC or rate missing gives
  the existing reason). One unit: byte-identical (golden `backend/tests/fixtures/dd3c/fuel-balance-one-unit-golden.json`,
  four nights, captured from rules equal to main 23d2cd9f6 in 55c32eb77 before the change). Above one unit only:
  `terms.units` (per unit kWh, idle s, loaded L, declared values; top-level sfc/no_load keys None), digest adds
  `generator_asset_ids` and `unit_declared`. `relevant_readings` takes one id or every unit's. `service.py`: one tank
  and at least one GENERATOR; `declared_order` via new adapter read `component_order` (reuses `_REVISIONS`, latest
  revision's components); row `generator_asset_id` = lead. Tests `test_dd3c_fuel_balance_units.py` (14; 14 failed
  first, AttributeError). Plants, reverted: one SFC for both units (f2, f8 fail); lead = last unit (f8 fails).
  `test_k3_fuel_balance_rules.py`: two helper call sites moved to `units=`, assertions untouched.
  `test_a1_parameters_are_f0_verbatim` fails when its file runs alone, also on unchanged code (imports
  `probe_kisiwa_fuel` from `tools/`, on sys.path only when another file puts it there): pre-existing, order-dependent.
- Part 3a targeted run (5990506f6, one `--db` call, 17 files: `test_dd3c_fuel_balance_units`, `test_k3_fuel_*`, `test_k4a_fuel_*`, `test_k5_fuel_*`, `test_k6a_fuel_*`, `test_k6b_fuel_*`, `test_k7_kisiwa_story`, `test_own_g2_fuel_night_*`, `test_ch5c_watermark_postgres`): 316 passed, 0 failed, 523 s wall. Main: these files are in `.agent/main-baseline/23d2cd9f6.md`'s 81-file scope (main's only failures there are ch5c2 and w204), so no main rerun. Architecture check passed; agent-workflow check passed; statement catalogue exit 0.
- D-DD.118 `fuel_basis` grep: `analytics/service.fuel_basis` is reached only by `main.py:418`
  (`ingestion.add_completed_listener(assessments.assess_site)`); `load_world_inputs.py` and `evidence/bulk_load.py`
  have no hit. Backlog line is the coordinator's.
- Next, part 3b-3d (not started; anchors from the survey, branch 5990506f6):
  - `analytics/dispatch_v3.py`: `_Index.lookup` L196-204 gives `MULTIPLE_BINDINGS` (L203); `_evaluate` L398 reads
    PV through `take()`; sum PV per asset like the feeder loop L391-397 through `unit_roles.site_power`. `_slot`
    L256-260 (`len(panels) != 1` -> GAP MULTIPLE_BINDINGS): same. Generators already per unit (`assess` L672-681).
    minimum-runtime: `index.control(CONTROL_MINIMUM_RUNTIME)` L432/L615, loaded in
    `analytics/adapters/postgres_assessment_store.py` L328-335 by `_property(content,"GENERATOR","minimum-runtime")`
    (L213-220, first GENERATOR holding the key): switch to `unit_roles.lead_policy`.
  - `actions/verification_rules.py`: `_SINGLE_POWER_ROLES` L371; `window_evidence` L392+ (`AMBIGUOUS_BINDING` at
    L419-425); slot loop L457-465 (sum per role over units); state `_instant` L489-495 -> `unit_roles.site_generator_state`.
    `actions/verification.py` `_cost_check` ~L1133-1180: `len(generators) != 1` -> empty sfc (L1160/L1163); fuel per
    unit summed into `trial_fuel_comparison.compare` (L180-188).
  - `runs/replay_series.py`: `ONE_ASSET_ROLES` L51; `bound_assets` L145-165 refuses (`READER_BINDING_CHANGED`
    L154-157); `series_from_readings` L276-294 (sum PV and GEN_POWER via `unit_roles.site_power_series`, state via
    `site_generator_state`). Replay study/headroom v8 refusal of two units stays (D-DD.110 Q10).
  - Then part 4 (D-DD.113 litres; `structure/litres/inputs.py:54,96-98`), part 5 (Kobo roles-5, D-DD.114).
- Risks: T2/T3/T5/T7 relabel the KOBO-001 PowerSite fixture's sets as replica; they do not publish under roles-5
  (part 5 does). The publish reach is the direct `mini_enqueue_configuration` call that publish makes. The
  architecture and agent-workflow checks passed on 450d5ed58.
- Risks (part 3a): at a multi-unit Site the night text's use note (`fuel_balance/night_text.py:195-198`) reads the
  top-level `sfc_l_per_kwh`/`no_load_l_per_h`, which are None there (each unit's are in `terms.units`), and
  `analytics/adapters/postgres_assessment_store.py:1643` takes the top-level revision ids only. Neither is in
  D-DD.117's text; one-unit Sites are unaffected. The refusal text "v1 assesses one fuel tank and one generator" is
  kept unchanged (no statement-catalogue move); it now fires for zero generators or not one tank.
