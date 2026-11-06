# CH-6b1 fix round R3+R4: PARTIAL handoff (stopped at the context budget)

Branch `task/CH-6b1-estate-chain`, main merged (R3/R4 rulings). Env helper (recreate): PYTHONPATH absolute worktree
`backend;contracts;tools;simulator;gateway;host;field`, venv `AssetOpsV1-plan2\.venv\Scripts\python.exe`, ASSETOPS_GUARD_PYTHON same.

## Step 1 result (clone check): R3 IS NEEDED
Clone `assetops_chainclone_ch6r_test` (clone name `ch6r`) is LEFT IN PLACE: created, migrated, backfill a-d, settled; bundle
collected to `var/ch6r_bundle` (work dir `var/ch6b1work`). OLD values (this code before R3), Portfolio week 25 Oct-1 Nov:
Cold OPTIMIZE_COST UNKNOWN, PROTECT_ASSET UNKNOWN (kpi "no backup start in this window", 0 of 7), ASSURE UNKNOWN "No verified result yet";
EV GROW UNKNOWN, OPTIMIZE NOT_MEASURED, PROTECT UNKNOWN ("Not known yet"), ASSURE UNKNOWN. No event or repeat warning shown -> build R3 (done below).
Still to do on the clone: re-collect after R3 (`chain_coherence.py collect --work var/ch6b1work --database-url <clone_url ch6r> --out var/ch6r_new`),
record NEW Cold/EV week + day values, COH check 0 new, W6 (`chain_watermark_guard.py`), `chain_response_probe.py fresh`, then `chain_clone.py drop ch6r`.

## Landed in working tree (committed WIP)
- R4 SPAN: `chain/vocabulary.py` `Claim.span` (wire `span:{first,last}`, additive), `span_text`, `days_line(days, day, span, window)` (names span only when != window; `named=` removed), `verdict_claim/money_claim(span=)`. `chain/outcomes.py` `_reading` returns (reading, days, span): record kpi = window; MINI record kpi (MG-2) judged on board day (days counted over that day, H2); monthly = [1st, hi] (M1); no-record = (hi,hi) (H1); earnings span = window. `site_outcomes/board.py` `SiteFacts.window_span` (read via getattr), assemble passes span+window. `read.py` sets `window_span` in `_window_parts` and `board()`.
- R3: `read.py` `contained_windows`, `latest_contained_window` (renamed: a test forbids `latest_window`), `event_window`, `contained_many` (one `site_selected_windows_many`), `compose/board/_summary(windows=)`; board window stays requested; fallback counted `summary.window_fallback` + logged (L3 also covers seed fallback: still only counted, add LOG.warning on the no-reader/multi-tenant path in `seed_snapshots`).
- L0 `tests/test_ch6b_estate_chain.py`: 20 pass (Objectives fake for MG-1/MG-2/EV-1, WindowsEstate fake, Q1 non-vacuous, contained/outside, board=summary L4, failed-window fallback).

## Remaining (in order)
1. Fix existing tests now failing from R3/R4 (run list: test_ch5a2_contract, test_ch5a1_summary_ledger, test_out_w2_summary_window, test_qw2_reuse, test_ch6_evaluator::test_cc1_chamber_no_data..., test_ch6_r2a_rows, test_ch5a1_board_contract):
   - goldens (`test_board_equals_its_golden`, `test_chain_body_equals_its_golden`): wire gains `span`; regenerate goldens by the file's own regen path and review the diff is only `span`.
   - `test_fixture_ledger_has_no_deleted_read[cold,ev]`, `test_qw2_reuse` (`.single == 0`, a board reads no estate rows), `test_out_w2_summary_window` (estate fake is a Never guard): cold/EV boards now read `site_selected_windows(_many)` by R3; allow exactly that read, still forbid estate ROW reads. Give the W2 test's estate a windows fake.
   - `test_cc1_chamber_no_data_is_not_judged...`: expects basis CHECKED_DAYS, got NOT_KNOWN: check whether `_reading` span/day change or window_span broke it.
2. Update `tests/test_out_c3_repeat_visits_postgres.py` back to NEEDS_ATTENTION + REPEATED on day and week (PERIOD basis, requested window) and add the L4 assertion (cold board over the day/week has same OPTIMIZE_COST state as the summary). Run it, c4, and L2m `test_ch6b_estate_postgres.py` via `tools/run-host-tests.ps1` (DB 127.0.0.1:55432), one at a time.
3. Not built: days line naming the event window (e.g. "26 Oct 16:00-17:05") for cold/EV rows; record as Known Deviation or add span for event-window node claims.
4. Lows: L1 docstrings `tools/demo_combined_finish.py:403,:451` (say PERIOD not LATEST_EVENT); L2 `site_selected_windows_many` now has a production caller (kept); L3 log on seed fallback paths + fallback count in the packet (expected 0 on W6).
5. Mutation proof (commit first): days_line always naming -> H1 test fails; contained filter removed -> outside-window test fails.
6. Guards A, W, V, N, M, L, D one at a time; packet "Fix round R3+R4" section (old -> new Cold/EV values, which client surface reached the failure before: Findings/evidence page); ACTIVE_CONTEXT/CODE_STATE not updated; do not merge.
