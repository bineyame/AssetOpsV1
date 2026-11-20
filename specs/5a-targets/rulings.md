# 5a rulings

Architect (Claude), 2026-11-20. Each ruling gives its reason. Index lines: `.ai/decisions/index-rulings-10.md`.
Handshake answers go below, under "Handshake answers (round 1)".

## D-5A.1 Targets are read from budget lines; one budget version governs a Site-month

- **Ruling.** The target side is evaluated from `3A4`'s budget lines for the Site and month. If the month holds lines
  of two or more `version_ref`s, there is no governing version: every line is unused (`BUDGET_VERSIONS`), and every
  factor that has a line in any version has no target, with that note.
- **Why.** P5 rule 5: never pick. An original budget and a reforecast answer different questions; choosing one is a
  person's decision, and this fortnight has no command for it (P5 question 1; queue Q1).

## D-5A.2 The declarer is the person who loaded and accepted the line

- **Ruling.** Each used line names the `entered_by` and `entered_at` of the intake that wrote its latest revision
  (`CommercialStore.intake`). `person_id` is set when `entered_by` is `person:<uuid>` (3A2's acceptance), else None
  (a bulk load), and the line says so.
- **Why.** Step 5's gate: "Is the declarer of each target recorded?" 3A2 records the accepting person as the intake's
  `entered_by` (D-3A2.4, D-3A2.13); a second record of the same fact would drift.

## D-5A.3 One line per factor; more is not available, never summed or picked

- **Ruling.** Two or more lines for one factor in the governing version (any `line_ref`, currency or origin), or
  3A4's `DUPLICATE_DECLARATION`, give that factor no target, note `DUPLICATE_DECLARATION`. A money line without a
  currency, or a quantity line with one, is blocked the same way (`CURRENCY_MISSING`, `CURRENCY_ON_QUANTITY`).
- **Why.** D-3A4.4 (budget lines are never summed; some are rates) and its R7 (5a detects a repeated factor across
  lines). Falling back to an assumption would hide a line the operator sent.

## D-5A.4 Where a line lands

- **Ruling.** A line for a leaf is that leaf's own target. A line for a node with `stated_by` (D-4B.1) is that
  heading's stated target. A line for any other node is a check: compared with the computed target, never used
  instead. A line naming no registry factor is unused (`NOT_A_FACTOR`).
- **Why.** P5 rule 2. Contribution is computed from its parts, so the screen's bridge always adds up; an operator's
  contribution line that disagrees is shown as a difference, not silently preferred.

## D-5A.5 A factor with no line of its own takes one of five literal rules, each a labelled assumption

- **Ruling.** `TARGET_RULE` names each leaf's rule: `LEAK_ZERO` (leaks and avoidable use, at 0), `AT_ACTUAL` (prices
  and other drivers, at this month's actual), `MAIN` (the main factor under a stated heading, carrying the rest),
  `OPTION` (the neutral, as on the actual side) and `CALENDAR` (the month's days). The first three are `ESTIMATED`,
  carried as `ASSUMPTION`, with literal words.
- **Why.** Owner item 6 (20 Nov): a driver with no target line is a labelled assumption. The structure specification
  §3.1 rule 2: "leaks and avoidable use are taken at zero, and the rest of the target on its main factor". Taking a
  price at its actual puts no gap on it, which is what an unstated price target means.

## D-5A.6 The main factor is solved through the evaluator, only when the heading is linear in it

- **Ruling.** With every other target known, the main leaf `m` is set so the heading's computed target equals its
  stated target: evaluate at `m = 0, 1, 2`; linear when the two steps are equal; `m = (T − v0) / (v1 − v0)` under the
  evaluator's context. Missing parts, a non-linear heading or a zero slope leave it with no target, each with its own
  note.
- **Why.** It reuses the one evaluator (D-3B3.1), so no vertical formula is written; and a solve that is not exact
  must not pretend to be.

## D-5A.7 A stated heading's target is Declared, whatever is assumed below it

- **Ruling.** The assumptions under a stated heading do not weaken it or its ancestors; they weaken only the
  branch that rests on them (e.g. `diesel_l`).
- **Why.** The heading's value rests on its own line, not on them (D-4B.1); labelling Kobo's contribution target
  *Estimated* because litres were inferred below fuel cost would mislabel the operator's own budget.

## D-5A.8 Portfolio targets are composed per factor; operator-level lines are listed, not spread

- **Ruling.** `compose` over the Sites' target structures, with `site_count` (k of n). Budget lines with no Site
  are read and classified the same way and returned as `portfolio_lines`; they are not added to any total.
- **Why.** The owner's "k of n sites" (20 Nov). Spreading a head-office line over Sites is an allocation rule no one
  has declared.

## D-5A.9 Targets are read, not stored

- **Ruling.** No table, no route. Each read carries the Site-month's 3A4 stamp (and the portfolio stamp), so `3B7a`
  can rebuild when a budget line changes.
- **Why.** D-3B3.5 and D-3A4.1: no stored figure is a source; `3B7a` stores and serves.

## D-5A.10 On the target side too, unknown is never zero

- **Ruling.** `AT_ACTUAL` with no actual value, `LEAK_ZERO` on a money leaf with no Site currency, and an unsolved
  main factor all give no target, naming the budget line that would set it.
- **Why.** P5 rule 4 and the owner's rule; an assumption needs something to assume from.

## D-5A.11 5a's evaluation builds on `4b1`, not on `4b`'s providers

- **Ruling.** Unit 1 (lines) starts at once. Units 2 and 3 start after `4b1` merges (D-4B.1). The actual side is any
  `StructureRead`; the tests use a fake source, so `4b2` is never needed.
- **Why.** D-BW1.10 cut `5a` from `4b` because 5a reads no money leaf 4b computes; it does need the stated-heading
  seam, which is shared and small.

## D-5A.12 Code starts after the owner approves P5

- **Ruling.** No 5a code merges before P5 is approved (RC3, day 3). If the owner changes a rule, this spec is revised
  before the unit it touches.
- **Why.** W1: structure first, owner-approved.

## D-5A.13 A blocked target is held but refused: cause `NOT_CALCULATED_YET`, and never computed instead

- **Ruling.** A factor in `bl.blocked` (two versions, two lines, a currency problem) gives an absent target with
  cause `NOT_CALCULATED_YET` and the blocked note. For a stated heading this triggers 4b1's blocking row (D-4B.16):
  the heading has no target even when its expression could compute one from leaf lines.
- **Why.** Handshake R6. The operator sent lines for that factor; serving a computed target in their place would pick
  for them, which P5 rule 5 forbids. `NOT_RECEIVED` would also be false: the line was received. One class with 4b's
  mixed-currency records (D-4B.16), so one evaluator row serves both.

## D-5A.14 The declarer is the intake that wrote the line's latest revision; an unchanged re-upload does not re-declare

- **Ruling.** D-5A.2 holds as written. A person who accepts an upload whose lines are unchanged writes no revision
  (3A1's `UNCHANGED`), so the line keeps its earlier declarer, and a bulk-loaded line keeps reading "no person
  declared it".
- **Why.** Handshake R3. The declarer is who put these values into the record, which the revision proves; an
  acceptance that changed nothing is on the intake, not on the line. Reading "the latest intake that carried the
  record" needs a 3A1 store read 5a may not add (5a edits no existing module), and it is not on the demo path: this
  fortnight's budgets enter once, through the budget file (owner default, 20 Nov). Queue Q6 holds the change.

## D-5A.15 A cost with no budget line is taken at its actual, labelled, and the headings above it read Estimated

- **Ruling.** `om` and `staff` stay `AT_ACTUAL` (spec §3.1). Their headings (`cost_to_serve`, and `contribution`
  above it, neither stated) then read *Estimated* by the weakest-part rule, naming the cost taken at actual. Owner
  question Q7 (spec §10) carries this with its default.
- **Why.** Handshake R2. The alternative (no target) makes a missing small cost line erase the Site's contribution
  target and its whole bridge, while P5 rule 4 is about targets that cannot be set; this one can be set, as a
  labelled assumption, and the label already stops it being read as the operator's. No gap is claimed on a cost
  nobody budgeted, which is the same reason a price is taken at actual. P5 rule 3 says "prices and other drivers";
  costs are leaves (drivers) of their heading, but the owner did not see them named, so the owner is asked.

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, on `handshake.md` at `4da3a0dc6`. P5 is approved
(`owner/owner-p5-approved-and-defaults-2026-11-20.md`), so D-5A.12 is met. Answers are folded into `spec.md` rev 2
and `reviewer-guide.md` rev 2. Every gate named has a plant that fails it.

- **R1 (Medium).** Accepted. §5's Kobo table adds `productive_kwh` 0, `ESTIMATED`, `AT_ACTUAL_TEXT`, sources
  `("assumption:at-actual",)`, currency None; new test 3(b) drops Mto's step-1 `staff` record and asserts Mto
  `staff` 450.00 `ESTIMATED` at actual, `cost_to_serve` 1325.00 and `contribution` 915.00 both `ESTIMATED` (the
  check still agrees). V10 names `productive_kwh` (test 3) and test 3(b).
- **R2 (Medium, owner).** Kept `AT_ACTUAL` with reasons (D-5A.15); new owner question Q7 with that default. Test 3(b)
  pins the labelled result, so a change of default is one rule-table edit and that test.
- **R3 (Medium).** D-5A.14: kept. New test 1(b) pins it: re-ingest step 1's batch unchanged at
  `2026-11-08T09:00:00+00:00` by `person:5a000000-0000-4000-8000-000000000002`; Kobo `om`'s line still has
  `declared_by` `loader:ds3`, `person_id` None, `declared_at` `2026-11-06T09:00:00+00:00`. Plant V14 (take the
  latest intake touching the Site's budget lines) fails it. Queue Q6 holds the later change.
- **R4 (Low).** Accepted: "the heading is in `blocks_of(reg, (leaf,))`".
- **R5 (Low).** Accepted: a target exists for an open or future month (budgets are declared ahead; `BudgetLineReader`
  never reads `closed`); an `AT_ACTUAL` target follows the actual side's answer for that month, so in an open month
  it is absent (`ACTUAL_NOT_AVAILABLE`) except `diesel_price`, which follows 4b's D-4B.14.
- **R6 (Low).** D-5A.13 with 4b's D-4B.16: a blocked heading stays absent. New test 8(c) with a `delivered_kwh` leaf
  line beside a duplicated `revenue` line; its control (no duplicate) shows the expression has a value, so the plant
  V15 (serve the expression for a blocked heading) can fail.
- **R7 (Low).** Intended (D-5A.1): any line of a second version shows two budgets were sent for the month, and
  which one governs is a person's choice; a non-factor line is still part of a budget. Rule 1 stays first.
- **R8 (Low).** One wording: no 5a code is written before P5's approval; P5 was approved on 20 Nov, so unit 1 starts
  when this handshake has no open question.
- **R9 (Low).** Accepted: units 1, 2, 3.
- **R10 (Low).** Accepted: the fixture's `_note` reads "5a spec §5; Kisiwa's contribution line −60.00 is a deliberate
  disagreement with the computed −65.00 (the pack's plan), so the check reads False; do not correct it".
- **P1 (Medium).** Accepted: `summary = store.intake(...)`; `declared_by = summary.intake.entered_by`, `declared_at =
  summary.intake.entered_at`; `None` raises `RuntimeError("budget line without its intake")`, a bug as for a used
  line without its revision.
- **P2 (Low).** Accepted as is: two `PostgresCommercialStore`s in one service, each disposed. Sharing one needs an edit
  to 4b2's `structure/composition.py`, outside 5a's scope; `3B7a`, which composes the served reads, can share them.

No change to scope or units. New owner question Q7 (default: costs with no line at actual, labelled).

## Mid-build answers (round 1)

Architect (Claude), 2026-11-20, on `mid-build-questions.md` Q1 at `e28cd1e0c`. No new decision: this places test 10.

- **Q1 (unit 1, test 10).** The builder's default is confirmed, with the details below. The guard stays as it is
  (`dependency-direction.ps1`: "Do not weaken the checks below to make a task pass"); an allowlist for
  `backend/tests` would open the product-to-simulator direction for a whole folder. The parity check is the
  simulator's claim (its generator writes what the product's fixture says it writes), so it belongs on the simulator
  side, which may read a repository file without importing the product; `simulator/tests` already runs on every
  branch and after every merge through check-all's T2 guard (`tools/checks/neutral_tests.py`), so a later edit of the
  fixture or of DS1b is still caught.
  - **Where.** New `simulator/tests/world/test_5a_fixture_parity.py`. It reads
    `backend/tests/fixtures/targets_lakeside.json` by path from the repository root (found from `__file__`, as
    `test_5a_targets.py` finds `TREE`), with `json.loads`; it imports nothing from `assetops_backend` (test_records'
    roots assertion, `:550`, stays green). The fixture does not move.
  - **What it asserts (each can fail).** (a) Step 1's batch holds exactly 6 records (spec §5), all `BUDGET_LINE`, and
    their `source_record_id`s are distinct. (b) Over `build_records(view, generate_history(view))`'s batches, each of
    those IDs occurs exactly once. (c) Each fixture record equals, as a parsed JSON object, that record as DS1b writes
    it into its batch file (the same serialisation the world CLI writes, loaded back with `json.loads`), field for
    field: kind, `source_record_id`, `source_version`, `site_code`, `clocks`, `body`. (d) Step 1's batch `tenant_code`,
    `source_type` and `provenance` equal those of the DS1b batch that holds the records. `view` is `load_fixture()`
    from `simulator/tests/world/conftest.py` (`fixtures/view_v1.json`, the view DS1b's goldens pin), never a copy
    or the demo manifest. If step 1 does not match that view's output, the fixture is wrong: raise Q2, do not switch
    the view or edit the expected values to pass.
  - **Plants (in the packet).** P10a: change Kobo `om`'s `value` in a scratch copy of the fixture read through a
    module-level path the plant repoints, fails (c); P10b: drop one record from step 1, fails (a); P10c: rename one
    `source_record_id`, fails (b). Revert after each; tree clean.
  - **Scope.** Spec §7 question 8 now also allows this one file; §6 test 10 names it. Test 10's stub in
    `backend/tests/test_5a_targets.py` is removed (no skipped test left behind).
