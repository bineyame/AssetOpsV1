# 0K4a handoff: commits 1 and 2 built (partial; commit 3 waits for 0K4b)

Implementer (Claude), 2026-11-21. Branch `task/0K4a-dispatch-v8`, worktree `/opt/assetecon/AssetOpsV1-0k4a`, base
`main` `b96d5e978`. Status stays `live` until commit 3 and the packet.

## Pre-flight print (for the packet's first section)

On `main` `b96d5e978` plus only `host/tests/trajectory_digest.py`, no product edit:

- v7 8-day Kobo season (`base_run(8)`, default `site_edit=season_site`, `season_inputs(run, 8)`): COMPLETED, 2305
  boundaries, `trajectory_digest` `8eb9c44c38f31a77a8faf6e7e9f90fd2c62112dbe0d01c6a3243b7dae783f280` (N9's literal).
- Day 4 05:00 local (offset 6060, the dawn after the first overcast day): SOC `28243/912` (30.97 %), generator
  RUNNING (D-0K2.17's fault reproduced).
- Measurement addresses: `battery-ac-power@battery-pcs`, `pv-ac-power@pv-inverter`,
  `pv-available-power@pv-inverter`, `generator-output-power@generator`, `battery-charge-requested-power@battery`,
  `battery-discharge-capability@battery-pcs`, `load-requested-power@load-{clinic,mill,res}`,
  `load-served-power@load-{clinic,mill,res}`.

## Done

- Commit 1: §2.1 extraction (`_add_v2_measures`, `_add_v3_measures`, `_add_v4_measures`, `_add_v6_measures`; each
  `resolve_vN` now composes them), §2.2 `CycleSplit` / `cycle_charge_split` (D-0K4.22), `host/tests/
  trajectory_digest.py` (D-0K4.20), `simulator/tests/test_cycle_charge_split.py` (S1-S7, S10, S8 over 540
  combinations, S9 for each argument), `host/tests/test_0k4a_dispatch_v8.py` holding N9 only.
- Commit 2: §2.3 `decide_v8` and `CYCLE_CHARGING_REASON`; `simulator/tests/test_decide_v8.py`.
- Plants (each reverted): P2 fails S4, S10, S8; P3 fails S1; P4 fails S4, S5, S10, S8; P5 fails S5, S8; P12 fails
  S10, S8; P9 as a value swap between the two addresses fails N9; P1 fails the four reorder cases of
  `test_decide_v8.py` (N2 and N3 come in commit 3).

## Next (commit 3, after 0K4b on `main`)

Merge `main` with 0K4b; then §2.4 `_resolve_cycle` / `resolve_v8` / `prepare_v8`, §2.5 the version (simulator,
backend `MODEL_PROFILES`, `EXECUTABLE_MODELS`, `REPLAY_MODELS` with the N11 comment), `host/tests/kobo.py` tuple
entry, §2.7 statements, cases and the `served_text` seam; N1-N8, N10-N13 into `test_0k4a_dispatch_v8.py`,
`backend/tests/test_0k4a_profile_words.py` W1-W2; plants P1 (on N2, N3), P6-P8, P10, P11, P13-P16; regression; N12
literal; packet. Needs from 0K4b: `packs/generator_curve.py` (`fuel_curve`, `output_cap_kw`, `fuel_litres`,
`charge_acceptance_kw`, `CurveRefused`, `CURVE_HANDLERS`, `DIESEL_ENERGY_KWH_PER_L`, `TAPER_FLOOR_SHARE`, the
`NO_LOAD_FUEL_RATE` / `MINIMUM_LOAD` / `TAPER_START` keys), backend `runs/profiles.py:GENERATOR_CURVE_NEEDS`,
`i18n/statements/en/model_profile.py`, `served_text`, and `host/tests/kobo_assumed.py:assumed_site`.

## Risks and notes

- P9 as worded (swap the tuple order of the two v3 measurements) is behaviour-neutral: `_add_v3_measures` sorts
  `interval_energies`, so N9 passes, correctly. The meaningful plant (swap the values between the two addresses)
  fails N9. The packet should record both.
- `decide_v8` with a Site order that puts PV behind the battery (`battery, pv, generator`) gives `generator,
  battery, pv`: only the generator moves (mid-build question 1 in the dispatch report). Kobo's order is not affected
  by the choice.
- `simulator/tests/test_decide_v8.py` is a new file not in §0's list; §4 asks commit 2 for "its own pure test".
