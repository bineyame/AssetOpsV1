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

Next: unit 2
