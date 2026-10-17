# W2-02 handoff after commit (2) part 1 — PARTIAL (context budget)

Branch `task/W2-02-cold-producer`, worktree `AssetOpsV1-review2`. Read `.agent/W2-02-build-spec.md` (binding) and
`.agent/W2-02-phase-1-handoff.md` (commit-1 anchors, env notes). Commit (2) part 1 is `9e827421`. Resume at
"Remaining in commit (2)" below; then commits (3) and (4) as the spec orders them.

## Landed in 9e827421 (all focused tests pass)
- `simulator/assetops_simulator/packs/errors.py`: `PhysicallyUnacceptable`; `packs/fuel.py` re-exports it.
- `packs/cold.py`: `ColdParameters.from_properties({key: (value_text, unit)})` (all 13 required, exact units,
  whole minutes), fixed delays gen 2 / transfer 1; `ColdState` (+ private lifecycle/energy bookkeeping, per-channel
  transition `ordinals`, `outage`/`door_cycle` correlation counters); `ColdPack.step(state, forcings,
  transition=True, start=)` in spec minute order; `run_window(pack, start, end, initial_temperature, ambient,
  forcings) -> ColdRun(transitions, records)` with the 20:00 closing boundary (`transition=False`).
  `PublicRecord` = exact public record (measurement or event: `record_kind, outcome, component_id, actor,
  transition_ordinal, correlation_key=("outage"|"door-cycle", n)`). `PROBE_FAILURE` forcing exists for unit tests only.
  Interpretations (record in packet Known Deviations): a GENERATOR_FAILURE forcing is a latent fault: request ->
  STARTING, FAILED + START_RESULT/FAILED at the 5-min timeout; restore at 19:35 switches transfer to GRID
  immediately (TRANSFER_RESULT emitted) and stops the generator; compressor power kW = cooling capacity while
  RUNNING and bus powered; grid/transfer events share the outage correlation; ambient-probe published every 5 min.
- `observation/transform.py` (end): `cold_value_text`, `ColdObservation`, `cold_observations(records,
  observation_rows)` — rows need datetime `at`/`release_at` (convert from the parser's strings). ADD ordinal =
  channel max ordinal + 1; correlation = the attempt's (latest start-event at/before `at`). HOLD publishes at
  `release_at`; others at source_time + 3 s.
- `gateway/mappings.py`: `V4MappingSet`, `COLD_V4_GATEWAY_MAPPINGS` (11 channels, schema 4);
  `gateway_mapping_for('cold-publication',1)` returns it; other cold-publication versions raise `LookupError`.
- `kernel/execute.py` (end): `COLD_PROFILE_PAIR`, `execution_path_for(model, publication) -> "COLD"|"MODEL_SPEC"`
  (half-cold pair -> `ProfilePairMismatch`), `ColdExecution(parameters, start=, end=, initial_temperature=,
  ambient=, backup_enabled=, forcings=)` with `.records`.
- `backend/.../runs/profiles.py`: `COLD_THERMAL_MODEL`, `COLD_PUBLICATION_PROFILE` (cadence 5, 4 record channels,
  `RUN_VIRTUAL`), appended to `MODEL_PROFILES`/`PUBLICATION_PROFILES`.
- `runs/models.py`: `FrozenScenarioBinding.scenario_sha256`, `FrozenProfileBinding.observation_profile_id/
  _version/observation_sha256` (all default None). `runs/parsing.py`: `_render_present` (omit-never-null) in
  `render_run_document`; `_parse_cold_identity` (all four or none; lowercase 64-hex).
- `backend/tests/test_run_setup.py`: the four keys classified not_rendered (summary audit).
- `simulator/tests/test_cold_pack.py`: the four named tests + probe failure + transform test (6 pass).
- Tests run: simulator suite + run_setup/addressed_bindings/component_properties/execution_contract_alignment/
  model_owned_needs/run_binds/run_store_loader/s405 + host test_host_execution/test_lab_execution: all pass.

## Remaining in commit (2)
1. `runs/service.py`: replace the `_resolve_scenario` cold refusal (~:571) with dispatch in `create_draft_run`
   (~:407) to a cold-only freeze: registered Site only (selection not None) and `site.site_id == doc.site_code`;
   request model/publication == doc `cold-thermal/1`/`cold-publication/1` exactly; scenario version, seed,
   start/end == doc, timestep 1; else `refuse(...)` before Draft. Build `DeterministicIdentity` (fields at
   models.py ~:888; legacy builder at service.py ~:1058) with empty legacy projections, `scenario_sha256=doc
   digest`, observation `cold-observation`/1 + `observation_sha256` (define: SHA-256 of canonical JSON of the
   doc's `observations` rows + profile id/version — not specified; or ask), `registered_basis=selection.basis`
   (carries foundation_revision_id and binding_set_revision_id = the v4 revision). Then `_decide` / READY.
   The thirteen Foundation values: host must read them at execution from the frozen Foundation revision (basis
   `foundation_revision_id` + `content_sha256`), and the cold document by id verified against `scenario_sha256`.
2. Run-identity round-trip test (old run omits keys; cold run renders/parses; bad sha refused) and confirm old
   golden vectors (`run_identity_sha256`, `test_scenario_fingerprints.py`) unchanged.
3. `host/execution_adapter.py:model_for` (~:138) / `publication_profile_for` (~:154) and
   `host/lab_execution.py:_model_for` (~:1978): explicit cold dispatch via `execution_path_for` (cold run never
   resolves a ModelSpec).
4. `simulator_lab_api.py`: `GET /api/simulator-lab/cold-scenarios?site_id=` per the spec's "Lab choice closure"
   (labels Normal/Excursion/Backup failed/Missing probe/Late reading/Contradictory; empty for other/unregistered
   Site; store errors stay unavailable) + frontend Lab choice client call after Site selection; API tests.

## Then
- (3) DeviceReportV2 (`contracts/.../gateway_report.py`), gateway `_admit_in` v2 branch (service.py ~:583-650:
  v1 parser at :603, `binding_for` at :610, sequence at :647), host `_stage_registered_virtual` (~:2501) cold
  path via `RegisteredGatewayPublisher.publish_in_boundary_order` (host/gateway_publication.py:128; IPC
  `admit_texts` passes only snapshot sha). Gateway/source IDs: gateway `edge-cold-lab-001`, sources = device ids
  (foundation_service.py:183-208); only the pinned snapshot names them.
- (4) cold replay read, manifests, six-case proof, full suites, packet.
