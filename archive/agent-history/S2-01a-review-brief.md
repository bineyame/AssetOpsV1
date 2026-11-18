# Review brief: S2-01a (first review)

Role: Reviewer (Codex, per `.ai/ROLE_CONFIG.md`; first review of a slice is discovery).

- Target: branch `task/S2-01a-registered-lab-basis`, commits `ce65b8d`..`145ca18` on top of main `26d013b` (planning/decision commits `b322843`, `8544549`, `684aa91` are on the branch too).
- Spec: `tasks/S2-01a-registered-lab-basis.md`. Decisions: `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary` (with amendment), `D-2026-10-08-s1-bindings-roles-and-snapshot`, `D-2026-10-07-s2-edge-split-and-demo-source` in `.ai/DECISIONS.md`. Architect answers: `.agent/architect-S2-answers-2026-10-08.md`, `.agent/architect-S2-01a-answers-2.md`.
- Packet: `.agent/S2-01a-review-packet.md`; phase handoff `.agent/S2-01a-phase-1-handoff.md`; open implementer questions `.agent/S2-01a-questions-2.md` (being answered by the Architect in parallel; not for you to decide).
- Standing criteria: the task file, `.ai/WORKFLOW.md`, `.ai/ROLE_CONFIG.md`, and the project records.

Already run by the Implementer (do not re-run green suites unless you need to test a specific doubt): backend with Postgres tests 1614 passed; host 624; simulator 244; frontend vitest 1196; `npm run build` and `tsc` clean; architecture and agent-workflow checks pass; S2-01a layout mode passed at 1280/640 px; full layout-evidence run reached 132 PASS / 0 FAIL then the browser stopped responding (later sections unmeasured).

Constraints: do not fix, do not merge, do not commit (git is read-only in your sandbox). Write the review to `.agent/S2-01a-codex-review.md` with a verdict and findings, each classified as block or carry with reason.
