# DD4a handoff (STOPPED FOR THE OWNER at C-DD6; join pending DD3a)

Branch `task/DD4-cold-ev-reality`, worktree `/opt/assetecon/AssetOpsV1-dd4`. Packet `packet-DD4a.md`.

## Done (D-DD.88 builder order)
1. D-DD.87 grid + rounding ledger (95507fa56). 2. D-DD.83 failure at request, `GENERATOR_HAND_START` (ab38dcd9e).
3. D-DD.85 receiving lots, named lots, pack guard, `EMU_RECEIVING` (b0f... see log) and goldens. 4. `ColdSiteRun`
(`world/telemetry_cold.py`) with D-DD.86 forcings. State entry 205.

## Stop
C-DD6 B-1031: peak 4.049 degC in the outage window, 0 minutes above 5 degC (packet "C-DD6 measurement").
Owner chooses (D-DD.83 default: readings stand).

## Next
- After DD3a merges: the join (D-DD.81): dispatch in `build_telemetry`, frame `TelemetryRefused`, parity
  `test_telemetry_join_parity.py`, then the writer run and C-DD6 again.
- Architect: June/November season for the ambient (packet deviation 5); event row shape (deviation 3).
- DD4b on its own branch after DD4a merges.
