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

Typed EvidenceQuery/AnalyticInputSet, versioned dispatch analytic, persisted AnalyticRun/AssessmentRevision and window Performance read model.

## Demo acceptance

Choose a window, inspect generator/load/PV/battery evidence IDs and quality limits; add late evidence, recompute and reopen old/new revisions.

## Missing/conflicting evidence

A missing role, contradictory samples or weak quality yields an explicit Indeterminate/Unknown limit.

## Evidence lineage

Interval detail resolves accepted evidence IDs and exact Foundation/binding basis; contract tests compare simulated and captured physical inputs after normalization.

## Review and refinement

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Other domain analytics, direct JSON-file analytic reads and invented service status.
