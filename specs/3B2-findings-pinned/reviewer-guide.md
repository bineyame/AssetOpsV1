# 3B2 reviewer guide

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md` and this guide, then write your questions
in `handshake.md`), then at the review. Review depth: discovery (W5).

## First checks

1. **Scope.** The diff holds only spec §7.5's list, plus the finish bookkeeping. `outcome_map.py` is untouched.
2. **No wire change.** T4 passes against its committed literal snapshot (D-3B2.6: not built from `ENTRIES`),
   `test_out_a1_outcome_map.py` passes unchanged, and `git diff main -- backend/assetops_backend/outcomes/` is empty.
   The snapshot literal is the one written from `main` at 39e1682de.
3. **Independence.** T1's pin table and T3's expected differences are literals written in the test. They are not
   imported from `pins.py`.
4. **Module path.** The packet shows the worktree.
5. **No served text (D-3B2.8).** The diff adds no `messages.CATALOGUE` key, sentence or word map. If it does, High.
6. **Layering (D-3B2.11).** `structure/` imports `outcome_map` only in `pins.py` and `check.py`; no guard file is
   changed; `tools/check-architecture.ps1` passes (set `ASSETOPS_GUARD_PYTHON`).
7. **3B1 unchanged.** `check_all(registries=X)` runs no pin check, and `CODES` is untouched (`PIN_CODES` is separate).

## Probes

- **P1.** Pin `UNEXPLAINED_FUEL` to `diesel_l`: start-up refuses with `STRUCTURE_PIN_TOTAL`.
- **P2.** Remove `EV_INTERRUPTION` from `PENDING_PINS`: start-up refuses with `STRUCTURE_PIN_MISSING`.
- **P3.** Change `candidate_l`'s home to protect P1 in a scratch copy. `parity()` reports a new divergence, and T3
  fails.
- **P5.** Plant a registry set without `MINI_GRID` through `check_all(registries=...)`: no pin code raised.
- **P6.** Pin `fuel_cost` (a product): accepted. Pin `cost_to_serve` (a sum): `STRUCTURE_PIN_TOTAL`.
- **P7.** `parity()` has no entry for a cold or EV domain of a mini mechanism (D-3B2.7).
- **P4.** `pinned_category` reads the registry at call time (patch `REGISTRIES` and the answer changes).

## Class sweep (W6)

- If one pin is wrong, check both pins and the three pending pins against the design §4 table.

## Risks

- `3B5` must apply D-3B2.4 when it switches the wire, and nothing else. Any other category change needs its own ruling.
