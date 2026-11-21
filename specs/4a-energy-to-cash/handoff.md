# 4a handoff (PARTIAL): units 1 and 2 (code) done; Postgres tests, plants, packet open

Implementer (Claude), 2026-11-21. Branch `task/4a-energy-to-cash`, worktree `/opt/assetecon/AssetOpsV1-4a`. Stopped
at the context limit (standing brief). Mid-build questions: 0.

## Done (commits)

- `30bbd12d8` unit 1: registry v4 (`rows_mini_grid.py` two `stated_by`, `registry.py`), `check._stated` (`or
  row.unit == KWH`), `sources.py` (six leaves PROVIDED, `STATED_STATE` +2, `ENERGY_LEAVES`/`ENERGY_STATED`),
  `money.py` (one branch in `stated`), `targets/rules.py`/`read.py` (`MAIN_OF` tuples, D-4A.9),
  `structure/energy/rules.py` (§2.4), `source.py` (§3); tests 1, 2 (V1-V26, V9b, V9c), 2b (`STEPS`/`STEP_MAP`), 4,
  5, 6, 7, 8; unit-test sweep pins.
- `bc0c2ac5c` unit 2 code: `technical-loss-band` (`sites/models.py`, `minigrid_foundation.py`), `MiniDepthRead.
  feeder_month` + `FeederMonthRows` + `_ACCEPTED_FEEDERS` (`mini_depth/read.py`), `structure/energy/inputs.py`
  (`feeder_month`, `read_kwh`, `StoreEnergyInputs`), `energy/composition.py`, fifth builder in
  `structure/composition.py`; tests 3, 6b, 9, V15 register read, composition L1 (fifth builder).
- No-DB state at `bc0c2ac5c`: `test_4a_energy_to_cash.py` 117 passed with `test_4b_money_leaves.py`; the unit
  regression (3a4, 3b1, 3b3, 3b7a, 4b, 4b1, 4d, 5a, 5b, component_properties, w205a, w402, addressed_bindings,
  fuel_cost_v2, k1, w201) 829 passed, 1 skipped, 0 failed (`-n 4`). `check-architecture.ps1` passed (set
  `ASSETOPS_GUARD_PYTHON`).

## W6 sweep so far (old -> new; reason)

| Test | Old | New | Reason |
|---|---|---|---|
| `test_3b1_structure_registry.py:88`, `test_3b3_structure_evaluate.py:376`, `test_4b1_stated_nodes.py:291` | `version == 3` | `4` | registry v4 |
| `test_3b3_structure_evaluate.py:664`, `test_4b1_stated_nodes.py:379` | `("MINI_GRID", 3, ...)` | `4` | registry v4 |
| `test_3b3_structure_evaluate.py` `STATE_TABLE`, `PROVIDED_CAUSE` | six energy leaves HELD/NOT_CONNECTED | PROVIDED; read alone NOT_CONNECTED | §2.2 |
| `test_4b_money_leaves.py` `STATE_TABLE`, `STATED_TABLE` | as above; 2 stated | + `metered_kwh`, `billed_kwh` | §2.2 |
| `test_4b_money_leaves.py` `MTO_MISSING`, `REVENUE_NINE` | 13 / 9 names | + `billed_kwh`, `metered_kwh` | stated kWh nodes absent without the energy source |
| `test_4b_money_leaves.py` `assert_read_as` | `READ_AS[f]` | `ENERGY_READ_AS` for the two nodes | stated kWh nodes name their `stated_by` |
| `test_4b_money_leaves.py` test 13 | `_sources` is `CommercialLeafSource` | `EnergyLeafSource` in front of it | fifth builder (§4.3) |
| `test_4b1_stated_nodes.py` s8, s9 | two stated rows; asked (`revenue`, `fuel_cost`) | four; fake answers the kWh nodes NOT_CONNECTED | stated kWh nodes |
| `test_3b7a_site_inputs_seam.py:49` | `["revenue", "fuel_cost"]` | `["metered_kwh", "billed_kwh", "revenue", "fuel_cost"]` | stated kWh nodes |
| `test_5a_targets.py` test 4 | `MAIN_OF` strings | tuples | D-4A.9 (MAIN_OF) |
| `test_5a_targets.py:695` | MTO out list without kWh nodes | + `billed_kwh`, `metered_kwh` | target-side stated kWh nodes absent |
| `test_w402_roles_properties.py:91-109` | 8 carriers | + `technical-loss-band` | new property |

## Next (in order)

1. Read the Postgres regression log `/opt/assetecon/evidence/4a-energy-to-cash/pg-regression.log` (3a4, 3b3,
   3b7a, 4b, 4d, 5a, 5b postgres at `bc0c2ac5c`, started in the background) and sweep e2e pins by class (spec
   §6.4: `test_5b_attribution_postgres.py` Kobo/Kisiwa/Mto revenue now split as far as billed kWh and tariff are
   observed; `test_5b_attribution.py:434` `REVENUE_UNOBSERVED` passed unchanged at no-DB level). Also
   `test_3b3_structure_read_postgres.py`, `test_s1_foundation_postgres.py`, `test_s3_dispatch_assessment_postgres.py`
   (class grep hits).
2. Pre-flight (d), a hard stop before PG1b: in the D-4A.22 world seal one feeder batch after a Foundation change,
   print its disposition; not ACCEPTED -> `mid-build-questions.md`.
3. Write `backend/tests/fixtures/energy_to_cash_mto.json` (§5.5) and `test_4a_energy_to_cash_postgres.py` (PG1,
   PG1b, PG2, PG3; spec §6.2 and D-4A.15/17/21/22). Harness files: `tests/test_walk1_productive_producer_postgres.py
   :1-100`, `tools/demo_combined_kobo.py:60-140`, `tests/test_s4_consequence_store_postgres.py:85-105`,
   `sites/foundation_service.py:505-620`. PG1(e): if the structure read refuses the producer Site, mid-build question.
4. Plants P1-P27 (reviewer guide) in a scratch copy, each failing its named test; P18, P24 need PG1(b)/PG1b(c).
5. Fast check-all (`pwsh -NoProfile -File tools/check-all.ps1`), `check-agent-workflow.ps1`; packet
   `specs/4a-energy-to-cash/packet.md` (sweep table above + e2e rows, stored-snapshot statement D-4A.25, plants,
   `R-PRODUCTIVE`, `R-TARIFF`, `R-ABSENT-META`, mid-build count); spec `Status: in_review`; `.ai/state` entry +
   index line. 5c record keys only if 5c and SC-1a have merged (they had not at `aa3ebefe8`).

## Anchors and choices a reviewer should see

- `rules.py`: coverage only on `delivered_kwh` (spec §2.4 table); technical and unexplained carry delivered's cause
  and note without coverage (V3's "coverage (30, 31)" asserted on delivered). Unexplained sources are the sorted
  union; technical's are `("readings:feeder_demand", "foundation:technical-loss-band")` in spec order.
- `inputs.py` imports `commercial.months._parse` (3A4's rule, reused, so `structure/energy/` has no `except`; test 8
  asserts none). Origins: GOOD readings with a kW value overlapping the month.
- `money.py`: the `ENERGY_STATED` branch runs before the key lookup.
- No migration, no guard edit, no served text. Live DBs: none held by this run except the background regression's
  harness clones.

## Risks

- e2e literals in `test_5b_attribution_postgres.py` / `test_3b7a_*_postgres.py` will move (expected by §6.4); each
  must be justified in the packet, any other move is a mid-build question.
- PG1b's harness (2,232 readings through central ingestion) is the largest new test; size its runtime.
