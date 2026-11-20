# 3B1 packet: the structure registry, mini-grid

Implementer (Claude), 2026-11-20. Branch `task/3B1-structure-registry`, base `main` `8c9af447b`, worktree
`/opt/assetecon/AssetOpsV1-3b1` (the spec's §0 path). Spec rev 2, rulings D-3B1.1-9 and round-1 answers. Not merged.
`USER_REVIEW_REQUIRED`: false (non-screen; P3B already owner-approved). Review depth: discovery (W5).

## Commits

- `b7d261bf9` code and tests: `backend/assetops_backend/structure/{__init__,expressions,registry,rows_mini_grid,check}.py`,
  `backend/tests/test_3b1_structure_registry.py`, `main.py` (+2 lines: function-local import and
  `check_at_start()` right after `install_handle_error_hook()`, before the first `include_router`).
- (second commit) bookkeeping: this packet, spec `Status: in_review`, `specs/INDEX.md`, `.ai/state/data.md` + `index-2.md`.

No migration, no route, no store.

## Module-path check

```
$PY -c "import assetops_backend, assetops_contracts; print(...)"
/opt/assetecon/AssetOpsV1-3b1/backend/assetops_backend/__init__.py /opt/assetecon/AssetOpsV1-3b1/contracts/assetops_contracts/__init__.py
```

## Done (spec §7)

| # | Question | Answer | Proof |
|---|---|---|---|
| 1 | 47 rows equal to the manifest's structure, leaves, sources, absence, homes | yes: 31 leaves + 16 nodes | T1 (8 tests; own home map asserted against `CATEGORIES`) |
| 2 | Units compose under the literal rule; a mismatch stops start-up naming the row | yes | T2, T2b, T4 (`ConfigurationError` "STRUCTURE_MONEY_HOME MINI_GRID/collected", cause `StructureError`) |
| 3 | Each §4 refusal proven, incl. the three design acceptance cases | yes, 12 codes | T3 + mutation table below |
| 4 | Every row names its own category; no inheritance path | yes | `check._category`/`_objective`/`_money_home` read `row.home` only; no parent lookup in `registry.py`/`check.py` |
| 5 | Nothing outside `structure/**`, the `main.py` call, the test file, bookkeeping | yes | `git diff --stat main` |

## Tests

`env -u DATABASE_URL -u ASSETOPS_TEST_DATABASE_URL $PY -m pytest backend/tests/test_3b1_structure_registry.py backend/tests/test_health.py -q`
-> `83 passed, 1 warning in 2.74s` (warning: starlette httpx deprecation, pre-existing).
Tests were written first: the first run failed at collection (module absent).

`python3 tools/select-tests.py --base main` -> `mode: full (518 of 518 backend test files)`, `full because:
backend/assetops_backend/main.py`. Not run while building (spec §6); the merge's full tier runs it.

`pwsh -NoProfile -File tools/check-all.ps1` (fast; it takes its own heavy slot, so it is not wrapped in
`heavy-slot.sh`, which would hold a second slot): `All 40 guards passed (blocking; 0 advisory, 0 warned)`, 76.2 s wall, at `b7d261bf9`; architecture seams (module roots, dependency direction, ...) and the decision-index guard included. Log: `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/check-all.log` (scratch).

## Per-code plants (each check disabled in turn; T3 rerun; `git checkout` restored)

Each plant raises its own full text in T3 (e.g. `STRUCTURE_MONEY_HOME MINI_GRID/collected`). Disabling the code's check
function makes its plant fail:

| Code | Plant (T3) | Disabled -> T3 |
|---|---|---|
| DUPLICATE | second `tariff` row | 1 failed |
| EXPRESSION | `fuel_cost` = `diesel_l ** diesel_price` (+4 forms) | 5 failed |
| UNKNOWN_FACTOR | `diesel_l * diesel_cost` | 1 failed |
| CYCLE | `diesel_l` reads `fuel_cost` -> names `diesel_l` | 1 failed |
| CATALOGUE | renamed leaf, wrong unit, cold leaf, deleted `liability`, node `base_kwh`, key `SOLAR_FARM/-` | 1 failed |
| LEAF_SOURCE | `om` no source / family `EMAIL`; node with source | 1 failed |
| LEAF_ABSENT | none / bad value / NEVER_EMPTY off calendar / calendar not NEVER_EMPTY / node | 1 failed |
| TOLERANCE | unknown `of_factor`, unit differs, pct 0, pct -1 | 1 failed |
| UNIT | `fuel_cost` = `diesel_l + diesel_price`; declared L | 3 failed |
| CATEGORY | `unmapped_kwh` no home; OTHER; CALENDAR off calendar leaf; calendar leaf homed O2; ABOVE on leaf | 2 failed |
| OBJECTIVE | G3 under Optimize, None, O0, O10, ABOVE A1, CALENDAR O1 | 1 failed |
| MONEY_HOME | `collected` P1, `liability` P1, `om` A1 | 2 failed |

Code-major order is pinned (`test_t3_code_major_order`: MONEY_HOME on `tariff` + UNIT on `contribution` -> UNIT).
Removing the `check_at_start()` line from `main.py` fails T4 (1 failed).

## Parity (T1)

Node set and 16 expression texts equal `structures.MINI_GRID`; leaf set equals `factor_map.MINI_GRID`; every leaf's
`FilledBy(family, kind, words)` and `absent` equal `leaf_sources` (words on `om`, `staff`); every row's home equals
`home_categories.nodes.MINI_GRID`; the only unrowed home names are `cover_not_claimable`, `unclaimable_cover`;
tolerance `unexplained_l` = 2.0 % of `diesel_l`, equal to the manifest's fuel-balance `tolerance_pct`. All pass.

## Timing (R6, bound 10 ms)

First `check_all()` 0.770 ms (structure import 45 ms, once per process); median of 1,000 calls 0.454 ms (max 1.694 ms).

## Mid-build questions

Count: **0**.

## Known deviations and local readings (none changes behaviour the spec fixed)

- T1 tolerance: KOBO-001 and KISIWA-001 declare `fuel_balance.tolerance_pct: 2.0`; MTO-001 declares no fuel balance,
  so the test pins every Site that declares one (asserts at least two).
- `STRUCTURE_CATALOGUE` within its code: unknown key first (`<key>/-`), then rows in `ROWS` order, then missing
  catalogue leaves in catalogue order. "A node whose ID is a catalogue leaf ID" uses the whole catalogue.
- `parse` wraps `SyntaxError` as `ExpressionError`; `check` still maps all three (R8). `+a` is refused (not in §3).
  Unequal operands raise `UnitError` (a `ValueError`, local name).
- `registry.py` imports the rows after its records; `structure/__init__.py` imports `registry` first so any import
  order works (checked for all four modules).

## Not verified

- Full backend suite (select-tests says full; scheduled at merge).
- `3C1a` also edits `main.py`: merge `main` before review (expected one-hunk, not yet done).
- Layout evidence: not run (non-screen).

## Review focus

The literal rule in `expressions._unit`; code-major ordering in `check._CHECKS`; T1's independence (own home map, unit
table in the test); no float in `expressions.py` (`grep -n float` -> none).
