# DD3a review packet (DD3.1 + DD3.2; `task/DD3a-mini-reality`)

Spec `specs/DD-demo-data/spec.md` §4.1, §4.2, §6, §7 DD3.1/DD3.2; rulings D-DD.17, .19, .30, .67-.69, .75-.77, .79,
.80 (`rulings.md`). Session notes: `DD3a-handoff.md` (Updates 1-5). `USER_REVIEW_REQUIRED: true` (demo narrative,
evidence labels, moved story-world figures).

## Outcome
Kobo's operating reality is written by a pure writer on v8 from the Site's own records; Kobo's equipment carries its data
sheets (labels Declared / Assumed); the kernel runs a 123-day span in about 1-2 minutes, byte-identical to main.

## Files changed (by commit group)
- DD3.2 commit 1a `3bfe1451d`: `config/datasheets/kobo-equipment.json`, `tools/datasheet_template.py`, `sites/models.py`
  basis siblings + DATASHEET_FIT, `i18n/statements/en/foundation.py` `component_property.basis`.
- D-DD.67/68 `2e2b697cc`: `financials/fuel_cost_v2.py` NO_LOAD_BASES, `chain/vocabulary.py` words, parity test + golden.
- DD3.1 `2d0a68f3a`, `402daec56`: `simulator/assetops_simulator/world/telemetry.py`, `tools/world_history.py`
  `site-inputs`/`telemetry`, `tools/dd3_pure_run.py`, `tools/dd_check.py` C-DD11/12/21.
- D-DD.75 `e347205d6`, `776285ae1`: forcing index; `host/tests/test_kernel_forcing_index_parity.py` + golden.
- D-DD.77 `afce2bd40` (sun outside season v2), D-DD.76 `ab349bb8d` (tanks 5000/2500/1000 L, source SITE).
- D-DD.80 `a7b758a47` (C1, C2, S2 goldens from main's kernel), `5f40dee24` (cause index, `kernel/execute.py` only).
- DD3.2 commit 2 `e5fd43bfa`, `7c2709005`, `39ac029c1`: the `/2` file at the slot's mapping, manifest rev 16.18 Kobo
  `physical`, regenerated view/history.json/history golden/derived-values.json/mock fixtures/`PINNED_ALL_MONTHS`,
  re-based H10, K8_HISTORY_SHA, K13 in `check_manifest.py`; C-DD16 live with its test; W1 golden regenerated.

## Acceptance, one by one
- Data-sheet tool and labels (§6): `--check` exits 0 on the written file; residuals 10.50/10.50, 7.80/8.03, 5.60/5.56.
- D-DD.67/68: DATASHEET_FIT in both sets; parity golden holds the other bases.
- Writer (§4.1/4.2, DD3.1): C-DD12, C-DD21 pass; C-DD11 fails (Q4).
- D-DD.75 / D-DD.80 parity: K1-K8, D1, F1, X1, W1, S1, C1, C2, S2 green on the branch kernel (20 tests). C1 = S2 =
  `815d3901...`, C2 `ac72d516...`, from main's kernel, and green on the D-DD.75 kernel before the cause edit.
  Two mutation probes caught: POINT due set to the cause offset (C1, S2 fail); spread step 600 dropped (C2 fails).
- Reach (grep): only `Execution`/`_PHASES` reach the phases; `ColdExecution` (`execute.py:2088`) uses none; the EV
  writer does not import the kernel; `host/forward_replay.py` calls `execute` once and is unchanged. Contracts unchanged.
- D-DD.80 target: met (below). Stop rule not triggered.
- C-DD16 live: 12 properties and 2 ratings equal the slot's mapping (test failed 6/6 first, passes 6/6).
- Pure run gate (D-DD.19, D-DD.70): produced at 0.62 and 3.3; **a bound is hit** (overfill), see the tables; per D-DD.19
  this goes to the Architect before DD3 merges.

## Timings (wall, `tools/dd3_pure_run.py`, Kobo, through `tools/heavy-slot.sh`; host shared, load 3-4.7 on 8 cores)
| span | before D-DD.75 | after D-DD.75 | after D-DD.80 |
|---|---|---|---|
| 7 days | 7.3 s | 5.5 s | 4.7 s |
| 14 days | - | 15.3 s | 8.5 s |
| 28 days | - | 74.8 s | 16.2 s |
| 123 days 0.62 | - | > 10 min (stopped) | 138.4 s, rerun 106.1 s (byte-identical output) |
| 123 days 3.3 | - | not run | 66.4 s |

wall(28)/wall(14) = 1.90 (target 2.4). 28-day cProfile after: 37.2 s; `point_due_at` and `step_starts` are gone from the
top 15 (top: `minigrid.py:372 _one` 4.4 s, `str.split` 4.2 s, Fraction arithmetic, `_resolve_cycle` 1.2 s).

## Pure-run tables (2500 L tank, Jul-Oct; litres)
0.62 L/h: month, notes, accepted, refused, drawn, burned, tank min/max, balance, unserved kWh, gen h, stand-in candidate
- Jul 983 / 983.00 / 0 / 12 / 37.29 / 1212.32-2189.86 / 12.00 / 0 / 3.75 / 0
- Aug 967 / 322.14 / 644.86 / 12 / 0 / 2183.32-2500 / 12.00 / 0 / 0 / 0
- Sep 1035 / 363.57 / 671.43 / 11 / 744.16 / 2102.26-2500 / 11.00 / 0 / 74.50 / 60.94
- Oct 1180 / 897.42 / 282.58 / 120 / 507.86 / 2067.05-2500 / 120.00 / 0 / 51.17 / 42.03
3.3 L/h: Jul burned 38.09; Aug refused 644.06; Sep refused 664.10, burned 759.02, candidate 65.53; Oct refused 271.84,
burned 518.93, candidate 45.34; unserved 0 throughout. Both: `bound hit: YES` (overfill, BOUNDED_AND_RECORDED), not
stopped. The balance equals the drawn litres each month (the declared unexplained draw), as D-DD.19 intends.

## Checks run (revision 39ac029c1 unless stated)
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- `tools/checks/statement_catalogue.py`: exit 1, 146 lines, byte-identical to main `dd04e8d0f` (none from DD3a).
- `check_manifest.py`: 7792 passed, 6 failed, the same 6 as before commit 2. `check_alignment.py`: 110 passed, 4 failed,
  as at base.
- Scope (every test file importing kernel, telemetry, sites.models, fuel_cost_v2, chain.vocabulary; Postgres included):
  74 files on the branch, 70 on main `dd04e8d0f` (4 are new), one `heavy-slot.sh --db` call each. Branch: 2 failed,
  2558 passed, 3 errors (444 s); main: 2504 passed, 3 errors (490 s). The 3 errors are the same on both
  (`test_ch6b_estate_postgres.py` setup). Branch-only failures, both commit-2 followers (Q2):
  `test_dd3_datasheet_template.py::test_cli_check_reports_the_diff_then_write_makes_it_clean` (expects `--check` exit 1 on
  the unwritten file) and `test_dd3_telemetry.py::test_frozen_inputs_come_from_the_foundation_by_address` (40 -> 36).
- dd_check: C-DD12, C-DD16, C-DD21 PASS. **C-DD11 FAIL** (could not be judged): `world_history.py site-inputs
  --onboarding backend/tests/fixtures/on1` reads every `*.onboarding.json` there, including the `/1` Lakeside file and the
  cold and EV files, and `telemetry.site_inputs` raises `KeyError: 'rating'` (`telemetry.py:151`). With the `/2` file alone
  it runs. A DD3.1 defect (C-DD11 had never run green); not fixed in this round (Q4).

## Known deviations
1. Load and sun are hour-block WINDOW forcings (spec silent; Update 4).
2. `lakeside-power.v1.onboarding.json` declares no FUEL_TANK; no tank row added there (D-DD.76; would be design).
3. W1's golden was regenerated twice, each time with main's kernel because its INPUTS moved: by `ab349bb8d`'s onboarding
   tank rows (W1 was red at c35c50e92, missed in session 4), and by commit 2's rated power, SFC and battery rows, which
   `W1_ROWS` does not pin. The kernel never moved it (branch and main kernels give the same digest each time).
4. D-DD.75 edge: a zero-length forcing is skipped by the index (the old loop raised). D-DD.80 edge: a zero-length spread
   cause sits at step 0 so the old raise is kept; no case reaches either (setup refuses them).
5. C1's excluded cause: admitted by frozen inputs without a setup change (`UnmodelledInput(..., "CAUSAL_INPUT")`); C2's
   short last step: admitted (2467 min, last step 7 min).
6. Five hand-written test figures follow the regenerated world and were NOT updated (left red; see Risks).
7. `worked-portfolios.md:74` still reads "metered generator energy x 0.30 L/kWh = 1,060 L" (a declared input; not changed).

## Moved figures (for 0K4f, D-DD.30)
- `/2` file KOBO-001: generator rating and rated power 40 -> 36 (TEMPLATE v2 -> SITE v1); SFC 0.3 -> 0.2917; new no-load
  0.62 (DATASHEET_FIT), minimum load 30 and taper 95 (GENERIC_DEFAULT); battery 200 -> 191.5; each with a `-basis` sibling.
  Tanks (D-DD.76): Kisiwa 5000, Kobo 2500, Mto 1000 L; the writer's Kobo tank start 200 -> 1250 L.
- Manifest Kobo `physical`: genset_kw 40 -> 36, sfc 0.30 -> 0.2917, battery_kwh 200 -> 191.5; `worked-portfolios.md:59`.
- history.json Kobo actual Jul / Aug / Sep: delivered kWh 8592->8767 / 8669->8663 / 8646->8870; technical loss
  387->395 / 391->390 / 390->400; necessary L 711->730 / 701->721 / 658->662; candidate L 260->265 / 254->266 / 366->363.
- derived-values (history part), Kobo July: billed 8163->8329, revenue 3265.20->3331.60, collected 3002.73->3063.78,
  diesel 983->1007, fuel cost 1228.75->1258.75; contribution Jul/Aug/Sep 936.45->972.85, 985.25->943.25,
  891.45->975.40; portfolio contribution 1310.85->1347.25, 1429.85->1387.85, 1594.15->1678.10. October unchanged (H8).
- Export digests: billing, collections, expenses, all months (`PINNED_ALL_MONTHS`); October `PINNED` unchanged.

## Fix round (D-DD.93-96)
Commits `12528fd24` (D-DD.95), `9e986aa7f` (D-DD.93), `61714a300` (D-DD.94), then this packet. D-DD.92 (fuel purchases follow
the tank) is DD3b's and is not built. Units 5.75 (D-DD.96).
- **D-DD.95** `tools/world_history.py` `site-inputs` reads `assetops.operator-onboarding/2` documents only (others: stderr
  `SKIPPED <file> <format>`), refuses a Site code in two read documents (`TEL_FOUNDATION <code> is in A and B`, exit 3);
  `telemetry.site_inputs` writes `rating` only when the component has one. Tests `simulator/tests/world/test_dd3_site_inputs_cli.py`
  (4: `/1` skipped and the on1 directory runs, Lakeside entries from on1 equal `/2` alone with the golden sha256
  `4e36563d...333d9` from the branch's `/2`-only run, no-rating component passes, duplicate refuses); all 4 failed on the
  pre-change code and pass now. C-DD11 now PASSES (below).
- **D-DD.93** old -> new: `test_dd3_telemetry` rated power 40 -> 36, SFC Fraction(3,10) -> Fraction(2917,10000);
  `test_dd2_nodes` July billed 8163 -> 8329, revenue 3265.20 -> 3331.60, collected 3002.73 -> 3063.78, fuel litres
  711+260+12 -> 730+265+12 (1007); `test_dd2_checker` C-DD4 plant "stored 8164 != evaluated 8163" -> "8330 != 8329";
  backend `test_dd2_check` billed 8163 -> 8329, revenue 3265.2 -> 3331.6, collected 3002.73 -> 3063.78, diesel 983 -> 1007,
  fuel cost 1228.75 -> 1258.75 (each from the regenerated `derived-values`/`history.json`, checked by running the
  evaluator). `test_dd3_datasheet_template` CLI check now works on a `tmp_path` copy with the no-load rate reverted to 0.99:
  `--check` exit 1 and the diff line, `--write` exit 0, `--check` exit 0.
- **D-DD.94** `worked-portfolios.md:74` "x 0.30 L/kWh" -> "x 0.2917 `<!--rec:...Kobo.physical.sfc_l_per_kwh-->` L/kWh";
  1,060 L unchanged. Sweep of Kobo hand-typed figures in the Layer-4 docs: `domain-and-decision-models.md:484` "30 kW on
  200 kWh = 0.15C" -> `30`/`191.5` rec references, 0.157C. Other hits are not Kobo's (Mto, EV) or historical review files
  (`REVIEW*.md`). **Not converted:** the vNEXT mock hand-types Kobo's 200 kWh (18 places in `screens.js`, 5 in the generated
  `screen-manifest-vnext.json`), 40 kW (4) and 0.30 L/kWh (3: `screens.js` lines 112, 279, 478): the mock has no `rec`/`fig`
  mechanism and is regenerated by its audit, so converting them is mock work for the W1-conclusion pass; the owner may
  route it. `check_alignment.py`: 110 passed, 4 failed (as base). `check_manifest.py`: 7795 passed, 6 failed (7792 + the 3
  new rec markers; the same 6 failures; the H9 baseline line is one of them, as before).
- **Guards** (revision `61714a300`): `check-architecture.ps1` passed; `check-agent-workflow.ps1` passed;
  `statement_catalogue.py` exit 0 ("OK statement catalogue", 3 ALLOWED entries).
- **dd_check** (after the last code commit): C-DD11 PASS (18 files compared), C-DD12 PASS (19 modules), C-DD16 PASS,
  C-DD21 PASS (17 rows).
- **Further followers fixed** (DD3.1 made them red; the earlier scope run missed them): `test_dd1_check` stub set and
  no-shared-module guard and `test_dd2_check` no-simulator-import guard now allow the one import C-DD21 needs (the writer's
  `telemetry`, inside `check_property_table_parity` only); DS1 guards `test_t6_greps[\b31\b]`,
  `test_t8_cli_has_no_literal_month_length` (telemetry.py's end-of-October date and the CLI `--end` default are built from
  1 Nov minus a day; same values) and `test_t3b_name_absent_from_generator` (skips `telemetry.py`, the named answer-block
  refuser that C-DD12 scans).
- **Scope** (every test file importing a touched module; one heavy-slot call per tree): branch backend+tools 194 passed;
  branch simulator+host 272 passed; main `c51ce8004` backend 169 passed, simulator+host 231 passed (the difference is the
  branch's new files). No failures when each tree runs in its own call (a mixed backend+simulator call collides on the
  module name `world`: `test_ds4_world.py` 24 failures and 39 errors, the same on main).

## Fix round 2, run 1 (D-DD.102)
Commits `f33745834` (merge main, L6), `aaec9b147` (cold golden from main, before the change), `23b22334b` tests first
(16 red on the pre-change code), `0945812c2` the change, `0aec5ea16` regeneration and re-pins. Run 2 (L2, L3, L5, slice end)
is not built here.
- **L6 merge.** Main at `108af5378` merged. Conflicts: `.ai/state/index-3.md` (both rows kept: IA-P2 is 205, DD3a
  becomes 206) and `backend/tests/test_sc1_statements.py` (both key lists kept). `tools/checks/statement_catalogue.py`
  on the merged head: "OK statement catalogue: load, coverage, legacy, scan (9 adopted), keys, imports", exit 0, output
  identical to main's (3 ALLOWED entries).
- **Change.** `world/scope.py`: `PHYSICAL_READS = {"fleet_kwh": ("buses", "kwh_per_bus_night"), "fleet_nights":
  ("buses",)}` and `physical_read(site_doc, rules)` (first whitespace token of every string rule on both sides; sorted
  read keys present in the block; `{}` without a block). `scope_input` writes `site.physical` only when non-empty.
  `world/history.py`: `_Scope` stores the restricted dict and `_Scope.physical(name, leaf)` reads only it, so a read not
  declared for its word refuses `HISTORY_RULE_REF` (tested by narrowing the table). Naming deviation: the ruling says
  `self.physical = physical_read(...)`, but `physical` is already the read method, so the attribute is `physical_keys`.
- **Tests** `simulator/tests/world/test_scope_physical_reads.py` (23): cold fixture scopes and cold `history.json` blocks
  equal the golden `simulator/tests/world/golden/physical_reads_cold_main.json` (computed from main's files at
  `108af5378` with main's scope/history modules, which the branch had not changed; committed before the change); kit
  invariance at all six Sites with a block (every unread key replaced and a new key added; Kobo with main's 40 / 0.30 /
  200) leaves every scope block, digest included, byte-identical; Embakasi `buses` + 1 moves exactly Embakasi's three
  scopes; mini-grid and cold scope inputs have no `physical`; depot inputs hold exactly `buses`, `kwh_per_bus_night`;
  the table as declared; an undeclared read refuses; `history.json` is the fixture view's history. The comparison is
  of scope blocks: `meta.view_digest` covers the whole view (DS1) and moves with any view change, by design.
- **Regeneration** (as commit 2 ran it): the view is unchanged (`world_history.py view` = `view_v1.json`);
  `world_history.py generate` then `check` (exit 0); history golden by `--update-golden` on `test_t2_golden`;
  `gen_fixtures.py` (evaluate_structure.py; "evaluator vs stated fields: 0 differences") and `build.mjs`. Only the
  `history` part of `derived-values.json` moved; `missing-records.json` unchanged.
- **Re-pins** (D-DD.93's rule, each literal the regenerated value): K8 `history.json` 329181f2... -> 6fd61089...; K13
  `derived-values.json` history 3de20420... -> 57bac43d...; `PINNED_ALL_MONTHS` billing 60c2ac9e... -> 96fc678b...,
  collections 1ae56f43... -> 6f45cdb5..., expenses 8a0a1102... -> bc991181... (budget, `PINNED`, `PINNED_COLD_EV`
  unchanged); `test_dd2_nodes` Kobo July billed 8329 -> 8318, revenue 3331.60 -> 3327.20, collected 3063.78 -> 3059.74,
  fuel 730+265+12 -> 703+257+12; `test_dd2_checker_on_emulated_rows` plant "8330 != 8329" -> "8319 != 8318"; backend
  `test_dd2_check` July 8329 -> 8318, 3331.6 -> 3327.2, 3063.78 -> 3059.74, diesel 1007 -> 972, fuel cost 1258.75 -> 1215.
  `dd_check` reads the history golden's `file_sha256`, so it follows the golden.

### Moved figures (D-DD.102), by Site
history.json leaves, actual side only (plan unchanged everywhere):
- **Kobo** Jul: delivered 8767->8755, technical loss 395->394, necessary L 730->703, candidate L 265->257, outstanding
  26782->26746 c. Aug: delivered 8663->8577, loss 390->386, adjustments 43->42, necessary 721->717, candidate 266->273,
  outstanding 26466->26201. Sep: delivered 8870->8690, loss 400->392, adjustments 44->43, necessary 662->648, candidate
  363->344, outstanding 27097->26549.
- **Kisiwa** Jul: delivered 7654->7697, loss 501->503, necessary 2377->2333, outstanding 25996->26142. Aug: 7582->7651,
  496->500, 2286->2320, 25750->25983. Sep: 7619->7812, 498->511, 2165->2116, 25876->26530.
- **Mto** Jul: delivered 5726->5881, adjustments 38->39, expected technical loss 286->294, unexplained 115->118, necessary
  314->319, outstanding 11452->11761. Aug: 5676->5831, 38->39, 284->292, 114->117, 309->318, 11351->11662. Sep: delivered
  5821->5825, necessary 288->293, outstanding 11643->11650.
- **Embakasi, Kasarani, Ruiru**: the nine scope digests only (their `physical` input is now `buses` and
  `kwh_per_bus_night`); no leaf moved (the EV rules take no jitter), so no export or derived figure moved.
- **Room A, B, C**: none (golden parity, 9 + 9 scopes).

derived-values.json `history` (actual nodes; plan unchanged):
- Kisiwa 2026-07: billed_kwh 7124->7165; collected 3658.24->3679.33; contribution -397.9->-318.15; cost_to_serve 4316.1->4258.9; delivered_kwh 7654->7697; diesel_l 2397->2353; fuel_cost 3116.1->3058.9; metered_kwh 7153->7194; necessary_l 2377->2333; outstanding 259.96->261.42; revenue 3918.2->3940.75; technical_loss_kwh 501->503.
- Kisiwa 2026-08: billed_kwh 7057->7122; collected 3623.85->3657.27; contribution -315.15->-323.6; cost_to_serve 4196.5->4240.7; delivered_kwh 7582->7651; diesel_l 2305->2339; fuel_cost 2996.5->3040.7; metered_kwh 7086->7151; necessary_l 2286->2320; outstanding 257.5->259.83; revenue 3881.35->3917.1; technical_loss_kwh 496->500.
- Kisiwa 2026-09: billed_kwh 7092->7272; collected 3641.84->3734.3; contribution -137.3->25.4; cost_to_serve 4037.9->3974.2; delivered_kwh 7619->7812; diesel_l 2183->2134; fuel_cost 2837.9->2774.2; metered_kwh 7121->7301; necessary_l 2165->2116; outstanding 258.76->265.3; revenue 3900.6->3999.6; technical_loss_kwh 498->511.
- Kobo 2026-07: billed_kwh 8329->8318; candidate_l 265->257; collected 3063.78->3059.74; contribution 972.85->1012.2; cost_to_serve 2358.75->2315; delivered_kwh 8767->8755; diesel_l 1007->972; fuel_cost 1258.75->1215; metered_kwh 8372->8361; necessary_l 730->703; outstanding 267.82->267.46; revenue 3331.6->3327.2; technical_loss_kwh 395->394.
- Kobo 2026-08: adjustments_kwh 43->42; billed_kwh 8230->8149; candidate_l 266->273; collected 3027.34->2997.59; contribution 943.25->907.1; cost_to_serve 2348.75->2352.5; delivered_kwh 8663->8577; diesel_l 999->1002; fuel_cost 1248.75->1252.5; metered_kwh 8273->8191; necessary_l 721->717; outstanding 264.66->262.01; revenue 3292->3259.6; technical_loss_kwh 390->386.
- Kobo 2026-09: adjustments_kwh 44->43; billed_kwh 8426->8255; candidate_l 363->344; collected 3099.43->3036.51; contribution 975.4->948.25; cost_to_serve 2395->2353.75; delivered_kwh 8870->8690; diesel_l 1036->1003; fuel_cost 1295->1253.75; metered_kwh 8470->8298; necessary_l 662->648; outstanding 270.97->265.49; revenue 3370.4->3302; technical_loss_kwh 400->392.
- Mto 2026-07: adjustments_kwh 38->39; billed_kwh 5287->5430; collected 2000.28->2054.39; contribution 772.3->823.25; cost_to_serve 1342.5->1348.75; delivered_kwh 5726->5881; diesel_l 314->319; fuel_cost 392.5->398.75; metered_kwh 5325->5469; necessary_l 314->319; outstanding 114.52->117.61; revenue 2114.8->2172; technical_loss_kwh 286->294; unexplained_loss_kwh 115->118.
- Mto 2026-08: adjustments_kwh 38->39; billed_kwh 5240->5383; collected 1982.49->2036.58; contribution 759.75->805.7; cost_to_serve 1336.25->1347.5; delivered_kwh 5676->5831; diesel_l 309->318; fuel_cost 386.25->397.5; metered_kwh 5278->5422; necessary_l 309->318; outstanding 113.51->116.62; revenue 2096->2153.2; technical_loss_kwh 284->292; unexplained_loss_kwh 114->117.
- Mto 2026-09: billed_kwh 5375->5379; collected 2033.57->2035.1; contribution 840->835.35; cost_to_serve 1310->1316.25; delivered_kwh 5821->5825; diesel_l 288->293; fuel_cost 360->366.25; metered_kwh 5414->5418; necessary_l 288->293; outstanding 116.43->116.5; revenue 2150->2151.6.
- Site contribution Jul/Aug/Sep: Kobo 972.85->1012.20, 943.25->907.10, 975.40->948.25; Kisiwa -397.90->-318.15,
  -315.15->-323.60, -137.30->+25.40 (September turns positive); Mto 772.30->823.25, 759.75->805.70, 840.00->835.35.
- Site gap Jul/Aug/Sep: Kobo -472.15->-432.80, -501.75->-537.90, -387.95->-415.10; Kisiwa -332.90->-253.15,
  -250.15->-258.60, -35.40->+127.30; Mto -142.70->-91.75, -155.25->-109.30, -15.10->-19.75.
- Lakeside portfolio contribution 1347.25->1517.30, 1387.85->1389.20, 1678.10->1809.00; gap -947.75->-777.70,
  -907.15->-905.80, -438.45->-307.55. October unchanged (H8). Metro-bus and harvest-cold: no derived figure moved.

### Sweep (W6): every digest-input key and the rule word that reads it
Words in use: mini-grid `fixed, per_day, plan_value, scale, zero`; EV `fixed, fleet_kwh, per_day, plan_value, rest, share`;
cold `cold_kwh, fixed, occupancy, per_day, plan_value, ratio, zero`.
- `generator`: no rule; the generator identity (a version constant whose change is meant to re-seed). Reported.
- `month`: every word (days, season weight, seed key).
- `history_global.months`: list rules `occupancy`, `cold_kwh`, `share` (the Jul/Aug/Sep position); no mini-grid word
  reads it (it is also the scope set itself). Reported: unread by mini-grid scopes.
- `history_global.anchor_period`: `per_day` (anchor days), the family words' weight ratio, `occupancy`/`cold_kwh` anchor.
- `history_global.seasons`, `day_classes`, `families`: the family words `scale` (mini-grid) and `cold_kwh` (cold); no
  EV word reads them. `seasons` is D-DD.90's (DD4a). Reported: `day_classes` and `families` unread by EV scopes.
- `history_global.money_leaves`: every word reading an October money leaf (cents conversion).
- `rules`: every word (the scope's own rules).
- `tenant.tenant`, `tenant.vertical`: the scope key and the rule table chosen; `tenant.energy_model`: `cold_kwh`;
  `tenant.capacity_crates_per_room`: `occupancy` (both only on the cold tenant, whose rules read them).
- `site.site`: the scope key; `site.code`: no rule reads it. Reported.
- `site.period`: every word reading October (`per_day, fixed, plan_value, scale, ratio, share, occupancy, cold_kwh`).
- `site.physical`: now exactly `PHYSICAL_READS` (`fleet_kwh`, `fleet_nights`), D-DD.102.
None of the reported items is changed in this round.

### Checks (branch at `0aec5ea16`; main at `108af5378` in a temporary detached worktree, removed after)
- `ASSETOPS_GUARD_PYTHON=... pwsh tools/check-architecture.ps1`: "Architecture check passed."; `check-agent-workflow.ps1`:
  "Agent workflow check passed."; `statement_catalogue.py`: exit 0, output identical to main's (above).
- Simulator, all `simulator/tests/world/test_*.py` (`heavy-slot.sh -- run-host-tests.ps1`): branch 275 passed (37 s;
  before the re-pins: 5 failed, 8 errors, all pins and the dd_check golden sha); main 231 passed (25 s; the branch adds
  the 23 new tests and DD3a's own).
- Backend + host, one `--db` call per tree: the importers of a touched module or file (`test_3a1`, `test_3a3_load_emulated`,
  `test_3b1`-`3b4`, `test_3b6`, `test_4b_money_leaves`, `test_5a_targets`, `test_5b_attribution`, `test_dd1_check`,
  `test_ddr_rehearsal_postgres`, `test_ds4_world`, `test_on1_served_tenant`, `test_wk_walk_world`,
  `test_2a_canonical_manifest_parity`, `test_dd2_check`, `test_dd3_*` (3), `test_sc1_statements`,
  `host/tests/test_kernel_forcing_index_parity.py`, `host/tests/test_0m_mto_headroom.py`,
  `tools/checks/test_select_tests_neutral.py`): branch 1200 passed, 2 failed, 1 skipped (340 s); main (the four
  branch-only files absent) 1155 passed, 2 failed, 1 skipped (284 s). The 2 are the same on both: `test_3b1 ... t1_leaf_sources`
  and `test_3b3 ... t6_each_state` ("dispatch-3.3" vs the manifest's "dispatch-3.2"), main's failures.
- `check_manifest.py`: 7795 passed, 6 failed (walkthroughs, A1, A2, A3, A5, H9: the branch baseline the review lists).
  K8 and K13 failed before their re-base and pass after.

## Fix round 2, run 2 (D-DD.106 L2, L3, L5; D-DD.105)
- Main merged again (clean; index rows kept). `statement_catalogue.py` rerun after the merge (result under Checks, below).
- **L2.** `telemetry.py` declares `SEASON_V2_DAYS = 61` and `SEASON_V2_LAST_DAY = SEASON_V2_DAY_ZERO + timedelta(days=SEASON_V2_DAYS - 1)`;
  no month-end literal. `world_history.py telemetry --end` defaults to `None` and resolves to
  `period_end(view["accounting_period"])` (D-DD.103's `READINGS_SPAN` replaces it later). No guard was given an allowance.
  Tests: `simulator/tests/world/test_records.py` (`test_l2_*`), `host/tests/test_0k4c_season_v2.py`
  (`SEASON_V2_DAYS == kobo_season.SEASON_DAYS`).
- **L5 (the tank's moved product readers).** Every reader of `tank-capacity` on a Lakeside Site sees 2500/5000/1000 L once DD5
  loads the `/2` file: `runs/profiles.py:910-920` (`fuel-tank-capacity`, frozen into lab runs) and
  `runs/operational_actions.py:76` (`CAPACITY_STATE`). Nothing served moves before DD5.
- **D-DD.105.** The mock's Kobo kit strings ("200 kWh", "40 kW", "0.30 L/kWh" in `screens.js` and
  `screen-manifest-vnext.json`) go to the design-doc alignment pass queued in `.ai/NOW.md`, not this slice.
- **L3.** `.ai/state/data.md` and `.ai/state/index-3.md` "Open" now name the true open items (D-DD.92, D-DD.103, D-DD.104, D-DD.97, mock kit).

## Residual risk and questions
- Q1 (gate, D-DD.19): overfill bound hit Aug-Oct at both rates (about 270-670 L refused a month). The stated fallback
  (notes restated from a reorder rule at 25 %) is the Architect's call; it would move the books and history again.
- Q2: the five red test figures (`test_dd2_nodes` July, `test_dd2_checker` C-DD4 plant, `test_dd3_telemetry` frozen 40
  -> 36 and 0.3 -> 0.2917, backend `test_dd2_check` July by hand) follow the regenerated world; the commit-2 builder
  reports its edit to them was denied, so they are left red for the coordinator to decide.
- Q3: `worked-portfolios.md:74` arithmetic (0.30 L/kWh) vs the new 0.2917.
- Q4: C-DD11 / `site-inputs` directory read (above): read only the `/2` files, or skip components without a rating?
  Either is a choice the spec does not make; the build stops here for it.
- Timings were taken on a shared host (other lanes' jobs running); both 123-day runs are under 3 minutes regardless.

## Review focus
`kernel/execute.py` `_steps_overlapping`, `_cause_index`, `_ensure_cause_index`, the two phase loops (byte-identity
argument D-DD.80 (a)-(d)); the parity cases C1/C2/S2; commit 2's regeneration chain and re-based pins.
