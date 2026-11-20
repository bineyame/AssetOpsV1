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

## Handshake answers (round 1)

None yet.
