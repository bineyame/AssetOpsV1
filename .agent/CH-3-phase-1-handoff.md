# CH-3 handoff (partial): resume from "Remaining"

- Branch `task/CH-3-lifecycle` in worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch3` (from main `54d46479f`).
- Commits: `e54880b39` (lifecycle core), `c9150f459` (read path).
- Sheet: `AssetOpsV1-plan2\.agent\build-sheet-CH-3.md`.
- Rulings: coordinator relay of 2026-11-03 (all six pre-flight defaults accepted). Q1 changed: segments by STORY time, never `joined_at`/`linked_at`; see plan row CH3-R.
- CH-1b had no commits at branch time, so the fallback is built: `stages.py` `chain_threads` runs steps (b, c, d).
- Overlap with CH-1b:
  - `B/scheduling/stages.py`: `chain_threads`, one-line steps change plus docstring.
  - `B/chain/backfill.py`: `run_threads` / `dry_run` step d.
  - `B/chain/adapters/file_chain_config.py`: `load_thread_lifecycle`.

## Landed

**Lifecycle core**
- `config/chain/thread-lifecycle-v1.json`. Loader: `file_chain_config.load_thread_lifecycle`.
- `B/chain/lifecycle.py` (pure):
  - `TRANSITIONS`, `plan_lifecycle` (illegal causes skipped and reported; idempotent on `(cause_kind, cause_id)`);
  - segments: `segment_on`, `occurrence_segment`, `action_segment`;
  - `state_on`, `complete_days`, `thread_view`.
- `B/chain/lifecycle_run.py`: `causes_for_site`, `thread_causes` (OCCURRENCE causes for occurrences with no event, which handles backfill order; SUPPORT_LOST), `run_lifecycle`.
- Stores:
  - `PostgresThreadStore.site_threads` / `append_events` (same advisory lock as `place`) / `thread_head`;
  - `MemoryThreads` twins (`B/chain/threads.py`).
- `PostgresThreadSources.lifecycle_inputs`: read-only cause SELECTs, plus snapshots when 0043 is present.
- Backfill step d (`backfill.py`; `_lifecycle_report` adds `site_code`).

**L4 dry run on `assetops_polish_full_test` (0041, so no snapshots): matches the sheet**
- Kobo generator: RESOLVED_MONITORING, 2026-11-01.
- Cold start failure: ACTION_IN_HAND, 2026-11-02.
- Cold excursion: OPEN.
- EV interruption: ACTION_IN_HAND, 2026-11-02.
- Kobo headroom: OPEN.
- One cause was skipped and reported, and this is honest:
  - ACT-000002's case COMPLETE (`occurred_at` 31 Oct, story time) precedes its raise (`recorded_at` 2 Nov, build time), so APPLIED is ILLEGAL_TRANSITION from OPEN.
  - This is DD-1 territory. List it as a deviation or residual risk.

**Read path**
- `B/chain/lookup.py`: a new uniform 11-column `LOOKUP` with F/E/A rows. `thread_lookup(rows, day=, known_at=, complete=, close_after=)` returns `findings` (with `segment_no`, `state`, `state_effective_day`), `actions`, `action_segments`, `lifecycle` and `subjects`.
- `PostgresThreadSources.lookup(..., day=, known_at=)` also reads COMPLETE days from `site_day_snapshot`.
- `B/site_outcomes/read.py` `board()`: `board_day` is the mini overview day, or `_last_local_day(window.to)` for cold and EV. `cutoff` is the request's `known_at`, else the window's. Both go into `SiteFacts.day` / `known_at`, only when a thread port exists.
- `B/site_outcomes/board.py`:
  - `finding_signal_state`: with a thread, the thread state decides; without one, the exact-revision rule stays.
  - `thread_line` builds the 4 literals: `THREAD_*`, `TRIAL_SCOPE`.
  - `_earlier_segment`: an open old-segment Action goes to Earlier.
  - The subline gets the thread line on the row of the Finding's primary MOVES outcome.
  - Q2 `state_label_on` re-runs `outcome_state` with that day's thread state.
  - `THREAD_WIRE_KEYS` strips the wire `ref.thread`.
  - `cost_line` uses `outcomes/credit.credited`.
  - The board must import only `outcomes/` and the stdlib allowlist (`test_out_b1_board.py:342`), so the I-11 local times are computed in `mini._trial_hours`.
- `B/actions/verification.py` `_cost_check_read`: `trial_hours` gains `later_start` / `later_end` (additive).
- `B/outcomes/credit.py`: `credited`, `recovered_value`, `MONEY_NOT_CREDITED`.
- `B/estate/portfolio.py`:
  - `attach_threads(..., req)` passes `day` = UTC last day of `req.to` and `known_at`;
  - `_action_for` adds a same-segment rule;
  - `thread_progress` gives `verified_resolution_count` and `priority_site_count`;
  - `recovered()`.
- `postgres_estate_read.threads(..., day=, known_at=)` and `cost_checks()`.
- Tests updated (old → new):
  - `test_ch2_threads.py::test_lookup_rows_reduce...` (new row shape);
  - `recovered_value` `None` → NOT_CREDITED object in `test_w303_portfolio_api.py:392`, `_comparison_postgres.py:160`, `_scope_snapshot_postgres.py:335`.
- Frontend types: `estateClient.ts` (`thread` fields, `recovered_value`), `outcomeBoardClient.ts` (`FindingThreadRef`).
- Scoped unit run: 381 passed, 1 skipped. That covers the board/status/vocabulary/portfolio unit files plus `test_ch2_threads`.

## Remaining (in order)

1. **New tests** (sheet §8 L0 and L2):
   - `backend/tests/test_ch3_lifecycle.py` and `test_ch3_rows.py`: transitions and illegal skips, Addis/UTC effective days, INCONCLUSIVE expiry, CLEAN_DAYS with PARTIAL not counted, the occurrence-4 segment case, the signal from the thread, the 4 lines, the money rule per `cost_check` state, Portfolio counts. Also pin `board.THREAD_*_STATES == lifecycle` constants, and `portfolio.VERIFIED/ATTENTION_THREAD_STATES`.
   - `test_ch3_lifecycle_postgres.py`: on the s6 harness (`test_s6_action_store_postgres.py:119-131`) and the CH-2 L2 setup, check OPEN → ACTION_IN_HAND → CHANGE_APPLIED → RESOLVED_MONITORING. A rerun writes 0. A domain raise gives ACTION_IN_HAND. The SUPPORT_LOST guard holds.
2. **Vocabulary guard V:** add `THREAD_*` (formatted) and `TRIAL_SCOPE` to `test_out_b2_vocabulary.py::_constants` (:63-74), plus `credit.MONEY_NOT_CREDITED`.
3. **COH-13/14/15** in `tools/checks/chain_coherence.py`: `RULES` at :801-805. Each needs a failing fixture bundle in `tools/checks/fixtures/chain_coherence/bundles/` plus a `FAILING` entry in `tools/checks/test_chain_coherence.py:26-42`. Prove each guard non-vacuous.
   - COH-13 compares the board `ref.thread.state` on day d against the Portfolio row `thread.state`. Pair them by the window whose last day is d: the Portfolio reads its state on the window's last day.
4. **`expected-today.json`:** remove the 3 COH-8 / I-01 entries if they resolve on the clone.
5. **L3:** `python tools/chain_clone.py create ch3 --migrate`, giving a clone named `assetops_chainclone_*_test`, then:
   - backfill `--steps b,c,d`, then `chain_coherence.py collect` / `check`;
   - report the 31 Oct and 1 Nov Kobo cost rows (state + subline) verbatim, plus thread states per Site and ACT-001's thread and rows before and after;
   - drop the clone.
6. **Scoped existing suites:** `test_s6_verification_*.py`, `test_s6_action_store_postgres.py`, `test_out_b4_board_postgres.py`, `test_w303_portfolio_*postgres.py`, `test_ch2_*postgres.py` and `test_out_e*` (the `trial_hours` keys grew). Run them through `tools\run-host-tests.ps1 -- <files>`.
7. **Frontend:** `npx vitest related --run src/estate/estateClient.ts src/sites/outcomeBoardClient.ts`, plus the typecheck. Junction `node_modules` from plan2.
8. **Guards:** `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1`, with `ASSETOPS_GUARD_PYTHON` set.
9. **Packet:** `.agent/review-packet-CH-3.md`, committed with `git add -f`.

## Open risks to check

- `credited()` sums the per-kWh nominal change (`change_per_demand_kwh`). The unit is per kWh, not a money total. The sheet says "sum of credited amounts"; flag it in the packet. Today nothing is credited.
- OCCURRENCE → RECURRED needs `occurrence day > head event day` (strict).
- A thread with a no-episode occurrence falls into the latest segment.
- `PostgresThreadSources.lookup` snapshot SELECT: SITE-kind measures are matched by Site only through the occurrence's `site_id` subquery. That is acceptable for one-Site boards.
- `thread_view.checked_days` counts COMPLETE days without excluding occurrence-start days. `run_lifecycle` CLEAN_DAYS does exclude them, so this is a minor copy and close mismatch.
- The Portfolio thread `day` is the UTC date of `req.to - 1µs`, while the board uses the Site-local day.
