# DD3d-b handoff (partial: run 1 stopped at its context budget, 23 Nov)

Branch `task/DD3d-b-fuel-cost`, worktree `/opt/assetecon/AssetOpsV1-dd3db`, cut from main aae7d9826. Card
`cards/DD3d.md` Part DD3d-b, **as amended by `rulings.md` round 28 (D-DD.177 to D-DD.180, the last 80 lines: read them
first)**. Evidence `/opt/assetecon/evidence/DD3d/b/`. No job is running. Architect questions: one batch of four,
answered by an `assetops-architect` subagent this builder spawned (no lane-Architect session was asked): the
coordinator should confirm the four rulings. The branch is RED by design until the tests below follow (116 pure failures).

## Done (DD3d.4, product part; not reviewed, no Postgres run yet)
- `test_dd3d_fuel_cost.py` (9): 6 failed first (`fuel-cost-first.log`). Rows v5, `STATED_STATE`, `money.FUEL_BOUGHT`,
  `_ROWS`/`READ_AS` `fuel_bought`; reconciliation heading key `fuel_bought` / word `FUEL_BOUGHT` (label "Fuel bought
  (invoices)", record noun "fuel invoices"); statement field and flag unchanged.
- `evaluate(..., stated_nodes=)`, `targets/rules.BUDGET_STATED`, `targets/read.py` (D-DD.178). Its tests are not written.
- `publish_assumption.py` checks `served_tenant_slug()` (exit stays 2, D-DD.179); a malformed slug is a traceback at
  parse, handle `ConfigurationError`. Three fixtures `backend/conversions/world/lakeside-power.diesel-price.*.json`
  (parity test in place). Publisher tests in `test_s4_assumptions_postgres.py` are not written.
- Rulings and index lines appended.

## Pure failures to work (`pure-1.log`; rerun `/opt/assetecon/evidence/DD3d/b/pure.sh LOG`, 80 s)
1. Renames and version pins (mechanical): 3a7 x15 ("fuel_cost" heading key -> "fuel_bought", "Fuel cost (" -> "Fuel
   bought (invoices) ("), `statement_cases/{worked,reconciliation}.py` (`FUEL_COST` -> `FUEL_BOUGHT`), 3b1 x2, 3b3 x3,
   4a x1, 4b1 x9 (fuel_cost was one of the stated examples: move them to `revenue`), 5a x1 (a table), 6a x1.
2. Worlds that state fuel by invoices and hold no litres (4b money x10, 4d x4, 5b x5, 5c view x23 + api x2 +
   screen_worlds_fresh x2, iap x17, 3b7a x7, sc1 x14): 4b's assertions become "not available, the litre leaves named";
   the 5b/5c/iap/3b7a worlds need litres. Plan: one helper (`backend/tests/pack_litres.py`) wrapping `fallback()` with
   MODELLED litre leaves per Site so the pack's figures hold: Kobo 730/330/120 (already `test_4d.LakesideInputs`),
   Kisiwa 2,400 x 1.30 = 3,120, Mto 320 x 1.25 = 400; used by `t5b.reads` (line 462, 838), `served_world` (5c view
   line 72), `3b7a setup`. `fb=` is already a parameter of `3b7a.setup` / `served_world`. Literals then change only in
   evidence words and SPLIT (fuel now splits into litres): World A's "not split to its drivers yet" lines, the litre
   rows of `not_available`, and fixture `5c/deep_dive_lakeside_2026-10.json`, the `statement_cases/deep_dive.py`,
   `frontend/src/estate/__tests__/fixtures/*` regenerate from the same worlds (list each in the packet).

## Next, in order
1. The tests above; D-DD.178 tests; publisher Postgres tests; G4 + its tests (`test_ddr_rehearsal_check.py`): code
   `rehearsal_check.py:380` loop, `PRICE_SOURCE`; declared price is evidence ESTIMATED/ASSUMED per
   `sources.ASSUMPTION_WORDS["diesel_price"]`, prints "declared, no fuel invoice this month".
2. DDR (D-DD.177): `LitreLeafSource._month` replaced in the fixture from `M`; `fuel_bought` key; S5/S8 offsets;
   `test_7`; runbook sentence. C4 classes in `tools/world.py` (Mto plan classes only in DD3d.5's commit).
3. `dd_check` C-DD4 fuel clause (D-DD.180), tests in `test_dd2_check.py`.
4. DD3d-a Lows L1 to L6 (`review-DD3d-a.md`): not started.
5. DD3d.5 whole: `--leaves` `quarter`, `RUN_WRITTEN["MINI_GRID"]["plan"]`, guard test, `M`, then the D-DD.176 form of
   the acceptance (generate 2 and 3 byte-identical, every `--check` 0), D-DD.30 chain, re-pins, anchors, A114 confirm.
6. Plants a to d (a amended by D-DD.177), reach set once, guards, packet, state entry, spec in_review. Amend the DD5b
   card with D-DD.177's "DD5b card gains" lines and the DD3d card's plant (a) and C-DD4 lines.

## Anchors and risks
- `M` line 83 prices; `M`'s Kisiwa October litres are 903, so fuel projects 2,006.40 and the headline about −195.30
  (not −196.60); owner to be told. No served figure was measured in this run.
- `targets/read.py` `MAIN_OF` heading fuel_cost; `deep_dive/tables.py:46` evidence `FUEL_INVOICES` needs no edit.
- `tools/dd3_pure_run.py`: `october_leaves` 254, `print_leaves` 326, `LEDGER_KEYS` 53. `world/scope.py` `RUN_WRITTEN`.
- `world/history.py` `RUN_DERIVED` may gain plan keys computed from the new `RUN_WRITTEN` plan keys (`per_day`): check
  before step 5's diff (D-DD.176 5c).
