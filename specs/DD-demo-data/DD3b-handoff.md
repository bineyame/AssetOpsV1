# DD3b handoff (PARTIAL: DD3b1 fix round done; DD3b2 writer and model steps 1-7 done; DD3b2 steps 8-9 and DD3b3 not started)

Branch `task/DD3b-mini-plant`, worktree `/opt/assetecon/AssetOpsV1-dd3b`, main merged up to D-DD.146. Packet:
`packet-DD3b.md` (DD3b1 + the parts below). Stopped at the context budget.

## Done

- **DD3b1 fix round (D-DD.145):** `test_mini_grid_v9.py` gains `test_the_requested_generator_power_is_never_negative`
  and `test_a_fuel_limited_segment_never_burns_more_than_the_tank` (commit `DD3b1 fix`). Both test behaviour already
  built, so each was shown failing by a plant (packet "Plants" 3 and 4). The pack is unchanged. The event-stamp and
  `conditions` lag line are the writer's and are still to do (below).
- **DD3b2 part 1 (D-DD.128):** Kisiwa's and Mto's kit in `backend/tests/fixtures/on1/lakeside-power.onboarding.json`
  (no-load 4.8 / 2.4 L/h, minimum load 30 %, taper 95 %, each with a `-basis` GENERIC_DEFAULT, SITE, v1;
  `pv-array-share` 100 % Kisiwa, 50/50 Mto, with a `pv-array-share-basis` GENERIC_DEFAULT); every tank's rating is
  its capacity (2500/5000/1000 L). `pv-array-share` and its basis are new members of `COMPONENT_PROPERTY_DEFINITIONS`
  (unit %, INVERTER) with `foundation_property` words and statement cases. Tests: `simulator/tests/world/
  test_dd3b2_units.py` (3, failed 3/3 on the old file). Lakeside's F digest re-pinned in `test_dd3_site_inputs_cli.py`.

- **DD3b2 steps 1-7 (this run, `08edaab94`, `71badcc41`, packet section "DD3b2 writer and model steps"):** per-unit
  `NEEDS`, v8/v9 by Site, unit attachments and states, `UNIT_EVENTS` + `M` parity, the state-row stamp, the lag line,
  per-unit ledger, Kobo-only season sun, D-DD.97 shape + basis, D-DD.104 warm-up + `conditions.start_soc`, the
  D-DD.129 defaults refused, `unbound` F list. `test_dd3b2_units.py` 19 pass (16 shown failing first); simulator
  reach 222 passed. Kobo moved exactly to D-DD.97's projection (packet "Moved figures"). C-DD21 kept on Kobo's v8
  rows (it would fail on the v9-only `pv-array-share` row otherwise).

## Next (DD3b2 rest, in this order)

8. `tools/dd_check.py`: C-DD6 clauses gain `evidence` (event/state/power) per D-DD.146; Kisiwa (state, `gen-ks-01-
   controller` `status` FAILED from 18:40) and Mto (power: `inv-mt-02-controller` `ac-power` 0 from the 11:00 step to
   span end, irradiance > 0 and INV-MT-01 > 0 at that step, > 0 the step before; detail says 11:02 is the O&M
   record's) live, both removed from `PENDING`. Tests on the writer's rows: one-day runs as in
   `test_dd3b2_units.py` `_run` (Kisiwa 30 Oct, Mto 28 Oct; 14-17 Aug as information). D-DD.132 `--pure DIR`
   (C-DD8, C-DD17 pure, C-DD20 Kisiwa/Mto; `--database-url` then optional). C-DD21's v9 row on Kisiwa (the writer's
   `frozen_inputs` for Kisiwa: `pv-array-share@pv-inverter` = (1, "1", FRACTION) and each unit answered); the
   filter `n.version in (None, 8)` is already in.
9. `tools/dd3_pure_run.py --site CODE` (Kobo only today) and the Kisiwa/Mto pure runs; exports by
   `python tools/world_history.py exports --manifest <M> --out <scratch>/bk --tenant lakeside-power` (seconds).
   Then the one `--db-lane` reach run (pre-flight §4 DD3b list + `test_dd3b2_units.py` + `test_sc1_statements.py` +
   `test_dd1_onboarding_postgres.py`) and the host tests that import the writer (`host/tests/test_0k4c_season_v2.py`,
   `test_kernel_forcing_index_parity.py`): not yet run this run. Cite `.agent/main-baseline/` for main.

## Risks

- The new property keys reach the DB onboarding path (`test_dd1_onboarding_postgres.py`), not yet run on Postgres.
- `/1` file left unchanged: it carries no properties for any Site and the writer SKIPs `/1` (Known Deviations 5).
- The warm-up adds one simulated day per `frozen_inputs` call (about 1 s on Kobo).
- Host tests importing the writer (season v2 constants, forcing index parity) were not run this run.
