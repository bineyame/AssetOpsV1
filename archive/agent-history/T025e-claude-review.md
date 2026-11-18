# T025e discovery review: Lab cockpit organisation and live playback

Reviewer: **Claude** (fresh `assetops-reviewer` instance, not the implementer),
produced under the temporary binding in `.ai/ROLE_CONFIG.md` (Reviewer is Claude
until the Codex reset at 2026-10-03 21:23). This is the **first review of a new
mechanism and wire addition**. It would normally go to Codex, so a later reader
should weigh it as a Claude discovery review and may send it back to Codex.

Scope: the whole slice, all three phases, `git diff main...HEAD` on
`task/T025e-cockpit-organisation-and-live-playback` at `b0b5944`. Judged
against AC1-AC12, the review packet, the Architect guidance (items, Addendum A,
Addendum B option R), and `D-2026-09-30-t025e-live-follow`.

## Verdict: REJECT (narrow). Fix finding 1 on the branch, then re-review.

Most of the slice is sound. That includes the scheduler, the one-owner state,
the commit chain, the cockpit organisation, the protected seams and option R.
But the core claim of the new mechanism does not hold for a legal input. That
claim is that every append family grows only at its end, so a client can fold
deltas. `exposures` is keyed on a field that is not its recording boundary.

For a forcing window that opens mid-step, the live client does one of two
things:

- It silently appends a duplicate row, which the Applied timeline shows twice.
- Or it refuses the merge and makes a full read in the middle of play.

The prefix guard is correct, but its fixtures never exercise this case. The
owner approved moving exposures to the append class on the basis that "the
prefix guard proves it append-only". So this is not a carry: it changes what
the owner approved.

Findings 2-9 can be carried, and finding 2 is cheap enough to fix in the same
pass.

## Findings

### 1. HIGH - `exposures` is not prefix-stable when a forcing window opens mid-step (acceptance gap: AC1, AC2, AC3, AC6)

**Where.**
- `backend/assetops_backend/simulator_lab_api.py:234` (`"exposures": "from_offset"`)
  and `:1450` (the `> after` selection).
- `frontend/src/shell/liveHistory.ts:45`, with its checks at `:228` and `:234`.
- The source of the mismatch: `simulator/assetops_simulator/kernel/execute.py:1292-1293`.
  There, `exposed_from = max(world.offset, start)`, and the exposure goes on the
  boundary that *begins* the step (`contracts/assetops_contracts/trajectory.py:211`:
  "the exposure's own half-open span inside the step").

**What is wrong.** An exposure is recorded at the boundary t_k that begins its
step. Its `from_offset` is the window start, which can lie strictly inside
(t_k, t_{k+1}). The execution contract's `window-active-span` rule explicitly
allows a window that meets or opens inside a step.

So at capture k the history holds a row whose key is after
`recorded_through_offset`. That is exactly what the prefix property forbids.

**Reproduced.** I copied the fuel gate run
(`host/tests/contract9_gate/runs/run-c9000000000000000000000000000102.yaml`)
and changed `generator-run-window` from `offset_minutes: 1080` to `1082`. The
run is still `READY`. I then drove `live_captures` from
`host/tests/test_lab_history_prefix.py`. The probe script was in scratch and
was not committed.

- **The prefix property fails.** Capture 217 is recorded through 1080 and holds
  the exposure `generator-run-window [1082, 1085)`.
- **The row is sent twice.** Take a full read at capture 217, then the route's
  `since_boundary` delta from its count. The delta re-sends that exposure,
  because 1082 > 1080.
- **The fold does not equal the full read.** Folding every delta over the
  first full read gives 50 exposures; the full read at the end has 49. So
  `test_folding_every_delta_reproduces_the_full_read` would fail on this input.
- **Only exposures fails.** The same probe with a cause window at 1502, a
  reporting gap at 1492, a refuel point at 2402 and an irradiance window at 722
  shows no violation in any other family. Intervals and `electrical_steps` are
  keyed on the deciding boundary, so `from_offset` is always a boundary offset
  for them.

**Why it matters.** There are two client outcomes.

- **Duplicate path, silent.** The base is a full read at k. That covers the
  load of a running run, Start's base read, and the fallback full read after
  any refusal. If boundary k's step has a mid-step window start, the next delta
  carries the row again. `appendHistory` accepts it: the key is > after and
  <= through, and it is in order. Nothing checks non-boundary families for
  duplicates. The held history then carries the exposure twice, and
  `historyTimelineModel.ts:133` draws it twice in the Applied timeline. It
  stays that way until the terminal full read.
- **Refusal path.** During auto-play, the delta that ends at boundary k carries
  the row with a key > through, so the merge refuses it with
  `ROW_AHEAD_OF_RECORDED`. The next tick then makes a full read in the middle
  of play. That breaks AC6 ("none between first step and terminal") and the
  32 KB budget for that tick. It is honest, but it is not what the packet
  measured.

**Why the guard missed it.** Every fixture window is aligned to a 5-minute
boundary. The guard's own logic
(`test_lab_history_prefix.py:95-98`) would catch this case given a fixture that
had it.

**Fix (needs an Architect/owner call, since it reopens the phase-2 approval).**
Choose one of the following.

- **(a) Select exposures by the step they belong to.**
  - The server keeps a row when `from_offset >= boundaries[since].offset_minutes`,
    that is, half-open ownership of the step. This selects on recorded values
    and computes nothing.
  - The client's range check for this family becomes "at or after the first
    new boundary's offset, and before the end of the last new boundary's step".
  - This needs a per-family ownership rule in both tables, not one time key.
- **(b) Return exposures to the sent-whole class.** This is AC2's own
  prescribed remedy. It reopens the 71,935 B budget miss, which then goes to
  the owner.

Whichever is chosen, add a fixture with a mid-step window (the 1082 edit above
is enough) to `test_lab_history_prefix.py`, the fold test and the client's
`kobo-mini-grid-history-deltas.json` family. Then the guard covers the case it
is cited for.

### 2. MEDIUM - A history read that hangs stalls auto-play, and a pause never resolves (AC4, AC5)

**Where.**
- `frontend/src/shell/runHistory.ts:424` and `:473`: a plain `fetch` with no
  timeout.
- `frontend/src/shell/RunFrame.tsx`, in `commit`, which awaits the read inside
  the commit chain.
- `frontend/src/shell/runPlayback.ts:261`: `handle` arms nothing until `shown`
  settles.

**What is wrong.** The step has a timeout (`stepTimeoutMs`); the history read
after it has none.

- **Play halts silently.** A read that never settles leaves the scheduler at
  `playing` with nothing in flight and no next delay armed. No refusal, lag
  line or reason is shown.
- **Pause stays pending.** A Pause asked for then stays at `pausing` forever,
  because it resolves only after the commit.
- **Later commits queue.** Every later commit, including a manual control's,
  queues behind it on `commits.current`.

AC4 and AC5 say a history failure never stops play. A hang is the one failure
mode the code does not turn into a failure. The per-run host lock makes a long
wait plausible when another request holds it, for example a large Run to the
end from another tab.

**Fix.** Bound the history read with an `AbortController`, using the step
timeout or a named history timeout. On expiry, commit it as
`{status: "unavailable"}`. The existing lag and full-read-next path then
handles it. Add one scheduler/screen test in which a delta never settles.

### 3. LOW-MEDIUM - Recorded can exceed the clock, and the packet dropped the risk (AC5 claimed Met)

**Where.** `frontend/src/shell/runFrameState.ts:124-127` (`recorded >= clock`
leads to `none`) and `:254-270` (`historyLag` only states `recorded < clock`).
The phase-2 handoff names this under "Open risks". `.agent/T025e-review-packet.md`
omits it from its residual risk and marks AC5 "Met".

**What is wrong.** Suppose another tab steps the run between this tab's step
answer and its delta read. The delta's `through_boundary` is then above this
tab's clock, and the merge accepts it (correctly: it is not a patch).

- The live cursor, the drawing and the inspection show a boundary past the
  execution clock, and no statement explains it.
- **Under auto-play,** the next guarded step is refused and the re-read
  realigns.
- **After a manual Step,** it persists until the next control or a reload.

AC5's "cursor <= recorded <= clock" does not hold in that window.

**Fix (carry).** When a committed delta records more than the answer's clock,
make one execution read, or state it: "History recorded through k; execution
clock at n; another control advanced this run". Add a reducer or screen test.
The packet must list it as residual risk.

### 4. LOW - Load reads sit outside the commit chain and can regress a newer commit

**Where.**
- `frontend/src/shell/RunFrame.tsx:342`: the load `getExecutionHistory`
  dispatches `HISTORY_READ` directly.
- `frontend/src/shell/runFrameState.ts:130-149`: `wholeRead` replaces the held
  history unconditionally.
- `runFrameState.ts:183-184`: `EXECUTION_READ` replaces the execution without
  `laterExecution`.

**What is wrong.** A control that commits before the load reads land can be
overwritten by the older load snapshot. That regresses recorded, and possibly
the clock too.

It heals at the next tick. After a manual Start, though, it shows a false lag
line until the next action. It is also a second history request in parallel
with a commit's, which the "never parallel" wording rules out.

**Fix (carry).** Route the load reads through `commits`, or ignore a whole read
whose `boundaries_recorded` is below the held one, and apply `laterExecution`
to `EXECUTION_READ`.

### 5. LOW - The lag line reads as "behind" for a history that will never catch up (Deviation 5)

**Where.** `frontend/src/shell/HistoryInspector.tsx:427-433` and
`runFrameState.ts:254`.

**What is wrong.** Take a terminal run whose history is `NOT_RECORDED`,
`LEGACY_ARTIFACT` or `WRITE_FAILED`. It shows "History recorded through
boundary 0; execution at N." with `data-history-lag="behind"`. The sentence is
true, but the attribute and its placement next to live follow imply catching
up. The source statement elsewhere says why nothing is recorded.

**Fix (carry, or owner accepts).** Show the lag statement only while the held
history is not a full read of a terminal run. Otherwise defer to the source
statement.

### 6. LOW - Evidence: name what the two timing budgets cover, and the server's scaling

**Where.** `frontend/src/shell/RunFrame.tsx:90-111` and `tools/layout-evidence.mjs`
(the T025e budgets section).

**Tick commit.** "Tick commit" is measured from the `TICK_COMMITTED` dispatch to
the next layout effect. That is React scheduling plus render plus commit. It
does not cover the step, the history fetch, or the browser's style, layout and
paint. It is a fair reading of AC12, but the packet should say so.

**Server p95.** The 45.9 ms is measured at the stated boundary: a one-boundary
delta at recorded 96 of 97. It is wall time through the `vite preview` proxy,
so it is conservative about the proxy. But it comes from 40 sequential
re-reads while paused, not under a concurrent step.

**Residual risk the packet under-states.** Every delta read does a full
`capture` (`generate_observations` over all boundaries). So server delta cost
grows with the length of the window. The packet names the 8 % margin, not this
scaling. A longer window, for example 288 boundaries, would likely miss the
budget.

**Carry.** Take the named stop (memoise capture per session and boundary
count) before a longer demo window.

### 7. LOW - Evidence gaps in the pinned and empty-frame claims

**Where.** `tools/layout-evidence.mjs`, `T025E_OBSERVE_PINNED` and `T025E_SAMPLER`.

**Pinned geometry is not measured.** The pinned pass counts mutations only. It
samples no geometry when pinning makes "Return to live" appear, so AC7's
"reserved slot, nothing moves" is proved only by jsdom structure, not in the
browser.

**The empty-frame check is weak.** It counts non-empty series paths
page-wide. One panel that goes blank while others draw would not register.

**Carry.** Sample the cockpit and cursor boxes across the pin and return
transitions. Count empty panels per panel.

### 8. LOW - The Lab gate never iterates the new cursor controls

**Where.** `frontend/src/shell/__tests__/simulatorLabGate.test.tsx`: the fake
client renders no recorded history.

**What is wrong.** "Offers exactly the named execution controls on the run
surface" is vacuous over the reader controls phase 2 added. Those are the
timeline "at T min" buttons, the SLD arrows, Return to live and chart clicks.
The layout evidence exempts them by label instead.

**The disclosure allowance itself is scoped correctly.** It applies only on
run-surface URLs, and only to `details[data-disclosure]` or its own `summary`.
Controls inside a disclosure are still iterated one by one, so it opens no
hole. The one nuance is that the allowance is by attribute, not by the
primitive.

**Carry.** Give the gate test a recorded-history fixture and a named allowance
for cursor movers (reads that execute nothing), so the ban covers them.

### 9. INFO - Performance entries accumulate

`run-frame-commit` marks and measures (`RunFrame.tsx:90-111`) are never cleared
in production. At about 2 entries per tick this is negligible for a 97-boundary
run, but it is unbounded. Clear the mark after measuring, or cap it.

## Deviations (packet list) - judgement

| # | Deviation | Judgement |
|---|---|---|
| 1 | Append families keyed on `from_offset`, not `to_offset` | **Accept for intervals and `electrical_steps`** (always the deciding boundary's offset). **Not for exposures**: see finding 1. Neither `from_offset` nor `to_offset` is its recording boundary. |
| 2 | Merge stricter than A2 (`NOT_A_DELTA`, `ROW_AHEAD_OF_RECORDED`) | Accept. `ROW_AHEAD` is what turns finding 1 into a full read on the auto-play path rather than corruption. |
| 3 | Component curves in phase 2 | Accept. Superseded by option R: the totals are read verbatim (`fromStep`), and the components are marked `data-series-role="detail"`. |
| 4 | Start makes one whole read | Accept. It happens before the first step, so "none between first step and terminal" holds. |
| 5 | Lag line on load for `NOT_RECORDED` | Accept, with finding 5 as a carry. |
| 6 | New cursor movers | Accept. Finding 8 is a carry for gate coverage. |
| 7 | Day curves start at 1057 px, below 800 | Owner call, as the packet says. AC9's first viewport otherwise holds (strip at 108 px, stage at 448 px, cursor at 992 px). |
| 8 | The charts region grows once at the first recorded interval | Accept. The cockpit top, drawing row and cursor do not move, as the evidence shows. The cockpit *height* does change once, and the evidence claim "does not move the cockpit" checks only the top. It is stated, not hidden. |
| 9 | Status announced once per play, not per tick | Accept. It reduces screen-reader chatter. It is a departure from AC11's "announced once per tick" wording, and the owner should be told. |
| 10 | A message slot below the controls; facts moved to provenance | Accept. The hooks are unchanged (checked). |
| 11 | Gate allowance for `details[data-disclosure]` | Accept (see finding 8). |
| 12 | `run-frame-commit` instrumentation in production | Accept. It costs one `performance.mark` and one `measure` per tick, and it cannot throw (guarded). Finding 9 applies. |

## Verified clean (claims checked, not adopted)

**Protected seams.**
- `ConfiguredSingleLineDrawing` (`frontend/src/sites/SiteSingleLineDiagram.tsx`)
  is not in the diff. Memo and layout are Lab-side.
- `host/tests/contract9_gate/` is not in the diff and passes (23).
- `EXECUTION_CONTRACT_VERSION = 9` and `LAB_HISTORY_SCHEMA_VERSION = 2` are
  unchanged.
- `render_history` is unchanged: `electrical_steps` is joined and never
  persisted, and `projection_binding` already covers it. This matches B3.
- The contract dataclass gains a defaulted field, as B2 prescribes.

**Charts.**
- Charts read `pv_output` and `battery_power` verbatim from `electrical_steps`,
  matched by `from_offset`.
- Components come from the recorded flows. There is no client arithmetic on any
  quantity; the y-ratchet computes axis ticks only.
- No per-step execution data reaches a chart, which closes C3.

**Server.**
- The history read holds the per-run host lock (`host/lab_execution.py:2195`),
  so a delta cannot capture a half-advanced session.
- `since_boundary` parsing: a non-integer or negative value gets a 422, and a
  value ahead of what is recorded gets a 409 `HISTORY_SINCE_AHEAD`. Without
  the parameter the read is unchanged, apart from Addendum B's
  `electrical_steps`, which the owner chose.

**Merge.**
- Identity, `since`, not-a-delta, gap, duplicate-boundary, order and
  ahead-of-recorded refusals are all present and tested.
- The result is a new object; static families and old rows are kept by
  reference.
- A terminal full read replaces the accumulated history; the reducer test
  compares it family by family.

**Scheduler and state.**
- `show` is awaited before the delay is armed or a pause resolves.
- A late answer reconciles once (`recorded >= clock` leads to `none`).
- The `commits` promise chain serialises every committed read, so there are no
  parallel or catch-up requests from ticks. Finding 4 is the exception outside
  the chain.
- A failed delta leads to one full read next. A failed full read keeps the
  last frame and retries a delta from k.
- The four states have one owner each.

**Truth labels and reachability.**
- "an accounting value, not a wire" (`intervalDrawingModel.ts:352`) and the
  reporting-gap-not-outage line (`HistoryTimeline.tsx:73`) are untouched.
- "What this run is not" is one visible line plus a disclosure.
- The stage inspector is reachable in the `stage` disclosure.
- Controller and resolver commitments and the "against simulation time" tables
  are inside `latest-step`.
- The removed `data-*` hooks and heading ids either survive or were removed on
  purpose. The one removed on purpose is `data-history-boundary-select`, AC7's
  retired `<select>`, and tests assert its absence.

## Checks I ran

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| host `pytest tests/test_lab_history_prefix.py tests/test_lab_history.py` | 57 passed |
| host `pytest tests/contract9_gate` | 23 passed |
| backend `pytest backend/tests/test_run_history_delta_api.py` | 19 passed |
| frontend `npx.cmd tsc --noEmit` | clean (exit 0) |
| frontend `npm.cmd test` | 38 files, 984 passed. It ran in this session; the esbuild sandbox denial the standing brief warns about did not occur here. |
| frontend `npm.cmd run build` | built, 438.46 kB JS |
| Scratch probe (finding 1): fuel gate run with the window at 1082 | prefix violation at capture 217; delta re-sends the row; fold 50 vs full 49 |
| Scratch probe: cause, gap, refuel and irradiance offsets moved off-grid | no violation in any other family |

**Not verified by me.**
- The full host (495), backend (1316) and simulator (227) suites; I ran
  targeted subsets only.
- `tools/layout-evidence.mjs`, which needs Chrome, the backend and a dev
  server. I read the script and `.agent/T025e-layout-evidence.txt`: the claims
  measure what they say, subject to findings 6 and 7. The packet records the
  run honestly, including the first run's 11 failures.

## Carries proposed for the milestone backlog

These apply once finding 1 is fixed.

- **C-T025e-1 (finding 2).** Bound the history read with a timeout and commit
  expiry as unavailable. Preferably fix it in the finding 1 pass.
- **C-T025e-2 (finding 3).** Handle recorded > clock (another tab), and name it
  in the packet.
- **C-T025e-3 (finding 4).** Put the load reads inside the commit chain, or make
  them monotone.
- **C-T025e-4 (finding 5).** Lag statement only for a live lag, not an
  unrecorded terminal history.
- **C-T025e-5 (finding 6).** Memoise capture per session and boundary count
  before any longer demo window. State what the commit timing covers.
- **C-T025e-6 (finding 7).** Browser geometry across pin and return; count empty
  frames per panel.
- **C-T025e-7 (finding 8).** A Lab gate test with a recorded history and a named
  allowance for cursor movers.
