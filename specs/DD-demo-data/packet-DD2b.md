# DD2b packet: cold and EV decided books (DD2.3, DD2.4; 3.25 u)

Branch `task/DD2b-cold-ev-books` (from DD2.2 `012b08c37`, `main` merged). Implementer (Claude), 2026-11-22. Status:
`in_review`. `USER_REVIEW_REQUIRED: false` (no screen; emulated source files only).

## Outcome
`tools/world_history.py exports` now writes cold and EV books for July to October in their own source-profile formats,
next to the unchanged mini-grid October files. Every DS1b record of a cold or EV tenant lands in exactly one place.

## Files
- `simulator/assetops_simulator/world/profile_csv.py`: loads `backend/conversions/profiles/<id>.profile.json` (read as
  data), compiles it with the contract and writes CSV rows through its columns. It is the inverse of `read_rows`.
  `render_layout` refuses profile layouts on purpose. `row_digest` gives the reader's `row_digest` version.
- `world/books.py`: shared Site-months, DS1b partition, `NODE_LINES` (D-DD.49), `STAGED_KINDS`, and `build_books`
  (mini-grid + cold + EV, one unwritten list, the cold/EV `NOT_ON_PATH_VERTICAL` rows dropped).
- `world/exports_cold.py`: ledger, invoices, receipts, budget, expenses. `NODES["COLD_CHAIN"]` (D-DD.50), `LEAF_TEXT`,
  `NAMED_BATCHES` (D-DD.51), `EMU_NODE`, `EMU_CAPACITY`, `EMU_LEDGER`.
- `world/exports_ev.py`: `roster_rows` (the one roster function, D-DD.52), `TICKETS` (D-DD.51), budget, expenses.
- `backend/conversions/profiles/`: 9 profiles, each with `.sample.csv` and `.expected.json`.
- `tools/world_history.py` (`_exports` calls `build_books`). `simulator/tests/world/test_3a3_exports.py`: the CLI file list
  gains the 9 cold/EV files. The mini-grid PINNED bytes are unchanged.
- Tests: `simulator/tests/world/{books_support,test_dd2b_cold,test_dd2b_ev,test_dd2b_books}.py`,
  `backend/tests/test_dd2b_profile_admission.py`, `backend/tests/test_dd2b_departures_postgres.py`.

## Acceptance, one by one
- Cold and EV budgets as `cold-budget-illustrative` / `ev-budget-illustrative`. Lines: DS1b own-leaf lines + node lines
  (cold `kwh`; EV `energy_cost`, `departures_required`). Parity: each node line is a key of `M structures` (c6, c11, v6).
- Expenses via `expenses-illustrative-1`, unchanged. No cold/EV expense row is ENERGY or PENALTY (c10, v8). No
  PENALTY(0) row exists anywhere.
- Cold revenue = crate_days × rate (invoices) and received = revenue − outstanding, all COLLECTED (c5). October: 868/820,
  1736/1650, 1984/1900. History check: Mwea July received 1312.00. `EMU_NODE` plant (c7).
- Ledger: the month's occupied crate-days equal the leaf in every month at every Site, counted independently from the
  rows (c2). 08:00 in, 16:00 out, ≤ 40 crates and ≤ 7 days for each generated batch. Peak ≤ capacity (Kiri 400, Thika
  380, Mwea 280). Named batches parity (c3, c4).
- EV roster Jul-Oct through `roster_rows`: 5166 rows (buses × nights). Σ required = month `kwh`, times per §4.5 (v2, v3).
  One writer: `"FLEET_ROSTER"` appears only in `exports_ev.py`, and the function widens to November nights (v4).
- ev-departures with bool `block_met` admitted end to end. Memory admission names the analyst (a2). A text "false" in
  expected is refused `ADMIT_EXPECTED` (a3). **PostgreSQL**: admit, upload, accept; the stored `canonical` holds JSON
  booleans `[True, False, True]` (d1).
- Plan fields with no line stay in `unwritten.json` with DS1b's reason (cold `revenue/energy/contribution/occupancy_pct`
  `NOT_READ_BY_A_LEAF`; EV `kwh/offpeak_kwh` `NOT_OWN_LINE`, Ruiru `total` `NOT_READ_BY_A_LEAF`) (c11, v6). Missing leaf
  → `NOT_IN_HISTORY`, no row, never zero (c9, v7).
- D-DD.54: every DS1b record of the three tenants is in exactly one of files / staged / unwritten. Staged =
  `{gen:COLD-THIKA:2026-10:actual:liability}`. Mini-grid is checked on its accounting period only (b1).
- Every profile passes 3A6 admission steps 1-6 on its sample through the real `SourceProfiles` (a1 ×9). Samples are
  slices of the emulated file and cannot drift (b3), or hand-written records for rows that come later (b4).

## Checks (revision `65f4fb270`; evidence `/opt/assetecon/evidence/DD2b/run-2026-11-22/`)
- New tests shown failing first: the three simulator files fail collection without the modules (3 errors). Admission
  first failed `ADMIT_MAP_UNCOVERED` on 3 profiles (ledger, receipts, tickets); the samples were fixed (commit
  `65f4fb270`).
- `simulator/tests/world/` (PYTHONPATH on the worktree): **180 passed** in 14.1 s (32 new).
- `tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- backend/tests/test_dd2b_profile_admission.py
  backend/tests/test_dd2b_departures_postgres.py`: **13 passed**, 0 skipped, wall 9.8 s.
- Plants, each run then reverted with `git checkout`, each failed its test: P3 PENALTY row (c10), P4 staged list dropped
  (b1), P5 a second `"FLEET_ROSTER"` (v4), P6 commodity order (b3 ledger sample), P7 node text (c6), P8 remainder crate
  dropped (c2, c5), P9 roster total +0.001 (v2). Also c7 (`EMU_NODE`) and c8 (`EMU_CAPACITY`) are plant tests.
- `check-architecture.ps1` passed. `check-agent-workflow.ps1` passed. `check-decision-index.py` OK. The real manifest:
  `world_history.py exports` exit 0, 13 files + `unwritten.json`.
- Layout evidence: not run (no UI).

## Known deviations (defaults taken; spec untouched)
1. **Receipts and tickets profiles use `version: row_digest`, not constant "1".** `compile_profile` refuses a constant
   version with a `status` column (`profiles_v1.py`, version rule). Other profiles use constant "1".
2. **The EV invoice "Line" column is split into `Line` (band) and `Line type` (`Usage`/`Demand`).** A profile map must be
   one-to-one (`len(set(values)) == len(map)`), so §5.6's `{PEAK, OFFPEAK, NIGHT → USAGE}` does not compile.
3. **Ledger rule** (§5.2 assumes crate-days divisible by 7; Thika's 8432 is not). A crate-day is a crate on a date from its
   admission up to the day before it leaves, so a late batch carries crate-days into the next month. Standard 40-crate
   batches go on the least crowded day while they fit. The remainder batch holds `r//7` crates for 7 days plus one crate
   leaving after `r%7` days. Opening stock: June batches still in on 1 Jul. OUT rows after `as_of` are not written
   (those crates are still in the room).
4. Named batch times: only B-1029's check-out is in `M`. B-1029 is in on 28 Sep 08:00; B-1031 and B-1034 are in 1 Oct
   08:00 and out 8 Oct 16:00 (Assumed). Their customer is the code `COLD-THIKA-K-01` (R5: no names).
5. `NODE_LINES` applies wherever the plan holds the field, so October Embakasi and Kasarani also get `energy_cost` and
   `departures_required` lines. §5.3's "at Ruiru" describes history.
6. Roster service day = the night's start date. Embakasi returns are rounded to the whole minute (half-even).
7. Receipts are paid at month end, 10:00. Methods rotate M-Pesa, M-Pesa, Bank. Tariff code `T-STORAGE`. Sample-only extra
   rows: a cash receipt, an in-transit receipt, and ACKNOWLEDGED/CLOSED tickets (admission step 4b needs every map value).
8. The cold electricity-bill profile is not built: DD2.4 lists only the EV invoice and departure profiles; the bill is
   DD4.4's.

## Architect questions (default in force)
- **Q1 (High for DD5): source-system switch.** Cold invoices and receipts are both `customer_invoicing` with distinct
  systems (`PROFILE_SOURCE_SYSTEM_TAKEN` forbids a shared one). `_refuse_switch` allows one system per source type per
  Site, so the second upload, and DS1b's staged Thika ADJUSTMENT (`customer_invoicing`, generator system), will be
  refused `UPLOAD_SOURCE_SWITCHED` at load. Default: built to spec; DD5 resolves it (one invoicing file, receipts as
  `billing_export`, or a contract rule).
- Q2: DS1b writes no TARIFF_SCHEDULE or METER_ASSIGNMENT today (D-DD.24 says "as today"). Default: DD2a's staging owns
  it; the `T-STORAGE` code must match its `contract_ref`.
- Q3: `NODES["COLD_CHAIN"]` lives in `exports_cold.py`, and DD2a builds `NODES["MINI_GRID"]` in `exports.py`. Default:
  unify at merge. `world_history.py` / `test_3a3_exports.py` overlap with DD2a (small conflicts expected).
- Q4: deviations 1-3 above need ratification.

## Residual risk / review focus
- Kiri's room reaches exactly 400 crates (capacity). DD4.1's thermal pack runs at a full room on peak days.
- Review: the ledger algorithm (`_fill`, `crate_days_in`), `profile_csv` as the inverse of `read_rows` (b3 + round trips),
  D-DD.54 accounting in `build_books`, and the switch conflict (Q1).

## Fix round (round 7; D-DD.58 to D-DD.66; head after the merge of `main` at 80661e824)

Spec: the "DD2b fix round" items of `rulings.md` round 7. Nothing is designed beyond them.

**Merge of `main`.** Four conflicts, all text: `.ai/state/data.md` and `index-3.md` (both entries kept, DD2a's first,
DD2b stays 200: `main` took 199), `specs/DD-demo-data/spec.md` (status line names both), and
`simulator/tests/world/test_3a3_exports.py` (DD2a's `PINNED_ALL_MONTHS` and `--extras` assertions kept, DD2b's cold and
EV file list added). Git merged `exports.py` and `world_history.py` cleanly, but their combination was wrong: `build_books`
dropped `mini.staged` and `mini.statements`, and `_exports` iterated `result.staged` as pairs while DD2b's was a list of
IDs. `BooksResult` now carries `staged` and `statements` as (name, bytes) pairs, and mini-grid's come through for
mini-grid tenants only. DD2a's behaviour is intact: Lakeside's four files are byte-identical to `main` (hashes compared
from a scratch worktree of `main`; the 3A3 pins and `test_b2` hold them), and its statements file is still written.

**Changes.**
- D-DD.62: `world/nodes.py` holds `NODES` (`MINI_GRID`, `COLD_CHAIN`), `evaluate` and `emu_node`; `exports.py` and
  `exports_cold.py` import them, their tables are deleted. One parity test over both keys (`test_dd2b_nodes.py`); the
  mini-grid leaf-alternative test stays in `test_dd2_nodes.py`. The checker keeps its own evaluator.
- D-DD.59: `cold-storage-invoicing-illustrative` (Type, 22 columns, `row_digest`, no constants) replaces the invoices and
  receipts profiles, with its sample and expected file. Thika's ADJUSTMENT is a `Credit note` row (-108.00, subject SITE).
  `compile_profile` and admission accept `kind` from a mapped column and the empty coded cells (no stop-and-ask).
  Nine profiles became eight.
- D-DD.60: `check_source_systems` in `build_books` stops `EMU_SOURCE_SWITCH <tenant> <source_type> <site>` (two files of
  one source type, or a staged batch against another source system at a shared Site). Staged JSON goes to
  `<slug>/staged/` in `tools/world.py` `inputs()`. A cold ADJUSTMENT is staged only where no invoicing file exists.
- D-DD.61: `world/tariffs.py`, `tariff_schedules(view) -> {tenant: batch}`, staged as `harvest-cold.storage_rate_card.json`
  and `metro-bus.utility_invoice.json`. Parity test: every cold invoice and every EV invoice sample `Tariff` is a schedule
  in force on its `effective_from`, every rate is `M`'s price. The OFFPEAK-AM/PM split is the ruling's WORKAROUND.
- D-DD.63: the ledger already wrote June opening stock (L2); the module text now says so and `test_r14` asserts it
  (June rows are IN only, each batch still in on 1 July, every OUT has its IN, no June invoice).
- D-DD.65a: L4 `zone_currency(view)[0]` in `test_dd2b_ev.py`; sha256 pins of the eight cold and EV files
  (`PINNED_COLD_EV`, also checked on the CLI run). EV files and the cold ledger, budget and expenses are byte-identical
  to the DD2b head (compared from a scratch worktree); only the cold invoicing file is new.

**Counts.** `simulator/tests`: 645 passed at this head (world: 208 + 15 new in `test_dd2b_round7.py` and 4 in
`test_dd2b_nodes.py`, less the deleted node tests). Backend, one `run-host-tests.ps1` call on the nine files importing a
touched module: 167 passed, 9 failed, all in `test_ddr_rehearsal_postgres.py` (`EXPORT_FILE_UNKNOWN
harvest-cold.expenses.csv`: the loader reads Lakeside's files only). The same 9 fail at 3b353031c (run from a scratch
worktree: 9 failed, 3 passed), so they are DD5's. Architecture and workflow guards pass.

**Plants (each shown failing, then reverted).** Guard `check_source_systems` removed: `test_r5` (non-zero Lakeside
liability) fails. `TARIFF_CODE` set to `T-STORE`: `test_r12` (parity) and `test_r15` (pin) fail. The first run of the
moved tables failed on the missing `exports.NODES` import before `nodes.py` existed.

**Left for DD5.** `L1.staged:<slug>` loads the staged directory; the meter register (`lakeside-power.meter_register.json`)
is DD5.2's. DD5's first C-DD2 run is `BOOK_QUERY`'s first proof (DD2a L1).
