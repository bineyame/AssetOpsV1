# Planner brief: refine S2-01c (2026-10-09)

Role: Planner (Codex). Branch: `task/S2-01c-gateway-diagnostics-faults`, cut from `task/S2-01b-durable-simulated-gateway` at `08712e7` (S2-01b built, Codex first review, fix rounds and fresh Claude re-reviews accepted; not yet merged to main).

Owner instruction (verbatim, 2026-10-08): "start from and .agent/coordinator-handoff.md and let the architect and  planner plan S2-0* and implementer proceed. Open questions should be forwarded to architect."

Read: `tasks/S2-01c-gateway-diagnostics-faults.md` (amended several times by the Architect), `tasks/README.md`, `tasks/S2-01b-durable-simulated-gateway.md`, `.agent/S2-01b-review-packet.md`, `.agent/S2-01b-codex-review.md`, `.agent/S2-01b-fix-rereview.md`, `.agent/S2-01b-fix-rereview-2.md`, S2 decisions in `.ai/DECISIONS.md`, S2 carries in `.ai/MILESTONE_REVIEW_BACKLOG.md` (R1 is assigned to S2-01c's sealing work; F2/F3 layout carries are candidates for its Lab touch), and S2 sections of the architecture/technical design/execution plan. Bounded code reads for anchors.

Work: refine S2-01c to implementation-ready against S2-01b as built, in phases each under ~120k implementer context. Update S2-02's outline and `tasks/README.md` only where needed; check `queue_baseline_nodes`. No product code, no merge; git is read-only for you, the coordinator commits.

Questions needing an Architect decision go to `.agent/planner-S2-01c-questions.md` (self-contained, options, recommendation, whether implementation can proceed on a default). End with a short summary.
