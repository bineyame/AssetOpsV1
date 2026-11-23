# DD3c pre-flight: unit roles in the readers (DD3.4, 2.5 u)

Branch `task/DD3c-unit-roles` from main `108af5378`. Spec §7 DD3.4; rulings D-DD.41, D-DD.43, D-DD.44, D-DD.45,
D-DD.70, D-DD.107. One batch, each with the default applied pending the Architect's answer. No BLOCKER.

## Code reality (anchors on main)

- Role-set filters: only `mini_depth` and `structure/energy` select a set, and only roles-4:
  `mini_depth/inputs.py:216,227`, `mini_depth/read.py:220,487`, `mini_depth/store.py:376-386` (`_PV_BOUND`),
  `structure/energy/inputs.py` (via `read.feeder_month`). The SQL gate is 0048's body (0048 re-creates 0029's
  `mini_enqueue_hour`, `mini_enqueue_accepted`, `mini_enqueue_configuration` by text replacement and adds
  `mini_renewable_hour`, both on `role_set = 'minigrid-roles-4'`, `0029:196-205`, `0048:55`).
- Every other listed reader is set-agnostic (`postgres_assessment_store.py:350-360` reads all sets). With two units on
  one role they refuse or degrade; none double-counts today:
  `dispatch_v3.py:201-202,255-257` (pv `MULTIPLE_BINDINGS`), `verification_rules.py:371,419-423`
  (`AMBIGUOUS_BINDING`), `verification.py:1158-1164` (fuel comparison needs one generator),
  `replay_series.py:51,147-160` (`READER_BINDING_CHANGED`), `fuel_balance/service.py:75-79` (`ASSETS_UNSUPPORTED`
  unless one GENERATOR), `mini_depth/inputs.py:207-209,254` (`_one_bound` drops fuel and backup rows),
  `mini_depth/rules.py:223-247` (`any_asset` merge gives CONFLICTING), `mini_depth/projection.py:86,89`.
- Already per unit (Protect reads, D-DD.41 "read the unit series"): `dispatch_v3` generator intervals
  (`:542-545,:680-681`), `finding_episode.py:280,330,447,628,810-821`, `financials/fuel_cost.py:292,317-341`,
  `chain/measure_impls.py:291-308`.
- First-match policy reads, no lead rule, no refusal: `postgres_assessment_store.py:328-335` and `:1383`
  (`minimum-runtime`), `analytics/service.py:43-54` (`fuel_basis`, legacy dispatch-3.1).
- Set tables: the exclusion on `signal_binding_set_revision` is per `(site_id, role_set, range)` (`0002:57-61`), so a
  roles-4 and a roles-5 set can both be current for one Site.
- Kobo: `conversions/world/KOBO-001-bindings.json` (roles-4, one `generator`, one `pv-inverter`, no
  `mini_backup_start_event`). Other Kobo sets stay roles-4 (`kobo-001-minigrid-roles-4-demo-config.json`,
  `mg-w402-001-minigrid-roles-4.json`). Pins: `test_dd1_operator_files.py:17-19,114`,
  `test_dd1_onboarding_postgres.py:27,114-135`, `test_dd1_readiness_parity_postgres.py:34,122`.

## Questions (default applied unless the Architect rules otherwise)

1. **Two sets at once.** A roles-4 and a roles-5 set may both be current (per-set exclusion). Default: "exactly one
   set in force" counts roles-4 and roles-5 together, in Python and SQL; two overlapping sets = no work / the
   reader's existing configuration refusal. No new constraint.
2. **Migration shape.** Default: `0074_unit_role_sets` in 0048's style, replacing the one `role_set = '<roles-4>'`
   text in each of 0048's bodies (and `mini_renewable_hour`) with `IN (roles-4, roles-5)`, each replacement counted
   once; downgrade restores 0048's bodies. No data change.
3. **Which readers aggregate.** Default: the Site-figure readers call `sites/unit_roles.py` whatever the role set
   (one unit gives the unit's value byte for byte, so roles-1..4 output is unchanged): `mini_depth/inputs.py` (power,
   state, backup events, SFC burn, policy), `dispatch_v3` pv and `minimum-runtime` (lead unit), `verification*`
   (the three single-power roles and `generator_state`, fuel comparison per unit summed), `replay_series`
   (`ONE_ASSET_ROLES`), `fuel_balance` (per-unit SFC, Site litres summed, one tank). The per-unit readers listed
   above are left unchanged and get one two-unit test each that they stay per unit.
4. **`generator_state` with a unit absent at a step.** The rule names absence only for power. Default: Site state is
   absent at that step, named by unit (same no-imputation rule), even when another unit runs.
5. **"Non-FAILED" for the rating sum.** Default: per step, from that unit's `generator_state`; a unit with no state
   at the step makes the Site rating absent there. A reader with no step (a Foundation-only read) sums every unit.
6. **Lead-unit refusal code.** D-DD.43 says readers refuse `TEL_FOUNDATION` when a non-lead unit carries a policy
   key. Default: `unit_roles` raises one `UnitRolesRefused(code="TEL_FOUNDATION", unit=...)`; each reader maps it to
   its existing Foundation/configuration refusal (mini_depth `CONFIGURATION_MISSING`, dispatch a limit line), so no
   new user-facing string and `statement_catalogue` stays identical to main.
7. **Absence "named by unit".** Default: the result carries the missing units' asset codes; readers keep their
   current reason codes and text (no new copy), the units go into the existing detail/limit field where one exists.
8. **Event ties.** Union in time order; equal times ordered by the units' declared Foundation order. Default as stated.
9. **Readers not in D-DD.41's list** that also refuse two GENERATORs: `structure/litres/inputs.py:96-98`
   (`NOT_ONE_EACH`), `analytics/service.py:43-54`, `mini_decisions/projection.py:85` (inherits `daylight_hours`,
   fixed by item 3's store change). Default: litres and `fuel_basis` untouched in DD3c (Kisiwa's litres show
   `NOT_ONE_EACH`, an honest absence); logged for the Architect.
10. **Replay on a multi-unit Site.** `replay_study`/`headroom_replay` consume one `ObservedSeries` and v8 `model_needs`
    (`runs/profiles.py:1181-1238`, `runs/models.py:262-275`). Default: `replay_series` builds the Site series through
    `unit_roles`; study/headroom code unchanged (their model needs resolve per lead unit already refuse on two
    matches; v9 replay is not DD3c's).
11. **Kobo's move.** Default: only `conversions/world/KOBO-001-bindings.json` moves to roles-5 (and its three test
    pins); the demo-config and w402 conversions stay roles-4, which the readers still accept. The parity test
    publishes Kobo once under each set on a scratch test DB and compares mini-depth revision digests, the dispatch
    assessment and the fuel balance for one October day.
12. **Size.** Survey: one module, one migration, five Site readers, four per-unit checks, Kobo move and parity.
    Estimate 2.75 u (under D-DD.44's 3 u stop). Parts: (1) `unit_roles.py` pure, with Kobo one-unit parity;
    (2) migration and mini_depth/structure readers; (3) dispatch_v3, verification, replay_series, fuel_balance;
    (4) Kobo to roles-5 and the Postgres product parity.
