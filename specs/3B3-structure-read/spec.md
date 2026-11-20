# 3B3: the structure read, Site and portfolio (implementer spec)

Architect (Claude), 2026-11-20. Rev 1, spec handshake step 1. Lane B, the unit after `3B1` (the schedule order is
`3B1`, `3B3`, `3B2`).
- **Structure:** page P3B (approved 20 Nov), `decision-loop-specification.md` §3 ("Evaluation"), and
  `structure-specification.md` §2 and §3.1.
- **Empty states:** D-2026-11-20-l4-empty-states.
- **Decisions:** `rulings.md` (D-3B3.1 to D-3B3.10).
- **Carried from 3B1's review:** L1, the Decimal context, division by zero, floor and ceil, the neutral values for
  option-only leaves, and parse-once (`specs/3B1-structure-registry/rulings.md`, "Review round 1 answers").
- **Reviewer guide:** `reviewer-guide.md`.

Non-screen. 3 units. Discovery review (W5), because the unit computes a new mechanism and money figures.

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
    - `chain/outcomes.py:108` `_month_reading`;
    - `chain/reader.py:154` `SnapshotReader.latest`;
    - `chain/measures.py:44,55`;
    - `chain/read.py:162-180` `window_days` and `local_days`;
    - `financials/fuel_cost.py:440` `select_window_price`;
    - `financials/assumption_read.py:63`.
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
- its sources and coverage;
- a `missing` record whenever the value does not rest on its own record.

Portfolio nodes are the sum of the Sites' nodes, and any Site that cannot be evaluated is named as excluded.

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
| `Missing` | `record_kind`, `source_family`, `cause` (`NOT_RECEIVED`, `NOT_CONNECTED`, `NOT_CALCULATED_YET`), `carried_as` (`None`, `TARGET`, `ASSUMPTION`, `RESIDUAL`), `blocks: tuple[str, ...]`, `record_words: str \| None`, `assumption: str \| None`. These are the `factor_value.missing` fields; `slice` and `trigger` are pack-only and left out |
| `Coverage` | `covered: int`, `expected: int` (Site-local days of the month) and `grades: Mapping[str, int]` (day counts by grade) |
| `LeafValue` | `value: Decimal \| None`, `evidence: str`, `sources: tuple[str, ...]`, `coverage: Coverage \| None`, `missing: Missing \| None` |
| `FactorValue` | `factor_id`, `value: Decimal \| None`, `unit: Unit`, `evidence: str`, `sources: tuple[str, ...]`, `coverage: Coverage \| None`, `missing: Missing \| None`, `missing_leaves: tuple[str, ...]`, `assumed_leaves: tuple[str, ...]` |

- **Evidence classes, strongest first** (D-3B3.2): `RECORDED`, `MEASURED`, `DECLARED`, `DERIVED`, `ESTIMATED`,
  `MODELLED`, `NOT_AVAILABLE`.
  - A node's evidence is the weakest of its children's, which is the latest in this order.
  - A node over any child with no value is `NOT_AVAILABLE`.
- **Sources** are union-sorted up the structure.
- **Coverage** at a node is the minimum share of its children's coverage, taken as the child with the smallest
  `covered/expected`. `None` is ignored.

### 2.2 `evaluate(registry, leaves: Mapping[str, LeafValue]) -> Mapping[str, FactorValue]`

- **Decimal context** (carried). Every operation runs inside
  `decimal.localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN))`. Nothing is quantised.
- **The parsed tree.** Expressions are taken from the registry's parse-once cache (§2.4).
- **Leaves.** Each leaf's `FactorValue` copies its `LeafValue`.
  - A leaf missing from `leaves` raises `StructureError("STRUCTURE_LEAF_INPUT", key, factor)`. That is a caller bug,
    never a zero.
- **Nodes** are evaluated in dependency order.
  - If any child has no value, the node has no value. `missing_leaves` is the sorted union of the leaves below it that
    have no value, and the node's own `missing` is `None`; each leaf carries its own. The node is never zero-filled.
- **Operators.**
  - `+`, `-`, `*` and unary minus work on Decimals.
  - `/` by zero gives no value. The node's `missing` is `Missing("ZERO_DENOMINATOR:<text of the denominator>",
    "OBSERVER", "NOT_CALCULATED_YET", None, blocks, None, None)` (carried).
  - `min` and `max` work on Decimals.
  - `floor(x)` is `x.to_integral_value(rounding=ROUND_FLOOR)`, and `ceil(x)` uses `ROUND_CEILING`. Both are
    mathematical (carried).
- **`assumed_leaves`** is the sorted union, below the node, of the leaves whose `missing.carried_as` is `ASSUMPTION`
  or `TARGET`. A node over any such leaf is at most `ESTIMATED`.
- **`blocks`** for a leaf's `Missing` is computed here, never typed. It lists the ancestors breadth-first and nearest
  first, in registry order within a level, matching the pack's `ancestors()`.

### 2.3 `compose(per_site: Mapping[str, Mapping[str, FactorValue]]) -> Composition`

The portfolio is composed node by node.
- A Site is **excluded by name** when its `contribution` has no value. Its reasons are its `missing_leaves`.
- Every factor whose unit is money, or a count or quantity unit (`KWH`, `L`, `DAY`, `HOUR`, `MINUTE`, `1`), is the
  sum over the included Sites.
- Price factors (`MONEY/…`) and ratio factors are not summed. Their portfolio value is `None`, with
  `missing = Missing("NOT_COMPOSABLE", "DERIVED", "NOT_CALCULATED_YET", None, (), None, None)`. Weighted prices are
  `5b`'s.
- Evidence is the weakest across the Sites.
- `Composition(values: Mapping[str, FactorValue], included: tuple[str, ...], excluded: Mapping[str, tuple[str, ...]])`.

### 2.4 Registry changes (`structure/registry.py`, `rows_mini_grid.py`)

- **Neutral values** (carried). `FactorRow` gains `neutral: Decimal | None = None`.
  - The OPTION_ONLY leaves carry the literal the manifest's `factor_map` declares: `extra_l`,
    `battery_throughput_kwh` and `collection_cost` are `Decimal("0")`.
  - `MINI_GRID` becomes version 2, because a row field changed (D-2A.2's class).
  - The start-up check refuses `neutral` on a row that is not OPTION_ONLY, and an OPTION_ONLY row without it
    (`STRUCTURE_NEUTRAL`).
- **Parse once** (carried). `Registry` gains a cached `parsed: Mapping[str, Expr]` and
  `parents: Mapping[str, tuple[str, ...]]`, both built on first access and kept. `FactorRow.children` reads the
  registry's cache through `Registry.children(id)`. The row property stays for compatibility and delegates to the
  cache.
- **L1, tolerance** (carried). `STRUCTURE_TOLERANCE` also refuses a `pct` that is not a `Decimal`, not finite, or not
  greater than 0. A float, `Decimal("Infinity")` and `Decimal("NaN")` each raise the full text, and none of them
  raises a `TypeError` or `InvalidOperation`.

## 3. Leaves from today's product (`structure/sources.py`)

`LeafSource` is a Protocol: `leaf(ctx: ReadContext, factor_id: str) -> LeafValue`.
`ReadContext(tenant_id, site: SiteRef, month: str, known_at: datetime | None)`. The month is Site-local.

`SOURCE_STATE: Mapping[str, Mapping[str, str]]` is a literal per structure key and leaf, with one of four states:
`PROVIDED`, `HELD_NOT_CALCULATED`, `NOT_CONNECTED` and `OPTION_ONLY` (D-3B3.3). This is the honest state of
20 Nov 2026:

| State | MINI_GRID leaves |
|---|---|
| PROVIDED | `period_days`, `productive_kwh`, `unserved_critical_kwh`, `productive_tariff`, `diesel_price` |
| HELD_NOT_CALCULATED (records held, calculation not built) | `delivered_kwh` (feeder demand readings), `necessary_l` and `candidate_l` (dispatch gives minutes, not litres), `unexplained_l` (night-window residual, not a monthly litre), `reduced_days` and `hours_per_day` (work cases), `customer_hours_interrupted` (backup hours), `field_visits` (site-visit records), `dawn_days_below` (battery state of charge) |
| NOT_CONNECTED | `technical_loss_kwh`, `unexplained_loss_kwh`, `adjustments_kwh`, `unmapped_kwh`, `tariff`, `in_transit`, `outstanding`, `wear_rate`, `om`, `staff`, `major_assets`, `liability`, `standby_kw`, `lost_unit_kw` |
| OPTION_ONLY | `extra_l`, `battery_throughput_kwh`, `collection_cost` |

How a leaf is read, by its state:
- **HELD_NOT_CALCULATED.** No value. The leaf carries `Missing(filled_by.kind, filled_by.family,
  "NOT_CALCULATED_YET", None, blocks, filled_by.words, None)`.
- **NOT_CONNECTED.** No value. The leaf carries `Missing(…, "NOT_CONNECTED", None, …)`. A ZERO_WHEN_HELD leaf is a
  recorded zero **only** when its source is held, and none is held here, so it is NOT_CONNECTED and never 0 (rule 1).
- **OPTION_ONLY.** `value = row.neutral`, `evidence = DERIVED`, `missing = None`, `sources = ("option-only neutral",)`.
- **PROVIDED.** Read as follows (D-3B3.4). Each source is today's code, reused and not copied:

| Leaf | How it is read | Evidence | Absent |
|---|---|---|---|
| `period_days` | `len(local_days(month_lo, month_hi, tz))` | `DERIVED` (calendar) | never |
| `productive_kwh` | The snapshot measure `productive_kwh`, summed over the month exactly as `chain/outcomes.py` `_month_reading` sums it: COMPLETE and PARTIAL days counted, LOW never totalled. Coverage holds those counts | `MEASURED` | No counted day: `Missing("feeder_demand", "READING", "NOT_RECEIVED", …)` |
| `unserved_critical_kwh` | The snapshot `critical_served` `unserved_kwh`, summed by the same rule | `MEASURED` | As above, with `critical_load_delivered_power` |
| `productive_tariff` | `select_window_price` over the month, with key `productive_use_price_per_kwh` | `DECLARED` (an assumption series, not a record) | NO_PRICE, CONFLICT or PRICE_SPANS_WINDOW: `Missing("TARIFF_SCHEDULE", "COMMERCIAL_RECORD", "NOT_RECEIVED", …)` |
| `diesel_price` | `select_window_price`, with key `diesel_price_per_litre` | `DECLARED` | As above, with `EXPENSE (FUEL)` |

`ProductLeafSource(chain_reader, assumption_read)` implements the Protocol from the existing ports, and is built by
`structure/composition.py: build_structure_read(database_url)`. A provider for another leaf is a later slice's
addition to `SOURCE_STATE` and the provider map. It never changes the evaluator.

## 4. The read (`structure/read.py`)

`StructureRead(sources: LeafSource)` has two methods:
- `site(tenant_id, site: SiteRef, month, known_at=None) -> SiteStructure(site_code, month, values)`. It reads every
  leaf through `sources` and evaluates.
- `portfolio(tenant_id, sites: Sequence[SiteRef], month, known_at=None) -> PortfolioStructure(month, composition,
  sites)`.

Only MINI_GRID Sites are read, because cold-room and EV Sites need `3B6`. Any other Site type is excluded from a
portfolio with the reason `STRUCTURE_NOT_DECLARED`.

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
evidence `ESTIMATED` and `missing.carried_as = TARGET`. It is proven by T2 on Kisiwa's `om`.

## 6. Tests (written first)

`backend/tests/test_3b3_structure_evaluate.py`, with no database:

**T1, actual-side parity with the pack (W2: the pack's evaluator is independent).** For each mini-grid Site in
`derived-values.json` (Kobo, Kisiwa, Mto):
1. Build the leaf values from that file's `actual.nodes` leaves: `Decimal(str(x))`, evidence `MEASURED`.
2. Where `missing-records.json` lists an actual-side leaf, attach its `Missing`, with `carried_as` as listed.
3. Evaluate, then check that every node equals the file's node to the cent (`quantize(Decimal("0.01"))`), and that
   every leaf's computed `blocks` equals the file's `blocks`.

**T2, plan side and assumptions.** Do the same with `plan.nodes`, attaching the plan-side ASSUMPTION entry's leaves.
- Every node equals the file's.
- Every node above an assumed leaf is `ESTIMATED`, and lists those leaves.
- Kisiwa's ESTIMATED `om` carried at target is labelled as §5 says.

**T3, portfolio.** `compose` over the three Sites' actual nodes equals `derived-values.json`
`portfolio.lakeside-power.actual.sums` for every summed factor. Prices are not composed.

**T4, unknown is never zero.**
- With `om` missing, `cost_to_serve` and `contribution` have no value. `contribution.missing_leaves` includes `om`.
  No node is 0.
- A ZERO_WHEN_HELD leaf in NOT_CONNECTED state has no value.

**T5, carried items.**
- Division by zero gives `ZERO_DENOMINATOR`, with no value.
- `floor(Decimal("-1.5")) == -2` and `ceil(Decimal("-1.5")) == -1` through the evaluator.
- Evaluation does not change the global decimal context.
- The neutral values equal the manifest `factor_map`'s literals, read from YAML. `STRUCTURE_NEUTRAL` is proven on
  planted rows.
- L1: a float, `Infinity`, `NaN` and `0` pct each raise `STRUCTURE_TOLERANCE` with the full text.
- Parse once: patch `expressions.parse` to count calls. Evaluating twice parses each node once.

**T6, sources (fakes).**
- `SOURCE_STATE` covers exactly the 31 leaves.
- Each state yields §3's `LeafValue`.
- A ZERO_WHEN_HELD leaf is never 0.
- `period_days` for 2026-10 is 31.

**T7, evidence order.** A node over MEASURED and DECLARED children is DECLARED. A node over any child with no value is
`NOT_AVAILABLE`.

`backend/tests/test_3b3_structure_read_postgres.py`, pooled with `--db`:
- On a harness world with Kobo's productive-use snapshots for some October days and a diesel price revision,
  `StructureRead.site` returns `productive_kwh` summed by `_month_reading`'s rule, with its coverage, and
  `diesel_price` `DECLARED`.
- Every NOT_CONNECTED leaf has no value.
- `contribution` has no value, and names its missing leaves.

**Regression:** `backend/tests/test_3b1_structure_registry.py`, which must stay green after the version 2 bump, and
the existing `chain/outcomes` tests that touch `_month_reading`.

Commands:
```bash
env -u DATABASE_URL -u ASSETOPS_TEST_DATABASE_URL $PY -m pytest backend/tests/test_3b3_structure_evaluate.py backend/tests/test_3b1_structure_registry.py -q
ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test \
  tools/heavy-slot.sh --db -- $PY -m pytest backend/tests/test_3b3_structure_read_postgres.py -q
pwsh -NoProfile -File tools/check-all.ps1
python3 tools/select-tests.py --base main
```

## 7. Done (questions)

1. Given the pack's leaves, do all 47 nodes at Kobo, Kisiwa and Mto equal `derived-values.json` to the cent, on both
   sides? Does the portfolio composition equal it, and does every computed `blocks` equal the pack's?
2. Is every leaf without a held source "not available", with its record, cause and blocks, and never 0? Is every node
   above it without a value?
3. Is every node labelled with its weakest part, and does every assumed or carried-at-target leaf make its ancestors
   `ESTIMATED`?
4. Are the six carried items done and tested: L1, the context, division by zero, floor and ceil, the neutral values,
   and parse once?
5. Does the read use today's sources only through their existing functions, store nothing, and add no route?
6. Is nothing changed outside these files and the finish bookkeeping:
   - `structure/{evaluate,sources,read,composition}.py`;
   - the registry and rows edits, and `check.py`;
   - the two test files?

## 8. Out of scope

- The route, the snapshot and "as of" (`3B7a`); recalculation (`3B7b`).
- Commercial providers (`3A4`, `4b`).
- Litre splits and the other HELD_NOT_CALCULATED observers (step 4, `OPS2`).
- Which value a target assumption takes (`5a`); attribution (`5b`).
- Cold-room and EV structures (`3B6`).
- Pins (`3B2`).
