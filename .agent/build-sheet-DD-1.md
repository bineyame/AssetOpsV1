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

## DD1a1-R13: the Cold failure day with full days, and the steady-afternoon generator start

- Architect: Claude (Architect 25), 2026-11-06. Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` at `80f199328` ("Cold failure day with full days", and the `kobo-steady-dusk` observation); `backend/tests/test_w502_cold_scenario_producer.py:160-182` (`enqueue_window`, `finding_revision`: exact `ar.window_start`/`window_end` equality); `:213` (the case's release is start + 70 min, its window start + 65 min); DD-0c §1 (`_coalesce_job` widens a PENDING job on overlap, and Cold adds a 10-min bridge). The build DBs were dropped, so the cause is not yet observed.
- **1. Cold failure day: two candidate causes, one cheap probe decides.**
  - **(a) Matching defect in the tool.** The hourly fill-ins' recompute jobs lie within Cold's 10-min bridge of the failure run's job, so they coalesce. The failure is then assessed in a wider analytic run, and `finding_revision`'s exact-window match finds nothing, although a COLD_START_FAILURE Finding exists.
  - **(b) A real double send (tiling defect).** The failure case runs 65–70 min, but its hour slot is 60 min. If the next fill-in starts at the slot edge, its first 5–10 min re-send instants the failure run already covers. That breaks R5's "each instant is sent once" and can rightly change or refuse the assessment.
  - **Probe (L2, own `*_test` DB, the `cold` build to the failure day).** Report:
    - every cold_chain `analytic_run` window over the failure hour;
    - every COLD_START_FAILURE Finding and its interval;
    - per signal, any source time sent by two runs.
- **Ruling.**
  - **If (b):** the fill-in after the failure run is a derived file that starts at the failure run's last stamp plus one step, as in R7b. Each instant is sent once. The physics decides, and nothing is tuned. L0 adds that the Cold day's runs tile [00:00, 24:00) local with no instant twice.
  - **If (a) (after any (b) fix):** the BUILD path selects the failure Finding by its run, not by an equal window: the newest COLD_START_FAILURE revision whose analytic run window contains [case start, case window_end). The w502 test's own exact-window assertion stays for its test; only the build body changes. `enqueue_window` is not used to force the case's window on the full-day build.
  - **Acceptance:** with versus without full days, the failure day has the same 3 Findings: mechanism, episode interval, claim level, citations and the cold money/cost rows, apart from revision counts as R8 allows. 0 AMBIGUOUS.
  - **Stop and the Architect rules if:** no COLD_START_FAILURE Finding exists in any window after the (b) fix, or its interval or claim differs. Either would mean the fill-ins truly change the assessment.
- **2. The steady-afternoon 12:05Z (15:05 local) start: honest physics, not an R12-class defect.**
  - Its 14:00 seam is continuous (SoC step ≤ 0.16), so the run starts from the day's own state, not a declared reset.
  - The days that use it are story days after a `dispatch-necessary` morning, whose story is that the generator is needed. A low battery that meets the afternoon load and starts the generator follows from that declared cause.
  - MG-2 candidate-avoidable counts, Findings and money are already equal with and without full days (R3 check 2).
  - **R12 still binds B-22.** The pure steady days that DD-1a2 adds run `kobo-steady-day` + `kobo-steady-dusk` + `kobo-night-late` (Q3), so the measured dusk start state is needed there. R12's "every steady day" was premature for v2, but right for B-22.
  - **Checks, standing in DD-1a2 and DD-1b2.**
    - Per complement window on every Kobo day: generator starts, runtime and fuel, and the SoC step at each seam, which must be ≤ 0.5 percentage points with an equal generator state.
    - A pure steady day must show 0 starts from 06:00 to 20:00 local, as Probe S expects.
    - MG-2 counts, Findings and money must stay equal with and without full days.
    - If a seam step exceeds the bound, or a pure steady day starts the generator before 20:00, stop and the Architect rules.
- **Size: +0.25** for the probe, one derived Cold fill-in or the build-path selector (whichever the probe needs), and the checks. DD-1a1 4.75 → 5.0, DD-1 9.5 → 9.75; the plan rows need it. No owner question: no shown story changes.
- **Handoff:** the builder runs the Cold probe, applies (b) and/or (a) as found, reruns `cold` and `cold-without`, records the result in the packet, and adds the per-seam checks to the DD-1a2 and DD-1b2 lists. Context note: this Architect's context is getting heavy. One more short ruling at most; use a fresh Architect after that.

## DD1a1-R14: Cold full days are withdrawn (amends Q4); every complement seam carries the measured state of that day's previous run

- Architect: Claude (Architect 26, new standing lane-2 Architect), 2026-11-06. Binding checked: Claude (`.ai/ROLE_CONFIG.md` 2026-10-27, in the plan2 and dd1a1 worktrees). Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` "R13 (builder 18)" and `DD-1a1-handoff.md` "Builder 18", both at `b313fba57`. The probe is accepted: the cause is neither R13 (a) nor (b). It is the S4-05 source gate. The day-wide window holds evidence from 68 runs, `source_provenance.classify` returns MIXED (`MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS`), and `failure_finding = failure and gate.permitted` is false. COLD_EXCURSION is affected in the same way.
- **1. Cold failure day. Ruling: drop Cold full days (option 4). This reverses Q4 for Cold only; Kobo full days stand.**
  - **Why.** Rule N-L2 ("several runs are never coherent") is correct for central evidence. It cannot tell tool-made fill-ins from unrelated uploads, the same reason R5 (b) and (d) were rejected. Every tool option still leaves more than one run in the window: fewer or longer fill-ins, or a "shared basis", which only the product rule could grant. A gate change for "same Site, steady runs, one basis" is product-level S4-05 work. It would weaken a gate that defends every Cold Finding, so it is out of SCOPE-1.
  - Option 1 (story-only on Finding days only) is option 4 in practice, because the Cold days in v2 are its story days, and all of them carry the failure or the excursion. A partial-day rule that applies to some days and not others would also be harder to explain.
  - **How they grade.** Each Cold story day goes back to its v1/`cold-without` shape. It grades partial (partly checked), because only the declared example hours were sent, and it keeps its 3 failure-day Findings, its excursion and its cold money/cost rows exactly as reviewed before DD-1a1.
  - **Why that is defensible.** The partial grade is literally true: the hours with no data were not checked. Q4's only reason was the look of 23 unchecked hours. No Cold claim, number or "Why?" line depends on those hours, whereas with full days the Findings disappear. Presenting less beats a full day that shows no Finding.
  - **Build.** Cold leaves the v2 `complement` lists, and `cold-steady` is no longer used by the tool. Q7's L0 union check applies to Kobo days only. For Cold, L0 asserts that v2 days equal v1 days (R8 epoch and sequence exemption). If B-22 (DD-1a2) would add a Cold steady day, it is a story-only day on the same rule, or it is left out; it is never tiled.
  - **Acceptance.** `cold` equals `cold-without`: the same 3 Findings on the failure day, the excursion, the intervals, claims, citations and money/cost rows, with 0 AMBIGUOUS.
  - **Backlog (coordinator adds the id to `.agent/backlog-post-demo.md`).** For a real Cold site sending many uploads a day, the S4-05 multi-run gate could withhold every day-wide Cold Finding. This is a product question for after the demo: a compatible-run basis attestable from evidence. Source DD1a1-R14, size not estimated (S4-05 Architect pass first).
- **2. Seams. Ruling: every seam where a complement starts carries the measured end state of the run before it in the same Site-day stream. Story-run starts are the only declared resets.**
  - **Why.** R12's rule is "start states are measured handovers, never declared values". A handover measured on a different day (Probe S, the steady night probe) is still a declared value on a story day. That is exactly what makes 17:00Z step +38 pp (and +44 pp on 11-05), with RUNNING → STOPPED, and 15:00Z step +0.95 pp. A 38 pp jump with the generator switching off by itself cannot be explained to a client.
  - **Mechanism, as R12's `kobo-mill-dusk`.** For each distinct story-day chain on the v2 list (by story scenario id; 11-04 and 11-05 differ), the builder adds a derived dusk (18:00), late night (20:00) and next early night (00:00) file. Each one's SoC, fuel and generator state comes from one probe of the preceding run of that chain, and each cites the probe run id. The windows are verbatim with their `# source:` lines, and the label says "start state measured at HH:00 after <story day>". If the next local day is a story day, the chain ends at its 06:00 story start. All the files go into `--check`. The physics then decides. A generator still RUNNING at 20:00 keeps running, and nothing is tuned.
  - **Bound.** At every complement start (11:00Z, 15:00Z, 17:00Z and 21:00Z, plus any R7 split instant), the SoC step must be ≤ 0.5 pp, with equal generator state and a fuel step of ≤ 0.5 L. **15:00Z's 0.95 pp is not accepted**: it is the same cross-day handover defect, and the chain removes it.
  - **Exempt seams.** These are only the 03:00Z (06:00 local) story-run starts, where the story run is byte-equal to v1 (R5). They are declared starts. They are reported per day in the check output, and the preceding night's source line names the boundary (R3 item 5). No bound is applied, and the story is never edited to close the gap. On a steady-to-steady 06:00 seam the bound applies.
  - **Stops (L2, own `*_test` DB).** Stop and the Architect rules if, after the chain:
    - any non-exempt seam exceeds the bound;
    - a night adds a generator interval, Finding, thread or money change that the without-full-days build lacks (R2 stop gate and R13 check 3: MG-2 counts, Findings and money equal);
    - the R3, R6, R7, R7b and R12 checks change.
  - The pure-steady-day check (0 starts from 06:00 to 20:00) stays INFO here and binds in DD-1a2/B-22 (R13).
- **Size.**
  - Cold withdrawal: +0. Removing the Cold complement path and the v1-equality L0 offset the extra work.
  - Seam chain: +0.5. That covers derived files for each story chain, their probes and `--check`, the bound with its exemption, and the reruns.
  - DD-1a1 5.0 → 5.5 (2 planned), DD-1 9.75 → 10.25; the plan rows need it.
  - SCOPE-1 reasons: without (1) the board shows a Cold failure day with no Finding; without (2) the Kobo battery chart shows 38–44 pp jumps that no "Why?" line can explain.
- **Owner question (one, recommendation given; the build proceeds on it unless overridden):** "The cold-lab example days only have data for their example hours. Keep them shown as 'partly checked' so the cold failure findings still appear? Recommended: yes. The alternative, filling the whole day, makes the cold failure finding disappear."
- **Handoff:** the builder removes Cold from the v2 complement lists and reruns `cold`/`cold-without` to equality. It then builds the per-story chain files, reruns Kobo `with`/`without` with `dd1a1_r12_check.py` updated for the bound and the 03:00Z exemption, and records both in the packet. Context note: this Architect is fit for the next lane-2 ruling.

## DD1a1-R15: step back. Cut complements only where the generator is STOPPED: one rest-of-day run per story day (replaces R14 part 2's chain design)

- Architect: Claude (Architect 26), 2026-11-06. Binding: Claude. Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` "DD1a1-R14 (builder 19)", `DD-1a1-handoff.md` "Builder 19", `.agent/DD-1a1-r14-wip/` at `1debe5a9d`; `simulator/assetops_simulator/packs/mini_grid.py:9-11,96` and `backend/assetops_backend/runs/profiles.py:1240-1242` (`initial_values_supported={STOPPED, FAILED}`, "RUNNING and STARTING need timer history"). R14 part 1 (Cold) is done and stands.
- **The root cause behind R12, R13 and R14 part 2.** A run can start only from STOPPED. Any cut in a day where the previous run ends RUNNING can never be a true handover. Under R2's nights, a cut at 18:00 or 20:00 local often falls in a dusk or evening generator interval, and the 06:00 cut falls in the 05:05 pre-dawn interval. So more chained files cannot fix it. The fix is fewer cuts, placed only at instants where the generator is STOPPED.
- **Options weighed.**
  - **(A) One 24 h run per Kobo day: not possible as stated.** The story run is ACT-K1's run and is byte-equal to v1 (R5, R8). It starts at 06:00 from its declared state. A 24 h run starting at 00:00 would reach 06:00 in its own physical state, so the story hours would change and the story itself might not occur.
  - **(A′) The feasible nearest form: RECOMMENDED.**
    - The story run is untouched.
    - One derived **rest-of-day** run per story chain covers 14:00–24:00 local. It holds the afternoon, dusk (18–20 evening parent) and R2 late-night windows verbatim, each with its `# source:` line. This is Q3's original single 14–24 complement, with R2's night windows inside it. Its start state is measured on the **registered Site** at the story run's 14:00 end. R13 measured that seam at −0.16 pp with equal state.
    - Each early night (00–06) is one run from the previous built day's measured 24:00 state.
    - A pure steady day (B-22, DD-1a2) is one 00:00–24:00 run from the previous day's measured 24:00 state, which avoids the 06:00 cut.
    - R7's 03:00 split stays as ruled, since it falls before the pre-dawn start.
    - The 15:00Z and 17:00Z seams then no longer exist, and runs per day go down, which also helps Q8.
  - **(B) Allow a RUNNING start: rejected; product change, to the backlog.** It needs a declared runtime-so-far timer in the scenario contract, the simulator pack and the backend profile (`initial_values_supported`), with a profile-version and registered-basis check (R7b boundary). About 1–1.5 units plus regression risk on a defended path. The coordinator adds the backlog id: "RUNNING/STARTING initial state with timer history", source DD1a1-R15.
  - **(C) Keep stitching and disclose: not defensible as the main design.** Three or four resets a day, with the generator switching off by itself and 38–44 pp battery jumps, cannot be explained under questioning. Disclosure is defensible for **one** reset per story day, at 06:00 where the example day begins. That is R14's 03:00Z exemption and it stays: reported, and named by the night's source line (R3 item 5).
  - **(D) Story-only Kobo days: rejected while A′ holds.** It loses CH9-R2's "daytime solar unused" (and R12's +42 kWh daylight productive use), MG-5's full day, MILL-3's COMPLETE days and so the Grow "Target met" claim, and the owner's night decision. It is the fallback only if A′'s guards stop.
- **Bound (amends R14).**
  - At every cut that is not a story start (14:00 local / 11:00Z, 24:00 local / 21:00Z, the R7 split instant), the generator must be **STOPPED on both sides**. The SoC step must be ≤ 0.5 pp and the fuel step ≤ 0.5 L.
  - The 06:00 story start is exempt, as in R14.
- **Probe first (L2, own `*_test` DB, registered Site via the `_shifted` drafter of `host/tests/test_dd1a1_registered_kobo.py`).** The template-Site probe is not evidence for the build and is set aside.
  - Probe each story chain to 14:00 and through its rest-of-day to 24:00: N, the R30 trial day and the mill day.
  - The R25 chain (the 25 % reserve after S+1) is probed with the Foundation revision applied on that Site, as the trial chain applies it.
  - Report the state at 14:00, the state at 24:00, and the generator intervals inside each run.
- **Stops.** Stop and the Architect rules if any of these happens; this is the only point where D for the affected days goes to the owner:
  - a story run ends RUNNING at 14:00 local;
  - a rest-of-day or steady run ends RUNNING at 24:00;
  - R14's stop list fails: MG-2 counts, Findings and money equal; the R2 night gate; the R3, R6, R7, R7b and R12 checks;
  - MILL-3 later fails.
- **Build.**
  - Retire R14's `afternoon-<c>`, `late-<c>` and dusk split kinds and the `kobo-steady-dusk`/`kobo-mill-dusk` files from the v2 list. The R12 files are superseded, since dusk is now inside the rest-of-day run.
  - Add `kobo-rest-<c>` (14–24) and `kobo-night-early-after-<c>` per chain, plus the steady-day 00–24 file for DD-1a2.
  - L0 tiles each local day with ≤ 3 Kobo runs (early night, story, rest-of-day), with each instant sent once (R5, R8).
  - `dd1a1_r12_check.py` takes the new bound, the STOPPED-at-cut rule and the 06:00 exemption.
  - The WIP's `after` hook and probe `chains()` are reused.
- **Size.** This replaces R14 part 2's +0.5 (not added to it). +0.25 more for the registered-Site probes, including the R25 Foundation revision. DD-1a1 5.5 → 5.75 (2 planned), DD-1 10.25 → 10.5; the plan rows need it. SCOPE-1 reason: the same as R14 part 2. Without it the Kobo battery chart shows jumps no "Why?" line explains. This is the last stitching design: if its guards stop, D goes to the owner rather than another seam ruling.
- **Owner.** No decision needed now: no shown story changes, and the owner's night decision and CH9-R4 hold. The coordinator informs the owner of the size against the 2 planned.
  - Only if A′ stops: "Some Kobo example days can't be filled to a full day honestly. Show them as 'partly checked', losing the 'daytime solar unused' figure and the mill 'Target met' result for those days?" The recommendation would then be given against the probe's numbers.
- **Handoff.** The builder takes the registered-Site probes first. If no stop fires, it derives the `kobo-rest-*` and early-night files, runs `--check`, rebuilds Kobo `with`/`without`, runs the R3–R14 checks with the amended bound, and runs guards V, A and W. Context note: this Architect is fit for one more lane-2 ruling.

## DD1a1-R16: after the R15 stops, Kobo goes hybrid: full days only where every join is STOPPED (recommended; owner decides)

- Architect: Claude (Architect 26), 2026-11-06. Input: `AssetOpsV1-dd1a1\.agent\review-packet-DD-1a1.md` "DD1a1-R15 (builder 20)" at `afe90e8c1` (registered KOBO-001 probe).
- **Probe results.**
  - N is RUNNING at 14:00 (06:25–14:00) and at 24:00.
  - R30 and R25 are STOPPED at 14:00, but RUNNING at 24:00 (22:05 and 23:25 on) and through their early nights.
  - The mill chain passes. It is STOPPED at its 18:00 story end (89.47 %) and at 24:00 (48.42 %). The 18:00 cut is accepted as a valid cut, since it is STOPPED on both sides.
- **What each option keeps and loses.**
  - **(1) Hybrid: RECOMMENDED.**
    - A day is full only if every join of its chain is STOPPED on registered-Site probes, under the R15 bound. Today that is the mill day, plus any steady 00–24 day whose 24:00 ends STOPPED (B-22, DD-1a2, probed per day).
    - The N (necessary-run), R30 and R25 trial days are story-only and read "partly checked", which is literally true.
    - **Keeps:**
      - The 3 generator Findings, their intervals and their citations ("without" = "with", R5/R8).
      - ACT-K1's trial outcome and metrics (Q6 equality: complements never moved them).
      - MG-2 counts and money (R3 check 2, equal).
      - On the mill/Grow day: "daytime solar unused", the R12 +42 kWh daylight productive use, and the MG-5 full day.
    - **MILL-3/"Target met"** stays possible, but it is not yet proven. It needs 3 COMPLETE days on each side, and those days must be mill or steady days that pass the join rule. The DD-1a2 dry run decides; if it fails, the R12 stop applies.
    - **Loses (generator/ACT-K1 days only):**
      - The full-day solar-unused and MG-5 readings on N/R30/R25 days. These show as "not available yet" or partly checked.
      - Those days' nights, so the owner's night profile shows only on full days.
      - The R6/R7/R7b night-split work for those days, which becomes moot.
      - Nothing the generator story claims.
  - **(2) All Kobo days story-only (D).** Everything in (1)'s losses, plus:
    - the mill day's solar-unused, MG-5 full day and daylight kWh;
    - MILL-3, so the Grow "Target met" result cannot be shown at all;
    - the owner's night decision entirely.
  - **(3) Option B.** It keeps full days everywhere, but only after a product/simulator change: a RUNNING start with a timer, in three contracts, with a profile-version/registered-basis check. That is about 1–1.5 units, plus re-probing every chain, which takes DD-1a1 to about 7–7.5, against 2 planned. It also puts regression risk on a defended path just before the demo. It fails SCOPE-1's "present less over building more" while (1) keeps every claim.
- **Build if (1).**
  - v2 keeps complements only for chains that pass. N/R30/R25 days become story-only, with v1-equal payloads.
  - The mill day gets `kobo-rest-mill` (18–24) and its early night.
  - L0: a full day tiles [00:00, 24:00); a story-only day equals v1.
  - `dd1a1_r12_check.py` applies the R15 bound to full days only.
  - DD-1a2's B-22 steady days are full only if their 24:00 probe is STOPPED, and story-only otherwise. They are never tuned.
- **Size: −0.25.** The N/R30/R25 chains, the R25 Foundation-revision probe build-out and the R7 night split for trial days are dropped. DD-1a1 5.75 → 5.5 and DD-1 10.5 → 10.25; the plan rows need it. SCOPE-1 reason: as in R15, but only for the days kept full.
- **Owner question (one; recommendation: yes, option 1; the build waits for the answer, because it reverses part of CH9-R4/Q4 for Kobo):** "On the example days where the generator is still running at the edge of the example, we can't fill in the rest of the day honestly. Show those days (the generator-support and trial days) as 'partly checked'? Their findings and the trial result stay the same, and the mill day keeps its full day and 'Target met'. Recommended: yes. The alternative is about 1–1.5 extra units of simulator work to fill every day."
- **Handoff.** Wait for the owner's answer. If it is yes, the builder applies "Build if (1)", rebuilds Kobo `with`/`without`, runs the R3–R15 checks on the full days and guards V, A and W, and adds the join rule to the DD-1a2 MILL-3 dry run. Context note: this Architect is fit for one more short lane-2 ruling.

## DD1a2-R: rulings on the DD-1a2 pre-flight (Architect, Claude, 2026-11-06)

- Architect: Claude (new standing lane-2 Architect). Binding checked: Claude (`.ai/ROLE_CONFIG.md` on this branch, owner 2026-10-27). Input: `.agent/DD-1a2-preflight.md` at `1592b5543`.
- **Evidence weight.** The builder's chain table comes from a scratch script on the template Site, and Findings and grades were not measured. R15 and R16 required registered-Site probes, so **no figure in that table binds anything here**. G0, G1 and G2 below re-measure on the registered Site. Everything in this ruling marked "read from code" is a code reading, not a measurement.

### Builder's claims, checked against code and files

| Claim | Result |
|---|---|
| Q2: `kobo-steady-day` and `kobo-mill-midday` have the same mill windows | **Correct.** Both are 0, 15, 18, 10, 12, 0 kW, verbatim `kobo-daytime`. |
| Q2: INEFFECTIVE TARGET_MISS "by construction" | **Correct, and it holds wherever both sides run these windows.** `assess` (`verification_families.py:321`) needs `10*l*nb >= 11*b*nl`. Equal non-zero means fail it. Placement cannot help. |
| Q2: `kobo-daytime-larger-mill` fails the join rule | Not verified on the registered Site. It is rejected anyway: its mill is 35, 40, 30, 32 kW, more than double the reference, so it declares a second machine, not a change of operating pattern. |
| Q3: the window rule and fixed days | **Correct** (`verification_families.py:13-16`, v2 `sites`). |
| Q4: `LATE_IN_STREAM` refuses S-4 and S-2 | **Correct** (`demo_story_days.py:296`). `plan_add_day` does not run this check. See Q4. |
| Q6: "the plan rows (`:781-787`) agree" | **Partly wrong.** The bullet below the table still says "above 2 h elapsed, the fallback is B-16". The owner's later decision says 3 h and it governs. |
| Q8.4: `DEGRADED_DAY_HELD` is vacuous on this list | **Correct** (`demo_story_days.py:163`, only with a `complement`). |

**What the builder did not raise, and it matters for Q2.**
- **The verdict measures whole-day mill energy, not midday.** `productive_kwh` has period `operating_hours` (`chain/measures.py:45`), and `day_kwh` sums every row of the day. The catalogue's `[midday]` is not applied by any code.
- This has two consequences:
  - A true shift that keeps the energy equal and moves it out of the sun would read no change and fail. So a conserved-energy "before" is not available without a metric change.
  - The sentence "Midday use before and after: 42 → 110 kWh" is only loosely true: all of this energy is in daylight, but not all at midday.
- **A "before" with the mill idle until 14:00 has a measured precedent.** R12 item 2 accepted "0 → 42 kWh" on the build's trial days as honest daylight use: the reserve-trial morning plus the evening parent's 14-18 windows. The builder's composition is that same shape.
- **On today's data the story has no "before" at all.** A plain steady day already runs the mill at midday, so "run the mill at midday" would be a change to nothing. This is a story defect as well as a check failure.

### Q1. Steady day: **(b), the mill-day shape, with a 06:00 start. This reverses R15's pure steady day and R14's "on a steady-to-steady 06:00 seam the bound applies". The owner is asked.**

- **The builder's gate is not the right decider, for three reasons.**
  - **A Finding a day is close to certain under (a) (read from code).** `dispatch._classify` works per segment. From 10:00, at 900 W/m² against about 30 kW of load, PV alone clears load plus 10% with no binding constraint, which is CANDIDATE. FINDING_CLAIM_LEVELS raises on that. The reserve-trial day has the same mixed interval (minimum-runtime minutes, then candidate) and it is exactly what raises ACT-K1's problem. So about 13 extra days would carry the problem that the story says recurs weekly, which breaks R13's "MG-2 counts, Findings and money equal".
  - **Even with no Finding, (a) damages the mill story.** The builder's scratch table shows about 7-9 L a day on the "before" pattern and about 22 L a day on the "after" pattern. Continuous physics would then show the mill change roughly tripling diesel on the Grow Action's own days, with no guardrail on screen (BL-09). That figure is template-Site only. It is enough to rule against, and not enough to quote as fact.
  - **(a) is not what the owner approved.** They were told about 0 L and no story figure changes.
- **What (b) costs, stated plainly.** Each full day starts 06:00 from a declared 55 %, 300 L, STOPPED. The battery line steps up at 06:00 and the generator stops by itself. Battery and fuel do not carry across 06:00, so the example adds energy each morning that the model did not earn. R15 option (C) already held that one disclosed reset a day, at 06:00 where the example day begins, is defensible. The mill day already has it and has passed every R3-R13 check on the registered Site. The 06:00 seam is reported per day, never bounded.
- **Disclosure, required on each 06:00 start file.** Label and first source line read: "Example data. Each full example day starts at 06:00 from a declared battery level and fuel level. Battery and fuel are not carried over from the night before." The existing `RESET_0600` line on `kobo-night-early` stays.
- **Gate G1 (L2, one registered day of each profile, about 5 min each).** Report intervals, classes, Findings and money.
  - **Pass:** only the pre-dawn start, all of its minutes classed needed, 0 L, 0 starts 06:00-20:00, 0 Findings, no money change. Build continues.
  - **Fail:** stop and the Architect rules. No value changes. The likely result is that those days cannot be full, MILL-3 stops, and the owner gets the "not judged yet" choice.
- **If the owner picks continuous days (a).** Run G1a first: one registered 00-24 day on each profile, same report. Report the measured figures back to the owner before building anything. If they still choose (a), it needs one file per chain position, +0.25, and the mill profile question reopens because of the fuel figures.

### Q2. **Option A in the corrected form below, as an owner question. Not "tuned", and not neutral.**

- **Is it an honest "before"? Yes, if it is called what it is.** It is an **authored** example. We wrote the before pattern because the story needs one, the same way the reserve-trial days are authored. It is not a measurement, and it cannot be called "no value chosen to reach a result" in the sense of a neutral draw: the pattern was deliberately chosen to differ. What keeps it honest:
  - Every value comes from an existing parent, and no new number is introduced.
  - The shape already exists on this build (R12 item 2).
  - The margin (about 162 % by windows, not measured) is nowhere near the 10 % line, so nothing is sitting on the threshold.
  - The evaluator is the real one over real rows, and the owner's 10 % is unchanged.
  - **The composition is frozen by this ruling, before any product measurement. It is never revisited after seeing a result.**
- **What the client is told (demo script, and if asked):** "This site is example data. In the example, the mill used to start at 2 pm. After the change it runs from 8 am and uses the spare solar. It runs more hours and grinds more, so this is more daytime use, not the same work moved. The check itself is real and applies the 10% rule to the readings." **Do not say** "same grain, moved to midday", "measured at a real mill", or quote the percentage as a result.
- **The file: `config/scenarios/kobo-steady-before-mill.yaml`,** generated by `tools/derive_steady_scenarios.py` and included in `--check`.
  - `kobo-daytime@2` windows and SoC verbatim for irradiance, residential and clinic. Start 55 %, 300 L, STOPPED, as `kobo-mill-midday`.
  - Mill, each with its `# source:` line: 06-08, 08-10, 10-12, 12-14 = 0 (`kobo-mini-grid-reserve-trial.yaml`, `mill-demand-1`); 14-16 = 18 and 16-18 = 3 (`kobo-mini-grid-evening.yaml`, `mill-demand-2`, `mill-demand-3`).
  - Label: "example data, the mill's pattern before the change (authored for this story: idle until 14:00 as in kobo-mini-grid-reserve-trial, afternoon as in kobo-mini-grid-evening; sun and other loads as kobo-daytime)".
  - R2's "reviewers diff against the parent" reads here: **the diff against `kobo-daytime` is exactly the six mill windows**, and L0 asserts that.
- **Rejected.**
  - **B (one profile everywhere, "not judged yet"):** see the branch below; it is not recommended.
  - **C (larger mill):** not a pattern change.
  - **D (show "Target missed"):** the data would be correct, but the claim false about what the example declares. It tells a client a working change failed.
  - **A conserved-energy shift:** fails on the whole-day metric (above).
- **If the owner picks "not judged yet" (branch B).**
  - All steady days are the `steady` kind. `mill-midday` is placed at **S-5**, the latest built full day, so it has no complete later days. Baseline is then S-9, S-8, S-6; there is no `steady-before*` kind and no `kobo-steady-before-mill`.
  - The screen reads "Not judged yet" and stays so while the look-ahead is open. **Three more added days would produce "Target missed"**, so the script adds at most two later Kobo days.
  - Size −0.25. CH-9b's stored-outcome path stays built and is not shown. F-THREADS (DD-1b2) expects the not-judged state. The owner's "keeps its 'Target met' check" (`owner-kobo-partial-days`) is then withdrawn by their own answer.
- **Story cracks to carry in the demo script (not code).**
  - S-7, S+0 and S+1 run the reserve-trial scenario, with the mill idle until 14:00 and story-only. S-7 falls after the mill change. On those days the day's productive energy reads 0.
  - S-1 and S-3 (`necessary-run`, 22 kW for 8 h) read about 168 kWh, and so do S-28 and S-21. These partly checked days are not in the verdict.
  - The honest answer: only fully checked days count, and those story days declare their own loads. They stay byte-equal (R5).
- **Backlog BL-23** (below): make the measure midday-only. Class: backlog. With all mill energy in daylight, no verdict changes; the script line above covers the wording.

### Q3. Placement: **accepted, E = S-9.** `mill-midday` on S-9.
- It is also the latest placement possible: anything later leaves fewer than 3 complete days after it (S-8, S-6, S-5 are the only ones after S-9 before the unbuilt S-4). This choice is by grade only, and it was made before the data, as R4 asks.
- Baseline S-13, S-12, S-11 (S-10 skipped as `missing`). Later S-8, S-6, S-5 (S-7 skipped as partly checked). It survives B-16.

### The Kobo list, `backend/conversions/demo-story-days-v3.json` (becomes `DEFAULT_FILE`; v1 and v2 kept)

| Day | Kind | Runs |
|---|---|---|
| S-28, S-21 | `normal`, `overcast` | unchanged, story-only |
| S-20 | `steady-before-first` | `night-early`, `kobo-steady-before-mill`, `before-rest` |
| S-19 to S-15 | `steady-before` | `night-early-after-before`, `kobo-steady-before-mill`, `before-rest` |
| S-14 | `overuse` | story-only |
| S-13 | `steady-before-first` | as S-20 |
| S-12, S-11 | `steady-before` | as S-19 |
| S-10 | `missing` | existing v1 entry |
| S-9 | `mill-midday` | as v2 |
| S-8, S-6, S-5 | `steady` | `night-early`, `kobo-steady-day`, `mill-rest` |
| S-7 | `overuse` | story-only |
| S-4, S-2 | no entry | NO_DATA |
| S-3 | `late`, as `normal` | story-only |
| S-1, S+0, S+1 | `normal`, `trial-before`, `trial-after` | story-only |

- That is 13 fully checked days, 6 partly checked, 3 with no data, inside `[S-20, S+1]`.
- **New files, all generated and in `--check`:**
  - `kobo-steady-before-mill` (above).
  - `kobo-rest-before-mill` (18-24, the same windows as `kobo-rest-mill`, start state measured at the 18:00 end of `kobo-steady-before-mill` on the registered Site).
  - `kobo-night-early-after-before-mill` (00-06, `kobo-night-early`'s windows, start state measured at `kobo-rest-before-mill`'s 24:00).
- **Reused:** `kobo-steady-day` is un-held (its HELD header goes) and `kobo-rest-mill` is reused. L0 asserts `kobo-steady-day`'s windows and start equal `kobo-mill-midday`'s, so its 18:00 state is the same one R16 measured.
- **Add a top-level `"mill_change_day": "S-9d"`.** L0, in `resolve` and `plan_add_day`: a `steady-before*` kind only before it, a `steady` kind only after it. A refusal uses `MILL_PROFILE_WRONG_SIDE`. This stops a live fill of S-10 from putting the "after" pattern on a "before" day.
- **`ADD_DAY_KINDS["kobo"]` gains `steady`, `steady-before-first`.** S-10 is filled with the second, because its predecessor is S-11 but the fresh start is the honest one for a live fill.
- **G0 (registered Site, `_shifted` drafter, before any v3 use).** The 18:00 and 24:00 states of `kobo-steady-before-mill` and `kobo-rest-before-mill`, the 06:00 end of the night, generator intervals per run, all recorded in `full_days`.
  - **Pass:** STOPPED at 18:00 and 24:00, 0 starts 06:00-20:00, and for `steady`, the 24:00 within R15's bound of `kobo-night-early`'s declared start.
  - **Fail:** stop and the Architect rules. No value changes. A `before` day that cannot be full removes the baseline, so it goes to the owner as branch B.

### Q4. **Accepted: S-4 and S-2 are not built.** The late day is not moved and the guard is not weakened.
- Building them is backlog (BL-25): no shown claim needs those two days.
- **Add to `plan_add_day`:** refuse a Kobo day next to a `late` entry with `LATE_IN_STREAM`. Today `add-day` would skip this check by minting its own epoch, so a live add on S-4 would produce a case nobody has tested. +0, one test. These days read "no data", which is true.

### Q5. **Accepted: Cold has no steady day.** Cold stays v1's 3 days.
- R14 and the owner's cold decision stand: a `cold-normal` day repeats its Finding, and no day is tiled. Re-deriving a `cold-steady` (the alternative) fails SCOPE-1, since it exists only so the board looks fuller.
- **DD-1b2's partial prepare and SCOPE-1's phrase become "Cold 3 story days".** R1's "Kobo and Cold 24 h" no longer applies to Cold.
- Saving is about 36 min of E3 (the builder's estimate, not measured); DD-1b2's rehearsal re-projects it.

### Q6. **Confirmed, with one correction.** Build B-22. B-16 applies only if the DD-1b2 rehearsal measures the whole prepare above **3 h** (`owner-build-time-2026-11-06`). The plan's "above 2 h elapsed" bullet is stale.
- **The fallback must exist as a switch, or it is not a fallback.** `prepare --baseline b16` drops every entry whose **resolved** offset lies in `[S-20, S-15]`. That includes an EV Tuesday that `weekday_offset` lands there. S-28 and S-21 stay. There is no second file.
- L0: with the filter, the MILL-3 days are unchanged. +0.

### Plan row `client-demo-plan.html:781` (and `:782`). **The builder is right, and the row is false in two claims, not one.** The coordinator applies this; the builder does not touch the plan.
- "The story week reads 7 of 7" is false. S-5 to S+1 is 1 fully checked (S-5), 4 partly checked, 2 no data.
- "MG-1 judged on 21 fully checked October days" is also false: 13 are fully checked.
- **`:781` "What the client sees" becomes:** "One normal week before the first overrun. Three weekly recurrences. 13 of 22 Kobo days fully checked; the generator and trial days read partly checked; S-10, S-4 and S-2 have no data. Cold shows its 3 story days. EV shows 3 Tuesdays."
- **`:782` becomes:** "The first overrun falls on the first day, so there is no normal history before the problem. 7 of 16 Kobo days fully checked."
- **DD-1b2:** F-THREADS reports how many days MG-1's verdict actually reads, and says so if that is not what the screen implies.
- The owner's B-16 answer carried the words "every day fully checked", which R16 and this list overtook. The coordinator tells the owner (see "Owner, informed").

### Q7. **Accepted: the after-overcast night pair is withdrawn.** R2's own fallback ("presents less") applies, and the owner delegated the night design to the Architect (`owner-kobo-nights`). DD-1a2 −0.25.
- **Lost:** the only night generator cost shown.
- **Removed:** `kobo-night-late-after-overcast`, `kobo-night-early-after-overcast`, `kobo-steady-afternoon`, `kobo-steady-dusk`, `kobo-night-late`.
- **Kept:** `kobo-steady-day`, un-held under (b). The `NIGHTS` table entry that `rest_document` reads stays, but it writes no file.
- **Tests to edit:** `host/tests/test_dd1a1_registered_kobo.py:40-44`, `host/tests/test_dd1a1_stream_probe.py:88`, and any fingerprint list `--check` names. The handover JSON's old probe entries stay as history.

### Q8. The five rules

1. **Steady day after a story-only or missing day: accepted.** A fresh declared start, 48.42 %, 300 L, STOPPED, which is `kobo-night-early` unchanged. There is no bound and it is reported per day as a real data gap. The kinds are in the table above.
2. **A steady day whose 24:00 is RUNNING:** never silently partly checked on this list. On G0 it is a stop, because these days carry MILL-3. Partly checked (the 06-18 run alone) applies only to an add-day (item 3).
3. **ST-7 add-day after S+1: accepted, with the gate.**
   - The kind is `steady`; `plan_add_day` expands it into its three runs through `_expand`, with `received_at` at DB now and each run's offset kept in order. +0.25.
   - **Gate:** one registered probe of the three runs on the Foundation with the 25 % reserve, as the trial chain applies it.
   - **Pass (STOPPED at 18:00 and 24:00, no Finding):** the day is full.
   - **Fail:** the kind on that side of S+1 runs 06-18 only and reads partly checked. The script says so, and no Architect return is needed.
   - **Class: demo-critical.** The live add is ST-7, and a live normal day should read like its 13 neighbours. The price is the +0.25.
4. **Degraded guard: reading confirmed.** Refuse any Kobo `degraded` entry and add-day regardless of `complement`, with only `DEGRADED_PROBE` passing. Update `test_demo_story_days.py:461-475`: `test_r10_no_shown_calendar_...` loses its `complement` clause. Cold's S-3 `degraded` is `cold-missing-probe`, not an outage cut, and stays allowed.
5. **The MILL-3 dry run (G2): allowed. It does not count as a demo prepare, on these terms.**
   - **Allowed:** `tools/dd1a2_mill3_dry_run.py` drives the Kobo child's existing build path for v3's S-14 to S-5 (10 days, S-10 stays empty) on the builder's own `*_test` DB.
   - **Barred:** the `tools/demo_combined.py prepare` parent; the finish rows; Cold and EV; any `assetops_polish_*` DB; the full-prepare test; `test_demo_combined_*` beyond the scoped ones. Any need to cross these is a stop.
   - Machine idle, one heavy job at a time. Start `tools/keep-awake-during-tests.ps1`. Cap at 40 min, twice the estimate. Past the cap, stop and report.
   - Then call `assess()` directly with an in-memory plan: `effective_day` = S-9, baseline chosen by `choose_days`. No Action is recorded (that is DD-1b).
   - Report to `.agent/DD-1a2-mill3-dry-run.json`: every R12 item, run sets, and the S-14 and S-7 Findings compared to the story-only build.
   - **Pass:** 3 COMPLETE each side, the later days' run sets contain `kobo-steady-day`, VERIFIED by the catalogue rule, and S-14 and S-7 have the same Findings, intervals, claims and money.
   - **Fewer than 3 COMPLETE days, or not VERIFIED:** R12 stop, report, never tune. The Architect rules, and if no honest fix exists, the owner gets branch B.
   - **A story Finding on S-14 or S-7 changes because of its neighbours:** the generator Findings win (R16). The next step is leaving the neighbouring steady days unbuilt. That shortens the MILL-3 windows, so the Architect re-rules with the owner's B option in view. Do not widen any product gate (BL-20).

### Accepted without change
- **Guard extension,** list-level checks in `resolve`, proved by mutation, closing `review-DD-1a1.md:108-110`: each full kind's complement list matches `full_days`; each 00:00 start matches the previous built full day's recorded 24:00 within R15's bound, unless item 1 applies.
- **EV `S-14d normal`.** A 4th Tuesday is reported, never moved.
- **S-10 `missing`** stays.
- **FILL-1's** five refusals, plus the test that `DAY_HAS_EVIDENCE` fires before provisioning (DD0c-R Q4).

### Tests
- **L0 (`backend/tests/test_demo_story_days.py`):**
  - v3 resolves on the table above; each full day tiles; S-4 and S-2 absent;
  - the `kobo-steady-before-mill` six-window diff; `kobo-steady-day` equals `kobo-mill-midday`;
  - `MILL_PROFILE_WRONG_SIDE`; `LATE_IN_STREAM` on add-day; degraded always refused;
  - `--baseline b16`; the guard mutations; the five refusals; add-day expanding to three runs.
- **L2 (`host/tests/test_dd1a2_registered_kobo.py`):** G0, G1, the R25 add-day probe, and one `add-day steady` end to end with real-time delivery and story-time readings.
- **Scoped as DD-1a1. Guards A, W, N, V, M.**
- **Carried into DD-1b2:** F-THREADS asserts MILL-3 and the G1 pass on the whole build.

### Scope and size (SCOPE-1)

| Item | Class | Reason | Size |
|---|---|---|---|
| Withdraw the after-overcast pair | removal | No legal place under R15/R16 | −0.25 |
| `kobo-steady-before-mill` chain and probes | demo-critical | Without a "before", the mill Action changes nothing and "Target met" cannot be true | +0.25 |
| Add-day expands to three runs, with R25 gate | demo-critical | ST-7's live day must read like its neighbours | +0.25 |
| G1, guards, B-16 switch, late check on add-day | demo-critical | Inside existing acceptance | +0 |
| BL-23 midday-only measure | backlog | No verdict changes on current data; the script covers the wording | 0.5 est. |
| BL-24 continuous days without the 06:00 start | backlog | Needs a site energy balance and Findings work; the disclosure covers the demo | not estimated |
| BL-25 late day inside a stream (build S-4, S-2) | backlog | No shown claim needs them | est. |

**DD-1a2 2.0 → 2.25. DD-1 +0.25 (10.25 at R16 → 10.5); the plan rows need it.** Branch B: −0.25, DD-1a2 2.0. BL-23 to BL-25 are the next free ids in this worktree and on `main` at this ruling. **Lane 1's Architect is also writing backlog rows, so whoever merges second re-checks the ids and renumbers.**

### Owner questions (ask together; the recommendation is the first answer of each)

**Question 1. "Normal days on the Kobo example."** "A sunny day at this example site doesn't put back what the night takes out. If we run normal days as one continuous stretch, the generator comes on around 5am and stays on until about noon, on a test copy about 22 litres a day. That isn't what you approved (about 0 litres). It would also very likely raise a 'generator ran longer than needed' problem nearly every day, against the handful the story is about, and show fuel going up after the mill change.
- **Each normal day starts at 6am from a set battery and fuel level (recommended).** Keeps what you approved: about 0 litres, and the same problems and money. It costs a visible jump in the battery line at 6am, with the generator stopping by itself, on each fully checked day. The mill day already does this, and a line on screen says so.
- **Continuous days.** Keeps a smooth line and true day-to-day fuel. It loses the 0 litres and likely changes the problems and costs shown. We'd measure it on the real example site first and come back to you."

**Question 2. "How the mill 'before' is written."** "The check on 'run the mill at midday' compares days before and after. Today the example's ordinary days already run the mill at midday, so there is no before, and the check would say 'Target missed'. Nothing was measured here; we write both patterns.
- **Write a 'before' pattern (recommended):** the mill idle until 2pm, then the late-afternoon pattern, both taken from other example days. Keeps 'Target met', as you were told. The check would read roughly 40 up to 110 kWh a day. We'd present it as example data and as more daytime use, not the same work moved, because the mill grinds more after the change.
- **No 'before':** the mill change shows 'Not judged yet'. It loses 'Target met', and adding three more days live would show 'Target missed', so the script avoids that. It is simpler, but the Grow story ends without a result."

**Does the build wait?** Yes for the scenario files, the day list and the gates, since both answers change them. The builder may meanwhile do the items that do not depend on them: Q7's removals, Q8.4, the late check, the B-16 switch, the EV entry. If the owner is in a delegated absence, the build proceeds on both recommendations and each is logged for owner review.

### Owner, informed (no decision)
- Kobo: 13 of 22 days fully checked, not "every day" as an earlier question said; S-4 and S-2 read "no data" in the story week.
- Cold: its 3 story days only.
- No night generator cost is shown (the after-overcast night is withdrawn).

### Handoff
Wait for the owner's answers, then: G0, the files and v3, G1, the R25 probe, G2, the scoped tests and guards. Stops are as ruled above; a stop returns to this Architect with its report.

## DD1a2-R2: G1 failed on "0 L" on the `steady-before` night: accept the measured litre, and say so (Architect, Claude, 2026-11-07)

- Input: `.agent/DD-1a2-handoff.md` at `215984add`, `.agent/DD-1a2-g1.json`, `.agent/DD-1a2-g1-control.json`, `.agent/owner-dd1a2-answers-2026-11-07.md`. The owner chose the 06:00 start and to write the "before".

### The report, checked

| Claim | Result |
|---|---|
| 0.973 L, generator 04:00-06:00 | **Confirmed**, probe `B-early` in `kobo-night-handover-v1.json:546-571`: start 45.26 %, end 299.03 L, 30.0 %, RUNNING. |
| G0 states (89.47 / 48.42, 86.32 / 45.26) | **Confirmed** in the same file. |
| 3 NECESSARY intervals, 0 Findings; control finds 2 | **Confirmed** in the two JSON files. |
| Money 0 rows on both | **Confirmed.** Money is unmeasured on this path. |
| 3.167 kWh "in evidence" | **Not in `DD-1a2-g1.json`.** That file predates the builder's fuel-field change. It has no `generator_kwh`, and its `fuel_used_l` reads 0 on every day, including S-12, which is the vacuous figure the builder later removed. **That file must not be cited for litres.** The 3.167 is unverified here, though it is consistent with 0.973 L. Regenerate it (below). |
| 7 days, about 6.8 L | The 7 days match the v3 table. 6.8 L is 7 × one probe, not measured as a sum. |

### 1. Option: **(a), keep the 7 nights as measured.** G1 stays recorded as a fail on that line, accepted by this ruling.

- **This does not redefine the gate.** The packet records: "G1: FAIL on 0 L for `steady-before`; accepted, DD1a2-R2". DD1a2-R said a G1 fail would likely mean the days cannot be full. That prediction does not apply: every join is STOPPED, the interval is NECESSARY, and there are 0 Findings. The only thing false is the "0 L" sentence, so the sentence changes, not the day.
- **(b) is rejected, and the bound stays at 0.5 pp.** A 48 % start after a day measured ending at 45.26 % is a declared value, picked because it removes the fuel. That is exactly what R2 forbids ("measured handover, never chosen"), and the bound exists to catch it. I see no honest reading of a 2.74 pp step here. `check_full_day_chains` is unchanged.
- **Branch B is rejected.** It is the route for days that cannot be full, and these can. The owner chose "write a 'before'".
- **The frozen pattern stays frozen.** The cause is the authored afternoon load, and it is not revisited now that a result is known.
- **Regenerate G1 (required, with handoff step 1).** Rerun through `host/tests/test_dd1a2_registered_kobo.py` with the current report and overwrite `.agent/DD-1a2-g1.json`. It must show `generator_kwh` per day and, for the 04:00-06:00 night, clinic and residential delivered equal requested (R3 check 1: nothing unserved; the battery sits at its reserve).
  - **Pass:** NECESSARY, 0 Findings, nothing unserved, litres as the probe. If the litre figure differs, `BEFORE_NIGHT_DISCLOSURE` takes the measured figure and the build continues.
  - **Fail (a Finding, a Candidate or Cannot-determine minute, or any unserved load):** stop and the Architect rules. No value changes.

### What the screen and the demo say

- **Screen: no new copy, and no litre figure is added.** No fuel signal reaches evidence on this Site (the builder's note, consistent with G1's signal list), so nothing shows these litres as a reading. The day's Cost row reads `COST_NO_MONEY`, "No fuel cost estimated for this day", because that row prices only time beyond need, from a Finding. Read from code: `mini.py:477`; confirm the shown text in F-THREADS. The night's source line already says it, through `BEFORE_NIGHT_DISCLOSURE`: "...the generator delivers energy and this night uses about 1 L of fuel."
- **Demo script, if asked:** "On the days before the mill change, the evening ends with the battery a little lower, so the generator comes on from about 4am and uses about a litre. It was needed, so no problem is raised and no extra cost is estimated."
- **Do not say** "the mill change saved a litre a day". The drop from about 1 L to 0 comes from the pattern we authored and the 06:00 start, not from a measured saving. **Do not say** "about 0 litres" of these 7 days.

### 2. Owner: **informed, no question; the build does not wait.**

The owner's choice was between about 0 L and about 22 L, and about 1 L on 7 days does not change which is better. The only other routes are a chosen number or losing "Target met". Line for the coordinator to send, with the right to overrule:

> "A correction to what we told you about normal days on the Kobo example. Most run about 0 litres before dawn, but the 7 days before the mill change use about 1 litre each, because the generator comes on from 4am. It was needed, so no problem is raised and no extra cost is shown, and the night's explanation says so. We kept the measured figure instead of changing the numbers. We also said money stays the same: that isn't proven yet. It gets checked on a test build and again on the final rehearsal, and we'll tell you before the full build if it differs. The new full days do add their own mill sales figures, which is expected. Tell us if you'd like this handled differently."

### 3. Money: proved in two named places, neither left vacuous

- **Why it is expected to hold (read from code, not proof).** A fuel consequence comes only from a Finding's Candidate span (`financials/fuel_cost.py:284-311`, `NO_CANDIDATE_TIME`), so a day with 0 Findings has nothing to price.
- **G2 (`MONEY-A`, DD-1a2).** After each build (`mill3`, `story-only`), run the same worker the prepare's ticks use (`--consequence-items`, `demo_combined.py:66`) until nothing is pending, then report the rows per local day.
  - **Non-vacuity:** the `story-only` control must give rows or a stated priced result for S-14 and S-7. If it gives none, the check is vacuous: say so in the packet, and do not claim it.
  - **Pass:** S-14 and S-7 equal between the builds, and no fuel-consequence row on any steady, `steady-before` or mill day.
  - **Fail (a row differs, or one lands on a steady day):** stop and the Architect rules.
  - **If it needs more than the worker call and the price seed the child already has (`demo_combined_kobo.py:138`):** do not build more here. Report it unproved in the packet, and `MONEY-B` carries it.
- **DD-1b2 F-THREADS (`MONEY-B`, always, on the whole build).**
  - Every Kobo fuel-consequence row traces to a Finding on a story day, and none lies on a steady day.
  - The Cost headline on one `steady-before` day and one `steady` day is reported as shown.
  - Each Grow figure reproduces from its rows (R12 item 2), which means the new full days' figures are stated, not assumed. Finish row WK-2a's S-1 figure (42.08 USD, `demo_combined_finish.py:527`) must stay equal, since S-1 is byte-equal.
  - **If MONEY-B differs from what the owner was told, they hear it before E3.**
- **Standing, +0, lane 1 (CH6b3-R2 in `build-sheet-CH-6.md`, once merged):** F-THREADS also reports every shown Kobo row state and fails on PRODUCER_NOT_SETTLED or a PARTIAL board.

### 4. `test_demo_combined_postgres.py:198`: **no change.**

- Line 198 reads the same default file that the test's prepare uses (`demo_combined.py:343`; that test file passes no `--days`), so the listed and resolved days agree on v3. EV's new `S-14d` fits the assertions by reading: the same count, the ruled weekday, and within the 7 days before the listed date. Not run.
- **Prove that part now without the barred test (+0):** L0 in `test_demo_story_days.py` resolves v3 on 7 consecutive values of S and applies the same weekday assertions.
- **The real consequence is cost, not line 198.** That test's fixture now prepares the whole of v3, about the same cost as E3. **DD-1b2 states how E2 runs it:** against the one E3 build, or pinned by `--days` to a shorter list. Any finish row it then breaks is DD-1b2's to fix. No change in DD-1a2.

### Size

**+0. DD-1a2 stays 2.25, DD-1 10.5.** All of this is inside existing G1, G2 and F-THREADS acceptance. Nothing goes to the backlog. SCOPE-1: both money checks are demo-critical, because the owner was told money stays the same.

### Handoff

Regenerate G1, then continue the handoff's order: R25 probe, L2 add-day, G2 with MONEY-A, the L0 above, the packet. The handoff's "Next" items otherwise stand.

## DD1a2-R3: review H1: the live day after the trial is `normal`, not `steady`; two owner corrections (Architect, Claude, 2026-11-07)

- Input: `.agent/review-DD-1a2.md` at `42a5d6ad6`. This is this Architect's last ruling in the lane. Nothing was run for it; the measurements are the reviewer's.

### 1. H1: **no product change. ST-7's live day is `normal` on S+2, and `add-day` refuses `steady` on that date by name.**

- **Reviewer's cause: confirmed in code.** `_day_states` applies the equal-facts rule only when given a `facts_window` (`actions/verification.py:553`), and later pins have none (per the review, `:702` and `:1093-1095`). `kobo-night-early` on S+2 starts S+1 21:00Z, inside S+1's UTC day, so S+1's selected run changes and `:564` reports "moved". Nothing re-binds it, so it never recovers.
- **What the demo needs (plan `client-demo-plan.html:592`, `:829`).** ST-7 is the closing step: one new day arrives and the board re-assesses on the next tick. With E3 on the session day minus 1, the day added is **S+2**. So the plan's own date is the failing date, and **option (b) alone fails**: S+3 needs the demo at least 2 days after the prepare, with S+2 reading no data. The open client date does not matter for this ruling: S+2 is the next free day on any session date at least one day after the prepare.
- **Why `normal`.** The reviewer measured it with the real chain: VERIFIED on all 3 ticks after the add. It is the existing `add-day` kind that ST-7 was built on, it needs no new scenario, and FILL-1's "named event kinds" already cover it. The added day reads partly checked, like S-1, S+0 and S+1 right beside it. **This reverses my Q8.3 reason** ("a live normal day should read like its 13 neighbours"): a "Verified" result staying true outranks a fully checked closing day. Its generator is needed throughout, and no Finding is expected (not measured here; the board check below reads it).
- **Rejected.**
  - **(a) Later pins get the equal-facts rule: not for this demo, backlog BL-26.** It is the honest fix for a real continuous Site, and it is small. But it changes what can keep an outcome VERIFIED, on the defended path behind the story's main verdict: a wrong facts comparison would hold "Verified" when readings really moved, and that error is silent. The demo does not need that risk.
  - **(c) `steady` 06-18 only:** a new untested kind that gives the same partly checked result as `normal`.
- **`steady` stays as built** for a live day from S+3 on (reviewer: VERIFIED on all 3 ticks with S+2 empty) and the `steady-before-first` fill of S-10. The R25 gate result stands for those days.

**Fix, for a fresh Sonnet builder (`task/DD-1a2-b22-day-list`).**
1. `tools/demo_story_days.py` `plan_add_day`: after the offset is resolved, if `site == "kobo"`, the kind has a `complement`, and the offset equals the `trial-after` entry's offset + 1 in `current`, raise `StoryDaysError("FULL_DAY_AFTER_TRIAL", ...)`. Message: "a full day here starts its night inside the trial's later day and takes the trial off Verified; use --kind normal (DD1a2-R3)". It must fire before any provisioning.
2. L0, `backend/tests/test_demo_story_days.py`: `steady` on S+2 refused with that code; `normal` on S+2 planned as one run; `steady` on S+3 planned as three runs. Mutation: remove the check and the first assertion fails.
3. L2, `host/tests/test_dd1a2_registered_kobo.py`, own `*_test` DB, about 5 min: the child's trial chain on S+0 and S+1; `plan_add_runs` and the child's `add_day` with `normal` on S+2; the prepare's tick 3 times. ACT-K1 reads VERIFIED through `VerificationService.current_state` before the add and after the ticks. Fail: stop and report.
4. Packet: correct `:18` (R25 plus L0 did not cover this), and correct `:46` to "price 1.25 USD, quantity 0 L: the generator delivers no power in the Candidate span". List H1's closure, and carry the script lines below under "Owed to DS-1".
5. Guards V, A, W, and the scoped story-day tests. A fresh Claude reviewer verifies H1's closure only.

**Owed to DD-1b2 / EX-1 (+0):** on a clone of the whole build, after the live `normal` add and its tick, read the board: Assure count, trial line and the Action's words unchanged, no new Finding. The reviewer's probe was two story days, read at the service.

**Plan, for the coordinator:** `:829` gains "the live step uses `normal` (DD1a2-R3)".

### 2. The two owner corrections: **informed, no question; the build does not wait.**

**(i) "A line on screen says so" was wrong, and that error was mine.** The text reaches only the Lab scenario pages, not the client screens where the jump shows.
- **The script explains it now (+0).** A note on the board's battery chart would be new copy on a shared screen, outside the mock-up, for a jump the owner has not yet seen. It goes on the walkthrough list as the owner's call, once they see it on screen.
- **It does not reopen their choice.** The alternative was about 22 litres a day and a problem raised on most days. The missing line does not make that better. The owner may still overrule.
- **Script:** "Each full example day starts at 6 am from a set battery level, so the line steps up there and the generator stops. Days aren't carried over; this is example data."

**(ii) MONEY-A shows no new cost rows, not "the same money".**
- **The price seed is not the cause (packet `:46` is wrong).** The rows carry 1.25 USD and 0 L. The trial Findings' generator delivers no power in the Candidate span and idle fuel isn't modelled, so 0 USD is computed. This is **already-decided behaviour, not a new defect**: `COST_ZERO`, "No fuel cost estimated: the generator was on but delivered no measured power" (`mini.py:64-65`, POLISH §1.1, R626 owner Q1), with idle fuel in BL-16.
- **Stated plainly: on the Kobo build the generator problem carries no fuel money figure.** The non-zero Kobo money is the Grow sales: WK-2a's 42.08 USD on S-1, and the new full days' own figures.
- **MONEY-B covers the non-zero money, confirmed:** each Grow figure reproduces from its rows, and WK-2a stays 42.08 USD (R2 §3). Add one assertion, +0: the fuel-consequence rows on S-14 and S-7 are PRICED with quantity 0, reported as such, so nobody reads them later as proof of equal non-zero money.

**Lines for the coordinator to send:**

> "Two corrections and one change on the Kobo example. First, we told you a line on screen explains the 6am battery jump. That was wrong: it only appears on an internal page. For now the presenter explains it, and you can decide whether it needs a line on screen when you walk through it. The 22-litre alternative isn't any better because of this, so we've kept your choice, but tell us if you see it differently. Second, the money check so far shows only that no new fuel cost appears. The generator problem days show no fuel cost at all, as you decided earlier, because the generator delivers no power in those hours. The real money figures are the mill sales, and those get checked on the final rehearsal before the full build. Third, the day added live at the end of the demo will be an ordinary generator day that reads 'partly checked', like the days right beside it. A fully checked day on that date would knock the trial off 'Verified', so the tool now refuses it."

### 3. Three revisions vs one: **confirmed, a script line; no separate walkthrough item.**
Finding counts, claim, minutes, thread counts and money are unaffected, and "Assessment updated; amount unchanged" is true. This answers the packet's question: accepted as expected. The cause is the reviewer's inference, not stored. The walkthrough will see it in passing.
**Script, if asked:** "The next day's readings overlap that day's window, so the system re-checked it. The result didn't change."

### Size and scope (SCOPE-1)
**+0. DD-1a2 stays 2.25, DD-1 10.5.** The refusal, its L0 and the L2 check are demo-critical: without them the closing step can take the story's main result off "Verified". **BL-26 (backlog, 0.5 est.):** later pins with the equal-facts rule. Only a continuous real Site needs it, and the demo avoids the date. BL-23 to BL-26 are free in this worktree and on main's list. Lane 1 may collide, so the second merge renumbers.

### Handoff
The fresh builder takes "Fix" items 1-5. A stop goes to a **new** lane-2 Architect, which reads this section, R2 and `.agent/review-DD-1a2.md`.

## DD1b1-R: rulings on the DD-1b1 pre-flight (Architect, Claude, 2026-11-07)

Binding checked: Claude (`.ai/ROLE_CONFIG.md` in this worktree, owner 2026-10-27). Input: `.agent/DD-1b1-preflight.md` at `74d092b24`. Nothing built or run; "read, not run" marks what the build must prove. **Where this differs from R6, R7, CH9b1-R2 or CH-9b `:187`, this section wins.**

**In one view**

| Q | Ruling |
|---|---|
| Q1 | (a). Cold and EV workers run on a story clock, on every prepare day. Add-day stays on wall time |
| Q2 | One rule per day: worker `received_at` + 5 min, work store + 6 min, Action + 10 min. The builder's single clock and EV 09:15 are refused |
| Q3 | (a) for ACT-003, and **ACT-002 also reads "Action agreed"**. R6's "APPLIED" is corrected |
| Q4 | (a). No migration, one L2 pin |
| Q5 | Owner **DD-1b2**, +0.75, with an order correction |
| Q6 | Refusal as recommended, on the seam that stays. The probe is not a demo prepare. `coh3_pairs` shares COH-3's own loop |
| Q7 | Objectives: one instant. **Publication seam goes to backlog (BL-30).** R6 overrides R645; owner informed |

**Size: DD-1b1 stays 1.25. DD-1b2 1.5 → 2.25. DD-1 10.5 → 11.25. Lane 2 remaining (DD-1b1, DD-1b2, CH-5d1): 3.75 → 4.5.** No owner question. **The build does not wait.**

### Builder's claims, checked

| Claim | Result |
|---|---|
| Finding pin needs a revision and selection known by `command_now` | Right. `finding_revision` is "created by `command_now`" (`postgres_domain_intent.py:85`), and the mill's `opportunity_revision_selected` is the same (`:120-128`) |
| Workers default to wall time | Right (`test_w206 :78-81`, `test_w203 :78`) |
| `select_exact` may not follow the clock | **Settled: it does.** `_project` passes `self.clock()` to `ev_persist` (`assessment_worker.py:333-334`) and `selected_at` is that value (`postgres_assessment_store.py:803`). Only `select_exact`'s own worker needs the clock |
| Triggers already pass `decided` | Right (`0025 :365,371,378,438`, `0029 :258`). A fresh read of `assetops_polish_full_test`: `cold_chain`, `ev_charging`, `mini_*` and `dispatch` `available_at` are story dates; only `mini_opportunity` (4 rows) is 2026-11-02 |
| EV "decision seam = `received_at`" (Q7) and worker "`received_at` + 5" meaning 09:10 (Q1/Q2) | **Wrong for EV.** The day's `received_at` is 09:30 (`demo-story-days-v3.json`); the decisions are 09:00 and 09:05 (`test_w205b :113-114`). See Q2 |
| ACT-002 carries APPLIED | **True only with the builder's single clock, and then the screen is wrong.** See Q3 |
| No tool records the mill Action | Right. But an owner was already named, twice and inconsistently. See Q5 |

### Q1. **(a).** Demo-critical; R6 cannot be met without it.

- **Cold (`demo_combined_cold.run_day`):** when the story clock is on, swap `P.run` so `produce` calls `test_w203_cold_replay_postgres.run(built, clock=lambda: worker_at)`. It applies to every Cold day built by `build`.
- **EV (`demo_combined_ev.run_day`):** call `run_worker(built, build_ev_assessment_worker(url, clock=lambda: worker_at))`, and swap `test_w206_ev_store_postgres.build_ev_assessment_worker` process-locally so `select_exact` gets the same clock. Dispose the worker yourself; `run_worker` disposes only its own.
- **All prepare days, not only the failure and fault days.** A story-dated S+0 beside a build-dated earlier occurrence would order one thread's causes across two clocks.
- **`add_day` passes the story clock off.** Its `received_at` is DB now, so + 5 min would stamp a selection in the future and hide it from live reads. Add-day stays byte-unchanged.
- **Standalone w502 and w504 are unchanged.**
- **Stop, do not patch, if** `P.enqueue_window` fires on a built day (its job has `available_at = now()`, so a story clock never leases it), or if `doc["blocked"]` is non-null after the failure day.
- This changes `created_at` and `selected_at` on those rows from build to story time. That is the intent: CH-6b2's "cause known after the evidence cutoff" stops applying to them. Any finish row or capture this moves is DD-1b2's.

### Q2. **One rule for both Sites, from the day's own `received_at`.**

| Step | Instant | Cold S+0 | EV fault Tuesday |
|---|---|---|---|
| Evidence decided | existing | 17:05 | 09:00, 09:05 |
| `received_at` | existing | 17:05 | 09:30 |
| `worker_at` | `received_at` + 5 min | 17:10 | 09:35 |
| Work store clock (cases, records, events, visits, plans) | `received_at` + 6 min, then + 1 s per command | 17:11:00 | 09:36:00 |
| Action `raised_at`, then domain store clock (Action, links, intent) | `received_at` + 10 min, then + 1 s per command | 17:15:00 | 09:40:00 |

- **Two clocks, not one.** They are the two existing seams: `PostgresWorkStore(test_db_clock_override=)` and `PostgresDomainIntentStore(test_db_clock_override=)`. Why is Q3. The work store still validates Finding links against the worker's selection.
- **Assert in the child:** the last work-store instant < the Action instant. Stop if not.
- **EV 09:15 is refused.** It precedes the day's own `received_at`, and it needs a Site-specific rule. All instants above are after the evidence.
- **`occurred_at` values do not move** (Cold 16:11-16:42; visits and plans). Story reading: the visit happened during the failure and was logged once the readings were in; the follow-up was agreed minutes later. No screen or script claims the gap.
- **`raised_at` hook.** In `tools/w502_cold_work_walkthrough.py` `BUILD`, in the `DEMO_NARRATIVES` pattern: `raised = globals().get("DEMO_ACTION_AT") or k0.known_at + step`. The child sets `DEMO_ACTION_AT` and swaps `test_w502_domain_intent_postgres.now_utc` to the domain clock before the `exec`; the first read returns the Action instant, so `raised <= db_now` holds. EV: swap `W._db_now` to the same clock. Restore every swap, as `_restore` does.
- Swaps of `work.composition.build_work_store` and `build_domain_intent_store` stay process-local and in the children. Composition still passes nothing.

### Q3. **(a) for ACT-003. ACT-002 also ends ACTION_IN_HAND ("Action agreed"). No new story content.**

R6 says "with their APPLIED and case causes". Everything about what the client sees says otherwise:
- plan `:811`: "ACT-002 reads 'Action agreed'. EV: the same with ACT-003"; ST-4 and ST-5 (`:589-590`): "in hand"; `build-sheet-CH-3.md:20`: both ACTION_IN_HAND; MD-0 ACT-E1;
- mock `:336` shows the Action "Open", and `:604-610`: "Activity completed", "Witnessed auto-start test: Missing", "Completion proves the inspection happened";
- the record itself says "witnessed automatic-start test remains required" (`w502` BUILD).

**What the builder's single clock would do (read, not run).** `cause_order` is known-time order (`lifecycle.py:186`). The Action at 17:15:00, then COMPLETE recorded after it, gives ACCEPTED then APPLIED, so CHANGE_APPLIED effective S+0 from the 16:42 `occurred_at`. The S+0 board would then read "Change made", for work done before the Action existed, on an Action whose own record says it is not done. `outcomes/status.py:75` stops counting an applied primary signal, so the row can lose Needs attention, and `claims.py:35` stops counting the thread as disrupting. Story cutoffs hide this today only because the causes are build-dated (`review-packet-CH-3.md:329-333`, listed there "for the DD-1 inventory"). R6 would have exposed it.

**The fix is the record order; no product change.** With Q2's clocks, COMPLETE is known at 17:11, after the thread's OPEN (17:10) and before ACCEPTED (17:15):
- APPLIED is judged from OPEN and skipped `ILLEGAL_TRANSITION`; ACCEPTED then gives ACTION_IN_HAND;
- on a rerun the same cause is `BEFORE_HEAD`, so a rerun writes nothing (`lifecycle.py:252-266`).

That is also the true rule: a completion before the Action cannot be the Action's change.

**Kept:** WR COMPLETED on Maintenance and on the Action detail, the case link, the intent basis, and the third-visit notice, untouched.

**R6 and the acceptance now read:** ACT-002 and ACT-003 are recorded at story time. ACT-002 keeps its linked case, and its COMPLETE is recorded at story time and applies no change. Both threads read ACTION_IN_HAND on their day.

Class: demo-critical (a false "Change made" on a client screen), +0. **Backlog BL-31:** a real later "Change made" for Cold and EV (Q3(b), and MD-0's ACT-C1 pattern). It is new shown content, and no script line needs it. Change made is shown on Kobo and the mill.

### Q4. **(a). No migration, no trigger edit.**

- L2, own `*_test` DB: for one EV and one mini row, `available_at = created_at = decided_at` with the ledger's decision override set; DB time with it unset.
- R7's third item is withdrawn. R7's aim, "studies carry story time", is not reached through this seam.
- Opportunity studies stay a declared R4 build-time fact (BL-32), **except the one study the mill Action pins**, which is DD-1b2's (Q5).

### Q5. **Owner: DD-1b2. Demo-critical, +0.75.**

The record: CH9b1-R2 names DD-1b2 ("recorded before R8 step 1", +0); `build-sheet-CH-9b.md:187` says "DD-1b1 calls" the freeze; CH9b3-R Q9 and Q11 say "DD-1b". **CH9b1-R2 stands as the owner. `:187`'s "DD-1b1" is corrected to DD-1b2.** The +0 was wrong: no part of this exists, as the builder found. Without it, ST-3's Grow story, F-THREADS and MILL-3 have nothing to read. DD-1b1 builds none of it and adds no stub.

DD-1b2 gets this at **+0.75** (its pre-flight confirms the seams; all read, not run):
1. **One step, `tools/demo_combined_mill.py`, run by the parent as a child. It must run after all three Site children.** `next_action_no` is the shared `action_code_seq` (`postgres_domain_intent.py:118`), so running it inside the Kobo child would take ACT-000002 and renumber Cold and EV against ST-4 and ST-5. It takes the next code after them.
2. **It must run after backfill step `a` and before `b,c,d`, which corrects CH9b1-R2's "before R8 step 1".** The freeze chooses baseline days from snapshot rows (`test_ch9b2_midday_plan_postgres.py` `_snap`; the DD-1a2 dry run also runs step `a` first), and step `a` builds those. The mill Action is then linked by step `c`.
3. **The story-dated study (Q4(b), this one only):** the study for the days before S-9, in process, with the existing `test_clock_override`, `test_lease_clock` and worker clock. The instant is after the last built day before `mill-midday`. So `opportunity_revision_selected` holds at the Action's `command_now`.
4. **The record, in story time, in Action-first order:** Action, case, record, COMPLETE before S-9's midday, link, `freeze_domain_plan`, then `evaluate_domain_plan` over the later days. Unlike ACT-002, here ACCEPTED must be known before COMPLETE, so that it reaches CHANGE_APPLIED. F-THREADS and MILL-3 assert this as already ruled.

### Q6. **Refusal as recommended. The probe is allowed. `coh3_pairs` shares the loop.**

**Refusal.**
- New `backend/assetops_backend/prepare_clock.py`: `require_prepare_database(url)`. The database name comes from `sqlalchemy.engine.make_url`, against `^assetops_polish_.*$|^.*_test$`. Otherwise it raises `PrepareClockRefused` with code `PREPARE_CLOCK_REFUSED`, naming the database. Composition never imports it.
- `PostgresObjectiveStore(url, *, test_recorded_clock_override=None)` calls it at construction when the override is set. The SQL fragment is literally `clock_timestamp()` when unset, `:recorded_at` when set.
- The children call it where they switch the story clock on. Existing `test_*` overrides are not edited.
- L0: `assetops_polish_x` and `foo_test` pass; `assetops`, `assetops_polish` and `assetops_demo3_x` refuse; a refused construction opens no connection. L0: with the override unset, the statement text contains `clock_timestamp()` and no new parameter.

**`coh3_pairs(bundle)`.** One generator beside `coh3_action_on_board`, yielding `(site_code, day, action_id, finding_id, linked)` for the pairs passing its existing condition. `coh3_action_on_board` is rewritten over it, so the count cannot drift from the rule; its findings stay identical. `test_chain_coherence.py`: a pair linked, a pair not linked (finding), and an Action after the window (no pair). Mutation: invert the window test and a test fails.

**The probe, `tools/dd1b1_coh3_probe.py`: confirmed, not a "demo prepare", on the DD1a2-R Q8.5 terms.**
- **Allowed:** the children's `run_day` for Cold's `failure` day and EV's `fault` day only, on the builder's own `pg_harness.fresh_database()`; `backfill --steps a,b,c,d`; at most 3 ticks; the board and index reads; `chain_coherence.collect`.
- **Barred:** the `tools/demo_combined.py prepare` parent; finish rows; Kobo; any `assetops_polish_*` or `assetops_demo3_*` DB; the full-prepare test.
- Machine idle, one heavy job, `tools/keep-awake-during-tests.ps1`. **Cap 20 min; past it, stop and report.**
- **Report to `.agent/DD-1b1-coh3-probe.json`. Pass means all of:**
  - `coh3_pairs` ≥ 1 for COLD-LAB-001 and for EV-LAB-001, with 0 COH-3 findings;
  - both Actions' `raised_at` and `recorded_at`, COMPLETE's `recorded_at` and each Finding's `created_at` at the Q2 instants (the +1 s steps allowed);
  - the Cold start-failure and EV interruption threads ACTION_IN_HAND; ACT-002's APPLIED appears in lifecycle `skipped`; a further tick writes no thread event;
  - each S+0 board's `in_hand` lists the Action; the Cold Protect row is `NEEDS_ATTENTION`;
  - WR COMPLETED, and `doc["blocked"]` null.
- **Fail:** stop and report. Never change the product, a clock or a threshold to pass it. A real COH-3 finding, or CHANGE_APPLIED on Cold, comes back to this Architect.

**Scoped checks:** the above; `test_demo_story_days.py`; `test_ch1b_*`; `test_s6_verification_replay*`; `tools/checks/test_chain_coherence.py`; guards A, W, N, V, M. Not `test_demo_combined_*`, not the suites. F-COH3 on the whole build stays in DD-1b2.

### Q7. **Objectives: one instant. Publication: backlog. R645: overridden.**

**Objective seam, demo-critical.** A past-cutoff read must show the target that existed, or the same day's verdict differs by read (`current(known_at)`, `postgres_objective_store.py:167-171`).
- **All fixture lines at one instant: `ev.install_at` + `TARIFF_AFTER_INSTALL`, which is S-26d 07:00**, the first moment all three Sites exist. It is a fixed value from existing facts. The per-Site offsets and "MG-1 alone" are refused: `declare_objective fixture` is one call with one store, and mixed dates on one board help nobody.
- New `tools/demo_declare_objectives.py <url> <file> <iso>`, calling `declare_objective.main(["fixture", "--file", file], store=PostgresObjectiveStore(url, test_recorded_clock_override=...))`. `demo_combined.finish` calls it through `self.py` at the same place, under the same guard, with the same stdout, so `objectives.json` is unchanged in shape.
- Assert the instant is earlier than the first built day's start across the Sites; stop if not.
- L2: set: `recorded_at` is the instant, a `known_at` read before it shows none and after it shows the line. Unset: DB time, and a live read is unchanged.

**Publication seam: not built. Backlog BL-30.** Nothing shown or cut off reads this date: `source_provenance.py:6` reads no date; the ledger's other uses are `ORDER BY p.recorded_at` inside one run (`postgres_evidence_ledger.py:1096-1100`) and an idempotent replay. It fails the SCOPE-1 test, and it would need a third seam and an EV-specific value. It stays a declared build-time fact. This reduces R7. **Build check:** grep routes for `evidence_publication`'s `recorded_at`; if any response carries it to a client, stop and report.

**R645: R6 overrides it. Confirmed, and it is not an owner question.** R645 was a recorded data reading, "Backdating is refused: the Finding revisions are recorded at build time", and Q1 removes that cause. The change goes toward what the owner was told (plan ST-5 "ACT-003 is visible as in hand", MA-1 M6, mock `cold` and `ev` rows), and the owner's walkthrough of this dataset has not happened.
- The builder updates the comment at `demo_combined_ev.py:162-164` and the docstring's "raised at DB now", and marks register row R645 closed by DD-1b1 in `.agent/mock-departure-register.md`.
- `POLISH-runbook.md` line 49 is history. The script line is DS-1's. Finish rows and captures expecting the old state are DD-1b2's.

### Scope and size (SCOPE-1)

| Item | Class | Reason | Size |
|---|---|---|---|
| Cold/EV worker story clock (Q1) | demo-critical | R6 is refused without it | +0.25 |
| Two-clock record order (Q2, Q3) | demo-critical | Keeps a false "Change made" off the screen | +0 |
| Trigger work replaced by one L2 pin (Q4) | removal | Premise was wrong | −0.125 |
| Publication seam (Q7) | backlog, **BL-30** | No reader of the date | −0.125 |
| Probe, `coh3_pairs`, refusal helper | demo-critical | Inside R6/R7 acceptance | +0 |
| Mill Action step and its study (Q5) | demo-critical, **DD-1b2** | ST-3, F-THREADS, MILL-3 have nothing to read otherwise | +0.75 on DD-1b2 |
| Later "Change made" for Cold and EV | backlog, **BL-31** | New shown content | 0.5 est. |
| Other opportunity studies at story time | backlog, **BL-32** | No shown date, Action or cutoff needs them | 0.25 est. |

**DD-1b1 acceptance, replacing line 117 (with SCOPE-1):** ACT-002 and ACT-003 recorded at story time per Q2, both threads ACTION_IN_HAND; ACT-002's case linked with COMPLETE recorded and no change applied; COH-3 evaluates at least one pair per Cold and EV board, proved by the Q6 probe; the objective override refused outside `assetops_polish_*` / `*_test`, and the children's clocks behind the same check; unset leaves product behaviour byte-unchanged (L0 text, L2 reads); add-day unchanged; the Q4 pin; R645 closed.

**Owed to DD-1b2 (+0 beyond Q5):** `expected-threads.json` and F-THREADS expect ACT-002 and ACT-003 "Action agreed"; `expected-today.json` I-09 reconcile; finish rows and E2 effects of story-dated Cold and EV rows; the Protect "Why?" now naming both Cold threads.

**Plan, for the coordinator:** DD-1b1 1.25 with R7 reduced; DD-1b2 2.25 (mill step, Q5); DD-1 11.25; lane 2 remaining 4.5; the R6 phrase at the handoff's `:58` and `:227` is corrected by Q3. Plan `:811` and ST-4/ST-5 stand as written.

### Owner, informed (no decision; the build does not wait)
- "The GreenHarvest and Depot actions now show on their failure-day boards as 'Action agreed', as the plan says. The GreenHarvest inspection shows as completed and the witnessed start test as still to do. We won't show 'Change made' there, because that inspection happened before the action was agreed."
- "Recording the mill action was never built, and the last data step now includes it: 0.75 more, for 4.5 left on this lane. Without it the Grow story has nothing to verify."

### Handoff
The builder resumes on `task/DD-1b1-story-time-actions`: Q6's helper and L0s; Q1 and Q2's child swaps and the BUILD hook; `coh3_pairs`; Q7's objective seam and tool; Q4's pin; the probe; scoped checks; the R645 records; packet. Stops come back to this Architect. Own review.

## DD1b1-R2: the Q6 probe failed; one read fix, whole-day links, per-Site objective instants (Architect, Claude, 2026-11-07)

Input: `.agent/DD-1b1-coh3-probe.json`, `.agent/review-packet-DD-1b1.md` at `131f18e86`, the probe's bundle, and the code. **This section wins over DD1b1-R where they differ.** The misses were this Architect's, not the builder's: DD1b1-R Q6 expected a pair without tracing the board's read windows, Q7 did not check Kobo's first day, and "reads Action agreed" named the wrong screen. The builder stopped correctly and tuned nothing.

**Size: DD-1b1 1.25 → 1.5 (+0.25, demo-critical: ST-4 and ST-5 cannot be shown truthfully without it). DD-1 11.5. Lane 2 remaining on the DD1b1-R basis: 4.5 → 4.75.** No owner question. **The build resumes; it does not wait.**

### 1. What the client must see, and why no window reaches it today

**Requirement (ST-4, ST-5, MA-1 M6, mock `:336`).** On the story-day board the client sees, together: the Finding; Protect at Needs attention; the Action under "Already in hand", state **"Open"**, with no "outside this view" suffix. "Action agreed" is the thread's word, on the Site chain (`chain_site` carries it; the board bundle has none). The board's "Open" is the mock's own badge and `board.py:865`. So plan `:811` is met on the chain, not by the board row. No label changes.

**What the demo opens.** `story_links` (`demo_combined.py:237-262`): Cold `/sites/COLD-LAB-001?from=16:00&to=17:05`, EV `/sites/EV-LAB-001/ev?from=08:00&to=09:00`, each the day's event window. The finish rows read the same (`Ctx.window`). **The COH-3 collector reads something else for Cold**: the Site-local day (`day_windows`).

**Why no window works (code; EV and Cold's local day are also observed in the probe).** The Action index selects `raised_at` in `[lo, hi)` (`postgres_domain_action_index.py:74-77`), and the composers call it with their `hi`.
- **Event found in the window:** `compose` passes `read_hi` = the event's end as `hi` (`read.py:384-389`), whatever was requested. An Action follows its evidence, so `raised_at` ≥ `hi` always. The Finding shows and the Action never does. The week link has the same defect.
- **No event found:** Findings are read over a window with no selection. The Action lists, as "outside this view", and the Finding does not.

**S1 answered: `received_at` was not the wrong anchor.** No instant after the evidence can pass, and the board's `known_at` is not what excludes the Action. Moving the Action inside the event is **refused**: it would claim the Action before its Finding existed. **Q2's instants stand unchanged**, proved by the probe.

**Options**

| | Change | Client sees | Cost |
|---|---|---|---|
| **A. Ruled** | The board's Action read runs to the **requested** window's end; Cold and EV story links open the whole UTC day | Finding and Action together; Needs attention; the lead names the event's own time (CH6b1-R5). An event-only window still lists no Action | +0.25 |
| B | In hand reads by thread, whatever the date | The same, and also on event-only windows and on boards before the Action | About +0.5 and a new as-known rule. Not demo-critical; BL-38 |
| C | Drop COH-3 for these boards; no product change | Finding and no Action on the board; the Action only on Work › Actions; "Action agreed" on the chain. R645 stays. ST-4 and ST-5 are false and the plan and owner line change | 0, but it presents less than was told |

**Why A is right beyond the demo.** On any real Site an Action follows its event, so today a week board can never list it. CH6b1-R3 already says the board's window stays the requested one; only this read drifted to the event. Nothing outside the requested window is read.

### 2. The build (A), and the corrected values

**Product, one read.** `read.py` `compose` passes `actions_to=hi` to the composer when `event` is not None. `cold.compose` and `ev.compose` take `actions_to: datetime | None = None` and call `ports.domain_actions(work_lo, actions_to or hi)`. With no event the call is unchanged. Plans, incidents and visits keep `hi`. Mini is untouched.

**S1, S2 windows, by rule: a Cold or EV story day's board is its whole UTC day, `[00:00Z, next 00:00Z)`.** It is the existing no-event form in `story_links`, and the only day form the estate read accepts (`estate/scope.py:108-110`).
- Probe days: EV `2026-11-03T00:00Z` to `2026-11-04T00:00Z`, containing 08:00-09:00 and the Action at 09:40; Cold `2026-11-05T00:00Z` to `2026-11-06T00:00Z`, containing 16:00-17:05 and 17:15.
- `story_links`: every Cold and EV dated day uses it (labels keep their kind), and `LINK_FORMS` stands.
- `chain_coherence.day_windows`: Cold and EV `from`/`to` are that day, `estate` the same. Kobo is unchanged. COH-3's rule is unchanged, `created <= to`.
- **Refused:** a local-day Cold link. It falls back (`EstateRefusal`) unless the estate rule is widened, and BL-20's rule stands.
- `demo_combined_finish.Ctx.window` is **not** changed here. Rows that need the Action move to the day window in DD-1b2.

**S3, by rule: each Site's lines at that Site's own first declared knowledge instant. This reverses Q7's "one instant".** That Q7 reason was wrong: `declare_objective fixture` already takes `--site`, and one date per Site is not mixed dates on a board.

| Site | Rule | Value | First built day |
|---|---|---|---|
| KOBO-001 | `price_recorded_at` (install + 1 h) | S-29d 12:00 | S-28d |
| COLD-LAB-001 | `install_at` + `TARIFF_AFTER_INSTALL` | S-26d 06:30 | S-7d |
| EV-LAB-001 | `install_at` + `TARIFF_AFTER_INSTALL` (its tariff instant) | S-26d 07:00 | S-14d, moved to its Tuesday |

- `objectives_instant` becomes `objectives_instants(story) -> {site_code: instant}`, asserting per Site that the instant is before that Site's first built day, else `OBJECTIVES_INSTANT_CONFLICT`.
- `demo_declare_objectives.py <url> <file> <site> <iso>` is called once per Site through `self.py`; `objectives.json` holds all the lines in the same shape. Update the L0s.

### 3. The control: **no story-clock-off run. Read the same database three ways, inside the re-probe.**

A story-off run costs another build and a new flag, and it proves less. On the one story-clock DB, read Cold's board over:
1. the UTC day;
2. the event window `[16:00, 17:05)`;
3. the local day `[21:00Z, 21:00Z)`, for the record.

**The attribution is (2).** Its `known_at` stays 17:05 and the Finding is 17:10. Finding shown: the window was the cause and `known_at` is cleared (leading reading now: the logged `EstateRefusal`; a build-dated Finding was also after 17:05 and shown on this window in the finish rows; EV shows a 09:35 Finding at `known_at` 09:00). **Finding absent on (1) and (2): the story clock hid it. Stop and return here; only then is the story-off control named.**

### 4. R645: **the reversal stands, conditional on the re-probe.** Keep the register row open until it passes; then close it and correct the `demo_combined_ev.py` comment.

**Corrected owner line, replacing the one sent:** "Correction to what I told you: this isn't proved yet. A retest is coming, after a small fix. Boards stopped looking at the end of the event, so an action agreed afterwards never appeared. With the fix, each GreenHarvest and Depot story-day link opens the whole day and shows the problem together with its action, marked 'Open'. 'Action agreed' appears on the Site's chain, not on the board row. The GreenHarvest inspection still shows completed, with the witnessed test still to do. No decision needed."

### 5. The re-probe, the cheapest honest proof

The same `tools/dd1b1_coh3_probe.py` on its own routed `*_test` DB, Q6's terms and bars. **1 tick instead of 3** (0 thread events are proved, and DD-1b2 repeats it on the whole build). About 3 min, cap 20.

**Pass, all of:**
- UTC-day boards: `coh3_pairs` ≥ 1 for each Site, 0 COH-3 findings; Protect `NEEDS_ATTENTION`; the Finding in `issues`; the Protect row's `in_hand` lists the Action, state "Open", no suffix;
- `chain_site` for each day carries "Action agreed";
- event-window boards: the Finding shown, and the Action **not** listed (recorded as the rule);
- every instant and state check that already passed;
- `objectives_instants` resolved on real v3 passes all three Sites, with no prepare.

Any other result: stop and report.

**New tests.** L0 for both composers: event inside a wider window: Action after the event and inside the window listed; Action after the requested end not listed; no event: arguments unchanged. Mutation: drop `actions_to` and a test fails. `test_demo_combined_links.py` and `test_chain_coherence.py` for the day form.

**Then, as the handoff lists:** mutation proofs, `test_ch1b_*`, `test_s6_verification_replay*`, add `test_ch6b1*` and `test_ch6b2*`, guards A, W, N, V, M. `demo_declare_objectives.py` per Site runs end to end on the probe DB, for that part only. Add-day stays by construction, and its run is DD-1b2's.

### 6. Scope

| Item | Class | Reason | Size |
|---|---|---|---|
| `actions_to`, day links, collector, per-Site objectives | demo-critical | ST-4 and ST-5; a full prepare stops at finish without S3 | +0.25 |
| Board in hand by thread, for any window (B) | backlog, **BL-38** | Day and week links show the Action; exact-window reads are not in the script | 0.5 est. |

**Owed to DD-1b2 (+0):** finish rows needing the Action read the day window; any in-app link carrying an exact event window that the script follows is listed and either avoided or stated; COH rules on the new Cold and EV day windows reconciled with `expected-today.json`.

**Plan, for the coordinator:** DD-1b1 1.5; DD-1 11.5; lane 2 remaining +0.25; plan `:811`'s "reads 'Action agreed'" is the chain, and the board reads "Open".
