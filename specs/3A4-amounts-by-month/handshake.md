# 3A4 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Fresh Reviewer (Claude), 2026-11-20, after `spec.md`, `rulings.md`, `reviewer-guide.md` and P3A rules 2, 5, 7.
Severity: High blocks coding; Medium needs an answer; Low may be answered "as written". The §4 expected tables were
recomputed by hand and agree (19 lines; `received` 1/5/6/2; the `known_at` read 19 lines, 6/5; stamps and
`months_touched` for B, D, E, F).

- **R1 (High, done). Reviewer guide V9, §6 test 6, D-3A4.9: the default-context plant cannot fail.**
  `Decimal("1000000000000") + Decimal("0.000000000001")` has 25 significant digits, inside Python's default 28, so
  it is exact under the default context too; `5.00 + -5.00` likewise. V9 passes every test. Expected: test 6 adds a
  sum that needs more than 28 digits within 2a's 32-character limit, e.g. `"99999999999999999999.99999999999"` +
  `"0.000000000001"` = `"99999999999999999999.999999999991"` (the default context gives
  `100000000000000000000.0000000`), and V9 names it.
- **R2 (Medium, done). §6 test 5 contradicts §3.3's sort.** Test 5 wants the `observed-financial` OM PAID line "after
  the emulated one", but `PROVENANCE_ORDER` puts `observed-financial` first. Expected: "before", or the order
  reversed (and the ruling says which reads first for `4b`).
- **R3 (Medium, done). §3.3: the `currency` and `unit` slots of AMOUNT and QUANTITY lines.** The key is `(kind, dims,
  measure, currency, unit, provenance)` but the spec does not say that an AMOUNT line's `unit` is None and a
  QUANTITY line's `currency` is None. If an AMOUNT line carried the record's quantity unit, a FUEL expense with litres
  and an OM expense without would never meet, and two FUEL invoices could split by unit on their money line.
  Expected: AMOUNT has `(currency=amount.currency, unit=None)`, QUANTITY has `(currency=None, unit=quantity.unit)`,
  and test 1 asserts both slots on every line.
- **R4 (Medium, done). §3.3, §3.5 `MonthLine.basis`: basis is not in the key.** A SETTLEMENT with
  `recognition_period` and one without, same `provider`, land on one line with a single `basis`. Expected: `basis`
  joins the key (so the two show apart), or the line carries the basis of each record (`bases: tuple`), with a test.
- **R5 (Medium, done). §3.5 `MonthAmounts.closed` with `known_at`.** `closed` is `clock() >= hi` even when `known_at`
  is given; 3B3's `ProductLeafSource` decides "has the month closed" from `known_at` when given and from the clock
  only otherwise. An "as known on 31 Oct" read of October would say closed. Expected: `closed = (known_at or
  clock()) >= hi`, with a test on the `known_at` read.
- **R6 (Medium). §2: the store-error rule for the three new reads.** `3A2` (D-3A2.2, its §3.5) widens the adapter so
  every non-connection `DBAPIError` leaves as a scrubbed `StoreRefused`; 3A4 adds reads to the same adapter in
  parallel and says nothing. Expected: the same rule for `latest_revisions(known_at)`, `intake_revisions` and
  `site_zones`, whichever unit merges second applying it, stated in both specs.
- **R7 (Low). §3.3 D-3A4.4: conflicting budget declarations that do not share a key.** Two declarations of
  `diesel_price` for one `(version_ref, line_ref)` in USD and in KES (or under two provenances) give two lines, each
  with a value and no note. Expected: as written (`5a` decides), or `DUPLICATE_DECLARATION` on both when
  `(factor_id, version_ref, line_ref)` repeats across keys.
- **R8 (Low). Reviewer guide V1, V2: where the plant goes.** `site_month` filters the period in Python and the
  no-database file uses the test subclass's `latest_revisions`, so V2 planted in the adapter fails only the
  Postgres file's test 2, and V1 has no single obvious site. Expected: name the file and function for each plant
  (V1 in `months.py`, V2 in the adapter's `_LATEST`, failing the Postgres file).
- **R9 (Low). §4 step B.** `KOBO-ST-1030`'s `provider` is not stated (the expected table implies `mobile-money`).
  Expected: state it.

## Implementer pre-flight

Pre-flight against `main` at `e39e617df` and `task/3B3-structure-read` at `7f0ca4804`. Numbered P… for this round
(the preamble's I…). Checked and found as cited, no question: `latest_revisions`' `_LATEST` (latest per record in
the `DISTINCT ON` subquery, filters outside, so §2's clause goes in the inner `WHERE`); `RevisionRow` has
`recognition_period`, `settled_at`, `recorded_at`, `supersedes_revision_id`; `site.timezone` is `NOT NULL`
(`0001`); `month_window(month, tz)` returns `(lo, hi, first, last)` on the 3B3 branch; `LEAF_FACTORS` has
`diesel_price` (`MONEY/L`) and `staff` (`MONEY`) and not `diesel_l` (so its unit None is right and 2a admits it with
no currency); `str(Unit)` prints `MONEY/L`; source types admit every fixture kind (`billing_export` CHARGE and
RECEIPT, `mobile_money_statement` SETTLEMENT, `expense_ledger` EXPENSE and ADJUSTMENT, `budget_workbook`
BUDGET_LINE); only BUDGET_LINE and CONTRACT_DOCUMENT may omit `site_code`, so `portfolio_month` reading BUDGET_LINE
alone misses no money kind; `make_world` registers `lakeside-power` with `KOBO-001`; no test checks Protocol
conformance of the in-memory stores, so the 3A2/3A4 collision is textual only. No migration, as the spec says.

- **P1 (Medium). §6 Postgres file: Site time zones.** 3A1's Postgres `Seeder.add_site` inserts `timezone 'UTC'`
  (`test_3a1_commercial_postgres.py:55-57`) and may not be edited, so the 3A4 file needs its own seeder (or a
  subclass) writing `Africa/Nairobi`. Expected: a subclass in the 3A4 file; confirm.
- **P2 (Low). §0 Base.** The branch waits on 3B3's merge for one import (test 10). If 3B3's review runs long,
  may the branch start on `main` with test 10 marked to be added after the merge? Expected: no; wait, as written.
- **P3 (Low). §2 item 2 "at most two statements" and the "one parse per placed revision" probe.** Neither is a test.
  Expected: as written (review probes, not gates); say so in the packet.
