# CH-6b1 handoff (PARTIAL: stopped at the context budget)

Branch `task/CH-6b1-estate-chain` (worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch6b1`), main merged at `53e5eddff` (CH6b1-R). Head `79886c69f`.

## Landed (commits)
- `7cc440771` build. `B/site_outcomes/read.py`: `summary` -> `seed_snapshots` (one `ChainRequest.seed_days` over `snapshot_specs`; fallback counted `summary.seed_fallback` + LOG) -> `_summary`; `board(..., node_days=)` adds `_window` via `_window_parts` (composer `NodeInputs` re-evaluated over `window_days`, rows = composer rows + the `claim_days` memo read, rows' nodes via `assemble`, income earnings); `portfolio_parts(sites)` = the ONE function for per-Site `rows{state,state_label,lead,nodes}`/`earnings` + `money_total`; `summary_window` DAY/PERIOD only; `latest_window`, `_event_window`, `_prefetch`, `_PREFETCH`, `WINDOW_BASIS_EVENT` deleted; summary rows gain `nodes`, sites gain `earnings`, body gains `money_total`; `overview_href` = base link. `chain_api._estate_chain` calls `portfolio_parts(summary["sites"])`. `chain/read.py` `ChainRequest.seed_days`; `chain/reader.py` `latest_many`; `postgres_chain_read.py` `snapshots_many`; `read_scope.seed`. `chain/vocabulary.py` `estate_income` + `income.*` templates. Composers keep `node_inputs` (`mini.py` MiniComposition field; `domain_nodes.node_inputs`). COH-7a per domain (`chain_coherence.py`), CO-6/CO-6b PERIOD (`tools/demo_combined_finish.py` :416, :458-460 only).
- `bc1de29f4` L0 `backend/tests/test_ch6b_estate_chain.py` (15 pass). Mutations M1 composer window, M2 raw sum, M3 NOT_KNOWN not lower bound, M4 no seeding, M5 unfiltered seed slice: each fails it; reverted.
- `04f6a43d6`, `79886c69f` L2m `backend/tests/test_ch6b_estate_postgres.py`: 1 pass, 374 s (Kobo earnings 239.00 -> 299.00 USD after `late_fill` D7; days 4/7 -> 5/7). c3/c4 postgres summary tests rewritten to PERIOD (NOT yet run).
- `c65e52cd3` chain-structure baseline shrinks (latest_window). `check-architecture.ps1`: passed.
- MD-0 `states` template rebuilt once: `assetops_mechanism_tpl_aad4a485_test` (seed 1595 s, 5 resumes).

## Known deviations to carry into the packet
- KD-1 (Q6): Cold 7/7 and EV D9 are L0 only (mechanism_db is Kobo only).
- KD-2: reading-based verdicts with no kpi contribution record (MG-5) are judged on the composer's reading of the last window day (`chain/outcomes.py:136-140`), so their node days are 1 of 1, not the 7 window days; MG-1 is month-to-date (R5). Architect question, not changed here.
- KD-3: the `states` template holds D1-D5, D10-D14 only, so D7-D13 reads 4/7 (D7, D8, D9 NO_DATA), not §B5's 6/7; L2m recomputes from stored rows.
- Pre-existing on main `9c30094a6`: `test_ch5a1_summary_ledger.py::test_summary_reads_each_key_at_most_once` (productive_readings hit count) fails on main and here.
- Frontend untouched (CH-6b2): `estateClient.ts:627` type still lists `LATEST_EVENT`; `portfolioFixtures.ts:406-410` fixture only.

## Resume here
1. DB-scoped existing tests, one file per call: `test_out_c3_repeat_visits_postgres.py`, `test_out_c4_ev_warnings_postgres.py`, `test_w303_portfolio_fixture_postgres.py`, `test_cov_partial_portfolio_postgres.py`, `test_ch5a2_chain_api_postgres.py`, `test_ch4_opportunities_postgres.py`, `test_qw2_many_postgres.py`. (Non-DB scoped list: 391 pass, only the pre-existing failure.)
2. `tools/check-agent-workflow.ps1`; frontend not changed (no vitest needed beyond a sanity typecheck).
3. One polish clone L3 (standard procedure: create -> migrate -> backfill a-d -> settle -> W6 -> `fresh` with store on -> collect -> COH 0 new vs `expected-today.json` -> drop). Record Portfolio summary values old -> new (window_basis, overview_href, money_total, nodes) and the P2 plan/timing (`summary.seed_snapshots` perf; >50 ms reported).
4. Packet `.agent/review-packet-CH-6b1.md` with the mock -> new table (income.* texts vs v70 `pfGrowParts`); task Status in_review; ACTIVE_CONTEXT / CODE_STATE entries.
- USER_REVIEW: none required by the sheet (CH6b1-R: "No owner question").
