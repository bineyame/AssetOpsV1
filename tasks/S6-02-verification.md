# S6-02 — Later-window verification

Status: outline; refine after preceding task review, before activation
USER_REVIEW_REQUIRED: true
Milestone: S6 Work / Action / Verification
Depends on: S6-01
Branch: task/S6-02-verification
Planner: Codex, 2026-10-07

## Visible outcome

Site verification shows target, service/reserve guardrails and Verified, Ineffective or Inconclusive outcome.

## Persisted object and read contract

Immutable VerificationPlanRevision/Outcome and later-window analytic comparison read API.

## Demo acceptance

Planner names `I-sim-verification-cases`: use a baseline Lab run under the old effective Foundation and a separate later run under the S6-01 persisted policy revision. Produce a later public window with a target outcome, a guardrail failure and an inconclusive-evidence variant. Commit reports through the S2 gateway/ingestion path before evaluation. No policy change partway through one run is required; keep the fixed plan revision, applied-change event and both runs' public observations separately traceable.

Evaluate later committed evidence against frozen baseline and plan; fail a guardrail; reopen both windows and later recurrence.

## Missing/conflicting evidence

Missing baseline, weak coverage or conflicting later evidence yields Inconclusive.

## Evidence lineage

Outcome resolves plan, baseline/later assessments and accepted SourceEnvelope IDs.

## Review and refinement

S6-02 owns `I-sim-verification-cases`, `D-verification-window`, `I-verification-plan-read/ui`, `I-verification-read/ui` and `I-action-evidence-read/ui`. These gate `verification:1-3`, effect `changes:2`, `recommendation:2-3`, `action-plan:1` and `action-evidence:1`. The moved child views select the frozen `plan_revision_id`, predeclared target/guardrails and required evidence, accepted later-window IDs and explicit missing/inconclusive states. Compare exact Action child-view app/mock desktop and narrow behavior; no panel is delivered until its read and fixture paths are reviewed.

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Global Actions index and causal claims stronger than the comparison supports.
