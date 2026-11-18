# Planner brief: mock gap closure packets (2026-10-12)

Role: Planner (Codex). Work only in this worktree (branch `planning/mock-gap-closure`). Do not edit `C:/Users/assef/Bineyame/AssetOpsV1`.

Owner-confirmed: `D-2026-10-12-mock-gap-closure-mechanism` sections 1-2 (`.ai/DECISIONS.md`, `.agent/architect-mock-gap-mechanism-answers.md`, `.agent/owner-mock-gap-confirmation-2026-10-12.md`); ranking (section 3) deferred to W1 exit.

Write reviewable packets per section 4 and `.ai/WORKFLOW.md` task-spec rules:
1. `tasks/G-01-mock-gap-catalogue-and-guard.md` (M): versioned registry `mock_gaps` schema, checker validation, typed missing-state component/API, orphan guard in `tools/check-all.ps1` with dated non-expanding legacy baseline, Vitest assertions, `delivery_next_work.cjs` reads but ignores the catalogue for scoring, mutation tests proving unknown/unused IDs and untagged copy fail.
2. `tasks/G-02-v01a-gap-pilot.md` (M): pilot mapping for `sites`, `foundation`, `readiness`, `sld` against V-01a's merged UI (it starts after V-01a merges; V-01a round 3 is on `task/V-01a-foundation-visual`, see `.agent/architect-V-01a-round3-answers.md` addendum for the current visible missing states).
3. Outline-only entries for the remaining W1 backfill batches (Lab/Evidence, Dispatch/Finding, Money/Overview/Work/Health), each M.
Add them to `tasks/README.md` and the registry/ledger as the queue rules require (with whatever registry nodes the checker needs so next-work can select them; state their dependencies: G-02 after V-01a merge and G-01; batches after G-02). Run the registry checker and `tools/check-all.ps1` (`powershell -ExecutionPolicy Bypass -File tools/check-all.ps1`). Questions needing the Architect go to `.agent/planner-mock-gap-questions.md` with fail-closed defaults. Leave edits uncommitted; end with a short summary.
