# S2-01b phase 2 handoff: transfer and staged publication

Branch `task/S2-01b-durable-simulated-gateway`. Phase 2 is complete with the fail-closed defaults below. Phase 3 is the visible closeout: frontend, F1 and layout. The full review comes after phase 3.

The phase-2 commits:

- `79fbbf2` gateway process, channel and chunked admission;
- `a8bd895` host/backend wiring;
- `1f0d25b` host-boundary guard;
- `77736f9` Architect questions.

## What landed

### Gateway process (`gateway/assetops_gateway/`)

- **Entry point.** `__main__.py` provides `python -m assetops_gateway serve --config gateway.json`.
  - The config holds `database`, `credential_file`, an optional `address`, and `provisioning`: tenant, Site, gateway, `SIMULATED`, permitted sources and epoch.
  - Provisioning happens once at startup and never per request. A ledger already provisioned differently prints `REFUSED IDENTITY_FIXED` and exits 2.
  - The process prints `READY <address>` when it is up. `reprovision-epoch` is the only way to change the epoch.
- **Channel.** `ipc.py` implements `D-2026-10-08-s2-local-gateway-snapshot-transfer`.
  - Transport is `multiprocessing.connection`: a Windows named pipe, or a Unix socket elsewhere. It is used only through `send_bytes`/`recv_bytes`; there is no pickle.
  - Authentication is a mutual HMAC challenge in each connection thread, over a 32-byte credential that the gateway creates owner-only beside its ledger (`ensure_credential`). A peer without the credential never gets a request read.
  - Bounds: 16 MiB per message, at most 1024 reports per admit, exact request/body keys, and the ops `identity|activate|admit|seal|run_stage`.
  - Refusals come back typed (`kind/field/detail`). `GatewayUnavailable` and `GatewayRequestRefused` are raised client-side.
  - The service runs under one lock, so there is a single writer.
- **Service.** `service.py`:
  - adds `admit_texts`, which admits one chunk in one transaction and addresses the phase-1 speed risk;
  - routes `admit` and `admit_texts` through `_admit_in`;
  - adds `identity()`.

### Contract

`contracts/assetops_contracts/gateway_stage.py` provides `RegisteredStageView`, `GatewayEnvelope`, `GatewayBatch` and `GatewayHold`, plus the constants `GATEWAY_LEDGER_STORE` and `UPLOAD_PENDING`. The guards treat it like `source_stage`: only `simulator_lab_api.py` and `execution_ports.py` may import it.

### Host

- **`host/gateway_publication.py`**
  - `RegisteredGatewayPublisher.publish` does the following in order:
    1. checks gateway identity against the basis tenant/Site (`WRONG_SITE`);
    2. sends `activate` with `basis.snapshot_canonical` and the six claimed references;
    3. adapts observations with `report_from_observation`;
    4. admits in chunks;
    5. seals.
  - `report_key` is `lab-` plus SHA-256 of `(run_id, snapshot sha, device, signal, source_time, ordinal)`. It is opaque, so the run id never appears in report text.
  - `stage()` reads back over the channel. `unavailable_stage()` produces a `GATEWAY_UNAVAILABLE` view.
- **`host/lab_execution.py`**
  - The constructor takes `gateway=`.
  - `LabSession` has a new field, `registered_basis`, set in `start()`.
  - `_stage` sends registered sessions to `_stage_registered`. Refusals become `staging_notes`, and nothing is written to the file Stage. A registered run with delay windows is refused (Q3). A registered run with records gets a note that records are `SCHEMA_UNSUPPORTED`.
  - The new `registered_stage(run)` performs the read.
- **`host/lab_app.py`** builds the publisher from `ASSETOPS_GATEWAY_ADDRESS` and `ASSETOPS_GATEWAY_CREDENTIAL`. If either is unset, there is no gateway and registered runs stage nothing.

### Backend

- `runs/execution_ports.py`: `LabExecutionPort.registered_stage`.
- `simulator_lab_api.py`: `registered_stage_payload(view)`, and `read_run_stage` now branches on `record.registered_basis`.
- The registered stage payload carries:
  - `store: GATEWAY_LEDGER`, `status`, `statement`, `execution_status`;
  - `release_eligible: false`, `upload_state: PENDING`, `upload_statement`, `receipts: []`;
  - `snapshot_sha256`, `site_id`, `gateway_id`, `sequence_epoch`, `unavailable_detail`, `publication_notes`;
  - `queue_depth_by_state`;
  - `envelopes[]`: `message_id`, `source_id`, `sequence_epoch`, `sequence`, `source_time`, `snapshot_sha256`, `canonical`, `sha256`, `state`, `batch_id`, `ordinal`;
  - `batches[]`: `batch_id`, `source_id`, `sequence_epoch`, `snapshot_sha256`, `canonical`, `sha256`, `state`, `attempt_count`, `message_ids`;
  - `holds[]`: `hold_id`, `kind`, `field`, `detail`, `device_id`, `signal_id`, `source_time`, `seen_count`.

  Pre-import runs keep the old `stage_payload`. Direct registered Commit still returns 409 before the port.

### Guards

- `dependency-direction.ps1` and `analytic-declaration.ps1` now cover `gateway_stage`.
- A new host-side rule: the host may import `assetops_gateway.ipc` only, with an anti-vacuity count; backend, including its tests, may not import `assetops_gateway`.
- I proved each rule non-vacuous by introducing the violation, watching the check fail, and reverting:
  - an `evidence_api` import of `gateway_stage`;
  - a `lab_app` import of `assetops_gateway.service`;
  - removing every host `ipc` import, which fails the vacuity check.

## Tests

- **Gateway:** `gateway/tests/test_gateway_process.py`, seven tests against a real process: the serve flow, a stranger credential refused, no gateway gives unavailable, exact and bounded requests, typed activation refusals, wrong-Site provisioning refusing to start, and restart keeping identity and bytes.
- **Host:** `host/tests/test_registered_gateway_publication.py`, nine tests driving the real S2-01a registered KOBO-001 Draft and a real gateway process. A real snapshot activates, which closes the phase-1 risk.
  - Run results: five source-specific Batch V2 objects; 252 envelopes plus 41 ratio holds (Q1); per-source sequences 1..n.
  - Batch content: batch bytes equal the ordered envelope bytes, and `foundation_valid_from` is verbatim.
  - Replay: a whole-series replay is `ALREADY_ADMITTED`.
  - Restarts: with the gateway killed, the read is `GATEWAY_UNAVAILABLE` and nothing falls back. After a gateway restart and a new host, the bytes are identical.
  - Process boundary: only `assetops.simulated-device-report` texts cross it, with exact keys, no run id and no private words; the activate request carries the exact snapshot bytes.
  - Crashes: a host crash mid-series resumes without reallocation. A gateway killed after enqueue and after seal keeps its rows and bytes.
  - Probes: a same-time distinct report gets a new id. Unknown channel and incompatible unit are holds with no sequence allocated.
  - Wrong Site or no gateway: a note, and nothing staged.
  - Kobo ENUM end to end (Q2).
  - Later basis: a new basis gets new batches with foundation_version 4 while the old bytes are unchanged.
  - A full run with a per-step whole-series replay takes about 0.3 s.
- **Updated tests:**
  - `host/tests/test_registered_kobo_execution.py`: notes now differ by exactly the no-gateway refusal.
  - `backend/tests/test_s1_cutover.py::StagedExecution.registered_stage`.
  - `backend/tests/test_s2_registered_basis.py`: the registered `/stage` is `GATEWAY_LEDGER`, PENDING, with no receipts, and the file Stage is never asked.
- **Suites:** see the results section at the end.

## What phase 3 needs

- **Frontend.**
  - Today `isRunStage` rejects the registered payload, so a registered run's Stage shows "unavailable" in the Lab. That is honest, but it is not the target.
  - Add a `GATEWAY_LEDGER` branch in `frontend/src/shell/runSetupClient.ts` (`isRunStage` ~1529, fetch ~1790) and render it in `RunFrame.tsx`. Show:
    - snapshot hash, epoch, per-source batches with digest and bytes;
    - envelopes with sequence, ordinal and state;
    - queue depth, typed holds with field and detail;
    - "upload pending, no receipt";
    - `publication_notes`.
  - Close F1 in `RunCommitPanel.tsx`.
- **Running it.** Provision a gateway config for KOBO-001 from its registered snapshot: tenant, Site, gateway id and source ids. `host/tests/gateway_process.py::provisioning_from_snapshot` shows the shape. Then:
  1. Run `..\.venv\Scripts\python.exe -m assetops_gateway serve --config <cfg>`.
  2. Set `ASSETOPS_GATEWAY_ADDRESS`, and set `ASSETOPS_GATEWAY_CREDENTIAL` to `<cfg dir>/<credential_file>`.
  3. Start `lab_app`.

  There is no operator CLI that writes this config yet; it is optional.

## Risks and open items

- **Q1–Q3** are in `.agent/S2-01b-questions-2.md`:
  - ratio readings are held rather than rounded;
  - the registered daytime profile does not report generator status, so ENUM is proved by a direct public observation;
  - delay windows are refused.

  If the answer to Q1 is option 2, the adapter changes and the 41 holds become envelopes.
- **Credential protection** relies on `O_EXCL` and 0600. On Windows the file mode is mostly advisory, so protection comes from the user-profile ACL. I did not do an explicit ACL hardening.
- **Single-threaded handling.** A connection thread that never sends after authenticating holds only its own thread; the service lock is taken only per request. There is no idle timeout.
- **Hold dedupe.** Holds are keyed by report hash and snapshot, so a replayed held report increments `seen_count` and its `last_seen_at` changes. Hold rows are not byte-fixed, but envelope and batch rows are.
- **Speed and size.** The host re-sends the whole series on each step, which costs O(n) per step. That is fine for 48 boundaries. A week-long run would want a watermark. The stage read over the channel is about 1 MiB for a full Kobo day, against a 16 MiB bound.

## Suite results (full runs after the build commits)

- gateway 76 passed; backend 1583 passed, 31 skipped; simulator 244 passed.
- host 632 passed, 1 failed: `test_lab_execution.py::...::test_there_is_no_commit_or_release_anywhere_on_the_port`. The port's public-name inventory lacked the new `registered_stage` read. The fix is `1d98fa1`, and that test now passes. The host suite was not rerun in full after that one-line test change.
- `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1` pass.
- Frontend suite, typecheck and build were not run, because phase 2 changed no frontend code. Layout evidence was not run, because phase 2 changed nothing on screen; it belongs to phase 3.
