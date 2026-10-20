# W4-02 unit 1 handoff (partial)

Branch `task/W4-02-mini-grid-depth`, commit `00a5703a`. Main was fast-forwarded first to `c5a3b5d5`, which carries
closure 5. Context ran past budget, so this run stops at a partial unit 1. A patch is saved at
`%TEMP%\claude\0001-W4-02-unit-1-partial-*.patch`.

## Spec readings this run applied (I decided nothing; list for review)
- Unit 1 scope comes from closure 2 Q28 and closure 4 N4: `0029`, roles-4, typed properties, publication enqueue
  call sites, the store writer, and guard registration. I read B2's authored v4 profile and binding-service mapping,
  and both closure-5 items (the cold-gate Site-type lookup and the `MG-W402-001` registration), as unit 3, because
  their named tests need the `MG-W402-001` Site and an authored batch. None of them is built.
- The 0029 selection table creates `job_id` inside `CREATE TABLE`, then adds `job_id` and its FK with an
  `ALTER TABLE`, which matches the closure-2 DDL shape.
- Hours: a job window is `[local_hour AT TZ, +1h)` using `site.timezone`. `mini_enqueue_hour` refuses three
  things: a window that is not exactly 1 h and aligned to a local hour, a domain outside the four, and a renewable
  hour other than local 12:00.
- Configuration enqueue covers `[max(effective_from, at - 5 days), min(coalesce(effective_to, at), at))`. `at` is
  `plan.superseded_at`, as the EV precedent does. The Foundation store calls it from both `publish()` and
  `publish_configuration()`, for every inserted Foundation and binding-set revision.
- Downgrade takes ACCESS EXCLUSIVE on the three mini tables and EXCLUSIVE on `recompute_job`, then counts.
- S3 is applied as written: `_fence` and `site_window` exclude the mini domains, and `dispatch_jobs` gets
  `AND domain = 'dispatch'`.
- The store writer is `mini_depth/store.py` (`PostgresMiniDepthStore.append_selection`). The worker in unit 4 owns
  lease and settle.

## Landed (anchors)
- `backend/migrations/versions/0029_w4_mini_depth.py`: `GATE_ROLES` has the 17 channel roles. `DOMAIN_ROLES` is the
  B1 matrix. The file holds the functions, the constraint trigger and the guarded downgrade.
- `sites/binding_roles.py`: `ROLE_SET_MINIGRID_4` and `MINIGRID_ROLES_4`, added to served and verification sets.
  `analytics/assessment_worker.py` `ROLES_BY_SET` includes roles-4.
- `sites/models.py`: three properties, `MINIGRID_PROPERTY_CARRIERS` and `MINIGRID_STRICTLY_POSITIVE_PROPERTIES`.
  `sites/minigrid_foundation.py` validates them, called from `site_parsing.py`.
- `sites/adapters/postgres_foundation_store.py`: `_enqueue_mini_configuration`.
- Rule 8 (`tools/checks/configuration-persistence.ps1`) registers `$miniWriter` and `$miniTables` with
  anti-vacuity, plus mini enqueue SQL limited to the Foundation store. `tools/writer_guard_probes.py` has the mini
  probes and controls; the probe corpus has not been run.
- Tests: `backend/tests/test_w402_migration_postgres.py` (9 nodes) and `test_w402_roles_properties.py` (pure,
  including the dispatch-roles check). Both pass on the private `w402a_test` clone. Current-head literals in the
  13 named test files now read `0029_w4_mini_depth`. The W4-01 `down_revision` assertion now pins `0027`.

## Checks
- `tools/check-all.ps1`: all 10 guards passed (architecture, navigation, workflow and missing-claim included).
- Focused run (16 files, `-n 2`, `w402a_test`): **185 passed, 29 failed**, 11m45s. The private DB and its clones
  were dropped afterwards.

## Resume here: the 29 failures (none in the w402 files)
1. **Downgrade-through tests (about 22 nodes).** These include s1 0004, s2 0005, s405, the s4 0011/0015
   consequence tests, the s4 evidence-work tests, w200 0020, w203, w204, w205a, w206 (four), w207 (two) and w401
   (two). Their MINIGRID fixtures now leave `mini_*` jobs, so 0029's N5 refusal fires before their own expected
   message. Each test needs the `ev_charging` precedent at `test_w200_source_events_postgres.py:559`: before each
   `command.downgrade`, delete `recompute_job WHERE domain LIKE 'mini\_%'` as replica. Do not weaken 0029.
2. `test_s2_evidence_ledger_postgres.py`: one exact-job assertion (`366 == 1`) is the S4 "exact-job assertion"; scope
   it to `domain = 'dispatch'`. Three scope/refusal tests compare table-count dicts that now include mini jobs.
3. `test_w200_source_events_postgres.py`: the dispatch-only job check (line 176) needs the mini domains excluded.
   The raw-copy accepted row raises 23514 at the former lines 568 and 633-634. Per S4, add the same-transaction
   ACCEPTED disposition or use an unmapped role.

## Next, still in unit 1
Fix the 29 tests above and rerun the focused set. Run `python tools/writer_guard_probes.py --seam mini` (the mini
probe names) on a committed tree. Then commit and go to unit 2. Open question for unit 3:
`.agent/W4-02-pending-rulings.md` R1 (mixed v3/v4 validation for roles-4).
