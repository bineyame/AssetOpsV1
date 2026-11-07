# DIESEL-F0: Kisiwa fuel-events probe, evidence

Ruling: DIESEL-1-R2 §8.3 with §8.2a (`.agent/build-sheet-DIESEL-1.md`, dc72cb72a). Branch
`task/DIESEL-F0-kisiwa-fuel-probe`. In memory; no DB, no product code, no suite.

## Pre-registered expectation (committed before any run)

Committed together with the operational-action log `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml`,
before the probe tool was written or run. Restated from §8.3 verbatim in substance; nothing below is changed after a
result is seen.

- Declared world: §2.2 unchanged except start fuel **700 L** (run 1) and the operational actions; 10 day-runs
  15:00-15:00 local from `2026-10-01T12:00:00Z`, chained at full precision, stop 90 % throughout.
- Actions: delivery 300 L at 10:00 local closing night 2 (ticket 300 L); unrecorded removal 120 L over 45 min,
  01:00-01:45 local in night 4, sensor disconnected 00:50-02:20 local; dips at 07:00 local closing night 4 and at
  18:00 and 06:00 local in runs 6-10; seal and sensor-power fix at the run 6 start (no physical effect in v1).
- `fuel-balance-1` parameters exactly as §8.3 (a = 10 L, margin 2a, delivery tolerance 1 %, use band 9/10 loaded to
  11/10 (loaded + idle_h x 4.9), materiality 40 L, gap spans > 60 min).
- Architect's expectation (arithmetic): night use about 43.4 L, unchanged by the actions. Night 4 residual about
  **[95.7, 144.3] L, UNEXPLAINED**, gap > 0 (about 90 min of silence). Clean nights about [-24.3, +24.3] L,
  WITHIN_MARGIN. Night 2 (delivery) about [-27.3, +27.3] L, WITHIN_MARGIN. No night NOT_ASSESSED.
- Builder's expectation for F0a, written before running: the frozen run's causes and reporting-path conditions are
  read by `host/execution_adapter.py` `frozen_world_inputs` / `reporting_inputs` from the run alone, so causes and a
  reporting condition added with `dataclasses.replace` should be applied with no scenario entry. `FrozenCause` has no
  origin field, so the origin and content hash can only be carried in the cause's `event_id` and in
  `intervention_history` until K0 adds a field. The gap measured between readings is expected to be about 105 min
  (00:45 to 02:30 local readings around a 00:50-02:20 silence), not 90.

## F0r pre-registration addendum (DIESEL-1-R3 §9.4, b5b3e7f03; committed before any (c)-path code runs)

No expectation changes. The declared world, the parameters, the action log and the Architect's expectation are as
§8.3 and above.

- **Registered setup (c):**
  - `import_site` the Kisiwa record (D0 `kisiwa_site()`) into `InMemoryFoundationStore` at `2026-09-29T09:00:00Z`.
  - `convert` with `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json` at `2026-09-29T09:30:00Z`.
  - Real `RegisteredLabBasis(ImportedSiteRegistry(FoundationService(store, "demo", clock)))`; `knowledge_at` absent;
    `foundation_version` = the registered version the selection returns.
- **Bindings draft:** `backend/conversions/kobo-001-bindings.json` with `site_code` KISIWA-001, keeping every binding
  whose `legacy_mapping_id` is a mapping in Kisiwa's template (9 of Kobo's 10). Dropped: the generator
  `status` binding (`legacy_mapping_id` null, so not a Kisiwa mapping). Builder's note before running: Kisiwa's
  template has three mappings with no Kobo binding to carry (`pv-inverter-available-power`,
  `battery-pcs-discharge-capability`, `generator-status`). `plan_requests`
  (`backend/assetops_backend/sites/binding_conversion.py:127-129`) refuses unconverted legacy mappings, so S6 is
  expected at conversion. No binding is invented.
- **Probe-local mini-grid v7:** "Tank level from a probe-local mini-grid v7 identical in content to K1a's; product
  code has no v7 until K1a merges." Not built if conversion stops first.

## First attempt (stopped, aa49a18fd): STOPPED at run setup (S1 refusal on F1; S4 also certain by code reading)

No night was measured. No plain-words result line exists, there is no per-night table, and
`.agent/DIESEL-F0/probe-result.json` was not written. Nothing was changed after the stop: not the declared world,
the profile or the parameters.

### S1: the refusal, verbatim (run 1 setup, before any action was applied)

`tools/probe_kisiwa_fuel.py --write` at 8370a0689. `kisiwa_registered_draft` uses the ruling's
`registered-kobo-publication` v5 with D0's in-memory `FakeSites` Kisiwa site:

> assetops_backend.runs.refusals.RunSetupRefused: Publication profile 'registered-kobo-publication' at version 5
> states a simulated device resolution against registered binding source units, and site KISIWA-001 has no
> registered basis to check them against. No run was created.

- Raised at `backend/assetops_backend/runs/service.py:911-918` (`_freeze_signal_resolutions`, kind
  `PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE`).
- A registered profile states device resolutions (`REGISTERED_KOBO_RESOLUTION`, `runs/profiles.py:1841-1860`). It
  can only be selected for a Site with a registered Foundation and SignalBinding basis (`RegisteredLabBasis`). That
  basis is DB-backed (`host/tests/test_dd1a1_registered_kobo.py:64-86` builds it on Postgres). An in-memory Kisiwa
  has none.
- Smallest fixes, for the Architect to rule on (none was tried):
  - (a) Draft on a profile without resolutions (Lab v3, as D0 did). This changes a declared item in §8.3 F5.
  - (b) An in-memory registered basis for Kisiwa: a fake `RegisteredSiteSelection` or registry carrying Kobo's
    binding units, built in the probe. This needs a probe-side fixture and no product change. It is unverified.

### S4: certain even past the refusal (code reading; not run)

The `mini-grid` model publishes no tank level on ANY publication profile:

- `host/execution_adapter.py:734-739`: `reporting_inputs` drops every declared signal for which
  `model.reports(state_key, reading_class, unit)` is false.
- `simulator/assetops_simulator/kernel/model.py:396-400`: a `STATE_SIGNAL` is reported only when the model has a
  `STATE_SAMPLE` handler for the state.
- `simulator/assetops_simulator/packs/mini_grid.py:192-207`: `mini-grid` has only the `fuel-tank-volume-stock`
  STOCK handler (v2-v6 are `replace`s, `:1019`, `:1075`, `:1126`, `:1197`, `:1244`). The only fuel
  `STATE_SAMPLE` handler is `packs/fuel.py:207-212`, and only the minimal fuel model uses it.
- So `fuel-level-sensor/fuel-level` never enters `FrozenReportingInputs.signals`, and F5 would find 0 fuel-level
  observations. The readings source of F9 would then be NOT_ASSESSED (MISSING_OPENING) on every night, which is
  S3. This applies equally to D0's Lab v3 runs, matching §2.2's "No tank signal is published".
- `unconfigured_signals` (`execution_adapter.py:853-863`) applies the same filter, so the drop is silent.

### F6: why Kobo stores 0 `fuel_level` rows (code reading)

- **First stage that drops them: execution.** The model filter in `reporting_inputs` described under S4: mini-grid
  v1-v6 have no `STATE_SAMPLE` handler for `fuel-tank-volume`. Every other stage carries the signal:
  - profile: registered v1-v5 inherit Lab v3's declaration (`runs/profiles.py:1460-1478`, `:1855-1859`);
  - template: `config/site-templates/kobo-mini-grid-60kw.yaml:321-328` (device) and `:387-390`
    (`fuel-tank-level` mapping);
  - binding: `backend/assetops_backend/conversions/kobo-001-bindings.json:5`, `:23` (role `fuel_level`,
    `sites/binding_roles.py:102`);
  - acceptance: consumers exist at `mini_depth/inputs.py:141`, `:254` and `evidence/overview.py:80`.
- **Mapping:**
  - `gateway_mapping_for('registered-kobo-publication', 5)` falls back to `SIMULATOR_LAB_GATEWAY_MAPPINGS`
    (`simulator-lab-gateway-fuel` v1, which includes fuel-level; `simulator/.../gateway/mappings.py:40-56`,
    `:214`).
  - The registered path does not use it. `host/lab_execution.py:2803-2849` and `:2876-2893` send `DeviceReport`s
    to the gateway process, which maps them through the activated binding snapshot
    (`host/gateway_publication.py:72-184`).
- **K1 sizing consequence:** a tank level needs a `STATE_SAMPLE` handler for `fuel-tank-volume` in a new
  `mini-grid` version, which is a model change and a version bump. It does not need a mapping or binding change.

### F0a: code facts for K0 (code reading; the hook itself was not exercised because setup refused first)

- (i) **Provenance checks of a frozen cause against scenario entries: none.**
  - Kernel refusals are unrelated to the scenario: outside the interval (`kernel/execute.py:244-259`), no handler
    (`:721-730`) and no initial value (`:857-872`).
  - `SimulationRun.__post_init__` (`runs/models.py:976-1045`) checks only absent magnitudes.
  - Run parsing (`runs/parsing.py:1765-1786`) checks shape only.
  - `runs/provenance.py:434-459` and `:513-536` label every cause and condition "answered by SCENARIO". **K0 must
    extend this**, together with a cause-origin field: `FrozenCause` (`runs/models.py:572-619`) and
    `DeclaredCause` (`contracts/.../world_inputs.py:170-204`) have no origin field. The trajectory identity hash
    (`contracts/.../trajectory.py:570-589`, `:639-662`) hashes `event_id` and `intervention_history` as given.
- (ii) `reporting_inputs` takes an added `FrozenReportingPathCondition` with no scenario check
  (`execution_adapter.py:769-820`). It silently skips a condition the profile does not support.
  `fuel-level-reporting-availability` is supported (`runs/profiles.py:1444-1457`). But it silences a signal that
  mini-grid never emits (S4).
- (iii) Other mechanisms:
  - **M2** `OPERATOR_RECORD` (`scenarios/models.py:279`): no run, publication or gateway reader.
  - **M3** commandable states are only `generator-stop-soc-threshold` and `battery-reserve-state-of-charge`
    (`scenarios/models.py:255-258`). `issued_by` on anything else is refused at parse (`scenarios/parsing.py:783-802`).
    Registered v3+ has `record_channels=()` (`runs/profiles.py:1946`), and the registered path publishes
    measurements only (`host/lab_execution.py:2829-2835`).
  - **`intervention_history` readers:** `runs/provenance.py:743-746` (render), `runs/parsing.py:1281-1287` (parse;
    refuses only non-string or empty entries), `execution_adapter.py:347`, `trajectory.py:589`,
    `simulator_lab_api.py:2304`. None refuses a non-empty value.

### Gates

| Gate | Result |
|---|---|
| F0a | Not reached at run time. Scenario: D0 `day_document` unchanged. Code facts above |
| F1 | **FAIL**: run 1 refused at setup (S1) |
| F2, F3, F4, F7, F8, F9 | Not run |
| F5 | Not run; would fail (S4, code reading) |
| F6 | Code finding above (not a stop) |
| F10 | **PASS**: `tools/probe_kisiwa_nights.py --check` printed "probe result current (G6 pass)". No D0 file differs from main |

Seconds per run: none measured.

Stops: **S1** (fired). **S4** (certain by code; not run).
