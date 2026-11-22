# Review packet: DD4a cold operating reality, part 1 (run 2: D-DD.90, D-DD.103, the join; C-DD6 still open)

Branch `task/DD4-cold-ev-reality`; spec `spec.md` §4.4, §7 DD4; rulings D-DD.81-88 (DD4a change list and order);
run 2: D-DD.96's DD4a list after DD3a (D-DD.90, the join with D-DD.91) and D-DD.103. Not in run 2: D-DD.89's `M`
commit, the writer run, `test_dd4_thika_incident.py`, C-DD6 (next run).
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

## Run 2 (after DD3a merged; main merged at f131aa174)
Commits: d47713bd7 (D-DD.90), cd71da771 (D-DD.103), 4ec8033db (join, D-DD.81 + D-DD.91).
- **D-DD.90.** `M` `history.seasons` gains `"2026-11": short_rains`. `scope.history_global` restricts `seasons` to the
  history's months plus `anchor_period`. `DEFAULT_SUN_WEIGHTS["seasons"]` gains `2026-11`, pinned to `M` by a test.
  Fixture view and `history.json` regenerated from `M`. Test `world/test_scope_seasons_parity.py` (6), golden
  `golden/scope_seasons_main.json` from main 759759598: all 27 scope digests of the fixture view and history.json's
  scope blocks (sha256 of `tenants`) equal main's; a season planted at 2027-01 moves none.
- **D-DD.103.** `telemetry.READINGS_SPAN = ("2026-07-01T00:00", "2026-11-06T06:00")`; `span_days` takes a local date
  or a whole-hour local instant (others `TEL_EVENT_UNPLACED`). Mini-grid frozen inputs end at the instant (no forcing,
  note or draw after it); `SiteRun` writes 72 slots on 6 Nov; `ColdSiteRun` ends at the instant. `books_for` writes
  each span month after the accounting period as `{"rate_of": "2026-10", "delivered_kwh": E}` (Kobo E by the rule;
  blocks inside `READINGS_SPAN` scaled to E); a `rate_of` day draws the rate month's same-day part at 02:00. Site
  manifest `span.to`; `conditions.month_without_books` when the span reaches such a month; `measured.json` month the
  span ends inside carries `partial_to`. CLI `--start`/`--end` default to `READINGS_SPAN`; the `period_end` fallback
  is gone. Test `world/test_dd4_span_end.py` (7): Kobo 1 Nov to the end writes six files, the last all `end` <= 06:00,
  every signal 72 slots, last end 06:00; November load = E (computed in the test by the formula); six draws at 02:00 =
  October's first six parts (3.88 x 3, 3.87 x 3 L); Mwea ends at 06:00 (meter 72 slots); CLI defaults; refusals.
- **Join (D-DD.81, D-DD.91).** `build_telemetry` dispatches by `pack_family` (role set family: `minigrid-roles` ->
  `SiteRun`, `cold-roles` -> `ColdSiteRun`, `ev-roles` -> not written, DD4b). `SiteRun` gains `advance_day()` and
  `day_records(day)`. `VerticalBinding` (the frame) resolves each pack `(device_id, signal_id)` to one binding row,
  checks the unit (an event channel must be bound `event`), rounds to the millesimal, checks state maps, writes local
  ISO instants and event rows `{"value": null, "unit": "event", "event": {record_kind, outcome, actor, component_id,
  ordinal, correlation}}`; rows sorted by (start, source_id, signal_id, ordinal or 0). Cold manifest: pack
  `cold-thermal` 2, span with `to`, the run's `private_parameters()` and `conditions()`, mappings by binding row.
  `telemetry_cold` raises the frame's `TelemetryRefused`; `day_records` rows have the seventh element; the string
  packing is gone. Test `world/test_telemetry_join_parity.py` (8), golden `golden/telemetry_join_kobo_main.json` from
  main 759759598 (generator script in scratch, run against the main checkout read-only).

### Parity results
- Kobo 7 days (W1 inputs, 1-7 Jul): all 7 readings files byte-identical to main. Manifest identical except the two ruled
  keys, asserted: `span.to` = `2026-07-08T00:00:00+03:00` (D-DD.103) and `2026-11` in the sun table (D-DD.90).
  Guard proof: QUANTUM planted at 0.0001 -> both Kobo parity tests FAIL; reverted with `git checkout`.
- Scope digests: 27/27 equal main; history.json scope blocks equal main.
- Red first (scratch logs): seasons parity 3 failed before the scope change; span-end 5 failed before D-DD.103 (CLI
  test failed with the CLI change stashed); join 3 failed + 2 errors before the join (the edited cold tests 5 failed
  with the join stashed).

### Run 2 checks
- Touched-module tests (every file importing `scope`/`telemetry`/`telemetry_cold`/`world_history` or reading `M`,
  history.json or the fixture view), separate sim, backend and host pytest calls through `run-host-tests.ps1`,
  non-DB files in a plain heavy slot (the DB queue was held 20+ min by other lanes), the one Postgres file in `--db`:
  - branch 4bd79822d: sim (24 files) 311 passed; backend (11) 437 passed, 2 failed; host (3) 40 passed. Wall 127 s.
  - main 759759598: sim (18 files) 277 passed; backend (11) 437 passed, 2 failed (the same two:
    `test_3b1_structure_registry::test_t1_leaf_sources...`, `test_3b3_structure_evaluate::test_t6_each_state...`);
    host 40 passed. Wall 109 s. Sim difference 34: the six world test files
    only on this branch (receiving, telemetry_cold, cold_ledger, span_end, seasons parity, join parity) and the cases
    run 1 added to existing files.
  - First branch run found two of this branch's own failures, fixed in 4bd79822d: `test_core::test_t6_greps[\b31\b]`
    (run 1's November shift wrote `timedelta(days=31)`; now `days_in("2026-10")`) and D-DD.106 L2's CLI test (its
    `None` default is replaced by D-DD.103, as that ruling says; the test now asserts `READINGS_SPAN`).
  - Postgres `test_ddr_rehearsal_postgres.py` (one `--db` slot per tree): branch a5c7e9515 12 passed (214 s, after
    a 90-min queue); main 759759598 12 passed (178 s).
- `tools/check-architecture.ps1` (ASSETOPS_GUARD_PYTHON set): passed, 110 s. `tools/check-agent-workflow.ps1`: passed.
- `tools/checks/statement_catalogue.py`: exit 0 on branch and on main, outputs byte-identical.
- Layout evidence: not run (no UI).

### Run 2 known deviations
7. `meta.view_digest` covers the whole view (DS1), so `history.json` bytes move with the new season key: only that
   line. D-DD.90 expected sha256(history.json) unchanged; the test asserts the scope blocks instead. Pins moved:
   `golden/history_v1.json` `file_sha256` and `view_digest` (via `--update-golden`); no other.
8. The readings manifest of an unchanged span moves by D-DD.103's `span.to` and D-DD.90's sun-table key (rulings
   require both); the parity test removes exactly those two, asserting their values. `measured.json` of a span ending
   inside a month (the 7-day run: July) carries `partial_to`.
9. D-DD.91 names the door correlation `door`; the pack's key is `door-cycle`, written as the pack gives it.
10. Pack family is read from the role set family (no `/2` field names a pack); D-DD.81 names the families only.
11. Cold mappings `record` is the binding row's `asset_code` (mini-grid's is the pack address; cold rows carry no
    address). The last cold day keeps no 06:00 instant state row (06:00 is the horizon; the meter's interval to 06:00
    is the last row).
12. Not built here: cold `books_for` (ledger, cooling, events from `M`) is the writer run's; `tools/dd3_pure_run.py`
    keeps `--end 2026-10-31` (its table is the booked months); measured `room_kwh` (D-DD.99) is DD4b's.

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
