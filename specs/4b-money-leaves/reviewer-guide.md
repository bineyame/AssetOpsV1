# 4b reviewer guide (rev 1)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md` and this guide; put questions in
`handshake.md`), then at each of the two reviews (`4b1`, then `4b2`). Depth: discovery (W5) for both: `4b1` changes
the evaluator every later money figure rests on; `4b2` produces the first money figures from records.

## First checks

1. **Scope.** Each diff holds only spec §6 question 8's list for its unit. No migration. Nothing under `commercial/`
   but `composition.py`, and `commercial/` imports nothing from `structure/`.
2. **Order.** `4b1` merged to `main` before `4b2` branched (RULES §7).
3. **Module paths** in each packet show the worktree.
4. **W2.** Expected values are spec §4's literals, never computed by the code under test; the state tables in the
   tests are the tests' own literals.

## Done means

Spec §6's eight questions answered yes with real output: the unit's no-database file, the Postgres file and the
regression set through `tools/heavy-slot.sh --db`, check-all, and every planted violation below failing.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Unit | Plant | Must fail |
|---|---|---|---|
| V1 | 4b1 | Ignore `stated` (always compute the expression) | S1 (revenue None), S2 |
| V2 | 4b1 | Accept a stated value for a node without `stated_by` | S5 (`contribution`) |
| V3 | 4b1 | Leave the node itself out of `missing_leaves` when stated and expression are both absent | S4 |
| V4 | 4b1 | Inherit the other operand's `detail_missing` and origins through the neutral identity | S6 |
| V5 | 4b1 | Sort origins alphabetically instead of by `ORIGIN_ORDER` | S6 |
| V6 | 4b1 | Leave MINI_GRID at version 2 | S8 |
| V7 | 4b2 | Count QUOTE expenses as cost | test 1 (Kobo `fuel_cost` 1835.00), test 8 |
| V8 | 4b2 | Read an absent O&M as 0 | tests 1 and 3 (Kisiwa contribution has a value; portfolio 2 of 3) |
| V9 | 4b2 | Return month-to-date values for an open month | test 2 |
| V10 | 4b2 | Prefer the declared price to the invoices, or fall back on mixed currencies | test 1 (1.30), test 6 |
| V11 | 4b2 | Judge "connected" by the month instead of any month | test 7(b), and test 1 (Kisiwa `om` cause) |
| V12 | 4b2 | Treat a missing RECEIPT as zero receipts in `outstanding` | test 7 |
| V13 | 4b2 | Cache the month by context equality (or across reads) | test 9 |
| V14 | 4b2 | Sum through `float`, or under the default decimal context | tests 1 and 11 |
| V15 | 4b2 | Give the portfolio total over all Sites, filling a missing Site with 0 | test 3 |

## Probes

- **Field-for-field equality with 3B3.** With `stated` empty, compare a whole `evaluate` output with the 3B3 result on
  `main` for the pack's three Sites: only the four new fields differ, and only by their rules.
- **Every `Missing` names its own record.** Leaves: `filled_by`; stated nodes: `stated_by`. Never a second kind.
- **Composition.** `build_structure_read` disposes every store on a builder failure and on `dispose()`.
- **One read per Site-month.** Count store calls in one `site()` read: two (`site_month`, the kinds read).

## Class sweeps (W6)

- A leaf filled from a different quantity: check every row of spec §3.4 against its `filled_by` and the 2a field.
- An unknown read as zero: every path in `money.py` that returns a value with no line behind it must be a
  ZERO_WHEN_HELD row with its kind held.
- The weakest label: every place a `FactorValue` is built (`_leaf`, `_node`, the stated rule, `_compose_factor`)
  carries origins.

## Risks

- `3A2`'s merge edits `commercial/composition.py` beside `build_commercial_reads`; the second to merge keeps both.
- `5a` builds on `4b1`'s fields; a change to them after `4b1` merges needs a ruling here and a note to `5a`.
