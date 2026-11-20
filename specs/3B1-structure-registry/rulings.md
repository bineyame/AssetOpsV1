# 3B1 rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines are in `.ai/decisions/index-rulings-7.md`.
Handshake answers go below, under "Handshake answers (round 1)".

## D-3B1.1 The registry is literal code rows, pinned to the manifest by test

- **Ruling.** `ROWS` is a hand-written literal. A test compares it with the manifest. The product never reads the
  manifest.
- **Why.**
  - The design asks for code rows that are versioned and need no migration (`decision-loop-specification.md` §3).
  - The manifest is the demonstration's declared structure. Reading it at run time would make product start-up
    depend on a demo file.
  - The parity test is the independent check (W2).

## D-3B1.2 A literal takes the unit its place needs

- **Ruling.**
  - In `+`, `-`, `min` and `max`, a literal takes the unit of the other operands.
  - In `*` and `/`, a literal is dimensionless.
- **Why.** D-2A.4 left this rule to `3B1`. Under it, every mini-grid node composes, including `max(lost_unit_kw, 1)`
  and `0 - cost`. P3B states the rule in plain words.

## D-3B1.3 The start-up check refuses rather than repairs

- **Ruling.** The first failure stops the process and names the structure and the row.
- **Why.**
  - The design says the process refuses to start (§3).
  - A structure that is quietly repaired would compute figures from a different model than the one declared.

## D-3B1.4 Tolerance: one declared value in version 1

- **Ruling.** Only `unexplained_l` carries a tolerance: 2 per cent of `diesel_l`, which is the manifest's fuel-balance
  tolerance.
- **Why.** It is the only tolerance the demonstration states. Other tolerances are declared by the operator in step 5,
  or by `3B4` with its observer. Inventing them here would be figures with no source.

## D-3B1.5 Rights nodes and operations measures are not rows yet

- **Ruling.** `cover_not_claimable`, `unclaimable_cover` and the operations measures are not rows in version 1.
- **Why.** They come with `9a0` and `OPS1` (D-L4OPS.7). P3B says they attach to this registry, not to a second model.
  Adding them later is a version 2 of `MINI_GRID`.

## D-3B1.6 Three of the design's start-up checks belong to later slices

- **Ruling.** These three checks are deferred:
  - the runtime MISSING rule, to `3B3`;
  - observer existence, to `3B4`;
  - pins and levers, to `3B2` and step 6.
- **Why.** Each needs a construct that does not exist yet. A check written without its subject would be vacuous.
