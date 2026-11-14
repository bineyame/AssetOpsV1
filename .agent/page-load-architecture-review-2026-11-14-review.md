# Review: Page-Load Architecture Review (2026-11-14)

Reviewed: `.agent/page-load-architecture-review-2026-11-14.html` (Architect, commit bc8fe7077), against main at bc8fe7077 and the live walk serve (`AssetOpsV1-walk`, walk tree at f679402c9, PID 3662583 on :8990, DB `assetops_polish_walk1113_test`).
Reviewer: fresh Claude reviewer. Nothing was changed. The only live actions were read-only SQL (`default_transaction_read_only=on`), `pg_stat_activity`, and one GET on an already-stored board (a hit, 0.083 s).

## Verdict: REVISE (targeted)

The diagnosis is accurate and well evidenced. The direction (option C: facts built on arrival plus a thin version cache) is the right one, and it matches AG-20/§11b and the owner's 2026-11-03 words. Two parts need revising before the owner decides:

1. **C0 is not safe as specified**, and D2's line "either choice is safe" is unsupported (H1, H2, M1, M2).
2. **Option C drops one guarantee and underplays two gaps**: automatic invalidation on code change (H3), cold-chain and EV coverage (M5), and reconciliation with the BL-66/ANY plan that is already partly built (M4).

The rest can be fixed as notes.

## Checks run and what they returned

| Claim in the document | Checked | Result |
|---|---|---|
| `_WATERMARK` count at `postgres_response_store.py:41-42` | read the file | Exact match |
| Watermark cost 158 ms (Kobo) | EXPLAIN ANALYZE, read-only | 125 ms now, using a parallel index-only scan. Same order of magnitude. |
| 1.56 M change rows; 1.04 M for Kobo | count(*) | 1,564,835 in total; KOBO 1,042,953; KISIWA 485,818 |
| Top change tables (mini_depth_revision_evidence 474 k, and so on) | group by | Exact match |
| chain_response 519 MB | pg_total_relation_size | 539 MB and 8,694 rows. It is still growing. |
| site_day_snapshot 867 rows; site_period_read 8 kinds, 121-127 rows each | count | Exact match |
| "80 input tables" with triggers | information_schema.triggers | 84 tables now. 0047 lists about 80; later migrations added more. |
| 0047 change log at lines 29-50, 61-70 and 110-128 | read | Accurate |
| No route passes `if_none_match`; `If-None-Match: *` returns 200 | grep of every `responses.serve(` caller, plus a live GET | Confirmed. 200 in 0.083 s. |
| demo_combined `:63` TICK, `:124` warm_due, `:1357` performance_and_prebuild, `:1796` single uvicorn | read | All exact |
| `chain/prebuild.py:49-121` runs over HTTP | read | `run` is at 49-117. Accurate. |
| `tools/warm_ranges.py:468-484` | read | This is `run()` with 4 threads. Accurate. |
| `site_outcomes/read.py:438` compose; `:693-697` summary rebuilds each board | read | Accurate: `self.board(...)` is called once per Site inside the summary |
| `mini.py:507`, `estate/index.py:301`, `estate/coverage.py:102-119/301-313`, `estate/evidence_money.py:476`, `dispatch_day_rows.py:174-197` | read | Accurate |
| `period_read.py` gives PENDING-at-k from outbox/consumption; an older builder version reads PENDING | read the docstring | Accurate |
| Event register exists | `config/chain/event-register-v1.yaml` | Exists. Every period kind is **MINIGRID only** (lines 40-52). See M5. |
| Parity harness: 6 kinds, 42 pass, 0 fail | `parity-6kinds-final.json` | cases 42, pass 42, mismatch 0 |
| 0043 columns (subject_kind, evidence_class, coverage seconds, grade, value, money) | read 0043:29-56 | Accurate |
| tools/ is not in `code_version` | `file_code_version.py:47-53` | Confirmed. Only backend, migrations, config, host and contracts are hashed. |
| AG-20 (line 199), §11b budgets (about 2415-2427), scale path | `Docs/demo-sprint/implementation-logic-design-proposal.html` | Accurate. The brief pointed to AG-20/§11b in `production-shaped-mvp-technical-design.md`, but that file contains neither. The document cites the correct file. |
| prebuilt routes 167; warm 47 ranges, 1,672 requests | walk work folder | Exact match. The latest warm is all hits, 110.7 s wall. |
| max_connections 300; about 85 in use | pg_stat_activity | 300; 90 idle on the walk DB, all from the one API process (backend_start from 07:48) |

About 25 file:line claims were checked. Apart from L1 below, none is wrong.

## Findings

### High

**H1. C0 roughly triples the API connection footprint, and the range crawl then stalls.**
- Evidence:
  - The serve builds about 35 SQLAlchemy engines per process. All but one use the default pool (5 plus 10 overflow); the exception is the response store at `pool_size=2, max_overflow=2` (`chain/adapters/postgres_response_store.py:96`).
  - Measured now: **90 idle connections** on the walk DB from the single uvicorn process.
  - C0 runs three API processes: two user workers plus a crawl process that touches every route, so it warms every pool. That is about 270 idle connections against `max_connections=300`, which was raised to 300 because of D-E5.47 (`.agent/vps-migration-plan.md:22`). The tick and Performance children, test lanes and the other DBs on this cluster come on top of that.
  - `warm_ranges.throttle` waits **without limit** while `pg_stat_activity` is above 150 (`tools/warm_ranges.py` throttle, `--max-connections` default 150). Under C0 the crawl will very likely never finish. Hitting the 300 ceiling would turn user requests into INFRA-1 `stale` or 503 responses.
- Why it matters: D2 tells the owner that "either choice is safe". On the measured numbers, it is not.
- Fix:
  - Drop the second user worker from C0, or cap the pools per process (for example `ASSETOPS_POOL_SIZE`, which does not exist today and would be code in backend, so it would change `code_version`).
  - Re-base the warm throttle on this DB's own connections, or give it a ceiling.
  - Add a measured connection budget to C0, and test C0 on a scratch copy before restarting the walk serve.

**H2. Two uvicorn workers break process-local state that the walk serve uses.**
- Evidence:
  - `HostLabExecution._sessions` is an in-memory dict (`host/lab_execution.py:2116`). Status reads it at 2199-2211, and a run with no live session in this process reads `INTERRUPTED`. `_require_session` refuses `INTERRUPTED` (3285-3293).
  - The walk tree has `simulator_lab.enabled: true` (`var/polish_walk1113/tree/config/app-config.json`).
  - With two workers, a Lab run started on worker 1 shows INTERRUPTED, and its controls refuse, whenever the next request lands on worker 2.
  - The file-backed stores serialise writes only with `threading.Lock`, which is per process: `runs/adapters/json_commit_store.py:42`, `yaml_run_store.py:110`, `evidence/adapters/json_evidence_store.py:90`, `analytics/adapters/json_assessment_store.py:42` and `sites/adapters/yaml_user_site_store.py:73`. Concurrent writes from two workers are not serialised.
  - Checked and safe across workers: `read_scope` memos (per request), the `lru_cache` config loaders, `code_version` (the same tree in each worker), the response-store insert and its ON CONFLICT handling, and the prune, which runs only in the prebuild.
- Why it matters: the brief asked about process-local state, and the document does not examine it.
- Fix: keep one user worker before the walkthrough. Before any multi-worker stage (C5, S1), list the process-local state and move Lab sessions out of process, or route Lab requests to a single process.

**H3. Option C swaps automatic invalidation on code change for builder versions bumped by hand.**
- Evidence:
  - Today `code_version` hashes every backend, config, host and contracts file (`file_code_version.py:47-53`). Any code change therefore invalidates every stored body: this is safe by construction.
  - In C, facts are invalidated only by `builder_version`, which is a hand-maintained constant: `chain/dispatch_day_rows.py:40`, `mini_depth/period_rows.py:33` and `estate/period_rows.py:48`.
  - The table says "After a code change: Nothing, unless a builder changed". In practice "changed" means "someone remembered to bump the string". A pure function edited without a bump serves stale facts under a fresh version cache. Today the page store cannot do that.
  - The parity harness rebuilds rows to compare them, so it does not detect stale rows already sitting in a deployed DB.
- Fix: derive `builder_version` from a hash of the builder's source closure, or add a guard that fails when a builder module's source changes without a version change. State this in §6 as a guarantee.

### Medium

**M1. The idle-prebuild skip in C0 is underspecified and has side effects.**
- Evidence:
  - The prebuild does more than react to W. It re-warms live rows whose `valid_until` passed at the local midnight (`chain/prebuild.py:7-9`, `response_store.py:27-29`).
  - It also follows the F file term, the schedule term `|s:` (`response_store.py:117-119, 148-152`), and the route list that `write_prebuilt_routes` regrows with the calendar (`demo_combined.py:1371`). It runs the prune (`prebuild.py:111`).
  - A skip keyed only on "no Site's W moved" misses all of these.
  - If the skip leaves `last_prebuild_states` at None, `warm_due` returns True on **every** tick (`demo_combined.py:124-129`), so the 1,672-request crawl runs back to back.
  - The saving is small: a prebuild of all hits took 10-17 s in today's logs.
- Fix: remove the skip from C0, or key it on (W, F and the schedule terms for every Site, the route-file hash, the earliest `valid_until`) and report the hit states instead of None.

**M2. C0's benefit is overstated, and its version check is aimed at the wrong process.**
- Evidence:
  - At 21:37 the slow hits were `store.lookup` 3.6 s (WALK-perf ruling, line 11). That is the count(*) under database load. Moving the crawl into its own process removes contention for Python's interpreter lock (the GIL) and the event loop. It does not remove Postgres contention from crawl composes, or from the parallel count scans, which run in a different process but on the same 8 cores. So "removes the slow-while-crawling case" should read "reduces it".
  - "Check that the code_version is unchanged" is not enough. The crawl process must have the **same** `code_version` as the user process, which depends on the cursor keys and manifests in its environment (`watermark.py:31-43`). The prebuild prints its own child's version, not either API's (`prebuild.py:51`).
- Fix: verify with `warm_ranges --verify` against the **user** port after the restart. Every answer must be a `hit`.

**M3. The per-Site counter row adds lock contention and deadlock risk that the document does not mention.**
- Evidence:
  - "Incremented by the existing 0047 triggers… the row lock gives commit order" is correct for ordering. It also means every writer transaction holds the (tenant, Site) row lock until it commits.
  - Long builder or backfill transactions would block user writes to that Site, such as operational entry and uploads.
  - A statement that touches several Sites in different orders can deadlock.
  - NULL-Site and TRUNCATE rows (`0047:9-11, 118-119`) become one tenant-wide hot row that every Site-less write locks.
- Fix:
  - Specify the lock order: sorted Sites, then the tenant row last.
  - Keep builder transactions short, or batch by Site.
  - Measure contention in C1's evidence.
  - Alternatively, compare against a design that keeps the change log for ordering and bumps the version through a single committer.

**M4. The document is not reconciled with BL-66 and ANY-1/ANY-2.**
- Evidence:
  - BL-66 (`backlog-post-demo.md:85`) planned 8.5 units: AR-0 to AR-7 plus MN-1 to MN-3, targeting a board and Portfolio of 2 s or less with no pre-loading.
  - AR-1, AR-2, AR-3 and part of AR-4 are built. The board fell from 11 s to 2.7 s; the Portfolio is still 12-24 s.
  - The document proposes about 9 more units for a tighter budget (0.5/0.8 s) without explaining why the built rows missed the 2 s target. One known cause: the AR-4 evidence gave only −2 to −4 s, because of a second compose in `evidence_money.site_data_gap_days_many` (coordinator-handoff).
  - It does not map C1-C5 to the open cards (AR-4 remainder, AR-5, AR-7 `outcome.site_row`, MN-2/3).
  - C2 is sized at 2.5 units, but ANY-2's earlier estimate was 5.5. The 0.3-0.8 s "expected result" in the plain-words summary has no prototype measurement behind it.
- Fix:
  - Add a table mapping each BL-66 card to done, subsumed, or carried into C1-C5.
  - Add a short post-mortem on why the built rows have not delivered.
  - Re-size C2, or justify 2.5 units.
  - Mark the 0.5 s figure as a target until it is measured.

**M5. Cold-chain and EV Sites are not in the C plan.**
- Evidence:
  - Every period kind in the register is `site_types: [MINIGRID]` (`event-register-v1.yaml:40-52`).
  - §6 claims "one range aggregator over one fact shape for mini-grid, cold room, EV and diesel", but C2 and C3 list no cold or EV fact kinds and size none.
  - The owner rule (range output the same for every Site type) makes them required.
- Fix: list cold and EV kinds (board, range overview, Findings by day) in C3 or a separate stage, and add them to the effort.

**M6. "Reuses everything" is overstated, and the PENDING exposure after a builder change is not costed.**
- Evidence:
  - Today's `site_period_read` bodies are "the exact fragment today's compose builds for the period" (`0059:7-8`, `period_read.py:3-5`). They are not additive parts.
  - C's rule ("facts store parts that add up; ratios are computed when the page is read") means re-shaping the existing kinds, not only adding new ones.
  - Under the existing rule, a builder bump makes **every historical period** of that kind read PENDING until the backfill finishes. The document gives no backfill time at demo or pilot scale, and no option to keep serving the previous builder's rows until the new rows are complete (a blue/green switch).
  - Today, after a code change, a page is slow but correct. Under C, history would read PENDING for the whole backfill: a regression users can see.
- Fix: estimate the backfill time per kind, and specify serving the previous builder version until the new one completes, or explain why not.

**M7. The decision text hides the risky parts of C0.**
- Evidence: the plain-words summary and D2 describe C0 as "crawlers in their own process; tools only". Neither mentions the second user worker or the prebuild skip, which are where H1, H2 and M1 sit.
- Fix: list all three C0 parts in D2, with the risks of each.

### Low

- **L1. Line references to `response_store.py` have drifted.** They are 6-12 lines off: `request_key` is at 82-88 (cited 76-83), `_state` at 137-153, `serve` at 162-222, `valid_until` at 266-280, and the 304 support at 162-163 and 194 (cited 160 and 186). The file has not changed since the document was written, so the drift is in the citations. "80 input tables" is now 84.
- **L2. The tick extrapolation ignores the Site cap.** "At 100 Sites a quiet tick takes about 22 min" ignores `--max-sites 5` (`demo_combined.py:78-79`). At 100 Sites, each Site is reached about every 20 ticks instead. The conclusion still holds, and staleness becomes the symptom.
- **L3. The repeat budgets disagree.** D3 says repeats ≤ 0.1 s, but the §7 table says ≤ 50 ms (304) for Site pages and ≤ 100 ms for Portfolio.
- **L4. D5 should say how the date bar's days map to each Site's days.** The presets are full **UTC** days (`warm_ranges.py:7-8`, `sharedRange.ts presetRange`). D5 should state how a from/to date maps to each Site's local days when the Portfolio spans time zones, and what the owner will see at the edges.
- **L5. D6 depends on the other Architect.** It assumes agreement from the conversion-potential Architect. The fit is good: conversion §10 and §13 propose a billing store with a `collected_amount` measure and "beside, never added" money, which matches §9's per-Site-day aggregates per tariff class with ledgers kept in import tables. D6 should be framed as a joint confirmation after that Architect agrees.
- **L6. "Either choice is safe" (D2) should be removed** until H1, H2 and M1 are resolved.

## Root causes R1-R6

Root causes R1-R6 are structural and correct. One amplifier is missing from R2: bookkeeping tables (`recompute_job`, `event_outbox`, `event_consumption`, `analytic_run_evidence`; together about 50% of the change rows) move W even when no business data changed. The document hints at this with "a quiet tick can still write". The fact-input guard in C should decide explicitly which of these bump the version. I found no stored-route races in today's log (0 `stored_route_race`), so race churn is not a missed cause.

## Is C0 safe before the walkthrough?

**Not as specified.** The two-worker part breaks Lab sessions (H2) and pushes the connection count toward the 300 limit, which stalls the warm crawl (H1). The prebuild skip can leave pages expired after midnight and make the crawl run back to back (M1).

A reduced C0 is lower risk: one user worker, no prebuild skip, the crawl in its own process with a connection check, and after the restart `warm_ranges --verify` on the user port showing 100% hits. Even so, it needs a scratch rehearsal first, and the benefit is partial (M2). With the walkthrough on a clean DB, the conservative choice is no change before the walkthrough.

## Residual risks the document does not name

- **Late data and the event worker.** If the worker dies, periods read PENDING indefinitely. That is honest, but the S0 stage has no alarm; the dirty-queue age alarm appears only at S1. Add a basic stall alarm at S0.
- **The read itself may grow with history.** PeriodReader's PENDING-at-k is an anti-join over the append-only outbox and consumption ledgers (150 k outbox rows today). Its cost could grow with history the way R3 did. Add it to the C1-C3 measurements.
- **chain_response grows without limit.** It is 539 MB, and rows of dead code versions are cleared only by reset or prepare. This matters for C's thin cache if code versions churn.
