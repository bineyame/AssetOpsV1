# DD4 handoff (PARTIAL: stopped at the context budget)

Branch `task/DD4-cold-ev-reality`, worktree `/opt/assetecon/AssetOpsV1-dd4`. Spec `specs/DD-demo-data/spec.md` §7 DD4.

## Done
- **DD4.1 cold-thermal 2** (`bc0ff7ac8`). `packs/cold.py`: `MODEL_PROFILE_V2`, `ColdLoadParameters`,
  `DD_LOAD_PARAMETERS` (§4.4 table), `ColdPack(..., load=)`; state `crates`, `efficiency`, field-heat `pulses`;
  forcings `CRATES_IN/OUT` (room-1), `AMBIENT` (ambient-1), `EFFICIENCY` (compressor-1), `GENERATOR_RESET`
  (FAILED -> STOPPED only; raises otherwise). Meter (`compressor-meter/power`, 5-min mean) = cooling x f / cop + aux
  (aux on a powered bus only). Tests `simulator/tests/test_cold_thermal2.py` (8): v1 parity digest (C-DD19 cold part;
  mutation `+1/1000 kW` makes it fail, reverted), exact heat/meter, crates < 0, v1 refuses v2 forcings, reset,
  full room at 400 crates (D-DD.65).
- **DD4.2, ledger part** (`f98c8badb`). `exports_cold._november`: 1-6 Oct generated admissions repeated +31 days,
  new refs, capped at as_of, EMU_CAPACITY re-checked. Test `simulator/tests/world/test_dd4_cold_ledger.py` (2).
  Pin moved: `harvest-cold.profile.cold-storage-ledger.csv` in `books_support.PINNED_COLD_EV` (only that file).

## Counts (simulator, same files)
Branch 87 passed; main 77 passed (difference = the 10 new tests). `tools/check-architecture.ps1` passed.

## Next
1. DD4.2 rest: cold writer. DD3a's `world/telemetry.py` is not on main and is off-limits, so build
   `world/telemetry_cold.py` (per room: one continuous `ColdPack.step` run from the first June movement, day files
   `assetops.world-readings/1`, ambient per day from the `cooling` day weight, `f_m` per month, Thika events, door per
   movement instant) and plug it into `build_telemetry` after DD3a merges.
2. DD4.3: `world/telemetry_ev.py` + widen `exports_ev.roster_rows` callers to 6 Nov with Kasarani spare nights.
3. DD4.4: `world/exports_measured.py`, `body.band` on EV CHARGE rows, `HAND_SAMPLES` empty, C-DD5/6/7/20 live.
4. Packet `packet-DD4.md`, state entry in `.ai/state/index-3.md`, spec Status.

## Open questions for the Architect (defaults taken)
- Q1 C-DD3 FLAT: M has `tariff.usd_per_kwh` (0.15) but not `tariff.prices.usd_per_kwh`. Default: the checker reads
  `tariff.usd_per_kwh` for FLAT (not yet changed in `dd_check.py`).
- Q2 Thika reset timing: the pack's start timeout (Foundation `cold-start-timeout` 5 min) makes the start FAILED at
  19:16, after the spec's reset at 19:14. Default: the writer applies `GENERATOR_RESET` at the later of 19:14 and the
  FAILED minute, stated in `conditions`; C-DD6 judges the failure by the 19:11 START_REQUEST with a FAILED result.
- Q3 C-DD19 in `dd_check`: the checker may not import the simulator (`test_dd1_check` seam). Default: the cold part is
  the simulator parity test; `dd_check` C-DD19 stays a stub until DD3.3 decides how it reads parity digests.
- Q4 Field heat: 40 crates at 24 degC is 2.7 kW for 6 h; several batches admitted the same 08:00 can exceed the 6 kW
  cooling (thermal capacity 1.2 kWh/degC, crates add no mass per the §4.4 table). If the world's ledger stacks them, the
  chamber may pass 60 degC and the pack raises (`TEL_PACK`). Not tuned; to be measured by the writer run.
- Q5 `AMBIENT` and `EFFICIENCY` are new private forcings (the spec gives values per day/month, no mechanism).

## Risks
- `dd_check.py` and `world_history.py` will conflict with DD3a; keep edits additive.
