# 3B1: the structure registry, mini-grid (implementer spec)

Architect (Claude), 2026-11-20. Rev 1, spec handshake step 1. Lane B (structure). The structure is page P3B
(`structure-page-P3B.md`, approved by the owner on 20 Nov). Decisions are in `rulings.md` (D-3B1.1 to D-3B1.6). The
reviewer's guide is `reviewer-guide.md`. Questions go in `handshake.md`, then `mid-build-questions.md`.

Non-screen. Code rows only: no migration, no route, no store. 4 units. Discovery review (W5): a new mechanism and a
protected seam.

## 0. Before you start

- **Branch** `task/3B1-structure-registry` off `main`, after this spec branch merges; worktree
  `/opt/assetecon/AssetOpsV1-3b1`. Code starts when the handshake has no open question.
- **Python.** The shared `.venv` imports `main`. Set this tree first and check the module paths:
  ```bash
  cd /opt/assetecon/AssetOpsV1-3b1
  export PYTHONPATH=$PWD/backend:$PWD/backend/tests:$PWD/contracts:$PWD/simulator:$PWD/gateway:$PWD/field:$PWD/host:$PWD/tools
  PY=/opt/assetecon/AssetOpsV1/.venv/bin/python
  $PY -c "import assetops_backend, assetops_contracts; print(assetops_backend.__file__, assetops_contracts.__file__)"
  ```
  The packet records this output.
- **Read:**
  - this spec, `rulings.md` and P3B;
  - `Docs/demo-sprint/product-direction-layer4/decision-loop-specification.md` §3 (B1: the records and the start-up
    check);
  - `structure-specification.md` §2.4 (the expression language) and §3.1 (empty leaves);
  - the manifest's `structures.MINI_GRID`, `factor_map.MINI_GRID`, `home_categories.nodes.MINI_GRID` and
    `empty_states.leaf_sources.MINI_GRID`;
  - `contracts/assetops_contracts/canonical/factors.py` and `units.py`;
  - `backend/assetops_backend/outcomes/catalogue.py` (category codes);
  - `backend/assetops_backend/chain/graph.py` (today's start-up check style);
  - `backend/assetops_backend/main.py` `create_app`.
- **Databases.** None. No test here needs one, so nothing is pooled except check-all.
- **Collisions.**
  - `3A1` and `3C1` (lanes A and C) add migrations. 3B1 adds none.
  - The only shared file is `backend/assetops_backend/main.py`: one start-up call, see §5. `3C1` also edits
    `main.py`, so merge `main` before review. The edit is one line.
  - The UI lanes and DS1m touch mock-up files only.

## 1. Outcome and why

The mini-grid structure becomes code that the product checks at start-up. It is one row per factor, from leaves to
contribution, Protect measures included. Each row carries:
- its expression and unit;
- its home category and objective;
- what fills it and what its absence means (leaves);
- its tolerance where one is declared.

`3B3` evaluates it, `3B2` pins Findings to it, `3B7a` snapshots it, and `3B6` adds cold rooms and EV depots on the
same core. P3B's rules 1, 2 (its declaration half) and 5 hold here.

## 2. The rows

`backend/assetops_backend/structure/rows_mini_grid.py` holds one literal tuple `ROWS` of 47 `FactorRow` values
(D-3B1.1): 31 leaves and 16 nodes. Version 1 of `MINI_GRID`.

### 2.1 Leaves (31)

The leaves are exactly `canonical.leaves_of("MINI_GRID")`, in that order. For each leaf:

| Field | Value |
|---|---|
| `unit` | The catalogue unit (`LEAF_FACTORS[id].unit`) |
| `filled_by` | `FilledBy(family, kind)`, copied verbatim from `empty_states.leaf_sources.MINI_GRID[id]` `family` and `kind` |
| `absent` | That row's `absent` |
| `home` | `home_categories.nodes.MINI_GRID[id]`, mapped as in §2.3 |
| `expression` | None |
| `tolerance` | None, except `unexplained_l`: `Tolerance(of_factor="diesel_l", pct=Decimal("2.0"))`, the manifest's fuel-balance tolerance (D-3B1.4) |

### 2.2 Nodes (16)

The expression is the manifest's text verbatim. The unit is the composed unit; it is declared and is also checked at
start-up.

| Node | Expression | Unit | Home |
|---|---|---|---|
| `metered_kwh` | `delivered_kwh - technical_loss_kwh - unexplained_loss_kwh` | `KWH` | grow G1 |
| `billed_kwh` | `metered_kwh - adjustments_kwh - unmapped_kwh` | `KWH` | grow G1 |
| `revenue` | `billed_kwh * tariff + productive_kwh * productive_tariff` | `MONEY` | grow G1 |
| `collected` | `revenue - in_transit - outstanding` | `MONEY` | optimize O3 |
| `diesel_l` | `necessary_l + candidate_l + unexplained_l + extra_l` | `L` | optimize O1 |
| `fuel_cost` | `diesel_l * diesel_price` | `MONEY` | optimize O1 |
| `battery_wear` | `battery_throughput_kwh * wear_rate` | `MONEY` | optimize O1 |
| `cost_to_serve` | `fuel_cost + om + staff + collection_cost + battery_wear` | `MONEY` | optimize O1 |
| `contribution` | `revenue - cost_to_serve` | `MONEY` | above |
| `obligation_hours_without_redundancy` | `reduced_days * hours_per_day` | `HOUR` | protect P1 |
| `shortfall_backed` | `min(1, floor(standby_kw / max(lost_unit_kw, 1)))` | `1` | protect P1 |
| `obligation_hours_without_backup` | `obligation_hours_without_redundancy * (1 - shortfall_backed)` | `HOUR` | protect P1 |
| `replayed_dawn_days_below_safeguard` | `dawn_days_below` | `DAY` | protect P1 |
| `asset_days_out_of_service` | `reduced_days` | `DAY` | protect P2 |
| `asset_days_total` | `major_assets * period_days` | `DAY` | optimize O2 |
| `asset_days_available` | `asset_days_total - asset_days_out_of_service` | `DAY` | optimize O2 |

`home_categories.nodes.MINI_GRID` also names `cover_not_claimable` and `unclaimable_cover`. Those are rights nodes;
they come with `9a0` and `OPS1` (queued) and are not rows here (D-3B1.5). The operations measures (repeat failures,
overdue schedules, scheduled share) are `OPS1`'s rows.

### 2.3 Records and vocabularies (`structure/registry.py`)

- `HOMES`: `grow` → `GROW_REVENUE`, `optimize` → `OPTIMIZE_COST`, `protect` → `PROTECT_ASSET`, `assure` →
  `ASSURE_PERFORMANCE`, `above` → `ABOVE`, `calendar` → `CALENDAR`. These are the catalogue's codes
  (`outcomes/catalogue.py:9`), plus `ABOVE` and `CALENDAR`.
- `Home(category, objective)`. `objective` is `G1`..`G9`, `O1`..`O9`, `P1`..`P9`, `A1`..`A9`, or `None` for `ABOVE`
  and `CALENDAR`.
- `ABSENT = ("MISSING", "ZERO_WHEN_HELD", "OPTION_ONLY", "NEVER_EMPTY")`.
- `FAMILIES = ("COMMERCIAL_RECORD", "READING", "OPERATIONAL_RECORD", "OBSERVER", "DECLARED", "DOCUMENT", "CALENDAR")`.
- Frozen dataclasses:
  - `FilledBy(family, kind)`;
  - `Tolerance(of_factor, pct: Decimal)`;
  - `FactorRow(factor_id, expression: str | None, unit: Unit, home: Home, filled_by: FilledBy | None,
    absent: str | None, tolerance: Tolerance | None, levers: tuple[str, ...] = ())`, with the properties `is_leaf`
    (expression is None), `money` (`unit.is_money`) and `children` (the names in the expression, in first-seen order);
  - `Registry(structure_key, version, rows: tuple[FactorRow, ...])`, with `row(id)`.
- `REGISTRIES: Mapping[str, Registry]` holds only `MINI_GRID` (version 1) in this unit. `3B6` adds `COLD_CHAIN` and
  `EV_DEPOT_CAPTIVE`.
- `levers` stays empty until step 6 declares levers (P6).

## 3. The expression language (`structure/expressions.py`)

- `parse(text) -> Expr` uses `ast.parse(text, mode="eval")`. It allows only:
  - names;
  - numeric literals, read from their source text as `Decimal`, never as a float;
  - binary `+ - * /`;
  - unary `-`;
  - calls to `min`, `max`, `ceil` and `floor`, with positional arguments only.

  Anything else raises `StructureError("STRUCTURE_EXPRESSION <key>/<factor>")`.
- `unit_of(expr, units: Mapping[str, Unit]) -> Unit` applies the literal rule (D-2A.4, ruled here as D-3B1.2):
  - in `+`, `-`, `min` and `max`, a literal takes the unit of the other operands;
  - all non-literal operands must have equal units;
  - in `*` and `/`, a literal is dimensionless;
  - `ceil` and `floor` keep their argument's unit;
  - an expression made only of literals is dimensionless.
- No evaluation here: `3B3` evaluates.

## 4. The start-up check (`structure/check.py`)

`check(registry) -> None` raises the first `StructureError(code, structure_key, factor_id)`. Its text is
`"<CODE> <structure_key>/<factor_id>"`. The checks run in this order, over the rows in table order:

| Code | When |
|---|---|
| `STRUCTURE_DUPLICATE` | two rows with one ID |
| `STRUCTURE_EXPRESSION` | an expression outside §3 |
| `STRUCTURE_UNKNOWN_FACTOR` | a name in an expression with no row |
| `STRUCTURE_CYCLE` | a node reaches itself through its children |
| `STRUCTURE_CATALOGUE` | a leaf not in `2a`'s catalogue for this structure key, or whose unit differs from the catalogue's |
| `STRUCTURE_LEAF_SOURCE` | a leaf without `filled_by`, or a family outside `FAMILIES` |
| `STRUCTURE_LEAF_ABSENT` | a leaf without `absent`, or a value outside `ABSENT`; `NEVER_EMPTY` only for family `CALENDAR` and the reverse |
| `STRUCTURE_UNIT` | a node whose composed unit differs from its declared unit, or whose operands cannot compose |
| `STRUCTURE_CATEGORY` | a row with no `home`, or a category outside `HOMES` (never taken from a parent: there is no inheritance code path) |
| `STRUCTURE_OBJECTIVE` | an objective whose letter is not its category's (G for Grow, O for Optimize, P for Protect, A for Assure; none for `ABOVE` or `CALENDAR`) |
| `STRUCTURE_MONEY_HOME` | a money row whose home is `PROTECT_ASSET` or `ASSURE_PERFORMANCE` |

`check_all()` runs `check` on every registry in `REGISTRIES`. Three checks from `decision-loop-specification.md` §3
belong to later slices (D-3B1.6):
- "a MISSING leaf reads a number when absent" is a runtime rule of `3B3`;
- "a named observer exists at its version" waits for the observer registry (`3B4`);
- mechanism pins and levers belong to `3B2` and step 6.

## 5. Start-up

In `create_app` (`backend/assetops_backend/main.py`), before any router is built, add
`structure.check.check_all()`. A `StructureError` becomes `ConfigurationError(str(error))`, so the process refuses to
start and names the row. This is one call and one import. The cost is under 10 ms, measured in the packet.

## 6. Tests (written first)

All in `backend/tests/test_3b1_structure_registry.py`, no database:

- **T1 Parity with the manifest.** This is the independent check (W2): the test reads the manifest with `yaml` and
  never imports the rows' constants into its expectations.
  - the node set and each node's expression text equal `structures.MINI_GRID`;
  - the leaf set equals `factor_map.MINI_GRID`'s keys;
  - every leaf's `filled_by` and `absent` equal `leaf_sources`;
  - every row's home equals `home_categories.nodes.MINI_GRID`, mapped through `HOMES`;
  - the only home names without a row are `cover_not_claimable` and `unclaimable_cover`.
- **T2 Units.** `check_all()` passes. The composed unit of each node equals §2.2's table, which the test lists itself.
  `unit_of` follows the literal rule on `max(x, 0)`, `0 - cost` and `min(1, …)`.
- **T3 Refusals.** For each code of §4, a planted copy of the registry (`dataclasses.replace` on one row) raises the
  full text, for example `STRUCTURE_MONEY_HOME MINI_GRID/collected` when `collected` is homed under protect P1.
  Three cases follow `decision-loop-specification.md` §3's acceptance tests:
  - the home removed from `unmapped_kwh` gives `STRUCTURE_CATEGORY`;
  - `liability` homed under Protect gives `STRUCTURE_MONEY_HOME`;
  - a unit mismatch gives `STRUCTURE_UNIT`.
- **T4 Start-up.** `create_app()` with a monkeypatched bad registry raises `ConfigurationError` naming the row. With
  the real registry it starts, and existing routes are unchanged (`test_health.py` still passes).
- **T5 Expressions.** Every disallowed form is refused: attribute access, subscripts, `**`, keyword arguments, an
  unknown function and a string literal. Numeric literals are `Decimal` (`"1.5"` is not `1.5` as a float).

Commands:
```bash
$PY -m pytest backend/tests/test_3b1_structure_registry.py backend/tests/test_health.py -q
pwsh -NoProfile -File tools/check-all.ps1      # fast mode, once, at the end
python3 tools/select-tests.py --base main      # main.py changes, so "full"; not run while building; the merge's full tier runs it
```

## 7. Done (questions)

1. Does the registry hold the 47 mini-grid rows, equal to the manifest's structure, leaves, sources, absence rules and
   homes (T1)?
2. Do units compose under the literal rule, and does a mismatch stop the process at start-up, naming the row (T2, T4)?
3. Is each refusal of §4 proven, including the design's three acceptance cases (T3)?
4. Does every row name its own category, with no inheritance path in the code?
5. Is nothing changed outside `backend/assetops_backend/structure/**`, the one `main.py` call, the test file and the
   finish bookkeeping?

Packet: `specs/3B1-structure-registry/packet.md`, with the module-path output, the start-up time and the mid-build
question count.

## 8. Out of scope

Evaluation and the `missing` record (`3B3`). Findings pins and the outcome map's parity (`3B2`). The observer and
tolerance use (`3B4`). Cold rooms and EV depots (`3B6`). The snapshot (`3B7a`). Operations and rights rows (`OPS1`,
`9a0`). Levers (step 6).
