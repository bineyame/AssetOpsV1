# 3A7 reviewer guide (rev 2, after handshake round 1)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md` and this guide; put questions in
`handshake.md`), then at the review. Depth: discovery (W5): a money figure's label and a new table.

## First checks

1. **Scope.** The diff holds only spec §8 question 9's list.
2. **Migration.** One new head, `0068_commercial_reconciliation`, revising `0067_source_profile` (D-3A6.12; its test
   asserts the chain link);
   both tables append-only; downgrade refused with a row.
3. **Built on 3A6.** The branch's base holds 3A6's merge.
4. **3A4 and 4b unchanged.** Their test files pass; the 3A4 fixture is not edited.

## Done means

Spec §8's nine questions answered yes with real output: the service and command files, the Postgres file through
`tools/heavy-slot.sh --db`, the regression set, check-all, and each plant below failing its named test.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V1 | Count QUOTE fuel expenses | R2 (T1: fuel 1400.00) |
| V2 | Copy `("INVOICED", "PAID")` into the module instead of importing `COST_STATUSES`, then add `"QUOTE"` to 4b's | R7 |
| V3 | Use `<` instead of `<=` against the allowed amount | R3 (510.05) |
| V4 | Base the tolerance on the records' figure | R3 or R2 (T1 fuel: 5.00 allowed, not 5.05) |
| V5 | Read the stored `result_at_record` in the standing | R2 (T2) |
| V6 | Let a matched month elsewhere override a covering unmatched statement | R2 (T2, T6) |
| V7 | Treat no fuel lines as 0.00 recorded | R2 (T6) |
| V8 | Accept an open month | R2 (T9) |
| V9 | Quantise the allowed amount (half-even) before comparing | R3 (501.50 / 506.52 must be NOT_MATCHED) |
| V10 | Read the tolerance stored at recording instead of now | R2 (T3) |
| V11 | Let the analyst record a statement | R4, M2 |
| V12 | Show the share when the accounts' figure is 0 | R3 |
| V13 | Let any `MATCHED` statement open the gate (ignore `opens`) | R2 (T10) |
| V14 | Ignore `known_at` (read statements, tolerance and months live) | R9, M4 |
| V15 | Display the allowed amount `ROUND_HALF_EVEN` in a not-matched sentence | R3 ("beyond the 5.01 allowed") |
| V16 | Sum every Site of the tenant in the organisation scope | R2 (T1 revenue 1749.00), R10 |
| V17 | Accept any existing owner file (no slug or figure check) | M5 |
| V18 | Drop the per-call `site_month` memo | R8 |
| V19 | Leave the failing headings out of the standing's text | R2 (T2, T6 standing texts) |
| V20 | Break the current-statement tie by insertion order instead of `recorded_at` then `id` | R2 (T6), R5 |

Rule for plants (rev 2): every gate in `rulings.md` "Handshake answers (round 1)" has a row here; a plant that no
listed test fails is a High finding against the spec, reported, not waived.

## Probes

- **Independence (W2).** Every expected figure and sentence in R1 to R3 is a literal from the spec, written by hand;
  recompute T2's share (7.50 / 505.00 = 1.485...% → 1.49%, rounded up), K's fuel share (2.2436% → 2.25%) and the
  boundary (501.50 × 0.01 = 5.015 < 5.02) yourself.
- **Honesty.** No path makes money read reconciled without a current matched statement; absent records are never 0
  except where the accounts themselves state 0.00.
- **Person.** Every statement carries the finance lead's person ID (5c resolves the name) and is marked scripted; the
  analyst cannot record one.
- **Words.** Read T2's and T6's sentences as an executive would: do they say what did not match, by how much, and what
  is allowed?
