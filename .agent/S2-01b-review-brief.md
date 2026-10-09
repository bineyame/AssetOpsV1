# Review brief: S2-01b (first review)

Role: Reviewer (Codex, per `.ai/ROLE_CONFIG.md`; first review of a slice is discovery).

- Target: branch `task/S2-01b-durable-simulated-gateway`, HEAD `bb09554`, cut from S2-01a branch at `85a11c4` (S2-01a: built, Codex first review ACCEPT WITH CARRIES, `.agent/S2-01a-codex-review.md`; not merged to main). Review the diff `85a11c4..bb09554` (planning/decision/record commits by the coordinator are included).
- Spec: `tasks/S2-01b-durable-simulated-gateway.md`. Decisions for S2-01b in `.ai/DECISIONS.md` (snapshot transfer; phase-1 wire defaults; `D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary` and amendment). Architect answers: `.agent/architect-S2-01b-answers*.md`. Questions files: `.agent/S2-01b-questions-*.md`.
- Packet: `.agent/S2-01b-review-packet.md`; phase handoffs `.agent/S2-01b-phase-1-handoff.md`, `-phase-2-handoff.md`, `-phase-3a-handoff.md`.
- Standing criteria: the task file, `.ai/WORKFLOW.md`, `.ai/ROLE_CONFIG.md`, project records.

Already run by the Implementers (do not re-run green suites unless testing a specific doubt): frontend vitest 1212; backend with Postgres 1630; host 638; simulator 265; gateway 76; architecture and agent-workflow checks pass. Layout evidence results and their limits are in the packet.

Constraints: do not fix, merge or commit (git is read-only for you). Write the review to `.agent/S2-01b-codex-review.md` with a verdict and findings, each classified block or carry with reason.
