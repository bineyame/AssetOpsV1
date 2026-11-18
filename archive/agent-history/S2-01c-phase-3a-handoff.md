# S2-01c phase 3a handoff: post-run release, Q5, Lab API

Branch `task/S2-01c-gateway-diagnostics-faults`. Phase 3a is complete: answers-3 Q3/Q5, the backend Lab API and the `outbox_state` carry. Design defaults are in `.agent/S2-01c-questions-3.md` (Q1-Q4, fail-closed, none blocking). **Read Q1 first:** the pending report is the run's end-instant reading (source 15:00), not the 14:45 sample, because the alternative is a two-report batch release.

## What landed

- **Setup amendment (Q3).** `backend/assetops_backend/runs/service.py` `_post_run_release_window` (~3473), called from `_refuse_entries_outside_the_interval` (now takes `publication`). It applies only to a RUN_VIRTUAL profile and a declared publication-delay WINDOW with `0 <= offset < length` and `end <= length + timestep`. The cadence rule is unchanged. The `outside-the-interval` statement in `contracts/.../execution_contract.py` names the exception.
- **Fixture.** `config/scenarios/kobo-daytime-post-run-publication.yaml` v1 is delayed-publication v1 with the closing window moved to [710, 725). Fingerprint `70cce87a…adcb` is pinned, and the never-shipped-as-v1 and count lists are extended. Delayed-publication v1 is unchanged and selectable. `host/fixtures/gateway-fault-scenarios.v2.json` (`supersedes: 1`) has a `POST_RUN_ADVANCE` case (source 15:00, before-due 15:03, past-due 15:10 → `published_at` 15:10), oracle 710-725 → 15:05, and a HOST_RESTART control. v1 is untouched.
- **Q5.** `host/lab_execution.py` `advance_publication` returns `release_basis` (`LIVE_SESSION|STORED_SCHEDULE_ONLY`, ~2626). An executed run with no session and no stored schedule refuses the new `PUBLICATION_SCHEDULE_MISSING` (~2599, `_executed` ~2642; kind and statement added in `contracts/.../lab_projection.py`). `publication_schedule` raises `LabControlRefused(PUBLICATION_SCHEDULE_UNREADABLE)` and never returns an empty queue.
- **Contracts.** `DelayedReport`, `PublicationSchedule`, `parse_instant`, `PENDING` and `RELEASED` moved to `contracts/assetops_contracts/publication_schedule.py`, re-exported from `host/publication_schedule.py`.
- **Port.** `backend/.../runs/execution_ports.py` `LabExecutionPort` gains `advance_publication`, `publication_schedule` and `gateway_diagnostics`.
- **API** (`backend/assetops_backend/simulator_lab_api.py`):
  - Routes (~250): `GET /api/simulator-lab/runs/{id}/publication`, `POST .../publication/advance` (body exactly `{instant}`; 422 before the port; port refusals are 409 with `refusal_kind` and `advanced:false`), and `GET /api/simulator-lab/gateway/diagnostics`.
  - `publication_schedule_payload` (~1878) carries:
    - `status` `AVAILABLE|NO_SCHEDULE|NOT_SUPPORTED|UNREADABLE`;
    - `publication_clock` and `clock_labels` (source `SOURCE_TIME`, scheduled `RUN_VIRTUAL_SCHEDULED`, clock and released `RUN_VIRTUAL`, `published_at` `GATEWAY_STAMPED_RUN_VIRTUAL`);
    - the clock, world-reached and world-complete fields, plus `pending_count` and `released_count`;
    - `reports[]`, where actual `published_at` comes from the Stage envelope or is null, never the scheduled instant. The delay cause and report text are omitted.
  - The advance response adds `publication_refused`, `release_basis` and `release_basis_statement`.
  - `gateway_diagnostics_payload` (~1947) has `status AVAILABLE|GATEWAY_UNAVAILABLE`. When unavailable, `current` and `last_emitted` are both null and there are no counters. Otherwise `current` is the live read (queue, contacts, clock_offset and disk_pressure with provenance, acquisition, config without text), `last_emitted` is the newest stored diagnostic, and `observed_at_clock: GATEWAY_REAL_UTC`. A statement says the read is not device or asset health and not central receipt.
  - The publication profile summary has `publication_clock` (~901), and the registered Stage `seal_refusals[]` carry `outbox_state` (~1866).

## Tests and proof (actual)

- New `backend/tests/test_s2_publication_lab_api.py` (22) and `host/tests/test_registered_post_run_release.py` (3). The host test is the real gateway process: run_to_end → 15:00 report PENDING (292 envelopes) → live advance to 15:03 releases nothing and steps no kernel → Lab host forget plus gateway restart → `STORED_SCHEDULE_ONLY` advance to 15:10 → source 15:00, value equal to the stored text, `published_at` 15:10 (not 15:05), 293 envelopes, prior sequences unchanged → repeat advances and a third gateway restart leave the bytes identical → no private field on the IPC or in an envelope. A deleted schedule refuses MISSING with the bytes unchanged.
- Non-vacuity (each run against the committed tree, then `git checkout --`): exception removed → 14 failed and 3 errors; bound widened to two timesteps → 1 failed; RUN_VIRTUAL condition dropped → 1 failed (after adding the v5 test; before it this passed, which is why the v5 test exists); MISSING refusal removed → 1 failed; release basis made constant → 1 failed; `published_at` falling back to the scheduled instant → 1 failed.
- Full suites (Postgres on, `ASSETOPS_TEST_DATABASE_URL` per `backend/README-db.md`):
  - `pytest gateway/tests`: 125 passed.
  - `simulator` (run from `simulator/`): 265 passed.
  - `pytest host/tests backend/tests`: 1 failed, 2312 passed. The one failure was the pinned gated-route catalog (`test_simulator_lab_gate.py::test_enabling_the_gate_adds_only_the_simulator_lab_surface`). The three new paths were added by name, the T023/T025c precedent, and the file then passed 20/20. Only that test file changed after the full run, so the full run was not repeated.
- `tools/check-architecture.ps1` passed; `tools/check-agent-workflow.ps1` passed. Frontend untouched.

## Phase 3b needs

- `frontend/src/shell/runSetupClient.ts`: parse the three routes. Unknown refusal kinds currently map to REFUSED (`runPlayback.ts` ~296); add vocabulary for `PUBLICATION_CLOCK_NOT_SUPPORTED|_BACKWARD|PUBLICATION_AHEAD_OF_WORLD|PUBLICATION_SCHEDULE_UNREADABLE|_MISSING|PUBLICATION_INSTANT_INVALID`. Add `publication_clock` on profiles (Q1 from answers-3: show which clock the frozen selection uses) and `outbox_state` on seal refusals.
- `GatewayLedgerView.tsx` / `RunCommitPanel.tsx`: the schedule (pending, due and released with the three clock labels), an advance control, `release_basis_statement` after a restart, the diagnostics panel (GATEWAY_UNAVAILABLE as unavailable text, injected provenance labelled), F2 and F3, layout, then the full suites and the review packet.
- Fault injection stays fixture-only (questions-3 Q4).

## Risks

- Q1 interpretation (end-instant reading) awaits Architect confirmation.
- The read route does not separate NO_SCHEDULE from schedule-missing-after-execution (questions-3 Q3).
- A seal refusal after admission still leaves a delayed report PENDING until the next advance (phase-2 risk, unchanged).
