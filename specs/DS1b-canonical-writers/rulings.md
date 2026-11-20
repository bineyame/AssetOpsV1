# DS1b rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines: `.ai/decisions/index-rulings-7.md`.
Handshake answers go below under "Handshake answers (round 1)".

## D-DS1B.1 DS1b writes month cost lines and budget lines, nothing finer

- **Ruling.** DS1b writes the O&M, staff and maintenance EXPENSEs, customer-compensation ADJUSTMENTs and BUDGET_LINEs
  at month grain, for July to October. It writes no customer charge, receipt, settlement, reading or utility line.
- **Why.** Those are the records the month-grain history already determines exactly. Customer-level and day-level
  records need `DS2`'s day split and `3A3`'s per-source shapes. Writing them now would invent a split that a later
  slice must then match.

## D-DS1B.2 `world/leaves.py` keeps its set; D-2A.8 amended

- **Ruling.** `MONEY_LEAVES` stays as it is and is documented as history record-field names. Factor IDs come only
  from `assetops_contracts.canonical`. DS1b's mapping from field to leaf is `PASS_THROUGH` and `ACTUAL_WRITERS`.
- **Why.** The history's fields (`unbilled_mapping_kwh`, `offpeak_kwh`, `total` and so on) are record names, a
  different namespace from factor IDs. Replacing the set would change `history.json`, which must stay byte-identical
  (DS1). D-2A.8 said DS1b "switches" `leaves.py`. The switch is this: the mapping now lives in DS1b, and `leaves.py`
  says it is not the factor catalogue.

## D-DS1B.3 A zero liability writes no row; a zero cost line does

- **Ruling.** A `liability` of 0 writes no ADJUSTMENT. An `om`, `staff`, `maint` or `maintenance` of 0 writes a
  0.00 EXPENSE.
- **Why.** `liability` is ZERO_WHEN_HELD (manifest `leaf_sources`): a held source with no credit note means zero. Cost
  lines are MISSING when absent, so a zero cost must be a row, or it would read as missing.

## D-DS1B.4 Budget lines follow the evaluator's first-present rule

- **Ruling.** A plan field becomes a BUDGET_LINE only for the leaf whose `factor_map` passes it through, the first
  present alternative winning. Plan fields that no leaf reads are not written.
- **Why.** The budget lines then hold exactly the targets the evaluator used for the demonstration, so the structure
  read's target side, when it reads them, reproduces `derived-values.json`. Plan totals (`contribution`, `revenue`,
  Ruiru's `total`) are stated or derived figures, or targets above factor level. Writing them would make a total an
  input, against D-DS1.4. A leaf with no line reads as the owner's "labelled assumption" (20 Nov, item 6).

## D-DS1B.5 The records are `source-emulated`

- **Ruling.** Every batch's provenance is `source-emulated`.
- **Why.** D-DS1.10 rev 2: *Emulated* arrives with DS1b's source-shaped records. They stand in for an operator's
  export, which is what `3A5` labels *Emulated*.

## D-DS1B.6 Tests stay in `simulator/tests/world`; the merge gap is a tools item

- **Ruling.** DS1b's tests sit beside DS1a's, which own the fixture view and the golden option. The coordinator runs
  `simulator/tests/world` by hand at this merge. A small tools item, proposed to the coordinator, adds
  `simulator/tests` and `contracts/tests` to the merge runner and to `select-tests`.
- **Why.** Moving them into `backend/tests`, as D-2A.10 did, would make a backend test file import the simulator. The
  class (tests outside `backend/tests` never run at merge) is better closed once, in the tools, than per slice.
