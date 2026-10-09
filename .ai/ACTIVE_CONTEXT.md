# Active Context

Routing only. Built history remains in `.ai/CODE_STATE.md`; decisions remain in `.ai/DECISIONS.md`.

## Current milestone and task

S2 Evidence is the active milestone. S1 Foundation (S1-01/02/03) is done: merged on `main` at `26d013b`, independently reviewed with carries (recorded in the S1 packets and `.ai/MILESTONE_REVIEW_BACKLOG.md`), owner UI check accepted.

S2-01a (registered Lab basis) and S2-01b (durable simulated gateway) are reviewed and merged to main at `7c10283`; their carries are in `.ai/MILESTONE_REVIEW_BACKLOG.md`.

S2-01c is merged at `b4006d1`. [S2-02 authenticated ingestion and Site Evidence](../tasks/S2-02-ingestion-site-evidence.md) is built on `task/S2-02-ingestion-site-evidence` in phases 1-3 and is `in_review` (USER_REVIEW_REQUIRED: S2 Evidence owner checkpoint): Postgres evidence ledger and Receipt V2, owner-only gateway credential and direct-TLS upload, central diagnostics freshness, fingerprinted KOBO-001 empty-set cutover, Site Evidence/Analysis and Lab Commit UI, and a repeatable walkthrough (`tools/s2_demo_walkthrough.py`). Packet `.agent/S2-02-review-packet.md`, owner walkthrough `.agent/S2-02-owner-walkthrough.md`, built state in `.ai/CODE_STATE.md` "S2-02"; open Architect questions `.agent/S2-02-questions-5.md` and `-6.md`.

The only executable queue is [tasks/README.md](../tasks/README.md). The current [system architecture](../frontend/docs/architecture/production-shaped-mvp.md), [technical design](../frontend/docs/architecture/production-shaped-mvp-technical-design.md), and [Site-first execution plan](../frontend/docs/architecture/site-first-execution-plan.md) own the current direction. The [open T0xx archive](../tasks/archive/pre-site-first-2026-10-07/README.md) is superseded historical reference. `.ai/FEATURE_MAP.md`, `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` and old scoped handoffs do not route current work.

The Architect decision `D-2026-10-07-s1-foundation-import-and-cutover` and [S1-01 addendum](../frontend/docs/architecture/s1-01-foundation-contract-addendum.md) control the first slice. Their decision status is distinct from owner acceptance; no owner sign-off on the three Site-first documents or S1-01 is recorded here.

## Built state to carry forward

The completed T001–T028 history remains in `tasks/completed/` and `.ai/CODE_STATE.md`: the existing Site shell, file-backed Foundation and Lab, causal mini-grid simulator, staged envelopes, demo Commit/Evidence/Overview and dispatch Finding. These are migration and regression inputs, not proof that the target Postgres/SQLite contracts already exist. Keep gitignored `var/sites`, Lab runs, stages and committed artifacts intact. Import or replay only through explicit migration steps and compare results; private world state never enters the product evidence store.

## Next read

Reviewer (S2-02): read the task, `.agent/S2-02-review-packet.md`, `.agent/S2-02-owner-walkthrough.md` and the S2-02 decisions named in the task, then `git diff main...HEAD`. Postgres setup is in `backend/README-db.md`; the live path runs with `tools/s2_demo_walkthrough.py run` (isolated database `assetops_s2demo`). Run the workflow and architecture guards and checks applicable to changed behavior.
