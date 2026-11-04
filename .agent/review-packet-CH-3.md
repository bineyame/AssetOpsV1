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

## Fix round 1 (Architect rulings CH3-R phase 3)

### A/B check: Kobo boards UNKNOWN after settle (not a regression)

Both trees read the same, so this is environmental. A is main `73a558a1b` (the branch base, 0041, read-only worktree, never migrated, one tick with its own code). B is a fresh clone migrated to 0045 and settled with this branch. Both clones and the A worktree are dropped.

| | A: pre-chain (main `73a558a1b`) | B: this branch |
|---|---|---|
| Overview freshness / assessment | no overview: `AwaitingComparison` (assessment null) | identical |
| `base` (CURRENT and assessment not CLOSED) | False | False |
| Dispatch present | yes | yes |
| Finding index, 31 Oct | PARTIAL, 24 gaps, none on 31 Oct | identical |
| Finding index, 1 Nov | PARTIAL, 23 gaps, none on 1 Nov | identical |
| `findings_ok` | true | true |
| Readiness 31 Oct / 1 Nov | FULL / UNKNOWN | identical |
| Failing `settled` input | the overview | the overview |

- The overview port raises: "Site KOBO-001 is imported; its Evidence moves to the central ledger only after a passing legacy comparison record. No legacy comparison record exists; run `python -m assetops_backend.evidence_migration ...`". `assetops_polish_full_test` carries no such record, and neither a tick nor `performance_migration run` ("permitted") adds one.
- So `base` is False and every Kobo outcome reads `PRODUCER_NOT_SETTLED`, before and after the chain. CH-1a, CH-2 and CH-3 are not involved.
- Consequence: COH-14 and the 1 Nov verified line stay unproven on real data until the clone also gets the legacy comparison record (a coordinator/Architect call; not done here).

### Fixes

- **COH-13 = 0 on the clone** (fresh clone: migrate, backfill a-d, settle, collect, check; no COH-13 entry added).
  - `estate/portfolio.py` `attach_threads` reads thread state at the envelope's resolved `window.known_at` (D-b rule).
  - **Sub-deviation (needs Architect sight).** That literal reading was not enough: the envelope value is the read instant (4 Nov), so build-time events still showed OPEN on the Cold and EV rows while the board (cutoff 31 Oct 17:05) hid them; COH-13 stayed 7.
    - The board's resolved cutoff for a cold/EV Site is that Site's evidence cutoff, which the Portfolio already holds per Site (`_WindowRecorder.cutoff`, the same value in the row's Finding link).
    - Each cold/EV row now carries `_cutoff = min(site evidence cutoff, envelope k)`, and `attach_threads` reads each distinct cutoff in its own lookup. Mini-grid rows and Actions use the envelope value. After this COH-13 is 0.
  - New unit `test_portfolio_thread_state_uses_the_resolved_cutoff` (`test_ch2_threads.py`).
- **COH-5:** the 3 Kobo PROTECT_ASSET lens findings (17 Oct, 24 Oct, 31 Oct; `<finding>:RISK`) are in `expected-today.json` as I-21, owner CH-5a.
- **D-f (L2, both directions).** `test_ch3_lifecycle_postgres.py`:
  - with an Action on the thread (ACTION_IN_HAND), every occurrence NO_LONGER_SUPPORTED: SUPPORT_LOST is skipped and no WITHDRAWN row exists;
  - a new test on an Action-free thread (`bare` fixture): the same cause writes exactly one WITHDRAWN (`SUPPORT_LOST`), and none is written before the cause is supplied.
- **D-b sub-calls accepted** (CH3-R): INCONCLUSIVE expiry `cause_known_at = max(outcome recorded_at, expiry instant)`; CLEAN_DAYS close has a null `cause_known_at` and falls back to `recorded_at`.
- D-e is closed by the COH-13 fix above.

### Fix round 1 checks (final code)

- Unit scope (the phase scope plus `tools/checks/test_estate_guard.py`): 251 passed (365 s).
- Postgres: `test_ch3_lifecycle_postgres.py` 4 passed (26 s). The Portfolio files I touched (`test_w303_portfolio_{comparison,fixture,scope_snapshot}_postgres`, `test_ch2_thread_store_postgres`): 19 passed (855 s).
- L3 on a fresh clone (migrate to head, backfill a,b,c,d, one settle tick, collect 56 x 200, check against `expected-today.json`): every rule 0 new; COH-5 6 of 6 expected; COH-13, COH-14, COH-15 0; self-check 39 pass, 0 fail. Clone dropped.
- `check-architecture.ps1`: passed.
- Non-vacuity (each after commit, reverted with `git checkout`):
  - Portfolio ignoring the row `_cutoff`: `test_portfolio_thread_state_uses_the_resolved_cutoff` fails.
  - COH-13 before the fix: 7 new on the clone (the proof of the check itself); after: 0.
  - Allowing `ACTION_IN_HAND` + SUPPORT_LOST to WITHDRAWN and neutering the Action guard: the L2 test with an Action fails.
  - Dating the SUPPORT_LOST cause after the head was needed: the first version of the "Action" direction passed under that mutation (the cause was skipped as BEFORE_HEAD); it now fails under it.

## Fix round 2 (review REVISE M1-M3, L1-L5; CH3-R consolidated ruling)

Commits: `6865714a9` (code and tests), `e4137cdb2` (L2 Postgres assertion), `68440bd6e` (COH-14 thread-level line), `f573c53c7` (the estate lookup takes the policy through `chain.composition`, because the architecture guard refused the direct adapter import).

### Fixes
- **M1** `chain/lifecycle.py`:
  - Causes sort by `cause_order` = (`cause_known_at`, `recorded_at`, id).
  - BEFORE_HEAD compares `known_time(cause) < known_time(head)`. A planned head uses its cause's known time. A planned CLEAN_DAYS close has no known time and never blocks.
  - `state_on` is unchanged: the highest seq with `effective_day <= d`, after `visible(k)`.
  - `lifecycle_run.causes_for_site`: a superseded VERIFIED or INEFFECTIVE outcome gives no cause.
- **M2** `tools/chain_clone.py`:
  - `settle` runs `SETTLE_STEPS` in order: s2-comparison (`evidence_migration run --tenant demo --site KOBO-001`), tick, performance.
  - It diffs `var/` before and after, and writes `var/chainclone_<name>/created.json` (files and dirs), also on failure.
  - `drop` drops the DB, then `cleanup` deletes exactly the recorded files. It refuses any recorded path outside `var/` before deleting anything. Then it removes the emptied recorded dirs and the record.
- **M3** `site_outcomes/board.py` `thread_line_findings`:
  - In-window Findings work as before.
  - A thread with no in-window Finding also gets a line, from its latest occurrence, when all three hold:
    - `facts.work_window` is set (mini only);
    - the thread's occurrence (`FindingFact.in_work_window`) or one of its Actions is in the 31-day work window;
    - its state on d is RESOLVED_MONITORING, CLOSED or RECURRED.
  - The line goes in the subline of its primary MOVES row. Earlier is unchanged.
- **L1** `site_outcomes/read.py` `board_cutoff(known_at, resolved)`: one helper for mini, cold and EV. Mini resolves no cutoff, so None means "as known now" (output unchanged).
- **L2**:
  - `lifecycle_inputs` returns `site_type`.
  - LOOKUP's F rows carry `s.site_type` as a 12th column; 11-column rows still read.
  - `thread_lookup(close_after=policy.close_after)` reads the per-type count for each Finding.
- **L3** `portfolio.thread_progress`: one state per thread, taken from its highest (segment_no, occurrence_no) row.
- **L4**:
  - `test_thread_wire_keys_copy_matches_the_lookup` added.
  - EARLIER_SEGMENT is pinned (an Action re-accepted after a REOPENED).
  - `lc.accepted_day` (the earliest ACCEPTED day) is used by both the lifecycle and the lookup.
- **L5** `test_ch2_thread_store_postgres`:
  - The placement test asserts exactly "0045 refused".
  - New `test_0042_refuses_its_downgrade_while_a_thread_exists` (a thread row with no known time) asserts 0042's own message and an unchanged head.
- **Action segments per cutoff group** (`portfolio.attach_threads`):
  - Every cutoff group reads the Actions too, into `_segment_at[cutoff]`.
  - `action_segment_for(a, row)` serves both `same_segment` and the wire `action_segment_no`.
- **Found while running the unit scope.** `test_out_a1_outcome_map::test_outcomes_package_is_pure` already failed on `046d29094`, because CH-3's `outcomes/credit.py` imported `decimal` and `fractions`. `credit.py` now uses exact int pairs with a half-even three-decimal wire form, and tests are added.

### L3 clone `assetops_chainclone_rtwo_test`
From `assetops_polish_full_test`, code `6865714a9`, no serve.

**Create and backfill**
- Create and migrate to head: 2 s.
- Backfill a,b,c,d: a 139, b 11, c 3, **d 6** (ACTION_IN_HAND 3, CHANGE_APPLIED 2, RESOLVED_MONITORING 1); skipped 0.
- Rerun b,c,d: 0 / 0 / 0; skipped 0.

**Thread heads**

| Thread | Head |
|---|---|
| Kobo generator | RESOLVED_MONITORING, 1 Nov |
| Kobo headroom | OPEN, 25 Oct |
| Cold start | **CHANGE_APPLIED, 31 Oct** |
| Cold excursion | OPEN, 31 Oct |
| EV | ACTION_IN_HAND, 2 Nov |

**Settle**
- s2-comparison: exit 0 in 1 s ("Evidence cutover: permitted").
- Tick: exit 0 in 39 s (COMPLETED).
- Performance: exit 0 in 1 s.
- `created.json` listed 2 files and 2 dirs. The files are one `evidence/migration/kobo-001/...json` and one `evidence/migration-performance/kobo-001/...json`.

**Collect and check**
- Collect: 56 requests, all 200.
- Check against `expected-today.json`: every rule 0 new; self-check 39 pass, 0 fail.
  - COH-1 12/12, COH-2 2/2, COH-5 6/6, COH-6 6/6, COH-7 10/10, COH-8 3/3.
  - COH-0, 3, 4, 9, 10, 11, 13, 14 and 15: 0.

**Kobo boards** now read AVAILABLE. OPTIMIZE_COST, verbatim:
- 31 Oct: NEEDS_ATTENTION, subline "Generator stayed on 200 minutes longer than needed · Before the change on 1 Nov · after the change: not judged yet, no fully checked day since 1 Nov".
- 1 Nov: ON_TRACK, subline "Fix verified, monitoring (ACT-001) · 7 more fully checked days to close"; Earlier lists ACT-001.

**COH-14**
- 6 rows across the bundle are NEEDS_ATTENTION / PRIMARY_FINDING_OPEN, including Kobo 17, 24 and 31 Oct.
- None of them has all its MOVES Findings on a verified thread, because a verified fix ends the episode (the M3 cause).
- With the thread-level extension, COH-14's compared set is **1 row** (Kobo 1 Nov OPTIMIZE_COST, ON_TRACK), and it passes.

**Portfolio**
- The Kobo generator row reads RESOLVED_MONITORING.
- `verified_resolution_count` is 1 and `priority_site_count` is 0.
- Money is NOT_CREDITED.

**Drop**
- The clone was dropped, and the tool reported "deleted 2 file(s)".
- A `find var` listing equals the one taken before settle; the 4 earlier `migration-performance` files are kept.

### Known deviations (fix round 2)

**FR2-a: COH-14 extended (Architect or reviewer to confirm).**
- Without the extension, COH-14 cannot have a non-empty compared set on real data, for the same reason as M3.
- `coh14_rows` now also judges a row that has no MOVES Finding but whose subline carries the verified thread line.
- The line is matched by `VERIFIED_LINE_PREFIX = "Fix verified"`, which is pinned against `board.THREAD_MONITORING` and `THREAD_CLOSED`.
- This strengthens the rule: nothing it judged before is dropped.

**FR2-b: ACT-000002 now applies, so DS-R1's "refused until DD-1" no longer holds.**
- In known-time order, the cold domain case COMPLETE (recorded after the raise) applies after ACCEPTED.
- So Cold start reads CHANGE_APPLIED, with `effective_day` 31 Oct (story time). That is before the 2 Nov of its ACTION_IN_HAND.
- `state_on` takes the highest seq, so from 31 Oct the thread reads CHANGE_APPLIED as known after both causes.
- At story cutoffs both events stay hidden, because their causes were recorded at build time. So the boards are unchanged (COH-13 0).
- For the DD-1 inventory, list it as "applied, effective before accept".

**Postgres revision.** The Postgres runs below were at `e4137cdb2`. `f573c53c7` changes only the import path of the same policy object.

### Fix round 2 checks

**Unit (no database), final head**
- The CH-3, out, portfolio and board scope (46 backend files) plus `tools/checks/test_chain_coherence.py`: 767 passed, 1 skipped.
- `tools/checks/test_estate_guard.py` through `run-host-tests.ps1`, final head: 9 passed (353 s).
  - Run directly with pytest from Git Bash, the same 9 fail with "running scripts is disabled" on the temp-dir `.ps1` the test spawns. That is the shell's execution policy, not the code.

**Postgres** (`run-host-tests.ps1`, shared `assetops_test`)
- `test_ch3_lifecycle_postgres` and `test_ch2_thread_store_postgres`: 8 passed (45 s).
- `test_ch3_lifecycle_postgres`, `test_out_e4_readback_postgres` and `test_w303_portfolio_scope_snapshot_postgres`: 15 passed (543 s).
- `test_w303_portfolio_comparison_postgres`: 4 passed (209 s).
- `test_w303_portfolio_fixture_postgres`: 2 passed (69 s).
- `test_out_b4_board_postgres`: 5 passed (110 s).

**Guards** (`ASSETOPS_GUARD_PYTHON` = the plan2 venv)
- `check-architecture.ps1`: passed (after `f573c53c7`).
- `check-agent-workflow.ps1`: passed.

**Non-vacuity.** Each proof mutated committed code, ran the new tests and restored the file with `git checkout`. The tree was clean after each.
- Unit: all 18 mutations fail their tests:
  - the known-time sort;
  - BEFORE_HEAD by known time (this also fails the two-runs test);
  - the superseded filter;
  - accepted day min to max;
  - the EARLIER_SEGMENT branch;
  - the site type in the lookup and in run_lifecycle;
  - the thread-level line turned off;
  - the work-window condition;
  - the per-thread rank;
  - the Action segment at the row's cutoff;
  - Actions read per cutoff group;
  - the wire keys;
  - credit half-even rounding;
  - the settle comparison step;
  - recording only created files;
  - the outside-var refusal;
  - the COH-14 line branch.
- Postgres: dropping 0042's `REFUSE_IF_USED` and the `site_type` key fails both new Postgres assertions (2 failed).

**Not run**
- Frontend: no change this round.
- Full backend suite: outside the dispatch scope.
