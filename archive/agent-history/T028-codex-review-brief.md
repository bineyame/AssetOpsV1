# Reviewer brief: T028 first review (Codex Reviewer, 2026-10-04)

You are the AssetOps Reviewer (Codex; `.ai/ROLE_CONFIG.md`), independent of the
Claude implementers who built this slice.

Target: branch `task/T028-dispatch-finding-and-evidence`, HEAD `3e75a54`,
diff against `main` (`38177b3`). Task `tasks/T028-dispatch-finding-and-evidence.md`.
Packet `.agent/T028-review-packet.md` (its uncertainties and reviewer items are
the authors' own). Phase handoffs `.agent/T028-phase-1-handoff.md`,
`-phase-2-handoff.md`, `-phase-3a-handoff.md`. Owner rulings
`.agent/owner-T028-phase-1-questions-2026-10-03.md`,
`.agent/owner-T028-closeout-2026-10-04.md`. Architect decisions
`.agent/T028-architect-readiness-decisions.md` and
`D-2026-10-04-analytic-readiness-scope-and-gap-impact`. No prior review exists.

Criteria: the task's acceptance criteria, Proof table and scope limits; this
project's records (`.ai/PROJECT_RULES.md`, `.ai/ARCHITECTURE.md`, decisions the
task cites); `D-2026-09-22-milestone-speed-over-purity` for block vs carry.

Already run and verified (do not re-run): at `3e75a54` backend 1468, host 616,
frontend 1098 passed; `tsc --noEmit` clean; both `tools/check-*.ps1` pass.
At `9524382` (before the readiness correction round) simulator 244, production
build, layout evidence `.agent/T028-layout-evidence.txt` 560 PASS / 5 FAIL.

Constraints: do not fix, edit code or merge. Write the review to
`.agent/T028-codex-review.md` with a verdict, findings with file:line anchors,
and for each finding whether it blocks or is carried and why. State that it is
a Codex review.
