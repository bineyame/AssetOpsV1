# T025e phase 2 handoff: follow state (AC4-AC8), plus the AC1 exposures change

Branch `task/T025e-cockpit-organisation-and-live-playback`. Commits:
`88382e5` (step 0: exposures move to the append class), `4065a52` (scheduler
awaits the commit), `5fe352a` (one owner, live follow, one cursor, charts from
history). The layout is unchanged apart from where the cursor now sits.

## Step 0: exposures are append-class (owner approved 2026-09-30)

- `HISTORY_APPEND_FAMILY_KEYS` gains `"exposures": "from_offset"`
  (`backend/assetops_backend/simulator_lab_api.py:222`). The host prefix
  guard reads this same table, so it now covers exposures on both fixtures.
- On the client, `APPEND_FAMILY_KEYS` gains `exposures`, and it is removed
  from `WHOLE_FIELDS` (`frontend/src/shell/liveHistory.ts:35-75`).
- The backend fake now holds three exposures, and a test asserts the delta
  selects `e-2` and `e-3`. The merge test asserts that only the new exposures
  arrive. `kobo-mini-grid-history-deltas.json` was regenerated with
  `live_deltas()` only; the other fixtures written by `main()` were left as
  they were.
- The AC1 wording in the task and the A1 row-family list in the guidance each
  carry the one-line owner note.
- **Measured** (in process: capture, `history_delta_payload`, compact
  `json.dumps` with the envelope; the full read matches phase 1 at
  1,122,198 B):

| session | one-boundary delta max / median | was (phase 1) |
|---|---|---|
| mini-grid PROLONGED, 97 boundaries | **15,747 B / 13,402 B** | 71,935 / 42,972 |
| fuel with gap, 493 boundaries | **3,778 B / 2,548 B** | 11,654 / 7,999 |

  The worst mini-grid delta is at boundary 13: intervals 8,508 B, attempts
  2,280 B, coverage 1,536 B, samples 1,457 B, exposures 607 B. It is under the
  32 KB budget. The HTTP measurement is still phase 3's job.

## What landed (phase 2)

- **AC4 scheduler** (`runPlayback.ts`).
  - `PlaybackDeps.show` returns `void | Promise<void>`.
  - `handle` awaits `shown(...)`, then `afterShown`, which does the terminal,
    pause and next-delay decisions.
  - `shown` swallows rejections, so a history failure is never a step failure.
  - The late answer and the stop re-read go through `shown` too; the re-read
    awaits it before calling `onStopped`.
- **AC4-AC7 owner** (`runFrameState.ts`, new and pure).
  - `RunFrameState {execution, history: HeldHistory, fullReadDue, cursor}`.
  - Actions: `RESET`, `EXECUTION_READ`, `HISTORY_READ`, `TICK_COMMITTED`,
    `SELECT`, `RETURN_TO_LIVE`.
  - `historyRequest(state, answer)` decides the read:
    - a full read when nothing is held, at a terminal answer (unless the
      held history is already a full read covering it), or when
      `fullReadDue` is set;
    - nothing when the recorded count is at or past the clock;
    - otherwise a delta since the recorded count.
  - Selectors: `selectedOffset`, `boundariesBehindLive`, `historyLag`.
- **`RunFrame.tsx`**.
  - State lives in `useState` plus a `held` ref, and `dispatch` computes
    through the reducer. This lets an async commit decide from the latest
    state.
  - `commit(answer, base)` is chained on `commits.current`, so there is one
    history request at a time and never two in parallel. It dispatches one
    `TICK_COMMITTED`.
  - The scheduler's `show`, the manual controls and Run to the end all use
    `commit`.
  - Start passes `base=true`: one whole read as the live session's base,
    before the first step.
  - `rereadRecords` is gone. The stage is re-read after a control and on
    stop; the history is not.
- **AC7 cursor**.
  - `HistoryCursor` in `HistoryInspector.tsx` holds `#history-cursor-range`,
    labelled "History cursor", with `data-history-cursor=live|pinned`.
  - It has two reserved slots: `data-return-to-live-slot`, which shows
    "Return to live (n boundaries behind live)" or "Following live", and
    `data-history-lag`, which shows "History recorded through boundary k;
    execution at n.".
  - The CSS for the slots is in `ui/primitives.css`, after `.history-cursor`.
  - Other ways to move the cursor:
    - SLD arrow keys, Home and End, on a Lab-side wrapper in
      `IntervalDrawing.tsx`; `ConfiguredSingleLineDrawing` is untouched;
    - timeline "When" buttons (`data-timeline-go`) in `HistoryTimeline.tsx`;
    - chart clicks, as before.
  - The raw records' `<select data-history-boundary-select>` is removed. Its
    text now reads "interval decided at T".
- **AC8 charts**.
  - `chartModel(history, timestepMinutes)`: the `steps` parameter is gone,
    which closes C3.
  - PV is plotted as five recorded flows: potential, to loads, to battery,
    curtailed and clipped.
  - The battery is plotted as `battery_to_load`, `pv_to_battery` and
    `generator_to_battery` when present.
  - `ChartPanel.bound`: SOC is 0-100, and generator output runs from 0 to the
    held `generator-rated-power`.
  - `valueTicks(panel, values)` in `HistoryCharts.tsx`: a declared bound when
    there is one, otherwise a nice ratchet with 1.25 headroom. It is monotone
    because the live history only grows.

## Checks (this phase)

- Frontend `src/shell`: **28 files, 629 passed**. `tsc --noEmit` is clean.
- New and changed tests:
  - `runFrameState.test.ts` (12 tests, against backend deltas);
  - `runPlayback.test.ts` (+3);
  - `runPlaybackScreen.test.tsx` (+3 live-follow screen tests; the old
    history-on-stop test is rewritten to deltas plus one terminal read);
  - `historyCharts.test.tsx` (flow-per-curve, declared bounds, ratchet
    widening at most 3 per panel, never lowers);
  - inspector and interval tests now drive the one cursor.
- Host: prefix, lab_history, cockpit_window and contract9_gate: **87 passed**.
- Backend: delta, history, gate and execution API: **85 passed**.
- `check-architecture.ps1` and `check-agent-workflow.ps1` passed.
- Mutation proofs. Each was committed first, then reverted with
  `git checkout`:
  - scheduler not awaiting `show`: 2 failed;
  - no `fullReadDue` after a failed delta: 1 reducer and 1 screen test failed;
  - the terminal full read resetting the cursor to live: 1 failed;
  - bound ignored: 1 failed;
  - PV series fed from the wrong flow: 1 failed;
  - backend exposures keyed on `to_offset`: host 4 failed, backend 2 failed.

## Deviations

1. **PV and battery series changed shape** to satisfy "charts from history
   only" without recomputing.
   - The old "Accepted" PV curve and the signed battery-power curve were the
     host's *sums* of flows (`lab_execution.py:780-791`).
   - The history records only the component flows, so each is now its own
     curve.
   - This needs the owner's eye (presentation, not semantics).
2. **Start makes one whole read.** It is the session's base, needed because
   the pre-start history is `NOT_RECORDED` with a different identity. It is
   before the first step, so AC6's "none between first step and terminal"
   holds.
3. **The lag statement shows whenever recorded < clock**, which includes on
   load for a run whose history is `NOT_RECORDED`. It is a derived fact, not a
   stored `behind` flag.
4. The two phase-2 frontend commits are coupled: `HistoryCharts` lost the
   range and `steps` in the same change as the lifted cursor.

## For phase 3

- The cursor strip sits between "Recorded coverage" and the charts; move it
  into the cockpit (AC9). The `data-*` hooks above must survive.
- Not done yet: AC11 memoisation. The chart model rebuilds per commit; the
  SLD, inspection and records are not memoised on the slice. `frame.slices`
  is held in `HeldHistory.frame`, ready for it.
- `onState` still renders twice per tick (in-flight true and false: F4 and
  F5).
- Charts and cursor render only after the first recorded boundary, so the
  first tick after Start adds them. Reserve space for them.
- Layout evidence (AC12): the delta sizes above are in process. Take HTTP
  bytes and the p95 at the demo window's last boundary.

## Open risks

- If another tab steps the run, a delta can carry more boundaries than the
  local answer's clock, so recorded > clock until the next answer. It is not
  clipped (that would be patching); the lag statement stays hidden.
- The terminal decision uses `held.full && recorded >= clock`. A terminal
  answer arriving after a failed terminal read re-reads once per answer,
  which is bounded by the answers.
- The screen-test fake host builds a synthetic live history (no intervals).
  The merge against real deltas is covered by the reducer tests and
  `liveHistory.test.ts`.
