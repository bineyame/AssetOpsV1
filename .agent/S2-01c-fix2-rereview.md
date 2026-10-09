# S2-01c fix round 2: re-review

Reviewer: a fresh Claude reviewer. I am independent and authored none of this slice, its fix rounds, or the earlier reviews. This re-review covers `a2d409d..2797ccc` on `task/S2-01c-gateway-diagnostics-faults` (commits `803f62f`, `70e5f19`, `2797ccc`). I judged it against the Architect's fix list in `.agent/architect-S2-batch-answers-2026-10-09.md` ("S2-01c re-review R1 and questions-5", items (1)-(4)), `D-2026-10-09-s2-publication-gap-and-batch-boundary`, R1 in `.agent/S2-01c-fix-rereview.md`, and the task file. Questions-6 belong to the Architect and are not ruled on here. N1, N2, C2 and C3 stay carried, as ruled.

## Verdict

**Accept.** R1 is fixed as the ruling directs. A stored-schedule-only advance now refuses `PUBLICATION_GAP` before the Lab clock, the gateway or a seal moves. The watermark and the ordinary-publication state persist, the read and the advance answer carry them, and the Lab panel shows them plainly. Q5 is consistent across read, advance and later live steps. The tests reproduce the R1 probe and the complete-schedule control. I found one carry-level wording issue (N3) and no block.

## Fix list, as verified

- **(1) Preflight refusal. Fixed.** `host/lab_execution.py:2687-2702`: `if session is None and schedule.ordinary_gap()` raises before `note`/`_release`. `_release` is the first place that writes `clock_instant` or calls the gateway (`:2597`, `:2617`), so the refusal precedes both clocks, any admission, seal or release. The order after the existing BACKWARD and AHEAD_OF_WORLD checks is sound. `test_a_stored_only_advance_refuses_a_known_ordinary_gap_before_anything_moves` is the R1 probe as a test. It asserts that the Stage bytes, the gateway's sqlite `publication_clock` row and the Lab schedule are all unchanged, and that no `activate`, `admit*`, `seal` or `advance_publication_clock` request was sent. I also ran my own variant: a fault on the **last step of a mid-run** (world not complete, reached 12:45, admitted through 11:45), then a host restart, then a stored-only advance to the reached instant. The advance was refused `PUBLICATION_GAP` with both instants, the Stage bytes, the gateway clock and the schedule were unchanged. The ruling's complete-schedule control holds: `test_pending_at_completion_then_released_after_restart` asserts COMPLETE before the stored-only release.
- **(2) Watermark, world reached and incomplete/terminal state exposed. Fixed.** `contracts/assetops_contracts/publication_schedule.py:73-94` adds `world_boundaries_completed`, `ordinary_stopped_at` and `ordinary_publication()`. In `_release` (`lab_execution.py:2622-2641`), `through` still advances for empty boundary groups, so a boundary with no ordinary readings does not create a false gap. `stopped_at` is recorded only for a boundary group refused `PUBLICATION_INSTANT_PASSED`. `publication_schedule_payload` carries `admitted_through`, `ordinary_publication` and `ordinary_stopped_at` with `RUN_VIRTUAL` labels, and the advance answer reuses the same payload (API test across five states). The panel adds an "Ordinary publication" fact, a bold "This run is not fully published." paragraph for INCOMPLETE/TERMINAL_GAP, and the typed refusal. `isRunPublicationSchedule` refuses an unknown state.
- **(2, live terminal path).** A live advance on a TERMINAL_GAP keeps `PUBLICATION_INSTANT_PASSED`. Every delayed report stays PENDING and no envelope is added (`test_a_boundary_the_gateway_clock_has_passed_is_refused_not_stamped_late`). The Lab clock still moves forward on that path, which is questions-6 Q2 and the Architect's to decide; the ruling's "before either clock moves" is scoped to the stored-only advance.
- **(3) Missing schedule. Fixed.** Read (`:2756`), advance (`:2668`) and live staging (`:2515-2526`) now share `_executed_id`. `start()` stages (`:2179`) before `note_running`/`write`, so only the first start can create a schedule. `test_a_live_session_that_lost_its_schedule_reads_and_advances_missing` proves a later step does not rebuild it.
- **(4) Tests.** All present and pass (below). The packet's non-vacuity reverts are plausible; I did not repeat them.
- **Kept.** Per-boundary sealing, the exact IPC body and the sealed bytes are unchanged. `gateway_publication.py` is not in the diff.
- **Layout evidence.** The packet records the gap case as FIXTURE-INJECTED over CDP and names why (a valid live run has no gap). I confirmed the honesty of that label in `tools/layout-evidence.mjs`. The injected rows use the real panel selectors, so the injection does not stand in for rendering. I did not rerun it.

## Findings

### N3 (carry, wording). The PUBLICATION_GAP refusal text says "the world's last boundary", which is wrong mid-run

- **Where:** `frontend/src/shell/GatewayPublicationPanels.tsx:60`.
- **What:** the text reads "Ordinary publication stopped before the world's last boundary". My mid-run probe shows the refusal also fires when the world has not completed (reached 12:45 of a 15:00 interval). Then "last boundary" reads as if the run had finished. The backend statement (`lab_projection.py`, "before the boundary its world reached") and the gap paragraph's explicit instants are both correct, so the operator is not misled about what was published.
- **Why carry:** the wording is imprecise but nothing is mis-stated as published, and the instants shown next to it are right. **Fix:** say "before the boundary the world reached", matching the backend statement.

No block findings.

## Checks I ran (HEAD `2797ccc`)

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `pytest host/tests/test_registered_post_run_release.py host/tests/test_registered_publication_delay.py backend/tests/test_s2_publication_lab_api.py` | 47 passed |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run src/shell/__tests__/gatewayPublication.test.tsx` | 22/22 passed (vitest did run under this session) |
| Scratch probe (temporary file in `host/tests`, deleted after): last-step fault mid-run, then host restart, then stored-only advance | `PUBLICATION_GAP` with both instants; Stage bytes, gateway clock row and schedule unchanged |

**Not run by me:** the full host and backend suite with Postgres (2329), the gateway suite (127), the simulator suite (265), the full frontend suite (1239), `npm.cmd run build`, and `tools/layout-evidence.mjs`. Those numbers are the Implementer's. I started no servers. Each gateway process the probe started was killed in its `finally`. The working tree is as I found it (only `.agent/coordinator-handoff.md` modified, by another role).

## Residual risk not named in the packet

- After a host restart, the Stage panel's `STAGED` statement ("Every report the gateway admitted ... is in a sealed local batch") does not mention the gap, and the live session's staging notes are gone. The gap is visible only in the publication panel next to it. The statement is accurate, because it is scoped to admitted reports, but S2-02 should take the gap state from the schedule, not infer completeness from `STAGED`, before it treats a run's batches as a complete upload set.
- A run with no gateway configured at its first start never gets a schedule. It reads `SCHEDULE_MISSING` afterwards, which is consistent with Q5 and fails closed. Recovery is a new run.
