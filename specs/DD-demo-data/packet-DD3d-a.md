# DD3d-a review packet (the tolerance floor, the fuel records, H5 on the floor)

Branch `task/DD3d-fuel-floor` (worktree `/opt/assetecon/AssetOpsV1-dd3d`), main merged. Card `cards/DD3d.md` (DD3d-a),
D-DD.153, D-DD.154 as amended by D-DD.168, D-DD.156. Evidence `/opt/assetecon/evidence/DD3d/`. Mid-build questions: 0.
`USER_REVIEW_REQUIRED`: no screen changes (the band is not rendered); two findings verdicts move (below).

## What was built

- **Floor (DD3d.1).** `structure/observe/`: `FLOORED`, `Floor`, the floors argument and the adverse-branch rule (band =
  max(relative, 2a), strict `>`), `FloorReadPort` and `StoreFloorRead` (`floor.py`) on the Foundation read the litres
  inputs use. `/2` file: each tank declares a (Kobo 25, Kisiwa 50, Mto 10 L, GENERIC_DEFAULT). Basis sentence: "Generic
  capacitive level-sensor class, ±1 % of measuring length (Technoton DUT-E data sheet), taken as 1 % of this tank's
  capacity; not this sensor's calibration (Assumed)". `/2` digest: file 92ca8fed -> 18fd700e, `LAKESIDE_ALONE_SHA256`
  7d582e06 -> c3260726; `config/world/fuel-leaves.json` `inputs_sha256` at three Sites (no figure moves).
- **Records (DD3d.2).** `world/exports_fuel_records.py`, `exports --telemetry`, `load_fuel_records.py` behind
  `require_prepare_database` (widened). Kobo 5 dips + 3 deliveries (OOO-1 late), Kisiwa 5 + 8, Mto 5 + 0.
- **Checks.** C-DD17: own read of a, factor 2 typed, all three Sites, no no-burn carve-out; served clause DD6.1's. C-DD2:
  `TANK_DIP` and `FUEL_DELIVERY` per mini-grid Site-month. C-DD8: balance on the records equals the declared draw
  (pure: the file; store: LIVE, nights by state), no tank-accuracy fallback anywhere.
- **H5 (DD3d.3).** `unexplained_l <= max(2 % x diesel_l, 2a)`; no declared a is a FAIL. `M` rev 16.24: the two wordings
  (Kobo note, Kisiwa basis), no figure moves; fixtures.js, index.html regenerated; H10 re-based with a dated note. The mock's
  sentence map in `loop-core.js` follows the Kisiwa wording (its key was the old text).

## Verdicts, from `dd_check --pure` (`dd_check-pure.log`, exit 0: C-DD8, C-DD17, C-DD20 PASS)

| Site-month | consumption L | unexplained L | 2 % | 2a | state | was (2 % alone) |
|---|---|---|---|---|---|---|
| Kobo Jul, Aug | 12.00 | 12.0 | 0.24 | 50 | INSIDE_TOLERANCE | RAISED |
| Kobo Sep | 785.15 | 11.0 | 15.70 | 50 | INSIDE_TOLERANCE | INSIDE |
| Kobo Oct | 634.22 | 120.0 | 12.68 | 50 | **RAISED** | RAISED |
| Kisiwa Jul, Aug | 1260.77, 1246.60 | 20.0, 19.0 | 25.22, 24.93 | 100 | INSIDE_TOLERANCE | INSIDE |
| Kisiwa Sep | 710.94 | 18.0 | 14.22 | 100 | INSIDE_TOLERANCE | RAISED |
| Kisiwa Oct | 903.07 | 20.0 | 18.06 | 100 | INSIDE_TOLERANCE | RAISED |
| Mto Jul-Oct | 0 to 32.38 | 0.0 | - | 20 | NO_GAP | NO_GAP |

"Was" is measured: the same run with the floor removed (`plant-c17-real-run.log`) fails exactly Kobo Jul, Aug, Kisiwa Sep, Oct.
Consumption differs from D-DD.153's projections by DD3b's fix rounds (Kobo Sep 773.20 projected); no verdict changes.
C-DD8 on the records: the declared draw to 0.1 L in all 12 Site-months. Night states (`nights.py`, the product's `assess`
over the pure readings and records, 1 Jul to 4 Nov, 127 nights per Site): Kobo, Kisiwa and Mto all WITHIN_MARGIN, 127 each;
largest residual_low -46.1 / -95.6 / -20.0 L; Kobo one DELIVERY_RECORDED_LATE. No UNEXPLAINED, no EXCESS night.

## check_manifest

12 failed before (`check-manifest-before.log`: main's 6 + six H5); 6 failed after (`check-manifest-after.log`, 7,882 passed):
main's 6 as they were before DD3b (4 walkthrough alignment lines, the walkthroughs figure line and H9, which prints 4599
and not 4574: DD3b's unre-based +24, and +1 here from Kobo's note being one more manifest string checked; H9 fails
on main's account, as its `with 5 failed` says, so it is not re-based here).

## Plants (each seen failing, reverted)

`plant-port-none` (card a: Kobo July RAISED), `plant-b` (Kisiwa declares no a: three H5 FAILs "no declared level accuracy"),
`plant-c`, `plant-d`, `plant-parity-5L`, the six observer mutations (handoff), and the checker's own: floor removed
(`plant-c17-no-floor.log` 7 failed, and the real run above), C-DD2 equality removed (`plant-c2.log` 1 failed), C-DD8
equality removed (`plant-c8.log` 2 failed).

## Reach set and guards

RESULTS_PLACEHOLDER

## Known deviations

1. **C-DD2 "each Site-month" read as the books.** `FUEL_DELIVERY` litres equal the Site-month's fuel EXPENSE rows; a month
   the books bought none in has none (Mto never, Kobo July and August; consistent with D-DD.175). The card's literal
   "in every Site-month" cannot hold. For the reviewer to confirm.
2. C-DD8 is LIVE on the store and FAILs until DD5.1 loads readings ("no readings stored: the loader is DD5.1's"), as C-DD6
   does. Tank bounds, unserved energy and candidate minutes on the store are printed pending (DD5.1). `--pure` does not
   print night states: the tool has no store, so they are the evidence script's.
3. The loader sets the clock on the one store it builds (no module swap); the Foundation floor is read for the revision in
   force over the whole month, so DD6.1 must confirm the world's `valid_from` covers July.
4. Other documents still say "above 2 % tolerance" (`economic-metric-and-effect-contracts.md` 227 and 400, the
   traceability CSV, `integration-source-to-canonical-design.md` 463). D-DD.156 names the two `M` strings; these go to the
   design-doc alignment pass. The month-end dip is an ordinary-practice assumption (Assumed); D-DD.168's fixed schema has no
   `conditions` field for it.

## Residual risk and review focus

The served observation (bands in production composition) is first asserted end to end in DD6.1. Focus: the floor's adverse
branch and byte-identity when no floor binds; C-DD2's default; `stored_fuel_nights` (latest revision per night).
