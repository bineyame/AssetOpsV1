# Architect request: S2-01c batched questions and review ruling (2026-10-09)

Owner instructions (verbatim): 2026-10-08 "start from and .agent/coordinator-handoff.md and let the architect and  planner plan S2-0* and implementer proceed. Open questions should be forwarded to architect." 2026-10-09 "codex review happens for the whole S2-0* for usage efficency. also bundle questions to codex, be efficent with its use"

This is one batched call. S2-01c is built on `task/S2-01c-gateway-diagnostics-faults` (packet `.agent/S2-01c-review-packet.md`) and had its per-slice first review by a fresh Claude reviewer: `.agent/S2-01c-review.md` (B1, B2 block; C1-C3 carry). Codex will review S2-01c and S2-02 together at the end of S2.

Please, in one pass:
1. Answer the open implementer questions, each built on a fail-closed default: `.agent/S2-01c-questions-3.md` (Q1 — whether the run's end-instant 15:00 reading is the right post-run pending report, given the 15-minute cadence rule — is the main one) and `.agent/S2-01c-questions-4.md` (Q1-Q5).
2. Rule on review finding B1 (undelayed readings stamped at the step-end instant, so `published_at - source_time` shows up to 12 h of undeclared delay and V3 bytes depend on step size): confirm the reviewer's fix direction or state the contract it must meet. Also say whether you disagree with any block/carry classification in the review.
3. Record material decisions in `.ai/DECISIONS.md`, amend S2-01c/S2-02 packets if needed, and write `.agent/architect-S2-01c-answers-4.md` with a precise list of what the fix round must change. Say whether you want the owner to weigh in.

No product code; leave edits uncommitted (the coordinator commits).
