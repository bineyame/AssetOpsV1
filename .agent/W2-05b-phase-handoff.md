# W2-05b phase handoff - run 2 (spec commits 1 and 2 built)

Branch `task/W2-05b-ev-producer`, worktree `AssetOpsV1-review5`. Not merged.

## Done
- `59608b3f` commit 1: strict `ev-scenario/1` parser `backend/assetops_backend/scenarios/ev_parsing.py`
  (Q1-Q7), six `config/scenarios/ev-*.yaml`, loader dispatch + basename check
  (`scenarios/adapters/yaml_shipped_scenario_store.py` `_read_shipped`), union in `scenarios/ports.py`;
  `runs/profiles.py` `EV_CHARGER_MODEL`, `EV_CONNECTOR_STATES`, `EV_PUBLICATION_PROFILE` (Q12);
  `runs/service.py` `_create_ev_draft` + shared `_freeze_document_draft` (cold refactored onto it, bytes
  unchanged), EV profiles refused on legacy scenarios; `runs/parsing.py` `_require_ev_identity`;
  `simulator_lab_api.py` `list_ev_scenarios` (`EV_SCENARIOS_ROUTE`, `EV_SCENARIO_LABELS`, kw `ev_access`,
  `ev_owner`), legacy list/detail exclude EV; `main.py` composes `development_access` + `no_owner_principal`.
  Frontend: `EvRunSetupFrame.tsx`, `evScenarioChoiceClient.ts`, `EV_RUN_SETUP_PATH`/`EV_SCENARIOS_API_PATH`
  and route in `simulatorLabRoutes.tsx`, `App.tsx` `evScenarios` prop, Lab link in `SimulatorLabFrame.tsx`.
- `1d7bfd7c` commit 2: pure pack `simulator/assetops_simulator/packs/ev_charger.py` (Q2/Q3/Q13/Q14).

## Focused counts (this run)
- `backend/tests/test_w205b_ev_scenarios.py` 73 passed; adjacent backend (run setup, scenarios, cold API/
  identity, lab gate, fingerprints, binds, profile users) 820 passed after inventory updates.
- host adjacent (cold lab execution/dispatch, contract9 gate, s6 replay) 42 passed, 2 skipped (pre-existing).
- `simulator/tests/test_ev_pack.py` 73 passed; `test_cold_pack.py` 6 passed.
- frontend `evRunSetup.test.tsx` 13 + `evScenarioChoiceClient.test.ts` 12 passed; adjacent shell suites
  (cold setup/client, Lab gate, entry point, rail, routes, runs, catalog, vocabulary) 329 passed.
- `tsc --noEmit` exit 0. `tools/check-all.ps1`: 10/10 passed on `1d7bfd7c`.
- Non-vacuous: removing `_require_ev_identity` and the START-twice guard each fails its test.

## Anchors for commit 3 (public transform / v4 mapping / gateway Stage)
- Pack output: `run_window(EvChargerPack(params, scenario_sha256=...), start, end, forcing)` -> `EvRun`;
  `EvRun.events` (`EvEvent.at, connector, kind in START|END|ABORT|FAULT|CLEAR, session_id`), `EvRun.minutes[i]
  .document` (per boundary: connector `state, session_id, requested_kw, allocated_kw, energy_kwh` as exact
  `p/q` text, `site_import_kw`), `.after` states (`energy_kwh` Fraction for half-even rounding),
  `EvRun.content_digest()`. `scoped_session_id(sha, label)`; `DEFAULT_PARAMETERS` (Foundation mapping is commit 4).
- Document side: `EvScenarioDefinition.observations` (`EvObservation time, kind, connector, action,
  release_at`), `.scenario_sha256`, `.observation_sha256`; forcing to pack rows via `EvForcingRow`.
- Unchanged from run 1: `simulator/assetops_simulator/gateway/mappings.py:175,189` (cold closed mapping),
  `contracts/assetops_contracts/source_envelope_v4.py:600,685,693` (EV tables, `V4_EV_MAPPING_PROFILE_ID`),
  `contracts/assetops_contracts/gateway_report.py:DeviceReportV2`, `host/cold_publication.py` (report-key
  helper precedent), `host/lab_execution.py:_stage_registered_virtual_cold` :2335,
  `simulator/assetops_simulator/observation/transform.py:350`. 05a binding: `sites/ev_lab.py`,
  `backend/tests/fixtures/w2/ev-lab-001.yaml`.

## Open
Non-blocking interpretation notes N1-N8 appended to `.agent/W2-05b-pending-rulings.md`; N8 changes the private
`content_digest` that commit 5 manifests pin, so confirm it before commit 5. Next: commit 3.
