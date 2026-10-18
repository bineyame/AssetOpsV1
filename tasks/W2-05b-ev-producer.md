# W2-05b — EV causal producer and public replay

Status: implementation-ready (planning, 2026-10-18). Size M; two phases. Branch `task/W2-05b-ev-producer` from merged W2-05a. USER_REVIEW_REQUIRED: true, after independent slice review in the later owner W2 walkthrough. Exit: a registered EV Lab run whose public v4 reports reach ordinary S2 AcceptedEvidence; no W2-06 assessment or Finding is produced here.

## Binding design and dependencies

`D-2026-10-17-w2-techdesign-ev` (amended), `.agent/W2-technical-design-ev.md` §§2–3,8 and `.agent/W2-05b-build-spec.md` bind this build. Requires merged W2-00 v4/Batch V2, W2-05a effective EV Foundation/bindings, W2-02 closed pack selection/DeviceReport v2/Lab Stage/Commit/replay pattern, registered Lab and SQLite outbox. The six cases use a new EV-LAB-001 registration, not the mock's illustrative counts/120 kWh/$36. OCPP 1.6J vendor peer, physical capture and attestation are pilot gates under the amended EV design; this slice does not invent a peer fixture.

## Phase 1 — deterministic pack, six cases and frozen identity

Register `ev-charger/1`, `ev-publication/1`, `ev-observation/1`, `ev-scenario/1` in the closed host/Lab/kernel dispatch. Freeze Foundation, binding/source IDs, scenario SHA, profiles, UTC window and seed before Draft; reject unknown version or unsupported EV state. Implement the one-minute exact-decimal connector/session state machine and round-robin shared-cap allocation in the technical design. Add `config/scenarios/ev-{complete,interrupted,fault,missing-meter,late-record,contradictory}.yaml` with the exact forcing/observation table and strict document parser. Keep request schedule/private cause/oracle out of public reports. Build the registered `EV-LAB-001` fixture with two 60 kW connectors, 80 kW Site limit and the declared 08:00–16:00 UTC enable schedule; publish a v4-mapped binding revision before run time.

Acceptance tests: all six cases yield the technical design's event/energy assertions (30.000, 15.000, 10.000, 25.000 supported, late 30.000 and contradictory null-complete). Verify one-minute state transitions, 1 kW fair allocation quanta, limits, exact energy residual, no duplicate START/terminal and invalid-state refusal. Host, Lab and kernel use the same frozen pack; old mini-grid/cold bytes and branches remain unchanged. Fault before START creates no ABORT/session Finding. Missing end stays incomplete at first cutoff. Tests do not infer charge demand from private request forcing.

## Phase 2 — Stage, Commit, S2 receipts and replay

Transform only observed connector state, START/END/ABORT/FAULT/CLEAR, half-open five-minute connector energy deltas and optional power/site import into `DeviceReportV2`. Reuse gateway-owned schema-4 envelope identity/sequence, SQLite outbox, registered Stage/Commit, authenticated Batch V2 and S2 admission. Split intervals at session boundaries; round cumulative boundaries half-even to 0.001 kWh before differencing. Observation drop/hold changes publication only, retaining source time and event ID. Serve owner-gated `GET /api/sites/{code}/ev/replay?run_id=<id>` from persisted run/publication/batch/disposition/accepted rows, with no private world bytes.

Acceptance tests: commit six `ev-replay-manifest/1` files under `contract-fixtures/w2/ev/`, pinning frozen identities, canonical public envelope/batch hashes, dispositions, accepted IDs and bounded public assertions. Run each through the real registered path on a private `*_test` DB, repeat same bytes for idempotent gateway/receipt behavior, and verify late release retains source time. Prove S2 EV connector/delta refusals and event/session conflict classifications from ordinary reads. Scan Stage, Batch, accepted rows and replay JSON for private forcing, vehicle/customer identity and oracle. Test 401/403/404/422/503 and owner role, frozen re-read and corrupt artifact refusal. Run focused simulator/host/gateway/contracts/backend tests, rule-8 and architecture/workflow guards, registry checker, and **one full backend suite on final revision** with JUnit zero failed/skipped. Independent review and later owner walkthrough use stored replay.

## Registry

Set only existing open `A-ev-world.task` and `I-ev-world.task` to `W2-05b`. Leave `I-ev-device-adapter` and `D-ev-physical-peer` unassigned for pilot; leave statuses/evidence unchanged. Proposed `D-w2-ev-replay` is not inserted. Run the registry checker.
