# CH-5c pre-flight (build sheet `AssetOpsV1-plan2/.agent/build-sheet-CH-5c.md`, rulings CH5c-R3)

Branch `task/CH-5c-perf` from main `fd03ae6b0`; worktree `AssetOpsV1-ch5c`. No production code changed. The only
edit is `tools/chain_perf_probe.py`, which now also times the Findings index (the CH-5a2b residual).

Measurement clone `assetops_chainclone_ch5c_test`: create --migrate 4 s; backfill a-d 25 s (b 9, c 3, d threads 6);
settle 96 s (tick COMPLETED in 90 s). All reads ran with `PGOPTIONS=default_transaction_read_only=on`. **The clone
is kept for step 2**: it serves as the A side, the post-build settle and COH, and it is dropped at the end. Scratch
work dir: `scratchpad/ch5c/work` (a copy of `polish_work`).

## P1. Baseline on main fd03ae6b0 (probe, in process; 5 cold children and 5 warm; ms)

| Route | Cold median (min-max) | Warm median (min-max) | Bytes | Budget |
|---|---|---|---|---|
| Kobo board 31 Oct | 4,937 (4,710-6,361) | 3,525 (3,434-3,825) | 18,042 | 1 s / 300 ms / 60 KB |
| Cold board failure night | 2,099 (1,972-2,201) | 925 (899-1,051) | 20,005 | same |
| EV board 27 Oct | 2,493 (2,348-2,612) | 1,179 (1,028-1,379) | 14,710 | same |
| Summary week | 8,962 (8,431-9,439) | 5,219 (4,198-6,509) | 13,964 | 1 s / 300 ms |
| Portfolio week | 6,588 (5,960-6,685) | 5,245 (4,502-5,385) | **287,304** | 1 s / 300 ms / 100 KB |
| Findings week (new) | 2,519 (2,258-2,894) | 1,734 (1,669-1,867) | 24,712 | 1 s / 300 ms |

The machine was noisy: another session was running pytest. The summary and Portfolio are slower than the sheet's
CH-5a1 figures; CH-5a2b added the claims read to them.

**`_window` split (cProfile of one warm request):**
- **Findings week**, 2,222 ms in total:
  - `_window_read`: 7 reads, 1,370 ms (62%), about 196 ms per read.
    - `input_basis` 522 ms. This is CPU, of which `select_cohort` is 398 ms.
    - The rest is SQL plus run detail: `_run_detail` 317 ms over 3 calls.
  - The claims read: 186 ms.
  - The Findings route has **no `perf.route` read scope** (`estate_api.py:46` `serve`), so its memo is not shared
    and the ledger is empty.
- **Portfolio week**, 6,689 ms:
  - `_window_read`: 7 real reads (35 calls, 28 of them memo hits), 1,184 ms (18%).
  - Coverage: `site_coverage` 2,878 ms, of which the `_mini_grid_basis` dispatch days are 2,066 ms.
  - Provenance: `link_rows_on` 1,202 ms. That is 6,748 `_link_row` calls and 20,244 `_commitment` calls, about
    0.78 s of pure hashing (`evidence/adapters/postgres_evidence_ledger.py:1161,1202`).
  - `claim_limit_on`: 810 ms. `select_financial_scope`: 939 ms.
- **Kobo board** (ledger): `assessment._window` 900 ms, `money_head` 1,160 ms, `mini_depth` 658 ms, `action_facts`
  426 ms, `dispatch` 421 ms.
- **R3 pairs:** across the whole collect (85 requests), the `_window_read` arguments repeat in the boards (22 reads
  over 11 distinct keys), in `/estate/chain` (30 over 13) and in the summary (9 over 4). Portfolio has none
  (40 over 40). I will measure the per-request live-vs-read-instant pairs in the R3 L2 test.

**Conclusion.** The window round trips are the main residual on Findings, but only about 20-25% on the Portfolio
and Kobo board. Batching alone cannot bring the Portfolio uncached time to 1.5-2.5 s; the stored responses are the
lever that meets the budgets. See Q1.

## P2. `_configuration` (`postgres_assessment_store.py:292-334`)

Its statements are: 1 foundation query; 1 binding-set query; and 1 binding-revision query **per set**. The set
query uses `_KNOWN` and `_OVERLAPS` on `[lo, hi)`; the revisions are unfiltered by time.

Union-then-filter is sound in principle. Each per-day row set is the union-range set filtered by the same
`_OVERLAPS` predicate. The foundation overlap limits are computed over the filtered, ordered set. Default (as the
sheet says): keep it per day unless the L2 parity test proves equality, then batch it.

## P3. Driver

- The read engines use `postgresql+psycopg` with psycopg **3.3.6** and SQLAlchemy 2.1.4 (`tools/demo_combined.py:260`).
  psycopg2 is not installed.
- psycopg 3 already prepares server-side after **5** executions of the same statement (its default
  `prepare_threshold`). R4 can only lower that threshold.
- `PostgresAssessmentStore` has one engine that serves both reads and writes (`postgres_assessment_store.py:243`).
  See Q6.

## P4. Wall-clock fields (empirical, plus `path:line`)

**Empirical test.** Two full collects of the same clone, 3 minutes apart: 85 requests each, all 200. 31 files
differ, and only in these fields:
- `window.known_at` and `selection_token`, in Portfolio, Findings (all, opportunities, day), Actions and
  action-index (that body has a top-level `known_at`).
- **Boards, summary and the chain bodies are byte-identical.**

**Static sources (each read instant):**
- `estate/adapters/postgres_estate_read.py:92` `now()`;
- `estate/adapters/postgres_evidence_money_read.py:38`;
- `work/adapters/postgres_work_read.py:383`, `postgres_global_read.py:182` and `postgres_domain_action_index.py:193`
  (`clock_timestamp()`);
- `mini_depth/read.py:347,407`;
- `chain/read.py:245` (`datetime.now` when `k` is None);
- `chain/adapters/postgres_chain_inputs.py:151`;
- `chain/adapters/postgres_thread_sources.py:189`;
- `chain/adapters/postgres_event_store.py:137` (Site today);
- `analytics/adapters/postgres_assessment_store.py:916` (`read_at`) and `:961` (transaction time, live vs historical);
- `objectives/adapters/postgres_objective_store.py:163` (`coalesce(k, now())`);
- `financials/adapters/postgres_consequence_store.py:400` (cutoff default).

Each of these is a read cutoff. No rule computes elapsed time against now:
- plan due is measured against the window `to` (`outcomes/plan_due.py:25-31`);
- staleness is data-driven (`estate/coverage.py:120-135`).

See Q4.

## P5. Writes reaching `event_outbox` (`backend/migrations/versions/0044_chain_events.py:34-80` PRODUCERS)

**Covered** (an AFTER INSERT statement trigger, plus a `recompute_job` status UPDATE trigger at `:143-147`):

| Table | Covers |
|---|---|
| accepted_evidence | readings |
| analytic_run_selection | assessment |
| mini_depth_selection | assessment |
| recompute_job | insert, and status update |
| financial_assumption_revision | **price** |
| foundation_revision | **Foundation** |
| finding_revision | |
| mini_opportunity_revision | |
| action_event | **Action** |
| domain_action | **work intent** |
| verification_outcome | **verification** |
| outcome_objective_revision | **objective** |

**Not covered.** These were found by a SQL listener over all 85 collected requests (tables read per route). The
pre-built routes read them, and they produce no outbox event:
- **configuration:** `signal_binding_set_revision` (UPDATEd: `UPDATE signal_binding_set_revision` exists),
  `signal_binding_revision`, `source_clock_attestation`;
- **price assignment:** `financial_assumption_assignment` (UPDATEd);
- **money:** `financial_consequence_*` (revision, assessment/assumption/power links, work, work_attempt),
  `cold_consequence_*`, `ev_consequence_*`, `trial_cost_comparison_revision`;
- **domain records:** `cold_episode`, `cold_episode_revision`, `ev_session*`, `ev_meter_interval`;
- **work:** `work_case`, `work_case_revision`, `work_case_*_link`, `work_case_evidence`, `work_event`,
  `maintenance_plan`, `maintenance_record`, `maintenance_work_request`, `domain_action_case_link`,
  `domain_action_intent`, `action`, `action_basis_*`, `action_policy_change`, `chain_action`, `chain_action_thread`;
- **finding/thread side:** `finding`, `finding_match_pass`, `finding_merge`, `finding_thread`,
  `finding_thread_occurrence`, `finding_revision_*` links, `mini_opportunity`, `mini_opportunity_selection`,
  `mini_depth_revision*`;
- **run side:** `analytic_run*`, `assessment_revision`;
- **ingestion and publication:** `ingestion_batch`, `ingestion_disposition`, `evidence_publication`,
  `batch_publication_link`;
- **verification:** `verification_plan`, `verification_metric`;
- **Site and setup:** `site`, `asset`, `site_cutover_basis`, `site_import`, `tenant`;
- **settled flags:** `event_consumption`.

Many of these are written in the same transaction as a covered table, but I have not proved that for each one.
See Q3.

## P6. Portfolio bytes (week, page 1: 287,293 B)

| Field | Bytes | Note |
|---|---|---|
| `scope_disclosure` | 237,864 | |
| `scope_disclosure.sites[]` (3) | 22.8 K, 18.5 K, 196.4 K | the large one is Cold |
| `scope_disclosure.sites[].source_provenance` | 154 K in total | Cold: `evidence_ids` 64.8 K, `reasons[].accepted_evidence_ids` 65.0 K |
| `scope_disclosure.sites[].selected_revision_ids` | 81.6 K in total | |
| `rows` (5) | 24.6 K | `source_provenance` 12.4 K |
| `selected_lines` | 8.7 K | |
| `objectives` | 4.7 K | |
| the rest | under 2.4 K each | |

**Consumers:**
- `frontend/src/estate/EstatePortfolio.tsx:586` reads `scope_disclosure.sites[].source_provenance` **only as
  `=== null`**. Its ids and reasons are never rendered.
- `selected_revision_ids` **is rendered**, inside a technical disclosure (`EstatePortfolio.tsx:562-571`), so it stays.
- The footer `source_provenance` is rendered (`:633-650`) and stays.

**Trim candidate:** `scope_disclosure.sites[].source_provenance` is reduced to the fields that something consumes.
The estimated result is about 135 KB. That is still over 100 KB, because the remainder is rendered content.
Backend contract tests and the frontend types are checked in u3. See Q9.

## P7. Hook point and headroom

- **Per Site:** `chain_threads` (`scheduling/tick.py:470-475`, limit `chain_seconds` 60), then the consequence
  drains, then `chain_snapshots` (`:503-513`, limit `chain_snapshot_seconds` 60), then `release_site`.
- **Lease:** `site_lease_seconds` (`:113-116`) sums the stage limits plus 60.
- **Tick time:** the settle tick took 90 s for 3 Sites.
- **Pre-build load:** the estate routes span every Site, so the pre-build belongs after the Site loop, not inside
  one Site. The pre-built set, from the sheet and `days.json`, is: 14 boards, the summary, 3 Portfolio windows and
  the Findings story window. That is about 19 routes, roughly 45-60 s uncached at today's cold timings, which is
  about a 60 s stage bound. See Q8.

## Questions (each with a proposed default)

**Q1 (P1).** The window residual is 62% of Findings but only about 18-25% of the Portfolio and Kobo board. The rest
is provenance `_commitment` hashing (0.78 s), coverage and the money reads.
- Default: build R1 as ruled. Do not optimise provenance, coverage or money (out of scope). Report the uncached
  Portfolio honestly (about 4-5 s expected, not 1.5-2.5 s). Stored or pre-built responses meet EX-3 per R9.

**Q2.** The migration is `0047_chain_response`, built on `down_revision = "0044_chain_events"` (today's head).
CH-9's `0046` also branches from 0044.
- Default: whichever slice merges second re-points its `down_revision` (one line). CH-5c touches no CH-9 file
  (`mini_depth/*`, `mini_decisions/*`, `chain/measures*`, `chain/vocabulary.py`, `site_outcomes/mini.py`).
  It overlaps CH-9 only through the tick module and the probe, if CH-9 edits them.

**Q3 (P5, R7).** Many input tables produce no outbox event, and three are UPDATEd in place.
- Default:
  - Add a declared list `config/chain/watermark-inputs-v1.json` of the uncovered tables.
  - The watermark statement adds, for each listed table (scoped by tenant, and by Site where the column exists),
    `count(*)` and `max(xmin::text::bigint)`. Any INSERT, UPDATE or DELETE moves one of the two.
  - A guard test runs the pre-built routes under the SQL listener and fails if a table read is neither an outbox
    producer, nor a direct watermark term, nor in that list (proved non-vacuous).
  - The cost of the watermark statement is reported. If it exceeds about 50 ms on the clone, ask before going on.

**Q4 (P4, R6).** Live bodies differ from a fresh compute only in `window.known_at` / `known_at` and
`selection_token` (the build instant, and the token bound to it).
- Default:
  - A stored live body keeps the build-instant values. That is truthful while the watermark is unchanged, and the
    token's later pages read at that instant, so they stay consistent.
  - "Byte-equal to a fresh compute" is asserted byte for byte after replacing exactly these fields. Historical
    (`known_at` given) bodies are asserted byte for byte with no replacement.
  - The boards and summary carry no such field and are byte for byte as they stand.

**Q5 (R6).** `code_version` is not defined.
- Default: a sha256, computed once per process, over the sorted (path, bytes) of `backend/assetops_backend/**/*.py`,
  `config/chain/**` and the `config` files the composers read. The R7 "policy versions" are then covered by
  `code_version`, since they live in those config files.

**Q6 (R4).** The assessment store uses one engine for reads and writes.
- Default:
  - Add a second, read-only engine inside `PostgresAssessmentStore`, used only by `_snapshot`, with
    `connect_args={"prepare_threshold": 1}`. Apply the same setting to the chain read engine.
  - Measure before and after. If the gain is under 5%, drop it and report.

**Q7.** Findings (`estate_api.py:46`) and `/estate/chain` run without a `perf.route` read scope.
- Default: wrap the Findings index in `perf.route`, as the board, summary and Portfolio are. This gives it the
  batched prefetch and a ledger, and it adds no semantics.

**Q8 (R6, P7).** Where and how the pre-build runs.
- Default:
  - A tick-level stage `chain_prebuild` runs after the Site loop, through `runner.run`.
  - It has its own limit `prebuild_seconds = 120`, below the server statement-timeout rule. It is not a per-Site
    stage: no stage CHECK change, and no lease change.
  - It runs only when at least one Site's chain stages returned OK in this tick, or when no stored row matches the
    current watermark.
  - It is deadline-bounded. Routes left unbuilt are reported and built on first request.

**Q9 (R8).** Trimming `scope_disclosure.sites[].source_provenance` brings the Portfolio to about 135 KB, not 100 KB.
- Default:
  - Replace it with the fields that something consumes: a `null` check today, so keep `classification`, `state`,
    `source_ids` and `basis_sha256`, and drop `evidence_ids` and `reasons`. The frontend type changes to match.
  - Stop at the floor and report it, because the remaining bytes (`selected_revision_ids`, the rows) are rendered.

**Q10.** GETs become writers: the store insert runs on a request.
- Default:
  - The insert runs in its own short write transaction after the compute.
  - On a read-only database or an insert failure, serve the computed body, log it, and never fail the request.
  - So a `PGOPTIONS` read-only collect still works, as all misses.

**Q11 (paging).** Default: the cursor and page parameters are part of `request_key`, and each page is stored
separately. Only page 1 is pre-built.
