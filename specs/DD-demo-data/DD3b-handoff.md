# DD3b handoff (PARTIAL: DD3b1 and DD3b2 done and in_review; DD3b3 not started)

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

- **DD3b2 steps 8-9 (this run, `9133791e3`..`45a74193f`, packet "DD3b2 checks and pure runs"):** C-DD6 evidence
  (Kisiwa state, Mto power) live, out of `PENDING`; `dd_check --pure DIR`; C-DD21's v9 row on Kisiwa (filter plant
  shown failing on `pv-array-share`); `dd3_pure_run.py --site`; Kisiwa/Mto pure runs (bound hit at all three
  Sites); W1 forcing-index case fixed (sun_weights) and its digest regenerated with main's kernel; one `--db-lane`
  reach run (464 + 171/1 failed (W1, fixed, rerun 31 passed) + 217).

## Next (DD3b3)

1. Wait for the Architect on packet Known Deviations 9-11 (`--pure` reading defaults; Kisiwa candidate minutes > 0
   vs OR-MG-2; Kisiwa October unserved 0 vs C-DD20; bound hit at all three Sites).
2. DD3b3: D-DD.92, .130, .131 (notes restated from the pure run so no delivery overfills; M fuel leaves). Then
   `world_history.py telemetry` Jul-Oct for the three Sites (`--books` from `exports` WITHOUT `--tenant`: the
   writer needs every tenant's books) and `python tools/dd_check.py --pure <DIR>`.

## Risks

- The strict writer refuses Kobo's Jul-Oct telemetry from 2026-08-01 (overfill after D-DD.104's 0 L July). Any
  caller that writes Kobo past July fails until DD3b3.
- `--pure` reads month totals for Kisiwa's C-DD20 clause (cannot resolve 17-31 Aug, 1-30 Oct).
- The reach wrapper's own stdout log carried another lane's pytest output; the per-suite logs are this worktree's.
