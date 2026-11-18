> Finished; historical. Archived from .agent/page-load-architecture-review-2026-11-14-review.md on 2026-11-18 (declutter step 4).
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

---

## Re-review (rev 2)

Reviewed: revision 2 at 16eb2b860 (diff bc8fe7077..16eb2b860 on the HTML), against main at 16eb2b860. Fresh Claude reviewer. Nothing was changed; no DB or serve was touched (code and git reads only, so the live re-measurements in the first review were not repeated).

### Verdict: REVISE (targeted, text-only)

Every first-round finding is handled in the body, not only in the changelog. The "no change before the walkthrough" call, the dropped worker and skip, the §4b card map, C3b and the re-costing are all sound. Two claims are still wrong, though: the new H3 guarantee ("with no human step") does not hold for the builders as they are wired today, and §4b's main post-mortem cause was already fixed on main. Both are text fixes in §4b, §5, §6 and §8. **D1-D6 can go to the owner now**: none of them depends on these fixes. The fixes must land before C1b and C2 are planned.

### First-round findings: resolved in the body?

| Finding | Where in rev 2 | Status |
|---|---|---|
| H1 connections | §5 "connection budget"; §8 C0 table; R0 gate (<200) | Resolved. "Pool sizes are not configurable" is confirmed (no pool env in backend). See N4 on the rehearsal itself. |
| H2 workers vs process-local state | §5; §8 (worker dropped until C5); C5 scope | Resolved. The `lab_execution.py:2116` and five store citations are accurate. |
| H3 hand-bumped builder_version | §5 "Invalidation that cannot be forgotten", §6, C1b | Addressed, but the new design is unsound as specified (N1) |
| M1 prebuild skip | §8 table: dropped | Resolved |
| M2 benefit, code_version | §8 C0 table; R0 gate verifies on the user port | Resolved |
| M3 counter contention | §5 "One version per (tenant, Site)"; C1 exit | Addressed. The lock order and fallback have gaps (N3). |
| M4 BL-66 | §4b, card table, "Why C2 is 4.0" | The map is good, but one cause is stale (N2) |
| M5 cold and EV | §5 rule; C3b at 2.0 u | Resolved. There is an ordering gap with C2 (N5). |
| M6 additive reshape, PENDING | §3, §5 rule 2, blue/green, backfill estimate | Addressed. The blue/green mechanics are incomplete (N1b). |
| M7 / L6 decision text | D2 rewritten, "either choice is safe" removed | Resolved |
| L1-L5 | Line refs refreshed (they match my reads: serve 162-222, `_state` 137-153, `valid_until` 266-280); 84 tables; --max-sites (`demo_combined.py:79`); budgets consistent between §7 and D3; D5 and D6 reframed | Resolved. Nit: R5 and §7 still say "85 connections in use" where §5 says about 90. |
| Residual risks | §5 operational alarms: stall alarm at S0, the PENDING anti-join timed, a dead-version prune | Resolved |

### Re-costing check

C1 1.25 + C1b 0.75 + C2 4.0 + C3 2.5 + C3b 2.0 + C4 1.0 + C5 2.0 = 13.5, and C1-C4 = 11.5 as D4 says. The arithmetic is consistent. The C2 rationale against ANY-2's 5.5 is reasonable. C1b at 0.75 is probably low once N1 and N1b are specified, because it then needs a composition-root closure, an active-version pointer, per-period fallback and a cache bump on switch. Budget about 1.25 u, or say it is a floor.

### Remaining findings

#### High

**N1. The builder hash is not "unforgettable" as defined, because the builders' real computation is injected and is not in their import closure.**
- §5 defines the closure as "its module, the pure functions it imports from the project, and its config". All three existing builders receive their compute by dependency injection at the composition root:
  - `DispatchDayKindBuilder(day_now)` gets `store.dispatch_day_now`, a method of `PostgresAssessmentStore` (`analytics/adapters/postgres_assessment_store.py:1054`, wired in `chain/composition.py` `dispatch_day_builders`). `dispatch_day_rows.py` never imports that adapter.
  - `EvidenceClaimKindBuilder(estate_read)` reaches `snap._o.claim_limits.store.claim_limit_snapshot_on` and `provenance_reads(...)` through attributes (`estate/period_rows.py:195-235`), not imports.
  - `MiniDepthKindBuilder(d, mini)` takes an injected `mini` service (`mini_depth/period_rows.py:192-197`).
- A SQL or logic change in those adapters would therefore leave the hash unchanged and serve stale facts: exactly the H3 hazard.
- Further failure modes the definition misses:
  - **Dynamic imports.** `chain/adapters/file_chain_config.py:127-129` and `chain/adapters/file_inputs.py:31` use `importlib`.
  - **SQL in migrations.** The `chain_action` view (`0042:112`, `0051:53,100`) is read through SQL whose definition lives in a migration. The closure needs the alembic head, as `code_version` does.
  - **Env-named manifests and config.** `COMPOSER_ENV` and `MANIFEST_ENV` are hashed into `code_version` (`file_code_version.py:36-44`) but are not named in the closure.
  - **Shared versions.** `mini_depth` shares one version across six kinds (`period_rows.py:32-33`, because the provenance blocks share it), so "blue/green per kind" and "hash per builder" must state which unit they use.
  - **Opt-out.** "A guard fails if a hand-written label exists without the hash" does not stop a new builder that sets no label, or one that computes its own.
- Fix:
  - Compute the version in the framework, not in the builder. `PeriodReadBuilder` derives it at registration from the builder class's module and the classes of every injected dependency (`type(dep).__module__`), each with its transitive project imports, plus the alembic head, the config files and the composer env and manifests. Builders cannot set it themselves.
  - The guard asserts that every registered kind's version equals that computed hash.
  - The C1b exit test must also edit an **injected adapter's SQL** and a migration view, not only "a helper a builder imports".
  - Add a deploy-time drift sampler as a backstop: rebuild a random sample of periods per kind with the current code, and compare the input and body fingerprints (`period_fp`) with the stored latest rows. A mismatch under an unchanged version fails the deploy.
  - State the trade-off. A conservative closure (for example all of `backend` except the presenters) is safe but bumps most kinds on most deploys. At pilot scale that means about 20 CPU-hours per kind per deploy (§5's own estimate). Precision matters for cost, not only for correctness.
  - Until this is fixed, §6's "Same as today" for automatic invalidation overstates the guarantee.

#### Medium

**N1b. The blue/green switch is underspecified, and the gaps are visible to users.**
- `site_period_read` revisions are per (Site, kind, period), with `latest + 1` across builder versions (`period_read.py` builder rules). The reader treats any older version as PENDING (`period_read.py:407-409, 432`).
- Serving "the previous version's rows" therefore needs an active-version pointer and a reader that selects the latest revision **of the active version**. Neither exists, and §5 does not name them.
- During the backfill only the new code is deployed, so a period whose inputs change can be rebuilt only under the new version. Under the rule as written ("switch only when the new set covers every period the old one did"), today's and other freshly dirty periods read PENDING for the whole backfill: about 2.5 h at pilot, on the most-viewed days. Allowing per-period fallback instead sums parts built by two builder semantics inside one range.
- The switch is a runtime event, not a code change. Unless it bumps every affected Site's `site_read_version` (or the active versions join the cache key), cached bodies keep the old rows after the switch.
- Serving old-version rows also means serving values from known-superseded logic, which is wrong when the builder change was a bug fix. That is a policy choice the owner should see.
- Fix: specify the active-version pointer and the reader query; rebuild newest periods first, and state the fresh-period rule (PENDING or per-period fallback, and whether mixed versions may be summed); bump the versions on switch; and add a "bug-fix bump: PENDING instead of old rows" option per kind.

**N2. §4b's second cause is stale: the second compose was removed on main on 12 Nov.**
- `evidence_money.site_data_gap_days_many` (`:589`) calls `coverage.dispatch_days`, which reads stored rows when served (`estate/coverage.py:65-75`), since 182220d4e ("AR-4: _data_gaps reads coverage.dispatch_days"). That commit is on main and in the walk tree (f679402c9).
- DISP-1 then moved `money_eligibility.for_finding_on` (coordinator-handoff "MERGED DISP-1": week 10.9 → 8.6 s).
- The cited handoff lines (`:109`, `:132`) are the 06:45 entries from before the fix. The 12-24 s Portfolio composes in §1 were measured on a tree that already has the fix, so they are not explained by it. The remaining time is `portfolio.evidence` at 10.2 s, which the document does not attribute.
- C2's item "remove the second compose in site_data_gap_days_many" is work that is already done, and C2's 4.0 u counts it.
- Fix: replace the cause with an attribution of the measured 10.2 s `portfolio.evidence`, 6.3 s `portfolio.money` and 4.9 s `portfolio.findings` (for example, whether `dispatch.day` is in the served kinds on the walk serve: `ASSETOPS_PERIOD_READ_KINDS` in §1 lists it, so those timers are not dispatch). Drop the item from C2, or re-justify the size.

**N3. The per-Site counter's lock order and fallback are incomplete.**
- **Lock order holds only inside one statement.** The 0047 triggers are statement-level with transition tables (`0047:6-8, 116-125`), so one trigger can lock its Sites in sorted order. A transaction that writes Site B in one statement and Site A in a later one, or a Site-less (tenant-row) statement before a Site statement, still takes the locks in application order. "Then the tenant row last" cannot be enforced by a trigger. Deadlocks between, for example, an import and the tick remain possible. Postgres resolves them by aborting one transaction, which may be a user's upload.
- **The tenant row is a hot row.** Every Site-less write locks it until commit. That is the over-invalidation 0047 already chose, now with a lock as well. It is not discussed.
- **The single-committer fallback has R3's hazard.** It advances the version "from the change log as a high-water mark". `change_id` is assigned at insert, not commit (R3), so the committer needs a visibility rule, for example only rows whose xid is below `pg_snapshot_xmin(pg_current_snapshot())`, or the existing count. As written it reintroduces the `max(id)` race the document rejects.
- **Bookkeeping tables versus the guard.** "Bookkeeping tables (outbox, consumption…) stop bumping it", but the reader's PENDING-at-k reads the outbox and consumption ledgers on the serve path (`period_read.py` docstring). §6's guard says every serve-path table bumps the version. Stopping the bump is safe only after PENDING moves into fact rows written in the input transaction. Say that as the precondition, not "once the facts carry their own PENDING state".
- Fix:
  - State that the ordering covers one statement, and require writers that touch several Sites to go through one ordered call, or accept deadlock retries and test them in C1.
  - Name the tenant hot row as a measured C1 item.
  - Give the fallback its commit-visibility rule.
  - Make the bookkeeping change conditional, as above.

**N4. The R0 rehearsal gate is not sufficient as written.**
- **Shared cluster.** The rehearsal runs a scratch copy on the same Postgres cluster as the walk and demo serve. Two API processes at about 90 connections each, plus the walk serve's 90, approach the 300 cluster limit, so the rehearsal can harm the live serve. The "<200" pass condition is `pg_stat_activity` cluster-wide (`warm_ranges.py:542-545`), so it depends on whatever else runs at the time.
- **A miss can mask itself.** `--verify` stores on a miss in the user process, so only the **first** verify after the crawl is evidence. A second verify passes even when the code versions differed.
- **The benefit is not measured.** Nothing in the gate shows user latency during a crawl improving (for example, Overview hit p95 during a crawl versus the 5.7 s baseline). Without that, R0 carries risk for an unmeasured gain.
- **No rollback or after-midnight check.** The gate has no rollback step, and no check after the local-midnight re-warm. Variant 1 also changes backend code, so it needs its own review and a full re-warm (11 min plus about 1 h) on the demo DB before 17 Nov. The gate does not budget that window.
- Fix:
  - Rehearse only when the walk serve is idle, or cap both rehearsal processes so the cluster stays under 200 in total.
  - Gate on the first `--verify`.
  - Add a user-latency-during-crawl measurement with a pass threshold.
  - Add a rollback step and a midnight check.
  - For variant 1, require a review and a timed re-warm window.
  - Otherwise default D2 to "nothing until after the demo", which is the Architect's own recommendation.

**N5. C2's exit evidence depends on C3b, but they are sequenced in parallel.**
- The outcome summary and Portfolio include EV and COLD Sites (§1: summary timers for EV 2.6 s and COLD 0.8 s).
- AR-7's `outcome.site_row` for those Sites needs their kinds. `evidence.claim` returns nothing for non-MINIGRID Sites (`estate/period_rows.py:211-212`), and `evidence.provenance` is declared there as the cold/EV pinned-window kind.
- C2's exit ("no compose timer on the Portfolio") cannot hold for cold and EV until C3b lands, yet C3b "follows in whichever lane frees first".
- Fix: either C2 builds the cold and EV `site_row` and provenance inputs, or C2's exit is scoped to mini-grid with C3b closing the Portfolio. State this so the owner's every-Site-type rule is not met silently for only some Site types.

#### Low

- **N6. D-items are plain, but a few terms remain for the owner.**
  - D3 says "within 2 ticks"; say "about 4 minutes".
  - D4 gives "about 11.5 units" with no calendar estimate, and uses "presenter rule" without explaining it.
  - D3 uses "p95"; say "almost every time".
  - Otherwise D1-D6 are decidable as written. Each has a recommendation and an alternative, and D6 is correctly framed as a joint confirmation.
- **N7. The "85 in use" connection figure** in R5 and §7 is inconsistent with "about 90" in §5 and §8.

### Checks run

- `git diff bc8fe7077 16eb2b860` on the HTML; the full rev 2 text was read.
- Read on main:
  - `file_code_version.py` (code_version scope and env)
  - the three `BUILDER_VERSION` sites and their builder classes and wiring (`chain/composition.py:85-130`)
  - `period_read.py` version and PENDING handling (`:204-264, 319, 407-432`)
  - the 0047 trigger generator (statement-level)
  - views in migrations (0042, 0051)
  - `importlib` uses
  - `warm_ranges.py` throttle and verify, and its connection count
  - `demo_combined.py:79`, `lab_execution.py:2116`
  - `estate/coverage.py:65-75`, `evidence_money.py:573-594`
- git: 182220d4e is an ancestor of main and of the walk tree f679402c9; `origin/task/ANY-2-AR4b` exists.
- `backlog-post-demo.md:85` (BL-66 8.5 u, ANY-2 5.5) and `coordinator-handoff.md:61, 105-132` were checked against §4b. Accurate except N2.

### Not verified

- No live DB or serve reads in this round, so the connection counts, timers and row counts are taken from the first review and the document.
- The backfill rates were checked only for internal arithmetic (Kobo: 124 hour periods in 34 s, 62 day periods in 103 s; pilot about 20 CPU-hours per kind). The walk build logs were not re-read.

## Re-review (rev 3)

Reviewed: revision 3 at eb8508edc (diff 16eb2b860..eb8508edc on the HTML), against main at eb8508edc. Fresh Claude reviewer. Read-only: code and git reads only; no DB, serve or walk tree touched; nothing changed except this appended section.

### Verdict: ACCEPT WITH NOTES

Every rev 2 finding (N1-N7) is addressed in the body, not only in the changelog. The §4b correction and the re-costing match code and git. The blue/green, fallback-visibility and R0 texts are sound. D1-D6 can go to the owner now. Two Medium spec gaps remain in the new C1/C1b text (P1, P2). Neither affects any D-item or the demo, but both must be fixed in the document, or in the Planner packet, before C1 and C1b are planned.

### Rev 2 findings: resolved in the body?

| Finding | Status |
|---|---|
| N1 builder identity | Direction resolved: the framework computes the version; injected deps, dynamic loads, alembic head, config and env manifests are covered; version groups; drift sampler; trade-off stated; exit tests edit an injected adapter's SQL, a migration view and an env manifest. The mechanism as specified does not work for the cited deps (P1). |
| N1b blue/green | Resolved. Pointer `period_builder_active`, active-version reader, newest-first, no mixed versions per range, `site_read_version` bump on switch, bug-fix PENDING policy. Wording nit in P5. |
| N2 §4b | Resolved and verified. 182220d4e (2026-11-12 06:17, "AR-4: _data_gaps reads coverage.dispatch_days") is an ancestor of main. DISP-1 at coordinator-handoff `:123` shows week 10.9 → 8.6 s. `estate/period_rows.py:46-47` registers only `evidence.claim`; `evidence.provenance` and `money.lines` are declared but not built; `origin/task/ANY-2-AR4b` exists. The serve env (§1, HTML `:275`) serves `dispatch.day,evidence.claim`. `architect-answer-any-range-speed-2026-11-10.md §2` exists. |
| N3 counter | Mostly resolved. Per-statement scope, retries with a forced-deadlock test, the tenant hot row and the bookkeeping precondition are all present. The fallback's `xact < pg_snapshot_xmin(pg_current_snapshot())` is sound: 0047 `:66` has `xact xid8 NOT NULL DEFAULT pg_current_xact_id()`, the same type. The new end-of-transaction call is underspecified (P2). |
| N4 R0 gate | Resolved: first `--verify` only, a user-latency threshold (<1 s against 5.7 s), the midnight check, rollback, variant 1 excluded, default "not done". One gate is not achievable as written (P3). |
| N5 sequencing | Resolved. C2's exit is mini-grid only; C3b carries the cold/EV `outcome.site_row` and provenance, and must finish before C4; the owner is told meanwhile. |
| N6 wording | Resolved ("about 4 minutes", "95 in 100 views", calendar weeks, "prepared date ranges" replaces "presenter rule"). |
| N7 | Resolved. No "85" remains in the HTML. |

### Re-costing check

The stage figures are C1 1.25 + C1b 1.25 (chart `:586` 2.5), C2 3.75, C3 2.5, C3b 2.0, C4 1.0 and C5 2.0.

- Their sum is 13.75, which matches the summary (`:119`), the §6 table (`:346`), the chart (`:596`) and D1.
- C1-C4 sum to 11.75, which matches D4.
- Dropping the already-done second-compose item from C2 is correct, and so is adding the profile and the Findings-by-day kind.
- C3b took on the cold/EV Portfolio inputs without being resized (see P6).

### Remaining findings

#### Medium

**P1. As specified, the "type(dep).__module__" rule misses the injected dependencies it cites, and the reader cannot compute it.**
- **`type(dep).__module__` misses the cited dependencies.**
  - `dispatch_day_builders` injects the bound method `store.dispatch_day_now` (`chain/composition.py:136-137`). Its `type(dep).__module__` is `builtins`, not the `postgres_assessment_store` module.
  - `estate_kind_builders(_estate_evidence_read)` injects an `lru_cache`-wrapped factory (`:91, :106-114`). Its type's module is `functools`, and the class it returns (the estate store) is known only after it is called, which opens a DB service.
- **The reader cannot compute the version at registration.** The reader's PENDING rule takes its versions from `period_kind_versions()` (`:97-104`; used at `:127, 151, 160, 175`). That function deliberately builds no inputs, so a hash computed "when PeriodReadBuilder registers" from live deps is not available on the read path, and the builder and the reader could disagree.
- The drift sampler would catch the resulting stale rows, but only after a deploy.
- **Fix:**
  - Each version group declares its dependency modules statically: the port adapters and the services it is wired to. The hash is computed from that list, with no instantiation, so builder and reader compute the same value.
  - A composition-root test then resolves each actual injected dependency to its defining module, unwrapping it first: `__self__` / `__func__` for bound methods, `__wrapped__` for `lru_cache`, and the factory's return type. The test fails if that module is not in the group's list.
- The exit tests already listed would then prove it.

**P2. "One call at the end of the transaction" does not say how the 0047 statement triggers are kept from bumping earlier in the same transaction, or what happens if the call is skipped.**
- §5 still has `site_read_version` "incremented by the 0047 trigger functions". The triggers fire per statement, mid-transaction, in application order, so they defeat the end-of-transaction sorted bump.
- If the triggers are suppressed for these writers, for example by a `SET LOCAL` flag, a writer that forgets the final call commits facts without a version bump. Cached bodies then serve stale data: the H3 hazard again.
- Fix:
  - The triggers record the touched Sites in a transaction-local set and do not bump when the flag is set.
  - The end call bumps the sorted set.
  - A commit-time guard fails the transaction when the set is non-empty and unflushed, for example a deferred constraint trigger on the collector table.
  - Alternatively, drop the end call and accept deadlock retries only.
- Also correct the C1 stage row (`:456`, "lock order (sorted Sites, then the tenant row)"). It still states the rev 2 rule.

#### Low

- **P3. R0's connection cap is not reachable.**
  - Pools are SQLAlchemy defaults that keep idle connections (`create_engine(..., pool_pre_ping=True)` without `pool_size`, across many stores), so an *idle* walk serve still holds about 90 connections.
  - Two rehearsal processes add about 90 each. That makes about 270, above the 200 gate, and variant 1 (the pool cap) is excluded.
  - In practice R0 can pass only if the walk serve is stopped during the rehearsal. That is an owner-visible condition, and D2 should say it.
  - The gate fails closed (R0 is skipped), so this is not a safety issue.
- **P4. The drift sampler needs a sampling rule.** It must sample only periods that have no dirty or PENDING marks (`period_read.py:400-403` `dirty_marks`). Otherwise legitimately dirty periods fail deploys. It should compare `period_fp` (which already folds in the version, `:204, 288`) rather than raw bodies, unless the bodies are known to be deterministic.
- **P5. Wording.** "Not the active version and not the candidate version" reads as if candidate rows are served before the switch. Say that the reader serves only active-version rows; candidate rows are invisible until the switch.
- **P6. Alembic head and C3b size.**
  - The alembic head makes every group bump on any migration. That is rare today: 1 of the last 40 first-parent commits on main touched `migrations/versions`, and 58 migrations exist. Each such bump still costs about 20 CPU-hours per group at pilot. Note it in C1b's measurement step, or hash only the view and function definitions a group reads.
  - C3b gained the cold/EV Portfolio inputs but stays at 2.0 u. Mark it as a floor.
- **P7. D-items.** D1-D6 read plainly. D2's "a second user worker" and "file stores lose their locking" are the only remaining engineer phrases; "Lab runs could break" would do. This is not blocking.

### Checks run

- `git diff 16eb2b860 eb8508edc` on the HTML. Revision 3 was read in full, with the tags stripped.
- Code read on main:
  - `chain/composition.py:80-150`: the injected deps and `period_kind_versions` with its call sites.
  - `estate/period_rows.py:44-47, 236-241`.
  - `mini_depth/period_rows.py:192-197`.
  - `chain/period_read.py:204, 266-295, 400-432`: fingerprint, dirty marks and the version-PENDING rule.
  - `0047_chain_response.py:66`: the `xact xid8` column.
  - `create_engine` usage: no pool settings.
- git:
  - 182220d4e: its date and subject, and that it is an ancestor of main.
  - the DISP-1 handoff line.
  - the `origin/task/ANY-2-AR4b` branch.
  - migration frequency over the last 40 first-parent commits.
- Arithmetic of all the effort figures in the HTML.

### Not verified

- No live DB or serve reads, so the timers (10.2 / 6.3 / 4.9 s), connection counts and backfill rates are taken from earlier rounds and the document.
- The 11 min + about 1 h re-warm figure for variant 1 was not re-measured.
