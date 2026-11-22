# DD3b handoff (PARTIAL: DD3b1 fix round done; DD3b2 part 1 of the writer done; DD3b2 rest and DD3b3 not started)

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

## Next (DD3b2 rest, in this order; all in `simulator/assetops_simulator/world/telemetry.py` unless named)

1. `NEEDS` gains `per_unit` (GENERATOR unit keys, INVERTER `inverter-ac-limit`) + a v9-only `pv-array-share` need
   (declared %, canonical unit "1", FRACTION, divisor 100: the pack checks 0 < share <= 1). Policy rows from the lead
   unit only (D-DD.43). `_component` refuses >1 only for single-cardinality kinds.
2. `frozen_inputs`: per-unit initial values, GENERATION + FUEL_SUPPLY attachments per generator, PV_SOURCE per
   inverter, `generator-state` STOPPED per generator; on v9 also `inverter-state` AVAILABLE per inverter, model
   version 9. `supported()` per D-DD.129; pack per Site: v8 with one of each (Kobo), else v9 (`PACK` per run, the
   manifest's `pack` from the run).
3. `UNIT_EVENTS` module table (D-DD.126: KISIWA gen-ks-01 FAIL 2026-08-14T19:20, RESTORE 2026-08-17T11:00, FAIL
   2026-10-30T18:40; MTO inv-mt-02 FAIL 2026-10-28T11:02, all +03:00) with an `M` `operations` parity test; forcings
   as one-minute WINDOWs `unit-fail@<unit>` / `unit-restore@<unit>` (shape of `_event` in `test_mini_grid_v9.py`).
   `conditions.unit_events` (instant + source key, information) and the lag line verbatim from D-DD.145.
4. Readings: `_resolve` binds the per-unit roles (generator_power, generator_state, pv_power, pv_available_power) one
   row per unit; the state row of the failing step starts at the instant (D-DD.146; 18:40/19:20/11:00 are step
   starts). Inverter state is not emitted. Ledger: each unit's litres on its own curve, summed (`_curve` per unit).
5. Sun: `SEASON_V2_SUN_SITES = ("KOBO-001",)`; test Kisiwa on 15 Sep = clear x weight.
6. D-DD.97: `LOAD_SHAPE_KW["res"]` = (5, 5, 3, 3, 3, 5, 8, 8, 6, 6, 5, 5, 6, 6, 8, 8, 8, 8, 14, 14, 14, 14, 9, 9) and
   the basis line in `conditions`. D-DD.104: one warm-up day from the lead's stop threshold; `conditions.start_soc`;
   delete `books.get("start_soc", 40)`.
7. D-DD.129 defaults removed (list in the ruling); unbound Site -> `not_written` manifest line.
8. `tools/dd_check.py`: C-DD6 clauses gain `evidence` (event/state/power) per D-DD.146; Kisiwa (state) and Mto (power,
   detail says 11:02 is the O&M record's) live, removed from `PENDING`; D-DD.132 `--pure DIR`; C-DD21's v9 row on Kisiwa.
9. Pure runs Kobo/Kisiwa/Mto (`tools/dd3_pure_run.py` per Site); report Kobo's fuel, candidate, bridge before/after
   (D-DD.97 table: Oct consumption ~628 -> ~634 L, candidate 42.03 -> 24.56 L, bridge ~-52.54 -> ~-30.70; D-DD.104
   moves July 37.39 -> 0 L burned). Re-pin moved goldens by D-DD.93; one `--db-lane` reach run (pre-flight §4 DD3b
   list + `test_dd3b2_units.py` + `test_sc1_statements.py` + `test_dd1_onboarding_postgres.py`).

## Risks

- The new property keys reach the DB onboarding path (`test_dd1_onboarding_postgres.py`), not yet run on Postgres.
- `/1` file left unchanged: it carries no properties for any Site and the writer SKIPs `/1` (Known Deviations 5).
