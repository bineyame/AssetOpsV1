# 4b handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Fresh Claude reviewer, 2026-11-20, against `caafe4212` (spec rev 1, D-4B.1 to D-4B.12, reviewer guide rev 1).
Severity: **High** blocks code until answered; Medium and Low are answered in the same round. Numbering is R/P as
the dispatch asked (the template's I-numbers are the P-numbers below).

- **R1 (High, done). Planted V5 cannot fail; origin order is never actually tested.** Spec §2.7 S6, §4.1;
  reviewer guide V5. Every origin tuple any test asserts is drawn from `{observed-financial, source-emulated}`, and
  those two sort the same alphabetically as in `ORIGIN_ORDER`. So "sort origins alphabetically" (V5) passes S6, S7
  and every §4.1 row; the same holds for a `weakest_origin` planted as the alphabetical maximum (S6 still gets
  `source-emulated`). S5's wrong-order refusal tests the input check, not the union. This is the "weakest part sets
  the label" rule in origin, with no test that can fail. Expected answer: S6 adds a pair whose two orders differ,
  e.g. `om` `("demo-simulated",)` and `staff` `("source-emulated",)` giving `cost_to_serve.origins ==
  ("source-emulated", "demo-simulated")` and `weakest_origin == "demo-simulated"`, plus one with `field-integrated`
  or `bench-tested` against `observed-financial`; the guide names that assertion for V5.
- **R2 (High, done). An absent `in_transit` (and `outstanding` in one case) names a record that is not the one
  judged.** Spec §3.3 to §3.4, D-4B.9, done Q3 ("its own record and a true cause"). `in_transit`'s `filled_by` is
  `COMMERCIAL_RECORD`/`SETTLEMENT` (`rows_mini_grid.py:207`), but 4b fills it from RECEIPT status and judges
  `NOT_CONNECTED` on RECEIPT, while §3.3 builds the `Missing` from `filled_by`. Test 7(a) (no RECEIPT at all) then
  says "settlement statement not connected", which is false (settlement matching is not built, queue Q3) and is
  not the record that would fill it. Likewise `outstanding` (`filled_by` RECEIPT) with CHARGE not connected and
  RECEIPT connected reads "RECEIPT not connected", which is also false; `NEEDS:<kind>` is set only in case 3, not
  case 1. Expected answer: a ruling on which record an absent 4b leaf names when its needed kinds differ from
  `filled_by`, either (a) a v3 registry change to `in_transit`'s `filled_by` (it touches 3B1's manifest parity,
  so the manifest moves too), or (b) a 4b-local "needed record" carried in `Missing` with `note
  NEEDS:<kind>` in case 1 as well; and test 7(a) asserting `record_kind` and note for both leaves.
- **R3 (High, done). In an open month the diesel price falls back to the declared price even when fuel invoices
  exist.** §3.3 (the `diesel_price` exception covers case 2), D-4B.6 ("an open month"), against D-4B.4 ("every leaf
  ... 4b provides has no value" in an open month), D-4B.6's own reason ("the assumption never hides records") and
  done Q6 ("a price never taken from the assumption while invoices exist"). Kobo in November with a fuel invoice on
  file would read the declared 1.30, labelled, while the invoices say otherwise. No test reads `diesel_price` in an
  open month (test 2 reads `revenue` and `om` only, and Kobo has no November fuel invoice), so done Q6 would be
  answered yes untested. Expected answer: an open month gives `diesel_price` no value (`NOT_RECEIVED`,
  `MONTH_OPEN`) when the month holds any FUEL cost line, and the fallback only when it holds none (or always no
  value, as every other 4b leaf); test 2 adds a November FUEL invoice and asserts it.
- **R4 (Medium, done). Planted V14's second half ("under the default decimal context") cannot fail.** Guide V14,
  §3.4 sums. Every fixture sum fits in 28 significant digits, so a sum under the default context gives the same
  digits, and test 11 greps only `float(`. Expected: either drop that half of V14, or add a case that needs more than
  28 digits exactly (2a's decimal limits permitting) or a check that the sums run under 3A4's `_exact()` context.
- **R5 (Medium, done). Zero litres divide by zero.** §3.4 `diesel_price`. 2a's EXPENSE `quantity` sign is
  `nonneg` (`records_v1.py:115-120`, `_Part.sign` default), so a FUEL invoice of 0 L is valid, and FUEL cost lines
  summing to 0 L make `Σ amount / Σ litres` raise `DivisionByZero` inside the read. Expected: a ruling (no value,
  `NOT_CALCULATED_YET`, a note such as `ZERO_DENOMINATOR:fuel_litres`, never the fallback since invoices exist) and a
  test.
- **R6 (Low). Two named gates in the guide cannot fail by the stated mechanism.** V7: test 8 gives 1835.00 with or
  without the plant (only test 1 fails). V11: test 1's Kisiwa `om` cause is `NOT_RECEIVED` either way, because
  Kisiwa holds October EXPENSE lines (fuel, staff); only test 7(b) fails. Expected: the guide names the tests that do
  fail.
- **R7 (Low). The composition's disposal on a builder failure has no test.** §3.5 requires it and the guide probes
  it, but §5 lists no test. Expected: an L1-style test (`test_3b3_structure_evaluate.py:784` pattern) where the
  commercial builder raises and both earlier stores are disposed once, and `dispose()` disposes all three.
- **R8 (Low). `computed` for a stated node: bullet against table.** §2.3 says "computed on a stated node is the
  expression's value"; the table's second row says `computed = None` while the expression has a value. Also, that
  row drops the stated value's `missing` (for example `CURRENCY_MISMATCH` on the charges) once the expression
  computes; unreachable for MINI_GRID until 4a and 4d, but worth a line in D-4B.1. Expected: the bullet defers to the
  table, and the ruling says whether a refused record (mixed currency) may be silently replaced by the expression.
- **R9 (Low). Which lines give a recorded zero its currency, and which lines step 4 checks.** §3.3 step 4 says "the
  lines"; for a recorded zero (Kobo `in_transit` 0 USD) the used lines are empty, and a money leaf with a value and
  no currency is refused (`STRUCTURE_CURRENCY`). Expected: "all lines of the needed kind" for both the currency and
  the mixed-currency check of a recorded zero.
- **R10 (Low). The deep-dive gate says 883.00 "equal to the pack's", but no 4b test reads the pack.** §1, §5.
  Expected: test 1 (or the Postgres test) also reads `derived-values.json`
  `sites.lakeside-power/Kobo.actual.nodes.contribution` (W2's independent check), or the gate drops "equal to the
  pack's".
- **R11 (Low). The guide's "two store calls" probe counts the wrong thing.** One `site()` read makes three store
  calls: `site_zones` and `latest_revisions` inside `site_month`, then the kinds read. Expected: "one `site_month`
  and one `latest_revisions` per Site read".
- **R12 (Low). S8's `diesel_l` plant should state its family.** To fail only for the unit, the planted `stated_by`
  on `diesel_l` needs family `COMMERCIAL_RECORD`; otherwise it fails for the family first and the unit refusal is
  never exercised.

## Implementer pre-flight questions

Pre-flight of `spec.md` against `main` at `caafe4212` (3B1, 3B3, 3A1, 3A2, 3A4 merged). Numbered P.

- **P1 (Medium, done). The version sweep misses a fourth assertion.**
  `backend/tests/test_3b3_structure_evaluate.py:652` asserts `(result.structure_key, result.structure_version,
  result.site_code) == ("MINI_GRID", 2, "KOBO-001")`. §2.1's grep (`version == 2\|, 2)`) does not match it, and done
  Q8 allows only the three named edits, so 4b1's regression is red or the diff leaves its list. The three cited lines
  are right (`test_3b1_structure_registry.py:88`, `test_3b3_structure_evaluate.py:366`,
  `test_3b3_structure_read_postgres.py:82`). Expected: name `:652` as the fourth edit; sweep with `grep -rn
  '"MINI_GRID", 2\|version == 2' backend/tests` (which finds the four, plus `test_s3_dispatch_assessment_postgres.py:455`, an
  unrelated `version == 2`).
- **P2 (Medium, done). The T6 test body, not only its table, breaks under §3.2.**
  `test_t6_each_state_yields_its_leaf_value_on_its_own_record` (`test_3b3_structure_evaluate.py:532-553`) maps each
  state to one cause (`"PROVIDED": "NOT_RECEIVED"`) and has no key for `PROVIDED_ELSE_ASSUMED` (a `KeyError` for
  `diesel_price`). After §3.2, PROVIDED holds `period_days` (skipped), `unserved_critical_kwh` (today's cause) and the
  five new leaves (`NOT_CONNECTED` through `ProductLeafSource`), so a per-state cause cannot hold. The table itself is
  at `:69-80`, not `:60-80`. Expected: the spec names this edit (a per-leaf cause for the five, and
  `PROVIDED_ELSE_ASSUMED` checked like `ASSUMED`) inside done Q8's list.
- **P3 (Low). Collision note and base are stale.** 3A2 merged (`6db81330a`); `commercial/composition.py:78` already
  has `build_commercial_months`, and `build_commercial_reads` goes beside it. "Builds on (merged, a8e1fd2a3)" is now
  `caafe4212`. Expected: the spec says so; no merge-order question remains for `composition.py`.
- **P4 (Low). "Money dimension" for `STRUCTURE_STATED`: which test?** `FactorRow.money` is `Unit.is_money`
  (exactly `MONEY^1`, `units.py:62`); `evaluate._money_dimension` is any MONEY exponent. Both refuse `diesel_l`
  (L), and no stated node today is a rate. Expected: confirm `_money_dimension`'s meaning (so a future money-per-unit
  heading is allowed) or `is_money`.
- **P5 (Low). Builder order in `build_structure_read`.** Today: snapshots, then prices, with the L1 test
  monkeypatching both (`test_3b3_structure_evaluate.py:784-800`). Expected: commercial third, so the L1 test stays
  green unchanged; confirm.

Verified, no question: `FilledBy(family, kind, words)` order matches §2.1's literals; `_node` (`rows_mini_grid.py:186`)
takes keyword-only `composes`, so `stated_by=None` joins it; `_CHECKS` order (`check.py:209-222`) and no test pins
`CODES`; `PROVENANCE_ORDER` (`months.py:30`) equals §2.2's `ORIGIN_ORDER` and, as a set, `PROVENANCES`
(`records_v1.py:38`); `MonthLine` carries `provenance`, `currency`, `unit`, `source_systems`, and EXPENSE dims are
`(category, status)`; `latest_revisions` takes `known_at`; `new_world` has all nine Sites (tests build `SiteRef`
themselves, `site_type` `MINIGRID`); `ingest_at` hardcodes `entered_by=BY`, so a local helper is needed (§5 says
so); 2a accepts every fixture enum (CASH, QUOTE, optional `tariff_class`). Hand figures recomputed: Kobo October
3,458.00 billed (2,000.00 + 1,458.00; the November 50.00 excluded), 3,180.00 received, 278.00 outstanding, collected
3,458.00 − 0 − 278.00 = 3,180.00, fuel 1,475.00 over 1,180 L = 1.25 (the 360.00 QUOTE excluded), cost to serve
1,475.00 + 600.00 + 500.00 = 2,575.00, contribution 883.00, equal to the pack's actual (`derived-values.json`);
Kisiwa 4,070.00, 270.00, 3,120.00 / 2,400 = 1.3; portfolio 7,528.00, 4,595.00, 1,100.00, 1,450.00, 548.00, 6,980.00,
883.00 (1 of 3); Mto's thirteen and the nine and eleven out lists; §4.2 after step F and at `known_at` 5 Nov
(495.50, 60.00, 335.50, 100.00, 1,000, 775.00 / 620 L, 275.00, 1,500.00, −1,004.50; 505.50, 345.50, 762.50,
−887.00). DS1b batch E: `build_records(view_v1, generate_history(view_v1))` writes exactly the five October actual
expenses (PAID, Kisiwa O&M unwritten `ESTIMATED_NOT_RECEIVED`), envelope `assetops-world-generator`,
`source-emulated`, `produced_at` `2026-11-06T06:00:00+03:00`. After 4b2, `test_3b3_structure_read_postgres.py`
reads through `CommercialLeafSource`; its assertions still hold with no commercial records (EXPENSE not connected,
the declared price, `contribution` missing `om`, `staff`, `tariff`, `necessary_l`).
