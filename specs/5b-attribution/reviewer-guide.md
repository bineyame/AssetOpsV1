# 5b reviewer guide (rev 2, handshake round 1 answered)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md`, P5 and this guide; put questions in
`handshake.md`), then at the review. Depth: discovery (W5): the first gap in money, a new mechanism, and the rule
that turns a missing record into an estimate.

## First checks

1. **Scope.** New: `structure/attribution/` (rules, bridge, carry, site, portfolio, read, composition), the fixture
   `attribution_lakeside_mto.json`, `test_5b_attribution.py`, `test_5b_attribution_postgres.py`, the packet. **No diff
   in `structure/read.py`**: `git diff main...task/5b-attribution -- backend/assetops_backend/structure/read.py` is
   empty (the seam is 3B7a unit 0's, D-3B7A.10). No other existing module edited; no migration.
2. **W2.** Expected values are spec §5's hand-computed literals and the pack's `derived-values.json`, never the
   code's own output; the AT vectors are typed in the test, not derived.
3. **Order.** Unit 2 built only after 3B7a unit 0 merged to `main`; unit 3 after unit 2.

## Done means

Spec §7's nine questions answered yes with real output: the no-database file, the Postgres file and the regression
set through `tools/heavy-slot.sh --db`, check-all, and every planted violation below failing its named test.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V1 | Price effect at target volume `(Pa − Pt) × Qt` | test 2 (35.00 and 624.00) |
| V2 | Volume effect at actual price | test 1 (AT-1 rows), test 2 |
| V3 | Pick the price by position in the product | test 3(d) |
| V4 | Carry a stated heading (`fuel_cost`) at its target | test 5(e) |
| V5 | Carry in an open month (ignore the note) | test 5(b) |
| V6 | Carry from an assumed target | test 5(d) |
| V7 | Give the carried leaf the evidence `RECORDED`, or no `carried_as` | test 6 (Kisiwa root ESTIMATED; the leaf field by field) |
| V8 | Use the budget's contribution line (−60.00) as Kisiwa's target | test 6 (−185.00), test 7 (−852.00, disagreements) |
| V9 | Portfolio gap as composed actual minus composed target | test 8 (−747.00, not −1662.00) |
| V10 | A missing side read as 0 | test 3(g), test 8 (Mto root) |
| V11 | Row evidence from the actual side only | test 6 (Kobo root DECLARED), cash roots ESTIMATED |
| V12 | `by_home` from the root's direct children | test 1 (`OPTIMIZE_COST` −782.00) |
| V13 | A residual on a heading with no computable term (the "node not stated" half is unreachable: handshake R8) | test 3(b), test 1 (no RESIDUAL anywhere) |
| V14 | Emit rows for neutral terms | test 1 (cost_to_serve children exactly fuel_cost, om, staff), test 4 |
| V15 | Drop the disagreement | test 7 |
| V16 | Split a heading whose record its factors do not explain | test 3(c), 3(j) |
| V17 | Sum `actual`/`target`/`gap` for every key (a price adds across Sites) | test 8(c) (a "diesel price" of 2.55) |
| V18a | Compare exactly (`SOLVE_TOLERANCE` 0, or `==` in steps 4 and 6) | test 3(i) |
| V18b | A tolerance of a cent or more | test 3(j) |
| V19 | `BridgeRead` passes `known_at` None through instead of pinning its clock | test 9(b) |
| V20 | Drop `PortfolioRow.carried`, or derive it from the targets rather than the Sites' carried leaves | test 7 |
| V21 | No repeated-key check in `portfolio_bridge` | test 11 |
| V22 | An edit to `structure/read.py` on this branch | first check 1, test 10 (`git diff` non-empty) |

## Probes

- **Exactness.** Every SPLIT row's children sum to it with `==` on `Decimal` wherever no quotient enters, and within
  `SOLVE_TOLERANCE` (1E-12) only where 5a's solve does (D-5B.14); no quantising; no `float`.
- **Words.** `CARRIED_TEXT` and the reason literals are the spec's, byte for byte.
- **Reads.** `BridgeRead.portfolio` reads `TargetRead.portfolio` once and each Site's inputs once.
- **No commercial import.** `structure/attribution/` reaches records only through `StructureRead` and `TargetRead`;
  `composition.py` alone imports `commercial` (wiring).
- **One instant.** Every read in a `BridgeRead` call receives the same `known_at`.

## Class sweeps (W6)

- *An unknown read as zero:* every path in `bridge.py` and `portfolio.py` that yields `Decimal("0")` is a gap of two
  equal values or a sum of zeros, never a missing value.
- *An estimate presented as recorded:* every `LeafValue` built in `carry.py` is `ESTIMATED` with `carried_as`
  TARGET.
- *Two sets subtracted:* every portfolio sum is over one `included` tuple.
- *A figure added that does not add:* every cross-Site sum checks `composes == "SUM"` (effects excepted).
- *Two contributions for one month:* nothing in this slice returns a composed actual or target as a bridge figure;
  `5c`'s spec carries D-5B.12.

## Risks

- `4d` lands litre leaves while this is in review: §2.3 splits them with no change; check the AT-2 test still names
  the same rows.
- The owner answers Q1 (carry a heading) against the default: `CARRY_AT_TARGET` and test 5(e) change together.
- The owner answers Q5 (show the full target too) against the default: a `5c` change only; this slice's rows stay.
