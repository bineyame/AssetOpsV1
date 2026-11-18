# SCN-kobo-reserve-matters review packet: design D2 passes U2; U1 registered

Spec: `AssetOpsV1-plan2/.agent/build-sheet-SCN-kobo-reserve.md` (§2 U1; Addendum 1 design D2 and its five kernel
properties). Branch `task/SCN-kobo-reserve-matters` from main `ca6d7d61b`. Implementer: Claude, 2026-10-31.
Decision `D-2026-10-31-scn-kobo-reserve-matters`. Task `tasks/SCN-kobo-reserve-matters.md` (in_review).

## Outcome

The first design (§2) stopped at U2 property 2: the generator started but delivered 0 kWh (section "First design"
below). The Architect stated D2 in Addendum 1. D2 ran once with its values exactly as stated, and **all five D2
properties pass. H = 04:00-05:00 UTC.** U1 is registered. U3 (the real chain at H) is out of scope here.

## Files

- `config/scenarios/kobo-mini-grid-reserve-matters.yaml` (new). It is a structural copy of reserve-trial with the D2
  values: SOC 34 %, 300 L, STOPPED; `irradiance-1` 30 W/m2 0/240; `irradiance-2` 800 W/m2 240/240; residential
  4 kW, clinic 2 kW, mill 0 kW over 0/480. `display_name` is the sheet's. The `purpose` is restated per the
  Addendum and kept under the parser's 800-character limit: my first wording failed to parse, so I shortened it,
  with no value changes.
- `host/tests/test_scn_reserve_matters.py` (new): the D2 kernel properties, never money.
- `backend/tests/test_scenario_fingerprints.py`: pin `("kobo-mini-grid-reserve-matters", 1)` =
  `50f8be3ec4020e500c85041165a6911fb0d0678d04dda8652cbee46a3a59c956`, add the id to `NEW_SINCE_T025G`, and change
  `test_the_shipped_scenarios_were_found` (`:141-143`) from `== 13` to `== 14`. That last change is the only
  non-additive line and is named in Addendum 1.
- `backend/tests/test_run_binds_scenario_to_site.py`: add the id to `NEVER_SHIPPED_AS_V1`.
- Records: `.ai/DECISIONS.md`, `.ai/CODE_STATE.md` "SCN", `.ai/ACTIVE_CONTEXT.md`, the task file.
- Evidence: `.agent/SCN-evidence/` holds `trajectory-d2-5min.txt` (D2, both runs). It also holds the first design's
  YAML, test and `trajectory-5min.txt`.
- U1 grep: no other list must be complete. Frontend, layout-evidence and contract9 references each use one
  scenario.
- Not touched: prices, SFC, profiles, the template, verification, the cost check and every existing scenario file.

## U2 (D2), one run, mini-grid v5, reserve 30 (template) vs 25

| # | Property | Result |
|---|---|---|
| 1 | Baseline generator > 0 kWh in a whole UTC hour lying before offset 240; H = the first | PASS, H = 04:00-05:00 UTC, 2.95 kWh |
| 2 | Reserve 25: generator energy in H = 0 | PASS, 0 kWh. Requested from 04:50, unloaded |
| 3 | Neither run below its own reserve | PASS. Baseline min 30.00 %, reserve-25 min 25.16 % |
| 4 | Baseline requested after the clearing while PV covers every load | PASS (07:00 onward, unloaded) |
| 5 | Every generator transition >= 20 min from 00:00 UTC | PASS |

pytest `host/tests/test_scn_reserve_matters.py`: 5 passed.

**Instrument correction, flagged for review.** My first D2 run failed property 1 because of my own definition, not
the Addendum's: I had required every 5-minute step of H to be loaded. Under the frozen policy the generator loads in
a sawtooth. At 30 % the battery stops, and for one step the generator carries the load and is requested to charge at -35.8 kW
(2.85 kWh produced); the accepted charge is 30 kW (2.5 kWh in 5 minutes, the PCS limit). The battery then rises above the reserve and serves again. So no hour is loaded in every step. The
Addendum's text is "> 0 kWh in at least one whole hour before offset 240". I corrected the helper to that wording
(an hour's total > 0, with the hour lying wholly before offset 240) and reran once. The design values were not
changed. If the Reviewer reads "whole hour" as "loaded throughout", D2 fails property 1.

The Addendum expected H = 05:00. The run gives H = 04:00 because the baseline first touches 30 % at 04:45-04:50.

## D2 trajectory (UTC, 5-min steps; full rows in `trajectory-d2-5min.txt`)

| Hour | Baseline gen kWh | Reserve-25 gen kWh | Note |
|---|---|---|---|
| 03:00 | 0 | 0 | Baseline STARTING at 03:00 (SOC 34 % <= 35 %), RUNNING from 03:05 |
| 04:00 | 2.95 | 0 | Baseline first loaded 04:45 (0.10 kWh) and 04:50 (2.85 kWh, SOC 30.0 %). Reserve 25 requested at 04:50 (SOC 29.95 %) |
| 05:00 | 3.04 | 0 | Sawtooth at 30 %: loaded steps at 05:25 and 05:30 |
| 06:00 | 6.09 | 0 | Loaded steps at 06:05, 06:10, 06:45 and 06:50 |
| 07:00-10:00 | 0 | 0 | Clearing at 07:00. Both run unloaded, PV charges at the PCS limit |

- Baseline: requested 03:00 to the run end, 480 min including the 5-minute start delay; SOC 84-90 % at 11:00, so
  no stop. Generator energy before the clearing is 12.08 kWh.
- Reserve 25: requested 04:50 to the run end, 370 min, 0 kWh throughout. Its minimum SOC is 25.16 %, at the 07:00 boundary.
- For U3, as information only and not a money claim: in the kernel the trial removes 12.08 kWh of generator energy
  and 110 min of requested runtime. The battery goes deeper (25.16 % vs 30.00 %), which matters for the guardrail
  the Addendum names.

## First design (sheet §2): stopped at U2

The values were exactly as the sheet stated: 37 %, rain 0/150, clearing 150/330. P1 passed (STARTING 03:55, SOC
34.97 %). **P2 failed: 0 kWh in 03:00-04:00 UTC, and 0 kWh in every hour.** P3 passed (reserve-25 min 31.47 %), so
the redesign trigger did not fire, and P4 and P5 passed. The cause is the source order `[pv-array, battery,
generator]` (`config/site-templates/kobo-mini-grid-60kw.yaml:417-419`, `mini_grid.py:704-712`). A running generator
carries load only once the battery reaches its reserve, and charges only while the battery is not discharging
(`:721-730`). The baseline minimum was 31.47 %. The Architect ruled the sheet's premise wrong (Addendum 1).

## Checks

- `pytest backend/tests/test_scenario_fingerprints.py backend/tests/test_run_binds_scenario_to_site.py
  host/tests/test_mini_grid_v5.py host/tests/test_scn_reserve_matters.py` at `aeb53fb86`: **63 passed in 12.37s**.
  That is 58 existing tests plus the 5 U2 tests. Every existing pinned digest matches, and the pinned dict and lists
  only gain entries.
- Before registration, with the tree identical to the base: 58 passed in 11.24s.
- The first design's U2: 1 failed, 4 passed.
- `tools\check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`: **All 11 guards passed** (architecture seams, estate self-tests, navigation, agent workflow, registry, delivery and mock-gap fixtures, missing-claim scan and fixtures, evidence width, screen ledger).
  `frontend/node_modules` is a junction to plan2's, untracked and gitignored. Note that check-all ignores
  `ASSETOPS_GUARD_PYTHON` from the environment, because it sets the variable from its own `-Python` (`:23`, `:55`).
- Not run, per the coordinator: the full suite and `tools/select-tests.py`. U3 is not run.

## Known deviations

1. The instrument correction to property 1, above.
2. H is 04:00, not the expected 05:00.
3. `purpose` is shortened from my first wording to fit the 800-character parser limit (prose only).

## Residual risk and review focus

- Check the property-1 reading: whole-hour total > 0 versus loaded throughout.
- U3 may still fail verification. The runtime target may not be met, and the battery goes deeper, which bears on the
  guardrails. It may also produce a Finding on S or not. The choice rule is fixed: (d) only if it shows the lever,
  has a Finding on S and VERIFIES.
- USER_REVIEW_REQUIRED: false (Lab content, no UI). A fresh independent review gates the merge.

## Fix round (review SCN-review.md)

- M1: merged main `89280952d`; kept both IDX-GAPS and SCN entries in ACTIVE_CONTEXT, CODE_STATE, DECISIONS.
- L1: `purpose` reworded (prose only; 742 characters): the generator loads in short bursts that mostly recharge the
  battery while the battery carries the load in between. Fingerprint re-pinned in `PINNED_SCENARIO_FINGERPRINTS`.
  Old digest `50f8be3ec4020e500c85041165a6911fb0d0678d04dda8652cbee46a3a59c956`;
  new digest `515f0292c3c5046133223ce4aefd21db8a2b752c5f0e40c189116180c935aa0c`.
- L2: property 5 now prepends the starting STOPPED state, so the transition into step 0 is checked.
- L3: `assert hour == 4` pins H = 04:00-05:00 UTC as the recorded U3 window.
- L4: line 47 states the accepted 30 kW (2.5 kWh) charge next to the requested -35.8 kW.

