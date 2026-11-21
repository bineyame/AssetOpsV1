# 3B6 reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): two new structures on the shared core and a change to how
portfolio reads exclude a Site. Read `spec.md`, `rulings.md`, then the diff. Done means every question of spec §8
answers yes with evidence and every plant below fails its named test. Run nothing heavy yourself unless a finding needs
it; cite the builder's gate run at the same commit (`.ai/ROLE_CONFIG.md`).

## What to check, and how

1. **Independent checks (W2).** Tests 1, 2, 4, 4b read the pack (`demo-site-scenario-manifest.yaml`,
   `derived-values.json`) or the test's own literals; none reads `rows_cold_chain.py`, `rows_ev_depot.py`, `HOMES`,
   `SOURCE_STATE` or the evaluator for an expected value.
2. **No vertical code.** `git diff main...HEAD -- backend/assetops_backend/structure/evaluate.py
   backend/assetops_backend/structure/expressions.py` is empty. `check.py` and `read.py` contain no `COLD_CHAIN` or
   `EV_DEPOT_CAPTIVE` literal (only `registry.py`, the row files, `pins.py` and `sources.py` name them).
3. **Not applicable is not zero.** No EV row named `revenue`; `applicability` is pure and total; the cross-registry check
   runs over the checked set only (spec §2.4 item 2).
4. **Unknown is not zero.** Every cold and EV leaf without a provider is `NOT_AVAILABLE` with the manifest's record kind;
   no money node of either Site reads 0 (test 5b).
5. **The exclusion class (W6).** The packet's §4.4 grep table covers every hit; each portfolio reader uses
   `sites_excluded`; each mini-grid-only Site reader refuses with `STRUCTURE_KEY_NOT_READ`; no `KeyError` path remains
   (test 8).
6. **The sweep.** Every changed literal in an existing test is in spec §6.3 with its reason; any other is a finding.
7. **Seams.** `git diff main...HEAD --stat` lists only spec §0's files; no migration, no `tools/` change; check-all and
   `check-architecture.ps1` pass; no served text.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Must fail |
|---|---|---|
| P1 | One cold node expression differs from the manifest (`energy: "kwh * elec_price * 1"`) | test 1 |
| P2 | EV gains a `revenue` node `"0"` | test 1 and test 5 |
| P3 | EV `not_applicable` emptied | test 5 |
| P4 | `REGISTRIES["COLD_CHAIN"]` holds the EV registry | test 3 (L2) and start-up |
| P5 | `not_applicable=("revenu",)` | test 3 and `create_app` |
| P6 | `not_applicable=("cost_to_serve",)` | test 3 |
| P7 | cold `staff` absent `ZERO_WHEN_HELD` | test 1 |
| P8 | one cold leaf missing from `SOURCE_STATE["COLD_CHAIN"]` | test 5b (key set) |
| P9 | `minutes_per_day` provider returns 1400 | test 5b |
| P10 | cold `staff` state `PROVIDED` | test 6 (raising commercial fake) |
| P11 | `sites_excluded` returns `NOT_DECLARED` for a cold Site | test 8 |
| P12 | `TargetRead.site` without the `KEY_NOT_READ` guard | test 8 (KeyError, not StructureError) |
| P13 | EV `charger_kw` composes `SUM` | start-up (`STRUCTURE_COMPOSES`) and test 2 |
| P14 | `COLD_START_FAILURE` pinned to `nights_without_backup_cover` | test 7 (`STRUCTURE_PIN_TOTAL`) |
| P15 | cold `model_factor` neutral 0 | test 2 and test 4 (`kwh_model` 0) |
| P16 | `buses_short_per_night` composes `SUM` | test 2 |
| P17 | an EV `NOT_CONNECTED` leaf returns value 0 | test 5b |
| P18 | `StructureRead.portfolio` ignores `structure_key` (composes MINI_GRID always) | test 8 |

## Not findings

- Stored snapshots reading "rebuild needed" after merge (code digest; spec §6.3).
- The pack's portfolio sums of prices and per-night rates not compared (they are `NONE` here).
- `capacity_crate_days`, `excess_kwh` and every record-fed leaf reading "Not available yet" (D-3B6.10, `9d`, `9e`).
