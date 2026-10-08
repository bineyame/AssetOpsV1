# Active Context

Routing only. Built history remains in `.ai/CODE_STATE.md`; decisions remain in `.ai/DECISIONS.md`.

## Current milestone and task

S1 Foundation is the active milestone. [S1-01 persisted Foundation](../tasks/S1-01-persisted-foundation.md) is built and independently re-reviewed (accept with carries) on `task/S1-01-persisted-foundation`, awaiting owner review. [S1-02 bindings, Readiness and SLD](../tasks/S1-02-bindings-readiness.md) is built on `task/S1-02-bindings-readiness` (cut from S1-01 `06ac8f5`) and is **in review** (packet `.agent/S1-02-review-packet.md`); not accepted. The Codex review accepted S1-01 with carries and returned S1-02 for changes; the fix round (M1-M3, D2-D5; migration 0004) is in the packet's "Fix round" section and awaits re-review. Owner review is required for both. Decision `D-2026-10-08-s1-bindings-roles-and-snapshot` governs S1-02. The owner could not verify S1 on the old Foundation page (`.agent/owner-S1-ui-feedback-2026-10-08.md`), so [S1-03 Foundation organization](../tasks/S1-03-foundation-organization.md) (decision `D-2026-10-08-s1-foundation-organization`) is built on `task/S1-03-foundation-organization` and is **in review** (packet `.agent/S1-03-review-packet.md`, owner guide `.agent/S1-03-owner-steps.md`). It was independently reviewed (accept with carries) and owner-accepted; its fix round plus the S1-02 n6 binding-edit correction are in the packet, and the n6 correction needs an independent review before S2-01a and the S1 merge.

The only executable queue is [tasks/README.md](../tasks/README.md). The current [system architecture](../frontend/docs/architecture/production-shaped-mvp.md), [technical design](../frontend/docs/architecture/production-shaped-mvp-technical-design.md), and [Site-first execution plan](../frontend/docs/architecture/site-first-execution-plan.md) own the current direction. The [open T0xx archive](../tasks/archive/pre-site-first-2026-10-07/README.md) is superseded historical reference. `.ai/FEATURE_MAP.md`, `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` and old scoped handoffs do not route current work.

The Architect decision `D-2026-10-07-s1-foundation-import-and-cutover` and [S1-01 addendum](../frontend/docs/architecture/s1-01-foundation-contract-addendum.md) control the first slice. Their decision status is distinct from owner acceptance; no owner sign-off on the three Site-first documents or S1-01 is recorded here.

## Built state to carry forward

The completed T001–T028 history remains in `tasks/completed/` and `.ai/CODE_STATE.md`: the existing Site shell, file-backed Foundation and Lab, causal mini-grid simulator, staged envelopes, demo Commit/Evidence/Overview and dispatch Finding. These are migration and regression inputs, not proof that the target Postgres/SQLite contracts already exist. Keep gitignored `var/sites`, Lab runs, stages and committed artifacts intact. Import or replay only through explicit migration steps and compare results; private world state never enters the product evidence store.

## Next read

Reviewer: for S1-03, read its task, the Architect decision, `.agent/S1-03-review-packet.md`, the `.ai/CODE_STATE.md` S1-03 entry and `.agent/S1-03-questions.md`, then the diff from `f639990`. For S1-01 and S1-02, read their packets and code-state entries, then the diffs. Postgres setup and commands are in `backend/README-db.md`. S1-01 creates a persisted Foundation version and honest configuration gaps. S1-02 binds signals and completes configuration Readiness/SLD. S2 supplies accepted SourceEnvelope lineage. Run the workflow and architecture guards and checks applicable to changed behavior. Independent review and owner review are required by each packet; no approval is implied here.
