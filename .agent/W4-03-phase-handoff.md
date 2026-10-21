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

Next: unit 2b after PR-2 is ruled, then unit 3
