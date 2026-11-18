# Planner brief — refine S6-01 (Action store + controlled policy change)

You are the AssetOps Planner (Codex). The Architect's work order (`.agent/architect-autonomy-2026-10-15-answers.md`, item 3 and "Planner work" item 2; decision `D-2026-10-15-owner-absence-work-order`) asks you to refine S6-01 around `I-action-store`. Refine `tasks/S6-01-action-change.md` (38-line outline) into an implementation-ready packet on branch `plan/S6-01-refine` in worktree `C:\Users\assef\Bineyame\AssetOpsV1-plan2`. No code. The coordinator commits.

## Read

- Decision `D-2026-10-14-action-lifecycle-and-policy-application` in `.ai/DECISIONS.md` (and any answers file it or the A-action-lifecycle review cites), `.agent/A-action-lifecycle-review.md`.
- Backlog `.ai/MILESTONE_REVIEW_BACKLOG.md` "A-action-lifecycle review carries": L1, L2, I1 and S6-01 Planner carries P1-P10 — cover each explicitly.
- Registry nodes `I-action-store`, `I-action-read`, `I-action-ui`, `I-S6-01`, `D-action-records`, `I-configuration-change-read/-ui`, `I-recommendation-read/-ui`, `I-action-overview-ui`, `I-action-execution-ui`, `I-action-history-ui` and their panels (`frontend/docs/architecture/v69-dependency-registry-pilot.json`, `v69-panel-contracts.json`); mockups under `frontend/mockups/v69/`.
- Current Foundation publish path and actor identity code (S1, S4-02a SYSTEM publication), the Finding read (S4-01/S4-03), `backend/TESTING.md`, exemplar packet `tasks/S4-02d-analytic-finding-worker-schedule.md`.

## Requirements

1. Code-reality check: cite and verify every function, table, column, route, component, test and tool `path:line`; mark new things new.
2. Work-order constraint: `I-action-store` may be a reviewable, mergeable non-UI phase **only** if its persisted Action/event/application proof and its exact S6-01 consumer are demonstrated; do not ship a bare schema as a user outcome. Base on main (do not depend on unmerged LR-01/S5-01).
3. Pick one Action creation model and idempotency key (L1/P1), the transition table, command and actor authorization (SYSTEM demonstration commands labelled, P7), event ledger, Foundation publish under the Site lock with expected-revision check and typed 409 + FAILED event (P3), change artifact recording every row written, APPLIED only after commit (P4), no Action backdating (P5), pinned origin FindingRevision beside latest (P6), routes and `site_code` (P8), fixtures for every state at 1440/390 (P9), new columns (P10). No mock money as savings (P2).
4. Size: if larger than M, split into S6-01a (store + read, non-UI, mergeable) and S6-01b (UI, held for owner) with at most two phases each; the last phase review of each is its slice review. Focused tests per phase; one full suite per slice (`backend/TESTING.md`). UI part USER_REVIEW_REQUIRED true with reproducible owner walkthrough (serve mode, 1440/390 evidence).
5. Update `tasks/README.md` and registry `task` fields; keep the registry valid (`node frontend/docs/architecture/check_v69_dependency_registry.cjs`). Status must start `implementation-ready`.
6. Open contract choices: list as "Architect questions" with your recommendation each; plan around the recommendation.

Keep each packet tight (under ~250 lines). Print a short summary: packet(s), phases, Architect questions with recommendations, code-reality gaps.
