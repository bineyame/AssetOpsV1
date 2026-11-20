# 5b rulings

Architect (Claude), 2026-11-20. Each ruling gives its reason. Index lines: `.ai/decisions/index-rulings-11.md`.
Handshake answers go below, under "Handshake answers (round 1)".

## D-5B.1 The gap is actual minus target, both valued, in one currency; a budget contribution line is never the target

- **Ruling.** A row's gap is `actual − target` only when both sides have a value and the money currencies agree;
  otherwise it has no gap (`GAP_NOT_AVAILABLE` or `CURRENCY_MISMATCH:`), never 0. The target is 5a's evaluated value;
  5a's `TargetCheck`s pass through untouched (`SiteBridge.targets.checks`, `PortfolioBridge.disagreements`).
- **Why.** P5 rules 2 and 4: a contribution line that disagrees is "shown, never hidden or used instead"; unknown is
  never zero. Kisiwa's −60.00 against −65.00 stays visible for `5c`.

## D-5B.2 Two split rules: exact sums (AR1) and volume-then-price products (AR2)

- **Ruling.** A node splits only when its expression is a signed sum of factors or of two-factor products. A sum
  splits into its terms with their signs. A product `Q × P` splits into a volume effect at target price `(Qa − Qt) ×
  Pt` and then a price effect at actual volume `(Pa − Pt) × Qa`; the price is the factor whose unit is money per unit,
  never chosen by position. Any other shape is not split (`RULE_NOT_DECLARED`; `PRICE_NOT_DECLARED`).
- **Why.** P5 rule 8 and `economic-metric-and-effect-contracts.md` §4.2 (AR1, AR2, decision A13): exact by
  construction, no cross term, the finance convention, and the order declared so it never changes silently (AT-3).
  Every MINI_GRID node is one of these shapes; AR3 to AR5 are not needed by any node yet.

## D-5B.3 Effects are pushed down by a scale, so a quantity's parts get money at target price

- **Ruling.** Each row carries `scale`, the money on the root per unit of its gap: the root 1; a sum's term the
  parent's scale times its sign; a product's volume row times the target price, its price row times the actual
  volume. `effect = scale × gap`. A quantity node splits further by its own expression with that scale.
- **Why.** AT-2: Kobo's 480 litres at 1.25 split into necessary −37.50, candidate −412.50 and not explained −150.00,
  each priced at the target price, and they sum to the fuel line's −600.00 exactly. One rule covers kWh under revenue
  and litres under fuel cost alike.

## D-5B.4 A stated heading splits only as far as its factors explain its record; a residual sits only beside what is not observed

- **Ruling.** Where a side's record differs from what its factors compute, the heading is not split
  (`RECORD_AND_FACTORS_DIFFER`). Where some terms cannot be computed: with at least one computable term, those terms
  split and one RESIDUAL row carries the rest, naming the unobserved leaves; with none, the heading is not split
  (`DETAIL_NOT_AVAILABLE`), naming them. A node that is not stated never has a residual (its value implies every
  part is known).
- **Why.** P5 rule 8: "a residual appears only beside a factor that is not observed"; AT-11: no invented split. On a
  typical operator's exports, revenue and fuel cost come from records while kWh and litres are not observed, so the
  bridge stops at the heading (Kobo +38.00 and −600.00) and names what would split it, exactly as the plan's §0.4
  says the screen must.

## D-5B.5 Option-only parts give no row

- **Ruling.** A term with a factor that is `NEUTRAL` on both sides gives no row (`collection_cost`, `battery_wear`,
  `extra_l` today).
- **Why.** D-3B3.15: an option-only factor holds its neutral value on observed and target sides alike and moves only
  under an option, which this bridge never contains (design: an option is beside the structure, never a node of it).

## D-5B.6 Each row's label is the weakest of what it rests on

- **Ruling.** Evidence is the weakest class and origins the union, in `ORIGIN_ORDER` with `unknown` last, over the
  exact values the amount uses: both sides for a sum term or the root; actual and target quantity and target price for
  a volume effect; actual and target price and actual quantity for a price effect; the parent's two sides for a
  residual.
- **Why.** P5 rule 6 and D-4B.18: a figure is never labelled stronger than its weakest part. A gap against an assumed
  target (Kobo's cash: zero leaks assumed) reads *Estimated* with `unknown` origin.

## D-5B.7 A missing cost line is carried at its own budget line, Estimated; nothing else is carried

- **Ruling.** Only the leaves in `CARRY_AT_TARGET` (`om`, `staff`), only when the actual's cause is `NOT_RECEIVED`
  with no note (a connected source, a closed month, no record), and only from a target that is its own budget line
  (`DECLARED`, `budget:` sources). The carried value is `ESTIMATED`, `carried_as` TARGET, with the missing record's
  words and `CARRIED_TEXT`, sources `target:budget:<revision>` and the line's origins. Headings are never carried; an
  assumed target is never carried; an open month is never carried. Owner questions Q1 and Q2 carry the first and
  third with their defaults.
- **Why.** P5 rule 8, the structure specification §3 rule 3 and D-4B.8 ("`5b` applies it"); plan §0.4: a cost line not
  sent reads "Not available yet", or *Estimated* where the operator states an estimate. A heading carried at target
  has a zero gap by construction, which would hide the gap the screen exists to show. In an open month every record
  is still due, so carrying would show a month on budget that has not happened.

## D-5B.8 Headings on the bridge are the factors' own homes, read from the lowest rows

- **Ruling.** `by_home` sums the effects of the lowest rows (not split further, and residuals) by each factor's own
  home category, so losses and adjustments under revenue count under Optimize.
- **Why.** Decisions-register item 17 and design §2.0: a part can belong under a different heading from its whole;
  the bridge "by heading" (vNEXT Assure, "Contribution's bridge by heading") must read the same rule. Σ by heading
  equals the root effect.

## D-5B.9 The portfolio gap is one set of Sites against the same set

(Amended at the handshake by D-5B.11: only `SUM`-composing rows add their values.)

- **Ruling.** Each portfolio row sums actual, target, gap and effect over the Sites whose own row has an effect, and
  names the Sites left out with their reasons ("k of n"). It never subtracts a target over n Sites from an actual over
  k. Currencies are never added together.
- **Why.** Owner: "k of n sites". Without Mto's billing the honest gap is −747.00 over two Sites, not 633.00 − 2295.00.

## D-5B.10 `5c` shows every disagreement and every stop

(Amended at the handshake by D-5B.12: `5c` also shows one contribution per month, the bridge's.)

- **Ruling.** `5c`'s spec must show each `disagreements` entry (Kisiwa's budget contribution −60.00 against the
  computed −65.00) and each `NOT_SPLIT` reason with the records that would split it, in plain words.
- **Why.** P5 rule 2 ("a difference is shown, never hidden") and the plan's §0.4 ("each naming the record that would
  fill it"). Recorded here so the obligation reaches the screen slice.

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, against `handshake.md` round 1 (`task/3B7a-5b-handshake` at `9908b6028`). Every
answer is folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. Four new rulings (D-5B.11 to D-5B.14) follow
the answers. Each gate below names a plant that fails it.

### R1 (High): only SUM-composing rows add up across Sites (D-5B.11)

**Answer.** The class is "a figure added across Sites whose factor does not add". 3B3's `compose` already fails
closed on it (D-3B3.14: only `composes == "SUM"` factors are summed), and 5a's portfolio target goes through
`compose`; `portfolio_bridge` is the one path that sums every key. Ruling: a `PortfolioRow` adds `actual`, `target`
and `gap` across Sites **only when its factor's registry row has `composes == "SUM"`**; for any other factor
(today `tariff`, `productive_tariff`, `diesel_price`, `wear_rate`, `period_days` and the other `NONE` rows) those
three are None. `effect` is always summed (it is money on the root, and effects add), with `k of n` and `out` as
before. RESIDUAL rows are unchanged (None). Sweep: `compose` (3B3) and `TargetRead.portfolio` (5a) are clean; the
pack is not (below); nothing else adds across Sites today.

**The pack and the mock-ups.** The pack sums every node: `derived-values.json`
`portfolio["lakeside-power"].{plan,actual}.sums` holds `diesel_price` 3.8, `tariff` 1.35, `productive_tariff` 0.9,
`wear_rate` 0.24 and `period_days` 93, written by `evaluate_structure.py` line 562 (a sum over every node name). **No
screen shows a summed price.** The vNEXT mock embeds the file (`fixtures.js`, `index.html`) but no screen reads
`portfolio.*.sums`: prices appear per Site only (the Site tree's tariff and diesel price, the Site inputs table).
`frontend/mockups/v70/index.html` and the v72 hi-fi pages show no portfolio price. So no screen fix is needed. **Pack
fix, queued (not blocking 5b):** `evaluate_structure.py:562` sums only factors the structure declares summable
(MINI_GRID: `composes == "SUM"`), then `derived-values.json` and the copy embedded in the vNEXT mock are regenerated.
Owner of the fix: the pack lane (the maintainer of the DS1p evaluator), dispatched by the coordinator. Until it
lands, test 7 compares only `SUM` keys with the pack and asserts the `NONE` rows' sums are None.

**Gate.** Spec test 8(c): two Site bridges from §5.1's leaves (as given, and AT-3's actual price 1.30), composed by
`portfolio_bridge`: the `diesel_price` row has `actual`, `target`, `gap` None and `effect` −59.00 (0 + −59.00),
`k` 2; the `tariff` row has them None and `effect` 0.00; the `diesel_l` row (SUM) has 2360, 1400, 960 and −1200.00.
Plant V17 (sum every key) fails it with a "diesel price" of 2.55.

### R2 (High): one contribution per month, and which (D-5B.12)

**Answer.** P5 rule 8 (owner-approved) makes the carried figure *the* actual: "a missing actual line is carried at
its own target only where one exists, *Estimated*, naming the missing record". The owner's "k of n" rule and D-5B.9
make one set of Sites per figure. One rule follows, and `5c` shows it:

1. **Which figure.** Every screen that shows a month's money for a structure (contribution, its headings, the cash
   root) shows the **bridge's** figures: a Site's from `SiteBridge.roots[...]` (its `actual` is
   `evaluate_inputs(carried inputs)`), the portfolio's from `PortfolioBridge.rows[...]`. For Lakeside October:
   1,443.00 against 2,295.00, −852.00, 3 of 3, *Estimated*. The uncarried composed actual (`StructureRead.portfolio`,
   3B7a's `PortfolioMonthSnapshot.actual()`: 883.00, 1 of 3) and the composed target (`TargetRead.portfolio`,
   `PortfolioMonthSnapshot.targets()`) are inputs and verification reads, never a screen figure. The fresh path and
   the snapshot path give the same bridge (`site_bridge(snap.inputs, snap.targets)`, spec §4.2).
2. **Which Site set.** Each row's `actual`, `target` and `gap` are over that row's included Sites, one set (D-5B.9).
   A Site left out is named in `out` with its reason; `5c` may show its own target on that line (from its own
   `SiteBridge` root), never added into the row.
3. **How the carried value is labelled.** The row's evidence is *Estimated* (weakest part, D-5B.6) and
   `PortfolioRow.carried` names the Sites whose figure rests on a carried line (R7, accepted); `SiteBridge.carried`
   names the leaves. `5c`'s words name, per carried Site, the missing record and `CARRIED_TEXT` (e.g. "Kisiwa: service
   contractor invoice not received; taken at its budget line for the month (estimate)").

D-5B.10 is amended: `5c`'s spec inherits points 1 to 3, and its review gate includes "the screen's contribution equals
the bridge row; a plant rendering `PortfolioMonthSnapshot.actual()` fails".

**Owner's view wanted on one point (queue Q5, default applied).** When a Site's actual is missing, the like-for-like
target (e.g. 1,380.00, 2 of 3, Mto left out) differs from P5 rule 7's portfolio target over every Site with a target
(2,295.00, 3 of 3). Default: the gap view shows only the like-for-like figures, with "Mto not compared: billing not
received; its target 915.00" beside them, so no second contribution target appears. The owner may prefer the
3-of-3 target shown as well; the default applies until the owner says otherwise. Lakeside's demo October (with Mto's
billing) is 3 of 3 and reads the same either way.

**Gate.** Spec test 7: `rows["contribution"][k].carried == ("KISIWA-001",)` for `om`, `cost_to_serve` and
`contribution`, `()` for `revenue`, `fuel_cost` and `staff`; the portfolio `contribution` row is 1443.00 / 2295.00 /
−852.00, ESTIMATED. Plant V20 (drop `carried`, or compute it from `targets` rather than the Sites' carried leaves)
fails it; plant V9 (composed actual minus composed target) already fails test 8. The screen-side half is `5c`'s gate.

### R3 (Medium): the seam

**Answer.** As 3B7a R1 (D-3B7A.10): 3B7a unit 0 writes it alone and merges first; 5b unit 2 starts after it is on
`main`. The guide's check is now "5b's branch has no diff in `structure/read.py`" (plant: one edited line there; the
`git diff main...task/5b-attribution -- backend/assetops_backend/structure/read.py` is non-empty).

### R4 (Medium): one instant per bridge read (D-5B.13)

**Answer.** Accepted. `BridgeRead(actual, targets, clock)`; each `site` and `portfolio` call pins `k = known_at if
known_at is not None else clock()` (UTC) once and passes `k` to `targets.site`/`targets.portfolio` and to every
`site_inputs`. `build_bridge_read` passes a UTC clock. **Gate.** Spec test 9(b): recording wrappers around the
`StructureRead` and `TargetRead` record each call's `known_at`; `BridgeRead(..., clock=lambda: READ_AT)` with
`known_at` None records only `READ_AT`. Plant V19 (pass None through) fails it.

### R5 (Medium): the 34-digit solve (D-5B.14)

**Answer.** The reviewer's case is real, and it reaches further than step 4: once litres are observed, the solved
target litres also make step 6's sum check fail (`(Qa − Qt) × Pt + (Pa − Pt) × Qa` equals `Qa·Pa − Qt·Pt`, and
`Qt·Pt` is 874.99…99, not 875.00), so the heading would read `SPLIT_INEXACT`. The class is "a quotient compared
exactly". Ruling: steps 4 and 6 compare with `SOLVE_TOLERANCE = Decimal("1E-12")`: two values agree when
`abs(x − y) <= SOLVE_TOLERANCE`. That is far below any recorded unit (a cent, a watt-hour) and far above the
34-digit context's error at these magnitudes (about 1E-30). Nothing is quantised; displayed figures are rounded by
`5c`. Exactness stays `==` wherever no quotient enters (all of §5.1 and §5.2).

**Gate.** Spec test 3(i) at 1.27 (fuel cost splits; VOLUME 623.60 to the cent, PRICE −23.60 exactly; children differ
from the parent by a non-zero amount within the tolerance) fails plant V18a (`SOLVE_TOLERANCE` 0 or `==`); test 3(j)
(a stated revenue of 3458.01 against computed 3458.00 still `RECORD_AND_FACTORS_DIFFER`) fails plant V18b (a
tolerance of 0.01 or more).

### R6 (Medium): test 10's commercial import

**Answer.** `structure/attribution/composition.py` is exempt (wiring, as every composition module); every other
module under `structure/attribution/` imports no `commercial` or `snapshot` module. Building through
`build_target_read` is not used: its service does not expose the actual `StructureRead`, and a second
`build_structure_read` would open a second pool for the same reads. Plant: a `commercial` import in `bridge.py`
fails test 10.

### R7 (Medium): carried marker on the portfolio row

**Answer.** Accepted, as part of R2: `PortfolioRow.carried: tuple[str, ...]`, the included Sites (in `asked` order)
whose own row rests on a carried leaf (the row is that leaf, or the leaf is below it in the Site's tree:
`row.carried` or any descendant's). Test 7 as R2's gate.

### R8 (Medium): V13's second half

**Answer.** Dropped. A RESIDUAL is created only in step 6's "some term not computable" branch, which needs a side
whose node value exists while a factor does not, i.e. a stated side; a non-stated node with a value has every factor.
The half was unreachable, so no plant could fail it. V13 keeps its first half (test 3(b)).

### R9 (Low): Kisiwa and Mto literals

**Answer.** Accepted: revenue and fuel cost are `NOT_SPLIT`, `DETAIL_NOT_AVAILABLE`, and their `unobserved_*` are
Kobo's literals, written out per Site: revenue `unobserved_actual == ("adjustments_kwh", "delivered_kwh",
"productive_tariff", "tariff", "technical_loss_kwh", "unexplained_loss_kwh", "unmapped_kwh")`, `unobserved_target ==
("delivered_kwh", "productive_tariff", "tariff")`; fuel cost `unobserved_actual == ("candidate_l", "necessary_l",
"unexplained_l")`, `unobserved_target == ()`. Why the same: the same 4b readers judge the same record shapes (a
billing export with kWh but no meter or tariff schedule; a fuel invoice with litres, no litre split; Mto's step
copies Kisiwa's shapes), and 5a's target rules are per factor, not per Site (5a's test asserts the target revenue
tuple for all three). A run that differs is a mid-build question, never the output adopted.

### R10 (Low): test 3(a)'s RESIDUAL

**Answer.** Accepted: the literal `("delivered_kwh",)` (as 4b1's test asserts for a stated revenue with
`delivered_kwh` absent).

### R11 (Low): a repeated key

**Answer.** Accepted: `portfolio_bridge` raises `ValueError("REPEATED_FACTOR:<factor_id>")` when one Site's tree under
one root holds a factor twice. Test 11: a hand-built `SiteBridge` whose tree repeats `om`. Plant: no check (rows
merge silently) fails it.

### R12 (Low): `unobserved_*` holds stated nodes too

**Answer.** Intended. For `GAP_NOT_AVAILABLE` the field is the side's `missing_leaves`, which names a stated node when
its own record is missing (4b's `MTO_MISSING` holds `fuel_cost` and `revenue`): `actual:fuel_cost` reads "the fuel
invoice for the month". The field comment now says "the inputs (leaves, or stated nodes whose record is missing)
that would fill this side".

### R13 (Low): the pack comparison

**Answer.** Accepted. Compared: for each Site (`{"Kobo": "KOBO-001", "Kisiwa": "KISIWA-001", "Mto": "MTO-001"}`,
pack key `sites["lakeside-power/<Name>"]`) and for the portfolio (`portfolio["lakeside-power"]`), the nodes
`revenue`, `collected`, `in_transit`, `outstanding`, `fuel_cost`, `om`, `staff`, `cost_to_serve`, `contribution`:
the bridge row's `actual` against the pack's `actual` (`nodes`, or `sums` for the portfolio) and `target` against
`plan`, each as `Decimal(str(x)) == row value` (numeric equality). Gaps, effects and evidence are not in the pack and
are checked against the spec's literals only. `NONE` keys are not compared (R1).

### Pre-flight P1 to P6

- **P1, P2, P3, P6:** confirmed, no change. P6's comparison follows R13.
- **P4:** accepted as planned: if 3A1 refuses `mto-billing` or two intakes at one instant, stop that test and ask
  (mid-build question); do not change the fixture's figures.
- **P5:** answered by R3 (D-3B7A.10).

## D-5B.11 Across Sites, only SUM-composing rows add their values

- **Ruling.** A portfolio row adds `actual`, `target` and `gap` only for a factor with `composes == "SUM"`; otherwise
  they are None. `effect` (money on the root) always adds.
- **Why.** D-3B3.14: `NONE` fails closed. A summed price (3.80 a litre over three Sites) is a false figure; the
  effect of a price on contribution is money and adds exactly.

## D-5B.12 One contribution per month: the bridge's, one Site set per figure, the carried part labelled

- **Ruling.** Every screen showing a month's money for a structure shows the bridge's rows (Site: `SiteBridge`;
  portfolio: `PortfolioBridge`), each over its own included Sites with "k of n" and the Sites left out named; the
  composed actual and target are never screen figures. A row resting on a carried line is *Estimated* and names its
  Sites (`carried`). Amends D-5B.10: `5c` inherits this.
- **Why.** P5 rule 8 makes the carried figure the actual; the owner's "k of n" and D-5B.9 forbid one set against
  another. Two figures for one month (883.00 and 1,443.00) would make the executive ask which is true.

## D-5B.13 A bridge read is taken at one instant

- **Ruling.** `BridgeRead` pins `known_at` (given, or its clock once) and passes it to every read in the call.
- **Why.** `TargetRead.site` reads the actual itself for `AT_ACTUAL` targets; two reads at two moments could set a
  target from one state and the actual from another, a false gap (as D-3B7A.2 for the snapshot).

## D-5B.14 Agreement is judged within `SOLVE_TOLERANCE` (1E-12), never by quantising

- **Ruling.** Step 4 (record against factors) and step 6 (children against parent) treat values within 1E-12 as
  equal. Exact `==` holds wherever no quotient enters.
- **Why.** 5a's solve divides at 34 digits, so a solved target never multiplies back exactly; without a tolerance a
  heading with solved litres never splits. 1E-12 is far below any recorded unit, so a real difference (a cent) still
  stops the split.
