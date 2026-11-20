# 3B3 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

Round 1, 2026-11-20. One fresh Claude agent wrote both sides on request (the Reviewer's questions and an
Implementer-style pre-flight), against `main` at `e65088b10` (no change since `726a0c2cc` to the spec, the
structure package, `chain/`, `financials/` or the pack). The pre-flight items are numbered P1... as the dispatch
asked, in place of I1.... Read-only: no database, server or Docker was touched. Two probes were run in a scratch
folder against the pack and the merged registry (results quoted where used).

**Summary.** 4 High (R1 to R4), all on honesty: three "PROVIDED" leaves are not filled by their own record (R1),
a month with gap days is summed as if the gaps were 0 (R2), an empty portfolio sums to 0 (R3), and the unit rule
for what is summed misclassifies two factors and leaves three unassigned (R4). Parity to the cent holds on
today's pack (probe: 0 differences on 96 node values). The PYTHONPATH recipe imports the worktree (checked).

The Architect's expected questions, mapped: `_month_reading` and time basis, R2 and P1; prices as DECLARED, R1;
coverage merge, R7; float to Decimal parity, R12; another structure key, R10; `blocks` order, R11 (not an issue);
NOT_COMPOSABLE, R8; `missing_leaves` and `assumed_leaves` on leaves, R13; the v2 version, R9.

## Reviewer questions

**R1. High (done). Three of the five PROVIDED leaves do not come from their own record, yet carry no `missing`
and a strong class (§3, spec.md:152, :168-171; D-3B3.4).**
- Why: design §6.2 says `missing` is "null when the value rests on the leaf's own record; otherwise" it names
  that record (`integration-source-to-canonical-design.md:555`). The registry names each leaf's own record:
  - `productive_tariff`: `TARIFF_SCHEDULE`, COMMERCIAL_RECORD (`rows_mini_grid.py:44`).
  - `diesel_price`: `EXPENSE (FUEL)`, COMMERCIAL_RECORD (`rows_mini_grid.py:55`).
  - `productive_kwh`: `CHARGE (productive tariff class)`, COMMERCIAL_RECORD (`rows_mini_grid.py:42-43`).

  The spec fills them from other sources, with `missing = None`:
  - The two prices come from the operator's declared price series. The product itself calls these
    *assumptions* (`financials/assumptions.py:32`, `assumption_read.py`), and treats DECLARED as not
    authoritative (`chain/outcomes.py:31`, `AUTHORITY["DECLARED"] = False`).
  - `productive_kwh` comes from metered energy at the LOAD components the Foundation declares PRODUCTIVE
    (`chain/measure_impls.py:123-146`, `mini_depth/read.py:423-427`). That is kWh delivered, not kWh charged at
    the productive tariff. By D-3B3.4's own test ("a value of a different scope ... would be an invented figure"),
    it is a different scope and a different source family.
- The spec's "absent" column also invents record kinds that differ from the row's `filled_by`. For example,
  `productive_kwh` absent gives `Missing("feeder_demand", "READING", ...)` while the row says CHARGE /
  COMMERCIAL_RECORD. The same leaf would then name two different records, depending on whether it has a value.
- Proposed answer, as one rule for all three: a PROVIDED value that does not rest on `filled_by` is carried as a
  **labelled assumption**:
  - `missing = Missing(filled_by.kind, filled_by.family, "NOT_CONNECTED", "ASSUMPTION", blocks, filled_by.words,
    <literal words>)`. The cause is NOT_CONNECTED because no commercial intake exists before `3A4` and `4b`
    (structure-spec §3.1 defines the causes).
  - Leaf evidence is `ESTIMATED`, so every node above is ESTIMATED and lists the leaf in `assumed_leaves`.
  - `sources` names the real source: the price revision ID, or the snapshot measure.
  - The assumption words are code literals, for example "Declared diesel price per litre, not a fuel invoice" and
    "Metered productive-use energy, not billed productive kWh". The product never reads the manifest (D-3B1.1).
  - When the source is absent, the leaf carries `filled_by`'s record with the true cause, never a second kind.
  - D-3B3.4's count then reads honestly: 2 leaves on their own record (`period_days`, and
    `unserved_critical_kwh` under R2's rule), plus 3 labelled assumptions.
  - Alternative: move `productive_kwh` to HELD_NOT_CALCULATED.
- Sweep (W6): check every later provider against `filled_by` the same way. The reviewer guide's risk on `3A4`/`4b`
  already points there.

**R2. High (done). A month with gap days is summed as if the gaps were 0 (§3, spec.md:168-169).**
- Why: `_month_reading` (`chain/outcomes.py:108-124`, the sum at `:116`) sums kWh over COMPLETE and PARTIAL days. LOW and NO_DATA
  days, and every uncovered hour inside a PARTIAL day, add nothing. The board uses that sum as a month-to-date
  reading beside its checked-day count. As a structure leaf labelled MEASURED, it is a lower bound presented as
  the month's value: unknown read as zero, and a partial source filling a leaf.
  - For `unserved_critical_kwh` this understates a Protect measure. An hour with no service head is uncovered
    (`chain/measure_impls.py:226-235`), so missing hours lower the unserved total.
  - Design §6.7 (`:642`): an expected record not received leaves the node "ESTIMATED ... or not available, and
    coverage says so".
- Proposed answer:
  - The leaf has a value only when every expected Site-local day of the month is COMPLETE (`covered == expected`).
  - Otherwise the value is None, with `Missing(filled_by..., "NOT_RECEIVED", None, ...)` and the coverage kept, so
    the screen can say "28 of 31 days".
  - If the Architect prefers early visibility, the alternative is a value with evidence ESTIMATED and a stated
    lower-bound label. That needs a `carried_as` value the design does not have, so the first option is the
    default.
- Time basis (the expected question): for the current month, days after today's Site-local date are not yet
  expected. Default: a month that has not closed is read like any other month, so its leaves are None with
  NOT_RECEIVED until it closes. Month-to-date figures stay with the existing board and `3B7a`'s ranges (D-3B3.10).

**R3. High (done). An empty portfolio sums to 0, and a missing factor at an included Site is skipped (§2.3,
spec.md:116-118).**
- Why: as of 20 Nov, `contribution` has no value at any mini-grid Site, because `om`, `staff`, `tariff`,
  `wear_rate` and the litre leaves are not connected or not calculated. So every Site is excluded. "The sum over
  the included Sites" is then a sum over nothing, which a natural implementation returns as `Decimal(0)` on every
  summed factor (the pack does exactly this, `evaluate_structure.py:562`, `sum(... get(nn, 0))`).
  - Separately, an included Site may lack a factor; Protect nodes do not depend on `contribution`. Skipping that
  Site in the sum understates the total.
- Proposed answer:
  1. With no included Site, every portfolio value is None, and the composition says why (all excluded).
  2. A summed factor is None when any included Site lacks it. Its `missing_leaves` is the union, prefixed by Site
     code.
  3. T3 adds both cases, and P6 adds "drop every Site's `om`: no portfolio value, no 0".
- Question for the Architect (W3 default: keep): should exclusion be per factor, not per Site? A Site with no
  contribution still has a valid `unserved_critical_kwh`. Per-factor exclusion gives a useful portfolio read
  today; per-Site exclusion gives an empty one.

**R4. High (done). The unit rule for summing misclassifies factors (§2.3, spec.md:117-120; D-3B3.8).**
- Why: unit `1` covers counts (`major_assets`, `field_visits`) and also the 0/1 ratio `shortfall_backed`
  (`min(1, floor(...))`, `rows_mini_grid.py:88`). Summing that ratio gives "Sites backed", a different quantity
  under the same factor ID.
  - `KW` (`standby_kw`, `lost_unit_kw`) and `HOUR/DAY` (`hours_per_day`) are in neither list. The pack sums all
    of them, prices included (`derived-values.json` portfolio: `diesel_price` 3.8, `tariff` 1.35, `hours_per_day`
    10, `lost_unit_kw` 85).
  - So "equals the pack for every summed factor" depends on a list the spec does not fix.
  - `period_days` summed gives 93 "Site-days", not a period.
- Proposed answer:
  - Summing is an explicit allow-list per structure: a literal frozenset of factor IDs in the registry module, or
    a row flag `composes: SUM | NONE`, not a rule over units.
  - MINI_GRID default: money nodes and leaves; KWH and L leaves and nodes; `reduced_days`, `dawn_days_below`,
    `customer_hours_interrupted`, `unserved_critical_kwh`, `field_visits`, `major_assets`, and the `asset_days_*`
    and `obligation_hours_*` nodes.
  - Not summed: prices and rates (`MONEY/…`, `HOUR/DAY`), `KW`, `shortfall_backed` and `period_days`.
  - T3 keeps its own copy of the list (W2: shares no list with the code), and compares only those IDs with the
    pack.

**R5. Medium (done). T4 and P1 say "no node is 0", which is false on the pack's data (spec.md:223-225,
reviewer-guide P1).**
- Why: with `om` removed at Kobo, `battery_wear`, `shortfall_backed`, the `obligation_hours_*` nodes and others
  are legitimately 0 (`derived-values.json` Kobo actual). These nodes do not rest on `om`.
- Proposed answer: "every node in `blocks(om)` has no value, and no node with a value rests on `om`". Apply the
  same wording in reviewer-guide P1.

**R6. Medium (done). The deferred runtime MISSING rule (D-3B1.6) is not in the spec.**
- Why: 3B1 deferred "the runtime MISSING rule, to `3B3`". Nothing in §2.2 refuses an inconsistent `LeafValue`:
  - value None with `missing` None, which would show "not available" with no record (structure-spec l.274
    forbids a null alone);
  - a value present with `missing.carried_as` None;
  - a value None with `carried_as` TARGET or ASSUMPTION.
- Proposed answer: `evaluate` raises `StructureError("STRUCTURE_MISSING", key, leaf)` for each of the three
  cases, and T5 plants each one. This closes D-3B1.6's first item.

**R7. Medium (done). The coverage merge rule is underspecified (§2.1, spec.md:87-88).**
- Why:
  - `expected = 0` (a Site with no operating-calendar entry, P4) divides by zero.
  - Ties, and which child's `grades` the node keeps, are not stated.
  - Portfolio coverage is not defined at all (§2.3).
  - Design §6.2's coverage also names excluded subjects; `Coverage` has no place for them.
- Proposed answer:
  - The share is a `Fraction(covered, expected)`, and `expected == 0` is treated as share 0 (or refused as
    NOT_CONNECTED by P4).
  - The node keeps the minimum child's whole `Coverage`. On a tie, the first child in `names()` order wins.
  - Portfolio coverage is per factor, `Coverage(Σ covered, Σ expected, Σ grades)` over the included Sites.
  - Excluded subjects stay `3B7a`'s.

**R8. Medium (done). NOT_COMPOSABLE is a pseudo-record in the `missing` schema (spec.md:119-120).**
- Why:
  - `source_family = "DERIVED"` is not a family (`registry.py:35` FAMILIES; design §6.2).
  - NOT_CALCULATED_YET means "records held; the calculation is in a queued slice", which is only loosely true.
  - A screen that shows "not available yet" from any `missing` (structure-spec l.274) would show it for a
    portfolio price that is simply not defined.
- Proposed answer: non-composable factors are left out of `Composition.values`, and listed in
  `Composition.not_composed: tuple[str, ...]`. `ZERO_DENOMINATOR` (carried, a node-level cause) stays as ruled.

**R9. Medium (done). The v2 bump: in place, and recorded where? (§2.4, spec.md:130; D-3B3.9; D-2A.2.)**
- Why: D-2A.2 says a change is "a version 2 **beside** version 1". The spec replaces version 1 in place. Nothing
  stores a structure value yet (3B7a is not built), so in-place is safe today. But no output carries the version:
  - `SiteStructure` has `site_code`, `month` and `values` only;
  - `3B7a` must store which structure version computed a node (reviewer-guide "Risks").
- Proposed answer:
  - Replace in place, and say why in D-3B3.9 (no stored consumer of v1).
  - `SiteStructure` and `PortfolioStructure` carry `structure_key` and `structure_version`.
  - `test_3b1_structure_registry.py:88` (`MG.version == 1`) is updated to 2. Today the spec forbids that edit
    (§7.6), so it must allow it; otherwise the "stays green" regression (spec.md:253) cannot pass.

**R10. Medium. A Site with a different structure key, and mixed portfolios (§4, spec.md:185-186).**
- Why:
  - `SiteRef.site_type` is `MINIGRID | COLDCHAIN | EV_CHARGING` (`chain/ports.py:16-22`), while structure keys
    are `MINI_GRID | COLD_CHAIN | EV_DEPOT_CAPTIVE`. The mapping is not stated, and `EV_CHARGING` is not always
    a captive depot.
  - After `3B6`, MINI_GRID and COLD_CHAIN share leaf and node IDs (`staff`, `liability`, `outstanding`,
    `period_days`, and the nodes `revenue` and `contribution`; probe on `leaves_of`). A mixed portfolio would sum
    them across verticals and treat the others as partial.
- Proposed answer:
  - A literal map `{"MINIGRID": "MINI_GRID"}` in `read.py`. Any other type is excluded with
    `STRUCTURE_NOT_DECLARED`.
  - `compose` refuses Sites of more than one structure key (`StructureError("STRUCTURE_COMPOSE", ...)`). `3B6`
    decides cross-vertical totals.
  - `Composition.excluded` keeps leaf IDs and codes apart, for example `excluded: {site: reasons}` where a code
    reason is the single tuple `("STRUCTURE_NOT_DECLARED",)`. State it.

**R11. Low (closed by probe). The order of `blocks` within one level.**
- Checked: the manifest's `structures.MINI_GRID` order equals the registry's node order, and the pack's
  `ancestors()` over the manifest equals it over the registry expressions for all 31 leaves (no difference).
- One gap remains, for T2. The plan side's entries are **groups** (`leaves: [...]`), and the file's `blocks` is
  the breadth-first walk from the whole group (`evaluate_structure.py:626-634`). That is not the union of the
  per-leaf lists in any fixed order.
- Proposed answer: either T2 compares the group's `blocks` as a set equal to the union of its leaves' `blocks`,
  or `evaluate.py` exports `blocks_of(registry, leaves)`, which T2 calls on the group. The second is preferred
  (one function, the same as the pack).
- T1's "every leaf's computed `blocks`" covers only entries that carry a `leaf`; the actual-side `right` and
  `stage` entries (BAT-001, `headroom`) are not leaves. Kisiwa `om` is the only actual-side leaf entry. Say so
  in T1.

**R12. Low (closed by probe). Can the parity check to the cent fail?**
- Probe: the leaves from `derived-values.json` (`Decimal(str(x))`) were evaluated with the merged registry's
  expressions at prec 34 / HALF_EVEN, for Kobo, Kisiwa and Mto, actual and plan. Result: 0 differences over
  16 × 6 node values.
- The non-integer leaves are only prices at 2 decimals (`tariff`, `productive_tariff`, `diesel_price`,
  `wear_rate`), so `str(float)` is exact.
- Residual risk: the pack writes every value through `money()` (`evaluate_structure.py:145`, quantised to cents).
  A future leaf with sub-cent precision would be rounded in the file but not in the pack's own evaluation, and T1
  would then fail for a reason that is not a defect.
- Proposed answer: T1 asserts that each leaf it reads equals itself quantised to 0.01, so such a change fails
  loudly and names the leaf. T1 then proves the arithmetic only. The leaves are the pack's, not the product's.
- The prec 34 against 28 gap cannot matter here: the only division is `standby_kw / max(lost_unit_kw, 1)` under
  `floor`.

**R13. Low (done). `missing_leaves` and `assumed_leaves` on a leaf (§2.1).**
- Proposed answer:
  - A leaf with no value has `missing_leaves = (itself,)`. A leaf with `carried_as` TARGET or ASSUMPTION has
    `assumed_leaves = (itself,)`. Otherwise both are `()`.
  - A node's lists are the sorted union of its children's lists. This makes one rule for leaves and nodes, and
    T4's "includes `om`" holds at every level.

**R14. Medium (done). Leaf evidence when carried, and in T1 and T2 (spec.md:210, :215-218; §5).**
- Why: T1 builds every leaf as MEASURED, including Kisiwa's `om`, which is carried at TARGET and must be
  ESTIMATED (§5; structure-spec §3.1 rule 3). T2 builds plan targets as MEASURED, but a target is not a
  measurement. A leaf whose own label is stronger than the nodes above it is the inconsistency the rule forbids.
- Proposed answer:
  - Any leaf with `carried_as` TARGET or ASSUMPTION has evidence ESTIMATED, refused otherwise under R6's check.
  - T1 uses ESTIMATED for Kisiwa `om`, and T2 uses DECLARED for plan lines and ESTIMATED for the assumed ones.
  - A leaf with no value has evidence NOT_AVAILABLE (§3 does not say).

**R15. Medium. OPTION_ONLY neutral leaves weaken every cost label, and `wear_rate` blocks `contribution` for good
(§3, spec.md:161; D-3B3.2).**
- Why: `extra_l`, `collection_cost` and `battery_throughput_kwh` are DERIVED, and the weakest part wins, so
  `diesel_l`, `fuel_cost`, `cost_to_serve` and `contribution` can never read better than DERIVED, even when every
  real input is RECORDED. The neutral is an identity ("adds nothing to its parent", 3B1 carried item), not
  evidence.
  - Separately, `battery_wear = battery_throughput_kwh * wear_rate` with the neutral 0 and `wear_rate`
    NOT_CONNECTED has no value. So `cost_to_serve` and `contribution` stay unavailable until a `wear_rate`
    provider exists. No slice owns one: `ASSUMPTION_KEYS` has no wear key (`financials/assumptions.py:32`).
  - The pack's actual `battery_wear` is 0 at every Site.
- Proposed answer, Architect's call:
  - (a) Neutral leaves do not take part in the weakest-part rule.
  - (b) Keep strict evaluation (no short cut for `0 × unknown`), and name the slice that adds `wear_rate`, or
    rule that an OPTION_ONLY neutral 0 in a product makes the product 0 with the neutral's evidence.
  - Default: (a), plus strict evaluation, plus a named owner slice for `wear_rate`. Otherwise `contribution` is
    "not available" at every Site even after `3A4` and `4b`.

**R16. Medium. Money has no currency (§2.1 `FactorValue`).**
- Why: `select_window_price` returns a currency per Site and key (`financials/fuel_cost.py:440-463`). The
  productive price and the diesel price may be authored in different currencies, and Sites in a portfolio may
  differ. `revenue - cost_to_serve` and the portfolio sums would then mix currencies silently. Design §6.2 has a
  `currency` field, and `3B7a` must store it.
- Proposed answer:
  - `LeafValue` and `FactorValue` carry `currency: str | None` for money units.
  - A node over money children of two currencies has no value, with
    `Missing("CURRENCY_MISMATCH", ...)` or a `StructureError`.
  - `compose` refuses mixed currencies.

**R17. Low. Evidence order against the design (D-3B3.2).**
- Why: D-3B3.2 cites design §6.2, whose list is "Recorded | Measured | Derived | Estimated | Modelled | At stake
  | Verified | Not available". It has no DECLARED, and has two classes the spec drops. The snapshot vocabulary
  also has EXTERNAL (`chain/outcomes.py:31`).
- Proposed answer: keep the spec's order, record DECLARED as an addition to §6.2 in D-3B3.2, and have `evaluate`
  refuse a class outside the order (no silent rank). With R1 adopted, DECLARED is used only for site
  configuration values.

**R18. Low. P7 carried from 3B1: a bound or Protect list that names a node with no row.**
- Proposed answer: not applicable to 3B3, which reads no bound or Protect list. Carry it to `3B4` and step 6
  by name, so it is not lost.

**R19. Low. Are the stated causes true for four leaves? (§3 table, D-3B3.3.)**
- `major_assets` (asset register), `standby_kw` and `lost_unit_kw` (site configuration) and `field_visits` (work
  cases) are listed NOT_CONNECTED or HELD_NOT_CALCULATED. The Foundation holds asset components, and work cases
  exist (`work/service.py`), so the true cause may be NOT_CALCULATED_YET (held, not counted) rather than
  NOT_CONNECTED.
- Proposed answer: the Architect confirms each of the four rows. No leaf is filled here: the "major" class and the
  outage units are not declared fields, so filling them would be invented (D-3B3.4).
- On "could any more be filled exactly": `delivered_kwh` uses the same kW × interval integration of feeder
  readings that `productive_kwh` uses (`site_outcomes/productive_use.py:37-60`). The reason given for refusing it
  ("an hourly mean is not delivered kWh") also applies to `productive_kwh`, so the two rulings must agree (see R1).

## Implementer pre-flight questions

**P1. Medium (done). `_month_reading` cannot be reused as written (§3, spec.md:35, :168-169).**
- It is a private method of `OutcomeEvaluator` that takes a full `NodeInputs` (`chain/outcomes.py:108`). It
  hard-codes the `"kwh"` key (`:116`), so it cannot sum `critical_served`'s `unserved_kwh`. It also judges
  month-to-date from `inp.window[1]`.
- Rows come from `SnapshotReader.latest(tenant, site_id, lo, hi, [measure], known_at)` (`chain/reader.py:154`),
  so the read goes through SnapshotReader in any case.
- Proposed answer:
  - Extract a public pure `month_sum(rows, measure, lo, hi, key) -> (Decimal | None, GradeCounts)` in
    `chain/outcomes.py`. `_month_reading` calls it with `key="kwh"`, with no behaviour change, and the existing
    outcomes tests are the regression.
  - Allow `chain/outcomes.py` in §7.6.
  - Under R2, the leaf takes the sum only when coverage is full.
  - Alternative: a copy in `sources.py` with a parity test against `_month_reading`, which the spec ("reused
    and not copied") currently forbids.

**P2. Medium (done). The price port is pointed at the wrong function (spec.md:40, :170-173).**
- `AssumptionReadService.series` (`assumption_read.py:63`) returns views: `valid: {from, to}`, with prices
  nested. `select_window_price` needs the raw `timeline` and `cited` rows from `PostgresAssumptionStore.snapshot`.
- The reuse pattern already exists: `financials/composition.py:142-171` (`price_selection`,
  `build_productive_price_selection`, which passes `unit=unit_for(key)`).
- Proposed answer:
  - `ProductLeafSource(snapshot_reader, window_price)`, where
    `window_price(tenant, site, key, start, end, known_at) -> PriceSelection`.
  - It is built in `structure/composition.py` from `PostgresAssumptionStore.snapshot` and
    `fuel_cost.select_window_price(..., key=key, unit=unit_for(key))`.
- The spec's reason list is also incomplete, and one name is wrong: "CONFLICT" is `PRICE_CONFLICT`, and
  `PRICE_REVISION_MISSING`, `PRICE_UNIT_MISMATCH` and `PRICE_INVALID` also exist (`fuel_cost.py:440-463`).
  Proposed: any `UNPRICED` state is absent, and the reason goes into `sources` or a `reason` field for the
  screen.

**P3. Medium (done). The time basis of the price window and the Postgres fixture (§3, §6).**
- The month is Site-local, so for a UTC+3 Site the window is `[30 Sep 21:00Z, 31 Oct 21:00Z)`.
  `select_window_price` returns PRICE_SPANS_WINDOW unless one assignment covers the whole window
  (`fuel_cost.py:450-454`). A price authored from 1 Oct 00:00Z leaves the leaf empty for the month.
- The Postgres test's "diesel price revision" must therefore cover the whole Site-local month, or the test must
  expect the empty state. As written, a mid-month revision gives no value, not DECLARED.
- Proposed answer:
  - The window is `[local midnight of day 1, local midnight of day 1 of the next month)` converted to UTC.
  - The same `known_at` is the snapshot cutoff and the assumption `recorded_at`.
  - The fixture states its `valid_from`.
  - The Postgres test adds the mid-month revision case and expects the empty state.

**P4. Medium. Sites with no operating calendar (page × Site).**
- `config/chain/operating-calendar-v1.json:3` declares KOBO-001 only. For any other mini-grid Site, every day is
  NOT_EXPECTED or NO_DATA, `expected` may be 0, and a NOT_RECEIVED cause would be false.
- Also, a Site whose Foundation declares no PRODUCTIVE user has no `productive_kwh` subject, so no rows. For a
  ZERO_WHEN_HELD leaf whose source is held, the honest value may be a recorded 0.
- Proposed answer:
  - `expected == 0` gives no value, with NOT_CONNECTED (no reading role declared).
  - "No productive user declared" (from `productive_users`, which already separates it from "unavailable",
    `mini_depth/read.py:425-427`) gives a recorded 0 with its source named.
  - The Postgres test covers both.

**P5. Medium (done). Parse once and `FactorRow.children` (§2.4, spec.md:133-136).**
- `test_3b1_structure_registry.py:145-146` builds a free-standing row with `dataclasses.replace` and reads
  `.children`. A row that delegates to "the registry's cache" has no registry to delegate to, and would return the
  original row's children. `_replace` in the same test file (`:68-71`) builds new `Registry` objects whose cache
  must start empty.
- Proposed answer:
  - `Registry.parsed` and `Registry.parents` are `functools.cached_property`. This works on a frozen dataclass
    without slots and is per instance, so planted registries are fresh. They are built lazily per row, so a
    planted bad expression is still refused by `check`, not at attribute access (R14 of 3B1).
  - `FactorRow.children` stays self-contained, through a module-level `functools.lru_cache` over the expression
    text that calls `expressions.parse` by attribute, so T5's patch counts it. The T5 counting test clears that
    cache first.

**P6. Medium (done). `blocks`: does the source or the evaluator fill it? (§2.2 spec.md:111 against §3 :158-160.)**
- §3 has sources build `Missing(..., blocks, ...)`, and §2.2 says `blocks` "is computed here, never typed".
- Proposed answer: sources pass `blocks=()`. `evaluate` replaces it with the computed list
  (`dataclasses.replace`), and refuses a non-empty caller value (R6's check). T1 and T2 therefore never type
  `blocks`.

**P7. Low (done). L1, and the same class for `neutral` (§2.4, spec.md:127-140).**
- Today `_tolerance` uses `not tolerance.pct > 0` (`check.py:138`). A float 2.0 passes, `Decimal("Infinity")`
  passes, and `Decimal("NaN") > 0` raises `InvalidOperation`, so L1 is real.
- Sweep (W6): the new `neutral` field is the same class. It must be a finite `Decimal`. A float, NaN or Infinity
  gives `STRUCTURE_NEUTRAL`.
- State where `STRUCTURE_NEUTRAL` sits in `CODES`. Proposed: right after `STRUCTURE_LEAF_ABSENT`, since it reads
  `absent`. No 3B1 test pins `CODES`.

**P8. Low (done). §7.6's file list is too narrow for the spec it carries.**
- The edits needed are:
  - `backend/tests/test_3b1_structure_registry.py:88` (R9);
  - `chain/outcomes.py` (P1);
  - possibly `structure/__init__.py` (load order, if `evaluate` imports the registry).
- Proposed answer: list them.

**P9. Low. Test commands and module path (spec.md:20-25, :256-262).**
- Checked: with the spec's PYTHONPATH set to a worktree, `assetops_backend` and `assetops_contracts` resolve to
  the worktree, ahead of the `.venv` editable finders (those are appended to `sys.meta_path`).
- Two caveats:
  - `fixtures` becomes a namespace package that also takes in main's `host/fixtures`. Harmless for these tests,
    but say so in the packet line.
  - The first pytest command runs without `tools/heavy-slot.sh`, which RULES §7 refuses for heavy tools. Wrap
    it.
- `/opt/assetecon/AssetOpsV1-3b3` does not exist yet. That is fine: the Implementer creates it.

**P10. Low. Small contract points.**
- Two `SiteRef` classes exist (`chain/ports.py:16`, `site_outcomes/read.py:73`). Proposed: `chain.ports.SiteRef`.
- `ReadContext` repeats `tenant_id`, which `SiteRef` already carries. Proposed: assert that they are equal, or
  drop one.
- `portfolio()` should refuse duplicate Sites and Sites of another tenant.
- `-x` of 0 gives `Decimal("-0")`, which shows as "-0.00". Proposed: normalise -0 to 0 at the node.
- The pack's `note` on Kisiwa `om` ("O&M invoice for October not received; plan amount carried as ESTIMATED") has
  no field in `Missing`. Proposed: a `note: str | None` field, or the words go into `assumption`.
