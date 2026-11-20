# 3B3 rulings

Architect (Claude), 2026-11-20. Each ruling gives its reason. The index lines are in
`.ai/decisions/index-rulings-8.md`. Handshake answers go below, under "Handshake answers (round 1)".

## D-3B3.1 One pure evaluator, with sources behind a port

- **Ruling.** `evaluate` is pure. Leaf values come through `LeafSource`.
- **Why.** The same evaluator then serves the parity test against the pack, the product read, the snapshot (`3B7a`)
  and option evaluation (step 6). A later slice adds a leaf by adding a provider, not by editing the evaluator.

## D-3B3.2 Evidence order, and the weakest part wins

- **Ruling.** The order, strongest first, is: RECORDED, MEASURED, DECLARED, DERIVED, ESTIMATED, MODELLED,
  NOT_AVAILABLE. A node takes the weakest of its parts.
- **Why.** P3B rule 3 says the weakest part sets the label. The order follows the design's evidence classes
  (`integration-source-to-canonical-design.md` §6.2):
  - a declared price is weaker than a measurement;
  - an estimate is weaker than either;
  - a model is weaker still.

  *Emulated* and *Recorded* (D14) are provenance labels, which `3A5` shows beside the class. They are not ranks here.

## D-3B3.3 The source state of every leaf is a literal, and states the truth on 20 Nov

- **Ruling.** `SOURCE_STATE` names every leaf as PROVIDED, HELD_NOT_CALCULATED, NOT_CONNECTED or OPTION_ONLY.
- **Why.** The cause in `missing` must be true. Where records are held but the calculation is not built, the cause is
  NOT_CALCULATED_YET. Where no intake exists, it is NOT_CONNECTED. A literal keeps this auditable, and each later
  slice changes one row.

## D-3B3.4 Only exact sources fill a leaf; a partial source does not

- **Ruling.** Only five leaves are filled today. Dispatch minutes are not litres, a night-window fuel residual is not a
  monthly unexplained litre, and an hourly mean is not delivered kWh, so those leaves stay HELD_NOT_CALCULATED.
- **Why.** Unknown is never zero, and it is never something else either. Filling a leaf from a value of a different
  scope or unit would be an invented figure (owner rule: claim only what was tested).

## D-3B3.5 No route and no storage in 3B3

- **Ruling.** The read is a service only. `3B7a` adds the snapshot and the route.
- **Why.** The design serves screens from the snapshot, never from compute-on-read (OD-23). A route here would need a
  perf budget and a cache registration that `3B7a` replaces.

## D-3B3.6 Assumptions are carried and labelled; their value comes from 5a

- **Ruling.** The evaluator carries the label and makes the nodes above an assumption ESTIMATED. Which value an
  assumption takes is decided by `5a`, from target lines.
- **Why.** The owner's labelled-assumption default (20 Nov, item 6) needs the label to reach every figure it touches.
  The pack's fallback rule ("leaks and avoidable use at zero, the rest on the main factor") needs target lines, which
  only `5a` brings.

## D-3B3.7 Division by zero is missing, never infinite and never zero

- **Ruling.** As carried from the 3B1 review: the node has no value, and its `missing` names the zero denominator.
- **Why.** An infinite or zero figure would be a claim the records do not make.

## D-3B3.8 The portfolio excludes a Site by name and sums only additive factors

- **Ruling.** A Site with no contribution is excluded, and its reasons are listed. Amounts, quantities and counts are
  summed. Prices and ratios are not summed.
- **Why.** The design says "a Site that cannot be evaluated is excluded by name" and composes Σ amounts and Σ/Σ ratios.
  A summed price would be meaningless. A weighted price is attribution, which belongs to `5b`.

## D-3B3.9 The registry gains `neutral`, which makes MINI_GRID version 2

- **Ruling.** OPTION_ONLY rows carry the manifest's literal. The version is bumped.
- **Why.** A changed row field is a new version (the protected seam's rule). The neutral value is what the observed
  sides carry for an option-only factor (structure-specification §3.1).

## D-3B3.10 Months only, in the Site's calendar

- **Ruling.** The read takes a Site-local month (`YYYY-MM`). Day and range reads are `3B7a`'s.
- **Why.** The structure is declared per period. The bridge and the cards read months. A range read would duplicate
  the snapshot's job.
