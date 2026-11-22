# Review packet: DD4a cold operating reality, part 1 (run 3: D-DD.89, D-DD.119-122; C-DD6 live for cold)

Branch `task/DD4-cold-ev-reality`; spec `spec.md` §4.4, §7 DD4; rulings D-DD.81-88 (DD4a change list and order);
run 2: D-DD.96's DD4a list after DD3a (D-DD.90, the join with D-DD.91) and D-DD.103. Not in run 2: D-DD.89's `M`
commit, the writer run, `test_dd4_thika_incident.py`, C-DD6 (next run).
USER_REVIEW_REQUIRED: false (run 3 reproduces D-DD.89's story figures from the readings; the owner already chose "Change the event"; no UI).
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

## Run 3 (D-DD.119, D-DD.120, D-DD.89, D-DD.122, D-DD.121; main merged at 34928040d)
Commits: 085f94dd3 (D-DD.119 cold books + CLI `TEL_BOOKS`, D-DD.120 `STORY_EVENTS`), 0c5d5fab7 (D-DD.89 `M` rev 16.19,
regeneration, sweep), 0707ce3c1 (`test_dd4_thika_incident.py`, C-DD6 live for cold, C-DD11 gains Mwea).
- **D-DD.119.** `telemetry_cold.cold_books_for(view, history, records, *, ledgers=None)`: ledger rows of
  `build_cold_exports`' `profile.cold-storage-ledger` file per Site; `cooling`/`seasons`/`day_classes` from the view;
  `efficiency` from the Site's own `actual.kwh` rule read by `history._parse`/`_Scope.listed`, the accounting period
  `kwh / kwh_model`, the months after it at that value. `tools/world_history.py telemetry` builds records, re-renders
  each cold ledger with its profile, compares with `<books>/<file>` and refuses `TEL_BOOKS <file>` (exit 3).
- **D-DD.120.** `STORY_EVENTS["COLD-THIKA"]` exactly as ruled; parity test reads `M`'s three instants.
- **D-DD.89.** `M` lines 463, 480, 481, 487, 538, 539, 1867, 2024, 2025 per the ruling (rev 16.19 header line). The view
  and history.json are byte-identical (no scope digest, mini-grid or EV pin moves). Regenerated: derived-values.json
  (Thika unavailable 72, 99.839 %; portfolio 99.946), mock fixtures.js and index.html (gen_fixtures.py, build.mjs).
  Hand sweep (19:14->20:22, 19:15->20:23, 19:19->20:25, 19:45->20:55, 8.2->5.4, 25-35->75-85, 4->72 min,
  99.997->99.946): vNEXT screens.js 86, 92, 178, 214, 221, 240, 393, 400, 401, 416, 417, 419, 420, 457, 559, 592, 627,
  700, 832, 1038, 1040, 1044, 1117; outcomes.js 84, 85, 129, 136; portfolio.js 18, 21; loop-decisions.js 351;
  CHANGE-REGISTER.md 289; tools/gen_docs.cjs 114; worked-portfolios.md 24, 375; integration-source-to-canonical-design.md
  173, 296, 319, 321, 324, 333; domain-and-decision-models.md 260, 273, 364; economic-metric-and-effect-contracts.md 176;
  derivation-register.md 1982, 2451. Content only; no MOCK DEVIATION. `check_manifest.py` re-based H8, H10, K13 with
  dated notes; it exits 1 with 7 failures that failed before this change too (H9, K8, A1, A2, A3, A5 alignment);
  regenerating the stale fixtures.js/index.html cleared 5 earlier failures (K11 x4, K7).
- **Writer run (D-DD.122).** Output `/opt/assetecon/worlds/DD4a-0c5d5fab7b90/` (books, sites.json, one telemetry tree
  per room). exports 1.7 s; COLD-MWEA 29.4 s, COLD-KIRI 30.1 s, COLD-THIKA 30.7 s (one process each, ~0.23 s per
  Site-day); 129 day files per room, 41.27 / 41.32 / 41.32 MB (~320 kB per Site-day); each room's last row ends
  2026-11-06T06:00+03:00 and `span.to` is that instant. Thika 6 Oct 5-minute readings above 5 degC: 20:10 5.081,
  20:15 5.223, 20:20 5.365, 20:25 5.422, 20:30 5.147. Events: START_REQUEST/START_RESULT FAILED (CONTROLLER) and
  POWER_LOSS 19:11; START_RESULT SUCCEEDED (OPERATOR) 20:22; TRANSFER_RESULT 20:23; POWER_RESTORED and transfer 22:00.
- **D-DD.89 reproduced (`test_dd4_thika_incident.py`, Thika 1 Jul-7 Oct via `build_telemetry`, per-minute chamber
  captured from the pack's own steps).** Peak 5.477 degC at 20:24; above 5 degC 20:08-20:32 = 25 min; cooling
  unavailable (bus unpowered) 72 min; five 5-minute readings above 5 (largest 5.422 at 20:25), bound 20-30; readings
  above 4 from 19:35 to 20:50 (16, bound 75-85); first in band 20:55 at 3.793. Above 4 degC: see deviation 13.
- **C-DD6 (D-DD.121).** `dd_check.judge_failures_at_instant({code: rows})`: GEN-CR-01 = a FAILED event on
  `generator-controller` (and no other channel) at 2026-10-06T19:11; B-1031 above 5 degC more than 15 min by the
  5-minute lower bound (n-1)x5 of the longest run; B-1034 peak below 12. `STUBS["C-DD6"]` is the pending list (EV-KAS
  CH-K2, EV-RUI CH-R7 c2: DD4b; KISIWA-001 GEN-KS-01 18:40, MTO-001 INV-MT-02: DD3b), returned as `Result.pending`.
  Live on the writer's Thika rows; a FAILED moved to 19:12, a 12.5 degC reading, or no rows each fail.
  `check_two_processes_agree` (C-DD11) adds `--site COLD-MWEA` for 1-2 Jul.

### Run 3 red first (scratch logs)
- `test_dd4_cold_books.py`: collection error (no `STORY_EVENTS`/`cold_books_for`); after the code 7 passed, the `M`
  parity test failed (`19:14` != `20:22`) until 0c5d5fab7.
- `test_dd4_thika_incident.py` with `tools/dd_check.py` at HEAD: 4 failed (the judge missing, plus two measurement
  windows of mine that were too wide, fixed to the excursion run before the green run).

### Run 3 checks
- Reach set (preflight-remaining §4, DD4a), head 0707ce3c1/0c5d5fab7: simulator world 17 files (`test_dd4_*`,
  `test_dd3_telemetry`, `test_telemetry_join_parity`, `test_scope_seasons_parity`, `test_dd2b_*`, `test_history*`,
  `test_records*`) 207 passed, 95 s; backend `test_dd1_check`, `test_dd2_check`, `test_dd3_datasheet_check` 24 passed;
  `test_ddr_rehearsal_postgres.py` (`--db`) 12 passed, 224 s. Layer-4 chain (step 3 run): backend 13 files reading `M`
  or derived-values 678 passed, 2 failed (the two main fails of run 2: `test_3b1...t1_leaf_sources`,
  `test_3b3...t6_each_state`), 1 skipped; host `test_0m_mto_headroom` 9 passed. Main: `.agent/main-baseline/23d2cd9f6.md`
  does not list these files; run 2's main figures stand for the unchanged files.
- Parity: `test_telemetry_join_parity` (Kobo W1 7 days byte-identical) and `test_dd2b_*` (mini-grid and EV book pins)
  green; the view and history.json unchanged by the `M` commit; no cold book changes in this run.
- `statement_catalogue.py`: exit 0. `check-architecture.ps1` (ASSETOPS_GUARD_PYTHON set): passed, 202 s. `check-agent-workflow.ps1`: passed. Layout evidence: not run (no
  UI code; the mock's content strings only).

### Run 3 known deviations / builder defaults (for the reviewer to confirm)
13. D-DD.89's "above 4 degC 82 minutes": the excursion itself is 79 min (19:33-20:51, back at or below 4 by 20:52 as
    ruled); 82 is the count of minutes above 4 over 18:00-23:30, which adds 22:37-22:39 after the grid restore. The
    test asserts both. Not a stop: peak and minutes above 5 degC reproduce exactly.
14. D-DD.119's efficiency: only a Site with its own `history.sites` `actual.kwh` rule has a table (Kirinyaga), as the
    ruling's test requires; Mwea's period ratio 2650/2635 is therefore not applied (f = 1). An `anchor` entry gets no
    month entry.
15. C-DD6's clone fetch (`stored_readings`) returns no rows: the world's readings reach the store only through DD5's
    loader, so the check fails on the clone until then, as D-DD.121 says.
16. Order: the Thika test and C-DD6 were written while the `M` commit ran in parallel, before the writer run; the
    writer run's 6 Oct rows equal the test's.
17. Sweep choices no ruling fixes (step 3): the excursion window text "began 19:30-19:35, ended 20:50-20:55"; "from
    about 19:35"; "peak came two minutes after cooling resumed"; screens.js:214 arrival 20:03 -> 21:03; a sample
    source_time 17:25Z. Left for a content pass from the writer's readings: the mock's temperature and recovery chart
    series (screens.js:71, 77-78, still peaking at 8.2 on a 19:00-20:00 axis), "Exposure size 50-90 degC-min"
    (screens.js:400); historical review records untouched.
