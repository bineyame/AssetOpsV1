# 4b rulings

Architect (Claude), 2026-11-20. Each ruling gives its reason. Index lines: `.ai/decisions/index-rulings-10.md`.
Handshake answers go below, under "Handshake answers (round 1)".

## D-4B.1 A node that a record states is read from that record; its expression stays as the explanation

- **Ruling.** A registry node may declare `stated_by` (the record that states its total). `evaluate` takes an optional
  `stated` map: a stated value with a value is the node's value, and the node's expression is still evaluated and
  kept as `computed` and `detail_missing`. With no stated value the node is computed as before. MINI_GRID: `revenue`
  (CHARGE) and `fuel_cost` (EXPENSE FUEL) only. The seam is unit `4b1`, reviewed and merged on its own before `4b2`
  and before `5a`'s units 2 and 3 build on it (RULES §7: a unit that touches shared code is reviewed first).
- **Why.** A typical operator sends billing and fuel invoices, not kWh delivered or litres burned (`two-week-build-plan.md`
  §0.4). Bottom-up, `revenue` needs `delivered_kwh` (4a) and `fuel_cost` needs the litre split (4d), so without this
  the deep-dive screen could show neither heading. The charge total is revenue's own record, not a substitute (the
  structure specification's rule 1: a leaf "may fall back only to another record"; the pack's "stated totals", §3).
  The expression is kept so the screen can still say which factors below the heading are not available yet.
- **Consequence for D-BW1.10.** `5a` no longer waits for `4b`'s providers; it waits for `4b1` (1 unit, day 3), the
  seam both use. Its unit 1 does not wait at all.

## D-4B.2 Origin is carried beside the evidence class, and the weakest origin labels a total

- **Ruling.** `LeafValue` and `FactorValue` gain `origins` (the record provenances beneath the value, strongest first in
  `ORIGIN_ORDER`). Nodes and portfolio values take the union; `weakest_origin` gives the label's origin.
- **Why.** `economic-metric-and-effect-contracts.md` §4.4: a node "carries every provenance beneath it", and "no total
  is shown as a stronger class or provenance than its weakest part" (P3B rule: the weakest part sets the label).
  Emulated is a provenance, not a class (D-3B3.2), so it needs its own field; `3A5`'s rule on `5c` reads it.

## D-4B.3 Which records fill which leaf

- **Ruling.** As spec §3.4. Cost counts only `INVOICED` and `PAID` expenses, never `QUOTE`. Revenue is every CHARGE
  amount of the month. Credits (`ADJUSTMENT`) are not revenue; they are `liability`, outside 4b.
- **Why.** 3A4's queue Q3 (a quote is not a cost). A month's billing is the operator's billed revenue; netting credits
  would hide them, and the structure keeps them on their own leaf.

## D-4B.4 Money leaves from records need a closed month

- **Ruling.** While the month is open (3A4's `closed` false), every leaf and stated node 4b provides has no value,
  cause `NOT_RECEIVED`, note `MONTH_OPEN`.
- **Why.** The same class as D-3B3.12: a partial month's sum is a lower bound shown as the month.

## D-4B.5 Cause: connected, received, held

- **Ruling.** A record kind is *connected* for a Site when the store holds any record of that kind for the Site (as of
  `known_at`); it is *held for the month* when the month has a line of that kind. Absent value: `NOT_CONNECTED` when
  a needed kind is not connected, else `NOT_RECEIVED`. A ZERO_WHEN_HELD leaf reads a recorded 0 only when its kind is
  held for the month.
- **Why.** The structure specification §3.1 causes and rule 1 ("zero is a recorded fact only while the source that
  would record the event is held"). Kisiwa's missing O&M invoice is then "not received", not "not connected".

## D-4B.6 The diesel price comes from fuel invoices first; the declared price only when the month has none

- **Ruling.** New state `PROVIDED_ELSE_ASSUMED`. `diesel_price` = fuel cost / fuel litres over the month's INVOICED
  and PAID fuel invoices, evidence `DERIVED`. With no such invoice (no expense source, an open month, or no fuel line) it is read from the
  delegate (3B3's labelled assumption). With invoices that cannot give a price (mixed currencies), it has no value; the assumption never hides
  records.
- **Why.** The leaf's own record is `EXPENSE (FUEL)`; 3B3's declared price is the operator's value of the same
  quantity (D-3B3.11), so it is the honest fallback, still labelled.

## D-4B.7 Fuel cost is fuel bought in the month (owner question Q1)

- **Ruling.** The stated `fuel_cost` is the month's fuel invoices, named "Fuel invoices for the month". Litres burned
  come with `4d`; stock change is not modelled.
- **Why.** It is what the operator's accounts show as the month's fuel cost; anything else needs tank dips.

## D-4B.8 4b never fills a missing actual from a target (owner question Q2)

- **Ruling.** A missing actual reads not available, and the portfolio says "k of n sites". The structure
  specification's rule 3 (carry a missing line at its target, *Estimated*) needs `5a`'s targets, so `5b` applies it.
- **Why.** 4b does not depend on 5a (D-BW1.10); the owner accepted "k of n sites" (20 Nov).

## D-4B.9 Money in transit is read from the receipt's status

- **Ruling.** `in_transit` = the month's RECEIPT amounts with status `PAID_IN_TRANSIT`, as known at the read. Matching
  receipts to settlement statements is not built (queue Q3). A later revision of a receipt to `COLLECTED` moves it, as
  any late record does (3A4's stamps).
- **Why.** 2a carries the status on the receipt; matching by `receipts` references needs record bodies 3A4 does not
  line up, and is not on the path.

## D-4B.10 MINI_GRID becomes version 3, in place

- **Ruling.** `stated_by` is a row field, so the version moves to 3 (D-2A.2's class). It is replaced in place.
- **Why.** No stored value of version 2 exists (`3B7a` has not merged), as with D-3B3.9.

## D-4B.11 `detail_missing` names what is not available below a value

- **Ruling.** Every factor value carries `detail_missing`: the leaves beneath it with no value, even when the value
  itself rests on a stated record. The neutral identity (D-3B3.15) drops the other operand's list.
- **Why.** "Not available yet, with the record that would fill it" must survive under a stated heading: the screen says
  where the kWh and the litres are not known while revenue and fuel cost are.

## D-4B.12 One read of the store per Site-month read, never a cache across reads

- **Ruling.** `CommercialLeafSource` keeps one entry keyed by the identity of the `ReadContext` object, stored as one
  tuple. `StructureRead.site` builds a new context per call, so a later read always sees new records.
- **Why.** About ten leaves and stated nodes read the same month; a cache keyed by equality would serve a stale month
  after an intake.

## D-4B.13 An absent leaf names the record 4b reads for it, which may differ from the registry's `filled_by`

- **Ruling.** The record an absent value names (`fb` in spec §3.3) is the row's `READ_AS` record (spec §3.4's
  "Names" column): `stated_by` for the two stated nodes; `filled_by` for `om`, `staff`, `productive_kwh` and
  `diesel_price`; for `in_transit` the literal `RECEIPT_RECORD`; for `outstanding` the record of the *failing* kind
  (CHARGE → `CHARGE_RECORD`, RECEIPT → its `filled_by`), with note `NEEDS:<kind>` in cases 1 and 3. The registry is
  unchanged: `in_transit`'s own record stays SETTLEMENT, named again when settlement matching is built (queue Q3).
- **Why.** Handshake R2. Done Q3 asks for "its own record and a true cause": a gap must name the record that would
  close it *in this build*. 4b reads money in transit from the receipt's status (D-4B.9), so "settlement statement not
  connected" names a record nothing reads and sends the operator to the wrong file. Moving `filled_by` (option (a))
  would state in the registry, and in 3B1's manifest, that the leaf's own record is a receipt, which is false once
  matching exists; the substitute belongs to the reader that substitutes. `ProductLeafSource` (no commercial source at
  all) keeps naming `filled_by`: with nothing connected, the registry's own record is the honest answer.

## D-4B.14 The declared diesel price never stands in for fuel invoices, open month or closed (refines D-4B.6)

- **Ruling.** `diesel_price` falls back to the declared price only when the month has no fuel *cost* line (EXPENSE
  AMOUNT, category FUEL, INVOICED or PAID) or EXPENSE is not connected. A month with such a line and still open has no
  price (`NOT_RECEIVED`, `MONTH_OPEN`), as every other 4b leaf (D-4B.4).
- **Why.** Handshake R3. D-4B.6's own reason is "the assumption never hides records"; rev 1 let it hide November's
  invoices. With no invoice, the declared price is not a partial sum (D-4B.4's reason does not apply), so it stays the
  labelled fallback in an open month too.

## D-4B.15 Fuel invoices with zero litres give no price

- **Ruling.** When the month's fuel cost lines sum to 0 L, `diesel_price` has no value: `NOT_CALCULATED_YET`, note
  `ZERO_DENOMINATOR:fuel_litres`. Never the fallback, since invoices exist (D-4B.14).
- **Why.** Handshake R5. 2a allows a 0 L fuel line (a delivery fee); a division by zero is a refusal to compute, not
  a reason to show the assumption.

## D-4B.16 A stated record that is held but refused blocks its heading; the expression never replaces it (refines D-4B.1)

- **Ruling.** A stated value with no value and cause `NOT_CALCULATED_YET` (records held that cannot be read: mixed
  currency for 4b, a blocked budget line for 5a) gives the node no value, whatever the expression, in spec §2.3's
  third row's form. Only `NOT_CONNECTED` or `NOT_RECEIVED` (nothing to read) lets the expression's value through.
  `computed` is set only on the first row (a stated value with a value).
- **Why.** Handshake R8 (and 5a's R6, the same class). Serving the expression would silently replace the operator's own
  records with a figure that disagrees with them, the class D-4B.6 and D-5A.3 already refuse ("the assumption never
  hides records"; "never picked"). Unreachable for MINI_GRID actuals until 4a and 4d, reachable now on the target side.

## D-4B.17 A stated node's unit is exactly money

- **Ruling.** `STRUCTURE_STATED` refuses `stated_by` on a row whose unit is not `Unit.is_money` (exactly `MONEY^1`).
- **Why.** Handshake P4. `stated_by` names the record that states a node's *total*, and 4b sums records into it
  (§3.4). A money-per-unit heading is a rate; a record stating it would need a division the seam does not define.

## D-4B.18 Every valued part names its origin; an origin that cannot be named is `unknown`, ranked weakest

- **Ruling.** `ORIGIN_ORDER` gains a last, weakest element `ORIGIN_UNKNOWN = "unknown"` (never a record provenance).
  A leaf or stated value with a value must carry non-empty `origins`, unless its evidence is `NEUTRAL` or its row's
  `filled_by.family` is `CALENDAR` (a value that rests on no data). `()` is never read as "adds nothing": the
  evaluator refuses it (`STRUCTURE_ORIGIN`). A provider that cannot name a provenance passes `(ORIGIN_UNKNOWN,)`
  explicitly; the evaluator never infers it. Enforced in the evaluator only (`_check_leaf`, the one door every leaf
  and stated value passes); the registry holds no values, and the exemption is read from the row.
- **Why.** F3 of `.agent/review-4b1-r1.md`. D-4B.2 and the P3B rule (the weakest part sets the label; nothing is
  shown stronger than its evidence) fail when a part with an unknown origin adds nothing to the union: a total over
  emulated records and an untagged snapshot read "source-emulated", though the snapshot could be simulated. Ranking
  `unknown` weakest makes the label honest; refusing `()` turns a provider that forgot to tag into a failure, not a
  stronger label (the class is "silent absence of provenance", W6). A calendar count and an option-only neutral have
  no data beneath them, so they carry no origin and are the only exemptions.
- **Consequences.** `ProductLeafSource` (4b1's fix round, not 4b2): the snapshot leaf and the declared-price leaf carry
  `(ORIGIN_UNKNOWN,)` (neither reader exposes a record provenance today; plumbing it is backlog, not 4b);
  `period_days` (CALENDAR) and `NEUTRAL` leaves keep `()`. On a value, `weakest_origin` returns `None` only when
  nothing beneath it is data. `5a` and `5c` read `"unknown"` as no stronger than `"demo-simulated"`: any rule that asks
  "is this recorded?" answers no.

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, on `handshake.md` at `4da3a0dc6`. Each answer is folded into `spec.md` rev 2 and
`reviewer-guide.md` rev 2. Every gate named below has a plant that fails it.

- **R1 (High).** Accepted. S6 adds two pairs whose alphabetical and `ORIGIN_ORDER` orders differ: `om`
  `("demo-simulated",)` with `staff` `("source-emulated",)` gives `cost_to_serve.origins == ("source-emulated",
  "demo-simulated")` and `weakest_origin == "demo-simulated"`; `om` `("field-integrated",)` with `staff`
  `("observed-financial",)` gives `("observed-financial", "field-integrated")` and `"field-integrated"`. S5 adds the
  refusal of `("demo-simulated", "source-emulated")` (alphabetical, wrong in `ORIGIN_ORDER`). V5 names these three
  assertions; the alphabetical plant fails all three, and a `weakest_origin` planted as the alphabetical maximum fails
  both `weakest_origin` assertions.
- **R2 (High).** Option (b), D-4B.13: §3.4 gains a "Names when absent" column (`READ_AS`), with literals `CHARGE_RECORD
  = FilledBy("COMMERCIAL_RECORD", "CHARGE", "Billing export: the month's charges")` and `RECEIPT_RECORD =
  FilledBy("COMMERCIAL_RECORD", "RECEIPT", "Receipts for the month, with their payment status")`. Test 7 asserts
  `record_kind`, family, cause, words and note for both leaves in (a) and (b), and adds (c), Mto (neither CHARGE nor
  RECEIPT): `outstanding` names CHARGE, `NOT_CONNECTED`, note `NEEDS:CHARGE`; `in_transit` names RECEIPT, note None.
  Test 10 checks every absent value against `READ_AS`. Plant V19 (build `Missing` from `filled_by` for every leaf)
  fails 7(a) and 7(c).
- **R3 (High).** Accepted, D-4B.14: diesel_price has its own order of judgement (§3.3). Test 2 reads Kobo November
  twice: (i) before any November fuel invoice, `diesel_price` is the fallback's 1.30, `ESTIMATED`; (ii) after
  ingesting `KOBO-EX-FUEL-1105` (§5 test 2's literal), `diesel_price` and `fuel_cost` have no value, `NOT_RECEIVED`,
  note `MONTH_OPEN`. V10 adds "fall back in an open month with invoices", failing 2(ii).
- **R4 (Medium).** Kept, with a test that can fail: test 11(b) reads Kobo October inside
  `decimal.localcontext(Context(prec=3))` and asserts `revenue`, `fuel_cost` and `outstanding` as `format(v, "f")`
  text (`"3458.00"`, `"1475.00"`, `"278.00"`) and `diesel_price == Decimal("1.25")`. A sum under the ambient context
  gives `3.46E+3`. If a 3A4 or 3B3 path fails under it, that is a mid-build question, not a reason to drop the test.
- **R5 (Medium).** Accepted, D-4B.15; new test 12 (Mto with a 0 L fuel invoice). Plant V17.
- **R6 (Low).** Accepted. V7 fails test 1 only. V11 fails test 7(b) and test 2(i) (`om` in November before the
  invoice: judged by month, EXPENSE reads `NOT_CONNECTED`, not `MONTH_OPEN`).
- **R7 (Low).** Accepted: new test 13, the L1 pattern (`test_3b3_structure_evaluate.py:784`): the commercial builder
  raises, the snapshots and prices stores are each disposed once; a good build's `dispose()` disposes all three once.
  Plant V20 (no disposal on the third builder's failure).
- **R8 (Low).** The bullet defers to the table; D-4B.16: a refused stated record (`NOT_CALCULATED_YET`) blocks. New
  4b1 test S10; plant V16.
- **R9 (Low).** Accepted: for a recorded zero, the currency and step 4's check run over all AMOUNT lines of the needed
  kind (any status); sources and origins over all lines of the needed kind, as rev 1.
- **R10 (Low).** Accepted: test 1 reads `Docs/demo-sprint/product-direction-layer4/derived-values.json` (parsed with
  `parse_float=Decimal`), `sites["lakeside-power/Kobo"]["actual"]["nodes"]["contribution"]`, and asserts it equals
  Kobo's `contribution` value. The file today gives `883.0`.
- **R11 (Low).** Accepted: the probe counts one `site_month` and one `latest_revisions` per Site read.
- **R12 (Low).** Accepted: S8's `diesel_l` plant is `FilledBy("COMMERCIAL_RECORD", "EXPENSE (FUEL)", None)`.
- **P1 (Medium).** Accepted: `test_3b3_structure_evaluate.py:652` is the fourth version edit; §2.1's sweep is `grep -rn
  '"MINI_GRID", 2\|version == 2' backend/tests`, whose only other hit is the unrelated
  `test_s3_dispatch_assessment_postgres.py:455`. Done Q8 lists the four.
- **P2 (Medium).** Accepted: 4b2 edits T6's table (`:69-80`) and its body (`:532-553`): the five new PROVIDED leaves
  are checked against a per-leaf cause (`NOT_CONNECTED`, `filled_by`), and `PROVIDED_ELSE_ASSUMED` like `ASSUMED`.
  Inside done Q8.
- **P3 (Low).** Accepted: builds on `main` at `5a2ea9974`; `build_commercial_reads` goes beside 3A2's
  `build_commercial_months`; no merge-order question remains for `composition.py`.
- **P4 (Low).** `is_money`, D-4B.17. S8 adds a planted copy of `revenue` with `tariff`'s unit (`MONEY / KWH`); plant
  V18 (any MONEY exponent) fails it.
- **P5 (Low).** Confirmed: snapshots, prices, then commercial; the L1 test stays green unchanged.

No change to scope or units: 4b1 gains S10 and the D-4B.17 check (inside its unit); 4b2 gains tests 12 and 13.

## Mid-build answers (round 1)

Architect (Claude), 2026-11-20, on `mid-build-questions.md` Q1 at `aa5e78036`. No new decision: this fixes the test
that carries D-4B.17. The discovery review of 4b1 (`.agent/review-4b1-r1.md`) did not exist when this was written.

- **Q1 (4b1, S8 / V18).** Builder's diagnosis is right: `check` runs code by code (`CODES` order, R9), so a
  `MONEY / KWH` row is refused by `STRUCTURE_COMPOSES` (D-3B3.14) or, with `NONE`, by the `composes` condition of
  `STRUCTURE_STATED`; the unit condition never decides it. **The check order stays** (fixed by the spec; moving
  `STRUCTURE_STATED` ahead of `STRUCTURE_COMPOSES` would change which code every existing bad registry reports).
  **The plant changes**, by class: a stated node that passes every earlier check and is not exactly money. S8's
  `MONEY / KWH` copy of `revenue` is replaced by two *added* rows (a test-local helper appends a copy of `revenue`'s
  row with `dataclasses.replace`: new `factor_id`, `expression` and `unit`; `composes="SUM"`, `stated_by` revenue's
  literal `FilledBy("COMMERCIAL_RECORD", "CHARGE", ...)`, every other field as `revenue`):
  - `s8_money_sq = tariff * delivered_kwh * om`, unit `MONEY * MONEY` (MONEY exponent 2, no denominator);
  - `s8_money_kwh = om * delivered_kwh`, unit `MONEY * KWH` (MONEY exponent 1 plus another dimension).
  Each asserts `STRUCTURE_STATED` with `factor_id` equal to the planted ID, and a control asserts that the same two
  rows *without* `stated_by` pass `STRUCTURE_STATED` (so the refusal is the unit, not the row: the control may stop
  at a later code, never at `STRUCTURE_STATED` or an earlier one). Plants: **V18** (refuse only units with no MONEY
  exponent) fails both; new **V18b** (accept a MONEY exponent of 1 whatever else the unit holds) fails
  `s8_money_kwh`. The packet records both plants. `spec.md` S8 and `reviewer-guide.md` V18 are amended to match.

## Review answers (r1)

Architect (Claude), 2026-11-20, on `.agent/review-4b1-r1.md` at `aa5e78036`. One new decision (D-4B.18). Built in
4b1's fix round on this branch, before 4b1 merges: so before 4b2 branches and before 5a or 5c read `origins`.

- **F3 (origins of a valued part; D-4B.18).** Rule above. Built in 4b1 (spec §2.2, §2.5, §2.7 S6 and S11; 3B3 test
  edits listed in §2.7's regression line). Plants that must fail (guide V21 to V24):
  - **V21** `_check_leaf` accepts `()` on a valued, non-NEUTRAL, non-CALENDAR leaf or stated value (or maps it to
    `unknown` silently): fails S11(a).
  - **V22** `ORIGIN_UNKNOWN` dropped from `ORIGIN_ORDER`, or ranked anywhere but last: fails S6 (order) and S11(b).
  - **V23** the exemption keyed on evidence (`DERIVED`, or any class) instead of `family == "CALENDAR"`: fails S11(a)
    (a `DERIVED` `outstanding` with `()` is refused) and S11(c) (`period_days` with `()` accepted).
  - **V24** `ProductLeafSource` returns `()` for the snapshot or the declared price: fails `test_t6_prices` and
    `test_t6_unserved_critical_needs_a_closed_fully_covered_month` (both edited to expect `(ORIGIN_UNKNOWN,)`).
- **F4 (spec text).** §2.7's regression line corrected: the four version edits of §2.1 (two in
  `test_3b3_structure_evaluate.py`, `:366` and `:652`), plus D-4B.18's edits.
- **F1 / V18.** Already answered (mid-build Q1, `2a6386689`). The reviewer's `revenue * om` on `contribution` (a
  `_plant` of an existing row, no new row) isolates the same condition, but it gives one plant where V18b needs two
  shapes (`MONEY^2` and `MONEY * KWH`) and their no-`stated_by` controls. **The Q1 ruling stands unchanged**: the
  builder writes the two added rows as ruled.
- **F2.** Builder's, as the reviewer gives it (no ruling needed).
- **Note to 5a.** Every valued `LeafValue` 5a builds (budget lines) names its line's record provenance; 5a's expected
  `contribution` origins `("source-emulated",)` hold because 3B3's `pack_leaves` now tags `("source-emulated",)`.
- **F3 (fixture declarer literal).** Applies the 5a Q2 ruling (D-5A: the fixture declarer is a `service:` name everywhere) to 4b by class. `"test:4b"` becomes `"service:test-4b"` in the fixture, both test files and spec §4.1/§5; `PG_ENTERED_BY` is removed; mid-build Q2 is answered.
