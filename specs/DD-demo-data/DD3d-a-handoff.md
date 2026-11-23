# DD3d-a handoff (partial: run 1 stopped at its context budget, 23 Nov)

Branch `task/DD3d-fuel-floor`, worktree `/opt/assetecon/AssetOpsV1-dd3d`, main merged at 558b32f32. Card:
`cards/DD3d.md` (DD3d-a). Evidence `/opt/assetecon/evidence/DD3d/`. No job is running. Mid-build questions: 0.

## Done
- **DD3d.1 except C-DD17.** `structure/observe/{rules,observe,service,composition}.py`, new `floor.py`
  (`StoreFloorRead`; `FloorReadPort` in `service.py`, optional constructor argument so `test_3b4_observer*` need no
  edit). `/2` file: three tanks declared. `backend/tests/test_dd3d_tolerance_floor.py` (37): 11 failed first
  (`floor-tests-first.log`); the other 26 are parity guards, each shown failing by a mutation
  (`plant-{strict-gt,unfiltered,none-source,band-none,two-tanks,port-none}.log`). Card plant (a) is `plant-port-none`.
  `test_dd3c_kobo_parity_postgres.py` injection dropped; NOT rerun yet, nor its +5 L plant (packet-DD3c line 37:
  +5 L on the roles-5 opening level at 18:00 must fail at fuel_balance).
- **DD3d.2 writer and loader.** `world/exports_fuel_records.py`; `world_history.py exports --telemetry`;
  `exports.DATED_NOTES` gains the recorded date as its sixth field (parity test `test_dd2_nodes.py` updated,
  `dd3_pure_run.py` unpacks it). `test_dd3d_fuel_records_file.py` (13; 12 failed first). `load_fuel_records.py`,
  `prepare_clock.py`; `test_dd3d_fuel_records_postgres.py` (15; `loader-first.log`), `test_dd1b1_prepare_clock.py`
  (33; 6 failed first, `guard-tests-first.log`). Card plants (c) and (d) seen failing and reverted (`plant-c.log`,
  `plant-d.log`; the writer's d too). Statement catalogue exit 0.
- **Digest chain (`/2` move).** file sha256 92ca8fed -> 18fd700e; `LAKESIDE_ALONE_SHA256` 7d582e06 -> c3260726;
  `config/world/fuel-leaves.json` `inputs_sha256` at KOBO, KISIWA, MTO re-recorded by `--leaves --write`
  (`leaves-rerecord.log`): only the three hash lines moved, every ledger figure is identical.
- **Pure run for evidence**: `/opt/assetecon/evidence/DD3d/pure/` (`pure-run.sh`): Lakeside telemetry for
  `READINGS_SPAN` in `parts-<SITE>/lakeside-power/telemetry/`, and `exports/lakeside-power/fuel-records.json` (Kobo 5
  dips + 3 deliveries, Kisiwa 5 + 8, Mto 5 + 0). Delete `parts-*` (about 230 MB) after the packet.

## Next, in order
1. **C-DD17** (`tools/dd_check.py` `within_tolerance`, `judge_unexplained_month`, `judge_pure_c_dd17`; tests in
   `simulator/tests/world/test_dd3b3_notes.py` from line 325 pin the old carve-out and must change with it). Own JSON
   read of a through `_components(onboarding, code, "FUEL_TANK")`; factor 2 typed, comment citing D-DD.153;
   consumption = burned + draw; `tol = max(pct / 100 x consumption, 2a)`; Kobo within Jul-Sep and above in Oct;
   Kisiwa equal to its draw and within every month; Mto 0; no a is a FAIL. `STUBS["C-DD17"]` becomes DD6.1 (served).
2. **C-DD2** (`judge_kinds`): `TANK_DIP` in every mini-grid Site-month. `FUEL_DELIVERY`: Mto buys no fuel and Kobo
   none in July and August, so "every Site-month" cannot hold literally. Default: the Site-month's FUEL_DELIVERY
   litres equal its fuel EXPENSE rows' litres (none where the books bought none). Record it in the packet.
   `judge_kinds(inputs, rows, tenants, fuel=None)`; None prints a pending line; the LIVE entry passes a new
   `stored_fuel_records(url)` (heads only, month by Site timezone; test it in `test_dd3d_fuel_records_postgres.py`).
3. **C-DD8**: a balance judge on records (first-of-month dips, deliveries by `taken_at_local`, burned by
   `step_litres`) per mini-grid Site-month, equal to `declared_draws` to 0.1 L; `read_pure` also reads
   `fuel-records.json` (missing is a FAIL). Store path: records plus `stored_readings` (empty until DD5.1, so it FAILs
   naming that, as C-DD6 does) and `fuel_balance_window` latest revision per night: print states per Site, FAIL on
   UNEXPLAINED, EXCESS or no assessed night. If C-DD8 goes LIVE, move it out of `STUBS` and update
   `backend/tests/test_dd1_check.py:101-104`.
4. Assemble the pure DIR (`pure-run.sh` in DD3b/fix2 shows the `measured.json` join; add `fuel-records.json`) and run
   `dd_check --pure`. Night states per Site for the packet: drive `fuel_balance.rules.assess` over the pure readings
   and the records (the tool has no store); any UNEXPLAINED or EXCESS night stops for the Architect.
5. **DD3d.3 H5** (`check_manifest.py` about line 1520), `M` lines 123 and 198, rev bump. Count before and after; plant
   (b). Read `/2` by its own JSON.
6. Reach set once, guards, packet, state entry 220 in `.ai/state/index-4.md`, spec in_review.

## Anchors and notes for the packet
- C-DD17 consumption moved since D-DD.153's table (DD3b fix rounds, `M` 16.23): Kobo September 785.2 L (table 773.20);
  the verdict is unchanged. Compare Kisiwa's and Mto's too.
- The loader sets the clock on the one store it builds instead of swapping `build_work_store` in the module (same
  effect, nothing global). `WorkService(store)` is built from it.
- `require_prepare_database`'s refusal text is unchanged: the hand-built baseline pins it.
- `test_e10` in `test_dd4_exports_measured.py` now gives the mini-grid readings: `exports --telemetry` without a
  tenant filter refuses `EMU_FUEL_RECORDS` when a mini-grid Site has no readings (D-DD.168).
- `fuel-records.json` sits at `<out>/<slug>/`; `load_world_inputs` `_LAYOUT` refuses it inside a world tenant folder,
  so DD5b keeps the exports directory apart.
- The basis sentence (R2792-2795) and the month-end-dip assumption go in the packet; D-DD.168's fixed file schema has
  no `conditions` field, and the telemetry manifest's `conditions` is not edited.
- Served floor needs the Foundation revision in force over the whole month (`declared_for`); a Foundation published at
  load time gives none for July (tested). DD6.1 must confirm the world's `valid_from`.
