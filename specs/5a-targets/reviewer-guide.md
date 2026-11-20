# 5a reviewer guide (rev 1)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md`, `structure-page-P5.md` and this guide;
put questions in `handshake.md`), then at the review. Depth: discovery (W5): the first target figures, a new read
and the labelled-assumption rule the owner set.

## First checks

1. **P5 approved** before any unit merged (D-5A.12); the packet cites the owner file.
2. **Scope.** Only `structure/targets/` (new), the fixture, `test_5a_targets.py`, `test_5a_targets_postgres.py` and
   the packet. No existing module edited; no migration.
3. **Order.** Units 2 and 3 built after `4b1` merged; the branch merged `main` before unit 2.
4. **W2.** Expected values are spec §5's literals; `TARGET_RULE` and `MAIN_OF` are compared with the test's own
   tables; the pack comparison reads `derived-values.json`, not the code.

## Done means

Spec §7's eight questions answered yes with real output: the no-database file, the Postgres file and the regression
set through `tools/heavy-slot.sh --db`, check-all, and every planted violation below failing.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V1 | Sum two lines for one factor | test 2(b), test 8 |
| V2 | Pick the latest version when two exist | test 2(a), test 7 |
| V3 | Give an assumed target evidence `DECLARED` (or no `carried_as`) | test 3 (`in_transit`, `collected`) |
| V4 | Leave a leak target absent instead of 0 | test 3 (`collected` 3420.00) |
| V5 | Let assumptions below a stated heading weaken it (contribution `ESTIMATED`) | test 3, test 6 (DECLARED) |
| V6 | Use the budget's contribution line instead of the computed one | test 3 (Kisiwa −65.00), test 6 (2295.00) |
| V7 | Add the operator-level line into the portfolio | test 6 (`staff` 1450.00) |
| V8 | Solve the main factor without the linearity or slope test | test 5(b), 5(c) |
| V9 | Take the declarer from the revision's source system, or drop the `person:` parse | test 1 |
| V10 | Take an `AT_ACTUAL` target with the actual's evidence | test 3 (`diesel_price` ESTIMATED) |
| V11 | Read an absent actual as 0 under `AT_ACTUAL` | test 3 (`tariff` absent), test 8 |
| V12 | Fall back to an assumption for a blocked factor | test 8 |
| V13 | Compose the portfolio over all Sites with 0 for a missing one | test 7 |

## Probes

- **No second figure.** The target contribution comes from `evaluate`, never from a line; the check only compares.
- **Every absent target names `BUDGET_LINE`** with a note from the spec's closed set (`BUDGET_VERSIONS`,
  `DUPLICATE_DECLARATION`, `CURRENCY_MISSING`, `CURRENCY_ON_QUANTITY`, `TARGET_CURRENCY_UNKNOWN`,
  `ACTUAL_NOT_AVAILABLE`, `MAIN_FACTOR_UNSOLVED:`, `MAIN_FACTOR_NONLINEAR:`, `MAIN_FACTOR_ZERO_SLOPE:`, or None).
- **Words.** The three assumption texts and `TARGET_WORDS` are the spec's literals, byte for byte.
- **Reads.** One `site_month`, one `latest_revisions` and one `intake` per distinct intake per Site read.

## Class sweeps (W6)

- An assumption presented as declared: every `LeafValue` built in `read.py` with a value either cites a line
  (DECLARED) or is `ESTIMATED` with `carried_as` ASSUMPTION, or is NEUTRAL or CALENDAR.
- An unknown read as zero: every path that returns `Decimal("0")` is `LEAK_ZERO` or a neutral.

## Risks

- `4b1`'s fields change after this builds on them: check `4b`'s rulings at review time.
- The owner changes a P5 rule on day 3: the spec is revised first (D-5A.12).
