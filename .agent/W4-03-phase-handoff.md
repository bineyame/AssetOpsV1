# W4-03 phase handoff

Branch `task/W4-03-mini-decisions-work` (from `main`), worktree `AssetOpsV1-review5`.

## Unit 1 (landed, commit c3713564)

Migration `0030_w4_mini_decisions` (parent `0029_w4_mini_depth`), `mini_decisions/store.py` insert
skeletons, Rule-8 registration with per-table probes, and S18 current-head updates.

File anchors for later units:
- `backend/migrations/versions/0030_w4_mini_decisions.py`: `TABLES` (closure-1 lock/drop order),
  `SCHEMA`, `REFUSE_IF_USED`, `DROP`. Stage CHECK now `IDLE,S3,MINI,OPPORTUNITY,S4,CONSEQUENCE`.
- `backend/assetops_backend/mini_decisions/store.py`: `PostgresMiniDecisionStore.transaction()`, one
  `insert_<table>` per table (literal `"INSERT INTO <table> (` once each, which the unseen probes need),
  `_check_job` (tenant/Site/domain), alternative finding-pair check, selection revision/opportunity check.
  Constants `OPPORTUNITY_JOB_DOMAIN`, `OPPORTUNITY_MODEL_VERSION`.
- Rule 8: `$decisionWriter`/`$decisionTables` in `tools/checks/configuration-persistence.ps1`; probes
  `decision <table> ...`, `decision truncate` and `controls decision <table> insert` in `tools/writer_guard_probes.py`.
  The worker's `recompute_job` registration is unit 4 (S2).
- Tests: `backend/tests/test_w403_migration_postgres.py` (9 collected): exact catalog arrays, empty
  downgrade/upgrade round trip, lock order and lock-before-count, job-only refusal (PENDING/DONE/FAILED),
  OPPORTUNITY-stage refusal, decision-history refusal, store service checks and append-only.

## Readings taken (not rulings; reviewer may overturn)

1. The spec says "bounded" without numbers. Bounds follow merged W4-01 `0027`: actor_id and create_actor_id
   1-128, authorization_basis 1-500 and attestation 1-1000 non-blank characters; explanation and evidence_summary
   1-2000; reason, missing_evidence_reason and correction_reason 1-500.
2. CHECK names that the spec does not name: `mini_scenario_revision_chain_check` (original revision/supersedes
   CHECK), `mini_opportunity_window_check`, `mini_decision_work_link_target_check`, and
   `<table>_<column>_check` for the rest.
3. `model_version='mini-opportunity/1'` is a store constant, not a DB CHECK. The original 0..4-day window
   CHECK is kept verbatim.
4. `_check_job` validates tenant, Site and domain only. The study-window comparison needs the closure-2
   window key, so it waits for unit 4.
5. Downgrade locks `recompute_job` and `schedule_site_head` EXCLUSIVE after the ten tables and before
   counting. Refusal order: decision history, then opportunity jobs, then the active stage.
6. S18 in `test_w402_migration_postgres.py`: `HEAD` now means the current head (0030), and the new
   `MIGRATION` keeps the 0029 parent assertion. `SITE_STAGES_AFTER` includes OPPORTUNITY at the current head.
   `mini_depth_probe.MINI_HEAD` is the current head, and the 0029 refusal text is unchanged.

## Checks

All runs used private DB `w403a_test` (dropped afterwards). No full suite was run.
- `test_w403_migration_postgres.py` + `test_w402_migration_postgres.py` + `test_w401_migration_postgres.py`:
  25 passed (122 s).
- The other 12 S18 head files (s1, s2, s405, s4 x2, w200, w201, w203, w204, w205a, w206, w207): 168 passed (856 s).
- Collection: `pytest tests --collect-only` collected 3488 tests; w403 file collected 9.
- `tools/writer_guard_probes.py --seam` over the 61 new decision probes: 51 CAUGHT and 10 ALLOWED; the tree
  was restored.
- `check-all.ps1`: 9/11 passed. The two missing-claim guards failed only because the fresh worktree had no
  `frontend/node_modules` (MODULE_NOT_FOUND). After `npm ci`, both passed when rerun alone (scan passed;
  fixtures 24 passed, 0 failed).
- Open question for unit 4: PR-1 in `.agent/W4-03-pending-rulings.md` (OPPORTUNITY counter columns).

## Unit 2a (landed, commit 011961ec)

Pure scenario rules; no database. Spec: original Scenario paragraph, closure 1 Q7-Q11, closure 2 N1, closure 4 S8/S16.
- `backend/assetops_backend/mini_decisions/model.py`: `DecisionRefused(code)` with the W4-03 error table plus closure
  codes (`DECISION_USER_AUTH_REQUIRED`, `DECISION_ATTESTATION_INVALID`, `DECISION_CORRECTION_CONFLICT`,
  `DECISION_LINK_SCOPE_INVALID`, `DECISION_COUNTEREVIDENCE_INVALID`, `INVALID_LIMIT`); `invalid()`.
- `backend/assetops_backend/mini_decisions/scenario_rules.py`: `assumptions(kind, items)` (closed keys, canonical
  sorted list, decimal strings), `tariff_currency(unit)` (`<ISO 4217>/kWh`, list imported from
  `financials/assumptions.py:ISO_4217`), `physical_decimal`/`physical_range`/`decimal_text` (S8),
  `DayRow`, `calculate(kind, items, days)` -> `{state,energy_kwh,gross_sales,reason}`, `eligible_days(days)`.
- `backend/tests/test_w403_scenario_rules.py`: 26 passed (USD/kWh accepted, `ISO4217/kWh` refused, $2.50 pure
  vector, 4/5 EXCLUDED-day vector, 18/18.0/fractional/1e-7 serialization, withheld states).

Readings (2a; reviewer may overturn):
7. Authored decimals must be JSON strings in plain base-10 form; a JSON number or exponent is 422.
8. `OTHER`: `declared_value` carries a signed decimal and `declared_unit` carries the 1-32 character text, both with
   `unit: null`.
9. Assumption `source` is 1-500 trimmed characters.
10. Calculation reasons: `NOT_PRODUCTIVE_LOAD`, `NO_PINNED_SELECTION` (NO_CALCULATION); `INCOMPLETE_STUDY` (a LIMITED,
    CONFLICT or bound-less pinned day), `NO_ELIGIBLE_DAY`, `HEADROOM_BELOW_LOAD` (WITHHELD); null when computed.
    Energy and gross are per eligible one-hour window, not five-day totals.

## Unit 2b (not started: blocked on PR-2)

Stopped before the scenario store/POST: `narrative` is required by the command but 0030 has no column for it. See
PR-2 in `.agent/W4-03-pending-rulings.md` (plus three readings to confirm). Survey already done for 2b; anchors:
- S9 basis reader goes on `mini_depth/read.py:MiniDepthRead` beside `_hour` (lines ~408-430), reusing `_HEAD`,
  `_JOBS`, `_cutoff_sha`, `mini_blocks`, `aggregate_state/job`, `inputs.local_noon`; stored ELIGIBLE bound is
  `result["hour"]["opportunity_kwh"]`, decision `result["hour"]["decision"]`. `_JOBS` returns statuses only, so
  pending job IDs for the selection token need an ID-returning variant inside read.py.
- Gate/principal pattern: `work_api.py:build_work_router` (`read_scope`/`open_scope`); actor/attestation:
  `work/model.py:actor_shape`, `authorize`, `ATTESTATION`, `canonical_json`, `command_sha256`, `idempotency_key`,
  `closed`, `uuid_text` (N6: import, do not copy). Registry/MINIGRID: `mini_depth_api.py:site_of`.
- Mount: `main.py` beside `build_mini_depth_router` (~line 451); `create_app` params end at line 198.

## Checks (2a)
- `pytest tests/test_w403_scenario_rules.py`: 26 passed. No database used; `w403b_test` not created.
- `check-all.ps1` at 011961ec: all 11 guards passed.


## u1/u2 0030 amendment (commit c351eed1)

- `0030`: `narrative text NOT NULL` + `mini_scenario_revision_narrative_check` beside name/kind; `SCHEMA` ends with
  the three `schedule_site_head` counters; `DROP` drops them right after restoring the 0029 stage CHECK.
- `store.py:_INSERT_SCENARIO_REVISION` inserts `narrative`. Test helpers `scenario_revision`, `site_head`,
  `head_counters`, constants `COUNTERS`, `NARRATIVE_CHECK`, `HEAD_CHECKS = 2` (schedule_site_head CHECKs, unchanged).
- New tests: `test_counters_zero_on_existing_site_head_and_round_trip`, `test_narrative_trimmed_length_bounds`;
  history/job-only/active-stage refusals now assert narrative and counter values survive.
- Checks (private `w403c_test`, dropped): w403 migration 11 collected, 10 passed, 1 failed - only
  `len(CHECKS) == 48` (catalog has 45, matching the exact name array). w402+w401 migration: 16 passed.
- **Blocked: PR-3** in `.agent/W4-03-pending-rulings.md` (CHECK count 45 vs ruled 48). Unit 2b not started.

PR-3 resolved by u2b (45 is correct; commit d59fc8f1 changes only the test assertion).

## Unit 2b (landed; commit after d59fc8f1)

Spec: API/error table; closure 1 Q1-Q3/Q12-Q16; closure 2 Q1; closure 4 B1/B2/S5/S9/S10/S15/S20/N5-N8; u2; u2b.
- `mini_depth/read.py`: S9 `MiniDepthRead.read_selected_renewable_basis(c, tenant_id, site_id, days, known,
  historical)` (per-day seq/revision/decision/`opportunity_kwh`/digest/accepted IDs/state/job IDs, aggregate
  currentness, `pending_job_ids`, `pending_evidence_ids`, three blocks), `provenance_blocks(...)`, module function
  `renewable_revisions(c, t, s, ids)`. `_JOBS` now selects `j.id, j.status`; `_Hour.job_ids`. Correction to the 2b
  survey anchor: the one-hour bound is `result["rows"][0]["opportunity_kwh"]`, not `result["hour"]`.
- `mini_decisions/model.py`: `GRANT_PREFIX`, `DecisionPrincipal(kind,id,tenant_id,site_id,grant)`.
- `mini_decisions/store.py`: `snapshot()` (read-only RR), `db_now`, `scenario_by_create_key`, `lock_scenario`
  (FOR UPDATE), `scenario_revisions`, `scenario_heads` (head per root at cutoff; creation-time window).
- `mini_decisions/scenarios.py`: `ScenarioService.create/correct/list`; `admit`, `authorize` (W4-01 `ATTESTATION`),
  `parse_command`, `parse_pins`, `parse_list`, cursor encode/decode, token, per-row read gate.
- `mini_decisions_api.py`: `build_mini_decisions_router` (GET/POST scenarios, POST revisions), `deny_decision_writes`,
  `no_decision_principal`, `DecisionPrincipalResolver`. `main.py:create_app` gains `mini_decision_command_access`
  and `mini_decision_principal`; router mounted after the mini-depth router.
- Tests: `backend/tests/test_w403_scenarios_postgres.py` (5): create/correct/retry/409/conflict/404/422 and fresh-app
  persisted read + historical narrative + default-composition 403; pin scope/basis/shape vectors (foreign, other
  domain, seq mismatch, same-Site non-head, 0/5 pins, duplicate/gap/6, USER/attestation/basis/narrative bounds);
  published (AUTHORED_DEMONSTRATION) pages/provenance union/own-row UNKNOWN withholding/stale-current vs historical;
  router refusal order 401/403/404/503 and non-MINIGRID; principal scope before body.
- Readings taken: PR-4 in `.agent/W4-03-pending-rulings.md` (provisional, non-blocking).
- Open for later units: S9's "stale digest and pending newer evidence through both W4-02 and W4-03 reads at the
  same cutoff" vector is not yet written (the code path is the shared `_hour`); the walkthrough tool (closure 2 Q1,
  unit 9a) and N7 `currentness.windows[]` translation (unit 5) are not in 2b. `ScenarioService` has a
  `test_read_clock_override` for lists only.

## Checks (2b)
- Private DB `w403d_test` (dropped afterwards). `test_w403_migration_postgres.py`: 11 passed (66 s) after the u2b fix.
- `test_w403_scenarios_postgres.py` + `test_w402_reads_postgres.py` + `test_w402_reads.py` +
  `test_w403_scenario_rules.py`: 61 passed (1020 s). No full suite run.
- `check-all.ps1`: all 11 guards passed.

u2c merged from main (3476b97b) and applied as commit 17d91aa1 (fix to unit 2b): decimal-string energy/gross,
empty-union currentness UNKNOWN/HISTORICAL, no UNKNOWN->SELECTION_CHANGED mapping, S9 W4-02/W4-03 parity test
(`test_u2c_currentness_reselection_and_s9_parity`), rows[0] fractional bound test, PR-4.1/4.2 route tests. PR-4 resolved.

## Unit 3 (landed; commit after 17d91aa1)

Spec: original Alternative paragraph/panel ledger; closure 1 Q1-Q3, Q12-Q16; closure 4 B1/S17/S20/N1/N2.
- `mini_decisions/alternatives.py`: `AlternativeService.create/list`, `parse_command`, `rules_out` (N2), `RANKS`,
  constants; reuses `admit`/`authorize`/`_shape`/`encode_cursor` from `scenarios.py`. Constructor-only test clocks
  `test_db_clock_override` (command instant, bound to `created_at`) and `test_read_clock_override`.
- `store.py`: `finding_root` (`FOR NO KEY UPDATE` on commands), `finding_revisions`, `alternative_revisions` (with
  sorted `cited`), `accepted_intervals` (point evidence `+1us`); `_INSERT_ALTERNATIVE_REVISION` now writes
  `created_at = COALESCE(:created_at, clock_timestamp())`.
- `scenarios.decode_cursor` accepts null `from`/`to` together (alternatives cursor).
- `mini_decisions_api.py`: `GET/POST /api/sites/{code}/findings/{finding_id}/alternatives`; `command()` takes the
  service; `build_mini_decisions_router(..., alternatives=)`. `main.py` mounts `AlternativeService`.
- Tests: `backend/tests/test_w403_alternative_postgres.py` (4): F02 R1 -> R2 lifecycle (create/retry/409, RULED_OUT
  outside-only and absence refused, refusal vectors write nothing, R1 HISTORICAL, R2 NEEDS_REVIEW, carry-forward
  CURRENT, both cutoffs, S20 basis digests incl. no-citation case, pages/cursor/token, W1 Finding read unchanged before
  and after writes); N1 cold-domain and non-dispatch replica copies (GET 404, POST 422); N2 interval vectors; route
  refusal order plus `create_app` mount.
- Readings: PR-5 in `.agent/W4-03-pending-rulings.md` (non-blocking).

## Checks (u2c + 3)
- Private DB `w403e_test` (dropped afterwards). `test_w403_alternative_postgres.py` + `test_w403_migration_postgres.py`
  + `test_s4_finding_read_postgres.py` (W1 Finding regression) + `test_w403_scenarios_postgres.py` +
  `test_w403_scenario_rules.py`: 53 passed (891 s). No full suite run.
- `check-all.ps1`: all 11 guards passed.

Next: unit 4.

## u3 applied (commit cb9211fe)

All eight u3 readings matched the `ff79469b` code; no service change. `test_w403_alternative_postgres.py` gains the
named vectors: retry after R2, second version 1 on R2, wrong-key and wrong-path predecessor, blank/501 missing reason,
foreign-Site citation (replica copy), fresh-service stable row IDs, R2 requested before its cutoff, wrong-path revision
POST 422 / GET 404, and `test_one_command_instant_governs_basis_citation_and_recorded_at` (clock just before a citation's
`received_at`, across R2's `created_at`, exact `recorded_at`). 5 passed (49 s). PR-5 marked resolved.

## Unit 4 (PARTIAL; commit 17b77a6a) - resume here

Landed: B3 literals add `'mini_opportunity'` at `postgres_finding_store.py:115` and `postgres_evidence_ledger.py:814`;
`PostgresAssessmentStore.lease_job` refuses `mini_opportunity` (beside the `MINI_JOB_DOMAINS` refusal, ~line 336).
W4-02 `test_w402_mini_lease_postgres.py` + `test_w402_cold_enqueue_gate_postgres.py`: 4 passed. Stopped for context budget.

Still to build (read: u3 "Unit 4 dry-read", u1 PR-1, closure 2 Q4 SQL, closure 4 B3/S1-S7/S19):
- `postgres_assessment_store.py`: `enqueue_opportunity_job` (advisory lock, PENDING FOR UPDATE, coalesce UPDATE or INSERT;
  `test_clock_override` at this seam), `lease_opportunity_job`, `settle_opportunity_job`, `fail_opportunity_job`, each with
  literal `domain='mini_opportunity'`; pattern: `lease_mini_job`/`settle_mini_job`/`fail_mini_job` (~lines 367-430).
- Rule 8: allow the coalescing `UPDATE recompute_job SET available_at = greatest(...)` only there
  (`tools/checks/configuration-persistence.ps1`), with positive/negative probes in `tools/writer_guard_probes.py`.
- `mini_decisions/worker.py`: scan (head query, `:at - interval '5 days'`, S5 physical identity incl. null missing days),
  `reconcile`, lease loop, projection (S5 `input_sha256`, reuse existing revision, selection only on change), job
  window/five-noon validation before inserts; no `recompute_job` DML in the worker.
- Scheduling: `record_opportunity` + three `_SITE_HEAD` columns (pattern `record_mini`), OPPORTUNITY after MINI in
  `ScheduleTick._site`, stages, limits, lease budget, `TickReport`; Site selection for PENDING/LEASED opportunity jobs.
- Tests: `test_w403_opportunity_job_isolation_postgres.py` (B3) plus the u3 unit-4 list (token loss, atomic counters,
  opportunity-only Site, failed stage, resume, unchanged reselection, late evidence, missing day, retention edge,
  historical reconcile, window mismatch, coalesced scan, interrupted lease, exact five-day selection).

## Checks (u3 + unit 4 partial)
- Private DB `w403f_test` (dropped afterwards). No full suite run.
- `check-all.ps1` at 17b77a6a: all 11 guards passed.

Next: unit 4 (resume the remainder above), then unit 5.

## Unit 4 resumed (commits afd15193, 24e460d3) - BLOCKED on PR-6

(a) landed `afd15193`: `postgres_assessment_store.py` `enqueue_opportunity_job` (Q4 advisory lock, PENDING FOR UPDATE,
exact coalesce UPDATE or INSERT; `self.test_clock_override`), `lease_/settle_/fail_opportunity_job`,
`live_opportunity_jobs` (PENDING/LEASED). Rule 8: `$opportunityCoalesce` exact-text allowance + vacuity check in
`configuration-persistence.ps1`; probes `opportunity coalesce {other domain,other status,widened,plain set,foreign
writer,unseen}` all CAUGHT, `controls opportunity coalesce` ALLOWED.
(b, partial) landed `24e460d3`: `mini_decisions/projection.py` (study window/days, `DayHead`, S5 `input_sha256`,
`day_heads`), `mini_decisions/worker.py` `MiniOpportunityWorker.enqueue_from_selections(tenant, site)` and
`reconcile(code, from, to)`; SQL readers in `mini_decisions/store.py` (`renewable_scan_heads`, `renewable_noon_heads`,
`latest_opportunity_sha`, `sites_by_code`; only store.py may import the driver). Test
`test_w403_opportunity_scan_postgres.py`: 3 passed (hash vectors, historical reconcile + coalesce, retention edge +
missing day).

Remaining (after PR-6): worker lease loop + projection (validate job window/five noons before inserts; reuse revision
on equal hash; selection only on head change; settle in one txn), `run_pending`/CLI; (c) tick stage +
`record_opportunity`; (d) B3 isolation test + the u3 unit-4 list. Private DB `w403g_test` dropped.

## Unit 4 complete (commits c4180e15, de4301f2, 791e36c2 + run-pending fix)

PR-6 resolved by u4. (b2) `mini_decisions/projection.py`: `frozen_result(days, classification)` (u4 status precedence,
weakest-eligible-hour `headroom_kw`, ordered limitations), `day_row` (copies the selected revision's single `rows[0]`;
integrity mismatch -> `ProjectionIntegrityError`, never a missing day), `selected_hours`; `DayHead` carries non-hashed
integrity fields. `worker.py`: `MiniOpportunityWorker(jobs, store, reader)`, `run_once`/`run_pending(scan=True)` (scan
first, then lease), `_project` (job window = exact Site-local midnights, study advisory lock, reuse revision on equal
`input_sha256`, selection only when the head revision changes, evidence links = union of selected accepted IDs, settle on
the same txn; any error -> `fail_opportunity_job`), `build_worker`, CLI. Provenance class = `MiniDepthRead.provenance_blocks`
over the pinned revisions/accepted IDs (`selected_source_provenance.classification`). `store.py`: `_check_job(study_window=)`,
`lock_study`, `site_timezone`, `opportunity_root`, `opportunity_state`; `renewable_noon_heads` adds selection/revision windows
and result. (c) `scheduling`: OPPORTUNITY stage after MINI (`stages.opportunity`, `OPPORTUNITY_JOB_LEASE_SECONDS`),
`TickLimits.opportunity_jobs_per_site/opportunity_seconds` (Site lease now 600 s), `record_opportunity` (token-scoped, all
three), discover/`select_sites` with `live_opportunity_jobs` (FAILED diagnostic); Rule 8 schedule allowlist gains the three
counters (proved non-vacuous: removing `opportunity_failed` fails the architecture check). W4-02 stage tests updated for the
new stage order and 600 s lease.
Readings (reviewer may overturn): `producer_id='mini-opportunity/1'` (closure 1 Q1-Q3); a missing day's `selected_hours`
keeps `window_from/to` with null seq/at/revision and `evidence_ids: []`; a day row's cited IDs must be a subset of the
revision's accepted set; `deferred` = this Site's PENDING/LEASED opportunity jobs after the loop.
Tests: `test_w403_opportunity_result.py` (18, pure u4 vectors), `test_w403_opportunity_worker_postgres.py` (5),
`test_w403_opportunity_scan_postgres.py` (+concurrent coalesce), `test_w403_opportunity_stage.py` (pure, 8),
`test_w403_opportunity_job_isolation_postgres.py` (4: B3 fences, token/atomic counters, opportunity-only Site + resume,
unchanged-fence SKIPPED with an opportunity job settled). Left for unit 5: the u4 read-time tests (pending/stale
currentness on a stored SUPPORTED revision, no positive chip) and the opportunity page mapping.

## Checks (unit 4)
- Private DB `w403h_test` (dropped afterwards). No full suite run.
- New files: result 18 + stage 8 passed (pure); worker 5, isolation 4, scan +1 passed (Postgres).
- Adjacent: `test_w402_mini_stage_postgres` + `test_s4_schedule_tick_postgres` + w403 scan + worker + `test_w402_mini_lease_postgres`
  + `test_w403_migration_postgres`: 33 passed (1454 s). `test_w402_mini_stage.py` (updated): passed.
- `check-all.ps1`: all 11 guards passed (after naming run-pending from the method, as W4-02 does).

Next: unit 5

## u4b tests (commit ba492755)

`test_w403_opportunity_worker_postgres.py::test_exact_five_day_selection_and_unchanged_reselection` re-reads the one
revision after the unchanged rerun and asserts `producer_id`/`model_version`; `test_w403_opportunity_stage.py` asserts
the literal `site_lease_seconds == 600` and adds `test_run_pending_cli_parses_limit_and_calls_the_worker` (stub
`build_worker`; `main(['run-pending','--limit','1'])` -> `run_pending(1)`, then `store.dispose()`). Stage 8 + worker 1
passed (private `w403i_test`, dropped).

## Unit 5 (landed; PR-7 resolved by u5)

Opportunity list/detail reads and the authored opportunity-scenario association (u5 unit 5 rulings 1-7 + command).
File anchors for later units:
- `backend/assetops_backend/mini_decisions/opportunities.py`: `OpportunityService.list/detail/link_scenario`,
  `_study` (one study at the cutoff: head = greatest visible selection whose pins satisfy the cutoff; currentness
  precedence; read-time codes; compatible-link scenario/load/money; history; scenario_links; token row), `_compatible`,
  `parse_opportunity_list`, `decode_cursor` (`after=[first_day,id]`), `opportunity_code`, `unsupported_detail`.
- `store.py` unit-5 reads: `opportunity_roots`, `opportunity_selections`, `live_opportunity_jobs_at`,
  `opportunity_scenario_links`, `opportunity_work_kinds`, `scenario_head_at`, `lock_opportunity`, `scenario_exists`,
  `opportunity_link_by_key`.
- Router `mini_decisions_api.py`: `GET /api/sites/{code}/opportunities`, `GET .../opportunities/{id}`, `POST
  .../opportunities/{id}/scenario-links`; params `opportunities=`, `gate=` (default `closed_gate`),
  `gate_unavailable=`; `physical()` gate after scope/role. `main.py` passes `performance_gate` and
  `finding_store_unavailable()` (the driver-import guard forbids sqlalchemy in the router).
- Unit 7 consumes `currentness`, `status`, `opportunity.eligible_days` and `selected_source_provenance` for the green
  display (helper `positive()` in the read test states the u5 ruling 1 inputs).

Readings taken (not rulings; reviewer may overturn):
1. Non-MINIGRID detail returns a 200 `mini-opportunity-detail-1` UNKNOWN envelope (`opportunity:null`, empty history/
   links, `SITE_ROLE_UNSUPPORTED`), mirroring the list envelope.
2. `SOURCE_STALE` is appended whenever currentness is `STALE_SOURCE`, so a changed head alone yields
   `SELECTION_CHANGED, SOURCE_STALE`; `SELECTION_CHANGED` is appended whenever a pin's revision/accepted set differs,
   even under `PENDING_RECOMPUTE`.
3. "Overlapping" opportunity jobs are literal window overlap with the study window (an adjacent study's job counts);
   no clearing by a later opportunity selection (u5 omits the W4-02 clearing clause).
4. `gross_sales_scenario` from a compatible link is also withheld (null) unless currentness is CURRENT/HISTORICAL and
   the selected class is not MIXED/UNKNOWN (closure 1 Q7-Q11 read gate, same as the scenario row);
   `proposed_load_kw`/`scenario_id` still show.
5. Body `opportunity_id` differing from the path is 422 `DECISION_INPUT_INVALID` (shape), before the store.
6. Detail has no `window`/`known_at` key (u5 ruling 5 lists none); the cutoff is in `links.renewable`.
7. A closed gate answers `{"code":"PERFORMANCE_CUTOVER_CLOSED","message":<reason>}` (+ `rows`/`total_count` null on the
   list), not W1's extra `read` key.
8. List page two without explicit `known_at` uses the cursor's cutoff but `historical=False`, as the scenario list does.
9. Job status is not versioned: a replay at an earlier cutoff after a job settled reads it as settled (same as W4-02).

Tests: `test_w403_opportunity_read_postgres.py` (9: the eight u5-named tests plus the u4b vector
`test_stored_supported_result_unchanged_through_s9_pending_and_stale_reads`), `test_w403_opportunity_links_postgres.py`
(1: `test_association_retry_scope_and_latest_compatible_head`).

## Checks (unit 5)
- Private DB `w403j_test` (dropped afterwards). No full suite run.
- New files: read 9 + links 1 passed (heavy set 780 s; the u4b vector re-run after a test-expectation fix, 2 passed).
  Scenario router regressions (`router`, `principal`, `u2c_non`): passed.
- `check-all.ps1`: all 11 guards passed (after removing a sqlalchemy import from the router).

Next: unit 6

## u5b tests (commit 4a3f7bda)

All nine u5b items plus the u4b vector are test extensions; no service change was needed (all passed first run).
`test_w403_opportunity_read_postgres.py`: `UNSUPPORTED_DETAIL` literal (item 1, cold client with closed gate, failing
store and `not-a-uuid`); exact 409 dicts and composed `permits_performance_cutover` -> `FindingStoreUnavailable` -> 503
(item 7); exact code arrays with a PENDING job (item 2); touching/adjacent FAILED jobs, later selection keeps pending,
fixed-cutoff replay before/after settle (items 3, 9); money gate current/historical/pending/stale/MIXED/UNKNOWN/None via
`mg_published` + monkeypatched `provenance_blocks` (item 4; the 7 Oct `_reconcile` moved before the second link);
detail key set and exact renewable link (item 6); cursor walk CURRENT then explicit-past HISTORICAL (item 8, uses
`_ingest`). `test_w403_opportunity_links_postgres.py`: foreign path + own body ID -> 422, no insert (item 5).
Readings: item 4 MIXED/UNKNOWN is driven by monkeypatching the reader's classification (no fixture yields MIXED);
item 1 "empty UNKNOWN source provenance" = the existing `EMPTY_CITATION_SET` block.

## Unit 6a (landed; commit after 4a3f7bda) - 6b BLOCKED on PR-8

- `frontend/src/sites/miniDecisionsClient.ts`: `createMiniDecisionsClient().getScenarios(code, scope)`,
  `readDecision`, `scenarioScopeSearch`, `microsecondBefore`.
- `frontend/src/sites/MiniScenarios.tsx` (+ `w4-mini-decisions.css`): panel `Financial scenarios`, exact empty/
  secondary/foot/notice copy, 5 columns with colgroup widths, `Scenario detail unavailable`, `Scenario creation
  unavailable`, refusal copy, Next/First page; `scenarioMoney` (half-even, `$` for USD else `CODE x.xx`).
- `shell/SiteAnalyticsFrames.tsx`: `FinancialsSections({scenarios:"live"|"unavailable"})` (single
  `<UnavailableTab label="Scenarios" />` literal kept for cold), `SiteFinancialsFrame` view `"scenarios"`,
  `miniDecisions` prop; `operatorSiteRoutes.ts` `SITE_FINANCIAL_SCENARIOS_ROUTE_PATH`/`siteFinancialScenariosHref`;
  `App.tsx` route + `miniDecisions` prop; `SITE_SCREEN_DESCRIPTIONS.scenarios`; settled regex `the site's scenarios`.
- Guard: multiset unchanged (the one Scenarios literal is cold's); comment updated. 6b swaps `Alternatives` for
  `Analysis` per B4.
- Tests: `frontend/src/sites/__tests__/miniDecisions.test.tsx` (3: the three 6a names).

Readings taken (6a; reviewer may overturn):
1. `{read time}` is shown as the raw six-digit UTC token (`window.to` minus 1 us), not localized.
2. After the first unbounded read, the returned `from/to/known_at` are written into the address with `replace` and
   no second read; Next sends `from,to,known_at,cursor`, so later pages and reloads read `Historical basis` rows
   (explicit past cutoff).
3. Pager is `{n} of {total}` with `First page` / `Next` buttons (no Previous).
4. Declared change = `key value unit` joined by `; `; Physical basis = pinned mini revision UUIDs in a list;
   Illustrative result: GROSS_SCENARIO -> `{money} gross sales scenario per eligible window, before costs`,
   ENERGY_ONLY -> `{kWh} kWh energy scenario per eligible window; gross sales unknown`, else `Cannot calculate from the
   selected evidence`; State = `Defined`/`Historical basis` + ` · ` + calculation words; kind words for the Scenario
   cell (`Productive load`, ...).
5. A non-MINIGRID Site at `/financials/scenarios` makes no read and shows panel text `Scenarios are read for mini-grid
   sites only.` with the unavailable Scenarios tab.
6. Breadcrumb `Sites › {Site} › Financials › Scenarios`; page title fallback `Financial scenarios`.

## Checks (u5b + 6a)
- Private DB `w403k_test` (dropped). Read 9 + links 1: 10 passed (794 s).
- Frontend: miniDecisions 3 passed; full suite 103 files / 2438 tests passed; `tsc --noEmit` clean; `vite build` built.
- `check-all.ps1`: all 11 guards passed. No full backend suite.

## u6 applied: no 6a amendment
u6 confirmed all six unit-6a readings unchanged (raw UTC token, replace with no second read, pager copy, cell
strings, non-mini refusal, breadcrumb/fallback; `site.site_id` is the public code). No code change, so no commit 1.

## Unit 6b (landed; PR-8 resolved by u6)
- `sites/miniDecisionsClient.ts`: `getAlternatives(code, findingId, revisionId)` (`mini-alternatives-1`).
- `sites/MiniAlternatives.tsx`: panel `Alternatives to investigate`, columns Explanation/Evidence/Disposition,
  exact empty/notice/NEEDS_REVIEW/no-evidence copy, `ALTERNATIVES_FINDING_UNAVAILABLE`.
- `shell/SiteAnalyticsFrames.tsx`: `SiteFindingFrame` routes MINIGRID to `CanonicalMiniFinding` (one W1 read
  resolves the revision; six-slot row; global breadcrumb; replace on absent `revision_id`); cold/EV child addresses
  render `Finding section unavailable for this site.` + `Open Finding overview`. `operatorSiteRoutes.ts`:
  `FINDING_CHILD_VIEWS` gains `alternatives`; `siteFindingAlternativesHref`.
- `sites/SiteFindingEvidence.tsx` `FindingSections`: `gap` section variant and `helper` prop.
- `sites/SitePerformance.tsx` `useResolvedAlternativesHref` + `assessmentAnalysis.tsx` `alternativesUnavailable`:
  the analytic CTA links only after a same-Site W1 read; `FindingDetail` untouched.
- Guard: `$expectedTabs` is the final u6/B4 multiset; fixtures swap the Alternatives case for two Analysis cases.
- Tests: `miniDecisions.test.tsx` `alternative_cells_and_revision_state`, `canonical_mini_tabs_breadcrumb_and_analytic_cta`,
  `cold_ev_alternatives_absent`; `siteFindingEvidence` row and `siteAction` unmatched-request expectation updated.

Readings taken (6b; reviewer may overturn):
1. The Overview tab keeps its `data-finding-section="finding"` id; only the label changes.
2. Analysis is declared `{ id: "analysis", label: "Analysis", unavailable: true }` in the frame, which renders
   `<UnavailableTab label="Analysis" />` through `FindingSections` (the guard's declared-entry form).
3. The helper renders inside the section-row `nav`, after the money aside, as plain `<p data-analysis-helper>`, on
   child views only (the root Overview has none). Inside the row it is chrome, so the v69 panel checks accept it.
4. Breadcrumb `Findings` links `/findings`; `Finding code unavailable` appears only after the W1 read loads (omitted
   while loading or refused); the section crumb is `Overview` on the root, omitted for an unknown section name; then
   `· site: {display_name}` linking the Site Overview. MINIGRID only; the Site tabs row stays.
5. While the W1 read loads or refuses, the Alternatives slot is a plain span with `Alternatives for this Finding
   unavailable` (new `gap` variant, not an `UnavailableTab`, so outside the guard multiset).
6. Sibling tabs use the resolved revision once loaded, the raw `revision_id` while loading or refused.
7. "Same-Site exact" means `site_code === site.site_id` and `finding.id` equals the route ID (case-insensitive).
8. After the replace, the frame does not re-read the W1 Finding (a ref holds the resolved selection).
9. Body states: W1 loading `Loading the Finding.`; W1 refused `Alternatives for this Finding unavailable`; Alternatives
   loading `Loading the Finding's alternatives.`; any Alternatives refusal `Alternatives unavailable` (ledger's 503
   copy); `currentness.state` HISTORICAL adds `Historical basis`.
10. Evidence cell: `evidence_summary`, then each cited ID linking the Site Evidence record inspector (no shared
    provenance drawer exists); none gives the ledger copy; `missing_evidence_reason` is not displayed.
11. Disposition words are the original ledger's four; no pager (at most one row per key, so 3 rows).
12. Alternatives page heading is the W1 `revision.title`.
13. Cold/EV `/recommendation` and unknown child names also render the section gap. The cold/EV link carries the window
    query. A cold/EV root without a domain client (test-only) renders `SiteFinding` with no section row.
14. Analytic CTA: the gap also shows while its W1 read loads; `finding_id: null` shows no CTA, as before.

## Checks (6b)
- No DB used. Frontend: miniDecisions 6 passed; full suite 103 files / 2441 tests passed; `tsc --noEmit` clean;
  `vite build` built. `check-all.ps1`: all 11 guards passed (in-page fixtures include the two new Analysis cases). No full backend suite (frontend-only unit).

## Unit 7 (landed; commit 8bd3b5c4)
- `sites/miniDecisionsClient.ts`: `getOpportunity(code,id)` (`mini-opportunity-detail-1`), `listOpportunities(code,
  {from,to,known_at})` (`mini-opportunities-1`, limit 100); `decisionRefusalCopy` (u6b 9 copy by code).
- `sites/MiniOpportunity.tsx`: `MiniOpportunityPage` (status, four cards, Bounded opportunity, Next decision | Consequence
  basis), `positiveOpportunity` (= read test `positive()`), `supportedRead`, `opportunityTone`, `renewableHref` (Site code
  + stored `from/to/known_at` parsed from `links.renewable`; never the UUID), `OpportunityDecisionEntry` +
  `selectedLocalDays` + `matchStudy` (S14 CTA).
- `shell/SiteAnalyticsFrames.tsx` `SiteOpportunityFrame`; `operatorSiteRoutes.ts` `SITE_OPPORTUNITY_ROUTE_PATH`,
  `siteOpportunityHref`; `App.tsx` route + `miniDecisions` passed to `SitePerformanceFrame` -> `MiniRenewable` ->
  `ProductiveUsePanel` (the W4-02 `Opportunity decision` unavailable entry is replaced only when the client is wired).
- `SITE_SCREEN_DESCRIPTIONS.opportunity`; settled regex `the opportunity|the opportunity decision`; CSS tones in
  `w4-mini-decisions.css`. Site Findings: `SiteFindingIndex opportunityHelper` (MINIGRID) renders the S11 helper below
  the lens row; the `Opportunities` chip stays `UnavailableChip`. Estate lens untouched (S21).
- Tests (`miniDecisions.test.tsx`): the four named unit-7 tests + `opportunity_chip_and_estate_lens_stay_unavailable`;
  `miniRenewableRoutes.test.tsx` one-day CTA expectation updated to the shorter-study copy. Backend vector
  `test_stored_supported_result_unchanged_through_s9_pending_and_stale_reads` already landed in unit 5 (unchanged, not
  rerun: no backend change). Non-vacuity: removing the CURRENT term from the positive gate fails the supported test.

Readings taken (unit 7; reviewer may overturn). PR-9 holds 1-3.
1. Breadcrumb: disabled root copy then `Sites › {Site} › Renewable evaluation › {OPP} › Overview` (PR-9.1); the
   Renewable crumb links the same exact href as the CTA; code crumb only once loaded.
2. Proposed-load card value `{kW} kW`, note `Linked scenario; name unavailable in this read` / `No scenario linked`
   (PR-9.2).
3. Multiple exact roots or any list refusal: noninteractive u6b-9 copy (PR-9.3).
4. Tone: green = positive gate; else HISTORICAL blue; else LIMITED or PENDING_RECOMPUTE/STALE_SOURCE amber; else grey
   (so SUPPORTED with zero eligible days is grey).
5. Usable headroom/Technical quantity show the frozen `headroom_kw` whenever status is SUPPORTED, including pending/
   stale reads (u4b: unchanged frozen values); the chip, secondary line, claim and Next decision use `supportedRead`
   (SUPPORTED, five assessed, CURRENT|HISTORICAL, resolved selected class).
6. Positive claim sentence only when the proposal is at most every eligible day's lower bound; a non-fitting proposal
   uses the `Measured renewable headroom ...` sentence.
7. Gross sales gap: `Withheld pending evidence` for PENDING_RECOMPUTE/STALE_SOURCE, else `Not calculated` (card and
   basis row). Scenario energy/Tariff: `Unavailable in this read` with a linked scenario, else the no-scenario copy.
8. Evidence drawer: an inline bounded list (max-height 96 px, inner scroll) of the day rows' accepted-ID union, each
   linking the Site Evidence accepted-record inspector.
9. Status bar shows currentness words (`Current selection`, `Recompute pending`, `Source changed since selection`,
   `Historical basis`, `Selection unknown`). No Site tabs row (mock has only the Overview context row); header action
   `Open site` links `/sites/{code}`.
10. CTA list read passes the renewable read's `known_at`; detail link carries no query. A non-MINIGRID Site at the
    opportunity route makes no read and shows `Opportunities are read for mini-grid sites only.`; a 200 with
    `opportunity:null` shows the same text.
11. The S11 Site Findings helper renders only for MINIGRID Sites, as `<p data-opportunity-index-helper>` after the chip
    list inside the controls block.
12. 1440/390 captures and layout evidence for the Opportunity page: not run (no browser run in this unit); the
    per-piece caps are unverified until 9b's captures.

## u6b applied (commits b28b4ed3, 53e3abf0; main merged at 2f98f72a)
All 14 checked. Changed: 3 (helper is the section row's next sibling, outside `nav`; panel guard
`test/panelStructure.ts` LEADING_SELECTOR admits exactly `[data-analysis-helper]`), 6 (sibling/Overview/money hrefs only
from the loaded selection; before that `gap` text and no money link; a W1 selection differing from a supplied
`revision_id` refuses), 9 (refusal copy by code via `decisionRefusalCopy`), 10 (`missing_evidence_reason` shown), 11
(`getAlternatives(..., page?)` with `known_at/cursor/limit`; `Next` iff `next_cursor`, `First page`; component keyed by
Site|Finding|revision), 13 (cold/EV `/recommendation` renders the domain frame; cold/EV root or `/recommendation`
without a domain client shows `This site's Finding view is unavailable.`), 14 (`alternativesUnavailable` whenever the
CTA destination exists, so `finding_id:null` shows the gap). Confirmed, tests only: 1, 2, 4, 5, 7, 8 (existing ref key
already carried Site/Finding/revision), 12.
Tests: `miniDecisions.test.tsx` `u6b_helper_after_row_and_sibling_predicate`, `u6b_same_site_identity_and_replace_reread`,
`u6b_alternatives_refusal_copy_reason_and_paging`, `u6b_cold_ev_recommendation_stays_in_domain_row`;
`t028Screens.test.tsx` null-Finding gap; `siteFindingEvidence`/`siteFindingHistory`/`siteAction` fixtures updated to
the ruling-6 predicate. Non-vacuity: restoring `resolved ?? revisionId` fails the sibling-predicate test.
Readings (u6b): gap text for an unresolved sibling is its own label (`Overview`, `Evidence`, ...); the domain-unavailable
copy is new; the `First page` control is an addition beside `Next`.

## Checks (unit 7 + u6b)
- No DB used (frontend-only). Frontend: 103 files / 2450 tests passed; `tsc --noEmit` clean; `vite build` built.
- `check-all.ps1`: all 11 guards passed on the final code revision 53e3abf0.
- Layout evidence: not run (no dev server/browser in this unit); Opportunity 1440/390 caps unverified.

## Unit 8 (landed; commit bb03bdc8)
- Backend `mini_decisions/work_links.py`: `WorkLinkService.link` (POST `/api/sites/{code}/work/decision-links`,
  `mini-decision-link-command-1` -> `mini-decision-link-write-1`), `contexts` (GET `.../work/decision-contexts`,
  `mini-work-contexts-1`), `parse_case_ids`. `store.py` unit-8 block: `lock_work_case` (FOR SHARE),
  `opportunity_exists`, `work_link_by_key`, `work_link_pair`, `visible_cases`, `work_contexts`. `model.py`:
  `DecisionRefused(..., status=)` + `case_not_found()` (W4-01 code/message, not remapped). Router kwarg
  `work_links=`; `main.py` composes `WorkLinkService(decision_store)`.
- Frontend: `miniDecisionsClient.getWorkContexts`; `siteWorkCases.tsx` `useDecisionOverlay` (keyed by Site, list
  `known_at`, `selection_token`, page case IDs; other-key answers discarded), `DecisionContext` (Incident `Linked
  findings` cell after Finding links; Maintenance line under Activity); `SiteWorkCasesFrame` passes the client only
  for MINIGRID; App wires `miniDecisions`. CSS `.work-cases-context` (2-line clamp, N4 bounded row space).
- Tests: `test_w403_work_links_postgres.py` (3 named); `siteWorkCases.test.tsx` (2 named; `serve` now answers the
  overlay with all-`[]` by default and records it in `contextRequests`). Non-vacuity: overlay order swapped to
  SCENARIO-first fails the contexts test; `DecisionContext` returning null fails the frontend tests.

Readings taken (unit 8; reviewer may overturn). PR-10 holds 1-3.
1. Already-linked pair under a new key: 409 `DECISION_DUPLICATE_KEY` (PR-10.1).
2. Refused overlay: `Decision context unavailable` without prefix; nothing while loading (PR-10.2).
3. Scenario label + `(Scenario detail unavailable)` plain text (PR-10.3).
4. POST refusal order: scope -> grant -> store -> MINIGRID (non-MINIGRID 422 `DECISION_LINK_SCOPE_INVALID`, as the
   other W4-03 writes) -> principal -> shape (exactly one of `scenario_id,opportunity_id`, else 422
   `DECISION_INPUT_INVALID`) -> actor -> [txn] case 404 -> key lookup 200/409 -> decision 422 -> pair 409.
5. Canonical hash path `{site_id, route:"work/decision-links"}` (no path root).
6. Contexts: `known_at` optional (omitted = DB read time), one value, future 422 `INVALID_KNOWN_AT`; `case_ids` one
   parameter, 1-100 distinct lowercase UUIDs, else 422 `DECISION_INPUT_INVALID`; a case is visible iff same
   tenant/Site and `created_at <= known_at` (W4-01 detail rule), else whole-read 404; any Site type is served (no
   Performance gate; authored associations only), the UI calls it only for MINIGRID.
7. Opportunity "visible selected revision" = the detail head rule (a visible selection whose pins satisfy the
   cutoff); Scenario uses its head revision `name` at the cutoff.
8. Opportunity URL uses `site.site_code` (public code, u6), not the UUID.
9. Layout evidence / stocked 1440/390 captures: not run (no dev server or browser); W4-01 Incidents 460 px cap with
   context lines is unverified until 9b.

## u7 applied (commit 3ba626ba; main merged at the merge after bb03bdc8)
PR-9.1: Opportunity breadcrumb is `Findings › {OPP} › Overview · site: {Site}` (root gap text, code only once
loaded, only the Site suffix links); `Sites`/`Renewable evaluation` slots removed. Test in
`opportunity_history_and_exact_renewable_cta` at innerWidth 1440 and 390 (DOM only; geometry is 9b). PR-9.2/9.3 and
readings 2-15 confirmed without code change (CTA refusal copy is already by code; empty evidence copy present).

## Checks (unit 8 + u7)
- Private DB `w403n_test` (dropped). Backend: `test_w403_work_links_postgres.py` 3 passed; with
  `test_w401_work_api.py` and `test_w403_opportunity_links_postgres.py` 15 passed (600 s). No full suite.
- Frontend: 103 files / 2452 tests passed; `tsc --noEmit` clean; `vite build` built.
- `check-all.ps1`: all 11 guards passed (on 3ba626ba).
- Layout evidence: not run.

Next: unit 9

## Unit 9a (landed; commits 37122434, u8 applied 6915ae31; main merged at 56591c78)
- `backend/tests/fixtures/w4/w403-mini-decisions.json` (`w403-mini-decisions/1`, sorted keys, final LF): Site codes,
  W4-02 source, both reconcile windows, the late variant, command templates (`<placeholder>` values), semantic expects.
- `tools/w403_mini_decisions_walkthrough.py`: `--db <*_test> --work var/<dir>` with `prepare|serve|replay|capture|drop`;
  library functions the test reuses: `fixture_callbacks(secret, scopes, grants=)`, `import_sites`, `publish_and_ingest`,
  `ingest_late`, `mini_days`, `opportunity_cli` (worker CLI reconcile + run-pending), `seed_case` (W4-01 `WorkService`,
  `service:w401-fixture`), `kobo_revision`, `http_replay` (five W4-03 command types), `reads`, `run_replay`, `iso`, `fill`.
  `serve` binds 127.0.0.1:9761; `capture` delegates to `tools/w403-mini-decisions-evidence.mjs <web> <work>/capture`
  (NOT YET WRITTEN: unit 9b). The tool runs the Performance comparison for MG-W402-001 (opportunity GETs are gated).
- `backend/tests/test_w403_replay_postgres.py`: `test_positive_missing_late_replay_and_fresh_reload` (fixture bytes,
  no-credential/wrong-secret/wrong-Site/no-grant 403 with no write, SUPPORTED 5/5 with 6 Oct EXCLUDED, pins = row tuples,
  per-eligible-window 10 kWh / 2.50 USD or WITHHELD, no-tariff null gross, OPPORTUNITY context only on the linked
  Incident, late branch new head + 2-entry history + old-cutoff first head, missing study not SUPPORTED, fresh-app reload)
  and `test_authored_work_link_preserves_unlinked_case_count` (+u8: same-pair new-key 409 exact body, OPPORTUNITY then
  SCENARIO at now, OPPORTUNITY only at the earlier cutoff, later case 404). The comparison report goes to `tmp_path`.

Readings taken (9a; reviewer may overturn). PR-11 holds 1-3.
1. KOBO Alternative POST at wall time is 409 `DECISION_BASIS_CHANGED` (F02 revisions at fixture `SETUP_AT` 29 Oct, after
   DB time); recorded as the observed exit and asserted conditionally (PR-11.1).
2. Late branch reads `STALE_SOURCE` before rerun and at the old cutoff (PR-11.2); the late variant is authored in the W4-03
   fixture and not published under the W4-02 source.
3. Missing branch uses a second reconcile `[2026-10-07T21Z, 2026-10-12T21Z)` (PR-11.3).
4. `--db` must be a lower-case identifier ending `_test`; `--work` a folder directly under repo `var/`; `drop` only with
   the tool's marker.
5. The work-link test window is the last 20 days to tomorrow (W4-01 31-day cap).
6. Scenario fresh-reload equality is over authored fields only (state fields legitimately change after the late branch).

## Checks (9a + u8)
- Private DB `w403o_test` (dropped). `test_w403_replay_postgres.py`: 2 passed (350 s); after u8 vectors the work-link
  test passed alone (106 s). No full suite.
- `check-all.ps1` at the 9a code: all 11 guards passed. No frontend change in 9a.

## Unit 9b (not started; context budget)
Remaining per u5 9b + u8 9: five registry panel entries (screen list at `v69-dependency-registry-pilot.json:408-409`
holds the two sitework rows; add scenarios/alternatives/opportunity-finding; which opportunity indices count toward
"five" is open - three panels exist in `v69-rendered-panels.json:856`), `expectV69Panels` for the three W4-03 screens in
`miniDecisions.test.tsx` plus `narrow_mock_panel_budgets` and `exact_routes_no_dead_cta`, the capture script
`tools/w403-mini-decisions-evidence.mjs` (pattern: `.agent/W4-01-evidence/capture.mjs`; caps in u5 9b; stocked/refused
overlay and scenario no-route copy per u8 9), served via `walkthrough serve` + vite, one full backend Postgres suite,
review packet.

Next: unit 9b, then unit 10 (superseded by the Unit 9b section below)

## Unit 9b (landed except the PR-12 fixes; commits 09bae780, d56c25c3, fb2e3eb2, e1590a74, 5014fe32, 2eba1be3)
- Registry (`09bae780`): the five u9 `panels[]` keys, `status:"gap"`, areas money/claims; new nodes
  `I-mini-decision-store|read|ui`, `D-mini-decisions` (task W4-03); ledger `registry_dependencies` for `scenarios`,
  `alternatives`, `opportunity-finding` (coverage left `deferred`). `check_v69_dependency_registry.cjs` valid (249 nodes,
  39 linked panels); `analysis:3#b` and the estate Opportunities index untouched.
- Tests: `miniDecisions.test.tsx` per screen `*_v69_panels_and_planted_rejection` (Scenarios populated/empty/refused,
  Alternatives rows/empty/503, Opportunity) plus `narrow_mock_panel_budgets` and `exact_routes_no_dead_cta` in each of
  the three describes (24 tests); `siteWorkCases.test.tsx` adds `u9b_incident_linked_and_refused_overlay_panels`
  (expectV69Panels + planted rejection with the linked Scenario `(Scenario detail unavailable)` line and a scoped 503).
  `noDeadCta` proved non-vacuous (planted `href="#"` fails); CSS budget asserts failed on an empty stylesheet.
- `tools/w403-mini-decisions-evidence.mjs` (shared width guard, 32 width claims all ok) and `Walk.stock()` in
  `tools/w403_mini_decisions_walkthrough.py` (four more Incidents, two more Requests through `WorkService`, keys
  `w403-capture-{incidents,requests}-N`, recorded in `<work>/capture/stock.json`, run inside `capture`).
- Capture (run 2, code `2eba1be3`, DB `w403p_test` dropped after): `var/w403p/capture/evidence.json` 240/265 checks;
  `<state>-<1440|390>-app.png`, `<screen>-<w>-mock.png`, `mock-measure/mock-measure.json`. Panel set and order match
  the mock on every produced state. 25 failures are PR-12 (Scenarios, Opportunity cards and Incidents-390 over cap;
  Alternatives blocked: KOBO site 503 from the worktree's local `var/sites/kobo-001.yaml`, KOBO Finding read
  `PERFORMANCE_CUTOVER_CLOSED`). Unproved: Opportunity SUPPORTED/CURRENT, stocked Alternative (u9: not a gate).
- Viewed: `incidents-linked-stocked-390-app.png`, `opportunity-current-late-settled-1440-app.png`,
  `scenarios-populated-1440-app.png`, `scenarios-1440-mock.png`.

Readings taken (9b; reviewer may overturn):
1. Opportunity panels `requires` also name `I-mini-depth-read` (W4-02 read beside the W4-03 nodes); each new panel
   carries the W4-03 read/UI/data nodes.
2. Capture stock is seeded by `capture` itself (no new subcommand); IDs/counts live in `stock.json`, not `replay.json`.
3. Work window for captures: the last 7 days through tomorrow at 00:00Z.
4. Scenarios empty uses `from=1970-01-01T00:00:00.000000Z&to=2026-10-01T00:00:00.000000Z`; refused uses reversed bounds.
5. Opportunity states: current detail (after the missing branch it reads `Source changed since selection`),
   `k_before_late` via a harness rule appending `known_at` to the exact detail GET (PR-12.5), missing via the
   `first_day=2026-10-08` row of `replay.missing`.
6. jsdom budget tests assert the stylesheet rules as text plus structure; geometry is the capture's.
7. Captures use `mobile:false` (W4-01 pattern); `measure-mock-panels.mjs` uses `mobile:true` at 390 (mock 360 wide vs
   345 in the capture's own mock shots).
8. The Alternatives scoped-503 rule never fired (the frame stopped at `Site unavailable`); recorded, not retried.

## Checks (9b)
- Focused: `miniDecisions.test.tsx` 24 passed; `siteWorkCases.test.tsx` 9 passed.
- Frontend suite at `2eba1be3`: 103 files, 2462 tests passed. `tsc -b --noEmit` 0. `npm run build` 0.
- `tools/check-all.ps1`: all 11 guards passed (incl. navigation truthfulness, rail fixtures via architecture seams,
  dependency registry, screen ledger, evidence width check). No backend suite run (brief).

PR-12 is OPEN in `.agent/W4-03-pending-rulings.md` (five questions). Build stopped there.

Next: unit 10
(Per u9, 9b is unit 12 and the last build unit; what remains after the PR-12 rulings is the cap fixes, an
Alternatives/Opportunity recapture, the one full backend Postgres suite and `.agent/W4-03-review-packet.md`.)
