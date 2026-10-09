# S2-01c phase 1 handoff — ledger correctness and diagnostics

Branch `task/S2-01c-gateway-diagnostics-faults`. Phase 1 complete (AC1, AC2, gateway half of AC3). Packet placement put the F2/F3 UI carry in phase 3, so it was not touched. Design defaults: `.agent/S2-01c-questions-1.md` (Q1-Q5, fail-closed; awaiting Architect, none blocks phase 2).

## What landed

- **R1 (AC1).** Ledger schema 3 (`gateway/assetops_gateway/ledger.py` `MIGRATION_3` ~239): `seal_refusal` PK adds `outbox_state` (`STAGED|READY`); v2 rows take the state of the envelope they name (unbatched state never changes). `service.py` `seal` (~697) records/deletes per `(source, epoch, snapshot, state)`; `GatewayReader.run_stage` looks up by state. `SealRefusalRow` and contract `GatewaySealRefusal` (`contracts/.../gateway_stage.py`) gained required `outbox_state`; host builds it via `GatewaySealRefusal(**r)` so it travels already. Backend `registered_stage_payload` does NOT yet emit it (phase 3 / Lab API). Sealed bytes/IDs and v3/batch vectors untouched.
- **Wire (AC2).** `contracts/assetops_contracts/gateway_diagnostics.py`: `GatewayDiagnosticsV1`, `seal_gateway_diagnostics_v1`, strict `parse_canonical_gateway_diagnostics_v1_text` (exact keys, digest excludes itself, canonical rebuild, 64 KiB / 256-source bounds, contact <= observed_at, age null iff queue 0), and `DiagnosticConfig` (cadence, WARN/STOP free-byte triggers; canonical text returned with limits). Vectors: `contract-fixtures/gateway-diagnostics-v1-vectors.json` (first payload_sha256 `e7fde117…f787`, pinned in test).
- **Ledger (AC2).** Tables `diagnostic_config` (frozen, triggers refuse UPDATE/DELETE), `diagnostic_outbox` (PK `(gateway, epoch, sequence)`, `UNIQUE(gateway, epoch, cadence_slot)`, bytes immutable, never deleted, only `READY` written, `server_received_at` always NULL), `health_observation(name, value_text, observed_at, provenance)`.
- **Service** (`service.py`): `provision(..., diagnostics=DiagnosticConfig())` freezes config (~236); `_record_contact` (~804) on any report resolving to a permitted source, gateway real UTC, provenance `OBSERVED_SIMULATED_REPORT`; `_refuse_at_stop` (~837) first thing in `admit`/`admit_texts` → `DISK_PRESSURE_STOP`, no writes; `inject_disk_pressure` / `inject_clock_offset` (~852/866, SIMULATED only, `INJECTED_FAULT_FIXTURE`); `_health` (~880) counters from rows; `emit_diagnostic` (~936) one tx, slot-idempotent, `CLOCK_BEHIND` refusal, fault points `after_diagnostic_sequence_read`/`after_diagnostic_commit`; `local_diagnostics` (~994) the read document. Constructor takes `disk_free=` probe (default `shutil.disk_usage`).
- **IPC/process.** `ipc.py` ops `diagnostics` and `emit_diagnostic` (empty bodies); `GatewayServer.start_diagnostics` (~191) ticker under the service lock; `__main__` optional `diagnostics` config block, ticker started at serve.

## Tests (actual results)

- `pytest gateway/tests`: 115 passed (new `test_gateway_diagnostics.py` 32, process test +1, migration test now expects `[1,2,3]`).
- `pytest host/tests/test_registered_gateway_publication.py host/tests/test_registered_kobo_resolution.py backend/tests/test_s2_registered_basis.py backend/tests/test_s2_registered_resolution.py`: 69 passed.
- Full `pytest host/tests backend/tests`: 2244 passed, 31 skipped, 3 warnings (455.9 s).
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed. Frontend untouched (no vitest/tsc/build run).
- Non-vacuity (mutate committed tree, run, `git checkout --`): state-blind refusal DELETE → 1 failed; state-blind refusal lookup → 1 failed; STOP check removed → 2 failed; slot idempotency removed → 2 failed; contact recording removed → 1 failed. (A first R1 test was vacuous: the second seal pass re-recorded the erased refusal; fixed by asserting after the first pass and adding a BOTH-states case.)

## Phase 2 needs

- **Virtual publication clock** (`D-2026-10-09-s2-simulated-publication-clock`): V3 `published_at` is `self._now()` at `service.py` ~484, and `envelope_outbox.created_at` reuses the same value (~547). Queue age (`_health`) reads `created_at`, so when `published_at` moves to the scoped virtual clock keep `created_at` (and contacts, diagnostics `observed_at`, slot) on real UTC, or queue age turns into virtual time.
- Fault controls over IPC: phase 1 exposes `inject_disk_pressure`/`inject_clock_offset` on the service only. Phase 2 must choose how the fixture drives them (IPC op or gateway config) and keep them out of V3/Batch V2/diagnostic wire.
- Host: a host-side diagnostics read through `GatewayLink.call("diagnostics")`, mapping `GatewayUnavailable` to an explicit unavailable state (never a zero queue). `host/gateway_publication.py` should surface `DISK_PRESSURE_STOP` as a typed publication refusal.
- Phase 3: backend payload and frontend parser for `outbox_state` and the diagnostics read; F2/F3.

## Risks

- Default measured disk probe uses the real volume: on a host with < 256 MiB free the gateway honestly reports STOP and refuses acquisition (tests using the default `gateway` fixture would then fail).
- The process test's slot-retry assertion is conditional (a 60 s slot boundary or the ticker can intervene); the deterministic proof is in the service-level tests.
- `mapping_error_count` counts every hold kind (Q4); if Architect narrows it, only `_health` changes.
