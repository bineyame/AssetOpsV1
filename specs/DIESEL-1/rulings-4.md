## 9c. Ruling DIESEL-1-R3c: the K1 and K2 consolidated cards

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `840d5dade`, then `992847b72`, where F0 merged and its review sits at `.agent/review-F0.md`. F0r evidence read on `task/DIESEL-F0-kisiwa-fuel-probe` at `c77eb135f`. K1a read on `task/DIESEL-K1a-minigrid-v7` at `1a4d3b5c5`. A2 read on `task/FUEL-A2-trial-fuel-comparison` at `7a390ea66`.
- Owner decisions in force, verbatim:
  - `.agent/owner-kisiwa-scope-2026-11-07.md`: "Build it, with the action link (Recommended)".
  - `.agent/owner-scenario-data-2026-11-07.md`: "this is not true, these are injected through operational actions".
  - `.agent/owner-missing-fuel-2026-11-07.md`: "'Unexplained fuel', never 'theft'".
  - `.agent/owner-fuel-scope-2026-11-07.md`: "Generic 3.3 L/h, labelled (Recommended)". Kisiwa applies the same generic rule, so its rate is 4.9 L/h.
- **What this section does.** Each card below is the one current card for its unit. It replaces §3.1, the K1 and K2 rows of §8.4, the K1 row of §9.5 and the K1 notes in §9.2 and §9a. **Builders read only their card.** Paths use the header's short forms.
- Two code facts change §3.1 and §8.4. Both are folded into the cards:
  - **Signal resolution (§3.1 pre-flight (a)) is closed.** F0r ran `registered-kobo-publication` v5 on an imported Kisiwa with no refusal. The profile is not bound to `KOBO-001` by name.
  - **The registered-parity reference is now F0r, not D0.** D0 is dropped from the demo (§8.1). F0r's `.agent/DIESEL-F0/probe-result.json` is the reference. Its F3 already holds D0's 43.428 L per night.

### 9c.1 K1 card: the Kisiwa Site, 1.25 (range 1.0–1.5)

**Lane, start, branch.**
- Lane 3. K1 starts once **F0 (the F8 fix, evidence-only) and K1a have both merged**. It is on the critical path.
- Branch `task/DIESEL-K1-kisiwa-site`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k1`, from main after both merges.
- Opus does the first build and the first review.

**What K1 delivers.** `KISIWA-001` registered the way the demo prepare will register it: import, convert, demo configuration, supply uses, no-load fact, sensor accuracy and diesel price. It also proves, on Postgres, that the registered Site reproduces F0r's measured result exactly.
- K1 does **not** add Kisiwa to `T/demo_combined.py` (`SITES`, `SITE_CODE`). It does not run a story day, a scenario calendar or a prepare. Those belong to K7.
- So no client screen of the demo DB changes when K1 merges.

**Files (all new unless marked edit):**

| # | File | Content |
|---|---|---|
| 1 | `C/site-templates/kisiwa-diesel-hybrid-60kw.yaml` | `.agent/DIESEL-D0/kisiwa-diesel-hybrid-60kw.draft.yaml`, **every byte from `template_id:` (line 23) to the end unchanged**. Only lines 1–21 (the DRAFT comment) are replaced by a shipped-template header (literal below). Parsed content therefore equals the draft. |
| 2 | `backend/tests/test_site_template_fingerprints.py` (edit) | One pin: `("kisiwa-diesel-hybrid-60kw", 1): ("013c3bbc9c9fcf6897eab6eb3d811637c606ee980feb06e53730f9903d4ca07c")`. The Architect computed it with `content_fingerprint` on the draft. |
| 3 | `backend/tests/test_site_template_catalog.py` (edit) | The shipped listing becomes `["hybrid-mini-grid-100kw", "kisiwa-diesel-hybrid-60kw", "kobo-mini-grid-60kw", "twin-tank-mini-grid-150kw"]`, with one comment line: "Four since DIESEL-1 K1: the Kisiwa diesel-hybrid island archetype." |
| 4 | `backend/tests/fixtures/s1/kisiwa-001.yaml` | The import record, as `B/tests/fixtures/s1/kobo-001.yaml` is for Kobo. It is exactly `yaml.safe_dump(render_site_document(record), sort_keys=True)`, where `record` = `site_from_template(<file 1>, site_id="KISIWA-001", display_name="Kisiwa island mini-grid", timezone="Africa/Dar_es_Salaam")` with `foundation.valid_from = "2026-09-01T00:00:00Z"`. That is F0r's `register_kisiwa` payload, with the shipped template in place of the draft. |
| 5 | `V/kisiwa-001-bindings.json` | `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json`, **byte-equal**: 12 rows, `minigrid-roles-2`, `declare_signals: []`, the R3a note. |
| 6 | `V/kisiwa-001-minigrid-roles-demo-config.json` | The roles-4 demo configuration (literal below). |
| 7 | `B/sites/models.py` (edit) | The sensor-accuracy vocabulary (below). |
| 8 | `T/demo_combined_kisiwa.py` | The registration flow (below). |
| 9 | `host/tests/kisiwa.py` | The registered Kisiwa drafter (below). |
| 10 | `backend/tests/test_k1_kisiwa_fixtures.py` | L0 tests, no DB. |
| 11 | `backend/tests/test_k1_kisiwa_site_postgres.py` | L2 on own `assetops_k1_test`. |
| 12 | `host/tests/test_k1_registered_kisiwa.py` | L2 registered parity on own `assetops_k1_test`. |

**Shipped-template header (file 1, lines 1–n, literal):**
```
# Shipped Site configuration template. Read-only at runtime.
#
# The Kisiwa diesel-hybrid island archetype (DIESEL-1 §2.2, promoted by K1,
# DIESEL-1-R3c): a small PV array behind one inverter, one battery behind one
# power conversion system, and a 60 kW diesel generator with its 1000 L tank
# that carries the night and charges the battery while it runs ("cycle
# charging": source priority PV, generator, battery). Three separately metered
# loads: households, a cold store for ice and fish, and a water pump.
#
# Component, device, signal and mapping ids are Kobo's, unchanged: the
# dispatch analytic reads Kobo's device ids by name. Display names, ratings,
# property values and Site Controls carry what differs.
#
# The numbers are DEMONSTRATION values, fixed before the D0 probe ran and
# never tuned: plausible for a small island mini-grid, not a recommendation
# for any real installation and not calibrated to one.
#
# Everything here is component truth about the template and never evidence.
# Templates copy; they never migrate an existing Site.
```

**Foundation vocabulary (file 7), following A1's pattern:**
- In `COMPONENT_PROPERTY_DEFINITIONS`, after the A1 entries, with the comment `# DIESEL-1 K1 (R3c): the tank level sensor's declared accuracy, read by fuel-balance-1 (K3) as the margin term a.`:
  - `"fuel-level-sensor-accuracy": PropertyDefinition(unit="L", kind="PHYSICAL", display_name="Fuel level sensor accuracy")`;
  - `"fuel-level-sensor-accuracy-basis": PropertyDefinition(unit="state", kind="PHYSICAL", display_name="Fuel level sensor accuracy basis")`.
- Add `STATE_PROPERTY_VALUES["fuel-level-sensor-accuracy-basis"] = frozenset({"GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_CALIBRATION"})`.
- Add both keys to `MINIGRID_PROPERTY_CARRIERS` with carrier `"FUEL_TANK"`, comment `# DIESEL-1 K1`.
- Add `"fuel-level-sensor-accuracy"` to `MINIGRID_STRICTLY_POSITIVE_PROPERTIES`. An accuracy of 0 L would claim a perfect sensor.
- `minigrid_foundation.py` needs no edit; it reads both tables.

**Roles-4 demo configuration (file 6, literal):**
```json
{
  "schema": {"id": "assetops.demo-configuration", "version": 1},
  "status": "SIMULATED DEMO CONFIGURATION - DIESEL-1-R3c (K1). Not operator-entered Site truth.",
  "label": "kisiwa-minigrid-roles-4-demo-config-v1",
  "site_code": "KISIWA-001",
  "component_properties": {
    "effective_from": "2026-09-29T09:57:00Z",
    "asset_code": "fuel-tank",
    "note": "Generic level-sensor accuracy, about 1 % of a 1000 L tank; not this sensor's calibration.",
    "properties": [
      {"property_key": "fuel-level-sensor-accuracy", "value": 10, "unit": "L", "source": "SITE", "source_version": 1},
      {"property_key": "fuel-level-sensor-accuracy-basis", "value": "GENERIC_DEFAULT", "unit": "state", "source": "SITE", "source_version": 1}
    ]
  },
  "bindings": {
    "effective_from": "2026-09-29T09:57:00Z",
    "role_set": "minigrid-roles-4",
    "note": "DIESEL-1-R3c K1 simulated demo configuration (kisiwa-minigrid-roles-4-demo-config-v1): every binding converted at import carried unchanged (12 rows, minigrid-roles-2), plus the cold store's (load-clinic, first in critical-load-priority) simulated requested and delivered power and the battery converter's charge request (registered-kobo-publication v5, mini-grid v7).",
    "declare_signals": [
      {"device_id": "clinic-meter", "signal_id": "requested-power", "display_name": "Cold store requested power (simulated critical load)", "unit": "kW"},
      {"device_id": "clinic-meter", "signal_id": "delivered-power", "display_name": "Cold store delivered power (simulated critical load)", "unit": "kW"},
      {"device_id": "battery-pcs-controller", "signal_id": "charge-requested-power", "display_name": "Battery charge requested power (simulated)", "unit": "kW"}
    ],
    "add": [
      {"device_id": "clinic-meter", "signal_id": "requested-power", "asset_code": "load-clinic", "role": "critical_load_requested_power", "source_unit": "kW", "canonical_unit": "kW", "conversion": {"kind": "IDENTITY", "parameters": {}}},
      {"device_id": "clinic-meter", "signal_id": "delivered-power", "asset_code": "load-clinic", "role": "critical_load_delivered_power", "source_unit": "kW", "canonical_unit": "kW", "conversion": {"kind": "IDENTITY", "parameters": {}}},
      {"device_id": "battery-pcs-controller", "signal_id": "charge-requested-power", "asset_code": "battery", "role": "storage_charge_requested_power", "source_unit": "kW", "canonical_unit": "kW", "conversion": {"kind": "IDENTITY", "parameters": {}}}
    ]
  }
}
```
- **Why the `component_properties` block is the sensor accuracy.** `apply_demo_configuration` requires the block (`B/sites/demo_configuration.py:49` `FIXTURE_KEYS`), and the tank is the one Kisiwa fact the roles-4 step needs. Both `effective_from` values are rewritten by the tool (Kobo's pattern, `T/demo_combined_kobo.py:112-116`).
- **Kobo's D-W1-3 margins are not declared at Kisiwa.** These are `pv-available-uncertainty` 3 kW and `renewable-retained-margin` 5 kW. They are Kobo's values for the mill's midday spare-solar check, Kisiwa has no productive load, and there is no basis for a Kisiwa figure. The midday check therefore reads its existing "not declared" state there. Pre-flight (c) confirms that this state exists.
- **Signals the template lacks.** The template declares none of the three added signals, so they are declared here with Kisiwa names. Kobo's configs name them "Clinic …", which is false for a cold store.

**Registration flow (`T/demo_combined_kisiwa.py`).** Modelled on `T/demo_combined_kobo.py:62-149`, `:385-408`. K7 later adds the story part to this file; K1 writes only the part below.
- Constants:
  - `SITE_CODE = "KISIWA-001"`;
  - `SITE_SOURCE = <file 4>`, `BINDINGS = <file 5>`, `ROLES4 = <file 6>`;
  - `CONFIG_OFFSETS = {"uses": timedelta(minutes=25), "roles4": timedelta(minutes=27), "known": timedelta(minutes=30), "price": timedelta(hours=1)}`;
  - `SUPPLY_USES = {"load-clinic": "ESSENTIAL_SERVICE", "load-res": "HOUSEHOLD", "load-mill": "HOUSEHOLD"}` (§2.2);
  - `NO_LOAD = [{"property_key": "generator-no-load-fuel-rate", "value": 4.9, "unit": "L/h", "source": "SITE", "source_version": 1}, {"property_key": "generator-no-load-fuel-rate-basis", "value": "GENERIC_DEFAULT", "unit": "state", "source": "SITE", "source_version": 1}]`;
  - `NO_LOAD_NOTE = "Generic no-load fuel rate for a 60 kW diesel set (common design-software default, about 0.08 L/h per kW of rating); not this generator's datasheet. Owner decision 2026-11-07 (generic, labelled)."`;
  - **the model pin:** `RUN_PROFILE = {"model_profile": {"profile_id": "mini-grid", "profile_version": 7}, "publication_profile": {"profile_id": "registered-kobo-publication", "profile_version": 5}, "timestep_minutes": 5, "seed": 20260929}`. Kisiwa runs only on v7 (K1a). Kobo stays on v6, through `V/d-verification-window-v3.json`, which is not edited.
- `register_in(store, import_at, install_at) -> dict`. It is store-agnostic: Postgres in the prepare and L2, `InMemoryFoundationStore` in L0. Steps, in order:
  1. `import_site(store, tenant_slug="demo", configured_tenant_slug="demo", source=ImportSource(path="var/sites/kisiwa-001.yaml", sha256=<sha256 of file 4's bytes>, record=read_import_source(file 4).record), legacy_documents=(), clock=Clock(import_at))` (`B/sites/foundation_service.py:247`).
  2. `convert(store, BindingService(store, Clock(install_at)), tenant, site, BINDINGS)`.
  3. Using `FoundationService(store, "demo", Clock(install_at + known))` and `BindingService(store, same clock)`:
     - (a) `declare_supply_uses`: one `publish_component_properties` per load at `install_at + uses`, note "Demonstration supply use declared at commissioning" (Kobo's literal);
     - (b) `declare_no_load_rate`: one publish on `generator` at `install_at + uses`, properties `NO_LOAD`, note `NO_LOAD_NOTE`;
     - (c) `configure_roles4`: deep-copy `ROLES4`, set both `effective_from` to `install_at + roles4`, assert the status prefix, then `apply_demo_configuration`, and assert `periods[-1]["role_set"] == "minigrid-roles-4"`.
  4. Return `{"site_code", "tenant_id", "site_id", "import_at", "install_at", "supply_uses_effective_from", "no_load_effective_from", "roles4_effective_from", "recorded_at", "periods"}`.
- `register(url, work, import_at, install_at) -> dict`. Postgres only:
  - `register_in(PostgresFoundationStore(url), …)`;
  - the same `UPDATE gateway/source SET disabled_at = NULL WHERE site_id = :s` as Kobo (`:405-407`);
  - **diesel price v1 only**: `publish(["fixture", "--site", "KISIWA-001", "--file", <V/demo-diesel-price-publications.json>, "--step", "v1"])` through `PostgresAssumptionStore(url, test_recorded_clock_override=lambda: install_at + price)`;
  - no productive-use price (Kisiwa has no productive load);
  - write `<work>/kisiwa-register.json`.
- CLI: `python tools/demo_combined_kisiwa.py register <database-url> <work> <import-at ISO> <install-at ISO>`.
- The no-load and the accuracy facts are Site-declared data. Their "generic" label travels in the basis property, never in product copy (A1's rule).

**The registered drafter (`host/tests/kisiwa.py`):**
- `class KisiwaRegistered`, constructed as `KisiwaRegistered(store, setup_at: str)`. It has the attribute and method surface that `T/probe_kisiwa_fuel.py` `build()`, `execute_day()` and `readings()` use from `Registered`:
  - `.store`;
  - `.basis = RegisteredLabBasis(ImportedSiteRegistry(FoundationService(store, "demo", Clock(setup_at))))`;
  - `.foundation_version`, from `basis.select("KISIWA-001", start_time=run 1 start, end_time=+1 day, knowledge_at=None)`;
  - `.v7_sim = assetops_simulator.packs.mini_grid.MINI_GRID_V7_MODEL` and `.v7_profile = B.runs.profiles.MINI_GRID_V7_MODEL` (**K1a's product v7, not the probe-local copy**);
  - `.draft(document, start, end, model="v7")`: the same `RunSetupService` call as the probe's `Registered.draft` (`T/probe_kisiwa_fuel.py:325-347`), with product v7 or v6;
  - `.sim(model)`.
- `def draft_day(store, document, start, end, setup_at)`: a convenience wrapper for the L2 site test.

**Registered parity (`host/tests/test_k1_registered_kisiwa.py`, L2, `assetops_k1_test`):**
- Module fixture:
  - `pg_harness.fresh_database()`;
  - `register_in(PostgresFoundationStore(URL), import_at=2026-09-29T09:00:00Z, install_at=2026-09-29T09:30:00Z)` (F0r's clock: import 09:00, conversion 09:30);
  - setup clock `"2026-09-29T11:00:00Z"`, after everything is recorded at 10:00.
- Test `test_f0r_reproduces_on_the_registered_site`:
  - `monkeypatch.setattr(probe, "Registered", lambda: KisiwaRegistered(store, "2026-09-29T11:00:00Z"))`, then `result = probe.build()`. **`T/probe_kisiwa_fuel.py` is not edited.**
  - Load the committed `.agent/DIESEL-F0/probe-result.json` as `ref`.
  - Assert `result == ref` after removing, from both, **only**:
    - `assumptions.model` and `assumptions.probe_local_v7` (product v7 replaces the probe copy);
    - `assumptions.registered_path` (foundation and binding-set version, snapshot, selection and clocks differ by design);
    - `gates.F6.example_fuel_level_report_text` (its key hashes the run id and snapshot).
  - From `gates.F6.snapshot_fuel_level_binding`, keep only `role`, `source_unit`, `canonical_unit` and `conversion`, and compare those.
  - Everything else must be equal, every litre, band, state, gap, dip, count and gate value included. That covers `runs` (scenario sha, intervention history, start and end states), `night4_tank_account`, `nights`, `dips`, and gates F0a–F5, F7, F9 and F11.
  - Print the removed keys' two values for the packet.
- Why this is the right check: F0r ran on Foundation v1 with roles-2. K1 adds the supply uses, the no-load fact, the accuracy and roles-4. None of these may change physics or the tank publication. Dropout is keyed per signal (`S/observation/transform.py:189-200`), so the added roles-4 signals cannot move a fuel-level dropout.

**L0 tests (`backend/tests/test_k1_kisiwa_fixtures.py`, no DB):**
1. The shipped template parses through the catalog. Its parsed document equals the draft's parsed document. Its bytes from `template_id:` onward equal the draft's.
2. File 5 is byte-equal to `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json`.
3. File 4 is byte-equal to the render described in the files table.
4. File 6 checks:
   - its keys are exactly `FIXTURE_KEYS`, its status starts "SIMULATED DEMO CONFIGURATION", `site_code` is KISIWA-001 and `role_set` is roles-4;
   - each `add` role is in roles-4's vocabulary (`B/sites/binding_roles.py`);
   - no `display_name` or `note` contains "Clinic", "clinic ", "mill", "Mill" or "Kobo" (case-sensitive except as listed). The device id `clinic-meter` is an id, not copy, and is exempt.
5. The vocabulary:
   - 10 L accepted on FUEL_TANK and refused on GENERATOR (carrier);
   - 0 L refused (strictly positive);
   - basis `SITE_CALIBRATION` accepted and `SITE_TEST` refused;
   - `L/h` refused for the accuracy (unit).
6. `register_in` on `InMemoryFoundationStore` (F0r's precedent, `backend/tests/foundation_fakes.py`) at import 2026-09-29T09:00Z and install 09:30Z. At 2026-10-01T12:00Z, as known at 10:00Z:
   - `fuel-tank` declares 10 L and GENERIC_DEFAULT;
   - `generator` declares 4.9 L/h and GENERIC_DEFAULT, and keeps every template property;
   - the three loads carry their supply uses;
   - the binding set is roles-4 with 15 bindings (12 + 3).
   - If the in-memory store cannot run `apply_demo_configuration`, this item moves to L2 unchanged (no stop).
7. `RUN_PROFILE`'s model `("mini-grid", 7)` is in `host/execution_adapter.py` `EXECUTABLE_MODELS` and in `MODEL_PROFILES`, and `V/d-verification-window-v3.json` still pins mini-grid 6.

**L2 site test (`backend/tests/test_k1_kisiwa_site_postgres.py`, `assetops_k1_test`):**
- `register(url, tmp, import 2026-09-29T09:00Z, install 09:30Z)`. Then:
  - the three Foundation facts and the supply uses, as known at install + 30 min;
  - the diesel price v1 (1.25 USD/L) known at install + 1 h through the assumption read the cost path uses (PRE-FLIGHT names it; `select_window_price` or its store);
  - binding set roles-4.
- **One Kisiwa day end to end.** F0r run 1 is 2026-10-01T12:00Z to 2026-10-02T12:00Z, `probe_kisiwa_nights.day_document(probe_kisiwa_fuel.START_SOC, probe_kisiwa_fuel.START_FUEL)`, with no actions.
  - Draft it through `draft_day` (READY, registered basis frozen, v7/v5).
  - Publish and accept it with `test_s6_verification_replay._publish_and_accept` (real gateway, S2 at `received_at` = 2026-10-02T12:10Z).
  - Run S3 assess and S4 match with `LabRunner` at +5 min.
  - Assert:
    - accepted `fuel_level` records exist for KISIWA-001: the first tank readings the product has stored;
    - the dispatch assessment for the window exists with no refusal (same device ids);
    - the Site outcome board read for KISIWA-001 returns 200 (PRE-FLIGHT names the call), and every row's state is a member of its existing state set.
  - Print every served board string for pre-flight (c) and (b).
- Rough machine time: one 24 h run through the gateway, about 3–5 min.

**PRE-FLIGHT (no code first; batch every question in one message):**
- (a) Closed by F0r (see the top of §9c).
- (b) Strings that name "clinic", "mill" or "Kobo" on a Kisiwa screen by device or component id instead of the Site's display name. The Architect's grep finds:
  - server: `B/evidence/overview.py:71-75` `SERVICE_FEEDERS` ("Clinic feeder", "Mill feeder");
  - UI: `F/sites/MiniPerformance.tsx:971` `CLINIC_FEEDER_LABEL` and `F/sites/SiteWindowOverview.tsx:484` (the "residential, clinic and productive loads" objective).
  - Rule: **K1 fixes a server string only if the Site's display names are already an input of that read.** Otherwise, and for every UI string, K1 lists it with file:line in its packet as a finding for **K8**, which the Architect sizes at K8's card round.
  - `SERVICE_FEEDERS` has no Foundation input, so it goes to K8. **No Kobo byte changes in K1.**
- (c) Every board row without a PRODUCTIVE load (Grow sales, the mill's midday check, Kobo's D-W1-3 margins) must read an existing honest state at Kisiwa. A row that needs new text is a **stop**.
- (d) Name the in-memory store's support for `publish_component_properties` and `apply_demo_configuration` (decides L0 item 6), and the board and price read calls.

**Client wording.**
- K1 adds no served copy and no UI string. Its client-visible strings are Site data:
  - the Site name "Kisiwa island mini-grid";
  - the template's component display names ("Households", "Cold store (ice and fish)", "Water pump", "Generator fuel tank" …);
  - the property display names "Fuel level sensor accuracy" and "Fuel level sensor accuracy basis";
  - the three declared signal names above;
  - the two notes.
- None says theft, stolen, stole, siphon or pilfer (H4).
- **MOCK DEVIATION MD-KIS-K1-1.** On Kisiwa's pages, the load names and roles come from Kisiwa's Foundation, not from v69's Kobo-like text. Examples: `frontend/mockups/v69/index.html:420` "Clinic feeder", "Grain mill · productive", and `:619`. Layout and components are unchanged; only data differs. Kisiwa reaches a client screen only after K7, and the four-Site estate screens are K8's.

**Guards and checks.**
- `tools\check-all.ps1`, `tools\check-architecture.ps1`, `tools\check-agent-workflow.ps1` and `tools\check-navigation-truthfulness.ps1`, run directly with no `-ExecutionPolicy`.
- `T/probe_kisiwa_fuel.py --check` and `T/probe_kisiwa_nights.py --check` must still print "probe result current".
- **Localised tests only** (no full suite in the sprint):
  - the three new files;
  - `test_site_template_fingerprints.py`, `test_site_template_catalog.py`;
  - `test_s1_bindings.py`, `test_s2_registered_basis.py`;
  - the A1 vocabulary tests (`test_fuel_cost_v2.py` parser part);
  - `test_scenario_execution_contract.py`, `test_execution_contract_alignment.py` (vocabulary must not move a digest);
  - `host/tests/test_mini_grid_v7.py`.

**DB.** Only `assetops_k1_test`, created by `pg_harness`. Never `assetops_demo3_full_test` or any other DB. No prepare, no tick, no `serve`.

**Stops (report to the Architect; never design around them):**
- any Kobo, Cold or EV byte change (templates, fixtures, configs, digests, served bytes);
- the vocabulary addition moves a scenario, run-contract or handover digest;
- a refusal anywhere in the registration flow (import, convert, a publish, the demo configuration, the price): report it verbatim with file:line and never edit the template, the bindings or a value;
- **the parity test finds any difference** outside the removed keys: report the key and both values, and never edit `probe-result.json` or the probe;
- a board row at Kisiwa needs new text (pre-flight (c));
- a migration would be needed;
- more than 1.5 units.

**Size 1.25:**
- template, pin and catalog 0.1;
- import record and render check 0.1;
- vocabulary and parser tests 0.15;
- bindings promotion and roles-4 config 0.1;
- `register_in` / `register` 0.3;
- drafter and parity test 0.25;
- L2 site test 0.2;
- pre-flight inventory 0.05.

**Reading budget:** this §9c.1; §2.2 (the table only); `T/demo_combined_kobo.py:30-150`, `:385-410`; `host/tests/test_dd1a1_registered_kobo.py:1-100`; `T/probe_kisiwa_fuel.py:240-450`, `:482-520`; `B/sites/demo_configuration.py:80-215`; `B/sites/models.py:255-340`; `backend/tests/test_s1_bindings_postgres.py:35-110`; `backend/tests/test_s6_verification_replay.py` (`_draft`, `_publish_and_accept`, `LabRunner` only); the K1a diff for the v7 names.

### 9c.2 K2 card: fuel delivery and tank dip records on Work operational records, 0.75 (range 0.6–1.0)

**Lane, start, branch.**
- Lane 2, after **A2 merges**. Branch `task/DIESEL-K2-fuel-records`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k2`, from main after A2's merge.
- Opus does the first build and the first review.

**No conflict with A2, checked against A2's branch diff (`7a390ea66`).** A2 edits:
- `B/actions/` (`verification.py`, `verification_rules.py`, the Postgres action store);
- `B/financials/trial_fuel_comparison.py`, `B/outcomes/credit.py`, `B/estate/portfolio.py`, `B/site_outcomes/board.py`;
- `F/estate/estateClient.ts` and its tests.

A2 adds no migration. K2 touches none of those files. K0 (later on lane 2) and K1 (lane 3) do not touch `B/work/`. **K2 owns migration 0054.**

**What K2 delivers.**
- Two new Work operational record kinds, `FUEL_DELIVERY` and `TANK_DIP`, posted through the existing route `POST /api/sites/{site_code}/work/operational-records` (`B/work_api.py:185-189`). Each carries a tank link, `asset_id`.
- An as-known read, `fuel_records`, for K3.
- Plain labels for the two kinds on the existing records screens.
- **Unchanged:** the four existing kinds, their command hashes, responses and rows. The contract's `OPERATIONAL_RECORD_KINDS` (`contracts/…/source_envelope.py:126`) and the run path are untouched.

**API body (closed shape).**
- `OPERATIONAL_KEYS` (required) is unchanged.
- The optional keys become `OPERATIONAL_CORRECTION + ("asset_id",)`.
- `OPERATIONAL_KINDS = ("OPERATOR_LOG", "MANUAL_READING", "SHIFT_NOTE", "SITE_VISIT", "FUEL_DELIVERY", "TANK_DIP")`, and `FUEL_KINDS = ("FUEL_DELIVERY", "TANK_DIP")` in `B/work/service.py`.

Examples. K7's injector uses these body sentences verbatim, filled from the action log and the handover file:
```json
{"kind": "FUEL_DELIVERY",
 "body": "Fuel delivery of 300 L received, ticket KIS-DT-0001.",
 "occurred_at": "2026-10-03T07:00:00Z", "period_end": null,
 "unit": "L", "quantity": "300",
 "source_document_sha256": "<64 lowercase hex: sha256 of the delivery ticket document>",
 "case_id": null, "asset_id": "<the Site's fuel-tank asset id>",
 "actor": {"kind": "SERVICE", "id": "<principal>", "attestation": "service=<principal>;job=<job>;rule=<rule>"},
 "idempotency_key": "kisiwa-kis-delivery-1"}
```
```json
{"kind": "TANK_DIP", "body": "Tank dip at the 07:00 round: 706 L.",
 "occurred_at": "2026-10-05T04:00:00Z", "period_end": null, "unit": "L", "quantity": "706",
 "source_document_sha256": null, "case_id": null, "asset_id": "<fuel-tank asset id>",
 "actor": {...}, "idempotency_key": "kisiwa-kis-dip-n4-0700"}
```
- `occurred_at` is when the delivery or dip happened. The record's `recorded_at` is the command's DB instant: K7 sets it through the existing test-only `test_db_clock_override` seam (`B/work/adapters/postgres_work_store.py:281-285`), recording the ticket 30 min after delivery (§8.2a).
- The existing 30-day backdate limit and the 5-minute future slack (`B/work/model.py:36-37`) apply unchanged.

**Validation, in this order. The existing steps are unchanged; the new ones are marked NEW:**
1. Gate; closed shape; actor; correction triple; `kind ∈ OPERATIONAL_KINDS` (else `WORK_INPUT_INVALID`); instants; quantity, unit and digest shapes; the existing check `(quantity is None) != (unit is None)` or MANUAL_READING without a quantity or `period_end < occurred_at` → `WORK_INPUT_INVALID`.
2. NEW, before the transaction:
   - a fuel kind without the `asset_id` key, or with null → `WORK_RECORD_ASSET_REQUIRED`;
   - a non-fuel kind with the `asset_id` key present (even null) → `WORK_RECORD_ASSET_NOT_ALLOWED`;
   - a fuel kind with `period_end` not null → `WORK_INPUT_INVALID` (both are instants);
   - a fuel kind with `quantity` null or `unit != "L"`, or a `FUEL_DELIVERY` with quantity 0 → `WORK_RECORD_QUANTITY_INVALID` (a dip may be 0 L);
   - a `FUEL_DELIVERY` with `source_document_sha256` null → `WORK_RECORD_TICKET_REQUIRED`;
   - `asset_id` not a UUID → `WORK_INPUT_INVALID` (`m.uuid_text`).
3. In the transaction, the existing order: an idempotent retry (200 or `WORK_EVENT_DUPLICATE_KEY`); `check_occurrence`; the case scope. Then NEW: `tx.asset_type(asset_id)` is None → `WORK_LINK_SCOPE_INVALID` (the existing code for a foreign or unknown asset); a value other than `"FUEL_TANK"` → `WORK_RECORD_ASSET_NOT_TANK`. Then the correction successor and the insert.
- **Canonical hash: byte-equal for the four existing kinds.** `canon["asset_id"] = m.uuid_text(body["asset_id"])` is added **only for a fuel kind**. The key is absent otherwise, so every existing `payload_sha256` and idempotency result is unchanged.
- The insert passes `asset_id` (None for the other kinds).
- The response `operational-record-1` is **unchanged** (no new field).

**Refusal codes (add to `B/work/model.py` `MESSAGES` and `STATUS`, all 422):**

| Code | Message (literal) |
|---|---|
| `WORK_RECORD_ASSET_REQUIRED` | "A fuel delivery or tank dip must name the fuel tank it concerns." |
| `WORK_RECORD_ASSET_NOT_ALLOWED` | "Only a fuel delivery or tank dip names a tank; other record kinds carry no asset." |
| `WORK_RECORD_ASSET_NOT_TANK` | "The named asset is not a fuel tank at this Site." |
| `WORK_RECORD_QUANTITY_INVALID` | "A fuel delivery needs a volume above 0 L, and a tank dip a volume of 0 L or more, in L." |
| `WORK_RECORD_TICKET_REQUIRED` | "A fuel delivery needs the SHA-256 of its delivery ticket." |

**Store (`B/work/adapters/postgres_work_store.py`):**
- `_Tx.asset_type(asset_id) -> str | None`, using `SELECT asset_type FROM asset WHERE tenant_id = :t AND site_id = :s AND id = :a AND retired_at IS NULL`.
- `insert_operational_record` gains the `asset_id` column and parameter.

**Migration `backend/migrations/versions/0054_operational_fuel_records.py`:**
- `revision = "0054_operational_fuel_records"`, `down_revision = "0053_fuel_cost_2"`.
- The constraint name `operational_record_kind_check` was confirmed by a read-only `pg_constraint` query on `assetops_test`.
```sql
ALTER TABLE operational_record DROP CONSTRAINT operational_record_kind_check;
ALTER TABLE operational_record ADD CONSTRAINT operational_record_kind_check
    CHECK (kind IN ('OPERATOR_LOG','MANUAL_READING','SHIFT_NOTE','SITE_VISIT','FUEL_DELIVERY','TANK_DIP'));
ALTER TABLE operational_record ADD COLUMN asset_id uuid NULL;
ALTER TABLE operational_record ADD CONSTRAINT operational_record_asset_fk
    FOREIGN KEY (tenant_id, site_id, asset_id) REFERENCES asset(tenant_id, site_id, id);
ALTER TABLE operational_record ADD CONSTRAINT operational_record_fuel_asset
    CHECK ((kind IN ('FUEL_DELIVERY','TANK_DIP')) = (asset_id IS NOT NULL));
ALTER TABLE operational_record ADD CONSTRAINT operational_record_fuel_quantity
    CHECK (kind NOT IN ('FUEL_DELIVERY','TANK_DIP') OR (quantity IS NOT NULL AND unit = 'L' AND period_end IS NULL));
ALTER TABLE operational_record ADD CONSTRAINT operational_record_delivery_ticket
    CHECK (kind <> 'FUEL_DELIVERY' OR (quantity > 0 AND source_document_sha256 IS NOT NULL));
CREATE INDEX operational_record_asset ON operational_record (tenant_id, site_id, asset_id, occurred_at)
    WHERE asset_id IS NOT NULL;
```
- The asset FK targets the existing `asset_scope_unique` (`0001`). Its default MATCH SIMPLE leaves rows with a null `asset_id` unchecked.
- Adding a nullable column fires none of the append-only triggers.
- **Downgrade:**
  - refuse with `RuntimeError("0054 downgrade requires no FUEL_DELIVERY or TANK_DIP operational records")` if any such row exists (rows are append-only, so they cannot be deleted);
  - then drop the index, the three CHECKs, the FK and the column;
  - restore the four-kind CHECK under the same name.
- **Renumber rule (§8.4):** if a migration has landed on main as 0054 before K2 starts, K2 takes the next free number and re-points `down_revision`. The single-alembic-head test catches a miss. **K3's 0055 then follows K2's number.**

**The `fuel_records` read, for K3 (new `B/work/fuel_records.py` and new `B/work/adapters/postgres_fuel_records.py`):**
```python
FUEL_KINDS = ("FUEL_DELIVERY", "TANK_DIP")

@dataclass(frozen=True)
class FuelRecord:
    root_id: str              # canonical record id (the REC lineage root)
    head_id: str              # the version selected at known_at
    code: str                 # the root's public code, REC-nnnnnn
    kind: str                 # the head's kind, one of FUEL_KINDS
    occurred_at: datetime     # the head's occurrence (a correction may move it)
    recorded_at: datetime     # the head's recorded_at
    root_recorded_at: datetime  # when the record was first recorded (K3's DELIVERY_RECORDED_LATE reads it)
    quantity_l: Decimal       # the head's quantity, exact
    ticket_sha256: str | None # the head's source_document_sha256
    actor_id: str
    body: str

class FuelRecordsPort(Protocol):
    def fuel_records(self, tenant_id: UUID, site_id: UUID, tank_asset_id: UUID,
                     lo: datetime, hi: datetime, known_at: datetime) -> tuple[FuelRecord, ...]: ...
```
- **Selection.** Every operational-record root of the Site recorded at or before `known_at`, at its latest version recorded at or before `known_at` by `(recorded_at, id)`. This is the root/head shape of `_OPERATIONAL` (`B/work/adapters/postgres_global_read.py:74-85`). Keep a record whose **head** has kind in `FUEL_KINDS`, `asset_id = tank_asset_id`, and `occurred_at` in `[lo, hi)`. Order by `(occurred_at, root_id)`.
  - Membership uses the head's occurrence, unlike the list page's root occurrence: a corrected time must move a delivery to its true night.
- **Arguments.** All three instants must be UTC-aware and `lo < hi`, else `ValueError("fuel_records needs UTC instants with lo < hi")`. `known_at` is not capped (K3 passes a window end that is already in the past).
- **Adapter.**
  - `select_fuel_records(c: Connection, tenant_id, site_id, tank_asset_id, lo, hi, known_at)` runs on a caller's connection, so K3 can read inside its own snapshot.
  - `PostgresFuelRecords(database_url, *, statement_timeout_ms=30_000)` implements the port with one `REPEATABLE READ READ ONLY` transaction.
  - Neither one writes.
- **No new HTTP route in K2.** K5's list of deliveries and dips adds its route in its own card.

**Screens (frontend, small):**
- `F/work/WorkRequestRecord.tsx` `REC_KIND_LABEL` gains `FUEL_DELIVERY: "Fuel delivery"` and `TANK_DIP: "Tank dip"`. `recKindLabel` is also what the global Operational records page shows in its Type column (`F/work/OperationalRecords.tsx:126-128`), so no raw kind ever reaches the screen.
- In `F/work/globalWorkClient.ts`, add `export type FuelRecordKind = "FUEL_DELIVERY" | "TANK_DIP"` and set `GlobalOperationalRow.kind: GlobalOperationalKind | FuelRecordKind`.
- The kind filter (`GLOBAL_OPERATIONAL_KINDS`, `KIND_CHIPS`, `KIND_ZERO`, the backend `RECORD_KINDS` in `B/work/global_index.py:52` and `B/work/operational_index.py:26`) stays at the four v69 kinds.
- **MOCK DEVIATION MD-FUEL-K2-1.** v69's Operational records chips are "All, Operator log, Manual reading, Shift note, Site visit" (`frontend/mockups/v69/index.html:984`), and its subtitle names those four (`:1083`). Fuel delivery and tank dip rows appear under "All" with the plain labels above. No chip is added, and a `kind=FUEL_DELIVERY` URL stays the existing invalid-filter state.
- The reading line (`readingLine`, `OperationalRecords.tsx:97-101`) stays MANUAL_READING-only: the fuel bodies above already state the litres once.
- Wording: the guard words theft, stolen, stole, siphon and pilfer appear nowhere (H4).

**Tests:**
- **L0 `backend/tests/test_k2_fuel_records.py`** (no DB; a fake transaction implementing only the `_Tx` methods `post_operational_record` calls):
  - each new refusal, in the order above, with its literal message;
  - one existing-kind body (`oprec()` from `test_w401_work_service_postgres.py`, OPERATOR_LOG) gives a command hash **equal to a literal pinned from main before any edit**. The builder computes it on main first and commits the pin with the test;
  - `asset_id` present on a SITE_VISIT → `WORK_RECORD_ASSET_NOT_ALLOWED`;
  - `FuelRecord` window argument checks.
- **L2 `backend/tests/test_k2_fuel_records_postgres.py`** on own `assetops_k2_test` (Kobo imported via `test_s1_bindings_postgres.imported`; Kobo's `fuel-tank` asset is `FUEL_TANK`; `VirtualDbClock` as in W401):
  - migration up/down/up on an empty table;
  - down is refused with a fuel row present;
  - single alembic head;
  - post a delivery and a dip (201, `operational-record-1`, REC code, row `asset_id` set);
  - idempotent retry 200, and a different body under the same key gives 409;
  - the `generator` asset gives `WORK_RECORD_ASSET_NOT_TANK`; an unknown or foreign-Site asset gives `WORK_LINK_SCOPE_INVALID`;
  - a raw SQL insert of a TANK_DIP with a null `asset_id` violates `operational_record_fuel_asset` (the CHECKs hold below the service);
  - `fuel_records`:
    - the window is half-open at both edges;
    - a record recorded after `known_at` is absent;
    - a correction of the dip (new quantity, recorded later) is read as the head after its `recorded_at` and as the root before it;
    - a correction that moves `occurred_at` out of the window drops the record;
    - an OPERATOR_LOG of the same Site never appears;
  - the global Operational records list returns the fuel rows with `kind` set, and `?kind=FUEL_DELIVERY` keeps today's invalid-filter refusal.
- **Existing, must stay green unchanged:** `test_w401_work_service_postgres.py`, `test_w401_work_api.py`, `test_w401_migration_postgres.py`, `test_w401_work_read_postgres.py`, `test_w401_site_indexes_postgres.py`, the W6-01 operational-records tests (`test_w601*`), the single-alembic-head test. If any of them needs a behaviour edit, that is a stop. A test that only enumerates migration heads or the kind CHECK text may take the new head or kinds.
- **Frontend:** `operationalRecords.test.tsx` gains a TANK_DIP row rendering "Tank dip" in the Type cell. `workRequestRecord.test.tsx` gains a `recKindLabel("FUEL_DELIVERY") === "Fuel delivery"` case.
- **Guards:** the four tools, run directly, and `frontend-hardwiring` (the two labels are plain copy constants).

**DB.** Only `assetops_k2_test`. Never `assetops_demo3_full_test`. No prepare, tick or suite.

**Stops:**
- any change to an existing kind's `payload_sha256`, response bytes, row shape or refusal;
- a need to edit `contracts/` (`OPERATIONAL_RECORD_KINDS`), `B/runs/`, the scenario models or the envelope schema;
- a W401 or W601 test needs a behaviour change;
- a client screen would need a new chip, panel or route (that is K5's);
- more than 1.0 unit.

**Size 0.75:** migration and its tests 0.15; service, model codes and store 0.2; the read port and adapter 0.15; frontend labels 0.05; tests 0.2.

**Reading budget:** this §9c.2; `B/work/service.py:30-40`, `:398-530`; `B/work/model.py:1-90`, `:140-245`; `B/work/adapters/postgres_work_store.py:1-200`, `:266-333`; `B/work/adapters/postgres_global_read.py:55-145`; `backend/migrations/versions/0027_w4_work_cases.py:160-222`; `0053_fuel_cost_2.py` (pattern); `backend/tests/test_w401_work_service_postgres.py:1-150`, `:458-482`; `F/work/WorkRequestRecord.tsx:45-60`; `F/work/OperationalRecords.tsx:55-130`; `F/work/globalWorkClient.ts:140-200`.

### 9c.3 F0 review Lows and the residual risk, placed in the cards they belong to

F0 merged as evidence only (`992847b72`, review ACCEPT, `.agent/review-F0.md`). Its three Lows and its residual risk are assigned here. K0 is build-ready from §9.3 and its pre-flight, so items 1 and 4 bind K0 as amendments to §9.3. Item 2 binds K3's card, written at the round before K3 starts.

1. **L1, K0: the log id and file name.**
   - The F0r action log's own `log_id` is `kisiwa-001-operational-actions` (`.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml:18`). §9.3 item 2's example says `"log_id": "kisiwa-001"`.
   - **Ruling: the pre-registered file wins.** K0 promotes the log **verbatim** (§9.3) and never edits it, so the id stays `kisiwa-001-operational-actions`.
   - By §9.3's path rule `C/operational-actions/{log_id}-v{log_version}.yaml`, the file is **`C/operational-actions/kisiwa-001-operational-actions-v1.yaml`**. The run request key is `{"log_id": "kisiwa-001-operational-actions", "log_version": 1}`.
   - The adapter refuses a log whose inner `log_id` or `log_version` differs from its file name (`OPERATIONAL_ACTION_LOG_MISMATCH`, typed, nothing written). A K0 test covers that refusal.
   - This amends §9.3's example only. K7 uses the same key.
2. **L2, K3: the use-term source and the untested band edges.**
   - The probe's "readings" source took night use from the true trajectory (`T/probe_kisiwa_fuel.py:620-625`). §8.3 defines use from the **published generator readings per 5-minute slot**.
   - K3's card will require:
     - (a) K3 computes `loaded` and `idle_h` **only** from accepted generator readings, through A2's slot rule; it never reads a trajectory;
     - (b) K3's L0 tests pin the three edges F0's tests never exercised: an idle-only night with `idle_h × 4.9` in `use_high` (so dropping the idle term fails a test); a window with `residual_low` exactly 0 (WITHIN_MARGIN, not BELOW_MATERIALITY); and the delivery night's high edge, `+ D_tol` with the ticket tolerance, as an exact Fraction;
     - (c) K3's evidence states that Kisiwa has 0 idle minutes, so on Kisiwa's own nights the idle term is exercised only by the test in (b).
   - K3's L2 must also match F0r's per-night bands from the stored windows (the KIS-3 reproduction), now from readings.
3. **L3, information only:** `seeded_uuid4` wraps all of `build()` and so also seeds run ids. That is harmless.
   - K1's parity test calls `build()` without the seeding. Run ids and snapshot-derived values differ, and §9c.1 already removes exactly those keys. No action.
4. **Residual risk, K0: the operational origin is so far proven only through F0r's event-id carrier.** K0's tests add, beyond §9.3's list:
   - (a) a Kisiwa run-2 delivery and run-4 removal frozen with the **field** `origin == "OPERATIONAL_ACTION"` and `action_ref`, and an `event_id` that is `"{action_id}/{effect}"` with **no** `OPERATIONAL_ACTION/` prefix carrier;
   - (b) the omit rule, byte-level: for a scenario-only run, the rendered run, the frozen causes and conditions, the trajectory identity and every stored form contain neither the `origin` nor the `action_ref` key. The digests equal pins taken on main before K0's first edit (one Kobo, one Cold, one EV run);
   - (c) a round-trip through every run store keeps both fields for an action cause and keeps them absent for a scenario cause;
   - (d) the kernel result for the Kisiwa runs with actions equals F0r's per-step tank account for run 4 (40/3 L at steps 120–128) and run 2 (300 L at step 227). This shows that the real field path gives the same physics as the carrier.
   - Inside K0's 0.4 test allowance; no size change.

### 9c.4 Sizes, date and the tripwire

- **Unit sizes: unchanged.** K1 is 1.25 and K2 is 0.75. Every other §9.5 row stands.
- **Contingency (0.5).** It has now paid for the R3a, R3b and R3c card rounds and the F8 Sonnet round (about 0.25 together). About 0.25 remains, for K4's Finding-kind risk.
- **One new risk, off the critical path.** K1's pre-flight (b) routes Kisiwa's device-id copy, starting with `SERVICE_FEEDERS` and the two UI strings, to K8. The Architect sizes it at K8's card round; the estimate is +0.1 to +0.25 on lane 1. K8's code part runs beside K4 and K6, so the critical path does not move unless it exceeds about 1 unit.
- **Critical path.** F0r's two extra rounds (R3a and F8) add about 0.15 to its 0.5. The path is F0r about 0.65 → K1 1.25 → K3 1.5 → K4 2.0 → K6 1.5 → K7 freeze 0.5 → K8 captures 0.25 → K9 1.0, about **8.65 lane-units, about 2.9 working days**, with K1a run in parallel as it was. **That is below the 9.75 tripwire. It is not crossed, so no cut is needed.**
- **Demo date: unchanged at about +3.25 working days** (range 2.75–5.25) against the plan without Kisiwa.
- **Machine time:** K1's L2 adds about 5 min of one gateway-published day; K2 adds none of note. E3 is unchanged.

### 9c.5 Owner questions

None.

---

