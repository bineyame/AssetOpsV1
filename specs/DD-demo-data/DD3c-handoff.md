# DD3c handoff (partial: parts 1 and 2 of 5; D-DD.116)

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
- P1-P4 failed on the branch. The cause is the test's construction, not a reader: the test wrote new readings per
  label and took a fresh `now()` cutoff, so the UUID order and the cutoff differed between labels. It is rewritten to
  write once, use one cutoff and read under each label. **The rewrite has NOT been run** (the coordinator closed the
  DB lane). Run it first next time.
- Scope, 81 files (every test importing a touched module, plus the migration tests):
  - Branch 450d5ed58: 1055 passed, 6 failed, 1 skipped, 3880 s.
  - Main 23d2cd9f6, same files without the new-module test: 1008 passed, 10 failed, 4 errors, 3717 s.
  - Failing on both trees: `test_ch5c2_clock_guard` (actions/composition:226) and
    `test_w204_cold_migration::TestMigration0023`.
  - Fixed in 09bd3ba99: T3 test order, the P-read cutoff, and 6h's head pin (now one head, since 0074 follows;
    6a's precedent).
  - `test_evhb_ev_window::test_run_day_records...` failed once on the branch and passed in the rerun (flaky).
- Next: rerun `test_dd3c_role_sets_postgres.py`. Then part 3 (dispatch_v3, verification, replay_series,
  fuel_balance, per-unit checks), part 4 (D-DD.113 litres per unit, `fuel_basis` check), part 5 (Kobo to roles-5,
  D-DD.114). Main holds D-DD.117/.118 for parts 3-5; read them first.
- Risks: T2/T3/T5/T7 relabel the KOBO-001 PowerSite fixture's sets as replica; they do not publish under roles-5
  (part 5 does). The publish reach is the direct `mini_enqueue_configuration` call that publish makes. The
  architecture and agent-workflow checks passed on 450d5ed58.
