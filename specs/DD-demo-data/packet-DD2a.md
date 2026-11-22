# DD2a packet: books for four months (DD2.1, DD2.2 review Lows, DD2.5)

Branch `task/DD2-books`, rulings D-DD.48 to D-DD.57 (round 6). DD2a is 3.0 u: DD2.2 (done, review ACCEPT), DD2.1, DD2.5.
DD2.3 and DD2.4 are DD2b (`task/DD2b-cold-ev-books`) and are not built here. Review needed: yes for the protected seam
(`contracts/`, two Low fixes); the rest is simulator and `tools/`. USER_REVIEW_REQUIRED: no.

## DD2.2 review Lows (`contracts/`)
- L1: a `bool` on a `CODED_PATHS` path or on `source_record_id` is refused at `{path}.type` (`profiles_v1.py` compile) and
  by `check_layout` (`NATIVE_LAYOUT <id> <path>`). Tests `test_review_l1_*` in `contracts/tests/test_dd2_bool_type.py`
  (3 of 4 cases failed before the change; the layout-check case failed on the coded path). Contract suite 206 passed.
- L2: `specs/3A6-source-profiles/spec.md` path-object row lists `bool` and its rule.

## DD2.1 mini-grid months (`simulator/assetops_simulator/world/exports.py`)
- `NODES["MINI_GRID"]`: six expressions as manifest text plus callables, in dependency order; `ZERO_LEAVES`;
  `evaluate_mini_grid`. Labelled "node of `structures.MINI_GRID`, evaluated on the month's leaves (D-DD.48)". Exact
  `Decimal`; history money is cents (divided in `_leaves`), October dollars. Leaves read through `PASS_THROUGH`.
- `build_exports(view, history, *, months=None)`: default is every history month plus the accounting period; rows
  ordered by (month, Site, row); unknown month stops `EMU_MONTH`. `_charges`, `_receipt_records`, `_fuel_records` and
  the plan lines read the evaluated nodes. `EMU_REVENUE`, `EMU_COLLECTIONS`, `EMU_FUEL` stay behind them.
- `EMU_NODE <tenant>/<code> <month> <node>` (plan nodes are `plan.<node>`): for October the evaluated node must equal the
  period's. Prices are checked first (`EMU_PRICE`). An absent required leaf writes no row for the node and its
  dependants, listed `NOT_IN_HISTORY`.
- D-DD.53 fuel notes: `DATED_NOTES` (OOO-1) cut first at their date, then 400 L on the 1st/8th/15th/22nd/29th at 10:00,
  cycling; the last note says its remainder in its document reference. Kobo October: 400 L 26 Oct, 400 L 1 Oct, 380 L 8 Oct.
- D-DD.54 staging: DS1b's METER_ASSIGNMENT, TARIFF_SCHEDULE and ADJUSTMENT records are staged as
  `<tenant>.<source_type>.json` (`ExportsResult.staged`). For a cold or EV tenant every other record is listed
  `NOT_ON_PATH_VERTICAL` per record (until DD2b). Test: every DS1b record of all three tenants is in exactly one of a CSV, a
  staged file or `unwritten.json`.
- Tooling: `world_history.py exports --extras DIR` writes the staged JSON and `<tenant>.statements.json` (not into the
  CSV directory: the loader reads a directory whole). `tools/world.py inputs()` passes `--extras` and places staged JSON
  for the tenants the definition names; the statements file is not staged (reader is DD5/WK).
- Tests: `simulator/tests/world/test_dd2_nodes.py` (22; parity with the manifest, October recorded nodes both sides at
  three Sites, planted `EMU_NODE` on actual and plan, July Kobo 8163 / 3265.20 / 3002.73, ordering, cents vs dollars,
  October bytes unchanged, notes, the exactly-one-place invariant, absent leaf, negative collected). `test_3a3_exports.py`
  updated: the E-tests build October only; E8 plants now stop at `EMU_NODE` first.

## DD2.5 statements and checks
- `world/statements.py`: `assetops.world-statements/1`, one statement per history month, each figure the sum of that
  month's rows, `source_ref` "Emulated management accounts, July 2026, final". Lakeside's July to September only
  (October stays in the walk). The cold/EV cost key `energy_cost` is tested on fixture rows.
- `tools/dd_check.py`: its own evaluator (`Formulas`: names, numbers, `+ - *`, parentheses, `a | b`, `[site]`), no import
  from the simulator. C-DD2 (decided kinds per Site-month, source word Emulated), C-DD3 (revenue = billed x tariff;
  collected + in transit + outstanding = revenue; cold storage invoices = crate-days x rate; EV lines = energy cost),
  C-DD4 (decided leaves to the cent; node figures of history months equal the checker's evaluation; October's equal the
  period). SQL read `stored_books` (latest revisions joined to `site`); judges are pure on rows. Live; they fail on a
  store without the books.
- Tests: `backend/tests/test_dd2_check.py` (evaluator by hand, seam), `simulator/tests/world/test_dd2_checker_on_emulated_rows.py`
  (judges on the emulator's Lakeside rows; plants flip each check), `test_dd1_check.py` (stub list).

## Pin moves (listed for review)
- `SOURCE_VERSION` "2" on charges, fuel, budget and DS1b-independent rows. Billing, expenses and budget hashes move;
  collections' October hash does not (receipts keep "1"). October-only pins in `test_3a3_exports.py`:
  billing `20955b91...`, collections `8b3cd80a...` (unchanged), expenses `74c5ad18...`, budget `1c10cdb5...`.
  Billing and budget October bytes equal the old pins when `SOURCE_VERSION` is "1" (test): the node derivation changed nothing.
- Default all-month pins (`PINNED_ALL_MONTHS`): billing `e5b74fbb...`, collections `8bb39b30...`, expenses `00e3449a...`, budget `e12bcd1f...`.
- Expenses October moved for notes (D-DD.53: days and 10:00, Kobo's dated note).

## Deviations and questions
1. Receipts keep `source_version` "1": `collections-illustrative-1` holds it as a layout constant, and the ruling forbids a contract change.
2. METER_ASSIGNMENT and TARIFF_SCHEDULE: DS1b `records.py` writes neither today. Only ADJUSTMENT exists (cold liability, `harvest-cold.customer_invoicing.json`). The staging code takes all three kinds.
3. Staged JSON shares a source type with a CSV or profile file for the same tenant would load as `EXPORT_PATHS_MIXED` (billing_export, customer_invoicing). Not met today (cold has no CSV yet); DD2b/DD5 must keep it in mind.
4. DD2.5's "cold and EV writer wired to `measured.json`": no `measured.json` exists before DD4.4. The writer is `figures_from_rows`/`statements_document`, tested on fixture rows; the wiring and cold/EV statements are DD2b/DD4.4.
5. C-DD2's kind table is the kinds every Site-month holds (decided kinds only; tickets and measured kinds excluded). C-DD2 EV `FLEET_ROSTER` month comes from recognition_period, else effective_from or occurred_at.
6. `EMU_PLAN_PRICE` is now unreachable by a planted manifest (the plan price is node over quantity by construction); the check stays.

## Plants run
- Node text edit (exporter `billed_kwh` expression): 2 parity tests fail. Node callable edit: 5 failed + 10 errors (EMU_NODE at Mto October).
- History-only leaf drop in the exporter (`adjustments_kwh` ignored for history): C-DD4 fails on `KOBO-001 2026-07: billed_kwh stored 8205 != evaluated 8163`; C-DD3 passes (consistent), proving C-DD4's clause is the independent one.
- Checker evaluator sign flip: 5 tests fail. All reverted.

## Checks
- `simulator/tests/world`: 170 passed. `contracts/tests`: 206 passed. `backend/tests/test_3a3_load_emulated.py`, `test_ds4_world.py`, `test_dd1_check.py`, `test_dd2_check.py`: 117 passed.
- Postgres, one `tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1` run (ds4 world, DDR rehearsal, WK walk): 118 passed, 202 s. A first run failed (9 failed, 3 errors) when staged JSON sat in the exports directory; fixed by `--extras`. Baseline before DD2.1: passed.
- `tools/check-architecture.ps1` (ASSETOPS_GUARD_PYTHON set), `tools/check-agent-workflow.ps1`, `tools/check-decision-index.py`: pass.
