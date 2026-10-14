# S4-02c phase 2 handoff - scoped drain and run plan

Implementer: fresh Claude, 2026-10-14. Branch `task/S4-02c-evidence-consequence-work`, from `0a79be14`. Phase 2 only (packet table row 2; items 3-4; carries C4 worker half, N1, N3, N4, N7, R2; phase 1 review L1-L3, I1-I2). No phase 3 walkthrough. Built state: `.ai/CODE_STATE.md` "S4-02c phase 2".

## Built

- `financials/recompute.py`
  - `targets()` dispatches `EVIDENCE_ACCEPTED`: `store.evidence_target(...)` (scoped snapshot); missing evidence/revision in this tenant/Site -> FAILED `EVIDENCE_LOCATOR_NOT_IN_SITE`, no ACCEPTED disposition -> FAILED `EVIDENCE_NOT_ACCEPTED` (both without fallback); `evidence_no_op(target)` -> typed no-op, else derive that same revision.
  - `evidence_no_op`: `FINDING_REVISION_SUPERSEDED` (queued `revision_no` != highest same tenant/Site/Finding `revision_no`, the 0012 trigger's definition), `EVIDENCE_ROLE_NOT_RELEVANT`, `EVIDENCE_ASSET_NOT_RELEVANT`, `EVIDENCE_OUTSIDE_CANDIDATE_TIME` (no strict overlap with `fuel_cost.merge` of positive-width claim spans; also null interval). Never quality (N1).
  - `process()` refuses a work dict whose `tenant_id`/`site_id` differ from the run scope (`WORK_SCOPE_MISMATCH`, attempt not recordable in another scope, `attempt_no` 0). No-ops record `SUCCEEDED`, `[]` IDs, `no_op_reason`.
  - `retry_due_at` (1, 2, 4, 8, 16, then 16 min, no cap), `eligible_since`, `RunReport.counts()`, `ConsequenceRecomputeWorker(clock=...)`, `run(tenant, site, limit, now=None)`: Site claim -> pending -> due (never attempted, or `now >= retry_due_at(last finished_at, last attempt_no)`) -> sort by eligible-since instant (L2) -> first `limit` once each. `run_pending` kept unchanged as the unscheduled helper (tests/walkthrough).
- `financials/adapters/postgres_consequence_store.py`: `pending_work` adds `last_attempt_no/last_outcome/last_finished_at` (lateral on the 0012 attempt index); `evidence_target` (REPEATABLE READ, all lookups tenant/Site scoped); `claim_site` context manager (dedicated AUTOCOMMIT connection, `pg_try_advisory_lock(hashtextextended('financial_consequence_runner:'||site, 0))`, explicit unlock in `finally`, `invalidate()` if unlock fails); `record_attempt(..., no_op_reason=)`.
- `recompute_consequences.py`: `run --tenant --site [--limit 100]` (tenant now required; non-`demo` tenant refused, exit 2, message says it covers no other tenant's Sites), per-item lines plus a summary line (`claimed`, `skipped`, `now`, `limit`, selected/appended/replayed/no_op/failed/deferred/backlog). Timer, owner, cadence and recovery documented in its docstring and `backend/README-db.md` "Consequence recompute runner (S4-02c)".

## Proofs

- `backend/tests/test_s4_evidence_drain_postgres.py` (10): same-revision drain -> consequence 2 `QUANTITY_UNAVAILABLE/POWER_NOT_IN_ASSESSMENT_INPUTS`, consequence 1 retained, attempt IDs, read STALE -> CURRENT, rerun selects 0; SUSPECT same-asset mean derives (N1); append-then-crash replays the same ID; superseded no-op + revised revision's own FRA consequence; role / asset (cloned Finding of the pv asset, N7) / outside-Candidate no-ops via test-written work rows; forged Site B evidence locator FAILED and a Site A row under Site B scope refused, no consequence; retry at f+59s deferred, f+1m due, f+2m, f+4m (injected `now` vs DB `finished_at`, no sleep); L2 starvation; claim held -> second runner skipped; subprocess runner killed -> claim released, restart drains, no runner lock left in `pg_locks`; R2 bounded batch.
- `backend/tests/test_s4_evidence_drain.py` (12, no DB): predicate edges (half-open, merged touching spans, zero-width, quality), retry schedule, selection/order/limit/counts, injected clock, skipped claim, locator refusals.
- Carries: L1 race probe now `database = current_database()` and the Site's enqueue key (`(classid<<32)|objid`); L3 `test_downgrade_refuses_while_a_no_op_reason_exists`. The phase 1 chain test no longer asserts `CAUSE_NOT_SUPPORTED` for evidence (now dispatched); `test_s4_consequence_cause_dispatch.py` keeps unknown causes only.

## Checks as observed

- Mutation proofs (scratchpad `mutate.py`, DB `assetops_s402c2_mut_test`, each file restored by `git checkout`, tree clean after): 11/11 killed - quality no-op (unit), superseded check removed (3 failed), non-strict overlap, unmerged/zero-width spans, forged locator falls back to `latest_revisions_overlapping` (3), work scope check removed (PG), retry schedule ignored (3), enqueue-order-only selection (2), claim ignored (2), explicit unlock removed (PG `pg_locks` check), `no_op_reason` not stored (PG).
- L1 non-vacuity: the scoped probe still observes the waiter (`waited` asserted true; phase 1 file 13 passed).
- R2 measured: six ingestion chunks of 48 accepted generator-power means (581 evidence work rows across the real Finding and two whole-day clones) took 0.698, 0.627, 0.640, 0.604, 0.611, 0.599 s; the remaining 481 rows drained in bounded runs of 100 in 14.2 s; no duplicate basis.
- Focused: `test_s4_evidence_drain_postgres.py` 10 passed; `test_s4_evidence_consequence_work_postgres.py` 13 passed; `test_s4_evidence_drain.py` + `test_s4_consequence_cause_dispatch.py` + `test_s4_consequence_read.py` 19 passed.
- `tools/check-all.ps1`: All 9 guards passed.
- Full backend (`assetops_s402c2_full_test`, after the build commits): 2090 passed in 15:59. Frontend not run (no frontend file changed).

## Deviations

- Never-attempted work is always due regardless of `now` (the schedule only defers FAILED work); eligibility order uses its `enqueued_at`.
- A work dict scoped to another Site cannot have its FAILED attempt recorded (attempt FK is Site-scoped); `process` returns it unrecorded with `WORK_SCOPE_MISMATCH`. The runner never selects such rows; this is defensive.
- Wrong-role/asset/outside-Candidate no-ops cannot arise from the 0012 trigger for role and episode (it filters them); the Postgres proofs use test-written work rows (allowed: rule 8 scans only `backend/assetops_backend`).
- Runner exit code is 0 when the Site is skipped.

## Questions

None. No owner-facing text added (error/no-op codes are typed fields; no component renders them).

## What phase 3 needs

- Use `run(...)` (or the CLI) for the walkthrough drain so Site claim and counts are exercised; `run_pending` remains for setup.
- Leg A: `evidence_target`/`evidence_no_op` decide; same-revision consequence n+1 should be `QUANTITY_UNAVAILABLE/POWER_NOT_IN_ASSESSMENT_INPUTS` (proved here on PowerSite). Leg B: the old evidence work drained after the revision no-ops `FINDING_REVISION_SUPERSEDED`.
- N2 price publication, N5 precondition and C5 captured IDs remain phase 3.

## Risks

- R2 measured (see Checks): ingestion chunk latency with the Site enqueue lock and ~580 rows. Not measured: two concurrent overlapping chunks (I1 deadlock window).
- `pending_work` loads every pending row of a Site per run (bounded processing, unbounded selection read); fine at hundreds of rows.
- Phase 1 merge gate (L2) is now closed by this phase; phase 1 + 2 still must not deploy before review.
