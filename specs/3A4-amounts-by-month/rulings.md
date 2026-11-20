# 3A4 rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines: `.ai/decisions/index-rulings-9.md`.
Handshake answers go below, under "Handshake answers (round 1)".

## D-3A4.1 Money by month is a read over latest revisions; nothing is stored

- **Ruling.** `CommercialMonths` computes every month on each call from `latest_revisions`. No table, no stored
  total, no migration. Only the six money kinds are read.
- **Why.** A stored total is a second copy that can disagree with the records (D-3B3.5's rule: no stored figure as a
  source). Pilot volumes are small. `3B7a` owns serving reads from snapshots.

## D-3A4.2 A record's month is its recognition month; a settlement without one, its Site-local settlement month

- **Ruling.** As spec §3.2. Month bounds follow 3B3's `month_window` (P3) and a test proves they agree.
- **Why.** P3A rule 2: a late record changes its own month. 2a lets a SETTLEMENT omit `recognition_period`; mobile
  money settles after midnight, so the Site's own calendar decides, never UTC.

## D-3A4.3 Never summed across currency, unit or evidence origin

- **Ruling.** Currency, unit and provenance are part of each line's key.
- **Why.** Nothing is converted (D-3B3.16), and "simulated and observed values never share a number" (integration
  design, labels). Evidence words come from the record (P3A rule 7), so a line has one origin.

## D-3A4.4 Budget lines are listed, never summed

- **Ruling.** One DECLARED line per `(factor_id, version_ref, line_ref)`; two records on one key give no value and
  the note `DUPLICATE_DECLARATION`.
- **Why.** A budget value may be a rate (`diesel_price`), and summing rates is meaningless. Which version governs is
  `5a`'s choice; this read only reports what was declared.

## D-3A4.5 No record, no line; a recorded zero is shown

- **Ruling.** A heading with no placed record is absent. A line whose records sum to 0 shows 0.
- **Why.** P3A rule 5 and the owner's rule "missing data lowers confidence but still computes; a contributor of zero
  is shown as zero" (RULES §1). `4b` turns an absent heading into its `Missing` with the record that would fill it.

## D-3A4.6 "Out of date" is a stamp, not a table

- **Ruling.** Each month read carries a digest of the revisions placed in it. `stale()` compares; `months_touched()`
  names the months an intake changed, including a month a record left.
- **Why.** P3A: "October's figures are then marked for recalculation". A digest over contributing revision IDs is
  exact (it changes on a new record, a revision, a move in or a move out, and on nothing else), needs no write and no
  trigger, and lets `3B7a` keep its own record of what it read. A "late" flag per record says nothing (every October
  bill is recorded after October closes), so none is kept (queue Q2).

## D-3A4.7 `known_at` reads the month as it was known

- **Ruling.** `known_at` limits the candidate revisions to those recorded by then, before "latest" is picked.
- **Why.** 3B3's `ReadContext.known_at` is the read's cutoff; a replay or a snapshot "as of" must not see a later
  correction. Picking latest first and filtering after would drop a record whose later revision is too new, instead
  of showing its earlier one.

## D-3A4.8 The structure provider is `4b`'s, not `3A4`'s

- **Ruling.** 3A4 adds no `LeafSource` provider and imports nothing from `structure/`. `4b` maps lines to leaves and
  changes `SOURCE_STATE`. This amends the note in 3B3's spec §0 ("`3A4` ... will later register a commercial
  provider").
- **Why.** The re-cut (§0.1 rows 3 and 8) gives "money leaves from records into the structure read" to `4b`. Keeping
  `commercial` free of `structure` also avoids an import cycle when `4b`'s provider imports `commercial.months`.

## D-3A4.9 Exact sums, or an error

- **Ruling.** Sums run under a 200-digit context that traps `Inexact` and `Rounded`.
- **Why.** 2a's decimals reach 32 characters with exponents within ±12; Python's default 28 digits would round a
  real sum silently. A money figure that cannot be exact must fail, not drift.

## D-3A4.10 A line's key holds its basis; an AMOUNT has no unit and a QUANTITY no currency (handshake R3, R4)

- **Ruling.** The line key is `(kind, dims, measure, currency, unit, provenance, basis)`. AMOUNT lines have
  `(currency = amount.currency, unit = None)`, QUANTITY lines `(currency = None, unit = quantity.unit)`, DECLARED
  lines as §3.3. `basis` sorts last, `RECOGNITION_PERIOD` before `SETTLED_AT`.
- **Why.** A line must say one thing. A settlement placed by its recognition month and one placed by its settlement
  instant answer different questions, so one line with one `basis` would mislabel one of them. Money never carries a
  unit and a quantity never a currency, or one FUEL invoice with litres and one without would never meet.

## D-3A4.11 "Closed" is judged at the read's cutoff (handshake R5)

- **Ruling.** `closed = (known_at or clock()) >= hi`.
- **Why.** A read "as known on" an instant must answer as it would have then, as 3B3's `ProductLeafSource` does; a
  month read as of a day inside it was open.

## Handshake answers (round 1)

Answered once, 2026-11-20, and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. "Adopted" means the
writer's expected answer is the ruling. **Estimate unchanged: 2 units.**

**The High**
- **R1: adopted, with other values.** The reviewer's `99999999999999999999.99999999999` is refused by 2a (its
  `adjusted()` is 19; 2a admits -12 to 12). Test 6 adds two ADJUSTMENTs of one `reason_code`,
  `"1000000000000.000000000000000001"` (32 characters, adjusted 12) and `"0.000000000001"` (adjusted -12), whose exact
  sum is `"1000000000000.000000000001000001"` (31 significant digits). Python's default context gives
  `1000000000000.000000000001000`, so **V9** fails test 6. Checked by hand against `_check_decimal` and both
  contexts. The old pair stays as a within-28-digit case.

**The Mediums**
- **R2: "before".** `PROVENANCE_ORDER` stands: `observed-financial` reads first (strongest evidence first, as `4b`
  shows it). Test 5 says the observed line comes **before** the emulated one.
- **R3: adopted** (D-3A4.10). Test 1 asserts `currency` and `unit` on every line. Plant **V10** (an AMOUNT line
  carries the quantity's unit) fails test 1.
- **R4: `basis` joins the key** (D-3A4.10). Test 3 adds a SETTLEMENT `KOBO-ST-1101`, `provider` `mobile-money`,
  `recognition_period` `2026-11`, 40.00: November then has two `SETTLEMENT mobile-money` lines, 40.00
  `RECOGNITION_PERIOD` first, 60.00 `SETTLED_AT` second. Plant **V11** (drop `basis` from the key) fails it.
- **R5: adopted** (D-3A4.11). Test 2 adds October read with `known_at = 2026-10-31T20:00:00+00:00` (before October's
  end in Nairobi, 21:00 UTC): `closed` false, `lines == ()` (nothing was recorded by then). The §4 `known_at` read
  (5 November) stays `closed` true. Plant **V12** (`closed` from the clock only) fails test 2.
- **R6: the same rule** (D-3A2.16). Every public method of the Postgres adapter, the three reads here included,
  carries 3A2's `_scrubbed`. If `3A4` merges first, the decorator does not exist yet and `3A2` decorates these three
  when it merges; if `3A4` merges second, it decorates them and runs 3A2's service test 21 after merging `main`.
  Stated in both specs.
- **P1: confirmed.** A `NairobiSeeder` subclass of 3A1's `Seeder` in the 3A4 Postgres file overrides `add_site` to
  insert `timezone 'Africa/Nairobi'`; 3A1's file is not edited.

**The Lows**
- **R7: as written.** Two declarations of one `(factor_id, version_ref, line_ref)` under different currencies or
  origins are two lines, each with its value; `5a` decides (its spec must detect a repeated triple across lines).
  Reason: currency and origin are part of the key by D-3A4.3, and a duplicate across keys is a budget-reading
  question, not a sum.
- **R8: adopted.** The plants are named by file and function in reviewer guide rev 2: **V1** moves the period filter
  into the `DISTINCT ON` subquery of the adapter's `_LATEST` and fails Postgres test 3 (new: `latest_revisions(...,
  recognition_period="2026-10")` after F does not hold `KOBO-CH-0004`); **V2** moves the `known_at` clause outside
  the subquery and fails Postgres test 1 (the `known_at` read), and planted in `MonthsMemoryStore.latest_revisions`
  fails no-database test 2.
- **R9: adopted.** `KOBO-ST-1030`'s `provider` is `mobile-money`.
- **P2: wait, as written.** The branch starts after `3B3` merges.
- **P3: as written.** "At most two statements" and "one parse per placed revision" are review probes, not gates;
  the packet says so.
