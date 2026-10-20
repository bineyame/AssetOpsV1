# W4-01 phase handoff - run 4: commit 3 partial (2026-10-20)

Branch `task/W4-01-work-case-core` (worktree `AssetOpsV1-review5`). Commit 1 `4cb89c68`, commit 2 `9533d97d`, run-3
handoff `69fcbf80`; merge of main `dd57d874` (clean); **commit 3 partial `5973ca09`**. Stopped on pending rulings
q3 (6-10) in `.agent/W4-01-pending-rulings.md`.

## What landed in `5973ca09`

- `backend/assetops_backend/work_api.py`: `build_work_router(service, scope, unavailable, access, command_access,
  principal)`; `W401_FIXTURE_SERVICE_PRINCIPAL_ID = "service:w401-fixture"`; `Principal` callback type with
  `no_service_principal` default. Six POST routes: `/api/sites/{site_code}/work/cases`, `cases/{case_id}/events`,
  `cases/{case_id}/revisions`, `cases/{case_id}/records`, `plans`, `operational-records`. Order: `access`
  401/403, scope 404 `SITE_NOT_FOUND`, `command_access` 401/403, no service 503, then the service (q2 reading 2).
  Refusals are `{"detail":{"code","message"}}`; 201 new, 200 exact retry.
- `backend/assetops_backend/main.py`: Lane A mount after the Action index router, `build_work_service(database_url())`
  or None, `(WORK_UNAVAILABLE,)`; no SERVICE principal injected (q3 question 10).
- `backend/tests/test_w401_work_api.py` (7 nodes): `test_scope_before_shape_401_403_404`,
  `test_mutation_409_422_and_store_503`, `test_idempotent_200_same_body`,
  `test_user_actor_403_and_service_attestation_422`, `test_client_authorization_basis_422_and_server_basis_persisted`,
  `test_path_identity_changes_idempotency_hash`, `test_plan_record_operational_literal_responses` (injected
  `10000000-...` IDs). Fixture: `imported(store)` plus a test scope dict; second Site via `imported(store, code=...)`.

## Not built (awaiting q3 rulings)

- `GET /api/sites/{site_code}/work/cases/{id}?known_at=` (B3 `work-case-detail-1`) and
  `work/link_coverage.py:linked_coverage` (Q9): blocked by the no-edit rule on
  `analytics/adapters/postgres_assessment_store.py` (q3 question 6) and adapter placement (7, 8).
- `test_list_refusal_has_null_rows_and_total` (question 9).

## Checks (this run)

- Focused on private `w401d_test` (created, then dropped): `test_w401_work_api.py` 7 passed (22 s);
  adjacent `test_w401_work_service_postgres.py` 7 passed (43 s).
- `create_app()` OpenAPI lists the six work paths.
- `tools/check-all.ps1`: all 10 guards passed on `5973ca09`.

## Next

Answer q3 6-10, then finish commit 3: detail GET, `link_coverage.py` and its adapter reads, and detail tests.
Review this phase before UI (spec item 3).

## Run 5 (stopped)
Merged main at `ec91ed70`. Prerequisite cherry-pick `a75b0291` conflicted in `tools/checks/configuration-persistence.ps1`
(`$pgWriters` list: `$workWriter` vs new `$pgReaders` line); aborted. Resume: after a ruling on the conflict (see
pending rulings "Run 5 stop"), redo step 2 from `a75b0291`, then finish commit 3 per spec "Run 3 rulings (q3)".
