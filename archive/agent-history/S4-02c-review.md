# S4-02c fresh Claude review: phase 3 and the whole slice (consequence work on accepted evidence)

Reviewer: fresh Claude. I did not build or review any earlier phase. Branch `task/S4-02c-evidence-consequence-work`
at `f385ad3b`.

- Phase 3 diff: `6d4a1995..HEAD`. Whole slice: `5af9f214..HEAD`.
- Phases 1 and 2: only their carries re-checked (`.agent/S4-02c-phase-1-review.md`, `.agent/S4-02c-phase-2-review.md`).

Judged against `tasks/S4-02c-evidence-consequence-work.md` (items 1-5, phase 3 row, C1-C5, R1/R2),
`.agent/S4-02c-plan-fix-rereview.md` (N2, N5, N7), `D-2026-10-14-s402-post-review-follow-ons`,
`D-2026-10-14-s5-selected-window-overview`, the packet `.agent/S4-02c-review-packet.md`, the phase 3 handoff, the
walkthrough evidence (`.md` + `.json`), `.ai/CODE_STATE.md` S4-02c sections and the `backend/README-db.md` runbook.

## Verdict: ACCEPT with carries

The slice delivers its contract. I reran the two-leg walkthrough on my own database and got the claimed pattern
(21/21). I reran the S4-02b walkthrough tool and, unlike the implementer, its browser harness: 92/92. M1 is closed.
The phase-2 carries landed, and one of them killed my own mutation. USER_REVIEW_REQUIRED stays false.

The fixture's sequence-rule change is an acceptable authoring correction. It does not force Leg A, which I
reproduced as identical under both numberings. It is not acceptable as a description of how *this project's*
gateway numbers a late reading, though. I reproduced run 1 too, and the result is more serious than the packet
says. It is an Architect question for S5-01 and real-Site readiness (F1). It is not an S4-02c acceptance gap.

Carries before merge are documentation only: F1's scoping sentence and F2. Neither needs a fresh re-review; the
coordinator can check them by diff.

## Checks I ran (as observed)

| Check | Result |
| --- | --- |
| `tools/s402c_late_power_walkthrough.py run --db assetops_s402c3walk_rv --work %LOCALAPPDATA%/AssetOps/s402c3rv` (code from `f385ad3b`) | exit 0, **0 failed checks** (21). Price v1 `cd6cddd3...`; late evidence `d1a502e1...` at source sequence 14; EVIDENCE_ACCEPTED work `1d1ba7e7...`; Leg A consequence 2 `e73708a0...` CURRENT `QUANTITY_UNAVAILABLE/POWER_NOT_IN_ASSESSMENT_INPUTS`, s5 false; r2 SUPPORT_CHANGED, its FRA work `5bd08502...` drains to `5f676e7e...` CURRENT PRICED, 23 means, 12.65 L, 15.8125 USD, s5 true; r1 HISTORICAL with 2 revisions; replay selected 0, backlog 0; no duplicate basis. Dropped. |
| Run-1 reproduction: same tool, with `LateWalk.power_envelopes` monkeypatched to the S4-02b append numbering (scratch script, not committed), `assetops_s402c3walk_rv1`, ports 8922/8923 | exit 0 with 1 failed check, as the evidence records: late mean at sequence 25; Leg A identical (STALE_QUEUED, then consequence 2 `POWER_NOT_IN_ASSESSMENT_INPUTS`); r2 Candidate `[06:05, 07:00)`, **CURRENT PRICED 11 means, 6.05 L, 7.5625 USD, s5 true**. Details under F1. Dropped. |
| `tools/s402b_fuel_cost_walkthrough.py` `prepare` / `publish-v4` / `recompute` / `recompute --empty` (`assetops_s402brv3walk`/`assetops_s402brv3empty`) | All exit 0. 34 items, 0 failed, 31 appended, 12 replayed, P01 PRICED; after v4, 1 appended, 11 replayed; empty, 31 appended, P01 `UNPRICED (NO_PRICE)`. Matches the packet. Dropped. |
| `tools/s402b-fuel-cost-evidence.mjs` on a fresh pair (`assetops_s402brv3evwalk`/`evempty`), APIs on 8920/8921, Vite dev servers on 5420/5421 (`npm.cmd run dev` started under the sandbox here), CDP 9420 | exit 0, **92/92 claims passed**, including the two new claims "walkthrough recompute (... --tenant demo) succeeded" and "... --empty succeeded". Servers stopped, DBs dropped. |
| Focused S4 suites on `assetops_s402crev3_test`: evidence_consequence_work_postgres, consequence_cause_dispatch, evidence_drain, evidence_drain_postgres, consequence_read, consequence_recompute_postgres, consequence_store_postgres, fuel_cost, finding_api, power_demo_case_postgres | **123 passed** in 3:51 |
| Mutation: phase-2 L1 backlog (`recompute.py:312` -> `len(pending) - len(report.outcomes)`) | the retry test FAILS (killed). Restored with `git checkout`, and the tree is clean. |
| `tools/check-all.ps1` | All 9 guards passed |
| Full backend (2090 per the packet) | not rerun. No finding needed it. |
| Frontend `npm.cmd test` / `build` / `tsc` | not run. The slice changes no `frontend/` file (`git diff --stat 5af9f214..HEAD -- frontend` is empty). |

## Question 1: the sequence-order deviation

**Is the change fixture forcing?** No, in the sense N5 guards against. N5 forbids changing the fixture to make
Leg A's precondition hold. Leg A and N5 pass identically under both numberings, and I reproduced both. The change
affects only the S3/S4 re-evaluation in Leg B, which is upstream reviewed code, not this slice. The packet's phase 3
row says only "one mean withheld until a later decided time", so it fixes no numbering. Run 1 is recorded
transparently. Under SOURCE_ORDER, the variant models a reading the gateway sequenced on time whose upload arrived
late. That is a legitimate path, since sealed batches may upload independently (S2-02). I accept it as authoring.

**But the stated rationale is wrong for this repository, and the real-path consequence is understated (F1).**

## Findings

### F1 (Medium, residual risk and Architect question; not an S4-02c acceptance gap): this project's own late-reading path produces run 1, and run 1 yields current S5-eligible money that is understated without saying so

Files:
- `backend/conversions/s4-power-late-demo-cases-v1.json:11` (`sequence_rule`);
- `.agent/S4-02c-walkthrough-evidence.md` "Run 1";
- packet "Residual risk: New (from run 1)";
- `.ai/CODE_STATE.md` ("late-delivery sequence numbering on real gateways unproved").

The fixture says "a store-and-forward gateway numbers readings when it takes them", so the late mean fills its gap.
That holds only when the gateway *takes* the reading on time and the upload is late. In this repository, the
gateway allocates the next sequence at admission (`gateway/assetops_gateway/service.py:9-11`: "read/increment
sequence" inside the admission transaction). Under `D-2026-10-09-s2-simulated-publication-clock`, a Lab-delayed
reading "has no V3 envelope or sequence" until it is released. So the Lab's simulated late delivery, and any device
reading that reaches the gateway late, takes a sequence *after* later readings: exactly run 1's numbering. The
packet calls this "not proved here". It is determinable from the code, and it is the default late path for S2-S7
simulated input.

What run 1 actually does (my reproduction, then dropped):
- S3 marks `SEQUENCE_ORDER_INVERTED: generator_power 07:05..08:00`. The **window** assessment is `INDETERMINATE`
  with `GENERATOR_SERIES_AMBIGUOUS`.
- The revised **FindingRevision** r2 nonetheless stays `SUPPORTED`/`CANDIDATE_AVOIDABLE`, and its episode shrinks
  to `[06:05, 07:00)`:
  - candidate minutes fall from 115 to 55, and indeterminate minutes stay 0;
  - its only limitation is `OPEN_BOUND: no OFF evidence after the interval`. That misattributes the end of the
    interval, which ends because of the series refusal, not because of missing OFF evidence.
- Its consequence drains to **CURRENT PRICED, 7.5625 USD over 11 means**, and the money predicate the tool uses
  (CURRENT, PRICED, amount present) makes it **S5-eligible**. That is less than half of the 15.8125 USD the same
  physical data gives when numbered in source order. Neither the Finding nor the consequence names the inversion.

So the answer to "can a real late reading never yield current money via this path?" is: **it does yield current
money, but understated, and the truncation is silent at the Finding and consequence level.** The packet has the
direction of the risk the wrong way round. The risk is not that money never arrives. It is that money which is too
low arrives as current.

Effect on acceptance:
- **S4-02c:** none. Item 3/5 and Leg A behave identically. The consequence correctly derives from r2's accepted
  inputs, and the S3 cohort rule and the Finding episode limitation are S3-01/S4-01 reviewed behaviour.
- **S5-01 and real-Site readiness:** affected. S5-01's money read (`mini:4#a`) would show this figure as current.

Fix on the branch (Low, documentation): scope the `sequence_rule` text and the evidence or packet residual-risk
wording to "a reading sequenced on time and uploaded late". State that admission-time sequencing (Lab-delayed or
device-late readings) gives run 1, with the measured result above. Do not change the fixture again.

Architect questions (batch them, per the owner's routing):
- **Q1.** Should S3's cohort rule (`backend/assetops_backend/analytics/cohort.py` `series_limits`, docstring lines
  17-20) treat a gateway-admission-sequenced late reading as an inversion? The technical design says "monotonic
  arrival is not required" (technical design, V3 identity paragraph) and that "late or out-of-order evidence
  recomputes the affected and neighboring continuity window" (Assess step 4). Today the rule refuses the whole
  later span.
- **Q2.** When the window is `INDETERMINATE` with `GENERATOR_SERIES_AMBIGUOUS` over part of a Finding's former
  episode, must the revised FindingRevision carry that limitation (rather than only `OPEN_BOUND`)? And must the S5
  money predicate exclude, or label, a consequence whose FindingRevision's window is INDETERMINATE?
- **Q3.** Does this belong with `R1` and the owner's analysis-input backlog item ("analysis input data for
  simulated and real Sites"), or as its own node ahead of S5-01?

### F2 (Low, tool regression in strictness): the S4-02b `recompute` no longer fails when a work item fails

`tools/s402b_fuel_cost_walkthrough.py:169-182`. Before M1, `tree_py(..., check=True)` raised on the runner's exit 1
(any item failed). Now exit 1 is tolerated, failed items are printed, and the function returns normally, so the tool
exits 0. The new `.mjs` claims (`tools/s402b-fuel-cost-evidence.mjs:254-255`) check that exit status and would
therefore pass with failed items. The later API claims would probably still catch a bad amount, but the
"recompute succeeded" claim no longer means what it says. In the same loop, if 50 runs exhaust with backlog left,
the tool also exits silently.

Fix: after printing, `raise SystemExit(1)` when `failed` is non-empty or the loop ended with backlog > 0.

### F3 (Info, housekeeping): earlier-phase scratch databases remain on the shared server

`assetops_s402c_mut_test`, `assetops_s402c_p1_test`, `assetops_s402c2_main_test`, `assetops_s402c2_mut_test`,
`assetops_s402c2_full_test`. None is phase 3's: the phase 3 `s402c3*` databases were dropped, as were all of mine.
They are worth dropping before merge.

### Not findings (checked)

- **N2:** price v1 is published first and r2 is priced by that revision. I checked the revision-ID equality in my run.
- **N5:** a real assertion. `walk()` stops unless `[07:00, 07:05)` lies inside the merged observed Candidate
  spans, and it also requires the reason to be anything other than `CANDIDATE_SPAN_UNVERIFIED`
  (`tools/s402c_late_power_walkthrough.py:243-250`). Pre-late result: `POWER_COVERAGE_GAP`.
- **N7 / the phase 3 row "include unrelated accepted input as typed no-op":** not shown by the fixture (one bound
  generator), stated in the evidence, and proved in `test_s4_evidence_drain_postgres.py`. The plan re-review
  explicitly allowed this.
- **C5:** exact work, attempt, consequence, accepted and examined IDs and digests are in the evidence JSON. My
  run's IDs differ (fresh DB) and its pattern matches.
- **The superseded no-op branch** did not arise because evidence work drained before r2 existed. The packet says
  so, and the Postgres test covers it.
- **Reads with `source_open=True`:** an honest, stated deviation. The source gate is S4-02b's, and it is exercised
  by the S4-02b harness I ran.

## Question 4: USER_REVIEW_REQUIRED and the phase-2 carries

- **(a)** holds. `NO_WORK_RECORDED` is only a typed `currentness.reasons` code (`consequence_read.py`). No
  `REASONS` entry was added. `finding_api.py` and every `frontend/` file are unchanged across `5af9f214..HEAD`. The
  frontend only types `currentness_reasons` (`financialsClient.ts:103`) and renders none of them.
- **(b)** holds. Leg A ends on the existing `QUANTITY_UNAVAILABLE` bridge reason with the reviewed
  `POWER_NOT_IN_ASSESSMENT_INPUTS` reason, in both my runs.
- **M1** is closed: shown end to end, including the browser harness the implementer did not run (see F2 for one
  strictness gap).
- **L1:**
  - The backlog-after-failure assertion is non-vacuous: my mutation is killed.
  - The `pg_locks` assertion targets the 64-bit advisory key form (`objsubid = 1`, classid/objid recombined), and
    it passes with `claim_site` keyed by `RUNNER_LOCK_PREFIX + site_id`.
  - The other-Site claim is asserted.
- **L2:** the label is fixed.
- **I1/I2:** the runbook now names repeated `skipped` as the hung-runner alarm, and the permanent-failure volume,
  with no code change. This matches the review's allowance.

## Registry closeout notes

- **`I-evidence-acceptance-consequence-work` may resolve on merge.** Evidence: this review, the walkthrough
  evidence, and the phase 1-2 reviews. Every clause of its acceptance target is met:
  - transactional scoped enqueue;
  - dedupe by accepted evidence and target/cause;
  - worker recheck of role/asset/window/latest revision;
  - typed no-op of unrelated input (tests);
  - no identical basis;
  - late power through pending/stale to a recomputed version;
  - a runnable schedule: the one-shot `run` plus the documented external one-minute timer. No timer is installed,
    and none was required.
- **Stays open:**
  - **R1.** S3 `process-jobs` and S4 `match-findings` are unscheduled. Current money after late evidence waits for
    them; Leg B ran them by hand. This needs its own follow-on node or an Architect W1 decision before S5-01 relies
    on "recomputed after late evidence" without an operator.
  - **F1's Q1-Q3.** Sequence inversion of admission-sequenced late readings, and the silent understatement of
    current money, ahead of S5-01's money read.
  - **I1-I4** as named in the packet, plus pre-0012 `NO_WORK_RECORDED` heads without backfill.
- `I-site-overview-read` (S5-01) requires this node. Its packet should carry R1 and F1 explicitly.

## Residual risk not already named by the packet

- F1's direction: understated current money, not absent money, under the gateway's real numbering.
