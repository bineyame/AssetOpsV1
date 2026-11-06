# Build sheet DD-1: the B-22 baseline with the story injected, fill-any-day, and a prepare that drains to empty, split into DD-1a and DD-1b

- Architect: Claude (Architect 5), 2026-11-04. Rulings are logged in the plan as **DD1-R**.
- Owner decisions (OWN-1104):
  - OD-P11 = **B-22**, fallback B-16;
  - OD-P12 = **one-time 3 h sequential E3**, background, keep-awake, hard stop at 6 h, after the DD-0c re-probe;
  - the levers are gateway batching (L1) and the Cold steady day as one 24 h run (L2);
  - **no set-based insert**;
  - BASE-1, FILL-1, OD-P13 (two labelled steady-day scenarios), OD-P14.
- Inputs:
  - `DD-0-probe-results.md`, `DD-0b-probe-results.md` and **`DD-0c-probe-results.md`** (required before code);
  - plan §2.5.1/§2.5.1a;
  - CH-9 §9 (`mill-midday`, measured daylight), CH-9b R8, MD-0 §7 and §15 (Kobo-only);
  - CH0-R (COH-3 non-vacuous), DS-1 §4.
- Lane 2, after CH-9b: **DD-1a → DD-1b**. Then CH-5c. Paths: `B/` = `backend/assetops_backend/`, `T/` = `backend/tests/`.

## Why it is split (DD1-R S1)

The Architect 4 scope (6 units) plus OWN-1104's additions comes to about 6.5 units:
- the L1 batching knob;
- the prepare drain to empty with its finish rows;
- the tick-output split;
- the publication and MG-1 clock seams.

The owner's rule splits anything over 6.

| Slice | Units | Delivers |
|---|---|---|
| **DD-1a** baseline data | 3.5 | Steady scenarios (L2 Cold as 24 h), the B-22 day list with story days injected, EV Tuesdays, `mill-midday` placement, planned `missing` days, FILL-1 steady kinds, L1 batching |
| **DD-1b** prepare and proof | 3 | Story-time Actions (ACT-002/003, causes), clock seams, backfill and drain-to-empty in prepare, finish rows, tick output split, the trimmed partial-prepare rehearsal and the E3 cost report |

## 1. Rulings (DD1-R)

| # | Ruling |
|---|---|
| R1 | **Length B-22.** Story days are injected at their S-relative dates (`S = prepare day − 2`, `tools/demo_combined.py:124`). The baseline covers `[S−20d, S+1d]` per Site, on each Site's declared calendar: Kobo and Cold 24 h, EV Tuesdays 08:00–16:00Z. Days before a Site's install refuse with `DAY_BEFORE_INSTALL` (DD-0b §8). The day list starts each Site at its first day on or after install. A missing EV Tuesday is reported, not moved. **Fallback B-16** only if the DD-1b rehearsal projects E3 over 3 h (OWN-1104). The owner is told before E3. |
| R2 | **Steady scenarios (OD-P13), reviewed as data.** `kobo-steady` is derived from `kobo-daytime` / `kobo-mini-grid-evening`, and `cold-steady` from `cold-normal`: same model, profile and seed, forcings removed, no value changed. **Cold's steady day is one 24 h run (L2)** if DD-0c §4 proves it equivalent; otherwise the measured shape DD-0c gives. Each file carries `label: "example data, steady day (derived from <scenario>)"` and its source lines. A reviewer diffs each against its parent. |
| R3 | **L1 batching.** Delivery uses the largest legal seal (≤ 256 envelopes per device) **only if DD-0c §2 parity was equal**. If DD-0c found the knob hard-coded in gateway code, the change is a reviewed gateway edit here (+0.25, within DD-1a). If parity differed, stop: the Architect rules. |
| R4 | **The day list** (`backend/conversions/demo-story-days-v1.json`, the next version):<ul><li>steady days fill every baseline day not taken by a story day;</li><li>planned `missing` days, one per Site in the baseline (for example Kobo's "gateway offline"), read NO_DATA and are fillable live (FILL-1);</li><li>`mill-midday` (CH-9 R7) is placed so that 3 COMPLETE days fall on each side within the baseline (CH-9b R8). Placement only, never values.</li></ul> |
| R5 | **FILL-1 in `add-day`** (`tools/demo_story_days.py:200-231`; the children `tools/demo_combined_{kobo,cold,ev}.py`):<ul><li>it adds the `steady` kinds;</li><li>it keeps the five refusals (`DAY_HAS_EVIDENCE`, `DUPLICATE_DAY`, `OUTSIDE_BOARD_WINDOW`, `DAY_NOT_IN_PAST`, `PREPARE_ONLY_KIND`);</li><li>ST-7 rule: a day is addable once it has ended in real time;</li><li>delivery is at real time, and readings keep their story time.</li></ul> |
| R6 | **Story-time facts (CH0-R, DD-1b).** ACT-002 (Cold) and ACT-003 (EV), with their APPLIED and case causes, are recorded at story time through the existing seams (MD-0 P1 table). COH-3 must evaluate at least one pair per Cold and EV board with an Action. |
| R7 | **Clock seams (DD-1b).** `evidence_publication.recorded_at` (ledger `:429`) and the MG-1 objective's `recorded_at` (`postgres_objective_store.py:125`) get test/prepare clock overrides in the style of the existing `test_*_clock_override` seams. Also a story-time `available_at` on the DB-trigger enqueues (EV 0025, mini-depth 0029, the opportunity enqueue), so studies and jobs carry story time (MD0-S3 Q3). Prepare-only, refused outside `assetops_polish_*`/`*_test`. Parity: an unset override leaves product behaviour unchanged (L2). |
| R8 | **Prepare drains to empty (DD-1b).** After ingestion, `prepare` runs:<ol><li>`python -m assetops_backend.chain.backfill --steps a,b,c,d` (its own bound);</li><li>tick and drain until `snapshot_dirty = 0` and the `snapshots`, `threads` and `lifecycle` consumers have no pending subscribed events. At most N ticks, N = ceil(dirty rows / `chain_snapshot_items`) + 2. Each tick is logged, and a stop past N is a prepare failure with the counts, never a silent pass.</li></ol>The live cap `chain_snapshot_items = 200` is **not** raised: ST-7's one-day add drains in one tick (DD-0b §4). |
| R9 | **Tick output split (DD-1b).** `B/scheduling/tick.py:191-193` keeps each stage's `consume` and `drain` sub-objects (ms, consumed, pages, deferred) in the printed JSON and the `assetops.perf` line. Output only; no behaviour change. |
| R10 | **Finish rows (DD-1b, `demo_combined_finish.py`).**<ul><li>**F-DRAIN:** 0 dirty, 0 pending.</li><li>**F-COH:** `chain_coherence.py check` with no expectation file passes (EX-2).</li><li>**F-PERF:** `perf_budget.py` runs and reports.</li><li>**F-THREADS:** the expected threads for the story (counts per thread, ACT-001/002/003 states).</li><li>**F-COH3:** non-vacuous.</li><li>**F-FILL:** a planned missing day reads NO_DATA.</li><li>**F-CAL:** every Site-day of the day list has its expected snapshot rows.</li></ul> |
| R11 | **Not in DD-1.**<ul><li>The set-based insert (OWN-1104, post-demo).</li><li>A commit-safe outbox cursor: only if the DD-1b rehearsal shows one 24 h Kobo day's consume above 50% of `chain_snapshot_seconds` (CH1b-R2 item 2). DD-0b projects about 35%.</li><li>MD-0 parity: `late_fill` stays MD-0's own, Kobo only (MD0-S2).</li></ul> |

## 2. Pre-flight (both parts; batch the answers, then stop)

- **P1.** The DD-0c results applied: the L1 knob location and parity, the Cold 24 h equivalence, and the projected B-22 sequential time. Over 3 h → state the B-16 projection and stop for the owner.
- **P2.** Install dates per Site against `S−20d` for the planned E3 date, and the EV Tuesdays that result.
- **P3.** `add-day` and prepare paths for the new kinds, with `path:line`, and the busy-lock behaviour.
- **P4.** The seams for R7 and the guard registration they need.
- **P5.** `tick.py` output assembly (R9) and every consumer of the tick JSON (finish check, tools).
- **P6.** Memory: the sequential prepare's peak on the rehearsal, against the 2 GB floor.

## 3. Tests

- **L0:** day-list validation (overlap, before install, `missing` kinds, `mill-midday` spacing); the FILL-1 refusals; R8's N formula; the R9 output shape.
- **L2:** the R7 seams (set and unset); `add-day` steady kind end to end on one Kobo day; the R8 loop on a seeded backlog stops at 0, and fails past N.
- **§4.4 partial prepares:** `prepare --sites kobo --days <7 days incl. one missing and mill-midday>`, the same for Cold (3 days, one 24 h steady) and EV (2 Tuesdays). Then the R8 drain and the R10 finish rows. Report wall time per Site-day and project B-22 sequential.
- **Existing, scoped:** `test_demo_story_days*.py`, `test_demo_combined_*` (not the full-prepare test, which runs at E2), `test_s6_verification_replay*`, `test_ch1b_*`, the tick tests, `tools/checks/test_chain_coherence.py`.
- **Guards:** A, W, N, V, M; the estate guard self-tests only if R7 edits the guard.

## 4. DS-R1 and OL-1

| Item | Resolution |
|---|---|
| Sparse story days and honest PARTIAL/LOW grades | **Fixed** by the full-calendar baseline; grades are what the data gives |
| Build-time-dated Cold/EV Actions (COH-3 vacuous, I-09) | **Fixed** (R6) |
| Publication and MG-1 `recorded_at` at build time (MD0-PF Q1/Q5) | **Fixed** (R7) |
| Drain left to later ticks after prepare | **Fixed** (R8) |

**OL-1:** no outcome link changes.

## 5. Size

| Slice | Units |
|---|---|
| **DD-1a** | 3.5: R2 scenarios 1, R4 day list and injection 1, R5 FILL-1 0.75, R3 batching 0.25, L0/L2 0.5 |
| **DD-1b** | 3: R6 0.75, R7 0.5, R8 0.5, R9 0.25, R10 0.5, rehearsal and report 0.5 |

## 6. Review focus

- No value tuned. Scenarios are reviewed as data against their parents.
- Story dates come from S, and no day is moved to fit.
- Prepare ends at 0 dirty, or fails loudly.
- E3 projected under 3 h, or B-16 put to the owner.

## Build units (split 2026-11-05)

- Architect: Claude (Architect 13), 2026-11-05, under the owner's efficiency rule (`.ai/ROLE_CONFIG.md` "Token Efficiency", demo-sprint additions). Plan row **SPLIT-1**. The DD1-R rulings are unchanged.
- **Two must-haves sized here; they were never in the 6.5.**
  - **Full-day story days (+0.5, DD-1a).** CH9-R4 (`build-sheet-CH-9.md` §12, "Polish summary row") made them a hard G5 requirement, and CH9-R2 Q2 (§10) gave the direction: a story day is the full declared day, with the story scenario run in its hours and the steady scenario (R2) in the rest, using existing scenarios only. The work is one more day-list kind shape (story hours plus steady complement), its overlap check, and the producer children running two scenarios in one Site-day. If the DD-1 pre-flight measures the extension above the +50% prepare budget, it goes to the owner then, as a measured choice.
  - **M2 trigger-cost measurement (+0.25, DD-1b).** Owned by DD-1b (`build-sheet-CH-5c.md` §8.6 M2): on the 24 h volume, for one data-bearing tick, the change rows written, settle seconds with and without the triggers (one A/B), and `wmtime` for the tenant-wide and per-Site terms. Stop rule: `wmtime` > 50 ms or trigger cost > 10% of settle seconds goes to the Architect.
- **Sizes:** DD-1a 3.5 → **4.0** (2 + 2); DD-1b 3 → **3.25** (1.5 + 1.75). The +0.75 is new scope, not split overhead.
- **Pre-flight.** P1–P6 (§2) are answered once, by the DD-1a1 builder (Opus), before any code, because P1 (DD-0c results, B-22 projection, over 3 h → owner) and the full-day extension cost gate both slices. `.agent/DD-0c-probe-results.md` must exist first; if it does not, stop.
- **Common rules** as in `build-sheet-CH-5b.md` "Build units".

| Unit | Size | Scope | Depends on | Review |
|---|---|---|---|---|
| **DD-1a1** steady scenarios, full-day story days, batching | 2 | R2 (1), full-day story days (0.5), R3 (0.25), their L0/L2 (0.25) | CH-9 merged; DD-0c results | Own review (scenarios reviewed as data against their parents) |
| **DD-1a2** the B-22 day list and FILL-1 | 2 | R1, R4 (1), R5 (0.75), their L0/L2 (0.25) | DD-1a1 merged | Own review |
| **DD-1b1** story-time Actions, clock seams, tick output | 1.5 | R6 (0.75), R7 (0.5), R9 (0.25) | DD-1a2 and CH-9b1 merged | Own review |
| **DD-1b2** drain to empty, finish rows, rehearsal, M2 | 1.75 | R8 (0.5), R10 (0.5), the §3 partial-prepare rehearsal and E3 report (0.5), M2 (0.25) | DD-1b1, **CH-9b3** and CH-5c2 merged | Own review |

**DD-1a1 (2).**
- **Reading budget:** this sheet header, §1 R2, R3, R11; §2 (all P items, answered here); §3 L0/L2 lines for scenarios; `.agent/build-sheet-CH-9.md` §10 Q2 third bullet and Q8, §12 "Polish summary row"; `.agent/DD-0c-probe-results.md` §2 and §4. Code: the parent scenario files (`kobo-daytime`, `kobo-mini-grid-evening`, `cold-normal`, by grep under `backend/conversions/`), the gateway seal setting (DD-0c §2 location).
- **Acceptance:** each steady file diffs against its parent with forcings removed and no value changed, and carries its label and source lines; Cold steady as one 24 h run if DD-0c §4 proved it equivalent; a full-day story day composes story hours plus steady complement with no overlap and no gap, validated at L0; batching uses the largest legal seal only with DD-0c parity equal (else stop); L2 one Kobo full-day story day end to end grades COMPLETE where the data is complete; the measured cost of the full-day extension reported against the +50% prepare budget; scoped `test_demo_story_days*.py`, `test_demo_combined_*` (not the full-prepare test); guards A, W, N, V, M.

**DD-1a2 (2).**
- **Reading budget:** §1 R1, R4, R5; §3 L0 (day-list validation, FILL-1 refusals) and L2 (`add-day` steady kind); `.agent/build-sheet-CH-9b.md` §1 R8; the P2/P3 answers. Code: `tools/demo_story_days.py:190-240`, `tools/demo_combined.py:115-135`, the three `tools/demo_combined_{kobo,cold,ev}.py` children (grep the kind dispatch), `backend/conversions/demo-story-days-v1.json`.
- **Acceptance:** the next day-list version covers `[S−20d, S+1d]` per Site on its calendar, refuses `DAY_BEFORE_INSTALL`, reports (never moves) a missing EV Tuesday; one planned `missing` day per Site reads NO_DATA; `mill-midday` with 3 COMPLETE days on each side (placement only); L0 validation (overlap, before install, `missing` kinds, `mill-midday` spacing) and the five FILL-1 refusals; L2 `add-day` steady kind on one Kobo day, delivered at real time with readings at story time; scoped tests as DD-1a1; guards A, W, N, V, M.

**DD-1b1 (1.5).**
- **Reading budget:** §1 R6, R7, R9; §2 P4, P5 answers; §3 L0 (R9 output shape) and L2 (R7 seams set and unset). `.agent/build-sheet-MD-0.md` P1 table (the seams, grep). Code: ledger `:420-435` (`evidence_publication.recorded_at`), `postgres_objective_store.py:115-130`, the 0025 / 0029 / opportunity enqueue triggers (grep `available_at`), `B/scheduling/tick.py:180-200`, an existing `test_*_clock_override` seam as the pattern.
- **Acceptance:** ACT-002 and ACT-003 with APPLIED and case causes recorded at story time, and COH-3 evaluates at least one pair per Cold and EV board; the clock overrides are prepare-only and refused outside `assetops_polish_*` / `*_test`; an unset override leaves product behaviour byte-unchanged (L2); the tick JSON and `assetops.perf` line carry per-stage `consume` / `drain` with every tick-JSON consumer (P5) still passing; scoped `test_ch1b_*`, the tick tests, `test_s6_verification_replay*`; guards A, W, N, V, M (estate guard self-tests only if R7 edits the guard).

**DD-1b2 (1.75).**
- **Reading budget:** §1 R8, R10, R11; §3 L2 (R8 loop) and the §4.4 partial-prepare bullet; §6; `.agent/build-sheet-CH-5c.md` §8.6 M2 paragraph only; the P1 and P6 answers. Code: `tools/demo_combined_finish.py`, the prepare entry in `tools/demo_combined.py` (grep `prepare`), `python -m assetops_backend.chain.backfill` arguments (grep), `tools/checks/chain_coherence.py` and `perf_budget.py` CLIs.
- **Acceptance:** L0 R8 N formula; L2 the drain loop on a seeded backlog stops at 0 and fails past N with the counts; the R10 finish rows F-DRAIN, F-COH, F-PERF, F-THREADS (including the mill Action's verification state from CH-9b3), F-COH3, F-FILL, F-CAL; the partial prepares (Kobo 7 days incl. one missing and `mill-midday`, Cold 3 days incl. one 24 h steady, EV 2 Tuesdays), wall time per Site-day and the projected B-22 sequential E3 (over 3 h → B-16 projection to the owner before E3); peak memory against the 2 GB floor; the M2 figures with the stop rule applied; scoped `tools/checks/test_chain_coherence.py`; guards A, W, N, V, M.
- **Lane-2 order note (SPLIT-1).** DD-1a1, DD-1a2 and DD-1b1 do not need CH-9b3 or CH-6a. If CH-6a3 is not on main when CH-6b0 merges, lane 2 runs them before CH-9b3; DD-1b2 always follows CH-9b3, because F-THREADS expects the mill verification.

## Scope cut (SCOPE-1)

- Architect: Claude (Architect 16), 2026-11-05. Plan row **SCOPE-1**. Owner, verbatim (`.agent/owner-scope-backlog-2026-11-05.md`): "put implemnatation that are not demo critical to a backlog, don't keep on pilling commitments", then "let architect divide the remaing work accordingly and only focus on what we should be presenting defensibily to the frist clients". Test and backlog: `.agent/backlog-post-demo.md`. This section overrides the "Build units" section and every earlier ruling where they differ; backlogged text above is history, not scope.
- **DD-1a1 (2): unchanged.** Steady scenarios and full-day story days make the build runnable and the grades honest; batching is needed for the E3 cap.
- **DD-1a2: 2 → 1.75.** Backlogged: the planned `missing` day per Site and its L0 checks (**BL-10**). Kept: the B-22 day list, `DAY_BEFORE_INSTALL`, `mill-midday` placement, FILL-1 steady kinds and the five refusals (ST-7).
- **DD-1b1: 1.5 → 1.25.** Backlogged: R9 tick output split (**BL-11**). Kept: R6, R7.
- **DD-1b2: 1.75 → 1.5.** Backlogged: M2 (**BL-12**) and the F-FILL row (BL-10). Kept: R8 drain, finish rows F-DRAIN, F-COH, F-PERF, F-THREADS, F-COH3, F-CAL, the partial prepares (Kobo 7 days including `mill-midday`, Cold 3 days with one 24 h steady, EV 2 Tuesdays), the E3 projection and the memory peak.
  - **F-THREADS addition (CH6a3-R2 H2, Architect 21, 2026-11-06; +0):** on the combined demo dataset, the Kobo and EV boards on the story days named in `build-sheet-CH-6.md` §A8 item 3 show a non-null Grow earnings figure, a SUPPORTED potential with its money line (Kobo), an MG-1 verdict from the day snapshots, and the "Why?" price line. Each figure is asserted by recomputation from the stored rows, never by a literal, and on each the ONE-SOURCE rule holds: the subline and contributor kWh equal the claim's kWh. SCOPE-1 reason: this is the only real-data, end-to-end proof of the Grow money a client sees, and it needs the full days.
- **Lane-2 order:** CH-9b3 no longer needs CH-6a3, so the conditional order is gone: CH-9b1 → CH-9b2 → CH-9b3 → DD-1a1 → DD-1a2 → DD-1b1 → DD-1b2 → CH-5d1.
- **DD-1 total: 7.25 → 6.5.**

## DD0c-R: rulings on the DD-0c probe results

- Architect: Claude (Architect 20), 2026-11-06. Binding checked (Claude, `.ai/ROLE_CONFIG.md` 2026-10-27). Input: `.agent/DD-0c-probe-results.md` (merged on main). These rulings answer P1 for DD-1a1 and override R2, R3 and SCOPE-1 where they differ. No new demo work: every item below is stated against SCOPE-1.
- **Q1, L1 batching: approved, as a host change in DD-1a1 at the existing R3 +0.25 (no size change).** The knob is in the host, not the gateway, so R3's "reviewed gateway edit" now reads "reviewed host edit".
  - The change is `RegisteredGatewayPublisher.publish_in_boundary_order` (`host/gateway_publication.py:139-149`). Add an opt-in `seal_once` keyword, default off. When it is on, each boundary group is admitted at its own instant as today, and `seal` is called once after the last group. `seal` keeps its own bounds (256 envelopes, the `_fit` byte bound), so batches stay legal.
  - Only the demo prepare and `add-day` children (`tools/demo_combined_{kobo,cold,ev}.py`, through the shared producer path) pass `seal_once=True`. The default keeps D-2026-10-09 ("every group is sealed before the next, so the batches do not depend on how the operator stepped") for every other caller. Within one prepare run, the one call is the whole run, so the batches still do not depend on stepping.
  - SCOPE-1 reason: without it B-22 does not fit the 3 h E3 cap (DD-0b: 5.9 h); with it the projection is 1.81 h central.
  - Acceptance adds: an L2 parity test on one short Cold prepare, `seal_once` on and off, compared by the Q2 parity rule below; a unit test that the default path still seals per group.
- **Q2, the three parity differences: all acceptable. None is a fix or a stop.** The rule for DD-1 parity checks from now on: compare `mini_opportunity_revision` without `selection_seq`, the verification basis without `publication_ids` and `run_id`, and assessment `links` as a multiset.
  1. **Kobo `mini_opportunity_revision.selection_seq`: acceptable.** It is an insertion ordinal of mini-depth revisions, so it follows job order. What it selects is equal: `local_day`, windows, `evidence_ids` and `mini_revision_id`. No client figure, label or claim reads the ordinal's value; the demo build is one run, so no client ever compares two builds.
  2. **Verification basis `publication_ids` 74 → 6: acceptable.** Each batch is still registered as a publication, so source resolution is unchanged, and the outcome is equal (`VERIFIED`, `TARGET_AND_GUARDRAILS_PASS`, same metrics). What a client sees: the "Publications" fact on the verification page (`SiteActionVerification.tsx:1981`) lists 6 opaque ids instead of 74. The accepted readings for each window are listed and linked to Evidence as before, so the result stays traceable. The ACT-K1 verdict and the mill verdict (CH-9b) decide on metrics, not on publication counts, so neither changes. `plan_sha256` and `run_id` differ because run ids are minted per run; that is expected.
  3. **Cold start-response link order: not a defect caused by L1, and no fix in DD-1.** The two links are CONTEXT links taken in the group's order, which is `(source_time, received_at, evidence_id)` (`B/analytics/cold.py:264`, links at `:640-641`). The replay decides every batch at one overridden `received_at`, so two events at the same `source_time` tie-break on `evidence_id`, which is minted per run. The same reorder occurs between two per-boundary runs. The order is a total order on stored data, so one build reads the same way every time, and the content is equal. A stable secondary key (record kind) would be cleanup only; it is not backlogged, because nothing shown depends on it.
- **Q3, Cold steady day as one 24 h run (R2, L2): not built. Batching only, B-22 stays.**
  - L2 needs a change to the Cold replay path (the fixed 65-min window at `tools/w502_cold_work_cases.py:49,56,144` and the producer branch at `T/test_w502_cold_scenario_producer.py:149`) plus a snapshot-grade equivalence proof. That is new code and a new proof for about 18-20 min of build margin, and no shown number needs it. It fails SCOPE-1.
  - R2 therefore takes its "otherwise" branch: `cold-steady` is a 65-min scenario derived from `cold-normal` as R2 states, and a Cold steady day is the measured shape, about 22 consecutive short runs covering the day (DD-0b §7). SCOPE-1's DD-1b2 phrase "Cold 3 days with one 24 h steady" now reads "one full steady day of short runs".
  - B-22 with L1 projects 1.81 h central and 2.46 h upper, or 2.26 h / 2.91 h with the drain add-on, all under the 3 h cap. The 2.91 h upper rests on an unmeasured 900 s tick allowance, so it is not a reason to change OD-P11 now. R1 already holds the rule: the DD-1b2 rehearsal measures the drain and re-projects E3, and B-16 (1.63-2.09 h with drain) is used only if that projection is over 3 h, with the owner told before E3. No owner question now.
- **Q4, FILL-1 for an earlier Cold day: not demo-critical. Backlogged as BL-14 (0.5 est.).**
  - The refusal is real (`gateway_credential_revocation`: the prior credential is revoked at the new day's story time, before its issue time). But with the B-22 baseline full and the planned `missing` day backlogged (BL-10), every earlier Cold day in the board window already has evidence and is refused `DAY_HAS_EVIDENCE` first. The demo has no earlier Cold day to fill; ST-7 adds the next ended day forward.
  - The owner's "fill or inject any day" is met for every day the demo can offer. Note for the script and the owner: **for Cold, only forward days can be added** until BL-14 is done.
  - No new code. DD-1a2's existing `DAY_HAS_EVIDENCE` refusal test must show the refusal is decided before Cold provisioning starts (a reading, at +0), so an earlier Cold day on the full build is refused by name, never by a database error.
- **Q5, sizes: unchanged.** DD-1a1 2 (R2 1, full-day story days 0.5, R3 host edit 0.25, L0/L2 0.25); DD-1a2 1.75; DD-1b1 1.25; DD-1b2 1.5. **DD-1 total 6.5.** No backlog size added to the plan; BL-14 is 0.5 outside it.
- **P1 answer for DD-1a1:** L1 is in the host (`gateway_publication.py:139-149`), parity accepted by Q2; Cold 24 h equivalence not proven and not pursued (Q3); projected B-22 sequential 1.81 h central / 2.46 h upper, 2.26 h / 2.91 h with drain, under 3 h, so no stop. DD-1a1 may start.

## DD1a1-R: rulings on the DD-1a1 pre-flight

- Architect: Claude (Architect 20), 2026-11-06. Pre-flight `AssetOpsV1-dd1a1\.agent\DD-1a1-preflight.md` at `b8267f01b` (branch `task/DD-1a1-steady-fullday`). P1–P6 are accepted as answered. Each question is ruled against SCOPE-1 and the owner's rule that numbers are never tuned.
- **Q1, Kobo "forcings removed": accepted.** Kobo's FORCING_INPUT entries are the healthy reference profile, not fault forcings. R2's "forcings removed" means fault forcings, and the Kobo parents have none, so `kobo-steady*` copy the parent windows verbatim and change only `scenario_id`, `display_name`, `purpose`, `label` and the source lines. This gives a real steady day: the declared normal day, repeated. Cold removes GRID_LOSS and GRID_RESTORE, as R2 states.
- **Q2, night hours (20:00–06:00 local): accepted, with a label and a stop gate.** This is the defensibility point of the unit.
  - Leaving the night undelivered is not an honest option here. The Kobo study day is the declared 24 h operating day (`mini_depth/store.py:366-396`), so an undelivered hour is a missing hour. Every Kobo day would then read partial, and MG-5 and "daytime solar unused" would stay missing: the CH9-R2 failure.
  - The 18–20 h window of `kobo-mini-grid-evening` is the only parent window without sun. Repeating it unchanged is derivation, not tuning: no value is chosen. It is a conservative night (evening-peak load), not a measured night profile, and the label must say so. The night segment's `label` reads: "example data, steady night (repeats the 18–20 h window of kobo-mini-grid-evening; no sun)". Each repeated window carries its source line, so "Why?" can name the source.
  - **Stop gate (L2, before DD-1a2 builds the B-22 list):** on the one L2 full Kobo day, report whether the night segment starts the generator, burns fuel, opens a Finding or thread, or moves any Kobo money figure. If it does any of these, stop and the Architect rules before DD-1a2. The night must not add a story the parents never declared. Values are never tuned to avoid it.
- **Q3, one steady file per complement segment: accepted.** The files are `kobo-steady-night` (00–06), `kobo-steady-afternoon` (14–24), `kobo-steady-evening` (18–24) and `kobo-steady` (00–24). Each segment starts from its parent's declared state, and state is not carried across runs. The resulting jumps in state of charge at segment edges are reported in the packet, not smoothed.
- **Q4, full days for Kobo and Cold, not EV: accepted.** Kobo has full days because CH9-R2 needs them. Cold also has full days because its declared day is 24 h, and its story days are the days the board shows; without the complement they would read partial for 23 hours. EV is unchanged: it is declared 08–16Z, and R2 has no `ev-steady`.
- **Q5, Cold hourly tiling (24 runs per steady day): accepted.** The L0 check runs on the 60-min scenario intervals. This corrects DD0c-R Q3's "about 22" to 24 runs, about +10 s per Cold day over the DD-0c projection at L1 speed; the projection stays under 3 h. The cost is reported.
- **Q6, complement delivery: accepted.** Each complement is its own run, with its own epoch and `received_at` (end + 1 h). A `late` day's complements share its lateness offset. `_trial_chain` is unchanged. The L2 check that the trial verification metrics are equal with and without the complements is required.
- **Q7, `demo-story-days-v2.json` with `complement` lists: accepted.** v1 is kept. L0 asserts that each local day's union is exactly [00:00, 24:00), with no overlap and no gap.
- **Q8, cost gate: accepted.** The extra cost per full Kobo day and per full Cold day is measured on L2 and projected against the +50% prepare budget. If it is over, it goes to the owner as a measured choice (Build units, full-day bullet).
- **Size: DD-1a1 stays 2.** Cold full days reuse the same complement mechanism and the `cold-steady` file R2 already sized. No backlog item. DD-1 stays 6.5.
- **Owner (informed, not blocking).** Kobo has no example night data, so the build repeats the parent's 18–20 h no-sun evening values through the night, labelled as such. The recommendation is to accept. The alternative, leaving nights undelivered, makes every Kobo day read partial and removes the solar-unused figure. The build proceeds on the recommendation, and the owner can override before DD-1a2.

## DD1a1-R2: the Kobo night profile (supersedes DD1a1-R Q2 and its stop gate)

- Architect: Claude (Architect 20), 2026-11-06. Owner, verbatim (`.agent/owner-kobo-nights-2026-11-06.md`): "let the architect provide one based on domain knowledge and utility to the application grounded on how actual sites operate and what makes nights interesting". DD1a1-R Q1 and Q3–Q8 stand, except where Q3's files change below.
- **Site facts the night uses** (`config/site-templates/kobo-mini-grid-60kw.yaml`; `backend/tests/fixtures/s1/kobo-001.yaml`; nothing here changes them):
  - battery 200 kWh, PCS 30 kW at 95%, reserve 30%;
  - generator 40 kW, start at 35% SoC, stop at 90%, minimum runtime 30 min, start delay 5 min, 0.3 L/kWh, tank 400 L;
  - load ratings: residential 25 kW, clinic 10 kW (the critical load), mill 40 kW.
  - Kobo runs on UTC+3 at about 9°N, with sunset about 18:30 and sunrise about 06:15. Every parent declares 0 W/m² from 18:00.
  - Every parent declares a dawn state at 06:00 between 34% and 55% SoC, with 300 L and the generator STOPPED.

### How a site like Kobo runs at night (the grounding)

- **Residential.** On rural East African mini-grids the evening peak is 18:00–22:00: lighting, TV, phone charging. Load then falls to a night base of roughly 15–25% of the peak: security and street lights, shop and household refrigeration, phones. It rises a little before dawn as people get up.
- **Clinic.** At night a health post keeps vaccine and medicine refrigeration, security and ward lighting, and on-call care. That is roughly 1.5–3 kW against a daytime 5–7 kW.
- **Mill.** It does not run at night.
- **Batteries and the generator.** On hybrid PV–battery–diesel sites the battery carries the night after a sunny day. After a cloudy day it does not: the generator starts at its SoC threshold, and a high stop threshold keeps it running long after the need has passed. Night generator hours are a site's largest fuel cost.
- These are typical-pattern bases, stated as such. They are not measurements from Kobo. The label is **"example data, night profile"**, and each value's comment states its basis below.

### The night inputs (no sun; 2 h or 1 h windows)

| Window (local) | Residential kW | Basis | Clinic kW | Basis | Mill | Irradiance |
|---|---|---|---|---|---|---|
| 20–22 | 9 | evening peak tapering, ~65% of the parent's 14 kW at 18–20 | 4 | parent's 5 kW, with evening activity ending | 0 | 0 |
| 22–24 | 5 | most homes asleep | 2 | night base: refrigeration, lights, on-call | 0 | 0 |
| 00–05 | 3 | night base, ~21% of the 14 kW peak | 2 | as above | 0 | 0 |
| 05–06 | 5 | pre-dawn rise, ending at the 06–08 daytime parent's lower values | 2 | as above | 0 | 0 |

- Energy check (stated, not tuned): 20–24 is 40 kWh, about 21% SoC through the PCS; 00–06 is 32 kWh, about 17%.

### Starting states: measured handover, never chosen

A run cannot start mid-scenario and state is not carried between runs (DD1a1-R Q3). Each night file's start state therefore comes from one measured probe run, cited in the file with the probe's run id. No value is picked to reach an outcome.
- **Probe S, the steady day:** one continuous 06:00–20:00 run of `kobo-daytime`'s windows plus `kobo-mini-grid-evening`'s 18–20 window. It starts from `kobo-daytime`'s declared 55%, 300 L and STOPPED.
  - Its SoC, fuel and generator state at 20:00 (SoC rounded to a whole %) become `kobo-night-late`'s start.
  - `kobo-night-late`'s measured end becomes `kobo-night-early`'s start.
  - The estimate is about 68% at 20:00 and about 41% at 06:00. The battery carries the night with a small margin and the generator does not start. That is what a sunny day buys at this site.
- **Probe O, after the overcast story day:** the same method on the overcast story run's windows (`kobo-s3-dispatch-necessary-run`, its declared start) plus the steady 14–20 windows. This gives `kobo-night-late-after-overcast` and `kobo-night-early-after-overcast`.
  - The physics decides what happens. The expected result is a battery near the 35% start threshold early in the night, then the generator requested and held by the 90% stop: a night generator run with real runtime and fuel. Nothing declares generator output.
- **Run-boundary limitation (stated, not hidden).** A generator cannot be declared RUNNING at run start (setup refuses it). If it is running at 24:00, the 00:00 run starts STOPPED and restarts it after its 5-min start delay; the battery serves first. The packet reports this, and the night's "Why?" source line names the boundary.

### Shape, files and kinds

- **Steady night, every Kobo night unless placed otherwise:** `config/scenarios/kobo-night-late.yaml` (20–24) and `kobo-night-early.yaml` (00–06).
- **One story night, declared by cause, not by result:** the night after the `overcast` story day uses `kobo-night-late-after-overcast.yaml` and, on the next local day, `kobo-night-early-after-overcast.yaml`. "Some nights, not all" follows from the weather the day list already declares. No second story night (SCOPE-1).
- **Q3's files change:**
  - `kobo-steady-night` (repeated evening) is withdrawn; `kobo-night-early` replaces it.
  - The afternoon complement becomes `kobo-steady-afternoon` (14–20, the evening parent's windows verbatim) plus `kobo-night-late`.
  - `mill-midday`'s complement becomes `kobo-steady-dusk` (18–20) plus `kobo-night-late`.
  - A pure steady day (DD-1a2) is the run set `kobo-night-early`, `kobo-steady-day` (06–18, `kobo-daytime` verbatim, the scenario Q1 already defines), `kobo-steady-dusk` and `kobo-night-late`. There is no single 00–24 file.
- Each night file carries `label: "example data, night profile"`, the basis comment per value, and the probe run id for its start state.

### What the nights do for the demo (utility), and what they must not do

- **Critical supply served (MG-5) becomes a true 24 h claim.** The clinic is supplied through the night from the battery, every hour delivered and graded. Without nights it is a daytime-only claim on a 24 h declared day.
- **Spare solar ("daytime solar unused") and the daylight read.** Night hours are covered with `pv_available_power` = 0, so they are counted as not daylight and the day grades COMPLETE (`mini_depth/store.py:366-396`). Daylight hours are measured, not assumed.
- **Cost.** The after-overcast night is an asset to the story: a night generator run with hours and litres, caused by a cloudy day and held by the 90% stop policy. That is the mechanism ACT-K1's reserve change acts on, shown at night. The overcast day sits early in the list (v1: S−21d), before the trial, so its night adds evidence to the problem ACT-K1 addresses and cannot read as a recurrence after verification.
- **Grow (mill).** Neutral and unmuddied. The mill verification and the spare-solar study read daylight hours only, and the night start states are fixed, so a night is identical before and after the mill change.
- **Must not (gate, measured on L2 in DD-1a1 for the steady night and in DD-1a2 for the after-overcast night).** Report generator starts, runtime, fuel, Findings, threads and money per night.
  - The steady night must start no generator.
  - The after-overcast night may open Cost evidence only before ACT-K1's trial-before day.
  - Neither may change the ACT-K1 verification metrics, the mill verification or the spare-solar study (compare with the night runs and without them, as Q6).
  - If the steady night fails its gate, stop and the Architect rules. If the after-overcast night fails, it falls back to the steady night files, so the demo presents less. No value is ever adjusted to pass.

### Units and size

- **DD-1a1 2 → 2.5 (+0.5):** the four night files with their bases; probes S and O; the withdrawn and renamed Q3 files; the steady-night gate on L2.
  - SCOPE-1 reason: MG-5's "critical supply served" and the COMPLETE daylight read are untrue or partial on a 24 h declared day without delivered nights, and the owner directed a grounded night (above).
- **DD-1a2 1.75 → 2.0 (+0.25):** placing the after-overcast night pair after the `overcast` day, before trial-before, as complement data, with its gate.
  - SCOPE-1 reason: the only night generator cost shown must have a stated cause and must not land after the ACT-K1 verification.
- **DD-1 total 6.5 → 7.25.** Lane 2 +0.75; the plan's lane-2 totals need it.

## DD1a1-R3: the steady-night gate result, and the Kobo initial values

- Architect: Claude (Architect 22), 2026-11-06. Binding checked (Claude, `.ai/ROLE_CONFIG.md` 2026-10-27). Input: `AssetOpsV1-dd1a1\.agent\DD-1a1-handoff.md` at `02b2336dd` and `backend/conversions/kobo-night-handover-v1.json` (branch `task/DD-1a1-steady-fullday`). Owner rule: numbers are never tuned. DD1a1-R2 stands except where this section differs.

### Q1, the steady night requests the generator at 05:00: (a) accept the physics, with a disclosure and named checks

- **The error is R2's, not the loads'.** R2's own energy check gives 69 − 21 − 17 ≈ 31 % at 06:00; "about 41 %" was an arithmetic slip. The probe measured 47.95 % at 24:00 and 31.16 % at 06:00, which is exactly the check.
- **(b) is not available.** Each night value matches its stated basis: residential 3 kW is 21 % of the 14 kW peak (the basis says 15–25 %); clinic 2 kW is inside 1.5–3 kW; 00–06 is 32 kWh, or 16.8 % through the 95 % PCS. No basis was wrong on its own terms, so no value changes.
- **(a) is the honest reading.** The declared sunny day (`kobo-daytime`, 55 % → 69 %) does not put back what a grounded night takes out (69 % → 31 %). A site like this crosses its 35 % start threshold shortly before dawn and the Site policy starts the generator. That is common on village hybrid mini-grids, and it is a property of the declared site and its loads, not a story added by the night.
- **The 0.0 L in 55 min RUNNING is not a code defect.** It is the specified model (`simulator/assetops_simulator/packs/mini_grid.py:14-27`, dispatch `:571-596`, delivery `:678-736`):
  - Kobo's declared source order is PV, battery, generator. Between the 35 % start and the 30 % reserve, the battery still serves the whole load.
  - A running generator charges only while the battery is not discharging, so it delivers 0 kW.
  - The fuel law is linear on accepted energy with no idle fuel. The step notes disclose this.
  - The same zero-output band already occurs inside the overcast runs (probe O and the shipped `kobo-s3-dispatch-necessary-run`). Fuel is understated there too, but not to a visibly false zero.
  - **However, "ran 55 min, used 0 L" on every steady day cannot hold up under questioning**: a real set idling for an hour burns a few litres. No simulator change in DD-1, because it would re-baseline every Kobo day and choose an idle-fuel value no Site fact states. The fix is backlogged as **BL-16**. The disclosure below is required instead.
- **Disclosure (required, +0).** Each steady night file's label and the 04–06 source line read, in plain words: "Example data, night profile. At about 05:00 the battery reaches the 35 % generator start level and the site starts the generator. The battery is still above its reserve and serves first, so the generator delivers almost no energy before 06:00. Fuel is counted per kWh delivered; idle fuel is not modelled, so this hour shows no fuel." The packet quotes the "Why?" line where it appears.
- **The steady-night gate is replaced by these checks.** Each is measured on L2 on the registered Kobo Site, comparing runs with and without the night runs as in Q6:
  1. **Night shape.** At most one generator start per steady night, and only by the Site policy at the start threshold from 04:00. Fuel is 0.0 L. Unserved load is 0 in every night hour, which is MG-5's critical supply.
  2. **"Generator time beyond need" (MG-2) and ACT-K1.** Every steady-night generator minute is classified as needed, through `MINIMUM_RUNTIME` then `BATTERY_NEAR_RESERVE` (`B/analytics/dispatch.py:493-508`). There are no Candidate or Cannot-determine minutes, so `avoidable_generator_minutes` is equal with and without nights on the trial-before and trial-after days. The steady-night trajectory is identical before and after the reserve change (its lowest SoC, 31.16 %, is above both 30 % and 25 %). The ACT-K1 verification outcome and metrics are equal.
  3. **Mill verdict and spare solar.** The mill verification metrics and the spare-solar study are equal with and without nights. Each full day grades COMPLETE, and daylight hours exclude 20:00–06:00.
  4. **Findings, threads and money.** A steady night adds no Finding, no thread event and no change to any Kobo money figure.
  5. **The 06:00 seam.** The night ends at 31 % with the generator RUNNING, and the steady day starts from its declared 55 % with the generator STOPPED. The packet reports this as a seam (DD1a1-R Q3), and the night's source line names the boundary (R2).
  - If any check fails: **stop, and the Architect rules.** No value is adjusted to pass.
- **Assets for the stories.** MG-5 gains a true 24 h clinic claim. The pre-dawn start is neutral for MG-2: it is needed, so ACT-K1 is untouched. The after-overcast nights (O-late 235 min / 13.07 L, O-early 355 min / 10.51 L) remain the Cost story, and DD-1a2 keeps their gate unchanged.

### Q2, initial values on mini-grid v6

- **Cause.** `kobo-daytime` is written for the `daytime-mini-grid` profile, which has no generator or tank (`config/scenarios/kobo-daytime.yaml:4`), so it declares only SoC. On mini-grid v6 a derived file must declare the generator and tank start states.
- **Honest declaration.** `kobo-steady-day` and probe S's document add `starting-fuel` 300 L and `starting-generator-state` STOPPED as public parameters. Each carries a source comment: "not declared by kobo-daytime (daytime-mini-grid profile, no generator); the dawn state every mini-grid Kobo parent declares (cite file:line each); STOPPED is the only state setup accepts at run start". These values are uniform across the parents and are not chosen for an outcome. The steady day must still show 0 generator starts.
- **`kobo-daytime` itself is not edited**, because it is a shipped parent used by CH-9b.
- **The builder verifies, before the v2 day list:**
  - Draft every Kobo scenario in the v2 list on the **registered** demo Kobo Site, with the profile and version the prepare uses. That covers `kobo-steady-day`, `-afternoon`, `-dusk`, both steady nights, both after-overcast nights, and `mill-midday` (`kobo-daytime` v2). Report READY or BLOCKED for each, with its reason.
  - Report which profile the prepare actually runs `mill-midday` on (`tools/demo_combined_kobo.py`, `M["model_profile"]`). If `mill-midday` is BLOCKED on that profile, or its profile differs from the complement runs on the same day, stop and the Architect rules.
  - **Re-run probes S and O on the registered Site**, or show that its frozen policy facts equal the template's: reserve, start and stop thresholds, minimum runtime, start delay, specific fuel consumption, source order, PCS and capacity. The reserve is the load-bearing one, because MD-0 phase 3 recorded a reserve of 20. In the handover JSON, record the Site id and fill `scenario_sha256`.

### Size

- **DD-1a1 2.5 → 2.75 (+0.25)**, for the registered-Site drafts and re-probe, the declared initial values, and the five replacement checks. The disclosure costs +0.
  - SCOPE-1 reason: without the checks, the MG-2, ACT-K1 and mill figures on every Kobo day are not shown to be unchanged by the night. Without the registered-Site probe, the night states may not be the demo Site's.
- **DD-1 7.25 → 7.5.** Lane 2 +0.25; the plan rows need it.
- **BL-16 (backlog, 1.0 est.).** Idle and start fuel in the mini-grid fuel law. This needs a stated Site fact for idle consumption and a re-baseline of the Kobo days.

### Owner (informed; the build proceeds on the recommendation)

- Question: "On a normal sunny day Kobo's battery runs down to the generator start level about an hour before dawn, so the generator switches on around 05:00 and delivers almost nothing before sunrise (idle fuel isn't modelled, which the screen says). Is that OK to show?"
- Recommendation: yes. It is how many village mini-grids actually run, and it changes no story figure. The only alternative is a different night load, and that would have to come from the owner as data, not from an agent.

## DD1a1-R4: `mill-midday` is BLOCKED on mini-grid v6

- Architect: Claude (Architect 22), 2026-11-06. Input: `AssetOpsV1-dd1a1\.agent\DD-1a1-handoff.md` at `04473dc5d`. `mill-midday` (`kobo-daytime@2`) is BLOCKED with `INITIAL_VALUE_NOT_RESOLVED` for fuel and generator state. Every other Kobo kind and file is READY on the registered KOBO-001. The reserve is 30, and the probes reproduce there.
- **Ruling: use a derived `kobo-mill-midday`, as the coordinator proposed.**
  - Generate it with `tools/derive_steady_scenarios.py` and include it in `--check`.
  - Copy `kobo-daytime@2`'s windows and SoC verbatim. Declare `starting-fuel` 300 L and `starting-generator-state` STOPPED, with R3 Q2's source line.
  - The label reads "derived from kobo-daytime v2, the mill story day", and each window keeps its `# source:` line.
  - Point the `mill-midday` kind at it in v2 only. v1 is kept as history. `kobo-daytime` is not edited.
- **Rejected: a manifest override running the kind on `daytime-mini-grid`.** That profile has no generator, so one Kobo day would mix two models. The registered Site's generator would vanish from its own day, and the mill day's dispatch figures could not be compared with the days around it.
- **Rejected: pointing the kind at `kobo-steady-day`.** It has the same windows, but its "steady day" label would misdescribe the mill story day, and its "Why?" source would not name the mill day.
- **Checks (L0/L2):**
  - The derived file's windows and SoC equal `kobo-daytime@2`'s.
  - It drafts READY on KOBO-001 under the prepare's manifest.
  - On the L2 mill day: 0 generator starts, so 300 L and STOPPED decide nothing.
  - The CH-9b mill verification outcome and metrics are as CH-9b recorded.
  - Any CH-9b test or fixture that names `kobo-daytime` for the mill kind is listed in the packet. It is either updated to the derived id or shown to read only v1.
  - If any check fails: stop, and the Architect rules.
- **Size: +0.** It uses the same mechanism and checks as R3 Q2's `kobo-steady-day`, inside R3's +0.25. DD-1a1 stays 2.75 and DD-1 stays 7.5.

## DD1a1-R5: complements make every full day cohort AMBIGUOUS (amends Q6)

- Architect: Claude (Architect 22), 2026-11-06. Input: `AssetOpsV1-dd1a1\.agent\DD-1a1-trial-anchor-diagnosis.md` at `64856f4be`.
  - Q6 gave each complement its own epoch. Adjacent segments then share an edge sample, and both `_clashing` (closed `_overlaps`, `cohort.py:58`) and `_multi_epoch` (`cohort.py:95-114`) fire.
  - Every full-day dispatch window comes out AMBIGUOUS, so the "with" build has 0 Findings against 3 without, and no trial anchor.
  - The cohort guard is right: central evidence cannot attest that two epochs are one stream. The defect is Q6's epoch shape.
- **Ruling: option (a). One sequence epoch per Site-day stream, with the sequence continuing across that day's runs and each instant emitted once.**
  - **Why (a) is the honest shape.** A real gateway changes its sequence epoch only on a reset. A fresh epoch every few hours would claim resets that never happened. One local day of one Site is one stream.
  - **The edge rule.** A story run is emitted unchanged, byte-equal to the "without" build. A complement leaves out any sample at an instant a story run already emits. Between two complements, the earlier one ends exclusive.
  - **Day edges.** Adjacent Site-days keep separate epochs, as v1 already does (`day-<n>` per day), and the shared 21:00Z instant goes to the later day. A neighbour epoch seen only in the bracket is not a candidate (`cohort.py`, `select_cohort`), so it does not make a window ambiguous.
  - **Cold has the same shape and the same rule.** There are 24 hourly runs per day, and `cold-steady` is 65 min while `covers_end` is start + 60. Each Cold complement is emitted on [start, covers_end) and starts after any story run's emitted end. Cold story runs are never trimmed.
  - Q6 otherwise stands: each complement remains its own run with its own `received_at`.
- **Rejected options.**
  - (b) would assert "one stream" by an operator act that cohort-4 says evidence cannot attest. That is an architecture change.
  - (c) leaves the Finding and trial days partial, contrary to CH9-R4. Presenting less is preferred only when it is honest, and a partial story day is not.
  - (d) changes rule cohort-4 and is out of scope.
- **Probe first (L2, own `*_test` DB, before the change is built out).** On one Kobo Site-day, test that the gateway accepts the following:
  - One epoch whose sequence continues across separately sealed runs.
  - A complement received after a later-sequence run. The trial-day complements are delivered after the trial chain, so this case is real.
  - A `late` day's offset.
  - If the gateway refuses any of these, stop and the Architect rules. Do not fall back to (b) or (c) without a ruling.
- **Acceptance.**
  - The "with" build has the same 3 Findings as "without" (10-21, 10-28, 11-04, at 04:35, `GENERATOR_SUPPORT_CANDIDATE`), with the same CANDIDATE intervals and citations.
  - `cohort_status` shows 0 AMBIGUOUS on full days, for Kobo and Cold.
  - Q6 holds: the trial verification outcome and metrics are equal with and without complements.
  - L0 on the v2 list:
    - Each Site-day has one epoch per source.
    - Each instant is emitted at most once per stream.
    - Story-run payloads are equal to v1's.
  - The R3 and R4 checks are unchanged. No value is tuned.
- **Size: DD-1a1 2.75 → 3.25 (+0.5)**, for the shared epoch and the continued sequence in `tools/demo_story_days.py` and the producers, the edge rule for Kobo and Cold, the gateway probe, and the acceptance above.
  - SCOPE-1 reason: without it, the full-day build has no Kobo Finding, no ACT-K1 trial anchor and no Cold assessment basis, so the board story cannot be shown.
- **DD-1 7.5 → 8.0.** Lane 2 +0.5; the plan rows need it. No owner question: this is a build-shape fix that changes no shown story.

## DD1a1-R6: on the Kobo `degraded` day, the outage lasts the rest of the local day

- Architect: Claude (Architect 23), 2026-11-06. Binding checked: Claude in the lane worktrees' `.ai/ROLE_CONFIG.md` (owner, 2026-10-27). The primary checkout's copy is older and still reads Codex. Input: `AssetOpsV1-dd1a1\.agent\DD-1a1-handoff.md` at `cb2204416`, "Kobo producer" deviation; `tools/demo_combined_kobo.py` `publish_first_half`/`run_day`/`_OUTAGE`; `backend/conversions/demo-story-days-v2.json`.
- **Ruling: accepted. After the outage, complements on that Site-day deliver nothing. The reset-epoch alternative is rejected.**
  - **What the day must show.** The day's story is an evidence gap: the gateway stopped part way through the 06:00–14:00 local run. A real gateway that stays down sends nothing more, so no later reading that day may arrive. The night before the outage is still present: `night-early` is received at 04:00Z, before the story run's 12:00Z. The client sees readings up to the outage point and "not received" from then to 24:00 local. That is a true gap, not a gap filled with partial data.
  - **No false filling.** On R5's one gateway state, any post-outage delivery would first flush the withheld half from the outbox. That would make the gap disappear and contradict the kind's note that the rest is never delivered (append-only). The builder's rule is the only shape that keeps the gap on one stream.
  - **Grading.** The day grades as v1's degraded day: the story run's assessment, its incomplete-evidence reason and the absence of a Finding are unchanged. The post-outage hours add no evidence, so "with" equals "without" for that day after the outage. The day stays one epoch, so it is not AMBIGUOUS.
  - **Why the reset epoch is rejected.** It claims a gateway reset that the story does not contain. R5 rejected invented resets. It also makes the day AMBIGUOUS, which would hide the gap behind a cohort refusal instead of showing it.
  - **The next day is unaffected.** Each Site-day has its own gateway state (`gw-<epoch>`), so the withheld batches are never delivered on a later day either. This matches "never delivered".
- **Scope note.** The v2 Kobo calendar has no `degraded` day, so `_OUTAGE` does not fire in the full-day build. `degraded` is an `add-day` kind only, and `add_day` runs the story run alone on a fresh gateway dir with no complements. The rule is still kept for any calendar or test that lists the day.
- **Required.**
  - `_OUTAGE` is cleared at the start of each `build`, so a later build in the same process does not inherit an outage.
  - The kind's `note` adds: "the gateway stays down for the rest of the local day; later hours are not received". Each post-outage complement's packet line says it was staged and not delivered.
- **The check the builder must run (L2, own `*_test` DB; L0 where it can).** Use a test calendar holding one Kobo `degraded` day with its three complements, built through `run_day`. Assert:
  1. `night-early` is delivered in full.
  2. The story run delivers exactly `len(batches)//2` batches, equal to the v1 degraded delivery.
  3. `steady-afternoon` and `night-late` deliver 0 batches.
  4. S2 holds no reading for that day after the last delivered story sample. Every row is checked by source time.
  5. The gateway outbox still holds the withheld and complement batches at the end.
  6. The next Site-day's gateway delivers none of them.
  7. The day is one epoch with 0 AMBIGUOUS, and its assessment and Findings equal the v1 degraded day.
  - If any assertion fails, stop and the Architect rules.
- **Size: +0.** The mechanism is already built. The check is one L2 case inside R5's probe and acceptance. DD-1a1 stays 3.25 and DD-1 stays 8.0. No owner question: no shown story changes.

## DD1a1-R7: split the trial-after night at the reserve change's instant

- Architect: Claude (Architect 23), 2026-11-06. Input: `AssetOpsV1-dd1a1\.agent\DD-1a1-handoff.md` at `4e2eed8db`.
  - The `with` build refuses `trial-after`'s `night-early` complement on 2026-11-05, which runs [21:00Z, 03:00Z): "Foundation v16 is valid until 2026-11-05T00:00:00Z".
  - ACT-K1's `effective_from` is `S+1d 00:00` (`demo-combined-story-v1.json:15`), which is 03:00 local, in the middle of that night.
- **Ruling: split the night run at 00:00Z into two complements on the same Site-day stream.**
  - **Part A** is `night-early` on [21:00Z, 00:00Z), ending exclusive. It cites v16 and reserve 30 %.
  - **Part B** is a derived `kobo-night-early-from-0300` on [00:00Z, 03:00Z). It cites v17 and reserve 25 %. It follows R5's edge rule, so it sends nothing at the trial run's 03:00Z start.
  - **Why the split is honest.** A configuration change takes effect at one instant, so the readings before 00:00Z were made under v16 and those after under v17. Two runs, each citing the basis that was valid for it, state exactly that. The refusal is correct: one run cannot claim one basis across a change. A run is a simulation session, not a gateway event, so splitting it claims no gateway reset.
  - **R5 holds.** Both parts take the S+1d Site-day's one epoch (`day-<n>`) and its one gateway state (`gw-<epoch>`). The sequence continues from A into B. Each instant is sent once: A's end is exclusive and 00:00Z belongs to B. This is R5's own case of several runs on one stream, with one more complement.
  - **Part B's start state is measured, not chosen** (R2, Q3: no state is carried between runs).
    - Generate it with `tools/derive_steady_scenarios.py`.
    - It copies `kobo-night-early`'s windows from 03:00 local verbatim: 03–04 is the second hour of the 02–04 window, then 04–05 and 05–06. Each keeps its `# source:` line.
    - Its SoC, fuel and generator state come from one probe run of Part A, measured at 00:00Z under v16. The file cites the probe's run id. It goes into `--check`.
    - The label reads: "Kobo night 03:00–06:00, after the reserve change took effect at 03:00; start state measured at that instant".
  - The physics decides what the 25 % reserve does to the night, including the R3 05:00 generator start. Nothing is tuned.
- **Rejected options.**
  - **Starting trial-after's night at 00:00Z and placing local 00:00–03:00 elsewhere.** Those hours belong to the S+1d local day (R5's day edges). Moving them to another day or stream breaks the day's coverage or invents a second epoch.
  - **Moving the revision boundary.** It changes ACT-K1's recorded `effective_from`, and with it the applied basis, the frozen plan and the verified trial. The coordinator's condition was that ACT-K1 stays unchanged. Moving it to fit a data seam would also be tuning.
- **Generalising rule.** Any complement whose interval crosses a foundation revision's `valid_until` is split at that instant, using this same method. `resolve` detects the crossing and does not hard-code a date. Today this is the only case.
- **The check (L0, then L2 on its own `*_test` DB).**
  - **L0.**
    - The v2 calendar still sends each instant once, with one epoch per Site-day.
    - Part A ends exclusive at 00:00Z, and B starts at 00:00Z and ends before the trial run's 03:00Z.
    - Part B's windows equal `kobo-night-early`'s from 03:00 local.
  - **L2.**
    1. Part A drafts READY on v16 and Part B on v17, and the `with` build completes.
    2. Part B's first sample equals Part A's state at 00:00Z: no SoC, fuel or generator-state jump. The cited probe run reproduces it.
    3. Both parts are on one epoch, and the sequence runs 1..N with no gap across them.
    4. ACT-K1 is unchanged with and without the complements: the accept, apply, `effective_from`, plan windows, VERIFIED outcome and metrics are equal (Q6).
    5. R5's acceptance holds: the same 3 Findings and 0 AMBIGUOUS.
  - Stop and the Architect rules if any of these happens:
    - Part A's 3 h interval is refused;
    - Part B does not draft READY;
    - a seam jump appears;
    - ACT-K1 differs.
- **Size: +0.25** for the derived file and its probe, the split in `resolve` and the calendar, and the checks. DD-1a1 3.25 → 3.5 and DD-1 8.0 → 8.25; the plan rows need it. SCOPE-1 reason: without it the `with` build cannot finish, so the trial day is partial. No owner question: no shown story changes.
- **DD1a1-R7a** (Architect 23, 2026-11-06): confirmed. Part A becomes a derived `kobo-night-early-until-0300` with the same start state and source lines as `kobo-night-early`. Its windows are 00–02 local verbatim, and 02–03, which is the first hour of the 02–04 window. It carries the label "Kobo night 00:00–03:00, before the reserve change". It goes into `--check`, and the L0 check adds that its windows equal the parent's first 3 h. Part B's start state is measured from a probe of this file at 03:00 local, which must equal `kobo-night-early`'s state at that instant under v16. R7's checks are otherwise unchanged. Size stays +0.25, since it is the same mechanism as Part B.
- **DD1a1-R7b** (Architect 23, 2026-11-06; input handoff at `e29a99981`, `REGISTERED_BASIS_BOUNDARY` at `runs/registered_basis.py:88`). **Ruling: option (1). Part A ends at 23:55Z, one 5-min step before the change. The 00:00Z reading belongs to Part B and cites v17.**
  - **Why.** v17 takes effect at 00:00Z, so a reading stamped at that instant was made under the new setting. The end-stamp rule exists to stop exactly that reading being cited under v16.
  - **Option (2) rejected.** Allowing end == `valid_until` is a product change that would let one wrongly cited reading through.
  - **Option (3) rejected.** No other cut is honest: the change's instant fixes the cut.
  - **The 23:55–00:00 interval needs no home.** Every Kobo publication cadence is 5 or 15 min. On those grids no instant lies strictly between 23:55Z (Part A's last stamp) and 00:00Z (Part B's first), so no reading is lost. The physics of those 5 min stays in the measurement: Part B's start state is still the R7a probe's state at 00:00Z, unchanged.
  - **Build.**
    - Part A runs on a derived `kobo-night-early-until-0255`: R7a's file, with its last window trimmed to 02:00–02:55 local (175 min). The start state and source lines are the same, and the label adds "ends 5 minutes before the reserve change".
    - R7a's 180-min file stays as the probe that measures Part B's start state.
  - **Added checks.**
    - **L0.** Part A's windows equal the parent's first 175 min.
    - **L2.**
      - Part A's state at 23:55Z equals the probe's.
      - For each signal, A's source times plus B's equal the unsplit night's grid on [21:00Z, 03:00Z): none missing, none extra, and no off-grid end stamp.
      - No reading at or after 00:00Z cites v16, and none before 00:00Z cites v17.
    - The rest of R7 is unchanged, including ACT-K1 equal with and without.
  - **Size +0.** It is the same derivation mechanism, inside R7's +0.25. DD-1a1 stays 3.5.

## DD1a1-R8: one epoch per unbroken Site stream, not per Site-day (amends R5 "Day edges")

- Architect: Claude (Architect 23), 2026-11-06. Input: `AssetOpsV1-dd1a1\.agent\DD-1a1-1104-finding-diagnosis.md` at `ab253c74a`. The diagnosis is accepted.
  - Dispatch windows are UTC days (`dispatch_read.py:80-82`). At UTC+3, the next local day's 00:00–03:00 lies inside the current UTC window.
  - So R5's per-Site-day epoch puts two epochs in one window, and `_multi_epoch` correctly makes it AMBIGUOUS. This happens on 11-04, where it turns the Finding UNCONFIRMED NO_INTERVAL, and silently on 11-03.
  - R5's premise that the local day is the analytic window was wrong. The cohort rule is right.
- **Ruling: option 1.** Each maximal run of consecutive built Site-days of one Site is one stream: one `sequence_epoch` and one gateway state (`gw-<epoch>`), with the sequence continuing across local and UTC midnight.
  - The epoch changes only across a day with no run. That is a real gap and a plausible reset: 10-25 and 11-02 today.
  - Isolated days keep their v1 `day-<n>` epoch. A merged stream takes the epoch of its first day.
  - **Why it is honest.** This is R5's own reason: a real gateway changes epoch only on a reset, and it does not reset at local midnight. It is also the least invasive option: it changes no product code and no cohort rule, and every day stays full.
- **Rejected options.**
  - (2) is an analytics calendar change, out of scope.
  - (3) leaves partial days, contrary to CH9-R4, as R5 (c) did.
  - (4) is R5 (b), already rejected.
- **Guards. Neither case is in the v2 calendar; if a build would hit one, stop and the Architect rules.**
  - A `late` day must not sit in a multi-day stream. One stream cannot deliver an earlier day after its neighbour without a backlog claim. 11-01 is isolated.
  - A `degraded` day (R6) must not have a built day after it in its stream. The shared outbox would flush the withheld half. Starting a new epoch the next day would put two epochs in the degraded day's UTC window.
- **Trial chain.** The baseline and later runs take the stream's epoch and gateway state, not `k["runs"][...]["sequence_epoch"]`. ACT-K1 is otherwise unchanged.
- **The v1-equality check now reads:** "story-run payloads are equal to v1's in every field except `sequence_epoch` and the sequence numbers. Each isolated day's epoch equals its v1 `day-<n>`."
  - The `without` build uses the same stream epochs, so story-run payloads stay byte-equal between `with` and `without`.
  - The 2–4 revision counts may differ between the builds. Same-epoch BASIS_REFRESHED revisions are bookkeeping. Each Finding's final state must be equal.
- **L0 (`test_demo_story_days.py`).**
  - There is one epoch per maximal run of consecutive built days, per Site and source.
  - Each instant is sent once per stream, and each sequence increases monotonically across day edges.
  - A non-vacuity mutation is caught: a per-day epoch on 11-04 and 11-05.
- **Probe (L2, own `*_test` DB, before the full build).** On KOBO-001, three consecutive Site-days go on one epoch through one gateway state.
  - Every delivery is COMPLETED, with 0 duplicates, 0 rejected and 0 conflicts. Each sequence runs 1..N with no gap across both midnights.
  - A complement received after the next day's run is accepted.
  - An isolated `late` day on its own epoch is accepted.
  - `cohort_status` is SELECTED_UNIQUE in all three UTC windows.
  - If the gateway refuses any of these, stop.
- **Acceptance (full `with` and `without` builds).**
  - The same 3 Findings at 04:35 (10-21, 10-28, 11-04), with equal CANDIDATE intervals, citations and final lifecycle. The 11-04 Finding is not UNCONFIRMED.
  - 0 AMBIGUOUS in every built UTC window for Kobo and Cold, 11-03 included.
  - Q6 trial metrics are equal, and the R6, R7 and R7b checks are unchanged.
- **Size: +0.25** for the stream grouping in `resolve`, the gateway state per stream, the trial-chain epoch, the guards, the L0 updates and the probe. DD-1a1 3.5 → 3.75 and DD-1 8.25 → 8.5; the plan rows need it. No owner question: no shown story changes. Context note: this Architect is still fit for the next lane-2 ruling.

**Coordinator note (2026-11-06, from CH-6a3 M-R1):** DD-1b2 F-THREADS also asserts Kobo MG-2 (Cost) on the combined dataset: a MISSED/MET verdict and the "{lo}–{hi} L × {price} {cur}/L" line reproducing its figure (or the Known-Deviation omission when no fuel price is stored). On `mechanism_db()` MG-2 is NOT_JUDGED because no Performance comparison report exists there. +0.

## DD1a1-R9: the frozen baseline and continuous data; a baseline "move" is a change of the baseline facts

- Architect: Claude (Architect 23), 2026-11-06. Input: `AssetOpsV1-dd1a1\.agent\DD-1a1-handoff.md` at `7861ab03b`. The evidence: `actions/verification.py:486-509` (`_day_states`: "moved" = a different selected run id) and `:647`; `analytics/assessment_inputs.py:32` (`BRACKET` = 6 h); `assessment_worker.py:70-78`.
- **What happens, and why it is honest data.** A UTC-day window is read with a 6 h continuity bracket. The later run's readings at 11-05 03:00–06:00Z are in the 11-04 window's bracket. On one stream they are rightly in its read, so the 11-04 window is re-run and re-selected (seq 23).
  - On a real continuous Site this always happens. The baseline day's selection keeps moving until its own afternoon, its night and the next 6 h have been delivered.
  - On R5's separate epochs the bracket stream was not a candidate, so this never showed. The masking, not R8, was the false shape.
- **Answer 1: may a closed window's selection change?** Yes, until window end plus `BRACKET` has been delivered. After that only late or restated data moves it. Re-selection is the product working, not a fault.
- **Answer 2: what freeze point would a real verification use?** It freezes before the change takes effect: here 11-04 15:00, after the 14:00 apply and before 00:00Z. ACT-K1 does this, and it stays.
  - For ACT-K1, the baseline day can settle only at 11-05 06:00Z or later. That is inside the later window, which starts at 03:00Z. So no freeze point is both settled and prospective.
  - Freezing after the later data arrives would mean fixing the plan after seeing the result. That is not defensible to a client and is **rejected**.
  - **Rejected: giving the later run its own epoch.** It invents a reset (R5, R8) and only re-masks the issue.
- **The defect is in the product guard, not the data.** `_day_states` treats any change of selected run id as BASELINE_SELECTION_CHANGED. The guard's purpose is to catch a restated baseline, meaning baseline facts that changed after the freeze. A re-run whose facts over the baseline window are identical is not a restatement. Blocking on it would block every real Site with continuous data whose trial windows are adjacent.
- **Ruling: a product fix (least invasive), plus an honest build order.**
  1. **Product (`actions/verification.py`, `_day_states` and the port it reads).** For a baseline pin, `moved` holds only when the current selection's assessments that the verification reads over [baseline_start, baseline_end) differ from the pinned run's: the same keys, values, intervals and statuses.
     - A run-id change with equal facts is recorded in the day state as `reselected` (pinned run, current run) and does not block. The evaluation's details list it, so a reader can see it.
     - Facts that differ still give BASELINE_SELECTION_CHANGED.
     - The later pins keep their current rule ("append a new later selection binding").
     - No cohort, bracket or window rule changes. **Pre-flight:** the builder confirms that the store can read the pinned run's and the current run's baseline-window assessments. If it cannot without a schema change, stop and the Architect rules.
  2. **Build order.** The trial chain is no longer atomic. Every complement is admitted at its `received_at`, interleaved with the chain steps: 11-04 freeze 15:00, afternoon 18:00, night-late 22:00, Part A 01:00, Part B 04:00, later 12:00, evaluate 13:00.
     - Today the 11-04 and 11-05 complements are admitted after the evaluation. The evaluation then reads a state of the data that never existed.
  3. ACT-K1 is unchanged: accept, apply, `effective_from`, `freeze_at`, windows and values. Nothing is tuned.
- **Checks.**
  - **Unit (backend, with the product fix).**
    - A pinned and current run with equal baseline facts and different ids is not moved, and is listed as `reselected`.
    - One differing assessment value or interval in the baseline window is moved and gives BASELINE_SELECTION_CHANGED. This is the non-vacuity case.
    - An assessment outside [baseline_start, baseline_end) does not count.
    - The existing verification tests pass unchanged.
  - **L2 (own `*_test` DB, the R8 probe, then the full `with`/`without` builds).**
    - The interleaved order is used.
    - Every post-freeze re-selection of 11-04 is recorded as `reselected` with equal facts.
    - ACT-K1 is VERIFIED, with outcome and metrics equal with and without (Q6).
    - R8's acceptance holds.
    - If any re-selection changes the baseline facts, that is a real restatement: stop and the Architect rules.
- **Size: +0.75.** The product guard and its unit tests are 0.5. The interleaved build order and the L2 checks are 0.25. DD-1a1 3.75 → 4.5 and DD-1 8.5 → 9.25; the plan rows need it.
  - The product change gets its own reviewer pass inside DD-1a1's review, on the verification diff.
  - SCOPE-1 reason: without it, ACT-K1 cannot show VERIFIED on full days, and the Protect/Optimize board line loses its proof.
- **Owner, informed, not blocking.** Verification now blocks only when the baseline facts change, not when the internal run identity changes. This was found by the full-day data and would hit any real continuous Site.
- **Context note:** this Architect's context is getting heavy. Use a fresh Architect for the next lane-2 ruling.

## DD1a1-R10: R6 assertion 7 restated as deterministic assertions; the batch-order cut goes to the backlog

- Architect: Claude (Architect 25), 2026-11-06. Binding checked: Claude in the lane worktrees' `.ai/ROLE_CONFIG.md` (owner, 2026-10-27). Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` "R6 degraded-day check" and `DD-1a1-handoff.md` at `68be2a339`. The builder's diagnosis is accepted.
- **Answer 1: grade equality to v1 is the wrong acceptance.** v1's degraded grade depends on which source's batches sort first by a random source id, so it is not a reference. R6's own premise ("the day grades as v1's degraded day") was wrong in the same way. An equality to a random value cannot pass or fail for the right reason.
- **Answer 2: the honest cut is by source time, not batch order.** A gateway outage is one instant: every signal stops together. The delivered part is every reading with source time before the outage instant, for every source; nothing at or after it. Batches that span the instant are split there. The instant is fixed by the kind, not chosen: the story run's start plus half its duration (06:00 + 4 h = 10:00 local, 07:00Z). The batch-order cut is not honest: one source stops at 02:55 while another continues, which is no real outage shape.
- **Answer 3: not defensibility-critical now; backlog it.** The v2 calendar has no `degraded` day (R6 scope note), so no shown story carries the defect. It matters only if a degraded day is added.
  - **Backlog (next free BL id, BL-18 at the time of writing): source-time outage cut** in `publish_first_half` and the `add_day` degraded path, with the instant above. Its check: the delivered set is identical across two builds, and every signal's last delivered source time is below the instant.
  - **Guard.** No `degraded` day may enter a shown calendar, demo script or live `add-day` demo until that backlog item lands. If one is asked for, stop and the Architect rules.
- **R6 assertion 7 now reads (deterministic):**
  - The day is one epoch with 0 AMBIGUOUS, and no Finding (equal to v1: none).
  - The day's window is not COMPLETE: it is LIMITED with an incomplete-evidence reason, in both v1 and the `with` build.
  - No story-window interval ends after the last delivered source time, except as OPEN_BOUND.
  - The post-outage hours add nothing: the story-window intervals in `with` equal those of `without` on the same build's delivered set.
  - No comparison of interval times or classes to v1.
- **Size: +0.** The check script changes only. DD-1a1 stays 4.5 and DD-1 stays 9.25. No owner question: no shown story changes.
- **Handoff:** builder applies the restated assertion 7 in `deg.sh`, reruns it, records the result in the packet's R6 section, and continues with the handoff's "Resume here" step 2. Context note: this Architect is fit for the next lane-2 ruling.

## DD1a1-R11: Q8 cost, projected full-day prepare against the 3 h cap

- Architect: Claude (Architect 25), 2026-11-06. Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` at `ff21f16e0` (Q8 line), `.agent\DD-0c-probe-results.md` §5, `.agent\DD-0b-probe-results.md` §7.
- **What the +226 % measures.** It compares v2's 8 Kobo story days with and without their complements: (330 − 27) / 8 = 37.9 s per story-only day against (1075 − 27) / 8 = 131 s per full day, ×3.46. But DD-0b/DD-0c never projected story-only days. They priced every Kobo day as a full 24 h day: `day_kobo = per_run × 24/8` = 123 s central, 138 s upper. So the measured full day is **+6.5 % over the projection's own Kobo term**, not +226 %. The +50 % gate was set against the wrong base. The 3 h cap is the binding test.
- **Assumptions.**
  - Kobo full day is 131 s central (measured, including the trial-day split). The upper is 147 s, scaled by DD-0c's 46/41.
  - Cold full day is 24 hourly runs (Q5) × 5.17 s = 124 s central, and × 6.84 s = 164 s upper. This is not yet measured as a whole day; the Cold failure day with 23 fill-ins will measure it.
  - EV, `tree`, `finish` and fixed costs are as DD-0c §5. Day counts are 22/22/3 (B-22) and 16/16/2 (B-16).
  - Drain: DD-0c's 32 s per Kobo day was measured on story-only data. Shown two ways: unscaled (DD-0c's 1,611 s at B-22) and scaled ×3.46 to full-day data (111 s per Kobo day + the 900 s tick allowance = 3,336 s at B-22, 2,431 s at B-16). Scaled is the planning case. The ticks remain unmeasured.
- **Projection (sequential, with drain; central / upper).**
  - **B-22 full days (as built):** 6,889 / 9,316 s before drain. With drain: unscaled 2.36 / 3.04 h, **scaled 2.84 / 3.51 h**.
  - **B-16 full days:** 4,990 / 6,683 s before drain. With drain: unscaled 1.71 / 2.18 h, **scaled 2.06 / 2.53 h**.
  - **B-22 with full story days and short (8 h) steady days:** **about 2.2 / 2.8 h** (scaled). It saves only about 0.6 h, because Cold and EV are unchanged.
  - **Accept a longer one-time build:** B-22 as built, at up to about 3.5 h. That is under the 6 h hard stop.
- **Fits 3 h?** On central, yes (2.4–2.8 h). On the upper case, no (3.0–3.5 h). The overrun rests on two unmeasured terms, the drain scaling and the tick allowance. So it is not yet a measured over-run.
- **Options.**
  1. **B-16, all days full:** 2.1 / 2.5 h. Every day is COMPLETE and the board window keeps 16 days of history. It loses 6 baseline days per Site.
  2. **Short steady days:** 2.2 / 2.8 h. The steady days grade LIMITED, as "without" did on 10-07, 10-14 and 11-01, so most of the history shows incomplete evidence that a real Site would not have. This contradicts CH9-R4 (full days) and weakens R9's continuous-data baseline. **Rejected** as dishonest for the saving it brings.
  3. **B-22 as built, one-time longer build:** up to about 3.5 h.
- **Recommendation: keep B-22 full days now.** R1's rule stands: the DD-1b2 rehearsal measures the whole prepare, including drain and ticks. If it is over 3 h, use B-16 (option 1). Option 3 only if the owner prefers 22 days over a 3 h build.
- **Owner question (plain language):** "The full demo history is projected to take about 2½–3 hours to build once, possibly up to 3½ hours. If the final rehearsal runs over 3 hours, should we (a) show 16 days of history instead of 22, every day complete, or (b) keep 22 days and accept a one-time build of up to about 3½ hours?" **Recommendation: (a).**
- **Size: +0.** Projection only; the measurement is already in the DD-1b2 rehearsal. Q8's +50 % gate is superseded by the 3 h cap on the projection base. Handoff: the coordinator puts the owner question; the builder continues with the packet's Open items; DD-1b2 reports the measured whole-prepare time against the 3 h cap. Context note: this Architect is fit for the next lane-2 ruling.

## DD1a1-R12: the mill-day probe; the dusk start state, other days' productive kWh, and the mill verdict's days

- Architect: Claude (Architect 25), 2026-11-06. Input: the coordinator's mill-day probe report (local day 10-30); `config/scenarios/kobo-steady-dusk.yaml` (start state: lines 4 and 7, values 42 %, 300 L, STOPPED, "the parent's, declared at that parent's own start"); this sheet's Q3 night section ("Starting states: measured handover, never chosen").
- **1. The 15:50Z (18:50 local) generator start is a defect, not honest physics.**
  - `kobo-steady-dusk` restarts the battery at the evening parent's declared 42 %. Under the 18–20 evening peak with no sun, 42 % reaches the 35 % start threshold in about 50 minutes. The start comes from that declared reset, not from the day.
  - A real day reaches 18:00 with the state its daytime left. Probe S estimates about 68 % at 20:00 on a sunny day, so no dusk start.
  - It breaks the rule the nights follow: start states are measured handovers, never declared values.
  - The defect is on every day, not only the mill day. Every B-22 steady day runs `kobo-steady-dusk`, so it would put one dusk generator start, held by the 90 % stop, on every steady day. That is a recurring generator interval no parent declared. It could add MG-2 candidate-avoidable intervals and fuel cost to the baseline and muddy the 3 MG-2 Findings and ACT-K1's baseline.
  - The v2 probe did not show this: dusk appears only on the mill day, and the mill day was not in the probe calendar.
  - The 02:05Z (05:05 local) night start is the accepted pre-dawn start (R3 Q2; R3 L2 check 1) and stands.
- **Ruling: measured dusk start states.**
  - `kobo-steady-dusk` takes its SoC, fuel and generator state from Probe S at 18:00, the continuous steady day. The file cites the run id.
  - A derived `kobo-mill-dusk` (the same windows, each with its `# source:` line, labelled "Kobo 18:00–20:00 after the mill story day; start state measured at 18:00") takes them from one probe of `kobo-mill-midday` at its 18:00 end. The `mill-midday` complement uses it.
  - Both files go into `--check`. The physics then decides. Nothing is tuned, and no file is edited to avoid a start.
- **The checks (L2, own `*_test` DB).**
  - On 10-30 and on one steady day: generator starts, runtime and fuel per complement window.
  - Findings, threads, money rows and MG-2 candidate-avoidable intervals equal with and without full days.
  - The 18:00 seam shows no SoC, fuel or generator-state jump.
  - If a dusk start remains under measured states, or any of these differs, stop and the Architect rules.
- **2. Other days' productive kWh (168.333 → 210.333, 0 → 42): honest, and no proven figure moves.**
  - The +42 kWh is real daylight productive use in the steady-afternoon complement's 14–18 local hours. It was absent when story days ended at 14:00. Full days measure the whole daylight period, which is the point of CH-9 §9.
  - The CH-6 proofs are of computations, not of v2 values. Kobo's Grow 42.08 USD on clone 10-30 comes from polish data and is not affected.
  - On the v2/B-22 build, every Grow figure is whatever its own rows give. DD-1b2 F-THREADS reports each Grow value and proves it reproduces from those rows, as the coordinator's MG-2 note already requires. No value is pinned to a CH-6 number.
- **3. The mill verdict on B-22: not proven, and it is the Grow story's E3 risk.**
  - Full days make COMPLETE days possible. Without them none exist, which is why the probe was NOT_JUDGED. But no build has yet shown 3 COMPLETE days on each side.
  - A second risk is what the later days run. If the days after the mill Action's effective day are plain steady days (the pre-change mill window), the later window measures no change, and "Target met" cannot honestly come out.
  - **Named check, MILL-3, run as a dry run in DD-1a2 (where R4 places `mill-midday` on the B-22 list) and asserted in DD-1b2 F-THREADS.** From the B-22 day list and build, report:
    - the effective day;
    - the 3 baseline and 3 later days the plan freezes, within the 14-day look-ahead;
    - each day's grade, run set (scenario ids) and `productive_kwh`;
    - the MG-5 and MG-4 guardrail days;
    - the evaluator's outcome.
  - Acceptance: 3 COMPLETE days on each side, and an outcome of VERIFIED ("Target met") by the catalogue rule.
  - Stop and the Architect rules if any of these happens:
    - fewer than 3 COMPLETE days on either side;
    - the later days do not run the changed mill operation;
    - the outcome is not VERIFIED.
  - Never move days or tune values to pass.
- **Size: +0.25** for the two measured dusk start states, `kobo-mill-dusk` and their checks. MILL-3 is +0 inside the DD-1a2 placement and DD-1b2 F-THREADS acceptance. DD-1a1 4.5 → 4.75, DD-1 9.25 → 9.5; the plan rows need it. No owner question now. If MILL-3 stops, the Grow story's later days are an owner-visible choice.
- **Handoff:** the builder measures the two dusk start states, adds `kobo-mill-dusk`, reruns the mill-day probe with the checks above, and records them in the packet. MILL-3 is added to the DD-1a2 and DD-1b2 acceptance lists. Context note: this Architect is fit for the next lane-2 ruling.
