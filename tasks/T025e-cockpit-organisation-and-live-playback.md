# T025e - Lab cockpit organisation and live playback (L1c)

Status: in_review
USER_REVIEW_REQUIRED: true

Map: Lab cockpit L1c. Depends on: completed T025d and T025c. Next: T026.
Branch: task/T025e-cockpit-organisation-and-live-playback
Sizing: beyond one focused change; three phases per `.ai/ROLE_CONFIG.md`.
Planner: Claude under `D-2026-09-30-planner-claude-until-reset`.

## Outcome

Press Play in gated Lab: the SLD, selected-interval inspection, day curves and
Applied timeline stay current at every boundary without moving, blanking or
disagreeing. A pinned earlier boundary holds while play continues; Return to
live resumes following. The first viewport is an organised cockpit.

Why now: the owner accepted T025d functionally but found it poorly organised,
"too low a bar", and flickering. `D-2026-09-30-t025e-live-follow` adds live
follow "with no flicker" and retires read-history-on-stop. T026 adds panels
here next. Function outranks fidelity; the organisation floor is required.

## Read for detail

- `.agent/T025e-architect-guidance.md` (F1-F6, items 1-11; addendum A1-A7 wins).
- `D-2026-09-30-t025e-live-follow`, `-lab-cockpit-history`, `-presentation`;
  T025d packet; carry C3 in the milestone backlog; `tasks/README.md` checks.

## Phases

A fresh Implementer per phase; each ends with committed work and
`.agent/T025e-phase-N-handoff.md` (what landed, anchors, next, open risks).

1. **Data path (AC1-AC3).** Nothing on screen changes.
2. **Follow state (AC4-AC8).** Observable: the old layout, current during play.
3. **Layout and no-flicker (AC9-AC12)**, then full suites and the packet.

## Acceptance criteria

1. **Wire addition, no contract or schema move.** The gated history read takes
   optional `since_boundary=n` and answers the same `history` document plus
   sibling `delta: {since_boundary, through_boundary}`. Append families
   (boundaries, samples, intervals, attempts, applied events, bounded and
   discrete transitions, `exposures`) carry only rows whose recorded time key
   is after n (`exposures` append-class: owner approved 2026-09-30 after phase
   1 measured 71,935 B); manifest scalars, coverage and content/observation
   digests are whole; static families (signals, bus attachments, frozen reporting gaps,
   drawing context, sample phases) are empty or null; `history_digest` is null.
   It is a backend-route selection over the port's `LabHistory`, computing
   nothing. Without the parameter the read is unchanged and has no `delta`.
   Negative, non-integer or ahead-of-recorded n gets a typed refusal. Contract
   9, history schema 2, port, `projection_binding` and persisted artifact are
   unchanged. Tests: delta equals full read filtered by time key; no static
   families; refusals; closed gate has no route; artifact bytes and contract-9
   gate unchanged.
2. **Prefix stability (host test).** Across every boundary of a fixture live
   session, capture at m restricted to keys at or before k equals capture at k,
   per append family, row by row, in order. A failing family moves to the
   sent-whole class and the handoff names it; the client never patches it.
3. **Pure merge.** Accepts a delta only on matching run and inputs identity,
   `since_boundary` equal to the base's recorded count, contiguous boundaries,
   and ordered rows after the base's recorded-through time. Returns a new
   object, carries static families and unchanged boundary slices by reference,
   extends a per-boundary slice index. Unit tests: accept contiguous; refuse
   wrong `since_boundary`, gap, duplicate, row at or before recorded-through,
   identity mismatch; frozen base unmutated; old references `toBe`-equal;
   folding deltas 0..N deep-equals the full read at N.
4. **One commit per tick.** One `RunFrame` owner holds execution, history,
   follow status and cursor. Every committed answer (auto-play, Step, Run to
   the end, late timed-out answer, stop re-read) is one dispatch with its
   delta. The scheduler still solely owns playback and the guarded step and
   knows nothing of history; it awaits a promise from `show` before arming the
   next delay or resolving pause. Tests: no next step before commit; history
   failure neither stops play nor reports a refusal; pause during the delta
   read resolves PAUSED after commit; late answer reconciles history once.
5. **Honest lag, bounded requests.** A refused merge or failed delta makes one
   full read at the next tick; if that fails the last good frame stays with
   "History recorded through boundary k; execution at n", and the next tick
   retries from k. At most one history request per tick, never parallel; a
   multi-boundary delta commits in one frame. Cursor <= recorded <= clock;
   recorded equals clock after a successful tick.
6. **Full reads only at the edges.** One on load, one on terminal; the
   terminal read replaces the accumulated history and in tests deep-equals it
   per append family. None between first step and terminal; history-on-stop
   is gone. Reload starts stopped, cursor live, not persisted.
7. **One cursor, live or pinned.** SLD, inspection, chart cursor, timeline
   marker and T025c raw records (own `<select>` removed, labelled "interval
   decided at T") read one cursor under one convention. Live follows the last
   recorded boundary in the clock's commit. Selecting an earlier boundary by
   range, SLD arrows, timeline or chart pins; the last boundary, `End` or
   Return to live resumes. Return to live shows only while pinned, in a
   reserved slot beside "History cursor", with boundaries behind live. Pause,
   refusal, timeout, not-found and terminal never move the cursor. Tested.
8. **Charts from history, fixed geometry.** Per-step execution data no longer
   reaches the charts (closes C3). X-domain is the whole run window from the
   first frame, unrecorded time labelled "not recorded". Y-domain uses a
   declared bound where frozen inputs give one (SOC 0-100 %, held ratings),
   else a monotone "nice" ratchet with headroom, never shrinking, moved in its
   point's frame. Paths come from recorded points only.
9. **Organised first viewport at 1280 px.** Control strip: execution status,
   execution clock ("boundary n of N"), Start, Step with count, Run to the
   end, Play/Pause with delay, one-line playback status in a fixed slot; long
   text behind "How playback works". Directly below: SLD beside selected
   interval inspection (requested/accepted, `limited_by`, per-load service,
   one-line balance verdict with the table expandable), a "History cursor"
   distinct from the execution clock, day curves, Applied timeline. Nothing
   above the cockpit grows per tick.
10. **Everything else on demand, nothing lost.** Closed `<details>`: run
    identity and frozen inputs (`RunHeader` merged with "This run"), execution
    provenance, latest step on the execution clock (electrical, generator,
    observation panels, both "against simulation time" tables), time-series
    tables as the charts' accessible alternative, raw records, coverage, paths
    and declared gaps, stage and envelopes, commitments. "What this run is not"
    is one visible line; duplicate facts and digests go; captions are one line.
    Truth labels stay beside values (zero/absent/unmodeled, stock vs flow,
    accounting PV is not a wire, a reporting gap is not an outage). Every
    `data-*` hook and heading id survives.
11. **No intermediate frames.** History is never null or loading during
    follow; no Suspense, `key` change or unmount. In-flight is an attribute on
    one stable status sentence, announced once per tick. SLD mapping,
    inspection, drawing and raw records memoise on the boundary slice, so a
    pinned tick re-renders only charts and timeline. Numbers use tabular
    figures and reserved widths.
12. **Measured smoothness.** `tools/layout-evidence.mjs` opens disclosures
    before measuring and adds >= 20 auto-play steps at 250 ms. Live cursor,
    sampled every animation frame: cockpit top and height, SLD and chart boxes
    never move; x ticks identical; y ticks identical except logged ratchets
    (<= 3 per series); drawing, chart, timeline and inspection boundaries equal
    in every frame; no empty SLD or chart frame. Pinned: zero mutations on SLD
    and inspection nodes. One-boundary deltas <= 32 KB; no full read between
    first step and terminal; tick commit p95 <= 50 ms and max <= 100 ms in the
    production build; server delta p95 <= 50 ms at the demo window's last
    boundary. Existing widths still pass.

## Protected seams, stops and proof

`ConfiguredSingleLineDrawing` is unchanged and imports no Lab, simulator, gate
or shell type; memo and layout stay Lab-side. Cursor, clock, playback and stage
status keep one owner each; stage is re-read after a control and on stop only,
and stays reachable. History stays a host-owned gated projection the client
merges but never recomputes. T025d's guarded playback holds: no burst, no blind
retry, pacing-independent digests. Presentation truth labels survive the trim.

Named stops: over the server budget, the host may memoise capture per session
and boundary count internally, only after measuring. A budget still missed is
reported with measurements for the owner, never passed silently. If phase 3
exceeds one T025d-sized change, report before cutting: only the owner may move
guidance items 5-7 to a T025f; live follow and AC11-AC12 stay here.

Run shared checks, affected backend/host/frontend suites, the contract-9 gate
and layout evidence on copied/isolated var; evidence at
`.agent/T025e-layout-evidence.txt`, packet at `.agent/T025e-review-packet.md`.

## Scope limits and review

No physics, Lab fact, contract, schema, artifact, stage, publication, operator
surface, reset or jump (T029A); T026 owns dispatch report panels.

First review is a **discovery** review (`.ai/ROLE_CONFIG.md`: new mechanism and
wire addition) of the whole slice after phase 3; the report names its reviewer.
The owner judges organisation and flicker-free current playback. Outcome: pending.
