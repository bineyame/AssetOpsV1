# Architect request - contracts for the remaining W1 screen slices (2026-10-16)

Role: Architect (Codex). Branch `plan/W1-remaining-arch` (from main), worktree `C:\Users\assef\Bineyame\AssetOpsV1-gap-planning`. One batched call. Owner direction: maximum W1 progress, demo speed over perfection; user-facing wording and visuals are one W1-conclusion task, so do not spend rulings on copy.

State: main has S1-S5-01, S4-04, S6-01 (a+b) merged. S6-02a is in build, S5-02 in review, S4-05b implementation-ready. Remaining W1 screen slices whose packets are outlines and whose registry gates are open:
- S6-03 Site Work list (`tasks/S6-03-site-work-list.md`): needs `A-action-index` (registry node; requires `A-action-lifecycle`). Precedent: `D-2026-10-15-a-finding-index` and `.agent/A-finding-index-review.md` for the Finding index.
- S7-01 Site Health (`tasks/S7-01-site-health.md`): needs `A-S7-health` (requires `A-S2-evidence`, `A-S1-bindings`) and the bounds of `D-edge-health-cases`.
- S3-02 claim limit (`tasks/S3-02-claim-limit-follow-up.md`): needs `I-capability-read` under `A-evidence-readiness-health` (pre-S3 decision).

For each of the three, give the smallest implementable contract that closes its W1 core panel honestly (`sitework:1`, the health/asset W1 core panels `health:2` and `asset:3`, and the Evidence Analysis claim-limit panel): data source and read scope, currentness/watermark and empty vs Unknown semantics, refusals, what is new vs reused (cite path:line from current code), and fixture needs. Say whether each can be a single S slice or needs a non-UI/UI split. Read the registry nodes and panel `claim_portions` in `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `frontend/docs/architecture/site-first-execution-plan.md`, the v69 mockups for these screens, and the related decisions in `.ai/DECISIONS.md`.

Write `.agent/architect-W1-remaining-answers.md` and decisions `D-2026-10-16-a-action-index`, `D-2026-10-16-a-s7-health`, `D-2026-10-16-s302-capability` in `.ai/DECISIONS.md` (UTF-8, ASCII hyphens). Update the registry only to mark the A- nodes resolved with evidence if the checker stays valid (`node frontend/docs/architecture/check_v69_dependency_registry.cjs`). No code, no packet edits. Print a short summary.
