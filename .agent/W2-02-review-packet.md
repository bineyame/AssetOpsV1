# W2-02 review packet - cold causal producer and public replay

Task: `tasks/W2-02-cold-producer.md`. Binding spec: `.agent/W2-02-build-spec.md` (`D-2026-10-17-w2-02-buildspec`,
q4/q5 merged). Branch `task/W2-02-cold-producer`, worktree `AssetOpsV1-review2`. Final code revision: `7b0c9f79`.
USER_REVIEW_REQUIRED: true (after independent review, in the later owner W2 walkthrough). Not merged.

## Outcome delivered

A registered cold Lab run now reaches ordinary S2 accepted evidence, and an explicit-run replay route reads it back.
The chain is COLD-LAB-001 (registered fixture plus an immutable v4 binding revision), then a strict `cold-scenario/1`
Draft, then Host Lab start (frozen re-read, one-shot 61-boundary window, schema-6 artifact). Next a real gateway
process turns DeviceReport v2 into SourceEnvelope V4 and seals Stage. Then come SYSTEM_LAB_RELEASE publication and
gateway release, the gateway's own TLS upload of Batch V2, and the S2 ledger. Finally
`GET /api/sites/{code}/cold/replay?run_id=` serves the result. The six scenarios are pinned as canonical
`cold-replay-manifest/1` files. No assessment, Finding, migration or new writer.

## Commits (spec order)
- (0) `ff0a4906`, `4d708c31`: step 0, the W2-01 re-review Lows and the recapture.
- (1) `d23db231`, `4906d6a5`: the COLD-LAB-001 fixture, the v4 binding revision and the strict scenario parser.
- (2) `9e827421`, `1ad4a075`, `bd32d369`, `a1f64a6d`: the cold pack, observation, profile pair, run identity,
  cold-scenarios API and client.
- (3) `d3795c67`, `623c12d4`, `cb166a1d`, `73a5cae7`, `68740276`, `93a3aedc`: report v2, the gateway V4 branch,
  host verification and series, the `cold-` IDs, the Lab cold run-setup route, and the cold start, artifact and
  late release.
- (4) `12404684`, `c9cdc96d`, `e2392288`, `7b0c9f79`: the replay read and API, the six manifests, the Postgres
  proofs, the V4 header path in run publication, the Lab-gate path list, and the host upload-credential helper.

## Files materially changed in (4)
- `backend/assetops_backend/cold_replay.py`: `ColdReplayService`. It holds no SQL. The run profile comes from the
  frozen run. The publication, batch and disposition checks answer 503 when they fail. The digest is computed per
  the spec.
- `backend/assetops_backend/cold_replay_api.py`: `build_cold_replay_router(service, scope, *, access, owner)`, plus
  `no_owner_principal` (production) and `development_owner` (tests only).
- `backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py`: SELECT-only `cold_replay_rows` and
  `cold_replay_run_referenced`.
- `backend/assetops_backend/evidence/composition.py`: `build_cold_replay_reader`.
- `backend/assetops_backend/main.py`: the route is mounted only under `simulator_lab_enabled`, with
  `owner=no_owner_principal`.
- `backend/assetops_backend/evidence/publication.py`: `simulation_records` now reads schema-4 envelopes by their
  header, the same rule `seal_batch_v2` uses. Without this, every cold release was refused (`EnvelopeRejected`
  "v4 is not a V3 envelope").
- `backend/tests/test_w202_cold_replay_api.py` (13, fakes) and `backend/tests/test_w202_cold_replay_postgres.py`
  (12, real chain).
- `backend/tests/test_simulator_lab_gate.py`: the Lab-gated served-path list now names the cold replay route.
- `host/tests/gateway_process.py`: `write_upload_credential`. The backend proof cannot import `assetops_gateway`
  (dependency direction), so it writes the owner-only upload credential through the host's helper.
- `contract-fixtures/w2/cold/{normal,excursion,backup-failed,missing-probe,late-reading,contradictory}.json`.

## Acceptance criteria
| Criterion | Status / evidence |
| --- | --- |
| Cold pack laws, door heat 0.02, hysteresis/delays, physical refusals | Met. `simulator/tests/test_cold_pack.py::{test_normal_thermal_balance,test_door_heat_exact_002,test_hysteresis_and_delays,test_invalid_capacity_transition_residual_temperature}` |
| Six strict scenario documents, digest ignores YAML format, wrong asset/observation refused | Met. `backend/tests/test_w202_cold_scenario.py` (the three named tests) |
| DeviceReport v2 round trip, v1 bytes unchanged, private field refused | Met. `contracts/tests/test_gateway_report_v2.py` (the three named tests) |
| Gateway allocates the v4 sequence, report-key replay, conflicting key held, v3 branch unchanged | Met. `gateway/tests/test_cold_v4_admission.py` (the four named tests) |
| Host, Lab and kernel select the same frozen pack; unknown identities refused before Draft; old fixtures keep their bytes | Met (commits 2-3). `host/tests/test_cold_lab_execution.py` (10), `test_cold_dispatch`, kernel conformance |
| Six manifests pin envelope/batch digests, receipts, accepted IDs, window and assertions; the second clean replay is byte-identical | Met. `test_six_registered_replays[*]` (6) compares canonical bytes with the pinned files. Non-vacuity: a one-byte manifest edit (`seed` 20417 -> 20418) failed the normal case, then was reverted |
| Expected points: 13 / missing-probe 7 / late 12 then 13; normal start 19:07 and transfer 19:08; failure 19:05; excursion T(19:15)=4.1>4.06 and T(19:20)=4.2>4.15; late source 19:20 published 20:10 | Met. Manifest `assertions`, cross-checked against the S2 records route |
| Duplicate: gateway `ALREADY_ADMITTED`; idempotent central re-upload; no second disposition set; digest stable | Met. `test_second_release_duplicate` |
| Late release keeps source 19:20, publishes at 20:10, S2 receive time is later, 12 -> 13 | Met. `test_late_source_time_and_receive_time` |
| `EVENT_ID_CONFLICT` and `SESSION_ID_CONFLICT` count as conflicts in the Site Evidence and rejection-list routes | Met with a deviation (session path, below). `test_event_conflict_counts`: the rejection list is exactly these two kinds; Site Evidence `counts` is conflicts 2, rejected 0 |
| Owner/tenant gate: 401/403/404; production has no ownerless read; Lab gate | Met. `test_owner_and_tenant_gate` (also real `create_app`: 403 with the Lab on, 404 with it off) and the API unit tests |
| No private truth in Stage, Batch, accepted rows or replay; digest recomputed from persisted text and dispositions | Met. `test_public_digest_no_private_truth` |
| Rule 8: SELECT-only reader; the ledger stays the sole writer; foreign writers fail; v4 gateway-to-ledger probe | Met. Probes plus `test_v4_gateway_to_ledger_probe` (one V4 measurement and one V4 event, with allocation, canonical Batch V2, dispositions and accepted read) |
| One full backend suite on the final revision, JUnit zero failed/skipped | See Checks |

## Checks run (final revision `7b0c9f79` unless stated)
- Rule-8 probes: `python tools/writer_guard_probes.py --seam`, clean tree, exit 0. 83 CAUGHT, 6 ALLOWED controls,
  including every `w200 foreign accepted/rejection/disposition writer` probe. The tree was restored afterwards.
- Architecture check: `tools/check-architecture.ps1` passed at `12404684`. `check-all` (below) covers the final
  revision.
- Focused W2-02 Postgres tests on `assetops_w202c_test`: `test_w202_cold_replay_postgres.py` 12 passed.
  Adjacent: `test_s405_publication_postgres`, `test_s405_resolver_postgres`, `test_s4_power_demo_case_postgres`,
  `test_w202_cold_replay_api`, host `test_cold_lab_execution`, `test_registered_post_run_release`: 69 passed.
- Frontend: `npm.cmd test` exit 0, 84 files, 2153 tests passed, 171 s.
- **Full backend suite** (real Postgres; private base `assetops_w202c_test`; keep-awake running; no other pytest).
  Command: `python -m pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q -rfE --durations=30
  --junitxml=.pytest-junit.xml`.
  - Final run at `7b0c9f79`: wall 1552 s (25.9 min). JUnit: 2705 cases, 0 skipped, 0 failed (2705 passed).
  - Run 1 at `c9cdc96d` was stopped at the TESTING.md 20-minute cap at 55%. That was progress, not a stall; the
    recent recorded runs on this host take 37-62 min.
  - Run 2 at `c9cdc96d`, cap raised to 75 min: 2192 s, 2704 passed and 1 failed. The failure was
    `test_simulator_lab_gate::test_enabling_the_gate_adds_only_the_simulator_lab_surface`: the new Lab-gated route
    was not in the expected path list. `e2392288` fixes the list.
- Other suites at `e2392288` (test-only changes since then), with JUnit counts:
  - simulator: 271 cases, 0 skipped, 0 failed (13 s).
  - gateway: 233 cases, 0 skipped, 0 failed (50 s).
  - host: 706 cases, 0 skipped, 0 failed (784 s).
  - `contracts/tests`: 6 cases, 0 skipped, 0 failed.
- After `7b0c9f79`: `test_w202_cold_replay_postgres.py` 12 passed and host `test_registered_gateway_delivery` 4
  passed.
- `tools/check-all.ps1 -Python <plan2 venv>` at `7b0c9f79`: exit 0, 10 of 10 guards PASS (architecture,
  navigation, agent workflow, registry, delivery and mock-gap fixtures, missing-claim scan, evidence width, screen
  ledger). The first check-all, at `e2392288`, failed dependency direction: the backend proof imported
  `assetops_gateway`. `7b0c9f79` fixes this.
- `var/sites` was copied from the main worktree for the suites and removed afterwards. `assetops_w202c_test` was
  dropped at the end.

## Known deviations
1. **[Closed in the fix round by the q6 ruling - see Fix round.] Production registered basis refuses a COLDCHAIN snapshot (open Architect question, High).**
   `binding_service.acquisition_snapshot` applies the MINIGRID `configuration_gaps` (SITE_TYPE_UNSUPPORTED and the
   electrical component gaps) to COLD-LAB-001. As a result `RegisteredLabBasis` refuses every cold Draft in
   production composition. The Postgres proofs lift only that gap check, test-only and only for a COLDCHAIN Site
   (`open_cold_snapshot_gate`). The stored snapshot bytes, hash and pinned-identity checks still run. How COLDCHAIN
   readiness should gate the acquisition snapshot is not specified, so it was not decided here.
2. **Session conflict vector path.** COLD-LAB-001 binds no session channel, and the gateway refuses an unbound
   channel, so the gateway cannot admit an EV session report. The event conflict goes through the real gateway. The
   session vector is posted to the ordinary S2 ingestion route under the gateway credential, with the reserved EV
   session channel bound test-only, as W2-00's acceptance already does (`basis_from_snapshot` patch). The Site
   Evidence and rejection-list routes are real.
3. **V4 header path in `simulation_records`** (`evidence/publication.py`). This is a production change outside the
   spec's file list. Without it the preauthorized release could not attest a V4 Stage. It uses the same dispatch
   rule as `seal_batch_v2`. The S4-05 publication tests are unchanged and pass.
4. **Manifest field readings.** `batch_sha256` is each batch's committed `payload_sha256`. `event_kinds` are
   accepted event kinds ordered by source time, ties in receipt order. `unavailable_count` counts accepted
   `UNAVAILABLE` records. `high_1915`/`high_1920` are filled only for `excursion`; `late_*` only where a record was
   published at or after 20:10; `start_result_at`/`transfer_result_at` take the first such event. Manifests are
   written only with `ASSETOPS_W202_WRITE_MANIFESTS=1`.
5. **Replay ladder readings.** Order is access (401/403), then the owner check (403), then parameters (422), then
   Site (404), then run. Another tenant's, another Site's, or a non-cold run is 404 `RUN_NOT_FOUND`. A cold pair
   without its frozen observation identity or scenario SHA is 503. A missing run that a publication names is 503.
   No separate "source gate" seam exists: the gate is the REGISTERED_SIMULATION filter plus the access and owner
   checks. Production composes `access=development_access` with `owner=no_owner_principal`, so it answers 403.
6. **Determinism controls (test-only).** A per-case UUID counter replaces `uuid4` in loaded backend and host modules
   and the run-ID allocator. The gateway epoch is `cold-<case>`, and setup clocks are fixed. Production allocation is
   unchanged. Each case runs in a fresh cloned database.
7. From commit (3), per `.agent/W2-02-phase-4-handoff.md`:
   - The spec names `JsonExecutionArtifacts`; the store is `YamlExecutionArtifacts`, and schema 6 is written there.
   - The Draft cold projection uses `inputs_identity=run_identity_sha256(run)` and the empty digest SHA-256 of
     canonical `[]`.
   - The host-only failure kind `PUBLICATION_REFUSED` is excluded from the simulator reachability guard and reached
     in the host test.
   - The run-setup UI readings: the profile string is split at the last `/`; the basis is read at the document
     `start`; the result clears only on a Site change; the Lab home links "Set up a cold-chain run"; the
     `settled.ts` loading pattern is widened for two loading sentences.
8. From commit (3), phase 3: `ColdExecution(pack, *, runner, ...)` takes the pack from the composition leaf, because
   the kernel names no pack (dependency guard). The Q1-Q5 outcomes are as merged into the spec (q4 route, q5
   `cold-` IDs).
9. From commit (2), phase 2. These are pack interpretations:
   - A GENERATOR_FAILURE latent fault gives START_RESULT/FAILED at the timeout.
   - Restore switches transfer to GRID immediately and stops the generator.
   - Compressor kW equals the cooling capacity while RUNNING on a powered bus.
   - Grid and transfer events share the outage correlation.
   - Ambient is reported every 5 minutes.
   - The cold Draft carries `signal_mappings=selection.signal_mappings`, as the registered legacy path does.

## Residual risk
- Deviation 1 means the production Lab cannot yet freeze a cold run against the real registered basis. The proofs
  show every other stage of the chain.
- `backend/TESTING.md`'s 20-minute `-n 2` cap is stale on this host. The final run took 26 min. See Checks.
- `missing-probe` shows its gap as 7 of 13 points with `unavailable_count` 0. The gap is absent points, not
  UNAVAILABLE records.

## User-review focus
- Rule on deviation 1: how COLDCHAIN readiness gates the acquisition snapshot.
- Accept or redirect deviation 2 (session vector path) and deviation 3 (header path in run publication).
- The pinned manifest `assertions` against the §4 scenario expectations.

## Fix round (review `.agent/W2-02-review.md` RETURN; q6 ruling `D-2026-10-17-w2-02-buildspec`)
Commits: `ada7ec68` (q6 gate), `5e2cae92` (M1), `afb76402` (M2, L3), `273ac204` (L4-L6).

| Item | Change | Proof |
|---|---|---|
| Deviation 1 (q6) | `binding_service.acquisition_snapshot` dispatches by `site.site_type`: COLDCHAIN derives gaps from `cold_snapshot_gaps` (W2-01 `cold_foundation_document` on the *selected* revision and binding set, `assets_by_code`, no contact); every `blocking` message refuses, current or historical; MINIGRID `configuration_gaps` is never called for it. Role set other than `cold-roles-1` refuses (`BINDING_ROLE_SET_UNKNOWN`); a revision the cold rule cannot evaluate refuses (`COLD_FOUNDATION_UNEVALUABLE`). Absent set / mismatched revision keep their existing refusals. `open_cold_snapshot_gate` removed. | Six Postgres proofs pass without the lift: `test_w202_cold_replay_postgres.py` 12 passed (189 s). New `test_w202_cold_snapshot_gate_postgres.py` 14 passed: pass case with `configuration_gaps` patched to raise; ROOM_MISSING, PROBE_MISSING, POLICY_MISSING, START_EVENT_MISSING, ROLE_UNBOUND x3 (grid_power_event, generator_state, backup_bus_state), unknown role set, unevaluable revision, mismatched revision; TRANSFER_UNREPORTED / ambient / compressor_power nonblocking. Non-vacuity: with the pre-fix `binding_service.py` 13 of 14 fail (the mismatched-revision case is pre-existing behaviour). |
| M1 | Legacy branch of `create_draft_run` refuses `VERSION_UNAVAILABLE` ("Cold-chain profiles run only from a cold-scenario/1 document. Profiles are not substituted.") when the model profile ID is `cold-thermal` or the publication profile ID is `cold-publication`. | `test_a_cold_profile_with_a_legacy_scenario_is_refused_before_draft` x3 (cold/cold, cold/legacy, legacy/cold), each `store.written == []`. Non-vacuity: pre-fix `service.py` -> 3 failed. |
| M2 | `ColdRunSetupFrame`: the button-side reason is suppressed for the choose-site, unavailable and empty states (button stays disabled); the Foundation version fact shows the version or "Not available" (see Fix-round deviation F1), never `blockedReason`. | `states each setup message exactly once` (`getAllByText(...).length === 1` for the three copies and the basis-loading reason; fact text "Not available"). Non-vacuity: pre-fix frame -> fails with 2 matches (`<p>`, `<span>`). |
| L3 | Choice label is `display_name` only (scenario ID stays a read-only fact). Reason-code line kept (optional in the review). | coldRunSetup tests select the radio by "Normal". |
| L4 | `("STARTING","STOPPED")` added to `_GENERATOR_MOVES`; restore calls `check_move("generator", ..., "STOPPED")`. | simulator cold tests 6 passed; six manifests unchanged byte for byte. |
| L5 | `build_cold_replay_reader` returns a two-method facade (`cold_replay_rows`, `cold_replay_run_referenced`) over the ledger. | `test_composed_reader_exposes_only_the_two_select_reads`; non-vacuity: pre-fix composition -> fails. |
| L6 | `_start_cold` maps a `PhysicallyUnacceptable` from `cold_execution` to `LabControlRefused("FROZEN_RUN_NOT_RECONSTRUCTIBLE")` before any Stage output. | `test_valid_values_driving_the_world_out_of_bounds_refuse_before_any_stage` (capacity 0.0001 kWh/degC, backup-failed case): refused, no groups staged, no schedule, NOT_STARTED. Non-vacuity: pre-fix host -> fails. |

Reading (not a design choice beyond precedent): L6 reuses `FROZEN_RUN_NOT_RECONSTRUCTIBLE`, the kind
`verify_cold_inputs` already uses for physically invalid cold parameters; the spec names no kind and no new
contract kind was added. If the Architect wants a distinct kind, it is a one-line change plus a contract entry.

Fix-round deviation F1 (Low): the review asked for "Not available yet" in the Foundation version fact. That
phrase is reserved missing-capability copy; `check-all` failed the missing-claim scan on it (`untagged_copy
ColdRunSetupFrame.tsx:350`, register a mock_gaps gap). A pending or refused basis is not a missing capability,
and adding a gap or a scan exemption is a guard/design change, so `5e294b3f` uses the frame's existing fallback
"Not available". The say-it-once intent (never `blockedReason` in the fact) is met.

### Fix-round checks (final code revision `5e294b3f`; nothing but this packet changed after it)
- Full backend suite, real Postgres (private base `assetops_w202fix_test`, keep-awake running, no other pytest):
  `python -m pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q -rfE --junitxml=.pytest-junit.xml`
  at `273ac204` (backend unchanged since): wall 1552 s (25.9 min); JUnit 2723 cases, 0 skipped, 0 failed,
  0 errors.
- Simulator `tests`: JUnit 271, 0 skipped, 0 failed (4 s). Host `tests`: JUnit 707, 0 skipped, 0 failed (757 s).
  Both at `273ac204` (unchanged since). Gateway and contracts untouched in this round; not re-run.
- Frontend `npm.cmd test` at `5e294b3f`: 84 files, 2156 tests passed, exit 0 (140 s). (Also 2156 passed at
  `273ac204` before F1.)
- `tools/check-all.ps1 -Python <plan2 venv>` at `5e294b3f`: All 10 guards passed (at `273ac204` it failed the
  missing-claim scan and its fixture check on the F1 copy, fixed by `5e294b3f`).
- Rule-8 probes `tools/writer_guard_probes.py --seam` at `5e294b3f`: exit 0, 83 CAUGHT, 6 ALLOWED controls,
  tree restored.
- Focused: `test_w202_cold_replay_postgres` 12 passed (no lift); `test_w202_cold_snapshot_gate_postgres` 14;
  `test_w202_cold_run_identity` + `test_run_setup` 107; `test_w202_cold_replay_api` 14; host
  `test_cold_lab_execution` new case; simulator cold 6; `coldRunSetup.test.tsx` 10.
- `var/sites` copied for the suites and removed; `assetops_w202fix_test` dropped.
