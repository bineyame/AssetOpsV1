# 3B3: the structure read, Site and portfolio (implementer spec)

Architect (Claude), 2026-11-20. Rev 2: handshake round 1 folded in (`rulings.md`, "Handshake answers (round 1)"). Lane B, the unit after `3B1` (the schedule order is
`3B1`, `3B3`, `3B2`).
- **Structure:** page P3B (approved 20 Nov), `decision-loop-specification.md` §3 ("Evaluation"), and
  `structure-specification.md` §2 and §3.1.
- **Empty states:** D-2026-11-20-l4-empty-states.
- **Decisions:** `rulings.md` (D-3B3.1 to D-3B3.16, and the handshake answers R1 to R19, P1 to P10).
- **Carried from 3B1's review:** L1, the Decimal context, division by zero, floor and ceil, the neutral values for
  option-only leaves, and parse-once (`specs/3B1-structure-registry/rulings.md`, "Review round 1 answers").
- **Reviewer guide:** `reviewer-guide.md`.

Non-screen. 4 units (rev 2; was 3). Discovery review (W5), because the unit computes a new mechanism and money figures.

## 0. Before you start

- **Branch.** `task/3B3-structure-read` off `main`. It depends on `3B1`, which is merged. The worktree is
  `/opt/assetecon/AssetOpsV1-3b3`. Code starts when the handshake has no open question.
- **Python.** The shared `.venv` imports `main`. Set this tree first, and check the module paths:
  ```bash
  cd /opt/assetecon/AssetOpsV1-3b3
  export PYTHONPATH=$PWD/backend:$PWD/backend/tests:$PWD/contracts:$PWD/simulator:$PWD/gateway:$PWD/field:$PWD/host:$PWD/tools
  PY=/opt/assetecon/AssetOpsV1/.venv/bin/python
  $PY -c "import assetops_backend, assetops_contracts; print(assetops_backend.__file__, assetops_contracts.__file__)"
  ```
  The packet records the output.
- **Read:**
  - `rulings.md`;
  - `backend/assetops_backend/structure/` (all of it), and the 3B1 rulings;
  - `structure-specification.md` §3.1, and `integration-source-to-canonical-design.md` §6.2 (`factor_value` and
    `missing`);
  - `Docs/demo-sprint/product-direction-layer4/evaluate_structure.py:637-700` (`leaf_values`, `missing_entry`,
    `target_side_entries`);
  - for the providers:
    - `chain/outcomes.py:108` `_month_reading` (its sum is extracted as `month_sum`, P1);
    - `chain/reader.py:154` `SnapshotReader.latest`;
    - `chain/measures.py:44,55`;
    - `chain/read.py:162-180` `window_days` and `local_days`;
    - `financials/fuel_cost.py:440` `select_window_price`;
    - `financials/composition.py:142-171` (`price_selection`, the reuse pattern for the price port, P2).
- **Databases.** The Postgres provider tests use `*_test` only, through the harness, with
  `tools/heavy-slot.sh --db -- <command>`. Never touch ports 5490 or 8990, the walkthrough database or Docker.
- **Collisions.**
  - `3B2` follows this unit. It adds `structure/pins.py` and extends `check.py`; this unit also edits `check.py` (L1).
    Whichever merges second merges `main` first.
  - `3B1`'s rows gain a `neutral` field here (§2.4).
  - Lanes A and C do not touch `structure/`. `3A4` (lane A) will later register a commercial provider through §3's
    port. This unit adds none.

## 1. Outcome and why

One function evaluates the registry, bottom-up, for a Site and a month, from the leaf values that today's product
holds. It returns for every factor:
- its value, or none;
- its evidence class, which is the weakest among its parts;
- its sources, coverage and currency;
- a `missing` record whenever the value does not rest on its own record.

Each summed portfolio factor is the sum over the Sites that have it, and the Sites that do not are named as excluded
for that factor (D-3B3.13).

Today most leaves have no source yet. They read "not available yet", with the record that would fill them, and
never 0. As `3A4`, `4b` and the observers land, each one adds a provider, and the same read fills more of the
structure with no change here.

Gate question: does the structure evaluate on today's operational leaves, with coverage and evidence class, and with no
stored figure as a source? The proof is a parity test against the pack's evaluator: given the pack's leaves, the nodes
equal `derived-values.json` to the cent.

## 2. The evaluator (`structure/evaluate.py`; pure, no I/O)

### 2.1 Records

All records are frozen dataclasses.

| Record | Fields |
|---|---|
| `Missing` | `record_kind`, `source_family`, `cause` (`NOT_RECEIVED`, `NOT_CONNECTED`, `NOT_CALCULATED_YET`), `carried_as` (`None`, `TARGET`, `ASSUMPTION`, `RESIDUAL`), `blocks: tuple[str, ...]`, `record_words: str \| None`, `assumption: str \| None`, `note: str \| None` (P10: a price reason, or a pack note). These are the `factor_value.missing` fields; `slice` and `trigger` are pack-only and left out |
| `Coverage` | `covered: int`, `expected: int` (Site-local days of the month) and `grades: Mapping[str, int]` (day counts by grade) |
| `LeafValue` | `value: Decimal \| None`, `evidence: str`, `sources: tuple[str, ...]`, `coverage: Coverage \| None`, `missing: Missing \| None`, `currency: str \| None` |
| `FactorValue` | `factor_id`, `value: Decimal \| None`, `unit: Unit`, `evidence: str`, `sources: tuple[str, ...]`, `coverage: Coverage \| None`, `missing: Missing \| None`, `missing_leaves: tuple[str, ...]`, `assumed_leaves: tuple[str, ...]`, `currency: str \| None` |

- **Evidence classes, strongest first** (D-3B3.2): `RECORDED`, `MEASURED`, `DECLARED`, `DERIVED`, `ESTIMATED`,
  `MODELLED`, `NOT_AVAILABLE`. `NEUTRAL` (D-3B3.15) is outside the order: only an OPTION_ONLY leaf at its neutral
  value carries it, and the fold below skips it. Any other class is refused (`STRUCTURE_EVIDENCE`).
  - A node's evidence is the weakest of its non-`NEUTRAL` children's, which is the latest in this order. A node
    whose children are all `NEUTRAL` is `NEUTRAL`.
  - A node over any child with no value is `NOT_AVAILABLE`.
- **Sources** are union-sorted up the structure.
- **Coverage** (R7). The share is `Fraction(covered, expected)`, and `expected == 0` is share 0. A node keeps the
  whole `Coverage` of the child with the smallest share; on a tie, the first child in `names()` order. `None` is
  ignored.
- **`missing_leaves` and `assumed_leaves`** (R13). A leaf with no value has `missing_leaves = (itself,)`; a leaf
  with `carried_as` TARGET or ASSUMPTION has `assumed_leaves = (itself,)`; otherwise `()`. A node's lists are the
  sorted union of its children's.
- **Currency** (R16, D-3B3.16). A node's currency is the one non-None currency among its children. Two different
  currencies give no value, with `Missing("CURRENCY_MISMATCH:<a>,<b>", "OBSERVER", "NOT_CALCULATED_YET", None,
  blocks, None, None, None)`. Nothing is converted.
- **Zero.** A node value equal to zero is normalised with `copy_abs()`, so `-0` never shows (P10).

### 2.2 `evaluate(registry, leaves: Mapping[str, LeafValue]) -> Mapping[str, FactorValue]`

- **Decimal context** (carried). Every operation runs inside
  `decimal.localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN))`. Nothing is quantised.
- **The parsed tree.** Expressions are taken from the registry's parse-once cache (§2.4).
- **Leaves.** Each leaf's `FactorValue` copies its `LeafValue`, with `missing.blocks` filled by `evaluate` (P6:
  callers pass `blocks=()`, and `dataclasses.replace` sets the computed list).
  - A leaf missing from `leaves` raises `StructureError("STRUCTURE_LEAF_INPUT", key, factor)`. That is a caller bug,
    never a zero.
- **Leaf-value checks** (R6, R14, R16, R17; closes D-3B1.6's first item). Before evaluating, every input `LeafValue`
  is checked, and the first failure raises `StructureError(code, key, leaf)`. These are runtime codes, not in
  `check.CODES`:
  - `STRUCTURE_MISSING`: value None and `missing` None; a value with a `missing` whose `carried_as` is None; value
    None with `carried_as` set; a non-empty `missing.blocks`.
  - `STRUCTURE_EVIDENCE`: a class outside §2.1's order and `NEUTRAL`; `carried_as` TARGET or ASSUMPTION without
    `ESTIMATED`; value None without `NOT_AVAILABLE`; `NEUTRAL` on a row that is not OPTION_ONLY, or with a value
    other than `row.neutral`.
  - `STRUCTURE_CURRENCY`: a leaf whose unit has the money dimension, with a value and no currency, unless `NEUTRAL`.
- **Nodes** are evaluated in dependency order.
  - If any child has no value, the node has no value. `missing_leaves` is the sorted union of the leaves below it that
    have no value, and the node's own `missing` is `None`; each leaf carries its own. The node is never zero-filled.
- **Operators.**
  - `+`, `-`, `*` and unary minus work on Decimals.
  - **Neutral identity** (R15, D-3B3.15). In `*`, an operand that is a `NEUTRAL` 0 makes the product 0 with
    evidence `NEUTRAL`, whatever the other operand, and the other operand's missing leaves are not inherited. This
    is the only short cut: any other `0 x unknown` has no value.
  - `/` by zero gives no value. The node's `missing` is `Missing("ZERO_DENOMINATOR:<text of the denominator>",
    "OBSERVER", "NOT_CALCULATED_YET", None, blocks, None, None)` (carried).
  - `min` and `max` work on Decimals.
  - `floor(x)` is `x.to_integral_value(rounding=ROUND_FLOOR)`, and `ceil(x)` uses `ROUND_CEILING`. Both are
    mathematical (carried).
- **`assumed_leaves`**: a node over any assumed or carried-at-target leaf is at most `ESTIMATED` (it follows from the
  leaf being `ESTIMATED`).
- **`blocks`** for a leaf's `Missing` is computed here, never typed. It lists the ancestors breadth-first and nearest
  first, in registry order within a level, matching the pack's `ancestors()`. `blocks_of(registry, leaves) ->
  tuple[str, ...]` is exported: the same walk started from a group of leaves (R11), as the pack's plan-side groups.

### 2.3 `compose(registry, per_site: Mapping[str, SiteStructure]) -> Composition` (D-3B3.13, D-3B3.14)

The portfolio is composed factor by factor, never Site-by-Site on `contribution`.
- A `SiteStructure` evaluated under another structure key or version raises
  `StructureError("STRUCTURE_COMPOSE", key, site_code)` (R10).
- Only rows with `composes == "SUM"` are composed. The rest are listed in `Composition.not_composed` and are not in
  `values` (R8). Weighted prices are `5b`'s.
- For each composed factor:
  - `included` are the Sites where it has a value; `excluded` maps every other Site to its `missing_leaves`.
  - The value is the sum over `included`. With no Site included, the value is None (never 0), and `missing_leaves`
    is the union of the excluded Sites' lists, each entry `SITE:leaf`.
  - Evidence is the weakest across `included` (§2.1's fold); sources the union.
  - Coverage is `Coverage(sum covered, sum expected, summed grades)` over `included` (R7).
  - Currency as §2.1: two currencies across `included` give no value and `CURRENCY_MISMATCH`.
- Records:
  - `PortfolioValue(value: FactorValue, included: tuple[str, ...], excluded: Mapping[str, tuple[str, ...]])`.
  - `Composition(values: Mapping[str, PortfolioValue], not_composed: tuple[str, ...], sites: tuple[str, ...],
    sites_excluded: Mapping[str, tuple[str, ...]])`. `sites_excluded` holds the Sites excluded whole, with
    `("STRUCTURE_NOT_DECLARED",)` (§4).
- Because two factors may rest on different Site sets, portfolio `revenue - cost_to_serve` need not equal portfolio
  `contribution`. The screen (`3B5`) shows "k of n Sites" beside any value with a non-empty `excluded`.

### 2.4 Registry changes (`structure/registry.py`, `rows_mini_grid.py`)

- **Neutral values** (carried). `FactorRow` gains `neutral: Decimal | None = None`.
  - The OPTION_ONLY leaves carry the literal the manifest's `factor_map` declares: `extra_l`,
    `battery_throughput_kwh` and `collection_cost` are `Decimal("0")`.
  - `MINI_GRID` becomes version 2, because a row field changed (D-2A.2's class). It is replaced in place, because
    nothing stores a version 1 value (R9; D-3B3.9 amended). `test_3b1_structure_registry.py:88` is edited to
    `version == 2`.
  - The start-up check refuses `neutral` on a row that is not OPTION_ONLY, an OPTION_ONLY row without it, and a
    `neutral` that is not a finite `Decimal` (a float, NaN or Infinity) (`STRUCTURE_NEUTRAL`, placed after
    `STRUCTURE_LEAF_ABSENT` in `CODES`; P7).
- **What is summed** (R4, D-3B3.14). `FactorRow` gains `composes: str = "NONE"` (`SUM` or `NONE`; the default fails
  closed). `_leaf` and `_node` take it as a required keyword, so every row states it.
  - MINI_GRID `SUM`: every money leaf and node; every `KWH` and `L` leaf and node; `reduced_days`,
    `dawn_days_below`, `customer_hours_interrupted`, `field_visits`, `major_assets`,
    `obligation_hours_without_redundancy`, `obligation_hours_without_backup`, `replayed_dawn_days_below_safeguard`,
    `asset_days_out_of_service`, `asset_days_total`, `asset_days_available`.
  - MINI_GRID `NONE`: `tariff`, `productive_tariff`, `diesel_price`, `wear_rate`, `hours_per_day`, `standby_kw`,
    `lost_unit_kw`, `shortfall_backed`, `period_days`.
  - `STRUCTURE_COMPOSES` (after `STRUCTURE_UNIT`) refuses a value outside the two, and `SUM` on a unit with a
    denominator.
- **Parse once** (carried; P5). `Registry.parsed: Mapping[str, Expr]` and `Registry.parents: Mapping[str,
  tuple[str, ...]]` are `functools.cached_property` (per instance, so a planted registry starts empty), built lazily
  per row so a planted bad expression is still refused by `check`, not at attribute access. `FactorRow.children`
  stays self-contained, through a module-level `functools.lru_cache` over the expression text that calls
  `expressions.parse` by attribute. The T5 counting test clears that cache first.
- **L1, tolerance** (carried; the same class as `neutral`, P7). `STRUCTURE_TOLERANCE` also refuses a `pct` that is not a `Decimal`, not finite, or not
  greater than 0. A float, `Decimal("Infinity")` and `Decimal("NaN")` each raise the full text, and none of them
  raises a `TypeError` or `InvalidOperation`.

## 3. Leaves from today's product (`structure/sources.py`)

`LeafSource` is a Protocol: `leaf(ctx: ReadContext, factor_id: str) -> LeafValue`.
`ReadContext(site: chain.ports.SiteRef, month: str, known_at: datetime | None)`; the tenant is `site.tenant_id`
(P10). The month is Site-local. Its window is `[local midnight of day 1, local midnight of day 1 of the next month)`
in the Site's time zone, converted to UTC (P3). The same `known_at` is the snapshot cutoff and the assumption
`recorded_at`.

`SOURCE_STATE: Mapping[str, Mapping[str, str]]` is a literal per structure key and leaf, with one of five states
(D-3B3.3, D-3B3.11): `PROVIDED` (the leaf's own record), `ASSUMED` (a person's declared value of the same quantity,
labelled), `HELD_NOT_CALCULATED`, `NOT_CONNECTED` and `OPTION_ONLY`. A measurement of a different quantity fills
nothing. This is the honest state of 20 Nov 2026:

| State | MINI_GRID leaves |
|---|---|
| PROVIDED | `period_days`, `unserved_critical_kwh` |
| ASSUMED | `productive_tariff`, `diesel_price` |
| HELD_NOT_CALCULATED (records held, calculation not built) | `delivered_kwh` (feeder demand readings; no monthly measure built), `necessary_l` and `candidate_l` (dispatch gives minutes, not litres), `unexplained_l` (night-window residual, not a monthly litre), `reduced_days` and `hours_per_day` (work cases), `customer_hours_interrupted` (backup hours), `field_visits` (site-visit records), `dawn_days_below` (battery state of charge) |
| NOT_CONNECTED | `productive_kwh` (its record is CHARGE; metered productive energy is a different quantity, R1), `technical_loss_kwh`, `unexplained_loss_kwh`, `adjustments_kwh`, `unmapped_kwh`, `tariff`, `in_transit`, `outstanding`, `wear_rate`, `om`, `staff`, `major_assets`, `liability`, `standby_kw`, `lost_unit_kw` |
| OPTION_ONLY | `extra_l`, `battery_throughput_kwh`, `collection_cost` |

Every `Missing` a source builds names `filled_by`'s record (kind, family, words), never another record kind, and
passes `blocks=()` (P6).

How a leaf is read, by its state:
- **HELD_NOT_CALCULATED.** No value, evidence `NOT_AVAILABLE`. `Missing(filled_by.kind, filled_by.family,
  "NOT_CALCULATED_YET", None, (), filled_by.words, None, None)`.
- **NOT_CONNECTED.** No value, evidence `NOT_AVAILABLE`. `Missing(…, "NOT_CONNECTED", None, …)`. A ZERO_WHEN_HELD
  leaf is a recorded zero **only** when its source is held, and none is held here, so it is NOT_CONNECTED and never
  0 (rule 1). No recorded 0 is inferred from "no subject declared" (P4).
- **OPTION_ONLY.** `value = row.neutral`, `evidence = NEUTRAL`, `missing = None`, `currency = None`,
  `sources = ("option-only neutral",)`.
- **PROVIDED and ASSUMED.** Read as follows. Each source is today's code, reused and not copied:

| Leaf | State | How it is read | When it has a value | Absent |
|---|---|---|---|---|
| `period_days` | PROVIDED | `len(local_days(month_lo, month_hi, tz))`; evidence `DERIVED` (calendar) | always | never |
| `unserved_critical_kwh` | PROVIDED | `month_sum(rows, lo, hi, key="unserved_kwh")` over the snapshot measure `critical_served`, rows from `SnapshotReader.latest`; evidence `MEASURED`; coverage from the grade counts | the month has closed in the Site's calendar, `expected > 0` and every expected day is COMPLETE (R2, D-3B3.12) | not closed or not fully covered: `Missing(filled_by..., "NOT_RECEIVED", None, ...)`, coverage kept, no value. `expected == 0`: `NOT_CONNECTED` (P4) |
| `productive_tariff` | ASSUMED | `window_price(..., key="productive_use_price_per_kwh")`; value and currency from the PRICED selection; evidence `ESTIMATED`; `sources = ("assumption:<revision id>",)` | PRICED | any other state: `Missing(filled_by..., "NOT_CONNECTED", None, (), words, None, note=<state reason>)` |
| `diesel_price` | ASSUMED | `window_price(..., key="diesel_price_per_litre")`, as above | PRICED | as above |

An ASSUMED value carries `Missing(filled_by.kind, filled_by.family, "NOT_CONNECTED", "ASSUMPTION", (),
filled_by.words, <words>, None)`, with these literal words (the product never reads the manifest):
- `productive_tariff`: "Declared productive-use price per kWh, not a tariff schedule";
- `diesel_price`: "Declared diesel price per litre, not a fuel invoice".

**`month_sum`** (P1). A public pure `month_sum(rows, lo, hi, key) -> tuple[Decimal | None, GradeCounts]` is extracted
in `chain/outcomes.py` from `_month_reading`'s body; `_month_reading` calls it with `key="kwh"`, with no behaviour
change. The leaf applies D-3B3.12's full-coverage rule on top.

**The price port** (P2). `ProductLeafSource(snapshot_reader, window_price)`, where
`window_price(tenant, site, key, start, end, known_at) -> PriceSelection`. `structure/composition.py:
build_structure_read(database_url)` builds it from `PostgresAssumptionStore.snapshot` and
`fuel_cost.select_window_price(..., key=key, unit=unit_for(key))`, as `financials/composition.py:142-171` does. Any
state other than PRICED (`NO_PRICE`, `PRICE_CONFLICT`, `PRICE_SPANS_WINDOW`, `PRICE_REVISION_MISSING`,
`PRICE_UNIT_MISMATCH`, `PRICE_INVALID`) is absent, with the reason in `Missing.note`.

A provider for another leaf is a later slice's addition to `SOURCE_STATE` and the provider map, checked against
`filled_by` by D-3B3.11's test. It never changes the evaluator.

## 4. The read (`structure/read.py`)

`StructureRead(sources: LeafSource)` has two methods:
- `site(site: SiteRef, month, known_at=None) -> SiteStructure(site_code, month, structure_key, structure_version,
  values)`. It reads every leaf through `sources` and evaluates.
- `portfolio(tenant_id, sites: Sequence[SiteRef], month, known_at=None) -> PortfolioStructure(month, structure_key,
  structure_version, composition, sites)`. A duplicate Site, or a Site of another tenant, raises
  `StructureError("STRUCTURE_COMPOSE", key, site_code)` (P10).

`SITE_TYPE_TO_STRUCTURE = {"MINIGRID": "MINI_GRID"}` is a literal in `read.py` (R10). Only MINI_GRID Sites are read,
because cold-room and EV Sites need `3B6`. Any other Site type is excluded whole, in `Composition.sites_excluded`,
with `("STRUCTURE_NOT_DECLARED",)`. Cross-vertical totals are `3B6`'s.

**No route and no stored figure** (D-3B3.5). The read is a service only. `3B7a` serves it from the snapshot behind a
route, and `3B5` shows it. Nothing here is stored, and no stored total is an input: every value comes from leaves on
each call.

## 5. Target side

**Labelled assumptions** (D-3B3.6). The evaluator is side-agnostic. A target leaf whose `LeafValue.missing.carried_as`
is `ASSUMPTION` keeps its value and its label (`empty_states.target_side.assumption`), and makes every node above it
`ESTIMATED`, with that leaf in `assumed_leaves`.

**Which value an assumption takes** is `5a`'s, from target lines. In 3B3 the product has no target lines, so
`StructureRead` reads the actual side only. The mechanics are proven by T2 on the pack's plan side.

**An ESTIMATED actual line** carried at its target (structure-specification §3.1 rule 3) is a `LeafValue` with
evidence `ESTIMATED` and `missing.carried_as = TARGET`, and the pack's note in `Missing.note`. It is proven by T1 on
Kisiwa's `om`.

## 6. Tests (written first)

`backend/tests/test_3b3_structure_evaluate.py`, with no database:

**T1, actual-side parity with the pack (W2: the pack's evaluator is independent).** For each mini-grid Site in
`derived-values.json` (Kobo, Kisiwa, Mto):
1. Build the leaf values from that file's `actual.nodes` leaves: `Decimal(str(x))`, after asserting that each equals
   itself quantised to 0.01 (naming the leaf if not; R12). Evidence `MEASURED`; the OPTION_ONLY leaves `NEUTRAL`;
   one literal currency on every money leaf with a value (the file's, if it names one).
2. Where `missing-records.json` lists an actual-side `leaf` entry (Kisiwa `om` only; `right` and `stage` entries are
   not leaves), attach its `Missing` with `carried_as` as listed, evidence `ESTIMATED`, and its note.
3. Evaluate, then check that every node equals the file's node to the cent (`quantize(Decimal("0.01"))`), and that
   each attached leaf's computed `blocks` equals the file's `blocks`.

**T2, plan side and assumptions.** Do the same with `plan.nodes`: plan lines `DECLARED`, the plan-side ASSUMPTION
entries' leaves `ESTIMATED` with `carried_as = ASSUMPTION`.
- Every node equals the file's.
- Every node above an assumed leaf is `ESTIMATED`, and lists those leaves.
- Each plan-side group's `blocks` equals `blocks_of(registry, group.leaves)` (R11).

**T3, portfolio.** T3 keeps its own literal copy of §2.4's `SUM` list (W2).
- `compose` over the three Sites' actual values equals `derived-values.json` `portfolio.lakeside-power.actual.sums`
  for every factor in that list, with all three Sites `included`.
- The `NONE` factors are in `not_composed` and not in `values`.
- With every Site's `om` removed, `contribution` has no value (never 0), every Site is in its `excluded` with
  `om`, and `unserved_critical_kwh` is still the sum over all three (per factor, D-3B3.13).
- With only Kisiwa's `om` removed, `contribution` is the sum over Kobo and Mto, with Kisiwa excluded by name.
- Two currencies across Sites give `CURRENCY_MISMATCH`; a Site evaluated under another version raises
  `STRUCTURE_COMPOSE`.

**T4, unknown is never zero.**
- With `om` missing, every node in `blocks(om)` has no value, and no node with a value rests on `om` (R5).
  `contribution.missing_leaves` includes `om`.
- A ZERO_WHEN_HELD leaf in NOT_CONNECTED state has no value.

**T5, carried items and leaf-value checks.**
- Division by zero gives `ZERO_DENOMINATOR`, with no value.
- `floor(Decimal("-1.5")) == -2` and `ceil(Decimal("-1.5")) == -1` through the evaluator.
- Evaluation does not change the global decimal context.
- The neutral values equal the manifest `factor_map`'s literals, read from YAML. `STRUCTURE_NEUTRAL` is proven on
  planted rows, including a float, NaN and Infinity neutral.
- `STRUCTURE_COMPOSES` is proven on a planted value outside `SUM`/`NONE` and on `SUM` for a price row.
- L1: a float, `Infinity`, `NaN` and `0` pct each raise `STRUCTURE_TOLERANCE` with the full text.
- Parse once: clear the `children` cache, patch `expressions.parse` to count calls. Evaluating twice parses each
  node once.
- Each `STRUCTURE_MISSING`, `STRUCTURE_EVIDENCE` and `STRUCTURE_CURRENCY` case of §2.2 is planted once and raises.
- Neutral identity: `battery_wear` is 0, `NEUTRAL`, with `wear_rate` NOT_CONNECTED; `cost_to_serve`'s evidence is
  not weakened by the neutral leaves. A planted `MEASURED` 0 times an unknown has no value.
- A node over two currencies has no value, with `CURRENCY_MISMATCH`.
- A node computing `x - x` reads `0`, not `-0`.

**T6, sources (fakes).**
- `SOURCE_STATE` covers exactly the 31 leaves, with §3's five states.
- Each state yields §3's `LeafValue`, and every `Missing` names the row's `filled_by` kind and family.
- A ZERO_WHEN_HELD leaf is never 0.
- `period_days` for 2026-10 is 31.
- `unserved_critical_kwh`: a closed month with every day COMPLETE has the sum; one day PARTIAL or NO_DATA gives no
  value, NOT_RECEIVED, coverage `30 of 31`; an open month gives no value; `expected == 0` gives NOT_CONNECTED.
- Prices: PRICED gives an ASSUMED leaf (`ESTIMATED`, `carried_as = ASSUMPTION`, the literal words, currency); each
  non-PRICED state gives no value with the reason in `note`.

**T7, evidence order.** A node over MEASURED and DECLARED children is DECLARED. A node over any child with no value is
`NOT_AVAILABLE`. A node over MEASURED and NEUTRAL children is MEASURED.

`backend/tests/test_3b3_structure_read_postgres.py`, pooled with `--db`:
- On a harness world with Kobo's `critical_served` snapshots for every day of a closed October, and a diesel price
  revision whose `valid_from` is at or before Kobo's Site-local 1 October 00:00 (the fixture states it, P3),
  `StructureRead.site` returns `unserved_critical_kwh` summed by `month_sum` with full coverage, and `diesel_price`
  ASSUMED (`ESTIMATED`, with its currency).
- The same world with one October day missing gives `unserved_critical_kwh` no value, NOT_RECEIVED, with coverage.
- A mid-month price revision gives `diesel_price` no value, with `PRICE_SPANS_WINDOW` in `note`.
- A mini-grid Site with no operating-calendar entry gives `unserved_critical_kwh` NOT_CONNECTED (P4).
- Every NOT_CONNECTED leaf has no value. `contribution` has no value, and names its missing leaves.
- `SiteStructure` carries `MINI_GRID` and version 2.

**Regression:** `backend/tests/test_3b1_structure_registry.py` (green after the version 2 edit at `:88`), and the
existing `chain/outcomes` tests that touch `_month_reading` (unchanged after the `month_sum` extraction).

Commands (the packet also notes that `fixtures` resolves as a namespace package that takes in main's
`host/fixtures`, which is harmless here; P9):
```bash
env -u DATABASE_URL -u ASSETOPS_TEST_DATABASE_URL tools/heavy-slot.sh -- $PY -m pytest backend/tests/test_3b3_structure_evaluate.py backend/tests/test_3b1_structure_registry.py -q
ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test \
  tools/heavy-slot.sh --db -- $PY -m pytest backend/tests/test_3b3_structure_read_postgres.py -q
pwsh -NoProfile -File tools/check-all.ps1
python3 tools/select-tests.py --base main
```

## 7. Done (questions)

1. Given the pack's leaves, do all 47 nodes at Kobo, Kisiwa and Mto equal `derived-values.json` to the cent, on both
   sides? Does the composition equal it for every `SUM` factor, and does every computed `blocks` equal the pack's?
2. Is every leaf without a held source "not available", with its own record (never a second kind), cause and blocks,
   and never 0? Is every node above it without a value? Does a month with any gap day give no value?
3. Is every node labelled with its weakest part (neutrals skipped), and does every assumed or carried-at-target leaf
   make its ancestors `ESTIMATED`? Is each value that does not rest on its own record an ASSUMED leaf with words?
4. Does an empty portfolio give no value, never 0, and does every composed value name its included and excluded
   Sites? Are mixed currencies, versions, tenants and duplicate Sites refused or left without a value?
5. Are the six carried items done and tested: L1, the context, division by zero, floor and ceil, the neutral values,
   and parse once?
6. Are the leaf-value checks (`STRUCTURE_MISSING`, `STRUCTURE_EVIDENCE`, `STRUCTURE_CURRENCY`) and the start-up
   codes `STRUCTURE_NEUTRAL` and `STRUCTURE_COMPOSES` tested on planted cases?
7. Does the read use today's sources only through their existing functions, store nothing, and add no route?
8. Is nothing changed outside these files and the finish bookkeeping:
   - `structure/{evaluate,sources,read,composition}.py`, and `structure/__init__.py` only if the load order needs it;
   - the registry and rows edits, and `check.py`;
   - `chain/outcomes.py` (the `month_sum` extraction only);
   - `backend/tests/test_3b1_structure_registry.py:88` (`version == 2` only);
   - the two new test files?

## 8. Out of scope

- The route, the snapshot and "as of" (`3B7a`); recalculation (`3B7b`).
- Commercial providers (`3A4`, `4b`).
- Litre splits and the other HELD_NOT_CALCULATED observers (step 4, `OPS2`).
- Which value a target assumption takes (`5a`); attribution (`5b`).
- Cold-room and EV structures (`3B6`).
- Pins (`3B2`).
- A bound or Protect list naming a node with no row (3B1's P7): carried to `3B4` and step 6 (R18).
- A `wear_rate` provider: step 6, when an option first adds throughput (R15).
- The "k of n Sites" display: `3B5` (D-3B3.13).
