# CH-5a1 phase 2 handoff - PARTIAL (wiring landed at 8d9cda125; tests not yet adapted)

Authority unchanged: build sheet Part A (incl. §A12) + pre-flight §1/§2/§6. Phase 1 handoff: `CH-5a1-phase-1-handoff.md`.
Stopped at the context budget after the production wiring commit. Resume at "Remaining (phase 2b)" item 1.

## Landed (commit 8d9cda125), anchors under `backend/assetops_backend/`
- `chain/adapters/postgres_chain_read.py` (new, SELECT only): `PostgresChainRead.snapshots` (SnapshotReader.latest),
  `finding_heads` (§A3 SQL verbatim; columns confirmed vs 0009/0042/0045: `f.domain`, `f.analytic_id`, `f.mechanism`,
  `finding_merge.superseded_finding_id/created_at`), `findings_settled` (R8/P8 EXISTS anti-join, bare types,
  `occurred_at <= k`), `has_change` (EXISTS action_policy_change over `unnest(:ids)`; MappingProxyType, lower-case keys).
- Guard: `tools/checks/configuration-persistence.ps1` `$pgReaders` gains the module with a ruling comment;
  `tools/checks/test_estate_guard.py` `test_chain_reader_write_rejected` (probe INSERT must be refused). Self-test run
  was started from the PowerShell tool and had not finished when I stopped (it exceeded 600 s under load; the bash
  run fails only on ExecutionPolicy for temp copies - environmental). **Re-run it** (command below).
- `chain/composition.py:115` `build_chain_reader(url, consequences=, verification=) -> (reader, dispose)`; its money
  port returns `{"body": jsonable consequence read, "source": stored_source(...)}` (site_overview/read.py:46).
- `chain/read.py`: `ChainRequest.day(..., readiness_days=)` (`:225`; mini: gaps over the 31 local work days, readiness
  over `(D,)`, one snapshot read); grades frozen; `action_facts` keys lower-cased; `money_head` (`:265`) parses the
  real consequence body (`money_eligibility.state`, `currentness.current_amount_shown`, `consequence.display.*`);
  new pure `lead_finding` (`:133`, CH5a1-R Q5: pinned while unsettled/closed, else discovered = max episode_start,
  min finding_id).
- `site_outcomes/composition.py`: builds the reader with `site_overview.upstream.consequence_read` (P6) and a
  jsonable `VerificationService.summary` callable; `BoardServices.chain_reader` (`read.py:117`); dispose chained.
- `site_outcomes/mini.py`: `MiniPorts` (`:183`) now `source, depth, dispatch, assumption, chain_day, chain_findings,
  findings_settled, estate, action_index, action_facts, money, work, plans, objectives, pin, productive_*`
  (overview, finding_index, readiness, verification, action, finding_history removed). `compose` (`:365`): R6
  `board_day(day, tz)`; reads named `source`, `chain_day`, `chain_findings`, `findings_settled`, `money_head`,
  `action_facts` (the per-Action memo inside is `action_read`); `base = source_open and day.settled and dispatch`
  (Q2); assessment from the dispatch body + `assessment_state`; `read_ok` (source and day read) replaces
  `overview is not None`; unsettled Findings mark `chain_findings` failed (PARTIAL). `finding_gap_line(day_facts, 31)`
  (`:274`; NO_DATA-only -> "no checked readings", any PENDING -> "not assessed"; withheld always False, Q4).
  `_findings` (`:625`) over `FindingHead` with `selected_revision_link` (C4, `analytics/finding_index.py:108`, now
  used by the index too). `_lineage`, `index_settled` deleted.
- `site_outcomes/board.py`: `refresh_chain`, `BASIS_REFRESHED`, `FindingFact.refreshed_from` deleted;
  `linked_actions` (`:533`) = same thread id and segment; no thread -> exact origin revision.
- cold/EV: read renamed `readiness_of`; `read.py` `_shared.readiness` = `ChainRequest.day(local_days(lo,hi,tz))`
  (no `covering_days` widening, no estate call).
- `read.py`: `board_cutoff(domain, known_at, resolved)` (`:580`) -> `site_cutoff`; board day for every domain =
  `_last_local_day(window.to, tz)`; summary `summary_day(hi, site.timezone)` (`:512`); `mini_summary_day` deleted;
  `_prefetch` (`:461`) local mini bounds, no `site_readiness_many`. `FINDING_SCOPE` (`:63`).
- `estate/index.py:398` `site_list` (`_scope` only, same single `_read` open); `_cutoff` (`:171`) via `site_cutoff`;
  `outcome_api.py:159` calls `site_list`.

## Tests run
- L0 + board unit run (before adapting tests): 124 passed, 31 failed - all 31 in `test_out_b2_mini.py` (old Fake
  ports); collection errors in `test_out_b4_read.py` (imports `mini_summary_day`) and `test_link_lineage.py`.
  `test_ch5a1_reader/scope`, `test_out_b1_board`, `test_out_b3_cold_ev`, `test_ch3_rows`, `test_out_b4_imports` pass.

## Remaining (phase 2b), in order
1. `tests/test_out_b2_mini.py`: rewrite `Fake.ports()` (`:80-112`) to the new MiniPorts (fixture `DayFacts`,
   `FindingHead`, `ActionFacts`, `MoneyHead` from `chain.read`; map old overrides: `overview` -> `source`/`day`/
   dispatch `limitations`; `finding_index` status/gaps -> `findings_settled`/day gaps; `readiness` -> day
   readiness); delete the m1-m7 lineage tests (`:431-578`) and add thread-join cases. Expected-value changes allowed
   only within E1-E5.
2. `test_out_b4_read.py:12,21-23` -> `summary_day` (Addis + UTC); `test_link_lineage.py` rewritten to the thread
   join (`linked_actions` same thread+segment; no thread -> exact revision).
3. Scoped §A9 item 4 list (run one at a time, Postgres ones on `pg_harness.fresh_database()`): b4_board_postgres
   (`:369` dict key), b4_route (site_list replaces scope), b4_window, qw1_perf, qw2_reuse (prefetch keys / no
   readiness batch), qw2_many_postgres, test_ch2_*, test_ch3_*, w301_estate_api, w303_portfolio_api, polish_pa1,
   out_d4, `tools/checks/test_chain_coherence.py`; also `test_w601c_request_detail.py` (scope route test).
   Watch for TypeError on MappingProxyType (thaw at the consumer).
4. L1 `test_ch5a1_board_contract.py` (fixture ChainReader; goldens need the phase-3 A side - generate goldens from B
   with E1-E5 listed, or mark golden capture for phase 3), ledger 0 calls of mini_overview/finding_index/
   evidence_readiness/estate.site_readiness*.
5. L2 `test_ch5a1_reader_postgres.py` (non-mechanism): each §A3 SQL rows; known_at hides later revision/occurrence;
   R8 true/false around an unconsumed `finding.revised`; `has_change` parity with `bool(detail.change)`; L5 count at k
   before a third occurrence; board route under TestClient ledger max 1 and none of the three names.
   **L2m TODO (do not build until MD-0 merges):** every §A3 port over 14-day Kobo/Cold/EV on `mechanism_db()`;
   `readiness_of` per MD-0 day = the E1 MD-0 list; R8 around `late_fill(KOBO-001, D7)` before/after consume; board
   ledger max 1 on Kobo D13, Cold D13, EV D9.
6. Collector (§A9 item 5): `tools/checks/chain_coherence.py` `_board_query` (`:384-394`) canonicalise to the body's
   `window.from/to`; `day_windows` (`:67-85`) Kobo and Cold as Site-local days; `backend/tests/mechanism_dataset.py`
   `build_work` Kobo local-day bounds; Addis cases in `tools/checks/test_chain_coherence.py`.
7. Frontend `npx vitest related --run src/sites/outcomeBoardClient.ts`; guards A and W; estate guard self-tests.

## Deviations / open questions (proposed defaults, proceeding on them)
- D1 `lead_finding` pinned rule uses `day.settled` as the overview's `discovery_complete` (the overview's inputs are
  gone). Default: accept; the A/B gates it.
- D2 `money.priced` per §A3 only (no `money_state` seam/upstream checks). Default: accept; A/B gates it.
- D3 `BoardServices.finding_reads` / composition param kept but unused (main.py still passes it). Default: delete in
  phase 2b if no test needs it.
- D4 `covering_days` (read.py:153) now unused in production; kept for its tests.
- Q: the cold/EV readiness read runs at the request `known_at`, not the overview-resolved cutoff (as before).

## Importers for the packet (site_outcomes.*, chain.lookup, perf, estate.index)
tests: ch0_tick_timing, ch2_threads, ch3_lifecycle, ch3_rows, ch5a1_scope, cov_partial, fix01_windowed_dedupe,
idx_gaps_board, idx_gaps_postgres, link_lineage, out_b1_board, out_b2_mini, out_b2_vocabulary, out_b3_cold_ev,
out_b4_board_postgres, out_b4_imports, out_b4_main_binding, out_b4_read, out_b4_window, out_c2_board, out_c3_cold_cost,
out_c3_repeat_visits_postgres, out_c4_ev_warnings_postgres, out_c4_mini_ev, out_d2_objectives, out_d4_board,
out_d5_objectives_postgres, out_e4_readback, out_w2_summary_window, polish_pa1_board_truth, polish_pa2a_server_copy,
polish_pa2b_plan_due_assets, post_w6_w3_estate_links, qw1_perf, qw2_reuse, w301_estate_api,
w301_estate_index_postgres, w302_estate_cursor, w303_estate_cursor, w303_portfolio_api, walk1_3b_target_progress,
walk1_5_solar_window, walk1_objective_min_days_postgres, walk1_productive_sales; tools/checks/chain_coherence.py,
tools/checks/test_chain_coherence.py. (`idx_gaps_board`, `out_c2_board`, `out_c4_mini_ev`, `walk1_*` also build
MiniPorts or read the overview port - check them in item 3.)

## Commands
- bash: `source C:/Users/assef/AppData/Local/Temp/claude/C--Users-assef-Bineyame-AssetOpsV1/809ecc09-3853-48b6-b795-60539b50a963/scratchpad/ch5a1env.sh`
  then from `backend/`: `$PY -m pytest tests/<file> -q -p no:cacheprovider | tail`.
- Estate guard self-tests (PowerShell tool, run_in_background, >600 s under load): set `$env:PYTHONPATH` (worktree
  backend;contracts;tools;simulator;gateway;host;field) and `$env:ASSETOPS_GUARD_PYTHON`, then
  `python -m pytest tools/checks/test_estate_guard.py -q -p no:cacheprovider`.
- Guards: `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1` (PowerShell tool, no -ExecutionPolicy).
- Phase 3: L3 clone A/B, chain_perf_probe.py, P1 cProfile, packet (unchanged from phase 1 handoff).
