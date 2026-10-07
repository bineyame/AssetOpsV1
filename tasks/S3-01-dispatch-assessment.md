# S3-01 — Typed dispatch assessment and interval detail

Status: outline; refine after preceding task review, before activation
USER_REVIEW_REQUIRED: true
Milestone: S3 Performance / Dispatch
Depends on: S2-02
Branch: task/S3-01-dispatch-assessment
Planner: Codex, 2026-10-07

## Visible outcome

Site dispatch and selected-interval analysis classify a generator interval as Necessary, Candidate or Indeterminate.

## Persisted object and read contract

Typed EvidenceQuery/AnalyticInputSet over Postgres accepted records and time-valid role bindings, a durable consumer of S2-02 recompute jobs, versioned dispatch analytic, persisted AnalyticRun/AssessmentRevision and window Performance read model. Replace hard-coded demo device keys in `backend/assetops_backend/analytics/dispatch.py` and JSON assessment persistence with role-bound inputs and Postgres revisions; no raw envelope, SQL row or Lab world object crosses the analytic boundary.

## Demo acceptance

Planner names the Lab scenario producer `I-sim-dispatch-cases`: reproducible complete, missing, contradictory and late public-report intervals from the registered Kobo basis through the durable gateway and normal ingestion. Record the scenario manifest and expected claim ceilings; private world truth is for Lab comparison only. This producer is part of the S3-01 review, not an assumed fixture supplied by the central analytic.

Choose a window, inspect generator/load/PV/battery evidence IDs and quality limits; compare representative dispatch claims with the file-backed S2-02 baseline before switching Performance reads to Postgres-derived revisions. Add late evidence, recompute and reopen old/new revisions.

## Missing/conflicting evidence

A missing role, contradictory samples or weak quality yields an explicit Indeterminate/Unknown limit.

## Evidence lineage

Interval detail resolves accepted evidence IDs and exact Foundation/binding basis; contract tests compare simulated and captured physical inputs after normalization.

## Review and refinement

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Other domain analytics, direct JSON-file analytic reads and invented service status.
