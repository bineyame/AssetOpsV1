# 0K4b reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a new physical law that will put litres on a money
figure. Read `spec.md`, `specs/0K4-dispatch-model-review/rulings.md` (D-0K4.5 to D-0K4.7), then the diff. Done means
every question of spec §5 answers yes with evidence and every plant below fails its named test.

## What to check, and how

1. **The law, by hand.** Recompute F1-F3 yourself from D-0K4.5 (`r x h_on + (SFC - r/rating) x E`). A test whose
   expected litres come from calling `fuel_litres` is High (W2): expected values are literals or hand arithmetic.
2. **Units once.** The frozen no-load rate is `L/min` (`CANONICAL_UNITS["L/h"]`). The `/60` or `x 60` appears in one
   place in the module, and F4 (0.275 L in a 5-minute STARTING step) proves it. A second conversion anywhere is High.
3. **Exactness.** No `float(`, no `round(` in `generator_curve.py`; F9.
4. **No dispatch here.** The module reads no context, holds no state and is imported by nothing under `packs/` except
   tests (0K4a wires it). `git grep generator_curve` lists only the module, its test, and nothing in `mini_grid.py`.
5. **Catalogue.** Four new rows, two state sets, two carriers; the FUEL-1 rows untouched (`git diff` of
   `sites/models.py`). `GENERATOR_CURVE_NEEDS` is on no profile (P4).
6. **Template untouched.** `git diff main...HEAD -- config/` is empty; the Kobo digest tests pass unchanged.
7. **Labels.** Every assumed value has its basis row `GENERIC_DEFAULT`; `ASSUMPTION_NOTE` names all three.
8. **Packet.** The load table is labelled assumed; no design value or verdict word appears beside it.

## Plants (each must fail the named test; revert after)

| # | Plant | Must fail |
|---|---|---|
| P1 | `fuel_litres` drops the no-load term while RUNNING | F1 |
| P2 | slope computed as `sfc` (no `- r/rating`) | F2 |
| P3 | STARTING burns 0 | F4 |
| P4 | the no-load rate read as L/h without the `/60` | F4 |
| P5 | refusal order swapped (slope before SFC) | F5 |
| P6 | `TAPER_FLOOR_SHARE` set to 0 | F7 (and F8 never reaches 100) |
| P7 | taper applied at or below the start | F7 |
| P8 | basis set gains `"ASSUMED"` | P2 |
| P9 | `generator-minimum-load` carried by BATTERY | P3 |

## What counts as done

All of spec §5 yes; plants P1-P9 each fail their test; check-all (fast) green; mid-build count 0 in the packet.
