# 3B3 rulings

Architect (Claude), 2026-11-20. Each ruling gives its reason. The index lines are in
`.ai/decisions/index-rulings-8.md`. Handshake answers go below, under "Handshake answers (round 1)".

## D-3B3.1 One pure evaluator, with sources behind a port

- **Ruling.** `evaluate` is pure. Leaf values come through `LeafSource`.
- **Why.** The same evaluator then serves the parity test against the pack, the product read, the snapshot (`3B7a`)
  and option evaluation (step 6). A later slice adds a leaf by adding a provider, not by editing the evaluator.

## D-3B3.2 Evidence order, and the weakest part wins

- **Ruling.** The order, strongest first, is: RECORDED, MEASURED, DECLARED, DERIVED, ESTIMATED, MODELLED,
  NOT_AVAILABLE. A node takes the weakest of its parts.
- **Why.** P3B rule 3 says the weakest part sets the label. The order follows the design's evidence classes
  (`integration-source-to-canonical-design.md` §6.2):
  - a declared price is weaker than a measurement;
  - an estimate is weaker than either;
  - a model is weaker still.

  *Emulated* and *Recorded* (D14) are provenance labels, which `3A5` shows beside the class. They are not ranks here.

## D-3B3.3 The source state of every leaf is a literal, and states the truth on 20 Nov

- **Ruling.** `SOURCE_STATE` names every leaf as PROVIDED, HELD_NOT_CALCULATED, NOT_CONNECTED or OPTION_ONLY.
- **Why.** The cause in `missing` must be true. Where records are held but the calculation is not built, the cause is
  NOT_CALCULATED_YET. Where no intake exists, it is NOT_CONNECTED. A literal keeps this auditable, and each later
  slice changes one row.

## D-3B3.4 Only exact sources fill a leaf; a partial source does not

- **Ruling.** Only five leaves are filled today. Dispatch minutes are not litres, a night-window fuel residual is not a
  monthly unexplained litre, and an hourly mean is not delivered kWh, so those leaves stay HELD_NOT_CALCULATED.
- **Why.** Unknown is never zero, and it is never something else either. Filling a leaf from a value of a different
  scope or unit would be an invented figure (owner rule: claim only what was tested).

## D-3B3.5 No route and no storage in 3B3

- **Ruling.** The read is a service only. `3B7a` adds the snapshot and the route.
- **Why.** The design serves screens from the snapshot, never from compute-on-read (OD-23). A route here would need a
  perf budget and a cache registration that `3B7a` replaces.

## D-3B3.6 Assumptions are carried and labelled; their value comes from 5a

- **Ruling.** The evaluator carries the label and makes the nodes above an assumption ESTIMATED. Which value an
  assumption takes is decided by `5a`, from target lines.
- **Why.** The owner's labelled-assumption default (20 Nov, item 6) needs the label to reach every figure it touches.
  The pack's fallback rule ("leaks and avoidable use at zero, the rest on the main factor") needs target lines, which
  only `5a` brings.

## D-3B3.7 Division by zero is missing, never infinite and never zero

- **Ruling.** As carried from the 3B1 review: the node has no value, and its `missing` names the zero denominator.
- **Why.** An infinite or zero figure would be a claim the records do not make.

## D-3B3.8 The portfolio excludes a Site by name and sums only additive factors

- **Ruling.** A Site with no contribution is excluded, and its reasons are listed. Amounts, quantities and counts are
  summed. Prices and ratios are not summed.
- **Why.** The design says "a Site that cannot be evaluated is excluded by name" and composes Σ amounts and Σ/Σ ratios.
  A summed price would be meaningless. A weighted price is attribution, which belongs to `5b`.

## D-3B3.9 The registry gains `neutral`, which makes MINI_GRID version 2

- **Ruling.** OPTION_ONLY rows carry the manifest's literal. The version is bumped.
- **Why.** A changed row field is a new version (the protected seam's rule). The neutral value is what the observed
  sides carry for an option-only factor (structure-specification §3.1).

## D-3B3.10 Months only, in the Site's calendar

- **Ruling.** The read takes a Site-local month (`YYYY-MM`). Day and range reads are `3B7a`'s.
- **Why.** The structure is declared per period. The bridge and the cards read months. A range read would duplicate
  the snapshot's job.

## Handshake answers (round 1)

Answered once, 2026-11-20, against `handshake.md` (R1 to R19, P1 to P10), and folded into `spec.md` rev 2 and
`reviewer-guide.md` rev 2. "Adopted" means the proposed answer is the ruling. Six new rulings (D-3B3.11 to
D-3B3.16) come out of the four Highs and R15/R16; D-3B3.4 and D-3B3.8 are amended below. The estimate moves from 3
to 4 units (the leaf-value checks, currency, the `composes` flag, `month_sum` and per-factor composition).

### The four Highs

- **R1: adopted for the two prices, overruled for `productive_kwh`** (D-3B3.11).
  - The class: a leaf is filled either by its own record (`filled_by`) or, where a person has declared a value of
    the **same quantity**, by that declaration carried as a labelled assumption. A measurement of a **different
    quantity** is neither, and fills nothing.
  - `productive_tariff` and `diesel_price` are the operator's declared values of the same price, and the product
    already calls them assumptions. They are carried with `Missing(filled_by.kind, filled_by.family,
    "NOT_CONNECTED", "ASSUMPTION", (), filled_by.words, <literal words>, note=None)`, evidence `ESTIMATED`,
    `sources = ("assumption:<revision id>",)`. Words: "Declared productive-use price per kWh, not a tariff
    schedule" and "Declared diesel price per litre, not a fuel invoice".
  - `productive_kwh` is metered energy at productive loads, not kWh charged at the productive tariff. It is a
    different quantity, and no one declared it as the billed value, so it is not an assumption. It moves to
    NOT_CONNECTED (its own record, CHARGE, has no intake). Its metered figure stays on the existing board.
  - When a source is absent, the leaf carries `filled_by`'s record with the true cause, never a second record kind.
  - The new state is `ASSUMED` (§3). Today: 2 leaves on their own record (`period_days`, `unserved_critical_kwh`),
    2 labelled assumptions, 0 substitutes.
  - Sweep (W6): every later provider is checked against `filled_by` by the same test; the reviewer guide carries it.
- **R2: adopted** (D-3B3.12). A summed reading leaf has a value only when the month has closed in the Site's
  calendar and every expected day is COMPLETE (`expected > 0` and `covered == expected`). Otherwise no value,
  `Missing(filled_by..., "NOT_RECEIVED", None, ...)`, with the coverage kept so the screen can say "28 of 31 days".
  A month not yet closed is read the same way. Month-to-date figures stay with the board and `3B7a`.
  The lower-bound alternative is refused: it needs a label the design does not have, and it reads as the month.
- **R3: adopted, with the open question ruled per factor, not per Site** (D-3B3.13, which replaces D-3B3.8's
  first sentence). Pushback on the reviewer's default ("keep per Site"):
  - Per Site keys exclusion on `contribution`, which has no value at any Site today. Every portfolio figure,
    including Protect figures that never rest on money (`unserved_critical_kwh`), would vanish for a reason that
    does not touch them. That hides known values, which is the mirror of reading unknown as zero.
  - The design's rule is "a Site that cannot be evaluated is excluded by name". Per factor applies it at the
    grain the evaluator already works at: the Site cannot be evaluated *for that factor*.
  - Ruling: for each composed factor, the Sites with a value are `included`, the others are `excluded` by name
    with their `missing_leaves`. The value is the sum over `included`. With no Site included, the value is None
    (never 0), and `missing_leaves` is the union prefixed `SITE:leaf`.
  - The cost of per factor is that two portfolio factors may rest on different Site sets, so portfolio
    `revenue - cost_to_serve` need not equal portfolio `contribution`. Every composed value therefore carries its
    `included` and `excluded`, and `3B5` must show "k of n Sites" whenever `excluded` is non-empty (carried to
    `3B5`'s spec as a done criterion). The owner may want to weigh in on this display (decision queue).
  - A Site whose type has no structure is excluded whole, in `Composition.sites_excluded`, with
    `("STRUCTURE_NOT_DECLARED",)`.
- **R4: adopted, as a row flag** (D-3B3.14). `FactorRow` gains `composes: str` (`SUM` or `NONE`; dataclass default
  `NONE`, which fails closed: a forgotten row gives no total, never a wrong one). `_leaf` and `_node` take it as a
  required keyword, so every MINI_GRID row states it. The start-up check `STRUCTURE_COMPOSES` refuses a value
  outside the two, and `SUM` on a unit with a denominator. MINI_GRID `SUM`: the reviewer's list. `NONE`: the four
  prices and rates, `hours_per_day`, `standby_kw`, `lost_unit_kw`, `shortfall_backed`, `period_days`. A row flag
  over a module frozenset because `3B6` then declares its own rows the same way. T3 keeps its own copy (W2).

### The rest

- **R5: adopted.** "Every node in `blocks(om)` has no value, and no node with a value rests on `om`", in T4 and P1.
- **R6: adopted, widened** (closes D-3B1.6's first item). `evaluate` checks every input `LeafValue` and raises
  `StructureError(code, key, leaf)`:
  - `STRUCTURE_MISSING`: value None and `missing` None; value present with `missing` whose `carried_as` is None;
    value None with `carried_as` set; a non-empty `missing.blocks` (P6).
  - `STRUCTURE_EVIDENCE`: a class outside the order (R17); `carried_as` TARGET or ASSUMPTION without `ESTIMATED`
    (R14); value None without `NOT_AVAILABLE` (R14); `NEUTRAL` on a row that is not OPTION_ONLY or with a value
    other than `row.neutral` (R15).
  - `STRUCTURE_CURRENCY`: a money-dimension leaf with a value and no currency, except a `NEUTRAL` leaf (R16).
  - These are runtime codes, not in `check.CODES`. T5 plants each case.
- **R7: adopted.** Share is `Fraction(covered, expected)`; `expected == 0` is share 0. A node keeps the minimum
  child's whole `Coverage`; on a tie, the first child in `names()` order. Portfolio coverage per factor is the sum
  of `covered`, `expected` and `grades` over `included`. Subject-level exclusions stay `3B7a`'s.
- **R8: adopted.** `Composition.not_composed: tuple[str, ...]` lists the `NONE` factors; they are not in `values`.
- **R9: adopted.** Replaced in place (nothing stores a v1 value; D-3B3.9 amended). `SiteStructure` and
  `PortfolioStructure` carry `structure_key` and `structure_version`. The edit of
  `test_3b1_structure_registry.py:88` to `version == 2` is allowed.
- **R10: adopted.** A literal map `SITE_TYPE_TO_STRUCTURE = {"MINIGRID": "MINI_GRID"}` in `read.py`; any other
  type is excluded whole. `compose(registry, per_site)` raises `StructureError("STRUCTURE_COMPOSE", key, site)`
  for a Site evaluated under another key or version. Cross-vertical totals are `3B6`'s.
- **R11: adopted, second option.** `evaluate.py` exports `blocks_of(registry, leaves) -> tuple[str, ...]` (the
  pack's breadth-first walk from the whole group); T2 calls it per plan-side group. T1 compares `blocks` only for
  entries that carry a `leaf` (Kisiwa `om` on the actual side); `right` and `stage` entries are not leaves.
- **R12: adopted.** T1 and T2 assert each pack leaf equals itself quantised to 0.01, naming the leaf if not.
- **R13: adopted.**
- **R14: adopted.** Plan lines in T2 are `DECLARED`; assumed and carried leaves `ESTIMATED`; no-value leaves
  `NOT_AVAILABLE`. Enforced by R6's `STRUCTURE_EVIDENCE`.
- **R15: ruled (D-3B3.15), not the default.** An OPTION_ONLY leaf carries evidence `NEUTRAL`, a class outside the
  order that the weakest-part fold skips (it is an identity, not evidence). In a product, a `NEUTRAL` 0 operand
  makes the product 0 with evidence `NEUTRAL`, whatever the other operand: an option that adds no throughput adds
  no wear at any rate, which is the 3B1 carried meaning of the neutral ("adds nothing to its parent"). Everything
  else stays strict (`0 x unknown` from any other source is unknown). So `battery_wear` is 0 today and does not
  block `contribution`; `wear_rate` stays NOT_CONNECTED and is carried to step 6 (option evaluation), where a
  non-zero throughput needs it.
- **R16: adopted** (D-3B3.16). `LeafValue` and `FactorValue` carry `currency: str | None`. A node's currency is the
  one non-None currency among its children; two different ones give no value with
  `Missing("CURRENCY_MISMATCH:<a>,<b>", "OBSERVER", "NOT_CALCULATED_YET", None, blocks, None, None)`, the same
  node-level pattern as `ZERO_DENOMINATOR`. `compose` does the same per factor across included Sites. No
  conversion anywhere.
- **R17: adopted.** D-3B3.2 records DECLARED as an addition to the design's §6.2 list, and `NEUTRAL` (R15) as a
  non-ranked class. `AT_STAKE` and `VERIFIED` are not produced by an evaluation; `EXTERNAL` is not a leaf class here.
- **R18: adopted.** Carried to `3B4` and step 6 by name.
- **R19: confirmed.** `major_assets`, `standby_kw`, `lost_unit_kw`: NOT_CONNECTED (the "major" class and outage
  units are not declared fields; the held components are not that record). `field_visits` is already
  HELD_NOT_CALCULATED. `delivered_kwh` stays HELD_NOT_CALCULATED because no monthly measure over feeder readings is
  built, not because integration is invalid; D-3B3.4's reason is corrected, so it agrees with R1.
- **P1: adopted.** Public pure `month_sum(rows, lo, hi, key) -> tuple[Decimal | None, GradeCounts]` in
  `chain/outcomes.py`; `_month_reading` calls it with `key="kwh"`, unchanged behaviour. `chain/outcomes.py` is
  added to the file list.
- **P2: adopted.** `ProductLeafSource(snapshot_reader, window_price)`, built in `structure/composition.py` from
  `PostgresAssumptionStore.snapshot` and `fuel_cost.select_window_price(..., key=key, unit=unit_for(key))`, as in
  `financials/composition.py:142-171`. Any state other than PRICED is absent; the reason (`NO_PRICE`,
  `PRICE_CONFLICT`, `PRICE_SPANS_WINDOW`, `PRICE_REVISION_MISSING`, `PRICE_UNIT_MISMATCH`, `PRICE_INVALID`) goes in
  `Missing.note`.
- **P3: adopted.**
- **P4: adopted in part.** `expected == 0` gives no value with NOT_CONNECTED (no reading role declared). No recorded
  0 is inferred from "no subject declared": that would be a claim about the Foundation's completeness. Moot for
  `productive_kwh` after R1; the Postgres test covers a non-Kobo Site.
- **P5: adopted.**
- **P6: adopted.**
- **P7: adopted.** `STRUCTURE_NEUTRAL` sits after `STRUCTURE_LEAF_ABSENT`; `STRUCTURE_COMPOSES` after
  `STRUCTURE_UNIT`.
- **P8: adopted.**
- **P9: adopted.** The first pytest command runs under `tools/heavy-slot.sh --`; the packet notes the `fixtures`
  namespace package.
- **P10: adopted.** `chain.ports.SiteRef`; `ReadContext(site, month, known_at)` with the tenant read from `site`;
  `portfolio()` raises `StructureError("STRUCTURE_COMPOSE", ...)` on a duplicate Site or another tenant's Site; a
  zero node value is normalised with `copy_abs()`; `Missing` gains `note: str | None` (the pack's Kisiwa `om` words,
  and P2's price reason).

### New rulings

## D-3B3.11 A leaf rests on its own record or on a declared value of the same quantity, labelled

- **Ruling.** States are PROVIDED (own record), ASSUMED (a person's declared value of the same quantity, carried as
  ASSUMPTION, ESTIMATED, with literal words), HELD_NOT_CALCULATED, NOT_CONNECTED, OPTION_ONLY. A measurement of a
  different quantity fills nothing.
- **Why.** P3B: unknown is never zero and the weakest part sets the label; a declared price is the operator's
  assumption (`AUTHORITY["DECLARED"] = False`), and a delivered kWh is not a billed kWh.

## D-3B3.12 A summed reading leaf needs a closed, fully covered month

- **Ruling.** No value unless the month has closed and every expected day is COMPLETE; coverage is kept.
- **Why.** A sum over fewer days is a lower bound shown as the month: unknown days read as zero (design §6.7).

## D-3B3.13 The portfolio excludes Sites per factor, by name

- **Ruling.** Each composed factor sums its Sites with a value and names the others; none included gives no value.
- **Why.** Exclusion keyed on `contribution` would hide every known Protect figure today; per factor is the
  design's rule at the evaluator's grain. The value carries its Site sets so the screen says "k of n Sites".

## D-3B3.14 What is summed is a declared row flag

- **Ruling.** `FactorRow.composes` is `SUM` or `NONE` (default `NONE`), checked at start-up.
- **Why.** A unit rule cannot tell a 0/1 ratio from a count, or a period from a quantity; a declared flag can, and
  `3B6` reuses it.

## D-3B3.15 An option-only neutral is an identity, not evidence

- **Ruling.** Evidence `NEUTRAL`, skipped by the weakest-part fold; a `NEUTRAL` 0 operand makes a product 0.
- **Why.** The neutral says the option adds nothing; ranking it would weaken every cost label for no record, and
  strictness on it would block `contribution` on a rate the zero does not depend on.

## D-3B3.16 Money carries its currency; mixed currencies give no value

- **Ruling.** `currency` on leaf and factor values; a mismatch is a node-level missing; no conversion.
- **Why.** Prices are authored per Site and key with a currency; summing two silently would be an invented figure.

### Amended

- **D-3B3.4**: "an hourly mean is not delivered kWh" is replaced by "no monthly measure over feeder readings is built
  yet"; filled leaves are as D-3B3.11.
- **D-3B3.8**: the first sentence ("a Site with no contribution is excluded") is replaced by D-3B3.13; what is
  summed is D-3B3.14.
- **D-3B3.9**: in place, because no stored consumer of version 1 exists; outputs carry key and version.

### Decision queue (W3)

- **Per-factor "k of n Sites" display** (D-3B3.13). Default: shown beside every portfolio figure with a non-empty
  `excluded`. Owner view welcome before `3B5`.
- **Who supplies `wear_rate`.** Default: step 6, when an option first adds throughput.

## Mid-build answers (round 1)

Architect (Claude), 2026-11-20, against `mid-build-questions.md` Q1-Q4 and the packet's "Deviations", test and
"Not verified" sections (head `ae641e63b`). One new ruling (D-3B3.17); P1, P2, D-3B3.12 and D-3B3.13 are amended.
The estimate stays at 4 units.

### Q1. `month_sum` takes `measure`: the five-argument form is the ruling (P1 amended)

- **Ruling.** `month_sum(rows, measure, lo, hi, key)`. P1's four-argument text was a transcription slip: the
  handshake's proposed answer, which "adopted" made the ruling, has `measure`, and without it an empty month counts
  every day NOT_EXPECTED, which would change `_month_reading` and turn the leaf's NOT_RECEIVED into NOT_CONNECTED.
- **Code change.** None beyond Q2's return value. P1 now reads: `month_sum(rows, measure, lo, hi, key) ->
  tuple[Decimal | None, GradeCounts, tuple[date, ...]]` (the third element is Q2's).

### Q2. Yes: an analysed day with no value is being read as zero. It is unknown (D-3B3.17, D-3B3.12 amended)

- **Finding.** `month_sum` counts a COMPLETE day whose row has `value = None` or no `key`, and sums the other days.
  A closed month with all days COMPLETE then has a value that silently treats that day as 0. That breaks
  "unknown is never zero" (design §6.7) and D-3B3.12, whose "every expected day is COMPLETE" was meant as "every
  expected day has a measured value".
- **Ruling (D-3B3.17).** A counted day that does not state the summed key is unknown. The fact lives in `month_sum`
  (the one place that knows which days were counted); the decision lives in the leaf.
- **Code change.**
  1. `month_sum` returns a third element `unstated: tuple[date, ...]`: the counted days (COMPLETE or PARTIAL,
     in `counted`) on which no counted row has `value[key]` not None, ascending. Value and `GradeCounts` are
     unchanged.
  2. `_month_reading` takes `value, days, _ = month_sum(...)`: board behaviour unchanged (P1 stays
     behaviour-neutral).
  3. `_unserved_critical`: `Coverage.covered` = `days.complete` minus the COMPLETE days in `unstated`; the grades
     map is unchanged. The value rule becomes "closed, `expected > 0`, `covered == expected`". When `unstated` is
     non-empty and the month otherwise qualifies, `Missing(..., "NOT_RECEIVED", ..., note=f"VALUE_NOT_STATED:{n}")`.
     The screen then reads "30 of 31 days", never the 31-day figure.
  4. Plants in T4: a closed month, every day COMPLETE, one row with `value=None`; the same with `value={}`. Each
     must give no value, NOT_RECEIVED, covered = expected - 1 and the note. A third plant: `unstated` lists the
     day for a PARTIAL day too.
- **Sweep (W6), not in 3B3.** The same class sits in `chain/outcomes.py` `_month_reading` (the board's
  month-to-date sum counts an unstated day as checked) and `energy_basis` (line 283, `kwh` skips an unstated
  counted row). Both are board behaviour, so 3B3 does not touch them; they go to the decision queue below.

### Q3. "Closed" against the wall clock when `known_at` is None: confirmed

- **Ruling.** The seam is the injected `now` on `ProductLeafSource`, as built; `known_at` wins whenever given.
  `3B7a` always passes `known_at` (its snapshot cutoff), so the wall clock decides only a live, unstored read and
  never a stored figure. A month is closed when its window end (Site-local midnight of the next month, as UTC) is
  at or before that instant.
- **Code change.** None. If not already planted, add one T4 case with `known_at=None` and `now` one second before
  the window end (no value, NOT_RECEIVED) and at the window end (value).

### Q4. "n" is every Site the portfolio was asked for (D-3B3.13 amended)

- **Ruling.** n = `PortfolioStructure.sites`; k = the factor's `included`. Named out = the factor's `excluded`
  plus `Composition.sites_excluded`. A Site with no declared structure is part of the owner's portfolio, so "2 of 2
  sites" when the user has 3 would hide one, against the owner's "k of n sites" (owner file
  `owner-k-of-n-sites-2026-11-20.md`: "$6,200 · 2 of 3 sites (Kisiwa not available yet)").
- **Code change.** So `3B5` designs nothing, add to `read.py` a pure
  `site_count(portfolio: PortfolioStructure, factor_id: str) -> SiteCount | None`, with frozen
  `SiteCount(k: int, n: int, out: tuple[tuple[str, tuple[str, ...]], ...])`. `out` is `(site_code, reasons)` in
  `portfolio.sites` order, reasons from `excluded` or `NOT_DECLARED`. A factor in `not_composed` gives None. Test:
  for every composed factor `k + len(out) == n`; a cold-room Site is counted in n and named out with
  `STRUCTURE_NOT_DECLARED`. `3B5` shows "k of n" whenever `out` is non-empty; its screen words for each reason are
  `3B5`'s.

### The deviation: prices through the existing builders. A workaround; the right wiring is one builder (P2 amended)

- **Finding.** The guard is right: only `financials/composition.py` may build the assumption adapter. But the
  workaround builds two `PostgresAssumptionStore`s and an unused `PostgresTrialComparisonStore`, and `dispose()`
  releases only the trial store, so both assumption-store engines leak. It is a workaround, and it stays out of
  the merge.
- **Ruling.** P2's form, at the seam the guard allows. `financials/composition.py` gains
  `build_window_price_selection(database_url) -> WindowPriceSelection`, a frozen dataclass with
  `select(tenant_id, site_id, key, start, end, known_at) -> PriceSelection` and `dispose() -> None`. It holds one
  `PostgresAssumptionStore`. `select` is `prices.snapshot(tenant_id, site_id, key, known_at, 0, 1)` then
  `fuel_cost.select_window_price(timeline, cited, start, end, key=key, unit=unit_for(key))`. `dispose` disposes
  that store. The two existing builders are not changed (their callers are other slices').
- **Code change.** `structure/composition.py` uses `build_window_price_selection` as `window_price` and its
  `dispose` alongside `snapshots.dispose()`; `build_trial_comparison_ports` and `build_productive_price_selection`
  are no longer imported there. Tests: for the diesel key, `select` equals `build_trial_comparison_ports(...)
  .price_selection` on the same rows (PG test), and `dispose()` disposes every engine built (a fake-store unit
  test counting the dispose calls). The packet's "Deviations" line is removed.

### TEMPLATE_STALE: rebuild by the coordinator, after checking what the prune would drop

- **Finding.** The fingerprint covers `chain/outcomes.py` (and, after the deviation fix, may cover
  `financials/composition.py`), so 3B3 needs its own template. `publish_template` keeps the two newest
  per-fingerprint templates (`TEMPLATES_KEPT = 2`), but there are two lanes plus main, so one build can drop
  another live checkout's template. The builder was right not to build.
- **Ruling.** The builder does not touch databases. After the code changes above, the coordinator, with the
  machine quiet:
  1. Runs `python tools/mechanism_dataset.py status` from main and from each active lane's worktree, and notes
     each live checkout's template.
  2. Builds in `/opt/assetecon/AssetOpsV1-3b3` (`python tools/mechanism_dataset.py ensure`) only if the prune would
     drop no live checkout's template. That holds when at most one other per-fingerprint template is live.
     Otherwise it waits until the other lane merges or no longer needs its template.
  3. Runs the 11 errored tests, then puts the result in the packet.
- **Before merge, not before review.** The 11 must pass before merge. The review may start with them listed under
  "Not verified".
- **Class fix (decision queue).** `TEMPLATES_KEPT` = lanes + 1 (3 today), as its own tooling task on its own
  branch. 3B3 does not take it: `mechanism_dataset.py` changes would also require the close template.

### The 32 failing test files: no action before review, with one condition

- **Ruling.** A failure that is identical at base `bf72c735d` is not 3B3's. The condition: the packet must name
  the evidence file listing the 32 files with their branch and base results side by side, plus the 3 that failed
  only on the branch's full run and pass alone (flakes). The reviewer reruns those 3 alone. The host-run (not
  Docker) cause is environmental. It is carried to the full-suite run at the next milestone (owner test-suite
  policy, 2026-11-19), not fixed in 3B3.
- **Code change.** None; packet only.

## D-3B3.17 A counted day that does not state the summed value is unknown, not zero

- **Ruling.** `month_sum` reports the counted days with no value for the key; a leaf's coverage does not count
  them, so the month has no value.
- **Why.** An analysed day with no value is a day we do not know. Summing around it reads it as 0 and shows a
  lower bound as the month (design §6.7, D-3B3.12).

### Amended (round 1)

- **P1**: the five-argument form, with the `unstated` return (Q1, Q2).
- **P2**: the prices come through `financials.composition.build_window_price_selection`, one store, disposed.
- **D-3B3.12**: "every expected day is COMPLETE" means every expected day is COMPLETE and states the value
  (D-3B3.17).
- **D-3B3.13**: n is every Site asked for; `site_count` gives k, n and the Sites named out.

### Decision queue (W3), round 1

- **The board's unstated days** (`_month_reading`, `energy_basis`). Default: a small separate task after 3B3
  merges, using `month_sum`'s `unstated`. A board day that states no kWh is not counted as checked and is named.
  It changes board captures, so it is its own slice.
- **`TEMPLATES_KEPT` = lanes + 1.** Default: 3, as its own tooling task before the next lane touches a traced
  input writer.
