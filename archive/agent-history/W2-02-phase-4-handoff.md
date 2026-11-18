# W2-02 handoff after commit (3) complete; commit (4) not started

Branch `task/W2-02-cold-producer`, worktree `AssetOpsV1-review2`. Binding: `.agent/W2-02-build-spec.md` (q4/q5 merged:
"Cold Lab execution and frozen re-read", "Commit (4) exact contract"). Env: `.agent/W2-02-build-brief.md`.
Earlier anchors: `W2-02-phase-2-handoff.md` (pack interpretations), `W2-02-phase-3-handoff.md` (report v2/gateway).

## Landed since phase 3 (focused tests pass; architecture check passes)
- `73a5cae7` event/correlation IDs `cold-` + SHA-256 (report keys keep `cold:`); test asserts V4 grammar.
- `68740276` frontend `/simulator-lab/cold-run-setup` (`frontend/src/shell/ColdRunSetupFrame.tsx`,
  `__tests__/coldRunSetup.test.tsx` 9/9, settledScreen; 177/177 across the 5 touched vitest files; tsc clean).
  Literal readings for the packet: profile string split at last `/`; basis read at the document `start`;
  result cleared only on Site change; link panel on the Lab home ("Set up a cold-chain run"); `settled.ts`
  loading pattern widened for the two new loading sentences; `SitePicker` etc. exported from `RunSetupFrame.tsx`.
- `93a3aedc` host cold start:
  - `host/cold_lab.py`: `ColdInputs` port, `StoreColdInputs(foundation_store, scenario_repository)`,
    `cold_draft_projection`, `cold_terminal_projection`, schema-6 `render_cold_projection`/`parse_cold_projection`
    (exact key order, strict), `delay_event_id` (`cold-delay-` + SHA-256 of report key).
  - `host/cold_publication.py`: `cold_execution(verified)`, `cold_reports(verified, execution)`,
    `cold_minute_records`, `cold_content_digest`, `cold_series_digest` (the one renderer).
  - `host/lab_execution.py`: `HostLabExecution(cold_inputs=)`, `_is_cold`, `_not_started` (cold Draft bypasses
    `_reporting_for`), `start` -> `_start_cold`, `_stage_registered_virtual_cold` (sibling method, not a branch
    inside `_stage_registered_virtual`, because a cold run has no `LabSession`), `YamlExecutionArtifacts.write_cold`
    (private doc `{schema:"cold-private/1",run_id,content_digest,minute_records}` after `HISTORY_MARKER`),
    `parse_projection` dispatches marker 6, `render_projection` refuses a cold projection, cold `read_history`
    -> `HISTORY_UNAVAILABLE`.
  - `host/lab_app.py:build_app` resolves `foundation_store`/`scenario_repository` exactly as `create_app` does
    and passes the same objects to both.
  - Contracts: `PUBLICATION_REFUSED` added to `EXECUTION_FAILURE_KINDS`; `HOST_STAGING_FAILURE_KINDS` excluded
    from the simulator reachability guard (`simulator/tests/conftest.py`), reached in the host test.
    `HISTORY_UNAVAILABLE` added to `LAB_HISTORY_SOURCES`.
  - `host/tests/test_cold_lab_execution.py` (10): late-reading 12 points staged, 13 after
    `advance_publication(20:10)` with source 19:20, retry idempotent; schema-6 artifact read after restart,
    `_execution_status==COMPLETED`; step/run_to_end NOT_STARTED before and ALREADY_TERMINAL after; 5 refusal
    cases leave no gateway call and no schedule; publication refusal persists FAILED; damaged/future artifact
    -> ARTIFACT_UNREADABLE.
  - Adjacent passing: host lab_execution/kernel_conformance/cold_publication/cold_dispatch/publication_delay/
    lab_history, simulator execution_failures, backend run_execution_api, contracts/tests.

Known Deviations to record: the spec names `JsonExecutionArtifacts`; the store is `YamlExecutionArtifacts`
(schema 6 written there). Draft cold projection uses `inputs_identity=run_identity_sha256(run)` and empty
digest SHA-256(canonical `[]`). Host-only failure kind excluded from the kernel reachability guard.

## Survey facts for commit (4) (verified by Explore, not yet acted on)
- **Rule 8:** a new module importing sqlalchemy fails (`tools/checks/configuration-persistence.ps1:676,763-790`);
  every listed writer must write. So the read adapter must be SELECT-only methods added to
  `backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py` (pattern: `link_rows` :971, `_LINKS`
  joins :1036, `_envelope_at` :1047), composed in `evidence/composition.py` (like `build_source_provenance` :36).
  `cold_replay.py` then holds `ColdReplayService` over that reader + `SimulationRunRepository` with no SQL.
- **Access:** `finding_api.py:37` `Access = Callable[[Request,str], int|None]` (None admits, 401/403); scope via
  `registry.ledger_scope(site_code)` (`sites/cutover.py:107`). No production access resolver or owner role
  exists; per spec, production composition with no owner principal must answer 403. Router/error pattern:
  `cold_foundation_api.py:43-81`. Mount under `main.py:424` `if resolved_flags.simulator_lab_enabled:`.
- **Batch:** `contracts/assetops_contracts/ingestion_batch_v2.py:302` `parse_canonical_batch_v2_text(...).envelopes`.
- **No pytest drives the full chain** (Lab start -> gateway -> release -> upload -> Site Evidence); only
  `tools/s2_demo_walkthrough.py` (`Demo` :65) does it via subprocesses. Closest pytest:
  `backend/tests/test_s4_power_demo_case_postgres.py:285-300`; building blocks `tests/pg_harness.py`
  (`fresh_database` :302), `test_s2_evidence_ledger_postgres.py` (`Kit` :64, `submit` :153),
  `test_s405_resolver_postgres.py` (`simulated` :95), `test_w202_cold_lab_bindings_postgres.py`
  (`install_cold_lab`), and the real gateway process helper `host/tests/gateway_process.py`.
- **TESTING.md:** full run `& $py -m pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q
  --durations=30 --junitxml=.pytest-junit.xml` with `ASSETOPS_TEST_DATABASE_URL`; zero-skip check `:138-146`.

## Remaining, in order
1. Commit (4) per "Commit (4) exact contract": reader methods in `postgres_evidence_ledger.py`;
   `cold_replay.py:ColdReplayService`; `cold_replay_api.py:build_cold_replay_router`
   (`GET /api/sites/{site_code}/cold/replay?run_id=`), Lab-gated in `main.py`; API unit tests with fakes.
2. `backend/tests/test_w202_cold_replay_postgres.py` (6 named tests) on `assetops_w202c_test`, copying
   `var/sites` into the isolated work dir: needs a real gateway process (`host/tests/gateway_process.py`) +
   `HostLabExecution(cold_inputs=StoreColdInputs(...))` + release + upload; fix IDs/clock/epoch/UUIDs via test
   fixtures. Generate the six `contract-fixtures/w2/cold/*.json` manifests from the first run, pin them.
3. Rule-8 probes `python tools/writer_guard_probes.py --seam` (clean tree) + a v4 gateway-to-ledger probe test.
4. Final proof (no other pytest running): full backend (keep-awake, 2x cap), simulator, gateway, host,
   `contracts/tests` with JUnit counts; `npm.cmd test`; `tools/check-all.ps1 -Python <plan2 venv>`.
5. Packet `.agent/W2-02-review-packet.md` (`git add -f`), with the Known Deviations above and from phase 2/3.
