# 0K1 mid-build questions

Questions raised during the build about something the spec did not fix (spec rev 2). Count: 2. Both concern which
test catches a plant, not what is built; the build is complete and nothing waits on them.

## Q1 P2 (loads matched by position) cannot fail T1

- **Found.** Planted in the committed tree, P2 passes T1 (`test_t1...[7]`: 1 passed). The reader's reverse order of
  three loads swaps `load-clinic` and `load-res` and leaves `load-mill` in place. Every projected field that
  depends on the loads (`unserved_kwh`, and through dispatch the state, SOC and fuel) depends only on their sum, and
  a sum does not change under a permutation. So no ordering in the reader can make T1 see a positional match: the
  projection carries no per-load field. D-0K1.10's "a mix-up changes the result" does not hold for the projection.
- **Done in the build (test only).** T10 (`test_t10_everything_not_replaced_is_kept_unchanged`) now checks that each
  `load-demand@<id>` forcing in the plan carries that load's own series, matched by id, and P2 fails it. T1 keeps the
  pairwise-unequal and reverse-order preconditions.
- **Question for the Architect.** Accept T10 as P2's test (guide row P2: "T10, not T1"), or is a per-load field
  wanted in the projection (a type change, out of 0K1's scope as written)? Default if no answer: T10.

## Q2 P4 (reserve applied to the start threshold) fails T10, not T4

- **Found.** Planted, P4 passes T4 and fails T10. With the reserve setting written into the start threshold (25)
  and the reserve left at its baseline (30), v5 starts at min(25, 30 + 5) = 25; the kernel's own run starts at
  min(35, 25 + 5) = 30. The dawn dip bottoms at 34.6 %, so neither starts, and the reserve never binds above 30 %:
  the two trajectories are identical step by step. T4 cannot tell them apart on this scenario.
- **Done in the build.** Nothing beyond T10's one-forcing-at-the-reserve-address check, which catches it.
- **Question for the Architect.** Accept T10 alone for P4 (guide row P4: "T10"), or add a case where the dip
  crosses 30 % (a new fixture edit, not in spec §3)? Default if no answer: T10 alone.
