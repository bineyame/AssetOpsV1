# Architect request: S2-01c phase-2 choices (2026-10-09)

Owner instruction (verbatim, 2026-10-08): "start from and .agent/coordinator-handoff.md and let the architect and  planner plan S2-0* and implementer proceed. Open questions should be forwarded to architect."

S2-01c phase 2 (run publication clock, delayed-publication profile/scenario, fault manifest, host schedule) is built on `task/S2-01c-gateway-diagnostics-faults` (`2d442a2`..`5ec78a7`; handoff `.agent/S2-01c-phase-2-handoff.md`). The Implementer listed five choices in `.agent/S2-01c-questions-2.md`, each built fail-closed; it flags Q2 and Q3 (clock may not pass the world's position while executing; setup refuses delay windows extending past the run interval, so nothing releases after the world run ends) as the ones you may want to rule on.

Phase 3 (backend Lab routes, frontend, carries, full suites, packet) waits for your answers so any change folds into it. Please confirm or redirect each, record anything material in `.ai/DECISIONS.md`, amend packets if needed, write `.agent/architect-S2-01c-answers-3.md` stating precisely what phase 3 must change, and say whether you want the owner to weigh in. Do not review the phase. No product code; leave edits uncommitted.
