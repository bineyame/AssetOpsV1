# S2-01c review: gateway diagnostics and fault scenarios

Reviewer: a fresh Claude reviewer (independent; authored none of this slice). This is the per-slice review; Codex reviews S2-01c and S2-02 together at the end of S2 (owner rule, 2026-10-09).

- Branch `task/S2-01c-gateway-diagnostics-faults`, HEAD `4ca159c`; diff reviewed `08712e7..4ca159c` (72 files, coordinator planning/decision/record commits included).
- Judged against `tasks/S2-01c-gateway-diagnostics-faults.md`, the four S2-01c decisions in `.ai/DECISIONS.md` and `.agent/architect-S2-01c-answers{,-2,-3}.md`. Open questions `.agent/S2-01c-questions-3.md` and `-4.md` are the Architect's to decide and are not ruled on here.

## Verdict

**Accept with findings fixed on the branch.** R1, the diagnostic wire and ledger, the counters and pressure, STOP, the Lab-private schedule, restart and replay, F2 and the layout fixes all hold up under reading and under the checks I re-ran. One finding (B1) must be fixed, or explicitly ruled acceptable by the Architect, before merge. It puts an undeclared publication delay on ordinary readings in the V3 wire, which S2-02 is told to interpret as simulated reporting delay. B2 is a small flaky-test fix. The rest can be carried.

## Findings

### B1 (block). Ordinary readings are stamped with the step's end instant, so they show a delay the scenario does not declare

- **Where:** `host/lab_execution.py`, `_stage_registered_virtual` (about lines 2495-2580) and `_release`. Every not-yet-admitted undelayed report in a step goes out in one `publish_at_run_clock` call at `target = max(reached, clock, target)`. `run_to_end` (line 2215) stages once, at the end.
- **What I saw:** a scratch probe (scratchpad only, no repo change) ran the post-run Draft with `start` and then `run_to_end`, the reviewer path in the packet. Result: 292 envelopes, **all `published_at = 2026-09-30T15:00:00Z`**, with source times from 03:00. Ordinary readings therefore carry up to 12 h of "publication delay". The one report the scenario actually delays is released at 15:10 and shows 10 min, so it looks the *least* delayed. A step of N boundaries does the same thing over N timesteps; `test_registered_publication_delay` uses `step(17)`, so the 03:00-06:45 readings are all stamped 07:00. The stamped bytes also depend on how the operator stepped: the same frozen run gives different V3 bytes after `step(1)` x48 than after `run_to_end`.
- **Why it matters:** `D-2026-10-09-s2-simulated-publication-clock` says that for SIMULATED evidence "`published_at - source_time` is a simulated reporting delay", and S2-02 carries that meaning centrally. answers-3 Q2 bounded the clock so that "later ordinary readings do not acquire a delay absent from the frozen scenario". This path gives earlier ordinary readings exactly that kind of delay, and it undercuts AC4's demonstration. The tests do not catch it because they assert only `published_at >= source_time` for undelayed envelopes (`test_registered_post_run_release.py:165`, `test_registered_publication_delay.py:226`).
- **Fix:** within a step, admit undelayed reports in boundary order, advancing the gateway run clock to each report's own reached boundary instant before admitting it. Then a cadence-aligned undelayed reading has `published_at == source_time`, whatever the step size. Release each due delayed report at the first boundary instant at or after its due time, in the same ordered pass; that also gives it a sequence before readings observed later. Add a test that a `run_to_end` and a step-by-step run of the same Draft give identical undelayed `published_at`. The delayed-case pins in the v1/v2 manifests should not change. If the Architect prefers the current semantics, record it as a decision and have S2-02 label it, because the wire cannot tell the two apart.

### B2 (block, small, test-only). A flaky refusal test in the new frontend suite

- **Where:** `frontend/src/shell/__tests__/gatewayPublication.test.tsx:410-428` (`it.each` "names the %s refusal in plain words and moves nothing").
- **What I saw:** 2 of 5 focused runs failed one case, each time a different kind: a 10 s `waitFor` timeout with "no [data-publication-refusal=…]". Example: `PUBLICATION_SCHEDULE_MISSING`. The full `npm.cmd test` run passed 1232/1232.
- **Likely cause:** after `settledScreen()`, the click can land before `PublicationSchedulePanel`'s passive effect sets `instant` from `suggestedInstant`. The button is still disabled (`instant.trim() === ""`), so the click does nothing and no refusal is ever rendered.
- **Fix:** wait until the advance button is enabled, or until the input holds the suggested value, before clicking. A flaky test makes the packet's green-suite number unreliable.

### C1 (carry). A HELD delayed report reads as released and says its publication time is unreadable

- **Where:** `frontend/src/shell/GatewayPublicationPanels.tsx:285-293`. `contracts/assetops_contracts/publication_schedule.py` `released()` marks a submitted report RELEASED whatever the gateway answered.
- **What:** if the gateway holds a due delayed report, the row reads "Released to the local gateway", sequence "none", and published at "not readable from the gateway". The last phrase suggests a read failure when the report was actually held. The payload already carries `outcome`, but the view does not render it.
- **Fix:** show the HELD outcome, for example "Held by the gateway; no envelope", and keep "not readable" for a Stage that could not be read. It is unlikely in the shipped fixtures, which is why it is a carry.

### C2 (carry). AC5 diagnostic bytes across a real reconnect are not asserted

- **Where:** `host/tests/test_registered_publication_delay.py`, `test_link_loss_keeps_the_report_pending_and_reconnect_releases_it_once`.
- **What:** AC5 says that after reconnect "sealed batches and diagnostics remain byte-identical and pending". The test compares envelope and batch bytes but not stored diagnostics. Diagnostic identity and bytes surviving a restart are proven only at service level (`gateway/tests/test_gateway_diagnostics.py::test_emission_is_one_identity_per_cadence_slot_and_survives_restart`).
- **Fix:** read the stored diagnostics before the kill and assert that the same rows, still READY, exist after reconnect.

### C3 (carry, residual). The full layout regression run is unverified past its stop point

The packet is honest about this. The S2-01c mode passes 9/9 at 1280 and at 640, and 6/6 for the fixture-injected Sealing refused table at 640. The full `tools/layout-evidence.mjs` run on the isolated store stopped at "Draft run started" with 6 FAILs that are plausibly store-data gaps, and it is not recorded as a pass. I could not rerun it (it needs Chrome, a backend and a dev server). Run it on a fully seeded store before S2 closes.

### Notes, not findings

- The diagnostics panel lives on the registered run page rather than on a Gateway & Ingestion page (questions-4 Q2), and F2 treats a basis-less Stage as unknown (questions-4 Q1). Both are open with the Architect, and both have fail-closed defaults.
- The packet tells reviewers to use `git diff main...HEAD`, but the slice base is `08712e7`. They resolve to the same base in practice, but the dispatch named `08712e7..HEAD`.
- `pytest gateway/tests host/tests …` in one invocation fails at collection with 4 errors (module-name clash between the suites). Run separately, each passes. This predates the slice and is how the packet ran them.

## Acceptance criteria, as verified

1. **R1. Met.** Migration 3 re-keys `seal_refusal` by `outbox_state` and carries each v2 row with its unbatched envelope's state. Write, delete and lookup all filter by state, and the reader groups by state. Mixed-state, restart and migration tests exist.
2. **Diagnostic wire and ledger. Met.** Exact key set, bounded parse and a digest that excludes itself, all matching the technical design. Sequence and bytes are inserted in one transaction, with one row per cadence slot. Triggers make the bytes immutable and the config frozen. `server_received_at` is never written and no ACKED row exists. The config is returned with the read, and the ticker thread runs under the IPC lock.
3. **Counters and pressure. Met.** Queue counts come from `STAGED|READY|IN_FLIGHT` using real-UTC `created_at`, with the full breakdown. `mapping_error_count` uses the six kinds. Contact is `OBSERVED_SIMULATED_REPORT` at real UTC and null if never heard. Offset is null unless injected. STOP refuses whole calls before any write (`_refuse_at_stop` precedes the clock read and the admissions). An unmeasurable probe is STOP. An unreachable gateway is `GATEWAY_UNAVAILABLE` with no counters.
4. **Delayed local admission. Mechanically met; B1 open.** The Lab-private schedule is written before submission. Releases stamp the actual instant and are never backdated. Backward, ahead-of-world and missing-schedule cases refuse, and the post-run release after a restart is proven on the real gateway. No private field crosses (checked by the tests on recorded requests). The setup exception (`_post_run_release_window`) is as narrow as answers-3 says, and the GATEWAY_UTC delay refusal remains. B1 is what the undelayed readings carry on the same clock.
5. **Faults and Lab view. Met, with C2.** Link loss, reconnect, WARN and STOP go through the real IPC. The view labels every clock, says unavailable instead of showing an empty queue, and never presents a diagnostic as device health.
6. **F2 and F3. Met.** `releaseBasisBlock` offers no Resume or Retry while the read is pending, unavailable, not found or basis-less. The 640 overflow (an S2-01b defect, shown on the main baseline) is fixed by `overflow-wrap` on the two hash lines. C3 is residual.

## Checks I ran (HEAD `4ca159c`)

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | Architecture check passed |
| `tools/check-agent-workflow.ps1` | Agent workflow check passed |
| `pytest gateway/tests` | 125 passed |
| `pytest host/tests/test_registered_publication_delay.py test_registered_post_run_release.py test_lab_execution.py` | 107 passed |
| `pytest backend/tests/test_s2_publication_lab_api.py test_simulator_lab_gate.py test_scenario_fingerprints.py` | 48 passed |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npm.cmd test` (frontend, full) | 51 files, 1232 passed (it ran in this session; the expected sandbox esbuild failure did not occur) |
| `npx.cmd vitest run gatewayPublication + runCommitPanel`, 5 runs | 3 passed 34/34; **2 failed 1 test each** (B2) |
| `npm.cmd run build` | built, chunk-size warning only |
| Scratch probe: run-to-end on the post-run Draft | 292 envelopes, all `published_at` 15:00Z (B1) |

**Not run by me:** the full host and backend suite with Postgres (the packet reports 2313), the simulator suite (265), the live reviewer path with the gateway, `lab_app` and vite, and `tools/layout-evidence.mjs`. Those numbers are the Implementer's and I have not verified them.

## Residual risk not named in the packet

- B1's semantics reach S2-02's central interpretation unless they are fixed or ruled on first.
- The diagnostics ticker swallows every exception (`ipc.py` `start_diagnostics`), so a persistent `CLOCK_BEHIND` or a storage failure leaves no local trace beyond the absence of new rows. The local read still shows live state, so this is acceptable for S2-01c, but S2-02 should surface the last emission failure.
