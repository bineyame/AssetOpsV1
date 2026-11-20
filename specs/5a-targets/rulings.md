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
