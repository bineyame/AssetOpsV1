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

Pre-activation decisions `D-2026-10-09-pre-s3-claim-routes-and-actor`, `D-2026-10-09-pre-s3-evidence-readiness-health` and `D-2026-10-09-pre-s3-shared-contract-scope` are recorded. They define shared routes, actors and readiness/health boundaries; they do not add dispatch implementation dependencies. Activation still waits for `A-S3-dispatch` and normal-ingestion `I-sim-dispatch-cases`, plus accepted S2-02 and time-valid S1 bindings. W1 owner core-panel/demo-value input and startup guards are separate planning stops.

Typed EvidenceQuery/AnalyticInputSet over Postgres accepted records and time-valid role bindings, a durable consumer of S2-02 recompute jobs, versioned dispatch analytic, persisted AnalyticRun/AssessmentRevision and window Performance read model. Replace hard-coded demo device keys in `backend/assetops_backend/analytics/dispatch.py` and JSON assessment persistence with role-bound inputs and Postgres revisions; no raw envelope, SQL row or Lab world object crosses the analytic boundary.

Refinement must bind tenant/Site/domain, half-open window, knowledge cutoff, accepted evidence IDs/digests, Foundation/binding revisions and role coverage. Select a run/epoch basis for overlapping same-time simulated reports (including the S2 demo's two runs and fault epoch) or return Limited/Indeterminate; never sum them as one physical stream. Distinguish source-time overlap, server receipt and virtual publication time. Compare representative file-backed dispatch claims before read cutover; persist input hash/run/assessment revisions, consume recompute jobs and prove late-evidence revision selection. Necessary/Candidate/Indeterminate uses accepted lineage, not diagnostic contact or readiness as dispatch proof.

## Demo acceptance

Planner names the Lab scenario producer `I-sim-dispatch-cases`: reproducible complete, missing, contradictory and late public-report intervals from the registered Kobo basis through the durable gateway and normal ingestion. Record the scenario manifest and expected claim ceilings; private world truth is for Lab comparison only. This producer is part of the S3-01 review, not an assumed fixture supplied by the central analytic.

Choose a window, inspect generator/load/PV/battery evidence IDs and quality limits; compare representative dispatch claims with the file-backed S2-02 baseline before switching Performance reads to Postgres-derived revisions. Add late evidence, recompute and reopen old/new revisions.

## Missing/conflicting evidence

A missing role, contradictory samples or weak quality yields an explicit Indeterminate/Unknown limit.

## Evidence lineage

Interval detail resolves accepted evidence IDs and exact Foundation/binding basis. The S3 demo uses simulated input only; the first real pilot later compares captured physical inputs after normalization.

## Review and refinement

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Other domain analytics, direct JSON-file analytic reads and invented service status.
