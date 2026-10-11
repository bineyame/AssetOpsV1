# S3-01 phase 2 review packet: typed seam and durable dispatch assessment (`I-dispatch-assessment-store`)

- **Task:** `tasks/S3-01-dispatch-assessment.md`, phase 2. Status stays `active`. This phase gets a fresh Claude review before phase 3. USER_REVIEW_REQUIRED for the task is true; the owner checkpoint is at task close.
- **Branch:** `task/S3-01-dispatch-assessment`, commits `75886d1` (2a), `f2b7dee`, `148641c`, `452a5b1`, `2f716d8` and this packet's commit. Diff base: `733ea8d`.
- **Authority:** `D-2026-10-11-s3-dispatch-interval-assessment`, `D-2026-10-11-s3-phase-1-fixture-and-late-evidence` (`.agent/architect-S3-answers-1.md`), phase-1 review carries F3 and F5.
- **Open questions:** `.agent/S3-01-questions-2.md` Q1-Q8. Each has its fail-closed default built.

## Outcome delivered

Accepted S2 evidence now flows through a typed seam into a pure, versioned analytic and immutable revisions:

1. A tenant- and Site-scoped `EvidenceQuery` reads accepted evidence and the configuration selected at the knowledge cutoff.
2. Cohort selection runs next.
3. The result is frozen into an `AnalyticInputSet` with an input hash.
4. The `dispatch-3` pure analytic produces window and interval assessments.
5. These are persisted as an idempotent `AnalyticRun` and append-only `AssessmentRevision`s.

A recompute worker leases the S2 `dispatch` jobs, retries them and fails them with a reason. It coalesces through S2's PENDING-only rule, so no event is lost while a job is leased. It reassesses the affected window and its continuity neighbours. It also schedules windows whose model version or selected configuration changed.

The fixture now proves two of the Architect's required cases:
- A labelled out-of-order fault-fixture cohort.
- A two-cutoff late **central** acceptance.

There is no read API, UI or cutover; those are phase 3.

## Files materially changed

- `backend/assetops_backend/analytics/assessment_inputs.py`: the typed seam.
- `analytics/cohort.py`: cohort selection.
- `analytics/dispatch_v3.py`: the pure analytic.
- `analytics/assessment_ports.py`, `analytics/assessment_worker.py`, `analytics/assess_dispatch.py`: the CLI `process-jobs|reconcile|assess`.
- `analytics/composition.py`: `build_dispatch_assessment_worker`.
- `analytics/adapters/postgres_assessment_store.py`.
- `backend/migrations/versions/0007_dispatch_assessment.py`. Head assertions were bumped in `test_s1_bindings_postgres.py` and `test_s2_evidence_ledger_postgres.py`.
- `backend/tests/dispatch_3_decision_table.md`: the versioned table, comparing every carried or changed `dispatch-2` branch. `dispatch_decision_table.md` and `dispatch.py` are unchanged.
- Tests: `backend/tests/test_s3_dispatch_v3_analytic.py` (16), `backend/tests/test_s3_dispatch_assessment_postgres.py` (8).
- `tools/checks/configuration-persistence.ps1`: rule 8 now has a fourth writer, confined to its own tables plus `recompute_job` lease/retry/scheduling. No other module may write the assessment tables.
- `tools/s3_dispatch_cases.py`, plus evidence in `.agent/S3-01-dispatch-cases-run.txt` and `.agent/S3-01-dispatch-cases-v1.manifest.json`.

## Acceptance (task phase-2 row, the decision, and the Architect rulings)

| Criterion | Status | Evidence |
| --- | --- | --- |
| `EvidenceQuery`/`AnalyticInputSet` covering tenant/Site/domain, half-open window, `knowledge_at`, cohort, exact evidence IDs and digests, as-accepted and selected Foundation/binding revisions, role coverage, watermarks kept separate | Met | `assessment_inputs.py`. The repository read joins the ACCEPTED disposition and applies the cutoff to `decided_at`. Rejected, duplicate and conflicting dispositions never supply readings. Tests: `test_the_query_is_tenant_and_site_scoped_and_cut_at_knowledge` (another tenant returns no readings, controls or bindings; a cutoff 1 s earlier returns nothing) and `test_input_hash_covers_digests_not_order_or_cutoff` |
| F5: no unscoped or today's Foundation lookup | Met | Foundation and binding rows are filtered by tenant and Site, then selected with `recorded_at <= K < superseded_at` and validity overlapping the read range (`_configuration`). Each reading's as-accepted revision IDs are hashed too (Q1) |
| Pure analytic sees only typed public inputs | Met | `dispatch_v3.assess(AnalyticInputSet)` performs no IO. Roles are canonical role names, not device strings. The existing guards (dependency direction, analytic declaration) pass |
| Cohort: overlap or ambiguity gives Limited/Indeterminate, never latest-wins or summing | Met | 10-05 (two epochs) gives window `INDETERMINATE`, `AMBIGUOUS_COHORT`, no intervals. Explicit choices (`selection=EXPLICIT`, cohort-suffixed keys): epoch-1 run `3b30fd64…`, epoch-2 run `97187b74…`, each `SELECTED_EXPLICIT`. 10-04 (same epoch, Q3) gives window `INDETERMINATE` with `SEQUENCE_ORDER_INVERTED`/`REPORTS_OVERLAP`/`GENERATOR_SERIES_AMBIGUOUS`. Unit tests cover both |
| `dispatch-3` table and rule version stored per run/revision | Met | `dispatch_3_decision_table.md`; `analytic_run.model_version` and `assessment_revision.model_version` = `dispatch-3` |
| Necessary / bounded Candidate / Indeterminate; Candidate only with both capability roles | Met | 10-01 (roles-1): interval `INDETERMINATE`, window `LIMITED` with `MISSING_ROLE … over 00:00..24:00`. 10-02: `CANDIDATE_AVOIDABLE` bounded to Candidate segments, with `NECESSARY` segments present (`physical-necessary` check). 10-03 gap: Indeterminate segments over 06:00-06:45 |
| Run/revision persistence with input hash; idempotent replay; old revisions preserved | Met | Migration 0007 (append-only triggers; DELETE refused for all four tables in the test). `test_same_basis_reassessment_is_idempotent`. In the late test, replaying cutoff A reproduces run A's input hash, and `record_runs` returns the same run with `created=False` |
| Worker leases and retries S2 jobs and coalesces without losing an event during a run | Met | `test_acceptance_racing_a_leased_job_stays_dirty_and_is_reassessed`: jobs go LEASED+PENDING, then DONE+PENDING, then revision 2. `test_a_failed_run_retries_then_fails_with_its_reason`: RETRY, back-off, DONE; then RETRY, RETRY, FAILED with `last_error`. `test_a_lost_lease_commits_nothing` |
| Affected and continuity-neighbour windows for late evidence, backdated configuration and model version | Met | Each job covers the UTC days within ±6 h of its window. `test_backdated_configuration_and_model_version_schedule_reassessment`: a backdated reserve publication makes `reconcile` enqueue the window, giving a new window revision; a later reconcile enqueues nothing; a different model version is enqueued |
| F3 / ruling: two-cutoff late central acceptance | Met | Case `late-central-acceptance` (10-08). Two sealed batches were held at the gateway. Cutoff A `18:01:51.135Z` gave run `2190b1ff…` with window rev 1 `ebcfea71…`. The held batches were accepted at `18:01:54.398Z`/`.470Z` (four late IDs, `54688ac2…`, `682b244b…`, `c1682afb…`, `c9b8bfe9…`); new PENDING job `ac92d232…` for [10:55, 11:00]. Cutoff B `18:01:55.401Z` gave run `e17cfbbd…` with window rev 2 `57d693c3…`. `verify`, in a fresh process, confirms run A still selects rev 1 |
| Ruling Q5: separately labelled out-of-order fixture | Met | Case `out-of-order-fault-fixture` (10-07, epoch `s3-out-of-order-fixture-epoch`). `459de6e1…` (seq 1, 05:15) was accepted at 18:01:00.176. `5c701b59…` (seq 2, 05:00) was accepted at 18:01:00.284. The persisted window limitation is `SEQUENCE_ORDER_INVERTED: battery_soc 05:00..05:15` naming both IDs. The ordinary delayed case is renamed `late-publication` |
| Fixture never inferred from epoch name or manifest | Met | `cohort.py` has no epoch-string logic. The fault-fixture windows hold only limits; no Candidate or Necessary claim is made. Q4 asks how phase 3 should show a lone labelled stream |
| No read API, UI or cutover | Met | No router, frontend or Performance read touched |

## Checks run (final tree)

- **Backend, Postgres on** (isolated `assetops_s3p2_test`): `1795 passed` (317 s). This includes the 16 + 8 new tests.
- **Host:** `666 passed`. **Gateway:** `164 passed`. **Simulator:** `265 passed`, run from `simulator/`. From the repo root it reports a pre-existing collection error, `No module named 'tests'`, which this change did not cause.
- **`tools/check-all.ps1 -ExecutionPolicy Bypass`:** `All 6 guards passed`. Between `148641c` and `452a5b1` the CLI command name `run-pending` tripped the run-identity guard. It was renamed to `process-jobs` in `2f716d8`.
- **Non-vacuity of the new guard rule:** `DELETE FROM assessment_revision` in the assessment store, and `INSERT INTO assessment_revision` in the ledger, each fail it with a named reason. Both were reverted with `git checkout`.
- **Producer:** `tools/s3_dispatch_cases.py run` exited 0 (238 s, 10 cases, 3,197 accepted readings, 168 jobs DONE, every case `check met`). The in-run `verify` gave `VERIFY PASSED`. No listener was left on 8710/8743.
- **Layout evidence:** not applicable (no UI).

## Known deviations

- **Late-central proof scope.** The held batches carry readings at 10:55-11:00, after the 10-08 interval's last report. The interval revision (`969ade40…`, rev 1) is therefore correctly reused, and only the window revision changes. Interval-level reassessment by a late in-interval reading is proven in the Postgres test (`test_late_central_acceptance_appends_revisions_and_keeps_the_old_ones`: interval rev 1 → 2, late ID present only in rev 2).
- **Same-epoch overlap (10-04)** gives no interval at all. The generator series itself is ambiguous, so the window is `INDETERMINATE` with `GENERATOR_SERIES_AMBIGUOUS`. No interval claim is made.
- **Minimum runtime (Q2)** is Candidate-blocking only, and the table records this. No policy Necessary is claimed from a configured value.
- **No projection table (Q7).** The `site_window_projection` from the technical design is left to phase 3, or derived there.
- **One manifest schema.** The manifest stays `s3-dispatch-cases-v1`. Phase 2 adds `assessment`, `assessment_check`, `explicit_choices` and two cases; IDs are regenerated per environment (the phase-1 review carry).

## Residual risk

- **In-flight acceptance at lease time (Q6).** An acceptance still in flight at lease time is never lost, because S2 creates a new job for it. A replay at that cutoff could still differ from the run.
- **Interval keys anchor on the first ON report (Q8).** A late earlier ON report creates a new key.
- **Repeated input sets.** If a configuration revert re-creates an earlier input set, the old run is reused and the newest run per window by `completed_at` stays the later one. Phase 3 reads should select by job/cutoff, not by `completed_at` alone.

## Reviewer focus

1. Read `dispatch_3_decision_table.md` against `dispatch_decision_table.md`, especially rows 1-2, the cohort rules and the window claim levels.
2. Cohort and series limits in `cohort.py`: does anything in them amount to an epoch-name, sequence-range or receipt-order heuristic?
3. The worker's commit boundary: the lease token is `attempts`, and `_still_mine` runs inside the persisting transaction. Also review the guard rule 8 extension.
4. Q1 (controls at the cutoff versus as-accepted revisions) and Q4 (fixture default read) before phase 3.
