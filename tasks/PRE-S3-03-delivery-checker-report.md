# PRE-S3-03 — Delivery-plan checker and next-work report

Status: implementation-ready after this planning branch is reviewed; not a product slice
USER_REVIEW_REQUIRED: false
Branch: task/pre-S3-delivery-checker-report
Depends on: reconciled registry/queue and owner W1 core-panel/demo-value decision for a live ranking

## Visible outcome

The coordinator gets a deterministic `next-work` report showing eligible W1 candidates, blockers, scores and exact panel paths. Missing owner input or an unmapped approved claim fails closed; no task is selected. This implements `D-2026-10-09-owner-delivery-strategy` and the versioned `delivery_plan` in the dependency registry.

## Contract

- Discover S1–S7 task IDs and packet paths from `tasks/README.md`; validate unique ordered task rows, matching task nodes/packets and layer status. Do not maintain a second hard-coded task list. Keep `requires` technical, `sequenced_after` historical scheduling only, and `delivery_plan.enables` planning benefit only.
- Validate all 110 unique wave allocations against the manifest, all 58 W1 panel keys/titles against panel contracts, each approved core panel's reviewed claim-portion mapping, owner evidence, 1–5 demo value and active wave/K. Proposed IDs or unmapped positive portions are not reviewed paths. Product status/target is not panel completion. Reconcile the pilot panel/ledger links without claiming the remaining 200 panels are W1 work.
- Technical readiness follows all `requires` and claim-portion AND gates. Within one panel, alternative positive/Unknown variants remain separate; a truthful Unknown alone does not complete a positive core claim. Resolve all referenced nodes or report a typed mapping error. Emit stale-input fingerprints for registry, queue, packet status, panel contracts, manifest and owner input; refuse to rank when any changed since report generation.
- Score only unfinished, reviewable S/M/L candidates with a reviewed path to approved active-wave core panels. Compute every distinct reachable panel once: `B=Σ 1/(1+d)`, `P=5×(1−exp(−B/K))`, `R=min(5, distinct approved downstream areas/domains)`, and `score=.4D+.3P+.2R−.1E` with E 1/3/5. Distance counts remaining closeouts after the candidate and unresolved AND branches. Publish raw ready-now, closure-unlock, panel reach, d/path proof, D/P/R/E, eligible screens and blocked reasons. Apply technical/owner/review/active-task stops before ranking; XL has no score. Ties: fewer unresolved technical gates, lower effort, stable ID.
- For top two eligible scores, `gap=(top−second)/max(abs(top),1)`: at ≤5% stop for owner with facts and recommendation; at >5% through 10% choose by published tie-break and emit a notice for `.agent/coordinator-handoff.md`; above 10% select top. One eligible candidate needs no ranking notice. Never auto-clear a `USER_REVIEW_REQUIRED` checkpoint.

## Acceptance

Run the checker and report from a clean tree. Show fixtures for missing owner value, unmapped approved panel, proposed-only node, stale fingerprint, ordering-only S6/S7 edge, technical S5 money edge, tie/5%/10% boundaries, XL and a valid one-candidate result. All invalid cases fail closed with an actionable reason. Existing registry, ledger and navigation checks continue to pass.

## Normal check path

Wire registry, ledger, navigation and workflow guards into the normal local/CI check command documented for this repo. A clean run reports each guard; a missing tool or nonzero guard exits nonzero. The coordinator verifies this prerequisite before activating ranking or S3-01. Keep the report non-authoritative until owner W1 input is recorded.
