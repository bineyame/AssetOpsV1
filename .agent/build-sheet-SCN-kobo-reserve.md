# Build sheet SCN · a registered Kobo scenario where the reserve change matters, plus the overcast window

Architect: Claude (`.ai/ROLE_CONFIG.md:9`), 2026-10-31. Owner, verbatim (end of
`.agent/owner-client-demo-sequence-2026-10-30.md`): "commission a new scenario and allow the longer overcast window".
Branch `task/SCN-kobo-reserve-matters`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-scn`, from main `ca6d7d61b`.
Evidence: `AssetOpsV1-demo3/.agent/DEMO-SPARSE-trial-probe.md` (P1, P3). This sheet changes no product code.

## 0. Rules

- **Design is allowed; tuning is not.** The scenario's causes (irradiance, demand, starting states) are chosen for
  the demo story and are stated below **before any run**. They must be physically plausible for Kobo and declared in
  the document's `purpose`. Prices, SFC, the Site template, the Foundation, model and publication profiles, the
  verification rules and the cost-check formulas are not touched. The money figure is whatever the simulator plus
  the cost check produce, including 0 or a failed verification.
- **One redesign at most**, the one written in U2, used only on its stated trigger. After that the values are frozen
  and the result is reported as measured.
- Existing scenario files and their pinned fingerprints stay byte-identical. The only change is one added file and
  three list or dict entries.
- Every run of it is a registered Lab run, shown as "Generated test data". Scenario text is Lab vocabulary (exempt),
  but it never names a Site (`test_no_shipped_scenario_names_a_site`).
- PYTHONPATH `<wt>\backend;<wt>\contracts;<wt>\tools;<wt>\simulator;<wt>\gateway;<wt>\host;<wt>\field`. DB names only
  `*_test` or `<prefix>_audit*`. Never pass `-ExecutionPolicy`. No BOM: write `.yaml` and `.py` with the Edit tool or
  `write_text(encoding="utf-8")`. `serve` needs `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` and
  `ASSETOPS_WORK_CURSOR_KEY_HEX`.

## 1. Code reality: why the current scenarios give no saving

- `kobo-mini-grid-reserve-trial` v1: the dawn dip crosses v5's 35 % start, but sunrise at offset 60 (04:00 UTC) gives
  PV surplus beyond the PCS charge limit. **The generator delivers no energy in the whole run**
  (`host/tests/test_mini_grid_v5.py:9`). It is requested but unloaded, so its runtime is avoidable (F-104, 04:35-07:55),
  but no trial hour can change generator energy or fuel. Hence `MODELLED_NO_IMPROVEMENT`, 0 USD, at any hour.
- `kobo-mini-grid-evening` v1: the start is reserve-bound (06:20 `BATTERY_NEAR_RESERVE`), but all of it is
  NECESSARY, so there is no Finding (probe P3 c).
- **The lever, stated physically.** Under v5 the start is at `min(35, reserve + 5)` (`test_mini_grid_v5.py:4`). A
  30 → 25 % reserve trial changes a start only when the state of charge passes **between 35 % and 30 %**, so a
  loaded start in that band is the one the trial removes. The trial hour must hold such a start with generator
  energy > 0 in the baseline. The probe (b) test in DEMO-SPARSE used binding constraints, a narrower proxy; for
  this scenario the lever evidence is the definition here.
- Template facts used (`config/site-templates/kobo-mini-grid-60kw.yaml`): battery 200 kWh (`:88-92`), PCS charge and
  discharge 30 kW, efficiency 95 % (`:112-125`), PV 60 kW (`:65`), start 35 %, stop 90 %, start delay 5 min, generator
  40 kW (`:149-165`). Kobo local time is UTC+3. The interval is 03:00-11:00 UTC (06:00-14:00 local), as v2.
- Registration lists: `backend/tests/test_scenario_fingerprints.py:31` `PINNED_SCENARIO_FINGERPRINTS`, `:176`
  `NEW_SINCE_T025G`; `backend/tests/test_run_binds_scenario_to_site.py:209-217` `NEVER_SHIPPED_AS_V1`.

## 2. Units (3 in this slice plus 1 consumption step). Effort 1.5 builder days

### U1 · The scenario document and its registration · 0.5 d
New `config/scenarios/kobo-mini-grid-reserve-matters.yaml`. It is a structural copy of
`kobo-mini-grid-reserve-trial.yaml` (same `site_contract`, `observation_sources: []`, parameter shapes, roles and
`state_key`s), `scenario_version: 1`, `version_valid_from: '2026-10-01T00:00:00Z'`, no `supersedes`.
- `display_name`: "Kobo mini-grid (rainy dawn, reserve trial)".
- `purpose` (stated design): "A heavily overcast, rainy dawn keeps solar output near zero until it clears at 08:30
  local. Through the dark start the residential and clinic loads (6 kW) draw the battery down from 37 %. With a 30 %
  reserve the state of charge crosses the 35 % start threshold before the sky clears, so the generator starts and
  carries the load and charges the battery; once the sky clears, PV covers every load and the 90 % stop keeps the
  generator requested for most of the morning. With a 25 % reserve the dip ends above the 30 % start, so the battery
  alone carries the dark hours. The runtime follows from the frozen policy and these causes; this document authors no
  generator output. Demonstration values designed for a client demo story, not a recommendation for any real site."
- Values (each with a one-line comment in the file):

| Entry | Offset / duration (min) | Value |
|---|---|---|
| `starting-state-of-charge` | — | 37 % |
| `starting-fuel` / `starting-generator-state` | — | 300 L / STOPPED (as reserve-trial) |
| `irradiance-1` (rain) | 0 / 150 | 30 W/m2 |
| `irradiance-2` (clearing) | 150 / 330 | 800 W/m2 |
| `residential-demand-1` | 0 / 480 | 4 kW |
| `clinic-demand-1` | 0 / 480 | 2 kW |
| `mill-demand-1` | 0 / 480 | 0 kW |

- Expected trajectory (a design note for the review, **not** an assertion target): net drain about 6 − 1.8 kW PV,
  divided by 0.95, gives about 2.2 %/h. The baseline therefore crosses 35 % at about 03:55 and starts at about 04:00,
  loaded. The later run's lowest point is about 31.7 % at 05:30, above its 30 % start, so it never starts. Episodes
  sit inside 04:00-11:00 UTC, at least 20 minutes from midnight.
- Registration: add `("kobo-mini-grid-reserve-matters", 1): "<fingerprint>"` to `PINNED_SCENARIO_FINGERPRINTS` (the
  value is the one `test_every_shipped_scenario_matches_its_pinned_fingerprint` prints; no write flag exists), and
  add the id to `NEW_SINCE_T025G` and `NEVER_SHIPPED_AS_V1` with the comment `# SCN-kobo-reserve-matters`.
  `git diff` on those two tests shows additions only.
- Grep `kobo-mini-grid-reserve-trial` for any other list that enumerates shipped scenarios (Lab picker tests,
  scenario-count asserts). Add the new id only where a list must be complete, and name each in the packet.

### U2 · Kernel design check (in process, no DB) · 0.5 d
New `host/tests/test_scn_reserve_matters.py`, using the `test_mini_grid_v5.py` pattern (`kobo_draft`, `model_for`,
`run_to_end`, START/END `:26-27`), mini-grid v5. Run once on the template Foundation (reserve 30) and once with
reserve 25. Assert the **design properties** only, never money:
1. Baseline: the generator starts (`generator-state@generator` on) at a step where SOC ∈ (30, 35] %, before offset 150.
2. Baseline: generator energy > 0 in the hour holding that start (rounded down to the whole hour; expected
   04:00-05:00 UTC).
3. Reserve 25: no generator start in the whole run; minimum SOC > 30 % and > the 25 % reserve.
4. Baseline: generator still requested at offset ≥ 180 while PV covers every load (the unloaded, avoidable morning).
5. Every generator transition lies ≥ 20 min from 00:00 UTC.

- **Single redesign (stated now).** Trigger: property 3 fails, i.e. the reserve-25 run reaches 30 % before the sky
  clears. Change: the clearing moves 30 min earlier (`irradiance-1` duration 120, `irradiance-2` offset 120,
  duration 360). Nothing else changes. Any other failure, or a failure after the redesign: stop, record the trajectory
  in the packet, and do not ship the scenario. The owner is told that the honest result is no such Kobo run.
- Record in the packet: start time, SOC at start, generator kWh per hour, the reserve-25 minimum SOC, and the
  morning runtime.

### U3 · Probe on the real chain and record (in `-demo3` after this branch merges) · 0.5 d
- After SCN merges to main and main is merged into `task/DEMO-A-combined-dataset`, run DEMO-SPARSE's P3 as
  **candidate (d)**: the trial pair on scratch S/S+1 with `M["scenario"] = kobo-mini-grid-reserve-matters v1`. The
  window is the U2 property-2 hour (one candidate, fixed by U2, not searched). Use a DB `assetops_demo3_probe4_test`.
- Record the same columns as P3 in `.agent/DEMO-SPARSE-trial-probe.md`: lever evidence (start time, SOC at start,
  generator kWh in the hour), Finding on S (id, episode), verification outcome, cost-check state, nominal and upper
  USD, plus the binding constraints for information.
- **Choice rule (fixed now, savings not an input):** use (d) if it shows the lever, has a Finding on S and VERIFIES.
  Otherwise keep (a), shown as "no modelled improvement". A guardrail failure or INCONCLUSIVE is recorded and keeps
  (a). There is no further scenario work.

### Consumption · DEMO-SPARSE day-list values that change after U3 (0.25 d, DEMO-SPARSE builder)
In `backend/conversions/demo-story-days-v1.json`:
- `trial.scenario_id`: `"kobo-mini-grid-reserve-matters"` (only if U3 chose d); `trial.window_hour`: the U2 hour
  (expected `"04:00"`); `trial.probe_ref` keeps the probe file, row (d).
- `kinds.kobo.trial-before` / `trial-after` read `trial.scenario_id` (`demo_combined_kobo.resolved_manifest`, `:29-42`,
  sets `M["scenario"]`). `overuse` stays `kobo-mini-grid-reserve-trial` (S−14, S−7: a Finding with an unloaded
  generator, a different weather day).
- `kinds.kobo.overcast` (owner item 2): `scenario_id: "kobo-daytime-overcast"`, `scenario_version: 2`,
  `start: "D+0d 03:00"`, **`end: "D+0d 15:00"`** (720 min, the interval its own header declares,
  `kobo-daytime-overcast.yaml:4-5`), `received_at: "D+0d 16:00"`. The model and publication profiles stay the v2
  manifest's (mini-grid v5, publication v4), so the dispatch assessment applies as on other days. This is a day-list
  change only; the scenario file is untouched.
  - DEMO-SPARSE U1 P1 re-runs this one row. If it is READY and gives generator time with no Finding, it is taken.
    Otherwise overcast keeps the already-taken `kobo-s3-dispatch-necessary-run` (no further fallback), recorded.
  - A 12-hour day runs to 15:00 UTC, so it still holds episodes ≥ 20 min from midnight. `DAY_NOT_IN_PAST` checks
    against 16:00.
- DEMO-SPARSE `EXPECTED_SECONDS["kobo"]` adds about 40 s for the longer overcast run.

## 3. Validation tier

- U1/U2: `backend/tests/test_scenario_fingerprints.py backend/tests/test_run_binds_scenario_to_site.py
  host/tests/test_mini_grid_v5.py host/tests/test_scn_reserve_matters.py` plus any list test found by the U1 grep.
  `tools\check-all.ps1` at each commit.
- Merge gate: `python tools/select-tests.py --base main`. If it selects the whole suite (a `config/` change may),
  run one `tools\run-backend-suite-in-container.ps1 -Tier all` on an idle machine; otherwise run the selected set.
  U3 runs under DEMO-SPARSE's tier.

## 4. Acceptance

1. The new file is registered; every existing scenario fingerprint is unchanged (pinned test green, diff
   additions-only).
2. U2's five properties hold on the stated design, or on the stated redesign, recorded. Otherwise the slice stops
   and reports.
3. U3 row (d) is recorded with every column, whatever it shows. The choice follows the fixed rule.
4. No price, SFC, profile, template, verification or cost-check change in the diff (reviewer checks
   `git diff --stat`: `config/scenarios/` one new file, two test lists, one new test).

## 5. Register and decisions

- No mock-departure row: Lab content only. If U3 keeps (a), R617 is added in DEMO-SPARSE ("trial hour and scenario
  kept; measured 0").
- Decision log: append `D-2026-10-31-scn-kobo-reserve-matters` to `.ai/DECISIONS.md` (the owner quote, the lever
  definition, the one-redesign rule, the fixed choice rule).
- Owner decisions: none new. If the honest result is still 0 or not verified, that is shown as is (owner
  recommendation 3).

## Addendum 1 · after the U2 stop (Architect: Claude, 2026-10-31)

**The stop was correct.** Under the frozen policy as it really behaves (`mini_grid.py:704-730`: source order pv,
battery, generator; a running generator carries load only once the battery is at its reserve), the SCN U2 design gave
a start with no energy. That was my error in §1: I assumed a start means a loaded generator.

**Can the baseline carry load while the reserve-25 run never starts? No.** Before the baseline generator carries load,
both runs have identical causes and identical state-of-charge paths. The baseline carries load only from 30 %
(its reserve), and 30 % is exactly the reserve-25 run's own start (min(35, 25 + 5)). So the reserve-25 run always
starts too. "Never starts" and "baseline carries load" cannot both hold; no starting SOC or rain length changes that.

**What the reserve change does change, honestly: fuel, not starts.** From 30 % the baseline generator carries the
load. In the reserve-25 run the generator is requested at 30 % but stays unloaded while the battery serves load down
to 25 %. Over that span, generator energy differs.

**Design D2 (stated before running; one run; stop on failure; no further designs).** It reuses the U1 file
(`kobo-mini-grid-reserve-matters` v1, unregistered so far) with these values changed:
- `starting-state-of-charge` 34 %;
- `irradiance-1` (rain) offset 0, duration 240, 30 W/m2;
- `irradiance-2` offset 240, duration 240, 800 W/m2 (clears at 10:00 local: a heavy rainy-season morning);
- loads unchanged (residential 4 kW, clinic 2 kW, mill 0);
- `purpose` restated: the generator is requested early in both runs; with a 30 % reserve it carries the load from
  30 %, and with 25 % the battery carries it down to 25 %; the trial changes generator energy, not starts.

Expected (a design note, not an assertion target): about 2.2 %/h net drain. The baseline is at 30 % at about 04:50 and
carries load until the clearing at 07:00. The reserve-25 run reaches 25 % at about 07:05, so its generator stays
unloaded until the clearing.

Kernel properties (they replace §2 U2 1-5 for D2):
1. Baseline: the generator delivers > 0 kWh in at least one whole hour before offset 240. H = the first such hour
   (expected 05:00-06:00 UTC).
2. Reserve 25: generator energy in H is 0 kWh. Its start is allowed and recorded.
3. Neither run goes below its own reserve. Record both minimum SOCs.
4. Baseline: the generator is still requested after the clearing while PV covers every load (the avoidable morning,
   a Finding).
5. Every generator transition lies ≥ 20 min from 00:00 UTC.

On any failure: stop, record the trajectory, nothing ships, and the demo keeps the honest 0 ((a)). On a pass,
U1 registration also changes `test_scenario_fingerprints.py:141-143` `len(documents) == 13` to `== 14` (name it in
the packet). U3 then runs at H with the unchanged choice rule. The verification may still fail its target (runtime
is not reduced) or its guardrails (the battery goes deeper); whatever it shows is recorded, and (a) stays unless (d)
VERIFIES.

**Overcast (Q2): no new scenario.** A new `kobo-daytime-overcast` version would replace a shipped file, and so change
an existing digest; that is refused. A new overcast id is not worth it, because `kobo-s3-dispatch-necessary-run`
already is the weather-explained beat (its own text: an overcast morning; generator needed throughout, 455 min, no
Finding). S−21 stays on necessary-run, and the longer-window day-list change is withdrawn. Inform the owner: their
"allow the longer overcast window" was applied and cleared the interval refusal, but the scenario lacks the mini-grid
v5 initial states, and the beat is kept honestly with necessary-run.

**Clarification of D2 check 1 (Architect, 2026-10-31).** The intended meaning was (a): a whole clock hour that lies
wholly before offset 240 and whose total generator energy is > 0 kWh. "kWh in an hour" is a total, and "whole hour"
fixes the window, not a loaded-at-every-step condition. The words came before any run, so the implementer's rerun
is the test as written, not a retune. H = 04:00-05:00 UTC (2.95 kWh at baseline, 0 at reserve 25) stands, and U3
proceeds with the unchanged choice rule.
