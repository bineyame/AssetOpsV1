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

Next: unit 3.
