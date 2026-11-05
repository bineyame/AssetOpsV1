# Build sheet CH-5c: batched reads, stored route responses, Portfolio payload trim (OWN-CH5c)

- Architect: Claude (Architect 6), 2026-11-04. The owner chose option A (plan row CH5c-R2). Owner, verbatim: "go with option A". Rulings are logged in the plan as **CH5c-R3**. This sheet replaces the 3-unit CH-5c of CH5c-R, whose u1 and u2 batching work is absorbed into §3.1. That sheet's evidence cell and Optimize card (its R4/R5, unit u3) move to **`build-sheet-CH-5d.md`** (lane 2, 1 unit, after CH-6b), because they need EstateChain.
- **Lane 1**, after CH-5a2 and **before CH-5b**: branch `task/CH-5c-reads-and-stored-responses`, cut from main after CH-5a2 merges. **MD-0 must be merged.** Paths: `B/` = `backend/assetops_backend/`, `M/` = `backend/migrations/versions/`.
- Inputs: the CH-5a1 packet and fix-round profile (`AssetOpsV1-ch5a1\.agent\review-packet-CH-5a1.md`); `build-sheet-CH-5a.md` R1, §A12 and §A13; `build-sheet-CH-5b.md` R4 (its watermark moves here, R7); design §11b; EX-3.
- Measured start (CH-5a1 fix round, median cold / warm):

| Route | Cold | Warm |
|---|---|---|
| Cold board | 1.6 s | 0.7 s |
| EV board | 1.8 s | 0.7 s |
| Kobo board | 5.2 s | 3.4 s |
| Summary | 6.4 s | 3.8 s |
| Portfolio | 4.2 s | 3.0 s |

  The Portfolio body is 281 KB. Budgets (unchanged): ≤ 1 s cold, ≤ 300 ms p95 warm, board ≤ 60 KB, Portfolio ≤ 100 KB.

## 0. Result and boundary

**Observable result.**
- The DS-1 script routes are answered from a **stored response** that is built when the chain settles. Both a first request and a repeat meet the budgets, measured.
- A route that is not pre-built is computed once and stored, then served stored until its watermark moves. Uncached compute time is reported honestly; the batching in §3.1 targets about 1.5–2.5 s.
- A stored body is **byte-equal** to a fresh compute of the same request. It is never older than its inputs: the watermark covers every input.
- The Portfolio body is trimmed towards 100 KB, with no rendered content removed.

**Not in this slice.**
- An expression index or any other new index (R5).
- The evidence cell and the Optimize card (CH-5d).
- The ETag/304 (CH-5b reuses R7).
- Any change to a rule, money model, detector, threshold, copy or grade. Any such change is High.

## 1. Rulings (CH5c-R3)

| # | Gap (code reality) | Ruling |
|---|---|---|
| R1 | `_window` is about 15 small statements (3–5 ms each), plus about 38 ms of run-evidence reads and about 39 ms of input-sha hashing per key. It is not one slow query. | **Batch the round trips; keep per-day semantics.** Use one prefetch per (request scope, Site, day range): the `_EVIDENCE` rows over the union range, split in Python by the **same** range predicate; `_attestations` once; the selection heads, jobs, key heads and run evidence for all windows, one statement each (`window_start = ANY(:ws)`). `_configuration` stays per day unless P2 proves that the union read, filtered, equals each per-day read. `input_basis` runs per day over the split rows, unchanged. This applies to every route (boards, summary, Portfolio), through the CH-5a1 read scope. |
| R2 | Parity. | **Deep equality, not similarity** (carried from CH5c-R R2). An L2 test compares the batched day dicts with the per-day path for every seeded day, both live and historical cutoffs, and every job state. The old path is kept as test-only `_select_dispatch_days_each` and deleted at merge. Any difference is High. |
| R3 | Two of the five keys read the same evidence range twice: once live, and once with a cutoff equal to the read time. | **They may share, under one condition.** Inside one read scope that runs in one REPEATABLE READ snapshot, a cutoff `k ≥` the scope's read instant is normalised to **live** in the memo key. This holds because a visible row's `decided_at` (DB `clock_timestamp()` before its commit) precedes the snapshot, and Q31 already treats equality as current. A `k` below the read instant stays a separate key. Prove it with an L2 parity test on one result dict per normalised pair. If any read is outside the scope's snapshot, it keeps its own key, and the packet says so. |
| R4 | Prepared statements. | **Allowed at the driver level only.** No SQL text changes. If the read engine is psycopg 3, set `prepare_threshold`; if it is psycopg2, skip this and report (P3). Apply it to the read engines only (chain read scope, assessment store reads), never to writers. Measure before and after. |
| R5 | The expression index needs a migration and pays off only at volume. | **Not in CH-5c.** Re-evaluate at DD-1b with the 24 h volume (`EXPLAIN (ANALYZE, BUFFERS)` in its packet). If it dominates there, it becomes a post-DD-1 ruling. Otherwise it is a **labelled keep → post-demo**. |
| R6 | Stored responses. | Migration **`chain_response`** (take `down_revision` from main at branch time). Columns: `tenant_id`, `route`, `request_key` (canonical: route, sorted Site ids, window, `known_at` normalised as in R3, query params), `watermark` (R7), `code_version`, `etag` = sha256(`route`, `request_key`, `watermark`, `code_version`), `body` (the exact response bytes), `built_at`, `build_ms`. Unique on (`route`, `request_key`, `watermark`, `code_version`).<br>**Read:** compute the watermark (one statement); on a hit, return the stored bytes; on a miss, compose as today, store, return. The store is insert-only (`ON CONFLICT DO NOTHING`). Keep the latest 3 per (`route`, `request_key`).<br>**Build at settle:** after the chain stage drains (consume → snapshots → threads), pre-build the live routes in `config/chain/prebuilt-routes-v1.json`. Those are the DS-1 script routes: Portfolio week/S/month, the summary, every board in `days.json`, and the Findings index for the story window. Pre-build them in the same tick, bounded by the stage time limit and reported. A historical `known_at` request is stored on first request, because its watermark is fixed.<br>**Wall clock:** P4 lists every wall-clock-dependent field in these bodies. Each one is either removed (DS-R1), part of `request_key`, or proved absent. A live body's `window.known_at` is the build instant, and that is truthful while the watermark is unchanged. It is labelled "as of {built_at}" only if MA-1 already shows a time; no new copy. |
| R7 | The watermark must change whenever a body can. | `B/chain/watermark.py`, which takes the CH-5b R4 key as written: max `event_outbox` (recorded_at, event_id) ≤ k; max `site_day_snapshot.recorded_at` in the window; max `finding_thread_event.seq` for the Sites; the R8 settled flags; the policy versions. **P5** must also prove that price, objective, Foundation, configuration and Action/work writes reach the outbox. Any that do not are added to the watermark explicitly. L2 flip test: changing each input flips the watermark; an unrelated Site's change does not. CH-5b's ETag **is** the stored row's `etag`. |
| R8 | The Portfolio is 281 KB against 100 KB. | **Trim only what nothing consumes.** P6 measures bytes per top-level and per-row field, and lists the frontend and test-contract consumers of each. Remove duplicates and fields with no consumer (for example, repeated provenance blocks or unrendered per-row id lists). Contract and type changes come with their frontend types. If 100 KB needs rendered content removed, stop at the floor and report it. Never drop content to pass. |
| R9 | Budgets. | Reported, never relaxed. The probe reports three numbers per route: stored hit, uncached compute and pre-built first request. EX-3 is judged on the stored or pre-built path, and the packet names the uncached time beside it. |

## 2. Pre-flight (answer from code, the polish clone and L3m; batch the answers, then stop)

- **P1.** Re-profile on main after CH-5a2: the five routes above, with the `_window` split (statements, run evidence, hashing) and the R3 duplicate-key pairs. If the residual is no longer the window round trips, stop: S1 is re-ruled.
- **P2.** `_configuration`: its statements, and whether union-then-filter equals the per-day result.
- **P3.** The DB driver of the read engines, and whether `prepare_threshold` applies.
- **P4.** Every wall-clock read reachable from the pre-built routes' composition, with `path:line`.
- **P5.** For price, objective, Foundation, configuration, Action, work and verification writes: does each reach `event_outbox` (CH-1b register)? Give `path:line`, or "not covered".
- **P6.** Portfolio bytes by field, with the consumers of each.
- **P7.** The chain-stage hook point for the pre-build, and the tick's time headroom (CH-1b `chain_seconds`).

## 3. Work

1. **Batching (R1–R4):** `B/analytics/adapters/postgres_assessment_store.py` (`_prefetch_days`, `_window(prefetched=)`); the R3 key normalisation in the CH-5a1 read scope; the R4 driver setting on the read engines.
2. **Stored responses (R6, R7):** the migration; `B/chain/watermark.py`; `B/chain/response_store.py` (read/insert, prune); route wiring inside `perf.route` for the chain routes, the summary and the Portfolio; the pre-build in the chain stage; `config/chain/prebuilt-routes-v1.json`.
3. **Trim (R8):** the Portfolio composition and its frontend types.
4. **Probe:** `tools/chain_perf_probe.py` gains the three modes from R9. No budget edit.

## 4. Acceptance

- A/B against main on the polish clone (L3) and on L3m: every body is byte-equal (stored and computed), except the R8 trim fields, each listed.
- **Stored equals fresh** for every pre-built route after settle, and again after `late_fill(KOBO-001, D7)` and its consume. Kobo's watermark moves; Cold's does not.
- R2 and R3 parity tests pass. The R7 flip test covers each input.
- COH 0 new. Perf reported per R9.

## 5. Test ladder

| Level | Tests |
|---|---|
| L0 | `test_ch5c_batch.py`: the split predicate (edges, boundary reading, empty day, UTC-midnight crossing); key normalisation; request-key canonicalisation |
| L2 | `test_ch5c_batch_postgres.py` (R2/R3 parity); `test_ch5c_response_store_postgres.py` (hit, miss, insert-only race, prune, R7 flips, stored equals fresh) |
| L2m | Parity over all MD-0 days; stored equals fresh after `late_fill` |
| L3 | Polish clone: settle, A/B, coherence, probe, drop |
| Scoped | `test_ch5a1_*`, `test_ch5a2_*`, `test_w301_*`, `test_w303_*`, `test_qw1_perf.py`, the importers of `postgres_assessment_store`, the frontend Portfolio tests |
| Guards | A, W, N, V, M; the estate guard rule 8 for the new readers |

## 6. Size: 5 units (≤ 6, no split)

| Unit | Content |
|---|---|
| u1 (1.5) | Batching R1–R4 with parity |
| u2 (3.0) | Stored responses R6/R7: migration, watermark, store, wiring, pre-build, flip and stored-equals-fresh tests, A/B |
| u3 (0.5) | Portfolio trim R8 |

## 7. Review focus

- The watermark covers every body input, proved by the flip tests and P5.
- A stored body is byte-equal to a fresh compute.
- Batched reads equal per-day reads.
- No semantic change hides inside "performance".
- Budgets are reported with the uncached time named beside them.

## 8. Revision CH5c-R4 (pre-flight rulings)

- Architect: Claude (Architect 10), 2026-11-05. Pre-flight: `AssetOpsV1-ch5c\.agent\CH-5c-preflight.md` at `fd3348fd7`. Logged in the plan as **CH5c-R4**.
- **Size: 5 → 5.75 units** (≤ 6, no split): u2 3.0 → 3.25 (W1–W6 below), u3 0.5 → 1.0 (Q9).

### 8.1 Q3 is overridden. The watermark rule (W1–W6)

The proposed `count(*)` + `max(xmin)` term is **not sound**, so a stored body could be stale:
- xmin follows transaction start order, not commit order. Suppose T1 (xid 100) updates a row and T2 (xid 101) commits first. A watermark read now sees max 101. When T1 commits, the count and max are unchanged, so the watermark does not move.
- Two more cases miss in the same way: a delete plus an insert in one older transaction, and xid wraparound or subtransaction ids.
- The R7 term "max `event_outbox` (recorded_at, event_id)" has the same hole:
  - `recorded_at` is `clock_timestamp()` taken before commit;
  - `event_id` is a random uuid (`0044_chain_events.py:113,117`).

So R7 is amended. These rules make a stored body never stale:

- **W1. Every term is commit-order monotone.** A term may only be a `count(*)` of rows in a table that the DB enforces as append-only. That means a `ledger_append_only`-style trigger, BEFORE UPDATE OR DELETE, and TRUNCATE refused or covered by W5. The term may be scoped by tenant and Site, and for a historical `k`, by `recorded_at ≤ k`. Snapshots nest, so an equal count means the same committed row set. **No `max(...)` term is allowed.**
  - `event_outbox`, `event_consumption` and `site_day_snapshot` (`0043:62`) become counts.
  - `finding_thread_event` becomes a count only if it is DB append-only. Otherwise it goes under W2.
- **W2. A change log covers every other input.** Migration 0047 adds an append-only table `chain_input_change`:
  - columns: `change_id`, `tenant_id`, `site_id` (nullable), `table_name`, `xact` = `pg_current_xact_id()`;
  - an index on (`tenant_id`, `site_id`);
  - statement-level AFTER INSERT, UPDATE and DELETE triggers with transition tables. Each one inserts one row per distinct Site touched, or a `site_id` NULL row when the table has no Site column;
  - a statement-level TRUNCATE trigger that writes a tenant-wide NULL row.

  This applies to every input table that is not DB append-only, **including outbox producers that are UPDATEd or DELETEd** (for example `recompute_job`'s non-status columns). The watermark term is the count of change rows for the tenant, with `site_id` either in the request's Sites or NULL. It is **not** filtered by `k`, because a late change to a historical row must flip it too. Generate the triggers from one list, following the 0044 pattern. The declared list `config/chain/watermark-inputs-v1.json` stays, as the generator's input.
- **W3. One snapshot.** On every request and every pre-build, the watermark is the **first statement** of the same REPEATABLE READ read scope that composes the body. A hit serves the stored row for that watermark. A miss composes in the same snapshot and stores under that watermark. A watermark read outside the compose snapshot is High.
- **W4. Historical bodies are checked too.** R6's "a historical `known_at` request is stored on first request, because its watermark is fixed" is withdrawn. A row recorded at or before `k` can commit later, and W2 terms ignore `k`. Every request computes the watermark, historical or live.
- **W5. Resets clear the store.** The test harness truncates `chain_response` and `chain_input_change` together. A guard test fails if one table is truncated or reset without the other, because a count that drops can repeat an old value. No pruning of `chain_input_change` in this slice.
- **W6. The guard covers reads and writes.** The listener guard resolves views to base tables (`pg_depend`/`pg_rewrite`) and fails on any relation it cannot resolve. Every base table read by a stored route must be either a W1 count term or W2-triggered for all four operations. This is checked from `pg_trigger`, not from the declared list. The guard is proved non-vacuous: a planted untracked table read fails it.
- **Flip tests (R7) gain three cases:**
  - T1/T2 out-of-order commit on an UPDATEd table;
  - a DELETE;
  - a late-committing outbox row with an earlier `recorded_at`.

  An unrelated Site's change does not flip the watermark, except through NULL-Site (tenant-wide) rows. Those over-invalidate, which is the safe direction, and the packet lists those tables.
- **Cost:** the watermark statement is reported. If it is over 50 ms on the clone, stop and ask (the Q3 default stands). The write cost of the triggers on the tick is reported as before/after settle seconds.

### 8.2 The other rulings

| Q | Ruling | Why |
|---|---|---|
| Q1 | Accept | Stored and pre-built responses meet EX-3. Provenance, coverage and money tuning are out of scope. The uncached time (about 4–5 s for the Portfolio) is named beside each budget (R9). |
| Q2 | Accept | The migration is 0047 on 0044. The slice that merges second re-points its `down_revision`. If CH-9 adds a table that a stored route reads, the W6 guard catches it. |
| Q3 | **Override** (§8.1) | max(xmin) and max(recorded_at) do not follow commit order. A stale serve would be false evidence. |
| Q4 | Accept | Only `known_at` and `selection_token` are wall-clock fields, and both are the build instant. That stays true while the watermark is unchanged. Byte equality is checked after replacing exactly those fields. Historical bodies are checked byte for byte. |
| Q5 | Accept, with additions | `code_version` also hashes the alembic head and every environment setting a composer reads. The packet lists those settings, or says there are none. It also hashes the file list, so deleting a file changes it. |
| Q6 | Accept | The change is driver-level and limited to readers. Measure before and after; if the gain is under 5%, drop it and report. |
| Q7 | Accept | `perf.route` on the Findings index adds no semantics. `/estate/chain` gets the scope only if it becomes a stored route. |
| Q8 | Accept, with conditions | The pre-build calls the same request code path as a request (W3). It holds no Site lease. It prunes the store to the latest 3 per (`route`, `request_key`). Its seconds are reported against the tick's EX-3 "≤ 50% of limit" rule. |
| Q9 | **Override: the trim plus an on-open load; no budget change** | The trim reaches about 135 KB. The other 81.6 KB is `scope_disclosure.sites[].selected_revision_ids`, which is shown only inside the closed "assessment ids" technical disclosure (`EstatePortfolio.tsx:564-571`). The Portfolio body therefore carries `selected_revision_count`, which the summary line already uses (`selectedAssessmentWords(length)`). The ids come from one stored sub-route, `GET /estate/portfolio/scope-ids` (same window, Site and watermark rules), which is fetched when the disclosure opens. It has an honest loading state and an error state, and no new copy beyond the existing labels. Nothing rendered is removed. The estimate is about 55 KB, against the 100 KB budget, which is unchanged. If the measurement is still over 100 KB, stop at the floor and report it. |
| Q10 | Accept | The insert runs on the write engine in its own short transaction, after the compute. The stored bytes are the exact bytes served, serialised once. A failure is logged and the request is never failed. Pruning happens only in the pre-build, so GETs stay light. |
| Q11 | Accept | The cursor, page and `selection_token` are in `request_key`. Only page 1 is pre-built. |

### 8.3 Acceptance additions

- W6 guard green, and non-vacuous.
- The three new flip cases pass.
- The W5 reset guard passes.
- The Portfolio week body is ≤ 100 KB, or the measured floor is reported.
- Each scope-ids disclosure shows the same ids as main, checked by an A/B over the ids.

### 8.4 Revision CH5c-R5 (build questions at `134f04941`)

- Architect: Claude (Architect 10), 2026-11-05. Source: `AssetOpsV1-ch5c\.agent\CH-5c-handoff.md`. Size stays **5.75 units**.

**R5-1. W3 is amended to a before/after check.** The board and the summary span several store transactions (`site_outcomes/read.py:390,460`), so W3 cannot hold as written. The builder's argument is sound, under conditions:
- The watermark counts only rise (W1, W2, W5).
- Every compose read starts its snapshot after the watermark transaction ends, so it sees every commit that W saw.
- A body stored under W is therefore never older than W.
- Any later commit raises the count, and the count never returns to W. A body containing δ can only be served to a request whose watermark snapshot was taken before δ committed. That request sees data that was already committed, which is newer, never stale.

It is also not consistent: a multi-transaction compose can be torn across δ. So:
- **(a)** Read the watermark and look up the stored row in one short REPEATABLE READ transaction. Close it before the first compose read.
- **(b)** No compose read may use a memo or cache that was filled before (a). The read-scope memo is created after (a). There is no cross-request cache.
- **(c)** On a miss, compose, then re-read the watermark in a new short transaction:
  - if it equals W, store the body under W;
  - if it differs, serve the body and **do not store it**, and log the race.
  
  Stored bodies are therefore quiet-state bodies, and this keeps "stored equals fresh" true by construction. The cost is one watermark statement, on misses only.
- **(d)** The pre-build follows the same rule.
- **(e)** An L2 test commits a change-log write between the compose reads, and asserts that the body is served and nothing is stored.

**R5-2. Over-invalidation: keep complete coverage, and narrow the scope instead of excluding tables.**
- **Triggering the append-only tables too is accepted.** One mechanism is simpler and still sound.
- **`event_consumption` is not excluded by assertion.** P5 found it read by the stored routes as the settled flags. Excluding it is allowed only if the W6 listener proves that no stored route reads it. Then the guard pins that fact, and a future read fails the guard.
  - Otherwise it stays, but Site-scoped. The trigger joins its transition table to `event_outbox` on `event_id` and writes one row per distinct `site_id`. It writes NULL only for outbox rows that have no Site.
- **`site` is Site-scoped by its own id.**
- **`tenant` and TRUNCATE stay tenant-wide.** Their writes are rare, and TRUNCATE is harness-only.
- **The packet lists every table that still writes tenant-wide rows.**
- **Idle stability test:** run two consecutive ticks with no new data on the clone. The watermark of every pre-built route must not move.
  - If a table flips it on an idle tick (heartbeats, `recompute_job` non-status columns, leases), stop and report it with the columns written. The Architect then rules column-listed `UPDATE OF` triggers, proven against the columns the routes read.
  - Never exclude a table to make the test pass.
- **Speed during a live demo is accepted as honest.**
  - A real data change invalidates the routes it touches. The Portfolio spans every Site, so any Site change invalidates it.
  - The Q8 pre-build re-warms them after the tick. The pre-build runs only when a watermark moved.
  - Between the change and the re-warm, a request is an uncached compute (about 4–5 s), never a stale serve.
  - The packet reports the measured re-warm seconds after `late_fill`.
  - The DS-1 script runs on a settled chain. Keeping the demo on settled state is DS-1's job, not this slice's.

### 8.5 Revision CH5c-R6 (packet open item at `1f74ea49d`; Architect 11, Claude, 2026-11-05)

**Size: CH-5c goes from 5.75 to 6.0 units (+0.25), which is at the cap, so there is no split.**

- **Facts.** `code_version` hashes the cursor keys correctly, because they shape paged bodies (Q5). The fault is in the launch path:
  - `demo_combined` runs the TICK child with `self.env()` (keys popped), but serves with `self.env(keys=True)`.
  - So in a real demo run, every pre-built row is a miss for the server.
  - `_PRUNE` partitions by (route, request_key) only, so wrong-version rows can evict the server's own rows.
- **The fix (builder 1 and 3 accepted; one guard added):**
  1. `tools/demo_combined.py` runs the TICK child with the serve env (`py(..., keys=True)`). Both children get their environment from one function, so they cannot drift. `chain_clone.settle_env` stays keyless, because clone settles are not served.
  2. `report.prebuild` gains `code_version` (the 16-hex prefix) next to the stage outcome, so a demo log shows a mismatch.
  3. **The guard that makes it bulletproof, not just this launcher:** the `prebuild` stage writes nothing when any of `KEY_NAMES` (the cursor keys the server needs to serve) is absent from its process. It reports `SKIPPED_NO_SERVE_ENV` instead. A keyless tick from any launcher then cannot waste 37–93 s or store rows no server will read.
- **Prune: keep rows per version, and never delete by "not my version".** `_PRUNE` partitions by (route, request_key, code_version) and keeps the latest 3 in each.
  - Deleting other-version rows is rejected. A process whose version differs from the server's would delete the server's live rows, which is this defect again.
  - Dead versions after a code change are cleared by the existing W5 reset and the prepare.
  - The packet reports the `chain_response` row count after the L3 run.
- **Tests (+0.25 in total):**
  - **Env parity, L0/L1, no DB:** build `demo_combined`'s tick env and serve env, compute `code_version()` in a child process for each, and assert they are equal. It must fail when the keys are popped from one; prove that once.
  - **L2:** a keyless pre-build stores 0 rows and reports `SKIPPED_NO_SERVE_ENV`.
  - **L2:** rows of version A are not pruned by version-B inserts beyond A's own 3.
- **Factory (`create_app` vs `lab_app.build_app`):**
  - Unify only if `B/` may call it without breaking the architecture seam guard. `B/` must not import `host/`.
  - Otherwise, keep `main.create_app()` and pin the parity: the packet re-runs `fresh` (stored vs `lab_app` bodies, today 23/23 equal) on the L3 data after the fix. Any difference is a stop.
  - A seam-legal factory injection is post-demo.
- **Acceptance addition:** a short real demo run (`demo_combined` serve with one data-bearing tick). The first request after the tick to the Portfolio and the summary returns `X-AssetOps-Stored: hit` within budget, and `report.prebuild.code_version` equals the server's.

### 8.6 Revision CH5c-R7 (review REVISE at `0353f63ed`; Architect 12, Claude, 2026-11-05)

Source: `.agent/review-CH-5c.md` (H1, H2, M1-M3, L1-L7). Both Highs are accepted as stale-serve paths. The packet's Q4 claim ("only `known_at` and `selection_token` are wall-clock fields") and the sheet's "the watermark covers every input" were both wrong, because the watermark sees only DB writes.

**Size and split.** The fix is about 2.5 units, and CH-5c is already at the 6.0 cap, so the slice splits:
- **CH-5c (stays 6.0) merges with the response store OFF.** `response_store.enabled()` defaults to off. A pre-build with the store off stores nothing and reports `SKIPPED_STORE_OFF`. `demo_combined` does not turn it on. The slice therefore delivers the batching (u1), the Portfolio trim and the scope-ids route (u3), migration 0047 (store, change log and triggers) and the dormant store code. No stored body can be served, so neither High can reach a client. Its merge chores are M3 and L7 below. The §8.5 E4 acceptance moves to CH-5c2.
- **CH-5c2 (new, 2.5 units, lane 1, directly after CH-5c and before CH-5b; branch `task/CH-5c2-store-on`)** does H1, H2, M1, L1, L2, L3, L4 and the `code_version` residual. It then turns the store on by default and passes the E4 check. CH-5b reuses the stored ETag, so CH-5b waits for CH-5c2.
- **Why not one round:** 8.5 units is over the cap, and the two Highs are new mechanism (a file term and an expiry), not corrections. Merging CH-5c with the store off costs the demo nothing yet, because nothing before CH-5b is judged on stored speed, and it unblocks CH-9's merge order.

**H1 (CH-5c2, 0.75). File-backed inputs join the watermark as a file-state term.** The reviewer's (a) is adopted in a cheaper form; (b) is rejected.
- **Why not (b), the gate result in the key:** evaluating the gates on every request runs the lineage DB reads and the legacy history loads on the hit path. The (c) re-check would then need a second evaluation.
- **Over-invalidation is accepted.** The demo loop writes a new report on every tick (`performance_migration run`, with a new `report_id` and `compared_at`). A content digest would therefore move on every loop tick, just as the cheaper file-state term below does. That is the safe direction, and F5 re-warms the routes in the same tick.
- **F1. The survey.** List every non-DB input that a stored route's compose reads, with `path:line`: files, directories, manifests, environment, process memos and caches, network. Each one is classified as one of:
  - hashed by `code_version`;
  - a declared file input (F2);
  - proved absent.

  Known so far:
  - `EVIDENCE_STORE_ROOT/migration-performance` (Performance gate);
  - the S2 comparison reports, the legacy evidence inventory, the commit store and `current_store_root` (`ledger_reads.s2_scope`, `evidence_migration.py:79-92`);
  - `legacy_dispatch_claims`, which is the legacy assessment history (`performance_migration.py:32`);
  - whatever backs `finding_index_gate`.
- **F2. The term.** Declared roots are listed in `config/chain/file-inputs-v1.json` and read through a `chain/adapters/` port (seam rule as for `file_code_version`). For a request, `F` = sha256 over, for each root relevant to the request's Sites: the root's canonical path, then for every regular file under it the sorted (relative path, size, `mtime_ns`). A missing root hashes as `absent`. `F` is read at (a) together with the DB watermark and appended to `W`, so the lookup, the insert and the ETag all include it. It is read again at (c): if `F` changed, the body is served and not stored (`race`). The pre-build follows the same rule.
- **F3. Cost.** `F` ≤ 20 ms per request on the polish data. If it is over, narrow each root to the per-Site sub-paths the gate reads; never drop a root.
- **F4. The guard: no unlisted non-DB read during compose.** A test-only `sys.addaudithook` is active only inside a stored-route compose (a contextvar set by `serve`). It runs in an L2 test over every stored route and inside the W6 CLI run. It fails on:
  - an `open`, `os.listdir` or `os.scandir` of a path that is neither under a declared root nor in the `code_version` file set (backend sources, `config/`, migrations, hashed manifests, and `host/` and `contracts/`, see below);
  - any `socket.connect` other than to the DB.

  Prove non-vacuity once each with a planted file read and a planted directory listing.
- **F5. The demo loop order.** In `demo_combined.tick`: the tick runs with its pre-build stage disabled (a stage flag), then `performance_migration run`, then the pre-build stage alone, in the serve env. With F2 the old order is no longer stale, only slow. This order makes E4 step 2 a hit. Other launchers keep the in-tick pre-build.
- **F6. L2 test.** Two identical board requests with a new Performance report written between them. The second is not a `hit`, and its body shows the new gate state. Repeat for a report that closes the gate (planted FAILED). On the summary, the same with an S2 report.

**H2 (CH-5c2, 1.0). A live body carries `valid_until` and is a miss after it.** The approach is adopted, with three rules that make it never late.
- **C1. One clock seam.** Compose code reads the wall clock only through `read_scope.clock()`. It compares clock-derived instants only through registering helpers:
  - `read_scope.within(start, end, at)` (half-open) registers `start` if `at < start`, and `end` if `start <= at < end`;
  - `read_scope.since(t, lookback, at)` (`at - lookback <= t <= at`) registers `t` if `t > at`, and `t + lookback` otherwise.

  Rewrite `estate/coverage.py:410-411`, `chain/read.py:245,256` and every other site the survey finds to use them. The verdicts are unchanged: this is a semantics-preserving rewrite, and the A/B stays byte-equal.
- **C2. Computing `valid_until` so it can never be late.** `valid_until` = min(every registered boundary later than its own `at`, the earliest next local midnight over the request's Sites) − 1 s.
  - Each registered boundary is the earliest instant at which that comparison's result can change, rounded down, never up. For inclusive ends, use the instant itself, not +1 µs.
  - The midnight cap catches any date-granular "today" logic the survey misses, at the cost of one rebuild per route per day.
  - The 1 s margin covers app/DB clock skew on one host.
  - A historical request (`k` fixed) registers nothing that can expire, and gets `valid_until` NULL.
  - New column `chain_response.valid_until` (edit 0047 in place; it is unmerged). The lookup condition is `valid_until IS NULL OR valid_until > clock_timestamp()`.
- **C3. Every clock read in compose is accounted for.**
  - **Survey:** every wall-clock read reachable from the stored composers, with `path:line`, in Python and in SQL (`now()`, `clock_timestamp()`, `current_date`, `current_timestamp`, `localtimestamp`, `statement_timestamp()`, `transaction_timestamp()`). Each read is classified as one of:
    - a read instant used only in a Q4-masked field;
    - a read instant whose every comparison goes through C1;
    - not in compose (a writer).

    `perf_counter` and `monotonic` are not wall clock.
  - **Static guard** (architecture or L0): in the stored-composer modules (the W6 listener's module set), no `datetime.now`, `utcnow`, `date.today` or `time.time` outside `read_scope.py`, and no SQL clock function outside a named allowlist of read-instant captures. A planted `datetime.now()` fails it.
  - **Listener guard:** the W6 run fails on a compose statement that uses a SQL clock function in a predicate.
- **C4. Tests.**
  - **Moved clock:** monkeypatch `read_scope.clock()` across a plan-window end, and separately across the 30-day edge, between two requests. The second request is not a `hit`, and its body shows the new label or count.
  - **Sweep (the completeness proof on data):** on the L2 seed, with plan windows and a verified outcome placed within 40 days, compose each stored route at `t0` and at each candidate instant up to 40 days later. The candidates are every timestamp in the seeded input rows, the same plus `VERIFIED_LOOKBACK`, each ±1 µs, and each local midnight. Assert: if a body (Q4-masked) differs from the `t0` body at `t`, then `valid_until(t0) <= t`.
- **C5. The pre-build runs every tick**, not only when a watermark moved (amends R5-2). A hit costs about 50 ms, so an expired live row is re-warmed within one tick.
- **Amends Q4:** the wall-clock fields are `known_at` and `selection_token` (masked), plus every C1-registered comparison (expiring).

**M1 (CH-5c2, 0.25). Accepted as written.** Wrap the (c) re-check. On any store exception after compose, serve the composed bytes with `unstored` and no ETag, and store nothing. L2 tests use a failing port for each of lookup, re-check and insert, and each asserts a 200 with the correct body.

**M2. An open acceptance item with an owner, not a Pass.** The packet's "Cost" line reads "open, owned by DD-1b".
- The **DD-1b packet** reports, on the 24 h volume, for one data-bearing tick:
  - the change rows written;
  - settle seconds with and without the triggers (one A/B);
  - `wmtime` for the tenant-wide and per-Site terms at the resulting log size.
- **Stop rule:** `wmtime` > 50 ms, or a trigger cost > 10% of settle seconds, goes to the Architect. The likely ruling is a per-(tenant, Site) counter row instead of `count(*)`, which also removes the growth.
- CH-5c2's E4 run records the change rows per data-bearing tick as a first data point.
- No change-log pruning before the demo: a prune breaks count monotonicity (W5).

**M3. Accepted. The merge chores belong to whichever of CH-5c and CH-9 merges second.**
- Re-point its migration to `0048` on the other's head.
- Replace the literal head pin (`test_ch5c_watermark_postgres.py:213`) with an L0 test that asserts exactly one alembic head and that `code_version` includes it. This lands in CH-5c now, so the trap fails loudly.
- Run the W6 CLI on a clone of the merged tree (`unresolved []`, `untracked []`, `event_consumption_read` as recorded) and `fresh` on the same clone. With the store off, `fresh` runs with the store forced on in the probe only.
- Record both in the merge packet.

**L items.**
- **L1 (CH-5c2): fix.** Send no ETag on `race` or `unstored`, or when the insert's `ON CONFLICT` inserted nothing (the insert reports its rowcount). CH-5b builds on this tag.
- **L2 (CH-5c2): fix.** Bind `clock_timestamp()` in the first statement of `postgres_estate_read.py:93` and `postgres_evidence_money_read.py:39`. Under REPEATABLE READ the snapshot is taken at that statement, so `read_at` ≥ the snapshot instant and R3 holds as written.
- **L3 (CH-5c2): fix the cheap gaps.** Add schema-qualified names and comma-joined FROM lists to `chain_watermark_guard.targets`, each with a planted test. SQL-function bodies and non-Engine statements stay a named residual. File reads are covered by F4.
- **L4 (CH-5c2): fix.** Add a BEFORE TRUNCATE refusal on `chain_input_change` in 0047. The W5 harness reset runs under `replica` and is unaffected; prove that once. Add a guard rule that owns `chain_input_change` as trigger-written only, as for `event_outbox`.
- **L5:** folded into F6 and C4, which drive the board, the summary and the Portfolio with its scope-ids sibling. Per-caller admission differences are post-demo, since the demo has one development tenant.
- **L6:** a packet note only. The scope-ids are honest live data.
- **L7 (CH-5c merge): fix.** Move the per-day loop into the test module as a test helper over `_window(prefetched=None)`, and delete `_select_dispatch_days_each` from the product code in the same commit. Re-run the 279-day clone parity once at the final head before the merge.
- **`code_version` residual (CH-5c2): fix.** Hash `host/**/*.py` and `contracts/**` too.

**CH-5c2 acceptance.**
- F6, C4 and M1 tests pass.
- The F4 and C3 guards are green and non-vacuous.
- A/B byte-equal to CH-5c, except the Q4 fields.
- `fresh` 23/23.
- Idle stability: two settles with no data and no comparison run; the DB watermark and `F` are both unmoved.
- The review's E4 check (`review-CH-5c.md` "R6 E4 check"), with F5's order. Step 4 holds after the comparison step.

### 8.7 Revision CH5c2-R1 (CH-5c2 pre-flight; Architect 12, Claude, 2026-11-05)

Source: `AssetOpsV1-ch5c2\.agent\CH-5c2-preflight.md` (branch `task/CH-5c2-store-safety`, `55219fd1f`). **Size: CH-5c2 goes from 2.5 to 3.0 units (+0.5).** The increase covers the extra clock comparison sites (`portfolio.py:573`, the assessment store FUTURE_NOTE at `:2200`, `verification.py:982`, the objective predicate), migration 0048 and the module-set file. That is under the cap, so there is no split.

**Forced deviation, accepted.** 0047 is merged, so `valid_until` and the L4 TRUNCATE refusal go in a new migration, `0048_chain_response_expiry`, on 0047. The M3 rule stands: whichever of CH-5c2 and CH-9 merges second re-points to the next free number on the other's head (`0050` on `0049_mini_service_v2` if CH-9 lands first). It also runs W6 and `fresh` on a merged-tree clone. The single-head L0 test catches a miss.

| Q | Ruling |
|---|---|
| Q1 | **Accept.** The DB read-instant captures (§3 list) are the named allowlist. C1 governs comparisons: every comparison of a clock-derived value goes through `within`/`since`, with `at` = the captured instant. Python `datetime.now` and injected `self.clock()` defaults in compose paths become `read_scope.clock()`. **Added:** every Python or DB clock value that reaches a stored body as an output field (for example `actions/site_index.py:164` `read_at`) is either added to the Q4 mask list, with its name and a "build instant" reason in the packet, or proved not to reach a stored body. An unmasked clock field in a stored body is High. The rest of §3 (`verification.py` 149/379/547/784/903/964, `analytics/service.py:151`, `sites/cutover.py:209`, `gateway_api.py:109`) is each classified in the packet as an output field (masked), a comparison (C1) or not in a stored compose. |
| Q2 | **Accept, as a named residual.** A live row's write time is at or before its commit, which is before the snapshot, which is at or before the read instant (after L2). So `col <= :k` on DB-clock write-time columns cannot change without a write that moves W. The residual is a future-dated write-time from a fixture or a manual insert. The C4 sweep covers the seed, and the 1 s margin covers clock skew. |
| Q3 | **Accept.** Allow `sys.prefix`, `sys.base_prefix` and the site-packages trees, read-only, as installed runtime. Any `socket.connect` inside the compose contextvar fails unconditionally. The hook stays test-only and scoped to the contextvar. |
| Q4 | **Accept.** The live read binds `read_scope.clock()`. The head per key is picked in Python, and a `recorded_at > at` registers that instant as a boundary. Historical `k` is unchanged. **Added:** an L2 parity test shows the objective heads are equal between the old SQL and the new path, both live and historical, on the seed. The listener guard must then pass. |
| Q5 | **Accept.** The W6 CLI records the executed backend modules into the committed `config/chain/stored-composer-modules-v1.json` (hashed through `config/`). The CLI fails on an executed module that is not listed, and the L0 static guard reads the same file. Updating the list is a reviewed diff, never an automatic write in a normal run. |
| Q6 | **Accept.** Roots are named symbolically and resolved at read time from the adapters' root constants, so a patched root is followed. Estate and Portfolio routes hash every tenant Site's roots. This over-invalidates once per loop tick and is re-warmed by F5, which is accepted. Report the `F` time against F3's 20 ms. |
| Q7 | **3.0 units.** Build every site in pre-flight §3. Any site found beyond it is a Known Deviation, with `path:line`, and goes to the Architect before merge if it is a comparison that reaches a stored body. It is never silently left out. |

C5 is already true (`stages.py:444-448`), so only the docstring changes. The §8.6 acceptance is unchanged.
