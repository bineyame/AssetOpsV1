## 9. Ruling DIESEL-1-R3: after F0's stop (registered probe path, tank-level signal, K0 extended, F0 re-issued)

- Architect: Claude (fresh Architect), 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `826d91572` (CH-5d1 merged). F0 evidence read on `task/DIESEL-F0-kisiwa-fuel-probe` at `aa49a18fd` (`.agent/DIESEL-F0-probe-results.md`, `T/probe_kisiwa_fuel.py`, the draft action log).
- Owner decisions in force, verbatim: `.agent/owner-kisiwa-scope-2026-11-07.md` (build with the operational-action link, i.e. §8.2a Option A, K0); `.agent/owner-scenario-data-2026-11-07.md` ("these are injected through operational actions"); `.agent/owner-missing-fuel-2026-11-07.md` ("'Unexplained fuel', never 'theft'").
- **This section amends §8.3 (F0), §8.4 (K0, K1, totals) and §8.8–§8.9.** Everything else in §8 stands. Where §8 and §9 differ, §9 wins.
- **F0's stop was correct and is accepted as history.** The builder reported S1 verbatim, tried no fix and changed no declared item. F0 spent its 0.5 unit. Nothing in §8.3's declared world, parameters or pre-registered expectation changes.

### 9.1 Decision 1: the S1 fix for the probe — neither (a) nor (b) as proposed; (c) register Kisiwa in memory through the product's own import, conversion and selection code

**Ruling (c).** F0r registers Kisiwa in an `InMemoryFoundationStore` with the same calls K1 will make against Postgres, then sets up every run through the **real** `RegisteredLabBasis` over that store. Only the storage engine is substituted.
- `B/sites/foundation_service.py:247` `import_site(store, tenant_slug="demo", configured_tenant_slug="demo", source=ImportSource(path, sha256, record), legacy_documents=(), clock=…)` with the Kisiwa Site record (D0's `kisiwa_site()` rendered document; `B/sites/adapters/import_files.py:46` `read_import_source` if a file is needed, written to the scratch folder, never to `C/`).
- `B/sites/binding_conversion.py` `convert(store, BindingService(store, clock), tenant, site, fixture)` with a new draft fixture `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json` (§9.4).
- `RunSetupService(..., registered_bases=RegisteredLabBasis(ImportedSiteRegistry(FoundationService(store, "demo", clock))))` (`B/runs/registered_basis.py:49-107`). The `FakeSites` legacy store holds no Kisiwa.
- Precedent, default suite, no DB: `backend/tests/test_s2_registered_basis.py:83-93` and `backend/tests/test_s1_bindings.py:39-44` (Kobo imported and converted over `InMemoryFoundationStore`, `backend/tests/foundation_fakes.py`).

**Why not (a):** Lab v3 has no device resolutions and no registered basis, so a pass would prove a path the demo never uses (D0's limit, repeated). The demo prepare runs Kisiwa through `registered-kobo-publication` v5 and the gateway, exactly as Kobo (`T/demo_combined_kobo.py:401-410`).
**Why not (b):** a hand-built `RegisteredSiteSelection` skips `select_registered_basis`, `_signal_mappings` (`registered_basis.py:110-146`: every bound asset must be a Foundation component) and the resolution-unit check (`B/runs/service.py:919-937`). Those are the three places Kisiwa's template can fail on the registered path.
**What (c) proves beyond F0's questions:** that Kisiwa's template imports, that a Kobo-shaped binding set converts onto it, that the registered selection accepts it, and that `registered-kobo-publication` v5 is not tied to `KOBO-001` by name. That answers D1 pre-flight (a) (§3.1) before K1 starts.
**Cost:** about +0.15 inside F0r.

### 9.2 Decision 2: the tank-level signal — `mini-grid` v7, a new unit K1a (0.5), used by Kisiwa only

**Finding confirmed by Architect reading.** `S/kernel/model.py:396-400` reports a numeric STATE_SIGNAL only with a STATE_SAMPLE handler; `S/packs/mini_grid.py:192-207` has only the STOCK handler for `fuel-tank-volume`, and v2–v6 are `replace`s that keep that handler table (`:1019`, `:1244`). `host/execution_adapter.py:734-739` then drops `fuel-level-sensor/fuel-level` silently. The fuel pack's sampler (`S/packs/fuel.py:207-221`, `SAMPLE_HANDLER`) is model-agnostic. The `fuel-tank` component relation already names the state (`mini_grid.py:230-232`), so the kernel's one-relation rule (`model.py:360-380`) is satisfied.

**K1a: `mini-grid` v7 (simulator and product profile).** One new version; v1–v6 objects are not edited.
- Simulator (`S/packs/mini_grid.py`, after `:1256`): `MINI_GRID_V7_MODEL = replace(MINI_GRID_V6_MODEL, model_profile_version=7, statement=V6.statement + V7_SENTENCE, handlers=<V6 handlers with the stock handler restated> + (fuel.SAMPLE_HANDLER,))`.
  - `fuel.SAMPLE_HANDLER` is imported and reused, never copied.
  - The STOCK handler is restated for v7 only (same `handler_id`, role, kind, floor, `consume`, `initialize`), with statement: "The fuel in the tank, initialized by the scenario, moved by accepted generator energy and by any frozen declared cause, such as a recorded operational action." The v1–v6 handler keeps "moved only by accepted generator energy". Reason: K0 makes the old sentence false for a run with actions.
  - `V7_SENTENCE`: " Version seven also samples the fuel in the tank at an instant, after that instant's events, so a tank level sensor can report it."
- Product profile (`B/runs/profiles.py`, after `:1367`): `MINI_GRID_V7_MODEL = replace(MINI_GRID_V6_MODEL, model_profile_version=7, statement=…same sentence…, supported_states=<v6's, with fuel-tank-volume supported_roles {"CAUSAL_INPUT", "REPORTED_OBSERVATION"} and the restated statement>)`. Appended to `MODEL_PROFILES` (`:2164-2175`), after v6.
- Executable: appended to `host/execution_adapter.py:128-137` `EXECUTABLE_MODELS` and to the profile tuple in `host/tests/kobo.py:129-138` (the `next(...)` there picks the first match, so `None` still resolves to v1; no Kobo call changes).
- **Publication:** no new publication profile and no mapping or binding change. `registered-kobo-publication` v5 already declares `fuel-level-sensor/fuel-level` at 15 min, bias −0.5 L, dropout 40/1000, and the `fuel-level-reporting-availability` forcing state (`B/runs/profiles.py:1426-1470`, `:1985-2000`). Kisiwa's template already carries the device and the `fuel-tank-level` mapping (D0 draft `:292-297`, `:358-360`). §8.4's "K1 +0.25–0.5 if F6 needs a new publication profile version" is **withdrawn**: F6 found the drop at execution, not publication.

**Effects (the stops guard each):**
- **Digests.** v1–v6 trajectories, run identities and digests are byte-equal; v7 is a new identity, so no frozen run changes. A v7 run's trajectory carries the sampled tank value, so it differs from a v6 run of the same document by design. Stop: any v1–v6 digest change.
- **Kobo stays on v6 and publishes no tank level.** Kobo's replay pins the model through its manifest (`host/tests/test_s6_verification_replay.py:141-146`); `T/demo_combined_kobo.py` is not edited. So Kobo still stores **0** `fuel_level` rows, Kobo's Fuel page and `mini_depth.rules.assess_fuel_hour` are byte-equal, A2/A3/MB-1 checks and the all-26 audit are unaffected, and K3 gives Kobo `NOT_ASSESSED` as §8.4 says. Moving Kobo to v7 is **not** demo-critical (it would add tank rows to Kobo's Fuel page and change Kobo's evidence, checks and captures); it goes to the after-the-demo list as "Kobo tank level (mini-grid v7 on Kobo)".
- **Kisiwa starts publishing `fuel_level`** at 15 min from K1 onward, through the gateway and the activated binding snapshot, as any registered signal. Its consumers already exist (`mini_depth/inputs.py:141`, `:254`; `evidence/overview.py:80`); K3 is the first that judges it.
- **Profile listings.** The Lab's model-profile catalogue gains one row. Tests that enumerate `MODEL_PROFILES` or `EXECUTABLE_MODELS` (`backend/tests/test_component_properties.py`, `backend/tests/test_addressed_bindings.py`, `host/tests/test_kernel_conformance.py`, `host/tests/test_mini_grid.py`) take the new entry. That is a listing change, not a digest change.
- **Guards and checks:** no served copy changes; guards A, W, N, V, M and frontend-hardwiring are unaffected; chain coherence is unaffected.

**K1a card (0.5; range 0.4–0.75):** files above; tests:
- L0 `host/tests/test_mini_grid_v7.py`: `MINI_GRID_V7_MODEL.reports("fuel-tank-volume", "STATE_SIGNAL", "L")` is true and v6's is false; v7's advertised supported states equal the product profile's (the existing parity pattern); a short Kobo-template run on v7 with `registered-kobo-publication`'s fuel-level signal gives 15-min tank observations equal to the stock at each instant minus 0.5 L before noise; the same document on v6 gives an identical generator, battery and tank trajectory except the sample (physics unchanged).
- Byte-equal pins: one v6 Kobo run digest and one v5 run digest, re-asserted unchanged.
- **Stops:** any v1–v6 digest or trajectory byte change; any Kobo, Cold or EV byte change; a need to change a publication profile, mapping or binding; more than 0.75.
- **Order:** starts **now, in parallel with F0r** (its content does not depend on F0r's result; F0r uses a probe-local copy, §9.4). If F0r stops on S4 again (the sampled tank does not publish), K1a pauses at its next commit and the Architect rules.

### 9.3 Decision 3: K0's extended scope (2.0 → 2.5; range 2.0–3.25)

F0's code facts (§F0a in the evidence file) change K0 as follows: the host and kernel need **no** change to accept added causes and conditions (no provenance check refuses them: `S/kernel/execute.py:244-259`, `:721-730`, `:857-872`; `B/runs/models.py:976-1045`; `host/execution_adapter.py:769-820`), which frees about 0.4. But K0 must add the origin field on both frozen record kinds, provenance labels, persistence round-trip and composition wiring, which costs about 0.9.

**K0 consolidated scope:**
1. **Origin on causes and conditions.** Two fields on `DeclaredCause` (`contracts/assetops_contracts/world_inputs.py:170-204`), `FrozenCause` (`B/runs/models.py:572-619`), `FrozenReportingPathCondition` and its contract counterpart (PRE-FLIGHT names the class):
   - `origin: Literal["SCENARIO", "OPERATIONAL_ACTION"] = "SCENARIO"`;
   - `action_ref: str | None = None`, format `"{action_id}:{content_sha256}"` (content hash = sha256 of the action's canonical JSON, sorted keys, compact separators, ASCII, as F0's `load_actions`).
   - **Byte-equal rule:** every render, canonical form and hash (`B/runs/parsing.py`, the trajectory identity `contracts/assetops_contracts/trajectory.py:570-589`, `:639-662`, every run store) **omits both keys when `origin == "SCENARIO"` and `action_ref is None`.** So every existing run, scenario cause and digest is byte-equal. Stop: any digest change for a run with no actions.
   - Parse refusals, kind `CAUSE_ORIGIN_INVALID`: `OPERATIONAL_ACTION` without `action_ref`; `action_ref` with `SCENARIO`; an unknown origin.
2. **Run setup reads the log by a named version, never "latest".** New optional run-setup request key `operational_actions: {"log_id": "kisiwa-001", "log_version": 1}` (absent = no actions; the request and identity are then byte-equal). A new read-only port `OperationalActionLogPort` with a file adapter over `C/operational-actions/{log_id}-v{log_version}.yaml`. The identity freezes `operational_action_log = {log_id, log_version, sha256}` only when present (omitted otherwise).
   - Selection: actions with `at` in `[start_time, end_time)`.
   - Effects (unchanged from §8.2a): `FUEL_DELIVERY` → INCREASE POINT; `FUEL_REMOVAL_UNRECORDED` → DECREASE WINDOW plus, with `sensor_disconnected`, a `fuel-level-reporting-availability@fuel-tank` WINDOW condition; `TANK_DIP`, `TANK_SEALED`, `SENSOR_POWER_PROTECTED` → no physical effect.
   - `event_id` = `"{action_id}/{effect}"`, effect ∈ `tank-increase`, `tank-decrease`, `sensor-disconnected`. A clash with a scenario event id refuses (`OPERATIONAL_ACTION_EVENT_ID_CONFLICT`).
   - `intervention_history` += `"OPERATIONAL_ACTION:{action_id}:{content_sha256}"`, ordered by `at`, then `action_id` (F0's form).
   - Setup refusals (typed, nothing written): `OPERATIONAL_ACTION_COMPONENT_UNKNOWN`; `OPERATIONAL_ACTION_STATE_NOT_CAUSAL` (the model has no CAUSAL_INPUT STOCK for the state); `OPERATIONAL_ACTION_UNIT` (not L); `OPERATIONAL_ACTION_OVER_CAPACITY` when initial stock + Σ deliveries in the run up to and including this one > the frozen `fuel-tank-capacity` (an exact sufficient bound, since nothing else raises the stock; **refused, never clamped**); `OPERATIONAL_ACTION_OVER_STOCK` when a removal exceeds initial stock + earlier deliveries in the run. **Correction to §8.2a:** "a delivery fits free capacity at `at`" cannot be known at setup (the stock at `at` depends on dispatch); the bound above replaces it. The kernel floor (`insufficient-fuel`) remains the run-time backstop and is reported by the existing bound-case path, never silently.
   - `TANK_DIP` and the two `SITE_VISIT` actions are validated (component exists, `at` in interval) but freeze nothing.
3. **Provenance labels.** `B/runs/provenance.py:434-459` and `:513-536`: a cause or condition with `origin == "OPERATIONAL_ACTION"` renders `answered_by="OPERATIONAL_ACTION"`, `answered_by_detail="Operational action {action_id} ({kind}, by {actor}), log {log_id} v{log_version}"`. Scenario rows keep `"SCENARIO"` byte-equal. `answered_by` is a free string (`world_inputs.py:111`, `:266`; `F/shell/runSetupClient.ts:113`), so the Lab view shows it with no frontend edit; this is Lab-only, never client-facing.
4. **How operator records reach the product: only through the Work API (K2), never through the run.**
   - `OPERATOR_RECORD` (M2) gets **no** reader; registered v3+ keeps `record_channels=()` (`B/runs/profiles.py:1946`); `SourceEnvelope` stays MEASUREMENT-only for the registered path (`host/lab_execution.py:2829-2835`); `OPERATOR_COMMANDABLE_STATES` (`B/scenarios/models.py:255-258`) is unchanged.
   - The same log is the one source: K7's injector reads it and posts `FUEL_DELIVERY` (ticket 30 min after `at`), `TANK_DIP` (value from the handover file, §8.3) and the `SITE_VISIT` record through K2's `post_operational_record`. `FUEL_REMOVAL_UNRECORDED` posts nothing.
   - The product never reads `C/operational-actions/`: a K0 test asserts that no module under `B/` other than the run-setup adapter, and nothing under `F/`, names that path.
5. **Composition.** Wire the port in `B/main.py:690` (the Lab composition) and in the registered test harnesses that K7 uses (`host/tests/test_s6_verification_replay.py` `LabRunner` pattern; PRE-FLIGHT names the exact constructor). Default `None` → no actions.
6. **Host and kernel:** no change expected (F0r proves it in memory, §9.4 F0a). If F0r shows otherwise, K0's +0.5 reserve inside the range covers it, and the Architect rules.

**Files:** `contracts/assetops_contracts/world_inputs.py`, `contracts/assetops_contracts/trajectory.py` (only if the omit rule needs it), `B/runs/models.py`, `B/runs/parsing.py`, `B/runs/service.py`, `B/runs/ports.py`, new `B/runs/operational_actions.py` (loader, validation, freeze), new adapter under `B/runs/adapters/`, `B/runs/provenance.py`, every run store's render/parse (PRE-FLIGHT names them), `B/main.py`, new `C/operational-actions/kisiwa-001-v1.yaml` (F0r's draft, promoted verbatim after F0r merges), tests.
**Tests:** L0 round-trip of both origins on every store; byte-equal digests for one Kobo, one Cold and one EV fixture run and for every shipped scenario's frozen causes; each refusal; the Kisiwa run-2 delivery and run-4 removal frozen with origin, ref and history; the provenance rows; the no-reader test. L1/L2 setup through the registered path on own `assetops_k0_test`.
**Size, 2.5:** contract and models origin with the omit rule 0.5; request key, port, adapter, loader, validation and freeze 0.75; provenance 0.15; persistence round-trip 0.25; composition 0.2; tests 0.4; host/kernel reserve 0.25. **Stops:** any digest or byte change for a run with no actions; a need to change M2, M3, `record_channels` or the envelope schema; more than 3.25.

### 9.4 Re-issued F0 (F0r), full card, ready for a builder now, 0.5

**Branch and worktree:** continue `task/DIESEL-F0-kisiwa-fuel-probe` in `C:\Users\assef\Bineyame\AssetOpsV1-f0`. First merge main (for this §9). The pre-registration commit `54ef019e1` stands unchanged.

**Unchanged from §8.3, verbatim:** purpose questions 0–5; the declared world table (10 day-runs, 700 L start, the four action kinds and their times, dips, change instant); the `fuel-balance-1` parameters; the Architect's pre-registered expectation; the action log `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml` (not edited). D0's files stay byte-equal.

**What changes (and only this):**
1. **Registered setup through (c), §9.1.** New draft fixture `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json`: `backend/conversions/kobo-001-bindings.json` with the Site code `KISIWA-001` and every binding kept whose `legacy_mapping_id` is a mapping in Kisiwa's template. Report every Kobo binding dropped and why. A Kisiwa mapping with no binding in the fixture is a **stop** (conversion refuses unconverted mappings, `test_s1_bindings.py:148-154`); never invent a binding. K1 promotes this file verbatim to `V/kisiwa-001-bindings.json`.
   - Clocks: import at `2026-09-29T09:00:00Z`, conversion at `2026-09-29T09:30:00Z` (before run 1 at `2026-10-01T12:00:00Z`); `knowledge_at` absent; the request's `foundation_version` = the registered version the selection returns (as Kobo, likely 2). Record all three in the result JSON.
2. **Probe-local `mini-grid` v7, stated plainly.** The real v7 belongs to K1a (§9.2). F0r builds, **inside `T/probe_kisiwa_fuel.py` only**, `PROBE_V7_SIM` and `PROBE_V7_PROFILE` with exactly K1a's content (§9.2: version 7, `fuel.SAMPLE_HANDLER` reused, restated stock statement, product supported roles `{CAUSAL_INPUT, REPORTED_OBSERVATION}`). It passes `PROBE_V7_PROFILE` in `model_profiles=` and executes with `run_to_end(run, PROBE_V7_SIM)` and `reporting_inputs(run, profile, PROBE_V7_SIM)` instead of `model_for(run)` (which only knows `EXECUTABLE_MODELS`). The result JSON and the evidence file carry the line: **"Tank level from a probe-local mini-grid v7 identical in content to K1a's; product code has no v7 until K1a merges."** No product file is edited.
   - The reference chain (F3) uses the same probe-local v7 without actions, so dispatch equality compares like with like. F3 additionally asserts that a v6 chain without actions has equal generator state, accepted generator energy, battery level and tank stock at every boundary (v7 adds a sample, not physics).
3. **F0a carrier.** Origin and content hash ride in the `event_id` prefix `OPERATIONAL_ACTION/` and in `intervention_history`, as F0 built (no product origin field until K0). F0a passes on that carrier.
4. **F6 becomes a gate on the registered report path, in memory:** pass the F5 observations through `host/gateway_publication.py:79` `keyed_reports(run_id, basis.snapshot_sha256, observations, 5)` with the run's frozen basis. Gate: fuel-level report texts exist, one per F5 observation, and the activated binding snapshot (`basis.snapshot_canonical`) holds a `fuel_level` binding for `fuel-level-sensor/fuel-level`. **No gateway process and no SQLite ledger** (no DB of any kind). Kobo's 0-row cause is now settled (§9.2) and is not re-investigated.

**Gates (each asserted; a failing gate stops the run):**
- **F0a** scenario of every run is weather and loads only (F0's `scenario_is_weather_and_loads_only` empty); the actions enter only through `apply_actions` on the frozen run; the kernel applies them or refuses (report verbatim).
- **F1** every run READY on the registered path through (c), and `run_to_end` completes.
- **F2** tank law per step, exactly: `tank[i+1] = tank[i] − E_i × SFC − removal_i + delivery_i`; Σ removal = 120 and Σ delivery = 300 exactly; report the removal's per-step litres.
- **F3** dispatch unaffected, as above (with actions vs without, both probe v7; and probe v7 vs v6 without actions). Every night's litres equal D0's 43.428 L (26057/600).
- **F4** no fuel-limited step.
- **F5** fuel-level observations at 15-min cadence on `registered-kobo-publication` v5; none with an instant in `[00:50, 02:20)` local of night 4; at least one in the 30 min before and the 30 min after; bias −0.5 L.
- **F6** as item 4.
- **F7** each per-day document below 4000 nodes; record the largest.
- **F8** `--check` byte-equal.
- **F9** both sources (true stock; F5 readings): night 4 `UNEXPLAINED` with gap > 0; every other night `WITHIN_MARGIN` with gap 0; none `NOT_ASSESSED`.
- **F10** D0 untouched (`T/probe_kisiwa_nights.py --check` prints "probe result current").
- **F11 (new) K0's setup bounds hold for the declared world:** for runs 2 and 4, initial stock + deliveries ≤ 1000 L and removal ≤ initial stock + earlier deliveries (§9.3 item 2). Report the numbers.

**Stops (report to the Architect; never design around them):**
- **S0 (OA-1)** the only way to move the tank or open the gap is a scenario entry. Never write one.
- **S1** a refusal on the registered path through (c): import, conversion, selection (`REGISTERED_BASIS_*`), `PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE`, `PUBLICATION_UNIT_MISMATCH`, a blocking reason, or a kernel refusal of an added cause. Report verbatim with file:line and the smallest fix. **Never fall back to Lab v3 or to a hand-built selection.**
- **S2** F2 or F3 fails.
- **S3** F9 differs from the expectation (report the night and its terms). Never change the removal size, times, materiality, accuracy, tolerances, cadence, dropout or seed.
- **S4** F5 fails with the probe-local v7 (the sample does not publish, or the gap does not silence). K1a pauses (§9.2).
- **S5** F7 over 4000 on a single day.
- **S6** a Kisiwa mapping has no Kobo binding to carry (item 1).
- **S7** F11 fails. Report; the Architect rules (the declared world is not changed).
- **S8** the re-issued work exceeds 0.75 unit.

**Files:** `T/probe_kisiwa_fuel.py` (edit: (c) setup, probe-local v7, F3/F6/F11 additions); new `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json`; `.agent/DIESEL-F0/probe-result.json` (new); `.agent/DIESEL-F0-probe-results.md`: keep the S1 stop section as "First attempt (stopped, aa49a18fd)" and add the re-run with the plain-words line of §8.3, the per-night table, gates, seconds per run and the probe-local-v7 line; `host/tests/test_probe_kisiwa_fuel_band.py` (L0, as §8.3, if not yet written).
- **Before running:** commit a short pre-registration addendum to the evidence file (the (c) path, the clocks, the bindings draft, the probe-local v7). No expectation changes.
- **Reading budget:** this §9; §8.3; `B/runs/registered_basis.py:49-170`; `B/runs/service.py:395-500`, `:740-790`, `:888-938`; `backend/tests/test_s2_registered_basis.py:1-100`; `backend/tests/test_s1_bindings.py:1-60`, `:140-160`; `backend/tests/test_s1_cutover.py:40-75`; `B/sites/foundation_service.py:100-130`, `:247-300`; `backend/conversions/kobo-001-bindings.json`; `S/packs/mini_grid.py:185-235`, `:1240-1257`; `S/packs/fuel.py:150-221`; `B/runs/profiles.py:1140-1165`, `:1354-1367`; `host/gateway_publication.py:60-105`.
- **Rules:** no DB (Postgres or SQLite), no prepare, no suite, no tick, no `-ExecutionPolicy`; never `assetops_demo3_full_test`. One fresh Opus reviewer re-runs both `--check`s, reads (c) against `test_s2_registered_basis.py`, and diffs the probe-local v7 against §9.2. **Merge on ACCEPT whatever the result.**

### 9.5 Revised sizes, order, lanes, totals and date

**Arithmetic correction to R2.** §8.4's unit rows sum to **15.25 remaining** (the rows are F0 0.5, K0 2.0, K1 1.25, K2 0.75, K3 1.5, K4 2.0, K5 1.0, K6 1.5, K7 2.25, K8 1.0, K9 1.0, contingency 0.5), not the 14.75 printed; the Kisiwa total with D0 was **15.75**, not 15.25. R2's "19.25 before DS-1" was therefore 19.75 on its own rows. The figures below use the rows.

| Unit | Size | Change | Depends on (merged) |
|---|---|---|---|
| D0 | 0.5 | spent | — |
| F0 (first attempt) | 0.5 | spent (stopped S1) | — |
| **F0r** | 0.5 | new (§9.4) | none (now) |
| K0 | **2.5** (2.0–3.25) | +0.5 (§9.3) | F0r; owner answered (Option A) |
| **K1a** mini-grid v7 | **0.5** (0.4–0.75) | new (§9.2) | none (now, parallel with F0r) |
| K1 | 1.25 | the "+0.25–0.5 publication profile" risk withdrawn; now uses v7 and promotes F0r's bindings draft | F0r, K1a, A1 |
| K2 | 0.75 | — | F0r |
| K3 | 1.5 | — | K1, K2 |
| K4 | 2.0 | — | K3; board/chain part after PV-1 |
| K5 | 1.0 | — | K3; panel after K4 |
| K6 | 1.5 | — | K4, MV-1, A2 |
| K7 | 2.25 | sets `operational_actions` on each Kisiwa run request (K0) and `model_profile` v7 (K1a) | K0, K1, K2; K6 for the freeze step |
| K8 | 1.0 | — | PV-1, A3, CH-5d1 (merged), K4; captures after K7 |
| K9 | 1.0 | — | all |
| Contingency | 0.5 | card round after F0r; K4 Finding-kind risk | |
| **Kisiwa remaining** | **16.25** (range 14.5–19.0) | +1.0 vs R2's corrected 15.25 after F0 spent (F0r +0.5, K0 +0.5, K1a +0.5, F0 −0.5 now spent) | |
| **Kisiwa total incl. spent** | **17.25** | | |

**Order (lane-units; about 3 units per lane-day including review):**
```
now (t=0):   MB-1 (lane 1) | A2 (lane 2) | F0r (lane 3) | K1a (lane 4, light, in parallel)
t≈0.5:       F0r result -> card round (contingency) | K1a merged
t≈0.55:      A2 merged -> K2 (lane 2, to ≈1.3)
t≈0.6:       K1 (lane 3, after F0r PASS and K1a; to ≈1.85)
t≈1.25:      MB-1 merged -> WD-1 -> PV-1 (lane 1, to ≈2.15)
t≈1.3:       K2 merged (0054) -> A3 (lane 2, after MB-1; to ≈2.0)
t≈1.85:      K1 merged -> K3 (lane 3, 0055; to ≈3.35)
t≈2.0:       A3 merged -> K0 (lane 2; to ≈4.5)
t≈2.15:      PV-1 merged -> lane 1 idle until K3 (the coordinator may pull backlog-free fix rounds here)
t≈3.35:      K3 merged -> K4 (lane 3, 0056; to ≈5.35) | K5 fuel page (lane 1; to ≈4.35)
t≈4.5:       K0 merged -> K7 data part (lane 2; to ≈6.25)
t≈5.35:      K4 merged -> K6 (lane 3, 0057; to ≈6.85) | K8 code (lane 1) | K5 Finding panel
t≈6.85:      K6 merged -> K7 freeze step and Kisiwa scratch prepare (≈7.35)
t≈7.35–7.6:  K8 captures -> merged
t≈7.6–8.6:   K9 (finish rows, guard, rehearsal prepare)
then:        DS-1 -> E1–E6
```
- If no fourth builder is available, K1a runs on lane 3 right after F0r (K1 then starts at ≈1.0 and the path grows by 0.4).
- **Critical path:** F0r 0.5 → K1 1.25 (K1a parallel) → K3 1.5 → K4 2.0 → K6 1.5 → K7 freeze 0.5 → K8 captures 0.25 → K9 1.0 ≈ **8.5–8.6 lane-units ≈ 2.9 working days** (≈ 9.0 if K1a is serial). K0 stays off the critical path with about 2.3 units of float (needed by t≈6.85).
- **Remaining before DS-1:** lanes 1–2 **3.75** (CH-5d1 merged; MB-1 1.25 + WD-1 0.15 + PV-1 0.75 + A2 0.55 + A3 0.7 + E3 allowance 0.35; the coordinator confirms A2's and MB-1's remainders) + Kisiwa **16.25** = **20.0** (R2 printed 19.25; on its own rows 19.75; less CH-5d1's 0.75 and F0's spent 0.5 that is 18.5; R3 adds +1.5).
- **Plan total:** ≈ 117.3 (FUEL-1) + 17.25 = **≈ 134.55** (R2 printed ≈ 132.55).
- **Demo date:** the critical path is about the same as R2's (8.5) when K1a runs in parallel, but it now starts half a unit later because F0's first attempt stopped. Net: **about +3.25 working days (range 2.75–5.25)** against the lanes-1–2 plan without Kisiwa, versus R2's +3 (2.5–5). The central figure is inside the owner's accepted "about +3 (range 2.5–5)" and inside the earlier "about 4–5". **The top of the range is now about a quarter-day over 5.** Tripwire: if, at any card round, the Kisiwa critical path re-plans above **9.75 lane-units** (the point where the central date passes +3.75 and the top passes about +5.5), the Architect stops the lane's next dispatch and the coordinator takes the cut options to the owner (first candidate: drop K6, the verification page, and end the DS-1 beat at the Action; about −1.75 units and −0.6 day).
- **E3:** unchanged (+25–35 min; E3 ≈ 1.3–1.5 h of the 3 h cap).

### 9.6 Plan HTML (`Docs/demo-sprint/client-demo-plan.html`) rows to change (the coordinator carries these on top of §8.9)

1. Build-units row "DIESEL-1-R2 …": becomes "DIESEL-1-R3 …", **17.25** (D0 0.5 and F0 0.5 spent, F0r 0.5, K0 2.5, K1a 0.5, K1 1.25, K2 0.75, K3 1.5, K4 2.0, K5 1.0, K6 1.5, K7 2.25, K8 1.0, K9 1.0, contingency 0.5). Note: "F0 stopped at run setup (no registered Site in memory) and found mini-grid never samples the tank; re-run on the real registered path with a new mini-grid v7 (Kisiwa only)".
2. Total row ≈ 134.55; G5/G6 +17.25 (DIESEL-1-R3) instead of R2's +15.25.
3. Lanes figure: K1a beside F0r; lane 3 F0r → K1 → K3 → K4 → K6 → K9; lane 2 A2 → K2 → A3 → K0 → K7; lane 1 MB-1 → WD-1 → PV-1 → K5 → K8.
4. Calendar line and OD-P9: G6 about +3.25 working days (range 2.75–5.25) against the plan without Kisiwa.
5. Rulings table: a "DIESEL-1-R3" row pointing to §9: (c) in-memory registered setup, mini-grid v7 for Kisiwa only (Kobo stays v6, 0 tank rows), K0 origin fields with the omit-when-scenario rule, records only through the Work API, R2 arithmetic corrected.
6. After-the-demo list: add "Kobo tank level (mini-grid v7 on Kobo)".

### 9.7 Owner questions

**None blocking.** The owner already chose the operational-action link (Option A); nothing here reopens it.

For the owner's information, in plain words:
- The first fuel trial stopped before measuring anything, for two technical reasons: the example site wasn't set up the way the real product sets up a site, and the simulated generator site never reported its tank level at all (that is also why Kobo shows no tank readings). We fix both: the trial re-runs on the real set-up path, and the simulated site gains the ability to report its tank level. Kobo keeps working exactly as it does today; only Kisiwa uses the new tank reading.
- Kisiwa now adds about **3¼ working days** before the demo, against about 3 before (range now 2¾ to 5¼, against 2½ to 5). The middle estimate is still inside what you accepted; the worst case is now about a quarter-day past your 5-day upper end. If the plan grows further, we will come back to you with a cut (most likely: skip the "after the fix" check page and end the Kisiwa story at the agreed action) before going over.

---

## 9a. Ruling DIESEL-1-R3a: F0r's S6 stop at conversion

- Architect: Claude, 2026-11-07. Binding unchanged (`.ai/ROLE_CONFIG.md:9`). F0r branch commits be4bbceb6, 3a147f96e, bf70fd180, 1ba54aa43 (`AssetOpsV1-f0`). This amends §9.4 item 1 only.
- Refusal, verbatim (`B/sites/binding_conversion.py:127-129`): "ConversionConflict: Legacy mappings ['battery-pcs-discharge-capability', 'generator-status', 'pv-inverter-available-power'] have no explicit conversion in the fixture." The stop was correct.
- **Cause:** Kisiwa's template has 12 legacy mappings (D0 draft `:326-372`). Kobo's conversion fixture (`V/kobo-001-bindings.json`, `minigrid-roles-1`) predates three of them. Kobo's import has no such mappings, so it bound `generator-controller/status` with `legacy_mapping_id: null` and gained the two capability channels later by republication (`V/kobo-001-s3-dispatch-demo-config.json` `bindings.add`, roles-2). Copying Kobo's history onto a Site whose template already has these mappings does not fit.

**Decision: fix (i), and it is the real K1 path too.** Kisiwa's conversion fixture converts **every** legacy mapping in its template, once, at import:
1. `role_set` = **`minigrid-roles-2`**: the set `B/sites/binding_roles.py:36` names as the default for a new MINIGRID publication, and the lowest one holding `pv_available_power` and `pcs_discharge_capability`.
2. `bindings` = 12 rows: the 9 F0r kept, plus:
   - `generator-status`: Kobo's status row (`V/kobo-001-bindings.json`, role `generator_state`, `state`→`state`, ENUM map STOPPED/STARTING/RUNNING/FAILED) **with `legacy_mapping_id: "generator-status"`**, not null (the template has the mapping; `plan_requests` checks the row matches it, `:95-101`);
   - `pv-inverter-available-power` and `battery-pcs-discharge-capability`: Kobo's two `add` rows from `V/kobo-001-s3-dispatch-demo-config.json` (roles `pv_available_power`, `pcs_discharge_capability`, kW→kW IDENTITY), each with its `legacy_mapping_id`.
3. `declare_signals` = **`[]`**. **The builder's judgement call is overruled.** Keeping Kobo's entry is harmless to the code (`B/sites/binding_service.py:507-522` returns no change for an already-declared signal with the same unit), but its `reason` ("Absent from the original Kobo import…") is false for Kisiwa, whose template declares the signal (`:289`). A fixture must state only true provenance. Set `note` to: "Converted from the imported Kisiwa Foundation's legacy signal_mappings; every template mapping converted once, under minigrid-roles-2 (DIESEL-1-R3a)."
- **Why not (ii):** republishing after conversion can't help, because conversion refuses first. Republication is only for channels the template does not have.
- **Why not (iii):** it changes D0's template, which §8.1 item 2 forbids.
- **Roles-3/4 stay a republication, as Kobo does.** The channels Kisiwa's template does not map (critical-load requested and delivered power, storage charge request, and the other roles-4 depth channels) stay for K1's `V/kisiwa-001-minigrid-roles-demo-config.json` through `B/sites/demo_configuration.py`, as §3.1 already says. F0r does **not** apply it, because none of its gates reads those channels. An unbound signal is not a reporting path (`B/runs/service.py:899-902`), so v5's resolutions for them are skipped. K1's registered-parity test proves the roles-4 step.
- **Kobo:** its fixtures and configs are not edited.

**F0r's other gates and stops stand unchanged** (§9.4: F0a–F11, S0–S8), with two additions:
- if the corrected fixture is refused again (a role, unit or conversion check), that is **S6**: report it verbatim, and never drop a mapping or edit the template;
- the evidence file records the 12-row fixture and the roles-2 choice in the pre-registration addendum before any run.
- The S8 cap (0.75 of re-issued work) stands; this fix is about 0.05.

**K1's size is unchanged at 1.25.** K1 promotes the corrected draft verbatim to `V/kisiwa-001-bindings.json`. It writes one roles-4 demo configuration for Kisiwa instead of replaying Kobo's three-step history (s3, s6, roles-4). That is no more work than §3.1 assumed. Totals and the date in §9.5 are unchanged.

---

## 9b. Ruling DIESEL-1-R3b: F0r result, F8, merge, next K units, setup clock

- Architect: Claude, 2026-11-07. Binding unchanged. F0r commits 0011ad361, 77ad11f17, 77958a20c, ab33768d7, 9e5fad4e1 on `task/DIESEL-F0-kisiwa-fuel-probe`. The result matches the pre-registration:
  - night 4 is UNEXPLAINED from both sources, [95.657, 144.343] L, with a 105-min gap (the builder's pre-run 105-min expectation, not the 90-min span);
  - every other night is WITHIN_MARGIN (±24.343 L; the delivery night ±27.343 L);
  - F0a, F1–F7, F9, F10 and F11 pass.
- Foundation selection v1 is correct: with R3a's `declare_signals: []` the conversion makes no joint Foundation revision.

**1. F8: seed the ids; F0 then closes PASS.**
- **The fix:** inside `T/probe_kisiwa_fuel.py` only, wrap the in-memory import and conversion in a context manager that replaces `uuid4` with a seeded generator: `random.Random(20260929)`, `uuid.UUID(int=rng.getrandbits(128), version=4)`.
  - Patch it at every name the store, the services and the conversion actually call (`uuid.uuid4` and any module-level `from uuid import uuid4` binding; the builder lists them in the evidence file).
  - Restore it on exit.
  - No product or `backend/tests/` file is edited.
- **Rejected: marking or omitting the ids as volatile.** The snapshot hash and the report key are part of what F6 proves, and a check that skips them cannot see a real regression in them.
- **Fallback:** if any id still varies after seeding, the builder stops and reports which one. Volatile marking is not a quiet alternative.
- **Who can apply it:** this is a Sonnet fix round.
- **Mechanical verification, by the coordinator, no reviewer judgement needed:**
  - (a) `--write`, then `--check` in a **fresh process**, prints "probe result current";
  - (b) a second fresh `--check` does the same;
  - (c) `git diff` of `probe-result.json` against 9e5fad4e1 changes only the id fields and the values derived from them (snapshot sha, report key and the ids listed). Every litre, band, state, gap, count and gate value is byte-equal;
  - (d) `T/probe_kisiwa_nights.py --check` still prints "probe result current".
- **Then F0 closes PASS**, with all gates F0a–F11 met.

**2. Merge: yes, as evidence-only, like D0.**
- The merge carries `T/probe_kisiwa_fuel.py`, `host/tests/test_probe_kisiwa_fuel_band.py`, `.agent/DIESEL-F0/` (the action-log draft, the bindings draft, the result JSON) and `.agent/DIESEL-F0-probe-results.md`. No product code.
- One fresh Opus reviewer runs §9.4's review: re-run both `--check`s, read (c) against `test_s2_registered_basis.py`, and diff the probe-local v7 against §9.2.
- The review starts once (1) verifies, and its finding goes in the same packet. Merge on ACCEPT.
- K0 promotes the action log later, and K1 promotes the bindings draft. Neither is moved now.

**3. K units: order and readiness**

| Order | Unit | Lane, start | Readiness |
|---|---|---|---|
| 1 | K1a | in build now | its card is §9.2 |
| 2 | **K1** Kisiwa Site (critical path) | lane 3, after F0 merges and K1a merges | **needs one consolidated card.** It is spread over §3.1, §8.4, §9.2 and §9a, and ROLE_CONFIG Token Efficiency item 5 requires one card. **The Architect writes it next (R3c)**, before K1a merges. |
| 3 | **K2** fuel records on the Work path (0054) | lane 2, after A2 merges | **needs a card**: the API body and refusal literals, the `fuel_records` read signature, migration 0054's exact CHECK and column, and the tests. §8.4 pins the decisions but not the literals. The Architect writes it in the same R3c round, after K1. |
| 4 | **K0** operational-action bridge | lane 2 after A3, or any lane that idles first (it has about 2.3 units of float) | **build-ready from §9.3 as its card**, with one pre-flight: the builder names the PRE-FLIGHT items (the contract reporting-condition class, every run store's render/parse, the harness constructor) and batches any questions before writing code. The Architect answers them within that pre-flight. No further card is needed. |

- Everything after these (K3 onward) keeps §9.5's order, and each gets its card at the round before it starts.

**4. The setup clock is confirmed: `2026-09-29T10:00:00Z`.**
- It falls after the 09:30 conversion, so the binding basis is recorded at setup, and before run 1 at `2026-10-01T12:00:00Z`.
- It is a probe-only constant and is recorded in the result JSON.
- R3 should have named it; this ruling fixes that omission.
- K1 and K7 use their own install and setup instants from the story calendar, never this one.

---

