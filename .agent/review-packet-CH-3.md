# Review packet: CH-3 thread lifecycle and feedback

- Branch `task/CH-3-lifecycle`, worktree `AssetOpsV1-ch3`. Head: see the final commit on the branch (this packet's commit).
- Sheet: `AssetOpsV1-plan2/.agent/build-sheet-CH-3.md`. Rulings: plan row CH3-R (Q1-Q6, build questions phases 1 and 2) and the §4.1 L3 ladder (settle step).
- Earlier records: `.agent/CH-3-phase-1-handoff.md`, `.agent/CH-3-phase-2-handoff.md` (anchors and the first clone runs).
- Not merged. User review: none required by the sheet. Architect attention is needed on deviation **D-e** (COH-13 on the clone).

## Outcome delivered

- **Lifecycle core.** A pure state machine with segments by story time (`chain/lifecycle.py`) and `run_lifecycle` (backfill step d, plus the `chain_threads` tick fallback) are written through the CH-2 store under its advisory lock.
- **Board and Portfolio.**
  - Both read the thread state (Q2/Q3/Q4).
  - The board shows the four thread lines and the I-11 trial scope.
  - Money is credited only from a priced total, so today it reads "No money credited · modelled, not saved".
  - The Portfolio adds `verified_resolution_count` and `priority_site_count`.
- **D-b, bitemporal visibility (this phase).**
  - Migration `0045_thread_known_at` (down_revision `0042_chain_threads`) adds `finding_thread_event.cause_known_at` and `finding_thread_occurrence.source_known_at`. Both are nullable and written at insert.
  - Visibility is `coalesce(cause_known_at, recorded_at) <= k`. It is applied in `lifecycle.visible`, the `LOOKUP` E rows (`at2`) and the occurrence-start SELECT.
  - The board again honours its resolved cutoff (Q3). The interim "request `known_at` only" rule is withdrawn.
- **Coherence.**
  - Added COH-13 (lifecycle agreement, time-zone free), COH-14 (a verified thread is not attention) and COH-15 (Action segment).
  - `collect` stamps `lifecycle`. On a stamped bundle, a missing `state_day` or `action_segment_no` fails COH-0 style.
  - Added the additive Portfolio key `action_segment_no`.
- **Settle step.** `tools/chain_clone.py settle <name>`:
  - runs ONE `demo_combined.TICK`, then the serve's Kobo performance step, on the clone only;
  - uses this worktree's code, captures its output itself and writes no file;
  - never reads or writes the work dir. The tick reads nothing from it; serve only logs into `logs/` there.

## Files materially changed (this phase)

- `backend/migrations/versions/0045_thread_known_at.py` (new).
- `backend/assetops_backend/chain/`: `lifecycle.py` (`Event.known_at`, `Cause.known_at`, `visible`), `lifecycle_run.py` (cause times; policy via composition), `threads.py` (plan and memory twin), `lookup.py`, `composition.py` (`thread_lifecycle_policy`), `adapters/postgres_thread_store.py`, `adapters/postgres_thread_sources.py`.
- `backend/assetops_backend/site_outcomes/read.py` (Q3 cutoff restored); `estate/portfolio.py` (`action_segment_no`); `frontend/src/estate/estateClient.ts` (type only).
- `tools/checks/chain_coherence.py`, `tools/checks/test_chain_coherence.py`, and fixtures `clean_lifecycle`, `coh13_lifecycle_disagree`, `coh14_verified_attention`, `coh15_earlier_segment`; `tools/chain_clone.py`.
- Tests:
  - `backend/tests/test_ch3_lifecycle.py` (+2);
  - `test_ch3_lifecycle_postgres.py` (new);
  - `test_ch2_thread_store_postgres.py` (the downgrade message may be 0045's);
  - `test_out_e4_readback_postgres.py` (I-11 scope suffix);
  - `fixtures/s6_verification_api_contract.json` (additive `trial_hours.later_start/later_end`).

## Acceptance per sheet item

| Item | Status |
|---|---|
| A5 transitions, illegal skips reported, idempotent rerun | Met. L0 `test_ch3_lifecycle.py` (22 tests). L2 rerun writes 0. Clone rerun b,c,d gives 0/0/0. |
| Segments by story time (Q1) | Met (L0). |
| State on day d as of known_at (Q3), bitemporal (D-b) | Met. L0 `test_visibility_is_bitemporal_on_the_cause_time` and L2 `lookup(known_at=accepted)` give ACTION_IN_HAND, although every row was recorded later. |
| Four lines, Q4 placement, I-11 scope | Met (L0 `test_ch3_rows.py`). On the clone, only the 31 Oct line is observable (see below). |
| Money rule, Portfolio counts (Q5, build Q1) | Met (L0; clone `recovered_value` NOT_CREDITED). |
| L2 lifecycle on Postgres | Met: `test_ch3_lifecycle_postgres.py`, 3 tests (see Known Deviations D-f). |
| COH-13 to COH-15 pass with no entries (Q6) | Fixtures and non-vacuity met. **On the clone COH-13 reports 7. Not met; see D-e.** COH-14 and COH-15: 0. |
| I-01 entries removed if resolved | Not resolved. COH-8 keeps 3 entries, owned by CH-5a (CH3-R). |
| I-02 by COH-14, I-12 by verbatim L3 | COH-14 is 0, but its compared set is empty on the clone (no NEEDS_ATTENTION row). The I-12 31 Oct line is shown verbatim below; the 1 Nov line is not observable. |

## L3 clone (`assetops_chainclone_ch3_test`, created at `217d57486`+, migrated to 0045, dropped at the end)

**Backfill and reruns**
- Backfill `a,b,c,d`:
  - d wrote 5: ACTION_IN_HAND 3, CHANGE_APPLIED 1, RESOLVED_MONITORING 1;
  - d skipped 1: ACT-000002 APPLIED from OPEN, ILLEGAL_TRANSITION.
- Rerun `b,c,d`: 0 / 0 / 0, with d skipping 1 BEFORE_HEAD.
- `source_known_at` is filled on 11 of 11 occurrences.

**Thread states and stored `cause_known_at`**

| Thread | Head state | Cause times |
|---|---|---|
| Kobo generator | RESOLVED_MONITORING, 1 Nov | 17 Oct 12:07, 31 Oct 13:00, 31 Oct 14:00, 1 Nov 13:00 (story time) |
| Kobo headroom | OPEN, 25 Oct | 2 Nov 18:46 (build) |
| Cold start failure | ACTION_IN_HAND, 2 Nov | 2 Nov 18:42 / 18:43 (build) |
| Cold excursion | OPEN, 31 Oct | 2 Nov 18:43 (build) |
| EV interruption | ACTION_IN_HAND, 2 Nov | 2 Nov 18:43 / 18:44 (build) |

All `recorded_at` values are 3 Nov 21:47 (the backfill).

**Settle**
- `settle ch3`: tick PID 32260 exited 0 in 60 s with outcome COMPLETED; performance PID 12096 exited 0 in 2 s with "Performance cutover: permitted". No other process was spawned.
- Collect started right after: 56 requests, all 200, in 129 s (inside the 4-minute window).

**Check with `expected-today.json`**
- COH-0/3/4/9/10/11/14/15: 0.
- COH-1: 12 of 12 expected. COH-2: 2 of 2. COH-6: 6 of 6. COH-7: 10 of 10. COH-8: 3 of 3 (I-01, CH-5a).
- COH-5: 6 found, 3 new (D-g). COH-13: 7 new (D-e).
- COH-13 compared 27 board/Portfolio pairs.
- Self-check: 36 pass, 10 fail. These are exactly the 10 new findings.

**Board refs**
- Cold and EV refs read `thread: (None, None)` on every board day. This is the expected honest D-b result: their causes were recorded at build time (2 Nov) and the boards' resolved cutoff is the story time.
- Kobo refs carry state:

| Kobo board | Ref state | Effective |
|---|---|---|
| 17 Oct | OPEN | 17 Oct |
| 24 Oct | OPEN | 17 Oct |
| 31 Oct | ACTION_IN_HAND | 31 Oct |

**Kobo board, verbatim (in-process, after settle)**

31 Oct (`day:kobo:trial-before`):
- **OPTIMIZE_COST:** state UNKNOWN (MG-2 `PRODUCER_NOT_SETTLED`).
  - subline: "Generator stayed on 200 minutes longer than needed · Before the change on 1 Nov · after the change: not judged yet, no fully checked day since 1 Nov"
  - issues: FINDING MOVES "Generator may have been on longer than needed" (thread ACTION_IN_HAND); OPPORTUNITY CHECKED "Productive-use headroom".
  - earlier: ACT-001.
- **PROTECT_ASSET:** state UNKNOWN (MG-5, MG-4 `PRODUCER_NOT_SETTLED`).
  - headline: "1 early warning on battery and generator"
  - subline: "Battery and generator condition is not assessed; these are early warnings only. Power was delivered, but what customers needed is not measured"
  - issues: FINDING CHECKED "Generator may have been on longer than needed · checked here as a safeguard"; EARLY_WARNING MOVES "Battery capacity test due soon".

1 Nov (`day:kobo:trial-after`):
- **OPTIMIZE_COST:** state UNKNOWN (MG-2 `PRODUCER_NOT_SETTLED`); subline null; no FINDING issue; earlier: ACT-001.
- **PROTECT_ASSET:** same state, headline and subline as 31 Oct; no FINDING issue.

**I-12 / I-01 on real data**
- The 31 Oct before-the-change line IS shown (I-12, verbatim above).
- The 1 Nov verified/monitoring line is NOT shown: the generator Finding is not an issue on the 1 Nov board, so no row carries its thread line.
- The Kobo outcomes stay UNKNOWN after one settle tick. The board reads `read_state` PARTIAL: "24 of the last 31 days have no checked readings yet" (sparse demo days). So COH-14 has no NEEDS_ATTENTION row to judge.

## Checks run (final code unless noted)

**Unit (no database)**
- Phase scope: `test_ch3_lifecycle`, `test_ch3_rows`, `test_ch2_threads`, `test_out_b1_board`, `test_out_b2_vocabulary`, `test_out_b4_read`, `test_w303_portfolio_api`, `test_w303_portfolio_reduction` and `tools/checks/test_chain_coherence.py`: 240 passed, 1 skipped.
- `test_ch3_lifecycle` and `tools/checks/test_estate_guard.py`: 29 passed.

**Postgres scoped (`tools/run-host-tests.ps1 --`)**
- L2 `test_ch3_lifecycle_postgres` and `test_ch2_thread_store_postgres`: 6 passed (49 s).
- Batch 1 (`test_s6_action_store_postgres`, `test_s6_verification_{evaluator,holds,plan}_postgres`, `_rules`, `_verdict`, `test_out_e2`, `test_out_e4_readback`): 128 passed and 1 failed (377 s).
  - The failure: the contract-fixture shape lacked the additive `trial_hours.later_start/later_end` (CH-3 phase 1).
  - The fixture was regenerated with the test's own `ASSETOPS_WRITE_S6_VERIFICATION_CONTRACT` switch, keeping only that hunk; the test then passed.
- Batch 2 (that test, `test_out_b4_board_postgres`, `test_w303_portfolio_{comparison,fixture,scope_snapshot}_postgres`, `test_out_e3_trial_comparison_postgres`, `test_out_e4_readback_postgres`): 26 passed and 1 failed (1446 s).
  - The failure: E4 read-back expected the cost line without the I-11 scope.
  - The expectation was updated. Rerun of `test_out_e4_readback_postgres.py`: 1 passed (25 s).
- No full backend suite was run (dispatch rule).

**Frontend**
- `tsc --noEmit`: exit 0.
- vitest: an empty file filter ran the whole suite once by mistake: 3621 passed and 1 failed of 3622 (152 files).
  - The failure is in `src/sites/__tests__/siteFinding.test.tsx`. A rerun of that file alone failed a different test ("selects a block…", element not found), so the failure is flaky or date-dependent.
  - It is unrelated: the CH-3 frontend diff is type-only (`estateClient.ts`, `outcomeBoardClient.ts`).
- `vitest related` itself aborts on parsing a `.py` import in `fetchSeamContract.test.ts` (tool limitation, pre-existing).

**Guards and non-vacuity**
- `check-architecture.ps1`: passed. Its first run failed on the phase-1 adapter import in `lifecycle_run.py:101`, which now goes through `chain.composition`.
- `check-agent-workflow.ps1`: passed.
- Each proof was run after commit, then reverted with `git checkout`:
  - visibility on `recorded_at` only: 1 test fails;
  - COH-13 neutered: 4 tests fail;
  - COH-14 neutered: 1 fails;
  - COH-15 neutered: 2 fail;
  - settle without the name check: 7 fail.

## Known deviations

- **D-a, `BEFORE_HEAD` (accepted, CH3-R).** A non-OCCURRENCE cause dated before the head is skipped. Residual: same-day causes ordered across runs.
- **D-b (ruled, built).** Bitemporal visibility. Two choices made inside the ruling:
  - An INCONCLUSIVE expiry's `cause_known_at` is `max(outcome recorded_at, expiry instant)`, because it cannot be known before it expires.
  - A CLEAN_DAYS close has no single cause fact, so its `cause_known_at` is null and falls back to `recorded_at`.
- **D-c, `state_day` (accepted).** An additive wire key on the board and Portfolio threads.
- **D-d, `action_segment_no`.** An additive Portfolio row key for COH-15. The board leg has no segment on the wire and is covered by the board unit tests (`_earlier_segment`).
- **D-e, COH-13 is 7 on the clone (needs the Architect).**
  - The board honours its resolved story cutoff (D-b), so Cold and EV refs read no state.
  - The Portfolio, read without `known_at` (CH-2 D-1), reads the build-time states: OPEN since 28 Oct and 31 Oct, OPEN since 27 Oct for EV.
  - The two surfaces disagree for the same Finding, which is exactly what COH-13 exists to catch. Q6 ("COH-13 must pass with no entries") cannot hold until DD-1 fixes the build-time facts, or the Portfolio also takes a resolved cutoff.
  - No entries were added and nothing was tuned.
- **D-f, L2 apply and verify.** The APPLIED action event and the VERIFIED outcome enter through the reader's lifecycle inputs, not the Action or verification ledgers (the accept and the domain raise are real rows). The ledgers keep their own `test_s6_*` suites. The SUPPORT_LOST assertion in L2 is weak: the seed has no NO_LONGER_SUPPORTED revision. The guard is proven in L0 `test_support_lost_withdraws_only_without_an_action`.
- **D-g, COH-5 has 3 new Kobo findings, visible only after settle.** Each reads "on the board under PROTECT_ASSET, but its Findings row lens_flags ['COST'] lack RISK" (17 Oct, 24 Oct, 31 Oct). The Kobo boards had no FINDING issues before settle. CH-3 does not change the categories or lens flags, so this is a register item for the coordinator, not fixed here.
- **ACT-000002 APPLIED refused (ILLEGAL_TRANSITION from OPEN)** until DD-1: its case COMPLETE is story-dated before its build-time raise.
- **COH-8 / I-01 (3 entries) are left to CH-5a**, which owns the exact-revision progress rule.
- **Backfill step a on the clone.** The sheet says b,c,d; a fresh clone of the polish DB needs a, as in phase 2.
- **The four thread lines are MOCK DEVIATION candidates** (MA-1 M4).

## DS-R1

- Thread times come from stored story times.
- `created_at` is used only as a labelled fallback (`time_basis`).
- D-b adds each cause's own recorded time, so no backfill time decides visibility.

## Residual risk

- Same-day cause order across runs (D-a).
- Occurrence counts are still read as stored, not as of `known_at` (CH-2 R-2, owned by CH-5a).
- Kobo outcomes stay UNKNOWN on the clone after one tick (sparse days), so COH-14 and the 1 Nov line are unproven on real data.
- CH-1b must re-point its 0044 onto 0045.
- `frontend/node_modules` in the worktree is a junction to plan2's.
