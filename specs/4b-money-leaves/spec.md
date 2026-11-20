# 4b: money leaves from records into the structure read (implementer spec)

Status: spec rev 3. Rev 2: handshake round 1 answered (D-4B.13 to D-4B.17). Rev 3: 4b1 review r1 answered
(`rulings.md` "Review answers (r1)"; D-4B.18 origins, built in 4b1's fix round; §2.7 regression line corrected).
4b1: merged. 4b2: in_review (`packet-4b2.md`, branch `task/4b2-money-providers`; mid-build Q2 answered).
Code starts when the handshake has no open question (`.ai/RULES.md` §4).

Architect (Claude), 2026-11-20. Lane B, on the deep-dive path's critical chain (`3B3` → `3A4` → `4b` and `5a` → `5b` →
`5c`; `two-week-build-plan.md` §0.1 row 8; D-BW1.8 to D-BW1.12; owner RC1 to RC9 accepted).
- **Structure:** P3B (approved 20 Nov): rules "unknown is never zero", "the weakest part sets the label". P3A rules 5
  and 7. Owner: "k of n sites" (`owner/owner-k-of-n-sites-2026-11-20.md`). No structure page of its own
  (`delivery-plan.md` §2).
- **Builds on (merged; `main` at `5a2ea9974`):** `3B1` (`Registry`, `FactorRow`, `FilledBy`, `REGISTRIES`, `check`), `3B3`
  (`evaluate`, `compose`, `LeafValue`, `FactorValue`, `Missing`, `blocks_of`, `StructureRead.site`/`.portfolio`,
  `site_count`, `ReadContext`, `LeafSource`, `SOURCE_STATE`, `ProductLeafSource`, `build_structure_read`), `3A4`
  (`CommercialMonths.site_month`, `MonthAmounts.closed`/`.lines`/`.stamp`, `MonthLine`, `PROVENANCE_ORDER`), `3A1`
  (`CommercialStore.latest_revisions`, `CommercialRecords.ingest`), `2a` (`PROVENANCES`, the EXPENSE, CHARGE and
  RECEIPT fields).
- **Decisions:** `rulings.md` (D-4B.1 to D-4B.17). **Reviewer guide:** `reviewer-guide.md`.

Non-screen. **2.5 units in two merges:** `4b1` (1 unit, the shared seam, reviewed and merged first) and `4b2`
(1.5 units, the providers). Discovery review (W5) for both: a seam change and money figures.

## 0. Before you start

- **Branches.** `task/4b1-stated-nodes` off `main` (worktree `/opt/assetecon/AssetOpsV1-4b1`); after it merges,
  `task/4b2-money-providers` off `main` (worktree `/opt/assetecon/AssetOpsV1-4b2`). Code starts when the handshake
  has no open question.
- **Python:** as 3B3 `spec.md` §0 (set `PYTHONPATH` for the worktree; the packet records the module paths).
- **Read:** `rulings.md`; 3B3 `spec.md` §2 to §4 and `rulings.md` D-3B3.11 to D-3B3.17; 3A4 `spec.md` §3 and §4;
  `backend/assetops_backend/structure/` (all); `commercial/months.py`, `commercial/composition.py`;
  `backend/tests/test_3a4_commercial_months.py:27-115` (`MonthsMemoryStore`, `new_world`, `ingest_at`) and
  `test_3a4_commercial_months_postgres.py:32-60` (`NairobiSeeder`, `pgworld`).
- **Databases:** `*_test` only, through the harness, Postgres runs as `tools/heavy-slot.sh --db -- <command>`. Never
  ports 5490 or 8990, the walkthrough database or Docker. **No migration.**
- **Collisions.** `5a` (lane C) adds the new package `structure/targets/` and builds on `4b1`; it does not edit what
  `4b2` edits. `3A2` has merged (`6db81330a`): `composition.py` already holds `build_commercial_months`, and `4b1`'s
  `build_commercial_reads` goes beside it; no merge-order question remains. `3B7a` (lane B, next) stores this read.
  `4d` later moves the litre leaves out of HELD_NOT_CALCULATED.

## 1. Outcome and why

The structure read shows an operator's money from their own records. For a closed month and a mini-grid Site it
fills revenue and fuel cost as stated by the billing export and the fuel invoices, collected, in transit and
outstanding from receipts, O&M and staff from expenses, and the diesel price from the fuel invoices. Every value
names its records, its evidence class and its origin (Emulated or Recorded beneath it). Every gap names the record
that would fill it, and is never 0. Below a stated heading, the factors that are not known yet (kWh delivered,
litres burned) stay named.

Gate questions (`delivery-plan.md` §3, step 4): do Kobo's 3,458.00 billed, 3,180.00 collected and 278.00
outstanding appear from records? Is each node built from mixed evidence given its weakest class, with every source
named? And, for the deep-dive: does Kobo's October contribution read 883.00, equal to the pack's
(`derived-values.json` `sites.lakeside-power/Kobo.actual.nodes.contribution`), from records alone?

## 2. Unit `4b1`: the stated-node seam (1 unit; merged on its own)

### 2.1 Registry (`structure/registry.py`, `rows_mini_grid.py`, `check.py`)

- `FactorRow` gains `stated_by: FilledBy | None = None` (after `composes`). `_node` takes `stated_by=None`.
- MINI_GRID rows, literally:
  - `revenue`: `stated_by=FilledBy("COMMERCIAL_RECORD", "CHARGE", "Billing export: the month's charges")`;
  - `fuel_cost`: `stated_by=FilledBy("COMMERCIAL_RECORD", "EXPENSE (FUEL)", "Fuel invoices for the month")`.
  - No other row states (D-4B.1).
- `REGISTRIES["MINI_GRID"]` becomes `Registry("MINI_GRID", 3, ...)`, in place (D-4B.10). Edit the four version
  assertions to 3: `test_3b1_structure_registry.py:88`, `test_3b3_structure_evaluate.py:366` and `:652`,
  `test_3b3_structure_read_postgres.py:82`. Sweep: `grep -rn '"MINI_GRID", 2\|version == 2' backend/tests` lists
  these four and the unrelated `test_s3_dispatch_assessment_postgres.py:455` only.
- Start-up check `STRUCTURE_STATED`, placed after `STRUCTURE_COMPOSES` in `_CHECKS`: refuses `stated_by` on a leaf, a
  `stated_by` whose family is not `COMMERCIAL_RECORD`, `stated_by` on a row with `composes != "SUM"`, and `stated_by`
  on a row whose unit is not exactly money (`Unit.is_money`, `MONEY^1`; D-4B.17). Message as the other codes (code, structure key, factor). Update any
  test that pins `CODES`.
- `stated_by` is product-only: the manifest has no counterpart. 3B1's manifest parity compares leaves, so it is
  unchanged; the packet confirms by running it.

### 2.2 Records (`structure/evaluate.py`)

- `ORIGIN_UNKNOWN = "unknown"` and `ORIGIN_ORDER = ("observed-financial", "field-integrated", "bench-tested",
  "source-emulated", "demo-simulated", ORIGIN_UNKNOWN)`, strongest first (a literal; a test proves `ORIGIN_ORDER[:-1]`
  equals `commercial.months.PROVENANCE_ORDER` and, as a set, `assetops_contracts.canonical.PROVENANCES`, and that
  `ORIGIN_UNKNOWN` is not in `PROVENANCES`; D-4B.18). Both exported.
- `LeafValue` gains `origins: tuple[str, ...] = ()` (last field). Every element must be in `ORIGIN_ORDER`, else
  `StructureError("STRUCTURE_ORIGIN", key, factor)` (a runtime code, beside `STRUCTURE_MISSING`); the tuple is
  stored in `ORIGIN_ORDER` order, without repeats (a caller passing another order is refused the same way).
  **D-4B.18:** a leaf or stated value with `value is not None` must have non-empty `origins`, unless its evidence is
  `NEUTRAL` or its row's `filled_by.family == "CALENDAR"`; else the same `STRUCTURE_ORIGIN`. The condition sits in
  `_check_leaf`'s existing origin check (after the currency and evidence checks, so their codes are unchanged). The
  evaluator never fills `ORIGIN_UNKNOWN` itself.
- `FactorValue` gains, as the last fields with defaults: `origins: tuple[str, ...] = ()`, `stated: bool = False`,
  `computed: Decimal | None = None`, `detail_missing: tuple[str, ...] = ()`.
- `weakest_origin(origins) -> str | None`: the element latest in `ORIGIN_ORDER`; `None` for `()`. Exported.
- Union rule for origins: `tuple(o for o in ORIGIN_ORDER if o in <union>)`.

### 2.3 `evaluate(registry, leaves, stated=MappingProxyType({}))`

Everything in 3B3 §2.2 holds. Additions:
- **Origins** fold like sources: a leaf's are its `LeafValue.origins`; a node's are the union over its operands. The
  neutral identity (D-3B3.15) returns the neutral operand, so the other operand's origins are dropped with it.
- **`detail_missing`.** A leaf with no value: `(itself,)`; a leaf with a value: `()`. A node: the sorted union of its
  operands' `detail_missing` (the neutral identity drops the other operand's list, D-4B.11). It is independent of
  whether the node has a value.
- **`computed`** is set only in the table's first row (a stated value with a value): the expression's value, None
  when the expression has none. Everywhere else it is `None`.
- **`stated`.** Keys must be rows with `stated_by` (a leaf, a node without it, or an unknown ID:
  `StructureError("STRUCTURE_STATED", key, factor)`). Each value is checked first, with `_check_leaf`'s three
  checks against the node's row (so a NEUTRAL stated value, value None without `missing`, or money without currency
  is refused with the same codes), and its origins as §2.2. Then, for a stated node:

| Stated value | Expression | The node's `FactorValue` |
|---|---|---|
| has a value | any | `value`, `evidence`, `sources`, `origins`, `coverage`, `currency` from the stated value; `missing` = its `missing` with `blocks = blocks_of(node)` (None when it has none); `missing_leaves = ()`; `assumed_leaves = (node,)` if its `carried_as` is TARGET or ASSUMPTION, else `()`; `stated = True`; `computed` = the expression's value; `detail_missing` per the rule above |
| no value, cause `NOT_CONNECTED` or `NOT_RECEIVED` | has a value | exactly as 3B3 computes it (`stated = False`, `computed = None`); the stated value's `missing` is dropped |
| no value, cause `NOT_CALCULATED_YET` (records held but refused; D-4B.16) | any | as the next row, whatever the expression: the expression never replaces a refused record |
| no value, cause `NOT_CONNECTED` or `NOT_RECEIVED` | no value | `value None`, evidence `NOT_AVAILABLE`, `missing` = the stated value's `missing` with `blocks = blocks_of(node)`; `missing_leaves` = sorted union of the expression's missing leaves and `(node,)`; sources, origins and coverage of the expression; `stated = False`, `computed = None` |

- The stated value's zero is normalised with `copy_abs()` (P10). Two currencies (stated against nothing) cannot meet:
  the stated value is the node's whole value.
- Ancestors fold the node's resulting `FactorValue` as before. With `stated` empty, `evaluate` returns exactly what
  3B3's does, field for field, plus the new fields' values per the rules above.

### 2.4 `compose`

`_compose_factor` adds: `origins` = the union over `included`; `detail_missing` = the sorted union, over `included`,
of `f"{site}:{leaf}"`; `stated = False`, `computed = None`. Nothing else changes (3B3 §2.3).

### 2.5 The read (`structure/read.py`, `structure/sources.py`)

- `sources.py` adds `class StatedSource(Protocol): def stated(self, ctx: ReadContext, factor_id: str) -> LeafValue`.
- `ProductLeafSource` (D-4B.18): `_unserved_critical`'s value and `_price`'s value pass
  `origins=(ORIGIN_UNKNOWN,)`; `_period_days` (CALENDAR), the NEUTRAL leaf and every absent leaf keep `()`.
- `StructureRead(sources, stated: StatedSource | None = None)`. `site()` passes `stated={row.factor_id:
  stated.stated(ctx, row.factor_id) for row in reg.rows if row.stated_by is not None}` when `stated` is given, else
  no `stated`. `portfolio()` is unchanged (it calls `site()`).

### 2.6 Commercial reads for the structure (`commercial/composition.py`)

```python
@dataclass(frozen=True)
class CommercialReads:
    months: CommercialMonths
    store: CommercialStore
    dispose: Callable[[], None]

def build_commercial_reads(database_url: str) -> CommercialReads  # one PostgresCommercialStore, months over it
```
`dispose` calls the store's `dispose()`. `commercial/` still imports nothing from `structure/` (D-3A4.8).

### 2.7 Tests for `4b1` (`backend/tests/test_4b1_stated_nodes.py`, no database; written first)

Leaves are built with the builder 3B3's T1 uses for Kobo's actual side (imported from
`test_3b3_structure_evaluate`; its only edit is D-4B.18's `origins` keyword (regression line below); name it in the packet), then changed as stated.
- **S1 (stated governs).** `delivered_kwh` replaced by an absent HELD leaf (3B3 §3's form); `stated={"revenue":
  LeafValue(Decimal("3458.00"), "RECORDED", ("commercial:kobo-vending",), None, None, "USD",
  ("source-emulated",))}`. Then `revenue` is 3458.00, `RECORDED`, `stated` True, `computed` None, `missing_leaves`
  `()`, `detail_missing == ("delivered_kwh",)`; `contribution` is 883.00 with `detail_missing == ("delivered_kwh",)`
  and `missing_leaves == ()`; `contribution.origins == ("source-emulated",)`.
- **S2 (both known).** All pack leaves; stated revenue 3500.00: `revenue.value == 3500.00`, `computed == 3458`
  (to the cent), `contribution == 925.00`.
- **S3 (stated absent, computed known).** All pack leaves; stated revenue absent with `Missing("CHARGE",
  "COMMERCIAL_RECORD", "NOT_CONNECTED", None, (), "Billing export: the month's charges", None, None)`: revenue is
  the computed 3458.00, `stated` False, `missing` None.
- **S4 (both absent).** As S3 with `delivered_kwh` absent: revenue has no value; `missing.record_kind == "CHARGE"`,
  `missing.blocks == ("collected", "contribution")`; `missing_leaves == ("delivered_kwh", "revenue")`;
  `contribution.missing_leaves` holds both.
- **S5 (refusals).** `STRUCTURE_STATED` for a stated key `contribution`, `om` and `nope`; `STRUCTURE_MISSING` for a
  stated value None with `missing` None; `STRUCTURE_CURRENCY` for a stated 3458.00 with currency None;
  `STRUCTURE_EVIDENCE` for a stated `NEUTRAL`; `STRUCTURE_ORIGIN` for origins `("emulated",)`, for
  `("source-emulated", "observed-financial")` and for `("demo-simulated", "source-emulated")` (wrong order; the last
  is alphabetical, so an alphabetical check accepts it).
- **S6 (origins).** `ORIGIN_ORDER[-1] == ORIGIN_UNKNOWN == "unknown"`; `ORIGIN_ORDER[:-1]` equals
  `PROVENANCE_ORDER` and, as a set, `PROVENANCES`; `"unknown" not in PROVENANCES`. With `om` origins
  `("source-emulated",)` and `staff` `("observed-financial",)`, `cost_to_serve.origins == ("observed-financial",
  "source-emulated")` and `weakest_origin` of it is `"source-emulated"`. Two pairs whose alphabetical order differs
  from `ORIGIN_ORDER`: `om` `("demo-simulated",)` with `staff` `("source-emulated",)` gives `("source-emulated",
  "demo-simulated")` and `weakest_origin` `"demo-simulated"`; `om` `("field-integrated",)` with `staff`
  `("observed-financial",)`, over `pack_leaves("Kobo", origins=("observed-financial",))`, gives
  `("observed-financial", "field-integrated")` and `"field-integrated"`. With `battery_throughput_kwh` NEUTRAL and
  `wear_rate` absent with origins `()`, and a planted `wear_rate` value with origins `("demo-simulated",)`,
  `battery_wear.origins == ()` and `battery_wear.detail_missing == ()` in both cases.
- **S7 (compose).** Kobo stated as S1 and Kisiwa from the pack (no stated): `contribution`'s portfolio
  `detail_missing == ("Kobo:delivered_kwh",)` (the Site keys the test uses), origins the union, `stated` False.
- **S8 (registry).** `MG.version == 3`; exactly `revenue` and `fuel_cost` have `stated_by`, with the literals of
  §2.1. `STRUCTURE_STATED` is raised by `check` on planted copies: `stated_by` on `om` (a leaf), on `diesel_l` as
  `FilledBy("COMMERCIAL_RECORD", "EXPENSE (FUEL)", None)` (a node, unit L, not money; the family is right, so only
  the unit refuses it), on two added stated SUM nodes that are not exactly money, `s8_money_sq = tariff * delivered_kwh * om` (`MONEY * MONEY`) and `s8_money_kwh = om * delivered_kwh` (`MONEY * KWH`), each with a control without `stated_by` (D-4B.17; mid-build Q1), on
  `contribution` with family `DECLARED`, and on a planted node with `composes="NONE"`. `CODES` has `STRUCTURE_STATED` right after `STRUCTURE_COMPOSES`.
- **S11 (a valued part names its origin; D-4B.18).** (a) Over the pack's leaves, each refused with
  `STRUCTURE_ORIGIN` and `factor_id` the planted ID: leaf `om` as `LeafValue(Decimal("600.00"), "MEASURED", ("x",),
  None, None, "USD")` (origins `()`); leaf `outstanding` the same with evidence `DERIVED`; stated `revenue`
  `LeafValue(Decimal("3458.00"), "RECORDED", ("commercial:kobo-vending",), None, None, "USD")` (origins `()`).
  (b) `om` origins `("unknown",)`, `staff` `("observed-financial",)`: `cost_to_serve.origins ==
  ("observed-financial", "source-emulated", "unknown")`, `weakest_origin` `"unknown"`; `om` `("demo-simulated",)`
  and `staff` `("unknown",)`: `weakest_origin(cost_to_serve.origins) == "unknown"`. (c) Accepted with `()`: the pack's `period_days`
  replaced by `LeafValue(Decimal(31), "DERIVED", ("calendar",), None, None, None)`, and every NEUTRAL pack leaf;
  `asset_days_total.origins == ("source-emulated",)` (from `major_assets` only).
- **S9 (read).** A fake `LeafSource` and a fake `StatedSource` that records the IDs it was asked: `StructureRead(...,
  stated=fake).site(...)` asks exactly `("revenue", "fuel_cost")` once each; without `stated` nothing is asked and
  the result equals 3B3's for the same leaves.
- **S10 (a refused stated record blocks; D-4B.16).** All pack leaves (the expression has a value); stated revenue
  absent with `Missing("CHARGE", "COMMERCIAL_RECORD", "NOT_CALCULATED_YET", None, (), "Billing export: the month's
  charges", None, "CURRENCY_MISMATCH:KES,USD")`: revenue has no value, `computed` None, `stated` False,
  `missing.cause == "NOT_CALCULATED_YET"`, `missing.note == "CURRENCY_MISMATCH:KES,USD"`, `missing_leaves ==
  ("revenue",)`; `contribution` has no value.

**Regression:** `test_3b3_structure_evaluate.py` (T1 to T7 green; its only edits are the two version edits of
§2.1, `:366` and `:652`, and D-4B.18's: `pack_leaves` gains keyword `origins: tuple[str, ...] = ("source-emulated",)`
given to every non-NEUTRAL valued leaf (NEUTRAL leaves keep `()`); `:459`'s `battery_throughput_kwh` gains
`("source-emulated",)`; `test_t6_prices` and `test_t6_unserved_critical_needs_a_closed_fully_covered_month` expect
`origins == (ORIGIN_UNKNOWN,)` on the value; `test_t6_period_days` is unchanged),
`test_3b1_structure_registry.py`, and (pooled, `--db`) `test_3b3_structure_read_postgres.py`.

## 3. Unit `4b2`: the money leaves (1.5 units)

### 3.1 `structure/money.py`

```python
COST_STATUSES = ("INVOICED", "PAID")
class CommercialLeafSource:  # implements LeafSource and StatedSource
    def __init__(self, months: CommercialMonths, store: CommercialStore, fallback: LeafSource) -> None
    def leaf(self, ctx: ReadContext, factor_id: str) -> LeafValue
    def stated(self, ctx: ReadContext, factor_id: str) -> LeafValue
```
- `leaf` serves the leaves whose state (§3.2) is `PROVIDED` or `PROVIDED_ELSE_ASSUMED` in 4b's table (§3.4); every
  other leaf goes to `fallback.leaf(ctx, factor_id)` unchanged. `stated` serves `STATED_STATE`'s `PROVIDED` nodes; any
  other ID raises `StructureError("STRUCTURE_STATED", key, factor)`.
- **One read per Site-month read** (D-4B.12). For a context it reads, once: `amounts = months.site_month(tenant_id,
  site_id, month, known_at=known_at)` and `held_kinds = frozenset(r.kind for r in store.latest_revisions(tenant_id,
  site_id=site_id, known_at=known_at))` (the kinds *connected*, D-4B.5). It keeps `self._last = (ctx, amounts,
  held_kinds)` as one tuple and reuses it only when `self._last[0] is ctx`.

### 3.2 States (`structure/sources.py`)

- `STATES` gains `PROVIDED_ELSE_ASSUMED` (sixth, last).
- `SOURCE_STATE["MINI_GRID"]` changes exactly: `productive_kwh`, `in_transit`, `outstanding`, `om`, `staff` →
  `PROVIDED`; `diesel_price` → `PROVIDED_ELSE_ASSUMED`. The comment on `productive_kwh` becomes "its own record,
  CHARGE (productive class), now has an intake". Nothing else changes.
- New `STATED_STATE: Mapping[str, Mapping[str, str]] = {"MINI_GRID": {"revenue": PROVIDED, "fuel_cost": PROVIDED}}`.
- `ProductLeafSource.leaf` treats `PROVIDED_ELSE_ASSUMED` as its ASSUMED price path (it is the fallback's answer), and
  `PROVIDED` leaves it has no provider for (the five above) as `NOT_CONNECTED` with `filled_by` (so 3B3's read alone
  stays honest when no commercial source is wired). Edit 3B3's T6 literal state table in
  `test_3b3_structure_evaluate.py:69-80` to the new states and add the sixth, and T6's body
  (`test_t6_each_state_yields_its_leaf_value_on_its_own_record`, `:532-553`): the PROVIDED state no longer has one
  cause, so the five new PROVIDED leaves are checked against a per-leaf cause (`NOT_CONNECTED`, their `filled_by`),
  and `PROVIDED_ELSE_ASSUMED` is checked as `ASSUMED`. T6 keeps testing `ProductLeafSource`.

### 3.3 Order of judgement for every leaf and stated node 4b serves

For every row but `diesel_price`, with the row's needed kinds (§3.4):
1. A needed kind not in `held_kinds`: no value, cause `NOT_CONNECTED`.
2. `amounts.closed` is false: no value, cause `NOT_RECEIVED`, note `MONTH_OPEN` (D-4B.4).
3. The value's lines (§3.4) are empty and the row is not ZERO_WHEN_HELD, or a needed kind has no line in the month:
   no value, cause `NOT_RECEIVED`.
4. The currency lines carry two or more currencies: no value, cause `NOT_CALCULATED_YET`, note
   `CURRENCY_MISMATCH:<a>,<b>` (sorted, comma-joined). The currency lines are the used lines (§3.4), or, for a
   recorded zero, all AMOUNT lines of the needed kind, any status (handshake R9).
5. Otherwise the value of §3.4.

`diesel_price` has its own order (D-4B.6, D-4B.14, D-4B.15). A *fuel cost line* is an EXPENSE AMOUNT line, category
FUEL, status in `COST_STATUSES`:
1. EXPENSE not in `held_kinds`, or the month has no fuel cost line (open or closed): `fallback.leaf(ctx,
   "diesel_price")`, the labelled declared price.
2. `amounts.closed` is false: no value, `NOT_RECEIVED`, note `MONTH_OPEN` (invoices exist; the assumption never
   hides them).
3. The fuel cost lines carry two or more currencies: no value, `NOT_CALCULATED_YET`, `CURRENCY_MISMATCH:<a>,<b>`.
4. Σ litres (§3.4) is 0: no value, `NOT_CALCULATED_YET`, note `ZERO_DENOMINATOR:fuel_litres`.
5. Otherwise Σ amount / Σ litres.

An absent value is `LeafValue(None, "NOT_AVAILABLE", (), None, Missing(fb.kind, fb.family, cause, None, (), fb.words,
None, note), None)`, with `fb` the row's "Names when absent" record (§3.4, D-4B.13) and `note` as above, else None.
For `outstanding` in cases 1 and 3, the *failing kind* is the first of CHARGE, RECEIPT that is not connected (case 1)
or has no line in the month (case 3); `fb` is that kind's record and the note is `NEEDS:<kind>`.

### 3.4 The table (all lines from `amounts.lines`; "cost" means `status in COST_STATUSES`)

| Factor | Needed kinds | Lines | Value | Evidence | Currency | Names when absent (`READ_AS`) |
|---|---|---|---|---|---|---|
| `revenue` (stated) | CHARGE | CHARGE AMOUNT, all | Σ amount | RECORDED | the lines' | its `stated_by` |
| `fuel_cost` (stated) | EXPENSE | EXPENSE AMOUNT, category FUEL, cost | Σ amount | RECORDED | the lines' | its `stated_by` |
| `om` | EXPENSE | EXPENSE AMOUNT, category OM, cost | Σ amount | RECORDED | the lines' | its `filled_by` |
| `staff` | EXPENSE | EXPENSE AMOUNT, category STAFF, cost | Σ amount | RECORDED | the lines' | its `filled_by` |
| `productive_kwh` (ZERO_WHEN_HELD) | CHARGE | CHARGE QUANTITY, `line_type` USAGE, `tariff_class` PRODUCTIVE | Σ quantity; 0 when none and CHARGE is held | RECORDED | None | its `filled_by` |
| `in_transit` (ZERO_WHEN_HELD) | RECEIPT | RECEIPT AMOUNT, status PAID_IN_TRANSIT | Σ amount; 0 when none and RECEIPT is held | RECORDED | the RECEIPT lines' | `RECEIPT_RECORD` (not its `filled_by` SETTLEMENT, D-4B.13) |
| `outstanding` (ZERO_WHEN_HELD) | CHARGE, RECEIPT | CHARGE AMOUNT, all; RECEIPT AMOUNT, all | Σ charges − Σ receipts | DERIVED | the lines' | the failing kind's: CHARGE → `CHARGE_RECORD`, RECEIPT → its `filled_by`; cases 2 and 4: its `filled_by` |
| `diesel_price` | EXPENSE | EXPENSE AMOUNT and QUANTITY, category FUEL, cost | Σ amount / Σ litres | DERIVED | the AMOUNT lines' | its `filled_by` |

Literals in `money.py`: `CHARGE_RECORD = FilledBy("COMMERCIAL_RECORD", "CHARGE", "Billing export: the month's
charges")`; `RECEIPT_RECORD = FilledBy("COMMERCIAL_RECORD", "RECEIPT", "Receipts for the month, with their payment
status")`; `READ_AS` is the column above as a mapping (the `outstanding` entry resolved per failing kind).

- "Held" for a ZERO_WHEN_HELD row means the month has at least one line of the needed kind (any dims). A held source
  with no matching line gives a recorded `Decimal("0")`.
- **Sources** = `tuple(sorted({f"commercial:{s}" for line in used for s in line.source_systems}))`, where *used* is
  the lines that gave the value; for a recorded zero, all lines of the needed kind. **Origins** = the union of those
  lines' `provenance`, in `ORIGIN_ORDER`. Coverage is `None`.
- **Sums** are exact, under `Context(prec=200, traps=[Inexact, Rounded, InvalidOperation])` (D-3A4.9); a zero result
  is `copy_abs()`-normalised. **The price** is the one division, under `Context(prec=34, rounding=ROUND_HALF_EVEN)`,
  not quantised. Litres: QUANTITY lines with unit `L` only (2a makes every FUEL expense carry litres). No `float`.
- `outstanding` may be negative (receipts above charges, e.g. prepayment); it is shown as recorded, not clamped.
- Settlement lines are not read (D-4B.9). ADJUSTMENT, BUDGET_LINE and every other kind are not read here.

### 3.5 Composition (`structure/composition.py`)

`build_structure_read(database_url)` also calls `commercial.composition.build_commercial_reads(database_url)` and
builds `source = CommercialLeafSource(reads.months, reads.store, ProductLeafSource(...))`, the commercial builder
called third (after the snapshots and the prices, so 3B3's L1 test stays green unchanged); it returns
`StructureRead(source, stated=source)`. `dispose` disposes the snapshots, the prices and the commercial store; a
failure in any builder disposes the ones already built (3B3's L1 pattern).

## 4. Fixtures (hand-computed; the tests write these literals, W2)

### 4.1 `backend/tests/fixtures/money_leaves_lakeside.json`

`{"_note": "4b spec §4.1", "steps": [{"at": ..., "entered_by": ..., "batch": ...}]}`. Tenant `lakeside-power`, USD,
`source_version` `"1"`, every Site in `Africa/Nairobi`. Records are written in 3A4 §4's forms (CHARGE effective
`2026-10-01` to `2026-11-01` and `recognition_period` `2026-10`; RECEIPT and EXPENSE `occurred_at` as stated and
`recognition_period` `2026-10`; EXPENSE `counterparty_ref` `SUP-F` and `document_ref` = its ID) unless stated.
All steps `at` `2026-11-06T09:00:00+00:00`, `entered_by` `"service:test-4b"`, `produced_at` `2026-11-05T09:00:00+03:00`.

| Batch (`source_type`, `source_system`, provenance) | Records |
|---|---|
| A `billing_export`, `kobo-vending`, `source-emulated` | `KOBO-CH-1001` CHARGE KOBO-001: 2000.00, 5000 kWh, USAGE, `tariff_code` `T-RES`, `tariff_class` STANDARD, `account_ref` `C-1001`. `KOBO-CH-1002`: 1458.00, 3645 kWh, USAGE, `T-RES`, no `tariff_class`, `C-1002`. `KOBO-RC-1001` RECEIPT: `2026-10-20T10:00:00+03:00`, 2000.00, COLLECTED, MOBILE_MONEY, `payer_ref` `C-1001`. `KOBO-RC-1002` RECEIPT: `2026-10-25T10:00:00+03:00`, 1180.00, COLLECTED, CASH, `C-1002`. `KOBO-CH-1101` CHARGE: period `2026-11`, effective `2026-11-01` to `2026-12-01`, 50.00, 125 kWh, USAGE, `T-RES`, STANDARD, `C-1001` |
| B `expense_ledger`, `lakeside-fuel`, `observed-financial` | `KOBO-EX-FUEL-1005` EXPENSE KOBO-001: `2026-10-05T11:00:00+03:00`, 875.00, 700 L, PAID, FUEL. `KOBO-EX-FUEL-1020`: `2026-10-20T11:00:00+03:00`, 600.00, 480 L, INVOICED, FUEL. `KOBO-EX-FUEL-Q1025`: `2026-10-25T11:00:00+03:00`, 360.00, 300 L, QUOTE, FUEL |
| C `billing_export`, `kisiwa-billing`, `source-emulated` | `KISIWA-CH-1001` CHARGE KISIWA-001: 4070.00, 7400 kWh, USAGE, `T-KIS`, STANDARD, `C-2001`. `KISIWA-RC-1001` RECEIPT: `2026-10-28T10:00:00+03:00`, 3800.00, COLLECTED, MOBILE_MONEY, `C-2001` |
| D `expense_ledger`, `lakeside-accounts`, `source-emulated` | `KISIWA-EX-FUEL-1010` EXPENSE KISIWA-001: `2026-10-10T11:00:00+03:00`, 3120.00, 2400 L, PAID, FUEL |
| E DS1b's `lakeside-power.expense_ledger` batch, envelope as DS1b writes it (`assetops-world-generator`, `source-emulated`, `produced_at` `2026-11-06T06:00:00+03:00`) | Its October `actual` records only, verbatim: `gen:KOBO-001:2026-10:actual:om` 600.00, `gen:KOBO-001:2026-10:actual:staff` 500.00, `gen:KISIWA-001:2026-10:actual:staff` 500.00, `gen:MTO-001:2026-10:actual:om` 500.00, `gen:MTO-001:2026-10:actual:staff` 450.00 (DS1b writes no Kisiwa O&M: ESTIMATED_NOT_RECEIVED) |

Read clock `2026-11-20T08:00:00+00:00`. The fallback (`ProductLeafSource`) gets a snapshot reader whose `latest`
returns `()` and a `window_price` returning `SimpleNamespace(state="PRICED", value=Decimal("1.30"), currency="USD",
revision_id=UUID("4b000000-0000-4000-8000-000000000001"), reason=None)` for `diesel_price_per_litre` and
`SimpleNamespace(state="NO_PRICE", value=None, currency=None, revision_id=None, reason="NO_PRICE")` otherwise.

**Expected, Kobo `2026-10` (one Site read):**

| Factor | Value | Evidence | Sources | Origins |
|---|---|---|---|---|
| `revenue` (stated) | 3458.00 USD, `computed` None | RECORDED | `commercial:kobo-vending` | source-emulated |
| `fuel_cost` (stated) | 1475.00 USD, `computed` None | RECORDED | `commercial:lakeside-fuel` | observed-financial |
| `diesel_price` | 1.25 USD (not the fallback's 1.30) | DERIVED | `commercial:lakeside-fuel` | observed-financial |
| `om` / `staff` | 600.00 / 500.00 USD | RECORDED | `commercial:assetops-world-generator` | source-emulated |
| `productive_kwh` | 0, currency None (recorded zero) | RECORDED | `commercial:kobo-vending` | source-emulated |
| `in_transit` | 0 USD (recorded zero) | RECORDED | `commercial:kobo-vending` | source-emulated |
| `outstanding` | 278.00 USD | DERIVED | `commercial:kobo-vending` | source-emulated |
| `collected` | 3180.00 USD | DERIVED | `commercial:kobo-vending` | source-emulated |
| `cost_to_serve` | 2575.00 USD | RECORDED | `commercial:assetops-world-generator`, `commercial:lakeside-fuel`, `option-only neutral` | observed-financial, source-emulated |
| `contribution` | 883.00 USD | RECORDED | `commercial:assetops-world-generator`, `commercial:kobo-vending`, `commercial:lakeside-fuel`, `option-only neutral` | observed-financial, source-emulated |

- `revenue.detail_missing == ("adjustments_kwh", "delivered_kwh", "productive_tariff", "tariff",
  "technical_loss_kwh", "unexplained_loss_kwh", "unmapped_kwh")`; `fuel_cost.detail_missing == ("candidate_l",
  "necessary_l", "unexplained_l")`; `contribution.detail_missing` is those ten, sorted; `contribution.missing_leaves
  == ()`; `weakest_origin(contribution.origins) == "source-emulated"`.
- Kobo `2026-11`: `revenue` no value, `missing` `("CHARGE", "COMMERCIAL_RECORD", "NOT_RECEIVED", carried None, blocks
  ("collected", "contribution"), words "Billing export: the month's charges", note "MONTH_OPEN")`; `om` no value,
  NOT_RECEIVED, note `MONTH_OPEN`.

**Expected, Kisiwa `2026-10`:** revenue 4070.00; fuel_cost 3120.00; diesel_price 1.3 (compared as
`Decimal("1.30")`); staff 500.00; outstanding 270.00; collected 3800.00; in_transit 0; productive_kwh 0. `om` no
value: `Missing("EXPENSE (OM)", "COMMERCIAL_RECORD", "NOT_RECEIVED", None, ("cost_to_serve", "contribution"),
"Service contractor invoice", None, None)`. `cost_to_serve` and `contribution` no value, `missing_leaves ==
("om",)`.

**Expected, Mto `2026-10`:** om 500.00, staff 450.00. `revenue` no value, `missing` CHARGE `NOT_CONNECTED` (note
None); `fuel_cost` no value, `missing` `EXPENSE (FUEL)` `NOT_RECEIVED` (EXPENSE is connected through O&M);
`diesel_price` is the fallback's labelled assumption 1.30 (`ESTIMATED`, `carried_as` ASSUMPTION, sources
`("assumption:4b000000-0000-4000-8000-000000000001",)`, origins `("unknown",)`, D-4B.18); `productive_kwh`, `in_transit` and `outstanding` no value,
`NOT_CONNECTED`, naming (kind, words, note): `productive_kwh` its `filled_by` (`"CHARGE (productive tariff class)"`,
None, None); `in_transit` `RECEIPT_RECORD` (note None); `outstanding` `CHARGE_RECORD`, note `NEEDS:CHARGE`. `contribution.missing_leaves == ("adjustments_kwh", "candidate_l", "delivered_kwh", "fuel_cost",
"necessary_l", "productive_kwh", "productive_tariff", "revenue", "tariff", "technical_loss_kwh", "unexplained_l",
"unexplained_loss_kwh", "unmapped_kwh")`.

**Expected, portfolio** (`StructureRead.portfolio` over Kobo, Kisiwa, Mto in that order; `site_count` from 3B3):

| Factor | Value | k of n | Out |
|---|---|---|---|
| `revenue` | 7528.00 | 2 of 3 | MTO-001 with revenue's nine missing leaves (the Mto list above without the four litre and fuel entries) |
| `fuel_cost` | 4595.00 | 2 of 3 | MTO-001: `("candidate_l", "fuel_cost", "necessary_l", "unexplained_l")` |
| `om` | 1100.00 | 2 of 3 | KISIWA-001: `("om",)` |
| `staff` | 1450.00 | 3 of 3 | none |
| `outstanding` | 548.00 | 2 of 3 | MTO-001: `("outstanding",)` |
| `collected` | 6980.00 | 2 of 3 | MTO-001: revenue's nine plus `in_transit` and `outstanding` (eleven, sorted) |
| `contribution` | 883.00 | 1 of 3 | KISIWA-001: `("om",)`; MTO-001: the thirteen above |

`contribution` portfolio evidence RECORDED, origins `("observed-financial", "source-emulated")`.

### 4.2 3A4's fixture, reused (`commercial_months_kobo.json`, never edited)

After step F, Kobo `2026-10`: revenue 495.50; in_transit 60.00; outstanding 335.50; collected 100.00;
productive_kwh 1000; fuel_cost 775.00; diesel_price 1.25; om 275.00 (95.00 INVOICED + 180.00 PAID; the REPAIR
QUOTE is not O&M and not cost); staff 450.00; cost_to_serve 1500.00; contribution −1004.50.
With `known_at = 2026-11-05T00:00:00+00:00`: revenue 505.50 (the FIXED 10.00 still in October); outstanding 345.50;
collected 100.00; fuel_cost 762.50; diesel_price 1.25; om 180.00; contribution −887.00.

## 5. Tests for `4b2` (written first)

**No database** (`backend/tests/test_4b_money_leaves.py`): the world is 3A4's `new_world` (imported, never edited);
batches ingested with `ingest_at`'s pattern but each step's own `entered_by`.
1. §4.1 Kobo, Kisiwa and Mto tables, every field named there (value as `Decimal` and, for sums, as `format(v, "f")`
   text; currency; evidence; sources; origins; `missing` field by field). Kobo's `contribution` equals the pack's:
   `Docs/demo-sprint/product-direction-layer4/derived-values.json` parsed with `parse_float=Decimal`,
   `sites["lakeside-power/Kobo"]["actual"]["nodes"]["contribution"]` (W2's independent check).
2. §4.1 November reads, in this order. (i) `revenue` and `om` as §4.1 (`MONTH_OPEN`), and `diesel_price` the
   fallback's 1.30, `ESTIMATED` (no November fuel invoice yet). (ii) Ingest, at `2026-11-06T10:00:00+00:00` with
   `entered_by` `"service:test-4b"`, batch B's envelope with `KOBO-EX-FUEL-1105` (EXPENSE KOBO-001,
   `2026-11-05T11:00:00+03:00`, `recognition_period` `2026-11`, 130.00, 100 L, PAID, FUEL), and read again (a new
   context): `diesel_price` and `fuel_cost` have no value, `NOT_RECEIVED`, note `MONTH_OPEN`, each naming its
   `READ_AS` record; `diesel_price` is **not** the fallback's (D-4B.14).
3. §4.1 portfolio table, with `site_count` per factor (k, n, out in the order asked).
4. §4.2 both reads.
5. **DS1b parity:** batch E's records equal, as parsed objects, the records `build_records(view, generate_history(view))`
   writes for those IDs (view: `simulator/tests/world/fixtures/view_v1.json`).
6. **Currency apart:** a KES O&M PAID expense for Kobo in October gives `om` no value, `NOT_CALCULATED_YET`, note
   `CURRENCY_MISMATCH:KES,USD`; a KES fuel invoice gives `fuel_cost` and `diesel_price` no value with that note, and
   `diesel_price` is **not** the fallback's.
7. **Connected against received, and the record named** (D-4B.5, D-4B.13; each `missing` asserted as `record_kind`,
   `source_family`, `cause`, `record_words`, `note`): (a) a world without `KISIWA-RC-1001`: Kisiwa holds no RECEIPT
   at all, so `outstanding` has no value, `("RECEIPT", "COMMERCIAL_RECORD", "NOT_CONNECTED", None,
   "NEEDS:RECEIPT")`, and `in_transit` `("RECEIPT", "COMMERCIAL_RECORD", "NOT_CONNECTED", "Receipts for the month,
   with their payment status", None)`. (b) the same world plus `KISIWA-RC-0901` (RECEIPT, period `2026-09`, 100.00,
   COLLECTED, CASH): RECEIPT is connected but not received for October, so `outstanding` is as (a) with
   `NOT_RECEIVED`, and `in_transit` as (a) with `NOT_RECEIVED`. (c) Mto in the §4.1 world (neither CHARGE nor
   RECEIPT): `outstanding` `("CHARGE", "COMMERCIAL_RECORD", "NOT_CONNECTED", "Billing export: the month's charges",
   "NEEDS:CHARGE")`; `in_transit` as (a).
8. **Quote is never cost:** with batch B's QUOTE revised to INVOICED (v`2`), Kobo `fuel_cost` 1835.00 and
   `diesel_price` 1835.00/1480 (compared as `Decimal("1835.00") / Decimal("1480")` under the 34-digit context).
9. **A late record is seen** (D-4B.12): read Kobo October through one `StructureRead`, ingest
   `KOBO-EX-OM-1030` (OM, PAID, 50.00, `lakeside-accounts`), read again with an equal but new context: `om` 650.00.
10. **States:** `SOURCE_STATE` and `STATED_STATE` equal the test's own literal tables (W2); every absent value the
    provider builds in tests 1, 2, 6, 7 and 12 names its `READ_AS` record (§3.4; the test's own literal mapping) kind,
    family and words (D-3B3.11's test, extended).
11. **Exact sums.** (a) Grep: no `float(` in `structure/money.py`; no `structure` import under `commercial/`. (b) Read
    Kobo October inside `decimal.localcontext(Context(prec=3))`: `format(v, "f")` of `revenue`, `fuel_cost` and
    `outstanding` is `"3458.00"`, `"1475.00"`, `"278.00"`, and `diesel_price == Decimal("1.25")` (a sum under the
    ambient context gives `3.46E+3`).
12. **Zero litres** (D-4B.15): the §4.1 world plus `MTO-EX-FUEL-1015` (EXPENSE MTO-001, `lakeside-accounts`,
    `2026-10-15T11:00:00+03:00`, 40.00, 0 L, PAID, FUEL): Mto `fuel_cost` 40.00 stated; `diesel_price` no value,
    `NOT_CALCULATED_YET`, note `ZERO_DENOMINATOR:fuel_litres`, **not** the fallback's.
13. **Composition disposal** (3B3's L1 pattern, `test_3b3_structure_evaluate.py:784`): with the commercial builder
    monkeypatched to raise, the snapshots and prices stores are each disposed exactly once and the error propagates;
    with all three faked, `dispose()` disposes each exactly once.

**Postgres** (pooled, `--db`; `backend/tests/test_4b_money_leaves_postgres.py`; Sites by 3A4's `NairobiSeeder`,
imported):
1. §4.1 ingested through `PostgresCommercialStore`; no-database tests 1 and 3 against it.
2. `build_structure_read(url).read.site(kobo, "2026-10")`: `revenue` 3458.00 stated, `contribution` 883.00 RECORDED;
   `dispose()` then runs without error.

**Regression:** the `4b1` set, `test_3a4_commercial_months.py`, `test_3a4_commercial_months_postgres.py`.

Commands as 3B3 §6 with these files; check-all once at the end of each unit; `select-tests` before each review.

## 6. Done (questions; each can fail)

1. Does a stated node take its record's value while keeping its expression as `computed` and `detail_missing`, and
   does the read without a stated source equal 3B3's?
2. Do Kobo's October revenue 3,458.00, collected 3,180.00, outstanding 278.00 and contribution 883.00 come from
   records alone, each with its evidence class, sources and origins?
3. Is every absent leaf or heading "not available" naming the record 4b reads for it (`READ_AS`) and a true cause (not connected, not
   received, month open, mixed currency), never 0, and is a recorded 0 shown only when its source is held?
4. Is a total never labelled stronger than its weakest part, in class and in origin?
5. Does the portfolio give each factor over the Sites that have it, naming every Site left out ("k of n sites")?
6. Is a QUOTE never a cost, a price never taken from the assumption while invoices exist (open month or closed, zero
   litres included), and every sum exact?
7. Does a second read see a record ingested after the first?
8. Is nothing changed outside: `structure/{registry,rows_mini_grid,check,evaluate,read,sources,money,composition}.py`,
   `commercial/composition.py`, the four version edits of §2.1 and the T6 table and body edits of §3.2 in the 3B1 and
   3B3 tests, the fixture, the three new test files, `simulator/tests/world/test_4b_fixture_parity.py` and the packets?

Packets: `specs/4b-money-leaves/packet-4b1.md` and `packet-4b2.md`, each with module paths and the mid-build count.

## 7. Out of scope

Tariffs (`TARIFF_SCHEDULE`) and the energy chain (`4a`); litre splits (`4d`); `liability` and kWh adjustments;
settlement matching (queue Q3); targets (`5a`); carrying a missing actual at its target (`5b`, D-4B.8); attribution
(`5b`); snapshots and routes (`3B7a`); labels on screen (`5c` with 3A5's rule); reconciliation against management
accounts (`3A7`); cold-chain and EV leaves (RC5).

## 8. Units

| Unit | Content | Commits |
|---|---|---|
| `4b1` (1) | §2: registry v3 and `STRUCTURE_STATED`; evaluator `stated` (D-4B.16's blocking row), origins, `detail_missing`; compose; `StatedSource`; `build_commercial_reads`; §2.7 tests S1 to S11 (S11 and the origin rule: D-4B.18, review r1); packet. Reviewed and merged alone | 2 |
| `4b2` (1.5) | §3: `money.py` (with `READ_AS`), states, composition; §4 fixture; §5 tests 1 to 13; packet | 2 to 3 |

## 9. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Fuel cost is the month's fuel invoices (bought), not litres burned | Yes (D-4B.7); burned litres with `4d` |
| Q2 (owner) | A missing invoice (Kisiwa's October O&M) reads not available with "k of n sites"; carrying it at its target, *Estimated*, is `5b`'s | Yes (D-4B.8) |
| Q3 | Money in transit from the receipt's status, not matched to settlement statements | Yes (D-4B.9); matching after the deep-dive |
| Q4 | `outstanding` may be negative (prepaid receipts above charges) | Shown as recorded |
