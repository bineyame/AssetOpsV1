# 3B1 review, round 1 (discovery, W5)

Reviewer: fresh Claude reviewer (not the author), 2026-11-20. Branch `task/3B1-structure-registry`, commits
`b7d261bf9` (code and tests) and `841ea2d61` (bookkeeping), base `main` `8c9af447b`. Read in a scratch worktree
at `841ea2d61`, which was removed afterwards. The author's worktree was not touched.

## Summary (round 1)

- **Verdict: ACCEPT with Lows.** No High, no Medium. Both Lows are optional hardening; neither is an acceptance gap.
- All five done questions in spec §7 are answered yes, and I reproduced the evidence myself.
- Fidelity: my own script reads the rows file and the catalogue as text (it never imports them). It found the 47 rows
  (31 leaves, 16 nodes) equal to the manifest's `structures`, `factor_map`, `leaf_sources` (family, kind, words,
  absent) and `home_categories`, and equal to the catalogue's units. My unit algebra composes every node unit. The
  script also caught each of four planted errors.
- Start-up check: each of the 12 codes refuses a planted fault, naming the row. The order is code by code, then
  row by row. Money is allowed only under Grow, Optimize or ABOVE. The catalogue check runs both ways. A broken
  rows file stops `import assetops_backend.main` with a `ConfigurationError`.
- T1 is independent: a wrong home planted in the rows file passes `check_all()` but fails T1, and so does a wrong
  `HOMES` map.
- The `Expr` contract is complete enough for 3B3. It also parses, and its units compose, for all 48 node
  expressions of the three manifest structures, so 3B6 needs no language change.
- The author's four unstated choices need no reopening. Two of them are worth a one-line ratification by the
  Architect (see Q6).
- Merge tier: the focused tests, `test_health.py` and a smoke run over the `create_app` tests are enough
  technically (see Q8).

## Findings

| # | Sev | Where | What | Why it matters | Fix | Kind |
|---|---|---|---|---|---|---|
| L1 | Low | `backend/assetops_backend/structure/check.py:137-138` | `STRUCTURE_TOLERANCE` tests only `pct > 0`. A float `pct` passes start-up. `Decimal("Infinity")` passes. `Decimal("NaN")` raises `decimal.InvalidOperation` instead of a `StructureError`, so `create_app` still stops, but without the named `ConfigurationError`. | The records do no validation (R14), so `check` is the only gate. 3B4 and 3B6 will add tolerances, and the slice's rule is "no float anywhere". | Refuse when `not isinstance(pct, Decimal) or not pct.is_finite() or not pct > 0`, and add one T3 plant per case. | Preference. The spec's three conditions are met. |
| L2 | Low | `backend/assetops_backend/structure/check.py:207-210` | `check_all` never compares a `REGISTRIES` key with that registry's own `structure_key`. An entry `"COLD_CHAIN": Registry("EV_DEPOT_CAPTIVE", ...)` would pass start-up. | 3B6 adds two entries, and 3B3 and 3B7a will look structures up by key. A mis-keyed entry would quietly serve the wrong structure. | Refuse a mismatch, for example as `STRUCTURE_CATALOGUE <key>/-`, or build `REGISTRIES` from the registries' own keys. Can be deferred to 3B6. | Preference, forward-looking. Not in spec §4. |

Nothing else found. I made no finding about scope, about floats, or about inheritance.

## Reviewer-guide checklist

- **Scope (first check 1).** The diff holds `structure/{__init__,registry,rows_mini_grid,expressions,check}.py`, the
  test file, two lines in `main.py`, the packet, the spec status line, `specs/INDEX.md` and `.ai/state/data.md` plus
  `index-2.md`. There is no migration. `__init__.py` is the only file the spec does not list, and the package needs
  it.
- **`main.py`.** It gains exactly two lines (`+2/-0`), at lines 342-343, immediately after
  `install_handle_error_hook()` (line 341) and before the first `include_router`. The import is function-local, and
  no name `registry` is imported into `main`. `git merge-tree` shows a clean merge against `main` and against
  `task/3C1a-person-on-work`, which does not touch `main.py` yet.
- **Independence (first check 2).** T1's expectations come from the YAML and from `OWN_HOME_MAP`
  (`test_3b1_structure_registry.py:52-59`), which is asserted against `CATEGORIES` (line 84). T2's unit table is
  written in the test (lines 158-175). `ROWS` writes leaf units, sources, words and absence values as literals.
- **Module path (first check 3).** The packet records the author's worktree. I verified my own:
  `/opt/assetecon/scratch-rev3b1-r1-wt/backend/assetops_backend/__init__.py`, `.../contracts/assetops_contracts/__init__.py`
  and `.../backend/assetops_backend/structure/check.py`.
- **Tests first.** I cannot verify this from git, because code and tests are in one commit. Only the packet states
  that the first run failed at collection.
- **P1.** All four planted faults are refused, naming the row:
  - `collected` homed under protect P1 gives `STRUCTURE_MONEY_HOME`;
  - `unmapped_kwh` with no home gives `STRUCTURE_CATEGORY`;
  - `fuel_cost = diesel_l + diesel_price` gives `STRUCTURE_UNIT`;
  - `diesel_l` reading `fuel_cost` gives `STRUCTURE_CYCLE MINI_GRID/diesel_l`.
- **P2.** `max(lost_unit_kw, 1)` composes to `KWH/HOUR` (kW), `1 - shortfall_backed` to `1`, and `x - (1 + 1)` to
  `KWH`. I also tried `x * (1 + 1)`, which gives `KWH`, and `(1 + 1) / x`, which gives `1/DAY`.
- **P2b.** These placements are refused:
  - a money row homed `CALENDAR` is refused by CATEGORY, which runs first;
  - a money row homed `PROTECT_ASSET` or `ASSURE_PERFORMANCE` is refused by MONEY_HOME;
  - `ABOVE` on a leaf is refused by CATEGORY;
  - deleting an unreferenced catalogue leaf (`liability`) is refused as CATALOGUE, naming the leaf.

  Deleting a leaf that a node references (`dawn_days_below`) is refused earlier, as
  `STRUCTURE_UNKNOWN_FACTOR MINI_GRID/replayed_dawn_days_below_safeguard`. That is correct under the spec's order of
  codes, but the guide's phrase "refused by name" holds only for an unreferenced leaf.

  Two placements pass, as they should. The non-money `tariff` (`MONEY/KWH`) passes under Protect, because `is_money`
  is exactly `MONEY^1`. Money under Grow G2 also passes.
- **P3.** `registry.py` and `check.py` contain no parent or inherit lookup; the only hits are docstrings. Every
  check reads `row.home` only.
- **P4.** `grep -rn float backend/assetops_backend/structure/` finds nothing. A literal is
  `Decimal(<source segment>)`, gated by `[0-9]+(\.[0-9]+)?`.
- **P5.** See the timing under Q7.
- **Generic over `REGISTRIES`.** `check.py` contains no `MINI_GRID` literal. The CALENDAR, ABOVE and whole-catalogue
  rules also hold for COLD_CHAIN (`minutes_per_day`, `period_days`) and EV (`nights_in_period`): no node ID in any
  structure collides with a catalogue leaf ID.

## Q2 Fidelity (hand and script)

I checked by hand the 16 node texts, the 31 leaf rows and the homes against the manifest, at lines 812-866,
868-901, 1372-1420 and 1639-1670.

My script is `scratchpad/rev3b1/fidelity.py` (session scratch; not kept). It reads `rows_mini_grid.py` and the
catalogue `_TABLE` in `factors.py` with `ast`, and never imports the code under review. It checks:
- node IDs, their order and their expression texts against `structures.MINI_GRID`;
- the leaf set against `factor_map.MINI_GRID` and `leaf_sources.MINI_GRID`;
- family, kind, words (`om`, `staff`) and absence on every leaf;
- every row's home against `home_categories`, through its own map;
- that the only unrowed homes are `cover_not_claimable` and `unclaimable_cover`;
- leaf units and leaf order against the catalogue;
- node units, through its own unit algebra under the literal rule;
- that money rows are homed only under grow, optimize or above;
- the tolerance on `unexplained_l` (2.0 % of `diesel_l`), which equals the Site values `[2.0, 2.0, None]`;
- the evaluator's function set in `evaluate_structure.py` (`min`, `max`, `ceil`, `floor`) and its operators
  (`+ - * /`; `|` appears only in `factor_map`), which equal the language.

Result: `ERRORS: none`. To prove the script is not vacuous, I planted four errors in a copy of the rows file:
- words `Payroll`;
- `reduced_days` homed P1;
- `hours_per_day` with unit `HOUR`, which the script reports and which also breaks the composed unit of
  `obligation_hours_without_redundancy`;
- `dawn_days_below` with absence `MISSING`.

The script caught all four.

## Q3 Start-up check

- **One plant per code.** Each fails with its own text:

  | Code | Plant | Refusal |
  |---|---|---|
  | DUPLICATE | a second `om` row | `MINI_GRID/om` |
  | EXPRESSION | `+diesel_l*…`, `diesel_l * 1.` | `MINI_GRID/fuel_cost` |
  | UNKNOWN_FACTOR | a name with no row | `MINI_GRID/collected` |
  | CYCLE | a self cycle | `MINI_GRID/contribution` |
  | LEAF_SOURCE | family `SPREADSHEET` | `MINI_GRID/tariff` |
  | LEAF_ABSENT | absence `ZERO` | `MINI_GRID/tariff` |
  | TOLERANCE | `pct` 0.0 | `MINI_GRID/unexplained_l` |
  | OBJECTIVE | Grow with `O1` | `MINI_GRID/revenue` |
  | CATALOGUE, CATEGORY, MONEY_HOME, UNIT | as listed under P1 and P2b above | as listed there |

  The author's T3 covers every code. I did not rerun the packet's per-code tests with each check disabled, because
  my own plants cover the same claim.
- **Code-major order.** I put an OBJECTIVE fault on row 1 and a CATEGORY fault on row 47. The check reports
  `STRUCTURE_CATEGORY .../asset_days_available`, so code order wins. Within one code, two OBJECTIVE faults report
  the earlier row (`delivered_kwh`). `CODES` follows spec §4's order.
- **Catalogue both ways.** Both directions are pinned in `test_t3_catalogue_both_directions`:
  - leaf to catalogue: a renamed leaf, a wrong unit, or a cold-chain leaf;
  - catalogue to row: a deleted leaf;
  - a node with a catalogue leaf ID;
  - an unknown key, refused as `SOLAR_FARM/-`.
- **A broken registry stops start-up for real.** I edited the real `rows_mini_grid.py` in the scratch worktree, then
  ran `python -c "import assetops_backend.main"`. Importing `main` calls `create_app()` at module level, line 834.
  It raised `assetops_backend.config.ConfigurationError: STRUCTURE_MONEY_HOME MINI_GRID/collected`. T4 proves the
  same through the monkeypatched `REGISTRIES`, with `__cause__` a `StructureError`.

## Q4 T1 independence

- **Plant A.** `technical_loss_kwh` homed `optimize O3` in the rows file. `check_all()` still passes, since the plant
  is legal for the check, but `test_t1_every_row_home_equals_home_categories` fails (`AssertionError:
  technical_loss_kwh`): 1 failed, 7 passed.
- **Plant B.** `HOMES["grow"]` changed to `_OPTIMIZE` in `registry.py`. T1 fails again. T1 does not share the
  product's home map.

## Q5 Expr contract (D-3B1.8)

Complete and unambiguous for 3B3:
- There are five frozen types (`Num(Decimal)`, `Ref`, `Bin(op)`, `Neg`, `Call(func, args: tuple)`). `op` is drawn
  from the exported `OPERATORS` and `func` from the exported `FUNCTIONS`, with fixed arities enforced in `parse`.
- Precedence and associativity are Python's, through `ast`, so `a - b - c` parses as left-nested `Bin` nodes. A
  literal is never negative: `-1` is `Neg(Num(1))`.
- `names()` gives the first-seen distinct children.
- Forward check: the 16 MINI_GRID, 13 COLD_CHAIN and 19 EV_DEPOT_CAPTIVE manifest expressions all parse, and their
  units compose from catalogue leaf units. Two examples: EV `cost_per_departure_met` gives `MONEY/DAY`, and
  `contribution = 0 - cost_to_serve` gives `MONEY`.

What 3B3's spec must fix, because the contract rightly leaves it open:
- the Decimal context and precision;
- division by zero, which `max(lost_unit_kw, 1)` already guards in the mini-grid;
- the direction of `floor` and `ceil` on negatives (the pack uses `math.floor` and `math.ceil` on Decimal);
- the identity values of OPTION_ONLY leaves.

None of these is a 3B1 gap.

## Q6 The author's four unstated choices

1. **Fuel tolerance pinned only for Sites that declare one** (`test_3b1_structure_registry.py:126-132`). Spec §6
   says "every mini-grid Site", but MTO-001 declares no `fuel_balance`. Pinning the Sites that declare one (two of
   them, with `>= 2` asserted) is the only reading that keeps the test meaningful. It is a factual slip in the spec,
   not a design choice. Architect: fix the spec's wording; no ruling is needed.
2. **The order inside `STRUCTURE_CATALOGUE`.**
   - Putting the unknown key first is forced, because `leaves_of` raises `KeyError` on an unknown key.
   - Checking rows in `ROWS` order and then the missing catalogue leaves in catalogue order is the natural reading
     of R9 and R10.
   - "A node whose ID is a catalogue leaf ID" is read against the whole catalogue, not just this key's leaves. That
     is a real semantic choice the spec left open: the stricter reading, consistent with "one quantity, one ID". It
     causes no collision in any of the three structures.

   Architect: ratify in one line, after the fact. Strictly, it would have been a mid-build question. It is not
   worth a reopen.
3. **Wrapping parse errors, and refusing unary `+`.** `parse` turns a `SyntaxError` into an `ExpressionError`,
   which matches "`parse` raises `ExpressionError`"; `check` still maps all three (R8). Unary `+` has no node among
   the five frozen types, so refusing it is the closed-grammar reading. No ruling needed.
4. **Import order.** The spec places the records and `REGISTRIES` in `registry.py` and `ROWS` in
   `rows_mini_grid.py`, which forces a circular import. The author resolves it with a bottom import in `registry.py`
   (`registry.py:99`) and with `__init__` importing `registry` first. I confirmed that importing any of the four
   modules first works and that `check_all()` passes after each. No ruling needed.

## Q7 What I reran

All runs used `PYTHONPATH` pointed at the scratch worktree's `backend`, `backend/tests`, `contracts`, `simulator`,
`gateway`, `field`, `host` and `tools`, with `DATABASE_URL` and `ASSETOPS_TEST_DATABASE_URL` unset. Pytest ran
through `tools/heavy-slot.sh`.

- `pytest backend/tests/test_3b1_structure_registry.py backend/tests/test_health.py -q`: **83 passed, 1 warning**
  (the Starlette httpx deprecation) in 4.07 s. This matches the packet's 83.
- `pwsh tools/check-architecture.ps1`: **passed**. The first try could not run the chain-structure guard because
  the scratch worktree has no `.venv`; it passed with `ASSETOPS_GUARD_PYTHON` set to the shared `.venv`.
- `pwsh tools/check-agent-workflow.ps1`: **passed**.
- **Timing (bound 10 ms):**

  | Measure | Result |
  |---|---|
  | First `check_all()` | 0.461 ms |
  | Median of 1,000 calls | 0.468 ms (max 1.562 ms) |
  | `check_at_start()` after `main` is imported | 0.444 ms median |
  | Structure package's share of `import assetops_backend.main` (`-X importtime`) | about 22 ms, once per process |
  | `create_app()` median | 170 ms, so the per-call cost of the check is under 0.3 % |

  The packet's numbers are 0.770, 0.454 and 45 ms; they agree.
- **Smoke run** of six no-database test files that call `create_app`: `test_out_b4_main_binding`,
  `test_simulator_lab_gate`, `test_ch5b_graph`, `test_sites_api`, `test_3c0a_accounts_api` and
  `test_fetch_seam_contract`. Result: **138 passed**.
- Plus the plants and the fidelity script described above.

## Q8 Merge test tier

`select-tests` chose the full suite only because `main.py` changed. The change is two lines: a pure check that reads
no environment, database or global state other than `REGISTRIES`, and passes on the real registry. No test
monkeypatches `CATEGORIES`, `LEAF_FACTORS` or `STRUCTURE_KEYS` before calling `create_app` (I grepped for it). No
test checks the text of `create_app` in a way the two lines would break; `test_demo_a0_assumption_clock_seam` scans
`main.py` for one keyword only.

My judgment: the focused tests, `test_health.py` and the 138-test smoke run are technically enough for this merge.
The full suite can run at the next milestone, under the owner's test-suite policy. If the coordinator still wants
the full tier, it is the tooling rule asking for it, not a risk I can name.

## Not verified

- That the tests were written before the code: there is one commit for both.
- The full backend suite: not run, by the brief.
- Layout evidence: not applicable, since this is a non-screen slice.

## Residual risks the packet does not name

- **Deep nesting.** Pathologically deep expressions (about 5,000 nested unary minus signs, or a 20,000-term sum)
  raise `RecursionError` out of `parse`, so the process still stops, but not with the named `ConfigurationError`.
  Rows are reviewed code, so this is negligible.
- **Repeated parsing.** `FactorRow.children` re-parses the expression on every access (`registry.py:80-82`). 3B2 and
  3B3 should parse once (`check` already does, in `_Context.parsed`) rather than call `.children` in loops.
- **Error text for a deleted leaf.** A deleted leaf that a node references is reported against that node as
  UNKNOWN_FACTOR, not against the leaf as CATALOGUE. That is correct under the spec's order of codes, but the error
  text then names the node, not the missing leaf.
- **Where this review is written.** The standing reviewer brief says `specs/<ID>/review.md` and "never `.agent/`".
  This file follows the dispatch's explicit path, so the coordinator may want to copy it to
  `specs/3B1-structure-registry/review.md`.
