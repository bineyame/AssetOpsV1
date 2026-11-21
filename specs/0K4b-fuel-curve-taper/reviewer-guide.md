# 0K4b reviewer guide

Architect (Claude), 2026-11-21, rev 2 (handshake answered: D-0K4.19 to D-0K4.21). Discovery review (W5): a new physical law that will put litres on a money
figure. Read `spec.md`, `specs/0K4-dispatch-model-review/rulings.md` (D-0K4.5 to D-0K4.7), then the diff. Done means
every question of spec §5 answers yes with evidence and every plant below fails its named test.

## What to check, and how

1. **The law, by hand.** Recompute F1-F3 yourself from D-0K4.5 (`r x h_on + (SFC - r/rating) x E`). A test whose
   expected litres come from calling `fuel_litres` is High (W2): expected values are literals or hand arithmetic.
2. **Units once.** The frozen no-load rate is `L/min` (`CANONICAL_UNITS["L/h"]`). The only `60` in the module is the
   slope's `60 x no_load / rated`. F11 runs the contract's own conversion (`frozen_canonical_value`, then
   `normalize_authored_float`) and F4 the module's arithmetic; a test that divides by 60 by hand, or a second
   conversion anywhere, is High.
3. **Exactness.** No `float(`, no `round(` in `generator_curve.py`; F9.
4. **No dispatch here.** The module reads no context, holds no state and is imported by nothing under `packs/` except
   tests (0K4a wires it). `git grep generator_curve` lists only the module, its test, and nothing in `mini_grid.py`.
5. **Catalogue.** Four new rows, two state sets, two carriers; the FUEL-1 rows untouched (`git diff` of
   `sites/models.py`). `GENERATOR_CURVE_NEEDS` is on no profile (P4).
6. **Template untouched.** `git diff main...HEAD -- config/` is empty; the Kobo digest tests pass unchanged.
7. **Labels.** Every assumed value has its basis row `GENERIC_DEFAULT`; `ASSUMPTION_NOTE` names all three.
8. **Packet.** The load table is headed "assumed (GENERIC_DEFAULT)"; the 0 % row reads "not defined (no output)" for
   litres per kWh; no design value or verdict word appears beside it.
9. **Words (D-0K4.19).** Every new served word is in `foundation_property`, `foundation.property_name` or
   `model_profile.need`, each variant and entry with a hand-literal case. `git diff main -- tools/checks/` is empty (no
   baseline, no allow entry); the statement guard is green. Legacy definitions keep `str`; only the four new names and
   three needs are `Message`s; `served_text` is the only place that tells them apart.
10. **Pins (D-0K4.20).** F12 asserts literals, not the module's names compared with themselves. The pre-flight shows the
   with-and-without `assumed_site` comparison and says equal or why not.
11. **Independent fixture check.** P1-P3 build their six rows inline; only P5 imports `kobo_assumed.py`.

## Plants (each must fail the named test; revert after)

| # | Plant | Must fail |
|---|---|---|
| P1 | `fuel_litres` drops the no-load term while RUNNING | F1 |
| P2 | slope computed as `sfc` (no `- r/rating`) | F2 |
| P3 | STARTING burns 0 | F4 |
| P4 | `fuel_litres` multiplies the rate by `minutes / 60` (reads the L/min input as L/h) | F4, F11 |
| P5 | refusal order swapped (slope before SFC) | F5 |
| P6 | `TAPER_FLOOR_SHARE` set to 0 | F7 (and F8 never reaches 100) |
| P7 | taper applied at or below the start | F7 |
| P8 | basis set gains `"ASSUMED"` | P2 |
| P9 | `generator-minimum-load` carried by BATTERY | P3 |
| P10 | `TAPER_FLOOR_SHARE = Fraction(1, 10)` | F12 (and F7) |
| P11 | the minimum-load acceptor reverted to `daytime._percentage("a minimum generator load")` | F10 |
| P12 | one new `display_name` written as a plain `str` literal | the statement guard (`HAND_BUILT_NEW`) |
| P13 | `assumed_site` overwrites a key already present | P5 |

## What counts as done

All of spec §5 yes; plants P1-P13 each fail their test; check-all (fast) green; mid-build count 0 in the packet.
