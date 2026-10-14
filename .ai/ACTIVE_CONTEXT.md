# Active Context

Routing only. Built history remains in `.ai/CODE_STATE.md`; decisions remain in `.ai/DECISIONS.md`.

## Current milestone and task

**S4-02d ([analytic/Finding worker schedule](../tasks/S4-02d-analytic-finding-worker-schedule.md)) is `active`** on `task/S4-02d-analytic-finding-worker-schedule` (from main `0d137768`; next-work select, 8.28% notice). Non-UI; storage ratified `D-2026-10-14-s402d-schedule-storage-and-install-gate`; do NOT install the schedule on an owner-visible host before `I-late-reading-series-and-money-limit` lands. Carries: packet implementer carries and `.agent/S4-02d-plan-fix-rereview.md` N2-N6. Phase 1 is reviewed (ACCEPT with carries, `.agent/S4-02d-phase-1-review.md`). **Phase 2 (health, install gate, S5 currentness seam; F1-F3 fixed) is built, fresh review pending**: handoff `.agent/S4-02d-phase-2-handoff.md`, built state `.ai/CODE_STATE.md` "S4-02d phase 2"; the review also owns its own I4 overlapping-ingestion race. Phase 3 (tick-only walkthrough) waits for that review. S4-02c is done and merged (`68106bac`). The S2-S4 paragraphs below are earlier routing.

S2 Evidence is the active milestone. S1 Foundation (S1-01/02/03) is done: merged on `main` at `26d013b`, independently reviewed with carries (recorded in the S1 packets and `.ai/MILESTONE_REVIEW_BACKLOG.md`), owner UI check accepted.

S2-01a (registered Lab basis) and S2-01b (durable simulated gateway) are reviewed and merged to main at `7c10283`; their carries are in `.ai/MILESTONE_REVIEW_BACKLOG.md`.

S2-01c is merged at `b4006d1`. [S2-02 authenticated ingestion and Site Evidence](../tasks/S2-02-ingestion-site-evidence.md) is built on `task/S2-02-ingestion-site-evidence` in phases 1-3 and is `in_review` (USER_REVIEW_REQUIRED: S2 Evidence owner checkpoint): Postgres evidence ledger and Receipt V2, owner-only gateway credential and direct-TLS upload, central diagnostics freshness, fingerprinted KOBO-001 empty-set cutover, Site Evidence/Analysis and Lab Commit UI, and a repeatable walkthrough (`tools/s2_demo_walkthrough.py`). Packet `.agent/S2-02-review-packet.md`, owner walkthrough `.agent/S2-02-owner-walkthrough.md`, built state in `.ai/CODE_STATE.md` "S2-02"; fix round 1 (review F1, Architect batch 4 Q28/Q26/Q32/count) built, see packet "Fix round 1"; open Architect questions `.agent/S2-02-questions-7.md`.

Pre-S3 startup: [PRE-S3-03](../tasks/PRE-S3-03-delivery-checker-report.md) (delivery checker, `next-work` report, `tools/check-all.ps1`) is `in_review` on `plan/pre-S3-startup`; packet `.agent/PRE-S3-03-review-packet.md`, built state in `.ai/CODE_STATE.md` "PRE-S3-03". The live report currently refuses to rank (37 approved core panels lack reviewed paths). Reviewer: read the task, that packet and `.agent/PRE-S3-03-questions.md`, then run `tools/check-all.ps1` and the `--next-work` command.

S3-01 ([typed dispatch assessment](../tasks/S3-01-dispatch-assessment.md)) is `in_review` on `task/S3-01-dispatch-assessment` (USER_REVIEW_REQUIRED: owner checkpoint). Phases 1, 2 and 3a (with `dispatch-3.1` and fix R1) are reviewed and accepted; phase 3b (Performance > Dispatch and Analysis UI, cutover summary, walkthrough, V-01 evidence 32/32) is built and awaits a fresh Claude review. Packet `.agent/S3-01-review-packet.md`, built state in `.ai/CODE_STATE.md` "S3-01 phase 3b", questions `.agent/S3-01-questions-5.md` (Q17-Q22), owner steps `.agent/S3-01-owner-walkthrough.md`.

S4-01 ([candidate generator-support Finding](../tasks/S4-01-finding-identity.md)) is `in_review` on `task/S4-01-finding-identity` (USER_REVIEW_REQUIRED: owner checkpoint). Phases 1 and 2 are reviewed and closed; phase 3 (`I-finding-ui`: Site Finding detail at `/sites/{site}/findings/{id}`, Dispatch day Finding links, walkthrough and app-vs-mock evidence 36/36) is built and awaits a fresh Claude review. Packet `.agent/S4-01-review-packet.md` (all phases), built state in `.ai/CODE_STATE.md` "S4-01 phase 3", questions `.agent/S4-01-questions-5.md` (Q25-Q30), owner steps `.agent/S4-01-owner-walkthrough.md`.

The only executable queue is [tasks/README.md](../tasks/README.md). The current [system architecture](../frontend/docs/architecture/production-shaped-mvp.md), [technical design](../frontend/docs/architecture/production-shaped-mvp-technical-design.md), and [Site-first execution plan](../frontend/docs/architecture/site-first-execution-plan.md) own the current direction. The [open T0xx archive](../tasks/archive/pre-site-first-2026-10-07/README.md) is superseded historical reference. `.ai/FEATURE_MAP.md`, `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` and old scoped handoffs do not route current work.

The Architect decision `D-2026-10-07-s1-foundation-import-and-cutover` and [S1-01 addendum](../frontend/docs/architecture/s1-01-foundation-contract-addendum.md) control the first slice. Their decision status is distinct from owner acceptance; no owner sign-off on the three Site-first documents or S1-01 is recorded here.

## Built state to carry forward

The completed T001–T028 history remains in `tasks/completed/` and `.ai/CODE_STATE.md`: the existing Site shell, file-backed Foundation and Lab, causal mini-grid simulator, staged envelopes, demo Commit/Evidence/Overview and dispatch Finding. These are migration and regression inputs, not proof that the target Postgres/SQLite contracts already exist. Keep gitignored `var/sites`, Lab runs, stages and committed artifacts intact. Import or replay only through explicit migration steps and compare results; private world state never enters the product evidence store.

## Next read

Reviewer (S4-02c phase 3 and slice): read the task (phase 3 row, carries C5, risks), `.agent/S4-02c-review-packet.md`, `.agent/S4-02c-phase-2-review.md` "Carries for phase 3" and `.agent/S4-02c-phase-3-handoff.md`, then `git diff 6d4a1995..HEAD` (slice: `git diff f9d6d1a5..HEAD`). Rerun `tools/s402c_late_power_walkthrough.py run --db assetops_s402c3walk_<x> --work <dir named s402c3*>` then `drop`; Postgres tests need `ASSETOPS_TEST_DATABASE_URL` on a `*_test` DB.

Reviewer (S4-02b phase 2b and whole slice): read the task, `.agent/S4-02b-review-packet.md`, `.agent/S4-02b-phase-2b-handoff.md` and `.agent/S4-02b-phase-2a-review.md` carries, then `git diff 3793e4d..HEAD`. Use private DBs via `tools/s402b_fuel_cost_walkthrough.py --work-name <new> prepare` and `tools/s402b-fuel-cost-evidence.mjs`; the owner keeps 8872/8873/5372/5373 and `assetops_s402bwalk`/`assetops_s402bempty`.

Reviewer (S4-02a phase 2 and closeout): read the task, `.agent/S4-02a-review-packet.md` and `.agent/S4-02a-phase-2-handoff.md`, then `git diff 5159b96..HEAD`. Walk it with `tools/s402a_assumptions_walkthrough.py --db assetops_s402a_<x> --empty-db assetops_s402a_<y> --work-name <new> prepare|links|serve|drop` and `node tools/s402a-assumptions-evidence.mjs <base> <empty-base> <finding-id> <out>`; the owner keeps 8870/8871/5370/5371.

Reviewer (S4-03 phase 3 and closeout): read the task's phase 3 row, `.agent/S4-03-review-packet.md`, `.agent/S4-03-handoff.md` "Phase 3", `.agent/architect-S4-03-answers.md` (Q3) and `.agent/S4-03-questions-2.md`, then `git diff 26b5e7a..HEAD`. Walk it on a private copy with `tools/s4_finding_walkthrough.py --db <private> --work <new folder> prepare|serve` and `node tools/s4-finding-evidence.mjs` (`ASSETOPS_S4_WALK_WORK`, `ASSETOPS_CDP_PORT`, suites all/history/closed) on ports 8898/5398; the owner keeps 8866/8867/5366/5367.

Reviewer (S4-01 phase 3 and closeout): read the task's phase 3 row and "Detail read and visible states", `.agent/S4-01-review-packet.md` and `.agent/S4-01-questions-5.md`, then `git diff 0f4808b..HEAD`; walk it with `tools/s4_finding_cases.py run`, `tools/s4_finding_walkthrough.py prepare|links|serve` (DB `assetops_s4walk`, API 8840, web 5340) and `node tools/s4-finding-evidence.mjs http://localhost:5340`.

Reviewer (S3-01 phase 3b): read the task's phase 3 row and "Read states and acceptance", `.agent/S3-01-review-packet.md`, `.agent/S3-01-phase-3b-handoff.md` and `.agent/S3-01-questions-5.md`, then `git diff cdc24f7..HEAD`; walk it with `tools/s3_dispatch_walkthrough.py` (isolated DBs `assetops_s3cases`, `assetops_s3walk`; API port 8820).

Reviewer (S2-02): read the task, `.agent/S2-02-review-packet.md`, `.agent/S2-02-owner-walkthrough.md` and the S2-02 decisions named in the task, then `git diff main...HEAD`. Postgres setup is in `backend/README-db.md`; the live path runs with `tools/s2_demo_walkthrough.py run` (isolated database `assetops_s2demo`). Run the workflow and architecture guards and checks applicable to changed behavior.
