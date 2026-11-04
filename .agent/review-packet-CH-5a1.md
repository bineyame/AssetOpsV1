# Review packet: CH-5a1 (ChainReader and the board read path)

Branch `task/CH-5a1-chain-reader`. **CH5a1-R2 fix round** (sheet §A13) on 110d0057a: ff033ade1 (R-1), d088b16f1 (COH-7a), e542064b2 (ledger), packet f6dfc60e4. **MD-0 round** (sheet §A13 / MD-0 §7, §16-§18): e40018c53 (merge main c036f8a49), c9638be3f (D-2d-1), 99e956dec (L2m), 33841fd57 (e4 importer); this packet commit follows. Not merged.
Authority: build sheet Part A (`AssetOpsV1-plan2/.agent/build-sheet-CH-5a.md`, incl. §A12 CH5a1-R and §A13 CH5a1-R2). Evidence: `.agent/CH-5a1-phase-{1,2,2b,2c,2d}-handoff.md`, `.agent/CH-5a1-phase-3-results.md`, and the R2 section below.
**Status: ready for review**, with three Architect items from the MD-0 round (MD-0 section: F1, COH-5 x6 on L3m, the template fingerprint). R-1, COH-7a, the extra E1 entry and the ledger are applied. USER_REVIEW: the build sheet sets no USER_REVIEW_REQUIRED flag; the coordinator decides.

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
| A0 same on MD-0 (L3m) | met-with-finding | MD-0 A2 vs B: 17/40 requests, 664 paths, all E1/E2/E4 (+ E2-derived); COH-5 x6 new on B (MD-0 section, item M3) |
| A0 measured timings reported | met | perf table below |
| A0 boundary: no detector/matcher/money/verification/lifecycle/copy change | met-with-deviation | copy unchanged; `GAPS_WITHHELD` deleted with its COPY entry (Q4, 2c); behaviour changes D-Q2/Q8/R8 below |
| A6 A/B on L3 clone, both sides on B's `days.json` | met | 56 requests per side, A = main a07452c63 |
| A6 E1 readiness | met | matches pre-flight §4, plus the accepted extra entry (§A13): summary month Kobo, local 3 Nov, Unknown → Low |
| A6 E2 / E3 / E4 / E5 | met | E5 met for every Site after R-1 (Cold/EV threads unchanged from A) |
| A6 E3b | met | empty; (finding_id, revision_id) sets equal on every day board and the Portfolio |
| A6 no other difference | met | R2 clone (below) |
| A6 A side at the MD-0 merge; L3m + `--variant close` | met (close: n/a) | A = main c036f8a49 on a fresh polish clone and on L3m; `--variant close` is MD-0b and refused by the tool |
| A7 probe, 5 cold/5 warm, bytes, top-10 ledger | met (clone and L3m) | `tools/chain_perf_probe.py`; L3m table in the MD-0 section |
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

## MD-0 round (main c036f8a49 merged; MD-0 §7, §16-§18)
- **Merge (e40018c53).**
  - `chain_coherence.py` auto-merged. `_coh7a_window` and its call are kept beside MD-0's in-process collect and `check --threads`.
  - `test_chain_coherence.py` conflicted. Both blocks are kept (95 passed).
  - `expected-today.json` drops the two `COH-7a KOBO-001` week/month entries that this slice resolves, per the file's rule ("later slices delete the entries they resolve"). Main did not edit this file.
- **D-2d-1 (c9638be3f).** `backend/tests/mechanism_dataset.py` `build_work` writes each Kobo entry from `local_instant(n, "00:00")` to `local_instant(n, "24:00")`.
  - Test: L0 `test_md0_fixture.py::test_build_work_writes_kobo_days_as_site_local_days`. It failed on the pre-change file, then passed (41 passed).
- **Template: stale, so rebuilt.**
  - `status` gave `usable: false` (b23a1ca0 vs ee2b4136).
  - The branch edits 15 files in the tag's traced module list: `mechanism_dataset.py`, `main.py`, `outcome_api.py`, `perf.py`, `estate/{index,portfolio}.py`, `estate/adapters/postgres_estate_read.py`, `analytics/finding_index.py`, `analytics/adapters/postgres_assessment_store.py` and `site_outcomes/{board,cold,composition,ev,mini,read}.py`.
  - Rebuilt with `build --variant states --budget 540` in two parts: 491 s (exit 3, resume), then 153 s. The new tag is 5e589e86, `usable: true`.
  - The shared template now carries this branch's fingerprint (item M4).
- **L3m.**
  - `derive` took 61 s (clone 1.1 s, derive 58.4 s).
  - An unticked collect gave 40 x 200 and 0 findings, but every Kobo row was UNKNOWN. I then settled the DB with `chain_clone.py settle mechanism` (tick COMPLETED, 30 s), the path MD-0 §6 provides.
  - Settled check, B (`check --threads var/mechanism/expected-threads.json --expect expected-mechanism.json`): **COH-7a 0** (MD-0's L3m had 2), COH-10/11 0, every other rule 0, and **6 new COH-5** (item M3).
  - Settled check, A (main on the same DB): COH-7a x2 (week and month), and nothing else.
- **E1 on MD-0** (chip `readings`, rows pooled per day):
  - Every delivered day, normal and overrun, reads High (FULL), on the board and in L2m.
  - **GAP-K7 (D7) reads Unknown, not the expected NONE** (item M1).
  - The summary month card (local 3 Nov, no rows) reads Low (NO_DATA), as on the polish clone.
  - MD-0 has 3 studies. The headroom opportunity OPP-000003 shows on the D13/D14 boards on both sides; its state_day moves to the local day (E4).
- **L2m (99e956dec)**, `test_ch5a1_mechanism_postgres.py`: a template clone plus derive (`test_md0_mechanism_postgres.mech`), then `_settle_chain`.
  - Asserted: R8 settled; `readiness_of` FULL on every delivered day (hard); the thread occurrences carry exactly the manifest's Findings.
  - D7 UNKNOWN is recorded as `xfail("MD-0-F1 ...")` after the hard assertions (MD-0 R7 pattern).
  - Result: 1 xfailed, 61 s.
  - Proof: changing `readiness_of` FULL → LIMITED fails the hard assertion (`{1: 'LIMITED', ...} != {}`); restored.
- **A/B on L3m.** A2 = main c036f8a49. Both sides used B's collector and `days.json`, in read-only transactions. 17 of 40 requests differ, 664 paths.
  - Differing: Kobo day boards 11/11, summary-linked boards 3/3, summaries 3/3. Findings index, Portfolio and actions: 0.
  - E2: A reads `PRODUCER_NOT_SETTLED` everywhere. B shows settled rows, the objective verdicts MET/MISSED/NOT_JUDGED/TOO_EARLY, and the D4/D11/D14 dispatch Findings on the board (thread occurrence 3 on D14, CHANGE_APPLIED).
  - E2-derived:
    - ACT-001 "in hand" moves from PROTECT_ASSET to OPTIMIZE_COST, because its origin Finding is now on the board (`board.py:736-737`; the fallback is PROTECT_ASSET);
    - the "Battery stayed clear of its reserve ..." headlines;
    - `earlier_empty_text`.
  - E1: chips read High.
  - E4: local windows, state_day +1, and the Grain mill kWh is summed over the local day (238 ↔ 240).
- **A/B on a fresh polish clone** (`assetops_chainclone_ch5a1r3_test`; create 3 s, backfill a-d 12 s, settle 59 s, collect B 64 s and A 93 s; then dropped). 18 of 56 requests differ, 676 paths. Every difference is E1, E2 or E4.
  - Kobo day boards: 8/8.
  - EV boards: 2/2 (E1: Limited → Low; `EVIDENCE_READINESS_LIMITED` → `_NONE`).
  - Kobo/EV summary-linked boards: 5/9. Summaries: 3/3.
  - **No difference** on Cold, the Portfolio (0/3), the Findings index (0/19) or actions (0/9). R-1's Portfolio paths are gone against this main.
  - Coherence, B: 2 new (the known COH-5 Kobo 17/24 Oct COST lens), 7 resolved.
  - Coherence, A (main): 3 new COH-7a (Kobo S/week/month on UTC windows), judged by this branch's rule and the trimmed `expected-today.json`.
- **Perf on L3m** (probe, 5 cold / 5 warm, ms):

| URL | cold med | warm med | bytes | max_per_key |
|---|---|---|---|---|
| Kobo board 31 Oct | 3,914 | 2,903 | 10,780 | 1 |
| summary, week | 4,234 | 2,917 | 2,728 | 1 |
| Portfolio, week | 3,919 | 3,607 | 20,908 | 1 |

  - Kobo D13 warm ledger (§A3 ports, ms): `assessment._window` 1,025, `mini_depth` 896, `estate` 673, `dispatch` 576, `productive_readings` 229, `source` 81, `chain_findings` 61, `work_index` 54, `action_facts` 17, `productive_price` 15.
  - Summary: `chain.money_head` 848. Portfolio: `_window` 2,074, `claim_limit_snapshot_on` 912.
  - On normal data the payloads meet the 60 KB and 100 KB budgets. The time budgets are missed, as on the clone; none is relaxed.
- **P8** (L3m, settled).
  - Rows: `event_outbox` 33,815 (Kobo: 32,550 `reading.accepted`, 8 `finding.revised`, 3 `opportunity.revised`); `event_consumption` 13 for `threads`.
  - The R8 statement takes 2-6 ms per call, with k None and with k = 31 Oct 21Z.
  - EXPLAIN (ANALYZE, BUFFERS):
    - Nested Loop Anti Join;
    - Index Scan on `event_outbox_site_type_order` (11 rows, or 7 with the k filter);
    - Index Only Scan on `event_consumption_pkey`;
    - 21 shared hits; execution 0.27 / 0.14 ms.
  - The cost scales with a Site's Finding events, not its readings. At this volume no commit-safe cursor is needed (CH1b-R2 item 2 stays with DD-1).

### Architect items from the MD-0 round
- **M1 (MD-0-F1, owner CH-5a1 R5): the cause is found; no code changed.**
  - Cause: D7-D9 each carry a live `mini_renewable` job for the noon hour. It was enqueued on 29 Oct at 11:00 (the D11 delivery) and never reconciled, because nothing was delivered on those days.
  - So `noon_headroom_kw` is PENDING there (`renewable_pending`, `postgres_chain_inputs.py:82-88`). D6, by contrast, is NO_DATA on every measure.
  - R5 as written ("any PENDING → UNKNOWN") therefore gives UNKNOWN.
  - Conflict: MD0-S4 R1.5 accepts "GAP-K7 stays NO_DATA/PENDING before the fill", but the E1 line expects "GAP-K7 reads NONE".
  - Changing R5 would change semantics, so I made no change.
  - Ruling needed, either:
    - accept UNKNOWN for GAP-K7 before the fill; or
    - have the MD-0 harness reconcile the queued noon jobs of undelivered days (MD-0b / DD-1).
- **M2: COH-7a on MD-0 is 0** (A has the 2), as §A13 requires. Nothing was added to `expected-mechanism.json`.
- **M3: COH-5 x6 on L3m B.**
  - What: the D4/D11/D14 dispatch Findings appear under OPTIMIZE_COST and PROTECT_ASSET, but their Findings index rows carry `lens_flags []`.
  - Main is the same: A's index rows for these Findings are also `[]`. B exposes the gap because the board now shows the settled Findings (E2).
  - It is the same class as the polish clone's Kobo COH-5 entries (owner CH-5a), and COH-5 = 0 on L3m is CH-5a2's acceptance (MD-0 §7: COH-1/5/8 = 0).
  - Not added to `expected-mechanism.json`: that file only shrinks, and these are neither GAP-K7 nor R4 facts.
  - Ruling needed: carry it to CH-5a2 as its L3m COH-5 target.
- **M4: the shared template fingerprint.**
  - The template now carries this branch's fingerprint, so `status` on main reads stale until CH-5a1 merges.
  - Ruling needed: rebuild on main after the CH-5a1 merge, or accept it as stale until then.

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
**Full real-Postgres backend suite (MD-0 round)**
- Command: `tools\run-backend-suite-in-container.ps1 -Tier all -Workers 2`, on 99e956dec, server `postgres-test`, cache on. Run `20261104-163109-be9c25`.
- Wall: 4,125 s (68.7 min). That exceeds the guide's 40 min estimate but is inside the runner's own cap. Memory at start: 4,738 MB free.
- JUnit: tests 5169, failures 8, errors 29, **skipped 0** (zero-skip check met).
- Every failure was rerun on **main c036f8a49**, in a detached worktree, with the same runner and `-Targets` (run `20261104-174416-fc7884`, 720 s): 7 failed, 30 passed, 28 errors.

| failing on the branch | on main | cause |
|---|---|---|
| `test_demo_combined_postgres` x25 (module set-up: `SystemExit: SELF-CHECK FAILED`) | same 25 errors | pre-existing |
| `test_md0_mechanism_postgres` x3, `test_ch5a1_mechanism_postgres` x1 (`TEMPLATE_MISSING`) | MD-0's 3: same | environment: the container's `postgres-test` server has no `assetops_mechanism_tpl_test`. The template lives on the dev server (55432), where L2m passes (1 xfailed). Not run on main: `test_ch5a1_mechanism_postgres` (new on this branch) |
| `test_w301_estate_golden_postgres` x6 (`$.opportunities: actual [] != expected '<absent>'`) | same 6 | pre-existing (main's `estate/index.py:346` emits `opportunities`; the goldens predate it) |
| `test_runs_api::...test_the_shipped_scenario_blocks_only_on_the_values_this_site_lacks` (`var/sites/mg-001.yaml` missing in the container copy) | same | pre-existing / environment |
| `test_out_e4_readback_postgres::test_kobo_verified_protect_entry_and_assure_read_back` (`ImportError: _assert_lineage_must_not_harm`) | **passes** | **branch-caused**: phase 2b deleted the lineage helpers, and this importer was missing from the 2b list. Fixed in 33841fd57 (settle the chain as b4 does, record Must-not-harm). Rerun in the container: 1 passed (run `20261104-175742-a48f88`) |

- After 33841fd57: `check-architecture.ps1` passed (132 s); `check-agent-workflow.ps1` passed. `tools/checks/test_chain_coherence.py` 95 passed; `test_md0_fixture.py` 41 passed. `test_ch5a1_mechanism_postgres.py` on the host (dev server): 1 xfailed (MD-0-F1).
- The full suite was not rerun after 33841fd57, which changes one test file only. The rerun covers that file.

## Importers (§A9 item 4)
These are the phase-2 handoff list, plus `test_out_b4_main_binding`, `test_ch2_threads` (2b), `test_idx_gaps_postgres`, `test_out_c3_repeat_visits_postgres`, `test_ch5a1_board_contract` (2c), `test_ch5a1_reader_postgres` and `tools/checks/test_chain_coherence.py` (2d).

## Production fixes found by tests
1. 2b: `ChainRequest.day` `m.measure` → `m.key`.
2. 2b: `mini.estate_bounds`, so the estate read keeps UTC-midnight bounds (`check_window`).
3. 2c: `SITE_TYPE_OF_DOMAIN["ev_charging"]` = `"EV_CHARGING"`.
4. 0c9cfe98e: the mini route accepts its own Site-local window.
5. 9cbe253c9: Portfolio rows emit `public_thread`.
6. c74ffbb22: the board money port binds `site_overview.read.consequences`.
7. 33841fd57 (test only): `test_out_e4_readback_postgres` still imported the deleted lineage helpers; found by the full suite.

## Known deviations
- **D-UTC:** the estate read stays on UTC-day bounds while the board day is local, until CH-5a2 B3.
- **Q2:** a dispatch refusal now unsettles every measured outcome (UNKNOWN).
- **Q8:** cold/EV readiness pools all intersected local days (32 for an unaligned 31-day window).
- **R8 alone:** Finding settledness no longer follows gap days; an unsettled chain shows no Findings.
- **D1:** `lead_finding` pinned rule uses `day.settled` as `discovery_complete`.
- **D2:** `priced` per §A3 only. D4: `covering_days` unused in production, kept for its tests.
- **D-2d-1:** closed by c9638be3f (Kobo `days.json` entries are Site-local days).
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
1. MD-0 is merged, and its L2m/L3m, A-side, D-2d-1 and P8 items are done (MD-0 section). Architect rulings are needed on M1 (GAP-K7 reads Unknown), M3 (COH-5 x6, to go to CH-5a2) and M4 (the template fingerprint).
2. The full real-Postgres backend suite ran on 99e956dec (Checks). Every remaining failure also fails on main, or comes from the environment. The one branch-caused failure is fixed (33841fd57).
3. Performance stays a finding (R2-P1, R2-P2 and the L3m table). The plan change is the owner's decision.

## User-review focus
- R-1's two time axes (transaction `visible_at` and the story-time state cutoff) at the three ports.
- Whether the E2 Kobo change (settled rows instead of `PRODUCER_NOT_SETTLED`) and the summary card's local-day move read correctly.
- The performance gap against the budgets.
