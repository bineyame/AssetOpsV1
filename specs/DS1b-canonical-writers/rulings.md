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

## Handshake answers (round 1)

Answered once, 2026-11-20, and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. "Adopted" means the
proposed answer is the ruling.

### Highs

- **R1 (High): adopted. A budget line is written only from the leaf's own field.**
  - A BUDGET_LINE is written only when the **first** field of the leaf's `PASS_THROUGH` list is present. This is the
    evaluator's `own` rule (`evaluate_structure.py:637-650`).
  - When only a later field is present, nothing is written, and the field is listed `NOT_OWN_LINE`. This replaces
    `ALTERNATIVE_NOT_FIRST`. Those fields (`billed_kwh`, `diesel_l`, `offpeak_kwh`, `kwh`) are node-level or fallback
    figures, and targets at that level belong to `5a`.
  - A new test, T9, independent of DS1b's rule: for every October Site, no BUDGET_LINE names a leaf that
    `missing-records.json` lists on the target side as carried ASSUMPTION.
  - **Why.** The owner approved the labelled-assumption default on 20 Nov (item 6). A line written from a fallback would
    erase that label in the store. D-DS1B.4 is amended.
- **R2 (High): adopted. ESTIMATED October cost lines are not written.**
  - A §2.1 field whose October `coverage` entry of the same name is `ESTIMATED` writes nothing and is listed
    `ESTIMATED_NOT_RECEIVED`. Today that is Kisiwa `om`, Thika `maint` and Kasarani `maintenance`.
  - History months are unaffected: their coverage is RECORDED, and the evaluator ignores ESTIMATED for history.
  - T4 and T5 are updated.
  - **Why.** A PAID invoice for a line the manifest says was not received would invent a record and remove disorder test
    GAP-1 from the store. New ruling D-DS1B.7.
- **R3 (High): adopted. T3 derives the writers by a rule that reproduces §2.1.**
  - The writers are the `leaf_sources` rows whose kind starts with `EXPENSE` or `ADJUSTMENT`, whose `absent` is not
    `OPTION_ONLY`, and whose catalogue `Factor.money` is true. The history clause is dropped.
  - T3 also asserts that the kind's parenthesis matches the category: `(OM)` gives OM, `(STAFF)` gives STAFF, and
    `(credit note)` gives ADJUSTMENT.

### Mediums

- **R4: adopted.** A new reason, `READ_IN_AN_EXPRESSION`, covers a field the `factor_map` reads outside a whole
  alternative (COLD_CHAIN `kwh` through `excess_kwh`). T3 derives that set. The `excess_kwh` target is `5a`'s
  (D-DS1B.4 amended).
- **R5: adopted.**
  - D-DS1B.5 adds that the evidence word follows the path: a store record is *Emulated*, a history leaf is *Simulated*,
    and no screen shows both words for one figure.
  - T1 adds a byte check: no output contains `RECORDED`, `Recorded`, `field-integrated`, `observed-financial` or
    `bench-tested`.
  - The constant references (`om-contractor`, `payroll`, `finance-lead`) are source text. `3A5` never shows them as a
    named approver or counterparty.
- **R6: adopted.**
  - Whether a source is held is `DS3`'s to declare, from coverage per Site and month, not DS1b's. DS1b writes no empty
    batches.
  - `ZERO_NO_ROW` applies to the actual side only. Thika's plan `liability` of 0 writes a BUDGET_LINE of `0.00`: it is
    the leaf's own line and a received zero target.
  - **Architect's confirmation for `3B6`.** At Mwea and Kirinyaga, an absent `liability` reads as zero only when `DS3`
    declares the room's customer-invoicing source held for that month. Otherwise it is missing, NOT_CONNECTED, never 0.
- **R7: adopted. One canonical record per (Site, month, field).** A later slice (`3A3`, `DS2`) that writes finer
  records for the same Site, month and field either takes the month record out of `DS3`'s load or reconciles to it,
  with its sum equal to the month line. New ruling D-DS1B.8. This sentence goes into `3A3`'s spec when it is written.
- **R8: adopted, as a separate unit.** The tools item is `T2`, a 0.5-unit unit with its own spec
  (`specs/T2-neutral-package-tests/spec.md`). A check-all guard runs `simulator/tests` and `contracts/tests`, and
  `select-tests` names them. `T2` merged is a precondition of DS1b's merge (D-DS1B.6 amended). Until then, the packet
  records the by-hand run with its revision.

### Lows

- **R9: adopted.** T4 asserts that `produced_at` is later than every `occurred_at`.
- **R10: adopted.** T3 asserts that `set(STRUCTURE_KEY.values())` equals `canonical.STRUCTURE_KEYS`, and that
  `STRUCTURE_KEY`'s keys equal the keys of `history.rules`.
- **R11: adopted.** The wording becomes: a `PASS_THROUGH` or `ACTUAL_WRITERS` field in `MONEY_LEAVES` must map to a
  leaf whose `Factor.money` is true, and a field mapped to such a leaf must be in `MONEY_LEAVES`. `currency` follows
  `2a`'s MONEY-exponent rule.
- **R12: adopted.** The table stays literal. T3 splits on top-level `|` only, and asserts that no Site's
  `factor_sources` holds a `record.<field>` alternative.

### Implementer pre-flight

- **P1: adopted.** The CLI also inserts the repository's `contracts` directory on `sys.path`.
- **P2: adopted.**
  - T7 calls `build_records(planted view, history of the unplanted fixture)`. There is no view and history digest
    check.
  - The `crate_days` case is on the plan side.
  - Refusal texts carry the side: `DS1B_MONEY <tenant>/<site code>/<month> <side> <field>`, and the same for
    `DS1B_NUMBER`.
- **P3: adopted, by dropping the clause.** T6 relies on DS1a's T1 and T2 (golden and CLI digest), which already pin
  `history.json`'s bytes.
- **P4: adopted.** For a BUDGET_LINE, `<field>` in the record ID and in the sort key is the `factor_id`, and
  `body.line_ref` holds the plan record's field. Under R1 the field always equals the first field of the leaf's list.
- **P5: adopted.** `simulator/tests/world/conftest.py` gets a docstring and help-text change only. It joins §4 and the
  scope list.
- **P6: adopted.**
  - The CLI creates `DIR`. It refuses with `DS1B_OUT <reason>` when `DIR` resolves inside the repository or already
    holds a file.
  - `DS1B_*` failures exit 3; argparse keeps exit 2.
  - T2 covers both refusals.
  - The coordinator writes to `/opt/assetecon/generated/ds1b-<rev>/`.
- **P7: adopted.**
  - No `31` anywhere in `records.py`; the month's last day comes from `months.period_end`.
  - The private block's name never appears in `records.py`, the CLI or its help.
- **P8: adopted.** `world/__init__.py` says "standard library and `assetops_contracts` only".
- **P9: adopted.** A written field that is not an int or decimal text is refused `DS1B_NUMBER`. An `as_of` that is not
  a date is refused `DS1B_AS_OF`.
- **P10: adopted.** `text(c)` is `"-" + text(-c)` for any negative `c`.
- **P11: adopted.** The unwritten list uses the Site code.
- **P12: confirmed.**
  - `build_records` applies `ManifestView.from_document`, which is idempotent.
  - `site_code` is allowed on a BUDGET_LINE (2a §6.2).
  - `zoneinfo` with the system tzdata is accepted.

**Open after round 1:** none.

## D-DS1B.7 ESTIMATED lines are never written as records

- **Ruling.** As R2.
- **Why.** A record says a source sent it, and an estimate was not sent.

## D-DS1B.8 One canonical record per Site, month and field

- **Ruling.** As R7.
- **Why.** Two records for one amount would count it twice in the store.

## Mid-build answers (DS1b, 2026-11-20)

Neither case occurs in today's data. Both provisional builds are adopted, and Q2 gains one test. The code does not
change.

**MB1 (Q1): an ESTIMATED October `liability` of 0 is listed `ESTIMATED_NOT_RECEIVED`.**
- **The rule.** The ESTIMATED check comes first for every §2.1 field, so a field gets one reason, in this order:
  `ESTIMATED_NOT_RECEIVED`, then `ZERO_NO_ROW`.
- **Why.** An estimate means the source was not received. "Zero, held" would claim a held source the manifest says is
  missing (D-DS1B.7).

**MB2 (Q2): exponent text from the view is accepted and normalised. The record never carries it.**
- **Why it must be accepted.** The view writes every binary float as its `repr` (`view.py`), and `repr(0.00001)` is
  `"1e-05"`. Refusing exponent text would refuse a legitimate manifest value only because of how Python prints it.
- **What is written.** The value goes through `format(Decimal(text), "f")` (spec §3), so the record holds plain text
  (`"0.00001"`), which is 2a's canonical form (R2). Money goes through `Fraction(text) * 100` and the whole-cent rule
  as before.
- **What is still refused.**
  - A value whose plain form breaks 2a's bounds (over 32 characters, or an adjusted exponent outside [-12, 12], such
    as `"1e+30"`) is refused `DS1B_FORMAT CANONICAL_NUMBER ...` by `parse_batch`, as spec §3 says.
  - Anything else that is not an int or matches the built pattern is refused `DS1B_NUMBER`.
- **One test to add in the fix round or the review round.** T7 gains three cases:
  - an October plan `crate_days` of `"1e+03"` is written as `1000`;
  - an October plan `crate_days` of `"1e+30"` is refused `DS1B_FORMAT`;
  - no output byte string anywhere matches `[0-9][eE][-+]?[0-9]`.

The DS1b packet's mid-build count is 2.
