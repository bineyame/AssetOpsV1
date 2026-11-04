# CH-5a1 phase 3 results: L3 on the polish clone (§A9 item 5). Evidence only. OPEN: R-1 needs an Architect ruling.

Authority: build sheet Part A §A6, §A7, §A9 item 5, R3/P1; pre-flight §3 and §4. Previous: `CH-5a1-phase-2d-handoff.md`.

## Setup
- Clone `assetops_chainclone_ch5a1_test`, made from `assetops_polish_full_test` (read-only source, never ticked).
- **A** = read-only detached worktree `AssetOpsV1-ch5a1-A` at main **a07452c63**. Rerun A against main at the MD-0 merge.
- **B** = this branch. The final B bundle is at **c74ffbb22** (this branch's fixes 1-3). The probe commit e756438e1 is tools only.
- Both sides ran B's `tools/checks/chain_coherence.py collect` (the same `day_windows`/`days.json` windows, §A6), each with its own
  backend on `PYTHONPATH`, with `PGOPTIONS=-c default_transaction_read_only=on`. The `--work` was the scratch `polish_work`.
- **A-side precondition:** the S2/Performance comparison records live in the worktree's `var/` and are bound to the evidence store.
  - With none in A, A's `mini_overview`, `dispatch` and `finding_index` failed (gates closed). The first A bundle was invalid.
  - I ran `evidence_migration run` and `performance_migration run` from A, read-only against the clone. Both permitted, with no DB
    writes, 4 s. A was then recollected (bundle A2).

| step | command | wall |
|---|---|---|
| 1 | `chain_clone.py create ch5a1 --migrate` | 5 s |
| 2 | `python -m assetops_backend.chain.backfill --steps a,b,c,d` (counts: a 139, b 9, c 3, d 6 written) | 45 s |
| 3 | `chain_clone.py settle ch5a1` (comparison 12 s, tick COMPLETED 128 s, performance 2 s) | 145 s |
| 4 | collect A2 / B (first run) / B2 / B3: 56 requests each | 180 / 75 / 77 / about 77 s |
| 5 | `chain_coherence.py check` B3 and A2 against `expected-today.json` | under 1 s |
| 6 | `chain_perf_probe.py`, boards; summary + Portfolio with `--profile --outbox` | 259 s; 179 s |
| 7 | `chain_clone.py drop ch5a1`, then `git worktree remove` of A | done |

## Regressions found by the A/B, fixed and committed (each with a test proven to fail on revert)
1. **0c9cfe98e: the mini route refused its own Site-local window.**
   - Symptom: B's Kobo `links.self` and the summary's Site window (`21:00Z`-`21:00Z`) got 422 `NOT_ONE_UTC_DAY` (3 of 56 requests).
   - Fix: `outcome_api._mini_day_params` reads a one-Site-local-day `from`/`to` as `date=`. A UTC day and every 422 code are
     unchanged.
   - Test: `test_out_b4_route::test_mini_accepts_its_own_site_local_day_window`.
2. **9cbe253c9: board state classes leaked onto the Portfolio wire.**
   - Symptom: `thread_lookup` now adds `applied`/`verified`/`later`/`wire_keys`, and `portfolio_row` emitted
     `dict(r["_thread"])`.
   - Fix: the row uses `public_thread`.
   - Test: `test_ch2_threads::test_portfolio_row_thread_is_the_public_form_only`.
3. **c74ffbb22: the money port was never bound.**
   - Cause: `site_outcomes/composition.py` read `site_overview.upstream`, but `site_overview` is the `SiteOverviewRoute`, which has no
     `upstream`. `money_head` was therefore always None, so MG-7 read "Source not resolved" and COST was never priced.
   - Fix: it now reads `site_overview.read.consequences` (pre-flight P6: the overview read's own consequence read).
   - Test: `test_out_b4_imports::test_board_chain_reader_gets_the_overview_consequence_read`.

## A/B diff (A2 vs B3, after normalising `window.known_at`, `selection_token` and `links.self`): 30 of 56 requests differ, 617 paths
| surface | requests | differing | paths | classes |
|---|---|---|---|---|
| day boards, Kobo (8 days) | 8 | 8 | 28-41 each | E2, E1, E4 (+ derived E2) |
| day boards, Cold 24/28/31 Oct | 3 | 0 | 0 | none |
| day boards, EV 20/27 Oct | 2 | 2 | 8 / 10 | E1; R-1 (EV 27 Oct, 2 paths) |
| summary-linked boards (3 windows x 3 Sites) | 9 | 8 | 3-96 | Kobo E4 (a different day); Cold R-1; EV E1 + R-1 |
| summary (week, S, month) | 3 | 3 | 13 / 13 / 14 | Kobo card: E4 + E2 |
| Portfolio (week, S, month) | 3 | 3 | 4 / 2 / 4 | R-1 only |
| Findings index (all, opportunities, day) | 19 | 0 | 0 | none |
| actions, action index | 9 | 6 | 1 each | N0: top-level `known_at` is the wall-clock read time (not a product change) |

### Classified, old → new
- **E1 (`readiness_of`)** matches pre-flight §4 exactly:
  - Kobo 17, 24, 31 Oct: High → Limited (chip x3, MG-7 "readiness Full" → "Limited");
  - Kobo 1 Nov: Unknown → Limited;
  - Kobo 3, 10, 28, 30 Oct: Limited, unchanged;
  - Cold 24, 28, 31 Oct: unchanged (NONE);
  - EV 20 and 27 Oct: Limited → Low (7 chips; MG/EV reason `EVIDENCE_READINESS_LIMITED` → `_NONE`).
  - **Not in §4:** the summary month board for Kobo is now local 3 Nov. It reads Unknown → Low (NO_DATA), combined with E4 below.
- **E2:** on A every Kobo board reads `PRODUCER_NOT_SETTLED` (wall-clock overview freshness; no serve). On B they read settled.
  - Rows go from UNKNOWN to ON_TRACK, NEEDS_ATTENTION or WATCH. Objective verdicts go from None to MET, MISSED or NOT_JUDGED.
    "Not checked yet" becomes Met or Missed.
  - Derived from that: the MG-4/MG-5 lead outcome becomes MG-4 (WATCH leads once states are known), on every Kobo day.
  - COST headline on 17, 24 and 31 Oct: "No fuel cost estimated for this day" → "No fuel cost estimated: the generator was on but
    delivered no measured power". A's overview money was unpriced only because it was unsettled; B prices through `money_head`
    (Q5).
- **E3:** `finding_gaps` is equal on every day board. It differs only where E4 moves the summary's Kobo day.
- **E4:**
  - Kobo `window` is the local day (`2026-10-30T21:00Z`-`31T21:00Z` for 31 Oct) on all 8 boards.
  - **The summary's Kobo card moves day** (R6 `summary_day` = local day of `to - 1 µs`): week and S go from 31 Oct to **1 Nov**,
    month from 2 Nov to **3 Nov**.
  - Proof that this is only a day change: on each side, the summary board equals that side's own day board with 0 differences
    (A summary = A 31 Oct board; B summary = B 1 Nov board).
- **E5:** no other occurrence-count change at the latest cutoff. Kobo threads are unchanged.
- **R-1 (outside E1-E5, open, Architect).** Cold and EV threads are hidden on the Portfolio, the summary boards and the EV 27 Oct
  board (`thread` → null; 2-4 paths per surface).
  - Cause: the L5 `LOOKUP` filter `coalesce(source_known_at, joined_at) <= :k`, where `:k` is the Cold/EV row cutoff, which is
    story time: Cold 31 Oct 17:05Z, EV 27 Oct 09:00Z.
  - On this clone, `source_known_at` is the revision's wall-clock `created_at` (2 Nov 18:42-18:43Z), so every Cold/EV occurrence is
    after its own cutoff.
  - So the latest read changes, against E5's "no change at the latest cutoff". The Finding stays visible while its own occurrence is
    hidden.
  - It also adds COH-10 x7 and COH-11 x2 (below). Not fixed here, because the fix is a semantics choice.
  - Proposed default: L5 occurrence visibility uses the **request** `known_at` (None = as stored). The Cold/EV evidence cutoff keeps
    bounding only the thread *state* (CH3-R COH-13).
  - Alternative: compare a story-time instant, as R8 rules for `recorded_at`.

### E3b and the Finding set
- **E3b: empty.**
- The (finding_id, revision_id) set is equal on A and B for every day board (Kobo 17/24/31 Oct have 1 each, EV 27 Oct 1, the other 9
  boards 0) and for the Portfolio (week 5, S 3, month 7).
- The summary-linked Kobo board differs (A 1, B 0) only because the two sides show different days (E4). B's 1 Nov set equals A's
  1 Nov set (both 0).

## Coherence check against `expected-today.json` (B3 vs A2 = main)
| | pass | fail (new) | resolved |
|---|---|---|---|
| A2 (main a07452c63) | 28 | 2: COH-5 Kobo 17/24 Oct COST lens | 5 (COH-1 x3, COH-5 x2, Cold) |
| B3 (this branch) | 28 | 12: the same 2 + **COH-7a x1** + **COH-10 x7** + **COH-11 x2** | the same 5 (none resolved here) |

- COH-10/11 are R-1: the Cold f9ed0fec/2505d188 rows and the EV 274196f4 Portfolio rows have no thread, and Actions ced674cb/b9f71cdd
  answer a thread-less row.
- **COH-7a** (S window): the summary's Kobo window `[31 Oct 21Z, 1 Nov 21Z)` is not the requested `[31 Oct, 1 Nov)`. This is R6
  `summary_day` against the COH-7a rule. **Architect:** keep `to - 1 µs` (the window then runs past the request), use the local day
  of `from`, or adapt COH-7a.

## Performance (`tools/chain_perf_probe.py`, in process, read-only)
Cold = first request in a fresh process, 5 runs. Warm = 5 runs in one process after one discarded request. ms. The machine was shared
with other jobs; QW-1 measured ±15-25% run-to-run.

| URL | cold med (min-max) | warm med (min-max) | bytes | QW-1 B cold / warm (design §11b) | P1 warm (pre-flight §3) |
|---|---|---|---|---|---|
| Kobo board `?date=2026-10-31` | 4,508 (4,027-4,916) | 7,803 (7,108-9,013) | 14,487 | 9,458 / 8,374 | 8,690-8,824 |
| Cold failure-night board | 1,815 (1,566-2,282) | 1,114 (1,008-1,249) | 15,553 | (inside summary: 0.5-1.0 s) | 632 (ledger) |
| EV 27 Oct board | 4,664 (3,201-18,066) | 1,039 (964-1,219) | 12,218 | (inside summary: 0.6-0.9 s) | 881 (ledger) |
| summary, week | 7,028 (6,749-7,902) | 4,344 (4,171-4,704) | 12,588 | 13,046 / 9,534 | 9,363-10,798 |
| Portfolio, week | 5,168 (4,563-5,688) | 4,247 (3,965-4,398) | **280,903** | 8,304 / 7,226 | 7,258-7,592 |

- **Budgets (none relaxed):** cold ≤ 1 s, warm ≤ 300 ms p95, board ≤ 60 KB, Portfolio ≤ 100 KB.
  - Missed: every cold time, every warm time, and the Portfolio payload (281 KB).
  - Met: the board payloads (12-16 KB).
  - The Kobo warm-above-cold inversion was reproducible in this run. It was not investigated (shared machine). Reread on L3m.
- **Top ledger by ms (last warm run):**
  - Kobo: `assessment._window` 2,139; `estate` 1,858; **`money_head` 1,534 (`chain.money_head` 1,503)**; `mini_depth` 1,209;
    `dispatch` 691; `action_facts` 611; `action_read` 600; `work_index` 263; `source` 207.
  - Cold: `work_index` 606; `cold_overview` 292; `cold_findings` 140; `readiness_of` 14; `chain.day` 14.
  - EV: `ev_overview` 287; `ev_depth` 189; `ev_availability` 144; `work_index` 134; `ev_findings` 102.
  - Summary: `mini_depth` 685; `work_index` 685; `_window` 671; `action_facts` 371; `action_read` 363; `dispatch` 313.
  - Portfolio: `_window` 741; `claim_limit_snapshot_on` 245.
  - **money_head line:** Kobo 1,503 ms; Cold, EV, summary and Portfolio 0 (no lead money read in their ledger).
  - money_head alone is about 5x the 300 ms warm budget. Pre-flight §3 estimated 0.66 s. It is now measured, because fix 3 binds it.
- `max_per_key` is 1 on every board and the Portfolio, and 3 on the summary. These are not memoised repeats: `objectives ()` is keyed
  `()` per Site (3 Sites), and Kobo `productive_readings` runs twice with the same day and month window on 1 Nov. Both are
  `Reads.call` timing records, as on A.
- **P8 stub:** `event_outbox` 3 rows, `event_consumption` 0. R8 is 6.8-7.2 ms per Site (settled=True for all 3).

## P1 / R3: one warm Portfolio (story week, 4,482 ms)
- **`select_evidence_scope`, 2.10 s cumulative** (pre-flight: about 4.4 s per run). 234 statements; DB wait (`select.select`) 0.73 s.
  - `mini_grid_rows` 0.71 s;
  - `claim_limit_on` x7 0.70 s (`claim_limit_read.py:357`);
  - `link_rows_on` x29 0.67 s;
  - `cited_set` x27 0.65 s; `source_provenance.resolve` x27 0.64 s;
  - **`cited_provenance` x20 0.61 s** (`postgres_estate_read.py:138`, per row); `link_rows` x27 0.59 s.
- **`select_financial_scope`, 0.73 s** (was about 1.5 s). 173 statements; DB wait 0.37 s.
  - `site_coverage` x3 0.40 s; `windowed_lines` x2 0.33 s; `_mini_grid_basis` 0.20 s; `link_rows_on` x14 0.19 s;
  - `selected_windows` x2 0.19 s; `_cold_window` x4 0.15 s; `ev_money` x2 0.15 s.
- **Reading for CH-5c (R3 rule; the Architect rules on these numbers):**
  - The R1 memo removed the repeated `_window` reads: `_window` is 741 ms total, and `max_per_key` is 1.
  - The residual is per-row provenance (`cited_provenance` → `cited_set` → `link_rows_on`, 20-29 calls) plus 7 claim-limit reads.
    Both are DB round trips. Python selection compute is small.
  - That is the batching branch: **CH-5c ≈ 1-2 units**.
  - The Portfolio payload (281 KB, 2.8x budget) is a separate residual for CH-5b/CH-5c.

## Checks after the fixes
- Focused: `test_out_b4_*`, `test_ch5a1_*` (non-Postgres), `test_ch2_threads`, `test_ch3_rows`, `test_qw1_perf`, `test_out_b2_*`,
  `test_s5_overview_read`: **224 passed**.
- Each new test failed on revert (1 failed each), then was restored.
- `check-architecture.ps1`: passed, with `ASSETOPS_GUARD_PYTHON` set (without it Rule 8 cannot run).
- `check-agent-workflow.ps1`: passed.
- L2 (`test_ch5a1_reader_postgres`) and the real-Postgres full suite were not rerun after fixes 1-3 (fix 3 changes the board's money
  path on a DB). **Due in the final full suite.**

## Cleanup
- `assetops_chainclone_ch5a1_test` dropped (0 chain clones remain), and settle's 2 `var/` files were deleted.
- The A worktree was removed with `git worktree remove`; the directory is gone and it is not listed.
- Nothing was committed on A. The polish DB, polC, demo3, mechanism and dd0b were not touched.

## Open for the Architect before merge
1. R-1 (L5 occurrence bound against the Cold/EV story-time cutoff; COH-10 x7, COH-11 x2).
2. COH-7a against R6 `summary_day` (the summary's Kobo card now shows 1 Nov for the week ending 1 Nov 00Z).
3. The extra E1 entry: summary month Kobo 3 Nov reads Low.
4. CH-5c sizing from P1.
