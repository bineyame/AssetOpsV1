# Review packet: CH-5a1 (ChainReader and the board read path)

Branch `task/CH-5a1-chain-reader`. **CH5a1-R2 fix round** (sheet §A13) on 110d0057a: ff033ade1 (R-1), d088b16f1 (COH-7a), e542064b2 (ledger); this packet commit follows. Not merged.
Authority: build sheet Part A (`AssetOpsV1-plan2/.agent/build-sheet-CH-5a.md`, incl. §A12 CH5a1-R and §A13 CH5a1-R2). Evidence: `.agent/CH-5a1-phase-{1,2,2b,2c,2d}-handoff.md`, `.agent/CH-5a1-phase-3-results.md`, and the R2 section below.
**Status: OPEN BEFORE MERGE only on MD-0 and the full suite** (last section). R-1, COH-7a, the extra E1 entry and the ledger are applied. USER_REVIEW: the build sheet sets no USER_REVIEW_REQUIRED flag; the coordinator decides.

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
| A0 ledger max 1 per key (board, summary, Portfolio) | met | R2: `Reads(site)` keys every composer read `(site_code, *args)`, so `objectives` is `(KOBO-001,)`, `(COLD-LAB-001,)`, `(EV-LAB-001,)`; `productive_readings` is memoised (same arguments on day 1 of a month). L1 `test_ch5a1_summary_ledger.py` asserts max 1 on the summary; clone: summary week 54 keys, `repeated []` (key list below) |
| A0 board text unchanged except E1-E5 (L3 clone) | met | R2 clone: A2 vs R2 24/56 requests, 592 paths, all E1-E5; the R-1 paths are gone |
| A0 same on MD-0 (L3m) | blocked-on-MD-0 | |
| A0 measured timings reported | met | perf table below |
| A0 boundary: no detector/matcher/money/verification/lifecycle/copy change | met-with-deviation | copy unchanged; `GAPS_WITHHELD` deleted with its COPY entry (Q4, 2c); behaviour changes D-Q2/Q8/R8 below |
| A6 A/B on L3 clone, both sides on B's `days.json` | met | 56 requests per side, A = main a07452c63 |
| A6 E1 readiness | met | matches pre-flight §4, plus the accepted extra entry (§A13): summary month Kobo, local 3 Nov, Unknown → Low |
| A6 E2 / E3 / E4 / E5 | met | E5 met for every Site after R-1 (Cold/EV threads unchanged from A) |
| A6 E3b | met | empty; (finding_id, revision_id) sets equal on every day board and the Portfolio |
| A6 no other difference | met | R2 clone (below) |
| A6 A side at the MD-0 merge; L3m + `--variant close` | blocked-on-MD-0 | A was main a07452c63 |
| A7 probe, 5 cold/5 warm, bytes, top-10 ledger | met (clone) / blocked-on-MD-0 (L3m) | `tools/chain_perf_probe.py` |
| A7 budgets reported, not relaxed | met | every cold/warm time and the Portfolio payload miss |
| A11 frozen memo values | met | L0 `test_ch5a1_scope.py` |
| A11 no re-derived join/window/day count/card rule outside `chain/` | met-with-deviation | `mini.estate_bounds` keeps the UTC estate day outside `chain/` until CH-5a2 B3 (D-UTC) |

## A/B diff (phase 3: A2 vs B3; normalised `window.known_at`, `selection_token`, `links.self`): 30 of 56 requests, 617 paths. R2: A2 vs R2 24 of 56, 592 paths (the R-1 paths removed; see the R2 section)
- Kobo day boards 8/8 (E2, E1, E4); Cold day boards 0/3; EV 2/2 (E1; R-1 on 27 Oct); summary-linked boards 8/9 (Kobo E4; Cold R-1; EV E1+R-1); summaries 3/3 (E4+E2); Portfolio 3/3 (R-1 only); Findings index 0/19; actions 6/9 (N0: top-level wall-clock `known_at`).
- E1: Kobo 17/24/31 Oct High → Limited; Kobo 1 Nov Unknown → Limited; Kobo 3/10/28/30 Oct and Cold 24/28/31 Oct unchanged; EV 20/27 Oct Limited → Low; **summary month Kobo card (local 3 Nov) Unknown → Low** (accepted, §A13: the honest R5 `readiness_of` grade of a part day; also for DS-1's honest-state table).
- E2: Kobo `PRODUCER_NOT_SETTLED` → settled rows/verdicts; derived lead outcome MG-4; COST 17/24/31 Oct priced through `money_head`.
- E3: `finding_gaps` equal on every day board. E4: Kobo windows local; summary Kobo card moves 31 Oct → 1 Nov (week, S), 2 → 3 Nov (month); each side's summary equals its own day board with 0 differences.
- E5: no occurrence change on any Site (R-1 fixed).

## Performance (R2 rerun, `tools/chain_perf_probe.py`, in process, read-only clone at e542064b2, ms; machine quieter than phase 3)
| URL | cold med | warm med | bytes | phase 3 cold / warm |
|---|---|---|---|---|
| Kobo board 31 Oct | 5,191 | 3,434 | 14,487 | 4,508 / 7,803 |
| Cold failure-night board | 1,603 | 742 | 16,018 | 1,815 / 1,114 |
| EV 27 Oct board | 1,753 | 732 | 12,528 | 4,664 / 1,039 |
| summary, week | 6,357 | 3,846 | 12,588 | 7,028 / 4,344 |
| Portfolio, week | 4,208 | 2,970 | 281,523 | 5,168 / 4,247 |
- Budgets (none relaxed): cold ≤ 1 s and warm ≤ 300 ms p95 are missed everywhere; board ≤ 60 KB is met; Portfolio ≤ 100 KB is missed (2.8x).
- The Cold/EV bytes grew by the restored threads (R-1).
- Kobo top ledger (warm): `_window` 1,051, `money_head` 862 (`chain.money_head` 849), `estate` 749, `mini_depth` 555, `action_facts` 327, `action_read` 320, `dispatch` 295.
- P8 stub unchanged (needs MD-0).

### Finding R2-P1: the Kobo warm-over-cold inversion is load, not a code path
- It does not reproduce. The R2 probe gives cold 5,191 and warm 3,434; a 6-request sequence in one process gives 6,758 (first, profiled), 3,224, 3,822, 2,839, 2,590 and 4,133 (profiled).
- The board waits on the database. A warm request is 1.2-1.6 s CPU against 2.6-4.1 s wall, and `select.select` (the socket wait) takes 1.55 s of the 4.1 s profiled warm request.
- The phase-3 warm ledger was about 2x the R2 one on every line, not on one read. For example `_window` 2,139 → 1,051, `estate` 1,858 → 749 and `money_head` 1,534 → 862. The ledger names, the key count (35) and max_per_key (1) are the same. The DB sessions stay at 21, with no growth.
- So the phase-3 warm runs, issued back to back, met contention on the shared Postgres server, while the cold children were spaced by about 3 s of process start-up. Nothing is repeated or leaked between requests.
- A real cold cost: the first request opens 147 psycopg connections (0.23 s of `_connect_gen`); warm requests reuse the pool.

### Finding R2-P2: `_window` (EXPLAIN) is round trips and repetition; no slow plan
- On the warm Kobo board, `assessment._window` is 1,060 ms over **5 keys** (about 210 ms each). It is not one slow read.
- Per call: `_EVIDENCE` about 34 ms (1,070 rows), the run-evidence read about 38 ms, the input-sha `basis` (Python) about 39 ms, `_reading` 8 ms, and about 15 small statements at 3-5 ms each.
- `EXPLAIN (ANALYZE, BUFFERS)` of `_EVIDENCE` (`postgres_assessment_store.py:118`; Kobo, [29 Oct 18:00, 31 Oct 06:00), 6 roles):
  - plan: Hash Join of two Seq Scans, `ingestion_disposition` 10,300 rows and `accepted_evidence` 10,300 rows (9,230 removed by the filter);
  - Execution 20.5 ms, Planning 10.5 ms, 1,969 shared hits, no reads.
  - At 10k rows a seq scan is the right plan. The `COALESCE(interval_*, source_time)` range predicates cannot use `accepted_evidence_site_role_time`, so at production volume this would degrade.
- Cheap options, reported and not built:
  - (a) An expression index `(tenant_id, site_id, role, COALESCE(interval_start, source_time))`. It is a migration, it matters only at volume, and on this clone it would save little.
  - (b) A repetition: 2 of the 5 keys read the same evidence range twice, once live (`cutoff` None, `knowledge_at` = the memo sentinel) and once at `cutoff` = the request's read time (2026-11-04 12:09Z). They are different memo keys with identical rows. Sharing the evidence, configuration and attestation part of `_window_read` on `(t, s, read_range, roles, knowledge_at)`, or normalising a cutoff equal to read-now to None, saves about 2/5 of `_window` (about 0.4 s warm). That is a semantics call for CH-5c.
  - (c) The planning cost (10 ms per call) could go with server-side prepared statements.
  - None of these meets the 300 ms budget alone. The per-request round-trip count is the main lever, which is CH-5c batching.

## P1 and CH-5c sizing (phase 3, warm Portfolio, 4,482 ms; not rerun)
- `select_evidence_scope` 2.10 s: `cited_provenance` ×20, `cited_set` ×27, `link_rows_on` ×29, `claim_limit_on` ×7. DB round trips dominate; `_window` is 741 ms with max_per_key 1.
- `select_financial_scope` 0.73 s: `site_coverage` ×3 0.40 s. By the R3 rule, CH-5c is about **1-2 units (batching)**; plan row CH5a1-R2 / CH5c-R2 is the owner's.

## CH5a1-R2 fix round (§A13)
- **R-1.** `LOOKUP`/`OPPORTUNITY_LOOKUP` filter occurrences on `:kv` (`chain/lookup.py:31,37,58`). The board (`site_outcomes/read.py` thread call) and the Portfolio (`estate/portfolio.py` `attach_threads`) pass the request/envelope transaction-time `known_at` as `visible_at`. `postgres_thread_sources.py` `_lookup` start-day read uses `:kv`. `known_at` (the story cutoff for cold/EV) still bounds events and snapshots. `postgres_chain_read.py` `_FINDING_HEADS` already compared with `ChainRequest.k` (= the request `known_at`), so it gained a comment, no change.
- **COH-7a.** `tools/checks/chain_coherence.py` `_coh7a_window`: a `mini_grid` summary Site expects `chain.read.board_day(summary_day(to, tz), tz)` (imported); every other Site expects the requested window. It is one helper and one call, commented for the MD-0 merge.
- **Ledger.** `site_outcomes/mini.py` `Reads(site)` and `Reads.call(..., memo=)`; `Reads(c)` in the mini, cold and EV composers; `productive_readings` uses `memo=True` at both calls.
- **Summary ledger key list (clone, week, 54 keys, max 1).** By read: `action_facts` 1, `action_index` 1, `action_read` 1, `assessment._window` 3, `assumptions` 1, `chain.day` 3, `chain.findings` 1, `chain.findings_settled` 1, `chain.has_change` 1, `chain_day` 1, `chain_findings` 1, `cold_findings` 1, `cold_overview` 1, `dispatch` 1, `domain_action_index` 2, `estate` 1, `ev_availability` 1, `ev_depth` 1, `ev_findings` 1, `ev_overview` 1, `findings_settled` 1, `mini_depth` 4, `objectives` 3 (one per Site code), `plans` 3, `productive_price` 1, `productive_readings` 1 (`('KOBO-001', [u], 31 Oct 21Z, 1 Nov 21Z)`, plus 1 memo hit), `productive_users` 1, `readiness_of` 2, `source` 1, `work_index` 12.
- **Clone** `assetops_chainclone_ch5a1r2_test`, fresh from the polish DB (never ticked). Steps, all exit 0:
  - create --migrate 3 s; backfill a,b,c,d 16 s (a 139, b 9, c 3, d 6, as in phase 3);
  - settle 80 s (tick COMPLETED); collect 79 s (56 requests, all 200, read-only transaction, `--work` the scratch `polish_work`);
  - check against `expected-today.json`; dropped (0 clones remain; settle's 2 `var/` files deleted).
- **Coherence check: 26 pass, 2 fail, 7 resolved.**
  - COH-10 0 and COH-11 0 (were 7 and 2); COH-7a 0 new.
  - The 2 fails are the known COH-5 Kobo 17/24 Oct COST lens; main A2 has the same 2.
  - Resolved: the phase-3 5, plus the expected `COH-7a KOBO-001 week/month window` entries, which no longer occur. `expected-today.json` is left unchanged, because MD-0 also edits these files.
- **B3 → R2 diff.** 15 requests, 31 paths: 25 restored `thread` objects (EV 27 Oct board ×2; Cold summary boards S/week/month ×3 each; EV summary week/month ×2 each; Portfolio S ×2, week ×4, month ×4) and 6 wall-clock action-index `known_at`. Nothing else changed.
- **Tests and proofs.** Each new test failed when its change was reverted, then passed when restored:
  - L0 `test_ch5a1_r1_visibility.py` (5): the board and the Portfolio pass the story cutoff as the visibility bound → 5 failed;
  - L2 `test_ch5a1_reader_postgres.py` L5: `LOOKUP` back on `:k` → `(2, 3, 2) != (2, 3, 3)`;
  - coherence COH-7a fixture (4): mini rule removed → 2 failed;
  - L1 `test_ch5a1_summary_ledger.py`: Site prefix removed → `3 == 1`; memo removed → `2 == 1`.

## Checks
R2 (code at e542064b2, `tools\run-host-tests.ps1`, `assetops_test` on 127.0.0.1):
- 18 scoped files in one run: 348 passed, 0 failed, 0 skipped (69 s). The files: `test_ch5a1_{r1_visibility,summary_ledger,reader,scope,board_contract,reader_postgres}`, `test_ch2_threads`, `test_ch3_{rows,lifecycle,lifecycle_postgres}`, `test_ch4_opportunities`, `test_out_{b2_mini,b3_cold_ev,b4_route,c2_board}`, `test_qw1_perf`, `test_w303_portfolio_api`, `tools/checks/test_chain_coherence.py`.
- `test_out_b4_board_postgres`, `test_w301_estate_api`, `test_idx_gaps_postgres`, `test_out_c3_repeat_visits_postgres`: 24 passed (227 s).
- `check-architecture.ps1` passed; `check-agent-workflow.ps1` passed.

Phase 3 (revision 33f06bcba, each file alone):
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
- R2: `visible_at` defaults to None (live) at both thread ports. A future caller that passes only `known_at` sees every occurrence, by design (R-1). The ledger keys of composer reads now start with the Site code; the QW-1 `timings`/`perf` names are unchanged.

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
1. **MD-0 not merged.** Pending on it: L2m/L3m (MD-0's L3m rerun after this merge must show COH-7a 0), the A-side rerun at the MD-0 merge, D-2d-1, and the P8 full-outbox measurement. `tools/checks/chain_coherence.py` conflicts with MD-0's branch; the second merge keeps `_coh7a_window` and its call.
2. **Full real-Postgres backend suite** (with the JUnit zero-skip check) on the final revision after 1.
3. R-1, COH-7a, the extra E1 entry and the ledger are closed by CH5a1-R2. Performance stays a finding (R2-P1, R2-P2); the plan change is the owner's.

## User-review focus
- R-1's two time axes (transaction `visible_at` and the story-time state cutoff) at the three ports.
- Whether the E2 Kobo change (settled rows instead of `PRODUCER_NOT_SETTLED`) and the summary card's local-day move read correctly.
- The performance gap against the budgets.
