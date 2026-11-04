# Review packet: CH-5a1 (ChainReader and the board read path)

Branch `task/CH-5a1-chain-reader`; final revision **33f06bcba** (code at c74ffbb22; the commits after it are tools and evidence). Not merged.
Authority: build sheet Part A (`AssetOpsV1-plan2/.agent/build-sheet-CH-5a.md`, incl. §A12 CH5a1-R). Evidence: `.agent/CH-5a1-phase-{1,2,2b,2c,2d}-handoff.md`, `.agent/CH-5a1-phase-3-results.md`.
**Status: OPEN BEFORE MERGE** (see the last section). USER_REVIEW: the build sheet sets no USER_REVIEW_REQUIRED flag; the coordinator decides (owner walkthrough policy). Architect rulings are needed for R-1, COH-7a and CH-5c sizing.

## Outcome delivered
- One request has one `ReadScope` (`read_scope.py`, opened by `perf.route`). It holds a ledger and a deep-frozen memo over `_window`, `claim_limit_snapshot_on` and every ChainReader port.
- `chain/read.py` ChainReader + `chain/adapters/postgres_chain_read.py` (SELECT only) replace `mini_overview`, `finding_index` and `estate.site_readiness*` on the board and the summary.
- R4 snapshot settledness, R5 `readiness_of`, R6 Site-local board day, R7 `site_cutoff`, R8 outbox settledness, L5 known_at-bounded occurrences, the thread join replacing `_lineage`/`refresh_chain`, R2 `site_list`.

## Files materially changed (58 files, +4752/-832 vs main)
- Production (`backend/assetops_backend/`): `read_scope.py` (new), `chain/read.py`, `chain/composition.py`, `chain/adapters/postgres_chain_read.py` (new), `chain/lookup.py`, `chain/lifecycle.py`, `chain/adapters/postgres_thread_sources.py`, `site_outcomes/{mini,board,read,composition,cold,ev}.py`, `outcome_api.py`, `perf.py`, `estate/{index,portfolio}.py`, `estate/adapters/postgres_estate_read.py`, `analytics/finding_index.py`, `analytics/adapters/postgres_assessment_store.py`, `main.py`.
- Tools: `tools/chain_perf_probe.py` (new), `tools/checks/chain_coherence.py`, `tools/checks/configuration-persistence.ps1` (`$pgReaders`), `tools/checks/test_estate_guard.py`, `tools/checks/test_chain_coherence.py`.
- Tests: new `test_ch5a1_{reader,scope,board_contract,reader_postgres}.py` + 4 goldens under `backend/tests/fixtures/ch5a1_board_contract/`; 20 adapted files (see the 2b/2c handoffs).

## Acceptance
| Item | Status | Evidence |
|---|---|---|
| A0 zero calls of `mini_overview`/`finding_index`/`estate.site_readiness*` | met | L1 ledger test; L2 board route under TestClient (none of `DELETED`) |
| A0 ledger max 1 per key (board, summary, Portfolio) | met-with-deviation | max 1 on boards and the Portfolio; the summary reads 3: `objectives ()` per Site (×3) and Kobo `productive_readings` twice, both `Reads.call` timing records, as on A, not memoised repeats (phase-3 results, Performance) |
| A0 board text unchanged except E1-E5 (L3 clone) | open | all differences are E1-E5 except R-1 (below) |
| A0 same on MD-0 (L3m) | blocked-on-MD-0 | |
| A0 measured timings reported | met | perf table below |
| A0 boundary: no detector/matcher/money/verification/lifecycle/copy change | met-with-deviation | copy unchanged; `GAPS_WITHHELD` deleted with its COPY entry (Q4, 2c); behaviour changes D-Q2/Q8/R8 below |
| A6 A/B on L3 clone, both sides on B's `days.json` | met | 56 requests per side, A = main a07452c63 |
| A6 E1 readiness | met | matches pre-flight §4; extra entry: summary month Kobo 3 Nov Unknown → Low |
| A6 E2 / E3 / E4 / E5 | met | E5 met for Kobo; Cold/EV threads changed by R-1 |
| A6 E3b | met | empty; (finding_id, revision_id) sets equal on every day board and the Portfolio |
| A6 no other difference | open | R-1 |
| A6 A side at the MD-0 merge; L3m + `--variant close` | blocked-on-MD-0 | A was main a07452c63 |
| A7 probe, 5 cold/5 warm, bytes, top-10 ledger | met (clone) / blocked-on-MD-0 (L3m) | `tools/chain_perf_probe.py` |
| A7 budgets reported, not relaxed | met | every cold/warm time and the Portfolio payload miss |
| A11 frozen memo values | met | L0 `test_ch5a1_scope.py` |
| A11 no re-derived join/window/day count/card rule outside `chain/` | met-with-deviation | `mini.estate_bounds` keeps the UTC estate day outside `chain/` until CH-5a2 B3 (D-UTC) |

## A/B diff (A2 vs B3; normalised `window.known_at`, `selection_token`, `links.self`): 30 of 56 requests, 617 paths
- Kobo day boards 8/8 (E2, E1, E4); Cold day boards 0/3; EV 2/2 (E1; R-1 on 27 Oct); summary-linked boards 8/9 (Kobo E4; Cold R-1; EV E1+R-1); summaries 3/3 (E4+E2); Portfolio 3/3 (R-1 only); Findings index 0/19; actions 6/9 (N0: top-level wall-clock `known_at`).
- E1: Kobo 17/24/31 Oct High → Limited; Kobo 1 Nov Unknown → Limited; Kobo 3/10/28/30 Oct and Cold 24/28/31 Oct unchanged; EV 20/27 Oct Limited → Low. Extra: summary month Kobo (local 3 Nov) Unknown → Low.
- E2: Kobo `PRODUCER_NOT_SETTLED` → settled rows/verdicts; derived lead outcome MG-4; COST 17/24/31 Oct priced through `money_head`.
- E3: `finding_gaps` equal on every day board. E4: Kobo windows local; summary Kobo card moves 31 Oct → 1 Nov (week, S), 2 → 3 Nov (month); each side's summary equals its own day board with 0 differences.
- E5: no Kobo occurrence change. **R-1** is outside E1-E5 (below).

## Performance (in process, read-only clone, ms; shared machine, ±15-25 %)
| URL | cold med | warm med | bytes | QW-1 cold/warm |
|---|---|---|---|---|
| Kobo board 31 Oct | 4,508 | 7,803 | 14,487 | 9,458 / 8,374 |
| Cold failure-night board | 1,815 | 1,114 | 15,553 | - |
| EV 27 Oct board | 4,664 | 1,039 | 12,218 | - |
| summary, week | 7,028 | 4,344 | 12,588 | 13,046 / 9,534 |
| Portfolio, week | 5,168 | 4,247 | 280,903 | 8,304 / 7,226 |
Budgets: cold ≤ 1 s and warm ≤ 300 ms p95 are missed everywhere; board ≤ 60 KB is met; Portfolio ≤ 100 KB is missed (2.8x). None are relaxed. Kobo top ledger: `_window` 2,139, `estate` 1,858, `money_head` 1,534, `mini_depth` 1,209, `dispatch` 691. The warm-above-cold inversion on Kobo is not investigated. P8 stub: R8 is 6.8-7.2 ms per Site on 3 outbox rows; the full-outbox P8 needs MD-0.

## P1 and CH-5c sizing (warm Portfolio, 4,482 ms)
- `select_evidence_scope` 2.10 s (pre-flight about 4.4 s): `cited_provenance` ×20, `cited_set` ×27, `link_rows_on` ×29, `claim_limit_on` ×7. DB round trips dominate; `_window` is 741 ms with max_per_key 1.
- `select_financial_scope` 0.73 s (was about 1.5 s): `site_coverage` ×3 0.40 s.
- By the R3 rule (per-row provenance dominates), CH-5c is about **1-2 units (batching)**. The Architect rules. The Portfolio payload is a separate residual for CH-5b/5c.

## Checks (final revision 33f06bcba, each file alone, `tools\run-host-tests.ps1`, Postgres on a `*_test` DB)
| file | result |
|---|---|
| test_ch5a1_reader_postgres.py (L2) | 7 passed (28 s) |
| test_ch5a1_board_contract.py (L1) | 13 passed |
| test_ch5a1_reader.py / test_ch5a1_scope.py (L0) | 24 / 7 passed |
| test_out_b2_mini.py / test_out_b4_route.py | 32 / 6 passed |
| test_out_b4_board_postgres.py | 5 passed (134 s) |
| test_w303_portfolio_api.py / test_w301_estate_api.py | 6 passed, 0 skipped / 11 passed |
| test_ch3_rows.py / test_ch2_threads.py / test_qw1_perf.py | 39 / 28 / 8 passed |
| tools/checks/test_chain_coherence.py | 87 passed |
| tools/check-architecture.ps1 / check-agent-workflow.ps1 | passed / passed |
- 0 failures in these reruns. Estate guard self-tests 15/15 passed, in 3 chunks, 759 s, at 2d. No guard file has changed since then (`git log 073e96f2f..HEAD` on `tools/checks/*.ps1` and `test_estate_guard.py` is empty).
- The other scoped files and their counts are in the 2b/2c tables. Phase 3 focused: 224 passed. Each of the three phase-3 fix tests failed on revert.
- Frontend: 13 importer files, 407 passed (2c). `npx vitest related` fails at startup ("Failed to parse source for import analysis ... .py"), so the explicit importer list was run instead.
- **Not run:** the full real-Postgres backend suite. It is due on the final revision after the rulings and MD-0.

## Importers (§A9 item 4)
These are the phase-2 handoff list, plus `test_out_b4_main_binding`, `test_ch2_threads` (2b), `test_idx_gaps_postgres`, `test_out_c3_repeat_visits_postgres`, `test_ch5a1_board_contract` (2c), `test_ch5a1_reader_postgres` and `tools/checks/test_chain_coherence.py` (2d).

## Production fixes found by tests
1. 2b: `ChainRequest.day` `m.measure` → `m.key`.
2. 2b: `mini.estate_bounds`, so the estate read keeps UTC-midnight bounds (`check_window`).
3. 2c: `SITE_TYPE_OF_DOMAIN["ev_charging"]` = `"EV_CHARGING"`.
4. 0c9cfe98e: the mini route accepts its own Site-local window.
5. 9cbe253c9: Portfolio rows emit `public_thread`.
6. c74ffbb22: the board money port binds `site_overview.read.consequences`.

## Known deviations
- **D-UTC:** the estate read stays on UTC-day bounds while the board day is local, until CH-5a2 B3.
- **Q2:** a dispatch refusal now unsettles every measured outcome (UNKNOWN).
- **Q8:** cold/EV readiness pools all intersected local days (32 for an unaligned 31-day window).
- **R8 alone:** Finding settledness no longer follows gap days; an unsettled chain shows no Findings.
- **D1:** `lead_finding` pinned rule uses `day.settled` as `discovery_complete`.
- **D2:** `priced` per §A3 only. D4: `covering_days` unused in production, kept for its tests.
- **D-2d-1:** `mechanism_dataset.build_work` local-day bounds are pending MD-0.
- **D-2d-2:** "later selection" = snapshot latest-row selection.
- **D-2d-3:** L2 seeds per module, not `setup_cache`.
- **The four 2c defaults are accepted** (2d handoff): the c3 spy is an R5 consequence; idx_gaps p5 NO_DATA; EV readiness listed per day; the 2b deviations stand.
- **Thread-view classes:** threads carry `lookup.state_classes` and lifecycle `applied_states`/`verified_states` (for a state on another day), not per-Finding booleans.
- **vitest `related`** has a startup failure; the explicit importer list was substituted.

## Residual risk
- **2d test order:** an APPLY run before F04 left no unconsumed `finding.revised`, so the APPLY test runs last. The cause is not investigated.
- The memo returns `MappingProxyType`/tuples, so an unscoped consumer that mutates them would TypeError. None was seen in the scoped runs.
- Performance is far over budget, and `money_head` alone is about 5x warm budget.

## DS-R1 and OL-1
| §A8 item | Resolution |
|---|---|
| Wall-clock freshness on the board | Fixed: R4 snapshot settledness |
| Board day = UTC day | Fixed: Site-local day (R6); estate read UTC until CH-5a2 B3 (D-UTC) |
| Dispatch analytic UTC day key | Labelled keep → SWEEP-DS |
| Exact-revision lineage join | Fixed: thread join (`linked_actions` same thread+segment) |
| Duplicated state tuples | Fixed: `lookup.state_classes` |
| Occurrence counts include later occurrences (L5) | Fixed (L2 count 2 at k1, 3 at None); see R-1 |
| Portfolio evidence cell `evidence_cell_state` | Labelled keep → CH-5c |
| "Verified on example data" | Labelled keep → CH-5a2 |
OL-1: met. ChainReader names measures and mechanisms only, and outcomes stay `outcome_map.finding_signal_key`.

## OPEN BEFORE MERGE
1. **R-1:** the L5 filter compares wall-clock `source_known_at` with the story-time Cold/EV evidence cutoff, so threads are hidden (COH-10 ×7, COH-11 ×2). Proposed default: bound occurrence visibility by the request `known_at` and use the evidence cutoff for thread state only. Alternative: a story-time instant, as R8.
2. **COH-7a ×1:** `summary_day` picks the Kobo window [31 Oct 21Z, 1 Nov 21Z) for the S request [31 Oct, 1 Nov). Options: keep `to − 1 µs`, use the local day of `from`, or adapt COH-7a.
3. **MD-0 not merged.** Pending on it: L2m/L3m, the A-side rerun at the MD-0 merge, D-2d-1, and the P8 full-outbox measurement.
4. **Full real-Postgres backend suite** (with the JUnit zero-skip check) on the final revision after 1-3.
5. **Rulings and user review:** the Architect rules on the extra E1 entry and CH-5c sizing. User review: no USER_REVIEW_REQUIRED flag is set in Part A; the coordinator decides.

## User-review focus
- The R-1 and COH-7a rulings.
- Whether the E2 Kobo change (settled rows instead of `PRODUCER_NOT_SETTLED`) and the summary card's local-day move read correctly.
- The performance gap against the budgets.
