# Active Context

Routing only. Built history remains in `.ai/CODE_STATE.md`; decisions remain in `.ai/DECISIONS.md`.

## Current milestone and task

S1 Foundation is the active milestone. [S1-01 persisted Foundation](../tasks/S1-01-persisted-foundation.md) is built on branch `task/S1-01-persisted-foundation` and is **in review** (packet `.agent/S1-01-review-packet.md`); not accepted. Independent review and owner review (`USER_REVIEW_REQUIRED: true`) come next; S1-02 follows acceptance. Only one slice is active at a time.

The only executable queue is [tasks/README.md](../tasks/README.md). The current [system architecture](../frontend/docs/architecture/production-shaped-mvp.md), [technical design](../frontend/docs/architecture/production-shaped-mvp-technical-design.md), and [Site-first execution plan](../frontend/docs/architecture/site-first-execution-plan.md) own the current direction. The [open T0xx archive](../tasks/archive/pre-site-first-2026-10-07/README.md) is superseded historical reference. `.ai/FEATURE_MAP.md`, `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` and old scoped handoffs do not route current work.

The Architect decision `D-2026-10-07-s1-foundation-import-and-cutover` and [S1-01 addendum](../frontend/docs/architecture/s1-01-foundation-contract-addendum.md) control the first slice. Their decision status is distinct from owner acceptance; no owner sign-off on the three Site-first documents or S1-01 is recorded here.

## Built state to carry forward

The completed T001–T028 history remains in `tasks/completed/` and `.ai/CODE_STATE.md`: the existing Site shell, file-backed Foundation and Lab, causal mini-grid simulator, staged envelopes, demo Commit/Evidence/Overview and dispatch Finding. These are migration and regression inputs, not proof that the target Postgres/SQLite contracts already exist. Keep gitignored `var/sites`, Lab runs, stages and committed artifacts intact. Import or replay only through explicit migration steps and compare results; private world state never enters the product evidence store.

## Next read

Reviewer: read S1-01, its review packet and the `.ai/CODE_STATE.md` S1-01 entry, then the diff. Postgres setup and commands are in `backend/README-db.md`. S1-01 creates a persisted Foundation version and honest configuration gaps. S1-02 binds signals and completes configuration Readiness/SLD. S2 supplies accepted SourceEnvelope lineage. Run the workflow and architecture guards and checks applicable to changed behavior. Independent review and owner review are required by each packet; no approval is implied here.
