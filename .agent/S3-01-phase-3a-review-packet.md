# S3-01 phase 3a review packet - durable dispatch read, comparison and cutover gate

Task: `tasks/S3-01-dispatch-assessment.md`, phase 3 row "Read, comparison and UI cutover" (backend half; UI is phase 3b). Branch `task/S3-01-dispatch-assessment`, commits `aaa47ae`..HEAD. Status stays `active`. Rulings: `D-2026-10-11-s3-phase-2-selection-and-read`, `.agent/architect-S3-answers-1.md`; phase-2 review carries F3-F6 and fixture determinism (`.agent/S3-01-phase-2-fix-rereview.md`). Questions with built fail-closed defaults: `.agent/S3-01-questions-3.md` Q9-Q13.

USER_REVIEW_REQUIRED: not at this phase; the owner checkpoint closes the whole task after phase 3b (UI). This phase needs a fresh Claude review.

## Outcome delivered

- Carries closed: F3 (no default blending of successive epochs), F4 (automatic reconcile + `STALE_PROJECTION` on configuration/model change), F5 (an ordinary Necessary interval case, 10-09), F6 (an always-expiring lease reaches FAILED), fixture SOC template chosen by minimum `(source_time, sequence)`.
- Append-only selection log (migration 0008 `analytic_run_selection`) gives commit-ordered heads.
- A read service deriving `UNASSESSED | PENDING | CURRENT | STALE_PROJECTION | FAILED` from one REPEATABLE READ snapshot, with pinned revision drill-down (as-accepted vs selected configuration, backdated `selection_note`), typed `UNAVAILABLE` gaps and demo annotations kept apart from provenance.
- Routes `/api/sites/{code}/performance/dispatch/{cutover|windows/{day}|runs/{id}|revisions/{id}}`, closed (409) until a file-backed comparison report PASSES with a current legacy digest and zero live lineage breaks.
- Anomaly fixed: a `LIMITED` window now always names its limitation (the 10-09 window had `LIMITED` with `[]`; cause: an interval `OPEN_BOUND` limited the window without being lifted into the window list).

## Files materially changed

- `backend/assetops_backend/analytics/cohort.py` (`_multi_epoch`), `dispatch_v3.py` (`INTERVAL_LIMITED` lift; `LIMITED` only from a non-empty list), `assessment_worker.py` (reconcile, `max_attempts`), `adapters/postgres_assessment_store.py` (lease cap, selection log, `window_snapshot`, run/revision detail, lineage reader), `dispatch_read.py`, `performance_comparison.py`, `adapters/demo_manifest_file.py`.
- `backend/assetops_backend/performance_api.py`, `performance_migration.py`, `main.py` (mount + gate), `evidence/composition.py`.
- `backend/migrations/versions/0008_assessment_selection.py`; `tools/checks/configuration-persistence.ps1` (rule 8 lists the table).
- `tools/s3_dispatch_cases.py` (necessary-run case, deterministic template); scenario `kobo-s3-dispatch-necessary-run` v1 registered in the scenario guards.
- Tests: `test_s3_dispatch_v3_analytic.py` (F3 x2, open-bound window), `test_s3_dispatch_assessment_postgres.py` (F6), `test_s3_dispatch_read_postgres.py` (status, race, backdated config, failed job, pinned drill-down, routes over Postgres), new `test_s3_performance_cutover.py` (14), `backend/tests/dispatch_3_decision_table.md`.

## Acceptance (phase 3 row and "Read states and acceptance", backend half)

| Criterion | Status | Evidence |
| --- | --- | --- |
| Read returns Site/window, cutoff label, selected run/model/cohort, evidence IDs, limitations, derived status | Met | `DispatchReadService.window`; `test_current_window_and_pinned_drill_down` |
| `NO_PENDING_DISPATCH` alone is not CURRENT; overlapping pending/leased/failed job is never CURRENT | Met | `test_acceptance_racing_a_lease_is_never_current_until_reassessed`; Q12 mapping |
| Stale keeps prior revision inspectable and visibly stale | Met | `test_backdated_configuration_reads_stale_then_is_reassessed_without_an_operator`, `test_a_failed_recompute_reads_failed_with_the_prior_selection` |
| Historical revision reloads by stored run/evidence/revision, not `knowledge_at` replay | Met | pinned drill-down via `revision_detail`; `CUTOFF_LABEL` names the worker timestamp as non-replayable |
| 404 foreign/unknown, 409 closed, 503 store unavailable | Met | `TestRoutes` (fake reads) and `test_routes_serve_the_pinned_drill_down_only_through_the_open_gate` (Postgres) |
| File-backed comparison: MATCH / INTENTIONAL_DELTA / MISSING_SOURCE / UNPROVEN; empty set stated as such | Met | `TestComparison` (each class, unnamed-Indeterminate is UNPROVEN, citing-no-record, empty set, lineage break FAILED) |
| Cutover closed if comparison or lineage fails | Met | `TestGate.test_every_refusal` (no report, schema, Site code/UUID, tenant, environment, non-PASSED, changed legacy digest, unreadable lineage, lineage break); PASSED opens |
| Fixture labelled cases never ordinary positive; demo annotation separate from provenance | Met | `demo_manifest_file.py` matches by exact evidence IDs; fault-fixture windows hold only limits |
| A LIMITED window names its limitation (phase-2 F1 rule) | Met | `test_open_bound_interval_makes_window_limited_and_names_it`; producer 10-09 line below |
| Dispatch/Analysis UI, V-01 comparison evidence, reviewer walkthrough | Not started | Phase 3b |

## Non-vacuity proofs (each reverted with `git checkout --`; `git status` clean afterwards)

- `_multi_epoch` disabled: 2 F3 tests fail. Lease `FAILED` update neutralised (`AND FALSE`): `test_a_lease_that_always_expires_reaches_failed` fails. `analytic_run_selection` removed from guard rule 8: `check-all` fails 1 of 6 ("The assessment store inserts only ... postgres_assessment_store.py:339 INSERT INTO analytic_run_selection").
- `INTERVAL_LIMITED` lift removed: the open-bound test fails (`'COMPLETE' == 'LIMITED'`). Digest refusal removed: `test_every_refusal` fails. Empty-set flag forced false: `test_empty_set_is_stated_as_such` fails. 409 branch removed: both route tests (fake and Postgres) fail.

## Checks run (final tree)

- **Backend with Postgres** (isolated `assetops_s3p3a2_test`, dropped afterwards; the leftover `assetops_s3p3a_test` was dropped first): `pytest backend/tests -q` 1818 passed (315 s). Targeted: analytic 19 passed; cutover 14 passed; S3 Postgres read + assessment 14 passed.
- **Host** 667 passed. **Gateway** 164 passed. **Simulator** 265 passed (from `simulator/`).
- **`tools/check-all.ps1`** (`-ExecutionPolicy Bypass`): 6 of 6 guards PASS.
- **Producer** `tools/s3_dispatch_cases.py run` at `74ad6c3`: exit 0, 313 s, 11 cases, every case `check met`, `VERIFY PASSED`, all evidence digests match, cutoff-A run still selects window revision 1. 10-09 `necessary-interval`: window `LIMITED`, interval `NECESSARY`, window limitations now `["INTERVAL_LIMITED: interval from 2026-10-09T03:30:00.000000Z: OPEN_BOUND: no OFF evidence after the interval in the read range"]`. Output `.agent/S3-01-dispatch-cases-run.txt`, manifest `.agent/S3-01-dispatch-cases-v1.manifest.json`. No listener left on 8710/8743.
- **Gate closed -> permitted** (producer tree, `DATABASE_URL` = `assetops_s3cases`, reports in the tree's own `var/`): `performance_migration show --site KOBO-001` before: "No Performance comparison report exists" (exit 2, gate closed). `run --tenant demo --site KOBO-001`: `PASSED: Empty-set comparison ...`, lineage `selected_runs 10`, all break counts 0, "Performance cutover: permitted" (exit 0).
- Frontend not run: no frontend file changed in phase 3a. Layout evidence: not applicable (no UI).
- Workspace `var/`, database `assetops` and the owner's servers untouched. A leftover `assetops_s3p2_test` from phase 2 remains (not created in this phase; not dropped).

## Known deviations

- Q9 and Q13: the stricter cohort rule and the named window limitation change `dispatch-3` output without a model-version bump; claim levels are unchanged by Q13, text and basis digests change. Pre-fix persisted runs are not reconciled automatically.
- Q10/Q11: gate closed on any `MISSING_SOURCE` exception; `INTENTIONAL_DELTA` only for Indeterminate with named limitations.
- Route tests for 503 and the 409 reason use a fake read service; the Postgres route test covers the real read path for 409 -> 200 and 404.

## Residual risk

- A window read evaluates the full input basis per request (~3k rows/day); `run_pending` reconciles every assessed Site per pass.
- KOBO-001's file baseline holds no dispatch claim, so the live gate opens on an explicit empty-set comparison; the classification paths are proven only by unit tests.

## Reviewer focus

- `dispatch_read.derive_status` against the "Read states" paragraph and Q12.
- `permits_performance_cutover` refusal order and the `main.py` gate wiring (environment identity, lineage reader).
- The `INTERVAL_LIMITED` lift (`dispatch_v3.assess`) and Q13.
