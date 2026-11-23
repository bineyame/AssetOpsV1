# DD3d-b handoff (partial: run 1 stopped at its context budget, 23 Nov)

Branch `task/DD3d-b-fuel-cost`, worktree `/opt/assetecon/AssetOpsV1-dd3db`, cut from main aae7d9826. Card
`cards/DD3d.md` Part DD3d-b, **as amended by `rulings.md` round 28 (D-DD.177 to D-DD.180, the last 80 lines: read them
first)**. Evidence `/opt/assetecon/evidence/DD3d/b/`. No job is running. Architect questions: one batch of four,
answered by an `assetops-architect` subagent this builder spawned (no lane-Architect session was asked): the
coordinator should confirm the four rulings. The branch is RED by design until the tests below follow (116 pure failures).

## Done (DD3d.4, product part; not reviewed, no Postgres run yet)
- `test_dd3d_fuel_cost.py` (9): 6 failed first (`fuel-cost-first.log`). Rows v5, `STATED_STATE`, `money.FUEL_BOUGHT`,
  `_ROWS`/`READ_AS` `fuel_bought`; reconciliation heading key `fuel_bought` / word `FUEL_BOUGHT` (label "Fuel bought
  (invoices)", record noun "fuel invoices"); statement field and flag unchanged.
- `evaluate(..., stated_nodes=)`, `targets/rules.BUDGET_STATED`, `targets/read.py` (D-DD.178). Its tests are not written.
- `publish_assumption.py` checks `served_tenant_slug()` (exit stays 2, D-DD.179); a malformed slug is a traceback at
  parse, handle `ConfigurationError`. Three fixtures `backend/conversions/world/lakeside-power.diesel-price.*.json`
  (parity test in place). Publisher tests in `test_s4_assumptions_postgres.py` are not written.
- Rulings and index lines appended.

## Pure failures to work (`pure-1.log`; rerun `/opt/assetecon/evidence/DD3d/b/pure.sh LOG`, 80 s)
1. Renames and version pins (mechanical): 3a7 x15 ("fuel_cost" heading key -> "fuel_bought", "Fuel cost (" -> "Fuel
   bought (invoices) ("), `statement_cases/{worked,reconciliation}.py` (`FUEL_COST` -> `FUEL_BOUGHT`), 3b1 x2, 3b3 x3,
   4a x1, 4b1 x9 (fuel_cost was one of the stated examples: move them to `revenue`), 5a x1 (a table), 6a x1.
2. Worlds that state fuel by invoices and hold no litres (4b money x10, 4d x4, 5b x5, 5c view x23 + api x2 +
   screen_worlds_fresh x2, iap x17, 3b7a x7, sc1 x14): 4b's assertions become "not available, the litre leaves named";
   the 5b/5c/iap/3b7a worlds need litres. Plan: one helper (`backend/tests/pack_litres.py`) wrapping `fallback()` with
   MODELLED litre leaves per Site so the pack's figures hold: Kobo 730/330/120 (already `test_4d.LakesideInputs`),
   Kisiwa 2,400 x 1.30 = 3,120, Mto 320 x 1.25 = 400; used by `t5b.reads` (line 462, 838), `served_world` (5c view
   line 72), `3b7a setup`. `fb=` is already a parameter of `3b7a.setup` / `served_world`. Literals then change only in
   evidence words and SPLIT (fuel now splits into litres): World A's "not split to its drivers yet" lines, the litre
   rows of `not_available`, and fixture `5c/deep_dive_lakeside_2026-10.json`, the `statement_cases/deep_dive.py`,
   `frontend/src/estate/__tests__/fixtures/*` regenerate from the same worlds (list each in the packet).

## Next, in order
1. The tests above; D-DD.178 tests; publisher Postgres tests; G4 + its tests (`test_ddr_rehearsal_check.py`): code
   `rehearsal_check.py:380` loop, `PRICE_SOURCE`; declared price is evidence ESTIMATED/ASSUMED per
   `sources.ASSUMPTION_WORDS["diesel_price"]`, prints "declared, no fuel invoice this month".
2. DDR (D-DD.177): `LitreLeafSource._month` replaced in the fixture from `M`; `fuel_bought` key; S5/S8 offsets;
   `test_7`; runbook sentence. C4 classes in `tools/world.py` (Mto plan classes only in DD3d.5's commit).
3. `dd_check` C-DD4 fuel clause (D-DD.180), tests in `test_dd2_check.py`.
4. DD3d-a Lows L1 to L6 (`review-DD3d-a.md`): not started.
5. DD3d.5 whole: `--leaves` `quarter`, `RUN_WRITTEN["MINI_GRID"]["plan"]`, guard test, `M`, then the D-DD.176 form of
   the acceptance (generate 2 and 3 byte-identical, every `--check` 0), D-DD.30 chain, re-pins, anchors, A114 confirm.
6. Plants a to d (a amended by D-DD.177), reach set once, guards, packet, state entry, spec in_review. Amend the DD5b
   card with D-DD.177's "DD5b card gains" lines and the DD3d card's plant (a) and C-DD4 lines.

## Anchors and risks
- `M` line 83 prices; `M`'s Kisiwa October litres are 903, so fuel projects 2,006.40 and the headline about −195.30
  (not −196.60); owner to be told. No served figure was measured in this run.
- `targets/read.py` `MAIN_OF` heading fuel_cost; `deep_dive/tables.py:46` evidence `FUEL_INVOICES` needs no edit.
- `tools/dd3_pure_run.py`: `october_leaves` 254, `print_leaves` 326, `LEDGER_KEYS` 53. `world/scope.py` `RUN_WRITTEN`.
- `world/history.py` `RUN_DERIVED` may gain plan keys computed from the new `RUN_WRITTEN` plan keys (`per_day`): check
  before step 5's diff (D-DD.176 5c).


## Run 2 (23 Nov, partial; stopped at the context budget) 
Branch head: see `git log -1`. Merged `fix/main-4d-litre` (coordinator order). Classification of the 116:
`/opt/assetecon/evidence/DD3d/b/classification-116.md` (49 rename/version pin, 67 world without litres, 0 other).
Done and green (pure): 3a7 x4 files, sc1, statement_cases, 3b1, 3b3, 3b7a seam/snapshot, 4a, 4b1, 4b (money: fuel_cost,
cost_to_serve, contribution not available with the litre leaves named; invoices read through `_judge(..., "fuel_bought")`
helpers `bought`/`assert_fuel_not_available`), 4d, 5a, 5b, 6a, 3b4 observer. New `backend/tests/pack_litres.py`
(`with_litres()`: October litres of the three lakeside Sites from `derived-values.json`, MODELLED, origin unknown, source
`test:M-october-litres`); used by 5b `reads`, 3b7a `fresh` default. Pure rerun (`pure-4.log`): 23 failed before the 3b4 fix
(now 22): 5c api x2, 5c view x9, 5c screen_worlds_fresh x2, iap period x3, iap sites x6.
Choices recorded (defaults, no owner question): (1) litre leaves are to the millilitre so figures carry a third decimal
(1565.500); the 5b `money` helper and `by_home` text compare numerically exact and quantize the text to the cent.
(2) Evidence words of Kobo/Kisiwa/Mto contribution and cost lines are now MODELLED (litres modelled), origins gain
"unknown" (5b, 3b7a). (3) 3b7a `untracked` now lists the three litre leaves of every Site (not commercial records).
(4) 4d: Kisiwa/Mto root NOT_SPLIT GAP_NOT_AVAILABLE; portfolio fuel effect 82.50 of 1 of 3. (5) 3b4: candidate_l and
unexplained_l are now RAISED. (6) 4b test_1 no longer compares Kobo contribution to the pack (no litres there); the pack
comparison belongs in a litre world: restore it in a 5b test (open). (7) `_check_stated` takes `also` (call-site updated).
## Next (remaining of steps 1-3)
- 5c view x9, api x2, screen_worlds_fresh x2 (regenerate `fixtures/5c/*` via `make_screen_worlds.py` with litres, list each in the
  packet), iap period x3 / sites x6 (`IAP_WRITE_FIXTURES=1` regenerates `fixtures/iap`; frontend `sitesList.test.tsx`
  "World A, October" and estate fixtures regenerate from the same worlds). iap 6 and 8 stay until DD3d.5 (coordinator).
  `served_world` takes `fb=`; 3b7a `setup` default is now `with_litres()` so 5c/iap worlds get litres through it: check
  why 5c still fails (evidence words Modelled, "of 3 Sites" lines, SPLIT lines, standing text).
- D-DD.178 tests (target values byte-identical on 5a fixtures; Mto no price: budget line Declared; `STRUCTURE_STATED`
  without `stated_nodes`; every `BUDGET_STATED` node non-leaf/SUM/money-or-kWh) in `test_dd3d_fuel_cost.py`, shown failing first.
- Publisher tests (`test_s4_assumptions_postgres.py`, D-DD.179), G4 + `test_ddr_rehearsal_check.py`, DDR (D-DD.177), C4 classes
  `tools/world.py`, C-DD4 fuel clause + tests (`test_dd2_check.py`, D-DD.180). None started. Postgres run not done.
- Coordinator items: (2) 5c standing fixture input moved (accounts 5,100 to 2,100) untouched; (3) 3b1 t1 / 3b3 t6 manifest
  version replacement kept as merged.

## Run 3 (23 Nov): pure suite green but iap 6 and 8; run 2's checks repaired
Pure (`pure.sh pure-6.log`, 104 s): 2 failed (iap sites 6 and 8, held for DD3d.5), 2,365 passed, 1 skipped. Also 0k4b and wk:
120 passed. Frontend `src/estate` + three shell files that read the fixtures: all pass. Statement catalogue exit 0 (it was
red since run 1), architecture and agent-workflow pass. No Postgres run. Mutations: `mutations-r3.log` (10, each fails its test).

1. **Served money text.** Every served money figure goes through `i18n.formats.money` (cents, half-even) except one: tile 1's
   `bar` was `str()` of the stored figure in `deep_dive/view.py` and `period.py`, so the API served `4431.600`, and 4299.87125 in
   a world where Kobo burned 739.383 L. Product fault, fixed: `deep_dive.words.plain` (the money rule's cents, half-even, as a
   bare decimal); stored values stay exact. Failing first: `served-money-first.log`; tests `test_served_money_is_whole_cents`,
   `test_bar_text_is_moneys_rule` (5c), `test_2c_money_text_is_whole_cents` (iap period). `test_5b` compares the exact value and
   the text through `plain`, no rounding of its own. Readers checked: snapshot payload (stored, exact), observer claims (leaves
   only, no litres x price), decisions (`evaluate_options.money`, cents), 3A7 (invoices), `rehearsal_check._money` (cents),
   `walk_world` (numeric compare: it failed on a real third-decimal difference only), frontend (bar widths only).
2. **Checks restored** (where each lives now).
   - Kobo contribution, cost to serve, fuel cost, litres against the pack; their sources, origins, `missing_leaves ()`,
     `detail_missing`; Kisiwa `("om",)` alone: 4b `test_1b_october_with_litres_is_the_packs`.
   - Kobo and Kisiwa fuel invoices' currency, evidence, source, origin: 4b `invoice_facts`. Revenue's `detail_missing`, price
     not the fallback's: back in `check_kobo_october`.
   - Portfolio fuel cost (3 of 3) and contribution (1 of 3) with words: 4b `test_3b_portfolio_with_litres`.
   - 3A4's 1,500.00 / -1,004.50 / -887.00: 4b `test_4b_3a4_fixture_with_litres`.
   - 4d portfolio fuel over three Sites (2,233.60, 3 of 3, the split adds up): `test_6_the_portfolio_over_three_sites`.
   - Litre leaves not available in the 5b world: 3b4 `test_8b_5b_world_without_litres`. Kobo and Kisiwa untracked `()`: 3b7a
     `test_3_a_site_on_commercial_records_alone_is_tracked`.
   - 5c stop and out sentences for fuel without litres (EMS, curve, dips, delivery notes, setup), "1 of 3 Sites" drivers: world
     HK, `test_4_hk_two_sites_without_litres`. iap Site below target (order, count, cost driver): `test_1b_sites_below_target`;
     the browser's Below-target facet: `sitesList.test.tsx`.
   - Gone with its state, not restored: "fuel cost valued but not split" (5b `FUEL_UNOBSERVED`, removed). A fuel cost has a value
     only when its litres do, so it always splits. The rule itself stays tested on revenue.
3. **3b4 is right at Kobo, from the rule.** `candidate_l` and `unexplained_l` are observed UP (`observe/rules.py`) with target 0
   (LEAK_ZERO, P5 rule 3). Candidate has no tolerance row, so NONE, band 0: 25 > 0, RAISED. Unexplained has 2 % of `diesel_l`:
   12.68 L, and with Kobo's declared floor 2a = 50 L (D-DD.153, whose table says October RAISED): 120 > 50, RAISED. Necessary
   489 against 700 is FAVOURABLE. The test pins target, gap, band, tolerance source and the floored case.
4. **Fixtures regenerated**, from the same worlds: `backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json` (from `view("A")`);
   `frontend/src/estate/__tests__/fixtures/deep_dive_world_h.json`, `deep_dive_currency_mismatch.json` (`make_screen_worlds.py`);
   `fixtures/iap/`: `month-g-2026-10`, `period-period-2026-09-10`, `period-period-g-2026-09-10`, `sites-2026-09-10`,
   `sites-2026-10`, `sites-g-2026-09-10`, `sites-g-2026-10` (`IAP_WRITE_FIXTURES=1`). New golden
   `backend/tests/golden/dd3d_targets_before.json`, written by the test's own function on aae7d9826 (v4). World H is now Kobo's
   own litres beside the pack's (all three Sites); World A is the pack's at all three.
5. **D-DD.178 tests** 7 to 13 in `test_dd3d_fuel_cost.py`. `stated_nodes` naming a leaf or unknown row was accepted: now
   `STRUCTURE_STATED` (tests 11 failed first). 0k4b p6: the two `pv-array-share` names added.

Open, with defaults (none acted on):
- (a) **Blocker for L2 and DDR, not for this branch:** litres are no commercial record, so every served litre world carries
  `fresh.untracked_text` ("Not checked for later changes: ..."), and `rehearsal_check` G9 (`UNTRACKED`) and `walk_world` fail on
  any text. It also fails D-DD.177's DDR fixture (source `test:M-october-litres`). Default: both judge it against an expected
  text in the expect file; the product keeps saying it until 3B7b tracks readings.
- (b) "86.7% of cost from figures received": unchanged number, but fuel is now modelled litres x price, not a figure received.
  The ratio only takes out O&M carried at its budget. Default: the words change in the copy pass; the ratio stays.
- (c) The 5c standing input (accounts 5,100 to 2,100): default keep 2,100.00 against 2,006.40 (the world's invoices), because
  5,100 against 2,006.40 is a 60 % miss and tests a different case; but the canned sentence says "Fuel cost" and the product
  now says "Fuel bought (invoices)": change it with the 5c Postgres test in the Postgres run.
- (d) 3b1 t1 / 3b3 t6 replace `dispatch-3.2`: default keep until the owner's pack names dispatch-3.3 (D-0K4.10), then delete.
- (e) World A pins no Site below target (D-DD.164's figures); DD3d.5 moves them again, then iap 6 and 8 and the turned world go.
- (f) `publish_assumption`'s refusal is now `TENANT_NOT_SERVED <slug>` (the catalogue refuses a new hand-built sentence).

## Run 4 (23 Nov): the parts run 3's open questions do not block. DD3d.5 not started
Commits on 39c9fd2de: publisher tests, C4 classes, C-DD4's fuel clause, DD3d-a's Lows, the price SQL's boundary test.

1. **Publisher Postgres tests** (D-DD.169, D-DD.179; `test_s4_assumptions_postgres.py`, class `TestServedTenant`): the three world
   files publish to the served tenant (named and by default, twice, the second writes nothing); another `--tenant` exits 2 before
   any store is built; unset is the development tenant. The refusal's words are not pinned. A malformed `ASSETOPS_TENANT_SLUG`
   was a traceback: exit 2, `CONFIGURATION ASSETOPS_TENANT_SLUG` (failed first, `s4-first.log`). Two mutations (`s4-mut1/2.log`).
2. **C4 classes** (D-DD.177): actual `fuel_cost`, `cost_to_serve`, `contribution` "B"; `MTO-001` actual `diesel_price` "B". Plan
   classes untouched. `C4_KNOWN_FINDINGS` empty. `c4-first.log` (2 failed), `c4-green.log`.
3. **C-DD4's fuel clause** (D-DD.180): `judge_october_fuel`, `stored_diesel_prices` (the checker's own SQL: the current assignment
   covering the Site's whole local month, USD), live in `check_leaves_and_nodes`. 8 tests, failed first (`cdd4-first.log`); the SQL
   is tested on Postgres in `TestServedTenant`. On the real run's records (`/opt/assetecon/evidence/DD3d/dir` and `pure`) with the
   emulator's books and Mto's declared price: PASS, no detail (`real_run.py`). A pure caller that gives no records reads pending,
   as C-DD2 does; the live check never does. The dead `diesel` ESTIMATED skip is removed (no node of that name is judged there).
4. **L1** floor read over July to October at the three Sites, none in June. **L2** "FAIL <code>: a declared draw and no
   tolerance_pct". **L3** every record is read before the first is written; a malformed one or a naive instant is
   `FUEL_RECORDS_FILE <id> record`, another shape `FUEL_RECORDS_FILE - <what>`, an unreachable store `FUEL_RECORDS_STORE <id or ->`,
   all exit 2. **L4, L6** `packet-DD3d-a.md` (three files is right, the log's name is wrong). **L5** left: the baseline pins the text
   (`statement-handbuilt-baseline.json` `require_prepare_database`).
5. **ds4 t12 passes** as it is (`t12-1.log`, and again in `db-r4.log`): no cell outside the named ones is blank.
6. **Plants** `plants-r4.log`, `plant-*.log`, all failed and reverted. The card's plant (a): four `test_dd3d_fuel_cost.py` tests,
   12 of 4b money and 2 of 4b1, and t12 (4 lines: `fuel_cost class=B product=1040.00` at Kisiwa; Kobo's fuel cost 500.00 and the
   two figures over it). Mto is not among them: with no fuel row its figure stays blank in this plant, so the ruling's and the
   card's "Mto reads 0" is not what happens, and unit test (i) fails on the structure, not on a 0.
7. **Results.** One `--db-lane` call, nine files (`db-r4.log`, 119 s): 186 passed, 1 failed, `test_5c_deep_dive_postgres::test_9`
   (listed as main's; here it fails on its own canned words "Fuel cost" against the served "Fuel bought (invoices)": run 3's open
   (c), held). Pure (`pure-r4.log`, 77 s): 2,373 passed, 1 skipped, 2 failed, iap sites 6 and 8, held for DD3d.5. World checker
   files, wk excluded: 437 passed. Architecture, agent-workflow, statement catalogue and decision index exit 0. The other Postgres
   files of the reach set (3b, 4a, 4b, 4d, 5a, 5b, 6a, DDR ...) have not run on this branch: step 6's one reach-set run.
   Next: run 3's open questions (ruled by the Architect), then DD3d.5, whose commit adds `MTO-001`'s plan classes.

## Run 5 (23 Nov, stopped early by a usage limit; the branch is RED on purpose)
Round 29 and main (at d3f0fc978's line) are both merged (9c8eed22d, cecc81f71). Of the brief's six items:
1. **D-DD.181 done and committed (a94c91f10).** `view.untracked_line` (one function, month and range; a leaf outside the registry or
   a Site outside `codes` raises `UNTRACKED_OUTSIDE [...]`), `period.py` drawer, `rehearsal_check` G9, `walk_world.judge_month`; DDR
   expect has the literal twice and `fuel_bought` per Site. Failing first: `r5-untracked-first.log` (9 failed); then 404 passed and
   the iap fixtures `period-period-2026-09-10.json`, `period-period-g-2026-09-10.json` regenerated (`IAP_WRITE_FIXTURES=1`), 74
   passed. Statement catalogue exit 0 at that commit. NOT done: `judge_month` is also read by the walk tests (green); `test_7`'s exact
   text (item 4); plant (e); vitest over the two fixtures.
2. **D-DD.182 half done: tests and expected words are committed, the product code is NOT.** So these are red until the code lands:
   `test_5c_deep_dive_view.py` (world A, D, B, `test_cost_at_budget_*`, `test_no_served_word_*`, the fixture comparison),
   `test_5c_deep_dive_api.py` where it reads the fixture, `test_5c_screen_worlds_fresh.py`, `statement_cases` readers
   (`test_3a7_reconciliation_words.py`, `test_3a7_reconcile_command.py`, `test_sc1_statements.py`, `test_iap_portfolio_period.py`
   cases), DDR pure fixtures' words only. The failing-first run (`r5-words-first.log`) was killed part way, so no failing-id list
   exists: rerun it first. The finished code edit, not applied and never run, is `/opt/assetecon/evidence/DD3d/b/r5-words-code.py`
   (`python3` it once from anywhere; it asserts each old string occurs once): `deep_dive.cost_at_budget`, `assure_line` through the
   part, the four "reconciled" strings, `cost_ratio` = carried / cost. Command, before and after:
   `tools/heavy-slot.sh -- /opt/assetecon/evidence/DD3d/b/t.sh backend/tests/test_5c_deep_dive_view.py
   backend/tests/test_5c_deep_dive_api.py backend/tests/test_5c_screen_worlds_fresh.py backend/tests/test_3a7_reconcile_command.py
   backend/tests/test_3a7_reconciliation_words.py backend/tests/test_iap_portfolio_period.py
   backend/tests/test_iap_portfolio_sites.py backend/tests/test_sc1_statements.py backend/tests/test_ddr_rehearsal_check.py`.
   The case `deep_dive.cost_at_budget`/`none` expects evidence `[]`: a guess, check it. Then: regenerate `make_screen_worlds.py` and iap fixtures (list them),
   vitest on `src/estate` + the shell files; the Finding/3A7 Postgres words (`test_3a7_reconciliation_postgres.py`,
   `test_ddr_rehearsal_postgres.py`, `test_5c_deep_dive_postgres.py`); spec rows (5c tile1_cost, assure, standing_short; 3A7 2.7;
   DDR S5/S8); register row **R801** (D2); the ruling's sweep table row by row with each row's test, in the packet; the plant (old
   ratio, new words: World A reads 86.7%).
3. **D-DD.183 NOT started.** `NOT_MATCHED` / `RECONCILED` in `test_5c_deep_dive_view.py` still hold the old canned standing detail; the
   `.replace` calls and `A_FIXTURE_*` in `test_5c_deep_dive_postgres.py` are still there.
4. **NOT started:** G4 (D-DD.163, .177, .185, the cents helper `words.cents`, the sub-cent sign sweep), the DDR fixture
   (`LitreLeafSource._month`), `test_7`, S5/S8, the runbook, the remaining re-pins of the DDR screen literals. The seven DDR rehearsal
   tests have not been run on this branch.
5. **NOT started:** D-DD.184 confirmation; L5 (`prepare_clock` refusal text, stale pin out of
   `statement-handbuilt-baseline.json`).
6. **NOT started:** plants of this run; run 4's Q1 words (card plant (a) and packet: 4 tests of `test_dd3d_fuel_cost.py`, 12 of 4b
   money, 2 of 4b1 and t12 fail; "Mto reads 0" is not what happens, and whether the unit test shows it is unsaid); Q2 keep.
   The `--db-lane` run over the touched files plus every DDR and 5c Postgres file has not been made.
Other checks not run on this branch state: architecture, agent-workflow, decision-index, vitest. No plant was applied, no Postgres
run was made, no process is left running. **Run 6 (DD3d.5)** is unchanged: the budget, `M`'s October plan, board budget (D-DD.185), 3b1
t1 / 3b3 t6 in its first `M` commit, iap sites 6 and 8, `MTO-001`'s plan classes, the reach set, packet, state entry, in_review.
