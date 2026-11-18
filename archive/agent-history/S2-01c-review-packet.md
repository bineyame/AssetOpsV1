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

Measured on an isolated runs store and gateway (the owner's `var/` and servers were not used), vite on 5320 against a host lab app on 8010. Command: `ASSETOPS_LAYOUT_S2_01C_RUN=run-f0c3b1d0... node tools/layout-evidence.mjs http://localhost:5320`.

- **S2-01c mode, after the fixes (HEAD `c8ec0a8`): ALL CLAIMS HOLD.** 1280x800: 9/9 PASS (no horizontal scroll, scrollWidth 1265 = clientWidth; publication and contact tables scroll in their own boxes, set not empty: 2 report rows, 8 contacts; no Resume/Retry). 640x700: 9/9 PASS (scrollWidth 625 = clientWidth 625). Fixture-injected Sealing refused table (Stage response intercepted over CDP, one READY TOO_LARGE row, labelled as fixture): 6/6 PASS at 640, own scroller, no page overflow.
- **640 overflow found and fixed.** Before the last fix the 640 check failed (scrollWidth 781 vs 625, `.app-frame`) and the cause was the ledger panel "The selected batch, exactly as sealed": its summary `<p>` (batch ID plus full SHA-256, unbroken) set the page minimum width. Fixed by `[data-gateway-batch-summary] { overflow-wrap: anywhere; }` (`c8ec0a8`, same shape as `4bc54d2` for the diagnostics last-stored line). Non-vacuous: the same check failed at 781 immediately before the fix and passes at 625 after.
- **Baseline on main `7c10283`** (temporary worktree, removed): the same ledger page at 640x700 measured scrollWidth 781 vs 625. So this overflow **predates S2-01c** (an S2-01b defect); S2-01c fixes it. (Main's frontend was run against the S2-01c host on the same store, so the Stage payload is S2-01c's; the long line is unchanged since S2-01b.)
- **Full `tools/layout-evidence.mjs` on the isolated store: not clean, stopped early.** 222 PASS, 6 FAIL, then the run died in "Draft run started at 1280x800" ("CDP Runtime.evaluate got no reply within 60000ms", renderer stopped answering); later sections were not measured. FAILs: "a ready draft still lists what the profile does not model [no optional-inputs panel]" x3 (READY draft run at 1280, 1000, 640) and, in Draft run started, "both configured reporting paths are drawn [6 configured signal rows]", "the declared reporting gap is drawn [0 gap rows]", "the gap row carries the declared instant... [0 cells]". These sections depend on specific scenario/draft fixtures with optional inputs and a declared reporting gap; the isolated store holds only five scenarios, so these are most likely isolated-store data gaps, **not proven** to be defects and not attributed to S2-01c. An earlier attempt on the same store failed differently (2 FAIL "all nine columns... [0 headers]", then "run-setup submit still disabled"); not reproduced this time, same likely cause, not diagnosed further. The full-run result is therefore **unverified for sections after this stop point**; run it on a store with the full fixtures before treating it as a regression check.
- Vitest 1232 passed (51 files) and `npm run build` OK after `c8ec0a8`.

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

## Fix round 1

Against `.agent/architect-S2-01c-answers-4.md` "First-review ruling" and `D-2026-10-09-s2-ordered-publication-and-closing-boundary`. Commits `f693d4e` (B1), `5cbbbc5` (Q3 host/API), `d7beec7` (C1, Q3 UI, B2), plus this closeout.

- **B1. Fixed.** The gateway's `admit_at_run_clock` now requires `at_instant` (the reports' reached boundary). It advances the run clock to that instant in the admission transaction. Once the clock has passed it, a report already admitted replays with its first identity, and a new admission refuses the whole chunk `PUBLICATION_INSTANT_PASSED` instead of being stamped late (`gateway/assetops_gateway/service.py` `_clock_at`, `_admit_in(replay_only=)`). The host admits each reached boundary after the schedule's durable `admitted_through` watermark at its own instant. Delayed reports due by then go first, then that boundary's undelayed readings, and every boundary is sealed (`host/gateway_publication.py` `publish_in_boundary_order`, `host/lab_execution.py` `_release`). Post-run leftovers go at the explicit advance instant, never backdated. Admitted envelopes are never rewritten.
  - The reviewer's probe is now a test, `test_run_to_end_and_single_steps_publish_the_same_bytes_at_source_instants`. Every undelayed envelope has `published_at == source_time` (293 envelopes). The closing-boundary observation is stamped 15:10 after the advance, and the midday report is stamped 07:15, ahead of the 07:15 readings of its source. `run_to_end` and repeated `step(1)` give identical envelope and batch bytes.
  - Retry and restart: `test_a_retry_after_a_failed_pass_resumes_in_order_with_the_same_bytes`, with link loss injected on the 20th admission, then a retry, a host restart and the post-run advance. Its final bytes equal a clean run's.
  - Skipped boundary: `test_a_boundary_the_gateway_clock_has_passed_is_refused_not_stamped_late`. The run's publication is refused and the refusal is shown. Nothing at or after the gap is admitted, and the watermark stays.
  - Gateway level: `test_an_admission_instant_moves_the_clock_with_the_admission` and `test_a_passed_instant_replays_but_never_stamps_a_new_admission_later`.
  - Non-vacuous: stamping every group at the pass target (the old behaviour) fails all 3 new host tests. Disabling `replay_only` fails the gateway test and the skipped-boundary host test. Both mutations were reverted with `git checkout`.
- **B2. Fixed.** `readyAdvanceButton()` waits for the suggested instant and an enabled Advance button before any click, in the refusal `it.each` and in the advance test. `gatewayPublication` + `runCommitPanel` run 10 times in a row: **10/10 passed**. That only shows the flake did not recur; it does not prove the race is gone.
- **C1. Fixed.** A RELEASED schedule row whose gateway outcome is `HELD` renders as state `HELD`, "Submitted, held by the gateway". Its published-at cell reads "Held by the gateway (HELD): no envelope and no publication instant", and the summary counts it as held. "not readable from the gateway" remains only for an admitted release with no readable Stage envelope. Tests cover both; reverting the HELD state fails the test.
- **Q3. Fixed.** `HostLabExecution.publication_schedule` refuses `PUBLICATION_SCHEDULE_MISSING` for an executed run with no stored schedule and no live session, the same condition as the advance refusal. The API returns `status: SCHEDULE_MISSING` with the detail. The UI shows "executed, but its publication schedule is missing ... not an empty queue", with no counts and no Advance. `NO_SCHEDULE` stays for not started. Tests: host, API, UI; removing the UI branch fails the test.
- **Wording.** No product UI string said "in-interval final sample". Test docstrings now say "closing-boundary observation". The shipped scenario YAML and the v1/v2 manifests are unchanged, including their comments, so their fingerprints and sealed bytes are preserved.
- **Not done (carried per ruling):** C2, C3.

### Checks (fix round 1, HEAD after `d7beec7`)

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` / `check-agent-workflow.ps1` | passed / passed |
| `pytest gateway/tests` | 127 passed |
| `pytest host/tests backend/tests` (Postgres on) | 2318 passed, 0 skipped (829 s) |
| `pytest` (simulator/) | 265 passed |
| `npm.cmd test` (frontend) | 51 files, 1235 passed |
| `npx.cmd tsc --noEmit` / `npm.cmd run build` | exit 0 / built (chunk-size warning only) |
| Layout, S2-01c mode, isolated store (vite 5320, lab app 8010, own gateway), run `run-32df7374...` | 1280x800 9/9 PASS; 640x700 9/9 PASS; fixture Sealing-refused 640 6/6 PASS; publication table 2 rows, 8 contacts |

Layout limit: the run had neither a HELD row nor a SCHEDULE_MISSING paragraph, so the 640 width of the two new strings is **unmeasured**. Both are plain wrapping text in an existing scroll box or paragraph.

### Fix-round deviations and risk

- Batches are now sealed per boundary, so a full run seals many small batches: 292 envelopes in 245 batches in the layout run. See questions-5 Q1.
- A passed boundary stops the run's ordinary publication for good, and there is no repair control (questions-5 Q2).
- New open questions: `.agent/S2-01c-questions-5.md` (Q1-Q5, fail-closed, built).

## Fix round 2

Against `.agent/architect-S2-batch-answers-2026-10-09.md` ("S2-01c re-review R1 and questions-5", items (1)-(4)) and `D-2026-10-09-s2-publication-gap-and-batch-boundary`. Commit `803f62f` (code and tests), the layout-tool commit, and this closeout. Not worked, as directed: N1, N2, C2 and C3.

- **R1 (1). Fixed.** A stored-schedule-only advance (no live session) refuses `PUBLICATION_GAP` when the schedule's contiguous `admitted_through` is absent or earlier than `world_reached_instant` for a run that has reached a boundary. The refusal detail names both instants, and `ordinary_stopped_at` when the gap is terminal. It is raised in `host/lab_execution.py` `advance_publication`, after the backward and ahead-of-world checks and before `_release`. The Lab clock is not written, the gateway is not called, and nothing is sealed or released. Q3: a delayed report never leaps a gap. On the live path, `_release` stops at the first refused boundary group, so neither the tail nor any later group is admitted. On the stored-only path, the preflight refuses. The new kind is in `LAB_CONTROL_REFUSALS` with its statement, and the API returns it as a 409 `EXECUTION_PUBLICATION_GAP`.
- **Q2 (2). Watermark and state persisted and exposed.** `PublicationSchedule` gains `world_boundaries_completed` and `ordinary_stopped_at`, and derives `ordinary_publication()`: NOT_STARTED, CONTIGUOUS, COMPLETE, INCOMPLETE or TERMINAL_GAP. `_release` records `ordinary_stopped_at` when the gateway refuses an ordinary boundary group `PUBLICATION_INSTANT_PASSED`. The schedule read and the advance answer carry `admitted_through`, `ordinary_publication` and `ordinary_stopped_at`, all labelled `RUN_VIRTUAL`. In the Lab panel:
  - an "Ordinary publication" fact (`data-ordinary-publication`);
  - for INCOMPLETE and TERMINAL_GAP, a bold "This run is not fully published." paragraph (`data-publication-gap`) with both instants. TERMINAL_GAP adds the passed boundary and "Start a new run";
  - the refused advance as `data-publication-refusal="PUBLICATION_GAP"` in plain words.
  
  A live session still retries while the gateway clock permits the boundary. After that, the terminal `PUBLICATION_INSTANT_PASSED` is kept, as ruled.
- **Q5 (3). Fixed.** `publication_schedule` and `advance_publication` refuse `PUBLICATION_SCHEDULE_MISSING` for an executed run with no schedule even when a live session exists. `_stage_registered_virtual` creates a schedule only before the run's execution artifact exists, which is the first start and comes before any gateway submission. Afterwards a missing schedule is a staging note `PUBLICATION_SCHEDULE_MISSING`, and the schedule is never rebuilt.
- **Tests (4).**
  - **The reviewer's probe, as a host test:** `test_a_stored_only_advance_refuses_a_known_ordinary_gap_before_anything_moves`. It runs `_FailingLink(fail_at=20)`, `run_to_end`, a host restart, then `advance_publication(PAST_DUE)`. Result: PUBLICATION_GAP naming both instants. Stage envelope and batch bytes are unchanged, the gateway's persisted `publication_clock` row is unchanged (read from its sqlite), and the Lab schedule is equal to before. No `activate`, `admit*`, `seal` or `advance_publication_clock` request reached the link, and a repeat at 15:00 is also refused.
  - **Complete-schedule control:** `test_pending_at_completion_then_released_after_restart` now asserts the schedule is COMPLETE before its stored-only advance, which still releases the 15:00 report at 15:10.
  - **Live retry before the boundary passes:** the retry test asserts INCOMPLETE, then COMPLETE after the live retry.
  - **Terminal case:** the passed-boundary test asserts TERMINAL_GAP with `ordinary_stopped_at` 04:00. A live advance to 15:10 is refused `PUBLICATION_INSTANT_PASSED`, with every delayed report still PENDING and no new envelope. After a restart it is refused `PUBLICATION_GAP` and the Lab clock is unchanged.
  - **Q5:** `test_a_live_session_that_lost_its_schedule_reads_and_advances_missing`.
  - **API:** PUBLICATION_GAP 409 with both instants, and the watermark and state across five states in both the read and the advance answer.
  - **UI:** complete (no warning), an INCOMPLETE gap with a refused advance, TERMINAL_GAP, and a parse check that refuses an unknown state or a missing watermark.
- **Non-vacuous, each reverted with `git checkout`:**
  - Disabling the preflight fails the R1 and terminal tests ("DID NOT RAISE").
  - Letting a live step rebuild the schedule fails the Q5 test.
  - Restoring the live-session exception on the read fails the Q5 test.
  - Not recording `ordinary_stopped_at` fails the terminal test.
  - Never rendering the gap paragraph fails both UI gap tests.
  - Layout: changing the gap selector to INCOMPLETE fails both injected widths.
- **Kept:** per-boundary batches, the exact IPC body, and the sealed bytes. The byte-equality, retry and complete-run tests are unchanged and pass. Schedule documents stay version 1, and the new fields are optional with defaults.

### Checks (fix round 2, HEAD `803f62f` + layout tool)

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` / `check-agent-workflow.ps1` | passed / passed |
| `pytest gateway/tests` | 127 passed |
| `pytest host/tests backend/tests` (Postgres on) | 2329 passed, 0 skipped (645 s) |
| `pytest` (simulator/) | 265 passed |
| `vitest run` (frontend) | 51 files, 1239 passed |
| `npx.cmd tsc --noEmit` / `npm.cmd run build` | exit 0 / built (chunk-size warning only) |
| Layout, S2-01c mode, isolated store (vite 5320, lab app 8010, own gateway), run `run-0de38165...` | 1280x800 10/10 PASS (`data-ordinary-publication` COMPLETE); 640x700 10/10 PASS (scrollWidth 625 = 625); fixture Sealing refused 640 6/6 PASS; **fixture-injected TERMINAL_GAP + PUBLICATION_GAP refusal** 640 5/5 PASS and 1280 5/5 PASS (gap paragraph right edge 542 of 625 at 640, refusal paragraph 542; no page scroll) |

The gap case is FIXTURE-INJECTED. It rewrites the publication read and answers the advance with the 409 over CDP, because the layout run's live run has no gap. The live gap path is covered by the host tests above. All servers were stopped. The owner's ports and `var/` were not used.

### Fix-round-2 deviations and risk

- Schedules written by earlier branch code have no boundary count, so the gap is judged from the two instants alone. A run that was only started under that code reads INCOMPLETE (fail-closed; questions-6 Q1).
- On a terminal gap, a live-session advance still moves the Lab clock before the gateway refuses, as ruled (questions-6 Q2).
- New open questions: `.agent/S2-01c-questions-6.md` (Q1-Q5, fail-closed, built). Independent re-review of R1 is required before merge.
