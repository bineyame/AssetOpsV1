# W2-05b phase handoff - run 3 (spec commits 1-3 built)

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
- `110f66de` commit 3: `ev-publication/1`+`ev-observation/1` transform appended to
  `simulator/assetops_simulator/observation/transform.py` (`EvChannel`, `EvPublicRecord`, `ev_public_records`,
  `ev_decimal_text`, `ev_rounded_kwh`); `gateway_report.py` `ev_event_id`/`ev_report_key`; `gateway/mappings.py`
  `EV_V4_GATEWAY_MAPPINGS` + `("ev-publication",1)` in `gateway_mapping_for` (other versions LookupError);
  `host/ev_publication.py` (`ev_channels(binding rows)` -> `EvBindingRefused`, `ev_execution(definition,
  EvParameters)`, `report_of`, `ev_reports`, `EvReport`, `ev_series_digest`); `host/lab_execution.py`
  `_stage_registered_virtual_ev` sharing `_stage_registered_v2_reports` with cold (cold bytes/message unchanged).

## Focused counts (this run)
- `backend/tests/test_w205b_ev_scenarios.py` 73 passed; adjacent backend (run setup, scenarios, cold API/
  identity, lab gate, fingerprints, binds, profile users) 820 passed after inventory updates.
- host adjacent (cold lab execution/dispatch, contract9 gate, s6 replay) 42 passed, 2 skipped (pre-existing).
- `simulator/tests/test_ev_pack.py` 73 passed; `test_cold_pack.py` 6 passed.
- frontend `evRunSetup.test.tsx` 13 + `evScenarioChoiceClient.test.ts` 12 passed; adjacent shell suites
  (cold setup/client, Lab gate, entry point, rail, routes, runs, catalog, vocabulary) 329 passed.
- `tsc --noEmit` exit 0. `tools/check-all.ps1`: 10/10 passed on `1d7bfd7c`.
- Non-vacuous: removing `_require_ev_identity` and the START-twice guard each fails its test.

## Run 3 focused counts (commit 3, `110f66de`)
- `gateway/tests/test_ev_v4_admission.py` 14; gateway suite 249 passed. `simulator/tests/test_ev_public_transform.py`
  7 (+ ev/cold pack 79). `host/tests/test_ev_publication.py` 27; host cold lab/publication + t026 dispatch 40.
- backend adjacent on private `w205b_run3_test` (S2 ledger/gateway access/receipt/registered basis/commit API/
  rejection placement, W2-00 binding metadata/receipt bytes/source events, `test_w205b_ev_scenarios`, all
  `test_w205a_ev_*`): 324 passed; DB dropped. Frontend untouched (no tsc). `tools/check-all.ps1` 10/10.
- Non-vacuous: disabling the DROP, the no-session fault refusal, or the mean channels each fails a test.

## Blocking for commit 4 (see `.agent/W2-05b-pending-rulings.md`)
- **Q15** public `UNPLUGGED` is not a label of the 05a state ENUM map: the gateway holds it `INVALID_ENUM`, so a
  real Stage refuses at 08:00. **Q17** the 05a energy rows' `IDENTITY_KWH` conversion is unsupported by the gateway
  snapshot reader (activation refuses) and the S2 ledger. Commit 4's admitted Stage cannot pass until both are
  ruled. Tests characterize both (host test offers energy as IDENTITY; UNPLUGGED asserted HELD) and must be
  flipped when ruled. Q16 (fault correlation without S) does not affect the six documents. Notes N9-N12 added.
- N3/N8 rulings are with the Architect; this run did not touch them.

## Anchors for commit 4 (artifact, delayed schedule, restart, Commit)
- Dispatch: `host/lab_execution.py` `start` :2187 dispatches cold at :2206 via `_is_cold` :2128; mirror with an EV
  branch and `_start_ev` beside `_start_cold` :2266 (verify inputs -> `ev_execution` -> `ev_reports` ->
  `_stage_registered_virtual_ev` -> terminal projection -> artifact). `PhysicallyUnacceptable` and binding refusal
  before Stage map to `FROZEN_RUN_NOT_RECONSTRUCTIBLE`; Stage refusal string -> `ExecutionFailure(kind=
  "PUBLICATION_REFUSED")` as cold :2311.
- Inputs: model on `host/cold_publication.py:verify_cold_inputs` and `host/cold_lab.py` `ColdInputs`/
  `StoreColdInputs` :50-80; compose in `host/lab_app.py:85` (`cold_inputs=`) an `ev_inputs` port that re-reads the
  exact Foundation revision, the effective binding revision rows (`device_id,signal_id,role,asset_code` for
  `ev_channels`) and the scenario by ID/SHA. Foundation -> `EvParameters` mapping is still to write
  (`packs/ev_charger.py:72` fields; frozen values in build spec "Registered fixture").
- Artifact: `YamlExecutionArtifacts.write_cold` :1896 and `cold_lab.py` render/parse :173/:219 are the schema-6
  precedent for schema 7 `execution_kind:"EV"`; `cold_lab.delay_event_id` :276 is already used by the EV Stage.
- Digests: `EvRun.content_digest()` (private, N8 pending) and `ev_series_digest(reports)`.
