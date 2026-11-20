# 5b handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md`, `rulings.md` and P5
(`specs/5a-targets/structure-page-P5.md`), and the Implementer, after a pre-flight of `spec.md` against `main`, write
their questions here in one batch. Number them R1, R2 ... and I1, I2 .... Each question cites the spec section, says
what is unclear and what answer the writer expects, and is marked **(done)** when its answer changes what counts as
done. The Architect answers every question once, in `rulings.md` under "Handshake answers (round 1)", and folds the
answers into `spec.md`. The handshake ends when neither section has an open question; coding starts only then.

## Reviewer questions

Reviewer (Claude, fresh; handshake round 1, 2026-11-20), against `main` at `11a5e2a06`. **High** blocks the start of
coding. Hand figures recomputed, all agree with the spec: §5.1 revenue +38.00 (billed 95 × 0.40; metered 140 × 0.40 =
+56.00 = +220.00 − 164.00; adjustments −18.00), fuel −600.00 = diesel_l 480 × −1.25 (necessary −37.50, candidate
−412.50, unexplained −150.00) + price 0; root −562.00; `by_home` 220.00 / −782.00; cash −240.00 = +38.00 − 278.00;
AT-3 −659.00 = −600.00 − 59.00 (plants V1/V2 give 35.00 and 624.00). §5.2 Kobo 883.00 − 1445.00 = −562.00;
Kisiwa −250.00 − (−65.00) = −185.00 (revenue −55.00, fuel −130.00, om carried 0.00); Mto 810.00 − 915.00 = −105.00
(−80.00, −25.00); portfolio 1443.00 / 2295.00 / −852.00, revenue 9688.00 / 9785.00, cost to serve 8245.00 / 7490.00,
fuel 4995.00 / 4240.00, om 1800.00, staff 1450.00, `by_home` −97.00 / −755.00; cash 8870.00 / 9785.00 / −915.00 =
−97.00 − 150.00 − 668.00; without the step 633.00 / 1380.00 / −747.00, 2 of 3 (V9's −1662.00 = 633.00 − 2295.00).
The pack (`derived-values.json`) agrees on every node value.

- **R1 (High, done).** §4.1 `PortfolioRow`: `actual`, `target` and `gap` are summed across Sites for every key,
  including PRICE rows (`tariff`, `productive_tariff`, `diesel_price`, all `composes == "NONE"`). A portfolio
  "diesel price" of 3.80 (1.25 + 1.30 + 1.25) is a false figure, and D-3B3.14 says `NONE` fails closed (no total).
  The pack itself sums prices (`portfolio.lakeside-power.plan.sums.diesel_price` 3.8, `tariff` 1.35), so the pack
  comparison would bless it, and no test reaches a PRICE row at portfolio level (Lakeside stops at the headings), so
  no plant can fail. Expected: for a row whose factor's `composes != "SUM"`, `actual`, `target` and `gap` are None
  (only `effect` is summed, which is money on the root); a test with two §5.1 Site bridges asserting the portfolio
  `diesel_price` row has `effect` summed and `actual`/`target`/`gap` None; a plant that sums them.
- **R2 (High, done).** Two different "actual contribution" figures for the same month. `SiteBridge.actual` evaluates
  the *carried* inputs (Kisiwa −250.00, portfolio 1443.00, 3 of 3), while 3B3's `StructureRead.portfolio` and 3B7a's
  `PortfolioMonthSnapshot.actual()` (3B7a spec §5: 883.00, 1 of 3) do not carry. Beside them, 5a's composed target is
  2295.00 over 3 Sites, while without Mto the bridge's own target is 1380.00 over 2. If `5c` shows the composed
  actual or target next to the bridge's gap, the screen subtracts one set from another, which D-5B.9 and the owner's
  "k of n sites" forbid. D-5B.10 does not cover it. Expected: a ruling that the figures shown beside a gap are the
  bridge's own row sums (`PortfolioRow.actual/target`, with k of n), that the uncarried composed actual is never shown
  on the bridge, and that `5c`'s spec inherits this (add to D-5B.10).
- **R3 (Medium, done).** The seam: see 3B7a handshake R1. The guide's "byte-identical to 3B7a's text" cannot be
  checked; expected "5b's branch has no diff in `structure/read.py`" once the seam is merged alone first.
- **R4 (Medium, done).** §4.2 `BridgeRead.site`/`.portfolio` with `known_at=None` read the actual twice (once inside
  `TargetRead.site` for its `AT_ACTUAL` targets, once in `site_inputs`) at two moments, and 3A4's "month closed" is
  taken from the months' clock each time. A record arriving between them gives an `AT_ACTUAL` target from one state
  and the actual from another, i.e. a false gap on a leaf whose target is "taken at this month's actual". D-3B7A.2
  solves this for the snapshot; the fresh path does not. Expected: `BridgeRead` takes a clock and pins
  `known_at = known_at or clock()` once per call, passed to every read; a test with a recording reader.
- **R5 (Medium, done).** §2.3 step 4 compares `computed != value` exactly, but 5a's `solve_main` divides at 34 digits:
  a fuel target of 875.00 at 1.27 per litre gives `computed` 874.9999999999999999999999999999999 (checked in Python
  under 5a's context), so the *target* side reports `RECORD_AND_FACTORS_DIFFER` for a rounding artefact of the solve
  and the heading never splits once `4d` lands litres. Lakeside's prices (1.25, 1.30, 0.40) happen to be exact.
  Expected: step 4 ignores a side whose value was solved (`assumed_leaves` contains its `MAIN_OF` leaf), or the
  comparison is made at the record's own exponent; a test at 1.27.
- **R6 (Medium, done).** Test 10 forbids any `commercial` import under `structure/attribution/`, but §4.2's
  `build_bridge_read` calls `build_commercial_reads` (and the reviewer-guide probe repeats the rule). Expected: exempt
  `composition.py`, or build through `structure.targets.composition.build_target_read` plus `build_structure_read`.
- **R7 (Medium).** §4.1 `PortfolioRow` has no carried marker: the portfolio `om` row reads 1800.00 against 1800.00,
  ESTIMATED, 3 of 3, with nothing saying that Kisiwa's 700.00 is its budget line and its gap 0.00 by construction.
  P5 asks that the estimate name the missing record. Expected: `carried: tuple[str, ...]` (Site codes, `asked`
  order) on `PortfolioRow`, asserted in test 7 as `("KISIWA-001",)` on `om`, `cost_to_serve` and `contribution`.
- **R8 (Medium, done).** Reviewer-guide V13's second half ("a residual on a node that is not stated") cannot fail:
  a non-stated node with a value always has every non-neutral term computable (the only short cut is the neutral
  zero), so the code path is unreachable. Expected: drop that half, or plant it through `_toy` with a stated-False
  node and a hand-built `FactorValue` map.
- **R9 (Low).** §5.2's table gives Kisiwa and Mto revenue and fuel as `NOT_SPLIT` with no reason, yet test 6 checks
  "every named field". Expected: `DETAIL_NOT_AVAILABLE` and their `unobserved_actual`/`unobserved_target` written out
  as literals, as for Kobo.
- **R10 (Low).** Test 3(a) says the RESIDUAL's `unobserved_actual` "is the actual's `detail_missing`" (the code's own
  output, W2). Expected: the literal `("delivered_kwh",)`.
- **R11 (Low).** §4.1 keys rows by factor id: a factor appearing twice in one root's tree would merge two rows. None
  does in MINI_GRID today. Expected: `portfolio_bridge` raises on a repeated key within one Site's tree (one line, one
  assertion).
- **R12 (Low).** §2.3 step 6 calls `unobserved_*` "leaves", but `missing_leaves` holds stated nodes too (4b's
  `MTO_MISSING` includes `fuel_cost` and `revenue`), so `out` reads `actual:fuel_cost`. Expected: confirm that is
  intended (the record that would fill it), and say so in the field comment.
- **R13 (Low).** Tests 6 and 7 "compare to the cent" with the pack: the pack keys Sites by name (`Kobo`), holds JSON
  floats and has no effects. Expected: name the compared fields (node `actual`/`plan` values, root gap from
  `history`), the name-to-code map, and `Decimal(str(x))` at two places.


## Implementer pre-flight questions

Implementer pre-flight (same agent, implementer hat), every citation checked against `main` at `11a5e2a06`.

- **P1 (confirmed).** `weakest`, `weakest_origin`, `ORIGIN_ORDER`, `blocks_of`, `compose`, `evaluate`,
  `CARRIED_AS` (`TARGET`) are in `structure/evaluate.py`; `Bin`/`Neg`/`Ref`/`Num`/`Call` in
  `structure/expressions.py`; `REGISTRIES`, `Registry.parsed`, `FactorRow.home.category`, `HOMES` (`ABOVE`,
  `CALENDAR`) in `structure/registry.py`; `CATEGORIES == ("GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET",
  "ASSURE_PERFORMANCE")` in `outcomes/catalogue.py`; `Unit.exponents` (sorted, zeros dropped) and `Unit.is_money`
  (`== (("MONEY", 1),)`) in `contracts/.../canonical/units.py`, so "has `("MONEY", 1)` and is not money" picks
  `tariff`, `productive_tariff`, `diesel_price`, `wear_rate`. Every money-tree node is a signed sum or `Ref × Ref`
  with the price second, so only test 3(d) discriminates V3.
- **P2 (carry is reachable).** Kisiwa's `om`: EXPENSE held, month closed at `READ_AT`, no OM line, `zero_when_held`
  False, so `money.py` `_judge` returns `NOT_RECEIVED` with note None and words "Service contractor invoice". Its
  target is a DECLARED `budget:` line (`targets_lakeside.json` step 1, 700.00). The carried leaf passes
  `_check_leaf` (value with `carried_as` TARGET, ESTIMATED, `blocks == ()`, USD, ordered origins) and lands in
  `assumed_leaves`. Note 5a's rule for `om`/`staff` with no line is `AT_ACTUAL`, so `NO_TARGET_LINE` is the only
  outcome there.
- **P3 (test references).** `test_4b_money_leaves.py:77-140` (steps, `ingest`, `fallback`, `reader`, `site`) and
  `MTO_MISSING` (line 67, thirteen ids incl. two nodes); `test_5a_targets.py:36-60` (`steps`, `ingest`, `load`,
  `lakeside`) and `_toy` at 595 (rows `x`, `p`, `y`, home None, so `by_home` is `UNPLACED`). Test 3(e) needs a `z`
  row, so it builds its own registry next to `_toy`. `new_world()` is `test_3a4_commercial_months.py:78`.
- **P4 (fixture).** The new step reuses `KISIWA-*` shapes; `mto-billing` is a new `source_system` (4b used
  `kobo-vending`, `kisiwa-billing`), and both batches share one `at`. I will confirm on the first run that 3A1 accepts
  both (no source-system registry, two intakes at one instant) and report it in the packet. Mto's price is
  400.00 ÷ 320 = 1.25 exactly; productive_kwh is 0 (STANDARD class, held).
- **P5 (no collision).** No migration. ON1's branch touches no file under `structure/`; nothing else in flight edits
  `structure/read.py`. The seam follows 3B7a R1's answer.
- **P6 (pack).** `Docs/demo-sprint/product-direction-layer4/derived-values.json` exists with
  `sites["lakeside-power/<Name>"].{plan,actual}.nodes` and `portfolio["lakeside-power"].{plan,actual}.sums`;
  every §5.2 node value matches (revenue, collected, in transit, outstanding, fuel, O&M, staff, cost to serve,
  contribution; Sites and portfolio, both sides). The comparison waits on R13.
