# W4-01 phase handoff - after spec commit 1 (2026-10-20)

Branch `task/W4-01-work-case-core` (worktree `AssetOpsV1-review5`), from main `d30fdc90`.
Commit 1 landed as `4cb89c68`. Next run: **commit 2 (domain and writer)**, spec `.agent/W4-01-build-spec.md`
"Commit sequence" item 2, plus Review closure B4-B6, S14-S17, S25 (rule-8 registration), Q11 and Q6/Q28.

## What landed (commit 1)

- `backend/migrations/versions/0027_w4_work_cases.py`: spec lines 49-270 copied byte-for-byte by script (no
  hand transcription, no added docstring). `down_revision = "0026_w2_ev_money"` matches installed 0026 spelling.
  Blob `a40af142`, file SHA-256 `12d07fef2be677a68885af2b5625d21fbf2c667beb1f32c773752ebcf7dac10e`.
- `backend/tests/test_w401_migration_postgres.py`: exactly the two named nodes
  `test_0027_parent_scoped_fks_append_only_and_clean_downgrade` and `test_0027_nonempty_downgrade_refuses`.
- Upgraded-head literals `0026_w2_ev_money` -> `0027_w4_work_cases` in: test_s1_bindings, test_s2_evidence_ledger,
  test_s405_publication, test_s4_consequence_store, test_s4_evidence_consequence_work, test_w200_source_events,
  test_w201_cold_foundation, test_w203/w204/w205a/w206 (`HEAD` constants). test_w207: new `UPGRADED_HEAD` for every
  `head(engine)`/`get_heads()` assertion; `HEAD = "0026_w2_ev_money"` kept for the 0026 identity/down_revision check;
  `PREVIOUS`/direct-target 0025 assertions untouched.

## Checks run (private DB `w401a_test`, created and dropped; no other DB touched)

- `test_w401_migration_postgres.py`: 2 passed (14.6 s).
- Adjacent head/downgrade nodes: s1 TestMigration, w203, w204, w205a, w206, w207 TestMigration0026: 31 passed
  (121.6 s); s2 drifted-asset, s405 publication downgrade, s4 0015 downgrade, s4 TestMigrationPaths, w200
  TestMigration0020, w201 TestMigration0021: 9 passed (45.3 s). No full suite run (per dispatch).
- `tools/check-architecture.ps1` passed; `tools/check-agent-workflow.ps1` passed.

## Readings made (all recorded; none decided product semantics)

1. Head-literal updates belong in commit 1: adding 0027 breaks every upgraded-head assertion at that commit. Every
   listed occurrence was inspected; all were upgraded-head (after `upgrade head` or a rolled-back downgrade).
2. Alembic runs one transaction for the whole downgrade (`env.py` has no per-migration transactions), so a lower
   migration's refusal also rolls back 0027's empty downgrade; existing refusal tests keep passing unchanged.
3. Catalog count is exact, not `>=`: 11 PK + 27 UNIQUE + 7 explicit = 45 indexes on the 11 tables (measured equal).
4. Scoped FKs are proved by exact `pg_get_constraintdef` text for all 25 FKs, no-CASCADE (`confdeltype/confupdtype =
   'a'`), and behavioural refusals: foreign-Site Asset, unknown Site, kind/child mismatch both ways, cross-Site
   request->Incident, cross-case revision predecessor, forked successor, duplicate revision number, wrong-Site
   revision/event/record/op-record, mismatched Finding/revision pair, unknown evidence, unknown Action/event.
   The second Site is `imported(store, code="KOBO-002")` (pattern from test_s7_source_health).
5. A **positive** `work_case_action_link` insert is not exercised in commit 1: the PowerSite fixture has no Action
   rows. Its FK definitions are asserted exactly and an unknown Action/event is refused. The positive pinned Action
   comes with commit 2's F01 + `recommendation/accept` path (Review closure 3 Q7).
6. N36: quantity `Infinity`, `NaN` and `-1` are each refused by `operational_record_quantity_check`.
7. Test helper rows use SERVICE actor `service:w401-fixture` and SQL inserts only (schema-level; no writer yet). Rule-8
   registration is deliberately not added (spec S25: lands with the writer in commit 2).
8. Nonempty downgrade is one node that refuses with each W4 root alone (operational record, plan, case+revision), so
   the node count stays at the spec's 2 for this file.

## Next (commit 2) anchors

- Writer: `backend/assetops_backend/work/{model,service,adapters/postgres_work_store.py,composition.py}`.
- Rule-8: `tools/checks/configuration-persistence.ps1`, `$workWriter` + 11 tables (spec S25 literal).
- Positive fixture: `test_s6_action_store_postgres.py:runner,CASES["F01"]`, `test_s4_finding_store_postgres.py:run_case`,
  `action_api.py:accept` (Review closure 3).
- Shared provenance: Q11 - W4 commit 2 carries `evidence/public_provenance.py` only if W3-01 commit 1 is not merged.
- Open questions for commit 2 are in `.agent/W4-01-pending-rulings.md`; resolve before building commit 2.

## Open risks

- Full real-Postgres backend suite not run (deferred to the slice's final revision per spec).
