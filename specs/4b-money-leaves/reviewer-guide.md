# 4b reviewer guide (rev 2)

Rev 2 folds in the handshake answers (`rulings.md` "Handshake answers (round 1)", D-4B.13 to D-4B.17).

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
| V5 | 4b1 | Sort origins alphabetically instead of by `ORIGIN_ORDER` (in the union, the input check or `weakest_origin`) | S6 (`("source-emulated", "demo-simulated")`, `("observed-financial", "field-integrated")` and both `weakest_origin` assertions), S5 (`("demo-simulated", "source-emulated")` refused) |
| V6 | 4b1 | Leave MINI_GRID at version 2 | S8 |
| V7 | 4b2 | Count QUOTE expenses as cost | test 1 (Kobo `fuel_cost` 1835.00) |
| V8 | 4b2 | Read an absent O&M as 0 | tests 1 and 3 (Kisiwa contribution has a value; portfolio 2 of 3) |
| V9 | 4b2 | Return month-to-date values for an open month | test 2 |
| V10 | 4b2 | Prefer the declared price to the invoices, fall back on mixed currencies, or fall back in an open month that holds fuel invoices | test 1 (1.30), test 6, test 2(ii) |
| V11 | 4b2 | Judge "connected" by the month instead of any month | test 7(b), test 2(i) (`om` in November reads `NOT_CONNECTED`) |
| V12 | 4b2 | Treat a missing RECEIPT as zero receipts in `outstanding` | test 7 |
| V13 | 4b2 | Cache the month by context equality (or across reads) | test 9 |
| V14 | 4b2 | Sum through `float`, or under the ambient decimal context | test 11(a) (`float`), test 11(b) (context) |
| V15 | 4b2 | Give the portfolio total over all Sites, filling a missing Site with 0 | test 3 |
| V16 | 4b1 | Serve the expression's value when the stated record is refused (`NOT_CALCULATED_YET`) | S10 |
| V17 | 4b2 | Divide by zero litres, or fall back to the declared price on zero litres | test 12 |
| V18 | 4b1 | Allow `stated_by` on any unit with a MONEY exponent | S8 (`revenue` copy with `MONEY / KWH`) |
| V19 | 4b2 | Build every absent `Missing` from `filled_by` (ignore `READ_AS`) | test 7(a), 7(c) (`in_transit` names SETTLEMENT; `outstanding` names RECEIPT) |
| V20 | 4b2 | Leave earlier stores undisposed when the commercial builder fails | test 13 |

## Probes

- **Field-for-field equality with 3B3.** With `stated` empty, compare a whole `evaluate` output with the 3B3 result on
  `main` for the pack's three Sites: only the four new fields differ, and only by their rules.
- **Every `Missing` names the record 4b reads for it** (`READ_AS`, D-4B.13): `stated_by` for stated nodes, `filled_by`
  except `in_transit` (`RECEIPT_RECORD`) and `outstanding` (the failing kind's record, `NEEDS:<kind>`).
- **Composition.** `build_structure_read` disposes every store on a builder failure and on `dispose()`.
- **One read per Site-month.** In one `site()` read: one `site_month` and one `latest_revisions` (the store calls
  inside `site_month` are 3A4's), and nothing reused across reads.

## Class sweeps (W6)

- A leaf filled from a different quantity: check every row of spec §3.4 against its `filled_by` and the 2a field.
- An unknown read as zero: every path in `money.py` that returns a value with no line behind it must be a
  ZERO_WHEN_HELD row with its kind held.
- A record hidden by a substitute: every path that returns the fallback or the expression must have nothing held to
  read (D-4B.14, D-4B.16); a held but refused record always blocks.
- The weakest label: every place a `FactorValue` is built (`_leaf`, `_node`, the stated rule, `_compose_factor`)
  carries origins.

## Risks

- `5a` builds on `4b1`'s fields; a change to them after `4b1` merges needs a ruling here and a note to `5a`.
