# Review CH-5c (OWN-CH5c): batched reads, stored route responses, Portfolio trim, R6

- Reviewer: fresh Claude reviewer (did not author the slice), 2026-11-05.
- Branch `task/CH-5c-perf`, worktree `AssetOpsV1-ch5c`, head `0353f63ed`, base `fd03ae6b0`. Diff
  `git diff fd03ae6b0...HEAD -- ':!.agent'` (42 files, +2533/-94). Worktree clean.
- Judged against `build-sheet-CH-5c.md` §0-§8.5 (binding: §8.1 W1-W6, §8.4 R5-1/R5-2, §8.5 R6, Q9) and the packet
  `.agent/review-packet-CH-5c.md`.

## Verdict: REVISE

The mechanism is well built: change-log watermark, before/after rule, insert-only store, per-version prune,
keyless-skip guard, honest guard fix. But it has **two stale-serve paths (High)**. In both, a stored body depends on
an input that is neither a DB write the triggers see nor part of `code_version`. The packet's P4/Q4 claim, "only
`known_at` and `selection_token` are wall-clock fields", is wrong. Both paths can be reached in the real demo loop
(`demo_combined serve`) and on any day after the stored rows were built.

## Findings

### H1 (High): file-backed gate inputs reach stored board and summary bodies; neither the watermark nor `code_version` covers them
- **Where.**
  - `site_outcomes/read.py:229` and `:246`: `_open(s.finding_index_gate, ...)` and `_open(s.performance_gate, ...)`
    inside the mini board ports. A closed gate raises `PortUnavailable`, so the board reads PARTIAL / not available.
  - `site_outcomes/composition.py:35-46`: `overview_source` uses `s2_scope(code)`, which is
    `evidence/ledger_reads.py:212-236`: the newest S2 comparison report, the legacy inventory and the store root.
  - `main.py:391-400`: `performance_gate` = `permits_performance_cutover(performance_reports.latest(site_code), ...,
    legacy_claims=...)`. `performance_reports` is `ComparisonReportFiles(EVIDENCE_STORE_ROOT /
    "migration-performance")` (`evidence/composition.py:112-116`). These are files, not DB rows.
  - `analytics/performance_comparison.py:244-250`: the gate also closes when the classified revisions are "no longer
    selected (reassessed since the comparison); rerun it". It returns `report["statement"]` as the open reason.
- **Reachable in the demo loop.** `tools/demo_combined.py:463-470` runs the TICK, whose `prebuild` stage stores the
  KOBO boards and summaries, and **then** `performance_migration run`. `performance_migration.py:46-90` writes only a
  report file. Two cases:
  - A tick that reassesses KOBO closes the gate at pre-build time. The rerun then reopens it, but the stored body
    stays under the same W, because no input table was written.
  - Even with no closure, the gate's reason text comes from the newest report.

  Either way the stored board or summary is served stale until some unrelated DB write moves W. The W6 guard is a
  DB-statement listener, so it cannot see file reads. `fresh` 23/23 compares stored and fresh bodies at the same
  instant, so it cannot catch this either.
- **Why it matters.** This is a stale stored body served to a client (High by the review rule). On the dispatch
  section it is false evidence: the board says not available while the comparison has passed, or the reverse.
- **Fix (any one, plus a test).**
  - (a) Put each request Site's file-backed gate state into the stored key. Read it in the R5-1(a) step and add it
    to `request_key` or the watermark: the newest performance and S2 report ids or sha, `current_store_root()`, and
    the legacy inventory or claims digest. The check (c) must re-read it too.
  - (b) Evaluate the gates before `serve` and put the `(permitted, reason)` pairs in the key.

  Add an L2 test: write a new comparison report between two identical board requests, and assert that the second
  is not a `hit` and that its body shows the new gate. Also reorder `demo_combined.tick` so the comparison runs
  before the pre-build, or pre-build again after it.

### H2 (High): stored live bodies carry wall-clock-derived fields beyond the Q4 pair
- **Where.**
  - `estate/coverage.py:386,410-411`: `_verification_window = later_start <= k < later_end` and
    `_verified_recent = k - VERIFIED_LOOKBACK (30 d) <= verified_at <= k`. For a live request, `k` is the read
    instant (`estate/index.py:259`).
  - `chain/read.py:245,256,266`: the same window test with `at = datetime.now()` when `k` is None (the board's
    `action_rows`).
  - Consumers:
    - `estate/portfolio.py:222`: the workflow label "Outcome pending";
    - `estate/portfolio.py:613-614`: `pending_trial_count` and `verified_resolution_count`;
    - `estate/index.py:409`;
    - the mini board Action labels.
- **Why it matters.**
  - Story data is dated October 2026, and live reads are at the current date, so the 30-day "recent verified" count
    and the plan-window labels change as the calendar moves, with no data write.
  - Idle ticks write 0 change rows (packet: idle `moved {}`), so a live Portfolio, summary or board stored on day N
    is served on day N+k with the old counts and labels. That includes rows built by the prepare's own ticks, now
    that ticks pre-build with the serve env.
  - `known_at` (the build instant) was accepted as truthful by Q4. These fields are not.
- **Fix.** For a live request, the compose returns its next wall-clock boundary: the minimum, over values later
  than `k`, of `later_start`, `later_end` and `verified_at + VERIFIED_LOOKBACK`. Store it as `valid_until`. The
  lookup treats `now >= valid_until` as a miss. The alternative is a boundary epoch in `request_key`.
  - Redo the P4 survey over every wall-clock read reachable from the stored composers, with `path:line`.
  - Add a test with a clock monkeypatched across a plan-window end or the 30-day edge between two requests: the
    second request must not be a `hit`.

### M1 (Medium): the (c) re-check can fail a request; the store-failure paths are untested
- **Where.** `chain/response_store.py:133`: `after = self.watermark(req)` is outside any `try`. A DB error on the
  re-check, after a successful compose, propagates and fails the request. The (a) lookup and the insert are
  guarded; this read is not.
- **Why it matters.** Q10 and the brief: "a store failure is logged and never fails the request". There is no test
  for the `unstored` paths (a lookup failure, an insert failure). `test_ch5c_response_store_postgres.py` covers
  hit, miss, race, admission and prune only.
- **Fix.** Wrap the re-check. On an exception, serve the composed bytes with `X-AssetOps-Stored: unstored` and store
  nothing. Add tests with a failing port for lookup, re-check and insert, each asserting a 200 and the correct
  body.

### M2 (Medium, acceptance gap): trigger write cost and watermark growth were never measured under data
- §8.1 "Cost" requires the triggers' tick write cost as before/after settle seconds. Every measured settle was idle,
  with 0 change rows (packet "Timings"), so the measurement says nothing about the cost.
- `wmtime` (2-6 ms) was measured on a near-empty `chain_input_change`. Nothing prunes it, and the Portfolio, summary
  and Findings use the tenant-wide count (`_TENANT_WATERMARK`), which scans the tenant's whole range.
- Statement-level transition tables also add a tuplestore per input statement.
- Risk judgement:
  - It is likely fine at demo volume: at most one change row per (statement, Site), and a count over the
    `(tenant_id, site_id)` index.
  - It is unproven at DD-1b's 24 h volume, and the 50 ms stop rule has never been tested under load.
- **Fix.** Name a measurement point that carries an owner, for example DD-1b or E-stage with the 24 h volume. It
  should report change rows per data-bearing tick, settle seconds with and without the triggers, and `wmtime` at
  that log size, against the 50 ms stop rule. Until then, record it as an open acceptance item, not as "Pass".

### M3 (Medium): merge traps with CH-9 (`task/CH-9-measured-daylight` @ `c61be3a73`)
- `git merge-tree --write-tree HEAD task/CH-9-measured-daylight` returns exit 0, tree `2be5f3896...`, with **no
  textual conflicts**. The merged tree holds `0046_daylight_enqueue` (on `0044`), `0047_mini_service_v2` (on `0046`)
  and `0047_chain_response` (on `0044`), so it has **two alembic heads**.
- Consequences:
  - `alembic upgrade head` refuses.
  - `file_code_version.alembic_head()` returns `"0047_chain_response,0047_mini_service_v2"`.
  - `test_ch5c_watermark_postgres.py:213` (`== "0047_chain_response"`) fails.
- The slice that merges second must re-point its migration to `0048` on the other's head (both docstrings say so),
  and the head pin must be updated.
- **Semantic trap.** CH-9 adds no table, but it changes stored-route composers and readers: `chain/read.py`,
  `site_outcomes/mini.py`, `site_outcomes/read.py` and `mini_depth/read.py`. The W6 read-set check exists only as a
  CLI run on a clone (`tools/chain_watermark_guard.py`). No automated check re-verifies the merged tree.
  - **Required at the second merge:** run the W6 CLI on a clone of the merged tree. It must show `unresolved []`,
    `untracked []` and `event_consumption_read` as recorded. Record the run in the merge packet.
  - CH-9's `0047_mini_service_v2` enqueue will run under the change triggers if CH-5c merges first. That writes
    change rows, which is safe over-invalidation.
- If CH-5c merges first, CH-9's `0046` must re-point to `0047_chain_response`.

### L1 (Low): the ETag on non-stored bodies
- `response_store.py:136` gives the `race` body `ETag` = tag(W), although its bytes can contain the post-W change δ.
- Two concurrent quiet composes under one W also return different `known_at` and `selection_token` bytes under the
  same tag, because the loser's `ON CONFLICT DO NOTHING` still returns its own bytes.
- This is harmless today, since there is no 304 yet. CH-5b reuses this tag, though.
- Omit the ETag on `race`. On a lost insert, return the stored row's bytes or omit the tag.

### L2 (Low): the R3 read instant is the transaction start
- `postgres_estate_read.py:93` and `postgres_evidence_money_read.py:39` bind `read_at = now()`, which is the
  transaction start, not the snapshot instant.
- A row committed between BEGIN and the first statement is visible with `decided_at > read_at`. A cutoff in
  `[read_at, decided_at)` would then be normalised to live and include it.
- The window is microseconds. It still contradicts the R3 premise as written. Bind `clock_timestamp()` taken in
  the first statement, or note the bound.

### L3 (Low): blind spots of the W6 listener
- `tools/chain_watermark_guard.py:30-35` (`targets`) has these gaps:
  - it skips schema-qualified names (`public.x` reads as a column);
  - it misses comma-joined FROM lists;
  - it does not see inside SQL functions;
  - it sees only SQLAlchemy `Engine` statements;
  - it does not see file reads (H1).
- No comma-joined input read was found in `backend/assetops_backend` today. The packet names only the SQL-function
  gap.

### L4 (Low): `chain_input_change` truncation is not refused
- W5 pins the test harness only (`pg_harness.RESPONSE_TABLES`). Migration 0047 refuses UPDATE and DELETE on
  `chain_input_change`, but not TRUNCATE, and the architecture guard does not own the table as trigger-only (as it
  does `event_outbox`).
- A runtime `TRUNCATE chain_input_change` without `chain_response` would let a count repeat.
- Add a BEFORE TRUNCATE refusal, or a guard rule.

### L5 (Low): stored-path coverage outside the Findings route
- The L2 store tests drive only the Findings router.
- These are covered only by the L3 `fresh` run:
  - the board's own key;
  - the summary's re-implemented `admit` (`outcome_api.py`: `admitted` + `disclosed`, mirroring `estate_sites`);
  - the Portfolio's two-route insert.
- One L2 test per route would pin admission-in-key and the scope-ids sibling row. That matters if non-development
  access or disclosure ever differs per caller.

### L6 (Low): the scope-ids load is not pinned to the shown body
- A live Portfolio body and its later on-open scope-ids read are not tied to one cutoff or watermark. If data
  changes in between, the ids can disagree with the count already shown.
- This is acceptable as honest live data. Note it in the packet, or pass `window.known_at` (which costs an
  uncached historical key).

### L7 (Low, process): deleting `_select_dispatch_days_each` at merge breaks the parity test
- R2 requires deleting the test-only `_select_dispatch_days_each` at merge. Both parity tests in
  `test_ch5c_batch_postgres.py` call it, including the L2m clone test, so the deletion must convert or remove them
  in the same commit.
- The 279-day clone parity ran once, at `b38bcaf45` (handoff 2), and the store file has not changed since. It was
  not re-run at head and is skipped by default.

## Focus items checked (no finding)
- **Trigger coverage.**
  - Migration 0047 generates INSERT, UPDATE, DELETE and TRUNCATE triggers for every input from one list.
  - UPDATE uses the union of old and new, so a Site move flips both Sites.
  - The L0 test pins the declared list against the migration list, and an L2 test checks all four bits from
    `pg_trigger`.
  - W6 is non-vacuous: a planted table, a planted view and a dropped trigger each fail it.
- **`event_consumption`.** It is Site-scoped through `JOIN event_outbox`. A cascade DELETE whose outbox row is
  already gone writes nothing for consumption, but the outbox DELETE itself writes the same Site.
- **W4 and W5.** Every request computes W, historical requests included. The reset empties both tables together
  (under `replica`, which also bypasses the append-only trigger).
- **The race rule.** (a), (b) (`read_scope.fresh`) and (c) are implemented as ruled. The (e) test commits an
  outbox row mid-compose and asserts that the body is served and nothing is stored. It is non-vacuous.
- **Caches.** No cross-request cache: the only `lru_cache`s hold `config/` files, which `code_version` hashes.
- **`code_version` env.** A grep of `os.environ` and `getenv` under `backend/assetops_backend` matches the
  `COMPOSER_ENV` list. `DATABASE_URL` and `ASSETOPS_SERVER_TIMING` are correctly excluded.
- **`code_version` files.** It hashes `assetops_backend/**/*.py`, `migrations/versions/*.py` and `config/**`, with
  CRLF normalised.
- **What `code_version` does not hash.** `contracts/` and `host/` (`lab_app`, the serving factory) are not
  hashed. I found no stored composer that reads `assetops_contracts`. `lab_app` only adds resolved flags and
  execution, and `fresh` 23/23 pins parity on data. **Residual:** a `host/` change that alters a body would not
  change the version.
- **Q9.**
  - The ids load on the first open (`onToggle`, only when open), with a `role=status` loading line ("Assessment
    IDs…", built from the existing label), the refusal copy on error, and one read per Portfolio window.
  - The count line uses `selected_revision_count`, and the disclosure provenance is still read only as `=== null`.
  - Nothing rendered was removed. Two frontend tests cover it.
  - Backend: `test_w303_*` pins count = len(ids) and scalar-only provenance.
- **R6.**
  - The env-parity test builds the tick env from the real `Demo.tick()` Popen. It is non-vacuous: a keyless control
    must differ, and the packet records the reverted-tick proof.
  - The serve child is checked by source text, which is weaker but adequate.
  - The keyless pre-build stores 0 rows and reports `SKIPPED_NO_SERVE_ENV`.
  - The per-version prune test passes.
- **Guard fix.**
  - The `$responseWriter` registration follows the `postgres_event_store` pattern: two exact statement shapes, sole
    ownership of `chain_response`, anti-vacuity per shape, and nothing loosened.
  - The new writer rules are correct and strict: the prune must partition by `code_version`, and any other module
    writing `chain_response` fails.
- **File hygiene.** The `Add-Content` revert is clean.
  - `postgres_thread_store.py` is not in the diff.
  - No changed file has a BOM or mojibake (UTF-8 byte scan).
  - The index EOL is LF for the files checked, and the working-tree CRLF comes from `core.autocrlf`.
- **Owned `link_ref` fix.** It adds literal `link_ref` dicts with kind and view pins, and weakens no assertion.

## R6 E4 check (the packet's text is not yet precise enough; use this)
The deferral to end-game E4 is acceptable. A server-side miss falls back to an uncached compute, never a stale body,
and the root cause is pinned by the L0 env-parity test and the keyless-skip guard.

The E4 run, in the E4 demo tree with `demo_combined serve` (no separate prepare beyond E4's own):
1. Wait for the first loop tick that is **data-bearing**. Its tick JSON must show `prebuild.code == "OK"` and
   `prebuild.states.stored >= 1` (a watermark moved). Record `prebuild.code_version` = X (16 hex) and `prebuild_ms`
   (≤ 50% of `tick_seconds`).
2. After that tick's `performance_migration` line, and before any other HTTP request, `GET` the exact
   `portfolio.week` and `summary.week` queries from `config/chain/prebuilt-routes-v1.json`, then load the Portfolio
   page in the browser. Each must return:
   - 200;
   - `X-AssetOps-Stored: hit`;
   - a server wall time ≤ 1000 ms;
   - for the Portfolio, a body ≤ 100 KB.
3. Server version:
   `SELECT DISTINCT left(code_version,16) FROM chain_response WHERE built_at >= <tick start>` = {X}. A request in
   step 2 that stored a new row under another version fails the check.
4. Run `tools/chain_response_probe.py fresh` against the same DB. It must report all requests equal (Q4 mask), and
   **after H1 is fixed**, the same must still hold after the comparison step.

## Checks run (this review)
- `tools/run-host-tests.ps1` (plan2 python, absolute PYTHONPATH of the worktree, `assetops_test` on 127.0.0.1),
  over these files:
  - `test_ch5c_{batch,env_parity,response_store,w6_guard,watermark}*`;
  - `test_out_b4_route.py`;
  - `test_out_b4_board_postgres.py`.

  Result: **38 passed, 1 skipped** (the L2m clone parity, env unset), 181 s.
- `tools/run-host-tests.ps1` over `test_w303_portfolio_scope_snapshot_postgres.py` and `test_w303_portfolio_api.py`:
  **16 passed**, 760 s. This includes the owned `link_ref` fix and the Q9 count = len(ids) pins.
- `frontend`: `npx.cmd tsc --noEmit` exit 0 (52 s). `npx.cmd vitest run
  src/estate/__tests__/estatePortfolio.test.tsx`: **59/59 passed**. It ran on this machine.
- Guards with `ASSETOPS_GUARD_PYTHON` set to the plan2 python:
  - `tools/check-architecture.ps1 -Python ...`: **passed** (240 s);
  - `tools/check-agent-workflow.ps1`: **passed**.
- `git merge-tree` against CH-9: as in M3.
- **Not run:**
  - the full suite, and any prepare;
  - the polish-clone spot check (stored equals fresh, idle tick), **skipped**: a lane-2 job was running
    (`chain_coherence.py collect` on `assetops_mechanism_test`, PID 15892, CH-9 worktree);
  - the 279-day clone parity, at head;
  - the W6 CLI on a real clone.
- The idle-tick, `fresh` 23/23 and W6-on-clone results are the builder's L3 evidence, which this review did not
  reproduce.

## Residual risk not named in the packet
- H1 and H2 above: the sources not covered by the watermark (files, the wall clock).
- `code_version` omits `host/` and `contracts/`.
- The watermark count grows unbounded and its growth is unmeasured (M2).

## Coordinator verification (merge prep CH5c-R7, 5bd8dbee2) — ACCEPT for merge with the store OFF
- `response_store.enabled()` is off unless `ASSETOPS_RESPONSE_STORE` is on/1/true/yes; product code, `demo_combined` and settle env never set it — only the probe tools (`chain_perf_probe`, `chain_response_probe`) opt in. So H1/H2 cannot reach a client; they are owned by CH-5c2 (§8.6), which turns the store on.
- M3: literal head pin replaced by `test_exactly_one_alembic_head`. L7: per-day loop moved to the test module; 279-day clone parity re-run at final head (3 passed).
- Builder evidence: test_ch5c_* + out_b4_route 48 passed/1 skipped (clone test, run separately); store-off L0 tests 18 passed; guards A, W pass.
- Residual (owned by DD-1b, M2): change-log triggers are live on all inputs even with the store off; their write cost on a data-bearing tick is unmeasured.
