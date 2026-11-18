# Planner brief: refine S2-01b (2026-10-08)

Role: Planner (Codex). Branch: `task/S2-01b-durable-simulated-gateway`, cut from `task/S2-01a-registered-lab-basis` at `85a11c4` (S2-01a built, Codex first review ACCEPT WITH CARRIES, not yet merged to main).

Owner instruction (verbatim, 2026-10-08): "start from and .agent/coordinator-handoff.md and let the architect and  planner plan S2-0* and implementer proceed. Open questions should be forwarded to architect."

Read: `tasks/S2-01b-durable-simulated-gateway.md`, `tasks/README.md`, `tasks/S2-01a-registered-lab-basis.md`, `.agent/S2-01a-review-packet.md`, `.agent/S2-01a-codex-review.md`, the S2 decisions in `.ai/DECISIONS.md` (`D-2026-10-07-s2-edge-split-and-demo-source`, `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary` with amendment, `D-2026-10-08-s2-registered-kobo-demo-configuration`), the S2 carries in `.ai/MILESTONE_REVIEW_BACKLOG.md`, and the S2 sections of the architecture/technical design/execution plan. Bounded code reads for anchors.

Work: refine S2-01b to implementation-ready against S2-01a as built (the Architect noted S2-01b must define the separate process's snapshot transfer and authorization), in phases each under ~120k implementer context. Fold in backlog carry F1 (RunCommitPanel committed-branch Commit block) only if it belongs in this slice's Lab touch. Update S2-01c/S2-02 outlines and `tasks/README.md` only where needed; check `queue_baseline_nodes`. No product code, no merge; git is read-only for you, the coordinator commits.

Questions needing an Architect decision go to `.agent/planner-S2-01b-questions.md` (self-contained, options, recommendation, whether implementation can proceed on a default). End with a short summary.
