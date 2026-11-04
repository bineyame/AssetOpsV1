# CH-5a1 phase 2b handoff - PARTIAL (tests items 1-3 mostly landed; stopped at the context budget)

Authority unchanged: build sheet Part A (incl. §A12). Previous: `CH-5a1-phase-2-handoff.md` (its "Remaining" list).
Branch `task/CH-5a1-chain-reader`, HEAD `d0129ca75`. Resume at "Remaining (phase 2c)" item 1.

## Landed (commits 7692b0bd5, 18a0482b1, a7efaee0f, 6fc7e3f73, d0129ca75)
- **D3 done:** `BoardServices.finding_reads`, the composition param and the `main.py` kwarg deleted
  (`main.py` still builds `finding_reads` for the Action service). `test_out_b4_main_binding.py` now asserts absence.
- `test_out_b2_mini.py`: Fake on the new MiniPorts (`DayFacts`/`FindingHead`/`ActionFacts`/`MoneyHead`; override
  map in the module docstring; `day=` overrides DayFacts fields; `verification=` is the summary body). m1-m7 lineage
  tests deleted; added thread-join cases, port-shape/ledger case (no overview/index/readiness/verification/action/
  history ports, each chain port called once), money lead-Finding case, has_change case.
- `test_link_lineage.py` rewritten to the thread join (same thread+segment; other segment/thread/unthreaded never;
  no thread -> exact revision; lineage symbols deleted).
- Adapted: `test_out_b4_read.py` (summary_day Addis+UTC, chain ports forwarding), `test_idx_gaps_board.py` (gap
  line over DayFacts, `index_settled` gone), `test_out_d4_board.py`, `test_polish_pa1_board_truth.py`,
  `test_out_b4_route.py` (`site_list`, R2), `test_out_b4_window.py` (readiness_of over local days, Q8),
  `test_qw2_reuse.py` (no readiness batch), `test_out_w2_summary_window.py` (E4), `test_ch2_threads.py` (view
  carries `state_classes`/`wire_keys`, phase-1 §A5), `test_out_b4_board_postgres.py` (see failure below).

## Production fixes (minimal)
1. `chain/read.py:231` `ChainRequest.day`: `m.measure` -> `m.key` (`MeasureSpec` has no `measure`; every real board
   failed `chain_day`/`readiness_of`). L0 missed it (fake measures) - **L1 must cover `day()` with the real registry.**
2. `site_outcomes/mini.py` new `estate_bounds(day)`; compose calls the kept estate read on the UTC day D and the 31
   UTC days ending with it (as before R6). The estate window rule (`estate/scope.py:106` `check_window`) refuses
   non-midnight bounds, so local R6 bounds made every Kobo estate read INVALID_WINDOW. `read.py` `_prefetch` keys
   its spans with the same helper (`estate_days`). **Open question for the Architect** (default: accept until
   CH-5a2 B3 replaces the estate read): the estate rows stay UTC-day while the board day is local.

## Tests run (bash, plan2 venv, `-p no:cacheprovider`)
Pass: b2_mini 32, link_lineage 8, b4_main_binding 2, b4_read 8, idx_gaps_board 5, d4_board 17, pa1 8, e4_readback 19,
c4_mini_ev 12, walk1_3b 22, walk1_5 10, walk1_productive_sales 20, b2_vocabulary 4, out_c2_board 13, b1_board 28,
b3_cold_ev 21, b4_route 5, b4_window 10, qw1_perf 8, qw2_reuse 4, w2_summary_window 16, w301_estate_api 11,
w303_portfolio_api 5 (+1 skip), b4_imports 3, ch5a1_reader 24, ch5a1_scope 7, c3_cold_cost 6, pa2a 14, pa2b 8,
post_w6_w3 7, w302 26, w303_cursor 43, cov_partial 20, fix01 11, ch0_tick 10, ch2_threads 27, ch3_lifecycle +
ch3_rows + ch2_backfill_cli (in a 98-test run: 96 passed before the ch2 fix, the 2 were ch2_threads).
Postgres (`tools\run-host-tests.ps1`): `test_out_b4_board_postgres.py` 4 passed, **1 failed**
`test_kobo_guardrail_two_board_days`: Day A has no F01 MOVES issue because `chain_findings` returns `[]` - the
fixture (`_build_kobo`) never runs the chain (no `finding_thread_occurrence` rows; outbox unconsumed, so R8 also
unsettled). Not loosened. Fix in the fixture: settle the chain after `_build_kobo` (`chain.backfill.main` steps
a,b,c,d with `DATABASE_URL` = the case url, then consume the outbox so R8 settles), then the Day A F01 checks must
pass unmodified; if they do not, that is a regression to fix in production.
Not yet run: `test_w601c_request_detail.py` (18 skipped without Postgres - run via run-host-tests),
`test_qw2_many_postgres.py`, `test_ch2_thread_store_postgres.py`, `test_ch3_lifecycle_postgres.py`,
`test_w301_estate_index_postgres.py`, `test_idx_gaps_postgres.py`, the other `*_postgres` importers.

## Remaining (phase 2c), in order
1. Settle the chain in the `kobo_guardrail` fixture (above); rerun b4_board_postgres; then the Postgres list above,
   one at a time.
2. L1 `test_ch5a1_board_contract.py` (fixture ChainReader incl. a `ChainRequest.day` over real `measures_for`;
   ledger 0 of mini_overview/finding_index/evidence_readiness/estate.site_readiness*; goldens: phase 3 A side).
3. L2 `test_ch5a1_reader_postgres.py` (non-mechanism; list in phase-2 handoff item 5, incl. L5 count at k before a
   third occurrence and `has_change == bool(detail.change)` per seeded Action).
4. Collector: `tools/checks/chain_coherence.py` `_board_query` + `day_windows`; `backend/tests/mechanism_dataset.py`
   `build_work` Kobo local-day bounds; Addis cases in `tools/checks/test_chain_coherence.py`.
5. vitest `npx vitest related --run src/sites/outcomeBoardClient.ts`; guards A and W; estate guard self-tests
   (none of these run in 2b).

## Behaviour changes adapted in tests, outside the literal E1-E5 wording (Architect review)
- Dispatch refusal now unsettles every measured outcome (CH5a1-R Q2 `base` includes `dispatch is not None`; the
  overview's assessment was the dispatch day, so in production a dispatch failure was an overview failure).
- A 31-day unaligned cold/EV window: readiness now pools its 32 local days (Q8) instead of the estate's
  INVALID_WINDOW -> Assure UNKNOWN.
- Findings settledness no longer follows the gap days (R8 only); a fixture whose chain is unsettled shows no
  Findings (heads come from thread occurrences, §A3).
- Dead after the slice, left in place: `mini.UNSETTLED_INDEX_STATUS`, `GAPS_WITHHELD` (still in COPY).

## L2m TODO (do not build until MD-0 merges) - unchanged from the phase-2 handoff item 5.

## Importers for the packet
Phase-2 handoff list, plus `test_out_b4_main_binding.py` and `test_ch2_threads.py` (changed here).

## Phase 3 needs
Unchanged (L3 clone A/B, perf probe, P1 cProfile, packet). Add the estate-bounds question and the three behaviour
changes above to the packet's Known Deviations.
