# 4d rulings

Architect (Claude), 2026-11-20. Each ruling is indexed in `.ai/decisions/index-rulings-13.md`.

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
  (`use_from_readings`). If any running slot of the month has no usable output or state, no litre figure is given for
  the month (`GENERATOR_USE_INCOMPLETE`).
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
  earliest in the 24 hours after it ends. Burned = opening + deliveries in the window − closing. Dips only; the
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
