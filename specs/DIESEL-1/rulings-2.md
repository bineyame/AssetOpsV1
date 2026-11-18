## 8. Ruling DIESEL-1-R2: Kisiwa re-planned around unexplained fuel (supersedes §1, §3–§6 for D1–D5)

- Architect: Claude (fresh Architect), 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `2ca92124a` (MV-1, A1 and D0 merged; CH-5d1 in build).
- Owner decisions now in force, verbatim:
  - `.agent/owner-missing-fuel-2026-11-07.md`: "Before the demo, both"; if the 60 % trial misses, "Kisiwa with missing fuel"; "'Unexplained fuel', never 'theft'" (the "Label the 'after' nights" option was **not** selected); client diesel-heavy or raised missing fuel: "Not specifically".
  - `.agent/owner-scenario-data-2026-11-07.md`: "dont be limited by existing data, data that is reasonable and can reflect a situation can be legitmately added via a scneario for days that are not covered today", and the correction "this is not true, these are injected through operational actions" (§8.2a).
  - Still in force: the night window "6 pm to noon" (`owner-diesel-night-window-2026-11-07.md`), the generic no-load rate rule (`owner-fuel-scope-2026-11-07.md`), no combined savings total, no annualising.
- **§2 (D0) stays as history.** D1–D5 in §1, §3–§6 are **withdrawn**. They are replaced by F0 and K1–K9 below. The design basis is `.agent/fuel-loss-feasibility-2026-11-07.md` Part B; this ruling supersedes it where they differ.
- Paths as in the header: `B/`, `F/`, `T/`, `C/`, `V/`, `S/` = `simulator/assetops_simulator/`.

### 8.1 Disposition of D0

1. **The 4.4 % result is dropped from the demo.** It appears on no screen, in no finish row and in no DS-1 line, not even as "the setting change saved only about 4 %".
   - Reason: a demo claim must come from the product's own evidence path. The 4.4 % came from an agent's in-memory probe; no product code computes it (D2 is withdrawn). Showing it would mean quoting a number the product cannot show.
   - Reason: the owner ruled that the 60 % story "does not go in as a success". A failure beat would need the full night-fuel family (1.75) to be honest, and it would teach the client nothing they need.
   - It stays in `.agent/DIESEL-D0-probe-results.md` as the record. If the client asks, the presenter may say, unscripted and without a figure: "we tested a generator setting on this example site, it didn't meet the bar we set in advance, so we didn't show it."
2. **Kisiwa keeps D0's physics unchanged**, including the stop setting at **90 % throughout** (no setting change in the story) and cycle charging. The template D1 promotes is D0's draft, verbatim in the `foundation` block. D0 is **never re-run with changed assumptions.**
3. **G4 window merge: confirmed.** In the G4 comparison document only, `T/probe_kisiwa_nights.py:192-203` joins adjacent windows whose level is identical. The level at every minute is unchanged. The measured day-runs use the unjoined per-day document. The chained runs and the continuous run matched exactly across *different* window partitions, so the merge makes G4 a stricter check, not a weaker one: equality would have failed if event boundaries alone changed the physics. Conditions:
   - every measured or product run (F0, K7) uses the unjoined per-day document;
   - any later multi-day document joins only identical levels and records the node count;
   - no window is ever split or joined in a way that changes a level.
4. **Kisiwa's dispatch Findings stay.** The product's dispatch analytic will mark Candidate avoidable running on Kisiwa's nights (D0's indicative figure was 190 minutes a night). That is real product output from Kisiwa's readings, priced by fuel-cost-2. It is neither suppressed nor acted on. DS-1 does not narrate it. KIS-2 checks it.
5. **A rainy-season stretch is not proposed.** The new owner guidance allows one, but the unexplained-fuel story does not need it. Kisiwa already burns about 43 L a night. More diesel only widens the expected-use margin (±10 % of use), which makes a removal *harder* to see. No owner question.

### 8.2 Honest presentation of the "after" nights (no special label)

**Ruling: the general example-data labelling is enough, under the conditions below.** The owner did not choose a special label and has since said that reasonable authored days are legitimate. The removal (with the sensor unplugged), the delivery and the dips are authored operational actions (§8.2a), and the clean after-nights are authored days with no removal. Like every Kisiwa day, they are example data and labelled as such through the existing example-data labelling. Honesty then rests on what the product *claims*, which these rules pin:
- **H1. The verdict claims only what the check measures.** VERIFIED says the fuel stayed accounted for within the margin and the sensor reported all night. It never says the seal "stopped", "prevented" or "saved" anything. One fixed line on the verdict page: "This check shows the fuel stayed accounted for after the change; it does not measure how much the change itself prevented." (§8.4 K6).
- **H2. No money on the verification.** No "recovered" or "saved" value is computed for this Action. The Assure card counts it as a verified result with no value line.
- **H3. The Finding's money is a band from evidence.** Litres [low, high] × the declared price, with its own basis, never added to any other money.
- **H4. Wording.** Client copy and DS-1 say "unexplained fuel". They never say "theft", "stolen", "stole", "siphon" or "pilfer", and never imply any of them. A guard enforces this (K9). The two existing "theft" strings in `F/sites/MiniPerformance.tsx:1311` and `:1343` are reworded (K5).
- **H5. Inputs are declared before F0 runs** (§8.3) and never chosen to reach a result.

### 8.2a Owner correction: fuel events enter through operational actions

Owner, verbatim (`.agent/owner-scenario-data-2026-11-07.md`), correcting the coordinator's "where the simulator can't produce something (for example, a removal), an authored scenario input is acceptable": **"this is not true, these are injected through operational actions"**.
- **Binding rule (OA-1).** The fuel removal, the delivery, the hand dips, the tank seal and the sensor power fix are operational actions. None is written into a scenario as a direct state change (`CAUSAL_INPUT` on the tank) or as a reading (`REPORTED_OBSERVATION`). The scenario keeps only the world's own conditions: weather and loads, as in D0.

**What exists today (code reality at `2ca92124a`):**

| # | Mechanism | Where | What it can and cannot do |
|---|---|---|---|
| M1 | Scenario timeline entry kind `INTERVENTION` | `B/scenarios/models.py:93`, `:203-212` | An operator's act, as a `CAUSAL_INPUT` (moves world state) or a `REPORTED_OBSERVATION`. Run setup executes an INTERVENTION cause exactly like an EVENT cause. It is still scenario-authored, so **OA-1 rules it out** |
| M2 | `OPERATOR_RECORD` observation source | `B/scenarios/models.py:274-279`; used by `C/scenarios/fuel-loss-event.yaml:388-450` | A person's written value, Lab-only. **No run, publication or gateway path reads it** (no reader in `B/runs/service.py` or `host/execution_adapter.py`). It never reaches the product |
| M3 | Operator override commands | scenario CONTROL windows declared operator-issued: `B/runs/service.py:2151-2190`, `:3743-3746`; `B/scenarios/models.py:256` `OPERATOR_COMMANDABLE_STATES`; frozen as `OverrideCommand` (`contracts/assetops_contracts/operational_records.py:72-98`); published by `S/observation/records.py:39-120` as `OPERATIONAL_RECORD` envelopes, `record_kind` `OVERRIDE_COMMAND` (`contracts/assetops_contracts/source_envelope.py:126`, `:855-860`) | The only operational action that reaches the product through ingestion today. **CONTROL states only** (generator and battery policy); it cannot address the tank stock. Also scenario-authored |
| M4 | Run-scoped interventions | designed in `.ai/ARCHITECTURE.md:204-214`, `:228` | **Not built.** `intervention_history` is always empty (`B/runs/service.py:719`, `:1376`; `B/runs/models.py:900-918`). Nothing turns an operational action into a world change |
| M5 | Human operational records on the site-first path | `B/work/service.py:36-38` (`OPERATIONAL_KINDS = OPERATOR_LOG, MANUAL_READING, SHIFT_NOTE, SITE_VISIT`), `:470-520` `post_operational_record` (quantity and unit, source document hash, correction chain, idempotency) | **The real operations path for records.** It has no `FUEL_DELIVERY` or `TANK_DIP` kind and no tank link. The technical design names exactly this gap: `frontend/docs/architecture/production-shaped-mvp-technical-design.md:200` ("typed kind (such as fuel delivery) … Define approved record kinds … before FuelBalanceWindow") |
| M6 | W1 Actions and Foundation revisions | `B/actions/` | The lever path: an Action raised from a Finding thread, with an effective instant. Exists |
| M7 | The kernel's declared causes | `contracts/assetops_contracts/world_inputs.py:170-205` `DeclaredCause`; `S/kernel/execute.py:915-940` | Applies INCREASE/DECREASE to any `CAUSAL_INPUT` stock from the frozen world inputs, whatever their origin. This is the hook a run-scoped intervention would use |

**Conclusion: the mechanism is missing on the site-first path.** Records can enter the product the real way (M5, after two new kinds and a tank link). But **no operational action can change the simulated world** without being written into the scenario (M1, M3), and the designed path for that (M4) does not exist.

**Design under OA-1 (Option A, recommended): an operational-action bridge for the tank (new unit K0).**
- **One source per Site:** a versioned, Lab-private operational-action log, `C/operational-actions/kisiwa-001-v1.yaml`. Each action has `action_id`, `at`, `actor` and `kind`. Its effects are derived from the action, never authored separately:

| Action kind | Physical effect on the simulated world (frozen at run setup as a run-scoped intervention, M4, applied through M7) | Product record (through M5's API, the real operations path) |
|---|---|---|
| `FUEL_DELIVERY` | INCREASE on `fuel-tank-volume@fuel-tank` by the delivered volume, at `at` | `FUEL_DELIVERY` operational record: the ticket volume and reference, recorded by the operator 30 min later |
| `FUEL_REMOVAL_UNRECORDED` | DECREASE over its window; plus, when `sensor_disconnected` is given, the tank sensor's reporting path is unavailable over that span (the person unplugs it) | **none**: nobody records it, as in reality |
| `TANK_DIP` | none (a person reads the tank) | `TANK_DIP` operational record. The value is read from the run's tank stock at `at`, rounded half-even to 1 L, by the loader after the run. Never typed |
| `TANK_SEALED`, `SENSOR_POWER_PROTECTED` | none in v1 (no later removal is authored) | Work `SITE_VISIT` record "Tank cap sealed; tank sensor moved to its own protected supply", linked to the W1 Action (M6), which carries the effective instant |

- **Run setup** (`B/runs/service.py`) reads the log for the run's Site and interval and validates each action, with typed refusals: the component exists; the stock is a `CAUSAL_INPUT` stock in the model; the unit is L; a delivery fits free capacity at `at` (else refused, never clamped); the removal does not exceed the stock. It then freezes the physical effects as `DeclaredCause`s (and the reporting-path span as a reporting condition). Each one carries origin `OPERATIONAL_ACTION` and the action's content hash, listed in `deterministic_identity.intervention_history`.
- **Runs with no actions are byte-equal** (empty history, as today). That is a stop condition for K0.
- **The product never reads the log.** Analytics read only the M5 records and accepted readings, so the Lab-private removal stays private truth.

**Option B (cheaper, not OA-1-faithful): M1 from the same log.** The loader turns each physical effect into a scenario `INTERVENTION` entry, and the records go through M5 as in Option A. That is about +0.25 instead of K0's 2.0. It still writes the change into the scenario, which the owner's correction rejects, so it is offered only as an owner choice (§8.10 Q1).

**Sizes:**
- **K0 operational-action bridge: 2.0** (range 1.5–3.0): contract origin and history 0.5; run setup read, validation, freeze and parse 0.75; host and kernel application plus the reporting-path span 0.5; tests (byte-equal for runs with no actions, refusals, L2 setup) 0.25.
- **K2 becomes M5's extension** (same 0.75, §8.4).
- **K7 +0.25** for the action-log injector.
- **Net +2.25** over §8.4's figure.

### 8.3 F0: the Kisiwa fuel-events probe (full ruling, ready for a builder now), 0.5

**Purpose.** In memory, with no DB, no product code and no suite, answer six questions. **Question 0 is the operational-action path (§8.2a) and comes first:**
0. **The bridge hook.** On a Kisiwa run built by normal run setup from a weather-and-loads-only scenario, can the frozen world inputs carry extra `DeclaredCause`s **that no scenario entry produced**, and does the kernel apply them (M7) without a provenance refusal? Can a reporting-path span be added to the run's reporting inputs the same way? The probe adds them with `dataclasses.replace` on the frozen run, standing in for K0's run setup. **No scenario `CAUSAL_INPUT`, `INTERVENTION` or `REPORTED_OBSERVATION` entry is written (OA-1).** Also confirm, by code reading with file:line, that M2 and M3 cannot carry a tank action or a dip into the product, and that `intervention_history` has no reader that would refuse a non-empty value. The answer sizes K0.
1. Does `mini-grid` v6 apply the delivery (INCREASE, POINT) and the removal (DECREASE, WINDOW) on `fuel-tank-volume@fuel-tank` through that hook?
2. Does the removal's sensor-disconnected span silence `fuel-level-sensor/fuel-level`?
3. Is dispatch unaffected?
4. Does the declared `fuel-balance-1` band (below) flag the removal night and no other night, both from the true tank and from the published readings?
5. Does the registered publication path publish Kisiwa's tank level, and why does Kobo store 0 `fuel_level` rows (`.agent/build-sheet-DD-1.md:1934`)?

**Code reality the builder starts from:**
- The mini-grid tank stock is a `CAUSAL_INPUT` STOCK handler with `consume=daytime._apply_to_stock` and floor 0 (`S/packs/mini_grid.py:192-207`). Its statement says "moved only by accepted generator energy". Only the minimal fuel model has exercised authored INCREASE/DECREASE (`S/packs/fuel.py:93-101`; `C/scenarios/fuel-loss-event.yaml:329-357`, `:452-478`). For mini-grid this is unverified, hence F0.
- `registered-kobo-publication` v1–v5 inherit Lab v3's `fuel-level-sensor/fuel-level` (15 min, bias −0.5 L, dropout 40/1000) and the `fuel-level-reporting-availability` forcing state (`B/runs/profiles.py:1426-1470`, `:1843-1860`, `:1873-1890`, `:1911-1945`, `:1985-2000`, `:2052-2058`). Kobo still stores 0 tank rows. F0 finds the stage that drops them.
- In-memory publication: `host/execution_adapter.py:679` `reporting_inputs(run)`, then `S/observation/transform.py:224` `generate_observations(trajectory.boundaries, reporting)` (as `host/tests/test_generator_observation.py:466-469`). The gateway `publish(observations, mapping_set, …)` is `S/gateway/publish.py`. `SIMULATOR_LAB_DISPATCH_MAPPINGS` includes the fuel-level entry (`S/gateway/mappings.py:105-108`).

**Declared world (fixed now, before any run; never tuned).** Everything in §2.2 is unchanged except the start fuel and the operational actions:

| Item | Value | Basis |
|---|---|---|
| Runs | **10** day-runs, 15:00–15:00 local (§2.3 shape), run 1 at `2026-10-01T12:00:00Z`, chained at full precision, stop 90 % throughout | D0's run shape |
| Start fuel, run 1 | **700 L** of 1000 | A site between deliveries, so a delivery fits below capacity (the Lab's capped-delivery false positive is excluded). Not outcome-dependent: dispatch is never fuel-limited |
| Operational action `FUEL_DELIVERY` | **300 L**, **10:00 local on the morning that closes night 2** (run 2, offset 1140 min), actor "Fuel supplier". Ticket 300 L | The Lab scenario's figure, reused (`fuel-loss-event.yaml:466-474`) |
| Operational action `FUEL_REMOVAL_UNRECORDED` | **120 L** over **45 min, 01:00–01:45 local in night 4** (run 4, offset 600 min), actor "Unidentified", with `sensor_disconnected` **00:50–02:20 local** (run 4, offset 590 min, 90 min) | The Lab scenario's figure, duration, 10-min lead and 90-min span, reused (`:329-386`). Under OA-1 the gap is the same person's act (unplugging the sensor), not a scenario forcing |
| Operational action `TANK_DIP` | night 4 morning round **07:00 local**; after the change, **06:00 and 18:00 local** every day in runs 6–10; actor "Shift operator". Value = the tank stock at that instant, rounded half-even to **1 L** (dipstick reading) | Read from the trajectory, never typed |
| Operational actions `TANK_SEALED`, `SENSOR_POWER_PROTECTED` | at the change instant (below); no physical effect in v1 | Recorded only (§8.2a) |
| Where the actions live in F0 | `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml`, in K0's log format (K0 promotes it verbatim to `C/operational-actions/kisiwa-001-v1.yaml`) | One source for effects and records |
| Change instant (for partitioning only) | 15:00 local at the start of **run 6**. Before = nights 1–5 (night 4 = incident); after = nights 6–10 | Action is agreed the day after the Finding and done the next afternoon (K7) |

**`fuel-balance-1` parameters (declared now; K3 implements exactly these; any change is a new parameter version, never a retune):**
- Window = night k, 18:00 local to 12:00 local next day (owner window).
- **Opening** = the last accepted `fuel_level` reading in `[start − 30 min, start]`. **Closing** = the first in `[end, end + 30 min]`. If either is missing, the window is `NOT_ASSESSED` (limitation `MISSING_OPENING` / `MISSING_CLOSING`).
- **Tank margin** = 2 × a, where a = the Foundation `fuel-level-sensor-accuracy` = **10 L**, basis `GENERIC_DEFAULT` (1 % of a 1000 L tank, a common level-sensor class). Applied to opening and closing, combined linearly.
- **Deliveries** D = Σ ticket volumes of `FUEL_DELIVERY` records with instant in `[start, end)`. Tolerance = Σ 1/100 × ticket.
- **Use**, from the generator readings per 5-minute slot: loaded = Σ kWh × SFC (as known); idle hours = RUNNING slots at 0 kWh (A2's slot rule). `use_low = 9/10 × loaded`; `use_high = 11/10 × (loaded + idle_h × r)` (fuel-cost-2's multiplier and no-load rate r). The low edge counts no idle fuel, because the simulator burns none; that is the honest band from FUEL design B1.
- `residual_low = (O − C) + D − D_tol − use_high − 2a`; `residual_high = (O − C) + D + D_tol − use_low + 2a`. Exact Fractions.
- **States:** `UNEXPLAINED` iff `residual_low ≥ 40 L` (materiality, about one normal night's diesel); `WITHIN_MARGIN` iff `residual_low ≤ 0 ≤ residual_high`; `BELOW_MATERIALITY` iff `0 < residual_low < 40`; `EXCESS` iff `residual_high < 0` (more fuel than explained, e.g. an unrecorded delivery; reported, no Finding in v1).
- **Reporting gap minutes** = Σ over spans longer than **60 min** between consecutive accepted `fuel_level` readings inside the window, including the edges. A single or double dropout (30–45 min) is not a gap.

**Architect's pre-registered expectation (arithmetic, written before any run):** night use about 43.4 L (D0, since dispatch is unchanged). Incident night: residual ≈ [120 + 43.4 − 47.8 − 20, 120 + 43.4 − 39.1 + 20] ≈ **[95.7, 144.3] L, UNEXPLAINED**, gap 90 min. Clean nights ≈ [−24.3, +24.3] L, WITHIN_MARGIN. The delivery night ≈ [−27.3, +27.3] L, WITHIN_MARGIN.

**Gates (each one asserted; a failing gate stops the run):**
- **F0a (operational-action path)**:
  - each run is set up from a scenario holding **only** weather and load entries (grep of the documents: no tank `CAUSAL_INPUT`, no `INTERVENTION`, no `REPORTED_OBSERVATION`, no reporting-availability entry);
  - the actions enter only through the frozen-input hook, with origin `OPERATIONAL_ACTION` and their content hash on each added cause;
  - the kernel applies them, or refuses with a reason the builder reports verbatim.
  - Also report: (i) every place a frozen cause's provenance is checked against scenario entries (file:line), i.e. what K0 must extend; (ii) whether the host's `reporting_inputs` takes an added reporting-path span; (iii) the M2 and M3 findings and the `intervention_history` readers. These code facts go in the evidence file as K0's starting map.
- **F1** every run READY and `run_to_end` completes with the actions applied.
- **F2** tank law per step, exactly: `tank[i+1] = tank[i] − E_i × SFC − removal_i + delivery_i`. Σ removal = 120 and Σ delivery = 300 exactly. Report how the kernel spreads the removal over the 45 min (per-step litres).
- **F3** dispatch unaffected: a reference chain of the same 10 runs from the same start state, **without** the operational actions, has equal generator state, accepted generator energy and battery level at every boundary, exactly. Every night's litres equal D0's 43.428 L.
- **F4** no fuel-limited step (`mini_grid.py:683-684` note absent).
- **F5** publication on `registered-kobo-publication` v5, drafted for Kisiwa: fuel-level observations at 15-min cadence; **none** with an instant in `[00:50, 02:20)` of night 4; at least one in the 30 min before and the 30 min after the gap; bias −0.5 L.
- **F6** the registered path, in memory: publish the F5 observations through the mapping set the registered gateway uses for Kobo (the builder names it from code). Report whether fuel-level envelopes are produced. Report, with file:line, the stage at which Kobo's tank readings are dropped today (publication, mapping, binding role config or acceptance). **Not a stop**; it sizes K1 (§8.4).
- **F7** each per-day document's node count is below 4000; record the largest.
- **F8** determinism: `--check` gives byte-equal JSON.
- **F9** band results from **both** sources, (i) the true stock and (ii) the F5 readings (opening and closing chosen by the rule above): night 4 is `UNEXPLAINED` with gap > 0; every other night is `WITHIN_MARGIN` with gap 0; no night is `NOT_ASSESSED`.
- **F10** D0 untouched: `T/probe_kisiwa_nights.py --check` still prints "probe result current", and no D0 file changes.

**Stops (report to the Architect; never design around them):**
- **S0 (OA-1).** The only way to move the tank or open the gap is a scenario entry. **Never** fall back to writing one. Report it; K0's size is then re-ruled (a kernel or host provenance change).
- **S1 refusal** (F0a/F1). Report the refusal verbatim and the smallest fix. Candidates: a cause-origin field in the contract (K0); the stock statement or role in a new `mini-grid` version; a Kisiwa model version (+0.5–1.0). The Architect rules.
- **S2** F2 or F3 fails.
- **S3** F9 differs from the expectation: the incident night is not flagged, a clean night is flagged, or a night is NOT_ASSESSED because of dropout. Report the night and its terms. **Never** change the removal size, times, materiality, accuracy, tolerances, cadence, dropout or seed.
- **S4** F5 fails (the gap does not silence, or the profile refuses the forcing state).
- **S5** F7 over 4000 on a single day. Report it; the Architect rules on splitting the run.
- **S6** the work exceeds 0.75 unit.

**Files (all new; D0's files byte-equal):**
1. `T/probe_kisiwa_fuel.py`: **imports** `kisiwa_site`, `day_document`, `measure_night`, `stop_at` and the constants from `T/probe_kisiwa_nights.py`, never editing it.
   - `kisiwa_registered_draft(document, start, end)` copies `kisiwa_draft`'s pattern (`:130-157`) with the `registered-kobo-publication` v5 profile.
   - The scenario is `day_document(...)` **unchanged** (weather and loads only). `load_actions(path)` parses the draft operational-action log. `apply_actions(run, actions)` adds the run's physical effects to the frozen world inputs (and the reporting span to the reporting inputs) as `DeclaredCause`s with origin `OPERATIONAL_ACTION`, the F0a hook. `dip_values(trajectory, actions)` reads the dips.
   - `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml` (new) is the action log above.
   - `balance(window_terms)` = the parameters above as one pure function.
   - CLI: `--write` writes `.agent/DIESEL-F0/probe-result.json`; `--check`; `--handover` is K7's and is not built now.
2. `host/tests/test_probe_kisiwa_fuel_band.py` (L0, no DB): `balance` on hand-built terms. The incident terms give exactly `Fraction` [95.7…, 144.3…]; a clean night contains 0; residual_low at exactly 40 is UNEXPLAINED; 39.999 is BELOW_MATERIALITY; residual_high < 0 is EXCESS; gap spans of 60 and 61 min.
3. `.agent/DIESEL-F0/probe-result.json` (schema `{"id": "assetops.kisiwa-fuel-probe", "version": 1}`): assumptions, the per-step tank account for night 4, per-night terms and states (both sources), the derived dip values, gates, F6 findings.
4. `.agent/DIESEL-F0-probe-results.md`: a plain-words line ("Kisiwa fuel check (example data, simulator): on the night 120 L was taken out, the check found {lo}–{hi} L unexplained; on the other 9 nights it found nothing outside the margin."), the per-night table, gates, F6 findings, seconds per run, and the stop if any.

**Run** exactly as §2.10, with branch `task/DIESEL-F0-kisiwa-fuel-probe` and worktree `C:\Users\assef\Bineyame\AssetOpsV1-f0`, from main at or after `2ca92124a`. No DB, no prepare, no suite, no `-ExecutionPolicy`.
- **Reading budget:** this §8.1–§8.3 (with §8.2a); `contracts/assetops_contracts/world_inputs.py:140-300`; `S/kernel/execute.py:880-960`; `B/runs/service.py:700-730`, `:2140-2200`, `:3740-3760`; `B/work/service.py:30-40`, `:470-520`; `T/probe_kisiwa_nights.py`; `C/scenarios/fuel-loss-event.yaml:300-480`; `S/packs/mini_grid.py:180-210`, `:405-440`, `:635-740`, `:880-895`; `S/packs/fuel.py:80-110`; `host/execution_adapter.py:670-720`; `S/observation/transform.py:200-260`; `host/tests/test_generator_observation.py:60-110`, `:440-520`; `B/runs/profiles.py:1400-1470`, `:1840-1870`; `S/gateway/mappings.py`.
- **Review:** one fresh Opus reviewer. It re-runs both `--check`s and reads the events against the table and `balance` against the parameters.
- **Merge** on ACCEPT, whatever the result.

### 8.4 Units K0–K9 (outlines with decisions pinned; each gets one consolidated card after F0 and the owner's Q1 answer, inside the contingency)

| Unit | Delivers | Size | Depends on (merged) | Migration |
|---|---|---|---|---|
| **F0** | §8.3 | 0.5 | none (now) | none |
| **K0** operational-action bridge (§8.2a, Option A; owner Q1) | The Lab-private action log `C/operational-actions/kisiwa-001-v1.yaml` (F0's draft promoted). Run setup reads, validates and freezes the physical effects as run-scoped interventions (`DeclaredCause` origin `OPERATIONAL_ACTION`, content hash in `intervention_history`) plus the reporting-path span. Host and kernel apply them. Files: `contracts/assetops_contracts/world_inputs.py`, `B/runs/service.py`, `B/runs/parsing.py`, `B/runs/models.py`, `host/execution_adapter.py`, `S/kernel/execute.py` (only if F0a shows it is needed), tests. **Stop:** any digest or byte change for a run with no actions | 2.0 (1.5–3.0) | F0 | none (file-based log) |
| **K1** Kisiwa Site | D1 (§3.1) as written, **plus** the Foundation vocabulary `fuel-level-sensor-accuracy` (L, PHYSICAL) and `fuel-level-sensor-accuracy-basis` (state: `GENERIC_DEFAULT`, `MANUFACTURER_DATASHEET`, `SITE_CALIBRATION`), carried by `FUEL_TANK` in `B/sites/models.py` (A1's pattern), declared at Kisiwa as 10 L `GENERIC_DEFAULT` with the note "Generic level-sensor accuracy, about 1 % of a 1000 L tank; not this sensor's calibration". The tank publishes on the registered profile, fixed per F6 | 1.25 (+0.25–0.5 if F6 needs a new publication profile version) | F0, A1 | none |
| **K2** fuel records on the operations path (M5) | Extend Work operational records (`B/work/service.py:36-38`, `:470-520`, its model and store): add kinds `FUEL_DELIVERY` (quantity L and `source_document_sha256` for the ticket, required) and `TANK_DIP` (quantity L, required), and a nullable `asset_id` tank link, required for these two kinds and refused on others. Existing kinds and corrections are byte-equal. Add an as-known read `fuel_records(site, tank, window, known_at)` for K3. **Not a telemetry envelope:** the contract's `OPERATIONAL_RECORD_KINDS` (`source_envelope.py:126`) is untouched. **Changed by OA-1 from a separate table:** this is the record path real operations use, and the one the technical design names | 0.75 | F0 | **0054** (widen the kind CHECK, add `asset_id`) |
| **K3** `fuel-balance-1` | Pure rules (§8.3 parameters, verbatim), service and store; one stored row per night per Site with a bound `fuel_level` and a declared accuracy. States and limitations (`MISSING_OPENING`, `MISSING_CLOSING`, `REPORTING_GAP`, `DIP_SENSOR_CONFLICT` when \|dip − nearest sensor\| > a + 10 L, `DELIVERY_RECORDED_LATE`). Reuses A2's slot rule and the as-known SFC and no-load history; it never re-derives them. Parameter version `fuel-balance-1/v1`. It never feeds the dispatch consequence. Kobo (no accuracy declared) gets `NOT_ASSESSED`; `mini_depth.rules.assess_fuel_hour` and Kobo's Fuel page are byte-equal | 1.5 | K1, K2 | **0055** `0055_fuel_balance_window.py` |
| **K4** UNEXPLAINED_FUEL Finding | The Finding kind raised from an `UNEXPLAINED` window (one per window, existing thread and recurrence rules). Consequence model `fuel-residual-1` = [residual_low, residual_high] L × the declared diesel price as known at the window end (`select_window_price`), basis `UNEXPLAINED_FUEL_AT_DECLARED_PRICE`, never added to fuel-cost-1/2 rows. Kisiwa board **Protect** row: "Fuel" contributor from the window (replacing `NO_FUEL_BALANCE`, `B/site_outcomes/mini.py:77`, `:873-877`, only where a window is assessed) and the thread line; chain vocabulary and claims | 2.0 | K3; **board/chain part after CH-5d1, MB-1, A3, PV-1** | **0056** (Finding kind and consequence model CHECKs) |
| **K5** fuel screens | Site Performance › Fuel in **window mode** (night list; v69 `:623-630` cards, waterfall and bridge filled), a list of deliveries and hand dips, and the Finding's fuel panel. **MD-FUEL-K-1:** a night window, not the mock's Kobo hour. **MD-FUEL-K-2:** the notice and the RESIDUAL row reworded on every Site (owner wording rule, below). Layout evidence at 1440 and 390 | 1.0 | K3; the Finding panel after K4 | none |
| **K6** `fuel-residual-within-band-1` | The verification family and page (§8.5) | 1.5 | K4, MV-1, A2 | **0057** (0052 pattern: widen `rule_id`/`plan_version`, the family CHECK with reserve columns NULL) |
| **K7** Kisiwa story data | D3 (§3.3) as written, **with** 10 runs (§8.3 table). The per-day scenarios hold weather and loads only (OA-1); the fuel actions come from K0's log. `T/probe_kisiwa_fuel.py --handover` writes `V/kisiwa-day-handover-v1.json` (start states **and** dip values; `--check` guards it). The action-log injector posts each action's record through the Work API (delivery ticket recorded 30 min after delivery; dips signed by "Shift operator"; the SITE_VISIT for the seal and sensor fix), then the Action (§8.6), plan freeze and evaluation. One Kisiwa-only scratch prepare: stored windows equal F0 (exact), then drop | 2.25 | K0, K1, K2 (data part); K6 (freeze step) | none |
| **K8** four Sites on estate screens | D4 (§3.4) **minus** the Assure value line (H2), **plus** the Protect card Kisiwa unexplained-fuel line "{site} · {code}: about {lo}–{hi} L unexplained fuel, {lo$}–{hi$} {cur} at your declared price" (own basis, never summed). The Assure count includes the Kisiwa verified result. MD-FUEL-D-1 kept | 1.0 | PV-1, A3, CH-5d1, K4; captures after K7 | none |
| **K9** finish, guard, rehearsal | KIS-1–KIS-8 (§8.7), COH-17 and V4 for Kisiwa, **wording guard** (a new check in `tools/checks/`, wired into `check-all`): served copy and `F/` strings contain none of theft/stolen/stole/siphon/pilfer (case-insensitive; tests and code comments excluded), with a self-test. Whole-list rehearsal prepare (3 h cap). DS-1 beat (§8.6) | 1.0 | all | none |
| Contingency | Card round after F0, the F6 publication risk, the K4 Finding-kind risk | 0.5 | | |
| **Total** | | **14.75 remaining** (15.25 with D0's spent 0.5); range 13.0–17.5. With Option B instead of K0 (owner Q1): 12.75 remaining | | |

**Wording (K5, MD-FUEL-K-2), literals:**
- Notice (replaces `MiniPerformance.tsx:1311`): "Unexplained fuel is fuel that left the tank that the generator's running and recorded deliveries don't account for, within a stated margin. It does not say why the fuel left, and it is never added to the generator's possible extra fuel."
- RESIDUAL row (replaces `:1343`): "Needs every term with a supported range; never says why fuel left".
- These are the only Kobo Fuel page bytes that change.

**Finding literals (K4; the guard and guard V apply):**
- Title: "Unexplained fuel overnight".
- Line 1: "About {lo}–{hi} L left the tank on the night of {date} (6 pm to noon) that the generator's running and recorded deliveries don't explain."
- Line 2, only when the gap is above 0: "The tank sensor sent no readings from {a} to {b}."
- Money: "Worth about {lo$}–{hi$} {cur} at your declared {p} {cur} per litre. This does not say why the fuel left the tank."
- Litres to 0.1, money by `money2`; the browser formats no number.

**File and migration conflicts:**
- **Migrations: A1 owns 0053 (merged).** The earlier D2 claim on 0054 is **void** (D2 is withdrawn). The new chain is **K2 0054 → K3 0055 → K4 0056 → K6 0057**, each with `down_revision` = the previous one. FUEL-1 lanes (A2, A3, MB-1, WD-1, PV-1) and CH-5d1 add none. If any other merge lands a migration first, the next K unit renumbers; the single-alembic-head test catches a miss.
- **K4 ↔ MB-1, A3, PV-1, CH-5d1:** `B/site_outcomes/mini.py`, `board.py`, `B/chain/vocabulary.py`, `B/chain/claims.py`, `T/checks/chain_coherence.py`. K4 builds the Finding, consequence and store first; its board and chain edits wait for lane 1 to finish (PV-1 merged).
- **K5 ↔ none:** `F/sites/MiniPerformance.tsx` is not edited by lanes 1–2.
- **K0 ↔ none:** no lane 1–2 unit or CH-5d1 edits `B/runs/`, `host/execution_adapter.py`, the contracts or the kernel. K0's stop guards Kobo, Cold and EV run digests.
- **K2 ↔ none:** no lane 1–2 unit edits `B/work/`. The Work tests (`test_w401_*`) must stay green.
- **K6 ↔ A2:** `B/actions/verification.py`, `verification_rules.py`, `verification_families.py`. K6 starts after A2 merges.
- **K8 ↔ CH-5d1, PV-1:** `B/site_outcomes/read.py`, `F/estate/PortfolioOutcomes.tsx`. K8 goes after both; the CH-5d1 Optimize card and PV-1's Assure lines stay byte-equal for the three existing Sites.
- **K9 ↔ MV-1, MB-1, A3, PV-1:** `T/demo_combined_finish.py`, last.
- **Data effects (no edit; tell the lanes):**
  - CH-5d1's Optimize card takes the "two or more priced Sites" path (Kobo idle mornings after A3, and Kisiwa's dispatch Findings), never summed.
  - PV-1's Assure card gains **no** line (H2), so PV-A is unchanged.
  - The all-26 audit is recaptured in K8.

### 8.5 K6 decisions (verification)

- **Origin:** a W1 Action raised from the UNEXPLAINED_FUEL Finding thread. Plan version `fuel-residual-verification-1`.
- **Baseline:** the Finding's own window (stored id). **Later:** the first 3 COMPLETE nights whose window starts at or after the Action's effective instant, looking ahead at most 14.
  - COMPLETE = the window is not `NOT_ASSESSED`, and every generator-state and generator-power slot is COMPLETE (the mill's weakest-row rule).
  - Chosen by grade, never by value.
  - The night choice is built here, because D2 is withdrawn (+0.25 against the feasibility's 1.25).
- **Target (frozen in the plan):** `{"rule": "every later night: residual_low <= 0 <= residual_high and reporting_gap_minutes == 0", "over": "first 3 COMPLETE nights after the change", "basis": "owner-reviewed design, fuel-loss-feasibility Part A §3 Verify, chosen 2026-11-07"}`.
- **Verdicts:** VERIFIED (all 3 pass); INEFFECTIVE (any later night fails); INCONCLUSIVE (fewer than 3 COMPLETE nights in 14). All recorded truthfully.
- **Page** `F/sites/SiteFuelResidualVerification.tsx`, reusing the mill page's components and CSS.
  - VERIFIED line: "On {n} fully checked nights after the change, the tank's fuel matched the generator's running and recorded deliveries within the margin, and the tank sensor reported all night."
  - Fixed line (H1), always shown: "This check shows the fuel stayed accounted for after the change; it does not measure how much the change itself prevented."
  - No money, so no mock deviation is needed for money.

### 8.6 Story (K7) and DS-1 beat

- **Action**, raised from the Finding thread at 12:30 local on the day after night 4 (after the closing reading):
  - title "Seal the tank cap, sign the dip log at every shift change, and put the tank sensor on its own protected power supply";
  - effective at 15:00 local on run 6's start (done the next afternoon);
  - plan frozen at that instant.
- **Night 5** (Finding raised, change not yet done) is authored clean. That is reasonable and is not counted in either window.
- **After the change:** dips at 06:00 and 18:00 local each day, signed. The after-nights have no removal and no gap (authored, under the owner's scenario guidance; §8.2).
- The evaluation runs after night 8 is graded. Dates are fixed in K7's card so that night 8 closes before the S+0 board cutoff.
- **DS-1 beat (draft):** "Kisiwa: one night, about {lo}–{hi} L left the tank that the generator and deliveries don't explain, while the tank sensor was silent → seal the cap, sign the dip log, protect the sensor's power → the next 3 checked nights stayed within the margin with the sensor reporting. We say unexplained, not why; this is example data."

### 8.7 Finish rows (written in K9, run at E3)

| Row | Checks |
|---|---|
| KIS-1 | `KISIWA-001`; diesel price v1, no-load 4.9 L/h `GENERIC_DEFAULT` and sensor accuracy 10 L `GENERIC_DEFAULT`, as known; stop setting 90 throughout |
| KIS-2 | Kisiwa dispatch Findings are SUPPORTED and priced fuel-cost-2, with `quantity_high` computed from stored segments |
| KIS-3 | Every stored night window's band reproduces from its stored terms and the declared parameters (Fractions); night 4 is UNEXPLAINED and all others are WITHIN_MARGIN, as computed, never forced |
| KIS-4 | The Finding's money band = stored litres × the declared price; no field equals a sum with any dispatch money |
| KIS-5 | The verdict as computed from stored windows (INEFFECTIVE recorded truthfully if so); no money on the page |
| KIS-6 | Portfolio and estate list four Sites; counts equal the boards |
| KIS-7 | CH-5d1's Optimize card on the ≥2-priced-Sites path, with no sum |
| KIS-8 | The Protect card Kisiwa line equals its source; the wording guard is clean on served pages |
| re-expected | COH-17 and V4 (Kisiwa), F-THREADS (the Kisiwa thread) |

### 8.8 Order, totals, date, E3

```
now (t=0):   CH-5d1 (lane 1, finishing) | A2 (lane 2) | F0 (lane 3)
t≈0.5:       F0 result -> card round (contingency) | K2 (lane 3)
t≈0.55:      A2 merged -> K1 (lane 2)
t≈0.75:      CH-5d1 merged -> MB-1 -> WD-1 -> PV-1 (lane 1, to ≈2.9)
t≈1.25:      K2 merged (0054)
t≈1.8:       K1 merged -> A3 (lane 2, after MB-1) | K3 (lane 3, 0055)
t≈2.5:       A3 merged -> K0 (lane 2, after the owner's Q1 answer; to ≈4.5)
t≈4.5:       K0 merged -> K7 data part (lane 2, to ≈6.0)
t≈2.9:       PV-1 merged -> K5 fuel page (lane 1, after K3)
t≈3.3:       K3 merged -> K4 (lane 3, 0056; board part after PV-1)
t≈5.3:       K4 merged -> K6 (lane 3, 0057) | K8 code (lane 1) | K5 Finding panel
t≈6.8:       K6 merged -> K7 freeze step and Kisiwa scratch prepare (≈7.3)
t≈7.3–7.5:   K8 captures -> merged
t≈7.5–8.5:   K9 (finish rows, guard, rehearsal prepare)
then:        DS-1 -> E1–E6
```

- **Critical path:** F0 → K1 → K3 → K4 → K6 → K7 freeze → K8 captures → K9 ≈ **8.5 lane-units ≈ 2.8 working days**, plus the Kisiwa scratch prepare (about 40 min) and one rehearsal prepare (about 1.5 h).
- K0 runs on lane 2, off the critical path: K7's data part needs it only by about t≈6.8, when K6 merges.
- **Remaining before DS-1:** lanes 1–2 **4.5** (CH-5d1 0.75 + MB-1 1.25 + WD-1 0.15 + PV-1 0.75 + A2 0.55 + A3 0.7 + E3 allowance 0.35; the coordinator confirms CH-5d1's remainder) + Kisiwa **14.75** = **19.25** (Option B: 17.25).
- **Plan total:** ≈ 117.3 (FUEL-1) + 15.25 = **≈ 132.55** (Option B: ≈ 130.55). This replaces the earlier ≈ 124.3 with the withdrawn D lane.
- **Demo date:** about **+3 working days** (range 2.5–5) against the lanes-1–2 plan without Kisiwa. K0 adds effort but sits off the critical path; its slip risk widens the top of the range. That is about +1 more than the withdrawn D-lane plan, and inside the "about 4–5 working days later" the owner accepted with "Kisiwa with missing fuel". Without Kisiwa, DS-1 would start after about 1 working day of lanes.
- **E3:** 10 Kisiwa day-runs at an estimated 150–200 s each with the pipeline (D0: about 1 s in memory per run), plus one 15-min tank signal and a few records: **+25–35 min**, so **E3 ≈ 1.3–1.5 h of the 3 h cap**. K7 records seconds per day and K9 restates the figure. If the rehearsal exceeds 2.5 h, the Architect rules before E3; the cap is never raised silently.

### 8.9 Plan HTML (`Docs/demo-sprint/client-demo-plan.html`) rows to change

The coordinator carries FUEL-1's delta first (§6 of FUEL-1), then:
1. **Build-units table:** replace the "DIESEL-1 … D0–D5 … 7.0" row (or add, if not yet carried) with "DIESEL-1-R2 Kisiwa diesel-hybrid example Site with the unexplained-fuel story (owner 2026-11-07: Kisiwa with missing fuel; 'unexplained fuel', never 'theft'; fuel events through operational actions)", **15.25** (D0 0.5 done, F0 0.5, K0 2.0, K1 1.25, K2 0.75, K3 1.5, K4 2.0, K5 1.0, K6 1.5, K7 2.25, K8 1.0, K9 1.0, contingency 0.5). Note: "the 60 % generator-setting trial (D0) was not met at 4.4 % and is not shown in the demo". If the owner picks Option B: 13.25 without K0.
2. **Total row:** ≈ 132.55; lanes +15.25.
3. **G5 freeze and G6:** +15.25 (DIESEL-1-R2) on top of FUEL-1's +5.35 and CH-5d's −0.25.
4. **Lanes schedule table and figure:** a lane 3 strip F0 → K2 → K3 → K4 → K6 → K9; K1, then A3, K0 and K7 on lane 2; K5 then K8 on lane 1 after PV-1 (§8.8).
5. **E3 row:** "Kisiwa: 10 day-runs, +25–35 min; E3 ≈ 1.3–1.5 h of the 3 h cap".
6. **Machine-time note:** +1.5 h rehearsal prepare (K9) and +40 min Kisiwa scratch prepare (K7), both before E3.
7. **Calendar estimate line and OD-P9:** G6 moves about +3 working days (range 2.5–4.5) against the plan without Kisiwa.
8. **Rulings table:** a "DIESEL-1-R2" row pointing to this §8: D0 dropped from the demo, G4 merge confirmed, F0 ruling, OA-1 and the operational-action bridge (§8.2a), the fuel-balance-1 parameters, migrations 0054–0057, and no special label for the after-nights (H1–H5).
9. **After-the-demo list:** remove any "Kisiwa unexplained fuel ≈ 8.5" entry; keep "Kisiwa measured tank or flow panel (simulator idle law)". BL-16's tank half is now done by K1/K3 for Kisiwa only.

### 8.10 Owner questions

1. **How do fuel deliveries, the missing fuel and hand dips get into the example site?** You told us these come in through operational actions, the way real operations would. Today the product can *record* what people do, such as notes and readings, and with a small addition it can record fuel deliveries and dips. But nothing yet lets a recorded action change the simulated site itself: today the tank only changes if we write the change into the example day directly, which you ruled out. Options:
   - **(a) Recommended:** build that link. Each action (delivery, missing fuel, dip, the seal and sensor fix) is written once. The simulated tank changes because of it, and the records reach the product the normal way. The missing fuel has no record, as in real life. About **+2 units**. It runs beside other work, so the demo date moves little (range widens by about half a day).
   - **(b)** Keep the same single list of actions, but have the tool turn each one into an "operator action" entry in the example day, with the records going in the normal way. About +0.25 units. It is cheaper, but the change still sits inside the example day, which is what you said not to do.

   The half-unit trial (F0) runs now either way and tests the link in memory first, so nothing is built before you answer.

For the owner's information, in plain words:
- The 60 % generator-setting trial saved about 4 % of diesel a night against your 20 % bar, so we leave it out of the demo entirely rather than show a weak result.
- The nights after the fix are example data like every other Kisiwa day. The screen claims only that the fuel stayed accounted for afterwards, never that the fix stopped a loss. So no extra label is needed.
- Kisiwa will also show the usual "generator ran when the battery could have carried the load" findings; they are real results from its data, and we don't narrate them.
- We are not adding a rainy-season stretch: more diesel would make missing fuel harder to see, not easier.
- Kisiwa adds about 3 working days before the demo (range 2.5–5), within the 4–5 you accepted.

---

