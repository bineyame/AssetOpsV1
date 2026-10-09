# S2-01c review packet: gateway diagnostics and fault scenarios

- **Task:** `tasks/S2-01c-gateway-diagnostics-faults.md`. USER_REVIEW_REQUIRED: false.
- **Branch:** `task/S2-01c-gateway-diagnostics-faults`, cut after S2-01a/S2-01b were merged to main (`7c10283`). Not merged. Review the diff with `git diff main...HEAD`.
- **Decisions:** `D-2026-10-09-s2-gateway-sealing-state-and-partial-progress`, `D-2026-10-09-s2-simulated-publication-clock`, `D-2026-10-09-s2-gateway-diagnostic-semantics` (answers-2), `D-2026-10-09-s2-publication-clock-post-run-release` (answers-3).
- **Phases:** 1 `edf5c8c`..`6b63d6e`; 2 `2d442a2`..`5ec78a7`; 3a `40799c5`..`a28ec2a`; 3b `8cae309`, the layout commit and this closeout. Handoffs are in `.agent/S2-01c-phase-{1,2,3a}-handoff.md`.

## Outcome

The separate simulated gateway now keeps state-safe seal refusals (R1). It stores durable, slot-idempotent `GatewayDiagnosticsV1` reports with ledger-derived counters, and refuses acquisition at STOP before any sequence is used. A registered run can opt into a run-scoped virtual publication clock (`registered-kobo-publication` v2, `RUN_VIRTUAL`). A delayed report waits in a Lab-private schedule and is admitted at its actual virtual instant, with its original source time; it is never backdated. The new post-run scenario keeps the run's final reading pending at world completion, and an explicit advance releases it after the end, also after a host and gateway restart. The Lab shows that schedule (each instant labelled by its clock), an advance control that names the six refusals in plain words, and the gateway's local diagnostics (an unavailable gateway is shown as unavailable, never as an empty queue). It also shows each seal refusal's outbox group. Release controls stay unavailable while the frozen basis is unknown (F2). Nothing is uploaded, received centrally or written as Site Evidence.

## Files materially changed

- Gateway: `gateway/assetops_gateway/ledger.py` (migrations 3, 4), `service.py`, `ipc.py`, `__main__.py`.
- Contracts: `gateway_diagnostics.py` (new), `publication_schedule.py` (new), `gateway_stage.py`, `lab_projection.py` (six publication refusal kinds), `execution_contract.py` (narrowed `outside-the-interval` rule). Vectors: `contract-fixtures/gateway-diagnostics-v1-vectors.json`.
- Host: `host/publication_schedule.py`, `lab_execution.py`, `gateway_publication.py`, `profiles.py`. Fixtures: `host/fixtures/gateway-fault-scenarios.v1.json` and `.v2.json`.
- Scenarios: `config/scenarios/kobo-daytime-delayed-publication.yaml` v1 and `kobo-daytime-post-run-publication.yaml` v1.
- Backend: `runs/service.py` (`_post_run_release_window`), `runs/execution_ports.py`, `simulator_lab_api.py` (three routes, payloads, `outbox_state`, `publication_clock`).
- Frontend: `src/shell/runSetupClient.ts` (parsers and three methods), `GatewayPublicationPanels.tsx` (new), `GatewayLedgerView.tsx`, `RunFrame.tsx`, `RunSetupFrame.tsx`, `RunCommitPanel.tsx` (F2), `src/test/settled.ts` (two new loading texts).
- Tools: `tools/layout-evidence.mjs` (`ASSETOPS_LAYOUT_S2_01C_RUN` mode).

## Acceptance criteria

1. **R1. Met.** `seal_refusal` is keyed by `(source, epoch, snapshot, outbox_state)` (ledger schema 3), and write, delete and lookup all use that state. Tests cover a mixed READY/STAGED fixture through restart, partial sibling progress and clearing on the same group's success. Non-vacuity: a state-blind delete fails 1 test, and a state-blind lookup fails 1. Phase 3 carries `outbox_state` through the API and shows it in the "Outbox group" column (`gatewayLedgerStage.test.tsx`).
2. **Diagnostic wire and ledger. Met.** Canonical V1 with bounded parse and vectors (first `payload_sha256` `e7fde117…f787`). Sequence allocation and the byte insert happen in one transaction, and there is one report per cadence slot, so a retry or restart returns the same identity and bytes. The config is frozen and returned with the read. No `received_at` or ACKED row exists (`server_received_at` is always NULL), and the client refuses an ACKED diagnostic.
3. **Counters and pressure. Met.** Queue counts come from ledger rows with the local breakdown (sealed or unbatched, held, active seal refusals, dead letters). `mapping_error_count` counts only mapping kinds (answers-2 Q4). A contact is recorded as `OBSERVED_SIMULATED_REPORT`, and an absent contact shows "Unknown: no report observed … not a healthy source". Clock offset reads "Unknown: not measured" unless injected. Pressure is labelled MEASURED, INJECTED_FAULT_FIXTURE or UNMEASURABLE; STOP refuses before sequence assignment and keeps the stored bytes. `GATEWAY_UNAVAILABLE` carries no counters, and the client refuses an unavailable read that carries any.
4. **Delayed local admission. Met.** Covered by `test_registered_publication_delay.py` (wait, then admission at the actual virtual instant; pause and restart release nothing) and `test_registered_post_run_release.py`. That second test runs the real gateway: the 15:00 report is PENDING at world end; an advance to 15:03 releases nothing; after a host forget and a gateway restart, an advance to 15:10 publishes it at 15:10, not 15:05; repeats leave the bytes identical; and no private field crosses. BACKWARD, AHEAD_OF_WORLD and MISSING refuse. The S2-01b GATEWAY_UTC delay refusal remains.
5. **Fault scenarios and Lab view. Met, with Q2 of questions-4 open.** The manifests v1 and v2 separate public expectations, delayed cases, fault controls and the private oracle. `test_link_loss_keeps_the_report_pending_and_reconnect_releases_it_once` and `test_injected_stop_refuses_acquisition_and_keeps_bytes` exercise the real IPC path. The Lab view (`gatewayPublication.test.tsx`, 15 tests) labels each clock: source time, scheduled release and released-at on the run's virtual clock, `published_at` as the gateway's stamp on that clock, and diagnostics on gateway real UTC. It shows pending, due and released states, the release basis after a restart, the six refusals, NO_SCHEDULE as "not an empty queue", and GATEWAY_UNAVAILABLE with no counters. Fault injection stays fixture-only (questions-3 Q4).
6. **Lab carries and layout.** F2 is met: `releaseBasisBlock` offers no Resume or Retry while the Stage read is pending, unavailable, not found, or silent about the basis, and shows the basis block once the read resolves after Site import (3 new tests). F3: see Layout evidence.

Non-vacuity (phase 3b, each mutation run against the committed tree and then `git checkout --`): F2 pending branch disabled → 1 failed; `published_at` falling back to the scheduled instant in the view → 2 failed; the absent-schedule clause removed from the parser → 1 failed; the unavailable-with-counters check removed → 1 failed. Earlier phases' proofs are in their handoffs.

## Checks run (final tree, Postgres on)

| Check | Result |
|---|---|
| `pytest gateway/tests` | 125 passed |
| `pytest host/tests backend/tests` (`ASSETOPS_TEST_DATABASE_URL` set) | 2313 passed, 0 skipped (442 s) |
| `simulator` (from `simulator/`) | 265 passed |
| `npx vitest run` | 51 files, 1232 passed |
| `npx tsc --noEmit` | clean |
| `npm run build` | built (chunk-size warning only) |
| `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1` | passed |

## Layout evidence

Not recorded in this packet. A layout-evidence run was still in progress when this packet was committed. It adds the `ASSETOPS_LAYOUT_S2_01C_RUN` mode, which measures at 1280 and 640 and includes a fetch-intercepted "Sealing refused" row, uses an isolated runs store, takes a 640 baseline against main and runs the full layout check on a clean store. Until its results are appended here, the F3 claims (640 `.app-frame` overflow, the later full-run sections and the narrow Sealing refused table) and the layout of the new panels are **unverified**. Check `git log` for a layout-evidence commit on this branch.

## Known deviations

- The client's three new methods are optional on `RunSetupClient` (questions-4 Q4).
- The diagnostics panel lives on the registered run page, not on a separate Gateway & Ingestion page (questions-4 Q2).
- F2 also treats a Stage read with no reported basis as unknown (questions-4 Q1); two T027 tests now state an explicit releasable basis.

## Residual risk

- questions-3 Q1: the pending report is the run's end-instant reading (source 15:00). This awaits Architect confirmation.
- The read route does not separate NO_SCHEDULE from a schedule missing after execution (questions-3 Q3). Advance does refuse MISSING.
- A seal refusal after admission leaves a delayed report PENDING until the next advance.
- Whole-series republish per step remains O(n) (S2-01b).

## Open questions

`.agent/S2-01c-questions-3.md` (Q1-Q4) and `.agent/S2-01c-questions-4.md` (Q1-Q5), both unanswered and fail-closed. Earlier sets were answered in `.agent/architect-S2-01c-answers{,-2,-3}.md`.

## Reviewer path

1. Read the task, the two answer files and this packet, then run `git diff main...HEAD`.
2. Live: provision the gateway as in the S2-01b packet (steps 1-2) and start `lab_app` and vite. Set up a registered KOBO-001 Draft with scenario `kobo-daytime-post-run-publication` v1 and profile `registered-kobo-publication` v2; setup names "Publication clock: the run's virtual publication clock". Run it to the end. In "Stage and staged envelopes", check that the Delayed publication table shows the 15:00 report waiting. Advance to 15:03 (nothing is released), then to 15:10: published at 15:10, source time 15:00, and the sequence appears in the ledger. Restart both processes, re-read, and advance again: the bytes are unchanged.
3. Gateway diagnostics: stop the gateway and the panel says "Gateway unavailable" with no counters. Inject a fault through the manifest's fixture IPC to see INJECTED provenance.
4. Layout: run `ASSETOPS_LAYOUT_S2_01C_RUN=<run> node tools/layout-evidence.mjs <base>`.

## User-review focus

None is required. Plain-language clock labels and the unavailable wording are worth a glance.
