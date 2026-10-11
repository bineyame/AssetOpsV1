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

## dispatch-3.1 (version bump required before phase 3b)

Ruling `D-2026-10-11-s3-phase-3a-version-and-cutover` (`.agent/architect-S3-answers-3.md`, Q9-Q13). Commits `05f9b4d`..HEAD. Handoff to 3b, with the list of what the UI must show: `.agent/S3-01-dispatch-3-1-handoff.md`. Questions: `.agent/S3-01-questions-4.md` (Q14-Q16, with fail-closed defaults built). This section supersedes the Q9/Q13 "Known deviations" above.

### Delivered

- `dispatch_v3.MODEL_VERSION = "dispatch-3.1"` covers Q9 (multi-epoch default `AMBIGUOUS`) and Q13 (`INTERVAL_LIMITED` lifted into the window). The version is in every input and basis digest, so new revisions append under the same keys.
- Stored `dispatch-3` default windows are reassessed by the existing worker reconcile (`run_pending`, CLI `assess_dispatch process-jobs`). `dispatch-3` runs and revisions are untouched and stay readable. `run` and `revision` carry `model_note: OLDER_RULE_RESULT ...`. A `dispatch-3` head reads `STALE_PROJECTION` with `MODEL_VERSION_CHANGED` and is never CURRENT. Explicit selections are not remapped.
- Comparison (report schema v2, which records `model_version`):
  - `STALE_MODEL` is `UNPROVEN`.
  - `STALE_PROJECTION` is `UNPROVEN`. It applies when a PENDING, LEASED or FAILED job overlaps the window's read range, so a matching prior result stays stale.
  - `MISSING_SOURCE` gives `EXCEPTIONS`, so the gate stays closed.
  - `INTENTIONAL_DELTA` applies only through `DOCUMENTED_DELTAS`, which has one entry: `CAPABILITY_CHANNELS_REQUIRED`, rows 5a/5b, legacy Candidate to Indeterminate. The interval's own segments must name the limitation, and the cited records must be in the interval's evidence. A window-level limitation does not qualify.
  - `MATCH` also needs that comparable basis (Q15 default).
  - The gate refuses a report made under another model version. It also refuses while any head is still on another model (lineage `selected_heads_other_model`).
  - An empty-set statement says "a zero-inventory statement, not claim parity". The statement names any lineage breaks.
- Labels:
  - The cutover read label is `POSTGRES_DISPATCH_3_1`.
  - The window calendar names the model.
  - The decision table `backend/tests/dispatch_3_decision_table.md` gains "Model versions" and "Comparison" sections.

### Tests (each failed before its change)

- Analytic `test_corrected_rules_publish_as_dispatch_3_1_and_refuse_a_dispatch_3_input_set`: 1 failed, then passed.
- Postgres `test_stored_dispatch_3_windows_are_reassessed_under_dispatch_3_1_and_kept_as_history` failed, then passed. It writes the stored rows with the pre-bump `MODEL_VERSION`, then checks:
  - the window reads stale;
  - lineage counts 1 head on the old model;
  - the normal worker pass leaves the window CURRENT on `dispatch-3.1`, with the same key and a higher `revision_no`;
  - the old revision and run stay addressable with an unchanged basis and an `OLDER_RULE_RESULT` note;
  - a second reconcile is empty.
- Cutover tests (`test_s3_performance_cutover.py`, 20): the window-limitation-elsewhere delta is now `UNPROVEN`; plus the delta's comparable basis, `MATCH` comparable basis, delta claim specificity, stale model, outstanding job (PENDING, LEASED, FAILED), and refusals for a `MISSING_SOURCE` report, another model version, a report model and stale heads. 12 failed before the change, then all passed.

### Non-vacuity proofs (each mutation on committed code, reverted with `git checkout --`; `git status` clean)

| Mutation | Result |
| --- | --- |
| `MODEL_VERSION` back to `dispatch-3` | 2 failed |
| stale-model check removed | 1 failed |
| outstanding-job check removed | 1 failed |
| delta comparable-basis check removed | 1 failed |
| delta reads window limitations | 2 failed |
| `MATCH` comparable-basis check removed | 1 failed |
| report-model refusal removed | 1 failed |
| stale-heads refusal removed | 1 failed |
| `selected_heads_other_model` SQL neutralised | 1 failed (Postgres) |
| `model_note` removed | 1 failed (Postgres) |

### Stored-window migration and the rerun comparison gate (`.agent/S3-01-dispatch-3-1-migration-run.txt`)

The phase-3a `assetops_s3cases` held 9 `dispatch-3` heads (12 runs, 18 revisions). The commands ran in the producer tree with the backend at `05f9b4d`.

1. Before:
   - The phase-3a report (v1) is refused.
   - `performance_migration run` gives FAILED with `selected_heads_other_model: 9` and keeps the gate closed (exit 1).
2. `assess_dispatch process-jobs` exits 0.
3. After:
   - All 9 heads are `dispatch-3.1`.
   - The `dispatch-3` runs and revisions are retained: 12 runs and 18 revisions, beside 9 runs and 13 revisions on `dispatch-3.1`.
   - The 10-09 window is `LIMITED` and names `INTERVAL_LIMITED ... OPEN_BOUND ...`.
4. `performance_migration run` gives PASSED (empty set, zero-inventory) with "Performance cutover: permitted" (exit 0).

On the rebuilt fixture (commit `2dd90ec`), all heads are `dispatch-3.1` and the gate goes from "No report" (closed) to PASSED (permitted).

### Checks run (final code `2dd90ec`)

- Backend with Postgres (isolated `assetops_s31_test`, dropped afterwards): `pytest backend/tests` 1826 passed (337 s).
- Host 667 passed. Gateway 164 passed. Simulator 265 passed (from `simulator/`).
- `tools/check-all.ps1` (`-ExecutionPolicy Bypass`): 6 of 6 PASS.
- Producer `tools/s3_dispatch_cases.py run`:
  - First attempt: VERIFY FAILED on `overlap-separable-epoch`, because the epoch-2 upload pass hit `TIMEOUT` with one batch retrying (656 rows reloaded against 498). That run overlapped my concurrent test and proof runs; the upload fault came before any analytic step.
  - Rerun with no other load: 322 s, `VERIFY PASSED`, exit 0. Its log is `.agent/S3-01-dispatch-cases-run.txt`. No listener remains on 8710 or 8743.
- Frontend: not run (no frontend change). Layout evidence: not applicable.
- Housekeeping: dropped the leftover agent databases `assetops_s3p2_test` and `assetops_s3p3arev_test`. No producer process was on 8710 or 8743. The processes on 8610 (Lab) and 8643 (S2 demo TLS) were left alone. The workspace `var/` and the owner's servers were not touched.

### Known deviations and residual risk

- `DOCUMENTED_DELTAS` holds one rule (Q14). Every other legacy mismatch is `UNPROVEN`. KOBO-001 has no legacy claims, so the classification paths are proven by unit tests only.
- The cutover route returns `permitted` and `reason` only. Phase 3b must expose the report summary (counts, missing IDs, delta rule and IDs, `model_version`) before the UI can show it.
- The producer's own manifest status text still says "phase 2 adds the persisted dispatch-3 result". It was left unchanged so the manifest does not change.

## Fix round (R1)

R1 (review `.agent/S3-01-phase-3a-review.md`): a FAILED recompute job no longer makes a window read FAILED forever.

- `postgres_assessment_store.py`: new `_LIVE_JOBS` predicate used by `window_snapshot` and `selected_intervals`. PENDING/LEASED jobs always count; a FAILED job counts only until a later DEFAULT selection of the analytic (`selected_at` after the failure) overlaps the job's window. `fail_job` now stores the failure instant in `available_at` on final failure (no backoff offset; no migration) so "later" is well defined. A superseded job is ignored for every window in its bracket, so `derive_status` returns CURRENT and the comparison no longer classifies the intervals STALE_PROJECTION. The FAILED row stays as history.
- Tests (`backend/tests/test_s3_dispatch_read_postgres.py`): `test_a_later_successful_reassessment_supersedes_the_failed_job` (FAILED, then CURRENT after a successful matching reassessment; `selected_intervals` shows no FAILED `window_jobs` afterwards) and `test_a_neighbouring_window_in_the_bracket_recovers_with_it` (next-day window reads FAILED via the bracket, then CURRENT). Both fail before the fix (`FAILED == CURRENT` assertion, fix stashed) and pass after.
- Checks: S3 Postgres files plus `test_s3_performance_cutover.py` pass; full backend 1828 passed (isolated DB `assetops_s3r1_test`, dropped afterwards); `tools/check-all.ps1` all 6 guards passed.
- Known: jobs that already failed before this change have `available_at` offset by backoff, so their recovery is delayed by that offset at most. R2-R5 untouched.
