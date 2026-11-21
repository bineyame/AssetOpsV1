# DS4 mid-build questions

Implementer (Claude), 2026-11-21, on `task/DS4-template-ladder` (base `eb78c5684`). Count: 1.

## MBQ-1 The spike (D-DS4.18) differs from spec §2.1 in 15 Site-side cells beyond the known `adjustments_kwh`

**Spike.** `assetops_ds4t<hex>_audit_spike` (created, used, dropped; `spike2` likewise), temporary 0700 key directory,
exports in a temporary directory. Every step exited 0: migrate, digest, check, apply, exports, load (`commercial_exit` 0,
`batches` 0), snapshot build (three Sites, nothing excluded), observe. `structure_snapshot` count 4. After `pseudonym_key
erase`, a second L1 into the same key directory applied (exit 0, new tenant id). Per Site and side the E/B counts equal
§2.1's (actual 18/29, plan 36/11) only by coincidence of the counted classes; the cell-by-cell comparison differs:

| Site | Side | Factor | §2.1 | Spike (value, `missing.record_kind`, `missing_leaves`) |
|---|---|---|---|---|
| all three | actual | `adjustments_kwh` | B | 0 (known: D-DS4.25, `C4_KNOWN_FINDINGS`) |
| KISIWA-001 | actual | `om` | E (700.0) | blank, `EXPENSE (OM)` |
| KISIWA-001 | actual | `cost_to_serve`, `contribution` | E | blank, `missing_leaves ['om']` |
| all three | plan | `tariff` | E (0.55 / 0.40 / 0.40) | blank, `BUDGET_LINE` |
| all three | plan | `diesel_price` | E (1.30 / 1.25 / 1.25) | blank, `BUDGET_LINE` |
| all three | plan | `necessary_l` | E (2300 / 700 / 300) | blank, `BUDGET_LINE` |
| all three | plan | `diesel_l` | E | blank, `missing_leaves ['necessary_l']` |

**What the inputs show.** (a) Kisiwa's O&M is not in the exports by design: `unwritten.json` lists
`lakeside-power KISIWA-001 2026-10 actual om ESTIMATED_NOT_RECEIVED`, and `lakeside-power.expenses.csv` has no Kisiwa
O&M line (Kobo and Mto have one). So the world honestly has no Kisiwa O&M record and the pack's 700.0 is an estimate.
(b) The budget export does carry the lines (`tariff_usd_per_kwh` 0.55, `diesel_usd_per_l` 1.30, `diesel_l` 2300 at
Kisiwa, and the Kobo/Mto equivalents), but the plan side reads `tariff`, `diesel_price` and `necessary_l` as blank
`BUDGET_LINE`. Either the budget layout or the target rule does not take those three lines (the `diesel_l` MAIN solve
the spec's † cell names), or §2.1 assumed a path the product does not have. I did not trace which; that is the
Architect's call (code anchors: `structure/targets/rules.py` `TARGET_RULE`, the budget layout in `layouts_v1.py`).

Full printout (282 factor lines, step exits and timings): `/opt/assetecon/evidence/DS4/spike-2026-11-21/spike.log`.

**What I did meanwhile (spec §6: "While you wait, §3.1 to §3.4 may proceed").** Built unit 1 and unit 2 to the spec as
written. `C4_CONTRACT` is §2.1's literal unchanged and `C4_KNOWN_FINDINGS` holds only the three D-DS4.25 lines. So the
real-world C4 in T12 reports these 15 cells as `new` FAIL lines, and T12's C4 assertion fails: that is the open part,
stopped there. Nothing was adapted.

**Proposed default.** (a) Kisiwa `om`, `cost_to_serve`, `contribution` actual: a spec edit to `B` (Src R, the record
`EXPENSE (OM)`, `ESTIMATED_NOT_RECEIVED` in the manifest), with a site-specific contract cell, since the table is no
longer the same at all three Sites. (b) Plan `tariff`, `diesel_price`, `necessary_l`, `diesel_l`: a product finding
(the budget export carries the lines; the product should read them), routed to the budget/target unit and added to
`C4_KNOWN_FINDINGS` (12 lines) until fixed. Either answer is a two-line change to the literals; the C4 mechanism and
T9/T9b need no change except T9b's counts if (a) makes the contract per Site.
