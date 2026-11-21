# 4d rulings

Architect (Claude), 2026-11-20; rev 2 the same day (D-4D.10 to D-4D.15, handshake answers below). Each ruling is indexed
in `.ai/decisions/index-rulings-13.md`.

## D-4D.1 No new intake: litres read the evidence and records the product already holds

- **Ruling.** The EMS export reaches the product as readings through the existing evidence path and is classified by
  dispatch-3.2; dips and deliveries are the existing TANK_DIP and FUEL_DELIVERY operational records; the fuel curve is
  the Foundation's generator properties. `4d` adds no intake, format or migration.
- **Why.** D-2A.7 keeps telemetry and fuel records in their formats; dispatch-3.2 already classifies running time
  under a reviewed decision table, and K3/FUEL-1 already read the generator's use and the fuel curve. Reuse on merit:
  a second classifier would give two answers to one question. An EMS export in another shape needs a field profile
  (queued `4e`).

## D-4D.2 A litre is the measured output of a running slot at the declared fuel curve; a gap in output gives no figure

- **Ruling.** Litres of a span are `sfc × kWh + no-load rate × idle hours`, kWh and idle time from A2's slot rule
  (`use_from_readings`). If any slot of the month has no usable output or state, no litre figure is given for
  the month (`GENERATOR_USE_INCOMPLETE`). Rev 2: the month's total is taken over the whole month, not span by span
  (D-4D.11).
- **Why.** The same rule and fuel curve as K3's night check and FUEL-1's comparison, so a litre means one thing.
  Filling a gap would invent fuel; claim only what was tested.

## D-4D.3 Fuel burned while dispatch could not judge counts as necessary, never candidate

- **Ruling.** INDETERMINATE segments' litres are added to `necessary_l`; the part is kept as `indeterminate_l`.
- **Why.** Candidate litres are a claim that solar and battery could have carried the load; time not shown to be
  avoidable must not widen that claim. Leaving it out would push it into `unexplained_l`, which would call explained
  running "unexplained". Owner queue Q1.

## D-4D.4 A slot takes the class of the segment holding its start

- **Ruling.** Segments are mapped to 5-minute UTC slots by slot start; overlapping segments are a data fault
  (`SPANS_OVERLAP`, not analysed yet).
- **Why.** A2's slot rule measures 5-minute slots; one class per slot keeps each litre counted once.

## D-4D.5 The month's fuel balance runs between two tank dips within a day of the month's ends

- **Ruling.** Opening dip: the latest TANK_DIP in the 24 hours before the month starts (inclusive); closing: the
  earliest in the 24 hours after it ends (`hi <= t < hi + 24 h`, half-open as K2's read; rev 2, R11). Burned = opening + deliveries in the window − closing. Dips only; the
  fuel-level sensor stays K3's.
- **Why.** An operator's export is a manual dip at month end, rarely at midnight. The window is the dips' own, so the
  balance and the modelled litres cover the same time.

## D-4D.6 Exact until the end, then one millilitre

- **Ruling.** All arithmetic in `Fraction`; each leaf converted once at prec 34 and quantised to 0.001 L, half even.
- **Why.** Slots give repeating fractions (5/12 L); a leaf must be a finite decimal, and one rounding at the end is
  the smallest error.

## D-4D.7 Unexplained litres may be negative

- **Ruling.** `unexplained_l = burned − modelled` is shown with its sign; a negative value means the fuel curve
  states more use than the tank shows.
- **Why.** Clipping at zero would hide an over-stated curve; unknown is never zero and a measured difference is never
  hidden.

## D-4D.8 Litres are Modelled with origin `unknown`

- **Ruling.** Every litre leaf has evidence `MODELLED` and origins `("unknown",)`.
- **Why.** The figure is the output of a declared curve, not a record; readings carry no record provenance today, as
  3B3's reading-based leaves (D-4B.18).

## D-4D.9 Sources name the runs, the curve and the fuel records used

- **Ruling.** `sources`: `dispatch-run:<id>` (sorted), the SFC revision, the no-load revision when idle time was used,
  then for `unexplained_l` the dips and deliveries by time.
- **Why.** A figure names what it rests on (owner: the source is a displayed data element); a later drawer shows them.

## D-4D.10 Generator readings are checked day by day; no generator reading is "Not available yet", never 0 litres

- **Ruling.** `LitreInputs.held(a, b)` says whether any generator power or state reading has its instant in `(a, b]`.
  Rule 3 fires on `not held(lo, hi)` alone (`NO_RUNNING_RECORD`); rule 4 fires for any UTC day meeting the range that
  is `NO_READINGS` **or** has no generator reading in its part of the range (`RUNNING_RECORD_GAP`), whatever its
  dispatch state.
- **Why.** An EMS export with solar and battery columns but no generator columns gives ASSESSED days with no running
  intervals; read through spans alone, they gave 0.000 litres (handshake R1). A generator that did not run still
  reports its state, so a day with no generator reading is a gap in the record, and unknown is never zero.

## D-4D.11 Every litre the generator's readings explain is counted; spans only decide candidate or not (amends D-4D.2, D-4D.3)

- **Ruling.** `T(range)` = the litres of the generator's whole output over the range at the fuel curve, from A2's slot
  rule in UTC-day pieces. `candidate_l` = the CANDIDATE spans' litres; `necessary_l = T(month) − candidate_l`;
  `indeterminate_l = necessary_l − ` the NECESSARY spans' litres (INDETERMINATE spans plus running no span covers).
  The modelled litres of the dip window are `T(window)`. Any slot of the range with unknown output or state gives no
  figure (`GENERATOR_USE_INCOMPLETE`).
- **Why.** dispatch-3.2 intervals run from the first ON instant to the last, so the slot before the first and the
  time after the last lie in no segment (handshake R7, about 15 L a month on KOBO-OCT). Counting them as unexplained
  would call explained running "unexplained"; counting them as candidate would widen a claim nobody tested. Running
  that dispatch did not classify is "not shown to be avoidable", as INDETERMINATE (D-4D.3). A whole-range total also
  makes `necessary_l + candidate_l` equal the generator's own litres by construction.

## D-4D.12 Only a CURRENT dispatch selection is analysed

- **Ruling.** A day with a selection whose `status` is not `CURRENT` (`STALE_PROJECTION`, `FAILED`, `PENDING`,
  `UNASSESSED`) is `NOT_ASSESSED`: the month reads `DISPATCH_NOT_ASSESSED` ("Not analysed yet", NOT_CALCULATED_YET).
- **Why.** A stale run did not see the latest accepted readings (handshake R6); its litres would be served as
  Modelled while the analysis is out of date. "Not analysed yet" is exactly the pending-system-work case.

## D-4D.13 A segment class 4d does not know stops the month

- **Ruling.** `CLAIMS = ("NECESSARY", "CANDIDATE_AVOIDABLE", "INDETERMINATE")` (test 9 proves they equal
  `analytics.dispatch`'s constants). A span with any other claim gives `SPAN_CLASS_UNKNOWN` (after `SPANS_OVERLAP`,
  cause NOT_CALCULATED_YET; 5c reads it as "being analysed").
- **Why.** A new dispatch class would otherwise fall silently into necessary; the litre rule must be reviewed first.

## D-4D.14 The fuel curve must be in force over the whole dip window for unexplained litres

- **Ruling.** The curve is chosen over `[lo, hi]` (K3's choice). `FuelCurve.valid` is the interval over which the
  chosen revisions are in force; a dip window reaching outside it gives `unexplained_l` `FUEL_CURVE_MISSING`.
- **Why.** The window may run up to 24 h outside the month (handshake R12); a revision there must not be applied
  to time it does not cover.

## D-4D.15 The undecided part stays inside 4d; the screen's label says what the figure is

- **Ruling.** `indeterminate_l` is kept in `LitreMonth` (tests, invariants) and does not travel in `LeafValue`.
  5c labels `necessary_l` "Diesel not shown to be avoidable" (D-5C.16).
- **Why.** `LeafValue` has no field for a part of a value, and a `sources` entry carrying a number would be a second
  meaning for one field. The label is true of every litre in the figure; "needed" was not (handshake R8, 5c R7).

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, on `task/4d-5c-DDR-handshake` 8ce960a64. Every answer is folded into `spec.md`
rev 2. Each gate named here has a plant in `reviewer-guide.md` rev 2 that fails it.

### Reviewer

- **R1 (High).** Accepted: D-4D.10. `readings_held: bool` becomes `held: Callable[[datetime, datetime], bool]`;
  rules 3 and 4 as the ruling. New V18 (every day ASSESSED, no spans, `held` always False: all three
  `NO_RUNNING_RECORD`) and V19 (`held` False inside UTC day 2026-10-28, which is ASSESSED with no spans: all three
  `RUNNING_RECORD_GAP`). Gates: P13 (rule 3 needs both conditions) fails V18 (0.000 values); P14 (rule 4 by state only)
  fails V19.
- **R2 (High).** Accepted. The bridge world is 5b §5.2 **with** its step (`attribution_lakeside_mto.json`); the
  literals (Mto `fuel_cost` `NOT_SPLIT` `DETAIL_NOT_AVAILABLE`, portfolio `fuel_cost` −755.00 3 of 3, `diesel_l`'s
  `out` Kisiwa and Mto `("NOT_SPLIT",)`) are the with-step values and stand. Done question 2 unchanged.
- **R3 (High).** Accepted. New V20: V7 plus FUEL_DELIVERY 50 at 2026-09-30T20:00+03:00 (`del-0`, inside the window,
  before the month): burned 1250, modelled 1065, `unexplained_l` **185.000**. Gate: P5 (deliveries by calendar month)
  gives 135.000 and fails V20.
- **R4 (High).** Accepted. The case is V21: day **2026-09-29** NOT_ASSESSED gives all three `DISPATCH_NOT_ASSESSED`.
  Gate: P12 (rule 5 from `lo`) never reads 2026-09-29 and fails V21.
- **R5 (Medium).** Accepted: D-4D.13. `RunSpan.claim` holds `CLAIMS`; V23 (claim `"SOMETHING_NEW"`) gives
  `SPAN_CLASS_UNKNOWN`. Gate: P17 (unknown claim ignored) fails V23.
- **R6 (Medium).** Accepted: D-4D.12. `dispatch_spans` returns the raw day facts; `inputs.day_state` maps them
  (pure; test 10 is its table). Gate: P18 (status ignored) fails test 10.
- **R7 (Medium).** Accepted, by D-4D.11 rather than by widening intervals: the running dispatch did not classify is
  counted, as necessary (indeterminate). V24 (one running slot on 27 Oct outside every span): `necessary_l` 730.417,
  `indeterminate_l` 10.417, `unexplained_l` 119.583. Gate: P16 (`necessary_l` from spans only) fails V24 and test 3.
  Postgres test 1 needs no coverage comparison: spans no longer decide whether a litre counts.
- **R8 (Medium).** Answered by D-4D.15: out of `LeafValue`; 5c's label changes.
- **R9 (Medium).** The note stays `GENERATOR_OR_TANK_NOT_DECLARED`; its words (5c `SITE_SETUP`) become "one generator
  and one fuel tank declared in the Site's setup (litres are worked out for one of each)", which is true for Kisiwa's
  two generators and for a Site with none.
- **R10 (Low).** Accepted. V22: two NECESSARY spans 07:00–07:05 local on 13 and 14 Oct: `necessary_l` 730.833,
  `unexplained_l` 119.167. Gate: P15 (rounding each span or each day piece) gives 730.834 and fails V22.
- **R11 (Low).** Half-open, as K2's read: the closing dip is the earliest with `hi <= occurred_at < hi + EDGE`
  (D-4D.5 amended). V26: a closing dip at exactly `hi + EDGE` and none earlier gives `TANK_DIPS_MISSING`. Gate: P19
  (inclusive end) fails V26.
- **R12 (Low).** Accepted: D-4D.14; V25. Gate: P20 (no window check) fails V25.
- **R13 (Low).** Intended. Valued litre leaves are listed `untracked` by 3B7a; a corrected dip or a dispatch re-run
  after the snapshot does not mark it out of date, and 5c says so ("Not checked for later changes", World H). Rebuild
  after such a change (runbook step 9).
- **R14 (Low).** Accepted as written: between `hi` and `hi + EDGE` a read gives `TANK_DIPS_MISSING`, which is true at
  that moment ("tank dips at the start and end of the month" not yet received). Snapshots are built days after
  month end.

### Implementer pre-flight

- **P1 (Medium).** Allowed: §0 adds one `dispose()` to `PostgresAssessmentStore` (disposes `_engine`); Postgres test 3
  uses it.
- **P2 (Medium).** §0 lists `backend/tests/test_4b_money_leaves.py:55-62` and
  `backend/tests/test_3b3_structure_evaluate.py:76`; the packet's W6 sweep greps 3B7a's tests once 3B7a merges and
  edits any line pinning the old state or cause.
- **P3 (Medium).** Stated in §4.1: only assets, properties and fuel records run on the read-only transaction; readings
  and the curve histories go through the Action store's own connection, pinned by `known_at`. Postgres test 2 proves
  `c` only. Accepted for this unit.
- **P4 (Low).** The tuple in `rules.py` is `LITRE_ORDER`; `LITRE_LEAVES` is only the frozenset in `sources.py`.
- **P5 (Low).** Stated: the rules sort spans by `(start, end, claim)`; adapter order does not matter.
- **P6 (Low).** Noted in §4.3 with D-4D.11's cost: one `use` per UTC day of the range plus one per span; fine for
  Lakeside; a 300-Site build is a 3B7b concern.
