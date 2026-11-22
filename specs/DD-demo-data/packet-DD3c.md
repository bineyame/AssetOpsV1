# DD3c review packet (DD3.4 unit roles in the readers; `task/DD3c-unit-roles`)

Spec `specs/DD-demo-data/spec.md` §7 DD3.4; rulings D-DD.108-118 (`rulings.md`), D-DD.116's five parts. Session notes,
anchors and every run: `DD3c-handoff.md`. `USER_REVIEW_REQUIRED: true` (analytics: multi-unit sums, the night note's
blended figure); merges on review ACCEPT, the owner sees it at the product-shape walkthrough.

## Outcome
Every Site-figure reader takes a Site's units through one rule (`sites/unit_roles.py`): one `minigrid-roles-4` or
`minigrid-roles-5` set opens every mini-depth gate, and Kisiwa (two generators) and Mto (two inverters) give summed Site
figures where today they refuse; Kobo now publishes under roles-5 with its stored product outputs equal to roles-4.

## Files changed (by part)
1. `sites/unit_roles.py` (state D-DD.111, installed/available rating D-DD.112, lead policy D-DD.43);
   `tests/test_dd3c_unit_roles.py` (39).
2. `migrations/versions/0074_unit_role_sets.py`, `sites/binding_roles.MINI_DEPTH_ROLE_SETS`, `mini_depth/{store,inputs,
   read}.py`, `structure/energy` hour reads, `assessment_worker.ROLES_BY_SET`; `test_dd3c_role_sets_postgres.py`
   (T1-T5, T7, P1-P4), `test_dd3c_migration_0074.py` (T6, P5), golden `fixtures/dd3c/role-sets-golden.json` (main).
3. `fuel_balance/{rules,service,night_text}.py` (D-DD.117), `analytics/dispatch_v3.py`, `postgres_assessment_store`
   (lead policy, fuel-balance foundation ids), `actions/{verification,verification_rules,trial_fuel_comparison}.py`,
   `runs/replay_series.py` (D-DD.118); tests `test_dd3c_{fuel_balance_units,readers_units,cost_check_units}.py`,
   one-unit goldens `fixtures/dd3c/{fuel-balance-one-unit,kobo-one-unit}-golden.json` (captured on main first).
4. `structure/litres/{rules,inputs}.py` (D-DD.113); `test_dd3c_litres_units.py` (6).
5. `conversions/world/KOBO-001-bindings.json` `role_set` -> `minigrid-roles-5` (09e958005); pins
   `test_dd1_operator_files.py`, `test_dd1_onboarding_postgres.py`, `simulator/tests/world/test_dd3_telemetry.py`;
   parity `test_dd3c_kobo_parity_postgres.py` (2f5a91e10).

## Acceptance, one by one
- D-DD.111/112 state and ratings: 39 unit tests; plants (empty sum, RUNNING after absent) fail, reverted.
- D-DD.109 gates and readers: T1/T4 pass on main (parity), T2/T3/T5/T7/P1-P5/T6 fail on main and pass here; SQL plant
  (roles-5 dropped from 0074's list) fails T2 and T5.
- D-DD.117 fuel balance: one unit byte-identical (golden); two units on their own SFCs; plants fail.
- D-DD.118 readers: dispatch pv summed, minimum-runtime from the lead unit, verification and replay over units; one-unit
  Kobo golden byte-equal after parts 3-4; plants fail. `fuel_basis` grep: reached only by `main.py:418` (ingestion
  listener); `load_world_inputs.py` and `evidence/bulk_load.py` have no hit; backlog line is the coordinator's.
- D-DD.113 litres per unit: 6 tests; plants (one curve, first unit's window) fail.
- D-DD.114 Kobo move and parity: `test_dd3c_kobo_parity_postgres.py` (2f5a91e10): 1 passed, 65 s. Roles-4 and roles-5 worlds
  compared through D-DD.45's normaliser. Plant: +5 L on the roles-5 opening level at 18:00 fails at the fuel_balance
  residuals, as it should. Deviations for the reviewer: (1) evidence ids are rewritten to
  `evidence:<device>/<signal>#<sequence>` and sorted before the normaliser, because random ids reorder the lists;
  (2) `committed_watermark` is masked as wall clock. Weak part: the litres-month parity is weak, all values are
  NOT_AVAILABLE with about 1.5 days loaded. KOBO-001's tank got sensor accuracy 10 L GENERIC_DEFAULT in the onboarding copy only.

## Checks run
- Reach set (84 files by import grep of the touched modules plus the 9 `test_dd3c_*`, 6a/6h migrations, dd1 x3, 4d litres;
  the handoff's 85-file list was not recorded, so this is a reconstruction): one `--db-lane` call. Its pytest summary line was
  lost (the log file was removed from under the run); the progress lines to 88% survived and show failures only in
  `test_3b1_structure_registry`, `test_ch5c2_clock_guard`, `test_k7_kisiwa_story`, `test_pr3_price_entry_postgres` x2. Files after 88%
  and every failing file were rerun in one more `--db-lane` call: 386 items, 380 passed, 6 failed (above five plus
  `test_w403_opportunity_job_isolation_postgres::test_unchanged_fence_tick...`), 634 s. Against `.agent/main-baseline/23d2cd9f6.md`
  (main's failures: ch5c2, w204 TestMigration0023): ch5c2 matches. The other five fail identically at merge-base 0c44ae75b
  (4 files, 5 failed, 184 passed, 145 s), so they are main's own, newer than the baseline. `test_w204_cold_migration` is not in
  this set. The first-run total counts are not available.
- Architecture, agent-workflow: passed. Statement catalogue: exit 0 (OK, 9 adopted, 3 allowed entries).

## Known deviations
1. Pins beyond D-DD.114's three. The role-set name enters the site-inputs bytes (`role_set`, and `foundation_digest`
   is taken over it), so four more world pins moved: `test_telemetry_join_parity.py` (2 tests) and
   `host/tests/test_kernel_forcing_index_parity.py` W1 check main's goldens with Kobo's binding relabelled roles-4 in
   the test (asserting the file says roles-5); `test_dd3_site_inputs_cli.py` `LAKESIDE_ALONE_SHA256` re-pinned
   (old value kept in the comment). A diff of `site_inputs` under both labels shows exactly those two keys.
2. Cost check, multi-unit wire shape (D-DD.117's pattern, the builder's): above one unit only, `windows.*.units`,
   `basis.units`, `sfc: None`, basis `sfc_l_per_kwh`/`no_load_l_per_h` None per window, `no_load = {value_l_per_h:
   None, basis: common basis or None}`; `window_evidence` gains `generator_units` (not in `details`, not in
   `plan_sha256`). No reader shows these keys (`_fuel_value` reads only `priced_total`, `price`, `no_load.basis`).
3. Night note at a multi-unit Site (`night_text._use_note`): the existing USE note over the Site's summed figure, a
   blended L/kWh = sum(loaded L)/sum(kWh) at 3 dp, summed idle minutes at idle L per idle hour, the lead's declared SFC
   when no kWh ran. No new template; the form is the coordinator's named default, to be confirmed.
4. minimum-runtime on a non-lead unit raises `UnitRolesRefused` out of `_configuration` rather than adding a limit
   (D-DD.108 Q6; no new text).
5. The refusal text "v1 assesses one fuel tank and one generator" is kept (no catalogue move); it now fires for zero
   generators or not one tank.
6. KOBO-001's conversion `note` still says "First minigrid-roles-4 binding set", as Kisiwa's and Mto's do (DD1.2
   precedent, ac222ff45, changed `role_set` only).

## Residual risk
- Pre-existing failures on both trees, outside DD3c: `test_ch5c2_clock_guard`, `test_w204_cold_migration::
  TestMigration0023`, `test_pr3_price_entry_postgres` x2, `host/.../test_dd1a2_r3...::test_h1`, `test_w403...
  unchanged_fence_tick`, `test_3b1...leaf_sources...manifest`; `test_evhb_ev_window` flaky once.
- `test_k3::test_a1_parameters_are_f0_verbatim` is order-dependent (imports from `tools/`), also on main.

## Review focus
- `unit_roles.per_asset` deciding when a reader sums (roles-5 PER_ASSET only) vs keeps today's refusal under roles-4.
- Deviations 2 and 3 (wire shape, blended note) and the one-unit byte-identity goldens' capture provenance.
- The part 5 parity's normaliser and which digests were compared directly.
