# 3B1 rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines are in `.ai/decisions/index-rulings-8.md`.
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

## Handshake answers (round 1)

Answered once, 2026-11-20, and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. "Adopted" means the
proposed answer is the ruling. No High. The estimate stays 4 units.

- **R1: adopted.**
  - The four category codes are imported from `CATEGORIES`. `ABOVE` and `CALENDAR` are placements, not categories.
  - Money is allowed only under `GROW_REVENUE`, `OPTIMIZE_COST` and `ABOVE`.
  - `CALENDAR` is tied to calendar leaves, and `ABOVE` is refused on a leaf.
- **R2: adopted.** Numeric literals are `[0-9]+(\.[0-9]+)?` read as `Decimal`. Every other literal form is refused.
- **R3: adopted.** `children` holds distinct IDs in first-seen order; function names are excluded.
- **R4: adopted** (D-3B1.7).
- **R5: adopted.** No second call: the check runs wherever `create_app` runs.
- **R6: adopted.** The first call and the median of 1,000 calls are timed against a 10 ms bound. Nothing is cached.
- **R7: adopted.** T1 uses its own home map, and its four category values are checked against `CATEGORIES`.
- **R8: adopted.** `ExpressionError` is raised by `parse` and mapped by `check`.
- **R9: adopted.**
  - The check runs code by code.
  - `ROWS` lists the leaves first, then the nodes in §2.2's order.
  - `CYCLE` names the first row on the cycle.
  - A node's units are composed from its children's declared units.
- **R10: adopted.** The catalogue check runs both ways, and an unknown structure key is refused by name.
- **R11: adopted.**
- **R12: adopted** (D-3B1.4 amended). The tolerance is the structure default, as a per cent of `of_factor`, and a
  Site's value overrides it. A new code, `STRUCTURE_TOLERANCE`, refuses a bad tolerance. T1 pins the manifest's 2.0.
- **R13: adopted.** `FilledBy` carries `words`.
- **R14: adopted.** The records do no validation; every refusal lives in `check`.
- **R15: adopted** (D-3B1.8).
- **R16: adopted.** A literal-only subtree takes the unit its place needs, as a single literal does.
- **R17: adopted.** A node with `filled_by` or `absent` is refused.
- **R18: done.** `mid-build-questions.md` is reset, and the pointer to `index-rulings-8.md` is fixed.
- **R19: adopted.** Leaf units, sources, words and absence values are literals in `ROWS`.
- **P1: adopted.** Tests run with the database variables unset.
- **P2: adopted.** `check_at_start()` is called right after `install_handle_error_hook()` (D-3B1.9).
- **P3: adopted.**
- **P4: adopted.**
- **P5: noted.** A manifest-only edit selects no parity file while building. The full tier at merge catches it, and
  T2's `select-tests` change names the neutral tests, not these. It is a queued tools item, outside 3B1's scope.
- **P6: verified.** No guard needs registering.
- **P7: noted for 3B3.** A bound or Protect list that names a node with no row (`cover_not_claimable`) must be
  tolerated, or refused by name, until `9a0` adds it.

**Open after round 1:** none.

## D-3B1.7 The expression is the record

- **Ruling.** `kind` and the signs of `children` are read from the parsed `Expr`. They are not stored fields.
- **Why.** Storing them beside the expression would give two declarations that can disagree. Both are derived
  exactly from the expression.

## D-3B1.8 `Expr` is a contract for 3B3

- **Ruling.** `Expr` is the five frozen node types of spec §3, with fixed arities.
- **Why.** `3B3` evaluates `Expr`. Leaving its shape to the implementer would be a design choice made inside a build
  (RULES §7).

## D-3B1.9 The start-up check sits right after the error hook

- **Ruling.** `check_at_start()` is called right after `install_handle_error_hook()`, through a function-local
  import, and raises `ConfigurationError` on failure.
- **Why.** It runs before any router is built, and it stays a hunk apart from `3C1a`'s edits to `main.py`.
