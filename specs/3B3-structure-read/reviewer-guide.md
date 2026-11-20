# 3B3 reviewer guide

Fresh Reviewer:
- **Handshake:** read `spec.md`, `rulings.md` and this guide, then write your questions in `handshake.md`.
- **Review:** depth is discovery (W5).

## First checks

1. **Scope.** The diff holds only spec §7.6's list, plus the finish bookkeeping.
2. **Independence.** T1 to T3 read `derived-values.json` and `missing-records.json` and nothing from the code under
   test. Their expected values are the pack's.
3. **Module path.** The packet shows the worktree.
4. **No zero.** Grep `evaluate.py` and `sources.py` for any `Decimal(0)`, `or 0` or `get(..., 0)` default. Each one
   must be justified by a neutral value or by the calendar.

## Probes

- **P1. Missing leaf.** Remove `om` from Kobo's actual leaves: `contribution` has no value and lists `om`, and no node
  reads 0.
- **P2. Assumption.** Mark `candidate_l` as ASSUMPTION on the plan side: `fuel_cost`, `cost_to_serve` and
  `contribution` become ESTIMATED.
- **P3. Division.** Plant a node `x / y` with `y = 0`: there is no value, and the cause is `ZERO_DENOMINATOR`.
- **P4. Context.** Set the global context to precision 5 before calling `evaluate`: the results are unchanged.
- **P5. Sources.** For each NOT_CONNECTED leaf, the read returns no value and the right cause. A ZERO_WHEN_HELD leaf
  (`adjustments_kwh`) is never 0.
- **P6. Portfolio.** Drop Kisiwa's `om`: Kisiwa is excluded by name, and the sums cover Kobo and Mto only.
- **P7. Parse once.** Count the calls to `parse`.

## Class sweeps (W6)

- If one node differs from the pack, recheck all 47 nodes at all three Sites through T1 and T2.
- If one leaf's state is wrong, recheck all 31 rows of `SOURCE_STATE`.

## Risks

- `3B7a` serves these values from the snapshot. Check that every `FactorValue` field can be stored unchanged,
  including `missing`.
- Later providers (`3A4`, `4b`) must keep D-3B3.4's rule: exact sources only.
