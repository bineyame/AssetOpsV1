# DD3c handoff (partial: parts 1, 2 and 3 of 5, part 3's trial fuel comparison per unit open; D-DD.116)

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
- Done, part 3b-3d (D-DD.118, D-DD.110 Q3/Q10), commits bedf63cff (tests, 12 failed first) and 31abdf4da:
  - `sites/unit_roles.per_asset(role_set, role)`: a reader sums a role only when every binding of it is PER_ASSET in
    its set (roles-5); under a ONE set two assets keep each reader's existing refusal (MULTIPLE_BINDINGS,
    AMBIGUOUS_BINDING, READER_BINDING_CHANGED).
  - `analytics/dispatch_v3.py`: `_Index.unit_assets`/`site_lookup` (PV through `unit_roles.site_power`; an absent
    unit named as `<existing missing text> (asset <id>)`, D-DD.108 Q7); `_slot` sums the PV units' held values.
    minimum-runtime: `postgres_assessment_store._lead_policy_property` (`unit_roles.lead_policy`); a non-lead unit
    holding a policy key raises `UnitRolesRefused` out of `_configuration` (no new text; see open points).
  - `actions/verification_rules.window_evidence(..., unit_roles=...)`: named unit roles reported by several assets
    give the Site slot payload (same keys plus `units`: each unit's payload) through `site_power` and
    `site_generator_state`; idle via `_idle` over the Site state at the slot end. `verification._unit_roles(bound)`
    names the roles PER_ASSET in every bound set. One asset: byte-identical (test).
  - `runs/replay_series.py`: `UNIT_ROLES = (PV, GEN_POWER, GEN_STATE)`; `bound_assets` keeps every unit under
    roles-5; the series sums PV and generator power and states the Site state per step. `replay_study`/headroom v8
    refusal untouched (D-DD.110 Q10).
  - D-DD.117 risks: `night_text._use_note`: at a multi-unit Site the existing USE note over the Site's summed
    figure (summed kWh at sum(loaded L)/sum(kWh), 3 dp; summed idle minutes at idle L per idle hour; lead's
    declared SFC when no kWh ran); no None, no new template (statement catalogue exit 0). `postgres_assessment_store
    ._fuel_balance_foundation_ids(terms)` adds every unit's SFC and no-load revision ids; one unit unchanged.
  - Tests `backend/tests/test_dd3c_readers_units.py` (14). Plants, reverted: sum under roles-4 (2 dispatch tests
    fail), replay first unit only, verification first unit's kWh, night note lead SFC (each its test fails).
  - Checks on 31abdf4da: architecture passed, agent workflow passed, statement catalogue exit 0.
  - Targeted `--db` run (31abdf4da, 66 files: `test_dd3c_*` and every test importing dispatch_v3,
    verification*, replay_series, fuel_balance/, night_text): 1197 passed, 15 failed, 1 skipped, 1429 s. Fixed in
    420dc4a0e: 12 s6 evaluator/holds tests (their window fake took no `unit_roles` keyword; the keyword is now passed
    only when a bound set names a unit role, so the roles-4 call is unchanged) and the replay_series import pin.
    Rerun on 420dc4a0e (s6 x2, 0k3 replay_series, w403, 3b1; same `--db` call as the main check): 134 passed,
    2 failed. Those 2 (`test_w403...unchanged_fence_tick...`, `test_3b1...leaf_sources...manifest`) fail identically
    on main 23d2cd9f6 (detached temp worktree, removed after the run): 82 passed, 2 failed. `test_ch5c2_clock_guard`
    fails as on main (baseline 23d2cd9f6). One-unit Sites (Kobo): every Kobo Postgres pin in the set passes, and the
    pure one-unit identity tests hold.
- Open points for review: (1) the night note's form (summed figure, blended L/kWh) is the default the coordinator
  named, to be confirmed; per-unit terms would need a new catalogued template. (2) minimum-runtime refusal raises
  (the dispatch job fails loud) rather than adding a limit: a limit line would be new text (D-DD.108 Q6).
- Next, part 3 remainder: `actions/verification._cost_check` (L1160-1170) still gives an empty SFC history unless
  exactly one generator (the cost check reads UNAVAILABLE at a two-unit Site, honest absence). D-DD.118 wants the
  fuel comparison per unit summed: needs per-unit `generator_kwh`/idle per window (now in each slot's `units`) and
  `financials/trial_fuel_comparison.compare` taking per-unit SFC/no-load; not built.
  - Then part 4 (D-DD.113 litres; `structure/litres/inputs.py:54,96-98`), part 5 (Kobo roles-5, D-DD.114).
- Risks: T2/T3/T5/T7 relabel the KOBO-001 PowerSite fixture's sets as replica; they do not publish under roles-5
  (part 5 does). The publish reach is the direct `mini_enqueue_configuration` call that publish makes. The
  architecture and agent-workflow checks passed on 450d5ed58.
- Risks (part 3a): at a multi-unit Site the night text's use note (`fuel_balance/night_text.py:195-198`) reads the
  top-level `sfc_l_per_kwh`/`no_load_l_per_h`, which are None there (each unit's are in `terms.units`), and
  `analytics/adapters/postgres_assessment_store.py:1643` takes the top-level revision ids only. Neither is in
  D-DD.117's text; one-unit Sites are unaffected. The refusal text "v1 assesses one fuel tank and one generator" is
  kept unchanged (no statement-catalogue move); it now fires for zero generators or not one tank.
