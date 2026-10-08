# Architect request: S2-01b phase-2 questions (2026-10-08)

Owner instruction (verbatim, 2026-10-08): "start from and .agent/coordinator-handoff.md and let the architect and  planner plan S2-0* and implementer proceed. Open questions should be forwarded to architect."

S2-01b phase 2 (gateway process, authenticated local channel, host/backend wiring) is built on `task/S2-01b-durable-simulated-gateway` (HEAD `692296d`; handoff `.agent/S2-01b-phase-2-handoff.md`). The Implementer raised Q1-Q3 in `.agent/S2-01b-questions-2.md`, each built on a fail-closed default. Q1 is material: 41 of 293 Kobo reports are held as `INVALID_VALUE` because their exact values are non-terminating decimals.

Phase 3 (Lab frontend for the registered Stage, carry F1, packet and full suites) waits for your answer so that any adapter change can be folded into it. Please decide Q1-Q3, state precisely what phase 3 must build (if anything) for each and what moves to S2-01c/S2-02, record material decisions in `.ai/DECISIONS.md`, amend packets as needed, write `.agent/architect-S2-01b-answers-3.md`, and say whether you want the owner to weigh in. Do not review the phase. No product code; leave edits uncommitted.
