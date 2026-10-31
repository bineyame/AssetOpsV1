# SCN-kobo-reserve-matters packet: STOPPED at U2 (property 2 failed, not the redesign trigger)

Spec: `AssetOpsV1-plan2/.agent/build-sheet-SCN-kobo-reserve.md` (U1, U2). Branch `task/SCN-kobo-reserve-matters`
from main `ca6d7d61b`. Implementer: Claude, 2026-10-31.

## Outcome

The scenario was written with every value exactly as the sheet states (37 %, 300 L, STOPPED, 30 W/m2 0/150,
800 W/m2 150/330, 4 / 2 / 0 kW over 0/480) and the U2 design check was run once, on mini-grid v5, reserve 30 and
reserve 25. **Property 2 fails: the baseline generator delivers 0 kWh in the start hour, and 0 kWh in every hour of
the run.** Property 3 (the redesign trigger) holds, so the one permitted redesign does not apply. Per the sheet
("any other failure: stop, record the trajectory, do not ship the scenario") the scenario is **not shipped**:
no file under `config/scenarios/`, no registration entry, no new test under `host/tests/`. The honest result is
that no such Kobo run exists with these causes. Tracked-file diff against main: empty.

The scenario document and the U2 test as run are kept as evidence only, in `.agent/SCN-evidence/`
(`kobo-mini-grid-reserve-matters.yaml`, `test_scn_reserve_matters.py`, `trajectory-5min.txt`). To reproduce: copy
the YAML to `config/scenarios/` and the test to `host/tests/`, then run the test.

## U2 result (one run, design as stated)

| # | Property | Result |
|---|---|---|
| 1 | Baseline start at SOC in (30, 35] %, before offset 150 | PASS: offset 55 (03:55 UTC), SOC 34.97 % |
| 2 | Baseline generator energy > 0 in the start hour | **FAIL**: `generator energy 0.0 kWh in 03:00-04:00 UTC` |
| 3 | Reserve 25: no start; min SOC > 30 % and > 25 % | PASS: never starts, min 31.47 % |
| 4 | Baseline requested at offset >= 180 while PV covers every load | PASS (unloaded, PV to load = demand) |
| 5 | Every generator transition >= 20 min from 00:00 UTC | PASS |

pytest: `1 failed, 4 passed in 2.60s`.

**The hour U2 identifies:** the start step is 03:55 UTC (STARTING; RUNNING from 04:00), so the property-2 hour,
rounded down, is **03:00-04:00 UTC**, not the sheet's expected 04:00. Generator energy is 0 in that hour and in
04:00-05:00 alike, so the choice of hour does not change the result.

## Trajectory (baseline reserve 30 / later reserve 25, 5-min steps; full rows in `trajectory-5min.txt`)

| UTC | Offset | SOC base % | Gen base | Battery req base kW | Gen kWh (step) | SOC r25 % | Gen r25 |
|---|---|---|---|---|---|---|---|
| 03:00 | 0 | 37.00 | STOPPED | +4.2 | 0 | 37.00 | STOPPED |
| 03:50 | 50 | 35.16 | STOPPED | +4.2 | 0 | 35.16 | STOPPED |
| 03:55 | 55 | 34.97 | STARTING | +4.2 | 0 | 34.97 | STOPPED |
| 04:00 | 60 | 34.79 | RUNNING | +4.2 | 0 | 34.79 | STOPPED |
| 05:00 | 120 | 32.58 | RUNNING | +4.2 | 0 | 32.58 | STOPPED |
| 05:30 | 150 | 31.47 (min) | RUNNING | -82.0 | 0 | 31.47 (min) | STOPPED |
| 06:00 | 180 | 38.60 | RUNNING | -82.0 | 0 | 38.60 | STOPPED |
| 09:35 | 395 | 89.66 | RUNNING | -82.0 | 0 | 89.66 | STOPPED |
| 09:40 | 400 | 90.85 | STOPPED | -42.0 | 0 | 90.85 | STOPPED |

- Generator kWh per hour, baseline, 03:00 to 10:00 UTC: 0, 0, 0, 0, 0, 0, 0, 0.
- Reserve-25 minimum SOC: 31.47 % at offset 150 (05:30 UTC).
- Baseline runtime: 03:55-09:40 UTC (345 min including the 5-min start delay), all unloaded; morning runtime after
  the clearing (offset >= 150): 250 min. The SOC trajectory is identical in both runs (as in reserve-trial v1).

## Why (code reality, not a redesign)

- Source priority is `[pv-array, battery, generator]` (`config/site-templates/kobo-mini-grid-60kw.yaml:417-419`) and
  the mini-grid dispatch serves load in that order (`simulator/assetops_simulator/packs/mini_grid.py`, the
  `supply` / `gen.order` loop at `:704-712`). While RUNNING, v5 still requests +4.2 kW from the battery, and the
  battery serves it while above the reserve in effect, so the generator takes no load. Charging from the generator
  happens only while the battery is not discharging (`:721-730`), so it does not charge the battery either.
- So the sheet's lever ("a start in the 35-30 % band") is necessary but not sufficient: generator energy needs the
  baseline SOC to reach the 30 % reserve itself, and this design's baseline minimum is 31.47 %. The purpose text's
  "the generator starts and carries the load and charges the battery" does not follow from the frozen policy.
- The stated redesign (clearing 30 min earlier) cannot repair this: it only raises the minimum SOC. It was not run
  (its trigger, property 3 failing, did not occur).

## U1 registration survey (for a future attempt)

`grep kobo-mini-grid-reserve-trial` finds the complete lists only in `backend/tests/test_scenario_fingerprints.py`
(`PINNED_SCENARIO_FINGERPRINTS`, `NEW_SINCE_T025G`) and `backend/tests/test_run_binds_scenario_to_site.py`
(`NEVER_SHIPPED_AS_V1`). Not named by the sheet: `test_the_shipped_scenarios_were_found`
(`test_scenario_fingerprints.py:141-143`) asserts `len(documents) == 13`; registering a scenario must change it to
14, a one-token modification, so "diff additions only" cannot hold literally. No other list enumerates shipped
scenarios (frontend, layout-evidence and contract9 references are single-scenario usages).

## Checks (tree identical to main)

- `pytest backend/tests/test_scenario_fingerprints.py backend/tests/test_run_binds_scenario_to_site.py
  host/tests/test_mini_grid_v5.py`: 58 passed in 11.24s (existing digests untouched; nothing added).
- U2 test (with the scenario temporarily in place): 1 failed, 4 passed.
- `tools\check-all.ps1 -Python <plan2 venv python>`: 9 of 11 PASS (architecture seams, estate self-tests,
  navigation, agent workflow, registry, delivery and mock-gap fixtures, evidence width, screen ledger). 2 FAIL,
  environment only: missing-claim orphan scan and its fixtures, `MODULE_NOT_FOUND` for `typescript`
  (`tools/checks/missing-claim-scan.mjs:19-20` requires it from `frontend/node_modules`, absent in this worktree).
  The tracked tree is identical to the base. Note `check-all.ps1` ignores
  `ASSETOPS_GUARD_PYTHON` from the environment (it sets it from its own `-Python` parameter, `:23`, `:55`); it must
  be run with `-Python <plan2 venv python>`.

## Known deviations / not done

- Not shipped, by rule: no task file, no decision entry, no CODE_STATE / ACTIVE_CONTEXT update; these wait for the
  coordinator, since the slice's deliverable does not exist.
- U3 and the consumption step cannot proceed for (d); per the sheet's choice rule the demo keeps (a).

USER_REVIEW: the owner should be told the honest result (no such Kobo run under the frozen v5 dispatch with the
stated causes); any new attempt is an Architect design change, not a tuning round.
