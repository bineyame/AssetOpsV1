# CH-4 phase 1 handoff (PARTIAL: backend core landed; stopped at the context cap)

Branch `task/CH-4-opportunity` in worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch4`, cut from plan2 main `e207f328f`.
Commits: `fbb6d29a6` backend core, `ce5d6a901` L0 tests and expected bodies, `066ad51f9` Findings count rule.
Build sheet: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-CH-4.md` (authoritative).
The sheet names the branch `task/CH-4-opportunity-threads`; the dispatch named `task/CH-4-opportunity`, which is used.

## Pre-flight answers (no Architect questions)
- P1: rule 8 of `tools/checks/configuration-persistence.ps1` lists writer tables only. Readers are a file list,
  `$pgReaders` (:904). The estate reader and thread sources already read `mini_opportunity*`, so no edit is needed.
- P2: consumers of `opportunity` and the PRODUCTIVE_USE card:
  - `test_w303_portfolio_api.py:382` (updated);
  - `test_w303_portfolio_scope_snapshot_postgres.py:301,336-337,438` (NOT yet updated: the card tail and the
    UNSUPPORTED literal);
  - `F/estate/estateClient.ts:376`, `EstatePortfolio.tsx:385-417` (static panel), `portfolioFixtures.ts:165,219`,
    `estatePortfolio.test.tsx:381-393,581-584`;
  - `tools/checks/chain_coherence.py:546-552` (COH-6), the bundles `portfolio.week.p1.json:18`,
    `test_chain_coherence.py:37,130`, and `expected-today.json:167-213` (6 COH-6 entries to delete).
  - `demo_combined_finish.py` reads neither field.
- P3: `opportunity_count` readers:
  - backend: `portfolio.py` (now the item count), `test_w303_portfolio_api.py:398` (updated),
    `test_cov_partial_portfolio.py:228,246` (asserts int; passes);
  - frontend: `estateClient.ts:357`, `EstatePortfolio.tsx:711-716`, `portfolioFixtures.ts:195`,
    `estatePortfolio.test.tsx:1236-1313`.
  - `openOpportunitySuffix` and `openOpportunitySiteCount` are read only by `EstatePortfolio.tsx:68,716` and the
    test `walk1_6_d5_strip_names_open_board_opportunities` (:1286-1313), so they can be deleted.
- P4: `G-portfolio-opportunity` appears in `frontend/docs/architecture/v69-dependency-registry-pilot.json:422` and
  `F/ui/gapCatalogue.ts:42`, with placements `portfolio.opportunity.review-finding` and `.inspect-headroom`.
  Retire it in both and remove the MissingClaims at `EstatePortfolio.tsx:408,411`. The scanner is
  `tools/checks/missing-claim-scan.mjs`.
- P5: `lc.thread_view(events, Occurrence, day, known_at, complete=(), close_after)` needs no Finding-only field.
- P6: the route is `B/mini_decisions_api.py:247`, with `known_at` as a query list. The frontend helper is
  `siteOpportunityHref` (`F/shell/operatorSiteRoutes.ts:208`). The board link is bare, as `work_links.py:173` is.
- P7: `OPPORTUNITY_LOOKUP` (`B/chain/lookup.py`) keeps the tuple convention:
  - txt3 is the study as JSON text (with `selected_at`, `seq`, `joined_at` and `source_known_at`), day1 is
    `last_day`, and txt4 is `site_type`;
  - the E branch is the shared `_EVENTS` constant, also used by `LOOKUP`.
- P8 (L4, run on `assetops_polish_full_test`, SELECT only): `skipped_ineligible: 2`. The Kobo headroom thread
  `2fc15fab-…` holds OPP-000003 (#1) and OPP-000004 (#2), and both start 2026-10-31T00:00+03:00. The ends were not
  printed (the dry run prints only the start); confirm them in L3 with SQL on the clone.

## Landed (backend)
- `B/chain/threads.py`:
  - `OPP_MIN_ELIGIBLE_DAYS`;
  - `opportunity_source` returns `None` below the minimum, and its episode is the eligible days (R1, R2).
- `B/chain/adapters/postgres_thread_sources.py`:
  - `_OPPORTUNITY_SOURCES` gains `eligible_days` and `day_rows`;
  - `sources()` returns the placed sources, then the `None`s;
  - `opportunity_threads()`; `lookup(..., site_id=, opportunity_window=)` adds `"opportunities"`;
  - `_OPPORTUNITY_HEADS` goes into `lifecycle_inputs["opportunity_heads"]`.
- `B/chain/backfill.py`: `_placeable` counts `skipped_ineligible` in step b, in both the live and dry-run paths.
- New `B/chain/vocabulary.py` (§2.2) and `B/chain/opportunities.py` (`opportunity_items`, §2.1).
- `B/chain/lifecycle_run.py` `thread_causes`: opportunity SUPPORT_LOST (R6).
- `B/outcomes/outcome_map.py`: `LENS_OF_CATEGORY`, `thread_signal_key`, `lens_flags` (R5).
- `B/mini_depth/rules.py`: `observed_headroom_range` and `headroom_on_every_eligible_day`; `projection.py` calls
  the latter (R3).
- `B/estate/adapters/postgres_estate_read.py`: `opportunity_threads`.
- `B/estate/index.py`: `opportunity_read` (shared), and `opportunities` plus `summary.opportunity_count` on Findings.
- `B/estate/portfolio.py`: `productive_use_card`, `opportunity_block`, `summary.opportunity_count` and
  `opportunity_labels`, and `CARD_DESTINATION`.
- `B/site_outcomes/board.py`: `SignalFact.ref`, and `with_threads` replaces the headroom href and ref.
  `read.py:413` passes the renewable five days.

## Deviations so far (for the packet)
- D1: when the opportunity read raises, the Portfolio `opportunity.state` and the PRODUCTIVE_USE card read
  `UNKNOWN`, with the new line "Opportunities could not be read". The sheet names only FOUND and NONE.
- D2: Findings `summary.opportunity_count` is null unless the read is complete (the existing summary rule,
  `test_w301_estate_api.py:119`).
- D3: the board issue `ref.thread` carries `occurrence_no` and `segment_no` as null (opportunity-level thread).
- R7: the Value line is still not built (CH-9), as the sheet says.

## Checks so far
L0 plus the scoped non-Postgres set: 377 passed and 1 failed. The failure (`test_w301 incomplete summary`) was
fixed in `066ad51f9` and not rerun. Rerun this command first:
`tools\run-host-tests.ps1 -- backend/tests/test_ch4_opportunities.py backend/tests/test_ch2_threads.py backend/tests/test_ch2_backfill_cli.py backend/tests/test_ch3_lifecycle.py backend/tests/test_ch3_rows.py backend/tests/test_w301_estate_api.py backend/tests/test_w303_portfolio_api.py backend/tests/test_w303_portfolio_reduction.py backend/tests/test_out_b1_board.py backend/tests/test_out_b2_mini.py backend/tests/test_w403_opportunity_result.py backend/tests/test_w402_rules.py backend/tests/test_w402_projection.py backend/tests/test_out_a1_outcome_map.py backend/tests/test_walk1_5_solar_window.py backend/tests/test_cov_partial_portfolio.py tools/checks/test_chain_coherence.py -q`

## Remaining, in order
1. The L2 test `backend/tests/test_ch4_opportunity_postgres.py` (§8.2), registered in `setup_cache.py:77`
   `FUNCTION_OPS`.
2. The Postgres scoped tests: `test_ch2_thread_store_postgres.py` (its `:124,164` read `sources()`, so drop the
   `None`s there), `test_ch3_lifecycle_postgres.py`, `test_w301_estate_index_postgres.py`,
   `test_w303_portfolio_fixture_postgres.py`, `test_w303_portfolio_scope_snapshot_postgres.py` (P2 lines),
   `test_out_b4_board_postgres.py`, and the w403 opportunity read/route tests.
3. Coherence (§6):
   - `tools/checks/chain_coherence.py` COH-6 (:529-553) and COH-10 (:710-770); a new COH-16 in `RULES` (:949);
   - fixtures `clean_opportunity`, `coh6_opportunity_missing`, `coh16_opportunity_disagree`; the bundles'
     `portfolio.*.json` `opportunity` shape plus the Findings `opportunities`;
   - `expected-threads.json` `kobo-headroom` → `["OPP-000003","OPP-000004"]`;
   - delete the 6 COH-6 entries in `expected-today.json`.
4. Frontend (§5):
   - `estateClient.ts`, `findingIndex.tsx` (OpportunityList and the table rows), `EstatePortfolio.tsx` (the panel
     and the strip), `PortfolioOutcomes.tsx:162-177` (delete);
   - `SiteFindingIndex.tsx:89-115` (the helper text), CSS `.opp-list`/`.opp-limit`, and the tests;
   - retire `G-portfolio-opportunity` (P4).
   - Junction `frontend\node_modules` to plan2.
5. Guards: A, W, N, V, M, and the chain-coherence fixtures. Then L3 (§8.5) on the `ch4` clone, and record the
   verbatim texts.
6. The packet `.agent/review-packet-CH-4.md`.

## CH-1b overlap (flag to the coordinator)
CH-1b edits `chain/backfill.py`, `chain/adapters/postgres_thread_sources.py`, `configuration-persistence.ps1`,
`test_chain_coherence.py` and `test_ch2_thread_store_postgres.py`. CH-4 touches the first two and will touch the last
two. Expect textual conflicts in `sources()`/`lookup()` and in run_threads step b.
