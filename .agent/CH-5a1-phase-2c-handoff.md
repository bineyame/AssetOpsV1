# CH-5a1 phase 2c handoff - PARTIAL (items 1-3, 6, 7 landed; L2 and the collector next; stopped at the context budget)

Authority unchanged: build sheet Part A (incl. §A12). Previous: `CH-5a1-phase-2b-handoff.md`.
Branch `task/CH-5a1-chain-reader`. Resume at "Remaining (phase 2d)" item 1.

## Landed (commits e4aff009f, 931b423b3, fa177ab48, b701bd23a)
- `test_out_b4_board_postgres.py` `_settle_chain` (called from `_build_kobo`): backfill `--steps a,b,c,d`, then
  `scheduling.stages.chain_threads` consumes the Site's outbox (deferred 0). The 2b adaptation
  (`failed_a == ["estate", "chain_findings"]`) is reverted to the original `["estate"]`; Day A F01 MOVES/Protect checks
  pass unmodified (no production fix needed).
- `mini.UNSETTLED_INDEX_STATUS`, `GAPS_WITHHELD` (and its COPY entry) deleted; `test_idx_gaps_board.py` and
  `test_out_b2_vocabulary.py::test_finding_gap_line_strings_are_scanned` adapted (CH5a1-R Q4: the board never
  withholds; the estate keeps its own `coverage.DAYS_WITHHELD`).
- `test_idx_gaps_postgres.py` p5 rewritten over the chain day (deleted `finding_index` read; R4/R8/Q9): backfill step
  (a) on the F01 case, `build_chain_reader(URL)`, `ChainRequest.day`. Behaviour recorded: the S4 case delivers dispatch
  blocks only, so step (a) writes NO_DATA snapshots, every window day incl. 10-06 is a "no checked readings" gap
  (31 of 31) and the board day is unsettled (index era: 10-06 settled, 30 of 31). Gap lines over real readings = L2m.
- `test_out_c3_repeat_visits_postgres.py` window spy also wraps `site_selected_windows_many`: with no readiness
  prefetch (R5) the QW-2 batch now serves the cold window, so the per-Site spy saw nothing. Remaining assertions
  (window == latest, < 2 s) pass unmodified. Unverified: why main's batch fell back (see open questions).
- L1 `test_ch5a1_board_contract.py` (13 tests): `SiteOutcomeBoardService` over a real `ChainReader` on an in-memory
  port + small fake services; goldens `backend/tests/fixtures/ch5a1_board_contract/{kobo_2026-10-31,kobo_2026-11-01,
  cold_2026-10-31,ev_2026-10-27}.json` (E-changes listed in the module docstring; regen only with
  `ASSETOPS_REGEN_CH5A1_GOLDENS=1`); ledger test: 0 calls of mini_overview / finding_index / estate site_readiness*,
  none of the deleted names in `read_scope` names, `max_per_key() == 1`; `ChainRequest.day` over real
  `measures_for` per site type; `SITE_TYPE_OF_DOMAIN` values all have registry measures.

## Production fix (phase 2c)
- `chain/read.py:24` `SITE_TYPE_OF_DOMAIN["ev_charging"]` `"EV"` -> `"EV_CHARGING"` (the registry's key,
  `chain/measures.py:61`). Found by L1: every EV board's `readiness_of` asked the port for zero measures and read
  UNKNOWN. Same class as 2b fix 1 (fake site types/measures in L0). Reran after it: b3_cold_ev, b4_window, b4_read,
  ch5a1_reader/scope, b4_route, qw2_reuse, w2_summary_window (95 passed), c4_ev_warnings_postgres (1 passed).

## Tests run (this phase; Postgres via `tools\run-host-tests.ps1`, one file per run)
| file | result |
|---|---|
| test_out_b4_board_postgres.py | 5 passed (after the fixture fix; before: 4 passed 1 failed, now `failed_a` restored) |
| test_w601c_request_detail.py | 18 passed |
| test_ch2_thread_store_postgres.py | 4 passed |
| test_ch3_lifecycle_postgres.py | 4 passed |
| test_qw2_many_postgres.py | 1 passed |
| test_idx_gaps_postgres.py | 7 passed (p5 adapted; before: 1 failed, TypeError `MiniPorts(overview=)`) |
| test_w301_estate_api.py | 11 passed |
| test_w303_portfolio_api.py | 6 passed, 0 skipped (Postgres run) |
| test_w301_estate_index_postgres.py | 20 passed |
| test_walk1_objective_min_days_postgres.py | 3 passed |
| test_out_d5_objectives_postgres.py | 3 passed |
| test_out_c3_repeat_visits_postgres.py | 1 passed (spy adapted; before: 1 failed, `len(chosen) == 0`) |
| test_out_c4_ev_warnings_postgres.py | 1 passed (before and after the EV fix) |
| idx_gaps_board + b2_vocabulary + pa2a + b2_mini + cov_partial | 75 passed |
| test_ch5a1_board_contract.py | 13 passed |
| frontend: 13 files importing outcomeBoardClient / outcomeBoardFixture (`npx vitest run <files>`) | 13 files, 407 tests passed |

`npx vitest related --run src/sites/outcomeBoardClient.ts` itself errors at startup ("Failed to parse source for
import analysis ... .py file format") - environmental (the related graph reaches a .py); the explicit file list above
is the same importer set. `frontend\node_modules` is now a junction to plan2's.

## Guards
- `tools/check-architecture.ps1`: Architecture check passed. `tools/check-agent-workflow.ps1`: passed.
- Estate guard self-tests (`tools/checks/test_estate_guard.py`): **not run** - phase 2a measured 1566 s (15 passed),
  over the 600000 ms cap; per the brief it is reported, not backgrounded. No guard file changed since 2a.

## Open questions (proposed defaults)
1. c3 window spy: on main the per-Site `site_selected_windows` was hit, so main's QW-2 batch presumably fell back
   (its readiness batch failing). Default: accept as an R5 consequence; phase 3 can confirm by grepping the A-side log
   for "batched estate reads fell back".
2. idx_gaps p5: the S4 case's chain day is NO_DATA throughout. Default: accept (deleted read); L2m covers real readings.
3. The EV fix changes EV readiness on real data from UNKNOWN to the R5 grade - E1 expects "EV 20/27 Oct Limited ->
   Low", which was unreachable before the fix. Default: the L3 A/B reads it; list per day in the packet.
4. Carried from 2b (coordinator-ruled, packet Known Deviations): estate read on UTC-day bounds; Q2 dispatch refusal;
   Q8 pooled local days; Findings settledness from R8 alone.

## Remaining (phase 2d), in order
1. L2 `backend/tests/test_ch5a1_reader_postgres.py` (non-mechanism, `pg_harness.fresh_database()` + `setup_cache`,
   seeded as CH-2/CH-3 L2 - `test_ch3_lifecycle_postgres.py:28,77` uses `run_threads(reader, writer, t, s)`; the
   outbox consume is `scheduling.stages.chain_threads(url, {"tenant_id", "site_id"})`, as `_settle_chain` above):
   each §A3 SQL (`chain/adapters/postgres_chain_read.py` `snapshots`, `finding_heads`, `findings_settled` `_UNSETTLED`
   `:43`, `has_change` `:52`) returns the expected rows; known_at hides a later revision, occurrence, selection; L5
   thread_lookup count at k before a third occurrence; R8 before/after consume; `has_change == bool(detail.change)` per
   seeded Action; board route under TestClient: capture the `read_scope.ReadScope` (opened by `perf.route`,
   `perf.py:133`) and assert `max_per_key() == 1` and none of `DELETED` (reuse the tuple from the L1 file). Keep the
   L2m TODO (phase-2 handoff item 5) as a comment block.
2. Collector (§A9 item 5): `tools/checks/chain_coherence.py` `_board_query` (`:384-394`) canonicalises `date=D` to the
   body's `window.from/to`; `day_windows` (`:67-85`) Kobo and Cold as Site-local days; `backend/tests/mechanism_dataset.py`
   `build_work` Kobo local-day bounds; Addis cases in `tools/checks/test_chain_coherence.py`; run it.
3. Guards A and W again after 1-2.

## Phase 3 needs
Unchanged: L3 polish-clone A/B (§A6, both sides on B's `days.json` windows), `chain_coherence collect/check`,
`tools/chain_perf_probe.py`, P1 cProfile, packet. Add to the packet: the two production fixes from 2b and the EV
site-type fix above, the four Known Deviations (item 4), and the importer list (phase-2 handoff + 2b additions +
`test_idx_gaps_postgres.py`, `test_out_c3_repeat_visits_postgres.py`, `test_ch5a1_board_contract.py`).
