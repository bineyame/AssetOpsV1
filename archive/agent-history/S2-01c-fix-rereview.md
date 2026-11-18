# S2-01c fix round 1: re-review

Reviewer: a fresh Claude reviewer (independent; authored none of this slice or its fix round). Re-review of `fb4edae..84a71e6` on `task/S2-01c-gateway-diagnostics-faults` (commits `f693d4e`, `5cbbbc5`, `d7beec7`, `84a71e6`), against `.agent/architect-S2-01c-answers-4.md`, `D-2026-10-09-s2-ordered-publication-and-closing-boundary`, the task file and the prior review `.agent/S2-01c-review.md`. Questions-5 is the Architect's to decide and is not ruled on here; C2 and C3 stay carried per the ruling.

## Verdict

**Accept with findings fixed on the branch.** B2, C1 and Q3 are fixed. On the live-session path, B1 is fixed as the ruling directs. The gateway now stamps each first admission at its own boundary, `run_to_end` and single steps give the same bytes, and a passed boundary refuses instead of stamping a late time. One path the ruling names explicitly, a fault followed by a host restart, still closes a publication gap without exposing it (R1). Fix it, or have the Architect rule on it, before merge.

## Findings

### R1 (block). After a failed pass and a host restart, the post-run advance releases delayed reports past a known gap, silently and for good

- **Where:** `host/lab_execution.py` `advance_publication`, no-session branch (about line 2684): `self._release(run.run_id, run.registered_basis, schedule, instant, note)` with no `instants`/`ordinary`. `_release` then builds only the `tail` group at `target`. `admitted_through` is not checked, and `publish_in_boundary_order` moves the gateway clock to `target`.
- **What I saw:** a scratch probe in the scratchpad (no repo change) reused `_FailingLink(fail_at=20)` from `test_registered_post_run_release.py`. It ran `start`, then `run_to_end` (the pass fails at `admitted_through = 07:30`, with 114 envelopes), then a host restart, then `advance_publication(PAST_DUE)`. Result: `publication_refused: None`, `release_basis: STORED_SCHEDULE_ONLY`, and 115 envelopes against a full 293. The closing-boundary SOC was released at 15:10 with sequence 39, directly after the pre-gap readings. `admitted_through` stays at 07:30. The 07:45-15:00 ordinary readings (178) can never be admitted now, because the clock has passed them and they would refuse `PUBLICATION_INSTANT_PASSED`. Nothing in the advance answer or the schedule read says they are missing: `admitted_through` is not in `publication_schedule_payload`. On the wire the source's sequence has no hole, so a consumer cannot tell either.
- **Why it matters:** the decision says "no unadmitted earlier ordinary report may be silently [...] because batching, restart or a fault skipped its boundary ... refuse or expose the missing publication". questions-5 Q2 states the invariant "nothing later is admitted, so no later reading gets a sequence ahead of the gap", and this path breaks it. The existing retry test avoids the case, because it retries with a live session before restarting. The task's "a no-session advance releases stored delayed reports only; it does not claim an unadmitted undelayed series was regenerated" is satisfied in the letter. The gap is still neither refused nor exposed.
- **Fix:** in the no-session path, when `schedule.admitted_through` is earlier than `world_reached_instant` (or is `None` for an executed run that has ordinary readings), either refuse the advance with a typed kind before the gateway clock moves, or release and expose the gap explicitly: put `admitted_through` or "ordinary publication stopped at X" into the advance answer and the schedule read, and show it in the UI. Which one is a product choice; the Architect can decide it alongside questions-5 Q2. Add the probe above as a test.

### N1 (carry, test quality). The channel test no longer asserts which refusal it gets

- **Where:** `gateway/tests/test_gateway_process.py:202-203`. `pytest.raises(GatewayRequestRefused)` no longer checks `.kind`.
- **What:** the test intends to prove that a body without `at_instant` is refused as an exact-body violation, but any refusal kind passes. The old `NO_PUBLICATION_CLOCK` assertion over the channel is gone. That is expected, because `_clock_at` now creates the clock on first admission, but nothing replaced it.
- **Fix:** assert the specific kind the IPC returns for a key-set mismatch. It is low risk, so it is a carry.

### N2 (carry, residual). The 640 px width of the two new strings is unmeasured

The packet states this honestly. The isolated-store layout run had no HELD row and no SCHEDULE_MISSING paragraph. Both are plain wrapping text in existing containers. Fold it into C3's full seeded layout run before S2 closes.

## Ruling items, as verified

- **B1 (live path). Fixed.** `_clock_at` advances the clock inside the admission transaction. `replay_only` refuses new admissions once the clock has passed the boundary and still answers replays with their first identity. The host groups ordinary readings by their own boundary instant, puts due delayed reports first, seals every boundary and persists the `admitted_through` watermark. The tests cover byte equality between `run_to_end` and steps, `published_at == source_time` for undelayed readings, the delayed-first sequence order at 07:15, retry-then-restart and the skipped boundary. The `tail` merge branch in `_release` (target <= last) is unreachable but harmless. A partly committed chunked group replays correctly on retry, because the clock equals that group's instant.
- **B2. Fixed.** `readyAdvanceButton()` waits for the suggested value and an enabled button. I ran the focused file 4 times and it passed 18/18 each time.
- **C1. Fixed.** HELD renders as "Submitted, held by the gateway" with no envelope or publication instant, and "not readable" is kept for a Stage-read gap. The gateway produces only `ADMITTED`, `ALREADY_ADMITTED` and `HELD`, so no other envelope-less outcome is left unhandled.
- **Q3. Fixed.** Host, API and UI return `SCHEDULE_MISSING` under the same condition as the advance refusal, and `NO_SCHEDULE` remains for a run not yet started. The live-session nuance is questions-5 Q5.
- **Wording. Fixed.** No product string, packet text or task text says "in-interval final sample". The shipped YAML and manifests are unchanged.

## Checks I ran (HEAD `84a71e6`)

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `pytest gateway/tests` | 127 passed |
| `pytest host/tests/test_registered_post_run_release.py test_registered_publication_delay.py backend/tests/test_s2_publication_lab_api.py` | 37 passed |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run src/shell/__tests__/gatewayPublication.test.tsx` x4 | 18/18 each run |
| Scratch probe: fault, then restart, then post-run advance | R1 reproduced (115/293 envelopes, no refusal) |

**Not run by me:** the full host and backend suite with Postgres (2318), the simulator suite (265), the full frontend suite (1235) and build, and `tools/layout-evidence.mjs`. Those numbers are the Implementer's. I started no servers; the probe's gateway process was killed in its `finally`.

## Residual risk not named in the packet

- Per-boundary sealing (questions-5 Q1) makes many small batches: 245 for 292 envelopes. S2-02's central ingestion and batch-ACK cost scale with that. This is for the Architect, not a defect.
- A `PUBLICATION_INSTANT_PASSED` stop (questions-5 Q2) is permanent for the run, and the live-session path exposes it only as a staging note. Like R1, the schedule read does not show where ordinary publication stopped.
