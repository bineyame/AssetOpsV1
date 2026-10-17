# W2-02 handoff after commit (3), partial: report, gateway and host verification landed; Lab session wiring blocked on 4 questions

Branch `task/W2-02-cold-producer`, worktree `AssetOpsV1-review2`. Binding: `.agent/W2-02-build-spec.md`. Env:
`.agent/W2-02-build-brief.md`. The previous handoff (`W2-02-phase-2-handoff.md`) still holds the anchors for the
commit-(1)/(2) work, the open UI question and the pack interpretations for Known Deviations.
Commit-(3) commits: `d3795c67` (report v2 + gateway), `623c12d4` (host verification + series), `cb166a1d`
(guard fixes).

## Landed (focused tests pass; architecture check passes)
- `contracts/assetops_contracts/gateway_report.py`: `DeviceReportV2`, `device_report_v2_text`,
  `parse_device_report_v2_text`, `device_report_schema_version(text)` (dispatch only), `cold_event_id`,
  `cold_report_key` (`cold:` + SHA-256 of canonical tuple, per spec). v1 untouched.
  Test `contracts/tests/test_gateway_report_v2.py` (6; new `contracts/tests/` dir, so check that check-all/the
  full run collects it).
- `gateway/assetops_gateway/snapshot.py`: `Binding.v4_metadata` (the five keys as stated, or None; not compared).
- `gateway/assetops_gateway/service.py`: `_admit_in` dispatches by report schema. v2 goes to `_check_report_v2`,
  which runs before duplicate lookup and sequence allocation: timing/validity, exact metadata ==
  `V4_CHANNEL_MAPPINGS[...]`.metadata() (else `MAPPING_INCOMPATIBLE`), family/measurement, record kind
  (`RECORD_KIND_UNSUPPORTED`), unit (`UNIT_INCOMPATIBLE`), enum/decimal value, and a provisional `_envelope_v4`
  parse. Then the existing report-key dedup, the same sequence row, `v3_message_id` and
  `canonical_envelope_v4_text` into `envelope_outbox`. The v1 path is now `_envelope_v3_text` (moved without
  change). Test `gateway/tests/test_cold_v4_admission.py` (5): the 4 spec names plus a metadata-missing hold. The
  mixed V3/V4 group seals as one batch.
- `host/cold_publication.py`: `verify_cold_inputs(run, revision, definition)` refuses with
  `FrozenRunNotReconstructible` on any mismatch: revision missing, wrong ID, stored or recomputed `content_digest`
  != frozen SHA, document missing, wrong scenario/version, `scenario_sha256` mismatch, recomputed
  `observation_sha256` mismatch, or the 13 values missing or invalid. No fallback. `cold_reports(verified)` runs
  `ColdExecution` and `cold_observations`, then gives `ColdReport(report_key, report_text, device_id, signal_id,
  source_time, published_at, held)` in publication order. `report_of` and `cold_correlation_id` are here.
  Test `host/tests/test_cold_publication.py` (3) asserts:
  - normal: 13 probe points, start SUCCEEDED 19:07, transfer 19:08;
  - excursion: FAILED 19:05;
  - missing-probe: 7 points;
  - late-reading: held 19:20, published 20:10;
  - contradictory: 2 event IDs, 1 correlation;
  - determinism;
  - every refusal.
- Guard fixes (both left by commit (2)): `ColdExecution(pack, *, runner, ...)`, because the kernel no longer
  imports `packs.cold` and the host hands in `ColdPack`/`run_window`. `COLD_SCENARIOS_API_PATH` now lives in
  `frontend/src/shell/simulatorLabRoutes.tsx` (re-exported by the client). Vitest client 5/5, tsc clean.
- Adjacent tests pass: gateway wire/ledger/v4/publication-clock, host `test_cold_dispatch`,
  `test_registered_gateway_publication`, simulator `test_cold_pack`.

## Questions for the Architect (blocking the rest of commit (3))
1. **Spec conflict: event ID grammar.** The spec sets event ID = `cold:` + SHA-256. `SourceEnvelopeV4` validates
   `event_id`/`correlation_id` with `_IDENTIFIER` = `[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?`, which has
   no `:`. Every cold event is therefore held `CORRELATION_INVALID` at `payload.event_id`. Report keys are fine,
   because the report-key grammar allows `:`. The choice is between two options:
   - a `cold-`/`cold.` prefix, with the W2-00 parser unchanged;
   - widening the V4 identifier grammar, which is a W2-00 contract change and needs a DB CHECK review.
   `cold_event_id` currently emits the spec form; the gateway tests use V4-valid literal IDs.
2. **Correlation ID encoding** is unspecified. Implemented: `cold:` + SHA-256 of canonical
   `[scenario_sha256, kind, ordinal]`, where kind is `outage` or `door`, from `PublicRecord.correlation_key`.
   The `:` from Q1 applies here too. Confirm the encoding or give the exact form.
3. **Lab session and projection for a cold run.** `HostLabExecution.start/step/run_to_end` return a
   `LabProjection` built from an `Execution`. `_execution_status`, which `release_registered` requires to be
   COMPLETED, reads the YAML execution artifact (`render_projection`/`parse_projection`). The cold run has no
   `Execution`/`ModelSpec`. Specify:
   - the cold `LabProjection` values: status, boundaries, `inputs_identity`, `content_digest`,
     `observation_series_digest`, `private_state`/observations/signals (empty?);
   - what the execution artifact stores;
   - whether the whole window executes at `start` (`ColdExecution` runs it at construction), and what `step`
     does.
4. **Host composition for the frozen re-read.** `HostLabExecution` today has no Foundation or scenario reader.
   Confirm a new injected port (e.g. `cold_inputs=` with
   `foundation_revision(tenant_id, site_record_id, revision_id)` over the Postgres foundation store
   `revisions()`, and `cold_scenario(id, version)` over `ScenarioCatalogService`), composed in
   `host/lab_app.py:build_app`. Also confirm that a refusal is `LabControlRefused("FROZEN_RUN_NOT_RECONSTRUCTIBLE")`.

Planned staging interpretation, for confirmation with Q3. `_stage_registered_virtual` (lab_execution.py ~:2505)
gets a cold branch:
- ordinary reports are grouped by their `published_at` (source time + 3 s), as the boundary instants;
- held reports become `DelayedReport(scheduled_release_at=release_at)`;
- the world-reached instant is the last ordinary `published_at` (20:00:03);
- then the existing `_release` runs and calls `RegisteredGatewayPublisher.publish_in_boundary_order`.
The gateway publisher currently adapts `DeviceObservation` via `keyed_reports` (host/gateway_publication.py). The
cold branch passes the v2 texts directly, so check that `publish_in_boundary_order` accepts texts as-is (it takes
`wanted=[(instant, [texts])]`).

## Remaining, in order
1. After Q1-Q4: change the ID format if told to, then do the host start routing:
   - in `start` (lab_execution.py ~:2122), before `_model_for`, when `execution_path(run) == "COLD"`: read the
     inputs, then `verify_cold_inputs` (refuse before any Stage), then `cold_reports`;
   - the cold session and projection as answered;
   - the cold branch in `_stage_registered_virtual` as above;
   - `advance_publication` releases the late reading at 20:10.
   Add a host test with a fake gateway: no Stage output on refusal; 12 points before the release and 13 after.
2. Lab run-setup UI wiring (separate Architect answer; phase-2 handoff Q1-Q3): wire
   `createColdScenarioChoiceClient` after Site selection, with a `settledScreen` test, vitest and tsc.
3. Commit (4), per the spec's "Replay read, migrations and proof":
   - `backend/assetops_backend/cold_replay.py:ColdReplayService` and `cold_replay_api.py:build_cold_replay_router`;
   - six manifests at `contract-fixtures/w2/cold/`;
   - `backend/tests/test_w202_cold_replay_postgres.py` (6 named tests) on `assetops_w202c_test`, with `var/sites`
     copied in and removed afterwards;
   - the rule-8 probes plus a v4 gateway-to-ledger probe;
   - full backend, simulator, gateway and host suites (one at a time, keep-awake, 2x cap) and `check-all`;
   - packet `.agent/W2-02-review-packet.md` (git add -f). Its Known Deviations: the pack interpretations from the
     phase-2 handoff, the `signal_mappings` choice, the Q1/Q2 outcome, and the `ColdExecution` signature change
     for the dependency guard.
