# 3B6 reviewer guide

Architect (Claude), 2026-11-21, rev 2 (handshake round 1, `rulings.md` D-3B6.13 to D-3B6.24). Discovery review (W5): two new structures on the shared core and a change to how
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
3. **Not applicable is not zero, and is claimed no further than built.** No EV row named `revenue`; `applicability` is
   pure and total; the cross-registry check runs over the checked set only (spec §2.4 item 2). The packet and the
   code claim "declared, checked, queryable" only: a sentence saying a read, a screen or a record "shows" revenue as
   not applicable is a finding (D-3B6.14); `applicability()` has no caller outside tests.
4. **Unknown is not zero, and a held record is real.** Every cold and EV leaf without a provider is `NOT_AVAILABLE`
   with the manifest's record kind; no money node of either Site reads 0 (test 5b). Every `HELD_NOT_CALCULATED` leaf
   cites a stored record that exists (test 5c): open each cited file at the token and confirm it is a binding role or
   Foundation property, not a work case; a HELD leaf with no real record is a finding (D-3B6.13).
5. **The exclusion class (W6).** The packet's three-grep table (spec §4.4: G1, G2, G3) covers every hit; each portfolio
   reader uses `sites_excluded`; each mini-grid-only Site reader (`TargetRead.site`, `BridgeRead.site`,
   `SnapshotRead.site`) refuses with `STRUCTURE_KEY_NOT_READ` before it reads anything, so no leaf provider or lines
   store is called for a refused Site; no `KeyError` path remains (test 8). `BridgeRead.site` evaluates the target
   side first (D-3B6.17).
5a. **Shared IDs (`R-SHARED-ID`).** `COMMERCIAL_KEYS` gates `CommercialLeafSource.leaf`; test 6(b) holds by state, not
   by ID; `money._ROWS` keys and `COMMERCIAL_LEAVES` are otherwise unchanged (D-3B6.18).
6. **The sweep.** Every changed literal in an existing test is in spec §6.3 with its reason; any other is a finding.
7. **Seams.** `git diff main...HEAD --stat` lists only spec §0's files; no migration, no `tools/` change; check-all and
   `check-architecture.ps1` pass; no served text.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

Two classes (D-3B6.16). A **data plant** mutates the real rows or the real `REGISTRIES`: it fails tests 1 and 2 (which
read the real registries) and start-up (`create_app`), and **cannot** fail test 3, which passes its own mappings to
`check_all`. A **code plant** removes a line of code: it fails the test that exercises that line. Each row names every
test that fails; "only" means no other test may.

### Data plants

| # | Plant | Must fail |
|---|---|---|
| P1 | One cold node expression differs from the manifest (`energy: "kwh * elec_price * 1"`) | test 1 and test 4 |
| P2 | EV gains a `revenue` node `"0"` | test 1, test 5a and start-up (own-row refusal) |
| P3 | EV `not_applicable` emptied | test 1 (against `chain_model`) and test 5a |
| P4 | `REGISTRIES["COLD_CHAIN"]` holds the EV registry | tests 1 and 2 and start-up (L2) |
| P5 | `not_applicable=("revenu",)` | test 1, test 2 (`check_all()`) and `create_app` |
| P6 | `not_applicable=("cost_to_serve",)` | test 1, test 2 and `create_app` |
| P7 | cold `staff` absent `ZERO_WHEN_HELD` | test 1 |
| P8 | one cold leaf missing from `SOURCE_STATE["COLD_CHAIN"]` | test 5b (key set) |
| P10 | cold `staff` state `PROVIDED` | test 6(b) (the state assertion; not 6(c), which sets the state itself) |
| P13 | EV `charger_kw` composes `SUM` | start-up (`STRUCTURE_COMPOSES`) and test 2 |
| P14 | `COLD_START_FAILURE` pinned to `nights_without_backup_cover` | test 7 (`STRUCTURE_PIN_TOTAL`, and the `PINS` literal) |
| P15 | cold `model_factor` neutral 0 | test 2 and test 5b |
| P16 | `buses_short_per_night` composes `SUM` (not forced by `STRUCTURE_COMPOSES`) | test 2 only |
| P17 | an EV `NOT_CONNECTED` leaf returns value 0 | test 5b |
| P27 | a HELD leaf's record token absent from its file (rename the cited role in a scratch copy) | test 5c |
| P28 | `charger_out_days` set back to `HELD_NOT_CALCULATED` | test 5b (state table) and test 5c (the HELD set) |

### Code plants

| # | Plant | Must fail |
|---|---|---|
| P9 | `minutes_per_day` provider returns 1400 | test 5b |
| P11 | `sites_excluded` returns `NOT_DECLARED` for a cold Site | test 8 |
| P12 | `TargetRead.site` without the `KEY_NOT_READ` guard | test 8 (a `KeyError`, not `StructureError`) |
| P18 | `StructureRead.portfolio` ignores `structure_key` (composes MINI_GRID always) | test 8 |
| P19 | `nights_in_period` returns 31 for every month (or `period_days` hard-coded 31) | test 5b, the `2026-02`, `2026-11` and `2028-02` reads |
| P20 | the L2 key check removed from `check_all` | test 3 (`STRUCTURE_CATALOGUE COLD_CHAIN/-`) |
| P21 | the cross-registry not-applicable pass removed | test 3 (EV alone, and `revenu` on the three-registry set) |
| P22 | the own-row refusal removed from `_not_applicable` | test 3 (`check(EV)` with `cost_to_serve`) |
| P23 | the repeat refusal removed from `_not_applicable` | test 3 (`("revenue", "revenue")` through `check(EV)`) |
| P24 | the pattern refusal removed from `_not_applicable` | test 3 (`("Revenue",)` through `check(EV)`) |
| P26 | the `key in COMMERCIAL_KEYS` guard removed from `CommercialLeafSource.leaf` | test 6(c) (COLD `staff` reaches the raising commercial fake) |
| P29 | `BridgeRead.site` evaluates `site_inputs` before `targets.site` (the old order) | test 8 (the raising `site_inputs` fake is called) |
| P30 | `TargetRead.portfolio` includes a cold Site in its composition | test 8 (`OTHER_STRUCTURE` and the composed set) |

## Not findings

- Stored snapshots reading "rebuild needed" after merge (code digest; spec §6.3).
- The pack's portfolio sums of prices and per-night rates not compared (they are `NONE` here).
- `applicability()` having no caller outside tests, and no read showing revenue as not applicable (D-3B6.14).
- `capacity_crate_days`, `excess_kwh` and every record-fed leaf reading "Not available yet" (D-3B6.10, `9d`, `9e`).
