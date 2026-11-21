# 4a review packet: energy to cash, where the kWh went

Implementer (Claude), 2026-11-21. Branch `task/4a-energy-to-cash` (base main `aa3ebefe8`; main has since moved, merge
check is the coordinator's), head: the commit carrying this packet. Spec rev 2, rulings D-4A.1-26, reviewer guide rev 2.
`USER_REVIEW_REQUIRED: false` (non-screen; 5c owns the screen). Mid-build questions: **2**, defaults applied, none
blocking (`mid-build-questions.md`). Layout evidence: not run (no UI change).

## Outcome

MINI_GRID registry v4 states `metered_kwh` (customer meter reads) and `billed_kwh` (billing export). A new pure
`structure/energy/rules.month_energy` gives the eight energy factors (delivered, technical, metered, unexplained,
adjustments, unmapped, billed, tariff) from one `EnergyInputs` per Site-month. Every absence is value None,
`NOT_AVAILABLE`, with a cause and a note ("Not available yet"), never 0. `EnergyLeafSource` is the fifth builder in
`build_structure_read`. No migration, no guard edit, no served text.

## Files

New: `structure/energy/{__init__,rules,inputs,source,composition}.py`; tests `test_4a_energy_to_cash.py`,
`test_4a_energy_to_cash_postgres.py`; fixture `tests/fixtures/energy_to_cash_mto.json`. Edited, only the spec's list:
`rows_mini_grid.py`, `registry.py`, `check.py`, `sources.py`, `money.py`, `structure/composition.py`,
`targets/rules.py`, `targets/read.py`, `sites/models.py`, `sites/minigrid_foundation.py`, `mini_depth/read.py`; the
W6 sweep lines below.

## Acceptance (spec §8)

1. Mto chain 6000 → 300 → 5580 → 120, unmapped 140: tests 1 and PG1b (real readings and a real Foundation band), PG2.
2. "Never 0": the pure layer in test 1 (Kobo) and 2b; the evaluated structure in PG3(a) (Kobo `FEEDER_NOT_BOUND`) and
   PG1(e) (see Q2).
3. Tariff 0.4 = billed money / billed kWh: tests 1 and V13/V14/V16, PG2.
4. Bridge: VOLUME `billed_kwh` [0.40] gap 95, +38.00; PRICE `tariff` [8645] 0.00; children sum +38.00; RESIDUAL
   0.00; without the billed budget line revenue is NOT_SPLIT: PG3(a), PG3(b).
5. Origins: SIMULATED readings → `demo-simulated`, LIVE → `unknown` (test 3, PG1(a), PG1b(a)); a live read passes no
   cutoff (6b).
6. Every §2.4 step reached: 2b's step map equals the hand `STEPS`.

## Checks (real output; logs under `/opt/assetecon/evidence/4a-energy-to-cash/`)

| Check | Revision | Result | Wall |
|---|---|---|---|
| Postgres regression, 7 files (3a4, 3b3 read, 3b7a snapshot, 4b, 4d, 5a, 5b), `heavy-slot --db` + `run-host-tests` (`pg-regression-2.log`) | `59ea84aa9` | 34 passed, 0 failed (fix of the 3B3 version pin confirmed) | 46.9 s pytest, 3 m 41 s with slot wait |
| Dry run `ASSETOPS_HOST_DRY_RUN=1`: all 7 files are targets; `--collect-only`: 34 tests over the 7 (the count is right, not a dropped file) | `59ea84aa9` | exit 3 (no run, by design) | |
| Pre-flight (d) (`preflight-d.log`): one feeder batch sealed after the band's Foundation change | world of Q1 | status 200, 24/24 ACCEPTED | |
| `test_4a_energy_to_cash_postgres.py` (`pg-4a.log`) | ``1052af7e8`` | 4 passed, 0 failed (PG1+PG1b, PG2, PG3a, PG3b) | 33.0 s pytest, 12 m 8 s with slot wait |
| No-DB: 4a, 3B2 (`test_3b2_findings_pinned.py`), 3b1, 3b3, 4b, 4b1, 3b7a seam, 5a, 5b, 4d, 3a4, component properties, w205a, w402 (`nodb-regression.log`) | `1052af7e8` | 783 passed, 1 skipped, 0 failed (7.2 s, `-n 4`) | |
| `pwsh -NoProfile -File tools/check-all.ps1` (fast; `check-all.log`) | `1052af7e8` | All 40 guards passed | 2 m 39 s |
| `tools/check-agent-workflow.ps1` | `1052af7e8` | passed | |

## Plants P1-P27 (reviewer guide), on a scratch copy of HEAD, each reverted

Runner `proto/plants.py` (copy of HEAD, deleted after the run; diff against the worktree after the run: identical). Each plant is
one string edit; "caught" means the named test **failed** (an import or collection error does not count).
All 25 no-database plants were caught (`plants/result-nodb.txt`): P1 test 1 Mto, P2 V12, P3 test 1 Kobo, P4 V3, P5
V12, P6 test 1 Kobo, P7 V9, P8 V13, P9 V13, P10 V6 (straddle step removed), P11 V5, P12 test 4, P13 test 5, P14
test 6, P15 test 7 (2 failed), P16 test 3, P17 test 9, P19 test 1 Kobo, P20 V9c (the account route matches any
registered customer), P21 V18, P22 6b, P23 6b (errors turned into the fallback's absence; 2 failed), P25 2b billed
step 3, P26 V19, P27 V26. The two PG plants ran in the worktree at clean HEAD, reverted by `git checkout` (status after: clean; the copy cannot use the slot pool): P18 caught at PG1(b) `216 == 144`; P24 caught at PG1b(c), technical `MONTH_OPEN` not `LOSS_BAND_NOT_DECLARED` (`plants/result-pg.txt`).

## W6 sweep: every pinned literal changed in an existing test (old → new; reason)

| Test:line | Old | New | Reason |
|---|---|---|---|
| `test_3b1_structure_registry.py:88`, `test_3b3_structure_evaluate.py:376`, `test_4b1_stated_nodes.py:291` | `version == 3` | `4` | registry v4 |
| `test_3b3_structure_evaluate.py:664`, `test_4b1_stated_nodes.py:379` | `("MINI_GRID", 3, ...)` | `4` | registry v4 |
| `test_3b3_structure_read_postgres.py:82` | `("MINI_GRID", 3)` | `4` | registry v4 |
| `test_3b3_structure_evaluate.py` `STATE_TABLE`, `PROVIDED_CAUSE` | six energy leaves HELD / NOT_CONNECTED | PROVIDED; read alone NOT_CONNECTED | §2.2 |
| `test_4b_money_leaves.py` `STATE_TABLE`, `STATED_TABLE` | as above; 2 stated | + `metered_kwh`, `billed_kwh` | §2.2 |
| `test_4b_money_leaves.py` `MTO_MISSING`, `REVENUE_NINE` | 13 / 9 names | + `billed_kwh`, `metered_kwh` | stated kWh nodes absent without the energy source |
| `test_4b_money_leaves.py` `assert_read_as` | `READ_AS[f]` | `ENERGY_READ_AS` for the two nodes | they name their `stated_by` |
| `test_4b_money_leaves.py` test 13 | `_sources` is `CommercialLeafSource` | `EnergyLeafSource` in front of it | fifth builder (§4.3) |
| `test_4b1_stated_nodes.py` s8, s9 | two stated rows; asked (`revenue`, `fuel_cost`) | four; the fake answers the kWh nodes NOT_CONNECTED | stated kWh nodes |
| `test_3b7a_site_inputs_seam.py:49` | `["revenue", "fuel_cost"]` | `["metered_kwh", "billed_kwh", "revenue", "fuel_cost"]` | stated kWh nodes |
| `test_5a_targets.py` test 4 | `MAIN_OF` strings | tuples | D-4A.9 |
| `test_5a_targets.py:695` | MTO out list without the kWh nodes | + `billed_kwh`, `metered_kwh` | target-side stated kWh nodes absent |
| `test_w402_roles_properties.py:91-109` | 8 carriers | + `technical-loss-band` | new property |

E2e literals: **none moved.** The class grep (§6.4) named `test_5b_attribution_postgres.py`,
`test_5b_attribution.py:434` `REVENUE_UNOBSERVED`, `test_3b7a_*_postgres.py`, `test_s1_foundation_postgres.py`,
`test_s3_dispatch_assessment_postgres.py`; the 5b, 3b7a and 3b3 Postgres files pass unchanged at `59ea84aa9`, because
5b's fixture world carries no meter reads or register, so its revenue stays unsplit as before. The `test_s1`/`test_s3`
hits are not pinned literals of this class and were not changed. `test_w205a_ev_vocabulary.py:131` unchanged (D-4A.18).

**Stored snapshots (D-4A.25):** a 3B7a snapshot built at version 3 is served `REBUILD_NEEDED` (`STRUCTURE_VERSION`)
until 3B7a's build rebuilds it; 4a writes no migration and touches no stored snapshot.

## Known deviations

- **Q1:** D-4A.22's world dates (08-31/09-01) precede the Kobo Foundation (2026-09-29T11:57:49Z). Used 2026-09-29T12:00Z /
  2026-09-30T06:00Z (roles-4 still covers October), plus `enable()` of the gateway and sources, as the producer demo does.
- **Q2:** PG1(e) expects unexplained `LOSS_BAND_NOT_DECLARED`; §2.4 (binding) makes it take delivered's absence first
  (`FEEDER_READINGS_GAP` after days 1-3). The test asserts §2.4; both factors are None / NOT_AVAILABLE.
- **5c record keys are not done:** they wait on 5c and SC-1a merging (D-4A.12, D-4A.20, D-4A.24); untouched here.

## Residual risk

- `R-PRODUCTIVE` (D-4A.10): billed kWh counts standard usage only; with productive usage, billed's disagreement with
  metered reads as less leakage. Every demo Site has productive kWh 0.
- `R-TARIFF` (D-4A.6): a mix of tariff codes reads as one average price.
- `R-ABSENT-META` (D-4A.17): `unexplained_loss_kwh` keeps `absent: ZERO_WHEN_HELD` (manifest parity) while the product
  says "Not available yet"; nothing reads it (test 8 asserts no `absent` read under `structure/energy/`).

## Review focus

The §2.4 step order (2b map); the customer join (V9b/V9c, P6/P20); the cutoffs (PG1(b), PG1b(c), 6b); Q1 and Q2; that
the sweep rows above are every changed literal (`git diff aa3ebefe8 -- backend/tests ':!*test_4a*'`).
