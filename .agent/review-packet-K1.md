# Review packet K1: the Kisiwa Site (DIESEL-1-R3c §9c.1)

- Branch `task/DIESEL-K1-kisiwa-site`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k1`, from main `f9d27116b`.
- Commits: `007ff6aee` (build), `4dabd2a47` (test fixes), plus this packet's commit.
- Merge check against current main `70a5e8699` (MB-1a merged since branching): `git merge-tree` clean, no conflict.
- Size used: about 1.25 (inside the card).
- USER_REVIEW_REQUIRED: no client screen changes (Kisiwa is not in `T/demo_combined.py`). Reviewer gate only.

## Outcome

`KISIWA-001` is registered the way the prepare will register it: import, convert (12 rows, roles-2), supply uses, the generic no-load rate, the labelled roles-4 demo configuration (the tank sensor accuracy plus 3 bindings) and diesel price v1. On Postgres, the registered Site reproduces F0r's `probe-result.json` exactly outside the removed keys. One Kisiwa day ran end to end: gateway, S2, S3 and S4, then the board.

## Files (all as the card's table)

| # | File | Note |
|---|---|---|
| 1 | `config/site-templates/kisiwa-diesel-hybrid-60kw.yaml` | The card's header, then the draft's bytes from `template_id:` on. A blank line 22 is kept as the separator. |
| 2 | `backend/tests/test_site_template_fingerprints.py` | Pin `013c3bbc…ca07c`. It passes, so the Architect's digest matches. |
| 3 | `backend/tests/test_site_template_catalog.py` | Four templates, plus the comment line. |
| 4 | `backend/tests/fixtures/s1/kisiwa-001.yaml` | The render. L0 checks it. |
| 5 | `backend/conversions/kisiwa-001-bindings.json` | Byte-equal to the F0 draft. L0 checks it. |
| 6 | `backend/conversions/kisiwa-001-minigrid-roles-demo-config.json` | The card literal. |
| 7 | `backend/assetops_backend/sites/models.py` | Two definitions, the basis state set, the FUEL_TANK carriers, and strictly positive. |
| 8 | `tools/demo_combined_kisiwa.py` | `register_in`, `register` and the CLI. |
| 9 | `host/tests/kisiwa.py` | `KisiwaRegistered`, `draft_day` (product v7). |
| 10–12 | `backend/tests/test_k1_kisiwa_fixtures.py`, `backend/tests/test_k1_kisiwa_site_postgres.py`, `host/tests/test_k1_registered_kisiwa.py` | L0, L2 site, L2 parity |

## Pre-flight (run against the code before the build; no stop)

- **(a)** Closed by F0r.
- **(b)** Kisiwa copy that names the clinic, the mill or Kobo by id goes to **K8** (no Kobo byte changed in K1).
  - Server:
    - `backend/assetops_backend/evidence/overview.py:71-75` `SERVICE_FEEDERS` ("Clinic feeder", "Mill feeder"). `site_overview` receives the Site, but the labels ignore Foundation display names. Fixing it would mean a new input, so it goes to K8.
    - `backend/assetops_backend/work/domain_action.py:118` "Run the mill at midday". This Action is raised only from an opportunity study, and Kisiwa has none.
  - UI:
    - `frontend/src/sites/MiniPerformance.tsx:971-972` `CLINIC_FEEDER_LABEL`
    - `frontend/src/sites/SiteWindowOverview.tsx:484` (the residential, clinic and productive objective)
    - `frontend/src/sites/SiteMillVerification.tsx:77`
    - `frontend/src/sites/siteWorkCases.tsx:297` (comment; check it)
  - **Site data (new finding):** the shipped template, copied byte-for-byte from the Architect's draft, names two meter signals "Active power to the clinic" and "Active power to the mill" (template `devices`, `clinic-meter` and `mill-meter`). K1 must not change the template, so the Architect should decide at K8 whether a template v2 renames them.
- **(c)** Every row without a productive load reads an existing honest state on the served board. No new text was needed. Served strings (L2 run):
  - Grow:
    - "Not available yet · no productive users identified for this site"
    - "Not available yet · spare solar not checked on the last 5 days" (the margins are not declared)
    - "Sales to productive users are not metered, so revenue itself is not measured yet"
    - KPI "No target set yet"; potential "No potential found yet"; earnings "Not known yet"
  - Cost: "Declared at 1.25 USD per litre", "No complete fuel balance yet", and generator use "Not available yet · this record could not be loaded".
  - Protect: "Battery and generator condition are not assessed"; service "Not available yet · delivered power not read for this hour".
  - Assure: "No verified result yet"; readings "Not available yet · this record could not be loaded".
  - Every row's state is UNKNOWN, and `read_state` is PARTIAL.
  - No served string contains Clinic, Mill, Kobo, theft, stolen, siphon or pilfer.
- **(d)** In-memory store support:
  - `InMemoryFoundationStore` supports `publish_component_properties`, `apply_demo_configuration`, `import_site` and `convert` (`backend/tests/foundation_fakes.py:44-183`). L0 item 6 runs in memory.
  - The board read is `GET /api/sites/{code}/outcome-board` (`backend/assetops_backend/outcome_api.py:44`), called through `TestClient(create_app(load_feature_flags()))`.
  - The price read is `PostgresAssumptionStore.snapshot` + `fuel_cost.select_window_price` (`backend/assetops_backend/financials/composition.py:151-153`).

## Acceptance (card items)

**L0, items 1–7: pass.** 44 tests (with fingerprint and catalog). In detail:
- item 1: the template parses, its parsed content equals the draft's, and its bytes from `template_id:` on are equal;
- item 2: the bindings file is byte-equal to the draft;
- item 3: the import record equals the render;
- item 4: the roles-4 configuration's keys, status, roles and copy check pass;
- item 5: the vocabulary checks pass: 10 L accepted on FUEL_TANK, GENERATOR refused, 0 L refused, SITE_CALIBRATION accepted, SITE_TEST refused, L/h refused;
- item 6: `register_in` in memory gives the tank 10 L GENERIC_DEFAULT, the generator 4.9 L/h GENERIC_DEFAULT plus all template properties, the three supply uses, and roles-4 with 15 bindings;
- item 7: the v7 pin is in `EXECUTABLE_MODELS` and `MODEL_PROFILES`, and v3 still pins mini-grid 6.

**L2 site test: 3 passed (470.99 s on `assetops_k1_test` via `pg_harness`).**
- The Foundation facts and supply uses are as above (as known at install + 30 min).
- Diesel price: UNPRICED/NO_PRICE at install + 59 min, then PRICED 1.25 USD at install + 1 h.
- The day was READY on the registered basis and published as 1828 batches and 3659 envelopes, all accepted.
- **94 accepted `fuel_level` records** for KISIWA-001, 12:00Z to 12:00Z: the first tank readings stored.
- **Dispatch assessments exist** (`dispatch` CANDIDATE_AVOIDABLE ×2, COMPLETE ×2), and the worker reported DONE with no refusal.
- **Board 200.**

**Registered parity: 1 passed.** The values of the removed keys were printed:
- `assumptions.model` and `assumptions.probe_local_v7`: identical text. The probe writes these constants itself; physics ran on product v7.
- `registered_path`: as expected, only the following differ:
  - foundation_version 9 against 1
  - binding_set_version 9 against 1
  - snapshot `ee166f4d…` against `38a121ba…`
- `example_fuel_level_report_text`: only `report_key` differs. The value is 699.5 L in both.
- `snapshot_fuel_level_binding`: role, units and conversion are equal; only the ids differ.

**Parity is non-vacuous.** Changing the import record's `stop-soc-threshold` from 90 to 80 makes it fail (`dips[0].dip_l` 683 against 706, …). The change was reverted with `git checkout`.

## Known deviation (needs the Architect's eye): line endings in the parity test

- **What happened.** The first parity run found exactly one difference: `assumptions.actions_sha256`, `a939…911d` against `7777…b634`.
- **Cause.** The probe hashes the action log's working-copy bytes. This checkout uses `core.autocrlf=true` (system gitconfig), so the file is CRLF. The committed blob is LF, and its sha is `7777…b634`, F0r's value.
- **The same happens on main.** On this checkout, `tools/probe_kisiwa_fuel.py --check` prints "probe result differs from the committed file". When the two hashed files are read LF-normalised (scratch run), it prints "probe result current".
- **What I did.**
  - The parity test reads exactly `probe.ACTIONS` and `probe.BINDINGS` as their committed LF bytes, through a monkeypatched `Path.read_bytes`. Nothing else is normalised.
  - The probe and `probe-result.json` are not edited.
  - With that, the comparison is fully equal; `registered_path.bindings_sha256` matches F0r too.
- **Why I did not treat it as the stop.** The difference is a working-copy artefact, not a registered-Site difference.
- **Suggested follow-up (not done; outside K1's files).** Add `.gitattributes` `eol=lf` for `.agent/DIESEL-F0/*`, as the W2/W4 byte-pinned fixtures have. This makes F8's `--check` checkout-independent.

## Kobo / Cold / EV byte-equal proof

- `git diff --stat main...HEAD` lists 12 files: the card's files plus `models.py`. No Kobo, Cold or EV template, fixture, config, conversion or scenario changed. `d-verification-window-v3.json` is untouched and still pins v6 (L0 item 7).
- The vocabulary addition moves no digest: `test_scenario_execution_contract.py` and `test_execution_contract_alignment.py` pass, and the earlier Kobo template pins still pass.

## Checks run

- Localised tests (no DB): 240 passed. They cover `test_k1_kisiwa_fixtures`, `test_site_template_fingerprints`, `test_site_template_catalog`, `test_s1_bindings`, `test_s2_registered_basis`, `test_fuel_cost_v2`, `test_scenario_execution_contract` and `test_execution_contract_alignment`. `host/tests/test_mini_grid_v7.py`: 9 passed.
- L2 (on `assetops_k1_test`, one at a time): the site test 3 passed (it ran twice, the second time to print the board strings); parity 1 passed.
- `tools/probe_kisiwa_nights.py --check`: "probe result current (G6 pass)".
- `tools/probe_kisiwa_fuel.py --check` on this CRLF checkout: "differs". With LF reads: "probe result current" (see the deviation above).
- Guards (run directly, no `-ExecutionPolicy`; `npm ci` in `frontend/` first):
  - `tools\check-all.ps1 -Python <plan2 venv>`: **All 17 guards passed**.
  - `tools\check-architecture.ps1`: passed.
  - `tools\check-agent-workflow.ps1`: passed.
  - `tools\check-navigation-truthfulness.ps1`: passed.
  - A first run without `-Python` failed 9 guards with "missing tool …\.venv\Scripts\python.exe". The worktree has no `.venv`, and check-all overwrites `ASSETOPS_GUARD_PYTHON` with its default. That was an environment problem only.
- No full suite, no prepare, no `test_demo_combined_postgres`. `assetops_demo3_full_test` was not touched.

## Residual risk

- Several board contributors read "this record could not be loaded" (generator use, battery, readings) for one Kisiwa day with no S2 imported comparison. This is honest existing text; K7's story days should show whether it persists.
- The import-record sha256 stored at import depends on the checkout's line endings, exactly as Kobo's does. It is never compared.

## Reviewer focus

- The LF normalisation in `host/tests/test_k1_registered_kisiwa.py`: accept it, or treat it as the card's stop.
- `register_in` follows the card's order and clocks; `register` publishes diesel v1 only.
- The K8 findings list above, including the template's two signal names.

## Fix round 1 (review-K1, verdict FIX)

- **M1 closed.** `test_w402_roles_properties.py` carriers dict and `test_w205a_ev_vocabulary.py` `STATE_PROPERTY_VALUES` now include `fuel-level-sensor-accuracy` (L, PHYSICAL, FUEL_TANK) and `fuel-level-sensor-accuracy-basis` (state, PHYSICAL, FUEL_TANK; GENERIC_DEFAULT / MANUFACTURER_DATASHEET / SITE_CALIBRATION). Only those keys were added; no assertion weakened. The EV-named file edit is a shared-table assertion update, not an EV data change.
- **L2 closed.** `test_k1_kisiwa_site_postgres.py` pins exactly 94 `fuel_level` records, first and last at 12:00Z to 12:00Z, and `analytic_id == "dispatch"`.
- L1, the probe, `probe-result.json` and `.gitattributes` were not touched.
- Main merged first. No-DB set (47 files plus the host registered test): 961 passed, 41 skipped.
