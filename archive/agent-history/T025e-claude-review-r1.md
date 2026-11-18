# T025e re-review after fix round R1

Reviewer: **Claude**. This is a fresh `assetops-reviewer` instance. It did not
author the slice or the R1 fixes, and it did not produce the first review. It
works under the temporary binding in `.ai/ROLE_CONFIG.md`: the Reviewer is
Claude until the Codex reset at 2026-10-03 21:23. A Claude review of Claude
work is weaker than a Codex one, so a later reader may send finding R1-1 back
to Codex.

## Scope

- **Commits reviewed:** the R1 commits `63046eb..35c013f` (b7d521a, e3f0c3a,
  696fc21, ccd538d, 35c013f), on `task/T025e-cockpit-organisation-and-live-playback`.
- **Read in context:** the whole slice diff (`main...HEAD`).
- **Judged against:**
  - the owner's R1 decisions: fix findings 1 (option A), 2, 4 and 5; carry 3,
    6, 7, 8 and 9;
  - AC1-AC6 of `tasks/T025e-cockpit-organisation-and-live-playback.md`;
  - the R1 section of `.agent/T025e-review-packet.md`.

## Verdict: REJECT (narrow). Fix R1-1 on the branch, then re-review.

Findings 2, 4 and 5 are fixed as asked, and they are tested. Finding 1 is fixed
for **correctness**. Selecting exposures by the step that recorded them removes
the silent duplicate. The server fold now equals the full read from any base,
and I checked this on the mid-step fixture. That was the severe half of
finding 1.

The **refusal** half is still open whenever more than one forcing address is
active. The R1 client check requires a delta's exposures to be in ascending
`from_offset` order. The kernel does not record them in that order: it records
them in `(address, from_offset)` order. So a mid-step window at any address
that is not last in sort order is refused, and a full read follows in the
middle of play.

This contradicts two things:

- the packet's R1 claim, "every delta accepted so no full read";
- AC6's "none between first step and terminal".

It happens on a legal input, and it happens on the mini-grid's ordinary shape,
which has five concurrent forcing addresses. It fails safe: the refusal is
stated, and nothing wrong is drawn. The fix is small. If the owner prefers a
carry under `D-2026-09-22-milestone-speed-over-purity`, it qualifies: it is
local, reversible and honest. But it is the unfinished half of a reject-level
finding, so I do not carry it on my own authority.

## Findings

### R1-1. MEDIUM: a mid-step window at a non-last address is refused as out of order (acceptance gap: AC6, and the R1 claim for finding 1)

**Where.**

- `frontend/src/shell/liveHistory.ts:249`: the step-owned branch refuses
  `key < previous` over raw `from_offset`.
- `simulator/assetops_simulator/kernel/execute.py:1937`: the boundary's
  `forcing_exposures` are sorted by `(address, from_offset)`.
- `host/lab_history.py:194`: the history keeps that order, boundary by
  boundary.

**What is wrong.** Take one step that holds two addresses. Address A's window
opens mid-step at t_k+2. Address B's exposure starts at t_k. If A sorts before
B, the step's rows arrive as `[A@t_k+2, B@t_k]`. The client refuses this with
`ROW_OUT_OF_ORDER`. The server's own full read is not ordered by `from_offset`
either, so the client is imposing an order the wire never promised for this
family. That order held before R1 only because every fixture window was aligned
to a 5-minute boundary.

**Reproduced.** The probe scripts lived in scratch and were not committed.

1. I ran `draft(PROLONGED)` with `mill-demand-1` lengthened to 62 minutes and
   `mill-demand-2` moved to offset 62. The run stays `READY`.
2. I drove `live_captures` and took the route's one-boundary delta for each
   step. The delta `since 12 -> 13` carries `load-clinic@60, load-mill@60,
   load-mill@62, load-res@60, irradiance@60`.
3. I compiled `liveHistory.ts` with `tsc` and ran `appendHistory` on that base
   and delta. The result was `{"refused":{"reason":"ROW_OUT_OF_ORDER",
   "statement":"A exposures row at 60 follows one at 62."}}`.
4. The fuel fixture passes only because it has one forcing address.

**Why it matters.**

- Every step in which a window opens mid-step at a non-last address costs a
  refused delta.
- The next tick then makes a full read, which is about 72 KB on the mini-grid.
- This breaks AC6 and that tick's budget.
- The packet records the mid-step case as covered.

A load step change at 07:02, or an irradiance change inside a step, is exactly
what an authored scenario does.

**Fix.**

- **Client.** In the step-owned branch, check order by the owning step, not by
  the raw key. The owning step is the last new boundary at or before the row's
  `from_offset`, and the check requires it to be non-decreasing. Alternatively,
  drop the within-step order check for step-owned families: the
  `>= first-new-boundary` check already rules out duplicates, and nothing
  downstream relies on `from_offset` order, since the full read is not in that
  order either.
- **Server.** No change is needed.
- **Fixture and tests.** Add a multi-address mid-step fixture, for example the
  mini-grid edit above, to `make_history_fixtures.py`. Add a client test that
  accepts every delta and folds to the full read. The host prefix and fold
  tests already pass on such input; my probe confirms the server side.

### R1-2. LOW: the load-history guard compares recorded counts across runs (carry)

**Where.** `frontend/src/shell/runFrameState.ts:189-199`.

**What is wrong.** The new `HISTORY_READ` guard discards a load read that
records fewer boundaries than the history already held. Unlike
`laterExecution` (`runPlayback.ts:104`), it does not check that the two belong
to the same `run_id`.

R1 also chains the load after `commits.current`. So when `runId` changes on
the same `RunFrame` instance while a commit is in flight, events land in this
order:

1. the old run's `TICK_COMMITTED`;
2. `RESET`;
3. the new run's load.

If the old run recorded more boundaries, the guard discards the new run's
history, and the old run's history stays on the new run's page.

Before R1 this was a timing race. R1 makes the landing order deterministic. I
found no in-app run-to-run navigation (no `navigate(` in `shell`), so this is
reachable only through browser history between two run pages.

**Fix.** Add `run_id` equality to the guard, mirroring `laterExecution`. Or
drop a commit whose `runId` is no longer the current one.

### R1-3. LOW: a timed-out history read is ignored but not cancelled (residual risk, carry)

**Where.** `frontend/src/shell/RunFrame.tsx:137` (`withinTimeout`).

**What is wrong.** On expiry, the fetch keeps running. Each hung read that
expires is followed by a full read on the next tick. Under HTTP/1.1, repeated
hangs therefore hold open the browser's six per-host connections, and later
steps and reads queue in the browser rather than on the host. This is bounded
by the step timeout, and play stays honest.

The first review suggested an `AbortController`. The packet does not name
this residual.

**Fix.** Pass an `AbortSignal` through `getExecutionHistory` and
`getExecutionHistorySince`, and abort on expiry.

### R1-4. NIT (preference): the host test writes its scratch run into the source tree

**Where.** `host/tests/test_lab_history_prefix.py:55`.

**What is wrong.** The test writes `host/.pytest_mid_step_run.yaml` and unlinks
it in `finally`. It works, but it writes into the repository and would collide
under parallel test workers. `make_history_fixtures.py` uses `tempfile`
instead.

**Fix.** Use `tempfile.mkdtemp()` here as well.

## What I checked holds

- **Finding 1, server.**
  - `simulator_lab_api.py:1458-1462` selects exposures by
    `from_offset >= boundaries[since].offset_minutes`, and returns none when
    `since` equals the recorded count.
  - This matches the kernel: `exposed_from = max(world.offset, start)` lies in
    `[t_k, t_{k+1})`.
  - The rows are recorded values, and nothing is computed.
  - Intervals and `electrical_steps` are unchanged.
- **Finding 1, client, single address.**
  - The fold from the base, and from a rebased full read, has no duplicate. So
    the 49-versus-50 case is closed.
  - A held-step row is refused.
  - Missing an upper bound is stated, and cannot be stated from a delta.
- **Finding 2.**
  - Both commit reads and the load read are bounded. Expiry commits
    `unavailable`, so the existing lag line and the full read on the next tick
    handle it.
  - The screen test shows play reaching `TERMINAL`, the hung delta asked once,
    and three history reads.
- **Finding 4.**
  - The load reads now wait on the chain.
  - `EXECUTION_READ` goes through `laterExecution`.
  - A lower-recording `HISTORY_READ` is discarded, subject to R1-2 above.
- **Finding 5.**
  - `kind: "unrecorded"` applies only to a terminal run with a whole read that
    still lags.
  - I checked that this happens only with a `without_history` source.
    `boundaries_completed` is `len(world.boundaries)`, so a failed run's
    persisted prefix has no lag (`test_lab_history.py:432-435`), and the new
    sentence cannot misdescribe a partial record.
- **Carries.** Backlog entries C1-C5 carry findings 3, 6, 7, 8 and 9 accurately,
  each with a repair and a trigger. The packet's budget section now states what
  "tick commit" and "server delta" measure, and names the scaling.

## Checks run by this reviewer

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `npx.cmd tsc --noEmit` | clean (exit 0) |
| host `test_lab_history_prefix.py`, `test_lab_history.py` and `contract9_gate` | 94 passed |
| `pytest backend/tests -q` | 1316 passed, 2 warnings |
| `npm.cmd test -- --run src/shell` | 29 files, 648 passed |
| `npm.cmd test -- --run` (full) | 38 files, 993 passed (984 + 9 new) |
| probe: multi-address mid-step one-boundary deltas through `appendHistory` | refused, `ROW_OUT_OF_ORDER` (R1-1) |
| probe: exposure order in one-boundary deltas on the three committed fixtures | ordered; the only multi-address fixture has no mid-step window |

The frontend suite **did run** under this session, although the standing brief
says it usually cannot. I report the numbers I saw.

## Not verified

- **Layout evidence.** `tools/layout-evidence.mjs` was not run: it needs
  Chrome, the backend and a dev server. R1 changes no layout or rendering: the
  lag span's new text and attribute sit in the existing slot. So the 438 PASS
  from before R1 stands as recorded, and was not re-run.
- **Production build.** `npm.cmd run build` was not run.
- **Simulator suite.** Not run. R1 touches no simulator code.
- **Host suite.** I ran only the history tests and the gate subset, not the
  full host suite.
- **Mutations.** The packet's mutation results were not reproduced.

## Residual risk not named in the packet

- **R1-1:** a multi-address mid-step window costs one full read per such step.
- **R1-3:** hung reads are not cancelled.
- **Missing upper bound.** The step-owned check has no upper bound, so a server
  bug that sends a future exposure would be accepted until the terminal full
  read replaces the history. This is stated in code, and it is acceptable.
