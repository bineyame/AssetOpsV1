# T025e Architect guidance: cockpit organisation and playback flicker

Architect pass, 2026-09-30, advisory and read-only. **Produced by Claude**
(`assetops-architect`) under the temporary binding in `.ai/ROLE_CONFIG.md`
(`D-2026-09-30-architect-reviewer-claude-until-reset`), because Codex was at its
usage limit. Evidence is code reading only: the app was not run and suites were
not re-run.

Trigger: the owner's hands-on check of T025d found it functionally OK, but
"a lot of content that is poorly organised ... it really looks disorganised and
too low a bar", and "a lot of flickering as the simulation is happening".

Owner decision, 2026-09-30: T025d closes as accepted; the fixes go into a
dedicated slice **T025e** before T026. Live follow during play (item 11) is
**in** T025e: the owner decided on 2026-09-30 (`D-2026-09-30-t025e-live-follow`)
that the cockpit stays current during playback with no flicker. See the addendum.

## 1. Layout and information organisation

### Inventory

`frontend/src/shell/RunFrame.tsx` renders one column of about 40 panels:

1. Run facts: `RunHeader` (`RunHeader.tsx:53`), "This run" (`RunFrame.tsx:332`),
   "What ready does not assert", "The frozen inputs" (`:360`), and the
   conditional draft/optional-input panels.
2. "Executing this run" (`:437`): about 17 execution facts (`:482-535`); Start,
   boundaries input, Step, Run to the end (`:560-635`); Auto-play with a long
   paragraph, delay picker, Play/Pause and status (`:1257-1326`).
3. Live latest step (execution clock): "What the world holds" (`:673`);
   `ElectricalPanels` x7 (`ElectricalPanels.tsx:84-409`); `GeneratorPanels` x4
   (`GeneratorPanels.tsx:53-202`); device reports, reporting paths, declared
   gaps and newest sample attempts (`RunFrame.tsx:706-864`).
4. Recorded history (history cursor), `HistoryInspector.tsx`: history and
   coverage; day curves with range cursor and sticky "Exact values"; the SLD at
   the selected boundary; `IntervalInspection` x4 (`IntervalInspection.tsx:29-178`);
   Applied timeline; the T025c `BoundaryRecords` with a second selector
   (`HistoryInspector.tsx:263-467`).
5. Stage and claims: staged envelopes, allowlist, selected envelope, every
   envelope; "What this run is not".

### Why it reads as disorganised

- The headline T025d feature (SLD plus interval inspection) sits below about 20
  panels; Play is far above the drawing it animates.
- Facts repeat up to three times on two clocks under near-identical headings:
  controls (`ElectricalPanels.tsx:159`, `IntervalInspection.tsx:29/46`,
  `HistoryInspector.tsx:378`); load service (`ElectricalPanels.tsx:209`,
  `IntervalInspection.tsx:145`, `HistoryInspector.tsx:354`); flows
  (`ElectricalPanels.tsx:248`, `HistoryInspector.tsx:368`, SLD labels); private
  state (`RunFrame.tsx:673`, `HistoryInspector.tsx:294`); reports
  (`RunFrame.tsx:706/864`, `HistoryInspector.tsx:401`, chart rings); three
  timelines; "against simulation time" tables duplicating the day curves;
  `RunHeader` duplicating "This run" and execution facts; the trajectory digest
  twice.
- Three selectors with two conventions: range input and SLD arrow keys select
  the interval *ending* at T; the T025c `<select>` selects the interval
  *decided* at T (`HistoryInspector.tsx:269`, `:236`).
- No hierarchy: every panel has equal weight, nothing is collapsed, provenance
  sits beside live values.
- Heavy prose: most panels open with 2-5 sentences of claim boundary (e.g.
  `RunFrame.tsx:1281`, `HistoryCharts.tsx:866-873`).

### Minimum bar (a floor, not a design system)

- **Primary, in the first viewport at 1280 px:**
  - a compact control strip: execution status badge; execution clock
    (simulated time, "boundary n of N"); Start, Step with input, Run to the end;
    Play/Pause with delay; one-line playback status. Long explanations move to
    a "How playback works" disclosure;
  - the cockpit directly under it: SLD beside the selected-interval inspection
    (requested/accepted, `limited_by`, per-load service, one-line balance
    verdict with the table expandable); one shared history cursor labelled
    "History cursor", visibly separate from the execution clock (AC7); day
    curves; Applied timeline.
- **Secondary, visible below:** Applied timeline if it does not fit; "Exact
  values" (may stay sticky); "What this run is not" as one visible line.
- **On demand, closed `<details>`:** run identity and frozen inputs (merge
  `RunHeader` with "This run"); execution provenance; latest step on the
  execution clock (live electrical, generator and observation panels);
  time-series tables (kept as the charts' accessible alternative); raw records
  at one boundary (T025c `BoundaryRecords`, own `<select>` removed, following
  the shared cursor and labelled "interval decided at T"); coverage/history
  metadata; reporting paths and declared gaps; stage and envelopes (reachable,
  AC7); controller/resolver commitments.
- **Remove:** the second boundary `<select>`; duplicate digest/fact rows.
- **Prose:** captions of one line or less beside values. Truth labels stay in
  place: zero / absent / unmodeled; stock-at-instant vs flow-over-interval;
  accounting PV is not a wire; a reporting gap is not an outage.
- **Test hooks:** keep every `data-*` attribute and heading id.
  `tools/layout-evidence.mjs` must open disclosures before measuring, since a
  closed `<details>` measures as zero.

## 2. Flicker root causes

No CSS transitions or animations exist in `src/ui/*.css`. The flicker is
layout movement and uneven per-tick updates.

- **F1 - growing tables above the cockpit shift it every tick (confirmed,
  main cause).** "Against simulation time" (`ElectricalPanels.tsx:362`) and the
  generator equivalent (`GeneratorPanels.tsx:150`) add a row per step and render
  at `RunFrame.tsx:701`, above `HistoryInspector` (`RunFrame.tsx:910`). Newest
  sample attempts (`RunFrame.tsx:864`, host cap `host/lab_execution.py:726`) and
  device reports also change size per step.
- **F2 - the cockpit freezes during play, then jumps on stop (confirmed).**
  History is re-read only on stop (`RunFrame.tsx:123-132`, `onStopped` at
  `:147`), a disclosed cost choice (history read 1,152,446 B, packet line 153).
  On pause the SLD, inspection, timeline and cursor jump together; the cursor
  snaps to the last boundary via `HistoryInspector.tsx:110-114`. Falls short of
  "Live follow follows the last available record"
  (`.ai/PLANNING_HANDOFF_LAB_COCKPIT.md:178`).
- **F3 - charts mix fresh and cached data (backlog carry C3, confirmed).**
  `RunFrame.tsx:912` passes per-step `projection.electrical.steps` into charts
  built on cached history (`HistoryCharts.tsx:842-845`,
  `historyChartModel.ts:211-223`, `:323-332`). PV/battery curves grow per tick
  into the "not recorded" region (`HistoryCharts.tsx:225`); y-axes auto-rescale
  on new maxima (`HistoryCharts.tsx:388-390`).
- **F4 - three full-page reconciliations per tick (confirmed as cost,
  suspected as jank at 0.25 s).** `setExecution` (`RunFrame.tsx:145`), `onState`
  in-flight true (`runPlayback.ts:203`) and false (`runPlayback.ts:251`). Nothing
  memoised; `LoadedHistory`, `IntervalDrawing` (`IntervalDrawing.tsx:27,42`) and
  the SLD re-render with unchanged inputs. Re-render, not remount.
- **F5 - status sentence alternates twice per tick (confirmed, minor).**
  `RunFrame.tsx:1231-1234` inside `role="status"` (`:1307`); different lengths
  re-wrap and screen readers announce twice.
- **F6 - variable-width values in auto-layout tables (suspected).** `.data-table`
  lacks `table-layout: fixed` (`primitives.css:539`); exact rationals change
  length and columns resize.

Ruled out: key-change remounts; loading placeholders (state never reset to
null, `RunFrame.tsx:126-132, 145`); `innerHTML`; CSS transitions; scheduler
recreated per render (created once per run, `RunFrame.tsx:137-168`; delay via a
separate effect `:170-173`); chart `ResizeObserver` (`HistoryCharts.tsx:57-75`);
SLD remount.

## 3. Sequencing

T025e, after T025d and before T026. Frontend plus one backend wire addition
(a `since_boundary` query on the existing history read; see the addendum). No
host, contract or persisted-schema change. Not inside T025d (would
reopen an accepted review across every panel and test hook). Not inside T026
(T026 adds panels to this page; C3's trigger is T026 touching the refresh
path). Fits `D-2026-09-22-milestone-speed-over-purity`.

Protected seams and decisions:

- Shared SLD takes neutral slots and imports no Lab/simulator/gate/shell type
  (T025d AC1, `.ai/ARCHITECTURE.md:329-338`). Memoisation and layout stay
  Lab-side; do not change `ConfiguredSingleLineDrawing`.
- History cursor, execution clock, playback state and stage status stay
  distinct (AC7). Playback state stays owned by `PlaybackScheduler`.
- History is a host-owned gated projection; charts read, never recompute
  (`D-2026-09-30-lab-cockpit-history`).
- Timing and missingness labels required by
  `D-2026-09-30-lab-cockpit-presentation` survive the prose trim.
- ~~Refresh policy (history on stop) is kept.~~ **Superseded** by
  `D-2026-09-30-t025e-live-follow`: the cockpit follows the run during play.
  The mechanism is set in the addendum.
- Stage inspector stays reachable (AC7): collapse, do not remove.

## Prioritised changes for the Planner

1. Stop the layout shift: move the latest-step block (electrical, generator,
   observation panels, both "against simulation time" tables) below the cockpit
   into a closed "Latest step (execution clock)" disclosure. Nothing that grows
   per tick sits above the SLD or charts. (F1)
2. **(Revised by the addendum.)** Close carry C3: charts are built from the
   accumulated history only. `projection.electrical.steps` stops reaching the
   charts (`RunFrame.tsx:912`), so fresh and cached data can no longer mix.
   (F3; addendum A2)
3. **(Revised by the addendum.)** Fixed chart geometry. The x-domain is the
   whole run window from the manifest, fixed from the first frame. The y-domain
   comes from a declared bound where the frozen inputs have one; otherwise it is
   a monotone "nice" ratchet that never shrinks. (F3; addendum A4)
4. **(Superseded by the addendum.)** ~~Frozen-cockpit marker, "refreshes on
   pause".~~ The cockpit no longer freezes. Instead there is a history cursor
   in `live` or `pinned` mode, with a "Return to live" affordance, and pause
   does not move it. (F2; addendum A3)
5. Build the primary layout: control strip, SLD beside interval inspection, one
   shared cursor, day curves, Applied timeline; label the SLD's selected boundary
   so history cursor and execution clock are distinct.
6. Remove duplication: merge `RunHeader` and "This run"; drop the second
   `<select>` and let T025c records follow the shared cursor ("interval decided
   at T"); collapse provenance, coverage, reporting paths/gaps, commitments and
   stage into closed `<details>`; keep "What this run is not" as one visible line.
7. Trim prose to one-line captions; long explanations into "How to read this"
   disclosures; truth labels stay beside values.
8. Cut render cost: memoise the Lab-side `HistoryInspector`/`IntervalDrawing`
   subtree on the per-boundary slice reference, not on the whole `history`
   (see addendum A2 on structural sharing); one stable "playing" status sentence
   with in-flight as an attribute. (F4, F5)
9. Tabular figures and fixed or min-width numeric columns in data tables. (F6)
10. Update `tools/layout-evidence.mjs`: open disclosures before measuring; keep
    all `data-*` hooks and heading ids; add a check that the cockpit panel's top
    edge does not move between steps during auto-play. The addendum's A6
    extends this list.
11. **In scope (owner, `D-2026-09-30-t025e-live-follow`).** Live follow during
    play through an append-only history read. The mechanism is in the addendum
    below, and it replaces the read-history-on-stop policy
    (`RunFrame.tsx:123-132, 147`).

---

## Addendum: live follow mechanism

Architect pass, 2026-09-30, advisory. **Produced by Claude** (`assetops-architect`)
under the temporary binding in `.ai/ROLE_CONFIG.md` (Architect is Claude until
the Codex reset on 2026-10-03 21:23). Evidence comes from reading
`host/lab_execution.py` (`step` :2083, `_history_document` :2163, `history`
:2186), `host/lab_history.py` (`capture` :125, digest :481-503), the backend
route (`simulator_lab_api.py:208, 1099, 2207`), `runHistory.ts`, `runPlayback.ts`
and `RunFrame.tsx`. The app was not run.

Trigger: `D-2026-09-30-t025e-live-follow`. The owner asked for the cockpit to be
current during playback, with high-quality state updates and no flicker. That
brings item 11 into scope and supersedes items 2-4 and the "history on stop"
seam above.

### Facts the choice rests on

- A live session's history is recomputed whole on every read: `_captured` at
  `lab_execution.py:2150` runs `capture` and `generate_observations` over all
  boundaries. It is served with `source: LIVE_SESSION` and **`history_digest:
  null`** (`lab_history.py:235`). The digest and `projection_binding` (history
  schema 2) exist only on the persisted terminal artifact. They are verified on
  read-back (`read_history` :1813) and are never computed for a running run.
- A RUNNING artifact carries no history (`_history_document` :2169). So during
  play the only history source is the live capture, and it has no integrity
  digest to preserve or break.
- The step already costs O(n) server-side: `_stage` republishes the whole series
  every step. So a history read that is O(n) server-side does not change the
  asymptotic cost per tick. What does hurt is wire and client parse: 1,152,446 B
  per full read.
- The route split is deliberate (`simulator_lab_api.py:205-207`): "a step
  response carrying it would ship the whole run again at every boundary."
  Auto-play's step is byte-for-byte the manual Step (`runPlayback.ts:6-11`).

### A1. Data path: an append-only read on the existing route

**Decision: an incremental read.** Use
`GET /runs/{id}/execution/history?since_boundary=n`. It returns the same
`history` document shape, with the time-keyed row families filtered to records
after boundary `n`.

Rejected alternatives:

- **Step response carries the new boundary's records.** This couples the
  execution payload (contract 9's projection) to the history projection, and
  it merges the execution clock with the history cursor on the wire (AC7). It
  also changes what a manual Step answers, and it contradicts the recorded
  reason for the route split. Rejected.
- **Throttled full re-read.** 1.15 MB, parsed and diffed on the client, at up
  to 4 Hz. That is about 4.6 MB/s, and parsing alone breaks the render budget.
  Throttling to about 1 Hz makes the cockpit lag the clock by several steps,
  which is the "not current" the owner rejected. Rejected.

Shape of the addition:

- **Where the filter lives.** In the backend route, as a **selection** over the
  `LabHistory` the port already returns: rows whose own recorded time key is
  after boundary `n`'s offset. It computes no quantity, so the history stays a
  host-owned projection that the client never recomputes
  (`D-2026-09-30-lab-cockpit-history` holds). No port or host change is
  required.
- **Family classes.** The contract states the two classes and the backend
  enforces them:
  - **Append families** have a time key: `boundaries` (`offset_minutes`),
    `samples` (`offset_minutes`), `intervals` (`to_offset`), `attempts`
    (`at_offset_minutes`), `applied_events`, `bounded_transitions` and
    `discrete_transitions` (`at_offset_minutes`). The delta carries only rows
    after `n`.
  - **Manifest scalars and small mutable families** are sent whole in every
    delta: status, `boundaries_recorded`, `recorded_through_offset_minutes`,
    `failure`, `notes`, `coverage`, `content_digest`,
    `observation_series_digest`, and `exposures`, which is deduplicated on
    first sight at `lab_history.py:188` and has no reliable boundary key.
  - **Static families** are not re-sent. They are `signals`,
    `bus_attachments`, `reporting_gaps` (the frozen `reporting.gaps`),
    `drawing_context` and `sample_phases`. The delta sends them as empty lists
    or `null`, and the client keeps the values from the base read.
- **Delta envelope.** The response adds a sibling to `history`:
  `delta: {since_boundary: n, through_boundary: m}`. A full read has no `delta`
  key. The rest is the same document, so `isRunHistory` still validates it.
  A delta **always** carries `history_digest: null`. A delta is not a
  verifiable document, and the client never computes a digest.
- **Refusals.** `since_boundary` greater than the boundaries recorded, negative,
  or not a whole number gets a typed refusal (`HISTORY_SINCE_AHEAD` /
  `EXECUTION_REQUEST_INVALID`). The client answers a refusal with one full
  read.
- **The invariant the mechanism rests on (must be tested host-side).**
  Prefix stability: for every `k < m` in a live session, `capture` at `m`,
  restricted to time keys at or before boundary `k`, equals `capture` at `k`,
  family by family and row by row, in order. If any family fails this (for
  example, an attempt whose `at_offset` lies at or before `k` but is only
  generated later), that family moves to the "sent whole" class. It must not
  be patched on the client.

**Contract and schema position:**

- It is a **wire addition only**: an optional query parameter and one response
  key.
- Contract 9 is untouched, because neither the execution projection nor
  physics changes.
- History schema 2 and the persisted artifact are untouched, because nothing
  new is written.
- `history_digest` and `projection_binding` semantics are unchanged: they bind
  the terminal persisted document, and the live path never had them.
- The shared SLD is untouched: it still takes neutral slots, and the Lab side
  maps each boundary's slice into those slots exactly as today.

This counts as a new mechanism, so under `ROLE_CONFIG.md` "Which Reviewer For
Which Round" its first review is a discovery review.

**Server cost.** If the delta's p95 latency at the last boundary of the demo
window is above 50 ms, the host may memoise the capture per
`(session, boundaries_completed)`. That is an internal change with no contract
effect. Do not build it before measuring.

**Terminal reconciliation.** When a step or Run to the end answers terminal,
the client does **one** full read, about 1.15 MB, once per run. That read
replaces the accumulated history as the authoritative document. In tests (and
behind a dev-only assertion), the accumulated history must deep-equal that read
on every append family. On reload, the page does one full read, as today. For
a terminal run that read is the persisted, digest-verified document.

### A2. Client state ownership

- **One owner.** A Lab-side pure module, `liveHistory.ts`, plus one reducer
  hook in `RunFrame`. The reducer owns `{execution, history, followStatus,
  cursor}` and every tick is **one dispatch**. `HistoryInspector` stops owning
  the cursor (today it holds `chosen` at `HistoryInspector.tsx:110`). It
  receives the cursor and an `onSelect` callback. The T025c `BoundaryRecords`
  follows the same cursor.
- **The merge is a pure function.** Its signature is
  `appendHistory(base: RunHistory, delta: RunHistory, envelope): {ok: RunHistory} | {refused: AppendRefusal}`.
  It accepts only when all of the following hold:
  - `run_id` and `inputs_identity` equal the base's;
  - `envelope.since_boundary` equals the base's `boundaries_recorded`;
  - the appended `boundaries` are contiguous from `since_boundary + 1` to
    `through_boundary`;
  - every appended row's time key is strictly after
    `base.recorded_through_offset_minutes`, and rows are ordered within each
    family.

  On acceptance it returns a **new** object: new arrays for the append
  families (`base.x.concat(delta.x)`, with row objects shared, not copied),
  replaced scalars and sent-whole families, and the static families carried by
  reference. It never mutates the base.
- **Structural sharing for memo.** Alongside the flat arrays the reducer keeps
  a `slices: ReadonlyMap<boundary, BoundarySlice>` index. A `BoundarySlice` is
  the interval, samples, attempts and transitions that one boundary owns. It
  is built incrementally, adding entries only for the new boundaries, and
  existing slice objects keep their identity. The SLD mapping,
  `IntervalInspection`, `IntervalDrawing` and `BoundaryRecords` are memoised on
  `(slice, site)`, so a pinned cursor re-renders none of them while play runs.
  The static families keep their identity, so `bindDrawing` and the Site fetch
  run once. The chart model is memoised per series array and extends its point
  arrays for new boundaries rather than rebuilding them. Chart paths are
  recomputed, but only from recorded points (never recomputed quantities).
- **The scheduler stays the scheduler.** `PlaybackScheduler` keeps sole
  ownership of playback state and of the guarded step. It gains no knowledge of
  history. The one change is that `PlaybackDeps.show` may return a promise, and
  the scheduler awaits it before it arms the next delay (or before it resolves
  a pending pause).

  `RunFrame`'s `show` issues the delta read for that answer and then dispatches
  `TICK_COMMITTED {execution, delta}` once. The wall delay therefore runs from
  commit to the next request, and a slow history read slows play instead of
  queuing it. A history failure is **never** a step failure. It must not stop
  the scheduler, retry the step or report as a refusal, because the step
  happened. The late-answer path (`runPlayback.ts:224-229`) and the stop
  re-read go through the same `show`, so they reconcile history too. Manual
  Step and Run to the end use the same commit path.
- **The four AC7 states stay distinct and each has one owner:**
  - **Execution clock**: `execution.boundaries_completed`, from step or read
    answers, owned by the reducer.
  - **History cursor**: `cursor`, owned by the reducer and changed only by
    ticks in live mode or by the user.
  - **Playback state**: owned by the scheduler.
  - **Stage status**: the stage read, still re-read after a control and on
    stop, not per tick.

  The reducer maintains `cursor ≤ recorded ≤ clock`. After a successful tick,
  `recorded == clock`. When a delta failed, `recorded < clock`, and the cockpit
  shows it: "History recorded through boundary k; execution at n".

### A3. Cursor semantics

`cursor = {mode: "live"} | {mode: "pinned", boundary}`.

- **Live.** The selected boundary is the last recorded one, and it advances in
  the same commit as the clock.
- **Pinned.** Any user selection of a boundary earlier than the last one pins
  the cursor there: the range input, the SLD arrow keys, the timeline or chart
  click. A pinned cursor never moves on a tick. Selecting the last boundary,
  pressing `End`, or pressing **Return to live** sets live.
- **Return to live.** The button is visible only while pinned, is always in
  the same reserved slot next to the cursor label, and shows how far behind
  the pin is ("12 boundaries behind live").
- **Pause.** The cursor stays where it is: no snap. This removes F2's jump.
- **Refusal, timeout, network error or 404.** The cursor stays where it is,
  and the last committed history stays. The scheduler's authoritative re-read
  runs through `show`, so it triggers one delta read. A step that was accepted
  but whose answer timed out therefore appears exactly once. A live cursor
  follows it and a pinned one does not.
- **Append refused by `appendHistory`** (out of order, a gap, an identity
  mismatch) or **a delta read failure.** The merge discards the delta and
  performs **one** full read at the next tick, not immediately. If the full
  read also fails, `followStatus` becomes `behind`, the cockpit keeps its last
  good frame with the "recorded through k" note, and the next tick tries a
  delta from `k` again. It never issues more than one history request per tick
  and never runs requests in parallel.
- **Terminal.** The full read replaces the history, and the cursor mode and
  pinned boundary are kept. A boundary is a stable identity.
- **Reload.** Playback starts stopped (unchanged). There is one full read, and
  the cursor starts live at the last recorded boundary. The cursor is not
  persisted.

### A4. No-flicker contract

These are the rules, and the Planner turns them into acceptance criteria:

1. **Stable geometry.** The cockpit (control strip, SLD, inspection, charts,
   timeline) has fixed or min-reserved heights. Nothing above it grows per
   tick (item 1).
   - Chart x-domain: the whole run window `[0, boundaries_total × timestep]`
     from the base read. Unrecorded time stays visibly "not recorded", and the
     curve grows into reserved space.
   - Chart y-domain: taken from a declared bound where the frozen inputs have
     one (state of charge 0-100 %, rated capacities the page already holds).
     Otherwise it is a monotone ratchet to the next "nice" value with about 25 %
     headroom. It never shrinks, and a ratchet is committed in the same frame
     as the point that caused it.
   - Numeric cells use tabular figures and reserved widths (item 9). Status
     text lives in fixed-height slots.
2. **At most one React commit per tick** that touches the cockpit. Execution
   and history arrive in one dispatch. The in-flight flag is not rendered into
   the cockpit and changes only an attribute on the status line (item 8, F4,
   F5).
3. **No intermediate frames.** History is never set to `null` or "loading"
   during follow. The previous frame stays until the next is committed. There
   is no Suspense and no `key` change, and nothing unmounts.
4. **Same boundary everywhere.** The SLD, inspection, chart cursor and timeline
   marker all read one `cursor` from one committed state, so they cannot
   disagree in any frame.
5. **No catch-up bursts** (the existing auto-play decision). One step, then one
   history read, then commit, then the delay. A delta that covers several
   boundaries after a failure is a single request, and all of them are
   committed in one frame. The delta does not animate through them.

### A5. Budgets at the 0.25 s delay

- **Delta payload.** At most 32 KB for a one-boundary delta at any point in the
  demo window, measured as response bytes. It should be of the order of the
  full read divided by the boundary count plus about 5 KB of manifest. The
  static families are not re-sent.
- **Server.** Delta p95 at most 50 ms at the last boundary of the demo window.
  Otherwise, memoise the capture (A1).
- **Client commit.** Tick commit p95 at most 50 ms and max at most 100 ms
  (React Profiler or `performance.measure` around the dispatch), in the
  production build, on the machine that measured T025d's 118 ms selection
  re-render. A pinned-cursor tick should commit the charts and timeline only.
- **Full reads.** One on load, one per terminal. None per tick.

### A6. Verification the Planner can put in acceptance criteria

1. **Merge unit tests (`liveHistory.ts`).**
   - Accept a contiguous delta.
   - Refuse each of the following: a wrong `since_boundary`, a gap, a
     duplicate boundary, a row at or before `recorded_through`, and a
     mismatched `run_id` or `inputs_identity`.
   - The base is unmutated (frozen fixture).
   - Static families and unchanged slices keep their references (`toBe`).
   - Folding deltas 0→1→…→N deep-equals the full read at N.
2. **Host or backend tests.**
   - Prefix stability across every boundary of a fixture run, per append
     family.
   - The delta equals the full read filtered by time key.
   - A delta carries `history_digest: null` and no static families.
   - `since_boundary` past the recorded count is refused.
   - With the gate closed there is still no route.
   - The persisted artifact bytes and the contract-9 gate are unchanged.
3. **Scheduler tests.**
   - `show` awaited: the next step is not requested before the tick commits.
   - A delta failure does not stop playback and is not reported as a refusal.
   - Pause during the delta read resolves to PAUSED after the commit.
   - The late timed-out answer reconciles history exactly once.
4. **Cursor tests.**
   - Live follows the edge on each tick.
   - Pinned does not move across N ticks.
   - Return to live jumps to the edge and resumes following.
   - Pause, refusal and terminal do not move a pinned cursor.
5. **Layout evidence (`tools/layout-evidence.mjs`), auto-play at 250 ms for
   N ≥ 20 steps with a live cursor.** Record the following per frame:
   - the cockpit's top edge and height, the SLD and chart bounding boxes, and
     each chart's axis tick labels;
   - `data-drawing-boundary`, the chart cursor's boundary, the timeline
     marker's boundary and the inspection's boundary.

   Pass criteria:
   - zero movement of the top edge and bounding boxes;
   - x-axis ticks identical;
   - y-axis ticks identical except at logged ratchet events (at most 3 per
     series per run);
   - all four boundaries equal in every sampled frame, sampled on each
     `requestAnimationFrame`, not only after settle;
   - no frame where the SLD or charts are empty.

   Repeat with the cursor pinned: the SLD and inspection DOM nodes are
   unchanged (MutationObserver count 0) across the run.
6. **Payload assertion.** The evidence run logs each delta's response bytes and
   fails if any is over 32 KB. It also asserts that no full read occurs between
   the first step and terminal.
7. **Commit budget.** The evidence run logs the tick-commit timings and reports
   p95 and max against A5.

### A7. Sizing and phases

Build T025e in **three phases**, following `ROLE_CONFIG.md`'s phase rule, with
a fresh implementer per phase and a handoff at
`.agent/T025e-phase-N-handoff.md`. The slice is well beyond one focused change:
a wire addition, a new client state owner, a scheduler seam, and the whole
layout.

1. **Phase 1, data path.**
   - The backend `since_boundary` selection and refusal.
   - The prefix-stability and delta tests (A6.2).
   - `liveHistory.ts` with `appendHistory` and the slice index, and the merge
     tests (A6.1).
   - `runSetupClient` delta fetch.
   - Nothing on screen changes yet.
2. **Phase 2, follow state.**
   - The `RunFrame` reducer.
   - The awaited `show` in `PlaybackScheduler` (A6.3).
   - Lifting the cursor out of `HistoryInspector`, the live and pinned modes,
     and Return to live (A6.4).
   - Charts fed only from the history (item 2, closing C3).
   - The terminal reconcile.
   - Removing the history-on-stop policy.
   - Observable result: the old layout, now current during play.
3. **Phase 3, layout and no-flicker.**
   - Items 1, 3 and 5-10: the primary layout, fixed domains, disclosures,
     prose trim, memo on slices and tabular figures.
   - The A6.5-A6.7 layout-evidence extensions.
   - Full suites and the packet.

Data and state come first because the memo boundaries and the layout's
single-commit guarantee depend on the state's shape. Layout built first would
be rebuilt around the reducer.

The review is one discovery review at the end, covering the wire addition and
the new mechanism.

**Split trigger.** If phase 3 alone is sized at more than one T025d-sized
change, the Planner may cut it into T025f (layout organisation, items 5-7)
after T025e. Live follow and the no-flicker guarantees stay in T025e. The owner
must agree to that cut, because the decision names one slice.
