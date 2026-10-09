# Active Context

Routing only. Built history remains in `.ai/CODE_STATE.md`; decisions remain in `.ai/DECISIONS.md`.

## Current milestone and task

S2 Evidence is the active milestone. S1 Foundation (S1-01/02/03) is done: merged on `main` at `26d013b`, independently reviewed with carries (recorded in the S1 packets and `.ai/MILESTONE_REVIEW_BACKLOG.md`), owner UI check accepted.

[S2-01a registered Lab basis](../tasks/S2-01a-registered-lab-basis.md) is built on `task/S2-01a-registered-lab-basis` (packet `.agent/S2-01a-review-packet.md`); Codex first review ACCEPT WITH CARRIES (`.agent/S2-01a-codex-review.md`), carries in the backlog; not yet merged to main. Decisions: `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary` (with amendment), `D-2026-10-08-s2-registered-kobo-demo-configuration`.

[S2-01b durable simulated gateway](../tasks/S2-01b-durable-simulated-gateway.md) is built on `task/S2-01b-durable-simulated-gateway` (cut from S2-01a `85a11c4`) in phases 1, 2, 3a and 3b and is `in_review`: separate gateway process, authenticated local IPC, V3/Batch V2 SQLite ledger, registered Stage read from it, `registered-kobo-publication` v1 device resolution, Lab gateway Stage and S2-01a carry F1 closed. Packet `.agent/S2-01b-review-packet.md`; built state in `.ai/CODE_STATE.md` "S2-01b".

The only executable queue is [tasks/README.md](../tasks/README.md). The current [system architecture](../frontend/docs/architecture/production-shaped-mvp.md), [technical design](../frontend/docs/architecture/production-shaped-mvp-technical-design.md), and [Site-first execution plan](../frontend/docs/architecture/site-first-execution-plan.md) own the current direction. The [open T0xx archive](../tasks/archive/pre-site-first-2026-10-07/README.md) is superseded historical reference. `.ai/FEATURE_MAP.md`, `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` and old scoped handoffs do not route current work.

The Architect decision `D-2026-10-07-s1-foundation-import-and-cutover` and [S1-01 addendum](../frontend/docs/architecture/s1-01-foundation-contract-addendum.md) control the first slice. Their decision status is distinct from owner acceptance; no owner sign-off on the three Site-first documents or S1-01 is recorded here.

## Built state to carry forward

The completed T001–T028 history remains in `tasks/completed/` and `.ai/CODE_STATE.md`: the existing Site shell, file-backed Foundation and Lab, causal mini-grid simulator, staged envelopes, demo Commit/Evidence/Overview and dispatch Finding. These are migration and regression inputs, not proof that the target Postgres/SQLite contracts already exist. Keep gitignored `var/sites`, Lab runs, stages and committed artifacts intact. Import or replay only through explicit migration steps and compare results; private world state never enters the product evidence store.

## Next read

Reviewer (S2-01b): read the task, `.agent/S2-01b-review-packet.md` and the S2-01b decisions, then the diff from S2-01a `85a11c4`; the packet names the reviewer path and live gateway setup. Postgres setup is in `backend/README-db.md`. Run the workflow and architecture guards and checks applicable to changed behavior.
