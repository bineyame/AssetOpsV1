# 3B3 reviewer guide

Rev 2 (handshake round 1 folded in; `rulings.md`, "Handshake answers (round 1)").

Fresh Reviewer:
- **Handshake:** closed at round 1 (`handshake.md`).
- **Review:** depth is discovery (W5).

## First checks

1. **Scope.** The diff holds only spec §7 item 8's list, plus the finish bookkeeping. The `chain/outcomes.py` edit is
   the `month_sum` extraction only, and the 3B1 test edit is `version == 2` only.
2. **Independence.** T1 to T3 read `derived-values.json` and `missing-records.json` and nothing from the code under
   test. Their expected values are the pack's, and T3's `SUM` list is its own literal.
3. **Module path.** The packet shows the worktree, and notes the `fixtures` namespace package.
4. **No zero.** Grep `evaluate.py`, `sources.py` and `read.py` for any `Decimal(0)`, `or 0`, `sum(...)` with a 0
   start, or `get(..., 0)` default. Each one must be justified by a neutral value, the neutral identity (D-3B3.15) or
   the calendar. An empty portfolio sum is None.
5. **Own record.** Every `Missing` a source builds names the row's `filled_by` kind and family. Only `period_days`
   and `unserved_critical_kwh` are PROVIDED; the two prices are ASSUMED with literal words (D-3B3.11).

## Probes

- **P1. Missing leaf.** Remove `om` from Kobo's actual leaves: every node in `blocks(om)` has no value and
  `contribution` lists `om`; no node with a value rests on `om` (other nodes may legitimately be 0).
- **P2. Assumption.** Mark `candidate_l` as ASSUMPTION on the plan side: `fuel_cost`, `cost_to_serve` and
  `contribution` become ESTIMATED.
- **P3. Division.** Plant a node `x / y` with `y = 0`: there is no value, and the cause is `ZERO_DENOMINATOR`.
- **P4. Context.** Set the global context to precision 5 before calling `evaluate`: the results are unchanged.
- **P5. Sources.** For each NOT_CONNECTED leaf, the read returns no value and the right cause. A ZERO_WHEN_HELD leaf
  (`adjustments_kwh`) is never 0. `productive_kwh` is NOT_CONNECTED.
- **P6. Portfolio.** Drop Kisiwa's `om`: `contribution` sums Kobo and Mto and names Kisiwa; `unserved_critical_kwh`
  still sums all three. Drop every Site's `om`: `contribution` has no value, never 0.
- **P7. Parse once.** Count the calls to `parse`.
- **P8. Gap days.** One NO_DATA day in a closed month: `unserved_critical_kwh` has no value, NOT_RECEIVED, coverage
  kept. An open month: no value.
- **P9. Leaf-value checks.** Plant a None value with no `missing`, an assumption labelled MEASURED, a money value
  with no currency: each raises its code.
- **P10. Neutral.** `battery_wear` is 0 and `NEUTRAL` with `wear_rate` unknown; a `MEASURED` 0 times an unknown has
  no value.

## Class sweeps (W6)

- If one node differs from the pack, recheck all 47 nodes at all three Sites through T1 and T2.
- If one leaf's state is wrong, recheck all 31 rows of `SOURCE_STATE` against `filled_by` (D-3B3.11's test).
- If one `composes` flag is wrong, recheck all 47 rows against T3's list.

## Risks

- `3B7a` serves these values from the snapshot. Check that every `FactorValue` and `PortfolioValue` field can be
  stored unchanged, including `missing`, `currency`, the structure key and version, and `included`/`excluded`.
- Later providers (`3A4`, `4b`) must keep D-3B3.11: own record, or a declared value of the same quantity labelled as
  an assumption; never a different quantity.
- Portfolio factors may rest on different Site sets (D-3B3.13); `3B5` must show "k of n Sites".
