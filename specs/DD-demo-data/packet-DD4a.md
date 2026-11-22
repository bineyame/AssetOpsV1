# Review packet: DD4a cold operating reality, part 1 (STOPPED FOR THE OWNER at C-DD6)

Branch `task/DD4-cold-ev-reality`; spec `spec.md` §4.4, §7 DD4; rulings D-DD.81-88 (DD4a change list and order).
USER_REVIEW_REQUIRED: true (C-DD6's B-1031 clause fails on the declared room; story figures vs room figures is the owner's call).

## Outcome
Cold-thermal 2 completed per D-DD.87, D-DD.83, D-DD.85 (pack part), the ledger received in lots (D-DD.85), and
`ColdSiteRun` on D-DD.81's protocol with D-DD.86's forcings. The join (step 5) is not built: DD3a is not on main.

## Files
- `simulator/assetops_simulator/packs/cold.py`: `temperature_quantum` + `rounding_total` (residual books it);
  `start_failure_at_request`; `GENERATOR_HAND_START` (FAILED -> RUNNING, OPERATOR, transfer after its delay),
  `GENERATOR_RESET` removed; pulse carries its admission ambient, field-heat guard.
- `simulator/assetops_simulator/world/exports_cold.py`: `Batch.ins` lots, per-lot crate-days/presence, `_named` lots,
  `_fill` on free receiving times (08:00/16:00) with the ruled key, `EMU_RECEIVING <site> <month>`, `in-k` Movement ids
  for multi-lot batches, November shifts lots.
- `simulator/assetops_simulator/world/telemetry_cold.py` (new): `ColdSiteRun`, `cold_parameters`, `day_ambient`.
- Tests: `test_cold_thermal2.py` (+7, 2 reset tests replaced), `world/test_dd4_cold_receiving.py` (3, new),
  `world/test_dd4_telemetry_cold.py` (8, new), `test_dd2b_cold.py` / `test_dd4_cold_ledger.py` (read lots).
- Goldens: `books_support.PINNED_COLD_EV` cold ledger + invoicing only; `backend/conversions/profiles/cold-storage-
  {ledger,invoicing}-illustrative.{sample.csv,expected.json}` via `--update-golden`.

## Acceptance (ruling tests)
- D-DD.87: zero-terms v1 digest unchanged; every step's temperature denominator divides 10^6; residual holds and fails
  without the booked rounding; 6 h exact vs grid agree within 1e-5 degC (see deviation 1). Timing: one room 7 days
  1.3 s (0.19 s/day); Thika 123 days through `ColdSiteRun` 23.9 s. Stop rule (15 min) not reached.
- D-DD.83: failure in the request minute; flag False keeps the 5-minute timeout; hand start runs at its minute, bus
  powered one minute later; hand start while STOPPED raises; reset is gone.
- D-DD.85: one IN per receiving time, <= 40 crates, all at 08:00/16:00; named lots exactly as ruled (B-1029 20+40,
  B-1031 3x40 from 30 Sep 08:00, B-1034 2x40 on 29 Sep); `EMU_RECEIVING`; guard raises at chamber >= produce. Cold
  month crate-days/revenue/received unchanged (C-DD3/C-DD4 tests green); mini and EV pins unchanged.
- D-DD.86: AMBIENT at local midnights after day 1 (24.8 / 24 values), EFFICIENCY at first minute and month change.

## C-DD6 measurement (the stop)
Thika, fixture-view ledger, span 1 Jul-31 Oct, events GRID_LOSS + GENERATOR_FAILURE 19:11, HAND_START 19:14, RESTORE
22:00. Request and FAILED at 19:11, OPERATOR start 19:14, bus powered 19:15. The compressor was OFF at 19:11 (chamber
3.34 degC, cycling 2-4 degC); 19:11-19:16 adds ~0.15 degC. Peak per-minute chamber in 18:30-23:00: **4.049 degC at
21:20**; **minutes above 5 degC on 6 Oct: 0** (above 4 degC: 35, ordinary cycling). B-1031's whole stay: max probe
4.124 degC (6 Oct 11:10), 0 readings above 5 degC; span max 4.166 degC. The clause fails as D-DD.83 predicted;
nothing was changed. Script: scratch, not committed.

## Checks
- Touched-module tests, one heavy slot per tree (sim and backend in separate pytest calls: shared `conftest` name):
  branch d1b765db2: sim 269 passed, backend 85 passed, wall 35 s; main dd04e8d0f: sim 241 passed, backend 85 passed,
  wall 32 s. Difference 28 = the DD4 test files not on main (thermal2 15, ledger 2, receiving 3, telemetry 8).
- `tools/check-architecture.ps1`: passed (1 min 48 s). `tools/check-agent-workflow.ps1`: passed.
- `statement_catalogue.py` and `--self-test`: exit 1 on branch AND main with identical output (pre-existing
  `CASE_MISSING decision_lever.title fuel_reconciliation` etc.; no file of this slice involved).
- Layout evidence: not run (no UI).

## Known deviations
1. D-DD.87's "identical probe readings to the thousandth": rounding both to 0.001 differs at 1 of 73 readings (exact
   3.3254983 sits 1.7e-6 from a half-thousandth); the test asserts max |exact - grid| < 1e-5 (measured 2.9e-6).
2. One door cycle per movement instant (several OUTs, or an OUT and an IN, share 16:00; two DOOR_OPENs would raise).
3. Event rows: value `"<KIND> <OUTCOME> <ACTOR>"`, unit `event` (no ruling fixes event rows; the join decides).
4. Initial state: chamber at control low, crates = net movements before `first`, no field heat carried (not ruled).
5. No season is declared for June or November: `day_ambient` refuses `TEL_FOUNDATION`, so the run cannot start at the
   first June movement or reach 6 Nov until the Architect declares one. Measurement span therefore 1 Jul-31 Oct.
6. D-DD.87's EV denominator check is left to DD4b.

## Residual risk / review focus
`_fill` key and free-slot search; `presence_by_date` per-lot rewrite; day boundary handling of the last interval mean
(closing read without next-day forcings); refusal codes as message first word (replaced at the join).
