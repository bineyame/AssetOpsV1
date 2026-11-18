# S2-01b phase 1 handoff: wire and ledger

Branch `task/S2-01b-durable-simulated-gateway`. Phase-1 commit `775f8f9`, after the Architect transfer decision `10aebb9`. Status: phase 1 is complete. There is no host wiring, transport or UI yet.

## What landed

- **Contracts** (`contracts/assetops_contracts/`). These are new modules. The v1/v2 envelope reader and the v1 batch reader are untouched.
  - `source_envelope_v3.py` provides `SourceEnvelopeV3`, `v3_message_id`, `length_delimited`, `canonical_envelope_v3_text`, `parse_canonical_envelope_v3_text`, `text_sha256` and `MAX_SEQUENCE = 2**63-1`.
    - `message_id` is SHA-256 over 4-byte big-endian length-prefixed UTF-8 fields: `(domain, site, gateway, source, epoch, decimal seq)`.
    - Every key is present, with `null` when absent.
    - Values are canonical decimals only: no ratio, no `-0`, no exponent. A member is allowed in the `state` unit.
    - Families: MEASUREMENT only; POLICY and OPERATIONAL_RECORD are refused (see `.agent/S2-01b-questions-1.md` Q2).
  - `ingestion_batch_v2.py` provides `seal_batch_v2` (which returns the batch and its exact text), `parse_canonical_batch_v2_text` and `batch_v2_id`.
    - The batch id is derived from `(gateway, source, epoch, snapshot_sha, first, last, count)`.
    - The digest excludes `payload_sha256`.
    - Bounds are 256 envelopes and 1 MiB.
    - Batches are homogeneous by site/gateway/source/binding set and version/epoch, in ascending sequence order.
  - `gateway_report.py` provides `DeviceReport` and its strict wire (`assetops.simulated-device-report` v1, exact keys), plus `report_from_observation(obs, interval_minutes=, report_key=)`.
    - DROPPED and SUPPRESSED observations produce `None`.
    - NO_PRECEDING_INTERVAL and NO_VALUE_AT_BOUNDARY produce an explicit UNAVAILABLE report.
  - Vectors are in `contract-fixtures/source-envelope-v3-vectors.json`: message ids, the unframed-collision pair, two envelopes and one batch.
- **Gateway package** (`gateway/assetops_gateway/`). It imports `assetops_contracts` only. Install with `pip install -e gateway`; this is done in `.venv`.
  - `ledger.py` holds the SQLite migration v1 and the connection setup.
    - Connections use WAL, `foreign_keys`, `busy_timeout` and `synchronous=FULL`.
    - The single writer holds an OS file lock (`<db>.writer.lock`; msvcrt on Windows, flock elsewhere); a second writer gets `WriterBusy`. The OS releases the lock on crash.
    - Triggers make envelope bytes, batch bytes, batch items, snapshots and mapping rows immutable and undeletable.
    - Tables follow technical design §2. Additions: `permitted_source`, `sequence_epoch_history`, `active_mapping`, `report_admission` (dedupe before sequence allocation), `mapping_hold` (holds, deduplicated by report hash and snapshot), `lab_report_provenance` (private run→message/hold) and `acknowledgement` (an empty receipt slot).
    - `sequence_state.last_sequence` stores the last allocated value, so `MAX_SEQUENCE` itself can be stored.
  - `snapshot.py`: `verify_snapshot(text, ClaimedReferences, Provisioning)` checks, in order:
    - the hash;
    - the schema `assetops.acquisition-snapshot/1`;
    - that the text is canonical;
    - exact keys;
    - provisioned tenant, Site, gateway, `SIMULATED` mode and permitted sources;
    - row consistency, including `bindings_sha256` recomputed as in `binding_service.bindings_digest`;
    - that the claimed references match.

    `VerifiedSnapshot.valid_at` checks the Foundation and binding half-open periods.
  - `service.py`: `GatewayService(path, clock=, fault=)` exposes `provision`, `reprovision_epoch`, `activate`, `admit(report_text, snapshot_sha256=, lab_run_ref=, initial_state=)`, `seal(max_envelopes=)`, `mark_ready`, `begin_attempt` and `attempt_failed`.
    - On restart it moves IN_FLIGHT batches back to READY with identical bytes.
    - There is no ACK path.
    - `GatewayReader(path).run_stage(lab_run_ref)` is the read-only per-run view: envelopes with batch and ordinal, batches with bytes and message ids, holds, and queue depth by state.
    - Holds are: INVALID_REPORT, NO_ACTIVE_MAPPING, UNKNOWN_CHANNEL, SOURCE_NOT_PERMITTED, INVALID_TIMING, OUTSIDE_VALIDITY, SOURCE_TIME_IN_FUTURE, UNIT_INCOMPATIBLE, INVALID_ENUM, INVALID_VALUE, CONFLICTING_REPORT, SEQUENCE_EXHAUSTED, and envelope-rule kinds. A hold never allocates a sequence.
    - `published_at` is the admission (sealing) time, from the injected clock.
- **Guards.** `tools/checks/dependency-direction.ps1` bans gateway imports of the simulator and backend, and adds `gateway` to the trees that may not import host. `module-roots.ps1` requires `gateway/`. I proved the ban non-vacuous: I added a simulator import and a host import to gateway files, the check failed on both, and I reverted them.

## Tests (run from `gateway/` with `..\.venv\Scripts\python.exe -m pytest`)

- 69 passed. `test_wire_contracts.py` covers vectors, refusals, batch tampering and bounds, and the adapter. `test_gateway_ledger.py` covers:
  - pragmas and the single writer;
  - sequence, replay and same-time distinct reports;
  - conflict, overflow and epoch handling;
  - fixed identity;
  - seven hold kinds with no sequence allocated;
  - activation refusals: hash, scope, mode, references, schema, canonicality, row tampering and foreign source;
  - per-source sealing, replay of a whole series, batch bound, a new basis creating new batches with the old bytes unchanged, and immutability triggers;
  - restart recovery of an IN_FLIGHT batch;
  - three subprocess crash windows using `os._exit`: inside the enqueue transaction, after enqueue commit, and after seal commit.
- Simulator suite: 244 passed. Architecture and agent-workflow checks pass. Backend, host and frontend suites were not run; phase 1 changed no code they import beyond adding contract modules and a docstring.

## What phase 2 needs

- **Transport** (`D-2026-10-08-s2-local-gateway-snapshot-transfer`). Wrap `GatewayService` in a separate process (`python -m assetops_gateway ...`, still to be written) behind authenticated local IPC: an OS peer identity or a protected local credential. Provision from a gateway-local config at startup, not per request.
  - Activation gets its `ClaimedReferences` from `RegisteredBasis`: `snapshot_sha256`, `foundation_revision_id`, `foundation_version`, `binding_set_id`, `binding_set_revision_id`, `binding_set_version` (`backend/assetops_backend/runs/models.py:805-866`).
  - Permitted sources come from provisioning, not from the snapshot.
- **Host.** In `host/lab_execution.py::_stage`, for registered runs only, map observations through `report_from_observation`. Pass a deterministic `report_key` per observation, for example derived from the run's frozen basis, device, signal, source time and an ordinal for genuinely repeated samples, so that a whole-series replay returns ALREADY_ADMITTED. Then call `seal()`.
  - Stage reads use `GatewayReader.run_stage(run_id)`. The run id lives only in `lab_report_provenance`.
  - The Kobo ENUM binding must map `RUNNING`/`STOPPED` labels as keys (see Q1).
- The Stage API (`simulator_lab_api.stage_payload`) and the frontend are phase 2 and 3, as the packet says.

## Risks

- I wrote `.agent/S2-01b-questions-1.md` with three wire-semantics questions: original vs converted value, the families, and the `valid_from` spelling. Each is built on a fail-closed default; answering differently changes the vectors.
- The gateway suite restates the snapshot shape rather than importing the backend. Phase 2 must activate a real S2-01a snapshot in a host test to prove the shapes agree.
- `admit` is one transaction per report. A full-day run may need a batched admission path for speed; measure in phase 2.
- The writer lock uses an msvcrt byte-range lock on Windows. I have not checked the lock on a network filesystem.
