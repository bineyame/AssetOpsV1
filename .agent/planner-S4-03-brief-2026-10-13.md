# Planner brief: S4-03 refinement (2026-10-13)

Role: Planner (Codex, per `.ai/ROLE_CONFIG.md`). Worktree `C:\Users\assef\Bineyame\AssetOpsV1-gap-planning`, branch `plan/S4-03-refine` (from main `d9eb9ca`). Codex cannot write .git: edit files only; the coordinator commits.

Owner selected S4-03 / `I-finding-evidence-read` next (verbatim in `.agent/owner-next-work-2026-10-13.md`) after a ≤5% contest with A-S4-financial.

## Read first
- `.agent/coordinator-handoff.md` (top section only), `AGENTS.md`, `.ai/START_HERE.md`, `.ai/PLANNING_GUIDANCE.md`, `.ai/WORKFLOW.md` (Task Spec Size: S/M; ceiling 160-220 lines; no minimum)
- `tasks/README.md`; `tasks/S4-03-finding-evidence-history.md` (outline); `tasks/S4-01-finding-identity.md` and its review/closeout records (`.agent/S4-01-*`), the S4-01 registry closeout
- Registry nodes on S4-03's path in `frontend/docs/architecture/v69-dependency-registry-pilot.json`: `I-finding-evidence-read`, `I-S4-03`, `I-finding-evidence-ui`, `I-finding-history-read`, `I-finding-history-ui`, `D-finding-revisions`, `I-finding-read`; panels `finding-evidence:1-2`, `finding-history:1`
- Decisions `D-2026-10-12-...finding...` and S4-01 decisions in `.ai/DECISIONS.md`; the S4 sections of `frontend/docs/architecture/production-shaped-mvp-technical-design.md` and `site-first-execution-plan.md`
- Mock: `frontend/mockups/v69/` finding-evidence and finding-history screens (honest missing states rule: content without a source is shown as "Not available yet" through `<MissingClaim gapId>` per `D-2026-10-13-g01-placement-and-orphan-scan-boundary`, or named for G-04 backfill)
- The built S4-01 code where needed for accurate anchors (bounded reads)

## Work
1. Refine `tasks/S4-03-finding-evidence-history.md` to implementation-ready against the built S4-01: concrete ACs, reviewer steps, file/API anchors, out-of-scope, honest missing states (state how new missing copy interacts with the G-01 orphan scan), checks (incl. `tools/check-all.ps1`, layout evidence at 1440/390 if layout-sensitive), owner walkthrough expectation. Phases under ~120k context each for a Claude implementer.
2. Note any registry/ledger edits the slice's closeout will need. Update the `tasks/README.md` S4-03 row.
3. Do not implement product code. Do not merge.

## Open questions
Architecture questions go to `.agent/planner-S4-03-questions-2026-10-13.md`: self-contained, options, recommendation, and whether implementation can proceed on a fail-closed default. Only questions that genuinely block or would mislead an Implementer.

End with a short summary: files changed, questions file path (or "none").
