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

- **Ruling.** Each portfolio row sums actual, target, gap and effect over the Sites whose own row has an effect, and
  names the Sites left out with their reasons ("k of n"). It never subtracts a target over n Sites from an actual over
  k. Currencies are never added together.
- **Why.** Owner: "k of n sites". Without Mto's billing the honest gap is −747.00 over two Sites, not 633.00 − 2295.00.

## D-5B.10 `5c` shows every disagreement and every stop

- **Ruling.** `5c`'s spec must show each `disagreements` entry (Kisiwa's budget contribution −60.00 against the
  computed −65.00) and each `NOT_SPLIT` reason with the records that would split it, in plain words.
- **Why.** P5 rule 2 ("a difference is shown, never hidden") and the plan's §0.4 ("each naming the record that would
  fill it"). Recorded here so the obligation reaches the screen slice.

## Handshake answers (round 1)

(none yet)
