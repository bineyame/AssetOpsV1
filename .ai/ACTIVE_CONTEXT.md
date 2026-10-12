# Active Context

Routing only. Built history remains in `.ai/CODE_STATE.md`; decisions remain in `.ai/DECISIONS.md`.

## Current milestone and task

**V-01a ([Site and Foundation visual fidelity](../tasks/V-01a-foundation-visual-fidelity.md)) is `in_review`** on `task/V-01a-foundation-visual` (USER_REVIEW_REQUIRED: owner visual checkpoint). Round 2 (owner rulings `D-2026-10-12-v01a-owner-visual-rulings`, Architect items 1-5) is built through `16d1095` and awaits a fresh independent fix re-review, then the owner's visual checkpoint. Packet `.agent/V-01a-review-packet.md` (section "Round 2"), owner guide `.agent/V-01a-owner-walkthrough.md`, built state in `.ai/CODE_STATE.md` "V-01a" and "V-01a round 2". The S2-S4 paragraphs below are earlier routing; S4-01 and its registry closeout are merged on main.

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

Reviewer (V-01a round 2): read the task, `.agent/architect-V-01a-answers.md` and the packet's "Round 2" section, then `git diff 13620b6..HEAD`; walk it with `tools/v01a_foundation_walkthrough.py prepare|serve` (DBs `assetops_v01awalk`, `assetops_v01aempty`; API 8860/8861, web 5360/5361) and `node tools/v01a-foundation-evidence.mjs http://localhost:5360 <dir> http://localhost:5361`.

Reviewer (S4-01 phase 3 and closeout): read the task's phase 3 row and "Detail read and visible states", `.agent/S4-01-review-packet.md` and `.agent/S4-01-questions-5.md`, then `git diff 0f4808b..HEAD`; walk it with `tools/s4_finding_cases.py run`, `tools/s4_finding_walkthrough.py prepare|links|serve` (DB `assetops_s4walk`, API 8840, web 5340) and `node tools/s4-finding-evidence.mjs http://localhost:5340`.

Reviewer (S3-01 phase 3b): read the task's phase 3 row and "Read states and acceptance", `.agent/S3-01-review-packet.md`, `.agent/S3-01-phase-3b-handoff.md` and `.agent/S3-01-questions-5.md`, then `git diff cdc24f7..HEAD`; walk it with `tools/s3_dispatch_walkthrough.py` (isolated DBs `assetops_s3cases`, `assetops_s3walk`; API port 8820).

Reviewer (S2-02): read the task, `.agent/S2-02-review-packet.md`, `.agent/S2-02-owner-walkthrough.md` and the S2-02 decisions named in the task, then `git diff main...HEAD`. Postgres setup is in `backend/README-db.md`; the live path runs with `tools/s2_demo_walkthrough.py run` (isolated database `assetops_s2demo`). Run the workflow and architecture guards and checks applicable to changed behavior.
