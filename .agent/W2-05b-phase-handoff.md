# W2-05b phase handoff - run 5 (commits 1-3 built; q2 and q3 applied; commit 4 blocked on Q20-Q25)

Branch `task/W2-05b-ev-producer`, worktree `AssetOpsV1-review5`. Not merged.

## Run 5: q3 fixes (`21745982` "W2-05b q3 fixes")
- Q15: `sites/binding_roles.py` `EV_CONNECTOR_STATES` seven values; both `conversions/ev-lab-001-bindings.json`
  state maps seven identity labels. Gateway admits 08:00 c1/c2 `UNPLUGGED` unchanged; an old map without it
  holds `INVALID_ENUM` (Stage -> PUBLICATION_REFUSED). Tests: roles seven-value map, foundation-postgres old
  revision row keeps id/sha/bytes and the 2026-10-05 corrected revision is selected for 08:00, ev_scenarios
  real `RegisteredLabBasis` Draft freezes the corrected revision/snapshot SHA.
- Q17: `gateway/.../snapshot.py` accepts `IDENTITY_KWH` only for `ev_connector_energy`, kWh->kWh, `{}`;
  service unchanged (non-ENUM canonical-decimal passthrough). `evidence/ledger.py:_normalize` returns the
  unchanged decimal + `IDENTITY_KWH` for that shape, else `CONVERSION_UNSUPPORTED`.
- Q16: `transform.py` `EvPublicRecord.fault_episode=(asset_code, fault_ordinal)` latched per connector;
  `contracts gateway_report.ev_fault_episode_id`; `host/ev_publication.py:_correlation` uses S else episode.
- N10: tests for connector-mean splits at 08:01/08:31 and the nonterminating-mean refusal. N9/N11/N12 already
  matched the build (ratified).
- Counts: gateway suite 260; simulator ev pack/transform/cold 94; host EV+cold/t026/w203/delay/release 91;
  backend `test_s2_*`, `test_w200_*`, `test_w205*` on private `w205b_run5_test` 415 (DB dropped); contracts 6;
  `check-all.ps1` 10/10. Frontend untouched (no tsc).
- Non-vacuous: dropping the snapshot role check fails 3 gateway tests; the ledger role check fails 1; a
  constant fault episode fails 2 transform/host tests.

## Pending (see `.agent/W2-05b-pending-rulings.md`)
- Q18 Draft refusal against an old selected map; Q19 upgrade publication for an installed EV-LAB-001.
- Q20-Q25 block commit 4: schema-7 keys, schedule location, Foundation->EvParameters, binding rows source
  for `ev_channels`, EV notes/history, delay ID prefix.
- **Still owed from N1 (commit 5):** pass `create_app`'s `ev_access`/`ev_owner` to the EV replay router, and the
  walkthrough's isolated ASGI app calls `create_app` with the Site-scoped owner (no global flag).

## Anchors for commit 4 (refreshed on `21745982`)
- `host/lab_execution.py`: `start` :2187 (cold dispatch :2205 via `_is_cold` :2128 -> `execution_path` in
  `host/execution_adapter.py:138`); `_start_cold` :2266 is the model; `_stage_registered_virtual_ev` :2343;
  `_not_started` :2134; artifact read dispatch by `artifact_schema_version` :1651; `YamlExecutionArtifacts.
  write_cold` :1896, `read_history` cold branch :1936.
- `host/cold_lab.py`: `ColdInputs`/`StoreColdInputs` :50-80, `_base` :93, projections :125/:137, schema-6
  render/parse :173/:219, `delay_event_id` :276. `host/cold_publication.py:verify_cold_inputs` :83 (content SHA
  check :97). `host/lab_app.py` `cold_inputs=` composition. `packs/ev_charger.py:EvParameters` :70.

## Anchors for commit 5
- Replay beside `backend/assetops_backend/cold_replay.py` / `cold_replay_api.py`; mounted in `main.py` :493
  (`build_cold_replay_router`, `no_owner_principal` import :57); Lab router composed :470.

## Run 4 record

Branch `task/W2-05b-ev-producer`, worktree `AssetOpsV1-review5`. Not merged.


## Run 4: q2 corrections (`f2eafdee` "W2-05b q2 corrections")
- N1: `main.create_app(..., ev_access=development_access, ev_owner=no_owner_principal)` passed to
  `build_simulator_lab_router`. Tests `test_w205b_ev_scenarios.py::composed` (real `create_app` over
  `InMemoryFoundationStore` with imported `fixtures/w2/ev-lab-001.yaml`): default 403 `SITE_SCOPE_FORBIDDEN`, no rows;
  injected `code == "EV-LAB-001"` owner 200 with six labels; legacy and COLD-LAB-001 403; injected 401.
  **Commit 5 still owes**: pass the same `ev_access`/`ev_owner` from `create_app` to the EV replay router, and the
  walkthrough's isolated ASGI app must call `create_app` with the Site-scoped owner (no global flag).
- N3: `SimulatorLabFrame.tsx` sibling Panel `EV charging run setup` (`headingId simulator-lab-ev-run-setup-heading`)
  after the cold panel, before `What this workspace is`; ruled sentence via the Panel `description` prop (renders as
  the v69 panel sub-line, smaller than the cold panel's body copy - reviewer to confirm this reading of
  "description"). Cold panel cold-only. Frame test in `simulatorLabWorkspaceEntryPoint.test.tsx` asserts both
  regions, copy, one link each, and order. Captures (viewed, not committed): scratchpad `cap/app-1440.png`,
  `app-390.png`, `mock-1440.png`, `mock-390.png`; no overflow (scrollWidth = viewport).
- N8: `packs/ev_charger.py` `step` refuses ordinals unless exactly `range(prev+1 or 0, +len(forcing))`, and any
  ordinals at the closing snapshot; `forcing_ordinal` set only when rows applied. Document shape already matched N8.
  Tests: ordinal guard, ordinal progression (null then carried to 09:00), 09:00 closing snapshot (base 1/3 kW ->
  `181/3`, `1/3`, `239/3`), fractional final quantum (`81/2`, `27/40`), pinned complete-case digest
  `6fc2f2a8...14adab2c` over 61 documents with key order and reduced-rational text. Test helper `forced` supplies
  continuing ordinals so earlier refusal tests still refuse for their own reason.
- Counts: backend ev_scenarios+lab gate+s1 cutover+scenarios API 155; simulator ev/cold pack+public transform 91;
  host `test_ev_publication` 27; frontend 5 files 150; `tsc --noEmit` 0; `check-all.ps1` 10/10.
- Non-vacuous: disabling the ordinal guard fails its test; default `ev_owner` -> True fails 2; `ev_access` ->
  `development_access` fails the injected-401 test. No seed DB created. Q15-Q17/N9-N12 untouched.

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
