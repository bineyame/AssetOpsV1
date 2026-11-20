# 5a handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md`, `rulings.md` and `structure-page-P5.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Fresh Claude reviewer, 2026-11-20, against `caafe4212` (spec rev 1, D-5A.1 to D-5A.12, P5, reviewer guide rev 1).
No High: every planted violation can fail a named test, and every honesty rule asked about (unknown never 0, the
weakest part, a target with no line, k of n) has a test that can fail. Numbering is R/P as the dispatch asked.

- **R1 (Medium, done). `AT_ACTUAL` is barely exercised, and V10's named gate fails only by accident.** §5, test 3,
  guide V10. `FakeActual`'s `diesel_price` is already `ESTIMATED` (3B3's assumed form), so "take the actual's
  evidence" leaves `diesel_price` `ESTIMATED` and test 3's named row passes. The plant fails only if it keeps the
  `ASSUMPTION` `Missing` on a leaf whose actual is RECORDED (`productive_kwh`, then `evaluate` refuses
  `STRUCTURE_EVIDENCE`), and `productive_kwh` is not in §5's table. No fixture exercises `AT_ACTUAL` on a cost
  (every Site has `om` and `staff` lines). Expected: §5's Kobo table adds `productive_kwh` 0, `ESTIMATED`,
  `AT_ACTUAL_TEXT`, sources `("assumption:at-actual",)`; one case drops a Site's `staff` line and asserts the
  `AT_ACTUAL` target; the guide names `productive_kwh` for V10.
- **R2 (Medium, owner via P5). A cost with no budget line is taken at its actual.** §3.1 puts `om` and `staff` under
  `AT_ACTUAL`; P5 rule 3 and D-5A.5 say "prices and other drivers". O&M and staff are costs, not drivers, and taking
  them at actual puts no gap on an overspend, the opposite of the leak rule. Expected: either they stay `AT_ACTUAL`
  and P5 rule 3 names costs explicitly for the owner, or a cost without a line is "not available" (no target, the
  budget line that would set it), as D-5A.10 does for an unsolved heading.
- **R3 (Medium, done). The declarer when a person re-accepts an unchanged budget.** D-5A.2 takes the intake that
  wrote the latest revision. An upload whose lines are unchanged writes no revision (3A1's `UNCHANGED`), so a budget
  first bulk-loaded (`loader:ds3`, `person_id` None) and then accepted by a person through 3A2 still reads "no person
  declared it". Step 5's gate ("is the declarer recorded?") then depends on load order. Expected: a ruling (keep the
  latest revision's intake, or the latest intake that carried the record, which `store.intake` alone cannot answer)
  and, if it changes, a test.
- **R4 (Low, done). Test 4's last clause can never hold.** "the leaf is in `blocks_of(reg, (leaf,))`": `blocks_of`
  never returns its start (`evaluate.py:136-148`). Expected: "the heading is in `blocks_of(reg, (leaf,))`".
- **R5 (Low). Open months on the target side.** `BudgetLineReader` never reads `amounts.closed`, which is right for
  budgets (declared ahead), but the spec does not say so; `AT_ACTUAL` leaves follow the actual side, where 4b gives
  an open month no value except `diesel_price`'s fallback (4b handshake R3). Expected: one sentence that a target
  exists for an open or future month, and that `AT_ACTUAL` follows the actual's open-month answer.
- **R6 (Low). A blocked stated heading can still get a computed target.** §3.2 step 4 passes the heading absent
  with the `BUDGET_VERSIONS` or `DUPLICATE_DECLARATION` note; 4b1's table row 2 then serves the expression's value
  when it has one and drops the note. For MINI_GRID that needs a `delivered_kwh` or `necessary_l` LEAF line beside a
  duplicated heading. Expected: the ruling that this is not "picking" (the computed target is labelled by its
  parts), or that a blocked heading stays absent.
- **R7 (Low). Rule 1 counts versions over every candidate, including `NOT_A_FACTOR` lines.** A stray non-factor
  line of another version blocks the whole Site-month. Expected: intended, or rule 2 runs first.
- **R8 (Low). When does unit 1 start?** Status and §0 say code waits for P5's approval; D-5A.12 says no code
  *merges* before it. Expected: one wording.
- **R9 (Low). §9's Unit column reads "1" on all three rows.** Expected: 1, 2, 3 (each one unit).
- **R10 (Low). Kisiwa's −60.00 contribution line is a planted disagreement.** The pack's plan says −65.00
  (`derived-values.json`); the fixture's `_note` should say the −60.00 is deliberate, so nobody "fixes" it.

## Implementer pre-flight questions

Pre-flight of `spec.md` against `main` at `caafe4212` (3B1, 3B3, 3A1, 3A2, 3A4 merged; 4b1 not yet). Numbered P.

- **P1 (Medium). `store.intake` returns an `IntakeSummary`, not an intake row.** §2's declarer join reads
  `intake.entered_by`; `CommercialStore.intake` returns `IntakeSummary | None` (`commercial/store.py:42`,
  `model.py:147`), so the fields are `summary.intake.entered_by` and `.entered_at`. Expected: the spec says so, and
  what `None` means (a `RuntimeError` like a used line without its revision, by the same reasoning).
- **P2 (Low). Two commercial stores in one service after 4b2.** `build_target_read` builds `build_structure_read`
  (which, after 4b2, holds a `PostgresCommercialStore`) and `build_commercial_reads` (a second one). Expected:
  accepted as is, or 4b2 exposes its reads so 5a reuses them.

Sequencing on `4b1`, checked: unit 1 uses only `main` (`CommercialMonths`, `latest_revisions(kind=,
recognition_period=, known_at=)`, `REGISTRIES`, `MonthStamp`) and builds no `LeafValue` with `origins`; units 2 and 3
need 4b1's `stated_by`, `evaluate(..., stated=)`, `origins`, `computed` and `detail_missing` (test 3 asserts all
of them) and `build_commercial_reads` (unit 3), so D-5A.11's split holds. Units 2 and 3 do not depend on 4b2: the
Postgres test 2's `contribution` 1,445.00 rests only on budget lines, whichever actual side `main` wires.

Verified, no question: BUDGET_LINE `MonthLine` dims are `(factor_id, version_ref, line_ref)` (`months.py:42`), a
repeated key gives `value None` and `DUPLICATE_DECLARATION`, `unit` is None for node factors; 2a checks a budget
line's currency only for leaf factors (`records_v1.py:676-681`), so test 2(c)'s `revenue` line without currency can
be ingested; `MonthsMemoryStore` and `MemoryCommercialStore.intake` cover the reads; 3A2 writes
`person:{person_id}` (lower-case UUID text, which the regex matches). DS1b step 1: `build_records(view_v1, ...)`
writes exactly six October plan lines (`om`, `staff` for each Site), `version_ref` `budget-2026-v1` (the same as
step 2, so no `BUDGET_VERSIONS`), `line_ref` the factor, values as §5. Hand figures recomputed: Kobo 3,420.00 −
(875.00 + 600.00 + 500.00) = 1,445.00; Kisiwa 4,125.00 − (2,990.00 + 700.00 + 500.00) = −65.00 against the line's
−60.00 (check `False`); Mto 2,240.00 − 1,325.00 = 915.00; portfolio 2,295.00 3 of 3, and revenue 9,785.00, fuel
cost 4,240.00, O&M 1,800.00, staff 1,450.00, cost to serve 7,490.00, litres 3,300 equal the pack's
`portfolio.lakeside-power.plan.sums`; `necessary_l` 875.00 / 1.25 = 700, 2,990.00 / 1.30 = 2,300, 375.00 / 1.25 =
300; test 7's 1,380.00 and its eight out leaves; test 5(a)'s 3,420.00 / 0.40 = 8,550; P5's Kobo gap −562.00 = +38.00
− 600.00. The rule table covers the 31 leaves exactly (14 + 11 + 2 + 3 + 1).

## Architect

Round 1 answered, 2026-11-20: every R and P question in `rulings.md` "Handshake answers (round 1)", folded into
`spec.md` rev 2 and `reviewer-guide.md` rev 2. No question is open unless round 2 adds one.
