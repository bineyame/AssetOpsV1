# 3B1 reviewer guide (rev 2: handshake round 1 folded in)

You are the fresh Reviewer. Read this guide at two points:
- **At the handshake:** read `spec.md`, `rulings.md`, P3B and this guide, then put your questions in `handshake.md`.
- **At the review:** the depth is discovery (W5).

## First checks

1. **Scope.** The diff contains only:
   - `backend/assetops_backend/structure/**`;
   - one import and one call in `main.py`;
   - `backend/tests/test_3b1_structure_registry.py`;
   - the packet and the finish bookkeeping.

   There must be no migration.
2. **Independence.** T1 builds its expectations from the manifest and its own literal home map (never `HOMES` or
   `rows_mini_grid.py`), and T2's unit table is written in the test itself. `ROWS` writes leaf units, sources and
   words as literals.
3. **Module path.** The packet shows the worktree.

## Done means

All five questions in spec §7 are answered yes, backed by real output.

## Probes

- **P1 Planted faults.** Plant each of these faults and check that start-up refuses, naming the row:
  - Give `collected` the home protect P1.
  - Remove the home from `unmapped_kwh`.
  - Change `fuel_cost` to `diesel_l + diesel_price`.
  - Add a cycle: `diesel_l` reads `fuel_cost`.
- **P2 Literal rule.** `max(lost_unit_kw, 1)` composes to kW, `1 - shortfall_backed` is dimensionless, and
  `x - (1 + 1)` keeps `x`'s unit.
- **P2b Placements.** A money row homed `CALENDAR` or `PROTECT_ASSET` is refused, `ABOVE` on a leaf is refused, and
  a catalogue leaf with its row deleted is refused by name.
- **P3 No inheritance.** Grep `registry.py` and `check.py` for any lookup of a parent's home. There must be none.
- **P4 No floats.** No float appears anywhere in `expressions.py`. Numeric literals become `Decimal` from their source
  text.
- **P5 Start-up cost.** `create_app()` takes no measurable extra time; the packet gives a number.

## Class sweep (W6)

- If one row differs from the manifest, recheck all 47 rows through T1.

## Risks

- `3B6` adds two more registries. The check must already be generic over `REGISTRIES`, with nothing specific to the
  mini-grid.
