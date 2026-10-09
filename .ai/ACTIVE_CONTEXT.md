# Active Context

Routing only. Built history remains in `.ai/CODE_STATE.md`; decisions remain in `.ai/DECISIONS.md`.

## Current milestone and task

S2 Evidence is the active milestone. S1 Foundation (S1-01/02/03) is done: merged on `main` at `26d013b`, independently reviewed with carries (recorded in the S1 packets and `.ai/MILESTONE_REVIEW_BACKLOG.md`), owner UI check accepted.

S2-01a (registered Lab basis) and S2-01b (durable simulated gateway) are reviewed and merged to main at `7c10283`; their carries are in `.ai/MILESTONE_REVIEW_BACKLOG.md`.

[S2-01c gateway diagnostics and fault scenarios](../tasks/S2-01c-gateway-diagnostics-faults.md) is built on `task/S2-01c-gateway-diagnostics-faults` in phases 1, 2, 3a and 3b and is `in_review`: state-safe seal refusals, GatewayDiagnosticsV1, opt-in run-virtual publication clock with delayed and post-run release, fault manifests, Lab schedule/advance/diagnostics views, S2-01b F2/F3 carries. Packet `.agent/S2-01c-review-packet.md`; built state in `.ai/CODE_STATE.md` "S2-01c"; fix round 1 (B1 ordered publication, B2, C1, Q3 `SCHEDULE_MISSING`) per `.agent/architect-S2-01c-answers-4.md` was re-reviewed (`.agent/S2-01c-fix-rereview.md`); fix round 2 (R1 `PUBLICATION_GAP`, ordinary watermark, Q5 live `SCHEDULE_MISSING`) per `.agent/architect-S2-batch-answers-2026-10-09.md` is built and awaits independent re-review; open Architect questions `.agent/S2-01c-questions-6.md`.

The only executable queue is [tasks/README.md](../tasks/README.md). The current [system architecture](../frontend/docs/architecture/production-shaped-mvp.md), [technical design](../frontend/docs/architecture/production-shaped-mvp-technical-design.md), and [Site-first execution plan](../frontend/docs/architecture/site-first-execution-plan.md) own the current direction. The [open T0xx archive](../tasks/archive/pre-site-first-2026-10-07/README.md) is superseded historical reference. `.ai/FEATURE_MAP.md`, `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` and old scoped handoffs do not route current work.

The Architect decision `D-2026-10-07-s1-foundation-import-and-cutover` and [S1-01 addendum](../frontend/docs/architecture/s1-01-foundation-contract-addendum.md) control the first slice. Their decision status is distinct from owner acceptance; no owner sign-off on the three Site-first documents or S1-01 is recorded here.

## Built state to carry forward

The completed T001–T028 history remains in `tasks/completed/` and `.ai/CODE_STATE.md`: the existing Site shell, file-backed Foundation and Lab, causal mini-grid simulator, staged envelopes, demo Commit/Evidence/Overview and dispatch Finding. These are migration and regression inputs, not proof that the target Postgres/SQLite contracts already exist. Keep gitignored `var/sites`, Lab runs, stages and committed artifacts intact. Import or replay only through explicit migration steps and compare results; private world state never enters the product evidence store.

## Next read

Reviewer (S2-01c): read the task, `.agent/S2-01c-review-packet.md` (its "Fix round 2" section first) and the S2-01c decisions including `D-2026-10-09-s2-publication-gap-and-batch-boundary`, then `git diff main...HEAD`; the packet names the reviewer path and live gateway setup. Postgres setup is in `backend/README-db.md`. Run the workflow and architecture guards and checks applicable to changed behavior.
