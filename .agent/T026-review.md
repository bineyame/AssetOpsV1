# T026 review - Dispatch-capable evidence

Reviewer: Claude (`assetops-reviewer`, Opus 5.5), fresh session, did not author
any T026 phase. Discovery review per the task's Review section. Diff reviewed:
`3bbcf65..b7677d2`, excluding the planning/ruling commits `37a0e1e`, `bcdbbe5`,
`5fed927` and the workflow-rules commit `21628ec`.

## Verdict

**Accept with findings fixed on the branch.** Two block findings, both small
and local; seven carries. The contract/gateway work, the history families and
the named-stop discipline hold up under reading: profiles 3/4 keep the
schema-1 fuel-only mapping, `mini-grid` v3 is a new version beside v2,
`git diff 3bbcf65..HEAD -- host/tests/contract9_gate
contracts/assetops_contracts/execution_contract.py` is empty, a delay moves only
`published_at` (message id keys on source time, so retries keep identity), and
nothing of T026A (bias, noise, retry, duplicate delivery, buffering, reorder)
was added - a hold that would batch is refused at setup instead.

AC15's server-delta budget miss is the owner's named stop and is not ruled on
here.

## Block

### B1. The inspector's Publication column says "nothing was published" for readings the stage did publish, and calls a lost publication a sensor gap

`frontend/src/shell/HistoryInspector.tsx:463-487` (`attemptArrival`) labels
every attempt with `reported_value === null` as `SENSOR_GAP`, "Sensor gap: no
reading existed, so nothing was published." That is only true of
`SUPPRESSED_BY_GAP`. In the committed degraded fixture
(`kobo-degraded-evidence-deltas.json`, `full.attempts`) the null-value attempts
are 4 `SUPPRESSED_BY_GAP`, **8 `NO_PRECEDING_INTERVAL`** and **3 `DROPPED`**:

- `NO_PRECEDING_INTERVAL` (every `INTERVAL_MEAN` signal at boundary 0, every
  run): the dispatch mapping publishes unavailable
  (`simulator/assetops_simulator/gateway/mappings.py:74`, `publishes_unavailable=True`)
  and `publish` maps it to an `UNAVAILABLE`/`NO_COMPLETED_INTERVAL` envelope
  (`gateway/publish.py:64-67`). Failure scenario: owner puts the cursor on
  boundary 0, opens Raw records - the attempts table says nothing was
  published for `battery-pcs-controller ac-power`; opens Stage at the same
  cursor - an `UNAVAILABLE` envelope for that reading is there. One cursor, two
  contradictory facts, in the very view AC10 exists for ("C's evidence gaps
  trace to accepted inputs"). The stage side (`RunFrame.tsx:1491-1498`) also
  calls this envelope a "Sensor gap: no fresh reading existed", which is wrong
  for a run's first interval: the interval had not completed.
- `DROPPED` (e.g. `battery-pcs-controller state-of-charge` at 195, generator
  status at 135): profile 4/5 describe this as a sample that "does not arrive"
  and `source_envelope.py` documents it as "a publication lost". Labelling it
  "no reading existed" is the gap/delivery confusion AC10 asks the inspector to
  avoid.
- The column is drawn for every attempt of every run, so profile 3/4 runs and
  never-allowlisted signals also read "No publication delay recorded" / "nothing
  was published" for signals no mapping stages at all.

Fix: branch on `outcome` (SUPPRESSED_BY_GAP -> reporting/sensor gap;
DROPPED -> lost in transit, no envelope; NO_PRECEDING_INTERVAL /
NO_VALUE_AT_BOUNDARY -> published as UNAVAILABLE with its reason), and say "not
staged under this run's mapping" when the frozen mapping has no entry for the
signal (the AC14 `stagedSignal` rule already knows this). Make the stage-side
`UNAVAILABLE` text name the reason rather than asserting a sensor gap. Add a
test on a boundary-0 interval attempt and a `DROPPED` attempt; the current test
(`t026Evidence.test.tsx:253-272`) only exercises SUPPRESSED_BY_GAP.

### B2. Profile 5's frozen statements describe a delay parameter that does not exist

`backend/assetops_backend/runs/profiles.py:1647` and `:1658` (profile 5 state
statements) say a publication "can be held back by a declared number of
minutes"; `:232` says a scenario entry "names its delay as a parameter in
minutes". The implementation (decision 1, `observation.py`
`PublicationDelayWindow`) is the opposite: the scenario parser refuses a
duration parameter and the window end IS the release. Failure scenario: an
author reads the profile, adds a `minutes` parameter to a delay entry, and the
scenario parser refuses it; or reads "10 minutes" as a magnitude independent of
the window. Why block rather than carry: this is profile content users read and
that Drafts are set up against. No profile-5 Draft exists yet; the owner's
hands-on review will create the first. After that, correcting the statement is
changing published profile content under an existing document (the
implementer itself treated profile 4's stale "T026 owns that" sentence as
untouchable for that reason). Fixing it now costs two strings and the comment.

## Carry

C1. **stop-60's override becomes an "OPERATOR" command record under profile 5**
(packet decision 16). `host/execution_adapter.py:853`
(`OVERRIDE_CHANNEL_OF_STATE`) and `backend/assetops_backend/runs/service.py:3333`
turn every scenario forcing of the stop threshold or reserve into an
`OVERRIDE_COMMAND` with actor `OPERATOR`, while
`config/scenarios/kobo-mini-grid-stop-60.yaml:3-5` says its override is "not
operator evidence". Scenario: stop-60 run on profile 5; T028 reads an operator
override provenance the scenario author disclaimed. Needs an owner ruling
(declare operator-commandedness on the scenario entry, or reword stop-60);
reached only by new profile-5 Drafts, so not a named-stop breach.

C2. **A held publication reads as on time until it is released** (packet
decision 15, extended). Live cursor at boundary 245 (hold 240->250):
inspector says "No publication delay recorded" for the 240 SOC reading, which
is not yet published; a delayed override record shows "published: ..." at its
occurrence in the timeline (`historyTimelineModel.ts:290`) before its release.
A run stopped inside the hold keeps saying so forever, while the stage has no
envelope. Fix with B1's branch: "not yet published as of the recorded extent"
when the stage lacks the envelope / no release row exists. Not shipped-scenario
reachable for records (the shipped record is missing, not delayed), hence carry.

C3. **Proof row "policy effective at boundary" is covered only with an
effective start weeks before the run.** `test_policy_records_carry_version_effective_time_and_source`
(`host/tests/test_t026_dispatch_evidence.py:228`) asserts `2026-09-01` for a
`2026-09-22` run. No test has a Foundation valid-from at or inside the run
interval, which is the case the row names. Add one (or state that run setup
refuses it, and test that).

C4. **Layout evidence is not fully green.** Three "blocked table" claims FAIL
(attributed to MG-006 being READY in the chosen store copy, unverified by me),
and the stage Arrival fact and the 5-column attempts table were not measured at
the narrow width. Recorded honestly as FAIL/not measured; rerun on a store with
a blocked Site to close it, and include the Arrival fact after B1 changes its
text.

C5. **Scenario headers steer the hands-on review to the wrong model.**
`kobo-mini-grid-prolonged.yaml:6` says "model profile VERSION 2" and the
evening header names no version; both yield no capability signals under profile
5 (`test_a_model_that_measures_no_capability_publishes_none`). The healthy and
prolonged Proof runs need `mini-grid` v3. Comment-only, but the owner follows
headers.

C6. **`JsonSourceStages._verified` is unbounded** (`host/source_stages.py:59`):
one stage text (~267 KB at 8 h) plus its parsed stage per run, kept for the
process lifetime. Harmless at Lab scale; bound it or drop entries on stop.

C7. **Duplicated span rule.** `service.py` `_held_span` restates
`ReportingPathWindow`'s shape rule for the reorder refusal; the agreement test
covers override states, not span arithmetic for POINT/INTERVAL_WIDE. Low risk
today (the shipped delay is a WINDOW).

## Claims checked by reading

- AC1/AC5/AC9: schema 2 beside schema 1; stage document states the mapping's
  envelope schema and the parser cross-checks them; R3 `fullmatch`, R2 `1/0`
  and non-UTF-8 now `StageUnreadable`. Write switched to `write_bytes`; old
  stages are single-line canonical JSON, so no CRLF change reaches them.
- AC2: capability is a `mini-grid` v3 measurement (`resolve_v3`); under v2 the
  signals are no reporting path, not inferred.
- AC4/AC6/AC7: missing-record, gap and SOC hold in the degraded scenario;
  held envelope withheld from the stage until release; sequence spent so the
  release keeps its sequence; no reorder possible since hold <= cadence.
- AC13: two append families with keys mirrored in backend and frontend;
  schema-2 artifacts disclose both as not recorded; held_minutes host-derived.
- AC14: NOT_STAGED kept only where still true (profile 4).
- T026A boundary: no bias/noise on new signals (0/0), no retry/duplicate code;
  the conversion memo is a pure cache, admission still compares.
- C's required evidence has owners: PV inverter, BMS/PCS, generator controller,
  meters, Foundation policy records, operator override records; fuel delivery
  and hand-dip correctly left to T030.

## Checks

Per the dispatch, the full suites, typecheck, build and both repo checks were
verified on the final tree before this review and were not re-run. I ran no
test suite. I inspected the committed degraded fixture directly (Python) to
confirm B1's outcome counts. Not verified by me: AC15 measurements, layout
evidence, the attribution of the three blocked-table FAILs.

## Residual risk not in the packet

- B1's mislabel exists on the stage side too, so the owner's hands-on check of
  the two timestamps can pass while the boundary-0 envelopes read wrongly.
- Policy records carry `effective_end = None` and the override record is the
  only evidence of the 60 % window; in the shipped degraded run that record is
  missing, so C sees an open-ended 90 % policy over 08:00-12:00. Correct by
  AC4's rule, but T028 must not treat an open policy end as "no override".

## Re-review (fix round 1)

Range `1ef1073..HEAD`. Suite numbers taken from the dispatch (not re-run); I
read the diff and cross-checked the mapping against the simulator.

**Verdict: accept.** No new block findings.

- **B1 resolved.** `HistoryInspector.tsx` `attemptArrival` now branches on
  `outcome` and the frozen mapping: SUPPRESSED_BY_GAP -> sensor gap; held row ->
  DELAYED; no stage -> UNKNOWN; signal absent from mapping -> NOT_STAGED;
  DROPPED -> lost in transit; typed absence -> "Published as UNAVAILABLE
  (reason)". `UNAVAILABLE_REASON_OF_OUTCOME` matches
  `simulator/.../gateway/publish.py:64-67` exactly. `unavailableArrival` is shared
  with the stage's `envelopeArrival`, so one cursor now says one thing; only
  REPORTING_PATH_UNAVAILABLE is a sensor gap. New tests cover boundary 0,
  DROPPED, unmapped signal and the stage-side envelope; the implementer
  reports a non-vacuity check.
- **B2 resolved.** Both profile-5 statements and the comment now say the window
  end is the release with no duration parameter; no version guard fired.
- **C7 (shared span rule)** is correctly done via `ReportingPathWindow`.

New carry (not blocking):

- **C8.** `HistoryInspector.tsx` `attemptArrival`: the final `NOT_HELD` branch
  ("No publication delay recorded") is still asserted for a mapped, valued
  reading with no held row, including a reading held but not yet released (the
  earlier C2 case). Scenario: live cursor inside a hold shows no delay for the
  held reading. Unchanged from C2, still open.
- **C1, C2, C3, C4** from the first review remain open as carry (C4: layout
  evidence not re-run after B1 changed Arrival text; the owner's hands-on check
  should look at the Publication column width).
