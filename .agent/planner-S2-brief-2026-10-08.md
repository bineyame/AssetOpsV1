# Planner brief: S2 refinement (2026-10-08)

Role: Planner (Codex, per `.ai/ROLE_CONFIG.md`). Branch: `task/S2-01a-registered-lab-basis` (cut from main `26d013b`, S1 merged).

Owner instruction (verbatim, 2026-10-08): "start from and .agent/coordinator-handoff.md and let the architect and  planner plan S2-0* and implementer proceed. Open questions should be forwarded to architect."

## Read first

- `.agent/coordinator-handoff.md` (top section only)
- `AGENTS.md`, `.ai/START_HERE.md`, `.ai/ACTIVE_CONTEXT.md`, `.ai/PLANNING_GUIDANCE.md`
- `tasks/README.md`; `tasks/S2-01a-registered-lab-basis.md`, `tasks/S2-01b-*.md`, `tasks/S2-01c-*.md`, `tasks/S2-02-*.md` (and `tasks/S2-01-durable-gateway.md` if still referenced)
- `frontend/docs/architecture/production-shaped-mvp.md`, `-technical-design.md`, `site-first-execution-plan.md` (S2 sections)
- `D-2026-10-07-s2-edge-split-and-demo-source`, `D-2026-10-08-s1-bindings-roles-and-snapshot`, `D-2026-10-08-s1-foundation-organization` in `.ai/DECISIONS.md`
- S1 carries: `.agent/S1-01-review-packet.md`, `.agent/S1-02-review-packet.md` (notably n5 at line ~181: historical snapshot download availability depends on current registrations, "carry before S2"), `.agent/S1-03-review-packet.md`
- The built S1 code where needed to state accurate anchors (bounded reads; do not read whole large files).

## Work

1. Refine `tasks/S2-01a-registered-lab-basis.md` to implementation-ready against the S1 result as built and the carries S2-01a consumes (n5 snapshot availability; any others you judge in scope). Concrete ACs, reviewer steps, file/API anchors, out-of-scope, honest missing states, checks. Size it so a Claude implementer can build it in phases of under ~120k context each; if it is larger, propose phases (or a split) inside the packet.
2. Refresh S2-01b, S2-01c and S2-02 outlines only where the S1 result changes them (keep them outlines; note what each must refine before activation). Update `tasks/README.md` statuses accordingly. Compare with `queue_baseline_nodes` as `tasks/README.md` requires.
3. Do not implement product code. Do not merge. Commit your planning edits on this branch with a clear message.

## Open questions

Do not decide architecture questions yourself. Write any question that needs an Architect decision to `.agent/planner-S2-questions-2026-10-08.md`: each question self-contained, with the options you see, your recommendation, and whether S2-01a implementation can proceed before it is answered (and on what default). The coordinator forwards them to the Architect (Codex). Keep questions to ones that genuinely block or would mislead an Implementer.

End with a short summary: files changed, commit hash, questions file path (or "none").
