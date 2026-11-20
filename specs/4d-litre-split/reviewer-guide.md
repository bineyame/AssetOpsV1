# 4d reviewer guide

Architect (Claude), 2026-11-20, rev 1. Discovery review (W5): a new mechanism feeding money figures. Read `spec.md`,
`rulings.md`, then the diff. Done means every question in spec §7 answers yes with evidence, and every plant below
fails its named test.

## What to check, and how

1. **Hand values, not code values (W2).** Tests 1, 2 and 6 write spec §5's literals. A test that computes its expected
   value with `month_litres` or the slot rule is a finding (High).
2. **Precedence.** Read `rules.py` against spec §2.3 rule by rule: the note order is `NOTES`, the unexplained leaf
   adds rules 11 to 13 only after 1 to 9, and rule 12 re-checks the window's outside parts.
3. **One litre, one class.** INDETERMINATE goes to necessary (D-4D.3); slots by start (D-4D.4); the month's
   `necessary_l + candidate_l` equals all its spans' litres (test 3).
4. **Absent is never 0.** Every absent leaf has value None, evidence NOT_AVAILABLE, a `Missing` with `blocks == ()`,
   the row's `filled_by` words and the note; cause NOT_CALCULATED_YET only for `DISPATCH_NOT_ASSESSED` and
   `SPANS_OVERLAP`.
5. **Seams.** `git diff main...HEAD --stat`: only spec §0's files. `read_at` and `dispatch_spans` are read-only and
   add nothing else to their stores; the configuration-persistence guard passes; no adapter import outside a
   composition.
6. **5b untouched.** `git diff main...HEAD -- backend/assetops_backend/structure/attribution/` is empty; test 6 passes.
7. **Memo.** Only pinned reads are memoised (test 5).
8. **W6 sweep.** The packet lists every place that named the three leaves HELD_NOT_CALCULATED (code, tests, specs'
   live text) and what changed; check it with `grep -rn "necessary_l\|candidate_l\|unexplained_l" backend specs`.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | INDETERMINATE litres added to `candidate_l` | test 1 (`candidate_l` 340.000), test 3 |
| P2 | `unexplained_l` clipped at 0 | test 2, V6 (−80.000) |
| P3 | an incomplete span skipped instead of stopping | test 2, V4 |
| P4 | a missing dip read as 0 | test 2, V5 |
| P5 | deliveries counted by calendar month, not the dip window | test 2, V7 (135.000) and V16 |
| P6 | the month read while open | test 2, V12 |
| P7 | rounding each slot's litres (5/12 L) to 0.001 before summing | test 1 (`necessary_l` 730.584, not 730.000) and V17 |
| P8 | `DISPATCH_NOT_ASSESSED` given cause NOT_RECEIVED | test 2, V8 |
| P9 | the no-load rate required with no idle time | test 2, V3 |
| P10 | `LitreLeafSource` memoises a live read | test 5 |
| P11 | `read_at` without READ ONLY | Postgres test 2 |
| P12 | a day before the month left unread (rule 5 from `lo`) | add a case: day 2026-09-30 NOT_ASSESSED gives `DISPATCH_NOT_ASSESSED` (test 2, written by the builder as V18) |

## Not findings

The registry's 2 % tolerance on `unexplained_l` is not applied (spec §8). Fuel cost from invoices still stops at
`RECORD_AND_FACTORS_DIFFER` when the tank's stock changed (queue Q3).
