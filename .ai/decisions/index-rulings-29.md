# Decision index: Demo-sprint and later rulings (index only) (D-DD.67 to D-DD.74)

- `D-DD.67` no-load basis one vocabulary: fuel-cost-2 admits DATASHEET_FIT (no parameter version change), client words "the datasheet-fitted idle fuel rate", set-equality test · live · specs/DD-demo-data/rulings.md
- `D-DD.68` parity test for D-DD.67, goldens from main 80661e824 (three bases, missing basis, no rate, parameter digest, words) · live · specs/DD-demo-data/rulings.md
- `D-DD.69` writer: one continuous execution per Site advanced one local day (288 steps), every pack; 2x288 = 576 test · live · specs/DD-demo-data/rulings.md
- `D-DD.70` Kisiwa and Mto pure run (D-DD.19) moves to DD3b DD3.3 on v9; Kobo's in DD3a gates DD3a merge · live · specs/DD-demo-data/rulings.md
- `D-DD.71` data-sheet tool writes source SITE, source_version 1, basis siblings too · live · specs/DD-demo-data/rulings.md
- `D-DD.72` readings source_id = binding row device_id; TEL_BINDING refusal · live · specs/DD-demo-data/rulings.md
- `D-DD.73` DD3a 4.0 u, DD3b 5.0 u; DD 35.75 u in eight parts · live · specs/DD-demo-data/rulings.md
- `D-DD.74` DD2b V1: option (c) as a fix, `world_history.py exports --tenant` (repeatable; EMU_TENANT_UNKNOWN), world.py L1 and DDR S3 and two runbooks pass it; DD2b 4.5 u, DD 36.25 u; DD5 unchanged · live · specs/DD-demo-data/rulings.md
