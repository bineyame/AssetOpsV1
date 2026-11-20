# 3B2 reviewer guide

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md` and this guide, then write your questions
in `handshake.md`), then at the review. Review depth: discovery (W5).

## First checks

1. **Scope.** The diff holds only spec §7.5's list, plus the finish bookkeeping. `outcome_map.py` is untouched.
2. **No wire change.** T4 passes, `test_out_a1_outcome_map.py` passes unchanged, and the diff of `outcomes/` is empty.
3. **Independence.** T1's pin table and T3's expected differences are literals written in the test. They are not
   imported from `pins.py`.
4. **Module path.** The packet shows the worktree.

## Probes

- **P1.** Pin `UNEXPLAINED_FUEL` to `diesel_l`: start-up refuses with `STRUCTURE_PIN_TOTAL`.
- **P2.** Remove `EV_INTERRUPTION` from `PENDING_PINS`: start-up refuses with `STRUCTURE_PIN_MISSING`.
- **P3.** Change `candidate_l`'s home to protect P1 in a scratch copy. `parity()` reports a new divergence, and T3
  fails.
- **P4.** `pinned_category` reads the registry at call time (patch `REGISTRIES` and the answer changes).

## Class sweep (W6)

- If one pin is wrong, check both pins and the three pending pins against the design §4 table.

## Risks

- `3B5` must apply D-3B2.4 when it switches the wire, and nothing else. Any other category change needs its own ruling.
