# CH-3 handoff 2 (partial): resume at "Remaining"

- Branch `task/CH-3-lifecycle`, worktree `AssetOpsV1-ch3`. Read `.agent/CH-3-phase-1-handoff.md` first for the core anchors; this file supersedes its "Remaining" list.
- Commits since phase 1 (`fc4d0f078`):
  - `a2e850f98`: CH3-R rulings applied, L0 tests, vocabulary V registration.
  - `3484b4d73`: BEFORE_HEAD skip (rerun idempotency).
  - `6e3dc8d16`: board cutoff, plus the `state_day` wire key.

## Landed this phase

**CH3-R rulings (coordinator relay, 2026-11-04)**
1. **Money.**
   - `outcomes/credit.credited` credits only `cost_check["priced_total"]` = `{amount, currency, basis}` (none is stored today). The per-kWh `nominal` is never money.
   - `board.cost_line` is back to main's logic: the VERIFIED MODELLED_IMPROVEMENT rate line `COST_CHANGE` shows the rate with its unit, labelled "not money saved".
   - The estate `cost_checks` SELECT no longer reads `nominal`.
   - Tests: `test_ch3_rows.py::test_per_kwh_nominal_never_produces_an_amount` and `::test_priced_total_credited...`.
2. **One fully-checked-day rule.**
   - `lifecycle.fully_checked_days(rows, subject, measures, occurrence_starts)` serves both `lifecycle_run.thread_clean_days` (close) and `PostgresThreadSources.lookup` (the board's "k more" count; a new SELECT reads the thread's occurrence starts, `joined_at <= known_at`).
   - Test: `test_ch3_lifecycle.py::test_one_fully_checked_day_rule_for_close_and_count`.
3. **Portfolio day.**
   - `thread_lookup(..., day_at=)` reads each Finding on its own Site's local day holding that instant.
   - `portfolio.attach_threads` passes `day_at = req.to - 1µs`; `postgres_estate_read.threads(day_at=)`.
   - Test: `test_lookup_day_at_reads_each_site_local_day`.
4. **Tuple copies.** The equality test is in `test_ch3_rows.py::test_board_and_portfolio_tuple_copies_match_lifecycle`.

**Vocabulary V**
- `test_out_b2_vocabulary.py::_constants` adds the formatted thread lines, `TRIAL_SCOPE` and `credit.MONEY_NOT_CREDITED`.
- Non-vacuous: putting `RESOLVED_MONITORING thread` into `THREAD_MONITORING` made `test_board_and_status_copy_pass_vocabulary` fail. The change was reverted.

**L3 clone findings, now fixed (both are packet deviations)**
- **D-a, BEFORE_HEAD.**
  - On the first clone, a rerun of step d wrote CHANGE_APPLIED: ACT-000002's case COMPLETE (31 Oct) was skipped as ILLEGAL from OPEN, then applied on the next run against the ACTION_IN_HAND head (2 Nov).
  - `plan_lifecycle` now skips a non-OCCURRENCE cause dated before the head (`reason: BEFORE_HEAD`).
  - Test: `test_rerun_after_an_out_of_order_skip_writes_nothing`.
  - Residual: same-day causes ordered across runs.
- **D-b, cutoff.**
  - Ruling Q3's fallback ("otherwise the read's resolved cutoff") hid every thread state on the Cold and EV boards. Their resolved cutoff is the story time (for example 31 Oct 17:05), but backfilled events carry the build-time `recorded_at` (4 Nov), so `ref.thread.state` was null.
  - `site_outcomes/read.py` `board()` now uses the request's `known_at` only, as the Portfolio does (CH-2 D-1).
  - Flag it for the Architect.
- **D-c, `state_day`.**
  - An additive key `state_day` (the Site-local day the state was read on) is added to `chain/lookup.PUBLIC_KEYS` and `board.THREAD_WIRE_KEYS`, and to the frontend types `estateClient.ts` and `outcomeBoardClient.ts`.
  - Reason: board days (Cold 31 Oct in Addis) never equal a Portfolio read day (S window → 1 Nov local, month → 3 Nov). COH-13 needs both read days and no zone is on any body.

## Clone `assetops_chainclone_ch3_test` (LEFT IN PLACE for the final collect; drop it at the end)

- Recreated at `3484b4d73`, migrated. Backfill `a,b,c,d`:
  - a: 138 written;
  - b: 11 (NEW_THREAD 5, ADDED 6, ALREADY_PLACED 4);
  - c: 3 LINKED;
  - d: 5 written (ACTION_IN_HAND 3, CHANGE_APPLIED 1, RESOLVED_MONITORING 1), plus 1 skipped (ACT-000002's APPLIED from OPEN, ILLEGAL_TRANSITION).
- Rerun `b,c,d`: 0 / 0 / 0. d skipped 1 BEFORE_HEAD.
- Thread states, matching the sheet's L4:
  - Kobo generator: RESOLVED_MONITORING, 2026-11-01;
  - Kobo headroom: OPEN, 2026-10-25;
  - Cold start failure: ACTION_IN_HAND, 2026-11-02;
  - Cold excursion: OPEN, 2026-10-31;
  - EV interruption: ACTION_IN_HAND, 2026-11-02.
- Bundles, collected before D-b and D-c (re-collect for the packet), in the scratchpad `ch3-pre` (after a,b,c) and `ch3-post`. Collect: `chain_coherence.py collect --work C:\Users\assef\Bineyame\AssetOpsV1-polC\var\polish_full --database-url <chain_clone.clone_url('ch3')>`, 56 × 200, about 120 s.
- Check on `ch3-post` with `expected-today.json`: every rule matches the expectations, with 0 new; self-check 36 pass.
- **COH-8 (I-01 part) does NOT resolve.** All 3 entries remain: "ACT-001 ... progress row has origin_revision_selected False". That is the exact-revision progress rule (I-03), not thread state, so keep the entries and say so.
- Portfolio, collected after the rulings:
  - Kobo rows RESOLVED_MONITORING, effective 1 Nov, in week, S and month (Addis local day; week `to` 1 Nov 00Z gives 1 Nov local);
  - Cold and EV rows: OPEN in week and S, ACTION_IN_HAND in month;
  - `verified_resolution_count` 1, `priority_site_count` 2, `recovered_value` NOT_CREDITED "No money credited · modelled, not saved".
- **Kobo board leg not observable.**
  - Every Kobo day board has no FINDING issue. The rows read UNKNOWN with MG-2 `PRODUCER_NOT_SETTLED`, the same pre and post, and CH-2 saw the same.
  - On 1 Nov, ACT-001 is under PROTECT_ASSET Earlier: "Verified on example data · Not available yet · linked finding could not be loaded".
  - So the sheet's verbatim 31 Oct and 1 Nov Kobo cost-row lines cannot be shown from this unticked in-process clone. Report the rows verbatim as they are, mark I-12 and I-01 board text as unverified on L3, and cite `test_ch3_rows.py` for the lines.

## Remaining (in order)

1. **COH-13/14/15** in `tools/checks/chain_coherence.py`. Add them to `RULES` (`:801`) and `FAILING` (`tools/checks/test_chain_coherence.py:26`). Add one failing bundle each: copy `bundles/clean`, then edit. Prove each non-vacuous. Also make `collect` stamp `manifest["lifecycle"] = True`; on a stamped bundle, a board or Portfolio thread missing `state_day` fails (COH-0 style, like `_missing_thread_keys`).
   - **COH-13** (tz-free). For each board `d` FINDING ref with `thread.state_day` and each estate window `w` whose Portfolio row has the same `finding_id` and a thread, order the two reads by `state_day` into lo and hi:
     - hi.eff is None: lo and hi must be equal;
     - hi.eff ≤ lo.day: `(state, state_effective_day)` must be equal;
     - otherwise: lo.eff must be None or < hi.eff.
     - Clone pairs exist: the Cold 31 Oct ref against week (1 Nov, OPEN 28 Oct) and month (3 Nov, ACTION_IN_HAND 2 Nov). Record the count of pairs compared.
   - **COH-14.** A board row outcome with `state == NEEDS_ATTENTION` and `reason == "PRIMARY_FINDING_OPEN"`, where every FINDING issue with `role == "MOVES"` on the row has `ref.thread.state` in (RESOLVED_MONITORING, CLOSED), is a finding. On the clone the verified-ref set is empty (Kobo not observable). Say so; the fixture proves it can fail.
   - **COH-15.** It needs the Action's segment on the wire, so add an additive Portfolio row key `action_segment_no` next to `action_thread_id` (`portfolio.py:224-226`, from `action["_segment_no"]`). Fail when `action_id` is set, `action_thread_id == thread.id` and `action_segment_no < thread.segment_no`. Board leg: the board never puts an earlier-segment Action in hand (`_earlier_segment`, `board.py:854`), but in-hand items carry no segment. State that the board leg is covered by unit `test_line_recurred...` only, or add a segment to the in-hand ACTION item only if the tests allow it.
2. **Re-collect** on the clone (no `--known-at`) and check:
   - COH-13 to COH-15 report 0 with no entries;
   - COH-8 keeps its 3 entries;
   - record the Cold and EV ref states;
   - report the Kobo 31 Oct and 1 Nov rows verbatim (OPTIMIZE_COST and PROTECT_ASSET);
   - then `chain_clone.py drop ch3`.
3. **L2** `backend/tests/test_ch3_lifecycle_postgres.py`, on the s6 harness (`test_s6_action_store_postgres.py:119-131`): accept, apply, verify gives OPEN → ACTION_IN_HAND → CHANGE_APPLIED → RESOLVED_MONITORING. Rerun gives 0. A domain raise gives ACTION_IN_HAND. The SUPPORT_LOST guard holds.
4. **Scoped Postgres suites** via `tools\run-host-tests.ps1 -- <files>`: `test_s6_verification_*`, `test_s6_action_store_postgres`, `test_out_b4_board_postgres`, `test_w303_portfolio_*postgres`, `test_ch2_*postgres`, `test_out_e*`.
5. **Frontend:** `tsc --noEmit` plus `npx vitest related --run src/estate/estateClient.ts src/sites/outcomeBoardClient.ts`, with `node_modules` junctioned from plan2.
6. **Guards** `check-architecture.ps1` and `check-agent-workflow.ps1`, with `ASSETOPS_GUARD_PYTHON` set.
7. **Packet** `.agent/review-packet-CH-3.md`, added with `git add -f`. Deviations: D-a, D-b, D-c, `action_segment_no`, ACT-000002 refused APPLIED (until DD-1), COH-8 not resolved, Kobo board leg not observable, and the step-a run on the clone (the sheet says b,c,d). The four lines are MOCK DEVIATION candidates (MA-1 M4).

## Unit state at `6e3dc8d16`

`test_ch3_lifecycle`, `test_ch3_rows`, `test_ch2_threads`, `test_out_b1_board`, `test_out_b2_vocabulary`, `test_out_b4_read` and `test_w303_portfolio_api`: 119 passed, 1 skipped.
