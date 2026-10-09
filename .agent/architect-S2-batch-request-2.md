# Architect request: batched S2 questions before S2-02 phase 3 (2026-10-09)

Owner instructions (verbatim): 2026-10-08 "start from and .agent/coordinator-handoff.md and let the architect and  planner plan S2-0* and implementer proceed. Open questions should be forwarded to architect." 2026-10-09 "codex review happens for the whole S2-0* for usage efficency. also bundle questions to codex, be efficent with its use"

S2-01c is merged to main (`b4006d1`). S2-02 phases 1 and 2 are built on `task/S2-02-ingestion-site-evidence` (handoffs `.agent/S2-02-phase-1-handoff.md`, `.agent/S2-02-phase-2-handoff.md`). Phase 3 (frontend Evidence and Lab Commit views, legacy replay comparison and cutover, owner Evidence walkthrough) waits for this one batched call so its answers fold in before the owner sees the slice.

Open questions, each built on a fail-closed default:
1. `.agent/S2-01c-questions-6.md` (Q1-Q5, from S2-01c fix round 2; S2-01c is merged — say if any needs a follow-up and where).
2. `.agent/S2-02-questions-1.md` (Q1-Q7, phase 1: external-ID mutability, who enables imported gateways/sources, claim/mode mismatch 403, whole-batch refusal on bad configuration reference, recompute domain, `received_at`, 413).
3. `.agent/S2-02-questions-2.md` (Q8-Q12, phase 2: rotation revokes immediately, freshness CURRENT within 2x cadence, direct TLS only, diagnostic refusal shape, demo-tenant-only CLI).
Also note the phase-2 open risks in its handoff (Windows credential-file permissions, a batch shared between runs blocking fully-released, a checked-in test TLS key, delivery state on GET commit rather than Stage).

Please rule on all in one pass, record material decisions in `.ai/DECISIONS.md`, amend `tasks/S2-02-ingestion-site-evidence.md` if phase 3 or a fix must change, record carries in `.ai/MILESTONE_REVIEW_BACKLOG.md`, and write `.agent/architect-S2-batch-answers-2.md` with an exact list of what phase 3 (or a phase-2 correction) must change. Say whether you want the owner to weigh in. Do not review the slice (fresh Claude reviews it, then Codex reviews S2-01c+S2-02 together). No product code; leave edits uncommitted.
