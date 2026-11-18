# T026 phase 3a handoff (Lab and frontend build)

Branch `task/T026-dispatch-capable-evidence`. Commits: `f26afb2` (build),
`aa22cc2` (tests and regenerated fixtures), and the commit adding this file.
No named stop hit: contract still 9, `var/` untouched, no profile 3/4 content
changed.

## What landed, per AC

- **History wire (AC13).** `liveHistory.ts:35` `APPEND_FAMILY_KEYS` gains
  `records: at_offset_minutes`, `publications: released_offset_minutes`;
  `BoundarySlice` and `SLICED` carry both (`liveHistory.ts` ~:333-380).
  Types `RunHistoryRecord`, `RunHistoryPublication` and guards in
  `runHistory.ts` (`isRunHistory` requires both arrays).
- **Fixtures regenerated, not hand-edited.** `host/tests/make_history_fixtures.py`
  rerun (all fixtures now schema 3, 7 coverage rows; Site detail now template
  v3 as phase 1 made it); new `degraded_evidence_deltas()` writes
  `kobo-degraded-evidence-deltas.json` (1.38 MB: base, delta to 230, single
  steps to 255, full) with real records and the SOC hold 240 -> 250.
- **AC13 markers / T025d C2** (`historyTimelineModel.ts` `allEntries`):
  declared gaps clipped to `recorded_through_offset_minutes`, unreached gaps
  absent; `Policy record` / `Operational record` entries at occurrence
  (suppressed = "None observed ... never establishes that nothing was
  commanded"); `Publication delay` entry spanning source -> release, shown in
  the interval view at both ends only. All in the REPORTING lane of the
  Applied timeline (records are reported evidence, not applied events).
- **AC10.** Inspector (`HistoryInspector.tsx` `attemptArrival`,
  `BoundaryRecords`): new "Publication" column on attempts -
  `SENSOR_GAP` / `DELAYED` (source, published, host `held_minutes`) /
  `NOT_HELD`; new panel "Records and released publications here". Stage
  detail (`RunFrame.tsx` `envelopeArrival`): "Arrival" fact - DELAYED (from the
  history's held row, never subtracted), SENSOR_GAP (UNAVAILABLE), ON_TIME,
  UNKNOWN (no history held).
- **AC14.** Stage panel names a state signal "observed, not staged" only when
  the stage's frozen mapping lacks it (`stagedSignal`). Host:
  `GENERATOR_STATUS_REPORTED_STAGED` (`lab_projection.py`) chosen in
  `with_reported_generator_status(..., mapping)` when `session.mapping` carries
  the status; says staged is "not committed or accepted as Site evidence".
  Profile-4 runs keep the NOT_STAGED text (still true; profile 4's own
  statement "It is not staged: T026 owns that" is frozen profile content and
  was not touched - named-stop territory).
- **Stage rows refined on screen** (backend wire unchanged): `family`/`members`
  optional on `RunStagedEnvelope`/`RunStageMappingEntry`; a record shows
  "POLICY record" in quality (`data-staged-quality="RECORD"`) and as
  "Record" in the detail; mapping "Published as" shows an enum's members.
- **AC15 screen fit.** Capability tracks join existing day curves
  (`historyChartModel.ts`: `pv-available-power` -> PV panel,
  `battery-discharge-capability` -> battery power); a second reported track in
  a panel draws square marks and a dashed join (`HistoryCharts.tsx`,
  `primitives.css` `--alt`). No new panel or region, so T025e C3 not
  triggered. Inspector additions sit in the closed "Raw records" disclosure;
  stage detail in the closed "Stage" disclosure. One cursor drives all.
  `BoundaryRecords` memo gains a `publications` prop whose identity changes
  only when a delta appends a publication. Header: "families recorded 6 of 6
  (1 not applicable)" (`RunHeader.tsx`) - fixed length, not per tick.

## Checks run (3a)

- Frontend full suite: 41 files, 1037 passed. `tsc --noEmit` clean;
  `npm run build` ok.
- Host targeted: `test_t026_history.py` + `test_generator_observation.py`
  35 passed; `test_mini_grid.py` + `test_t026_dispatch_evidence.py` 66 passed.
  Full host/backend/simulator suites NOT run in 3a (3b).
- `check-architecture` and `check-agent-workflow` passed.
- Probes (each reverted with `git checkout`, tree clean): P1 drop append keys,
  P2 drop gap clipping, P3 inspector ignores held rows, P4 unstaged line always
  shown, P5 stage gap not named, host H1 mapping not passed - 6 of 6 CAUGHT.

## 3b must measure / record

- AC15: delta bytes (<= 32 KB) and both 50 ms p95 budgets (server step, client
  tick) with records/publications in every capture; if the server budget
  misses, T025e's named memoisation stop (backlog T025e C2).
- Layout evidence (layout-sensitive surfaces touched): Applied timeline
  REPORTING lane with new entries (long `applies`/`detail` text), inspector
  attempts table now 5 columns, stage envelopes table quality cell, battery and
  PV charts with two reported tracks, header coverage text. Run on a copy of
  `var/`, on a Site from template v3 (v2 sites read BEHIND).
- `tools/layout-evidence.mjs:2794/:2900` asserts the status is "disclosed as
  observed and not staged". True for a profile-4 run; false (line absent) for
  a profile-5 run. Check which run it measures and update the claim.
- T023 stage buttons: degraded 8 h one-shot stage is 329 envelopes (< 500), so
  the carry is not triggered; confirm healthy/prolonged envelope counts.
- Full host, backend, simulator (from `simulator/`), frontend suites serially;
  review packet; CODE_STATE / ACTIVE_CONTEXT.

## Open risks

- `kobo-degraded-evidence-deltas.json` is 1.38 MB in the repo.
- The stage "Arrival" lookup matches on device, signal and source time; two
  held publications of one signal at one source time cannot exist (reorder
  refusal), so it is unique today.
- A run stopped inside a hold never records its publication row (phase 2);
  the inspector then says `NOT_HELD` for that reading ("No publication delay
  recorded"), which is true of the record but not of the gateway.

## Decisions for the reviewer

1. Records and delays go in the Applied timeline's REPORTING lane, not APPLIED.
2. The "observed, not staged" rule keys on the stage's frozen mapping; with no
   stage read yet, no line is shown.
3. Stage `family` is refined on the screen only (backend wire left interim).
4. The header counts NOT_APPLICABLE families apart from missing ones.
5. Fixtures regenerated wholesale (run ids and Site detail moved with them).
