# W2-02 handoff after commit (2) — commit (2) landed except the Lab run-setup UI wiring (one question open)

Branch `task/W2-02-cold-producer`, worktree `AssetOpsV1-review2`. Binding: `.agent/W2-02-build-spec.md` (amended
q3). Env: `.agent/W2-02-build-brief.md`, `.agent/W2-02-phase-1-handoff.md` (private DB `assetops_w202c_test`).
Commit-(2) commits: `9e827421` (pack/transform/mappings/profiles/identity fields), `1ad4a075` (cold freeze),
`bd32d369` (host dispatch), `a1f64a6d` (cold-scenarios endpoint + client).

## Landed in 9e827421 (from the previous run; anchors still valid)
- `packs/errors.py` `PhysicallyUnacceptable`; `packs/cold.py` `ColdParameters.from_properties`, `ColdState`,
  `ColdPack.step`, `run_window -> ColdRun(transitions, records)`; `observation/transform.py` `cold_observations`;
  `gateway/mappings.py` `COLD_V4_GATEWAY_MAPPINGS`; `kernel/execute.py` `execution_path_for`, `ColdExecution`;
  `runs/profiles.py` cold profiles; `runs/models.py`/`runs/parsing.py` the four optional identity keys.
  Pack interpretations to record in packet Known Deviations: GENERATOR_FAILURE latent fault -> START_RESULT/FAILED
  at the timeout; restore switches transfer to GRID immediately and stops the generator; compressor kW = cooling
  capacity while RUNNING on a powered bus; grid/transfer share the outage correlation; ambient every 5 min.

## Landed this run (focused tests pass)
- `scenarios/cold_parsing.py:observation_sha256(definition)` — the q3 digest (canonical JSON of
  `{"observation_profile":"cold-observation/1","observations":[rows]}`); the host must reuse it to recompute.
- `runs/service.py:create_draft_run` dispatches a `ColdScenarioDefinition` to `_create_cold_draft` (before
  model/publication resolution). Refusals before Draft: unregistered/legacy Site or `site_id != site_code`
  (VERSION_UNAVAILABLE), scenario version, model/publication pair != document (VERSION_UNAVAILABLE), seed
  (REQUEST_INVALID), interval or timestep != 1 (INTERVAL_INVALID). Identity: empty legacy projections,
  `signal_mappings=selection.signal_mappings` (as the registered legacy path does), `scenario_sha256`,
  observation `cold-observation`/1 + digest, `registered_basis=selection.basis`; reasons = cadence+publication.
- `backend/tests/test_w202_cold_run_identity.py` (16): round trip, digest over rows, legacy omits keys, bad
  digest refused on read, request mismatches refused before Draft, legacy-run `run_identity_sha256` golden pinned
  (`0db30ea9…0bd5`, computed on `main` and on this branch: identical). `test_scenario_fingerprints.py` unchanged.
- `host/execution_adapter.py:execution_path(run)` (wraps `execution_path_for`; a half pair ->
  `FrozenRunNotReconstructible`); `model_for` refuses the cold pair; `publication_profile_for` checks the pair
  first. `host/lab_execution.py:_model_for` checks the path before the injected model (cold -> LabControlRefused
  FROZEN_RUN_NOT_RECONSTRUCTIBLE). Test `host/tests/test_cold_dispatch.py` (6). A cold run cannot start in the
  Lab until commit (3) routes it to `ColdExecution` before `_model_for`.
- `simulator_lab_api.py`: `COLD_SCENARIOS_ROUTE`, `COLD_SCENARIO_LABELS`, `list_cold_scenarios(site_id)`
  (empty unless `site_id == COLD-LAB-001` and registered; SiteStoreUnavailable / scenario store -> 503).
  `backend/tests/test_w202_cold_scenarios_api.py` (5); gate route set updated in `test_simulator_lab_gate.py`.
- `frontend/src/shell/coldScenarioChoiceClient.ts` (`createColdScenarioChoiceClient().listColdScenarios(siteId)`,
  strict parse, unavailable never empty) + `__tests__/coldScenarioChoiceClient.test.ts` (5). Typecheck clean.
- Adjacent: `test_run_setup`, `test_w202_cold_scenario`, `test_scenarios_api`, `test_fetch_seam_contract`,
  host `test_host_execution`/`test_lab_execution` pass. `test_runs_api::...PropertylessFoundation...` fails only
  because `var/sites/mg-001.yaml` is absent in this worktree (copy `var/sites` per the brief for the full run).

## Open question (send to the Architect before wiring the UI)
The spec says the Lab choice client "calls this read after Site selection and offers the returned cold scenarios
only for that selected Site". But `RunSetupFrame` (`frontend/src/shell/RunSetupFrame.tsx`) is scenario-first:
its route carries `:scenarioId`, and its form is built from the legacy `getScenario` detail, which the spec makes
a 404 for cold. v69 has no Lab cold-choice surface. Questions:
1. Where do the cold choices render: inside `RunSetupFrame` after the Site picker (`onChoose`, ~:690), or on a
   separate cold run-setup route?
2. When a person selects a choice, does the screen create the run directly with the document-fixed interval,
   seed, timestep 1 and the two profiles (read-only), or prefill the existing form?
3. What copy do the empty and unavailable states use?

## Remaining
1. After the answer: wire `createColdScenarioChoiceClient` into Lab run setup after Site selection, with a
   `settledScreen` frontend test; then vitest for the touched tests and typecheck.
2. Commit (3), per the spec's "DeviceReport v2 and gateway path":
   - Contracts: `DeviceReportV2`, `device_report_v2_text` and `parse_device_report_v2_text` in
     `contracts/.../gateway_report.py`, with `contracts/tests/test_gateway_report_v2.py`.
   - Gateway: the v2 branch in `_admit_in` (`gateway/assetops_gateway/service.py` ~:583-650; v1 parser ~:603,
     `binding_for` ~:610, sequence ~:647), with `gateway/tests/test_cold_v4_admission.py`.
   - Host:
     - route a cold run (path `COLD`) before `_model_for` in start;
     - read the 13 values (`ColdParameters.from_properties`) from the frozen Foundation revision (basis
       `foundation_revision_id` + `foundation_content_sha256`);
     - re-read the cold document by ID, verify `scenario_sha256` and recompute `observation_sha256`; refuse any
       mismatch before any Stage output;
     - run `ColdExecution` and `cold_observations`, then adapt the records to v2 reports;
     - stage through `_stage_registered_virtual` (~:2501) ->
       `RegisteredGatewayPublisher.publish_in_boundary_order` (`host/gateway_publication.py:128`).
   - Identities: gateway `edge-cold-lab-001`; sources are the device IDs (`foundation_service.py:183-208`).
3. Commit (4):
   - the cold replay read and API;
   - the six manifests;
   - the Postgres proof tests and the rule-8 probes;
   - full suites and check-all;
   - packet `.agent/W2-02-review-packet.md`, with the pack interpretations above and the `signal_mappings` choice
     under Known Deviations.
