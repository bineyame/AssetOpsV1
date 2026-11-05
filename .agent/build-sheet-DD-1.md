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
- **Lane-2 order:** CH-9b3 no longer needs CH-6a3, so the conditional order is gone: CH-9b1 → CH-9b2 → CH-9b3 → DD-1a1 → DD-1a2 → DD-1b1 → DD-1b2 → CH-5d1.
- **DD-1 total: 7.25 → 6.5.**
