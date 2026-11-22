# Decision index: Demo-sprint and later rulings (index only) (D-DD.67 to D-DD.79)

- `D-DD.67` no-load basis one vocabulary: fuel-cost-2 admits DATASHEET_FIT (no parameter version change), client words "the datasheet-fitted idle fuel rate", set-equality test · live · specs/DD-demo-data/rulings.md
- `D-DD.68` parity test for D-DD.67, goldens from main 80661e824 (three bases, missing basis, no rate, parameter digest, words) · live · specs/DD-demo-data/rulings.md
- `D-DD.69` writer: one continuous execution per Site advanced one local day (288 steps), every pack; 2x288 = 576 test · live · specs/DD-demo-data/rulings.md
- `D-DD.70` Kisiwa and Mto pure run (D-DD.19) moves to DD3b DD3.3 on v9; Kobo's in DD3a gates DD3a merge · live · specs/DD-demo-data/rulings.md
- `D-DD.71` data-sheet tool writes source SITE, source_version 1, basis siblings too · live · specs/DD-demo-data/rulings.md
- `D-DD.72` readings source_id = binding row device_id; TEL_BINDING refusal · live · specs/DD-demo-data/rulings.md
- `D-DD.73` DD3a 4.0 u, DD3b 5.0 u; DD 35.75 u in eight parts · live · specs/DD-demo-data/rulings.md
- `D-DD.74` DD2b V1: option (c) as a fix, `world_history.py exports --tenant` (repeatable; EMU_TENANT_UNKNOWN), world.py L1 and DDR S3 and two runbooks pass it; DD2b 4.5 u, DD 36.25 u; DD5 unchanged · live · specs/DD-demo-data/rulings.md
- `D-DD.75` kernel forcing index by step (`_compute_exposures`, lazy, byte-identical), parity golden from main's kernel (K1-K8, D1, F1, X1, W1, S1); mini-grid only, cold and EV unreached; (b) and (c) refused · live · specs/DD-demo-data/rulings.md
- `D-DD.76` mini-grid tanks declared by the Site (SITE v1, /2 and /1): two months of the largest month's litres, rounded to a standard size: Kobo 2500, Kisiwa 5000, Mto 1000 L; notes unchanged; D-DD.19 fallback restated · live · specs/DD-demo-data/rulings.md
- `D-DD.77` Kobo sun outside season v2's calendar = clear shape x solar_surplus day weight (Jul-Aug 0.80), not all clear · live · specs/DD-demo-data/rulings.md
- `D-DD.78` DD3a Update 4 deviations ratified: hour-block forcings, largest remainder, load shape, critical order, skips, rounding, tank failures as TEL_PACK, C-DD21 · live · specs/DD-demo-data/rulings.md
- `D-DD.79` DD3a 4.75 u (DD3.1 2.25, DD3.2 2.5), DD3 9.75 u, DD 37.0 u; order inside DD3a · live · specs/DD-demo-data/rulings.md
