# T026 review packet - Dispatch-capable evidence

Task `tasks/T026-dispatch-capable-evidence.md` (Status `in_review`).
`USER_REVIEW_REQUIRED: true`. Branch `task/T026-dispatch-capable-evidence`, three
phases; evidence in `.agent/T026-phase-1-handoff.md` (P1), `-phase-2-handoff.md`
(P2), `-phase-3a-handoff.md` (P3). Implementer: Claude (Codex-reset exception).
First review is discovery; reviewer to be named in the report.

## Outcome

A degraded-evidence Draft (template v3 Site, `mini-grid` v3, publication profile
5) stages dispatch-capable source envelopes: PV output and available power,
battery SOC/power/discharge capability, generator power and status (typed enum
member), load meters, policy records and operator-override records. It carries
one reporting gap and one held publication; the cockpit shows source time,
publication time, sensor gap versus delay, records and markers after reload.
Contract version stays 9; Site accepted history untouched.

## Files materially changed

`contracts/assetops_contracts/{source_envelope,lab_history,observation,
operational_records,lab_projection}.py`; `simulator/assetops_simulator/{gateway/
publish.py,gateway/mappings.py,observation/records.py,packs/mini_grid.py,
profiles.py}`; `host/{lab_execution,lab_history,source_stages}.py`;
`backend/assetops_backend/simulator_lab_api.py`; `config/scenarios/
kobo-mini-grid-degraded-evidence.yaml`, template v3; frontend `shell/{liveHistory,
runHistory,historyTimelineModel,historyChartModel,HistoryInspector,HistoryCharts,
RunFrame,RunHeader}`; tests `host/tests/test_t026_*.py`,
`simulator/tests/test_t026_schema2.py`, regenerated history fixtures (incl.
1.38 MB `kobo-degraded-evidence-deltas.json`); `tools/layout-evidence.mjs`.

## Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| 1 schema/profile/mapping | met | P1 AC1; schema 1 reads unchanged; S `test_a_schema_one_mapping_persists_exactly_as_before` |
| 2 output vs capability | met | P1 AC2; v2 publishes no capability (H test) |
| 3 policy evidence | met | P1 AC3 (version, effective interval, source) |
| 4 operational records | met | P1 AC4; present, missing, delayed override cases |
| 5 strict validation, carries | met | P1 AC5; S `TestParserCarries`; 10 of 10 probes caught |
| 6 two imperfections | met | P1 AC6/7; gap + hold, nothing else added |
| 7 source vs publication time | met | P1; delay moves only `published_at`; trajectory and decisions identical (H `test_gap_and_delay_change_publication_only`) |
| 8 enum status | met | P1 AC8; member allowlist; T025b gap/stale untouched |
| 9 persistence | met | P1 AC9; canonical text + mapping byte for byte |
| 10 gap vs delay in inspector | met | P3: Publication column, stage Arrival fact; layout evidence: DELAYED row at boundary 48 |
| 11 three runs stage datasets | met | P1 AC11 |
| 12 allowlist strict | met | P1 AC12 |
| 13 history | met | P2 (schema 3, prefix proof, reload equals live) + P3 (markers, gaps clipped, wire mirror, fixtures regenerated) |
| 14 staging disclosure removed | met | P3; shown only when frozen mapping lacks the signal; layout evidence profile 5: line absent, staged statement present |
| 15 cockpit fit | **partly met** | bytes and client budget pass; server budget misses, see below |

Proof table: sensor dropout = "no fresh reading" (SENSOR_GAP), delayed
publication = source vs later publication time, missing capability = no private
replacement, missing override record = "None observed, not absence of override",
policy at boundary preserves version/effective time: each has a named test in
`test_t026_dispatch_evidence.py` / `test_t026_history.py`. Gap and delay change
reporting only: trajectory and decisions identical. Contract-9 gate unedited
and green. A shipped run stages real `INTERVAL_MEAN` and `UNAVAILABLE` envelopes.

## AC15 measurements (profile 5, degraded, 8 h, 5 min, this machine)

Method: T025e's, via `tools/layout-evidence.mjs` against `vite preview` over a
copy of the run store (served by `tools/run-store-evidence.py serve`); T025e
section now drives a profile-5 degraded Draft (records, gap, hold in every
capture).

| Budget | Limit | Measured |
| --- | --- | --- |
| delta bytes | 32,768 B | max 20,249 B, median 15,024 (30 deltas) PASS |
| tick commit p95 / max | 50 / 100 ms | 30.5 / 34.6 ms PASS (T025e: 10.6 / 11.9) |
| server delta p95, boundary 96 | 50 ms | **108.3, 132.7, 133.6 ms in three runs (p50 84-104) FAIL** |
| full reads | 0 between first step and end | 0 PASS |

Attribution (in-process delta read at boundary 96, 40 reads, same day, same
machine; `scratchpad delta_ms.py`, not committed): pre-T026 tree (3bbcf65,
`mini-grid` v2/profile 4) p95 68.2 and 93.3 ms; this branch profile 4 84.2 and
95.4 ms; profile 5 95.4 and 97.2 ms. Through the proxy the unchanged
profile-4 T025e run on this branch measured 131.7 ms. So the 50 ms budget is
missed here even before T026 (T025e's 45.9 ms does not reproduce on today's
machine, which also runs the client commit about 2x slower than T025e's), and
T026 adds on the order of 0-15 %. This is the named stop: **memoisation
(backlog T025e C2) was not taken**; the Architect/owner decides whether to take
it, re-measure on a quiet machine first, or re-baseline the budget.

## Checks run (serial, final tree)

host 591 passed; backend 1375 passed; simulator 244 passed (from `simulator/`);
frontend 1037 passed (41 files); `tsc --noEmit` clean; `npm run build` ok;
`check-architecture` and `check-agent-workflow` passed. Guard probes: P1 10/10,
P2 5/5, P3 6/6 caught and reverted.

## Layout evidence

Run on a copy of `var/` (sites backdated, `.demo/T025c` runs, no executions;
`var/` untouched), production build, `ASSETOPS_LAYOUT_SITE=MG-006
ASSETOPS_KOBO_SITE=KOBO-V3`. Script updated: the T025b claim follows the run's
profile (`EXPECT_UNSTAGED`: profile 4 line present; profile 5 absent plus the
staged statement), the Kobo setup now picks its Site (T025g left it unable to),
and a T026 section measures a completed profile-5 run at 1280 and 640: staged
statement, 329 envelopes, 6 record rows, 15 timeline entries, 2 square-mark
second tracks in 9 panels, no page overflow, overflowing tables scroll inside
their region, and the cursor through boundaries 48-51 shows the Publication
delay entry and one delayed attempt row in a five-column table. Result: all
T026 claims PASS; 4 FAIL in the full run: the server-p95 budget above and 3
pre-existing "blocked table" claims (run setup against MG-006 is READY, so no
blocked table exists; environment of my store choice, repeats at three widths).
Not measured: stage "Arrival" fact and inspector at 375 px.

## Known deviations

- AC15 server budget missed (above).
- Profile 4's own frozen text "It is not staged: T026 owns that" was left (named
  stop territory); the Lab's profile-4 line stays true.
- Stage family/members refined on screen only; backend wire left interim.

## Residual risk

The 1.38 MB fixture; the stage Arrival lookup is unique only because the
reorder refusal forbids two holds of a signal at one source time; stage write
cost 36-47 ms CPU per control (no stated budget).

## Decisions for the reviewer

1. Delay = the hold window (no magnitude field; scenario parser refuses durations).
2. Reorder bound refused at setup (`PUBLICATION_DELAY_REFUSED`).
3. Override records are the scenario CONTROL overrides executed as operator commands.
4. No shipped world curtails PV: available equals output; the distinction shows on the battery.
5. Healthy world runs on `mini-grid` v3 though its header says v1.
6. Two history families: records (append at occurrence), held publications (append at release); undelayed publications are not rows.
7. Records coverage keys on the mapping having a record channel; record `members` are component ids.
8. `held_publications` re-derives publish's skip rules, bound by a stage-agreement test.
9. Stage withholds an envelope until its release (shared `_still_held`).
10. Records and delays sit in the REPORTING lane, not APPLIED.
11. "Observed, not staged" keys on the frozen mapping; with no stage read yet no line shows.
12. Header counts NOT_APPLICABLE families apart from missing ones.
13. Fixtures regenerated wholesale (run ids and Site detail moved).
14. Stage order in a stepped run is arrival order (pre-existing; contents identical).
15. A run stopped inside a hold shows "No publication delay recorded" for the held reading (no release row exists).
16. `kobo-mini-grid-stop-60` override now publishes a record despite its "not operator evidence" header.
17. Whether to take memoisation (C2) for the server budget.

## User-review focus

The owner follows one sample through the delayed case and identifies the two
timestamps (SOC 07:00:00Z source, 07:10:03Z published, held 10 min). The hands-on
check needs a Site the owner creates from template v3 (a v2 Site reads BEHIND),
then a Draft of `kobo-mini-grid-degraded-evidence` on `mini-grid` v3 / profile 5.
Reviewer checks C's required evidence has real owners and that nothing of T026A
(bias, noise, retries, duplicates) crept in.

## Fix round 1 (review `.agent/T026-review.md`)

- **B1.** `HistoryInspector.tsx` `attemptArrival` now branches on `outcome` and the
  run's frozen mapping (passed to `HistoryRecordsAtCursor`/`BoundaryRecords`):
  SUPPRESSED_BY_GAP stays a sensor gap; a held row is DELAYED; no stage held is
  UNKNOWN; a signal absent from the mapping (profile 3/4 included) is NOT_STAGED;
  DROPPED is "lost in transit, not a sensor gap"; a typed absence the mapping
  publishes reads "Published as UNAVAILABLE (reason)". `unavailableArrival` is
  shared with `RunFrame.envelopeArrival`, so inspector and stage agree at one
  cursor; only REPORTING_PATH_UNAVAILABLE is called a sensor gap. `stagedSignal`
  moved to the inspector module. Tests (`t026Evidence.test.tsx`, `settledScreen`):
  boundary-0 interval attempt, DROPPED attempt, signal absent from the mapping,
  stage-side boundary-0 envelope. Non-vacuity: DROPPED branch disabled, the
  DROPPED test failed (1 failed, 16 passed), restored with `git checkout --`.
  Existing inspector tests now use a mapped stage.
- **B2.** `profiles.py` comment and the two profile-5 statements say the delay is
  a declared window, released at its end, with no duration parameter. No
  fingerprint or version guard fired; no version move.
- **C7.** `service.py` `_held_span` now builds a `ReportingPathWindow` and reads
  its start/end, the rule the host resolves delay windows with. (`_still_held` is
  a release comparison, not span arithmetic, so the shared rule is the window.)
- Suites: frontend 1041, typecheck and build clean, host 591, backend 1375,
  simulator 244, check-architecture and check-agent-workflow pass. Layout
  evidence not re-run (B1 changed the Arrival text; C4 remains open).
