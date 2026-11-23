# DD3b review packet (DD3b1 + its D-DD.145 fix round; DD3b2: writer, model, checks and pure runs; DD3b3: notes, books, leaves table, `--pure` by D-DD.148/149; `M` commit held for the Architect)

Branch `task/DD3b-mini-plant` (worktree `/opt/assetecon/AssetOpsV1-dd3b`), base main `6e3c02ab5`. Part 1 of 3
(D-DD.142: DD3b1 2.0 u). Scope: D-DD.127 and spec DD §4.3, in `simulator/assetops_simulator/packs/mini_grid.py` and
tests only. DD3b2 (writer units, D-DD.97/104/126/128/129/132) and DD3b3 (D-DD.92/130/131) follow.
`USER_REVIEW_REQUIRED`: no (no screen; the figures moved are the owner-approved D-DD.97 and D-DD.104, below).

## What was built

- `MINI_GRID_V9_MODEL` (`mini-grid` 9) = v8 + `V9_SENTENCE`, appended after v8; v1-v8, the kernel, the contracts and
  the writer are untouched (`git diff main -- simulator/assetops_simulator` adds lines only, after line 1875).
- **Lifecycles (D-DD.127).** `GENERATOR_LIFECYCLE_V9`: v8's transitions plus STOPPED/STARTING/RUNNING → FAILED and
  FAILED → STOPPED. `INVERTER_LIFECYCLE`: `inverter-state` AVAILABLE ↔ FAILED, scenario-owned initial value
  (refused when absent, never assumed). v8's `GENERATOR_LIFECYCLE` (and its FAILED-initial rule) is unchanged.
- **Unit events.** `unit-fail@<unit>` / `unit-restore@<unit>` FORCING handlers (value 1, dimension COUNT), in a
  `unit-event` relation. `commit_v9` applies the events the step holds at the step's start (`point-applied-once`),
  before v8's lifecycle; a fail of a FAILED unit, a restore of a unit not FAILED, or an unknown unit refuses.
- **Units (§4.3).** Generators and inverters in component code order; the Site's plant, tank and control policy are
  read by v8's own readers from the lead units (`_lead_context`); another unit may restate the policy, never differ.
  The view adds each unit's state, running time and rating and P = max(0, demand + battery acceptance − available
  solar); `decide_v9` runs `decide_v8` for the Site (battery request, whether the set runs), then asks the shortest
  non-empty prefix of non-FAILED units whose summed rating ≥ P to run; a unit outside it keeps running to its minimum
  runtime, a STARTING one keeps starting. `due_v9` runs v8's start delay per unit.
- **Resolution (`_resolve_units`).** The RUNNING units act as one set in v8's `cycle_charge_split`: usable rating =
  the largest set output at which no unit exceeds its own (fuel-capped) rating, set minimum = the smallest at which
  every unit is at or above its own minimum load, each unit carrying output × rating / Σ rating. Each unit burns on
  its own curve (STARTING: no-load); the tank is the Site's one. Solar is split by `pv-array-share` and clipped per
  inverter; a FAILED inverter's share is clipped whole. Per-unit flows `generator_output:<unit>`, `pv_ac:<inv>` with
  balances `generator-units`, `inverter-units`; readings per unit: `generator-output-power@<unit>`,
  `pv-ac-power@<inv>`, `pv-available-power@<inv>`; every v2-v6 measure is kept.
- **One-unit fast path.** With one generator and one inverter (inverter AVAILABLE) `prepare/due/view/decide/commit/
  resolve` hand the step to v8's callables; `EXECUTABLE_MODELS` is not registered (D-DD.127 default).

## Tests (`simulator/tests/world/test_mini_grid_v9.py`, 10 tests, about 51 s)

- Written first, commit `299afe6e9`; the run failed at collection: `AttributeError: module
  'assetops_simulator.packs.mini_grid' has no attribute 'MINI_GRID_V9_MODEL'`.
- C-DD19 (mini part): v8 and v9 on Kobo's October inputs (the writer's `frozen_inputs` on the fixture view's books,
  8929 boundaries, the generator runs): equal digest over every boundary and transition, with only v9's
  `inverter-state` entries projected out (named projection; they are asserted AVAILABLE throughout).
- The unit path forced onto Kobo's one of each for a week equals v8 in every stock, transition and interval
  measurement (evidence that the multi-unit code lifts v8's rule rather than approximating it).
- Two sets (Kobo re-rated to 20 kW plus a 24 kW test set): the second joins only after the lead, outputs in ratio
  20:24, per-unit sum = the set's output. A fail 12 min into a run lands at its step (RUNNING → FAILED), the unit
  carries nothing until the restore (FAILED → STOPPED) and the second set carries meanwhile. A failed inverter
  (11:02-style instant, 06:02) gives 0 from its step; the other keeps its half. v9 runs a one-unit fail that v8
  refuses. Refusals: restore of a running unit, an unknown unit, a missing inverter state, shares summing to 3/4+1/2.

## Plants

1. `_fast` forced to `False` (the one-unit fast path removed): C-DD19's October test FAILED
   (`a8644171... != f5c3837f...`); reverted with `git checkout`.
2. Proportional split replaced by an equal split (`kw / len(running)`): the two-set test FAILED
   (`assert (Fraction(2117, 1500) * 24) == (Fraction(2117, 1500) * 20)`); reverted with `git checkout`.

## Checks (revision 2ab413b27, code unchanged since)

- Focused: `simulator/tests/world/test_mini_grid_v9.py` 10 passed in 50.9 s.
- Reach set (pre-flight §4, DD3b, once, `--db-lane`): 28 files of the pre-flight's DD3b list (every one present) plus the v9 file: **414 passed, 0 failed**, 1 warning, 182 s of test time (7 min 50 s wall time with the lane queue). No main rerun needed: nothing failed. `.agent/main-baseline/23d2cd9f6.md` lists DD3c's backend files, not these.
- `tools/check-architecture.ps1` (ASSETOPS_GUARD_PYTHON=main venv): passed. `tools/checks/statement_catalogue.py`:
  exit 0. `check-agent-workflow.ps1`: passed. `check-decision-index.py`: OK.

## DD3b1 fix round (D-DD.145) and DD3b2 part 1 (D-DD.128)

- Tests added to `test_mini_grid_v9.py`: P is never negative (min 0, max > 0 on Kobo 1-2 Oct with two sets) and a
  fuel-limited two-set segment never burns more than the tank (tank 0.3 L, runs dry, never below 0). Both pass on
  the built pack (the behaviour was DD3b1's), so each was proven by a plant (3, 4 below). Requested-power floor and
  litres cap were already in the code; the pack is unchanged.
- Kit (D-DD.128) in Lakeside's `/2` file; `pv-array-share` (+ basis) registered as a Foundation property (unit %,
  INVERTER, words and statement cases). `test_dd3b2_units.py` 3 tests, failed 3/3 on the old file first.
- Plants: 3. `max(0, ...)` removed from `view_v9`: the floor test FAILED (`assert Fraction(-32193, 1000) == 0`).
  4. The scaling of litres to the tank removed: the fuel test FAILED (`INTEGRATION_BOUND_FAILURE ... take the stock to
  -37/300 against a LOWER bound of 0`). Both reverted with `git checkout`.
- Checks at f16d759a8: `test_mini_grid_v9.py -k never` 2 passed; `test_dd3b2_units.py`, `test_dd1_operator_files.py`,
  `test_sc1_statements.py` 414 passed; `test_dd3_telemetry.py`, `test_dd3_site_inputs_cli.py`,
  `test_dd3_datasheet_check.py`, `test_dd1_check.py` 34 passed after the F re-pin. Architecture guard passed;
  statement catalogue exit 0. No Postgres run yet (DD3b2 incomplete; one `--db-lane` run at its end).

## DD3b2 writer and model steps (D-DD.97, .104, .126, .129, .145, .146)

Commits `08edaab94` (code + tests), `71badcc41` (callers, re-pins). All in `simulator/assetops_simulator/world/telemetry.py`:
- `Need.per_unit` / `Need.version`: generator curve keys and `inverter-ac-limit` per unit; policy rows (start/stop
  SOC, runtime, delay) from the lead unit only (first by code, D-DD.43); `pv-array-share` v9 only, % / 100 -> "1".
- `pack_version`: v8 with one generator and one inverter (Kobo), else v9 (Kisiwa, Mto); `SiteRun.pack` feeds the
  manifest's `pack`. Per unit: GENERATION + FUEL_SUPPLY per generator, PV_SOURCE per inverter, `generator-state`
  STOPPED per generator, on v9 `inverter-state` AVAILABLE per inverter. `supported()` per D-DD.129.
- `UNIT_EVENTS` (D-DD.126, 4 rows, `M` operations parity test); one-minute WINDOW forcings `unit-fail@<unit>` /
  `unit-restore@<unit>`; a generator's state row of the step holding the event starts at the instant;
  `conditions.unit_events` and `conditions.unit_event_timing` (D-DD.145's sentence verbatim). Inverter state is not
  emitted (D-DD.146); `_resolve` binds the per-unit roles one row per unit.
- Ledger: each generator's litres on its own curve, summed; a missing unit output or state refuses `TEL_PACK`.
- `SEASON_V2_SUN_SITES = ("KOBO-001",)`; D-DD.97's `res` shape + `conditions.load_shape_basis`; D-DD.104 warm-up
  (`warm_up_soc`, `conditions.start_soc`, the 40 % default deleted).
- Defaults refused: `sun_weights`, `fuel_notes` (`TEL_BOOKS`); no expenses file for a mini-grid tenant
  (`TEL_BOOKS`); an empty state map (`TEL_BINDING`, mini and vertical frames; every committed map is non-empty);
  a Site with no binding is F's `unbound` list and a `not_written` manifest line. `DEFAULT_DAY_WEIGHTS` moved into
  `test_dd3_telemetry.py`; `DEFAULT_SUN_WEIGHTS` is kept only for tests' hand-made books (parity-pinned).

Tests first: `test_dd3b2_units.py` +16 (16 failed before the code: refusals not raised, MTO "needs exactly one
INVERTER", the old `res` tuple, no `unit_events`; reasons kept in the session log), 19 pass after. Simulator reach
(`test_dd3_telemetry`, `_site_inputs_cli`, `test_dd4_span_end`, `test_telemetry_join_parity`, `test_mini_grid_v9`,
`test_scope_seasons_parity`, `test_3a3_exports`, `test_dd2_*`, `test_dd2b_*`, `test_dd4_telemetry_cold`,
`test_dd4_thika_incident`, `test_decide_v8`, `test_cycle_charge_split`, `test_dd3b2_units`): 222 passed, 47 s,
revision `71badcc41`. Re-pins: four `test_mini_grid_v9.py` multi-unit cases start at a stated 40 % (`_kobo_at_40`,
their own scenario; the warm-up start leaves no generator run on 1-2 Oct); W1's join golden regenerated from the
writer (kernel and pack v8 equal main's; `source` names the revision).

## DD3b2 checks and pure runs (D-DD.132, D-DD.146; C-DD21's v9 row)

Commits `9133791e3` (tests first: 9 failed), `f2d532075` (dd_check), `8d61890a8` (`dd3_pure_run.py --site`; its test
failed first with `SystemExit: 2`), `45a74193f` (W1 forcing-index case). All in `tools/dd_check.py`,
`tools/dd3_pure_run.py`, tests.
- **C-DD6 (D-DD.146).** `FAILURES_LIVE` clauses carry `evidence`: Thika `event` (unchanged), Kisiwa `state`
  (`gen-ks-01-controller` STATE row FAILED starting 2026-10-30T18:40, no other source FAILED then), Mto `power`
  (`inv-mt-02-controller` `ac-power` 0 from the 11:00 step to span end, above 0 at 10:55, irradiance and INV-MT-01
  above 0 at 11:00; an information line says 11:02 is the O&M record's). `PENDING` keeps only EV-KAS and EV-RUI.
  `passed` now reads failing lines only, so information lines can stand in `detail`. Thika's test judges its own
  lines (with Kisiwa/Mto absent the whole result fails by design); its three plants still fail on Thika lines.
- **`--pure DIR` (D-DD.132).** No `--database-url`. Reads `<tenant>/telemetry/*.readings.json`, `*.manifest.json`,
  `measured.json`; judges C-DD8 (tank in [0, rating]; Kobo October balance beside the manifest's 120 L; Kobo October
  unserved critical energy, MG-5; Kisiwa candidate minutes, OR-MG-2), C-DD17 pure (Kobo monthly unexplained >= 0,
  <= 2 % Jul-Sep, > 2 % Oct) and C-DD20 Kisiwa/Mto. Readings only, no simulator import (the import guard holds).
- **C-DD21's v9 row.** `judge_v9_rows`: on the writer's `frozen_inputs` for Kisiwa (v9), every per-unit need and
  `pv-array-share` is answered at each unit with the table's unit and dimension, shares sum to 1. Kobo's v8
  comparison keeps the `n.version in (None, 8)` filter.
- **`dd3_pure_run.py --site CODE`** (Kobo default; Kisiwa/Mto from the committed `/2` kit, v9; `--no-load` Kobo only).

Tests: `simulator/tests/world/test_dd3b2_checks.py` (9; every new clause shown failing on a planted row: late or
shared FAILED state, power returning at 16:00, already 0 at 10:55, INV-MT-01 off, dark irradiance, tank 5000.5 L,
a generator at 10:20 while PV charges, missing 28-day window, a dropped `generator-no-load-fuel-rate@gen-ks-02`, a
halved share).

**Plant (C-DD21 filter):** the filter removed, `check_property_table_parity` fails with `pv-array-share: backend None
!= writer ('pv-array-share', '1', 'FRACTION', 'pv-array-share')`; reverted (`git checkout`). With the filter: PASS,
"17 rows equal ...; KISIWA-001 v9: every unit answered, pv-array-share sums to 1".

### Pure runs (`dd3_pure_run.py --books <exports> --site CODE`, 1 Jul-31 Oct; nothing fitted)

| Site | month | notes | accepted | refused | drawn | burned | tank min-max | unserved kWh | gen h | stand-in cand. |
|---|---|---|---|---|---|---|---|---|---|---|
| Kisiwa v9 (5000 L) | Jul | 2353 | 2353 | 0 | 20 | 1255.28 | 2479-3687 | 0 | 92.58 | 3.67 |
| | Aug | 2339 | 2339 | 0 | 19 | 1236.15 | 3559-4763 | 0 | 92.42 | 115.39 |
| | Sep | 2134 | 998.33 | 1135.67 | 18 | 689.02 | 4661-5000 | 0 | 49.67 | 0 |
| | Oct | 2400 | 874.46 | 1525.54 | 20 | 883.56 | 4784-5000 | 0 | 65.58 | 66.93 |
| Mto v9 (1000 L) | Jul | 319 | 319 | 0 | 0 | 0 | 500-819 | 0 | 0 | 0 |
| | Aug | 318 | 181 | 137 | 0 | 0 | 819-1000 | 0 | 0 | 0 |
| | Sep | 293 | 0 | 293 | 0 | 0 | 1000 | 0 | 0 | 0 |
| | Oct | 320 | 0 | 320 | 0 | 32.38 | 968-1000 | 0 | 3.25 | 32.17 |
| Kobo v8 0.62 (2500 L) | Jul | 972 | 972 | 0 | 12 | 0 | 1250-2216 | 0 | 0 | |
| | Aug | 1002 | 295.85 | 706.15 | 12 | 0 | 2210-2500 | 0 | 0 | |
| | Sep | 1003 | 345.45 | 657.55 | 11 | 762.20 | 2066-2500 | 0 | 75.67 | |
| | Oct | 1180 | 934.58 | 245.42 | 120 | 514.22 | 2062-2500 | 0 | 51.33 | |

Balance (open + accepted - close - modelled) equals the drawn litres every month at all three. **Bound hit: YES at
all three** (deliveries overfill the tank). Walls 75 s (Kisiwa), 73 s (Mto). Each goes to the Architect (D-DD.19/
D-DD.70); D-DD.131's notes restatement is DD3b3. Kobo's bound hit is new with D-DD.104 (July burns 0 L from a 60 %
start, so August's notes overfill).

### `dd_check --pure` on the writer's files

The strict writer (`world_history.py telemetry`) refuses the overfill (`TEL_PACK ... fuel-tank-capacity refused`):
Kobo on 2026-08-01 (109.61 L), Kisiwa on 2026-09-01 (194.97 L). So no Jul-Oct pure DIR exists until DD3b3. Run on
1-31 Jul for all three (telemetry exit 0; dd_check exit 1): tanks within bounds at all three; FAIL lines are
coverage (no October, no August-October months, no 28-day Mto window) and two world facts: **Kisiwa 20 candidate
minutes in July** (and 20 on 30 Oct in the one-day test run: GEN-KS-01 running 10:00-10:15 at 22.8 kW to its 90 %
stop while PV gives 27 kW against a 19.8 kW load), against OR-MG-2's zero; and the pure table's **Kisiwa October
unserved 0 kWh**, against C-DD20's "unserved evening energy after 30 Oct 18:40" (GEN-KS-02 carries the evening).
Mto in the table: 0 L burned July-September, 32.38 L over 3.25 h in October (the table does not say when in October; C-DD20's Mto clause needs the Jul-Oct DIR). Reported, nothing tuned.

### Host tests that import the writer; the one `--db-lane` reach run

`tools/heavy-slot.sh --db-lane -- bash reach.sh` at revision `8d61890a8` (one call, three `run-host-tests.ps1`
runs): backend 8 files (`test_0k4a_profile_words`, `test_k1_kisiwa_fixtures`, `test_dd1_operator_files`,
`test_dd2_check`, `test_dd1_check`, `test_sc1_statements`, `test_dd1_onboarding_postgres`,
`test_dd3_datasheet_check`) **464 passed** 30.8 s; host 8 files (§4 DD3b list) **171 passed, 1 failed** 80.4 s;
simulator 22 files (§4 DD3b list + `test_dd3b2_units`, `test_dd3b2_checks`, `test_mini_grid_v9`,
`test_dd4_thika_incident`) **217 passed** 147.6 s. The failure: `test_kernel_forcing_index_parity[W1]`,
`TEL_BOOKS KOBO-001 the books carry no sun_weights` (its hand-made books relied on the default D-DD.129 removed).
Fix `45a74193f`: the case passes `tel.DEFAULT_SUN_WEIGHTS`; its inputs moved (D-DD.97, D-DD.104), so its digest was
regenerated with main's kernel (`--reference main W1`, `b00c96e1...`). Rerun `test_0k4c_season_v2` +
`test_kernel_forcing_index_parity`: **31 passed**. Main: `.agent/main-baseline/23d2cd9f6.md` (DD3c's 81 backend
files, 1008 passed, 10 failed, 4 errors; main's own failures `test_ch5c2_clock_guard`, `test_w204`
TestMigration0023), partial, no per-test list; none of this run's failures is among them, and host/simulator files
are outside it.

**For the reviewer:** W1's **join** golden (`test_telemetry_join_parity`) was regenerated from the writer because
D-DD.97 and D-DD.104 move Kobo's world (step 7 commit `71badcc41`); the kernel and pack v8 are unchanged against
main. The forcing-index W1 digest above is the same move, computed by main's kernel. Judge both.

Guards: `tools/check-architecture.ps1` passed; `tools/checks/statement_catalogue.py` exit 0.

## DD3b3: notes, books and leaves (D-DD.92, .130, .131, .147-149)

Commits `6fd644bb1` (tests first: **12 of 12 failed**), `299a88da7` (tool, exports, dd_check), the notes file commit,
the exports-tests restatement. Files: `tools/dd3_pure_run.py`, `simulator/assetops_simulator/world/exports.py`,
`tools/dd_check.py`, `config/world/fuel-notes.json` (new), tests.
- **Reorder rule (D-DD.92).** `dd3_pure_run.py --restate-notes [--check] --site CODE`: the strict writer runs the span
  on the current notes; at the first boundary where the level goes from at least 25 % of the tank to below it, notes
  are placed at the next 10:00 (the same day only when the crossing is before 10:00), `min(2, free // 400)` of them,
  free = capacity minus the level at that 10:00 boundary; rerun until no new crossing. OOO-1's note keeps its date
  (`exports.DATED_NOTES`, basis `STORY:OOO-1`). A pass stops at the 10:00 after its crossing, so only the last pass
  runs the whole span. `--check` reruns the rule and exits 1 when the file's entry differs.
- **Books (D-DD.130).** `build_exports(..., fuel_notes=None)` reads `config/world/fuel-notes.json` by default
  (`read_fuel_notes`, schema checked). For a Site in it the FUEL rows are its notes in the month, litres x price;
  `EMU_FUEL` is the sum of the amounts against the notes. A Site not in it keeps D-DD.53's cycle. C-DD4 no longer
  judges mini-grid `diesel_l` / `fuel_cost` (`_RECORDED_NODE`, `_stored_nodes`); its October plant moved to revenue,
  and a planted fuel amount is now shown as not judged.
- **Leaves (D-DD.131).** `--leaves --site CODE` runs the span on the file's notes and prints October's leaves,
  `fuel_balance`, the bridge's fuel lines on their stated formulas, whether the bridge closes, the
  GENERATOR_SUPPORT_CANDIDATE days, and the peak evening generator kW after 30 Oct 18:40. Builder choices: necessary
  = `diesel_l` - candidate - unexplained (keeps `M`'s `diesel_l` identity); candidate = the stand-in, whole litres
  half-even. Exit 4 when the bridge does not close.
- **`--pure` (D-DD.149, D-DD.148).** `fuel_tolerances()` reads `M`'s `period.fuel_balance.tolerance_pct` (Kobo,
  Kisiwa: 2.0); C-DD17 uses Kobo's. C-DD8 Kisiwa: `judge_candidate_share`, candidate minutes under 1 % of generator
  minutes (any unit above 0 kW) in every month, printed. C-DD20 Kisiwa: `judge_kisiwa_failure` (GEN-KS-01 FAILED at
  0 kW from 30 Oct 18:40, never restored; every evening generator step after it on GEN-KS-02; unserved 0 every month).

Tests: `simulator/tests/world/test_dd3b3_notes.py` 12 (rule unit tests on a fake tank, the committed file, books from
the notes, C-DD4, leaves arithmetic, tolerance, Kisiwa share and failure on the writer's 30 Oct rows with three
plants). Restated (old -> new, read from the regenerated source): `test_3a3_exports` PINNED expenses `74c5ad18...` ->
`298773a4...`, PINNED_ALL_MONTHS expenses `bc991181...` -> `ab112234...`, `test_e4_fuel` October litres
[2400, 1180, 320] -> [800, 400, 0] (Kisiwa, Kobo, Mto); `test_dd2_nodes` Kobo October notes -> OOO-1 only, fuel rows
present exactly where the file has a note, the cycle test on a file listing no Site;
`test_dd2_checker_on_emulated_rows` October plant on revenue.

**Plants** (each introduced, run, reverted with `git checkout`): `MAX_NOTES = 3` fails the count test; `<=` in
`note_instant` fails the 10:00 test; a 2 % candidate bound fails the Kisiwa share test (3 failed, 9 passed).

### The notes run (`--restate-notes`, 1 Jul-31 Oct; walls Mto 69 s, Kobo 112 s, Kisiwa 220 s)

| Site | notes |
|---|---|
| Kobo (2500 L) | 26 Sep 2 x 400 REORDER; 26 Oct 400 STORY:OOO-1 (1,200 L) |
| Kisiwa (5000 L) | 31 Jul, 20 Aug, 15 Sep, 15 Oct: 2 x 400 REORDER each (3,200 L) |
| Mto (1000 L) | none (never reaches 250 L; D-DD.147) |

Pure tables on the exports of the new file: **bound hit no** at all three; balance equals the drawn litres every
month. Kobo tank 572-1373 L Sep, Kisiwa 1238-2500 L, Mto 468-500 L.

### Moved figures against D-DD.147 (`--leaves`; nothing fitted)

| Leaf | Kobo old -> new | Kisiwa old -> new (projection) | Mto old -> new (projection) |
|---|---|---|---|
| `diesel_l` | 1180 -> 634 (about 634) | 2400 -> **904** (about 904) | 320 -> **32** (about 32) |
| `necessary_l` / `candidate_l` | 730 / 330 -> 489 / 25 | 2380 / 0 -> 817 / 67 | 320 / 0 -> 0 / 32 |
| `diesel_cost` | 1475.00 -> 792.50 | 3120.00 -> **1175.20** (about 1,175) | 400.00 -> 40.00 (about 40) |
| `contribution` | 883.00 -> 1565.50 | -250.00 -> **1694.80** (about +1,695) | 810.00 -> 1170.00 |
| `variance` | -562.00 -> 120.50 | -185.00 -> 1759.80 | -105.00 -> 255.00 |
| fuel balance open / deliv / close | 220/1200/240 -> 1253/400/1019 | - -> 1663/800/1559 | - -> 500/0/468 |
| consumed / implied / residual | 1180/1060/120 -> 634/514/120 | 2400/2380/20 -> 904/884/20 | - -> 32/32/0 |
| CANDIDATE_RUNNING | -412.50 -> -31.25 | (no line) | (no line) |
| necessary line | EVENING -37.50 -> +263.75 | SOLAR_SHORTFALL -104.00 -> +1927.90 | EVENING -25.00 -> +375.00 |
| bridge vs variance | **closes** (120.50) | **does not close** (1846.90 vs 1759.80, gap -87.10) | **does not close** (295.00 vs 255.00, gap -40.00) |
| GENERATOR_SUPPORT_CANDIDATE | 11 days, [0, 330] -> 5 days, [0, 25] L, [0, 31.25] | count 0 -> 9 days, [0, 67] L, [0, 87.10] | - -> 1 day, [0, 32] L, [0, 40.00] |

Kisiwa's peak evening generator power after 30 Oct 18:40: 41.87 kW, so the typed "95 %" would print as 69.8 % of
60 kW. BATTERY_NEAR_RESERVE's count is the product's warning (`outcomes/warnings.py`), not computed here.

**`M` is not changed.** D-DD.131: "If the bridge does not close against the restated variance under the manifest
check, stop for the Architect." Kisiwa's and Mto's gaps are exactly `-candidate_l x price`: neither Site's bridge has
a CANDIDATE_RUNNING line, and the stand-in now gives both a candidate. Known Deviation 12.

### Full Jul-Oct pure DIR (`world_history.py exports` without `--tenant`, `site-inputs`, `telemetry` for the three Sites)

Telemetry exit 0 (233.75 s): the strict writer accepts the Jul-Oct span at all three (deviation 10 closes).
`dd_check --pure` exit 1:
- C-DD8 FAIL: tanks within bounds; Kobo October balance 1252.8 + 400.0 - 1018.6 - 514.2 = 120.0 L (the manifest's
  120 L); Kobo October unserved clinic energy 0 (MG-5); **Kisiwa candidate time 2026-07 20 of 5555 min (0.36 %),
  2026-08 625 of 5545 (11.27 %), 2026-09 0 of 2980, 2026-10 400 of 3935 (10.17 %)**: D-DD.148's "under 1 % in every
  month" holds for July only (Known Deviation 13).
- C-DD17 FAIL: July and August unexplained 12 of 12 L consumed (100 %): Kobo burns 0 L those months (D-DD.104), so the
  declared draw is all of consumption; September 1.42 %, October 18.92 % (Known Deviation 14).
- C-DD20 PASS: Kisiwa GEN-KS-01 FAILED at 0 kW over 352 steps from 30 Oct 18:40, 40 evening generator steps all on
  GEN-KS-02, unserved 0 every month; Mto 0.00 L/day in the 28 days before 28 Oct 11:00, 9.14 after.

## Moved figures

Kobo, `tools/dd3_pure_run.py --books <exports>` (no-load 0.62, 1 Jul-31 Oct), before (`3aa165f67`) -> after (`71badcc41`):

| Kobo | before | after | D-DD.97 projection |
|---|---|---|---|
| Oct burned | 507.86 L | 514.22 L | 514.22 L |
| Oct consumption (burned + 120 L draw) | 627.86 L | 634.22 L | about 634 L |
| Oct stand-in candidate | 42.03 L | 24.56 L | 24.56 L |
| CANDIDATE_RUNNING bridge at 1.25 $/L | -52.54 | -30.70 | about -30.70 |
| Oct generator hours | 51.17 | 51.33 | 51.3 |
| Jul burned | 37.38 L | 0.00 L | 0 (D-DD.104) |
| Sep burned / candidate | 751.90 / 59.75 L | 762.20 / 39.92 L | |
| Starting SOC (1 Jul) | 40 % | 437916/7277 = 60.18 % | about 60.4 % (old shape) |

Nothing fitted: the shape is D-DD.97's tuple, the SOC the warm-up's exact value. Pins moved earlier: Lakeside's F
digest `4e36563d...` -> `25345568...` (D-DD.128).

## Known Deviations

1. **Unit events are not POINT forcings in the kernel's terms (D-DD.127 says POINT, indexed by step, D-DD.75).**
   The kernel gives a POINT forcing a zero-length span: `_forcing_index` skips it (`end <= start`,
   `kernel/execute.py:288`) and no step context, nor phase A's `due` context (`exposures=()`), ever carries it. So a
   pack cannot read a POINT forcing, and the scope (pack and tests only) excludes a kernel change. Builder default:
   v9 reads the events from the step's exposures in `commit` (phase F), applied at the step's start, so the writer
   declares each as a WINDOW of one minute at the instant, which reaches exactly the step that holds it (the same
   step `point-applied-once` names). Consequences: the sample and view at the failing step's start still show the
   unit as it was; the controller reacts from the next step. **Question for the Architect:** keep this, or make the
   kernel expose POINT forcings at `point_due_at` (a kernel change and version move, outside DD3b's units)? If the
   kernel later exposes them, `_unit_events` reads them unchanged.
2. P (the requested generator power selecting the running set) is not defined numerically in §4.3 ("v8's rule");
   builder default: the demand plus the battery's acceptance at T (taper and headroom) less available solar. v8
   never needed it (one set runs whole).
3. A fuel-limited multi-unit segment caps each unit on its rating share of the tank; when the no-load burn exceeds
   the tank, the litres are scaled to the tank (v8's single-unit rule, lifted). Not reached by any Site's run.
4. A restored generator returns to STOPPED and can be asked to start from the next step.

5. **`/1` file unchanged (D-DD.128 says `/2` and `/1`).** `lakeside-power.v1.onboarding.json` carries no properties
   for any Site (format 1 has ratings only) and the writer SKIPs `/1`; adding the kit there would invent a shape.
   The coordinator confirmed: the kit is in `/2` alone (kept here for the reviewer).
7. `generator_minutes` in the ledger counts unit-minutes (each running unit); only the pure-run table reads it.
8. A Site with no binding is carried in F as `unbound` (written only when non-empty, so committed F digests hold)
   rather than as a Site entry, because F's readers take every `sites` entry as bound.
6. D-DD.146 built (section "DD3b2 checks and pure runs").
9. **`--pure` readings choices (D-DD.132 names the checks, not every reading).** Builder defaults, for the
   Architect: burned = the `/2` curve per unit on (no-load x h + (SFC - no-load/rated) x kWh, as the pure table);
   opening/closing dip = the month's first tank reading and the next month's first; candidate = a generator above 0
   kW while PV >= 1.1 x feeder load (dispatch-3.2's rule); MG-5 critical = the first of `critical_load_order`
   (clinic); unexplained tolerance 2 % (domain models §3.3; no product constant found); C-DD8's candidate count
   over the whole span. **C-DD20 Kisiwa** is judged on `measured.json` months, which cannot resolve 17-31 Aug or
   1-30 Oct (stated in the detail). **Question:** is a per-day unserved series wanted in `measured.json` (writer
   change) or is the month reading accepted?
10. **No Jul-Oct pure DIR** while the notes overfill (strict writer refuses); judged on July only. Closes with
    DD3b3's notes (D-DD.131).
11. **Two world facts against the oracle**, reported, not tuned: Kisiwa candidate minutes > 0 (OR-MG-2 says 0);
    Kisiwa October unserved 0 kWh (C-DD20 expects unserved evening energy after 30 Oct 18:40). Both to the Architect.

12. **`M` commit held (D-DD.131 stop).** Kisiwa's and Mto's bridges do not close on the restated leaves: gap
    -87.10 (Kisiwa) and -40.00 (Mto), each exactly `-candidate_l x price`; their bridges carry no CANDIDATE_RUNNING
    line. Kobo closes. So no leaf, `fuel_balance`, `findings_expected`, OR-MG-2, D-DD.30 chain output or
    `worked-portfolios.md:74` was changed. **Question:** add a CANDIDATE_RUNNING line to Kisiwa's and Mto's bridges
    (as Kobo's), or fold the candidate into the necessary line, or another rule? BATTERY_NEAR_RESERVE (22 days) waits
    with it (the product's warning, not a writer figure).
13. **Kisiwa candidate time above 1 % in August (11.27 %) and October (10.17 %)** by D-DD.149's measure (generator
    above 0 kW while PV >= 1.1 x load). D-DD.148's bound came from July and one 30 Oct day; the full run disagrees.
    Reported, not tuned; for the Architect (OR-MG-2's restated wording).
14. **C-DD17 July and August fail by construction** since D-DD.104 (Kobo burns 0 L, so the 12 L draw is 100 % of
    consumed). For the Architect: the clause's "within 2 % July-September" needs a rule for a month with no burn.
15. Books: for a Site in the notes file the FUEL rows are purchases, but `diesel_l` / `diesel_cost` are still marked
    written in the unwritten list (no new reason word was ruled). Notes after 31 Oct are not placed (the span is the
    tool's; exports write Jul-Oct only).

## Next

The Architect on deviations 12-14; then DD3b3's `M` commit (D-DD.131 leaves via `--leaves`, a test that `M` equals the
tool's output, the D-DD.30 chain), then the one DD3b review.
